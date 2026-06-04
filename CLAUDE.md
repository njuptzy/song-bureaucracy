# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在本仓库中工作时的指引。

## 项目概述

本项目是一个多轮实验，尝试将《宋代官制辞典》的 OCR 文本转换为可追溯的结构化历史数据。核心对象是"机构"和"官职"，需要保留它们的时间变化、相互关系和史料引用。

**当前活跃实现：** `agent_v0303/`。除非明确要求维护历史版本，所有新工作都应在此目录下进行。

## 常用命令

本项目没有正式的构建系统、测试套件或依赖锁文件。项目由 Jupyter Notebook 和 Python 脚本驱动。

**修改后验证 Python 语法：**
```bash
python3 - <<'PY'
from pathlib import Path
import ast
for path in sorted(Path(".").glob("**/*.py")):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print("Python 语法检查通过")
PY
```

**运行冒烟测试（不调用 LLM，对结构化数据库只读）：**
```bash
cd agent_v0303 && python smoke_test.py
```

**检查结构化结果数据库：**
```bash
sqlite3 data/database/song_bureaucracy_entries_v0304.db '.tables'
sqlite3 data/database/song_bureaucracy_entries_v0304.db '.schema'
sqlite3 data/database/song_bureaucracy_entries_v0304.db 'pragma integrity_check;'
```

**运行主处理 Notebook：**
在 Jupyter 中打开 `agent_v0303/agent.ipynb`。该 Notebook 遍历辞典索引条目，运行两阶段 Agent 循环（每阶段最多 10 轮），并将每条记录保存到 `agent_v0303/save/`。

**环境配置：**
复制 `agent_v0303/.env.example` 到 `agent_v0303/.env` 并设置 `OPENROUTER_API_KEY`。可选覆盖项：`OPENROUTER_MODEL`、`SONG_DICT_DB_PATH`、`SONG_ENTRY_DB_PATH`、`SONG_DICT_TABLE`。

## 架构

### 数据流程

```
MinerU OCR 输出
  → process/ocr-results/（预处理 Notebook）
  → data/database/song_bureaucracy_dictionary.db（数据源，表：chapter8t10）
  → agent_v0303/agent.ipynb（外层遍历辞典索引）
      → 阶段 1：辞典条目 → 原子事实
      → 阶段 2：原子事实 → 结构化数据库更新
  → data/database/song_bureaucracy_entries_v0304.db（结构化结果）
  → analysis/（批处理日志、分析 Notebook）
```

### 两阶段 Agent 设计

Agent 不是聊天机器人，而是一个结构化循环：LLM 输出 JSON 格式的"思维-行动-观察"链，框架执行工具、更新状态，并将观察结果反馈到下一轮提示词中。

**阶段 1 —— `prompt_input2facts.py`：** 从辞典条目中提取原子事实。
- 输入：辞典文本、已有原子事实、CoT 历史
- LLM 工具：`search_dictionary`、`add_atomic_fact`、`remove_atomic_fact`、`update_atomic_fact`
- 输出：带引用的原子事实列表，供阶段 2 使用
- 关键规则：仅在出现显式交叉引用如"详见'XX'条"时才调用 `search_dictionary`。不要查询每个被提到的机构。

**阶段 2 —— `prompt_facts2data.py`：** 将原子事实写入结构化数据库。
- 输入：原子事实、实体索引、已加载实体状态、CoT 历史
- LLM 工具：`get_entity`、`create_entity`、`create_timepoint`、`update_timepoint_attr`、`create_timepoints_relationship`、`append_citation`
- 输出：更新后的 Entities、Timepoints、Relationships 和 Citations 表

两个阶段均在 LLM 输出 `"Tasks All Finished"` 或达到 10 轮上限时终止。

### 核心模块职责

