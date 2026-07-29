#!/usr/bin/env python3
"""提取 chapter2t4 第1271–1290条：水部员外、军器所与秘书省前段。"""
import extract_2t4_1251_1270 as x


base = x.base
base.F = {i: base.load(i) for i in range(1271, 1291)}
base.F[1269] = base.load(1269)
F = base.F
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine
ft_any = x.ft_any


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def entry1271():
    i = 1271
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称")
    office_staff = field(1269, "编制")
    w = W(i)
    eid = fe(w, "水部司员外郎", "官职")
    sui = tp(
        w, eid, "隋开皇六年", "始置水部司员外郎",
        i, origin, "水部司郎官", "建立水部司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期",
        "无职事，为后行员外郎寄禄官阶，元丰后寄禄官易朝奉郎",
        i, duty, "文臣迁转官阶", "建立水部司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), 1269, office_staff,
        "水部司总条补证元丰置员外郎一人。", "编制",
        event="水部司副长官", category="水部司郎官", grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称仅作称谓证据。", "简称", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(
        w, eid, [sui, song, reform],
        "连接水部司员外郎隋、宋前期与元丰节点。",
    )
    office_e = fe(w, "水部司", "机构")
    rel(
        w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期水部司员外郎为无职事阶官。", "职掌", staff_type="官",
    )
    rel(
        w, ft(w, office_e, "北宋元丰新制"), reform, "编制隶属",
        1269, office_staff, "元丰水部司置员外郎一人。", "编制",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1272():
    i = 1272
    main = Q(i, F[i]["text"])
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    alias = field(i, "别名")
    w = W(i)
    archive_e = w.entity(
        "工、刑部架阁库", "机构", "本条明确主管工、刑二部档案库。",
        quotation=duty,
    )
    archive_t = tp(
        w, archive_e, "南宋绍兴十五年",
        "工部、刑部合置的档案库，收存办结逾二年的文书帐籍",
        i, origin, "六部架阁库", "建立工、刑部架阁库绍兴十五年节点。",
        "职源与沿革",
    )
    cite(w, "Timepoints", archive_t, i, duty, "补证档案入库与检索职掌。", "职掌")
    eid = w.entity(
        "主管尚书省工部、刑部架阁文字", "官职",
        "本条直接定义工、刑两部合置主管架阁文字官。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋绍兴十五年",
        "始置，主管工部、刑部架阁库档案编目、登记与检索",
        i, origin, "工刑二部档案官",
        "建立主管尚书省工部、刑部架阁文字节点。",
        "职源与沿革",
    )
    cite(w, "Timepoints", tid, i, duty, "补证具体档案职掌。", "职掌")
    cite(w, "Timepoints", tid, i, rank, "补证以有时望的进士出身选人充任。", "品位")
    cite(
        w, "Timepoints", tid, i, alias,
        "别名‘掌故’仅作称谓证据。", "别名", note="纯别名",
    )
    rel(
        w, archive_t, tid, "编制隶属", i, origin,
        "绍兴十五年工、刑部合置主管架阁文字官。", "职源与沿革",
        staff_quota=1, staff_type="官",
    )
    generic_e = fe(w, "主管尚书某部架阁文字", "官职")
    rel(
        w, ft(w, generic_e, "南宋绍兴十五年"), tid, "统称与实例",
        i, origin, "本官是主管尚书某部架阁文字的工、刑部实例。",
        "职源与沿革",
    )
    work_e = fe(w, "工部", "机构")
    justice_e = fe(w, "刑部", "机构")
    rel(
        w, ft(w, work_e, "南宋绍兴五年"), archive_t, "上下级机构",
        i, duty, "工部与刑部共用本架阁库。", "职掌",
    )
    rel(
        w, ft(w, justice_e, "南宋建炎三年"), archive_t, "上下级机构",
        i, duty, "刑部与工部共用本架阁库。", "职掌",
    )
    w.commit()


def create_military_post(w, office_tp, i, quotation, title, event, quota,
                         *, time="北宋元丰新制", staff_type="官"):
    eid = w.entity(
        title, "官职", f"军器所编制明确设置{title}。",
        quotation=quotation,
    )
    tid = tp(
        w, eid, time, event, i, quotation, "军器所官属",
        f"建立{title}{time}节点。", "编制", chain="none",
    )
    rel(
        w, office_tp, tid, "编制隶属", i, quotation,
        f"制造御前军器所设置{title}。", "编制",
        staff_quota=quota, staff_type=staff_type,
    )
    return eid, tid


def entry1273():
    i = 1273
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity(
        "制造御前军器所", "机构", "本条直接定义制造御前军器所。",
        quotation=main,
    )
    reform = tp(
        w, eid, "北宋元丰新制", "始置，制造盔甲、马甲、弓枪刀箭等军器",
        i, origin, "中央军器制造机构",
        "建立制造御前军器所元丰始置节点。", "职源", chain="none",
    )
    cite(w, "Timepoints", reform, i, duty, "补证军器制造职掌。", "职掌")
    later_control = tp(
        w, eid, "宋代元丰以后（具体年月未载）",
        "由初隶工部改隶步军司、殿前司",
        i, main, "中央军器制造机构",
        "建立制造御前军器所隶属变化节点。", None, chain="none",
    )
    jianyan = tp(
        w, eid, "南宋建炎初", "吏额由北宋四十四人减为八人，后略增",
        i, staff, "中央军器制造机构",
        "建立制造御前军器所建炎裁减吏额节点。", "编制", chain="none",
    )
    shaoxing3 = tp(
        w, eid, "南宋绍兴三年四月九日",
        "东、西作坊并入，人员定为一千六百人",
        i, staff, "中央军器制造机构",
        "建立军器所绍兴三年并入两作坊节点。", "编制", chain="none",
    )
    shaoxing15 = tp(
        w, eid, "南宋绍兴十五年",
        "提辖官、监造官各增至六员",
        i, staff, "中央军器制造机构",
        "建立军器所绍兴十五年官额变化节点。", "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴初",
        "隶工部，枢密院与工部提纲、军器监居中统辖",
        i, aliases, "中央军器制造机构",
        "建立制造御前军器所隆兴统属节点。",
        "简称与别名", chain="none",
    )
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与别名仅作称谓及统属证据。",
        "简称与别名", note="简称兼隆兴统属证据",
    )
    ordered = [reform, later_control, jianyan, shaoxing3]
    return_from_bureau = w.find_timepoint(eid, "南宋绍兴七年十一月")
    if return_from_bureau:
        ordered.append(return_from_bureau)
    ordered.extend([shaoxing15, longxing])
    chain_all(
        w, eid, ordered,
        "连接制造御前军器所元丰至隆兴完整时间链。",
    )
    work_e = fe(w, "工部", "机构")
    rel(
        w, ft(w, work_e, "北宋元丰新制"), reform, "上下级机构",
        i, main, "制造御前军器所始隶工部。",
    )
    for parent_title in ("步军司", "殿前司"):
        parent_e = w.entity(
            parent_title, "机构", f"本条明载军器所后隶{parent_title}。",
            quotation=main,
        )
        parent_t = tp(
            w, parent_e, "宋代元丰以后（具体年月未载）",
            f"制造御前军器所的上级机构之一",
            i, main, "禁军统辖机构", f"据军器所条建立{parent_title}承载节点。",
        )
        rel(
            w, parent_t, later_control, "上下级机构", i, main,
            f"制造御前军器所后隶{parent_title}。",
        )
    monitor_e = fe(w, "军器监", "机构")
    monitor_longxing = tp(
        w, monitor_e, "南宋隆兴初", "居枢密院、工部与军器所、作坊之间统辖",
        i, aliases, "军器机构", "建立军器监隆兴统辖节点。",
        "简称与别名", chain="none",
    )
    existing_monitor = [
        row[0] for row in w.conn.execute(
            "select id from Timepoints where entity_id=? and id<>? order by id",
            (monitor_e, monitor_longxing),
        )
    ]
    chain_all(
        w, monitor_e, existing_monitor + [monitor_longxing],
        "连接军器监北宋与南宋隆兴节点。",
    )
    rel(
        w, ft(w, work_e, "南宋隆兴后"), monitor_longxing, "上下级机构",
        i, aliases, "隆兴时工部在上提纲军器事务。", "简称与别名",
    )
    privy_e = fe(w, "枢密院", "机构")
    rel(
        w, ft(w, privy_e, "南宋绍兴七年"), monitor_longxing, "上下级机构",
        i, aliases, "隆兴时枢密院在上提纲军器事务。", "简称与别名",
    )
    rel(
        w, monitor_longxing, longxing, "上下级机构", i, aliases,
        "隆兴时军器监居中统辖制造御前军器所。", "简称与别名",
    )

    posts = [
        ("提点制造御前军器所", "提点御前军器所事务", 2, "官"),
        ("提辖制造御前军器所", "提辖军器制造", 2, "官"),
        ("制造御前军器所监造官", "监督军器制造", 2, "官"),
        ("干办制造御前军器所公事", "干办军器所事务", 2, "官"),
        ("制造御前军器所受给官", "办理物料军器受给", None, "官（一或二员）"),
        ("制造御前军器所监门官", "监督军器所门户", None, "官（一或二员）"),
    ]
    post_nodes = {}
    for title, event, quota, staff_type in posts:
        post_nodes[title] = create_military_post(
            w, reform, i, staff, title, event, quota, staff_type=staff_type,
        )
    for title in ("提辖制造御前军器所", "制造御前军器所监造官"):
        post_e, north = post_nodes[title]
        south = tp(
            w, post_e, "南宋绍兴十五年", "增至六员",
            i, staff, "军器所官属", f"建立{title}绍兴十五年增额节点。",
            "编制", chain="none",
        )
        chain_all(w, post_e, [north, south], f"连接{title}元丰与绍兴十五年节点。")
        rel(
            w, shaoxing15, south, "编制隶属", i, staff,
            f"绍兴十五年{title}增至六员。", "编制",
            staff_quota=6, staff_type="官",
        )

    for title in ("军器所行移内案", "军器所军器案", "军器所事务案"):
        case_e = w.entity(
            title, "机构", f"军器所编制列举{title}。",
            quotation=staff,
        )
        case_t = tp(
            w, case_e, "北宋元丰新制", "军器所三案之一",
            i, staff, "军器所办事机构", f"建立{title}元丰节点。",
            "编制",
        )
        rel(
            w, reform, case_t, "上下级机构", i, staff,
            f"{title}隶制造御前军器所。", "编制",
        )
    workshop_e = w.entity(
        "万全作坊", "机构", "军器所编制明确辖万全作坊。",
        quotation=staff,
    )
    workshop_t = tp(
        w, workshop_e, "北宋元丰新制",
        "军器所所属作坊，服役兵匠三千七百人",
        i, staff, "官办兵工场", "建立万全作坊北宋节点。",
        "编制",
    )
    rel(
        w, reform, workshop_t, "上下级机构", i, staff,
        "万全作坊隶制造御前军器所。", "编制",
    )
    w.commit()


