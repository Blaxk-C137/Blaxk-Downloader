import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .meta import extract_metadata, build_search_query, is_youtube_url, Metadata
from .searcher import search_youtube, extract_playlist_urls
from .downloader import download_single, find_ffmpeg, resolve_base_output_dir

# ──────────────────────────────────────────────────────────────
# Theme
# ──────────────────────────────────────────────────────────────
BG_DARK = "#0a0a0a"
BG_CARD = "#1a1a1a"
BG_CARD_HOVER = "#222222"
BG_INPUT = "#141414"
RED = "#e63946"
RED_DARK = "#991f2b"
RED_GLOW = "#ff2d3b"
WHITE = "#f1f1f1"
GRAY = "#888888"
GREEN = "#2ecc71"
YELLOW = "#f1c40f"
FONT_FAMILY = "Segoe UI"

MAX_CONCURRENT = 4


class GlassCard(ctk.CTkFrame):
    """A semi-transparent card with rounded corners — glass morph effect."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=BG_CARD,
            corner_radius=16,
            border_width=1,
            border_color="#2a2a2a",
            **kwargs,
        )


class DownloadRow(ctk.CTkFrame):
    """A single row in the download queue showing title + progress."""

    def __init__(self, master, title: str, index: int, **kwargs):
        super().__init__(master, fg_color="transparent", height=48, **kwargs)
        self.grid_columnconfigure(1, weight=1)

        self.index_label = ctk.CTkLabel(
            self,
            text=f"#{index}",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=RED,
            width=36,
        )
        self.index_label.grid(row=0, column=0, padx=(8, 4), pady=4)

        display_title = title if len(title) <= 55 else title[:52] + "..."
        self.title_label = ctk.CTkLabel(
            self,
            text=display_title,
            font=(FONT_FAMILY, 12),
            text_color=WHITE,
            anchor="w",
        )
        self.title_label.grid(row=0, column=1, padx=4, pady=4, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(
            self,
            width=140,
            height=10,
            corner_radius=5,
            fg_color="#2a2a2a",
            progress_color=RED,
            border_width=0,
        )
        self.progress_bar.grid(row=0, column=2, padx=8, pady=4)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self,
            text="Queued",
            font=(FONT_FAMILY, 10),
            text_color=GRAY,
            width=80,
        )
        self.status_label.grid(row=0, column=3, padx=(4, 12), pady=4)

    def update_progress(self, fraction: float, status_text: str = "", color: str = ""):
        self.progress_bar.set(min(fraction, 1.0))
        if status_text:
            self.status_label.configure(text=status_text)
        if color:
            self.status_label.configure(text_color=color)
            self.progress_bar.configure(progress_color=color)


class BlaXkGrabber(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("BlaXk Grabber")
        self.geometry("900x720")
        self.minsize(780, 620)
        self.configure(fg_color=BG_DARK)

        self.output_dir = resolve_base_output_dir(Path.home() / "Downloads" / "BlaXk_Grabber")
        self.ffmpeg_path = find_ffmpeg()
        self.download_rows: list[DownloadRow] = []
        self.is_downloading = False

        self._build_ui()

    # ──────────────────────────────────────────────────────────
    # UI Construction
    # ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(24, 0))

        logo_label = ctk.CTkLabel(
            header_frame,
            text="BlaXk",
            font=(FONT_FAMILY, 42, "bold"),
            text_color=RED_GLOW,
        )
        logo_label.pack(side="left")

        grabber_label = ctk.CTkLabel(
            header_frame,
            text=" Grabber",
            font=(FONT_FAMILY, 42),
            text_color=WHITE,
        )
        grabber_label.pack(side="left")

        version_label = ctk.CTkLabel(
            header_frame,
            text="v2.0",
            font=(FONT_FAMILY, 12),
            text_color=GRAY,
        )
        version_label.pack(side="left", padx=(12, 0), pady=(20, 0))

        subtitle = ctk.CTkLabel(
            self,
            text="YouTube • Spotify • Audiomack → MP3 / MP4",
            font=(FONT_FAMILY, 13),
            text_color=GRAY,
        )
        subtitle.pack(anchor="w", padx=34, pady=(2, 16))

        # ── Input Card ──
        input_card = GlassCard(self)
        input_card.pack(fill="x", padx=28, pady=(0, 12))
        input_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            input_card,
            text="URL or search query",
            font=(FONT_FAMILY, 11),
            text_color=GRAY,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 0))

        self.input_entry = ctk.CTkEntry(
            input_card,
            placeholder_text="Paste YouTube / Spotify / Audiomack link, or type a search...",
            font=(FONT_FAMILY, 13),
            height=44,
            corner_radius=10,
            fg_color=BG_INPUT,
            border_color="#333333",
            border_width=1,
            text_color=WHITE,
        )
        self.input_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(6, 16))

        # ── Options Card ──
        options_card = GlassCard(self)
        options_card.pack(fill="x", padx=28, pady=(0, 12))
        options_card.grid_columnconfigure(1, weight=1)

        # Format toggle
        ctk.CTkLabel(
            options_card,
            text="Format",
            font=(FONT_FAMILY, 11),
            text_color=GRAY,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 0))

        self.format_var = ctk.StringVar(value="audio")
        format_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        format_frame.grid(row=1, column=0, sticky="w", padx=20, pady=(6, 16))

        self.audio_btn = ctk.CTkButton(
            format_frame,
            text="🎵  MP3 Audio",
            font=(FONT_FAMILY, 12, "bold"),
            width=150,
            height=38,
            corner_radius=10,
            fg_color=RED,
            hover_color=RED_DARK,
            command=lambda: self._set_format("audio"),
        )
        self.audio_btn.pack(side="left", padx=(0, 8))

        self.video_btn = ctk.CTkButton(
            format_frame,
            text="🎬  MP4 Video",
            font=(FONT_FAMILY, 12, "bold"),
            width=150,
            height=38,
            corner_radius=10,
            fg_color="#333333",
            hover_color="#444444",
            command=lambda: self._set_format("video"),
        )
        self.video_btn.pack(side="left")

        # Output directory
        ctk.CTkLabel(
            options_card,
            text="Download folder",
            font=(FONT_FAMILY, 11),
            text_color=GRAY,
        ).grid(row=0, column=1, sticky="w", padx=20, pady=(16, 0))

        dir_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        dir_frame.grid(row=1, column=1, sticky="ew", padx=20, pady=(6, 16))
        dir_frame.grid_columnconfigure(0, weight=1)

        self.output_entry = ctk.CTkEntry(
            dir_frame,
            font=(FONT_FAMILY, 11),
            height=38,
            corner_radius=10,
            fg_color=BG_INPUT,
            border_color="#333333",
            border_width=1,
            text_color=WHITE,
        )
        self.output_entry.insert(0, str(self.output_dir))
        self.output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            dir_frame,
            text="📁",
            font=(FONT_FAMILY, 16),
            width=42,
            height=38,
            corner_radius=10,
            fg_color="#333333",
            hover_color="#444444",
            command=self._choose_output_dir,
        ).grid(row=0, column=1)

        # Concurrent count slider
        ctk.CTkLabel(
            options_card,
            text="Concurrent downloads",
            font=(FONT_FAMILY, 11),
            text_color=GRAY,
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(0, 0))

        slider_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        slider_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=20, pady=(4, 16))

        self.concurrent_var = ctk.IntVar(value=MAX_CONCURRENT)
        self.concurrent_label = ctk.CTkLabel(
            slider_frame,
            text=f"{MAX_CONCURRENT}",
            font=(FONT_FAMILY, 13, "bold"),
            text_color=RED,
            width=30,
        )
        self.concurrent_label.pack(side="right", padx=(8, 0))

        self.concurrent_slider = ctk.CTkSlider(
            slider_frame,
            from_=1,
            to=8,
            number_of_steps=7,
            variable=self.concurrent_var,
            width=200,
            height=18,
            fg_color="#2a2a2a",
            progress_color=RED,
            button_color=RED,
            button_hover_color=RED_GLOW,
            command=self._on_slider_change,
        )
        self.concurrent_slider.pack(side="left")

        # ── Big Download Button ──
        self.download_btn = ctk.CTkButton(
            self,
            text="⬇  GRAB IT",
            font=(FONT_FAMILY, 18, "bold"),
            height=54,
            corner_radius=14,
            fg_color=RED,
            hover_color=RED_DARK,
            command=self._on_download,
        )
        self.download_btn.pack(fill="x", padx=28, pady=(4, 12))

        # ── Status Bar ──
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=(FONT_FAMILY, 11),
            text_color=GRAY,
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=34, pady=(0, 4))

        # ── Queue Card (scrollable) ──
        queue_card = GlassCard(self)
        queue_card.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        ctk.CTkLabel(
            queue_card,
            text="Download Queue",
            font=(FONT_FAMILY, 13, "bold"),
            text_color=WHITE,
        ).pack(anchor="w", padx=20, pady=(14, 4))

        self.queue_scroll = ctk.CTkScrollableFrame(
            queue_card,
            fg_color="transparent",
            corner_radius=0,
        )
        self.queue_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        self.empty_label = ctk.CTkLabel(
            self.queue_scroll,
            text="No downloads yet. Paste a link and hit GRAB IT.",
            font=(FONT_FAMILY, 12),
            text_color="#555555",
        )
        self.empty_label.pack(pady=40)

        # ── Log Card ──
        log_card = GlassCard(self)
        log_card.pack(fill="x", padx=28, pady=(0, 20))

        ctk.CTkLabel(
            log_card,
            text="Log",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=GRAY,
        ).pack(anchor="w", padx=20, pady=(12, 0))

        self.log_box = ctk.CTkTextbox(
            log_card,
            font=(FONT_FAMILY, 10),
            height=90,
            fg_color=BG_INPUT,
            text_color="#cccccc",
            corner_radius=8,
            border_width=0,
            state="disabled",
            wrap="word",
        )
        self.log_box.pack(fill="x", padx=16, pady=(6, 14))

        # Warnings
        if not self.ffmpeg_path:
            self._log("⚠ ffmpeg not found on PATH — some conversions may fail.", YELLOW)

    # ──────────────────────────────────────────────────────────
    # UI Helpers
    # ──────────────────────────────────────────────────────────

    def _set_format(self, choice: str) -> None:
        self.format_var.set(choice)
        if choice == "audio":
            self.audio_btn.configure(fg_color=RED, hover_color=RED_DARK)
            self.video_btn.configure(fg_color="#333333", hover_color="#444444")
        else:
            self.video_btn.configure(fg_color=RED, hover_color=RED_DARK)
            self.audio_btn.configure(fg_color="#333333", hover_color="#444444")

    def _on_slider_change(self, value: float) -> None:
        v = int(value)
        self.concurrent_var.set(v)
        self.concurrent_label.configure(text=str(v))

    def _choose_output_dir(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.output_entry.get() or str(Path.home()))
        if directory:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, directory)

    def _log(self, message: str, color: str = WHITE) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def _clear_queue_ui(self) -> None:
        for row in self.download_rows:
            row.destroy()
        self.download_rows.clear()
        if hasattr(self, "empty_label") and self.empty_label.winfo_exists():
            self.empty_label.destroy()

    def _add_queue_row(self, title: str, index: int) -> DownloadRow:
        row = DownloadRow(self.queue_scroll, title=title, index=index)
        row.pack(fill="x", pady=2)
        self.download_rows.append(row)
        return row

    # ──────────────────────────────────────────────────────────
    # Download Logic
    # ──────────────────────────────────────────────────────────

    def _on_download(self) -> None:
        source = self.input_entry.get().strip()
        if not source:
            messagebox.showwarning("BlaXk Grabber", "Please enter a URL or search query.")
            return
        if self.is_downloading:
            messagebox.showinfo("BlaXk Grabber", "A download is already in progress.")
            return

        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="⏳  Grabbing...")
        self._clear_queue_ui()

        threading.Thread(target=self._resolve_and_download, args=(source,), daemon=True).start()

    def _resolve_and_download(self, source: str) -> None:
        try:
            metadata = extract_metadata(source)
            fmt = self.format_var.get()
            out_dir = self.output_entry.get().strip()
            max_workers = self.concurrent_var.get()

            # Determine the YouTube URL(s)
            if is_youtube_url(source):
                # Check if it's a playlist
                if "list=" in source.lower():
                    self.after(0, self._log, "🔍 Extracting playlist...", GRAY)
                    self.after(0, self._set_status, "Extracting playlist...")
                    entries = extract_playlist_urls(source)
                    if not entries:
                        raise ValueError("Could not extract any videos from this playlist.")
                    self.after(0, self._log, f"📋 Found {len(entries)} videos in playlist", GREEN)
                    self._download_batch(entries, fmt, out_dir, metadata, max_workers)
                    return
                else:
                    entries = [{"title": metadata.title or source, "link": source}]
            else:
                query = build_search_query(metadata)
                if not query:
                    raise ValueError("Unable to build a search query from the provided input.")
                self.after(0, self._log, f"🔍 Searching: {query}", GRAY)
                self.after(0, self._set_status, "Searching YouTube...")
                video = search_youtube(query)
                self.after(0, self._log, f"✅ Found: {video['title']}", GREEN)
                entries = [video]

            self._download_batch(entries, fmt, out_dir, metadata, max_workers)

        except Exception as exc:
            self.after(0, self._log, f"❌ Error: {exc}", RED)
            self.after(0, self._set_status, "Error")
            self.after(0, messagebox.showerror, "BlaXk Grabber", str(exc))
        finally:
            self.after(0, self._finish_download)

    def _download_batch(
        self,
        entries: list[dict],
        fmt: str,
        out_dir: str,
        base_metadata: Metadata,
        max_workers: int,
    ) -> None:
        # Create queue rows on the UI thread
        rows: list[DownloadRow] = []
        for i, entry in enumerate(entries, 1):
            row = self._safe_add_row(entry.get("title", "Unknown"), i)
            rows.append(row)

        total = len(entries)
        completed = 0
        failed = 0

        self.after(0, self._set_status, f"Downloading 0/{total}...")

        def do_download(index: int, entry: dict, row: DownloadRow) -> str:
            url = entry["link"]
            title = entry.get("title", "Unknown")
            self.after(0, row.update_progress, 0.0, "Downloading...", RED)
            self.after(0, self._log, f"⬇ Starting: {title}")

            def progress_hook(d: dict):
                if d.get("status") == "downloading":
                    total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded = d.get("downloaded_bytes") or 0
                    if total_bytes > 0:
                        fraction = downloaded / total_bytes
                        pct_text = f"{fraction * 100:.0f}%"
                        self.after(0, row.update_progress, fraction, pct_text, RED)
                elif d.get("status") == "finished":
                    self.after(0, row.update_progress, 1.0, "Finalizing...", YELLOW)

            try:
                download_single(
                    url=url,
                    format_choice=fmt,
                    base_output_dir=out_dir,
                    ffmpeg_path=self.ffmpeg_path,
                    metadata=base_metadata,
                    progress_callback=progress_hook,
                )
                self.after(0, row.update_progress, 1.0, "Done ✓", GREEN)
                self.after(0, self._log, f"✅ Finished: {title}", GREEN)
                return "ok"
            except Exception as e:
                self.after(0, row.update_progress, 0.0, "Failed ✗", RED)
                self.after(0, self._log, f"❌ Failed: {title} — {e}", RED)
                return "fail"

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, (entry, row) in enumerate(zip(entries, rows)):
                future = executor.submit(do_download, i, entry, row)
                futures[future] = entry

            for future in as_completed(futures):
                result = future.result()
                if result == "ok":
                    completed += 1
                else:
                    failed += 1
                self.after(
                    0,
                    self._set_status,
                    f"Downloaded {completed}/{total} — {failed} failed" if failed else f"Downloaded {completed}/{total}",
                )

        # Summary
        summary = f"🎉 All done! {completed}/{total} succeeded"
        if failed:
            summary += f", {failed} failed"
        self.after(0, self._log, summary, GREEN if not failed else YELLOW)
        self.after(0, self._set_status, summary)

    def _safe_add_row(self, title: str, index: int) -> DownloadRow:
        """Thread-safe row creation — blocks until the UI thread creates it."""
        import queue as q

        result_q = q.Queue()

        def create():
            row = self._add_queue_row(title, index)
            result_q.put(row)

        self.after(0, create)
        return result_q.get()

    def _finish_download(self) -> None:
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="⬇  GRAB IT")


def main() -> None:
    app = BlaXkGrabber()
    app.mainloop()