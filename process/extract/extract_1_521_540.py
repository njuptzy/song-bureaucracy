#!/usr/bin/env python3
"""提取第一编第521-540条：内侍省领省官、内侍班六等与祗候班。"""

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
    """据原书第64-67页修复#526、#528-530、#534、#540 OCR及错并。"""
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(f"SELECT text,fields FROM {table} WHERE id=526").fetchone()
            assert row and row[0] and row[1]
            f526 = json.loads(row[1])
            key = "职源与沿革、职掌、官品"
            if "\n序位 " in f526[key]:
                same, order = f526[key].split("\n序位 ", 1)
                f526[key] = same.strip()
                f526["序位"] = order.strip()
            else:
                assert "序位" in f526
            conn.execute(
                f"UPDATE {table} SET text=?,fields=? WHERE id=526",
                (row[0].rstrip("。") + "。", json.dumps(f526, ensure_ascii=False)),
            )

            row = conn.execute(f"SELECT fields FROM {table} WHERE id=528").fetchone()
            assert row and row[0]
            f528 = json.loads(row[0])
            f528["简称与别名"] = f528["简称与别名"].replace("：“人为内侍押班", "：“入为内侍押班")
            conn.execute(f"UPDATE {table} SET fields=? WHERE id=528", (json.dumps(f528, ensure_ascii=False),))

            row529 = conn.execute(f"SELECT text FROM {table} WHERE id=529").fetchone()
            row530 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=530").fetchone()
            assert row529 and row529[0] and row530
            marker = "内侍省内侍押班 “内侍”为加官"
            if marker in row529[0]:
                text529, tail = row529[0].split(marker, 1)
                text530 = "“内侍”为加官" + tail
                conn.execute(f"UPDATE {table} SET text=? WHERE id=529", (text529,))
                conn.execute(f"UPDATE {table} SET text=?,fields=NULL WHERE id=530", (text530,))
            else:
                assert row530[0] == "内侍省内侍押班" and row530[1].startswith("“内侍”为加官") and row530[2] is None

            row = conn.execute(f"SELECT fields FROM {table} WHERE id=534").fetchone()
            assert row and row[0]
            f534 = json.loads(row[0])
            f534["简称"] = f534["简称"].replace("全称应为内侍省内内侍殿头", "全称应为内侍省内侍殿头")
            conn.execute(f"UPDATE {table} SET fields=? WHERE id=534", (json.dumps(f534, ensure_ascii=False),))

            row = conn.execute(f"SELECT fields FROM {table} WHERE id=540").fetchone()
            assert row and row[0]
            f540 = json.loads(row[0])
            f540["别名"] = f540["别名"].replace("诸内容省使至内侍省内品", "诸内客省使至内侍省内品")
            conn.execute(f"UPDATE {table} SET fields=? WHERE id=540", (json.dumps(f540, ensure_ascii=False),))


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute("SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)).fetchone()
    assert row, i
    return {"title": row[0], "page": row[1], "text": row[2] or "", "fields": json.loads(row[3] or "{}")}


F = {i: load(i) for i in range(521, 541)}


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


def province_tp(w): return find_tp(w, "内侍省", "北宋景德三年（1006）五月", "机构")


def entry521():
    i = 521; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); staffing = field(i, "编制"); w = W(i)
    eid = w.entity("内侍省左右班都知", "官职", "正文定义其为隶内侍省的宦官。", quotation=main)
    start = timepoint(w, i, eid, "北宋景德三年（1006）五月", "立定内侍省时设置，为内侍省总辖官", history,
                      "建立左右班都知始置节点。", "职源与沿革", category="领省官", grade="正六品")
    cite(w, "Timepoints", start, i, duty, "补证总辖内侍省供奉、差遣及选补职掌。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证左右班都知品位与班序。", "品位")
    cite(w, "Timepoints", start, i, staffing, "补证左右班都知无定员。", "编制")
    yuanfeng = timepoint(w, i, eid, "北宋元丰新制", "沿置左右班都知", history,
                         "建立元丰沿置节点。", "职源与沿革", category="领省官")
    yuanyou = timepoint(w, i, eid, "北宋元祐时期（1086—1094）", "《元祐令》称左右班都知，从六品", history,
                        "建立元祐令存名节点。", "职源与沿革", category="领省官", grade="从六品")
    end = timepoint(w, i, eid, "南宋绍兴三十年（1160）以后", "不置", history,
                    "建立绍兴三十年后不置节点。", "职源与沿革", category="废罢")
    relation(w, i, province_tp(w), start, "编制隶属", main, "内侍省左右班都知隶内侍省。", staff_type="总辖官")
    alias_citation(w, i, start, "简称与别名")
    w.commit()


