from abc import ABC, abstractmethod


class ListScraper(ABC):
    _alias_ = None

    @staticmethod
    @abstractmethod
    def get_list(list_id, config=None):
        pass
