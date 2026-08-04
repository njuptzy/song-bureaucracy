from typing import Optional, Dict, Any, List
from database import Database
import json
import re

def _escape_inner_quotes(json_str: str) -> str:
  """
  修复 JSON 字符串值内未转义的英文双引号（LLM 常见输出错误，如
  "thought": "涉及实体"河北兵马大元帅府"（已存在..."）。

  逐字符扫描：在字符串内遇到 `"` 时向前看，若跳过空白后的下一个字符不是
  JSON 结构字符（, : } ]）或输入结尾，则视为内容引号，转义为 \\"。
  仅为 best-effort 修复，修复后仍解析失败的由调用方按原样报错。
  """
  out = []
  in_string = False
  stack = []  # 括号上下文栈：'{' 或 '['
  i = 0
  n = len(json_str)
  while i < n:
    ch = json_str[i]
    if not in_string:
      if ch == '"':
        in_string = True
      elif ch in '{[':
        stack.append(ch)
      elif ch in '}]' and stack:
        stack.pop()
      out.append(ch)
    elif ch == '\\':
      out.append(ch)
      if i + 1 < n:
        out.append(json_str[i + 1])
        i += 1
    elif ch == '"':
      j = i + 1
      while j < n and json_str[j] in ' \t\r\n':
        j += 1
      if j >= n or json_str[j] in ':}]':
        in_string = False
        out.append(ch)
      elif json_str[j] == ',':
        # `",` 既可能是真正的字符串结束，也可能是值内部的伪代码，如
        # create_entity("都督", "官职")（first20 批跑中 8 轮因此解析失败）。
        # 数组上下文中元素间逗号是常态，按结束处理；对象上下文中向前看
        # 逗号后的 token：必须是后跟冒号的 "key"（或可作键的字面量开头）
        # 才视为真正的字符串结束。
        is_close = True
        if not stack or stack[-1] == '{':
          k = j + 1
          while k < n and json_str[k] in ' \t\r\n':
            k += 1
          if k < n and json_str[k] == '"':
            m = k + 1
            while m < n and json_str[m] != '"':
              if json_str[m] == '\\':
                m += 1
              m += 1
            m += 1
            while m < n and json_str[m] in ' \t\r\n':
              m += 1
            if m < n and json_str[m] != ':':
              is_close = False
          else:
            # 对象中逗号后只能是 "key"；其他字符说明这是值内的伪代码逗号
            is_close = False
        if is_close:
          in_string = False
          out.append(ch)
        else:
          out.append('\\"')
      else:
        out.append('\\"')
    else:
      out.append(ch)
    i += 1
  return ''.join(out)


def load_json_string(input: str):
  pattern = r'```json\s*\n(.*?)\n\s*```'
  matches = re.findall(pattern, input, re.DOTALL)
  json_str = ""
  if len(matches) >= 1:
    json_str = matches[0]
  else:
    json_str = input

  try:
    return json.loads(json_str)
  except json.JSONDecodeError:
    # v0612 批跑中约 31 轮因字符串值内的未转义引号解析失败，先修复再试一次
    return json.loads(_escape_inner_quotes(json_str))

def search_dictionary(db: Database, title: str, page: str) -> Dict[str, Any]:
  """
  查询《辞典》原始文献
  
  Args:
    db: Database 实例
    title: 词条名称
    page: 页码
    
  Returns:
    词条对象结构，如果出错则返回 {"error": "..."}
  """
  return db.search_dictionary(title, page)

def dict_entry_to_str(entry: Dict[str, Any]) -> str:
  """
  将《辞典》词条对象转为结构化文本
  
  Args:
    entry: 词条对象
    
  Returns:
    格式化后的文本字符串
  """
  fields_texts = []
  for key, value in entry.get("fields", {}).items():
    fields_texts.append(f"{key}: {value}")
  
  return f"""# {entry["title"]}
文本来源：{entry["catalog"]} {entry["page"]}页
基本介绍：{entry["text"]}
{"\n".join(fields_texts)}
"""

