#!/usr/bin/env python3
"""提取 chapter2t4 第1351–1370条：秘书省杂役与司天台、司天监前段。"""
import extract_2t4_1331_1350 as x


base = x.base
base.F = {i: base.load(i) for i in range(1351, 1371)}
F = base.F
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def secretary_parent(w, time):
    return ft(w, fe(w, "秘书省", "机构"), time)


def entry1351():
    i = 1351
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("御厨工匠", "官职", "本条直接定义御厨工匠。",
                   quotation=main)
    north = tp(
        w, eid, "北宋（具体年月未载）",
        "每日分上、下班供送秘书省官员吃食",
        i, main, "秘书省杂役", "建立御厨工匠北宋节点。",
        attr_officer_type="匠人",
    )
    rel(
        w, secretary_parent(w, "宋前期"), north, "编制隶属",
        i, main, "北宋御厨工匠供送秘书省官吃食。",
        staff_type="匠人",
    )
    w.commit()


def entry1352_1353():
    i = 1352
    main = Q(i, F[i]["text"])
    w = W(i)
    unit_e = w.entity(
        "秘书省抬盘司", "机构",
        "本条明确它是储藏会食筵宴用具的秘书省省舍。",
        quotation=main,
    )
    unit_t = tp(
        w, unit_e, "南宋（具体年月未载）",
        "储藏会食、筵宴所用筷子、碗碟等用具",
        i, main, "秘书省省舍", "建立秘书省抬盘司南宋节点。",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), unit_t,
        "上下级机构", i, main, "秘书省抬盘司是秘书省省舍。",
    )
    w.commit()

    i = 1353
    main = Q(i, F[i]["text"])
    w = W(i)
    post_e = w.entity(
        "抬盘子厨子", "官职", "本条直接定义抬盘子厨子。",
        quotation=main,
    )
    post_t = tp(
        w, post_e, "南宋（秘书省）",
        "供奉秘书省官员吃食，简称抬盘子",
        i, main, "秘书省杂役", "建立抬盘子厨子南宋节点。",
        attr_officer_type="公吏",
    )
    rel(
        w, ft(w, unit_e, "南宋（具体年月未载）"), post_t, "编制隶属",
        i, main, "秘书省抬盘司由抬盘子厨子五人掌管。",
        staff_quota=5, staff_type="公吏",
    )
    w.commit()


def entry1354_1355():
    i = 1354
    main = Q(i, F[i]["text"])
    w = W(i)
    unit_e = w.entity(
        "潜火司", "机构",
        "本条明确潜火司是秘书省储放防火器材并值火警的省舍。",
        quotation=main,
    )
    unit_t = tp(
        w, unit_e, "南宋（具体年月未载）",
        "储放防火器材并值火警",
        i, main, "秘书省省舍", "建立潜火司南宋节点。",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), unit_t,
        "上下级机构", i, main, "潜火司是秘书省防火省舍。",
    )
    w.commit()

    i = 1355
    main = Q(i, F[i]["text"])
    w = W(i)
    post_e = w.entity(
        "潜火军兵", "官职", "本条直接定义秘书省潜火军兵。",
        quotation=main,
    )
    north = tp(
        w, post_e, "北宋（秘书省）",
        "潜火兵丁二百人，节级十人，部辖军员二人",
        i, main, "秘书省防火军兵", "建立潜火军兵北宋节点。",
        attr_officer_type="军兵", chain="none",
    )
    south = tp(
        w, post_e, "南宋（秘书省）",
        "潜火军兵六十六人，军员二人",
        i, main, "秘书省防火军兵", "建立潜火军兵南宋节点。",
        attr_officer_type="军兵", chain="none",
    )
    chain_all(w, post_e, [north, south], "连接潜火军兵北宋与南宋节点。")
    rel(
        w, secretary_parent(w, "宋前期"), north, "编制隶属",
        i, main, "北宋秘书省置潜火兵丁二百人。",
        staff_quota=200, staff_type="潜火兵丁（另节级十人、部辖军员二人）",
    )
    rel(
        w, ft(w, unit_e, "南宋（具体年月未载）"), south, "编制隶属",
        i, main, "南宋秘书省潜火司置潜火军兵六十六人。",
        staff_quota=66, staff_type="军兵（另军员二人）",
    )
    w.commit()


