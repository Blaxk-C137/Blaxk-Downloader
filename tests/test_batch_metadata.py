"""Regression tests for the batch-download metadata bug and GUI method wiring."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_media_grabber.meta import Metadata, enrich_from_ytdlp


def test_enrich_does_not_mutate_shared_metadata():
    """A shared base Metadata object must not be polluted by enrichment.

    Reproduces the batch bug: the first song's data being reused for the rest.
    """
    base = Metadata(source_platform="YouTube")

    info1 = {"title": "Song One", "artist": "Artist One",
             "album": "Album One", "genre": "Rock", "upload_date": "20200101"}
    info2 = {"title": "Song Two", "artist": "Artist Two",
             "album": "Album Two", "genre": "Jazz", "upload_date": "20210202"}

    r1 = enrich_from_ytdlp(base, info1)
    r2 = enrich_from_ytdlp(base, info2)

    # Each result reflects its own source info
    assert r1.title == "Song One" and r1.artist == "Artist One"
    assert r2.title == "Song Two" and r2.artist == "Artist Two"

    # The shared base object is never mutated
    assert base.title == "" and base.artist == ""


def test_gui_download_methods_are_bound_to_class():
    """The download orchestration functions must be methods of BlaXkGrabber."""
    from youtube_media_grabber.gui import BlaXkGrabber

    for name in ("_resolve_and_download", "_download_batch", "_finish_download"):
        assert hasattr(BlaXkGrabber, name), f"BlaXkGrabber is missing method {name!r}"


if __name__ == "__main__":
    # Runnable without pytest: `python tests/test_batch_metadata.py`
    test_enrich_does_not_mutate_shared_metadata()
    print("PASS: enrich does not mutate shared metadata")
    try:
        test_gui_download_methods_are_bound_to_class()
        print("PASS: gui download methods are bound to class")
    except ImportError as exc:
        print(f"SKIP: gui method check (needs customtkinter installed) — {exc}")

