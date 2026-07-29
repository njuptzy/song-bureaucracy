#!/usr/bin/env python3
"""提取 chapter2t4 第1491–1510条：算学、国史院系统与实录院。"""
import extract_2t4_1471_1490 as x

base = x.base
base.F = {i: base.load(i) for i in range(1491, 1511)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def ft_any(w, entity_id, *times):
    for time in times:
        tid = w.find_timepoint(entity_id, time)
        if tid:
            return tid
    raise AssertionError((entity_id, times))


def alias(w, tid, i):
    for key in ("简称", "别称", "别名"):
        if key in F[i]["fields"]:
            cite(w, "Timepoints", tid, i, field(i, key),
                 f"{F[i]['title']}称谓仅作名称证据。", key,
                 note="纯简称或别称")


def entry1491():
    i = 1491
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("造历局楷书", "官职", "本条直接定义造历局楷书。",
                   quotation=main)
    tid = tp(w, eid, "宋代造新历期间", "专掌誊抄历书",
             i, main, "造历局吏人", "建立造历局楷书节点。",
             attr_officer_type="吏")
    rel(w, ft(w, fe(w, "造历局", "机构"), "宋代造新历期间"),
        tid, "编制隶属", i, main, "楷书隶造历局。", staff_type="吏")
    w.commit()


def entry1492():
    i = 1492
    main, origin = Q(i, F[i]["text"]), field(i, "职源")
    w = W(i)
    eid = w.entity("太史官", "官职", "本条定义司天监、太史局官通称。",
                   quotation=main)
    pre = tp(w, eid, "先秦西周", "已有世袭太史，掌天时星历",
             i, origin, "前代职源", "建立太史官先秦职源节点。",
             "职源", attr_officer_type="古官", chain="none")
    song = tp(w, eid, "宋代", "司天监官、太史局官通称，掌天文星历",
              i, main, "天文官统称", "建立宋代太史官统称节点。",
              attr_officer_type="技术官统称", chain="none")
    alias(w, song, i)
    chain_all(w, eid, [pre, song], "连接太史官先秦职源与宋代统称节点。")
    for title, time in (
        ("司天监官", "北宋（司天监时期）"),
        ("太史局官", "宋代太史局时期"),
    ):
        rel(w, song, ft(w, fe(w, title, "官职"), time),
            "统称与实例", i, main, f"{title}是太史官实例。")
    w.commit()


def entry1493():
    i = 1493
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("算学", "机构", "本条直接定义宋代算学。",
                   quotation=main)
    planned = tp(w, eid, "北宋元丰官制规划", "列为五学之一，但未及建置",
                 i, main, "学校", "建立算学元丰规划节点。", chain="none")
    start = tp(w, eid, "北宋崇宁三年六月", "始建算学",
               i, main, "学校", "建立算学崇宁始建节点。", chain="none")
    end1 = tp(w, eid, "北宋崇宁五年四月十二日", "罢算学",
              i, main, "学校", "建立算学首次罢置节点。", chain="none")
    restore = tp(w, eid, "北宋崇宁五年十一月", "复置算学",
                 i, main, "学校", "建立算学复置节点。", chain="none")
    merge = tp(w, eid, "北宋大观四年三月二日",
               "算学生并入太史局，算学官吏并罢",
               i, main, "学校", "建立算学并入太史局节点。", chain="none")
    end2 = tp(w, eid, "北宋宣和二年七月二十一日", "罢算学",
              i, main, "学校", "建立算学宣和罢置节点。", chain="none")
    chain_all(w, eid, [planned, start, end1, restore, merge, end2],
              "连接算学规划、两次设置及罢并节点。")
    w.commit()


def entry1494():
    i = 1494
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("算学生", "官职", "本条直接定义算学生。",
                   quotation=main)
    active = tp(
        w, eid, "北宋崇宁三年六月",
        "在算学习天文、历算、三式、法算四科；命官与未出官人均可报考，上中下等分别补通仕郎、登仕郎、将仕郎",
        i, main, "算学学生", "建立算学生崇宁节点。",
        attr_officer_type="学生", chain="none",
    )
    merge = tp(w, eid, "北宋大观四年三月二日", "并入太史局",
               i, main, "太史局学生", "建立算学生并入太史局节点。",
               attr_officer_type="学生", chain="none")
    alias(w, active, i)
    chain_all(w, eid, [active, merge], "连接算学生在算学与并入太史局节点。")
    rel(w, ft(w, fe(w, "算学", "机构"), "北宋崇宁三年六月"),
        active, "编制隶属", i, main, "算学生在算学习业。",
        staff_type="学生")
    rel(w, merge, ft(w, fe(w, "太史局学生", "官职"), "宋代太史局时期"),
        "前后演变", i, main, "大观四年算学生并入太史局。")
    w.commit()


def entry1495():
    i = 1495
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    eid = fe(w, "国史院", "机构")
    north = refine(
        w, ft_any(
            w, eid, "北宋元丰五年以后", "北宋元祐五年十一月十三日"
        ), i, history,
        "专条将国史院始置细化到元祐五年十一月十三日。",
        "职源与沿革", time="北宋元祐五年十一月十三日",
        event="始置，承秘书省国史案职事，隶门下省，初掌国史、实录、日历",
        category="修正史机构",
    )
    cite(w, "Timepoints", north, i, duty, "补证国史院职掌。",
         "职掌")
    cite(w, "Timepoints", north, i, staff, "补证国史院编制。",
         "编制")
    alias(w, north, i)
    south = tp(w, eid, "南宋绍兴二十八年七月十九日",
               "复置修国史院，专掌修正史",
               i, history, "修正史机构", "建立南宋国史院复置节点。",
               "职源与沿革", chain="none")
    late = tp(w, eid, "南宋嘉泰二年以后", "与实录院并置",
              i, history, "修正史机构", "建立国史院与实录院并置节点。",
              "职源与沿革", chain="none")
    chain_all(w, eid, [north, south, late], "连接国史院北宋始置与南宋复置节点。")
    rel(w, ft(w, fe(w, "门下省", "机构"), "北宋元祐间"),
        north, "上下级机构", i, main, "元祐初国史院隶门下省。")
    w.commit()


def entry1496():
    i = 1496
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("修史院", "机构", "本条直接定义修史院。",
                   quotation=main)
    tid = tp(w, eid, "北宋雍熙四年九月",
             "于史馆西庑始置，修日历、实录、国史",
             i, main, "修史机构", "建立修史院雍熙节点。")
    w.commit()


def entry1497():
    i = 1497
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("编修院", "机构", "本条直接定义编修院。",
                   quotation=main)
    active = tp(w, eid, "北宋天圣九年五月二十九日",
                "修史院移宣徽院之东改称编修院，隶门下省，修国史、会要",
                i, main, "修史机构", "建立编修院天圣节点。",
                chain="none")
    end = tp(w, eid, "北宋元丰四年十一月", "废罢，职事归史馆",
             i, main, "修史机构", "建立编修院元丰罢置节点。",
             chain="none")
    alias(w, active, i)
    chain_all(w, eid, [active, end], "连接编修院设置与罢置节点。")
    rel(w, ft(w, fe(w, "修史院", "机构"), "北宋雍熙四年九月"),
        active, "前后演变", i, main, "天圣九年修史院改称编修院。")
    w.commit()


def entry1498():
    i = 1498
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "史馆", "机构")
    for time, decision in (
        ("宋初", "补证宋初史馆及元丰前修史职能。"),
        ("北宋元丰五年", "补证元丰五年史馆并入秘书省国史案。"),
        ("南宋绍兴十年二月二十九日", "补证南宋绍兴十年复罢史馆。"),
    ):
        cite(w, "Timepoints", ft(w, eid, time), i, main, decision)
    w.commit()


