import json
from utils.base_plugin import ListScraper
import bs4
import requests
import time
from loguru import logger

class Letterboxd(ListScraper):

    _alias_ = 'letterboxd'

    def get_list(list_id, config=None):
        page_number = 1
        list_name = None
        description = None
        movies = []

        while True:
            r = requests.get(f"https://letterboxd.com/{list_id}/detail/by/release-earliest/page/{page_number}/", headers={'User-Agent': 'Mozilla/5.0'})

            soup = bs4.BeautifulSoup(r.text, 'html.parser')

            if list_name is None:
                list_name = soup.find('h1', {'class': 'title-1 prettify'}).text

            if description is None:
                description = soup.find('div', {'class': 'body-text'})
                if description is not None:
                    description = "\n".join([p.text for p in description.find_all('p')])
                else:
                    description = ""

            for movie_soup in soup.find_all('div', {'class': 'film-detail-content'}):
                movie_name = movie_soup.find('h2', {'class': 'headline-2 prettify'}).find('a').text
                movie_year = movie_soup.find('small', {'class': 'metadata'})
                if movie_year is not None:
                    movie_year = movie_year.text
                movie = {"title": movie_name, "release_year": movie_year, "media_type": "movie"}

                # Find the imdb id
                if config.get("imdb_id_filter", False):
                    r = requests.get(f"https://letterboxd.com{movie_soup.find('a')['href']}", headers={'User-Agent': 'Mozilla/5.0'})
                    movie_soup = bs4.BeautifulSoup(r.text, 'html.parser')
                    imdb_id = movie_soup.find("a", {"data-track-action":"IMDb"})
                    if imdb_id is not None:
                        movie["imdb_id"] = imdb_id["href"].split("/title/")[1].split("/")[0]

                movies.append(movie)

            if soup.find('a', {'class': 'next'}):
                page_number += 1
            else:
                break

        return {'name': list_name, 'items': movies, "description": description}