def entry1356_1357():
    i = 1356
    main = Q(i, F[i]["text"])
    w = W(i)
    unit_e = w.entity("补写所", "机构", "本条直接定义秘书省补写所。",
                      quotation=main)
    north = tp(
        w, unit_e, "北宋熙宁七年",
        "始置，缮写图书副本",
        i, main, "秘书省所属机构", "建立补写所熙宁始置节点。",
        chain="none",
    )
    south = tp(
        w, unit_e, "南宋（具体年月未载）", "沿置，缮写图书副本",
        i, main, "秘书省所属机构", "建立补写所南宋沿置节点。",
        chain="none",
    )
    chain_all(w, unit_e, [north, south], "连接补写所北宋始置与南宋沿置节点。")
    rel(
        w, secretary_parent(w, "宋前期"), north, "上下级机构",
        i, main, "熙宁七年补写所隶秘书省。",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), south,
        "上下级机构", i, main, "南宋补写所沿置于秘书省。",
    )
    w.commit()

    i = 1357
    main = Q(i, F[i]["text"])
    w = W(i)
    post_e = w.entity(
        "补写所杂务", "官职", "本条直接定义补写所杂务公吏。",
        quotation=main,
    )
    post_t = tp(
        w, post_e, "南宋（秘书省）", "掌补写所杂务",
        i, main, "秘书省公吏", "建立补写所杂务南宋节点。",
        attr_officer_type="公吏",
    )
    rel(
        w, south, post_t, "编制隶属", i, main,
        "补写所杂务隶秘书省补写所。",
        staff_type="公吏",
    )
    w.commit()


def entry1358():
    i = 1358
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "守门亲事官", "官职", "本条直接定义秘书省守门亲事官。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋（秘书省）",
        "轮班守门、登记书籍出入、抄转文历、投下文字及照管火烛头刃",
        i, main, "秘书省公吏", "建立守门亲事官南宋节点。",
        attr_officer_type="公吏",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), tid,
        "编制隶属", i, main, "守门亲事官把守秘书省大门。",
        staff_type="公吏",
    )
    for title, officer_type in (
        ("守门亲事官节级", "节级"),
        ("守门亲事官长行", "长行"),
    ):
        sub_e = w.entity(title, "官职", f"守门亲事官条明确列举{title}名目。",
                         quotation=main)
        sub_t = tp(
            w, sub_e, "南宋（秘书省）", "守门亲事官名目",
            i, main, "秘书省公吏", f"建立{title}南宋节点。",
            attr_officer_type=officer_type,
        )
        rel(
            w, tid, sub_t, "统称与实例", i, main,
            f"{title}是守门亲事官的名目。",
        )
    w.commit()


def attendant(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义秘书省从人{title}。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋（秘书省）", event,
        i, main, "秘书省官员从人", f"建立{title}南宋节点。",
        attr_officer_type="公吏",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), tid,
        "编制隶属", i, main, f"{title}为秘书省官员从人。",
        staff_type="公吏",
    )
    w.commit()


def entry1359():
    i = 1359
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("厅从", "官职", "本条直接定义秘书省官员从人统称厅从。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋（秘书省）", "秘书省官员办公厅吏胥、随从的统称",
        i, main, "秘书省官员从人统称", "建立厅从南宋节点。",
        attr_officer_type="公吏",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), tid,
        "编制隶属", i, main, "厅从是秘书省官员办公厅从人统称。",
        staff_type="公吏",
    )
    w.commit()


def entry1360():
    i = 1360
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("厅子", "官职", "本条直接定义秘书省各官厅子。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋（秘书省）", "秘书省各官厅吏人统称，每种一人",
        i, main, "秘书省官员从人统称", "建立厅子南宋节点。",
        attr_officer_type="官厅吏人",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), tid,
        "编制隶属", i, main, "秘书省八种官厅各置厅子一人。",
        staff_quota=8, staff_type="官厅吏人",
    )
    for title in (
        "秘书监厅子", "秘书少监厅子", "秘书丞厅子", "著作郎厅子",
        "秘书郎厅子", "著作佐郎厅子", "校书郎厅子", "正字厅子",
    ):
        sub_e = w.entity(title, "官职", f"厅子条明确列举{title}一人。",
                         quotation=main)
        sub_t = tp(
            w, sub_e, "南宋（秘书省）", "秘书省官厅吏人",
            i, main, "秘书省官员从人", f"建立{title}南宋节点。",
            attr_officer_type="官厅吏人",
        )
        rel(
            w, tid, sub_t, "统称与实例", i, main,
            f"{title}是厅子的实例。",
        )
    w.commit()


def entry1363():
    i = 1363
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity("司天台", "机构", "本条直接定义司天台。",
                   quotation=main)
    tang = tp(
        w, eid, "唐乾元元年三月十九日",
        "太史监改为司天台",
        i, history, "中央天文机构", "建立司天台唐代始名节点。",
        "职源与沿革", chain="none",
    )
    song = tp(
        w, eid, "北宋太宗朝", "沿置，掌天文历法",
        i, history, "中央天文机构", "建立司天台北宋节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", song, i, duty, "职掌参司天监专条。", "职掌")
    cite(
        w, "Timepoints", song, i, alias,
        "简称“天台”仅作称谓证据。", "简称", note="纯简称",
    )
    chain_all(w, eid, [tang, song], "连接司天台唐代与北宋节点。")
    collective_e = w.entity(
        "京百司", "机构", "司天台条明确它隶京百司。",
        quotation=main,
    )
    collective_t = tp(
        w, collective_e, "宋代（具体年月未载）", "京城中央官司统称",
        i, main, "机构统称", "建立京百司承载节点。",
    )
    rel(
        w, collective_t, song, "统称与实例", i, main,
        "司天台是京百司之一。",
    )
    w.commit()


