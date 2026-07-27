#!/usr/bin/env python3
"""提取 chapter2t4 修复后第321–339条（修复前原序第321–340条）。"""
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
    assert row, i
    fields = json.loads(row[3] or "{}")
    return {
        "title": row[0], "page": row[1], "text": row[2] or "", "fields": fields,
        "all": "\n".join([row[2] or ""] + [str(v) for k, v in fields.items() if not k.startswith("_")]),
    }


F = {i: load(i) for i in range(321, 340)}


def q(i, text):
    assert text in F[i]["all"], f"#{i} 不含：{text}"
    return text


def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])
def C(i): return f"《宋代官制辞典》第{F[i]['page']}页“{F[i]['title']}”条"
def entity(w, title, type_, quotation, decision): return w.entity(title, type_, decision, quotation=quotation)


def cite(w, table, rid, i, quotation, decision, **kw):
    return w.citation(table, rid, C(i), quotation, decision, **kw)


def tp(w, eid, time, event, i, quotation, category, decision, **kw):
    tid = w.timepoint(eid, time, event, decision, quotation, attr_category=category, **kw)
    cite(w, "Timepoints", tid, i, quotation, decision)
    return tid


def rel(w, source, target, kind, i, quotation, decision, **kw):
    rid = w.relationship(source, target, kind, decision, quotation, **kw)
    cite(w, "Relationships", rid, i, quotation, decision)
    return rid


def node(w, title, time, type_=None):
    eid = w.find_entity(title, type_); assert eid, f"缺实体：{title}"
    tid = w.find_timepoint(eid, time); assert tid, f"{title} 缺时间点：{time}"
    return eid, tid


def chain(w, tids, decision):
    assert len(tids) == len(set(tids)), tids
    for pos, tid in enumerate(tids):
        w.relink(tid, decision,
                 prev_id=tids[pos - 1] if pos else None,
                 succ_id=tids[pos + 1] if pos + 1 < len(tids) else None)


def simple_authorized_deputy(i, title, office):
    z = F[i]["text"]; w = W(i)
    eid = entity(w, title, "官职", z, "辞典明载为资浅者暂代三司副使的差遣官。")
    tid = tp(w, eid, "宋代（未载具体年月）", "本部副使缺时由资浅者带“权”字暂代",
             i, z, "财政副长官", f"建{title}概括节点。")
    office_tp = node(w, office, "北宋咸平六年", "机构")[1]
    rel(w, office_tp, tid, "编制隶属", i, z, f"{title}为{office}副长官的权任形态。", staff_type="官")
    w.commit()


def entry321(): simple_authorized_deputy(321, "权三司度支副使", "度支")
def entry322(): simple_authorized_deputy(322, "权三司户部副使", "户部")


def entry323():
    i = 323; z = F[i]["text"]
    q_start = F[i]["fields"]["职源"]
    q_rank = F[i]["fields"]["品位"]
    w = W(i)
    total_e = entity(w, "权发遣三司副使公事", "官职", z, "原文明载为三种权发遣副使公事的通称。")
    total_t = tp(w, total_e, "宋代（未载具体年月）", "权发遣盐铁、度支、户部副使公事通称",
                 i, z, "财政副长官合称", "建通称承载节点。")
    cite(w, "Timepoints", total_t, i, q_rank, "补充权发遣副使低于权副使一等。", note="品位")
    titles = ("权发遣三司盐铁副使公事", "权发遣三司度支副使公事", "权发遣三司户部副使公事")
    for title in titles:
        eid = entity(w, title, "官职", z, f"通称条明确列出实例{title}。")
        tid = tp(w, eid, "宋代（未载具体年月）", "权发遣三司副使公事之一",
                 i, z, "财政副长官", f"建{title}通称实例节点。")
        rel(w, total_t, tid, "统称与实例", i, z, f"权发遣三司副使公事包括{title}。")
    salt_e = w.find_entity("权发遣三司盐铁副使公事", "官职")
    exact = tp(w, salt_e, "北宋熙宁三年八月一日", "始置权发遣盐铁副使公事", i, q_start,
               "财政副长官", "建权发遣盐铁副使公事始置节点。", chain="head")
    cite(w, "Timepoints", exact, i, F[i]["fields"]["省称"], "补充权发遣制度自傅尧俞始。", note="职源")
    w.commit()


def simple_dispatch_deputy(i, title, office):
    z = F[i]["text"]; w = W(i)
    eid = w.find_entity(title, "官职")
    assert eid
    tid = node(w, title, "宋代（未载具体年月）", "官职")[1]
    cite(w, "Timepoints", tid, i, z, f"本条直接补证{title}的任用层级。")
    office_tp = node(w, office, "北宋咸平六年", "机构")[1]
    rel(w, office_tp, tid, "编制隶属", i, z, f"{title}为{office}副长官缺员时的权发遣形态。", staff_type="官")
    w.commit()


