#!/usr/bin/env python3
"""提取 chapter2t4 第1591–1610条：六尚局吏匠、御药院与尚衣库。"""
import extract_2t4_1571_1590 as x

base = x.base
base.F = {i: base.load(i) for i in range(1591, 1611)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def bureau(w, title):
    return ft(w, fe(w, title, "机构"), "北宋崇宁二年二月")


def field_staff(i, title, parent, origins, event, officer_type, quota, *,
                time="北宋崇宁二年二月", grade=None):
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{parent}{title}。",
                   quotation=main)
    nodes = [
        tp(w, eid, origin_time, origin_event, i, history, "前代职源",
           f"建立{title}{origin_time}职源节点。", "职源与沿革",
           attr_officer_type=officer_type, chain="none")
        for origin_time, origin_event in origins
    ]
    active = tp(
        w, eid, time, event, i, history, f"{parent}官吏",
        f"建立{title}{time}节点。", "职源与沿革",
        attr_officer_type=officer_type, attr_grade=grade,
        chain="none" if nodes else "auto",
    )
    nodes.append(active)
    for name in ("职掌", "品位", "编制"):
        if name in F[i]["fields"]:
            cite(w, "Timepoints", active, i, field(i, name),
                 f"补证{title}{name}。", name)
    if len(nodes) > 1:
        chain_all(w, eid, nodes, f"连接{title}前代职源与宋代节点。")
    rel(w, bureau(w, parent), active, "编制隶属", i, main,
        f"{title}隶{parent}。", staff_quota=quota,
        staff_type=officer_type)
    w.commit()


def simple_staff(i, title, parent, event, officer_type, quota, *,
                 origins=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{parent}{title}。",
                   quotation=main)
    nodes = []
    for origin_time, origin_event in origins or ():
        nodes.append(tp(
            w, eid, origin_time, origin_event, i, main, "前代职源",
            f"建立{title}{origin_time}职源节点。",
            attr_officer_type=officer_type, chain="none",
        ))
    active = tp(
        w, eid, "北宋崇宁二年二月", event, i, main, f"{parent}官吏",
        f"建立{title}崇宁节点。", attr_officer_type=officer_type,
        chain="none" if nodes else "auto",
    )
    nodes.append(active)
    if len(nodes) > 1:
        chain_all(w, eid, nodes, f"连接{title}前代职源与崇宁节点。")
    rel(w, bureau(w, parent), active, "编制隶属", i, main,
        f"{title}隶{parent}。", staff_quota=quota,
        staff_type=officer_type)
    w.commit()


def grouped_role(i, title, children, officer_type):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条定义分隶各局的{title}通称。",
                   quotation=main)
    total = tp(
        w, eid, "北宋崇宁二年二月", f"殿中省各有关六尚局所置{title}通称",
        i, main, "六尚局吏人统称", f"建立{title}统称节点。",
        attr_officer_type=f"{officer_type}统称",
    )
    if "别名" in F[i]["fields"]:
        cite(w, "Timepoints", total, i, field(i, "别名"),
             f"{title}别名仅作名称证据。", "别名", note="纯别名")
    for parent, child_title, event, quota in children:
        child_eid = w.entity(
            child_title, "官职", f"{title}条明确列举{child_title}。",
            quotation=main,
        )
        child = tp(
            w, child_eid, "北宋崇宁二年二月", event, i, main,
            f"{parent}官吏", f"建立{child_title}节点。",
            attr_officer_type=officer_type,
        )
        rel(w, total, child, "统称与实例", i, main,
            f"{child_title}是{title}实例。")
        rel(w, bureau(w, parent), child, "编制隶属", i, main,
            f"{child_title}隶{parent}。", staff_quota=quota,
            staff_type=officer_type)
    w.commit()


def entry1607():
    i = 1607
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("御药院", "机构", "本条直接定义御药院沿革。",
                   quotation=main)
    transfer = tp(
        w, eid, "北宋崇宁二年二月", "大部职事归隶殿中省",
        i, main, "内侍供奉机构", "建立御药院崇宁职事转出节点。",
        chain="none",
    )
    restore = tp(
        w, eid, "北宋靖康元年正月五日", "依元丰法仍归隶入内内侍省",
        i, main, "内侍供奉机构", "建立御药院靖康复归节点。",
        chain="none",
    )
    renamed = w.find_timepoint(eid, "北宋崇宁二年五月九日")
    chain_all(
        w, eid, [transfer] + ([renamed] if renamed else []) + [restore],
        "连接御药院崇宁职事转出、改名与靖康复归节点。",
    )

    parent_eid = fe(w, "入内内侍省", "机构")
    parent_restore = tp(
        w, parent_eid, "北宋靖康元年正月五日", "御药院依元丰法复归隶",
        i, main, "内侍机构", "建立入内内侍省靖康接回御药院节点。",
        chain="none",
    )
    chain_all(
        w, parent_eid,
        [
            ft(w, parent_eid, "北宋至道三年"),
            ft(w, parent_eid, "北宋元丰七年八月"),
            parent_restore,
        ],
        "连接入内内侍省至道、元丰与靖康节点。",
    )
    rel(w, parent_restore, restore, "上下级机构", i, main,
        "靖康元年御药院复归入内内侍省。")
    w.commit()


