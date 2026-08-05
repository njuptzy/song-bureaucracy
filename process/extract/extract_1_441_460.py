#!/usr/bin/env python3
"""提取第一编第441-460条：入内内侍省早期官阶、领省官与内侍班。"""

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
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)


def repair_dictionary_source():
    """据原书第53-56页修复#450-453错并、正式词头及确定OCR字误。"""
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            # #443只是#442“简称”字段中的称谓，并非正文独立词头。
            row443 = conn.execute(f"SELECT text,fields FROM {table} WHERE id=443").fetchone()
            assert row443
            if not row443[0]:
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=443",
                    (json.dumps({"__status__": "alias_only", "_canonical": "入内殿头高品"}, ensure_ascii=False),),
                )

            row450 = conn.execute(f"SELECT text,fields FROM {table} WHERE id=450").fetchone()
            row451 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=451").fetchone()
            assert row450 and row450[0] and row450[1] and row451
            text450 = row450[0].replace("有人内都知司", "有入内都知司")
            if not row451[1]:
                f450 = json.loads(row450[1])
                alias450, tail451 = f450["简称"].split("入内内侍省都知 宜官名。", 1)
                assert not tail451
                f451 = {
                    "职源与沿革": f450.pop("职源与沿革"),
                    "职掌": f450.pop("职掌"),
                    "品位": f450.pop("品位"),
                    "编制": f450.pop("编制"),
                    "简称与别名": f450.pop("简称与别名"),
                }
                f450["简称"] = alias450
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=? WHERE id=450",
                    (text450, json.dumps(f450, ensure_ascii=False)),
                )
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=451",
                    ("入内内侍省都知", "宦官名。", json.dumps(f451, ensure_ascii=False)),
                )
            else:
                assert row451[0] == "入内内侍省都知" and row451[1] == "宦官名。" and row451[2]
                conn.execute(f"UPDATE {table} SET text=? WHERE id=450", (text450,))

            row453 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=453").fetchone()
            assert row453 and row453[1] and row453[2]
            f453 = json.loads(row453[2])
            f453.pop("_catalog_name", None)
            f453.pop("__status__", None)
            text453 = row453[1]
            if text453.startswith("副都知 "):
                text453 = text453.removeprefix("副都知 ")
            assert text453 == "宦官名。"
            conn.execute(
                f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=453",
                ("入内内侍省副都知", text453, json.dumps(f453, ensure_ascii=False)),
            )

            row458 = conn.execute(f"SELECT text FROM {table} WHERE id=458").fetchone()
            assert row458 and row458[0]
            fixed458 = row458[0].replace("人内省内侍官总名", "入内省内侍官总名")
            if not fixed458.endswith("。"):
                fixed458 += "。"
            conn.execute(f"UPDATE {table} SET text=? WHERE id=458", (fixed458,))

            for entry_id in (459, 460):
                row = conn.execute(f"SELECT text,fields FROM {table} WHERE id=?", (entry_id,)).fetchone()
                assert row and row[0] and row[1]
                text = row[0]
                if not text.endswith("。"):
                    text += "。"
                fields = json.loads(row[1])
                if entry_id == 459:
                    fields["职源与沿革"] = fields["职源与沿革"].replace("置有人内供奉官", "置有入内供奉官")
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=? WHERE id=?",
                    (text, json.dumps(fields, ensure_ascii=False), entry_id),
                )


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute("SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)).fetchone()
    assert row, i
    return {"title": row[0], "page": row[1], "text": row[2] or "", "fields": json.loads(row[3] or "{}")}


F = {i: load(i) for i in range(441, 461)}


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


def timepoint(w, i, entity_id, time, event, quotation, decision, name=None,
              category=None, officer_type=None, grade=None, chain="tail", **cite_kwargs):
    target_id = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer_type, attr_grade=grade, chain=chain,
    )
    cite(w, "Timepoints", target_id, i, quotation, decision, name, **cite_kwargs)
    return target_id


