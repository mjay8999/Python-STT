import customtkinter as ctk


class RecordingPanel(ctk.CTkFrame):
    def __init__(self, master, on_record, on_stop, on_transcribe_file):
        super().__init__(master)
        self.on_record = on_record
        self.on_stop = on_stop
        self.on_transcribe_file = on_transcribe_file

        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.record_button = ctk.CTkButton(self, text="Start Recording", command=self.on_record, height=40)
        self.record_button.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self.stop_button = ctk.CTkButton(self, text="Stop", command=self.on_stop, height=40)
        self.stop_button.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        self.file_button = ctk.CTkButton(self, text="Transcribe File", command=self.on_transcribe_file, height=40)
        self.file_button.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

        self.hint = ctk.CTkLabel(
            self,
            text="Tip: VAD mode auto-stops when silence is detected.",
            text_color="gray70",
            anchor="w",
        )
        self.hint.grid(row=1, column=0, columnspan=3, padx=8, pady=(4, 8), sticky="ew")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.record_button.configure(state=state)
        self.file_button.configure(state=state)
