#!/usr/bin/env python3
"""提取第一编第481-500条：祗候内品、寄班、云韶部与内侍省沿革。"""

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
    """据原书第59-62页修复#482、#490、#492-493及#499-500 OCR。"""
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(f"SELECT text FROM {table} WHERE id=482").fetchone()
            assert row and row[0]
            conn.execute(f"UPDATE {table} SET text=? WHERE id=482", (row[0].replace("宜官名。", "宦官名。"),))

            row = conn.execute(f"SELECT fields FROM {table} WHERE id=490").fetchone()
            assert row and row[0]
            fields = json.loads(row[0])
            replacements = {
                "职源与沿革": (("改为内侍省《隋书", "改为内侍省（《隋书"), ("36之4)", "36之4）")),
                "编制": (("（即内品)", "（即内品）"),),
                "品位": (("位次于人内内侍省", "位次于入内内侍省"),),
                "简称与别名": (("王守忠为人内内侍省", "王守忠为入内内侍省"),),
            }
            for name, fixes in replacements.items():
                for old, new in fixes:
                    fields[name] = fields[name].replace(old, new)
            conn.execute(f"UPDATE {table} SET fields=? WHERE id=490", (json.dumps(fields, ensure_ascii=False),))

            row492 = conn.execute(f"SELECT text FROM {table} WHERE id=492").fetchone()
            row493 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=493").fetchone()
            assert row492 and row492[0] and row493
            marker = "内侍 宦官加官名。隶内侍省。"
            if marker in row492[0]:
                text492, text493 = row492[0].split(marker, 1)
                conn.execute(f"UPDATE {table} SET text=? WHERE id=492", (text492,))
                conn.execute(
                    f"UPDATE {table} SET title='内侍',text=?,fields=NULL WHERE id=493",
                    ("宦官加官名。隶内侍省。" + text493,),
                )
            else:
                assert row493[0] == "内侍" and row493[1].startswith("宦官加官名。隶内侍省。") and row493[2] is None

            row = conn.execute(f"SELECT text FROM {table} WHERE id=499").fetchone()
            assert row and row[0]
            text = row[0].replace("隋始置官闱局", "隋始置宫闱局").replace("36之1)", "36之1）")
            conn.execute(f"UPDATE {table} SET text=? WHERE id=499", (text,))

            row = conn.execute(f"SELECT text FROM {table} WHERE id=500").fetchone()
            assert row and row[0]
            text = row[0].replace("卷12)", "卷12）").replace("加官(", "加官（").replace("36之1)", "36之1）")
            conn.execute(f"UPDATE {table} SET text=? WHERE id=500", (text,))


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute("SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)).fetchone()
    assert row, i
    return {"title": row[0], "page": row[1], "text": row[2] or "", "fields": json.loads(row[3] or "{}")}


F = {i: load(i) for i in range(481, 501)}


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
    eid = find_entity(w, title, type_); tid = w.find_timepoint(eid, time); assert tid, (title, time); return tid


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(w, "Timepoints", tp_id, i, quotation, f"补证{F[i]['title']}的{name}；称谓不另建实体。", name,
         note=f"{name}仅作称谓证据，不另建实体")


def insert_before(w, i, entity_id, before_time, time, event, quotation, decision, name=None,
                  category=None, officer_type=None, grade=None, **cite_kwargs):
    """把确定较早的节点插到既有节点之前；幂等复跑不重复改链。"""
    existing = w.find_timepoint(entity_id, time)
    if existing:
        cite(w, "Timepoints", existing, i, quotation, decision, name, **cite_kwargs)
        return existing
    before = w.find_timepoint(entity_id, before_time); assert before, (entity_id, before_time)
    prev = w.conn.execute("SELECT prev_id FROM Timepoints WHERE id=?", (before,)).fetchone()[0]
    tid = timepoint(w, i, entity_id, time, event, quotation, decision, name, category, officer_type, grade, "none", **cite_kwargs)
    w.relink(tid, decision=f"将{time}插到{before_time}之前", prev_id=prev, succ_id=before)
    if prev is not None:
        w.relink(prev, decision=f"后继改接{time}", succ_id=tid)
    w.relink(before, decision=f"前驱改接{time}", prev_id=tid)
    return tid


def inner_parent_tp(w): return find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构")
def inner_group_tp(w): return find_tp(w, "入内内侍省祗候班", "北宋元丰新制", "官职")


def waiting_instance(i, time, event, alias=None):
    main = F[i]["text"]; w = W(i); title = F[i]["title"]
    eid = find_entity(w, title, "官职")
    early = insert_before(w, i, eid, "北宋元丰新制", time, event, main,
                          f"补建{title}早期确定节点。", category="入内祗候班", grade="从九品")
    yuanfeng = find_tp(w, title, "北宋元丰新制", "官职")
    cite(w, "Timepoints", yuanfeng, i, main, f"以本专条补证{title}元丰班序、品级及隶属。")
    relation(w, i, inner_parent_tp(w), early, "编制隶属", main, f"{title}隶入内内侍省。", staff_type="祗候班")
    relation(w, i, inner_group_tp(w), early, "统称与实例", main, f"{title}是入内内侍省祗候班实例。")
    if alias: alias_citation(w, i, early, alias)
    w.commit()


def entry481(): waiting_instance(481, "北宋大中祥符二年（1009）", "定置，位次入内贴祗候内品之下、把门内品之上")
def entry482(): waiting_instance(482, "北宋大中祥符二年（1009）", "定置，位次入内内品之下、后苑内品之上", "别名")
def entry483(): waiting_instance(483, "北宋大中祥符二年（1009）", "定置，位次把门内品之下、后苑散内品之上")
def entry484(): waiting_instance(484, "北宋大中祥符二年（1009）", "定置，位次后苑内品之下、北班内品之上")


def entry485():
    i = 485; main = F[i]["text"]; w = W(i); title = F[i]["title"]
    eid = find_entity(w, title, "官职")
    begin = insert_before(w, i, eid, "北宋元丰新制", "北宋大中祥符二年（1009）七月",
                          "由洒扫院子改名，列祗候班最低一级", main, "补建北班内品改名始置节点。",
                          category="入内祗候班", grade="从九品")
    old_e = w.entity("洒扫院子", "官职", "正文明载旧名洒扫院子。", quotation=main)
    old = timepoint(w, i, old_e, "北宋大中祥符二年（1009）七月", "改名入内北班内品", main,
                    "建立洒扫院子改名节点。", category="改名")
    relation(w, i, old, begin, "前后演变", main, "大中祥符二年七月洒扫院子改名入内北班内品。")
    relation(w, i, inner_parent_tp(w), begin, "编制隶属", main, "入内北班内品隶入内内侍省。", staff_type="祗候班")
    relation(w, i, inner_group_tp(w), begin, "统称与实例", main, "入内北班内品是祗候班最低一级。")
    w.commit()


def entry486():
    i = 486; main = F[i]["text"]; w = W(i); title = F[i]["title"]
    eid = find_entity(w, title, "官职")
    begin = insert_before(w, i, eid, "北宋元丰新制", "北宋大中祥符二年之后、英宗治平以前",
                          "置入内后苑勾当事内品", main, "补建该官始置时段。", category="入内祗候班")
    end = insert_before(w, i, eid, "北宋元丰新制", "北宋神宗朝以后", "祗候班已无此官", main,
                        "保留专条所载神宗朝以后废罢节点。", category="废罢",
                        note="与#471元丰编制字段仍列此官相冲突，双方证据并存", conflict_flag=1)
    yuanfeng = find_tp(w, title, "北宋元丰新制", "官职")
    cite(w, "Timepoints", yuanfeng, i, main, "标记专条废罢说与元丰列官说的证据冲突。",
         note="与#471元丰编制字段仍列此官相冲突，双方证据并存", conflict_flag=1)
    relation(w, i, inner_parent_tp(w), begin, "编制隶属", main, "该官隶入内内侍省。", staff_type="祗候班")
    relation(w, i, inner_group_tp(w), begin, "统称与实例", main, "该官是祗候班实例。")
    w.commit()


def entry487():
    i = 487; main = F[i]["text"]; w = W(i)
    group_e = w.entity("入内内侍省寄班", "官职", "正文定义七种寄班使臣的总名。", quotation=main)
    group = timepoint(w, i, group_e, "宋代（具体时间未载）", "统称寄班祗候等七种寄班使臣", main,
                      "建立入内内侍省寄班总称节点。", category="寄班使臣总称")
    relation(w, i, inner_parent_tp(w), group, "编制隶属", main, "入内内侍省寄班隶入内内侍省。", staff_type="寄班")
    for title in ("寄班祗候", "寄班供奉", "寄班侍禁", "寄班殿直", "寄班奉职", "寄班借职", "寄班小底"):
        eid = w.entity(title, "官职", "正文逐项列为入内内侍省寄班实例。", quotation=main)
        tp = timepoint(w, i, eid, "宋代（具体时间未载）", "列入入内内侍省寄班", main,
                       f"建立{title}寄班实例节点。", category="寄班使臣")
        relation(w, i, group, tp, "统称与实例", main, f"入内内侍省寄班为总称，{title}为实例。")
        relation(w, i, inner_parent_tp(w), tp, "编制隶属", main, f"{title}隶入内内侍省。", staff_type="寄班")
    for name in ("职源、职掌、编制", "序位", "简称"):
        alias_citation(w, i, group, name)
    w.commit()


def entry488():
    i = 488; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); staffing = field(i, "编制"); w = W(i)
    old_e = w.entity("箫韶部", "机构", "职源字段明载开宝四年赐名箫韶部。", quotation=history)
    old = timepoint(w, i, old_e, "北宋开宝四年（971）", "以南汉所俘宦者习乐，赐名箫韶部", history,
                    "建立箫韶部始置节点。", "职源与沿革", category="宫廷乐司")
    eid = w.entity("云韶部", "机构", "正文定义其为隶入内内侍省的乐司。", quotation=main)
    begin = timepoint(w, i, eid, "北宋雍熙初年（984—987）", "箫韶部改名云韶部", history,
                      "建立云韶部改名始置节点。", "职源与沿革", category="宫廷乐司")
    end = timepoint(w, i, eid, "南宋时期（具体时间未载）", "不置", history,
                    "建立云韶部南宋不置节点。", "职源与沿革", category="废罢")
    cite(w, "Timepoints", begin, i, duty, "补证云韶部宫廷节令献乐职掌。", "职掌")
    cite(w, "Timepoints", begin, i, staffing, "补证云韶部内品及执色乐人编制。", "编制")
    relation(w, i, old, begin, "前后演变", history, "雍熙初箫韶部改名云韶部。", "职源与沿革")
    relation(w, i, inner_parent_tp(w), begin, "上下级机构", main, "云韶部隶入内内侍省。")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry489():
    i = 489; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); staffing = field(i, "编制"); w = W(i)
    tang_e = w.entity("云韶府", "机构", "职源字段追溯武则天改内教坊为云韶府。", quotation=history)
    timepoint(w, i, tang_e, "唐武周时期（具体时间未载）", "内教坊改名云韶府", history,
              "建立云韶府历史源流节点。", "职源与沿革", category="内教坊")
    eid = w.entity("云韶部内品", "官职", "正文定义其为隶云韶部的黄门伶官。", quotation=main)
    begin = timepoint(w, i, eid, "北宋雍熙初年（984—987）", "置云韶部内品，三十人", history,
                      "建立云韶部内品始置节点。", "职源与沿革", category="黄门伶官")
    cite(w, "Timepoints", begin, i, duty, "补证云韶部内品掌本部乐。", "职掌")
    cite(w, "Timepoints", begin, i, staffing, "补证云韶部内品三十人。", "编制")
    end = timepoint(w, i, eid, "北宋元丰改制", "罢云韶部内品", history,
                    "建立元丰罢官节点。", "职源与沿革", category="废罢")
    relation(w, i, find_tp(w, "云韶部", "北宋雍熙初年（984—987）", "机构"), begin,
             "编制隶属", main, "云韶部内品隶云韶部。", staff_type="黄门伶官", staff_quota="三十人")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry490():
    i = 490; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); staffing = field(i, "编制"); grade = field(i, "品位"); w = W(i)
    eid = find_entity(w, "内侍省", "机构")
    sui = find_tp(w, "内侍省", "隋", "机构")
    cite(w, "Timepoints", sui, i, history, "补证隋避讳改中侍中省为内侍省。", "职源与沿革")
    song = find_tp(w, "内侍省", "北宋初", "机构")
    cite(w, "Timepoints", song, i, history, "补证宋初内侍省沿五代称内班院。", "职源与沿革")
    cite(w, "Timepoints", song, i, duty, "补证内侍省轮宿、拱侍、洒扫、奉使等职掌。", "职掌")
    cite(w, "Timepoints", song, i, grade, "补证内侍省序位及正六品至从九品范围。", "品位")
    zhong_e = w.entity("中侍中省", "机构", "职源字段明载北齐始置中侍中省。", quotation=history)
    zhong = timepoint(w, i, zhong_e, "北齐时期（具体时间未载）", "始置中侍中省", history,
                      "建立内侍省前身节点。", "职源与沿革", category="宦官署")
    relation(w, i, zhong, sui, "前后演变", history, "隋避中字讳，中侍中省改为内侍省。", "职源与沿革")

    inner_e = w.entity("内班院", "机构", "职源字段明载宋初称内班院。", quotation=history)
    inner = timepoint(w, i, inner_e, "北宋初", "沿五代之称设置内班院", history,
                      "建立宋初内班院节点。", "职源与沿革", category="宦官署")
    yellow_e = w.entity("黄门院", "机构", "职源字段明载淳化五年改为黄门院。", quotation=history)
    yellow = timepoint(w, i, yellow_e, "北宋淳化五年（994）", "内班院改名黄门院", history,
                       "建立黄门院改名节点。", "职源与沿革", category="宦官署")
    court_e = w.entity("内侍省内侍班院", "机构", "职源字段明载又改为内侍省内侍班院。", quotation=history)
    court = timepoint(w, i, court_e, "北宋淳化五年（994）九月", "黄门院改名内侍省内侍班院", history,
                      "建立内侍省内侍班院节点。", "职源与沿革", category="宦官署")
    named = timepoint(w, i, eid, "北宋景德三年（1006）五月", "正式定名内侍省", history,
                      "建立内侍省正式定名节点。", "职源与沿革", category="宦官署")
    relation(w, i, inner, yellow, "前后演变", history, "淳化五年内班院改黄门院。", "职源与沿革")
    relation(w, i, yellow, court, "前后演变", history, "黄门院又改内侍省内侍班院。", "职源与沿革")
    relation(w, i, court, named, "前后演变", history, "景德三年五月定名内侍省。", "职源与沿革")

    yuanfeng = timepoint(w, i, eid, "北宋元丰改制", "内侍班与祗候班合计定额一百八十人，寄班十五人，三案吏史六员", staffing,
                         "建立元丰编制定额节点。", "编制", category="编制", officer_type="内侍")
    yuanyou = timepoint(w, i, eid, "北宋元祐二年（1087）", "内侍班与祗候班定额改为一百人", staffing,
                        "建立元祐二年定额节点。", "编制", category="编制")
    end = timepoint(w, i, eid, "南宋绍兴三十年（1160）九月二十二日", "罢内侍省，并入入内内侍省", history,
                    "建立绍兴三十年罢省节点。", "职源与沿革", category="废罢")
    relation(w, i, end, find_tp(w, "入内内侍省", "南宋绍兴三十年九月", "机构"), "前后演变", history,
             "绍兴三十年罢内侍省，官名及职掌并入入内内侍省。", "职源与沿革")

    for title, label in (("内侍省内侍班", "内侍班"), ("内侍省祗候班", "祗候班"),
                         ("内侍省寄班", "寄班"), ("洒扫班", "洒扫班")):
        ge = w.entity(title, "官职", "编制字段明列内侍省四类班次。", quotation=staffing)
        gt = timepoint(w, i, ge, "北宋时期（具体时间未载）", f"列为内侍省{label}", staffing,
                       f"建立内侍省{label}总层节点。", "编制", category=f"{label}总称")
        relation(w, i, named, gt, "编制隶属", staffing, f"内侍省统辖{label}。", "编制", staff_type=label)
    alias_citation(w, i, named, "简称与别名")
    w.commit()


