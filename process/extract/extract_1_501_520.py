#!/usr/bin/env python3
"""提取第一编第501-520条：内班院、黄门院、内侍班院及都知。"""

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
    """据原书第62-63页修复#504/505、#511/512、#519/520错并及官名误字。"""
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(f"SELECT fields FROM {table} WHERE id=503").fetchone()
            assert row and row[0]
            f503 = json.loads(row[0])
            f503["职源与沿革"] = f503["职源与沿革"].replace("内侍班院《分纪》", "内侍班院（《分纪》")
            conn.execute(f"UPDATE {table} SET fields=? WHERE id=503", (json.dumps(f503, ensure_ascii=False),))

            row504 = conn.execute(f"SELECT fields FROM {table} WHERE id=504").fetchone()
            row505 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=505").fetchone()
            assert row504 and row504[0] and row505
            f504 = json.loads(row504[0])
            if row505[1]:
                assert f504["简称"].endswith("：“以")
                f504["简称"] += row505[1]
                conn.execute(f"UPDATE {table} SET fields=? WHERE id=504", (json.dumps(f504, ensure_ascii=False),))
                conn.execute(
                    f"UPDATE {table} SET text='',fields=? WHERE id=505",
                    (json.dumps({"_placeholder": True, "__status__": "placeholder_after_merge"}, ensure_ascii=False),),
                )
            else:
                assert "左都知窦神兴充庄宅使" in f504["简称"] and row505[0] == "内班"

            row511 = conn.execute(f"SELECT fields FROM {table} WHERE id=511").fetchone()
            row512 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=512").fetchone()
            assert row511 and row511[0] and row512
            f511 = json.loads(row511[0])
            if row512[1]:
                assert f511["简称"].endswith("诏，")
                f511["简称"] += row512[1]
                conn.execute(f"UPDATE {table} SET fields=? WHERE id=511", (json.dumps(f511, ensure_ascii=False),))
                conn.execute(
                    f"UPDATE {table} SET text='',fields=? WHERE id=512",
                    (json.dumps({"_placeholder": True, "__status__": "placeholder_after_merge"}, ensure_ascii=False),),
                )
            else:
                assert "本班亦请止称内侍省及赐新印" in f511["简称"] and row512[0] == "内班院"

            for entry_id in (516, 518):
                row = conn.execute(f"SELECT text FROM {table} WHERE id=?", (entry_id,)).fetchone()
                assert row and row[0]
                conn.execute(f"UPDATE {table} SET text=? WHERE id=?", (row[0].replace("宜官名。", "宦官名。"), entry_id))

            row519 = conn.execute(f"SELECT text,fields FROM {table} WHERE id=519").fetchone()
            row520 = conn.execute(f"SELECT title,text,fields FROM {table} WHERE id=520").fetchone()
            assert row519 and row519[1] and row520
            f519 = json.loads(row519[1])
            marker = "北宋大中祥符间见置"
            if marker in f519["职源与沿革"]:
                history519, history520_tail = f519["职源与沿革"].split(marker, 1)
                duty519, duty520_tail = f519["职掌"].split("为内侍省总辖官。", 1)
                grade519, grade520_tail = f519["品位"].split("《元祐令》从六品", 1)
                alias519, merged_head = f519["别名"].split("内侍省左右班都都知 宜官名。隶内侍省。", 1)
                assert not history520_tail.startswith(marker) and not duty520_tail and not merged_head
                f519 = {
                    "职源与沿革": history519,
                    "职掌": duty519,
                    "品位": grade519,
                    "别名": alias519,
                }
                f520 = {
                    "职源与沿革": marker + history520_tail,
                    "职掌": "为内侍省总辖官。",
                    "品位": "《元祐令》从六品" + grade520_tail,
                }
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=? WHERE id=519",
                    (row519[0].replace("宜官名。", "宦官名。"), json.dumps(f519, ensure_ascii=False)),
                )
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=520",
                    ("内侍省左右班都都知", "宦官名。隶内侍省。", json.dumps(f520, ensure_ascii=False)),
                )
            else:
                assert row520[0] == "内侍省左右班都都知" and row520[1] == "宦官名。隶内侍省。"


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute("SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)).fetchone()
    assert row, i
    return {"title": row[0], "page": row[1], "text": row[2] or "", "fields": json.loads(row[3] or "{}")}


F = {i: load(i) for i in range(501, 521)}


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
         note=f"{name}仅作称谓或追称证据，不另建实体")


