import bs4
import requests
import csv
from utils.base_plugin import ListScraper

class IMDBList(ListScraper):

    _alias_ = 'imdb_list'

    def get_list(list_id, config=None):
        r = requests.get(f'https://www.imdb.com/list/{list_id}', headers={'Accept-Language': 'en-US', 'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US'})
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        list_name = soup.find('h1').text
        description = soup.find("div", {"class": "list-description"}).text

        r = requests.get(f'https://www.imdb.com/list/{list_id}/export', headers={'Accept-Language': 'en-US', 'User-Agent': 'Mozilla/5.0'})
        reader = csv.DictReader(r.text.splitlines())
        movies = []
        for row in reader:
            movies.append({'title': row['Title'], 'release_year': row['Year'], "media_type": row['Title Type'], "imdb_id": row['Const']})
        return {'name': list_name, 'items': movies, "description": description}
