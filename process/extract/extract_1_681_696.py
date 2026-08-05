#!/usr/bin/env python3
"""提取第一编第681-696条：翰林医官职阶、内宿差遣与医职统称。"""

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

MEDICAL_SPECIALTIES = (
    ("大方脉医官", "大方脉", "五员"),
    ("小方脉医官", "小方脉", "三员"),
    ("风科医官", "风科", None),
    ("口齿科医官", "口齿科", None),
    ("眼科医官", "眼科", None),
    ("针科医官", "针科", None),
    ("疮肿科医官", "疮肿科", None),
    ("产科医官", "产科", None),
)
MEDICAL_OFFICES = ("翰林医效", "翰林医痊", "翰林医愈", "翰林医证", "翰林医诊")
MEDICAL_WORKERS = ("翰林医候", "翰林医学", "翰林祗候")


def repair_dictionary_source():
    """据原书第80-82页恢复#692、#694并修复跨条吞并。"""
    text692 = "宫廷内宿医官差遣。职掌为后宫宫人看病（《宋会要·职官》36之105）。"
    text693 = "翰林医官院（局）医官任在外州府军监差遣者（《宋会要·职官》36之103）。"
    text694 = (
        "政和六年正月定翰林医效、翰林医痊、翰林医愈、翰林医证、"
        "翰林医诊为医职（《宋会要·职官》36之102）。"
    )
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                f"UPDATE {table} SET text=? WHERE id=683",
                ("医职名。隶翰林医官院",),
            )
            row = conn.execute(f"SELECT fields FROM {table} WHERE id=687").fetchone()
            assert row and row[0]
            f687 = json.loads(row[0])
            f687["简称"] = f687["简称"].replace("祀候医人", "祗候医人", 1)
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=687",
                (json.dumps(f687, ensure_ascii=False),),
            )
            row = conn.execute(f"SELECT fields FROM {table} WHERE id=691").fetchone()
            assert row and row[0]
            f691 = json.loads(row[0])
            if "入内看医" in f691["别名"]:
                f691["别名"] = f691["别名"].split("入内看医", 1)[0].rstrip()
            else:
                assert f691["别名"].endswith("翰林金紫医官。”")
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=691",
                (json.dumps(f691, ensure_ascii=False),),
            )
            conn.execute(
                f"UPDATE {table} SET title=?,text=?,fields=NULL WHERE id=692",
                ("入内看医", text692),
            )
            conn.execute(f"UPDATE {table} SET text=? WHERE id=693", (text693,))
            conn.execute(
                f"UPDATE {table} SET title=?,text=?,fields=NULL WHERE id=694",
                ("医职", text694),
            )


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(681, 697)}


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


def find_entity(w, title, type_="官职"):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def find_tp(w, title, time, type_="官职"):
    eid = find_entity(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time, type_)
    return tid


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；称谓不另建实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def rechain(w, ordered, decision):
    assert len(ordered) == len(set(ordered)), ordered
    for index, tp_id in enumerate(ordered):
        w.relink(
            tp_id, decision,
            prev_id=(ordered[index - 1] if index else None),
            succ_id=(ordered[index + 1] if index + 1 < len(ordered) else None),
        )


def medical_academy_tp(w):
    return find_tp(w, "翰林医官院", "北宋景德元年（1004）八月", "机构")


def medical_bureau_tp(w):
    return find_tp(w, "翰林医官局", "北宋元丰五年（1082）六月十四日", "机构")


def medical_bureau_south_tp(w):
    return find_tp(w, "翰林医官局", "南宋绍兴二年（1132）", "机构")


def normalize_prior_entities():
    """以前批正文暂名规范为本批正式词头，并保留追溯。"""
    mappings = (
        ("翰林医官院直院", "直翰林医官院", 683),
        ("祗候医人", "翰林祗候医人", 687),
    )
    with sqlite3.connect(ENTRY_DB) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for old_title, new_title, i in mappings:
            old = conn.execute(
                "SELECT id FROM Entities WHERE title=? AND type='官职'", (old_title,)
            ).fetchone()
            new = conn.execute(
                "SELECT id FROM Entities WHERE title=? AND type='官职'", (new_title,)
            ).fetchone()
            if old:
                assert not new, (old_title, new_title, old, new)
                conn.execute(
                    "UPDATE Entities SET title=?,quotation=? WHERE id=?",
                    (new_title, F[i]["text"], old[0]),
                )
                conn.execute(
                    "INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)"
                    " VALUES(?,?,?,?,?)",
                    (
                        "Entities", old[0], F[i]["title"], F[i]["page"],
                        f"据#{i}正式词头，将前批暂名“{old_title}”规范为“{new_title}”。",
                    ),
                )
            else:
                assert new, (old_title, new_title)


