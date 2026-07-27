#!/usr/bin/env python3
"""提取 chapter2t4 第391–410条：开拆司属司、理欠司与凭由司。"""
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
    with sqlite3.connect(DICT_DB) as c:
        row = c.execute("select title,page,text,fields from chapter2t4 where id=?", (i,)).fetchone()
    assert row, i
    fields = json.loads(row[3] or "{}")
    return {"title": row[0], "page": row[1], "text": row[2] or "", "fields": fields,
            "values": [row[2] or ""] + [str(v) for k, v in fields.items() if not k.startswith("_")]}


F = {i: load(i) for i in range(391, 411)}


def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])
def C(i): return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'


def q(i, s):
    assert any(s in value for value in F[i]["values"]), (i, s)
    return s


def entity(w, title, type_, quotation, decision):
    return w.entity(title, type_, decision, quotation=quotation)


def cite(w, table, rid, i, quotation, decision, **kw):
    return w.citation(table, rid, C(i), quotation, decision, **kw)


def tp(w, eid, time, event, i, quotation, category, decision, **kw):
    tid = w.timepoint(eid, time, event, decision, quotation, attr_category=category, **kw)
    cite(w, "Timepoints", tid, i, quotation, decision)
    return tid


def rel(w, source, target, kind, i, quotation, decision, *, citation_kw=None, **kw):
    rid = w.relationship(source, target, kind, decision, quotation, **kw)
    cite(w, "Relationships", rid, i, quotation, decision, **(citation_kw or {}))
    return rid


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
    tids = [w.find_timepoint(eid, time) for time in times]
    assert all(tids), list(zip(times, tids))
    chain(w, tids, decision)


def sansi_tp(w, i, time, event, quotation):
    eid = w.find_entity("三司", "机构"); assert eid
    tid = w.find_timepoint(eid, time)
    if not tid:
        tid = tp(w, eid, time, event, i, quotation, "财政机构",
                 f"据第{i}条补建三司在{time}的子司变化节点。", chain="none")
    return tid


def entry391():
    i = 391; z = F[i]["text"]; w = W(i)
    old = w.find_entity("判三司开拆司", "官职")
    formal = w.find_entity("判三司开拆司公事", "官职")
    if old and not formal:
        w.conn.execute("update Entities set title=?,quotation=? where id=?", ("判三司开拆司公事", z, old))
        w._br("Entities", old, "据独立词条正式题名，将此前从编制段建立的‘判三司开拆司’规范为‘判三司开拆司公事’。")
        formal = old
    assert formal
    tid = w.find_timepoint(formal, "北宋雍熙四年十一月"); assert tid
    w.conn.execute("update Timepoints set attr_officer_type=coalesce(attr_officer_type,'朝官') where id=?", (tid,))
    w._br("Timepoints", tid, "本条明载该长官以朝官充，补充任官类型。")
    cite(w, "Timepoints", tid, i, z, "本条补证雍熙四年后判三司开拆司公事为长官及其品位。", note="职掌、品位")
    w.commit()


def undated_child(i, title):
    z = F[i]["text"]; w = W(i)
    eid = entity(w, title, "机构", z, f"本条明载{title}为开拆司属署。")
    tid = tp(w, eid, "宋代（未载具体年月）", z.split("。", 1)[-1].rstrip("。"),
             i, z, "文书机构", f"建{title}无确年制度节点。")
    parent = node(w, "三司开拆司", "宋初", "机构")[1]
    rel(w, parent, tid, "上下级机构", i, z, f"原文明载{title}隶三司开拆司。")
    w.commit()


def entry392_395():
    for i in range(392, 396):
        undated_child(i, F[i]["title"])


