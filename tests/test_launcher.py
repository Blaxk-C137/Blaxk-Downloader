import shutil
import stat
from pathlib import Path

import pytest

from youtube_media_grabber import launcher


@pytest.fixture
def config_dir(tmp_path) -> Path:
    d = tmp_path / "config" / "blaxk-grabber"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def bin_dir(tmp_path) -> Path:
    d = tmp_path / "local" / "bin"
    d.mkdir(parents=True)
    return d


class TestValidateLaunchWord:
    def test_accepts_simple_word(self):
        assert launcher.validate_launch_word("grab") is None

    def test_accepts_word_with_numbers_and_dashes(self):
        assert launcher.validate_launch_word("my-grabber-2") is None

    def test_rejects_empty(self):
        assert launcher.validate_launch_word("") is not None

    def test_rejects_too_short(self):
        assert launcher.validate_launch_word("a") is not None

    def test_rejects_too_long(self):
        assert launcher.validate_launch_word("x" * 21) is not None

    def test_rejects_bad_characters(self):
        for word in ["my word", "rm -rf", "../evil", "word;ls", "word&ls"]:
            assert launcher.validate_launch_word(word) is not None, word

    def test_rejects_reserved_commands(self):
        for word in ["ls", "cd", "python", "pip", "sudo", "rm", "blaxk"]:
            assert launcher.validate_launch_word(word) is not None, word


class TestGetLaunchWord:
    def test_none_when_not_configured(self, config_dir):
        assert launcher.get_launch_word(config_dir) is None

    def test_returns_word_after_install(self, config_dir, bin_dir):
        launcher.install_launch_word("grab", config_dir, bin_dir)
        assert launcher.get_launch_word(config_dir) == "grab"

    def test_returns_skipped_marker(self, config_dir):
        launcher.mark_skipped(config_dir)
        assert launcher.get_launch_word(config_dir) == launcher.SKIPPED


class TestInstallLaunchWord:
    def test_creates_executable_wrapper(self, config_dir, bin_dir):
        path = launcher.install_launch_word("grab", config_dir, bin_dir)
        assert path == bin_dir / "grab"
        assert path.exists()
        assert path.stat().st_mode & stat.S_IXUSR
        content = path.read_text()
        # Wrapper must exec an interpreter against this project's main.py
        assert content.startswith("#!/bin/sh")
        assert "main.py" in content
        assert "exec" in content

    def test_writes_marker_file(self, config_dir, bin_dir):
        launcher.install_launch_word("grab", config_dir, bin_dir)
        assert (config_dir / "launch_word").read_text().strip() == "grab"

    def test_creates_bin_dir_if_missing(self, config_dir, tmp_path):
        bin_dir = tmp_path / "newbin"
        path = launcher.install_launch_word("grab", config_dir, bin_dir)
        assert path.exists()

    def test_refuses_to_overwrite_existing_foreign_file(self, config_dir, bin_dir):
        (bin_dir / "grab").write_text("#!/bin/sh\nsome other tool\n")
        with pytest.raises(launcher.LauncherInstallError):
            launcher.install_launch_word("grab", config_dir, bin_dir)

    def test_overwrites_own_launcher(self, config_dir, bin_dir):
        launcher.install_launch_word("grab", config_dir, bin_dir)
        # Installing again (e.g. name change, re-setup) must succeed
        path = launcher.install_launch_word("grab", config_dir, bin_dir)
        assert path.exists()

    def test_rejects_invalid_word(self, config_dir, bin_dir):
        with pytest.raises(ValueError):
            launcher.install_launch_word("bad word", config_dir, bin_dir)


class TestChangeLaunchWord:
    def test_old_wrapper_removed(self, config_dir, bin_dir):
        launcher.install_launch_word("grab", config_dir, bin_dir)
        old = bin_dir / "grab"
        launcher.install_launch_word("media", config_dir, bin_dir)
        assert not old.exists()
        assert (bin_dir / "media").exists()
        assert launcher.get_launch_word(config_dir) == "media"


class TestMarkSkipped:
    def test_marker_prevents_reask(self, config_dir):
        launcher.mark_skipped(config_dir)
        assert launcher.get_launch_word(config_dir) == launcher.SKIPPED
