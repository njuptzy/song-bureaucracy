#!/usr/bin/env python3
"""提取 chapter2t4 第360–379条：度支、户部诸案与三部勾院。"""
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
    return {"title": row[0], "page": row[1], "text": row[2] or "",
            "fields": json.loads(row[3] or "{}")}


F = {i: load(i) for i in range(360, 380)}


def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])
def C(i): return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'


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


def entity(w, title, type_, quotation, decision):
    return w.entity(title, type_, decision, quotation=quotation)


def node(w, title, time, type_=None):
    eid = w.find_entity(title, type_); assert eid, f"缺实体：{title}"
    tid = w.find_timepoint(eid, time); assert tid, f"{title}缺时间点：{time}"
    return eid, tid


def chain(w, tids, decision):
    assert len(tids) == len(set(tids)), tids
    for pos, tid in enumerate(tids):
        w.relink(tid, decision,
                 prev_id=tids[pos - 1] if pos else None,
                 succ_id=tids[pos + 1] if pos + 1 < len(tids) else None)


def chain_times(w, eid, times, decision):
    tids = []
    for time in times:
        tid = w.find_timepoint(eid, time)
        assert tid, (eid, time)
        tids.append(tid)
    chain(w, tids, decision)


def entry360_363():
    for i in range(360, 364):
        z = F[i]["text"]; title = F[i]["title"]; w = W(i)
        eid, tid = node(w, title, "宋初", "机构")
        cite(w, "Timepoints", tid, i, z, f"本条补证{title}隶属度支及具体职掌。", note="职掌")
        degree = node(w, "度支", "宋初", "机构")[1]
        rel(w, degree, tid, "上下级机构", i, z, f"原文明载{title}隶三司度支部。")
        w.commit()


def ensure_hubu_daxiang(w, i, quotation):
    eid = w.find_entity("户部", "机构"); assert eid
    tid = w.find_timepoint(eid, "北宋大中祥符七年以后")
    if not tid:
        tid = tp(w, eid, "北宋大中祥符七年以后", "户部五案编制定型", i, quotation,
                 "财政机构", "据户部诸案条补建户部五案定制节点。", chain="none")
        chain_times(w, eid, ["唐贞元四年", "宋初", "北宋乾德四年", "北宋太平兴国八年三月七日",
                             "北宋淳化四年五月二十一日", "北宋淳化五年十二月二十四日",
                             "北宋咸平六年", "北宋大中祥符七年以后", "北宋元丰五年五月"],
                    "按历史顺序插入户部五案定制节点。")
    return tid


def entry364():
    i = 364; z = F[i]["text"]; w = W(i)
    group_e = entity(w, "三司户部诸案", "机构", z, "原文明载户部所领五个吏人办事机构。")
    group_t = tp(w, group_e, "北宋大中祥符七年以后", "定为五案，由三员判官分领",
                 i, z, "财政办事机构合称", "建户部五案定制节点。")
    hubu_t = ensure_hubu_daxiang(w, i, z)
    rel(w, hubu_t, group_t, "上下级机构", i, z, "三司户部诸案为户部所领办事机构。")

    cases = ("两税案", "曲案", "上供案", "修造案", "衣粮案")
    case_tids = {}
    for title in cases:
        eid = w.find_entity(title, "机构") or entity(w, title, "机构", z, f"五案名单明确列有{title}。")
        tid = w.find_timepoint(eid, "北宋大中祥符七年以后")
        if not tid:
            tid = tp(w, eid, "北宋大中祥符七年以后", "列入户部五案",
                     i, z, "财政办事机构", f"建{title}列入户部五案节点。", chain="none")
            older = {
                "曲案": ["宋初"],
                "上供案": ["北宋咸平四年"],
                "修造案": ["宋初", "北宋咸平四年"],
                "衣粮案": ["宋初", "北宋咸平四年"],
            }.get(title, [])
            chain_times(w, eid, older + ["北宋大中祥符七年以后"],
                        f"连接{title}既有沿革与户部五案节点。")
        case_tids[title] = tid
        rel(w, group_t, tid, "统称与实例", i, z, f"五案名单明确包括{title}。")

    officer_e = w.find_entity("三司户部判官", "官职"); assert officer_e
    officer_t = w.find_timepoint(officer_e, "北宋大中祥符七年以后")
    if not officer_t:
        officer_t = tp(w, officer_e, "北宋大中祥符七年以后", "三员分领户部五案",
                       i, z, "财政判官", "建户部判官分领五案节点。", chain="none")
        chain_times(w, officer_e, ["唐开元四年", "五代", "宋初", "北宋太平兴国八年前",
                                   "北宋咸平六年后", "北宋大中祥符七年以后"],
                    "连接三司户部判官编制变化。")
    rel(w, group_t, officer_t, "编制隶属", i, z, "五案由三员判官分领。",
        staff_quota=3, staff_type="官")
    w.commit()