def refine_military_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    tid = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        f"专条细化{title}职掌。", None,
        event=event, category="军器所办事机构",
    )
    chain_all(w, eid, [tid], f"确认{title}现有完整时间链。")
    w.commit()


def military_clerk(i, title, event, category="军器所吏人"):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义军器所吏职{title}。",
                   quotation=main)
    tid = tp(
        w, eid, "宋代（具体年月未载）", event,
        i, main, category, f"建立{title}宋代未详年月节点。",
    )
    office_e = fe(w, "制造御前军器所", "机构")
    rel(
        w, ft(w, office_e, "北宋元丰新制"), tid, "编制隶属",
        i, main, f"{title}隶制造御前军器所。",
        staff_type="吏",
    )
    w.commit()


def entry1283():
    i = 1283
    main = Q(i, F[i]["text"])
    staff = field(i, "编制")
    alias = field(i, "简称")
    w = W(i)
    eid = fe(w, "万全作坊", "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        "专条明确万全作坊为军器所所属官办兵工场。", None,
        event="官办兵工场，四指挥，服役兵匠三千七百人",
        category="官办兵工场",
    )
    cite(w, "Timepoints", north, i, staff, "补证北宋四指挥与兵匠额。", "编制")
    south = tp(
        w, eid, "南宋绍兴末",
        "服役兵匠减为五百人，另招工匠二千人",
        i, staff, "官办兵工场", "建立万全作坊绍兴末编制变化节点。",
        "编制", chain="none",
    )
    cite(
        w, "Timepoints", north, i, alias,
        "简称‘万全’仅作称谓证据。", "简称", note="纯简称",
    )
    chain_all(w, eid, [north, south], "连接万全作坊北宋与绍兴末节点。")
    office_e = fe(w, "制造御前军器所", "机构")
    rel(
        w, ft(w, office_e, "南宋绍兴十五年"), south, "上下级机构",
        i, main, "南宋绍兴末万全作坊仍隶制造御前军器所。",
    )
    w.commit()


