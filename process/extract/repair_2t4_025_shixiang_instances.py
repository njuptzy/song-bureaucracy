#!/usr/bin/env python3
"""补齐 #25“使相”的明确复合官名实例及元丰前后演变。"""
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


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (i,)
        ).fetchone()
    fields = json.loads(row[3] or "{}")
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "all": "\n".join(
            [row[2] or ""]
            + [str(v) for k, v in fields.items() if not k.startswith("_")]
        ),
    }


F = {i: load(i) for i in (25, 26)}
Q_TANG = (
    "使相之名，从唐玄宗朝起，始与宰相分列。凡带三省长官（尚书令、中书令、"
    "纳言或侍中）及同中书门下平章事或同中书门下三品，在外任节度使或他官者，"
    "都列为使相（《唐会要》卷1）。"
)
Q_SONG = (
    "宋初，凡节度使、枢密使、亲王、留守、检校官兼中书令、侍中、"
    "同中书门下平章事，为使相（《长编》卷17，开宝九年二月庚戌）。"
)
Q_REFORM = (
    "北宋元丰改官制，同中书门下平章事易以开府仪同三司，亦带节度使，"
    "称使相（《石林燕语》卷4）。"
)


def cite(w, table, rid, i, quotation, decision, **kwargs):
    citation = f"《宋代官制辞典》第{F[i]['page']}页“{F[i]['title']}”条"
    return w.citation(table, rid, citation, quotation, decision, **kwargs)


def rel(w, source, target, kind, i, quotation, decision):
    rid = w.relationship(source, target, kind, decision, quotation)
    cite(w, "Relationships", rid, i, quotation, decision)
    return rid


def main():
    assert Q_TANG in F[25]["all"]
    assert Q_SONG in F[25]["all"]
    assert Q_REFORM in F[26]["all"]

    # 唐、宋初：节度使带同中书门下平章事，是原文与相邻专条均明确的使相形态。
    w = EntryWriter(ENTRY_DB, F[25]["title"], F[25]["page"])
    shixiang = w.find_entity("使相", "官职"); assert shixiang
    old = w.find_entity("节度使、同中书门下平章事", "官职"); assert old
    sx_tang = w.find_timepoint(shixiang, "唐玄宗朝"); assert sx_tang
    sx_song = w.find_timepoint(shixiang, "宋初"); assert sx_song
    old_tang = w.find_timepoint(old, "唐"); assert old_tang
    old_end = w.find_timepoint(old, "北宋元丰改制"); assert old_end
    old_song = w.timepoint(
        old, "宋初", "节度使带同中书门下平章事，为使相",
        "补建宋初明确的节度使、同中书门下平章事实例节点。",
        Q_SONG, attr_category="使相形态", chain="none",
    )
    cite(
        w, "Timepoints", old_song, 25, Q_SONG,
        "宋初原文明载节度使兼同中书门下平章事为使相。",
    )
    for pos, tid in enumerate((old_tang, old_song, old_end)):
        w.relink(
            tid,
            "按唐、宋初、元丰改制重排节度使带相衔时间链。",
            prev_id=(old_tang, old_song, old_end)[pos - 1] if pos else None,
            succ_id=(old_tang, old_song, old_end)[pos + 1] if pos < 2 else None,
        )
    rel(
        w, sx_tang, old_tang, "统称与实例", 25, Q_TANG,
        "唐玄宗朝使相范围明确包括在外任节度使而带同中书门下平章事者。",
    )
    rel(
        w, sx_song, old_song, "统称与实例", 25, Q_SONG,
        "宋初使相明确包括节度使兼同中书门下平章事这一复合官名。",
    )
    w.commit()

    # 元丰后：另建节度使、开府仪同三司，不能继续把新形态塞在旧实体上。
    w = EntryWriter(ENTRY_DB, F[26]["title"], F[26]["page"])
    new = w.entity(
        "节度使、开府仪同三司", "官职",
        "元丰改制后明确以开府仪同三司带节度使为使相，建立新复合官名实体。",
        quotation=Q_REFORM,
    )
    new_tp = w.timepoint(
        new, "北宋元丰改制", "开府仪同三司带节度使，称使相",
        "建立元丰改制后的使相形态节点。", Q_REFORM,
        attr_category="使相形态",
    )
    cite(
        w, "Timepoints", new_tp, 26, Q_REFORM,
        "元丰改制后开府仪同三司带节度使为使相。",
    )
    old = w.find_entity("节度使、同中书门下平章事", "官职"); assert old
    old_end = w.find_timepoint(old, "北宋元丰改制"); assert old_end
    rel(
        w, old_end, new_tp, "前后演变", 26, Q_REFORM,
        "元丰改制以开府仪同三司替代同中书门下平章事，二者均带节度使。",
    )
    shixiang = w.find_entity("使相", "官职"); assert shixiang
    sx_reform = w.find_timepoint(shixiang, "北宋元丰改制"); assert sx_reform
    rel(
        w, sx_reform, new_tp, "统称与实例", 26, Q_REFORM,
        "元丰改制后的使相实例为节度使、开府仪同三司。",
    )
    w.commit()


if __name__ == "__main__":
    main()
