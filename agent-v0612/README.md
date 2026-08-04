# agent-v0612

基于 `agent_v0303` 的当前修复版。目标是继续使用原来的“两阶段 Agent + 四表 Schema”，但把 0304 批跑日志和 v0612 首批试跑中暴露出来的流程问题补齐。

正式批跑以 `run.sh --tag ...` 为入口；结果库和 records 默认按标签隔离在
`records/<tag>/`。

## 已修复的问题

### 1. LLM 调用不再静默返回 None

v0304 里外部 `LLMTool` 可能把失败调用包装成 `None`，notebook 再用多层下标取 `choices[0]`，导致整条词条崩溃。

现在改为 `SimpleLLMClient.chat()` 直接返回非空文本，并内置重试、退避和空内容校验。`agent.py` 与 `agent.ipynb` 均不再使用裸取 `["choices"][0]` 的结构。

### 2. 时间点 ID 和关系 ID 都显式反馈

旧流程里 `create_timepoint` 不返回新时间点 ID，LLM 会按自增规律猜，尤其在占位时间点复用时很容易猜错。

现在：

- `create_entity` 返回默认占位时间点 ID；
- `create_timepoint` 返回实际新时间点 ID；
- `create_timepoints_relationship` 返回实际关系 ID；
- 阶段 2 提示词明确禁止猜 ID，也禁止用 `"待定"` 作为关系引用的 `target_id`。

### 3. 同名实体默认复用

`create_entity(title, type)` 默认复用同名同类型实体，避免重跑词条时继续生成一串空壳实体。只有确认属于“同名不同体”时，才显式传 `allow_duplicate=True`。

### 4. 关系和引用去重

数据库层现在会复用语义相同的关系：

```text
subject_id + object_id + relation_type + staff_quota + staff_type
```

引用也会按以下字段去重：

```text
target_table + target_id + citation + quotation + note + conflict_flag
```

这只会阻止后续重复写入，不会自动清洗已经存在于旧结果库中的重复行。

### 5. 词条级事务回滚

`Database.entry_transaction()` 会把一个词条的写库操作包成一个事务。阶段 1 或阶段 2 达到最大轮次仍未完成、LLM 持续故障、或流程抛异常时，该词条本轮写入会整体回滚，减少半写入实体和空壳残留。

注意：工具调用返回业务错误时会进入下一轮让模型修正；只有流程最终失败并抛异常时才触发整条回滚。

### 6. 最大轮次不再静默进入下一阶段

阶段 1 或阶段 2 在 `MAX_llm_loop_count` 轮内没有输出 `"Tasks All Finished"`，现在会直接抛错并记录到 `save/failed_entries.json`，不会把未完成状态当作成功继续提交。

### 7. `agent.py` 与 notebook 同步

`agent.py` 已同步 `agent.ipynb` 的主流程逻辑，支持不用 notebook 也能审查和运行同一套流程。

### 8. API key 改为本地环境变量

默认 provider 为 OpenCode Go，模型是 `deepseek-v4-flash`，请求端点为
`https://opencode.ai/zen/go/v1/chat/completions`。`.gitignore` 已忽略 `.env`；
在 <https://opencode.ai/auth> 获取 Go API key 后，只需填写
`OPENCODE_GO_API_KEY`。不同 provider 的 key 不再互相回退，避免把一个平台的
凭据误发给另一个平台。OpenCode Go 默认使用 SSE 流式响应，以 120 秒原始
读取超时持续接收推理片段，不通过延长超时掩盖长响应问题。

### 9. 阶段 2 复合写入，减少工具往返

阶段 2 优先使用两个复合工具：

- `upsert_entity_timepoint`：一次完成实体、时间点、属性和首条引用；
- `upsert_relationship`：按精确实体名与时间解析两端，一次完成关系和首条引用。

同一 Action 可以先写多个端点，再顺序建立关系，不再为新实体 ID、时间点
ID 和关系引用各等一轮。旧的原子工具仍保留，专门处理既有记录修改、同名
或同时间歧义、额外证据与冲突证据。每个复合调用在词条事务内部使用独立
savepoint，中途失败不会留下半条写入。

默认批跑保留完整辞典与实体索引，只压缩已加载实体中的长引文和较早 CoT，
避免每一轮重复回灌相同大段文本。records 会额外记录两个阶段各自的轮数。

## 当前日志状态

当前本地 `agent-v0612/nohup.v0612.batch1.log` 对应的是前 50 条试跑，不是全量 1500 条：

```text
开始 50 条
完成 50 条
失败 0 条
JSON 解析失败 0 次
LLM 词条级重试 0 次
主要工具错误：未找到关系 id=待定 9 次
```

`id=待定` 已通过“关系 ID 显式反馈 + 提示词禁止占位 target_id”修复。已有结果库中的重复关系、重复引用属于历史运行结果，代码修复不会原地改库。

## 使用

```bash
cd agent-v0612
cp .env.example .env
# 编辑 .env，填入 OPENCODE_GO_API_KEY
python smoke_test.py
```

默认运行即使用 OpenCode Go / DeepSeek V4 Flash：

```bash
./run.sh --tag opencode-go-v4-flash-test --limit 1
```

切换 FreeModel GPT-5.5：

```bash
# 先在 .env 填 FREEMODEL_API_KEY
./run.sh --provider freemodel --tag freemodel-gpt55-test --limit 1
```

主流程可在 Jupyter 中打开 `agent.ipynb` 顺序执行，也可审查/运行同步后的 `agent.py`。正式批跑前建议先把 `todo_dict_entries` 限制为少量条目。

## 验证

不调用 LLM 的静态检查：

```bash
python3 -m compileall -q agent-v0612
python3 agent-v0612/smoke_test.py
```

结果库检查：

```bash
sqlite3 data/database/song_bureaucracy_entries_v0612.db 'pragma integrity_check;'
sqlite3 data/database/song_bureaucracy_entries_v0612.db '.tables'
```
