from utils.base_plugin import ListScraper
from loguru import logger
from letterboxdpy.list import List
from letterboxdpy.watchlist import Watchlist
from letterboxdpy.movie import Movie

class Letterboxd(ListScraper):

    _alias_ = 'letterboxd'

    def get_list(list_id, config=None):
        config = config or {}
        movies = []

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
                    try:
                        logger.debug(f"Fetching IMDb ID for: {movie['title']}")
                        movie_instance = Movie(slug)

                        # Get IMDb link and extract ID
                        if movie_instance.imdb_link:
                            imdb_id = movie_instance.imdb_link.split("/title/")[1].split("/")[0]
                            movie["imdb_id"] = imdb_id

                        # Get year if not already present
                        if "release_year" not in movie and movie_instance.year:
                            movie["release_year"] = str(movie_instance.year)

                    except Exception as e:
                        logger.warning(f"Failed to fetch details for {movie['title']}: {e}")

            # Only add movies with a release year
            if "release_year" in movie:
                movies.append(movie)

        return {'name': list_name, 'items': movies, "description": description}


if __name__ == "__main__":
    # Basic test
    result = Letterboxd.get_list("stautis/list/good-films-90-minutes-or-less", {"imdb_id_filter": True})
    print(f"List: {result['name']}")
    print(f"Total movies: {len(result['items'])}")
    print(f"First movie: {result['items'][0]['title']} ({result['items'][0].get('release_year', 'N/A')})")
