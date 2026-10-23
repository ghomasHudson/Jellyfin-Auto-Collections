from utils.base_plugin import ListScraper
from utils.plugin_loader import load_plugins


def test_load_plugins_discovers_builtin_aliases():
    plugins = load_plugins()

    assert {
        "arr",
        "bfi",
        "criterion_channel",
        "imdb_chart",
        "imdb_list",
        "jellyfin_api",
        "letterboxd",
        "listmania",
        "mdblist",
        "popular_movies",
        "trakt",
        "tspdt",
    }.issubset(plugins)
    assert all(issubclass(plugin, ListScraper) for plugin in plugins.values())