def entry396():
    i = 396; z = F[i]["text"]; w = W(i)
    eid = entity(w, "帐籍司", "机构", z, "本条明载帐籍司为开拆司属署。")
    start = tp(w, eid, "北宋淳化二年", "始置，掌三司三部帐簿",
               i, z, "帐籍机构", "建帐籍司始置节点。", chain="none")
    merged = tp(w, eid, "北宋淳化四年", "归开拆司兼领",
                i, z, "帐籍机构", "建帐籍司归开拆司节点。", chain="none")
    chain(w, [start, merged], "连接帐籍司始置与归开拆司节点。")
    parent_e = w.find_entity("三司开拆司", "机构"); assert parent_e
    parent_t = tp(w, parent_e, "北宋淳化四年", "兼领帐籍司", i, z,
                  "官署名", "补建开拆司兼领帐籍司节点。", chain="none")
    chain_times(w, parent_e, ["宋代（未载具体年月）", "宋初", "北宋开宝五年",
                              "北宋太平兴国三年十二月", "北宋雍熙四年十一月",
                              "北宋淳化四年", "北宋至道三年", "北宋咸平元年",
                              "北宋熙宁八年", "北宋熙宁八年十二月十二日"],
                "按历史顺序插入开拆司兼领帐籍司节点。")
    rel(w, parent_t, merged, "上下级机构", i, z, "淳化四年帐籍司归开拆司兼领。")
    w.commit()