def entry1284():
    i = 1284
    main = Q(i, F[i]["text"])
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "制造御前军器局", "机构", "本条直接定义制造御前军器局。",
        quotation=main,
    )
    start = tp(
        w, eid, "南宋绍兴七年正月一日",
        "始置，集中诸路州军工匠制造原由地方分造的兵器",
        i, origin, "临时军器制造机构", "建立制造御前军器局始置节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证集中工匠制造兵器职掌。", "职掌")
    end = tp(
        w, eid, "南宋绍兴七年十一月",
        "罢置，事务归制造御前军器所",
        i, origin, "临时军器制造机构", "建立制造御前军器局罢归节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", start, i, staff, "补证官属与吏额。", "编制")
    cite(
        w, "Timepoints", start, i, alias,
        "简称‘军器局’仅作称谓证据。", "简称", note="纯简称",
    )
    chain_all(w, eid, [start, end], "连接制造御前军器局始置与罢归节点。")
    work_e = fe(w, "工部", "机构")
    privy_e = fe(w, "枢密院", "机构")
    rel(
        w, ft(w, work_e, "南宋绍兴五年"), start, "上下级机构",
        i, main, "制造御前军器局隶工部。",
    )
    rel(
        w, ft(w, privy_e, "南宋绍兴七年"), start, "上下级机构",
        i, main, "制造御前军器局隶枢密院。",
    )
    for title, event in (
        ("制造御前军器局提辖官", "提辖军器局事务"),
        ("制造御前军器局监造官", "监督军器局制造"),
        ("制造御前军器局受给官", "办理军器局受给"),
        ("制造御前军器局监门官", "监督军器局门户"),
    ):
        post_e = w.entity(
            title, "官职", f"军器局编制明确设置{title}。",
            quotation=staff,
        )
        post_t = tp(
            w, post_e, "南宋绍兴七年", event,
            i, staff, "军器局官属", f"建立{title}节点。",
            "编制",
        )
        rel(
            w, start, post_t, "编制隶属", i, staff,
            f"制造御前军器局设置{title}。", "编制", staff_type="官",
        )
    office_e = fe(w, "制造御前军器所", "机构")
    return_t = tp(
        w, office_e, "南宋绍兴七年十一月",
        "制造御前军器局罢置，人员事务归还本所",
        i, origin, "中央军器制造机构",
        "建立制造御前军器所绍兴七年接收军器局节点。",
        "职源与沿革", chain="none",
    )
    ordered_times = (
        "北宋元丰新制",
        "宋代元丰以后（具体年月未载）",
        "南宋建炎初",
        "南宋绍兴三年四月九日",
        "南宋绍兴七年十一月",
        "南宋绍兴十五年",
        "南宋隆兴初",
    )
    chain_all(
        w, office_e, [ft(w, office_e, time) for time in ordered_times],
        "插入绍兴七年军器局罢归节点并重建军器所完整时间链。",
    )
    rel(
        w, end, return_t, "前后演变", i, origin,
        "绍兴七年十一月制造御前军器局罢归制造御前军器所。",
        "职源与沿革",
    )
    w.commit()


