# Python Speech-to-Text Desktop Application

🎤 Fully offline speech-to-text desktop app with a modern **Python GUI** (CustomTkinter), global hotkey, VAD auto-stop, and multilingual Whisper transcription.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)

## ✨ Features

- ✅ 100% offline after model download
- ✅ Modern Python desktop GUI (no web frontend)
- ✅ Whisper model support: tiny/base/small/medium/large
- ✅ Voice Activity Detection (auto-stop on silence)
- ✅ Global hotkey dictation (`Ctrl+Shift+Space`)
- ✅ Audio file transcription (WAV/MP3/M4A/FLAC/OGG)
- ✅ Config persistence via `settings.json`

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.12+
- FFmpeg in `PATH`

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
run_desktop_app.bat
```

or:

```bash
python main.py
```

## 📖 Usage

1. Open app
2. In Settings, pick model and click **Load Model**
3. Click **Start Recording** (or use file transcription)
4. Speak naturally; VAD stops on silence
5. Read/copy result from the transcription panel

### Global Hotkey

1. Load model
2. Enable **Global Hotkey** in Settings
3. Press `Ctrl+Shift+Space` anywhere
4. Transcribed text is copied/pasted based on settings

## 🌍 Languages

- Auto-detect
- en, hi, es, fr, de, it, pt, ru, ja, zh

## 🏗️ Architecture (Python-only)

```
┌─────────────────────────────────────────┐
│      Python Desktop GUI (CustomTkinter) │
│  ┌───────────────────────────────────┐  │
│  │  Recording / Settings / History   │  │
│  └─────────────┬─────────────────────┘  │
│                │                         │
│  ┌─────────────▼─────────────────────┐  │
│  │        Service Layer               │  │
│  │      (gui/services/stt_service.py) │  │
│  └──────┬───────────────┬────────────┘  │
└─────────┼───────────────┼───────────────┘
          │               │
   ┌──────▼──────┐   ┌────▼───────────┐
   │ audio_handler│   │ hotkey_handler │
   └──────┬──────┘   └────┬───────────┘
          │               │
          └──────┬────────┘
                 ▼
             stt_engine
            (Whisper AI)
```

## ⚙️ Configuration

Tune defaults in `config.py` or through the GUI settings panel:
- model/language/duration
- save audio/transcription
- VAD behavior
- hotkey auto-paste behavior

## 📝 License

MIT
