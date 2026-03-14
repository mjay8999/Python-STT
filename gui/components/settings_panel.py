import customtkinter as ctk


LANGUAGE_OPTIONS = [
    "auto", "en", "hi", "es", "fr", "de", "it", "pt", "ru", "ja", "zh"
]
MODEL_OPTIONS = ["tiny", "base", "small", "medium", "large"]


class SettingsPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, on_load_model, on_save_settings, on_toggle_hotkey):
        super().__init__(master)
        self.on_load_model = on_load_model
        self.on_save_settings = on_save_settings
        self.on_toggle_hotkey = on_toggle_hotkey

        self.grid_columnconfigure(1, weight=1)

        self._row = 0
        self.model_var = ctk.StringVar(value="base")
        self.language_var = ctk.StringVar(value="auto")
        self.duration_var = ctk.IntVar(value=10)
        self.silence_var = ctk.DoubleVar(value=1.5)
        self.use_vad_var = ctk.BooleanVar(value=True)
        self.save_audio_var = ctk.BooleanVar(value=True)
        self.save_text_var = ctk.BooleanVar(value=True)
        self.auto_paste_var = ctk.BooleanVar(value=True)
        self.hotkey_var = ctk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        self._label("Model")
        self.model_menu = ctk.CTkOptionMenu(self, variable=self.model_var, values=MODEL_OPTIONS)
        self.model_menu.grid(row=self._row, column=1, sticky="ew", padx=8, pady=6)
        self._row += 1

        self._label("Language")
        self.language_menu = ctk.CTkOptionMenu(self, variable=self.language_var, values=LANGUAGE_OPTIONS)
        self.language_menu.grid(row=self._row, column=1, sticky="ew", padx=8, pady=6)
        self._row += 1

        self._label("Max Duration (seconds)")
        self.duration_slider = ctk.CTkSlider(self, from_=5, to=60, number_of_steps=55, command=self._on_duration_slide)
        self.duration_slider.set(self.duration_var.get())
        self.duration_slider.grid(row=self._row, column=1, sticky="ew", padx=8, pady=6)
        self.duration_value = ctk.CTkLabel(self, text=str(self.duration_var.get()))
        self.duration_value.grid(row=self._row, column=2, padx=6)
        self._row += 1

        self._label("Silence Stop (seconds)")
        self.silence_slider = ctk.CTkSlider(self, from_=0.5, to=5.0, number_of_steps=45, command=self._on_silence_slide)
        self.silence_slider.set(self.silence_var.get())
        self.silence_slider.grid(row=self._row, column=1, sticky="ew", padx=8, pady=6)
        self.silence_value = ctk.CTkLabel(self, text=f"{self.silence_var.get():.1f}")
        self.silence_value.grid(row=self._row, column=2, padx=6)
        self._row += 1

        self._label("Use VAD")
        ctk.CTkSwitch(self, text="Enabled", variable=self.use_vad_var).grid(row=self._row, column=1, sticky="w", padx=8, pady=6)
        self._row += 1

        self._label("Save Audio")
        ctk.CTkSwitch(self, text="Enabled", variable=self.save_audio_var).grid(row=self._row, column=1, sticky="w", padx=8, pady=6)
        self._row += 1

        self._label("Save Transcription")
        ctk.CTkSwitch(self, text="Enabled", variable=self.save_text_var).grid(row=self._row, column=1, sticky="w", padx=8, pady=6)
        self._row += 1

        self._label("Auto Paste")
        ctk.CTkSwitch(self, text="Enabled", variable=self.auto_paste_var).grid(row=self._row, column=1, sticky="w", padx=8, pady=6)
        self._row += 1

        self._label("Global Hotkey")
        ctk.CTkSwitch(
            self,
            text="Ctrl+Shift+Space",
            variable=self.hotkey_var,
            command=lambda: self.on_toggle_hotkey(bool(self.hotkey_var.get())),
        ).grid(row=self._row, column=1, sticky="w", padx=8, pady=6)
        self._row += 1

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=self._row, column=0, columnspan=3, sticky="ew", padx=6, pady=(12, 8))

        ctk.CTkButton(actions, text="Load Model", command=lambda: self.on_load_model(self.model_var.get())).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Save Settings", command=lambda: self.on_save_settings(self.get_values())).pack(side="left")

    def _label(self, text: str):
        ctk.CTkLabel(self, text=text).grid(row=self._row, column=0, sticky="w", padx=8, pady=6)

    def _on_duration_slide(self, value: float):
        as_int = int(round(value))
        self.duration_var.set(as_int)
        self.duration_value.configure(text=str(as_int))

    def _on_silence_slide(self, value: float):
        rounded = round(value, 1)
        self.silence_var.set(rounded)
        self.silence_value.configure(text=f"{rounded:.1f}")

    def get_values(self) -> dict:
        return {
            "model": self.model_var.get(),
            "language": self.language_var.get(),
            "duration": self.duration_var.get(),
            "hotkey_silence_duration": self.silence_var.get(),
            "use_webrtc_vad": self.use_vad_var.get(),
            "save_audio": self.save_audio_var.get(),
            "save_transcription": self.save_text_var.get(),
            "auto_paste": self.auto_paste_var.get(),
        }

    def set_values(self, settings: dict):
        self.model_var.set(settings["model"])
        self.language_var.set(settings["language"])
        self.duration_var.set(int(settings["duration"]))
        self.duration_slider.set(int(settings["duration"]))
        self.duration_value.configure(text=str(int(settings["duration"])))
        self.silence_var.set(float(settings["hotkey_silence_duration"]))
        self.silence_slider.set(float(settings["hotkey_silence_duration"]))
        self.silence_value.configure(text=f"{float(settings['hotkey_silence_duration']):.1f}")
        self.use_vad_var.set(bool(settings["use_webrtc_vad"]))
        self.save_audio_var.set(bool(settings["save_audio"]))
        self.save_text_var.set(bool(settings["save_transcription"]))
        self.auto_paste_var.set(bool(settings["auto_paste"]))
        self.hotkey_var.set(bool(settings.get("hotkey_enabled", False)))
