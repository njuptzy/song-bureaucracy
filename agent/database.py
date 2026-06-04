import sqlite3
import re
import json

"""
构建信息获取与写入工具
Database 类封装了所有数据库操作方法
"""


class Database:
  # 字段白名单（防 SQL 注入）
  _entry_attr_whitelist = {
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
  _entry_list_attr_whitelist = {"superiors", "subordinates", "staffing"}
  
  def __init__(self, dict_db_path, entry_db_path, dict_table, entry_table, indexes):
    """
    初始化 Database 实例
    
    Args:
      dict_db_path: 《辞典》数据库路径
      entry_db_path: 官制条目数据库路径
      dict_table: 《辞典》数据表名
      entry_table: 官制条目数据表名
      indexes: 索引集合，格式为 set of "名称-页码" 字符串
    """
    self.dict_db_path = dict_db_path
    self.entry_db_path = entry_db_path
    self.dict_table = dict_table
    self.entry_table = entry_table
    self.indexes = indexes
    
    # 在初始化时建立数据库连接
    self._dict_conn = sqlite3.connect(self.dict_db_path)
    self._entry_conn = sqlite3.connect(self.entry_db_path)
  
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
    # 允许直接传入 JSON 字符串
    if isinstance(v, str):
      try:
        x = json.loads(v)
        if isinstance(x, list):
          return json.dumps(x, ensure_ascii=False)
      except Exception:
        pass
    raise ValueError("列表字段要求 list 或可解析为 list 的 JSON 字符串")

  def _row_to_entry_obj(self, row):
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
    }

  def _fetch_entry_by_id(self, cursor, entry_id):
    cursor.execute(
      f"""
      SELECT id, title, catalog, page, type, subtype, bgn_time, bgn_event, end_time, end_event,
             superiors, subordinates, staffing, department, grade
      FROM {self.entry_table}
      WHERE id = ?
      """,
      (entry_id,),
    )
    row = cursor.fetchone()
    if row is None:
      return None
    return self._row_to_entry_obj(row)

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

  def _is_indexed_format(self, name):
    """
    检查字符串是否符合 "名称-页码" 格式
    
    Args:
      name: 待检查的字符串
    
    Returns:
      bool: 如果符合格式返回 True，否则返回 False
    """
    if not isinstance(name, str) or not name:
      return False
    # 检查是否以 "-数字" 结尾
    return bool(re.search(r'-\d+$', name))
  
  def _validate_entry_ref(self, name):
    """
    验证条目引用是否存在于索引中
    仅当 name 符合 "名称-页码" 格式时才检查
    
    Args:
      name: 条目名称字符串
    
    Returns:
      dict: 如果验证失败返回 {"error": "..."}, 否则返回 None
    """
    # 如果不是索引格式，跳过检查
    if not self._is_indexed_format(name):
      return None
    
    # 检查是否在索引中
    if name not in self.indexes:
      return {"error": f"引用的条目不存在于索引中: {name}"}
    return None
  
  def _validate_string_list(self, items, field_name):
    """
    验证字符串列表中的所有条目引用
    
    Args:
      items: 字符串列表
      field_name: 字段名（用于错误提示）
    
    Returns:
      dict: 如果验证失败返回 {"error": "..."}, 否则返回 None
    """
    if not isinstance(items, list):
      return {"error": f"字段 {field_name} 必须为 list 类型"}
    
    for i, item in enumerate(items):
      if not isinstance(item, str):
        return {"error": f"字段 {field_name} 的元素 [{i}] 必须为 str 类型"}
      
      # 只检查符合索引格式的字符串
      err = self._validate_entry_ref(item)
      if err is not None:
        return {"error": f"字段 {field_name} 的元素 [{i}] 引用无效: {err['error']}"}
    
    return None
  
  def _validate_staffing_list(self, items):
    """
    验证 staffing 列表中的所有条目引用
    staffing 格式：[[职位名称(str), 类别(str), 编制数量(num)], ...]
    
    Args:
      items: staffing 列表
    
    Returns:
      dict: 如果验证失败返回 {"error": "..."}, 否则返回 None
    """
    if not isinstance(items, list):
      return {"error": "字段 staffing 必须为 list 类型"}
    
    for i, item in enumerate(items):
      if not isinstance(item, list):
        return {"error": f"字段 staffing 的元素 [{i}] 必须为 list 类型（三元组）"}
      if len(item) != 3:
        return {"error": f"字段 staffing 的元素 [{i}] 必须包含 3 个元素（职位名称, 类别, 编制数量）"}
      
      position_name = item[0]
      if not isinstance(position_name, str):
        return {"error": f"字段 staffing 的元素 [{i}] 的职位名称必须为 str 类型"}
      
      # 只检查符合索引格式的职位名称
      err = self._validate_entry_ref(position_name)
      if err is not None:
        return {"error": f"字段 staffing 的元素 [{i}] 职位名称引用无效: {err['error']}"}
    
    return None
  
  # ========== 读取工具 ==========
  
  def search_dictionary(self, title, page):
    """查询《辞典》数据"""
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
        return {"error": f"未找到条目: {title} (页码: {page})"}

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

  def check_existing_entry(self, title, page):
    """查询已有官制条目数据"""
    cursor = self._entry_conn.cursor()
    try:
      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype, bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing, department, grade
        FROM {self.entry_table}
        WHERE title = ? AND page = ?
        ORDER BY bgn_time, end_time, id
        """,
        (title, str(page)),
      )

      rows = cursor.fetchall()
      # 按文档约定：查不到返回空列表（不算错误）
      return [self._row_to_entry_obj(r) for r in rows]
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}

  # ========== 写入工具 ==========
  
  def insert(self, title, page, bgn_time, end_time, attr_key, attr_value):
    """填入官制条目的指定属性（创建）"""
    # 对于引用字段，需要额外验证
    if attr_key == "department":
      if attr_value is not None and attr_value != "":
        # department 是字符串
        err = self._validate_entry_ref(attr_value)
        if err is not None:
          return err
    
    elif attr_key in ["superiors", "subordinates"]:
      # 字符串列表
      err = self._validate_string_list(attr_value, attr_key)
      if err is not None:
        return err
    
    elif attr_key == "staffing":
      # staffing 是三元组列表
      err = self._validate_staffing_list(attr_value)
      if err is not None:
        return err
    
    cursor = self._entry_conn.cursor()
    try:
      if attr_key not in self._entry_attr_whitelist:
        return {"error": f"无效的属性名: {attr_key}"}

      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {"error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"}

      cursor.execute(
        f"SELECT {attr_key} FROM {self.entry_table} WHERE id = ?",
        (entry_id,),
      )
      current_value = cursor.fetchone()[0]
      if current_value is not None and current_value != "" and current_value != "[]":
        return {"error": f"属性 {attr_key} 已有值: {current_value}，请使用 update"}

      if attr_key in self._entry_list_attr_whitelist:
        attr_value = self._dumps_list(attr_value)

      cursor.execute(
        f"UPDATE {self.entry_table} SET {attr_key} = ? WHERE id = ?",
        (attr_value, entry_id),
      )
      self._entry_conn.commit()

      obj = self._fetch_entry_by_id(cursor, entry_id)
      return obj if obj is not None else {"error": "写入成功但读取更新后对象失败"}
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
  
  def update(self, title, page, bgn_time, end_time, attr_key, attr_value):
    """更新官制条目的指定属性（覆盖）"""
    # 对于引用字段，需要额外验证
    if attr_key == "department":
      if attr_value is not None and attr_value != "":
        err = self._validate_entry_ref(attr_value)
        if err is not None:
          return err
    
    elif attr_key in ["superiors", "subordinates"]:
      err = self._validate_string_list(attr_value, attr_key)
      if err is not None:
        return err
    
    elif attr_key == "staffing":
      err = self._validate_staffing_list(attr_value)
      if err is not None:
        return err
    
    cursor = self._entry_conn.cursor()
    try:
      if attr_key not in self._entry_attr_whitelist:
        return {"error": f"无效的属性名: {attr_key}"}

      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {"error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"}

      if attr_key in self._entry_list_attr_whitelist:
        attr_value = self._dumps_list(attr_value)

      cursor.execute(
        f"UPDATE {self.entry_table} SET {attr_key} = ? WHERE id = ?",
        (attr_value, entry_id),
      )
      self._entry_conn.commit()

      obj = self._fetch_entry_by_id(cursor, entry_id)
      return obj if obj is not None else {"error": "更新成功但读取更新后对象失败"}
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
  
  def append_list(self, title, page, bgn_time, end_time, attr_key, attr_value, index=None):
    """插入官制条目的指定列表属性（添加）"""
    # 对于引用列表字段，需要验证新增的元素
    if attr_key in ["superiors", "subordinates"]:
      if not isinstance(attr_value, str):
        return {"error": f"字段 {attr_key} 的元素必须为 str 类型"}
      err = self._validate_entry_ref(attr_value)
      if err is not None:
        return err
    
    elif attr_key == "staffing":
      if not isinstance(attr_value, list) or len(attr_value) != 3:
        return {"error": "staffing 的元素必须为三元组 list [职位名称, 类别, 编制数量]"}
      if not isinstance(attr_value[0], str):
        return {"error": "staffing 元素的职位名称必须为 str 类型"}
      err = self._validate_entry_ref(attr_value[0])
      if err is not None:
        return err
    
    cursor = self._entry_conn.cursor()
    try:
      if attr_key not in self._entry_list_attr_whitelist:
        return {"error": f"属性 {attr_key} 不是列表类型"}

      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {"error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"}

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

      obj = self._fetch_entry_by_id(cursor, entry_id)
      return obj if obj is not None else {"error": "更新成功但读取更新后对象失败"}
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
  
  def update_list(self, title, page, bgn_time, end_time, attr_key, attr_value, index):
    """修改官制条目的指定列表属性（修改）"""
    # 对于引用列表字段，需要验证更新后的元素
    if attr_key in ["superiors", "subordinates"]:
      if not isinstance(attr_value, str):
        return {"error": f"字段 {attr_key} 的元素必须为 str 类型"}
      err = self._validate_entry_ref(attr_value)
      if err is not None:
        return err
    
    elif attr_key == "staffing":
      if not isinstance(attr_value, list) or len(attr_value) != 3:
        return {"error": "staffing 的元素必须为三元组 list [职位名称, 类别, 编制数量]"}
      if not isinstance(attr_value[0], str):
        return {"error": "staffing 元素的职位名称必须为 str 类型"}
      err = self._validate_entry_ref(attr_value[0])
      if err is not None:
        return err
    
    cursor = self._entry_conn.cursor()
    try:
      if attr_key not in self._entry_list_attr_whitelist:
        return {"error": f"属性 {attr_key} 不是列表类型"}
      if not isinstance(index, int):
        return {"error": "index 必须为 int"}

      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {"error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"}

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

      obj = self._fetch_entry_by_id(cursor, entry_id)
      return obj if obj is not None else {"error": "更新成功但读取更新后对象失败"}
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
  
  def remove_list(self, title, page, bgn_time, end_time, attr_key, attr_value, index):
    """删除官制条目的指定列表属性（删除）"""
    # remove_list 不需要额外的引用验证，因为是删除操作
    cursor = self._entry_conn.cursor()
    try:
      if attr_key not in self._entry_list_attr_whitelist:
        return {"error": f"属性 {attr_key} 不是列表类型"}
      if not isinstance(index, int):
        return {"error": "index 必须为 int"}

      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {"error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"}

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

      obj = self._fetch_entry_by_id(cursor, entry_id)
      return obj if obj is not None else {"error": "更新成功但读取更新后对象失败"}
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
  
  def new_time_point(self, title, page, bgn_time, end_time, time_point, event):
    """通过添加时间点的方式，拆分官制条目"""
    cursor = self._entry_conn.cursor()
    try:
      entry_id = self._fetch_entry_by_meta(cursor, title, page, bgn_time, end_time)
      if entry_id is None:
        return {"error": f"未找到条目 (title={title}, page={page}, bgn_time={bgn_time}, end_time={end_time})"}

      cursor.execute(
        f"""
        SELECT id, title, catalog, page, type, subtype, bgn_time, bgn_event, end_time, end_event,
               superiors, subordinates, staffing, department, grade
        FROM {self.entry_table}
        WHERE id = ?
        """,
        (entry_id,),
      )
      row = cursor.fetchone()
      if row is None:
        return {"error": "读取待拆分条目失败"}

      old = self._row_to_entry_obj(row)

      # 插入两条新记录（复制旧记录其他字段）
      cursor.execute(
        f"""
        INSERT INTO {self.entry_table}
        (title, catalog, page, type, subtype, bgn_time, bgn_event, end_time, end_event,
         superiors, subordinates, staffing, department, grade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ),
      )
      id1 = cursor.lastrowid

      cursor.execute(
        f"""
        INSERT INTO {self.entry_table}
        (title, catalog, page, type, subtype, bgn_time, bgn_event, end_time, end_event,
         superiors, subordinates, staffing, department, grade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ),
      )
      id2 = cursor.lastrowid

      # 删除旧记录
      cursor.execute(
        f"DELETE FROM {self.entry_table} WHERE id = ?",
        (entry_id,),
      )

      self._entry_conn.commit()

      obj1 = self._fetch_entry_by_id(cursor, id1)
      obj2 = self._fetch_entry_by_id(cursor, id2)
      if obj1 is None or obj2 is None:
        return {"error": "拆分成功但读取新对象失败"}
      return [obj1, obj2]
    except Exception as e:
      self._entry_conn.rollback()
      return {"error": str(e)}
