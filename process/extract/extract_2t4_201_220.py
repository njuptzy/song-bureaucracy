#!/usr/bin/env python3
"""提取 chapter2t4 第201–220条：枢密院后期诸房、属官与银台司。"""
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
    fields = json.loads(row[3] or "{}")
    parts = [row[2] or ""] + [str(v) for k, v in fields.items() if not k.startswith("_")]
    return {"title": row[0], "page": row[1], "text": row[2] or "", "all": "\n".join(parts)}


F = {i: load(i) for i in range(201, 221)}


def q(i, text):
    assert text in F[i]["all"], f"#{i} 不含：{text}"
    return text


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def C(i):
    return f"《宋代官制辞典》第{F[i]['page']}页“{F[i]['title']}”条"


def cite(w, table, rid, i, quotation, decision, **kwargs):
    return w.citation(table, rid, C(i), quotation, decision, **kwargs)


def entity(w, title, type_, i, quotation, decision):
    return w.entity(title, type_, decision, quotation=quotation)


def tp(w, eid, time, event, i, quotation, category, decision, **kwargs):
    tid = w.timepoint(
        eid, time, event, decision, quotation, attr_category=category, **kwargs
    )
    cite(w, "Timepoints", tid, i, quotation, decision)
    return tid


def rel(w, source, target, kind, i, quotation, decision, **kwargs):
    rid = w.relationship(source, target, kind, decision, quotation, **kwargs)
    cite(w, "Relationships", rid, i, quotation, decision)
    return rid


def node(w, title, time, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, f"缺实体：{title}"
    tid = w.find_timepoint(eid, time)
    assert tid, f"{title} 缺时间点：{time}"
    return eid, tid


def chain(w, ids, decision):
    assert all(ids)
    for pos, tid in enumerate(ids):
        w.relink(
            tid,
            decision,
            prev_id=ids[pos - 1] if pos else None,
            succ_id=ids[pos + 1] if pos + 1 < len(ids) else None,
        )


def parent(w, period):
    return node(w, "枢密院", period, "机构")[1]


def room(w, title, i, quotation, decision):
    return entity(w, title, "机构", i, quotation, decision)


def insert_before(w, eid, tid, before_tid, decision):
    row = w.conn.execute("SELECT prev_id FROM Timepoints WHERE id=?", (before_tid,)).fetchone()
    assert row
    prev = row[0]
    w.relink(tid, decision, prev_id=prev, succ_id=before_tid)
    if prev is not None:
        w.relink(prev, decision, succ_id=tid)
    w.relink(before_tid, decision, prev_id=tid)


def entry201():
    i = 201
    z = F[i]["text"]
    w = W(i)
    eid = w.find_entity("枢密院小吏房", "机构")
    assert eid
    start = w.find_timepoint(eid, "北宋元祐")
    if start is None:
        start = w.find_timepoint(eid, "北宋元丰改制后")
        assert start
        w.conn.execute(
            "UPDATE Timepoints SET time=?,event=?,quotation=?,attr_category=? WHERE id=?",
            ("北宋元祐", "创置，掌内侍磨勘、功过叙复及使臣校尉迁转", z, "办事机构", start),
        )
        w._br("Timepoints", start, "据小吏房专条把十二房总条的宽泛元丰后节点精确为元祐创置，并补职掌。")
    cite(w, "Timepoints", start, i, z, "补证小吏房元祐创置与职掌。")
    end = w.find_timepoint(eid, "南宋乾道六年二月")
    assert end
    cite(w, "Timepoints", end, i, z, "本专条补证乾道六年并房。")
    chain(w, [start, end], "按元祐创置与乾道并房排序。")
    for target_title in ("枢密院吏房", "枢密院刑房"):
        target = node(w, target_title, "南宋乾道六年二月", "机构")[1]
        rel(w, end, target, "前后演变", i, z, f"小吏房于乾道六年并入{target_title}。")
    rel(w, parent(w, "北宋元丰四年"), start, "上下级机构", i, z, "小吏房为枢密院办事机构。")
    w.commit()


def entry202():
    i = 202
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "枢密院二十五房", "机构", i, z, "辞典明确把北宋末南宋初的二十五房作为机构组合。")
    expanded = tp(w, eid, "北宋末、南宋初", "因宋金战争由十二房扩为二十五房", i, z, "办事机构总名", "建二十五房扩充状态。", chain="none")
    reduced = tp(w, eid, "南宋乾道六年", "省并为五房及院杂司", i, z, "办事机构总名", "建乾道省并终结节点。", chain="none")
    chain(w, [expanded, reduced], "按战争期扩充与乾道省并排序。")
    rel(w, parent(w, "南宋绍兴七年"), expanded, "上下级机构", i, z, "二十五房为枢密院内部办事机构组合。")
    w.commit()