def entry324(): simple_dispatch_deputy(324, "权发遣三司盐铁副使公事", "盐铁")
def entry325(): simple_dispatch_deputy(325, "权发遣三司度支副使公事", "度支")
def entry326(): simple_dispatch_deputy(326, "权发遣三司户部副使公事", "户部")


def entry327():
    i = 327; z = F[i]["text"]; hist = F[i]["fields"]["职源与沿革"]
    w = W(i)
    total_e = entity(w, "三司判官", "官职", z, "辞典明载其既可为正式官名，也可为三部判官通称。")
    pre = tp(w, total_e, "后周显德初", "已有三司判官之名", i, hist,
             "财政判官合称", "建后周始见节点。", chain="none")
    song = tp(w, total_e, "北宋太平兴国八年前", "或为正式官名，或为三部判官通称，罕置",
              i, hist, "财政判官合称", "建宋初制度节点。", chain="none")
    chain(w, [pre, song], "连接三司判官后周始见与宋初制度节点。")
    for title in ("三司盐铁判官", "三司度支判官", "三司户部判官"):
        eid = entity(w, title, "官职", hist, f"三司判官条明确列出实例{title}。")
        tid = tp(w, eid, "北宋太平兴国八年前", "三部判官之一",
                 i, hist, "财政判官", f"建{title}宋初实例节点。")
        rel(w, song, tid, "统称与实例", i, hist, f"三司判官通称包括{title}。")
    w.commit()


def entry328():
    i = 328; z = F[i]["text"]; w = W(i)
    eid = entity(w, "随驾三司判官", "官职", z, "辞典明载为临时差遣。")
    tid = tp(w, eid, "北宋太平兴国四年", "置随驾三司判官", i, z,
             "临时差遣", "建太平兴国四年节点。")
    office = node(w, "随驾三司", "宋代（未载具体年月）", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "随驾三司判官为随驾三司属官。", staff_type="官")
    w.commit()


def entry329():
    i = 329; z = F[i]["text"]; w = W(i)
    eid = entity(w, "总计度司判官", "官职", z, "辞典明载为总计度司属官。")
    tid = tp(w, eid, "北宋淳化五年至十二月", "置，十二月罢，位于左右计判官之上",
             i, z, "财政判官", "建淳化五年置罢时段节点。")
    office = node(w, "总计司", "北宋淳化四年十月十六日", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "总计度司判官为总计司属官。", staff_type="官")
    w.commit()


def entry330():
    i = 330; z = F[i]["text"]; w = W(i)
    total_e = entity(w, "左、右计司判官", "官职", z, "标题和正文明确为左右计司判官的合称。")
    total_t = tp(w, total_e, "北宋淳化四年十月十六日至淳化五年十二月二十五日",
                 "始置至罢，分领十道判官事", i, z, "财政判官合称", "建置罢时段节点。")
    conflicts = []
    for title, office, source_i in (("左计司判官", "左计司", 287), ("右计司判官", "右计司", 288)):
        eid = entity(w, title, "官职", z, f"合称条明确包含{title}。")
        tid = tp(w, eid, "北宋淳化四年十月十六日至淳化五年十二月二十五日",
                 "分领十道判官事", i, z, "财政判官", f"建{title}置罢时段节点。")
        rel(w, total_t, tid, "统称与实例", i, z, f"左、右计司判官包括{title}。")
        office_tp = node(w, office, "北宋淳化四年十月十六日至淳化五年十二月二十四日", "机构")[1]
        rid = w.relationship(office_tp, tid, "编制隶属", f"{title}隶{office}。", z, staff_type="官")
        cite(w, "Relationships", rid, i, z, f"{title}隶{office}；本条判官罢于十二月二十五日。",
             conflict_flag=1, note="本条判官止于淳化五年十二月二十五日，所隶计司条作十二月二十四日。")
        conflicts.append((rid, source_i))
    w.commit()
    for rid, source_i in conflicts:
        source = load(source_i)
        source_c = f"《宋代官制辞典》第{source['page']}页“{source['title']}”条"
        sw = EntryWriter(ENTRY_DB, source["title"], source["page"])
        sw.citation(
            "Relationships", rid, source_c, source["text"],
            "补充所隶计司止于淳化五年十二月二十四日的相冲突证据。",
            conflict_flag=1,
            note="计司条止于十二月二十四日，左、右计司判官条作十二月二十五日。",
        )
        sw.commit()