def relation(w, i, subject, object_, kind, quotation, decision, name=None,
             staff_type=None, staff_quota=None, **cite_kwargs):
    target_id = w.relationship(
        subject, object_, kind, decision, quotation,
        staff_type=staff_type, staff_quota=staff_quota,
    )
    cite(w, "Relationships", target_id, i, quotation, decision, name, **cite_kwargs)
    return target_id


def find_entity(w, title, type_=None):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    return entity_id


def find_tp(w, title, time, type_=None):
    entity_id = find_entity(w, title, type_)
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time, type_)
    return target_id


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；不为称谓另建实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def normalize_derived_timepoint(title, old_time, new_time, event, source_i, decision):
    """原位规范上一批由总条预建的时间点，保留ID、链、关系与引用。"""
    with sqlite3.connect(ENTRY_DB) as conn:
        row = conn.execute(
            "SELECT t.id,t.time,t.event FROM Timepoints t JOIN Entities e ON e.id=t.entity_id "
            "WHERE e.title=? AND e.type='官职' AND t.time IN (?,?) ORDER BY t.id LIMIT 1",
            (title, old_time, new_time),
        ).fetchone()
        assert row, (title, old_time, new_time)
        if row[1] == new_time and row[2] == event:
            return row[0]
        conn.execute("UPDATE Timepoints SET time=?,event=? WHERE id=?", (new_time, event, row[0]))
        conn.execute(
            "INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision) VALUES(?,?,?,?,?)",
            ("Timepoints", row[0], F[source_i]["title"], F[source_i]["page"], decision),
        )
        return row[0]


def normalize_prior_leader_nodes():
    # 总条只说“建立以后”，专条明确景德三年二月始置。
    for title, source_i in (
        ("入内内侍省都都知", 449),
        ("入内内侍省都知", 451),
        ("入内内侍省副都知", 453),
        ("入内内侍省押班", 455),
    ):
        normalize_derived_timepoint(
            title, "北宋景德三年（1006）以后", "北宋景德三年（1006）二月",
            "入内内侍省始置时设置", source_i,
            "专条明确景德三年二月始置，将总条预建的“建立以后”节点原位规范到确切月份。",
        )

    # #422总条记五月四日，#451-456专条记五月八日，合并为有证据的两说节点。
    combined = "北宋崇宁二年（1103）五月四日或八日（两说）"
    for title, source_i, event in (
        ("入内内侍省都知", 451, "改名知入内内侍省事；总条记五月四日，专条记五月八日"),
        ("知入内内侍省事", 452, "由入内内侍省都知改名；总条记五月四日，专条记五月八日"),
        ("入内内侍省副都知", 453, "改名同知入内内侍省事；总条记五月四日，专条记五月八日"),
        ("同知入内内侍省事", 454, "由入内内侍省副都知改名；总条记五月四日，专条记五月八日"),
        ("入内内侍省押班", 455, "改名签书入内内侍省事；总条记五月四日，专条记五月八日"),
        ("签书入内内侍省事", 456, "由入内内侍省押班改名；总条记五月四日，专条记五月八日"),
    ):
        normalize_derived_timepoint(
            title, "北宋崇宁二年五月四日", combined, event, source_i,
            "总条与专条分别记崇宁二年五月四日、八日，保留为两说而不擅断。",
        )


def affiliation_relations(w, i, office_tp, quotation, include_predecessors=True):
    """为明载“景德三年前先后隶……景德三年后隶省”的官职补全隶属。"""
    if include_predecessors:
        for title, when in (
            ("内中高品班院", "宋开国之初"),
            ("入内内班院", "北宋淳化五年（994）初"),
            ("入内黄门班院", "北宋淳化五年（994）稍后"),
            ("内侍省入内内侍班院", "北宋淳化五年"),
        ):
            relation(
                w, i, find_tp(w, title, when, "机构"), office_tp, "编制隶属", quotation,
                f"原文明载{F[i]['title']}在景德三年前先后隶属{title}。",
                staff_type="内侍官",
                note="“入内高品班院”等时期称谓复用正式机构词头内中高品班院",
            )
    relation(
        w, i, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"),
        office_tp, "编制隶属", quotation,
        f"景德三年后{F[i]['title']}隶入内内侍省。", staff_type="内侍官",
    )


