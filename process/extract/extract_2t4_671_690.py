#!/usr/bin/env python3
"""提取 chapter2t4 第671–690条：谏院、都堂、门下省及其属司官职。"""
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


F = {i: load(i) for i in range(671, 691)}
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
def rewrite(w, t, time, event, i, q, cat, d, k=None, officer=None, grade=None):
    row = w.conn.execute(
        "select entity_id,time,event,attr_category,attr_officer_type,attr_grade from Timepoints where id=?", (t,)
    ).fetchone()
    assert row and not w.conn.execute(
        "select 1 from Timepoints where entity_id=? and time=? and id<>?", (row[0], time, t)
    ).fetchone()
    w.conn.execute(
        "update Timepoints set time=?,event=?,quotation=?,attr_category=?,attr_officer_type=?,attr_grade=? where id=?",
        (time, event, q, cat or row[3], officer or row[4], grade or row[5], t),
    )
    w._br("Timepoints", t, f"据专条细化 time={row[1]}、event={row[2]} 为 time={time}、event={event}：{d}")
    ac(w, "Timepoints", t, i, q, d, k)
    return t
def set_event(w, t, event, i, q, d, k=None):
    old = w.conn.execute("select event,quotation from Timepoints where id=?", (t,)).fetchone()
    assert old
    if (old[0], old[1]) != (event, q):
        w.conn.execute("update Timepoints set event=?,quotation=? where id=?", (event, q, t))
        w._br("Timepoints", t, f"据专条细化 event={old[0]}->{event}：{d}")
    ac(w, "Timepoints", t, i, q, d, k)
def relation_id(w, subject_title, object_title, kind, subject_time=None, object_time=None):
    sql = (
        "select r.id from Relationships r "
        "join Timepoints a on a.id=r.subject_id join Entities ea on ea.id=a.entity_id "
        "join Timepoints b on b.id=r.object_id join Entities eb on eb.id=b.entity_id "
        "where ea.title=? and eb.title=? and r.relation_type=?"
    )
    params = [subject_title, object_title, kind]
    if subject_time:
        sql += " and a.time=?"; params.append(subject_time)
    if object_time:
        sql += " and b.time=?"; params.append(object_time)
    row = w.conn.execute(sql + " order by r.id limit 1", params).fetchone()
    assert row, (subject_title, object_title, kind, subject_time, object_time)
    return row[0]
def set_rel_attrs(w, rid, quota, staff_type, d):
    old = w.conn.execute("select staff_quota,staff_type from Relationships where id=?", (rid,)).fetchone()
    assert old
    new = (quota if quota is not None else old[0], staff_type if staff_type is not None else old[1])
    if tuple(old) != new:
        w.conn.execute("update Relationships set staff_quota=?,staff_type=? where id=?", (*new, rid))
        w._br("Relationships", rid, f"补充编制属性 quota {old[0]}->{new[0]}, staff_type {old[1]}->{new[1]}：{d}")


def entry671():
    i = 671; z = Q(i); w = W(i)
    office = en(w, "谏院", "机构", i, z, "原文明载南宋两后省谏官另置局称谏院。")
    start = tp(w, office, "南宋", "中书、门下后省谏官另置局称谏院", i, z, "谏官机构", "建南宋谏院置局节点。", chain="none")
    sh2 = tp(w, office, "南宋绍兴二年", "谏院官吏依旧赴三省内原置局处供职", i, z, "谏官机构", "建绍兴二年谏院供职节点。", chain="none")
    chain(w, [start, sh2], "连接南宋谏院置局与绍兴二年供职节点。")
    parent = fe(w, "两后省", "机构")
    rel(w, ft(w, parent, "南宋"), start, "上下级机构", i, z, "谏院由中书、门下后省谏官另置。")

    group = en(w, "谏院", "官职", i, z, "原文明载谏院后用作两省六种谏官总名。")
    gt = tp(w, group, "南宋", "两省正职谏官总名", i, z, "谏官统称", "建南宋谏院官总称节点。", chain="none")
    members = ("左谏议大夫", "右谏议大夫", "左司谏", "右司谏", "左正言", "右正言")
    for title in members:
        me = fe(w, title, "官职")
        mt = tp(w, me, "南宋", "谏院正职官", i, z, "谏官", f"建{title}南宋谏院官节点。", attr_officer_type="正职")
        rel(w, gt, mt, "统称与实例", i, z, f"{title}为南宋谏院官实例。")
        rel(w, start, mt, "编制隶属", i, z, f"南宋谏院置{title}一人。", staff_quota=1, staff_type="官")
    w.commit()


