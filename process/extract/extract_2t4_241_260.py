#!/usr/bin/env python3
"""提取 chapter2t4 第241–260条：枢密院将佐、使臣与给使。"""
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
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "all": "\n".join(
            [row[2] or ""]
            + [str(v) for k, v in fields.items() if not k.startswith("_")]
        ),
    }


F = {i: load(i) for i in range(241, 261)}


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
            tid,
            decision,
            prev_id=tids[pos - 1] if pos else None,
            succ_id=tids[pos + 1] if pos + 1 < len(tids) else None,
        )


def insert_miyuan(w, i, time, event, quotation, prev_time, succ_time):
    eid = w.find_entity("枢密院", "机构")
    assert eid
    existing = w.find_timepoint(eid, time)
    tid = tp(
        w, eid, time, event, i, quotation, "官署名", f"建枢密院{time}制度节点。",
        chain="none",
    )
    if existing:
        return tid
    prev = w.find_timepoint(eid, prev_time)
    succ = w.find_timepoint(eid, succ_time)
    assert prev and succ
    w.relink(prev, f"在{prev_time}后插入{time}枢密院节点。", succ_id=tid)
    w.relink(tid, f"把{time}枢密院节点接入既有链。", prev_id=prev, succ_id=succ)
    w.relink(succ, f"在{succ_time}前插入{time}枢密院节点。", prev_id=tid)
    return tid


def append_miyuan(w, i, time, event, quotation):
    eid = w.find_entity("枢密院", "机构")
    assert eid
    return tp(
        w, eid, time, event, i, quotation, "官署名", f"建枢密院{time}制度节点。"
    )


def entry241():
    i = 241
    q_north = q(i, "北宋枢密院有发兵之权，而无领兵之权，故无将官。")
    q_1134 = q(i, "绍兴四年六月，以神武军、神武副军统制、统领官，并隶枢密院")
    q_1141 = q(i, "绍兴十一年四月，罢淮东、淮西、湖北三大宣抚司，其所属诸军皆冠以“御前”两字，归隶枢密院。")
    w = W(i)
    miyuan = w.find_entity("枢密院", "机构"); assert miyuan
    song = w.find_timepoint(miyuan, "宋初"); assert song
    cite(w, "Timepoints", song, i, q_north, "补证北宋枢密院有发兵权而无将官。", note="职掌")
    p1134 = insert_miyuan(
        w, i, "南宋绍兴四年六月", "神武军、神武副军统制及统领官并隶于此",
        q_1134, "北宋元丰四年", "南宋绍兴七年",
    )
    for title in ("统制", "统领"):
        eid = entity(w, title, "官职", q_1134, f"绍兴四年原文明载{title}官。")
        tid = tp(w, eid, "南宋绍兴四年六月", "神武军、神武副军所设，隶枢密院", i,
                 q_1134, "武官", f"建{title}绍兴四年隶属节点。")
        rel(w, p1134, tid, "编制隶属", i, q_1134, f"神武军、神武副军{title}官并隶枢密院。", staff_type="武官")
    p1141 = insert_miyuan(
        w, i, "南宋绍兴十一年四月", "三宣抚司罢后，其所属诸军冠御前名归隶于此",
        q_1141, "南宋绍兴七年", "南宋绍兴十一年四月后",
    ) if w.find_timepoint(miyuan, "南宋绍兴十一年四月后") else tp(
        w, miyuan, "南宋绍兴十一年四月", "三宣抚司罢后，其所属诸军冠御前名归隶于此",
        i, q_1141, "官署名", "建枢密院绍兴十一年领军节点。", chain="tail"
    )
    for title in ("淮东宣抚司", "淮西宣抚司", "湖北宣抚司"):
        eid = entity(w, title, "机构", q_1141, f"原文明载绍兴十一年罢{title}。")
        tp(w, eid, "南宋绍兴十一年四月", "罢", i, q_1141, "军政机构", f"建{title}罢置节点。")
    assert p1141
    w.commit()


