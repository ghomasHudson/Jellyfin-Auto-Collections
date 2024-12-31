import requests
import urllib.parse
from loguru import logger

class JellyseerrClient:
    def __init__(self, server_url: str, api_key: str):
        # Fix common url issues
        if server_url.endswith("/"):
            server_url = server_url[:-1]  # Remove trailing slash 
        if not server_url.endswith("/api/v1"):
            server_url += "/api/v1"
        self.server_url = server_url
        self.api_key = api_key

        # Check if server is reachable
        try:
            r = requests.get(self.server_url + "/status")
            if r.status_code != 200:
                raise Exception("Jellyseerr Server is not reachable")
        except requests.exceptions.ConnectionError:
            raise Exception("Jellyseerr Server is not reachable")

        # Check if api key is valid
        r = requests.get(f"{self.server_url}/auth/me")


    def make_request(self, item):
        '''Request item from jellyseerr'''

        # Search for item
        r = requests.get(f"{self.server_url}/search", params={
            "query": urllib.parse.quote_plus(item["title"])
        }, headers={
            "X-Api-Key": self.api_key
        })
        
        # Find matching item
        mediaId = None
        for result in r.json()["results"]:
            # Try IMDB match first
            if "mediaInfo" in result and "ImdbId" in result["mediaInfo"]:
                imdb_id = result["mediaInfo"]["ImdbId"]
                if imdb_id == item["imdb_id"]:
                    mediaId = result["id"]
                    logger.debug(f"Found exact IMDB match for {item['title']}")
                    break
            elif "releaseDate" in result:
                # Try year match
                release_year = result["releaseDate"].split("-")[0]
                if release_year == str(item["release_year"]):
                    mediaId = result["id"]
                    logger.debug(f"Found year match for {item['title']}")
                    break

        # Request item if not found
        if mediaId is not None:
            if "mediaInfo" not in result or result["mediaInfo"]["jellyfinMediaId"] is None:
                # If it's not already in Jellyfin
                # Request item
                r = requests.post(f"{self.server_url}/request", json={
                    "mediaType": result["mediaType"],
                    "mediaId": mediaId,
                }, headers={
                    "X-Api-Key": self.api_key
                })
                logger.info(f"Requested {item['title']} from Jellyseerr")



if __name__ == "__main__":
    from pyaml_env import parse_config
    config = parse_config("/home/thomas/Documents/Jellyfin-Auto-Collections/config.yaml", default_value=None)

    client = JellyseerrClient(
        server_url=config["jellyseerr"]["server_url"],
        api_key=config["jellyseerr"]["api_key"]
    )
    client.make_request({
        "title": "The Matrix",
        "imdb_id": "tt0133093",
        "release_year": 1999
    })
