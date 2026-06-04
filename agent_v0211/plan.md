## 官制数据结构化 Agent 实现规划（v0211）

### 一、整体目标

基于《宋代官制辞典》的 OCR 结果（长期记忆 L1）和结构化数据四表（长期记忆 L2），实现一个两层嵌套的 Agent 系统：  
外层按词条遍历，内层分两步完成从“辞典条目 → 原子事实 → 数据表更新”的自动化处理，并在 `save/` 目录中保留完整的 CoT 记录和中间状态，支持可审计与断点续跑。

---

### 二、架构概览：长期记忆 / 短期记忆 / CoT

- **长期记忆（数据库层）**
  - `L1 辞典数据`：`Database.search_dictionary` 访问 `Song_Bureaucracy_Dictionary`（如表 `chapter8t10`）。
  - `L2 实体数据表`：`Database` 中的 `Entities / Timepoints / Relationships / Citations` 四表，配合 `tools.py` 中的高层接口：
    - 查询：`get_entity`, `entity_to_str`, `format_citations`
    - 写入：`create_entity`, `create_timepoint`, `update_timepoint_attr`, `create_timepoints_relationship`, `append_citation`

- **短期记忆（当前轮内部状态）**
  - `S1 当前查询辞典条目`
    - 当前处理的 `{title, page}` 元信息
    - 已通过 `search_dictionary` 获得的条目列表（可多页）
    - 由 `dict_entry_to_str` 等拼接的「辞典长文本」视图
  - `S2 当前查询 / 更新数据项`
    - 当前轮涉及的实体 ID 集合及其 `get_entity` 视图缓存
    - 已计划 / 已执行的属性修改与关系修改列表

- **CoT / 上下文记录（C）**
  - 结构化的过程日志（仅存内存 + 落盘到 `save/`）：
    - 每次工具调用：函数名、参数摘要、结果摘要、成功 / 失败
    - 模型的关键思考步骤与决策理由
    - 原子事实列表及其处理状态（已应用 / 未应用 / 无法决策）
  - 每处理完一个辞典词条，将该轮的 CoT 记录 + 原子事实 + 最终实体快照序列化保存，便于审计和重放。

---

### 三、外层流程：遍历辞典词条（L1）

1. **预处理阶段（对应时序图中的注释）**
   - 读取配置：辞典库路径 / 表名、结构化库路径等。
   - 初始化单例 `Database(dict_db_path, dict_table, entry_db_path)`。
   - 构建「词条处理进度表」，可选形式：
     - 直接从辞典表中抽取全部 `{id, title, page}`，在内存维护状态；
     - 或维护单独的 JSON / SQLite 进度表，记录：`{dict_id/title/page, status, related_entity_ids, last_updated_at}`。

2. **外层主循环：逐词条处理**
   - 对每一个「待处理词条」：
     - 清空 / 初始化 S1、S2、C：
       - S1 = 当前辞典条目上下文
       - S2 = 当前数据库实体上下文
       - C = 本轮 CoT 记录（空列表）
     - 记录开始事件到 C：`{"step": "start_entry", "title": ..., "page": ...}`。
     - 调用内层处理函数 `process_entry(title, page, db, state)`：
       - 内部完成「辞典补查 + 原子事实抽取」和「数据库查询 + 数据更新」两步。
     - 根据返回结果更新进度表：
       - `status ∈ {"done", "partial", "failed"}`；
       - 记录本轮涉及到的实体 ID 列表、错误信息等。
   - 全部词条处理完毕或达到用户设定的轮次数 / 时间上限后，结束本轮批处理。

---

### 四、内圈第一步：辞典 → 原子事实（S1 + C + L1）

1. **初始化 S1：获取基础辞典条目**
   - 通过 `Database.search_dictionary(title, page)` 获取首个条目。
   - 将返回对象转为文本视图：
     - 调用 `dict_entry_to_str(entry)` 生成便于模型理解的结构化文本。
   - 在 S1 中记录：
     - `current_title`, `current_pages`, `dict_entries`, `dict_text_merged` 等字段。