def entry203():
    i = 203
    q_head = q(i, "官司名，初隶枢密院。绍兴末隶三省枢密院")
    q_1130 = q(i, "建炎四年（1130）六月辛未朔，御营使司并入枢密院为机速房")
    q_1159 = q(i, "绍兴二十九年（1159）九月十四日，罢机速房")
    q_1161 = q(i, "绍兴三十一年(1161)复置，但称“三省枢密院机速房”")
    q_1172 = q(i, "乾道八年(1172)复罢")
    q_duty = q(i, "不分日夜专一收发边防军机文书")
    w = W(i)
    old = w.find_entity("枢密院机速房", "机构")
    assert old
    yys = entity(w, "御营使司", "机构", i, q_1130, "原文明载御营使司并入枢密院。")
    yys_end = tp(w, yys, "南宋建炎四年六月", "并入枢密院，改为机速房", i, q_1130, "官司名", "建御营使司并入终结节点。")
    start = tp(w, old, "南宋建炎四年六月", "由御营使司并入枢密院后设置，掌边防机速", i, q_1130, "官司名", "建机速房始置节点。", chain="none")
    cite(w, "Timepoints", start, i, q_duty, "补充机速房职掌。", note="职掌")
    stop = tp(w, old, "南宋绍兴二十九年九月十四日", "罢", i, q_1159, "官司名", "建绍兴二十九年罢置节点。", chain="none")
    renamed = tp(w, old, "南宋绍兴三十一年", "复置时改称三省枢密院机速房", i, q_1161, "官司名", "建复置改名的来源节点。", chain="none")
    new_parent = entity(w, "三省枢密院", "机构", i, q_head, "原文明载绍兴末的隶属机构为三省枢密院。")
    parent_tp = tp(w, new_parent, "南宋绍兴末", "机速房改隶三省枢密院", i, q_head, "官署名", "建绍兴末三省枢密院承载节点。")
    new = entity(w, "三省枢密院机速房", "机构", i, q_1161, "原文明载复置后的正式称名。")
    new_start = tp(w, new, "南宋绍兴三十一年", "由枢密院机速房复置改称", i, q_1161, "官司名", "建新称始置节点。", chain="none")
    old_merge = w.find_timepoint(old, "南宋乾道六年二月")
    if old_merge is not None:
        w.conn.execute("UPDATE Timepoints SET entity_id=? WHERE id=?", (new, old_merge))
        w._br("Timepoints", old_merge, "据专条1161年改称三省枢密院机速房，将1170年并房节点移至改称后的机构。")
    else:
        old_merge = w.find_timepoint(new, "南宋乾道六年二月")
        assert old_merge
    new_end = tp(w, new, "南宋乾道八年", "复罢", i, q_1172, "官司名", "建乾道八年复罢节点。", chain="none")
    chain(w, [start, stop, renamed], "按建炎始置、绍兴罢置与复置改名排序。")
    chain(w, [new_start, old_merge, new_end], "按绍兴改称、乾道并房与复罢排序。")
    rel(w, yys_end, start, "前后演变", i, q_1130, "御营使司并入枢密院后成为机速房。")
    rel(w, renamed, new_start, "前后演变", i, q_1161, "复置时改称三省枢密院机速房。")
    rel(w, parent(w, "南宋绍兴七年"), start, "上下级机构", i, q_head, "机速房初隶枢密院。")
    rel(w, parent_tp, new_start, "上下级机构", i, q_head, "绍兴末机速房隶三省枢密院。")
    w.commit()


def entry204():
    i = 204
    z = F[i]["text"]
    w = W(i)
    eid = room(w, "枢密院写宣房", i, z, "辞典明载为枢密院办事机构。")
    start = tp(w, eid, "南宋初", "始置，掌书写宣命并检察文书递角", i, z, "办事机构", "建南宋初写宣房节点。", chain="none")
    end = tp(w, eid, "南宋乾道六年二月", "并入工房", i, z, "办事机构", "建乾道并入工房节点。", chain="none")
    chain(w, [start, end], "按南宋初始置与乾道并房排序。")
    target = node(w, "枢密院工房", "南宋乾道六年二月", "机构")[1]
    rel(w, end, target, "前后演变", i, z, "写宣房于乾道六年并入工房。")
    rel(w, parent(w, "南宋绍兴七年"), start, "上下级机构", i, z, "写宣房为枢密院办事机构。")
    w.commit()


