import json
import requests
from lxml import html

from utils import load_app_config, find_collection_with_name_or_create, get_all_collections

def update_top_1000_movies_collection(app_config: dict):
'''Gets top 1000 movies from the TSPDT masterlist'''
    server_url = app_config["server_url"]
    api_key= app_config["api_key"]
    user_id = app_config["user_id"]

    headers = {'X-Emby-Token': api_key}

    collection_name = "TSPDT Top 1000 Greatest"

    # Find list of all collections
    collections = get_all_collections(server_url, user_id, headers=headers)
    collection_id = find_collection_with_name_or_create(server_url, collection_name, collections, headers=headers)

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
            
if __name__ == "__main__":
    update_top_1000_movies_collection()
