import threading
from typing import Callable, Optional

import config
from audio_handler import AudioHandler
from hotkey_handler import ClipboardManager, HotkeyListener
from stt_engine import STTEngine


class STTService:
    """Service layer that coordinates audio, transcription, settings, and hotkey."""

    def __init__(self):
        self.audio_handler = AudioHandler(sample_rate=config.SAMPLE_RATE, channels=config.CHANNELS)
        self.stt_engine: Optional[STTEngine] = None
        self.hotkey_listener: Optional[HotkeyListener] = None
        self.clipboard_manager = ClipboardManager()
        self._hotkey_enabled = False
        self._lock = threading.Lock()

    def get_settings(self) -> dict:
        return {
            "model": config.DEFAULT_MODEL,
            "language": "auto" if config.DEFAULT_LANGUAGE is None else config.DEFAULT_LANGUAGE,
            "duration": config.DEFAULT_DURATION,
            "save_audio": config.SAVE_AUDIO,
            "save_transcription": config.SAVE_TRANSCRIPTION,
            "use_webrtc_vad": config.USE_WEBRTC_VAD,
            "hotkey_combination": config.HOTKEY_COMBINATION,
            "hotkey_silence_duration": config.HOTKEY_SILENCE_DURATION,
            "auto_paste": config.AUTO_PASTE,
            "hotkey_enabled": self._hotkey_enabled,
        }

    def update_settings(self, settings: dict):
        config.DEFAULT_MODEL = settings["model"]
        config.DEFAULT_LANGUAGE = None if settings["language"] == "auto" else settings["language"]
        config.DEFAULT_DURATION = int(settings["duration"])
        config.SAVE_AUDIO = bool(settings["save_audio"])
        config.SAVE_TRANSCRIPTION = bool(settings["save_transcription"])
        config.USE_WEBRTC_VAD = bool(settings["use_webrtc_vad"])
        config.HOTKEY_SILENCE_DURATION = float(settings["hotkey_silence_duration"])
        config.AUTO_PASTE = bool(settings["auto_paste"])
        config.save_settings()

    def load_model(self, model_name: str) -> str:
        with self._lock:
            engine = STTEngine(model_name=model_name)
            engine.load_model()
            self.stt_engine = engine
        return f"Model loaded: {model_name}"

    def stop_recording(self):
        self.audio_handler.stop_recording()

    def record_and_transcribe(
        self,
        duration: int,
        language: str,
        use_vad: bool,
        silence_duration: float,
    ) -> dict:
        engine = self._require_model()

        if use_vad:
            audio_data = self.audio_handler.record_with_vad(
                max_duration=duration,
                silence_duration=silence_duration,
                use_webrtc=config.USE_WEBRTC_VAD,
            )
        else:
            audio_data = self.audio_handler.record_audio(duration=duration)

        if audio_data.size == 0:
            return {"text": "", "language": "unknown", "audio_path": None}

        audio_path = None
        if config.SAVE_AUDIO:
            audio_path = self.audio_handler.save_audio(audio_data, output_dir=config.RECORDINGS_DIR)

        result = engine.transcribe_audio_data(
            audio_data,
            sample_rate=config.SAMPLE_RATE,
            language=None if language == "auto" else language,
        )

        if config.SAVE_TRANSCRIPTION:
            engine.save_transcription(result)

        result["audio_path"] = audio_path
        return result

    def transcribe_file(self, file_path: str, language: str) -> dict:
        engine = self._require_model()

        result = engine.transcribe_file(
            file_path,
            language=None if language == "auto" else language,
        )

        if config.SAVE_TRANSCRIPTION:
            engine.save_transcription(result)

        return result

    def toggle_hotkey(
        self,
        enable: bool,
        on_transcription: Callable[[str], None],
        on_status: Optional[Callable[[str], None]] = None,
    ) -> str:
        if enable:
            self._require_model()

            def _on_hotkey_trigger():
                try:
                    if on_status:
                        on_status("Hotkey triggered. Recording...")

                    audio_data = self.audio_handler.record_with_vad(
                        max_duration=config.DEFAULT_DURATION,
                        silence_duration=config.HOTKEY_SILENCE_DURATION,
                        use_webrtc=config.USE_WEBRTC_VAD,
                    )
                    if audio_data.size == 0:
                        return

                    result = self.stt_engine.transcribe_audio_data(audio_data, sample_rate=config.SAMPLE_RATE)
                    text = result.get("text", "").strip()
                    if not text:
                        return

                    if config.AUTO_PASTE:
                        self.clipboard_manager.paste_text(text, auto_paste=True)
                    else:
                        self.clipboard_manager.copy_to_clipboard(text)

                    on_transcription(text)
                    if on_status:
                        on_status("Hotkey transcription complete")
                except Exception as exc:
                    if on_status:
                        on_status(f"Hotkey error: {exc}")

            if self.hotkey_listener:
                self.hotkey_listener.stop()

            self.hotkey_listener = HotkeyListener(
                hotkey=config.HOTKEY_COMBINATION,
                callback=_on_hotkey_trigger,
            )
            self.hotkey_listener.start()
            self._hotkey_enabled = True
            return f"Hotkey enabled: {config.HOTKEY_COMBINATION}"

        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self._hotkey_enabled = False
        return "Hotkey disabled"

    def cleanup(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()

    def _require_model(self) -> STTEngine:
        if self.stt_engine is None or self.stt_engine.model is None:
            raise RuntimeError("Load a model first")
        return self.stt_engine
