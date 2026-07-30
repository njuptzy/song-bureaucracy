#!/usr/bin/env python3
"""提取 chapter2t4 第1611–1630条：衣物诸库、库吏与六尚局库务。"""
import extract_2t4_1591_1610 as x

base = x.base
base.F = {
    i: base.load(i)
    for i in [1568, *range(1611, 1631)]
}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def bureau(w, title):
    return ft(w, fe(w, title, "机构"), "北宋崇宁二年二月")


def entry1611():
    i = 1611
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "内衣库", "机构")
    end = ft(w, eid, "北宋大中祥符二年七月二十五日")
    cite(w, "Timepoints", end, i, main, "补证内衣库为尚衣库旧名。")
    rid = base.relation_id(
        w, "内衣库", "尚衣库", "前后演变",
        "北宋大中祥符二年七月二十五日",
        "北宋大中祥符二年七月二十五日",
    )
    assert rid
    cite(w, "Relationships", rid, i, main,
         "补证内衣库改称尚衣库。")
    w.commit()


def simple_supervisor(i, title, parent, parent_time, time, event,
                      officer_type, quota=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}差遣。",
                   quotation=main)
    tid = tp(
        w, eid, time, event, i, main, f"{parent}监官",
        f"建立{title}节点。", attr_officer_type=officer_type,
    )
    rel(w, ft(w, fe(w, parent, "机构"), parent_time),
        tid, "编制隶属", i, main, f"{title}监领{parent}。",
        staff_quota=quota, staff_type=officer_type)
    w.commit()


def entry1613():
    i = 1613
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("衣库", "机构", "本条直接定义衣库。",
                   quotation=main)
    start = tp(
        w, eid, "北宋开宝三年四月二十九日",
        "始置，收纳左藏库制造、给赐宗室近臣及禁军将校的时服",
        i, main, "宫廷衣物库", "建立衣库始置节点。",
        chain="none",
    )
    end = tp(
        w, eid, "北宋大中祥符元年以前", "改名内衣物库",
        i, main, "宫廷衣物库", "建立衣库改名节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接衣库始置与改名节点。")

    inner_eid = fe(w, "内衣物库", "机构")
    inner_start = w.find_timepoint(inner_eid, "北宋大中祥符元年以前")
    if inner_start is None:
        inner_start = tp(
            w, inner_eid, "北宋（衣库改名后）", "由衣库改名",
            i, main, "宫廷衣物库", "建立内衣物库由衣库改名节点。",
            chain="none",
        )
    inner_merge = w.find_timepoint(inner_eid, "北宋大中祥符元年")
    inner_end = ft(w, inner_eid, "北宋熙宁四年六月二十五日")
    chain_all(
        w, inner_eid,
        [inner_start] + ([inner_merge] if inner_merge else []) + [inner_end],
        "连接内衣物库改名、接收匹缎库与并入尚衣库节点。",
    )
    rel(w, end, inner_start, "前后演变", i, main,
        "衣库后改为内衣物库。")
    w.commit()


def entry1615():
    i = 1615
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("受纳匹缎库", "机构", "本条直接定义受纳匹缎库。",
                   quotation=main)
    start = tp(
        w, eid, "北宋太平兴国二年",
        "始置，收受绫锦院及西川输送的锦鹿胎、绫、罗、绢等匹缎",
        i, main, "宫廷衣物库", "建立受纳匹缎库始置节点。",
        chain="none",
    )
    end = tp(
        w, eid, "北宋大中祥符元年", "并入内衣物库",
        i, main, "宫廷衣物库", "建立受纳匹缎库并入节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end],
              "连接受纳匹缎库始置与并入节点。")

    inner_eid = fe(w, "内衣物库", "机构")
    inner_start = (
        w.find_timepoint(inner_eid, "北宋大中祥符元年以前")
        or ft(w, inner_eid, "北宋（衣库改名后）")
    )
    inner_merge = tp(
        w, inner_eid, "北宋大中祥符元年", "受纳匹缎库并入",
        i, main, "宫廷衣物库", "建立内衣物库接收匹缎库节点。",
        chain="none",
    )
    inner_end = ft(w, inner_eid, "北宋熙宁四年六月二十五日")
    chain_all(
        w, inner_eid, [inner_start, inner_merge, inner_end],
        "连接内衣物库改名、接收匹缎库与并入尚衣库节点。",
    )
    rel(w, end, inner_merge, "前后演变", i, main,
        "大中祥符元年受纳匹缎库并入内衣物库。")
    w.commit()


