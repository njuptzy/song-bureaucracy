#!/usr/bin/env python3
"""提取 chapter2t4 第971–990条：六部门、架阁官与吏部尚书左右选。"""
import extract_2t4_811_830 as x


x.b.F = {963: x.b.load(963), **{i: x.b.load(i) for i in range(971, 991)}}
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
mark_citation_conflict = x.b.mark_citation_conflict


def ft_any(w, entity_id, *times):
    for time in times:
        timepoint_id = w.find_timepoint(entity_id, time)
        if timepoint_id is not None:
            return timepoint_id
    raise AssertionError((entity_id, times))


def entry971():
    i = 971
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    grade = Q(i, x.b.F[i]["fields"]["官品"], "官品")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    eid = w.entity(
        "监尚书省六部门",
        "官职",
        "本条直接定义监尚书省六部门。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "南宋绍兴二年九月六日",
        "始置，编制一员，掌六部大门启闭、六部官出入请假及外来人员来访",
        i,
        origin,
        "尚书省六部门官",
        "建立监尚书省六部门始置节点。",
        "职源",
        attr_grade="秩比寺监、丞",
    )
    cite(w, "Timepoints", start, i, duty, "补证六部监门职掌。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证六部监门品秩。", "官品")
    cite(w, "Timepoints", start, i, staff, "补证六部监门一员及所隶选司。", "编制")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "全文扫描简称字段；六部监门、门司、门官均为称谓，不另建实体。",
        "简称与别名",
        note="纯简称与别名",
    )
    for selection in ("吏部尚书左选", "吏部尚书右选"):
        rel(
            w,
            ft(w, fe(w, selection, "机构"), "北宋元丰五年五月"),
            start,
            "编制隶属",
            i,
            staff,
            f"编制字段明确监尚书省六部门一员隶{selection}；属堂除阙。",
            "编制",
            staff_type="官",
        )
    w.commit()


def entry972_973():
    i = 972
    main = Q(i, x.b.F[i]["text"])
    history = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    grade = Q(i, x.b.F[i]["fields"]["品位"], "品位")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    eid = w.entity(
        "管勾尚书六部架阁库",
        "官职",
        "本条直接定义管勾尚书六部架阁库。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "北宋元丰间",
        "始置，主管六部档案文书编目、登记、保管与检索",
        i,
        history,
        "六部档案官",
        "建立管勾尚书六部架阁库始置节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证架阁官档案职掌。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证架阁官选任资格与品秩随本官。", "品位")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证北宋全称及避讳改字；六部架阁、架阁、掌故不另建实体。",
        "简称与别名",
        note="纯简称、拟古称与避讳说明",
    )
    separate = tp(
        w,
        eid,
        "北宋崇宁间",
        "六部各部置架阁官",
        i,
        history,
        "六部档案官",
        "建立崇宁间六部分置架阁官节点。",
        "职源",
        chain="none",
    )
    restore = tp(
        w,
        eid,
        "南宋绍兴三年",
        "复立尚书省六部架阁库官，不分部",
        i,
        history,
        "六部档案官",
        "建立绍兴三年六部架阁官复立节点。",
        "职源",
        chain="none",
    )
    change = tp(
        w,
        eid,
        "南宋绍兴十五年",
        "改置主管尚书某部架阁库，各部分置",
        i,
        history,
        "六部档案官",
        "建立绍兴十五年管勾官改为主管官节点。",
        "职源",
        chain="none",
    )
    chain_all(
        w,
        eid,
        [start, separate, restore, change],
        "连接管勾尚书六部架阁库元丰始置、崇宁分置、绍兴复立与改置节点。",
    )

    w.commit()

    i = 973
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "主管尚书某部架阁文字",
        "官职",
        "第973条直接定义主管尚书某部架阁文字。",
        quotation=main,
    )
    tid = w.find_timepoint(eid, "南宋绍兴十五年")
    if tid is None:
        tid = tp(
            w,
            eid,
            "南宋（未载具体年月）",
            "各部档案库官，北宋管勾之名在南宋改为主管",
            i,
            main,
            "尚书省各部档案官",
            "建立主管尚书某部架阁文字南宋节点；具体改置年月由第972条补证。",
        )
    else:
        cite(
            w,
            "Timepoints",
            tid,
            i,
            main,
            "专条补证北宋称管勾、南宋改主管及其档案库官性质。",
        )
    w.commit()

    i = 972
    w = W(i)
    successor_e = fe(w, "主管尚书某部架阁文字", "官职")
    successor = refine(
        w,
        ft_any(w, successor_e, "南宋（未载具体年月）", "南宋绍兴十五年"),
        i,
        history,
        "第972条职源明确绍兴十五年改置各部主管架阁官。",
        "职源",
        time="南宋绍兴十五年",
        event="改称主管并按尚书各部分置，主管本部架阁文字",
        category="尚书省各部档案官",
    )
    rel(
        w,
        ft(w, fe(w, "管勾尚书六部架阁库", "官职"), "南宋绍兴十五年"),
        successor,
        "前后演变",
        i,
        history,
        "绍兴十五年管勾尚书六部架阁库改为各部主管架阁官。",
        "职源",
    )
    w.commit()