def get_entity(db: Database, entity_id: int) -> Dict[str, Any]:
  """
  查询数据项：获取一个词条下的全部信息
  
  从数据库中获取：
  - Entities 表中对应的条目信息
  - Timepoints 中以对应 id 为关联的所有时间点数据项
  - Relationships 中以上述时间点为关联的所有关系数据项
  - Citations 中以上述时间点和关系为关联的所有引用依赖数据项
  
  按照时间点组织信息，即当前词条在每个时间点发生了什么变化，依赖引用信息是什么。
  
  Args:
    db: Database 实例
    entity_id: 词条 id
    
  Returns:
    格式化的词条信息，如果出错则返回 {"error": "..."}
  """
  try:
    # 获取词条基本信息
    entity = db.get_entity_by_id(entity_id)
    if entity is None:
      return {"error": f"未找到词条 id={entity_id}"}
    
    # 获取所有时间点
    timepoints = db.get_timepoints_by_entity_id(entity_id)
    
    # 构建结果结构
    result = {
      "entity": entity,
      "timepoints": []
    }
    
    # 为每个时间点收集相关信息
    for tp in timepoints:
      timepoint_id = tp["id"]
      
      # 获取该时间点的关系
      relationships = db.get_relationships_by_timepoint_id(timepoint_id)
      
      # 获取该时间点的引用
      citations = db.get_citations_by_target("Timepoints", timepoint_id)
      
      # 构建时间点信息（包含继承的属性）
      tp_info = {
        "id": timepoint_id,
        "time": tp["time"],
        "event": tp["event"],
        "attributes": {},
        "relationships": [],
        "citations": []
      }
      
      # 收集属性（只记录非空的属性，表示在该时间点发生了变化）
      if tp["attr_category"] is not None:
        tp_info["attributes"]["attr_category"] = tp["attr_category"]
      if tp["attr_officer_type"] is not None:
        tp_info["attributes"]["attr_officer_type"] = tp["attr_officer_type"]
      if tp["attr_grade"] is not None:
        tp_info["attributes"]["attr_grade"] = tp["attr_grade"]
      
      # 收集关系信息
      for rel in relationships:
        rel_id = rel["id"]
        # 获取关系的引用
        rel_citations = db.get_citations_by_target("Relationships", rel_id)
        
        # 获取相关实体的信息
        other_timepoint_id = rel["object_id"] if rel["subject_id"] == timepoint_id else rel["subject_id"]
        other_tp = db.get_timepoint_by_id(other_timepoint_id)
        other_entity = None
        if other_tp:
          other_entity = db.get_entity_by_id(other_tp["entity_id"])
        
        rel_info = {
          "id": rel_id,
          "subject_id": rel["subject_id"],
          "object_id": rel["object_id"],
          "relation_type": rel["relation_type"],
          "staff_quota": rel["staff_quota"],
          "staff_type": rel["staff_type"],
          "citations": rel_citations,
          "other_entity_id": other_entity["id"] if other_entity else None,
          "other_entity_title": other_entity["title"] if other_entity else None
        }
        tp_info["relationships"].append(rel_info)
      
      # 收集引用信息
      tp_info["citations"] = citations
      
      result["timepoints"].append(tp_info)
    
    return result
  except Exception as e:
    return {"error": str(e)}


def format_citations(citations: List[Dict[str, Any]], indent: str = "  ") -> List[str]:
  """
  格式化引用信息列表为文本行

  Args:
    citations: 引用信息列表
    indent: 缩进字符串，默认为 "  "

  Returns:
    格式化后的文本行列表
  """
  lines = []
  for citation in citations:
    citation_text = citation.get("citation", "")
    quotation_text = citation.get("quotation", "")
    note_text = citation.get("note", "")
    conflict_mark = " [冲突]" if citation.get("conflict_flag") else ""

    # 构建引用信息字符串
    citation_info_parts = []
    if quotation_text:
      citation_info_parts.append(f"原文：{quotation_text}")
    if citation_text:
      citation_info_parts.append(f"({citation_text})。")
    if note_text:
      citation_info_parts.append(f"备注：{note_text}")

    citation_info = " ".join(citation_info_parts)
    lines.append(f"{indent}* {citation_info}{conflict_mark}")

  return lines


_CITATION_LABEL_RE = re.compile(
  r'(\d+)\s*页[^“”"]*[“"]?([^“”"]+?)[”"]?\s*词条\s*[“"]?([^“”"]+?)[”"]?\s*标签'
)


def _extract_citation_label(citation_text: str) -> str:
  """从 citation 字符串里提取 '<页码> <词条> <标签>' 短标签，供 compact 模式使用。

  匹配不上就回退到 citation 前 30 字符（去掉 '《辞典》' 等前缀）。
  """
  if not citation_text:
    return ""
  m = _CITATION_LABEL_RE.search(citation_text)
  if m:
    return f"{m.group(1)}页·{m.group(2)}·{m.group(3)}"
  # fallback：去掉常见前缀后取前 30 字
  trimmed = citation_text
  for prefix in ("《宋代官制辞典》", "《辞典》"):
    if trimmed.startswith(prefix):
      trimmed = trimmed[len(prefix):]
      break
  return trimmed[:30].strip() or citation_text[:30]


def format_citations_compact(citations: List[Dict[str, Any]], indent: str = "  ") -> List[str]:
  """compact 模式：把整组 citations 折成一行 '引用 (N): 标签1; 标签2; ...'。

  不展开 quotation 原文（最大压缩点）。若有冲突标记，在行尾追加 [含冲突]。
  """
  if not citations:
    return []
  labels = []
  has_conflict = False
  for c in citations:
    if c.get("conflict_flag"):
      has_conflict = True
    labels.append(_extract_citation_label(c.get("citation", "")))
  conflict_mark = " [含冲突]" if has_conflict else ""
  return [f"{indent}* 引用 ({len(citations)}): {'; '.join(labels)}{conflict_mark}"]


