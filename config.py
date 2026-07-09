import os
import json

class ConfigManager:
    def __init__(self):
        self.config_file = os.path.expanduser("~/.ultra_station_config.json")
        self.settings = {
            "theme": "Dark",
            "output_folder": "",
            "recursive": False,
            "zip_after": False,
            "delete_after": False
        }
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings.update(json.load(f))
            except Exception as e: print(f"設定載入失敗: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"設定儲存失敗: {e}")

    def update(self, key, value):
        self.settings[key] = value
        self.save_config()

    def get(self, key, default=None):
        return self.settings.get(key, default)