import os
import re
import shutil
import zipfile
import subprocess
import threading
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image
from imageio_ffmpeg import get_ffmpeg_exe

# 萬能格式定義
SUPPORTED_EXTENSIONS = (
    '.webm', '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v',
    '.m4a', '.wav', '.flac', '.ogg', '.aac', '.wma', '.mp3'
)

# ----------------------------------------------------
# 【ThemeConfig】全自動現代美學主題設定類別
# ----------------------------------------------------
class ThemeConfig:
    # 專業色彩語意系統
    COLOR_BG_DARK = "#0d0f16"          # 深色模式：深極地藍黑底
    COLOR_BG_LIGHT = "#e2e8f0"         # [優化] 淺色模式：加深質感灰，拉開卡片對比
    
    COLOR_CARD_DARK = "#161922"        # 深色卡片
    COLOR_CARD_LIGHT = "#ffffff"       # 淺色純白卡片

    # [新增] 卡片邊框微陰影層次 (Elevation via Borders)
    COLOR_BORDER_DARK = "#1f2937"      
    COLOR_BORDER_LIGHT = "#cbd5e1"     # 淺灰邊框增建立體浮凸感

    # 拖曳進入時的卡片高亮指示色 (Visual Drag Feedback)
    COLOR_CARD_DRAG_HOVER_DARK = "#202534"
    COLOR_CARD_DRAG_HOVER_LIGHT = "#f1f5f9"
    
    # [新增] 文字色彩階級 (Visual Hierarchy)
    COLOR_TEXT_TITLE_DARK = "#ffffff"
    COLOR_TEXT_TITLE_LIGHT = "#0f172a" # [優化] 淺色標題使用深藍黑，創造聚焦感
    
    COLOR_TEXT_BODY_DARK = "#e2e8f0"
    COLOR_TEXT_BODY_LIGHT = "#1e293b"  # [優化] 淺色內文使用深炭灰，提升閱讀舒適度

    # 狀態對應色彩 (Semantic Colors)
    COLOR_ACCENT = "#2563eb"           # 主色 (寶石藍)
    COLOR_SUCCESS = "#10b981"          # 成功/啟動 (翡翠綠)
    COLOR_DANGER = "#f43f5e"           # 終止/警告 (珊瑚紅)
    COLOR_INACTIVE = "#64748b"         # 閒置/禁用 (鋼鐵灰)

    # 動態波形主題預設色 (Waveform Themes)
    COLOR_WAVE_DARK_FILL = "#00f0ff"       # Dark 模式：螢光藍
    COLOR_WAVE_DARK_FILL_ALT = "#38bdf8"   # 螢光藍中層透光
    COLOR_WAVE_DARK_LINE = "#0284c7"       # 螢光藍邊界

    COLOR_WAVE_LIGHT_FILL = "#4338ca"      # Light 模式：深邃靛色
    COLOR_WAVE_LIGHT_FILL_ALT = "#6366f1"  # 深邃靛中層透光
    COLOR_WAVE_LIGHT_LINE = "#312e81"      # 深邃靛邊界
    
    # 字體層次結構
    FONT_TITLE_LARGE = ("Microsoft JhengHei", 15, "bold")
    FONT_TITLE_CARD = ("Microsoft JhengHei", 13, "bold")
    FONT_BODY = ("Microsoft JhengHei", 11)
    FONT_CODE = ("Consolas", 10)

# 讓 CustomTkinter 與 TkinterDnD 完美相容的雙繼承主視窗
class ModernApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 這是觸發 TkinterDnD 核心機制的必要指令
        self.TkdndVersion = TkinterDnD._require(self)