def prebuild_secretariat_post(w, office_t, i, staff, title, event, quota):
    eid = w.entity(
        title, "官职", f"秘书省总条编制明确设置{title}。",
        quotation=staff,
    )
    tid = tp(
        w, eid, "北宋元丰五年五月", event,
        i, staff, "秘书省官属", f"建立{title}元丰节点。",
        "编制", chain="none",
    )
    existing = [
        row[0] for row in w.conn.execute(
            "select id from Timepoints where entity_id=? and id<>? order by id",
            (eid, tid),
        )
    ]
    if len(existing) == 1:
        existing_time = w.conn.execute(
            "select time from Timepoints where id=?", (existing[0],)
        ).fetchone()[0]
        if existing_time == "北宋元祐以后至南宋":
            chain_all(
                w, eid, [tid] + existing,
                f"连接{title}元丰节点与既有后续馆职节点。",
            )
    rel(
        w, office_t, tid, "编制隶属", i, staff,
        f"元丰秘书省置{title}{quota}人。", "编制",
        staff_quota=quota, staff_type="官",
    )
    return eid, tid


def prebuild_secretariat_unit(w, office_t, i, staff, title, event, time):
    eid = w.entity(
        title, "机构", f"秘书省总条编制明确设置{title}。",
        quotation=staff,
    )
    tid = tp(
        w, eid, time, event, i, staff, "秘书省所属机构",
        f"建立{title}{time}节点。", "编制", chain="none",
    )
    rel(
        w, office_t, tid, "上下级机构", i, staff,
        f"{title}隶秘书省。", "编制",
    )
    return eid, tid


