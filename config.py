"""
Configuration settings for STT application
"""

# Model Settings
DEFAULT_MODEL = "base"  # Options: tiny, base, small, medium, large
MODEL_DEVICE = "auto"  # Options: auto, cpu, cuda
COMPUTE_TYPE = "float16"  # Options: float16, int8, float32

# Audio Settings
SAMPLE_RATE = 16000  # Hz (16000 is optimal for Whisper)
CHANNELS = 1  # Mono audio
DEFAULT_DURATION = 10  # seconds

# Language Settings
DEFAULT_LANGUAGE = None  # Auto-detect (or set to 'en', 'es', 'fr', etc.)
TASK = "transcribe"  # Options: transcribe, translate

# Output Settings
OUTPUT_DIR = "transcriptions"
RECORDINGS_DIR = "recordings"
SAVE_AUDIO = True  # Save recorded audio files
SAVE_TRANSCRIPTION = True  # Save transcription to text file

# GUI Settings
WINDOW_TITLE = "STT Studio — Local Speech-to-Text"
WINDOW_SIZE = "1120x720"
THEME = "dark"          # Options: dark, light, system

# Advanced Settings
BEAM_SIZE = 5  # Higher = more accurate but slower
VAD_FILTER = True  # Voice Activity Detection
CONDITION_ON_PREVIOUS_TEXT = True  # Use previous text for context

# Model Download Settings
MODEL_CACHE_DIR = None  # None = default cache, or specify custom path
