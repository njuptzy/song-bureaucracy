#!/usr/bin/env python3
"""提取 chapter2t4 第691–710条：门下后省、给事中、起居郎、左省谏官及省吏。

第701–704条明确参见右补阙、右司谏、右拾遗、右正言，故按现行 Prompt 同步加载并
处理第801–804条；各自写入时仍使用实际出处词条的 source_entry/page。

原目录 p176 曾把给事中“简称与别名”第⑫项“大两省”误作独立主条目；
切分修复后该空占位已删除，因此其后条目编号较旧结果前移一位。
"""
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
    assert r, i
    return {
        "title": r[0],
        "page": r[1],
        "text": r[2] or "",
        "fields": json.loads(r[3] or "{}"),
    }


IDS = list(range(691, 711)) + list(range(798, 805))
F = {i: load(i) for i in IDS}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, k=None):
    return F[i]["fields"][k] if k else F[i]["text"]


def C(i, k=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{k}字段）" if k else "")


def en(w, title, typ, i, q, d):
    return w.entity(title, typ, d, quotation=q)


def ac(w, table, rid, i, q, d, k=None, **kw):
    return w.citation(table, rid, C(i, k), q, d, **kw)


def tp(w, e, time, event, i, q, cat, d, k=None, **kw):
    t = w.timepoint(e, time, event, d, q, attr_category=cat, **kw)
    ac(w, "Timepoints", t, i, q, d, k)
    return t


def rel(w, a, b, kind, i, q, d, k=None, **kw):
    r = w.relationship(a, b, kind, d, q, **kw)
    ac(w, "Relationships", r, i, q, d, k)
    return r


def fe(w, title, typ=None):
    e = w.find_entity(title, typ)
    assert e, (title, typ)
    return e


def ft(w, e, time):
    t = w.find_timepoint(e, time)
    assert t, (e, time)
    return t


def chain(w, ts, d):
    assert ts and len(ts) == len(set(ts)), ts
    for n, t in enumerate(ts):
        w.relink(
            t,
            d,
            prev_id=ts[n - 1] if n else None,
            succ_id=ts[n + 1] if n + 1 < len(ts) else None,
        )


def refine(
    w,
    t,
    i,
    q,
    d,
    k=None,
    *,
    event=None,
    category=None,
    officer=None,
    grade=None,
    replace_quotation=False,
):
    row = w.conn.execute(
        "select event,attr_category,attr_officer_type,attr_grade,quotation "
        "from Timepoints where id=?",
        (t,),
    ).fetchone()
    assert row, t
    new = [
        event if event is not None else row[0],
        category if category is not None else row[1],
        officer if officer is not None else row[2],
        grade if grade is not None else row[3],
        q if replace_quotation else row[4],
    ]
    if tuple(new) != tuple(row):
        w.conn.execute(
            "update Timepoints set event=?,attr_category=?,attr_officer_type=?,"
            "attr_grade=?,quotation=? where id=?",
            (*new, t),
        )
        w._br(
            "Timepoints",
            t,
            f"据专条细化时间点：event {row[0]}->{new[0]}；category {row[1]}->{new[1]}；"
            f"officer {row[2]}->{new[2]}；grade {row[3]}->{new[3]}。{d}",
        )
    ac(w, "Timepoints", t, i, q, d, k)
    return t


def retime(w, t, time, event, i, q, cat, d, k=None, *, grade=None):
    row = w.conn.execute(
        "select entity_id,time,event,attr_category,attr_grade from Timepoints where id=?",
        (t,),
    ).fetchone()
    assert row, t
    clash = w.conn.execute(
        "select id from Timepoints where entity_id=? and time=? and id<>?",
        (row[0], time, t),
    ).fetchone()
    assert not clash, (t, time, clash)
    new_grade = grade if grade is not None else row[4]
    w.conn.execute(
        "update Timepoints set time=?,event=?,attr_category=?,attr_grade=?,quotation=? "
        "where id=?",
        (time, event, cat or row[3], new_grade, q, t),
    )
    w._br(
        "Timepoints",
        t,
        f"据专条细化 time {row[1]}->{time}、event {row[2]}->{event}：{d}",
    )
    ac(w, "Timepoints", t, i, q, d, k)
    return t


def set_rel_attrs(w, rid, quota, staff_type, d):
    old = w.conn.execute(
        "select staff_quota,staff_type from Relationships where id=?", (rid,)
    ).fetchone()
    assert old, rid
    new = (
        quota if quota is not None else old[0],
        staff_type if staff_type is not None else old[1],
    )
    if tuple(old) != new:
        w.conn.execute(
            "update Relationships set staff_quota=?,staff_type=? where id=?",
            (*new, rid),
        )
        w._br(
            "Relationships",
            rid,
            f"补充编制属性 quota {old[0]}->{new[0]}、staff_type {old[1]}->{new[1]}：{d}",
        )


def relation_id(w, subject_title, object_title, kind, subject_time=None, object_time=None):
    sql = (
        "select r.id from Relationships r "
        "join Timepoints a on a.id=r.subject_id "
        "join Entities ea on ea.id=a.entity_id "
        "join Timepoints b on b.id=r.object_id "
        "join Entities eb on eb.id=b.entity_id "
        "where ea.title=? and eb.title=? and r.relation_type=?"
    )
    params = [subject_title, object_title, kind]
    if subject_time is not None:
        sql += " and a.time=?"
        params.append(subject_time)
    if object_time is not None:
        sql += " and b.time=?"
        params.append(object_time)
    row = w.conn.execute(sql + " order by r.id limit 1", params).fetchone()
    return row[0] if row else None


def entry691():
    i = 691
    main = Q(i)
    hist = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    comp = Q(i, "编制")
    aliases = Q(i, "简称与别名")
    w = W(i)

    e = fe(w, "门下后省", "机构")
    old = ft(w, e, "北宋元丰新官制")
    start = retime(
        w,
        old,
        "北宋元丰五年",
        "创建，专掌封驳、书读诏命",
        i,
        hist,
        "中央政务机构",
        "总条给出创建年月与职掌。",
        "职源与沿革",
    )
    ac(w, "Timepoints", start, i, duty, "补证门下后省专掌封驳、书读诏命。", "职掌")
    out = tp(
        w,
        e,
        "北宋元丰六年四月",
        "改名门下外省",
        i,
        aliases,
        "中央政务机构",
        "建门下后省改名节点。",
        "简称与别名",
        chain="none",
    )
    restored = tp(
        w,
        e,
        "北宋元丰八年",
        "由门下外省恢复门下后省旧名",
        i,
        aliases,
        "中央政务机构",
        "建门下后省复名节点。",
        "简称与别名",
        chain="none",
    )
    south = tp(
        w,
        e,
        "南宋建炎三年七月",
        "沿置，以给事中为长官，罢符宝郎",
        i,
        hist,
        "中央政务机构",
        "建南宋沿置节点。",
        "职源与沿革",
        chain="none",
    )
    ac(w, "Timepoints", south, i, comp, "补证南宋门下后省官额与五案编制。", "编制")
    chain(w, [start, out, restored, south], "连接门下后省创建、改名、复名与南宋沿置。")

    outer = en(w, "门下外省", "机构", i, aliases, "原文明载门下后省一度改名门下外省。")
    outer_start = tp(
        w,
        outer,
        "北宋元丰六年四月",
        "由门下后省改名",
        i,
        aliases,
        "中央政务机构",
        "建门下外省始置节点。",
        "简称与别名",
        chain="none",
    )
    outer_end = tp(
        w,
        outer,
        "北宋元丰八年",
        "恢复门下后省旧名",
        i,
        aliases,
        "中央政务机构",
        "建门下外省复旧节点。",
        "简称与别名",
        chain="none",
    )
    chain(w, [outer_start, outer_end], "连接门下外省始置与复旧节点。")
    rel(w, out, outer_start, "前后演变", i, aliases, "门下后省改为门下外省。", "简称与别名")
    rel(w, outer_end, restored, "前后演变", i, aliases, "门下外省恢复门下后省旧名。", "简称与别名")

    parent = fe(w, "门下省", "机构")
    rel(
        w,
        ft(w, parent, "北宋元丰新制"),
        start,
        "上下级机构",
        i,
        comp,
        "元丰新制门下后省为门下省后省机构。",
        "编制",
    )

    case_titles = [
        "门下后省上案",
        "门下后省下案",
        "门下后省封驳案",
        "门下后省谏官案",
        "门下后省记注案",
        "门下后省符宝郎案",
    ]
    for title in case_titles:
        ce = en(w, title, "机构", i, comp, f"门下后省编制明列{title.removeprefix('门下后省')}。")
        ct = tp(
            w,
            ce,
            "北宋元丰五年",
            "门下后省办事部门",
            i,
            comp,
            "后省办事机构",
            f"建{title}元丰节点。",
            "编制",
            chain="none",
        )
        rel(w, start, ct, "上下级机构", i, comp, f"{title}隶属门下后省。", "编制")
        if title != "门下后省符宝郎案":
            st = tp(
                w,
                ce,
                "南宋建炎三年七月",
                "门下后省办事部门",
                i,
                comp,
                "后省办事机构",
                f"建{title}南宋沿置节点。",
                "编制",
                chain="none",
            )
            chain(w, [ct, st], f"连接{title}北宋、南宋节点。")
            rel(w, south, st, "上下级机构", i, comp, f"南宋门下后省沿置{title}。", "编制")

    post_nodes = {
        "左散骑常侍": ft(w, fe(w, "左散骑常侍", "官职"), "北宋元丰新制"),
        "左谏议大夫": ft(w, fe(w, "左谏议大夫", "官职"), "北宋元丰改制后"),
        "左司谏": ft(w, fe(w, "左司谏", "官职"), "北宋元丰新制"),
        "左正言": ft(w, fe(w, "左正言", "官职"), "北宋元丰新制"),
        "给事中": ft(w, fe(w, "给事中", "官职"), "北宋元丰新制"),
        "起居郎": ft(w, fe(w, "起居郎", "官职"), "北宋元丰五年五月"),
    }
    quotas = {
        "左散骑常侍": 1,
        "左谏议大夫": 1,
        "左司谏": 1,
        "左正言": 1,
        "给事中": 4,
        "起居郎": 1,
    }
    for title, pt_id in post_nodes.items():
        ac(w, "Timepoints", pt_id, i, comp, f"总条补证{title}列门下后省官额。", "编制", note="编制")
        rid = rel(
            w,
            start,
            pt_id,
            "编制隶属",
            i,
            comp,
            f"门下后省置{title}{quotas[title]}员。",
            "编制",
            staff_quota=quotas[title],
            staff_type="官",
        )
        set_rel_attrs(w, rid, quotas[title], "官", "门下后省总条明载官额。")

    seal = en(w, "符宝郎", "官职", i, comp, "门下后省编制明列符宝郎二员。")
    seal_t = tp(
        w,
        seal,
        "北宋元丰新制",
        "门下后省官，二员",
        i,
        comp,
        "职事官",
        "建符宝郎元丰编制节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        start,
        seal_t,
        "编制隶属",
        i,
        comp,
        "门下后省置符宝郎二员。",
        "编制",
        staff_quota=2,
        staff_type="官",
    )
    w.commit()


def entries692_696():
    details = {
        692: ("门下后省上案", "掌大朝会所用各种文书"),
        693: ("门下后省下案", "掌收发门下后省五案文书"),
        694: ("门下后省封驳案", "掌抄录封驳文书及门下省人吏考试、迁补"),
        695: ("门下后省谏官案", "掌收受朝廷诸司上报门下后省文书"),
        696: ("门下后省记注案", "掌抄录起居郎所书朝廷议论的起居注"),
    }
    for i, (title, event) in details.items():
        z = Q(i)
        w = W(i)
        e = fe(w, title, "机构")
        t = ft(w, e, "北宋元丰五年")
        refine(
            w,
            t,
            i,
            z,
            "专条补足本案职掌。",
            event=event,
            category="后省办事机构",
            replace_quotation=True,
        )
        rid = relation_id(
            w, "门下后省", title, "上下级机构", "北宋元丰五年", "北宋元丰五年"
        )
        assert rid, title
        ac(w, "Relationships", rid, i, z, f"专条补证{title}隶属门下后省。")
        w.commit()


def entry697():
    i = 697
    main = Q(i)
    hist = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    grade = Q(i, "官品")
    comp = Q(i, "编制")
    aliases = Q(i, "简称与别名")
    w = W(i)
    e = fe(w, "给事中", "官职")
    qin = tp(w, e, "秦汉", "为加官", i, hist, "官职", "建给事中秦汉职源节点。", "职源与沿革", chain="none")
    jin = tp(w, e, "晋朝", "隶门下省", i, hist, "官职", "建给事中晋代节点。", "职源与沿革", chain="none")
    tang = tp(
        w,
        e,
        "隋炀帝至唐武德三年",
        "由门下省给事郎改为给事中，省读奏案、驳正违失",
        i,
        hist,
        "官职",
        "建给事中隋唐职源节点。",
        "职源与沿革",
        chain="none",
    )
    song = tp(
        w,
        e,
        "宋前期",
        "文臣迁转寄禄官阶，不掌封驳",
        i,
        duty,
        "阶官",
        "建给事中宋前期寄禄节点。",
        "职掌",
        attr_grade="正五品上",
        chain="none",
    )
    ac(w, "Timepoints", song, i, main, "补证宋前期为阶官。")
    ac(w, "Timepoints", song, i, grade, "补证宋前期官品。", "官品", note="官品")
    yf = ft(w, e, "北宋元丰新制")
    refine(
        w,
        yf,
        i,
        duty,
        "据给事中专条细化元丰职掌。",
        "职掌",
        event="门下后省长官，审读、封驳中央与地方重要文书",
        category="职事官",
        grade="正四品",
        replace_quotation=True,
    )
    ac(w, "Timepoints", yf, i, main, "补证元丰新制为职事官。")
    ac(w, "Timepoints", yf, i, grade, "补证元丰新制正四品。", "官品", note="官品")
    ac(w, "Timepoints", yf, i, comp, "补证元丰新制四人为额。", "编制", note="编制")
    chain(
        w,
        [
            qin,
            jin,
            tang,
            song,
            ft(w, e, "北宋天禧元年八月"),
            yf,
            ft(w, e, "北宋元丰五年六月二十五日"),
            ft(w, e, "南宋（未载具体年月）"),
        ],
        "重排给事中秦汉至南宋沿革链。",
    )
    rid = relation_id(w, "门下后省", "给事中", "编制隶属", "北宋元丰五年")
    assert rid
    set_rel_attrs(w, rid, 4, "官", "给事中专条明载四人为额。")
    ac(w, "Relationships", rid, i, duty, "补证给事中为门下后省长官。", "职掌")
    ac(w, "Relationships", rid, i, comp, "补证给事中四人为额。", "编制", note="编制")
    ac(w, "Timepoints", yf, i, aliases, "全文扫描简称别名字段；纯别称不另建实体。", "简称与别名", note="纯别称")
    w.commit()


def entry698():
    i = 698
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    comp = Q(i, "编制")
    grade = Q(i, "官品")
    aliases = Q(i, "简称与别名")
    w = W(i)
    e = fe(w, "起居郎", "官职")
    tang = tp(
        w,
        e,
        "唐贞观二年",
        "门下省始置起居郎",
        i,
        origin,
        "起居官",
        "建起居郎唐代职源节点。",
        "职源",
        chain="none",
    )
    song = ft(w, e, "宋初")
    refine(
        w,
        song,
        i,
        duty,
        "补证宋前期无职守、为迁转叙禄官阶。",
        "职掌",
        event="门下省起居郎名存而职事不举，为文臣迁转叙禄官阶",
        category="阶官",
        grade="从六品上",
        replace_quotation=True,
    )
    ac(w, "Timepoints", song, i, main, "补证宋前期为阶官。")
    ac(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品", note="官品")
    yf = ft(w, e, "北宋元丰五年五月")
    refine(
        w,
        yf,
        i,
        duty,
        "据专条细化元丰新制起居郎职掌。",
        "职掌",
        event="职事官，记皇帝言动并编年记载朝中大事",
        category="起居官",
        grade="从六品",
        replace_quotation=True,
    )
    ac(w, "Timepoints", yf, i, main, "补证元丰新制为职事官。")
    ac(w, "Timepoints", yf, i, comp, "补证元丰新制一人。", "编制", note="编制")
    ac(w, "Timepoints", yf, i, grade, "补证元丰新制从六品。", "官品", note="官品")
    ac(w, "Timepoints", yf, i, aliases, "全文扫描简称别名字段；纯别称不另建实体。", "简称与别名", note="纯别称")
    chain(w, [tang, song, yf], "连接起居郎唐代职源、宋初与元丰节点。")
    rid = relation_id(w, "门下后省", "起居郎", "编制隶属", "北宋元丰五年")
    assert rid
    set_rel_attrs(w, rid, 1, "官", "起居郎专条明载一人为额。")
    ac(w, "Relationships", rid, i, comp, "补证门下后省起居郎一人。", "编制")
    w.commit()


def entry699():
    i = 699
    main = Q(i)
    aliases = Q(i, "简称与别名")
    # 被对照的右散骑常侍条，提供“皆如”的具体职源、职掌和官品。
    ref = 798
    right_hist = Q(ref, "职源")
    right_duty = Q(ref, "职掌")
    right_grade = Q(ref, "官品")
    w = W(i)
    e = fe(w, "左散骑常侍", "官职")
    origin = tp(
        w,
        e,
        "曹魏黄初初年",
        "始置散骑常侍；唐显庆二年始分左右",
        i,
        main,
        "官职",
        "左散骑常侍专条明载职源皆如右散骑常侍。",
        chain="none",
    )
    pre = tp(
        w,
        e,
        "宋前期",
        "文臣迁转官阶，无实际职守",
        i,
        main,
        "阶官",
        "建左散骑常侍宋前期阶官节点。",
        attr_grade="正三品下",
        chain="none",
    )
    yf = ft(w, e, "北宋元丰新制")
    refine(
        w,
        yf,
        i,
        main,
        "据专条细化元丰新制虚官状态。",
        event="虚官，品位高而未曾除人",
        category="职事官",
        grade="正三品",
        replace_quotation=True,
    )
    chain(w, [origin, pre, yf, ft(w, e, "宋代（未载具体年月）")], "重排左散骑常侍职源与宋代节点。")
    ac(w, "Timepoints", pre, ref, right_duty, "右散骑常侍条提供左右相同的宋前期职掌。", "职掌")
    ac(w, "Timepoints", pre, ref, right_grade, "右散骑常侍条提供左右相同的宋前期官品。", "官品", note="官品")
    ac(w, "Timepoints", yf, ref, right_duty, "右散骑常侍条提供左右相同的元丰虚官状态。", "职掌")
    ac(w, "Timepoints", yf, ref, right_grade, "右散骑常侍条提供左右相同的元丰官品。", "官品", note="官品")
    ac(w, "Timepoints", origin, ref, right_hist, "右散骑常侍条提供散骑常侍职源。", "职源")
    ac(w, "Timepoints", yf, i, aliases, "全文扫描简称别名字段；纯别称不另建实体。", "简称与别名", note="纯别称")
    parent = fe(w, "门下省", "机构")
    rid = rel(
        w,
        ft(w, parent, "北宋元丰新制"),
        yf,
        "编制隶属",
        i,
        main,
        "左散骑常侍隶门下省。",
        staff_type="官",
    )
    set_rel_attrs(w, rid, 1, "官", "门下省总条明载一人为额。")
    w.commit()


def entry700():
    i = 700
    main = Q(i)
    aliases = Q(i, "简称与别名")
    ref = 799
    ref_origin = Q(ref, "职源")
    ref_duty = Q(ref, "职掌")
    ref_grade = Q(ref, "官品")
    w = W(i)
    e = fe(w, "左谏议大夫", "官职")
    origin = tp(
        w,
        e,
        "后汉",
        "始置谏议大夫；唐贞元四年分左右",
        i,
        main,
        "官职",
        "左谏议大夫专条明载职源与右谏议大夫同。",
        chain="none",
    )
    pre = ft(w, e, "北宋元丰改制前")
    refine(
        w,
        pre,
        i,
        main,
        "补证宋前期为官阶。",
        event="文臣迁转叙位禄阶官，不亲掌言事",
        category="寄禄官",
        grade="正四品下",
        replace_quotation=True,
    )
    post = ft(w, e, "北宋元丰改制后")
    refine(
        w,
        post,
        i,
        main,
        "补证元丰新制为职事谏官。",
        event="职事谏官，谏正朝政失误、任人不当及百司违失",
        category="谏官",
        grade="从四品",
        replace_quotation=True,
    )
    chain(
        w,
        [origin, pre, post, ft(w, e, "宋代（未载具体年月）"), ft(w, e, "南宋")],
        "重排左谏议大夫职源、元丰前后与南宋节点。",
    )
    ac(w, "Timepoints", origin, ref, ref_origin, "右谏议大夫条提供左右相同的职源。", "职源")
    ac(w, "Timepoints", pre, ref, ref_duty, "右谏议大夫条提供左右相同的宋前期职掌。", "职掌")
    ac(w, "Timepoints", pre, ref, ref_grade, "右谏议大夫条提供左右相同的宋前期官品。", "官品", note="官品")
    ac(w, "Timepoints", post, ref, ref_duty, "右谏议大夫条提供左右相同的元丰职掌。", "职掌")
    ac(w, "Timepoints", post, ref, ref_grade, "右谏议大夫条提供左右相同的元丰官品。", "官品", note="官品")
    ac(w, "Timepoints", post, i, aliases, "全文扫描简称别名字段；纯别称不另建实体。", "简称与别名", note="纯别称")
    rid = rel(
        w,
        ft(w, fe(w, "门下省", "机构"), "北宋元丰新制"),
        post,
        "编制隶属",
        i,
        main,
        "左谏议大夫隶门下省。",
        staff_type="官",
    )
    set_rel_attrs(w, rid, 1, "官", "门下省总条明载一人为额。")
    w.commit()


def referenced_right_801():
    i = 801
    main = Q(i)
    hist = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    grade = Q(i, "官品")
    aliases = Q(i, "简称")
    w = W(i)
    e = fe(w, "右补阙", "官职")
    tang = tp(w, e, "唐垂拱元年", "始置补阙", i, hist, "谏官", "建右补阙唐代职源节点。", "职源与沿革", chain="none")
    early = tp(
        w,
        e,
        "北宋初",
        "无职守，为文臣迁转官阶",
        i,
        duty,
        "阶官",
        "建右补阙宋初节点。",
        "职掌",
        attr_grade="从七品上",
        chain="none",
    )
    ac(w, "Timepoints", early, i, main, "补证宋初为阶官。")
    ac(w, "Timepoints", early, i, grade, "补证宋初从七品上。", "官品", note="官品")
    end = retime(
        w,
        ft(w, e, "宋代（《长编》卷29乙未）"),
        "北宋端拱元年二月八日",
        "改为右司谏",
        i,
        hist,
        "谏官",
        "据专条确定改名年月。",
        "职源与沿革",
    )
    restore = tp(
        w,
        e,
        "南宋淳熙十五年",
        "复置为专职谏官，不兼纠弹",
        i,
        hist,
        "谏官",
        "建右补阙南宋复置节点。",
        "职源与沿革",
        attr_grade="正七品",
        chain="none",
    )
    ac(w, "Timepoints", restore, i, duty, "补证复置后职掌。", "职掌")
    ac(w, "Timepoints", restore, i, grade, "补证南宋正七品。", "官品", note="官品")
    end2 = tp(
        w,
        e,
        "南宋绍熙二年",
        "又改为右司谏",
        i,
        hist,
        "谏官",
        "建右补阙绍熙改名节点。",
        "职源与沿革",
        chain="none",
    )
    chain(w, [tang, early, end, restore, end2], "连接右补阙唐代、宋初及南宋沿革。")
    ac(w, "Timepoints", early, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    w.commit()


def entry701():
    referenced_right_801()
    i = 701
    main = Q(i)
    aliases = Q(i, "简称")
    w = W(i)
    e = fe(w, "左补阙", "官职")
    tang = tp(w, e, "唐垂拱元年", "始置补阙", i, main, "谏官", "据参见条建左补阙唐代职源节点。", chain="none")
    early = tp(
        w,
        e,
        "北宋初",
        "无职守，为文臣迁转官阶",
        i,
        main,
        "阶官",
        "建左补阙宋初节点。",
        attr_grade="从七品上",
        chain="none",
    )
    end = retime(
        w,
        ft(w, e, "宋代（《长编》卷29乙未）"),
        "北宋端拱元年二月八日",
        "改为左司谏",
        i,
        main,
        "谏官",
        "据参见右补阙条确定改名年月。",
    )
    restore = tp(
        w,
        e,
        "南宋淳熙十五年",
        "复置为专职谏官，不兼纠弹",
        i,
        main,
        "谏官",
        "据参见条建左补阙南宋复置节点。",
        attr_grade="正七品",
        chain="none",
    )
    end2 = tp(
        w,
        e,
        "南宋绍熙二年",
        "又改为左司谏",
        i,
        main,
        "谏官",
        "据参见条建左补阙绍熙改名节点。",
        chain="none",
    )
    chain(w, [tang, early, end, restore, end2], "连接左补阙唐代、宋初及南宋沿革。")
    ac(w, "Timepoints", early, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    w.commit()


def referenced_right_802():
    i = 802
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    grade = Q(i, "官品")
    aliases = Q(i, "简称与别名")
    w = W(i)
    e = fe(w, "右司谏", "官职")
    start = retime(
        w,
        ft(w, e, "宋代（《长编》卷29乙未）"),
        "北宋端拱元年二月八日",
        "由右补阙改置，初为职事官",
        i,
        origin,
        "谏官",
        "专条补证右司谏始置。",
        "职源",
        grade="七品",
    )
    later = retime(
        w,
        ft(w, e, "宋代（未载具体年月）"),
        "北宋端拱以后（未载具体年月）",
        "转为差遣兼官，起本官阶叙位禄",
        i,
        duty,
        "阶官",
        "据专条细化端拱以后状态。",
        "职掌",
        grade="七品",
    )
    yf = tp(
        w,
        e,
        "北宋元丰新制",
        "职事官，掌规谏朝政阙失、用人不当并兼弹纠",
        i,
        duty,
        "谏官",
        "建右司谏元丰节点。",
        "职掌",
        attr_grade="正七品",
        chain="none",
    )
    ac(w, "Timepoints", yf, i, main, "补证元丰新制为职事官。")
    ac(w, "Timepoints", yf, i, grade, "补证元丰新制正七品。", "官品", note="官品")
    chain(w, [start, later, yf, ft(w, e, "南宋")], "连接右司谏端拱、元丰与南宋节点。")
    ac(w, "Timepoints", later, i, aliases, "全文扫描简称别名字段；纯别称不另建实体。", "简称与别名", note="纯别称")
    w.commit()


def entry702():
    referenced_right_802()
    i = 702
    main = Q(i)
    w = W(i)
    e = fe(w, "左司谏", "官职")
    start = retime(
        w,
        ft(w, e, "宋代（《长编》卷29乙未）"),
        "北宋端拱元年二月八日",
        "由左补阙改置，初为职事官",
        i,
        main,
        "谏官",
        "补证左司谏端拱初为职事官。",
        grade="七品",
    )
    old_generic = w.find_timepoint(e, "宋代（未载具体年月）")
    assert old_generic
    later = retime(
        w,
        old_generic,
        "北宋端拱以后（未载具体年月）",
        "转为阶官",
        i,
        main,
        "阶官",
        "据专条细化初置后转阶官。",
        grade="七品",
    )
    yf = ft(w, e, "北宋元丰新制")
    refine(
        w,
        yf,
        i,
        main,
        "补证元丰新制复为职事官且一人为额。",
        event="复为职事谏官，一人为额",
        category="谏官",
        grade="正七品",
        replace_quotation=True,
    )
    chain(w, [start, later, yf, ft(w, e, "南宋")], "连接左司谏端拱、元丰与南宋节点。")
    source_end = ft(w, fe(w, "左补阙", "官职"), "北宋端拱元年二月八日")
    rel(w, source_end, start, "前后演变", i, main, "端拱元年左补阙改为左司谏。")
    rid = rel(
        w,
        ft(w, fe(w, "门下省", "机构"), "北宋元丰新制"),
        yf,
        "编制隶属",
        i,
        main,
        "左司谏隶门下省，元丰新制一人。",
        staff_quota=1,
        staff_type="官",
    )
    set_rel_attrs(w, rid, 1, "官", "左司谏专条明载元丰一人。")
    w.commit()


def referenced_right_803():
    i = 803
    main = Q(i)
    hist = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    grade = Q(i, "官品")
    aliases = Q(i, "简称")
    w = W(i)
    e = fe(w, "右拾遗", "官职")
    tang = tp(w, e, "唐垂拱元年", "始置拾遗", i, hist, "谏官", "建右拾遗唐代职源节点。", "职源与沿革", chain="none")
    early = tp(
        w,
        e,
        "北宋初",
        "无职守，为文臣差遣所带阶官",
        i,
        duty,
        "阶官",
        "建右拾遗宋初节点。",
        "职掌",
        attr_grade="从八品上",
        chain="none",
    )
    ac(w, "Timepoints", early, i, main, "补证宋初为阶官。")
    ac(w, "Timepoints", early, i, grade, "补证宋初从八品上。", "官品", note="官品")
    end = retime(
        w,
        ft(w, e, "宋代（《长编》卷29乙未）"),
        "北宋端拱元年二月八日",
        "改为右正言",
        i,
        hist,
        "谏官",
        "据专条确定改名年月。",
        "职源与沿革",
    )
    restore = tp(
        w,
        e,
        "南宋淳熙十五年正月八日",
        "复置为职事谏官，不兼弹劾",
        i,
        hist,
        "谏官",
        "建右拾遗南宋复置节点。",
        "职源与沿革",
        attr_grade="从七品",
        chain="none",
    )
    ac(w, "Timepoints", restore, i, duty, "补证复置后职掌。", "职掌")
    ac(w, "Timepoints", restore, i, grade, "补证南宋从七品。", "官品", note="官品")
    end2 = tp(
        w,
        e,
        "南宋绍熙二年",
        "又改为右正言",
        i,
        hist,
        "谏官",
        "建右拾遗绍熙改名节点。",
        "职源与沿革",
        chain="none",
    )
    chain(w, [tang, early, end, restore, end2], "连接右拾遗唐代、宋初及南宋沿革。")
    ac(w, "Timepoints", early, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    w.commit()


def entry703():
    referenced_right_803()
    i = 703
    main = Q(i)
    w = W(i)
    e = fe(w, "左拾遗", "官职")
    tang = tp(w, e, "唐垂拱元年", "始置拾遗", i, main, "谏官", "据参见条建左拾遗唐代职源节点。", chain="none")
    early = tp(
        w,
        e,
        "北宋初",
        "无职守，为文臣差遣所带阶官",
        i,
        main,
        "阶官",
        "建左拾遗宋初节点。",
        attr_grade="从八品上",
        chain="none",
    )
    end = retime(
        w,
        ft(w, e, "宋代（《长编》卷29乙未）"),
        "北宋端拱元年二月八日",
        "改为左正言",
        i,
        main,
        "谏官",
        "据参见右拾遗条确定改名年月。",
    )
    restore = tp(
        w,
        e,
        "南宋淳熙十五年正月八日",
        "复置为职事谏官，不兼弹劾",
        i,
        main,
        "谏官",
        "据参见条建左拾遗南宋复置节点。",
        attr_grade="从七品",
        chain="none",
    )
    end2 = tp(
        w,
        e,
        "南宋绍熙二年",
        "又改为左正言",
        i,
        main,
        "谏官",
        "据参见条建左拾遗绍熙改名节点。",
        chain="none",
    )
    chain(w, [tang, early, end, restore, end2], "连接左拾遗唐代、宋初及南宋沿革。")
    w.commit()


def referenced_right_804():
    i = 804
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    grade = Q(i, "官品")
    aliases = Q(i, "简称与别名")
    w = W(i)
    e = fe(w, "右正言", "官职")
    start = retime(
        w,
        ft(w, e, "宋代（《长编》卷29乙未）"),
        "北宋端拱元年二月八日",
        "由右拾遗改置",
        i,
        origin,
        "谏官",
        "专条补证端拱始置。",
        "职源",
    )
    early = retime(
        w,
        ft(w, e, "宋代（未载具体年月）"),
        "宋前期（未载具体年月）",
        "无言事职守，为文臣迁转官阶",
        i,
        duty,
        "阶官",
        "据专条细化宋前期状态。",
        "职掌",
        grade="八品",
    )
    tx = tp(
        w,
        e,
        "北宋天禧元年",
        "置为职事谏官",
        i,
        duty,
        "谏官",
        "建右正言天禧职事节点。",
        "职掌",
        chain="none",
    )
    yf = tp(
        w,
        e,
        "北宋元丰新制",
        "职事谏官，任谏职并兼弹纠",
        i,
        duty,
        "谏官",
        "建右正言元丰节点。",
        "职掌",
        attr_grade="从七品",
        chain="none",
    )
    ac(w, "Timepoints", yf, i, main, "补证元丰新制为职事官。")
    ac(w, "Timepoints", early, i, grade, "补证宋前期八品。", "官品", note="官品")
    ac(w, "Timepoints", yf, i, grade, "补证元丰新制从七品。", "官品", note="官品")
    chain(w, [start, early, tx, yf, ft(w, e, "南宋")], "连接右正言端拱、天禧、元丰与南宋节点。")
    ac(w, "Timepoints", early, i, aliases, "全文扫描简称别名字段；纯别称不另建实体。", "简称与别名", note="纯别称")
    w.commit()


def entry704():
    referenced_right_804()
    i = 704
    main = Q(i)
    w = W(i)
    e = fe(w, "左正言", "官职")
    start = retime(
        w,
        ft(w, e, "宋代（《长编》卷29乙未）"),
        "北宋端拱元年二月八日",
        "由左拾遗改置，初为职事官",
        i,
        main,
        "谏官",
        "补证左正言端拱初置时为职事官。",
    )
    generic = w.find_timepoint(e, "宋代（未载具体年月）")
    assert generic
    early = retime(
        w,
        generic,
        "北宋端拱以后（未载具体年月）",
        "后仍为阶官",
        i,
        main,
        "阶官",
        "据专条细化端拱以后状态。",
    )
    yf = ft(w, e, "北宋元丰新制")
    refine(
        w,
        yf,
        i,
        main,
        "补证元丰新制为职事谏官且一人为额。",
        event="职事谏官，任言责，一人为额",
        category="谏官",
        grade="从七品",
        replace_quotation=True,
    )
    chain(w, [start, early, yf, ft(w, e, "南宋")], "连接左正言端拱、元丰与南宋节点。")
    source_end = ft(w, fe(w, "左拾遗", "官职"), "北宋端拱元年二月八日")
    rel(w, source_end, start, "前后演变", i, main, "端拱元年左拾遗改为左正言。")
    rid = rel(
        w,
        ft(w, fe(w, "门下省", "机构"), "北宋元丰新制"),
        yf,
        "编制隶属",
        i,
        main,
        "左正言隶门下省，元丰新制一人。",
        staff_quota=1,
        staff_type="官",
    )
    set_rel_attrs(w, rid, 1, "官", "左正言专条明载元丰一人。")
    w.commit()


def entry705_706():
    i = 705
    main = Q(i)
    hist = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    grade = Q(i, "官品")
    comp = Q(i, "编制")
    aliases = Q(i, "简称")
    w = W(i)
    generic = fe(w, "符宝郎", "官职")
    generic_start = ft(w, generic, "北宋元丰新制")
    refine(
        w,
        generic_start,
        i,
        comp,
        "补证元丰新制二员而实未除人。",
        "编制",
        event="门下后省官，二员，实未除人",
        grade="从七品",
        replace_quotation=True,
    )
    ac(w, "Timepoints", generic_start, i, hist, "补证符宝郎秦汉至唐沿革。", "职源与沿革")
    ac(w, "Timepoints", generic_start, i, duty, "补证掌珍藏国宝、捧宝。", "职掌")
    ac(w, "Timepoints", generic_start, i, grade, "补证从七品。", "官品", note="官品")
    split = tp(
        w,
        generic,
        "北宋大观二年",
        "分置内、外符宝郎各二人",
        i,
        comp,
        "职事官",
        "建符宝郎分置内外节点。",
        "编制",
        attr_grade="从七品",
        chain="none",
    )
    chain(w, [generic_start, split], "连接符宝郎元丰与大观分置节点。")

    outer = en(w, "外符宝郎", "官职", i, main, "原文明载外符宝郎官名。")
    outer_t = tp(
        w,
        outer,
        "北宋大观二年",
        "置二人，掌从禁中内符宝郎接宝并进呈御座",
        i,
        comp,
        "职事官",
        "建外符宝郎大观节点。",
        "编制",
        attr_grade="从七品",
        chain="none",
    )
    ac(w, "Timepoints", outer_t, i, duty, "补证外符宝郎捧宝进呈职掌。", "职掌")
    ac(w, "Timepoints", outer_t, i, grade, "补证从七品。", "官品", note="官品")
    stop = tp(
        w,
        outer,
        "北宋靖康元年二月",
        "罢置",
        i,
        comp,
        "职事官",
        "建外符宝郎靖康罢置节点。",
        "编制",
        chain="none",
    )
    restore = tp(
        w,
        outer,
        "南宋乾道后",
        "复置",
        i,
        comp,
        "职事官",
        "建外符宝郎南宋复置节点。",
        "编制",
        chain="none",
    )
    chain(w, [outer_t, stop, restore], "连接外符宝郎大观、靖康与南宋节点。")

    inner = en(w, "内符宝郎", "官职", i, comp, "大观二年明载内、外符宝郎各二人。")
    inner_t = tp(
        w,
        inner,
        "北宋大观二年",
        "置二人，由内侍充，掌禁中符宝",
        i,
        comp,
        "职事官",
        "建内符宝郎大观节点。",
        "编制",
        attr_grade="从七品",
        chain="none",
    )
    ac(w, "Timepoints", inner_t, i, duty, "补证内符宝郎从禁中捧宝交外符宝郎。", "职掌")
    rel(w, split, outer_t, "前后演变", i, comp, "大观二年符宝郎分置外符宝郎。", "编制")
    rel(w, split, inner_t, "前后演变", i, comp, "大观二年符宝郎分置内符宝郎。", "编制")
    parent = fe(w, "门下后省", "机构")
    rel(
        w,
        ft(w, parent, "北宋元丰八年"),
        outer_t,
        "编制隶属",
        i,
        comp,
        "外符宝郎隶门下后省。",
        "编制",
        staff_quota=2,
        staff_type="官",
    )
    ac(w, "Timepoints", outer_t, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    w.commit()

    i = 706
    main = Q(i)
    grade = Q(i, "官品")
    aliases = Q(i, "简称")
    w = W(i)
    e = fe(w, "内符宝郎", "官职")
    t = ft(w, e, "北宋大观二年")
    refine(
        w,
        t,
        i,
        main,
        "专条补证内符宝郎由内侍充及内外分工。",
        event="设于禁中，由内侍充，掌珍藏符宝；行用时交外符宝郎",
        grade="从七品",
        replace_quotation=True,
    )
    ac(w, "Timepoints", t, i, grade, "补证内符宝郎从七品。", "官品", note="官品")
    ac(w, "Timepoints", t, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    w.commit()


def entry707():
    i = 707
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    grade = Q(i, "品位")
    comp = Q(i, "编制")
    aliases = Q(i, "别名")
    w = W(i)
    e = fe(w, "录事", "官职")
    jin = tp(w, e, "西晋", "已有录事之名", i, origin, "吏职", "建录事西晋职源节点。", "职源", chain="none")
    sui = tp(
        w,
        e,
        "隋朝",
        "门下省始置录事，为正八品命官",
        i,
        origin,
        "吏职",
        "建录事隋代节点。",
        "职源",
        attr_grade="正八品",
        chain="none",
    )
    tang = tp(
        w,
        e,
        "唐朝",
        "掌收受、登记文书及转发程限",
        i,
        duty,
        "吏职",
        "建录事唐代职掌节点。",
        "职掌",
        chain="none",
    )
    song = ft(w, e, "宋前期")
    yf = ft(w, e, "北宋元丰新制")
    refine(
        w,
        yf,
        i,
        duty,
        "据专条细化元丰门下省录事职掌。",
        "职掌",
        event="门下省高级省吏，掌诸房进奏、发放、点检文字并分掌诸房",
        category="吏职",
        grade="正八品",
        replace_quotation=True,
    )
    ac(w, "Timepoints", yf, i, main, "补证录事为门下省吏。")
    ac(w, "Timepoints", yf, i, grade, "补证正八品及堂后官地位。", "品位", note="品位")
    ac(w, "Timepoints", yf, i, comp, "补证元丰新制三人。", "编制", note="编制")
    ac(w, "Timepoints", yf, i, aliases, "后堂官为别名，不另建实体。", "别名", note="纯别名")
    chain(w, [jin, sui, tang, song, yf], "连接录事西晋至元丰沿革。")
    rid = rel(
        w,
        ft(w, fe(w, "门下省", "机构"), "北宋元丰新制"),
        yf,
        "编制隶属",
        i,
        comp,
        "元丰门下省录事三人。",
        "编制",
        staff_quota=3,
        staff_type="吏",
    )
    set_rel_attrs(w, rid, 3, "吏", "录事专条明载三人为额。")
    w.commit()


def entries708_710():
    for i, title, quota in (
        (708, "主事", 3),
        (709, "令史", 6),
        (710, "书令史", 10),
    ):
        main = Q(i)
        origin = Q(i, "职源")
        duty = Q(i, "职掌")
        grade = Q(i, "品位")
        comp = Q(i, "编制")
        w = W(i)
        e = fe(w, title, "官职")
        # 职源为汉、隋、唐的连续背景，用一个摘要节点承载，quotation 保留整段原文。
        source = tp(
            w,
            e,
            "汉至唐",
            f"{title}职名沿置",
            i,
            origin,
            "吏职",
            f"建{title}汉至唐职源节点。",
            "职源",
            chain="none",
        )
        yf_time = f"北宋元丰新制（门下省）"
        yf = ft(w, e, yf_time)
        event = (
            "门下省公吏，一名监印，其余分管本省诸房职事"
            if title == "主事"
            else "门下省吏，一名兼监印，其余分管诸房职事"
        )
        refine(
            w,
            yf,
            i,
            duty,
            f"据专条细化门下省{title}职掌。",
            "职掌",
            event=event,
            category="吏职",
            grade="从八品",
            replace_quotation=True,
        )
        ac(w, "Timepoints", yf, i, main, f"补证{title}隶门下省。")
        ac(w, "Timepoints", yf, i, grade, f"补证{title}从八品。", "品位", note="品位")
        ac(w, "Timepoints", yf, i, comp, f"补证元丰新制{quota}人。", "编制", note="编制")
        existing = w.conn.execute(
            "select id from Timepoints where entity_id=? and id<>? order by id", (e, source)
        ).fetchall()
        ordered = [source]
        # 保留既有链的相对顺序，只把职源节点置于最前。
        heads = [r[0] for r in w.conn.execute(
            "with recursive ch(id,succ_id,n) as ("
            " select id,succ_id,0 from Timepoints where entity_id=? and prev_id is null and id<>?"
            " union all select t.id,t.succ_id,ch.n+1 from ch join Timepoints t on t.id=ch.succ_id"
            ") select id from ch order by n",
            (e, source),
        )]
        if heads:
            ordered.extend(heads)
        else:
            ordered.extend(r[0] for r in existing)
        # 防止旧链恰好已包含新节点或存在重复收集。
        ordered = list(dict.fromkeys(ordered))
        chain(w, ordered, f"把{title}职源节点接到既有宋代链首。")
        rid = relation_id(w, "门下省", title, "编制隶属", "北宋元丰新制", yf_time)
        if rid is None:
            rid = rel(
                w,
                ft(w, fe(w, "门下省", "机构"), "北宋元丰新制"),
                yf,
                "编制隶属",
                i,
                comp,
                f"元丰门下省置{title}{quota}人。",
                "编制",
                staff_quota=quota,
                staff_type="吏",
            )
        else:
            ac(w, "Relationships", rid, i, comp, f"专条补证门下省置{title}{quota}人。", "编制")
        set_rel_attrs(w, rid, quota, "吏", f"{title}专条明载员额。")
        w.commit()


def main():
    assert [F[i]["title"] for i in range(691, 711)] == [
        "门下后省",
        "门下后省上案",
        "门下后省下案",
        "门下后省封驳案",
        "门下后省谏官案",
        "门下后省记注案",
        "给事中",
        "起居郎",
        "左散骑常侍",
        "左谏议大夫",
        "左补阙",
        "左司谏",
        "左拾遗",
        "左正言",
        "外符宝郎",
        "内符宝郎",
        "录事",
        "主事",
        "令史",
        "书令史",
    ]
    assert [F[i]["title"] for i in range(801, 805)] == [
        "右补阙",
        "右司谏",
        "右拾遗",
        "右正言",
    ]
    entry691()
    entries692_696()
    entry697()
    entry698()
    entry699()
    entry700()
    entry701()
    entry702()
    entry703()
    entry704()
    entry705_706()
    entry707()
    entries708_710()


if __name__ == "__main__":
    main()
