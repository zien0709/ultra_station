import os # 🔴 修復：加入漏掉的 import os (防止 Drag & Drop 崩潰)
import threading
import customtkinter as ctk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

from theme import ThemeConfig
from config import ConfigManager
from task_queue.queue_manager import QueueManager
from engine.ffmpeg_engine import FFmpegEngine, SUPPORTED_EXTENSIONS

from ui.tabs.tab_basic import TabBasic
from ui.tabs.tab_advanced import TabAdvanced
from ui.tabs.tab_ai import TabAI
from ui.tabs.tab_sys import TabSys

from ui.panels.queue_panel import QueuePanel
from ui.panels.wave_panel import WavePanel
from ui.panels.engine_panel import EnginePanel

class ModernApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class UltraAudioStation:
    def __init__(self, root):
        self.root = root
        self.root.title("萬能核心影音處理工作站 v6.1.0 - 模組雙棲版")
        self.root.geometry("1280x900") 
        
        self.config = ConfigManager()
        self.qm = QueueManager()
        self.engine = FFmpegEngine()
        
        initial_theme = self.config.get("theme", "Dark")
        ctk.set_appearance_mode(initial_theme)
        ctk.set_default_color_theme("blue")
        self.root.configure(fg_color=(ThemeConfig.COLOR_BG_LIGHT, ThemeConfig.COLOR_BG_DARK))
        
        try:
            self.ffmpeg_exe = self.engine.get_exe()
        except Exception as e:
            messagebox.showerror("核心錯誤", f"找不到 FFmpeg 核心：{e}")
            self.root.destroy()
            return

        self.output_folder = self.config.get("output_folder", "")
        self.is_processing = False
        self.cancel_requested = False
        
        # 共享卡片佈局設定
        self.card_kwargs = {
            "corner_radius": 16,
            "fg_color": (ThemeConfig.COLOR_CARD_LIGHT, ThemeConfig.COLOR_CARD_DARK),
            "border_width": 1,
            "border_color": (ThemeConfig.COLOR_BORDER_LIGHT, ThemeConfig.COLOR_BORDER_DARK)
        }
        self.text_title_color = (ThemeConfig.COLOR_TEXT_TITLE_LIGHT, ThemeConfig.COLOR_TEXT_TITLE_DARK)
        self.text_body_color = (ThemeConfig.COLOR_TEXT_BODY_LIGHT, ThemeConfig.COLOR_TEXT_BODY_DARK)

        self._build_ui(initial_theme)
        
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)
        self.root.dnd_bind('<<DragEnter>>', self.handle_drag_enter)
        self.root.dnd_bind('<<DragLeave>>', self.handle_drag_leave)

    def _build_ui(self, initial_theme):
        self.root.grid_columnconfigure(0, weight=4) 
        self.root.grid_columnconfigure(1, weight=5) 
        self.root.grid_rowconfigure(0, weight=1)

        # 左側 Tabview
        self.left_panel = ctk.CTkFrame(self.root, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        
        self.tabview = ctk.CTkTabview(
            self.left_panel, 
            corner_radius=16, 
            fg_color=(ThemeConfig.COLOR_CARD_LIGHT, ThemeConfig.COLOR_CARD_DARK),
            border_width=1,
            border_color=(ThemeConfig.COLOR_BORDER_LIGHT, ThemeConfig.COLOR_BORDER_DARK),
            segmented_button_selected_color=ThemeConfig.COLOR_ACCENT,
            segmented_button_selected_hover_color="#1d4ed8",
            text_color=self.text_body_color
        )
        self.tabview.pack(fill="both", expand=True)
        
        self.tab_basic = TabBasic(self.tabview.add("🎛️ 基本轉換"), self)
        self.tab_adv = TabAdvanced(self.tabview.add("🎚️ 進階處理"), self)
        self.tab_ai = TabAI(self.tabview.add("✨ AI 魔法"), self)
        self.tab_sys = TabSys(self.tabview.add("⚙️ 系統設定"), self)

        # 右側 Panels
        self.right_panel = ctk.CTkFrame(self.root, corner_radius=16, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        self.right_panel.grid_rowconfigure(0, weight=4)  
        self.right_panel.grid_rowconfigure(1, weight=3)  
        self.right_panel.grid_rowconfigure(2, weight=3)  
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.queue_panel = QueuePanel(self.right_panel, self)
        self.queue_panel.card.grid(row=0, column=0, sticky="nsew", pady=5)
        
        self.wave_panel = WavePanel(self.right_panel, self)
        self.wave_panel.card.grid(row=1, column=0, sticky="nsew", pady=5)
        
        self.engine_panel = EnginePanel(self.right_panel, self)
        self.engine_panel.card.grid(row=2, column=0, sticky="nsew", pady=5)

    def toggle_theme(self, choice):
        theme_str = choice.split(" ")[0]
        self.config.update("theme", theme_str)
        if theme_str == "Dark":
            ctk.set_appearance_mode("Dark")
            bg_color, text_color = ThemeConfig.COLOR_CARD_DARK, ThemeConfig.COLOR_TEXT_BODY_DARK
            self.queue_panel.queue_box.configure(bg="#11131c", fg=text_color)
        else:
            ctk.set_appearance_mode("Light")
            bg_color, text_color = ThemeConfig.COLOR_CARD_LIGHT, ThemeConfig.COLOR_TEXT_BODY_LIGHT
            self.queue_panel.queue_box.configure(bg="#ffffff", fg=text_color)
            
        self.wave_panel.ax.set_facecolor(bg_color)
        self.wave_panel.fig.set_facecolor(bg_color)
        self.wave_panel.ax.tick_params(colors=text_color)
        selection = self.queue_panel.queue_box.curselection()
        if selection: self.wave_panel.on_queue_select(None)
        else: self.wave_panel.canvas.draw()

    def handle_drag_enter(self, event):
        is_dark = ctk.get_appearance_mode() == "Dark"
        self.queue_panel.card.configure(fg_color=ThemeConfig.COLOR_CARD_DRAG_HOVER_DARK if is_dark else ThemeConfig.COLOR_CARD_DRAG_HOVER_LIGHT)

    def handle_drag_leave(self, event):
        is_dark = ctk.get_appearance_mode() == "Dark"
        self.queue_panel.card.configure(fg_color=ThemeConfig.COLOR_CARD_DARK if is_dark else ThemeConfig.COLOR_CARD_LIGHT)

    def handle_drop(self, event):
        self.handle_drag_leave(event)
        paths = self.root.tk.splitlist(event.data)
        for path in paths:
            path = path.strip('"\'') 
            if os.path.isdir(path): self.qm.scan_directory(path, self.tab_sys.sw_recursive.get())
            elif path.lower().endswith('.zip') or path.lower().endswith(SUPPORTED_EXTENSIONS): self.qm.add(path)
        self.queue_panel.refresh_listbox()
        self.engine_panel.log_message(f"ℹ️ 加載完成，佇列共 {len(self.qm.get_all())} 檔。\n")

    def clear_queue(self):
        if self.is_processing:
            messagebox.showwarning("無法清空", "引擎自動化中，請先終止任務！")
            return
        self.qm.clear()
        self.queue_panel.refresh_listbox()
        self.engine_panel.log_message("🧹 佇列已清空。\n")
        self.wave_panel.draw_empty("")

    def request_cancel(self):
        if self.is_processing and messagebox.askyesno("終止確認", "確定要中止所有自動化任務嗎？"):
            self.cancel_requested = True
            self.engine_panel.log_message("\n🛑 接收中止命令... 系統將安全退出...\n")
            self.engine_panel.progress_bar.configure(progress_color=ThemeConfig.COLOR_DANGER)
            self.engine_panel.btn_cancel.configure(fg_color=ThemeConfig.COLOR_DANGER)
            self.engine.terminate_current()

    def launch_workflow_thread(self):
        if self.is_processing: return
        if not self.qm.get_all():
            messagebox.showwarning("佇列為空", "請先匯入檔案！")
            return
            
        selected_formats = []
        if self.tab_basic.fmt_mp3.get(): selected_formats.append("mp3")
        if self.tab_basic.fmt_wav.get(): selected_formats.append("wav")
        if self.tab_basic.fmt_m4a.get(): selected_formats.append("m4a")
        if not selected_formats:
            messagebox.showwarning("設定出錯", "至少勾選一種目標格式！")
            return
            
        t_start_raw = self.tab_adv.ent_start.get().strip()
        t_end_raw = self.tab_adv.ent_end.get().strip()
        if self.tab_adv.sw_trim.get():
            if t_start_raw and self.engine.parse_time(t_start_raw) < 0:
                messagebox.showwarning("格式錯誤", "起始時間格式不符！請輸入秒數 (例如 15) 或 MM:SS (例如 01:20)")
                return
            if t_end_raw and self.engine.parse_time(t_end_raw) < 0:
                messagebox.showwarning("格式錯誤", "結束時間格式不符！請輸入秒數或 MM:SS")
                return
            if t_start_raw and t_end_raw and self.engine.parse_time(t_start_raw) >= self.engine.parse_time(t_end_raw):
                messagebox.showwarning("邏輯錯誤", "起始時間必須小於結束時間！")
                return

        gui_snapshot = {
            "recursive": self.config.get("recursive"),
            "target_formats": selected_formats,
            "sample_rate": self.tab_adv.cbo_sr.get(),
            "channels": self.tab_adv.cbo_ch.get(),
            "bitrate": self.tab_adv.cbo_br.get(),
            "norm": self.tab_adv.sw_norm.get(),
            "denoise": self.tab_adv.sw_denoise.get(),
            "volume": self.tab_adv.vol_slider.get(),
            "speed": self.tab_adv.speed_slider.get(),
            "trim": self.tab_adv.sw_trim.get(),
            "trim_start": t_start_raw,
            "trim_end": t_end_raw,
            "meta_title": self.tab_adv.meta_title.get().strip(),
            "meta_artist": self.tab_adv.meta_artist.get().strip(),
            "meta_album": self.tab_adv.meta_album.get().strip(),
            "zip_after": self.config.get("zip_after"),
            "delete_after": self.config.get("delete_after"),
            "output_folder": self.output_folder
        }

        self.cancel_requested = False
        self.is_processing = True
        self.engine_panel.progress_bar.configure(progress_color=ThemeConfig.COLOR_ACCENT)
        self.engine_panel.btn_launch.configure(state="disabled", fg_color="gray")
        self.engine_panel.btn_cancel.configure(state="normal", fg_color=ThemeConfig.COLOR_DANGER)
        self.engine_panel.progress_bar.set(0)

        def progress_callback(overall_idx, text):
            self.root.after(0, self.engine_panel.lbl_progress.configure, {"text": text, "text_color": ThemeConfig.COLOR_ACCENT})
            self.root.after(0, self.engine_panel.progress_bar.set, overall_idx)
            
        def complete_callback():
            if self.cancel_requested:
                self.engine_panel.log_message("🛑 === 任務已中止 ===\n")
                self.root.after(0, self.engine_panel.lbl_progress.configure, {"text": "🛑 任務已手動終止", "text_color": ThemeConfig.COLOR_DANGER})
            else:
                self.engine_panel.log_message("🎉 === 所有調度完工！ ===\n")
                self.root.after(0, self.engine_panel.lbl_progress.configure, {"text": "🎉 所有轉檔與工作流皆已圓滿完成！", "text_color": ThemeConfig.COLOR_SUCCESS})
                self.root.after(0, self.engine_panel.progress_bar.set, 1.0)
                self.root.after(0, self.engine_panel.progress_bar.configure, {"progress_color": ThemeConfig.COLOR_SUCCESS})
                self.root.after(0, self.clear_queue)
                
            self.root.after(0, self.engine_panel.btn_launch.configure, {"state": "normal", "fg_color": ThemeConfig.COLOR_SUCCESS})
            self.root.after(0, self.engine_panel.btn_cancel.configure, {"state": "disabled", "fg_color": ThemeConfig.COLOR_INACTIVE})
            self.is_processing = False
            self.root.after(0, messagebox.showinfo, "工作站通知", "自動化任務已被中斷！" if self.cancel_requested else "工作站已全自動圓滿完工！")

        def thread_task():
            self.engine.run(self.qm.get_all(), gui_snapshot, progress_callback, self.engine_panel.log_message, lambda: self.cancel_requested)
            complete_callback()

        threading.Thread(target=thread_task, daemon=True).start()

def launch_gui():
    root = ModernApp()
    app = UltraAudioStation(root)
    root.mainloop()