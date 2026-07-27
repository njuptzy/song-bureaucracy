#!/usr/bin/env python3
"""提取 chapter2t4 第181–200条：承旨属官与枢密院诸房。"""
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


F = {i: load(i) for i in range(181, 201)}


def q(i, text):
    assert text in F[i]["all"], f"#{i} 不含：{text}"
    return text


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def C(i):
    return f"《宋代官制辞典》第{F[i]['page']}页“{F[i]['title']}”条"


def cite(w, table, rid, i, quotation, decision, **kwargs):
    return w.citation(table, rid, C(i), quotation, decision, **kwargs)


def entity(w, title, type_, quotation, decision):
    return w.entity(title, type_, decision, quotation=quotation)


def timepoint(w, eid, time, event, i, quotation, category, decision, **kwargs):
    tid = w.timepoint(
        eid, time, event, decision, quotation, attr_category=category, **kwargs
    )
    cite(w, "Timepoints", tid, i, quotation, decision)
    return tid


def relationship(w, source, target, kind, i, quotation, decision, **kwargs):
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


def room_tp(w, title, time, event, i, quotation, decision):
    eid = entity(w, title, "机构", quotation, decision)
    tid = timepoint(w, eid, time, event, i, quotation, "办事机构", decision, chain="none")
    return eid, tid


def merge_into(w, source_title, target_tid, i, quotation, target_title):
    _, source_tid = room_tp(
        w,
        source_title,
        "南宋乾道六年二月",
        f"并入{target_title}",
        i,
        quotation,
        f"原文明载乾道六年将{source_title}并入{target_title}，建终结节点。",
    )
    relationship(
        w,
        source_tid,
        target_tid,
        "前后演变",
        i,
        quotation,
        f"{source_title}于乾道六年并入{target_title}。",
    )
    return source_tid


def parent_node(w, period):
    return node(w, "枢密院", period, "机构")[1]


def entry181():
    i = 181
    q_type = q(i, "职事官。")
    q_start = q(i, "真宗咸平元年(998)十月始设")
    q_duty = q(i, "佐都承旨理院务事，如都承旨缺，则代掌本院事。")
    q_grade = q(i, "正六品。")
    q_quota = q(i, "都承旨、副都承旨或并置，或止置一员")
    w = W(i)
    eid = w.find_entity("枢密院副都承旨", "官职")
    assert eid
    start = timepoint(
        w, eid, "北宋咸平元年十月", "始设，佐都承旨理院务，正六品", i,
        q_start, "职事官", "建副都承旨始设节点。", attr_grade="正六品", chain="none",
    )
    cite(w, "Timepoints", start, i, q_type, "补充职事官性质。", note="官类")
    cite(w, "Timepoints", start, i, q_duty, "补充职掌。", note="职掌")
    cite(w, "Timepoints", start, i, q_grade, "补充官品。", note="官品")
    cite(w, "Timepoints", start, i, q_quota, "补充与都承旨不备置的编制规则。", note="编制")
    undated = w.find_timepoint(eid, "未知")
    assert undated
    chain(w, [start, undated], "按咸平始设与无统一时间的通制节点排序。")
    office = node(w, "枢密院承旨司", "北宋熙宁二年八月十二日", "机构")[1]
    relationship(
        w, office, start, "编制隶属", i, q_duty,
        "副都承旨佐都承旨处理承旨司院务。", staff_type="官",
    )
    w.commit()