def full_leading_office(i, title, duty_text, grade_text, alias_name, order_text=None):
    main = F[i]["text"]; history = field(i, "职源与沿革"); w = W(i)
    eid = w.entity(title, "官职", "正文定义其为隶内侍省的宦官。", quotation=main)
    start = timepoint(w, i, eid, "北宋景德三年（1006）五月", duty_text, history,
                      f"建立{title}始置节点。", "职源与沿革", category="领省官", grade=grade_text)
    timepoint(w, i, eid, "北宋元丰新制", "沿置", history, f"建立{title}元丰沿置节点。", "职源与沿革", category="领省官")
    timepoint(w, i, eid, "南宋绍兴三十年（1160）九月二十二日", "随内侍省罢而罢", history,
              f"建立{title}罢官节点。", "职源与沿革", category="废罢")
    relation(w, i, province_tp(w), start, "编制隶属", main, f"{title}隶内侍省。", staff_type="领省官")
    for name in ("职掌", "品位", "编制"):
        if name in F[i]["fields"]: cite(w, "Timepoints", start, i, field(i, name), f"补证{title}{name}。", name)
    if order_text: cite(w, "Timepoints", start, i, order_text, f"补证{title}序位。", "序位")
    alias_citation(w, i, start, alias_name)
    w.commit()


def entry522(): full_leading_office(522, "内侍省左班都知", "任领省官；因左右班都知不常除人，实为主掌官", "正六品", "简称")


def entry523():
    i = 523; main = F[i]["text"]; same = field(i, "职源与沿革、职掌、官品"); order = field(i, "序位"); staffing = field(i, "编制"); w = W(i)
    eid = w.entity("内侍省右班都知", "官职", "正文定义其为隶内侍省的宦官。", quotation=main)
    start = timepoint(w, i, eid, "北宋景德三年（1006）五月", "与左班都知同置，任领省官", same,
                      "依同左班都知字段建立始置节点。", "职源与沿革、职掌、官品", category="领省官", grade="正六品")
    cite(w, "Timepoints", start, i, order, "补证右班都知次于左班都知、高于押班。", "序位")
    cite(w, "Timepoints", start, i, staffing, "补证右班都知无定员。", "编制")
    timepoint(w, i, eid, "北宋元丰新制", "沿置", same, "依同左班都知字段建立元丰节点。", "职源与沿革、职掌、官品", category="领省官")
    timepoint(w, i, eid, "南宋绍兴三十年（1160）九月二十二日", "随内侍省罢而罢", same,
              "依同左班都知字段建立罢官节点。", "职源与沿革、职掌、官品", category="废罢")
    relation(w, i, province_tp(w), start, "编制隶属", main, "内侍省右班都知隶内侍省。", staff_type="领省官")
    alias_citation(w, i, start, "简称")
    w.commit()