def simple_additional_office(i, title, source_time, event, grade_value=None, alias=None):
    main = F[i]["text"]; w = W(i)
    eid = w.entity(title, "官职", "正文定义该官为内侍省宦官加官。", quotation=main)
    tp = timepoint(w, i, eid, source_time, event, main, f"建立{title}节点。",
                   category="宦官加官", grade=grade_value)
    relation(w, i, find_tp(w, "内侍省", "北宋初", "机构"), tp, "编制隶属", main,
             f"{title}隶内侍省。", staff_type="宦官加官")
    if alias: alias_citation(w, i, tp, alias)
    w.commit()


def entry491(): simple_additional_office(491, "内侍监", "宋初", "沿存五代南汉官名，用作宦官加官，罕置", alias="简称")
def entry492(): simple_additional_office(492, "内侍少监", "宋初", "沿五代之名，用作小黄门以上宦官加官，罕置")


def entry493():
    i = 493; main = F[i]["text"]; w = W(i)
    eid = w.entity("内侍", "官职", "正文定义其为隶内侍省的宦官加官。", quotation=main)
    sui = timepoint(w, i, eid, "隋代（具体时间未载）", "内侍之名始置", main, "建立内侍历史源流节点。", category="宦官")
    song = timepoint(w, i, eid, "宋前期（具体时间未载）", "沿置为宦官高等加官，内侍以上不常置", main,
                     "建立宋前期内侍加官节点。", category="宦官加官")
    relation(w, i, find_tp(w, "内侍省", "北宋初", "机构"), song, "编制隶属", main, "内侍隶内侍省。", staff_type="宦官加官")
    w.commit()