def entry681():
    i = 681
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, F[i]["title"])
    pre = timepoint(
        w, i, eid, "唐元和中（806—820）", "始置",
        history, "建立唐代始置节点。", "职源与沿革",
        category="医官院长官", officer_type="医官使", chain="none",
    )
    first = find_tp(w, F[i]["title"], "北宋雍熙二年（985）三月")
    cite(w, "Timepoints", first, i, history, "补证雍熙二年已见医官使。", "职源与沿革")
    roster = find_tp(w, F[i]["title"], "北宋前期（仁宗宝元二年制）")
    cite(w, "Timepoints", roster, i, field(i, "职掌"), "补证领医官院医药公事。", "职掌")
    cite(w, "Timepoints", roster, i, field(i, "品位"), "补证七品及居医官之首。", "品位")
    cite(w, "Timepoints", roster, i, field(i, "编制"), "补证编制二人。", "编制")
    changed = timepoint(
        w, i, eid, "北宋政和二年（1112）九月二十五日", "改医职名，易为翰林良医",
        history, "建立改称翰林良医节点。", "职源与沿革", category="医职改名", chain="none",
    )
    rechain(w, [pre, first, roster, changed], "按原文纪年重排翰林医官使时间链。")
    target_e = find_entity(w, "翰林良医")
    target = timepoint(
        w, i, target_e, "北宋政和二年（1112）九月二十五日", "由翰林医官使改称",
        history, "建立翰林良医改称承接节点。", "职源与沿革", category="医职阶官", chain="head",
    )
    relation(w, i, changed, target, "前后演变", history, "翰林医官使改称翰林良医。", "职源与沿革")
    relation(w, i, medical_academy_tp(w), roster, "编制隶属", main, "翰林医官使隶医官院。", staff_type="医官使", staff_quota="二人")
    relation(w, i, medical_bureau_tp(w), target, "编制隶属", history, "改名后的翰林良医隶医官局。", "职源与沿革", staff_type="医职阶官")
    alias_citation(w, i, roster, "简称")
    w.commit()


def entry682():
    i = 682
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, F[i]["title"])
    exact = timepoint(
        w, i, eid, "北宋仁宗宝元二年（1039）二月三日", "始定置，二员",
        history, "建立医官副使始置节点。", "职源与沿革",
        category="医官院副长官", officer_type="医官副使", grade="七品", chain="head",
    )
    cite(w, "Timepoints", exact, i, field(i, "职掌"), "补证副贰医官使、佐领院事。", "职掌")
    cite(w, "Timepoints", exact, i, field(i, "品位"), "补证品位、序位及以尚药奉御充。", "品位")
    cite(w, "Timepoints", exact, i, field(i, "编制"), "补证宝元、元丰二员编制。", "编制")
    generic = find_tp(w, F[i]["title"], "北宋前期（仁宗宝元二年制）")
    changed = timepoint(
        w, i, eid, "北宋政和二年（1112）九月二十五日", "改称翰林医正",
        history, "建立改称翰林医正节点。", "职源与沿革", category="医职改名", chain="none",
    )
    rechain(w, [exact, generic, changed], "按原文纪年重排翰林医官副使时间链。")
    target_e = w.entity("翰林医正", "官职", "正文明确医官副使改称翰林医正。", quotation=history)
    target = timepoint(
        w, i, target_e, "北宋政和二年（1112）九月二十五日", "由翰林医官副使改称",
        history, "建立翰林医正改称承接节点。", "职源与沿革",
        category="医职阶官", grade="从七品",
    )
    relation(w, i, changed, target, "前后演变", history, "翰林医官副使改称翰林医正。", "职源与沿革")
    relation(w, i, medical_academy_tp(w), exact, "编制隶属", main, "翰林医官副使隶医官院。", staff_type="医官副使", staff_quota="二员")
    relation(w, i, medical_bureau_tp(w), target, "编制隶属", history, "改名后的翰林医正隶医官局。", "职源与沿革", staff_type="医职阶官")
    source = find_tp(w, "尚药奉御", "北宋前期（仁宗宝元二年制）")
    relation(w, i, source, exact, "前后演变", field(i, "品位"), "尚药奉御可充医官副使。", "品位")
    relation(w, i, generic, find_tp(w, "翰林医官使", "北宋前期（仁宗宝元二年制）"), "前后演变", field(i, "简称"), "副使遇推恩可改正使。", "简称")
    alias_citation(w, i, exact, "简称")
    w.commit()


