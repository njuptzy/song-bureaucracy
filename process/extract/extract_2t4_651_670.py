#!/usr/bin/env python3
"""提取 chapter2t4 第651–670条：后省、给舍、起居官及谏官统称。"""
import json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")
)


def load(i):
    with sqlite3.connect(DICT_DB) as c:
        r = c.execute("select title,page,text,fields from chapter2t4 where id=?", (i,)).fetchone()
    assert r, i
    return {"title": r[0], "page": r[1], "text": r[2] or "", "fields": json.loads(r[3] or "{}")}


F = {i: load(i) for i in range(651, 671)}


def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])
def Q(i, k=None): return F[i]["fields"][k] if k else F[i]["text"]
def C(i, k=None):
    return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条' + (f"（{k}字段）" if k else "")
def en(w, title, typ, i, q, d): return w.entity(title, typ, d, quotation=q)
def ac(w, table, rid, i, q, d, k=None, **kw): return w.citation(table, rid, C(i, k), q, d, **kw)
def tp(w, e, time, event, i, q, cat, d, k=None, **kw):
    t = w.timepoint(e, time, event, d, q, attr_category=cat, **kw)
    ac(w, "Timepoints", t, i, q, d, k)
    return t
def rel(w, a, b, kind, i, q, d, k=None, **kw):
    r = w.relationship(a, b, kind, d, q, **kw)
    ac(w, "Relationships", r, i, q, d, k)
    return r
def chain(w, ts, d):
    assert ts and len(ts) == len(set(ts)), ts
    for n, t in enumerate(ts):
        w.relink(t, d, prev_id=ts[n - 1] if n else None, succ_id=ts[n + 1] if n + 1 < len(ts) else None)
def fe(w, title, typ=None):
    e = w.find_entity(title, typ)
    assert e, (title, typ)
    return e
def ft(w, e, time):
    t = w.find_timepoint(e, time)
    assert t, (e, time)
    return t
def first_tp(w, e):
    r = w.conn.execute("select id from Timepoints where entity_id=? order by id limit 1", (e,)).fetchone()
    assert r, e
    return r[0]
def group_rel(w, g, title, typ, target_time, i, q, d):
    e = fe(w, title, typ)
    t = ft(w, e, target_time) if target_time else first_tp(w, e)
    return rel(w, g, t, "统称与实例", i, q, d)
def relation_id(w, subject_title, object_title, kind):
    row = w.conn.execute(
        "select r.id from Relationships r "
        "join Timepoints a on a.id=r.subject_id join Entities ea on ea.id=a.entity_id "
        "join Timepoints b on b.id=r.object_id join Entities eb on eb.id=b.entity_id "
        "where ea.title=? and eb.title=? and r.relation_type=? order by r.id limit 1",
        (subject_title, object_title, kind),
    ).fetchone()
    assert row, (subject_title, object_title, kind)
    return row[0]
def add_grade(w, t, grade, i, q, d, k=None):
    row = w.conn.execute("select attr_grade from Timepoints where id=?", (t,)).fetchone()
    assert row
    if not row[0]:
        w.conn.execute("update Timepoints set attr_grade=? where id=?", (grade, t))
        w._br("Timepoints", t, f"补充官品 {row[0]}->{grade}：{d}")
    elif row[0] != grade:
        raise AssertionError((t, row[0], grade))
    ac(w, "Timepoints", t, i, q, d, k, note="官品")