def entry182():
    i = 182
    z = F[i]["text"]
    w = W(i)
    eid = w.find_entity("枢密院副承旨", "官职")
    assert eid
    tid = w.find_timepoint(eid, "未知")
    assert tid
    row = w.conn.execute(
        "SELECT attr_category,attr_grade FROM Timepoints WHERE id=?", (tid,)
    ).fetchone()
    if row != ("吏人职", "正七品"):
        w.conn.execute(
            "UPDATE Timepoints SET attr_category='吏人职',attr_grade='正七品' WHERE id=?",
            (tid,),
        )
        w._br("Timepoints", tid, "据本专条将官类明确为吏人职，并补正七品。")
    cite(w, "Timepoints", tid, i, z, "补充副承旨的吏人职性质、职掌、罕置与品级。")
    office = node(w, "枢密院承旨司", "北宋熙宁二年八月十二日", "机构")[1]
    rid = relationship(
        w, office, tid, "编制隶属", i, z,
        "副承旨为枢密院吏人职，通掌本院诸房公事。", staff_type="吏",
    )
    staff_type = w.conn.execute(
        "SELECT staff_type FROM Relationships WHERE id=?", (rid,)
    ).fetchone()[0]
    if staff_type != "吏":
        w.conn.execute("UPDATE Relationships SET staff_type='吏' WHERE id=?", (rid,))
        w._br("Relationships", rid, "据本专条‘枢密院吏人职’将 staff_type 从官改为吏。")
    w.commit()


def entry183():
    i = 183
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "辞典明载为枢密院吏人职。")
    tid = timepoint(
        w, eid, "未知", "佐都承旨、副都承旨在后殿祗应、侍立宣旨，正八品", i,
        z, "吏人职", "原文无设置时间，建真实的无年承载节点。", attr_grade="正八品",
    )
    office = node(w, "枢密院承旨司", "北宋熙宁二年八月十二日", "机构")[1]
    relationship(
        w, office, tid, "编制隶属", i, z,
        "诸房副承旨为承旨司吏人职。", staff_type="吏",
    )
    w.commit()


def entry184():
    i = 184
    q_early = q(i, "宋初枢密院分四房（兵、吏、户、礼），熙宁四年十月增置刑房，共为五房")
    q_late = q(i, "乾道六年，枢密院二十五房，合并为五房，以兵、吏、礼、刑、工房为名")
    w = W(i)
    eid = entity(w, "枢密院五房", "机构", q_early, "辞典把五房作为枢密院办事机构组合。")
    xining = timepoint(
        w, eid, "北宋熙宁四年十月", "在宋初四房基础上增刑房，合为五房", i,
        q_early, "办事机构总名", "建熙宁五房形成节点。", chain="none",
    )
    qiandao = timepoint(
        w, eid, "南宋乾道六年", "二十五房合并为兵、吏、礼、刑、工五房", i,
        q_late, "办事机构总名", "建乾道五房重组节点。", chain="none",
    )
    chain(w, [xining, qiandao], "按熙宁增房与乾道重组排序。")
    relationship(
        w, parent_node(w, "北宋熙宁元年"), xining, "上下级机构", i, q_early,
        "五房为枢密院内部办事机构组合。",
    )
    relationship(
        w, parent_node(w, "南宋绍兴七年"), qiandao, "上下级机构", i, q_late,
        "乾道重组后的五房仍属枢密院。",
    )
    w.commit()


def entry185():
    i = 185
    q_early = q(i, "宋初置。掌兵马名籍及卒校迁补、修筑城垒、防戍战守之事。")
    q_late = q(i, "南宋乾道六年（1170）二月，以兵籍房（部分）、机速房（部分）、教阅房、揭贴房、赏功房（部分）、支差房（部分）、河西房（部分）及民兵诸房并入")
    w = W(i)
    eid = entity(w, "枢密院兵房", "机构", F[i]["text"], "辞典明载为枢密院办事机构。")
    early = timepoint(w, eid, "宋初", "始置，掌兵籍、卒校迁补及防戍战守", i, q_early, "办事机构", "建宋初兵房节点。", chain="none")
    late = timepoint(w, eid, "南宋乾道六年二月", "并入相关诸房事务后重组", i, q_late, "办事机构", "建乾道并房节点。", chain="none")
    xining = w.find_timepoint(eid, "北宋熙宁四年十月")
    chain(w, [early] + ([xining] if xining else []) + [late], "按宋初、熙宁五房阶段与乾道重组排序。")
    relationship(w, parent_node(w, "宋初"), early, "上下级机构", i, F[i]["text"], "兵房为枢密院办事机构。")
    for source in ("枢密院兵籍房", "枢密院机速房", "枢密院教阅房", "枢密院揭贴房", "枢密院赏功房", "枢密院支差房", "枢密院河西房", "枢密院民兵房"):
        merge_into(w, source, late, i, q_late, "枢密院兵房")
    w.commit()


