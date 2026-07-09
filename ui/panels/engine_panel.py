import tkinter as tk
import customtkinter as ctk
from theme import ThemeConfig

class EnginePanel:
    def __init__(self, parent, app):
        self.app = app
        self.card = ctk.CTkFrame(parent, **self.app.card_kwargs)
        self._build()
        
    def _build(self):
        self.lbl_progress = ctk.CTkLabel(self.card, text="工作站閒置中...", font=ThemeConfig.FONT_BODY, text_color=ThemeConfig.COLOR_INACTIVE)
        self.lbl_progress.pack(anchor="w", padx=15, pady=2)
        
        self.progress_bar = ctk.CTkProgressBar(self.card, orientation="horizontal", mode="determinate", progress_color=ThemeConfig.COLOR_ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=15, pady=2)

        self.txt_log = ctk.CTkTextbox(self.card, font=ThemeConfig.FONT_CODE, fg_color=("#f8fafc", "#0d0f16"), text_color=("#059669", "#22c55e"))
        self.txt_log.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        btn_action_frame = ctk.CTkFrame(self.app.right_panel, fg_color="transparent")
        btn_action_frame.grid(row=3, column=0, sticky="ew", pady=5)
        btn_action_frame.grid_columnconfigure(0, weight=7)
        btn_action_frame.grid_columnconfigure(1, weight=3)
        
        self.btn_launch = ctk.CTkButton(btn_action_frame, text="🚀 啟動引擎", font=ThemeConfig.FONT_TITLE_LARGE, height=45, fg_color=ThemeConfig.COLOR_SUCCESS, hover_color="#059669", command=self.app.launch_workflow_thread)
        self.btn_launch.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.btn_cancel = ctk.CTkButton(btn_action_frame, text="🛑 終止", font=ThemeConfig.FONT_TITLE_LARGE, height=45, fg_color=ThemeConfig.COLOR_INACTIVE, hover_color=ThemeConfig.COLOR_DANGER, state="disabled", command=self.app.request_cancel)
        self.btn_cancel.grid(row=0, column=1, sticky="ew")

    def log_message(self, txt):
        self.app.root.after(0, self._sync_log_message, txt)

    def _sync_log_message(self, txt):
        self.txt_log.insert(tk.END, txt)
        self.txt_log.see(tk.END)