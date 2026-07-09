import os
import argparse
from tqdm import tqdm
from task_queue.queue_manager import QueueManager
from engine.ffmpeg_engine import FFmpegEngine

def parse_and_run(args_list):
    print("🚀 萬能影音工作站 CLI v6.1.0\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    parser = argparse.ArgumentParser(description='萬能影音處理工作站 CLI 模式')
    parser.add_argument('inputs', nargs='+', help='輸入來源（檔案、資料夾、ZIP）')
    
    # 輸出選項
    parser.add_argument('-f', '--format', action='append', help='輸出格式，逗號分隔可多選')
    parser.add_argument('-o', '--output', default='', help='自訂輸出資料夾')
    parser.add_argument('-b', '--bitrate', default='192k', help='壓縮位元率')
    parser.add_argument('--sr', '--sample-rate', default='保留原始', help='採樣率')
    parser.add_argument('--ch', '--channels', default='保留原始', help='聲道')
    
    # DSP 音訊處理
    parser.add_argument('-v', '--volume', type=float, default=1.0, help='音量增益')
    parser.add_argument('-s', '--speed', type=float, default=1.0, help='播放速度')
    parser.add_argument('-n', '--normalize', action='store_true', help='啟用 EBU R128 標準化')
    parser.add_argument('-d', '--denoise', action='store_true', help='啟用基礎降噪')
    
    # 剪輯
    parser.add_argument('--start', default='', help='起始時間')
    parser.add_argument('--end', default='', help='結束時間')
    
    # ID3
    parser.add_argument('--title', default='', help='ID3 標題')
    parser.add_argument('--artist', default='', help='ID3 演出者')
    parser.add_argument('--album', default='', help='ID3 專輯')
    
    # 自動化
    parser.add_argument('-r', '--recursive', action='store_true', help='遞迴掃描子資料夾')
    parser.add_argument('--zip', action='store_true', dest='zip_after', help='完成後打包成 ZIP')
    parser.add_argument('--trash', action='store_true', dest='delete_after', help='完成後將原始檔移至垃圾桶')
    
    # 輸出控制
    parser.add_argument('-q', '--quiet', action='store_true', help='靜默模式')
    parser.add_argument('--dry-run', action='store_true', help='模擬執行')

    args = parser.parse_args(args_list)

    # 處理 --format 的逗號分隔與重複旗標
    target_formats = []
    if args.format:
        for fmt_str in args.format:
            target_formats.extend([f.strip().lower() for f in fmt_str.split(',')])
    if not target_formats:
        target_formats = ['mp3'] # 預設格式

    # 🟡 修復：處理聲道大小寫不匹配問題
    ch_map = {"mono": "Mono (單聲道)", "stereo": "Stereo (雙聲道)"}
    ch_setting = ch_map.get(args.channels.lower(), "保留原始") if args.channels != '保留原始' else "保留原始"

    # 構建跟 GUI 相同的 settings dict
    settings = {
        "recursive": args.recursive,
        "target_formats": target_formats,
        "sample_rate": args.sr,
        "channels": ch_setting,
        "bitrate": args.bitrate,
        "norm": args.normalize,
        "denoise": args.denoise,
        "volume": args.volume,
        "speed": args.speed,
        "trim": bool(args.start or args.end),
        "trim_start": args.start,
        "trim_end": args.end,
        "meta_title": args.title,
        "meta_artist": args.artist,
        "meta_album": args.album,
        "zip_after": args.zip_after,
        "delete_after": args.delete_after,
        "output_folder": args.output
    }

    # 解析輸入路徑到佇列
    qm = QueueManager()
    for input_path in args.inputs:
        if os.path.isdir(input_path):
            qm.scan_directory(input_path, args.recursive)
        else:
            qm.add(input_path)
            
    queue_files = qm.get_all()
    if not queue_files:
        print("❌ 找不到支援的媒體檔案，請檢查輸入路徑。")
        return

    print(f"📋 任務佇列：{len(queue_files)} 個檔案  |  目標格式：{', '.join(target_formats)}")
    
    if args.dry_run:
        print("\n[模擬執行 (Dry Run)]")
        for f in queue_files:
            print(f" - 預計處理: {f['src']} -> 轉為 {', '.join(target_formats)}")
        return

    engine = FFmpegEngine()
    overall_pbar = tqdm(total=100, desc="整體進度", disable=args.quiet, bar_format="{l_bar}{bar}| {n:.1f}% [{postfix}]")

    def progress_callback(overall_idx, text):
        if not args.quiet:
            overall_pbar.n = min(100, overall_idx * 100)
            overall_pbar.set_postfix_str(text)
            overall_pbar.refresh()

    def log_callback(msg):
        # 🟢 修復：非靜默模式下，完整輸出所有轉檔進度與成功訊息
        if not args.quiet:
            tqdm.write(msg.strip())

    engine.run(queue_files, settings, progress_callback, log_callback, lambda: False)
    
    overall_pbar.n = 100
    overall_pbar.refresh()
    overall_pbar.close()
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎉 所有指令列轉檔任務執行完畢！")