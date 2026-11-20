from contextlib import contextmanager

from bs4 import BeautifulSoup
from PyMovieDb import IMDB


@contextmanager
def imdb_pages():
    """Render all pages for one list with the same Chromium process."""
    client = IMDB()
    try:
        with client.renderer as renderer:

            def read(url):
                return BeautifulSoup(renderer.render(url).html, "html.parser")

            yield read
    finally:
        client.session.close()
