# Local Speech-to-Text Software

A professional offline speech-to-text application using OpenAI's Whisper model.

## Features

- Real-time microphone recording
- Process audio files (WAV, MP3, etc.)
- User friendly GUI interface
- Command line interface (CLI)
- Multiple language support
- Save transcriptions to file
- Runs entirely offline/locally

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (for audio processing)

### Windows FFmpeg Installation
```powershell
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

### Python Dependencies
```powershell
pip install -r requirements.txt
```

## Usage

### GUI Mode (Recommended)
```powershell
python main.py
```

### CLI Mode
```powershell
# Record from microphone
python cli_app.py --mode record --duration 10

# Transcribe audio file
python cli_app.py --mode file --input audio.mp3

# Specify model size (tiny, base, small, medium, large)
python cli_app.py --mode record --model base --duration 5
```

## Model Sizes

| Model  | Parameters | VRAM    | Speed      | Accuracy |
|--------|-----------|---------|------------|----------|
| tiny   | 39 M      | ~1 GB   | Very Fast  | Good     |
| base   | 74 M      | ~1 GB   | Fast       | Better   |
| small  | 244 M     | ~2 GB   | Moderate   | Great    |
| medium | 769 M     | ~5 GB   | Slow       | Excellent|
| large  | 1550 M    | ~10 GB  | Very Slow  | Best     |

## Configuration

Edit `config.py` to customize:
- Default model size
- Audio quality settings
- Output directory
- Language preferences

## Troubleshooting

**PyAudio Installation Issues:**
```powershell
pip install pipwin
pipwin install pyaudio
```

**CUDA/GPU Support:**
- Install PyTorch with CUDA: https://pytorch.org/get-started/locally/

## License

MIT License - Free to use and modify