def entry205():
    i = 205
    q_head = q(i, "官司名，隶枢密院。")
    q_start = q(i, "北宋元丰六年二月二十八日已见置")
    q_duty = q(i, "收受、分类、保管三省、枢密院所修时政记")
    q_quota = q(i, "吏额七人")
    w = W(i)
    eid = room(w, "枢密院编修时政记房", i, q_head, "辞典明载为隶枢密院官司。")
    tid = tp(w, eid, "北宋元丰六年二月二十八日", "已见设置，收受保管时政记供修国史", i, q_start, "官司名", "建元丰已见置节点。")
    cite(w, "Timepoints", tid, i, q_duty, "补充职掌。", note="职掌")
    cite(w, "Timepoints", tid, i, q_quota, "补充吏额七人。", note="编制")
    rel(w, parent(w, "北宋元丰四年"), tid, "上下级机构", i, q_head, "编修时政记房隶枢密院。")
    w.commit()


def entry206():
    i = 206
    q_start = q(i, "建炎四年(1130)六月二十四日始置")
    q_change = q(i, "同年十一月十六日，改为计议官")
    q_duty = q(i, "设于办官以掌边防机速之事")
    q_quota = q(i, "四员")
    q_grade = q(i, "正八品")
    w = W(i)
    eid = entity(w, "枢密院干办官", "官职", i, q_start, "辞典明载为职事官。")
    start = tp(w, eid, "南宋建炎四年六月二十四日", "始置，掌边防机速，四员，正八品", i, q_start, "职事官", "建干办官始置节点。", attr_grade="正八品", chain="none")
    cite(w, "Timepoints", start, i, q_duty, "补充职掌。", note="职掌")
    cite(w, "Timepoints", start, i, q_quota, "补充四员编制。", note="编制")
    cite(w, "Timepoints", start, i, q_grade, "补充官品。", note="品位")
    end = tp(w, eid, "南宋建炎四年十一月十六日", "改为计议官", i, q_change, "职事官", "建改名终结节点。", chain="none")
    chain(w, [start, end], "按建炎始置与同年改名排序。")
    office = node(w, "枢密院机速房", "南宋建炎四年六月", "机构")[1]
    rel(w, office, start, "编制隶属", i, q_duty, "干办官设置于机速房掌边防机速。", staff_quota=4, staff_type="官")
    w.commit()


def entry207():
    i = 207
    q_start = q(i, "建炎四年（1130）十一月十六日，由枢密院于办官改名")
    q_end = q(i, "绍兴十一年（1141）四月二十二日罢置")
    q_same = q(i, "与“枢密院干办官”同。")
    w = W(i)
    eid = entity(w, "枢密院计议官", "官职", i, q_start, "辞典明载为干办官改名后的职事官。")
    start = tp(w, eid, "南宋建炎四年十一月十六日", "由枢密院干办官改名，掌边防机速，四员，正八品", i, q_start, "职事官", "建计议官改名始置节点。", attr_grade="正八品", chain="none")
    cite(w, "Timepoints", start, i, q_same, "本条明确职掌、品位与干办官相同。", note="参见同批#206")
    end = tp(w, eid, "南宋绍兴十一年四月二十二日", "罢置", i, q_end, "职事官", "建绍兴罢置节点。", chain="none")
    chain(w, [start, end], "按建炎改名与绍兴罢置排序。")
    source = node(w, "枢密院干办官", "南宋建炎四年十一月十六日", "官职")[1]
    rel(w, source, start, "前后演变", i, q_start, "枢密院干办官改名为计议官。")
    office = node(w, "枢密院机速房", "南宋建炎四年六月", "机构")[1]
    rel(w, office, start, "编制隶属", i, q_same, "计议官沿袭干办官在机速房的职掌。", staff_quota=4, staff_type="官")
    w.commit()


def entry208():
    i = 208
    q_head = q(i, "官署名。隶枢密院")
    q_start = q(i, "检详所之设不会早于是年（1071）")
    q_duty = q(i, "检用、审核枢密院诸房条例及行遣文字")
    w = W(i)
    eid = entity(w, "枢密院检详所", "机构", i, q_head, "辞典明载为隶枢密院官署。")
    tid = tp(w, eid, "北宋熙宁四年以后（推论）", "据检详官始置时间推论本所设置不早于此年", i, q_start, "官署名", "保留辞典明确标注的推论性起点。")
    cite(w, "Timepoints", tid, i, q_duty, "补充检详所职掌。", note="职掌")
    rel(w, parent(w, "北宋熙宁元年"), tid, "上下级机构", i, q_head, "检详所隶枢密院。")
    w.commit()