def inner_province_tp(w): return find_tp(w, "内侍省", "北宋景德三年（1006）五月", "机构")


def paired_bureau_offices(i, bureau, source_time, start_event):
    main = F[i]["text"]; w = W(i)
    be = w.entity(bureau, "机构", f"正文追溯{bureau}始置。", quotation=main)
    bt = timepoint(w, i, be, source_time, start_event, main, f"建立{bureau}历史节点。", category="宫内官署")
    for role, grade in (("令", "正八品下（唐制）"), ("丞", "正九品下（唐制）")):
        title = bureau + role
        eid = w.entity(title, "官职", "合称词头所含独立官名。", quotation=main)
        historical = timepoint(w, i, eid, source_time, f"置为{bureau}{role}", main,
                               f"建立{title}历史属官节点。", category="宫内官署属官", grade=grade)
        song = timepoint(w, i, eid, "宋初", f"仅存官名，局已废，作为小黄门以上宦官加官", main,
                         f"建立{title}宋初加官节点。", category="宦官加官")
        timepoint(w, i, eid, "北宋真宗朝以后", "不再设置", main, f"建立{title}终止节点。", category="废罢")
        relation(w, i, bt, historical, "编制隶属", main, f"历史上{title}隶{bureau}。", staff_type="历史属官")
        relation(w, i, find_tp(w, "内侍省", "北宋初", "机构"), song, "编制隶属", main,
                 f"宋初{title}作为内侍省宦官加官。", staff_type="宦官加官")
    w.commit()


def entry501(): paired_bureau_offices(501, "内仆局", "隋代（具体时间未载）", "隋始置内仆局")
def entry502(): paired_bureau_offices(502, "内府局", "隋代（具体时间未载）", "隋始置内府局")


def entry503():
    i = 503; main = F[i]["text"]; history = field(i, "职源与沿革"); w = W(i)
    eid = find_entity(w, "内班院", "机构")
    start = find_tp(w, "内班院", "北宋初", "机构")
    cite(w, "Timepoints", start, i, main, "补证内班院为宋初宦寺。")
    cite(w, "Timepoints", start, i, history, "补证五代称谓、宋初设置及淳化五年两次改名。", "职源与沿革")
    end = timepoint(w, i, eid, "北宋淳化五年（994）八月", "改名黄门院", history,
                    "建立内班院改名节点。", "职源与沿革", category="改名")
    alias_citation(w, i, start, "简称与追改")
    w.commit()


def simple_inner_office(i, title, event, alias=None):
    main = F[i]["text"]; w = W(i)
    eid = w.entity(title, "官职", "正文定义该官为内班院领院官。", quotation=main)
    tp = timepoint(w, i, eid, "宋初至北宋淳化五年（994）八月", event, main,
                   f"建立{title}任置时段。", category="内班院领院官")
    relation(w, i, find_tp(w, "内班院", "北宋初", "机构"), tp, "编制隶属", main,
             f"{title}隶内班院。", staff_type="领院官")
    if alias: alias_citation(w, i, tp, alias)
    w.commit()


def entry504(): simple_inner_office(504, "内班院左班都知", "任内班院领院官", "简称")
def entry505(): pass
def entry506(): simple_inner_office(506, "内班院右班都知", "任内班院领院官，次于左班都知")


def entry507():
    i = 507; main = F[i]["text"]; w = W(i)
    for side in ("左", "右"):
        title = f"内班院{side}班押班"
        eid = w.entity(title, "官职", "合称词头所含独立押班官名。", quotation=main)
        tp = timepoint(w, i, eid, "宋初至北宋淳化五年（994）八月", "任内班院领院官，次于都知、高于内供奉官", main,
                       f"建立{title}任置时段。", category="内班院领院官")
        relation(w, i, find_tp(w, "内班院", "北宋初", "机构"), tp, "编制隶属", main,
                 f"{title}隶内班院。", staff_type="押班")
        if side == "右": alias_citation(w, i, tp, "别名")
    w.commit()