def entry524():
    i = 524; main = F[i]["text"]; w = W(i)
    eid = w.entity("内侍省都知司", "机构", "正文定义其为内侍省左、右班都知治所。", quotation=main)
    tp = timepoint(w, i, eid, "北宋景德三年（1006）七月二十日以前", "作为都知治所，掌宦官轮值、差遣、调配及签发公事", main,
                   "建立内侍省都知司节点。", category="都知治所")
    relation(w, i, province_tp(w), tp, "上下级机构", main, "都知司为内侍省所属治所。")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry525():
    i = 525; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); w = W(i)
    eid = w.entity("内侍省左班副都知", "官职", "正文定义其为隶内侍省的宦官。", quotation=main)
    start = timepoint(w, i, eid, "北宋景德三年（1006）五月", "与左班都知同置，辅佐左班都知", history,
                      "建立左班副都知始置节点。", "职源与沿革", category="领省官", grade="正六品")
    cite(w, "Timepoints", start, i, duty, "补证左班副都知辅佐职掌。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证左班副都知品位、序位与充任资格。", "品位")
    timepoint(w, i, eid, "北宋元丰新制", "沿置，正六品", history,
              "依同左班都知字段建立元丰沿置节点。", "职源与沿革", category="领省官", grade="正六品")
    timepoint(w, i, eid, "南宋绍兴三十年（1160）九月二十二日", "随内侍省罢而罢", history,
              "依同左班都知字段建立罢官节点。", "职源与沿革", category="废罢")
    relation(w, i, province_tp(w), start, "编制隶属", main, "内侍省左班副都知隶内侍省。", staff_type="领省官")
    alias_citation(w, i, start, "简称")
    w.commit()


def entry526():
    i = 526; main = F[i]["text"]; same = field(i, "职源与沿革、职掌、官品"); order = field(i, "序位"); w = W(i)
    eid = w.entity("内侍省右班副都知", "官职", "正文定义其为隶内侍省的宦官。", quotation=main)
    start = timepoint(w, i, eid, "北宋景德三年（1006）五月", "与左班副都知同置，任领省官", same,
                      "依同左班副都知字段建立节点。", "职源与沿革、职掌、官品", category="领省官", grade="正六品")
    cite(w, "Timepoints", start, i, order, "补证位次于左班副都知、高于押班。", "序位")
    timepoint(w, i, eid, "北宋元丰新制", "沿置，正六品", same,
              "依同左班副都知字段建立元丰沿置节点。", "职源与沿革、职掌、官品", category="领省官", grade="正六品")
    timepoint(w, i, eid, "南宋绍兴三十年（1160）九月二十二日", "随内侍省罢而罢", same,
              "依同左班副都知字段建立罢官节点。", "职源与沿革、职掌、官品", category="废罢")
    relation(w, i, province_tp(w), start, "编制隶属", main, "内侍省右班副都知隶内侍省。", staff_type="领省官")
    alias_citation(w, i, start, "简称")
    w.commit()


def entry527():
    i = 527; main = F[i]["text"]; w = W(i)
    eid = w.entity("内侍省内侍右班副都知", "官职", "正式词头说明其为带内侍加官的右班副都知。", quotation=main)
    tp = timepoint(w, i, eid, "宋代（具体时间未载）", "以“内侍”为加官，任内侍省右班副都知", main,
                   "建立带内侍加官的右班副都知节点。", category="领省官兼加官")
    relation(w, i, province_tp(w), tp, "编制隶属", main, "该官隶内侍省。", staff_type="领省官兼加官")
    w.commit()


def entry528():
    i = 528; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); staffing = field(i, "编制"); w = W(i)
    eid = w.entity("内侍省押班", "官职", "正文定义其为隶内侍省的宦官。", quotation=main)
    start = timepoint(w, i, eid, "北宋景德三年（1006）五月", "初分左、右班押班，任领省官", history,
                      "建立内侍省押班始置节点。", "职源与沿革", category="领省官", grade="正六品")
    later = timepoint(w, i, eid, "北宋景德三年以后（具体时间未载）", "取消左右之别，统称内侍省押班", history,
                      "建立押班统一称谓节点。", "职源与沿革", category="领省官")
    end = timepoint(w, i, eid, "南宋绍兴三十年（1160）九月二十二日", "随内侍省罢而罢", history,
                    "建立押班罢官节点。", "职源与沿革", category="废罢")
    for name, quotation in (("职掌", duty), ("品位", grade), ("编制", staffing)):
        cite(w, "Timepoints", start, i, quotation, f"补证内侍省押班{name}。", name)
    relation(w, i, province_tp(w), start, "编制隶属", main, "内侍省押班隶内侍省。", staff_type="领省官")
    alias_citation(w, i, start, "简称与别名")
    w.commit()


