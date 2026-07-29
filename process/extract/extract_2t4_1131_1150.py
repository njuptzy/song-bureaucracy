#!/usr/bin/env python3
"""提取 chapter2t4 第1131–1150条：礼部诸案、礼部司与祠部司系统。"""
import extract_2t4_1111_1130 as x


base = x.base
base.F = {i: base.load(i) for i in range(1130, 1151)}
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


def refine_libu_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        f"专条细化{title}职掌。", None,
        event=event, category="礼部办事机构",
    )
    ordered = [north]
    south = w.find_timepoint(eid, "南宋建炎三年")
    if south is not None:
        ordered.append(south)
    chain_all(w, eid, ordered, f"确认{title}现有完整时间链。")
    w.commit()


def entry1131():
    i = 1131
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "礼部宝印案", "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        "专条细化礼部宝印案职掌。", None,
        event="掌官印的给赐、出借与请纳", category="礼部办事机构",
    )
    merged = tp(
        w, eid, "南宋建炎三年", "并入礼部封册案",
        i, main, "礼部办事机构", "建立宝印案建炎并省节点。",
        chain="none",
    )
    chain_all(w, eid, [north, merged], "连接宝印案元丰与建炎并省节点。")
    target_e = fe(w, "礼部封册案", "机构")
    target_n = ft(w, target_e, "北宋元丰新制")
    target_s = refine(
        w, ft(w, target_e, "南宋建炎三年"), i, main,
        "补充封册案接收宝印案职事。", None,
        event="接收并入的表奏案与宝印案职事", category="礼部办事机构",
    )
    chain_all(w, target_e, [target_n, target_s], "确认封册案元丰、建炎完整时间链。")
    rel(w, merged, target_s, "前后演变", i, main, "建炎三年宝印案并入封册案。")
    w.commit()


