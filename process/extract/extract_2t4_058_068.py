#!/usr/bin/env python3
"""提取 chapter2t4 第 58–68 条（新序号；制敕院系统收尾 + 中书门下宰属检官体系）。

辞典库已重建（1648→1647），id 前移：本批对应旧序号 #59–69。
  #58 制敕院生事房 / #59 制敕院勾销房 / #60 堂印 / #61 提点中书制敕院五房公事 /
  #62 检正中书五房公事 / #63 检正中书某房公事 / #64–68 检正中书孔目/吏/户/礼/刑房公事

要点：
  - 新库重建后“制敕院孔目房”条并回原“堂后官”伪条目内容（编制 + 熙宁检正），
    孔目房实体此前只有职掌节点，本批补建 编制隶属 与 熙宁三年九月 检正节点（entry53fix）。
  - #60 堂印为“印”（非机构/官职），不建实体；“守当官二人掌堂印”作为编制事实，
    追加引用到已存在的 中书门下→守当官 编制隶属（prompt 规则7）。
  - #64–68 检正各房公事“余与检正中书某房公事同”：创置时间转引 #63（实际出处），
    本条“余与……同”作转引证据；各房→检正 编制隶属 连接双方熙宁三年九月节点
    （与该制度变化时间相符），补 #55–58 留待本批的检正官—房关系。
  - 检正中书某房公事（#63）为各房检正通称 → 统称与实例 → #64–68 五个实例。
  - 提点（#61）为“宰属名”命官，#48③虽列入属吏，staff_type 从本条定“官”。
"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")

IDS = [50, 53, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68]


def load_entry(entry_id):
    conn = sqlite3.connect(DICT_DB)
    row = conn.execute(
        "SELECT title, page, text, fields FROM chapter2t4 WHERE id=?", (entry_id,)
    ).fetchone()
    conn.close()
    full = (row[2] or "") + "\n" + "\n".join(
        str(v) for k, v in json.loads(row[3] or "{}").items() if not k.startswith("_")
    )
    return row[0], row[1], full


FULL = {i: load_entry(i) for i in IDS}


def q(eid, s):
    assert s in FULL[eid][2], f"#{eid} 不含: {s[:60]}…"
    return s


def cite(eid):
    t, p, _ = FULL[eid]
    return f"《宋代官制辞典》第{p}页“{t}”条"


def writer(eid):
    t, p, _ = FULL[eid]
    return EntryWriter(ENTRY_DB, t, p)


def node_of(w, entity_title, time, type_="官职"):
    e = w.find_entity(entity_title, type_)
    assert e, f"应已建实体 {entity_title}({type_})"
    tp = w.find_timepoint(e, time)
    assert tp, f"{entity_title} 无 time={time} 节点"
    return e, tp


def bz_rel(w, parent_tp, off_node, quota, stype, quote, C, note):
    rel = w.relationship(
        parent_tp, off_node, "编制隶属",
        f"据{note}建编制隶属（机构→官职）。", quote,
        staff_quota=quota, staff_type=stype,
    )
    w.citation("Relationships", rel, C, quote, f"为编制隶属关系提供证据（{note}）")
    return rel


# ------------------------------------------- #53 补：孔目房编制+熙宁 ----
def entry53fix():
    C = cite(53)
    Q_BZ = q(53, "堂后官一人总其事。下设主事、录事、守当官等吏职（《宋会要·职官》3之23）。")
    Q_XN = q(53, "熙宁三年九月，创置检正中书孔目房公事二员，位在堂后官之上，以士人充任"
                 "（《宋会要·职官》）。")
    w = EntryWriter(ENTRY_DB, "制敕院孔目房", "96")
    e = w.find_entity("制敕院孔目房", "机构")
    assert e, "孔目房实体应已建"
    tp_sq = w.find_timepoint(e, "宋前期")
    assert tp_sq
    # 补编制隶属（新库重建后孔目房条并回原“堂后官”伪条目内容，补此遗漏）
    for title, quota in (("堂后官", 1), ("主事", None), ("录事", None), ("守当官", None)):
        _, node = node_of(w, title, "宋前期")
        bz_rel(w, tp_sq, node, quota, "吏", Q_BZ, C,
               "新库重建孔目房条并回原“堂后官”内容，补建孔目房编制")
    # 补熙宁三年九月检正节点
    tp_xn = w.timepoint(
        e, "北宋熙宁三年九月", "创置检正中书孔目房公事，位在堂后官之上",
        "新库重建孔目房条并回原“堂后官”内容，补建熙宁三年九月检正节点。",
        Q_XN, attr_category="机构名",
    )
    w.citation("Timepoints", tp_xn, C, Q_XN, "为孔目房熙宁检正节点提供证据")
    w.commit()
    return tp_xn


# --------------------------------------------------------------- #58 ----
def entry58():
    C = cite(58)
    Q_ENT = q(58, "中书门下办事机构。")
    Q_ZZ = q(58, "掌承受文书，并规定完成期限后分配给诸房行遣。")
    Q_BZ = q(58, "由主书一人掌本房事（《宋会要·职官》3之23、26）。")
    w = writer(58)
    e = w.entity("制敕院生事房", "机构",
                 "《辞典》载“中书门下办事机构”，建机构实体。", quotation=Q_ENT)
    tp = w.timepoint(
        e, "宋前期", "为中书门下办事机构（制敕院生事房），掌承受文书，规定完成期限后"
                     "分配给诸房行遣",
        "据本条职掌建节点（出处为中书门下办事机构，时期宋前期）。", Q_ZZ,
        attr_category="机构名",
    )
    w.citation("Timepoints", tp, C, Q_ENT, "为办事机构身份提供证据", note="机构名")
    w.citation("Timepoints", tp, C, Q_ZZ, "为生事房职掌提供证据", note="职掌")
    _, nd_zs = node_of(w, "主书", "宋前期")
    bz_rel(w, tp, nd_zs, 1, "吏", Q_BZ, C, "本条生事房编制")
    w.commit()
    return tp


# --------------------------------------------------------------- #59 ----
def entry59():
    C = cite(59)
    Q_ENT = q(59, "中书门下办事机构。")
    Q_ZZ = q(59, "掌每日收发文字目录登记及发遣处理后勾销，以便催驱滞留的文字。")
    Q_BZ = q(59, "守当官一人（《宋会要·职官》3之27)")
    w = writer(59)
    e = w.entity("制敕院勾销房", "机构",
                 "《辞典》载“中书门下办事机构”，建机构实体。", quotation=Q_ENT)
    tp = w.timepoint(
        e, "宋前期", "为中书门下办事机构（制敕院勾销房），掌每日收发文字目录登记及"
                     "发遣处理后勾销，以便催驱滞留的文字",
        "据本条职掌建节点（出处为中书门下办事机构，时期宋前期）。", Q_ZZ,
        attr_category="机构名",
    )
    w.citation("Timepoints", tp, C, Q_ENT, "为办事机构身份提供证据", note="机构名")
    w.citation("Timepoints", tp, C, Q_ZZ, "为勾销房职掌提供证据", note="职掌")
    _, nd_sg = node_of(w, "守当官", "宋前期")
    bz_rel(w, tp, nd_sg, 1, "吏", Q_BZ, C, "本条勾销房编制")
    w.commit()
    return tp


# --------------------------------------------------------------- #60 ----
def entry60():
    C = cite(60)
    Q = q(60, "中书门下行敕用印，由守当官二人掌之（《宋会要·职官》3之23）。")
    w = writer(60)
    # 堂印为“印”（非机构/官职），不建实体；“守当官二人掌堂印”追加到既有 中书门下→守当官
    _, tp_zsx = node_of(w, "中书门下", "宋前期", "机构")
    _, nd_sg = node_of(w, "守当官", "宋前期")
    rel = w.relationship(
        tp_zsx, nd_sg, "编制隶属",
        "复用中书门下→守当官编制隶属（堂印条提供守当官员额证据）。", Q,
    )
    w.citation("Relationships", rel, C, Q,
               "堂印条：守当官二人掌堂印（行敕用印），为守当官编制提供员额证据",
               note="编制·员额（堂印条）")
    w.commit()


# --------------------------------------------------------------- #61 ----
def entry61():
    C = cite(61)
    Q_ENT = q(61, "宰属名。")
    Q_ZY = q(61, "古无此官，初见于北宋淳化四年（993）八月（《宋会要·职官》3之22）。")
    Q_ZZ = q(61, "总掌制敕院五房公事、纠察制敕院诸房人吏。")
    Q_BZ = q(61, "编制 一人。")
    Q_PW = q(61, "淳化四年初置时，给俸依枢密副承旨（正七品）例；熙宁三年创置检正中书"
                 "五房公事，位在提点五房公事之上（《宋会要·职官》3之22、46）。")
    Q_XN = q(61, "熙宁三年创置检正中书五房公事，位在提点五房公事之上"
                 "（《宋会要·职官》3之22、46）。")
    Q_PY = q(61, "至和元年，诏中书提点五房公事，听佩鱼。")
    w = writer(61)
    e = w.entity("提点中书制敕院五房公事", "官职",
                 "《辞典》97页独立成条，“宰属名”，建官职实体。", quotation=Q_ENT)
    tp_cz = w.timepoint(
        e, "北宋淳化四年八月", "始置提点中书制敕院五房公事",
        "据本条职源建始置节点。", Q_ZY, attr_category="宰属名", attr_grade="正七品",
    )
    w.citation("Timepoints", tp_cz, C, Q_ZY, "为淳化四年始置节点提供职源证据")
    w.citation("Timepoints", tp_cz, C, Q_ZZ, "职掌证据：总掌制敕院五房公事、纠察诸房人吏",
               note="职掌")
    w.citation("Timepoints", tp_cz, C, Q_BZ, "编制证据：一人", note="编制")
    w.citation("Timepoints", tp_cz, C, Q_PW, "品位证据：给俸依枢密副承旨（正七品）例",
               note="品位")
    tp_xn = w.timepoint(
        e, "北宋熙宁三年", "检正中书五房公事创置，位在提点五房公事之上",
        "据本条品位建熙宁三年节点。", Q_XN, attr_category="宰属名",
    )
    w.citation("Timepoints", tp_xn, C, Q_XN, "为熙宁三年检正位提点之上节点提供证据")
    tp_zh = w.timepoint(
        e, "北宋至和元年", "诏提点五房公事听佩鱼",
        "据本条简称与别名②所引建至和元年听佩鱼节点。", Q_PY, attr_category="宰属名",
    )
    w.citation("Timepoints", tp_zh, C, Q_PY, "为至和元年听佩鱼节点提供证据",
               note="简称与别名②所引")
    # 编制隶属：中书门下→提点、制敕院→提点（宰属命官，staff_type=官）
    _, tp_zsx = node_of(w, "中书门下", "宋前期", "机构")
    _, tp_zcy = node_of(w, "制敕院", "宋前期", "机构")
    bz_rel(w, tp_zsx, tp_cz, None, "官", Q_ZZ, C, "提点为中书门下宰属")
    bz_rel(w, tp_zcy, tp_cz, None, "官", Q_ZZ, C, "提点总掌制敕院五房公事")
    w.commit()
    return tp_cz


# --------------------------------------------------------------- #62 ----
def entry62():
    C = cite(62)
    Q_ENT = q(62, "宰属名。隶中书。")
    Q_CZ = q(62, "熙宁三年九月一日创置（《长编》卷215）。")
    Q_BA = q(62, "元丰五年官制行，罢检正官（《合璧后集》卷18《宰属门·检正》）。")
    Q_ZZ = q(62, "总理、督察中书门下诸房吏人公事（《长编》卷215）。")
    Q_PW = q(62, "检正官系士人之高选，以朝官充。都检正中书五房公事位在提点中书制敕院"
                 "五房公事之上（《石林燕语》卷9）。")
    Q_BZ = q(62, "一员")
    w = writer(62)
    e = w.entity("检正中书五房公事", "官职",
                 "《辞典》97页独立成条，“宰属名。隶中书”，建官职实体。", quotation=Q_ENT)
    tp_cz = w.timepoint(
        e, "北宋熙宁三年九月一日", "创置检正中书五房公事（都检正），以朝官充",
        "据本条职源与沿革建创置节点。", Q_CZ, attr_category="宰属名",
    )
    w.citation("Timepoints", tp_cz, C, Q_CZ, "为熙宁三年九月一日创置节点提供职源证据")
    w.citation("Timepoints", tp_cz, C, Q_ZZ, "职掌证据：总理、督察中书门下诸房吏人公事",
               note="职掌")
    w.citation("Timepoints", tp_cz, C, Q_PW,
               "品位证据：士人高选以朝官充；都检正位在提点之上", note="品位")
    w.citation("Timepoints", tp_cz, C, Q_BZ, "编制证据：一员", note="编制")
    tp_ba = w.timepoint(
        e, "北宋元丰五年", "官制行，罢检正官",
        "据本条职源与沿革建罢官节点。", Q_BA, attr_category="宰属名",
    )
    w.citation("Timepoints", tp_ba, C, Q_BA, "为元丰五年罢检正官节点提供沿革证据")
    _, tp_zsx = node_of(w, "中书门下", "宋前期", "机构")
    bz_rel(w, tp_zsx, tp_cz, 1, "官", Q_ENT, C, "检正中书五房公事隶中书，编制一员")
    w.commit()
    return tp_cz


# --------------------------------------------------------------- #63 ----
def entry63():
    C = cite(63)
    Q_ENT = q(63, "宰属名，隶中书。")
    Q_CZ = q(63, "熙宁三年九月一日创置（《宋会要·职官》3之46）。")
    Q_ZZ = q(63, "掌本房（或孔目房、或吏房、或户房、或礼房、或刑房）记录功过簿，"
                 "以考核房内堂后官以下群吏的过失（《合璧后集》卷18《检正·事类》）。")
    Q_PW = q(63, "逐房检正官与提点中书五房公事（正七品）地位相等，位于堂后官之上"
                 "（《宋会要·职官》3之46）。")
    Q_BZ = q(63, "检正中书孔目房公事二员，检正中书吏房公事二员，检正中书户房公事二员，"
                 "检正中书礼房公事二员，检正中书刑房公事二员（《长编》卷215戊子）。")
    w = writer(63)
    e = w.entity("检正中书某房公事", "官职",
                 "《辞典》97页独立成条，“宰属名，隶中书”，为各房检正通称，建官职实体。",
                 quotation=Q_ENT)
    tp_cz = w.timepoint(
        e, "北宋熙宁三年九月一日", "创置检正中书某房公事（逐房检正）",
        "据本条职源建创置节点。", Q_CZ, attr_category="宰属名",
    )
    w.citation("Timepoints", tp_cz, C, Q_CZ, "为熙宁三年九月一日创置节点提供职源证据")
    w.citation("Timepoints", tp_cz, C, Q_ZZ, "职掌证据：掌本房记录功过簿考核群吏", note="职掌")
    w.citation("Timepoints", tp_cz, C, Q_PW,
               "品位证据：与提点（正七品）地位相等，位于堂后官之上", note="品位")
    w.citation("Timepoints", tp_cz, C, Q_BZ, "编制证据：五房检正各二员", note="编制")
    _, tp_zsx = node_of(w, "中书门下", "宋前期", "机构")
    bz_rel(w, tp_zsx, tp_cz, None, "官", Q_ENT, C, "检正中书某房公事隶中书")
    w.commit()
    return tp_cz, Q_BZ, C


# ------------------------------------------- #64–68 检正各房公事 ----
JZ = [
    (64, "检正中书孔目房公事", "制敕院孔目房", "北宋熙宁三年九月"),
    (65, "检正中书吏房公事", "制敕院吏房", "北宋熙宁三年九月"),
    (66, "检正中书户房公事", "制敕院户房", "北宋熙宁三年九月"),
    (67, "检正中书礼房公事", "制敕院兵、礼房", "北宋熙宁三年九月"),
    (68, "检正中书刑房公事", "制敕院刑房", "北宋熙宁三年九月"),
]


def jianzheng(eid, jz_title, room_title, room_xn_time, q_bz63, c63):
    C = cite(eid)
    Q_TONG = q(eid, "余与“检正中书某房公事”同。")
    w = writer(eid)
    e = w.entity(jz_title, "官职",
                 f"《辞典》载“{jz_title}”（余与检正中书某房公事同），建官职实体。",
                 quotation=Q_TONG)
    # 创置节点：时间转引 #63（实际出处），本条“余与……同”作转引证据
    Q_CZ63 = q(63, "熙宁三年九月一日创置（《宋会要·职官》3之46）。")
    tp_cz = w.timepoint(
        e, "北宋熙宁三年九月一日", f"创置{jz_title}（职掌、品位、编制转引“检正中书某房公事”条）",
        f"本条“余与检正中书某房公事同”，创置时间转引 #63 建节点。", Q_CZ63,
        attr_category="宰属名",
    )
    w.citation("Timepoints", tp_cz, c63, Q_CZ63,
               "创置时间转引“检正中书某房公事”条（实际出处）")
    w.citation("Timepoints", tp_cz, C, Q_TONG,
               "本条证据：余与“检正中书某房公事”同（职掌、品位、编制从某房条）")
    # 编制隶属：各房（熙宁节点）→ 该检正（熙宁节点，二员）
    e_room = w.find_entity(room_title, "机构")
    assert e_room, f"{room_title} 实体应已建"
    tp_room_xn = w.find_timepoint(e_room, room_xn_time)
    assert tp_room_xn, f"{room_title} 无 {room_xn_time} 节点"
    rel = w.relationship(
        tp_room_xn, tp_cz, "编制隶属",
        f"据 #63 编制“{jz_title}二员”建编制隶属（{room_title}→{jz_title}），"
        f"两端同取熙宁三年九月节点（与该制度变化时间相符）。", q_bz63,
        staff_quota=2, staff_type="官",
    )
    w.citation("Relationships", rel, c63, q_bz63,
               f"为{room_title}→{jz_title}编制隶属提供证据（#63 编制，实际出处）")
    w.citation("Relationships", rel, C, Q_TONG, "本条“余与……同”佐证")
    w.commit()
    return tp_cz


# --------------------- 关系：制敕院→生事/勾销房；检正某房→各检正 ----
def relations(jz_tps):
    # 上下级机构：制敕院 → 生事房、勾销房（出处“制敕院”条）
    C50 = cite(50)
    Q_ROOMS = q(50, "制敕院共分五正房：孔目房，吏房，户房，兵礼房，刑房。此外又有"
                    "生事房、勾销房（《宋会要·职官》3之23）。")
    w50 = EntryWriter(ENTRY_DB, "制敕院", "96")
    _, tp_zcy = node_of(w50, "制敕院", "宋前期", "机构")
    for title in ("制敕院生事房", "制敕院勾销房"):
        e = w50.find_entity(title, "机构")
        tp = w50.find_timepoint(e, "宋前期")
        rel = w50.relationship(
            tp_zcy, tp, "上下级机构",
            f"据“制敕院”条“此外又有生事房、勾销房”建上下级机构（制敕院→{title}）。",
            Q_ROOMS,
        )
        w50.citation("Relationships", rel, C50, Q_ROOMS,
                     f"为制敕院→{title}上下级关系提供证据")
    w50.commit()
    # 统称与实例：检正中书某房公事 → 五个检正房公事（出处“检正中书某房公事”条）
    C63 = cite(63)
    Q_BZ63 = q(63, "检正中书孔目房公事二员，检正中书吏房公事二员，检正中书户房公事二员，"
                   "检正中书礼房公事二员，检正中书刑房公事二员（《长编》卷215戊子）。")
    w63 = EntryWriter(ENTRY_DB, "检正中书某房公事", "97")
    _, tp_mou = node_of(w63, "检正中书某房公事", "北宋熙宁三年九月一日")
    for (eid, jz_title, _, _), tp_jz in zip(JZ, jz_tps):
        rel = w63.relationship(
            tp_mou, tp_jz, "统称与实例",
            f"检正中书某房公事为各房检正通称，{jz_title}为其构成实例（#63 编制列举），"
            f"建统称与实例。", Q_BZ63,
        )
        w63.citation("Relationships", rel, C63, Q_BZ63,
                     f"为检正某房→{jz_title}统称与实例关系提供证据")
    w63.commit()


if __name__ == "__main__":
    entry53fix(); print("53补 OK")
    entry58(); print("58 OK")
    entry59(); print("59 OK")
    entry60(); print("60 OK")
    entry61(); print("61 OK")
    entry62(); print("62 OK")
    tp_mou, Q_BZ63, C63 = entry63(); print("63 OK")
    jz_tps = []
    for eid, jz_title, room_title, room_xn in JZ:
        jz_tps.append(jianzheng(eid, jz_title, room_title, room_xn, Q_BZ63, C63))
        print(f"{eid} OK")
    relations(jz_tps); print("relations OK")
    conn = sqlite3.connect(ENTRY_DB)
    for t in ("Entities", "Timepoints", "Relationships", "Citations", "BuildRecords"):
        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    conn.close()
