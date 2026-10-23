from io import BytesIO

import pytest
from PIL import Image

from utils import poster_generation


class FakeResponse:
    def __init__(self, body, headers=None):
        self.body = body
        self.headers = headers or {}

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size=8192):
        for index in range(0, len(self.body), chunk_size):
            yield self.body[index:index + chunk_size]


def image_bytes(image_format):
    output = BytesIO()
    Image.new("RGB", (1, 1), "red").save(output, format=image_format)
    return output.getvalue()


@pytest.mark.parametrize(
    ("image_format", "content_type"),
    [
        ("JPEG", "image/jpeg"),
        ("PNG", "image/png"),
        ("WEBP", "image/webp"),
    ],
)
def test_download_image_accepts_expected_formats(monkeypatch, image_format, content_type):
    body = image_bytes(image_format)

    def fake_get(url, **kwargs):
        assert kwargs["stream"] is True
        return FakeResponse(body, {"Content-Type": content_type})

    monkeypatch.setattr(poster_generation.requests, "get", fake_get)

    image = poster_generation.download_image("https://example.test/poster", {})

    assert image.mode == "RGB"
    assert image.size == (1, 1)


def test_safe_download_rejects_non_image_content_type_before_decode(monkeypatch):
    def fake_get(url, **kwargs):
        return FakeResponse(b"not an image", {"Content-Type": "text/plain"})

    def fail_open(*args, **kwargs):
        raise AssertionError("Image.open should not be called")

    monkeypatch.setattr(poster_generation.requests, "get", fake_get)
    monkeypatch.setattr(poster_generation.Image, "open", fail_open)

    assert poster_generation.safe_download("https://example.test/poster", {}) is None


def test_safe_download_rejects_oversized_image_before_decode(monkeypatch):
    headers = {"Content-Length": str(poster_generation.MAX_POSTER_DOWNLOAD_BYTES + 1)}

    def fake_get(url, **kwargs):
        return FakeResponse(b"", headers)

    def fail_open(*args, **kwargs):
        raise AssertionError("Image.open should not be called")

    monkeypatch.setattr(poster_generation.requests, "get", fake_get)
    monkeypatch.setattr(poster_generation.Image, "open", fail_open)

    assert poster_generation.safe_download("https://example.test/poster", {}) is None