def entry651_654():
    i = 651; z = Q(i); w = W(i); e = fe(w, "两后省", "机构"); t = ft(w, e, "北宋元丰新官制")
    ac(w, "Timepoints", t, i, z, "后两省为两后省倒称；引文补证后省官员常有缺额。", note="纯别称不另建实体")
    w.commit()

    i = 652; z = Q(i); w = W(i)
    e = en(w, "后省", "机构", i, z, "原文明载为中书后省、门下后省通称。")
    g = tp(w, e, "宋代（未载具体年月）", "中书后省、门下后省通称", i, z, "机构统称", "建后省通称节点。", chain="none")
    group_rel(w, g, "中书后省", "机构", "北宋元丰新官制", i, z, "中书后省为后省实例。")
    group_rel(w, g, "门下后省", "机构", "北宋元丰新官制", i, z, "门下后省为后省实例。")
    w.commit()

    i = 653; z = Q(i); w = W(i)
    e = en(w, "两省给舍", "官职", i, z, "原文明载为门下给事中、中书舍人合称。")
    g = tp(w, e, "北宋天禧元年八月", "给事中、中书舍人合称，获准乘狨毛暖坐", i, z, "官职统称", "建两省给舍天禧实见节点。", chain="none")
    members = []
    for title in ("给事中", "中书舍人"):
        me = fe(w, title, "官职")
        mt = tp(w, me, "北宋天禧元年八月", "两省给舍之一，获准乘狨毛暖坐", i, z, "职事官", f"建{title}天禧实见节点。", chain="head" if title == "给事中" else "tail")
        members.append((title, mt))
    for title, mt in members:
        rel(w, g, mt, "统称与实例", i, z, f"{title}为两省给舍实例。")
    w.commit()

    i = 654; z = Q(i); w = W(i)
    e = en(w, "给舍", "官职", i, z, "原文明载为给事中、中书舍人连称。")
    g = tp(w, e, "南宋（未载具体年月）", "中书舍人论奏制敕错误，给事中驳正中书遗失", i, z, "官职统称", "建给舍连称及分工节点。", chain="none")
    for title, event in (("给事中", "驳正中书制敕遗失"), ("中书舍人", "制敕有误时许论奏")):
        me = fe(w, title, "官职")
        mt = tp(w, me, "南宋（未载具体年月）", event, i, z, "职事官", f"建{title}南宋给舍分工节点。")
        rel(w, g, mt, "统称与实例", i, z, f"{title}为给舍实例。")
    w.commit()


def entry655_665():
    i = 655; z = Q(i); w = W(i)
    e = en(w, "二起居", "官职", i, z, "原文明载为起居郎、起居舍人合称。")
    g = tp(w, e, "宋代（未载具体年月）", "起居郎、起居舍人合称，分任左、右史", i, z, "起居官统称", "建二起居统称节点。", chain="none")
    r1 = group_rel(w, g, "起居郎", "官职", "宋初", i, z, "起居郎为二起居实例。")
    r2 = group_rel(w, g, "起居舍人", "官职", "宋初", i, z, "起居舍人为二起居实例。")
    w.commit()

    i = 656; z = Q(i); w = W(i); e = fe(w, "二起居", "官职"); base = ft(w, e, "宋代（未载具体年月）")
    yuanyou = tp(w, e, "北宋元祐元年", "左、右史为侍从之臣，并分隶门下、中书两省", i, z, "起居官统称", "建元祐左右史制度节点。", attr_officer_type="侍从官", chain="none")
    chain(w, [base, yuanyou], "连接二起居通称与元祐侍从节点。")
    for title in ("起居郎", "起居舍人"):
        rid = relation_id(w, "二起居", title, "统称与实例")
        ac(w, "Relationships", rid, i, z, f"左右史条补证{title}属于二起居。", note="别称条补证")
    for office, post in (("门下后省", "起居郎"), ("中书后省", "起居舍人")):
        rid = relation_id(w, office, post, "编制隶属")
        ac(w, "Relationships", rid, i, z, f"左右史条补证{post}分隶{office}。")
    w.commit()

    # 657“柱下史”只是二起居典故别称，王莽柱下史也不是宋代官职沿革，不另落四表。
    i = 658; z = Q(i); w = W(i); back = fe(w, "两后省", "机构")
    south = tp(w, back, "南宋", "中书、门下后省合二为一", i, z, "机构统称", "建南宋后省合一节点。")
    two = fe(w, "二起居", "官职"); base = ft(w, two, "宋代（未载具体年月）")
    ac(w, "Timepoints", base, i, z, "左右起居为二起居别称；引文补证南宋二官同省。", note="纯别称不另建实体")
    w.commit()

    i = 659; z = Q(i); w = W(i); two = fe(w, "二起居", "官职"); base = ft(w, two, "宋代（未载具体年月）")
    ac(w, "Timepoints", base, i, z, "小两省官为二起居号称，补证两官分隶两省。", note="纯别称不另建实体")
    for title in ("起居郎", "起居舍人"):
        rid = relation_id(w, "二起居", title, "统称与实例")
        ac(w, "Relationships", rid, i, z, f"小两省官条补证{title}为二起居成员。", note="别称条补证")
    for office, post in (("门下后省", "起居郎"), ("中书后省", "起居舍人")):
        rid = relation_id(w, office, post, "编制隶属")
        ac(w, "Relationships", rid, i, z, f"小两省官条补证{post}分隶{office}。")
    w.commit()

    i = 660; z = Q(i); w = W(i)
    for title, times in (("起居郎", ("宋初", "北宋元丰五年五月")), ("起居舍人", ("宋初", "北宋元丰五年五月"))):
        e = fe(w, title, "官职")
        for time in times:
            add_grade(w, ft(w, e, time), "从六品", i, z, f"一点青条明载{title}为从六品官。")
    w.commit()

    i = 661; z = Q(i); w = W(i); e = fe(w, "二起居", "官职")
    near = tp(w, e, "宋代近岁（未载具体年月）", "始命起居郎、起居舍人从驾", i, z, "起居官统称", "二史别称条含始命从驾的制度事实。")
    w.commit()

    i = 662; z = Q(i); w = W(i); e = fe(w, "二起居", "官职"); base = ft(w, e, "宋代（未载具体年月）")
    ac(w, "Timepoints", base, i, z, "小侍从为二起居官称，不另建别称实体。", note="纯别称不另建实体")
    for title in ("起居郎", "起居舍人"):
        rid = relation_id(w, "二起居", title, "统称与实例")
        ac(w, "Relationships", rid, i, z, f"小侍从条补证{title}属于二起居。", note="别称条补证")
    w.commit()

    i = 663; z = Q(i); w = W(i); e = fe(w, "二起居", "官职"); base = ft(w, e, "宋代（未载具体年月）")
    ac(w, "Timepoints", base, i, z, "螭头为起居郎、舍人典故称，不另建别称实体。", note="典故称不另建实体")
    w.commit()

    i = 664; z = Q(i); w = W(i); e = fe(w, "二起居", "官职"); base = ft(w, e, "宋代（未载具体年月）")
    ac(w, "Timepoints", base, i, z, "侍立官为二起居因分左右侍立所得官称。", note="官称不另建实体")
    for office, post in (("门下后省", "起居郎"), ("中书后省", "起居舍人")):
        rid = relation_id(w, office, post, "编制隶属")
        ac(w, "Relationships", rid, i, z, f"侍立官条补证{post}分左右侍立。")
    w.commit()

    i = 665; z = Q(i); w = W(i); e = fe(w, "二起居", "官职")
    reform = tp(w, e, "北宋元丰新制", "始正起居郎、舍人之名，不复并任谏列", i, z, "起居官统称", "修注官条含元丰正名制度事实。", chain="none")
    chain(w, [ft(w, e, "宋代（未载具体年月）"), reform, ft(w, e, "北宋元祐元年"), ft(w, e, "宋代近岁（未载具体年月）")], "把二起居元丰正名节点插入通称与元祐节点之间。")
    w.commit()


