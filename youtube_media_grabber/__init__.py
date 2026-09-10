from .downloader import download_youtube, find_ffmpeg, resolve_base_output_dir
from .meta import extract_metadata, build_search_query, is_youtube_url, get_platform_name, is_url
from .searcher import search_youtube
from .spotify import extract_spotify_playlist_tracks, is_spotify_playlist_url

__all__ = [
    "download_youtube",
    "find_ffmpeg",
    "resolve_base_output_dir",
    "extract_metadata",
    "build_search_query",
    "is_youtube_url",
    "get_platform_name",
    "is_url",
    "search_youtube",
    "extract_spotify_playlist_tracks",
    "is_spotify_playlist_url",
]