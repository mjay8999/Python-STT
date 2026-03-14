"""
Hotkey Listener Module
Handles global keyboard shortcuts for triggering STT
"""

import threading
from typing import Callable, Optional


class HotkeyListener:
    """Global hotkey listener for triggering speech-to-text"""
    
    def __init__(self, hotkey="ctrl+shift+space", callback=None):
        """
        Initialize hotkey listener
        
        Args:
            hotkey: Hotkey combination (e.g., 'ctrl+shift+space')
            callback: Function to call when hotkey is pressed
        """
        self.hotkey = hotkey
        self.callback = callback
        self.is_listening = False
        self.is_recording = False
        self._lock = threading.Lock()
        
    def set_callback(self, callback: Callable):
        """Set the callback function"""
        self.callback = callback
    
    def on_hotkey_press(self):
        """Called when hotkey is pressed.

        Dispatches the callback to a background thread so the keyboard
        library's internal thread is never blocked by a long recording.
        A second press while recording is already in progress is ignored.
        """
        with self._lock:
            if self.is_recording or not self.callback:
                return
            self.is_recording = True

        def _run():
            try:
                self.callback()
            finally:
                with self._lock:
                    self.is_recording = False

        threading.Thread(target=_run, daemon=True).start()
    
    def start(self):
        """Start listening for hotkey"""
        import keyboard
        if self.is_listening:
            print("Hotkey listener already running")
            return
        
        try:
            keyboard.add_hotkey(self.hotkey, self.on_hotkey_press)
            self.is_listening = True
            print(f"Hotkey listener started. Press '{self.hotkey}' to start/stop recording.")
        except Exception as e:
            print(f"Error starting hotkey listener: {e}")
            print("Note: This may require administrator privileges on Windows.")
    
    def stop(self):
        """Stop listening for hotkey"""
        import keyboard
        if not self.is_listening:
            return
        
        try:
            keyboard.remove_hotkey(self.hotkey)
            self.is_listening = False
            print("Hotkey listener stopped")
        except Exception as e:
            print(f"Error stopping hotkey listener: {e}")
    
    def wait(self):
        """Block until listener is stopped"""
        import keyboard
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            self.stop()
    
    def change_hotkey(self, new_hotkey: str):
        """
        Change the hotkey combination
        
        Args:
            new_hotkey: New hotkey combination
        """
        was_listening = self.is_listening
        
        if was_listening:
            self.stop()
        
        self.hotkey = new_hotkey
        
        if was_listening:
            self.start()
        
        print(f"Hotkey changed to: {new_hotkey}")


class ClipboardManager:
    """Manages clipboard operations for pasting transcriptions"""
    
    @staticmethod
    def copy_to_clipboard(text: str):
        """
        Copy text to clipboard
        
        Args:
            text: Text to copy
        """
        import pyperclip
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False
    
    @staticmethod
    def paste_text(text: str, auto_paste: bool = True):
        """
        Copy text to clipboard and optionally paste it
        
        Args:
            text: Text to paste
            auto_paste: If True, simulate Ctrl+V to paste
            
        Returns:
            Boolean indicating success
        """
        import keyboard
        import pyperclip
        import time
        
        try:
            # Copy to clipboard
            pyperclip.copy(text)
            
            if auto_paste:
                # Small delay to ensure clipboard is updated
                time.sleep(0.1)
                
                # Simulate Ctrl+V
                keyboard.press_and_release('ctrl+v')
                
            return True
        except Exception as e:
            print(f"Error pasting text: {e}")
            return False
    
    @staticmethod
    def get_clipboard_text() -> Optional[str]:
        """
        Get current clipboard text
        
        Returns:
            Clipboard text or None
        """
        import pyperclip
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"Error getting clipboard text: {e}")
            return None
