#!/usr/bin/env python3
"""提取 chapter2t4 第811–830条：中书省吏人与尚书省总制、诸房。"""
import extract_2t4_771_790 as b


b.F = {i: b.load(i) for i in range(811, 831)}
W = b.W
Q = b.Q
fe = b.fe
ft = b.ft
cite = b.cite
tp = b.tp
rel = b.rel
chain_all = b.chain_all
refine = b.refine
relation_id = b.relation_id
set_rel_attrs = b.set_rel_attrs


def current_chain(w, entity_id):
    rows = {
        row[0]: (row[1], row[2])
        for row in w.conn.execute(
            "select id,prev_id,succ_id from Timepoints where entity_id=?",
            (entity_id,),
        )
    }
    heads = [tid for tid, (prev_id, _) in rows.items() if prev_id is None]
    assert len(heads) == 1, (entity_id, heads)
    ordered = []
    tid = heads[0]
    while tid is not None:
        assert tid not in ordered, (entity_id, tid)
        ordered.append(tid)
        tid = rows[tid][1]
    assert len(ordered) == len(rows), (entity_id, ordered, rows)
    return ordered


def move_after(w, entity_id, moved_id, after_id, decision):
    ordered = current_chain(w, entity_id)
    ordered.remove(moved_id)
    if after_id is None:
        ordered.insert(0, moved_id)
    else:
        ordered.insert(ordered.index(after_id) + 1, moved_id)
    chain_all(w, entity_id, ordered, decision)


def entry811():
    i = 811
    main = Q(i, b.F[i]["text"])
    origin = Q(
        i,
        "录事之名，始见于西晋，骠骑大将军下属员有录事（《晋书·职官志》）。"
        "隋朝内书省（即唐宋之中书省）始置录事",
        "职源",
    )
    duty = Q(i, "点检诸房发放文字，点检文字及掌诸房事。", "职掌")
    grade = Q(
        i,
        "正八品。《宋会要·职官》3之39：“准《绍兴令》；"
        "中书、门下省录事，尚书省都事为正八品。”",
        "品位",
    )
    quota = Q(i, "元丰新制3人", "编制")
    w = W(i)
    eid = fe(w, "中书省录事", "官职")
    jin = tp(
        w, eid, "西晋", "骠骑大将军属员已有录事", i, origin,
        "堂吏", "建录事西晋源流节点。", "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "内书省始置录事", i, origin,
        "堂吏", "建中书省录事隋代源流节点。", "职源", chain="none",
    )
    yuanfeng = tp(
        w, eid, "北宋元丰新制", "中书省录事三人，点检诸房文字并掌诸房事",
        i, duty, "堂吏", "建元丰中书省录事职掌节点。", "职掌",
        chain="none", attr_grade="正八品",
    )
    cite(w, "Timepoints", yuanfeng, i, quota, "专条补证元丰编制三人。", "编制")
    cite(w, "Timepoints", yuanfeng, i, grade, "专条补证录事正八品。", "品位")
    south = refine(
        w, ft(w, eid, "南宋绍兴年间"), i, main,
        "专条补证南宋中书、门下合省后录事仍为堂吏。", None,
        event="中书、门下合省后为堂吏，点检诸房文字",
        category="堂吏", grade="正八品",
    )
    cite(w, "Timepoints", south, i, grade, "专条补证南宋录事品位。", "品位")
    chain_all(w, eid, [jin, sui, yuanfeng, south],
              "连接中书省录事西晋、隋、元丰及南宋节点。")
    rel(
        w, ft(w, fe(w, "中书省", "机构"), "北宋元丰新制"), yuanfeng,
        "编制隶属", i, quota, "元丰中书省置录事三人。", "编制",
        staff_quota=3, staff_type="吏",
    )
    rel(
        w, ft(w, fe(w, "中书门下省", "机构"), "南宋建炎三年四月二十九日"),
        south, "编制隶属", i, main,
        "南宋中书、门下合省后录事隶合省机构。", None, staff_type="吏",
    )
    w.commit()


def entry812_816():
    specs = (
        (812, "主事", "北宋元丰新制（中书省）"),
        (813, "令史", "北宋元丰新制（中书省）"),
        (814, "书令史", "北宋元丰新制（中书省）"),
        (815, "守当官", "北宋元丰新制（中书省）"),
        (816, "守阙守当官", "北宋哲宗朝（中书省）"),
    )
    for i, title, time in specs:
        main = Q(i, b.F[i]["text"])
        w = W(i)
        eid = fe(w, title, "官职")
        tid = ft(w, eid, time)
        cite(w, "Timepoints", tid, i, main,
             f"专条补证{title}为中书省吏职，南宋随两省合并。")
        subject_time = (
            "北宋哲宗朝（中书省分房变化）"
            if title == "守阙守当官" else "北宋元丰新制"
        )
        rid = relation_id(
            w, "中书省", title, "编制隶属", subject_time, time
        )
        assert rid, (i, title)
        cite(w, "Relationships", rid, i, main,
             f"专条补证{title}隶中书省。")
        w.commit()


