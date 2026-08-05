#!/usr/bin/env python3
"""提取第一编第461-480条：入内内侍班六等、政和改名与祗候班。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
MERGED_DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1t7.db")
ENTRY_DB = os.environ.get("SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"))


def repair_dictionary_source():
    """据原书第56-59页修复空格误识别及#469-471、#479-480错并。"""
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            fixes = {
                461: (("隶入 内内侍省", "隶入内内侍省"),),
                462: (("隶人 内内侍省", "隶入内内侍省"),),
                463: (("隶入 内内侍省", "隶入内内侍省"),),
            }
            for entry_id, replacements in fixes.items():
                row = conn.execute(f"SELECT text FROM {table} WHERE id=?", (entry_id,)).fetchone()
                assert row and row[0]
                text = row[0]
                for old, new in replacements:
                    text = text.replace(old, new)
                conn.execute(f"UPDATE {table} SET text=? WHERE id=?", (text, entry_id))

            row464 = conn.execute(f"SELECT text,fields FROM {table} WHERE id=464").fetchone()
            assert row464 and row464[1]
            f464 = json.loads(row464[1])
            f464["职掌"] = f464["职掌"].replace("参“入内内侍省·职掌”）。", "参“入内内侍省·职掌”。")
            conn.execute(
                f"UPDATE {table} SET text=?,fields=? WHERE id=464",
                ("宦官名。隶入内内侍省内侍班。", json.dumps(f464, ensure_ascii=False)),
            )

            row469 = conn.execute(f"SELECT text,fields FROM {table} WHERE id=469").fetchone()
            row470 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=470").fetchone()
            row471 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=471").fetchone()
            assert row469 and row469[0] and row469[1] and row470 and row471
            fixed469 = row469[0].replace("入 内内侍省", "入内内侍省").replace("内 侍高品", "内侍高品").replace("《宋会 要", "《宋会要")
            if not row470[1]:
                f469 = json.loads(row469[1])
                alias469, merged = f469["简称"].split("入内内侍省右班殿直 宦官名。", 1)
                merged470, tail471 = merged.split("入内内侍省祗候班 入内内侍省诸内品总名，即祗候使臣总名。", 1)
                assert not tail471
                text470, alias470 = merged470.split("右班殿直。", 1)
                f470 = {"简称": "右班殿直。" + alias470}
                f471 = {k: v for k, v in f469.items() if k != "简称"}
                f469 = {"简称": alias469}
                conn.execute(f"UPDATE {table} SET text=?,fields=? WHERE id=469", (fixed469, json.dumps(f469, ensure_ascii=False)))
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=470",
                    ("入内内侍省右班殿直", "宦官名。" + text470, json.dumps(f470, ensure_ascii=False)),
                )
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=471",
                    ("入内内侍省祗候班", "入内内侍省诸内品总名，即祗候使臣总名。", json.dumps(f471, ensure_ascii=False)),
                )
            else:
                assert row470[0] == "入内内侍省右班殿直" and row471[0] == "入内内侍省祗候班"
                conn.execute(f"UPDATE {table} SET text=? WHERE id=469", (fixed469,))

            row479 = conn.execute(f"SELECT text FROM {table} WHERE id=479").fetchone()
            row480 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=480").fetchone()
            assert row479 and row479[0] and row480
            if not row480[1]:
                text479, text480 = row479[0].split("入内贴祗候内品 宦官名。", 1)
                conn.execute(f"UPDATE {table} SET text=? WHERE id=479", (text479,))
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=NULL WHERE id=480",
                    ("入内贴祗候内品", "宦官名。" + text480),
                )
            else:
                assert row480[0] == "入内贴祗候内品" and row480[1].startswith("宦官名。") and row480[2] is None


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute("SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)).fetchone()
    assert row, i
    return {"title": row[0], "page": row[1], "text": row[2] or "", "fields": json.loads(row[3] or "{}")}


F = {i: load(i) for i in range(461, 481)}


def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def field(i, name):
    value = F[i]["fields"][name]; assert value; return value


def C(i, name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{name}字段）" if name else "")


def cite(w, table, target_id, i, quotation, decision, name=None, **kwargs):
    source = field(i, name) if name else F[i]["text"]
    assert quotation in source, (i, name, quotation)
    return w.citation(table, target_id, C(i, name), quotation, decision, **kwargs)


def timepoint(w, i, entity_id, time, event, quotation, decision, name=None,
              category=None, officer_type=None, grade=None, chain="tail", **cite_kwargs):
    tid = w.timepoint(entity_id, time, event, decision, quotation, attr_category=category,
                      attr_officer_type=officer_type, attr_grade=grade, chain=chain)
    cite(w, "Timepoints", tid, i, quotation, decision, name, **cite_kwargs)
    return tid


def relation(w, i, subject, object_, kind, quotation, decision, name=None,
             staff_type=None, staff_quota=None, **cite_kwargs):
    rid = w.relationship(subject, object_, kind, decision, quotation,
                         staff_type=staff_type, staff_quota=staff_quota)
    cite(w, "Relationships", rid, i, quotation, decision, name, **cite_kwargs)
    return rid


def find_entity(w, title, type_=None):
    eid = w.find_entity(title, type_); assert eid, (title, type_); return eid


def find_tp(w, title, time, type_=None):
    eid = find_entity(w, title, type_); tid = w.find_timepoint(eid, time); assert tid, (title, time, type_); return tid


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(w, "Timepoints", tp_id, i, quotation, f"补证{F[i]['title']}的{name}；不为称谓另建实体。", name,
         note=f"{name}仅作称谓证据，不另建实体")


def parent_relation(w, i, office_tp, quotation, staff_type="内侍班", name=None):
    relation(w, i, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), office_tp,
             "编制隶属", quotation, f"{F[i]['title']}隶入内内侍省。", name, staff_type=staff_type)


ALT_NOTE = "本专条所记前身与#441-448所记改名链不同，作为并行史料证据保留。"


def enrich_inner_rank(i, title, grade_value, predecessor_titles, conflict=True):
    main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); staffing = field(i, "编制"); w = W(i)
    eid = find_entity(w, title, "官职")
    begin = find_tp(w, title, "北宋大中祥符二年（1009）二月", "官职")
    cite(w, "Timepoints", begin, i, main, f"补证{title}隶入内内侍省内侍班。")
    cite(w, "Timepoints", begin, i, history, f"补证{title}改名来源及元丰后沿置。", "职源与沿革")
    cite(w, "Timepoints", begin, i, duty, f"补证{title}轮值、传旨、外差与通进职掌。", "职掌")
    cite(w, "Timepoints", begin, i, grade, f"补证{title}{grade_value}及班序。", "品位")
    cite(w, "Timepoints", begin, i, staffing, f"补证{title}无定员。", "编制")
    for pred in predecessor_titles:
        pe = w.entity(pred, "官职", "职源字段明载该旧官改为本官。", quotation=history)
        pt = timepoint(w, i, pe, "北宋大中祥符二年（1009）二月三日", f"改为{title}", history,
                       f"建立{pred}改名节点。", "职源与沿革", category="改名",
                       note=ALT_NOTE if conflict else None, conflict_flag=1 if conflict else 0)
        relation(w, i, pt, begin, "前后演变", history, f"大中祥符二年{pred}改为{title}。", "职源与沿革",
                 note=ALT_NOTE if conflict else None, conflict_flag=1 if conflict else 0)
    parent_relation(w, i, begin, main)
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry461(): enrich_inner_rank(461, "入内内侍省内侍殿头", "正九品", ("入内内侍省殿头高品",), True)
def entry462(): enrich_inner_rank(462, "入内内侍省内侍高品", "正九品", ("入内内侍省高品",), True)
def entry463(): enrich_inner_rank(463, "入内内侍省内侍高班", "从九品", ("入内内侍省殿头高品", "入内内侍省殿头高班"), True)
def entry464(): enrich_inner_rank(464, "入内内侍省内侍黄门", "从九品", ("入内内侍省黄门",), False)