def entity_to_str(entity_data: Dict[str, Any], detail_level: str = "full") -> str:
  """
  将 get_entity 返回的数据格式化为文本字符串
  
  按照时间点组织信息，对于每个时间点，仅包含在这个时间点改变的属性，不考虑前后的继承问题。
  
  Args:
    entity_data: get_entity 返回的数据结构
    
  Returns:
    格式化后的文本字符串

    # 名称 (索引编号)
    类型
    ## 时间点1文本 (索引编号)
    时间点事件
    条目具体类别名称 attr_category
    官制类别 attr_officer_type
    品级信息
    引用
      * 引用文本 (引用信息)
    ### 上下级关系
    上级机构：
      * 机构1名称 (索引编号)
    下级机构：
      * 机构2名称 (索引编号)
    引用
      * 引用文本 (引用信息)
    ### 编制隶属关系
    编制信息：
      * 官职名称 (索引编号) 官职类别 官职人数
    引用
      * 引用文本 (引用信息)
    隶属机构：
      * 机构名称 (索引编号)
    ### 前后演变关系
    源自：
      * 条目名称 (索引编号)
    演化成为：
      * 条目名称 (索引编号)
    引用
      * 引用文本 (引用信息)
    ### 统称与实例关系
    统称模板：
      * 条目名称 (索引编号)
    统称实例：
      * 条目名称 (索引编号)
    引用
      * 引用文本 (引用信息)
  """
  if "error" in entity_data:
    return f"错误：{entity_data['error']}"

  entity = entity_data["entity"]
  timepoints = entity_data["timepoints"]
  entity_type = entity.get('type', '未设置')

  # compact 模式用短标签格式，full 模式保留完整 quotation
  _render_citations = format_citations_compact if detail_level == "compact" else format_citations
  
  # 构建词条基本信息
  lines = [
    f"# {entity['title']} (索引：{entity['id']})",
    f"类型：{entity_type}"
  ]
  
  # 遍历每个时间点
  for tp in timepoints:
    lines.append(f"## 时间点：{tp.get('time', '')} (索引：{tp['id']})")
    lines.append(f"事件：{tp.get('event', '')}")
    
    # 只显示在该时间点改变的属性
    attrs = tp.get("attributes", {})
    
    # 显示所有属性（不区分机构/官职）
    if "attr_category" in attrs and attrs["attr_category"] is not None:
      lines.append(attrs["attr_category"])
    if "attr_officer_type" in attrs and attrs["attr_officer_type"] is not None:
      lines.append(f"官制类别：{attrs['attr_officer_type']}")
    if "attr_grade" in attrs and attrs["attr_grade"] is not None:
      lines.append(f"品级信息：{attrs['attr_grade']}")
    
    # 时间点的引用
    citations = tp.get("citations", [])
    if citations:
      lines.append("引用")
      lines.extend(_render_citations(citations, indent="  "))
    
    # 按关系类型分组处理
    # 1. 上下级关系
    superiors = []
    subordinates = []
    hierarchy_citations = []
    
    # 2. 编制隶属关系
    staff_info = []  # 机构视角：编制信息
    affiliated = []  # 官职视角：隶属机构
    staff_relation_citations = []
    
    # 3. 前后演变关系
    evolution_prev = []
    evolution_succ = []
    evolution_citations = []
    
    # 4. 统称与实例关系
    template = []
    instance = []
    template_instance_citations = []
    
    # 收集所有关系
    for rel in tp.get("relationships", []):
      rel_type = rel.get("relation_type", "")
      other_entity_title = rel.get("other_entity_title")
      other_entity_id = rel.get("other_entity_id")
      rel_id = rel.get("id")
      rel_citations = rel.get("citations", [])
      
      if rel_type == "上下级机构":
        if rel.get("subject_id") == tp["id"]:
          # 当前时间点是主体，对方是客体（下级）
          if other_entity_title and other_entity_id:
            subordinates.append(f"  * {other_entity_title} (索引：{other_entity_id})")
        else:
          # 当前时间点是客体，对方是主体（上级）
          if other_entity_title and other_entity_id:
            superiors.append(f"  * {other_entity_title} (索引：{other_entity_id})")
        if rel_citations:
          hierarchy_citations.extend(rel_citations)
      
      elif rel_type == "编制隶属":
        if entity_type == "机构":
          # 机构视角：编制信息
          if other_entity_title and other_entity_id:
            staff_type = rel.get("staff_type", "")
            staff_quota = rel.get("staff_quota")
            quota_str = f"{staff_quota}" if staff_quota is not None else ""
            staff_info.append(f"  * {other_entity_title} (索引：{other_entity_id}) 官职类型：{staff_type} 人数：{quota_str}")
        else:
          # 官职视角：隶属机构
          if other_entity_title and other_entity_id:
            affiliated.append(f"  * {other_entity_title} (索引：{other_entity_id})")
        if rel_citations:
          staff_relation_citations.extend(rel_citations)
      
      elif rel_type == "前后演变":
        if rel.get("subject_id") == tp["id"]:
          if other_entity_title and other_entity_id:
            evolution_succ.append(f"  * {other_entity_title} (索引：{other_entity_id})")
        else:
          if other_entity_title and other_entity_id:
            evolution_prev.append(f"  * {other_entity_title} (索引：{other_entity_id})")
        if rel_citations:
          evolution_citations.extend(rel_citations)
      
      elif rel_type == "统称与实例":
        if rel.get("subject_id") == tp["id"]:
          if other_entity_title and other_entity_id:
            instance.append(f"  * {other_entity_title} (索引：{other_entity_id})")
        else:
          if other_entity_title and other_entity_id:
            template.append(f"  * {other_entity_title} (索引：{other_entity_id})")
        if rel_citations:
          template_instance_citations.extend(rel_citations)
    
    # 输出上下级关系
    if superiors or subordinates:
      lines.append("### 上下级关系")
      if superiors:
        lines.append("上级机构：")
        lines.extend(superiors)
      if subordinates:
        lines.append("下级机构：")
        lines.extend(subordinates)
      if hierarchy_citations:
        lines.append("引用")
        lines.extend(_render_citations(hierarchy_citations, indent="  "))
    
    # 输出编制隶属关系
    if staff_info or affiliated or staff_relation_citations:
      lines.append("### 编制隶属关系")
      if staff_info:
        lines.append("编制信息：")
        lines.extend(staff_info)
      if affiliated:
        lines.append("隶属机构：")
        lines.extend(affiliated)
      if staff_relation_citations:
        lines.append("引用")
        lines.extend(_render_citations(staff_relation_citations, indent="  "))
    
    # 输出前后演变关系
    if evolution_prev or evolution_succ or evolution_citations:
      lines.append("### 前后演变关系")
      if evolution_prev:
        lines.append("源自：")
        lines.extend(evolution_prev)
      if evolution_succ:
        lines.append("演化成为：")
        lines.extend(evolution_succ)
      if evolution_citations:
        lines.append("引用")
        lines.extend(_render_citations(evolution_citations, indent="  "))
    
    # 输出统称与实例关系
    if template or instance or template_instance_citations:
      lines.append("### 统称与实例关系")
      if template:
        lines.append("统称模板：")
        lines.extend(template)
      if instance:
        lines.append("统称实例：")
        lines.extend(instance)
      if template_instance_citations:
        lines.append("引用")
        lines.extend(_render_citations(template_instance_citations, indent="  "))
    
    lines.append("")
  
  return "\n".join(lines)