def entry672():
    i = 672; z = Q(i); w = W(i)
    group = en(w, "谏官厅", "机构", i, z, "原文明载为门下、中书两省谏官厅事总名。")
    gt = tp(w, group, "北宋元祐元年十一月", "门下、中书两省谏官厅事总名", i, z, "机构统称", "建谏官厅元祐实见节点。", chain="none")
    for province, title in (("门下省", "门下省谏官厅"), ("中书省", "中书省谏官厅")):
        pe = fe(w, province, "机构")
        pt = tp(w, pe, "北宋元祐元年十一月", "设置谏官厅事", i, z, "中央政务机构", f"建{province}元祐谏官厅端点。")
        oe = en(w, title, "机构", i, z, f"原文明确{province}谏官各置厅事。")
        ot = tp(w, oe, "北宋元祐元年十一月", "谏官厅事", i, z, "谏官机构", f"建{title}节点。", chain="none")
        rel(w, gt, ot, "统称与实例", i, z, f"{title}为谏官厅实例。")
        rel(w, pt, ot, "上下级机构", i, z, f"{title}设于{province}。")
    w.commit()


def entry673():
    i = 673; main = Q(i); hist = Q(i, "职源与沿革"); duty = Q(i, "职能"); aliases = Q(i, "简称与别名"); w = W(i)
    e = en(w, "都堂", "机构", i, main, "原文明载为官署名。")
    tang = tp(w, e, "唐代", "尚书令厅，因尚书令多不除而成为议事之所", i, hist, "中央议事机构", "建都堂唐代职源节点。", "职源与沿革", chain="none")
    early = tp(w, e, "宋前期", "沿用，为朝廷典礼及定谥等集议之所", i, hist, "中央议事机构", "建都堂宋前期节点。", "职源与沿革", chain="none")
    ac(w, "Timepoints", early, i, duty, "补证宋前期集议职能。", "职能", note="职能")
    yuanfeng = tp(w, e, "北宋元丰新制", "三省聚议朝政之所，代替旧政事堂职能", i, duty, "中央议事机构", "建都堂元丰职能节点。", "职能", chain="none")
    zhenghe = tp(w, e, "北宋政和二年九月", "改名公相厅", i, hist, "中央议事机构", "建都堂改名节点。", "职源与沿革", chain="none")
    south = tp(w, e, "南宋", "仍称都堂，为三省、枢密院聚议军政之所", i, hist, "中央议事机构", "建南宋都堂节点。", "职源与沿革", chain="none")
    ac(w, "Timepoints", south, i, duty, "补证南宋三省、枢密院聚议军政职能。", "职能", note="职能")
    chain(w, [tang, early, yuanfeng, zhenghe, south], "连接都堂唐代职源、宋前期、元丰、政和与南宋节点。")

    public = en(w, "公相厅", "机构", i, hist, "原文明载都堂改为公相厅。")
    p_start = tp(w, public, "北宋政和二年九月", "由都堂改名，蔡京以公相总领三省事", i, hist, "中央议事机构", "建公相厅始置节点。", "职源与沿革", chain="none")
    p_end = tp(w, public, "北宋宣和二年十一月九日", "改名都厅", i, hist, "中央议事机构", "建公相厅改名节点。", "职源与沿革", chain="none")
    chain(w, [p_start, p_end], "连接公相厅始置与改名节点。")
    hall = en(w, "都厅", "机构", i, hist, "原文明载公相厅改为都厅。")
    h_start = tp(w, hall, "北宋宣和二年十一月九日", "由公相厅改名", i, hist, "中央议事机构", "建都厅始置节点。", "职源与沿革", chain="none")
    h_end = tp(w, hall, "南宋（未载恢复年月）", "复以都堂之名通行", i, hist, "中央议事机构", "建都厅转回都堂节点。", "职源与沿革", chain="none")
    chain(w, [h_start, h_end], "连接都厅始置与南宋复称都堂。")
    rel(w, zhenghe, p_start, "前后演变", i, hist, "都堂于政和二年改为公相厅。", "职源与沿革")
    rel(w, p_end, h_start, "前后演变", i, hist, "公相厅于宣和二年改为都厅。", "职源与沿革")
    rel(w, h_end, south, "前后演变", i, hist, "南宋仍通称都堂。", "职源与沿革")
    old = fe(w, "政事堂", "机构")
    rel(w, ft(w, old, "北宋元丰官制"), yuanfeng, "前后演变", i, duty, "元丰新制都堂代替旧政事堂职能。", "职能")
    shangshu = fe(w, "尚书省", "机构")
    rel(w, ft(w, shangshu, "北宋元丰新制"), yuanfeng, "上下级机构", i, duty, "都堂设于尚书省，为三省聚议朝政之所。", "职能")
    ac(w, "Timepoints", south, i, aliases, "别名字段补证南宋都堂亦称政事堂等，但不另建别称实体。", "简称与别名", note="纯别称不另建实体")
    w.commit()


