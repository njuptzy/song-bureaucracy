import sqlite3
import json
from typing import Optional, Dict, List, Any, Tuple


class Database:
  """
  数据库管理类，负责管理《辞典》数据库和结构化数据数据库
  """
  
  def __init__(self, dict_db_path: str, dict_table: str, entry_db_path: str):
    """
    初始化 Database 实例
    
    Args:
      dict_db_path: 《辞典》数据库路径
      dict_table: 《辞典》数据表名
      entry_db_path: 结构化数据数据库路径（包含 Entities, Timepoints, Relationships, Citations 表）
    """
    self.dict_db_path = dict_db_path
    self.dict_table = dict_table
    self.entry_db_path = entry_db_path
    
    # 建立数据库连接
    self._dict_conn = sqlite3.connect(self.dict_db_path)
    self._entry_conn = sqlite3.connect(self.entry_db_path)
    
    # 启用外键约束（SQLite 默认关闭）
    self._entry_conn.execute("PRAGMA foreign_keys = ON")
    
    # 初始化结构化数据表
    self._init_tables()
  
  def close(self):
    """关闭所有数据库连接"""
    if self._dict_conn is not None:
      self._dict_conn.close()
      self._dict_conn = None
    if self._entry_conn is not None:
      self._entry_conn.close()
      self._entry_conn = None
  
  def __enter__(self):
    return self
  
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()

  def _recreate_tables(self):
    """重建结构化数据表（Entities, Timepoints, Relationships, Citations）"""
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute("DROP TABLE IF EXISTS Citations")
      cursor.execute("DROP TABLE IF EXISTS Relationships")
      cursor.execute("DROP TABLE IF EXISTS Timepoints")
      cursor.execute("DROP TABLE IF EXISTS Entities")
      self._init_tables()
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def _init_tables(self):
    """初始化结构化数据表（Entities, Timepoints, Relationships, Citations）"""
    cursor = self._entry_conn.cursor()
    try:
      # Entities 表
      cursor.execute("""
        CREATE TABLE IF NOT EXISTS Entities (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          type TEXT
        )
      """)
      
      # Timepoints 表
      cursor.execute("""
        CREATE TABLE IF NOT EXISTS Timepoints (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          entity_id INTEGER NOT NULL,
          time TEXT,
          event TEXT,
          prev_id INTEGER,
          succ_id INTEGER,
          attr_category TEXT,
          attr_officer_type TEXT,
          attr_grade TEXT,
          FOREIGN KEY (entity_id) REFERENCES Entities(id),
          FOREIGN KEY (prev_id) REFERENCES Timepoints(id),
          FOREIGN KEY (succ_id) REFERENCES Timepoints(id)
        )
      """)
      
      # Relationships 表
      cursor.execute("""
        CREATE TABLE IF NOT EXISTS Relationships (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          subject_id INTEGER NOT NULL,
          object_id INTEGER NOT NULL,
          relation_type TEXT,
          staff_quota INTEGER,
          staff_type TEXT,
          FOREIGN KEY (subject_id) REFERENCES Timepoints(id),
          FOREIGN KEY (object_id) REFERENCES Timepoints(id)
        )
      """)
      
      # Citations 表
      cursor.execute("""
        CREATE TABLE IF NOT EXISTS Citations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          target_table TEXT NOT NULL,
          target_id INTEGER NOT NULL,
          citation TEXT,
          quotation TEXT,
          note TEXT,
          conflict_flag INTEGER DEFAULT 0
        )
      """)
      
      self._entry_conn.commit()
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  # ========== 查询《辞典》索引 ==========

  def get_dictionary_index(self) -> List[Dict[str, Any]]:
    """
    从《辞典》数据库中获取索引数据（title-page）
    """
    cursor = self._dict_conn.cursor()
    try:
      cursor.execute(f"SELECT id, title, page FROM {self.dict_table} ORDER BY id")
      rows = cursor.fetchall()
      entries = [f"{title}-{page}" for (id, title, page) in rows]
      return entries
    except Exception as e:
      self._dict_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  # ========== 查询《辞典》原始文献 ==========
  
  def search_dictionary(self, title: str, page: str) -> Dict[str, Any]:
    """
    查询《辞典》原始文献
    
    Args:
      title: 词条名称
      page: 页码
      
    Returns:
      词条对象结构，如果未找到则返回 {"error": "..."}
    """
    cursor = self._dict_conn.cursor()
    try:
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, text, fields
        FROM {self.dict_table}
        WHERE title = ? AND page = ?
        """,
        (title, str(page))
      )
      row = cursor.fetchone()
      if row is None:
        return {"error": f"未找到《辞典》条目: {title} (页码: {page})"}
      
      return {
        "id": str(row[0]),
        "title": row[1],
        "catalog": row[2],
        "page": row[3],
        "text": row[4],
        "fields": json.loads(row[5]) if row[5] else {}
      }
    except Exception as e:
      self._dict_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  # ========== 获取条目表索引 ==========

  def get_entities_index(self) -> List[Dict[str, Any]]:
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(f"SELECT id, title FROM Entities ORDER BY id")
      rows = cursor.fetchall()
      entries = [f"{title}: {id}" for (id, title) in rows]
      return entries
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  # ========== 原子操作：Entities 表 ==========
  
  def insert_entity(self, title: str, type: Optional[str] = None) -> int:
    """
    向 Entities 表插入一条新记录
    
    Args:
      title: 词条名称
      type: 词条类型（'机构' 或 '官职'）
      
    Returns:
      新插入记录的 id
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        "INSERT INTO Entities (title, type) VALUES (?, ?)",
        (title, type)
      )
      self._entry_conn.commit()
      return cursor.lastrowid
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def update_entity(self, entity_id: int, title: Optional[str] = None, type: Optional[str] = None) -> bool:
    """
    更新 Entities 表中的记录
    
    Args:
      entity_id: 词条 id
      title: 新的词条名称（可选）
      type: 新的词条类型（可选）
      
    Returns:
      是否更新成功
    """
    cursor = self._entry_conn.cursor()
    try:
      updates = []
      params = []
      if title is not None:
        updates.append("title = ?")
        params.append(title)
      if type is not None:
        updates.append("type = ?")
        params.append(type)
      
      if not updates:
        return True
      
      params.append(entity_id)
      cursor.execute(
        f"UPDATE Entities SET {', '.join(updates)} WHERE id = ?",
        params
      )
      self._entry_conn.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def delete_entity(self, entity_id: int) -> bool:
    """
    删除 Entities 表中的记录（注意：会级联删除相关的 Timepoints）
    
    Args:
      entity_id: 词条 id
      
    Returns:
      是否删除成功
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute("DELETE FROM Entities WHERE id = ?", (entity_id,))
      self._entry_conn.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def get_entity_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
    """
    根据 id 查询 Entities 表中的记录
    
    Args:
      entity_id: 词条 id
      
    Returns:
      词条对象，如果未找到则返回 None
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        "SELECT id, title, type FROM Entities WHERE id = ?",
        (entity_id,)
      )
      row = cursor.fetchone()
      if row is None:
        return None
      return {
        "id": row[0],
        "title": row[1],
        "type": row[2]
      }
    finally:
      cursor.close()
  
  def get_entity_by_title(self, title: str) -> List[Dict[str, Any]]:
    """
    根据 title 查询 Entities 表中的记录
    
    Args:
      title: 词条名称
      
    Returns:
      匹配的词条列表
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        "SELECT id, title, type FROM Entities WHERE title = ? ORDER BY id",
        (title,)
      )
      rows = cursor.fetchall()
      return [
        {"id": row[0], "title": row[1], "type": row[2]}
        for row in rows
      ]
    finally:
      cursor.close()
  
  # ========== 原子操作：Timepoints 表 ==========
  
  def insert_timepoint(
    self,
    entity_id: int,
    time: Optional[str] = None,
    event: Optional[str] = None,
    prev_id: Optional[int] = None,
    succ_id: Optional[int] = None,
    attr_category: Optional[str] = None,
    attr_officer_type: Optional[str] = None,
    attr_grade: Optional[str] = None
  ) -> int:
    """
    向 Timepoints 表插入一条新记录
    
    Args:
      entity_id: 关联的词条 id
      time: 时间点
      event: 事件描述
      prev_id: 前一个时间点 id（可选）
      succ_id: 后一个时间点 id（可选）
      attr_category: 属性：细节分类
      attr_officer_type: 属性：官职分类
      attr_grade: 属性：品阶
      
    Returns:
      新插入记录的 id
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        """INSERT INTO Timepoints 
           (entity_id, time, event, prev_id, succ_id, attr_category, attr_officer_type, attr_grade)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (entity_id, time, event, prev_id, succ_id, attr_category, attr_officer_type, attr_grade)
      )
      self._entry_conn.commit()
      return cursor.lastrowid
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def update_timepoint(
    self,
    timepoint_id: int,
    time: Optional[str] = None,
    event: Optional[str] = None,
    prev_id: Optional[int] = None,
    succ_id: Optional[int] = None,
    attr_category: Optional[str] = None,
    attr_officer_type: Optional[str] = None,
    attr_grade: Optional[str] = None
  ) -> bool:
    """
    更新 Timepoints 表中的记录
    
    Args:
      timepoint_id: 时间点 id
      time: 时间点（可选）
      event: 事件描述（可选）
      prev_id: 前一个时间点 id（可选，设置为 -1 表示清空）
      succ_id: 后一个时间点 id（可选，设置为 -1 表示清空）
      attr_category: 属性：细节分类（可选）
      attr_officer_type: 属性：官职分类（可选）
      attr_grade: 属性：品阶（可选）
      
    Returns:
      是否更新成功
    """
    cursor = self._entry_conn.cursor()
    try:
      updates = []
      params = []
      if time is not None:
        updates.append("time = ?")
        params.append(time)
      if event is not None:
        updates.append("event = ?")
        params.append(event)
      if prev_id is not None:
        if prev_id == -1:
          updates.append("prev_id = NULL")
        else:
          updates.append("prev_id = ?")
          params.append(prev_id)
      if succ_id is not None:
        if succ_id == -1:
          updates.append("succ_id = NULL")
        else:
          updates.append("succ_id = ?")
          params.append(succ_id)
      if attr_category is not None:
        updates.append("attr_category = ?")
        params.append(attr_category)
      if attr_officer_type is not None:
        updates.append("attr_officer_type = ?")
        params.append(attr_officer_type)
      if attr_grade is not None:
        updates.append("attr_grade = ?")
        params.append(attr_grade)
      
      if not updates:
        return True
      
      params.append(timepoint_id)
      cursor.execute(
        f"UPDATE Timepoints SET {', '.join(updates)} WHERE id = ?",
        params
      )
      self._entry_conn.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def delete_timepoint(self, timepoint_id: int) -> bool:
    """
    删除 Timepoints 表中的记录（注意：会级联删除相关的 Relationships 和 Citations，并更新相邻时间点的指针）
    
    Args:
      timepoint_id: 时间点 id
      
    Returns:
      是否删除成功
    """
    cursor = self._entry_conn.cursor()
    try:
      # 先获取要删除的时间点信息
      timepoint = self.get_timepoint_by_id(timepoint_id)
      if timepoint is None:
        return False
      
      prev_id = timepoint.get("prev_id")
      succ_id = timepoint.get("succ_id")
      
      # 先删除相关的 Citations
      cursor.execute(
        "DELETE FROM Citations WHERE target_table = 'Timepoints' AND target_id = ?",
        (timepoint_id,)
      )
      # 删除相关的 Relationships（作为 subject 或 object）
      cursor.execute(
        "DELETE FROM Relationships WHERE subject_id = ? OR object_id = ?",
        (timepoint_id, timepoint_id)
      )
      
      # 更新相邻时间点的指针
      if prev_id is not None:
        # 更新前一个时间点的 succ_id
        cursor.execute(
          "UPDATE Timepoints SET succ_id = ? WHERE id = ?",
          (succ_id, prev_id)
        )
      if succ_id is not None:
        # 更新后一个时间点的 prev_id
        cursor.execute(
          "UPDATE Timepoints SET prev_id = ? WHERE id = ?",
          (prev_id, succ_id)
        )
      
      # 删除 Timepoint
      cursor.execute("DELETE FROM Timepoints WHERE id = ?", (timepoint_id,))
      self._entry_conn.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def get_timepoint_by_id(self, timepoint_id: int) -> Optional[Dict[str, Any]]:
    """
    根据 id 查询 Timepoints 表中的记录
    
    Args:
      timepoint_id: 时间点 id
      
    Returns:
      时间点对象，如果未找到则返回 None
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        """SELECT id, entity_id, time, event, prev_id, succ_id, attr_category, attr_officer_type, attr_grade
           FROM Timepoints WHERE id = ?""",
        (timepoint_id,)
      )
      row = cursor.fetchone()
      if row is None:
        return None
      return {
        "id": row[0],
        "entity_id": row[1],
        "time": row[2],
        "event": row[3],
        "prev_id": row[4],
        "succ_id": row[5],
        "attr_category": row[6],
        "attr_officer_type": row[7],
        "attr_grade": row[8]
      }
    finally:
      cursor.close()
  
  def get_timepoints_by_entity_id(self, entity_id: int) -> List[Dict[str, Any]]:
    """
    根据 entity_id 查询所有相关的 Timepoints
    
    Args:
      entity_id: 词条 id
      
    Returns:
      时间点列表，按 prev_id 链式顺序排序（从 prev_id 为 NULL 的开始）
    """
    cursor = self._entry_conn.cursor()
    try:
      # 先获取所有时间点
      cursor.execute(
        """SELECT id, entity_id, time, event, prev_id, succ_id, attr_category, attr_officer_type, attr_grade
           FROM Timepoints WHERE entity_id = ?""",
        (entity_id,)
      )
      rows = cursor.fetchall()
      timepoints = [
        {
          "id": row[0],
          "entity_id": row[1],
          "time": row[2],
          "event": row[3],
          "prev_id": row[4],
          "succ_id": row[5],
          "attr_category": row[6],
          "attr_officer_type": row[7],
          "attr_grade": row[8]
        }
        for row in rows
      ]
      
      # 如果没有时间点，直接返回
      if not timepoints:
        return []
      
      # 按 prev_id 链式顺序排序：找到 prev_id 为 None 的作为起点，然后按 succ_id 链式遍历
      # 如果链式结构不完整，则按 time 和 id 排序作为后备方案
      result = []
      visited = set()
      
      # 找到所有 prev_id 为 None 的时间点（链的起点）
      heads = [tp for tp in timepoints if tp["prev_id"] is None]
      
      if heads:
        # 从每个起点开始遍历链
        for head in heads:
          current = head
          while current and current["id"] not in visited:
            result.append(current)
            visited.add(current["id"])
            if current["succ_id"] is not None:
              # 找到下一个时间点
              current = next((tp for tp in timepoints if tp["id"] == current["succ_id"]), None)
            else:
              current = None
      
      # 添加未访问的时间点（可能是孤立节点或链式结构不完整）
      for tp in timepoints:
        if tp["id"] not in visited:
          result.append(tp)
      
      # 如果链式结构不完整，按 time 和 id 排序作为后备
      if len(result) != len(timepoints) or not all(tp["id"] in visited for tp in timepoints):
        # 重新按 time 和 id 排序
        result = sorted(timepoints, key=lambda x: (x["time"] or "", x["id"]))
      
      return result
    finally:
      cursor.close()
  
  def get_prev_timepoint_id(self, entity_id: int, timepoint_id: int) -> Optional[int]:
    """
    获取指定时间点的前一个时间点 id（从 prev_id 字段获取）
    
    Args:
      entity_id: 词条 id（保留参数以保持向后兼容，但不再使用）
      timepoint_id: 当前时间点 id
      
    Returns:
      前一个时间点 id，如果不存在则返回 None
    """
    timepoint = self.get_timepoint_by_id(timepoint_id)
    if timepoint is None:
      return None
    return timepoint.get("prev_id")
  
  def get_succ_timepoint_id(self, entity_id: int, timepoint_id: int) -> Optional[int]:
    """
    获取指定时间点的后一个时间点 id（从 succ_id 字段获取）
    
    Args:
      entity_id: 词条 id（保留参数以保持向后兼容，但不再使用）
      timepoint_id: 当前时间点 id
      
    Returns:
      后一个时间点 id，如果不存在则返回 None
    """
    timepoint = self.get_timepoint_by_id(timepoint_id)
    if timepoint is None:
      return None
    return timepoint.get("succ_id")
  
  # ========== 原子操作：Relationships 表 ==========
  
  def insert_relationship(
    self,
    subject_id: int,
    object_id: int,
    relation_type: Optional[str] = None,
    staff_quota: Optional[int] = None,
    staff_type: Optional[str] = None
  ) -> int:
    """
    向 Relationships 表插入一条新记录
    
    Args:
      subject_id: 主体时间点 id
      object_id: 客体时间点 id
      relation_type: 关系类型
      staff_quota: 编制人数（可选）
      staff_type: 职位类别（可选）
      
    Returns:
      新插入记录的 id
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        """INSERT INTO Relationships 
           (subject_id, object_id, relation_type, staff_quota, staff_type)
           VALUES (?, ?, ?, ?, ?)""",
        (subject_id, object_id, relation_type, staff_quota, staff_type)
      )
      self._entry_conn.commit()
      return cursor.lastrowid
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def update_relationship(
    self,
    relationship_id: int,
    relation_type: Optional[str] = None,
    staff_quota: Optional[int] = None,
    staff_type: Optional[str] = None
  ) -> bool:
    """
    更新 Relationships 表中的记录
    
    Args:
      relationship_id: 关系 id
      relation_type: 关系类型（可选）
      staff_quota: 编制人数（可选）
      staff_type: 职位类别（可选）
      
    Returns:
      是否更新成功
    """
    cursor = self._entry_conn.cursor()
    try:
      updates = []
      params = []
      if relation_type is not None:
        updates.append("relation_type = ?")
        params.append(relation_type)
      if staff_quota is not None:
        updates.append("staff_quota = ?")
        params.append(staff_quota)
      if staff_type is not None:
        updates.append("staff_type = ?")
        params.append(staff_type)
      
      if not updates:
        return True
      
      params.append(relationship_id)
      cursor.execute(
        f"UPDATE Relationships SET {', '.join(updates)} WHERE id = ?",
        params
      )
      self._entry_conn.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def delete_relationship(self, relationship_id: int) -> bool:
    """
    删除 Relationships 表中的记录（注意：会级联删除相关的 Citations）
    
    Args:
      relationship_id: 关系 id
      
    Returns:
      是否删除成功
    """
    cursor = self._entry_conn.cursor()
    try:
      # 先删除相关的 Citations
      cursor.execute(
        "DELETE FROM Citations WHERE target_table = 'Relationships' AND target_id = ?",
        (relationship_id,)
      )
      # 删除 Relationship
      cursor.execute("DELETE FROM Relationships WHERE id = ?", (relationship_id,))
      self._entry_conn.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def get_relationship_by_id(self, relationship_id: int) -> Optional[Dict[str, Any]]:
    """
    根据 id 查询 Relationships 表中的记录
    
    Args:
      relationship_id: 关系 id
      
    Returns:
      关系对象，如果未找到则返回 None
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        """SELECT id, subject_id, object_id, relation_type, staff_quota, staff_type
           FROM Relationships WHERE id = ?""",
        (relationship_id,)
      )
      row = cursor.fetchone()
      if row is None:
        return None
      return {
        "id": row[0],
        "subject_id": row[1],
        "object_id": row[2],
        "relation_type": row[3],
        "staff_quota": row[4],
        "staff_type": row[5]
      }
    finally:
      cursor.close()
  
  def get_relationships_by_timepoint_id(self, timepoint_id: int) -> List[Dict[str, Any]]:
    """
    根据 timepoint_id 查询所有相关的 Relationships（作为 subject 或 object）
    
    Args:
      timepoint_id: 时间点 id
      
    Returns:
      关系列表
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        """SELECT id, subject_id, object_id, relation_type, staff_quota, staff_type
           FROM Relationships
           WHERE subject_id = ? OR object_id = ?""",
        (timepoint_id, timepoint_id)
      )
      rows = cursor.fetchall()
      return [
        {
          "id": row[0],
          "subject_id": row[1],
          "object_id": row[2],
          "relation_type": row[3],
          "staff_quota": row[4],
          "staff_type": row[5]
        }
        for row in rows
      ]
    finally:
      cursor.close()
  
  # ========== 原子操作：Citations 表 ==========
  
  def insert_citation(
    self,
    target_table: str,
    target_id: int,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
    note: Optional[str] = None,
    conflict_flag: bool = False
  ) -> int:
    """
    向 Citations 表插入一条新记录
    
    Args:
      target_table: 关联的表名（'Timepoints' 或 'Relationships'）
      target_id: 对应表中的行 id
      citation: 引文出处
      quotation: 史料原文内容
      note: 考证说明或备注
      conflict_flag: 是否标记为冲突
      
    Returns:
      新插入记录的 id
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        """INSERT INTO Citations 
           (target_table, target_id, citation, quotation, note, conflict_flag)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (target_table, target_id, citation, quotation, note, 1 if conflict_flag else 0)
      )
      self._entry_conn.commit()
      return cursor.lastrowid
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def update_citation(
    self,
    citation_id: int,
    citation: Optional[str] = None,
    quotation: Optional[str] = None,
    note: Optional[str] = None,
    conflict_flag: Optional[bool] = None
  ) -> bool:
    """
    更新 Citations 表中的记录
    
    Args:
      citation_id: 引用 id
      citation: 引文出处（可选）
      quotation: 史料原文内容（可选）
      note: 考证说明或备注（可选）
      conflict_flag: 是否标记为冲突（可选）
      
    Returns:
      是否更新成功
    """
    cursor = self._entry_conn.cursor()
    try:
      updates = []
      params = []
      if citation is not None:
        updates.append("citation = ?")
        params.append(citation)
      if quotation is not None:
        updates.append("quotation = ?")
        params.append(quotation)
      if note is not None:
        updates.append("note = ?")
        params.append(note)
      if conflict_flag is not None:
        updates.append("conflict_flag = ?")
        params.append(1 if conflict_flag else 0)
      
      if not updates:
        return True
      
      params.append(citation_id)
      cursor.execute(
        f"UPDATE Citations SET {', '.join(updates)} WHERE id = ?",
        params
      )
      self._entry_conn.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def delete_citation(self, citation_id: int) -> bool:
    """
    删除 Citations 表中的记录
    
    Args:
      citation_id: 引用 id
      
    Returns:
      是否删除成功
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute("DELETE FROM Citations WHERE id = ?", (citation_id,))
      self._entry_conn.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self._entry_conn.rollback()
      raise e
    finally:
      cursor.close()
  
  def get_citations_by_target(self, target_table: str, target_id: int) -> List[Dict[str, Any]]:
    """
    根据 target_table 和 target_id 查询所有相关的 Citations
    
    Args:
      target_table: 关联的表名
      target_id: 对应表中的行 id
      
    Returns:
      引用列表
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        """SELECT id, target_table, target_id, citation, quotation, note, conflict_flag
           FROM Citations
           WHERE target_table = ? AND target_id = ?""",
        (target_table, target_id)
      )
      rows = cursor.fetchall()
      return [
        {
          "id": row[0],
          "target_table": row[1],
          "target_id": row[2],
          "citation": row[3],
          "quotation": row[4],
          "note": row[5],
          "conflict_flag": bool(row[6])
        }
        for row in rows
      ]
    finally:
      cursor.close()
