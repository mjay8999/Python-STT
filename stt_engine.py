"""
Speech-to-Text Engine Module
Handles model loading and transcription using Whisper
"""

import whisper
from pathlib import Path
import config
import os
from datetime import datetime
import torch


class STTEngine:
    """Speech-to-Text Engine using OpenAI Whisper"""
    
    def __init__(self, model_name=None, device=None, compute_type=None):
        """
        Initialize STT Engine
        
        Args:
            model_name: Model size (tiny, base, small, medium, large)
            device: Device to run on (auto, cpu, cuda)
            compute_type: Computation type (float16, int8, float32)
        """
        self.model_name = model_name or config.DEFAULT_MODEL
        self.device = device or config.MODEL_DEVICE
        self.compute_type = compute_type or config.COMPUTE_TYPE
        self.model = None
        
        print(f"Initializing STT Engine with model: {self.model_name}")
        
    def load_model(self):
        """Load the Whisper model"""
        if self.model is not None:
            print("Model already loaded")
            return
        
        print(f"Loading {self.model_name} model...")
        print("This may take a few minutes on first run (downloading model)...")
        
        try:
            # Determine device
            if self.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device
            
            # Load model
            self.model = whisper.load_model(
                self.model_name,
                device=device,
                download_root=config.MODEL_CACHE_DIR
            )
            
            print(f"Model loaded successfully on {device}!")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def transcribe_file(self, audio_path, language=None, task=None):
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es') or None for auto-detect
            task: 'transcribe' or 'translate' (to English)
            
        Returns:
            Dictionary with transcription results
        """
        if self.model is None:
            self.load_model()
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        language = language or config.DEFAULT_LANGUAGE
        task = task or config.TASK
        
        print(f"\nTranscribing: {audio_path}")
        print(f"Language: {language or 'auto-detect'}")
        print(f"Task: {task}")
        
        try:
            # Transcribe
            result = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                beam_size=config.BEAM_SIZE,
                condition_on_previous_text=config.CONDITION_ON_PREVIOUS_TEXT,
                verbose=False
            )
            
            return self._process_result(result)
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            raise
    
    def transcribe_audio_data(self, audio_data, sample_rate=16000, language=None, task=None):
        """
        Transcribe audio from numpy array
        
        Args:
            audio_data: numpy array of audio samples
            sample_rate: Sample rate of audio
            language: Language code or None for auto-detect
            task: 'transcribe' or 'translate'
            
        Returns:
            Dictionary with transcription results
        """
        if self.model is None:
            self.load_model()
        
        language = language or config.DEFAULT_LANGUAGE
        task = task or config.TASK
        
        print(f"\nTranscribing audio data...")
        
        try:
            # Whisper expects audio at 16kHz, flatten if needed
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()
            
            # Normalize audio to float32 in range [-1, 1]
            if audio_data.dtype == 'int16':
                audio_data = audio_data.astype('float32') / 32768.0
            
            # Resample if needed (Whisper internally handles this but we can help)
            # Note: Whisper will handle resampling internally
            
            result = self.model.transcribe(
                audio_data,
                language=language,
                task=task,
                beam_size=config.BEAM_SIZE,
                condition_on_previous_text=config.CONDITION_ON_PREVIOUS_TEXT,
                verbose=False
            )
            
            return self._process_result(result)
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            raise
    
    def _process_result(self, result):
        """
        Process and format transcription result
        
        Args:
            result: Raw result from Whisper
            
        Returns:
            Formatted result dictionary
        """
        processed = {
            'text': result['text'].strip(),
            'language': result.get('language', 'unknown'),
            'segments': []
        }
        
        # Process segments with timestamps
        for segment in result.get('segments', []):
            processed['segments'].append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip()
            })
        
        return processed
    
    def save_transcription(self, result, filename=None, output_dir=None):
        """
        Save transcription to text file
        
        Args:
            result: Transcription result dictionary
            filename: Output filename (auto-generated if None)
            output_dir: Directory to save file
            
        Returns:
            Path to saved file
        """
        output_dir = output_dir or config.OUTPUT_DIR
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcription_{timestamp}.txt"
        
        filepath = os.path.join(output_dir, filename)
        
        # Write transcription
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Language: {result['language']}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(result['text'] + "\n\n")
            
            # Write segments with timestamps
            if result['segments']:
                f.write("=" * 50 + "\n")
                f.write("Detailed Segments:\n")
                f.write("=" * 50 + "\n\n")
                
                for segment in result['segments']:
                    start_time = self._format_timestamp(segment['start'])
                    end_time = self._format_timestamp(segment['end'])
                    f.write(f"[{start_time} -> {end_time}]\n")
                    f.write(f"{segment['text']}\n\n")
        
        print(f"Transcription saved to: {filepath}")
        return filepath
    
    def _format_timestamp(self, seconds):
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def get_available_models(self):
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large"]
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            del self.model
            self.model = None
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            print("Model unloaded")
