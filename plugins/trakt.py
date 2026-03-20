import json
from utils.base_plugin import ListScraper
import bs4
import os
import requests
from loguru import logger
import time

class Trakt(ListScraper):

    _alias_ = 'trakt'
    _access_token_file = '.trakt_access_token'

    _chart_types = {
            "movies/trending": {
                "title": "Trending Movies",
                "description": "The most watched movies right now."
            },
            "movies/popular": {
                "title": "Popular Movies",
                "description": "The most popular movies of all time."
            },
            "movies/favorited": {
                "title": "Most Favorited Movies",
                "description": "The most favorited movies for the last week."
            },
            "movies/watched": {
                "title": "Most Watched Movies",
                "description": "The most watched movies for the last week."
            },
            "movies/collected": {
                "title": "Most Collected Movies",
                "description": "The most collected movies for the last week."
            },
            "movies/played": {
                "title": "Most Played Movies",
                "description": "The most played movies for the last week."
            },
            "movies/anticipated": {
                "title": "Most Anticipated Movies",
                "description": "The most anticipated movies based on the number of lists a movie appears on."
            },
            "movies/boxoffice": {
                "title": "Box Office Movies",
                "description": "The top 10 movies in the US box office last weekend."
            },
            "shows/trending": {
                "title": "Trending Shows",
                "description": "The most watched shows right now."
            },
            "shows/popular": {
                "title": "Popular Shows",
                "description": "The most popular shows of all time. Popularity is calculated using the rating percentage and the number of ratings."
            },
            "shows/favorited": {
                "title": "Most Favorited Shows",
                "description": "The most favorited shows for the last week."
            },
            "shows/watched": {
                "title": "Most Watched Shows",
                "description": "The most watched shows for the last week."
            },
            "shows/collected": {
                "title": "Most Collected Shows",
                "description": "The most collected shows for the last week."
            },
            "shows/played": {
                "title": "Most Played Shows",
                "description": "The most played (a single user can watch multiple episodes multiple times) shows for the last week."
            },
            "shows/anticipated": {
                "title": "Most Anticipated Shows",
                "description": "The most anticipated shows based on the number of lists a show appears on."
            }
        }



    def _get_auth_token(config):
        '''Get the authentication token for the Trakt API'''

        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": config["client_id"]
        }

        if os.path.exists(Trakt._access_token_file):
            # If we have already authenticated, read the access token from the file
            with open(Trakt._access_token_file, 'r') as f:
                access_token = f.read()
            logger.debug("Existing access token found")
        else:
            # If we have not authenticated, get the access token from the user
            r = requests.post("https://api.trakt.tv/oauth/device/code", headers=headers, json={"client_id": config["client_id"]})
            
            # Ensure the API request was successful to prevent JSON parsing crashes.
            # This safely catches errors like 429 (Rate Limit) or 401 (Bad Client ID).
            if r.status_code != 200:
                logger.error(f"Failed to get device code from Trakt! Status: {r.status_code}")
                return None
                
            device_code = r.json()["device_code"]
            user_code = r.json()["user_code"]
            interval = r.json()["interval"]

            # AUTHENTICATION PROMPT
            logger.info("===================================================")
            logger.info("🛑 AUTHENTICATION WITH TRAKT API REQUIRED 🛑")
            logger.info(f"Please visit: {r.json()['verification_url']}")
            logger.info(f"Enter this device code: {user_code}")
            logger.info("===================================================")

            # Poll the API until the user has authenticated
            while True:
                r = requests.post("https://api.trakt.tv/oauth/device/token", headers=headers, json={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": device_code
                })
                if r.status_code == 200:
                    break
                time.sleep(interval)

            access_token = r.json()["access_token"]

            # Save the access token to a file
            with open(Trakt._access_token_file, 'w') as f:
                f.write(access_token)
            logger.info("Successfully authenticated with Trakt API")
        return access_token


    def get_list(list_id, config=None):

        # Force user input to lowercase to prevent case-sensitive crashes
        list_id = str(list_id).lower()

        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": config["client_id"]
        }

        access_token = Trakt._get_auth_token(config)
        # If authentication failed, return an empty list structure
        if not access_token:
            return {"name": "Error", "description": "Auth Failed", "items": []}
            
        headers["Authorization"] = f"Bearer {access_token}"
        logger.debug("Access token loaded")
        item_types = "movie" # Default fallback

        if list_id.startswith("users/"):
            logger.debug(f"Trakt User list via slug: {list_id}")
            # Get Metadata
            r = requests.get(f"https://api.trakt.tv/{list_id}", headers=headers)
            if r.status_code != 200:
                logger.error(f"Trakt user list '{list_id}' not found! Status: {r.status_code}")
                return {"name": "Error", "description": "List Not Found", "items": []}
            
            list_data = r.json()
            list_name = list_data.get("name", "User List")
            description = list_data.get("description", "")
            
            # Get Items
            r = requests.get(f"https://api.trakt.tv/{list_id}/items", headers=headers)
            items_data = r.json() if r.status_code == 200 else []
        elif list_id.startswith("shows/") or list_id.startswith("movies/"):
            # Chart
            logger.debug("Trakt chart list")
            # Retrieve collection metadata based on the chart type.
            list_name = Trakt._chart_types[list_id]["title"]
            description = Trakt._chart_types[list_id]["description"]
            # Establish the default media type for parsing items below. (Fallback if Trakt doesnt provide)
            if list_id.startswith("shows/"):
                item_types = "show"
            else:
                item_types = "movie"

            current_page = 1
            items_data = []
            max_items = config.get("max_items") if config else None

            while True:
                r = requests.get(f"https://api.trakt.tv/{list_id}?page={current_page}", headers=headers)
                # Catch formal API errors (e.g., 429 Too Many Requests, 500 Server Error).
                if r.status_code != 200:
                    logger.error(f"Trakt API error (Status {r.status_code}) on page {current_page}.")
                    break
                # Safely try to read the JSON. This catches edge cases where Trakt returns a 200 OK status but serves an HTML Cloudflare page instead.
                try:
                    page_data = r.json()
                except Exception as e:
                    logger.error(f"Trakt returned invalid JSON on page {current_page}. Stopping pagination.")
                    break

                items_data += page_data
                page_count = int(r.headers.get("X-Pagination-Page-Count", 1))
                # Massive lists (like movies/watched) have tens of thousands of pages. Warn the user if they didn't set a limit so they know why it takes hours.
                if current_page == 1 and max_items is None and page_count > 50:
                    est_hours = round(page_count / 3600, 2)
                    logger.warning(f"WARNING: No 'max_items' limit set for {list_id}!")
                    logger.warning(f"Trakt reports {page_count} total pages. Due to API rate limits, this will take approximately {est_hours} hours to fetch.")
                    logger.warning("If it appears 'stuck', it is just working slowly in the background.")
                    logger.warning("Recommendation: Add 'max_items: 1000' (or similar) to your config.yaml to prevent this.")
                logger.debug(f"Page {current_page}/{page_count}. Total items: {len(items_data)}")
                # Stop paginating if we reach the end of Trakt's list OR hit the user's configured limit.
                if current_page >= page_count or (max_items is not None and len(items_data) >= max_items):
                    break
                current_page += 1
                # Pause for 1 second between requests to respect Trakt's rate limits.
                time.sleep(1)
            # We fetch in full pages, so we might have slightly overshot the limit. Slice the final array to return the exact number the user requested.
            if max_items is not None:
                items_data = items_data[:max_items]
        else:
            # CUSTOM USER LIST
            logger.debug(f"Trakt User list: {list_id}")
            
            r = requests.get(f"https://api.trakt.tv/lists/{list_id}", headers=headers)
            
            # Safety check: If list is private or ID is wrong, Trakt returns 404 or 401
            if r.status_code != 200:
                logger.error(f"Trakt list '{list_id}' not found or private (Status {r.status_code}). Skipping.")
                return {"name": "Error", "description": "List Not Found", "items": []}

            try:
                list_data = r.json()
                list_name = list_data.get("name", "Unknown List")
                description = list_data.get("description", "")
            except Exception:
                logger.error(f"Failed to parse metadata for Trakt list '{list_id}'.")
                return {"name": "Error", "description": "Invalid API Response", "items": []}

            # Fetch the Items
            r = requests.get(f"https://api.trakt.tv/lists/{list_id}/items", headers=headers)
            if r.status_code == 200:
                try:
                    items_data = r.json()
                except Exception:
                    items_data = []
            else:
                logger.warning(f"Could not fetch items for list '{list_id}'.")
                items_data = []

        # Process the items
        logger.debug("Processing items.")
        items = []
        for item_data in items_data:
            if "type" in item_data:
                item = {"media_type": item_data["type"]}
            else:
                item = {"media_type": item_types}

            if item["media_type"] == "season":
                # Ignore seasons
                continue

            if "ids" in item_data:
                meta = item_data
            else:
                meta = item_data[item["media_type"]]

            if "imdb" in meta["ids"]:
                item["imdb_id"] = meta["ids"]["imdb"]
            
            if "title" in meta:
                item["title"] = meta["title"]
            else:
                continue
            if "year" in meta:
                item["release_year"] = meta["year"]
            items.append(item)
            
        return {
            "name": list_name,
            "description": description,
            "items": items
        }
