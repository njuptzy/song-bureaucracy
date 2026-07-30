#!/usr/bin/env python3
"""提取 chapter2t4 第1571–1590条：六尚局官属与尚食、尚药技术人员。"""
import extract_2t4_1551_1570 as x

base = x.base
base.F = {i: base.load(i) for i in range(1571, 1591)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def alias(w, tid, i):
    for key in ("简称", "简称与别名", "别称", "别名", "合称"):
        if key in F[i]["fields"]:
            cite(w, "Timepoints", tid, i, field(i, key),
                 f"{F[i]['title']}称谓仅作名称证据。", key,
                 note="纯简称、别名或合称")


def palace(w):
    return ft(w, fe(w, "殿中省", "机构"), "北宋崇宁二年二月十二日")


def six_group(w):
    return ft(w, fe(w, "殿中省六尚局", "机构"), "北宋崇宁二年二月")


def bureau(w, title):
    return ft(w, fe(w, title, "机构"), "北宋崇宁二年二月")


def entry1571():
    i = 1571
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("勾当太官局", "官职", "本条直接定义勾当太官局差遣。",
                   quotation=main)
    tid = tp(w, eid, "北宋崇宁二年五月十四日",
             "由勾当御厨官改置，为太官局监官，由内侍充",
             i, main, "太官局差遣", "建立勾当太官局始置节点。",
             attr_officer_type="内侍差遣")
    rel(w, ft(w, fe(w, "太官局", "机构"), "北宋崇宁二年二月十二日"),
        tid, "编制隶属", i, main, "勾当太官局监领太官局。",
        staff_quota=3, staff_type="内侍差遣")
    w.commit()


def six_bureau_entry(i, title, specs, formal_event):
    main, history, duty = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌")
    w = W(i)
    eid = fe(w, title, "机构")
    new_nodes = []
    for time, event, category in specs:
        new_nodes.append(tp(w, eid, time, event, i, history, category,
                            f"建立{title}{time}节点。", "职源与沿革", chain="none"))
    formal = refine(w, ft(w, eid, "北宋崇宁二年二月"), i, duty,
                    f"专条补证{title}崇宁后职掌。",
                    event=formal_event, category="殿中省所属机构")
    end = tp(w, eid, "北宋靖康元年", f"罢{title}",
             i, history, "殿中省所属机构", f"建立{title}靖康罢置节点。",
             "职源与沿革", chain="none")
    cite(w, "Timepoints", formal, i, duty, f"补证{title}崇宁后职掌。", "职掌")
    if "编制" in F[i]["fields"]:
        cite(w, "Timepoints", formal, i, field(i, "编制"),
             f"补证{title}官吏编制。", "编制")
    alias(w, formal, i)
    chain_all(w, eid, new_nodes + [formal, end], f"连接{title}职源、宋前期、崇宁与靖康节点。")
    song_node = next((node for node, spec in zip(new_nodes, specs)
                      if spec[0].startswith("宋前期") or spec[0].startswith("北宋初")), None)
    if song_node:
        rel(w, ft(w, fe(w, "殿中省", "机构"), "宋前期"), song_node,
            "上下级机构", i, main, f"宋前期{title}空隶殿中省。")
    rel(w, palace(w), formal, "上下级机构", i, main,
        f"崇宁正式建置{title}，隶殿中省。")
    w.commit()


def entry1577():
    i = 1577
    main, history, duty = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌")
    w = W(i)
    eid = w.entity("尚乘局", "机构", "本条直接定义殿中省尚乘局。",
                   quotation=main)
    specs = [
        ("秦汉", "太仆为尚乘职事之始", "前代职源"),
        ("隋大业三年", "置殿内省尚乘局", "前代职源"),
        ("唐武德元年", "改为殿中省尚乘局", "前代职源"),
        ("北宋初", "空存其名，职事归骐骥院、内鞍辔库", "殿中省所属机构"),
        ("北宋元丰新制", "罢尚乘局，另新增尚酝局", "殿中省所属机构"),
    ]
    nodes = [
        tp(w, eid, time, event, i, history, category,
           f"建立尚乘局{time}节点。", "职源与沿革", chain="none")
        for time, event, category in specs
    ]
    cite(w, "Timepoints", nodes[3], i, duty, "补证北宋尚乘局职掌归属。", "职掌")
    chain_all(w, eid, nodes, "连接尚乘局秦汉职源、隋唐、北宋与元丰罢置节点。")
    rel(w, ft(w, fe(w, "殿中省", "机构"), "宋前期"), nodes[3],
        "上下级机构", i, main, "北宋初尚乘局空隶殿中省。")
    rel(w, ft(w, fe(w, "殿中省六尚局", "机构"), "宋前期"), nodes[3],
        "统称与实例", i, main, "尚乘局是宋前期六尚局实例。")
    rel(w, nodes[4], ft(w, fe(w, "尚酝局", "机构"), "北宋崇宁二年二月"),
        "前后演变", i, main, "元丰罢尚乘局并另增尚酝局。")
    w.commit()


SIX = ("尚食局", "尚药局", "尚酝局", "尚衣局", "尚舍局", "尚辇局")


def generic_six_role(i, title, event, *, quotas=None, history_fields=True,
                     end_event=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条定义六尚局各局所置{title}通称。",
                   quotation=main)
    nodes = []
    if history_fields:
        history = field(i, "职源与沿革")
        if title == "典御":
            nodes.extend([
                tp(w, eid, "北齐", "门下省置典御", i, history, "前代职源",
                   "建立典御北齐职源节点。", "职源与沿革", chain="none"),
                tp(w, eid, "隋初", "殿内局设典御", i, history, "前代职源",
                   "建立典御隋代节点。", "职源与沿革", chain="none"),
            ])
        elif title == "奉御":
            nodes.extend([
                tp(w, eid, "隋大业三年", "典御改为奉御", i, history, "前代职源",
                   "建立奉御隋代节点。", "职源与沿革", chain="none"),
                tp(w, eid, "唐武德元年", "改为殿中省六尚局奉御", i, history, "前代职源",
                   "建立奉御唐代节点。", "职源与沿革", chain="none"),
                tp(w, eid, "宋前期", "六尚局沿置奉御，罕以除人", i, history, "六尚局职事官",
                   "建立奉御宋前期节点。", "职源与沿革", chain="none"),
            ])
    start = tp(w, eid, "北宋崇宁二年二月", event,
               i, main if not history_fields else field(i, "职掌"),
               "六尚局职事官", f"建立{title}崇宁节点。",
               None if not history_fields else "职掌",
               attr_officer_type="职事官", chain="none")
    nodes.append(start)
    if history_fields:
        end = tp(w, eid, "北宋靖康元年", f"随殿中省罢{title}",
                 i, field(i, "职源与沿革"), "六尚局职事官",
                 f"建立{title}靖康罢置节点。", "职源与沿革",
                 attr_officer_type="职事官", chain="none")
        nodes.append(end)
        if "品位" in F[i]["fields"]:
            cite(w, "Timepoints", start, i, field(i, "品位"), f"补证{title}品位。", "品位")
        if "编制" in F[i]["fields"]:
            cite(w, "Timepoints", start, i, field(i, "编制"), f"补证{title}编制。", "编制")
        alias(w, start, i)
    elif end_event:
        nodes.append(tp(w, eid, "北宋靖康元年", end_event,
                        i, main, "六尚局职事官", f"建立{title}靖康罢置节点。",
                        attr_officer_type="职事官", chain="none"))
    chain_all(w, eid, nodes, f"连接{title}职源、崇宁设置与罢置节点。")
    for bureau_title in SIX:
        child_title = (
            title.replace("某局", bureau_title)
            if "某局" in title else f"{bureau_title}{title}"
        )
        child_eid = w.entity(child_title, "官职", f"{title}条明确列举{child_title}。",
                             quotation=main)
        quota = quotas.get(bureau_title) if quotas else None
        child_tid = tp(w, child_eid, "北宋崇宁二年二月",
                       f"{bureau_title}所属{title}", i, main,
                       "六尚局职事官", f"建立{child_title}节点。",
                       attr_officer_type="职事官")
        rel(w, start, child_tid, "统称与实例", i, main,
            f"{child_title}是{title}实例。")
        rel(w, bureau(w, bureau_title), child_tid, "编制隶属", i, main,
            f"{child_title}隶{bureau_title}。", staff_quota=quota,
            staff_type="职事官")
    w.commit()


def entry1578():
    generic_six_role(1578, "管勾殿中省某局",
                     "随殿中省始置，由内侍充，为六尚各局监领官",
                     quotas={title: 1 for title in SIX}, history_fields=False,
                     end_event="随殿中省罢管勾六尚各局")


def entry1581():
    i = 1581
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("典奉御", "官职", "本条定义典御、奉御连称。",
                   quotation=main)
    total = tp(w, eid, "北宋崇宁二年以后", "殿中省六尚局典御、奉御连称",
               i, main, "六尚局官连称", "建立典奉御连称节点。",
               attr_officer_type="官职连称")
    rel(w, total, ft(w, fe(w, "典御", "官职"), "北宋崇宁二年二月"),
        "统称与实例", i, main, "典御是典奉御连称实例。")
    rel(w, total, ft(w, fe(w, "奉御", "官职"), "北宋崇宁二年二月"),
        "统称与实例", i, main, "奉御是典奉御连称实例。")
    w.commit()


def entry1582():
    generic_six_role(1582, "监门", "六尚各局置监门，掌守本局大门及人、物出入",
                     quotas={title: (1 if title == "尚舍局" else 2) for title in SIX},
                     history_fields=False)


def technical_post(i, title, parent, time, event, officer_type, quota, *, origins=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{parent}{title}。", quotation=main)
    nodes = []
    if origins:
        source_key = "职源与沿革" if "职源与沿革" in F[i]["fields"] else "职源"
        source = field(i, source_key)
        for origin_time, origin_event in origins:
            nodes.append(tp(w, eid, origin_time, origin_event, i, source, "前代职源",
                            f"建立{title}{origin_time}职源节点。", source_key,
                            attr_officer_type=officer_type, chain="none"))
    source = field(i, "职源与沿革") if "职源与沿革" in F[i]["fields"] else (
        field(i, "职源") if "职源" in F[i]["fields"] else main
    )
    source_key = "职源与沿革" if "职源与沿革" in F[i]["fields"] else (
        "职源" if "职源" in F[i]["fields"] else None
    )
    tid = tp(w, eid, time, event, i, source, f"{parent}官吏",
             f"建立{title}{time}节点。", source_key,
             attr_officer_type=officer_type, chain="none" if nodes else "auto")
    if "职掌" in F[i]["fields"]:
        cite(w, "Timepoints", tid, i, field(i, "职掌"), f"补证{title}职掌。", "职掌")
    if "品位" in F[i]["fields"]:
        cite(w, "Timepoints", tid, i, field(i, "品位"), f"补证{title}品位。", "品位")
    if "编制" in F[i]["fields"]:
        cite(w, "Timepoints", tid, i, field(i, "编制"), f"补证{title}编制。", "编制")
    if nodes:
        chain_all(w, eid, nodes + [tid], f"连接{title}前代职源与崇宁节点。")
    rel(w, bureau(w, parent), tid, "编制隶属", i, main,
        f"{title}隶{parent}。", staff_quota=quota, staff_type=officer_type)
    w.commit()


def simple_staff(i, title, parent, event, officer_type, quota):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{parent}{title}。", quotation=main)
    tid = tp(w, eid, "北宋崇宁二年二月", event,
             i, main, f"{parent}官吏", f"建立{title}节点。",
             attr_officer_type=officer_type)
    rel(w, bureau(w, parent), tid, "编制隶属", i, main,
        f"{title}隶{parent}。", staff_quota=quota, staff_type=officer_type)
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1571, 1591)] == [
        "勾当太官局", "尚药局", "尚酝局", "尚衣局", "尚舍局", "尚辇局",
        "尚乘局", "管勾殿中省某局", "典御", "奉御", "典奉御", "监门",
        "食医", "膳工", "膳徒", "司珍", "杂役", "医师", "御医", "医正",
    ]
    entry1571()
    six_bureau_entry(1572, "尚药局", [
        ("北齐", "门下省已有尚药局", "前代职源"),
        ("唐代", "尚药局归隶殿中省", "前代职源"),
        ("宋前期", "空存其名，职事归医官院", "殿中省所属机构"),
    ], "正式举职，供奉御药、和剂诊候治病")
    six_bureau_entry(1573, "尚酝局", [
        ("北宋元祐时", "元祐官品令始见尚酝局", "殿中省所属机构"),
    ], "供奉御用酒醴")
    six_bureau_entry(1574, "尚衣局", [
        ("先秦战国", "已有尚服、尚衣、尚冠职事", "前代职源"),
        ("北齐至唐", "由主衣局演变为殿中省尚衣局", "前代职源"),
        ("宋前期", "空存其名，职事归尚衣库", "殿中省所属机构"),
    ], "正式举职，供御衣服及冠冕")
    six_bureau_entry(1575, "尚舍局", [
        ("先秦周代", "掌舍、掌行为尚舍职事之始", "前代职源"),
        ("隋唐", "隋置尚舍局，唐改为殿中省尚舍局", "前代职源"),
        ("宋前期", "空存其名，职事归仪鸾司", "殿中省所属机构"),
    ], "正式举职，掌供御帷幕幄帘张设")
    six_bureau_entry(1576, "尚辇局", [
        ("秦汉", "车府令为尚辇职事之始", "前代职源"),
        ("隋唐", "隋置尚辇局，唐改为殿中省尚辇局", "前代职源"),
        ("宋前期", "空存其名，职事归御辇院", "殿中省所属机构"),
    ], "正式举职，掌供御用辇舆")
    entry1577()
    entry1578()
    generic_six_role(1579, "典御", "六尚各局各置二人，佐本局管勾官领供奉事",
                     quotas={title: 2 for title in SIX})
    generic_six_role(1580, "奉御", "六尚各局奉御专掌监督本局供奉事",
                     quotas={title: (6 if title == "尚食局" else 4) for title in SIX})
    entry1581()
    entry1582()
    technical_post(1583, "食医", "尚食局", "北宋崇宁二年二月",
                   "辨验供御饮食及禁忌食品", "技术官", 4,
                   origins=[("周代", "已有食医之名"), ("隋代", "殿中省尚食局置食医")])
    simple_staff(1584, "膳工", "尚食局", "制作进御或宴饷百官饭菜", "工匠", 200)
    simple_staff(1585, "膳徒", "尚食局", "托盘送进御或朝会宴饷饮食", "公吏", 30)
    simple_staff(1586, "司珍", "尚食局", "由翰林司供御人员充，掌供御事", "公吏", 60)
    simple_staff(1587, "杂役", "尚食局", "供局内差使及杂役事", "给使", 30)
    technical_post(1588, "医师", "尚药局", "北宋崇宁二年二月十二日",
                   "侍奉皇帝疾病诊治、配方、和药", "技术官", 2,
                   origins=[("周代", "已有医师之名")])
    technical_post(1589, "御医", "尚药局", "北宋崇宁二年二月十二日",
                   "侍奉皇帝诊治配方和药，序位在医师下", "技术官", 4,
                   origins=[("晋代", "已有御医之名"), ("隋代", "尚药局置侍御医")])
    technical_post(1590, "医正", "尚药局", "北宋崇宁二年二月十二日",
                   "侍奉皇帝诊治配方和药，序位在御医下", "技术官", 4)


if __name__ == "__main__":
    main()
