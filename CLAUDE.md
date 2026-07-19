# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在本仓库中工作时的指引。

**详细项目说明以 `AGENTS.md` 为准**（目录地图、数据模型、管线细节、已知问题）。本文件只保留最常用的操作要点；修改任一份文件时请同步另一份，避免漂移。

## 项目概述

本项目把《宋代官制辞典》的 OCR 文本转换为可追溯的结构化历史数据。核心对象是"机构"和"官职"，需要保留时间变化、相互关系和史料引用。数据模型为四表（Entities / Timepoints / Relationships / Citations），全量重生成路线另有第五张追溯表 BuildRecords。

**当前活跃工作：**

- `vis/song-bureaucracy-visualization-v2/`：宋代官制时序图谱（Vue 3 + Vite），**当前主要方向**。
- `agent-v0612/`：两阶段数据抽取 agent（辞典 → 原子事实 → 四表），注意**该目录未被 git 跟踪**。

**当前最佳结果库：** `agent-v0612/records/v0620-regen-test/song_bureaucracy_entries_v0620-regen-test.db`（覆盖 832/833 条辞典）。`vis/data/song_bureaucracy_best.db` 是其只读副本，作为可视化数据源。

## 常用命令

**数据批跑（agent-v0612/）：**
```bash
cd agent-v0612
./run.sh --tag <版本标签> --model <模型ID> --limit 25   # 产物隔离到 records/<标签>/
./run.sh --help
```

**可视化（vis/song-bureaucracy-visualization-v2/）：**
```bash
pnpm live                      # 推荐：build + 实时只读服务（127.0.0.1:8643），改库后自动刷新
pnpm dev                       # 需先启动 python3 vis/serve_visualization_v2.py（/api 代理）
python3 vis/normalize_times.py           # 仅源库变化时：best.db -> visualization.db
python3 vis/export_visualization_data.py # 仅更新离线快照 JSON（实时接口失效时的兜底）
```

**验证：**
```bash
python3 -m compileall -q agent-v0612
cd agent-v0612 && python smoke_test.py   # 不调 LLM，对结构化库只读
python3 -m unittest vis.test_live_visualization_data vis.test_normalize_times
sqlite3 <结果库> 'pragma integrity_check;'
```

**环境配置：** 复制 `agent-v0612/.env.example` 到 `agent-v0612/.env` 并填入 key（OpenAI 兼容 / OpenRouter / FreeModel 多 profile，`run.sh --provider` 切换）。辞典源库为 `data/database/song_bureaucracy_dictionary.db`（表 `chapter8t10`）。

## 修改约定

- **修改代码前必须先做好 git 备份**（提交或暂存当前工作区改动，确保任何修改都可回退）。这条规则永远有效，任何会话、任何目录的代码改动都要遵守。
- 抽取相关只改 `agent-v0612/`；可视化相关只改 `vis/song-bureaucracy-visualization-v2/` 和 `vis/*.py` 数据脚本。历史目录（`agent/`、`agent_v0126/`、`agent_v0211/`、`agent_v0303/`）仅作参考。
- 保持 `database.py` 为原子 CRUD，跨表联动逻辑放在 `utils.py`；提示词变更落在两个 prompt 模块。
- 关系必须明确方向，并为关系本身保存引用。
- `db._recreate_tables()` 是破坏性操作，只允许对临时数据库副本执行。
- 调试批跑先用 `--limit` 限制词条数；不要手工编辑 `records/` 下的批跑产物。