2. **模型驱动的辞典补查（工具调用决策）**
   - 基于当前 `dict_text_merged` 和任务描述，构建提示词：
     - 说明可用工具：抽象地暴露 `search_dictionary(title, page)` 能力。
     - 要求模型输出：
       - 若需要补查：给出要查询的 `{title, page}` 列表；
       - 若信息已充分：返回「不再需要查询」，并转入事实抽取。
   - Python 侧根据模型输出：
     - 实际调用 `search_dictionary`；
     - 将新结果加入 S1，并用 `dict_entry_to_str` 等追加到 `dict_text_merged`；
     - 在 C 中记录：一次「查询工具调用决策 + 实际调用 + 返回摘要」。

3. **原子事实抽取**
   - 当模型判断信息足够时，提示词切换为「仅根据当前所有辞典文本，输出原子事实」：
     - 原子事实应包含：引用信息、引用原文、涉及实体（或实体组）、时间点描述、属性变化或关系变化等。
     - 允许一条引用对应多个事实。
   - 输出格式建议设计为 JSON List（逻辑结构），例如：
     - `fact_id`
     - `citation_info`（页码、字段来源、辞典原文片段）
     - `entity_candidates`（名称列表；后续与实体表匹配）
     - `time_expression`
     - `change_type`（属性 / 关系）
     - `attr_or_relation_detail`（具体字段）
   - Python 侧：
     - 将该批事实存入 S1 / AgentState（如 `atomic_facts` 字段）；
     - 在 C 中记录一个「atomic_facts」事件；
     - 同时将事实及其生成提示词落盘到 `save/`，便于独立调试第二步。

---

### 五、内圈第二步：原子事实 → 实体数据表（S2 + C + L2）

1. **初始化 S2：查询现有实体状态**
   - 基于原子事实中的 `entity_candidates` 字段：
     - 尝试通过 `Database.get_entity_by_title` 查找已存在实体；
     - 若不存在，则在后续允许模型建议创建新实体。
   - 对于候选实体 ID，调用 `get_entity(db, entity_id)`：
     - 得到实体在所有时间点上的属性与关系信息；
     - 按照文档要求以时间点为主线组织。
   - 在 S2 中建立：
     - `entities_state: Dict[int, get_entity_result]`
     - `pending_facts`, `applied_facts`, `skipped_facts` 等集合。

2. **模型生成“修改数据项决策”**
   - 设计统一的「操作描述」格式，供模型输出和 Python 执行，例如：
     - `op`: `"create_entity" | "create_timepoint" | "update_timepoint_attr" | "create_timepoints_relationship" | "append_citation"`
     - `args`: 对应 `tools.py` 的参数（`entity_id`, `timepoint_id`, `relation_type` 等）
     - `related_fact_ids`: 参考了哪些原子事实
     - `reason`: 简要理由
   - 提示词中提供：
     - 最新的 `entities_state` 概览（可用 `entity_to_str` 生成摘要）；
     - 原子事实列表及其当前状态；
     - 可用高层 API 的说明及约束规则。

3. **映射到 `tools.py` 并执行**
   - Python 侧根据 `op` 字段调用已有高层函数：
     - `create_entity` → `tools.create_entity`
     - `create_timepoint` → `tools.create_timepoint`
     - `update_timepoint_attr` → `tools.update_timepoint_attr`
     - `create_timepoints_relationship` → `tools.create_timepoints_relationship`
     - `append_citation` → `tools.append_citation`
   - 每次调用后：
     - 将调用参数、返回结果摘要、错误信息写入 C；
     - 若调用成功，使用返回的 `get_entity` 结果刷新 S2 中对应实体状态。

4. **多轮迭代与终止条件**
   - 控制逻辑：
     - 每轮将 `pending_facts` + 最新 `entities_state` + 已执行操作摘要 提供给模型；
     - 模型可：
       - 产生新一批操作；
       - 或声明「本轮已完成」，并列出无法处理的事实及原因。
   - 终止条件示例：
     - 模型明确输出 `status = "done"`；
     - 或循环轮数达到上限（如 10 轮），此时将剩余 `pending_facts` 记入 `skipped_facts`，交给人工复核。

---

### 六、轮次收尾与数据持久化

1. **本轮结果汇总**
   - 对本轮涉及到的每个实体，再次调用 `get_entity` 获取最终状态快照。
   - 构造轮次结果对象，包含：
     - `dict_entry_meta`（title, page, id 等）
     - `atomic_facts`（含状态：已应用 / 未应用 / 冲突）
     - `entities_final_state`（按 entity_id 索引）
     - `cot_log`（精简过的过程记录）
   - 序列化保存到 `save/`（例如 `save/{dict_id_or_title}_{timestamp}.json`）。

