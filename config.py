"""
Configuration settings for STT application
"""

import json
import os
import sys

# Model Settings
DEFAULT_MODEL = "base"  # Options: tiny, base, small, medium, large
MODEL_DEVICE = "auto"   # Options: auto, cpu, cuda

# Audio Settings
SAMPLE_RATE = 16000     # Hz (16000 is optimal for Whisper)
CHANNELS = 1            # Mono audio
DEFAULT_DURATION = 10   # seconds

# Language Settings
DEFAULT_LANGUAGE = None  # Auto-detect (or set to 'en', 'es', 'fr', etc.)
TASK = "transcribe"      # Options: transcribe, translate

# Output Settings
OUTPUT_DIR = "transcriptions"
RECORDINGS_DIR = "recordings"
SAVE_AUDIO = True           # Save recorded audio files
SAVE_TRANSCRIPTION = True   # Save transcription to text file

# GUI Settings
WINDOW_TITLE = "Local Speech-to-Text"
WINDOW_SIZE = "800x600"
THEME = "default"

# Advanced Settings
BEAM_SIZE = 5                       # Higher = more accurate but slower
VAD_FILTER = True                   # Voice Activity Detection
CONDITION_ON_PREVIOUS_TEXT = True   # Use previous text for context

# Model Download Settings
MODEL_CACHE_DIR = None  # None = default cache, or specify custom path

# Hotkey Settings
HOTKEY_COMBINATION = "ctrl+shift+space"  # Global hotkey to trigger recording
HOTKEY_MAX_DURATION = 30                 # Maximum recording duration in seconds
HOTKEY_SILENCE_DURATION = 1.5           # Seconds of silence before auto-stop
HOTKEY_LANGUAGE = None                  # Language for hotkey transcription (None = auto-detect)

# Voice Activity Detection Settings
USE_WEBRTC_VAD = True        # Use WebRTC VAD (True) or simple energy detection (False)
VAD_AGGRESSIVENESS = 2       # WebRTC VAD aggressiveness (0-3, higher = more aggressive)
SILENCE_THRESHOLD = 0.01    # Energy threshold for silence detection (if not using WebRTC)

# Auto-Paste Settings
AUTO_PASTE = True   # Automatically paste transcription to active window
PASTE_DELAY = 0.1   # Delay before pasting (seconds)

# ── Settings persistence ───────────────────────────────────────────────────────

_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

# Keys that are allowed to be saved/loaded from settings.json
_PERSISTED_KEYS = [
    'DEFAULT_MODEL',
    'DEFAULT_LANGUAGE',
    'DEFAULT_DURATION',
    'SAVE_AUDIO',
    'SAVE_TRANSCRIPTION',
    'USE_WEBRTC_VAD',
    'HOTKEY_COMBINATION',
    'HOTKEY_SILENCE_DURATION',
    'AUTO_PASTE',
]


def load_settings():
    """Load persisted settings from settings.json, overriding module defaults."""
    module = sys.modules[__name__]
    if not os.path.exists(_SETTINGS_FILE):
        return
    try:
        with open(_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        for key, value in saved.items():
            if key in _PERSISTED_KEYS and hasattr(module, key):
                setattr(module, key, value)
    except Exception as e:
        print(f"Warning: Could not load settings.json: {e}")


def save_settings():
    """Persist current settings to settings.json."""
    module = sys.modules[__name__]
    data = {key: getattr(module, key) for key in _PERSISTED_KEYS}
    try:
        with open(_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save settings.json: {e}")


# Apply any previously persisted overrides on import
load_settings()
