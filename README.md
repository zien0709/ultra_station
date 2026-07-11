# Ultra Station 專案架構說明文件

本文件詳細說明 `ultra_station` 專案的目錄結構、各模組之功能職責以及元件間的協調設計。

## 1. 專案目錄樹狀圖 (Directory Tree)

```text
ultra_station/
├── main.py               # 主程式進入點
├── cli.py                # 命令列介面控制器
├── theme.py              # 主題設計配置
├── config.py             # 設定管理器
│
├── engine/               # 核心處理引擎模組
│   ├── ffmpeg_engine.py  # 核心轉換引擎 (唯一核心，純吃 settings 字典)
│   └── ai_engine.py      # AI魔法引擎 (延遲載入，不拖慢 GUI 啟動)
│
├── hardware/             # 硬體層級探測模組
│   └── probe.py          # 硬體偵測模組 (完全無依賴的底層探測器)
│
├── task_queue/           # 任務佇列模組 (獨立命名以避開標準庫 queue 衝突)
│   ├── __init__.py       # 任務佇列初始化
│   └── queue_manager.py  # 任務佇列管理器
│
└── ui/                   # 圖形使用者介面模組 (GUI)
    ├── app.py            # 主視窗介面與協調器 (App 協調器，注入狀態至各面板)
    │
    ├── tabs/             # GUI 分頁標籤頁面
    │   ├── tab_basic.py  # UI基本分頁
    │   ├── tab_advanced.py # UI進階分頁
    │   ├── tab_ai.py     # UI魔法引擎分頁
    │   └── tab_sys.py    # UI系統設定分頁
    │
    └── panels/           # GUI 獨立功能面板
        ├── queue_panel.py  # UI佇列面板
        ├── wave_panel.py   # UI波形面板
        └── engine_panel.py # UI引擎監控面板
