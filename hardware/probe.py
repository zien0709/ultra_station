import os
import platform

class HardwareProbe:
    """
    純硬體探測模組，無任何 UI 依賴。
    為 Phase 3 的 AI 引擎預留，未來可擴充 psutil 或 pynvml 來偵測 RAM 與 GPU 狀態。
    """
    @staticmethod
    def get_cpu_cores():
        try:
            # 預設保留部分核心給系統，若無法偵測則退回安全值 2
            return os.cpu_count() or 2
        except Exception:
            return 2

    @staticmethod
    def get_system_info():
        return {
            "os": platform.system(),
            "release": platform.release(),
            "cpu_cores": HardwareProbe.get_cpu_cores()
        }