import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .meta import extract_metadata, build_search_query, is_youtube_url
from .searcher import search_youtube
from .downloader import download_youtube, find_ffmpeg, resolve_base_output_dir, get_expected_output_path


class BLAXKDownloader(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BLAXK DOWNLOADER")
        self.configure(bg="#111111")
        self.geometry("760x560")
        self.resizable(False, False)

        self.output_dir = resolve_base_output_dir(Path.home() / "Downloads" / "BLAXK_DOWNLOADER")
        self.ffmpeg_path = find_ffmpeg()

        self.input_var = tk.StringVar()
        self.format_var = tk.StringVar(value="audio")
        self.output_var = tk.StringVar(value=str(self.output_dir))
        self.status_var = tk.StringVar(value="Ready")

        self._create_style()
        self._build_ui()

        if not self.ffmpeg_path:
            self._append_log("⚠️ ffmpeg was not found on PATH. Downloads may still work if ffmpeg is installed manually.", "red")

    def _create_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("BW.TLabel", background="#111111", foreground="#ff3b3f", font=("Segoe UI", 11))
        style.configure("BW.TEntry", fieldbackground="#222222", background="#222222", foreground="#ffffff", borderwidth=0)
        style.configure("BW.TButton", background="#111111", foreground="#ffffff", borderwidth=1, focusthickness=3, focuscolor="#ff3b3f")
        style.map(
            "BW.TButton",
            background=[("active", "#330000")],
            foreground=[("active", "#ff3b3f")],
        )
        style.configure("BW.TRadiobutton", background="#111111", foreground="#ff3b3f", font=("Segoe UI", 10))
        style.configure("BW.Horizontal.TSeparator", background="#440000")

    def _build_ui(self) -> None:
        header = tk.Label(
            self,
            text="BLAXK DOWNLOADER",
            font=("Segoe UI Black", 28, "bold"),
            fg="#ff3b3f",
            bg="#111111",
        )
        header.pack(pady=(18, 4))

        subtitle = tk.Label(
            self,
            text="YouTube downloader with Spotify/Audiomack lookup.",
            font=("Segoe UI", 11),
            fg="#dddddd",
            bg="#111111",
        )
        subtitle.pack(pady=(0, 16))

        frame = tk.Frame(self, bg="#111111")
        frame.pack(fill="x", padx=18)

        ttk.Label(frame, text="Enter URL or query:", style="BW.TLabel").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(frame, textvariable=self.input_var, style="BW.TEntry", font=("Segoe UI", 11))
        entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 12))
        frame.columnconfigure(0, weight=1)

        radio_frame = tk.Frame(frame, bg="#111111")
        radio_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 12))
        ttk.Radiobutton(radio_frame, text="Audio", value="audio", variable=self.format_var, style="BW.TRadiobutton").pack(side="left", padx=(0, 16))
        ttk.Radiobutton(radio_frame, text="Video", value="video", variable=self.format_var, style="BW.TRadiobutton").pack(side="left")

        ttk.Label(frame, text="Download folder:", style="BW.TLabel").grid(row=3, column=0, sticky="w")
        output_entry = ttk.Entry(frame, textvariable=self.output_var, style="BW.TEntry", font=("Segoe UI", 10))
        output_entry.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        browse_button = ttk.Button(frame, text="Browse", style="BW.TButton", command=self._choose_output_dir)
        browse_button.grid(row=4, column=1, padx=(10, 0), sticky="e")

        button_frame = tk.Frame(self, bg="#111111")
        button_frame.pack(fill="x", padx=18, pady=(14, 0))
        download_button = ttk.Button(button_frame, text="DOWNLOAD", style="BW.TButton", command=self._on_download)
        download_button.pack(side="left", ipady=8, ipadx=18)
        self.status_label = ttk.Label(button_frame, textvariable=self.status_var, style="BW.TLabel")
        self.status_label.pack(side="right")

        separator = ttk.Separator(self, orient="horizontal", style="BW.Horizontal.TSeparator")
        separator.pack(fill="x", padx=18, pady=(18, 18))

        log_frame = tk.Frame(self, bg="#111111")
        log_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.log_text = tk.Text(
            log_frame,
            bg="#111111",
            fg="#ffffff",
            insertbackground="#ffffff",
            wrap="word",
            bd=0,
            relief="flat",
            font=("Segoe UI", 10),
            height=14,
        )
        self.log_text.pack(fill="both", side="left", expand=True)
        self.log_text.tag_config("red", foreground="#ff3b3f")
        self.log_text.tag_config("white", foreground="#ffffff")
        self.log_text.tag_config("green", foreground="#2ecc71")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self._append_log("Ready to download. Paste a YouTube link or search query and press DOWNLOAD.", "green")

        self.download_button = download_button

    def _choose_output_dir(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.home()))
        if directory:
            self.output_var.set(directory)

    def _append_log(self, message: str, tag: str = "white") -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_controls(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.download_button.configure(state=state)

    def _confirm_overwrite(self, filepath: Path) -> bool:
        result_queue = queue.Queue()

        def ask():
            result_queue.put(
                messagebox.askyesno(
                    "BLAXK DOWNLOADER",
                    f"The file already exists:\n{filepath}\n\nDo you want to overwrite it?",
                )
            )

        self.after(0, ask)
        return result_queue.get()

    def _on_download(self) -> None:
        source = self.input_var.get().strip()
        if not source:
            messagebox.showwarning("BLAXK DOWNLOADER", "Please enter a YouTube URL, Spotify/Audiomack link, or search query.")
            return

        self._set_controls(False)
        self.status_var.set("Preparing download...")
        threading.Thread(target=self._download_thread, args=(source,), daemon=True).start()

    def _download_thread(self, source: str) -> None:
        try:
            metadata = extract_metadata(source)
            if is_youtube_url(source):
                target_url = source
            else:
                query = build_search_query(metadata)
                if not query:
                    raise ValueError("Unable to build a search query from the provided input.")
                self.after(0, self._append_log, f"Searching YouTube for: {query}", "white")
                video = search_youtube(query)
                target_url = video["link"]
                self.after(0, self._append_log, f"Found: {video['title']}", "green")

            expected_path = get_expected_output_path(
                target_url,
                self.format_var.get(),
                base_output_dir=self.output_var.get(),
                ffmpeg_path=self.ffmpeg_path,
            )
            if expected_path.exists():
                overwrite = self._confirm_overwrite(expected_path)
                if not overwrite:
                    self.after(0, self._append_log, f"Skipping download; file already exists: {expected_path}", "red")
                    self.after(0, self.status_var.set, "Skipped")
                    return

            self.after(0, self._append_log, f"Starting download ({self.format_var.get()})...", "white")
            download_youtube(
                target_url,
                self.format_var.get(),
                base_output_dir=self.output_var.get(),
                ffmpeg_path=self.ffmpeg_path,
                metadata=metadata,
                allow_playlist=("list=" in target_url.lower() and "youtube" in target_url.lower()),
                progress_callback=lambda status: self.after(0, self._log_progress, status),
            )
            self.after(0, self._append_log, "Download complete.", "green")
            self.after(0, self.status_var.set, "Completed")
            self.after(0, messagebox.showinfo, "BLAXK DOWNLOADER", "Download finished successfully.")
        except Exception as exc:
            self.after(0, self._append_log, f"Error: {exc}", "red")
            self.after(0, self.status_var.set, "Error")
            self.after(0, messagebox.showerror, "BLAXK DOWNLOADER", str(exc))
        finally:
            self.after(0, self._set_controls, True)

    def _log_progress(self, status: dict) -> None:
        state = status.get("status")
        if state == "downloading":
            total = status.get("total_bytes") or status.get("total_bytes_estimate") or 0
            downloaded = status.get("downloaded_bytes") or 0
            if total:
                percent = downloaded / total * 100
                self.status_var.set(f"Downloading {percent:.1f}%")
            else:
                self.status_var.set("Downloading...")
        elif state == "finished":
            self.status_var.set("Finalizing file...")
        elif state == "error":
            self.status_var.set("Failed")


def main() -> None:
    app = BLAXKDownloader()
    app.mainloop()