def create_room(w, title, time, parent_tp, i, q, d):
    e = en(w, title, "机构", i, q, f"门下省编制明列{title}。")
    t = tp(w, e, time, "门下省办事部门", i, q, "省属办事机构", f"建{title}节点。", "编制", chain="none")
    rel(w, parent_tp, t, "上下级机构", i, q, f"{title}隶属门下省。", "编制")
    return e, t


def entry674():
    i = 674; main = Q(i); hist = Q(i, "职源与沿革"); duty = Q(i, "职掌"); comp = Q(i, "编制"); aliases = Q(i, "简称与别名"); w = W(i)
    e = fe(w, "门下省", "机构")
    early = rewrite(w, ft(w, e, "北宋元丰改制前"), "宋前期", "沿置但名存实亡，仅掌御宝、礼仪、考课等事", i, duty, "中央政务机构", "据总条细化宋前期状态。", "职掌")
    jin = tp(w, e, "晋朝", "始有门下省之称", i, hist, "中央政务机构", "建门下省晋代职源节点。", "职源与沿革", chain="none")
    yuanfeng = ft(w, e, "北宋元丰新制")
    set_event(w, yuanfeng, "中央审令机构，审读中书、枢密旨令和尚书六部文书", i, duty, "细化元丰新制职掌。", "职掌")
    yf8 = tp(w, e, "北宋元丰八年", "增催驱房，分房由九增至十", i, comp, "中央政务机构", "建门下省元丰八年增房节点。", "编制", chain="none")
    yy = tp(w, e, "北宋元祐间", "增班簿房、点检房", i, comp, "中央政务机构", "建门下省元祐增房节点。", "编制", chain="none")
    yy3 = tp(w, e, "北宋元祐三年", "增置点检房", i, comp, "中央政务机构", "建门下省元祐三年点检房节点。", "编制", chain="none")
    ss3 = tp(w, e, "北宋绍圣三年", "增守阙守当官一百人", i, comp, "中央政务机构", "建门下省绍圣三年增吏节点。", "编制", chain="none")
    south = tp(w, e, "南宋建炎三年四月", "与中书省合并为一省", i, hist, "中央政务机构", "建门下省南宋合并节点。", "职源与沿革", chain="none")
    chain(w, [jin, ft(w, e, "北宋建隆三年前"), early, yuanfeng, yf8,
              ft(w, e, "北宋元祐元年十一月"), yy, yy3, ss3, south],
          "重排门下省晋代职源至南宋合并沿革，并接入谏官厅条所建元祐节点。")
    ac(w, "Timepoints", early, i, comp, "补证宋前期判官一人及二十五名吏额。", "编制", note="编制")
    ac(w, "Timepoints", yuanfeng, i, hist, "补证两宋沿置与南宋合并。", "职源与沿革")
    ac(w, "Timepoints", yuanfeng, i, comp, "补证元丰新制官额、九房及吏额。", "编制", note="编制")
    ac(w, "Timepoints", early, i, aliases, "补读别名字段，不为门下、左省等纯别称另建实体。", "简称与别名", note="纯别称")

    room_specs = (
        ("门下省吏房", "北宋元丰新制"), ("门下省户房", "北宋元丰新制"),
        ("门下省礼房", "北宋元丰新制"), ("门下省兵房", "北宋元丰新制"),
        ("门下省刑房", "北宋元丰新制"), ("门下省工房", "北宋元丰新制"),
        ("门下省开拆房", "北宋元丰新制"), ("门下省章奏房", "北宋元丰新制"),
        ("门下省制敕库房", "北宋元丰新制"), ("门下省催驱房", "北宋元丰八年"),
        ("门下省班簿房", "北宋元祐间"), ("门下省点检房", "北宋元祐三年"),
    )
    parent_by_time = {"北宋元丰新制": yuanfeng, "北宋元丰八年": yf8, "北宋元祐间": yy, "北宋元祐三年": yy3}
    for title, time in room_specs:
        create_room(w, title, time, parent_by_time[time], i, comp, "总条编制明列该房。")

    post_specs = (
        ("侍中", "北宋元丰新制", 1), ("门下侍郎", "北宋元丰新制", 1),
        ("左散骑常侍", "北宋元丰新制", 1), ("给事中", "北宋元丰新制", 4),
        ("左谏议大夫", "北宋元丰改制后", 1), ("起居郎", "北宋元丰五年五月", 1),
        ("左司谏", "北宋元丰新制", 1), ("左正言", "北宋元丰新制", 1),
    )
    post_nodes = {}
    for title, time, quota in post_specs:
        pe = fe(w, title, "官职")
        pt = w.find_timepoint(pe, time) or tp(w, pe, time, "门下省官额", i, comp, "职事官", f"建{title}元丰官额节点。", "编制", chain="none")
        if w.find_timepoint(pe, time): ac(w, "Timepoints", pt, i, comp, f"补证{title}列门下省官额。", "编制", note="编制")
        post_nodes[title] = pt
        rid = rel(w, yuanfeng, pt, "编制隶属", i, comp, f"门下省置{title}{quota}人。", "编制", staff_quota=quota, staff_type="官")
        set_rel_attrs(w, rid, quota, "官", "门下省总条明载官额。")
    # 把本条新建的元丰官额节点按各实体既有历史位置接入。
    chain(w, [post_nodes["侍中"], ft(w, fe(w, "侍中", "官职"), "宋代（未载具体年月）"), ft(w, fe(w, "侍中", "官职"), "南宋乾道八年二月")], "暂接侍中元丰官额节点；专条将继续细化。")
    chain(w, [post_nodes["左散骑常侍"], ft(w, fe(w, "左散骑常侍", "官职"), "宋代（未载具体年月）")], "接入左散骑常侍元丰官额节点。")
    chain(w, [ft(w, fe(w, "给事中", "官职"), "北宋天禧元年八月"), post_nodes["给事中"], ft(w, fe(w, "给事中", "官职"), "北宋元丰五年六月二十五日"), ft(w, fe(w, "给事中", "官职"), "南宋（未载具体年月）")], "插入给事中元丰官额节点。")
    for title in ("左司谏", "左正言"):
        pe = fe(w, title, "官职")
        chain(w, [w.conn.execute("select id from Timepoints where entity_id=? and time like '宋代（《长编》%'", (pe,)).fetchone()[0], post_nodes[title], ft(w, pe, "宋代（未载具体年月）"), ft(w, pe, "南宋")], f"插入{title}元丰官额节点。")

    # 元丰新制吏额。
    staff_specs = (("门下省录事", 3), ("主事", 3), ("令史", 6), ("书令史", 18), ("守当官", 19))
    staff_nodes = {}
    for title, quota in staff_specs:
        se = fe(w, title, "官职")
        st = tp(w, se, "北宋元丰新制（门下省）", "门下省吏额", i, comp, "吏职", f"建{title}门下省吏额节点。", "编制", chain="none")
        staff_nodes[title] = st
        rel(w, yuanfeng, st, "编制隶属", i, comp, f"门下省置{title}{quota}人。", "编制", staff_quota=quota, staff_type="吏")
    chain(w, [staff_nodes["门下省录事"], ft(w, fe(w, "门下省录事", "官职"), "南宋绍兴年间")], "连接门下省录事元丰与绍兴节点。")
    chain(w, [ft(w, fe(w, "主事", "官职"), "宋前期"), staff_nodes["主事"], ft(w, fe(w, "主事", "官职"), "宋代（枢密院，未载具体年月）")], "插入主事门下省元丰吏额节点。")
    chain(w, [ft(w, fe(w, "令史", "官职"), "宋代（枢密院，未载具体年月）"), staff_nodes["令史"], ft(w, fe(w, "令史", "官职"), "南宋嘉定五年")], "插入令史门下省元丰吏额节点。")
    chain(w, [ft(w, fe(w, "书令史", "官职"), "宋代（枢密院，未载具体年月）"), ft(w, fe(w, "书令史", "官职"), "北宋淳化四年二月"), staff_nodes["书令史"], ft(w, fe(w, "书令史", "官职"), "南宋嘉定五年")], "插入书令史门下省元丰吏额节点。")
    chain(w, [ft(w, fe(w, "守当官", "官职"), "宋前期"), staff_nodes["守当官"], ft(w, fe(w, "守当官", "官职"), "南宋嘉定五年")], "插入守当官门下省元丰吏额节点。")

    for title, quota in (("白院令史", 12), ("画院令史", 3), ("甲库令史", 2), ("赞者", 4), ("驱使", 4)):
        se = en(w, title, "官职", i, comp, f"宋前期门下省吏额明列{title}。")
        st = tp(w, se, "宋前期（门下省）", "门下省吏额", i, comp, "吏职", f"建{title}宋前期吏额节点。", "编制", chain="none")
        rel(w, early, st, "编制隶属", i, comp, f"宋前期门下省置{title}{quota}人。", "编制", staff_quota=quota, staff_type="吏")
    guard = en(w, "守阙守当官", "官职", i, comp, "原文明确绍圣三年增置守阙守当官。")
    guard_t = tp(w, guard, "北宋绍圣三年", "门下省增置", i, comp, "吏职", "建守阙守当官绍圣节点。", "编制", chain="none")
    rel(w, ss3, guard_t, "编制隶属", i, comp, "门下省增守阙守当官一百人。", "编制", staff_quota=100, staff_type="吏")
    w.commit()


