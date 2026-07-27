#!/usr/bin/env python3
"""提取 chapter2t4 第281–300条：宰相兼枢密使及三司沿革、属官。"""
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
    fields = json.loads(row[3] or "{}")
    return {"title": row[0], "page": row[1], "text": row[2] or "",
            "all": "\n".join([row[2] or ""] + [str(v) for k, v in fields.items() if not k.startswith("_")])}


F = {i: load(i) for i in range(281, 301)}


def q(i, text):
    assert text in F[i]["all"], f"#{i} 不含：{text}"
    return text


def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])
def C(i): return f"《宋代官制辞典》第{F[i]['page']}页“{F[i]['title']}”条"
def cite(w, table, rid, i, quotation, decision, **kw): return w.citation(table, rid, C(i), quotation, decision, **kw)
def entity(w, title, type_, quotation, decision): return w.entity(title, type_, decision, quotation=quotation)


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


def first_node(w, title, type_=None):
    eid = w.find_entity(title, type_); assert eid, f"缺实体：{title}"
    row = w.conn.execute("SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (eid,)).fetchone()
    assert row
    return eid, row[0]


def chain(w, tids, decision):
    for pos, tid in enumerate(tids):
        w.relink(tid, decision, prev_id=tids[pos - 1] if pos else None,
                 succ_id=tids[pos + 1] if pos + 1 < len(tids) else None)


def entry281():
    i = 281; z = F[i]["all"]
    q_exact = q(i, "英宗嘉祐八年五月戊午，富弼拜枢相。弼既除丧，授枢密使、检校太师、行礼部尚书、同平章事。")
    w = W(i)
    eid = entity(w, "宰相兼枢密使", "官职", F[i]["text"], "辞典明载宋代宰相兼枢密使的复合职任。")
    tid = tp(w, eid, "北宋嘉祐八年五月", "宰相兼枢密使任官例", i, q_exact, "复合职任", "富弼任官例明确证明该复合职任。")
    cite(w, "Timepoints", tid, i, F[i]["text"], "补证宋代宰相或兼枢密使。", note="职任")
    w.commit()


def entry282():
    i = 282; z = F[i]["all"]
    qs = {
        "906": q(i, "唐天祐三年(906)三月，始有盐铁、度支、户部三司之名"),
        "song": q(i, "宋初沿五代、后唐之制。但三司有分有合。"),
        "983": q(i, "太平兴国八年三月七日，分三司为三部治事，即置盐铁使、度支使、户部使三使，并各置副使"),
        "993m": q(i, "淳化四年五月二十一日，三部又合并为三司。"),
        "993o": q(i, "十月，三司改为总计度司。"),
        "994": q(i, "次年十二月二十四日，分总计司为三部，至咸平六年重合为一司"),
        "1082": q(i, "元丰五年五月行新官制，罢三司归户部"),
    }
    w = W(i)
    tri = entity(w, "三司", "机构", F[i]["text"], "辞典明载为中央最高财政机构。")
    times = (
        ("唐天祐三年三月", "始有盐铁、度支、户部三司之名", qs["906"]),
        ("宋初", "沿五代、后唐之制，分掌中央财政", qs["song"]),
        ("北宋太平兴国八年三月七日", "分为盐铁、度支、户部三部", qs["983"]),
        ("北宋淳化四年五月二十一日", "三部合并为三司", qs["993m"]),
        ("北宋淳化四年十月", "改为总计司", qs["993o"]),
        ("北宋咸平六年", "三部重合为一司", qs["994"]),
        ("北宋元丰五年五月", "罢三司，职事归户部", qs["1082"]),
    )
    tri_tps = [tp(w, tri, t, e, i, quote, "财政机构", f"建三司{t}沿革节点。", chain="none") for t, e, quote in times]
    chain(w, tri_tps, "按唐末、宋初及北宋历次分合重排三司时间链。")
    dept_nodes = {}
    for title in ("盐铁", "度支", "户部"):
        eid = entity(w, title, "机构", qs["983"], f"三司分部原文明载{title}部。")
        t983 = tp(w, eid, "北宋太平兴国八年三月七日", "三司分部时置", i, qs["983"], "财政机构", f"建{title}首次分置节点。", chain="none")
        t993 = tp(w, eid, "北宋淳化四年五月二十一日", "并回三司", i, qs["993m"], "财政机构", f"建{title}首次并回节点。", chain="none")
        t994 = tp(w, eid, "北宋淳化五年十二月二十四日", "由总计司再分置", i, qs["994"], "财政机构", f"建{title}再次分置节点。", chain="none")
        t1003 = tp(w, eid, "北宋咸平六年", "重合为三司", i, qs["994"], "财政机构", f"建{title}再次并回节点。", chain="none")
        ordered = [t983, t993, t994, t1003]
        later_hubu = w.find_timepoint(eid, "北宋元丰五年五月") if title == "户部" else None
        if later_hubu:
            ordered.append(later_hubu)
        chain(w, ordered, f"按两轮分合连接{title}时间链。")
        dept_nodes[title] = (t983, t993, t994, t1003)
        rel(w, tri_tps[2], t983, "前后演变", i, qs["983"], f"三司分为{title}部。")
        rel(w, t993, tri_tps[3], "前后演变", i, qs["993m"], f"{title}部合并回三司。")
        rel(w, t1003, tri_tps[5], "前后演变", i, qs["994"], f"{title}部于咸平六年重合为三司。")
    total_e = entity(w, "总计司", "机构", qs["993o"], "三司于淳化四年十月改为总计司。")
    total_start = tp(w, total_e, "北宋淳化四年十月", "由三司改名", i, qs["993o"], "财政机构", "建总计司始置节点。", chain="none")
    total_end = tp(w, total_e, "北宋淳化五年十二月二十四日", "分为盐铁、度支、户部三部", i, qs["994"], "财政机构", "建总计司终结节点。", chain="none")
    precise_start = w.find_timepoint(total_e, "北宋淳化四年十月十六日")
    total_chain = [total_start] + ([precise_start] if precise_start else []) + [total_end]
    chain(w, total_chain, "连接总计司概括始置、精确始置与终结。")
    rel(w, tri_tps[4], total_start, "前后演变", i, qs["993o"], "三司改为总计司。")
    for title in ("盐铁", "度支", "户部"):
        rel(w, total_end, dept_nodes[title][2], "前后演变", i, qs["994"], f"总计司分为{title}部。")
    hubu_1082 = tp(w, w.find_entity("户部", "机构"), "北宋元丰五年五月", "承接罢三司后的财政职事", i, qs["1082"], "财政机构", "建户部承接三司职事节点。")
    chain(w, [*dept_nodes["户部"], hubu_1082], "把元丰承接三司职事节点接入户部时间链。")
    rel(w, tri_tps[6], hubu_1082, "前后演变", i, qs["1082"], "元丰五年罢三司归户部。")
    q_children = q(i, "三司子司有：勾院、都磨勘司、都主辖支收司、拘收司、都理欠司、都凭由司、河渠司、开拆司、发放司、勾凿司、催驱司、受事司、衙司等")
    q_quota = q(i, "三部勾院一百人，都磨勘司三十四人，都主辖支收司二十三人，拘收司四十人，都由司四十九人，都理欠司四十六人，开拆司五十人")
    quotas = {"三司勾院": 100, "三司都磨勘司": 34, "三司都主辖支收司": 23,
              "三司拘收司": 40, "三司都凭由司": 49, "三司都理欠司": 46, "三司开拆司": 50}
    child_titles = ("三司勾院", "三司都磨勘司", "三司都主辖支收司", "三司拘收司", "三司都理欠司",
                    "三司都凭由司", "三司河渠司", "三司开拆司", "三司发放司", "三司勾凿司", "三司催驱司", "三司受事司", "三司衙司")
    for title in child_titles:
        eid = entity(w, title, "机构", q_children, f"三司编制明确列子司{title}。")
        tid = tp(w, eid, "宋代（未载具体年月）", "三司子司", i, q_children, "财政子司", f"建{title}节点。")
        rel(w, tri_tps[1], tid, "上下级机构", i, q_children, f"{title}为三司子司。")
        if title in quotas:
            cite(w, "Timepoints", tid, i, q_quota, f"补充{title}吏额{quotas[title]}人。", note="吏额")
    q_duty = q(i, "总掌全国财政收支之大计，夺户部之权；兼掌城池土木工程，夺工部之职；又领库藏、贸易、四方贡赋、百官添给，侵太府寺之权。")
    cite(w, "Timepoints", tri_tps[1], i, q_duty, "补充三司财政职掌。", note="职掌")
    w.commit()


def simple_temp_office(i, title, event):
    z = F[i]["text"]; w = W(i)
    eid = entity(w, title, "机构", z, "辞典明载为临时机构。")
    tid = tp(w, eid, "宋代（未载具体年月）", event, i, z, "临时机构", f"建{title}节点。")
    tri = node(w, "三司", "宋初", "机构")[1]
    rel(w, tri, tid, "上下级机构", i, z, f"{title}为三司临时分司机构。")
    w.commit()


def entry283(): simple_temp_office(283, "行在三司", "随车驾置，保障皇帝出巡供给")
def entry284(): simple_temp_office(284, "留守司三司", "皇帝出巡或亲征时分领正常财计事务")
def entry285(): simple_temp_office(285, "随驾三司", "随驾赴澶渊，保障军事与生活物资供给")


def entry286():
    i = 286; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("总计司", "机构"); assert eid
    start = tp(w, eid, "北宋淳化四年十月十六日", "三司改名为总计司，置左右计使", i, z, "财政机构", "补建总计司精确始置节点。", chain="none")
    end = tp(w, eid, "北宋淳化五年十二月二十四日", "罢，分为三部", i, z, "财政机构", "补建总计司精确终结节点。", chain="none")
    general_start = w.find_timepoint(eid, "北宋淳化四年十月"); general_end = w.find_timepoint(eid, "北宋淳化五年十二月二十四日")
    assert general_start == start or general_start
    if general_start != start:
        chain(w, [general_start, start, end], "按概括时间、精确始置、精确终结连接总计司节点。")
    cite(w, "Timepoints", start, i, z, "补充总计司下置左右计使、分掌十道财赋。", note="编制、职掌")
    w.commit()


def entry287():
    i = 287; z = F[i]["text"]; w = W(i)
    eid = entity(w, "左计司", "机构", z, "辞典明载为隶总计司官署。")
    tid = tp(w, eid, "北宋淳化四年十月十六日至淳化五年十二月二十四日", "置于东京，分管十道财赋之一半", i, z, "财政机构", "据与总计司同置废时间建时段节点。")
    parent = node(w, "总计司", "北宋淳化四年十月十六日", "机构")[1]
    rel(w, parent, tid, "上下级机构", i, z, "左计司隶总计司。")
    w.commit()


def entry288():
    i = 288; z = F[i]["text"]; w = W(i)
    eid = entity(w, "右计司", "机构", z, "辞典明载为隶总计司官署。")
    tid = tp(w, eid, "北宋淳化四年十月十六日至淳化五年十二月二十四日", "置于西京，与左计分管十道财谷", i, z, "财政机构", "据与总计司同置废时间建时段节点。")
    parent = node(w, "总计司", "北宋淳化四年十月十六日", "机构")[1]
    rel(w, parent, tid, "上下级机构", i, z, "右计司隶总计司。")
    w.commit()


def entry289():
    i = 289; z = F[i]["all"]
    q_start = q(i, "唐昭宗天复元年(901)闰六月始见有三司使之名")
    q_1003 = q(i, "咸平六年(1003)后，专设一使，于元丰五年五月罢")
    w = W(i)
    eid = entity(w, "三司使", "官职", F[i]["text"], "辞典明载为职事官。")
    a = tp(w, eid, "唐天复元年闰六月", "始见", i, q_start, "财政长官", "建三司使始见节点。", chain="none")
    b = tp(w, eid, "北宋咸平六年", "专设一使，总领三部事务", i, q_1003, "财政长官", "建咸平专设节点。", chain="none")
    c = tp(w, eid, "北宋元丰五年五月", "罢", i, q_1003, "财政长官", "建元丰罢置节点。", chain="none")
    chain(w, [a, b, c], "按始见、咸平专置、元丰罢置连接三司使节点。")
    tri = node(w, "三司", "北宋咸平六年", "机构")[1]
    rel(w, tri, b, "编制隶属", i, q_1003, "咸平六年后三司专设一使。", staff_quota=1, staff_type="官")
    q_duty = q(i, "总领盐铁、度支、户部三事，经理国家财赋、土木工程、百官俸给的入与出")
    cite(w, "Timepoints", b, i, q_duty, "补充三司使职掌。", note="职掌")
    w.commit()


def entry290():
    i = 290; z = F[i]["text"]; w = W(i)
    eid = entity(w, "三司使厅", "机构", z, "辞典明载为三司使治所。")
    tid = tp(w, eid, "宋代（未载具体年月）", "三司使治所", i, z, "治所", "建三司使厅节点。")
    tri = node(w, "三司", "宋初", "机构")[1]
    rel(w, tri, tid, "上下级机构", i, z, "三司使厅为三司使治所。")
    w.commit()


def entry291():
    i = 291; z = F[i]["text"]; w = W(i)
    eid = entity(w, "行在三司使", "官职", z, "辞典明载为临时差遣官。")
    tid = tp(w, eid, "宋代（未载具体年月）", "掌领行在三司，筹办皇帝出巡供给", i, z, "临时差遣", "建行在三司使节点。")
    office = node(w, "行在三司", "宋代（未载具体年月）", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "行在三司使掌领行在三司。", staff_type="官")
    w.commit()


def entry292():
    i = 292; z = F[i]["all"]; w = W(i)
    q_period = q(i, "淳化四年(993)闰十月二十五日始置，于淳化五年十二月二十四日罢。")
    q_quota = q(i, "一人（《玉海》卷186《淳化总计使》）。")
    eid = entity(w, "三司总计度使", "官职", F[i]["text"], "辞典明载为差遣官。")
    a = tp(w, eid, "北宋淳化四年闰十月二十五日", "始置，总制左右计事", i, q_period, "财政官", "建始置节点。", chain="none")
    b = tp(w, eid, "北宋淳化五年十二月二十四日", "罢", i, q_period, "财政官", "建罢置节点。", chain="none")
    chain(w, [a, b], "连接总计度使始置与罢置。")
    office = node(w, "总计司", "北宋淳化四年十月十六日", "机构")[1]
    rel(w, office, a, "编制隶属", i, q_quota, "总计司置总计度使一人。", staff_quota=1, staff_type="官")
    w.commit()


def entry293():
    i = 293; z = F[i]["all"]; w = W(i)
    q_period = q(i, "淳化四年十月十六日始置，淳化五年十二月二十四日罢")
    eid = entity(w, "三司左计使", "官职", F[i]["text"], "辞典明载为隶总计司差遣官。")
    tid = tp(w, eid, "北宋淳化四年十月十六日至淳化五年十二月二十四日", "始置至罢", i, q_period, "财政官", "建左计使置废时段节点。")
    q_duty = q(i, "与右计使分管十道钱谷事，大约各领五十州。")
    cite(w, "Timepoints", tid, i, q_duty, "补充左计使职掌。", note="职掌")
    office = node(w, "左计司", "北宋淳化四年十月十六日至淳化五年十二月二十四日", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "左计使分管左计司财赋。", staff_type="官")
    w.commit()


def entry294():
    i = 294; z = F[i]["all"]; w = W(i)
    eid = w.find_entity("三司左计使", "官职"); assert eid
    tid = node(w, "三司左计使", "北宋淳化四年十月十六日至淳化五年十二月二十四日", "官职")[1]
    cite(w, "Timepoints", tid, i, F[i]["text"], "补充左计置署东京及品位。", note="驻地、品位")
    office = node(w, "左计司", "北宋淳化四年十月十六日至淳化五年十二月二十四日", "机构")[1]
    q_quota = q(i, "一人（《宋史·魏羽传》）。")
    rel(w, office, tid, "编制隶属", i, q_quota, "左计使一人。", staff_quota=1, staff_type="官")
    w.commit()


def entry295():
    i = 295; z = F[i]["all"]; w = W(i)
    q_duty = q(i, "建署在西京，与左计使分管十道钱谷，各领五十州")
    q_same = q(i, "与“三司左计使”同。")
    eid = entity(w, "三司右计使", "官职", F[i]["text"], "辞典明载为隶总计司差遣官。")
    tid = tp(w, eid, "北宋淳化四年十月十六日至淳化五年十二月二十四日", "建署西京，与左计使分管十道钱谷", i, q_duty, "财政官", "据与左计使相同置废、编制建节点。")
    office = node(w, "右计司", "北宋淳化四年十月十六日至淳化五年十二月二十四日", "机构")[1]
    rel(w, office, tid, "编制隶属", i, q_same, "右计使一人，与左计使同编制。", staff_quota=1, staff_type="官")
    w.commit()


def entry296():
    i = 296; z = F[i]["text"]; w = W(i)
    ge = entity(w, "三计使", "官职", z, "辞典明确界定为三种计使总名。")
    gt = tp(w, ge, "北宋淳化四年至五年", "总计度使、左计使、右计使总名", i, z, "财政官总称", "建三计使总称节点。")
    for title in ("三司总计度使", "三司左计使", "三司右计使"):
        mt = first_node(w, title, "官职")[1]
        rel(w, gt, mt, "统称与实例", i, z, f"三计使总名包括{title}。")
    w.commit()


def entry297():
    i = 297; z = F[i]["all"]; w = W(i)
    q_start = q(i, "五代后唐天成元年(926)四月，已有判三司之名")
    q_end = q(i, "于太平兴国七年(982)二月罢")
    q_song = q(i, "宋初沿置（《宋史·张美传》）")
    q_role = q(i, "执政官或宣徽使兼领者，带“判”字，位在三司使之上。职掌与“三司使”同")
    eid = entity(w, "判三司事", "官职", F[i]["text"], "辞典明载为差遣官。")
    a = tp(w, eid, "五代后唐天成元年四月", "已有判三司之名", i, q_start, "财政官", "建始见节点。", chain="none")
    b = tp(w, eid, "宋初", "沿置", i, q_song, "财政官", "建宋初沿置节点。", chain="none")
    cite(w, "Timepoints", b, i, q_role, "补充判三司事由执政或宣徽使兼领及其位次。", note="职掌、品位")
    c = tp(w, eid, "北宋太平兴国七年二月", "罢", i, q_end, "财政官", "建罢置节点。", chain="none")
    chain(w, [a, b, c], "按后唐始见、宋初沿置、太平兴国罢置排序。")
    tri = node(w, "三司", "宋初", "机构")[1]
    q_quota = q(i, "一人。如以二人判，资稍浅者为“同判三司事”。")
    rel(w, tri, b, "编制隶属", i, q_quota, "判三司事一人，兼领三司。", staff_quota=1, staff_type="官")
    w.commit()


def entry298():
    i = 298; z = F[i]["all"]; w = W(i)
    q_period = q(i, "太平兴国七年（982）二月七日始置"), q(i, "次年三月七日罢")
    eid = entity(w, "同判三司事", "官职", F[i]["text"], "辞典明载为差遣官。")
    a = tp(w, eid, "北宋太平兴国七年二月七日", "始置", i, q_period[0], "财政官", "建始置节点。", chain="none")
    b = tp(w, eid, "北宋太平兴国八年三月七日", "罢", i, q_period[1], "财政官", "建罢置节点。", chain="none")
    chain(w, [a, b], "连接同判三司事始置与罢置。")
    tri = node(w, "三司", "宋初", "机构")[1]
    q_rank = q(i, "职事与“判三司使”同，位次于判三司事。")
    rel(w, tri, a, "编制隶属", i, q_rank, "同判三司事为资浅者，位次判三司事。", staff_type="官")
    w.commit()


def entry299():
    i = 299; z = F[i]["text"]; w = W(i)
    eid = entity(w, "提点三司公事", "官职", z, "辞典明载为副相兼领三司的兼官。")
    tid = tp(w, eid, "北宋初", "参知政事兼领三司事时所带", i, z, "兼官", "建北宋初兼领节点。")
    tri = node(w, "三司", "宋初", "机构")[1]
    rel(w, tri, tid, "编制隶属", i, z, "提点三司公事为副相兼领三司之官。", staff_type="官")
    w.commit()


def entry300():
    i = 300; z = F[i]["all"]; w = W(i)
    eid = entity(w, "都提举三司公事", "官职", F[i]["text"], "辞典明载为宰相兼领三司的兼官。")
    tid = tp(w, eid, "北宋初", "宰相兼领三司公事，位于提点三司公事之上", i, F[i]["text"], "兼官", "建北宋初兼领节点。")
    tri = node(w, "三司", "宋初", "机构")[1]
    rel(w, tri, tid, "编制隶属", i, z, "都提举三司公事为宰相兼领三司之官。", staff_type="官")
    w.commit()


def main():
    entry281(); entry282(); entry283(); entry284(); entry285()
    entry286(); entry287(); entry288(); entry289(); entry290()
    entry291(); entry292(); entry293(); entry294(); entry295()
    entry296(); entry297(); entry298(); entry299(); entry300()


if __name__ == "__main__": main()
