from dataclasses import dataclass, replace
from urllib.parse import urlparse
import json
import re
import requests
from bs4 import BeautifulSoup

YOUTUBE_DOMAINS = ("youtube.com", "youtu.be")
SUPPORTED_PLATFORMS = {
    "spotify.com": "Spotify",
    "audiomack.com": "Audiomack",
}

MUSICBRAINZ_HEADERS = {
    "User-Agent": "BlaXkGrabber/2.0 (blaxkgrabber@proton.me)"
}


@dataclass
class Metadata:
    title: str = ""
    artist: str = ""
    album: str = ""
    release_date: str = ""
    genre: str = ""
    source_url: str = ""
    source_platform: str = ""
    query: str = ""


def normalize_text(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def is_youtube_url(url: str) -> bool:
    if not is_url(url):
        return False
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return any(domain in hostname for domain in YOUTUBE_DOMAINS)


def get_platform_name(url: str) -> str:
    if is_youtube_url(url):
        return "YouTube"
    for domain, platform in SUPPORTED_PLATFORMS.items():
        if domain in url.lower():
            return platform
    return "Web"


def _query_musicbrainz(title: str, artist: str) -> dict:
    result = {"album": "", "release_date": "", "genre": ""}
    if not title:
        return result

    query_parts = [f'recording:"{title}"']
    if artist:
        query_parts.append(f'artist:"{artist}"')
    query = " AND ".join(query_parts)

    try:
        response = requests.get(
            "https://musicbrainz.org/ws/2/recording",
            params={"query": query, "limit": 1, "fmt": "json"},
            headers=MUSICBRAINZ_HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, json.JSONDecodeError):
        return result

    recordings = data.get("recordings", [])
    if not recordings:
        return result

    recording = recordings[0]

    tags = recording.get("tags") or []
    if tags:
        sorted_tags = sorted(tags, key=lambda t: t.get("count", 0), reverse=True)
        result["genre"] = normalize_text(sorted_tags[0].get("name", ""))

    releases = recording.get("releases") or []
    if releases:
        dated = [r for r in releases if r.get("date")]
        release = dated[0] if dated else releases[0]
        result["release_date"] = release.get("date", "")
        rg = release.get("release-group") or {}
        result["album"] = normalize_text(rg.get("title") or release.get("title", ""))

    return result


def parse_spotify_oembed(url: str) -> Metadata:
    endpoint = f"https://open.spotify.com/oembed?url={url}"
    metadata = Metadata(source_url=url, source_platform="Spotify")
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        data = response.json()
        title = normalize_text(data.get("title", ""))
        artist = normalize_text(data.get("author_name", ""))
        metadata.title = title
        metadata.artist = artist
        metadata.query = f"{title} {artist}".strip() if title or artist else ""

        if title or artist:
            mb = _query_musicbrainz(title, artist)
            metadata.album = mb["album"]
            metadata.release_date = mb["release_date"]
            metadata.genre = mb["genre"]

        return metadata
    except (requests.RequestException, json.JSONDecodeError):
        return Metadata(source_url=url, source_platform="Spotify")


def parse_page_metadata(url: str) -> Metadata:
    metadata = Metadata(source_url=url, source_platform=get_platform_name(url))
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        og_title = soup.find("meta", property="og:title")
        og_description = soup.find("meta", property="og:description")
        og_audio_artist = soup.find("meta", property="music:musician")
        page_title = soup.title.string if soup.title else ""

        title = normalize_text(og_title["content"] if og_title else page_title)
        description = normalize_text(og_description["content"] if og_description else "")

        metadata.title = title
        metadata.query = title

        for sep in (" - ", " – ", " — ", "•", "|"):
            if sep in title:
                parts = [p.strip() for p in title.split(sep, 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    metadata.artist, metadata.title = parts[0], parts[1]
                    break

        if og_audio_artist and not metadata.artist:
            metadata.artist = normalize_text(og_audio_artist.get("content", ""))

        if description and not metadata.artist:
            match = re.search(r"\bby\s+(.+?)(?:\s*[·•|]|$)", description, re.IGNORECASE)
            if match:
                metadata.artist = normalize_text(match.group(1))

        if metadata.title and metadata.artist:
            metadata.query = f"{metadata.title} {metadata.artist}"
        elif description:
            metadata.query = f"{metadata.title} {description}".strip()

        if metadata.title or metadata.artist:
            mb = _query_musicbrainz(metadata.title, metadata.artist)
            metadata.album = mb["album"]
            metadata.release_date = mb["release_date"]
            metadata.genre = mb["genre"]

        return metadata
    except requests.RequestException:
        return metadata


def enrich_from_ytdlp(metadata: Metadata, yt_info: dict) -> Metadata:
    # Work on a copy so a shared/base Metadata object is never mutated. Without
    # this, the first track in a batch would populate the shared object and every
    # later track would keep the first track's title/artist/album/etc.
    metadata = replace(metadata)
    if not metadata.title:
        metadata.title = normalize_text(yt_info.get("title", ""))
    if not metadata.artist:
        metadata.artist = normalize_text(
            yt_info.get("artist") or yt_info.get("creator") or yt_info.get("uploader") or ""
        )
    if not metadata.album:
        metadata.album = normalize_text(yt_info.get("album", ""))
    if not metadata.release_date:
        raw_date = yt_info.get("release_date") or yt_info.get("upload_date") or ""
        if raw_date and len(raw_date) == 8:
            metadata.release_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
    if not metadata.genre:
        cats = yt_info.get("categories") or []
        if cats:
            metadata.genre = normalize_text(cats[0])
        genre_tag = yt_info.get("genre", "")
        if genre_tag and not metadata.genre:
            metadata.genre = normalize_text(genre_tag)

    # MusicBrainz enrichment if still missing album/genre
    if metadata.title and (not metadata.album or not metadata.genre):
        mb = _query_musicbrainz(metadata.title, metadata.artist)
        if not metadata.album:
            metadata.album = mb["album"]
        if not metadata.release_date:
            metadata.release_date = mb["release_date"]
        if not metadata.genre:
            metadata.genre = mb["genre"]

    return metadata


def extract_metadata(source: str) -> Metadata:
    source = source.strip()
    if not source:
        return Metadata()

    if not is_url(source):
        return Metadata(query=normalize_text(source), source_platform="Search")

    source_platform = get_platform_name(source)

    if source_platform == "YouTube":
        return Metadata(source_url=source, source_platform="YouTube", query=source)

    if source_platform == "Spotify":
        metadata = parse_spotify_oembed(source)
        if metadata.query:
            return metadata

    return parse_page_metadata(source)


def build_search_query(metadata: Metadata) -> str:
    if metadata.query:
        return metadata.query
    pieces = []
    if metadata.title:
        pieces.append(metadata.title)
    if metadata.artist:
        pieces.append(metadata.artist)
    return " ".join(pieces).strip()