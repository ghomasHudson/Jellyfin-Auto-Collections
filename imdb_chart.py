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
imdb_chart_ids = json.loads(config["main"]["imdb_chart_ids"])
headers = {'X-Emby-Token': config["main"]["jellyfin_api_key"]}

params = {
    "enableTotalRecordCount": "false",
    "enableImages": "false",
    "Recursive": "true"
}

# Find list of all collections
collections = get_all_collections(headers=headers)

for imdb_chart_id in imdb_chart_ids:
    # Parse each IMDB list page
    print()
    print()

    res = requests.get(f'https://www.imdb.com/chart/{imdb_chart_id}')
    list_name = html.unescape(res.text.split('<h1 class="header">')[1].split("</h1>")[0])
    collection_id = find_collection_with_name_or_create(list_name, collections, headers=headers)
    print("************************************************")
    print()

    # Add to collection
    text = res.text.split('ab_widget',1)[1].split('<tbody', 1)[1]
    for movie in text.split("<tr>")[2:]:
        movie_title = movie.split("titleColumn\">")[1].split(">")[1].split("<")[0]
        if "secondaryInfo\">(" in movie:
            movie_year = movie.split("secondaryInfo\">(")[1].split(")")[0]
        else:
            # Handle boxoffice where year is not given
            movie_year = datetime.date.today().year

        params2 = params.copy()
        params2["searchTerm"] = movie_title
        params2["years"] = movie_year
        params2["includeItemTypes"] = "Movie"
        res2 = request_repeat_get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params2)
        try:
            if len(res2.json()["Items"]) > 0:
                movie_id = res2.json()["Items"][0]["Id"]
                request_repeat_post(f'{server_url}/Collections/{collection_id}/Items?ids={movie_id}',headers=headers)
                print("Added", movie_title, movie_id)
            else:
                print("Can't find", movie_title)
        except simplejson.errors.JSONDecodeError:
            print("JSON decode error - skipping")
