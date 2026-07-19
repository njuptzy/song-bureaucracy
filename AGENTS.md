# Song Bureaucracy AGENTS Guide

## 项目目标

本项目把《宋代官制辞典》的 OCR 文本转成可追溯的宋代官制结构化数据。核心对象分为"机构"和"官职"，需要保留它们的时间变化、相互关系和史料引用。

当前有两条主线：

1. **数据抽取/重生成**：用 LLM agent 把辞典条目写入结构化 SQLite（`agent-v0612/` + `prompts/` 下的重生成/校对 agent 技能）。
2. **可视化**：`vis/song-bureaucracy-visualization-v2/` 的宋代官制时序图谱，**这是当前的主要工作方向**。

## 先看这里

- 当前活跃开发：`vis/song-bureaucracy-visualization-v2/`（可视化）和 `agent-v0612/`（数据抽取）。
- 当前最佳结果库：`agent-v0612/records/v0620-regen-test/song_bureaucracy_entries_v0620-regen-test.db`（覆盖辞典 833 条中的 832 条；981 实体 / 1813 时间点 / 1177 关系 / 3126 引用 / 7288 条 BuildRecords 追溯行）。
- `vis/data/song_bureaucracy_best.db` 是该库的只读副本，是可视化的数据源；`vis/data/song_bureaucracy_visualization.db` 是由它生成的时间标准化工作库。
- 辞典源库：`data/database/song_bureaucracy_dictionary.db`（表 `chapter8t10`，833 条）。
- `agent-v0612/` **整个目录未被 git 跟踪**，改坏没有版本兜底；数据库改动前先备份文件。
- `db._recreate_tables()` 会清空结构化结果表，只允许对临时数据库副本执行。
- `data/` 被根目录 `.gitignore` 忽略，但本地工作区已恢复外部数据。

## 目录地图

| 路径 | 用途 | 维护建议 |
| --- | --- | --- |
| `agent-v0612/` | 当前抽取实现：两阶段 agent（辞典 → 原子事实 → 四表）、`run.sh` 版本化批跑、多 provider LLM 客户端 | 主要开发目录之一；**未纳入 git** |
| `agent-v0612/records/<标签>/` | 各版本批跑产物（结果库、词条 records_*.json、failed_entries.json、run.log） | 生成物，不要手工编辑 |
| `agent_framework/` | 共享的 OpenRouter 客户端（`llm.py`），被 agent-v0612 包装使用 | 稳定 |
| `prompts/` | 两个独立 agent 技能提示词：逐条校对（`..._curation_...`）和全量重生成（`..._full_regeneration_...`），驱动 agent 直接操作 SQLite | 重生成路线的事实标准 |
| `vis/` | 可视化工作区：时间标准化、数据导出脚本、v1/v2 前端、CBDB 模板 | **当前主战场** |
| `vis/song-bureaucracy-visualization-v2/` | 当前可视化版本（Vue 3 + Vite）：时序事件 / 层级结构 / 年表三视图 + 底部宋代总时间线 | 活跃开发 |
| `vis/song-bureaucracy-visualization/` | v1 旧版前端 | 冻结，不再同步 |
| `vis/CBDB-Migration-Map/` | v2 复制改造前的原始模板，也是 `node_modules` 的符号链接来源 | 只读参考 |
| `visualization/` | 旧的逐条审查工具（只读 `server.py` + 静态页）：四表数据与辞典原文并排审查，自动标可疑数据 | 历史工具，仍可用 |
| `analysis/` | 模型对比报告（`v0614_first25_model_comparison.md`）、结果检查脚本 | 分析材料 |
| `outputs/excel-db-overlap/` | 尚书省 Excel 表与数据库重叠核查产物 | 生成物 |
| `process/ocr-results/` | OCR 清洗 notebook：MinerU 结果 → 半结构化辞典数据 | 输入预处理层 |
| `data/` | 外部数据（辞典库、OCR 结果等），git 忽略 | 只入不删 |
| `agent/`、`agent_v0126/`、`agent_v0211/`、`agent_v0303/`、`agent_test/` | 历史抽取版本 | 追溯思路用，不要同步修改 |
| `doc/`、`plans/` | 设计文档与演进记录 | 阅读时注意版本号 |
| `repair-agent/` | 空目录，预留 | — |

## 数据管线

### A. 两阶段抽取（`agent-v0612/`）

辞典 `chapter8t10` 逐条进入两阶段循环，每阶段最多 10 轮，模型输出 `"Tasks All Finished"` 结束：

1. 阶段 1（`prompt_input2facts.py`）：辞典条目 → 带引用的原子事实。工具：`search_dictionary`、`add_atomic_fact`、`remove_atomic_fact`、`update_atomic_fact`。
2. 阶段 2（`prompt_facts2data.py`）：原子事实 → 四表更新。工具：`get_entity`、`create_entity`、`create_timepoint`、`update_timepoint_attr`、`create_timepoints_relationship`、`append_citation`。

