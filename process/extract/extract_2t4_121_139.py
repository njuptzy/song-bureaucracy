#!/usr/bin/env python3
"""提取 chapter2t4 第 121–139 条：敕令所及其属官、胥吏系统。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")


def load(i):
    with sqlite3.connect(DICT_DB) as c:
        r = c.execute(
            "SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (i,)
        ).fetchone()
    return r[0], r[1], (r[2] or "") + "\n" + "\n".join(
        str(v) for k, v in json.loads(r[3] or "{}").items() if not k.startswith("_")
    )


FULL = {i: load(i) for i in range(121, 140)}


def q(i, s):
    assert s in FULL[i][2], f"#{i} 不含：{s}"
    return s


def writer(i):
    return EntryWriter(ENTRY_DB, FULL[i][0], FULL[i][1])


def cite(i):
    return f"《宋代官制辞典》第{FULL[i][1]}页“{FULL[i][0]}”条"


def ac(w, table, row_id, i, quote, decision, **kwargs):
    return w.citation(table, row_id, cite(i), quote, decision, **kwargs)


def entity(w, title, typ, i, quote, decision):
    return w.entity(title, typ, decision, quotation=quote)


def tp(w, entity_id, time, event, i, quote, category, decision, **kwargs):
    row_id = w.timepoint(
        entity_id, time, event, decision, quote, attr_category=category, **kwargs
    )
    ac(w, "Timepoints", row_id, i, quote, decision)
    return row_id


def rel(w, subject, obj, kind, i, quote, decision, **kwargs):
    row_id = w.relationship(subject, obj, kind, decision, quote, **kwargs)
    ac(w, "Relationships", row_id, i, quote, decision)
    return row_id


def node(w, title, time, typ=None):
    entity_id = w.find_entity(title, typ)
    assert entity_id, f"缺实体 {title}"
    row_id = w.find_timepoint(entity_id, time)
    assert row_id, f"{title} 缺 {time}"
    return entity_id, row_id


def first_node(w, title, typ=None):
    entity_id = w.find_entity(title, typ)
    assert entity_id, f"缺实体 {title}"
    row = w.conn.execute(
        "SELECT id FROM Timepoints WHERE entity_id=? ORDER BY"
        " CASE WHEN prev_id IS NULL THEN 0 ELSE 1 END,id LIMIT 1", (entity_id,)
    ).fetchone()
    assert row, f"{title} 无时间点"
    return entity_id, row[0]


def rechain(w, ids, decision):
    assert all(ids)
    for n, row_id in enumerate(ids):
        w.relink(
            row_id,
            decision,
            prev_id=ids[n - 1] if n else None,
            succ_id=ids[n + 1] if n + 1 < len(ids) else None,
        )


def entry121():
    i = 121
    text = FULL[i][2].split("\n", 1)[0]
    w = writer(i)
    office = entity(w, FULL[i][0], "机构", i, text, "辞典明载为熙宁间编修法令机构。")
    tp(w, office, "北宋熙宁间", "编修诸司敕式；王安石提举机构称编修三司令式并敕（所）", i, text, "编修法令机构名", "建熙宁间机构节点。")
    w.commit()


def entry123():
    i = 123
    text = FULL[i][2].split("\n", 1)[0]
    qstart = q(i, "元祐间编修法令机构名")
    qchange = q(i, "徽宗大观时改为详定一司敕令所")
    w = writer(i)
    source = entity(w, "重修敕令所", "机构", i, text, "辞典明载为编修法令机构。")
    start = tp(w, source, "北宋元祐间", "置重修敕令所，以废改熙丰法", i, text, "编修法令机构名", "建元祐设置节点。")
    end = tp(w, source, "北宋徽宗大观时", "改为详定一司敕令所", i, qchange, "编修法令机构名", "建改名终结节点。")
    successor = entity(w, "详定一司敕令所", "机构", i, qchange, "本条明确重修敕令所的后继机构。")
    successor_tp = tp(w, successor, "北宋徽宗大观时", "由重修敕令所改置", i, qchange, "编修法令机构名", "建大观改置节点。")
    rel(w, end, successor_tp, "前后演变", i, qchange, "重修敕令所改为详定一司敕令所。")
    rechain(w, [start, end], "按元祐设置、大观改名排序")
    w.commit()


def entry124():
    i = 124
    text = FULL[i][2].split("\n", 1)[0]
    w = writer(i)
    source = entity(w, "详定重修敕令所", "机构", i, text, "辞典明载为南宋敕局。")
    start = tp(w, source, "南宋建炎四年", "置详定重修敕令所", i, text, "敕局名", "建始置节点。")
    end = tp(w, source, "南宋绍兴五年", "改为详定一司敕令所", i, text, "敕局名", "建改名终结节点。")
    successor = w.find_entity("详定一司敕令所", "机构") or entity(w, "详定一司敕令所", "机构", i, text, "本条明确后继敕局。")
    successor_tp = tp(w, successor, "南宋绍兴五年", "由详定重修敕令所改置", i, text, "编修法令机构名", "建绍兴改置节点。")
    rel(w, end, successor_tp, "前后演变", i, text, "详定重修敕令所改为详定一司敕令所。")
    rechain(w, [start, end], "按建炎始置、绍兴改名排序")
    w.commit()


def entry125():
    i = 125
    text = FULL[i][2].split("\n", 1)[0]
    w = writer(i)
    office = entity(w, "详定敕令局", "机构", i, text, "辞典明载为敕局。")
    tp(w, office, "南宋光宗绍熙二年", "置详定敕令局", i, text, "敕局名", "建始置节点。")
    w.commit()


def entry126():
    i = 126
    text = FULL[i][2].split("\n", 1)[0]
    w = writer(i)
    office = entity(w, "编修敕令所", "机构", i, text, "辞典明载为敕局。")
    tp(w, office, "南宋宁宗庆元二年", "置编修敕令所", i, text, "敕局名", "建始置节点。")
    w.commit()


def entry122():
    i = 122
    qstart = q(i, "熙宁间审定诸司所编敕、式机构名，与诸司敕式所并存")
    qmerge = q(i, "熙宁八年九月，所有各司编敕机构并入“详定一司敕令所”")
    qperiods = q(i, "徽宗朝、绍兴五年至绍兴末、孝宗乾道六年至淳熙十五年，编修敕令均用此名")
    qduty = q(i, "编修、删定历朝敕、令、格、式与条法，各以本朝年号为名")
    qstaff = q(i, "淳熙十五年所定详定一司敕令所编制为例：提举官二员（宰相兼），同提举一员（执政兼），详定官一员（侍从官兼），正员删定官五员")
    qclerks = q(i, "此外，尚有胥史名目，如供检文字、法司、知杂司、编修文字、书写、守阙等")
    qqiandao = q(i, "据乾道六年详定一司敕令所编制，犹有都大提举诸司官、主管诸司官、承受本所文字官、书奏等员额，或由内侍充，或为书吏")
    qrestore = q(i, "乾道六年秋，复置详定一司敕令所")
    qshaoxing = q(i, "首立详定一司，指绍兴五年置详定一司敕令所")
    w = writer(i)
    office = w.find_entity("详定一司敕令所", "机构") or entity(w, "详定一司敕令所", "机构", i, qstart, "辞典明载为审定、编修法令机构。")
    xining = tp(w, office, "北宋熙宁间", "与诸司敕式所并存，审定诸司所编敕、式", i, qstart, "编修法令机构名", "建熙宁间机构节点。", chain="none")
    merge = tp(w, office, "北宋熙宁八年九月", "合并所有各司编敕机构", i, qmerge, "编修法令机构名", "建熙宁八年合并节点。", chain="none")
    _, huizong = node(w, "详定一司敕令所", "北宋徽宗大观时", "机构")
    ac(w, "Timepoints", huizong, i, qperiods, "补充徽宗朝沿用机构名的证据。", note="本条作徽宗朝概述；大观精确时间由重修敕令所条提供")
    _, shaoxing = node(w, "详定一司敕令所", "南宋绍兴五年", "机构")
    ac(w, "Timepoints", shaoxing, i, qperiods, "补充绍兴五年起沿用机构名的证据。")
    ac(w, "Timepoints", shaoxing, i, qshaoxing, "补充绍兴五年设置证据。")
    shaoxing_end = tp(w, office, "南宋绍兴末", "编修敕令使用详定一司敕令所名至绍兴末", i, qperiods, "编修法令机构名", "建绍兴阶段止点。", chain="none")
    qiandao = tp(w, office, "南宋乾道六年", "复置详定一司敕令所", i, qrestore, "编修法令机构名", "建乾道复置节点。", chain="none")
    chunxi = tp(w, office, "南宋淳熙十五年", "编修敕令仍用此名，并定机构编制", i, qperiods, "编修法令机构名", "建淳熙十五年制度节点。", chain="none")
    ac(w, "Timepoints", xining, i, qduty, "补充机构通行职掌。", note="职掌")
    ac(w, "Timepoints", chunxi, i, qstaff, "补充淳熙十五年官员编制。", note="编制")
    ac(w, "Timepoints", chunxi, i, qclerks, "补充淳熙十五年胥史名目。", note="胥史编制")
    rechain(w, [xining, merge, huizong, shaoxing, shaoxing_end, qiandao, chunxi], "按熙宁、徽宗、绍兴、乾道、淳熙各阶段排序")

    source_en, source_start = node(w, "编修诸司敕式所(令式所)", "北宋熙宁间", "机构")
    source_end = tp(w, source_en, "北宋熙宁八年九月", "并入详定一司敕令所", i, qmerge, "编修法令机构名", "建诸司敕式所合并终结节点。")
    rel(w, source_end, merge, "前后演变", i, qmerge, "各司编敕机构并入详定一司敕令所。")
    rechain(w, [source_start, source_end], "按熙宁间设置、熙宁八年合并排序")

    posts = (
        ("提举修敕令", 2, qstaff),
        ("同提举详定一司敕令", 1, qstaff),
        ("详定一司敕令", 1, qstaff),
        ("详定一司敕令所删定官", 5, qstaff),
    )
    for title, quota, quote in posts:
        post = w.find_entity(title, "官职") or entity(w, title, "官职", i, quote, f"淳熙十五年编制明确列{title}。")
        post_tp = tp(w, post, "南宋淳熙十五年", f"详定一司敕令所编制{quota}员", i, quote, "差遣名", "建淳熙十五年编制节点。")
        rel(w, chunxi, post_tp, "编制隶属", i, quote, f"详定一司敕令所设{title}{quota}员。", staff_quota=quota, staff_type="官")

    clerks = ("供检文字", "法司", "知杂司", "编修文字", "书写人", "守阙")
    for title in clerks:
        clerk = w.find_entity(title, "官职") or entity(w, title, "官职", i, qclerks, f"淳熙十五年胥史名目包括{title}。")
        clerk_tp = tp(w, clerk, "南宋淳熙十五年", "详定一司敕令所胥史", i, qclerks, "吏名", "建淳熙十五年胥史节点。")
        rel(w, chunxi, clerk_tp, "编制隶属", i, qclerks, f"详定一司敕令所设胥史{title}。", staff_type="吏")

    qiandao_posts = (
        ("详定一司敕令所都大提举诸司官", "官", "差遣名"),
        ("主管诸司官", "官", "差遣名"),
        ("详定一司敕令所承受", "官", "差遣名"),
        ("书奏", "吏", "吏名"),
    )
    for title, staff_type, category in qiandao_posts:
        post = w.find_entity(title, "官职") or entity(w, title, "官职", i, qqiandao, f"乾道六年编制明确列{title}。")
        post_tp = tp(w, post, "南宋乾道六年", "详定一司敕令所编制", i, qqiandao, category, "建乾道六年编制节点。")
        rel(w, qiandao, post_tp, "编制隶属", i, qqiandao, f"乾道六年详定一司敕令所设{title}。", staff_type=staff_type)
    w.commit()


def entry127():
    i = 127
    text = FULL[i][2].split("\n", 1)[0]
    qgeneral = q(i, "仁宗天圣以后，均由宰相或执政官提举")
    qxining = q(i, "熙宁三年，同中书门下平章事王安石“提举编修三司令式并敕”")
    qshaoxing = q(i, "绍兴五年，尚书右仆射张浚“兼提举详定一司敕令”")
    w = writer(i)
    post = w.find_entity("提举修敕令", "官职") or entity(w, "提举修敕令", "官职", i, text, "辞典明载为宰执兼官。")
    general = tp(w, post, "北宋仁宗天圣以后", "历朝编修律法由宰相或执政官提举，系衔随敕局名", i, qgeneral, "宰执兼官", "建天圣以后通制节点。")
    xining = tp(w, post, "北宋熙宁三年", "提举编修三司令式并敕", i, qxining, "宰执兼官", "建熙宁实例节点。")
    shaoxing = tp(w, post, "南宋绍兴五年", "兼提举详定一司敕令", i, qshaoxing, "宰执兼官", "建绍兴实例节点。")
    _, late = node(w, "提举修敕令", "南宋淳熙十五年", "官职")
    office121, office121_tp = node(w, "编修诸司敕式所(令式所)", "北宋熙宁间", "机构")
    rel(w, office121_tp, xining, "编制隶属", i, qxining, "熙宁三年编修三司令式并敕由提举官主管。", staff_type="官")
    _, office122_tp = node(w, "详定一司敕令所", "南宋绍兴五年", "机构")
    rel(w, office122_tp, shaoxing, "编制隶属", i, qshaoxing, "绍兴五年详定一司敕令所由提举官主管。", staff_type="官")
    rechain(w, [general, xining, shaoxing, late], "按天圣以后通制、熙宁、绍兴、淳熙排序")
    w.commit()


def entry128():
    i = 128
    text = FULL[i][2].split("\n", 1)[0]
    qquota = q(i, "提举官二，以属宰相；同提举一，以属执政")
    w = writer(i)
    post = w.find_entity("同提举详定一司敕令", "官职") or entity(w, "同提举详定一司敕令", "官职", i, text, "辞典明载为执政兼领敕局的兼官。")
    qiandao = tp(w, post, "南宋乾道七年", "执政官兼领敕局，带同字；梁克家兼同提举", i, text, "兼官名", "建乾道七年实例节点。")
    ac(w, "Timepoints", qiandao, i, qquota, "补充同提举一员、属执政的编制。", note="一员")
    _, late = node(w, "同提举详定一司敕令", "南宋淳熙十五年", "官职")
    _, office = node(w, "详定一司敕令所", "南宋乾道六年", "机构")
    rel(w, office, qiandao, "编制隶属", i, text, "乾道七年同提举兼领详定一司敕令所。", staff_quota=1, staff_type="官")
    rechain(w, [qiandao, late], "按乾道、淳熙排序")
    w.commit()


def entry129():
    i = 129
    qmain = q(i, "差遣名，由侍从官兼充，实际主持敕令所编修的官员。并裁定删定官所修敕令")
    qdate = q(i, "乾道四年，诏差（权）刑部侍郎汪大猷兼详定官")
    qrestore = q(i, "六年，汪大猷奏合行事件，请行删削，于是复置敕令所")
    w = writer(i)
    post = w.find_entity("详定一司敕令", "官职") or entity(w, "详定一司敕令", "官职", i, qmain, "辞典明载为差遣。")
    point = tp(w, post, "南宋乾道四年", "侍从官兼充，主持敕令所编修并裁定删定成果", i, qdate, "差遣名", "建乾道四年实例节点。")
    ac(w, "Timepoints", point, i, qmain, "补充通行职掌与充任资格。", note="侍从官兼充")
    _, late = node(w, "详定一司敕令", "南宋淳熙十五年", "官职")
    office_en = w.find_entity("详定一司敕令所", "机构")
    office_point = tp(w, office_en, "南宋乾道四年", "置详定官，乾道六年复置敕令所", i, qdate, "编修法令机构名", "建详定官设置的同期机构节点。", chain="none")
    ac(w, "Timepoints", office_point, i, qrestore, "补充乾道六年复置前因。", note="沿革")
    rel(w, office_point, point, "编制隶属", i, qmain, "详定一司敕令官主持敕令所编修。", staff_type="官")
    office_order = [w.find_timepoint(office_en, t) for t in ("北宋熙宁间", "北宋熙宁八年九月", "北宋徽宗大观时", "南宋绍兴五年", "南宋绍兴末", "南宋乾道四年", "南宋乾道六年", "南宋淳熙十五年")]
    rechain(w, office_order, "插入乾道四年详定官节点并按历史顺序重排")
    rechain(w, [point, late], "按乾道、淳熙排序")
    w.commit()


def entry130():
    i = 130
    text = FULL[i][2].split("\n", 1)[0]
    w = writer(i)
    post = entity(w, "同详定一司敕令", "官职", i, text, "辞典明载为差遣官。")
    point = tp(w, post, "未知", "详定官同时设数员时，资格略次者带同字", i, text, "差遣官名", "原文无明确时间，建制度事实承载节点。")
    _, office = first_node(w, "详定一司敕令所", "机构")
    rel(w, office, point, "编制隶属", i, text, "同详定一司敕令属详定一司敕令所差遣。", staff_type="官")
    w.commit()


def entry131():
    i = 131
    qmain = q(i, "差遣官名。敕令所属官，职掌比照、删修历朝敕令、条法，编出适用本朝的敕、令、格、式与条法。是敕令所编修事务的承担者")
    qgao = q(i, "（高宗）首立详定一司，自建炎四年六月以前著为《绍兴新法》")
    w = writer(i)
    post = w.find_entity("详定一司敕令所删定官", "官职") or entity(w, "详定一司敕令所删定官", "官职", i, qmain, "辞典明载为差遣官。")
    gao = tp(w, post, "南宋高宗朝", "比照、删修历朝敕令条法，编成本朝法令", i, qgao, "差遣官名", "建高宗朝编修制度节点。")
    ac(w, "Timepoints", gao, i, qmain, "补充通行职掌。", note="职掌")
    _, late = node(w, "详定一司敕令所删定官", "南宋淳熙十五年", "官职")
    _, office = node(w, "详定一司敕令所", "南宋绍兴五年", "机构")
    rel(w, office, gao, "编制隶属", i, qmain, "删定官为详定一司敕令所属官。", staff_type="官")
    rechain(w, [gao, late], "按高宗朝、淳熙排序")
    w.commit()


def entry132():
    i = 132
    text = FULL[i][2].split("\n", 1)[0]
    w = writer(i)
    post = w.find_entity("详定一司敕令所承受", "官职") or entity(w, "详定一司敕令所承受", "官职", i, text, "辞典明载为差遣官。")
    _, point = node(w, "详定一司敕令所承受", "南宋乾道六年", "官职")
    ac(w, "Timepoints", point, i, text, "补充内侍充任及文字进呈、承接职掌。", note="职掌与充任")
    _, office = node(w, "详定一司敕令所", "南宋乾道六年", "机构")
    rel(w, office, point, "编制隶属", i, text, "详定一司敕令所设承受，由内侍充。", staff_type="官")
    w.commit()


def entry133():
    i = 133
    text = FULL[i][2].split("\n", 1)[0]
    qquota = q(i, "修书令差供检文字一名")
    qdate = q(i, "（熙宁三年）以明法王兖为编敕所看检供应诸房条贯文字")
    w = writer(i)
    post = w.find_entity("供检文字", "官职") or entity(w, "供检文字", "官职", i, text, "辞典明载为详定一司敕令所吏名。")
    xining = tp(w, post, "北宋熙宁三年", "寻检、供应编敕所需前后续降文字", i, qdate, "吏名", "建熙宁三年实例节点。")
    ac(w, "Timepoints", xining, i, text, "补充通行职掌。", note="职掌")
    ac(w, "Timepoints", xining, i, qquota, "补充编制一名。", note="一名")
    _, late = node(w, "供检文字", "南宋淳熙十五年", "官职")
    office_en = w.find_entity("详定一司敕令所", "机构")
    office_tp = tp(w, office_en, "北宋熙宁三年", "编敕所设供检文字", i, qdate, "编修法令机构名", "建供检文字关系的同期机构节点。", chain="none")
    rel(w, office_tp, xining, "编制隶属", i, text, "供检文字隶详定一司敕令所。", staff_quota=1, staff_type="吏")
    order = [w.find_timepoint(office_en, t) for t in ("北宋熙宁间", "北宋熙宁三年", "北宋熙宁八年九月", "北宋徽宗大观时", "南宋绍兴五年", "南宋绍兴末", "南宋乾道四年", "南宋乾道六年", "南宋淳熙十五年")]
    rechain(w, order, "插入熙宁三年供检文字节点并按历史顺序重排")
    rechain(w, [xining, late], "按熙宁、淳熙排序")
    w.commit()


def simple_clerk(i, title, category="吏名"):
    text = FULL[i][2].split("\n", 1)[0]
    w = writer(i)
    post = w.find_entity(title, "官职") or entity(w, title, "官职", i, text, f"辞典明载{title}为详定一司敕令所吏名。")
    _, point = node(w, title, "南宋淳熙十五年", "官职")
    ac(w, "Timepoints", point, i, text, f"补充{title}的职掌与隶属证据。", note="职掌")
    _, office = node(w, "详定一司敕令所", "南宋淳熙十五年", "机构")
    rel(w, office, point, "编制隶属", i, text, f"{title}隶详定一司敕令所。", staff_type="吏")
    w.commit()


def entry134():
    simple_clerk(134, "法司")


def entry135():
    simple_clerk(135, "编修文字")


def entry136():
    simple_clerk(136, "书写人")


def entry137():
    i = 137
    text = FULL[i][2].split("\n", 1)[0]
    w = writer(i)
    post = w.find_entity("书奏", "官职") or entity(w, "书奏", "官职", i, text, "辞典明载为详定一司敕令所吏名。")
    _, qiandao = node(w, "书奏", "南宋乾道六年", "官职")
    ac(w, "Timepoints", qiandao, i, text, "补充置于详定官下、祗应行遣的职掌。", note="职掌")
    _, office = node(w, "详定一司敕令所", "南宋乾道六年", "机构")
    rel(w, office, qiandao, "编制隶属", i, text, "书奏隶详定一司敕令所。", staff_type="吏")
    w.commit()


def entry138():
    i = 138
    text = FULL[i][2].split("\n", 1)[0]
    qstaff = q(i, "设详定一司敕令所都大提举诸司官一名，点检文字官一名，主管文字二名，亲事官二人")
    w = writer(i)
    office = entity(w, "详定一司敕令所都大提举诸司", "机构", i, text, "辞典明载为敕令所附属吏人机构。")
    point = tp(w, office, "未知", "掌应办敕令所具体事务", i, text, "敕令所附属吏人机构名", "原文无明确时间，建机构制度事实节点。")
    _, parent = first_node(w, "详定一司敕令所", "机构")
    rel(w, parent, point, "上下级机构", i, text, "都大提举诸司为详定一司敕令所附属机构。")
    posts = (
        ("详定一司敕令所都大提举诸司官", 1, "官"),
        ("点检文字官", 1, "吏"),
        ("主管文字", 2, "吏"),
        ("亲事官", 2, "吏"),
    )
    for title, quota, staff_type in posts:
        post = w.find_entity(title, "官职") or entity(w, title, "官职", i, qstaff, f"附属机构编制明确列{title}。")
        row = w.conn.execute("SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (post,)).fetchone()
        post_tp = row[0] if row else tp(w, post, "未知", f"都大提举诸司编制{quota}人", i, qstaff, "差遣名", "原文无明确时间，建编制节点。")
        ac(w, "Timepoints", post_tp, i, qstaff, f"补充都大提举诸司内{title}{quota}人的编制。", note=f"编制{quota}人")
        rel(w, point, post_tp, "编制隶属", i, qstaff, f"都大提举诸司设{title}{quota}人。", staff_quota=quota, staff_type=staff_type)
    w.commit()


def entry139():
    i = 139
    text = FULL[i][2].split("\n", 1)[0]
    qquota = q(i, "提举诸司官一员")
    w = writer(i)
    post = w.find_entity("详定一司敕令所都大提举诸司官", "官职") or entity(w, "详定一司敕令所都大提举诸司官", "官职", i, text, "辞典明载为差遣官。")
    _, point = node(w, "详定一司敕令所都大提举诸司官", "南宋乾道六年", "官职")
    ac(w, "Timepoints", point, i, text, "补充内侍充任及领都大提举诸司的职掌。", note="职掌与充任")
    ac(w, "Timepoints", point, i, qquota, "补充编制一员。", note="一员")
    _, suboffice = node(w, "详定一司敕令所都大提举诸司", "未知", "机构")
    rel(w, suboffice, point, "编制隶属", i, text, "都大提举诸司官领附属吏人机构。", staff_quota=1, staff_type="官")
    w.commit()


def main():
    entry121()
    # 先建立两条改名来源，使总条可复用精确的大观、绍兴节点。
    entry123()
    entry124()
    entry125()
    entry126()
    entry122()
    entry127()
    entry128()
    entry129()
    entry130()
    entry131()
    entry132()
    entry133()
    entry134()
    entry135()
    entry136()
    entry137()
    entry138()
    entry139()


if __name__ == "__main__":
    main()
