#!/usr/bin/env python3
"""提取 chapter2t4 第851–870条：尚书省左右司、郎官与省吏。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(851, 871)}
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine
relation_id = x.relation_id
set_rel_attrs = x.b.set_rel_attrs
mark_citation_conflict = x.b.mark_citation_conflict
current_chain = x.current_chain
move_after = x.move_after


def repair_stale_right_remonstrance_citation():
    """修复早期 OCR 旧字残留，并把本次修改追溯到实际出处。"""
    correct = (
        "谏议大夫始置于后汉（《后汉书·百官志》）。"
        "唐德宗贞元四年（787）始分左、右，右谏议大夫隶中书省"
        "（《职源撮要》）。"
    )
    source = x.b.load(795)
    assert source["title"] == "右谏议大夫" and source["page"] == "189"
    assert correct in source["fields"]["职源"]
    w = x.b.EntryWriter(x.b.ENTRY_DB, "右谏议大夫", "189")
    row = w.conn.execute(
        "select quotation from Citations where id=4494"
    ).fetchone()
    assert row, 4494
    if row[0] != correct:
        assert row[0].startswith("谭议大夫始置于后汉")
        w.conn.execute(
            "update Citations set quotation=? where id=4494", (correct,)
        )
        w._br(
            "Citations",
            4494,
            "将早期OCR旧字“谭议大夫”恢复为当前辞典原文“谏议大夫”；"
            "本次修改按实际出处右谏议大夫第189页留痕。",
        )
    w.commit()


def entry851_853_core():
    i = 851
    origin = Q(
        i,
        "唐贞观元年（627）始分左司、右司，各置郎官",
        "职源",
    )
    duty = Q(
        i,
        "掌受、付六部之事，而纠举文书的违失、稽滞，分治省事。"
        "左司掌治尚书省吏房、户房、礼房、奏钞房、班簿房。"
        "与右司通治开拆房、制敕房、御史房、催驱房、封桩房、知杂房、印房。",
        "职掌",
    )
    staff = Q(
        i,
        "左司郎中一人、左司员外郎一人；吏额：手分二人、书奏二人",
        "编制",
    )
    w = W(i)
    left_e = w.entity(
        "尚书省左司", "机构", "据专条建立尚书省左司。",
        quotation=Q(i, "官司名。"),
    )
    left_tang = tp(
        w, left_e, "唐贞观元年", "始与右司分置，各置郎官",
        i, origin, "尚书省办事机构", "建左司唐代始置节点。",
        "职源", chain="none",
    )
    left_song = tp(
        w, left_e, "宋代（未载具体年月）",
        "分治尚书省吏、户、礼等房，并与右司通治诸房",
        i, duty, "尚书省办事机构", "建宋代左司职掌节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", left_song, i, staff,
         "专条补证左司官吏编制。", "编制")
    left_order = [left_tang, left_song]
    left_yf = w.find_timepoint(left_e, "北宋元丰新制")
    if left_yf is not None:
        left_order.append(left_yf)
    chain_all(w, left_e, left_order,
              "连接尚书省左司唐代始置、宋代沿置及既有元丰节点。")
    w.commit()

    i = 852
    origin = Q(
        i,
        "唐贞观元年（627）始分左、右司，各置郎官",
        "职源",
    )
    duty = Q(
        i,
        "掌受、付尚书省六部文书，而纠察其文书的违失、稽滞。"
        "右司分治尚书省兵房、刑房、工房、案钞房文书，"
        "与左司通治开拆房、制敕房、御史房、催驱房、封桩房、知杂房、印房。"
        "此外，右司掌纠察御史台及刑部刑狱",
        "职掌",
    )
    staff = Q(
        i,
        "右司郎中一人，右司员外郎各一人。吏额：手分二人。书奏二人",
        "编制",
    )
    w = W(i)
    right_e = w.entity(
        "尚书省右司", "机构", "据专条建立尚书省右司。",
        quotation=Q(i, "官司名。"),
    )
    right_tang = tp(
        w, right_e, "唐贞观元年", "始与左司分置，各置郎官",
        i, origin, "尚书省办事机构", "建右司唐代始置节点。",
        "职源", chain="none",
    )
    right_song = tp(
        w, right_e, "宋代（未载具体年月）",
        "分治尚书省兵、刑、工等房，并与左司通治诸房、纠察刑狱",
        i, duty, "尚书省办事机构", "建宋代右司职掌节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", right_song, i, staff,
         "专条补证右司官吏编制。", "编制")
    right_order = [right_tang, right_song]
    right_yf = w.find_timepoint(right_e, "北宋元丰新制")
    if right_yf is not None:
        right_order.append(right_yf)
    chain_all(w, right_e, right_order,
              "连接尚书省右司唐代始置、宋代沿置及既有元丰节点。")
    w.commit()

    i = 853
    main = Q(i, "尚书省左司、尚书省右司连称。")
    history = Q(
        i,
        "隋朝时尚书省都司分置左、右司郎官。宋沿用。",
        "简称与别名",
    )
    w = W(i)
    left_song = ft(w, fe(w, "尚书省左司", "机构"), "宋代（未载具体年月）")
    right_song = ft(w, fe(w, "尚书省右司", "机构"), "宋代（未载具体年月）")
    cite(w, "Timepoints", left_song, i, history,
         "别称字段仍包含左司宋代沿置事实。", "简称与别名")
    cite(w, "Timepoints", right_song, i, history,
         "别称字段仍包含右司宋代沿置事实。", "简称与别名")
    group_e = w.entity(
        "尚书省左、右司", "机构",
        "本条明确为尚书省左司、右司的同时代连称。",
        quotation=main,
    )
    group_t = tp(
        w, group_e, "宋代（未载具体年月）",
        "尚书省左司、尚书省右司连称",
        i, main, "机构统称", "建左右司连称节点。",
    )
    rel(w, group_t, left_song, "统称与实例", i, main,
        "尚书省左司是尚书省左、右司的实例。")
    rel(w, group_t, right_song, "统称与实例", i, main,
        "尚书省右司是尚书省左、右司的实例。")
    parent = ft(w, fe(w, "尚书省", "机构"), "宋前期")
    rel(w, parent, left_song, "上下级机构", i, history,
        "宋代尚书省沿用左司。", "简称与别名")
    rel(w, parent, right_song, "上下级机构", i, history,
        "宋代尚书省沿用右司。", "简称与别名")
    w.commit()


def entry851_852_rooms_and_staff():
    specs = (
        (
            851, "尚书省左司",
            (
                "尚书省吏房", "尚书省户房", "尚书省礼房",
                "尚书省奏钞班簿房", "尚书省开拆房", "尚书省催驱房",
            ),
            (
                ("尚书省左司郎中", "北宋元丰新制", 1),
                ("尚书省左司员外郎", "北宋元丰新制", 1),
            ),
        ),
        (
            852, "尚书省右司",
            (
                "尚书省兵房", "尚书省刑房", "尚书省工房",
                "尚书省案钞刑房", "尚书省开拆房", "尚书省催驱房",
            ),
            (
                ("尚书省右司郎中", "北宋元丰新制", 1),
                ("尚书省右司员外郎", "北宋元丰新制", 1),
            ),
        ),
    )
    for i, office_title, rooms, officers in specs:
        duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
        staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
        w = W(i)
        office_t = ft(w, fe(w, office_title, "机构"), "北宋元丰新制")
        for room_title in rooms:
            room_t = ft(w, fe(w, room_title, "机构"), "北宋元丰新制")
            rel(w, office_t, room_t, "上下级机构", i, duty,
                f"{office_title}分治或与另一司通治{room_title}。", "职掌")
        for officer_title, officer_time, quota in officers:
            rel(
                w, office_t, ft(w, fe(w, officer_title, "官职"), officer_time),
                "编制隶属", i, staff,
                f"{office_title}置{officer_title}{quota}人。", "编制",
                staff_quota=quota, staff_type="官",
            )
        w.commit()


def entry854_857():
    i = 854
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "尚书都司御史房", "机构",
        "据专条建立尚书省左右司御史房。",
        quotation=main,
    )
    tid = tp(
        w, eid, "北宋元丰六年正月",
        "创置，纠察御史台六察御史并记录年终考评",
        i, main, "尚书省左右司办事部门",
        "建御史房元丰六年创置节点。",
    )
    for parent_title in ("尚书省左司", "尚书省右司"):
        rel(
            w, ft(w, fe(w, parent_title, "机构"), "北宋元丰新制"),
            tid, "上下级机构", i, main,
            f"尚书都司御史房为{parent_title}共同办事部门。",
        )
    w.commit()

    i = 855
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "尚书都司茶盐案", "机构",
        "据专条建立尚书省左右司茶盐案。",
        quotation=main,
    )
    tid = tp(
        w, eid, "未知",
        "掌榷货都茶场所上盐、茶、香、矾等文字，置守当官二人",
        i, main, "尚书省左右司办事部门",
        "原文未载时间，复用新实体首个承载节点记录明确职掌。",
    )
    for parent_title in ("尚书省左司", "尚书省右司"):
        rel(
            w, ft(w, fe(w, parent_title, "机构"), "宋代（未载具体年月）"),
            tid, "上下级机构", i, main,
            f"尚书都司茶盐案为{parent_title}办事部门。",
        )
    rel(
        w, tid,
        ft(w, fe(w, "守当官", "官职"), "北宋元丰新制（尚书省）"),
        "编制隶属", i, main, "尚书都司茶盐案置守当官二人。",
        staff_quota=2, staff_type="吏",
    )
    w.commit()

    for i, title, parent_title in (
        (856, "尚书省左司知杂案", "尚书省左司"),
        (857, "尚书省右司知杂案", "尚书省右司"),
    ):
        main = Q(i, x.b.F[i]["text"])
        w = W(i)
        eid = w.entity(title, "机构", f"据专条建立{title}。", quotation=main)
        tid = tp(
            w, eid, "未知", "办理本司具体事务，置书令史一人",
            i, main, "尚书省左右司办事部门",
            f"原文未载时间，记录{title}职掌与吏额。",
        )
        rel(
            w, ft(w, fe(w, parent_title, "机构"), "宋代（未载具体年月）"),
            tid, "上下级机构", i, main, f"{title}隶{parent_title}。",
        )
        rel(
            w, tid,
            ft(w, fe(w, "书令史", "官职"), "北宋元丰新制（尚书省）"),
            "编制隶属", i, main, f"{title}置书令史一人。",
            staff_quota=1, staff_type="吏",
        )
        w.commit()


def entry858():
    i = 858
    origin = Q(
        i,
        "隋朝置尚书省左司郎，唐贞观元年（627）始置尚书省左司郎中"
        "（《新唐书·百官志》1《尚书省》）。宋沿置。",
        "职源",
    )
    early = Q(
        i,
        "① 宋前期无职事，为文臣寄禄官阶。"
        "元丰新制，其阶易为朝议大夫",
        "职掌",
    )
    reform = Q(
        i,
        "② 元丰新制，为职事官，领本司事。与右司郎中通治本司开拆、"
        "制敕、御史、催驱、封桩、知杂、印房。此外，分纠尚书省吏房、"
        "户房、礼房、奏钞房、班簿房及枢密院机速房文字",
        "职掌",
    )
    grade_early = Q(
        i, "① 宋前期依唐制，唐时官品为从五品上", "品位"
    )
    grade_reform = Q(i, "② 元丰新制正六品", "品位")
    quota = Q(i, "元丰新制定以一人为额", "编制")
    w = W(i)
    eid = fe(w, "尚书省左司郎中", "官职")
    sui = tp(
        w, eid, "隋", "置尚书省左司郎",
        i, origin, "官名源流", "建左司郎中隋代源流节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐贞观元年", "始置尚书省左司郎中",
        i, origin, "官名源流", "建左司郎中唐代始置节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事，为文臣寄禄官阶",
        i, early, "阶官", "建左司郎中宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade_early,
         "专条补证宋前期品位。", "品位")
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制"), i, reform,
        "专条细化元丰左司郎中职掌与品位。", "职掌",
        event="职事官，领左司并与右司郎中通治诸房、分纠相关房务",
        category="职事官", grade="正六品",
    )
    cite(w, "Timepoints", yuanfeng, i, grade_reform,
         "专条补证元丰正六品。", "品位")
    cite(w, "Timepoints", yuanfeng, i, quota,
         "专条补证元丰一人为额。", "编制")
    role_order = [sui, tang, song, yuanfeng]
    role_south = w.find_timepoint(eid, "南宋建炎四年九月十七日")
    if role_south is not None:
        role_order.append(role_south)
    chain_all(w, eid, role_order,
              "连接尚书省左司郎中隋唐源流、宋前期阶官与元丰职事节点。")
    office_e = fe(w, "尚书省左司", "机构")
    office_yf = tp(
        w, office_e, "北宋元丰新制",
        "由左司郎中领本司事，分治并通治尚书省诸房",
        i, reform, "尚书省办事机构",
        "左司郎中专条明确元丰新制领本司事，补建左司同时点。",
        "职掌", chain="none",
    )
    chain_all(
        w, office_e,
        [
            ft(w, office_e, "唐贞观元年"),
            ft(w, office_e, "宋代（未载具体年月）"),
            office_yf,
        ],
        "把元丰新制节点接入尚书省左司时间链。",
    )
    w.commit()


def entry859():
    i = 859
    early = Q(
        i,
        "① 宋前期无职事，为文臣迁转官阶。"
        "元丰新制，其阶易为朝议大夫",
        "职掌",
    )
    reform = Q(
        i,
        "② 元丰新制，为职事官，与左司郎中通治本司开拆、制敕、"
        "御史、催驱、封桩、知杂、印房等诸房事；并分纠尚书省兵房、"
        "刑房、工房、三省枢密院赏功房文字；御史台刑狱与诸州所上奏案，"
        "也归右司郎中纠察与看详。",
        "职掌",
    )
    quota = Q(i, "元丰新制一人", "编制")
    w = W(i)
    eid = fe(w, "尚书省右司郎中", "官职")
    song = tp(
        w, eid, "宋前期", "无职事，为文臣迁转官阶",
        i, early, "阶官", "建右司郎中宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从五品上",
    )
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制"), i, reform,
        "专条细化元丰右司郎中职掌；品位按本条明确参左司郎中。",
        "职掌",
        event="职事官，与左司郎中通治诸房并分纠兵刑工等房务、纠察刑狱",
        category="职事官", grade="正六品",
    )
    cite(w, "Timepoints", yuanfeng, i, quota,
         "专条补证元丰一人为额。", "编制")
    role_order = [song, yuanfeng]
    role_south = w.find_timepoint(eid, "南宋建炎四年九月十七日")
    if role_south is not None:
        role_order.append(role_south)
    chain_all(w, eid, role_order,
              "连接尚书省右司郎中宋前期阶官与元丰职事节点。")
    office_e = fe(w, "尚书省右司", "机构")
    office_yf = tp(
        w, office_e, "北宋元丰新制",
        "由右司郎中掌本司事，分纠兵、刑、工等房务并纠察刑狱",
        i, reform, "尚书省办事机构",
        "右司郎中专条明确元丰新制掌本司事，补建右司同时点。",
        "职掌", chain="none",
    )
    chain_all(
        w, office_e,
        [
            ft(w, office_e, "唐贞观元年"),
            ft(w, office_e, "宋代（未载具体年月）"),
            office_yf,
        ],
        "把元丰新制节点接入尚书省右司时间链。",
    )
    w.commit()


def entry860():
    i = 860
    origin = Q(
        i,
        "唐永昌元年(689)始置尚书省左、右司员外郎"
        "（《通典·职官》4《尚书令》）。宋沿置。",
        "职源",
    )
    duty = Q(
        i,
        "①宋前期无职事。②元丰新制为职事官。佐左司郎中掌本司事，"
        "即“掌受付六曹之事，而举正文书之稽失，分治司事”",
        "职掌",
    )
    grade_early = Q(
        i, "① 宋前期，沿唐制，唐时为从六品上", "品位"
    )
    grade_reform = Q(i, "② 元丰新制定为从六品", "品位")
    quota = Q(i, "元丰新制以一人为额", "编制")
    w = W(i)
    eid = fe(w, "尚书省左司员外郎", "官职")
    tang = tp(
        w, eid, "唐永昌元年", "始置尚书省左、右司员外郎",
        i, origin, "官名源流", "建左司员外郎唐代始置节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事",
        i, duty, "阶官", "建左司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade_early,
         "专条补证宋前期品位。", "品位")
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化元丰左司员外郎职掌与品位。", "职掌",
        event="职事官，佐左司郎中掌本司事并纠正文书稽失",
        category="职事官", grade="从六品",
    )
    cite(w, "Timepoints", yuanfeng, i, grade_reform,
         "专条补证元丰从六品。", "品位")
    cite(w, "Timepoints", yuanfeng, i, quota,
         "专条补证元丰一人为额。", "编制")
    role_order = [tang, song, yuanfeng]
    role_south = w.find_timepoint(eid, "南宋建炎四年九月十七日")
    if role_south is not None:
        role_order.append(role_south)
    chain_all(w, eid, role_order,
              "连接左司员外郎唐代始置、宋前期与元丰节点。")
    w.commit()


def entry861():
    i = 861
    duty = Q(
        i,
        "① 宋前期无职事。② 元丰新制为职事官，佐右司郎中掌本司事，"
        "即“掌受付六曹之事，而举正文书之稽失，分治司事。”",
        "职掌",
    )
    quota = Q(i, "元丰新制以一人为额", "编制")
    w = W(i)
    eid = fe(w, "尚书省右司员外郎", "官职")
    song = tp(
        w, eid, "宋前期", "无职事",
        i, duty, "阶官", "建右司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化元丰右司员外郎职掌；品位按本条所参左司员外郎。",
        "职掌",
        event="职事官，佐右司郎中掌本司事并纠正文书稽失",
        category="职事官", grade="从六品",
    )
    cite(w, "Timepoints", yuanfeng, i, quota,
         "专条补证元丰一人为额。", "编制")
    role_order = [song, yuanfeng]
    role_south = w.find_timepoint(eid, "南宋建炎四年九月十七日")
    if role_south is not None:
        role_order.append(role_south)
    chain_all(w, eid, role_order,
              "连接右司员外郎宋前期阶官与元丰职事节点。")
    w.commit()


def entry862():
    i = 862
    main = Q(
        i,
        "尚书省左、右司郎中与员外郎总称。"
        "《宋会要·职官》4之23：“（建炎）四年九月十七日，"
        "左、右司郎官旧系四员，今依旧。”"
        "《元丰官志》：“左、右司郎中，左、右司员外郎，左、右各一人，共四人。”",
    )
    w = W(i)
    group_e = w.entity(
        "尚书左、右司郎官", "官职",
        "本条明确为左右司郎中、员外郎总称。",
        quotation=main,
    )
    group_yf = tp(
        w, group_e, "北宋元丰新制",
        "左、右司郎中及员外郎各一人，共四人",
        i, main, "职官统称", "建元丰左右司郎官统称节点。",
        chain="none",
    )
    group_south = tp(
        w, group_e, "南宋建炎四年九月十七日",
        "恢复旧制四员",
        i, main, "职官统称", "建建炎恢复四员节点。",
        chain="none",
    )
    chain_all(w, group_e, [group_yf, group_south],
              "连接左右司郎官元丰四员与建炎恢复节点。")
    for title in (
        "尚书省左司郎中", "尚书省右司郎中",
        "尚书省左司员外郎", "尚书省右司员外郎",
    ):
        role_e = fe(w, title, "官职")
        role_yf = ft(w, role_e, "北宋元丰新制")
        existing_chain = current_chain(w, role_e)
        role_south = tp(
            w, role_e, "南宋建炎四年九月十七日",
            "依旧设置一员", i, main, "职事官",
            f"建{title}建炎恢复节点。", chain="none",
        )
        ordered = (
            existing_chain
            if role_south in existing_chain
            else [*existing_chain, role_south]
        )
        chain_all(
            w, role_e, ordered,
            f"把{title}建炎恢复节点接到既有时间链尾。",
        )
        rel(w, group_yf, role_yf, "统称与实例", i, main,
            f"{title}是元丰左右司郎官实例。")
        rel(w, group_south, role_south, "统称与实例", i, main,
            f"{title}是建炎恢复的左右司郎官实例。")
    w.commit()


def entry863():
    i = 863
    history = Q(
        i,
        "北宋徽宗大观二年六月二十九日置，大观三年五月二十八日罢"
        "（《十朝纲要》卷17、《宋会要·职官》4之13）。"
        "南宋绍兴初曾置",
        "职源与沿革",
    )
    duty = Q(i, "在尚书省实习政事，以广论议", "职掌")
    grade = Q(i, "以选人充", "品位")
    w = W(i)
    eid = w.entity(
        "尚书省习学公事", "官职",
        "本条明确为尚书省职事官名。",
        quotation=Q(i, "职事官名。"),
    )
    start = tp(
        w, eid, "北宋大观二年六月二十九日",
        "置，在尚书省实习政事、以广论议",
        i, history, "职事官", "建大观始置节点。",
        "职源与沿革", chain="none", attr_officer_type="选人",
    )
    cite(w, "Timepoints", start, i, duty, "补证习学公事职掌。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证以选人充。", "品位")
    stop = tp(
        w, eid, "北宋大观三年五月二十八日", "罢置",
        i, history, "职事官", "建大观三年罢置节点。",
        "职源与沿革", chain="none",
    )
    south = tp(
        w, eid, "南宋绍兴初", "复置",
        i, history, "职事官", "建南宋绍兴初复置节点。",
        "职源与沿革", chain="none", attr_officer_type="选人",
    )
    chain_all(w, eid, [start, stop, south],
              "连接习学公事北宋置罢与南宋复置节点。")
    institute_e = fe(w, "尚书省", "机构")
    institute_south = tp(
        w, institute_e, "南宋绍兴初", "复置尚书省习学公事",
        i, history, "中央政务机构",
        "习学公事复置事实同时证明尚书省南宋制度状态。",
        "职源与沿革", chain="none",
    )
    chain_all(
        w, institute_e,
        [
            ft(w, institute_e, "南朝梁"),
            ft(w, institute_e, "宋前期"),
            ft(w, institute_e, "北宋元丰新制"),
            institute_south,
        ],
        "把南宋绍兴初节点接入尚书省时间链。",
    )
    rel(
        w, ft(w, institute_e, "北宋元丰新制"), start,
        "编制隶属", i, history, "大观二年尚书省置习学公事。",
        "职源与沿革", staff_type="官",
    )
    rel(
        w, institute_south, south, "编制隶属", i, history,
        "南宋绍兴初尚书省复置习学公事。",
        "职源与沿革", staff_type="官",
    )
    w.commit()


def entry864():
    i = 864
    origin = Q(
        i,
        "晋朝有尚书都令史（《通典·职官》4《历代都事·令史》）。"
        "隋朝尚书省六部尚书各置都事，为正八品官"
        "（《隋书·百官志》下）。宋朝元丰五年复三省之制后始置。",
        "职源",
    )
    duty = Q(
        i,
        "头名都事掌点检尚书省诸房进入、发付文字。其余都事分房上呈文字",
        "职掌",
    )
    quota_yf = Q(i, "①元丰新制三人", "编制")
    quota_late = Q(i, "②北宋后期及南宋七人", "编制")
    grade = Q(i, "正八品", "品位")
    w = W(i)
    eid = fe(w, "尚书省都事", "官职")
    jin = tp(
        w, eid, "晋", "有尚书都令史",
        i, origin, "官名源流", "建都事晋代源流节点。",
        "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "尚书省六部尚书各置都事，为正八品官",
        i, origin, "吏职", "建都事隋代节点。",
        "职源", chain="none", attr_grade="正八品",
    )
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制（尚书省）"), i, duty,
        "专条细化元丰尚书省都事职掌、编制与品位。", "职掌",
        event="始置三人；头名点检诸房进出文字，其余分房上呈文字",
        category="堂吏", grade="正八品",
    )
    cite(w, "Timepoints", yuanfeng, i, origin,
         "专条补证元丰五年复三省后始置。", "职源")
    cite(w, "Timepoints", yuanfeng, i, quota_yf,
         "专条补证元丰三人。", "编制")
    cite(w, "Timepoints", yuanfeng, i, grade,
         "专条补证正八品。", "品位")
    late = tp(
        w, eid, "北宋后期", "增为七人",
        i, quota_late, "堂吏", "建北宋后期增额节点。",
        "编制", chain="none", attr_grade="正八品",
    )
    south = refine(
        w, ft(w, eid, "南宋绍兴年间"), i, quota_late,
        "专条补证南宋尚书省都事七人。", "编制",
        event="三省堂后官，尚书省都事七人",
        category="堂吏", grade="正八品",
    )
    chain_all(w, eid, [jin, sui, yuanfeng, late, south],
              "连接尚书省都事晋隋源流、元丰始置及北宋后期南宋增额节点。")
    rid = relation_id(
        w, "尚书省", "尚书省都事", "编制隶属",
        "北宋元丰新制", "北宋元丰新制（尚书省）",
    )
    assert rid
    set_rel_attrs(w, rid, 3, "吏", "专条明载元丰尚书省都事三人。")
    cite(w, "Relationships", rid, i, quota_yf,
         "专条补证元丰尚书省都事三人。", "编制")
    rel(
        w, ft(w, fe(w, "尚书省", "机构"), "南宋绍兴初"), south,
        "编制隶属", i, quota_late, "南宋尚书省都事七人。",
        "编制", staff_quota=7, staff_type="吏",
    )
    w.commit()


def entry865_869():
    specs = (
        (865, "主事", "北宋元丰新制（尚书省）", 6, "从八品", False),
        (866, "令史", "北宋元丰新制（尚书省）", 14, "从八品", False),
        (867, "书令史", "北宋元丰新制（尚书省）", 31, "从八品", True),
        (868, "守当官", "北宋元丰新制（尚书省）", 16, None, True),
        (869, "守阙守当官", "北宋绍圣三年（尚书省）", 150, None, False),
    )
    events = {
        865: "隶尚书省，六人，分押本省六房文字",
        866: "隶尚书省，十四人，监印、点检开拆房并分掌诸房事务",
        867: "隶尚书省，掌诸房行遣文字，须两试及格，专条记三十一人",
        868: "隶尚书省，专条记十六人；二人用印，其余掌簿书并通差行遣文字",
        869: "北宋后期非正员守当官一百五十人，掌诸房抄写文字",
    }
    for i, title, time, quota, grade, conflict in specs:
        main = Q(i, x.b.F[i]["text"])
        w = W(i)
        eid = fe(w, title, "官职")
        tid = ft(w, eid, time)
        if conflict:
            cite(
                w, "Timepoints", tid, i, main,
                f"专条补证{title}隶尚书省，但员额与尚书省总条冲突。",
                note=(
                    "本专条记三十一人，尚书省总条记三十五人。"
                    if i == 867
                    else "本专条记十六人，尚书省总条记六人。"
                ),
                conflict_flag=1,
            )
        else:
            refine(
                w, tid, i, main, f"专条细化尚书省{title}职掌与编制。",
                event=events[i], category="吏职", grade=grade,
            )
        rid = relation_id(
            w, "尚书省", title, "编制隶属",
            "北宋元丰新制" if i != 869 else "北宋元丰新制",
            time,
        )
        assert rid, (i, title, time)
        if conflict:
            cite(
                w, "Relationships", rid, i, main,
                f"保留{title}员额冲突，未覆盖总条既有关系数值。",
                note=(
                    "本专条记三十一人，尚书省总条记三十五人。"
                    if i == 867
                    else "本专条记十六人，尚书省总条记六人。"
                ),
                conflict_flag=1,
            )
        else:
            set_rel_attrs(w, rid, quota, "吏", f"{title}专条明载员额。")
            cite(w, "Relationships", rid, i, main,
                 f"专条补证{title}隶尚书省且员额为{quota}人。")
        w.commit()


def entry870():
    i = 870
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "法司", "官职",
        "本条明确法司为隶尚书省的吏名。",
        quotation=main,
    )
    tid = tp(
        w, eid, "未知", "隶尚书省，外差行遣制敕库房文字",
        i, main, "吏职",
        "原文未载时间，使用首个未知时间节点承载明确职掌。",
    )
    rel(
        w, ft(w, fe(w, "尚书省", "机构"), "宋前期"), tid,
        "编制隶属", i, main, "法司隶尚书省。",
        staff_type="吏",
    )
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(851, 871)] == [
        "尚书省左司",
        "尚书省右司",
        "尚书省左、右司",
        "尚书都司御史房",
        "尚书都司茶盐案",
        "尚书省左司知杂案",
        "尚书省右司知杂案",
        "尚书省左司郎中",
        "尚书省右司郎中",
        "尚书省左司员外郎",
        "尚书省右司员外郎",
        "尚书左、右司郎官",
        "尚书省习学公事",
        "尚书省都事",
        "主事",
        "令史",
        "书令史",
        "守当官",
        "守阙守当官",
        "法司",
    ]
    repair_stale_right_remonstrance_citation()
    entry851_853_core()
    entry858()
    entry859()
    entry860()
    entry861()
    entry851_852_rooms_and_staff()
    entry854_857()
    entry862()
    entry863()
    entry864()
    entry865_869()
    entry870()


if __name__ == "__main__":
    main()
