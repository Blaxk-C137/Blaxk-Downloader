"""Regression tests for the shutdown bgerror crash and None-title batch crash.

1. bgerror "invalid command name ...update" — customtkinter's internal
   AppearanceModeTracker `after` loop is never cancelled when the app is
   destroyed; Tcl then fires a timer whose command was deleted. BlaXkGrabber
   must therefore cancel pending timers itself on destroy and expose a
   thread-safe scheduler.
2. Playlists can contain dead/private entries whose yt-dlp metadata has
   title=None. Those must fall back to a placeholder instead of crashing
   DownloadRow (TypeError: object of type 'NoneType' has no len()).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youtube_media_grabber.searcher as searcher


class _FakeYDL:
    """Stands in for yt_dlp.YoutubeDL; yields entries with a None title."""

    def __init__(self, opts):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def extract_info(self, url, download=False):
        return {
            "entries": [
                {"id": "abc", "title": None,
                 "webpage_url": "https://youtu.be/abc"},
                {"id": "def", "title": "Real Title",
                 "webpage_url": "https://youtu.be/def"},
            ]
        }


def test_playlist_entries_with_none_title_get_fallback(monkeypatch):
    """Dead playlist entries (title=None) must not leak None into the GUI."""
    monkeypatch.setattr(searcher.yt_dlp, "YoutubeDL", _FakeYDL)
    entries = searcher.extract_playlist_urls("https://youtube.com/playlist?list=x")
    assert entries[0]["title"] == "Unknown"
    assert entries[1]["title"] == "Real Title"


def test_gui_shutdown_safety_exists():
    """The app must override destroy(), and offer a thread-safe scheduler
    plus a WM close handler, so worker threads can't schedule UI work on a
    destroyed Tk app (RuntimeError: main thread is not in main loop)."""
    from youtube_media_grabber.gui import BlaXkGrabber

    assert hasattr(BlaXkGrabber, "_schedule")
    assert hasattr(BlaXkGrabber, "_on_close")
    # destroy() must be overridden on BlaXkGrabber itself (not inherited)
    assert "destroy" in vars(BlaXkGrabber)


if __name__ == "__main__":
    # Runnable without pytest: `python tests/test_shutdown_safety.py`
    class _MP:
        @staticmethod
        def setattr(obj, name, value):
            setattr(obj, name, value)

    test_playlist_entries_with_none_title_get_fallback(_MP)
    print("PASS: playlist entries with None title get fallback")
    try:
        test_gui_shutdown_safety_exists()
        print("PASS: gui shutdown safety exists")
    except ImportError as exc:
        print(f"SKIP: gui shutdown safety (needs customtkinter installed) — {exc}")
