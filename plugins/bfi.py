import yaml
import re
from utils.base_plugin import ListScraper
import bs4
import requests
from loguru import logger

class BFI(ListScraper):

    _alias_ = 'bfi'

    def get_list(list_id, config=None):
        r = requests.get(f"https://www.bfi.org.uk/lists/{list_id}")
        soup = bs4.BeautifulSoup(r.text, 'html.parser')

        # Find the JSON-LD script tag
        json_ld_tag = soup.find("script", type="application/ld+json")
        if not json_ld_tag:
            raise ValueError("No JSON-LD metadata found on the page")
        json_ld = yaml.load(json_ld_tag.string, Loader=yaml.SafeLoader)

        # Basic metadata
        list_name = json_ld.get("headline", "").strip()
        description = json_ld.get("description", "").strip()

        # Movies
        items = []
        year_pattern = re.compile(r'\s*\((\d{4})\)\s*$')
        for entry in soup.find_all("figcaption"):
            title = entry.text

            match = year_pattern.search(title)
            if match is not None:
                year = int(match.group(1))
                title = year_pattern.sub('', title)

                items.append({
                    "title": title,
                    "release_year": year,
                    "media_type": "Movie"
                })

        return {
            "name": list_name,
            "description": description,
            "items": items
        }
