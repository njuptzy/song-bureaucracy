# Song Bureaucracy AGENTS Guide

## 项目目标

本项目尝试把《宋代官制辞典》的 OCR 文本转成可追溯的宋代官制结构化数据。核心对象分为“机构”和“官职”，需要保留它们的时间变化、相互关系和史料引用。

仓库包含多轮实验代码。除非任务明确要求维护历史版本，新的实现和修复应优先落在 `agent_v0303/`。

## 先看这里

- 当前最完整的实现位于 `agent_v0303/`。
- 当前流程入口仍是 `agent_v0303/agent.ipynb`，还没有独立 CLI、依赖锁文件或自动化测试套件。
- `data/` 被根目录 `.gitignore` 忽略，但本地工作区通常已恢复外部数据。
- notebook 中的 Windows 硬编码路径已替换为相对路径，适配 macOS / Linux / Windows。
- notebook 中的硬编码 API key 已移除，改为通过环境变量读取。共享仓库前仍需确认 `.env` 不被提交。
- `db._recreate_tables()` 会清空结构化结果表。只允许对临时数据库副本执行。

## 目录地图

| 路径 | 用途 | 维护建议 |
| --- | --- | --- |
| `process/ocr-results/` | OCR 清洗 notebook：读取 MinerU 结果、修复目录、用 Trie 切分正文并导出半结构化 JSON/CSV | 输入预处理层 |
| `agent/` | 最早期单表方案：直接修改按时间段拆分的官制条目 | 历史参考 |
| `agent_v0126/` | 单表方案增强版：增加时间索引、时间点扩展和引用记录思路 | 历史参考 |
| `agent_v0211/` | 四表模型的第一版：`Entities / Timepoints / Relationships / Citations`，含高层工具和设计文档 | 迁移参考 |
| `agent_v0303/` | 当前版本：两阶段提示词、运行时状态、工具调用解析和批处理 notebook | 主要开发目录 |
| `agent_test/` | 早期数据库与 LLM 实验 notebook | 历史参考，不是自动测试 |
| `analysis/` | 批处理日志、分析 notebook 和结果数据库快照 | 生成物与分析材料 |
| `doc/` | 数据建模、流程设计、问题复盘和汇报材料 | 理解设计演进 |
| `plans/` | 四表模型设计草案 | 注意与实际代码核对 |

## 当前架构

```text
MinerU OCR
  -> process/ocr-results/*.ipynb
  -> 外部 data/ 中的半结构化辞典数据
  -> 辞典 SQLite 表 chapter8t10
  -> agent_v0303/agent.ipynb 外层逐条遍历
      -> 阶段 1: 辞典条目 -> 原子事实
      -> 阶段 2: 原子事实 -> 四表更新
  -> 结构化 SQLite 结果库
  -> analysis/ 中的日志与结果分析
```

### 当前模块职责

| 文件 | 职责 |
| --- | --- |
| `agent_v0303/database.py` | SQLite 双连接管理；查询辞典；维护四张结果表的原子 CRUD |
| `agent_v0303/utils.py` | 领域级高层操作；组合 CRUD；格式化辞典和实体上下文 |
| `agent_v0303/agent_state.py` | 管理当前轮上下文、原子事实、CoT 记录；解析模型 JSON；把工具调用路由到高层接口 |
| `agent_v0303/prompt_input2facts.py` | 构建阶段 1 提示词：补查辞典并提取原子事实 |
| `agent_v0303/prompt_facts2data.py` | 构建阶段 2 提示词：查询实体并写入时间点、关系、引用 |
| `agent_v0303/agent.ipynb` | 配置 LLM，遍历辞典索引，执行两个阶段的最多 10 轮循环，并落盘每条词条的过程记录 |
| `agent_v0303/config.py` | 统一计算项目根目录、数据库路径和 `save/` 目录，支持环境变量覆盖 |
| `agent_v0303/llm_client.py` | OpenRouter 兼容 LLM 客户端，替代早期 `graph_agent` 外部依赖入口 |
| `agent_v0303/test_cot_1.py` | 保存若干手工 CoT 样例，不是可执行测试 |

