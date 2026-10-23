import requests


DEFAULT_TIMEOUT = (5, 30)

exceptions = requests.exceptions


def _with_timeout(kwargs):
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    return kwargs


def get(url, **kwargs):
    return requests.get(url, **_with_timeout(kwargs))


def post(url, **kwargs):
    return requests.post(url, **_with_timeout(kwargs))


def delete(url, **kwargs):
    return requests.delete(url, **_with_timeout(kwargs))


class Session(requests.Session):
    def request(self, method, url, **kwargs):
        return super().request(method, url, **_with_timeout(kwargs))
