"""
Voice Activity Detection Module
Detects when user stops speaking to automatically end recording
"""

import webrtcvad
import numpy as np
import collections


class VoiceActivityDetector:
    """Detects voice activity in audio stream"""
    
    def __init__(self, sample_rate=16000, frame_duration_ms=30, aggressiveness=2):
        """
        Initialize VAD
        
        Args:
            sample_rate: Audio sample rate (must be 8000, 16000, 32000, or 48000)
            frame_duration_ms: Duration of each frame in ms (10, 20, or 30)
            aggressiveness: VAD aggressiveness (0-3, higher = more aggressive filtering)
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        # Initialize WebRTC VAD
        self.vad = webrtcvad.Vad(aggressiveness)
        
    def is_speech(self, audio_frame):
        """
        Check if audio frame contains speech
        
        Args:
            audio_frame: numpy array of audio samples (float32)
            
        Returns:
            Boolean indicating if speech is detected
        """
        # Convert float32 to int16
        if audio_frame.dtype == np.float32:
            audio_int16 = np.int16(audio_frame * 32767)
        else:
            audio_int16 = audio_frame
        
        # VAD expects bytes
        audio_bytes = audio_int16.tobytes()
        
        try:
            return self.vad.is_speech(audio_bytes, self.sample_rate)
        except Exception as e:
            print(f"VAD error (frame size: {len(audio_bytes)} bytes, "
                  f"sample_rate: {self.sample_rate}): {e}")
            return False
    
    def detect_silence_end(self, audio_stream, silence_duration=1.5, 
                          speech_pad_ms=300, buffer_size=50):
        """
        Detect when user stops speaking
        
        Args:
            audio_stream: Generator yielding audio frames
            silence_duration: Seconds of silence before stopping
            speech_pad_ms: Milliseconds to pad before/after speech
            buffer_size: Number of frames to keep in buffer
            
        Yields:
            Audio frames with voice activity detection
        """
        num_silence_frames = int(silence_duration * 1000 / self.frame_duration_ms)
        num_padding_frames = int(speech_pad_ms / self.frame_duration_ms)
        
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False
        voiced_frames = []
        silence_count = 0
        
        for frame in audio_stream:
            is_speech = self.is_speech(frame)
            
            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                
                # Start of speech detected
                if num_voiced > 0.8 * ring_buffer.maxlen:
                    triggered = True
                    # Add buffered frames
                    for f, _ in ring_buffer:
                        voiced_frames.append(f)
                        yield f
                    ring_buffer.clear()
            else:
                # Currently recording speech
                voiced_frames.append(frame)
                yield frame
                
                if is_speech:
                    silence_count = 0
                else:
                    silence_count += 1
                
                # End of speech detected
                if silence_count > num_silence_frames:
                    break
        
        # Return any remaining buffered frames
        for frame in ring_buffer:
            if isinstance(frame, tuple):
                yield frame[0]
            else:
                yield frame


class SilenceDetector:
    """Simple silence detector based on audio energy"""
    
    def __init__(self, threshold=0.01, silence_duration=1.5, sample_rate=16000, 
                 frame_duration_ms=30):
        """
        Initialize silence detector
        
        Args:
            threshold: Energy threshold below which audio is considered silence
            silence_duration: Seconds of silence before stopping
            sample_rate: Audio sample rate
            frame_duration_ms: Duration of each frame in ms
        """
        self.threshold = threshold
        self.silence_duration = silence_duration
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.num_silence_frames = int(silence_duration * 1000 / frame_duration_ms)
        self.silence_count = 0
        
    def is_silent(self, audio_frame):
        """
        Check if audio frame is silent
        
        Args:
            audio_frame: numpy array of audio samples
            
        Returns:
            Boolean indicating if frame is silent
        """
        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_frame ** 2))
        return energy < self.threshold
    
    def reset(self):
        """Reset silence counter"""
        self.silence_count = 0
    
    def check_silence_end(self, audio_frame):
        """
        Check if silence duration threshold has been reached
        
        Args:
            audio_frame: numpy array of audio samples
            
        Returns:
            Boolean indicating if recording should stop
        """
        if self.is_silent(audio_frame):
            self.silence_count += 1
        else:
            self.silence_count = 0
        
        return self.silence_count >= self.num_silence_frames