def entries675_686():
    specs = {
        675: ("北宋元丰新制", "承尚书省吏部七司文书，掌官员班簿及本省杂务"),
        676: ("北宋元丰新制", "承尚书省户部五司所上文书"),
        677: ("北宋元丰新制", "承尚书省礼部四司所上文书"),
        678: ("北宋元丰新制", "承尚书省兵部四司所上文书"),
        679: ("北宋元丰新制", "承尚书省刑部四司所上文书"),
        680: ("北宋元丰新制", "承尚书省工部四司所上文书"),
        681: ("北宋元丰新制", "收发日常公事文书"),
        682: ("北宋元丰新制", "编目、分类进呈所领章奏"),
        683: ("北宋元丰新制", "汇编登记敕令格式并归档经审读的官爵勋黄甲文书"),
        684: ("北宋元丰八年", "检察催促本省诸房文书按期发送"),
        685: ("北宋元祐间", "由吏房分出，掌百官名籍以备查对"),
        686: ("北宋元祐三年", "检查诸房所行文书有无失误"),
    }
    for i, (time, event) in specs.items():
        z = Q(i); w = W(i); e = fe(w, F[i]["title"], "机构"); t = ft(w, e, time)
        set_event(w, t, event, i, z, "专条补足本房职掌。")
        rid = relation_id(w, "门下省", F[i]["title"], "上下级机构", object_time=time)
        ac(w, "Relationships", rid, i, z, f"专条补证{F[i]['title']}隶门下省。")
        w.commit()