def entry1285():
    i = 1285
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "秘书省", "机构")
    jin = tp(
        w, eid, "西晋元康二年", "已有秘书省之名",
        i, history, "中央文馆机构", "建立秘书省西晋名源节点。",
        "职源与沿革", chain="none",
    )
    song = tp(
        w, eid, "宋前期",
        "沿置，职事主要归三馆秘阁，仅掌一般祭祀祝文撰写",
        i, duty, "中央文馆机构", "建立秘书省宋前期节点。",
        "职掌", chain="none",
    )
    reform = refine(
        w, ft_any(w, eid, "北宋元丰五年", "北宋元丰五年五月"), i, history,
        "专条给出秘书省振职的精确月份。", "职源与沿革",
        time="北宋元丰五年五月",
        event="三馆秘阁职事并入，秘书省始振其职",
        category="中央文馆机构",
    )
    cite(w, "Timepoints", reform, i, duty, "补证图籍、国史、天文与祝辞职掌。", "职掌")
    zhenghe = tp(
        w, eid, "北宋政和六年", "增置道教案",
        i, staff, "中央文馆机构", "建立秘书省政和六年增案节点。",
        "编制", chain="none",
    )
    xuanhe = tp(
        w, eid, "北宋宣和三年十一月", "立定官员十八员",
        i, staff, "中央文馆机构", "建立秘书省宣和三年定额节点。",
        "编制", chain="none",
    )
    jianyan1 = ft(w, eid, "南宋建炎元年五月")
    cite(
        w, "Timepoints", jianyan1, i, history,
        "本条补证建炎三年罢置之前秘书省仍沿置。", "职源与沿革",
    )
    jianyan3 = tp(
        w, eid, "南宋建炎三年四月十三日", "罢置",
        i, history, "中央文馆机构", "建立秘书省建炎三年罢置节点。",
        "职源与沿革", chain="none",
    )
    shaoxing1 = tp(
        w, eid, "南宋绍兴元年二月十九日", "复置，初定馆职九人",
        i, history, "中央文馆机构", "建立秘书省绍兴元年复置节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", shaoxing1, i, staff, "补证绍兴复置初期九人编制。", "编制")
    shaoxing5 = tp(
        w, eid, "南宋绍兴五年八月三日",
        "仿唐十八学士制扩馆职，总计二十一人",
        i, staff, "中央文馆机构", "建立秘书省绍兴五年扩编节点。",
        "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴二年闰十一月三日",
        "著作郎至正字不立定额",
        i, staff, "中央文馆机构", "建立秘书省隆兴二年不立额节点。",
        "编制", chain="none",
    )
    shaoxi = tp(
        w, eid, "南宋绍熙以后",
        "馆职有阙时召试二员，监、少监、丞外多止除二员",
        i, staff, "中央文馆机构", "建立秘书省绍熙以后减员节点。",
        "编制", chain="none",
    )
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与别名仅作称谓证据。",
        "简称与别名", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证秘书省为官署。")
    chain_all(
        w, eid,
        [
            jin, song, reform, zhenghe, xuanhe, jianyan1, jianyan3,
            shaoxing1, shaoxing5, longxing, shaoxi,
        ],
        "重建秘书省西晋名源至南宋绍熙完整时间链。",
    )
    chongwen_e = fe(w, "崇文院", "机构")
    rel(
        w, ft(w, chongwen_e, "北宋元丰五年"), reform, "前后演变",
        i, history, "元丰五年崇文院改为秘书省，三馆秘阁职事并入。",
        "职源与沿革",
    )

    for title, event, quota in (
        ("秘书省监", "秘书省长官", 1),
        ("秘书省少监", "秘书省副长官", 1),
        ("秘书省丞", "参领秘书省事", 1),
        ("著作郎", "掌修史与祝辞撰写", 1),
        ("秘书郎", "秘书省馆职", 2),
        ("著作佐郎", "掌修史与祝辞撰写", 2),
        ("校书郎", "校勘典籍", 4),
        ("正字", "校正典籍文字", 2),
    ):
        prebuild_secretariat_post(w, reform, i, staff, title, event, quota)

    case_specs = (
        ("秘书省国史案", "北宋元丰五年五月", "掌国史事务", reform),
        ("秘书省太史案", "北宋元丰五年五月", "掌太史事务", reform),
        ("秘书省经籍案", "北宋元丰五年五月", "掌经籍事务", reform),
        ("秘书省知杂案", "北宋元丰五年五月", "掌本省杂务", reform),
        ("秘书省道教案", "北宋政和六年", "掌道教事务", zhenghe),
        ("秘书省祝版案", "南宋绍兴元年二月十九日", "掌祭祀祝版事务", shaoxing1),
    )
    case_nodes = {}
    for title, time, event, office_t in case_specs:
        unit_e, unit_t = prebuild_secretariat_unit(
            w, office_t, i, staff, title, event, time,
        )
        case_nodes[(title, time)] = (unit_e, unit_t)
    for title, event in (
        ("秘书省太史案", "掌太史事务"),
        ("秘书省经籍案", "掌经籍事务"),
        ("秘书省知杂案", "掌本省杂务"),
    ):
        unit_e = fe(w, title, "机构")
        south = tp(
            w, unit_e, "南宋绍兴元年二月十九日", event,
            i, staff, "秘书省所属机构", f"建立{title}绍兴复置节点。",
            "编制", chain="none",
        )
        north = case_nodes[(title, "北宋元丰五年五月")][1]
        chain_all(w, unit_e, [north, south], f"连接{title}元丰与绍兴节点。")
        rel(
            w, shaoxing1, south, "上下级机构", i, staff,
            f"绍兴复置秘书省时设{title}。", "编制",
        )
    for title in ("太史局",):
        unit_e = w.entity(
            title, "机构", "秘书省总条明确辖太史局。",
            quotation=staff,
        )
        north = tp(
            w, unit_e, "北宋元丰五年五月", "隶秘书省",
            i, staff, "秘书省所属机构", "建立太史局元丰节点。",
            "编制", chain="none",
        )
        south = tp(
            w, unit_e, "南宋绍兴元年二月十九日", "绍兴复置后仍隶秘书省",
            i, staff, "秘书省所属机构", "建立太史局绍兴节点。",
            "编制", chain="none",
        )
        chain_all(w, unit_e, [north, south], "连接太史局元丰与绍兴节点。")
        rel(w, reform, north, "上下级机构", i, staff, "元丰秘书省辖太史局。", "编制")
        rel(w, shaoxing1, south, "上下级机构", i, staff, "绍兴秘书省辖太史局。", "编制")
    for title, event in (
        ("文德殿钟鼓院", "隶秘书省"),
        ("测验浑仪刻漏所", "隶秘书省"),
    ):
        unit_e = w.entity(
            title, "机构", f"秘书省绍兴编制明确辖{title}。",
            quotation=staff,
        )
        unit_t = tp(
            w, unit_e, "南宋绍兴元年以后", event,
            i, staff, "秘书省所属机构", f"建立{title}南宋节点。",
            "编制",
        )
        rel(
            w, shaoxing1, unit_t, "上下级机构", i, staff,
            f"南宋秘书省辖{title}。", "编制",
        )
    w.commit()


