from typing import Optional, Dict, Any, List
from database import Database


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


def entity_to_str(entity_data: Dict[str, Any]) -> str:
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
      lines.extend(format_citations(citations, indent="  "))
    
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
        lines.extend(format_citations(hierarchy_citations, indent="  "))
    
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
        lines.extend(format_citations(staff_relation_citations, indent="  "))
    
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
        lines.extend(format_citations(evolution_citations, indent="  "))
    
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
        lines.extend(format_citations(template_instance_citations, indent="  "))
    
    lines.append("")
  
  return "\n".join(lines)


def create_entity(db: Database, title: str, type: str) -> Dict[str, Any]:
  """
  创建新词条
  
  向 Entities 表中添加项；需要词条名称和类别（机构或官职）；在添加前需要确认现有表中不包含该词条，
  或确认该词条与现有词条并非指向同一个机构或官职（同名不同体）；最好能够在名称上体现区别。
  创建 Entity 项会同步向 Timepoints 中添加一个占位时间点，设置 time 为 "未知" 并设置 event 为 "占位"。
  
  Args:
    db: Database 实例
    title: 词条名称
    type: 词条类型（'机构' 或 '官职'）
    
  Returns:
    创建该词条后，自动调用词条查询功能，返回查询结果
  """
  try:
    # 检查是否已存在同名词条
    existing = db.get_entity_by_title(title)
    if existing:
      # 返回警告，但不阻止创建（允许同名不同体的情况）
      pass
    
    # 创建新词条
    entity_id = db.insert_entity(title, type)
    
    # 创建占位时间点
    db.insert_timepoint(
      entity_id=entity_id,
      time="未知",
      event="占位"
    )
    
    # 返回查询结果
    return get_entity(db, entity_id)
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
      return get_entity(db, entity_id)
    
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
    
    # 返回查询结果
    return get_entity(db, entity_id)
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
    attr_key: 属性键（'attr_category', 'attr_officer_type', 'attr_grade'）
    attr_value: 属性值
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
    
    # 验证属性键
    valid_attrs = ["attr_category", "attr_officer_type", "attr_grade"]
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
  quotation: Optional[str] = None
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
    
    # 创建关系
    relationship_id = db.insert_relationship(
      subject_id=timepoint_id_1,
      object_id=timepoint_id_2,
      relation_type=relation_type,
      staff_quota=staff_quota,
      staff_type=staff_type
    )
    
    # 添加引用依赖
    if citation or quotation:
      db.insert_citation(
        target_table="Relationships",
        target_id=relationship_id,
        citation=citation,
        quotation=quotation
      )
    
    # 返回两个相关词条的查询结果
    entity_1 = get_entity(db, entity_id_1)
    entity_2 = get_entity(db, entity_id_2)
    
    return {
      "entity_1": entity_1,
      "entity_2": entity_2
    }
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