def entry186():
    i = 186
    q_early = q(i, "宋初置。掌东、西阁门使、副使武臣以上迁补之名籍，王公将帅迎授恩命及盗贼之事。")
    q_yuan = q(i, "神宗元丰新制，掌差遣将领、武臣知州、知军、路分都监以上及差遣内侍官的文书")
    q_late = q(i, "南宋乾道六年二月，以在京房（部分）、大吏房、小吏房（部分）及支差房（部分）并入")
    w = W(i)
    eid = entity(w, "枢密院吏房", "机构", F[i]["text"], "辞典明载为枢密院办事机构。")
    early = timepoint(w, eid, "宋初", "始置，掌武臣迁补名籍及相关事务", i, q_early, "办事机构", "建宋初吏房节点。", chain="none")
    yuan = timepoint(w, eid, "北宋元丰新制", "改掌将领、武臣及内侍差遣文书", i, q_yuan, "办事机构", "建元丰职掌变更节点。", chain="none")
    late = timepoint(w, eid, "南宋乾道六年二月", "并入相关诸房事务后重组", i, q_late, "办事机构", "建乾道并房节点。", chain="none")
    xining = w.find_timepoint(eid, "北宋熙宁四年十月")
    chain(w, [early] + ([xining] if xining else []) + [yuan, late], "按宋初、熙宁、元丰、乾道排序。")
    relationship(w, parent_node(w, "宋初"), early, "上下级机构", i, F[i]["text"], "吏房为枢密院办事机构。")
    for source in ("枢密院在京房", "枢密院大吏房", "枢密院小吏房", "枢密院支差房"):
        merge_into(w, source, late, i, q_late, "枢密院吏房")
    w.commit()


def entry187():
    i = 187
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "枢密院户房", "机构", z, "辞典明载为枢密院办事机构。")
    early = timepoint(w, eid, "宋初", "始置，掌金谷、马料刍粮出纳", i, z, "办事机构", "建宋初户房节点。", chain="none")
    end = timepoint(w, eid, "北宋元丰新制", "废罢", i, z, "办事机构", "建元丰废罢节点。", chain="none")
    xining = w.find_timepoint(eid, "北宋熙宁四年十月")
    chain(w, [early] + ([xining] if xining else []) + [end], "按宋初、熙宁五房阶段与元丰废罢排序。")
    relationship(w, parent_node(w, "宋初"), early, "上下级机构", i, z, "户房为枢密院办事机构。")
    w.commit()


def entry188():
    i = 188
    q_early = q(i, "宋初置，掌礼仪与外交往来事。")
    q_late = q(i, "乾道六年二月，以河北房、河西房（部分）、支差房（部分）、吏房、知杂房（部分）及兵籍（部分）、时政记等事务并入")
    w = W(i)
    eid = entity(w, "枢密院礼房", "机构", F[i]["text"], "辞典明载为枢密院办事机构。")
    early = timepoint(w, eid, "宋初", "始置，掌礼仪与外交往来", i, q_early, "办事机构", "建宋初礼房节点。", chain="none")
    late = timepoint(w, eid, "南宋乾道六年二月", "并入相关诸房事务后重组", i, q_late, "办事机构", "建乾道并房节点。", chain="none")
    xining = w.find_timepoint(eid, "北宋熙宁四年十月")
    chain(w, [early] + ([xining] if xining else []) + [late], "按宋初、熙宁五房阶段与乾道重组排序。")
    relationship(w, parent_node(w, "宋初"), early, "上下级机构", i, F[i]["text"], "礼房为枢密院办事机构。")
    for source in ("枢密院河北房", "枢密院河西房", "枢密院支差房", "枢密院吏房", "枢密院知杂房", "枢密院兵籍房"):
        merge_into(w, source, late, i, q_late, "枢密院礼房")
    w.commit()


