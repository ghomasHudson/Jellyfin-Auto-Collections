import yaml
from utils.base_plugin import ListScraper
import bs4
import requests
from loguru import logger

class ListMania(ListScraper):

    _alias_ = 'listmania'

    def get_list(list_id, config=None):
        r = requests.get(f"https://www.listmania.org/list/{list_id}")
        soup = bs4.BeautifulSoup(r.text, 'html.parser')

        # Find the JSON-LD script tag
        json_ld_tag = soup.find("script", type="application/ld+json")
        if not json_ld_tag:
            raise ValueError("No JSON-LD metadata found on the page")
        json_ld = yaml.load(json_ld_tag.string, Loader=yaml.SafeLoader)

        # Basic metadata
        list_name = json_ld.get("name", "").strip()
        description = json_ld.get("description", "").strip()

        # Movies
        items = []
        item_list = json_ld.get("mainEntity", {}).get("itemListElement", [])
        for entry in item_list:
            item = entry.get("item", {})
            title = item.get("name", "").strip()
            if title == "":
                continue
            year = item.get("datePublished", "").strip()
            imdb_url = item.get("sameAs", "")
            imdb_id = imdb_url.split('/')[-2] if "imdb.com" in imdb_url else None

            items.append({
                "title": title,
                "release_year": year,
                "media_type": item.get("@type", "Movie").lower(),
                "imdb_id": imdb_id
            })

        return {
            "name": list_name,
            "description": description,
            "items": items
        }
