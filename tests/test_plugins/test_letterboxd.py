from unittest.mock import Mock

import pytest
from plugins import letterboxd
from plugins.letterboxd import Letterboxd


# Test data as fixtures
@pytest.fixture
def test_lists():
    return ["jf_auto_collect/watchlist", "jf_auto_collect/list/test_list/"]


@pytest.fixture
def test_list_output():
    return [
        {
            "title": "The Godfather",
            "media_type": "movie",
            "imdb_id": "tt0068646",
            "release_year": "1972",
        },
        {
            "title": "The Godfather Part II",
            "media_type": "movie",
            "imdb_id": "tt0071562",
            "release_year": "1974",
        },
    ]


# Parametrized test for different lists
@pytest.mark.parametrize(
    "test_list", ["jf_auto_collect/watchlist", "jf_auto_collect/list/test_list/"]
)
def test_get_list(test_list, test_list_output):
    # Assuming Letterboxd.get_list returns a dictionary with a key "items"
    result = Letterboxd.get_list(test_list, {"imdb_id_filter": True})

    # Perform the assertion to check if the "items" key matches the expected output
    assert result["items"] == test_list_output


def test_liked_films(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    login = Mock()
    monkeypatch.setattr(letterboxd.UserSession, "login", login)
    likes = Mock()
    likes.return_value.get_liked_films.return_value = {
        "count": 1,
        "movies": {"alien": {"name": "Alien", "slug": "alien", "year": None}},
    }
    monkeypatch.setattr(letterboxd, "UserLikes", likes)
    profile = Mock()
    profile.return_value.get_year.return_value = 1979
    profile.return_value.get_imdb_id.return_value = "tt0078748"
    monkeypatch.setattr(letterboxd, "MovieProfile", profile)

    result = Letterboxd.get_list("ripley/likes/films/")
    likes.assert_called_once_with("ripley")
    login.assert_not_called()
    assert result["name"] == "ripley Liked Films"
    assert result["items"] == [{
        "title": "Alien", "release_year": "1979", "media_type": "movie",
        "imdb_id": "tt0078748",
    }]


@pytest.mark.parametrize("fetch_fails", [False, True])
def test_private_list_session(monkeypatch, tmp_path, fetch_fails):
    monkeypatch.chdir(tmp_path)
    previous = letterboxd.Scraper.instance()
    authenticated = Mock()

    def login(username, password, path):
        assert (username, password) == ("ripley", "test-password")
        letterboxd.Scraper.set_instance(authenticated)

    def fetch(owner, slug):
        assert letterboxd.Scraper.instance() is authenticated
        assert (owner, slug) == ("ripley", "private")
        if fetch_fails:
            raise RuntimeError("List unavailable")
        return Mock(title="Private", description="", movies={})

    monkeypatch.setattr(letterboxd.UserSession, "login", login)
    monkeypatch.setattr(letterboxd, "List", fetch)
    config = {"username": "ripley", "password": "test-password"}
    if fetch_fails:
        with pytest.raises(RuntimeError, match="List unavailable"):
            Letterboxd.get_list("ripley/list/private", config)
    else:
        assert Letterboxd.get_list("ripley/list/private", config)["name"] == "Private"
    assert letterboxd.Scraper.instance() is previous
    authenticated.close.assert_called_once()


def test_incomplete_credentials():
    with pytest.raises(ValueError, match="both username and password"):
        Letterboxd.get_list("ripley/list/private", {"username": "ripley"})
