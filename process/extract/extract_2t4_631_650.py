#!/usr/bin/env python3
"""提取 chapter2t4 第631–650条：直阁贴职、三省与两省统称。"""
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
        r = c.execute(
            "select title,page,text,fields from chapter2t4 where id=?", (i,)
        ).fetchone()
    assert r, i
    return {"title": r[0], "page": r[1], "text": r[2] or "", "fields": json.loads(r[3] or "{}")}


F = {i: load(i) for i in range(631, 651)}


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
def refine(w, t, time, event, i, q, cat, d, **attrs):
    row = w.conn.execute(
        "select entity_id,time,event,attr_category,attr_officer_type,attr_grade from Timepoints where id=?", (t,)
    ).fetchone()
    assert row and not w.conn.execute(
        "select 1 from Timepoints where entity_id=? and time=? and id<>?", (row[0], time, t)
    ).fetchone()
    officer = attrs.get("attr_officer_type") or row[4]
    grade = attrs.get("attr_grade") or row[5]
    w.conn.execute(
        "update Timepoints set time=?,event=?,quotation=?,attr_category=?,attr_officer_type=?,attr_grade=? where id=?",
        (time, event, q, cat or row[3], officer, grade, t),
    )
    w._br("Timepoints", t, f"据专条细化 time={row[1]}、event={row[2]} 为 time={time}、event={event}：{d}")
    ac(w, "Timepoints", t, i, q, d)
    return t
def rename(w, e, new_title, i, q, d):
    row = w.conn.execute("select title,type from Entities where id=?", (e,)).fetchone()
    assert row
    if row[0] != new_title:
        assert not w.conn.execute(
            "select 1 from Entities where title=? and type=? and id<>?", (new_title, row[1], e)
        ).fetchone()
        w.conn.execute("update Entities set title=?,quotation=? where id=?", (new_title, q, e))
        w._br("Entities", e, f"据正式专条将{row[0]}规范为{new_title}：{d}")
    return e
def member(w, group_tp, title, typ, target_time, i, q, d):
    e = fe(w, title, typ)
    t = ft(w, e, target_time) if target_time else first_tp(w, e)
    return rel(w, group_tp, t, "统称与实例", i, q, d)


def entry631_633():
    i = 631; z = Q(i); w = W(i); e = fe(w, "直睿思殿", "官职")
    start = refine(w, ft(w, e, "北宋政和三年十二月"), "北宋政和三年十二月十八日", "始定为贴职，系宦官所带职名", i, z, "贴职", "专条补足始定日及宦官带职性质。", attr_officer_type="宦官")
    end = tp(w, e, "北宋政和六年九月", "停止列为贴职", i, z, "贴职", "建直睿思殿贴职终止节点。", chain="none")
    chain(w, [start, end], "连接直睿思殿始定与终止节点。")
    ac(w, "Timepoints", start, i, Q(i, "简称"), "补读简称字段所见直殿新置事实。", "简称", note="纯简称不另建实体")
    w.commit()

    i = 632; z = Q(i); w = W(i)
    e = en(w, "直阁", "官职", i, z, "原文明载为南宋十二等直阁贴职总称。")
    group = tp(w, e, "南宋", "自直秘阁至直龙图阁十二等贴职的总称", i, z, "贴职统称", "建直阁总称节点。", chain="none")
    chain(w, [ft(w, e, "北宋端拱元年五月"), ft(w, e, "宋代（未载具体年月）"), group,
              ft(w, e, "南宋咸淳元年六月")], "把南宋十二等贴职总称接入直阁既有沿革链。")
    members = (
        ("直龙图阁", "北宋元祐六年"), ("直天章阁", "北宋政和六年九月十七日"),
        ("直宝文阁", "北宋政和六年九月十七日"), ("直显谟阁", "北宋政和六年九月十七日"),
        ("直徽猷阁", "北宋政和六年九月十七日"), ("直敷文阁", "南宋绍兴十年五月十一日"),
        ("直焕章阁", "南宋淳熙十五年十一月九日"), ("直华文阁", "南宋庆元二年五月十五日"),
        ("直宝谟阁", "南宋嘉泰二年八月十二日"), ("直宝章阁", "南宋宝庆二年十月二日"),
        ("直显文阁", "南宋咸淳元年六月十八日"), ("直秘阁", "南宋嘉定十五年"),
    )
    for title, time in members:
        member(w, group, title, "官职", time, i, z, f"{title}为十二等直阁贴职之一。")
    w.commit()

    i = 633; z = Q(i); w = W(i); e = fe(w, "睿思殿供奉官", "官职")
    rename(w, e, "睿思殿供奉", i, z, "专条正式标题不带‘官’字。")
    start = refine(w, ft(w, e, "北宋政和三年十二月"), "北宋政和三年十二月十八日", "定为贴职，系宦官所带职名", i, z, "贴职", "专条补足始定日及宦官带职性质。", attr_officer_type="宦官")
    end = tp(w, e, "北宋政和六年九月", "未再列为贴职", i, z, "贴职", "建政和六年未列贴职节点。", chain="none")
    chain(w, [start, end], "连接睿思殿供奉定职与未再列职节点。")
    w.commit()


