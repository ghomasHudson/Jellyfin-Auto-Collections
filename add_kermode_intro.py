'''Downloads BFI 'Mark Kermode Reviews' video to related films'''
#
# Requires the movies_dir path to be set to your movies library
# This will miss some movies, but shouldn't match incorrectly.
#
import os
import glob
import json
import re
import requests

env_config = load_env_config()
server_url = env_config["server_url"]
api_key= env_config["api_key"]
user_id = env_config["user_id"]
movies_dir = env_config["movies_dir"]

headers = {'X-Emby-Token': api_key}

def find_movie(title, year=None):
    params = {
        "searchTerm": title,
        "includeItemTypes": "Movie",
        "Recursive": "true",
        "enableTotalRecordCount": "false",
        "enableImages": "false",
    }
    if year is not None:
        params["years"] = year
    while True:
        try:
            res = requests.get(f'{server_url}/Users/{user_id}/Items',headers=headers, params=params)
            if len(res.json()["Items"]) > 0:
                return res.json()["Items"][0]
            else:
                return None
        except:
            pass

# Download playlist titles - delete this os.path.exists check to update playlist
if not os.path.exists("/tmp/bfi"):
    os.mkdir("/tmp/bfi")
    os.system("cd /tmp/bfi && youtube-dl --ignore-errors --write-info-json --skip-download 'https://www.youtube.com/playlist?list=PLXvkgGofjDzhx-h7eexfVbH3WslWrBXE9'")

for fn in glob.glob("/tmp/bfi/*.json"):
    data = json.load(open(fn))
    
    # Extract movie name and (hopefully) year from youtube video title
    movie_title = data["title"]
    movie_title = movie_title.split("|")[0]
    movie_title = movie_title.replace("BFI Player", "")
    movie_title = re.split(r'Reviews|reviews|reviews:|introduces', movie_title)[-1].strip()
    movie_title = movie_title.replace("[subtitled]", "").strip()
    year_search = re.search(r'\((.*?)\)',movie_title)
    movie_year = None
    if year_search is not None:
        movie_year = year_search.group(1)
    movie_title = re.sub(r'\(.+\)', '', movie_title).strip()
    movie = None
    search_str = movie_title
    
    # Sanity check in case year is a string
    if movie_year is not None and not movie_year.isnumeric():
        movie_year = None
        
    # Try and find a matching movie in the database
    while movie is None:
        movie = find_movie(search_str, movie_year)
        if " " not in search_str:
            break
        search_str = search_str.split(" ", 1)[-1]
        
    if movie is not None:
        if movie["Name"].lower() not in movie_title.lower():
            movie = None

    # Download Kermode intro if it doesn't already exist
    print(movie_title, movie_year)
    if movie is not None:
        movie = requests.get(f'{server_url}/Users/{user_id}/Items/{movie["Id"]}',headers=headers).json()
        movie_filepath = f'{movies_dir}/{movie["Path"].split("/")[-2]}/extras'
        if not os.path.exists(movie_filepath):
            os.mkdir(movie_filepath)
        if len(glob.glob(movie_filepath+"/Mark Kermode*")) == 0:
            print("\tDownloading", movie["Name"], "intro", movie["Id"])
            os.system("youtube-dl -i https://youtube.com/watch?v="+data["id"] + " --output '" + movie_filepath + "/Mark Kermode Introduces'")
        else:
            print("\tIntro already Exists")