def entry365():
    i = 365; z = F[i]["text"]; w = W(i)
    eid, tid = node(w, "两税案", "北宋大中祥符七年以后", "机构")
    cite(w, "Timepoints", tid, i, z, "本条补证两税案职掌。", note="职掌")
    hubu_t = node(w, "户部", "北宋大中祥符七年以后", "机构")[1]
    rel(w, hubu_t, tid, "上下级机构", i, z, "原文明载两税案隶三司户部。")
    bureau_e = entity(w, "斗秤务", "机构", z, "原文明载两税案所辖司局有斗秤务。")
    bureau_t = tp(w, bureau_e, "北宋大中祥符七年以后", "为两税案所辖司局",
                  i, z, "税务机构", "建斗秤务隶属节点。")
    rel(w, tid, bureau_t, "上下级机构", i, z, "两税案所辖司局有斗秤务。")
    w.commit()


def entry366_368():
    for i in range(366, 369):
        z = F[i]["text"]; title = F[i]["title"]; w = W(i)
        _, tid = node(w, title, "北宋大中祥符七年以后", "机构")
        cite(w, "Timepoints", tid, i, z, f"本条补证{title}隶属与职掌。", note="职掌")
        hubu_t = node(w, "户部", "北宋大中祥符七年以后", "机构")[1]
        rel(w, hubu_t, tid, "上下级机构", i, z, f"原文明载{title}隶三司户部。")
        w.commit()


def entry369():
    i = 369; z = F[i]["text"]; w = W(i)
    eid = entity(w, "衣料案", "机构", z, "本条标题与正文明确为衣料案；不与总条所列衣粮案擅自合并。")
    tid = tp(w, eid, "宋代（未载具体年月）", "隶三司户部，掌衣粮等发放额审核",
             i, z, "财政办事机构", "建衣料案无确年节点。")
    hubu_t = node(w, "户部", "宋初", "机构")[1]
    rel(w, hubu_t, tid, "上下级机构", i, z, "原文明载衣料案隶三司户部。")
    w.commit()


def entry370():
    i = 370; z = F[i]["text"]; w = W(i)
    eid = entity(w, "勾当修造案公事", "官职", z, "原文明载为修造案临时差遣。")
    start = tp(w, eid, "北宋嘉祐二年十月二十三日", "因水灾后突击修治临时设置",
               i, z, "临时差遣", "建临时设置节点。", attr_officer_type="朝官", chain="none")
    end = tp(w, eid, "修理工程完毕", "随工程完毕即罢",
             i, z, "临时差遣", "建工程完毕罢差节点。", attr_officer_type="朝官", chain="none")
    chain(w, [start, end], "连接勾当修造案公事设置、罢止节点。")
    repair_e = w.find_entity("修造案", "机构"); assert repair_e
    repair_t = w.find_timepoint(repair_e, "北宋大中祥符七年以后"); assert repair_t
    rel(w, repair_t, start, "编制隶属", i, z, "勾当修造案公事为修造案专职临时官。", staff_type="官")
    w.commit()