def entry441():
    i = 441; main = F[i]["text"]; w = W(i)
    eid = w.entity("入内殿头高班", "官职", "正文定义其为入内高品班院三等宦官之首。", quotation=main)
    begin = timepoint(w, i, eid, "北宋太平兴国四年（979）", "重定为三等宦官中最高一等", main, "建立入内殿头高班节点。", category="入内宦官等级")
    post = timepoint(w, i, eid, "北宋景德三年（1006）以后", "改隶入内内侍省", main, "建立景德三年后隶属节点。", category="入内宦官等级")
    end = timepoint(w, i, eid, "北宋大中祥符二年（1009）二月", "改为内侍殿头", main, "建立入内殿头高班改名节点。", category="改名")
    affiliation_relations(w, i, post, main)
    ne = w.entity("入内内侍省内侍殿头", "官职", "正文明载入内殿头高班改为内侍殿头。", quotation=main)
    nt = timepoint(w, i, ne, "北宋大中祥符二年（1009）二月", "由入内殿头高班改名", main, "建立内侍殿头始置节点。", category="入内内侍班", grade="正九品")
    relation(w, i, end, nt, "前后演变", main, "大中祥符二年入内殿头高班改为内侍殿头。")
    w.commit()


def entry442():
    i = 442; main = F[i]["text"]; w = W(i)
    eid = w.entity("入内殿头高品", "官职", "正文定义其为入内高品班院三等宦官之一。", quotation=main)
    begin = timepoint(w, i, eid, "北宋太平兴国四年（979）", "重定为三等宦官第二等", main, "建立入内殿头高品节点。", category="入内宦官等级")
    post = timepoint(w, i, eid, "北宋景德三年（1006）以后", "改隶入内内侍省", main, "建立景德三年后隶属节点。", category="入内宦官等级")
    end = timepoint(w, i, eid, "北宋大中祥符二年（1009）二月", "改为内侍高品", main, "建立入内殿头高品改名节点。", category="改名")
    affiliation_relations(w, i, post, main)
    ne = w.entity("入内内侍省内侍高品", "官职", "正文明载入内殿头高品改为内侍高品。", quotation=main)
    nt = timepoint(w, i, ne, "北宋大中祥符二年（1009）二月", "由入内殿头高品改名", main, "建立内侍高品始置节点。", category="入内内侍班", grade="正九品")
    relation(w, i, end, nt, "前后演变", main, "大中祥符二年入内殿头高品改为内侍高品。")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry444():
    i = 444; main = F[i]["text"]; w = W(i)
    eid = w.entity("入内殿头小底", "官职", "正文定义其为入内高品班院三等宦官最低一等。", quotation=main)
    begin = timepoint(w, i, eid, "北宋太平兴国四年（979）", "设置，为三等宦官最低一等", main, "建立入内殿头小底节点。", category="入内宦官等级")
    post = timepoint(w, i, eid, "北宋景德三年（1006）以后", "改隶入内内侍省", main, "建立景德三年后隶属节点。", category="入内宦官等级")
    timepoint(w, i, eid, "北宋大中祥符二年（1009）二月", "罢除", main, "建立入内殿头小底罢除节点。", category="罢除")
    affiliation_relations(w, i, post, main)
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry445():
    i = 445; main = F[i]["text"]; w = W(i)
    eid = w.entity("内中黄门小底", "官职", "正文定义其为宋初内中高品班院初补宦官。", quotation=main)
    tp = timepoint(w, i, eid, "北宋太祖朝（960—976）", "设置为初补宦官，在后宫给使", main, "建立内中黄门小底节点。", category="初补宦官")
    relation(w, i, find_tp(w, "内中高品班院", "宋开国之初", "机构"), tp, "编制隶属", main, "内中黄门小底隶内中高品班院。", staff_type="初补宦官")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry446():
    i = 446; main = F[i]["text"]; w = W(i)
    eid = w.entity("入内西头供奉官", "官职", "正文定义其为大中祥符二年前高等内臣。", quotation=main)
    tp = timepoint(w, i, eid, "宋初（大中祥符二年以前）", "隶内中高品班院等，为仅次于押班的高等内臣", main, "建立入内西头供奉官节点。", category="高等内臣")
    relation(w, i, find_tp(w, "内中高品班院", "宋开国之初", "机构"), tp, "编制隶属", main, "入内西头供奉官隶内中高品班院等。", staff_type="高等内臣")
    w.commit()