def entry1138():
    i = 1138
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "礼部司", "机构")
    sui_early = tp(
        w, eid, "隋初", "前身礼部曹",
        i, origin, "礼部所属司", "建立礼部司隋初职源节点。",
        "职源", chain="none",
    )
    sui_yang = tp(
        w, eid, "隋炀帝时", "礼部曹改为仪曹",
        i, origin, "礼部所属司", "建立礼部司隋炀帝改名节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐武德三年", "仪曹改为礼部司",
        i, origin, "礼部所属司", "建立礼部司唐代正名节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋代", "宋前期"), i, duty,
        "专条细化礼部司宋前期无职掌状态。", "职掌",
        time="宋前期", event="沿置但无实际职掌", category="礼部所属司",
    )
    reform = tp(
        w, eid, "北宋元丰新制", "参领礼乐、祭祀、朝会、宴享、学校与贡举事务",
        i, duty, "礼部所属司", "建立礼部司元丰恢复职事节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎中、员外郎各一人。", "编制")
    jianyan = tp(
        w, eid, "南宋建炎三年", "郎官仅置一员，并兼领主客司",
        i, staff, "礼部所属司", "建立礼部司建炎减员节点。",
        "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴元年", "礼部四司合置郎官一员通领",
        i, staff, "礼部所属司", "建立礼部司隆兴合领节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称材料补证礼部司为礼部四属之一。", "简称")
    cite(w, "Timepoints", reform, i, main, "正文补证礼部司为尚书省礼部四司之一。")
    chain_all(
        w, eid, [sui_early, sui_yang, tang, song, reform, jianyan, longxing],
        "重建礼部司隋初至南宋隆兴完整时间链。",
    )
    libu_e = fe(w, "礼部", "机构")
    rel(w, ft(w, libu_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期礼部司为礼部所属四司之一。")
    rel(w, ft(w, libu_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰礼部司隶礼部并参领礼乐贡举等事。", "职掌")
    w.commit()


def entry1139():
    i = 1139
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "礼部郎中", "官职")
    tang = tp(
        w, eid, "唐高祖武德年间", "礼部郎中之名始见",
        i, origin, "礼部司郎官", "建立礼部郎中唐代职源节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期", "北宋前期"), i, duty,
        "专条细化礼部郎中宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为后行郎中迁转阶，元丰后寄禄官易朝奉大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，领礼部司事并参预礼乐政令、起草礼仪表文",
        i, duty, "礼部司长官", "建立礼部郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证礼部司郎中一人。", "编制")
    cite(w, "Timepoints", reform, i, aliases, "简称与别名仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    chain_all(w, eid, [tang, song, reform], "连接礼部郎中唐代、宋前期与元丰节点。")
    rel(w, ft(w, fe(w, "礼部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, staff, "元丰礼部司置郎中一人。", "编制",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1140():
    i = 1140
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity("礼部员外郎", "官职", "本条直接定义礼部员外郎。", quotation=main)
    sui = tp(
        w, eid, "隋开皇六年", "礼部员外郎之名始置",
        i, origin, "礼部司郎官", "建立礼部员外郎隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事，为后行员外郎迁转阶，元丰后寄禄官易朝奉郎",
        i, duty, "文臣迁转官阶", "建立礼部员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰五年", "改为职事官，佐郎中掌礼部司事并专绘祥瑞图",
        i, duty, "礼部司副长官", "建立礼部员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证礼部司员外郎一人。", "编制")
    cite(w, "Timepoints", reform, i, aliases, "简称与别名仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    chain_all(w, eid, [sui, song, reform], "连接礼部员外郎隋代、宋前期与元丰节点。")
    rel(w, ft(w, fe(w, "礼部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, staff, "元丰礼部司置员外郎一人。", "编制",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1141():
    i = 1141
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "祠部司", "机构")
    sui = tp(
        w, eid, "隋", "作为礼部所属祠部曹出现",
        i, origin, "礼部所属司", "建立祠部司隋代机构职源节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐", "始有祠部司之名",
        i, origin, "礼部所属司", "建立祠部司唐代正名节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化祠部司宋前期职掌。", "职掌",
        time="宋前期", event="大部职掌旁落，仅掌祠祭日期、休假令、僧道名册与度牒",
        category="礼部所属司",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判祠部司事一人及吏额。", "编制")
    reform = tp(
        w, eid, "北宋元丰新制", "掌全国祀典、道佛教、祠庙及医药政令",
        i, duty, "礼部所属司", "建立祠部司元丰恢复职事节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎中、员外郎及所属办事机构。", "编制")
    jianyan = tp(
        w, eid, "南宋建炎三年", "祠部郎官仅置一员，并兼领膳部",
        i, staff, "礼部所属司", "建立祠部司建炎减员兼领节点。",
        "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴元年", "礼部、祠部合置郎官一员通领",
        i, staff, "礼部所属司", "建立祠部司隆兴合领节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与别名仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证祠部司为官司。")
    chain_all(w, eid, [sui, tang, song, reform, jianyan, longxing],
              "重建祠部司隋至南宋隆兴完整时间链。")
    libu_e = fe(w, "礼部", "机构")
    rel(w, ft(w, libu_e, "宋前期"), song, "上下级机构", i, duty,
        "宋前期祠部司隶属礼部。", "职掌")
    rel(w, ft(w, libu_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰祠部司为礼部所属司。", "职掌")

    cases = (
        ("祠部司道释案", "掌道教、佛教及度牒等事务"),
        ("详定祠祭、太医帐案", "掌祠祭、太医与僧道帐籍等事务"),
        ("祠部司知杂司", "总管祠部司杂务"),
        ("祠部司开拆司", "掌祠部司文书收发"),
    )
    for title, event in cases:
        case_e = w.entity(title, "机构", f"祠部司编制列有{title}。", quotation=staff)
        case_t = tp(
            w, case_e, "北宋元丰新制", event,
            i, staff, "祠部司办事机构", f"据祠部司编制建立{title}节点。",
            "编制",
        )
        rel(w, reform, case_t, "上下级机构", i, staff,
            f"{title}为祠部司办事机构。", "编制")
    w.commit()


def entry1142():
    i = 1142
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("判祠部司事", "官职", "本条直接定义北宋前期判祠部司事。", quotation=main)
    song = tp(
        w, eid, "北宋前期", "掌祠祭日期、休假令、僧道籍与度牒，由朝官充任",
        i, main, "判司差遣", "建立判祠部司事北宋前期节点。",
    )
    rel(w, ft(w, fe(w, "祠部司", "机构"), "宋前期"), song,
        "编制隶属", i, main, "北宋前期祠部司置判祠部司事一人。",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1143():
    i = 1143
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "祠部司郎中", "官职")
    tang = tp(
        w, eid, "唐初武德年间", "祠部郎中之名始见",
        i, origin, "祠部司郎官", "建立祠部司郎中唐代职源节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期", "北宋前期"), i, duty,
        "专条细化祠部司郎中北宋前期阶官性质。", "职掌",
        time="北宋前期", event="无职事，为文臣迁转官阶，元丰后寄禄官易朝奉大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为祠部司长官，实领祠部公事并提领度牒所",
        i, duty, "祠部司长官", "建立祠部司郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证元丰编制一人。", "编制")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    longxing = tp(
        w, eid, "南宋隆兴元年", "不再专置，由礼部一员郎官通领礼部、祠部",
        i, staff, "祠部司郎官", "建立祠部司郎中隆兴合领节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    chain_all(w, eid, [tang, song, reform, longxing],
              "连接祠部司郎中唐代、北宋前期、元丰与隆兴节点。")
    rel(w, ft(w, fe(w, "祠部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, staff, "元丰祠部司置郎中一人。", "编制",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1144():
    i = 1144
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    staff = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity("祠部司员外郎", "官职", "本条直接定义祠部司员外郎。", quotation=main)
    sui = tp(
        w, eid, "隋开皇六年", "祠部员外郎之名始置",
        i, origin, "祠部司郎官", "建立祠部司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事，为文臣迁转官阶，元丰后寄禄官易朝奉郎",
        i, duty, "文臣迁转官阶", "建立祠部司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为祠部司副长官，佐郎中领本司并提领度牒所",
        i, duty, "祠部司副长官", "建立祠部司员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证元丰编制一人。", "编制")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    longxing = tp(
        w, eid, "南宋隆兴元年", "不再专置，由礼部一员郎官通领礼部、祠部",
        i, staff, "祠部司郎官", "建立祠部司员外郎隆兴合领节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    chain_all(w, eid, [sui, song, reform, longxing],
              "连接祠部司员外郎隋代、宋前期、元丰与隆兴节点。")
    rel(w, ft(w, fe(w, "祠部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, staff, "元丰祠部司置员外郎一人。", "编制",
        staff_quota=1, staff_type="官")
    w.commit()


def refine_cibu_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    tid = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        f"专条细化{title}职掌。", None,
        event=event, category="祠部司办事机构",
    )
    chain_all(w, eid, [tid], f"确认{title}现有完整时间链。")
    w.commit()


def entry1147():
    i = 1147
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("祠部司制造案", "机构", "本条定义祠部所属制造案；加祠部司限定以避免同名机构混淆。", quotation=main)
    tid = tp(
        w, eid, "宋代", "掌度牒库官吏替换申请及度牒、紫衣、师号的制造书写审验",
        i, main, "祠部司办事机构", "原文未载始置年月，建立宋代概括节点。",
    )
    rel(w, ft(w, fe(w, "祠部司", "机构"), "北宋元丰新制"), tid,
        "上下级机构", i, main, "制造案为祠部办事部门；原文未载具体始置年月。")
    w.commit()


def entry1150():
    i = 1150
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("度牒库", "机构", "本条直接定义礼部祠部司所属度牒库。", quotation=main)
    store = tp(
        w, eid, "宋代", "制造、储存度牒，常备一万一千道或一万四千道",
        i, main, "祠部司监当机构", "原文未载始置年月，建立度牒库宋代节点。",
    )
    rel(w, ft(w, fe(w, "祠部司", "机构"), "北宋元丰新制"), store,
        "上下级机构", i, main, "原文明载度牒库隶礼部祠部司；未载具体始置年月。")
    post_e = w.entity("监度牒库", "官职", "度牒库条明确设监度牒库官一员。", quotation=main)
    post_t = tp(
        w, post_e, "宋代", "主管度牒库",
        i, main, "监当官", "据度牒库编制建立监度牒库宋代节点。",
    )
    rel(w, store, post_t, "编制隶属", i, main, "度牒库置监度牒库官一员。",
        staff_quota=1, staff_type="官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1131, 1151)] == [
        "礼部宝印案", "礼部检法案", "礼部礼乐案", "礼部贡举案",
        "礼部宗正案", "礼部知杂案", "礼部开拆案", "礼部司",
        "礼部郎中", "礼部员外郎", "祠部司", "判祠部司事",
        "祠部司郎中", "祠部司员外郎", "祠部司道释案",
        "详定祠祭、太医帐案", "制造案", "知杂司", "开拆司", "度牒库",
    ]
    entry1131()
    refine_libu_case(1132, "礼部检法案", "掌礼部四司条例法令的汇编与检阅")
    refine_libu_case(1133, "礼部礼乐案", "掌五礼仪式、乐制、器服与牲牢")
    refine_libu_case(1134, "礼部贡举案", "掌学校经籍、科举发解、省试及赐书修史")
    refine_libu_case(1135, "礼部宗正案", "掌后妃宗室礼仪、赏赐、婚冠丧葬与经义考试")
    refine_libu_case(1136, "礼部知杂案", "掌礼部杂事")
    refine_libu_case(1137, "礼部开拆案", "掌礼部文书收发")
    entry1138()
    entry1139()
    entry1140()
    entry1141()
    entry1142()
    entry1143()
    entry1144()
    refine_cibu_case(1145, "祠部司道释案", "掌坟寺申请、经书、紫衣师号、宫观寺院、度牒及僧道官迁补")
    refine_cibu_case(1146, "详定祠祭、太医帐案", "掌医官磨勘、太医局生考试、祠祭祈告、寺观赐额及僧道帐籍")
    entry1147()
    refine_cibu_case(1148, "祠部司知杂司", "总管祠部司杂务")
    refine_cibu_case(1149, "祠部司开拆司", "掌祠部司文书收发")
    entry1150()


if __name__ == "__main__":
    main()
