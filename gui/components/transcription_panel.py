from datetime import datetime

import customtkinter as ctk


class TranscriptionPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2)
        self.grid_rowconfigure(3, weight=1)

        self.title = ctk.CTkLabel(self, text="Current Transcription", font=ctk.CTkFont(size=16, weight="bold"))
        self.title.grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")

        self.current_text = ctk.CTkTextbox(self, height=220)
        self.current_text.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="nsew")

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="ew")

        self.copy_button = ctk.CTkButton(button_row, text="Copy", width=120, command=self.copy_current_text)
        self.copy_button.pack(side="left", padx=(0, 8))

        self.clear_button = ctk.CTkButton(button_row, text="Clear", width=120, command=self.clear)
        self.clear_button.pack(side="left")

        self.history_title = ctk.CTkLabel(self, text="History", font=ctk.CTkFont(size=15, weight="bold"))
        self.history_title.grid(row=3, column=0, padx=10, pady=(0, 4), sticky="w")

        self.history_text = ctk.CTkTextbox(self, height=180)
        self.history_text.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def set_current_result(self, text: str, language: str, source: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.current_text.delete("1.0", "end")
        self.current_text.insert("1.0", text.strip() or "(No speech detected)")

        history_entry = (
            f"[{timestamp}] {source} | lang={language}\n"
            f"{text.strip() or '(No speech detected)'}\n"
            f"{'-' * 50}\n"
        )
        self.history_text.insert("1.0", history_entry)

    def get_current_text(self) -> str:
        return self.current_text.get("1.0", "end").strip()

    def copy_current_text(self):
        text = self.get_current_text()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)

    def clear(self):
        self.current_text.delete("1.0", "end")
        self.history_text.delete("1.0", "end")
