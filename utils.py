'''Handy utility functions for other scripts'''
import requests
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
server_url = config["main"]["server_url"]
user_id = config["main"]["user_id"]


def get_all_collections(headers=None):
    '''Find list of all collections'''
    params = {
        "enableTotalRecordCount": "false",
        "enableImages": "false",
        "Recursive": "true",
        "includeItemTypes": "BoxSet"
    }
    print("Getting collections list...")
    res = requests.get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params)
    collections = {r["Name"]:r["Id"] for r in res.json()["Items"]}
    return collections

def find_collection_with_name_or_create(list_name, collections, headers=None):
    '''Find a collection with name `list_name` or create one if
    it doesn't exist'''
    # Try and find the collection with name `list_name`
    collection_id = None
    for collection in collections:
        if list_name == collection:
            print("found", list_name, collections[collection])
            collection_id = collections[collection]
            break

    if collection_id is None:
        # Collection doesn't exist -> Make a new one
        print(f"Creating {list_name}...")
        res2 = request_repeat_post(f'{server_url}/Collections',headers=headers, params={"name": list_name})
        collection_id = res2.json()["Id"]
    return collection_id



def get_library_id(library_name, headers=None):
    '''Get the library named library_name'''
    r = requests.get(f'{server_url}/Users/{user_id}/Views',headers=headers)
    r.raise_for_status()
    libraries = r.json().get('Items')
    library_id = [ x.get('Id') for x in libraries
                    if x.get('Name') == library_name]
    if library_id:
        library_id = library_id[0]
    return library_id


def request_repeat_get(url, headers=None, params=None):
    '''Do a GET request, repeat if err'''
    while True:
        try:
            res = requests.get(url, headers=headers, params=params)
            return res
        except:
            pass


def request_repeat_post(url, headers=None, params=None):
    '''Do a POST request, repeat if err'''
    while True:
        try:
            res = requests.post(url, headers=headers, params=params)
            return res
        except:
            pass
