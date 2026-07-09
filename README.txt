ultra_station/
├── 主程式進入點        = main.py
├── 命令列介面控制器    = cli.py
├── 主題設計配置        = theme.py
├── 設定管理器          = config.py
│
├── engine/
│   ├── 核心轉換引擎    = ffmpeg_engine.py  (唯一核心，純吃 settings 字典)
│   └── AI魔法引擎      = ai_engine.py      (延遲載入，不拖慢 GUI 啟動)
│
├── hardware/
│   └── 硬體偵測模組    = probe.py          (完全無依賴的底層探測器)
│
├── task_queue/                             (避開標準庫 queue 衝突)
│   ├── 任務佇列初始化  = __init__.py
│   └── 任務佇列管理器  = queue_manager.py
│
└── ui/
    ├── 主視窗介面與協調器 = app.py         (App 協調器，注入狀態至各面板)
    │
    ├── tabs/
    │   ├── UI基本分頁     = tab_basic.py
    │   ├── UI進階分頁     = tab_advanced.py
    │   ├── UI魔法引擎分頁 = tab_ai.py
    │   └── UI系統設定分頁 = tab_sys.py
    │
    └── panels/
        ├── UI佇列面板     = queue_panel.py
        ├── UI波形面板     = wave_panel.py
        └── UI引擎監控面板 = engine_panel.py