def create_entity(db: Database, title: str, type: str, allow_duplicate: bool = False) -> Dict[str, Any]:
  """
  创建新词条
  
  向 Entities 表中添加项；需要词条名称和类别（机构或官职）；默认会复用同名同类型实体，
  避免重跑词条时重复插入空壳。若确认该词条与现有词条并非指向同一个机构或官职（同名不同体），
  可显式设置 allow_duplicate=True；最好能够在名称上体现区别。
  创建 Entity 项会同步向 Timepoints 中添加一个占位时间点，设置 time 为 "未知" 并设置 event 为 "占位"。
  
  Args:
    db: Database 实例
    title: 词条名称
    type: 词条类型（'机构' 或 '官职'）
    allow_duplicate: 是否允许创建同名同类型实体
    
  Returns:
    创建该词条后，自动调用词条查询功能，返回查询结果
  """
  try:
    # 检查是否已存在同名同类型词条；默认复用最早创建的实体。
    existing = db.get_entity_by_title(title)
    same_type = [entity for entity in existing if entity.get("type") == type]
    if same_type and not allow_duplicate:
      result = get_entity(db, same_type[0]["id"])
      result["created"] = False
      return result

    # 创建新词条
    entity_id = db.insert_entity(title, type)

    # 创建占位时间点
    placeholder_id = db.insert_timepoint(
      entity_id=entity_id,
      time="未知",
      event="占位"
    )

    # 返回查询结果，附带占位时间点 ID，供工具层反馈给 LLM（时间点 ID 不可猜测）
    result = get_entity(db, entity_id)
    result["created"] = True
    result["default_timepoint_id"] = placeholder_id
    return result
  except Exception as e:
    return {"error": str(e)}


