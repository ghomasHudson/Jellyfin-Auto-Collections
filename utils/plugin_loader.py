import importlib
import inspect
import pkgutil

from .base_plugin import ListScraper


def load_plugins(package_name="plugins"):
    package = importlib.import_module(package_name)
    plugins = {}

    for module_info in pkgutil.walk_packages(package.__path__, f"{package.__name__}."):
        module = importlib.import_module(module_info.name)
        for plugin_class in _iter_plugin_classes(module):
            alias = getattr(plugin_class, "_alias_", None)
            if not alias:
                raise ValueError(f"Plugin {plugin_class.__name__} is missing _alias_")
            if alias in plugins:
                raise ValueError(f"Duplicate plugin alias: {alias}")
            plugins[alias] = plugin_class

    return plugins


def _iter_plugin_classes(module):
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj is ListScraper:
            continue
        if obj.__module__ != module.__name__:
            continue
        if inspect.isabstract(obj):
            continue
        if issubclass(obj, ListScraper):
            yield obj