def entry465():
    i = 465; main = F[i]["text"]; w = W(i)
    generic = w.entity("小黄门", "官职", "正文追溯东汉小黄门之始。", quotation=main)
    timepoint(w, i, generic, "东汉永平年间（58—75）", "始置小黄门", main, "建立小黄门历史源流节点。", category="宦官")
    eid = w.entity("入内内侍省小黄门", "官职", "正文定义其为隶入内省的初补小黄门。", quotation=main)
    tp = timepoint(w, i, eid, "宋代（具体时间未载）", "内侍初补，等外无品；遇恩可迁内侍黄门", main,
                   "建立入内内侍省小黄门节点。", category="初补宦官", grade="等外无品")
    parent_relation(w, i, tp, main, "初补宦官")
    alias_citation(w, i, tp, "简称")
    w.commit()


def rename_cycle(i, old_title, new_title, alias_field="简称"):
    main = F[i]["text"]; w = W(i)
    old_e = find_entity(w, old_title, "官职")
    old_end = timepoint(w, i, old_e, "北宋政和二年（1112）九月二十五日", f"改名{new_title}", main,
                        f"建立{old_title}政和改名节点。", category="改名")
    new_e = w.entity(new_title, "官职", "正文定义该官为政和二年改定的新官名。", quotation=main)
    new_begin = timepoint(w, i, new_e, "北宋政和二年（1112）九月二十五日", f"由{old_title}改名", main,
                          f"建立{new_title}始置节点。", category="政和新官名")
    new_end = timepoint(w, i, new_e, "北宋靖康元年（1126）", f"复旧称{old_title}", main,
                        f"建立{new_title}复旧终结节点。", category="改名")
    old_return = timepoint(w, i, old_e, "北宋靖康元年（1126）", f"恢复{old_title}旧称", main,
                           f"建立{old_title}靖康复称节点。", category="内侍班")
    relation(w, i, old_end, new_begin, "前后演变", main, f"政和二年{old_title}改名{new_title}。")
    relation(w, i, new_end, old_return, "前后演变", main, f"靖康元年{new_title}复称{old_title}。")
    parent_relation(w, i, new_begin, main)
    alias_citation(w, i, new_begin, alias_field)
    w.commit()