def entry1364_1366():
    for i, title, event, officer_type in (
        (1364, "判司天台事", "领司天台事", "差遣"),
        (1365, "司天台主簿", "依所能在监内供职，经召试除授", "天文官"),
        (1366, "司天台学生", "在司天台诸处学习、供职", "吏"),
    ):
        main = Q(i, F[i]["text"])
        w = W(i)
        eid = w.entity(title, "官职", f"第{i}条直接定义{title}。",
                       quotation=main)
        tid = tp(
            w, eid, "北宋太宗朝", event,
            i, main, "司天台官属", f"建立{title}北宋节点。",
            attr_officer_type=officer_type,
        )
        if "简称" in F[i]["fields"]:
            cite(
                w, "Timepoints", tid, i, field(i, "简称"),
                f"{title}简称仅作称谓证据。", "简称", note="纯简称",
            )
        rel(
            w, ft(w, fe(w, "司天台", "机构"), "北宋太宗朝"), tid,
            "编制隶属", i, main, f"{title}隶司天台。",
            staff_type=officer_type,
        )
        w.commit()


def prebuild_astronomy_staff(w, office_t, i, staff, title, officer_type):
    eid = w.entity(title, "官职", f"司天监总条编制明确设置{title}。",
                   quotation=staff)
    tid = tp(
        w, eid, "北宋端拱元年九月以后", "司天监官属",
        i, staff, "司天监官属", f"建立{title}司天监节点。",
        "编制", attr_officer_type=officer_type,
    )
    rel(
        w, office_t, tid, "编制隶属", i, staff,
        f"司天监设置{title}。", "编制",
        staff_type=officer_type,
    )
    return eid, tid


def entry1367():
    i = 1367
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    standing = field(i, "位遇")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity("司天监", "机构", "本条直接定义司天监。",
                   quotation=main)
    liang = tp(
        w, eid, "南朝梁", "已有司天监之名",
        i, history, "中央天文机构", "建立司天监南朝名源节点。",
        "职源与沿革", chain="none",
    )
    song = tp(
        w, eid, "北宋端拱元年九月",
        "始见司天监之称，掌天文、历法、刻漏、祭祀版位及择日",
        i, history, "中央天文机构", "建立司天监北宋始置节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", song, i, duty, "补证司天监完整职掌。", "职掌")
    cite(w, "Timepoints", song, i, standing, "补证技术官位遇。", "位遇")
    cite(
        w, "Timepoints", song, i, aliases,
        "简称与别名仅作称谓证据。", "简称与别名", note="纯简称",
    )
    end = tp(
        w, eid, "北宋元丰五年",
        "改称太史局",
        i, history, "中央天文机构", "建立司天监元丰改名节点。",
        "职源与沿革", chain="none",
    )
    chain_all(w, eid, [liang, song, end], "连接司天监南朝名源至元丰改名节点。")
    sky_e = fe(w, "司天台", "机构")
    rel(
        w, ft(w, sky_e, "北宋太宗朝"), song, "前后演变",
        i, history, "宋初司天台至端拱元年始见司天监之称。",
        "职源与沿革",
    )
    bureau_e = fe(w, "太史局", "机构")
    rel(
        w, end, ft(w, bureau_e, "北宋元丰五年五月"), "前后演变",
        i, history, "元丰改制司天监改称太史局。",
        "职源与沿革",
    )
    collective_t = ft(
        w, fe(w, "京百司", "机构"), "宋代（具体年月未载）"
    )
    rel(
        w, collective_t, song, "统称与实例", i, main,
        "司天监隶京百司。",
    )
    officer_titles = (
        "司天监监", "司天监少监", "司天监丞", "司天监主簿",
        "司天监春官正", "司天监夏官正", "司天监中官正",
        "司天监秋官正", "司天监冬官正", "司天监灵台郎",
        "司天监保章正", "司天监挈壶正",
    )
    clerk_titles = (
        "司天监礼生", "司天监历生", "司天监测验官",
        "司天监记注官", "司天监刻择官", "司天监监生",
        "司天监押更", "司天监学生", "司天监节级",
        "司天监直官", "司天监鸡唱",
    )
    for title in officer_titles:
        prebuild_astronomy_staff(w, song, i, staff, title, "技术官")
    for title in clerk_titles:
        prebuild_astronomy_staff(w, song, i, staff, title, "吏")
    w.commit()


