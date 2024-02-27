import requests
import html
import json
import csv

from utils import load_app_config, request_repeat_get, request_repeat_post, find_collection_with_name_or_create, get_all_collections

def update_imdb_list_collections(app_config: dict):
'''Make collections from IMDB lists'''
    server_url = app_config["server_url"]
    api_key= app_config["api_key"]
    user_id = app_config["user_id"]
    disable_tv_year_filter = app_config["disable_tv_year_filter"]
    imdb_list_ids = app_config["imdb_list_ids"]

    headers = {'X-Emby-Token': api_key}

    params = {
        "enableTotalRecordCount": "false",
        "enableImages": "false",
        "Recursive": "true"
    }

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

    # Find list of all collections
    collections = get_all_collections(server_url, user_id, headers=headers)

    for imdb_list_id in imdb_list_ids:
        # Parse each IMDB list page
        print()
        print()
        res = requests.get(f'https://www.imdb.com/list/{imdb_list_id}')
        list_name = html.unescape(res.text.split('<h1 class="header list-name">')[1].split("</h1>")[0])
        collection_id = find_collection_with_name_or_create(server_url, list_name, collections, headers=headers)
        print("************************************************")
        print()

        res = requests.get(f'https://www.imdb.com/list/{imdb_list_id}/export')
        reader = csv.DictReader(res.text.split("\n"))
        for item in reader:
            params2 = params.copy()
            params2["searchTerm"] = item["Title"]
            params2["years"] = item["Year"]

            if item["Title Type"] == "tvEpisode" and ": " in item["Title"]:
                params2["searchTerm"] = item["Title"].split(": ", 1)[1]

            if disable_tv_year_filter and item["Title Type"] in ["tvSeries", "tvMiniSeries"]:
                del params2["years"]

            params2["includeItemTypes"] = imdb_to_jellyfin_type_map[item["Title Type"]]
            res2 = request_repeat_get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params2)
            try:
                if len(res2.json()["Items"]) > 0:
                    item_id = res2.json()["Items"][0]["Id"]
                    request_repeat_post(f'{server_url}/Collections/{collection_id}/Items?ids={item_id}',headers=headers)
                    print("Added", item["Title"], item_id)
                else:
                    print("Can't find", item["Title"])
            except json.decoder.JSONDecodeError:
                print("JSON decode error - skipping")

if __name__ == "__main__":
    update_imdb_list_collections()