def entry817_core():
    i = 817
    main = Q(i, b.F[i]["text"])
    origin = Q(
        i,
        "东汉至魏晋均称尚书台，尚书省之名始自南朝梁",
        "职源",
    )
    early = Q(
        i,
        "① 宋前期名存实亡，所领事务甚微",
        "职掌",
    )
    reform = Q(
        i,
        "②元丰改制，尚书省依《唐六典》振举其职，掌执行经由门下省所付"
        "制、诏、敕、令，统管吏部、户部、礼部、兵部、刑部、工部六部"
        "及其所属二十八司",
        "职掌",
    )
    w = W(i)
    platform_e = w.entity(
        "尚书台", "机构", "据尚书省专条建立东汉至魏晋前身机构。",
        quotation=origin,
    )
    platform = tp(
        w, platform_e, "东汉至魏晋", "称尚书台", i, origin,
        "中央政务机构", "建尚书台前身节点。", "职源", chain="none",
    )
    platform_end = tp(
        w, platform_e, "南朝梁", "改称尚书省", i, origin,
        "中央政务机构", "建尚书台改称节点。", "职源", chain="none",
    )
    chain_all(w, platform_e, [platform, platform_end], "连接尚书台沿置与改称节点。")

    eid = fe(w, "尚书省", "机构")
    liang = tp(
        w, eid, "南朝梁", "始有尚书省之名", i, origin,
        "中央政务机构", "建尚书省始称节点。", "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "名存实亡，仅领集议谥号、誓戒、封赠等少量事务",
        i, early, "中央政务机构", "建宋前期尚书省名存实亡节点。", "职掌",
        chain="none",
    )
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制"), i, reform,
        "专条细化元丰尚书省执行政令并统辖六部的职掌。", "职掌",
        event="振举职权，执行门下省所付政令并统辖六部二十八司",
        category="中央政务机构",
    )
    cite(w, "Timepoints", yuanfeng, i, main, "专条补证尚书省为三省之一。")
    chain_all(w, eid, [liang, song, yuanfeng],
              "连接尚书省南朝梁始称、宋前期虚置与元丰振职节点。")
    rel(w, platform_end, liang, "前后演变", i, origin,
        "南朝梁尚书台改称尚书省。", "职源")
    w.commit()


