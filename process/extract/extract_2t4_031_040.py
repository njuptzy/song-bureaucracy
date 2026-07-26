#!/usr/bin/env python3
"""提取 chapter2t4 第 31–40 条（含"分参"跳转补读的 #861 尚书省左丞、#863 尚书省右丞）。

要点：
- #31 尚书左丞、尚书右丞（合称）→ 统称与实例 → 尚书省左丞/尚书省右丞（补读 #861/#863）；
- #32 执政官、#33 宰执、#34 公师、#35 公孤、#36 三师、#40 三公：原文明确的合称/总名，
  建统称与实例到各实例（实例无条目的先建最小实体，后续批次复用）；
- #36 三师→三公（北周、政和两次改名）建前后演变；#27/#31 副相演变链补齐。
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

IDS = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 861, 863]


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
    assert s in FULL[eid][2], f"#{eid} 不含: {s[:50]}…"
    return s


def cite(eid):
    t, p, _ = FULL[eid]
    return f"《宋代官制辞典》第{p}页“{t}”条"


def writer(eid):
    t, p, _ = FULL[eid]
    return EntryWriter(ENTRY_DB, t, p)


def chain(w, e, nodes, cat, C, note_src):
    """按历史顺序 tail 建链，每节点挂引用。nodes: (time, event, quote, grade|None)"""
    ids = []
    for time, event, quote, grade in nodes:
        tp = w.timepoint(
            e, time, event,
            f"据{note_src}建{time}节点。", quote,
            attr_category=cat, attr_grade=grade,
        )
        w.citation("Timepoints", tp, C, quote, f"为{time}节点提供证据（{note_src}）")
        ids.append(tp)
    return ids


# --------------------------------------------------------------- #31 ----
def entry31():
    C = cite(31)
    Q_A = q(31, "元丰新制罢参知政事，而易以两省侍郎、尚书左丞、尚书右丞为副相之职，"
                "直至南宋建炎三年复参知政事，尚书左、右丞省去不用"
                "（《宋史·职官志》1《参知政事》）。")
    Q_B = q(31, "建炎三年四月十三日（庚申）：“尚书右丞李邴改参知政事。”（《要录》卷22)")
    Q_REF = q(31, "分参“尚书省·左丞”、“尚书省·右丞”条。")
    w = writer(31)
    e = w.entity(
        "尚书左丞、尚书右丞", "官职",
        "《辞典》90页独立成条，“职事官名”，为元丰新制副相之职的合称，建官职实体。",
        quotation=q(31, "职事官名。"),
    )
    tp1 = w.timepoint(
        e, "北宋元丰新制", "罢参知政事，易以两省侍郎、尚书左丞、尚书右丞为副相之职",
        "据本条建元丰副相节点。", Q_A, attr_category="职事官名",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为元丰副相节点提供原文证据")
    w.citation("Timepoints", tp1, C, Q_REF,
               "跳转指引：已补读“尚书省·左丞”（p197）、“尚书省·右丞”（p198）条并提取",
               note="分参“尚书省·左丞”、“尚书省·右丞”条")
    tp2 = w.timepoint(
        e, "南宋建炎三年四月十三日", "复参知政事，尚书左、右丞省去不用（尚书右丞李邴改参知政事）",
        "据本条“建炎三年四月十三日（庚申）：‘尚书右丞李邴改参知政事。’”建终结节点。",
        Q_B, attr_category="职事官名",
    )
    w.citation("Timepoints", tp2, C, Q_B, "为省去不用节点提供原文证据")
    w.commit()
    return tp1, tp2


# ------------------------------------------- 补读 #861 尚书省左丞 ----
def annex861():
    C = cite(861)
    Q_QIN = q(861, "尚书丞为秦官。")
    Q_HAN = q(861, "尚书丞分左、右，始于东汉初（《后汉书·百官志》3、《晋书·职官志》）。")
    Q_SQ = q(861, "宋前期无职事，为文臣迁转官阶，位六部尚书之下；元丰寄禄新格，"
                  "易为光禄大夫阶（《宋会要·职官》4之6、《玉海》卷119《元丰新定官制》）。")
    Q_GP1 = q(861, "宋前期依唐制正四品上（《新唐书·百官志》1、《宋史·职官志》8）。")
    Q_YF = q(861, "元丰新制，为职事官，升任执政（副相）（《宋会要·职官》4之6《尚书省》）。")
    Q_YF2 = q(861, "《朝野杂记》甲集卷10《参知政事》：“参知政事，自太祖始置。"
                   "元丰官制改为门下、中书侍郎，尚书左、右丞。”")
    Q_YF3 = q(861, "又，与仆射合治尚书省事（《长编》卷326，辛巳）。")
    Q_GP2 = q(861, "元丰新制后，定为正二品（《分纪》卷8《左右丞》）。")
    Q_BZ = q(861, "元丰新制一人（《宋史·职官志》1《尚书省》）。")
    Q_END = q(861, "北宋沿置。至南宋建炎三年四月，罢尚书左、右丞（《要录》卷22庚申）。")
    w = writer(861)
    e = w.entity(
        "尚书省左丞", "官职",
        "《辞典》197页独立成条，“阶官，职事官名”，建官职实体（分参跳转补读）。",
        quotation=q(861, "阶官，职事官名。"),
    )
    nodes = [
        ("秦", "尚书丞为秦官", Q_QIN, None),
        ("东汉初", "尚书丞分左、右", Q_HAN, None),
        ("宋前期", "无职事，为文臣迁转官阶，位六部尚书之下（元丰寄禄新格易为光禄大夫阶）",
         Q_SQ, "正四品上"),
        ("北宋元丰新制", "为职事官，升任执政（副相），与仆射合治尚书省事", Q_YF, "正二品"),
        ("南宋建炎三年四月", "罢尚书左、右丞", Q_END, None),
    ]
    tps = chain(w, e, nodes, "阶官", C, "“尚书省·左丞”条（分参补读）")
    w.citation("Timepoints", tps[2], C, Q_GP1, "官品证据：宋前期正四品上", note="官品")
    w.citation("Timepoints", tps[3], C, Q_YF2, "职掌证据：元丰官制改为侍郎、左右丞", note="职掌")
    w.citation("Timepoints", tps[3], C, Q_YF3, "职掌证据：与仆射合治尚书省事", note="职掌")
    w.citation("Timepoints", tps[3], C, Q_GP2, "官品证据：元丰新制正二品", note="官品")
    w.citation("Timepoints", tps[3], C, Q_BZ, "编制证据：元丰新制一人", note="编制")
    w.commit()


# ------------------------------------------- 补读 #863 尚书省右丞 ----
def annex863():
    C = cite(863)
    Q_TONG = q(863, "宋代官制，左比右尊。除班位杂压次于左丞之外，"
                    "诸凡“职源与沿革”、“职掌”、“官品”、“编制”均与左丞同。")
    Q_REF = q(863, "详参“尚书省左丞”条。")
    w = writer(863)
    e = w.entity(
        "尚书省右丞", "官职",
        "《辞典》198页独立成条，“阶官、职事官名”，建官职实体（分参跳转补读）。",
        quotation=q(863, "阶官、职事官名。"),
    )
    nodes = [
        ("东汉初", "尚书丞分左、右（职源与沿革均与左丞同）", Q_TONG, None),
        ("宋前期", "无职事，为文臣迁转官阶（与左丞同），班位杂压次于左丞", Q_TONG, "正四品上"),
        ("北宋元丰新制", "为职事官，升任执政（副相）（与左丞同）", Q_TONG, "正二品"),
        ("南宋建炎三年四月", "罢尚书左、右丞（与左丞同）", Q_TONG, None),
    ]
    tps = chain(w, e, nodes, "阶官", C, "“尚书省·右丞”条（转引左丞条）")
    for tp in tps:
        w.citation("Timepoints", tp, C, Q_REF,
                   "职源、职掌、官品、编制转引“尚书省左丞”条", note="详参“尚书省左丞”条")
    w.commit()


# --------------------------------------------------------------- #32 ----
def entry32():
    C = cite(32)
    Q = q(32, "参知政事等副相（包括元丰新制门下侍郎、中书侍郎、尚书左丞、尚书右丞），"
              "以及枢密院长贰，即枢密使、知枢密院事、枢密副使、同知枢密院事、"
              "签书枢密院事、同签书枢密院事，总称执政官"
              "（《宋会要·职官》1之17、《庆元条法》卷4《职制门》、《宋史·职官志》2《枢密院》）。")
    w = writer(32)
    e = w.entity(
        "执政官", "官职",
        "《辞典》90页独立成条，“职官总名”，为副相与枢密院长贰的统称，建官职实体。",
        quotation=q(32, "职官总名。"),
    )
    tp = w.timepoint(
        e, "宋代", "参知政事等副相及枢密院长贰，总称执政官",
        "据本条建总名节点（原文未系年，按辞典断代为宋代）。",
        Q, attr_category="职官总名",
    )
    w.citation("Timepoints", tp, C, Q, "为执政官总名提供原文证据")

    # 实例：副相序列（复用已有实体与节点）+ 枢密院长贰（新建最小实体）
    inst = [
        ("参知政事", "北宋乾德二年四月十九日", None),
        ("门下侍郎", "北宋元丰新制", None),
        ("中书侍郎", "北宋元丰新制", None),
        ("尚书左丞、尚书右丞", "北宋元丰新制", None),
    ]
    for name in ("枢密使", "知枢密院事", "枢密副使", "同知枢密院事",
                 "签书枢密院事", "同签书枢密院事"):
        ei = w.entity(
            name, "官职",
            f"《辞典》90页“执政官”条载{name}为枢密院长贰、执政官实例，"
            f"建官职实体（该职在第三编枢密院门有条目，后续提取时同名复用）。",
            quotation=Q,
        )
        tpi = w.timepoint(
            ei, "宋代", "枢密院长贰，总称执政官",
            "据“执政官”条建节点（原文未系年，按辞典断代为宋代）。",
            Q, attr_category="职官总名",
        )
        w.citation("Timepoints", tpi, C, Q, f"为{name}为执政官实例提供原文证据")
        inst.append((name, None, tpi))

    for name, time, tpi_direct in inst:
        ei = w.find_entity(name, "官职")
        tpi = tpi_direct or w.find_timepoint(ei, time)
        assert tpi, f"{name} 缺节点"
        rel = w.relationship(
            tp, tpi, "统称与实例",
            f"执政官为总名，{name}为其构成实例，据“执政官”条建统称与实例（统称→实例）。",
            Q,
        )
        w.citation("Relationships", rel, C, Q, f"为执政官→{name}关系提供原文证据")
    w.commit()


# --------------------------------------------------------------- #33 ----
def entry33():
    C = cite(33)
    Q = q(33, "宰相与执政合称。")
    w = writer(33)
    e = w.entity(
        "宰执", "官职",
        "《辞典》90页独立成条，“职官总名”，宰相与执政合称，建官职实体。",
        quotation=q(33, "职官总名。"),
    )
    tp = w.timepoint(
        e, "宋代", "宰相与执政合称",
        "据本条建合称节点（原文未系年，按辞典断代为宋代）。",
        Q, attr_category="职官总名",
    )
    w.citation("Timepoints", tp, C, Q, "为宰执合称提供原文证据")
    for name in ("宰相", "执政官"):
        ei = w.find_entity(name, "官职")
        tpi = w.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (ei,)
        ).fetchone()[0]
        rel = w.relationship(
            tp, tpi, "统称与实例",
            f"宰执为合称，{name}为其构成一方，据本条建统称与实例（统称→实例）。", Q,
        )
        w.citation("Relationships", rel, C, Q, f"为宰执→{name}关系提供原文证据")
    w.commit()


# --------------------------------------------------------------- #34 ----
def entry34():
    C = cite(34)
    Q = q(34, "宋前期三师、三公合称。")
    Q_REF = q(34, "分参“三师”、“三公”条。")
    w = writer(34)
    e = w.entity(
        "公师", "官职",
        "《辞典》90页独立成条，为宋前期三师、三公合称，建官职实体。",
        quotation=Q,
    )
    tp = w.timepoint(
        e, "宋前期", "三师、三公合称",
        "据本条“宋前期三师、三公合称”建合称节点。", Q, attr_category="合称",
    )
    w.citation("Timepoints", tp, C, Q, "为公师合称提供原文证据")
    w.citation("Timepoints", tp, C, Q_REF, "跳转指引：三师、三公条同批提取", note="分参“三师”、“三公”条")
    w.commit()
    return tp


# --------------------------------------------------------------- #35 ----
def entry35():
    C = cite(35)
    Q = q(35, "宋政和二年之后，三公、三孤官合称。")
    w = writer(35)
    e = w.entity(
        "公孤", "官职",
        "《辞典》90页独立成条，为政和二年后三公、三孤官合称，建官职实体。",
        quotation=Q,
    )
    tp = w.timepoint(
        e, "北宋政和二年之后", "三公、三孤官合称",
        "据本条“宋政和二年之后，三公、三孤官合称”建合称节点。", Q, attr_category="合称",
    )
    w.citation("Timepoints", tp, C, Q, "为公孤合称提供原文证据")
    # 三孤=三少（少师、少傅、少保），其条目在本编后续；先建最小实体
    e3 = w.entity(
        "三少", "官职",
        "《辞典》90页“公孤”条载三公、三孤官合称“公孤”，三孤即三少，"
        "建官职实体（其条目在本编后续，提取时同名复用）。",
        quotation=Q,
    )
    tp3 = w.timepoint(
        e3, "北宋政和二年之后", "三孤官，与三公合称“公孤”",
        "据“公孤”条建节点。", Q, attr_category="合称",
    )
    w.citation("Timepoints", tp3, C, Q, "为三少（三孤）节点提供原文证据")
    w.commit()
    return tp


# --------------------------------------------------------------- #36 ----
def entry36():
    C = cite(36)
    Q_DEF = q(36, "太师、太傅、太保之总名。")
    Q_A = q(36, "“三师”之名始于北魏孝文帝太和年间（477—499）："
                "“太和中，高祖诏群僚议定百官，著于令：……太师、太傅、太保右三师。”"
                "（《魏书·官氏志》）")
    Q_B = q(36, "北周改“三师”之名为“三公”，隋朝复置“三师”，唐宋沿用之"
                "（《大唐六典》卷1《三师》）。")
    Q_C = q(36, "北宋政和二年九月，以“古无三师官”为由，改“三师”为“三公”"
                "（《宋诏令》卷163《新定三公辅弼御笔手诏政和二年九月二十五日》）。")
    Q_REF = q(36, "“官品”、“职掌”，分见于“太师”、“太傅”、“太保”条。")
    w = writer(36)
    e = w.entity(
        "三师", "官职",
        "《辞典》90页独立成条，为太师、太傅、太保之总名，建官职实体。",
        quotation=Q_DEF,
    )
    nodes = [
        ("北魏孝文帝太和年间", "始有“三师”之名（太师、太傅、太保为三师）", Q_A, None),
        ("北周", "改“三师”之名为“三公”", Q_B, None),
        ("隋", "复置“三师”，唐宋沿用", Q_B, None),
        ("北宋政和二年九月", "以“古无三师官”为由，改“三师”为“三公”", Q_C, None),
    ]
    tps = chain(w, e, nodes, "总名", C, "本条职源与沿革")
    w.citation("Timepoints", tps[3], C, Q_REF,
               "官品、职掌转见太师、太傅、太保各条", note="分见“太师”、“太傅”、“太保”条")
    w.commit()
    return tps[1], tps[3]  # 北周节点、政和节点（供三师->三公演变）


# --------------------------------------------------------------- #37 ----
def entry37():
    C = cite(37)
    Q_A = q(37, "太师之名，始于西周。")
    Q_B = q(37, "作为三师官，始于后魏。《魏书·官氏志》：“太师、太傅、太保，右三师。”")
    Q_C = q(37, "作为三公官，始于北周（《唐六典》卷1）。")
    Q_D = q(37, "宋前期为三师官（《宋史·职官志》1）。")
    Q_F = q(37, "元丰新制，“三公、三师与诸大夫均为寄禄官”（《宋宰辅》卷9，元祐三年四月）。")
    Q_E = q(37, "北宋政和二年（1112）改为三公官（《宋诏令》卷163《新定三公辅弼御笔手诏》）。")
    Q_I = q(37, "政和二年，改三师为三公，“若除三公，即为宰相”（《职源撮要》）。")
    Q_G = q(37, "宣和七年，太师仍为阶官，不预政事（《宋史·徽宗纪》4）。")
    Q_H = q(37, "宋前期为虚衔，系宰相、使相、亲王等加官。不复有皇帝师、保之任。")
    Q_J1 = q(37, "宋初依唐制，正一品。淳化三年（992）位于尚书令之下（《宋会要·职官》4之1）。")
    Q_J2 = q(37, "元丰新制，正一品（《宋会要·职官》57之55）。")
    w = writer(37)
    e = w.entity(
        "太师", "官职",
        "《辞典》91页独立成条，“加官、阶官名”，建官职实体。",
        quotation=q(37, "加官、阶官名。独政和二年至宣和七年间为真相之名。"),
    )
    nodes = [
        ("西周", "太师之名始见", Q_A, None),
        ("后魏", "作为三师官，始", Q_B, None),
        ("北周", "作为三公官，始", Q_C, None),
        ("宋前期", "为三师官，为虚衔，系宰相、使相、亲王等加官", Q_D, "正一品"),
        ("北宋元丰新制", "为寄禄官", Q_F, "正一品"),
        ("北宋政和二年", "改为三公官，“若除三公，即为宰相”", Q_E, None),
        ("北宋宣和七年", "仍为阶官，不预政事（迄南宋不变）", Q_G, None),
    ]
    tps = chain(w, e, nodes, "加官", C, "本条职源与沿革")
    w.citation("Timepoints", tps[3], C, Q_H, "职掌证据：宋前期虚衔加官", note="职掌")
    w.citation("Timepoints", tps[3], C, Q_J1, "品位证据：宋初正一品、淳化三年位尚书令下", note="品位")
    w.citation("Timepoints", tps[4], C, Q_J2, "品位证据：元丰新制正一品", note="品位")
    w.citation("Timepoints", tps[5], C, Q_I, "职掌证据：若除三公即为宰相", note="职掌")
    w.commit()
    return tps[3], tps[5]


# --------------------------------------------------------------- #38 ----
def entry38():
    C = cite(38)
    Q_A = q(38, "公元前593年，晋国有“大傅”（即太傅）之官，是为始见太傅的可考之年"
                "（《左传·宣公十六年》）。")
    Q_B = q(38, "高后元年（前187年），设太傅，为上公（《汉书·百官公卿表》）。")
    Q_D = q(38, "作为三公官，始于晋。《宋书·百官志》上：“（晋初）自太师至太保，是为三公。”")
    Q_C = q(38, "作为三师官，始置于后魏（《魏书·官氏志》）。")
    Q_E = q(38, "宋前期为三师官（《宋史·职官志》1）。")
    Q_J = q(38, "元丰新制为寄禄官（《宋宰辅》卷9）。")
    Q_F = q(38, "政和二年后为三公官（《宋大诏令集》卷163《新定三公辅弼御笔手诏》）。")
    Q_G = q(38, "宋前期无职事，为亲王、宰相、使相加官，“不预政事”"
                "（《文献通考·职官考》2《三公总序》）。")
    Q_H = q(38, "政和二年，为宰相之任，领三省事（《宋诏令》卷163）。")
    Q_I = q(38, "宣和七年(1125)复元丰之制，“三公但为阶官”（《宋史·徽宗纪》4）。")
    Q_K = q(38, "除班位杂压次于太师，余与太师同。又，其迁转次序，由太傅迁太尉，"
                "太尉迁太师（《宋会要·职官》1之10）。")
    w = writer(38)
    e = w.entity(
        "太傅", "官职",
        "《辞典》91页独立成条，“加官、阶官名”，建官职实体。",
        quotation=q(38, "加官、阶官名。独政和二年至宣和七年三月为真相之名。"),
    )
    nodes = [
        ("西周（前593）", "晋国有“大傅”（即太傅）之官（始见）", Q_A, None),
        ("西汉高后元年", "设太傅，为上公", Q_B, None),
        ("晋", "作为三公官，始", Q_D, None),
        ("后魏", "作为三师官，始置", Q_C, None),
        ("宋前期", "为三师官，无职事，为亲王、宰相、使相加官", Q_E, None),
        ("北宋元丰新制", "为寄禄官", Q_J, None),
        ("北宋政和二年", "为三公官，为宰相之任，领三省事", Q_F, None),
        ("北宋宣和七年", "复元丰之制，“三公但为阶官”", Q_I, None),
    ]
    tps = chain(w, e, nodes, "加官", C, "本条职源与沿革")
    w.citation("Timepoints", tps[4], C, Q_G, "职掌证据：宋前期无职事", note="职掌")
    w.citation("Timepoints", tps[4], C, Q_K, "品位证据：班位次太师、迁转次序", note="品位")
    w.citation("Timepoints", tps[6], C, Q_H, "职掌证据：政和二年为宰相之任领三省事", note="职掌")
    w.commit()
    return tps[4], tps[6]


# --------------------------------------------------------------- #39 ----
def entry39():
    C = cite(39)
    Q_A = q(39, "西周初已有太保之名：“匮侯令堇饴太保于宗周。”（《董鼎》）")
    Q_B = q(39, "作为三公官，始于晋（《宋书·百官志》上）。")
    Q_C = q(39, "作为三师官，始于后魏（《魏书·官氏志》）。")
    Q_D = q(39, "宋前期为三师官（《宋史·职官志》1）。")
    Q_E = q(39, "政和二年(1112)改为三公官。")
    Q_F = q(39, "除位次太师、太傅之外，余皆与“太师”同。又，其迁移次序，太保迁太傅，太傅迁太尉。")
    w = writer(39)
    e = w.entity(
        "太保", "官职",
        "《辞典》91页独立成条，“加官、阶官名”，建官职实体。",
        quotation=q(39, "加官、阶官名。独政和二年至宣和七年为真相名。"),
    )
    nodes = [
        ("西周初", "已有太保之名", Q_A, None),
        ("晋", "作为三公官，始", Q_B, None),
        ("后魏", "作为三师官，始", Q_C, None),
        ("宋前期", "为三师官", Q_D, None),
        ("北宋政和二年", "改为三公官", Q_E, None),
    ]
    tps = chain(w, e, nodes, "加官", C, "本条职源与沿革")
    w.citation("Timepoints", tps[3], C, Q_F,
               "职掌、品位转同“太师”条；迁移次序太保迁太傅、太傅迁太尉", note="职掌品位余同“太师”条")
    w.commit()
    return tps[3], tps[4]


# --------------------------------------------------------------- #40 ----
def entry40():
    C = cite(40)
    Q_DEF = q(40, "宋前期太尉、司徒、司空之总名。")
    Q_A = q(40, "以太尉、司徒、司空为三公官，始于东汉建武二十七年(51)(《后汉书·百官志》1)。")
    Q_B = q(40, "宋初沿置，及至徽宗政和二年九月，“合依三代”之制，"
                "即依《周官》所云“立太师、太傅、太保，兹惟三公，论道经邦”。"
                "以太师、太傅、太保为三公官，罢去太尉、司徒、司空“三公”官之名"
                "（《宋诏令》卷163《新定三公辅弼御笔手诏》，及《尚书·周官》）。")
    Q_REF = q(40, "官品、职掌 分见于“太尉”、“司徒”、“司空”各条。")
    Q_36B = q(36, "北周改“三师”之名为“三公”，隋朝复置“三师”，唐宋沿用之"
                  "（《大唐六典》卷1《三师》）。")
    C36 = cite(36)
    w = writer(40)
    e = w.entity(
        "三公", "官职",
        "《辞典》92页独立成条，宋前期为太尉、司徒、司空之总名，政和后为太师、"
        "太傅、太保之总名，建官职实体。",
        quotation=Q_DEF,
    )
    nodes = [
        ("东汉建武二十七年", "始以太尉、司徒、司空为三公官", Q_A, None),
        ("北周", "改“三师”之名为“三公”（太师、太傅、太保为三公官）", Q_36B, None),
        ("宋初", "沿置（太尉、司徒、司空为三公）", Q_B, None),
        ("北宋政和二年九月", "依《周官》以太师、太傅、太保为三公官，"
         "罢去太尉、司徒、司空“三公”官之名", Q_B, None),
    ]
    tps = chain(w, e, nodes, "总名", C, "本条职源与沿革")
    w.citation("Timepoints", tps[1], C36, Q_36B, "为北周三公节点提供沿革证据（“三师”条）")
    w.citation("Timepoints", tps[3], C, Q_REF,
               "官品、职掌转见太尉、司徒、司空各条", note="分见“太尉”、“司徒”、“司空”各条")

    # 宋前期实例：太尉、司徒、司空（本编后续有条目，先建最小实体）
    inst_song = []
    for name in ("太尉", "司徒", "司空"):
        ei = w.entity(
            name, "官职",
            f"《辞典》92页“三公”条载宋前期{name}为三公官之一，建官职实体"
            f"（其条目在本编后续，提取时同名复用）。",
            quotation=Q_DEF,
        )
        tpi = w.timepoint(
            ei, "宋前期", "为三公官之一（太尉、司徒、司空之总名为三公）",
            "据“三公”条建节点。", Q_DEF, attr_category="总名",
        )
        w.citation("Timepoints", tpi, C, Q_DEF, f"为{name}为三公官实例提供原文证据")
        inst_song.append((name, tpi))
    for name, tpi in inst_song:
        rel = w.relationship(
            tps[2], tpi, "统称与实例",
            f"三公为总名，{name}为其宋前期构成实例，据“三公”条建统称与实例（统称→实例）。",
            Q_DEF,
        )
        w.citation("Relationships", rel, C, Q_DEF, f"为三公→{name}关系提供原文证据")
    w.commit()
    return tps[1], tps[3]


# ------------------------------------------- 关系汇总 ----
def relations(tp31_1, tp31_2, tp_gs, tp_gg, tp_sanshi_bz, tp_sanshi_zh,
              tp_sangong_bz, tp_sangong_zh):
    w = EntryWriter(ENTRY_DB, "第二编关系汇总", "88-92")

    def tp_of(entity, time):
        eid = w.find_entity(entity, "官职")
        assert eid, entity
        tp = w.find_timepoint(eid, time)
        assert tp, f"{entity} {time}"
        return tp

    # 参知政事 <-> 尚书左丞、尚书右丞（副相演变）
    C31 = cite(31)
    Q31A = q(31, "元丰新制罢参知政事，而易以两省侍郎、尚书左丞、尚书右丞为副相之职，"
                 "直至南宋建炎三年复参知政事，尚书左、右丞省去不用"
                 "（《宋史·职官志》1《参知政事》）。")
    Q31B = q(31, "建炎三年四月十三日（庚申）：“尚书右丞李邴改参知政事。”（《要录》卷22)")
    tp_can_ba = tp_of("参知政事", "北宋元丰官制")
    tp_can_fu = tp_of("参知政事", "南宋建炎三年")
    rel = w.relationship(tp_can_ba, tp31_1, "前后演变",
                         "据“尚书左丞、尚书右丞”条，元丰新制罢参知政事，"
                         "易以侍郎、左右丞为副相，建前后演变（来源→后继）。", Q31A)
    w.citation("Relationships", rel, C31, Q31A, "为罢参改丞演变关系提供原文证据")
    rel = w.relationship(tp31_2, tp_can_fu, "前后演变",
                         "据“尚书左丞、尚书右丞”条，建炎三年复参知政事，"
                         "左右丞省去不用，建前后演变（来源→后继）。", Q31B)
    w.citation("Relationships", rel, C31, Q31B, "为复参演变关系提供原文证据")

    # 合称 -> 实例
    C34, C35, C36, C40 = cite(34), cite(35), cite(36), cite(40)
    Q34 = q(34, "宋前期三师、三公合称。")
    Q35 = q(35, "宋政和二年之后，三公、三孤官合称。")
    Q36DEF = q(36, "太师、太傅、太保之总名。")
    Q36C = q(36, "北宋政和二年九月，以“古无三师官”为由，改“三师”为“三公”"
                 "（《宋诏令》卷163《新定三公辅弼御笔手诏政和二年九月二十五日》）。")
    Q36B = q(36, "北周改“三师”之名为“三公”，隋朝复置“三师”，唐宋沿用之"
                 "（《大唐六典》卷1《三师》）。")
    Q40B = q(40, "宋初沿置，及至徽宗政和二年九月，“合依三代”之制，"
                 "即依《周官》所云“立太师、太傅、太保，兹惟三公，论道经邦”。"
                 "以太师、太傅、太保为三公官，罢去太尉、司徒、司空“三公”官之名"
                 "（《宋诏令》卷163《新定三公辅弼御笔手诏》，及《尚书·周官》）。")

    for name, time in (("三师", "隋"), ("三公", "宋初")):
        rel = w.relationship(tp_gs, tp_of(name, time), "统称与实例",
                             f"公师为合称，{name}为其构成一方，据“公师”条建统称与实例。",
                             Q34)
        w.citation("Relationships", rel, C34, Q34, f"为公师→{name}关系提供原文证据")

    rel = w.relationship(tp_gg, tp_of("三公", "北宋政和二年九月"), "统称与实例",
                         "公孤为合称，三公为其构成一方，据“公孤”条建统称与实例。", Q35)
    w.citation("Relationships", rel, C35, Q35, "为公孤→三公关系提供原文证据")
    rel = w.relationship(tp_gg, tp_of("三少", "北宋政和二年之后"), "统称与实例",
                         "公孤为合称，三孤（三少）为其构成一方，据“公孤”条建统称与实例。",
                         Q35)
    w.citation("Relationships", rel, C35, Q35, "为公孤→三少关系提供原文证据")

    # 三师 -> 太师/太傅/太保（三师链无宋前期节点，用“隋（复置三师，唐宋沿用）”节点）
    e_sanshi = w.find_entity("三师", "官职")
    tp_sanshi_use = w.find_timepoint(e_sanshi, "隋")
    for name in ("太师", "太傅", "太保"):
        rel = w.relationship(tp_sanshi_use, tp_of(name, "宋前期"), "统称与实例",
                             f"三师为总名，{name}为其构成实例，据“三师”条建统称与实例。",
                             Q36DEF)
        w.citation("Relationships", rel, C36, Q36DEF, f"为三师→{name}关系提供原文证据")

    # 三师 -> 三公（北周、政和两次改名，前后演变）
    rel = w.relationship(tp_sanshi_bz, tp_sangong_bz, "前后演变",
                         "据“三师”条，北周改“三师”之名为“三公”，建前后演变（来源→后继）。",
                         Q36B)
    w.citation("Relationships", rel, C36, Q36B, "为北周改名演变关系提供原文证据")
    rel = w.relationship(tp_sanshi_zh, tp_sangong_zh, "前后演变",
                         "据“三师”条，政和二年九月改“三师”为“三公”，建前后演变（来源→后继）。",
                         Q36C)
    w.citation("Relationships", rel, C36, Q36C, "为政和改名演变关系提供原文证据")

    # 三公（政和）-> 太师/太傅/太保
    for name, time in (("太师", "北宋政和二年"), ("太傅", "北宋政和二年"), ("太保", "北宋政和二年")):
        rel = w.relationship(tp_sangong_zh, tp_of(name, time), "统称与实例",
                             f"三公为总名，{name}为其政和后构成实例，据“三公”条建统称与实例。",
                             Q40B)
        w.citation("Relationships", rel, C40, Q40B, f"为三公→{name}关系提供原文证据")

    # 尚书左丞、尚书右丞（合称）-> 尚书省左丞/尚书省右丞
    Q31A2 = q(31, "元丰新制罢参知政事，而易以两省侍郎、尚书左丞、尚书右丞为副相之职，"
                  "直至南宋建炎三年复参知政事，尚书左、右丞省去不用"
                  "（《宋史·职官志》1《参知政事》）。")
    for name in ("尚书省左丞", "尚书省右丞"):
        rel = w.relationship(tp31_1, tp_of(name, "北宋元丰新制"), "统称与实例",
                             f"尚书左丞、尚书右丞为合称，{name}为其构成实例，"
                             f"据“尚书左丞、尚书右丞”条建统称与实例。", Q31A2)
        w.citation("Relationships", rel, C31, Q31A2, f"为左右丞→{name}关系提供原文证据")
    w.commit()


if __name__ == "__main__":
    tp31_1, tp31_2 = entry31(); print("31 OK")
    annex861(); print("861(补读) OK")
    annex863(); print("863(补读) OK")
    entry32(); print("32 OK")
    entry33(); print("33 OK")
    tp_gs = entry34(); print("34 OK")
    tp_gg = entry35(); print("35 OK")
    tp_ss_bz, tp_ss_zh = entry36(); print("36 OK")
    entry37(); print("37 OK")
    entry38(); print("38 OK")
    entry39(); print("39 OK")
    tp_sg_bz, tp_sg_zh = entry40(); print("40 OK")
    relations(tp31_1, tp31_2, tp_gs, tp_gg, tp_ss_bz, tp_ss_zh, tp_sg_bz, tp_sg_zh)
    print("relations OK")
    conn = sqlite3.connect(ENTRY_DB)
    for t in ("Entities", "Timepoints", "Relationships", "Citations", "BuildRecords"):
        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    conn.close()