def entry1616():
    i = 1616
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职能"), field(i, "编制"),
    )
    w = W(i)
    eid = fe(w, "内衣物库", "机构")
    start = refine(
        w, (
            w.find_timepoint(eid, "北宋大中祥符元年以前")
            or ft(w, eid, "北宋（衣库改名后）")
        ), i, history,
        "专条补证内衣物库由衣库改名及最迟见名时间。",
        "职源与沿革",
        time="北宋大中祥符元年以前",
        event="由衣库改名，至迟大中祥符元年已称内衣物库",
        category="宫廷衣物库",
    )
    merge = ft(w, eid, "北宋大中祥符元年")
    cite(w, "Timepoints", merge, i, history,
         "补证受纳匹缎库并入时已称内衣物库。", "职源与沿革")
    end = refine(
        w, ft(w, eid, "北宋熙宁四年六月二十五日"), i, history,
        "专条补证内衣物库熙宁四年六月并入尚衣库。",
        "职源与沿革",
        event="并入尚衣库",
        category="宫廷衣物库",
    )
    cite(w, "Timepoints", merge, i, duty,
         "补证内衣物库收储、发放时服职能。", "职能")
    cite(w, "Timepoints", merge, i, staff,
         "补证内衣物库官吏编制。", "编制")
    chain_all(w, eid, [start, merge, end],
              "连接内衣物库改名、接收匹缎库与并入尚衣库节点。")
    w.commit()


def entry1617():
    simple_supervisor(
        1617, "监内衣物库", "内衣物库",
        "北宋大中祥符元年以前", "北宋大中祥符元年以后",
        "由京朝官与内侍充，掌受纳衣料，预造并发放春冬时服及各类赐物",
        "京朝官或内侍差遣",
    )


def entry1616_supervisor_quota():
    i = 1616
    staff = field(i, "编制")
    w = W(i)
    rid = base.relation_id(
        w, "内衣物库", "监内衣物库", "编制隶属",
        "北宋大中祥符元年以前", "北宋大中祥符元年以后",
    )
    assert rid
    base.set_rel_attrs(w, rid, 2, None, "内衣物库条明确监官二人。")
    cite(w, "Relationships", rid, i, staff,
         "补证监内衣物库编制二人。", "编制")
    w.commit()


def entry1618():
    i = 1618
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("受纳衣服库", "机构", "本条直接定义受纳衣服库。",
                   quotation=main)
    tid = tp(
        w, eid, "北宋咸平四年",
        "收储诸司丁匠及诸军服，后并入新衣库",
        i, main, "宫廷衣物库", "建立受纳衣服库并入节点。",
    )
    base.mark_citation_conflict(
        w, "Timepoints", tid, i, main,
        "与“新衣库”条所记咸平元年十月并入相冲突；保留原书两说。",
        "标记原书内部关于并入年份的冲突。",
    )
    w.commit()