def entry1499():
    i = 1499
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "国史案", "机构")
    reform = refine(
        w, ft_any(
            w, eid, "北宋元丰五年", "北宋元丰五年五月"
        ), i, main,
        "专条细化国史案时间、隶属与职掌。",
        time="北宋元丰五年五月",
        event="罢史馆归秘书省国史案，掌国史、实录、日历及关报材料",
        category="秘书省修史机构",
    )
    transfer = tp(w, eid, "北宋元祐五年十一月十三日",
                  "职事归门下省新建国史院",
                  i, main, "秘书省修史机构", "建立国史案职事转出节点。",
                  chain="none")
    south = tp(w, eid, "南宋绍兴十年二月二十二日",
               "罢史馆归秘书省国史案，主修纂日历；四月改名国史日历所",
               i, main, "秘书省修史机构", "建立南宋国史案节点。",
               chain="none")
    chain_all(w, eid, [reform, transfer, south], "连接国史案北宋与南宋节点。")
    rel(w, ft(w, fe(w, "秘书省", "机构"), "北宋元丰五年五月"),
        reform, "上下级机构", i, main, "国史案隶秘书省。")
    rel(w, transfer,
        ft(w, fe(w, "国史院", "机构"), "北宋元祐五年十一月十三日"),
        "前后演变", i, main, "元祐五年国史案职事归国史院。")
    w.commit()


