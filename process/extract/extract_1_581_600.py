#!/usr/bin/env python3
"""提取第一编第581-600条：御药院属司职役与内东门司。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
MERGED_DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db")
)


def repair_dictionary_source():
    """据原书第71-72页修复本批标点、字形和纪年括号。"""
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            for entry_id in (583, 589):
                row = conn.execute(f"SELECT text FROM {table} WHERE id=?", (entry_id,)).fetchone()
                assert row and row[0]
                conn.execute(
                    f"UPDATE {table} SET text=? WHERE id=?",
                    (row[0].rstrip("。") + "。", entry_id),
                )
            row = conn.execute(f"SELECT text FROM {table} WHERE id=590").fetchone()
            assert row and row[0]
            conn.execute(f"UPDATE {table} SET text=? WHERE id=590", (row[0].replace(")", "）"),))
            row = conn.execute(f"SELECT text FROM {table} WHERE id=593").fetchone()
            assert row and row[0]
            conn.execute(f"UPDATE {table} SET text=? WHERE id=593", (row[0].replace("祇应", "祗应"),))
            row = conn.execute(f"SELECT fields FROM {table} WHERE id=594").fetchone()
            assert row and row[0]
            f594 = json.loads(row[0])
            f594["职源与沿革"] = f594["职源与沿革"].replace("景德三年(1006)", "景德三年（1006）")
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=594",
                (json.dumps(f594, ensure_ascii=False),),
            )


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(581, 601)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def field(i, name):
    value = F[i]["fields"][name]
    assert value
    return value


def C(i, name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{name}字段）" if name else "")


def cite(w, table, target_id, i, quotation, decision, name=None, **kwargs):
    source = field(i, name) if name else F[i]["text"]
    assert quotation in source, (i, name, quotation)
    return w.citation(table, target_id, C(i, name), quotation, decision, **kwargs)


def timepoint(
    w, i, entity_id, time, event, quotation, decision, name=None,
    category=None, officer_type=None, grade=None, chain="tail", **cite_kwargs,
):
    tid = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer_type,
        attr_grade=grade, chain=chain,
    )
    cite(w, "Timepoints", tid, i, quotation, decision, name, **cite_kwargs)
    return tid


def relation(
    w, i, subject, object_, kind, quotation, decision, name=None,
    staff_type=None, staff_quota=None, **cite_kwargs,
):
    rid = w.relationship(
        subject, object_, kind, decision, quotation,
        staff_type=staff_type, staff_quota=staff_quota,
    )
    cite(w, "Relationships", rid, i, quotation, decision, name, **cite_kwargs)
    return rid


def find_entity(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def find_tp(w, title, time, type_=None):
    eid = find_entity(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


def medicine_tp(w):
    return find_tp(w, "御药院", "宋代（具体时间未载）", "机构")


def inner_province_tp(w):
    return find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构")


def inner_official_tp(w):
    return find_tp(w, "内侍官", "宋代（具体时间未载）", "官职")


def east_gate_tp(w):
    return find_tp(w, "内东门司", "北宋景德三年（1006）二月二十四日", "机构")


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；称谓不另建实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def distinct_entity(w, title, type_, quotation, decision):
    """同名异机构职役按词条原文分建实体，并保持幂等。"""
    row = w.conn.execute(
        "SELECT id FROM Entities WHERE title=? AND type=? AND quotation=? ORDER BY id LIMIT 1",
        (title, type_, quotation),
    ).fetchone()
    if row:
        return row[0]
    return w._insert(
        "INSERT INTO Entities (title,type,quotation) VALUES (?,?,?)",
        (title, type_, quotation), "Entities", decision,
    )


def medicine_suboffice(i):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "机构", "正式词头定义御药院办事机构。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）", main,
        main, f"建立御药院{F[i]['title']}办事节点。", category="御药院办事机构",
    )
    relation(
        w, i, medicine_tp(w), tp, "上下级机构", main,
        f"{F[i]['title']}为御药院办事机构。",
    )
    w.commit()


def entry581(): medicine_suboffice(581)
def entry582(): medicine_suboffice(582)


def entry583():
    i = 583
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = w.entity("勾当御药院", "官职", "正式词头定义御药院主管差遣。", quotation=main)
    start = timepoint(
        w, i, eid, "宋初", "设置，通领御药院公事",
        history, "建立勾当御药院宋初节点。", "职源与沿革", category="御药院主管官",
    )
    yuanfeng = timepoint(
        w, i, eid, "北宋元丰改制后", "多以四员为额",
        field(i, "编制"), "建立元丰后定额节点。", "编制", category="编制",
    )
    cite(w, "Timepoints", start, i, field(i, "职掌"), "补证主管御药院及殿中侍立职掌。", "职掌")
    cite(w, "Timepoints", start, i, field(i, "品位"), "补证充任资格与品位。", "品位")
    relation(
        w, i, medicine_tp(w), start, "编制隶属", main,
        "勾当御药院隶御药院。", staff_type="主管官",
    )
    relation(
        w, i, inner_official_tp(w), start, "统称与实例", field(i, "品位"),
        "勾当御药院由入内内侍省内侍充任，属于内侍官差遣。", "品位",
    )
    alias_citation(w, i, start, "别名")
    w.commit()


def entry584():
    i = 584
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("干办御药院", "官职", "正式词头定义南宋避讳后的御药院主管差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋时期（1127—1279）",
        "避高宗赵构讳，由勾当御药院改称干办御药院",
        main, "建立干办御药院南宋节点。", category="御药院主管官",
    )
    relation(
        w, i, find_tp(w, "勾当御药院", "北宋元丰改制后", "官职"),
        tp, "前后演变", main, "南宋避讳，勾当御药院改称干办御药院。",
    )
    relation(
        w, i, medicine_tp(w), tp, "编制隶属", main,
        "干办御药院为御药院主管差遣。", staff_type="主管官",
    )
    alias_citation(w, i, tp, "简称与别名")
    w.commit()


def entry585():
    i = 585
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("主管御药院", "官职", "正式词头定义南宋御药院主管职事官。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋时期（1127—1279）",
        "由管勾御药院改称主管御药院",
        main, "建立主管御药院南宋节点。", category="御药院主管官",
    )
    relation(
        w, i, find_tp(w, "勾当御药院", "北宋元丰改制后", "官职"),
        tp, "前后演变", main,
        "管勾御药院即勾当御药院，南宋改称主管御药院。",
        note="管勾御药院据#583别名字段为勾当御药院同称",
    )
    relation(
        w, i, medicine_tp(w), tp, "编制隶属", main,
        "主管御药院为御药院主管职事官。", staff_type="主管官",
    )
    alias_citation(w, i, tp, "别名")
    w.commit()


def medicine_duty(i, start_time, start_event, end_time=None, history_name="职源与沿革"):
    w = W(i)
    main = F[i]["text"]
    history = field(i, history_name) if history_name else main
    eid = w.entity(F[i]["title"], "官职", "正式词头定义御药院内侍差遣。", quotation=main)
    start = timepoint(
        w, i, eid, start_time, start_event,
        history, f"建立{F[i]['title']}始置节点。", history_name,
        category="御药院内侍差遣",
    )
    if end_time:
        timepoint(
            w, i, eid, end_time, "罢置",
            history, f"建立{F[i]['title']}罢置节点。", history_name, category="废罢",
        )
    for name in ("职掌", "品位", "编制"):
        if name in F[i]["fields"]:
            cite(w, "Timepoints", start, i, field(i, name), f"补证{F[i]['title']}{name}。", name)
    relation(
        w, i, medicine_tp(w), start, "编制隶属", main,
        f"{F[i]['title']}隶御药院。", staff_type="内侍差遣",
    )
    relation(
        w, i, inner_official_tp(w), start, "统称与实例", main,
        f"{F[i]['title']}由内侍充任，属于内侍官差遣。",
    )
    w.commit()


def entry586():
    medicine_duty(
        586, "北宋天圣六年（1028）二月十二日", "设置",
        "北宋明道二年（1033）四月十八日",
    )


def entry587():
    i = 587
    medicine_duty(
        i, "北宋天圣四年（1026）二月一日", "始置",
        "北宋明道二年（1033）四月十八日", history_name="职源",
    )
    w = W(i)
    relation(
        w, i,
        find_tp(w, "上御药供奉", "北宋天圣四年（1026）二月一日", "官职"),
        find_tp(w, "上御药", "北宋天圣六年（1028）二月十二日", "官职"),
        "前后演变", field(i, "品位"),
        "天圣六年，上御药供奉去“供奉”称上御药。", "品位",
    )
    w.commit()


def entry588():
    i = 588
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("御药院祗候", "官职", "正式词头定义御药院宦官差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）", "以宦官充，在御药院供职",
        main, "建立御药院祗候节点。", category="御药院内侍差遣",
    )
    relation(w, i, medicine_tp(w), tp, "编制隶属", main, "御药院祗候隶御药院。", staff_type="祗候")
    relation(w, i, inner_official_tp(w), tp, "统称与实例", main, "御药院祗候由宦官充任，属于内侍官差遣。")
    w.commit()


def medicine_clerk(i, category, distinct=False):
    w = W(i)
    main = F[i]["text"]
    if distinct:
        eid = distinct_entity(
            w, F[i]["title"], "官职", main,
            f"本条{F[i]['title']}隶御药院，与其他机构同名职役分建实体。",
        )
    else:
        eid = w.entity(F[i]["title"], "官职", "正式词头定义御药院吏役。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（御药院，具体时间未载）", main,
        main, f"建立御药院{F[i]['title']}节点。", category=category, officer_type="吏人",
    )
    relation(
        w, i, medicine_tp(w), tp, "编制隶属", main,
        f"{F[i]['title']}隶御药院。", staff_type=category,
    )
    for name in F[i]["fields"]:
        alias_citation(w, i, tp, name)
    w.commit()


def entry589(): medicine_clerk(589, "御药院吏人")
def entry590(): medicine_clerk(590, "御药院给使", distinct=True)
def entry591(): medicine_clerk(591, "御药院祗应吏人")
def entry592(): medicine_clerk(592, "御药院祗应吏人")
def entry593(): medicine_clerk(593, "御药院祗应吏人")


def entry594():
    i = 594
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, "内东门司", "机构")
    start = timepoint(
        w, i, eid, "北宋景德三年（1006）二月二十四日",
        "由内东门取索司改名，隶入内内侍省",
        history, "建立内东门司改名始置节点。", "职源与沿革",
        category="入内内侍省属司", chain="head",
    )
    generic = find_tp(w, "内东门司", "宋代（具体时间未载）", "机构")
    cite(w, "Timepoints", generic, i, history, "补证内东门司南宋沿置。", "职源与沿革")
    for name in ("职掌", "序位", "编制"):
        cite(w, "Timepoints", start, i, field(i, name), f"补证内东门司{name}。", name)
    relation(
        w, i, inner_province_tp(w), start, "上下级机构", main,
        "内东门司隶入内内侍省。",
    )
    alias_citation(w, i, start, "简称")
    w.commit()


def entry595():
    i = 595
    w = W(i)
    main = F[i]["text"]
    stages = (
        ("内库门取索司", "北宋太平兴国年间（976—984）", "设置，掌承诏宣取宝货及贡献物品等"),
        ("内门取索司", "北宋太平兴国以后（具体时间未载）", "由内库门取索司改称"),
        ("内东门取索司", "北宋真宗朝景德三年以前（997—1006）", "真宗朝改称内东门取索司"),
    )
    points = []
    for title, when, event in stages:
        eid = w.entity(title, "机构", "正文记载内东门司改名前的历史官署名。", quotation=main)
        points.append(timepoint(
            w, i, eid, when, event, main,
            f"建立{title}历史节点。", category="内庭取索机构",
        ))
    relation(w, i, points[0], points[1], "前后演变", main, "内库门取索司后改称内门取索司。")
    relation(w, i, points[1], points[2], "前后演变", main, "真宗朝内门取索司改称内东门取索司。")
    relation(
        w, i, points[2], east_gate_tp(w), "前后演变", main,
        "景德三年二月二十四日，内东门取索司改名内东门司。",
    )
    alias_citation(w, i, points[2], "简称")
    w.commit()


def entry596():
    i = 596
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = w.entity("勾当内东门司", "官职", "正式词头定义内东门司主管差遣。", quotation=main)
    start = timepoint(
        w, i, eid, "北宋景德三年（1006）二月", "始置，主管内东门司",
        history, "建立勾当内东门司始置节点。", "职源与沿革", category="内东门司主管官",
    )
    south = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "沿置，改称干办内东门司",
        history, "建立南宋改称节点。", "职源与沿革", category="内东门司主管官",
    )
    for name in ("职掌", "品位", "编制"):
        cite(w, "Timepoints", start, i, field(i, name), f"补证勾当内东门司{name}。", name)
    relation(
        w, i, east_gate_tp(w), start, "编制隶属", main,
        "勾当内东门司隶内东门司。", staff_type="主管官", staff_quota="四人",
    )
    relation(
        w, i, inner_official_tp(w), start, "统称与实例", field(i, "品位"),
        "勾当内东门司以入内内侍省内侍充任，属于内侍官差遣。", "品位",
    )
    alias_citation(w, i, start, "简称与别名")
    w.commit()


def entry597():
    i = 597
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("干办内东门司", "官职", "正式词头定义南宋改称后的内东门司主管差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "由勾当内东门司改称",
        main, "建立干办内东门司南宋节点。", category="内东门司主管官",
    )
    relation(
        w, i, find_tp(w, "勾当内东门司", "南宋时期（1127—1279）", "官职"),
        tp, "前后演变", main, "南宋勾当内东门司改称干办内东门司。",
    )
    relation(w, i, east_gate_tp(w), tp, "编制隶属", main, "干办内东门司隶内东门司。", staff_type="主管官")
    alias_citation(w, i, tp, "别称")
    w.commit()


def east_gate_clerk(i, category):
    w = W(i)
    main = F[i]["text"]
    eid = distinct_entity(
        w, F[i]["title"], "官职", main,
        f"本条{F[i]['title']}隶内东门司，与其他机构同名职役分建实体。",
    )
    tp = timepoint(
        w, i, eid, "宋代（内东门司，具体时间未载）", main,
        main, f"建立内东门司{F[i]['title']}节点。", category=category, officer_type="吏人",
    )
    relation(
        w, i, east_gate_tp(w), tp, "编制隶属", main,
        f"{F[i]['title']}隶内东门司。", staff_type="吏人",
    )
    w.commit()


def entry598(): east_gate_clerk(598, "内东门司首等吏人")
def entry599(): east_gate_clerk(599, "内东门司吏人")
def entry600(): east_gate_clerk(600, "内东门司吏人")


def main():
    assert [F[i]["title"] for i in range(581, 601)] == [
        "开拆司", "合行案", "勾当御药院", "干办御药院", "主管御药院", "上御药",
        "上御药供奉", "御药院祗候", "典事", "药童", "封题学生", "封题书艺学",
        "书写崇奉祖宗表词待诏", "内东门司", "内东门取索司", "勾当内东门司",
        "干办内东门司", "押司官", "前行", "后行",
    ]
    assert F[583]["text"].endswith("。") and F[589]["text"].endswith("。")
    assert ")" not in F[590]["text"] and "祗应吏人" in F[593]["text"]
    assert "景德三年（1006）" in field(594, "职源与沿革")
    entry581(); entry582(); entry583(); entry584(); entry585(); entry586(); entry587(); entry588()
    entry589(); entry590(); entry591(); entry592(); entry593(); entry594(); entry595(); entry596()
    entry597(); entry598(); entry599(); entry600()


if __name__ == "__main__":
    main()
