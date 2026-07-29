#!/usr/bin/env python3
"""提取 chapter2t4 第1091–1110条：度支司、金部司及仓部司总条。"""
import extract_2t4_1071_1090 as x


x.x.b.F = {i: x.x.b.load(i) for i in range(1091, 1111)}
F = x.x.b.F
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
mark_citation_conflict = x.x.b.mark_citation_conflict


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def entry1091():
    i = 1091
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "度支司", "机构")
    sui = tp(
        w, eid, "隋", "度支曹始称度支司，列尚书省二十四司",
        i, origin, "尚书省户部属司", "建立度支司隋代始称节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化度支司宋前期无职掌。", "职掌",
        time="宋前期", event="名存而无所掌，由判度支司事守司",
        category="尚书省户部属司",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判司一人、吏人二。", "编制")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化元丰度支司职掌。", "职掌",
        event="恢复职事，量贡赋税租收入并计划逐年军国费用",
        category="尚书省户部属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎官、分案及吏额编制。", "编制")
    south = tp(
        w, eid, "南宋", "度支郎官一员，分案五；吏额递减",
        i, staff, "尚书省户部属司", "建立度支司南宋编制节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证度支司为户部五司之一。")
    chain_all(w, eid, [sui, song, reform, south], "重建度支司隋、宋前期、元丰及南宋完整时间链。")

    w.commit()


def duzhi_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "机构", f"第{i}条直接定义{title}及其职掌。", quotation=main)
    w.commit()

    parent_staff = field(1091, "编制")
    w = W(1091)
    eid = fe(w, title, "机构")
    north = tp(
        w, eid, "北宋元丰新制", "度支司办事案",
        1091, parent_staff, "度支司办事机构", f"据度支司元丰分案编制建立{title}节点。",
        "编制", chain="none",
    )
    south = tp(
        w, eid, "南宋", "度支司五案之一",
        1091, parent_staff, "度支司办事机构", f"据南宋度支司分案五建立{title}节点。",
        "编制", chain="none",
    )
    chain_all(w, eid, [north, south], f"连接{title}元丰与南宋节点。")
    rel(
        w, ft(w, fe(w, "度支司", "机构"), "北宋元丰新制"), north,
        "上下级机构", 1091, parent_staff, f"元丰{title}隶度支司。", "编制",
    )
    rel(
        w, ft(w, fe(w, "度支司", "机构"), "南宋"), south,
        "上下级机构", 1091, parent_staff, f"南宋{title}隶度支司。", "编制",
    )
    w.commit()

    w = W(i)
    eid = fe(w, title, "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        f"专条细化{title}职掌。", None, event=event,
        category="度支司办事机构",
    )
    south = refine(
        w, ft(w, eid, "南宋"), i, main,
        f"专条补证南宋{title}职掌。", None, event=event,
        category="度支司办事机构",
    )
    chain_all(w, eid, [north, south], f"确认{title}完整时间链。")
    w.commit()