def entry1286():
    i = 1286
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "秘书省监", "官职")
    han = tp(
        w, eid, "东汉延熹二年", "秘书监始置",
        i, history, "秘书省长官", "建立秘书省监东汉职源节点。",
        "职源与沿革", chain="none",
    )
    song = tp(
        w, eid, "宋前期",
        "无职事，为文臣迁转官阶；特令供职则以他官兼",
        i, duty, "文臣迁转官阶", "建立秘书省监宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从三品",
    )
    cite(w, "Timepoints", song, i, rank, "补证宋初从三品及序阶。", "品位")
    reform = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, duty,
        "专条细化秘书省监元丰职掌。", "职掌",
        event="秘书省长官，掌经籍、国史、实录、天文历数与祭祀文",
        category="秘书省长官", grade="正四品",
    )
    cite(w, "Timepoints", reform, i, rank, "补证元丰后正四品。", "品位")
    cite(w, "Timepoints", reform, i, staff, "补证编制一人。", "编制")
    abolish = tp(
        w, eid, "南宋建炎三年四月十三日", "随秘书省罢置",
        i, history, "秘书省长官", "建立秘书省监建炎罢置节点。",
        "职源与沿革", chain="none",
    )
    restore = tp(
        w, eid, "南宋绍兴元年二月十六日",
        "复置，监与少监通常只置一人",
        i, history, "秘书省长官", "建立秘书省监绍兴复置节点。",
        "职源与沿革", chain="none", attr_grade="正四品",
    )
    cite(w, "Timepoints", restore, i, staff, "补证南宋监、少监不并置。", "编制")
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与别名仅作称谓证据。",
        "简称与别名", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证宋前为阶官、元丰后为职事官。")
    chain_all(
        w, eid, [han, song, reform, abolish, restore],
        "连接秘书省监东汉职源至南宋绍兴完整时间链。",
    )
    office_e = fe(w, "秘书省", "机构")
    rel(
        w, ft(w, office_e, "宋前期"), song, "编制隶属", i, history,
        "宋前期秘书省监或由判秘阁官兼。", "职源与沿革",
        staff_quota=1, staff_type="官",
    )
    rel(
        w, ft(w, office_e, "北宋元丰五年五月"), reform, "编制隶属",
        i, staff, "元丰秘书省置监一人。", "编制",
        staff_quota=1, staff_type="官",
    )
    rel(
        w, ft(w, office_e, "南宋绍兴元年二月十九日"), restore,
        "编制隶属", i, staff, "南宋秘书省监与少监通常只置一人。",
        "编制", staff_quota=1, staff_type="官（监、少监不并置）",
    )
    w.commit()