def entry189():
    i = 189
    q_start = q(i, "神宗熙宁四年（1071）十月创置。掌兵官、将校、使臣、蕃官及军兵的断案、功赏、叙复及迁补。")
    q_late = q(i, "乾道六年二月，以河西房（部分）小吏房（部分）、广西房、知杂房（部分）、在京房（部分）及宣旨库并入")
    w = W(i)
    eid = entity(w, "枢密院刑房", "机构", F[i]["text"], "辞典明载为枢密院办事机构。")
    start = timepoint(w, eid, "北宋熙宁四年十月", "创置，掌军职人员断案、功赏与迁补", i, q_start, "办事机构", "建熙宁创置节点。", chain="none")
    late = timepoint(w, eid, "南宋乾道六年二月", "并入相关诸房与宣旨库事务后重组", i, q_late, "办事机构", "建乾道并房节点。", chain="none")
    chain(w, [start, late], "按熙宁创置与乾道重组排序。")
    relationship(w, parent_node(w, "北宋熙宁元年"), start, "上下级机构", i, F[i]["text"], "刑房为枢密院办事机构。")
    for source in ("枢密院河西房", "枢密院小吏房", "枢密院广西房", "枢密院知杂房", "枢密院在京房", "宣旨库"):
        merge_into(w, source, late, i, q_late, "枢密院刑房")
    w.commit()


def entry190():
    i = 190
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "枢密院十二房", "机构", z, "辞典明确列出元丰改制后的十二房。")
    tid = timepoint(w, eid, "北宋元丰改制后", "五房增改为十二房，分掌边防机要军政", i, z, "办事机构总名", "建元丰后十二房节点。")
    relationship(w, parent_node(w, "北宋元丰四年"), tid, "上下级机构", i, z, "十二房为枢密院办事机构组合。")
    w.commit()


def entry191():
    i = 191
    z = F[i]["text"]
    w = W(i)
    north_e, start = room_tp(w, "枢密院北面房", "北宋元丰改制时", "始置，掌河北、河东边防及对辽事务", i, z, "建元丰北面房节点。")
    renamed = timepoint(w, north_e, "南宋绍兴五年十二月", "改为河北房", i, z, "办事机构", "建绍兴改名终结节点。", chain="none")
    hebei_e = entity(w, "枢密院河北房", "机构", z, "原文明载北面房改为河北房。")
    hebei_start = timepoint(w, hebei_e, "南宋绍兴五年十二月", "由北面房改置", i, z, "办事机构", "建河北房改名后继节点。", chain="none")
    hebei_end = timepoint(w, hebei_e, "南宋乾道六年二月", "并入礼房", i, z, "办事机构", "复用乾道并房节点。", chain="none")
    chain(w, [start, renamed], "按元丰始置与绍兴改名排序。")
    chain(w, [hebei_start, hebei_end], "按绍兴改名与乾道并入排序。")
    relationship(w, renamed, hebei_start, "前后演变", i, z, "北面房于绍兴五年改为河北房。")
    target = node(w, "枢密院礼房", "南宋乾道六年二月", "机构")[1]
    relationship(w, hebei_end, target, "前后演变", i, z, "河北房于乾道六年并入礼房。")
    relationship(w, parent_node(w, "北宋元丰四年"), start, "上下级机构", i, z, "北面房为枢密院办事机构。")
    w.commit()


