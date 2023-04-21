'''Make collections from IMDB lists'''
import requests
import html
import json
import configparser

from utils import request_repeat_get, request_repeat_post, find_collection_with_name_or_create, get_all_collections

# Load Config
config = configparser.ConfigParser()
config.read('config.ini')
server_url = config["main"]["server_url"]
user_id = config["main"]["user_id"]
imdb_list_tv_ids = json.loads(config["main"]["imdb_list_tv_ids"])
headers = {'X-Emby-Token': config["main"]["jellyfin_api_key"]}

params = {
    "enableTotalRecordCount": "false",
    "enableImages": "false",
    "Recursive": "true"
}

# Find list of all collections
collections = get_all_collections(headers=headers)

for imdb_list_tv_id in imdb_list_tv_ids:
    # Parse each IMDB list page
    print()
    print()
    res = requests.get(f'https://www.imdb.com/list/{imdb_list_tv_id}')
    list_name = html.unescape(res.text.split('<h1 class="header list-name">')[1].split("</h1>")[0])
    collection_id = find_collection_with_name_or_create(list_name, collections, headers=headers)
    print("************************************************")
    print()

    # Add to collection
    for series in res.text.split("lister-item-header")[1:]:
        series_title = series.split('<a href="')[1].split('>')[1].split("<")[0]
        params2 = params.copy()
        params2["searchTerm"] = series_title
        params2["includeItemTypes"] = "Series"
        res2 = request_repeat_get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params2)
        try:
            if len(res2.json()["Items"]) > 0:
                series_id = res2.json()["Items"][0]["Id"]
                request_repeat_post(f'{server_url}/Collections/{collection_id}/Items?ids={series_id}',headers=headers)
                print("Added", series_title, series_id)
            else:
                print("Can't find", series_title)
        except json.decoder.JSONDecodeError:
            print("JSON decode error - skipping")
