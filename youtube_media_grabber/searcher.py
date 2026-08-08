import yt_dlp


def search_youtube(query: str, max_results: int = 1) -> dict:
    search_query = f"ytsearch{max_results}:{query}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)

    entries = info.get("entries") or []
    if not entries:
        raise ValueError(f"No YouTube results found for query: {query}")

    first = entries[0]
    link = first.get("webpage_url") or first.get("url")
    if not link and first.get("id"):
        link = f"https://www.youtube.com/watch?v={first.get('id')}"
    return {
        "title": first.get("title", ""),
        "link": link or "",
        "duration": first.get("duration", ""),
        "channel": first.get("uploader", ""),
        "views": first.get("view_count", ""),
    }


def extract_playlist_urls(url: str) -> list[dict]:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        return []

    entries = info.get("entries") or []
    results = []
    for entry in entries:
        if entry is None:
            continue
        link = entry.get("webpage_url") or entry.get("url")
        if not link and entry.get("id"):
            link = f"https://www.youtube.com/watch?v={entry['id']}"
        if link:
            results.append({
                "title": entry.get("title", "Unknown"),
                "link": link,
                "duration": entry.get("duration", ""),
            })
    return results