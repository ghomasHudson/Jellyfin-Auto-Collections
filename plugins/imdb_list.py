import json
from urllib.parse import urlsplit

from utils.base_plugin import ListScraper
from utils.imdb import imdb_pages


class IMDBList(ListScraper):
    _alias_ = "imdb_list"

    def get_list(list_id, config=None):
        add_year = (config or {}).get("add_release_year", False)
        with imdb_pages() as read:
            soup = read(f"https://www.imdb.com/list/{list_id}/")
            script = soup.find("script", type="application/ld+json")
            if not script:
                raise ValueError(f"IMDb returned no list data for {list_id}")
            data = json.loads(script.string)
            if not data.get("itemListElement"):
                raise ValueError(f"IMDb returned no list entries for {list_id}")

            movies = []
            for row in data["itemListElement"]:
                item = row["item"]
                imdb_id = urlsplit(item["url"]).path.rstrip("/").split("/")[-1]
                year = None
                if add_year:
                    date = item.get("datePublished")
                    if not date:
                        detail = read(f"https://www.imdb.com/title/{imdb_id}/")
                        script = detail.find("script", type="application/ld+json")
                        if script:
                            date = json.loads(script.string).get("datePublished")
                    year = date.split("-")[0] if date else None
                movies.append(
                    {
                        "title": item["name"],
                        "release_year": year,
                        "media_type": item["@type"],
                        "imdb_id": imdb_id,
                    }
                )

            description = data.get("description") or ""
            if not description:
                desc_tag = soup.find("div", class_="list-description")
                description = desc_tag.get_text(strip=True) if desc_tag else ""
            return {
                "name": data.get("name") or soup.h1.get_text(strip=True),
                "description": description,
                "items": movies,
            }
