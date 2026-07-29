#!/usr/bin/env python3
"""提取 chapter2t4 第1051–1070条：考功司、官告院与户部系统。"""
import extract_2t4_811_830 as x


x.b.F = {
    963: x.b.load(963),
    974: x.b.load(974),
    **{i: x.b.load(i) for i in range(1051, 1071)},
}
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
current_chain = x.current_chain
mark_citation_conflict = x.b.mark_citation_conflict


def field(i, name):
    return Q(i, x.b.F[i]["fields"][name], name)


def ft_any(w, entity_id, *times):
    for time in times:
        timepoint_id = w.find_timepoint(entity_id, time)
        if timepoint_id is not None:
            return timepoint_id
    raise AssertionError((entity_id, times))


def entry1051():
    i = 1051
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    grade = field(i, "官品")
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "考功司员外郎",
        "官职",
        "本条直接定义考功司员外郎为官阶名、职事官名。",
        quotation=main,
    )
    sui = tp(
        w,
        eid,
        "隋开皇六年",
        "始置",
        i,
        origin,
        "考功司郎官",
        "建立考功司员外郎隋代职源节点。",
        "职源",
        chain="none",
    )
    song = tp(
        w,
        eid,
        "宋前期",
        "无职事，为文臣迁转的前行员外郎阶",
        i,
        duty,
        "文臣迁转官阶",
        "建立考功司员外郎宋前期阶官节点。",
        "职掌",
        chain="none",
        attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w,
        eid,
        "北宋元丰新制",
        "为本司副贰，正郎缺则总领本司事",
        i,
        duty,
        "考功司副长官",
        "建立考功司员外郎元丰职事节点。",
        "职掌",
        chain="none",
        attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, staff, "补证郎中、员外郎不并置，共一人。", "编制")
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        aliases,
        "简称字段补证考功员外郎等称谓；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    chain_all(w, eid, [sui, song, reform], "连接考功司员外郎隋、宋前期和元丰节点。")
    rel(
        w,
        ft(w, fe(w, "考功司", "机构"), "北宋元丰新制"),
        reform,
        "编制隶属",
        i,
        staff,
        "考功司郎中、员外郎不并置，共设一人。",
        "编制",
        staff_type="官",
    )
    w.commit()


def entry1052():
    i = 1052
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    group_e = w.entity(
        "考功司十七案",
        "机构",
        "本条直接定义元丰考功司十七案的集合。",
        quotation=main,
    )
    group_t = tp(
        w,
        group_e,
        "北宋元丰新制",
        "考功司所分十七办事案的总称",
        i,
        main,
        "机构合称",
        "建立考功司十七案总称节点。",
    )
    parent = ft(w, fe(w, "考功司", "机构"), "北宋元丰新制")
    case_names = (
        "五品案",
        "六品案",
        "七品案",
        "八品案",
        "九品案",
        "职官案",
        "参军案",
        "令丞案",
        "主簿案",
        "县尉案",
        "使副案",
        "供奉官案",
        "资任案",
        "核定案",
        "检法案",
        "开拆案",
        "知杂案",
    )
    for short in case_names:
        title = f"考功司{short}"
        eid = w.entity(
            title,
            "机构",
            f"考功司十七案原文明列{short}。",
            quotation=main,
        )
        tid = tp(
            w,
            eid,
            "北宋元丰新制",
            f"考功司十七案之一：{short}",
            i,
            main,
            "考功司办事案",
            f"建立{title}元丰节点。",
        )
        rel(w, group_t, tid, "统称与实例", i, main, f"考功司十七案包括{short}。")
        rel(w, parent, tid, "上下级机构", i, main, f"{title}为考功司所属办事案。")
    w.commit()