def entry508():
    i = 508; main = F[i]["text"]; w = W(i)
    eid = find_entity(w, "黄门院", "机构")
    begin = timepoint(w, i, eid, "北宋淳化五年（994）八月十四日", "由内班院改名", main,
                      "建立黄门院精确始置节点。", category="宦寺")
    end = timepoint(w, i, eid, "北宋淳化五年（994）九月十日", "改名内侍省内侍班院", main,
                    "建立黄门院改名终止节点。", category="改名")
    relation(w, i, find_tp(w, "内班院", "北宋淳化五年（994）八月", "机构"), begin,
             "前后演变", main, "淳化五年八月十四日内班院改名黄门院。")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry509():
    i = 509; main = F[i]["text"]; w = W(i)
    eid = w.entity("黄门院左班都知", "官职", "正文定义其由内班院左班都知改名。", quotation=main)
    tp = timepoint(w, i, eid, "北宋淳化五年（994）八月十四日至九月九日", "由内班院左班都知改名，任黄门院领院官", main,
                   "建立黄门院左班都知节点。", category="黄门院领院官")
    relation(w, i, find_tp(w, "内班院左班都知", "宋初至北宋淳化五年（994）八月", "官职"), tp,
             "前后演变", main, "淳化五年八月十四日内班院左班都知改名黄门院左班都知。")
    relation(w, i, find_tp(w, "黄门院", "北宋淳化五年（994）八月十四日", "机构"), tp,
             "编制隶属", main, "黄门院左班都知隶黄门院。", staff_type="领院官")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry510():
    i = 510; main = F[i]["text"]; w = W(i)
    for side in ("左", "右"):
        title = f"黄门院{side}班押班"
        eid = w.entity(title, "官职", "合称词头所含独立押班官名。", quotation=main)
        tp = timepoint(w, i, eid, "北宋淳化五年（994）八月十四日至九月九日", "任黄门院领院官，次于都知、高于内供奉官", main,
                       f"建立{title}节点。", category="黄门院领院官")
        relation(w, i, find_tp(w, f"内班院{side}班押班", "宋初至北宋淳化五年（994）八月", "官职"), tp,
                 "前后演变", main, f"内班院{side}班押班随院改名为黄门院{side}班押班。")
        relation(w, i, find_tp(w, "黄门院", "北宋淳化五年（994）八月十四日", "机构"), tp,
                 "编制隶属", main, f"{title}隶黄门院。", staff_type="押班")
    w.commit()


def entry511():
    i = 511; main = F[i]["text"]; w = W(i)
    eid = find_entity(w, "内侍省内侍班院", "机构")
    begin = timepoint(w, i, eid, "北宋淳化五年（994）九月十日", "由黄门院改名", main,
                      "建立内侍省内侍班院精确始置节点。", category="宦寺")
    end = timepoint(w, i, eid, "北宋景德三年（1006）五月", "改称内侍省", main,
                    "建立内侍省内侍班院改名节点。", category="改名")
    relation(w, i, find_tp(w, "黄门院", "北宋淳化五年（994）九月十日", "机构"), begin,
             "前后演变", main, "淳化五年九月十日黄门院改名内侍省内侍班院。")
    relation(w, i, end, inner_province_tp(w), "前后演变", main, "景德三年五月内侍省内侍班院改称内侍省。")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry512(): pass


def inner_court_office(i, title, event, alias=None, predecessor=None):
    main = F[i]["text"]; w = W(i)
    eid = w.entity(title, "官职", "正文定义该官为内侍省内侍班院领院官。", quotation=main)
    tp = timepoint(w, i, eid, "北宋淳化五年（994）九月十日至景德三年（1006）五月", event, main,
                   f"建立{title}任置时段。", category="内侍班院领院官")
    relation(w, i, find_tp(w, "内侍省内侍班院", "北宋淳化五年（994）九月十日", "机构"), tp,
             "编制隶属", main, f"{title}隶内侍省内侍班院。", staff_type="领院官")
    if predecessor:
        relation(w, i, find_tp(w, predecessor, "北宋淳化五年（994）八月十四日至九月九日", "官职"), tp,
                 "前后演变", main, f"{predecessor}改名为{title}。")
    if alias: alias_citation(w, i, tp, alias)
    w.commit()


