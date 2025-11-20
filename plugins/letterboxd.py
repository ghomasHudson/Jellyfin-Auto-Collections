import json
from utils.base_plugin import ListScraper
import bs4
import requests
from loguru import logger
from requests_cache import CachedSession

class Letterboxd(ListScraper):

    _alias_ = 'letterboxd'

    def get_list(list_id, config=None):
        page_number = 1
        list_name = None
        description = None
        movies = []
        config = config or {}

        # Cache for movie pages - so we don't have to refetch imdb_ids
        session = CachedSession(backend='filesystem')

        while True:
            logger.info(f"Page number: {page_number}")
            watchlist = list_id.endswith("/watchlist")
            likeslist = list_id.endswith("/likes/films")

            if watchlist:
                list_name = list_id.split("/")[0] + " Watchlist"
                description = "Watchlist for " + list_id.split("/")[0]
            elif likeslist:
                list_name = list_id.split("/")[0] + " Likes"
                description = "Likes list for " + list_id.split("/")[0]

            url_format = "https://letterboxd.com/{list_id}{maybe_detail}/by/release-earliest/page/{page_number}/"
            maybe_detail = "" if watchlist or likeslist else "/detail"
            r = requests.get(
                url_format.format(list_id=list_id, maybe_detail=maybe_detail, page_number=page_number),
                headers={'User-Agent': 'Mozilla/5.0'},
            )

            soup = bs4.BeautifulSoup(r.text, 'html.parser')

            if list_name is None:
                title_tag = soup.find('h1', {'class': 'title-1 prettify'})
                if title_tag:
                    list_name = title_tag.text

            if description is None:
                desc_tag = soup.find('div', {'class': 'body-text'})
                if desc_tag is not None:
                    description = "\n".join([p.text for p in desc_tag.find_all('p')])
                else:
                    description = ""

            # NEW: handle both poster-container and poster-item
            page = soup.find_all('li', {'class': 'poster-container'})
            if not page:
                page = soup.find_all('div', {'class': 'poster-item'})

            logger.debug(f"Found {len(page)} film entries on page {page_number}")

            for movie_soup in page:
                img = movie_soup.find('img')
                if img:
                    movie = {"title": img.get('alt'), "media_type": "movie"}
                else:
                    continue

                # Link to film detail page
                link_tag = movie_soup.find('div', {'class': 'film-poster'})
                if link_tag and link_tag.has_attr('data-target-link'):
                    link = link_tag['data-target-link']
                else:
                    link = None

                # Release year
                year_tag = movie_soup.find('span', {'class': 'year'})
                if year_tag:
                    movie["release_year"] = year_tag.text

                # IMDb ID lookup if needed
                if link and (config.get("imdb_id_filter", False) or 'release_year' not in movie):
                    logger.debug(f"Fetching IMDb/year for: {movie['title']}")
                    r = session.get(f"https://letterboxd.com{link}", headers={'User-Agent': 'Mozilla/5.0'})
                    detail_soup = bs4.BeautifulSoup(r.text, 'html.parser')

                    imdb_id = detail_soup.find('a', href=lambda href: href and 'imdb.com/title' in href)
                    if imdb_id:
                        movie["imdb_id"] = imdb_id["href"].split("/title/")[1].split("/")[0]

                    year_tag = detail_soup.find("span", class_="year")
                    if year_tag:
                        movie["release_year"] = year_tag.text

                if 'release_year' in movie:
                    movies.append(movie)
                    logger.debug(f"Added movie: {movie}")

            # Pagination
            if soup.find('a', {'class': 'next'}):
                page_number += 1
            else:
                break

        return {'name': list_name, 'items': movies, "description": description}
