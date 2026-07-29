#!/usr/bin/env python3
"""提取 chapter2t4 第1031–1050条：吏部四选、七司及司封司等。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(1031, 1051)}
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


def full_field(i, field):
    return Q(i, x.b.F[i]["fields"][field], field)


def ft_any(w, entity_id, *times):
    for time in times:
        timepoint_id = w.find_timepoint(entity_id, time)
        if timepoint_id is not None:
            return timepoint_id
    raise AssertionError((entity_id, times))


def office(i, parent_title, title, event, definition):
    main = Q(i, x.b.F[i]["text"])
    intro = Q(i, definition)
    w = W(i)
    eid = w.entity(
        title,
        "机构",
        f"第{i}条直接定义{title}为{parent_title}办事部门。",
        quotation=intro,
    )
    tid = tp(
        w,
        eid,
        "北宋元丰五年五月",
        event,
        i,
        main,
        f"{parent_title}办事机构",
        f"原文未另载时间，按所属{parent_title}始置时间承载{title}职掌。",
    )
    rel(
        w,
        ft(w, fe(w, parent_title, "机构"), "北宋元丰五年五月"),
        tid,
        "上下级机构",
        i,
        intro,
        f"原文明确{title}为{parent_title}办事部门。",
    )
    w.commit()


def entry1031_1033():
    specs = (
        (
            1031,
            "吏部侍郎右选甲库案",
            "掌武臣符牒，验证转官人履历、相貌并发给制作官告或宣札的签符",
            "吏部侍郎右选常设办事部门之一。",
        ),
        (
            1032,
            "吏部侍郎右选法司案",
            "掌本选法令条例检阅，防止吏人舞文作弊",
            "吏部侍郎右选常设办事部门之一。",
        ),
        (
            1033,
            "吏部侍郎右选架阁案",
            "掌本选已结二年以上文书的保存、登记、管理和调阅",
            "吏部侍郎右选档案管理部门。",
        ),
    )
    for spec in specs:
        office(spec[0], "吏部侍郎右选", *spec[1:])


def institution_core(
    i,
    title,
    origin_time,
    origin_event,
    song_event,
    reform_event,
    *,
    later_nodes=(),
):
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源" if "职源" in x.b.F[i]["fields"] else "职源与沿革")
    duty = full_field(i, "职掌")
    staff = full_field(i, "编制")
    w = W(i)
    eid = fe(w, title, "机构")
    origin_t = tp(
        w,
        eid,
        origin_time,
        origin_event,
        i,
        origin,
        "尚书省吏部属司",
        f"据{title}专条建立宋前职源节点。",
        "职源" if "职源" in x.b.F[i]["fields"] else "职源与沿革",
        chain="none",
    )
    song_t = refine(
        w,
        ft(w, eid, "宋代（尚书二十四司）"),
        i,
        duty,
        f"据{title}专条细化宋前期职掌。",
        "职掌",
        event=song_event,
        category="尚书省吏部属司",
    )
    cite(w, "Timepoints", song_t, i, main, f"正文补证{title}为官司。")
    reform_t = tp(
        w,
        eid,
        "北宋元丰新制",
        reform_event,
        i,
        duty,
        "尚书省吏部属司",
        f"建立{title}元丰振职节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", reform_t, i, staff, f"补证{title}元丰编制。", "编制")
    ordered = [origin_t, song_t, reform_t]
    for time, event, quotation, field in later_nodes:
        later = tp(
            w,
            eid,
            time,
            event,
            i,
            quotation,
            "尚书省吏部属司",
            f"建立{title}{time}沿革节点。",
            field,
            chain="none",
        )
        ordered.append(later)
    chain_all(w, eid, ordered, f"重建{title}宋前至宋代的完整时间链。")
    parent = ft(w, fe(w, "吏部", "机构"), "北宋元丰改制后")
    rel(
        w,
        parent,
        reform_t,
        "上下级机构",
        i,
        duty,
        f"元丰改制后{title}归吏部。",
        "职掌",
    )
    w.commit()
    return reform_t


def entry1036():
    i = 1036
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源")
    duty = full_field(i, "职掌")
    staff = full_field(i, "编制")
    aliases = full_field(i, "简称")
    w = W(i)
    eid = fe(w, "吏部司", "机构")
    sui = tp(
        w,
        eid,
        "隋初",
        "尚书省吏部统吏部、主爵、司勋、考功四司",
        i,
        origin,
        "尚书省吏部属司",
        "建立吏部司隋代职源节点。",
        "职源",
        chain="none",
    )
    song = refine(
        w,
        ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"),
        i,
        duty,
        "专条细化吏部司宋前期无职掌。",
        "职掌",
        event="宋前期无职掌",
        category="尚书省吏部属司",
    )
    cite(w, "Timepoints", song, i, main, "正文补证吏部司为官司。")
    reform = tp(
        w,
        eid,
        "北宋元丰新制",
        "本司徒存其名；郎中、员外郎分掌四选，不在吏部七司之内",
        i,
        duty,
        "尚书省吏部属司",
        "建立吏部司元丰后存名而无独立司职节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证四选郎官共四员。", "编制")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        aliases,
        "简称字段仅作称谓和互证，不据简称另建实体。",
        "简称",
        note="纯简称",
    )
    chain_all(w, eid, [sui, song, reform], "连接吏部司隋代、宋前期与元丰节点。")
    w.commit()


def entry1037():
    i = 1037
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源与沿革")
    duty = full_field(i, "职掌")
    grade = full_field(i, "品位")
    aliases = full_field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "吏部司郎中", "官职")
    wei = tp(
        w,
        eid,
        "北魏太和二十三年",
        "始置尚书吏部郎中",
        i,
        origin,
        "吏部郎官",
        "建立吏部司郎中北魏职源节点。",
        "职源与沿革",
        chain="none",
    )
    liang = tp(
        w,
        eid,
        "南朝梁",
        "称尚书省吏部郎",
        i,
        origin,
        "吏部郎官",
        "建立南朝梁称谓沿革节点。",
        "职源与沿革",
        chain="none",
    )
    tang = tp(
        w,
        eid,
        "唐初",
        "确立尚书省吏部吏部司郎中之名",
        i,
        origin,
        "吏部郎官",
        "建立唐初官名沿革节点。",
        "职源与沿革",
        chain="none",
    )
    song = refine(
        w,
        ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"),
        i,
        duty,
        "据专条改为宋前期阶官节点并纠正品位。",
        "职掌",
        time="宋前期",
        event="无职事，为文臣迁转的前行郎中阶",
        category="文臣迁转官阶",
        grade="从五品上",
    )
    cite(w, "Timepoints", song, i, main, "正文补证兼有阶官名性质。")
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "品位")
    reform = tp(
        w,
        eid,
        "北宋元丰新制",
        "改为职事官，四员分别主管尚书、侍郎左、右四选",
        i,
        duty,
        "吏部四选郎官",
        "建立吏部司郎中元丰职事官节点。",
        "职掌",
        chain="none",
        attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品及郎中资序。", "品位")
    south = tp(
        w,
        eid,
        "南宋绍兴三十一年以后",
        "四选郎官正式使用尚左、尚右、侍左、侍右等职衔",
        i,
        aliases,
        "吏部四选郎官",
        "建立南宋四选郎官职衔变化节点。",
        "简称与别名",
        chain="none",
        attr_grade="从六品",
    )
    chain_all(
        w,
        eid,
        [wei, liang, tang, song, reform, south],
        "重建吏部司郎中北魏至南宋完整时间链。",
    )
    rel(
        w,
        ft(w, fe(w, "吏部司", "机构"), "北宋元丰新制"),
        reform,
        "编制隶属",
        i,
        duty,
        "元丰后吏部司郎中为分掌四选的吏部郎官。",
        "职掌",
        staff_type="官",
    )
    w.commit()


def entry1039():
    i = 1039
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源与沿革")
    duty = full_field(i, "职掌")
    grade = full_field(i, "品位")
    aliases = full_field(i, "简称")
    w = W(i)
    eid = w.entity(
        "吏部司员外郎",
        "官职",
        "本条直接定义吏部司员外郎为官阶名、职事官名。",
        quotation=main,
    )
    sui = tp(
        w,
        eid,
        "隋开皇六年",
        "始置",
        i,
        origin,
        "吏部郎官",
        "建立吏部司员外郎隋代职源节点。",
        "职源与沿革",
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
        "建立吏部司员外郎宋前期阶官节点。",
        "职掌",
        chain="none",
        attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "品位")
    reform = tp(
        w,
        eid,
        "北宋元丰新制",
        "改为职事官，与郎中同为分掌尚左、尚右、侍左、侍右四选的郎官",
        i,
        duty,
        "吏部四选郎官",
        "建立元丰职事官节点。",
        "职掌",
        chain="none",
        attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品及员外郎资序。", "品位")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        aliases,
        "简称字段补证四选郎官称谓；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    chain_all(w, eid, [sui, song, reform], "连接吏部司员外郎隋、宋前期和元丰节点。")
    rel(
        w,
        ft(w, fe(w, "吏部司", "机构"), "北宋元丰新制"),
        reform,
        "编制隶属",
        i,
        duty,
        "元丰后吏部司员外郎为分掌四选的吏部郎官。",
        "职掌",
        staff_type="官",
    )
    w.commit()


def create_reform_role(i, institution, title, event, quotation, grade=None):
    w = W(i)
    eid = w.entity(
        title,
        "官职",
        f"{institution}编制字段明列{title}。",
        quotation=quotation,
    )
    tid = tp(
        w,
        eid,
        "北宋元丰新制",
        event,
        i,
        quotation,
        f"{institution}郎官",
        f"据{institution}总条建立{title}元丰节点。",
        "编制",
        chain="none",
        attr_grade=grade,
    )
    rid = rel(
        w,
        ft(w, fe(w, institution, "机构"), "北宋元丰新制"),
        tid,
        "编制隶属",
        i,
        quotation,
        f"元丰{institution}置{title}一人。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()
    return eid, tid, rid


def entry1040():
    i = 1040
    staff = full_field(i, "编制")
    institution_core(
        i,
        "司封司",
        "唐高宗龙朔元年",
        "始置司封司之名",
        "宋沿置；宋前期职事甚微，仅在议谥前通知本部人吏赴会",
        "职事振举，掌官员封爵、赠官、奏荫、封号承袭等事",
    )
    create_reform_role(i, "司封司", "司封司郎中", "本司司长一人", staff, "从六品")
    create_reform_role(i, "司封司", "司封司员外郎", "本司副贰一人", staff, "正七品")


def judge_entry(i, institution, title, event):
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        title,
        "官职",
        f"本条直接定义{title}为宋前期差遣官。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "宋前期",
        event,
        i,
        main,
        f"{institution}差遣官",
        f"建立{title}宋前期节点。",
        chain="none",
    )
    rel(
        w,
        ft(w, fe(w, institution, "机构"), "宋代（尚书二十四司）"),
        tid,
        "编制隶属",
        i,
        main,
        f"宋前期{institution}另差{title}一人。",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def entry1042():
    i = 1042
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源")
    duty = full_field(i, "职掌")
    grade = full_field(i, "官品")
    staff = full_field(i, "编制")
    aliases = full_field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "司封司郎中", "官职")
    tang = tp(
        w,
        eid,
        "唐武则天光宅元年",
        "始有尚书省司封司郎中之名",
        i,
        origin,
        "司封司郎官",
        "建立司封司郎中唐代职源节点。",
        "职源",
        chain="none",
    )
    song = refine(
        w,
        ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"),
        i,
        duty,
        "据专条改为宋前期阶官节点并纠正品位。",
        "职掌",
        time="宋前期",
        event="无职事，为文臣迁转的前行郎中阶",
        category="文臣迁转官阶",
        grade="从五品上",
    )
    cite(w, "Timepoints", song, i, main, "正文补证兼有阶官名性质。")
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = refine(
        w,
        ft(w, eid, "北宋元丰新制"),
        i,
        duty,
        "专条细化司封司郎中元丰职掌。",
        "职掌",
        event="为本司司长，掌官员封爵、赠官、封号承袭及命妇封号等",
        category="司封司长官",
        grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "补证简称；不据简称另建实体。", "简称与别名", note="纯简称")
    chain_all(w, eid, [tang, song, reform], "重建司封司郎中唐至元丰完整时间链。")
    rid = relation_id(
        w, "司封司", "司封司郎中", "编制隶属", "北宋元丰新制", "北宋元丰新制"
    )
    assert rid
    cite(
        w,
        "Relationships",
        rid,
        i,
        staff,
        "专条称郎中或员外郎一人，与司封司总条各一人表述冲突。",
        "编制",
        note="员额冲突：总条称郎中、员外郎各一人；专条称郎中或员外郎一人",
        conflict_flag=1,
    )
    w.commit()


def entry1043():
    i = 1043
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源与沿革")
    grade = full_field(i, "官品")
    aliases = full_field(i, "简称")
    w = W(i)
    eid = fe(w, "司封司员外郎", "官职")
    song = tp(
        w,
        eid,
        "宋前期",
        "无职事，为文臣迁转的前行员外郎阶",
        i,
        origin,
        "文臣迁转官阶",
        "建立司封司员外郎宋前期阶官节点。",
        "职源与沿革",
        chain="none",
        attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, main, "正文补证兼有阶官名性质。")
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = refine(
        w,
        ft(w, eid, "北宋元丰新制"),
        i,
        origin,
        "专条细化元丰司封司副贰职掌。",
        "职源与沿革",
        event="为本司副贰，正郎缺则领本司事",
        category="司封司副长官",
        grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "补证简称；不据简称另建实体。", "简称", note="纯简称")
    chain_all(w, eid, [song, reform], "连接司封司员外郎宋前期与元丰节点。")
    w.commit()


def entry1044():
    i = 1044
    staff = full_field(i, "编制")
    institution_core(
        i,
        "司勋司",
        "隋文帝时",
        "始置，隶尚书省吏部",
        "宋沿置；宋前期无职掌，勋官之赐出于中书",
        "始振举司职，掌功勋、酬奖、审覆、赏格",
        later_nodes=(
            (
                "北宋元祐以后",
                "郎官由郎中、员外郎各一人减为一人",
                staff,
                "编制",
            ),
            (
                "南宋隆兴初",
                "省司勋郎官，由司封郎官兼领",
                staff,
                "编制",
            ),
        ),
    )
    create_reform_role(i, "司勋司", "司勋司郎中", "本司司长一人", staff, "从六品")
    create_reform_role(i, "司勋司", "司勋司员外郎", "本司副贰一人", staff, "正七品")


def entry1044_judge_conflict():
    i = 1044
    staff = full_field(i, "编制")
    w = W(i)
    rid = relation_id(
        w,
        "司勋司",
        "判司勋司事",
        "编制隶属",
        "宋代（尚书二十四司）",
        "宋前期",
    )
    assert rid
    cite(
        w,
        "Relationships",
        rid,
        i,
        staff,
        "司勋司总条误写判司封司事，与判司勋司事专条冲突。",
        "编制",
        note="原文疑误：司勋司总条写判司封司事，专条为判司勋司事",
        conflict_flag=1,
    )
    w.commit()


def entry1046():
    i = 1046
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源与沿革")
    duty = full_field(i, "职掌")
    grade = full_field(i, "官品")
    aliases = full_field(i, "简称")
    w = W(i)
    eid = fe(w, "司勋司郎中", "官职")
    tang = tp(
        w,
        eid,
        "唐武德初",
        "称尚书省吏部司勋司郎中",
        i,
        origin,
        "司勋司郎官",
        "建立司勋司郎中唐代职源节点。",
        "职源与沿革",
        chain="none",
    )
    song = refine(
        w,
        ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"),
        i,
        duty,
        "据专条改为宋前期阶官节点并纠正品位。",
        "职掌",
        time="宋前期",
        event="无职事，为文臣迁转的前行郎中阶",
        category="文臣迁转官阶",
        grade="从五品上",
    )
    cite(w, "Timepoints", song, i, main, "正文补证兼有阶官名性质。")
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = refine(
        w,
        ft(w, eid, "北宋元丰新制"),
        i,
        duty,
        "专条细化司勋司郎中元丰职掌。",
        "职掌",
        event="为本司司长，掌功勋、酬奖、审覆、赏格",
        category="司勋司长官",
        grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "补证简称；不据简称另建实体。", "简称", note="纯简称")
    abolished = tp(
        w,
        eid,
        "南宋隆兴元年",
        "裁省，由司封郎官兼领司勋司事",
        i,
        aliases,
        "司勋司郎官",
        "建立南宋裁省节点。",
        "简称",
        chain="none",
        attr_grade="从六品",
    )
    chain_all(w, eid, [tang, song, reform, abolished], "重建司勋司郎中唐至南宋完整时间链。")
    w.commit()


def entry1047():
    i = 1047
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源与沿革")
    duty = full_field(i, "职掌")
    grade = full_field(i, "官品")
    staff = full_field(i, "编制")
    aliases = full_field(i, "简称")
    w = W(i)
    eid = fe(w, "司勋司员外郎", "官职")
    sui = tp(
        w,
        eid,
        "隋开皇六年",
        "始有尚书省吏部司勋司员外郎之名",
        i,
        origin,
        "司勋司郎官",
        "建立司勋司员外郎隋代职源节点。",
        "职源与沿革",
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
        "建立司勋司员外郎宋前期阶官节点。",
        "职掌",
        chain="none",
        attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, main, "正文补证兼有阶官名性质。")
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = refine(
        w,
        ft(w, eid, "北宋元丰新制"),
        i,
        duty,
        "专条细化元丰司勋司副贰职掌。",
        "职掌",
        event="为本司副贰，正郎缺则总领本司事",
        category="司勋司副长官",
        grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        staff,
        "编制字段把司勋误写成司封，保留原文并标记疑误。",
        "编制",
        note="原文疑误：司勋司员外郎条写作司封郎中或司封员外郎",
        conflict_flag=1,
    )
    cite(w, "Timepoints", reform, i, aliases, "补证简称；不据简称另建实体。", "简称", note="纯简称")
    abolished = tp(
        w,
        eid,
        "南宋隆兴元年",
        "裁省，由司封郎官兼领司勋司事",
        i,
        staff,
        "司勋司郎官",
        "建立南宋裁省节点。",
        "编制",
        chain="none",
        attr_grade="正七品",
    )
    chain_all(w, eid, [sui, song, reform, abolished], "连接司勋司员外郎隋至南宋节点。")
    w.commit()


def entry1048():
    institution_core(
        1048,
        "考功司",
        "隋",
        "始有尚书省吏部考功司之名",
        "北宋、南宋沿置；宋前期掌覆审谥名及幕职州县官、流外官考课",
        "掌文武选官升迁、变动、磨勘、资任、考课政令",
    )


def entry1050():
    i = 1050
    main = Q(i, x.b.F[i]["text"])
    origin = full_field(i, "职源与沿革")
    duty = full_field(i, "职掌")
    grade = full_field(i, "官品")
    aliases = full_field(i, "简称")
    w = W(i)
    eid = fe(w, "考功司郎中", "官职")
    tang = tp(
        w,
        eid,
        "唐武德三年",
        "始置尚书省吏部考功司郎中",
        i,
        origin,
        "考功司郎官",
        "建立考功司郎中唐代职源节点。",
        "职源与沿革",
        chain="none",
    )
    song = refine(
        w,
        ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"),
        i,
        duty,
        "据专条改为宋前期阶官节点并纠正品位。",
        "职掌",
        time="宋前期",
        event="无职事，为文臣迁转的前行郎中阶",
        category="文臣迁转官阶",
        grade="从五品上",
    )
    cite(w, "Timepoints", song, i, main, "正文补证兼有阶官名性质。")
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w,
        eid,
        "北宋元丰新制",
        "为本司司长，掌文武官叙迁、磨勘、资任、考课等政令",
        i,
        duty,
        "考功司长官",
        "建立考功司郎中元丰职事节点。",
        "职掌",
        chain="none",
        attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "补证简称；不据简称另建实体。", "简称", note="纯简称")
    chain_all(w, eid, [tang, song, reform], "重建考功司郎中唐至元丰完整时间链。")
    rel(
        w,
        ft(w, fe(w, "考功司", "机构"), "北宋元丰新制"),
        reform,
        "编制隶属",
        i,
        duty,
        "元丰考功司郎中为本司司长。",
        "职掌",
        staff_type="官",
    )
    w.commit()


def entry1034():
    i = 1034
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "吏部四选",
        "机构",
        "本条直接定义元丰改制后吏部四选的总称。",
        quotation=main,
    )
    group = tp(
        w,
        eid,
        "北宋元丰改制后",
        "吏部尚书左、右选与侍郎左、右选的总称",
        i,
        main,
        "机构合称",
        "建立吏部四选总称节点。",
    )
    for title in (
        "吏部尚书左选",
        "吏部尚书右选",
        "吏部侍郎左选",
        "吏部侍郎右选",
    ):
        target = ft(w, fe(w, title, "机构"), "北宋元丰五年五月")
        cite(w, "Timepoints", target, i, main, f"补证{title}属于吏部四选。")
        rel(w, group, target, "统称与实例", i, main, f"吏部四选包括{title}。")
    w.commit()


def entry1035():
    i = 1035
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "吏部七司",
        "机构",
        "本条直接定义元丰改制后吏部七司的总称。",
        quotation=main,
    )
    group = tp(
        w,
        eid,
        "北宋元丰改制后",
        "四选与司封司、司勋司、考功司的总称",
        i,
        main,
        "机构合称",
        "建立吏部七司总称节点。",
    )
    specs = (
        ("吏部尚书左选", "北宋元丰五年五月"),
        ("吏部尚书右选", "北宋元丰五年五月"),
        ("吏部侍郎左选", "北宋元丰五年五月"),
        ("吏部侍郎右选", "北宋元丰五年五月"),
        ("司封司", "北宋元丰新制"),
        ("司勋司", "北宋元丰新制"),
        ("考功司", "北宋元丰新制"),
    )
    for title, time in specs:
        target = ft(w, fe(w, title, "机构"), time)
        cite(w, "Timepoints", target, i, main, f"补证{title}属于吏部七司。")
        rel(w, group, target, "统称与实例", i, main, f"吏部七司包括{title}。")
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(1031, 1051)] == [
        "吏部侍郎右选甲库案",
        "吏部侍郎右选法司案",
        "吏部侍郎右选架阁案",
        "吏部四选",
        "吏部七司",
        "吏部司",
        "吏部司郎中",
        "侍右郎官",
        "吏部司员外郎",
        "司封司",
        "判司封司事",
        "司封司郎中",
        "司封司员外郎",
        "司勋司",
        "判司勋司事",
        "司勋司郎中",
        "司勋司员外郎",
        "考功司",
        "判考功司事",
        "考功司郎中",
    ]
    entry1031_1033()
    entry1036()
    entry1037()
    # 第1038条“侍右郎官”为空占位，不凭别称标题造实体。
    entry1039()
    entry1040()
    judge_entry(
        1041,
        "司封司",
        "判司封司事",
        "以无职事朝官充，掌议谥前通知本部人吏赴会",
    )
    entry1042()
    entry1043()
    entry1044()
    judge_entry(
        1045,
        "司勋司",
        "判司勋司事",
        "以朝官一人兼差，实无职事，仅守本司",
    )
    entry1044_judge_conflict()
    entry1046()
    entry1047()
    entry1048()
    judge_entry(
        1049,
        "考功司",
        "判考功司事",
        "掌覆审太常寺拟谥及考校幕职州县官、流外官",
    )
    entry1050()
    entry1034()
    entry1035()


if __name__ == "__main__":
    main()