def entry817_staff():
    i = 817
    quota = Q(
        i,
        "② 元丰新制，官额九：尚书令，尚书省左仆射，尚书省右仆射，"
        "尚书省左丞，尚书省右丞，尚书省左司郎中，尚书省右司郎中，"
        "尚书省左司员外郎，尚书省右司员外郎各一人。",
        "编制",
    )
    clerk = Q(
        i,
        "吏额六十四：都事三人，主事六人，令史十四人，书令史三十五人，"
        "守当官六人。绍圣三年，置守阙守当官一百五十人。",
        "编制",
    )
    w = W(i)
    institute = ft(w, fe(w, "尚书省", "机构"), "北宋元丰新制")
    office_specs = (
        ("尚书令", "宋代（未载具体年月）"),
        ("尚书左仆射", "北宋元丰新制"),
        ("尚书右仆射", "北宋元丰新制"),
        ("尚书省左丞", "北宋元丰新制"),
        ("尚书省右丞", "北宋元丰新制"),
    )
    for title, time in office_specs:
        eid = fe(w, title, "官职")
        tid = w.find_timepoint(eid, time)
        if tid is None:
            tid = tp(
                w, eid, time, "列尚书省官额一人", i, quota,
                "职事官", f"据尚书省总条补建{title}元丰官额节点。",
                "编制", chain="none",
            )
            existing = [
                row[0]
                for row in w.conn.execute(
                    "select id from Timepoints where entity_id=? and id<>? order by id",
                    (eid, tid),
                )
            ]
            chain_all(
                w, eid, [tid, *existing],
                f"将{title}元丰官额节点接入既有时间链。",
            )
        rel(w, institute, tid, "编制隶属", i, quota,
            f"元丰尚书省官额列{title}一人。", "编制",
            staff_quota=1, staff_type="官")
    for title in (
        "尚书省左司郎中", "尚书省右司郎中",
        "尚书省左司员外郎", "尚书省右司员外郎",
    ):
        eid = w.entity(title, "官职", f"据尚书省元丰官额建立{title}。",
                       quotation=quota)
        tid = tp(
            w, eid, "北宋元丰新制", "列尚书省官额一人", i, quota,
            "职事官", f"建{title}元丰官额节点。", "编制",
        )
        rel(w, institute, tid, "编制隶属", i, quota,
            f"元丰尚书省置{title}一人。", "编制",
            staff_quota=1, staff_type="官")
    clerk_specs = (
        ("尚书省都事", 3, "南宋绍兴年间", None),
        ("主事", 6, "北宋元丰新制（门下省）", "北宋元丰新制（门下省）"),
        ("令史", 14, "北宋元丰新制（门下省）", "北宋元丰新制（中书省）"),
        ("书令史", 35, "北宋元丰新制（门下省）", "北宋元丰新制（中书省）"),
        ("守当官", 6, "北宋元丰新制（门下省）", "北宋元丰新制（中书省）"),
    )
    for title, count, fallback_time, insert_after_time in clerk_specs:
        eid = fe(w, title, "官职")
        time = "北宋元丰新制（尚书省）"
        tid = tp(
            w, eid, time, f"尚书省吏额{count}人", i, clerk,
            "吏职", f"建{title}在尚书省的元丰编制节点。", "编制",
        )
        move_after(
            w,
            eid,
            tid,
            ft(w, eid, insert_after_time) if insert_after_time else None,
            f"将{title}的尚书省元丰节点移到南宋节点之前。",
        )
        rel(w, institute, tid, "编制隶属", i, clerk,
            f"元丰尚书省置{title}{count}人。", "编制",
            staff_quota=count, staff_type="吏")
        # fallback_time 仅用于显式确认复用了既有实体，而非另造同名实体。
        assert ft(w, eid, fallback_time)
    candidate_e = fe(w, "守阙守当官", "官职")
    candidate = tp(
        w, candidate_e, "北宋绍圣三年（尚书省）",
        "尚书省增置守阙守当官一百五十人", i, clerk,
        "候补吏", "建尚书省守阙守当官增置节点。", "编制",
    )
    move_after(
        w,
        candidate_e,
        candidate,
        ft(w, candidate_e, "北宋绍圣三年"),
        "将尚书省绍圣三年守阙守当官节点置于南宋合省节点之前。",
    )
    rel(
        w, institute, candidate, "编制隶属", i, clerk,
        "绍圣三年尚书省增置守阙守当官一百五十人。", "编制",
        staff_quota=150, staff_type="候补吏",
    )
    w.commit()


def entry820():
    i = 820
    main = Q(i, b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "尚书都省", "机构",
        "据专条建立尚书省总部机构；严格范围不含六部。",
        quotation=main,
    )
    north_qi = tp(
        w, eid, "北齐", "始有尚书都省之制", i, main,
        "中央政务机构", "建尚书都省北齐源流节点。", None, chain="none",
    )
    yuanfeng = tp(
        w, eid, "北宋元丰五年十月十七日",
        "总辖六曹，办理奏授须具尚书都省官",
        i, main, "尚书省总部机构", "建元丰尚书都省总辖六曹节点。", None,
        chain="none",
    )
    chain_all(w, eid, [north_qi, yuanfeng], "连接尚书都省北齐源流与元丰节点。")
    rel(
        w, ft(w, fe(w, "尚书省", "机构"), "北宋元丰新制"), yuanfeng,
        "上下级机构", i, main,
        "尚书都省为尚书省总部机构，严格范围不包括六部。",
    )
    w.commit()


def entry821_830():
    for i in range(821, 831):
        main = Q(i, b.F[i]["text"])
        title = b.F[i]["title"]
        event = main.split("。", 2)[1] if "。掌" in main else main
        w = W(i)
        eid = w.entity(title, "机构", f"据专条建立{title}办事机构。", quotation=main)
        tid = tp(
            w, eid, "北宋元丰新制", event, i, main,
            "尚书省办事部门", f"建{title}元丰职掌节点。",
        )
        rel(
            w, ft(w, fe(w, "尚书省", "机构"), "北宋元丰新制"), tid,
            "上下级机构", i, main, f"{title}为尚书省办事部门。",
        )
        w.commit()


def main():
    entry811()
    entry812_816()
    entry817_core()
    entry817_staff()
    # 第818、819条为“粉省”“粉署”空占位，不凭别称标题造实体。
    entry820()
    entry821_830()


if __name__ == "__main__":
    main()