def simple_special(i, title, event):
    main = F[i]["text"]; w = W(i)
    eid = w.entity(title, "官职", "正式词头定义其为内侍省押班的加官或特授形态。", quotation=main)
    tp = timepoint(w, i, eid, "宋代（具体时间未载）", event, main, f"建立{title}节点。", category="押班兼加官")
    relation(w, i, province_tp(w), tp, "编制隶属", main, f"{title}隶内侍省。", staff_type="押班兼加官")
    w.commit()


def entry529(): simple_special(529, "内侍省内侍押班公事", "押班加内侍且带公事，为特除官，不签书押班公事")
def entry530(): simple_special(530, "内侍省内侍押班", "以内侍为加官，位尊于不带内侍的押班")


SIX = (
    ("内侍省内东头供奉官", "从八品", "内侍班第一等"),
    ("内侍省内西头供奉官", "从八品", "内侍班第二等"),
    ("内侍省内侍殿头", "正九品", "内侍班第三等"),
    ("内侍省内侍高品", "正九品", "内侍班第四等"),
    ("内侍省内侍高班", "从九品", "内侍班第五等"),
    ("内侍省内侍黄门", "从九品", "内侍班第六等"),
)


def entry531():
    i = 531; main = F[i]["text"]; history = field(i, "职源与改革"); duty = field(i, "职掌"); grade = field(i, "品位"); staffing = field(i, "编制"); w = W(i)
    eid = find_entity(w, "内侍省内侍班", "官职")
    base = find_tp(w, "内侍省内侍班", "北宋时期（具体时间未载）", "官职")
    cite(w, "Timepoints", base, i, main, "补证内侍班为内侍省内侍官总名。")
    xianping = timepoint(w, i, eid, "北宋咸平年间（998—1003）", "已见设置内侍班", history,
                         "建立咸平内侍班节点。", "职源与改革", category="内侍官总称")
    reform = timepoint(w, i, eid, "北宋大中祥符二年（1009）二月", "改定内侍班六等内侍官", history,
                       "建立大中祥符二年六等节点。", "职源与改革", category="内侍官总称")
    quota = timepoint(w, i, eid, "北宋皇祐五年（1053）闰七月", "内侍班定额一百八十人", staffing,
                      "建立皇祐定额节点。", "编制", category="编制")
    yuanfeng = timepoint(w, i, eid, "北宋元丰新制", "内侍班、祗候班合计定额一百八十人", staffing,
                         "建立元丰定额节点。", "编制", category="编制")
    yuanyou = timepoint(w, i, eid, "北宋元祐改制", "供奉官以下至黄门定额一百人", staffing,
                        "建立元祐定额节点。", "编制", category="编制")
    end = timepoint(w, i, eid, "南宋绍兴三十年（1160）九月", "随内侍省罢而罢", history,
                    "建立内侍班罢置节点。", "职源与改革", category="废罢")
    cite(w, "Timepoints", reform, i, duty, "补证内侍班供奉、出使、扈从与选补职掌。", "职掌")
    cite(w, "Timepoints", reform, i, grade, "补证内侍班六等品位及班序。", "品位")
    relation(w, i, find_tp(w, "内侍省内侍班院", "北宋淳化五年（994）九月十日", "机构"), xianping,
             "编制隶属", history, "咸平年间内侍班隶当时的内侍省内侍班院。", "职源与改革", staff_type="内侍班")
    relation(w, i, province_tp(w), reform, "编制隶属", history,
             "景德三年正式定名后，内侍班隶内侍省。", "职源与改革", staff_type="内侍班")
    for title, rank, order in SIX:
        oe = w.entity(title, "官职", "职源字段逐项列为内侍班六等官。", quotation=history)
        ot = timepoint(w, i, oe, "北宋大中祥符二年（1009）二月", f"改定为{order}", history,
                       f"建立{title}六等节点。", "职源与改革", category="内侍班", grade=rank)
        relation(w, i, reform, ot, "统称与实例", history, f"内侍省内侍班为总称，{title}为六等实例。", "职源与改革")
        relation(w, i, province_tp(w), ot, "编制隶属", history, f"{title}隶内侍省。", "职源与改革", staff_type="内侍班")
    alias_citation(w, i, reform, "简称")
    w.commit()