def entry466(): rename_cycle(466, "入内内侍省内东头供奉官", "入内内侍省供奉官")
def entry467(): rename_cycle(467, "入内内侍省内西头供奉官", "入内内侍省左侍禁")
def entry468(): rename_cycle(468, "入内内侍省内侍殿头", "入内内侍省右侍禁")
def entry469(): rename_cycle(469, "入内内侍省内侍高品", "入内内侍省左班殿直")
def entry470(): rename_cycle(470, "入内内侍省内侍高班", "入内内侍省右班殿直")


def entry471():
    i = 471; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); staffing = field(i, "编制"); w = W(i)
    eid = w.entity("入内内侍省祗候班", "官职", "正文定义祗候班为入内内侍省诸内品、祗候使臣总名。", quotation=main)
    start = timepoint(w, i, eid, "北宋大中祥符二年（1009）", "改定祗候官九等，始置祗候班", history,
                      "建立祗候班始置节点。", "职源与沿革", category="祗候使臣总称")
    xining = timepoint(w, i, eid, "北宋熙宁年间（1068—1077）", "祗候班增为十一等", history,
                       "建立熙宁十一等节点。", "职源与沿革", category="祗候使臣总称")
    yuanfeng = timepoint(w, i, eid, "北宋元丰新制", "减为九等，从九品，位次内侍班", history,
                         "建立元丰九等节点。", "职源与沿革", category="祗候使臣总称", grade="从九品")
    zhenghe = timepoint(w, i, eid, "北宋政和二年（1112）", "改内侍官名，祗候班仅存五等", history,
                        "建立政和五等节点。", "职源与沿革", category="祗候使臣总称")
    jingkang = timepoint(w, i, eid, "北宋靖康元年（1126）", "依元丰法恢复旧名", history,
                         "建立靖康复旧节点。", "职源与沿革", category="祗候使臣总称")
    south = timepoint(w, i, eid, "南宋时期（具体时间未载）", "沿置", history,
                      "建立南宋沿置节点。", "职源与沿革", category="祗候使臣总称")
    cite(w, "Timepoints", yuanfeng, i, duty, "补证祗候班职掌同黄门以上并轮宿给役。", "职掌")
    cite(w, "Timepoints", yuanfeng, i, grade, "补证祗候班从九品及班序。", "品位")
    cite(w, "Timepoints", yuanfeng, i, staffing, "补证祗候班无定员。", "编制")
    relation(w, i, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), start,
             "编制隶属", history, "祗候班隶入内内侍省。", "职源与沿革", staff_type="祗候班")
    alias_citation(w, i, yuanfeng, "简称与别名")
    w.commit()


