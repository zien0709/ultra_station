import customtkinter as ctk
from theme import ThemeConfig

class TabBasic:
    def __init__(self, parent, app):
        self.app = app
        self._build(parent)
        
    def _build(self, parent):
        card_fmt = ctk.CTkFrame(parent, fg_color="transparent")
        card_fmt.pack(fill="x", pady=10, padx=15)
        ctk.CTkLabel(card_fmt, text="音訊目標格式選擇 (可複選)", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", pady=(0, 10))
        
        self.fmt_mp3 = ctk.CTkCheckBox(card_fmt, text="轉換為 MP3", font=ThemeConfig.FONT_BODY, text_color=self.app.text_body_color)
        self.fmt_mp3.select()
        self.fmt_mp3.pack(anchor="w", pady=6)
        
        self.fmt_wav = ctk.CTkCheckBox(card_fmt, text="轉換為 WAV", font=ThemeConfig.FONT_BODY, text_color=self.app.text_body_color)
        self.fmt_wav.pack(anchor="w", pady=6)
        
        self.fmt_m4a = ctk.CTkCheckBox(card_fmt, text="轉換為 M4A", font=ThemeConfig.FONT_BODY, text_color=self.app.text_body_color)
        self.fmt_m4a.pack(anchor="w", pady=6)
        
        ctk.CTkLabel(card_fmt, text="影片目標格式 (即將開放)", font=ThemeConfig.FONT_TITLE_CARD, text_color=ThemeConfig.COLOR_INACTIVE).pack(anchor="w", pady=(20, 10))
        ctk.CTkCheckBox(card_fmt, text="轉換為 MP4 (H.264)", font=ThemeConfig.FONT_BODY, state="disabled").pack(anchor="w", pady=6)