#!/usr/bin/env python3
"""提取 chapter2t4 第1071–1090条：户部司郎官、左曹与右曹诸案。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(1071, 1091)}
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine


def field(i, name):
    return Q(i, x.b.F[i]["fields"][name], name)


def ft_any(w, entity_id, *times):
    for time in times:
        timepoint_id = w.find_timepoint(entity_id, time)
        if timepoint_id is not None:
            return timepoint_id
    raise AssertionError((entity_id, times))


def entry1071():
    i = 1071
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "户部司郎中", "官职")
    tang = tp(
        w, eid, "唐贞观二十三年", "始有尚书省户部户部司郎中之名",
        i, origin, "尚书省户部司郎官", "建立户部司郎中唐代职源节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化户部司郎中宋前期阶官性质与品位。", "职掌",
        time="宋前期", event="为无职事的中行郎中阶，元丰后寄禄官易为朝散大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，郎中二员分左曹、右曹治事",
        i, duty, "尚书省户部司郎官", "建立户部司郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰改制后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与分曹通称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [tang, song, reform], "重建户部司郎中唐、宋前期和元丰完整时间链。")
    rel(
        w, ft(w, fe(w, "户部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰户部司置郎中二员，分左、右曹治事。",
        "职掌", staff_quota=2, staff_type="官",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证本条兼具官阶名与职事官名。")
    w.commit()


def entry1072():
    i = 1072
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity("户部司员外郎", "官职", "本条直接定义户部司员外郎。", quotation=main)
    tang = tp(
        w, eid, "唐贞观二十三年", "始有尚书省户部户部司员外郎之正称",
        i, origin, "尚书省户部司郎官", "建立户部司员外郎唐代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "为无职事的中行员外郎阶，元丰后寄禄官易为朝散郎",
        i, duty, "文臣迁转官阶", "建立户部司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，按资序分治左曹、右曹事",
        i, duty, "尚书省户部司郎官", "建立户部司员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰新制后正七品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [tang, song, reform], "连接户部司员外郎唐、宋前期和元丰节点。")
    rel(
        w, ft(w, fe(w, "户部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰户部司员外郎按资序分治左、右曹。",
        "职掌", staff_type="官",
    )
    w.commit()


LEFT_CASES = (
    "户部左曹户口案", "户部左曹税赋案", "户部左曹农田案",
    "户部左曹检法案", "户部左曹知杂案",
)


def entry1073():
    i = 1073
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "户部左曹", "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化户部左曹元丰职掌。", "职掌",
        event="始置，掌全国户口、农田、贡赋、税租及诸课入政令",
        category="尚书省户部属司",
    )
    cite(w, "Timepoints", north, i, origin, "补证元丰五年以三司归户部并分左、右曹。", "职源")
    cite(w, "Timepoints", north, i, staff, "补证元丰左曹五案与吏额编制。", "编制")
    south = tp(
        w, eid, "南宋", "办事案减为户口、农田、检法三案，左曹郎官共一员",
        i, staff, "尚书省户部属司", "建立户部左曹南宋编制节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", north, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [north, south], "连接户部左曹元丰与南宋节点。")
    for title in LEFT_CASES:
        case_e = w.entity(title, "机构", f"编制字段明确列出{title}。", quotation=staff)
        case_n = tp(
            w, case_e, "北宋元丰新制", "户部左曹五案之一",
            i, staff, "户部左曹办事机构", f"据左曹编制建立{title}元丰节点。",
            "编制", chain="none",
        )
        ordered = [case_n]
        rel(w, north, case_n, "上下级机构", i, staff, f"元丰{title}隶户部左曹。", "编制")
        if title in ("户部左曹户口案", "户部左曹农田案", "户部左曹检法案"):
            case_s = tp(
                w, case_e, "南宋", "户部左曹保留的三案之一",
                i, staff, "户部左曹办事机构", f"据左曹编制建立{title}南宋节点。",
                "编制", chain="none",
            )
            ordered.append(case_s)
            rel(w, south, case_s, "上下级机构", i, staff, f"南宋{title}仍隶户部左曹。", "编制")
        existing_south = w.find_timepoint(case_e, "南宋")
        if existing_south is not None and existing_south not in ordered:
            ordered.append(existing_south)
        chain_all(w, case_e, ordered, f"重建{title}完整时间链。")
    cite(w, "Timepoints", north, i, main, "正文补证户部左曹为户部五司之一。")
    w.commit()


def left_case_entry(i, title, event):
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        f"专条细化{title}职掌。", None, event=event,
        category="户部左曹办事机构",
    )
    south = w.find_timepoint(eid, "南宋")
    if south:
        refine(
            w, south, i, main, f"专条补证南宋沿置的{title}职掌。", None,
            event=event, category="户部左曹办事机构",
        )
        chain_all(w, eid, [north, south], f"确认{title}元丰至南宋完整时间链。")
    else:
        chain_all(w, eid, [north], f"确认{title}现有完整时间链。")
    w.commit()


def entry1075():
    i = 1075
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "户部左曹税赋案", "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        "专条细化税赋案职掌。", None,
        event="掌二税支移、折变、房地税、僧道免丁钱及课利",
        category="户部左曹办事机构",
    )
    south = tp(
        w, eid, "南宋", "事务繁剧，分为二税窠、房地窠、课利窠",
        i, main, "户部左曹办事机构", "建立税赋案南宋分窠节点。",
        chain="none",
    )
    chain_all(w, eid, [north, south], "连接户部左曹税赋案元丰与南宋分窠节点。")
    w.commit()


def tax_branch(i, title, event):
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(title, "机构", f"第{i}条直接定义{title}。", quotation=main)
    tid = tp(
        w, eid, "南宋", event, i, main, "户部左曹税赋案分窠",
        f"建立{title}南宋节点。",
    )
    rel(
        w, ft(w, fe(w, "户部左曹税赋案", "机构"), "南宋"), tid,
        "上下级机构", i, main, f"{title}由户部左曹税赋案分出。",
    )
    w.commit()


RIGHT_CASES = (
    "户部右曹常平案", "户部右曹免役案", "户部右曹坊场案",
    "户部右曹检法案", "户部右曹知杂案",
)


def entry1082():
    i = 1082
    main = Q(i, x.b.F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "户部右曹", "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化户部右曹元丰职掌。", "职掌",
        event="始置，掌常平、免役、坊场、河渡、水利、义仓赈济等政令",
        category="尚书省户部属司",
    )
    cite(w, "Timepoints", north, i, origin, "补证元丰五年置左、右曹。", "职源")
    cite(w, "Timepoints", north, i, staff, "补证元丰右曹五案与吏额。", "编制")
    south = tp(
        w, eid, "南宋", "增平准案，合常平、免役、坊场、检法、知杂为六案",
        i, staff, "尚书省户部属司", "建立户部右曹南宋六案节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", south, i, aliases, "简称与拟称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [north, south], "连接户部右曹元丰与南宋节点。")
    for title in RIGHT_CASES:
        case_e = w.entity(title, "机构", f"编制字段明确列出{title}。", quotation=staff)
        case_n = tp(
            w, case_e, "北宋元丰新制", "户部右曹五案之一",
            i, staff, "户部右曹办事机构", f"据右曹编制建立{title}元丰节点。",
            "编制", chain="none",
        )
        case_s = tp(
            w, case_e, "南宋", "户部右曹六案之一",
            i, staff, "户部右曹办事机构", f"据右曹编制建立{title}南宋节点。",
            "编制", chain="none",
        )
        chain_all(w, case_e, [case_n, case_s], f"连接{title}元丰与南宋节点。")
        rel(w, north, case_n, "上下级机构", i, staff, f"元丰{title}隶户部右曹。", "编制")
        rel(w, south, case_s, "上下级机构", i, staff, f"南宋{title}仍隶户部右曹。", "编制")
    flat_e = w.entity("户部右曹平准案", "机构", "南宋编制明确增设平准案。", quotation=staff)
    flat_s = tp(
        w, flat_e, "南宋", "增设，为户部右曹六案之一",
        i, staff, "户部右曹办事机构", "建立户部右曹平准案南宋节点。",
        "编制",
    )
    rel(w, south, flat_s, "上下级机构", i, staff, "南宋平准案隶户部右曹。", "编制")
    cite(w, "Timepoints", north, i, main, "正文补证户部右曹为户部五司之一。")
    w.commit()


def right_case_entry(i, title, event):
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    north = w.find_timepoint(eid, "北宋元丰新制")
    south = ft(w, eid, "南宋")
    ordered = []
    if north:
        refine(
            w, north, i, main, f"专条细化{title}元丰职掌。", None,
            event=event, category="户部右曹办事机构",
        )
        ordered.append(north)
    refine(
        w, south, i, main, f"专条细化{title}南宋职掌。", None,
        event=event, category="户部右曹办事机构",
    )
    ordered.append(south)
    chain_all(w, eid, ordered, f"确认{title}完整时间链。")
    w.commit()


def divided_post(i, title, side):
    main = Q(i, x.b.F[i]["text"])
    duty = field(i, "职掌")
    aliases = field(i, "简称与别名")
    origin = field(i, "职源") if "职源" in x.b.F[i]["fields"] else main
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}为户部郎中、员外郎分工称。", quotation=main)
    tid = tp(
        w, eid, "北宋元丰五年", f"户部郎中、员外郎分工称，参掌户部{side}曹事",
        i, origin, "户部司郎官分工称", f"建立{title}元丰分工节点。",
        "职源" if "职源" in x.b.F[i]["fields"] else None,
    )
    cite(w, "Timepoints", tid, i, duty, f"补证参掌户部{side}曹事。", "职掌")
    cite(w, "Timepoints", tid, i, aliases, "简称与具体衔名仅作称谓证据。",
         "简称与别名", note="纯简称")
    rel(
        w, ft(w, fe(w, f"户部{side}曹", "机构"), "北宋元丰新制"), tid,
        "编制隶属", i, origin, f"{title}参掌户部{side}曹事。",
        "职源" if "职源" in x.b.F[i]["fields"] else None, staff_type="官",
    )
    for generic in ("户部司郎中", "户部司员外郎"):
        rel(
            w, ft(w, fe(w, generic, "官职"), "北宋元丰新制"), tid,
            "统称与实例", i, main, f"{title}是{generic}按左、右曹分工的称谓。",
        )
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(1071, 1091)] == [
        "户部司郎中", "户部司员外郎", "户部左曹", "户部左曹户口案",
        "户部左曹税赋案", "户部左曹农田案", "户部左曹检法案",
        "户部左曹知杂案", "户部左曹二税窠", "户部左曹房地窠",
        "户部左曹课利窠", "户部右曹", "户部右曹常平案",
        "户部右曹免役案", "户部右曹坊场案", "户部右曹平准案",
        "户部右曹检法案", "户部右曹知杂案", "户部左曹郎中、员外郎",
        "户部右曹郎中、员外郎",
    ]
    entry1071()
    entry1072()
    entry1073()
    left_case_entry(1074, "户部左曹户口案", "掌户口、婚姻、良贱、债务、官户及户绝财产等事")
    entry1075()
    left_case_entry(1076, "户部左曹农田案", "掌农田、田讼、灾伤查报及劝课农桑等事")
    left_case_entry(1077, "户部左曹检法案", "掌本曹法令条例检阅")
    left_case_entry(1078, "户部左曹知杂案", "掌本曹文书收发及具体事务办理")
    tax_branch(1079, "户部左曹二税窠", "由税赋案分出，掌二税受纳、驱磨、隐匿、支移、折变")
    tax_branch(1080, "户部左曹房地窠", "由税赋案分出，掌楼店务、房廊课利、官地侵占及房地钱等事")
    tax_branch(1081, "户部左曹课利窠", "由税赋案分出，掌酒务课利、盐场酒务租额及牙契等事")
    entry1082()
    right_case_entry(1083, "户部右曹常平案", "掌常平仓、水利、义仓救济、户绝田产及居养等事")
    right_case_entry(1084, "户部右曹免役案", "掌免役及不列民兵教阅的伍、保事")
    right_case_entry(1085, "户部右曹坊场案", "掌坊场河渡专利、纲运路费及公使人吏分配酬赏")
    right_case_entry(1086, "户部右曹平准案", "掌市易、平抑物价、抵当、医药石及木炭等事")
    right_case_entry(1087, "户部右曹检法案", "掌本曹法令条例检阅")
    right_case_entry(1088, "户部右曹知杂案", "掌本曹文书收发及具体事务办理")
    divided_post(1089, "户部左曹郎中、员外郎", "左")
    divided_post(1090, "户部右曹郎中、员外郎", "右")


if __name__ == "__main__":
    main()
