import customtkinter as ctk
from tkinter import filedialog
from theme import ThemeConfig

class TabSys:
    def __init__(self, parent, app):
        self.app = app
        self._build(parent)
        
    def _build(self, parent):
        card_io = ctk.CTkFrame(parent, fg_color="transparent")
        card_io.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(card_io, text="📂 輸出路徑設定", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", pady=(0, 10))
        ctk.CTkButton(card_io, text="選擇自訂輸出資料夾", font=ThemeConfig.FONT_BODY, command=self.choose_output_folder, fg_color="#2c3e50", hover_color="#34495e").pack(fill="x", pady=5)
        
        dir_text = f"目前: {self.app.output_folder}" if self.app.output_folder else "目前：輸出至來源相同目錄"
        self.lbl_out_dir = ctk.CTkLabel(card_io, text=dir_text, font=ThemeConfig.FONT_BODY, text_color=ThemeConfig.COLOR_SUCCESS if self.app.output_folder else ThemeConfig.COLOR_INACTIVE, wraplength=350)
        self.lbl_out_dir.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(card_io, text="自動化行為", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", pady=10)
        
        self.sw_recursive = ctk.CTkSwitch(card_io, text="載入子資料夾 (Recursive)", font=ThemeConfig.FONT_BODY, command=lambda: self.app.config.update("recursive", self.sw_recursive.get()))
        if self.app.config.get("recursive"): self.sw_recursive.select()
        self.sw_recursive.pack(anchor="w", pady=5)
        
        self.sw_zip = ctk.CTkSwitch(card_io, text="轉檔後自動打包 .zip", font=ThemeConfig.FONT_BODY, command=lambda: self.app.config.update("zip_after", self.sw_zip.get()))
        if self.app.config.get("zip_after"): self.sw_zip.select()
        self.sw_zip.pack(anchor="w", pady=5)

        self.sw_delete = ctk.CTkSwitch(card_io, text="轉檔後將原始檔移至垃圾桶", font=ThemeConfig.FONT_BODY, command=lambda: self.app.config.update("delete_after", self.sw_delete.get()))
        if self.app.config.get("delete_after"): self.sw_delete.select()
        self.sw_delete.pack(anchor="w", pady=5)
        
        ctk.CTkLabel(card_io, text="外觀主題設定", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", pady=(20, 10))
        self.theme_switch = ctk.CTkSegmentedButton(card_io, font=ThemeConfig.FONT_BODY, values=["Dark 模式", "Light 模式"], command=self.app.toggle_theme)
        self.theme_switch.set(f"{self.app.config.get('theme', 'Dark')} 模式")
        self.theme_switch.pack(fill="x")

    def choose_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.app.output_folder = folder
            self.app.config.update("output_folder", folder)
            self.lbl_out_dir.configure(text=f"目前: {folder}", text_color=ThemeConfig.COLOR_SUCCESS)