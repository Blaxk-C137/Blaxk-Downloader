<div align="center">

# 🔴 BlaXk Grabber

### YouTube Media Grabber with Spotify & Audiomack Metadata Lookup

[![Python](https://img.shields.io/badge/Python-3.11+-red?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![yt-dlp](https://img.shields.io/badge/Powered_by-yt--dlp-red?style=for-the-badge)](https://github.com/yt-dlp/yt-dlp)
[![License](https://img.shields.io/badge/License-MIT-black?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux_|_Windows_|_macOS-black?style=for-the-badge)]()

<br>

> **Paste a link. Pick a format. Hit GRAB IT.**
>
> YouTube • Spotify • Audiomack → MP3 / MP4

<br>

</div>

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🎵 | **Audio & Video** | Download as MP3 (192 kbps) or MP4 (best available quality) |
| 📋 | **Playlist Support** | Grab entire YouTube playlists in one go |
| ⚡ | **Concurrent Downloads** | 1–8 simultaneous downloads via a configurable slider |
| 🔍 | **Smart Search** | Type a track name — BlaXk finds it on YouTube automatically |
| 🎧 | **Spotify → YouTube** | Paste a Spotify link; metadata is extracted and matched on YouTube |
| 🔊 | **Audiomack → YouTube** | Same seamless flow for Audiomack links |
| 🏷️ | **Full ID3 Metadata** | Title, artist, album, genre, date, and album art via MusicBrainz + yt-dlp |
| 📂 | **Duplicate Detection** | Scans your output folder before each download — skips files that already exist |
| 🔄 | **Auto-Retry** | Failed downloads are automatically retried up to 2× after the batch finishes |
| 🖥️ | **Glassmorphic GUI** | Dark red/black themed interface with per-file progress bars |
| 🔇 | **Silent Terminal** | Zero console output — everything surfaces inside the GUI |

---

## 🚀 Quick Start

### Prerequisites

- Python **3.11+**
- `ffmpeg` installed and available on your system `PATH`

> **Install ffmpeg:**
> - **Ubuntu/Debian:** `sudo apt install ffmpeg`
> - **macOS:** `brew install ffmpeg`
> - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/blaxk-grabber.git
cd blaxk-grabber

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch
python main.py
```

---

## 🎯 Usage

### Supported Input Types

| Input | Example |
|---|---|
| YouTube video URL | `https://youtube.com/watch?v=...` |
| YouTube playlist URL | `https://youtube.com/playlist?list=...` |
| Spotify track/album/playlist | `https://open.spotify.com/track/...` |
| Audiomack track/album/playlist | `https://audiomack.com/...` |
| Plain search query | `Kendrick Lamar - Not Like Us` |

### Step-by-step

1. **Paste** a URL or type a search query in the input box
2. **Choose** your output format — `MP3` or `MP4`
3. **Set** the concurrency slider (how many files download at once)
4. **Pick** your output folder
5. **Hit** `⬇ GRAB IT` — per-file progress bars update in real time

### Spotify & Audiomack Flow

BlaXk Grabber does **not** download directly from Spotify or Audiomack. Instead, it:

1. Extracts track metadata (title, artist, album, artwork) from the link
2. Searches YouTube for the best match
3. Downloads from YouTube and embeds the original metadata as ID3 tags

---

## ⚙️ Configuration

All settings are managed through the GUI. There are no config files to edit manually.

| Setting | Default | Notes |
|---|---|---|
| Output format | `MP3` | Switch to MP4 for video |
| Audio bitrate | `192 kbps` | Fixed for consistent quality |
| Concurrent workers | `3` | Adjustable from 1–8 via slider |
| Output directory | `~/Downloads` | Changeable per session |
| Auto-retry limit | `2` | Retries happen after the full batch |

---

## 🏗️ Project Structure

```
blaxk-grabber/
├── main.py              # Entry point — launches the GUI
├── gui/
│   ├── app.py           # Main window and layout
│   ├── components.py    # Progress bars, buttons, input fields
│   └── theme.py         # Glassmorphic dark red/black theme
├── core/
│   ├── downloader.py    # yt-dlp wrapper, concurrent queue
│   ├── metadata.py      # MusicBrainz + yt-dlp ID3 tag injection
│   ├── resolver.py      # Spotify / Audiomack → YouTube lookup
│   └── search.py        # Plain-text YouTube search
├── utils/
│   ├── dedup.py         # Duplicate file detection
│   └── retry.py         # Auto-retry logic
├── requirements.txt
└── README.md
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | YouTube downloading engine |
| [`spotipy`](https://github.com/spotipy-dev/spotipy) | Spotify metadata extraction |
| [`musicbrainzngs`](https://github.com/alastair/python-musicbrainzngs) | MusicBrainz metadata lookup |
| [`mutagen`](https://github.com/quodlibet/mutagen) | ID3 tag writing |
| `tkinter` / `customtkinter` | GUI framework |
| `concurrent.futures` | Concurrent download threading |

Install all at once:

```bash
pip install -r requirements.txt
```

---

## 🛠️ Troubleshooting

**`ffmpeg` not found**
→ Make sure ffmpeg is installed and on your system `PATH`. Verify with `ffmpeg -version`.

**Spotify link not resolving**
→ Spotify metadata lookup requires a valid Spotify Developer API key. Set `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` as environment variables or in a `.env` file.

**Download stuck / no progress**
→ Check your internet connection. The auto-retry mechanism will kick in for failed items after the rest of the batch completes.

**Duplicate files being skipped unexpectedly**
→ BlaXk checks filenames in the output folder before downloading. Rename or move the existing file if you want a fresh download.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

```bash
# Fork → clone → branch
git checkout -b feature/your-feature-name

# Make changes, then
git commit -m "feat: describe your change"
git push origin feature/your-feature-name
# Open a PR
```

Please make sure your code runs without errors before submitting.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built by [BlaXk](https://github.com/yourusername) · Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)

</div>
