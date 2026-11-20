import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from letterboxdpy.auth import UserSession
from letterboxdpy.core.scraper import Scraper
from letterboxdpy.list import List
from letterboxdpy.pages.movie_profile import MovieProfile
from letterboxdpy.pages.user_likes import UserLikes
from letterboxdpy.watchlist import Watchlist
from loguru import logger

from utils.base_plugin import ListScraper


class Letterboxd(ListScraper):
    _alias_ = "letterboxd"
    _cache_file_ = ".letterboxd_cache.json"

    @staticmethod
    def _load_cache():
        """Load the movie details cache from disk."""
        if os.path.exists(Letterboxd._cache_file_):
            try:
                with open(Letterboxd._cache_file_, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                return {}
        return {}

    @staticmethod
    def _save_cache(cache):
        """Save the movie details cache to disk."""
        try:
            with open(Letterboxd._cache_file_, "w") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def get_list(list_id, config=None):
        config = config or {}
        list_id = list_id.rstrip("/")
        username, password = config.get("username"), config.get("password")
        if not username and not password:
            return Letterboxd._read_list(list_id, config)
        if not username or not password:
            raise ValueError(
                "Letterboxd authentication requires both username and password."
            )

        # login() installs a process-wide scraper session and saves its cookies.
        # Keep the cookie file private and restore anonymous access after this list.
        previous = Scraper.instance()
        try:
            with TemporaryDirectory() as directory:
                UserSession.login(username, password, Path(directory) / "cookies.json")
            return Letterboxd._read_list(list_id, config)
        finally:
            current = Scraper.instance()
            Scraper.set_instance(previous)
            if current is not previous:
                current.close()

    @staticmethod
    def _read_list(list_id, config):
        movies = []

        # Load cache
        cache = Letterboxd._load_cache()
        cache_updated = False

        # Determine list type and parse list_id
        username, _, route = list_id.partition("/")

        if route == "watchlist":
            # Format: username/watchlist
            logger.info(f"Fetching watchlist for user: {username}")
            movies_dict = Watchlist(username).movies
            list_name = f"{username} Watchlist"
            description = f"Watchlist for {username}"

        elif route == "likes/films":
            logger.info(f"Fetching liked films for user: {username}")
            movies_dict = UserLikes(username).get_liked_films()["movies"]
            list_name = f"{username} Liked Films"
            description = f"Films liked by {username}"

        else:
            # Accept both username/list/slug and the shorthand username/slug.
            slug = route.removeprefix("list/")
            logger.info(f"Fetching list for user: {username}, slug: {slug}")
            list_instance = List(username, slug)
            list_name = list_instance.title
            description = list_instance.description or ""
            movies_dict = list_instance.movies

        logger.info(f"Found {len(movies_dict)} movies in list")

        # Convert letterboxdpy format to our internal format
        for letterboxd_id, movie_data in movies_dict.items():
            movie = {
                "title": movie_data.get("name") or movie_data.get("title"),
                "media_type": "movie",
            }

            # Add year if available
            if "year" in movie_data and movie_data["year"]:
                movie["release_year"] = str(movie_data["year"])

            # Fetch IMDb ID if requested or if year is missing
            if config.get("imdb_id_filter", False) or "release_year" not in movie:
                slug = movie_data.get("slug")
                if slug:
                    # Check cache first
                    if slug in cache:
                        logger.debug(f"Using cached data for: {movie['title']}")
                        cached_data = cache[slug]
                        if cached_data.get("imdb_id"):
                            movie["imdb_id"] = cached_data["imdb_id"]
                        if "release_year" not in movie and cached_data.get("year"):
                            movie["release_year"] = str(cached_data["year"])
                    else:
                        # Fetch from API if not in cache
                        try:
                            logger.debug(f"Fetching IMDb ID for: {movie['title']}")
                            # Only fetch the main film page. Movie also loads unrelated
                            # pages (including /details), which may be blocked.
                            movie_profile = MovieProfile(slug)

                            # Prepare cache entry
                            cache_entry = {}

                            # Get IMDb ID from the main film page
                            imdb_id = movie_profile.get_imdb_id()
                            if imdb_id:
                                movie["imdb_id"] = imdb_id
                                cache_entry["imdb_id"] = imdb_id

                            # Get year if not already present
                            year = movie_profile.get_year()
                            if year:
                                cache_entry["year"] = year
                                if "release_year" not in movie:
                                    movie["release_year"] = str(year)

                            # Save to cache
                            cache[slug] = cache_entry
                            cache_updated = True

                        except Exception as e:
                            logger.warning(
                                f"Failed to fetch details for {movie['title']}: {e}"
                            )

            # Only add movies with a release year
            if "release_year" in movie:
                movies.append(movie)

        # Save cache if it was updated
        if cache_updated:
            Letterboxd._save_cache(cache)
            logger.info(f"Cache updated with new movie details")

        return {"name": list_name, "items": movies, "description": description}


if __name__ == "__main__":
    # Basic test
    result = Letterboxd.get_list(
        "stautis/list/good-films-90-minutes-or-less", {"imdb_id_filter": True}
    )
    print(f"List: {result['name']}")
    print(f"Total movies: {len(result['items'])}")
    print(
        f"First movie: {result['items'][0]['title']} ({result['items'][0].get('release_year', 'N/A')})"
    )