def entry683():
    i = 683
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职掌与沿革")
    eid = find_entity(w, F[i]["title"])
    before = timepoint(
        w, i, eid, "北宋仁宗宝元二年（1039）二月以前", "已置，编制七人",
        history, "建立宝元二年前直院节点。", "职掌与沿革",
        category="翰林医官院属员", officer_type="直院", chain="head",
    )
    after = find_tp(w, F[i]["title"], "北宋前期（仁宗宝元二年制）")
    cite(w, "Timepoints", after, i, field(i, "编制"), "补证宝元后定为四人。", "编制")
    cite(w, "Timepoints", after, i, field(i, "职掌"), "补证供奉医药事。", "职掌")
    cite(w, "Timepoints", after, i, field(i, "品位"), "补证位次。", "品位")
    renamed = timepoint(
        w, i, eid, "北宋元丰五年（1082）六月十四日", "改称直翰林医官局",
        history, "建立元丰改称节点。", "职掌与沿革", category="医职改名", chain="tail",
    )
    target_e = w.entity("直翰林医官局", "官职", "正文明确元丰改称直翰林医官局。", quotation=history)
    target = timepoint(
        w, i, target_e, "北宋元丰五年（1082）六月十四日", "由直翰林医官院改称",
        history, "建立直翰林医官局承接节点。", "职掌与沿革", category="翰林医官局属员",
    )
    target_end = timepoint(
        w, i, target_e, "北宋政和三年（1113）", "改称翰林医效",
        history, "建立直医官局改称医效节点。", "职掌与沿革", category="医职改名",
    )
    medical_effect = find_tp(w, "翰林医效", "北宋政和三年（1113）")
    relation(w, i, renamed, target, "前后演变", history, "直翰林医官院改称直翰林医官局。", "职掌与沿革")
    relation(w, i, target_end, medical_effect, "前后演变", history, "直翰林医官局改称翰林医效。", "职掌与沿革")
    relation(w, i, medical_academy_tp(w), before, "编制隶属", main, "直翰林医官院隶医官院。", staff_type="直院", staff_quota="七人")
    relation(w, i, medical_academy_tp(w), after, "编制隶属", field(i, "编制"), "宝元后直院隶医官院，定四人。", "编制", staff_type="直院", staff_quota="四人")
    alias_citation(w, i, after, "简称")
    w.commit()


def entry684():
    i = 684
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, F[i]["title"])
    before = timepoint(
        w, i, eid, "北宋仁宗宝元二年（1039）二月以前", "医官院所属，编制七人",
        field(i, "编制"), "建立宝元二年前尚药奉御节点。", "编制",
        category="翰林医官院属员", officer_type="尚药奉御", chain="head",
    )
    after = find_tp(w, F[i]["title"], "北宋前期（仁宗宝元二年制）")
    cite(w, "Timepoints", after, i, field(i, "职掌"), "补证供奉医药及院外差遣。", "职掌")
    cite(w, "Timepoints", after, i, field(i, "品位"), "补证序位及可充使、副。", "品位")
    changed = timepoint(
        w, i, eid, "北宋政和三年（1113）", "改称翰林医痊",
        history, "建立改称翰林医痊节点。", "职源与沿革", category="医职改名", chain="tail",
    )
    target = find_tp(w, "翰林医痊", "北宋政和三年（1113）")
    relation(w, i, changed, target, "前后演变", history, "尚药奉御改称翰林医痊。", "职源与沿革")
    relation(w, i, medical_academy_tp(w), before, "编制隶属", field(i, "编制"), "宝元前尚药奉御七人。", "编制", staff_type="尚药奉御", staff_quota="七人")
    relation(w, i, medical_academy_tp(w), after, "编制隶属", field(i, "编制"), "宝元后尚药奉御六人。", "编制", staff_type="尚药奉御", staff_quota="六人")

    palace_e = find_entity(w, "尚药局奉御")
    tang = timepoint(
        w, i, palace_e, "唐代", "殿中省尚药局置奉御官",
        history, "补建殿中省尚药局奉御唐代节点。", "职源与沿革",
        category="殿中省尚药局属员", officer_type="奉御", chain="head",
    )
    early_song = timepoint(
        w, i, palace_e, "北宋开宝五年（972）十二月", "殿中省沿置尚药奉御",
        history, "补建殿中省尚药奉御北宋沿置节点。", "职源与沿革",
        category="殿中省尚药局属员", officer_type="奉御", chain="none",
    )
    existing = find_tp(w, "尚药局奉御", "北宋崇宁二年二月")
    rechain(w, [tang, early_song, existing], "按纪年重排尚药局奉御时间链。")
    relation(w, i, find_tp(w, "尚药局", "唐代", "机构"), tang, "编制隶属", history, "唐殿中省尚药局置奉御官。", "职源与沿革", staff_type="奉御")
    relation(w, i, find_tp(w, "尚药局", "宋前期", "机构"), early_song, "编制隶属", history, "北宋殿中省沿置尚药奉御。", "职源与沿革", staff_type="奉御")
    alias_citation(w, i, after, "简称")
    w.commit()