def entry1608():
    i = 1608
    main = Q(i, F[i]["text"])
    w = W(i)
    medicine_eid = fe(w, "御药院", "机构")
    transfer = ft(w, medicine_eid, "北宋崇宁二年二月")
    rename = tp(
        w, medicine_eid, "北宋崇宁二年五月九日", "改名内药局",
        i, main, "内侍供奉机构", "建立御药院改名内药局节点。",
        chain="none",
    )
    restore = refine(
        w, ft(w, medicine_eid, "北宋靖康元年正月五日"), i, main,
        "内药局专条补全靖康复御药院旧名与职事。",
        event="复御药院旧名与职事，仍归隶入内内侍省",
        category="内侍供奉机构",
    )
    chain_all(
        w, medicine_eid, [transfer, rename, restore],
        "连接御药院崇宁职事转出、改名与靖康复名节点。",
    )

    eid = w.entity("内药局", "机构", "本条直接定义内药局。",
                   quotation=main)
    start = tp(
        w, eid, "北宋崇宁二年五月九日",
        "御药院改名内药局，主管划归尚药、尚衣局后所余供应、香表、国信礼物、殿试及夏药等职事",
        i, main, "内侍供奉机构", "建立内药局始置节点。",
        chain="none",
    )
    end = tp(
        w, eid, "北宋靖康元年正月五日", "复御药院旧名与职事",
        i, main, "内侍供奉机构", "建立内药局复旧名节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接内药局始置与复御药院节点。")
    rel(w, rename, start, "前后演变", i, main,
        "崇宁二年御药院改名内药局。")
    rel(w, end, restore, "前后演变", i, main,
        "靖康元年内药局复御药院旧名与职事。")
    w.commit()


def entry1609():
    i = 1609
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职能"), field(i, "编制"),
    )
    w = W(i)
    old_eid = w.entity("内衣库", "机构", "尚衣库沿革明确记载其旧名内衣库。",
                       quotation=history)
    old_end = tp(
        w, old_eid, "北宋大中祥符二年七月二十五日", "改为尚衣库",
        i, history, "宫廷衣物库", "建立内衣库改名节点。",
        "职源与沿革",
    )

    eid = w.entity("尚衣库", "机构", "本条直接定义尚衣库。",
                   quotation=main)
    start = tp(
        w, eid, "北宋大中祥符二年七月二十五日", "内衣库改名尚衣库",
        i, history, "殿中省所属库", "建立尚衣库始置节点。",
        "职源与沿革", chain="none",
    )
    merge = tp(
        w, eid, "北宋熙宁四年六月二十五日", "内衣物库并入",
        i, history, "殿中省所属库", "建立尚衣库接收内衣物库节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", merge, i, duty, "补证尚衣库职能。", "职能")
    cite(w, "Timepoints", merge, i, staff, "补证尚衣库官吏编制。", "编制")
    chain_all(w, eid, [start, merge], "连接尚衣库改名始置与熙宁合并节点。")

    merged_eid = w.entity(
        "内衣物库", "机构", "尚衣库沿革明确记载内衣物库并入。",
        quotation=history,
    )
    merged_end = tp(
        w, merged_eid, "北宋熙宁四年六月二十五日", "并入尚衣库",
        i, history, "宫廷衣物库", "建立内衣物库并入节点。",
        "职源与沿革",
    )
    rel(w, old_end, start, "前后演变", i, history,
        "大中祥符二年内衣库改为尚衣库。", "职源与沿革")
    rel(w, merged_end, merge, "前后演变", i, history,
        "熙宁四年内衣物库并入尚衣库。", "职源与沿革")
    rel(w, ft(w, fe(w, "殿中省", "机构"), "宋前期"),
        start, "上下级机构", i, main, "尚衣库隶殿中省。")
    w.commit()


def entry1610():
    i = 1610
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("监尚衣库", "官职", "本条直接定义监尚衣库差遣。",
                   quotation=main)
    tid = tp(
        w, eid, "北宋大中祥符二年七月以后",
        "由内侍与三班院使臣充，监修并进奉御殿、大礼、登位所需衮冕、服御及仪物",
        i, main, "尚衣库监官", "建立监尚衣库节点。",
        attr_officer_type="内侍或三班院使臣差遣",
    )
    rel(w, ft(w, fe(w, "尚衣库", "机构"),
              "北宋大中祥符二年七月二十五日"),
        tid, "编制隶属", i, main, "监尚衣库监领尚衣库。",
        staff_type="内侍或三班院使臣差遣")
    w.commit()