def create_timepoint(
  db: Database,
  entity_id: int,
  succ_timepoint_id: Optional[int],
  time: str,
  event: str,
  citation: Optional[str] = None,
  quotation: Optional[str] = None
) -> Dict[str, Any]:
  """
  创建词条时间点
  
  创建指定词条的时间点，需要指定该时间点的插入位置（在指定的时间点之前，如果留空在插入在最后）。
  如果当前词条的时间点仅包含占位时间点（即 time="未知", event="占位"）则将替换该时间点，并继承原占位时间点的其他属性值。
  
  Args:
    db: Database 实例
    entity_id: 词条 id
    succ_timepoint_id: 后一个时间点 id，如果为 None 则插入到最后面
    time: 时间点文本
    event: 事件描述
    citation: 引文出处（可选）
    quotation: 史料原文内容（可选）
    
  Returns:
    创建该时间点后，查询该词条并返回结果
  """
  try:
    # 验证词条是否存在
    entity = db.get_entity_by_id(entity_id)
    if entity is None:
      return {"error": f"未找到词条 id={entity_id}"}
    
    # 获取所有时间点
    timepoints = db.get_timepoints_by_entity_id(entity_id)
    
    # 检查是否只有占位时间点
    if len(timepoints) == 1 and timepoints[0]["time"] == "未知" and timepoints[0]["event"] == "占位":
      # 替换占位时间点，继承原属性值
      placeholder_id = timepoints[0]["id"]
      placeholder = timepoints[0]
      db.update_timepoint(
        timepoint_id=placeholder_id,
        time=time,
        event=event,
        prev_id=placeholder.get("prev_id"),
        succ_id=placeholder.get("succ_id")
      )
      # 添加引用依赖（如果有）
      if citation or quotation:
        db.insert_citation(
          target_table="Timepoints",
          target_id=placeholder_id,
          citation=citation,
          quotation=quotation
        )
      # 保留原有的属性值（attr_category, attr_officer_type, attr_grade）
      # 复用占位时间点：新时间点 ID 即原占位时间点 ID，必须显式带回，
      # LLM 无法按自增规律猜出这个 ID
      result = get_entity(db, entity_id)
      result["new_timepoint_id"] = placeholder_id
      return result
    
    # 确定新时间点的前后指针
    prev_id = None
    succ_id = None
    
    if succ_timepoint_id is None:
      # 插入到最后面：找到最后一个时间点（succ_id 为 None 的）
      last_tp = None
      for tp in timepoints:
        if tp.get("succ_id") is None:
          last_tp = tp
          break
      
      if last_tp:
        # 新时间点的 prev_id 指向最后一个时间点
        prev_id = last_tp["id"]
        # 插入新时间点
        timepoint_id = db.insert_timepoint(
          entity_id=entity_id,
          time=time,
          event=event,
          prev_id=prev_id,
          succ_id=None
        )
        # 更新最后一个时间点的 succ_id
        db.update_timepoint(
          timepoint_id=prev_id,
          succ_id=timepoint_id
        )
        # 添加引用依赖（如果有）
        if citation or quotation:
          db.insert_citation(
            target_table="Timepoints",
            target_id=timepoint_id,
            citation=citation,
            quotation=quotation
          )
      else:
        # 如果没有找到最后一个时间点（链式结构不完整），直接插入
        timepoint_id = db.insert_timepoint(
          entity_id=entity_id,
          time=time,
          event=event,
          prev_id=None,
          succ_id=None
        )
        # 添加引用依赖（如果有）
        if citation or quotation:
          db.insert_citation(
            target_table="Timepoints",
            target_id=timepoint_id,
            citation=citation,
            quotation=quotation
          )
    else:
      # 在指定时间点之前插入
      # 验证后一个时间点是否存在
      succ_tp = db.get_timepoint_by_id(succ_timepoint_id)
      if succ_tp is None:
        return {"error": f"未找到后一个时间点 id={succ_timepoint_id}"}
      if succ_tp["entity_id"] != entity_id:
        return {"error": f"后一个时间点不属于该词条"}
      
      # 新时间点的 succ_id 指向 succ_timepoint_id
      succ_id = succ_timepoint_id
      # 新时间点的 prev_id 指向 succ_tp 的 prev_id
      prev_id = succ_tp.get("prev_id")
      
      # 插入新时间点
      timepoint_id = db.insert_timepoint(
        entity_id=entity_id,
        time=time,
        event=event,
        prev_id=prev_id,
        succ_id=succ_id
      )
      
      # 更新 succ_tp 的 prev_id 指向新时间点
      db.update_timepoint(
        timepoint_id=succ_timepoint_id,
        prev_id=timepoint_id
      )
      
      # 如果 prev_id 不为 None，更新前一个时间点的 succ_id
      if prev_id is not None:
        db.update_timepoint(
          timepoint_id=prev_id,
          succ_id=timepoint_id
        )
      
      # 添加引用依赖（如果有）
      if citation or quotation:
        db.insert_citation(
          target_table="Timepoints",
          target_id=timepoint_id,
          citation=citation,
          quotation=quotation
        )
    
    # 返回查询结果，附带新时间点 ID，供工具层反馈给 LLM
    result = get_entity(db, entity_id)
    result["new_timepoint_id"] = timepoint_id
    return result
  except Exception as e:
    return {"error": str(e)}