def entry1619():
    i = 1619
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职能"), field(i, "编制"),
    )
    w = W(i)
    eid = w.entity("新衣库", "机构", "本条直接定义新衣库。",
                   quotation=main)
    start = tp(
        w, eid, "宋初", "已置于京师太平坊",
        i, history, "宫廷衣物库", "建立新衣库宋初节点。",
        "职源与沿革", chain="none",
    )
    merge = tp(
        w, eid, "北宋咸平元年十月", "受纳衣服库并入",
        i, history, "宫廷衣物库", "建立新衣库接收衣服库节点。",
        "职源与沿革", chain="none",
    )
    end = tp(
        w, eid, "北宋熙宁四年五月",
        "废罢，官物并入仪鸾司等处",
        i, history, "宫廷衣物库", "建立新衣库废罢节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", merge, i, duty,
         "补证新衣库收储衣物职能。", "职能")
    cite(w, "Timepoints", merge, i, staff,
         "补证新衣库官吏、监门与下设二库编制。", "编制")
    chain_all(w, eid, [start, merge, end],
              "连接新衣库宋初、接收衣服库与熙宁废罢节点。")
    old_end = ft(w, fe(w, "受纳衣服库", "机构"), "北宋咸平四年")
    rel(w, old_end, merge, "前后演变", i, history,
        "原书两条对并入年份记载不一；保留受纳衣服库并入新衣库关系。",
        "职源与沿革")
    w.commit()


def entry1620():
    i = 1620
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity("监新衣库", "官职", "本条直接定义监新衣库差遣。",
                   quotation=main)
    tid = tp(
        w, eid, "北宋咸平元年三月",
        "由诸司使、副使或三班使臣与内侍充，掌受纳衣物以备给赐百官、军兵及邦国仪注",
        i, main, "新衣库监官", "建立监新衣库节点。",
        attr_officer_type="诸司使副、三班使臣或内侍差遣",
    )
    cite(w, "Timepoints", tid, i, alias,
         "监新衣库简称监库，仅作名称与在职证据。",
         "简称", note="纯简称")
    rel(w, ft(w, fe(w, "新衣库", "机构"), "宋初"),
        tid, "编制隶属", i, main, "监新衣库监领新衣库。",
        staff_type="诸司使副、三班使臣或内侍差遣")
    w.commit()


def entry1619_supervisor_quota():
    i = 1619
    staff = field(i, "编制")
    w = W(i)
    rid = base.relation_id(
        w, "新衣库", "监新衣库", "编制隶属",
        "宋初", "北宋咸平元年三月",
    )
    assert rid
    base.set_rel_attrs(w, rid, 2, None, "新衣库条明确监官二人。")
    cite(w, "Relationships", rid, i, staff,
         "补证监新衣库编制二人。", "编制")
    w.commit()


def entry1621():
    i = 1621
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("裁造院", "机构", "本条直接定义裁造院。",
                   quotation=main)
    tp(
        w, eid, "宋代", "制作供丁匠、军兵的时服，送新衣库或受纳衣服库收储",
        i, main, "衣服制造机构", "建立裁造院宋代节点。",
    )
    w.commit()


def entry1622():
    i = 1622
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职能"), field(i, "编制"),
    )
    w = W(i)
    eid = w.entity("朝服、法物库", "机构",
                   "本条直接定义朝服、法物库。", quotation=main)
    start = tp(
        w, eid, "北宋太平兴国二年", "始置，分设三库",
        i, history, "礼服法物库", "建立朝服法物库始置节点。",
        "职源与沿革", chain="none",
    )
    merge = tp(
        w, eid, "北宋崇宁二年二月", "并入殿中省",
        i, history, "殿中省所属库", "建立朝服法物库并入节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", merge, i, duty,
         "补证朝服法物库职能。", "职能")
    cite(w, "Timepoints", merge, i, staff,
         "补证朝服法物库官吏编制。", "编制")
    chain_all(w, eid, [start, merge],
              "连接朝服法物库始置与并入殿中省节点。")
    rel(w, ft(w, fe(w, "殿中省", "机构"),
              "北宋崇宁二年二月十二日"),
        merge, "上下级机构", i, history,
        "崇宁二年朝服、法物库并入殿中省。", "职源与沿革")
    w.commit()


