 
 
 
 
 
 ```markdown
<div align="center">

# 🔴 BlaXk Grabber

### YouTube Media Grabber with Spotify & Audiomack Metadata Lookup

[![Python](https://img.shields.io/badge/Python-3.11+-red?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-black?style=for-the-badge)](LICENSE)
[![yt-dlp](https://img.shields.io/badge/Powered_by-yt--dlp-red?style=for-the-badge)](https://github.com/yt-dlp/yt-dlp)
[![Platform](https://img.shields.io/badge/Platform-Linux_|_Windows_|_macOS-black?style=for-the-badge)]()

<br>

<img src="https://img.shields.io/badge/⬇_GRAB_IT-ff2d3b?style=for-the-badge&logoColor=white" height="40">

<br><br>

**Paste a link. Pick a format. Hit GRAB IT.**

YouTube • Spotify • Audiomack → MP3 / MP4

---

</div>

## ✨ Features

| Feature | Description |
|---|---|
| 🎵 **Audio & Video** | Download as MP3 (192kbps) or MP4 (best quality) |
| 📋 **Playlist Support** | Grab entire YouTube playlists in one click |
| ⚡ **Concurrent Downloads** | Download 1–8 files simultaneously (configurable slider) |
| 🔍 **Smart Search** | Type a song name — BlaXk finds it on YouTube automatically |
| 🎧 **Spotify → YouTube** | Paste a Spotify link — metadata is extracted and the song is found on YouTube |
| 🔊 **Audiomack → YouTube** | Same for Audiomack links |
| 🏷️ **Full Metadata** | ID3 tags: title, artist, album, genre, date, album art (via MusicBrainz + yt-dlp) |
| 📂 **Duplicate Detection** | Scans your folder before downloading — skips files that already exist |
| 🔄 **Auto-Retry** | Failed downloads are automatically retried up to 2 times after the batch finishes |
| 🖥️ **Glassmorphic GUI** | Dark red/black themed interface with per-file progress bars |
| 🔇 **Silent Terminal** | Zero console output — everything stays in the GUI |

---

## 📸 Interface

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   BlaXk Grabber                              v2.0      │
│   YouTube • Spotify • Audiomack → MP3 / MP4             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ URL or search query                             │    │
│  │ [Paste link or type search here...            ] │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Format              Download folder             │    │
│  │ [🎵 MP3] [🎬 MP4]   [~/Downloads/BlaXk] [📁]   │    │
│  │                                                 │    │
│  │ Concurrent downloads                            │    │
│  │ ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  4    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │              ⬇  GRAB IT                         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Download Queue                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ #1  Song Title Here          ████████░░  78%    │    │
│  │ #2  Another Song             ██████████  Done ✓ │    │
│  │ #3  Already Had This         ██████████  Exists │    │
│  │ #4  One More Track           ██░░░░░░░░  21%    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Log                                                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ [14:32:01] 📋 Found 12 videos in playlist       │    │
│  │ [14:32:01] ⏭ Skipping 3 already downloaded      │    │
│  │ [14:32:05] ✅ Finished: Song Title Here          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.11+**
- **ffmpeg** (required for audio conversion and thumbnail embedding)

#### Install ffmpeg

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg

# macOS
brew install ffmpeg

# Windows — download from https://ffmpeg.org/download.html and add to PATH
```

### Install BlaXk Grabber

```bash
# Clone the repo
git clone https://github.com/yourusername/blaxk-grabber.git
cd blaxk-grabber

# Install (one time — no venv activation needed after this)
pip install -e .
```

### Add to PATH (if needed)

If you see `blaxk: command not found` after installing:

```bash
# Bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# Zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc

# Fish
fish_add_path ~/.local/bin
```

---

## 🎮 Usage

### Launch the GUI

```bash
blaxk
```

Or alternatively:

```bash
python -m youtube_media_grabber
```

### 🪄 First run — pick your own launch word

The first time you run BlaXk Grabber, it asks you to pick a **launch word** —
your own personal command for starting the app from any terminal:

```
Welcome to BlaXk Grabber! 🎉

Pick a launch word — the command you'll type in any terminal
to start BlaXk Grabber (e.g. 'grab', 'media').
```

Type something like `grab` or `media`, confirm, and from then on that word
launches the app from anywhere (a wrapper is installed in `~/.local/bin`).

- **Skip it** (close the dialog or leave it blank) → the app still works via
  `blaxk` or `python -m youtube_media_grabber`; you won't be asked again.