SPECIFIC_OFFICES = ("三司盐铁勾院", "三司度支勾院", "三司户部勾院")
SPECIFIC_POSTS = ("判三司盐铁勾院公事", "判三司度支勾院公事", "判三司户部勾院公事")


def seed_specific_entities():
    for i, office, post in zip((374, 376, 378), SPECIFIC_OFFICES, SPECIFIC_POSTS):
        z = F[i]["text"]; w = W(i)
        entity(w, office, "机构", z, f"本条明载{office}为官司。")
        w.commit()
        pi = i + 1; pz = F[pi]["text"]; w = W(pi)
        entity(w, post, "官职", pz, f"本条明载{post}为勾院主判官差遣。")
        w.commit()


def upgrade_sansi_gouyuan(w, quotation):
    eid = w.find_entity("三司勾院", "机构"); assert eid
    old = w.find_timepoint(eid, "宋代（未载具体年月）")
    if old:
        w.conn.execute("UPDATE Timepoints SET time=?,event=?,quotation=? WHERE id=?",
                       ("北宋太平兴国五年十月", "三部勾院合而为一", quotation, old))
        w._br("Timepoints", old, "勾院条给出确切时间，将原无确年节点改为太平兴国五年十月。")
    return eid


def add_history_tp(w, eid, time, event, quotation):
    return tp(w, eid, time, event, 371, quotation, "财政勾稽机构", f"据勾院沿革建{time}节点。", chain="none")


