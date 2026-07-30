#!/usr/bin/env python3
"""提取 chapter2t4 第1551–1570条：史局、书局、史官与殿中省系统。"""
import extract_2t4_1531_1550 as x

base = x.base
base.F = {i: base.load(i) for i in range(1551, 1571)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def alias(w, tid, i):
    for key in ("简称", "简称与别名", "别称", "别名"):
        if key in F[i]["fields"]:
            cite(w, "Timepoints", tid, i, field(i, key),
                 f"{F[i]['title']}称谓仅作名称证据。", key,
                 note="纯简称或别名")


def palace(w, time="北宋崇宁二年二月十二日"):
    return ft(w, fe(w, "殿中省", "机构"), time)


def six_bureaus(w, time="北宋崇宁二年二月"):
    return ft(w, fe(w, "殿中省六尚局", "机构"), time)


def entry1551():
    i = 1551
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("史局", "机构", "本条定义宋代修史机构通称。",
                   quotation=main)
    total = tp(w, eid, "宋代", "史馆、编修院、修史院、国史院、国史日历所、实录院等修史机构通称",
               i, main, "修史机构统称", "建立史局统称节点。")
    instances = (
        ("史馆", "宋初"),
        ("编修院", "北宋天圣九年五月二十九日"),
        ("修史院", "北宋雍熙四年九月"),
        ("国史院", "北宋元祐五年十一月十三日"),
        ("国史日历所", "南宋绍兴十年四月二十八日"),
        ("实录院", "北宋咸平元年正月"),
    )
    for title, time in instances:
        rel(w, total, ft(w, fe(w, title, "机构"), time),
            "统称与实例", i, main, f"{title}是史局实例。")
    w.commit()


def entry1552():
    i = 1552
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("书局", "机构", "本条定义修史及其他修书机构泛称。",
                   quotation=main)
    total = tp(w, eid, "宋代", "修史、修敕令格式、九域图志及类书等修书机构泛称",
               i, main, "修书机构统称", "建立书局泛称节点。")
    for title, time in (
        ("史局", "宋代"),
        ("详定一司敕令所", "北宋徽宗大观时"),
        ("定《九域图志》所", "北宋崇宁间"),
    ):
        rel(w, total, ft(w, fe(w, title, "机构"), time),
            "统称与实例", i, main, f"{title}属于书局泛称。")
    w.commit()


def entry1553():
    i = 1553
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("史官", "官职", "本条定义参与各类史书撰修文官的通称。",
                   quotation=main)
    total = tp(w, eid, "宋代", "参与国史、实录、日历、会要、起居注等撰修职事文官通称",
               i, main, "修史官统称", "建立史官统称节点。",
               attr_officer_type="文官统称")
    alias(w, total, i)
    for title, time in (
        ("著作郎", "北宋元丰五年五月"),
        ("著作佐郎", "北宋元丰五年五月"),
        ("起居郎", "宋初"),
        ("起居舍人", "宋前期"),
        ("国史院编修", "宋代国史院时期"),
        ("实录院修撰", "南宋实录院时期"),
        ("日历修书官", "北宋前期"),
        ("编修会要所编修", "宋代会要所时期"),
    ):
        rel(w, total, ft(w, fe(w, title, "官职"), time),
            "统称与实例", i, main, f"{title}属于史官通称。")
    w.commit()


def entry1554():
    i = 1554
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    eid = w.entity("殿中省", "机构", "本条直接定义殿中省。",
                   quotation=main)
    specs = [
        ("隋大业三年", "殿内监改为殿内省", "前代职源"),
        ("唐武德元年", "殿内省改为殿中省，殿中省之名始此", "前代职源"),
        ("宋前期", "名存实废，仅办理大礼仪仗法物", "中央供奉机构"),
        ("北宋元丰新制", "正殿中省之名，但禁中无建省之所，实际未建", "中央供奉机构"),
        ("北宋崇宁二年二月十二日", "重建殿中省，总领六尚局，供奉皇帝衣食住行医药", "中央供奉机构"),
        ("北宋靖康元年正月四日", "罢殿中省", "中央供奉机构"),
    ]
    nodes = [
        tp(w, eid, time, event, i, history, category,
           f"建立殿中省{time}节点。", "职源与沿革", chain="none")
        for time, event, category in specs
    ]
    cite(w, "Timepoints", nodes[2], i, duty, "补证宋前期殿中省职掌。", "职掌")
    cite(w, "Timepoints", nodes[3], i, duty, "补证元丰正名而未实建。", "职掌")
    cite(w, "Timepoints", nodes[4], i, duty, "补证崇宁重建后职掌。", "职掌")
    cite(w, "Timepoints", nodes[2], i, staff, "补证宋前期殿中省编制。", "编制")
    cite(w, "Timepoints", nodes[4], i, staff, "补证崇宁重建后编制与所属。", "编制")
    alias(w, nodes[4], i)
    chain_all(w, eid, nodes, "连接殿中省隋唐职源、宋前期、元丰、崇宁与靖康节点。")
    w.commit()


def entry1555():
    i = 1555
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("判殿中省事", "官职", "本条直接定义判殿中省事。",
                   quotation=main)
    tid = tp(w, eid, "宋初", "无职事朝官差充，办理大礼时扇伞等仪仗法物",
             i, main, "殿中省差遣", "建立判殿中省事宋初节点。",
             attr_officer_type="朝官差遣")
    alias(w, tid, i)
    rel(w, palace(w, "宋前期"), tid, "编制隶属", i, main,
        "宋前期以朝官一员判殿中省事。", staff_quota=1,
        staff_type="朝官差遣")
    w.commit()


def palace_official(i, title, specs, category, officer_type, *, grade=None):
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}。", quotation=main)
    nodes = [
        tp(w, eid, time, event, i, history,
           "前代职源" if time.startswith(("魏", "隋", "唐")) else category,
           f"建立{title}{time}节点。", "职源与沿革",
           attr_officer_type=officer_type, chain="none")
        for time, event in specs
    ]
    song_index = next(
        n for n, (time, _) in enumerate(specs)
        if time.startswith("宋前期") or time.startswith("北宋崇宁")
    )
    cite(w, "Timepoints", nodes[song_index], i, duty,
         f"补证{title}宋代职掌。", "职掌")
    if "品位" in F[i]["fields"]:
        cite(w, "Timepoints", nodes[song_index], i, field(i, "品位"),
             f"补证{title}品位。", "品位")
    if "编制" in F[i]["fields"]:
        cite(w, "Timepoints", nodes[song_index], i, field(i, "编制"),
             f"补证{title}编制。", "编制")
    alias(w, nodes[song_index], i)
    chain_all(w, eid, nodes, f"连接{title}职源及宋代制度节点。")
    for node, (time, _) in zip(nodes, specs):
        if time.startswith("宋前期"):
            rel(w, palace(w, "宋前期"), node, "编制隶属", i, main,
                f"{title}属宋前期殿中省。", staff_quota=1,
                staff_type=officer_type)
        elif time.startswith("北宋崇宁"):
            rel(w, palace(w), node, "编制隶属", i, main,
                f"崇宁重建后{title}为殿中省官。", staff_quota=1,
                staff_type=officer_type)
    w.commit()


