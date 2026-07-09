import os
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from theme import ThemeConfig
from engine.ffmpeg_engine import SUPPORTED_EXTENSIONS

class QueuePanel:
    def __init__(self, parent, app):
        self.app = app
        self.card = ctk.CTkFrame(parent, **self.app.card_kwargs)
        self._build()
        
    def _build(self):
        self.drop_lbl = ctk.CTkLabel(self.card, text="✨ 拖曳檔案/資料夾/ZIP 至此，或使用按鈕匯入 ✨", font=ThemeConfig.FONT_BODY, text_color=ThemeConfig.COLOR_ACCENT)
        self.drop_lbl.pack(pady=8)
        
        queue_title_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        queue_title_frame.pack(fill="x", padx=15)
        ctk.CTkLabel(queue_title_frame, text="📋 任務佇列", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(side="left")
        ctk.CTkButton(queue_title_frame, text="清空", font=ThemeConfig.FONT_BODY, width=60, height=24, fg_color=ThemeConfig.COLOR_DANGER, hover_color="#be123c", command=self.app.clear_queue).pack(side="right")
        
        import_btn_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        import_btn_frame.pack(fill="x", padx=15, pady=(5, 0))
        ctk.CTkButton(import_btn_frame, text="📄 匯入檔案", font=ThemeConfig.FONT_BODY, fg_color=ThemeConfig.COLOR_ACCENT, hover_color="#1d4ed8", height=28, command=self.import_files_dialog).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(import_btn_frame, text="📁 匯入資料夾", font=ThemeConfig.FONT_BODY, fg_color="#475569", hover_color="#334155", height=28, command=self.import_folder_dialog).pack(side="right", expand=True, fill="x", padx=(5, 0))

        is_dark = ctk.get_appearance_mode() == "Dark"
        self.queue_box = tk.Listbox(self.card, bg="#11131c" if is_dark else "#ffffff", fg=ThemeConfig.COLOR_TEXT_BODY_DARK if is_dark else ThemeConfig.COLOR_TEXT_BODY_LIGHT, selectbackground=ThemeConfig.COLOR_ACCENT, font=ThemeConfig.FONT_CODE, relief="flat", highlightthickness=0, bd=0)
        self.queue_box.pack(fill="both", expand=True, padx=15, pady=10)
        
        # 🔴 修復：使用 lambda 延遲查找，解決初始化時序問題
        self.queue_box.bind("<<ListboxSelect>>", lambda e: self.app.wave_panel.on_queue_select(e))
        
    def refresh_listbox(self):
        self.queue_box.delete(0, tk.END)
        for item in self.app.qm.get_all():
            self.queue_box.insert(tk.END, f"  [{item['size']}]  {item['name']}")

    def import_files_dialog(self):
        file_types = [("支援媒體檔案", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)), ("所有檔案", "*.*")]
        files = filedialog.askopenfilenames(title="選擇欲匯入的影音檔案", filetypes=file_types)
        if files:
            for file in files: self.app.qm.add(file)
            self.refresh_listbox()
            self.app.engine_panel.log_message(f"ℹ️ 加載完成，佇列共 {len(self.app.qm.get_all())} 檔。\n")

    def import_folder_dialog(self):
        folder = filedialog.askdirectory(title="選擇欲匯入的資料夾")
        if folder:
            self.app.qm.scan_directory(folder, self.app.tab_sys.sw_recursive.get())
            self.refresh_listbox()
            self.app.engine_panel.log_message(f"ℹ️ 加載完成，佇列共 {len(self.app.qm.get_all())} 檔。\n")