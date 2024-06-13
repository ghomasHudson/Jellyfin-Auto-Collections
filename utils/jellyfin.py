import requests
from loguru import logger
import json


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
            "includeItemTypes": "BoxSet"
        }
        print("Getting collections list...")
        res = requests.get(f'{self.server_url}/Users/{self.user_id}/Items',headers={"X-Emby-Token": self.api_key}, params=params)
        collections = {r["Name"]:r["Id"] for r in res.json()["Items"]}
        return collections


    def find_collection_with_name_or_create(self, list_name: str) -> str:
        '''Returns the collection id of the collection with the given name. If it doesn't exist, it creates a new collection and returns the id of the new collection.'''
        collection_id = None
        collections = self.get_all_collections()
        for collection in collections:
            if list_name == collection:
                logger.info("found collection: " + list_name + " (" + collections[collection] + ")")
                collection_id = collections[collection]
                break

        if collection_id is None:
            # Collection doesn't exist -> Make a new one
            logger.info("No matching collection found for: " + list_name + ". Creating new collection...")
            res2 = requests.post(f'{self.server_url}/Collections',headers={"X-Emby-Token": self.api_key}, params={"name": list_name})
            collection_id = res2.json()["Id"]
        return collection_id


    def add_item_to_collection(self, collection_id: str, item, year_filter: bool = True):
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
        # if year_filter:
        #     params["year"] = item["release_year"]

        res = requests.get(f'{self.server_url}/Users/{self.user_id}/Items',headers={"X-Emby-Token": self.api_key}, params=params)

        # Check if there's an exact imdb_id match first
        match = None
        if "imdb_id" in item:
            for result in res.json()["Items"]:
                if result["ProviderIds"].get("Imdb", None) == item["imdb_id"]:
                    match = result
                    break

        # Check if there's a year match
        if match is None and year_filter:
            for result in res.json()["Items"]:
                if result.get("ProductionYear", None) == item["release_year"]:
                    match = result
                    break

        # Otherwise, just take the first result
        if match is None and len(res.json()["Items"]) == 1:
            match = res.json()["Items"][0]

        if match is None:
            logger.warning(f"Item {item['title']} not found in jellyfin")
        else:
            try:
                item_id = res.json()["Items"][0]["Id"]
                requests.post(f'{self.server_url}/Collections/{collection_id}/Items?ids={item_id}',headers={"X-Emby-Token": self.api_key})
                logger.info(f"Added {item['title']} to collection")
            except json.decoder.JSONDecodeError:
                logger.error(f"Error adding {item['title']} to collection - JSONDecodeError")
                return

    def clear_collection(self, collection_id: str):
        '''Clears a collection by removing all items from it'''
        res = requests.get(f'{self.server_url}/Users/{self.user_id}/Items',headers={"X-Emby-Token": self.api_key}, params={"Recursive": "true", "parentId": collection_id})
        ids = [item["Id"] for item in res.json()["Items"]]
        requests.delete(f'{self.server_url}/Collections/{collection_id}/Items',headers={"X-Emby-Token": self.api_key}, params={"ids": ",".join(ids)})
        logger.info(f"Cleared collection {collection_id}")