def update_timepoint_attr(
  db: Database,
  timepoint_id: int,
  attr_key: str,
  attr_value: str,
  citation: Optional[str] = None,
  quotation: Optional[str] = None,
  note: Optional[str] = None
) -> Dict[str, Any]:
  """
  更新时间点属性
  
  更新时间点上的属性值，同时需要写入引用依赖信息。
  
  Args:
    db: Database 实例
    timepoint_id: 时间点 id
    attr_key: 属性键（'attr_category', 'attr_officer_type', 'attr_grade', 'event', 'time'）
    attr_value: 属性值。更新 'event'/'time' 时为整体覆盖，需传入完整的新文本
    citation: 引文出处
    quotation: 史料原文内容
    note: 考证说明或备注

  Returns:
    更新该时间点后，查询该词条并返回结果
  """
  try:
    # 验证时间点是否存在
    timepoint = db.get_timepoint_by_id(timepoint_id)
    if timepoint is None:
      return {"error": f"未找到时间点 id={timepoint_id}"}

    entity_id = timepoint["entity_id"]

    # 验证属性键。v0612 起允许更新 event/time：职掌、任期等描述性信息
    # 没有专属 attr 列，归宿就是 event 文本（v0612 批跑中 LLM 多次因此被拒）
    valid_attrs = ["attr_category", "attr_officer_type", "attr_grade", "event", "time"]
    if attr_key not in valid_attrs:
      return {"error": f"无效的属性键: {attr_key}，必须是 {valid_attrs} 之一"}
    
    # 更新属性
    update_params = {attr_key: attr_value}
    db.update_timepoint(timepoint_id, **update_params)
    
    # 添加引用依赖
    if citation or quotation or note:
      db.insert_citation(
        target_table="Timepoints",
        target_id=timepoint_id,
        citation=citation,
        quotation=quotation,
        note=note
      )
    
    # 返回查询结果
    return get_entity(db, entity_id)
  except Exception as e:
    return {"error": str(e)}


def create_timepoints_relationship(
  db: Database,
  timepoint_id_1: int,
  timepoint_id_2: int,
  relation_type: str,
  staff_quota: Optional[int] = None,
  staff_type: Optional[str] = None,
  citation: Optional[str] = None,
  quotation: Optional[str] = None,
  note: Optional[str] = None
) -> Dict[str, Any]:
  """
  添加时间点关系
  
  添加时间点之间的关系信息，同时需要写入引用依赖信息。
  
  Args:
    db: Database 实例
    timepoint_id_1: 主体时间点 id
    timepoint_id_2: 客体时间点 id
    relation_type: 关系类型
    staff_quota: 编制关系中的官职人数（可选）
    staff_type: 编制关系中的职位类别（可选）
    citation: 引文出处
    quotation: 史料原文内容
    note: 考证说明或备注
    
  Returns:
    更新该关系后，同时查询两个相关词条，并返回结果
  """
  try:
    # 验证时间点是否存在
    tp1 = db.get_timepoint_by_id(timepoint_id_1)
    tp2 = db.get_timepoint_by_id(timepoint_id_2)
    
    if tp1 is None:
      return {"error": f"未找到时间点 id={timepoint_id_1}"}
    if tp2 is None:
      return {"error": f"未找到时间点 id={timepoint_id_2}"}
    
    entity_id_1 = tp1["entity_id"]
    entity_id_2 = tp2["entity_id"]
    entity_1_meta = db.get_entity_by_id(entity_id_1)
    entity_2_meta = db.get_entity_by_id(entity_id_2)
    if entity_1_meta is None:
      return {"error": f"未找到主体时间点所属实体 id={entity_id_1}"}
    if entity_2_meta is None:
      return {"error": f"未找到客体时间点所属实体 id={entity_id_2}"}

    valid_relation_types = {"上下级机构", "编制隶属", "前后演变", "统称与实例"}
    if relation_type not in valid_relation_types:
      return {"error": f"无效的关系类型: {relation_type}，必须是 {sorted(valid_relation_types)} 之一"}

    if relation_type == "编制隶属":
      if entity_1_meta["type"] != "机构" or entity_2_meta["type"] != "官职":
        return {
          "error": (
            "编制隶属关系必须是“机构 -> 官职”。"
            f"当前主体为 {entity_1_meta['title']}({entity_1_meta['type']}), "
            f"客体为 {entity_2_meta['title']}({entity_2_meta['type']})。"
            "请不要把兵种、军额类别或机构当作编制隶属的官职端。"
          )
        }

    if relation_type == "上下级机构":
      if entity_1_meta["type"] != "机构" or entity_2_meta["type"] != "机构":
        return {
          "error": (
            "上下级机构关系必须是“机构 -> 机构”。"
            f"当前主体为 {entity_1_meta['title']}({entity_1_meta['type']}), "
            f"客体为 {entity_2_meta['title']}({entity_2_meta['type']})。"
          )
        }
    
    existing_relationship = db.find_relationship(
      timepoint_id_1,
      timepoint_id_2,
      relation_type,
      staff_quota,
      staff_type
    )
    created = existing_relationship is None

    # 创建或复用关系
    relationship_id = db.insert_relationship(
      subject_id=timepoint_id_1,
      object_id=timepoint_id_2,
      relation_type=relation_type,
      staff_quota=staff_quota,
      staff_type=staff_type
    )
    
    # 添加引用依赖
    if citation or quotation or note:
      db.insert_citation(
        target_table="Relationships",
        target_id=relationship_id,
        citation=citation,
        quotation=quotation,
        note=note
      )
    
    # 返回两个相关词条的查询结果
    entity_1 = get_entity(db, entity_id_1)
    entity_2 = get_entity(db, entity_id_2)
    
    return {
      "entity_1": entity_1,
      "entity_2": entity_2,
      "relationship_id": relationship_id,
      "created": created
    }
  except Exception as e:
    return {"error": str(e)}