def entry331():
    i = 331; z = F[i]["text"]; w = W(i)
    total_e = entity(w, "左、右计司十道判官", "官职", z, "原文明载为河南、河北等十道判官总名。")
    total_t = tp(w, total_e, "北宋淳化四年十月十六日至淳化五年十二月二十四日",
                 "始置至罢，各掌本道财谷事", i, z, "财政判官合称", "建十道判官置罢时段节点。")
    for office in ("左计司", "右计司"):
        office_tp = node(w, office, "北宋淳化四年十月十六日至淳化五年十二月二十四日", "机构")[1]
        rel(w, office_tp, total_t, "编制隶属", i, z, "十道判官分隶左、右计司，具体分道未载。", staff_type="官")
    ways = ("河南", "河北", "河东", "关西", "剑南", "淮南", "江南东", "江南西", "两浙", "广南")
    for way in ways:
        title = f"{way}道判官"
        eid = entity(w, title, "官职", z, f"十道判官名单明确列{title}。")
        tid = tp(w, eid, "北宋淳化四年十月十六日至淳化五年十二月二十四日",
                 "掌本道财谷事", i, z, "财政判官", f"建{title}置罢时段节点。")
        rel(w, total_t, tid, "统称与实例", i, z, f"左、右计司十道判官包括{title}。")
    w.commit()


def entry332():
    i = 332; z = F[i]["text"]; start = F[i]["fields"]["职源"]
    w = W(i)
    total_e = entity(w, "权发遣三司判官公事", "官职", z, "原文明载为三种权发遣三司判官公事的总名。")
    total_t = tp(w, total_e, "北宋庆历三年五月十二日", "始置，作为三种权发遣三司判官公事总名",
                 i, start, "财政判官合称", "建庆历三年始置节点。")
    cite(w, "Timepoints", total_t, i, F[i]["fields"]["职能"], "补充设置目的与久任制度。", note="职能")
    titles = ("权发遣三司盐铁判官公事", "权发遣三司度支判官公事", "权发遣三司户部公事")
    for title in titles:
        eid = entity(w, title, "官职", z, f"总名条明确包含{title}。")
        tid = tp(w, eid, "北宋庆历三年五月十二日", "权发遣三司判官公事之一",
                 i, start, "财政判官", f"建{title}始置节点。")
        rel(w, total_t, tid, "统称与实例", i, z, f"权发遣三司判官公事包括{title}。")
    w.commit()


def entry333():
    i = 333; hist = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]
    duty = F[i]["fields"]["职掌"]; w = W(i)
    eid = w.find_entity("三司盐铁判官", "官职"); assert eid
    existing = node(w, "三司盐铁判官", "北宋太平兴国八年前", "官职")[1]
    stages = [
        tp(w, eid, "唐大和五年四月", "已见判盐铁案之职，尚非正式官名", i, hist, "财政判官", "建唐代源流节点。", chain="none"),
        tp(w, eid, "宋初", "沿五代之制置一人", i, comp, "财政判官", "建宋初一员节点。", chain="none"),
        existing,
        tp(w, eid, "北宋太平兴国四年", "不置部判官", i, comp, "财政判官", "建不置节点。", chain="none"),
        tp(w, eid, "北宋淳化四年", "分十道，置道判官", i, comp, "财政判官", "建十道判官节点。", chain="none"),
        tp(w, eid, "北宋淳化五年十二月", "置盐铁判官二人", i, comp, "财政判官", "建二员节点。", chain="none"),
        tp(w, eid, "北宋大中祥符七年", "置盐铁判官三人", i, comp, "财政判官", "建三员节点。", chain="none"),
        tp(w, eid, "北宋元丰改制前", "沿置", i, hist, "财政判官", "建元丰改制前沿置节点。", chain="none"),
    ]
    chain(w, stages, "按唐代源流、宋初及北宋编制变化连接盐铁判官时间链。")
    cite(w, "Timepoints", stages[-2], i, duty, "补充与副使签署本部公事的职掌。", note="职掌")
    salt_e = w.find_entity("盐铁", "机构"); assert salt_e
    salt_daxiang = tp(w, salt_e, "北宋大中祥符七年", "盐铁判官增至三人", i, comp,
                      "财政机构", "补建盐铁判官员额变化节点。")
    office_times = ("宋初", "北宋淳化五年十二月二十四日", "北宋大中祥符七年")
    officer_nodes = (stages[1], stages[5], stages[6])
    for office_time, officer_tp, quota in zip(office_times, officer_nodes, (1, 2, 3)):
        office_tp = node(w, "盐铁", office_time, "机构")[1]
        rel(w, office_tp, officer_tp, "编制隶属", i, comp, f"盐铁在该期置判官{quota}人。",
            staff_quota=quota, staff_type="官")
    w.commit()


def simple_authorized_judge(i, title, office):
    z = F[i]["text"]; w = W(i)
    eid = entity(w, title, "官职", z, "辞典明载为本部判官缺员时的权任差遣。")
    tid = tp(w, eid, "宋代（未载具体年月）", "本部判官缺时暂代者带“权”字",
             i, z, "财政判官", f"建{title}概括节点。")
    office_tp = node(w, office, "北宋咸平六年", "机构")[1]
    rel(w, office_tp, tid, "编制隶属", i, z, f"{title}为{office}判官的权任形态。", staff_type="官")
    w.commit()