def entry1053():
    i = 1053
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    qualification = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    archive_e = w.entity(
        "吏部架阁库",
        "机构",
        "职源字段明确崇宁元年吏部单独置架阁库。",
        quotation=origin,
    )
    archive_t = tp(
        w,
        archive_e,
        "北宋崇宁元年",
        "吏部首次单独设置，保存本部结案二年以上文书",
        i,
        origin,
        "吏部档案机构",
        "建立吏部架阁库始置节点。",
        "职源",
    )
    cite(w, "Timepoints", archive_t, i, duty, "补证吏部架阁库档案保管职能。", "职掌")

    former_e = w.entity(
        "管勾尚书省吏部架阁库文字",
        "官职",
        "职源字段明确崇宁元年置管勾吏部架阁库文字官。",
        quotation=origin,
    )
    former_t = tp(
        w,
        former_e,
        "北宋崇宁元年",
        "始置，主管吏部架阁库文书档案",
        i,
        origin,
        "吏部档案官",
        "建立北宋管勾吏部架阁文字节点。",
        "职源",
    )
    cite(w, "Timepoints", former_t, i, duty, "补证档案整理、登记、保存与检索职掌。", "职掌")

    eid = w.entity(
        "主管尚书省吏部架阁文字",
        "官职",
        "本条直接定义南宋吏部架阁职事官。",
        quotation=main,
    )
    south = tp(
        w,
        eid,
        "南宋",
        "由管勾改称主管，掌吏部架阁库文书档案",
        i,
        origin,
        "吏部档案官",
        "建立南宋改称主管节点。",
        "职源",
    )
    cite(w, "Timepoints", south, i, duty, "补证档案整理、登记、保存与检索职掌。", "职掌")
    cite(w, "Timepoints", south, i, qualification, "补证由进士出身、有才望选人充任。", "官品")
    cite(
        w,
        "Timepoints",
        south,
        i,
        aliases,
        "简称与别名仅作称谓和制度证据，不另建实体。",
        "简称与别名",
        note="纯简称",
    )
    rel(
        w,
        ft(w, fe(w, "吏部", "机构"), "北宋元丰改制后"),
        archive_t,
        "上下级机构",
        i,
        origin,
        "崇宁元年吏部单独置架阁库。",
        "职源",
    )
    rel(
        w,
        archive_t,
        former_t,
        "编制隶属",
        i,
        origin,
        "北宋置管勾吏部架阁库文字官。",
        "职源",
        staff_quota=1,
        staff_type="官",
    )
    rel(
        w,
        archive_t,
        south,
        "编制隶属",
        i,
        origin,
        "南宋改管勾为主管，仍掌吏部架阁文字。",
        "职源",
        staff_quota=1,
        staff_type="官",
    )
    rel(
        w,
        former_t,
        south,
        "前后演变",
        i,
        origin,
        "南宋由管勾尚书省吏部架阁库文字改称主管尚书省吏部架阁文字。",
        "职源",
    )
    w.commit()


def entry1054():
    i = 1054
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "尚书省制造官告局",
        "机构",
        "本条直接定义尚书省制造官告局为官署。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋崇宁四年二月",
        "始置，专管文武官、将校、蕃官及封赠官告制造",
        i,
        origin,
        "尚书省官告制造机构",
        "建立制造官告局始置节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证制造官告局职掌。", "职掌")
    abolished = tp(
        w,
        eid,
        "北宋崇宁五年正月三十日",
        "罢",
        i,
        origin,
        "尚书省官告制造机构",
        "建立制造官告局首次罢置节点。",
        "职源与沿革",
        chain="none",
    )
    restored = tp(
        w,
        eid,
        "北宋大观元年二月二十四日",
        "复置",
        i,
        origin,
        "尚书省官告制造机构",
        "建立制造官告局复置节点。",
        "职源与沿革",
        chain="none",
    )
    renamed = tp(
        w,
        eid,
        "北宋大观元年十一月",
        "改名尚书省官告院",
        i,
        origin,
        "尚书省官告制造机构",
        "建立制造官告局改名终结节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", restored, i, aliases, "简称引文补证大观元年复置及十一月改名。", "简称")
    chain_all(w, eid, [start, abolished, restored, renamed], "连接制造官告局始置、罢置、复置与改名节点。")

    old_e = fe(w, "兵部、吏部、司封、司勋官告院", "机构")
    old_chain = current_chain(w, old_e)
    old_end = tp(
        w,
        old_e,
        "北宋元丰五年",
        "罢，文武官告归吏部尚书右选，蕃官官告归兵部",
        i,
        origin,
        "宋前期官告制造机构",
        "据专条补建早期四官告院元丰罢置节点。",
        "职源与沿革",
        chain="none",
    )
    if old_end not in old_chain:
        old_chain.append(old_end)
    chain_all(w, old_e, old_chain, "将元丰罢置接入早期四官告院完整时间链。")
    rel(
        w,
        old_end,
        start,
        "前后演变",
        i,
        origin,
        "早期四官告院罢后曾无专门机构，崇宁四年另置尚书省制造官告局。",
        "职源与沿革",
    )
    rel(
        w,
        ft(w, fe(w, "尚书省", "机构"), "北宋元丰新制"),
        start,
        "上下级机构",
        i,
        origin,
        "官署全称与正文明确其为尚书省机构。",
        "职源与沿革",
    )
    w.commit()


