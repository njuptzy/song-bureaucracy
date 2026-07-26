#!/usr/bin/env python3
"""提取 chapter2t4 第 69–73 条：中书五房习学、堂后官、沿堂五院及发敕官改名。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")
IDS = range(69, 74)


def load_entry(entry_id):
    conn = sqlite3.connect(DICT_DB)
    row = conn.execute(
        "SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (entry_id,)
    ).fetchone()
    conn.close()
    full = (row[2] or "") + "\n" + "\n".join(
        str(v) for k, v in json.loads(row[3] or "{}").items() if not k.startswith("_")
    )
    return row[0], row[1], full


FULL = {i: load_entry(i) for i in IDS}


def q(eid, text):
    assert text in FULL[eid][2], f"#{eid} 不含：{text}"
    return text


def cite(eid):
    title, page, _ = FULL[eid]
    return f"《宋代官制辞典》第{page}页“{title}”条"


def writer(eid):
    title, page, _ = FULL[eid]
    return EntryWriter(ENTRY_DB, title, page)


def node(w, title, time, type_=None):
    entity_id = w.find_entity(title, type_)
    assert entity_id, f"缺实体：{title}"
    tp_id = w.find_timepoint(entity_id, time)
    assert tp_id, f"{title} 缺少 time={time} 节点"
    return entity_id, tp_id


def add_cite(w, table, target_id, eid, quote, decision, **kwargs):
    return w.citation(table, target_id, cite(eid), quote, decision, **kwargs)


def staff(w, parent_tp, officer_tp, eid, quote, quota, decision):
    rel = w.relationship(
        parent_tp, officer_tp, "编制隶属", decision, quote,
        staff_quota=quota, staff_type="吏",
    )
    add_cite(w, "Relationships", rel, eid, quote, "为编制隶属及员额提供证据")
    return rel


def entry69():
    eid = 69
    Q_ENT = q(eid, "辛属名。")
    Q_START = q(eid, "熙宁六年(1073)十二月十一日始置（《长编》卷248）。")
    Q_DUTY = q(
        eid,
        "人中书五房习学检正官职事，通过实习，熟悉中书政事，经常参加议论，"
        "以备选拔检正官，如有不称职者，则黜退（《宋会要·职官》4之13）。",
    )
    Q_QUOTA = q(eid, "初户房置一员，后逐房皆置。")
    Q_GRADE = q(eid, "以初入仕的选人充任（《塵史》上《官制》）。")
    Q_END = q(eid, "（元丰官制行）所谓检正、习学之名，悉已罢去。")
    w = writer(eid)
    entity_id = w.entity(
        "中书五房习学公事", "官职",
        "辞典独立成条并标为属名，建官职实体；“辛”照录 OCR，不擅改原文。",
        quotation=Q_ENT,
    )
    tp_start = w.timepoint(
        entity_id, "北宋熙宁六年十二月十一日",
        "始置中书五房习学公事，以初入仕选人入五房习学检正职事",
        "据职源建始置节点。", Q_START, attr_category="属名",
        attr_officer_type="选人",
    )
    for quote, note in (
        (Q_START, "始置"),
        (Q_DUTY, "职掌"),
        (Q_QUOTA, "编制"),
        (Q_GRADE, "品位与任职资格"),
    ):
        add_cite(w, "Timepoints", tp_start, eid, quote, f"为{note}提供证据", note=note)
    tp_end = w.timepoint(
        entity_id, "北宋元丰官制施行时", "检正、习学之名悉罢",
        "简称段仍含元丰官制沿革，按 prompt 建终结节点。", Q_END,
        attr_category="属名",
    )
    add_cite(w, "Timepoints", tp_end, eid, Q_END, "为元丰官制时罢习学之名提供证据")

    five_id, five_last = node(w, "制敕院五房", "北宋咸平二年正月", "机构")
    five_xn = w.timepoint(
        five_id, "北宋熙宁六年十二月十一日", "始置中书五房习学公事",
        "五房的编制在熙宁六年新增习学公事，建对应机构节点。", Q_START,
        attr_category="机构名",
    )
    add_cite(w, "Timepoints", five_xn, eid, Q_START, "为五房新增习学公事提供证据")
    rel = w.relationship(
        five_xn, tp_start, "编制隶属",
        "中书五房设置习学公事；初户房一员，后逐房皆置。", Q_QUOTA,
        staff_type="官",
    )
    add_cite(w, "Relationships", rel, eid, Q_QUOTA, "为五房习学公事编制提供证据")
    w.commit()


def entry70():
    eid = 70
    Q_ENT = q(eid, "中书吏职名。")
    Q_TANG = q(
        eid,
        "唐朝时堂后主事，即宋堂后官（《资治通鉴》卷237，元和元年八月）",
    )
    Q_END = q(
        eid,
        "元丰新制罢，中书省、门下省置录事代之，但尚书省都事仍称为堂后官"
        "（《朝野杂记》甲集卷12《堂后官》）。",
    )
    Q_DUTY = q(
        eid,
        "逐房堂后官三人，一人掌承受皇帝言语，及进书草；一人掌点检书写熟状及呈进；"
        "一人掌敕命用印下发（《宋朝类苑》卷25《中书五房》、《宋会要·职官》3之22）。",
    )
    Q_GRADE = q(eid, "宋初曾定为同正官，五品阶（《宋会要·职官》3之23）。")
    Q_CHUN = q(
        eid,
        "淳化元年位遇与枢密院主事（从八品）相等（同上书卷）。",
    )
    Q_QUOTA = q(
        eid,
        "①中书制敕院孔目房、吏房、户房、兵礼房、刑房各三人。"
        "②淳化元年定为六人，逐房一人，一人都提点五房公事（同上书卷）。",
    )
    w = writer(eid)
    entity_id = w.find_entity("堂后官", "官职")
    assert entity_id, "前批应已有堂后官实体"
    tp_song = w.find_timepoint(entity_id, "宋前期")
    tp_xn = w.find_timepoint(entity_id, "北宋熙宁三年九月")
    assert tp_song and tp_xn

    tp_tang = w.timepoint(
        entity_id, "唐元和元年八月", "唐堂后主事为宋堂后官之源",
        "本条全称与既有堂后官是同一吏职，不另建别名实体；补唐代职源节点。",
        Q_TANG, attr_category="吏职名", chain="head",
    )
    add_cite(w, "Timepoints", tp_tang, eid, Q_TANG, "为唐代职源提供证据")
    tp_early = w.timepoint(
        entity_id, "宋初", "定为同正官、五品阶",
        "据品位字段建宋初节点。", Q_GRADE, attr_category="吏职名",
        attr_grade="五品阶", chain="none",
    )
    w.relink(tp_tang, "宋初节点接在唐代职源之后", succ_id=tp_early)
    w.relink(tp_early, "宋初节点接在既有宋前期节点之前", prev_id=tp_tang, succ_id=tp_song)
    w.relink(tp_song, "宋初节点前插，保持互反", prev_id=tp_early)
    add_cite(w, "Timepoints", tp_early, eid, Q_GRADE, "为宋初同正官、五品阶提供证据")
    add_cite(w, "Timepoints", tp_song, eid, Q_DUTY, "为逐房堂后官职掌提供证据", note="职掌")

    tp_chun = w.timepoint(
        entity_id, "北宋淳化元年", "位遇同枢密院主事，从八品；堂后官定六人",
        "据品位与编制字段建淳化元年节点。", Q_CHUN,
        attr_category="吏职名", attr_grade="从八品", chain="none",
    )
    w.relink(tp_song, "淳化元年节点插在宋前期与熙宁节点之间", succ_id=tp_chun)
    w.relink(tp_chun, "连接宋前期与熙宁节点", prev_id=tp_song, succ_id=tp_xn)
    w.relink(tp_xn, "淳化元年节点前插，保持互反", prev_id=tp_chun)
    add_cite(w, "Timepoints", tp_chun, eid, Q_CHUN, "为淳化元年品位提供证据")
    add_cite(w, "Timepoints", tp_chun, eid, Q_QUOTA, "为淳化元年员额变化提供证据", note="编制")

    tp_end = w.timepoint(
        entity_id, "北宋元丰新制", "中书省、门下省罢堂后官，置录事代之",
        "据职源与沿革建元丰终结节点。", Q_END, attr_category="吏职名",
    )
    add_cite(w, "Timepoints", tp_end, eid, Q_END, "为元丰罢置沿革提供证据")
    record_id = w.find_entity("录事", "官职")
    assert record_id
    record_tp = w.timepoint(
        record_id, "北宋元丰新制", "中书省、门下省置录事，代堂后官",
        "本条直接描述录事在元丰新制代堂后官，补录事节点。", Q_END,
        attr_category="吏职名",
    )
    add_cite(w, "Timepoints", record_tp, eid, Q_END, "为录事代堂后官提供证据")
    evolution = w.relationship(
        tp_end, record_tp, "前后演变",
        "元丰新制罢堂后官，中书省、门下省置录事代之。", Q_END,
    )
    add_cite(w, "Relationships", evolution, eid, Q_END, "为堂后官改置录事提供证据")

    five_id, five_song = node(w, "制敕院五房", "宋前期", "机构")
    five_chun = w.timepoint(
        five_id, "北宋淳化元年", "五房堂后官由逐房三人改为逐房一人，另以一人都提点五房公事",
        "据编制字段建淳化元年员额变化节点。", Q_QUOTA, attr_category="机构名",
        chain="none",
    )
    five_next = w.find_timepoint(five_id, "北宋淳化九年")
    assert five_next
    w.relink(five_song, "插入淳化元年五房编制节点", succ_id=five_chun)
    w.relink(five_chun, "淳化元年节点连接淳化九年", prev_id=five_song, succ_id=five_next)
    w.relink(five_next, "淳化元年节点前插，保持互反", prev_id=five_chun)
    add_cite(w, "Timepoints", five_chun, eid, Q_QUOTA, "为五房淳化元年员额变化提供证据")
    rel_old = w.relationship(
        five_song, tp_song, "编制隶属",
        "淳化元年前五房逐房设堂后官三人。", Q_DUTY,
        staff_quota=3, staff_type="吏",
    )
    add_cite(w, "Relationships", rel_old, eid, Q_DUTY, "为逐房三人及职掌提供证据")
    rel_new = w.relationship(
        five_chun, tp_chun, "编制隶属",
        "淳化元年堂后官定六人：逐房一人，另有一人都提点五房公事。", Q_QUOTA,
        staff_quota=1, staff_type="吏",
    )
    add_cite(w, "Relationships", rel_new, eid, Q_QUOTA, "为淳化元年逐房一人提供证据")
    w.commit()


def entry71():
    eid = 71
    Q_ENT = q(eid, "吏廨名。隶中书门下。")
    Q_DESC = q(eid, "中书制敕院沿堂五院，为中书门下给使的公廨。")
    Q_STAFF = q(
        eid,
        "沿堂五院有行首一人，副行首二人，通引官九人、堂门官七人，直省官十一人，"
        "发敕官五人，驱使官二十二人（《宋会要·职官》1之17）。",
    )
    w = writer(eid)
    entity_id = w.entity(
        "制敕院沿堂五院", "机构", "辞典明载为吏廨并隶中书门下，建机构实体。",
        quotation=Q_ENT,
    )
    tp = w.timepoint(
        entity_id, "宋前期", "为中书门下给使的公廨，隶中书门下",
        "本编为北宋前期中枢机构，按上下文建宋前期节点。", Q_DESC,
        attr_category="吏廨名",
    )
    add_cite(w, "Timepoints", tp, eid, Q_ENT, "为机构性质与隶属提供证据")
    add_cite(w, "Timepoints", tp, eid, Q_DESC, "为沿堂五院职能提供证据")
    _, central_tp = node(w, "中书门下", "宋前期", "机构")
    upper = w.relationship(
        central_tp, tp, "上下级机构", "沿堂五院明载隶中书门下。", Q_ENT,
    )
    add_cite(w, "Relationships", upper, eid, Q_ENT, "为上下级机构关系提供证据")

    posts = (
        ("行首", 1), ("副行首", 2), ("通引官", 9), ("堂门官", 7),
        ("直省官", 11), ("发敕官", 5), ("驱使官", 22),
    )
    for title, quota in posts:
        post_id = w.entity(
            title, "官职", f"本条明确列为沿堂五院给使并有员额，建{title}官职实体。",
            quotation=Q_STAFF,
        )
        post_tp = w.timepoint(
            post_id, "宋前期", f"为制敕院沿堂五院给使，编制{quota}人",
            f"据沿堂五院编制建{title}节点。", Q_STAFF, attr_category="给使名",
        )
        add_cite(w, "Timepoints", post_tp, eid, Q_STAFF, f"为{title}员额提供证据")
        staff(w, tp, post_tp, eid, Q_STAFF, quota, f"沿堂五院设{title}{quota}人。")
    w.commit()


def entry72():
    eid = 72
    Q = q(
        eid,
        "给使名。隶制敕院沿堂五院。掌发送中书敕命。淳化二年改为承旨官"
        "（《宋会要·职官》3之26）。",
    )
    w = writer(eid)
    post_id, post_song = node(w, "发敕官", "宋前期", "官职")
    add_cite(w, "Timepoints", post_song, eid, Q, "为发敕官性质、隶属与职掌提供证据")
    post_end = w.timepoint(
        post_id, "北宋淳化二年", "改名为承旨官",
        "据本条建发敕官改名终结节点。", Q, attr_category="给使名",
    )
    add_cite(w, "Timepoints", post_end, eid, Q, "为淳化二年改名提供证据")
    successor_id = w.entity(
        "承旨官", "官职", "本条明确发敕官于淳化二年改为承旨官，建后继官职实体。",
        quotation=Q,
    )
    successor_tp = w.timepoint(
        successor_id, "北宋淳化二年", "由发敕官改名而来，承接发送中书敕命之职",
        "据本条建立承旨官新置节点。", Q, attr_category="给使名",
    )
    add_cite(w, "Timepoints", successor_tp, eid, Q, "为承旨官改名新置提供证据")
    rel = w.relationship(
        post_end, successor_tp, "前后演变",
        "淳化二年发敕官改为承旨官。", Q,
    )
    add_cite(w, "Relationships", rel, eid, Q, "为发敕官至承旨官前后演变提供证据")
    _, yard_tp = node(w, "制敕院沿堂五院", "宋前期", "机构")
    successor_staff = w.relationship(
        yard_tp, successor_tp, "编制隶属",
        "承旨官由隶沿堂五院的发敕官改名，承接其隶属。", Q, staff_type="吏",
    )
    add_cite(w, "Relationships", successor_staff, eid, Q, "为承旨官隶沿堂五院提供证据")
    w.commit()


def entry73():
    eid = 73
    Q = q(eid, "发敕官之改名。")
    w = writer(eid)
    _, source_tp = node(w, "发敕官", "北宋淳化二年", "官职")
    _, target_tp = node(w, "承旨官", "北宋淳化二年", "官职")
    row = w.conn.execute(
        "SELECT id FROM Relationships WHERE subject_id=? AND object_id=?"
        " AND relation_type='前后演变'", (source_tp, target_tp)
    ).fetchone()
    assert row
    add_cite(w, "Relationships", row[0], eid, Q, "本条直接确认承旨官为发敕官改名")
    add_cite(w, "Timepoints", target_tp, eid, Q, "本条为承旨官改名来源提供补充证据")
    w.commit()


def main():
    entry69()
    entry70()
    entry71()
    entry72()
    entry73()
    print("完成 chapter2t4 #69–#73")


if __name__ == "__main__":
    main()
