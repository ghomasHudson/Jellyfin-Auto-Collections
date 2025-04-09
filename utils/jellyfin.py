import requests
from loguru import logger
from base64 import b64encode
import json
import concurrent.futures
from .poster_generation import fetch_collection_posters, safe_download, create_mosaic, get_font


class JellyfinClient:

    imdb_to_jellyfin_type_map = {
        "movie": ["Movie"],
        "short": ["Movie"],
        "tvEpisode": ["TvProgram", "Episode"],
        "tvSeries": ["Program", "Series"],
        "tvShort": ["TvProgram", "Episode", "Program"],
        "tvMiniSeries": ["Program", "Series"],
        "tvMovie": ["Movie", "TvProgram", "Episode"],
        "video": ["Movie", "TvProgram", "Episode", "Series"],
        "show": ["Program", "Series"],
    }

    def __init__(self, server_url: str, api_key: str, user_id: str):
        self.server_url = server_url
        self.api_key = api_key
        self.user_id = user_id

        # Check if server is reachable
        try:
            requests.get(self.server_url)
        except requests.exceptions.ConnectionError:
            raise Exception("Server is not reachable")

        # Check if api key is valid
        res = requests.get(f"{self.server_url}/Users/{self.user_id}", headers={"X-Emby-Token": self.api_key})
        if res.status_code != 200:
            raise Exception("Invalid API key")

        # Check if user id is valid
        res = requests.get(f"{self.server_url}/Users/{self.user_id}", headers={"X-Emby-Token": self.api_key})
        if res.status_code != 200:
            raise Exception("Invalid user id")


    def get_all_collections(self):
        params = {
            "enableTotalRecordCount": "false",
            "enableImages": "false",
            "Recursive": "true",
            "includeItemTypes": "BoxSet",
            "fields": ["Name", "Id", "Tags"]
        }
        logger.info("Getting collections list...")
        res = requests.get(f'{self.server_url}/Users/{self.user_id}/Items',headers={"X-Emby-Token": self.api_key}, params=params)
        return res.json()["Items"]


    def find_collection_with_name_or_create(self, list_name: str, list_id: str, description: str, plugin_name: str) -> str:
        '''Returns the collection id of the collection with the given name. If it doesn't exist, it creates a new collection and returns the id of the new collection.'''
        collection_id = None
        collections = self.get_all_collections()

        # Check if list name in tags
        for collection in collections:
            if json.dumps(list_id) in collection["Tags"]:
                collection_id = collection["Id"]
                break

        # if no match - Check if list name == collection name
        if collection_id is None:
            for collection in collections:
                if list_name == collection["Name"]:
                    collection_id = collection["Id"]
                    break

        if collection_id is not None:
            logger.info("found existing collection: " + list_name + " (" + collection_id + ")")

        if collection_id is None:
            # Collection doesn't exist -> Make a new one
            logger.info("No matching collection found for: " + list_name + ". Creating new collection...")
            res2 = requests.post(f'{self.server_url}/Collections',headers={"X-Emby-Token": self.api_key}, params={"name": list_name})
            collection_id = res2.json()["Id"]

        # Update collection description and add tags to we can find it later
        if collection_id is not None:
            collection = requests.get(f'{self.server_url}/Users/{self.user_id}/Items/{collection_id}', headers={"X-Emby-Token": self.api_key}).json()
            if collection.get("Overview", "") == "" and description is not None:
                collection["Overview"] = description
            collection["Tags"] = list(set(collection.get("Tags", []) + ["Jellyfin-Auto-Collections", plugin_name, json.dumps(list_id)]))
            r = requests.post(f'{self.server_url}/Items/{collection_id}',headers={"X-Emby-Token": self.api_key}, json=collection)

        return collection_id

    def has_poster(self, collection_id):
        '''Check if a collection already has a poster'''
        poster_url = f"{self.server_url}/Items/{collection_id}/Images/Primary"
        r = requests.get(poster_url, headers={"X-Emby-Token": self.api_key})
        if r.status_code == 404:
            return False
        return True


    def make_poster(self, collection_id, collection_name, mosaic_limit=20, google_font_url="https://fonts.googleapis.com/css2?family=Dosis:wght@800&display=swap"):

        # Check if collection poster exists
        poster_urls = fetch_collection_posters(self.server_url, self.api_key, self.user_id, collection_id)[:mosaic_limit]
        headers={"X-Emby-Token": self.api_key}

        # Use a ThreadPoolExecutor to download images in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(safe_download, url, headers) for url in poster_urls]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Filter out any failed downloads (None values)
        poster_images = [img for img in results if img is not None]

        font_path = get_font(google_font_url)

        if poster_images:
            safe_name = collection_name.replace(" ", "_").replace("/", "_")
            output_path = f"/tmp/{safe_name}_cover.jpg"
            create_mosaic(poster_images, collection_name, output_path, font_path)
        else:
            logger.warning(f"No posters available for collection '{collection_name}'. Skipping mosaic generation.")

        # Upload

        from PIL import Image
        img = Image.open(output_path)  # or whatever format
        img = img.convert("RGB")  # Ensures it's safe for JPEG
        img.save(output_path, format="JPEG")

        with open(output_path, 'rb') as f:
            img_data = f.read()
        encoded_data = b64encode(img_data)

        headers["Content-Type"] = "image/jpeg"
        r = requests.post(f"{self.server_url}/Items/{collection_id}/Images/Primary", headers=headers, data=encoded_data)


    def add_item_to_collection(self, collection_id: str, item, year_filter: bool = True, jellyfin_query_parameters={}):
        '''Adds an item to a collection based on item name and release year'''

        item["media_type"] = self.imdb_to_jellyfin_type_map.get(item["media_type"], item["media_type"])

        params = {
            "enableTotalRecordCount": "false",
            "enableImages": "false",
            "Recursive": "true",
            "IncludeItemTypes": item["media_type"],
            "searchTerm": item["title"],
            "fields": ["ProviderIds", "ProductionYear"]
        }

        params = {**params, **jellyfin_query_parameters}

        res = requests.get(f'{self.server_url}/Users/{self.user_id}/Items',headers={"X-Emby-Token": self.api_key}, params=params)

        # Check if there's an exact imdb_id match first
        match = None
        if "imdb_id" in item:
            for result in res.json()["Items"]:
                if result["ProviderIds"].get("Imdb", None) == item["imdb_id"]:
                    match = result
                    break
        else:
            # Check if there's a year match
            if match is None and year_filter:
                for result in res.json()["Items"]:
                    if str(result.get("ProductionYear", None)) == str(item["release_year"]):
                        match = result
                        break

            # Otherwise, just take the first result
            if match is None and len(res.json()["Items"]) == 1:
                match = res.json()["Items"][0]

        if match is None:
            logger.warning(f"Item {item['title']} ({item.get('release_year','N/A')}) {item.get('imdb_id','')} not found in jellyfin")
            return False
        else:
            try:
                item_id = res.json()["Items"][0]["Id"]
                requests.post(f'{self.server_url}/Collections/{collection_id}/Items?ids={item_id}',headers={"X-Emby-Token": self.api_key})
                logger.info(f"Added {item['title']} to collection")
                return True
            except json.decoder.JSONDecodeError:
                logger.error(f"Error adding {item['title']} to collection - JSONDecodeError")
        return False



    def clear_collection(self, collection_id: str):
        '''Clears a collection by removing all items from it'''
        res = requests.get(f'{self.server_url}/Users/{self.user_id}/Items',headers={"X-Emby-Token": self.api_key}, params={"Recursive": "true", "parentId": collection_id})
        ids = [item["Id"] for item in res.json()["Items"]]
        requests.delete(f'{self.server_url}/Collections/{collection_id}/Items',headers={"X-Emby-Token": self.api_key}, params={"ids": ",".join(ids)})
        logger.info(f"Cleared collection {collection_id}")