def entry687():
    i = 687; z = Q(i); w = W(i)
    e = en(w, "判门下省事", "官职", i, z, "原文明载为宋前期差遣官。")
    t = tp(w, e, "宋前期", "领门下省事，掌郊祀、大朝会及流外官考较等", i, z, "差遣官", "建判门下省事宋前期节点。", attr_officer_type="给事中", chain="none")
    parent = fe(w, "门下省", "机构")
    rel(w, ft(w, parent, "宋前期"), t, "编制隶属", i, z, "宋前期门下省置判门下省事一人，以给事中充。", staff_quota=1, staff_type="官")
    w.commit()


def entry688():
    i = 688; main = Q(i); hist = Q(i, "职源与沿革"); duty = Q(i, "职掌"); grade = Q(i, "官品"); comp = Q(i, "编制"); aliases = Q(i, "别名"); w = W(i)
    e = fe(w, "侍中", "官职")
    song = rewrite(w, ft(w, e, "宋代（未载具体年月）"), "宋前期", "为使相与宰相所带阶官，位高罕除", i, main, "阶官", "据侍中专条细化宋前期节点。", grade="正二品")
    ac(w, "Timepoints", song, i, duty, "补证宋前期使相、宰相带阶及元丰寄禄改易。", "职掌", note="职掌")
    ac(w, "Timepoints", song, i, grade, "补证宋初正二品。", "官品", note="官品")
    qin = tp(w, e, "秦代", "丞相史入殿往来，侍中名称所本", i, hist, "阶官", "建侍中秦代职源节点。", "职源与沿革", chain="none")
    yf = ft(w, e, "北宋元丰新制")
    set_event(w, yf, "名为门下省长官、真宰相，实虚位不除，由尚书左仆射兼门下侍郎行职", i, duty, "据专条细化元丰侍中状态。", "职掌")
    row = w.conn.execute("select attr_grade from Timepoints where id=?", (yf,)).fetchone()
    if not row[0]:
        w.conn.execute("update Timepoints set attr_grade='正一品' where id=?", (yf,)); w._br("Timepoints", yf, "侍中专条补元丰改制后正一品。")
    ac(w, "Timepoints", yf, i, grade, "补证元丰改制后正一品。", "官品", note="官品")
    ac(w, "Timepoints", yf, i, comp, "补证元丰新制一员、虚不除人。", "编制", note="编制")
    feb = ft(w, e, "南宋乾道八年二月")
    old = w.conn.execute("select event from Timepoints where id=?", (feb,)).fetchone()[0]
    if old != "议删侍中虚名":
        w.conn.execute("update Timepoints set event='议删侍中虚名' where id=?", (feb,)); w._br("Timepoints", feb, f"据专条区分二月议删与三月正式罢置：event {old}->议删侍中虚名")
    end = tp(w, e, "南宋乾道八年三月二十日", "正式罢置", i, hist, "职事官", "建侍中乾道正式罢置节点。", "职源与沿革", chain="none")
    chain(w, [qin, song, yf, feb, end], "重排侍中秦代职源、宋前期、元丰及乾道罢置。")
    ac(w, "Timepoints", song, i, aliases, "补读侍中别名典故，不另建省长、左貂等实体。", "别名", note="纯别名")
    w.commit()

