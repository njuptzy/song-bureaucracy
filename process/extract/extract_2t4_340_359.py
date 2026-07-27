#!/usr/bin/env python3
"""提取 chapter2t4 第340–359条：三司推巡官与三司二十四案。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get("SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db"))


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute("SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (i,)).fetchone()
    assert row, i
    fields = json.loads(row[3] or "{}")
    return {"title": row[0], "page": row[1], "text": row[2] or "", "fields": fields,
            "all": "\n".join([row[2] or ""] + [str(v) for k, v in fields.items() if not k.startswith("_")])}


F = {i: load(i) for i in range(340, 360)}


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
        w.relink(tid, decision, prev_id=tids[pos - 1] if pos else None,
                 succ_id=tids[pos + 1] if pos + 1 < len(tids) else None)


def insert_between(w, tid, prev_id, succ_id, decision):
    w.relink(prev_id, decision, succ_id=tid)
    w.relink(tid, decision, prev_id=prev_id, succ_id=succ_id)
    w.relink(succ_id, decision, prev_id=tid)


def entry340():
    i = 340; z = F[i]["text"]; w = W(i)
    eid = entity(w, "权三司户部判官", "官职", z, "切分修复后的正文明确为户部判官权任差遣。")
    tid = tp(w, eid, "宋代（未载具体年月）", "三司户部判官缺时由暂代者带“权”字",
             i, z, "财政判官", "建权三司户部判官概括节点。")
    office = node(w, "户部", "北宋咸平六年", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "权三司户部判官为户部判官的权任形态。", staff_type="官")
    w.commit()


def entry341():
    i = 341; w = W(i)
    eid = w.find_entity("权发遣三司户部公事", "官职"); assert eid
    tid = node(w, "权发遣三司户部公事", "北宋庆历三年五月十二日", "官职")[1]
    cite(w, "Timepoints", tid, i, F[i]["fields"]["职源"], "本条补证庆历三年始置。")
    office = node(w, "户部", "北宋咸平六年", "机构")[1]
    rel(w, office, tid, "编制隶属", i, F[i]["fields"]["职源"],
        "权发遣三司户部公事属户部判官系统。", staff_type="官")
    w.commit()


def add_department_timepoint(w, office, time, event, i, quotation):
    eid = w.find_entity(office, "机构"); assert eid
    tid = tp(w, eid, time, event, i, quotation, "财政机构", f"补建{office}{time}编制节点。", chain="none")
    prev = node(w, office, "宋初", "机构")[1]
    succ = node(w, office, "北宋太平兴国八年三月七日", "机构")[1]
    insert_between(w, tid, prev, succ, f"把{time}节点按年代插入{office}时间链。")
    return tid


def entry342():
    i = 342; z = F[i]["text"]; hist = F[i]["fields"]["职源与沿革"]
    comp = F[i]["fields"]["编制"]; duty = F[i]["fields"]["职掌"]
    w = W(i)
    total_e = entity(w, "三司推官", "官职", z, "原文明载为三部推官及盐铁胄案推官总名。")
    a = tp(w, total_e, "五代后晋", "已见置", i, hist, "财政推官合称", "建五代始见节点。", chain="none")
    b = tp(w, total_e, "北宋乾德四年", "三部各置推官一人", i, hist, "财政推官合称", "建乾德四年节点。", chain="none")
    c = tp(w, total_e, "北宋太平兴国三年", "户部税案、盐铁胄案各增推官一人，总数五人",
           i, comp, "财政推官合称", "建太平兴国三年五员节点。", chain="none")
    d = tp(w, total_e, "北宋真宗朝以后", "罕置", i, hist, "财政推官合称", "建真宗以后罕置节点。", chain="none")
    chain(w, [a, b, c, d], "连接三司推官五代始见、北宋编制与罕置节点。")
    cite(w, "Timepoints", b, i, duty, "补充督察吏人与处理违纪公事职掌。", note="职掌")
    dept_tps = {office: add_department_timepoint(w, office, "北宋乾德四年", "置本部推官一人", i, hist)
                for office in ("盐铁", "度支", "户部")}
    base = (("三司盐铁推官", "盐铁"), ("三司度支推官", "度支"), ("三司户部推官", "户部"))
    for title, office in base:
        eid = entity(w, title, "官职", z, f"三司推官总名明确列出{title}。")
        tid = tp(w, eid, "北宋乾德四年", "本部置推官一人", i, hist,
                 "财政推官", f"建{title}乾德四年节点。")
        rel(w, b, tid, "统称与实例", i, z, f"三司推官包括{title}。")
        rel(w, dept_tps[office], tid, "编制隶属", i, hist, f"{office}置推官一人。",
            staff_quota=1, staff_type="官")
    for title, office in (("户部税案推官", "户部"), ("盐铁胄案推官", "盐铁")):
        eid = entity(w, title, "官职", comp, f"太平兴国三年增设{title}一人。")
        tid = tp(w, eid, "北宋太平兴国三年", "增设一人", i, comp,
                 "财政推官", f"建{title}增设节点。")
        rel(w, c, tid, "统称与实例", i, comp, f"三司推官五员编制包括{title}。")
        rel(w, dept_tps[office], tid, "编制隶属", i, comp, f"{office}增设{title}一人。",
            staff_quota=1, staff_type="官")
    w.commit()


def entry343():
    i = 343; z = F[i]["text"]; hist = F[i]["fields"]["职源与沿革"]
    comp = F[i]["fields"]["编制"]; duty = F[i]["fields"]["职掌"]
    w = W(i)
    total_e = entity(w, "三司巡官", "官职", z, "原文明载为盐铁、度支、户部巡官总名。")
    a = tp(w, total_e, "唐元和六年", "户部始置户部巡官", i, hist,
           "财政巡官合称", "建唐代源流节点。", chain="none")
    b = tp(w, total_e, "五代", "三司沿置巡官", i, hist,
           "财政巡官合称", "建五代沿置节点。", chain="none")
    c = tp(w, total_e, "北宋太平兴国三年十二月二十八日", "始置三部巡官",
           i, hist, "财政巡官合称", "建北宋始置节点。", chain="none")
    chain(w, [a, b, c], "连接三司巡官唐代源流、五代沿置与北宋始置。")
    cite(w, "Timepoints", c, i, duty, "补充督察本部吏人职掌。", note="职掌")
    generic = (("三司盐铁巡官", "盐铁"), ("三司度支巡官", "度支"), ("三司户部巡官", "户部"))
    nodes = {}
    for title, office in generic:
        eid = entity(w, title, "官职", z, f"三司巡官总名明确列出{title}。")
        tid = tp(w, eid, "北宋太平兴国三年十二月二十八日", "本部巡官",
                 i, hist, "财政巡官", f"建{title}始置节点。")
        nodes[title] = tid
        rel(w, c, tid, "统称与实例", i, z, f"三司巡官包括{title}。")
        office_tp = node(w, office, "北宋乾德四年", "机构")[1]
        rel(w, office_tp, tid, "编制隶属", i, z, f"{title}属{office}。", staff_type="官")
    for title, parent, office in (("盐铁末盐案巡官", "三司盐铁巡官", "盐铁"),
                                  ("户部曲案巡官", "三司户部巡官", "户部")):
        eid = entity(w, title, "官职", z, f"三司巡官条明确列出具体巡官{title}。")
        tid = tp(w, eid, "北宋太平兴国三年十二月二十八日", "本部巡官一人",
                 i, comp, "财政巡官", f"建{title}一员节点。")
        rel(w, nodes[parent], tid, "统称与实例", i, z, f"{parent}包括{title}。")
        office_tp = node(w, office, "北宋乾德四年", "机构")[1]
        rel(w, office_tp, tid, "编制隶属", i, comp, f"{office}置{title}一人。",
            staff_quota=1, staff_type="官")
    degree_tid = nodes["三司度支巡官"]
    degree_office = node(w, "度支", "北宋乾德四年", "机构")[1]
    rid = w.relationship(degree_office, degree_tid, "编制隶属", "度支巡官一人。", comp,
                         staff_quota=1, staff_type="官")
    cite(w, "Relationships", rid, i, comp, "补充度支巡官一人员额。")
    w.commit()


def entry344():
    i = 344; z = F[i]["text"]; w = W(i)
    total_e = entity(w, "三司二十四案", "机构", z, "辞典明载三司分案治事，宋初共二十四案。")
    stages = [
        tp(w, total_e, "宋初", "三司分二十四案治事", i, z, "财政办事机构合称", "建宋初二十四案节点。", chain="none"),
        tp(w, total_e, "北宋乾德五年", "三部各领八案", i, z, "财政办事机构合称", "建乾德五年分领节点。", chain="none"),
        tp(w, total_e, "北宋咸平四年", "合并夏秋税案、东西上供案，并省竹木案与仓案", i, z,
           "财政办事机构合称", "建咸平四年并案节点。", chain="none"),
        tp(w, total_e, "北宋大中祥符七年", "新设常平案，其后三部定二十一案", i, z,
           "财政办事机构合称", "建大中祥符七年二十一案节点。", chain="none"),
    ]
    chain(w, stages, "连接三司案制二十四案、分领、并案与二十一案节点。")
    tri = node(w, "三司", "宋初", "机构")[1]
    rel(w, tri, stages[0], "上下级机构", i, z, "三司以二十四案分治事务。")
    names = ("兵刑案", "胄案", "铁案", "商税案", "茶案", "课盐案", "末盐案", "设案",
             "赏给案", "钱案", "发运案", "百官案", "斛米案", "粮料案", "骑案", "夏税案",
             "秋税案", "东上供案", "西上供案", "修造案", "竹木案", "曲案", "衣粮案", "仓案")
    nodes = {}
    for title in names:
        eid = entity(w, title, "机构", z, f"二十四案名单明确列{title}。")
        tid = tp(w, eid, "宋初", "三司二十四案之一", i, z,
                 "财政办事机构", f"建{title}宋初节点。")
        nodes[title] = tid
        rel(w, stages[0], tid, "统称与实例", i, z, f"三司二十四案包括{title}。")
    for sources, target in (("夏税案 秋税案", "户税案"), ("东上供案 西上供案", "上供案")):
        target_e = entity(w, target, "机构", z, f"咸平四年由{sources}合并为{target}。")
        target_t = tp(w, target_e, "北宋咸平四年", f"由{sources}合并而成", i, z,
                      "财政办事机构", f"建{target}合并节点。")
        for source in sources.split():
            source_e = w.find_entity(source, "机构"); assert source_e
            end = tp(w, source_e, "北宋咸平四年", f"并入{target}", i, z,
                     "财政办事机构", f"建{source}并案节点。")
            rel(w, end, target_t, "前后演变", i, z, f"{source}并为{target}。")
    for source, target in (("竹木案", "修造案"), ("仓案", "衣粮案")):
        source_e = w.find_entity(source, "机构"); target_e = w.find_entity(target, "机构")
        end = tp(w, source_e, "北宋咸平四年", f"并入{target}", i, z,
                 "财政办事机构", f"建{source}并省节点。")
        receive = tp(w, target_e, "北宋咸平四年", f"兼并{source}", i, z,
                     "财政办事机构", f"建{target}兼并节点。")
        rel(w, end, receive, "前后演变", i, z, f"{source}并入{target}。")
    cp_e = entity(w, "常平案", "机构", z, "大中祥符七年新设常平案。")
    cp_t = tp(w, cp_e, "北宋大中祥符七年", "新设", i, z,
              "财政办事机构", "建常平案始置节点。")
    rel(w, stages[3], cp_t, "统称与实例", i, z, "三司二十一案包括新设常平案。")
    w.commit()


def entry345():
    i = 345; z = F[i]["text"]; w = W(i)
    group_e = entity(w, "三司盐铁诸案", "机构", z, "辞典明载为盐铁部所领办事机构。")
    stages = [
        tp(w, group_e, "宋初", "盐铁部诸案已置", i, z, "财政办事机构合称", "建宋初节点。", chain="none"),
        tp(w, group_e, "北宋乾德五年", "定兵刑、胄、铁、商税、茶、盐、末盐、设八案", i, z,
           "财政办事机构合称", "建乾德五年八案节点。", chain="none"),
        tp(w, group_e, "北宋真宗朝", "定八案，由三员判官分领", i, z,
           "财政办事机构合称", "建真宗朝编制节点。", chain="none"),
        tp(w, group_e, "北宋元丰改制", "诸案罢", i, z,
           "财政办事机构合称", "建元丰罢置节点。", chain="none"),
    ]
    chain(w, stages, "连接盐铁诸案宋初、乾德、真宗与元丰节点。")
    salt = node(w, "盐铁", "宋初", "机构")[1]
    rel(w, salt, stages[0], "上下级机构", i, z, "三司盐铁诸案为盐铁部所领办事机构。")
    # “盐/税盐”具体规范名由紧邻的“颗盐案”条直接建立，避免在总条中替 OCR 猜名。
    names = ("兵刑案", "胄案", "铁案", "商税案", "茶案", "末盐案", "设案")
    for title in names:
        eid = w.find_entity(title, "机构") or entity(w, title, "机构", z, f"盐铁八案名单明确列{title}。")
        tid = w.find_timepoint(eid, "宋初") or tp(w, eid, "宋初", "盐铁部所领办事机构", i, z,
                                                   "财政办事机构", f"建{title}宋初节点。")
        cite(w, "Timepoints", tid, i, z, f"盐铁诸案条补证{title}属盐铁部。")
        rel(w, stages[0], tid, "统称与实例", i, z, f"三司盐铁诸案包括{title}。")
    salt_e = w.find_entity("盐铁", "机构")
    salt_end = tp(w, salt_e, "北宋元丰改制", "盐铁诸案统罢", i, z,
                  "财政机构", "补建盐铁诸案罢置节点。")
    w.commit()


def simple_case(i, title, group, time="宋初"):
    z = F[i]["text"]; w = W(i)
    eid = w.find_entity(title, "机构") or entity(w, title, "机构", z, f"本条明载{title}为三司办事机构。")
    tid = w.find_timepoint(eid, time) or tp(w, eid, time, f"{group}所属办事机构", i, z,
                                            "财政办事机构", f"建{title}{time}节点。")
    cite(w, "Timepoints", tid, i, z, f"本条补充{title}隶属和职掌。", note="职掌")
    group_tp = node(w, group, "宋初", "机构")[1]
    rel(w, group_tp, tid, "统称与实例", i, z, f"{title}为{group}实例。")
    w.commit()


def entry346(): simple_case(346, "兵刑案", "三司盐铁诸案")


def entry347():
    i = 347; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("胄案", "机构"); assert eid
    start = node(w, "胄案", "宋初", "机构")[1]
    cite(w, "Timepoints", start, i, z, "本条补充胄案隶属、职掌及皇祐三年前河渠职事。", note="职掌")
    end = tp(w, eid, "北宋熙宁六年六月二十七日", "废罢，改为军器监", i, z,
             "财政办事机构", "建胄案废罢节点。")
    arm_e = entity(w, "军器监", "机构", z, "原文明载胄案废罢后改为军器监。")
    arm_t = tp(w, arm_e, "北宋熙宁六年六月二十七日", "由胄案改置", i, z,
               "军器机构", "建军器监承接节点。")
    rel(w, end, arm_t, "前后演变", i, z, "胄案废罢，改为军器监。")
    w.commit()


def entry348(): simple_case(348, "铁案", "三司盐铁诸案")
def entry349(): simple_case(349, "商税案", "三司盐铁诸案")
def entry350(): simple_case(350, "茶案", "三司盐铁诸案")
def entry351(): simple_case(351, "设案", "三司盐铁诸案")
def entry352(): simple_case(352, "颗盐案", "三司盐铁诸案")
def entry353(): simple_case(353, "末盐案", "三司盐铁诸案")


def entry354():
    i = 354; z = F[i]["text"]; w = W(i)
    target_e = entity(w, "都盐案", "机构", z, "原文明载由颗盐案与末盐案合并而成。")
    target_t = tp(w, target_e, "宋代（未载具体年月）", "由颗盐案、末盐案合并，统掌榷盐",
                  i, z, "财政办事机构", "建都盐案合并节点。")
    for source in ("颗盐案", "末盐案"):
        source_e = w.find_entity(source, "机构"); assert source_e
        end = tp(w, source_e, "宋代（未载具体年月）", "合并为都盐案", i, z,
                 "财政办事机构", f"建{source}合并节点。")
        rel(w, end, target_t, "前后演变", i, z, f"{source}合并为都盐案。")
    w.commit()


def entry355():
    i = 355; z = F[i]["text"]; w = W(i)
    group_e = entity(w, "三司度支诸案", "机构", z, "标题及所列八案表明为度支部诸案；正文首句OCR作盐铁部，保留冲突。")
    song = tp(w, group_e, "宋初", "除常平案外其余诸案已置", i, z,
              "财政办事机构合称", "建宋初节点。", chain="none")
    daxiang = tp(w, group_e, "北宋大中祥符七年", "定八案，由三员判官分领", i, z,
                 "财政办事机构合称", "建大中祥符七年八案节点。", chain="none")
    end = tp(w, group_e, "北宋元丰改制", "诸案统罢", i, z,
             "财政办事机构合称", "建元丰罢置节点。", chain="none")
    chain(w, [song, daxiang, end], "连接度支诸案宋初、大中祥符与元丰节点。")
    degree_e = w.find_entity("度支", "机构"); assert degree_e
    degree_tp = tp(w, degree_e, "北宋大中祥符七年", "度支诸案定为八案", i, z,
                   "财政机构", "补建度支八案编制节点。")
    rid = w.relationship(degree_tp, daxiang, "上下级机构", "三司度支诸案隶度支。", z)
    cite(w, "Relationships", rid, i, z, "据标题、所列案名和后续各案条建立度支隶属；保留正文首句OCR冲突。",
         conflict_flag=1, note="本条标题为‘三司度支诸案’，后列度支八案，但正文首句OCR作‘盐铁部所领’。")
    names = ("赏给案", "钱帛案", "发运案", "斛斗案", "百官案", "粮料案", "常平案", "骑案")
    for title in names:
        eid = w.find_entity(title, "机构") or entity(w, title, "机构", z, f"度支八案名单明确列{title}。")
        time = "北宋大中祥符七年" if title == "常平案" else "宋初"
        tid = w.find_timepoint(eid, time) or tp(w, eid, time, "度支部所领办事机构", i, z,
                                                "财政办事机构", f"建{title}{time}节点。")
        cite(w, "Timepoints", tid, i, z, f"度支诸案条补证{title}为八案之一。")
        rel(w, daxiang, tid, "统称与实例", i, z, f"三司度支诸案包括{title}。")
    w.commit()


def entry356(): simple_case(356, "赏给案", "三司度支诸案")
def entry357(): simple_case(357, "钱帛案", "三司度支诸案")
def entry358(): simple_case(358, "粮料案", "三司度支诸案")


def entry359():
    i = 359; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("常平案", "机构"); assert eid
    tid = node(w, "常平案", "北宋大中祥符七年", "机构")[1]
    cite(w, "Timepoints", tid, i, z, "本条直接补证常平案始置、隶属与平籴职掌。", note="职掌")
    group = node(w, "三司度支诸案", "北宋大中祥符七年", "机构")[1]
    rel(w, group, tid, "统称与实例", i, z, "常平案为度支八案之一。")
    w.commit()


def main():
    entry340(); entry341(); entry342(); entry343(); entry344(); entry345()
    entry346(); entry347(); entry348(); entry349(); entry350(); entry351()
    entry352(); entry353(); entry354(); entry355(); entry356(); entry357()
    entry358(); entry359()


if __name__ == "__main__":
    main()