def entry685():
    i = 685
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, F[i]["title"])
    tang = timepoint(
        w, i, eid, "唐贞元八年（792）八月", "始置",
        history, "建立唐代始置节点。", "职源与沿革", category="医官", chain="none",
    )
    song = timepoint(
        w, i, eid, "北宋乾德元年（963）闰十二月", "已见置",
        history, "建立北宋已见置节点。", "职源与沿革", category="翰林医官院属员", chain="none",
    )
    roster = find_tp(w, F[i]["title"], "北宋前期（仁宗宝元二年制）")
    cite(w, "Timepoints", roster, i, field(i, "职掌"), "补证供奉医药及外任差遣。", "职掌")
    cite(w, "Timepoints", roster, i, field(i, "编制"), "补证改制前三十人。", "编制")
    reform = find_tp(w, F[i]["title"], "北宋政和三年（1113）")
    cite(w, "Timepoints", reform, i, history, "补证政和后旧翰林医官由医候代替、其名转为医正通称。", "职源与沿革")
    cite(w, "Timepoints", reform, i, field(i, "品位"), "补证政和后从七品。", "品位")
    cite(w, "Timepoints", reform, i, field(i, "编制"), "补证与正郎混同三十员。", "编制")
    south = find_tp(w, F[i]["title"], "南宋绍兴二年（1132）")
    rechain(w, [tang, song, roster, reform, south], "按纪年重排翰林医官时间链。")
    target = find_tp(w, "翰林医候", "北宋政和三年（1113）")
    relation(w, i, roster, target, "前后演变", history, "旧翰林医官由翰林医候代替。", "职源与沿革")
    relation(w, i, medical_academy_tp(w), roster, "编制隶属", main, "翰林医官隶医官院。", staff_type="医官")
    relation(w, i, medical_academy_tp(w), roster, "编制隶属", field(i, "编制"), "改制前翰林医官三十人。", "编制", staff_type="医官", staff_quota="三十人")
    alias_citation(w, i, roster, "简称")
    w.commit()


def entry686():
    i = 686
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, F[i]["title"])
    first = timepoint(
        w, i, eid, "北宋太平兴国六年（981）十二月", "已见置",
        history, "建立翰林医学已见置节点。", "职源与沿革",
        category="翰林医官院属员", officer_type="医学", chain="head",
    )
    roster = find_tp(w, F[i]["title"], "北宋前期（仁宗宝元二年制）")
    cite(w, "Timepoints", roster, i, field(i, "职掌"), "补证供奉医学及外任差遣。", "职掌")
    cite(w, "Timepoints", roster, i, field(i, "编制"), "补证改制前四十人。", "编制")
    reform = find_tp(w, F[i]["title"], "北宋政和三年（1113）")
    cite(w, "Timepoints", reform, i, history, "补证政和后名不变、称医工、不列医职。", "职源与沿革")
    cite(w, "Timepoints", reform, i, field(i, "品位"), "补证政和后从九品及序位。", "品位")
    relation(w, i, medical_academy_tp(w), roster, "编制隶属", main, "翰林医学隶医官院。", staff_type="医学")
    relation(w, i, medical_academy_tp(w), roster, "编制隶属", field(i, "编制"), "改制前翰林医学四十人。", "编制", staff_type="医学", staff_quota="四十人")
    alias_citation(w, i, roster, "简称")
    w.commit()