def entry494():
    i = 494; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职能"); grade = field(i, "品位"); w = W(i)
    eid = find_entity(w, "内常侍", "官职")
    song = find_tp(w, "内常侍", "宋初", "官职")
    cite(w, "Timepoints", song, i, main, "补证内常侍隶内侍省。")
    cite(w, "Timepoints", song, i, history, "补证内常侍秦隋源流及北宋沿置。", "职源与沿革")
    cite(w, "Timepoints", song, i, duty, "补证内常侍作为加官或特授职事官。", "职能")
    cite(w, "Timepoints", song, i, grade, "补证宋初正五品下。", "品位")
    relation(w, i, find_tp(w, "内侍省", "北宋初", "机构"), song, "编制隶属", main, "内常侍隶内侍省。", staff_type="宦官加官")
    moved = timepoint(w, i, eid, "南宋绍兴三十年（1160）九月", "内侍省罢后存其名，改隶入内内侍省", history,
                      "建立内常侍转隶节点。", "职源与沿革", category="宦官加官", grade="正八品")
    relation(w, i, find_tp(w, "入内内侍省", "南宋绍兴三十年九月", "机构"), moved, "编制隶属", history,
             "绍兴三十年后内常侍改隶入内内侍省。", "职源与沿革", staff_type="宦官加官")
    alias_citation(w, i, song, "简称")
    w.commit()