def entry1055():
    i = 1055
    main = Q(i, x.b.F[i]["text"])
    aliases = field(i, "简称")
    origin = field(1054, "职源与沿革")
    w = W(i)
    eid = w.entity(
        "主管尚书省制造官告局",
        "官职",
        "本条直接定义制造官告局主管官。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋崇宁四年二月",
        "随制造官告局始置，由监尚书都省门内臣或六部架阁文字官差充",
        i,
        main,
        "制造官告局主管官",
        "建立主管制造官告局始置节点。",
        chain="none",
    )
    abolished = tp(
        w,
        eid,
        "北宋崇宁五年正月三十日",
        "随制造官告局罢",
        1054,
        origin,
        "制造官告局主管官",
        "建立主管官随局罢置节点。",
        "职源与沿革",
        chain="none",
    )
    restored = tp(
        w,
        eid,
        "北宋大观元年二月二十四日",
        "随制造官告局复置",
        1054,
        origin,
        "制造官告局主管官",
        "建立主管官随局复置节点。",
        "职源与沿革",
        chain="none",
    )
    renamed = tp(
        w,
        eid,
        "北宋大观元年十一月",
        "制造官告局改为尚书省官告院，本官名终止",
        1054,
        origin,
        "制造官告局主管官",
        "建立主管制造官告局终止节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", restored, i, aliases, "简称引文补证大观元年主管官告局。", "简称")
    chain_all(w, eid, [start, abolished, restored, renamed], "连接主管制造官告局设置、罢复及终止节点。")
    for office_time, role_time in (
        ("北宋崇宁四年二月", "北宋崇宁四年二月"),
        ("北宋大观元年二月二十四日", "北宋大观元年二月二十四日"),
    ):
        rel(
            w,
            ft(w, fe(w, "尚书省制造官告局", "机构"), office_time),
            ft(w, eid, role_time),
            "编制隶属",
            i,
            main,
            "制造官告局设主管官。",
            staff_quota=1,
            staff_type="官",
        )
    w.commit()


def entry1057():
    i = 1057
    main = Q(i, x.b.F[i]["text"])
    manufacturing_origin = field(1054, "职源与沿革")
    old_duty = field(974, "职掌")
    w = W(i)
    eid = fe(w, "尚书省官告院", "机构")
    disputed_old = ft_any(
        w,
        eid,
        "北宋元丰改制后",
        "北宋元丰改制后（异文）",
    )
    mark_citation_conflict(
        w,
        "Timepoints",
        disputed_old,
        974,
        old_duty,
        "本条及制造官告局专条明确元丰五年旧官告院罢、当时无专门机构；"
        "吏部总条却称元丰后领官告院。",
        "标记元丰后官告院是否为专门机构的异文。",
        "职掌",
    )
    disputed = refine(
        w,
        disputed_old,
        974,
        old_duty,
        "将吏部总条说法保留为显式异文节点，不混同早期四官告院罢置事件。",
        "职掌",
        time="北宋元丰改制后（异文）",
        event="吏部总条称兼领官告院；专条称当时无专门官告制造机构",
        category="尚书省官告制造机构",
    )
    cite(
        w,
        "Timepoints",
        disputed,
        1054,
        manufacturing_origin,
        "制造官告局专条称元丰五年旧官告院罢且无专门机构，与吏部总条冲突。",
        "职源与沿革",
        note="元丰机构异文：吏部总条称领官告院，制造官告局专条称无专门机构",
        conflict_flag=1,
    )
    rid = relation_id(
        w,
        "吏部",
        "尚书省官告院",
        "上下级机构",
        "北宋元丰改制后",
        "北宋元丰改制后（异文）",
    )
    assert rid
    mark_citation_conflict(
        w,
        "Relationships",
        rid,
        974,
        old_duty,
        "制造官告局专条明确元丰五年旧官告院罢且无专门机构；"
        "保留吏部总条的相反关系并显式标冲突。",
        "标记元丰吏部领官告院关系异文。",
        "职掌",
    )

    start = tp(
        w,
        eid,
        "北宋大观元年十一月",
        "由尚书省制造官告局改名，仍隶尚书省左、右司",
        i,
        main,
        "尚书省官告制造机构",
        "建立尚书省官告院改名始置节点。",
        chain="none",
    )
    end_daguan = tp(
        w,
        eid,
        "北宋大观三年六月",
        "制造官告局专条记罢，职能转归吏部",
        1054,
        manufacturing_origin,
        "尚书省官告制造机构",
        "保留制造官告局专条所载大观三年罢置说。",
        "职源与沿革",
        chain="none",
    )
    mark_citation_conflict(
        w,
        "Timepoints",
        end_daguan,
        1054,
        manufacturing_origin,
        "终止时间异文：本条作大观三年六月，尚书省官告院条作政和三年六月。",
        "标记尚书省官告院大观三年终止说。",
        "职源与沿革",
    )
    end_zhenghe = tp(
        w,
        eid,
        "北宋政和三年六月",
        "本条记罢归吏部",
        i,
        main,
        "尚书省官告制造机构",
        "保留尚书省官告院专条所载政和三年罢置说。",
        chain="none",
    )
    mark_citation_conflict(
        w,
        "Timepoints",
        end_zhenghe,
        i,
        main,
        "终止时间异文：尚书省官告院条作政和三年六月，制造官告局条作大观三年六月。",
        "标记尚书省官告院政和三年终止说。",
    )
    chain_all(
        w,
        eid,
        [disputed, start, end_daguan, end_zhenghe],
        "连接元丰总条异文、大观改名及两种罢置时间异文。",
    )
    rel(
        w,
        ft(w, fe(w, "尚书省制造官告局", "机构"), "北宋大观元年十一月"),
        start,
        "前后演变",
        i,
        main,
        "尚书省制造官告局改名尚书省官告院。",
    )
    for parent_title in ("尚书省左司", "尚书省右司"):
        rel(
            w,
            ft(w, fe(w, parent_title, "机构"), "北宋元丰新制"),
            start,
            "上下级机构",
            i,
            main,
            f"尚书省官告院仍隶{parent_title}。",
        )
    w.commit()