| 文件 | 职责 |
|------|------|
| `agent_v0303/database.py` | SQLite 双连接管理器。四张表的原子 CRUD。**初始化时启用 `PRAGMA foreign_keys = ON`。** `_recreate_tables()` 是破坏性操作，仅用于临时数据库副本。 |
| `agent_v0303/utils.py` | 领域级高层操作：`create_entity`、`create_timepoint`、`update_timepoint_attr`、`create_timepoints_relationship`、`append_citation`、`get_entity`、`entity_to_str`。跨表联动逻辑在此实现。 |
| `agent_v0303/agent_state.py` | 持有 `Database` 实例作为长期记忆。管理单条处理过程中的短期记忆：已加载辞典条目、原子事实、已加载数据项、CoT 链。解析 LLM JSON 响应并路由工具调用。 |
| `agent_v0303/prompt_input2facts.py` | 构建阶段 1 提示词。纯字符串拼接，不直接调用 LLM。 |
| `agent_v0303/prompt_facts2data.py` | 构建阶段 2 提示词。纯字符串拼接，不直接调用 LLM。 |
| `agent_v0303/config.py` | 从仓库布局解析路径。支持通过环境变量覆盖数据库路径和表名。 |
| `agent_v0303/llm_client.py` | 最小化 OpenRouter 兼容客户端。包装 `agent_framework.llm.OpenRouterClient`，支持本地 `.env` 加载和遗留的 `LLMTool` 兼容层。 |
| `agent_framework/llm.py` | 所有 Agent 版本共享的 OpenRouter 客户端。加载 `.env` 文件，提供 `chat()` / `chat_raw()` 方法。 |

### 四表 Schema

权威 Schema 定义在 `agent_v0303/database.py` 和实际的 `analysis/song_bureaucracy_entries_v0304.db` 中。

- **Entities**：静态身份（`id`、`title`、`type`：机构 或 官职）
- **Timepoints**：实体时间线节点，含 `prev_id`/`succ_id` 指针，以及 `attr_category`、`attr_officer_type`、`attr_grade`
- **Relationships**：**时间点之间**的二元连接（不是实体之间）。类型：上下级机构、编制隶属、前后演变、统称与实例。`编制隶属` 可携带 `staff_quota` 和 `staff_type`。
- **Citations**：附着在 Timepoints 或 Relationships 上的学术证据（`target_table`、`target_id`、`citation`、`quotation`、`note`、`conflict_flag`）

**重要行为：**
- `create_entity()` 自动创建占位时间点（`time="未知"`、`event="占位"`）。第一次真正的 `create_timepoint()` 调用会复用该占位节点，而不是插入新行。
- `create_entity()` 默认按 `(title, type)` 去重。仅在确认"同名不同体"时传入 `allow_duplicate=True`。
- 每个写入工具都会刷新相关实体上下文，确保下一轮提示词看到最新状态。

### 模块导入约定

`agent_v0303/` 中的 Python 模块使用同目录导入（例如 `from database import Database`）。从 `agent_v0303/` 目录启动，或将其加入 `PYTHONPATH`。Notebook 和 `smoke_test.py` 自动处理路径插入。

## 修改约定

- **新工作仅在 `agent_v0303/` 中进行。** 历史目录（`agent/`、`agent_v0126/`、`agent_v0211/`）仅用于参考；不要向它们同步更改。
- 保持 `database.py` 为原子 CRUD。跨表联动逻辑放在 `utils.py`。
- LLM 工具封装和短期上下文更新放在 `agent_state.py`。
- 提示词行为变更放入两个提示词模块。不要把长提示词内联到 Notebook 中。
- 关系必须明确方向，并为关系本身保存引用。
- 调试批处理时，先将 `todo_dict_entries` 限制为少量条目。
- 不要手工编辑 `analysis/nohup.20260304.log` 或结果数据库快照，除非任务明确针对生成物。
- 破坏性调试请使用结构化数据库的临时副本；绝不要对主结果数据库运行 `_recreate_tables()`。