def entry1623():
    simple_supervisor(
        1623, "监朝服、法物库", "朝服、法物库",
        "北宋太平兴国二年", "北宋太平兴国二年以后",
        "由诸司使副、三班使臣或内侍官充，预备支借朝服礼衣仪仗并限期收还",
        "诸司使副、三班使臣或内侍差遣", quota=3,
    )


def entry1624():
    i = 1624
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "专知官", "官职")
    generic = tp(
        w, eid, "宋代诸库务", "掌所在库出纳、记帐、结帐及管钱粮财物",
        i, main, "库务公吏", "建立专知官诸库务节点。",
        attr_officer_type="公吏", chain="none",
    )
    chain_all(
        w, eid,
        [
            ft(w, eid, "宋代"),
            generic,
            ft(w, eid, "南宋"),
            ft(w, eid, "南宋（秘书省）"),
        ],
        "连接专知官皮剥所、诸库务与南宋秘书省节点。",
    )
    w.commit()


def entry1625():
    i = 1625
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("副知", "官职", "本条直接定义副知公吏。",
                   quotation=main)
    tp(
        w, eid, "宋代诸库务", "即副知官，职与专知同，位次于专知",
        i, main, "库务公吏", "建立副知诸库务节点。",
        attr_officer_type="公吏",
    )
    w.commit()


def entry1626():
    i = 1626
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("专副", "官职", "本条定义专知官与副知连称。",
                   quotation=main)
    total = tp(
        w, eid, "宋代诸库务", "专知官与副知连称",
        i, main, "库务公吏连称", "建立专副连称节点。",
        attr_officer_type="公吏连称",
    )
    for title in ("专知官", "副知"):
        rel(w, total, ft(w, fe(w, title, "官职"), "宋代诸库务"),
            "统称与实例", i, main, f"{title}是专副连称实例。")
    w.commit()


def entry1627():
    i = 1627
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "库子", "官职")
    generic = tp(
        w, eid, "宋代在京诸库务",
        "由刺字武卒补填，州郡库子须有产业及保人，掌本库钱货出纳",
        i, main, "库务公吏", "建立库子诸库务节点。",
        attr_officer_type="公吏", chain="none",
    )
    chain_all(
        w, eid,
        [
            ft(w, eid, "宋代"),
            generic,
            ft(w, eid, "南宋（秘书省）"),
            ft(w, eid, "宋代诸书局时期"),
        ],
        "连接库子皮剥所、在京库务、秘书省与修书局节点。",
    )
    targets = [
        ("手分", ft(w, fe(w, "手分", "官职"), "宋代")),
        ("副知", ft(w, fe(w, "副知", "官职"), "宋代诸库务")),
        ("专知官", ft(w, fe(w, "专知官", "官职"), "宋代诸库务")),
    ]
    promotion_eid = w.entity(
        "进义副尉", "官职", "库子条明确记载出职补进义副尉。",
        quotation=main,
    )
    promotion = tp(
        w, promotion_eid, "宋代库务吏出职",
        "库子出职可补进义副尉",
        i, main, "武阶", "建立进义副尉库子出职节点。",
        attr_officer_type="武阶",
    )
    targets.append(("进义副尉", promotion))
    for title, target in targets:
        rel(w, generic, target, "前后演变", i, main,
            f"库子可升迁或出职为{title}。")
    w.commit()


