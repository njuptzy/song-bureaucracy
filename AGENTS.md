# Song Bureaucracy AGENTS Guide

## 项目目标

本项目把《宋代官制辞典》的 OCR 文本转成可追溯的宋代官制结构化数据。核心对象分为"机构"和"官职"，需要保留它们的时间变化、相互关系和史料引用。

当前有两条主线：

1. **数据抽取**：`process/extract/` 的逐批提取脚本 + `ew.EntryWriter` 写入累计结果库（现行路线）。
2. **可视化**：`vis/ch1t12-design-vis/` 的原设计稿 SVG 驱动可视化，**这是当前的主要工作方向**。

## 先看这里

- 当前活跃开发：`vis/ch1t12-design-vis/`（可视化主线）和 `process/extract/`（提取主线）。
- 累计结果库：`data/database/song_bureaucracy_entries_ch1t12.db`（7107 实体 / 15792 时间点 / 12789 关系，逐批脚本持续追加）。ch1t7 / ch1t10 是同路线的中间累计库。
- 可视化主线数据源：`data/database/song_bureaucracy_entries_ch1t12.db` + 辞典原文库 `song_bureaucracy_dictionary_ch1t12.db`（辞典表 `chapter1t12`，当前 5252 条）；部署和本地运行均不得再根据旧目录名推断数据源。
- 辞典源库（schema 相同，表名 = 编组名）：`song_bureaucracy_dictionary_ch1.db`（695 条）、`..._ch2t4.db`（1649 条）、`..._ch5t7.db`（1489 条）、`..._ch11t12.db`（606 条）；合并版 `..._ch1t7.db`（3814 条）、`..._ch1t10.db`（4647 条）、`..._ch1t12.db`（5253 条）、`..._ch2t7.db`（3119 条）。均在 `data/database/`。
- 设计依据：`vis/resources/宋代职官可视化设计.pdf`（55 页，北大可视化实验室 2024 设计文档）+ `vis/宋代职官体系可视化打包文件/`（两张 SVG 画板 + 字体）。
- 数据库改动前必须先做文件级备份（`data/database/` 已有大量 `before-*` 备份示例）；`data/database/` 的正式库作为云端快照被 git 跟踪，改动要随批提交。
- `db._recreate_tables()` 会清空结构化结果表，只允许对临时数据库副本执行。

## 目录地图

| 路径 | 用途 | 维护建议 |
| --- | --- | --- |
| `process/extract/` | **现行提取实现**：`ew.py`（EntryWriter 写入辅助）+ 每批一个 `extract_<编组>_<起>_<止>.py` 脚本（约 235 个），直接读写 SQLite，四表 + BuildRecords 同事务 | 主要开发目录之一；新批次仿照最近批次脚本编写 |
| `agent-v0612/` | 两阶段 LLM agent 抽取实现（辞典 → 原子事实 → 四表）、`run.sh` 版本化批跑 | 历史路线，保留可用；源码已纳入 git |
| `agent-v0612/records/<标签>/` | 两阶段管线的批跑产物 | 生成物，不要手工编辑 |
| `agent_framework/` | 共享的 OpenRouter 客户端（`llm.py`） | 稳定 |
| `prompts/` | `song_bureaucracy_entry_extraction_prompt.md`：逐条提取标准，**是 process/extract 脚本路线的事实规范**（ew.py 的保证即按此实现） | 提取路线的规范来源 |
| `vis/ch1t12-design-vis/` | **可视化主线**：原设计稿两张 SVG 画板即界面，Vue 3 管状态、D3 绑真实数据进 SVG 槽位；只读 `server.py`（默认 127.0.0.1:8650，`./run.sh` 启动）；详见其 README.md | 活跃开发 |
| `vis/song-bureaucracy-visualization-v2/` | 前一版可视化（Vue 3 + Vite）：时序事件 / 层级结构 / 年表三视图，数据源仍是 v0620 系 8–10 编库 | 仍维护，共享快照语义 |
| `vis/shared/entity_lifecycle.js` | 两个前端共用的实体存废语义：建置/罢废动词分类、演变互斥、复归与断档判定 | 改动会影响两个前端，须同步测试 |
| `vis/backend/` | 时间标准化、离线导出、实时只读服务、`institution_categories.py`（五大类 + 制度组分类）、`repair_ch2t7_1080_*.py`（1080 元丰改制专项修复，幂等） | 修改后必跑 `vis/tests/` |
| `vis/tests/` | 可视化数据层单元测试 | 修改 `vis/backend/` 后必跑 |
| `vis/docs/` / `vis/reports/` / `vis/resources/` | 流程说明、运行报告、设计 PDF 与参考资源 | 不放业务代码 |
| `vis/legacy/CBDB-Migration-Map/` | v2 复制改造前的独立旧项目，也是各前端 `node_modules` 的共享来源 | 只读参考 |
| `visualization/` | 旧的逐条审查工具（只读 `server.py` + 静态页） | 历史工具，仍可用 |
| `analysis/` | 模型对比报告、结果检查脚本 | 分析材料 |
| `process/ocr-results/` | OCR 清洗与各编切分建库脚本 | 输入预处理层 |
| `data/` | 外部数据（辞典库、结果库、备份）；`data/database/` 正式库显式跟踪 | 只入不删 |
| `agent/`、`agent_v0126/`、`agent_v0211/`、`agent_v0303/`、`agent_test/` | 历史抽取版本 | 追溯思路用，不要同步修改 |
| `doc/`、`plans/` | 设计文档与演进记录 | 阅读时注意版本号 |

