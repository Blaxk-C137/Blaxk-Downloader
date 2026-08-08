import os
import re
import shutil
from pathlib import Path
from typing import Optional

import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

from .meta import Metadata, enrich_from_ytdlp


def resolve_base_output_dir(base_dir: str | None = None) -> Path:
    if base_dir:
        path = Path(base_dir).expanduser()
    else:
        path = Path.home() / "Downloads" / "BlaXk_Grabber"
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_filename(value: str) -> str:
    if not value:
        return ""
    result = re.sub(r"[\\/*?:\"<>|]", "", value)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def find_ffmpeg() -> Optional[str]:
    for command in ["ffmpeg", "ffmpeg.exe"]:
        path = shutil.which(command)
        if path:
            return path
    return None


def get_expected_output_path(
    url: str,
    format_choice: str,
    base_output_dir: str | None = None,
    ffmpeg_path: str | None = None,
) -> Path:
    output_dir = resolve_base_output_dir(base_output_dir)
    audio_dir = output_dir / "audio"
    video_dir = output_dir / "video"
    outtmpl = (
        str(audio_dir / "%(title)s.%(ext)s")
        if format_choice == "audio"
        else str(video_dir / "%(title)s.%(ext)s")
    )
    ydl_opts = {
        "quiet": True,
        "outtmpl": outtmpl,
        "noplaylist": True,
        "ffmpeg_location": ffmpeg_path,
        "prefer_ffmpeg": True,
        "windowsfilenames": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        filename = ydl.prepare_filename(info)
        if format_choice == "audio":
            stem = os.path.splitext(filename)[0]
            filename = f"{stem}.mp3"
        return Path(filename)


def embed_mp3_metadata(filepath: str, metadata: Metadata | dict) -> None:
    if not filepath.lower().endswith(".mp3"):
        return

    try:
        audio = EasyID3(filepath)
    except ID3NoHeaderError:
        audio = EasyID3()
        audio.save(filepath)
        audio = EasyID3(filepath)

    def val(key: str, default: str = "") -> str:
        if isinstance(metadata, Metadata):
            return getattr(metadata, key, default) or default
        return metadata.get(key, default) if metadata else default

    audio["title"] = val("title")
    audio["artist"] = val("artist")
    audio["album"] = val("album") or val("title")
    audio["genre"] = val("genre", "Unknown")
    album_artist = val("artist")
    if album_artist:
        audio["albumartist"] = album_artist

    release_date = val("release_date")
    if release_date:
        audio["date"] = release_date[:4]

    audio.save(filepath)


def download_single(
    url: str,
    format_choice: str,
    base_output_dir: str | None = None,
    ffmpeg_path: str | None = None,
    metadata: Metadata | None = None,
    progress_callback: callable | None = None,
) -> str:
    """Download a single video/audio. Returns the final filepath."""
    output_dir = resolve_base_output_dir(base_output_dir)
    audio_dir = output_dir / "audio"
    video_dir = output_dir / "video"
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = (
        str(audio_dir / "%(title)s.%(ext)s")
        if format_choice == "audio"
        else str(video_dir / "%(title)s.%(ext)s")
    )

    final_filepath = ""

    def hook(d):
        if progress_callback:
            progress_callback(d)

    class MetadataPostprocessor(yt_dlp.postprocessor.PostProcessor):
        def run(self, info):
            nonlocal final_filepath
            filepath = info.get("filepath") or info.get("filename")
            final_filepath = filepath or ""
            if filepath and filepath.lower().endswith(".mp3"):
                resolved_metadata = enrich_from_ytdlp(metadata or Metadata(), info)
                embed_mp3_metadata(filepath, resolved_metadata)
            return [], info

    ydl_opts = {
        "quiet": True,
        "progress_hooks": [hook],
        "outtmpl": outtmpl,
        "noplaylist": True,
        "ffmpeg_location": ffmpeg_path,
        "writethumbnail": format_choice == "audio",
        "prefer_ffmpeg": True,
        "windowsfilenames": True,
        "postprocessor_args": ["-id3v2_version", "3", "-write_id3v1", "1"],
    }

    if format_choice == "audio":
        ydl_opts.update({
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
                {"key": "EmbedThumbnail"},
                {"key": "FFmpegMetadata"},
            ],
            "writethumbnail": True,
        })
    else:
        ydl_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/mp4",
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_post_processor(MetadataPostprocessor())
        ydl.download([url])

    return final_filepath


# Legacy wrapper for compatibility
def download_youtube(
    url: str,
    format_choice: str,
    base_output_dir: str | None = None,
    ffmpeg_path: str | None = None,
    metadata: Metadata | None = None,
    allow_playlist: bool = False,
    progress_callback: callable | None = None,
) -> None:
    download_single(
        url, format_choice, base_output_dir, ffmpeg_path, metadata, progress_callback
    )