def grouped_six_role(i, title, quotas, *, child_quote=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条定义六尚局{title}通称。",
                   quotation=main)
    total = tp(
        w, eid, "北宋崇宁二年二月", f"殿中省六尚各局所置{title}通称",
        i, main, "六尚局库务公吏统称", f"建立{title}统称节点。",
        attr_officer_type="公吏统称",
    )
    if "别名" in F[i]["fields"]:
        cite(w, "Timepoints", total, i, field(i, "别名"),
             f"{title}别名仅作名称证据。", "别名", note="纯别名")
    for parent, quota in quotas.items():
        child_title = f"{parent}{title}"
        quote = child_quote(parent) if child_quote else main
        child_eid = w.entity(
            child_title, "官职", f"{title}条明确其分隶{parent}。",
            quotation=quote,
        )
        child = tp(
            w, child_eid, "北宋崇宁二年二月",
            f"{parent}所属{title}，掌本局各库出纳钱粮衣物",
            i, main, f"{parent}库务公吏", f"建立{child_title}节点。",
            attr_officer_type="公吏",
        )
        rel(w, total, child, "统称与实例", i, main,
            f"{child_title}是{title}实例。")
        rel(w, bureau(w, parent), child, "编制隶属", i, main,
            f"{child_title}隶{parent}。",
            staff_quota=quota, staff_type="公吏")
    w.commit()


def entry1629():
    main = Q(1629, F[1629]["text"])
    food_staff = field(1568, "编制")
    grouped_six_role(
        1629, "库典",
        {
            "尚食局": None,
            "尚药局": 7,
            "尚酝局": 5,
            "尚衣局": 10,
            "尚舍局": 6,
            "尚辇局": 10,
        },
        child_quote=lambda parent: food_staff if parent == "尚食局" else main,
    )


def entry1568_food_store_quota():
    i = 1568
    staff = field(i, "编制")
    w = W(i)
    rid = base.relation_id(
        w, "尚食局", "尚食局库典", "编制隶属",
        "北宋崇宁二年二月", "北宋崇宁二年二月",
    )
    assert rid
    base.set_rel_attrs(
        w, rid, 12, None,
        "尚食局专条明确库典十二人；库典条原书编制列表首项误重“尚衣局”。",
    )
    cite(w, "Relationships", rid, i, staff,
         "补证尚食局库典十二人。", "编制",
         note="库典条原书列表首项重出尚衣局，尚食局数额据本条")
    w.commit()


def entry1630():
    i = 1630
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("下都", "官职", "本条直接定义尚辇局下都。",
                   quotation=main)
    tid = tp(
        w, eid, "北宋崇宁二年二月十二日",
        "原为御辇院下等车匠，厘入殿中省尚辇局，仍在殿阁祗应车驾",
        i, main, "尚辇局公吏", "建立下都崇宁节点。",
        attr_officer_type="公吏",
    )
    rel(w, bureau(w, "尚辇局"), tid, "编制隶属", i, main,
        "下都隶尚辇局。", staff_quota=1000, staff_type="公吏")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1611, 1631)] == [
        "内衣库", "监内衣库", "衣库", "监衣库", "受纳匹缎库",
        "内衣物库", "监内衣物库", "受纳衣服库", "新衣库", "监新衣库",
        "裁造院", "朝服、法物库", "监朝服、法物库", "专知官", "副知",
        "专副", "库子", "掌库", "库典", "下都",
    ]
    entry1611()
    simple_supervisor(
        1612, "监内衣库", "内衣库",
        "北宋大中祥符二年七月二十五日",
        "北宋大中祥符二年七月二十五日以前",
        "监领内衣库受纳事务", "差遣",
    )
    entry1613()
    simple_supervisor(
        1614, "监衣库", "衣库",
        "北宋开宝三年四月二十九日", "北宋开宝三年四月",
        "始置，有官印，监衣库受纳事务", "差遣",
    )
    entry1615()
    entry1616()
    entry1617()
    entry1616_supervisor_quota()
    entry1618()
    entry1619()
    entry1620()
    entry1619_supervisor_quota()
    entry1621()
    entry1622()
    entry1623()
    entry1624()
    entry1625()
    entry1626()
    entry1627()
    grouped_six_role(
        1628, "掌库",
        {
            "尚食局": 2,
            "尚药局": 2,
            "尚酝局": 2,
            "尚衣局": 2,
            "尚舍局": 10,
            "尚辇局": 2,
        },
    )
    entry1629()
    entry1568_food_store_quota()
    entry1630()


if __name__ == "__main__":
    main()