def simple_room(i, title, start_time, start_event, merges, cite_merges=True):
    z = F[i]["text"]
    w = W(i)
    eid, start = room_tp(w, title, start_time, start_event, i, z, f"建{title}始置与职掌节点。")
    ids = [start]
    if merges:
        end = w.find_timepoint(eid, "南宋乾道六年二月")
        assert end, f"{title} 缺乾道并房节点"
        ids.append(end)
        if cite_merges:
            cite(w, "Timepoints", end, i, z, f"本专条补证{title}乾道并房。")
            for target_title in merges:
                target = node(w, target_title, "南宋乾道六年二月", "机构")[1]
                relationship(w, end, target, "前后演变", i, z, f"{title}于乾道六年并入{target_title}。")
    chain(w, ids, f"按{title}始置与乾道并房排序。")
    relationship(w, parent_node(w, "北宋元丰四年"), start, "上下级机构", i, z, f"{title}为枢密院办事机构。")
    w.commit()


def entry192():
    simple_room(192, "枢密院河西房", "北宋元丰改制时", "始置，掌陕西等地吏卒、西界边防及蕃官", ("枢密院兵房", "枢密院礼房", "枢密院刑房"))


def entry193():
    simple_room(193, "枢密院支差房", "北宋元丰改制时", "始置，掌军队调发、相关路分边防吏卒及选补", ("枢密院兵房", "枢密院吏房", "枢密院礼房"))


def entry194():
    simple_room(194, "枢密院在京房", "北宋元丰改制时", "始置，掌禁军、兵器及相关路分边防吏卒", ("枢密院兵房", "枢密院吏房", "枢密院刑房", "枢密院工房"))


def entry195():
    simple_room(195, "枢密院教阅房", "北宋元丰改制时", "始置，掌教练、边防、阙额俸给及驿传递铺", ("枢密院兵房",))


def entry196():
    # 本条不载乾道并房；终结节点及演变关系仅由 #189 的明确原文支撑。
    simple_room(196, "枢密院广西房", "北宋元丰改制时", "始置，掌募兵、捕盗赏罚及相关路分边防吏卒", ("枢密院刑房",), cite_merges=False)


def entry197():
    simple_room(197, "枢密院兵籍房", "北宋元丰改制时", "始置，掌将官、禁兵差发及卫军选补文书", ("枢密院兵房", "枢密院礼房", "枢密院刑房"))


def entry198():
    simple_room(198, "枢密院民兵房", "北宋元丰改制时", "始置，掌三路保甲、弓箭手", ("枢密院兵房",))


def entry199():
    simple_room(199, "枢密院知杂房", "北宋元丰改制时", "始置，掌本院杂务", ("枢密院礼房", "枢密院刑房"))


def entry200():
    i = 200
    z = F[i]["text"]
    w = W(i)
    eid, start = room_tp(w, "枢密院支马房", "北宋元祐", "创置，掌内外马政及相关监牧事务", i, z, "建元祐支马房创置节点。")
    end = timepoint(w, eid, "南宋乾道六年二月", "并入工房", i, z, "办事机构", "建乾道并入工房节点。", chain="none")
    chain(w, [start, end], "按元祐创置与乾道并入排序。")
    target = node(w, "枢密院工房", "南宋乾道六年二月", "机构")[1]
    relationship(w, end, target, "前后演变", i, z, "支马房于乾道六年并入工房。")
    relationship(w, parent_node(w, "北宋元丰四年"), start, "上下级机构", i, z, "支马房为枢密院办事机构。")
    w.commit()


