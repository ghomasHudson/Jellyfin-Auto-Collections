import requests
import html
import json
import html

from utils import load_app_config, request_repeat_get, request_repeat_post, find_collection_with_name_or_create, get_all_collections

def get_collection_data_from_letterboxd_list(list_id: str):
    '''Get all movies from a Letterboxd list'''
    page_number = 1
    movies = []
    list_name = None
    
    while True:
        request_base = f'https://letterboxd.com/{list_id}/detail/by/release-earliest/page/{page_number}/'
        res = requests.get(request_base)
        
        if list_name is None:
            list_name = html.unescape(res.text.split('<h1 class="title-1 prettify">')[1].split("</h1>")[0]).strip()
        page_movies = res.text.split('film-detail-content">')[1:]
        
        if len(page_movies) == 0:
            return {"list_name": list_name, "movies": movies}
        
        movies += page_movies
        page_number += 1

def update_letterboxd_list_collections(app_config: dict):
    '''Make collections from Letterboxd lists'''
    server_url = app_config["server_url"]
    api_key= app_config["api_key"]
    user_id = app_config["user_id"]
    letterboxd_list_ids = app_config["letterboxd_list_ids"]

    headers = {'X-Emby-Token': api_key}

    params = {
        "enableTotalRecordCount": "false",
        "enableImages": "false",
        "Recursive": "true"
    }

    collections = get_all_collections(server_url, user_id, headers=headers)

    for list_id in letterboxd_list_ids:
        # Parse letterboxd page
        print()
        print()
        
        collection_data = get_collection_data_from_letterboxd_list(list_id)
        list_name = collection_data["list_name"]
        movies = collection_data["movies"]
        
        collection_id = find_collection_with_name_or_create(server_url, list_name, collections, headers=headers)
        
        print("************************************************")
        print()

        for movie in movies:
            movie_title = html.unescape(movie.split('<a href="')[1].split('>')[1].split("<")[0])
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

if __name__ == "__main__":
    app_config = load_app_config()
    update_letterboxd_list_collections(app_config)