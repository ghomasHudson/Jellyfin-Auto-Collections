import requests
import configparser
import json
import threading
from queue import Queue
import sqlite3

# Utility functions
from utils import request_repeat_get, find_collection_with_name_or_create, get_all_collections

# Load Config
config = configparser.ConfigParser()
config.read('config.ini')
server_url = config["main"]["server_url"]
user_id = config["main"]["user_id"]
headers = {'X-Emby-Token': config["main"]["jellyfin_api_key"]}
trakt_api_key = config["main"]["trakt_client_id"]
db_path = config["main"]["db_path"]

params = {
    "enableTotalRecordCount": "false",
    "enableImages": "false",
    "Recursive": "true"
}

def initialize_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_ids (
            trakt_id INTEGER,
            imdb_id TEXT,
            tvdb_id TEXT,
            jellyfin_id TEXT,
            title TEXT,
            year INTEGER,
            media_type TEXT,
            PRIMARY KEY (trakt_id, imdb_id)
        )
    ''')
    conn.commit()
    conn.close()

def is_id_processed(db_path, trakt_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT trakt_id FROM processed_ids WHERE trakt_id = ?", (trakt_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_processed_id(db_path, trakt_id, tvdb_id, jellyfin_id, title, year, media_type):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO processed_ids (trakt_id, tvdb_id, jellyfin_id, title, year, media_type) VALUES (?, ?, ?, ?, ?, ?)", 
        (trakt_id, tvdb_id, jellyfin_id, title, year, media_type)
    )
    conn.commit()
    conn.close()

def request_repeat_post(url, headers, data=None):
    for _ in range(3):  # Try up to 3 times
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response
    response.raise_for_status()

def get_trakt_data(url, media_type, limit=100):
    collected_data = []
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": trakt_api_key
    }
    page = 1
    while True:
        paginated_url = f"{url}?page={page}&limit={limit}"
        response = requests.get(paginated_url, headers=headers)
        data = response.json()

        if data and isinstance(data[0], dict) and media_type in data[0]:
            collected_data.extend(item[media_type] for item in data)
        else:
            collected_data.extend(data)

        if len(data) < limit or len(collected_data) >= limit:
            break
        page += 1
    return collected_data[:limit]

def add_to_collection(queue, collection_id, media_type, db_path):
    while not queue.empty():
        media = queue.get()
        media_id = media["ids"]["trakt"]
        imdb_id = media["ids"].get("imdb", "")
        tvdb_id = media["ids"].get("tvdb", "")
        title = media["title"]
        year = media.get("year", None)
        jellyfin_id = ""

        # Check if the ID has been processed for Jellyfin search
        if is_id_processed(db_path, media_id):
            print(f"Already processed {title} (ID: {media_id}) in Jellyfin search")
        else:
            # Perform Jellyfin search
            params2 = params.copy()
            params2["searchTerm"] = title
            if year:
                params2["years"] = str(year)
            params2["includeItemTypes"] = ["Series"] if media_type == "show" else ["Movie"]

            res2 = request_repeat_get(f'{server_url}/Users/{user_id}/Items', headers=headers, params=params2)
            if len(res2.json()["Items"]) > 0:
                jellyfin_id = res2.json()["Items"][0]["Id"]
                print(f"Found {title} in Jellyfin with ID {jellyfin_id}")
            else:
                print(f"Can't find {title} in Jellyfin")
                jellyfin_id = ""

            # Update database with the new processed media item
            add_processed_id(db_path, media_id, tvdb_id, jellyfin_id, title, year, media_type)

        # Add to collection regardless of whether it was newly found or already processed
        if jellyfin_id:
            request_repeat_post(f'{server_url}/Collections/{collection_id}/Items?ids={jellyfin_id}', headers=headers)
            print(f"Added {title} (ID: {jellyfin_id}) to collection")

        queue.task_done()

def remove_unmatched_items_from_collection(collection_id, trakt_ids, headers):
    # Fetch current items in the Jellyfin collection
    response = requests.get(f'{server_url}/Collections/{collection_id}/Items', headers=headers)
    jellyfin_items = response.json()["Items"]

    # Determine items to remove from Jellyfin collection
    for item in jellyfin_items:
        trakt_id = item["CustomFields"]["TraktID"]  # Adjust based on how Trakt ID is stored
        if trakt_id not in trakt_ids:
            # Remove the item from Jellyfin collection
            jellyfin_id = item["Id"]
            requests.delete(f'{server_url}/Collections/{collection_id}/Items?ids={jellyfin_id}', headers=headers)
            print(f"Removed {item['Name']} (ID: {jellyfin_id}) from collection")

def process_media(media_list, collection_name, media_type, db_path):
    collections = get_all_collections(headers=headers)
    collection_id = find_collection_with_name_or_create(collection_name, collections, headers=headers)

    queue = Queue()
    for media in media_list:
        queue.put(media)

    threads = []
    for _ in range(10):  # Number of threads
        thread = threading.Thread(target=add_to_collection, args=(queue, collection_id, media_type, db_path))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

# Initialize the database
initialize_db(db_path)

# Fetch Trakt trending and popular movies and shows
trending_movies = get_trakt_data("https://api.trakt.tv/movies/trending", "movie", 100)
popular_movies = get_trakt_data("https://api.trakt.tv/movies/popular", "movie", 100)
trending_shows = get_trakt_data("https://api.trakt.tv/shows/trending", "show", 100)
popular_shows = get_trakt_data("https://api.trakt.tv/shows/popular", "show", 100)

# Process movies and shows
process_media(trending_movies, "Trending Movies", "movie", db_path)
process_media(popular_movies, "Popular Movies", "movie", db_path)
process_media(trending_shows, "Trending Shows", "show", db_path)
process_media(popular_shows, "Popular Shows", "show", db_path)