def entry1288():
    i = 1288
    main = Q(i, F[i]["text"])
    total_staff = field(1285, "编制")
    w = W(i)
    eid = w.entity(
        "判秘书省事", "官职", "本条直接定义宋前期判秘书省事差遣。",
        quotation=main,
    )
    tid = tp(
        w, eid, "宋前期",
        "两省五品以上官兼秘书监者称判秘书省事，掌常祭祝词",
        i, main, "秘书省差遣", "建立判秘书省事宋前期节点。",
    )
    office_e = fe(w, "秘书省", "机构")
    rel(
        w, ft(w, office_e, "宋前期"), tid, "编制隶属",
        1285, total_staff, "宋前期秘书省置判省事一人。",
        "编制", staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1289():
    i = 1289
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "提举秘书省", "官职", "本条直接定义提举秘书省差遣。",
        quotation=main,
    )
    zhenghe = tp(
        w, eid, "北宋政和七年五月四日",
        "始置，侍从官以上领秘书省事者称提举",
        i, main, "秘书省差遣", "建立提举秘书省政和始置节点。",
        chain="none",
    )
    shaoxing = tp(
        w, eid, "南宋绍兴间", "曾除二人",
        i, main, "秘书省差遣", "建立提举秘书省绍兴节点。",
        chain="none",
    )
    baoyou = tp(
        w, eid, "南宋宝祐间", "曾除一人",
        i, main, "秘书省差遣", "建立提举秘书省宝祐节点。",
        chain="none",
    )
    xianchun = tp(
        w, eid, "南宋咸淳间", "曾除一人",
        i, main, "秘书省差遣", "建立提举秘书省咸淳节点。",
        chain="none",
    )
    chain_all(
        w, eid, [zhenghe, shaoxing, baoyou, xianchun],
        "连接提举秘书省政和至咸淳节点。",
    )
    office_e = fe(w, "秘书省", "机构")
    rel(
        w, ft(w, office_e, "北宋政和六年"), zhenghe, "编制隶属",
        i, main, "政和七年始置提举秘书省。",
        staff_type="官",
    )
    rel(
        w, ft(w, office_e, "南宋绍兴五年八月三日"), shaoxing,
        "编制隶属", i, main, "南宋绍兴间秘书省曾除提举二人。",
        staff_quota=2, staff_type="官",
    )
    rel(
        w, ft(w, office_e, "南宋绍熙以后"), baoyou,
        "编制隶属", i, main, "南宋宝祐间曾除提举秘书省一人。",
        staff_quota=1, staff_type="官",
    )
    rel(
        w, ft(w, office_e, "南宋绍熙以后"), xianchun,
        "编制隶属", i, main, "南宋咸淳间曾除提举秘书省一人。",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1290():
    i = 1290
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "提纲史事", "官职", "本条直接定义提纲史事差遣。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋（具体年月未载）",
        "由带殿学士职名的提举秘书省官兼，提领本朝修史",
        i, main, "修史差遣", "建立提纲史事南宋未详年月节点。",
    )
    office_e = fe(w, "秘书省", "机构")
    rel(
        w, ft(w, office_e, "南宋绍兴元年二月十九日"), tid,
        "编制隶属", i, main,
        "《馆阁续录》所载提纲史事由提举秘书省官兼。",
        staff_type="官",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1271, 1291)] == [
        "水部司员外郎", "主管尚书省工部、刑部架阁文字",
        "制造御前军器所", "军器所行移内案", "军器所军器案",
        "军器所事务案", "干办司手分", "监造下人吏", "监门下人吏",
        "造帐司", "复算司", "库经司", "万全作坊",
        "制造御前军器局", "秘书省", "秘书省监", "书省",
        "判秘书省事", "提举秘书省", "提纲史事",
    ]
    assert F[1287]["fields"].get("__status__") == "placeholder"
    entry1271()
    entry1272()
    entry1273()
    refine_military_case(
        1274, "军器所行移内案",
        "掌军器制造所需材料计划、采办及相关报表",
    )
    refine_military_case(
        1275, "军器所军器案",
        "点查人匠、招补缺额及办理人吏出职转补",
    )
    refine_military_case(
        1276, "军器所事务案",
        "审批诸作坊申请各种材料",
    )
    military_clerk(
        1277, "干办司手分",
        "监视检查军器所大门官物交收及物料、军器收发",
    )
    military_clerk(
        1278, "监造下人吏",
        "隶军器所监造官，拟草本所往来文书",
    )
    military_clerk(
        1279, "监门下人吏",
        "隶军器所监门官，检查官物出入并搜检人匠",
    )
    military_clerk(1280, "造帐司", "隶制造御前军器所，专掌记帐")
    military_clerk(1281, "复算司", "隶制造御前军器所，覆核帐目")
    military_clerk(
        1282, "库经司",
        "掌物料库、木炭场、金成库每日收支结押与抄报",
    )
    entry1283()
    entry1284()
    entry1285()
    entry1286()
    entry1288()
    entry1289()
    entry1290()


if __name__ == "__main__":
    main()