def entry1058():
    i = 1058
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "别名")
    w = W(i)
    eid = w.entity(
        "官告院",
        "机构",
        "本条直接定义政和以后隶吏部的官告院。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋政和三年六月十四日",
        "依旧置于吏部，制造文武官、将校、蕃官及封赠官告",
        i,
        origin,
        "吏部属院",
        "建立吏部官告院始置节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证官告院制造各类官告职掌。", "职掌")
    cite(w, "Timepoints", start, i, aliases, "别名官诰院仅作称谓证据。", "别名", note="纯别名")
    jingkang = tp(
        w,
        eid,
        "北宋靖康元年二月二十三日",
        "主管官告院二员",
        1060,
        Q(1060, x.b.F[1060]["text"]),
        "吏部属院",
        "建立靖康主管官额节点。",
        chain="none",
    )
    south = tp(
        w,
        eid,
        "南宋隆兴元年",
        "沿置，主管官二员，吏额二十九人",
        i,
        staff,
        "吏部属院",
        "建立南宋官告院编制节点。",
        "编制",
        chain="none",
    )
    chain_all(w, eid, [start, jingkang, south], "连接官告院政和始置、靖康与南宋节点。")

    ministry_e = fe(w, "吏部", "机构")
    ministry_chain = current_chain(w, ministry_e)
    ministry_zhenghe = tp(
        w,
        ministry_e,
        "北宋政和三年六月十四日",
        "依旧在本部设置官告院",
        i,
        origin,
        "尚书省所属选官机构",
        "建立吏部政和复置官告院节点。",
        "职源",
        chain="none",
    )
    if ministry_zhenghe not in ministry_chain:
        ministry_chain.append(ministry_zhenghe)
    chain_all(w, ministry_e, ministry_chain, "将政和复置官告院接入吏部完整时间链。")
    rel(w, ministry_zhenghe, start, "上下级机构", i, origin, "政和三年官告院置于吏部。", "职源")
    rel(
        w,
        ft(w, fe(w, "尚书省官告院", "机构"), "北宋政和三年六月"),
        start,
        "前后演变",
        i,
        origin,
        "尚书省官告院罢后，依旧在吏部置官告院。",
        "职源",
    )
    w.commit()


