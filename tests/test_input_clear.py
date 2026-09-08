"""Tests for the auto-clear-on-success input behavior and Enter-to-download."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _FakeEntry:
    """Minimal CTkEntry stand-in that records delete() calls."""

    def __init__(self) -> None:
        self.cleared = False

    def delete(self, first, last):
        self.cleared = True


class _FakeButton:
    def configure(self, **kwargs):
        pass


def _make_app():
    """A BlaXkGrabber instance without launching a real Tk window."""
    from youtube_media_grabber.gui import BlaXkGrabber

    app = BlaXkGrabber.__new__(BlaXkGrabber)
    app._destroyed = False
    app.is_downloading = True
    app._batch_ok = False
    app.input_entry = _FakeEntry()
    app.download_btn = _FakeButton()
    return app


def test_finish_download_clears_input_on_success():
    app = _make_app()
    app._batch_ok = True
    app._finish_download()
    assert app.input_entry.cleared, "input should be cleared after a successful batch"


def test_finish_download_keeps_input_on_failure():
    app = _make_app()
    app._batch_ok = False
    app._finish_download()
    assert not app.input_entry.cleared, "input must stay so the user can retry"


def test_finish_download_resets_batch_flag():
    app = _make_app()
    app._batch_ok = True
    app._finish_download()
    assert app._batch_ok is False, "flag must be reset for the next run"


def test_enter_key_bound_to_download():
    """The input entry binds <Return> to _on_download in _build_ui."""
    import inspect
    from youtube_media_grabber.gui import BlaXkGrabber

    source = inspect.getsource(BlaXkGrabber._build_ui)
    assert 'bind("<Return>"' in source


if __name__ == "__main__":
    # Runnable without pytest: `python tests/test_input_clear.py`
    test_finish_download_clears_input_on_success()
    print("PASS: input cleared on success")
    test_finish_download_keeps_input_on_failure()
    print("PASS: input kept on failure")
    test_finish_download_resets_batch_flag()
    print("PASS: batch flag reset")
    test_enter_key_bound_to_download()
    print("PASS: <Return> bound in _build_ui")