def entry1558():
    i = 1558
    main, history, duty = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌")
    w = W(i)
    eid = w.entity("殿中省丞", "官职", "本条直接定义殿中省丞。",
                   quotation=main)
    specs = [
        ("隋大业三年", "始置殿内省丞"),
        ("唐武德元年", "随省名改为殿中省丞"),
        ("宋前期", "文臣寄禄官阶，无职事"),
        ("北宋元丰五年五月", "寄禄官殿中丞易为奉议郎；殿中丞列职事官但未授人"),
        ("北宋崇宁二年二月十二日", "重建殿中省后参领省事"),
        ("北宋靖康元年", "随殿中省罢"),
    ]
    nodes = [
        tp(w, eid, time, event, i, history,
           "前代职源" if idx < 2 else "殿中省官",
           f"建立殿中省丞{time}节点。", "职源与沿革",
           attr_officer_type="阶官或职事官", chain="none")
        for idx, (time, event) in enumerate(specs)
    ]
    for idx in (2, 3, 4):
        cite(w, "Timepoints", nodes[idx], i, duty, "补证殿中省丞职掌变化。", "职掌")
    cite(w, "Timepoints", nodes[2], i, field(i, "品位"), "补证殿中省丞品位。", "品位")
    cite(w, "Timepoints", nodes[4], i, field(i, "编制"), "补证崇宁后编制一人。", "编制")
    alias(w, nodes[4], i)
    chain_all(w, eid, nodes, "连接殿中省丞隋唐职源、寄禄官、元丰与崇宁节点。")
    rel(w, palace(w, "宋前期"), nodes[2], "编制隶属", i, main,
        "宋前期殿中省丞为空名寄禄官。", staff_type="阶官")
    rel(w, palace(w), nodes[4], "编制隶属", i, main,
        "崇宁重建后殿中省丞参领省事。", staff_quota=1, staff_type="职事官")
    w.commit()


