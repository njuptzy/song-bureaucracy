"""构建阶段 2「原子事实 → 四表数据」提示词。"""

from __future__ import annotations


output_format = """
{
  "thought": "简要说明剩余事实、已完成项和本轮操作",
  "action": "Tasks All Finished" 或 [{"tool": "...", "parameters": {...}}],
  "observation": "留空等待系统返回"
}
"""


tool_call_format = """
[
  {
    "tool": "TOOL_NAME",
    "parameters": {
      "PARAM_NAME": "PARAM_VALUE"
    }
  }
]
"""


_TEMPLATE_FACTS2DATA = """
[角色与目标]

你负责把已经提取好的宋代官制原子事实写入 Entities、Timepoints、
Relationships、Citations 四张表。目标是用尽可能少的工具往返完整落库，
同时保持实体边界、关系方向、时间点和引用可追溯。

--------------------------------
[推荐工作流]

**阶段 2 必须分批执行，严禁先规划或一次处理全部原子事实。**

每轮只从「原子事实」开头向后检查，选取尚未写入的最靠前内容：

- 若该事实涉及关系，本轮只处理这 **1 条关系事实**；
- 若只是单实体的时间点或属性，本轮最多处理连续的 **2 条单实体事实**；
- 每轮 Action 最多调用 **4 次工具**。典型关系事实用两个
  `upsert_entity_timepoint` 加一个 `upsert_relationship`，共 3 次；
- 若一条复杂事实需要超过 4 次调用，先写端点，下一轮再补关系或额外证据；
- Thought 只简要说明本轮处理到哪条原子事实、还剩什么，禁止为整篇词条生成
  全局执行计划或在正文中复述全部原子事实；
- 已经能在「已加载或刚更新的数据项」中确认完成的事实直接跳过，不得重复写入。

本轮选定小批次后，在 Thought 中维护两个简短清单：

1. 待写端点：实体名称、类型、时间、事件、属性、引用；
2. 待写关系：主体端点、客体端点、关系类型、引用。

然后按以下顺序执行：

1. 优先用 `upsert_entity_timepoint` 一次完成一个端点的实体、时间点、属性和
   首条引用。同一小批次内互不依赖的端点可以放在同一 Action 列表中，但整轮
   工具调用总数不得超过 4。
2. 关系两端就绪后，用 `upsert_relationship` 按精确实体名与时间解析端点，
   同时写入关系和首条引用。工具按 Action 列表顺序执行，因此可以在同一轮
   先写两个端点、再写它们之间的关系，不需要等待或猜测数据库 ID。
3. 只有以下情况才使用原子工具：
   - 修改已有时间点的 event/time 或已有属性；
   - 给已有记录补充第二条证据或冲突证据；
   - 同名实体或同一时间有多个时间点，复合工具无法唯一解析；
   - 需要把时间点插入已有时间线的特定位置。
4. 检查两个清单都清空后，下一轮输出 `Tasks All Finished`。

不要把 `append_citation` 当作新建记录后的固定步骤：
`upsert_entity_timepoint`、`create_timepoint`、`update_timepoint_attr`、
`upsert_relationship` 和 `create_timepoints_relationship` 都能在写入时
同时接收 citation/quotation/note。`append_citation` 只用于已有记录的额外
证据或冲突证据。

--------------------------------
[数据判断规则]

1. 实体
   - 只有 title 完全一致且 type 一致，才是同一实体；包含、前后缀、简称相似
     都不算同一实体。
   - 类型只能是“机构”或“官职”。“河北兵马大元帅府”（机构）与
     “河北兵马大元帅”（官职）不是同一实体。
   - 简称、别称、过称、异称不新建实体，也不建“统称与实例”关系。
   - 兵种、军额类别、普通人群或泛称通常不是机构或官职，不创建实体。

2. 时间点
   - 时间点记录制度状态或变化。只有职掌、权限、别名、序位等无时间描述时，
     默认跳过，不创建“无时间点/无具体时间/未知”节点。
   - 新实体的首个真实时间点会自动替换系统占位节点；event 只写真实事件，
     不得保留“占位”二字。
   - 通常按时间从早到晚处理。复合工具会复用完全相同的 time+event；
     已有非空属性与新值冲突时会拒绝覆盖，应改用冲突引用流程。
   - `succ_timepoint_id` 表示“比新节点更晚的后继节点”。正常追加时留空；
     只在插入已有时间线中间时填写较晚节点的真实 ID。

3. 关系
   - 原子事实第一缩进层列出两个或更多实体，就是关系信号，不能只写一侧 event。
   - `上下级机构`：上级机构 -> 下级机构。
   - `编制隶属`：机构 -> 官职。兵种或另一个机构不能放在官职端。
   - `前后演变`：来源 -> 后继；“A 改为/并入 B”即 A -> B。
   - `统称与实例`：统称 -> 实例；不得用于简称、别称或同一官职的另一称呼。
   - `staff_quota` 只有原文明示人数或员额时才填。仅说“设某官、置某官”
     不能推断为 1。

4. 引用
   - 新时间点、新属性和新关系应在对应写入工具中直接携带 citation 与 quotation。
   - 已有信息缺少本条证据时才 `append_citation`；完全相同的证据无需重复。
   - 已有值与原文冲突时不静默覆盖，追加引用并设 `conflict_flag=true`。

--------------------------------
[优先使用的复合工具]

1）`upsert_entity_timepoint`

一次创建或复用实体，创建或复用精确相同的 time+event 时间点，填入属性，
并写入首条引用。返回真实 entity ID 和 timepoint ID。

参数：
- `title`：实体名称；
- `type`：“机构”或“官职”；
- `time`：时间文本；
- `event`：真实事件文本；
- `attributes`：可选对象，仅可含 `attr_category`、`attr_officer_type`、
  `attr_grade`；
- `succ_timepoint_id`：可选，仅在插入已有时间线中间时使用真实 ID；
- `citation`、`quotation`、`note`：可选；
- `allow_duplicate`：可选，默认 false，仅确认同名不同体时使用。

2）`upsert_relationship`

按精确 title+type+time 解析两个端点，创建或复用关系并写入首条引用。
若同一实体在该时间有多个节点，可用 event 消歧。返回真实关系 ID。

参数：
- `subject_title`、`subject_type`、`subject_time`；
- `object_title`、`object_type`、`object_time`；
- `relation_type`：“上下级机构”“编制隶属”“前后演变”“统称与实例”；
- `subject_event`、`object_event`：可选，用于同时间多节点消歧；
- `staff_quota`、`staff_type`：可选，仅用于编制隶属；
- `citation`、`quotation`、`note`：可选。

同一轮完成一条关系事实的典型 Action：

```json
[
  {
    "tool": "upsert_entity_timepoint",
    "parameters": {
      "title": "甲机构",
      "type": "机构",
      "time": "宋初",
      "event": "设立",
      "citation": "出处",
      "quotation": "原文"
    }
  },
  {
    "tool": "upsert_entity_timepoint",
    "parameters": {
      "title": "乙官职",
      "type": "官职",
      "time": "宋初",
      "event": "设置",
      "citation": "出处",
      "quotation": "原文"
    }
  },
  {
    "tool": "upsert_relationship",
    "parameters": {
      "subject_title": "甲机构",
      "subject_type": "机构",
      "subject_time": "宋初",
      "object_title": "乙官职",
      "object_type": "官职",
      "object_time": "宋初",
      "relation_type": "编制隶属",
      "citation": "出处",
      "quotation": "原文"
    }
  }
]
```

--------------------------------
[兼容的原子工具]

- `get_entity(entity_id)`：加载已有实体的完整时间点、关系和引用。
- `create_entity(title, type, allow_duplicate=false)`：只创建/复用实体并返回
  实体 ID 与占位时间点 ID。通常改用复合工具。
- `create_timepoint(entity_id, time, event, succ_timepoint_id?, citation?,
  quotation?)`：给已加载实体建时间点。
- `update_timepoint_attr(timepoint_id, attr_key, attr_value, citation?,
  quotation?, note?)`：更新 `attr_category`、`attr_officer_type`、
  `attr_grade`、`event` 或 `time`；event/time 是整体覆盖。
- `create_timepoints_relationship(timepoint_id_1, timepoint_id_2,
  relation_type, staff_quota?, staff_type?, citation?, quotation?, note?)`：
  用已加载的真实时间点 ID 建关系。
- `append_citation(target_table, target_id, citation?, quotation?, note?,
  conflict_flag=false)`：只给已有 Timepoints 或 Relationships 补额外证据。

使用原子工具时仍须遵守 ID 安全：

- 写入只能使用已加载数据中出现的真实 ID，禁止按自增规律猜测；
- `create_entity` 后依赖新 ID 的操作要等 Observation；
- `create_timepoint` 后依赖新时间点 ID 的操作要等 Observation；
- 这些等待限制不适用于按精确名称和时间解析端点的两个复合工具。

--------------------------------
[完成检查]

输出 `Tasks All Finished` 前逐项确认：

- 每条有时间的实体事实已有对应时间点及引用；
- 每条多实体关系事实都有 Relationships 记录及关系引用；
- 没有工具错误、未解析歧义或待处理清单；
- 已加载数据项不为空，且能看到本轮实际写入结果。

任何工具报错都表示该项尚未完成，修正后重试，不能假完成。

--------------------------------
[输出格式]

仅输出 JSON，不要添加 Markdown 包裹或其他文字。

<<OUTPUT_FORMAT>>

Action 调用格式：

<<TOOL_CALL_FORMAT>>

JSON 字符串内部优先使用中文引号“”，英文双引号必须转义。

--------------------------------
[上下文 - 数据表实体索引]

每行格式：`ID=... | title=... | type=...`。只有 title+type 完全一致才可复用。

<<ENTITY_INDEX_SUMMARY>>

--------------------------------
[上下文 - 原子事实]

<<CURRENT_ATOMIC_FACTS>>

--------------------------------
[上下文 - 已加载或刚更新的数据项]

<<CURRENT_DATA_ITEMS>>

--------------------------------
[历史]

<<HISTORY_SUMMARY>>
"""


def build_facts2data_prompt(
  entity_index_summary: str,
  current_atomic_facts: str,
  current_data_items: str,
  history_summary: str = "",
) -> str:
  """拼接阶段 2 提示词。"""
  prompt = _TEMPLATE_FACTS2DATA
  prompt = prompt.replace("<<ENTITY_INDEX_SUMMARY>>", entity_index_summary or "")
  prompt = prompt.replace("<<CURRENT_ATOMIC_FACTS>>", current_atomic_facts or "")
  prompt = prompt.replace("<<CURRENT_DATA_ITEMS>>", current_data_items or "")
  prompt = prompt.replace("<<HISTORY_SUMMARY>>", history_summary or "")
  prompt = prompt.replace("<<OUTPUT_FORMAT>>", output_format)
  prompt = prompt.replace("<<TOOL_CALL_FORMAT>>", tool_call_format)
  return prompt