def entry447():
    i = 447; main = F[i]["text"]; w = W(i)
    eid = w.entity("入内供奉官", "官职", "正文定义其为雍熙三年增置的入内宦官。", quotation=main)
    begin = timepoint(w, i, eid, "北宋雍熙三年（986）", "于入内高品班院增置，高于入内殿头高班", main, "建立入内供奉官始置节点。", category="高等内臣")
    post = timepoint(w, i, eid, "北宋景德三年（1006）以后", "改隶入内内侍省", main, "建立景德三年后隶属节点。", category="高等内臣")
    end = timepoint(w, i, eid, "北宋大中祥符二年（1009）二月", "分改内东头供奉官、内西头供奉官", main, "建立入内供奉官分改节点。", category="改名分设")
    affiliation_relations(w, i, post, main)
    for title in ("入内内侍省内东头供奉官", "入内内侍省内西头供奉官"):
        ne = w.entity(title, "官职", "正文明载入内供奉官分改为东、西头供奉官。", quotation=main)
        nt = timepoint(w, i, ne, "北宋大中祥符二年（1009）二月三日", "由入内供奉官分改", main, f"建立{title}始置节点。", category="入内内侍班", grade="从八品")
        relation(w, i, end, nt, "前后演变", main, f"大中祥符二年入内供奉官分改为{title}。")
    w.commit()


def entry448():
    i = 448; main = F[i]["text"]; w = W(i)
    eid = w.entity("入内高班内品", "官职", "正文定义其为雍熙三年增置的宦官。", quotation=main)
    begin = timepoint(w, i, eid, "北宋雍熙三年（986）", "于入内高品班院增置", main, "建立入内高班内品节点。", category="入内宦官等级")
    post = timepoint(w, i, eid, "北宋景德三年（1006）以后", "改隶入内内侍省", main, "建立景德三年后隶属节点。", category="入内宦官等级")
    end = timepoint(w, i, eid, "北宋大中祥符二年（1009）正月", "改为入内内侍省黄门高品", main, "建立入内高班内品改名节点。", category="改名")
    affiliation_relations(w, i, post, main)
    middle_e = w.entity("入内内侍省黄门高品", "官职", "正文明载正月改为入内内侍省黄门高品。", quotation=main)
    middle = timepoint(w, i, middle_e, "北宋大中祥符二年（1009）正月", "由入内高班内品改名", main, "建立黄门高品节点。", category="入内宦官等级")
    middle_end = timepoint(w, i, middle_e, "北宋大中祥符二年（1009）二月", "又改为内侍高班", main, "建立黄门高品再改节点。", category="改名")
    high_e = w.entity("入内内侍省内侍高班", "官职", "正文明载二月又改为内侍高班。", quotation=main)
    high = timepoint(w, i, high_e, "北宋大中祥符二年（1009）二月", "由入内内侍省黄门高品改名", main, "建立内侍高班始置节点。", category="入内内侍班", grade="从九品")
    relation(w, i, end, middle, "前后演变", main, "大中祥符二年正月入内高班内品改为黄门高品。")
    relation(w, i, middle_end, high, "前后演变", main, "大中祥符二年二月黄门高品又改为内侍高班。")
    w.commit()