def entry1559():
    i = 1559
    main, history, duty = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌")
    w = W(i)
    eid = w.entity("殿中省主簿", "官职", "本条直接定义殿中省主簿。",
                   quotation=main)
    origin = tp(w, eid, "战国秦昭王时", "已有主簿官名",
                i, history, "前代职源", "建立主簿官名职源节点。",
                "职源与沿革", attr_officer_type="古官", chain="none")
    start = tp(w, eid, "北宋崇宁二年二月十二日",
               "始置殿中省主簿，管理考核簿册文书并通管杂务",
               i, history, "殿中省官", "建立殿中省主簿始置节点。",
               "职源与沿革", attr_officer_type="职事官", chain="none")
    end = tp(w, eid, "北宋靖康元年", "随殿中省罢",
             i, history, "殿中省官", "建立殿中省主簿罢置节点。",
             "职源与沿革", attr_officer_type="职事官", chain="none")
    cite(w, "Timepoints", start, i, duty, "补证殿中省主簿职掌。", "职掌")
    cite(w, "Timepoints", start, i, field(i, "品位"), "补证殿中省主簿序位。", "品位")
    cite(w, "Timepoints", start, i, field(i, "编制"), "补证殿中省主簿编制一人。", "编制")
    alias(w, start, i)
    chain_all(w, eid, [origin, start, end], "连接主簿职源、殿中省始置与罢置节点。")
    rel(w, palace(w), start, "编制隶属", i, main,
        "殿中省主簿隶殿中省。", staff_quota=1, staff_type="职事官")
    w.commit()


def entry1560():
    i = 1560
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("殿中监少丞簿", "官职", "本条定义殿中省四官连称。",
                   quotation=main)
    total = tp(w, eid, "北宋崇宁二年以后", "殿中省监、少监、丞、主簿连称",
               i, main, "殿中省官连称", "建立殿中监少丞簿连称节点。",
               attr_officer_type="官职连称")
    for title in ("殿中省监", "殿中省少监", "殿中省丞", "殿中省主簿"):
        rel(w, total, ft(w, fe(w, title, "官职"), "北宋崇宁二年二月十二日"),
            "统称与实例", i, main, f"{title}是殿中监少丞簿连称实例。")
    w.commit()


def append_clerk_node(i, title, time, event, existing_order, *, alias_key=False):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "官职")
    tid = tp(w, eid, time, event, i, main, "殿中省吏",
             f"建立{title}殿中省节点。", attr_officer_type="吏", chain="none")
    if alias_key:
        alias(w, tid, i)
    ordered = [ft(w, eid, old_time) for old_time in existing_order]
    insert_at = next((idx for idx, old_time in enumerate(existing_order)
                      if old_time.startswith("南宋")), len(ordered))
    ordered.insert(insert_at, tid)
    chain_all(w, eid, ordered, f"把{title}殿中省节点接入既有完整时间链。")
    rel(w, palace(w), tid, "编制隶属", i, main,
        f"崇宁后殿中省置{title}。", staff_type="吏")
    w.commit()