def child_base(i, title):
    w = W(i); main = F[i]["text"]; eid = find_entity(w, title, "官职")
    tp = find_tp(w, title, "北宋大中祥符二年（1009）二月", "官职")
    cite(w, "Timepoints", tp, i, main, f"补证{title}隶内侍省内侍班。")
    for name in F[i]["fields"]:
        cite(w, "Timepoints", tp, i, field(i, name), f"补证{title}{name}。", name)
    return w, eid, tp


def historical_chain(i, title, stages):
    w, eid, current = child_base(i, title); history = field(i, "职源与沿革")
    previous = None
    for old_title, when, event, category in stages:
        oe = w.entity(old_title, "官职", "职源字段记载该旧官名。", quotation=history)
        ot = timepoint(w, i, oe, when, event, history, f"建立{old_title}前身节点。", "职源与沿革", category=category)
        if previous is not None:
            relation(w, i, previous, ot, "前后演变", history, f"{stages[stages.index((old_title, when, event, category))-1][0]}演变为{old_title}。", "职源与沿革")
        previous = ot
    if previous is not None:
        relation(w, i, previous, current, "前后演变", history, f"{stages[-1][0]}改为{title}。", "职源与沿革")
    w.commit()


def entry532(): historical_chain(532, "内侍省内东头供奉官", (("内供奉官", "五代至宋初", "五代已有，宋初内班院沿置", "宦官"), ("内侍省内供奉官", "北宋景德三年（1006）五月", "随院改名为内侍省内供奉官", "内侍班")))


def entry533():
    w, eid, tp = child_base(533, "内侍省内西头供奉官"); w.commit()


def entry534(): historical_chain(534, "内侍省内侍殿头", (("殿头高品", "北宋太宗朝（具体时间未载）", "始置殿头高品", "宦官"), ("内侍省殿头高品", "北宋景德三年（1006）五月", "随院改名为内侍省殿头高品", "内侍班")))
def entry535(): historical_chain(535, "内侍省内侍高品", (("高品", "北宋太宗朝（具体时间未载）", "始置高品", "宦官"), ("内侍省高品", "北宋景德三年（1006）五月", "随院改名为内侍省高品", "内侍班")))
def entry536(): historical_chain(536, "内侍省内侍高班", (("高班内品", "北宋太宗朝（具体时间未载）", "始置高班内品", "宦官"), ("内侍省高班内品", "北宋景德三年（1006）五月", "随院改名为内侍省高班内品", "内侍班")))


def entry537():
    i = 537; w, eid, current = child_base(i, "内侍省内侍黄门"); history = field(i, "职源与沿革")
    old = w.entity("黄门", "官职", "职源字段追溯秦汉黄门及宋初内班院黄门。", quotation=history)
    old_tp = timepoint(w, i, old, "宋初", "内班院置黄门，为宦官初阶", history, "建立黄门前身节点。", "职源与沿革", category="宦官初阶")
    mid = w.entity("内侍省黄门", "官职", "职源字段记载景德三年内侍省黄门。", quotation=history)
    mid_tp = timepoint(w, i, mid, "北宋景德三年（1006）五月", "随院定名改为内侍省黄门", history,
                       "建立内侍省黄门节点。", "职源与沿革", category="内侍班")
    relation(w, i, old_tp, mid_tp, "前后演变", history, "宋初黄门随院定名为内侍省黄门。", "职源与沿革")
    relation(w, i, mid_tp, current, "前后演变", history, "大中祥符二年内侍省黄门改名内侍省内侍黄门。", "职源与沿革")
    timepoint(w, i, eid, "北宋大中祥符八年（1015）五月", "废罢", history, "建立内侍黄门废罢节点。", "职源与沿革", category="废罢")
    timepoint(w, i, eid, "北宋元丰新制", "复置", history, "建立元丰复置节点。", "职源与沿革", category="内侍班", grade="从九品")
    w.commit()