def entry371():
    i = 371; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; duty = F[i]["fields"]["职掌"]
    w = W(i)
    generic_e = entity(w, "勾院", "机构", z, "正文定义勾院为三司子司。")
    generic_t = tp(w, generic_e, "宋初", "三司三部各置勾院，掌帐籍勾销与纠察",
                   i, h, "财政勾稽机构", "建勾院宋初制度节点。")
    cite(w, "Timepoints", generic_t, i, duty, "补充勾院职掌。", note="职掌")

    ids = {name: w.find_entity(name, "机构") for name in SPECIFIC_OFFICES}
    assert all(ids.values())
    combo_e = entity(w, "盐铁、户部勾院", "机构", h, "开宝五年盐铁、户部二勾院合并后的机构。")
    sansi_gou_e = upgrade_sansi_gouyuan(w, h)
    all_e = entity(w, "三司都勾院", "机构", h, "原文明载三部勾院多次合为三司都勾院。")
    left_e = entity(w, "左计勾院", "机构", h, "原文明载总计司时期置左计勾院。")
    right_e = entity(w, "右计勾院", "机构", h, "原文明载总计司时期置右计勾院。")

    # 三部各院的分合节点。
    times = [
        ("宋初", "三司三部各置勾院"),
        ("北宋开宝五年十二月", "盐铁、户部勾院合并；度支勾院仍为一院"),
        ("北宋太平兴国五年十月", "三部勾院合而为一"),
        ("北宋雍熙三年八月", "由合一勾院复分为三部勾院"),
        ("北宋淳化三年七月一日", "三部勾院合为三司都勾院"),
        ("北宋淳化四年五月", "三司都勾院复分为三部勾院"),
        ("北宋淳化四年十月", "三部勾院改为左、右计勾院"),
        ("北宋淳化五年十二月二十五日", "左、右计勾院复分为三部勾院"),
        ("北宋至道二年十月二十七日", "三部勾院复并为三司都勾院"),
        ("北宋至道三年十一月五日", "三司都勾院复分为三部勾院"),
        ("北宋咸平六年七月十六日", "三部勾院合为一院"),
        ("北宋熙宁七年", "三部勾院又合为三司都勾院（此前复分时间未载）"),
    ]
    specific_t = {name: {} for name in SPECIFIC_OFFICES}
    for name in SPECIFIC_OFFICES:
        for time, event in times:
            actual_event = event
            if time == "北宋开宝五年十二月" and name == "三司度支勾院":
                actual_event = "盐铁、户部勾院合并，本院仍为一院"
            specific_t[name][time] = add_history_tp(w, ids[name], time, actual_event, h)
        chain(w, [specific_t[name][time] for time, _ in times], f"连接{name}分合沿革链。")

    combo_start = add_history_tp(w, combo_e, "北宋开宝五年十二月", "由盐铁、户部二勾院合并", h)
    combo_end = add_history_tp(w, combo_e, "北宋太平兴国五年十月", "并入三司勾院", h)
    chain(w, [combo_start, combo_end], "连接盐铁、户部勾院合并与终结节点。")

    sansi_start = w.find_timepoint(sansi_gou_e, "北宋太平兴国五年十月"); assert sansi_start
    cite(w, "Timepoints", sansi_start, i, h, "补证三司勾院合置时间。")
    sansi_end = add_history_tp(w, sansi_gou_e, "北宋雍熙三年八月", "复分为三部勾院", h)
    sansi_start2 = add_history_tp(w, sansi_gou_e, "北宋咸平六年七月十六日", "三部勾院合为一院", h)
    chain(w, [sansi_start, sansi_end, sansi_start2], "连接三司勾院两次合置沿革。")

    all_nodes = []
    for time, event in (("北宋淳化三年七月一日", "三部勾院合置"),
                        ("北宋淳化四年五月", "复分为三部勾院"),
                        ("北宋至道二年十月二十七日", "三部勾院复并"),
                        ("北宋至道三年十一月五日", "复分为三部勾院"),
                        ("北宋熙宁七年", "三部勾院又合置")):
        all_nodes.append(add_history_tp(w, all_e, time, event, h))
    chain(w, all_nodes, "连接三司都勾院合分沿革。")

    left_start = add_history_tp(w, left_e, "北宋淳化四年十月", "由三部勾院改置", h)
    left_end = add_history_tp(w, left_e, "北宋淳化五年十二月二十五日", "罢并复分三部勾院", h)
    chain(w, [left_start, left_end], "连接左计勾院置罢节点。")
    right_start = add_history_tp(w, right_e, "北宋淳化四年十月", "由三部勾院改置", h)
    right_end = add_history_tp(w, right_e, "北宋淳化五年十二月二十五日", "罢并复分三部勾院", h)
    chain(w, [right_start, right_end], "连接右计勾院置罢节点。")

    three_e = entity(w, "三部勾院", "机构", h, "沿革字段以三部勾院指盐铁、度支、户部三院合称。")
    three_yong = add_history_tp(w, three_e, "北宋雍熙三年八月", "复分为盐铁、度支、户部三勾院", h)
    three_oct = add_history_tp(w, three_e, "北宋淳化四年十月", "罢为左计勾院、右计勾院", h)
    three_dec = add_history_tp(w, three_e, "北宋淳化五年十二月二十五日", "由左、右计勾院复分", h)
    chain(w, [three_yong, three_oct, three_dec], "连接三部勾院复分、改为左右计及再复分节点。")

    # 分合关系。
    salt, degree, house = SPECIFIC_OFFICES
    rel(w, specific_t[salt]["北宋开宝五年十二月"], combo_start, "前后演变", i, h, "盐铁勾院并入盐铁、户部勾院。")
    rel(w, specific_t[house]["北宋开宝五年十二月"], combo_start, "前后演变", i, h, "户部勾院并入盐铁、户部勾院。")
    rel(w, combo_end, sansi_start, "前后演变", i, h, "盐铁、户部勾院并入三司勾院。")
    rel(w, specific_t[degree]["北宋太平兴国五年十月"], sansi_start, "前后演变", i, h, "度支勾院并入三司勾院。")

    for name in SPECIFIC_OFFICES:
        rel(w, sansi_end, specific_t[name]["北宋雍熙三年八月"], "前后演变", i, h, f"三司勾院复分为{name}。")
        rel(w, specific_t[name]["北宋淳化三年七月一日"], all_nodes[0], "前后演变", i, h, f"{name}并入三司都勾院。")
        rel(w, all_nodes[1], specific_t[name]["北宋淳化四年五月"], "前后演变", i, h, f"三司都勾院复分为{name}。")
        rel(w, specific_t[name]["北宋至道二年十月二十七日"], all_nodes[2], "前后演变", i, h, f"{name}并入三司都勾院。")
        rel(w, all_nodes[3], specific_t[name]["北宋至道三年十一月五日"], "前后演变", i, h, f"三司都勾院复分为{name}。")
        rel(w, specific_t[name]["北宋咸平六年七月十六日"], sansi_start2, "前后演变", i, h, f"{name}合为一院。")
        rel(w, specific_t[name]["北宋熙宁七年"], all_nodes[4], "前后演变", i, h, f"{name}又合为三司都勾院。")
        rel(w, three_oct, specific_t[name]["北宋淳化四年十月"], "统称与实例", i, h, f"三部勾院在改制前包括{name}。")
        rel(w, three_dec, specific_t[name]["北宋淳化五年十二月二十五日"], "统称与实例", i, h, f"复分后的三部勾院包括{name}。")
    rel(w, three_oct, left_start, "前后演变", i, h, "三部勾院改为左计勾院。")
    rel(w, three_oct, right_start, "前后演变", i, h, "三部勾院改为右计勾院。")
    rel(w, left_end, three_dec, "前后演变", i, h, "左计勾院罢后复分三部勾院。")
    rel(w, right_end, three_dec, "前后演变", i, h, "右计勾院罢后复分三部勾院。")

    # 三司为各勾院的上级；为关系事实补建同日的三司状态节点。
    parent_e = w.find_entity("三司", "机构"); assert parent_e
    parent_times = ["北宋开宝五年十二月", "北宋太平兴国五年十月", "北宋雍熙三年八月",
                    "北宋淳化三年七月一日", "北宋淳化四年五月", "北宋淳化四年十月",
                    "北宋淳化五年十二月二十五日", "北宋至道二年十月二十七日",
                    "北宋至道三年十一月五日", "北宋咸平六年七月十六日", "北宋熙宁七年"]
    parent = {}
    for time in parent_times:
        parent[time] = add_history_tp(w, parent_e, time, "所属勾院编制发生合分变化", h)
    chain_times(w, parent_e, ["唐天祐三年三月", "宋初", "北宋开宝五年十二月",
                              "北宋太平兴国五年十月", "北宋太平兴国八年三月七日",
                              "北宋雍熙三年八月", "北宋淳化三年七月一日",
                              "北宋淳化四年五月", "北宋淳化四年五月二十一日",
                              "北宋淳化四年十月", "北宋淳化五年十二月二十五日",
                              "北宋至道二年十月二十七日",
                              "北宋至道三年十一月五日", "北宋咸平六年",
                              "北宋咸平六年七月十六日", "北宋熙宁七年", "北宋元丰五年五月"],
                "按历史顺序插入三司所属勾院合分节点。")
    parent_song = node(w, "三司", "宋初", "机构")[1]
    for name in SPECIFIC_OFFICES:
        rel(w, parent_song, specific_t[name]["宋初"], "上下级机构", i, h, f"宋初{name}为三司子司。")
    rel(w, parent["北宋开宝五年十二月"], combo_start, "上下级机构", i, h, "盐铁、户部勾院为三司子司。")
    rel(w, parent["北宋太平兴国五年十月"], sansi_start, "上下级机构", i, h, "三司勾院为三司子司。")
    rel(w, parent["北宋淳化三年七月一日"], all_nodes[0], "上下级机构", i, h, "三司都勾院为三司子司。")
    rel(w, parent["北宋淳化四年十月"], left_start, "上下级机构", i, h, "左计勾院为三司改制时期子司。")
    rel(w, parent["北宋淳化四年十月"], right_start, "上下级机构", i, h, "右计勾院为三司改制时期子司。")
    rel(w, parent["北宋至道二年十月二十七日"], all_nodes[2], "上下级机构", i, h, "三司都勾院为三司子司。")
    rel(w, parent["北宋咸平六年七月十六日"], sansi_start2, "上下级机构", i, h, "合一勾院为三司子司。")
    rel(w, parent["北宋熙宁七年"], all_nodes[4], "上下级机构", i, h, "熙宁七年三司都勾院为三司子司。")
    w.commit()


