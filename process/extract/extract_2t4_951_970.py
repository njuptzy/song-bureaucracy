#!/usr/bin/env python3
"""提取 chapter2t4 第951–970条：讲议诸司与尚书省六部、二十四司统称。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(951, 971)}
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine
current_chain = x.current_chain


DEPARTMENTS = ("吏部", "户部", "礼部", "兵部", "刑部", "工部")
DEPARTMENT_TIMES = {
    "吏部": "北宋",
    "户部": "宋初",
    "礼部": "宋代",
    "兵部": "宋代",
    "刑部": "宋代",
    "工部": "宋代",
}
MINISTERS = tuple(f"{name}尚书" for name in DEPARTMENTS)
ACTING_MINISTERS = tuple(f"权{name}尚书" for name in DEPARTMENTS)
VICE_MINISTERS = tuple(f"{name}侍郎" for name in DEPARTMENTS)
ACTING_VICE_MINISTERS = tuple(f"权{name}侍郎" for name in DEPARTMENTS)

OFFICES = (
    "吏部司", "司勋司", "司封司", "考功司",
    "户部司", "度支司", "金部司", "仓部司",
    "礼部司", "祠部司", "主客司", "膳部司",
    "兵部司", "职方司", "驾部司", "库部司",
    "刑部司", "都官司", "比部司", "司门司",
    "工部司", "屯田司", "虞部司", "水部司",
)

DIRECTORS = (
    "吏部司郎中", "司勋司郎中", "司封司郎中", "考功司郎中",
    "户部司郎中", "度支司郎中", "金部司郎中", "仓部司郎中",
    "礼部郎中", "祠部司郎中", "主客司郎中", "膳部司郎中",
    "兵部司郎中", "职方司郎中", "驾部司郎中", "库部司郎中",
    "刑部司郎中", "都官司郎中", "比部司郎中", "司门司郎中",
    "工部司郎中", "屯田司郎中", "虞部司郎中", "水部司郎中",
)

mark_citation_conflict = x.b.mark_citation_conflict


def department_timepoint(w, title):
    return ft(w, fe(w, title, "机构"), DEPARTMENT_TIMES[title])


def entry951_953():
    for i, title, event in (
        (951, "讲议司商旅检讨文字", "分管讨论商贾活动及商税征收"),
        (952, "讲议司盐泽检讨文字", "分管讨论盐利等事"),
        (953, "讲议司尹牧检讨文字", "分管讨论京师及地方长吏"),
    ):
        main = Q(i, x.b.F[i]["text"])
        aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
        w = W(i)
        eid = w.entity(
            title,
            "官职",
            f"本条直接定义{title}。",
            quotation=main,
        )
        tid = tp(
            w,
            eid,
            "北宋崇宁元年七月一日",
            event,
            i,
            main,
            "讲议司分事检讨官",
            f"按尚书省讲议司始置时间建立{title}节点。",
        )
        cite(
            w,
            "Timepoints",
            tid,
            i,
            aliases,
            "简称字段补证分事检讨官省称；纯简称不另建实体。",
            "简称",
            note="纯简称",
        )
        office_t = ft(
            w,
            fe(w, "尚书省讲议司", "机构"),
            "北宋崇宁元年七月一日",
        )
        rel(
            w,
            office_t,
            tid,
            "编制隶属",
            i,
            main,
            f"原文明确{title}为讲议司内分事检讨官；不另推员额。",
            staff_type="官",
        )
        rel(
            w,
            ft(
                w,
                fe(w, "讲议司检讨文字", "官职"),
                "北宋崇宁元年七月一日",
            ),
            tid,
            "统称与实例",
            i,
            main,
            f"{title}为讲议司检讨文字按七事分工的实例。",
        )
        w.commit()


def entry954():
    i = 954
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "尚书省讲议司检阅文字", "官职")
    refine(
        w,
        ft(w, eid, "北宋崇宁元年七月一日"),
        i,
        main,
        "专条补证讲议司检阅文字的任职来源与职掌。",
        event="由尚书省都事担任，掌点检讲议司文书",
        category="讲议司吏职",
        officer="尚书省都事兼",
    )
    w.commit()


def entry955_core():
    i = 955
    name = Q(i, "临时官署名。")
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "尚书省讲议财利司",
        "机构",
        "本条直接定义尚书省讲议财利司。",
        quotation=name,
    )
    start = tp(
        w,
        eid,
        "北宋宣和六年十一月十三日",
        "始置，讨论省冗员、节浮费、重爵赏等挽救财政危机对策",
        i,
        origin,
        "临时中央财政议政机构",
        "建立尚书省讲议财利司始置节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证讲议财利司职掌。", "职掌")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证讲议司、尚书省讲议司省称及尚书省置司。",
        "简称",
        note="纯简称",
    )
    end = tp(
        w,
        eid,
        "北宋宣和七年",
        "徽宗禅位后不了了之",
        i,
        origin,
        "临时中央财政议政机构",
        "建立次年徽宗禅位后讲议财利司停顿节点。",
        "职源",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接讲议财利司始置及次年停顿节点。")
    rel(
        w,
        ft(w, fe(w, "尚书都省", "机构"), "北宋元丰五年十月十七日"),
        start,
        "上下级机构",
        i,
        aliases,
        "简称引文明示在尚书省设置讲议财利司。",
        "简称",
    )

    for title, quota, category in (
        ("提举尚书省讲议财利司", 4, "兼官"),
        ("讲议财利司详议官", 2, "讲议财利司属官"),
        ("讲议财利司详定官", 2, "讲议财利司属官"),
        ("讲议财利司参详官", 4, "讲议财利司属官"),
    ):
        role_e = w.entity(
            title,
            "官职",
            f"讲议财利司编制字段明列{title}。",
            quotation=staff,
        )
        role_t = tp(
            w,
            role_e,
            "北宋宣和六年十一月十三日",
            f"讲议财利司始置编制，{quota}人",
            i,
            staff,
            category,
            f"建立{title}随讲议财利司始置的编制节点。",
            "编制",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            staff,
            f"讲议财利司编制明示{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type="官",
        )
    w.commit()


def entry956():
    i = 956
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "提举尚书省讲议财利司", "官职")
    initial = refine(
        w,
        ft(w, eid, "北宋宣和六年十一月十三日"),
        i,
        main,
        "专条补证提举讲议财利司由宰执官兼任并总领司事。",
        event="由宰执官兼任，总领讲议财利司事",
        category="兼官",
        officer="宰执官兼",
    )
    later = tp(
        w,
        eid,
        "北宋宣和七年",
        "宰执官任提举，领枢密院蔡攸任同提举",
        i,
        main,
        "兼官",
        "建立专条引文所载宣和七年提举官节点；不据此改写第955条明确的置司日期。",
        chain="none",
        attr_officer_type="宰执官兼",
    )
    mark_citation_conflict(
        w,
        "Timepoints",
        later,
        i,
        main,
        "第955条职源明确讲议财利司置于宣和六年十一月十三日；"
        "本条原文作宣和七年置，保留异文而不改写机构始置日期。",
        "标记第956条宣和七年置司说与第955条始置日期冲突。",
    )
    chain_all(w, eid, [initial, later], "连接提举讲议财利司宣和六年、七年节点。")
    w.commit()


def entry957():
    i = 957
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "尚书省详议司",
        "机构",
        "本条直接定义尚书省详议司。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋靖康元年四月十二日",
        "始置，讨论祖宗旧法",
        i,
        main,
        "临时中央议政机构",
        "建立尚书省详议司始置节点。",
        chain="none",
    )
    end = tp(
        w,
        eid,
        "北宋靖康元年四月二十九日",
        "因臣僚强烈反对而罢",
        i,
        main,
        "临时中央议政机构",
        "建立尚书省详议司罢置节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接尚书省详议司置、罢节点。")
    rel(
        w,
        ft(w, fe(w, "尚书都省", "机构"), "北宋元丰五年十月十七日"),
        start,
        "上下级机构",
        i,
        main,
        "正式名称明确详议司置于尚书省。",
    )
    w.commit()


def entry958():
    i = 958
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "议礼局",
        "机构",
        "本条直接定义议礼局。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋大观元年正月十三日",
        "于尚书省始置，由执政官兼领，修礼书",
        i,
        main,
        "临时修礼机构",
        "建立议礼局始置节点。",
        chain="none",
    )
    book = tp(
        w,
        eid,
        "北宋政和元年",
        "修成《政和五礼新仪》二百二十卷",
        i,
        main,
        "临时修礼机构",
        "建立议礼局修成礼书节点。",
        chain="none",
    )
    stop = tp(
        w,
        eid,
        "北宋政和三年四月",
        "罢局",
        i,
        main,
        "临时修礼机构",
        "建立议礼局罢局节点。",
        chain="none",
    )
    finish = tp(
        w,
        eid,
        "北宋政和三年六月",
        "结局",
        i,
        main,
        "临时修礼机构",
        "建立议礼局结局节点。",
        chain="none",
    )
    chain_all(w, eid, [start, book, stop, finish], "连接议礼局始置、成书、罢局、结局节点。")
    rel(
        w,
        ft(w, fe(w, "尚书都省", "机构"), "北宋元丰五年十月十七日"),
        start,
        "上下级机构",
        i,
        main,
        "原文明确议礼局于尚书省设置。",
    )
    for title in (
        "议礼局详议官",
        "议礼局检讨官",
        "议礼局承受官",
        "议礼局检阅文字官",
        "议礼局杂务官",
    ):
        role_e = w.entity(
            title,
            "官职",
            f"议礼局条明确编制设{title.removeprefix('议礼局')}。",
            quotation=main,
        )
        role_t = tp(
            w,
            role_e,
            "北宋大观元年正月十三日",
            "议礼局始置编制",
            i,
            main,
            "修礼机构属官",
            f"建立{title}随议礼局始置节点。",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            main,
            f"议礼局设{title}；原文未明示员额。",
            staff_type="官",
        )
    w.commit()


def entry959():
    i = 959
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    parent_e = w.entity(
        "编类御笔所",
        "机构",
        "礼制局条明确记载礼制局置于编类御笔所。",
        quotation=main,
    )
    parent_t = tp(
        w,
        parent_e,
        "北宋政和三年七月二十一日",
        "礼制局置于本所",
        i,
        main,
        "御笔编类机构",
        "建立编类御笔所承载礼制局设置关系的节点。",
    )
    eid = w.entity(
        "礼制局",
        "机构",
        "本条直接定义礼制局。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋政和三年七月二十一日",
        "置于编类御笔所，讨论宫室车服器用之度及婚冠丧葬之节",
        i,
        main,
        "临时礼制议政机构",
        "建立礼制局始置节点。",
        chain="none",
    )
    end = tp(
        w,
        eid,
        "北宋宣和二年七月一日",
        "罢局",
        i,
        main,
        "临时礼制议政机构",
        "建立礼制局罢置节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接礼制局始置、罢置节点。")
    rel(w, parent_t, start, "上下级机构", i, main, "礼制局置于编类御笔所。")
    for title in ("礼制局详议官", "礼制局同详议官"):
        role_e = w.entity(
            title,
            "官职",
            f"礼制局条明确设置{title.removeprefix('礼制局')}。",
            quotation=main,
        )
        role_t = tp(
            w,
            role_e,
            "北宋政和三年七月二十一日",
            "礼制局始置编制",
            i,
            main,
            "礼制局属官",
            f"建立{title}随礼制局始置节点。",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            main,
            f"礼制局设{title}；原文未明示员额。",
            staff_type="官",
        )
    w.commit()


def entry960():
    i = 960
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    group_e = w.entity(
        "尚书省六部",
        "机构",
        "本条直接定义尚书省六部统称。",
        quotation=main,
    )
    sui = tp(
        w,
        group_e,
        "隋大业三年",
        "尚书省六部名称与排列次序定型",
        i,
        origin,
        "机构统称",
        "建立尚书省六部隋代定型节点。",
        "职源",
        chain="none",
    )
    song = tp(
        w,
        group_e,
        "宋代",
        "承唐制，统称吏、户、礼、兵、刑、工六部",
        i,
        main,
        "机构统称",
        "建立尚书省六部宋代节点。",
        chain="none",
    )
    cite(
        w,
        "Timepoints",
        song,
        i,
        aliases,
        "全文扫描简称与别名字段；六部、六曹等纯称谓不另建实体。",
        "简称与别名",
        note="纯简称、别名与典故称",
    )
    chain_all(w, group_e, [sui, song], "连接尚书省六部隋代定型、宋代沿用节点。")
    for title in DEPARTMENTS:
        entity_id = w.find_entity(title, "机构")
        if entity_id is None:
            entity_id = w.entity(
                title,
                "机构",
                f"本条明确{title}为尚书省六部之一。",
                quotation=main,
            )
            instance_t = tp(
                w,
                entity_id,
                "宋代",
                "尚书省六部之一",
                i,
                main,
                "中央行政机构",
                f"建立{title}宋代六部实例节点。",
            )
        else:
            # 本条语境明确是“宋承唐制”，连接既有实体的宋代节点；不另造关系承载点。
            instance_t = ft(
                w,
                entity_id,
                DEPARTMENT_TIMES[title],
            )
            cite(
                w,
                "Timepoints",
                instance_t,
                i,
                main,
                f"尚书省六部条补证{title}为六部之一。",
            )
        rel(
            w,
            song,
            instance_t,
            "统称与实例",
            i,
            main,
            f"{title}为尚书省六部实例。",
        )
    w.commit()


def entry961():
    i = 961
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    group_e = w.entity(
        "六部尚书",
        "官职",
        "本条直接定义六部尚书统称。",
        quotation=main,
    )
    sui = tp(
        w,
        group_e,
        "隋",
        "六部所属诸曹尚书始称部尚书",
        i,
        origin,
        "官职统称",
        "建立六部尚书隋代始称节点。",
        "职源",
        chain="none",
    )
    song = tp(
        w,
        group_e,
        "宋代",
        "吏、户、礼、兵、刑、工六部尚书总称",
        i,
        main,
        "官职统称",
        "建立六部尚书宋代节点。",
        chain="none",
    )
    reform = tp(
        w,
        group_e,
        "宋代厘正百司后",
        "任六曹尚书者始实领职事",
        i,
        aliases,
        "六部长官统称",
        "简称与别名字段明示厘正百司后六曹尚书始实领职事。",
        "简称与别名",
        chain="none",
    )
    cite(
        w,
        "Timepoints",
        song,
        i,
        aliases,
        "全文扫描简称与别名字段；六尚书、文昌等纯称谓不另建实体。",
        "简称与别名",
        note="纯简称、别名与典故称",
    )
    chain_all(w, group_e, [sui, song, reform], "连接六部尚书隋代源流、宋代总述及厘正后节点。")
    for department, title in zip(DEPARTMENTS, MINISTERS):
        role_e = w.entity(
            title,
            "官职",
            f"本条明确{title}为六部尚书之一。",
            quotation=main,
        )
        role_t = tp(
            w,
            role_e,
            "宋代",
            "六部尚书之一",
            i,
            main,
            "六部长官",
            f"建立{title}宋代节点。",
        )
        rel(w, song, role_t, "统称与实例", i, main, f"{title}为六部尚书实例。")
        rel(
            w,
            department_timepoint(w, department),
            role_t,
            "编制隶属",
            i,
            main,
            f"{title}为{department}长官；本条未载员额。",
            staff_type="官",
        )
    w.commit()


def entry962():
    i = 962
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    group_e = w.entity(
        "五曹尚书",
        "官职",
        "本条直接定义五曹尚书统称。",
        quotation=main,
    )
    group_t = tp(
        w,
        group_e,
        "宋代",
        "户、礼、兵、刑、工五部尚书总称，均从二品，用以区别正二品吏部尚书",
        i,
        main,
        "官职统称",
        "建立五曹尚书宋代节点。",
        attr_grade="从二品",
    )
    for title in MINISTERS[1:]:
        rel(
            w,
            group_t,
            ft(w, fe(w, title, "官职"), "宋代"),
            "统称与实例",
            i,
            main,
            f"{title}为五曹尚书实例。",
        )
    w.commit()


def entry963():
    i = 963
    main = Q(i, x.b.F[i]["text"])
    history = Q(i, x.b.F[i]["fields"]["职源与沿革"], "职源与沿革")
    grade = Q(i, x.b.F[i]["fields"]["官品"], "官品")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    group_e = w.entity(
        "权六部尚书",
        "官职",
        "本条直接定义权六部尚书统称。",
        quotation=main,
    )
    start = tp(
        w,
        group_e,
        "北宋元祐三年闰十二月二十八日",
        "始置权吏、户、礼、兵、刑、工部尚书",
        i,
        history,
        "权摄官职统称",
        "建立权六部尚书始置节点。",
        "职源与沿革",
        chain="none",
        attr_grade="正三品",
    )
    cite(w, "Timepoints", start, i, grade, "补证权六部尚书正三品。", "官品")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证权尚书、权六曹尚书省称；纯简称不另建实体。",
        "简称与别名",
        note="纯简称",
    )
    stop = tp(
        w,
        group_e,
        "北宋崇宁",
        "罢置",
        i,
        history,
        "权摄官职统称",
        "建立崇宁罢置节点。",
        "职源与沿革",
        chain="none",
    )
    restore = tp(
        w,
        group_e,
        "南宋绍兴八年",
        "复置，此后不废",
        i,
        history,
        "权摄官职统称",
        "建立绍兴八年复置节点。",
        "职源与沿革",
        chain="none",
        attr_grade="正三品",
    )
    chain_all(w, group_e, [start, stop, restore], "连接权六部尚书始置、罢置、复置节点。")
    for department, title in zip(DEPARTMENTS, ACTING_MINISTERS):
        role_e = w.entity(
            title,
            "官职",
            f"本条明确{title}为权六部尚书实例。",
            quotation=main,
        )
        role_start = tp(
            w,
            role_e,
            "北宋元祐三年闰十二月二十八日",
            "权六部尚书之一，始置",
            i,
            history,
            "权摄六部长官",
            f"建立{title}始置节点。",
            "职源与沿革",
            attr_grade="正三品",
        )
        rel(w, start, role_start, "统称与实例", i, main, f"{title}为权六部尚书实例。")
        rel(
            w,
            department_timepoint(w, department),
            role_start,
            "编制隶属",
            i,
            main,
            f"{title}为{department}权摄长官；本条未载员额。",
            staff_type="官",
        )
    w.commit()


def entry964():
    i = 964
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    aliases = Q(i, x.b.F[i]["fields"]["别称"], "别称")
    w = W(i)
    group_e = fe(w, "六部侍郎", "官职")
    sui = tp(
        w,
        group_e,
        "隋大业三年",
        "始设六部侍郎",
        i,
        origin,
        "官职统称",
        "建立六部侍郎隋代始置节点。",
        "职源",
        chain="none",
    )
    pre_reform = refine(
        w,
        ft(w, group_e, "北宋元丰改制前"),
        i,
        main,
        "专条补证六部侍郎为吏、户、礼、兵、刑、工六部侍郎总称。",
        event="吏、户、礼、兵、刑、工六部侍郎总称",
        category="官职统称",
    )
    reform = tp(
        w,
        group_e,
        "北宋元丰官制",
        "由阶官改为职事官，始有职掌",
        i,
        aliases,
        "六部副长官统称",
        "别称字段明示六部侍郎至元丰官制始有职掌。",
        "别称",
        chain="none",
    )
    cite(
        w,
        "Timepoints",
        pre_reform,
        i,
        aliases,
        "全文扫描别称字段；六曹侍郎、文昌贰卿等纯称谓不另建实体。",
        "别称",
        note="纯别称",
    )
    chain_all(
        w,
        group_e,
        [sui, pre_reform, reform],
        "连接六部侍郎隋代始置、元丰前阶官及元丰职事官节点。",
    )
    for department, title in zip(DEPARTMENTS, VICE_MINISTERS):
        role_e = w.entity(
            title,
            "官职",
            f"本条明确{title}为六部侍郎之一。",
            quotation=main,
        )
        role_t = tp(
            w,
            role_e,
            "北宋元丰改制前",
            "六部侍郎之一，贰本部尚书之职",
            i,
            main,
            "六部副长官",
            f"按六部侍郎既有宋代上下文建立{title}节点。",
        )
        rel(w, pre_reform, role_t, "统称与实例", i, main, f"{title}为六部侍郎实例。")
        rel(
            w,
            department_timepoint(w, department),
            role_t,
            "编制隶属",
            i,
            main,
            f"{title}为{department}副长官；本条未载员额。",
            staff_type="官",
        )
    w.commit()


def entry965():
    i = 965
    main = Q(i, x.b.F[i]["text"])
    history = Q(i, x.b.F[i]["fields"]["职源与沿革"], "职源与沿革")
    grade = Q(i, x.b.F[i]["fields"]["官品"], "官品")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    group_e = w.entity(
        "权六部侍郎",
        "官职",
        "本条直接定义权六部侍郎统称。",
        quotation=main,
    )
    start = tp(
        w,
        group_e,
        "北宋元祐二年",
        "始置权吏、户、礼、兵、刑、工部侍郎",
        i,
        history,
        "权摄官职统称",
        "建立权六部侍郎始置节点。",
        "职源与沿革",
        chain="none",
        attr_grade="从四品",
    )
    cite(w, "Timepoints", start, i, grade, "补证权侍郎从四品。", "官品")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证权侍郎、权六曹侍郎省称；纯简称不另建实体。",
        "简称与别名",
        note="纯简称",
    )
    stop = tp(
        w,
        group_e,
        "北宋崇宁初",
        "罢置",
        i,
        history,
        "权摄官职统称",
        "建立崇宁初罢置节点。",
        "职源与沿革",
        chain="none",
    )
    restore = tp(
        w,
        group_e,
        "南宋建炎四年",
        "复置，此后不废",
        i,
        history,
        "权摄官职统称",
        "建立建炎四年复置节点。",
        "职源与沿革",
        chain="none",
        attr_grade="从四品",
    )
    chain_all(w, group_e, [start, stop, restore], "连接权六部侍郎始置、罢置、复置节点。")
    for department, title in zip(DEPARTMENTS, ACTING_VICE_MINISTERS):
        role_e = w.entity(
            title,
            "官职",
            f"本条明确{title}为权六部侍郎实例。",
            quotation=main,
        )
        role_start = tp(
            w,
            role_e,
            "北宋元祐二年",
            "权六部侍郎之一，始置",
            i,
            history,
            "权摄六部副长官",
            f"建立{title}始置节点。",
            "职源与沿革",
            attr_grade="从四品",
        )
        rel(w, start, role_start, "统称与实例", i, main, f"{title}为权六部侍郎实例。")
        rel(
            w,
            department_timepoint(w, department),
            role_start,
            "编制隶属",
            i,
            main,
            f"{title}为{department}权摄副长官；本条未载员额。",
            staff_type="官",
        )
    w.commit()


def entry966():
    i = 966
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    group_e = w.entity(
        "六部长贰",
        "官职",
        "本条直接定义六部长贰统称。",
        quotation=main,
    )
    group_t = tp(
        w,
        group_e,
        "宋代",
        "六部尚书与六部侍郎总称",
        i,
        main,
        "官职统称",
        "建立六部长贰宋代节点。",
    )
    rel(
        w,
        group_t,
        ft(w, fe(w, "六部尚书", "官职"), "宋代"),
        "统称与实例",
        i,
        main,
        "六部尚书为六部长贰所含长官类别。",
    )
    rel(
        w,
        group_t,
        ft(w, fe(w, "六部侍郎", "官职"), "北宋元丰改制前"),
        "统称与实例",
        i,
        main,
        "六部侍郎为六部长贰所含副长官类别。",
    )
    w.commit()


def entry967():
    i = 967
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    group_e = w.entity(
        "尚书二十四司",
        "机构",
        "本条直接定义尚书省六部二十四司统称。",
        quotation=main,
    )
    sui = tp(
        w,
        group_e,
        "隋文帝时",
        "形成尚书省六部二十四司之制",
        i,
        origin,
        "机构统称",
        "建立尚书二十四司隋代源流节点。",
        "职源",
        chain="none",
    )
    song = tp(
        w,
        group_e,
        "宋代元丰改制后",
        "习称二十四司，但吏部增为七司、户部增为五司，六部实际共二十八司",
        i,
        main,
        "机构统称",
        "建立宋代元丰改制后二十四司习称与实际二十八司节点。",
        chain="none",
    )
    cite(
        w,
        "Timepoints",
        song,
        i,
        aliases,
        "简称字段补证二十四司、二十四曹等省称；纯简称不另建实体。",
        "简称与别名",
        note="纯简称",
    )
    chain_all(w, group_e, [sui, song], "连接尚书二十四司隋代源流与宋代节点。")
    for index, title in enumerate(OFFICES):
        office_e = w.entity(
            title,
            "机构",
            f"本条明确列举{title}为尚书二十四司之一。",
            quotation=main,
        )
        office_t = tp(
            w,
            office_e,
            "宋代（尚书二十四司）",
            "尚书省六部所属司之一",
            i,
            main,
            "尚书省属司",
            f"建立{title}宋代二十四司节点。",
        )
        rel(w, song, office_t, "统称与实例", i, main, f"{title}为尚书二十四司实例。")
        department = DEPARTMENTS[index // 4]
        rel(
            w,
            department_timepoint(w, department),
            office_t,
            "上下级机构",
            i,
            main,
            f"原文在{department}四司中明确列举{title}。",
        )
    w.commit()


def entry968():
    i = 968
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    group_e = w.entity(
        "尚书省二十四司郎中",
        "官职",
        "本条直接定义尚书省二十四司郎中统称。",
        quotation=main,
    )
    tang = tp(
        w,
        group_e,
        "唐武德三年",
        "二十四司诸司郎改称郎中，郎中为一司之长",
        i,
        origin,
        "官职统称",
        "建立二十四司郎中唐代定名节点。",
        "职源",
        chain="none",
    )
    song = tp(
        w,
        group_e,
        "宋代（尚书二十四司）",
        "六部所属各司郎中总称，为本司长官",
        i,
        main,
        "官职统称",
        "建立二十四司郎中宋代节点。",
        chain="none",
        attr_grade="从六品",
    )
    cite(
        w,
        "Timepoints",
        song,
        i,
        aliases,
        "全文扫描简称与别名字段；六曹郎中、正郎等纯称谓不另建实体。",
        "简称与别名",
        note="纯简称与别名",
    )
    chain_all(w, group_e, [tang, song], "连接二十四司郎中唐代定名、宋代沿用节点。")
    for office, title in zip(OFFICES, DIRECTORS):
        role_e = w.entity(
            title,
            "官职",
            f"本条简称字段明确列举{title}为二十四司郎中实例。",
            quotation=aliases,
        )
        role_t = tp(
            w,
            role_e,
            "宋代（尚书二十四司）",
            "本司长官",
            i,
            aliases,
            "尚书省属司长官",
            f"建立{title}宋代节点。",
            "简称与别名",
            attr_grade="从六品",
        )
        rel(
            w,
            song,
            role_t,
            "统称与实例",
            i,
            aliases,
            f"{title}为尚书省二十四司郎中实例。",
            "简称与别名",
        )
        office_role_rel = rel(
            w,
            ft(
                w,
                fe(w, office, "机构"),
                "宋代（尚书二十四司）",
            ),
            role_t,
            "编制隶属",
            i,
            main,
            f"正文明确每司置郎中，郎中为本司之长；本条未载员额。",
            staff_type="官",
        )
        cite(
            w,
            "Relationships",
            office_role_rel,
            i,
            aliases,
            f"简称与别名字段逐一列出包括{title}在内的二十四司郎中。",
            "简称与别名",
        )
    w.commit()


def entry969():
    i = 969
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    group_e = w.entity(
        "尚书省二十四司员外郎",
        "官职",
        "本条直接定义尚书省二十四司员外郎统称。",
        quotation=main,
    )
    sui = tp(
        w,
        group_e,
        "隋开皇六年",
        "尚书省二十四司各置员外郎一人",
        i,
        origin,
        "官职统称",
        "建立二十四司员外郎隋代定型节点。",
        "职源",
        chain="none",
    )
    song = tp(
        w,
        group_e,
        "宋代（尚书二十四司）",
        "六部所属各司员外郎总称",
        i,
        main,
        "官职统称",
        "建立二十四司员外郎宋代节点。",
        chain="none",
        attr_grade="正七品",
    )
    cite(
        w,
        "Timepoints",
        song,
        i,
        aliases,
        "全文扫描简称与别名字段；员外、外郎等纯称谓不另建实体。",
        "简称与别名",
        note="纯简称与别名",
    )
    chain_all(w, group_e, [sui, song], "连接二十四司员外郎隋代定型、宋代沿用节点。")
    # 本条没有逐一列出二十四个正式官名；不得跨用第967条司名自动拼接。
    # 各司员外郎留待后续各专条出现时逐条建立。
    w.commit()


def entry970():
    i = 970
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    early_q = Q(
        i,
        "宋前期尚书省郎官（郎中、员外郎）别称，因元丰改制前二十四司郎中"
        "无职事，仅起唐散官阶叙秩禄作用。",
        "简称与别名",
    )
    reform_q = Q(
        i,
        "本朝元丰官制，六曹郎官理郡守以上资任者郎中，"
        "通判以下资序者为员外郎。",
        "简称与别名",
    )
    w = W(i)
    group_e = w.entity(
        "尚书省六部诸司郎中、员外郎",
        "官职",
        "本条直接定义尚书省六部诸司郎中、员外郎总称。",
        quotation=main,
    )
    early = tp(
        w,
        group_e,
        "宋前期（元丰改制前）",
        "二十四司郎中、员外郎无职事，仅作散官阶叙秩禄",
        i,
        early_q,
        "官职统称",
        "建立宋前期六部诸司郎中、员外郎仅作散官阶的节点。",
        "简称与别名",
        chain="none",
    )
    reform = tp(
        w,
        group_e,
        "北宋元丰官制",
        "改为六部各司长贰；郡守以上资任者为郎中，通判以下资序者为员外郎",
        i,
        reform_q,
        "六部诸司长贰统称",
        "建立元丰官制后六曹郎官恢复职事并按资序分郎中、员外郎的节点。",
        "简称与别名",
        chain="none",
    )
    cite(
        w,
        "Timepoints",
        reform,
        i,
        main,
        "正文补证六部二十四司置郎中、员外郎并为本司长贰。",
    )
    cite(
        w,
        "Timepoints",
        reform,
        i,
        aliases,
        "全文扫描简称与别名字段；尚书郎、省郎等纯称谓不另建实体。",
        "简称与别名",
        note="纯简称与别名",
    )
    chain_all(
        w,
        group_e,
        [early, reform],
        "连接六部诸司郎中、员外郎元丰前散官阶与元丰后职事官节点。",
    )
    rel(
        w,
        reform,
        ft(w, fe(w, "尚书省二十四司郎中", "官职"), "宋代（尚书二十四司）"),
        "统称与实例",
        i,
        main,
        "二十四司郎中为六部诸司长贰中的长官类别。",
    )
    rel(
        w,
        reform,
        ft(w, fe(w, "尚书省二十四司员外郎", "官职"), "宋代（尚书二十四司）"),
        "统称与实例",
        i,
        main,
        "二十四司员外郎为六部诸司长贰中的副长官类别。",
    )
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(951, 971)] == [
        "讲议司商旅检讨文字",
        "讲议司盐泽检讨文字",
        "讲议司尹牧检讨文字",
        "尚书省讲议司检阅文字",
        "尚书省讲议财利司",
        "提举尚书省讲议财利司",
        "尚书省详议司",
        "议礼局",
        "礼制局",
        "尚书省六部",
        "六部尚书",
        "五曹尚书",
        "权六部尚书",
        "六部侍郎",
        "权六部侍郎",
        "六部长贰",
        "尚书二十四司",
        "尚书省二十四司郎中",
        "尚书省二十四司员外郎",
        "尚书省六部诸司郎中、员外郎",
    ]
    entry951_953()
    entry954()
    entry955_core()
    entry956()
    entry957()
    entry958()
    entry959()
    entry960()
    entry961()
    entry962()
    entry963()
    entry964()
    entry965()
    entry966()
    entry967()
    entry968()
    entry969()
    entry970()


if __name__ == "__main__":
    main()