相比 v0303 的关键修复：LLM 调用带重试与空响应校验；时间点/关系 ID 显式反馈（禁止模型猜 ID）；同名实体默认复用；关系与引用按语义去重；词条级事务回滚；达到最大轮次抛错记入 `failed_entries.json`。详见 `agent-v0612/README.md`。

批跑入口是 `run.sh`（不要用 notebook 跑正式批跑）：

```bash
cd agent-v0612
./run.sh --tag <版本标签> --model <模型ID> --start 0 --limit 25   # 常用
./run.sh --tag v0613-test --entries "河北兵马大元帅-482,都督府-483" # 指定词条
./run.sh --help                                                  # 完整选项
```

产物按标签隔离到 `records/<标签>/`：结果库 `song_bureaucracy_entries_<标签>.db`、词条记录、`failed_entries.json`、`run.log`。

LLM 配置在 `agent-v0612/.env`（参照 `.env.example`，支持 OpenAI 兼容端点 / OpenRouter / FreeModel 多 profile，`run.sh --provider` 切换）。另有 `kimi_cli_client.py`：以子进程方式调用本机 kimi CLI 作为模型后端（与 `SimpleLLMClient.chat()` 同接口）。

模型选型见 `analysis/v0614_first25_model_comparison.md`：当时结论以 deepseek v4-pro 为基线。

### B. 全量重生成（`prompts/` 技能路线）

`prompts/song_bureaucracy_full_regeneration_agent_skill.md` 定义了绕过两阶段管线、由 agent 直接读写 SQLite 的全量重生成流程。当前最佳库 `v0620-regen-test` 即此路线的产物（后续用 `run_721_833.sh` 把第 721–833 条叠加修补过）。

该路线在四表之外要求写第五张表 **`BuildRecords`**（追溯表）：每条四表数据记录 `target_table / target_id / source_entry / source_page / decision / created_at`，`decision` 必须说明"为什么建、依据原文哪句话"，与四表写入同事务。注意：`agent-v0612/database.py` 不创建此表，只有重生成/校对 agent 会写。

`prompts/song_bureaucracy_entry_curation_agent_prompt.md` 是同风格的逐条校对技能。`fix_evolution_timepoints.py`（根目录）是针对 v0620-regen-test 库的一次性修复脚本（为缺改名时间点的前后演变关系补建时间点），可作同类修复的参考。

### C. 可视化（`vis/`）

```text
vis/data/song_bureaucracy_best.db（只读源）
  -> python3 vis/normalize_times.py      # 年号纪年 -> 公元年，写 NormalizedTimes
  -> vis/data/song_bureaucracy_visualization.db（时间标准化工作库）
  -> python3 vis/serve_visualization_v2.py（只读实时 API，默认 127.0.0.1:8643）
  -> v2 前端运行时从 /api/data 取数（Vue 3 + Vite）
```

- 实时服务在请求时现场装配 payload：`NormalizedTimes` 缺失或 `raw_time` 与 `Timepoints.time` 不一致时即时重标准化，因此 `--db` 可直接指向任意结果库；按主库 + WAL 的 mtime/size 指纹缓存，写入稳定约 2 秒（`--settle-seconds`）后才重建，前端每 1.5 秒轮询 `/api/version`。
- `public/data/song-bureaucracy.json` 只是离线快照：实时接口不可用时前端自动回退，不再是主数据源；需要更新快照时跑 `python3 vis/export_visualization_data.py`。

时间分类规则（详见 `vis/plan.md`）：`exact`（确定到年）/ `range`（明确起止）/ `undated`（宋代无具体年）/ `pre_song`（宋前源流）/ `unresolved`（无法识别）。月日只用于年内排序，不转公历。

v2 前端结构（`src/`）：

- `App.vue`：唯一页面壳，三个视图模式（`时序事件` / `层级结构` / `年表`）+ 全局时间段状态，支持深链 `?view=...&entity=...`。
- `components/SongTimeline.vue`：底部 960–1279 总时间线（年刻度、帝系分段、事件刻度、d3 brush 框选时段）。
- `components/EntityTimeline.vue`：单实体纵向年表（间隔压缩行、1127 分隔、播放演示、与全局时段双向联动）。
- `components/HierarchyView.vue` + `utils/hierarchy.js`：按 `上下级机构/编制隶属/统称与实例` 建树，支持"所选时段/历时全貌"两种范围。
- `components/EventDetailPanel.vue`：时序事件与年表共用的详情面板（关系分组、引文证据展开、沿关系跳转）。
- `components/MainMap.vue`、`components/map/`、`store/`、`data/Data.js`、`PrimaryAxis.vue` 等是 CBDB 模板遗留死代码，未被引用，可清理。

前端命令（在 `vis/song-bureaucracy-visualization-v2/` 下）：

```bash
pnpm live   # 推荐：build 后启动实时只读服务（127.0.0.1:8643）
pnpm dev    # 前端开发（需先在仓库根目录启动 python3 vis/serve_visualization_v2.py，/api 自动代理）
pnpm build  # 构建到 dist/
```

## 数据模型

以实际 SQLite schema 为准（`agent-v0612/database.py` 与 v0620-regen-test 库）。历史文档中的单表方案已过时。

