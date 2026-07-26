#!/usr/bin/env python3
"""提取 chapter2t4 第 41–47 条（第二编 附：三师、三公门 余部）。

太尉/司徒/司空/三少复用 #40/#35 建的最小实体（同 time 节点复用、补属性、追加引用）；
三少→少师/少傅/少保建统称与实例；三公（旧）→三孤（三少）建前后演变。
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

IDS = list(range(41, 48))


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


def chain(w, e, nodes, cat, C, src):
    ids = []
    for time, event, quote, grade in nodes:
        tp = w.timepoint(
            e, time, event,
            f"据{src}建{time}节点。", quote,
            attr_category=cat, attr_grade=grade,
        )
        w.citation("Timepoints", tp, C, quote, f"为{time}节点提供证据（{src}）")
        ids.append(tp)
    return ids


# --------------------------------------------------------------- #41 ----
def entry41():
    C = cite(41)
    Q_A = q(41, "始于秦。《礼记·月令》：“（孟夏之月）命太尉，赞杰俊。”郑玄注：“太尉，秦官。”")
    Q_B = q(41, "作为三公官之一，始于后汉。《后汉书·百官志》1：“太尉，公一人。"
                "……国有过事，则与二公通谏争之。”")
    Q_C = q(41, "宋前期为三公官之一（《文献通考·职官志》2《太尉》）。") if False else \
        q(41, "宋前期为三公官之一（《文献通考·职官考》2《太尉》）。")
    Q_ZZ1 = q(41, "宋前期为亲王、宰相、使相加官，无论道经邦之责。")
    Q_ZZ2 = q(41, "元丰新制，三公官起寄禄官阶之用，仍不预政事，领俸禄、示优宠而已"
                  "（《宋宰辅》卷9）。")
    Q_D = q(41, "政和二年(1112)，太尉不复列为三公官，易为武阶官之首阶"
                "（《宋史·职官志》9《国朝武选》）。")
    Q_ZZ3 = q(41, "政和二年九月，“改太尉以冠武阶”（《宋史·徽宗纪》3）。")
    Q_PW1 = q(41, "宋前期为正一品。")
    Q_PW2 = q(41, "政和二年九月，改为武官阶之首，仍正一品（《宋会要·职官》1之12《太尉》）。")
    Q_PW3 = q(41, "政和二年十月三日之后，降为正二品（《宋会要·职官》56之39《官制别录》）。")
    w = writer(41)
    e = w.find_entity("太尉", "官职")
    assert e, "#40 应已建最小实体"
    tp_qin = w.timepoint(
        e, "秦", "始置太尉（秦官）",
        "据本条职源与沿革①建源头节点，接链首。",
        Q_A, attr_category="加官", chain="head",
    )
    w.citation("Timepoints", tp_qin, C, Q_A, "为秦源节点提供沿革证据")
    tp_han = w.timepoint(
        e, "后汉", "作为三公官之一，始",
        "据本条职源与沿革②建节点，接链首（秦之后、宋前期之前）。",
        Q_B, attr_category="加官", chain="none",
    )
    tp_sq = w.find_timepoint(e, "宋前期")
    assert tp_sq
    w.relink(tp_han, prev_id=tp_qin, succ_id=tp_sq, decision="后汉节点插入秦与宋前期之间")
    w.relink(tp_qin, succ_id=tp_han, decision="后汉节点插入其后")
    w.relink(tp_sq, prev_id=tp_han, decision="后汉节点插入其前")
    w.citation("Timepoints", tp_han, C, Q_B, "为后汉三公节点提供沿革证据")
    # 宋前期节点：复用（#40 所建），补官品、追加本条证据
    tp_sq2 = w.timepoint(
        e, "宋前期", "（复用）", "复用宋前期节点，补正一品属性。",
        Q_C, attr_grade="正一品", chain="none",
    )
    assert tp_sq2 == tp_sq
    w.citation("Timepoints", tp_sq, C, Q_C, "本条目佐证宋前期为三公官之一")
    w.citation("Timepoints", tp_sq, C, Q_ZZ1, "职掌证据：为加官，无论道经邦之责", note="职掌")
    w.citation("Timepoints", tp_sq, C, Q_PW1, "品位证据：宋前期正一品", note="品位")
    tp_yf = w.timepoint(
        e, "北宋元丰新制", "三公官起寄禄官阶之用，仍不预政事",
        "据本条职掌②建节点。", Q_ZZ2, attr_category="加官",
    )
    w.citation("Timepoints", tp_yf, C, Q_ZZ2, "为元丰寄禄节点提供职掌证据")
    tp_zh = w.timepoint(
        e, "北宋政和二年九月", "不复列为三公官，改太尉以冠武阶（易为武阶官之首阶）",
        "据本条职源与沿革④及职掌③建节点。", Q_D, attr_category="加官",
        attr_grade="正一品",
    )
    w.citation("Timepoints", tp_zh, C, Q_D, "为政和冠武阶节点提供沿革证据")
    w.citation("Timepoints", tp_zh, C, Q_ZZ3, "职掌证据：改太尉以冠武阶", note="职掌")
    w.citation("Timepoints", tp_zh, C, Q_PW2, "品位证据：改武官阶之首，仍正一品", note="品位")
    tp_ji = w.timepoint(
        e, "北宋政和二年十月三日之后", "降为正二品",
        "据本条品位③建官品变化节点。", Q_PW3, attr_category="加官",
        attr_grade="正二品",
    )
    w.citation("Timepoints", tp_ji, C, Q_PW3, "为降品节点提供品位证据")
    w.commit()


# --------------------------------------------------------------- #42 ----
def entry42():
    C = cite(42)
    Q_A = q(42, "司徒之名，始见于西周。西周早期，金文作：“嗣土”"
                "（《三代吉金文存》六·四三·六《嗣土殴》），晚期作“嗣徒”"
                "（同前书九·二四·二《扬殴》）。文献作“司土”、“司徒”。")
    Q_B = q(42, "西汉哀帝元寿二年，以大司马、大司徒、大司空为三公官，实为丞相之任"
                "（《汉书·哀帝纪》）。")
    Q_C = q(42, "去“大”字，以司徒为真三公官，始于东汉建武二十七年(51)五月"
                "（《后汉书·光武帝纪》）。")
    Q_D = q(42, "宋前期为三公官之一（《宋史·职官志》1《三公》）。")
    Q_E = q(42, "政和二年罢太尉、司徒、司空三公官之名"
                "（《宋诏令》卷163《新定三公辅弼御笔手诏》）。")
    Q_ZZ = q(42, "与政和二年前之“太尉”同，仅班位次于太尉。")
    Q_ZZ2 = q(42, "“凡除授，则自司徒迁太保，自太傅迁太尉”（《宋史·职官志》1《三师、三公》）。")
    Q_GP = q(42, "正一品（《宋会要·职官志》57之56）。")
    w = writer(42)
    e = w.find_entity("司徒", "官职")
    assert e, "#40 应已建最小实体"
    nodes = [
        ("西周", "司徒之名始见（金文作嗣土、嗣徒）", Q_A, None),
        ("西汉哀帝元寿二年", "以大司马、大司徒、大司空为三公官（实为丞相之任）", Q_B, None),
        ("东汉建武二十七年五月", "去“大”字，以司徒为真三公官", Q_C, None),
    ]
    for time, event, quote, grade in nodes:
        tp = w.timepoint(
            e, time, event, f"据本条职源与沿革建{time}节点，接链首。",
            quote, attr_category="加官", chain="head",
        )
        w.citation("Timepoints", tp, C, quote, f"为{time}节点提供沿革证据")
    tp_sq = w.find_timepoint(e, "宋前期")
    assert tp_sq
    tp_sq2 = w.timepoint(
        e, "宋前期", "（复用）", "复用宋前期节点，补正一品属性。",
        Q_D, attr_grade="正一品", chain="none",
    )
    assert tp_sq2 == tp_sq
    w.citation("Timepoints", tp_sq, C, Q_D, "本条目佐证宋前期为三公官之一")
    w.citation("Timepoints", tp_sq, C, Q_ZZ, "职掌证据：与太尉同，班位次太尉", note="职掌")
    w.citation("Timepoints", tp_sq, C, Q_ZZ2, "迁转证据：自司徒迁太保", note="职掌")
    w.citation("Timepoints", tp_sq, C, Q_GP, "官品证据：正一品", note="官品")
    tp_zh = w.timepoint(
        e, "北宋政和二年九月", "罢太尉、司徒、司空三公官之名",
        "据本条职源与沿革④建终结节点。", Q_E, attr_category="加官",
    )
    w.citation("Timepoints", tp_zh, C, Q_E, "为罢三公官名节点提供沿革证据")
    w.commit()


# --------------------------------------------------------------- #43 ----
def entry43():
    C = cite(43)
    Q_A = q(43, "殷商甲骨文中已有“王其令山司我工”（《殷契拾掇》一·431）的记载，"
                "是为“司空”一官之源（参《殷墟卜辞综述》页519）。")
    Q_B = q(43, "西周金文作“嗣工”（《啸堂集古录》94《嗣工毁》）。"
                "文献上作“司空”：“乃召司空，乃召司徒。”（《诗经·大雅·繇》）")
    Q_C = q(43, "作为三公官，始于汉。西汉哀帝元寿二年，改丞相为大司徒、大司空、大司马，"
                "称三公官（《汉书·哀帝纪》）。")
    Q_D = q(43, "至东汉光武帝建武二十七年，去“大”字，以司空为真三公官，备员而已"
                "（《后汉书·光武帝纪》）。")
    Q_E = q(43, "宋前期为三公官之一。")
    Q_F = q(43, "政和二年九月，罢太尉、司徒、司空三公官，其后不置司空官名"
                "（《宋诏令》卷163《新定三公辅弼御笔手诏》）。")
    Q_ZZ = q(43, "与政和二年前之“太尉”同，仅班位次于太尉、司徒。")
    w = writer(43)
    e = w.find_entity("司空", "官职")
    assert e, "#40 应已建最小实体"
    nodes = [
        ("殷商", "甲骨文已有“司我工”记载（司空一官之源）", Q_A, None),
        ("西周", "金文作“嗣工”，文献作“司空”", Q_B, None),
        ("西汉哀帝元寿二年", "改丞相为大司徒、大司空、大司马，称三公官", Q_C, None),
        ("东汉建武二十七年", "去“大”字，以司空为真三公官", Q_D, None),
    ]
    for time, event, quote, grade in nodes:
        tp = w.timepoint(
            e, time, event, f"据本条职源与沿革建{time}节点，接链首。",
            quote, attr_category="加官", chain="head",
        )
        w.citation("Timepoints", tp, C, quote, f"为{time}节点提供沿革证据")
    tp_sq = w.find_timepoint(e, "宋前期")
    assert tp_sq
    tp_sq2 = w.timepoint(
        e, "宋前期", "（复用）", "复用宋前期节点，追加本条证据。",
        Q_E, chain="none",
    )
    assert tp_sq2 == tp_sq
    w.citation("Timepoints", tp_sq, C, Q_E, "本条目佐证宋前期为三公官之一")
    w.citation("Timepoints", tp_sq, C, Q_ZZ, "职掌、品位与太尉同，班位次太尉、司徒",
               note="职掌品位转同“太尉”条")
    tp_zh = w.timepoint(
        e, "北宋政和二年九月", "罢三公官，其后不置司空官名",
        "据本条职源与沿革⑤建终结节点。", Q_F, attr_category="加官",
    )
    w.citation("Timepoints", tp_zh, C, Q_F, "为不置司空节点提供沿革证据")
    w.commit()


# --------------------------------------------------------------- #44 ----
def entry44():
    C = cite(44)
    Q_DEF = q(44, "少师、少傅、少保总名。")
    Q_A = q(44, "“三少”之名始见于《尚书·周官》北宋徽宗政和二年九月二十五日，"
                "立三少新官：“少师、少傅、少保。”（《宋诏令》卷163《新定三公辅弼御笔手诏》）")
    Q_B = q(44, "初为次相之任（《宋会要·职官》1之2）。")
    Q_C = q(44, "宣和七年(1125)之后，为阶官：文武臣授节度使之后，可望加“三少”官："
                "“公孤官如加官、贴职之类，不复有师保之任、论道经邦之责矣。"
                "祖宗之法，除三孤、三公者，必须建节。”（《通考·职官》2《三公总序》）")
    Q_D = q(44, "正一品（《宋史·职官志》8《官品》）。")
    Q_E = q(44, "（政和二年)九月二十五日，太尉、司徒、司空合罢，并依周创立三孤之官，"
                "乃次辅之位。三孤贰公洪化，寅亮天地，或称为三少，为次相之任。")
    w = writer(44)
    e = w.find_entity("三少", "官职")
    assert e, "#35 应已建最小实体"
    tp_li = w.timepoint(
        e, "北宋政和二年九月二十五日", "立三少新官：少师、少傅、少保（初为次相之任）",
        "据本条职源与沿革建立三少节点，接链首。", Q_A, attr_category="总名",
        attr_grade="正一品", chain="head",
    )
    w.citation("Timepoints", tp_li, C, Q_A, "为立三少节点提供沿革证据")
    w.citation("Timepoints", tp_li, C, Q_B, "职掌证据：初为次相之任", note="职掌")
    w.citation("Timepoints", tp_li, C, Q_D, "官品证据：正一品", note="官品")
    tp_jg = w.timepoint(
        e, "北宋宣和七年之后", "为阶官：文武臣授节度使之后，可望加“三少”官",
        "据本条职掌②建节点。", Q_C, attr_category="总名",
    )
    w.citation("Timepoints", tp_jg, C, Q_C, "为阶官节点提供职掌证据")
    # 前后演变：三公（太尉司徒司空，宋初沿置）-> 三孤（三少）
    e_sg = w.find_entity("三公", "官职")
    tp_sg = w.find_timepoint(e_sg, "宋初")
    assert tp_sg
    rel = w.relationship(
        tp_sg, tp_li, "前后演变",
        "据本条别名①，政和二年九月二十五日太尉、司徒、司空合罢，"
        "并依周创立三孤之官为次辅，建前后演变（来源→后继）。", Q_E,
    )
    w.citation("Relationships", rel, C, Q_E, "为三公合罢立三孤演变关系提供原文证据")
    w.commit()
    return tp_li


# --------------------------------------------------------------- #45 ----
def entry45():
    C = cite(45)
    Q_A = q(45, "《尚书·微子》载有“父师、少师”。春秋时，随国、卫国、楚国皆置少师。"
                "如“随人使少师董成”（《左传·桓公六年》）。")
    Q_B = q(45, "作为“三少”官，始于北宋政和二年。")
    Q_REF = q(45, "职掌、官品 参“三少”条。")
    w = writer(45)
    e = w.entity("少师", "官职",
                 "《辞典》93页独立成条，“加官、阶官名。三少官之一”，建官职实体。",
                 quotation=q(45, "加官、阶官名。三少官之一。"))
    tp1 = w.timepoint(
        e, "春秋", "随国、卫国、楚国皆置少师（《尚书·微子》已载“父师、少师”）",
        "据本条职源与沿革①建始见节点。", Q_A, attr_category="加官",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为春秋始见节点提供沿革证据")
    tp2 = w.timepoint(
        e, "北宋政和二年", "作为“三少”官，始置",
        "据本条职源与沿革②建始置节点。", Q_B, attr_category="加官",
    )
    w.citation("Timepoints", tp2, C, Q_B, "为政和始置节点提供沿革证据")
    w.citation("Timepoints", tp2, C, Q_REF, "职掌、官品转引“三少”条", note="职掌官品参“三少”条")
    w.commit()
    return tp2


# --------------------------------------------------------------- #46 ----
def entry46():
    C = cite(46)
    Q_A = q(46, "西周青铜器铭文中已有“小辅”之记载。《三代吉金文存》九·三五·一《师蔑毁》："
                "“既令女更乃祖考嗣小辅。”")
    Q_B = q(46, "春秋齐国已置少傅官。《左传·襄公十九年》：“夙沙卫为少傅。”")
    Q_C = q(46, "北宋政和二年九月始置少傅（《宋会要·职官》1之2《三公、三少》）。")
    Q_REF = q(46, "职掌、官品 参“三少”条。")
    w = writer(46)
    e = w.entity("少傅", "官职",
                 "《辞典》93页独立成条，“加官、阶官名。三少官之一”，建官职实体。",
                 quotation=q(46, "加官、阶官名。三少官之一。"))
    nodes = [
        ("西周", "金文已有“小辅”（读作“小傅”）之记载", Q_A, None),
        ("春秋", "齐国已置少傅官", Q_B, None),
        ("北宋政和二年九月", "始置少傅", Q_C, None),
    ]
    tps = chain(w, e, nodes, "加官", C, "本条职源与沿革")
    w.citation("Timepoints", tps[2], C, Q_REF, "职掌、官品转引“三少”条", note="职掌官品参“三少”条")
    w.commit()
    return tps[2]


# --------------------------------------------------------------- #47 ----
def entry47():
    C = cite(47)
    Q_A = q(47, "少保之名，始见于《尚书·周官》：“少师、少傅、少保为三孤。”"
                "（《汉书·百官表》上转引之）")
    Q_B = q(47, "作为实授之官，始见于北周。《周书·元伟传》："
                "“大将军、尚书令、少保、小司徒、广平郡王元赞。”")
    Q_C = q(47, "北宋政和二年九月置少保，为“三少（三孤）官之一"
                "（《宋会要·职官》1之2《三公、三少》）。")
    Q_REF = q(47, "职掌、官品 参“三少”条。")
    w = writer(47)
    e = w.entity("少保", "官职",
                 "《辞典》93页独立成条，“加官、阶官名。三少官之一”，建官职实体。",
                 quotation=q(47, "加官、阶官名。三少官之一。"))
    nodes = [
        ("周", "少保之名始见于《尚书·周官》（三孤）", Q_A, None),
        ("北周", "作为实授之官，始见", Q_B, None),
        ("北宋政和二年九月", "置少保，为三少（三孤）官之一", Q_C, None),
    ]
    tps = chain(w, e, nodes, "加官", C, "本条职源与沿革")
    w.citation("Timepoints", tps[2], C, Q_REF, "职掌、官品转引“三少”条", note="职掌官品参“三少”条")
    w.commit()
    return tps[2]


# ------------------------------------------- 三少 -> 少师/少傅/少保 ----
def relations(tp_sanshao, tp_shaoshi, tp_shaofu, tp_shaobao):
    C = cite(44)
    Q_DEF = q(44, "少师、少傅、少保总名。")
    w = EntryWriter(ENTRY_DB, "三少", "93")
    for name, tpi in (("少师", tp_shaoshi), ("少傅", tp_shaofu), ("少保", tp_shaobao)):
        rel = w.relationship(
            tp_sanshao, tpi, "统称与实例",
            f"三少为总名，{name}为其构成实例，据“三少”条建统称与实例（统称→实例）。",
            Q_DEF,
        )
        w.citation("Relationships", rel, C, Q_DEF, f"为三少→{name}关系提供原文证据")
    w.commit()


if __name__ == "__main__":
    entry41(); print("41 OK")
    entry42(); print("42 OK")
    entry43(); print("43 OK")
    tp_sanshao = entry44(); print("44 OK")
    tp_shaoshi = entry45(); print("45 OK")
    tp_shaofu = entry46(); print("46 OK")
    tp_shaobao = entry47(); print("47 OK")
    relations(tp_sanshao, tp_shaoshi, tp_shaofu, tp_shaobao)
    print("relations OK")
    conn = sqlite3.connect(ENTRY_DB)
    for t in ("Entities", "Timepoints", "Relationships", "Citations", "BuildRecords"):
        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    conn.close()
