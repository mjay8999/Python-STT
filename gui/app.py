import queue
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

from gui.components.recording_panel import RecordingPanel
from gui.components.settings_panel import SettingsPanel
from gui.components.status_bar import StatusBar
from gui.components.transcription_panel import TranscriptionPanel
from gui.services.stt_service import STTService


class STTDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Local Speech-to-Text")
        self.geometry("1100x760")
        self.minsize(980, 680)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.service = STTService()
        self.ui_queue: queue.Queue = queue.Queue()
        self.busy = False

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()
        self._load_initial_settings()
        self.after(100, self._process_ui_queue)

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Speech-to-Text Desktop (Python GUI)",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="w")

        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, padx=14, pady=8, sticky="nsew")
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(1, weight=1)

        self.recording_panel = RecordingPanel(
            content,
            on_record=self._on_record,
            on_stop=self._on_stop_recording,
            on_transcribe_file=self._on_transcribe_file,
        )
        self.recording_panel.grid(row=0, column=0, columnspan=2, padx=12, pady=(12, 8), sticky="ew")

        self.transcription_panel = TranscriptionPanel(content)
        self.transcription_panel.grid(row=1, column=0, padx=(12, 6), pady=(0, 12), sticky="nsew")

        self.settings_panel = SettingsPanel(
            content,
            on_load_model=self._on_load_model,
            on_save_settings=self._on_save_settings,
            on_toggle_hotkey=self._on_toggle_hotkey,
        )
        self.settings_panel.grid(row=1, column=1, padx=(6, 12), pady=(0, 12), sticky="nsew")

        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="ew")

    def _load_initial_settings(self):
        settings = self.service.get_settings()
        self.settings_panel.set_values(settings)
        self.status_bar.set_status("Ready. Load a model to begin.")

    def _set_busy(self, busy: bool, message: str = ""):
        self.busy = busy
        self.recording_panel.set_busy(busy)
        if message:
            self.status_bar.set_status(message)

    def _start_task(self, task_fn, on_success=None, start_message="Working..."):
        if self.busy:
            return

        self._set_busy(True, start_message)

        def _worker():
            try:
                result = task_fn()
                self.ui_queue.put(("success", on_success, result))
            except Exception as exc:
                self.ui_queue.put(("error", str(exc)))
            finally:
                self.ui_queue.put(("idle", None))

        threading.Thread(target=_worker, daemon=True).start()

    def _process_ui_queue(self):
        while not self.ui_queue.empty():
            item = self.ui_queue.get_nowait()
            event = item[0]

            if event == "success":
                _, callback, result = item
                if callback:
                    callback(result)
            elif event == "error":
                _, message = item
                messagebox.showerror("Error", message)
                self.status_bar.set_status(f"Error: {message}")
            elif event == "idle":
                self._set_busy(False)
            elif event == "hotkey_text":
                _, text = item
                self.transcription_panel.set_current_result(text, "auto", "Hotkey")
            elif event == "hotkey_status":
                _, text = item
                self.status_bar.set_status(text)

        self.after(100, self._process_ui_queue)

    def _on_load_model(self, model_name: str):
        self._start_task(
            task_fn=lambda: self.service.load_model(model_name),
            on_success=lambda message: self.status_bar.set_status(message),
            start_message=f"Loading model: {model_name}...",
        )

    def _on_save_settings(self, settings: dict):
        self.service.update_settings(settings)
        self.status_bar.set_status("Settings saved")

    def _on_record(self):
        settings = self.settings_panel.get_values()
        self._start_task(
            task_fn=lambda: self.service.record_and_transcribe(
                duration=int(settings["duration"]),
                language=settings["language"],
                use_vad=bool(settings["use_webrtc_vad"]),
                silence_duration=float(settings["hotkey_silence_duration"]),
            ),
            on_success=lambda result: self._show_result(result, "Microphone"),
            start_message="Recording and transcribing...",
        )

    def _on_stop_recording(self):
        self.service.stop_recording()
        self.status_bar.set_status("Stop requested")

    def _on_transcribe_file(self):
        path = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        settings = self.settings_panel.get_values()
        self._start_task(
            task_fn=lambda: self.service.transcribe_file(path, settings["language"]),
            on_success=lambda result: self._show_result(result, "File"),
            start_message="Transcribing file...",
        )

    def _on_toggle_hotkey(self, enabled: bool):
        def _status_update(text: str):
            self.ui_queue.put(("hotkey_status", text))

        def _on_hotkey_text(text: str):
            self.ui_queue.put(("hotkey_text", text))

        self._start_task(
            task_fn=lambda: self.service.toggle_hotkey(enabled, _on_hotkey_text, _status_update),
            on_success=lambda message: self.status_bar.set_status(message),
            start_message="Updating hotkey...",
        )

    def _show_result(self, result: dict, source: str):
        text = result.get("text", "")
        language = result.get("language", "unknown")
        self.transcription_panel.set_current_result(text, language, source)
        self.status_bar.set_status("Transcription complete")

    def _on_close(self):
        self.service.cleanup()
        self.destroy()
