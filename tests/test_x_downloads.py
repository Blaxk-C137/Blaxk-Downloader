"""Tests for X (Twitter) downloads: URL detection and quality selection."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_media_grabber.meta import (
    extract_metadata,
    get_platform_name,
    is_direct_download_url,
    is_x_url,
)
from youtube_media_grabber.downloader import build_video_format


def test_is_x_url_accepts_x_twitter_and_tco_links():
    assert is_x_url("https://x.com/user/status/1234567890")
    assert is_x_url("https://twitter.com/user/status/1234567890")
    assert is_x_url("https://t.co/abc123XYZ")


def test_is_x_url_rejects_non_x_links():
    assert not is_x_url("https://www.youtube.com/watch?v=abc")
    assert not is_x_url("https://open.spotify.com/track/xyz")
    assert not is_x_url("not a url")


def test_get_platform_name_reports_x():
    assert get_platform_name("https://x.com/user/status/123") == "X"
    assert get_platform_name("https://twitter.com/user/status/123") == "X"


def test_extract_metadata_treats_x_as_direct_download():
    """X URLs must not go through page scraping — like YouTube, they're
    handed straight to yt-dlp with the URL as the query."""
    url = "https://x.com/user/status/1234567890"
    metadata = extract_metadata(url)
    assert metadata.source_platform == "X"
    assert metadata.source_url == url
    assert metadata.query == url


def test_direct_download_urls_cover_youtube_and_x():
    """YouTube and X links download directly via yt-dlp; everything else
    (Spotify, search queries, random pages) goes through metadata/search."""
    assert is_direct_download_url("https://www.youtube.com/watch?v=abc")
    assert is_direct_download_url("https://x.com/user/status/123")
    assert is_direct_download_url("https://twitter.com/user/status/123")
    assert not is_direct_download_url("https://open.spotify.com/track/xyz")
    assert not is_direct_download_url("just a search query")


# ──────────────────────────────────────────────────────────────
# Quality selection
# ──────────────────────────────────────────────────────────────

BEST_FORMAT = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/mp4"


def test_best_quality_uses_default_format():
    assert build_video_format("best") == BEST_FORMAT


def test_capped_quality_limits_video_height():
    expected = (
        "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]"
        "/best[height<=720]/best"
    )
    assert build_video_format("720") == expected


def test_unknown_quality_falls_back_to_best():
    assert build_video_format("nonsense") == BEST_FORMAT
    assert build_video_format("") == BEST_FORMAT


class _FakeYoutubeDL:
    """Captures the opts yt-dlp is instantiated with; download is a no-op."""

    instances: list["_FakeYoutubeDL"] = []

    def __init__(self, opts):
        self.opts = opts
        self.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def add_post_processor(self, pp):
        pass

    def download(self, urls):
        return 0


def test_download_single_applies_quality_to_video(monkeypatch, tmp_path):
    import youtube_media_grabber.downloader as dl

    _FakeYoutubeDL.instances = []
    monkeypatch.setattr(dl.yt_dlp, "YoutubeDL", _FakeYoutubeDL)

    dl.download_single(
        "https://x.com/user/status/123",
        format_choice="video",
        base_output_dir=str(tmp_path),
        quality="480",
    )

    opts = _FakeYoutubeDL.instances[-1].opts
    assert "height<=480" in opts["format"]


def test_download_single_ignores_quality_for_audio(monkeypatch, tmp_path):
    import youtube_media_grabber.downloader as dl

    _FakeYoutubeDL.instances = []
    monkeypatch.setattr(dl.yt_dlp, "YoutubeDL", _FakeYoutubeDL)

    dl.download_single(
        "https://x.com/user/status/123",
        format_choice="audio",
        base_output_dir=str(tmp_path),
        quality="480",
    )

    opts = _FakeYoutubeDL.instances[-1].opts
    assert opts["format"] == "bestaudio[ext=m4a]/bestaudio/best"


if __name__ == "__main__":
    # Runnable without pytest: `python tests/test_x_downloads.py`
    test_is_x_url_accepts_x_twitter_and_tco_links()
    print("PASS: is_x_url accepts x/twitter/t.co links")
    test_is_x_url_rejects_non_x_links()
    print("PASS: is_x_url rejects non-X links")
    test_get_platform_name_reports_x()
    print("PASS: get_platform_name reports X")
    test_extract_metadata_treats_x_as_direct_download()
    print("PASS: extract_metadata treats X as direct download")
    test_direct_download_urls_cover_youtube_and_x()
    print("PASS: direct download URLs cover YouTube and X")
    test_best_quality_uses_default_format()
    print("PASS: best quality uses default format")
    test_capped_quality_limits_video_height()
    print("PASS: capped quality limits video height")
    test_unknown_quality_falls_back_to_best()
    print("PASS: unknown quality falls back to best")
