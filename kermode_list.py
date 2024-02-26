'''Adds videos with have a BFI 'Mark Kermode Reviews' video to a collection'''
import requests

from utils import load_env_config, find_collection_with_name_or_create, get_all_collections

env_config = load_env_config()
server_url = env_config["server_url"]
api_key= env_config["api_key"]
user_id = env_config["user_id"]

headers = {'X-Emby-Token': api_key}

# Find the mark kermode collection (or make one)
collection_name = "Mark Kermode Introduces"
collections = get_all_collections(server_url, user_id, headers=headers)
kermode_collection_id = find_collection_with_name_or_create(server_url, collection_name, collections, headers=headers)

params = {
    "hasSpecialFeature": "true",
    "enableTotalRecordCount": "false",
    "enableImages": "false",
    "Recursive": "true"
}
res = requests.get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params)
for item in res.json()["Items"]:
    # Find out if movie has a kermode intro
    has_kermode = False
    res = requests.get(f'{server_url}/Users/{user_id}/Items/{item["Id"]}/SpecialFeatures',headers=headers)
    for feature in res.json():
        if "Mark Kermode" in feature["Name"]:
            has_kermode = True
            break

    if has_kermode:
        # Add to "Mark Kermode Introduces" Collection
        print("Added", item["Name"])
        res = requests.post(f'{server_url}/Collections/{kermode_collection_id}/Items?ids={item["Id"]}',headers=headers)