def entry634_637():
    i = 634; z = Q(i); w = W(i); group_e = fe(w, "三省", "机构")
    early = tp(w, group_e, "宋前期", "无实权，政归中书门下", i, z, "中央政务机构统称", "建三省宋前期状态节点。", chain="none")
    reform = tp(w, group_e, "北宋元丰新制", "分权为中书、门下、尚书三省，成为中央最高政务机构", i, z, "中央政务机构统称", "建三省元丰改制节点。", chain="none")
    old_chain = [ft(w, group_e, t) for t in ("南宋", "南宋初", "南宋建炎初", "南宋建炎四年六月")]
    chain(w, [early, reform] + old_chain, "把三省宋前期、元丰新制节点接入既有南宋链之前。")
    offices = (("中书省", "承旨、造令"), ("门下省", "审议、覆奏"), ("尚书省", "颁降、施行"))
    for title, duty in offices:
        oe = en(w, title, "机构", i, z, f"三省条明确列举{title}为组成机构。")
        ot = tp(w, oe, "北宋元丰新制", duty, i, z, "中央政务机构", f"建{title}元丰新制职能节点。", chain="none")
        rel(w, reform, ot, "统称与实例", i, z, f"三省由{title}等三个正式省构成。")
    w.commit()

    # 东府只是三省别称；其中乾道元年引文只是个别官员奏事例，不另建实体或时间点。
    i = 636; z = Q(i); w = W(i); group_e = fe(w, "三省", "机构"); t = ft(w, group_e, "北宋元丰新制")
    ac(w, "Timepoints", t, i, z, "台省虽为别称，所引元丰诏书补证三省官开始实典职事。", note="别称不另建实体")
    w.commit()
    i = 637; z = Q(i); w = W(i); group_e = fe(w, "三省", "机构"); t = ft(w, group_e, "北宋元丰新制")
    ac(w, "Timepoints", t, i, z, "省台虽为台省倒称，所引材料补证元丰官制下省官实典职事。", note="别称不另建实体")
    w.commit()


def entry638_641():
    i = 638; z = Q(i); w = W(i)
    ge = en(w, "三省长官", "官职", i, z, "原文明载为三省三名长官的总名。")
    g = tp(w, ge, "宋代（未载具体年月）", "侍中、中书令、尚书令的总名", i, z, "官职统称", "建三省长官统称节点。", chain="none")
    end = tp(w, ge, "南宋乾道八年", "删去三省长官之名", i, z, "官职统称", "建三省长官名终止节点。", chain="none")
    chain(w, [g, end], "连接三省长官总称与删名节点。")
    for title in ("侍中", "中书令", "尚书令"):
        e = en(w, title, "官职", i, z, f"原文明确列{title}为三省长官之一。")
        t = tp(w, e, "宋代（未载具体年月）", "三省长官之一", i, z, "职事官", f"建{title}作为三省长官的承载节点。", chain="none")
        rel(w, g, t, "统称与实例", i, z, f"{title}为三省长官实例。")
    w.commit()

    i = 639; z = Q(i); w = W(i)
    ge = en(w, "两令", "官职", i, z, "原文明载为中书令、尚书令合称。")
    g = tp(w, ge, "宋代（未载具体年月）", "中书令、尚书令合称", i, z, "官职统称", "建两令统称节点。", chain="none")
    end = tp(w, ge, "南宋乾道八年二月", "删去两令之名", i, z, "官职统称", "建两令删名节点。", chain="none")
    chain(w, [g, end], "连接两令合称与删名节点。")
    for title in ("中书令", "尚书令"):
        e = fe(w, title, "官职"); base = ft(w, e, "宋代（未载具体年月）")
        rel(w, g, base, "统称与实例", i, z, f"{title}为两令实例。")
    for title in ("侍中", "中书令", "尚书令"):
        e = fe(w, title, "官职")
        tp(w, e, "南宋乾道八年二月", "虚名删去", i, z, "职事官", f"建{title}乾道八年二月删名节点。")
    w.commit()

    i = 640; z = Q(i); w = W(i)
    ge = en(w, "三省都录事", "官职", i, z, "原文明载为三省最高等吏人总名。")
    g = tp(w, ge, "南宋绍兴年间", "中书、门下省录事和尚书省都事的总名，正八品", i, z, "吏职统称", "据《绍兴令》建三省都录事节点。", attr_grade="正八品", chain="none")
    for title in ("中书省录事", "门下省录事", "尚书省都事"):
        e = en(w, title, "官职", i, z, f"《绍兴令》明列{title}为三省都录事。")
        t = tp(w, e, "南宋绍兴年间", "三省堂后官，三省吏人中地位最高者", i, z, "吏职", f"建{title}绍兴令品级节点。", attr_grade="正八品", chain="none")
        rel(w, g, t, "统称与实例", i, z, f"{title}为三省都录事实例。")
    w.commit()

    i = 641; z = Q(i); w = W(i)
    e = en(w, "经抚房", "机构", i, z, "原文明载为临时机密办事部门。")
    start = tp(w, e, "北宋宣和四年", "设置，专管联金伐辽、收复燕云等边事", i, z, "临时机密机构", "建经抚房始置节点。", chain="none")
    end = tp(w, e, "北宋宣和六年", "罢废", i, z, "临时机密机构", "建经抚房罢废节点。", chain="none")
    chain(w, [start, end], "连接经抚房设置与罢废节点。")
    three = fe(w, "三省", "机构")
    three_x4 = tp(w, three, "北宋宣和四年", "名义设置经抚房", i, z, "中央政务机构统称", "建三省宣和四年经抚房关系端点。", chain="none")
    chain(w, [ft(w, three, "宋前期"), ft(w, three, "北宋元丰新制"), three_x4] + [ft(w, three, t) for t in ("南宋", "南宋初", "南宋建炎初", "南宋建炎四年六月")], "把宣和四年节点插入三省沿革链。")
    rel(w, three_x4, start, "上下级机构", i, z, "经抚房名义设于三省。")
    w.commit()


