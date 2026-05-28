"""
GUI Application for Speech-to-Text
Modern, aesthetic interface built with customtkinter
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import sounddevice as sd
import threading
from pathlib import Path
from datetime import datetime
import config
from audio_handler import AudioHandler
from stt_engine import STTEngine

# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode(config.THEME)
ctk.set_default_color_theme("blue")

# ── Colour palette ────────────────────────────────────────────────────────────
ACCENT = "#4a9eff"
RECORD_IDLE = "#c0392b"
RECORD_ACTIVE = "#7d6608"
SUCCESS = "#2ecc71"
WARNING = "#f39c12"
ERROR = "#e74c3c"


# ── Reusable widgets ──────────────────────────────────────────────────────────

class HistoryItem(ctk.CTkFrame):
    """A clickable transcription-history card shown in the sidebar."""

    def __init__(self, master, text: str, language: str, timestamp: str,
                 on_select, **kwargs):
        kwargs.setdefault("corner_radius", 6)
        super().__init__(master, **kwargs)
        self.text_content = text
        self.configure(cursor="hand2")

        ctk.CTkLabel(
            self, text=timestamp,
            font=ctk.CTkFont(size=10), text_color="gray60",
        ).pack(anchor="w", padx=8, pady=(6, 0))

        ctk.CTkLabel(
            self, text=f"🌐 {language}",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT,
        ).pack(anchor="w", padx=8)

        preview = (text[:75] + "…") if len(text) > 75 else text
        ctk.CTkLabel(
            self, text=preview,
            font=ctk.CTkFont(size=11), wraplength=200, justify="left",
        ).pack(anchor="w", padx=8, pady=(2, 6))

        for child in self.winfo_children():
            child.bind("<Button-1>", lambda _e: on_select(text))
        self.bind("<Button-1>", lambda _e: on_select(text))
        self.bind("<Enter>", lambda _e: self.configure(
            fg_color=("gray75", "gray25")))
        self.bind("<Leave>", lambda _e: self.configure(
            fg_color=("gray85", "gray20")))


# ── Main application ──────────────────────────────────────────────────────────

class STTApp(ctk.CTk):
    """Modern Speech-to-Text desktop application."""

    # ── Initialisation ────────────────────────────────────────────────────────

    def __init__(self):
        super().__init__()
        self.title(config.WINDOW_TITLE)
        self.geometry(config.WINDOW_SIZE)
        self.minsize(820, 520)

        self.audio_handler = AudioHandler(
            sample_rate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
        )
        self.stt_engine = STTEngine()

        self.is_recording = False
        self.current_audio = None
        self.current_result = None
        self._timer_running = False
        self._timer_seconds = 0

        self._build_layout()
        self.set_status("Ready — load a model to begin.", "gray")

    # ── Layout builders ───────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._build_statusbar()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(10, weight=1)

        # App branding
        ctk.CTkLabel(
            sidebar, text="🎙 STT Studio",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(22, 2))
        ctk.CTkLabel(
            sidebar, text="Speech · to · Text",
            font=ctk.CTkFont(size=11), text_color="gray60",
        ).grid(row=1, column=0, padx=20, pady=(0, 16))

        ctk.CTkFrame(sidebar, height=1, fg_color="gray35").grid(
            row=2, column=0, sticky="ew", padx=14, pady=4)

        # Settings label
        ctk.CTkLabel(
            sidebar, text="SETTINGS",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="gray55",
        ).grid(row=3, column=0, padx=20, pady=(10, 4), sticky="w")

        # Settings grid
        sf = ctk.CTkFrame(sidebar, fg_color="transparent")
        sf.grid(row=4, column=0, padx=14, pady=2, sticky="ew")
        sf.grid_columnconfigure(1, weight=1)

        def _row(parent, label, row, widget_factory):
            ctk.CTkLabel(
                parent, text=label, font=ctk.CTkFont(size=12),
            ).grid(row=row, column=0, padx=6, pady=5, sticky="w")
            w = widget_factory(parent)
            w.grid(row=row, column=1, padx=6, pady=5, sticky="e")
            return w

        self.model_var = ctk.StringVar(value=config.DEFAULT_MODEL)
        _row(sf, "Model", 0, lambda p: ctk.CTkOptionMenu(
            p, variable=self.model_var,
            values=["tiny", "base", "small", "medium", "large"], width=115))

        self.language_var = ctk.StringVar(value="Auto")
        _row(sf, "Language", 1, lambda p: ctk.CTkOptionMenu(
            p, variable=self.language_var,
            values=["Auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh"],
            width=115))

        self.duration_var = ctk.StringVar(value=str(config.DEFAULT_DURATION))
        _row(sf, "Duration (s)", 2, lambda p: ctk.CTkEntry(
            p, textvariable=self.duration_var, width=70,
            placeholder_text="10"))

        self.task_var = ctk.StringVar(value=config.TASK)
        _row(sf, "Task", 3, lambda p: ctk.CTkOptionMenu(
            p, variable=self.task_var,
            values=["transcribe", "translate"], width=115))

        # Load model button
        self.load_btn = ctk.CTkButton(
            sidebar, text="⚡  Load Model",
            command=self.load_model_thread,
            height=38, corner_radius=8,
            fg_color="#1a5276", hover_color="#2471a3",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.load_btn.grid(row=5, column=0, padx=14, pady=12, sticky="ew")

        ctk.CTkFrame(sidebar, height=1, fg_color="gray35").grid(
            row=6, column=0, sticky="ew", padx=14, pady=4)

        # Theme toggle
        tf = ctk.CTkFrame(sidebar, fg_color="transparent")
        tf.grid(row=7, column=0, padx=14, pady=6, sticky="ew")
        tf.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tf, text="Dark Mode",
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=6, sticky="w")
        self.theme_switch = ctk.CTkSwitch(
            tf, text="", command=self._toggle_theme,
            onvalue="dark", offvalue="light",
        )
        self.theme_switch.select()
        self.theme_switch.grid(row=0, column=1, padx=6, sticky="e")

        ctk.CTkFrame(sidebar, height=1, fg_color="gray35").grid(
            row=8, column=0, sticky="ew", padx=14, pady=4)

        # History
        ctk.CTkLabel(
            sidebar, text="SESSION HISTORY",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="gray55",
        ).grid(row=9, column=0, padx=20, pady=(10, 4), sticky="w")

        self.history_frame = ctk.CTkScrollableFrame(
            sidebar, fg_color="transparent", label_text="")
        self.history_frame.grid(row=10, column=0, padx=6, pady=(0, 6),
                                sticky="nsew")

        ctk.CTkLabel(
            sidebar, text="v2.0  •  OpenAI Whisper",
            font=ctk.CTkFont(size=9), text_color="gray45",
        ).grid(row=11, column=0, padx=20, pady=(4, 10))

    # ── Main content area ─────────────────────────────────────────────────────

    def _build_main(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # ── Action bar ────────────────────────────────────────────────────────
        abar = ctk.CTkFrame(main, fg_color="transparent")
        abar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        abar.grid_columnconfigure(3, weight=1)

        self.record_btn = ctk.CTkButton(
            abar, text="🎤  Start Recording",
            command=self.toggle_recording, state="disabled",
            width=175, height=44, corner_radius=10,
            fg_color=RECORD_IDLE, hover_color="#922b21",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.record_btn.grid(row=0, column=0, padx=(0, 8))

        self.file_btn = ctk.CTkButton(
            abar, text="📁  Open File",
            command=self.transcribe_file, state="disabled",
            width=145, height=44, corner_radius=10,
            fg_color="#1e8449", hover_color="#27ae60",
            font=ctk.CTkFont(size=14),
        )
        self.file_btn.grid(row=0, column=1, padx=8)

        # Recording timer
        self.timer_label = ctk.CTkLabel(
            abar, text="",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=ERROR,
        )
        self.timer_label.grid(row=0, column=2, padx=8)

        # Progress bar (hidden until in use)
        self.progress = ctk.CTkProgressBar(abar, width=140, height=8)
        self.progress.set(0)
        self.progress.grid(row=0, column=3, padx=8, sticky="w")
        self.progress.grid_remove()

        # Right action buttons
        rbf = ctk.CTkFrame(abar, fg_color="transparent")
        rbf.grid(row=0, column=4, sticky="e")

        _btn_style = dict(
            height=38, corner_radius=8,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            font=ctk.CTkFont(size=12),
        )
        self.copy_btn = ctk.CTkButton(
            rbf, text="📋  Copy", command=self.copy_to_clipboard,
            state="disabled", width=95, **_btn_style)
        self.copy_btn.pack(side="left", padx=3)

        self.save_btn = ctk.CTkButton(
            rbf, text="💾  Save", command=self.save_transcription,
            state="disabled", width=95, **_btn_style)
        self.save_btn.pack(side="left", padx=3)

        ctk.CTkButton(
            rbf, text="🗑  Clear", command=self.clear_output,
            width=95, **_btn_style,
        ).pack(side="left", padx=3)

        # ── Tabbed output ─────────────────────────────────────────────────────
        self.tabs = ctk.CTkTabview(main, corner_radius=10)
        self.tabs.grid(row=1, column=0, sticky="nsew")
        self.tabs.add("Transcription")
        self.tabs.add("Segments")

        for tab_name, attr in (("Transcription", "output_text"),
                               ("Segments", "segments_text")):
            tab = self.tabs.tab(tab_name)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
            box = ctk.CTkTextbox(
                tab, font=ctk.CTkFont(size=13, family="Consolas"),
                wrap="word", corner_radius=6,
            )
            box.grid(row=0, column=0, sticky="nsew")
            setattr(self, attr, box)

        # ── Stats bar ─────────────────────────────────────────────────────────
        sbar = ctk.CTkFrame(main, height=28, fg_color="transparent")
        sbar.grid(row=2, column=0, sticky="ew", pady=(4, 0))

        self.word_count_lbl = ctk.CTkLabel(
            sbar, text="Words: 0", font=ctk.CTkFont(size=11),
            text_color="gray60")
        self.word_count_lbl.pack(side="left")

        self.char_count_lbl = ctk.CTkLabel(
            sbar, text="  |  Chars: 0", font=ctk.CTkFont(size=11),
            text_color="gray60")
        self.char_count_lbl.pack(side="left")

        self.lang_lbl = ctk.CTkLabel(
            sbar, text="", font=ctk.CTkFont(size=11), text_color="gray60")
        self.lang_lbl.pack(side="right")

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=34, corner_radius=0)
        bar.grid(row=1, column=1, sticky="ew")
        bar.grid_propagate(False)

        self._status_dot = ctk.CTkLabel(
            bar, text="●", font=ctk.CTkFont(size=14), text_color="gray50")
        self._status_dot.pack(side="left", padx=(16, 5), pady=7)

        self._status_lbl = ctk.CTkLabel(
            bar, text="Initializing…", font=ctk.CTkFont(size=12))
        self._status_lbl.pack(side="left", pady=7)

    # ── Helpers ───────────────────────────────────────────────────────────────

    _COLOR_MAP = {
        "green":  (SUCCESS,  SUCCESS),
        "red":    (ERROR,    ERROR),
        "orange": (WARNING,  WARNING),
        "blue":   (ACCENT,   ACCENT),
        "gray":   ("gray60", "gray60"),
    }

    def set_status(self, text: str, color: str = "gray"):
        fg, dot = self._COLOR_MAP.get(color, self._COLOR_MAP["gray"])
        self._status_lbl.configure(text=text, text_color=fg)
        self._status_dot.configure(text_color=dot)

    def _toggle_theme(self):
        ctk.set_appearance_mode(self.theme_switch.get())

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _start_timer(self):
        self._timer_running = True
        self._timer_seconds = 0
        self._tick_timer()

    def _tick_timer(self):
        if self._timer_running:
            m, s = divmod(self._timer_seconds, 60)
            self.timer_label.configure(text=f"⏺  {m:02d}:{s:02d}")
            self._timer_seconds += 1
            self.after(1000, self._tick_timer)

    def _stop_timer(self):
        self._timer_running = False
        self.timer_label.configure(text="")

    # ── Model ─────────────────────────────────────────────────────────────────

    def load_model_thread(self):
        self.load_btn.configure(state="disabled", text="Loading…")
        self.set_status("Loading model, please wait…", "orange")

        def _load():
            try:
                self.stt_engine.model_name = self.model_var.get()
                self.stt_engine.load_model()
                self.after(0, self._on_model_loaded)
            except Exception as exc:
                self.after(0, lambda: self._on_model_error(str(exc)))

        threading.Thread(target=_load, daemon=True).start()

    def _on_model_loaded(self):
        self.load_btn.configure(state="normal", text="⚡  Load Model")
        self.record_btn.configure(state="normal")
        self.file_btn.configure(state="normal")
        self.set_status(
            f"Model '{self.model_var.get()}' loaded — ready!", "green")

    def _on_model_error(self, error: str):
        self.load_btn.configure(state="normal", text="⚡  Load Model")
        self.set_status(f"Model error: {error}", "red")
        messagebox.showerror(
            "Model Error", f"Failed to load model:\n{error}", parent=self)

    # ── Recording ─────────────────────────────────────────────────────────────

    def toggle_recording(self):
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording_early()

    def _start_recording(self):
        try:
            duration = int(self.duration_var.get())
            if duration <= 0:
                duration = config.DEFAULT_DURATION
        except ValueError:
            duration = config.DEFAULT_DURATION

        self.is_recording = True
        self.record_btn.configure(
            text="⏹  Stop Recording",
            fg_color=RECORD_ACTIVE, hover_color="#a04000")
        self.file_btn.configure(state="disabled")
        self.set_status(f"Recording for {duration}s — speak now!", "red")
        self._start_timer()

        def _record():
            try:
                audio = self.audio_handler.record_audio(duration=duration)
                self.current_audio = audio
                if config.SAVE_AUDIO:
                    self.audio_handler.save_audio(
                        audio, output_dir=config.RECORDINGS_DIR)
                self.after(0, self._on_recording_done)
            except Exception as exc:
                self.after(0, lambda: self._on_recording_error(str(exc)))

        threading.Thread(target=_record, daemon=True).start()

    def _stop_recording_early(self):
        """Request early stop (sd.stop() interrupts the sounddevice recording)."""
        sd.stop()
        self.set_status("Stopping recording…", "orange")

    def _on_recording_done(self):
        self.is_recording = False
        self._stop_timer()
        self.record_btn.configure(
            text="🎤  Start Recording",
            fg_color=RECORD_IDLE, hover_color="#922b21")
        self.file_btn.configure(state="normal")
        self.set_status("Recording done — transcribing…", "blue")
        self._transcribe_audio()

    def _on_recording_error(self, error: str):
        self.is_recording = False
        self._stop_timer()
        self.record_btn.configure(
            text="🎤  Start Recording",
            fg_color=RECORD_IDLE, hover_color="#922b21", state="normal")
        self.file_btn.configure(state="normal")
        self.set_status(f"Recording error: {error}", "red")

    # ── Transcription ─────────────────────────────────────────────────────────

    def _transcribe_audio(self):
        if self.current_audio is None:
            return
        language = (
            None if self.language_var.get() == "Auto"
            else self.language_var.get()
        )
        self._begin_progress()

        def _do():
            try:
                result = self.stt_engine.transcribe_audio_data(
                    self.current_audio,
                    sample_rate=config.SAMPLE_RATE,
                    language=language,
                    task=self.task_var.get(),
                )
                self.current_result = result
                self.after(0, lambda: self._display_result(result))
            except Exception as exc:
                self.after(0, lambda: self._on_transcribe_error(str(exc)))

        threading.Thread(target=_do, daemon=True).start()

    def transcribe_file(self):
        filepath = filedialog.askopenfilename(
            parent=self, title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                ("All Files", "*.*"),
            ],
        )
        if not filepath:
            return

        self.set_status(f"Transcribing: {Path(filepath).name}", "blue")
        self.record_btn.configure(state="disabled")
        self.file_btn.configure(state="disabled")
        self._begin_progress()

        language = (
            None if self.language_var.get() == "Auto"
            else self.language_var.get()
        )

        def _do():
            try:
                result = self.stt_engine.transcribe_file(
                    filepath, language=language, task=self.task_var.get())
                self.current_result = result
                self.after(0, lambda: self._display_result(result))
            except Exception as exc:
                self.after(0, lambda: self._on_transcribe_error(str(exc)))

        threading.Thread(target=_do, daemon=True).start()

    def _begin_progress(self):
        self.progress.grid()
        self.progress.configure(mode="indeterminate")
        self.progress.start()

    def _end_progress(self):
        self.progress.stop()
        self.progress.grid_remove()

    def _display_result(self, result: dict):
        self._end_progress()
        text = result["text"]
        language = result.get("language", "unknown")

        # Transcription tab
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", text)

        # Segments tab
        self.segments_text.delete("1.0", "end")
        if result["segments"]:
            for seg in result["segments"]:
                start = self._fmt_time(seg["start"])
                end = self._fmt_time(seg["end"])
                self.segments_text.insert(
                    "end", f"[{start} → {end}]\n{seg['text'].strip()}\n\n")
        else:
            self.segments_text.insert("end", "No segment data available.")

        # Stats
        words = len(text.split())
        self.word_count_lbl.configure(text=f"Words: {words}")
        self.char_count_lbl.configure(text=f"  |  Chars: {len(text)}")
        self.lang_lbl.configure(text=f"🌐 {language}")

        # Action buttons
        self.copy_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.record_btn.configure(state="normal")
        self.file_btn.configure(state="normal")

        self._add_to_history(text, language)
        self.set_status("Transcription complete!", "green")

    def _on_transcribe_error(self, error: str):
        self._end_progress()
        self.record_btn.configure(state="normal")
        self.file_btn.configure(state="normal")
        self.set_status(f"Transcription error: {error}", "red")
        messagebox.showerror(
            "Transcription Error",
            f"Failed to transcribe:\n{error}", parent=self)

    # ── History ───────────────────────────────────────────────────────────────

    def _add_to_history(self, text: str, language: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = HistoryItem(
            self.history_frame,
            text=text, language=language, timestamp=timestamp,
            on_select=self._load_history_item,
            fg_color=("gray85", "gray20"),
        )
        item.pack(fill="x", padx=2, pady=3)

    def _load_history_item(self, text: str):
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", text)
        self.tabs.set("Transcription")

    # ── Action handlers ───────────────────────────────────────────────────────

    def copy_to_clipboard(self):
        text = self.output_text.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.set_status("Copied to clipboard!", "green")

    def save_transcription(self):
        if self.current_result is None:
            messagebox.showwarning(
                "Nothing to Save", "No transcription to save.", parent=self)
            return

        filepath = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=(
                f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            ),
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write(f"Language: {self.current_result['language']}\n")
                fh.write(
                    f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                fh.write("=" * 60 + "\n\n")
                fh.write(self.current_result["text"] + "\n")
                if self.current_result["segments"]:
                    fh.write("\n" + "=" * 60 + "\n")
                    fh.write("Timestamped Segments:\n")
                    fh.write("=" * 60 + "\n\n")
                    for seg in self.current_result["segments"]:
                        start = self._fmt_time(seg["start"])
                        end = self._fmt_time(seg["end"])
                        fh.write(
                            f"[{start} → {end}] {seg['text'].strip()}\n")
            self.set_status(f"Saved to {Path(filepath).name}", "green")
        except Exception as exc:
            messagebox.showerror(
                "Save Error", f"Failed to save:\n{exc}", parent=self)

    def clear_output(self):
        self.output_text.delete("1.0", "end")
        self.segments_text.delete("1.0", "end")
        self.current_result = None
        self.word_count_lbl.configure(text="Words: 0")
        self.char_count_lbl.configure(text="  |  Chars: 0")
        self.lang_lbl.configure(text="")
        self.copy_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        self.set_status("Cleared.", "gray")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    """Main entry point for GUI application."""
    app = STTApp()
    app.mainloop()


if __name__ == "__main__":
    main()

