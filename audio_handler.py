"""
Audio Handler Module
Handles microphone recording and audio file processing
"""

import wave
import time
import numpy as np
from pathlib import Path
from datetime import datetime
import os
import threading
import queue


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
        self._stop_event = threading.Event()

    def stop_recording(self):
        """Signal any in-progress VAD recording to stop early."""
        self._stop_event.set()

    def record_audio(self, duration=5, callback=None):
        """
        Record audio from microphone for a fixed duration.

        Args:
            duration: Recording duration in seconds
            callback: Optional callback function for progress updates

        Returns:
            numpy array of audio data
        """
        import sounddevice as sd
        print(f"Recording for {duration} seconds...")

        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32'
        )

        sd.wait()
        print("Recording finished!")

        return audio_data

    def save_audio(self, audio_data, filename=None, output_dir="recordings"):
        """
        Save audio data to WAV file.

        Args:
            audio_data: numpy array of audio data
            filename: Output filename (auto-generated if None)
            output_dir: Directory to save the file

        Returns:
            Path to saved file
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"

        filepath = os.path.join(output_dir, filename)

        # Clip before converting to avoid int16 overflow on hot signals
        audio_clipped = np.clip(audio_data, -1.0, 1.0)
        audio_int16 = np.int16(audio_clipped * 32767)

        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        print(f"Audio saved to: {filepath}")
        return filepath

    def load_audio(self, filepath):
        """
        Load audio file (supports various formats via soundfile).

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
        Get list of available audio input devices.

        Returns:
            List of device information
        """
        import sounddevice as sd
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
        Set the input device for recording.

        Args:
            device_id: Device ID to use
        """
        import sounddevice as sd
        sd.default.device = device_id
        print(f"Set input device to: {sd.query_devices(device_id)['name']}")

    def record_with_vad(self, max_duration=30, silence_duration=1.5,
                        callback=None, use_webrtc=True):
        """
        Record audio with voice activity detection (stops on silence or cancellation).

        Args:
            max_duration: Maximum recording duration in seconds
            silence_duration: Seconds of silence before stopping
            callback: Optional callback function(is_speaking, duration)
            use_webrtc: Use WebRTC VAD (True) or simple energy-based detection (False)

        Returns:
            numpy array of audio data (may be empty if nothing was captured)
        """
        import sounddevice as sd
        from vad import VoiceActivityDetector, SilenceDetector

        print(f"Recording with voice activity detection...")
        print(f"Will stop after {silence_duration}s of silence or {max_duration}s max")

        # Clear any previous stop request
        self._stop_event.clear()

        # Initialize detector
        if use_webrtc:
            vad = VoiceActivityDetector(
                sample_rate=self.sample_rate,
                frame_duration_ms=30,
                aggressiveness=2
            )
            frame_size = vad.frame_size
        else:
            silence_detector = SilenceDetector(
                threshold=0.01,
                silence_duration=silence_duration,
                sample_rate=self.sample_rate
            )
            frame_size = int(self.sample_rate * 0.03)  # 30ms frames

        audio_queue = queue.Queue()
        all_frames = []

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"Audio status: {status}")
            audio_queue.put(indata.copy())

        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32',
            callback=audio_callback,
            blocksize=frame_size
        )

        stream.start()

        try:
            start_time = time.monotonic()
            silence_frames = 0
            speech_started = False
            num_silence_frames = int(silence_duration * self.sample_rate / frame_size)

            while not self._stop_event.is_set():
                # Check max duration using monotonic clock
                elapsed = time.monotonic() - start_time
                if elapsed >= max_duration:
                    print("Maximum duration reached")
                    break

                try:
                    frame = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                all_frames.append(frame)

                if use_webrtc:
                    is_speech = vad.is_speech(frame.flatten())
                else:
                    is_speech = not silence_detector.is_silent(frame.flatten())

                if is_speech:
                    if not speech_started:
                        speech_started = True
                        print("Speech detected! Recording...")
                    silence_frames = 0
                    if callback:
                        callback(True, elapsed)
                else:
                    if speech_started:
                        silence_frames += 1
                        if callback:
                            callback(False, elapsed)

                if speech_started and silence_frames >= num_silence_frames:
                    print(f"Silence detected for {silence_duration}s. Stopping...")
                    break

        finally:
            stream.stop()
            stream.close()

        if all_frames:
            audio_data = np.concatenate(all_frames, axis=0)
            print(f"Recording complete! Duration: {len(audio_data) / self.sample_rate:.2f}s")
            return audio_data

        print("No audio recorded")
        return np.array([], dtype='float32')
