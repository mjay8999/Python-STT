# Installation Guide

## Quick Start

### 1. Install Python
- Download Python 3.8+ from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### 2. Install FFmpeg

**Option A: Using Chocolatey (Recommended for Windows)**
```powershell
# Install Chocolatey first (if not installed)
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Then install FFmpeg
choco install ffmpeg
```

**Option B: Manual Installation**
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to system PATH

### 3. Run Setup
```powershell
cd d:\proj\STT
python setup.py
```

This will:
- Check Python version
- Check FFmpeg installation
- Install all Python dependencies
- Create necessary directories

### 4. Launch the Application

**GUI Mode (Recommended):**
```powershell
python main.py
```
Or double-click `run_gui.bat`

**CLI Mode:**
```powershell
python cli_app.py --mode record --duration 10
```

## Manual Installation

If the setup script doesn't work, install dependencies manually:

```powershell
# Install core dependencies
pip install openai-whisper
pip install sounddevice numpy

# Install PyAudio (Windows)
pip install pipwin
pipwin install pyaudio

# Optional: Install with GPU support
# Visit https://pytorch.org/get-started/locally/ for CUDA installation
```

## Troubleshooting

### PyAudio Installation Issues
```powershell
# Try pipwin method
pip install pipwin
pipwin install pyaudio

# Or download wheel from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl
```

### FFmpeg Not Found
- Verify installation: `ffmpeg -version`
- Check PATH environment variable
- Restart terminal after installation

### CUDA/GPU Issues
- Install NVIDIA drivers
- Install CUDA Toolkit
- Install PyTorch with CUDA support:
  ```powershell
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```

### Model Download Issues
- First run downloads model (~150MB - 3GB depending on model)
- Requires stable internet connection
- Models cached in `~/.cache/whisper/`

## System Requirements

### Minimum
- CPU: Intel i5 or AMD Ryzen 5
- RAM: 8 GB
- Storage: 5 GB free
- OS: Windows 10/11, Linux, macOS

### Recommended
- CPU: Intel i7 or AMD Ryzen 7
- RAM: 16 GB
- GPU: NVIDIA RTX 2060 or better with 6GB+ VRAM
- Storage: 10 GB free SSD

## First Run

1. Launch the application
2. Click "Load Model" 
3. Wait for model download (first time only)
4. Start using the application!

## Model Selection Guide

| Model  | Size   | Speed      | Accuracy | Use Case               |
|--------|--------|------------|----------|------------------------|
| tiny   | ~40MB  | Very Fast  | Good     | Quick tests, real-time |
| base   | ~75MB  | Fast       | Better   | General use, balanced  |
| small  | ~250MB | Moderate   | Great    | High quality on CPU    |
| medium | ~770MB | Slow       | Excellent| Professional use       |
| large  | ~1.5GB | Very Slow  | Best     | Maximum accuracy       |

Start with `base` model for testing, then upgrade based on your needs.
