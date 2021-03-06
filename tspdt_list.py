'''Gets top 1000 movies from the TSPDT masterlist'''
import json
import requests
from lxml import html
import configparser

from utils import find_collection_with_name_or_create, get_all_collections

# Load Config
config = configparser.ConfigParser()
config.read('config.ini')
server_url = config["main"]["server_url"]
user_id = config["main"]["user_id"]
headers = {'X-Emby-Token': config["main"]["jellyfin_api_key"]}
collection_name = "TSPDT Top 1000 Greatest"


# Find list of all collections
collections = get_all_collections(headers=headers)
collection_id = find_collection_with_name_or_create(collection_name, collections, headers=headers)

res = requests.get("https://www.theyshootpictures.com/gf1000_all1000films_table.php")
tree = html.fromstring(res.text)
for row in list(tree.xpath("//tr"))[1:]:
    values = row.xpath("./td/text()")
    movie_title = values[2]
    for suffix in ["The", "A", "La"]:
        if movie_title.endswith(", "+suffix):
            movie_title = suffix + " " + movie_title[:-5].strip()
    params = {
        "searchTerm": movie_title,
        "years": values[4],
        "includeItemTypes": "Movie",
        "Recursive": "true",
        "enableTotalRecordCount": "false",
        "enableImages": "false",
    }
    res = requests.get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params)
    try:
        if len(res.json()["Items"]) > 0:
            movie_id = res.json()["Items"][0]["Id"]
            requests.post(f'{server_url}/Collections/{collection_id}/Items?ids={movie_id}',headers=headers)
            print("Added", movie_title, movie_id)
        else:
            print("Can't find", movie_title)
    except json.decoder.JSONDecodeError:
        print("JSON decode error - skipping")