def relations184():
    i = 184
    q_early = q(i, "宋初枢密院分四房（兵、吏、户、礼），熙宁四年十月增置刑房，共为五房")
    q_late = q(i, "乾道六年，枢密院二十五房，合并为五房，以兵、吏、礼、刑、工房为名")
    w = W(i)
    group_early = node(w, "枢密院五房", "北宋熙宁四年十月", "机构")[1]
    group_late = node(w, "枢密院五房", "南宋乾道六年", "机构")[1]
    early_times = {
        "枢密院兵房": ["宋初", "北宋熙宁四年十月", "南宋乾道六年二月"],
        "枢密院吏房": ["宋初", "北宋熙宁四年十月", "北宋元丰新制", "南宋乾道六年二月"],
        "枢密院户房": ["宋初", "北宋熙宁四年十月", "北宋元丰新制"],
        "枢密院礼房": ["宋初", "北宋熙宁四年十月", "南宋乾道六年二月"],
        "枢密院刑房": ["北宋熙宁四年十月", "南宋乾道六年二月"],
    }
    for title, times in early_times.items():
        eid = w.find_entity(title, "机构")
        assert eid
        stage = timepoint(w, eid, "北宋熙宁四年十月", "为枢密院五房之一", i, q_early, "办事机构", f"补建熙宁五房成员状态：{title}。", chain="none")
        ids = [w.find_timepoint(eid, t) for t in times]
        chain(w, ids, f"纳入{title}的熙宁五房阶段并按制度顺序重链。")
        relationship(w, group_early, stage, "统称与实例", i, q_early, f"枢密院五房以{title}为构成实例。")
    late_titles = ("枢密院兵房", "枢密院吏房", "枢密院礼房", "枢密院刑房", "枢密院工房")
    for title in late_titles:
        if title == "枢密院工房":
            _, stage = room_tp(w, title, "南宋乾道六年二月", "五房重组后设置", i, q_late, "据乾道五房名单建工房节点。")
        else:
            stage = node(w, title, "南宋乾道六年二月", "机构")[1]
            cite(w, "Timepoints", stage, i, q_late, "补证乾道五房成员状态。")
        relationship(w, group_late, stage, "统称与实例", i, q_late, f"乾道五房以{title}为构成实例。")
    w.commit()


def relations190():
    i = 190
    z = F[i]["text"]
    w = W(i)
    group = node(w, "枢密院十二房", "北宋元丰改制后", "机构")[1]
    member_times = {
        "枢密院北面房": "北宋元丰改制时",
        "枢密院河西房": "北宋元丰改制时",
        "枢密院在京房": "北宋元丰改制时",
        "枢密院教阅房": "北宋元丰改制时",
        "枢密院广西房": "北宋元丰改制时",
        "枢密院兵籍房": "北宋元丰改制时",
        "枢密院民兵房": "北宋元丰改制时",
        "枢密院吏房": "北宋元丰新制",
        "枢密院知杂房": "北宋元丰改制时",
        "枢密院支差房": "北宋元丰改制时",
        "枢密院支马房": "北宋元祐",
    }
    # 小吏房无独立专条，以十二房总条建立元丰后的起点，再接乾道并房节点。
    small_e = entity(w, "枢密院小吏房", "机构", z, "十二房名单明确列小吏房。")
    small_start = timepoint(w, small_e, "北宋元丰改制后", "为枢密院十二房之一", i, z, "办事机构", "建小吏房元丰后状态。", chain="none")
    small_end = w.find_timepoint(small_e, "南宋乾道六年二月")
    assert small_end
    chain(w, [small_start, small_end], "按元丰后十二房与乾道并房排序。")
    member_times["枢密院小吏房"] = "北宋元丰改制后"
    for title, time in member_times.items():
        member = node(w, title, time, "机构")[1]
        relationship(w, group, member, "统称与实例", i, z, f"十二房总条明确把{title}列为构成实例。")
    w.commit()


def main():
    entry181(); entry182(); entry183(); entry184(); entry185()
    entry186(); entry187(); entry188(); entry189(); entry190()
    relations184()
    entry191(); entry192(); entry193(); entry194(); entry195()
    entry196(); entry197(); entry198(); entry199()
    entry200()
    relations190()


if __name__ == "__main__":
    main()
