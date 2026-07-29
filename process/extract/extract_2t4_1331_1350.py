#!/usr/bin/env python3
"""提取 chapter2t4 第1331–1350条：秘书省八品吏、楷书递迁与省舍杂役。"""
import extract_2t4_1311_1330 as x


base = x.base
base.F = {i: base.load(i) for i in range(1331, 1351)}
F = base.F
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all


def secretary_parent(w):
    return ft(
        w, fe(w, "秘书省", "机构"), "南宋绍兴元年二月十九日"
    )


def existing_chain(w, entity_id, omit=None):
    rows = {
        row[0]: row
        for row in w.conn.execute(
            "select id,prev_id,succ_id from Timepoints where entity_id=?",
            (entity_id,),
        )
    }
    if not rows:
        return []
    heads = [
        row[0] for row in rows.values()
        if row[1] is None and row[0] != omit
    ]
    if not heads and omit in rows:
        heads = [omit]
    assert len(heads) == 1, (entity_id, heads)
    ordered = []
    current = heads[0]
    while current is not None:
        if current != omit:
            assert current not in ordered, (entity_id, current)
            ordered.append(current)
        successor = rows[current][2]
        current = successor if successor in rows else None
    assert len(ordered) == len(rows) - (1 if omit in rows else 0), (
        entity_id, ordered, rows
    )
    return ordered


def clerk(i, title, event, *, grade=None, parent=True, before_time=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义秘书省吏职{title}。",
                   quotation=main)
    time = "南宋（秘书省）"
    tid = tp(
        w, eid, time, event,
        i, main, "秘书省吏职", f"建立{title}南宋秘书省节点。",
        attr_officer_type="吏", attr_grade=grade, chain="none",
    )
    ordered = existing_chain(w, eid, omit=tid)
    if before_time:
        before_id = ft(w, eid, before_time)
        index = ordered.index(before_id)
        ordered.insert(index, tid)
    else:
        ordered.append(tid)
    chain_all(w, eid, ordered, f"重建{title}既有节点与南宋秘书省节点完整时间链。")
    if parent:
        rel(
            w, secretary_parent(w), tid, "编制隶属",
            i, main, f"{title}隶秘书省。",
            staff_type="吏",
        )
    w.commit()
    return eid, tid


def entry1331():
    i = 1331
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "秘书省八品吏", "官职",
        "本条直接定义秘书省六种有品告的八品吏统称。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋（具体年月未载）",
        "秘书省六种有品告八品吏的统称",
        i, main, "秘书省吏职统称", "建立秘书省八品吏南宋节点。",
        attr_officer_type="吏", attr_grade="八品",
    )
    rel(
        w, secretary_parent(w), tid, "编制隶属",
        i, main, "秘书省有品告八品吏六名。",
        staff_quota=6, staff_type="八品吏",
    )
    w.commit()


def collective_relations():
    i = 1331
    main = Q(i, F[i]["text"])
    w = W(i)
    collective_t = ft(
        w, fe(w, "秘书省八品吏", "官职"), "南宋（具体年月未载）"
    )
    for title in (
        "都孔目官", "孔目官", "四库书直官",
        "书直官", "表奏官", "书库官",
    ):
        rel(
            w, collective_t,
            ft(w, fe(w, title, "官职"), "南宋（秘书省）"),
            "统称与实例", i, main,
            f"{title}是秘书省六种有品告八品吏之一。",
        )
    w.commit()


def advancement(i, lower_title, higher_title):
    """按“由某吏递迁”建立吏职阶序，不把它误作机构上下级。"""
    main = Q(i, F[i]["text"])
    w = W(i)
    lower = ft(w, fe(w, lower_title, "官职"), "南宋（秘书省）")
    higher = ft(w, fe(w, higher_title, "官职"), "南宋（秘书省）")
    rel(
        w, lower, higher, "前后演变", i, main,
        f"本条明载由{lower_title}递迁为{higher_title}。",
    )
    w.commit()


def four_library_relation():
    i = 1334
    main = Q(i, F[i]["text"])
    w = W(i)
    group_t = ft(
        w, fe(w, "经、史、子、集四库", "机构"),
        "南宋（具体年月未载）",
    )
    post_t = ft(w, fe(w, "四库书直官", "官职"), "南宋（秘书省）")
    rel(
        w, group_t, post_t, "编制隶属", i, main,
        "四库书直官是经、史、子、集四书库吏人。",
        staff_type="八品吏",
    )
    w.commit()


def entry1347():
    i = 1347
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "秘书省仪鸾司", "机构",
        "本条明确它是秘书省贮存陈设物的省舍，虽非官司仍属空间机构。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋（具体年月未载）",
        "贮存皇帝临幸、曝书会或燕集时陈设的桌椅帐幕",
        i, main, "秘书省省舍", "建立秘书省仪鸾司南宋节点。",
    )
    rel(
        w, secretary_parent(w), tid, "上下级机构",
        i, main, "秘书省仪鸾司是秘书省内贮存陈设物的省舍。",
    )
    w.commit()


