from dataclasses import dataclass
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


def parse_spotify_oembed(url: str) -> Metadata:
    endpoint = f"https://open.spotify.com/oembed?url={url}"
    metadata = Metadata(source_url=url, source_platform="Spotify")
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        data = response.json()
        title = normalize_text(data.get("title", ""))
        author = normalize_text(data.get("author_name", ""))
        metadata.title = title
        metadata.artist = author
        if title and author:
            metadata.query = f"{title} {author}"
        else:
            metadata.query = title or author
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
        page_title = soup.title.string if soup.title else ""

        title = normalize_text(og_title["content"] if og_title else page_title)
        description = normalize_text(og_description["content"] if og_description else "")

        metadata.title = title
        metadata.query = title

        # Try to infer artist or track from title and description.
        if " - " in title:
            parts = [part.strip() for part in title.split(" - ", 1)]
            if len(parts) == 2:
                metadata.artist, metadata.title = parts[0], parts[1]
        elif "•" in title:
            parts = [part.strip() for part in title.split("•", 1)]
            if len(parts) == 2:
                metadata.artist, metadata.title = parts[0], parts[1]

        if description and not metadata.artist:
            if "by" in description.lower():
                parts = re.split(r"[bB]y", description, maxsplit=1)
                if len(parts) == 2:
                    metadata.title = normalize_text(parts[0]) or metadata.title
                    metadata.artist = normalize_text(parts[1])

        if metadata.title and metadata.artist:
            metadata.query = f"{metadata.title} {metadata.artist}"
        elif description:
            metadata.query = f"{metadata.title} {description}".strip()
        return metadata
    except requests.RequestException:
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
