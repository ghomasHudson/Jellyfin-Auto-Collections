import pytest
from plugins.letterboxd import Letterboxd

# Test data as fixtures
@pytest.fixture
def test_lists():
    return [
        "jf_auto_collect/watchlist",
        "jf_auto_collect/likes/films",
        "jf_auto_collect/list/test_list/"
    ]

@pytest.fixture
def test_list_output():
    return [
        {'title': 'The Godfather', 'media_type': 'movie', 'imdb_id': 'tt0068646', 'release_year': '1972'},
        {'title': 'The Godfather Part II', 'media_type': 'movie', 'imdb_id': 'tt0071562', 'release_year': '1974'}
    ]

# Parametrized test for different lists
@pytest.mark.parametrize("test_list", [
    "jf_auto_collect/watchlist",
    "jf_auto_collect/likes/films",
    "jf_auto_collect/list/test_list/"
])
def test_get_list(test_list, test_list_output):
    # Assuming Letterboxd.get_list returns a dictionary with a key "items"
    result = Letterboxd.get_list(test_list, {"imdb_id_filter": True})
    
    # Perform the assertion to check if the "items" key matches the expected output
    assert result["items"] == test_list_output

