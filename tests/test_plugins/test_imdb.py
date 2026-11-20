import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from plugins.imdb_chart import IMDBChart
from plugins.imdb_list import IMDBList


@pytest.fixture
def render(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr("utils.imdb.IMDB", lambda: client)
    renderer = client.renderer.__enter__.return_value
    pages = {}
    renderer.render.side_effect = lambda url: SimpleNamespace(
        html=pages[url], status_code=202
    )
    yield pages
    client.renderer.__exit__.assert_called_once()
    client.session.close.assert_called_once()


def script(data, attr='id="__NEXT_DATA__"'):
    return f"<script {attr}>{json.dumps(data)}</script>"


def test_chart_uses_embedded_title_data(render):
    node = {
        "id": "tt123",
        "titleText": {"text": "Series"},
        "titleType": {"id": "tvSeries"},
        "releaseYear": None,
    }
    page = {"chartTitles": {"edges": [{"node": node}]}}
    render["https://www.imdb.com/chart/tvmeter/"] = (
        '<title>TV chart</title><meta property="og:description" content="Popular shows">'
        + script({"props": {"pageProps": {"pageData": page}}})
    )
    assert IMDBChart.get_list("tvmeter") == {
        "name": "TV chart",
        "description": "Popular shows",
        "items": [
            {
                "title": "Series",
                "media_type": "tvSeries",
                "release_year": None,
                "imdb_id": "tt123",
            }
        ],
    }


def test_boxoffice_chart(render):
    title = {
        "id": "tt123",
        "titleText": {"text": "Film"},
        "titleType": {"id": "movie"},
        "releaseYear": {"year": 2020},
    }
    page = {
        "topGrossingReleases": {
            "edges": [{"node": {"release": {"titles": [{"id": "tt123"}]}}}]
        }
    }
    render["https://www.imdb.com/chart/boxoffice/"] = (
        "<title>Box office</title>"
        + script({"props": {"pageProps": {"pageData": page}}})
    )
    render["https://www.imdb.com/title/tt123/"] = script(
        {"props": {"pageProps": {"aboveTheFoldData": title}}}
    )
    assert IMDBChart.get_list("boxoffice") == {
        "name": "Box office",
        "description": "",
        "items": [
            {
                "title": "Film",
                "media_type": "movie",
                "release_year": 2020,
                "imdb_id": "tt123",
            }
        ],
    }


@pytest.mark.parametrize("add_year", [False, True])
def test_public_list(render, add_year):
    attr = 'type="application/ld+json"'
    item = {
        "name": "Episode",
        "@type": "TVEpisode",
        "url": "https://www.imdb.com/title/tt123/",
    }
    render["https://www.imdb.com/list/ls123/"] = script(
        {
            "name": "Favorites",
            "description": "Episodes",
            "itemListElement": [{"item": item}],
        },
        attr,
    )
    if add_year:
        render[item["url"]] = script({"datePublished": "2020-01-01"}, attr)
    assert IMDBList.get_list("ls123", {"add_release_year": add_year}) == {
        "name": "Favorites",
        "description": "Episodes",
        "items": [
            {
                "title": "Episode",
                "media_type": "TVEpisode",
                "release_year": "2020" if add_year else None,
                "imdb_id": "tt123",
            }
        ],
    }


@pytest.mark.parametrize(
    "plugin,path,list_id", [(IMDBChart, "chart", "top"), (IMDBList, "list", "ls123")]
)
def test_challenge_raises_instead_of_returning_empty_collection(
    render, plugin, path, list_id
):
    render[f"https://www.imdb.com/{path}/{list_id}/"] = "<title>Please wait</title>"
    with pytest.raises(ValueError, match=list_id):
        plugin.get_list(list_id)