def entry372():
    i = 372; z = F[i]["text"]; w = W(i)
    eid = entity(w, "三部勾院", "机构", z, "原文明确为盐铁、度支、户部三勾院合称。")
    tid = tp(w, eid, "北宋雍熙三年八月", "盐铁、度支、户部三勾院合称",
             i, z, "财政勾稽机构合称", "建三部勾院合称节点。")
    for title in SPECIFIC_OFFICES:
        child = node(w, title, "北宋雍熙三年八月", "机构")[1]
        rel(w, tid, child, "统称与实例", i, z, f"三部勾院包括{title}。")
    w.commit()


def entry373():
    i = 373; z = F[i]["text"]; w = W(i)
    eid = entity(w, "三部勾院判勾官", "官职", z, "原文明载为三部勾院判勾官合称。")
    tid = tp(w, eid, "北宋淳化四年五月", "三部勾院置判勾官一员、判官一员",
             i, z, "财政勾稽官合称", "建三部勾院判勾官编制节点。")
    for title in SPECIFIC_POSTS:
        pe = w.find_entity(title, "官职"); assert pe
        pt = tp(w, pe, "北宋淳化四年五月", "任本部勾院主判官",
                i, z, "财政勾稽差遣", f"据合称条建{title}制度节点。")
        rel(w, tid, pt, "统称与实例", i, z, f"三部勾院判勾官合称包括{title}。")
    w.commit()