## 数据管线

### A. 逐批脚本提取（`process/extract/`，现行路线）

每个批次一个脚本（如 `extract_11t12_502_521.py`），按 `prompts/song_bureaucracy_entry_extraction_prompt.md` 的标准把辞典条目直接写入累计结果库：

- 写入统一走 `ew.py` 的 `EntryWriter`，保证：四表 + BuildRecords 同事务；实体复用必须 `title` 和 `type` 都一致；`entity()/timepoint()/relationship()` 的 `quotation`（辞典原文逐字片段）强制必填；同 `time` 时间点优先复用；占位节点机制（`time="未知", event="占位"`）；citation 完全重复时不重复追加。
- 目标库用环境变量 `SONG_ENTRY_DB` 指定，默认写累计库（近期批次默认 `song_bureaucracy_entries_ch1t12.db`）；同编组脚本通过 `importlib` 复用前一批的辅助函数。
- 执行前先备份结果库文件；一批一提交（辞典库与结果库一起提交）。

### B. 两阶段 LLM 抽取（`agent-v0612/`，历史路线）

辞典条目逐条进入两阶段循环，每阶段最多 10 轮，模型输出 `"Tasks All Finished"` 结束：阶段 1（`prompt_input2facts.py`）辞典 → 原子事实；阶段 2（`prompt_facts2data.py`）原子事实 → 四表更新。批跑入口 `run.sh`，产物按标签隔离到 `records/<标签>/`。详见 `agent-v0612/README.md` 与 `run.sh --help`。

### C. 全量重生成与 BuildRecords

BuildRecords 是第五张追溯表：`target_table / target_id / source_entry / source_page / decision / created_at`，`decision` 必须说明"为什么建、依据原文哪句话"，与四表写入同事务。`agent-v0612/database.py` 不创建此表；`ew.EntryWriter` 与重生成/校对 agent 会写。

### D. 可视化（`vis/`）

主线 `vis/ch1t12-design-vis/`（详见其 README.md）：

- 设计稿两张 SVG 画板（层级画板 4-01、编制画板 4-02）**就是界面**，前端不仿画，只替换 SVG 文字槽位并绑定交互；字体直接读设计包的 TTF/OTF。
- `server.py` 只读 API（默认 127.0.0.1:8650）：`/api/data`（ch1t12 实体、时间点、层级/编制关系、引用、辞典原文）、`/api/design/*.svg|ttf|otf`、`/api/health`。`./run.sh` 一键构建并启动。
- `src/components/DesignTemplateCanvas.vue`（约 3000 行）是核心：单年年末快照选择、层级/编制画板切换、五大类机构 + 制度组导航、虚拟分组（不冒充历史层级边）、空间展开模式、编制按钮展开、三司职能分组、行内详情卡。
- 工具逻辑在 `src/utils/*.js`，各有对应 `.test.mjs`（共 83 个用例），测试命令见"验证方式"。
- `node_modules` 与 legacy 项目共用软链，**不要在本目录跑 `pnpm install`**。

旧线 v2（`vis/song-bureaucracy-visualization-v2/`）数据链路不变：

```text
vis/data/song_bureaucracy_best.db（只读源，v0620 系 8–10 编库）
  -> python3 vis/backend/normalize_times.py -> vis/data/song_bureaucracy_visualization.db
  -> python3 vis/backend/serve_visualization_v2.py（只读实时 API，默认 127.0.0.1:8643）
  -> v2 前端运行时从 /api/data 取数
```

- 数据契约：关系的纪年依据是 `relations[].periods`（离散段列表，空数组 = 时间未明），**不要**改回两端 min/max 合并的连续跨度。
- 年末快照语义（存废沿时间链累积、罢废不自动复活、关系取最近一次归属、年代未明不混入）由 `vis/shared/entity_lifecycle.js` 与各前端 `utils/snapshot.js` 共同实现，两个前端必须保持一致。

时间分类规则（详见 `vis/docs/time-normalization.md`）：`exact` / `range` / `undated` / `pre_song` / `unresolved`。月日只用于年内排序，不转公历。

## 数据模型

