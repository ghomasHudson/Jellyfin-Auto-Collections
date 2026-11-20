import json

from utils.base_plugin import ListScraper
from utils.imdb import imdb_pages


class IMDBChart(ListScraper):
    _alias_ = "imdb_chart"

    def get_list(list_id, config=None):
        with imdb_pages() as read:
            soup = read(f"https://www.imdb.com/chart/{list_id}/")
            script = soup.find("script", id="__NEXT_DATA__")
            if not soup.title or not script:
                raise ValueError(f"IMDb returned no chart data for {list_id}")

            page = json.loads(script.string)["props"]["pageProps"]["pageData"]
            chart = next(
                (v for v in page.values() if isinstance(v, dict) and "edges" in v), None
            )
            if not chart or not chart["edges"]:
                raise ValueError(f"IMDb returned no chart entries for {list_id}")

            movies = []
            for edge in chart["edges"]:
                movie = edge["node"]
                if "titleText" not in movie:
                    # Box office entries wrap the title in a release.
                    movie = movie["release"]["titles"][0]
                    if not {"titleText", "releaseYear", "titleType"} <= movie.keys():
                        detail = read(f"https://www.imdb.com/title/{movie['id']}/")
                        script = detail.find("script", id="__NEXT_DATA__")
                        if not script:
                            raise ValueError(
                                f"IMDb returned no title data for {movie['id']}"
                            )
                        movie = json.loads(script.string)["props"]["pageProps"][
                            "aboveTheFoldData"
                        ]

                movies.append(
                    {
                        "title": movie["titleText"]["text"],
                        "release_year": (movie.get("releaseYear") or {}).get("year"),
                        "media_type": movie["titleType"]["id"],
                        "imdb_id": movie["id"],
                    }
                )

            desc = soup.find("meta", property="og:description")
            return {
                "name": soup.title.get_text(strip=True),
                "description": desc.get("content", "") if desc else "",
                "items": movies,
            }