def entry209():
    i = 209
    q_start = q(i, "北宋熙宁四年（1071）十月五日始置")
    q_end = q(i, "元丰五年(1082)二月二十四日罢")
    q_restore = q(i, "南宋建炎三年(1129)六月二十六日复置")
    q_quota = q(i, "熙宁时定制三员，分房并置。南宋时二员，不分房")
    q_grade = q(i, "南宋时官品定为从六品")
    w = W(i)
    eid = entity(w, "枢密院检详诸房文字", "官职", i, q_start, "辞典明载为职事官名。")
    start = tp(w, eid, "北宋熙宁四年十月五日", "始置，三员分房并置", i, q_start, "职事官", "建熙宁始置节点。", chain="none")
    cite(w, "Timepoints", start, i, q_quota, "补充熙宁三员编制。", note="编制")
    end = tp(w, eid, "北宋元丰五年二月二十四日", "罢置", i, q_end, "职事官", "建元丰罢置节点。", chain="none")
    restore = tp(w, eid, "南宋建炎三年六月二十六日", "复置，二员不分房，从六品", i, q_restore, "职事官", "建建炎复置节点。", attr_grade="从六品", chain="none")
    cite(w, "Timepoints", restore, i, q_quota, "补充南宋二员编制。", note="编制")
    cite(w, "Timepoints", restore, i, q_grade, "补充南宋官品。", note="品位")
    chain(w, [start, end, restore], "按熙宁始置、元丰罢置、建炎复置排序。")
    office = node(w, "枢密院检详所", "北宋熙宁四年以后（推论）", "机构")[1]
    rel(w, office, start, "编制隶属", i, q_quota, "熙宁检详所置检详诸房文字三员。", staff_quota=3, staff_type="官")
    rel(w, office, restore, "编制隶属", i, q_quota, "南宋检详诸房文字二员、不分房。", staff_quota=2, staff_type="官")
    w.commit()


def entry210():
    i = 210
    q_type = q(i, "元祐前为差遣，其后为职事官。")
    q_1044 = q(i, "庆历四年（1044）二月五日始有“编修”之名")
    q_1089 = q(i, "元祐四年（1089）十一月十六日，正式设枢密院编修官")
    q_quota = q(i, "元祐时以四员为额")
    q_south = q(i, "南宋时以二员为额")
    q_grade = q(i, "正八品")
    w = W(i)
    eid = entity(w, "枢密院编修", "官职", i, q_type, "修复后的原页文字明确其先为差遣、后为职事官。")
    first = tp(w, eid, "北宋庆历四年二月五日", "始有编修之名，时为差遣", i, q_1044, "差遣", "建庆历初见节点。", chain="none")
    formal = tp(w, eid, "北宋元祐四年十一月十六日", "正式设置为职事官，四员，正八品", i, q_1089, "职事官", "建元祐正式设官节点。", attr_grade="正八品", chain="none")
    cite(w, "Timepoints", formal, i, q_type, "补充元祐前后官类变化。", note="官类")
    cite(w, "Timepoints", formal, i, q_quota, "补充元祐四员编制。", note="编制")
    cite(w, "Timepoints", formal, i, q_grade, "补充正八品。", note="品位")
    south = tp(w, eid, "南宋", "编制二员", i, q_south, "职事官", "建南宋员额节点。", attr_grade="正八品", chain="none")
    chain(w, [first, formal, south], "按庆历初见、元祐正式设官与南宋员额排序。")
    rel(w, parent(w, "宋初"), first, "编制隶属", i, q_1044, "枢密院编修为本院差遣。", staff_type="官")
    rel(w, parent(w, "北宋元丰四年"), formal, "编制隶属", i, q_quota, "元祐正式设枢密院编修四员。", staff_quota=4, staff_type="官")
    rel(w, parent(w, "南宋绍兴七年"), south, "编制隶属", i, q_south, "南宋枢密院编修二员。", staff_quota=2, staff_type="官")
    w.commit()


