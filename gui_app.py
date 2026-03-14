"""
GUI Application for Speech-to-Text
Modern, aesthetic interface with extended features.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import threading
import time
import json
import random
from pathlib import Path
from datetime import datetime
import config
from audio_handler import AudioHandler
from stt_engine import STTEngine

# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode(config.THEME)
ctk.set_default_color_theme("blue")

# ── Colour palettes ───────────────────────────────────────────────────────────
DARK = {
    "bg":            "#0f172a",
    "surface":       "#1e293b",
    "surface2":      "#273549",
    "border":        "#334155",
    "primary":       "#6366f1",
    "primary_hover": "#4f46e5",
    "accent":        "#a78bfa",
    "success":       "#10b981",
    "error":         "#ef4444",
    "error2":        "#b91c1c",
    "warning":       "#f59e0b",
    "info":          "#38bdf8",
    "text":          "#f1f5f9",
    "text_dim":      "#94a3b8",
    "text_muted":    "#475569",
}

LIGHT = {
    "bg":            "#f8fafc",
    "surface":       "#ffffff",
    "surface2":      "#f1f5f9",
    "border":        "#e2e8f0",
    "primary":       "#6366f1",
    "primary_hover": "#4f46e5",
    "accent":        "#8b5cf6",
    "success":       "#059669",
    "error":         "#dc2626",
    "error2":        "#991b1b",
    "warning":       "#d97706",
    "info":          "#0284c7",
    "text":          "#0f172a",
    "text_dim":      "#475569",
    "text_muted":    "#94a3b8",
}


# ── Session history ───────────────────────────────────────────────────────────
class TranscriptionHistory:
    """Stores transcription results for the current session."""

    MAX_ITEMS = 50

    def __init__(self):
        self.items: list[dict] = []

    def add(self, result: dict, source: str = "microphone") -> dict:
        entry = {
            "id":         len(self.items) + 1,
            "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source":     source,
            "language":   result.get("language", "unknown"),
            "text":       result.get("text", ""),
            "segments":   result.get("segments", []),
            "word_count": len(result.get("text", "").split()),
            "char_count": len(result.get("text", "")),
        }
        self.items.insert(0, entry)
        if len(self.items) > self.MAX_ITEMS:
            self.items.pop()
        return entry

    def clear(self):
        self.items.clear()


# ── Main application window ───────────────────────────────────────────────────
class STTApp(ctk.CTk):
    """Modern Speech-to-Text desktop application."""

    # ── Initialisation ────────────────────────────────────────────────────────
    def __init__(self):
        super().__init__()
        self.title(config.WINDOW_TITLE)
        self.geometry("1150x740")
        self.minsize(900, 620)

        self.audio_handler = AudioHandler(
            sample_rate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
        )
        self.stt_engine  = STTEngine()
        self.history     = TranscriptionHistory()

        # State
        self.is_recording      = False
        self.is_loading_model  = False
        self.current_audio     = None
        self.current_result    = None
        self._is_dark          = True
        self._timer_job        = None
        self._pulse_job        = None
        self._pulse_on         = False
        self._level_job        = None
        self._record_start     = None

        self._build_ui()
        self._set_status("Ready — load a model to get started", "info")

    # ── Layout scaffolding ────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.configure(fg_color=DARK["bg"])

        self._build_sidebar()
        self._build_main_area()
        self._show_panel("transcribe")

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        P = DARK
        sb = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=P["surface"])
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(8, weight=1)
        sb.grid_columnconfigure(0, weight=1)
        self._sidebar = sb

        # Logo
        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.grid(row=0, column=0, padx=20, pady=(28, 16), sticky="ew")
        ctk.CTkLabel(logo, text="🎙", font=("Segoe UI", 36)).pack(side="left", padx=(0, 12))
        txt = ctk.CTkFrame(logo, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(
            txt, text="VoiceScribe",
            font=ctk.CTkFont("Segoe UI", 17, "bold"),
            text_color=P["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            txt, text="AI Transcription",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=P["text_dim"],
        ).pack(anchor="w")

        # Divider
        ctk.CTkFrame(sb, height=1, fg_color=P["border"]).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 10)
        )

        # Nav buttons
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("transcribe", "🎤   Transcribe", 2),
            ("history",    "📋   History",    3),
            ("settings",   "⚙️   Settings",   4),
        ]
        for key, label, row in nav_items:
            btn = ctk.CTkButton(
                sb, text=label, anchor="w", height=44,
                corner_radius=10,
                font=ctk.CTkFont("Segoe UI", 13),
                fg_color="transparent",
                hover_color=P["surface2"],
                text_color=P["text_dim"],
                command=lambda k=key: self._show_panel(k),
            )
            btn.grid(row=row, column=0, padx=14, pady=3, sticky="ew")
            self._nav_btns[key] = btn

        # Spacer
        ctk.CTkFrame(sb, fg_color="transparent").grid(row=8, column=0)

        # Divider
        ctk.CTkFrame(sb, height=1, fg_color=P["border"]).grid(
            row=9, column=0, sticky="ew", padx=16, pady=8
        )

        # Theme toggle
        thm = ctk.CTkFrame(sb, fg_color="transparent")
        thm.grid(row=10, column=0, padx=18, pady=(0, 14), sticky="ew")
        ctk.CTkLabel(
            thm, text="Dark Mode",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=P["text_dim"],
        ).pack(side="left")
        self._theme_sw = ctk.CTkSwitch(
            thm, text="", width=46,
            onvalue=True, offvalue=False,
            command=self._toggle_theme,
        )
        self._theme_sw.pack(side="right")
        self._theme_sw.select()

        # Version tag
        ctk.CTkLabel(
            sb, text="v2.0  ·  Whisper AI",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=P["text_muted"],
        ).grid(row=11, column=0, padx=18, pady=(0, 14))

    def _show_panel(self, name: str):
        P = DARK if self._is_dark else LIGHT
        for key, btn in self._nav_btns.items():
            if key == name:
                btn.configure(
                    fg_color=P["primary"],
                    text_color=P["text"],
                    hover_color=P["primary_hover"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=P["text_dim"],
                    hover_color=P["surface2"],
                )
        for panel_name, panel in self._panels.items():
            if panel_name == name:
                panel.grid()
            else:
                panel.grid_remove()
        if name == "history":
            self._refresh_history()

    # ── Main content area ─────────────────────────────────────────────────────
    def _build_main_area(self):
        P = DARK
        self._main = ctk.CTkFrame(self, corner_radius=0, fg_color=P["bg"])
        self._main.grid(row=0, column=1, sticky="nsew")
        self._main.grid_columnconfigure(0, weight=1)
        self._main.grid_rowconfigure(1, weight=1)

        self._build_statusbar()

        self._panels: dict[str, ctk.CTkFrame] = {
            "transcribe": self._build_transcribe_panel(),
            "history":    self._build_history_panel(),
            "settings":   self._build_settings_panel(),
        }

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        P = DARK
        bar = ctk.CTkFrame(self._main, height=46, corner_radius=0, fg_color=P["surface"])
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        self._status_dot = ctk.CTkLabel(
            bar, text="●", font=("Segoe UI", 14), text_color=P["text_dim"], width=22
        )
        self._status_dot.grid(row=0, column=0, padx=(16, 6))

        self._status_lbl = ctk.CTkLabel(
            bar, text="Initializing…",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=P["text_dim"], anchor="w",
        )
        self._status_lbl.grid(row=0, column=1, sticky="w")

        self._timer_lbl = ctk.CTkLabel(
            bar, text="",
            font=ctk.CTkFont("Courier New", 13, "bold"),
            text_color=P["error"], anchor="e",
        )
        self._timer_lbl.grid(row=0, column=2, padx=(6, 18))

    # ── Transcribe panel ──────────────────────────────────────────────────────
    def _build_transcribe_panel(self):
        P = DARK
        panel = ctk.CTkFrame(self._main, fg_color=P["bg"], corner_radius=0)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_remove()

        # ── Settings card ─────────────────────────────────────────────────────
        sc = ctk.CTkFrame(panel, fg_color=P["surface"], corner_radius=14)
        sc.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="ew")
        sc.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.model_var    = self._combo_col(sc, "Model",         0,
                                            ["tiny", "base", "small", "medium", "large"],
                                            config.DEFAULT_MODEL)
        self.language_var = self._combo_col(sc, "Language",      1,
                                            ["Auto", "en", "es", "fr", "de", "it",
                                             "pt", "ru", "ja", "zh", "ar", "ko",
                                             "hi", "nl", "pl", "tr", "vi", "sv"],
                                            "Auto")
        self.duration_var = self._combo_col(sc, "Duration",      2,
                                            ["5s", "10s", "15s", "30s", "60s",
                                             "120s", "180s", "300s"],
                                            f"{config.DEFAULT_DURATION}s")
        self.task_var     = self._combo_col(sc, "Task",          3,
                                            ["transcribe", "translate"],
                                            "transcribe")

        # Load button column
        col4 = ctk.CTkFrame(sc, fg_color="transparent")
        col4.grid(row=0, column=4, padx=14, pady=16)
        ctk.CTkLabel(
            col4, text="Model",
            font=ctk.CTkFont("Segoe UI", 11), text_color=P["text_dim"],
        ).pack()
        self.load_model_btn = ctk.CTkButton(
            col4, text="Load", width=84, height=34, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=P["primary"], hover_color=P["primary_hover"],
            command=self._load_model_thread,
        )
        self.load_model_btn.pack(pady=(4, 2))
        self._model_status = ctk.CTkLabel(
            col4, text="● not loaded",
            font=ctk.CTkFont("Segoe UI", 10), text_color=P["text_muted"],
        )
        self._model_status.pack()

        # ── Action row ────────────────────────────────────────────────────────
        ar = ctk.CTkFrame(panel, fg_color="transparent")
        ar.grid(row=1, column=0, padx=20, pady=(4, 0), sticky="ew")
        ar.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.record_btn = ctk.CTkButton(
            ar, text="⏺  Start Recording",
            height=46, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=P["error"], hover_color=P["error2"],
            state="disabled", command=self._toggle_recording,
        )
        self.record_btn.grid(row=0, column=0, padx=3, pady=4, sticky="ew")

        self.file_btn = ctk.CTkButton(
            ar, text="📂  Open File",
            height=46, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=P["surface"], hover_color=P["surface2"],
            border_width=1, border_color=P["border"],
            state="disabled", command=self._transcribe_file,
        )
        self.file_btn.grid(row=0, column=1, padx=3, pady=4, sticky="ew")

        # Divider
        ctk.CTkFrame(ar, width=1, height=46, fg_color=P["border"]).grid(
            row=0, column=2, padx=2, pady=4
        )

        self.copy_btn = ctk.CTkButton(
            ar, text="📋  Copy",
            height=46, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=P["surface"], hover_color=P["surface2"],
            border_width=1, border_color=P["border"],
            state="disabled", command=self._copy_to_clipboard,
        )
        self.copy_btn.grid(row=0, column=3, padx=3, pady=4, sticky="ew")

        self.save_btn = ctk.CTkButton(
            ar, text="💾  Save ▾",
            height=46, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=P["surface"], hover_color=P["surface2"],
            border_width=1, border_color=P["border"],
            state="disabled", command=self._show_save_menu,
        )
        self.save_btn.grid(row=0, column=4, padx=3, pady=4, sticky="ew")

        self.clear_btn = ctk.CTkButton(
            ar, text="🗑  Clear",
            height=46, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=P["surface"], hover_color=P["surface2"],
            border_width=1, border_color=P["border"],
            command=self._clear_output,
        )
        self.clear_btn.grid(row=0, column=5, padx=3, pady=4, sticky="ew")

        # ── Audio level meter ─────────────────────────────────────────────────
        meter_wrap = ctk.CTkFrame(panel, fg_color=P["surface"], corner_radius=8, height=18)
        meter_wrap.grid(row=2, column=0, padx=20, pady=(4, 0), sticky="ew")
        meter_wrap.grid_propagate(False)
        self._level_bar = ctk.CTkProgressBar(
            meter_wrap, mode="determinate",
            progress_color=P["success"], fg_color=P["surface2"],
            height=6, corner_radius=3,
        )
        self._level_bar.pack(fill="x", padx=2, pady=6)
        self._level_bar.set(0)

        # ── Output card ───────────────────────────────────────────────────────
        oc = ctk.CTkFrame(panel, fg_color=P["surface"], corner_radius=14)
        oc.grid(row=3, column=0, padx=20, pady=(6, 16), sticky="nsew")
        oc.grid_columnconfigure(0, weight=1)
        oc.grid_rowconfigure(1, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        hdr = ctk.CTkFrame(oc, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=16, pady=(12, 0), sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hdr, text="Transcription",
            font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=P["text"],
        ).grid(row=0, column=0, sticky="w")

        self._lang_badge = ctk.CTkLabel(
            hdr, text="",
            font=ctk.CTkFont("Segoe UI", 11), text_color=P["accent"],
        )
        self._lang_badge.grid(row=0, column=1, sticky="e", padx=4)

        self._word_count_lbl = ctk.CTkLabel(
            hdr, text="",
            font=ctk.CTkFont("Segoe UI", 11), text_color=P["text_dim"],
        )
        self._word_count_lbl.grid(row=0, column=2, sticky="e")

        self.output_text = ctk.CTkTextbox(
            oc, font=ctk.CTkFont("Segoe UI", 13),
            wrap="word", fg_color=P["surface"], text_color=P["text"],
            border_width=0, activate_scrollbars=True,
        )
        self.output_text.grid(row=1, column=0, padx=12, pady=(8, 12), sticky="nsew")

        return panel

    # Helper: labelled combobox column
    def _combo_col(self, parent, label: str, col: int,
                   values: list, default: str) -> ctk.StringVar:
        P = DARK if self._is_dark else LIGHT
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, padx=12, pady=16, sticky="ew")
        ctk.CTkLabel(
            frame, text=label,
            font=ctk.CTkFont("Segoe UI", 11), text_color=P["text_dim"],
        ).pack()
        var = ctk.StringVar(value=default)
        ctk.CTkComboBox(
            frame, values=values, variable=var,
            width=120, height=32, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 12),
        ).pack(pady=(4, 0))
        return var

    # ── History panel ─────────────────────────────────────────────────────────
    def _build_history_panel(self):
        P = DARK
        panel = ctk.CTkFrame(self._main, fg_color=P["bg"], corner_radius=0)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_remove()

        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=22, pady=(18, 8), sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            hdr, text="Transcription History",
            font=ctk.CTkFont("Segoe UI", 20, "bold"), text_color=P["text"],
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            hdr, text="Clear All", width=96, height=32, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=P["surface"], hover_color=P["error"],
            border_width=1, border_color=P["border"],
            command=self._clear_history,
        ).grid(row=0, column=2, sticky="e")

        self._hist_scroll = ctk.CTkScrollableFrame(
            panel, fg_color=P["bg"],
            scrollbar_button_color=P["border"],
        )
        self._hist_scroll.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self._hist_scroll.grid_columnconfigure(0, weight=1)
        self._hist_placeholder = ctk.CTkLabel(
            self._hist_scroll,
            text="No transcriptions yet.\nGo to Transcribe to get started.",
            font=ctk.CTkFont("Segoe UI", 13), text_color=P["text_dim"],
        )
        self._hist_placeholder.grid(row=0, column=0, pady=50)
        return panel

    def _refresh_history(self):
        P = DARK if self._is_dark else LIGHT
        for w in self._hist_scroll.winfo_children():
            w.destroy()
        if not self.history.items:
            ctk.CTkLabel(
                self._hist_scroll,
                text="No transcriptions yet.\nGo to Transcribe to get started.",
                font=ctk.CTkFont("Segoe UI", 13), text_color=P["text_dim"],
            ).grid(row=0, column=0, pady=50)
            return
        for i, entry in enumerate(self.history.items):
            card = ctk.CTkFrame(
                self._hist_scroll, fg_color=P["surface"], corner_radius=12
            )
            card.grid(row=i, column=0, pady=6, padx=2, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            card_hdr = ctk.CTkFrame(card, fg_color="transparent")
            card_hdr.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="ew")
            card_hdr.grid_columnconfigure(2, weight=1)

            icon = "🎤" if entry["source"] == "microphone" else "📂"
            ctk.CTkLabel(
                card_hdr,
                text=f"{icon}  {entry['timestamp']}",
                font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=P["text"],
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                card_hdr,
                text=f"🌐 {entry['language']}  ·  {entry['word_count']} words",
                font=ctk.CTkFont("Segoe UI", 11), text_color=P["text_dim"],
            ).grid(row=0, column=1, padx=14, sticky="w")

            ctk.CTkButton(
                card_hdr, text="Restore", width=72, height=28, corner_radius=6,
                font=ctk.CTkFont("Segoe UI", 11),
                fg_color=P["primary"], hover_color=P["primary_hover"],
                command=lambda e=entry: self._restore_history_entry(e),
            ).grid(row=0, column=3, sticky="e")

            preview = entry["text"][:240] + ("…" if len(entry["text"]) > 240 else "")
            ctk.CTkLabel(
                card, text=preview,
                font=ctk.CTkFont("Segoe UI", 12), text_color=P["text_dim"],
                wraplength=660, justify="left", anchor="w",
            ).grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")

    def _restore_history_entry(self, entry: dict):
        result = {
            "text":     entry["text"],
            "language": entry["language"],
            "segments": entry["segments"],
        }
        self.current_result = result
        self._display_result(result)
        self._show_panel("transcribe")
        self._set_status(f"Restored transcription from {entry['timestamp']}", "info")

    def _clear_history(self):
        if messagebox.askyesno("Clear History",
                               "Clear all session history?"):
            self.history.clear()
            self._refresh_history()

    # ── Settings panel ────────────────────────────────────────────────────────
    def _build_settings_panel(self):
        P = DARK
        panel = ctk.CTkFrame(self._main, fg_color=P["bg"], corner_radius=0)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_remove()

        scroll = ctk.CTkScrollableFrame(
            panel, fg_color=P["bg"],
            scrollbar_button_color=P["border"],
        )
        scroll.grid(row=0, column=0, padx=22, pady=16, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            scroll, text="Settings",
            font=ctk.CTkFont("Segoe UI", 22, "bold"), text_color=P["text"],
        ).grid(row=0, column=0, pady=(8, 22), sticky="w")

        r = 1
        r = self._settings_section(scroll, r, "🎵  Audio", [
            ("Save recordings to disk",        "save_audio_var",      config.SAVE_AUDIO,       "switch"),
            ("Auto-transcribe after recording", "auto_transcribe_var", config.AUTO_TRANSCRIBE,  "switch"),
        ])
        r = self._settings_section(scroll, r, "📝  Transcription", [
            ("Auto-save transcriptions",        "save_transcription_var", config.SAVE_TRANSCRIPTION, "switch"),
            ("Show timestamped segments",        "show_segments_var",     True,                       "switch"),
            ("Beam size (1 = fast, 5 = best)",   "beam_size_var",         str(config.BEAM_SIZE),      "entry"),
        ])
        r = self._settings_section(scroll, r, "🤖  Model", [
            ("Inference device", "device_var", config.MODEL_DEVICE, "combo",
             ["auto", "cpu", "cuda"]),
        ])

        return panel

    def _settings_section(self, parent, start_row, title, items):
        P = DARK if self._is_dark else LIGHT
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=P["text"],
        ).grid(row=start_row, column=0, pady=(14, 4), sticky="w")

        card = ctk.CTkFrame(parent, fg_color=P["surface"], corner_radius=12)
        card.grid(row=start_row + 1, column=0, sticky="ew", pady=(0, 6))
        card.grid_columnconfigure(0, weight=1)

        for idx, item in enumerate(items):
            label_txt, attr, default, wtype = item[0], item[1], item[2], item[3]
            if idx > 0:
                ctk.CTkFrame(card, height=1, fg_color=P["border"]).grid(
                    row=idx * 2 - 1, column=0, sticky="ew", padx=16
                )
            row_frame = ctk.CTkFrame(card, fg_color="transparent")
            row_frame.grid(row=idx * 2, column=0, padx=16, pady=10, sticky="ew")
            row_frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row_frame, text=label_txt,
                font=ctk.CTkFont("Segoe UI", 12), text_color=P["text"], anchor="w",
            ).grid(row=0, column=0, sticky="w")

            if wtype == "switch":
                var = ctk.BooleanVar(value=default)
                setattr(self, attr, var)
                sw = ctk.CTkSwitch(row_frame, variable=var, text="", width=46)
                sw.grid(row=0, column=2, sticky="e")
                if default:
                    sw.select()
            elif wtype == "entry":
                var = ctk.StringVar(value=str(default))
                setattr(self, attr, var)
                ctk.CTkEntry(
                    row_frame, textvariable=var,
                    width=80, height=30, corner_radius=6,
                ).grid(row=0, column=2, sticky="e")
            elif wtype == "combo":
                options = item[4] if len(item) > 4 else []
                var = ctk.StringVar(value=str(default))
                setattr(self, attr, var)
                ctk.CTkComboBox(
                    row_frame, values=options, variable=var,
                    width=120, height=30, corner_radius=6,
                ).grid(row=0, column=2, sticky="e")

        return start_row + 2

    # ── Model loading ─────────────────────────────────────────────────────────
    def _load_model_thread(self):
        if self.is_loading_model:
            return
        self.is_loading_model = True
        self.load_model_btn.configure(state="disabled", text="Loading…")
        self._model_status.configure(
            text="● loading…", text_color=DARK["warning"]
        )
        self._set_status("Loading model — please wait, first run may download weights…",
                         "warning")

        def _load():
            try:
                self.stt_engine.model_name = self.model_var.get()
                self.stt_engine.model = None      # force reload on model change
                self.stt_engine.load_model()
                self.after(0, self._on_model_loaded)
            except Exception as exc:
                self.after(0, lambda e=str(exc): self._on_model_error(e))

        threading.Thread(target=_load, daemon=True).start()

    def _on_model_loaded(self):
        P = DARK if self._is_dark else LIGHT
        self.is_loading_model = False
        self.load_model_btn.configure(state="normal", text="Reload")
        self._model_status.configure(
            text=f"● {self.model_var.get()} ready",
            text_color=P["success"],
        )
        self.record_btn.configure(state="normal")
        self.file_btn.configure(state="normal")
        self._set_status(f"Model '{self.model_var.get()}' loaded — ready to transcribe",
                         "success")

    def _on_model_error(self, error: str):
        self.is_loading_model = False
        self.load_model_btn.configure(state="normal", text="Retry")
        self._model_status.configure(text="● error", text_color=DARK["error"])
        self._set_status(f"Model load failed: {error}", "error")
        messagebox.showerror("Model Error", f"Failed to load model:\n{error}")

    # ── Recording ─────────────────────────────────────────────────────────────
    def _toggle_recording(self):
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        self.is_recording = True
        duration = int(self.duration_var.get().rstrip("s"))
        self.record_btn.configure(text="⏹  Stop")
        self.file_btn.configure(state="disabled")
        self._set_status("🔴  Recording — speak clearly…", "error")
        self._record_start = time.time()
        self._update_timer()
        self._start_level_animation()

        def _record():
            try:
                audio = self.audio_handler.record_audio(duration=duration)
                self.current_audio = audio
                if getattr(self, "save_audio_var", None) and self.save_audio_var.get():
                    self.audio_handler.save_audio(audio, output_dir=config.RECORDINGS_DIR)
                self.after(0, self._on_recording_complete)
            except Exception as exc:
                self.after(0, lambda e=str(exc): self._on_recording_error(e))

        threading.Thread(target=_record, daemon=True).start()

    def _stop_recording(self):
        self._set_status("Finishing recording…", "warning")

    def _on_recording_complete(self):
        self.is_recording = False
        self._stop_timer()
        self._stop_level_animation()
        self.record_btn.configure(text="⏺  Start Recording")
        self.file_btn.configure(state="normal")
        self._set_status("Recording complete — transcribing…", "info")
        if getattr(self, "auto_transcribe_var", None) and self.auto_transcribe_var.get():
            self._transcribe_audio()

    def _on_recording_error(self, error: str):
        self.is_recording = False
        self._stop_timer()
        self._stop_level_animation()
        self.record_btn.configure(text="⏺  Start Recording")
        self.file_btn.configure(state="normal")
        self._set_status(f"Recording error: {error}", "error")
        messagebox.showerror("Recording Error", f"Failed to record:\n{error}")

    # ── Transcription ─────────────────────────────────────────────────────────
    def _transcribe_audio(self):
        if self.current_audio is None:
            return
        language = None if self.language_var.get() == "Auto" else self.language_var.get()
        task = self.task_var.get()

        def _do():
            try:
                result = self.stt_engine.transcribe_audio_data(
                    self.current_audio,
                    sample_rate=config.SAMPLE_RATE,
                    language=language,
                    task=task,
                )
                self.current_result = result
                self.history.add(result, source="microphone")
                self.after(0, lambda r=result: self._on_transcribe_done(r))
            except Exception as exc:
                self.after(0, lambda e=str(exc): self._on_transcribe_error(e))

        threading.Thread(target=_do, daemon=True).start()

    def _transcribe_file(self):
        filepath = filedialog.askopenfilename(
            title="Open Audio File",
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg *.wma *.aac"),
                ("All Files", "*.*"),
            ],
        )
        if not filepath:
            return
        self.record_btn.configure(state="disabled")
        self.file_btn.configure(state="disabled")
        self._set_status(f"Transcribing: {Path(filepath).name}…", "info")
        language = None if self.language_var.get() == "Auto" else self.language_var.get()
        task = self.task_var.get()

        def _do():
            try:
                result = self.stt_engine.transcribe_file(
                    filepath, language=language, task=task
                )
                self.current_result = result
                self.history.add(result, source=Path(filepath).name)
                self.after(0, lambda r=result: self._on_transcribe_done(r))
            except Exception as exc:
                self.after(0, lambda e=str(exc): self._on_transcribe_error(e))

        threading.Thread(target=_do, daemon=True).start()

    def _on_transcribe_done(self, result: dict):
        self._display_result(result)
        self.record_btn.configure(state="normal")
        self.file_btn.configure(state="normal")
        wc = len(result.get("text", "").split())
        self._set_status(f"Transcription complete  ·  {wc} words detected", "success")
        self._refresh_history()

    def _on_transcribe_error(self, error: str):
        self.record_btn.configure(state="normal")
        self.file_btn.configure(state="normal")
        self._set_status(f"Transcription failed: {error}", "error")
        messagebox.showerror("Transcription Error", f"Failed to transcribe:\n{error}")

    def _display_result(self, result: dict):
        P = DARK if self._is_dark else LIGHT
        self.output_text.configure(state="normal")
        self.output_text.delete("0.0", "end")

        text     = result.get("text", "").strip()
        lang     = result.get("language", "")
        segments = result.get("segments", [])

        self.output_text.insert("end", text + "\n")

        show_segs = getattr(self, "show_segments_var", None)
        if segments and (show_segs is None or show_segs.get()):
            self.output_text.insert("end", "\n" + "─" * 64 + "\n")
            self.output_text.insert("end", "Timestamped segments\n\n")
            for seg in segments:
                t0 = self._fmt_ts(seg["start"])
                t1 = self._fmt_ts(seg["end"])
                self.output_text.insert("end", f"[{t0} → {t1}]  {seg['text'].strip()}\n")

        self._lang_badge.configure(text=f"🌐  {lang}")
        wc = len(text.split())
        cc = len(text)
        self._word_count_lbl.configure(text=f"{wc} words  ·  {cc} chars")
        self.copy_btn.configure(state="normal")
        self.save_btn.configure(state="normal")

    # ── Export / Save ─────────────────────────────────────────────────────────
    def _copy_to_clipboard(self):
        if self.current_result is None:
            return
        self.clipboard_clear()
        self.clipboard_append(self.current_result.get("text", "").strip())
        self._set_status("Copied to clipboard ✓", "success")

    def _show_save_menu(self):
        if self.current_result is None:
            return
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Save as TXT",               command=self._save_txt)
        menu.add_command(label="Save as SRT (subtitles)",   command=self._save_srt)
        menu.add_command(label="Save as JSON",              command=self._save_json)
        try:
            x = self.save_btn.winfo_rootx()
            y = self.save_btn.winfo_rooty() + self.save_btn.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _save_txt(self):
        fp = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            initialfile=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if fp:
            try:
                self.stt_engine.save_transcription(
                    self.current_result,
                    filename=Path(fp).name,
                    output_dir=str(Path(fp).parent),
                )
                self._set_status(f"Saved TXT: {Path(fp).name}", "success")
            except Exception as exc:
                messagebox.showerror("Save Error", str(exc))

    def _save_srt(self):
        fp = filedialog.asksaveasfilename(
            defaultextension=".srt",
            filetypes=[("SRT Subtitle Files", "*.srt")],
            initialfile=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
        )
        if fp:
            try:
                self.stt_engine.save_as_srt(self.current_result, filepath=fp)
                self._set_status(f"Saved SRT: {Path(fp).name}", "success")
            except Exception as exc:
                messagebox.showerror("Save Error", str(exc))

    def _save_json(self):
        fp = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        if fp:
            try:
                self.stt_engine.save_as_json(self.current_result, filepath=fp)
                self._set_status(f"Saved JSON: {Path(fp).name}", "success")
            except Exception as exc:
                messagebox.showerror("Save Error", str(exc))

    def _clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("0.0", "end")
        self.current_result = None
        self.current_audio  = None
        self.copy_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        self._lang_badge.configure(text="")
        self._word_count_lbl.configure(text="")
        self._set_status("Cleared", "dim")

    # ── Theme toggle ──────────────────────────────────────────────────────────
    def _toggle_theme(self):
        self._is_dark = bool(self._theme_sw.get())
        ctk.set_appearance_mode("dark" if self._is_dark else "light")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _set_status(self, msg: str, kind: str = "dim"):
        P = DARK if self._is_dark else LIGHT
        colours = {
            "info":      P["info"],
            "success":   P["success"],
            "error":     P["error"],
            "warning":   P["warning"],
            "dim":       P["text_dim"],
            "recording": P["error"],
        }
        c = colours.get(kind, P["text_dim"])
        self._status_dot.configure(text_color=c)
        self._status_lbl.configure(text=msg, text_color=c)

    @staticmethod
    def _fmt_ts(seconds: float) -> str:
        m  = int(seconds // 60)
        s  = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{m:02d}:{s:02d}.{ms:03d}"

    def _update_timer(self):
        if not self.is_recording or self._record_start is None:
            return
        elapsed = int(time.time() - self._record_start)
        self._timer_lbl.configure(text=f"⏺  {elapsed // 60:02d}:{elapsed % 60:02d}")
        self._timer_job = self.after(500, self._update_timer)

    def _stop_timer(self):
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        self._timer_lbl.configure(text="")
        self._record_start = None

    def _start_level_animation(self):
        self._animate_level()

    def _animate_level(self):
        if not self.is_recording:
            self._level_bar.set(0)
            return
        # sounddevice.rec() is blocking, so real-time levels are unavailable here;
        # animate with pseudo-random values to indicate active recording.
        self._level_bar.set(random.uniform(0.05, 0.95))
        self._level_job = self.after(120, self._animate_level)

    def _stop_level_animation(self):
        if self._level_job:
            self.after_cancel(self._level_job)
            self._level_job = None
        self._level_bar.set(0)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    """Launch the GUI application."""
    app = STTApp()
    app.mainloop()


if __name__ == "__main__":
    main()