def entry513(): inner_court_office(513, "内侍省内侍班院左班都知", "任领院官，高于右班都知", predecessor="黄门院左班都知")
def entry514(): inner_court_office(514, "内侍省内侍班院右班都知", "任领院官，次于左班都知、高于押班", "简称")
def entry515(): inner_court_office(515, "内侍省内侍班院左班副都知", "任副领院官，次于都知、高于右班副都知和押班", "简称")
def entry516(): inner_court_office(516, "内侍省内侍班院右班副都知", "任副领院官，次于左班副都知、高于押班", "简称")
def entry517(): inner_court_office(517, "内侍省内侍班院左班押班", "任次辅领院官，位下于副都知、高于右班押班", predecessor="黄门院左班押班")
def entry518(): inner_court_office(518, "内侍省内侍班院右班押班", "由黄门院右班押班改名，任次辅领院官", predecessor="黄门院右班押班")


def entry519():
    i = 519; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); w = W(i)
    eid = w.entity("内侍省都都知", "官职", "正文定义其为隶内侍省的宦官。", quotation=main)
    begin = timepoint(w, i, eid, "北宋皇祐五年（1053）九月二十六日", "始置内侍省都都知，判省事，为内侍省极品", history,
                      "建立内侍省都都知始置节点。", "职源与沿革", category="内侍省总辖官")
    cite(w, "Timepoints", begin, i, duty, "补证判省事及皇帝坐朝旁侍职掌。", "职掌")
    cite(w, "Timepoints", begin, i, grade, "补证都都知位次、兼判两省及品位。", "品位")
    abolished = timepoint(w, i, eid, "北宋皇祐五年以后、元丰八年以前", "一度罢去", history,
                          "建立都都知中途罢去节点。", "职源与沿革", category="废罢")
    restored = timepoint(w, i, eid, "北宋元丰八年（1085）十二月", "增置内侍省都都知", history,
                         "建立元丰八年复置节点。", "职源与沿革", category="内侍省总辖官")
    relation(w, i, inner_province_tp(w), begin, "编制隶属", main, "内侍省都都知隶内侍省。", staff_type="总辖官")
    alias_citation(w, i, begin, "别名")
    w.commit()


def entry520():
    i = 520; main = F[i]["text"]; history = field(i, "职源与沿革"); duty = field(i, "职掌"); grade = field(i, "品位"); w = W(i)
    eid = w.entity("内侍省左右班都都知", "官职", "正文定义其为隶内侍省的宦官。", quotation=main)
    begin = timepoint(w, i, eid, "北宋大中祥符年间（1008—1016）", "已见设置，任内侍省总辖官", history,
                      "建立左右班都都知早期节点。", "职源与沿革", category="内侍省总辖官")
    cite(w, "Timepoints", begin, i, duty, "补证左右班都都知为内侍省总辖官。", "职掌")
    yuanyou = timepoint(w, i, eid, "北宋元祐时期（1086—1094）", "《元祐令》存其名，从六品，为内侍省极品", history,
                        "建立《元祐令》存名节点。", "职源与沿革", category="内侍省总辖官", grade="从六品")
    cite(w, "Timepoints", yuanyou, i, grade, "补证《元祐令》从六品及极品地位。", "品位")
    relation(w, i, inner_province_tp(w), begin, "编制隶属", main, "内侍省左右班都都知隶内侍省。", staff_type="总辖官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(501, 521)] == [
        "内仆局令、丞", "内府局令、丞", "内班院", "内班院左班都知", "内班",
        "内班院右班都知", "内班院左、右班押班", "黄门院", "黄门院左班都知",
        "黄门院左、右班押班", "内侍省内侍班院", "内班院", "内侍省内侍班院左班都知",
        "内侍省内侍班院右班都知", "内侍省内侍班院左班副都知", "内侍省内侍班院右班副都知",
        "内侍省内侍班院左班押班", "内侍省内侍班院右班押班", "内侍省都都知", "内侍省左右班都都知",
    ]
    assert not F[505]["text"] and not F[512]["text"]
    assert F[516]["text"].startswith("宦官名。") and F[518]["text"].startswith("宦官名。")
    assert F[519]["text"] == "宦官名。隶内侍省。" and "大中祥符" not in field(519, "职源与沿革")
    assert "大中祥符" in field(520, "职源与沿革")
    entry501(); entry502(); entry503(); entry504(); entry505(); entry506(); entry507()
    entry508(); entry509(); entry510(); entry511(); entry512(); entry513(); entry514()
    entry515(); entry516(); entry517(); entry518(); entry519(); entry520()


if __name__ == "__main__": main()