def specific_office_entry(i, office, post):
    z = F[i]["text"]; comp = F[i]["fields"]["编制"]; w = W(i)
    office_t = node(w, office, "北宋淳化四年五月", "机构")[1]
    cite(w, "Timepoints", office_t, i, z, f"本条补证{office}为三司属司。")
    post_t = node(w, post, "北宋淳化四年五月", "官职")[1]
    rel(w, office_t, post_t, "编制隶属", i, comp, f"{office}置主判官一人。",
        staff_quota=1, staff_type="官")
    clerk_e = w.find_entity("勾覆官", "官职") or entity(w, "勾覆官", "官职", comp, "三部勾院均明载勾覆官。")
    clerk_t = w.find_timepoint(clerk_e, "北宋淳化四年五月")
    if not clerk_t:
        clerk_t = tp(w, clerk_e, "北宋淳化四年五月", "任三部勾院吏职",
                     i, comp, "财政勾稽吏职", "建勾覆官编制节点。")
    rel(w, office_t, clerk_t, "编制隶属", i, comp, f"{office}置勾覆官一人。",
        staff_quota=1, staff_type="吏")
    w.commit()


def specific_post_entry(i, office, post):
    z = F[i]["text"]; w = W(i)
    post_t = node(w, post, "北宋淳化四年五月", "官职")[1]
    cite(w, "Timepoints", post_t, i, z, f"本条补证{post}为本部主判官及其职掌。", note="职掌")
    office_t = node(w, office, "北宋淳化四年五月", "机构")[1]
    rel(w, office_t, post_t, "编制隶属", i, z, f"{post}为{office}主判官。",
        staff_quota=1, staff_type="官")
    w.commit()


def main():
    entry360_363()
    entry364(); entry365(); entry366_368(); entry369(); entry370()
    seed_specific_entities()
    entry371(); entry372(); entry373()
    for i, office, post in zip((374, 376, 378), SPECIFIC_OFFICES, SPECIFIC_POSTS):
        specific_office_entry(i, office, post)
        specific_post_entry(i + 1, office, post)


if __name__ == "__main__":
    main()