def entry1609_supervisor_quota():
    i = 1609
    staff = field(i, "编制")
    w = W(i)
    rid = base.relation_id(
        w, "尚衣库", "监尚衣库", "编制隶属",
        "北宋大中祥符二年七月二十五日",
        "北宋大中祥符二年七月以后",
    )
    assert rid
    base.set_rel_attrs(w, rid, 2, None, "尚衣库条明确监官二人。")
    cite(w, "Relationships", rid, i, staff,
         "补证监尚衣库编制二人。", "编制")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1591, 1611)] == [
        "医佐", "药童", "药工", "局长", "封人", "酒人", "酒工", "缝人",
        "典功", "染人", "衣徒", "幕士", "正供", "次供", "书吏", "贴书",
        "御药院", "内药局", "尚衣库", "监尚衣库",
    ]
    field_staff(
        1591, "医佐", "尚药局",
        [("隋大业三年", "始置医佐")],
        "始置，参掌供御汤药、诊候等事，序位在医正之下",
        "技术官", 4, time="北宋崇宁二年二月十二日",
        grade="从八品（政和二年后）",
    )
    simple_staff(1592, "药童", "尚药局",
                 "供差使煎熬、制作、奉送药饵、汤药等杂事", "公吏", 20)
    simple_staff(1593, "药工", "尚药局",
                 "掌秤药、捣碾草药等杂役", "公吏", 10)
    simple_staff(1594, "局长", "尚药局",
                 "由点检文字更名，点检本局行遣文字有无停滞违误", "公吏", 1)
    simple_staff(
        1595, "封人", "尚药局", "掌药方等文书及实封",
        "公吏", 3,
        origins=[("周代", "已有封人官名，但掌边界树立标志，与宋制不同")],
    )
    field_staff(
        1596, "酒人", "尚药局",
        [("周代", "已有酒人，掌酿造酒")],
        "始置，炊造酒料与酿酒", "工匠", 10,
    )
    simple_staff(1597, "酒工", "尚酝局",
                 "由长行斗子改，为诸酒库库吏", "公吏", 50)
    field_staff(
        1598, "缝人", "尚衣局",
        [("周代", "已有缝人")],
        "始置，裁缝衣服", "工匠", 12,
    )
    simple_staff(
        1599, "典功", "尚衣局",
        "制作奉御幞头、衣帽、靴履、腰带等穿戴物", "工匠", 20,
        origins=[("周代", "已有典妇功，但职掌与北宋典功不同")],
    )
    field_staff(
        1600, "染人", "尚衣局",
        [("周代", "已有染人")],
        "始置，为御服染色", "工匠", 7,
    )
    simple_staff(1601, "衣徒", "尚衣局",
                 "供局内杂役差使", "公吏", 20)
    simple_staff(
        1602, "幕士", "尚舍局",
        "由仪鸾司供御人改充，张设皇帝行止处帐幕幄帘", "公吏", 100,
        origins=[("周代", "已有幕人，为设置之始")],
    )
    grouped_role(1603, "正供", [
        ("尚舍局", "尚舍局正供",
         "由仪鸾司次供御改充，祗应幄帘帐设，位次幕士", 50),
        ("尚辇局", "尚辇局正供",
         "由御辇院供御辇官改充，祗应御用车驾乘舆，位居本局工匠最高", 220),
    ], "公吏")
    grouped_role(1604, "次供", [
        ("尚舍局", "尚舍局次供",
         "由仪鸾司搭材改名，为帐设工匠下手", 50),
        ("尚辇局", "尚辇局次供",
         "由御辇院次供御辇官改充，祗应御用辇舆，位在下都辇官上", 130),
    ], "公吏")
    grouped_role(1605, "书吏", [
        ("尚食局", "尚食局书吏", "由贴司改充，抄写本局文书", 7),
        ("尚药局", "尚药局书吏", "由贴司改充，抄写本局文书", 3),
        ("尚酝局", "尚酝局书吏", "由贴司改充，抄写本局文书", 2),
        ("尚衣局", "尚衣局书吏", "由贴司改充，抄写本局文书", 2),
        ("尚舍局", "尚舍局书吏", "由贴司改充，抄写本局文书", 2),
        ("尚辇局", "尚辇局书吏", "由贴司改充，抄写本局文书", 3),
    ], "公吏")
    grouped_role(1606, "贴书", [
        ("尚药局", "尚药局贴书",
         "由守阙贴司改充，掌抄写，位次书吏", 10),
        ("尚衣局", "尚衣局贴书",
         "由守阙贴司改充，掌抄写，位次书吏", 5),
    ], "公吏")
    entry1607()
    entry1608()
    entry1609()
    entry1610()
    entry1609_supervisor_quota()


if __name__ == "__main__":
    main()