### 两阶段 Agent 流程

阶段 1 只负责把辞典文本提炼成带引用的原子事实：

1. `AgentState.append_input_entry()` 加载初始辞典条目。
2. `build_prompt_input2facts()` 注入辞典索引、已加载文本、已有原子事实和 CoT。
3. 模型可调用 `search_dictionary`、`add_atomic_fact`、`remove_atomic_fact`、`update_atomic_fact`。
4. 模型返回 `"Tasks All Finished"` 后进入阶段 2。

阶段 2 负责把原子事实写入结构化数据库：

1. `AgentState.prepare_for_update()` 保留原子事实，清空实体上下文和 CoT。
2. `build_prompt_facts2data()` 注入实体索引、原子事实、已加载实体和 CoT。
3. 模型可调用 `get_entity`、`create_entity`、`create_timepoint`、`update_timepoint_attr`、`create_timepoints_relationship`、`append_citation`。
4. 每个领域工具在写入后重新读取相关实体，使下一轮提示词看到最新状态。
5. 模型返回 `"Tasks All Finished"` 后保存该词条的处理记录。

## 实际数据模型

以 `agent_v0303/database.py` 和 `analysis/song_bureaucracy_entries_v0304.db` 的实际 schema 为准。历史文档中的单表方案和 `EntityIntervals` 名称已经过时。

### `Entities`

静态实体表：

| 字段 | 含义 |
| --- | --- |
| `id` | 实体 ID |
| `title` | 机构或官职名称 |
| `type` | `机构` 或 `官职` |

### `Timepoints`

实体时间线节点：

| 字段 | 含义 |
| --- | --- |
| `entity_id` | 所属实体 |
| `time`, `event` | 时间文本和事件描述 |
| `prev_id`, `succ_id` | 同一实体内的前后节点指针 |
| `attr_category` | 细分类，如官司名、军职名 |
| `attr_officer_type` | 官职分类，如差遣官或阶官 |
| `attr_grade` | 官品描述 |

新实体会自动创建 `time="未知", event="占位"` 的时间点。第一次写入真实时间时，`create_timepoint()` 会复用该占位节点。

### `Relationships`

关系连接的是时间点，不是实体：

| `relation_type` | 推荐方向：`subject_id -> object_id` |
| --- | --- |
| `上下级机构` | 上级机构 -> 下级机构 |
| `编制隶属` | 机构 -> 官职 |
| `前后演变` | 来源实体时间点 -> 后继实体时间点 |
| `统称与实例` | 统称模板 -> 具体实例 |

`编制隶属` 可额外记录 `staff_quota` 和 `staff_type`。

### `Citations`

引用挂在 `Timepoints` 或 `Relationships` 上：

| 字段 | 含义 |
| --- | --- |
| `target_table`, `target_id` | 被引用的时间点或关系 |
| `citation` | 出处 |
| `quotation` | 原文 |
| `note` | 考证说明 |
| `conflict_flag` | 是否存在冲突 |

新增属性、关系和时间点时应尽量同步写入引用。已有结论出现新证据时使用 `append_citation()`，不要静默覆盖史料冲突。

## 运行前置条件

当前仓库在本机已有数据，运行前仍需要确认：

1. `data/database/song_bureaucracy_dictionary.db` 存在，并确认包含 `chapter8t10` 表。
2. LLM 已迁移到本仓库的 `agent_framework/`，基于 OpenRouter API，无需额外安装 `graph_agent`。
3. 通过环境变量注入 `OPENROUTER_API_KEY`（以及可选的 `OPENROUTER_MODEL`），不要写入 notebook。可参考 `agent_v0303/.env.example`。
4. `agent_v0303/config.py` 默认使用 `data/database/song_bureaucracy_entries_v0304.db`；可用 `SONG_DICT_DB_PATH`、`SONG_ENTRY_DB_PATH`、`SONG_DICT_TABLE` 覆盖。
5. 使用临时结构化数据库副本调试破坏性流程，避免覆盖 `data/database/song_bureaucracy_entries_v0304.db`。

