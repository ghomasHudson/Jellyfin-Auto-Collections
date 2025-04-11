import bs4
import requests
import json
from utils.base_plugin import ListScraper

#from arrapi import SonarrAPI, RadarrAPI

class Arr(ListScraper):
    '''Generate collections based on Jellyfin API queries'''

    _alias_ = 'arr'

    def get_list(list_id, config=None):
        '''Call arr API'''

        items = []
        for server_config in config["server_configs"]:
            server_params = {"apikey": server_config["api_key"]}

            # Get tag id
            r = requests.get(server_config["base_url"] + "/api/v3/tag", params=server_params)
            tag_id = None
            for tag in r.json():
                if tag["label"] == list_id:
                    tag_id = tag["id"]
                    break
            if tag_id is None:
                continue

            # Get tag details
            r = requests.get(server_config["base_url"] + f"/api/v3/tag/detail/{tag_id}", params=server_params)

            # Get item details
            for item_id in r.json().get("movieIds", []):
                item_r = requests.get(server_config["base_url"] + f"/api/v3/movie/{item_id}", params=server_params)
                item_r = item_r.json()
                items.append({
                    "title": item_r["title"],
                    "release_year": item_r["year"],
                    "media_type": "movie",
                    "imdb_id": item_r["imdbId"]
                })

            for item_id in r.json().get("seriesIds", []):
                item_r = requests.get(server_config["base_url"] + f"/api/v3/series/{item_id}", params=server_params)
                item_r = item_r.json()
                items.append({
                    "title": item_r["title"],
                    "release_year": item_r["year"],
                    "media_type": "show",
                    "imdb_id": item_r["imdbId"]
                })


        return {
            "name": list_id.replace("_", " ").title(),
            "description": f"{list_id} tag from arr server",
            "items": items
        }