class UltraAudioStation:
    def __init__(self, root):
        self.root = root
        self.root.title("萬能核心影音處理工作站 v5.6 - 極致立體美學版")
        self.root.geometry("1200x870")
        
        # 初始主題與核心設定
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # 套用視窗基底背景色
        self.root.configure(fg_color=(ThemeConfig.COLOR_BG_LIGHT, ThemeConfig.COLOR_BG_DARK))
        
        try:
            self.ffmpeg_exe = get_ffmpeg_exe()
        except Exception as e:
            messagebox.showerror("核心錯誤", f"找不到系統內建的 FFmpeg 核心：{e}")
            self.root.destroy()
            return

        # 佇列與執行控制核心資料結構
        self.queue_files = []  # 格式: {"src": path, "name": name, "size": size}
        self.output_folder = ""
        self.is_processing = False
        self.cancel_requested = False
        self.current_process = None  # 追蹤當前正在運作的 FFmpeg Popen 進程
        self.waveform_thread = None  # 用於非同步讀取真實音訊波形

        self.setup_ui()
        
        # 註冊拖曳放開事件以及動態視覺反饋事件
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)
        self.root.dnd_bind('<<DragEnter>>', self.handle_drag_enter)
        self.root.dnd_bind('<<DragLeave>>', self.handle_drag_leave)

    def setup_ui(self):
        # 統一卡片美學設定字典 (Card Kwargs)，方便重複套用
        card_kwargs = {
            "corner_radius": 16,
            "fg_color": (ThemeConfig.COLOR_CARD_LIGHT, ThemeConfig.COLOR_CARD_DARK),
            "border_width": 1,
            "border_color": (ThemeConfig.COLOR_BORDER_LIGHT, ThemeConfig.COLOR_BORDER_DARK)
        }
        
        # 統一文字色彩元組
        text_title_color = (ThemeConfig.COLOR_TEXT_TITLE_LIGHT, ThemeConfig.COLOR_TEXT_TITLE_DARK)
        text_body_color = (ThemeConfig.COLOR_TEXT_BODY_LIGHT, ThemeConfig.COLOR_TEXT_BODY_DARK)

        # 配置網格權重，打造靈活自適應佈局
        self.root.grid_columnconfigure(0, weight=4)  # 左側控制卡片區
        self.root.grid_columnconfigure(1, weight=6)  # 右側佇列與波形日誌區
        self.root.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------
        # 【左側控制面板卡片區】
        # ----------------------------------------------------
        self.left_panel = ctk.CTkScrollableFrame(
            self.root, 
            corner_radius=16, 
            fg_color="transparent"
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # 卡片 1：路徑選擇與自動化
        card_io = ctk.CTkFrame(self.left_panel, **card_kwargs)
        card_io.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_io, text="📂 檔案路徑與自動化管理", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(anchor="w", padx=15, pady=10)
        
        # 遞迴掃描勾選
        self.sw_recursive = ctk.CTkSwitch(card_io, text="啟用子資料夾遞迴掃描", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.sw_recursive.pack(anchor="w", padx=20, pady=5)
        
        # 輸出路徑設定
        btn_out = ctk.CTkButton(card_io, text="選擇自訂輸出資料夾", font=ThemeConfig.FONT_BODY, command=self.choose_output_folder, fg_color="#2c3e50", hover_color="#34495e")
        btn_out.pack(fill="x", padx=20, pady=10)
        self.lbl_out_dir = ctk.CTkLabel(card_io, text="預設：輸出至來源相同目錄", font=ThemeConfig.FONT_BODY, text_color=ThemeConfig.COLOR_INACTIVE, wraplength=350)
        self.lbl_out_dir.pack(anchor="w", padx=20, pady=(0, 10))

        # 卡片 2：多重目標格式轉換
        card_fmt = ctk.CTkFrame(self.left_panel, **card_kwargs)
        card_fmt.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_fmt, text="🎛️ 批次多重目標格式選擇 (可複選)", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(anchor="w", padx=15, pady=10)
        
        self.fmt_mp3 = ctk.CTkCheckBox(card_fmt, text="轉換為 MP3", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.fmt_mp3.select()
        self.fmt_mp3.pack(anchor="w", padx=20, pady=6)
        self.fmt_wav = ctk.CTkCheckBox(card_fmt, text="轉換為 WAV", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.fmt_wav.pack(anchor="w", padx=20, pady=6)
        self.fmt_m4a = ctk.CTkCheckBox(card_fmt, text="轉換為 M4A", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.fmt_m4a.pack(anchor="w", padx=20, pady=6)

        # 卡片 3：高級聲學參數設定
        card_audio = ctk.CTkFrame(self.left_panel, **card_kwargs)
        card_audio.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_audio, text="⚙️ 高級聲學與音訊重採樣設定", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(anchor="w", padx=15, pady=10)
        
        # 採樣率 (Sample Rate)
        ctk.CTkLabel(card_audio, text="採樣率 (Sample Rate):", font=ThemeConfig.FONT_BODY, text_color=text_body_color).pack(anchor="w", padx=20, pady=2)
        self.cbo_sr = ctk.CTkComboBox(card_audio, font=ThemeConfig.FONT_BODY, text_color=text_body_color, values=["保留原始", "44100 Hz", "48000 Hz", "96000 Hz"])
        self.cbo_sr.pack(fill="x", padx=20, pady=4)
        
        # 聲道數 (Channels)
        ctk.CTkLabel(card_audio, text="聲道模式 (Channels):", font=ThemeConfig.FONT_BODY, text_color=text_body_color).pack(anchor="w", padx=20, pady=2)
        self.cbo_ch = ctk.CTkComboBox(card_audio, font=ThemeConfig.FONT_BODY, text_color=text_body_color, values=["保留原始", "Mono (單聲道)", "Stereo (雙聲道)"])
        self.cbo_ch.pack(fill="x", padx=20, pady=4)
        
        # 音質位元率
        ctk.CTkLabel(card_audio, text="壓縮位元率 (僅 MP3/M4A 有效):", font=ThemeConfig.FONT_BODY, text_color=text_body_color).pack(anchor="w", padx=20, pady=2)
        self.cbo_br = ctk.CTkComboBox(card_audio, font=ThemeConfig.FONT_BODY, text_color=text_body_color, values=["192k", "256k", "320k"])
        self.cbo_br.pack(fill="x", padx=20, pady=4)

        # 卡片 4：進階DSP訊號處理
        card_dsp = ctk.CTkFrame(self.left_panel, **card_kwargs)
        card_dsp.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_dsp, text="🚀 音訊增益與數位訊號優化 (DSP)", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(anchor="w", padx=15, pady=10)
        
        self.sw_norm = ctk.CTkSwitch(card_dsp, text="啟用音量自動標準化", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.sw_norm.pack(anchor="w", padx=20, pady=5)
        
        self.sw_denoise = ctk.CTkSwitch(card_dsp, text="輕量級智慧動態降噪", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.sw_denoise.pack(anchor="w", padx=20, pady=5)
        
        # 音量滑桿
        ctk.CTkLabel(card_dsp, text="手動精細音量增益調整:", font=ThemeConfig.FONT_BODY, text_color=text_body_color).pack(anchor="w", padx=20, pady=2)
        self.vol_slider = ctk.CTkSlider(card_dsp, from_=0.2, to=2.5, number_of_steps=23)
        self.vol_slider.set(1.0)
        self.vol_slider.pack(fill="x", padx=20, pady=4)
        
        # 速度調整
        ctk.CTkLabel(card_dsp, text="音訊播放變速調整 (Playback Speed):", font=ThemeConfig.FONT_BODY, text_color=text_body_color).pack(anchor="w", padx=20, pady=2)
        self.speed_slider = ctk.CTkSlider(card_dsp, from_=0.5, to=2.0, number_of_steps=15)
        self.speed_slider.set(1.0)
        self.speed_slider.pack(fill="x", padx=20, pady=4)

        # 卡片 5：精密音訊剪輯 (Trim)
        card_trim = ctk.CTkFrame(self.left_panel, **card_kwargs)
        card_trim.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_trim, text="✂️ 精密音訊時間剪輯 (Trim / Cut)", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(anchor="w", padx=15, pady=10)
        
        self.sw_trim = ctk.CTkSwitch(card_trim, text="啟用時間裁剪範圍", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.sw_trim.pack(anchor="w", padx=20, pady=5)
        
        frame_time = ctk.CTkFrame(card_trim, fg_color="transparent")
        frame_time.pack(fill="x", padx=20, pady=8)
        self.ent_start = ctk.CTkEntry(frame_time, placeholder_text="起始 如 00:05", font=ThemeConfig.FONT_BODY, text_color=text_body_color, width=120)
        self.ent_start.pack(side="left", expand=True, padx=2)
        self.ent_end = ctk.CTkEntry(frame_time, placeholder_text="結束 如 00:30", font=ThemeConfig.FONT_BODY, text_color=text_body_color, width=120)
        self.ent_end.pack(side="right", expand=True, padx=2)

        # 卡片 6：元資料標籤注入
        card_meta = ctk.CTkFrame(self.left_panel, **card_kwargs)
        card_meta.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_meta, text="🏷️ 媒體 ID3 標籤編輯 (Metadata Tags)", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(anchor="w", padx=15, pady=10)
        self.meta_title = ctk.CTkEntry(card_meta, placeholder_text="歌曲標題 (Title)", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.meta_title.pack(fill="x", padx=20, pady=4)
        self.meta_artist = ctk.CTkEntry(card_meta, placeholder_text="演出者/歌手 (Artist)", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.meta_artist.pack(fill="x", padx=20, pady=4)
        self.meta_album = ctk.CTkEntry(card_meta, placeholder_text="專輯名稱 (Album)", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.meta_album.pack(fill="x", padx=20, pady=4)

        # 卡片 7：系統自動化出貨選項
        card_export = ctk.CTkFrame(self.left_panel, **card_kwargs)
        card_export.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(card_export, text="📦 任務收尾工作流", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(anchor="w", padx=15, pady=10)
        self.sw_zip = ctk.CTkSwitch(card_export, text="完成後將所有新檔自動封裝為 .zip 檔", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.sw_zip.pack(anchor="w", padx=20, pady=5)
        self.sw_delete = ctk.CTkSwitch(card_export, text="完成後自動銷毀本機原始媒體檔", font=ThemeConfig.FONT_BODY, text_color=text_body_color)
        self.sw_delete.pack(anchor="w", padx=20, pady=5)

        # 亮暗主題切換器
        self.theme_switch = ctk.CTkSegmentedButton(self.left_panel, font=ThemeConfig.FONT_BODY, values=["Dark 模式", "Light 模式"], command=self.toggle_theme)
        self.theme_switch.set("Dark 模式")
        self.theme_switch.pack(fill="x", pady=15, padx=5)


        # ----------------------------------------------------
        # 【右側工作佇列、視覺化與日誌區】
        # ----------------------------------------------------
        self.right_panel = ctk.CTkFrame(self.root, corner_radius=16, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        self.right_panel.grid_rowconfigure(0, weight=4)  # 佇列管理區
        self.right_panel.grid_rowconfigure(1, weight=3)  # 波形圖展示區
        self.right_panel.grid_rowconfigure(2, weight=3)  # 日誌與進度條區
        self.right_panel.grid_columnconfigure(0, weight=1)

        # 區塊 1：動態任務工作佇列管理卡片
        self.queue_card = ctk.CTkFrame(self.right_panel, **card_kwargs)
        self.queue_card.grid(row=0, column=0, sticky="nsew", pady=5)
        
        # 拖曳提示區
        self.drop_lbl = ctk.CTkLabel(self.queue_card, text="✨ 拖曳多個檔案、資料夾、或 ZIP 至此，或使用下方按鈕匯入 ✨", 
                                     font=ThemeConfig.FONT_BODY, text_color=ThemeConfig.COLOR_ACCENT)
        self.drop_lbl.pack(pady=8)

        # 佇列控制與按鈕欄 (整合傳統式檔案/資料夾並行匯入按鈕)
        queue_title_frame = ctk.CTkFrame(self.queue_card, fg_color="transparent")
        queue_title_frame.pack(fill="x", padx=15)
        ctk.CTkLabel(queue_title_frame, text="📋 目前待處理任務佇列清單", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(side="left")
        
        btn_clear = ctk.CTkButton(queue_title_frame, text="清空佇列", font=ThemeConfig.FONT_BODY, width=80, height=26, fg_color=ThemeConfig.COLOR_DANGER, hover_color="#be123c", command=self.clear_queue)
        btn_clear.pack(side="right")

        # 傳統匯入並行控制按鈕欄
        import_btn_frame = ctk.CTkFrame(self.queue_card, fg_color="transparent")
        import_btn_frame.pack(fill="x", padx=15, pady=(5, 0))
        
        self.btn_import_files = ctk.CTkButton(
            import_btn_frame, 
            text="📄 選擇檔案匯入", 
            font=ThemeConfig.FONT_BODY,
            fg_color=ThemeConfig.COLOR_ACCENT, 
            hover_color="#1d4ed8",
            height=28,
            command=self.import_files_dialog
        )
        self.btn_import_files.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.btn_import_folder = ctk.CTkButton(
            import_btn_frame, 
            text="📁 選擇資料夾匯入", 
            font=ThemeConfig.FONT_BODY,
            fg_color="#475569", 
            hover_color="#334155",
            height=28,
            command=self.import_folder_dialog
        )
        self.btn_import_folder.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # 佇列清單框 (原生存取)
        self.queue_box = tk.Listbox(self.queue_card, 
                                    bg="#11131c" if ctk.get_appearance_mode() == "Dark" else "#ffffff", 
                                    fg=ThemeConfig.COLOR_TEXT_BODY_DARK if ctk.get_appearance_mode() == "Dark" else ThemeConfig.COLOR_TEXT_BODY_LIGHT, 
                                    selectbackground=ThemeConfig.COLOR_ACCENT, 
                                    font=ThemeConfig.FONT_CODE, relief="flat", highlightthickness=0, bd=0)
        self.queue_box.pack(fill="both", expand=True, padx=15, pady=10)
        self.queue_box.bind("<<ListboxSelect>>", self.on_queue_select)

        # 區塊 2：動態聲學真實波形預覽卡片
        wave_card = ctk.CTkFrame(self.right_panel, **card_kwargs)
        wave_card.grid(row=1, column=0, sticky="nsew", pady=5)
        ctk.CTkLabel(wave_card, text="📊 聲學實時真實波形預覽 (True Amplitude Preview)", font=ThemeConfig.FONT_TITLE_CARD, text_color=text_title_color).pack(anchor="w", padx=15, pady=6)
        
        # 內嵌 Matplotlib 畫布 - 極簡邊框與完美卡片背景融合
        self.fig, self.ax = plt.subplots(figsize=(5, 1.5), facecolor='#161922')
        self.ax.set_facecolor('#161922')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.plot(np.zeros(100), color=ThemeConfig.COLOR_WAVE_DARK_FILL)  # 預設空波形
        self.ax.axis('off')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=wave_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 10))

        # 區塊 3：自動化執行引擎與現代進度條卡片
        engine_card = ctk.CTkFrame(self.right_panel, **card_kwargs)
        engine_card.grid(row=2, column=0, sticky="nsew", pady=5)
        
        self.lbl_progress = ctk.CTkLabel(engine_card, text="工作站閒置中... 隨時可啟動自動化工作流", font=ThemeConfig.FONT_BODY, text_color=ThemeConfig.COLOR_INACTIVE)
        self.lbl_progress.pack(anchor="w", padx=15, pady=4)
        
        # 動態高科技進度條
        self.progress_bar = ctk.CTkProgressBar(engine_card, orientation="horizontal", mode="determinate", progress_color=ThemeConfig.COLOR_ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=15, pady=4)

        # 實時日誌監控視窗 (獨立的深色終端美學)
        self.txt_log = ctk.CTkTextbox(engine_card, font=ThemeConfig.FONT_CODE, 
                                      fg_color=("#f8fafc", "#0d0f16"), text_color=("#059669", "#22c55e"))
        self.txt_log.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        # 底部操作按鈕欄 (整合啟動與終止按鈕)
        btn_action_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        btn_action_frame.grid(row=3, column=0, sticky="ew", pady=10)
        btn_action_frame.grid_columnconfigure(0, weight=7)
        btn_action_frame.grid_columnconfigure(1, weight=3)

        self.btn_launch = ctk.CTkButton(
            btn_action_frame, 
            text="🚀 啟動多重任務全自動化工作流引擎", 
            font=ThemeConfig.FONT_TITLE_LARGE, 
            height=48, 
            fg_color=ThemeConfig.COLOR_SUCCESS, 
            hover_color="#059669"
        )
        self.btn_launch.configure(command=self.launch_workflow_thread)
        self.btn_launch.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.btn_cancel = ctk.CTkButton(
            btn_action_frame, 
            text="🛑 終止目前任務", 
            font=ThemeConfig.FONT_TITLE_LARGE, 
            height=48, 
            fg_color=ThemeConfig.COLOR_INACTIVE, 
            hover_color=ThemeConfig.COLOR_DANGER, 
            state="disabled", 
            command=self.request_cancel
        )
        self.btn_cancel.grid(row=0, column=1, sticky="ew")

    # ----------------------------------------------------
    # 【拖曳與 UI 視覺互動反饋機制】
    # ----------------------------------------------------
    def handle_drag_enter(self, event):
        # 拖曳物件進入視窗：調整卡片色澤，給予使用者即時就緒回饋
        is_dark = ctk.get_appearance_mode() == "Dark"
        hover_color = ThemeConfig.COLOR_CARD_DRAG_HOVER_DARK if is_dark else ThemeConfig.COLOR_CARD_DRAG_HOVER_LIGHT
        self.queue_card.configure(fg_color=hover_color)

    def handle_drag_leave(self, event):
        # 拖曳物件離開視窗：還原卡片色澤
        is_dark = ctk.get_appearance_mode() == "Dark"
        orig_color = ThemeConfig.COLOR_CARD_DARK if is_dark else ThemeConfig.COLOR_CARD_LIGHT
        self.queue_card.configure(fg_color=orig_color)

    def handle_drop(self, event):
        # 放開拖曳：還原背景色並處理檔案
        self.handle_drag_leave(event)
        
        # 使用 tkinter 原生內建方法解析拖曳路徑，完美處理含有空格及特殊符號之路徑
        paths = self.root.tk.splitlist(event.data)

        for path in paths:
            path = path.strip('"\'') 
            if os.path.isdir(path):
                self.load_directory(path, recursive=self.sw_recursive.get())
            elif path.lower().endswith('.zip'):
                self.load_zip(path)
            elif path.lower().endswith(SUPPORTED_EXTENSIONS):
                self.add_to_queue(path)
        
        self.log_message(f"ℹ️ 拖曳加載完成，目前任務佇列共計 {len(self.queue_files)} 個檔案。\n")

    # ----------------------------------------------------
    # 【傳統按鈕並行匯入對話框控制】
    # ----------------------------------------------------
    def import_files_dialog(self):
        # 多重檔案選擇器
        file_types = [("支援媒體檔案", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)), ("所有檔案", "*.*")]
        files = filedialog.askopenfilenames(title="選擇欲匯入的影音檔案", filetypes=file_types)
        if files:
            for file in files:
                self.add_to_queue(file)
            self.log_message(f"ℹ️ 傳統手動選擇加載完成，目前佇列共計 {len(self.queue_files)} 個檔案。\n")

    def import_folder_dialog(self):
        # 資料夾選擇器
        folder = filedialog.askdirectory(title="選擇欲匯入的資料夾")
        if folder:
            self.load_directory(folder, recursive=self.sw_recursive.get())
            self.log_message(f"ℹ️ 資料夾手動選擇加載完成，目前佇列共計 {len(self.queue_files)} 個檔案。\n")

    # ----------------------------------------------------
    # 【業務邏輯與自動化調度核心】
    # ----------------------------------------------------
    def toggle_theme(self, choice):
        # 即時切換主視覺顏色模式，並同步重新網格繪製與字體色彩
        if choice == "Dark 模式":
            ctk.set_appearance_mode("Dark")
            bg_color = ThemeConfig.COLOR_CARD_DARK
            text_color = ThemeConfig.COLOR_TEXT_BODY_DARK
            self.queue_box.configure(bg="#11131c", fg=text_color)
        else:
            ctk.set_appearance_mode("Light")
            bg_color = ThemeConfig.COLOR_CARD_LIGHT
            text_color = ThemeConfig.COLOR_TEXT_BODY_LIGHT
            self.queue_box.configure(bg="#ffffff", fg=text_color)
            
        self.ax.set_facecolor(bg_color)
        self.fig.set_facecolor(bg_color)
        self.ax.tick_params(colors=text_color)
        
        # 若有選取之佇列檔案，立即重繪波形，套用新模式的專屬色調
        selection = self.queue_box.curselection()
        if selection:
            self.on_queue_select(None)
        else:
            self.canvas.draw()

    def choose_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.lbl_out_dir.configure(text=f"自訂輸出位置: {folder}", text_color=ThemeConfig.COLOR_SUCCESS)

    def load_directory(self, folder, recursive=False):
        if recursive:
            for root_dir, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(SUPPORTED_EXTENSIONS):
                        self.add_to_queue(os.path.join(root_dir, f))
        else:
            for f in os.listdir(folder):
                if f.lower().endswith(SUPPORTED_EXTENSIONS):
                    self.add_to_queue(os.path.join(folder, f))

    def load_zip(self, zip_path):
        self.log_message(f"📦 偵測到 ZIP 壓縮檔：{os.path.basename(zip_path)}，將在啟動時自動進行安全流式解壓。\n")
        self.add_to_queue(zip_path)

    def add_to_queue(self, file_path):
        name = os.path.basename(file_path)
        # 防止重複加入相同路徑的檔案
        if any(item["src"] == file_path for item in self.queue_files):
            return
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.queue_files.append({"src": file_path, "name": name, "size": f"{size_mb:.2f} MB"})
            self.queue_box.insert(tk.END, f"  [{size_mb:.1f}MB]  {name}")
        except Exception as e:
            self.log_message(f"❌ 讀取檔案資訊失敗 {name}: {e}\n")

    def clear_queue(self):
        if self.is_processing:
            messagebox.showwarning("無法清空", "引擎正在自動化任務中，請先終止任務再清空佇列！")
            return
        self.queue_files.clear()
        self.queue_box.delete(0, tk.END)
        self.log_message("🧹 任務工作佇列已完全清空。\n")
        # 清除波形圖
        self.ax.clear()
        self.ax.axis('off')
        self.canvas.draw()

    def on_queue_select(self, event):
        # 當點擊佇列清單檔案時，啟動背景非同步執行緒抽取真實 PCM 取樣並繪圖，保障介面完全不卡頓
        selection = self.queue_box.curselection()
        if not selection:
            return
        
        idx = selection[0]
        file_info = self.queue_files[idx]
        file_path = file_info["src"]

        if file_path.lower().endswith('.zip'):
            self.ax.clear()
            self.ax.text(0.5, 0.5, "📦 ZIP 檔案 (解壓後顯示波形)", color='gray', ha='center', va='center', font=ThemeConfig.FONT_BODY)
            self.ax.axis('off')
            self.canvas.draw()
            return

        # 啟動非同步執行緒讀取波形
        if self.waveform_thread and self.waveform_thread.is_alive():
            pass
            
        self.waveform_thread = threading.Thread(target=self._async_load_waveform, args=(file_path,), daemon=True)
        self.waveform_thread.start()

    def _async_load_waveform(self, file_path):
        # 使用 FFmpeg 解出前 60 秒的 mono (單聲道) 8000Hz s16le PCM，藉此在無聲卡解碼庫的情況下繪製精準波形
        cmd = [
            self.ffmpeg_exe, "-y",
            "-ss", "0", "-t", "60",  # 只讀取前 60 秒
            "-i", file_path,
            "-f", "s16le", "-ac", "1", "-ar", "8000",
            "-"
        ]
        try:
            # 限制讀取的大小以防止超大檔案耗費記憶體 (8000 samples/sec * 2 bytes * 60 sec = 960000 bytes)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            raw_data = proc.stdout.read(960000)
            proc.stdout.close()
            proc.terminate()
            
            if len(raw_data) > 0:
                # 轉成 numpy int16 陣列
                data = np.frombuffer(raw_data, dtype=np.int16)
                # 做輕量級降採樣 (Downsample) 到 300 個點以便Matplotlib快速流暢呈現
                step = max(1, len(data) // 300)
                downsampled = data[::step]
                
                # 安全更新 GUI 繪圖板
                self.root.after(0, self._draw_waveform, downsampled)
            else:
                self.root.after(0, self._draw_empty_waveform, "無法取得音訊流 (無音軌)")
        except Exception:
            self.root.after(0, self._draw_empty_waveform, "波形解碼載入失敗")

    def _draw_waveform(self, y_data):
        self.ax.clear()
        x = np.arange(len(y_data))
        
        is_dark = ctk.get_appearance_mode() == "Dark"
        if is_dark:
            # Dark 螢光藍主題
            fill_color = ThemeConfig.COLOR_WAVE_DARK_FILL
            fill_alt = ThemeConfig.COLOR_WAVE_DARK_FILL_ALT
            line_color = ThemeConfig.COLOR_WAVE_DARK_LINE
            bg_color = ThemeConfig.COLOR_CARD_DARK
        else:
            # Light 深邃靛色主題
            fill_color = ThemeConfig.COLOR_WAVE_LIGHT_FILL
            fill_alt = ThemeConfig.COLOR_WAVE_LIGHT_FILL_ALT
            line_color = ThemeConfig.COLOR_WAVE_LIGHT_LINE
            bg_color = ThemeConfig.COLOR_CARD_LIGHT

        # 視覺美學進化：導入半透明多層疊加漸層效果 (Glow & Wave Depth)
        self.ax.fill_between(x, -y_data, y_data, color=fill_color, alpha=0.35)
        self.ax.fill_between(x, -y_data * 0.6, y_data * 0.6, color=fill_alt, alpha=0.5)
        self.ax.plot(x, y_data, color=line_color, alpha=0.8, linewidth=0.8)
        self.ax.axis('off')
        
        # 配合當前主題的極簡漂浮背景色
        self.ax.set_facecolor(bg_color)
        self.canvas.draw()

    def _draw_empty_waveform(self, msg):
        self.ax.clear()
        self.ax.text(0.5, 0.5, f"⚠️ {msg}", color='gray', ha='center', va='center', font=ThemeConfig.FONT_BODY)
        self.ax.axis('off')
        
        bg_color = ThemeConfig.COLOR_CARD_DARK if ctk.get_appearance_mode() == "Dark" else ThemeConfig.COLOR_CARD_LIGHT
        self.ax.set_facecolor(bg_color)
        self.canvas.draw()

    # 執行緒安全 GUI 日誌調度器
    def log_message(self, txt):
        self.root.after(0, self._sync_log_message, txt)

    def _sync_log_message(self, txt):
        self.txt_log.insert(tk.END, txt)
        self.txt_log.see(tk.END)

    def request_cancel(self):
        if self.is_processing:
            if messagebox.askyesno("終止確認", "確定要中止目前正在運行的所有自動化轉檔任務嗎？"):
                self.cancel_requested = True
                self.log_message("\n🛑 正在接收中止命令... 系統將在下一個安全時間點退出...\n")
                
                # 終止時將進度條顏色與狀態標籤變更為語意紅色 (珊瑚紅)
                self.root.after(0, self.progress_bar.configure, {"progress_color": ThemeConfig.COLOR_DANGER})
                self.root.after(0, self.btn_cancel.configure, {"fg_color": ThemeConfig.COLOR_DANGER})
                
                if self.current_process:
                    try:
                        self.current_process.terminate()  # 安全向當前 FFmpeg 發送終止信號
                        self.log_message("👉 已向核心 FFmpeg 進程發送終止命令...\n")
                    except Exception as e:
                        self.log_message(f"⚠️ 終止 FFmpeg 出錯: {e}\n")

    def launch_workflow_thread(self):
        if self.is_processing:
            messagebox.showwarning("工作站執行中", "引擎正在自動化轉算中，請勿重複啟動！")
            return
        if not self.queue_files:
            messagebox.showwarning("佇列為空", "目前工作佇列中沒有任何檔案，請先拖曳檔案或資料夾進來！")
            return
            
        # 蒐集勾選的輸出格式
        selected_formats = []
        if self.fmt_mp3.get(): selected_formats.append("mp3")
        if self.fmt_wav.get(): selected_formats.append("wav")
        if self.fmt_m4a.get(): selected_formats.append("m4a")
        
        if not selected_formats:
            messagebox.showwarning("設定出錯", "請至少勾選一種批次多重目標輸出格式！")
            return

        # ----------------------------------------------------
        # 在主執行緒中完成「GUI 控制項設定快照 (Snapshot)」
        # ----------------------------------------------------
        gui_snapshot = {
            "recursive": self.sw_recursive.get(),
            "target_formats": selected_formats,
            "sample_rate": self.cbo_sr.get(),
            "channels": self.cbo_ch.get(),
            "bitrate": self.cbo_br.get(),
            "norm": self.sw_norm.get(),
            "denoise": self.sw_denoise.get(),
            "volume": self.vol_slider.get(),
            "speed": self.speed_slider.get(),
            "trim": self.sw_trim.get(),
            "trim_start": self.ent_start.get().strip(),
            "trim_end": self.ent_end.get().strip(),
            "meta_title": self.meta_title.get().strip(),
            "meta_artist": self.meta_artist.get().strip(),
            "meta_album": self.meta_album.get().strip(),
            "zip_after": self.sw_zip.get(),
            "delete_after": self.sw_delete.get(),
            "output_folder": self.output_folder
        }

        # 重置控制參數與進度條樣式
        self.cancel_requested = False
        self.is_processing = True

        # 更新按鈕互動狀態與顏色回饋 (極簡呼吸效果)
        self.progress_bar.configure(progress_color=ThemeConfig.COLOR_ACCENT)
        self.btn_launch.configure(state="disabled", fg_color="gray")
        self.btn_cancel.configure(state="normal", fg_color=ThemeConfig.COLOR_DANGER)
        self.progress_bar.set(0)

        # 啟動背景調度核心，使用 Snapshot 進行數據操作
        threading.Thread(target=self.core_pipeline_engine, args=(gui_snapshot,), daemon=True).start()

    def core_pipeline_engine(self, settings):
        target_formats = settings["target_formats"]
        total_files = len(self.queue_files)
        
        converted_output_files = []  # 用於最終 ZIP 打包

        self.log_message(f"🚀 === 啟動自動化超高速工作流調度，佇列共計 {total_files} 個任務單元 ===\n")

        for f_idx, file_item in enumerate(self.queue_files):
            if self.cancel_requested:
                break

            src = file_item["src"]
            name = file_item["name"]
            
            temp_dir = None
            files_to_process = []
            
            # 是否為 ZIP 處理單元
            is_zip_task = src.lower().endswith('.zip')

            # ----------------------------------------------------
            # ZIP 檔案解壓與路徑防 Slip 漏洞檢查
            # ----------------------------------------------------
            if is_zip_task:
                self.log_message(f"⏳ 正在進行解壓工作流：{name}...\n")
                temp_dir = src + "_extracted_temp"
                os.makedirs(temp_dir, exist_ok=True)
                try:
                    with zipfile.ZipFile(src, 'r') as z_ref:
                        # 檢查並阻止任何含有 Directory Traversal (../) 的路徑
                        for member in z_ref.namelist():
                            filename = os.path.basename(member)
                            if not filename:
                                continue
                            
                            target_path = os.path.abspath(os.path.join(temp_dir, member))
                            if not target_path.startswith(os.path.abspath(temp_dir)):
                                raise Exception(f"偵測到惡意路徑穿越攻擊 (Zip Slip): {member}")
                                
                        z_ref.extractall(temp_dir)
                        
                    for root_d, _, fs in os.walk(temp_dir):
                        for f in fs:
                            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                                files_to_process.append(os.path.join(root_d, f))
                except Exception as ex:
                    self.log_message(f"❌ 壓縮檔處置出錯: {ex}\n")
                    if temp_dir and os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    continue
            else:
                files_to_process.append(src)

            # 決定輸出目錄 (若是 ZIP 檔案，最終輸出將安全隔離在一個獨立的專屬資料夾內)
            if is_zip_task:
                zip_base_name = os.path.splitext(name)[0]
                base_out_dir = settings["output_folder"] if settings["output_folder"] else os.path.dirname(src)
                final_out_dir = os.path.join(base_out_dir, f"{zip_base_name}_轉檔產出")
                os.makedirs(final_out_dir, exist_ok=True)
            else:
                final_out_dir = settings["output_folder"] if settings["output_folder"] else os.path.dirname(src)

            # 遍歷處理這個單元的所有檔案（一般檔案為1個，ZIP解壓後可能為多個）
            for sub_f_idx, current_file in enumerate(files_to_process):
                if self.cancel_requested:
                    break

                curr_name = os.path.basename(current_file)
                base_name = os.path.splitext(curr_name)[0]

                # 對勾選的每種格式進行平行轉檔
                for fmt in target_formats:
                    if self.cancel_requested:
                        break

                    # 決定輸出檔案路徑與檔名 (防呆：同檔名自動更名)
                    out_name = f"{base_name}.{fmt}"
                    if current_file.lower() == os.path.join(final_out_dir, out_name).lower():
                        out_name = f"{base_name}_converted.{fmt}"
                    final_out_path = os.path.join(final_out_dir, out_name)

                    # ----------------------------------------------------
                    # 【核心 FFmpeg 調變參數建置】
                    # ----------------------------------------------------
                    cmd = [self.ffmpeg_exe, "-y"]
                    
                    # 裁切時間參數 (Trim Control)
                    if settings["trim"]:
                        t_start = settings["trim_start"]
                        t_end = settings["trim_end"]
                        if t_start: cmd += ["-ss", t_start]
                        if t_end: cmd += ["-to", t_end]

                    cmd += ["-i", current_file]

                    # 濾鏡管道 (Filter Graph) 配製
                    audio_filters = []
                    
                    # 音量調整
                    v_scale = settings["volume"]
                    if v_scale != 1.0:
                        audio_filters.append(f"volume={v_scale}")
                        
                    # 智慧動態降噪
                    if settings["denoise"]:
                        audio_filters.append("afftdn=nr=12:nt=w")
                        
                    # 自動標準化 (Normalization)
                    if settings["norm"]:
                        audio_filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

                    # 播放速度變速調整 (FFmpeg 變速濾鏡)
                    speed_val = settings["speed"]
                    if speed_val != 1.0:
                        audio_filters.append(f"atempo={speed_val}")

                    if audio_filters:
                        cmd += ["-filter:a", ",".join(audio_filters)]

                    # 重新採樣率與聲道控制
                    sr_choice = settings["sample_rate"]
                    if sr_choice != "保留原始":
                        cmd += ["-ar", sr_choice.split()[0]]
                        
                    ch_choice = settings["channels"]
                    if "Mono" in ch_choice:
                        cmd += ["-ac", "1"]
                    elif "Stereo" in ch_choice:
                        cmd += ["-ac", "2"]

                    # 格式編碼與音質位元率配製
                    br_val = settings["bitrate"]
                    if fmt == "mp3":
                        cmd += ["-acodec", "libmp3lame", "-b:a", br_val]
                    elif fmt == "m4a":
                        cmd += ["-acodec", "aac", "-b:a", br_val]
                    elif fmt == "wav":
                        cmd += ["-acodec", "pcm_s16le"]

                    # 元資料 ID3 標籤注入
                    t_m = settings["meta_title"]
                    a_m = settings["meta_artist"]
                    al_m = settings["meta_album"]
                    if t_m: cmd += ["-metadata", f"title={t_m}"]
                    if a_m: cmd += ["-metadata", f"artist={a_m}"]
                    if al_m: cmd += ["-metadata", f"album={al_m}"]

                    cmd.append(final_out_path)

                    # ----------------------------------------------------
                    # 【技術升级】：真實非同步 FFmpeg 轉檔進度條解析與反饋
                    # ----------------------------------------------------
                    self.log_message(f"⏳ 正在轉檔: {curr_name} -> {out_name}...\n")
                    
                    try:
                        # 啟動非同步子進程並攔截 stderr
                        self.current_process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE,
                            universal_newlines=True,
                            encoding="utf-8",
                            errors="ignore"
                        )

                        duration_seconds = 0.0
                        
                        # 實時讀取 stderr 以解析 FFmpeg 的進度行
                        while True:
                            line = self.current_process.stderr.readline()
                            if not line:
                                break
                            
                            if "Duration:" in line:
                                duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", line)
                                if duration_match:
                                    hours = int(duration_match.group(1))
                                    minutes = int(duration_match.group(2))
                                    seconds = int(duration_match.group(3))
                                    centiseconds = int(duration_match.group(4))
                                    duration_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0

                            if "time=" in line:
                                time_match = re.search(r"time=(\d+):(\d+):(\d+)\.(\d+)", line)
                                speed_match = re.search(r"speed=\s*([\d\.]+)x", line)
                                if time_match and duration_seconds > 0:
                                    hours = int(time_match.group(1))
                                    minutes = int(time_match.group(2))
                                    seconds = int(time_match.group(3))
                                    centiseconds = int(time_match.group(4))
                                    curr_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
                                    
                                    # 計算當前檔案轉檔進度百分比
                                    file_progress = min(1.0, curr_seconds / duration_seconds)
                                    speed_str = f"{speed_match.group(1)}x" if speed_match else "N/A"
                                    
                                    # 整合總體佇列進度
                                    overall_idx = (f_idx / total_files) + (file_progress / total_files)
                                    
                                    # 安全地更新 UI 畫面上的進度與狀態 (Thread-Safe)
                                    lbl_text = f"正在轉檔: {curr_name} ({int(file_progress * 100)}%) | 速度: {speed_str}"
                                    self.root.after(0, self.lbl_progress.configure, {"text": lbl_text, "text_color": ThemeConfig.COLOR_ACCENT})
                                    self.root.after(0, self.progress_bar.set, overall_idx)

                        # 等待子進程結束
                        self.current_process.wait()
                        
                        if self.current_process.returncode == 0:
                            self.log_message(f"✅ 成功：{curr_name} -> {out_name}\n")
                            converted_output_files.append(final_out_path)
                        else:
                            if self.cancel_requested:
                                self.log_message(f"🛑 已手動取消當前轉檔：{curr_name}\n")
                                # 刪除未寫完的殘留檔案
                                if os.path.exists(final_out_path):
                                    os.remove(final_out_path)
                            else:
                                self.log_message(f"❌ 轉檔崩潰：{curr_name} 在處置為 {fmt} 時出錯，代碼 {self.current_process.returncode}\n")
                    
                    except Exception as err:
                        self.log_message(f"❌ 執行異常 {curr_name}: {err}\n")
                    finally:
                        if self.current_process:
                            self.current_process.stderr.close()
                            self.current_process = None

            # 清理 ZIP 解壓暫存資料夾
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                
            # 判斷是否執行原始碼銷毀機制
            if settings["delete_after"] and not is_zip_task and not self.cancel_requested:
                try:
                    os.remove(src)
                    self.log_message(f"🗑️ 已安全銷毀原始本機媒體檔: {name}\n")
                except Exception as e:
                    self.log_message(f"⚠️ 無法自動銷毀原始檔 {name}: {e}\n")

        # ----------------------------------------------------
        # 【全自動完成期：ZIP 打包出貨工作流】
        # ----------------------------------------------------
        if settings["zip_after"] and converted_output_files and not self.cancel_requested:
            self.log_message("⏳ 正在將所有產出的新檔案封裝為最終壓縮包...\n")
            zip_out_dir = settings["output_folder"] if settings["output_folder"] else os.path.dirname(self.queue_files[0]["src"])
            final_zip_path = os.path.join(zip_out_dir, "工作站批次產出包裹.zip")
            try:
                with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as z_file:
                    for f_path in converted_output_files:
                        z_file.write(f_path, os.path.basename(f_path))
                self.log_message(f"🎁 打包出貨成功！檔案已安全封裝至: {final_zip_path}\n")
            except Exception as e:
                self.log_message(f"❌ 壓縮包封裝失敗: {e}\n")

        # ----------------------------------------------------
        # 【收尾階段】更新 UI 控制元件狀態 (Thread-Safe 語意化回饋)
        # ----------------------------------------------------
        if self.cancel_requested:
            self.log_message("🛑 === 自動化工作流已被手動中止 ===\n")
            self.root.after(0, self.lbl_progress.configure, {"text": "🛑 任務已手動終止", "text_color": ThemeConfig.COLOR_DANGER})
        else:
            self.log_message("🎉 === 所有調度矩陣運算完工，感謝使用！ ===\n")
            self.root.after(0, self.lbl_progress.configure, {"text": "🎉 所有轉檔與工作流皆已圓滿完成！", "text_color": ThemeConfig.COLOR_SUCCESS})
            self.root.after(0, self.progress_bar.set, 1.0)
            self.root.after(0, self.progress_bar.configure, {"progress_color": ThemeConfig.COLOR_SUCCESS})
            self.root.after(0, self.clear_queue)
            
        self.root.after(0, self.btn_launch.configure, {"state": "normal", "fg_color": ThemeConfig.COLOR_SUCCESS})
        self.root.after(0, self.btn_cancel.configure, {"state": "disabled", "fg_color": ThemeConfig.COLOR_INACTIVE})
        
        self.is_processing = False
        
        # 彈出對話視窗通知使用者
        msg = "工作站自動化任務已被手動中斷！" if self.cancel_requested else "工作站已全自動圓滿完工！"
        self.root.after(0, messagebox.showinfo, "工作站通知", msg)

if __name__ == "__main__":
    root = ModernApp()
    app = UltraAudioStation(root)
    root.mainloop()