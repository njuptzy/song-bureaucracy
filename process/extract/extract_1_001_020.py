#!/usr/bin/env python3
"""提取第一编第1-20条：皇帝制度总条；具体帝王人物条目不落库。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter1 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(1, 21)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field_name=None):
    source = F[i]["fields"][field_name] if field_name else F[i]["text"]
    assert needle in source, (i, field_name, needle)
    return needle


def C(i, field_name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(w, table, target_id, i, quotation, decision, field_name=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field_name), quotation, decision, **kwargs
    )


def entry1():
    i = 1
    main = Q(i, "官名。")
    origin_quote = Q(
        i,
        "作为官名，始于公元前221年，秦王嬴政统一六国，自称“始皇帝”"
        "（《史记·秦始皇本纪》）。",
        "职源与沿革",
    )
    song_quote = Q(i, "秦汉以后，至宋，沿置不改。", "职源与沿革")
    duty_quote = Q(
        i,
        "作为封建国家最高统治者，总揽全国政权、军权、财权，发号施令，"
        "专制独裁。但皇帝的权力，也受到相权的制衡，与谏官、侍从官的干预。",
        "职掌",
    )

    w = W(i)
    entity_id = w.entity(
        "皇帝",
        "官职",
        "词条正文明言‘官名’，因此建为官职实体；不把历代皇帝人名或简称建为实体。",
        quotation=main,
    )
    origin_id = w.timepoint(
        entity_id,
        "公元前221年",
        "始作为官名，秦王嬴政自称始皇帝",
        "原文明确给出皇帝作为官名的起点。",
        origin_quote,
    )
    cite(
        w,
        "Timepoints",
        origin_id,
        i,
        origin_quote,
        "引文直接证明皇帝官名始于公元前221年。",
        "职源与沿革",
    )

    song_id = w.timepoint(
        entity_id,
        "宋代",
        "秦汉以后至宋沿置不改",
        "原文明言该官名至宋仍沿置，建立宋代制度状态。",
        song_quote,
        attr_category="封建国家最高统治者",
    )
    cite(
        w,
        "Timepoints",
        song_id,
        i,
        song_quote,
        "引文直接证明皇帝官名在宋代沿置不改。",
        "职源与沿革",
    )
    cite(
        w,
        "Timepoints",
        song_id,
        i,
        duty_quote,
        "补证宋代皇帝作为最高统治者的职掌与权力制衡。",
        "职掌",
    )
    cite(
        w,
        "Timepoints",
        song_id,
        i,
        main,
        "正文‘官名’补证皇帝的官职性质。",
    )
    w.commit()


SKIPPED_PERSON_ENTRIES = {
    2: "宋太祖",
    3: "宋太宗",
    4: "宋真宗",
    5: "宋仁宗",
    6: "宋英宗",
    7: "宋神宗",
    8: "宋哲宗",
    9: "宋徽宗",
    10: "宋钦宗",
    11: "宋高宗",
    12: "明受皇帝",
    13: "宋孝宗",
    14: "宋光宗",
    15: "宋宁宗",
    16: "宋理宗",
    17: "宋度宗",
    18: "宋恭帝",
    19: "宋端宗",
    20: "宋卫王",
}


def main():
    expected = {1: "皇帝", **SKIPPED_PERSON_ENTRIES}
    assert {i: F[i]["title"] for i in range(1, 21)} == expected
    entry1()
    for i, title in SKIPPED_PERSON_ENTRIES.items():
        print(f"#{i} {title}: person entry skipped")


if __name__ == "__main__":
    main()