当前 Python 模块使用同目录导入，例如 `from database import Database`。直接调试时从 `agent_v0303/` 目录启动，或把该目录加入 `PYTHONPATH`。

## 验证方式

仓库没有正式测试套件。修改后至少执行静态解析：

```bash
python3 - <<'PY'
from pathlib import Path
import ast

for path in sorted(Path(".").glob("**/*.py")):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print("Python syntax OK")
PY
```

检查结果数据库时，优先对副本执行：

```bash
sqlite3 analysis/song_bureaucracy_entries_v0304.db '.tables'
sqlite3 analysis/song_bureaucracy_entries_v0304.db '.schema'
sqlite3 analysis/song_bureaucracy_entries_v0304.db 'pragma integrity_check;'
```

新增或删除数据后，还应检查孤儿时间点、孤儿关系和孤儿引用。`database.py` 已在连接时启用 `PRAGMA foreign_keys = ON`，但仍建议人工复核。

## 修改约定

- 新功能默认只改 `agent_v0303/`。历史目录用于追溯思路，不要求同步维护。
- `database.py` 保持原子 CRUD；跨表联动逻辑优先放在 `utils.py`。
- LLM 工具封装和短期上下文更新放在 `agent_state.py`。
- 提示词行为变更分别落在两个 prompt 模块，不要把长提示词塞进 notebook。
- 关系必须明确方向，并为关系本身保存引用。
- 调试批处理前先把 `todo_dict_entries` 限制为少量词条。
- 不要手工编辑 `analysis/nohup.20260304.log` 或结果数据库快照，除非任务明确针对生成物。

## 已知问题

这些问题尚未修复，后续修改时应优先评估：

1. ~~notebook 中存在硬编码 API key。~~ **已修复**：改为通过 `OPENROUTER_API_KEY` 环境变量读取。
2. ~~`agent_v0303/agent.ipynb` 仍有硬编码 Windows 路径~~ **已修复**：已替换为相对路径。
3. `_recreate_tables()` 是破坏性操作；`agent_v0303/agent.ipynb` 默认已注释，只有临时测试库可手动启用。
4. ~~SQLite 外键没有显式开启~~ **已修复**：`Database.__init__` 中已启用 `PRAGMA foreign_keys = ON`。
5. ~~`AgentState.append_input_entry()` 使用 `split("-")` 拆分 `title-page`~~ **已修复**：已改为 `rsplit("-", 1)`。
6. ~~`AtomicFactsContext` 内部使用整数 ID，但更新和删除工具注解使用字符串 ID~~ **已修复**：`tool_remove_atomic_fact` / `tool_update_atomic_fact` 已强制将 `fact_id` 转为字符串。
7. ~~阶段 2 提示词提到了 `get_entity_by_title`~~ **已修复**：提示词已改为指引使用 `get_entity`。
8. 领域工具每个原子写操作都会单独提交事务；多步更新失败时没有整体回滚。
9. ~~`create_entity()` 允许同名实体~~ **已修复**：同名同类型实体默认复用已有实体；如确认为“同名不同体”，可显式传 `allow_duplicate=True`。`create_timepoints_relationship()` 仍未阻止重复关系，调用方需要先查询确认。
10. 早期 `agent/parse_response.py` 仍是空实现，但不属于当前 `v0303` 主路径。

## 版本演进

- `agent/`：以辞典 `title-page` 为索引，直接维护单表属性和时间段。
- `agent_v0126/`：增加时间切分、扩展时间点和引用记录思路。
- `agent_v0211/`：把静态实体、时间点、关系、引用拆成四表，并形成双层 Agent 设计。
- `agent_v0303/`：实现“辞典 -> 原子事实 -> 四表更新”的两阶段循环，并完成批量运行实验。

阅读历史文档时，以版本号判断上下文；最终行为以 `agent_v0303/` 源码和实际 SQLite schema 为准。
