#!/usr/bin/env python3
"""提取 chapter2t4 第 48–58 条（第三编 北宋前期中枢机构类：中书门下系统）。

首次引入 上下级机构 / 编制隶属 关系；实体以 机构 为主。
建模约定（详见 batch_report_ch2t4.md）：
  - 机构层级：上下级机构（上级→下级）。中书门下→制敕院、制敕院→五房、中书门下→制敕库。
  - 总名：统称与实例（统称→实例）。制敕院五房→孔目/吏/户/兵礼/刑 五房。
  - 编制配置：编制隶属（机构→官职），staff_quota 仅原文明示整数时填，staff_type=官/吏。
  - 无时间事实：写 time="未知" 的真实事件节点（不留 event="占位" 残留）。
  - 提点五房公事是 #62“提点中书制敕院五房公事”的简称，不为简称另建实体，延至 #62。
  - 中书令/侍中/同平章事/参知政事（宰相领导班子）已在 #1/#2/#27 建模，本批仅作
    中书门下宋前期节点的编制引文，不重复建编制隶属。
  - 给使（行首/副行首/通引官/堂门官/直省官/发敕官/驱使官）隶“沿堂五院”（非独立条目），
    仅作中书门下宋前期节点的编制引文，不建实体。
  - 各房“熙宁三年九月创置检正中书某房公事，位在堂后官之上”：检正官实体在 #64–67 建模，
    本批在各房时间链记该制度变化节点；检正官与房的编制隶属由 #64–67 补。
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

IDS = list(range(48, 59))

# 共享吏职实体（#48 建）：title -> (entity_id, 未知节点id)
OFF = {}
# 各房实体：title -> (entity_id, 主节点id)
ROOM = {}


def load_entry(entry_id):
    conn = sqlite3.connect(DICT_DB)
    row = conn.execute(
        "SELECT title, page, text, fields FROM chapter2t4 WHERE id=?", (entry_id,)
    ).fetchone()
    conn.close()
    full = (row[2] or "") + "\n" + "\n".join(
        str(v) for v in json.loads(row[3] or "{}").values()
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


def first_node(w, e):
    return w.conn.execute(
        "SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (e,)
    ).fetchone()[0]


def bz_rel(w, parent_tp, off_node, quota, stype, quote, C, note):
    """编制隶属（机构→官职）+ 引用。"""
    rel = w.relationship(
        parent_tp, off_node, "编制隶属",
        f"据{note}建编制隶属（机构→官职）。", quote,
        staff_quota=quota, staff_type=stype,
    )
    w.citation("Relationships", rel, C, quote, f"为编制隶属关系提供证据（{note}）")
    return rel


def lizhi(w, title, quote, C):
    """取或建共享吏职实体及其 time="未知" 承载节点（真实事件，不留占位）。"""
    e = w.entity(title, "官职", "《辞典》载为中书门下属吏（吏职），建官职实体。",
                 quotation=quote)
    node = w.find_timepoint(e, "未知")
    if not node:
        node = w.timepoint(
            e, "未知", "为中书门下属吏（吏职）", f"据中书门下条建{title}承载节点。",
            quote, attr_category="吏职名",
        )
        w.citation("Timepoints", node, C, quote, f"为{title}吏职身份提供证据")
    OFF[title] = (e, node)
    return e, node


# --------------------------------------------------------------- #48 ----
def entry48():
    C = cite(48)
    Q_ENT = q(48, "宋前期官署名。")
    Q_ZY = q(48, "唐开元十一年(723)始有此谓（《旧唐书·职官志》2《门下省》）。")
    Q_ZN = q(48, "宋前期宰相治事之所（《宋会要·职官》1之16）。")
    Q_BZ1 = q(48, "①名义上设中书令、侍中、同中书门下平章事、参知政事。实际上，中书令、"
                  "侍中不单除，即使除授亦罕预政事，只以同中书门下平章事为宰相之职，设二至三员。"
                  "参知政事为副相，二至三员或一员，不定。")
    Q_BZ2 = q(48, "②属官：有中书舍人，常设六员。但舍人常阙，而以他官知舍人职事，"
                  "称知制诰或直舍人院。其机构称舍人院。")
    Q_BZ2a = q(48, "②属官：有中书舍人，常设六员。")
    Q_BZ3 = q(48, "③属吏：有提点五房公事、堂后官、主事、录事、主书、守当官"
                  "（《宋会要·职官》1之16）。")
    Q_BZ4 = q(48, "④中书门下办事机构正房五：孔目房、吏房，户房、礼房，刑房。此外又有"
                  "生事房、勾销二房。统由吏人分掌，总称制敕院（《宋会要·职官》1之16、17）。")
    Q_BZ5 = q(48, "⑤给使：沿堂五院所属行首一人，副行首二人，通引官九人，堂门官七人，"
                  "直省官十一人，发敕官五人，驱使官二十二人（《宋会要·职官》1之17）。")
    w = writer(48)
    e = w.entity("中书门下", "机构",
                 "《辞典》95页独立成条，“宋前期官署名”，建机构实体。",
                 quotation=Q_ENT)
    # 唐开元十一年：始有此谓（源头，接链首）
    tp_tang = w.timepoint(
        e, "唐开元十一年", "始有“中书门下”之称",
        "据本条职源建源头节点，接链首。", Q_ZY, chain="head",
    )
    w.citation("Timepoints", tp_tang, C, Q_ZY, "为唐始称节点提供职源证据")
    # 宋前期：宰相治事之所
    tp_sq = w.timepoint(
        e, "宋前期", "为宰相治事之所",
        "据本条职能建宋前期节点。", Q_ZN, attr_category="官署名",
    )
    w.citation("Timepoints", tp_sq, C, Q_ZN, "为宋前期治事所节点提供职能证据")
    w.citation("Timepoints", tp_sq, C, Q_BZ1,
               "编制证据①：名义设中书令、侍中、同平章事、参知政事（宰相领导班子，已另建模）",
               note="编制·设官")
    w.citation("Timepoints", tp_sq, C, Q_BZ4,
               "编制证据④：下设五房，统由吏人分掌，总称制敕院", note="编制·办事机构")
    w.citation("Timepoints", tp_sq, C, Q_BZ5,
               "编制证据⑤：给使（沿堂五院行首、副行首、通引官、堂门官、直省官、发敕官、驱使官）",
               note="编制·给使")
    # 属官：中书舍人（官，常设六员）
    e_she = w.entity("中书舍人", "官职",
                     "《辞典》载为中书门下属官，建官职实体。", quotation=Q_BZ2a)
    tp_she = w.timepoint(
        e_she, "宋前期", "为中书门下属官，常设六员",
        "据本条编制②建中书舍人宋前期节点。", Q_BZ2a, attr_category="官名",
    )
    w.citation("Timepoints", tp_she, C, Q_BZ2, "为中书舍人属官及六员编制提供证据",
               note="编制·属官")
    bz_rel(w, tp_sq, tp_she, 6, "官", Q_BZ2a, C, "本条编制②属官")
    # 属吏：堂后官、主事、录事、主书、守当官（吏）
    for title in ("堂后官", "主事", "录事", "主书", "守当官"):
        _, node = lizhi(w, title, Q_BZ3, C)
        bz_rel(w, tp_sq, node, None, "吏", Q_BZ3, C, "本条编制③属吏")
    w.commit()
    return tp_sq


# --------------------------------------------------------------- #49 ----
def entry49():
    C = cite(49)
    Q_ENT = q(49, "宋前期官署名。")
    Q_ZY = q(49, "政事堂之名始于唐初武德年间（618—626年）（《全唐文》卷316《中书政事堂记》）。")
    Q_ZN = q(49, "中书门下所在地，即宰相办公厅（《玉海》卷161《宋朝政事堂》）。")
    Q_YF = q(49, "《玉海》卷121《元丰三省》：“中书在朝堂西，是为政事堂。……官制行，"
                 "悉厘正之。……并朝堂之西中书堂为门下、中书两省。”")
    w = writer(49)
    e = w.entity("政事堂", "机构",
                 "《辞典》95页独立成条，“宋前期官署名”，建机构实体。",
                 quotation=Q_ENT)
    tp_wd = w.timepoint(
        e, "唐武德年间", "政事堂之名始",
        "据本条职源建源头节点，接链首。", Q_ZY, chain="head",
    )
    w.citation("Timepoints", tp_wd, C, Q_ZY, "为唐武德始称节点提供职源证据")
    tp_sq = w.timepoint(
        e, "宋前期", "为中书门下所在地，即宰相办公厅",
        "据本条职能建宋前期节点。", Q_ZN, attr_category="官署名",
    )
    w.citation("Timepoints", tp_sq, C, Q_ZN, "为宋前期治所节点提供职能证据")
    tp_yf = w.timepoint(
        e, "北宋元丰官制", "官制行，悉厘正之，并朝堂之西中书堂为门下、中书两省",
        "据本条省称与别名②所引《元丰三省》建元丰官制节点（政事堂不复为宰相治所）。",
        Q_YF,
    )
    w.citation("Timepoints", tp_yf, C, Q_YF,
               "为元丰官制并中书堂为两省节点提供证据", note="省称与别名②所引")
    w.commit()


# --------------------------------------------------------------- #50 ----
def entry50(tp_sq_zsx):
    C = cite(50)
    Q_ENT = q(50, "吏署名。隶中书门下。")
    Q_ZN = q(50, "为中书门下五房堂后官以下吏人廨舍（《长编》卷34壬戌）。")
    Q_ROOMS = q(50, "制敕院共分五正房：孔目房，吏房，户房，兵礼房，刑房。此外又有"
                    "生事房、勾销房（《宋会要·职官》3之23）。")
    Q_STAFF = q(50, "制敕院官吏有：提点中书制敕院五房公事、堂后官、主事、录事、主书、守当官")
    Q_XN = q(50, "熙宁三年增设中书逐房检正公事与中书五房检正公事（都检正），以士人充"
                 "（同上书卷46）。")
    w = writer(50)
    e = w.entity("制敕院", "机构",
                 "《辞典》96页独立成条，“吏署名。隶中书门下”，建机构实体。",
                 quotation=Q_ENT)
    tp_main = w.timepoint(
        e, "未知", "为中书门下五房堂后官以下吏人廨舍，隶中书门下",
        "据本条职能建承载节点（本条职能无具体时间）。", Q_ZN, attr_category="吏署名",
    )
    w.citation("Timepoints", tp_main, C, Q_ZN, "为吏人廨舍节点提供职能证据")
    w.citation("Timepoints", tp_main, C, Q_ENT, "为隶中书门下提供证据", note="隶属")
    w.citation("Timepoints", tp_main, C, Q_ROOMS, "编制证据：分五正房，另有生事房、勾销房",
               note="编制·诸房")
    w.citation("Timepoints", tp_main, C, Q_STAFF, "编制证据：官吏构成", note="编制·官吏")
    tp_xn = w.timepoint(
        e, "北宋熙宁三年", "增设中书逐房检正公事与中书五房检正公事（都检正），以士人充",
        "据本条编制建熙宁三年节点。", Q_XN, attr_category="吏署名",
    )
    w.citation("Timepoints", tp_xn, C, Q_XN, "为熙宁增设检正节点提供编制证据")
    # 上下级机构：中书门下 -> 制敕院
    rel = w.relationship(
        tp_sq_zsx, tp_main, "上下级机构",
        "据本条“隶中书门下”建上下级机构（中书门下→制敕院）。", Q_ENT,
    )
    w.citation("Relationships", rel, C, Q_ENT, "为中书门下→制敕院上下级关系提供证据")
    # 编制隶属：制敕院 -> 属吏（堂后官/主事/录事/主书/守当官）
    for title in ("堂后官", "主事", "录事", "主书", "守当官"):
        _, node = OFF[title]
        bz_rel(w, tp_main, node, None, "吏", Q_STAFF, C, "本条编制·制敕院官吏")
    ROOM["制敕院"] = (e, tp_main)
    w.commit()
    return tp_main


# --------------------------------------------------------------- #51 ----
def entry51(tp_sq_zsx):
    C = cite(51)
    Q_ENT = q(51, "库名。隶中书。")
    Q_ZY = q(51, "熙宁五年至熙宁六年间，因检正中书刑房公事李承之之请而置"
                 "（《长编》卷248，壬戌，参《长编》卷237辛丑）。")
    Q_ZN = q(51, "贮存中书制敕院五房文书，近于今之档案库（《长编》卷248壬戌）。")
    Q_JC = q(51, "《宋会要·职官》3之27：“监中书制敕库张谔坐失察吏人，……自今制敕库监官"
                 "依旧堂后官兼。”")
    w = writer(51)
    e = w.entity("制敕库", "机构",
                 "《辞典》96页独立成条，“库名。隶中书”，建机构实体。",
                 quotation=Q_ENT)
    tp = w.timepoint(
        e, "北宋熙宁五年至六年", "因检正中书刑房公事李承之之请而置",
        "据本条职源建置库节点。", Q_ZY, attr_category="库名",
    )
    w.citation("Timepoints", tp, C, Q_ZY, "为置库节点提供职源证据")
    w.citation("Timepoints", tp, C, Q_ZN, "职能证据：贮存中书制敕院五房文书", note="职能")
    w.citation("Timepoints", tp, C, Q_JC, "编制证据：制敕库监官依旧堂后官兼",
               note="编制·监官")
    # 上下级机构：中书门下 -> 制敕库（“隶中书”，中书即中书门下，见中书门下条简称①）
    rel = w.relationship(
        tp_sq_zsx, tp, "上下级机构",
        "据本条“隶中书”建上下级机构（中书门下→制敕库；中书即中书门下简称）。", Q_ENT,
    )
    w.citation("Relationships", rel, C, Q_ENT, "为中书门下→制敕库上下级关系提供证据")
    w.commit()


# --------------------------------------------------------------- #52 ----
def entry52():
    C = cite(52)
    Q_ENT = q(52, "宋前期中书门下制敕院孔目房、吏房、户房、兵礼房、刑房总名。")
    Q_CH = q(52, "（淳化九年)诏重分擘五房所掌公事：孔目房；吏房；户房；兵礼房；刑房")
    Q_XP1 = q(52, "（咸平元年七月）诏制敕院诸房公事自今不得辄有漏泄。")
    Q_XP2 = q(52, "（咸平二年正月）诏中书五房各置主事一人。")
    w = writer(52)
    e = w.entity("制敕院五房", "机构",
                 "《辞典》96页独立成条，为制敕院孔目/吏/户/兵礼/刑五房总名，建机构实体。",
                 quotation=Q_ENT)
    tp_def = w.timepoint(
        e, "宋前期", "为中书门下制敕院孔目房、吏房、户房、兵礼房、刑房总名",
        "据本条定义建总名节点，接链首。", Q_ENT, attr_category="总名", chain="head",
    )
    w.citation("Timepoints", tp_def, C, Q_ENT, "为五房总名定义提供证据")
    tp_ch = w.timepoint(
        e, "北宋淳化九年", "诏重分擘五房所掌公事：孔目房、吏房、户房、兵礼房、刑房",
        "据本条引文建淳化九年分擘五房节点。", Q_CH,
    )
    w.citation("Timepoints", tp_ch, C, Q_CH, "为淳化分擘五房节点提供证据",
               note="原文“淳化九年”如此（淳化无九年，存疑照录）")
    tp_xp1 = w.timepoint(
        e, "北宋咸平元年七月", "诏制敕院诸房公事自今不得辄有漏泄",
        "据本条引文建咸平元年七月节点。", Q_XP1,
    )
    w.citation("Timepoints", tp_xp1, C, Q_XP1, "为咸平元年不得漏泄节点提供证据")
    tp_xp2 = w.timepoint(
        e, "北宋咸平二年正月", "诏中书五房各置主事一人",
        "据本条引文建咸平二年各置主事节点。", Q_XP2,
    )
    w.citation("Timepoints", tp_xp2, C, Q_XP2, "为咸平二年各置主事节点提供证据")
    ROOM["制敕院五房"] = (e, tp_def)
    w.commit()
    return tp_def


# --------------------------------------------------------------- #53 ----
def entry53():
    C = cite(53)
    Q_ENT = q(53, "中书门下办事机构名。")
    Q_ZZ = q(53, "掌文、武升朝官及刺史以上贵官与少尹、上佐、卫佐、技术、堂后（官）"
                 "进奏除授，及知州、通判差遣等事。")
    w = writer(53)
    e = w.entity("制敕院孔目房", "机构",
                 "《辞典》96页独立成条，“中书门下办事机构名”，建机构实体。",
                 quotation=Q_ENT)
    tp = w.timepoint(
        e, "未知", "为中书门下办事机构（制敕院孔目房），掌文、武升朝官及刺史以上贵官与"
                   "少尹、上佐、卫佐、技术、堂后进奏除授，及知州、通判差遣等事",
        "据本条职掌建承载节点（本条无具体时间）。", Q_ZZ, attr_category="机构名",
    )
    w.citation("Timepoints", tp, C, Q_ENT, "为办事机构身份提供证据", note="机构名")
    w.citation("Timepoints", tp, C, Q_ZZ, "为孔目房职掌提供证据", note="职掌")
    ROOM["制敕院孔目房"] = (e, tp)
    w.commit()
    return tp


# --------------------------------------------------------------- #54 ----
def entry54():
    C = cite(54)
    Q_ROLE = q(54, "一人总其事。下设主事、录事、守当官等吏职（《宋会要·职官》3之23）。")
    Q_XN = q(54, "熙宁三年九月，创置检正中书孔目房公事二员，位在堂后官之上，以士人充任"
                 "（《宋会要·职官》）。")
    w = writer(54)
    # #48 已建堂后官实体及其“未知”承载节点；本条（from_surname，姓氏检字表复原的
    # 残段）补充其职掌与熙宁三年节点。
    e = w.find_entity("堂后官", "官职")
    assert e, "#48 应已建堂后官实体"
    tp_ph = w.find_timepoint(e, "未知")
    assert tp_ph
    w.citation("Timepoints", tp_ph, C, Q_ROLE,
               "职掌证据：一人总其事，下设主事、录事、守当官等吏职",
               note="职掌（from_surname 残段）")
    tp_xn = w.timepoint(
        e, "北宋熙宁三年九月", "检正中书孔目房公事创置，位在堂后官之上",
        "据本条建熙宁三年九月节点（检正官创置，堂后官之上增设监督）。",
        Q_XN, attr_category="吏职名",
    )
    w.citation("Timepoints", tp_xn, C, Q_XN, "为熙宁三年检正位堂后官之上节点提供证据")
    w.commit()


# ------------------------------------------- 通用：带编制的办事机构房 ----
def room(eid, title, q_zz, ev_zz, bz, q_bz, q_xn, xn_ev):
    """职掌节点 + 编制隶属（堂后官/主事/录事/主书/守当官）+ 熙宁检正节点。

    bz: [(officer_title, quota), ...]；quota=None 表示原文未给该员整数员额。
    """
    C = cite(eid)
    Q_ENT = q(eid, "中书门下办事机构名。") if "中书门下办事机构名。" in FULL[eid][2] \
        else q(eid, "中书门下办事机构。")
    w = writer(eid)
    e = w.entity(title, "机构",
                 f"《辞典》载“{Q_ENT}”，建机构实体。", quotation=Q_ENT)
    tp = w.timepoint(
        e, "未知", ev_zz,
        "据本条职掌建承载节点（本条职掌无具体时间）。", q_zz, attr_category="机构名",
    )
    w.citation("Timepoints", tp, C, Q_ENT, "为办事机构身份提供证据", note="机构名")
    w.citation("Timepoints", tp, C, q_zz, f"为{title}职掌提供证据", note="职掌")
    w.citation("Timepoints", tp, C, q_bz, f"为{title}编制提供证据", note="编制")
    # 编制隶属：房 -> 堂后官/主事/录事/主书/守当官
    for off_title, quota in bz:
        _, node = OFF[off_title]
        bz_rel(w, tp, node, quota, "吏", q_bz, C, f"本条{title}编制")
    # 熙宁三年九月：创置检正中书某房公事，位在堂后官之上
    tp_xn = w.timepoint(
        e, "北宋熙宁三年九月", xn_ev,
        "据本条建熙宁三年九月检正节点（检正官实体在 #64–67 建模）。", q_xn,
        attr_category="机构名",
    )
    w.citation("Timepoints", tp_xn, C, q_xn, "为熙宁三年检正节点提供证据")
    ROOM[title] = (e, tp)
    w.commit()
    return tp


def entry55():
    room(
        55, "制敕院吏房",
        q(55, "掌后妃、诸王、公主封册，驸马都尉除拜，京官、幕职州县官注拟、加恩，"
              "诸司使、副之下、内侍加恩，百僚赠官、追封、叙封，河渠、堤堰、桥梁修造工役，"
              "祠祀、祈祷之事。"),
        "为中书门下办事机构（制敕院吏房），掌后妃、诸王、公主封册，驸马都尉除拜，"
        "京官、幕职州县官注拟、加恩，诸司使副之下、内侍加恩，百僚赠官、追封、叙封，"
        "河渠堤堰桥梁修造工役，祠祀祈祷之事",
        [("堂后官", 1), ("主事", 1), ("录事", 1), ("主书", 1), ("守当官", 1)],
        q(55, "堂后官一人总本房事，下设主事、录事、主书、守当官各一人分掌房事。"),
        q(55, "熙宁三年九月，创置检正中书吏房公事三员，位在堂后官之上（书卷同“孔目房”）。"),
        "创置检正中书吏房公事，位在堂后官之上",
    )


def entry56():
    room(
        56, "制敕院户房",
        q(56, "掌财币、军储、户口版籍、租调、漕运、禄俸、赈贷、土贡及诸路转运、"
              "内外监当差官之事。"),
        "为中书门下办事机构（制敕院户房），掌财币、军储、户口版籍、租调、漕运、禄俸、"
        "赈贷、土贡及诸路转运、内外监当差官之事",
        [("堂后官", 1), ("主事", 1), ("录事", 1), ("主书", 3), ("守当官", 4)],
        q(56, "堂后官一人总掌本房事，下设主事、录事各一人，主书三人，守当官四人，分掌本房事。"),
        q(56, "熙宁三年九月创置检正中书户房公事二员，位在堂后官之上（书卷同“孔目房”）。"),
        "创置检正中书户房公事，位在堂后官之上",
    )


def entry57():
    room(
        57, "制敕院兵、礼房",
        q(57, "掌郊祀、朝拜陵庙、朝会享宴，尊号，祭器，仪仗，刻漏，册礼，旌表，假告，"
              "外夷，馆阁、国学、图书，祥瑞，贡举，补荫，释道，二旌节，符印，诸司职掌、"
              "诸道行军司马、将校加恩，功臣子孙寒食洒扫、禁火，知军差官之事。"),
        "为中书门下办事机构（制敕院兵、礼房），掌郊祀、朝拜陵庙、朝会享宴、尊号、祭器、"
        "仪仗、刻漏、册礼、旌表、假告、外夷、馆阁国学图书、祥瑞、贡举、补荫、释道、"
        "旌节、符印、诸司职掌、行军司马将校加恩、功臣子孙寒食洒扫禁火、知军差官之事",
        [("堂后官", 1), ("主事", 1), ("录事", 1), ("主书", 1), ("守当官", 1)],
        q(57, "堂后官一人总掌本房事，下设主事、录事、主书、守当官各一人，分掌房事。"),
        q(57, "熙宁三年九月一日创设检正中书兵、礼房公事二员，位在堂后官之上（书卷同“孔目房”）。"),
        "创设检正中书兵、礼房公事，位在堂后官之上",
    )


def entry58():
    C = cite(58)
    Q_ENT = q(58, "中书门下办事机构。")
    Q_ZZ = q(58, "掌敕书、德音泛降，责授，经赦叙理，刑狱诉讼，擒捕，旌赏之事。")
    Q_BZ = q(58, "由堂后官一人总掌本房事，下设主事、录事一人、主事三人、守当官五人，"
                 "分掌本房事。")
    Q_XN = q(58, "熙宁三年九月一日创设检正中书刑房公事二人，位在堂后官之上（书卷同“孔目房”）。")
    w = writer(58)
    e = w.entity("制敕院刑房", "机构",
                 "《辞典》载“中书门下办事机构”，建机构实体。", quotation=Q_ENT)
    tp = w.timepoint(
        e, "未知", "为中书门下办事机构（制敕院刑房），掌敕书、德音泛降、责授、经赦叙理、"
                   "刑狱诉讼、擒捕、旌赏之事",
        "据本条职掌建承载节点（本条职掌无具体时间）。", Q_ZZ, attr_category="机构名",
    )
    w.citation("Timepoints", tp, C, Q_ENT, "为办事机构身份提供证据", note="机构名")
    w.citation("Timepoints", tp, C, Q_ZZ, "为刑房职掌提供证据", note="职掌")
    w.citation("Timepoints", tp, C, Q_BZ,
               "为刑房编制提供证据（原文“主事、录事一人、主事三人”主事重出，疑 OCR 讹误）",
               note="编制（主事务额存疑）")
    # 编制隶属：主事务额因原文重出存疑，不给整数；录事一、守当官五明确
    bz_rel(w, tp, OFF["堂后官"][1], 1, "吏", Q_BZ, C, "本条刑房编制")
    bz_rel(w, tp, OFF["主事"][1], None, "吏", Q_BZ, C, "本条刑房编制（主事务额存疑）")
    bz_rel(w, tp, OFF["录事"][1], 1, "吏", Q_BZ, C, "本条刑房编制")
    bz_rel(w, tp, OFF["守当官"][1], 5, "吏", Q_BZ, C, "本条刑房编制")
    tp_xn = w.timepoint(
        e, "北宋熙宁三年九月", "创设检正中书刑房公事，位在堂后官之上",
        "据本条建熙宁三年九月检正节点（检正官实体在 #64–67 建模）。", Q_XN,
        attr_category="机构名",
    )
    w.citation("Timepoints", tp_xn, C, Q_XN, "为熙宁三年检正节点提供证据")
    ROOM["制敕院刑房"] = (e, tp)
    w.commit()
    return tp


# --------------------------------- 关系：制敕院→五房；制敕院五房→五房 ----
def relations():
    # 上下级机构：制敕院 -> 五房（出处为“制敕院”条）
    C50 = cite(50)
    Q_ROOMS = q(50, "制敕院共分五正房：孔目房，吏房，户房，兵礼房，刑房。此外又有"
                    "生事房、勾销房（《宋会要·职官》3之23）。")
    w50 = EntryWriter(ENTRY_DB, "制敕院", "96")
    _, tp_zcy = ROOM["制敕院"]
    for title in ("制敕院孔目房", "制敕院吏房", "制敕院户房", "制敕院兵、礼房", "制敕院刑房"):
        _, tp_room = ROOM[title]
        rel = w50.relationship(
            tp_zcy, tp_room, "上下级机构",
            f"据“制敕院”条“制敕院共分五正房”建上下级机构（制敕院→{title}）。", Q_ROOMS,
        )
        w50.citation("Relationships", rel, C50, Q_ROOMS,
                     f"为制敕院→{title}上下级关系提供证据")
    w50.commit()
    # 统称与实例：制敕院五房 -> 五房（出处为“制敕院五房”条）
    C52 = cite(52)
    Q_ENT52 = q(52, "宋前期中书门下制敕院孔目房、吏房、户房、兵礼房、刑房总名。")
    w52 = EntryWriter(ENTRY_DB, "制敕院五房", "96")
    _, tp_wf = ROOM["制敕院五房"]
    for title in ("制敕院孔目房", "制敕院吏房", "制敕院户房", "制敕院兵、礼房", "制敕院刑房"):
        _, tp_room = ROOM[title]
        rel = w52.relationship(
            tp_wf, tp_room, "统称与实例",
            f"制敕院五房为五房总名，{title}为其构成实例，据“制敕院五房”条建统称与实例。",
            Q_ENT52,
        )
        w52.citation("Relationships", rel, C52, Q_ENT52,
                     f"为制敕院五房→{title}统称与实例关系提供证据")
    w52.commit()


if __name__ == "__main__":
    tp_sq_zsx = entry48(); print("48 OK")
    entry49(); print("49 OK")
    entry50(tp_sq_zsx); print("50 OK")
    entry51(tp_sq_zsx); print("51 OK")
    entry52(); print("52 OK")
    entry53(); print("53 OK")
    entry54(); print("54 OK")
    entry55(); print("55 OK")
    entry56(); print("56 OK")
    entry57(); print("57 OK")
    entry58(); print("58 OK")
    relations(); print("relations OK")
    conn = sqlite3.connect(ENTRY_DB)
    for t in ("Entities", "Timepoints", "Relationships", "Citations", "BuildRecords"):
        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    conn.close()