def entry495(): simple_additional_office(495, "内给事", "宋初", "沿隋官名，为小黄门以上宦官加官，并可充公主册封行事官")
def entry496(): simple_additional_office(496, "内寺伯", "宋初", "沿隋官名，为小黄门以上宦官加官", "正七品下（唐制）")
def entry497(): simple_additional_office(497, "宫教博士", "宋初", "沿隋官名，为小黄门以上宦官加官", "从九品下（唐制）")


def paired_bureau_offices(i, bureau, earlier, start_event):
    main = F[i]["text"]; w = W(i)
    be = w.entity(bureau, "机构", f"正文追溯{bureau}历史设置。", quotation=main)
    bt = timepoint(w, i, be, earlier, start_event, main, f"建立{bureau}历史节点。", category="宫内官署")
    song_parent = find_tp(w, "内侍省", "北宋初", "机构")
    for role in ("令", "丞"):
        title = bureau + role
        eid = w.entity(title, "官职", "词头合称所含独立官名。", quotation=main)
        historical = timepoint(w, i, eid, earlier, f"置为{bureau}{role}", main,
                               f"建立{title}历史属官节点。", category="宫内官署属官")
        tp = timepoint(w, i, eid, "宋初", f"仅存{title}官名，局已废，作为小黄门以上宦官加官", main,
                       f"建立{title}宋初加官节点。", category="宦官加官")
        relation(w, i, bt, historical, "编制隶属", main, f"历史上{title}隶{bureau}。", staff_type="历史属官")
        relation(w, i, song_parent, tp, "编制隶属", main, f"{title}作为内侍省宦官加官。", staff_type="宦官加官")
        timepoint(w, i, eid, "北宋真宗朝以后", "不再设置", main, f"建立{title}终止节点。", category="废罢")
    w.commit()


