'''Make collections from Letterboxd lists'''
import requests
import html
import json
import configparser

from utils import get_library_id, request_repeat_get, request_repeat_post

# Load Config
config = configparser.ConfigParser()
config.read('config.ini')
server_url = config["main"]["server_url"]
user_id = config["main"]["user_id"]
letterboxd_list_ids = json.loads(config["main"]["letterboxd_list_ids"])
headers = {'X-Emby-Token': config["main"]["jellyfin_api_key"]}

params = {
    "enableTotalRecordCount": "false",
    "enableImages": "false",
    "Recursive": "true"
}

print("Getting collections list...")
collections_id = get_library_id("Collections", headers=headers)
params2 = params.copy()
params2["includeItemTypes"] = "BoxSet"
res = requests.get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params2)
collections = {r["Name"]:r["Id"] for r in res.json()["Items"]}

for list_id in letterboxd_list_ids:
    # Parse letterboxd page
    res = requests.get(f'https://letterboxd.com/{list_id}/detail/by/release-earliest')
    list_name = html.unescape(res.text.split('<h1 class="title-1 prettify" itemprop="title">')[1].split("</h1>")[0]).strip()

    print()
    print()
    print("*******************************")

    collection_id = None
    for collection in collections:
        if list_name == collection:
            print("found", list_name, collections[collection])
            collection_id = collections[collection]
            break

    if collection_id is None:
        print(f"Creating {list_name}...")
        res2 = request_repeat_post(f'{server_url}/Collections',headers=headers, params={"name": list_name})
        collection_id = res2.json()["Id"]

    print()
    for movie in res.text.split('film-detail-content">')[1:]:
        movie_title = movie.split('<a href="')[1].split('>')[1].split("<")[0]
        movie_year = movie.split('metadata">')[1].split('<a href="')[1].split('>')[1].split("<")[0]
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
        except json.decoder.JSONDecodeError:
            print("JSON decode error - skipping")