def entry1059():
    i = 1059
    main = Q(i, x.b.F[i]["text"])
    duty = field(i, "职能")
    staff = field(i, "编制")
    w = W(i)
    eid = w.entity(
        "官告院绫纸库",
        "机构",
        "本条直接定义官告院附属绫纸库。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "北宋政和三年六月十四日",
        "随官告院置，掌官告绫纸及朱胶、绫纸钱",
        i,
        duty,
        "官告院附属库",
        "建立官告院绫纸库节点。",
        "职能",
    )
    rel(
        w,
        ft(w, fe(w, "官告院", "机构"), "北宋政和三年六月十四日"),
        tid,
        "上下级机构",
        i,
        main,
        "原文明确官告院绫纸库为官告院附属机构。",
    )
    roles = (
        ("官告院绫纸库专知官", "专领绫纸库事，由使臣充", 1, "官"),
        ("官告院绫纸库副专知官", "副领绫纸库事，由三司军大将充", 1, "官"),
        ("官告院绫纸库守阙吏人", "抄写文字", 1, "吏"),
    )
    for title, event, quota, staff_type in roles:
        role_e = w.entity(title, "官职", f"编制字段明列{title}。", quotation=staff)
        role_t = tp(
            w,
            role_e,
            "北宋政和三年以后",
            event,
            i,
            staff,
            "官告院绫纸库属员",
            f"建立{title}节点。",
            "编制",
        )
        rel(
            w,
            tid,
            role_t,
            "编制隶属",
            i,
            staff,
            f"官告院绫纸库置{title}一人。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )
    w.commit()


def entry1060():
    i = 1060
    main = Q(i, x.b.F[i]["text"])
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity(
        "主管官告院",
        "官职",
        "本条直接定义主管官告院为官告院长官。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "北宋靖康元年二月二十三日",
        "诏置二员主管官告院",
        i,
        main,
        "官告院长官",
        "建立主管官告院靖康节点。",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段补证主管院、主管官诰院等称谓；纯简称不另建实体。",
        "简称与别名",
        note="纯简称",
    )
    rel(
        w,
        ft(w, fe(w, "官告院", "机构"), "北宋靖康元年二月二十三日"),
        tid,
        "编制隶属",
        i,
        main,
        "靖康元年诏官告院官二员主管。",
        staff_quota=2,
        staff_type="官",
    )
    w.commit()


def entry1061():
    i = 1061
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity(
        "尚书省户部",
        "机构",
        "本条直接定义尚书省户部为六部之一；与三司户部区分。",
        quotation=main,
    )
    tang = tp(
        w,
        eid,
        "唐贞观二十三年",
        "民部改称户部",
        i,
        origin,
        "尚书省六部",
        "建立尚书省户部唐代始称节点。",
        "职源",
        chain="none",
    )
    song = tp(
        w,
        eid,
        "宋前期",
        "职权为三司所占，本部为空架子，仅掌贡物陈列等少量事务",
        i,
        duty,
        "尚书省六部",
        "建立尚书省户部宋前期节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判户部事与令史编制。", "编制")
    reform = tp(
        w,
        eid,
        "北宋元丰五年五月",
        "罢三司职归户部，掌全国户口、土地、钱谷、赋役政令",
        i,
        duty,
        "尚书省六部",
        "建立尚书省户部元丰恢复实职节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰户部五司与官额。", "编制")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        aliases,
        "简称与拟古称谓仅作制度证据，不另建实体。",
        "简称与别名",
        note="纯简称与拟古称谓",
    )
    chain_all(w, eid, [tang, song, reform], "连接尚书省户部唐代、宋前期与元丰节点。")
    rel(
        w,
        ft(w, fe(w, "尚书省", "机构"), "宋前期"),
        song,
        "上下级机构",
        i,
        main,
        "尚书省户部为尚书省六部之一。",
    )
    rel(
        w,
        ft(w, fe(w, "尚书省", "机构"), "北宋元丰新制"),
        reform,
        "上下级机构",
        i,
        main,
        "元丰恢复实职后的户部仍属尚书省。",
    )
    rel(
        w,
        ft(w, fe(w, "尚书省六部", "机构"), "宋代"),
        song,
        "统称与实例",
        i,
        main,
        "尚书省六部包括户部。",
    )
    rel(
        w,
        ft(w, fe(w, "三司", "机构"), "北宋元丰五年五月"),
        reform,
        "前后演变",
        i,
        duty,
        "元丰罢三司，财政职权归尚书省户部。",
        "职掌",
    )
    w.commit()


def entry1062():
    i = 1062
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity(
        "判尚书省户部事",
        "官职",
        "本条职源、职掌直接定义判尚书省户部事。",
        quotation=duty,
    )
    tang = tp(
        w,
        eid,
        "唐代",
        "已有判户部事之名",
        i,
        origin,
        "户部差遣官",
        "建立判尚书省户部事唐代职源节点。",
        "职源",
        chain="none",
    )
    song = tp(
        w,
        eid,
        "宋前期",
        "以两制以上朝官充，掌贡物、朝会陈列及旌表等杂事",
        i,
        duty,
        "户部差遣官",
        "建立判尚书省户部事宋前期节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", song, i, grade, "补证以本官决定官品。", "官品")
    cite(
        w,
        "Timepoints",
        song,
        i,
        aliases,
        "简称字段明确尚书省判户部事与三司户部判官不同。",
        "简称与别名",
        note="制度辨析；纯简称不另建实体",
    )
    chain_all(w, eid, [tang, song], "连接判尚书省户部事唐代与宋前期节点。")
    rel(
        w,
        ft(w, fe(w, "尚书省户部", "机构"), "宋前期"),
        song,
        "编制隶属",
        i,
        aliases,
        "宋前期尚书省户部置判部事一人；与三司户部判官不同。",
        "简称与别名",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def entry1063():
    i = 1063
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "户部尚书", "官职")
    qi = tp(
        w,
        eid,
        "南朝齐",
        "度支尚书为旧名，领度支、金部、仓部、起部四曹",
        i,
        origin,
        "户部长官",
        "建立户部尚书南朝齐职源节点。",
        "职源",
        chain="none",
    )
    sui = tp(
        w,
        eid,
        "隋开皇三年",
        "旧称民部尚书，为唐宋户部尚书前身",
        i,
        origin,
        "户部长官",
        "建立户部尚书隋代职源节点。",
        "职源",
        chain="none",
    )
    song = refine(
        w,
        ft_any(w, eid, "宋代", "宋前期"),
        i,
        duty,
        "据专条细化为宋前期阶官节点。",
        "职掌",
        time="宋前期",
        event="无职事，为文臣迁转寄禄官阶",
        category="文臣迁转官阶",
        grade="正三品",
    )
    cite(w, "Timepoints", song, i, main, "正文补证宋前期为阶官。")
    cite(w, "Timepoints", song, i, grade, "补证宋前期正三品。", "官品")
    reform = tp(
        w,
        eid,
        "北宋元丰五年五月",
        "始掌户部事，为一部长官，总军国用度与州县废置升降",
        i,
        duty,
        "户部长官",
        "建立户部尚书元丰职事官节点。",
        "职掌",
        chain="none",
        attr_grade="从二品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从二品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。", "简称与别名", note="纯简称")
    chain_all(w, eid, [qi, sui, song, reform], "重建户部尚书南朝齐至元丰完整时间链。")
    for office_time, role_time in (("宋前期", "宋前期"), ("北宋元丰五年五月", "北宋元丰五年五月")):
        rel(
            w,
            ft(w, fe(w, "尚书省户部", "机构"), office_time),
            ft(w, eid, role_time),
            "编制隶属",
            i,
            duty,
            "户部尚书为尚书省户部长官。",
            "职掌",
            staff_quota=1,
            staff_type="官",
        )
    w.commit()