以实际 SQLite schema 为准（`agent-v0612/database.py` 与各累计结果库）。历史文档中的单表方案已过时。

### 四表

- **Entities**：静态实体（`id`、`title`、`type`：`机构` 或 `官职`）。
- **Timepoints**：实体时间线节点（`entity_id`、`time`、`event`、`prev_id`/`succ_id`、`attr_category`、`attr_officer_type`、`attr_grade`）。新实体自动带 `time="未知", event="占位"` 的占位时间点，首次写入真实时间时复用。
- **Relationships**：连接的是**时间点**不是实体。方向约定：`上下级机构` = 上级→下级；`编制隶属` = 机构→官职（可带 `staff_quota`/`staff_type`）；`前后演变` = 来源→后继；`统称与实例` = 统称→实例。
- **Citations**：挂在 Timepoints 或 Relationships 上（`target_table`、`target_id`、`citation`、`quotation`、`note`、`conflict_flag`）。新证据用 `append_citation()`，不要静默覆盖冲突。

### BuildRecords

第五张追溯表，见上文"全量重生成与 BuildRecords"一节。分析或可视化脚本不应依赖它一定存在（两阶段管线的库没有此表）。

## 验证方式

```bash
# Python 语法
python3 -m compileall -q agent-v0612 process/extract
# 可视化数据层单元测试（改动 vis/backend/*.py 后必跑，共 44 个用例）
python3 -m unittest vis.tests.test_live_visualization_data vis.tests.test_normalize_times vis.tests.test_institution_categories
# ch1t12-design-vis 工具函数测试（改动其 src/utils 后必跑，共 83 个用例）
cd vis/ch1t12-design-vis && node --test src/utils/*.test.mjs
# 前端构建
cd vis/ch1t12-design-vis && pnpm build
```

结果库检查（优先对副本执行）：

```bash
sqlite3 <结果库> 'pragma integrity_check;'
sqlite3 <结果库> '.tables'
```

新增或删除数据后检查孤儿时间点、孤儿关系和孤儿引用。`database.py` 与 `ew.py` 连接时已启用 `PRAGMA foreign_keys = ON`，仍建议人工复核。

## 修改约定

- **修改代码前必须先做好 git 备份**（提交或暂存当前工作区改动，确保任何修改都可回退）。这条规则永远有效，任何会话、任何目录的代码改动都要遵守。
- 提取相关改动落在 `process/extract/`；可视化主线改动落在 `vis/ch1t12-design-vis/`；共享快照语义改动落在 `vis/shared/` 且须同步两个前端。历史目录用于追溯思路，不要同步修改。
- 关系必须明确方向，并为关系本身保存引用（quotation 必填）。
- 数据库改动先做文件级备份；破坏性调试用数据库的临时副本。
- 结果库一批一提交，备份文件不提交（`data/database/` 的 `before-*` 备份是本地安全网）。
- 不要手工编辑 `agent-v0612/records/` 下的批跑产物，除非任务明确针对生成物。

## 已知问题 / 注意事项

1. 各前端（v2 与 ch1t12-design-vis）的 `node_modules` 都是指向 legacy 项目的共享符号链接，**不要跑 `pnpm install`**；依赖变更用 `pnpm install --lockfile-only`。
2. ch1t12-design-vis 的 SVG 中只绑定了设计稿预留槽位的实体；设计稿没有槽位的实体不会凭空新增图形（见其 README "当前边界"）。
3. ch11t12 辞典现有 606 条，提取已提交至第 521 条，剩余批次待续。
4. v2 的离线快照 JSON 需手动重跑 `vis/backend/export_visualization_data.py` 才会更新。
5. v0620-regen-test 库（v2 数据源）有 1 条辞典条目未被 BuildRecords 覆盖，属历史遗留。
6. 早期 `agent/parse_response.py` 是空实现，不属于当前路径。

## 版本演进

- `agent/` → `agent_v0126/` → `agent_v0211/` → `agent_v0303/`：单表方案到四表两阶段管线的演进，均为历史参考。
- `agent-v0612/`（2026-06）：v0303 的修复版两阶段 LLM 管线。
- `prompts/` 重生成路线（2026-06）：直接全量重建，引入 BuildRecords 追溯表。
- `process/extract/` 脚本路线（2026-07 起）：按提取 prompt 逐批写确定性脚本，累计库 ch1t7 → ch1t10 → ch1t12；同期完成 ch2t7 库与 1080 年元丰改制专项修复。
- `visualization/` → `vis/song-bureaucracy-visualization/`（v1）→ `vis/song-bureaucracy-visualization-v2/` → `vis/ch1t12-design-vis/`（2026-08，原设计稿 SVG 驱动，当前主线）。

阅读历史文档时以版本号判断上下文；最终行为以 `process/extract/` 脚本、ch1t12 实际 schema 和 ch1t12-design-vis 源码为准。