def entry974():
    i = 974
    main = Q(i, x.b.F[i]["text"])
    history = Q(i, x.b.F[i]["fields"]["职源与沿革"], "职源与沿革")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)

    attendant_e = w.entity(
        "常侍曹",
        "机构",
        "职源字段明确东汉初由常侍曹改为吏曹。",
        quotation=history,
    )
    attendant = tp(
        w,
        attendant_e,
        "东汉初",
        "改为吏曹",
        i,
        history,
        "选官机构前身",
        "建立常侍曹改为吏曹节点。",
        "职源与沿革",
    )
    personnel_e = w.entity(
        "吏曹",
        "机构",
        "职源字段明确东汉初由常侍曹改为吏曹。",
        quotation=history,
    )
    personnel_start = tp(
        w,
        personnel_e,
        "东汉初",
        "由常侍曹改置",
        i,
        history,
        "选官机构",
        "建立吏曹东汉初改置节点。",
        "职源与沿革",
        chain="none",
    )
    personnel_end = tp(
        w,
        personnel_e,
        "东汉（未载具体年月）",
        "改为选部",
        i,
        history,
        "选官机构",
        "建立吏曹改为选部节点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, personnel_e, [personnel_start, personnel_end], "连接吏曹始置与改名节点。")
    selection_e = w.entity(
        "选部",
        "机构",
        "职源字段明确吏曹后改为选部。",
        quotation=history,
    )
    selection_start = tp(
        w,
        selection_e,
        "东汉（未载具体年月）",
        "由吏曹改称",
        i,
        history,
        "选官机构",
        "建立选部东汉改称节点。",
        "职源与沿革",
        chain="none",
    )
    selection_end = tp(
        w,
        selection_e,
        "三国魏",
        "改为吏部",
        i,
        history,
        "选官机构",
        "建立选部至魏改为吏部节点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, selection_e, [selection_start, selection_end], "连接选部东汉始称与魏代改名节点。")
    rel(w, attendant, personnel_start, "前后演变", i, history, "东汉初常侍曹改为吏曹。", "职源与沿革")
    rel(w, personnel_end, selection_start, "前后演变", i, history, "东汉吏曹后改为选部。", "职源与沿革")

    department_e = fe(w, "吏部", "机构")
    wei = tp(
        w,
        department_e,
        "三国魏",
        "由选部改称吏部",
        i,
        history,
        "中央选官机构",
        "建立吏部魏代始称节点。",
        "职源与沿革",
        chain="none",
    )
    liang = tp(
        w,
        department_e,
        "南朝梁武帝时",
        "置尚书省吏部",
        i,
        history,
        "尚书省所属选官机构",
        "建立南朝梁尚书省吏部节点。",
        "职源与沿革",
        chain="none",
    )
    early = refine(
        w,
        ft_any(w, department_e, "北宋", "宋前期"),
        i,
        duty,
        "专条细化宋前期吏部虚置及有限职掌。",
        "职掌",
        time="宋前期",
        event="名义设官而职事甚微，仅掌服色、祭祀摄官、拔萃举人并兼领南曹、格式司、甲库",
        category="尚书省所属选官机构",
    )
    reform = tp(
        w,
        department_e,
        "北宋元丰改制后",
        "恢复实职，掌六品以下文武官铨选并统总品阶爵勋、俸禄、分职、功赏与考绩",
        i,
        duty,
        "尚书省所属选官机构",
        "建立元丰改制后吏部恢复实职节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", wei, i, main, "正文补证本条所述机构为尚书省吏部。")
    cite(w, "Timepoints", early, i, staff, "补证宋前期判吏部事二人。", "编制")
    cite(w, "Timepoints", reform, i, staff, "补证元丰吏部官额。", "编制")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        aliases,
        "全文扫描简称字段；尚书吏部、吏部、天官等称谓不另建实体。",
        "简称与别名",
        note="纯简称、拟古称与雅称；其中元丰三年诏称尚书省吏部为名称证据",
    )
    chain_all(w, department_e, [wei, liang, early, reform], "连接吏部魏、梁、宋前期及元丰改制节点。")
    rel(w, selection_end, wei, "前后演变", i, history, "三国魏选部改为吏部。", "职源与沿革")

    subordinate_titles = (
        ("吏部尚书左选", "北宋元丰五年五月"),
        ("吏部尚书右选", "北宋元丰五年五月"),
        ("吏部侍郎左选", "北宋元丰五年五月"),
        ("吏部侍郎右选", "北宋元丰五年五月"),
        ("司封司", "宋代（尚书二十四司）"),
        ("司勋司", "宋代（尚书二十四司）"),
        ("考功司", "宋代（尚书二十四司）"),
    )
    for title, time in subordinate_titles:
        rel(
            w,
            reform,
            ft(w, fe(w, title, "机构"), time),
            "上下级机构",
            i,
            duty,
            f"元丰改制后吏部统领{title}。",
            "职掌",
        )
    notices_e = w.entity(
        "尚书省官告院",
        "机构",
        "职掌字段明确元丰改制后吏部兼领官告院。",
        quotation=duty,
    )
    notices = tp(
        w,
        notices_e,
        "北宋元丰改制后",
        "隶吏部，办理官告事务",
        i,
        duty,
        "尚书省属院",
        "建立吏部所领官告院节点。",
        "职掌",
    )
    rel(w, reform, notices, "上下级机构", i, duty, "元丰改制后吏部领官告院。", "职掌")

    minister_e = fe(w, "吏部尚书", "官职")
    minister_chain = current_chain(w, minister_e)
    minister = tp(
        w,
        minister_e,
        "北宋元丰新制",
        "吏部长官一人，总领吏部七司",
        i,
        staff,
        "吏部长官",
        "据吏部总条建立元丰吏部尚书编制节点。",
        "编制",
        chain="none",
    )
    if minister not in minister_chain:
        minister_chain.append(minister)
    # 此时专条976尚未补入更早节点；按现有宋代节点后接元丰节点。
    chain_all(w, minister_e, minister_chain, "将元丰吏部尚书编制节点接入现有完整时间链。")
    rel(
        w,
        reform,
        minister,
        "编制隶属",
        i,
        staff,
        "元丰新制吏部尚书一人。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )

    vice_e = fe(w, "吏部侍郎", "官职")
    vice = tp(
        w,
        vice_e,
        "北宋元丰新制",
        "吏部副长官二人",
        i,
        staff,
        "吏部副长官",
        "据吏部总条建立元丰吏部侍郎编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        vice_e,
        [ft(w, vice_e, "北宋元丰改制前"), vice],
        "连接吏部侍郎元丰改制前与元丰新制节点。",
    )
    rel(
        w,
        reform,
        vice,
        "编制隶属",
        i,
        staff,
        "元丰新制吏部侍郎二人。",
        "编制",
        staff_quota=2,
        staff_type="官",
    )
    w.commit()


def entry975():
    i = 975
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = fe(w, "判吏部事", "官职")
    tid = refine(
        w,
        ft_any(w, eid, "宋代", "宋前期"),
        i,
        main,
        "专条补证宋前期判吏部事的差遣性质、职掌及兼领机构。",
        time="宋前期",
        event="以朝官差判吏部事，掌吏部有限职事并兼领南曹、格式司、甲库",
        category="吏部差遣长官",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段补证判部、判部事、吏部判事等称谓及二人编制。",
        "简称",
        note="纯简称",
    )
    rel(
        w,
        ft(w, fe(w, "吏部", "机构"), "宋前期"),
        tid,
        "编制隶属",
        i,
        main,
        "宋前期以判吏部事二人掌吏部。",
        staff_quota=2,
        staff_type="官",
    )
    w.commit()


def entry976():
    i = 976
    main = Q(i, x.b.F[i]["text"])
    history = Q(i, x.b.F[i]["fields"]["职源与沿革"], "职源与沿革")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    grade = Q(i, x.b.F[i]["fields"]["官品"], "官品")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    eid = fe(w, "吏部尚书", "官职")
    wei = tp(
        w,
        eid,
        "三国魏黄初元年",
        "始有吏部尚书之名",
        i,
        history,
        "选官长官",
        "建立吏部尚书魏代始称节点。",
        "职源与沿革",
        chain="none",
    )
    liang = tp(
        w,
        eid,
        "南朝梁",
        "始称尚书省吏部尚书",
        i,
        history,
        "尚书省吏部长官",
        "建立南朝梁尚书省吏部尚书节点。",
        "职源与沿革",
        chain="none",
    )
    early = refine(
        w,
        ft_any(w, eid, "宋代", "宋前期"),
        i,
        duty,
        "专条细化宋前期吏部尚书为无职事阶官。",
        "职掌",
        time="宋前期",
        event="为阶官，无职事",
        category="阶官",
        grade="正三品",
    )
    cite(w, "Timepoints", early, i, grade, "补证宋前期正三品。", "官品")
    reform = refine(
        w,
        ft(w, eid, "北宋元丰新制"),
        i,
        duty,
        "专条细化元丰吏部尚书由阶官改为职事官后的职掌。",
        "职掌",
        event="改为职事官、吏部长官，掌七司及文武百官选试拟注迁授等政令",
        category="吏部长官",
        grade="从二品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰新制从二品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证吏部尚书一人。", "编制")
    yuan_you = tp(
        w,
        eid,
        "北宋元祐官品令",
        "官品改为正二品",
        i,
        grade,
        "吏部长官",
        "建立元祐官品令吏部尚书品级节点。",
        "官品",
        chain="none",
        attr_grade="正二品",
    )
    south = tp(
        w,
        eid,
        "南宋",
        "沿置为吏部长官",
        i,
        history,
        "吏部长官",
        "建立南宋吏部尚书沿置节点。",
        "职源与沿革",
        chain="none",
        attr_grade="从二品",
    )
    cite(w, "Timepoints", south, i, grade, "补证南宋从二品。", "官品")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        aliases,
        "简称字段补证吏书等称谓及吏部尚书为六官之长；纯称谓不另建实体。",
        "简称与别名",
        note="纯简称与拟古称",
    )
    chain_all(
        w,
        eid,
        [wei, liang, early, reform, yuan_you, south],
        "连接吏部尚书魏、梁、宋前期、元丰、元祐与南宋节点。",
    )

    rank_e = w.entity(
        "金紫光禄大夫",
        "官职",
        "职掌字段明确元丰改制后吏部尚书旧阶改为寄禄官金紫光禄大夫。",
        quotation=duty,
    )
    rank_t = tp(
        w,
        rank_e,
        "北宋元丰改制",
        "承接吏部尚书旧阶，作为寄禄官",
        i,
        duty,
        "寄禄官",
        "建立金紫光禄大夫承接吏部尚书旧阶节点。",
        "职掌",
    )
    rel(
        w,
        early,
        rank_t,
        "前后演变",
        i,
        duty,
        "元丰改制将吏部尚书旧阶易为寄禄官金紫光禄大夫。",
        "职掌",
    )
    w.commit()


def entry977():
    i = 977
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    grade = Q(i, x.b.F[i]["fields"]["官品"], "官品")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = fe(w, "权吏部尚书", "官职")
    conflicting = tp(
        w,
        eid,
        "北宋元祐三年闰十二月十八日",
        "本条记始置，用以位置资格未到的新进之士",
        i,
        origin,
        "权摄吏部长官",
        "保留权吏部尚书专条所载十八日始置异文。",
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
        "第963条职源作元祐三年闰十二月二十八日，本条作十八日；两说原样并存。",
        "标记权吏部尚书始置日异文。",
        "职源",
    )
    established = ft(w, eid, "北宋元祐三年闰十二月二十八日")
    mark_citation_conflict(
        w,
        "Timepoints",
        established,
        963,
        x.b.load(963)["fields"]["职源与沿革"],
        "第977条职源另作闰十二月十八日。",
        "回标既有二十八日节点与专条异文冲突。",
        "职源与沿革",
    )
    cite(w, "Timepoints", conflicting, i, duty, "补证权吏部尚书职掌与正任相同。", "职掌")
    cite(w, "Timepoints", conflicting, i, grade, "补证权吏部尚书正三品。", "官品")
    cite(
        w,
        "Timepoints",
        conflicting,
        i,
        aliases,
        "简称字段补证权尚书省称；人物任职仅作制度证据。",
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
        "权摄吏部长官",
        "建立南宋权吏部尚书沿置节点。",
        "职源",
        chain="none",
        attr_grade="正三品",
    )
    chain_all(
        w,
        eid,
        [conflicting, established, south],
        "连接权吏部尚书两种始置日异文与南宋沿置节点。",
    )
    w.commit()


def entry978():
    i = 978
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    eid = fe(w, "吏部尚书左选", "机构")
    start = refine(
        w,
        ft(w, eid, "北宋元丰五年五月"),
        i,
        origin,
        "专条补证吏部尚书左选由审官东院改置。",
        "职源",
        event="由审官东院改置，选授六品以下非中书敕授文臣",
        category="吏部文臣铨选机构",
    )
    cite(w, "Timepoints", start, i, main, "正文补证吏部尚书左选为官署。")
    cite(w, "Timepoints", start, i, duty, "补证尚书左选选授范围。", "职掌")
    cite(w, "Timepoints", start, i, staff, "补证尚书左选郎中、分案与吏额。", "编制")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证尚书左选、左选、尚左等称谓；纯简称不另建实体。",
        "简称与别名",
        note="纯简称",
    )
    role_e = w.entity(
        "吏部尚书左选郎中",
        "官职",
        "编制字段明确尚书左选郎中一人。",
        quotation=staff,
    )
    role_t = tp(
        w,
        role_e,
        "北宋元丰五年五月",
        "尚书左选长官，掌考校京朝官以下殿最",
        i,
        staff,
        "吏部铨选官",
        "建立吏部尚书左选郎中节点。",
        "编制",
    )
    rel(
        w,
        start,
        role_t,
        "编制隶属",
        i,
        staff,
        "尚书左选置郎中一人。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )
    monitor = ft(w, fe(w, "监尚书省六部门", "官职"), "南宋绍兴二年九月六日")
    rel(
        w,
        start,
        monitor,
        "编制隶属",
        i,
        staff,
        "编制字段明示尚书左选兼领尚书六部监门。",
        "编制",
        staff_type="官",
    )
    w.commit()


def entry979_988():
    for i in range(979, 989):
        main = Q(i, x.b.F[i]["text"])
        w = W(i)
        title = x.b.F[i]["title"]
        eid = w.entity(
            title,
            "机构",
            f"本条直接定义{title}为吏部尚书左选常设办事部门。",
            quotation=main,
        )
        tid = tp(
            w,
            eid,
            "北宋元丰五年五月",
            main.split("。", 1)[1].rsplit("（", 1)[0],
            i,
            main,
            "吏部尚书左选办事机构",
            f"按尚书左选始置时间建立{title}节点。",
        )
        rel(
            w,
            ft(w, fe(w, "吏部尚书左选", "机构"), "北宋元丰五年五月"),
            tid,
            "上下级机构",
            i,
            main,
            f"原文明确{title}为吏部尚书左选常设办事部门。",
        )
        w.commit()


def entry989():
    i = 989
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = fe(w, "吏部尚书右选", "机构")
    start = refine(
        w,
        ft(w, eid, "北宋元丰五年五月"),
        i,
        origin,
        "专条补证吏部尚书右选由审官西院改置。",
        "职源",
        event="由审官西院改置，选授非枢密院宣授的中下级武臣",
        category="吏部武臣铨选机构",
    )
    cite(w, "Timepoints", start, i, main, "正文补证吏部尚书右选为官署。")
    cite(w, "Timepoints", start, i, duty, "补证尚书右选选授范围。", "职掌")
    cite(w, "Timepoints", start, i, staff, "补证尚书右选郎中、分案与吏额。", "编制")
    cite(
        w,
        "Timepoints",
        start,
        i,
        aliases,
        "简称字段补证尚书右选、尚右等称谓；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    role_e = w.entity(
        "吏部尚书右选郎中",
        "官职",
        "编制字段明确尚书右选郎中一人。",
        quotation=staff,
    )
    role_t = tp(
        w,
        role_e,
        "北宋元丰五年五月",
        "尚书右选长官",
        i,
        staff,
        "吏部铨选官",
        "建立吏部尚书右选郎中节点。",
        "编制",
    )
    rel(
        w,
        start,
        role_t,
        "编制隶属",
        i,
        staff,
        "尚书右选置郎中一人。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def entry990():
    i = 990
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    title = x.b.F[i]["title"]
    eid = w.entity(
        title,
        "机构",
        "本条直接定义吏部尚书右选大夫案。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "北宋元丰五年五月",
        "掌武臣正七品官差注，政和二年后掌武功大夫至武翼大夫差注",
        i,
        main,
        "吏部尚书右选办事机构",
        "按尚书右选始置时间建立大夫案节点。",
    )
    rel(
        w,
        ft(w, fe(w, "吏部尚书右选", "机构"), "北宋元丰五年五月"),
        tid,
        "上下级机构",
        i,
        main,
        "原文明确大夫案为吏部尚书右选常设办事部门。",
    )
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(971, 991)] == [
        "监尚书省六部门",
        "管勾尚书六部架阁库",
        "主管尚书某部架阁文字",
        "尚书省吏部",
        "判吏部事",
        "吏部尚书",
        "权吏部尚书",
        "吏部尚书左选",
        "吏部尚书左选六品案",
        "吏部尚书左选七品案",
        "吏部尚书左选八品案",
        "吏部尚书左选九品案",
        "吏部尚书左选注拟案",
        "吏部尚书左选名籍案",
        "吏部尚书左选掌阙案",
        "吏部尚书左选催驱案",
        "吏部尚书左选甲库案",
        "吏部尚书左选检法案",
        "吏部尚书右选",
        "吏部尚书右选大夫案",
    ]
    entry971()
    entry972_973()
    entry974()
    entry975()
    entry976()
    entry977()
    entry978()
    entry979_988()
    entry989()
    entry990()


if __name__ == "__main__":
    main()
