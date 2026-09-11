from utils import http_client


def test_get_applies_default_timeout(monkeypatch):
    seen = {}

    def fake_get(url, **kwargs):
        seen["url"] = url
        seen["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(http_client.requests, "get", fake_get)

    http_client.get("https://example.test")

    assert seen["url"] == "https://example.test"
    assert seen["kwargs"]["timeout"] == http_client.DEFAULT_TIMEOUT


def test_get_preserves_explicit_timeout(monkeypatch):
    seen = {}

    def fake_get(url, **kwargs):
        seen["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(http_client.requests, "get", fake_get)

    http_client.get("https://example.test", timeout=(1, 2))

    assert seen["kwargs"]["timeout"] == (1, 2)


def test_session_applies_default_timeout(monkeypatch):
    seen = {}

    def fake_request(self, method, url, **kwargs):
        seen["method"] = method
        seen["url"] = url
        seen["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(http_client.requests.Session, "request", fake_request)

    session = http_client.Session()
    session.get("https://example.test")

    assert seen["method"] == "GET"
    assert seen["url"] == "https://example.test"
    assert seen["kwargs"]["timeout"] == http_client.DEFAULT_TIMEOUT


def test_session_preserves_explicit_timeout(monkeypatch):
    seen = {}

    def fake_request(self, method, url, **kwargs):
        seen["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(http_client.requests.Session, "request", fake_request)

    session = http_client.Session()
    session.post("https://example.test", timeout=(2, 4))

    assert seen["kwargs"]["timeout"] == (2, 4)
