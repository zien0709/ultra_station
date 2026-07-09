import os
from engine.ffmpeg_engine import SUPPORTED_EXTENSIONS

class QueueManager:
    def __init__(self):
        self.files = []
        
    def add(self, file_path):
        name = os.path.basename(file_path)
        # 防止重複加入相同路徑的檔案
        if any(item["src"] == file_path for item in self.files): return False
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.files.append({"src": file_path, "name": name, "size": f"{size_mb:.2f} MB"})
            return True
        except Exception:
            return False
            
    def scan_directory(self, folder, recursive=False):
        if recursive:
            for root_dir, _, fs in os.walk(folder):
                for f in fs:
                    if f.lower().endswith(SUPPORTED_EXTENSIONS) or f.lower().endswith('.zip'):
                        self.add(os.path.join(root_dir, f))
        else:
            for f in os.listdir(folder):
                if f.lower().endswith(SUPPORTED_EXTENSIONS) or f.lower().endswith('.zip'):
                    self.add(os.path.join(folder, f))

    def clear(self):
        self.files.clear()
        
    def get_all(self):
        return self.files