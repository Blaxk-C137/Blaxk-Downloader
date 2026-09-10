"""
Spotify playlist support.

Spotify's main playlist pages are client-side rendered (no track data in
the HTML), but the public *embed* page ships the full track list as a
`__NEXT_DATA__` JSON blob — no login, no API key. We fetch that, pull out
each track's title + artist, and let the GUI resolve each one to a YouTube
download at download time.
"""
import json
import re
from urllib.parse import urlparse

import requests

_EMBED_TIMEOUT = 15
_PLAYLIST_PATH_RE = re.compile(r"^/playlist/([A-Za-z0-9]+)")
_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def is_spotify_playlist_url(url: str) -> bool:
    """True for open.spotify.com/playlist/... links (any query params)."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = (parsed.hostname or "").lower()
    if hostname != "open.spotify.com" and hostname != "www.open.spotify.com":
        return False
    return bool(_PLAYLIST_PATH_RE.match(parsed.path or ""))


def _embed_url(playlist_url: str) -> str:
    """Rebuild the embed URL from the bare playlist id (drops ?si= tracking)."""
    match = _PLAYLIST_PATH_RE.match(urlparse(playlist_url.strip()).path or "")
    playlist_id = match.group(1) if match else ""
    return f"https://open.spotify.com/embed/playlist/{playlist_id}"


def _parse_track_list(embed_html: str) -> list[dict]:
    match = _NEXT_DATA_RE.search(embed_html)
    if not match:
        raise ValueError(
            "Could not read this Spotify playlist — the page format may have "
            "changed, or the playlist is unavailable."
        )
    try:
        data = json.loads(match.group(1))
        entity = data["props"]["pageProps"]["state"]["data"]["entity"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise ValueError(
            "Could not read this Spotify playlist. Is it public? Private "
            "playlists can't be downloaded."
        )

    tracks = []
    for entry in entity.get("trackList") or []:
        if entry is None:
            continue
        # Region-locked/unavailable tracks can't be searched meaningfully.
        if entry.get("isPlayable") is False:
            continue
        title = (entry.get("title") or "").strip()
        artist = (entry.get("subtitle") or "").strip()
        if not title:
            continue
        duration_ms = entry.get("duration") or 0
        tracks.append({
            # Display title matches the final file's "Artist - Track" shape.
            "title": f"{artist} - {title}" if artist else title,
            "link": None,  # resolved per-track via YouTube search at download time
            "query": f"{title} {artist}".strip(),
            "duration": round(duration_ms / 1000) if duration_ms else "",
            # Bare values for per-track ID3 tags in the GUI's do_download.
            "track": title,
            "artist": artist,
        })
    return tracks


def extract_spotify_playlist_tracks(playlist_url: str) -> list[dict]:
    """Return the tracks of a public Spotify playlist.

    Each entry: {"title": "Artist - Track", "link": None, "query": "...",
    "duration": seconds}. Raises ValueError with a user-facing message if
    the playlist can't be read.
    """
    response = requests.get(
        _embed_url(playlist_url),
        timeout=_EMBED_TIMEOUT,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()

    tracks = _parse_track_list(response.text)
    if not tracks:
        raise ValueError(
            "No tracks found in this Spotify playlist (or they are all "
            "unavailable in your region)."
        )
    return tracks