def entry1368():
    i = 1368
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "司天监监", "官职")
    tid = refine(
        w, ft(w, eid, "北宋端拱元年九月以后"), i, history,
        "专条细化司天监监职源。", "职源与沿革",
        event="司天监长官，领本监天文历法；罕除，多由他官兼判、同判或知",
        category="司天监长官", grade="从三品",
    )
    for quotation, decision, key in (
        (main, "正文补证技术官性质。", None),
        (duty, "补证长官职掌。", "职掌"),
        (grade, "补证从三品。", "官品"),
        (staff, "补证编制一人且不常除。", "编制"),
        (aliases, "简称与别名仅作称谓证据。", "简称与别名"),
    ):
        cite(w, "Timepoints", tid, i, quotation, decision, key)
    end = tp(
        w, eid, "北宋元丰五年", "随司天监罢置",
        i, history, "司天监长官", "建立司天监监元丰罢置节点。",
        "职源与沿革", chain="none",
    )
    chain_all(w, eid, [tid, end], "连接司天监监北宋任职与元丰罢置节点。")
    office_e = fe(w, "司天监", "机构")
    relationship_id = rel(
        w, ft(w, office_e, "北宋端拱元年九月"), tid, "编制隶属",
        i, staff, "司天监设监一人。", "编制",
        staff_quota=1, staff_type="技术官",
    )
    old_quota = w.conn.execute(
        "select staff_quota from Relationships where id=?", (relationship_id,)
    ).fetchone()[0]
    if old_quota != 1:
        w.conn.execute(
            "update Relationships set staff_quota=1,staff_type='技术官' "
            "where id=?", (relationship_id,),
        )
        w._br(
            "Relationships", relationship_id,
            f"司天监总条未载各官员额；据司天监监专条将编制由{old_quota}细化为一人。",
        )
    w.commit()


def judge_monitor(i, title, event):
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}差遣。",
                   quotation=main)
    tid = tp(
        w, eid, "北宋（司天监时期）", event,
        i, main, "司天监差遣", f"建立{title}北宋节点。",
        attr_officer_type="差遣", chain="none",
    )
    cite(
        w, "Timepoints", tid, i, alias,
        f"{title}简称仅作称谓证据。", "简称", note="纯简称",
    )
    office_t = ft(w, fe(w, "司天监", "机构"), "北宋端拱元年九月")
    rel(
        w, office_t, tid, "编制隶属", i, main,
        f"{title}领司天监事务。",
        staff_type="差遣",
    )
    nodes = [tid]
    if i == 1369:
        five_dynasties = tp(
            w, eid, "五代", "已有判司天监事差遣",
            i, main, "司天监差遣", "建立判司天监事五代职源节点。",
            attr_officer_type="差遣", chain="none",
        )
        nodes = [five_dynasties, tid]
    chain_all(w, eid, nodes, f"连接{title}完整时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1351, 1371)] == [
        "御厨工匠", "秘书省抬盘司", "抬盘子厨子", "潜火司",
        "潜火军兵", "补写所", "补写所杂务", "守门亲事官",
        "厅从", "厅子", "衣粮亲事官", "承送", "司天台",
        "判司天台事", "司天台主簿", "司天台学生", "司天监",
        "司天监监", "判司天监事", "同判司天监事",
    ]
    entry1351()
    entry1352_1353()
    entry1354_1355()
    entry1356_1357()
    entry1358()
    entry1359()
    entry1360()
    attendant(
        1361, "衣粮亲事官",
        "秘书省官员随从，除料钱外另有衣粮；监六人、少监四人、"
        "丞二人，著作郎佐及秘书郎二人，校书郎、正字无",
    )
    attendant(1362, "承送", "秘书省官员从人，位次衣粮亲事官")
    w = W(1359)
    group_t = ft(w, fe(w, "厅从", "官职"), "南宋（秘书省）")
    for title in ("厅子", "衣粮亲事官", "承送"):
        rel(
            w, group_t, ft(w, fe(w, title, "官职"), "南宋（秘书省）"),
            "统称与实例", 1359, Q(1359, F[1359]["text"]),
            f"{title}是厅从的实例。",
        )
    w.commit()
    entry1363()
    entry1364_1366()
    entry1367()
    entry1368()
    judge_monitor(
        1369, "判司天监事",
        "五代已有；宋代监或少监阙时，以五官正以上天文官判监事，"
        "位次监、少监",
    )
    judge_monitor(
        1370, "同判司天监事",
        "判监事置二员时，一员带“同”字",
    )


if __name__ == "__main__":
    main()
