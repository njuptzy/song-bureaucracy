#!/usr/bin/env python3
"""提取 chapter2t4 第991–1010条：尚书右选、吏部侍郎与侍郎左选诸案。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(991, 1011)}
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine


def ft_any(w, entity_id, *times):
    for time in times:
        timepoint_id = w.find_timepoint(entity_id, time)
        if timepoint_id is not None:
            return timepoint_id
    raise AssertionError((entity_id, times))


def right_selection_office(i, title, event, duty):
    definition = Q(i, "吏部尚书右选常设办事部门之一。")
    duty = Q(i, duty)
    w = W(i)
    eid = w.entity(
        title,
        "机构",
        f"第{i}条直接定义{title}为吏部尚书右选常设办事部门。",
        quotation=definition,
    )
    tid = tp(
        w,
        eid,
        "北宋元丰五年五月",
        event,
        i,
        duty,
        "吏部尚书右选办事机构",
        f"原文未另载时间，按所属吏部尚书右选的首个真实时间点承载{title}职掌。",
    )
    rel(
        w,
        ft(w, fe(w, "吏部尚书右选", "机构"), "北宋元丰五年五月"),
        tid,
        "上下级机构",
        i,
        definition,
        f"原文明确{title}为吏部尚书右选常设办事部门之一。",
    )
    w.commit()


def entry991():
    right_selection_office(
        991,
        "吏部尚书右选副使案",
        "掌武臣从七品诸司副使及政和二年后武功郎至武翼郎差注",
        "掌武臣从七品官差注，即诸司副使（自皇城副使至供备库副使）、"
        "政和二年后之武功郎至武翼郎的差注（《宋会要·职官》11之56）。",
    )


def entry992():
    right_selection_office(
        992,
        "吏部尚书右选敦修武案",
        "掌武臣正八品大使臣及政和二年后敦武郎、修武郎差注",
        "掌武臣正八品差注，即大使臣（内殿承旨、内殿崇班、阁门祗候）、"
        "政和二年后之敦武郎、修武郎的差注（《宋会要·职官》11之56）。",
    )


def entry993():
    right_selection_office(
        993,
        "吏部尚书右选注拟掌阙案",
        "掌武臣诸司正使、副使、大使臣官阙信息及除授手续",
        "掌武臣诸司正使、副使、大使臣的官阙信息及办理上述品官除授手续"
        "（《宋会要·职官》11之56）。",
    )


def entry994():
    right_selection_office(
        994,
        "吏部尚书右选奏荐赏功案",
        "掌奏荐、任使、诸军赏功推恩",
        "掌奏荐、任使、诸军赏功推恩（《宋会要·职官》11之56）。",
    )


def entry995():
    right_selection_office(
        995,
        "吏部尚书右选开拆案",
        "掌本选文书收发催督",
        "掌本选文书收发催督（《宋会要·职官》11之56）。",
    )


def entry996():
    right_selection_office(
        996,
        "吏部尚书右选名籍案",
        "掌本选武官名册",
        "掌本选武官名册（《宋会要·职官》11之56）。",
    )


def entry997():
    right_selection_office(
        997,
        "吏部尚书右选甲库案",
        "掌武官敕命收受、履历相貌验证、符牒出给及新除官告制作",
        "掌收受本选武官的敕命，并经验证迁转官人的履历、相貌无误之后，"
        "出给符牒等证明以制作新除命的官告（《宋会要·职官》11之56）。",
    )


def entry998():
    right_selection_office(
        998,
        "吏部尚书右选法司案",
        "掌本选法令条例检阅",
        "掌本选法令条例检阅（《宋会要·职官》11之56）。",
    )


def entry999():
    right_selection_office(
        999,
        "吏部尚书右选知杂案",
        "掌本选具体事务，近于后勤总务",
        "掌本选具体事务办理，近于后勤总务部门（《宋会要·职官》11之56）。",
    )


def entry1000():
    i = 1000
    main = Q(i, x.b.F[i]["text"])
    history = Q(i, x.b.F[i]["fields"]["职源与沿革"], "职源与沿革")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    grade = Q(i, x.b.F[i]["fields"]["官品"], "官品")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    eid = fe(w, "吏部侍郎", "官职")
    sui = tp(
        w,
        eid,
        "隋大业三年",
        "尚书省六部始各置侍郎一人",
        i,
        history,
        "六部副长官",
        "建立吏部侍郎隋代源流节点。",
        "职源与沿革",
        chain="none",
    )
    early = refine(
        w,
        ft_any(w, eid, "北宋元丰改制前", "宋前期"),
        i,
        duty,
        "专条细化宋前期吏部侍郎为无职事迁转官阶。",
        "职掌",
        time="宋前期",
        event="兼有官阶、职事官两种用法：作为官阶无职事，为文臣迁转官阶；"
        "作为职事官分掌东钰、西钰",
        category="官阶、职事官",
        grade="正四品上",
    )
    cite(w, "Timepoints", early, i, history, "补证隋置后宋沿置。", "职源与沿革")
    cite(w, "Timepoints", early, i, grade, "补证宋前期吏部侍郎正四品上。", "官品")
    cite(w, "Timepoints", early, i, main, "正文补证吏部侍郎兼具官阶与职事官性质。")
    cite(
        w,
        "Timepoints",
        early,
        i,
        aliases,
        "简称字段补证宋初吏部侍郎分掌东钰、西钰；OCR原字照录。",
        "简称与别名",
        note="纯简称不建实体；东钰、西钰为辞典OCR原字",
    )
    reform = refine(
        w,
        ft(w, eid, "北宋元丰新制"),
        i,
        duty,
        "专条细化元丰吏部侍郎为副长官、二员分领左选右选。",
        "职掌",
        event="改为吏部副长官，二员分领侍郎左选、右选",
        category="吏部副长官",
        grade="从三品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰改制后从三品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证元丰新制吏部侍郎定员二人。", "编制")
    cite(w, "Timepoints", reform, i, main, "正文补证吏部侍郎兼具官阶与职事官性质。")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        aliases,
        "全文扫描简称字段；吏侍、二铨、小天等称谓不另建实体。",
        "简称与别名",
        note="纯简称、拟古称与雅称",
    )
    chain_all(w, eid, [sui, early, reform], "连接吏部侍郎隋代、宋前期与元丰新制节点。")
    rel(
        w,
        ft(w, fe(w, "吏部", "机构"), "北宋元丰改制后"),
        reform,
        "编制隶属",
        i,
        staff,
        "元丰新制吏部侍郎定员二人，为吏部副长官。",
        "编制",
        staff_quota=2,
        staff_type="官",
    )

    rank_e = w.entity(
        "正议大夫",
        "官职",
        "职掌字段明确元丰新制后吏部侍郎旧本官阶易为寄禄官正议大夫。",
        quotation=duty,
    )
    rank_t = tp(
        w,
        rank_e,
        "北宋元丰新制",
        "承接吏部侍郎旧阶，作为寄禄官",
        i,
        duty,
        "寄禄官",
        "建立正议大夫承接吏部侍郎旧阶节点。",
        "职掌",
    )
    rel(
        w,
        early,
        rank_t,
        "前后演变",
        i,
        duty,
        "元丰新制将吏部侍郎旧阶易为寄禄官正议大夫。",
        "职掌",
    )
    w.commit()


def entry1001():
    i = 1001
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    grade = Q(i, x.b.F[i]["fields"]["品位"], "品位")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = fe(w, "权吏部侍郎", "官职")
    start = refine(
        w,
        ft_any(w, eid, "北宋元祐二年", "北宋元祐二年七月四日"),
        i,
        origin,
        "专条把权吏部侍郎始置时间细化到元祐二年七月四日。",
        "职源",
        time="北宋元祐二年七月四日",
        event="始置，用以提拔资格稍浅而有才能的新进之士；权官二年即转正",
        category="权摄吏部副长官",
        grade="从四品",
    )
    cite(w, "Timepoints", start, i, duty, "补证权吏部侍郎职掌与正任相同。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证从四品及权官二年转正制度。", "品位")
    cite(w, "Timepoints", start, i, main, "正文补证权吏部侍郎为职事官。")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证全称与省称；人物除授仅作制度证据。",
        "简称",
        note="纯简称；人物不建实体",
    )
    south = tp(
        w,
        eid,
        "南宋",
        "沿置",
        i,
        origin,
        "权摄吏部副长官",
        "建立南宋权吏部侍郎沿置节点。",
        "职源",
        chain="none",
        attr_grade="从四品",
    )
    chain_all(w, eid, [start, south], "连接权吏部侍郎元祐始置与南宋沿置节点。")
    w.commit()


def entry1002():
    i = 1002
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    flow_office = fe(w, "吏部流内铨", "机构")
    former = ft(w, flow_office, "北宋元丰三年八月十四日")
    ministry = ft(
        w,
        fe(w, "尚书吏部", "机构"),
        "北宋元丰三年八月十四日",
    )
    cite(
        w,
        "Timepoints",
        former,
        i,
        origin,
        "本条补证元丰三年八月十四日流内铨改名尚书省吏部。",
        "职源",
    )
    cite(
        w,
        "Timepoints",
        ministry,
        i,
        origin,
        "本条补证尚书省吏部承接流内铨。",
        "职源",
    )
    rel(
        w,
        former,
        ministry,
        "前后演变",
        i,
        origin,
        "元丰三年八月十四日，流内铨改为尚书省吏部。",
        "职源",
    )

    eid = fe(w, "吏部侍郎左选", "机构")
    start = refine(
        w,
        ft(w, eid, "北宋元丰五年五月"),
        i,
        origin,
        "专条补证尚书省吏部于元丰五年五月改为吏部侍郎左选。",
        "职源",
        event="由尚书省吏部改置，掌选人铨选、注授",
        category="吏部文臣铨选机构",
    )
    cite(w, "Timepoints", start, i, main, "正文补证吏部侍郎左选为吏部四选之一。")
    cite(w, "Timepoints", start, i, duty, "补证侍郎左选选授范围。", "职掌")
    cite(w, "Timepoints", start, i, staff, "补证侍郎左选官吏编制与分案数。", "编制")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证侍郎左选、左选等省称；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    rel(
        w,
        ft(w, fe(w, "尚书吏部", "机构"), "北宋元丰五年五月"),
        start,
        "前后演变",
        i,
        origin,
        "元丰五年五月尚书省吏部改为吏部侍郎左选。",
        "职源",
    )

    clerk_e = w.entity(
        "吏部侍郎左选郎中",
        "官职",
        "编制字段明确侍郎左选设郎中一人。",
        quotation=staff,
    )
    clerk_t = tp(
        w,
        clerk_e,
        "北宋元丰五年五月",
        "侍郎左选属官一人",
        i,
        staff,
        "吏部铨选官",
        "建立吏部侍郎左选郎中节点。",
        "编制",
    )
    rel(
        w,
        start,
        clerk_t,
        "编制隶属",
        i,
        staff,
        "侍郎左选置郎中一人。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def entry1003():
    i = 1003
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    grade = Q(i, x.b.F[i]["fields"]["官品"], "官品")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    eid = w.entity(
        "吏部左选侍郎",
        "官职",
        "本条直接定义吏部左选侍郎。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋元丰五年四月二十三日",
        "始除授，为吏部侍郎二员之一，分领侍郎左选",
        i,
        origin,
        "吏部副长官",
        "建立吏部左选侍郎始置节点。",
        "职源",
        attr_grade="从三品",
    )
    cite(w, "Timepoints", start, i, duty, "补证左选侍郎职掌与分工。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证左选侍郎从三品。", "官品")
    cite(w, "Timepoints", start, i, staff, "补证元丰新制两侍郎中一人为左选侍郎。", "编制")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证左选侍郎、侍左侍郎、侍左等称谓；纯简称不另建实体。",
        "简称与别名",
        note="纯简称；绍熙三年称谓变化不另建别称实体",
    )
    rel(
        w,
        ft(w, fe(w, "吏部侍郎左选", "机构"), "北宋元丰五年五月"),
        start,
        "编制隶属",
        i,
        duty,
        "吏部左选侍郎分管吏部侍郎左选；元丰两侍郎总额二人，其中左选一人。",
        "职掌",
        staff_quota=1,
        staff_type="官",
    )
    rel(
        w,
        ft(w, fe(w, "吏部侍郎", "官职"), "北宋元丰新制"),
        start,
        "统称与实例",
        i,
        staff,
        "吏部左选侍郎为元丰吏部侍郎二员之一。",
        "编制",
    )
    w.commit()


def entry1002_staff_link():
    """第1003条建成正式官名后，补挂第1002条独立提供的侍郎一人证据。"""
    i = 1002
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    w = W(i)
    rel(
        w,
        ft(w, fe(w, "吏部侍郎左选", "机构"), "北宋元丰五年五月"),
        ft(
            w,
            fe(w, "吏部左选侍郎", "官职"),
            "北宋元丰五年四月二十三日",
        ),
        "编制隶属",
        i,
        staff,
        "侍郎左选编制字段独立补证分领本选的侍郎一人。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def left_selection_office(i, title, definition, event, duty):
    definition = Q(i, definition)
    duty = Q(i, duty)
    w = W(i)
    eid = w.entity(
        title,
        "机构",
        f"第{i}条直接定义{title}为吏部侍郎左选常设办事部门。",
        quotation=definition,
    )
    tid = tp(
        w,
        eid,
        "北宋元丰五年五月",
        event,
        i,
        duty,
        "吏部侍郎左选办事机构",
        f"原文未另载时间，按所属吏部侍郎左选的首个真实时间点承载{title}职掌。",
    )
    rel(
        w,
        ft(w, fe(w, "吏部侍郎左选", "机构"), "北宋元丰五年五月"),
        tid,
        "上下级机构",
        i,
        definition,
        f"原文明确{title}为吏部侍郎左选常设办事部门之一。",
    )
    w.commit()


def entry1004():
    left_selection_office(
        1004,
        "吏部侍郎左选令丞案",
        "吏部侍郎左选常设办事部门之一。",
        "掌选人县令、丞拟注、辞谢、功过",
        "掌选人县令、丞拟注、辞谢、功过等事（《宋会要·职官》11之56）。",
    )


def entry1005():
    left_selection_office(
        1005,
        "吏部侍郎左选职官案",
        "吏部侍郎左选常设办事部门之一。",
        "掌幕职官选人拟注、辞谢、功过",
        "掌幕职官（选人）拟注、辞谢、功过事（《宋会要·职官》11之56）。",
    )


def entry1006():
    left_selection_office(
        1006,
        "吏部侍郎左选入官案",
        "吏部侍郎左选常设办事部门之一。",
        "掌选人改官条件审核、奏荐手续核验及引见应改官选人",
        "掌选人是否符合改官条件、改官奏荐手续的圆备及引见应合改官选人于便殿等事"
        "（《宋会要·职官》11之56，参《合璧后集》卷27《吏部侍郎》）。",
    )


def entry1007():
    left_selection_office(
        1007,
        "吏部侍郎左选县尉案",
        "吏部侍郎左选常设办事部门之一。",
        "掌县尉选人功过、磨勘、注拟",
        "掌任职县尉的选人功过、磨勘、注拟等事（《宋会要·职官》11之56）。",
    )


def entry1008():
    left_selection_office(
        1008,
        "吏部侍郎左选格式案",
        "吏部侍郎左选常设办事部门之一。",
        "掌依任职州县户口升降确定有职事选人俸禄",
        "掌有职事选人依任职所在州县户口升降数而定其俸禄"
        "（《宋会要·职官》11之56）。",
    )


def entry1009():
    left_selection_office(
        1009,
        "吏部侍郎左选主簿上案、下案",
        "部侍郎常设办事部门之一。",
        "掌县主簿选人功过、磨勘、注拟",
        "掌任职县主簿的选人功过、磨勘、注拟等事《宋会要·职官》11之56）。",
    )


def entry1010():
    left_selection_office(
        1010,
        "吏部侍郎左选开拆案",
        "吏部侍郎左选常设办事部门之一。",
        "掌本选文书收发",
        "掌本选文书的收发（《宋会要·职官》11之56）。",
    )


def main():
    assert [x.b.F[i]["title"] for i in range(991, 1011)] == [
        "吏部尚书右选副使案",
        "吏部尚书右选敦修武案",
        "吏部尚书右选注拟掌阙案",
        "吏部尚书右选奏荐赏功案",
        "吏部尚书右选开拆案",
        "吏部尚书右选名籍案",
        "吏部尚书右选甲库案",
        "吏部尚书右选法司案",
        "吏部尚书右选知杂案",
        "吏部侍郎",
        "权吏部侍郎",
        "吏部侍郎左选",
        "吏部左选侍郎",
        "吏部侍郎左选令丞案",
        "吏部侍郎左选职官案",
        "吏部侍郎左选入官案",
        "吏部侍郎左选县尉案",
        "吏部侍郎左选格式案",
        "吏部侍郎左选主簿上案、下案",
        "吏部侍郎左选开拆案",
    ]
    entry991()
    entry992()
    entry993()
    entry994()
    entry995()
    entry996()
    entry997()
    entry998()
    entry999()
    entry1000()
    entry1001()
    entry1002()
    entry1003()
    entry1002_staff_link()
    entry1004()
    entry1005()
    entry1006()
    entry1007()
    entry1008()
    entry1009()
    entry1010()


if __name__ == "__main__":
    main()