def entry1563():
    i = 1563
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "贴司", "官职")
    old = ft(w, eid, "未知")
    tid = tp(w, eid, "北宋崇宁二年以后（殿中省）",
             "充书吏抄写文书，从他司谙练行遣、谨畏的人吏中选抽",
             i, main, "殿中省吏", "建立贴司殿中省节点。",
             attr_officer_type="吏", chain="none")
    alias(w, tid, i)
    chain_all(w, eid, [old, tid], "连接贴司既有节点与殿中省节点。")
    rel(w, palace(w), tid, "编制隶属", i, main,
        "殿中省置贴司。", staff_quota=12, staff_type="吏")
    w.commit()


def entry1564():
    i = 1564
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("殿中省六尚局", "机构", "本条定义殿中省六尚局总名。",
                   quotation=main)
    early = tp(w, eid, "宋前期", "尚食、尚药、尚衣、尚舍、尚乘、尚辇六局总名，空存其名",
               i, main, "殿中省所属机构统称", "建立宋前期六尚局节点。", chain="none")
    yuanyou = tp(w, eid, "北宋元祐时", "尚食、尚药、尚酝、尚衣、尚舍、尚辇六局总名",
                 i, main, "殿中省所属机构统称", "建立元祐六尚局节点。", chain="none")
    chongning = tp(w, eid, "北宋崇宁二年二月", "重建殿中省，改尚乘为尚酝，六尚局名称固定",
                   i, main, "殿中省所属机构统称", "建立崇宁六尚局节点。", chain="none")
    alias(w, chongning, i)
    chain_all(w, eid, [early, yuanyou, chongning], "连接六尚局宋前期、元祐与崇宁节点。")
    rel(w, palace(w), chongning, "上下级机构", i, main,
        "崇宁重建殿中省总领六尚局。")
    for title in ("尚食局", "尚药局", "尚酝局", "尚衣局", "尚舍局", "尚辇局"):
        child_eid = w.entity(title, "机构", f"六尚局条明确列举{title}。",
                             quotation=main)
        child_tid = tp(w, child_eid, "北宋崇宁二年二月",
                       "殿中省六尚局之一",
                       i, main, "殿中省所属机构", f"建立{title}崇宁节点。")
        rel(w, chongning, child_tid, "统称与实例", i, main,
            f"{title}是崇宁六尚局实例。")
    w.commit()


def entry1565():
    i = 1565
    main, history = Q(i, F[i]["text"]), field(i, "职源与沿革")
    w = W(i)
    eid = w.entity("殿中省提举六尚局", "官职", "本条直接定义提举六尚局差遣。",
                   quotation=main)
    start = tp(w, eid, "北宋崇宁二年二月十二日", "始设，以入内内侍省官充，总领六尚局事",
               i, history, "六尚局差遣", "建立提举六尚局始置节点。",
               "职源与沿革", attr_officer_type="内侍差遣", chain="none")
    end = tp(w, eid, "北宋靖康元年", "罢提举六尚局",
             i, history, "六尚局差遣", "建立提举六尚局罢置节点。",
             "职源与沿革", attr_officer_type="内侍差遣", chain="none")
    cite(w, "Timepoints", start, i, field(i, "职掌"), "补证总领六尚局职掌。", "职掌")
    cite(w, "Timepoints", start, i, field(i, "品位"), "补证提举六尚局序位。", "品位")
    cite(w, "Timepoints", start, i, field(i, "编制"), "补证编制一人。", "编制")
    alias(w, start, i)
    chain_all(w, eid, [start, end], "连接提举六尚局始置与罢置节点。")
    rel(w, six_bureaus(w), start, "编制隶属", i, main,
        "提举六尚局总领六尚局事。", staff_quota=1, staff_type="内侍差遣")
    w.commit()