def entry642_645():
    i = 642; z = Q(i); w = W(i)
    ge = en(w, "两省", "机构", i, z, "原文明载为中书省、门下省合称。")
    old = tp(w, ge, "北宋元丰改制前", "中书省位在门下省之上", i, z, "机构统称", "建两省旧制节点。", chain="none")
    reform = tp(w, ge, "北宋元丰新制", "两省次序改变", i, z, "机构统称", "建两省元丰改序节点。", chain="none")
    tang = tp(w, ge, "唐代", "门下称左省、中书称右省，合称两省", i, z, "机构统称", "建唐代两省职源节点。", chain="none")
    chain(w, [tang, old, reform], "连接两省唐代称谓、宋旧制与元丰改序。")
    for title in ("中书省", "门下省"):
        oe = fe(w, title, "机构")
        ot = tp(w, oe, "北宋元丰改制前", "为两省之一", i, z, "中央政务机构", f"建{title}元丰前两省成员节点。", chain="head")
        rel(w, old, ot, "统称与实例", i, z, f"{title}为两省实例。")
    w.commit()

    i = 643; z = Q(i); w = W(i)
    ge = en(w, "北省", "机构", i, z, "原文明载门下、中书二省合称北省。")
    old = tp(w, ge, "北宋建隆三年前", "门下、中书省官班位高于尚书省官", i, z, "机构统称", "建北省建隆三年前班位节点。", chain="none")
    change = tp(w, ge, "北宋建隆三年三月", "调整北省与南省官朝会班位", i, z, "机构统称", "建北省建隆三年班位调整节点。", chain="none")
    chain(w, [old, change], "连接北省旧班位与建隆调整节点。")
    for title in ("中书省", "门下省"):
        oe = fe(w, title, "机构")
        ot = tp(w, oe, "北宋建隆三年前", "北省组成机构", i, z, "中央政务机构", f"建{title}北省成员节点。", chain="head")
        rel(w, old, ot, "统称与实例", i, z, f"{title}为北省实例。")
    w.commit()

    i = 644; z = Q(i); w = W(i)
    ge = en(w, "掖署", "机构", i, z, "原文明载为中书、门下二省通称，并明确不包括尚书省。")
    g = tp(w, ge, "宋代（沿唐称谓，未载具体年月）", "中书省、门下省通称", i, z, "机构统称", "建掖署通称节点。", chain="none")
    for title in ("中书省", "门下省"):
        rel(w, g, first_tp(w, fe(w, title, "机构")), "统称与实例", i, z, f"{title}为掖署所指实例。")
    w.commit()

    i = 645; z = Q(i); w = W(i)
    ge = en(w, "内两省", "机构", i, z, "原文明载为禁中中书、门下二省总称。")
    g = tp(w, ge, "北宋元丰新官制", "中书、门下省设于禁中，与皇城外尚书省相对", i, z, "机构统称", "建内两省元丰制度节点。", chain="none")
    for title in ("中书省", "门下省"):
        rel(w, g, ft(w, fe(w, title, "机构"), "北宋元丰新制"), "统称与实例", i, z, f"{title}为内两省实例。")
    w.commit()