def entry242():
    i = 242; z = F[i]["all"]
    q_xuanhe = q(i, "北宋宣和间（1119—1125）。因西南用兵始置，兵罢则废。")
    q_jianyan = q(i, "建炎元年五月擢王渊为御营司都统制。以都统制名官则起于此")
    q_miyuan = q(i, "枢密院都统制，始置于绍兴四年")
    w = W(i)
    eid = entity(w, "都统制", "官职", F[i]["text"], "辞典明载为武官名。")
    a = tp(w, eid, "北宋宣和间", "因西南用兵始置，兵罢则废", i, q_xuanhe, "武官", "建宣和间初置节点。", chain="none")
    b = tp(w, eid, "南宋建炎元年五月", "以都统制名官自御营司王渊始", i, q_jianyan, "武官", "建建炎名官节点。", chain="none")
    c = tp(w, eid, "南宋绍兴四年", "枢密院始置都统制", i, q_miyuan, "武官", "建枢密院都统制节点。", chain="none")
    chain(w, [a, b, c], "按宣和、建炎、绍兴先后连接都统制节点。")
    parent = node(w, "枢密院", "南宋绍兴四年六月", "机构")[1]
    rel(w, parent, c, "编制隶属", i, q_miyuan, "枢密院绍兴四年始置都统制。", staff_type="武官")
    cite(w, "Timepoints", c, i, z, "补充都统制为本军最高节制官及其位遇。", note="职掌与位遇")
    w.commit()


def entry243():
    i = 243; z = F[i]["text"]
    q_change = q(i, "孝宗隆兴二年三月，罢枢密院副都统制为统制官")
    q_restore = q(i, "度宗咸淳元年复置一员，与枢密院都统制并置，俾赞主帅")
    w = W(i)
    eid = entity(w, "副都统制", "官职", z, "辞典明载为武官名。")
    base = tp(w, eid, "南宋", "低阶武官带都统制权任者称副都统制", i, z, "武官", "建南宋通制节点。", chain="none")
    end = tp(w, eid, "南宋隆兴二年三月", "罢，改为统制官", i, q_change, "武官", "建隆兴改罢节点。", chain="none")
    restore = tp(w, eid, "南宋咸淳元年", "复置一员，与都统制并置以赞主帅", i, q_restore, "武官", "建咸淳复置节点。", chain="none")
    chain(w, [base, end, restore], "按南宋通制、隆兴罢改、咸淳复置排序。")
    tong_e = w.find_entity("统制", "官职"); assert tong_e
    target = tp(w, tong_e, "南宋隆兴二年三月", "由枢密院副都统制改置", i, q_change, "武官", "建隆兴改置统制官节点。")
    rel(w, end, target, "前后演变", i, q_change, "副都统制于隆兴二年改为统制官。")
    w.commit()


def entry244():
    i = 244; z = F[i]["text"]
    q_early = q(i, "南宋初，始有统制之名")
    q_water = q(i, "绍兴元年五月十六日，枢密院置水军统制官")
    w = W(i)
    eid = w.find_entity("统制", "官职"); assert eid
    early = tp(w, eid, "南宋初", "始有统制之名", i, q_early, "武官", "建南宋初始见节点。", chain="none")
    water = tp(w, eid, "南宋绍兴元年五月十六日", "枢密院始置水军统制官", i, q_water, "武官", "建枢府水军统制始置节点。", chain="none")
    s4 = w.find_timepoint(eid, "南宋绍兴四年六月"); lx = w.find_timepoint(eid, "南宋隆兴二年三月")
    assert s4 and lx
    ordered = [early]
    jianyan = w.find_timepoint(eid, "南宋建炎四年六月")
    if jianyan:
        ordered.append(jianyan)
    ordered.extend([water, s4, lx])
    chain(w, ordered, "按南宋初、建炎、绍兴元年、绍兴四年、隆兴排序统制节点。")
    parent = insert_miyuan(
        w, i, "南宋绍兴元年五月十六日", "始置水军统制官", q_water,
        "北宋元丰四年", "南宋绍兴四年六月",
    )
    rel(w, parent, water, "编制隶属", i, q_water, "枢密院始置水军统制官。", staff_type="武官")
    cite(w, "Timepoints", water, i, z, "补充统制高于统领、次于副都统制，属将佐。", note="位序")
    w.commit()


def entry245():
    i = 245; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("统领", "官职"); assert eid
    tid = tp(w, eid, "南宋", "位于正将之上、统制之下，属将佐", i, z, "武官", "建统领南宋制度节点。", chain="head")
    cite(w, "Timepoints", tid, i, z, "记录统领在将佐序列中的位次。", note="位序")
    w.commit()