def entry538():
    i = 538; main = F[i]["text"]; w = W(i)
    eid = w.entity("内侍省小黄门", "官职", "正文定义其为内班院初进宦官，后归内侍省。", quotation=main)
    early = timepoint(w, i, eid, "宋初", "私身内侍初进称小黄门，隶内班院，经恩可迁补黄门", main,
                      "建立小黄门宋初节点。", category="初进宦官")
    later = timepoint(w, i, eid, "北宋景德三年（1006）五月", "随院改名，归隶内侍省", main,
                      "建立小黄门转隶内侍省节点。", category="初进宦官")
    relation(w, i, find_tp(w, "内班院", "北宋初", "机构"), early, "编制隶属", main,
             "宋初小黄门隶内班院。", staff_type="初进宦官")
    relation(w, i, province_tp(w), later, "编制隶属", main, "景德三年后小黄门归隶内侍省。", staff_type="初进宦官")
    w.commit()


def entry539():
    i = 539; main = F[i]["text"]; w = W(i)
    eid = w.entity("内侍省内侍殿直", "官职", "正文定义其为内侍省内侍班临时特置官。", quotation=main)
    tp = timepoint(w, i, eid, "北宋咸平五年（1002）十一月二十四日", "为张仁恭临时改置，避免殿头高品称呼", main,
                   "建立内侍省内侍殿直特置节点。", category="临时特置")
    relation(w, i, find_tp(w, "内侍省内侍班院", "北宋淳化五年（994）九月十日", "机构"), tp,
             "编制隶属", main, "咸平五年该官隶当时的内侍省内侍班院；词头内侍省为追称。", staff_type="内侍班",
             note="咸平五年尚未正式定名内侍省，按当时机构名连接内侍省内侍班院")
    relation(w, i, find_tp(w, "内侍省内侍班", "北宋咸平年间（998—1003）", "官职"), tp,
             "统称与实例", main, "正文明确该官隶内侍省内侍班。")
    w.commit()


def entry540():
    i = 540; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); w = W(i)
    eid = find_entity(w, "内侍省祗候班", "官职")
    base = find_tp(w, "内侍省祗候班", "北宋时期（具体时间未载）", "官职")
    cite(w, "Timepoints", base, i, main, "补证祗候班为内侍省诸内品、祗候使臣总名。")
    begin = timepoint(w, i, eid, "北宋大中祥符二年（1009）", "改定祗候高班内品等九等", history,
                      "建立祗候班九等节点。", "职源与沿革", category="祗候使臣总称")
    yuanfeng = timepoint(w, i, eid, "北宋元丰改制", "沿置祗候班，名目有所增减变更", history,
                         "建立元丰祗候班节点。", "职源与沿革", category="祗候使臣总称", grade="从九品")
    south = timepoint(w, i, eid, "南宋初", "沿置，从九品", grade, "建立南宋沿置节点。", "品位", category="祗候使臣总称", grade="从九品")
    cite(w, "Timepoints", begin, i, duty, "补证祗候班职掌同黄门以上并可安置责降官。", "职掌")
    cite(w, "Timepoints", begin, i, grade, "补证祗候班品位及班序。", "品位")
    relation(w, i, province_tp(w), begin, "编制隶属", main, "内侍省祗候班隶内侍省。", staff_type="祗候班")
    alias_citation(w, i, begin, "别名")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(521, 541)] == [
        "内侍省左右班都知", "内侍省左班都知", "内侍省右班都知", "内侍省都知司",
        "内侍省左班副都知", "内侍省右班副都知", "内侍省内侍右班副都知", "内侍省押班",
        "内侍省内侍押班公事", "内侍省内侍押班", "内侍省内侍班", "内侍省内东头供奉官",
        "内侍省内西头供奉官", "内侍省内侍殿头", "内侍省内侍高品", "内侍省内侍高班",
        "内侍省内侍黄门", "内侍省小黄门", "内侍省内侍殿直", "内侍省祗候班",
    ]
    assert "序位" in F[526]["fields"] and F[526]["text"].endswith("。")
    assert F[530]["text"].startswith("“内侍”为加官") and not F[530]["fields"]
    assert "内侍省内内侍殿头" not in field(534, "简称")
    assert "内客省使" in field(540, "别名")
    entry521(); entry522(); entry523(); entry524(); entry525(); entry526(); entry527(); entry528()
    entry529(); entry530(); entry531(); entry532(); entry533(); entry534(); entry535(); entry536()
    entry537(); entry538(); entry539(); entry540()


if __name__ == "__main__": main()