def waiting_officer(i, title, time, event, grade_note=None, alias=None):
    main = F[i]["text"]; w = W(i)
    eid = w.entity(title, "官职", "正文定义该官为入内内侍省祗候班宦官。", quotation=main)
    tp = timepoint(w, i, eid, time, event, main, f"建立{title}节点。", category="入内祗候班", grade=grade_note)
    parent_relation(w, i, tp, main, "祗候班")
    if alias: alias_citation(w, i, tp, alias)
    w.commit(); return tp


def waiting_rename(i, old_title, new_title, alias=None):
    main = F[i]["text"]; w = W(i)
    old_e = find_entity(w, old_title, "官职")
    old_end = timepoint(w, i, old_e, "北宋政和二年（1112）九月二十五日", f"改名{new_title}", main,
                        f"建立{old_title}政和改名节点。", category="改名")
    new_e = w.entity(new_title, "官职", "正文定义其为政和二年祗候班新官名。", quotation=main)
    begin = timepoint(w, i, new_e, "北宋政和二年（1112）九月二十五日", f"由{old_title}改名", main,
                      f"建立{new_title}始置节点。", category="祗候班政和新名", grade="从九品")
    end = timepoint(w, i, new_e, "北宋靖康元年（1126）", f"复旧称{old_title}", main,
                    f"建立{new_title}复旧节点。", category="改名")
    old_return = timepoint(w, i, old_e, "北宋靖康元年（1126）", f"恢复{old_title}旧称", main,
                           f"建立{old_title}靖康复称节点。", category="入内祗候班", grade="从九品")
    relation(w, i, old_end, begin, "前后演变", main, f"政和二年{old_title}改名{new_title}。")
    relation(w, i, end, old_return, "前后演变", main, f"靖康元年{new_title}复称{old_title}。")
    group = find_tp(w, "入内内侍省祗候班", "北宋政和二年（1112）", "官职")
    relation(w, i, group, begin, "统称与实例", main, f"{new_title}为政和二年祗候班新官名。")
    parent_relation(w, i, begin, main, "祗候班")
    if alias: alias_citation(w, i, begin, alias)
    w.commit()