def entry246():
    i = 246; z = F[i]["text"]
    q_group = q(i, "统制、统领官合称。")
    q_date = q(i, "建炎四年六月戊寅：“诏御前五军改为神武军，御营五军改为神武副军。其将佐并属枢密院。”")
    w = W(i)
    ge = entity(w, "将佐", "官职", q_group, "辞典明确界定为统制、统领官合称。")
    gt = tp(w, ge, "南宋建炎四年六月", "统制、统领官合称，并属枢密院", i, q_date, "武官总称", "建建炎四年将佐节点。")
    for title in ("统制", "统领"):
        eid = w.find_entity(title, "官职"); assert eid
        mt = tp(w, eid, "南宋建炎四年六月", "神武军、神武副军将佐，隶枢密院", i, q_date, "武官", f"建{title}建炎四年成员节点。", chain="head")
        rel(w, gt, mt, "统称与实例", i, q_group, f"将佐为统制、统领官合称，包含{title}。")
        ordered_times = (
            ("南宋初", "南宋建炎四年六月", "南宋绍兴元年五月十六日", "南宋绍兴四年六月", "南宋隆兴二年三月")
            if title == "统制" else
            ("南宋", "南宋建炎四年六月", "南宋绍兴四年六月")
        )
        chain(w, [w.find_timepoint(eid, time) for time in ordered_times], f"按制度通制及明确年月重排{title}时间链。")
    parent = insert_miyuan(w, i, "南宋建炎四年六月", "神武军、神武副军将佐并属枢密院", q_date,
                           "北宋元丰四年", "南宋绍兴元年五月十六日")
    rel(w, parent, gt, "编制隶属", i, q_date, "神武军、神武副军将佐并属枢密院。", staff_type="武官")
    w.commit()


def entry247():
    i = 247; z = F[i]["text"]; w = W(i)
    eid = entity(w, "正将", "官职", z, "辞典明载为武官名。")
    tp(w, eid, "南宋", "枢密院所属将一级编制长官，位于统领之下、副将之上", i, z, "武官", "据南宋《要录》任官例建制度节点。")
    w.commit()


def entry248():
    i = 248; z = F[i]["text"]; w = W(i)
    eid = entity(w, "副将", "官职", z, "辞典明载为武官名。")
    tp(w, eid, "南宋", "枢密院所属将一级编制副长官，位于正将之下、准备将之上", i, z, "武官", "建副将南宋制度节点。")
    w.commit()


def entry249():
    i = 249; z = F[i]["all"]
    q_exact = q(i, "绍兴二年四月己丑：“赵琦为枢密院准备将领。”")
    w = W(i)
    eid = entity(w, "准备将领", "官职", F[i]["text"], "辞典明载为武官名。")
    tid = tp(w, eid, "南宋绍兴二年四月", "见枢密院准备将领任官例", i, q_exact, "武官", "任官例明确证明绍兴二年枢密院准备将领。")
    cite(w, "Timepoints", tid, i, F[i]["text"], "补充准备将领为将一级佐贰之末及其位序。", note="位序")
    w.commit()


def entry250():
    i = 250; z = F[i]["text"]; w = W(i)
    ge = entity(w, "偏裨", "官职", z, "辞典明确界定为下级指挥官总名。")
    gt = tp(w, ge, "南宋", "正将、副将、准备将领等下级指挥官总名", i, z, "武官总称", "建偏裨总称节点。")
    for title in ("正将", "副将", "准备将领"):
        mt = first_node(w, title, "官职")[1]
        rel(w, gt, mt, "统称与实例", i, z, f"偏裨总名明确包括{title}。")
    w.commit()


def entry251():
    i = 251; z = F[i]["text"]; w = W(i)
    eid = entity(w, "提领海船", "官职", z, "辞典明载为武官名。")
    tid = tp(w, eid, "南宋初", "隶枢密院，掌领海军", i, z, "武官", "建南宋初制度节点。")
    parent = insert_miyuan(w, i, "南宋初", "置提领海船等武官", z,
                           "北宋元丰四年", "南宋建炎四年六月")
    rel(w, parent, tid, "编制隶属", i, z, "提领海船隶枢密院。", staff_type="武官")
    w.commit()


