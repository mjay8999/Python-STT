import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.label = ctk.CTkLabel(self, text="Ready")
        self.label.pack(side="left", padx=12, pady=8)

    def set_status(self, message: str):
        self.label.configure(text=message)
