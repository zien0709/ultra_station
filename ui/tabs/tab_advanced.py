import customtkinter as ctk
from theme import ThemeConfig

class TabAdvanced:
    def __init__(self, parent, app):
        self.app = app
        self._build(parent)
        
    def _build(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        card_audio = ctk.CTkFrame(scroll, **self.app.card_kwargs)
        card_audio.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(card_audio, text="聲學與重採樣設定", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", padx=15, pady=10)
        self.cbo_sr = ctk.CTkComboBox(card_audio, font=ThemeConfig.FONT_BODY, values=["保留原始", "44100 Hz", "48000 Hz", "96000 Hz"])
        self.cbo_sr.pack(fill="x", padx=15, pady=(0, 5))
        self.cbo_ch = ctk.CTkComboBox(card_audio, font=ThemeConfig.FONT_BODY, values=["保留原始", "Mono (單聲道)", "Stereo (雙聲道)"])
        self.cbo_ch.pack(fill="x", padx=15, pady=5)
        self.cbo_br = ctk.CTkComboBox(card_audio, font=ThemeConfig.FONT_BODY, values=["192k", "256k", "320k"])
        self.cbo_br.pack(fill="x", padx=15, pady=(5, 10))

        card_dsp = ctk.CTkFrame(scroll, **self.app.card_kwargs)
        card_dsp.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_dsp, text="訊號優化與增益 (DSP)", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", padx=15, pady=10)
        self.sw_norm = ctk.CTkSwitch(card_dsp, text="自動標準化", font=ThemeConfig.FONT_BODY)
        self.sw_norm.pack(anchor="w", padx=15, pady=5)
        self.sw_denoise = ctk.CTkSwitch(card_dsp, text="FFmpeg 基礎降噪", font=ThemeConfig.FONT_BODY)
        self.sw_denoise.pack(anchor="w", padx=15, pady=5)
        ctk.CTkLabel(card_dsp, text="精細音量增益:", font=ThemeConfig.FONT_BODY).pack(anchor="w", padx=15, pady=(5, 0))
        self.vol_slider = ctk.CTkSlider(card_dsp, from_=0.2, to=2.5, number_of_steps=23); self.vol_slider.set(1.0)
        self.vol_slider.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(card_dsp, text="播放變速調整:", font=ThemeConfig.FONT_BODY).pack(anchor="w", padx=15, pady=(5, 0))
        self.speed_slider = ctk.CTkSlider(card_dsp, from_=0.5, to=2.0, number_of_steps=15); self.speed_slider.set(1.0)
        self.speed_slider.pack(fill="x", padx=15, pady=(5, 10))

        card_trim = ctk.CTkFrame(scroll, **self.app.card_kwargs)
        card_trim.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_trim, text="時間剪輯 (Trim)", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", padx=15, pady=10)
        self.sw_trim = ctk.CTkSwitch(card_trim, text="啟用裁剪", font=ThemeConfig.FONT_BODY)
        self.sw_trim.pack(anchor="w", padx=15, pady=5)
        frame_time = ctk.CTkFrame(card_trim, fg_color="transparent")
        frame_time.pack(fill="x", padx=15, pady=8)
        self.ent_start = ctk.CTkEntry(frame_time, placeholder_text="起始 (如 00:05)", font=ThemeConfig.FONT_BODY)
        self.ent_start.pack(side="left", expand=True, padx=(0, 2))
        self.ent_end = ctk.CTkEntry(frame_time, placeholder_text="結束 (如 00:30)", font=ThemeConfig.FONT_BODY)
        self.ent_end.pack(side="right", expand=True, padx=(2, 0))

        card_meta = ctk.CTkFrame(scroll, **self.app.card_kwargs)
        card_meta.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_meta, text="ID3 標籤編輯", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", padx=15, pady=10)
        self.meta_title = ctk.CTkEntry(card_meta, placeholder_text="歌曲標題 (Title)", font=ThemeConfig.FONT_BODY)
        self.meta_title.pack(fill="x", padx=15, pady=4)
        self.meta_artist = ctk.CTkEntry(card_meta, placeholder_text="演出者 (Artist)", font=ThemeConfig.FONT_BODY)
        self.meta_artist.pack(fill="x", padx=15, pady=4)
        self.meta_album = ctk.CTkEntry(card_meta, placeholder_text="專輯名稱 (Album)", font=ThemeConfig.FONT_BODY)
        self.meta_album.pack(fill="x", padx=15, pady=4)