def entry252():
    i = 252; z = F[i]["text"]
    q_start = q(i, "南宋初，军务丛集，使者旁午，于是设置枢密院准备差使、准备使唤等，供临时差遣、委以使命。初以二百人为额")
    q_reduce = q(i, "绍兴十五年减为一百五十人，三年一任。")
    w = W(i)
    eid = entity(w, "枢密院使臣", "官职", z, "辞典以专条记载枢密院临时使臣编制。")
    a = tp(w, eid, "南宋初", "置准备差使、准备使唤等，初额二百人", i, q_start, "武人差遣总称", "建南宋初使臣编制节点。", chain="none")
    b = tp(w, eid, "南宋绍兴十五年", "减额为一百五十人，三年一任", i, q_reduce, "武人差遣总称", "建绍兴十五年减额节点。", chain="none")
    chain(w, [a, b], "按南宋初置额与绍兴十五年减额排序。")
    parent_initial = node(w, "枢密院", "南宋初", "机构")[1]
    parent_reduce = append_miyuan(w, i, "南宋绍兴十五年", "使臣减额为一百五十人", q_reduce)
    rel(w, parent_initial, a, "编制隶属", i, q_start, "枢密院置临时差遣使臣二百人。", staff_quota=200, staff_type="武人")
    rel(w, parent_reduce, b, "编制隶属", i, q_reduce, "绍兴十五年枢密院使臣减为一百五十人。", staff_quota=150, staff_type="武人")
    for title in ("准备差使", "准备使唤"):
        member_e = entity(w, title, "官职", q_start, f"南宋初原文明载设置枢密院{title}。")
        member_t = tp(w, member_e, "南宋初", "供枢密院临时差遣、委以使命", i, q_start, "武人差遣", f"建{title}南宋初设置节点。")
        rel(w, parent_initial, member_t, "编制隶属", i, q_start, f"枢密院设置{title}供临时使命。", staff_type="武人")
    w.commit()


def entry253():
    i = 253; z = F[i]["all"]
    q_exact = q(i, "诏枢密院准备差使使臣以百五十人为额。")
    w = W(i)
    eid = w.find_entity("准备差使", "官职"); assert eid
    tid = node(w, "准备差使", "南宋初", "官职")[1]
    parent = node(w, "枢密院", "南宋初", "机构")[1]
    rel(w, parent, tid, "编制隶属", i, F[i]["text"], "准备差使供枢密院临时派遣。", staff_type="武人")
    cite(w, "Timepoints", tid, i, F[i]["text"], "补充准备差使的安置对象与临时差使职能。", note="职掌")
    cite(w, "Timepoints", tid, i, q_exact, "补证准备差使使臣曾以一百五十人为额；本条未明载年月，不另造精确时间点。", note="编制")
    w.commit()


def entry254():
    i = 254; z = F[i]["all"]
    q_head = q(i, "武人差遣名，非正官。南宋初见置，供枢密院临时使唤")
    w = W(i)
    eid = w.find_entity("准备使唤", "官职"); assert eid
    tid = node(w, "准备使唤", "南宋初", "官职")[1]
    parent = node(w, "枢密院", "南宋初", "机构")[1]
    rel(w, parent, tid, "编制隶属", i, q_head, "准备使唤供枢密院临时使唤。", staff_type="武人")
    cite(w, "Timepoints", tid, i, q_head, "专条补证准备使唤为非正官的武人差遣。")
    cite(w, "Timepoints", tid, i, z, "补充准备使唤全称与任官例；纯简称不另建实体。", note="简称字段")
    w.commit()


def entry255():
    i = 255; z = F[i]["text"]; w = W(i)
    eid = entity(w, "准备听候使唤", "官职", z, "辞典明载为武人差遣官名。")
    tid = tp(w, eid, "南宋", "低于准备使唤，多用于贬官", i, z, "武人差遣", "据南宋《要录》任官例建制度节点。")
    parent = insert_miyuan(w, i, "南宋", "置武人差遣等属官", z,
                           "北宋元丰四年", "南宋初")
    rel(w, parent, tid, "编制隶属", i, z, "枢密院听候使唤为枢府武人差遣。", staff_type="武人")
    w.commit()


def entry256():
    i = 256; z = F[i]["text"]; w = W(i)
    eid = entity(w, "准备差遣", "官职", z, "辞典明载为武官差遣名。")
    tid = tp(w, eid, "南宋", "由枢密院遣往外地办事", i, z, "武官差遣", "建南宋制度节点。")
    parent = node(w, "枢密院", "南宋", "机构")[1]
    rel(w, parent, tid, "编制隶属", i, z, "准备差遣为枢密院外派办事之官。", staff_type="武官")
    w.commit()


