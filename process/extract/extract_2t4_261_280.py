#!/usr/bin/env python3
"""提取 chapter2t4 第261–280条：枢密院吏人及三省枢密院合署局官。"""
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
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "all": "\n".join(
            [row[2] or ""]
            + [str(v) for k, v in fields.items() if not k.startswith("_")]
        ),
    }


F = {i: load(i) for i in range(261, 281)}


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


def first_node(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, f"缺实体：{title}"
    row = w.conn.execute(
        "SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (eid,)
    ).fetchone()
    assert row, f"{title} 无时间点"
    return eid, row[0]


def chain(w, tids, decision):
    for pos, tid in enumerate(tids):
        w.relink(
            tid, decision,
            prev_id=tids[pos - 1] if pos else None,
            succ_id=tids[pos + 1] if pos + 1 < len(tids) else None,
        )


def ensure_sansheng(w, i, time, quotation, event="与枢密院共同置属官、库局"):
    eid = entity(w, "三省", "机构", quotation, "原文明载三省与枢密院共同构成制度主体。")
    return tp(w, eid, time, event, i, quotation, "中央机构", f"建三省{time}承载节点。")


def entry261():
    i = 261
    q_head = q(i, "大程官 给使名。隶枢密院承旨司")
    q_source = q(i, "五代后蜀已有枢密院大程官之设")
    q_duty = q(i, "收发枢密院承旨司诸房文书。十分之七大程官，为它司外借供差")
    w = W(i)
    eid = w.find_entity("大程官", "官职"); assert eid
    early = tp(w, eid, "五代后蜀", "已有枢密院大程官之设", i, q_source, "给使", "建五代后蜀职源节点。", chain="head")
    song = node(w, "大程官", "宋代", "官职")[1]
    cite(w, "Timepoints", song, i, q_head, "专条补证大程官为隶承旨司给使。")
    cite(w, "Timepoints", song, i, q_duty, "补充收发文书及外借供差职掌。", note="职掌")
    office = first_node(w, "枢密院承旨司", "机构")[1]
    rel(w, office, song, "编制隶属", i, q_head, "大程官隶枢密院承旨司。", staff_type="给使")
    assert early
    w.commit()


def entry262():
    i = 262
    q_early = q(i, "枢密院吏人，宋初有逐房副承旨、主事、令史、书令史。宋初，主事以下吏人隶银台司")
    q_later = q(i, "后逐步增加名目，计有守阙主事、守阙书令史、正名贴房、守阙贴房、法司贴司、法司、写宣命等等")
    w = W(i)
    ge = entity(w, "枢密院吏人", "官职", F[i]["text"], "辞典以专条列枢密院吏人名目。")
    early = tp(w, ge, "宋初", "有逐房副承旨、主事、令史、书令史", i, q_early, "吏人总称", "建宋初吏人总称节点。", chain="none")
    later = tp(w, ge, "宋代（未载具体年月）", "后逐步增加守阙主事等名目", i, q_later, "吏人总称", "建后续增置名目节点。", chain="none")
    chain(w, [early, later], "按宋初与后续增置连接枢密院吏人节点。")
    initial = ("枢密院逐房副承旨", "主事", "令史", "书令史")
    subsequent = ("守阙主事", "守阙书令史", "贴房", "守阙贴房", "法司贴司", "法司", "写宣命")
    initial_nodes = {}
    for title in initial:
        eid = entity(w, title, "官职", q_early, f"宋初枢密院吏人明确列{title}。")
        time = (
            "宋初" if title == "枢密院逐房副承旨"
            else "宋代（枢密院，未载具体年月）"
        )
        mt = tp(w, eid, time, "枢密院吏职", i, q_early, "吏职", f"建{title}枢密院吏职节点。", chain="head")
        initial_nodes[title] = mt
        rel(w, early, mt, "统称与实例", i, q_early, f"宋初枢密院吏人包括{title}。")
    for title in subsequent:
        eid = entity(w, title, "官职", q_later, f"后续枢密院吏人名目明确列{title}。")
        time = "宋代（枢密院，未载具体年月）"
        mt = tp(w, eid, time, "后增枢密院吏职", i, q_later, "吏职", f"建{title}枢密院吏职节点。", chain="head")
        rel(w, later, mt, "统称与实例", i, q_later, f"后续枢密院吏人名目包括{title}。")
    silver = node(w, "银台司", "北宋淳化四年八月十八日", "机构")[1]
    for title in ("主事", "令史", "书令史"):
        rel(w, silver, initial_nodes[title], "编制隶属", i, q_early, f"宋初{title}属主事以下吏人，隶银台司。", staff_type="吏")
    w.commit()


def entry263():
    i = 263; z = F[i]["all"]
    q_group = q(i, "枢密院承旨司兵、吏、户、礼房副承旨总名。")
    q_staff = q(i, "共五人。其中枢密院兵房副承旨二人，吏、户、礼房兵房副承旨各一人")
    q_grade = q(i, "从八品，位于逐房主事之上，为承旨司吏人之首")
    w = W(i)
    ge = w.find_entity("枢密院逐房副承旨", "官职"); assert ge
    gt = node(w, "枢密院逐房副承旨", "宋初", "官职")[1]
    cite(w, "Timepoints", gt, i, z, "专条补充职掌、总额与品位。", note="职掌、编制、品位")
    office = first_node(w, "枢密院承旨司", "机构")[1]
    rel(w, office, gt, "编制隶属", i, q_staff, "承旨司逐房副承旨共五人。", staff_quota=5, staff_type="吏")
    for room, quota in (("兵", 2), ("吏", 1), ("户", 1), ("礼", 1)):
        title = f"枢密院{room}房副承旨"
        eid = entity(w, title, "官职", q_staff, f"编制明确列{title}。")
        tid = tp(w, eid, "宋代（未载具体年月）", f"承旨司{room}房副承旨，编制{quota}人", i, q_staff, "吏职", f"建{title}节点。")
        cite(w, "Timepoints", tid, i, q_grade, "补充逐房副承旨从八品且为承旨司吏人之首。", note="品位")
        rel(w, gt, tid, "统称与实例", i, q_group, f"逐房副承旨总名包括{title}。")
        rel(w, office, tid, "编制隶属", i, q_staff, f"承旨司置{title}{quota}人。", staff_quota=quota, staff_type="吏")
    w.commit()


def simple_clerk(i, title, event, quotation=None, grade=None):
    z = quotation or F[i]["text"]
    w = W(i)
    eid = w.find_entity(title, "官职")
    if not eid:
        eid = entity(w, title, "官职", z, "辞典明载为枢密院吏职名。")
    time = "宋代（枢密院，未载具体年月）"
    tid = tp(w, eid, time, event, i, z, "吏职", f"建{title}枢密院吏职节点。", chain="head")
    if grade:
        cite(w, "Timepoints", tid, i, z, f"补充{title}{grade}。", note="品位")
    parent = node(w, "枢密院", "宋初", "机构")[1]
    rel(w, parent, tid, "编制隶属", i, z, f"{title}为枢密院吏职。", staff_type="吏")
    w.commit()


def entry264():
    simple_clerk(264, "主事", "分管枢密院诸房职事及发放文字", grade="从八品")


def entry265():
    simple_clerk(265, "守阙主事", "候补主事")


def entry266():
    simple_clerk(266, "令史", "依所在房行遣文字", grade="从八品")


def entry267():
    simple_clerk(267, "书令史", "职掌同令史，位次于令史", grade="从八品")


def entry268():
    simple_clerk(268, "守阙书令史", "候补书令史")


def entry269():
    i = 269; z = F[i]["all"]
    q_quota = q(i, "正名贴房二十八人，……守阙贴房二百人。")
    w = W(i)
    eid = w.find_entity("贴房", "官职"); assert eid
    tid = node(w, "贴房", "宋代（枢密院，未载具体年月）", "官职")[1]
    cite(w, "Timepoints", tid, i, F[i]["text"], "专条补充贴房分在各房抄写文字。", note="职掌")
    office = node(w, "枢密院", "宋初", "机构")[1]
    rel(w, office, tid, "编制隶属", i, q_quota, "枢密院正名贴房二十八人；正名为与守阙相对的标识，不另建别名实体。", staff_quota=28, staff_type="吏")
    guard = node(w, "守阙贴房", "宋代（枢密院，未载具体年月）", "官职")[1]
    rel(w, office, guard, "编制隶属", i, q_quota, "枢密院守阙贴房二百人。", staff_quota=200, staff_type="吏")
    cite(w, "Timepoints", tid, i, z, "保留正名与守阙的制度区分，不把正名贴房作为纯别名实体。", note="编制")
    w.commit()


def entry270():
    i = 270; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("法司", "官职"); assert eid
    tid = node(w, "法司", "宋代（枢密院，未载具体年月）", "官职")[1]
    cite(w, "Timepoints", tid, i, z, "专条补充法司掌条令簿册及决断案件。", note="职掌")
    office = first_node(w, "宣旨院", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "法司掌枢密院宣旨院条令簿册。", staff_type="吏")
    w.commit()


def entry271():
    simple_clerk(271, "法司贴司", "掌案牍听差，由试中刑法人充任")


def entry272():
    i = 272; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("写宣命", "官职"); assert eid
    tid = node(w, "写宣命", "宋代（枢密院，未载具体年月）", "官职")[1]
    cite(w, "Timepoints", tid, i, z, "专条补充写宣命书写宣、札等文字。", note="职掌")
    office = node(w, "枢密院写宣房", "南宋初", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "写宣命供职于写宣房。", staff_type="吏")
    w.commit()


def entry273():
    i = 273; z = F[i]["all"]
    q_start = q(i, "古无此称，北宋始置。")
    q_1084 = q(i, "（元丰七年）枢密院昨置五房院，主事以下集居。")
    w = W(i)
    eid = entity(w, "枢密院五房院", "机构", F[i]["text"], "辞典明载为吏廨。")
    tid = tp(w, eid, "北宋元丰七年", "已置，供诸房主事以下吏人集居", i, q_1084, "吏廨", "元丰七年引文明确证明已经设置。")
    cite(w, "Timepoints", tid, i, q_start, "补证五房院为北宋始置。", note="职源")
    parent = node(w, "枢密院", "北宋元丰四年", "机构")[1]
    rel(w, parent, tid, "上下级机构", i, q_1084, "枢密院五房院为枢密院诸房吏人公寓。")
    w.commit()


def entry274():
    i = 274; z = F[i]["text"]; w = W(i)
    eid = entity(w, "同知三省、枢密院", "官职", z, "辞典明载为南宋临时差遣官。")
    tid = tp(w, eid, "南宋建炎初", "临时权差，随隆祐太后从行料理事务", i, z, "差遣官", "建建炎初临时权差节点。")
    san = ensure_sansheng(w, i, "南宋建炎初", z, "临时置同知三省、枢密院随行")
    mi_e = w.find_entity("枢密院", "机构"); assert mi_e
    mi = tp(w, mi_e, "南宋建炎初", "临时置同知三省、枢密院随行", i, z, "官署名", "建枢密院建炎初随行节点。", chain="none")
    before = w.find_timepoint(mi_e, "南宋初"); after = w.find_timepoint(mi_e, "南宋建炎四年六月"); assert before and after
    w.relink(before, "在南宋初后插入建炎初节点。", succ_id=mi)
    w.relink(mi, "把建炎初节点接入枢密院时间链。", prev_id=before, succ_id=after)
    w.relink(after, "在建炎四年前插入建炎初节点。", prev_id=mi)
    rel(w, san, tid, "编制隶属", i, z, "同知三省、枢密院为三省临时差遣。", staff_type="官")
    rel(w, mi, tid, "编制隶属", i, z, "同知三省、枢密院为枢密院临时差遣。", staff_type="官")
    w.commit()


def entry275():
    i = 275; z = F[i]["text"]; w = W(i)
    eid = entity(w, "三省、枢密院激赏库", "机构", z, "辞典明载为京局。")
    tid = tp(w, eid, "南宋初", "创置，用于对金战争犒赏及后续各项支付", i, z, "京局", "建南宋初创置节点。")
    san = ensure_sansheng(w, i, "南宋初", z)
    mi = node(w, "枢密院", "南宋初", "机构")[1]
    rel(w, san, tid, "上下级机构", i, z, "激赏库由三省、枢密院共同桩管。")
    rel(w, mi, tid, "上下级机构", i, z, "激赏库由三省、枢密院共同桩管。")
    w.commit()


def entry276():
    i = 276; z = F[i]["text"]
    q_change = q(i, "初为御营司激赏酒库。建炎四年六月罢御营使司，激赏酒库归隶三省枢密院")
    w = W(i)
    old_e = entity(w, "御营司激赏酒库", "机构", q_change, "原文明载其初名及所属。")
    old = tp(w, old_e, "南宋建炎四年六月", "御营使司罢，转归三省枢密院", i, q_change, "京局", "建原库归并终结节点。")
    new_e = entity(w, "三省枢密院激赏酒库", "机构", z, "辞典明载为京局。")
    new = tp(w, new_e, "南宋建炎四年六月", "由御营司激赏酒库转隶而来", i, q_change, "京局", "建转隶后的激赏酒库节点。")
    rel(w, old, new, "前后演变", i, q_change, "御营司激赏酒库转为三省枢密院激赏酒库。")
    san = ensure_sansheng(w, i, "南宋建炎四年六月", q_change)
    mi = node(w, "枢密院", "南宋建炎四年六月", "机构")[1]
    rel(w, san, new, "上下级机构", i, q_change, "激赏酒库归隶三省。")
    rel(w, mi, new, "上下级机构", i, q_change, "激赏酒库归隶枢密院。")
    w.commit()


def entry277():
    i = 277; z = F[i]["text"]; w = W(i)
    eid = entity(w, "三省枢密院架阁库", "机构", z, "辞典明载为京局。")
    tid = tp(w, eid, "南宋（未载具体年月）", "三省、枢密院文案贮存所，共四库十六间房", i, z, "京局", "据行在所录语境建南宋节点。")
    san = ensure_sansheng(w, i, "南宋", z)
    san_e = w.find_entity("三省", "机构"); assert san_e
    chain(w, [w.find_timepoint(san_e, time) for time in ("南宋", "南宋初", "南宋建炎初", "南宋建炎四年六月")], "按南宋通期、南宋初、建炎初、建炎四年重排三省时间链。")
    mi = node(w, "枢密院", "南宋", "机构")[1]
    rel(w, san, tid, "上下级机构", i, z, "架阁库为三省文案贮存所。")
    rel(w, mi, tid, "上下级机构", i, z, "架阁库为枢密院文案贮存所。")
    w.commit()


def entry278():
    i = 278; z = F[i]["all"]
    q_date = q(i, "一员，嘉定八年置。")
    w = W(i)
    eid = entity(w, "主管三省、枢密院架阁文字", "官职", F[i]["text"], "辞典明载为监当官。")
    tid = tp(w, eid, "南宋嘉定八年", "置一员，掌架阁库文牍及库房修葺", i, q_date, "监当官", "建嘉定八年始置节点。")
    cite(w, "Timepoints", tid, i, F[i]["text"], "补充掌管文牍与修葺职掌。", note="职掌")
    office = node(w, "三省枢密院架阁库", "南宋（未载具体年月）", "机构")[1]
    rel(w, office, tid, "编制隶属", i, q_date, "架阁库置主管文字一员。", staff_quota=1, staff_type="官")
    w.commit()


def entry279():
    i = 279; z = F[i]["text"]; w = W(i)
    eid = entity(w, "监三省、枢密院门", "官职", z, "辞典明载为南宋差遣官。")
    tid = tp(w, eid, "南宋", "看守三省、枢密院门，伺察出入人员", i, z, "差遣官", "建南宋监门节点。")
    san = node(w, "三省", "南宋", "机构")[1]
    mi = node(w, "枢密院", "南宋", "机构")[1]
    rel(w, san, tid, "编制隶属", i, z, "监三省、枢密院门看守三省门禁。", staff_type="官")
    rel(w, mi, tid, "编制隶属", i, z, "监三省、枢密院门看守枢密院门禁。", staff_type="官")
    w.commit()


def entry280():
    i = 280; z = F[i]["all"]
    q_head = q(i, "北宋前期，中书门下与枢密院为中央最高政府与军事机构，对持文武二柄。二司常连称")
    q_alias = q(i, "宋初，循唐、五代之制，置枢密院，与中书对持文武二柄，号为‘二府’。")
    w = W(i)
    ge = entity(w, "中书门下、枢密院", "机构", q_head, "辞典将两中央机构作为制度性连称记载。")
    gt = tp(w, ge, "北宋前期", "中书门下与枢密院对持文武二柄的连称", i, q_head, "中央机构总称", "建北宋前期连称节点。")
    middle = node(w, "中书门下", "宋前期", "机构")[1]
    mi = node(w, "枢密院", "宋初", "机构")[1]
    rel(w, gt, middle, "统称与实例", i, q_head, "中书门下、枢密院连称包括中书门下。")
    rel(w, gt, mi, "统称与实例", i, q_head, "中书门下、枢密院连称包括枢密院。")
    cite(w, "Timepoints", gt, i, q_alias, "别名字段补充二府称谓；纯别名不另建实体。", note="别名")
    w.commit()


def main():
    entry261(); entry262(); entry263(); entry264(); entry265()
    entry266(); entry267(); entry268(); entry269(); entry270()
    entry271(); entry272(); entry273(); entry274(); entry275()
    entry276(); entry277(); entry278(); entry279(); entry280()


if __name__ == "__main__":
    main()