def entry1097():
    i = 1097
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    w = W(i)
    eid = w.entity("判度支司事", "官职", "本条直接定义宋前期判度支司事。", quotation=main)
    tang = tp(
        w, eid, "唐天宝七载", "已有判度支之差遣",
        i, origin, "判司差遣", "建立判度支司事唐代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "由无职事朝官兼差，守司而无所掌",
        i, duty, "判司差遣", "建立判度支司事宋前期节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", song, i, grade, "补证品位随兼差朝官本官而定。", "官品")
    chain_all(w, eid, [tang, song], "连接判度支司事唐代职源与宋前期差遣节点。")
    rel(
        w, ft(w, fe(w, "度支司", "机构"), "宋前期"), song,
        "编制隶属", i, main, "宋前期度支司置判司事一人。",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1098():
    i = 1098
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "度支司郎中", "官职")
    beimei = tp(
        w, eid, "北齐", "已有度支曹郎中之名",
        i, origin, "度支司郎官", "建立度支司郎中北齐职源节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐高宗即位之初", "始有尚书省户部度支司郎中之名",
        i, origin, "度支司郎官", "建立度支司郎中唐代正称节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化度支司郎中宋前期阶官性质。", "职掌",
        time="宋前期", event="为无职事的中行郎中阶，元丰后寄禄官易为朝散大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，为度支司长官，掌领本司事",
        i, duty, "度支司长官", "建立度支司郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [beimei, tang, song, reform], "重建度支司郎中北齐至元丰完整时间链。")
    rel(
        w, ft(w, fe(w, "度支司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰度支司置郎中为司长。",
        "职掌", staff_quota=1, staff_type="官",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名和职事官名。")
    w.commit()


def entry1099():
    i = 1099
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity("度支司员外郎", "官职", "本条直接定义度支司员外郎。", quotation=main)
    sui = tp(
        w, eid, "隋文帝时", "始有尚书省民部度支司员外郎之名",
        i, origin, "度支司郎官", "建立度支司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐贞观二十三年", "始有尚书省户部度支司员外郎之名",
        i, origin, "度支司郎官", "建立度支司员外郎唐代正称节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "为无职事的中行员外郎阶，元丰后寄禄官易为朝散郎",
        i, duty, "文臣迁转官阶", "建立度支司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，为度支司副长官，佐郎中掌本司事",
        i, duty, "度支司副长官", "建立度支司员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [sui, tang, song, reform], "连接度支司员外郎隋、唐、宋前期与元丰节点。")
    rel(
        w, ft(w, fe(w, "度支司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰度支司置员外郎为副长官。",
        "职掌", staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1100():
    i = 1100
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "金部司", "机构")
    sui = tp(
        w, eid, "隋", "始有尚书省民部金部司之称",
        i, origin, "尚书省户部属司", "建立金部司隋代始称节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐贞观二十三年", "民部改户部，尚书省户部金部司称谓确立",
        i, origin, "尚书省户部属司", "建立金部司唐代正称节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化金部司宋前期无职掌。", "职掌",
        time="宋前期", event="名存而无职事", category="尚书省户部属司",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化元丰金部司职掌。", "职掌",
        event="恢复职事，掌库藏出纳、金银钱货支用及度量衡禁令",
        category="尚书省户部属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰分案七及吏额。", "编制")
    south = tp(
        w, eid, "南宋", "金部郎官一人，分案六；吏额递减",
        i, staff, "尚书省户部属司", "建立金部司南宋编制节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [sui, tang, song, reform, south], "重建金部司隋至南宋完整时间链。")
    cite(w, "Timepoints", reform, i, main, "正文补证金部司为官司。")
    w.commit()


def jinbu_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "机构", f"第{i}条直接定义{title}及其职掌。", quotation=main)
    w.commit()

    parent_staff = field(1100, "编制")
    w = W(1100)
    eid = fe(w, title, "机构")
    north = tp(
        w, eid, "北宋元丰新制", "金部司办事案",
        1100, parent_staff, "金部司办事机构", f"据金部司元丰分案建立{title}节点。",
        "编制", chain="none",
    )
    south = tp(
        w, eid, "南宋", "金部司六案之一",
        1100, parent_staff, "金部司办事机构", f"据南宋金部司分案六建立{title}节点。",
        "编制", chain="none",
    )
    chain_all(w, eid, [north, south], f"连接{title}元丰与南宋节点。")
    rel(
        w, ft(w, fe(w, "金部司", "机构"), "北宋元丰新制"), north,
        "上下级机构", 1100, parent_staff, f"元丰{title}隶金部司。", "编制",
    )
    rel(
        w, ft(w, fe(w, "金部司", "机构"), "南宋"), south,
        "上下级机构", 1100, parent_staff, f"南宋{title}隶金部司。", "编制",
    )
    w.commit()

    w = W(i)
    eid = fe(w, title, "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        f"专条细化{title}职掌。", None, event=event,
        category="金部司办事机构",
    )
    south = refine(
        w, ft(w, eid, "南宋"), i, main,
        f"专条补证南宋{title}职掌。", None, event=event,
        category="金部司办事机构",
    )
    chain_all(w, eid, [north, south], f"确认{title}完整时间链。")
    w.commit()


def entry1103():
    i = 1103
    main = Q(i, F[i]["text"])
    w = W(i)
    w.entity("金部司钱帛案", "机构", "第1103条直接定义金部司钱帛案及其职掌。", quotation=main)
    w.commit()

    parent_staff = field(1100, "编制")
    w = W(1100)
    eid = fe(w, "金部司钱帛案", "机构")
    north = tp(
        w, eid, "北宋元丰新制", "金部司办事案",
        1100, parent_staff, "金部司办事机构", "据金部司元丰分案建立钱帛案节点。",
        "编制", chain="none",
    )
    south = tp(
        w, eid, "南宋", "金部司六案之一",
        1100, parent_staff, "金部司办事机构", "据南宋金部司分案六建立钱帛案节点。",
        "编制", chain="none",
    )
    ordered = [north]
    existing_rename = w.find_timepoint(eid, "北宋元祐元年")
    existing_restore = w.find_timepoint(eid, "北宋崇宁二年")
    if existing_rename is not None:
        ordered.append(existing_rename)
    if existing_restore is not None:
        ordered.append(existing_restore)
    ordered.append(south)
    chain_all(w, eid, ordered, "连接金部司钱帛案元丰、改名沿革与南宋节点。")
    rel(
        w, ft(w, fe(w, "金部司", "机构"), "北宋元丰新制"), north,
        "上下级机构", 1100, parent_staff, "元丰金部司钱帛案隶金部司。", "编制",
    )
    rel(
        w, ft(w, fe(w, "金部司", "机构"), "南宋"), south,
        "上下级机构", 1100, parent_staff, "南宋金部司钱帛案隶金部司。", "编制",
    )
    w.commit()

    w = W(i)
    eid = fe(w, "金部司钱帛案", "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        "专条细化钱帛案职掌。", None,
        event="掌催收金银钱帛年额、折斛及封桩钱物",
        category="金部司办事机构",
    )
    rename = tp(
        w, eid, "北宋元祐元年", "改名催纳案",
        i, main, "金部司办事机构", "建立钱帛案元祐改名节点。",
        chain="none",
    )
    restore = tp(
        w, eid, "北宋崇宁二年", "由催纳案改回钱帛案",
        i, main, "金部司办事机构", "建立钱帛案崇宁复名节点。",
        chain="none",
    )
    south = refine(
        w, ft(w, eid, "南宋"), i, main,
        "专条补证钱帛案职掌及改名沿革。", None,
        event="掌催收金银钱帛年额、折斛及封桩钱物",
        category="金部司办事机构",
    )
    chain_all(w, eid, [north, rename, restore, south], "连接钱帛案元丰、元祐改名、崇宁复名及南宋节点。")

    alias_e = w.entity("金部司催纳案", "机构", "原文明载钱帛案元祐元年改为催纳案。", quotation=main)
    alias_start = tp(
        w, alias_e, "北宋元祐元年", "由金部司钱帛案改名",
        i, main, "金部司办事机构", "建立催纳案始称节点。",
        chain="none",
    )
    alias_end = tp(
        w, alias_e, "北宋崇宁二年", "改回金部司钱帛案",
        i, main, "金部司办事机构", "建立催纳案复名终点。",
        chain="none",
    )
    chain_all(w, alias_e, [alias_start, alias_end], "连接催纳案元祐始称与崇宁复名节点。")
    rel(w, rename, alias_start, "前后演变", i, main, "元祐元年钱帛案改为催纳案。")
    rel(w, alias_end, restore, "前后演变", i, main, "崇宁二年催纳案改回钱帛案。")
    w.commit()


def entry1107():
    i = 1107
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("判金部司事", "官职", "本条直接定义宋前期判金部司事。", quotation=main)
    tid = tp(
        w, eid, "宋前期", "由无职事朝官充任，实无所掌，品位随本官",
        i, main, "判司差遣", "建立判金部司事宋前期节点。",
    )
    rel(
        w, ft(w, fe(w, "金部司", "机构"), "宋前期"), tid,
        "编制隶属", i, main, "宋前期金部司置判司事一人。",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1108():
    i = 1108
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "金部司郎中", "官职")
    beiqi = tp(
        w, eid, "北齐", "已有金部曹郎中之名",
        i, origin, "金部司郎官", "建立金部司郎中北齐职源节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐", "始有尚书省户部金部司郎中之名",
        i, origin, "金部司郎官", "建立金部司郎中唐代正称节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化金部司郎中宋前期阶官性质。", "职掌",
        time="宋前期", event="为无职事的中行郎中阶，元丰后寄禄官易为朝散大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，为金部司长官，掌财货出纳政令",
        i, duty, "金部司长官", "建立金部司郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [beiqi, tang, song, reform], "重建金部司郎中北齐至元丰完整时间链。")
    rel(
        w, ft(w, fe(w, "金部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰金部司置郎中为司长。",
        "职掌", staff_quota=1, staff_type="官",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名和职事官名。")
    w.commit()


def entry1109():
    i = 1109
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity("金部司员外郎", "官职", "本条直接定义金部司员外郎。", quotation=main)
    sui = tp(
        w, eid, "隋开皇六年", "始有金部司员外郎之名；原书帝号与年号矛盾",
        i, origin, "金部司郎官", "按原书纪年建立金部司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    mark_citation_conflict(
        w, "Timepoints", sui, i, origin,
        "原书作“隋炀帝开皇六年”；开皇为隋文帝年号，帝号与年号内部矛盾。",
        "保留原书逐字引文，时间仅规范为隋开皇六年。", "职源",
    )
    song = tp(
        w, eid, "宋前期", "为无职事的中行员外郎阶，元丰后寄禄官易为朝散郎",
        i, duty, "文臣迁转官阶", "建立金部司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，为金部司副长官，郎中阙则主管本司",
        i, duty, "金部司副长官", "建立金部司员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [sui, song, reform], "连接金部司员外郎隋、宋前期与元丰节点。")
    rel(
        w, ft(w, fe(w, "金部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰金部司置员外郎为副长官。",
        "职掌", staff_quota=1, staff_type="官",
    )
    w.commit()


CANGBU_CASES = (
    "仓部司仓场案", "仓部司上供案", "仓部司巢籴案",
    "仓部司给纳案", "仓部司知杂案", "仓部司开拆案",
)


def entry1110():
    i = 1110
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "仓部司", "机构")
    sui = tp(
        w, eid, "隋", "仓部曹始称仓部司，列尚书省二十四司",
        i, origin, "尚书省户部属司", "建立仓部司隋代始称节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐贞观二十三年", "民部改户部，尚书省户部仓部司称谓确立",
        i, origin, "尚书省户部属司", "建立仓部司唐代正称节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化仓部司宋前期无职事。", "职掌",
        time="宋前期", event="存其名而无职事，由判仓部司事守司",
        category="尚书省户部属司",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判司一人、吏额二人。", "编制")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化元丰仓部司职掌。", "职掌",
        event="恢复职事，掌国家仓库场务储存政令及出纳",
        category="尚书省户部属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎官、六案及吏额。", "编制")
    south = tp(
        w, eid, "南宋", "沿置，吏额历经建炎、绍兴、隆兴、乾道及淳熙递减调整",
        i, staff, "尚书省户部属司", "建立仓部司南宋吏额沿革节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证仓部司为户部五司之一。")
    chain_all(w, eid, [sui, tang, song, reform, south], "重建仓部司隋至南宋完整时间链。")
    for title in CANGBU_CASES:
        case_e = w.entity(title, "机构", f"仓部司编制明确列出{title}。", quotation=staff)
        case_t = tp(
            w, case_e, "北宋元丰新制", "仓部司六案之一",
            i, staff, "仓部司办事机构", f"据仓部司编制建立{title}元丰节点。",
            "编制",
        )
        rel(w, reform, case_t, "上下级机构", i, staff, f"元丰{title}隶仓部司。", "编制")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1091, 1111)] == [
        "度支司", "度支司度支案", "度支司发运案", "度支司支供案", "度支司赏赐案",
        "度支司知杂案", "判度支司事", "度支司郎中", "度支司员外郎", "金部司",
        "金部司左藏案", "金部司右藏案", "金部司钱帛案", "金部司请给案",
        "金部司榷易案", "金部司知杂案", "判金部司事", "金部司郎中",
        "金部司员外郎", "仓部司",
    ]
    entry1091()
    duzhi_case(1092, "度支司度支案", "掌计划年度军国财用经费及年终会计诸路收支")
    duzhi_case(1093, "度支司发运案", "掌诸路上供总额、封桩、科买期限、漕运及运费")
    duzhi_case(1094, "度支司支供案", "掌文武官吏俸禄、内廷钱物及驿务支给")
    duzhi_case(1095, "度支司赏赐案", "掌赏赐、支赐及衣物钱帛的计划与按时给付")
    duzhi_case(1096, "度支司知杂案", "掌本司具体行政及生活事务")
    entry1097()
    entry1098()
    entry1099()
    entry1100()
    jinbu_case(1101, "金部司左藏案", "掌库藏出纳、金银钱帛丝绵及度量权衡之制")
    jinbu_case(1102, "金部司右藏案", "掌内藏宝货受纳、支借、拘催及杂物")
    entry1103()
    jinbu_case(1104, "金部司请给案", "掌合同取索财物、俸钱、请给券、冬服及杂给")
    jinbu_case(1105, "金部司榷易案", "掌市舶、榷场、禁榷及商税、香茶、盐矾等事")
    jinbu_case(1106, "金部司知杂案", "掌本司总务及文书收发")
    entry1107()
    entry1108()
    entry1109()
    entry1110()


if __name__ == "__main__":
    main()