### 四表

- **Entities**：静态实体（`id`、`title`、`type`：`机构` 或 `官职`）。
- **Timepoints**：实体时间线节点（`entity_id`、`time`、`event`、`prev_id`/`succ_id`、`attr_category`、`attr_officer_type`、`attr_grade`）。新实体自动带 `time="未知", event="占位"` 的占位时间点，首次写入真实时间时复用。
- **Relationships**：连接的是**时间点**不是实体。方向约定：`上下级机构` = 上级→下级；`编制隶属` = 机构→官职（可带 `staff_quota`/`staff_type`）；`前后演变` = 来源→后继；`统称与实例` = 统称→实例。
- **Citations**：挂在 Timepoints 或 Relationships 上（`target_table`、`target_id`、`citation`、`quotation`、`note`、`conflict_flag`）。新证据用 `append_citation()`，不要静默覆盖冲突。

### BuildRecords（重生成路线）

第五张追溯表，见上文"全量重生成"一节。分析或可视化脚本不应依赖它一定存在（两阶段管线的库没有此表）。

## 验证方式

仓库没有正式测试套件。修改后至少执行：

```bash
# Python 语法
python3 -m compileall -q agent-v0612
# 不调用 LLM 的冒烟测试（对结构化库只读）
cd agent-v0612 && python smoke_test.py
# 可视化数据层单元测试（改动 vis/*.py 后必跑）
python3 -m unittest vis.test_live_visualization_data vis.test_normalize_times
# 前端
cd vis/song-bureaucracy-visualization-v2 && pnpm build
```

结果库检查（优先对副本执行）：

```bash
sqlite3 <结果库> 'pragma integrity_check;'
sqlite3 <结果库> '.tables'
```

新增或删除数据后检查孤儿时间点、孤儿关系和孤儿引用。`database.py` 连接时已启用 `PRAGMA foreign_keys = ON`，仍建议人工复核。

## 修改约定

- **修改代码前必须先做好 git 备份**（提交或暂存当前工作区改动，确保任何修改都可回退）。这条规则永远有效，任何会话、任何目录的代码改动都要遵守。
- 抽取相关改动只落在 `agent-v0612/`；可视化相关改动只落在 `vis/song-bureaucracy-visualization-v2/`（及 `vis/*.py` 数据脚本）。历史目录用于追溯思路，不要同步修改。
- `database.py` 保持原子 CRUD；跨表联动逻辑优先放在 `utils.py`。
- LLM 工具封装和短期上下文更新放在 `agent_state.py`。
- 提示词行为变更分别落在两个 prompt 模块，不要把长提示词塞进 notebook。
- 关系必须明确方向，并为关系本身保存引用。
- 调试批跑前先用 `--limit` 限制词条数；破坏性调试用数据库的临时副本。
- 直接修改 `vis/data/song_bureaucracy_visualization.db` 后，实时服务会在写入稳定后自动刷新前端；只有源库（如 v0620-regen-test）变化时才需要先同步 `vis/data/song_bureaucracy_best.db` 并重跑 `vis/normalize_times.py`，需要更新离线快照时另跑 `vis/export_visualization_data.py`。
- 不要手工编辑 `agent-v0612/records/` 下的批跑产物，除非任务明确针对生成物。

## 已知问题 / 注意事项

1. `agent-v0612/` 未被 git 跟踪（还有 `outputs/`、`.claude/` 等），重要成果注意自行备份。
2. `agent-v0612/README.md` 部分信息偏旧（如默认结果库路径、`check_syntax.py` 已不存在）；以 `run.sh --help` 和源码为准。
3. 两阶段管线各工具仍是原子写、逐次提交；词条级事务由 `Database.entry_transaction()` 保证，跨词条无整体回滚。
4. v2 前端留有 CBDB 模板死代码（见"可视化"一节），清理不影响运行。
5. v2 的 `datavis.csv` 为历史产物；`dist/` 是构建输出；离线快照 JSON 需手动重跑 `vis/export_visualization_data.py` 才会更新。
6. v0620-regen-test 库有 1 条辞典条目（833 中的 1 条）未被 BuildRecords 覆盖，如需全覆盖请先定位补跑。
7. 早期 `agent/parse_response.py` 是空实现，不属于当前路径。

## 版本演进

- `agent/` → `agent_v0126/` → `agent_v0211/` → `agent_v0303/`：单表方案到四表两阶段管线的演进，均为历史参考。
- `agent-v0612/`：v0303 的修复版，当前抽取实现；批跑产物按版本标签存于 `records/`。
- `prompts/` 重生成路线（2026-06）：跳过两阶段管线直接全量重建，产出当前最佳库 `v0620-regen-test`，并引入 BuildRecords 追溯表。
- `visualization/` → `vis/song-bureaucracy-visualization/`（v1）→ `vis/song-bureaucracy-visualization-v2/`：审查工具到时序图谱的演进，v2 为当前版本。

阅读历史文档时以版本号判断上下文；最终行为以 `agent-v0612/` 源码、v0620-regen-test 实际 schema 和 v2 前端源码为准。
