#!/usr/bin/env python3
"""提取 chapter2t4 第 380–390 条（三司子司：勾院、磨勘司、开拆司及其判官）。

本批条目（p136–137）此前基本未被直接提取：三司勾院/都勾院/都磨勘司/开拆司的
已有节点均来自“三司”条、“勾院”条等他条，本批独立条目的始置、编制、判官内容
未入库。判官类官职全缺。可复用实体：三司勾院(411)、三司都勾院(551)、三司都磨勘司(412)、
三司开拆司(418)、左计勾院(552)、右计勾院(553)、勾覆官(556)、总计司(410)、三司(406)。

建模要点：
  - 已有机构只补缺失事实（追加职源/职掌/编制引用、补建缺漏节点、建编制隶属），不重复造节点。
  - 判官类官职全新建；编制隶属 机构→判官，quota 仅原文明示整数时填
    （“一员或二员”不给整数，“二人/三人”给整数）。
  - “宋代（未载具体年月）”泛节点保留在链首（不动 C 类），本批具体沿革节点接链尾。
  - 三司开拆司推官为起止型（太平兴国三年十二月置 → 雍熙四年十一月改判官），
    并与判三司开拆司建前后演变。
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

IDS = list(range(380, 391))


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


def new_officer(w, title, time, event, quote, C, cat, decision, grade=None):
    e = w.entity(title, "官职", decision, quotation=quote)
    tp = w.timepoint(e, time, event, decision, quote, attr_category=cat, attr_grade=grade)
    w.citation("Timepoints", tp, C, quote, f"为{title}提供证据（{decision[:20]}）")
    return e, tp


def officer_node(w, title, time, event, quote, C, cat):
    """取官职的 time 节点，没有则建（用于吏职/判官补承载节点）。"""
    e = w.find_entity(title, "官职")
    if e:
        tp = w.find_timepoint(e, time)
        if tp:
            return e, tp
    else:
        e = w.entity(title, "官职", f"《辞典》载{title}，建官职实体。", quotation=quote)
    tp = w.timepoint(e, time, event, f"据出处建{title}{time}节点。", quote, attr_category=cat)
    w.citation("Timepoints", tp, C, quote, f"为{title}提供证据")
    return e, tp


# --------------------------------------------------------------- #380 ----
def entry380():
    C = cite(380)
    Q_ZY = q(380, "太平兴国五年(980)十月，三部勾院合而为一，正称“三司勾院”，至雍熙三年"
                  "(986)八月再分为三部勾院（《宋会要·职官》5之23）。")
    Q_BZ1 = q(380, "①判三司勾院二人，资浅者称同勾当三司公事（《宋会要·职官》5之23）。")
    Q_BZ2 = q(380, "②勾覆官三人。")
    Q_ZZ = q(380, "统纠三司所属三部钱粮出入数及失陷数（《宋史·食货志》下一《会计》）。")
    w = writer(380)
    e = w.find_entity("三司勾院", "机构")
    assert e, "三司勾院实体应已建"
    tp = w.find_timepoint(e, "北宋太平兴国五年十月")
    assert tp
    w.citation("Timepoints", tp, C, Q_ZY, "本条职源：三部勾院合为三司勾院", note="职源")
    w.citation("Timepoints", tp, C, Q_ZZ, "职掌：统纠三部钱粮出入数及失陷数", note="职掌")
    w.citation("Timepoints", tp, C, Q_BZ1, "编制：判三司勾院二人", note="编制")
    w.citation("Timepoints", tp, C, Q_BZ2, "编制：勾覆官三人", note="编制")
    # 编制隶属：三司勾院→判三司勾院公事(2,官)、→勾覆官(3,吏)
    e_py = w.find_entity("判三司勾院公事", "官职")
    tp_py = w.find_timepoint(e_py, "宋前期")
    bz_rel(w, tp, tp_py, 2, "官", Q_BZ1, C, "本条编制①判三司勾院二人")
    _, tp_gf = officer_node(w, "勾覆官", "宋前期", "为三司勾院、都勾院勾覆吏职",
                            Q_BZ2, C, "吏职名")
    bz_rel(w, tp, tp_gf, 3, "吏", Q_BZ2, C, "本条编制②勾覆官三人")
    w.commit()


# --------------------------------------------------------------- #381 ----
def entry381():
    C = cite(381)
    Q_ENT = q(381, "差遣名。")
    Q_ZZ = q(381, "掌统纠三司所属三部出入帐籍，防止或检举舞弊贪污。")
    w = writer(381)
    new_officer(w, "判三司勾院公事", "宋前期",
                "掌统纠三司所属三部出入帐籍，防止或检举舞弊贪污",
                Q_ZZ, C, "差遣名",
                "《辞典》136页独立成条，“差遣名”，为三司勾院判官，建官职实体。")
    w.commit()


# --------------------------------------------------------------- #382 ----
def entry382():
    C = cite(382)
    Q_ZY = q(382, "淳化三年七月一日三部勾院又合为一，正称三司都勾院（《长编》卷33）。")
    Q_BZ1 = q(382, "①主判官一员或二员，资浅者或称同提点三司都勾院公事"
                   "（参《长编》卷40，至道二年十月已未）。")
    Q_BZ2 = q(382, "②吏额：勾覆官三员，熙宁七年复置三司都勾院，于八年减去勾覆官二员只存一员"
                   "（《宋会要·食货》56之1）。")
    w = writer(382)
    e = w.find_entity("三司都勾院", "机构")
    assert e, "三司都勾院实体应已建"
    tp = w.find_timepoint(e, "北宋淳化三年七月一日")
    assert tp
    w.citation("Timepoints", tp, C, Q_ZY, "本条职源：三部勾院合为三司都勾院", note="职源")
    w.citation("Timepoints", tp, C, Q_BZ1, "编制：主判官一员或二员", note="编制")
    w.citation("Timepoints", tp, C, Q_BZ2, "编制：勾覆官三员", note="编制")
    # 熙宁八年减员节点
    tp_j = w.timepoint(
        e, "北宋熙宁八年", "减勾覆官二员，只存一员",
        "据本条编制②建熙宁八年减员节点。", Q_BZ2, attr_category="官司名",
    )
    w.citation("Timepoints", tp_j, C, Q_BZ2, "为熙宁八年减勾覆官员额节点提供证据", note="编制")
    # 编制隶属：三司都勾院→判三司都勾院(官)、→勾覆官(3,吏)
    e_pd = w.find_entity("判三司都勾院", "官职")
    tp_pd = w.find_timepoint(e_pd, "宋前期")
    bz_rel(w, tp, tp_pd, None, "官", Q_BZ1, C, "本条编制①主判官一员或二员")
    _, tp_gf = officer_node(w, "勾覆官", "宋前期", "为三司勾院、都勾院勾覆吏职",
                            Q_BZ2, C, "吏职名")
    bz_rel(w, tp, tp_gf, 3, "吏", Q_BZ2, C, "本条编制②勾覆官三员")
    w.commit()


# --------------------------------------------------------------- #383 ----
def entry383():
    C = cite(383)
    Q_ENT = q(383, "差遣名。")
    Q_ZZ = q(383, "领三司都勾院，通纠三部钱谷出入帐籍，以防欺盗不实")
    Q_PW = q(383, "以朝官充。")
    w = writer(383)
    e, tp = new_officer(w, "判三司都勾院", "宋前期",
                        "领三司都勾院，通纠三部钱谷出入帐籍，以防欺盗不实",
                        Q_ZZ, C, "差遣名",
                        "《辞典》137页独立成条，“差遣名”，领三司都勾院，建官职实体。")
    w.citation("Timepoints", tp, C, Q_PW, "品位：以朝官充", note="品位")
    w.commit()


# --------------------------------------------------------------- #384 ----
def entry384():
    C = cite(384)
    Q_ENT = q(384, "官署名。")
    Q = q(384, "淳化四年十月，易三司为总计司，下分左、右计，各置勾院。淳化五年十二月罢"
               "（《分纪》卷13《勾院》）。")
    w = writer(384)
    e = w.entity("左、右计勾院", "机构",
                 "《辞典》137页独立成条，“官署名”，为左计勾院、右计勾院合称，建机构实体。",
                 quotation=Q_ENT)
    tp_zhi = w.timepoint(
        e, "北宋淳化四年十月", "易三司为总计司，下分左、右计，各置勾院",
        "据本条建置院节点。", Q, attr_category="官署名",
    )
    w.citation("Timepoints", tp_zhi, C, Q, "为淳化四年十月置左右计勾院节点提供证据")
    tp_ba = w.timepoint(
        e, "北宋淳化五年十二月", "罢左、右计勾院",
        "据本条建罢院节点。", Q, attr_category="官署名",
    )
    w.citation("Timepoints", tp_ba, C, Q, "为淳化五年十二月罢左右计勾院节点提供证据")
    # 上下级机构：总计司→左、右计勾院
    e_zjs = w.find_entity("总计司", "机构")
    tp_zjs = w.find_timepoint(e_zjs, "北宋淳化四年十月")
    rel = w.relationship(tp_zjs, tp_zhi, "上下级机构",
                         "据本条“易三司为总计司，下分左、右计，各置勾院”建上下级机构"
                         "（总计司→左、右计勾院）。", Q)
    w.citation("Relationships", rel, C, Q, "为总计司→左、右计勾院上下级关系提供证据")
    # 统称与实例：左、右计勾院→左计勾院、右计勾院
    for it in ("左计勾院", "右计勾院"):
        e_i = w.find_entity(it, "机构")
        tp_i = w.find_timepoint(e_i, "北宋淳化四年十月")
        rel = w.relationship(tp_zhi, tp_i, "统称与实例",
                             f"左、右计勾院为合称，{it}为其构成实例，建统称与实例。", Q)
        w.citation("Relationships", rel, C, Q, f"为左、右计勾院→{it}统称与实例关系提供证据")
    w.commit()


# ------------------------------------------- #385/#386 判左/右计勾院 ----
def entry385386():
    for eid, title, inst in ((385, "判左计勾院公事", "左计勾院"),
                             (386, "判右计勾院公事", "右计勾院")):
        C = cite(eid)
        Q_ENT = q(eid, "差遣名。")
        side = "左" if eid == 385 else "右"
        Q_ZZ = q(eid, f"掌{side}计院所辖诸道钱粮帐籍出入数的考校，纠察与检举虚伪不实、"
                      "诈冒贪污等违纪事（同上书卷）。")
        w = writer(eid)
        e, tp = new_officer(
            w, title, "北宋淳化四年十月",
            f"随{inst}置，掌{side}计院所辖诸道钱粮帐籍出入数的考校，纠察与检举虚伪不实、"
            "诈冒贪污等违纪事",
            Q_ZZ, C, "差遣名",
            f"《辞典》137页独立成条，“差遣名”，为{inst}判官，建官职实体。")
        # 编制隶属：左/右计勾院→判官
        e_i = w.find_entity(inst, "机构")
        tp_i = w.find_timepoint(e_i, "北宋淳化四年十月")
        bz_rel(w, tp_i, tp, None, "官", Q_ZZ, C, f"{inst}判官")
        w.commit()


# --------------------------------------------------------------- #387 ----
def entry387():
    C = cite(387)
    Q_ENT = q(387, "官署名，隶三司。")
    Q_ZY = q(387, "端拱二年(989)十二月四日始置（《长编》卷30）。")
    Q_ZZ = q(387, "掌覆核三部帐册，以检验财会出纳之数有无漏洞（《宋史·职官志》2《都磨勘司》）。")
    Q_BZ = q(387, "置主判官一人。")
    w = writer(387)
    e = w.find_entity("三司都磨勘司", "机构")
    assert e, "三司都磨勘司实体应已建"
    # 端拱二年始置（新事实），接链尾（“宋代”泛节点留链首）
    tp = w.timepoint(
        e, "北宋端拱二年十二月四日", "始置三司都磨勘司",
        "据本条职源建始置节点（此前仅有“宋代”泛节点，本条补具体始置时间）。",
        Q_ZY, attr_category="官署名",
    )
    w.citation("Timepoints", tp, C, Q_ZY, "为端拱二年始置节点提供职源证据")
    w.citation("Timepoints", tp, C, Q_ZZ, "职掌：覆核三部帐册检验出纳", note="职掌")
    w.citation("Timepoints", tp, C, Q_BZ, "编制：置主判官一人", note="编制")
    # 编制隶属：三司都磨勘司→判三司都磨勘司公事(1,官)
    e_p = w.find_entity("判三司都磨勘司公事", "官职")
    tp_p = w.find_timepoint(e_p, "宋前期")
    bz_rel(w, tp, tp_p, 1, "官", Q_BZ, C, "本条编制置主判官一人")
    w.commit()


# --------------------------------------------------------------- #388 ----
def entry388():
    C = cite(388)
    Q_ENT = q(388, "差遣官名。")
    Q_ZZ = q(388, "主掌三司都磨勘司公事")
    w = writer(388)
    new_officer(w, "判三司都磨勘司公事", "宋前期", "主掌三司都磨勘司公事",
                Q_ZZ, C, "差遣官名",
                "《辞典》137页独立成条，“差遣官名”，主掌三司都磨勘司公事，建官职实体。")
    w.commit()


# --------------------------------------------------------------- #389 ----
def entry389():
    C = cite(389)
    Q_ENT = q(389, "官署名，隶三司。")
    Q_YG = q(389, "宋初已置。熙宁八年曾废罢，十二月十二日复置"
                  "（《长编》卷271，《宋会要·食货》56之11）。")
    Q_ZZ = q(389, "承接中书与密院宣、敕及诸州申三司文书并发放三部，以及催驱有关文书与"
                  "钩销簿历等（同上书卷，及《宋史·职官志》2《三司使》）。")
    Q_BZ2 = q(389, "② 开宝五年，合盐铁、户部开拆司为一开拆司，度支开拆司为一司，"
                   "仍由本部判官领之。")
    Q_BZ3 = q(389, "③ 太平兴国三年十二月，设开拆司推官一员统领开拆司。五年后，三开拆司合为一司。")
    Q_BZ4 = q(389, "④ 雍熙四年十一月，设判三司开拆司一员。")
    Q_BZ5 = q(389, "⑤ 至道三年设判官二员。")
    Q_BZ6 = q(389, "⑥ 咸平元年后，定为一员。")
    w = writer(389)
    e = w.find_entity("三司开拆司", "机构")
    assert e, "三司开拆司实体应已建"
    # “宋代”泛节点留链首，本批具体沿革接链尾
    tp_sc = w.timepoint(e, "宋初", "已置三司开拆司（盐铁、度支、户部三部各置开拆司，"
                                    "各由本部判官兼领）",
                        "据本条职源与沿革建宋初已置节点。", Q_YG, attr_category="官署名")
    w.citation("Timepoints", tp_sc, C, Q_YG, "为宋初已置节点提供职源证据")
    w.citation("Timepoints", tp_sc, C, Q_ZZ, "职掌：承接宣敕文书发放三部、催驱钩销", note="职掌")
    tp_kb = w.timepoint(e, "北宋开宝五年", "合盐铁、户部开拆司为一开拆司，度支开拆司为一司",
                        "据本条编制②建开宝五年合司节点。", Q_BZ2, attr_category="官署名")
    w.citation("Timepoints", tp_kb, C, Q_BZ2, "为开宝五年合司节点提供编制证据", note="编制")
    tp_tg = w.timepoint(e, "北宋太平兴国三年十二月", "设开拆司推官一员统领开拆司",
                        "据本条编制③建太平兴国三年设推官节点。", Q_BZ3, attr_category="官署名")
    w.citation("Timepoints", tp_tg, C, Q_BZ3, "为设推官节点提供编制证据", note="编制")
    tp_pg = w.timepoint(e, "北宋雍熙四年十一月", "设判三司开拆司一员",
                        "据本条编制④建雍熙四年设判官节点。", Q_BZ4, attr_category="官署名")
    w.citation("Timepoints", tp_pg, C, Q_BZ4, "为设判官节点提供编制证据", note="编制")
    tp_zd = w.timepoint(e, "北宋至道三年", "设判官二员",
                        "据本条编制⑤建至道三年判官二员节点。", Q_BZ5, attr_category="官署名")
    w.citation("Timepoints", tp_zd, C, Q_BZ5, "为判官二员节点提供编制证据", note="编制")
    tp_xp = w.timepoint(e, "北宋咸平元年", "判官定为一员",
                        "据本条编制⑥建咸平元年定员节点。", Q_BZ6, attr_category="官署名")
    w.citation("Timepoints", tp_xp, C, Q_BZ6, "为定员节点提供编制证据", note="编制")
    tp_fi = w.timepoint(e, "北宋熙宁八年", "废罢三司开拆司",
                        "据本条职源与沿革建熙宁八年废罢节点。", Q_YG, attr_category="官署名")
    w.citation("Timepoints", tp_fi, C, Q_YG, "为熙宁八年废罢节点提供沿革证据")
    tp_fu = w.timepoint(e, "北宋熙宁八年十二月十二日", "复置三司开拆司",
                        "据本条职源与沿革建熙宁八年十二月十二日复置节点。", Q_YG,
                        attr_category="官署名")
    w.citation("Timepoints", tp_fu, C, Q_YG, "为熙宁八年复置节点提供沿革证据")
    # 判三司开拆司实体及其节点（雍熙四年设、至道三年二员、咸平元年定一员）
    e_pg = w.entity("判三司开拆司", "官职",
                    "《辞典》389 条编制④⑤⑥ 载判三司开拆司（雍熙四年设、员额有变化），"
                    "建官职实体。", quotation=Q_BZ4)
    tp_pg_o = w.timepoint(e_pg, "北宋雍熙四年十一月", "设判三司开拆司一员",
                          "据本条编制④建判三司开拆司始置节点。", Q_BZ4, attr_category="差遣名")
    w.citation("Timepoints", tp_pg_o, C, Q_BZ4, "为判三司开拆司始置节点提供证据")
    tp_zd_o = w.timepoint(e_pg, "北宋至道三年", "判官二员",
                          "据本条编制⑤建至道三年判官二员节点。", Q_BZ5, attr_category="差遣名")
    w.citation("Timepoints", tp_zd_o, C, Q_BZ5, "为判官二员节点提供证据", note="编制")
    tp_xp_o = w.timepoint(e_pg, "北宋咸平元年", "判官定为一员",
                          "据本条编制⑥建咸平元年定员节点。", Q_BZ6, attr_category="差遣名")
    w.citation("Timepoints", tp_xp_o, C, Q_BZ6, "为定员节点提供证据", note="编制")
    # 编制隶属：开拆司→推官(1)、→判三司开拆司(员额随时期)
    e_tg = w.find_entity("三司开拆司推官", "官职")
    tp_tg_o = w.find_timepoint(e_tg, "北宋太平兴国三年十二月")
    bz_rel(w, tp_tg, tp_tg_o, 1, "官", Q_BZ3, C, "本条编制③设推官一员")
    bz_rel(w, tp_pg, tp_pg_o, 1, "官", Q_BZ4, C, "本条编制④设判三司开拆司一员")
    bz_rel(w, tp_zd, tp_zd_o, 2, "官", Q_BZ5, C, "本条编制⑤判官二员")
    bz_rel(w, tp_xp, tp_xp_o, 1, "官", Q_BZ6, C, "本条编制⑥判官定一员")
    w.commit()


# --------------------------------------------------------------- #390 ----
def entry390():
    C = cite(390)
    Q_ENT = q(390, "差遣名。")
    Q = q(390, "太平兴国三年(978)十二月至雍熙四年(987)十一月间，领开拆司事"
               "（《宋会要·职官》5之38）。")
    w = writer(390)
    e = w.entity("三司开拆司推官", "官职",
                 "《辞典》137页独立成条，“差遣名”，建官职实体。", quotation=Q_ENT)
    tp_qi = w.timepoint(
        e, "北宋太平兴国三年十二月", "设开拆司推官，领开拆司事",
        "据本条建起节点（起止型之起）。", Q, attr_category="差遣名",
    )
    w.citation("Timepoints", tp_qi, C, Q, "为太平兴国三年设推官领开拆司事节点提供证据")
    tp_zhi = w.timepoint(
        e, "北宋雍熙四年十一月", "罢开拆司推官（改设判三司开拆司）",
        "据本条建止节点（起止型之止）。", Q, attr_category="差遣名",
    )
    w.citation("Timepoints", tp_zhi, C, Q, "为雍熙四年罢推官节点提供证据")
    w.commit()


def relations390():
    """前后演变：三司开拆司推官（雍熙四年十一月止）→ 判三司开拆司（雍熙四年十一月设）。"""
    C = cite(390)
    Q = q(390, "太平兴国三年(978)十二月至雍熙四年(987)十一月间，领开拆司事"
               "（《宋会要·职官》5之38）。")
    w = EntryWriter(ENTRY_DB, "三司开拆司推官", "137")
    _, tp_zhi = node_of(w, "三司开拆司推官", "北宋雍熙四年十一月")
    _, tp_pg = node_of(w, "判三司开拆司", "北宋雍熙四年十一月")
    rel = w.relationship(
        tp_zhi, tp_pg, "前后演变",
        "据本条起止型表述，太平兴国三年设推官、雍熙四年十一月改设判三司开拆司，"
        "建前后演变（推官→判官）。", Q,
    )
    w.citation("Relationships", rel, C, Q, "为推官→判官前后演变关系提供证据")
    w.commit()


if __name__ == "__main__":
    entry381(); print("381 OK")   # 先建判三司勾院公事实体
    entry383(); print("383 OK")   # 先建判三司都勾院实体
    entry388(); print("388 OK")   # 先建判三司都磨勘司公事实体
    entry390(); print("390 OK")   # 先建三司开拆司推官实体
    entry380(); print("380 OK")
    entry382(); print("382 OK")
    entry384(); print("384 OK")
    entry385386(); print("385/386 OK")
    entry387(); print("387 OK")
    entry389(); print("389 OK")   # 建三司开拆司节点+判三司开拆司实体+编制隶属
    relations390(); print("relations390 OK")
    conn = sqlite3.connect(ENTRY_DB)
    for t in ("Entities", "Timepoints", "Relationships", "Citations", "BuildRecords"):
        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    conn.close()
