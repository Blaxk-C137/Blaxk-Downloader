"""
First-run launch word setup.

Lets each user pick their own terminal command (launch word) on first run.
A small wrapper script is installed into ~/.local/bin that points back at
this code, and the choice is recorded in ~/.config/blaxk-grabber/launch_word.
"""
import os
import re
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


def project_root() -> Path:
    """Directory containing this checkout's main.py and pyproject.toml."""
    return Path(__file__).resolve().parent.parent


def record_project_path(config_dir: Path | None = None) -> Path:
    """Write this checkout's location to the config dir so launch
    wrappers can find the project after it has been moved/renamed."""
    cfg = config_dir or _default_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "project_path").write_text(str(project_root()) + "\n")
    return project_root()


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
    """Shell script that re-launches the GUI wherever the checkout lives.

    Hybrid resolution, in order:
      1. Fast path — the path recorded in ~/.config/blaxk-grabber/project_path
      2. Fallback — search common roots for a pyproject.toml naming
         "blaxk-grabber" (the checkout may have been renamed/moved).
    The winning path is written back to the record so the fast path heals.
    The project dir is used as PYTHONPATH so a stale editable install
    in a venv cannot break the import."""
    return _WRAPPER_TEMPLATE


_WRAPPER_TEMPLATE = """#!/bin/sh
# BlaXk Grabber launcher (generated on first run)
CFG="$HOME/.config/blaxk-grabber"
RECORD="$CFG/project_path"

# 1. Fast path: the recorded checkout location.
PROJECT=""
[ -f "$RECORD" ] && PROJECT=$(head -n 1 "$RECORD" 2>/dev/null)
[ -n "$PROJECT" ] && [ -f "$PROJECT/main.py" ] || PROJECT=""

# 2. Fallback: search for the checkout (it may have been moved/renamed).
if [ -z "$PROJECT" ]; then
    PROJECT=$(find "$HOME/Downloads" "$HOME/Documents" "$HOME/scripts" \\
        "$HOME/projects" "$HOME/dev" "$HOME" -maxdepth 5 \\
        -name pyproject.toml -type f \\
        -not -path '*/.venv/*' -not -path '*/.git/*' \\
        -not -path '*/.cache/*' -not -path '*/.config/*' \\
        -not -path '*/.local/*' -not -path '*/.claude/*' 2>/dev/null \\
        | while IFS= read -r p; do
            grep -qi '^name *= *"blaxk-grabber"' "$p" && printf '%s\\n' "$(dirname "$p")" && break
          done | head -n 1)
    [ -n "$PROJECT" ] && [ -f "$PROJECT/main.py" ] || PROJECT=""
fi

if [ -z "$PROJECT" ]; then
    echo "blaxk: can't find the BlaXk Grabber project." >&2
    echo "Looked via $RECORD and under common directories in your home." >&2
    exit 1
fi

# Heal the record so the next launch takes the fast path.
mkdir -p "$CFG"
printf '%s\\n' "$PROJECT" > "$RECORD" 2>/dev/null

PY="$PROJECT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

# PYTHONPATH makes the import work even if the venv's editable install
# still points at the old (renamed) location.
PYTHONPATH="$PROJECT" exec "$PY" "$PROJECT/main.py" "$@"
"""


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

    # Record where the checkout lives now so the wrapper's fast path
    # resolves without a search on this machine.
    record_project_path(config_dir)

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