def entry211():
    i = 211
    q_head = q(i, "官署名。枢密院编修官治所。")
    q_staff = q(i, "官额有枢密院编修，二至四员")
    q_change = q(i, "枢密院供检文字一名，嘉定五年改为令史；枢密院编修文字二名，嘉定五年改头名编修文字为书令史，第二名编修文字为守当官")
    w = W(i)
    office = entity(w, "枢密院编修司", "机构", i, q_head, "辞典明载为枢密院编修官治所。")
    office_tp = tp(w, office, "未知", "枢密院编修官治所", i, q_head, "官署名", "原文无始置时间，建真实无年节点。")
    rel(w, parent(w, "南宋绍兴七年"), office_tp, "上下级机构", i, q_head, "编修司为枢密院官署。")
    editor = node(w, "枢密院编修", "北宋元祐四年十一月十六日", "官职")[1]
    rel(w, office_tp, editor, "编制隶属", i, q_staff, "编修司官额为枢密院编修二至四员。", staff_type="官")
    supply_e = entity(w, "枢密院供检文字", "官职", i, q_change, "编制段明确列枢密院供检文字。")
    supply_before = tp(w, supply_e, "南宋嘉定五年前", "一名", i, q_change, "吏职", "建嘉定改名以前的供检文字节点。", chain="none")
    supply_end = tp(w, supply_e, "南宋嘉定五年", "改为令史", i, q_change, "吏职", "建嘉定改名终结节点。", chain="none")
    chain(w, [supply_before, supply_end], "按嘉定改名前后排序。")
    edit_e = entity(w, "枢密院编修文字", "官职", i, q_change, "编制段明确列枢密院编修文字。")
    edit_before = tp(w, edit_e, "南宋嘉定五年前", "二名", i, q_change, "吏职", "建嘉定改名以前的编修文字节点。", chain="none")
    edit_end = tp(w, edit_e, "南宋嘉定五年", "分别改为书令史、守当官", i, q_change, "吏职", "建嘉定分改终结节点。", chain="none")
    chain(w, [edit_before, edit_end], "按嘉定改名前后排序。")
    targets = []
    for title, quota in (("令史", 1), ("书令史", 1), ("守当官", 1)):
        target_e = entity(w, title, "官职", i, q_change, f"嘉定改名后形成{title}吏职。")
        target_tp = tp(w, target_e, "南宋嘉定五年", f"编修司内改置{title}", i, q_change, "吏职", f"建嘉定五年{title}节点。")
        targets.append((title, target_tp, quota))
    rel(w, office_tp, supply_before, "编制隶属", i, q_change, "编修司有供检文字一名。", staff_quota=1, staff_type="吏")
    rel(w, office_tp, edit_before, "编制隶属", i, q_change, "编修司有编修文字二名。", staff_quota=2, staff_type="吏")
    rel(w, supply_end, targets[0][1], "前后演变", i, q_change, "供检文字于嘉定五年改为令史。")
    rel(w, edit_end, targets[1][1], "前后演变", i, q_change, "头名编修文字于嘉定五年改为书令史。")
    rel(w, edit_end, targets[2][1], "前后演变", i, q_change, "第二名编修文字于嘉定五年改为守当官。")
    for title, target_tp, quota in targets:
        rel(w, office_tp, target_tp, "编制隶属", i, q_change, f"嘉定五年后编修司置{title}一名。", staff_quota=quota, staff_type="吏")
    w.commit()


def entry212():
    i = 212
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "枢属", "官职", i, z, "辞典明确将其定义为枢密院属官总称。")
    group = tp(w, eid, "未知", "枢密院都承旨、副都承旨、检详官、编修官的总称", i, z, "属官总称", "原文无统一时间，建总称节点。")
    members = (
        ("枢密院都承旨", "北宋太平兴国七年四月三日"),
        ("枢密院副都承旨", "北宋咸平元年十月"),
        ("枢密院检详诸房文字", "北宋熙宁四年十月五日"),
        ("枢密院编修", "北宋元祐四年十一月十六日"),
    )
    for title, time in members:
        member = node(w, title, time, "官职")[1]
        rel(w, group, member, "统称与实例", i, z, f"枢属总称明确包括{title}。")
    w.commit()


def entry213():
    # “枢掾”仅为“枢属”的同义称谓，人物任官例不形成新的制度事实。
    return


