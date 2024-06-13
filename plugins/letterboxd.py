import json
from utils.base_plugin import ListScraper
import bs4
import requests

class Letterboxd(ListScraper):

    _alias_ = 'letterboxd'

    def get_list(list_id, config=None):
        page_number = 1
        list_name = None
        movies = []

        while True:
            r = requests.get(f"https://letterboxd.com/{list_id}/detail/by/release-earliest/page/{page_number}/", headers={'User-Agent': 'Mozilla/5.0'})
            soup = bs4.BeautifulSoup(r.text, 'html.parser')

            if list_name is None:
                list_name = soup.find('h1', {'class': 'title-1 prettify'}).text

            for movie in soup.find_all('div', {'class': 'film-detail-content'}):
                movie_name = movie.find('h2', {'class': 'headline-2 prettify'}).find('a').text
                movie_year = movie.find('small', {'class': 'metadata'}).text
                movie = {"title": movie_name, "release_year": movie_year, "media_type": "movie"}

                # Find the imdb id
                if config.get("imdb_id_filter", False):
                    r = requests.get(f"https://letterboxd.com{movie.find('a')['href']}", headers={'User-Agent': 'Mozilla/5.0'})
                    movie_soup = bs4.BeautifulSoup(r.text, 'html.parser')
                    imdb_id = movie_soup.find("a", {"data-track-action":"IMDb"})["href"].split("/title/")[1].split("/")[0]
                    movie["imdb_id"] = imdb_id

                movies.append(movie)

            if soup.find('a', {'class': 'next'}):
                page_number += 1
            else:
                break

        return {'name': list_name, 'items': movies}
