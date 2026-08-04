#!/usr/bin/env python3
"""
批量修复 v0620-regen-test 库中前后演变关系缺少改名时间点的问题。

规则：
- 扫描所有 relation_type='前后演变' 的关系
- 如果 source_timepoint.event 不含改/改名/改称/改为/并入/合并/复称/复旧/易等关键字
- 则在 source_entity 下新建一个"改名/改设"时间点，插入到 source_timepoint 之后
- 将前后演变关系的 subject_id 改为新时间点
- 为新时间点添加引用
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("agent-v0612/records/v0620-regen-test/song_bureaucracy_entries_v0620-regen-test.db")
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys=ON")
cur = conn.cursor()

# 关键字：如果 source event 包含这些，则认为已经是改名事件，不需要新建时间点
EVOLUTION_KEYWORDS = ["改", "并入", "合并", "复称", "复旧", "易", "由", "为"]

def is_evolution_event(event: str) -> bool:
    if not event:
        return False
    return any(kw in event for kw in EVOLUTION_KEYWORDS)

# 查询所有前后演变关系
cur.execute("""
SELECT r.id, r.subject_id, r.object_id,
       se.id AS src_entity_id, se.title AS src_title,
       st.time AS src_time, st.event AS src_event, st.attr_category AS src_cat,
       st.prev_id AS src_prev, st.succ_id AS src_succ,
       oe.id AS tgt_entity_id, oe.title AS tgt_title,
       ot.time AS tgt_time, ot.event AS tgt_event
FROM Relationships r
JOIN Timepoints st ON st.id=r.subject_id
JOIN Entities se ON se.id=st.entity_id
JOIN Timepoints ot ON ot.id=r.object_id
JOIN Entities oe ON oe.id=ot.entity_id
WHERE r.relation_type='前后演变'
ORDER BY r.id
""")
rows = cur.fetchall()

# 过滤出需要处理的关系
to_fix = []
for row in rows:
    (rid, src_tp, tgt_tp, src_eid, src_title, src_time, src_event, src_cat,
     src_prev, src_succ, tgt_eid, tgt_title, tgt_time, tgt_event) = row
    if not is_evolution_event(src_event or ""):
        to_fix.append(row)

print(f"总共 {len(rows)} 条前后演变关系，需要处理 {len(to_fix)} 条")

fixed_count = 0
for row in to_fix:
    (rid, src_tp, tgt_tp, src_eid, src_title, src_time, src_event, src_cat,
     src_prev, src_succ, tgt_eid, tgt_title, tgt_time, tgt_event) = row

    # 确定新时间点的 event 文本
    if "并入" in (tgt_event or "") or "合并" in (tgt_event or ""):
        new_event = f"{src_title}并入{tgt_title}"
    else:
        new_event = f"由{src_title}改为{tgt_title}"

    # 新时间点的 time：优先用 target_timepoint.time，若为空则用 source_timepoint.time
    new_time = tgt_time if tgt_time else src_time

    # 在 source_entity 下新建时间点，插入到 source_tp 之后
    cur.execute("""
        INSERT INTO Timepoints (entity_id, time, event, attr_category, prev_id, succ_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (src_eid, new_time, new_event, src_cat, src_tp, src_succ))
    new_tp = cur.lastrowid

    # 更新 source_tp 的 succ_id
    cur.execute("UPDATE Timepoints SET succ_id=? WHERE id=?", (new_tp, src_tp))

    # 如果 source_tp 原本有 succ，更新那个时间点的 prev_id
    if src_succ:
        cur.execute("UPDATE Timepoints SET prev_id=? WHERE id=?", (new_tp, src_succ))

    # 更新前后演变关系的 subject_id
    cur.execute("UPDATE Relationships SET subject_id=? WHERE id=?", (new_tp, rid))

    # 查找 source_entity 的 citation 模板
    cur.execute("""
        SELECT citation FROM Citations
        WHERE target_table='Timepoints' AND target_id=?
        ORDER BY id LIMIT 1
    """, (src_tp,))
    src_citation_row = cur.fetchone()

    if src_citation_row:
        citation_template = src_citation_row[0]
    else:
        # 如果没有 source_tp 的引用，尝试用原关系的引用
        cur.execute("""
            SELECT citation FROM Citations
            WHERE target_table='Relationships' AND target_id=?
            ORDER BY id LIMIT 1
        """, (rid,))
        rel_citation_row = cur.fetchone()
        citation_template = rel_citation_row[0] if rel_citation_row else f"《辞典》?页 “{src_title}” 词条"

    # 生成 quotation：优先用 target_tp.event，否则用新 event
    quotation = tgt_event if tgt_event else new_event

    # 添加引用
    cur.execute("""
        INSERT INTO Citations (target_table, target_id, citation, quotation, note)
        VALUES (?, ?, ?, ?, ?)
    """, ("Timepoints", new_tp, citation_template, quotation, f"前后演变关系#{rid}补充的改名时间点"))

    fixed_count += 1
    print(f"  关系 {rid}: {src_title} -> {tgt_title}, 新增 tp {new_tp}: {new_time} / {new_event}")

conn.commit()
conn.close()
print(f"完成，共处理 {fixed_count} 条关系")