def entry498(): paired_bureau_offices(498, "掖庭局", "隋代（具体时间未载）", "置掖庭局；其令、丞前源可追溯至西汉")


def entry499():
    paired_bureau_offices(499, "宫闱局", "隋", "始置宫闱局")
    i = 499; main = F[i]["text"]; w = W(i)
    eid = w.entity("宫闱令", "官职", "正文明载咸平元年另置有职事的宫闱令。", quotation=main)
    tp = timepoint(w, i, eid, "北宋咸平元年（998）五月五日", "由内侍充任，改为太府寺有职事属官", main,
                   "建立性质改变后的宫闱令节点。", category="太府寺属官")
    relation(w, i, find_tp(w, "太府寺", "宋前期", "机构"), tp, "编制隶属", main,
             "咸平元年宫闱令为太府寺有职事属官。", staff_type="职事官")
    old = find_tp(w, "宫闱局令", "宋初", "官职")
    relation(w, i, old, tp, "前后演变", main, "咸平元年宫闱令由宦官加官转为太府寺职事官。")
    w.commit()


def entry500(): paired_bureau_offices(500, "奚官局", "隋代（具体时间未载）", "由南朝奚官署改称奚官局")


def main():
    assert [F[i]["title"] for i in range(481, 501)] == [
        "入内内品", "入内把门内品", "入内后苑内品", "入内后苑散内品", "入内北班内品",
        "入内后苑勾当事内品", "入内内侍省寄班", "云韶部", "云韶部内品", "内侍省",
        "内侍监", "内侍少监", "内侍", "内常侍", "内给事", "内寺伯", "宫教博士",
        "掖庭局令、丞", "宫闱局令、丞", "奚官局令、丞",
    ]
    assert F[482]["text"].startswith("宦官名。")
    assert F[492]["text"].endswith("罕置（《分纪》卷26《内侍省》）。")
    assert F[493]["text"].startswith("宦官加官名。隶内侍省。") and not F[493]["fields"]
    assert "隋始置宫闱局" in F[499]["text"]
    entry481(); entry482(); entry483(); entry484(); entry485(); entry486(); entry487()
    entry488(); entry489(); entry490(); entry491(); entry492(); entry493(); entry494()
    entry495(); entry496(); entry497(); entry498(); entry499(); entry500()


if __name__ == "__main__": main()
