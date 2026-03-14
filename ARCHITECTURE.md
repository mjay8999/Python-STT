# Architecture — Local Speech-to-Text Desktop App (Python GUI)

## Overview

This project is now a pure Python desktop app:
- UI: `customtkinter`
- Core STT: `openai-whisper` via `stt_engine.py`
- Audio capture: `sounddevice` via `audio_handler.py`
- Voice activity detection: `webrtcvad` via `vad.py`
- Global hotkey + clipboard: `hotkey_handler.py`

There is no React, Electron, or HTTP API layer.

---

## High-Level Design

```
┌──────────────────────────────────────────────────────────────┐
│              Python Desktop GUI (main.py / gui/app.py)      │
│                                                              │
│   ┌───────────────────┐    ┌──────────────────────────────┐  │
│   │  UI Components    │    │       STTService             │  │
│   │ (record/settings/ │───►│ gui/services/stt_service.py  │  │
│   │ transcription)    │    │                              │  │
│   └───────────────────┘    └──────────────┬───────────────┘  │
└────────────────────────────────────────────┼──────────────────┘
                                             │
         ┌───────────────────────────────────┼───────────────────────────────────┐
         │                                   │                                   │
   ┌─────▼──────────┐                 ┌──────▼──────────┐                 ┌──────▼──────────┐
   │ audio_handler  │                 │   stt_engine    │                 │ hotkey_handler  │
   │ mic capture +  │                 │ whisper model   │                 │ global hotkey + │
   │ VAD recording  │                 │ load/transcribe │                 │ clipboard paste │
   └────────────────┘                 └─────────────────┘                 └─────────────────┘
```

---

## Module Responsibilities

- `main.py`
  - Application entrypoint.
  - Starts `STTDesktopApp`.

- `gui/app.py`
  - Main window lifecycle.
  - Background task threading and UI queue handling.
  - Connects UI events to service operations.

- `gui/services/stt_service.py`
  - Orchestrates model loading, recording, transcription, file transcription, hotkey toggle.
  - Applies/saves runtime settings to `config.py` + `settings.json`.

- `gui/components/recording_panel.py`
  - Recording controls (record/stop/file).

- `gui/components/settings_panel.py`
  - Model/language/duration/VAD/hotkey/save settings controls.

- `gui/components/transcription_panel.py`
  - Current transcription and history display.

- `gui/components/status_bar.py`
  - Real-time status messaging.

- `audio_handler.py`
  - Audio recording (fixed duration + VAD mode).

- `stt_engine.py`
  - Whisper model management and transcription.

- `hotkey_handler.py`
  - Global hotkey registration and clipboard operations.

- `config.py`
  - Defaults + persisted settings support.

---

## Runtime Flow

1. User loads a Whisper model from Settings.
2. User starts recording or picks an audio file.
3. `STTService` executes work in background thread.
4. Transcription result is pushed to UI queue.
5. GUI updates current result + history.

For hotkey mode:
1. User enables hotkey.
2. `HotkeyListener` captures `Ctrl+Shift+Space`.
3. Callback records audio with VAD, transcribes, then copy/pastes text.
4. GUI receives status/result updates asynchronously.

---

## Concurrency Model

- GUI stays responsive by running heavy work in daemon threads.
- UI updates are marshaled back through an internal queue and processed on the main Tk thread.
- Recording stop uses `AudioHandler.stop_recording()` with a thread event.

---

## Storage & Outputs

- `settings.json` stores persisted user settings.
- `recordings/` stores WAV recordings when enabled.
- `transcriptions/` stores text outputs when enabled.