def entry689():
    i = 689; z = Q(i); w = W(i); e = fe(w, "侍中", "官职")
    zhenghe = tp(w, e, "北宋政和二年九月二十五日", "改名门下省左辅", i, z, "职事官", "建侍中改左辅节点。", chain="none")
    restore = tp(w, e, "北宋靖康元年十一月二十九日", "由左辅恢复侍中旧名", i, z, "职事官", "建侍中靖康复名节点。", chain="none")
    chain(w, [ft(w, e, "秦代"), ft(w, e, "宋前期"), ft(w, e, "北宋元丰新制"),
              zhenghe, restore, ft(w, e, "南宋乾道八年二月"),
              ft(w, e, "南宋乾道八年三月二十日")],
          "把侍中政和改左辅、靖康复名节点接入沿革链。")
    left = fe(w, "左辅", "官职")
    left_start = rewrite(w, ft(w, left, "北宋政和二年九月"), "北宋政和二年九月二十五日", "由门下省侍中改名", i, z, "职事官", "据左辅专条补确日并细化改名。")
    left_end = tp(w, left, "北宋靖康元年十一月二十九日", "恢复旧名侍中", i, z, "职事官", "建左辅复旧名节点。", chain="none")
    chain(w, [left_start, left_end], "连接左辅改置与复旧名节点。")
    rel(w, zhenghe, left_start, "前后演变", i, z, "侍中于政和二年改为左辅。")
    rel(w, left_end, restore, "前后演变", i, z, "左辅于靖康元年恢复侍中旧名。")
    w.commit()


