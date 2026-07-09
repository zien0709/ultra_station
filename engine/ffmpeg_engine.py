import os
import re
import uuid
import shutil
import zipfile
import subprocess
from imageio_ffmpeg import get_ffmpeg_exe

try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

# 支持格式常數
SUPPORTED_EXTENSIONS = (
    '.webm', '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v',
    '.m4a', '.wav', '.flac', '.ogg', '.aac', '.wma', '.mp3'
)

class FFmpegEngine:
    def __init__(self):
        # 🔴 修復：加入 __init__ 確保 terminate_current 安全
        self.current_process = None

    @staticmethod
    def get_exe():
        return get_ffmpeg_exe()
        
    @staticmethod
    def parse_time(t_str):
        if not t_str: return 0.0
        parts = str(t_str).split(':')
        try:
            if len(parts) == 3: return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
            elif len(parts) == 2: return float(parts[0])*60 + float(parts[1])
            elif len(parts) == 1: return float(parts[0])
        except ValueError:
            return -1.0
        return -1.0

    def run(self, queue_files, settings, progress_callback, log_callback, check_cancel):
        """ 獨立且無狀態的執行引擎。完全不碰觸 UI 元件。 """
        target_formats = settings.get("target_formats", ["mp3"])
        total_files = len(queue_files)
        converted_output_files = []
        ffmpeg_exe = self.get_exe()
        self.current_process = None
        
        trim_start_sec = self.parse_time(settings.get("trim_start", ""))
        trim_end_sec = self.parse_time(settings.get("trim_end", ""))

        log_callback(f"🚀 === 啟動自動化工作流，佇列共 {total_files} 個任務 ===\n")

        for f_idx, file_item in enumerate(queue_files):
            if check_cancel(): break

            src, name = file_item["src"], file_item["name"]
            temp_dir, files_to_process, is_zip_task = None, [], src.lower().endswith('.zip')

            if is_zip_task:
                log_callback(f"⏳ 正在解壓：{name}...\n")
                temp_dir = src + f"_extracted_temp_{uuid.uuid4().hex[:8]}"
                os.makedirs(temp_dir, exist_ok=True)
                try:
                    with zipfile.ZipFile(src, 'r') as z_ref:
                        for member in z_ref.namelist():
                            if not os.path.basename(member): continue
                            target_path = os.path.abspath(os.path.join(temp_dir, member))
                            if not target_path.startswith(os.path.abspath(temp_dir)):
                                raise Exception(f"Zip Slip 攻擊: {member}")
                        z_ref.extractall(temp_dir)
                    for r_d, _, fs in os.walk(temp_dir):
                        for f in fs:
                            if f.lower().endswith(SUPPORTED_EXTENSIONS): 
                                files_to_process.append(os.path.join(r_d, f))
                except Exception as ex:
                    log_callback(f"❌ 壓縮檔處置出錯: {ex}\n")
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    continue
            else: 
                files_to_process.append(src)

            if is_zip_task:
                final_out_dir = os.path.join(settings.get("output_folder", "") or os.path.dirname(src), f"{os.path.splitext(name)[0]}_轉檔產出")
                os.makedirs(final_out_dir, exist_ok=True)
            else:
                final_out_dir = settings.get("output_folder", "") or os.path.dirname(src)

            for current_file in files_to_process:
                if check_cancel(): break
                base_name = os.path.splitext(os.path.basename(current_file))[0]

                for fmt in target_formats:
                    if check_cancel(): break
                    
                    out_name = f"{base_name}.{fmt}"
                    final_out_path = os.path.join(final_out_dir, out_name)
                    
                    if os.path.abspath(current_file).lower() == os.path.abspath(final_out_path).lower():
                        out_name = f"{base_name}_converted.{fmt}"
                        final_out_path = os.path.join(final_out_dir, out_name)
                    
                    counter = 1
                    base_out_name = os.path.splitext(out_name)[0]
                    while os.path.exists(final_out_path) or final_out_path in converted_output_files:
                        out_name = f"{base_out_name}_{counter}.{fmt}"
                        final_out_path = os.path.join(final_out_dir, out_name)
                        counter += 1

                    cmd = [ffmpeg_exe, "-y"]
                    if settings.get("trim"):
                        if settings.get("trim_start"): cmd += ["-ss", str(settings["trim_start"])]
                        if settings.get("trim_end"): cmd += ["-to", str(settings["trim_end"])]
                    cmd += ["-i", current_file]

                    audio_filters = []
                    if settings.get("volume", 1.0) != 1.0: audio_filters.append(f"volume={settings['volume']}")
                    if settings.get("denoise"): audio_filters.append("afftdn=nr=12:nt=w")
                    if settings.get("norm"): audio_filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
                    if settings.get("speed", 1.0) != 1.0: audio_filters.append(f"atempo={settings['speed']}")
                    if audio_filters: cmd += ["-filter:a", ",".join(audio_filters)]

                    sr = settings.get("sample_rate", "保留原始")
                    if sr != "保留原始": cmd += ["-ar", sr.split()[0]]
                    ch = settings.get("channels", "保留原始")
                    if "Mono" in ch: cmd += ["-ac", "1"]
                    elif "Stereo" in ch: cmd += ["-ac", "2"]

                    br = settings.get("bitrate", "192k")
                    if fmt == "mp3": cmd += ["-acodec", "libmp3lame", "-b:a", br]
                    elif fmt == "m4a": cmd += ["-acodec", "aac", "-b:a", br]
                    elif fmt == "wav": cmd += ["-acodec", "pcm_s16le"]

                    if settings.get("meta_title"): cmd += ["-metadata", f"title={settings['meta_title']}"]
                    if settings.get("meta_artist"): cmd += ["-metadata", f"artist={settings['meta_artist']}"]
                    if settings.get("meta_album"): cmd += ["-metadata", f"album={settings['meta_album']}"]
                    cmd.append(final_out_path)

                    log_callback(f"⏳ 轉檔: {os.path.basename(current_file)} -> {out_name}...\n")
                    
                    try:
                        self.current_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8", errors="ignore")
                        duration_seconds = 0.0
                        while True:
                            line = self.current_process.stderr.readline()
                            if not line: break
                            
                            if "Duration:" in line:
                                duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", line)
                                if duration_match:
                                    duration_seconds = int(duration_match.group(1))*3600 + int(duration_match.group(2))*60 + int(duration_match.group(3)) + int(duration_match.group(4))/100.0
                                    
                                    if settings.get("trim"):
                                        if trim_end_sec > 0: duration_seconds = trim_end_sec - trim_start_sec
                                        else: duration_seconds = duration_seconds - trim_start_sec
                                        if duration_seconds <= 0: duration_seconds = 1.0 
                                        
                            if "time=" in line and duration_seconds > 0:
                                time_match = re.search(r"time=(\d+):(\d+):(\d+)\.(\d+)", line)
                                speed_match = re.search(r"speed=\s*([\d\.]+)x", line)
                                if time_match:
                                    curr_seconds = int(time_match.group(1))*3600 + int(time_match.group(2))*60 + int(time_match.group(3)) + int(time_match.group(4))/100.0
                                    file_progress = min(1.0, curr_seconds / duration_seconds)
                                    overall_idx = (f_idx / total_files) + (file_progress / total_files)
                                    spd = speed_match.group(1)+'x' if speed_match else 'N/A'
                                    lbl_text = f"進度: {os.path.basename(current_file)} ({int(file_progress * 100)}%) | 速度: {spd}"
                                    progress_callback(overall_idx, lbl_text)
                                    
                        self.current_process.wait()
                        
                        if self.current_process.returncode == 0:
                            log_callback(f"✅ 成功：{out_name}\n")
                            converted_output_files.append(final_out_path)
                        else:
                            if check_cancel():
                                if os.path.exists(final_out_path): os.remove(final_out_path)
                            else:
                                log_callback(f"❌ 轉檔崩潰，代碼 {self.current_process.returncode}\n")
                    except Exception as err:
                        log_callback(f"❌ 異常: {err}\n")
                    finally:
                        if self.current_process: 
                            self.current_process.stderr.close()
                            self.current_process = None

            if temp_dir and os.path.exists(temp_dir): 
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            if settings.get("delete_after") and not is_zip_task and not check_cancel():
                try: 
                    if send2trash:
                        send2trash(src)
                        log_callback(f"🗑️ 已安全將原始檔移至資源回收桶: {name}\n")
                    else:
                        os.remove(src)
                        log_callback(f"⚠️ 未安裝 send2trash，已永久銷毀原始檔: {name}\n")
                except Exception as e: 
                    log_callback(f"⚠️ 刪除原始檔失敗: {e}\n")

        if settings.get("zip_after") and converted_output_files and not check_cancel():
            log_callback("⏳ 正在封裝為壓縮包...\n")
            zip_out_dir = settings.get("output_folder") or os.path.dirname(queue_files[0]["src"])
            final_zip_path = os.path.join(zip_out_dir, "工作站批次產出包裹.zip")
            try:
                with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as z_file:
                    for f_path in converted_output_files: 
                        z_file.write(f_path, os.path.basename(f_path))
                log_callback(f"🎁 打包出貨成功: {final_zip_path}\n")
            except Exception as e: 
                log_callback(f"❌ 打包失敗: {e}\n")

    def terminate_current(self):
        if self.current_process:
            try: self.current_process.terminate()
            except Exception: pass