"""
GUI Application for Speech-to-Text
User-friendly interface for recording and transcription
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
from pathlib import Path
import config
from audio_handler import AudioHandler
from stt_engine import STTEngine


class STTApp:
    """Main GUI Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_SIZE)
        
        # Initialize components
        self.audio_handler = AudioHandler(
            sample_rate=config.SAMPLE_RATE,
            channels=config.CHANNELS
        )
        self.stt_engine = STTEngine()
        
        # State variables
        self.is_recording = False
        self.current_audio = None
        self.current_result = None
        
        # Setup UI
        self.setup_ui()
        
        # Load model in background
        self.status_label.config(text="Ready. Click 'Load Model' to begin.")
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Local Speech-to-Text",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Model selection
        ttk.Label(settings_frame, text="Model:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.model_var = tk.StringVar(value=config.DEFAULT_MODEL)
        model_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.model_var,
            values=["tiny", "base", "small", "medium", "large"],
            state="readonly",
            width=15
        )
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Duration selection
        ttk.Label(settings_frame, text="Duration (sec):").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.duration_var = tk.StringVar(value=str(config.DEFAULT_DURATION))
        duration_spin = ttk.Spinbox(
            settings_frame,
            from_=1,
            to=300,
            textvariable=self.duration_var,
            width=10
        )
        duration_spin.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Language selection
        ttk.Label(settings_frame, text="Language:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.language_var = tk.StringVar(value="Auto")
        language_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.language_var,
            values=["Auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh"],
            state="readonly",
            width=15
        )
        language_combo.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Load Model Button
        self.load_model_btn = ttk.Button(
            settings_frame,
            text="Load Model",
            command=self.load_model_thread
        )
        self.load_model_btn.grid(row=1, column=2, columnspan=2, padx=5)
        
        # Control Frame
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Record Button
        self.record_btn = ttk.Button(
            control_frame,
            text="🎤 Start Recording",
            command=self.toggle_recording,
            state="disabled"
        )
        self.record_btn.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Transcribe File Button
        self.file_btn = ttk.Button(
            control_frame,
            text="📁 Transcribe File",
            command=self.transcribe_file,
            state="disabled"
        )
        self.file_btn.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Save Button
        self.save_btn = ttk.Button(
            control_frame,
            text="💾 Save Transcription",
            command=self.save_transcription,
            state="disabled"
        )
        self.save_btn.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Clear Button
        clear_btn = ttk.Button(
            control_frame,
            text="🗑️ Clear",
            command=self.clear_output
        )
        clear_btn.grid(row=0, column=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Configure control frame columns
        for i in range(4):
            control_frame.columnconfigure(i, weight=1)
        
        # Status Label
        self.status_label = ttk.Label(
            main_frame,
            text="Initializing...",
            font=("Arial", 10),
            foreground="blue"
        )
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Output Frame
        output_frame = ttk.LabelFrame(main_frame, text="Transcription", padding="10")
        output_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Output Text Area
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Arial", 11)
        )
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def load_model_thread(self):
        """Load model in background thread"""
        self.load_model_btn.config(state="disabled")
        self.status_label.config(text="Loading model... Please wait.", foreground="orange")
        
        def load():
            try:
                # Update engine with selected model
                self.stt_engine.model_name = self.model_var.get()
                self.stt_engine.load_model()
                
                self.root.after(0, self.on_model_loaded)
            except Exception as e:
                self.root.after(0, lambda: self.on_model_error(str(e)))
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def on_model_loaded(self):
        """Called when model is loaded"""
        self.status_label.config(text="Model loaded! Ready to transcribe.", foreground="green")
        self.record_btn.config(state="normal")
        self.file_btn.config(state="normal")
        self.load_model_btn.config(state="normal")
    
    def on_model_error(self, error):
        """Called when model loading fails"""
        self.status_label.config(text=f"Error: {error}", foreground="red")
        self.load_model_btn.config(state="normal")
        messagebox.showerror("Model Error", f"Failed to load model:\n{error}")
    
    def toggle_recording(self):
        """Toggle recording on/off"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio"""
        self.is_recording = True
        self.record_btn.config(text="⏹️ Stop Recording")
        self.file_btn.config(state="disabled")
        self.status_label.config(text="Recording... Speak now!", foreground="red")
        
        duration = int(self.duration_var.get())
        
        def record():
            try:
                audio_data = self.audio_handler.record_audio(duration=duration)
                self.current_audio = audio_data
                
                # Save audio if configured
                if config.SAVE_AUDIO:
                    self.audio_handler.save_audio(
                        audio_data,
                        output_dir=config.RECORDINGS_DIR
                    )
                
                self.root.after(0, self.on_recording_complete)
            except Exception as e:
                self.root.after(0, lambda: self.on_recording_error(str(e)))
        
        thread = threading.Thread(target=record, daemon=True)
        thread.start()
    
    def stop_recording(self):
        """Stop recording (actually just waits for current recording to finish)"""
        self.status_label.config(text="Finishing recording...", foreground="orange")
    
    def on_recording_complete(self):
        """Called when recording is complete"""
        self.is_recording = False
        self.record_btn.config(text="🎤 Start Recording")
        self.file_btn.config(state="normal")
        self.status_label.config(text="Recording complete! Transcribing...", foreground="blue")
        
        # Transcribe immediately
        self.transcribe_audio()
    
    def on_recording_error(self, error):
        """Called when recording fails"""
        self.is_recording = False
        self.record_btn.config(text="🎤 Start Recording")
        self.file_btn.config(state="normal")
        self.status_label.config(text=f"Recording error: {error}", foreground="red")
        messagebox.showerror("Recording Error", f"Failed to record:\n{error}")
    
    def transcribe_audio(self):
        """Transcribe current audio data"""
        if self.current_audio is None:
            return
        
        language = None if self.language_var.get() == "Auto" else self.language_var.get()
        
        def transcribe():
            try:
                result = self.stt_engine.transcribe_audio_data(
                    self.current_audio,
                    sample_rate=config.SAMPLE_RATE,
                    language=language
                )
                self.current_result = result
                self.root.after(0, lambda: self.display_result(result))
            except Exception as e:
                self.root.after(0, lambda: self.on_transcribe_error(str(e)))
        
        thread = threading.Thread(target=transcribe, daemon=True)
        thread.start()
    
    def transcribe_file(self):
        """Transcribe an audio file"""
        filepath = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.m4a *.flac *.ogg"),
                ("All Files", "*.*")
            ]
        )
        
        if not filepath:
            return
        
        self.status_label.config(text="Transcribing file...", foreground="blue")
        self.record_btn.config(state="disabled")
        self.file_btn.config(state="disabled")
        
        language = None if self.language_var.get() == "Auto" else self.language_var.get()
        
        def transcribe():
            try:
                result = self.stt_engine.transcribe_file(
                    filepath,
                    language=language
                )
                self.current_result = result
                self.root.after(0, lambda: self.display_result(result))
                self.root.after(0, lambda: self.on_transcribe_complete())
            except Exception as e:
                self.root.after(0, lambda: self.on_transcribe_error(str(e)))
        
        thread = threading.Thread(target=transcribe, daemon=True)
        thread.start()
    
    def display_result(self, result):
        """Display transcription result"""
        self.output_text.delete(1.0, tk.END)
        
        # Display main text
        self.output_text.insert(tk.END, f"Language: {result['language']}\n\n", "header")
        self.output_text.insert(tk.END, result['text'] + "\n\n")
        
        # Display segments if available
        if result['segments']:
            self.output_text.insert(tk.END, "─" * 50 + "\n", "separator")
            self.output_text.insert(tk.END, "Timestamped Segments:\n\n", "header")
            
            for segment in result['segments']:
                start = self.format_time(segment['start'])
                end = self.format_time(segment['end'])
                self.output_text.insert(tk.END, f"[{start} -> {end}] ", "timestamp")
                self.output_text.insert(tk.END, f"{segment['text']}\n")
        
        # Configure tags
        self.output_text.tag_config("header", font=("Arial", 11, "bold"))
        self.output_text.tag_config("timestamp", foreground="blue")
        self.output_text.tag_config("separator", foreground="gray")
        
        self.save_btn.config(state="normal")
    
    def on_transcribe_complete(self):
        """Called when transcription is complete"""
        self.status_label.config(text="Transcription complete!", foreground="green")
        self.record_btn.config(state="normal")
        self.file_btn.config(state="normal")
    
    def on_transcribe_error(self, error):
        """Called when transcription fails"""
        self.status_label.config(text=f"Transcription error: {error}", foreground="red")
        self.record_btn.config(state="normal")
        self.file_btn.config(state="normal")
        messagebox.showerror("Transcription Error", f"Failed to transcribe:\n{error}")
    
    def save_transcription(self):
        """Save transcription to file"""
        if self.current_result is None:
            messagebox.showwarning("No Transcription", "Nothing to save!")
            return
        
        try:
            filepath = self.stt_engine.save_transcription(self.current_result)
            messagebox.showinfo("Saved", f"Transcription saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save:\n{e}")
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.delete(1.0, tk.END)
        self.current_result = None
        self.save_btn.config(state="disabled")
        self.status_label.config(text="Output cleared.", foreground="blue")
    
    def format_time(self, seconds):
        """Format seconds to MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


def main():
    """Main entry point for GUI application"""
    root = tk.Tk()
    app = STTApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