def entry449():
    i = 449; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); staffing = field(i, "编制"); w = W(i)
    eid = find_entity(w, "入内内侍省都都知", "官职")
    begin = find_tp(w, "入内内侍省都都知", "北宋景德三年（1006）二月", "官职")
    cite(w, "Timepoints", begin, i, history, "补证都都知景德三年二月始置。", "职源与沿革")
    cite(w, "Timepoints", begin, i, duty, "补证都都知总领入内内侍省。", "职掌")
    reform = timepoint(w, i, eid, "北宋元丰改制", "仍设但不常除人；一员，从五品，为内臣极品", history, "建立元丰改制节点。", "职源与沿革", category="入内内侍省最高长官", officer_type="总领", grade="从五品")
    cite(w, "Timepoints", reform, i, grade, "补证都都知从五品及任职资格。", "品位")
    relation(w, i, find_tp(w, "入内内侍省", "北宋元丰七年八月", "机构"), reform, "编制隶属", staffing, "元丰改制仍设都都知一员。", "编制", staff_type="总领", staff_quota=1)
    alias_citation(w, i, begin, "简称与别名")
    w.commit()


def entry450():
    i = 450; main = F[i]["text"]; w = W(i)
    eid = w.entity("入内内侍省都知司", "机构", "正文定义其为入内内侍省都知治所。", quotation=main)
    tp = timepoint(w, i, eid, "北宋景德三年（1006）", "由入内都知司、内东门都知司合并，为入内内侍省都知治所", main, "建立入内内侍省都知司节点。", category="领省官治所")
    relation(w, i, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), tp, "上下级机构", main, "入内内侍省都知司为入内内侍省都知治所。")
    for title, when in (("入内都知司", "北宋景德三年（1006）二月"), ("东门都知司", "北宋景德三年（1006）二月")):
        relation(w, i, find_tp(w, title, when, "机构"), tp, "前后演变", main, f"景德三年{title}并入入内内侍省都知司。", note="原文此处称“内东门都知司”，复用正式词头“东门都知司”")
    alias_citation(w, i, tp, "简称")
    w.commit()


CONFLICT_NOTE = "#422总条记崇宁二年五月四日，#451-456专条记五月八日；保留两说。"
COMBINED_TIME = "北宋崇宁二年（1103）五月四日或八日（两说）"


def leader_entry(i, title, renamed, begin_quote_name, duty_name, grade_name, staffing_name, alias_name, quota, grade_value, role):
    main = F[i]["text"]; history = field(i, begin_quote_name); duty = field(i, duty_name); grade = field(i, grade_name); staffing = field(i, staffing_name); w = W(i)
    eid = find_entity(w, title, "官职")
    begin = find_tp(w, title, "北宋景德三年（1006）二月", "官职")
    cite(w, "Timepoints", begin, i, history, f"补证{title}景德三年始置。", begin_quote_name)
    cite(w, "Timepoints", begin, i, duty, f"补证{title}职掌。", duty_name)
    cite(w, "Timepoints", begin, i, grade, f"补证{title}品位。", grade_name)
    old_end = find_tp(w, title, COMBINED_TIME, "官职")
    cite(w, "Timepoints", old_end, i, history, f"补证专条所记五月八日改名{renamed}。", begin_quote_name, note=CONFLICT_NOTE, conflict_flag=1)
    new_begin = find_tp(w, renamed, COMBINED_TIME, "官职")
    relation(w, i, old_end, new_begin, "前后演变", history, f"崇宁二年{title}改名{renamed}。", begin_quote_name, note=CONFLICT_NOTE, conflict_flag=1)
    relation(w, i, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), begin, "编制隶属", staffing, f"{title}为入内内侍省{role}。", staffing_name, staff_type=role, staff_quota=quota)
    alias_citation(w, i, begin, alias_name)
    w.commit()


def entry451():
    leader_entry(451, "入内内侍省都知", "知入内内侍省事", "职源与沿革", "职掌", "品位", "编制", "简称与别名", 4, "正六品；元祐从五品；南宋正六品", "总辖省务")


def renamed_entry(i, title, old_title):
    main = F[i]["text"]; w = W(i)
    begin = find_tp(w, title, COMBINED_TIME, "官职")
    cite(w, "Timepoints", begin, i, main, f"补证专条所记五月八日由{old_title}改名。", note=CONFLICT_NOTE, conflict_flag=1)
    end = find_tp(w, title, "北宋靖康元年（1126）", "官职")
    cite(w, "Timepoints", end, i, main, "补证靖康元年复旧名。")
    w.commit()