def entry1566():
    i = 1566
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("殿中省提举六尚局所", "机构",
                   "本条定义提举六尚局官治事厅。", quotation=main)
    tid = tp(w, eid, "北宋崇宁二年以后", "提举六尚局官治事厅",
             i, main, "殿中省治事机构", "建立提举六尚局所节点。")
    alias(w, tid, i)
    rel(w, palace(w), tid, "上下级机构", i, main,
        "殿中省提举六尚局所隶殿中省。")
    w.commit()


def entry1567():
    i = 1567
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("管勾殿中省六尚局", "官职", "本条直接定义管勾六尚局差遣。",
                   quotation=main)
    tid = tp(w, eid, "北宋崇宁二年二月", "始置，由内侍官充，在内庭监理六尚局供奉事",
             i, main, "六尚局差遣", "建立管勾六尚局始置节点。",
             attr_officer_type="内侍差遣")
    alias(w, tid, i)
    rel(w, six_bureaus(w), tid, "编制隶属", i, main,
        "管勾殿中省六尚局监理六尚供奉。", staff_quota=1,
        staff_type="内侍差遣")
    w.commit()


def entry1568():
    i = 1568
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    eid = fe(w, "尚食局", "机构")
    origin = tp(w, eid, "北齐", "始有尚食局之名",
                i, history, "前代职源", "建立尚食局北齐职源节点。",
                "职源与沿革", chain="none")
    early = tp(w, eid, "宋前期", "空存其名，职事归御厨",
               i, history, "殿中省所属机构", "建立尚食局宋前期节点。",
               "职源与沿革", chain="none")
    reform = tp(w, eid, "北宋元丰新制", "拟恢复尚食局职事",
                i, history, "殿中省所属机构", "建立尚食局元丰节点。",
                "职源与沿革", chain="none")
    formal = refine(w, ft(w, eid, "北宋崇宁二年二月"), i, history,
                    "专条补证尚食局崇宁正式建置与职掌。",
                    event="正式建置，供御膳羞及品尝事",
                    category="殿中省所属机构")
    end = tp(w, eid, "北宋靖康元年", "罢尚食局",
             i, history, "殿中省所属机构", "建立尚食局靖康罢置节点。",
             "职源与沿革", chain="none")
    cite(w, "Timepoints", early, i, duty, "补证宋前期尚食局职掌归御厨。", "职掌")
    cite(w, "Timepoints", formal, i, duty, "补证崇宁后尚食局职掌。", "职掌")
    cite(w, "Timepoints", formal, i, staff, "补证尚食局官吏与所属太官局。", "编制")
    alias(w, formal, i)
    chain_all(w, eid, [origin, early, reform, formal, end],
              "连接尚食局北齐职源、宋前期、元丰、崇宁与靖康节点。")
    rel(w, palace(w, "宋前期"), early, "上下级机构", i, main,
        "宋前期尚食局空隶殿中省。")
    rel(w, palace(w), formal, "上下级机构", i, main,
        "崇宁正式建置尚食局，隶殿中省。")
    w.commit()


def entry1569():
    i = 1569
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    eid = w.entity("太官局", "机构", "本条直接定义殿中省尚食局太官局。",
                   quotation=main)
    origin = tp(w, eid, "北齐", "始置光禄寺太官署",
                i, history, "前代职源", "建立太官局北齐职源节点。",
                "职源与沿革", chain="none")
    early = tp(w, eid, "宋初", "太官署事隶御厨，沿设太官",
               i, history, "供御膳机构", "建立太官局宋初节点。",
               "职源与沿革", chain="none")
    formal = tp(w, eid, "北宋崇宁二年二月十二日",
                "于尚食局设太官局，御厨并入，供御膳",
                i, history, "尚食局所属机构", "建立太官局崇宁节点。",
                "职源与沿革", chain="none")
    cite(w, "Timepoints", formal, i, duty, "补证太官局职掌。", "职掌")
    cite(w, "Timepoints", formal, i, staff, "补证太官局官吏编制。", "编制")
    chain_all(w, eid, [origin, early, formal], "连接太官署职源、宋初与崇宁太官局节点。")
    rel(w, ft(w, fe(w, "尚食局", "机构"), "北宋崇宁二年二月"), formal,
        "上下级机构", i, main, "太官局隶殿中省尚食局。")
    w.commit()