def entry397():
    i = 397; z = F[i]["text"]; source = F[i]["fields"]["职源"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = w.find_entity("三司衙司", "机构") or entity(w, "三司衙司", "机构", z, "本条明载三司衙司为官署。")
    old = w.find_timepoint(eid, "宋代（未载具体年月）")
    if old and not w.find_timepoint(eid, "宋初"):
        w.conn.execute("update Timepoints set time='宋初',event='宋初已有',quotation=?,attr_category='官署名' where id=?", (source, old))
        w._br("Timepoints", old, "本条给出宋初确切时期，将原无确年节点更新为宋初已有。")
        tid = old
    else:
        tid = tp(w, eid, "宋初", "宋初已有", i, source, "官署名", "建三司衙司宋初节点。")
    cite(w, "Timepoints", tid, i, z, "补证三司衙司机构性质。")
    cite(w, "Timepoints", tid, i, source, "补证三司衙司宋初已有。", note="职源")
    parent = node(w, "三司", "宋初", "机构")[1]
    rel(w, parent, tid, "上下级机构", i, z, "三司衙司隶三司。")
    officer_e = entity(w, "三司衙司管辖官", "官职", comp, "编制明确设管辖官二员。")
    officer_t = tp(w, officer_e, "宋初", "二员分掌，一员由判开拆司官兼，一员由诸司使或内侍充",
                   i, comp, "衙司机构管辖官", "建三司衙司管辖官编制节点。")
    rel(w, tid, officer_t, "编制隶属", i, comp, "三司衙司置管辖官二员。", staff_quota=2, staff_type="官")
    for title in ("都押衙", "衙佐", "前行", "后行"):
        ce = entity(w, title, "官职", comp, f"本条吏额明确列{title}。")
        ct = tp(w, ce, "宋初", "三司衙司吏职", i, comp, "衙司吏职", f"建{title}吏职节点。")
        rel(w, tid, ct, "编制隶属", i, comp, f"三司衙司吏额列{title}。", staff_type="吏")
    w.commit()


def upgrade_officer_time(w, title, old_time, new_time, event, quotation, decision):
    eid = w.find_entity(title, "官职"); assert eid
    old = w.find_timepoint(eid, old_time)
    current = w.find_timepoint(eid, new_time)
    if old and not current:
        w.conn.execute("update Timepoints set time=?,event=?,quotation=? where id=?", (new_time, event, quotation, old))
        w._br("Timepoints", old, decision)
        return eid, old
    assert current
    return eid, current


def entry398():
    i = 398; z = F[i]["text"]; source = F[i]["fields"]["职源"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = entity(w, "主辖支收司", "机构", z, "本条明载主辖支收司为都磨勘司属署。")
    tid = tp(w, eid, "北宋淳化三年十一月", "始置，掌三司财物支收核销",
             i, source, "财政核销机构", "建主辖支收司始置节点。")
    parent_e = w.find_entity("三司都磨勘司", "机构"); assert parent_e
    parent_t = tp(w, parent_e, "北宋淳化三年十一月", "兼辖主辖支收司", i, z,
                  "官署名", "补建都磨勘司兼辖支收司节点。", chain="none")
    chain_times(w, parent_e, ["宋代（未载具体年月）", "北宋端拱二年十二月四日", "北宋淳化三年十一月"],
                "连接都磨勘司始置与兼辖支收司节点。")
    rel(w, parent_t, tid, "上下级机构", i, z, "主辖支收司隶三司都磨勘司。")
    _, officer_t = upgrade_officer_time(w, "判三司都磨勘司公事", "宋前期", "北宋淳化三年十一月",
                                       "主判都磨勘司并兼领主辖支收司", comp,
                                       "本条给出兼领制度的确切始置时间，替换原宋前期泛节点。")
    cite(w, "Timepoints", officer_t, i, comp, "补证判都磨勘司官兼领主辖支收司。", note="编制")
    rel(w, tid, officer_t, "编制隶属", i, comp, "主辖支收司由判都磨勘司官兼领。", staff_type="官")
    w.commit()


def entry399():
    i = 399; z = F[i]["text"]; source = F[i]["fields"]["职源"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = entity(w, "拘收司", "机构", z, "本条明载拘收司为都磨勘司属署。")
    tid = tp(w, eid, "北宋咸平四年八月", "始置，检查催督未结财物帐目",
             i, source, "财政核销机构", "建拘收司始置节点。")
    parent_e = w.find_entity("三司都磨勘司", "机构"); assert parent_e
    parent_t = tp(w, parent_e, "北宋咸平四年八月", "兼辖拘收司", i, z,
                  "官署名", "补建都磨勘司兼辖拘收司节点。", chain="none")
    chain_times(w, parent_e, ["宋代（未载具体年月）", "北宋端拱二年十二月四日",
                              "北宋淳化三年十一月", "北宋咸平四年八月"],
                "连接都磨勘司与所属二司沿革。")
    rel(w, parent_t, tid, "上下级机构", i, z, "拘收司隶三司都磨勘司。")
    officer_e = w.find_entity("判三司都磨勘司公事", "官职"); assert officer_e
    officer_t = tp(w, officer_e, "北宋咸平四年八月", "兼领拘收司",
                   i, comp, "差遣官名", "建判都磨勘司官兼领拘收司节点。", chain="none")
    earlier = w.find_timepoint(officer_e, "北宋淳化三年十一月"); assert earlier
    chain(w, [earlier, officer_t], "连接判都磨勘司官两次兼领节点。")
    rel(w, tid, officer_t, "编制隶属", i, comp, "拘收司由判都磨勘司官兼领。", staff_type="官")
    w.commit()


def seed_400_409_entities():
    for i, title, type_ in ((400, "征欠司", "机构"), (401, "蠲纳司", "机构"),
                            (402, "三司都理欠司", "机构"), (403, "判三司都理欠、凭由司", "官职"),
                            (404, "权管勾三司都理欠、凭由司公事", "官职"), (405, "勾簿司", "机构"),
                            (406, "三司都凭由司", "机构"), (407, "三部凭由司", "机构"),
                            (408, "判户部(盐铁、度支)凭由司", "官职"),
                            (409, "三司都理欠、凭由司", "机构")):
        quotation = F[i]["text"] or next(iter(F[i]["fields"].values()))
        w = W(i); entity(w, title, type_, quotation, f"第{i}条独立定义{title}为{type_}。")
        w.commit()


def entry400_402():
    # 征欠司
    i = 400; z = F[i]["text"]; h = F[i]["fields"]["职源"]; w = W(i)
    eid = w.find_entity("征欠司", "机构"); assert eid
    start = tp(w, eid, "北宋雍熙二年", "三司盐铁、度支、户部三部始各置征欠司",
               i, h, "财政催欠机构", "建征欠司始置节点。", chain="none")
    joined = tp(w, eid, "北宋至道二年闰七月", "与都凭由司合为一司（后世追称理欠司）",
                i, F[i]["fields"]["别称"], "财政催欠机构", "建至道二年合司节点并标明追称。", chain="none")
    end = tp(w, eid, "北宋乾兴元年", "避仁宗赵祯讳，改为蠲纳司",
             i, h, "财政催欠机构", "建征欠司改名节点。", chain="none")
    chain(w, [start, joined, end], "连接征欠司始置、合司与改名节点。")
    parent = sansi_tp(w, i, "北宋雍熙二年", "三部各置征欠司", h)
    rel(w, parent, start, "上下级机构", i, z, "征欠司隶三司三部。")
    w.commit()

    # 蠲纳司
    i = 401; z = F[i]["text"]; h = F[i]["fields"]["职源"]; w = W(i)
    eid = w.find_entity("蠲纳司", "机构"); assert eid
    start = tp(w, eid, "北宋乾兴元年", "由征欠司避讳改名",
               i, h, "财政催欠机构", "建蠲纳司改名始置节点。", chain="none")
    end = tp(w, eid, "北宋天圣三年六月二十六日", "改为理欠司",
             i, h, "财政催欠机构", "建蠲纳司后续改名节点。", chain="none")
    chain(w, [start, end], "连接蠲纳司始末节点。")
    source_end = node(w, "征欠司", "北宋乾兴元年", "机构")[1]
    rel(w, source_end, start, "前后演变", i, h, "征欠司改名为蠲纳司。")
    parent = sansi_tp(w, i, "北宋乾兴元年", "征欠司改为蠲纳司", h)
    rel(w, parent, start, "上下级机构", i, z, "蠲纳司隶三司。")
    w.commit()

    # 三司都理欠司
    i = 402; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = w.find_entity("三司都理欠司", "机构"); assert eid
    old = w.find_timepoint(eid, "宋代（未载具体年月）")
    if old and not w.find_timepoint(eid, "北宋天圣三年六月二十六日"):
        w.conn.execute("update Timepoints set time=?,event=?,quotation=?,attr_category=? where id=?",
                       ("北宋天圣三年六月二十六日", "三司蠲纳司改为理欠司", h, "财政催欠机构", old))
        w._br("Timepoints", old, "本条给出确切改名时间，将原无确年节点更新为天圣三年。")
        tid = old
    else:
        tid = tp(w, eid, "北宋天圣三年六月二十六日", "三司蠲纳司改为理欠司",
                 i, h, "财政催欠机构", "建三司都理欠司改名节点。")
    cite(w, "Timepoints", tid, i, z, "补证三司都理欠司机构性质。")
    cite(w, "Timepoints", tid, i, h, "补证天圣三年由蠲纳司改为理欠司。", note="职源")
    source_end = node(w, "蠲纳司", "北宋天圣三年六月二十六日", "机构")[1]
    rel(w, source_end, tid, "前后演变", i, h, "蠲纳司改为理欠司。")
    parent = sansi_tp(w, i, "北宋天圣三年六月二十六日", "蠲纳司改为理欠司", h)
    rel(w, parent, tid, "上下级机构", i, z, "三司都理欠司隶三司。")
    # 编制关系在第409条补出主判官确切起点后建立。
    cite(w, "Timepoints", tid, i, comp, "补证判官一人兼领凭由司。", note="编制")
    w.commit()


def entry404():
    i = 404; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("权管勾三司都理欠、凭由司公事", "官职"); assert eid
    tid = tp(w, eid, "宋前期", "资浅者签书理欠司、凭由司公事，不称判而称管勾或权管勾",
             i, z, "财政差遣", "建资浅权管勾差遣节点。")
    parent = node(w, "三司都理欠、凭由司", "北宋至道二年闰七月", "机构")[1]
    rel(w, parent, tid, "编制隶属", i, z, "资浅者权管勾合并后的理欠、凭由司公事。", staff_type="官")
    w.commit()


def entry405():
    i = 405; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = w.find_entity("勾簿司", "机构"); assert eid
    start = tp(w, eid, "北宋咸平元年", "始置，掌三司帐簿勾销、移送及保管",
               i, h, "帐籍机构", "建勾簿司始置节点。", chain="none")
    end = tp(w, eid, "北宋景德四年", "废罢",
             i, h, "帐籍机构", "建勾簿司废罢节点。", chain="none")
    chain(w, [start, end], "连接勾簿司置罢节点。")
    parent = sansi_tp(w, i, "北宋咸平元年", "始置勾簿司", h)
    rel(w, parent, start, "上下级机构", i, z, "勾簿司隶三司。")
    officer_e = w.find_entity("判三司都理欠、凭由司", "官职"); assert officer_e
    officer_t = tp(w, officer_e, "北宋咸平元年", "兼领勾簿司",
                   i, comp, "财政差遣", "建理欠司主判官兼领勾簿司节点。", chain="none")
    earlier = w.find_timepoint(officer_e, "北宋至道二年闰七月"); assert earlier
    later = w.find_timepoint(officer_e, "北宋天圣三年六月二十六日"); assert later
    chain(w, [earlier, officer_t, later], "连接合司主判官始置、兼领勾簿司与天圣改名后节点。")
    rel(w, start, officer_t, "编制隶属", i, comp, "勾簿司由理欠司主判官兼领。", staff_type="官")
    w.commit()


def entry406_408():
    # 三部凭由司先建，供都凭由司演变承接。
    i = 407; z = F[i]["text"]; w = W(i)
    group_e = w.find_entity("三部凭由司", "机构"); assert group_e
    song = tp(w, group_e, "宋初", "盐铁、度支、户部各置凭由司，各置主判官",
              i, z, "凭据审核机构合称", "建三部凭由司宋初节点。", chain="none")
    yong = tp(w, group_e, "北宋雍熙四年", "改由本部推官专判凭由司事",
              i, z, "凭据审核机构合称", "建三部凭由司改判节点。", chain="none")
    end = tp(w, group_e, "北宋淳化二年", "合并为三司都凭由司",
             i, z, "凭据审核机构合称", "建三部凭由司合并节点。", chain="none")
    chain(w, [song, yong, end], "连接三部凭由司沿革。")
    parent = node(w, "三司", "宋初", "机构")[1]
    rel(w, parent, song, "上下级机构", i, z, "三部凭由司隶三司。")
    branches = (("盐铁", "盐铁凭由司"), ("度支", "度支凭由司"), ("户部", "户部凭由司"))
    for department, title in branches:
        be = entity(w, title, "机构", z, f"原文明载宋初{department}置凭由司。")
        bt = tp(w, be, "宋初", f"{department}所置凭由司", i, z, "凭据审核机构", f"建{title}节点。")
        rel(w, song, bt, "统称与实例", i, z, f"三部凭由司包括{title}。")
        dept = node(w, department, "宋初", "机构")[1]
        rel(w, dept, bt, "上下级机构", i, z, f"{title}隶{department}。")
    w.commit()

    i = 406; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = w.find_entity("三司都凭由司", "机构"); assert eid
    old = w.find_timepoint(eid, "宋代（未载具体年月）")
    if old and not w.find_timepoint(eid, "北宋淳化二年"):
        w.conn.execute("update Timepoints set time=?,event=?,quotation=?,attr_category=? where id=?",
                       ("北宋淳化二年", "三部凭由司合为三司都凭由司", h, "凭据审核机构", old))
        w._br("Timepoints", old, "本条给出确切合并时间，将原无确年节点更新为淳化二年。")
        start = old
    else:
        start = tp(w, eid, "北宋淳化二年", "三部凭由司合为三司都凭由司",
                   i, h, "凭据审核机构", "建都凭由司合并节点。", chain="none")
    end = tp(w, eid, "北宋至道二年闰七月", "并归都理欠司",
             i, h, "凭据审核机构", "建都凭由司并归理欠节点。", chain="none")
    chain(w, [start, end], "连接三司都凭由司合置与并归节点。")
    group_end = node(w, "三部凭由司", "北宋淳化二年", "机构")[1]
    cite(w, "Timepoints", start, i, h, "补证淳化二年合置三司都凭由司。", note="职源")
    rel(w, group_end, start, "前后演变", i, h, "三部凭由司合为三司都凭由司。")
    parent = sansi_tp(w, i, "北宋淳化二年", "合置三司都凭由司", h)
    rel(w, parent, start, "上下级机构", i, z, "三司都凭由司隶三司。")
    cite(w, "Timepoints", end, i, comp, "补证由都理欠司主判官兼领。", note="编制")
    w.commit()

    i = 408; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("判户部(盐铁、度支)凭由司", "官职"); assert eid
    song = tp(w, eid, "宋初", "分别主掌户部、盐铁、度支凭由司，以朝官充",
              i, z, "凭由司差遣", "建三部凭由司主判官节点。", attr_officer_type="朝官", chain="none")
    group = node(w, "三部凭由司", "宋初", "机构")[1]
    rel(w, group, song, "编制隶属", i, z, "三部凭由司各置主判官，共三员。", staff_quota=3, staff_type="官")
    w.commit()
    w = W(407)
    eid = w.find_entity("判户部(盐铁、度支)凭由司", "官职"); assert eid
    yong = tp(w, eid, "北宋雍熙四年", "改由各本部推官专判",
              407, F[407]["text"], "凭由司差遣", "建凭由司改由推官专判节点。", chain="none")
    song = w.find_timepoint(eid, "宋初"); assert song
    chain(w, [song, yong], "连接三部凭由司主判官配置变化。")
    w.commit()


def entry409_and_403():
    i = 409; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("三司都理欠、凭由司", "机构"); assert eid
    tid = tp(w, eid, "北宋至道二年闰七月", "都理欠司、都凭由司合为一司，主判官一人总领",
             i, z, "财政催欠与凭据审核合署", "建两司合署节点。")
    parent = sansi_tp(w, i, "北宋至道二年闰七月", "合并都理欠司、都凭由司", z)
    rel(w, parent, tid, "上下级机构", i, z, "合署机构隶三司。")
    due = node(w, "三司都凭由司", "北宋至道二年闰七月", "机构")[1]
    rel(w, due, tid, "前后演变", i, z, "都凭由司并入理欠、凭由合署。")
    debt = node(w, "征欠司", "北宋至道二年闰七月", "机构")[1]
    rel(w, debt, tid, "前后演变", i, z, "当时征欠司与都凭由司合署；标题‘理欠’为后世追称。",
        citation_kw={"conflict_flag": 1, "note": "第400条明确‘理欠司’之名始于天圣，至道二年称理欠司属于追称。"})
    officer_e = w.find_entity("判三司都理欠、凭由司", "官职"); assert officer_e
    officer_t = tp(w, officer_e, "北宋至道二年闰七月", "一人总领都理欠、凭由司",
                   i, z, "财政差遣", "建合署主判官节点。")
    rel(w, tid, officer_t, "编制隶属", i, z, "合署由主判官一人总领。", staff_quota=1, staff_type="官")
    w.commit()

    i = 403; z = F[i]["text"]; w = W(i)
    officer_t = node(w, "判三司都理欠、凭由司", "北宋至道二年闰七月", "官职")[1]
    w.conn.execute("update Timepoints set attr_officer_type=coalesce(attr_officer_type,'朝官') where id=?", (officer_t,))
    w._br("Timepoints", officer_t, "本条明载由朝官充任，补充任官类型。")
    cite(w, "Timepoints", officer_t, i, z, "补证判三司都理欠、凭由司职掌与任官类型。", note="职掌、品位")
    combined = node(w, "三司都理欠、凭由司", "北宋至道二年闰七月", "机构")[1]
    rel(w, combined, officer_t, "编制隶属", i, z, "该差遣掌领理欠司与凭由司公事。", staff_quota=1, staff_type="官")
    w.commit()

    # 天圣三年以后该官兼领都理欠司与凭由司；实际出处为第402条。
    w = W(402); comp = F[402]["fields"]["编制"]
    debt_office = node(w, "三司都理欠司", "北宋天圣三年六月二十六日", "机构")[1]
    officer_e = w.find_entity("判三司都理欠、凭由司", "官职"); assert officer_e
    later = tp(w, officer_e, "北宋天圣三年六月二十六日", "判都理欠司并兼领凭由司",
               402, comp, "财政差遣", "据都理欠司编制补建天圣三年兼领节点。", chain="none")
    earlier = w.find_timepoint(officer_e, "北宋至道二年闰七月"); assert earlier
    chain(w, [earlier, later], "连接合署主判官与天圣改名后兼领节点。")
    rel(w, debt_office, later, "编制隶属", 402, comp,
        "三司都理欠司置判官一人并兼领凭由司。", staff_quota=1, staff_type="官")
    w.commit()


def entry410():
    i = 410; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    inner_e = w.find_entity("入内内侍省", "机构") or entity(w, "入内内侍省", "机构", h, "沿革明确御宝凭由司归入内内侍省管。")
    old_e = entity(w, "御宝凭由司", "机构", h, "至道三年始置御宝凭由司。")
    old_start = tp(w, old_e, "北宋至道三年", "始置，归入内内侍省管",
                   i, h, "宫廷凭由机构", "建御宝凭由司始置节点。", chain="none")
    old_end = tp(w, old_e, "北宋天禧三年正月", "罢入内内侍省御宝凭由司，改在三司置司",
                 i, h, "宫廷凭由机构", "建御宝凭由司改隶节点。", chain="none")
    old_return = tp(w, old_e, "北宋元丰七年八月", "承接三司机构，复归入内内侍省管",
                    i, h, "宫廷凭由机构", "建元丰七年复归节点。", chain="none")
    chain(w, [old_start, old_end, old_return], "连接御宝凭由司入内省、三司与复归沿革。")
    inner_start = tp(w, inner_e, "北宋至道三年", "管辖御宝凭由司",
                     i, h, "内侍机构", "建入内内侍省初管节点。", chain="none")
    inner_return = tp(w, inner_e, "北宋元丰七年八月", "重新管辖御宝凭由司",
                      i, h, "内侍机构", "建入内内侍省复管节点。", chain="none")
    chain(w, [inner_start, inner_return], "连接入内内侍省两次管辖节点。")
    rel(w, inner_start, old_start, "上下级机构", i, h, "至道三年御宝凭由司归入内内侍省管。")
    eid = entity(w, "三司承受御宝凭由司", "机构", z, "本条明载三司承受御宝凭由司为官署。")
    start = tp(w, eid, "北宋天禧三年正月", "罢入内内侍省旧司，在三司置承受御宝凭由司",
               i, h, "宫廷凭由机构", "建三司承受御宝凭由司始置节点。", chain="none")
    end = tp(w, eid, "北宋元丰七年八月", "归隶入内内侍省管",
             i, h, "宫廷凭由机构", "建三司承受御宝凭由司归隶节点。", chain="none")
    chain(w, [start, end], "连接三司承受御宝凭由司置罢节点。")
    old_source = old_end
    rel(w, old_source, start, "前后演变", i, h, "入内内侍省御宝凭由司改为三司承受御宝凭由司。")
    parent = sansi_tp(w, i, "北宋天禧三年正月", "置承受御宝凭由司", h)
    rel(w, parent, start, "上下级机构", i, h, "天禧三年承受御宝凭由司置于三司。")
    rel(w, end, old_return, "前后演变", i, h, "元丰七年三司机构复归入内内侍省。")
    rel(w, inner_return, old_return, "上下级机构", i, h, "元丰七年御宝凭由司归入内内侍省管。")
    cite(w, "Timepoints", start, i, comp, "补证本司吏额六人。", note="编制")
    w.commit()


def finalize_sansi_chain():
    i = 410; w = W(i); eid = w.find_entity("三司", "机构"); assert eid
    times = ["唐天祐三年三月", "宋初", "北宋开宝五年十二月", "北宋太平兴国五年十月",
             "北宋太平兴国八年三月七日", "北宋雍熙二年", "北宋雍熙三年八月",
             "北宋淳化二年", "北宋淳化三年七月一日", "北宋淳化四年五月",
             "北宋淳化四年五月二十一日", "北宋淳化四年十月",
             "北宋淳化五年十二月二十五日", "北宋至道二年闰七月",
             "北宋至道二年十月二十七日", "北宋至道三年十一月五日",
             "北宋咸平元年", "北宋咸平六年", "北宋咸平六年七月十六日",
             "北宋天禧三年正月", "北宋乾兴元年", "北宋天圣三年六月二十六日",
             "北宋熙宁七年", "北宋元丰五年五月"]
    chain_times(w, eid, times, "按历史顺序插入本批三司子司机构变化节点。")
    w.commit()


def main():
    entry391(); entry392_395(); entry396(); entry397(); entry398(); entry399()
    seed_400_409_entities(); entry400_402()
    entry406_408(); entry409_and_403(); entry404(); entry405(); entry410()
    finalize_sansi_chain()


if __name__ == "__main__":
    main()