def entry687():
    i = 687
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, F[i]["title"])
    before = timepoint(
        w, i, eid, "北宋仁宗宝元二年（1039）二月以前", "已置，诸医职最末一等",
        history, "建立宝元二年前祗候医人节点。", "职源与沿革",
        category="翰林医官院属员", officer_type="祗候医人", chain="head",
    )
    roster = find_tp(w, F[i]["title"], "北宋前期（仁宗宝元二年制）")
    cite(w, "Timepoints", roster, i, field(i, "职掌"), "补证供奉医药及外任差遣。", "职掌")
    cite(w, "Timepoints", roster, i, field(i, "编制"), "补证十三人编制。", "编制")
    changed = timepoint(
        w, i, eid, "北宋政和三年（1113）", "改称翰林祗候，称医工，不列医职",
        history, "建立改称翰林祗候节点。", "职源与沿革", category="医职改名", chain="tail",
    )
    target = find_tp(w, "翰林祗候", "北宋政和三年（1113）")
    relation(w, i, changed, target, "前后演变", history, "翰林祗候医人改称翰林祗候。", "职源与沿革")
    relation(w, i, medical_academy_tp(w), before, "编制隶属", main, "翰林祗候医人隶医官院。", staff_type="祗候医人")
    relation(w, i, medical_academy_tp(w), roster, "编制隶属", field(i, "编制"), "北宋前期祗候医人十三人。", "编制", staff_type="祗候医人", staff_quota="十三人")
    alias_citation(w, i, roster, "简称")
    w.commit()


def entry688():
    i = 688
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正文定义宫内宿值侍医群体。", quotation=main)
    group = timepoint(
        w, i, eid, "宋代（具体时间未载）", "经选择、保荐、考试，在宫内宿值；分医师、御医及各科",
        main, "建立内宿医官统称节点。", category="宫廷内宿医官统称",
    )
    for title in ("医师", "御医"):
        instance = find_tp(w, title, "宋代（翰林医官局差遣）")
        relation(w, i, group, instance, "统称与实例", main, f"{title}为内宿医官实例。")
    physician = find_tp(w, "御医", "宋代（翰林医官局差遣）")
    for title, specialty, _ in MEDICAL_SPECIALTIES:
        post_e = w.entity(title, "官职", f"正文明确御医分设{specialty}科医官。", quotation=main)
        post = timepoint(
            w, i, post_e, "宋代（内宿医官分科）", f"御医所属{specialty}科医官",
            main, f"建立{title}节点。", category="内宿御医分科", officer_type=specialty,
        )
        relation(w, i, physician, post, "统称与实例", main, f"御医分设{specialty}科。")
    w.commit()


def entry689():
    i = 689
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, F[i]["title"])
    post = timepoint(
        w, i, eid, "北宋元丰法时期（1078—1085）", "选保试补，听御笔差填，为入内内宿医官差遣",
        history, "建立元丰法内宿医师差遣节点。", "职源与沿革",
        category="宫廷内宿医官差遣", officer_type="医师", chain="none",
    )
    cite(w, "Timepoints", post, i, field(i, "职掌"), "补证宫内宿直及御前医药职掌。", "职掌")
    cite(w, "Timepoints", post, i, field(i, "品位"), "补证官品随医阶、序位在御医之上。", "品位")
    cite(w, "Timepoints", post, i, field(i, "泛称"), "补证医师亦可作从医人员泛称；不另建实体。", "泛称", note="泛称说明不另建实体")
    zhou = find_tp(w, F[i]["title"], "周代")
    chongning = find_tp(w, F[i]["title"], "北宋崇宁二年二月十二日")
    generic = find_tp(w, F[i]["title"], "宋代（翰林医官局差遣）")
    rechain(w, [zhou, post, chongning, generic], "按纪年重排医师时间链。")
    relation(w, i, medical_academy_tp(w), post, "编制隶属", main, "医师为医官院内宿差遣。", staff_type="内宿医官差遣")
    w.commit()


