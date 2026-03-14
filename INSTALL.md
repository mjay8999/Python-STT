# Installation Guide (Python GUI)

## 1) Install prerequisites

- Python 3.12+
- FFmpeg in PATH

### FFmpeg on Windows (Chocolatey)

```powershell
choco install ffmpeg
```

Verify:

```powershell
ffmpeg -version
```

## 2) Install Python dependencies

```powershell
cd d:\proj\STT
pip install -r requirements.txt
```

## 3) Run setup helper (optional)

```powershell
python setup.py
```

## 4) Launch app

```powershell
run_desktop_app.bat
```

or:

```powershell
python main.py
```

## First run notes

- First model load downloads Whisper model files.
- Keep internet enabled for first download only.
- After download, transcription runs offline.

## Troubleshooting

### Hotkey not triggering
- Run terminal/app as Administrator.
- Ensure model is loaded before enabling hotkey.

### Microphone issues
- Check Windows privacy mic permissions.
- Verify input device availability.

### Slow transcription
- Use `tiny` or `base` model for speed.
- Use GPU-enabled PyTorch for faster inference.
