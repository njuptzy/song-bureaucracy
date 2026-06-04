import sqlite3
import re
import json

class Database:
  def __init__(self, dict_db_path, dict_table, entry_db_path, entry_table):
    """
    初始化 Database 实例
    
    Args:
      dict_db_path: 《辞典》数据库路径
      dict_table: 《辞典》数据表名
      entry_db_path: 官制条目数据库路径
      entry_table: 官制条目数据表名
    """
    self.dict_db_path = dict_db_path
    self.entry_db_path = entry_db_path
    self.dict_table = dict_table
    self.entry_table = entry_table

    # 在初始化时建立数据库连接
    self._dict_conn = sqlite3.connect(self.dict_db_path)
    self._entry_conn = sqlite3.connect(self.entry_db_path)

    # 构建索引表，格式为 set of "名称-页码" 字符串
    indexes = self.get_dict_indexes()
    if isinstance(indexes, set):
      self.indexes = indexes
    else:
      assert False, indexes["error"]

  def close(self):
    """关闭所有数据库连接"""
    if self._dict_conn is not None:
      self._dict_conn.close()
      self._dict_conn = None
    if self._entry_conn is not None:
      self._entry_conn.close()
      self._entry_conn = None
  
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
  
  def __enter__(self):
    return self

  # ======== JSON 格式转文本 =========

  @staticmethod
  def dict_entry_to_str(entry):
    fields = entry["fields"]
    fields_texts = []
    for key, value in fields.items():
      fields_texts.append(f"{key}: {value}")
    entry_text = f"""{entry["title"]}
文本来源：{entry["catalog"]} {entry["page"]}页
基本介绍：{entry["text"]}
{"\n".join(fields_texts)}
"""
    return entry_text
  
  @staticmethod
  def table_entry_to_str(entry):
    return json.dumps(entry, ensure_ascii=False, indent=2)

  @staticmethod
  def table_entries_to_str(entries):
    return "\n\n".join(
      [
        Database.table_entry_to_str(entry)
        for entry in entries
      ]
    )
  # ========= 构建新表（覆盖原表） =========

  def refresh_entry_table(self):
    """
    从《辞典》数据库中获取全部条目信息，并据此创建条目表，会覆盖原有的表格
    """
    cursor_dict = self._dict_conn.cursor()
    cursor_entry = None
    try:
      cursor_dict.execute(f"SELECT title, catalog, page FROM {self.dict_table}")
      entry_list = []
      for row in cursor_dict.fetchall():
        entry_list.append({
          "title": row[0],
          "catalog": row[1],
          "page": row[2]
        })
      
      cursor_entry = self._entry_conn.cursor()
      cursor_entry.execute(f"""DROP TABLE IF EXISTS {self.entry_table}""")
      cursor_entry.execute(f"""
      CREATE TABLE IF NOT EXISTS {self.entry_table} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        catalog TEXT NOT NULL,
        page TEXT NOT NULL,
        type TEXT,
        subtype TEXT,
        bgn_time TEXT,
        bgn_event TEXT,
        end_time TEXT,
        end_event TEXT,
        time_index FLOAT,
        superiors TEXT,
        subordinates TEXT,
        staffing TEXT,
        department TEXT,
        grade TEXT
      )
      """)

      cursor_entry.executemany(f"""
      INSERT INTO {self.entry_table} (title, catalog, page, bgn_time, bgn_event, end_time, end_event, time_index, superiors, subordinates, staffing)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, [
        (
          entry["title"],
          entry["catalog"],
          entry["page"],
          "-INF",
          "始置",
          "INF",
          "罢置",
          1,
          "[]",
          "[]",
          "[]",
        )
        for entry in entry_list
      ])

      self._entry_conn.commit()

      cursor_entry.execute(f"SELECT COUNT(*) FROM {self.entry_table}")
      count = cursor_entry.fetchone()[0]
      print(f"成功插入 {count} 条记录到 {self.entry_table} 表")
    finally:
      if cursor_dict is not None:
        cursor_dict.close()
      if cursor_entry is not None:
        cursor_entry.close()

  # ========= 内部工具函数 =========
  
  @staticmethod
  def _loads_list(v):
    if v is None or v == "":
      return []
    try:
      x = json.loads(v)
    except Exception:
      return []
    return x if isinstance(x, list) else []
  
  @staticmethod
  def _dumps_list(v):
    if v is None:
      return "[]"
    if isinstance(v, list):
      return json.dumps(v, ensure_ascii=False)
    if isinstance(v, str):
      # 允许直接传入 JSON 字符串
      try:
        x = json.loads(v)
        if isinstance(x, list):
          return json.dumps(x, ensure_ascii=False)
      except Exception:
        pass
    raise ValueError("列表字段要求 list 或可解析为 list 的 JSON 字符串")
  
  def _row_to_entry(self, row):
    """
    将官制表中的一行数据转换为字典对象
    """
    return {
      "id": row[0],
      "title": row[1],
      "catalog": row[2],
      "page": row[3],
      "type": row[4],
      "subtype": row[5],
      "bgn_time": row[6],
      "bgn_event": row[7],
      "end_time": row[8],
      "end_event": row[9],
      "superiors": self._loads_list(row[10]),
      "subordinates": self._loads_list(row[11]),
      "staffing": self._loads_list(row[12]),
      "department": row[13],
      "grade": row[14],
      "time_index": row[15],
    }
  
  def _fetch_entry_by_meta(self, cursor, title, page, bgn_time, end_time):
    cursor.execute(
      f"""
      SELECT id
      FROM {self.entry_table}
      WHERE title = ? AND page = ? AND bgn_time = ? AND end_time = ?
      """,
      (title, str(page), bgn_time, end_time),
    )
    row = cursor.fetchone()
    return None if row is None else row[0]
  
  def _rebuild_time_index(self, cursor, title, page):
    """
    对同一《辞典》条目 (title, page) 的所有时间段条目的 time_index 进行规整，
    调整临时的非整数 time_index，
    使得 time_index 回归从 1 开始的连续整数
    """
    cursor.execute(
      f"""
      SELECT id
      FROM {self.entry_table}
      WHERE title = ? AND page = ?
      ORDER BY time_index
      """,
      (title, str(page)),
    )
    rows = cursor.fetchall()
    for idx, (entry_id,) in enumerate(rows, start=1):
      cursor.execute(
        f"UPDATE {self.entry_table} SET time_index = ? WHERE id = ?",
        (idx, entry_id),
      )
  
  def get_dict_indexes(self):
    """
    从《辞典》数据库中获取索引数据（title-page）
    """
    cursor = self._dict_conn.cursor()
    try:
      cursor.execute(
        f"""
        SELECT title, page
        FROM {self.dict_table}
        """
      )
      rows = cursor.fetchall()
      return set([f"{row[0]}-{row[1]}" for row in rows])
    except Exception as e:
      self._dict_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()

  def get_dict_entry(self, title, page):
    """
    查询《辞典》数据（search_dictionary）
    """
    cursor = self._dict_conn.cursor()
    try:
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, text, fields
        FROM {self.dict_table}
        WHERE title = ? AND page = ?
        """,
        (title, str(page)),
      )
      row = cursor.fetchone()
      if row is None:
        return {"error": f"未找到《辞典》条目: {title} (页码: {page})"}
      
      return {
        "id": row[0],
        "title": row[1],
        "catalog": row[2],
        "page": row[3],
        "text": row[4],
        "fields": json.loads(row[5]) if row[5] else {},
      }
    except Exception as e:
      self._dict_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()

  def get_table_entries(self, title, page):
    """
    查询已有官制条目数据（check_existing_entry）
    返回同一《辞典》条目在不同时间段上的所有记录，按 time_index 排序
    """
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE title = ? AND page = ?
        ORDER BY time_index, bgn_time, end_time, id
        """,
        (title, str(page)),
      )
      rows = cursor.fetchall()
      return [self._row_to_entry(r) for r in rows]
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  # ========= 写入工具 =========
  
  def update_attr(self, title, page, bgn_time, end_time, attr_key, attr_value):
    """
    更新官制条目的指定属性值（update_attr）
    直接覆盖原值；如果 attr_key 为 bgn_time 或 end_time，会自动重建 time_index
    """
    # 允许更新的字段白名单（不允许直接修改元属性或 time_index 属性）
    attr_whitelist = {
      "type",
      "subtype",
      "bgn_time",
      "bgn_event",
      "end_time",
      "end_event",
      "superiors",
      "subordinates",
      "staffing",
      "department",
      "grade",
    }
    list_attrs = {"superiors", "subordinates", "staffing"}
    
    if attr_key not in attr_whitelist:
      return {"error": f"无效的属性名: {attr_key}"}
    
    cursor = self._entry_conn.cursor()
    try:
      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {
          "error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"
        }
      
      if attr_key in list_attrs:
        attr_value = self._dumps_list(attr_value)
      
      cursor.execute(
        f"UPDATE {self.entry_table} SET {attr_key} = ? WHERE id = ?",
        (attr_value, entry_id),
      )
      
      # 如果更新了时间边界，需要重新维护 time_index
      if attr_key in {"bgn_time", "end_time"}:
        self._rebuild_time_index(cursor, title, page)
      
      self._entry_conn.commit()
      
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE id = ?
        """,
        (entry_id,),
      )
      row = cursor.fetchone()
      return self._row_to_entry(row) if row is not None else {
        "error": "更新成功但读取更新后对象失败"
      }
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  def append_list(self, title, page, bgn_time, end_time, attr_key, attr_value, index=None):
    """
    向官制条目的指定列表属性中插入值（append_list）
    """
    list_attrs = {"superiors", "subordinates", "staffing"}
    if attr_key not in list_attrs:
      return {"error": f"属性 {attr_key} 不是列表类型"}
    
    cursor = self._entry_conn.cursor()
    try:
      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {
          "error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"
        }
      
      cursor.execute(
        f"SELECT {attr_key} FROM {self.entry_table} WHERE id = ?",
        (entry_id,),
      )
      current_list = self._loads_list(cursor.fetchone()[0])
      
      if index is None:
        current_list.append(attr_value)
      else:
        if not isinstance(index, int):
          return {"error": "index 必须为 int 或 None"}
        if index < 0 or index > len(current_list):
          return {"error": f"index 越界: {index} (len={len(current_list)})"}
        current_list.insert(index, attr_value)
      
      new_list_str = json.dumps(current_list, ensure_ascii=False)
      cursor.execute(
        f"UPDATE {self.entry_table} SET {attr_key} = ? WHERE id = ?",
        (new_list_str, entry_id),
      )
      
      self._entry_conn.commit()
      
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE id = ?
        """,
        (entry_id,),
      )
      row = cursor.fetchone()
      return self._row_to_entry(row) if row is not None else {
        "error": "更新成功但读取更新后对象失败"
      }
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  def update_list(self, title, page, bgn_time, end_time, attr_key, attr_value, index):
    """
    更新官制条目的指定列表属性中的指定值（update_list）
    """
    list_attrs = {"superiors", "subordinates", "staffing"}
    if attr_key not in list_attrs:
      return {"error": f"属性 {attr_key} 不是列表类型"}
    if not isinstance(index, int):
      return {"error": "index 必须为 int"}
    
    cursor = self._entry_conn.cursor()
    try:
      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {
          "error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"
        }
      
      cursor.execute(
        f"SELECT {attr_key} FROM {self.entry_table} WHERE id = ?",
        (entry_id,),
      )
      current_list = self._loads_list(cursor.fetchone()[0])
      
      if index < 0 or index >= len(current_list):
        return {"error": f"索引 {index} 超出范围 (列表长度: {len(current_list)})"}
      
      current_list[index] = attr_value
      
      new_list_str = json.dumps(current_list, ensure_ascii=False)
      cursor.execute(
        f"UPDATE {self.entry_table} SET {attr_key} = ? WHERE id = ?",
        (new_list_str, entry_id),
      )
      
      self._entry_conn.commit()
      
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE id = ?
        """,
        (entry_id,),
      )
      row = cursor.fetchone()
      return self._row_to_entry(row) if row is not None else {
        "error": "更新成功但读取更新后对象失败"
      }
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  def remove_list(self, title, page, bgn_time, end_time, attr_key, attr_value, index):
    """
    删除官制条目的指定列表属性中的指定值（remove_list）
    """
    list_attrs = {"superiors", "subordinates", "staffing"}
    if attr_key not in list_attrs:
      return {"error": f"属性 {attr_key} 不是列表类型"}
    if not isinstance(index, int):
      return {"error": "index 必须为 int"}
    
    cursor = self._entry_conn.cursor()
    try:
      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {
          "error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"
        }
      
      cursor.execute(
        f"SELECT {attr_key} FROM {self.entry_table} WHERE id = ?",
        (entry_id,),
      )
      current_list = self._loads_list(cursor.fetchone()[0])
      
      if index < 0 or index >= len(current_list):
        return {"error": f"索引 {index} 超出范围 (列表长度: {len(current_list)})"}
      
      if current_list[index] != attr_value:
        return {
          "error": "索引位置的值不匹配，拒绝删除",
          "current": current_list[index],
          "expected": attr_value,
        }
      
      current_list.pop(index)
      
      new_list_str = json.dumps(current_list, ensure_ascii=False)
      cursor.execute(
        f"UPDATE {self.entry_table} SET {attr_key} = ? WHERE id = ?",
        (new_list_str, entry_id),
      )
      
      self._entry_conn.commit()
      
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE id = ?
        """,
        (entry_id,),
      )
      row = cursor.fetchone()
      return self._row_to_entry(row) if row is not None else {
        "error": "更新成功但读取更新后对象失败"
      }
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  def insert_time_point(self, title, page, bgn_time, end_time, time_point, event):
    """
    通过插入时间点的方式，拆分官制条目（insert_time_point）
    会将选定的时间段拆分为两个时间段，并自动重建所有相关条目的 time_index
    """
    cursor = self._entry_conn.cursor()
    try:
      # 找到待拆分的条目
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE title = ? AND page = ? AND bgn_time = ? AND end_time = ?
        """,
        (title, str(page), bgn_time, end_time),
      )
      row = cursor.fetchone()
      if row is None:
        return {
          "error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"
        }
      
      old = self._row_to_entry(row)
      entry_id = old["id"]
      
      # 插入两条新记录（复制旧记录其他字段）
      cursor.execute(
        f"""
        INSERT INTO {self.entry_table}
        (title, catalog, page, type, subtype,
         bgn_time, bgn_event, end_time, end_event,
         superiors, subordinates, staffing,
         department, grade, time_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          old["title"],
          old["catalog"],
          str(old["page"]),
          old["type"],
          old["subtype"],
          old["bgn_time"],
          old["bgn_event"],
          time_point,
          event,
          json.dumps(old["superiors"], ensure_ascii=False),
          json.dumps(old["subordinates"], ensure_ascii=False),
          json.dumps(old["staffing"], ensure_ascii=False),
          old["department"],
          old["grade"],
          old["time_index"] - 0.5,
        ),
      )
      id1 = cursor.lastrowid
      
      cursor.execute(
        f"""
        INSERT INTO {self.entry_table}
        (title, catalog, page, type, subtype,
         bgn_time, bgn_event, end_time, end_event,
         superiors, subordinates, staffing,
         department, grade, time_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          old["title"],
          old["catalog"],
          str(old["page"]),
          old["type"],
          old["subtype"],
          time_point,
          event,
          old["end_time"],
          old["end_event"],
          json.dumps(old["superiors"], ensure_ascii=False),
          json.dumps(old["subordinates"], ensure_ascii=False),
          json.dumps(old["staffing"], ensure_ascii=False),
          old["department"],
          old["grade"],
          old["time_index"] + 0.5,
        ),
      )
      id2 = cursor.lastrowid
      
      # 删除旧记录
      cursor.execute(
        f"DELETE FROM {self.entry_table} WHERE id = ?",
        (entry_id,),
      )
      
      # 重新维护 time_index
      self._rebuild_time_index(cursor, title, page)
      
      self._entry_conn.commit()
      
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE id IN (?, ?)
        ORDER BY time_index, id
        """,
        (id1, id2),
      )
      rows = cursor.fetchall()
      if len(rows) != 2:
        return {"error": "拆分成功但读取新对象失败"}
      return [self._row_to_entry(r) for r in rows]
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
  def expend_time_point(self, title, page, bgn_time, end_time, exp_type, time_point, event):
    """
    通过追加时间点的方式，扩展官制条目的时间范围（expend_time_point）
    exp_type:
      - "before": 选取最早时间段，在其开始时间前添加新时间点，产生一个新的条目，起始时间为新时间点，结束时间为原条目的起始时间
      - "after":  选取最晚时间段，在其结束时间后添加新时间点，产生一个新的条目，起始时间为原条目的结束时间，结束时间为新时间点
    会自动重建所有相关条目的 time_index
    """
    if exp_type not in {"before", "after"}:
      return {"error": f"无效的 exp_type: {exp_type}, 只能为 'before' 或 'after'"}
    
    cursor = self._entry_conn.cursor()
    try:
      # 先确保当前条目存在
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE title = ? AND page = ? AND bgn_time = ? AND end_time = ?
        """,
        (title, str(page), bgn_time, end_time),
      )
      row = cursor.fetchone()
      if row is None:
        return {
          "error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"
        }
      
      current = self._row_to_entry(row)
      
      # 取最小和最大 time_index，用于校验 exp_type 是否正确
      cursor.execute(
        f"""
        SELECT MIN(time_index), MAX(time_index)
        FROM {self.entry_table}
        WHERE title = ? AND page = ?
        """,
        (title, str(page)),
      )
      min_idx, max_idx = cursor.fetchone()
      
      if exp_type == "before" and current["time_index"] != min_idx:
        return {
          "error": "exp_type='before' 只能作用于最早时间段对应的条目，请检查元数据是否正确"
        }
      if exp_type == "after" and current["time_index"] != max_idx:
        return {
          "error": "exp_type='after' 只能作用于最晚时间段对应的条目，请检查元数据是否正确"
        }
      
      # 创建新条目（不修改原有条目）
      if exp_type == "before":
        # 在最早时间段之前创建新条目：起始时间为新时间点，结束时间为原条目的起始时间
        cursor.execute(
          f"""
          INSERT INTO {self.entry_table}
          (title, catalog, page, type, subtype,
           bgn_time, bgn_event, end_time, end_event,
           superiors, subordinates, staffing,
           department, grade, time_index)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          """,
          (
            current["title"],
            current["catalog"],
            str(current["page"]),
            current["type"],
            current["subtype"],
            time_point,
            event,
            current["bgn_time"],
            current["bgn_event"],
            json.dumps(current["superiors"], ensure_ascii=False),
            json.dumps(current["subordinates"], ensure_ascii=False),
            json.dumps(current["staffing"], ensure_ascii=False),
            current["department"],
            current["grade"],
            current["time_index"] - 0.5,
          ),
        )
      else:
        # 在最晚时间段之后创建新条目：起始时间为原条目的结束时间，结束时间为新时间点
        cursor.execute(
          f"""
          INSERT INTO {self.entry_table}
          (title, catalog, page, type, subtype,
           bgn_time, bgn_event, end_time, end_event,
           superiors, subordinates, staffing,
           department, grade, time_index)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          """,
          (
            current["title"],
            current["catalog"],
            str(current["page"]),
            current["type"],
            current["subtype"],
            current["end_time"],
            current["end_event"],
            time_point,
            event,
            json.dumps(current["superiors"], ensure_ascii=False),
            json.dumps(current["subordinates"], ensure_ascii=False),
            json.dumps(current["staffing"], ensure_ascii=False),
            current["department"],
            current["grade"],
            current["time_index"] + 0.5,
          ),
        )
      
      new_entry_id = cursor.lastrowid
      
      # 重新维护 time_index
      self._rebuild_time_index(cursor, title, page)
      
      self._entry_conn.commit()
      
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype,
               bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing,
               department, grade, time_index
        FROM {self.entry_table}
        WHERE id = ?
        """,
        (new_entry_id,),
      )
      row = cursor.fetchone()
      return self._row_to_entry(row) if row is not None else {
        "error": "扩展成功但读取新对象失败"
      }
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
    finally:
      cursor.close()
  