def entry1064():
    i = 1064
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称")
    general_origin = field(963, "职源与沿革")
    w = W(i)
    eid = fe(w, "权户部尚书", "官职")
    conflicting = tp(
        w,
        eid,
        "北宋元祐三年闰十二月十八日",
        "本条记始置，用以位置资格未及的新进之士",
        i,
        origin,
        "权摄户部长官",
        "保留权户部尚书专条十八日始置异文。",
        "职源",
        chain="none",
        attr_grade="正三品",
    )
    mark_citation_conflict(
        w,
        "Timepoints",
        conflicting,
        i,
        origin,
        "始置日异文：本条作闰十二月十八日，总条作二十八日。",
        "标记权户部尚书十八日始置说。",
        "职源",
    )
    established = ft(w, eid, "北宋元祐三年闰十二月二十八日")
    mark_citation_conflict(
        w,
        "Timepoints",
        established,
        963,
        general_origin,
        "第1064条职源另作闰十二月十八日。",
        "回标权户部尚书二十八日节点与专条异文冲突。",
        "职源与沿革",
    )
    cite(w, "Timepoints", conflicting, i, main, "正文补证为职事官。")
    cite(w, "Timepoints", conflicting, i, duty, "补证职掌与户部尚书同。", "职掌")
    cite(w, "Timepoints", conflicting, i, grade, "补证正三品。", "官品")
    cite(w, "Timepoints", conflicting, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    chain_all(w, eid, [conflicting, established], "连接权户部尚书两种始置日异文。")
    for tid in (conflicting, established):
        rel(
            w,
            ft(w, fe(w, "尚书省户部", "机构"), "北宋元丰五年五月"),
            tid,
            "编制隶属",
            i,
            origin,
            "权户部尚书为户部长官权官。",
            "职源",
            staff_type="官",
        )
    w.commit()


def entry1065():
    i = 1065
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "户部侍郎", "官职")
    sui = tp(
        w,
        eid,
        "隋大业三年",
        "始置民部侍郎",
        i,
        origin,
        "户部副长官",
        "建立户部侍郎隋代职源节点。",
        "职源",
        chain="none",
    )
    tang = tp(
        w,
        eid,
        "唐高宗即位初",
        "民部侍郎改称户部侍郎",
        i,
        origin,
        "户部副长官",
        "建立户部侍郎唐代始称节点。",
        "职源",
        chain="none",
    )
    song = refine(
        w,
        ft_any(w, eid, "北宋元丰改制前", "宋前期"),
        i,
        duty,
        "据专条细化宋前期阶官节点。",
        "职掌",
        time="宋前期",
        event="无职事，为文臣迁转寄禄官阶",
        category="文臣迁转官阶",
        grade="正四品下",
    )
    cite(w, "Timepoints", song, i, main, "正文补证兼有阶官名性质。")
    cite(w, "Timepoints", song, i, grade, "补证宋前期正四品下。", "官品")
    reform = tp(
        w,
        eid,
        "北宋元丰五年五月",
        "改为户部副长官二员，其中一员专管右曹",
        i,
        duty,
        "户部副长官",
        "建立户部侍郎元丰职事官节点。",
        "职掌",
        chain="none",
        attr_grade="从三品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从三品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。", "简称与别名", note="纯简称")
    chain_all(w, eid, [sui, tang, song, reform], "重建户部侍郎隋至元丰完整时间链。")
    rel(
        w,
        ft(w, fe(w, "尚书省户部", "机构"), "北宋元丰五年五月"),
        reform,
        "编制隶属",
        i,
        duty,
        "元丰户部置侍郎二员。",
        "职掌",
        staff_quota=2,
        staff_type="官",
    )
    w.commit()


