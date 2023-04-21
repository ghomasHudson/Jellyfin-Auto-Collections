'''Make collections from IMDB charts'''
import requests
import html
import json
import simplejson
import configparser
import re
import datetime


from utils import request_repeat_get, request_repeat_post, find_collection_with_name_or_create, get_all_collections

# Load Config
config = configparser.ConfigParser()
config.read('config.ini')
server_url = config["main"]["server_url"]
user_id = config["main"]["user_id"]
imdb_chart_tv_ids = json.loads(config["main"]["imdb_chart_tv_ids"])
headers = {'X-Emby-Token': config["main"]["jellyfin_api_key"]}

params = {
    "enableTotalRecordCount": "false",
    "enableImages": "false",
    "Recursive": "true"
}

# Find list of all collections
collections = get_all_collections(headers=headers)

for imdb_chart_tv_id in imdb_chart_tv_ids:
    # Parse each IMDB list page
    print()
    print()

    res = requests.get(f'https://www.imdb.com/chart/{imdb_chart_tv_id}')
    list_name = html.unescape(res.text.split('<h1 class="header">')[1].split("</h1>")[0])
    collection_id = find_collection_with_name_or_create(list_name, collections, headers=headers)
    print("************************************************")
    print()

    # Add to collection
    text = res.text.split('ab_widget',1)[1].split('<tbody', 1)[1]
    for series in text.split("<tr>")[2:]:
        series_title = series.split("titleColumn\">")[1].split(">")[1].split("<")[0]
        if "secondaryInfo\">(" in series:
            series_year = series.split("secondaryInfo\">(")[1].split(")")[0]
        else:
            # Handle boxoffice where year is not given
            series_year = datetime.date.today().year

        params2 = params.copy()
        params2["searchTerm"] = series_title
        params2["years"] = series_year
        params2["includeItemTypes"] = "Series"
        res2 = request_repeat_get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params2)
        try:
            if len(res2.json()["Items"]) > 0:
                series_id = res2.json()["Items"][0]["Id"]
                request_repeat_post(f'{server_url}/Collections/{collection_id}/Items?ids={series_id}',headers=headers)
                print("Added", series_title, series_id)
            else:
                print("Can't find", series_title)
        except simplejson.errors.JSONDecodeError:
            print("JSON decode error - skipping")