def entry1348():
    i = 1348
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "仪鸾司吏", "官职", "本条直接定义供秘书省陈设的仪鸾司吏。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋（秘书省）",
        "由仪鸾司、临安府差到，掌陈设帘幕、椅桌",
        i, main, "秘书省杂役", "建立仪鸾司吏南宋节点。",
        attr_officer_type="军吏",
    )
    unit_t = ft(
        w, fe(w, "秘书省仪鸾司", "机构"), "南宋（具体年月未载）"
    )
    rel(
        w, unit_t, tid, "编制隶属", i, main,
        "秘书省仪鸾司由仪鸾司吏三人掌陈设。",
        staff_quota=3, staff_type="军吏",
    )
    w.commit()


def entry1349():
    i = 1349
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "秘书省翰林司", "机构",
        "本条明确它是秘书省储藏宴会与临幸器具的省舍，非官司。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋（具体年月未载）",
        "储藏宴会或皇帝临幸时所用水壶、酒瓶、茶盏、托盘等器具",
        i, main, "秘书省省舍", "建立秘书省翰林司南宋节点。",
    )
    rel(
        w, secretary_parent(w), tid, "上下级机构",
        i, main, "秘书省翰林司是秘书省内储藏宴饮器具的省舍。",
    )
    w.commit()


def entry1350():
    i = 1350
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "翰林司吏", "官职", "本条直接定义供秘书省茶汤的翰林司吏。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋（秘书省）",
        "由翰林司差给秘书省，供应茶汤",
        i, main, "秘书省杂役", "建立翰林司吏南宋节点。",
        attr_officer_type="军吏",
    )
    unit_t = ft(
        w, fe(w, "秘书省翰林司", "机构"), "南宋（具体年月未载）"
    )
    rel(
        w, unit_t, tid, "编制隶属", i, main,
        "秘书省翰林司由翰林司所差吏人掌管。",
        staff_type="军吏",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1331, 1351)] == [
        "秘书省八品吏", "都孔目官", "孔目官", "四库书直官",
        "书直官", "表奏官", "书库官", "守当官", "正名楷书",
        "守阙楷书", "正系名楷书", "守阙系名楷书", "投名人",
        "专知官", "通引官", "库子", "秘书省仪鸾司", "仪鸾司吏",
        "秘书省翰林司", "翰林司吏",
    ]
    entry1331()
    clerk(1332, "都孔目官", "秘书省吏中序位最高，点检诸案行遣文字",
          grade="八品")
    clerk(1333, "孔目官", "都孔目官副手，位次都孔目官",
          grade="八品")
    clerk(1334, "四库书直官", "经、史、子、集四书库吏人",
          grade="八品")
    clerk(1335, "书直官", "位次四库书直官",
          grade="八品")
    clerk(1336, "表奏官", "书写笺奏文字，位次书直官",
          grade="八品")
    clerk(1337, "书库官", "位次表奏官",
          grade="八品")
    clerk(
        1338, "守当官", "秘书省文书吏，给绫纸，位次书库官",
        before_time="南宋建炎三年（中书后省）",
    )
    clerk(1339, "正名楷书", "书写吏，每日抄写二千字，冬季一千五百字",
          parent=False)
    clerk(1340, "守阙楷书",
          "书写吏，每日抄写二千字，冬季一千五百字，位次正名楷书",
          parent=False)
    clerk(1341, "正系名楷书",
          "书写吏，每日抄写二千字，冬季一千五百字，位次守阙楷书",
          parent=False)
    clerk(1342, "守阙系名楷书",
          "书写吏，每日抄写二千字，冬季一千五百字，位次正系名楷书",
          parent=False)
    clerk(1343, "投名人",
          "守阙系名楷书缺人时递补，差充诸殿阁位书写，为书写吏最末等",
          parent=False)
    clerk(1344, "专知官", "主管秘书省应副钱粮、官物",
          before_time=None)
    clerk(1345, "通引官", "掌秘书省取索及投下文书")
    clerk(1346, "库子",
          "看管诸书库、出借书籍及应奉御前与朝廷取书画古器瑞物")
    collective_relations()
    four_library_relation()
    for i, lower, higher in (
        (1332, "孔目官", "都孔目官"),
        (1333, "四库书直官", "孔目官"),
        (1334, "书直官", "四库书直官"),
        (1335, "表奏官", "书直官"),
        (1336, "书库官", "表奏官"),
        (1337, "守当官", "书库官"),
        (1338, "正名楷书", "守当官"),
        (1339, "守阙楷书", "正名楷书"),
        (1340, "正系名楷书", "守阙楷书"),
        (1341, "守阙系名楷书", "正系名楷书"),
        (1342, "投名人", "守阙系名楷书"),
    ):
        advancement(i, lower, higher)
    entry1347()
    entry1348()
    entry1349()
    entry1350()


if __name__ == "__main__":
    main()