def entry690():
    i = 690
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, F[i]["title"])
    generic = find_tp(w, F[i]["title"], "宋代（翰林医官局差遣）")
    cite(w, "Timepoints", generic, i, history, "补证北宋设置、南宋沿置及其差遣性质。", "职源与沿革")
    cite(w, "Timepoints", generic, i, field(i, "职掌"), "补证宫内值宿、分科祗应医药。", "职掌")
    cite(w, "Timepoints", generic, i, field(i, "品位"), "补证官品随医阶及序位。", "品位")
    sx12 = timepoint(
        w, i, eid, "南宋绍兴十二年（1142）四月", "编制十人",
        field(i, "编制"), "建立绍兴十二年御医员额节点。", "编制",
        category="宫廷内宿医官差遣", officer_type="御医", chain="tail",
    )
    sx30 = timepoint(
        w, i, eid, "南宋绍兴三十年（1160）", "增置二十八人并分八科",
        field(i, "编制"), "建立绍兴三十年御医增额节点。", "编制",
        category="宫廷内宿医官差遣", officer_type="御医", chain="tail",
    )
    relation(w, i, medical_bureau_south_tp(w), sx12, "编制隶属", field(i, "编制"), "绍兴十二年御医十人。", "编制", staff_type="御医", staff_quota="十人")
    relation(w, i, medical_bureau_south_tp(w), sx30, "编制隶属", field(i, "编制"), "绍兴三十年御医二十八人。", "编制", staff_type="御医", staff_quota="二十八人")
    for title, specialty, quota in MEDICAL_SPECIALTIES:
        post_e = find_entity(w, title)
        post = timepoint(
            w, i, post_e, "南宋绍兴三十年（1160）", f"御医所属{specialty}科",
            field(i, "编制"), f"建立{title}绍兴三十年节点。", "编制",
            category="内宿御医分科", officer_type=specialty,
        )
        relation(w, i, sx30, post, "统称与实例", field(i, "编制"), f"御医分设{specialty}科。", "编制", staff_type=specialty, staff_quota=quota)
    w.commit()


def entry691():
    i = 691
    w = W(i)
    main = F[i]["text"]
    origin = field(i, "职源")
    eid = w.entity(F[i]["title"], "官职", "正式词头定义宫廷内宿诊脉差遣。", quotation=main)
    north = timepoint(
        w, i, eid, "北宋仁宗嘉祐元年（1056）三月", "始见置，祗应御前诊脉诊治",
        origin, "建立诊御脉北宋始见节点。", "职源",
        category="宫廷内宿医官差遣", officer_type="诊御脉", chain="head",
    )
    cite(w, "Timepoints", north, i, field(i, "职掌"), "补证诊候御脉、诊病开方及宫中诊治。", "职掌")
    cite(w, "Timepoints", north, i, field(i, "品位"), "补证官品随所带医阶。", "品位")
    sx12 = timepoint(
        w, i, eid, "南宋绍兴十二年（1142）四月", "编制十人",
        field(i, "编制"), "建立绍兴十二年诊御脉员额节点。", "编制",
        category="宫廷内宿医官差遣", officer_type="诊御脉",
    )
    sx30 = timepoint(
        w, i, eid, "南宋绍兴三十年（1160）", "编制四人",
        field(i, "编制"), "建立绍兴三十年诊御脉员额节点。", "编制",
        category="宫廷内宿医官差遣", officer_type="诊御脉",
    )
    relation(w, i, medical_academy_tp(w), north, "编制隶属", main, "诊御脉为医官院内宿差遣。", staff_type="诊御脉")
    relation(w, i, medical_bureau_south_tp(w), sx12, "编制隶属", field(i, "编制"), "绍兴十二年诊御脉十人。", "编制", staff_type="诊御脉", staff_quota="十人")
    relation(w, i, medical_bureau_south_tp(w), sx30, "编制隶属", field(i, "编制"), "绍兴三十年诊御脉四人。", "编制", staff_type="诊御脉", staff_quota="四人")
    alias_citation(w, i, north, "别名")
    w.commit()


def entry692():
    i = 692
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正式词头定义后宫看医差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）", "宫廷内宿医官差遣，为后宫宫人看病",
        main, "建立入内看医节点。", category="宫廷内宿医官差遣", officer_type="入内看医",
    )
    w.commit()


def entry688_relations():
    """#688在#691、#692实体恢复后补建御医科目实例关系。"""
    i = 688
    w = W(i)
    main = F[i]["text"]
    physician = find_tp(w, "御医", "宋代（翰林医官局差遣）")
    relation(
        w, i, physician, find_tp(w, "诊御脉", "北宋仁宗嘉祐元年（1056）三月"),
        "统称与实例", main, "诊御脉为御医内宿科目实例。",
    )
    relation(
        w, i, physician, find_tp(w, "入内看医", "宋代（具体时间未载）"),
        "统称与实例", main, "入内看医为御医内宿科目实例。",
    )
    w.commit()