def entry690():
    i = 690; main = Q(i); hist = Q(i, "职源与沿革"); duty = Q(i, "职掌"); grade = Q(i, "官品"); aliases = Q(i, "简称与别名"); w = W(i)
    e = fe(w, "门下侍郎", "官职")
    for time in ("汉代", "魏晋以来", "隋炀帝及唐前期", "唐天宝二年"):
        ac(w, "Timepoints", ft(w, e, time), i, hist, f"专条补证门下侍郎{time}职源。", "职源与沿革")
    song = ft(w, e, "宋前期"); yf = ft(w, e, "北宋元丰新制"); end = ft(w, e, "南宋建炎三年四月十三日")
    ac(w, "Timepoints", song, i, main, "补证宋前期为阶官。")
    ac(w, "Timepoints", song, i, duty, "补证宋前期不与政、为宰相所带阶官。", "职掌", note="职掌")
    ac(w, "Timepoints", song, i, grade, "补证宋前期正三品。", "官品", note="官品")
    ac(w, "Timepoints", yf, i, main, "补证元丰新制为职事官。")
    ac(w, "Timepoints", yf, i, duty, "补证元丰新制左相兼官与副相两种职能。", "职掌", note="职掌")
    ac(w, "Timepoints", yf, i, grade, "补证元丰新制正二品。", "官品", note="官品")
    ac(w, "Timepoints", end, i, hist, "补证建炎三年由参知政事取代、此后不置。", "职源与沿革")
    ac(w, "Timepoints", yf, i, aliases, "补读简称别名字段，不另建门侍、省佐等实体。", "简称与别名", note="纯别称")
    parent = fe(w, "门下省", "机构")
    rel(w, ft(w, parent, "北宋元丰新制"), yf, "编制隶属", i, duty, "元丰新制门下侍郎为门下省副长官。", "职掌", staff_quota=1, staff_type="官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(671, 691)] == [
        "谏院", "谏官厅", "都堂", "门下省", "门下省吏房", "门下省户房", "门下省礼房",
        "门下省兵房", "门下省刑房", "门下省工房", "门下省开拆房", "门下省章奏房",
        "门下省制敕库房", "门下省催驱房", "门下省班簿房", "门下省点检房", "判门下省事",
        "侍中", "左辅", "门下侍郎",
    ]
    entry671(); entry672(); entry673(); entry674(); entries675_686(); entry687(); entry688(); entry689(); entry690()


if __name__ == "__main__":
    main()