def entry334(): simple_authorized_judge(334, "权三司盐铁判官", "盐铁")


def entry335():
    i = 335; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("权发遣三司盐铁判官公事", "官职"); assert eid
    tid = node(w, "权发遣三司盐铁判官公事", "北宋庆历三年五月十二日", "官职")[1]
    cite(w, "Timepoints", tid, i, z, "本条直接补证其资历低于权盐铁判官。", note="品位")
    cite(w, "Timepoints", tid, i, F[i]["fields"]["职能"], "补充权发遣久任制度的设置目的。", note="职能")
    office = node(w, "盐铁", "北宋咸平六年", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "权发遣三司盐铁判官公事属盐铁部判官系统。", staff_type="官")
    w.commit()


def entry336():
    i = 336; hist = F[i]["fields"]["职源与沿革"]; duty = F[i]["fields"]["职掌"]
    w = W(i); eid = w.find_entity("三司度支判官", "官职"); assert eid
    early = node(w, "三司度支判官", "北宋太平兴国八年前", "官职")[1]
    stages = [
        tp(w, eid, "唐代", "已有判度支事官称判官", i, hist, "财政判官", "建唐代源流节点。", chain="none"),
        tp(w, eid, "五代", "成为正式官名", i, hist, "财政判官", "建五代正式官名节点。", chain="none"),
        tp(w, eid, "宋初", "沿置", i, hist, "财政判官", "建宋初沿置节点。", chain="none"),
        early,
        tp(w, eid, "北宋元丰改制", "罢", i, hist, "财政判官", "建元丰罢置节点。", chain="none"),
    ]
    chain(w, stages, "连接度支判官唐代源流、五代正式化、宋初沿置与元丰罢置。")
    cite(w, "Timepoints", stages[2], i, duty, "补充度支判官职掌。", note="职掌")
    office = node(w, "度支", "宋初", "机构")[1]
    rel(w, office, stages[2], "编制隶属", i, duty, "三司度支判官分治度支诸案。", staff_type="官")
    w.commit()


def entry337(): simple_authorized_judge(337, "权三司度支判官", "度支")


def entry338():
    i = 338; w = W(i); z = F[i]["text"]
    eid = w.find_entity("权发遣三司度支判官公事", "官职"); assert eid
    tid = node(w, "权发遣三司度支判官公事", "北宋庆历三年五月十二日", "官职")[1]
    cite(w, "Timepoints", tid, i, F[i]["fields"]["职源"], "本条补证始置日期。")
    office = node(w, "度支", "北宋咸平六年", "机构")[1]
    rel(w, office, tid, "编制隶属", i, F[i]["fields"]["职源"],
        "权发遣三司度支判官公事属度支判官系统。", staff_type="官")
    w.commit()


def entry339():
    i = 339; hist = F[i]["fields"]["职源与沿革"]; duty = F[i]["fields"]["职掌"]
    w = W(i); eid = w.find_entity("三司户部判官", "官职"); assert eid
    early = node(w, "三司户部判官", "北宋太平兴国八年前", "官职")[1]
    stages = [
        tp(w, eid, "唐开元四年", "已有户部本判官之名，尚为判户部钱谷文案之意",
           i, hist, "财政判官", "建唐代源流节点。", chain="none"),
        tp(w, eid, "五代", "成为正式官名", i, hist, "财政判官", "建五代正式官名节点。", chain="none"),
        tp(w, eid, "宋初", "沿五代之制，每部判官一人", i, hist, "财政判官", "建宋初一员节点。", chain="none"),
        early,
        tp(w, eid, "北宋咸平六年后", "与户部副使通签本部诸案文书", i, duty,
           "财政判官", "建咸平六年后职掌节点。", chain="none"),
    ]
    chain(w, stages, "连接户部判官唐代源流、五代正式化及宋初职掌变化。")
    office_song = node(w, "户部", "宋初", "机构")[1]
    rel(w, office_song, stages[2], "编制隶属", i, hist, "宋初户部置判官一人。",
        staff_quota=1, staff_type="官")
    office_later = node(w, "户部", "北宋咸平六年", "机构")[1]
    rel(w, office_later, stages[-1], "编制隶属", i, duty, "咸平六年后户部判官与副使通签公事。", staff_type="官")
    w.commit()


def main():
    entry321(); entry322(); entry323(); entry324(); entry325(); entry326()
    entry327(); entry328(); entry329(); entry330(); entry331(); entry332()
    entry333(); entry334(); entry335(); entry336(); entry337(); entry338(); entry339()


if __name__ == "__main__":
    main()
