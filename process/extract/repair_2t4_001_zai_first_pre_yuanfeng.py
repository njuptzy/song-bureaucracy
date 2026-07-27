#!/usr/bin/env python3
"""补修 #1“宰相”：元丰改制前三相所领馆职的制度时间点。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db"),
)


def main():
    with sqlite3.connect(DICT_DB) as conn:
        title, page, text, fields_json = conn.execute(
            "SELECT title,page,text,fields FROM chapter2t4 WHERE id=1"
        ).fetchone()
    assert title == "宰相"
    fields = json.loads(fields_json)
    quotation = (
        "如并置三员，元丰改制前，首相领昭文馆大学士、次相带兼修国史、"
        "末相领集贤殿大学士（《宋宰辅》卷1，建隆元年二月乙亥）。"
    )
    assert quotation in fields["编制"]

    writer = EntryWriter(ENTRY_DB, title, page)
    entity_id = writer.find_entity("宰相", "官职")
    assert entity_id
    timepoint_id = writer.timepoint(
        entity_id,
        "元丰改制前",
        "并置三相时，首相领昭文馆大学士、次相带兼修国史、末相领集贤殿大学士",
        "补入编制字段明确记载、此前遗漏的元丰改制前三相馆职配置节点。",
        quotation,
        attr_category="官称",
        chain="none",
    )
    citation = f"《宋代官制辞典》第{page}页“{title}”条"
    writer.citation(
        "Timepoints",
        timepoint_id,
        citation,
        quotation,
        "为元丰改制前三相所领馆职配置提供逐字证据。",
        note="编制；宰相为职任总称，不改写为统称与实例关系",
    )

    ordered_times = (
        "宋初",
        "元丰改制前",
        "北宋熙宁九年",
        "北宋元丰三年",
        "北宋元丰五年四月",
        "北宋元祐初",
        "北宋政和二年九月",
        "北宋靖康元年十一月",
        "南宋建炎三年四月",
        "南宋乾道八年",
    )
    ordered_ids = []
    for time in ordered_times:
        row = writer.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id=? AND time=? ORDER BY id LIMIT 1",
            (entity_id, time),
        ).fetchone()
        assert row, f"宰相缺时间点：{time}"
        ordered_ids.append(row[0])
    for pos, tid in enumerate(ordered_ids):
        writer.relink(
            tid,
            "补入元丰改制前三相馆职配置后重排宰相制度时间链。",
            prev_id=ordered_ids[pos - 1] if pos else None,
            succ_id=ordered_ids[pos + 1] if pos + 1 < len(ordered_ids) else None,
        )
    writer.commit()


if __name__ == "__main__":
    main()