def entry1070():
    i = 1070
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "户部司", "机构")
    sui = tp(
        w,
        eid,
        "隋",
        "前身为度支尚书所领民部司",
        i,
        origin,
        "尚书省户部属司",
        "建立户部司隋代职源节点。",
        "职源",
        chain="none",
    )
    tang = tp(
        w,
        eid,
        "唐贞观二十三年",
        "民部司改为户部司",
        i,
        origin,
        "尚书省户部属司",
        "建立户部司唐代始称节点。",
        "职源",
        chain="none",
    )
    song = refine(
        w,
        ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"),
        i,
        duty,
        "据专条细化户部司宋前期无职事。",
        "职掌",
        time="宋前期",
        event="无职事",
        category="尚书省户部属司",
    )
    cite(w, "Timepoints", song, i, main, "正文补证户部司为官司，又称户部头司。")
    reform = tp(
        w,
        eid,
        "北宋元丰新制",
        "恢复职事并分为左曹、右曹，二曹合称户部司",
        i,
        duty,
        "尚书省户部属司",
        "建立户部司元丰分曹节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰及宋代左、右曹郎官编制。", "编制")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    jingkang = tp(
        w,
        eid,
        "北宋靖康年间",
        "左曹郎官一员、右曹郎官二员，为特例",
        i,
        staff,
        "尚书省户部属司",
        "建立靖康特例编制节点。",
        "编制",
        chain="none",
    )
    south = tp(
        w,
        eid,
        "南宋",
        "左、右曹郎官各一员，总名户部郎官",
        i,
        staff,
        "尚书省户部属司",
        "建立南宋户部司编制节点。",
        "编制",
        chain="none",
    )
    chain_all(w, eid, [sui, tang, song, reform, jingkang, south], "重建户部司隋至南宋完整时间链。")

    parent = ft(w, fe(w, "尚书省户部", "机构"), "北宋元丰五年五月")
    rel(w, parent, reform, "上下级机构", i, duty, "元丰户部司为尚书省户部属司。", "职掌")
    for title, event in (
        ("户部左曹", "掌户口、赋税等政令"),
        ("户部右曹", "掌常平、青苗、役法、坊场等政令"),
    ):
        sub_e = w.entity(title, "机构", f"职掌字段明确户部司分{title}。", quotation=duty)
        sub_t = tp(
            w,
            sub_e,
            "北宋元丰新制",
            event,
            i,
            duty,
            "尚书省户部属司",
            f"建立{title}元丰节点。",
            "职掌",
        )
        rel(w, reform, sub_t, "统称与实例", i, duty, f"元丰户部司包括{title}。", "职掌")
        rel(w, parent, sub_t, "上下级机构", i, duty, f"{title}隶尚书省户部。", "职掌")
    w.commit()


def entry1066():
    i = 1066
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "户部左曹侍郎",
        "官职",
        "本条直接定义户部左曹侍郎为户部侍郎分工称。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋元丰五年五月",
        "户部侍郎分工称，佐尚书通掌除右曹外本部事务",
        i,
        main,
        "户部副长官",
        "建立户部左曹侍郎元丰节点。",
        attr_grade="从三品",
    )
    rel(
        w,
        ft(w, fe(w, "户部左曹", "机构"), "北宋元丰新制"),
        start,
        "编制隶属",
        i,
        main,
        "户部左曹侍郎为户部侍郎分工称。",
        staff_quota=1,
        staff_type="官",
    )
    rel(
        w,
        ft(w, fe(w, "户部侍郎", "官职"), "北宋元丰五年五月"),
        start,
        "统称与实例",
        i,
        main,
        "户部左曹侍郎是户部侍郎的分工称。",
    )
    w.commit()