def upsert_entity_timepoint(
  db: Database,
  title: str,
  type: str,
  time: str,
  event: str,
  attributes: Optional[Dict[str, str]] = None,
  succ_timepoint_id: Optional[int] = None,
  citation: Optional[str] = None,
  quotation: Optional[str] = None,
  note: Optional[str] = None,
  allow_duplicate: bool = False,
) -> Dict[str, Any]:
  """一次完成实体、时间点、属性和首条引用的创建或复用。

  这是面向 agent 的复合写入工具。它避免模型先创建实体、等待 ID、再创建
  时间点、等待 ID、最后补属性和引用的多轮往返。精确相同的 time+event
  时间点会被复用；已有非空属性若与新值冲突则拒绝覆盖，交给原子工具的
  冲突引用流程处理。
  """
  valid_types = {"机构", "官职"}
  valid_attrs = {"attr_category", "attr_officer_type", "attr_grade"}
  attributes = attributes or {}

  if type not in valid_types:
    return {"error": f"无效的实体类型: {type}，必须是 {sorted(valid_types)} 之一"}
  if not isinstance(attributes, dict):
    return {"error": "attributes 必须是对象"}
  invalid_attrs = sorted(set(attributes) - valid_attrs)
  if invalid_attrs:
    return {"error": f"无效的 attributes 键: {invalid_attrs}，仅支持 {sorted(valid_attrs)}"}

  try:
    with db.entry_transaction():
      entity_result = create_entity(db, title, type, allow_duplicate=allow_duplicate)
      if "error" in entity_result:
        raise ValueError(entity_result["error"])

      entity_created = bool(entity_result.get("created"))
      entity_id = entity_result["entity"]["id"]
      timepoints = db.get_timepoints_by_entity_id(entity_id)
      exact_matches = [
        tp for tp in timepoints
        if tp.get("time") == time and tp.get("event") == event
      ]
      same_time_matches = [tp for tp in timepoints if tp.get("time") == time]

      if len(exact_matches) > 1:
        raise ValueError(
          f"实体 #{entity_id} 存在多个完全相同的时间点 {time!r}/{event!r}，"
          "无法安全选择，请改用原子工具并显式指定时间点 ID"
        )

      if exact_matches:
        timepoint_id = exact_matches[0]["id"]
        timepoint_created = False
      else:
        if same_time_matches:
          existing_events = "；".join(
            f"#{tp['id']} {tp.get('event')!r}" for tp in same_time_matches
          )
          raise ValueError(
            f"实体 #{entity_id} 在 {time!r} 已有其他事件：{existing_events}。"
            "复合工具不会判断应合并还是并列；请先 get_entity，"
            "再用原子工具显式更新或创建"
          )
        timepoint_result = create_timepoint(
          db,
          entity_id,
          succ_timepoint_id,
          time,
          event,
        )
        if "error" in timepoint_result:
          raise ValueError(timepoint_result["error"])
        timepoint_id = timepoint_result["new_timepoint_id"]
        timepoint_created = True

      current_timepoint = db.get_timepoint_by_id(timepoint_id)
      if current_timepoint is None:
        raise ValueError(f"复合写入后未找到时间点 id={timepoint_id}")

      updates: Dict[str, str] = {}
      for key, value in attributes.items():
        if value is None:
          continue
        current_value = current_timepoint.get(key)
        if current_value not in (None, "", value):
          raise ValueError(
            f"时间点 #{timepoint_id} 的 {key} 已有值 {current_value!r}，"
            f"与新值 {value!r} 冲突；未覆盖，请改用 append_citation 标记冲突"
          )
        if current_value != value:
          updates[key] = value
      if updates:
        db.update_timepoint(timepoint_id, **updates)

      if citation or quotation or note:
        db.insert_citation(
          target_table="Timepoints",
          target_id=timepoint_id,
          citation=citation,
          quotation=quotation,
          note=note,
        )

      result = get_entity(db, entity_id)
      result.update({
        "entity_created": entity_created,
        "timepoint_created": timepoint_created,
        "timepoint_id": timepoint_id,
      })
      return result
  except Exception as e:
    return {"error": str(e)}