def history_post(i, title, event, time, parent_time, *, quota=None,
                 origin=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}史职。",
                   quotation=main)
    nodes = []
    if origin:
        ot, oe = origin
        nodes.append(tp(w, eid, ot, oe, i, main, "前代职源",
                        f"建立{title}{ot}职源节点。", chain="none"))
    tid = tp(w, eid, time, event, i, main, "国史院史职",
             f"建立{title}节点。", attr_officer_type="兼官或史官",
             chain="none" if nodes else "auto")
    alias(w, tid, i)
    if nodes:
        chain_all(w, eid, nodes + [tid], f"连接{title}职源与宋代节点。")
    rel(w, ft(w, fe(w, "国史院", "机构"), parent_time),
        tid, "编制隶属", i, main, f"{title}在国史院兼修史事。",
        staff_quota=quota, staff_type="兼官或史官")
    w.commit()


def entry1501():
    i = 1501
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提领修国史", "官职", "本条定义避讳所改兼官名。",
                   quotation=main)
    tid = tp(w, eid, "南宋隆兴元年",
             "因汤思退父名举避讳，提举修三朝国史改称提领修三朝国史",
             i, main, "国史院兼官异称", "建立提领修国史隆兴节点。",
             attr_officer_type="兼官")
    rel(w, ft(w, fe(w, "提举修国史", "官职"), "宋代国史院时期"),
        tid, "前后演变", i, main, "隆兴元年避讳，提举改称提领。")
    w.commit()


def entry1505():
    i = 1505
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "监修国史", "官职")
    pre = refine(
        w, ft(w, eid, "北宋乾德二年正月"), i, main,
        "专条补证元丰改制前监修国史为宰相所带衔。",
        event="宰相兼监修国史，元丰改制前为宰相所带衔",
        category="宰相兼官", officer="兼官",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰五年"), i, main,
        "专条修正元丰改制后监修国史并非罢绝，而是不入宰相衔。",
        event="改制后宰相监修国史不入衔",
        category="宰相兼官", officer="兼官",
    )
    south = tp(w, eid, "南宋绍兴二十八年八月十四日",
               "右仆射汤思退监修国史，领修神、哲、徽三朝正史",
               i, main, "宰相兼官", "建立监修国史绍兴节点。",
               attr_officer_type="兼官", chain="none")
    alias(w, south, i)
    chain_all(
        w, eid,
        [
            ft(w, eid, "唐贞观三年闰十二月"),
            ft(w, eid, "北宋建隆元年二月"),
            pre,
            ft(w, eid, "北宋皇祐五年闰七月"),
            reform,
            ft(w, eid, "南宋绍兴三年六月二十七日"),
            ft(w, eid, "南宋绍兴十年以后"),
            ft(w, eid, "南宋绍兴二十六年五月以后"),
            south,
        ],
        "连接监修国史唐代职源、宋初、改制前后与南宋完整时间链。",
    )
    rel(w, ft(w, fe(w, "国史院", "机构"), "南宋绍兴二十八年七月十九日"),
        south, "编制隶属", i, main, "监修国史主持南宋国史院修史。",
        staff_type="宰相兼官")
    w.commit()


