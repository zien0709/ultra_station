import customtkinter as ctk
from theme import ThemeConfig

class TabAI:
    def __init__(self, parent, app):
        self.app = app
        self._build(parent)
        
    def _build(self, parent):
        ctk.CTkLabel(parent, text="✨ AI 魔法引擎 (尚未掛載)", font=ThemeConfig.FONT_TITLE_LARGE, text_color=ThemeConfig.COLOR_ACCENT).pack(pady=(30, 10))
        ctk.CTkLabel(parent, text="準備支援：\n- Demucs v4 音軌分離 (人聲/伴奏)\n- Whisper 字幕自動生成\n- Rembg 背景去除", 
                     font=ThemeConfig.FONT_BODY, text_color=self.app.text_body_color, justify="left").pack(pady=10)
        btn_download_ai = ctk.CTkButton(parent, text="雲端下載 AI 模型 (開發中...)", font=ThemeConfig.FONT_BODY, state="disabled", fg_color=ThemeConfig.COLOR_INACTIVE)
        btn_download_ai.pack(pady=20)