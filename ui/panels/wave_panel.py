import threading
import subprocess
import numpy as np
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from theme import ThemeConfig

class WavePanel:
    def __init__(self, parent, app):
        self.app = app
        self.card = ctk.CTkFrame(parent, **self.app.card_kwargs)
        self.waveform_thread = None  
        self.waveform_proc = None 
        self.waveform_lock = threading.Lock()
        self._build()
        
    def _build(self):
        ctk.CTkLabel(self.card, text="📊 波形預覽 (True Amplitude)", font=ThemeConfig.FONT_TITLE_CARD, text_color=self.app.text_title_color).pack(anchor="w", padx=15, pady=6)
        
        self.fig, self.ax = plt.subplots(figsize=(5, 1.2), facecolor='#161922')
        self.ax.set_facecolor('#161922')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.plot(np.zeros(100), color=ThemeConfig.COLOR_WAVE_DARK_FILL)  
        self.ax.axis('off')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def on_queue_select(self, event):
        selection = self.app.queue_panel.queue_box.curselection()
        if not selection: return
        file_path = self.app.qm.get_all()[selection[0]]["src"]

        if file_path.lower().endswith('.zip'):
            self.draw_empty("📦 ZIP 檔案 (解壓後顯示波形)")
            return

        with self.waveform_lock:
            if self.waveform_proc and self.waveform_proc.poll() is None:
                try: self.waveform_proc.terminate()
                except Exception: pass
            
        self.waveform_thread = threading.Thread(target=self._async_load_waveform, args=(file_path,), daemon=True)
        self.waveform_thread.start()

    def _async_load_waveform(self, file_path):
        cmd = [self.app.ffmpeg_exe, "-y", "-ss", "0", "-t", "60", "-i", file_path, "-f", "s16le", "-ac", "1", "-ar", "8000", "-"]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            with self.waveform_lock:
                self.waveform_proc = proc
            
            raw_data = proc.stdout.read(960000)
            
            # 🔴 修復：Race Condition 防護，確認是我自己的 proc 才動手關閉
            with self.waveform_lock:
                if self.waveform_proc is proc:
                    proc.stdout.close()
                    proc.terminate()
                    self.waveform_proc = None
                    
            if len(raw_data) > 0:
                data = np.frombuffer(raw_data, dtype=np.int16)
                step = max(1, len(data) // 300)
                self.app.root.after(0, self.draw_waveform, data[::step])
            else:
                self.app.root.after(0, self.draw_empty, "無法取得音訊流")
        except Exception:
            self.app.root.after(0, self.draw_empty, "解碼失敗")

    def draw_waveform(self, y_data):
        self.ax.clear()
        x = np.arange(len(y_data))
        is_dark = ctk.get_appearance_mode() == "Dark"
        fc, fca, lc, bc = (ThemeConfig.COLOR_WAVE_DARK_FILL, ThemeConfig.COLOR_WAVE_DARK_FILL_ALT, ThemeConfig.COLOR_WAVE_DARK_LINE, ThemeConfig.COLOR_CARD_DARK) if is_dark else (ThemeConfig.COLOR_WAVE_LIGHT_FILL, ThemeConfig.COLOR_WAVE_LIGHT_FILL_ALT, ThemeConfig.COLOR_WAVE_LIGHT_LINE, ThemeConfig.COLOR_CARD_LIGHT)

        self.ax.fill_between(x, -y_data, y_data, color=fc, alpha=0.35)
        self.ax.fill_between(x, -y_data * 0.6, y_data * 0.6, color=fca, alpha=0.5)
        self.ax.plot(x, y_data, color=lc, alpha=0.8, linewidth=0.8)
        self.ax.axis('off')
        self.ax.set_facecolor(bc)
        self.canvas.draw()

    def draw_empty(self, msg):
        self.ax.clear()
        self.ax.text(0.5, 0.5, f"⚠️ {msg}", color='gray', ha='center', va='center', font=ThemeConfig.FONT_BODY)
        self.ax.axis('off')
        self.ax.set_facecolor(ThemeConfig.COLOR_CARD_DARK if ctk.get_appearance_mode() == "Dark" else ThemeConfig.COLOR_CARD_LIGHT)
        self.canvas.draw()