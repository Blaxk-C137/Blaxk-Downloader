"""Tests for Spotify playlist downloads: URL detection and track extraction."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from youtube_media_grabber.spotify import (
    extract_spotify_playlist_tracks,
    is_spotify_playlist_url,
)


def _embed_html(tracks, playlist_name="My Playlist"):
    """Build a minimal copy of Spotify's embed page __NEXT_DATA__ payload."""
    track_list = [
        {
            "uri": f"spotify:track:{i}",
            "uid": f"uid{i}",
            "title": title,
            "subtitle": artist,
            "duration": duration_ms,
            "isPlayable": is_playable,
            "entityType": "track",
        }
        for i, (title, artist, duration_ms, is_playable) in enumerate(tracks)
    ]
    payload = {
        "props": {
            "pageProps": {
                "state": {
                    "data": {
                        "embeded_entity_uri": "spotify:playlist:abc123",
                        "entity": {
                            "name": playlist_name,
                            "trackList": track_list,
                        },
                    }
                }
            }
        }
    }
    return (
        '<!DOCTYPE html><html><head>'
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
        '</head><body></body></html>'
    )


class _FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"HTTP {self.status_code}")


# ──────────────────────────────────────────────────────────────
# URL detection
# ──────────────────────────────────────────────────────────────

def test_is_spotify_playlist_url_accepts_playlist_links():
    assert is_spotify_playlist_url("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
    assert is_spotify_playlist_url("https://open.spotify.com/playlist/abc123?si=xyz789")
    assert is_spotify_playlist_url("http://open.spotify.com/playlist/abc123")


def test_is_spotify_playlist_url_rejects_other_links():
    assert not is_spotify_playlist_url("https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC")
    assert not is_spotify_playlist_url("https://open.spotify.com/album/abc123")
    assert not is_spotify_playlist_url("https://www.youtube.com/playlist?list=PL123")
    assert not is_spotify_playlist_url("just a search query")


# ──────────────────────────────────────────────────────────────
# Track extraction
# ──────────────────────────────────────────────────────────────

def test_extracts_titles_artists_and_queries(monkeypatch):
    import youtube_media_grabber.spotify as sp

    html = _embed_html([
        ("Ain't In LA", "ADÉLA", 184927, True),
        ("Espresso", "Sabrina Carpenter", 175459, True),
    ])
    requested = {}

    def fake_get(url, **kwargs):
        requested["url"] = url
        return _FakeResponse(html)

    monkeypatch.setattr(sp.requests, "get", fake_get)

    tracks = extract_spotify_playlist_tracks("https://open.spotify.com/playlist/abc123")

    assert requested["url"] == "https://open.spotify.com/embed/playlist/abc123"
    assert len(tracks) == 2
    assert tracks[0]["title"] == "ADÉLA - Ain't In LA"
    assert tracks[0]["query"] == "Ain't In LA ADÉLA"
    assert tracks[0]["duration"] == 185  # ms → seconds (rounded)
    assert tracks[0]["link"] is None  # resolved per-track at download time
    assert tracks[1]["title"] == "Sabrina Carpenter - Espresso"


def test_skips_unplayable_tracks(monkeypatch):
    import youtube_media_grabber.spotify as sp

    html = _embed_html([
        ("Playable Song", "Artist A", 100000, True),
        ("Region-Locked Song", "Artist B", 100000, False),
    ])
    monkeypatch.setattr(sp.requests, "get", lambda url, **kw: _FakeResponse(html))

    tracks = extract_spotify_playlist_tracks("https://open.spotify.com/playlist/abc123")
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Artist A - Playable Song"


def test_404_page_raises_helpful_error(monkeypatch):
    """A private/deleted playlist returns a 404 page — the user must be told
    to check the playlist's visibility, not see a stack trace."""
    import youtube_media_grabber.spotify as sp

    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"status": 404, "title": "Page not found"}}}'
        "</script>"
    )
    monkeypatch.setattr(sp.requests, "get", lambda url, **kw: _FakeResponse(html))

    with pytest.raises(ValueError, match="playlist"):
        extract_spotify_playlist_tracks("https://open.spotify.com/playlist/missing")


def test_empty_tracklist_raises_error(monkeypatch):
    import youtube_media_grabber.spotify as sp

    html = _embed_html([])
    monkeypatch.setattr(sp.requests, "get", lambda url, **kw: _FakeResponse(html))

    with pytest.raises(ValueError, match="No tracks"):
        extract_spotify_playlist_tracks("https://open.spotify.com/playlist/abc123")


def test_playlist_link_with_si_param_uses_clean_id(monkeypatch):
    """Share links carry ?si=... tracking params — the embed URL must be
    rebuilt from the bare playlist id."""
    import youtube_media_grabber.spotify as sp

    html = _embed_html([("Song", "Artist", 100000, True)])
    requested = {}

    def fake_get(url, **kwargs):
        requested["url"] = url
        return _FakeResponse(html)

    monkeypatch.setattr(sp.requests, "get", fake_get)

    extract_spotify_playlist_tracks(
        "https://open.spotify.com/playlist/abc123?si=a1b2c3d4e5f6"
    )
    assert requested["url"] == "https://open.spotify.com/embed/playlist/abc123"


# ──────────────────────────────────────────────────────────────
# GUI routing
# ──────────────────────────────────────────────────────────────