- **Change your word later** → run `python main.py --setup` (or
  `blaxk --setup`) to pick a new one; the old wrapper is removed automatically.
- Rules: 2–20 characters, lowercase letters, numbers and dashes; system
  commands like `ls`, `python` or `git` are rejected for safety.

Your choice is stored in `~/.config/blaxk-grabber/launch_word`. Delete that
file to get the first-run question again.

### What you can paste

| Input | What happens |
|---|---|
| `https://youtube.com/watch?v=...` | Downloads directly |
| `https://youtube.com/playlist?list=...` | Extracts all videos → concurrent download |
| `https://open.spotify.com/track/...` | Extracts title + artist → searches YouTube → downloads |
| `https://audiomack.com/artist/song` | Scrapes metadata → searches YouTube → downloads |
| `Kendrick Lamar humble` | Searches YouTube → downloads top result |

### Output Structure

```
~/Downloads/BlaXk_Grabber/
├── audio/
│   ├── Song Name.mp3
│   ├── Another Track.mp3
│   └── ...
└── video/
    ├── Music Video.mp4
    └── ...
```

---

## 🏷️ Metadata Pipeline

BlaXk Grabber pulls metadata from multiple sources and merges them. The first non-empty value wins:

```
Input
  │
  ├── Spotify URL ──→ oEmbed API ──→ title, artist
  ├── Audiomack URL ─→ og:title scrape ──→ title, artist
  ├── YouTube URL ──→ yt-dlp extract_info ──→ title, artist, album, date, genre
  └── Search query ─→ yt-dlp search ──→ same as YouTube
  │
  ▼
MusicBrainz API (free, no key needed)
  └──→ album, release_date, genre, tags
  │
  ▼
Merged Metadata ──→ ID3 tags embedded into MP3
  ├── title
  ├── artist
  ├── album
  ├── albumartist
  ├── genre
  ├── date (year)
  └── album art (thumbnail)
```

---

## ⚙️ Configuration

All configuration is done through the GUI:

| Setting | Default | Range |
|---|---|---|
| Format | MP3 Audio | MP3 / MP4 |
| Output folder | `~/Downloads/BlaXk_Grabber` | Any directory |
| Concurrent downloads | 4 | 1 – 8 |

---

## 🔄 How Retry Works

```
Batch download starts
  │
  ├── ✅ Successful downloads → Done ✓
  ├── ⏭ Duplicates → Exists ✓ (skipped)
  └── ❌ Failed downloads → collected
          │
          ▼
     Wait 2 seconds
          │
     Retry round 1 (up to 2 rounds)
          │
          ├── ✅ Now succeeded → Done ✓
          └── ❌ Still failing
                  │
             Retry round 2
                  │
                  ├── ✅ Recovered → Done ✓
                  └── ❌ Permanently failed → listed in log
```

---

## 📦 Project Structure

```
blaxk-grabber/
├── pyproject.toml                    # Package config + CLI entry point
├── main.py                           # Alternative entry point
├── README.md
│
└── youtube_media_grabber/
    ├── __init__.py                   # Public API exports
    ├── __main__.py                   # python -m entry point
    ├── gui.py                        # CustomTkinter glassmorphic GUI
    ├── downloader.py                 # yt-dlp download + ID3 tagging
    ├── meta.py                       # Metadata extraction + MusicBrainz
    └── searcher.py                   # YouTube search + playlist extraction
```

---

## 🛠️ Dependencies

| Package | Purpose |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube downloading & searching |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | Modern dark GUI |
| [mutagen](https://github.com/quodlibet/mutagen) | MP3 ID3 tag writing |
| [Pillow](https://python-pillow.org/) | Image handling for customtkinter |
| [requests](https://requests.readthedocs.io/) | HTTP calls (Spotify oEmbed, MusicBrainz) |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML scraping for metadata |
| [rich](https://github.com/Textualize/rich) | *(included but unused in GUI mode)* |
| **ffmpeg** (external) | Audio extraction, video merging, thumbnails |

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch (`git checkout -b feature/something`)
3. Commit your changes (`git commit -m 'Add something'`)
4. Push (`git push origin feature/something`)
5. Open a Pull Request

---

## 📄 License

MIT License — do whatever you want with it.

---

<div align="center">

**Built with Love for OPEN SOURCE by BlaXk**

*If it plays, we grab it.*

</div>
```