def entry1570():
    i = 1570
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("太官令", "官职", "本条直接定义太官局太官令。",
                   quotation=main)
    start = tp(w, eid, "北宋崇宁二年二月", "太官局置五人，掌供御膳及择膳工",
               i, main, "太官局职事官", "建立太官令崇宁节点。",
               attr_officer_type="职事官", attr_grade="正九品", chain="none")
    end = tp(w, eid, "北宋靖康元年正月四日", "罢太官令",
             i, main, "太官局职事官", "建立太官令靖康罢置节点。",
             attr_officer_type="职事官", attr_grade="正九品", chain="none")
    alias(w, start, i)
    chain_all(w, eid, [start, end], "连接太官令崇宁始置与靖康罢置节点。")
    rel(w, ft(w, fe(w, "太官局", "机构"), "北宋崇宁二年二月十二日"), start,
        "编制隶属", i, main, "太官令隶太官局。", staff_quota=5,
        staff_type="职事官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1551, 1571)] == [
        "史局", "书局", "史官", "殿中省", "判殿中省事", "殿中省监",
        "殿中省少监", "殿中省丞", "殿中省主簿", "殿中监少丞簿",
        "令史", "书令史", "贴司", "殿中省六尚局", "殿中省提举六尚局",
        "殿中省提举六尚局所", "管勾殿中省六尚局", "尚食局", "太官局", "太官令",
    ]
    entry1551()
    entry1552()
    entry1553()
    entry1554()
    entry1555()
    palace_official(1556, "殿中省监", [
        ("魏", "始置殿中监"),
        ("唐武德元年", "殿内省监改为殿中省监"),
        ("宋前期", "文臣寄禄官阶，无职事"),
        ("北宋崇宁二年二月十二日", "重建殿中省后总治一省供奉政令"),
        ("北宋靖康元年", "随殿中省罢"),
    ], "殿中省官", "阶官或职事官")
    palace_official(1557, "殿中省少监", [
        ("隋大业三年", "始置殿内少监"),
        ("唐武德元年", "改为殿中省少监"),
        ("宋前期", "存官名而无职掌，罕以除人"),
        ("北宋崇宁二年二月十二日", "重建殿中省后为佐贰官"),
        ("北宋靖康元年", "随殿中省罢"),
    ], "殿中省官", "阶官或职事官")
    entry1558()
    entry1559()
    entry1560()
    append_clerk_node(1561, "令史", "北宋崇宁二年以后（殿中省）",
                      "掌内庭供进文书，从内外官司选谙练行遣、奉事谨畏者充",
                      ["汉至唐", "宋代（枢密院，未载具体年月）",
                       "北宋（登闻检院，未载具体年月）", "北宋（登闻鼓院，未载具体年月）",
                       "北宋元丰新制（门下省）", "北宋元丰新制（中书省）",
                       "北宋元丰新制（尚书省）", "南宋建炎三年（中书后省）", "南宋嘉定五年"])
    append_clerk_node(1562, "书令史", "北宋崇宁二年以后（殿中省）",
                      "掌内庭供进文书，从内外官司抽取谨慎且谙练文书行遣者，位次令史",
                      ["汉至唐", "宋代（枢密院，未载具体年月）", "北宋淳化四年二月",
                       "宋前期（通进司）", "北宋元丰新制（门下省）",
                       "北宋元丰新制（中书省）", "北宋元丰新制（尚书省）",
                       "南宋初（登闻检院）", "南宋（登闻鼓院）", "南宋嘉定五年"])
    entry1563()
    entry1564()
    entry1565()
    entry1566()
    entry1567()
    entry1568()
    entry1569()
    entry1570()


if __name__ == "__main__":
    main()
