"""
First-run launch word setup.

Lets each user pick their own terminal command (launch word) on first run.
A small wrapper script is installed into ~/.local/bin that points back at
this code, and the choice is recorded in ~/.config/blaxk-grabber/launch_word.
"""
import os
import re
import shutil
import sys
from pathlib import Path

SKIPPED = "skipped"

# Commands we never want to shadow with a launcher.
RESERVED_WORDS = {
    "ls", "cd", "pwd", "rm", "cp", "mv", "cat", "grep", "find", "echo",
    "python", "python3", "pip", "pip3", "sudo", "apt", "dnf", "yum",
    "git", "curl", "wget", "ffmpeg", "sh", "bash", "zsh", "nano", "vim",
    "blaxk",
}

_WORD_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,19}$")


class LauncherInstallError(Exception):
    """Raised when the wrapper script cannot be installed."""


def validate_launch_word(word: str) -> str | None:
    """Return an error message for an invalid word, or None if it's fine."""
    word = (word or "").strip().lower()
    if not word:
        return "Please enter a launch word."
    if not _WORD_RE.match(word):
        return "Use 2-20 characters: lowercase letters, numbers and dashes only."
    if word in RESERVED_WORDS:
        return f"'{word}' is a system command — pick a different word."
    return None


def _default_config_dir() -> Path:
    return Path.home() / ".config" / "blaxk-grabber"


def _default_bin_dir() -> Path:
    return Path.home() / ".local" / "bin"


def get_launch_word(config_dir: Path | None = None) -> str | None:
    """
    Return the configured launch word, SKIPPED if the user declined,
    or None on a fresh install (first run).
    """
    marker = (config_dir or _default_config_dir()) / "launch_word"
    if not marker.exists():
        return None
    word = marker.read_text().strip().lower()
    return word or None


def mark_skipped(config_dir: Path | None = None) -> None:
    """Record that the user declined to pick a launch word."""
    d = config_dir or _default_config_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "launch_word").write_text(SKIPPED + "\n")


def _wrapper_content() -> str:
    """Shell script that re-launches the GUI using the interpreter that
    ran this install and this checkout's main.py."""
    project_root = Path(__file__).resolve().parent.parent
    main_py = project_root / "main.py"
    quoted_py = str(main_py).replace("'", "'\\''")
    quoted_interp = sys.executable.replace("'", "'\\''")
    return (
        "#!/bin/sh\n"
        "# BlaXk Grabber launcher (generated on first run)\n"
        f"exec '{quoted_interp}' '{quoted_py}' \"$@\"\n"
    )


def _is_our_launcher(path: Path) -> bool:
    try:
        return "BlaXk Grabber launcher" in path.read_text()
    except OSError:
        return False


def install_launch_word(
    word: str,
    config_dir: Path | None = None,
    bin_dir: Path | None = None,
) -> Path:
    """
    Validate and install the launch word: write the marker file and create
    an executable wrapper in bin_dir. Returns the wrapper path.

    Raises ValueError for a bad word, LauncherInstallError if the wrapper
    destination is occupied by something that isn't ours.
    """
    word = (word or "").strip().lower()
    error = validate_launch_word(word)
    if error:
        raise ValueError(error)

    bin_dir = bin_dir or _default_bin_dir()
    wrapper = bin_dir / word

    if wrapper.exists() and not _is_our_launcher(wrapper):
        raise LauncherInstallError(
            f"'{word}' already exists in {bin_dir} (not a BlaXk Grabber launcher). "
            "Pick a different word or remove that file first."
        )

    # Remove a previous launcher of ours so changing words cleans up.
    old = get_launch_word(config_dir)
    if old and old != SKIPPED and old != word:
        old_wrapper = bin_dir / old
        if _is_our_launcher(old_wrapper):
            old_wrapper.unlink(missing_ok=True)

    bin_dir.mkdir(parents=True, exist_ok=True)
    cfg = config_dir or _default_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)

    wrapper.write_text(_wrapper_content())
    wrapper.chmod(0o755)
    (cfg / "launch_word").write_text(word + "\n")

    return wrapper


def bin_dir_on_path(bin_dir: Path | None = None) -> bool:
    """Check whether bin_dir (default ~/.local/bin) is on PATH."""
    d = str((bin_dir or _default_bin_dir()).resolve())
    return d in os.environ.get("PATH", "").split(os.pathsep)