def entry452(): renamed_entry(452, "知入内内侍省事", "入内内侍省都知")


def entry453():
    leader_entry(453, "入内内侍省副都知", "同知入内内侍省事", "职源与沿革", "职掌", "品位", "编制", "简称", 1, "正六品", "副贰")


def entry454(): renamed_entry(454, "同知入内内侍省事", "入内内侍省副都知")


def entry455():
    leader_entry(455, "入内内侍省押班", "签书入内内侍省事", "职源与沿革", "职掌", "品位", "编制", "简称与别名", 2, "正六品", "都知辅佐")


def entry456(): renamed_entry(456, "签书入内内侍省事", "入内内侍省押班")


def entry457():
    i = 457; main = F[i]["text"]; history = field(i, "职源与沿革"); function = field(i, "职能"); grade = field(i, "品位"); w = W(i)
    eid = w.entity("内常侍", "官职", "正文定义内常侍为宦官加官。", quotation=main)
    timepoint(w, i, eid, "隋代（具体时间未载）", "内常侍之名始置", history, "建立内常侍隋代源流节点。", "职源与沿革", category="宦官加官")
    timepoint(w, i, eid, "宋初", "内班院设置，次于内侍，作为宦官加官", history, "建立宋初内常侍节点。", "职源与沿革", category="宦官加官")
    yuanfeng = timepoint(w, i, eid, "北宋元丰八年（1085）", "入内内侍省始置，作为内臣迁转等级", history, "建立元丰八年节点。", "职源与沿革", category="入内内侍省迁转等级")
    cite(w, "Timepoints", yuanfeng, i, function, "补证内常侍为内臣迁转等级。", "职能")
    south = timepoint(w, i, eid, "南宋时期（具体时间未载）", "仍置，列入杂压，正八品", history, "建立南宋节点。", "职源与沿革", category="宦官加官", grade="正八品")
    cite(w, "Timepoints", south, i, grade, "补证南宋内常侍正八品及班序。", "品位")
    relation(w, i, find_tp(w, "入内内侍省", "北宋元丰七年八月", "机构"), yuanfeng, "编制隶属", history, "元丰八年入内内侍省始置内常侍。", "职源与沿革", staff_type="迁转等级")
    w.commit()


def entry458():
    i = 458; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); staffing = field(i, "编制"); w = W(i)
    eid = w.entity("入内内侍省内侍班", "官职", "正文定义内侍班为入内省内侍官总名。", quotation=main)
    timepoint(w, i, eid, "北宋咸平年间（998—1003）", "已置内侍班", history, "建立内侍班早期节点。", "职源与沿革", category="入内内侍官总称")
    group = timepoint(w, i, eid, "北宋大中祥符二年（1009）二月", "改定为六等内侍官，总名内侍班，无定员", history, "建立六等内侍班节点。", "职源与沿革", category="入内内侍官总称")
    cite(w, "Timepoints", group, i, duty, "补证内侍班轮值、外差及通进等职掌。", "职掌")
    cite(w, "Timepoints", group, i, grade, "补证六等官品与班序。", "品位")
    cite(w, "Timepoints", group, i, staffing, "补证内侍班无定员。", "编制")
    relation(w, i, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), group, "编制隶属", history, "内侍班为入内内侍省内侍官总称。", "职源与沿革", staff_type="内侍班")
    for title in (
        "入内内侍省内东头供奉官", "入内内侍省内西头供奉官", "入内内侍省内侍殿头",
        "入内内侍省内侍高品", "入内内侍省内侍高班", "入内内侍省内侍黄门",
    ):
        te = w.entity(title, "官职", "职源字段明列为内侍班六等之一。", quotation=history)
        tt = w.find_timepoint(te, "北宋大中祥符二年（1009）二月")
        if tt is None:
            tt = timepoint(w, i, te, "北宋大中祥符二年（1009）二月", "列为入内内侍省内侍班六等之一", history, f"建立{title}六等内侍节点。", "职源与沿革", category="入内内侍班")
        relation(w, i, group, tt, "统称与实例", history, f"内侍班为总名，{title}为六等实例。", "职源与沿革")
    alias_citation(w, i, group, "简称")
    w.commit()


