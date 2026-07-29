#!/usr/bin/env python3
"""提取 chapter2t4 第931–950条：会子务、左藏封桩库与尚书省讲议司。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(931, 951)}
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


def entry931():
    i = 931
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["别称"], "别称")
    w = W(i)

    eid = w.entity(
        "行在会子务",
        "机构",
        "本条直接定义行在会子务。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "南宋绍兴三十一年二月十三日",
        "始置于临安府，印行会子并使其流通于东南诸路",
        i,
        origin,
        "纸币发行机构",
        "建立行在会子务始置节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证会子务印行纸币及流通职能。", "职掌")
    middle = tp(
        w,
        eid,
        "南宋（绍定五年前，未载具体年月）",
        "由榷货务监门官兼领",
        i,
        main,
        "纸币发行机构",
        "原文明示初隶都茶场后改由榷货务监门官兼领，但未载改领年月。",
        chain="none",
    )
    shaoding = tp(
        w,
        eid,
        "南宋绍定五年",
        "改隶都司，由都司官兼提领",
        i,
        main,
        "纸币发行机构",
        "建立绍定五年会子务改隶都司节点。",
        chain="none",
    )
    cite(w, "Timepoints", shaoding, i, staff, "补证提领官由都司兼领。", "编制")
    cite(w, "Timepoints", shaoding, i, aliases, "补证会子所在三省大门内并由都司官兼领。", "别称")
    chain_all(w, eid, [start, middle, shaoding], "连接行在会子务始置、改领及绍定改隶节点。")

    tea_e = w.entity(
        "都茶场",
        "机构",
        "会子务条明确记载行在会子务初隶都茶场。",
        quotation=main,
    )
    tea_t = tp(
        w,
        tea_e,
        "南宋绍兴三十一年二月十三日",
        "行在会子务初隶本场",
        i,
        main,
        "茶叶专卖机构",
        "建立都茶场承载会子务初隶关系的节点。",
    )
    rel(
        w,
        tea_t,
        start,
        "上下级机构",
        i,
        main,
        "原文明确行在会子务初隶都茶场。",
    )

    gate_e = w.entity(
        "榷货务监门官",
        "官职",
        "会子务条明确记载后改由榷货务监门官兼领。",
        quotation=main,
    )
    gate_t = tp(
        w,
        gate_e,
        "南宋（绍定五年前，未载具体年月）",
        "兼领行在会子务",
        i,
        main,
        "财政监当官",
        "建立榷货务监门官兼领会子务节点。",
        attr_officer_type="兼领",
    )
    rel(
        w,
        middle,
        gate_t,
        "编制隶属",
        i,
        main,
        "行在会子务由榷货务监门官兼领；原文未明示员额。",
        staff_type="官",
    )

    lead_e = w.entity(
        "行在会子务提领官",
        "官职",
        "编制字段明确行在会子务设提领官。",
        quotation=staff,
    )
    lead_t = tp(
        w,
        lead_e,
        "南宋绍定五年",
        "由都司官兼领行在会子务",
        i,
        staff,
        "财政兼官",
        "建立绍定五年会子务提领官节点。",
        "编制",
        attr_officer_type="都司官兼",
    )
    rel(
        w,
        shaoding,
        lead_t,
        "编制隶属",
        i,
        staff,
        "行在会子务提领官由都司兼领；原文未明示员额。",
        "编制",
        staff_type="官",
    )
    province_e = fe(w, "尚书都省", "机构")
    province_chain = current_chain(w, province_e)
    province_south = tp(
        w,
        province_e,
        "南宋绍定五年",
        "行在会子务改隶都司",
        i,
        main,
        "尚书省总部机构",
        "第931条明确绍定五年会子务改隶都司，补建同年尚书都省关系承载节点。",
        chain="none",
    )
    if province_south not in province_chain:
        province_chain.append(province_south)
    chain_all(w, province_e, province_chain, "将绍定五年都司节点接入尚书都省完整时间链。")
    rel(
        w,
        province_south,
        shaoding,
        "上下级机构",
        i,
        main,
        "绍定五年行在会子务改隶都司；关系两端均使用同年节点。",
    )
    w.commit()


def entry932():
    i = 932
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "会子库",
        "机构",
        "本条直接定义会子库。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋绍兴三十一年二月十三日",
        "行在会子务附属库，设在本务内",
        i,
        main,
        "纸币库",
        "会子库未载独立始置日，按所属会子务始置节点承载附属关系。",
    )
    rel(
        w,
        ft(w, fe(w, "行在会子务", "机构"), "南宋绍兴三十一年二月十三日"),
        tid,
        "上下级机构",
        i,
        main,
        "原文明确会子库附属于会子务并设在本务内。",
    )
    w.commit()


def entry933_core():
    i = 933
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职能"], "职能")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "左藏封桩库",
        "机构",
        "本条直接定义左藏封桩库。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "南宋淳熙二年十一月十一日",
        "由左藏南上库与封桩库合并创置，储藏金银钱币以供御前亲属及军事急需",
        i,
        origin,
        "御前财政库",
        "建立左藏封桩库合并创置节点。",
        "职源",
    )
    cite(w, "Timepoints", start, i, duty, "补证左藏封桩库储藏与支用职能。", "职能")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证封桩库省称；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )

    for predecessor in ("左藏南上库", "封桩库"):
        old_e = w.entity(
            predecessor,
            "机构",
            f"职源字段明确{predecessor}为左藏封桩库合并前身。",
            quotation=origin,
        )
        old_end = tp(
            w,
            old_e,
            "南宋淳熙二年十一月十一日",
            "并入左藏封桩库",
            i,
            origin,
            "财政库",
            f"建立{predecessor}合并终止节点。",
            "职源",
        )
        rel(
            w,
            old_end,
            start,
            "前后演变",
            i,
            origin,
            f"{predecessor}与另一库合并为左藏封桩库。",
            "职源",
        )
    rel(
        w,
        ft(w, fe(w, "尚书省左、右司", "机构"), "宋代（未载具体年月）"),
        start,
        "上下级机构",
        i,
        staff,
        "编制字段明确左藏封桩库隶尚书省左、右司。",
        "编制",
    )

    role_specs = (
        ("提领左藏封桩库", "官", 1, "兼官"),
        ("监左藏封桩库", "官", 1, "库务职事官"),
        ("监左藏封桩门", "官", 1, "库门职事官"),
        ("左藏封桩库副知", "吏", 1, "库务吏职"),
        ("左藏封桩库手分", "吏", 1, "库务吏职"),
        ("左藏封桩库书手", "吏", 1, "库务吏职"),
        ("左藏封桩库库子", "吏", 1, "库务吏职"),
    )
    for title, staff_type, quota, category in role_specs:
        role_e = w.entity(
            title,
            "官职",
            f"左藏封桩库编制字段明列{title.removeprefix('左藏封桩库')}。",
            quotation=staff,
        )
        role_t = tp(
            w,
            role_e,
            "南宋淳熙二年十一月十一日",
            "左藏封桩库创置编制",
            i,
            staff,
            category,
            f"建立{title}随左藏封桩库创置的编制节点。",
            "编制",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            staff,
            f"左藏封桩库编制明列{title}一员或一名。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )
    w.commit()


def entry934():
    i = 934
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "提领左藏封桩库", "官职")
    start = refine(
        w,
        ft(w, eid, "南宋淳熙二年十一月十一日"),
        i,
        main,
        "专条补证提领左藏封桩库由太常少卿兼任并总领库事。",
        event="总领左藏封桩库事，由太常少卿颜度兼任",
        category="兼官",
        officer="太常少卿兼",
    )
    later = tp(
        w,
        eid,
        "南宋淳熙九年后",
        "归尚书都司郎官提领，并可兼领杂卖场、寄桩库",
        i,
        main,
        "兼官",
        "建立淳熙九年后提领官兼任来源变化节点。",
        chain="none",
        attr_officer_type="尚书都司郎官兼",
    )
    chain_all(w, eid, [start, later], "连接提领左藏封桩库始置及淳熙九年后节点。")
    w.commit()


def entry935():
    i = 935
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "提领左藏封桩库所",
        "机构",
        "本条直接定义提领左藏封桩库所。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋（提领官设置后，未载具体年月）",
        "提领官办事机构；先有提领官，后设提领所",
        i,
        main,
        "财政库管理机构",
        "原文明确有提领官即设提领所，但未载本所确切设置年月。",
    )
    rel(
        w,
        ft(w, fe(w, "左藏封桩库", "机构"), "南宋淳熙二年十一月十一日"),
        tid,
        "上下级机构",
        i,
        main,
        "提领所是左藏封桩库提领官的办事机构。",
    )
    w.commit()


def entry936():
    i = 936
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = fe(w, "监左藏封桩库", "官职")
    tid = refine(
        w,
        ft(w, eid, "南宋淳熙二年十一月十一日"),
        i,
        main,
        "专条补证监左藏封桩库的职掌。",
        event="为提领官属官，实际监理库务",
        category="库务职事官",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段补证监封桩库省称；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    w.commit()


def entry937():
    i = 937
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "监左藏封桩门", "官职")
    refine(
        w,
        ft(w, eid, "南宋淳熙二年十一月十一日"),
        i,
        main,
        "专条补证监左藏封桩门的职掌。",
        event="守库门，检查出入本库人员有无不法事",
        category="库门职事官",
    )
    w.commit()


def entry938():
    _refine_store_clerk(
        938,
        "左藏封桩库副知",
        "掌管、签押本库财物，位次专知官",
    )


def entry939():
    _refine_store_clerk(
        939,
        "左藏封桩库手分",
        "掌管本库文案与文书收发",
    )


def entry940():
    _refine_store_clerk(
        940,
        "左藏封桩库书手",
        "抄写文书，地位低于手分",
    )


def entry941():
    _refine_store_clerk(
        941,
        "左藏封桩库库子",
        "经手库物出纳",
    )


def _refine_store_clerk(i, title, event):
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, title, "官职")
    refine(
        w,
        ft(w, eid, "南宋淳熙二年十一月十一日"),
        i,
        main,
        f"专条补证{title}职掌。",
        event=event,
        category="库务吏职",
    )
    w.commit()


def entry942_core():
    i = 942
    name = Q(i, "临时官署名。")
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "尚书省讲议司",
        "机构",
        "修复切分后，本条直接定义尚书省讲议司。",
        quotation=name,
    )
    start = tp(
        w,
        eid,
        "北宋崇宁元年七月一日",
        "始置，议宗室、国用、商旅、盐泽、赋调、冗官、尹牧七事并派官相度措置",
        i,
        origin,
        "临时中央议政机构",
        "建立尚书省讲议司始置节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证讲议司七事职掌及侵夺三省职权。", "职掌")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证讲议司、都省讲议司省称及都省置司。",
        "简称",
        note="纯简称；跨页引文已由切分修复完整归位",
    )
    end = tp(
        w,
        eid,
        "北宋崇宁三年四月",
        "结局",
        i,
        origin,
        "临时中央议政机构",
        "建立尚书省讲议司结局节点。",
        "职源",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接尚书省讲议司始置、结局节点。")
    rel(
        w,
        ft(w, fe(w, "尚书都省", "机构"), "北宋元丰五年十月十七日"),
        start,
        "上下级机构",
        i,
        aliases,
        "简称引文明确崇宁元年都省置讲议司。",
        "简称",
    )

    role_specs = (
        ("提举尚书省讲议司", "官", 1, "兼官"),
        ("讲议司详定官", "官", 3, "讲议司高级属官"),
        ("讲议司参详官", "官", 4, "讲议司属官"),
        ("讲议司检讨文字", "官", 20, "讲议司属官"),
        ("尚书省讲议司检阅文字", "吏", None, "讲议司吏职"),
    )
    for title, staff_type, quota, category in role_specs:
        role_e = w.entity(
            title,
            "官职",
            f"尚书省讲议司编制字段明列{title}。",
            quotation=staff,
        )
        role_t = tp(
            w,
            role_e,
            "北宋崇宁元年七月一日",
            (
                f"尚书省讲议司始置编制，{quota}人"
                if quota is not None
                else "尚书省讲议司始置编制，未载员额"
            ),
            i,
            staff,
            category,
            f"建立{title}随讲议司始置的编制节点。",
            "编制",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            staff,
            f"尚书省讲议司编制明列{title}；仅对原文明示数字填写员额。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )
    w.commit()


def entry943():
    i = 943
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "提举尚书省讲议司", "官职")
    initial = refine(
        w,
        ft(w, eid, "北宋崇宁元年七月一日"),
        i,
        main,
        "专条补证提举讲议司由宰相兼任并总领司事。",
        event="宰相兼官，总领尚书省讲议司事",
        category="兼官",
        officer="宰相兼",
    )
    appointment = tp(
        w,
        eid,
        "北宋崇宁元年八月四日",
        "尚书右仆射兼中书侍郎蔡京奉诏提举讲议司",
        i,
        main,
        "兼官",
        "建立蔡京奉诏提举讲议司的明确日期节点。",
        chain="none",
        attr_officer_type="宰相兼",
    )
    chain_all(w, eid, [initial, appointment], "连接提举讲议司始置编制及八月任命节点。")
    w.commit()


def entry944():
    i = 944
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "讲议司详定官", "官职")
    refine(
        w,
        ft(w, eid, "北宋崇宁元年七月一日"),
        i,
        main,
        "修复目录OCR后，专条补证讲议司详定官的层级与兼任来源。",
        event="尚书省讲议司高级属官，由六部长贰或翰林学士兼充",
        category="讲议司高级属官",
        officer="六部长贰或翰林学士兼",
    )
    w.commit()


def entry945():
    i = 945
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "讲议司参详官", "官职")
    refine(
        w,
        ft(w, eid, "北宋崇宁元年七月一日"),
        i,
        main,
        "专条补证讲议司参详官的层级。",
        event="尚书省讲议司属官，位次详定官",
        category="讲议司属官",
    )
    w.commit()


def entry946():
    i = 946
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = fe(w, "讲议司检讨文字", "官职")
    tid = refine(
        w,
        ft(w, eid, "北宋崇宁元年七月一日"),
        i,
        main,
        "专条补证讲议司检讨文字分管七事。",
        event="尚书省讲议司属官，分管讨论七事",
        category="讲议司属官",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段补证检讨官省称及每事差三员讨论。",
        "简称",
        note="纯简称；每事三员不改写为本官总员额",
    )
    w.commit()


def entry947():
    _entry_review_branch(
        947,
        "讲议司宗室检讨文字",
        "分管讨论宗室事",
    )


def entry948():
    _entry_review_branch(
        948,
        "讲议司冗官检讨文字",
        "分管讨论冗官事",
    )


def entry949():
    _entry_review_branch(
        949,
        "讲议司国用检讨文字",
        "分管讨论财政开支",
    )


def entry950():
    _entry_review_branch(
        950,
        "讲议司赋调检讨文字",
        "分管讨论国家税收",
    )


def _entry_review_branch(i, title, event):
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
        f"原文明确{title}为尚书省讲议司内分事检讨官；不另推员额。",
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
        f"{title}是讲议司检讨文字按七事分工的实例。",
    )
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(931, 951)] == [
        "行在会子务",
        "会子库",
        "左藏封桩库",
        "提领左藏封桩库",
        "提领左藏封桩库所",
        "监左藏封桩库",
        "监左藏封桩门",
        "左藏封桩库副知",
        "左藏封桩库手分",
        "左藏封桩库书手",
        "左藏封桩库库子",
        "尚书省讲议司",
        "提举尚书省讲议司",
        "讲议司详定官",
        "讲议司参详官",
        "讲议司检讨文字",
        "讲议司宗室检讨文字",
        "讲议司冗官检讨文字",
        "讲议司国用检讨文字",
        "讲议司赋调检讨文字",
    ]
    entry931()
    entry932()
    entry933_core()
    entry934()
    entry935()
    entry936()
    entry937()
    entry938()
    entry939()
    entry940()
    entry941()
    entry942_core()
    entry943()
    entry944()
    entry945()
    entry946()
    entry947()
    entry948()
    entry949()
    entry950()


if __name__ == "__main__":
    main()