def entry214():
    i = 214
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "枢密院制置兵马司", "机构", i, z, "辞典明载为官署。")
    tid = tp(w, eid, "北宋仁宗朝", "见置，掌防御、守边城寨及兵甲", i, z, "官署名", "建仁宗朝状态节点。")
    rel(w, parent(w, "宋初"), tid, "上下级机构", i, z, "制置兵马司为枢密院官署。")
    for title in ("枢密院副承旨", "主事"):
        post_e = w.find_entity(title, "官职")
        assert post_e
        post = w.conn.execute("SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (post_e,)).fetchone()[0]
        rel(w, tid, post, "编制隶属", i, z, f"制置兵马司由{title}等掌管。", staff_type="吏" if title == "主事" else "官")
    w.commit()


def entry215():
    i = 215
    q_head = q(i, "官署名。隶枢密院")
    q_start = q(i, "崇宁元年（1102）八月，以尚书省讲议武备房归枢密院置")
    q_end = q(i, "崇宁三年三月八日罢，四月结局")
    q_duty = q(i, "掌民兵训练、增置兵额及战备等事")
    q_staff = q(i, "置提举枢密院讲议司事、枢密院讲议司详定官、参详官等")
    w = W(i)
    source = entity(w, "尚书省讲议武备房", "机构", i, q_start, "原文明载为讲议司前身。")
    source_end = tp(w, source, "北宋崇宁元年八月", "归枢密院改置讲议司", i, q_start, "办事机构", "建前身终结节点。")
    eid = entity(w, "枢密院讲议司", "机构", i, q_head, "辞典明载为隶枢密院官署。")
    start = tp(w, eid, "北宋崇宁元年八月", "由尚书省讲议武备房归枢密院置，掌武备", i, q_start, "官署名", "建讲议司始置节点。", chain="none")
    cite(w, "Timepoints", start, i, q_duty, "补充职掌。", note="职掌")
    stop = tp(w, eid, "北宋崇宁三年三月八日", "罢", i, q_end, "官署名", "建罢置节点。", chain="none")
    close = tp(w, eid, "北宋崇宁三年四月", "结局", i, q_end, "官署名", "建结局节点。", chain="none")
    chain(w, [start, stop, close], "按始置、罢置、结局排序。")
    rel(w, source_end, start, "前后演变", i, q_start, "尚书省讲议武备房归枢密院改置讲议司。")
    rel(w, parent(w, "北宋元丰四年"), start, "上下级机构", i, q_head, "讲议司隶枢密院。")
    for title in ("提举枢密院讲议司事", "枢密院讲议司详定官", "枢密院讲议司参详官"):
        post_e = entity(w, title, "官职", i, q_staff, "讲议司编制明确列此官。")
        post = tp(w, post_e, "北宋崇宁元年八月", "随讲议司设置", i, q_staff, "职事官", "建随司设置节点。")
        rel(w, start, post, "编制隶属", i, q_staff, f"讲议司设置{title}。", staff_type="官")
    w.commit()


def entry216():
    i = 216
    q_head = q(i, "京局名，初隶枢密院。")
    q_song = q(i, "在帝门之侧置司——银台司，则始于宋")
    q_move = q(i, "淳化四年(993)八月十八日，通进司、银台司，移入宣徽北院置厅事，设知二司官，脱离枢密院")
    q_staff = q(i, "银台司主事二人，书令史八人，贴房十一人。")
    w = W(i)
    silver = entity(w, "银台司", "机构", i, q_head, "辞典明载为京局。")
    song = tp(w, silver, "宋代", "始置于帝门之侧，初隶枢密院", i, q_song, "京局名", "建宋代始置状态。", chain="none")
    moved = tp(w, silver, "北宋淳化四年八月十八日", "移入宣徽北院置厅事，脱离枢密院", i, q_move, "京局名", "建淳化移隶节点。", chain="none")
    chain(w, [song, moved], "按宋代始置与淳化移隶排序。")
    xuanhui = entity(w, "宣徽北院", "机构", i, q_move, "原文明载银台、通进二司移入宣徽北院。")
    xuanhui_tp = tp(w, xuanhui, "北宋淳化四年八月十八日", "接纳通进司、银台司置厅事", i, q_move, "官署名", "建宣徽北院承载节点。")
    tongjin = entity(w, "通进司", "机构", i, q_move, "原文明载通进司与银台司同时移入宣徽北院。")
    tongjin_tp = tp(w, tongjin, "北宋淳化四年八月十八日", "移入宣徽北院置厅事", i, q_move, "京局名", "建通进司淳化节点。")
    rel(w, parent(w, "宋初"), song, "上下级机构", i, q_head, "银台司初隶枢密院。")
    rel(w, xuanhui_tp, moved, "上下级机构", i, q_move, "淳化四年银台司移入宣徽北院。")
    rel(w, xuanhui_tp, tongjin_tp, "上下级机构", i, q_move, "淳化四年通进司移入宣徽北院。")
    staff = (("主事", 2), ("书令史", 8), ("贴房", 11))
    for title, quota in staff:
        post_e = entity(w, title, "官职", i, q_staff, f"银台司编制明确列{title}。")
        row = w.conn.execute("SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (post_e,)).fetchone()
        post = row[0] if row else tp(w, post_e, "未知", f"银台司吏职{title}", i, q_staff, "吏职", "原文无时间，建吏职承载节点。")
        if row:
            cite(w, "Timepoints", post, i, q_staff, f"补充银台司{title}编制。", note="编制")
        rel(w, song, post, "编制隶属", i, q_staff, f"银台司置{title}{quota}人。", staff_quota=quota, staff_type="吏")
    w.commit()


def entry217():
    i = 217
    z = F[i]["all"]
    q_start = q(i, "太宗淳化四年八月十八日设")
    w = W(i)
    eid = entity(w, "知通进、银台司公事", "官职", i, F[i]["text"], "辞典明载为差遣官名。")
    tid = tp(w, eid, "北宋淳化四年八月十八日", "始设，审察通进、银台二司章奏案牒，二人", i, q_start, "差遣官", "建淳化始置节点。")
    cite(w, "Timepoints", tid, i, z, "补充职掌与二人编制。", note="职掌、编制")
    for office in ("银台司", "通进司"):
        office_tp = node(w, office, "北宋淳化四年八月十八日", "机构")[1]
        rel(w, office_tp, tid, "编制隶属", i, z, f"知二司官共同掌领{office}。", staff_type="官")
    w.commit()


def entry218():
    i = 218
    q_type = q(i, "差遣名。由两制以上文臣充")
    q_start = q(i, "淳化四年，给事中封驳公事归银台司兼")
    q_end = q(i, "元丰五年六月二十五日罢银台司封驳房归给事中")
    q_duty = q(i, "兼掌制敕有所不当者，予以驳回")
    w = W(i)
    eid = entity(w, "知通进、银台司兼门下封驳公事", "官职", i, q_type, "辞典明载为两制以上文臣所充差遣。")
    start = tp(w, eid, "北宋淳化四年", "始兼门下封驳公事，掌不当制敕驳回", i, q_start, "差遣", "建淳化兼领节点。", chain="none")
    cite(w, "Timepoints", start, i, q_duty, "补充封驳职掌。", note="职掌")
    end = tp(w, eid, "北宋元丰五年六月二十五日", "随银台司封驳房罢而终止", i, q_end, "差遣", "建元丰终结节点。", chain="none")
    chain(w, [start, end], "按淳化兼领与元丰罢归排序。")
    silver = node(w, "银台司", "北宋淳化四年八月十八日", "机构")[1]
    tongjin = node(w, "通进司", "北宋淳化四年八月十八日", "机构")[1]
    rel(w, silver, start, "编制隶属", i, q_start, "该差遣掌银台司并兼封驳。", staff_type="官")
    rel(w, tongjin, start, "编制隶属", i, q_start, "该差遣同时掌通进司。", staff_type="官")
    room_e = entity(w, "银台司封驳房", "机构", i, q_end, "原文明载元丰五年罢银台司封驳房。")
    room_start = tp(w, room_e, "北宋淳化四年", "承接给事中封驳公事", i, q_start, "办事机构", "建淳化承接封驳节点。", chain="none")
    room_end = tp(w, room_e, "北宋元丰五年六月二十五日", "罢，封驳公事归给事中", i, q_end, "办事机构", "建元丰罢房节点。", chain="none")
    chain(w, [room_start, room_end], "按淳化承接与元丰罢归排序。")
    rel(w, silver, room_start, "上下级机构", i, q_start, "银台司兼领封驳公事。")
    geishi_e = entity(w, "给事中", "官职", i, q_end, "原文明载封驳房罢后公事归给事中。")
    geishi = tp(w, geishi_e, "北宋元丰五年六月二十五日", "接回门下封驳公事", i, q_end, "职事官", "建元丰接回事权节点。")
    rel(w, room_end, geishi, "前后演变", i, q_end, "银台司封驳房罢后封驳公事归给事中。")
    w.commit()


def entry219():
    i = 219
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, F[i]["title"], "官职", i, z, "辞典明载为较低资序者所称差遣。")
    tid = tp(w, eid, "未知", "资序未及两省官者称勾当，职掌同知通进银台兼封驳公事", i, z, "差遣", "原文无时间，建真实无年节点。")
    for office in ("银台司", "通进司"):
        office_tp = node(w, office, "北宋淳化四年八月十八日", "机构")[1]
        rel(w, office_tp, tid, "编制隶属", i, z, f"勾当差遣掌领{office}相关公事。", staff_type="官")
    w.commit()


def entry220():
    i = 220
    q_head = q(i, "官署名。隶银台司。")
    q_start = q(i, "北宋熙宁三年八月二十七日始设")
    q_duty = q(i, "审阅、处理经进奏院投进银台司的全国各地奏状文字")
    w = W(i)
    eid = entity(w, "看详银台司文字所", "机构", i, q_head, "辞典明载为隶银台司官署。")
    tid = tp(w, eid, "北宋熙宁三年八月二十七日", "始设，审阅处理投进银台司的奏状文字", i, q_start, "官署名", "建熙宁始设节点。")
    cite(w, "Timepoints", tid, i, q_duty, "补充职掌。", note="职掌")
    silver = node(w, "银台司", "北宋淳化四年八月十八日", "机构")[1]
    rel(w, silver, tid, "上下级机构", i, q_head, "看详银台司文字所隶银台司。")
    w.commit()


def membership_stage(w, title, i, quotation):
    eid = room(w, title, i, quotation, "二十五房名单明确列此机构。")
    existing = w.find_timepoint(eid, "北宋末、南宋初")
    if existing:
        return existing
    stage = tp(w, eid, "北宋末、南宋初", "为枢密院二十五房之一", i, quotation, "办事机构", "建二十五房成员状态。", chain="none")
    end = w.find_timepoint(eid, "南宋乾道六年二月")
    if end:
        insert_before(w, eid, stage, end, "把二十五房阶段插入乾道并房节点之前。")
    else:
        others = w.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id=? AND id<>? AND succ_id IS NULL ORDER BY id DESC LIMIT 1",
            (eid, stage),
        ).fetchone()
        if others:
            w.relink(others[0], "把二十五房阶段接到既有链尾。", succ_id=stage)
            w.relink(stage, "把二十五房阶段接到既有链尾。", prev_id=others[0])
    return stage