def entry459():
    i = 459; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); staffing = field(i, "编制"); w = W(i)
    eid = find_entity(w, "入内内侍省内东头供奉官", "官职")
    begin = find_tp(w, "入内内侍省内东头供奉官", "北宋大中祥符二年（1009）二月三日", "官职")
    cite(w, "Timepoints", begin, i, main, "补证内东头供奉官隶入内内侍省内侍班。")
    cite(w, "Timepoints", begin, i, history, "补证内东头供奉官由入内供奉官改名及南宋沿置。", "职源与沿革")
    cite(w, "Timepoints", begin, i, duty, "补证轮值、传旨、外差及通进职掌。", "职掌")
    cite(w, "Timepoints", begin, i, grade, "补证从八品及班序。", "品位")
    cite(w, "Timepoints", begin, i, staffing, "补证无定员。", "编制")
    relation(w, i, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), begin, "编制隶属", main, "内东头供奉官隶入内内侍省内侍班。", staff_type="内侍班")
    alias_citation(w, i, begin, "简称与别名")
    w.commit()


def entry460():
    i = 460; main = F[i]["text"]; history = field(i, "职源与沿革"); shared = field(i, "职掌、官品、编制"); w = W(i)
    eid = find_entity(w, "入内内侍省内西头供奉官", "官职")
    old = find_entity(w, "入内西头供奉官", "官职")
    old985 = timepoint(w, i, old, "北宋雍熙二年（985）", "见置，隶入内高品班院", history, "建立入内西头供奉官确切见置节点。", "职源与沿革", category="高等内臣")
    old_end = timepoint(w, i, old, "北宋大中祥符二年（1009）二月三日", "冠以入内内侍省号，改为入内内侍省内西头供奉官", history, "建立入内西头供奉官改名节点。", "职源与沿革", category="改名")
    begin = find_tp(w, "入内内侍省内西头供奉官", "北宋大中祥符二年（1009）二月三日", "官职")
    cite(w, "Timepoints", begin, i, main, "补证内西头供奉官隶入内内侍省内侍班。")
    cite(w, "Timepoints", begin, i, history, "补证大中祥符二年冠以入内内侍省号。", "职源与沿革")
    cite(w, "Timepoints", begin, i, shared, "补证职掌、官品、编制同内东头供奉官而位次较低。", "职掌、官品、编制")
    relation(w, i, old_end, begin, "前后演变", history, "大中祥符二年入内西头供奉官冠以入内内侍省号。", "职源与沿革")
    relation(w, i, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), begin, "编制隶属", main, "内西头供奉官隶入内内侍省内侍班。", staff_type="内侍班")
    alias_citation(w, i, begin, "简称")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(441, 461)] == [
        "入内殿头高班", "入内殿头高品", "入内殿头", "入内殿头小底", "内中黄门小底",
        "入内西头供奉官", "入内供奉官", "入内高班内品", "入内内侍省都都知",
        "入内内侍省都知司", "入内内侍省都知", "知入内内侍省事", "入内内侍省副都知",
        "同知入内内侍省事", "入内内侍省押班", "签书入内内侍省事", "内常侍",
        "入内内侍省内侍班", "入内内侍省内东头供奉官", "入内内侍省内西头供奉官",
    ]
    assert F[443]["fields"].get("__status__") == "alias_only" and not F[443]["text"]
    assert F[451]["text"] == "宦官名。" and "职源与沿革" in F[451]["fields"]
    assert F[453]["text"] == "宦官名。" and F[453]["title"] == "入内内侍省副都知"

    normalize_prior_leader_nodes()
    entry441(); entry442(); entry444(); entry445(); entry446(); entry447(); entry448()
    entry449(); entry450(); entry451(); entry452(); entry453(); entry454(); entry455(); entry456()
    entry457(); entry458(); entry459(); entry460()


if __name__ == "__main__":
    main()
