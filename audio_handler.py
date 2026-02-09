"""
Audio Handler Module
Handles microphone recording and audio file processing
"""

import wave
import sounddevice as sd
import numpy as np
from pathlib import Path
from datetime import datetime
import os


class AudioHandler:
    """Handles audio recording and file operations"""
    
    def __init__(self, sample_rate=16000, channels=1):
        """
        Initialize audio handler
        
        Args:
            sample_rate: Audio sample rate in Hz (16000 is optimal for Whisper)
            channels: Number of audio channels (1 for mono, 2 for stereo)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = []
        
    def record_audio(self, duration=5, callback=None):
        """
        Record audio from microphone
        
        Args:
            duration: Recording duration in seconds
            callback: Optional callback function for progress updates
            
        Returns:
            numpy array of audio data
        """
        print(f"Recording for {duration} seconds...")
        
        # Record audio
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32'
        )
        
        sd.wait()  # Wait until recording is finished
        print("Recording finished!")
        
        return audio_data
    
    def save_audio(self, audio_data, filename=None, output_dir="recordings"):
        """
        Save audio data to WAV file
        
        Args:
            audio_data: numpy array of audio data
            filename: Output filename (auto-generated if None)
            output_dir: Directory to save the file
            
        Returns:
            Path to saved file
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
        
        filepath = os.path.join(output_dir, filename)
        
        # Convert float32 to int16
        audio_int16 = np.int16(audio_data * 32767)
        
        # Save as WAV file
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        print(f"Audio saved to: {filepath}")
        return filepath
    
    def load_audio(self, filepath):
        """
        Load audio file (supports various formats via soundfile)
        
        Args:
            filepath: Path to audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        import soundfile as sf
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")
        
        audio_data, sr = sf.read(filepath)
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        print(f"Loaded audio file: {filepath}")
        print(f"Duration: {len(audio_data) / sr:.2f} seconds")
        
        return audio_data, sr
    
    def get_available_devices(self):
        """
        Get list of available audio input devices
        
        Returns:
            List of device information
        """
        devices = sd.query_devices()
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        
        return input_devices
    
    def set_device(self, device_id):
        """
        Set the input device for recording
        
        Args:
            device_id: Device ID to use
        """
        sd.default.device = device_id
        print(f"Set input device to: {sd.query_devices(device_id)['name']}")
