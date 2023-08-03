'''Make collections from IMDB lists'''
import requests
import html
import json
import configparser
import csv

from utils import request_repeat_get, request_repeat_post, find_collection_with_name_or_create, get_all_collections

# Load Config
config = configparser.ConfigParser()
config.read('config.ini')
server_url = config["main"]["server_url"]
user_id = config["main"]["user_id"]
imdb_list_ids = json.loads(config["main"]["imdb_list_ids"])
headers = {'X-Emby-Token': config["main"]["jellyfin_api_key"]}

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
collections = get_all_collections(headers=headers)

for imdb_list_id in imdb_list_ids:
    # Parse each IMDB list page
    print()
    print()
    res = requests.get(f'https://www.imdb.com/list/{imdb_list_id}')
    list_name = html.unescape(res.text.split('<h1 class="header list-name">')[1].split("</h1>")[0])
    collection_id = find_collection_with_name_or_create(list_name, collections, headers=headers)
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

        if config.getboolean("main", "disable_tv_year_filter", fallback=False) and item["Title Type"] in ["tvSeries", "tvMiniSeries"]:
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