def entry257():
    i = 257; z = F[i]["text"]; w = W(i)
    eid = entity(w, "效士", "官职", z, "辞典明载为文人差使名。")
    tid = tp(w, eid, "南宋", "安置陈献边事可采的进士及北方来归文人，供枢密院差使", i, z, "文人差使", "建南宋效士制度节点。")
    parent = node(w, "枢密院", "南宋", "机构")[1]
    rel(w, parent, tid, "编制隶属", i, z, "枢密院效士由检详官置册供差使。", staff_type="文人")
    w.commit()


def entry258():
    i = 258; z = F[i]["all"]
    q_exact = q(i, "绍兴十五年五月壬子：“忠训郎、枢密院尅择官兼御前祗应李辅忱勤停")
    w = W(i)
    eid = entity(w, "枢密院尅择官", "官职", F[i]["text"], "辞典明载为流外官名。")
    tid = tp(w, eid, "南宋绍兴十五年五月", "任官例证明仍置", i, q_exact, "流外官", "任官例明确证明绍兴十五年仍置。")
    parent = insert_miyuan(w, i, "南宋绍兴十五年五月", "置尅择官", q_exact,
                           "南宋绍兴十一年四月", "南宋绍兴十五年")
    rel(w, parent, tid, "编制隶属", i, q_exact, "任官例明载枢密院尅择官。", staff_type="流外官")
    cite(w, "Timepoints", tid, i, z, "补充尅择官属卜史、掌择吉日。", note="职掌")
    w.commit()


def entry259():
    i = 259; z = F[i]["text"]; w = W(i)
    ge = entity(w, "枢密院给使", "官职", z, "辞典明确界定为枢密院公人总名。")
    gt = tp(w, ge, "宋代", "枢密院公人总名，供驱使杂役", i, z, "公人总称", "建枢密院给使总称节点。")
    members = (
        "左押衙", "右押衙", "左知客", "右知客", "承引官行首", "承引官副行首",
        "承引官", "军将", "大程官", "食手", "直省官",
    )
    for title in members:
        eid = w.find_entity(title, "官职")
        if not eid:
            eid = entity(w, title, "官职", z, f"枢密院给使条明确列{title}为公人实例。")
            mt = tp(w, eid, "宋代", "枢密院给使公人，供驱使杂役", i, z, "公人", f"建{title}给使节点。")
        else:
            mt = first_node(w, title, "官职")[1]
            cite(w, "Timepoints", mt, i, z, f"补证{title}属于枢密院给使。", note="给使实例")
        rel(w, gt, mt, "统称与实例", i, z, f"枢密院给使总名明确包括{title}。")
    parent = node(w, "枢密院", "宋初", "机构")[1]
    rel(w, parent, gt, "编制隶属", i, z, "枢密院给使为枢密院公人总名。", staff_type="公人")
    w.commit()


def entry260():
    i = 260; z = F[i]["text"]; w = W(i)
    camp_e = entity(w, "大程官营", "机构", z, "辞典明载为大程官驻所。")
    camp = tp(w, camp_e, "宋代", "大程官驻所，隶枢密院承旨司", i, z, "驻所", "建大程官营制度节点。")
    office = first_node(w, "枢密院承旨司", "机构")[1]
    rel(w, office, camp, "上下级机构", i, z, "大程官营隶枢密院承旨司。")
    dache = first_node(w, "大程官", "官职")[1]
    rel(w, camp, dache, "编制隶属", i, z, "大程官营编制有大程官一百人。", staff_quota=100, staff_type="给使")
    for short in ("都头", "十将", "副将"):
        title = f"大程官营{short}"
        eid = entity(w, title, "官职", z, f"原文明载大程官由{short}分级管理；加驻所前缀以区别同名武官。")
        tid = tp(w, eid, "宋代", f"分级管理大程官", i, z, "公人管理职", f"建大程官营{short}节点。")
        rel(w, camp, tid, "编制隶属", i, z, f"大程官营由{short}分级管理。", staff_type="公人")
    w.commit()


def main():
    entry241(); entry242(); entry243(); entry244(); entry245()
    entry246(); entry247(); entry248(); entry249(); entry250()
    entry251(); entry252(); entry253(); entry254(); entry255()
    entry256(); entry257(); entry258(); entry259(); entry260()


if __name__ == "__main__":
    main()