def entry666_670():
    i = 666; z = Q(i); w = W(i)
    e = en(w, "常侍", "官职", i, z, "原文明载为左、右散骑常侍通称。")
    g = tp(w, e, "宋代（未载具体年月）", "左、右散骑常侍通称", i, z, "官职统称", "建常侍通称节点。", chain="none")
    for title in ("左散骑常侍", "右散骑常侍"):
        group_rel(w, g, title, "官职", "宋代（未载具体年月）", i, z, f"{title}为常侍实例。")
    w.commit()

    i = 667; z = Q(i); w = W(i); e = fe(w, "常侍", "官职"); g = ft(w, e, "宋代（未载具体年月）")
    ac(w, "Timepoints", g, i, z, "骑省为左、右散骑常侍别称，不另建实体。", note="纯别称不另建实体")
    for title in ("左散骑常侍", "右散骑常侍"):
        rid = relation_id(w, "常侍", title, "统称与实例")
        ac(w, "Relationships", rid, i, z, f"骑省条补证{title}为常侍实例。", note="别称条补证")
    w.commit()

    i = 668; main = Q(i); aliases = Q(i, "别名"); w = W(i)
    e = en(w, "谏大夫", "官职", i, main, "原文明载为左、右谏议大夫通称。")
    pre = tp(w, e, "北宋元丰改制前", "左、右谏议大夫为寄禄官", i, main, "谏官统称", "建谏大夫元丰前节点。", chain="none")
    post = tp(w, e, "北宋元丰改制后", "左、右谏议大夫为谏官领袖，左隶门下、右隶中书", i, aliases, "谏官统称", "建谏大夫元丰后职掌隶属节点。", "别名", chain="none")
    chain(w, [pre, post], "连接谏大夫元丰前寄禄与元丰后谏官节点。")
    for title, office in (("左谏议大夫", "门下省"), ("右谏议大夫", "中书省")):
        me = fe(w, title, "官职"); generic = ft(w, me, "宋代（未载具体年月）")
        mt_pre = tp(w, me, "北宋元丰改制前", "为寄禄官", i, main, "寄禄官", f"建{title}元丰前节点。", chain="none")
        mt_post = tp(w, me, "北宋元丰改制后", "为谏官领袖", i, aliases, "谏官", f"建{title}元丰后节点。", "别名", chain="none")
        chain(w, [mt_pre, mt_post, generic], f"连接{title}元丰前后状态与既有总述节点。")
        rel(w, pre, mt_pre, "统称与实例", i, main, f"{title}为元丰前谏大夫实例。")
        rel(w, post, mt_post, "统称与实例", i, aliases, f"{title}为元丰后谏大夫实例。", "别名")
        rel(w, ft(w, fe(w, office, "机构"), "北宋元丰新制"), mt_post, "编制隶属", i, aliases, f"元丰改制后{title}隶{office}。", "别名", staff_type="官")
    w.commit()

    i = 669; main = Q(i); aliases = Q(i, "别称"); w = W(i)
    e = en(w, "司谏", "官职", i, main, "原文明载为左、右司谏通称。")
    g = tp(w, e, "宋代（未载具体年月）", "左、右司谏通称", i, main, "谏官统称", "建司谏通称节点。", attr_grade="七品", chain="none")
    ac(w, "Timepoints", g, i, aliases, "别称字段补证司谏为七品官。", "别称", note="官品")
    change_time = "宋代（《长编》卷29乙未）"
    for side in ("左", "右"):
        source_title, target_title = f"{side}补阙", f"{side}司谏"
        se = en(w, source_title, "官职", i, main, f"原文明载{source_title}改称{target_title}。")
        st = tp(w, se, change_time, f"改为{target_title}", i, main, "谏官", f"建{source_title}改名节点。", chain="none")
        te = en(w, target_title, "官职", i, main, f"原文明载{target_title}由{source_title}改称。")
        tt = tp(w, te, change_time, f"由{source_title}改称", i, main, "谏官", f"建{target_title}改名节点。", attr_grade="七品", chain="none")
        generic = tp(w, te, "宋代（未载具体年月）", "司谏之一", i, main, "谏官", f"建{target_title}统称成员节点。", attr_grade="七品", chain="none")
        chain(w, [tt, generic], f"连接{target_title}改名与宋代总述节点。")
        rel(w, st, tt, "前后演变", i, main, f"{source_title}改为{target_title}。")
        rel(w, g, generic, "统称与实例", i, main, f"{target_title}为司谏实例。")
        ac(w, "Timepoints", generic, i, aliases, f"别称字段补证{target_title}为七品官。", "别称", note="官品")
    w.commit()

    i = 670; z = Q(i); w = W(i)
    e = en(w, "正言", "官职", i, z, "原文明载为左、右正言通称。")
    g = tp(w, e, "宋代（未载具体年月）", "左、右正言通称", i, z, "谏官统称", "建正言通称节点。", chain="none")
    change_time = "宋代（《长编》卷29乙未）"
    for side in ("左", "右"):
        source_title, target_title = f"{side}拾遗", f"{side}正言"
        se = en(w, source_title, "官职", i, z, f"原文明载{source_title}改称{target_title}。")
        st = tp(w, se, change_time, f"改为{target_title}", i, z, "谏官", f"建{source_title}改名节点。", chain="none")
        te = en(w, target_title, "官职", i, z, f"原文明载{target_title}由{source_title}改称。")
        tt = tp(w, te, change_time, f"由{source_title}改称", i, z, "谏官", f"建{target_title}改名节点。", chain="none")
        generic = tp(w, te, "宋代（未载具体年月）", "正言之一", i, z, "谏官", f"建{target_title}统称成员节点。", chain="none")
        chain(w, [tt, generic], f"连接{target_title}改名与宋代总述节点。")
        rel(w, st, tt, "前后演变", i, z, f"{source_title}改为{target_title}。")
        rel(w, g, generic, "统称与实例", i, z, f"{target_title}为正言实例。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(651, 671)] == [
        "后两省", "后省", "两省给舍", "给舍", "二起居", "左右史", "柱下史", "左右起居",
        "小两省官", "一点青", "二史", "小侍从", "螭头", "侍立官", "修注官", "常侍",
        "骑省", "谏大夫", "司谏", "正言",
    ]
    entry651_654(); entry655_665(); entry666_670()


if __name__ == "__main__":
    main()
