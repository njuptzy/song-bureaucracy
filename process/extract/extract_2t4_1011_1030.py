#!/usr/bin/env python3
"""提取 chapter2t4 第1011–1030条：侍郎左选诸案、侍郎右选及诸案。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(1011, 1031)}
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


def office(i, parent_title, title, event, definition_prefix):
    main = Q(i, x.b.F[i]["text"])
    definition = Q(i, definition_prefix)
    w = W(i)
    eid = w.entity(
        title,
        "机构",
        f"第{i}条直接定义{title}为{parent_title}常设办事部门。",
        quotation=definition,
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
        definition,
        f"原文明确{title}为{parent_title}常设办事部门之一。",
    )
    w.commit()


def entry1011_1016():
    specs = (
        (1011, "吏部侍郎左选名籍案", "掌文臣选人名册及籍贯、家世、履历、功过等信息"),
        (1012, "吏部侍郎左选甲库案", "掌选人符牒、黄甲、履历相貌验证及制作告身签符"),
        (1013, "吏部侍郎左选知阙案", "掌内外官阙信息，供拟注应格人参考"),
        (1014, "吏部侍郎左选注拟案", "掌拟注选人内外职任手续"),
        (1015, "吏部侍郎左选知杂案", "掌本选杂务"),
        (1016, "吏部侍郎左选法司案", "掌本选法令条例检阅"),
    )
    for i, title, event in specs:
        office(
            i,
            "吏部侍郎左选",
            title,
            event,
            "吏部侍郎左选常设办事部门之一。",
        )


def entry1017():
    i = 1017
    main = Q(i, x.b.F[i]["text"])
    origin = Q(
        i,
        "北宋元丰五年五月，改三班院为吏部侍郎右选",
        "职源",
    )
    duty = Q(
        i,
        "掌武臣东、西头供奉官以下（政和二年后为从义郎以下至副尉）"
        "考校、拟官、换官等",
        "职掌",
    )
    staff = Q(
        i,
        "侍郎、郎中各一人，分案十五，吏额八十三人",
        "编制",
    )
    w = W(i)
    eid = fe(w, "吏部侍郎右选", "机构")
    tid = refine(
        w,
        ft(w, eid, "北宋元丰五年五月"),
        i,
        duty,
        "专条细化吏部侍郎右选武臣考校、拟官与换官职掌。",
        "职掌",
        event="由三班院改置，掌低阶武臣考校、拟官、换官等事务",
        category="武臣铨选机构",
    )
    cite(w, "Timepoints", tid, i, origin, "专条补证由三班院改置。", "职源")
    cite(w, "Timepoints", tid, i, staff, "专条补证官额、十五案与吏额。", "编制")
    cite(w, "Timepoints", tid, i, main, "正文补证为官署。")
    rid = relation_id(
        w,
        "三班院",
        "吏部侍郎右选",
        "前后演变",
        "北宋元丰五年五月",
        "北宋元丰五年五月",
    )
    assert rid
    cite(w, "Relationships", rid, i, origin, "专条补证三班院改为吏部侍郎右选。", "职源")
    w.commit()


def entry1018():
    i = 1018
    main = Q(i, x.b.F[i]["text"])
    origin = Q(
        i,
        "北宋神宗元丰五年四月，始除吏部侍郎二员，分工主管侍郎左、右选",
        "职源",
    )
    duty = Q(
        i,
        "与尚书、左选侍郎通治吏部事，右选侍郎分管吏部右选事，"
        "即掌武臣未升朝官",
        "职掌",
    )
    w = W(i)
    eid = w.entity(
        "吏部右选侍郎",
        "官职",
        "据专条建立分管吏部侍郎右选的职事官。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "北宋元丰五年四月",
        "始置，分管吏部侍郎右选低阶武臣磨勘、拟注等事",
        i,
        origin,
        "吏部副长官",
        "建吏部右选侍郎始置节点。",
    )
    cite(w, "Timepoints", tid, i, duty, "专条补证右选侍郎职掌。", "职掌")
    rel(
        w,
        ft(w, fe(w, "吏部侍郎右选", "机构"), "北宋元丰五年五月"),
        tid,
        "编制隶属",
        i,
        duty,
        "右选侍郎分管吏部侍郎右选事务。",
        "职掌",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def entry1019_1030():
    specs = (
        (1019, ("吏部侍郎右选从义案",), "掌从义郎、秉义郎考校、拟官、换官、行赏等事"),
        (1020, ("吏部侍郎右选忠训案",), "掌忠训郎、忠翊郎考校、拟官、换官、行赏等事"),
        (1021, ("吏部侍郎右选成忠案",), "掌成忠郎、保义郎考校、拟官、换官、行赏等事"),
        (1022, ("吏部侍郎右选承节案",), "掌承节郎考校、拟官、换官、功过等事"),
        (1023, ("吏部侍郎右选承信案",), "掌承信郎考校、拟官、换官、行赏等事"),
        (1024, ("吏部侍郎右选进武案",), "掌校尉、副尉考校、拟官、行赏、换官等事"),
        (1025, ("吏部侍郎右选差注案",), "掌校尉、副尉至从义郎注授差遣手续"),
        (
            1026,
            ("吏部侍郎右选生事上案", "吏部侍郎右选生事下案"),
            "掌本选武臣犯纪违法的狱讼刑罚事务",
        ),
        (1027, ("吏部侍郎右选掌阙案",), "掌差注窠阙，供拟官奏差"),
        (1028, ("吏部侍郎右选资次案",), "掌武臣资序、恩例、名次，供差注拟官"),
        (1029, ("吏部侍郎右选知杂案",), "掌本选杂务"),
        (1030, ("吏部侍郎右选催驱案",), "掌催督本选稽滞文书"),
    )
    for i, titles, event in specs:
        for title in titles:
            office(
                i,
                "吏部侍郎右选",
                title,
                event,
                "吏部侍郎右选常设办事部门之一。",
            )


def main():
    assert [x.b.F[i]["title"] for i in range(1011, 1031)] == [
        "吏部侍郎左选名籍案",
        "吏部侍郎左选甲库案",
        "吏部侍郎左选知阙案",
        "吏部侍郎左选注拟案",
        "吏部侍郎左选知杂案",
        "吏部侍郎左选法司案",
        "吏部侍郎右选",
        "吏部右选侍郎",
        "吏部侍郎右选从义案",
        "吏部侍郎右选忠训案",
        "吏部侍郎右选成忠案",
        "吏部侍郎右选承节案",
        "吏部侍郎右选承信案",
        "吏部侍郎右选进武案",
        "吏部侍郎右选差注案",
        "吏部侍郎右选生事上案、下案",
        "吏部侍郎右选掌阙案",
        "吏部侍郎右选资次案",
        "吏部侍郎右选知杂案",
        "吏部侍郎右选催驱案",
    ]
    entry1011_1016()
    entry1017()
    entry1018()
    entry1019_1030()


if __name__ == "__main__":
    main()
