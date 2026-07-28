#!/usr/bin/env python3
"""提取 chapter2t4 第571–590条：三馆差遣、崇文院、昭文馆与史馆。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")
)


def load(i):
    with sqlite3.connect(DICT_DB) as c:
        r = c.execute(
            "select title,page,text,fields from chapter2t4 where id=?", (i,)
        ).fetchone()
    return {
        "title": r[0],
        "page": r[1],
        "text": r[2] or "",
        "fields": json.loads(r[3] or "{}"),
    }


F = {i: load(i) for i in range(571, 591)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, field=None):
    return F[i]["fields"][field] if field else F[i]["text"]


def C(i, field=None):
    suffix = f"（{field}字段）" if field else ""
    return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条{suffix}'


def ent(w, title, typ, i, quotation, decision):
    return w.entity(title, typ, decision, quotation=quotation)


def cite(w, table, rid, i, quotation, decision, field=None, **kw):
    return w.citation(table, rid, C(i, field), quotation, decision, **kw)


def tp(w, eid, time, event, i, quotation, category, decision, field=None, **kw):
    tid = w.timepoint(eid, time, event, decision, quotation, attr_category=category, **kw)
    cite(w, "Timepoints", tid, i, quotation, decision, field=field)
    return tid


def rel(w, subject, obj, kind, i, quotation, decision, field=None, citation_kw=None, **kw):
    rid = w.relationship(subject, obj, kind, decision, quotation, **kw)
    cite(
        w,
        "Relationships",
        rid,
        i,
        quotation,
        decision,
        field=field,
        **(citation_kw or {}),
    )
    return rid


def chain(w, tids, decision):
    assert tids and len(tids) == len(set(tids)), tids
    for n, tid in enumerate(tids):
        w.relink(
            tid,
            decision,
            prev_id=tids[n - 1] if n else None,
            succ_id=tids[n + 1] if n + 1 < len(tids) else None,
        )


def find_e(w, title, typ):
    eid = w.find_entity(title, typ)
    assert eid, (title, typ)
    return eid


def find_t(w, eid, time):
    tid = w.find_timepoint(eid, time)
    assert tid, (eid, time)
    return tid


def rewrite_tp(w, tid, time, event, i, quotation, category, decision, field=None,
               officer=None, grade=None):
    row = w.conn.execute(
        "select entity_id,time,event,attr_category,attr_officer_type,attr_grade from Timepoints where id=?",
        (tid,),
    ).fetchone()
    assert row, tid
    duplicate = w.conn.execute(
        "select id from Timepoints where entity_id=? and time=? and id<>?",
        (row[0], time, tid),
    ).fetchone()
    assert not duplicate, (tid, time, duplicate)
    w.conn.execute(
        "update Timepoints set time=?,event=?,quotation=?,attr_category=?,"
        "attr_officer_type=?,attr_grade=? where id=?",
        (
            time,
            event,
            quotation,
            category or row[3],
            officer or row[4],
            grade or row[5],
            tid,
        ),
    )
    w._br(
        "Timepoints",
        tid,
        f"据专条细化既有节点 time={row[1]}、event={row[2]} 为 time={time}、event={event}：{decision}",
    )
    cite(w, "Timepoints", tid, i, quotation, decision, field=field)
    return tid


def update_rel_attrs(w, rid, decision, quota=None, staff_type=None):
    row = w.conn.execute(
        "select staff_quota,staff_type from Relationships where id=?", (rid,)
    ).fetchone()
    assert row, rid
    new_quota = row[0] if quota is None else quota
    new_type = row[1] if staff_type is None else staff_type
    if (new_quota, new_type) != (row[0], row[1]):
        w.conn.execute(
            "update Relationships set staff_quota=?,staff_type=? where id=?",
            (new_quota, new_type, rid),
        )
        w._br(
            "Relationships",
            rid,
            f"据专条补充编制属性 quota {row[0]}->{new_quota}, staff_type {row[1]}->{new_type}：{decision}",
        )


def ensure_post(w, title, time, i, quotation, category, decision, field=None,
                officer=None, grade=None):
    eid = ent(w, title, "官职", i, quotation, f"原文编制或专条明载{title}。")
    tid = tp(
        w,
        eid,
        time,
        "设置或在编",
        i,
        quotation,
        category,
        decision,
        field=field,
        attr_officer_type=officer,
        attr_grade=grade,
        chain="none",
    )
    return eid, tid


def entry571_572():
    i = 571
    z = Q(i)
    w = W(i)
    eid = ent(w, F[i]["title"], "官职", i, z, "原文明载为差遣名。")
    tid = tp(
        w,
        eid,
        "北宋咸平元年十二月",
        "始置，掌馆阁图书保管，位次于监三馆书籍秘阁图书官",
        i,
        z,
        "馆阁差遣",
        "建点检三馆秘阁书籍始置节点。",
        attr_officer_type="朝臣、内侍",
    )
    parent = find_e(w, "三馆秘阁", "机构")
    rel(
        w,
        find_t(w, parent, "北宋端拱元年五月"),
        tid,
        "编制隶属",
        i,
        z,
        "该差遣掌三馆秘阁图书保管。",
        staff_type="官",
    )
    w.commit()

    i = 572
    z = Q(i)
    w = W(i)
    eid = ent(w, F[i]["title"], "官职", i, z, "原文明载为差遣名。")
    tid = tp(
        w,
        eid,
        "北宋天禧五年十二月",
        "临时特置，与内侍监官同掌三馆秘阁图书事",
        i,
        z,
        "馆阁差遣",
        "建同勾当三馆秘阁事始置节点。",
        attr_officer_type="三班使臣",
    )
    parent = find_e(w, "三馆秘阁", "机构")
    rel(
        w,
        find_t(w, parent, "北宋大中祥符八年至天圣九年十一月"),
        tid,
        "编制隶属",
        i,
        z,
        "该差遣与内侍监官同掌三馆秘阁图书事。",
        staff_type="官",
    )
    w.commit()


def entry573():
    i = 573
    z = Q(i)
    w = W(i)
    tang_e = ent(w, "崇文馆", "机构", i, z, "原文明载唐贞观十三年置崇文馆。")
    tp(w, tang_e, "唐贞观十三年", "置崇文馆", i, z, "文馆机构", "建唐代崇文馆节点。")

    eid = ent(w, "崇文院", "机构", i, z, "原文明载为昭文馆、集贤院、史馆总名。")
    start = tp(
        w,
        eid,
        "北宋太平兴国三年二月一日",
        "始以三馆为崇文院",
        i,
        z,
        "文馆机构统称",
        "建崇文院始置节点。",
        chain="none",
    )
    middle = tp(
        w,
        eid,
        "北宋端拱元年五月",
        "秘阁建于崇文院中堂",
        i,
        z,
        "文馆机构",
        "建秘阁入院节点。",
        chain="none",
    )
    end = tp(
        w,
        eid,
        "北宋元丰五年",
        "改为秘书省",
        i,
        z,
        "文馆机构",
        "建崇文院改制终结节点。",
        chain="none",
    )
    chain(w, [start, middle, end], "按太平兴国、端拱、元丰排序崇文院沿革。")

    member_tids = {}
    for title in ("昭文馆", "集贤院", "史馆"):
        me = ent(w, title, "机构", i, z, f"原文明载{title}为崇文院构成机构。")
        mt = tp(
            w,
            me,
            "北宋太平兴国三年二月一日",
            "为崇文院三馆之一",
            i,
            z,
            "文馆机构",
            f"建{title}作为崇文院成员节点。",
            chain="none",
        )
        member_tids[title] = mt
        rel(w, start, mt, "统称与实例", i, z, f"崇文院为包括{title}在内的三馆总名。")

    secretary = ent(w, "秘书省", "机构", i, z, "原文明载元丰五年以崇文院为秘书省。")
    secretary_start = tp(
        w,
        secretary,
        "北宋元丰五年",
        "由崇文院改置",
        i,
        z,
        "中央文馆机构",
        "建秘书省元丰改置节点。",
        chain="none",
    )
    rel(w, end, secretary_start, "前后演变", i, z, "崇文院于元丰五年改为秘书省。")

    for title in ("昭文馆", "集贤院"):
        me = find_e(w, title, "机构")
        mt = tp(
            w,
            me,
            "北宋元丰五年",
            "罢置",
            i,
            z,
            "文馆机构",
            f"建{title}元丰罢置节点。",
            chain="none",
        )
        old = [r[0] for r in w.conn.execute(
            "select id from Timepoints where entity_id=? and id<>? order by id", (me, mt)
        )]
        # 当前两机构节点均为宋前期、太平兴国、端拱及本次终结；按明确年代重排。
        times = [
            w.find_timepoint(me, "宋前期"),
            w.find_timepoint(me, "北宋太平兴国三年二月一日"),
            w.find_timepoint(me, "北宋端拱元年五月"),
            mt,
        ]
        chain(w, [x for x in times if x], f"重排{title}宋前期至元丰罢置链。")

    history = find_e(w, "史馆", "机构")
    history_end = tp(
        w,
        history,
        "北宋元丰五年",
        "并入秘书省著作局，不复作为三馆机构",
        i,
        z,
        "文馆机构",
        "建史馆元丰归并节点。",
        chain="none",
    )
    authors = ent(w, "著作局", "机构", i, z, "原文明载史馆并入秘书省著作局。")
    authors_start = tp(
        w,
        authors,
        "北宋元丰五年",
        "承接史馆职事",
        i,
        z,
        "秘书省属局",
        "建著作局承接史馆节点。",
        chain="none",
    )
    rel(w, history_end, authors_start, "前后演变", i, z, "史馆于元丰五年并入秘书省著作局。")
    chain(
        w,
        [
            find_t(w, history, "宋前期"),
            find_t(w, history, "北宋太平兴国三年二月一日"),
            find_t(w, history, "北宋端拱元年五月"),
            history_end,
        ],
        "重排史馆宋前期至元丰归并链。",
    )
    w.commit()


def entry574_575():
    i = 574
    z = Q(i)
    w = W(i)
    parent = find_e(w, "崇文院", "机构")
    split = tp(
        w,
        parent,
        "北宋大中祥符八年",
        "火灾后分建崇文内院、崇文外院",
        i,
        z,
        "文馆机构",
        "建崇文院火灾分院节点。",
        chain="none",
    )
    merge = tp(
        w,
        parent,
        "北宋天圣九年十一月八日",
        "内外院合并，仍为崇文院",
        i,
        z,
        "文馆机构",
        "建崇文院复合节点。",
        chain="none",
    )
    chain(
        w,
        [
            find_t(w, parent, "北宋太平兴国三年二月一日"),
            find_t(w, parent, "北宋端拱元年五月"),
            split,
            merge,
            find_t(w, parent, "北宋元丰五年"),
        ],
        "插入大中祥符分院、天圣复合节点。",
    )

    outer = ent(w, "崇文外院", "机构", i, z, "原文明载三馆迁置后称崇文外院。")
    outer_start = tp(
        w,
        outer,
        "北宋大中祥符八年",
        "三馆徙左、右掖门外道北，称崇文外院",
        i,
        z,
        "临时馆额",
        "建崇文外院始置节点。",
        chain="none",
    )
    outer_name = tp(
        w,
        outer,
        "北宋天禧元年八月",
        "以三馆为额",
        i,
        z,
        "临时馆额",
        "建崇文外院馆额节点。",
        chain="none",
    )
    outer_end = tp(
        w,
        outer,
        "北宋天圣九年十一月八日",
        "迁回左掖门内并与崇文内院合并",
        i,
        z,
        "临时馆额",
        "建崇文外院合并终结节点。",
        chain="none",
    )
    chain(w, [outer_start, outer_name, outer_end], "连接崇文外院置、额、并节点。")

    inner = ent(w, "崇文内院", "机构", i, z, "原文明载以旧秘阁修建崇文内院。")
    inner_start = tp(
        w,
        inner,
        "北宋大中祥符八年五月",
        "以旧秘阁修建，行秘阁职事",
        i,
        z,
        "文馆机构",
        "建崇文内院始置节点。",
        chain="none",
    )
    inner_end = tp(
        w,
        inner,
        "北宋天圣九年十一月八日",
        "与崇文外院合并，仍为崇文院",
        i,
        z,
        "文馆机构",
        "建崇文内院合并终结节点。",
        chain="none",
    )
    chain(w, [inner_start, inner_end], "连接崇文内院置、并节点。")
    rel(w, split, outer_start, "前后演变", i, z, "崇文院火灾后分置崇文外院。")
    rel(w, split, inner_start, "前后演变", i, z, "崇文院火灾后以旧秘阁修建崇文内院。")
    rel(w, outer_end, merge, "前后演变", i, z, "崇文外院迁回并恢复为崇文院。")
    rel(w, inner_end, merge, "前后演变", i, z, "崇文内院与外院合并恢复为崇文院。")

    for title in ("昭文馆", "集贤院", "史馆"):
        me = find_e(w, title, "机构")
        mt = tp(
            w,
            me,
            "北宋大中祥符八年",
            "迁入崇文外院",
            i,
            z,
            "文馆机构",
            f"建{title}迁入崇文外院节点。",
            chain="none",
        )
        rel(w, outer_start, mt, "统称与实例", i, z, f"崇文外院为{title}等三馆临时馆额。")
        chain(
            w,
            [
                find_t(w, me, "宋前期"),
                find_t(w, me, "北宋太平兴国三年二月一日"),
                find_t(w, me, "北宋端拱元年五月"),
                mt,
                find_t(w, me, "北宋元丰五年"),
            ],
            f"把{title}迁入崇文外院节点插入宋前期至元丰沿革链。",
        )
    w.commit()

    i = 575
    z = Q(i)
    w = W(i)
    inner = find_e(w, "崇文内院", "机构")
    a = tp(
        w,
        inner,
        "北宋大中祥符八年五月",
        "以火灾后原秘阁旧处修建，行秘阁职事",
        i,
        z,
        "文馆机构",
        "专条补证崇文内院始置与职事。",
        chain="none",
    )
    b = tp(
        w,
        inner,
        "北宋天圣九年十一月八日",
        "崇文内院时段终结",
        i,
        z,
        "文馆机构",
        "专条补证崇文内院终止日期。",
        chain="none",
    )
    chain(w, [a, b], "据专条确认崇文内院起止。")
    w.commit()


def entry576_577():
    i = 576
    z = Q(i)
    w = W(i)
    eid = find_e(w, "崇文院检讨", "官职")
    tid = find_t(w, eid, "北宋元丰改制前")
    row = w.conn.execute("select attr_officer_type from Timepoints where id=?", (tid,)).fetchone()
    if not row[0]:
        w.conn.execute("update Timepoints set attr_officer_type='京官' where id=?", (tid,))
        w._br("Timepoints", tid, "本条明载崇文院检讨以京官充，补任官类型。")
    cite(w, "Timepoints", tid, i, z, "补证馆职性质、任官类型与校勘书籍等职务。")
    parent = find_e(w, "崇文院", "机构")
    rel(
        w,
        find_t(w, parent, "北宋太平兴国三年二月一日"),
        tid,
        "编制隶属",
        i,
        z,
        "崇文院检讨参预崇文院馆务。",
        staff_type="官",
    )
    w.commit()

    i = 577
    z = Q(i)
    w = W(i)
    eid = ent(w, "崇文院校书", "官职", i, z, "原文明载为试官名。")
    tid = tp(
        w,
        eid,
        "宋代（未载具体年月）",
        "选有文学者入馆备访问差使；二年后按实绩转馆职、实职或外差遣",
        i,
        z,
        "试官",
        "建崇文院校书制度节点。",
    )
    parent = find_e(w, "崇文院", "机构")
    rel(
        w,
        find_t(w, parent, "北宋太平兴国三年二月一日"),
        tid,
        "编制隶属",
        i,
        z,
        "崇文院校书为崇文院试官。",
        staff_type="官",
    )
    w.commit()


def entry578():
    i = 578
    h = Q(i, "职源与沿革")
    duty = Q(i, "职能")
    order = Q(i, "序位")
    comp = Q(i, "编制")
    w = W(i)

    repair = ent(w, "修文馆", "机构", i, h, "原文明载唐武德四年置修文馆。")
    repair_start = tp(w, repair, "唐武德四年", "置修文馆", i, h, "文馆机构", "建修文馆始置节点。", field="职源与沿革", chain="none")
    repair_end = tp(w, repair, "唐武德九年", "改称弘文馆", i, h, "文馆机构", "建修文馆改名节点。", field="职源与沿革", chain="none")
    chain(w, [repair_start, repair_end], "连接修文馆置、改节点。")

    hong = ent(w, "弘文馆", "机构", i, h, "原文明载修文馆改称弘文馆及其后复名。")
    hong_626 = tp(w, hong, "唐武德九年", "由修文馆改称弘文馆", i, h, "文馆机构", "建弘文馆改称节点。", field="职源与沿革", chain="none")
    hong_705 = tp(w, hong, "唐神龙元年", "避讳改称昭文馆", i, h, "文馆机构", "建弘文馆避讳改名节点。", field="职源与沿革", chain="none")
    hong_719 = tp(w, hong, "唐开元七年", "复称弘文馆", i, h, "文馆机构", "建弘文馆复名节点。", field="职源与沿革", chain="none")
    hong_song = tp(w, hong, "宋初", "沿置弘文馆", i, h, "文馆机构", "建弘文馆宋初沿置节点。", field="职源与沿革", chain="none")
    hong_960 = tp(w, hong, "北宋建隆元年二月", "避讳改为昭文馆", i, h, "文馆机构", "建弘文馆宋代改名节点。", field="职源与沿革", chain="none")
    chain(w, [hong_626, hong_705, hong_719, hong_song, hong_960], "连接弘文馆唐宋沿革。")

    eid = find_e(w, "昭文馆", "机构")
    z705 = tp(w, eid, "唐神龙元年", "由弘文馆避讳改称昭文馆", i, h, "文馆机构", "建唐代昭文馆改称节点。", field="职源与沿革", chain="none")
    z719 = tp(w, eid, "唐开元七年", "复改为弘文馆", i, h, "文馆机构", "建唐代昭文馆复名终结节点。", field="职源与沿革", chain="none")
    z960 = tp(w, eid, "北宋建隆元年二月", "由弘文馆避讳改称昭文馆", i, h, "文馆机构", "建宋代昭文馆改称节点。", field="职源与沿革", chain="none")
    z1082 = find_t(w, eid, "北宋元丰五年")
    cite(w, "Timepoints", z1082, i, h, "专条补证元丰五年四月罢昭文馆。", field="职源与沿革")
    chain(
        w,
        [
            z705,
            z719,
            z960,
            find_t(w, eid, "宋前期"),
            find_t(w, eid, "北宋太平兴国三年二月一日"),
            find_t(w, eid, "北宋端拱元年五月"),
            find_t(w, eid, "北宋大中祥符八年"),
            z1082,
        ],
        "按唐代改名、宋代改名及三馆沿革重排昭文馆时间链。",
    )
    rel(w, repair_end, hong_626, "前后演变", i, h, "修文馆于唐武德九年改称弘文馆。", field="职源与沿革")
    rel(w, hong_705, z705, "前后演变", i, h, "弘文馆于唐神龙元年改称昭文馆。", field="职源与沿革")
    rel(w, z719, hong_719, "前后演变", i, h, "昭文馆于唐开元七年复称弘文馆。", field="职源与沿革")
    rel(w, hong_960, z960, "前后演变", i, h, "弘文馆于宋建隆元年二月改称昭文馆。", field="职源与沿革")

    parent = find_e(w, "崇文院", "机构")
    rel(w, find_t(w, parent, "北宋太平兴国三年二月一日"), find_t(w, eid, "北宋太平兴国三年二月一日"), "上下级机构", i, Q(i), "昭文馆隶属崇文院。")
    focus = find_t(w, eid, "北宋太平兴国三年二月一日")
    cite(w, "Timepoints", focus, i, duty, "补证昭文馆书库、藏校书籍及储才职能。", field="职能", note="职能")
    cite(w, "Timepoints", focus, i, order, "补证昭文馆在三馆中位居史馆之上。", field="序位", note="序位")
    cite(w, "Timepoints", focus, i, comp, "补证昭文馆官额与吏额。", field="编制", note="编制")

    position_specs = (
        ("昭文馆大学士", 1),
        ("昭文馆学士", None),
        ("昭文馆直学士", None),
        ("直昭文馆", None),
        ("判昭文馆事", None),
    )
    for title, quota in position_specs:
        pe, pt = ensure_post(w, title, "北宋元丰改制前", i, comp, "馆职", f"据昭文馆编制建立{title}节点。", field="编制")
        rel(w, z960, pt, "编制隶属", i, comp, f"昭文馆馆职额列{title}。", field="编制", staff_quota=quota, staff_type="官")

    clerk_specs = (("孔目官", 1), ("书库官", 1), ("守当官", 3), ("楷书", 5))
    for title, quota in clerk_specs:
        ce = ent(w, title, "官职", i, comp, f"昭文馆吏额明列{title}。")
        ct = w.find_timepoint(ce, "宋前期") or tp(w, ce, "宋前期", "昭文馆吏额", i, comp, "吏职", f"建{title}宋前期吏额节点。", field="编制", chain="none")
        rel(w, find_t(w, eid, "宋前期"), ct, "编制隶属", i, comp, f"昭文馆吏额列{title}{quota}人。", field="编制", staff_quota=quota, staff_type="吏")
    w.commit()


def entry579_582():
    i = 579
    h = Q(i, "职源与沿革")
    duty = Q(i, "职能")
    grade = Q(i, "品位")
    w = W(i)
    predecessor = ent(w, "弘文馆大学士", "官职", i, h, "原文明载宋建隆元年二月由弘文馆大学士改称。")
    p = tp(w, predecessor, "北宋建隆元年二月", "改称昭文馆大学士", i, h, "馆职", "建弘文馆大学士改名节点。", field="职源与沿革", chain="none")
    eid = find_e(w, "昭文馆大学士", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    song = rewrite_tp(w, old, "北宋建隆元年二月", "由弘文馆大学士改称，为首相所带职名", i, h, "馆职", "据专条把宽泛馆职节点细化为建隆改称节点。", field="职源与沿革")
    tang = tp(w, eid, "唐神龙元年", "始置昭文馆大学士", i, h, "馆职", "建唐代始置节点。", field="职源与沿革", chain="none")
    short = Q(i, "简称")
    witness = tp(w, eid, "北宋皇祐五年闰七月", "已见宰相带昭文馆大学士", i, short, "馆职", "建皇祐年间带职实见节点。", field="简称", chain="none")
    end = tp(w, eid, "北宋熙宁九年十月二十三日", "罢置，不再复置", i, h, "馆职", "建昭文馆大学士罢置节点。", field="职源与沿革", chain="none")
    chain(w, [tang, song, witness, end], "连接昭文馆大学士唐代始置、宋代改称、皇祐实见与熙宁罢置。")
    rel(w, p, song, "前后演变", i, h, "弘文馆大学士于建隆元年二月改称昭文馆大学士。", field="职源与沿革")
    cite(w, "Timepoints", song, i, duty, "补证首相带职及馆内无实职事。", field="职能", note="职能")
    cite(w, "Timepoints", song, i, grade, "补证三馆职名中品位最高。", field="品位", note="品位")
    cite(w, "Timepoints", song, i, short, "补证置二相时首相领昭文、修史。", field="简称", note="简称段制度事实")
    monitor = find_e(w, "监修国史", "官职")
    tp(w, monitor, "北宋皇祐五年闰七月", "已见宰相兼监修国史", i, short, "馆职", "本条直接证明皇祐年间监修国史带职。", field="简称", chain="none")
    office = find_e(w, "昭文馆", "机构")
    rel(w, find_t(w, office, "北宋建隆元年二月"), song, "编制隶属", i, duty, "昭文馆大学士为昭文馆职名，由首相带领。", field="职能", staff_type="官")
    w.commit()

    i = 580
    z = Q(i)
    comp = Q(i, "省称")
    w = W(i)
    office = find_e(w, "昭文馆", "机构")
    ot = tp(w, office, "北宋嘉祐四年六月", "置编校昭文馆书籍", i, z, "文馆机构", "建昭文馆嘉祐增置实事官节点。", chain="none")
    chain(w, [
        find_t(w, office, "唐神龙元年"), find_t(w, office, "唐开元七年"),
        find_t(w, office, "北宋建隆元年二月"), find_t(w, office, "宋前期"),
        find_t(w, office, "北宋太平兴国三年二月一日"), find_t(w, office, "北宋端拱元年五月"),
        find_t(w, office, "北宋大中祥符八年"), ot, find_t(w, office, "北宋元丰五年")
    ], "插入昭文馆嘉祐四年编校官节点。")
    eid = ent(w, "编校昭文馆书籍", "官职", i, z, "原文明载为馆阁实事官名。")
    tid = tp(w, eid, "北宋嘉祐四年六月", "始置，整理校对馆藏；供职二年可转馆阁校勘", i, z, "馆阁实事官", "建编校昭文馆书籍始置节点。")
    cite(w, "Timepoints", tid, i, comp, "补读省称字段；仅取其中编校官制度例证，不建别称实体。", field="省称", note="省称段制度例证")
    rel(w, ot, tid, "编制隶属", i, z, "昭文馆于嘉祐四年置编校昭文馆书籍。", staff_type="官")
    w.commit()

    i = 581
    h = Q(i, "职源与沿革")
    duty = Q(i, "职能")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "直昭文馆", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    start = rewrite_tp(w, old, "北宋淳化元年八月二十五日", "始除授直昭文馆", i, h, "馆职", "据专条细化此前编制节点。", field="职源与沿革")
    tang = tp(w, eid, "唐朝", "已有直馆之名", i, h, "馆职", "建唐代职源节点。", field="职源与沿革", chain="none")
    early = tp(w, eid, "北宋建国之初", "已有直昭文馆之名但未除人", i, h, "馆职", "建宋初有名未除节点。", field="职源与沿革", chain="none")
    used = tp(w, eid, "北宋淳化二年", "已见以他官兼直昭文馆", i, duty, "馆职", "建淳化二年实际兼带节点。", field="职能", chain="none")
    chain(w, [tang, early, start, used], "连接直昭文馆唐代职源、宋初有名、淳化始除与实见。")
    cite(w, "Timepoints", start, i, duty, "补证预馆务及贴职性质。", field="职能", note="职能")
    cite(w, "Timepoints", start, i, grade, "补证位于校理之上、学士之下。", field="品位", note="品位")
    cite(w, "Timepoints", start, i, comp, "补证无定员。", field="编制", note="编制")
    office = find_e(w, "昭文馆", "机构")
    rel(w, find_t(w, office, "北宋建隆元年二月"), start, "编制隶属", i, duty, "直昭文馆预昭文馆馆务。", field="职能", staff_type="官")
    w.commit()

    i = 582
    h = Q(i, "职源与沿革")
    duty = Q(i, "职能")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "判昭文馆事", "官职")
    tang = tp(w, eid, "隋朝", "已有判馆事之名", i, h, "馆职", "建隋代职源节点。", field="职源与沿革", chain="none")
    tang2 = tp(w, eid, "唐武则天垂拱以后", "常以给事中兼判昭文馆事", i, h, "馆职", "建唐代判馆节点。", field="职源与沿革", chain="none")
    song = find_t(w, eid, "北宋元丰改制前")
    cite(w, "Timepoints", song, i, h, "补证宋沿置。", field="职源与沿革")
    end = tp(w, eid, "北宋元丰五年", "改制罢", i, h, "馆职", "建判昭文馆事罢置节点。", field="职源与沿革", chain="none")
    chain(w, [tang, tang2, song, end], "连接判昭文馆事隋唐职源、宋沿置与元丰罢置。")
    cite(w, "Timepoints", song, i, duty, "补证预馆务及贴职性质。", field="职能", note="职能")
    cite(w, "Timepoints", song, i, grade, "补证任官资格与序位。", field="品位", note="品位")
    cite(w, "Timepoints", song, i, comp, "补证一员。", field="编制", note="编制")
    office = find_e(w, "昭文馆", "机构")
    rid = rel(w, find_t(w, office, "北宋建隆元年二月"), song, "编制隶属", i, comp, "昭文馆置判昭文馆事一员。", field="编制", staff_quota=1, staff_type="官")
    update_rel_attrs(w, rid, "判昭文馆事专条明载一员。", quota=1, staff_type="官")
    w.commit()


def entry583():
    i = 583
    h = Q(i, "职源与沿革")
    duty = Q(i, "职能")
    order = Q(i, "序位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "史馆", "机构")
    north_qi = tp(w, eid, "北齐", "已有史馆之名", i, h, "文馆机构", "建北齐职源节点。", field="职源与沿革", chain="none")
    tang = tp(w, eid, "唐贞观三年十二月", "置史馆于禁中，专掌国史", i, h, "文馆机构", "建唐代史馆节点。", field="职源与沿革", chain="none")
    song = tp(w, eid, "宋初", "沿置史馆", i, h, "文馆机构", "建宋初沿置节点。", field="职源与沿革", chain="none")
    reform = find_t(w, eid, "北宋元丰五年")
    cite(w, "Timepoints", reform, i, h, "本条另记史馆归入秘书省国史案，不复有史馆之名。", field="职源与沿革", conflict_flag=1, note="第573条记并入秘书省著作局；本条另记入国史案。")
    restore = tp(w, eid, "南宋建炎元年五月", "于秘书省复建史馆", i, h, "文馆机构", "建南宋复置史馆节点。", field="职源与沿革", chain="none")
    south_end = tp(w, eid, "南宋绍兴十年二月二十九日", "罢史馆", i, h, "文馆机构", "建绍兴罢馆节点。", field="职源与沿革", chain="none")
    rebuild = tp(w, eid, "南宋嘉定六年六月十八日", "重建三馆中的史馆", i, h, "文馆机构", "建嘉定重建史馆节点。", field="职源与沿革", chain="none")
    chain(w, [
        north_qi, tang, song, find_t(w, eid, "宋前期"),
        find_t(w, eid, "北宋太平兴国三年二月一日"), find_t(w, eid, "北宋端拱元年五月"),
        find_t(w, eid, "北宋大中祥符八年"), reform, restore, south_end, rebuild
    ], "按北齐、唐、北宋三馆、元丰改制及南宋复罢重建重排史馆链。")
    cite(w, "Timepoints", song, i, duty, "补证北宋史馆修史、藏书与储才职能。", field="职能", note="职能")
    cite(w, "Timepoints", restore, i, duty, "补证南宋史馆修国史、实录职能。", field="职能", note="职能")
    cite(w, "Timepoints", song, i, order, "补证史馆在三馆中次于昭文馆、高于集贤院。", field="序位", note="序位")
    cite(w, "Timepoints", song, i, comp, "补证史馆官额与吏额。", field="编制", note="编制")

    secretary = find_e(w, "秘书省", "机构")
    secretary_1127 = tp(w, secretary, "南宋建炎元年五月", "于省内复建史馆", i, h, "中央文馆机构", "建秘书省南宋复史馆节点。", field="职源与沿革", chain="none")
    chain(w, [find_t(w, secretary, "北宋元丰五年"), secretary_1127], "连接秘书省元丰改置与建炎复史馆节点。")
    rel(w, secretary_1127, restore, "上下级机构", i, h, "南宋建炎元年于秘书省复建史馆。", field="职源与沿革")
    main = Q(i)
    parent = find_e(w, "崇文院", "机构")
    rel(w, find_t(w, parent, "北宋太平兴国三年二月一日"), find_t(w, eid, "北宋太平兴国三年二月一日"), "上下级机构", i, main, "北宋前期史馆隶崇文院。")
    rel(w, secretary_1127, restore, "上下级机构", i, main, "南宋史馆隶秘书省。")

    record = ent(w, "国史案", "机构", i, h, "原文明载元丰改制后史馆归入秘书省国史案。")
    record_start = tp(w, record, "北宋元丰五年", "承接史馆职事", i, h, "秘书省属案", "建国史案承接史馆节点。", field="职源与沿革", chain="none")
    rel(w, reform, record_start, "前后演变", i, h, "本条另记史馆于元丰改制后归入国史案。", field="职源与沿革", citation_kw={"conflict_flag": 1, "note": "第573条记并入秘书省著作局。"})
    old_rel = w.conn.execute(
        "select r.id from Relationships r join Timepoints o on o.id=r.object_id "
        "join Entities e on e.id=o.entity_id where r.subject_id=? and r.relation_type='前后演变' and e.title='著作局'",
        (reform,),
    ).fetchone()
    assert old_rel
    cite(w, "Relationships", old_rel[0], i, h, "补录本条国史案异说。", field="职源与沿革", conflict_flag=1, note="本条记入国史案，与第573条著作局说并存。")

    history_office = ent(w, "国史院", "机构", i, h, "原文明载元丰改制后或置国史院。")
    history_office_start = tp(w, history_office, "北宋元丰五年以后", "或置国史院", i, h, "修史机构", "建国史院改制后设置节点。", field="职源与沿革", chain="none")
    rel(w, reform, history_office_start, "前后演变", i, h, "史馆罢名后或置国史院。", field="职源与沿革")

    three = find_e(w, "三馆", "机构")
    three_rebuild = tp(w, three, "南宋嘉定六年六月十八日", "重建三馆", i, h, "文馆机构统称", "建嘉定重建三馆节点。", field="职源与沿革", chain="none")
    chain(w, [
        find_t(w, three, "宋前期"), find_t(w, three, "北宋天禧元年八月"),
        find_t(w, three, "北宋元丰五年"), find_t(w, three, "北宋元丰五年以后"), three_rebuild
    ], "在三馆沿革链补嘉定重建节点。")
    rel(w, three_rebuild, rebuild, "统称与实例", i, h, "嘉定六年重建三馆，史馆为其一。", field="职源与沿革")

    north_parent = song
    south_parent = restore
    official_specs = (
        ("监修国史", 1), ("史馆修撰", None), ("判史馆事", None),
        ("直史馆", None), ("史馆勘书", None), ("史馆编修", None),
        ("史馆校勘", None), ("史馆检讨", None), ("史馆祗候", None),
        ("史馆编校书籍", None),
    )
    for title, quota in official_specs:
        pe, pt = ensure_post(w, title, "北宋元丰改制前", i, comp, "馆职", f"据史馆编制建立{title}节点。", field="编制")
        rel(w, north_parent, pt, "编制隶属", i, comp, f"史馆馆职列{title}。", field="编制", staff_quota=quota, staff_type="官")

    clerk_specs = (
        ("孔目官", 1), ("四库书直官", 1), ("表奏官", 1), ("书库官", 4),
        ("守当官", 3), ("楷书", 13), ("写日历楷书", 3),
    )
    for title, quota in clerk_specs:
        ce = ent(w, title, "官职", i, comp, f"史馆吏额明列{title}。")
        ct = w.find_timepoint(ce, "宋前期") or tp(w, ce, "宋前期", "史馆吏额", i, comp, "吏职", f"建{title}史馆吏额节点。", field="编制", chain="none")
        rel(w, north_parent, ct, "编制隶属", i, comp, f"史馆吏额列{title}{quota}人。", field="编制", staff_quota=quota, staff_type="吏")
    w.commit()


def entry584():
    i = 584
    h = Q(i, "职源与沿革")
    duty = Q(i, "职能")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "监修国史", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    song = rewrite_tp(w, old, "北宋建隆元年二月", "置三相时次相兼修国史", i, duty, "馆职", "据专条细化宰相分领三馆的确切起点。", field="职能")
    tang = tp(w, eid, "唐贞观三年闰十二月", "始以宰相兼修国史", i, h, "馆职", "建唐代始置节点。", field="职源与沿革", chain="none")
    short = Q(i, "简称")
    qiande = tp(w, eid, "北宋乾德二年正月", "已见宰相监修国史", i, short, "馆职", "建乾德二年监修国史实见节点。", field="简称", chain="none")
    huangyou = find_t(w, eid, "北宋皇祐五年闰七月")
    end = tp(w, eid, "北宋元丰五年", "改制罢", i, h, "馆职", "建元丰罢置节点。", field="职源与沿革", chain="none")
    restore = tp(w, eid, "南宋绍兴三年六月二十七日", "置二相时次相（右相）监修国史", i, h, "馆职", "建南宋复置配置节点。", field="职源与沿革", chain="none")
    after = tp(w, eid, "南宋绍兴十年以后", "宰相兼监修国史改指领国史院", i, h, "馆职", "建史馆罢后职义变化节点。", field="职源与沿革", chain="none")
    later = tp(w, eid, "南宋绍兴二十六年五月以后", "置二相由首相兼监修；独相领史院，不入衔", i, h, "馆职", "建绍兴后期配置节点。", field="职源与沿革", chain="none")
    chain(w, [tang, song, qiande, huangyou, end, restore, after, later], "连接监修国史唐代始置、宋初三相、乾德皇祐实见、元丰罢置及南宋配置变化。")
    cite(w, "Timepoints", song, i, duty, "补证三相时次相、二相时首相兼修国史。", field="职能", note="职能")
    cite(w, "Timepoints", song, i, grade, "补证馆职序位。", field="品位", note="品位")
    cite(w, "Timepoints", song, i, comp, "补证一人。", field="编制", note="编制")
    cite(w, "Timepoints", qiande, i, short, "补证乾德二年宰相监修国史。", field="简称", note="简称段制度事实")
    history = find_e(w, "史馆", "机构")
    rel(w, find_t(w, history, "宋初"), song, "编制隶属", i, comp, "史馆置监修国史一人。", field="编制", staff_quota=1, staff_type="官")
    rel(w, find_t(w, history, "南宋建炎元年五月"), restore, "编制隶属", i, h, "南宋复史馆后置监修国史。", field="职源与沿革", staff_type="官")
    w.commit()


def entry585():
    i = 585
    h = Q(i, "职源与改革")
    duty = Q(i, "职能")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "史馆修撰", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    song = rewrite_tp(w, old, "宋初", "沿置史馆修撰", i, h, "馆职", "据专条细化宽泛馆职节点。", field="职源与改革")
    tang = tp(w, eid, "唐武德间", "创置修撰", i, h, "馆职", "建唐代职源节点。", field="职源与改革", chain="none")
    formal = tp(w, eid, "北宋至道中", "作为官称始见", i, h, "馆职", "建宋代正式官称节点。", field="职源与改革", chain="none")
    end = tp(w, eid, "北宋元丰五年", "改制罢", i, h, "馆职", "建元丰罢置节点。", field="职源与改革", chain="none")
    restore = tp(w, eid, "南宋绍兴三年八月二十三日", "复置史馆修撰", i, h, "馆职", "建南宋复置节点。", field="职源与改革", chain="none")
    first = tp(w, eid, "南宋绍兴四年二月", "复置后始除人", i, h, "馆职", "建南宋始除节点。", field="职源与改革", chain="none")
    south_end = tp(w, eid, "南宋绍兴二十九年八月二十四日", "罢置", i, h, "馆职", "建南宋罢置节点。", field="职源与改革", chain="none")
    chain(w, [tang, song, formal, end, restore, first, south_end], "连接史馆修撰唐代职源、宋代置罢及南宋复罢。")
    cite(w, "Timepoints", formal, i, duty, "补证北宋修日历及兼职形态。", field="职能", note="职能")
    cite(w, "Timepoints", first, i, duty, "补证南宋掌修日历、国史。", field="职能", note="职能")
    cite(w, "Timepoints", formal, i, grade, "补证馆职序位及任官资格。", field="品位", note="品位")
    cite(w, "Timepoints", song, i, comp, "补证初置四员、后无常员。", field="编制", note="编制")
    qualified = tp(w, eid, "北宋大中祥符九年八月", "须两省五品官以上方能为史馆修撰", i, grade, "馆职", "建大中祥符九年任官资格变化节点。", field="品位", attr_officer_type="两省五品官以上", chain="none")
    carried = tp(w, eid, "北宋熙宁六年八月", "始有带出者", i, duty, "馆职", "建熙宁六年带出变化节点。", field="职能", chain="none")
    chain(w, [tang, song, formal, qualified, carried, end, restore, first, south_end], "补入史馆修撰大中祥符资格变化与熙宁带出节点。")
    history = find_e(w, "史馆", "机构")
    rid = rel(w, find_t(w, history, "宋初"), song, "编制隶属", i, comp, "宋初史馆修撰初置四员，后无常员。", field="编制", staff_quota=4, staff_type="官")
    update_rel_attrs(w, rid, "史馆修撰专条明载初置四员。", quota=4, staff_type="官")
    rel(w, find_t(w, history, "南宋建炎元年五月"), restore, "编制隶属", i, h, "南宋史馆复置史馆修撰。", field="职源与改革", staff_type="官")
    w.commit()


def entry586_590():
    i = 586
    h = Q(i, "职源与沿革")
    duty = Q(i, "职能")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "判史馆事", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    song = rewrite_tp(w, old, "宋初", "沿置判史馆事", i, h, "馆职", "据专条细化史馆编制节点。", field="职源与沿革")
    tang = tp(w, eid, "唐元和六年", "始以史馆修撰中官高者一人判史馆事", i, h, "馆职", "建唐代始置节点。", field="职源与沿革", chain="none")
    end = tp(w, eid, "北宋元丰五年", "改制罢", i, h, "馆职", "建元丰罢置节点。", field="职源与沿革", chain="none")
    chain(w, [tang, song, end], "连接判史馆事唐代始置、宋沿置与元丰罢置。")
    cite(w, "Timepoints", song, i, duty, "补证与史馆修撰同撰日历。", field="职能", note="职能")
    cite(w, "Timepoints", song, i, grade, "补证任官资格与序位。", field="品位", note="品位")
    cite(w, "Timepoints", song, i, comp, "补证一员。", field="编制", note="编制")
    history = find_e(w, "史馆", "机构")
    rid = rel(w, find_t(w, history, "宋初"), song, "编制隶属", i, comp, "史馆置判史馆事一员。", field="编制", staff_quota=1, staff_type="官")
    update_rel_attrs(w, rid, "判史馆事专条明载一员。", quota=1, staff_type="官")
    w.commit()

    i = 587
    h = Q(i, "职源与沿革")
    duty = Q(i, "职能")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "直史馆", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    song = rewrite_tp(w, old, "宋初", "沿置直史馆", i, h, "馆职", "据专条细化史馆编制节点。", field="职源与沿革")
    qi = tp(w, eid, "北齐", "已有直史馆之名", i, h, "馆职", "建北齐职源节点。", field="职源与沿革", chain="none")
    before = tp(w, eid, "北宋太平兴国以前", "与史馆修撰、判史馆事分撰日历", i, duty, "馆职", "建太平兴国前职事节点。", field="职能", chain="none")
    after = tp(w, eid, "北宋太平兴国以后", "不预修纂，多为在京文臣兼职或带外贴职", i, duty, "馆职", "建太平兴国后职事变化节点。", field="职能", chain="none")
    end = tp(w, eid, "北宋元丰五年", "改制罢", i, h, "馆职", "建元丰罢置节点。", field="职源与沿革", chain="none")
    restore = tp(w, eid, "南宋绍兴三年八月二十三日", "复置，预修日历或国史", i, h, "馆职", "建南宋复置节点。", field="职源与沿革", chain="none")
    chain(w, [qi, song, before, after, end, restore], "连接直史馆北齐职源、宋代职事变化、元丰罢置及南宋复置。")
    cite(w, "Timepoints", after, i, grade, "补证次于修撰、高于编修检讨。", field="品位", note="品位")
    cite(w, "Timepoints", after, i, comp, "补证无常员。", field="编制", note="编制")
    history = find_e(w, "史馆", "机构")
    rel(w, find_t(w, history, "宋初"), song, "编制隶属", i, h, "宋沿置直史馆。", field="职源与沿革", staff_type="官")
    rel(w, find_t(w, history, "南宋建炎元年五月"), restore, "编制隶属", i, h, "南宋史馆复置直史馆。", field="职源与沿革", staff_type="官")
    w.commit()

    i = 588
    h = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "史馆编修", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    start = rewrite_tp(w, old, "北宋太平兴国八年", "始见置史馆编修", i, h, "馆职", "据专条细化宽泛馆职节点。", field="职源与沿革")
    short = Q(i, "简称")
    witness = tp(w, eid, "北宋乾兴元年十月", "已见以馆阁官充史馆编修", i, short, "馆职", "建乾兴元年史馆编修实见节点。", field="简称", chain="none")
    end = tp(w, eid, "北宋元丰五年", "改制罢", i, h, "馆职", "建元丰罢置节点。", field="职源与沿革", chain="none")
    chain(w, [start, witness, end], "连接史馆编修始置、乾兴实见与元丰罢置。")
    cite(w, "Timepoints", start, i, duty, "补证预修国史或日历。", field="职掌", note="职掌")
    cite(w, "Timepoints", start, i, grade, "补证任官资格与序位。", field="品位", note="品位")
    cite(w, "Timepoints", start, i, comp, "补证初置一员、后无定员。", field="编制", note="编制")
    history = find_e(w, "史馆", "机构")
    rid = rel(w, find_t(w, history, "宋初"), start, "编制隶属", i, comp, "太平兴国八年初置史馆编修一员。", field="编制", staff_quota=1, staff_type="官")
    update_rel_attrs(w, rid, "史馆编修专条明载初置一员。", quota=1, staff_type="官")
    w.commit()

    i = 589
    h = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    eid = find_e(w, "史馆检讨", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    start = rewrite_tp(w, old, "北宋淳化二年十月二日", "始见置史馆检讨", i, h, "馆职", "据专条细化宽泛馆职节点。", field="职源与沿革")
    short = Q(i, "简称")
    witness = tp(w, eid, "北宋皇祐三年十月", "已见史馆检讨参与史事检核", i, short, "馆职", "建皇祐三年史馆检讨实见节点。", field="简称", chain="none")
    end = tp(w, eid, "北宋元丰五年", "随史馆罢置", i, h, "馆职", "建元丰罢置节点。", field="职源与沿革", chain="none")
    restore = tp(w, eid, "南宋绍兴初", "史馆复置，史馆检讨备置", i, h, "馆职", "建南宋复置节点。", field="职源与沿革", chain="none")
    end2 = tp(w, eid, "南宋绍兴十年", "随史馆罢置", i, h, "馆职", "建绍兴十年罢置节点。", field="职源与沿革", chain="none")
    again = tp(w, eid, "南宋绍兴十年以后", "又置史馆检讨官", i, h, "馆职", "建绍兴十年后复见节点。", field="职源与沿革", chain="none")
    end3 = tp(w, eid, "南宋绍兴二十九年八月二十四日", "罢置", i, h, "馆职", "建绍兴二十九年罢置节点。", field="职源与沿革", chain="none")
    chain(w, [start, witness, end, restore, end2, again, end3], "连接史馆检讨北宋始置、皇祐实见、元丰罢置及南宋复罢。")
    cite(w, "Timepoints", start, i, duty, "补证搜集检阅史料与校字职掌。", field="职掌", note="职掌")
    cite(w, "Timepoints", start, i, grade, "补证任官资格与序位。", field="品位", note="品位")
    cite(w, "Timepoints", start, i, comp, "补证无常员。", field="编制", note="编制")
    history = find_e(w, "史馆", "机构")
    rel(w, find_t(w, history, "宋初"), start, "编制隶属", i, h, "史馆置史馆检讨。", field="职源与沿革", staff_type="官")
    rel(w, find_t(w, history, "南宋建炎元年五月"), restore, "编制隶属", i, h, "南宋复史馆时备置史馆检讨。", field="职源与沿革", staff_type="官")
    w.commit()

    i = 590
    h = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    w = W(i)
    tang_e = ent(w, "集贤院校勘", "官职", i, h, "原文明载唐有集贤院校勘。")
    tp(w, tang_e, "唐朝", "已有集贤院校勘", i, h, "馆职", "建唐代集贤院校勘职源节点。", field="职源与沿革")
    eid = find_e(w, "史馆校勘", "官职")
    old = find_t(w, eid, "北宋元丰改制前")
    start = rewrite_tp(w, old, "北宋雍熙四年", "始置史馆校勘", i, h, "馆职", "据专条细化史馆编制节点。", field="职源与沿革")
    end = tp(w, eid, "北宋元丰五年", "改制罢", i, h, "馆职", "建元丰罢置节点。", field="职源与沿革", chain="none")
    restore = tp(w, eid, "南宋绍兴初", "史馆复置时复置史馆校勘", i, h, "馆职", "建南宋复置节点。", field="职源与沿革", chain="none")
    chain(w, [start, end, restore], "连接史馆校勘北宋始置、元丰罢置与南宋复置。")
    cite(w, "Timepoints", start, i, duty, "补证掌本馆图籍及不带外。", field="职掌", note="职掌")
    cite(w, "Timepoints", start, i, grade, "补证任官资格与序位。", field="品位", note="品位")
    cite(w, "Timepoints", start, i, comp, "补证无定员。", field="编制", note="编制")
    history = find_e(w, "史馆", "机构")
    rel(w, find_t(w, history, "宋初"), start, "编制隶属", i, h, "北宋史馆置史馆校勘。", field="职源与沿革", staff_type="官")
    rel(w, find_t(w, history, "南宋建炎元年五月"), restore, "编制隶属", i, h, "南宋史馆复置史馆校勘。", field="职源与沿革", staff_type="官")
    w.commit()


def main():
    entry571_572()
    entry573()
    entry574_575()
    entry576_577()
    entry578()
    entry579_582()
    entry583()
    entry584()
    entry585()
    entry586_590()


if __name__ == "__main__":
    main()
