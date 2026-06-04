import sqlite3

def create_entry_database(dict_db_path, entry_db_path, dict_table, entry_table):
  # 从《辞典》数据库中获取全部条目信息，并据此创建条目表
  conn_dict = sqlite3.connect(dict_db_path)
  cursor_dict = conn_dict.cursor()
  cursor_dict.execute(f"SELECT title, catalog, page FROM {dict_table}")

  entry_list = []
  for row in cursor_dict.fetchall():
    entry_list.append({
      "title": row[0],
      "catalog": row[1],
      "page": row[2]
    })
  print(len(entry_list))

  cursor_dict.close()
  conn_dict.close()

  # 连接到条目数据库
  conn_entry = sqlite3.connect(entry_db_path)
  cursor_entry = conn_entry.cursor()

  cursor_entry.execute(f"""DROP TABLE IF EXISTS {entry_table}""")
  cursor_entry.execute(f"""
  CREATE TABLE IF NOT EXISTS {entry_table} (
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
      superiors TEXT,
      subordinates TEXT,
      staffing TEXT,
      department TEXT,
      grade TEXT
  )
  """)

  # 从 entry_list 插入初始数据
  cursor_entry.executemany(f"""
  INSERT INTO {entry_table} (title, catalog, page, bgn_time, bgn_event, end_time, end_event, superiors, subordinates, staffing)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  """, [
    (
      entry["title"],
      entry["catalog"],
      entry["page"],
      "-INF",      # bgn_time 初始值
      "始置",      # bgn_event 初始值
      "INF",       # end_time 初始值
      "罢置",      # end_event 初始值
      "[]",        # superiors 初始值（空列表）
      "[]",        # subordinates 初始值（空列表）
      "[]"         # staffing 初始值（空列表）
    )
    for entry in entry_list
  ])

  conn_entry.commit()

  # 验证插入结果
  cursor_entry.execute(f"SELECT COUNT(*) FROM {entry_table}")
  count = cursor_entry.fetchone()[0]
  print(f"成功插入 {count} 条记录到 {entry_table} 表")

  # 查看前几条记录
  cursor_entry.execute(f'SELECT id, title, catalog, page, bgn_time, bgn_event, end_time, end_event FROM {entry_table} LIMIT 5')
  for row in cursor_entry.fetchall():
    print(f"Id: {row[0]}, Title: {row[1]}, Page: {row[3]}, bgn_time: {row[4]}, bgn_event: {row[5]}, end_time: {row[6]}, end_event: {row[7]}")

  cursor_entry.close()
  conn_entry.close()