def entry1510():
    i = 1510
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    eid = w.entity("实录院", "机构", "本条直接定义实录院。",
                   quotation=main)
    name = tp(w, eid, "北宋咸平元年正月", "始见实录院之名",
              i, history, "修实录机构", "建立实录院咸平名源节点。",
              "职源与沿革", chain="none")
    reform = tp(w, eid, "北宋元丰改制后",
                "遇修实录即临时开实录院",
                i, history, "修实录机构", "建立实录院元丰后节点。",
                "职源与沿革", chain="none")
    south = tp(w, eid, "南宋绍兴十年二月以后",
               "史馆罢后，遇修实录另设实录院，由宰相提举",
               i, history, "修实录机构", "建立实录院绍兴节点。",
               "职源与沿革", chain="none")
    late = tp(w, eid, "南宋嘉定二年以后", "与国史院并置",
              i, history, "修实录机构", "建立实录院嘉定并置节点。",
              "职源与沿革", chain="none")
    cite(w, "Timepoints", south, i, duty, "补证实录院职掌。",
         "职掌")
    cite(w, "Timepoints", south, i, staff, "补证实录院编制。",
         "编制")
    chain_all(w, eid, [name, reform, south, late], "连接实录院北宋至南宋节点。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1491, 1511)] == [
        "楷书", "太史官", "算学", "算学生", "国史院", "修史院",
        "编修院", "史馆", "国史案", "提举修国史", "提领修国史",
        "提举国史院", "权提举国史院", "国史院", "监修国史",
        "修国史", "同修国史", "国史院编修", "国史院检讨官", "实录院",
    ]
    assert F[1504]["fields"].get("__status__") == "placeholder"
    entry1491()
    entry1492()
    entry1493()
    entry1494()
    entry1495()
    entry1496()
    entry1497()
    entry1498()
    entry1499()
    history_post(1500, "提举修国史",
                 "宰相兼领修国史；乾兴有提举之名，天圣五年与监修分为二职",
                 "宋代国史院时期", "北宋元祐五年十一月十三日")
    entry1501()
    history_post(1502, "提举国史院",
                 "右相兼领修正史，职任同提举修国史",
                 "南宋（国史院）", "南宋绍兴二十八年七月十九日")
    history_post(1503, "权提举国史院",
                 "由参知政事兼领者带权字，始置于乾道元年三月",
                 "南宋乾道元年三月", "南宋绍兴二十八年七月十九日")
    entry1505()
    history_post(1506, "修国史",
                 "宋代多由六部尚书、翰林学士等侍从官兼修正史",
                 "北宋淳化四年", "北宋元祐五年十一月十三日",
                 origin=("唐长安二年", "始置修国史"))
    history_post(1507, "同修国史",
                 "以六部侍郎等侍从官兼执笔修史，景德中始置",
                 "北宋景德年间", "北宋元祐五年十一月十三日")
    history_post(1508, "国史院编修",
                 "非侍从官入编修院、国史院兼执笔修史，编制无定员",
                 "宋代国史院时期", "北宋元祐五年十一月十三日")
    history_post(1509, "国史院检讨官",
                 "非侍从官或秘书省官兼修国史，绍兴十三、十四年曾置三人后不复置",
                 "南宋绍兴十三至十四年", "南宋绍兴二十八年七月十九日")
    entry1510()


if __name__ == "__main__":
    main()
