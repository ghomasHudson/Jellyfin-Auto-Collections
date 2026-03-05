from utils.base_plugin import ListScraper
from loguru import logger
from letterboxdpy.list import List
from letterboxdpy.watchlist import Watchlist
from letterboxdpy.movie import Movie
import json
import os

class Letterboxd(ListScraper):

    _alias_ = 'letterboxd'
    _cache_file_ = '.letterboxd_cache.json'

    @staticmethod
    def _load_cache():
        """Load the movie details cache from disk."""
        if os.path.exists(Letterboxd._cache_file_):
            try:
                with open(Letterboxd._cache_file_, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                return {}
        return {}

    @staticmethod
    def _save_cache(cache):
        """Save the movie details cache to disk."""
        try:
            with open(Letterboxd._cache_file_, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def get_list(list_id, config=None):
        config = config or {}
        movies = []

        # Load cache
        cache = Letterboxd._load_cache()
        cache_updated = False

        # Determine list type and parse list_id
        watchlist = list_id.endswith("/watchlist")
        likeslist = list_id.endswith("/likes/films")

        if watchlist:
            # Format: username/watchlist
            username = list_id.split("/")[0]
            logger.info(f"Fetching watchlist for user: {username}")
            list_instance = Watchlist(username)
            list_name = f"{username} Watchlist"
            description = f"Watchlist for {username}"

        elif likeslist:
            raise NotImplementedError("Likes lists are not currently supported. Please use regular lists or watchlists instead.")

        else:
            # Format: username/list/list-slug
            parts = list_id.split("/")
            if len(parts) >= 3 and parts[1] == "list":
                username = parts[0]
                slug = "/".join(parts[2:])  # Join remaining parts in case slug has slashes
            else:
                # Fallback: assume entire string is username/slug
                username = parts[0]
                slug = "/".join(parts[1:])

            logger.info(f"Fetching list for user: {username}, slug: {slug}")
            list_instance = List(username, slug)
            list_name = list_instance.title
            description = list_instance.description or ""

        # Get movies from the list
        movies_dict = list_instance.movies
        logger.info(f"Found {len(movies_dict)} movies in list")

        # Convert letterboxdpy format to our internal format
        for letterboxd_id, movie_data in movies_dict.items():
            movie = {
                "title": movie_data.get("name") or movie_data.get("title"),
                "media_type": "movie"
            }

            # Add year if available
            if "year" in movie_data and movie_data["year"]:
                movie["release_year"] = str(movie_data["year"])

            # Fetch IMDb ID if requested or if year is missing
            if config.get("imdb_id_filter", False) or "year" not in movie_data:
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
                            movie_instance = Movie(slug)

                            # Prepare cache entry
                            cache_entry = {}

                            # Get IMDb link and extract ID
                            if movie_instance.imdb_link:
                                imdb_id = movie_instance.imdb_link.split("/title/")[1].split("/")[0]
                                movie["imdb_id"] = imdb_id
                                cache_entry["imdb_id"] = imdb_id

                            # Get year if not already present
                            if movie_instance.year:
                                cache_entry["year"] = movie_instance.year
                                if "release_year" not in movie:
                                    movie["release_year"] = str(movie_instance.year)

                            # Save to cache
                            cache[slug] = cache_entry
                            cache_updated = True

                        except Exception as e:
                            logger.warning(f"Failed to fetch details for {movie['title']}: {e}")

            # Only add movies with a release year
            if "release_year" in movie:
                movies.append(movie)

        # Save cache if it was updated
        if cache_updated:
            Letterboxd._save_cache(cache)
            logger.info(f"Cache updated with new movie details")

        return {'name': list_name, 'items': movies, "description": description}


if __name__ == "__main__":
    # Basic test
    result = Letterboxd.get_list("stautis/list/good-films-90-minutes-or-less", {"imdb_id_filter": True})
    print(f"List: {result['name']}")
    print(f"Total movies: {len(result['items'])}")
    print(f"First movie: {result['items'][0]['title']} ({result['items'][0].get('release_year', 'N/A')})")
