# YouTube Media Grabber

A console-based downloader focused on YouTube. If you paste a Spotify, Audiomack, or other web link, the tool extracts metadata from the page and searches YouTube for the matching song.

## Features

- Direct YouTube audio/video downloads
- Metadata lookup for Spotify/Audiomack links
- YouTube search fallback for non-YouTube sources
- MP3 metadata embedding for audio downloads
- Nice progress display with Rich
- Cross-platform download folder support

## Installation

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Install `ffmpeg` if it is not already installed.

## Usage

Run the downloader:

```bash
python main.py
```

Enter a URL or search query when prompted.

## Supported inputs

- YouTube links
- Spotify track links
- Audiomack links
- Plain search queries

The downloader always resolves to a YouTube video before downloading.