def entry693():
    i = 693
    w = W(i)
    main = F[i]["text"]
    tp = find_tp(w, F[i]["title"], "宋代（翰林医官局差遣）")
    cite(w, "Timepoints", tp, i, main, "补证驻泊医官为外州府军监差遣。")
    relation(w, i, medical_bureau_tp(w), tp, "编制隶属", main, "驻泊医官为医官局在外差遣。", staff_type="驻泊医官")
    w.commit()


def entry694():
    i = 694
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正文明确五种医阶合称医职。", quotation=main)
    group = timepoint(
        w, i, eid, "北宋政和六年（1116）正月", "定翰林医效、医痊、医愈、医证、医诊为医职",
        main, "建立医职统称节点。", category="医官局医阶统称",
    )
    for title in MEDICAL_OFFICES:
        post_e = find_entity(w, title)
        post = timepoint(
            w, i, post_e, "北宋政和六年（1116）正月", "定为医职",
            main, f"建立{title}定为医职节点。", category="医职",
        )
        relation(w, i, group, post, "统称与实例", main, f"{title}为医职实例。")
        if title in ("翰林医效", "翰林医痊"):
            rechain(
                w,
                [
                    find_tp(w, title, "北宋政和三年（1113）"),
                    find_tp(w, title, "北宋政和三年（1113）定额"),
                    post,
                    find_tp(w, title, "南宋绍兴二年（1132）"),
                ],
                f"将{title}政和六年分类节点插入1113与1132之间。",
            )
    w.commit()


def entry695():
    i = 695
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正文明确医工的历代设置及宋代构成。", quotation=main)
    han = timepoint(w, i, eid, "汉代", "置医工长", main, "建立汉代医工来源节点。", category="医工")
    tang = timepoint(w, i, eid, "唐代", "太医署置医工", main, "建立唐代医工节点。", category="医工")
    song = timepoint(w, i, eid, "北宋时期（具体时间未载）", "诸州置医工", main, "建立北宋诸州医工节点。", category="地方医工")
    reform = timepoint(
        w, i, eid, "北宋政和六年（1116）正月", "定翰林医候、翰林医学、翰林祗候为医工",
        main, "建立政和医工统称节点。", category="医官局医阶统称",
    )
    assert han and tang and song
    for title in MEDICAL_WORKERS:
        post_e = find_entity(w, title)
        post = timepoint(
            w, i, post_e, "北宋政和六年（1116）正月", "定为医工",
            main, f"建立{title}定为医工节点。", category="医工",
        )
        relation(w, i, reform, post, "统称与实例", main, f"{title}为医工实例。")
    w.commit()


def entry696():
    i = 696
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正文明确太医为宋代医官、医职、医工的统称。", quotation=main)
    group = timepoint(
        w, i, eid, "宋代", "翰林医官院医官、医职、医工的泛称",
        main, "建立太医统称节点。", category="宫廷医疗官统称",
    )
    instances = (
        find_tp(w, "翰林医官", "北宋前期（仁宗宝元二年制）"),
        find_tp(w, "医职", "北宋政和六年（1116）正月"),
        find_tp(w, "医工", "北宋政和六年（1116）正月"),
    )
    for title, target in zip(("翰林医官", "医职", "医工"), instances):
        relation(w, i, group, target, "统称与实例", main, f"{title}为太医所指实例。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(681, 697)] == [
        "翰林医官使", "翰林医官副使", "直翰林医官院", "尚药奉御",
        "翰林医官", "翰林医学", "翰林祗候医人", "内宿医官",
        "医师", "御医", "诊御脉", "入内看医", "驻泊医官", "医职", "医工", "太医",
    ]
    assert "入内看医" not in field(691, "别名")
    assert F[692]["text"].startswith("宫廷内宿医官差遣")
    assert F[693]["text"].endswith("36之103）。")
    assert F[694]["text"].startswith("政和六年正月定翰林医效")
    normalize_prior_entities()
    entry681(); entry682(); entry683(); entry684(); entry685(); entry686(); entry687(); entry688()
    entry689(); entry690(); entry691(); entry692(); entry688_relations(); entry693()
    entry694(); entry695(); entry696()


if __name__ == "__main__":
    main()