2. **重置短期记忆，进入下一条**
   - 清理 / 重新初始化 S1、S2、C；
   - 仅保留长期记忆（数据库连接和进度表）；
   - 继续外层主循环处理下一条辞典条目。

---

### 七、代码结构建议

- **已存在模块**
  - `database.py`：已实现四张表的创建与原子级 CRUD 操作。
  - `tools.py`：已实现领域语义级操作（创建词条、时间点、关系，更新属性，追加引用等）以及格式化输出。
  - `doc/Agent文档.0211.md`：已详细描述数据结构和 Agent 两层结构，并提供时序图。

- **建议新增 / 扩展部分**
  - `agent_state`（可先在 `agent.ipynb` 中用简单类或命名元组实现）：
    - 封装 S1（辞典上下文）、S2（实体上下文）、C（CoT 记录）。
  - `process_entry` 流程函数：
    - 输入：`title`, `page`, `db`；
    - 内部依次调用「内圈第一步」和「内圈第二步」；
    - 返回：该轮的结果对象（实体 ID 列表、原子事实状态、错误信息等）。
  - `run_outer_loop`：
    - 在 `agent.ipynb` 或独立脚本中，实现对 833 条（或子集）的批量处理 + 进度管理。
  - Notebook 用途区分：
    - `test.ipynb`：继续用于开发 / 回归测试单个工具与数据库操作。
    - `agent.ipynb`：用于调试单条词条的完整 Agent 流程、检查中间 CoT 和事实抽取质量。

---

### 八、TODO List

- **已完成**
  - [x] 设计并实现《辞典》输入数据库结构，以及查询接口 `Database.search_dictionary`。
  - [x] 设计并实现结构化数据四表（`Entities`, `Timepoints`, `Relationships`, `Citations`）及其原子级 CRUD 接口（`database.py`）。
  - [x] 实现领域语义级高层操作函数：`create_entity`, `create_timepoint`, `update_timepoint_attr`, `create_timepoints_relationship`, `append_citation` 等（`tools.py`）。
  - [x] 在文档中明确数据结构与 Agent 的两层架构，并绘制 Mermaid 时序图（`doc/Agent文档.0211.md`）。
  - [x] 在 `agent_v0211/plan.md` 中固化整体实现规划与任务清单（当前文件）。

- **待实现：Agent 流程与状态管理**
  - [x] 设计并实现 Agent 状态结构（S1 / S2 / C），封装为独立类或一组清晰的数据结构。
  - [ ] 在 `agent.ipynb` 中实现单条词条处理流程骨架（不依赖真实 LLM，先用假数据 / 模拟模型输出，打通数据流）。
  - [ ] 基于真实 LLM，实现「内圈第一步」：辞典补查决策 + 原子事实抽取（含工具调用协议和安全约束）。
  - [ ] 基于真实 LLM，实现「内圈第二步」：数据库更新决策到 `tools.py` API 调用的映射与执行。
  - [ ] 将 CoT 记录（工具调用、关键思考步骤、原子事实状态）序列化到 `save/` 目录，支持审计与重放。

- **待实现：批量处理与工程化**
  - [ ] 实现外层遍历 833 条（或指定子集）辞典词条的批处理脚本 / 函数 `run_outer_loop`，集成进度管理。
  - [ ] 支持断点续跑：进度信息持久化（SQLite / JSON），可从中间某条继续。
  - [ ] 在 `test.ipynb` 中为关键高层操作与 Agent 主要路径补充单元 / 集成测试用例。
  - [ ] 为异常场景（数据库错误、模型输出不合法、工具调用失败）设计健壮的错误处理与回滚策略。

### 实现 TODO List

按照流程来梳理还缺少的部分

构建第一步提示词
  * [x] 提示词框架
  * [x] 上下文-辞典索引（来自数据库接口）
  * [ ] 上下文-已知辞典条目
  * [ ] 上下文-提取的原子事实
  * [ ] 上下文-CoT记录
处理第一步输出
  * [ ] 解析CoT输出
    * [ ] 调用查询工具
    * [ ] 维护原子事实
  * [ ] 维护CoT记录
构建第二步提示词
  * [ ] 提示词框架
  * [ ] 上下文-已知数据项条目
处理第二步输出
  * [ ] 数据表更新工具