def _resolve_timepoint_by_entity_time(
  db: Database,
  title: str,
  type: str,
  time: str,
  event: Optional[str] = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
  """按精确 title+type+time（可选 event）解析唯一关系端点。"""
  entities = [
    entity for entity in db.get_entity_by_title(title)
    if entity.get("type") == type
  ]
  if not entities:
    raise ValueError(f"未找到精确实体: title={title!r}, type={type!r}")
  if len(entities) > 1:
    raise ValueError(
      f"实体 title={title!r}, type={type!r} 有 {len(entities)} 个同名实例，"
      "无法安全解析；请改用 create_timepoints_relationship 并显式指定已加载 ID"
    )

  entity = entities[0]
  timepoints = [
    tp for tp in db.get_timepoints_by_entity_id(entity["id"])
    if tp.get("time") == time and (event is None or tp.get("event") == event)
  ]
  if not timepoints:
    event_text = "" if event is None else f", event={event!r}"
    raise ValueError(
      f"实体 #{entity['id']} 未找到精确时间点: time={time!r}{event_text}"
    )
  if len(timepoints) > 1:
    raise ValueError(
      f"实体 #{entity['id']} 在 time={time!r} 下匹配到 {len(timepoints)} 个时间点；"
      "请补充 event 进行消歧，或改用显式 ID 工具"
    )
  return entity, timepoints[0]


def upsert_relationship(
  db: Database,
  subject_title: str,
  subject_type: str,
  subject_time: str,
  object_title: str,
  object_type: str,
  object_time: str,
  relation_type: str,
  subject_event: Optional[str] = None,
  object_event: Optional[str] = None,
  staff_quota: Optional[int] = None,
  staff_type: Optional[str] = None,
  citation: Optional[str] = None,
  quotation: Optional[str] = None,
  note: Optional[str] = None,
) -> Dict[str, Any]:
  """按精确实体与时间选择器，一次创建/复用关系并写入引用。

  端点不使用模型猜测的数据库 ID，因此可以排在同一 Action 中更早的
  ``upsert_entity_timepoint`` 调用之后顺序执行。
  """
  try:
    with db.entry_transaction():
      subject_entity, subject_timepoint = _resolve_timepoint_by_entity_time(
        db, subject_title, subject_type, subject_time, subject_event
      )
      object_entity, object_timepoint = _resolve_timepoint_by_entity_time(
        db, object_title, object_type, object_time, object_event
      )
      result = create_timepoints_relationship(
        db,
        subject_timepoint["id"],
        object_timepoint["id"],
        relation_type,
        staff_quota,
        staff_type,
        citation,
        quotation,
        note,
      )
      if "error" in result:
        raise ValueError(result["error"])
      result.update({
        "subject_entity_id": subject_entity["id"],
        "subject_timepoint_id": subject_timepoint["id"],
        "object_entity_id": object_entity["id"],
        "object_timepoint_id": object_timepoint["id"],
      })
      return result
  except Exception as e:
    return {"error": str(e)}


def append_citation(
  db: Database,
  target_table: str,
  target_id: int,
  citation: Optional[str] = None,
  quotation: Optional[str] = None,
  note: Optional[str] = None,
  conflict_flag: bool = False
) -> Dict[str, Any]:
  """
  添加引用依赖
  
  当有新的证据可以证实已有的属性或关系时，可以追加引用依赖；
  如果当前引用依赖与现有信息存在冲突，同样可以追加引用依赖；但是目前不对已有的信息进行修改，
  而是标记为可能存在冲突的属性值；留到以后的步骤再检查判断。
  
  Args:
    db: Database 实例
    target_table: 关联的表名（'Timepoints' 或 'Relationships'）
    target_id: 对应表中的行 id
    citation: 引文出处
    quotation: 史料原文内容
    note: 考证说明或备注
    conflict_flag: 是否标记为冲突
    
  Returns:
    查询相关的词条，并返回其值
  """
  try:
    # 验证 target_table
    if target_table not in ["Timepoints", "Relationships"]:
      return {"error": f"无效的 target_table: {target_table}，必须是 'Timepoints' 或 'Relationships'"}
    
    # 验证目标是否存在
    if target_table == "Timepoints":
      target = db.get_timepoint_by_id(target_id)
      if target is None:
        return {"error": f"未找到时间点 id={target_id}"}
      entity_id = target["entity_id"]
    else:  # Relationships
      target = db.get_relationship_by_id(target_id)
      if target is None:
        return {"error": f"未找到关系 id={target_id}"}
      # 获取关系关联的时间点，然后获取词条 id
      tp1 = db.get_timepoint_by_id(target["subject_id"])
      tp2 = db.get_timepoint_by_id(target["object_id"])
      if tp1 is None or tp2 is None:
        return {"error": "关系关联的时间点不存在"}
      entity_id_1 = tp1["entity_id"]
      entity_id_2 = tp2["entity_id"]
    
    # 添加引用依赖
    citation_id = db.insert_citation(
      target_table=target_table,
      target_id=target_id,
      citation=citation,
      quotation=quotation,
      note=note,
      conflict_flag=conflict_flag
    )
    
    # 返回查询结果
    if target_table == "Timepoints":
      return get_entity(db, entity_id)
    else:
      entity_1 = get_entity(db, entity_id_1)
      entity_2 = get_entity(db, entity_id_2)
      return {
        "entity_1": entity_1,
        "entity_2": entity_2
      }
  except Exception as e:
    return {"error": str(e)}