def relations202():
    i = 202
    z = F[i]["text"]
    w = W(i)
    group = node(w, "枢密院二十五房", "北宋末、南宋初", "机构")[1]
    group_end = node(w, "枢密院二十五房", "南宋乾道六年", "机构")[1]
    exact_members = {
        "枢密院机速房": "南宋建炎四年六月",
        "枢密院小吏房": "北宋元祐",
        "枢密院河北房": "南宋绍兴五年十二月",
        "枢密院支马房": "北宋元祐",
        "枢密院写宣房": "南宋初",
    }
    names = (
        "枢密院兵籍房", "枢密院机速房", "枢密院教阅房", "枢密院揭贴房", "枢密院赏功房",
        "枢密院在京房", "枢密院支差房", "枢密院河西房", "枢密院民兵房", "枢密院大吏房",
        "枢密院小吏房", "枢密院河北房", "枢密院吏房", "枢密院知杂房", "枢密院广西房",
        "枢密院宣旨房", "枢密院支马房", "枢密院写宣房", "枢密院院杂司", "枢密院生事房",
        "枢密院内降房", "枢密院实封房", "枢密院发递房", "枢密院架阁库", "枢密院印司",
    )
    for title in names:
        if title in exact_members:
            member = node(w, title, exact_members[title], "机构")[1]
        else:
            member = membership_stage(w, title, i, z)
        rel(w, group, member, "统称与实例", i, z, f"二十五房总条明确把{title}列为构成实例。")
    five = node(w, "枢密院五房", "南宋乾道六年", "机构")[1]
    rel(w, group_end, five, "前后演变", i, z, "二十五房于乾道六年省并为五房。")
    misc_e = w.find_entity("枢密院院杂司", "机构")
    assert misc_e
    misc_stage = w.find_timepoint(misc_e, "北宋末、南宋初")
    misc_end = tp(w, misc_e, "南宋乾道六年", "二十五房省并后保留院杂司", i, z, "办事机构", "建乾道保留节点。", chain="none")
    chain(w, [misc_stage, misc_end], "按二十五房时期与乾道保留排序。")
    rel(w, group_end, misc_end, "前后演变", i, z, "二十五房省并后形成五房及院杂司格局。")
    w.commit()


def main():
    entry201(); entry202(); entry203(); entry204(); entry205()
    entry206(); entry207(); entry208(); entry209(); entry210()
    entry211(); entry212(); entry213(); entry214(); entry215()
    entry216(); entry217(); entry218(); entry219(); entry220()
    relations202()


if __name__ == "__main__":
    main()