def entry646_650():
    i = 646; z = Q(i); w = W(i)
    ge = en(w, "大两省", "官职", i, z, "原文明载为两省六类侍从官总名。")
    g = tp(w, ge, "宋代（未载具体年月）", "散骑常侍、给舍、谏议大夫的总名", i, z, "官职统称", "建大两省统称节点。", chain="none")
    titles = ("左散骑常侍", "右散骑常侍", "给事中", "中书舍人", "左谏议大夫", "右谏议大夫")
    for title in titles:
        e = w.find_entity(title, "官职") or en(w, title, "官职", i, z, f"大两省条明确列举{title}。")
        if title in ("给事中", "中书舍人"):
            t = first_tp(w, e)
        else:
            t = tp(w, e, "宋代（未载具体年月）", "大两省侍从官之一", i, z, "侍从官", f"建{title}大两省成员节点。", chain="none")
        rel(w, g, t, "统称与实例", i, z, f"{title}为大两省实例。")
    w.commit()

    i = 647; z = Q(i); w = W(i)
    ge = en(w, "两省长官", "官职", i, z, "原文明载为侍中、中书令合称。")
    g = tp(w, ge, "宋代（未载具体年月）", "侍中、中书令合称", i, z, "官职统称", "建两省长官统称节点。", chain="none")
    for title in ("侍中", "中书令"):
        member(w, g, title, "官职", "宋代（未载具体年月）", i, z, f"{title}为两省长官实例。")
    w.commit()

    i = 648; z = Q(i); w = W(i)
    ge = en(w, "两省侍郎", "官职", i, z, "原文明载为门下侍郎与中书侍郎合称。")
    g = tp(w, ge, "北宋元丰新制", "门下侍郎、中书侍郎合称，并代参知政事", i, z, "副相统称", "建两省侍郎元丰制度节点。", chain="none")
    rel_ids = []
    for title in ("门下侍郎", "中书侍郎"):
        rel_ids.append(member(w, g, title, "官职", "北宋元丰新制", i, z, f"{title}为两省侍郎实例。"))
    w.commit()

    i = 649; z = Q(i); w = W(i); ge = fe(w, "两省侍郎", "官职"); g = ft(w, ge, "北宋元丰新制")
    ac(w, "Timepoints", g, i, z, "左、右省侍郎为两省侍郎别称；引文补证其副长官地位。", note="纯别称不另建实体")
    for title in ("门下侍郎", "中书侍郎"):
        obj = ft(w, fe(w, title, "官职"), "北宋元丰新制")
        rid = w.conn.execute(
            "select id from Relationships where subject_id=? and object_id=? and relation_type='统称与实例'", (g, obj)
        ).fetchone()[0]
        ac(w, "Relationships", rid, i, z, f"别称条引文补证{title}为两省副长官之一。", note="别称条补证")
    w.commit()

    i = 650; z = Q(i); w = W(i)
    ge = en(w, "两后省", "机构", i, z, "原文明载为中书后省、门下后省合称。")
    g = tp(w, ge, "北宋元丰新官制", "中书后省、门下后省合称", i, z, "机构统称", "建两后省元丰节点。", chain="none")
    ch = fe(w, "中书后省", "机构"); cht = ft(w, ch, "北宋元丰新官制")
    mh = en(w, "门下后省", "机构", i, z, "原文明载为两后省组成机构之一。")
    mht = tp(w, mh, "北宋元丰新官制", "设置左史厅", i, z, "中央政务机构", "建门下后省元丰节点。", chain="none")
    rel(w, g, cht, "统称与实例", i, z, "中书后省为两后省实例。")
    rel(w, g, mht, "统称与实例", i, z, "门下后省为两后省实例。")
    rel(w, cht, ft(w, fe(w, "起居舍人", "官职"), "北宋元丰五年五月"), "编制隶属", i, z, "起居舍人（右史）分属中书后省。", staff_type="官")
    rel(w, mht, ft(w, fe(w, "起居郎", "官职"), "北宋元丰五年五月"), "编制隶属", i, z, "起居郎（左史）分属门下后省。", staff_type="官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(631, 651)] == [
        "直睿思殿", "直阁", "睿思殿供奉", "三省", "东府", "台省", "省台", "三省长官",
        "两令", "三省都录事", "经抚房", "两省", "北省", "掖署", "内两省", "大两省",
        "两省长官", "两省侍郎", "左、右省侍郎", "两后省",
    ]
    entry631_633(); entry634_637(); entry638_641(); entry642_645(); entry646_650()


if __name__ == "__main__":
    main()