def entry1067():
    i = 1067
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "户部右曹侍郎",
        "官职",
        "本条直接定义户部右曹侍郎为户部侍郎分工称。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋元丰五年五月",
        "户部侍郎分工称，掌领户部右曹事",
        i,
        origin,
        "户部副长官",
        "建立户部右曹侍郎元丰节点。",
        "职源",
        chain="none",
        attr_grade="从三品",
    )
    cite(w, "Timepoints", start, i, duty, "补证右曹侍郎职掌。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证元丰后从三品。", "官品")
    special = tp(
        w,
        eid,
        "北宋绍圣三年",
        "专领右曹，户部尚书不得干预",
        i,
        origin,
        "户部副长官",
        "建立绍圣三年专领右曹节点。",
        "职源",
        chain="none",
        attr_grade="从三品",
    )
    end = tp(
        w,
        eid,
        "南宋绍兴四年七月",
        "两侍郎通治左、右曹，不再分称左、右曹侍郎",
        i,
        origin,
        "户部副长官",
        "建立南宋停止分称节点。",
        "职源",
        chain="none",
        attr_grade="从三品",
    )
    cite(w, "Timepoints", start, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    chain_all(w, eid, [start, special, end], "连接户部右曹侍郎元丰、绍圣及南宋节点。")
    rel(
        w,
        ft(w, fe(w, "户部右曹", "机构"), "北宋元丰新制"),
        start,
        "编制隶属",
        i,
        origin,
        "元丰户部右曹由右曹侍郎分管。",
        "职源",
        staff_quota=1,
        staff_type="官",
    )
    rel(
        w,
        ft(w, fe(w, "户部侍郎", "官职"), "北宋元丰五年五月"),
        start,
        "统称与实例",
        i,
        origin,
        "户部右曹侍郎是户部侍郎的分工称。",
        "职源",
    )

    left_e = fe(w, "户部左曹侍郎", "官职")
    left_start = ft(w, left_e, "北宋元丰五年五月")
    left_end = tp(
        w,
        left_e,
        "南宋绍兴四年七月",
        "两侍郎通治左、右曹，不再分称左、右曹侍郎",
        i,
        origin,
        "户部副长官",
        "据右曹侍郎专条补建左曹侍郎停止分称节点。",
        "职源",
        chain="none",
        attr_grade="从三品",
    )
    chain_all(w, left_e, [left_start, left_end], "连接户部左曹侍郎元丰与南宋停止分称节点。")
    w.commit()


def entry1068():
    i = 1068
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    w = W(i)
    eid = fe(w, "权户部侍郎", "官职")
    tid = refine(
        w,
        ft_any(w, eid, "北宋元祐二年", "北宋元祐二年七月四日"),
        i,
        origin,
        "专条给出权户部侍郎精确始置日期。",
        "职源",
        time="北宋元祐二年七月四日",
        event="始置，非侍从官除户部侍郎者带权字",
        category="权摄户部副长官",
    )
    cite(w, "Timepoints", tid, i, main, "正文补证为职事官。")
    cite(w, "Timepoints", tid, i, duty, "补证职掌与户部侍郎同及带权条件。", "职掌")
    rel(
        w,
        ft(w, fe(w, "尚书省户部", "机构"), "北宋元丰五年五月"),
        tid,
        "编制隶属",
        i,
        duty,
        "权户部侍郎为户部侍郎权官。",
        "职掌",
        staff_type="官",
    )
    w.commit()


def entry1069():
    i = 1069
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "户部五司",
        "机构",
        "本条直接定义元丰新制户部五司总名。",
        quotation=main,
    )
    group = tp(
        w,
        eid,
        "北宋元丰新制",
        "户部左曹、右曹、度支司、金部司、仓部司的总称",
        i,
        main,
        "机构合称",
        "建立户部五司总称节点。",
    )
    parent = ft(w, fe(w, "尚书省户部", "机构"), "北宋元丰五年五月")
    specs = [
        ("户部左曹", "北宋元丰新制"),
        ("户部右曹", "北宋元丰新制"),
    ]
    for title in ("度支司", "金部司", "仓部司"):
        sub_e = fe(w, title, "机构")
        existing = current_chain(w, sub_e)
        sub_t = tp(
            w,
            sub_e,
            "北宋元丰新制",
            "尚书省户部五司之一，恢复专司职事",
            i,
            main,
            "尚书省户部属司",
            f"据户部五司总条建立{title}元丰节点。",
            chain="none",
        )
        if sub_t not in existing:
            existing.append(sub_t)
        chain_all(w, sub_e, existing, f"将{title}元丰节点接入既有完整时间链。")
        specs.append((title, "北宋元丰新制"))
        rel(w, parent, sub_t, "上下级机构", i, main, f"{title}为尚书省户部五司之一。")
    for title, time in specs:
        target = ft(w, fe(w, title, "机构"), time)
        cite(w, "Timepoints", target, i, main, f"补证{title}属于户部五司。")
        rel(w, group, target, "统称与实例", i, main, f"户部五司包括{title}。")
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(1051, 1071)] == [
        "考功司员外郎",
        "考功司十七案",
        "主管尚书省吏部架阁文字",
        "尚书省制造官告局",
        "主管尚书省制造官告局",
        "官告局",
        "尚书省官告院",
        "官告院",
        "官告院绫纸库",
        "主管官告院",
        "尚书省户部",
        "判尚书省户部事",
        "户部尚书",
        "权户部尚书",
        "户部侍郎",
        "户部左曹侍郎",
        "户部右曹侍郎",
        "权户部侍郎",
        "户部五司",
        "户部司",
    ]
    entry1051()
    entry1052()
    entry1053()
    entry1054()
    entry1055()
    # 第1056条“官告局”为纯简称空占位，不凭标题造实体。
    entry1057()
    entry1058()
    entry1059()
    entry1060()
    entry1061()
    entry1062()
    entry1063()
    entry1064()
    entry1065()
    entry1070()
    entry1066()
    entry1067()
    entry1068()
    entry1069()


if __name__ == "__main__":
    main()
