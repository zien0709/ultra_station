import os
import subprocess
from imageio_ffmpeg import get_ffmpeg_exe

def batch_convert(folder_path):
    if not os.path.exists(folder_path):
        print("找不到這個資料夾，請檢查路徑是否正確！")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.webm')]
    
    if not files:
        print("資料夾內沒有 .webm 檔案！")
        return

    # 取得 moviepy 內建下載好的 ffmpeg 執行檔路徑
    ffmpeg_exe = get_ffmpeg_exe()
    print(f"共找到 {len(files)} 個檔案，開始強制轉碼...\n")

    for idx, file_name in enumerate(files, 1):
        webm_path = os.path.join(folder_path, file_name)
        mp3_name = os.path.splitext(file_name)[0] + ".mp3"
        mp3_path = os.path.join(folder_path, mp3_name)
        
        print(f"[{idx}/{len(files)}] 正在轉換: {file_name}")
        
        # 使用 ffmpeg 底層指令，-y 代表直接覆蓋，並強制忽略不完整的 Header
        cmd = [
            ffmpeg_exe, "-y",
            "-i", webm_path,
            "-acodec", "libmp3lame",
            "-ab", "192k",
            mp3_path
        ]
        
        try:
            # 執行指令並隱藏 ffmpeg 的囉嗦輸出
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print("   └ 成功！")
        except subprocess.CalledProcessError as e:
            print(f"   └ 失敗：轉碼出錯，原因可能為檔案損壞。")

    print("\n🎉 全部轉換完成！")

if __name__ == "__main__":
    target_folder = r"C:\Users\user\Downloads\33"
    batch_convert(target_folder)