def entry472(): waiting_officer(472, "入内祗候殿头", "北宋大中祥符二年以后、熙宁七年（1074）以前", "置于祗候班，地位最高，其下为祗候高品", "从九品")
def entry473(): waiting_rename(473, "入内祗候殿头", "入内祗候侍禁")
def entry474(): waiting_officer(474, "入内祗候高品", "北宋大中祥符二年以后、熙宁七年（1074）以前", "置于祗候班，次于祗候殿头、高于祗候高班内品", "从九品", "简称")
def entry475(): waiting_rename(475, "入内祗候高品", "入内祗候殿直")
def entry476(): waiting_officer(476, "入内祗候高班内品", "北宋大中祥符二年（1009）", "定置，次于祗候高品、高于祗候内品", "从九品")
def entry477(): waiting_rename(477, "入内祗候高班内品", "入内祗候黄门内品", "简称")
def entry478(): waiting_officer(478, "入内祗候内品", "北宋大中祥符二年（1009）", "定置，次于祗候高班内品、高于祗候小内品", "从九品")
def entry479(): waiting_officer(479, "入内祗候小内品", "北宋大中祥符二年（1009）", "定置；原条记次于祗候高班内品、高于贴祗候内品", "从九品")
def entry480(): waiting_officer(480, "入内贴祗候内品", "北宋仁宗嘉祐六年（1061）", "已见置，次于祗候小内品、高于入内内品", "从九品")


def link_waiting_instances():
    i = 471; history = field(i, "职源与沿革"); aliases = field(i, "简称与别名"); w = W(i)
    group = find_tp(w, "入内内侍省祗候班", "北宋元丰新制", "官职")
    current = (
        ("入内祗候殿头", "北宋大中祥符二年以后、熙宁七年（1074）以前"),
        ("入内祗候高品", "北宋大中祥符二年以后、熙宁七年（1074）以前"),
        ("入内祗候高班内品", "北宋大中祥符二年（1009）"),
        ("入内祗候内品", "北宋大中祥符二年（1009）"),
        ("入内祗候小内品", "北宋大中祥符二年（1009）"),
        ("入内贴祗候内品", "北宋仁宗嘉祐六年（1061）"),
    )
    for title, when in current:
        relation(w, i, group, find_tp(w, title, when, "官职"), "统称与实例", aliases,
                 f"祗候班为总称，{title}为正文明列实例。", "简称与别名")
    for title in ("入内北班内品", "入内后苑散内品", "入内后苑勾当事内品", "入内后苑内品", "入内把门内品", "入内内品"):
        eid = w.entity(title, "官职", "简称与别名字段明列为祗候班实例。", quotation=aliases)
        tp = timepoint(w, i, eid, "北宋元丰新制", "列为入内内侍省祗候班内品", aliases,
                       f"建立{title}祗候班节点。", "简称与别名", category="入内祗候班", grade="从九品")
        relation(w, i, group, tp, "统称与实例", aliases, f"祗候班为总称，{title}为正文明列实例。", "简称与别名")
        parent_relation(w, i, tp, aliases, "祗候班", "简称与别名")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(461, 481)] == [
        "入内内侍省内侍殿头", "入内内侍省内侍高品", "入内内侍省内侍高班", "入内内侍省内侍黄门",
        "入内内侍省小黄门", "入内内侍省供奉官", "入内内侍省左侍禁", "入内内侍省右侍禁",
        "入内内侍省左班殿直", "入内内侍省右班殿直", "入内内侍省祗候班", "入内祗候殿头",
        "入内祗候侍禁", "入内祗候高品", "入内祗候殿直", "入内祗候高班内品",
        "入内祗候黄门内品", "入内祗候内品", "入内祗候小内品", "入内贴祗候内品",
    ]
    assert F[470]["text"].startswith("宦官名。") and "简称" in F[470]["fields"]
    assert F[471]["text"].startswith("入内内侍省诸内品总名") and "职源与沿革" in F[471]["fields"]
    assert F[480]["text"].startswith("宦官名。") and not F[480]["fields"]
    entry461(); entry462(); entry463(); entry464(); entry465()
    entry466(); entry467(); entry468(); entry469(); entry470(); entry471()
    entry472(); entry473(); entry474(); entry475(); entry476(); entry477(); entry478(); entry479(); entry480()
    link_waiting_instances()


if __name__ == "__main__": main()