def _make_gui_app(monkeypatch, playlist_tracks):
    """A BlaXkGrabber instance with fakes, routed so a Spotify playlist
    pasted into the input expands into a batch download."""
    import youtube_media_grabber.gui as gui

    class _Var:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    class _Recorder:
        def __init__(self):
            self.calls = []

        def __call__(self, *args):
            self.calls.append(args)

    app = gui.BlaXkGrabber.__new__(gui.BlaXkGrabber)
    app._destroyed = False
    app.is_downloading = True
    app._batch_ok = False
    app.format_var = _Var("audio")
    app.quality_var = _Var("Best")
    app.output_entry = _Var("")
    app.concurrent_var = _Var(1)
    app._schedule = lambda fn, *args: fn(*args)
    app._log = _Recorder()
    app._set_status = _Recorder()
    app._show_error = _Recorder()
    app._finish_download = lambda: None

    batch_calls = []

    def fake_batch(entries, *args, **kwargs):
        batch_calls.append(entries)

    app._download_batch = fake_batch

    monkeypatch.setattr(gui, "extract_metadata", lambda src: __import__(
        "youtube_media_grabber.meta", fromlist=["Metadata"]).Metadata())
    monkeypatch.setattr(
        gui, "extract_spotify_playlist_tracks", lambda url: playlist_tracks
    )
    searches = []
    monkeypatch.setattr(gui, "search_youtube", lambda q: searches.append(q) or {})

    return app, batch_calls, searches


def test_spotify_playlist_expands_into_batch_not_single_search(monkeypatch):
    """The original bug: a playlist link was searched on YouTube by its
    *name*, downloading one random video. It must expand into a batch of
    per-track entries instead — no search at routing time."""
    tracks = [
        {"title": "Artist A - Song A", "link": None, "query": "Song A Artist A",
         "duration": 100, "track": "Song A", "artist": "Artist A"},
        {"title": "Artist B - Song B", "link": None, "query": "Song B Artist B",
         "duration": 200, "track": "Song B", "artist": "Artist B"},
    ]
    app, batch_calls, searches = _make_gui_app(monkeypatch, tracks)

    app._resolve_and_download("https://open.spotify.com/playlist/abc123")

    assert len(batch_calls) == 1, "playlist must go straight to a batch download"
    assert batch_calls[0] == tracks
    assert not searches, "routing must not search YouTube for the playlist name"


def test_resolve_download_target_searches_and_caches(monkeypatch):
    import youtube_media_grabber.gui as gui

    app = gui.BlaXkGrabber.__new__(gui.BlaXkGrabber)
    search_count = {"n": 0}

    def fake_search(query):
        search_count["n"] += 1
        assert query == "Song A Artist A"
        return {"title": "Song A", "link": "https://youtu.be/a1"}

    monkeypatch.setattr(gui, "search_youtube", fake_search)

    entry = {"title": "Artist A - Song A", "link": None, "query": "Song A Artist A"}
    assert app._resolve_download_target(entry) == "https://youtu.be/a1"
    # Retry path: the cached link means no second search.
    assert app._resolve_download_target(entry) == "https://youtu.be/a1"
    assert search_count["n"] == 1


def test_resolve_download_target_requires_link_or_query():
    import youtube_media_grabber.gui as gui

    app = gui.BlaXkGrabber.__new__(gui.BlaXkGrabber)
    with pytest.raises(ValueError, match="no download link"):
        app._resolve_download_target({"title": "Broken entry"})


def test_entry_metadata_is_per_track_for_spotify():
    from youtube_media_grabber.gui import BlaXkGrabber
    from youtube_media_grabber.meta import Metadata

    base = Metadata(title="shared")
    entry = {"title": "Artist A - Song A", "track": "Song A", "artist": "Artist A"}
    per_track = BlaXkGrabber._entry_metadata(entry, base)
    assert per_track.title == "Song A"
    assert per_track.artist == "Artist A"
    assert per_track.source_platform == "Spotify"
    # Non-track entries (YouTube/X) keep the batch's shared metadata.
    assert BlaXkGrabber._entry_metadata({"title": "Some video"}, base) is base


class _MiniMonkeypatch:
    """Just enough of pytest's monkeypatch for the __main__ runner."""

    def __init__(self):
        self._undo = []

    def setattr(self, obj, name, value):
        old = getattr(obj, name)
        self._undo.append((obj, name, old))
        setattr(obj, name, value)

    def undo(self):
        for obj, name, old in reversed(self._undo):
            setattr(obj, name, old)
        self._undo = []


if __name__ == "__main__":
    # Runnable without pytest: `python tests/test_spotify_playlists.py`
    test_is_spotify_playlist_url_accepts_playlist_links()
    print("PASS: is_spotify_playlist_url accepts playlist links")
    test_is_spotify_playlist_url_rejects_other_links()
    print("PASS: is_spotify_playlist_url rejects other links")
    for name in (
        "test_extracts_titles_artists_and_queries",
        "test_skips_unplayable_tracks",
        "test_404_page_raises_helpful_error",
        "test_empty_tracklist_raises_error",
        "test_playlist_link_with_si_param_uses_clean_id",
        "test_spotify_playlist_expands_into_batch_not_single_search",
        "test_resolve_download_target_searches_and_caches",
    ):
        mp = _MiniMonkeypatch()
        try:
            globals()[name](mp)
        finally:
            mp.undo()
        print(f"PASS: {name}")
