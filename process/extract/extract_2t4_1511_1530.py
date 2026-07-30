#!/usr/bin/env python3
"""提取 chapter2t4 第1511–1530条：实录院、日历所与会要所。"""
import extract_2t4_1491_1510 as x

base = x.base
base.F = {i: base.load(i) for i in range(1511, 1531)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def alias(w, tid, i):
    for key in ("简称", "简称与别名", "别名"):
        if key in F[i]["fields"]:
            cite(w, "Timepoints", tid, i, field(i, key),
                 f"{F[i]['title']}称谓仅作名称证据。", key,
                 note="纯简称或别名")


def institute(w, time="南宋绍兴十年二月以后"):
    return ft(w, fe(w, "实录院", "机构"), time)


def history_office(i, title, time, event, *, quota=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}兼官。",
                   quotation=main)
    tid = tp(w, eid, time, event, i, main, "实录院兼官",
             f"建立{title}节点。", attr_officer_type="兼官")
    alias(w, tid, i)
    rel(w, institute(w), tid, "编制隶属", i, main,
        f"{title}总领或参领实录院修史。", staff_quota=quota,
        staff_type="兼官")
    w.commit()


def entry1511():
    i = 1511
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("专切提举监修实录", "官职",
                   "本条定义乾兴修真宗实录时所设提举兼官。",
                   quotation=main)
    tid = tp(w, eid, "北宋乾兴元年十二月二十二日",
             "命右仆射冯拯专切提举监修，为修实录设提举官之始",
             i, main, "实录院兼官", "建立专切提举监修实录始置节点。",
             attr_officer_type="宰相兼官")
    rel(w, institute(w, "北宋咸平元年正月"), tid, "编制隶属", i, main,
        "该兼官为修实录所设提举官。", staff_quota=1,
        staff_type="宰相兼官")
    w.commit()


def entry1512():
    i = 1512
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提举修实录", "官职", "本条直接定义提举修实录。",
                   quotation=main)
    tid = tp(w, eid, "北宋元祐元年二月",
             "宰臣蔡确提举修神宗皇帝实录，总提实录大纲",
             i, main, "实录院兼官", "建立提举修实录元祐节点。",
             attr_officer_type="宰相兼官")
    rel(w, institute(w, "北宋咸平元年正月"), tid, "编制隶属", i, main,
        "宰相兼提举修实录。", staff_type="宰相兼官")
    rel(w, ft(w, fe(w, "专切提举监修实录", "官职"),
              "北宋乾兴元年十二月二十二日"), tid,
        "前后演变", i, main, "乾兴所始创提举修实录之制，后称提举修实录。")
    w.commit()


def entry1513():
    i = 1513
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提举史馆实录院", "官职",
                   "本条定义实录院寓史馆时的提举官衔。", quotation=main)
    tid = tp(w, eid, "南宋绍兴四年至十年",
             "实录院寓史馆，以宰臣一员兼，总领修实录事",
             i, main, "实录院兼官", "建立提举史馆实录院节点。",
             attr_officer_type="宰相兼官")
    alias(w, tid, i)
    rel(w, ft(w, fe(w, "史馆", "机构"), "南宋建炎元年五月"), tid,
        "编制隶属", i, main, "实录院寓史馆时提举官并系史馆名。",
        staff_quota=1, staff_type="宰相兼官")
    w.commit()


def entry1514():
    i = 1514
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提举实录院", "官职", "本条直接定义提举实录院。",
                   quotation=main)
    first = tp(w, eid, "南宋绍兴十年二月二十二日以后",
               "史馆罢后宰相领修实录，以提举实录院系衔；秦桧独相时兼领",
               i, main, "实录院兼官", "建立提举实录院绍兴十年节点。",
               attr_officer_type="宰相兼官", chain="none")
    two = tp(w, eid, "南宋绍兴二十六年以后",
             "置二相时由右相提举；无次相则参知政事权提举",
             i, main, "实录院兼官", "建立提举实录院二相制度节点。",
             attr_officer_type="宰相兼官", chain="none")
    alias(w, first, i)
    chain_all(w, eid, [first, two], "连接提举实录院绍兴十年与二十六年后节点。")
    rel(w, institute(w), first, "编制隶属", i, main,
        "宰相提举实录院。", staff_type="宰相兼官")
    rel(w, ft(w, fe(w, "提举史馆实录院", "官职"), "南宋绍兴四年至十年"),
        first, "前后演变", i, main, "绍兴十年史馆罢后官衔去史馆名。")
    w.commit()


def entry1515():
    i = 1515
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提领实录院", "官职", "本条定义避讳所改官名。",
                   quotation=main)
    tid = tp(w, eid, "南宋绍兴二十七年七月七日",
             "汤思退因父名举避讳，提举实录院特改称提领实录院",
             i, main, "实录院兼官异称", "建立提领实录院避讳节点。",
             attr_officer_type="宰相兼官")
    rel(w, institute(w), tid, "编制隶属", i, main,
        "提领实录院为提举实录院避讳称。", staff_type="宰相兼官")
    rel(w, ft(w, fe(w, "提举实录院", "官职"), "南宋绍兴二十六年以后"),
        tid, "前后演变", i, main, "绍兴二十七年因汤举名讳改提举为提领。")
    w.commit()


def entry1516():
    history_office(1516, "修实录", "南宋绍兴十一年七月",
                   "参知政事范同兼修实录，参领徽宗实录纂修")


def entry1517():
    i = 1517
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("权提举实录院", "官职", "本条定义副相权提举实录院。",
                   quotation=main)
    tid = tp(w, eid, "南宋乾道二年十二月十九日",
             "缺次相提举时由副相权提举，始置权提举实录院",
             i, main, "实录院兼官", "建立权提举实录院始置节点。",
             attr_officer_type="执政兼官")
    rel(w, institute(w), tid, "编制隶属", i, main,
        "副相权提举实录院。", staff_type="执政兼官")
    rel(w, ft(w, fe(w, "提举实录院", "官职"), "南宋绍兴二十六年以后"),
        tid, "前后演变", i, main, "缺次相时由副相权提举。")
    w.commit()


def entry1518():
    i = 1518
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("实录院修撰", "官职", "本条直接定义实录院修撰。",
                   quotation=main)
    origin = tp(w, eid, "北宋乾兴元年十一月八日",
                "已命侍从官修撰真宗实录，尚未冠实录院名",
                i, main, "实录史官名源", "建立实录院修撰名源节点。",
                attr_officer_type="侍从史官", chain="none")
    south = tp(w, eid, "南宋实录院时期", "侍从官修实录称实录院修撰，为主笔史官",
               i, main, "实录院史官", "建立实录院修撰南宋节点。",
               attr_officer_type="侍从史官", chain="none")
    quota = tp(w, eid, "南宋庆元六年", "与实录院同修撰合计以六员为额",
               i, main, "实录院史官", "建立实录院修撰庆元编制节点。",
               attr_officer_type="侍从史官", chain="none")
    alias(w, south, i)
    chain_all(w, eid, [origin, south, quota], "连接实录院修撰名源、南宋与庆元编制节点。")
    rel(w, institute(w), south, "编制隶属", i, main,
        "实录院修撰隶实录院。", staff_quota="与同修撰合计6员",
        staff_type="侍从史官")
    w.commit()


def entry1519():
    i = 1519
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("实录院同修撰", "官职", "本条直接定义实录院同修撰。",
                   quotation=main)
    origin = tp(w, eid, "北宋乾兴元年十一月",
                "已有同修撰真宗实录之名，尚未冠实录院名",
                i, main, "实录史官名源", "建立同修撰实录名源节点。",
                attr_officer_type="侍从史官", chain="none")
    start = tp(w, eid, "南宋绍兴二十七年十一月二十六日",
               "正式始置实录院同修撰，资序稍次于修撰",
               i, main, "实录院史官", "建立实录院同修撰始置节点。",
               attr_officer_type="侍从史官", chain="none")
    quota = tp(w, eid, "南宋庆元六年", "与实录院修撰合计以六员为额",
               i, main, "实录院史官", "建立实录院同修撰庆元编制节点。",
               attr_officer_type="侍从史官", chain="none")
    alias(w, start, i)
    chain_all(w, eid, [origin, start, quota], "连接实录院同修撰名源、始置与编制节点。")
    rel(w, institute(w), start, "编制隶属", i, main,
        "实录院同修撰隶实录院。", staff_quota="与修撰合计6员",
        staff_type="侍从史官")
    w.commit()


def entry1520():
    i = 1520
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("权实录院同修撰", "官职",
                   "本条定义非侍从官所带权同修撰。", quotation=main)
    tid = tp(w, eid, "南宋淳熙三年正月",
             "李焘以非侍从官始带权实录院同修撰；两月后迁侍从官即落权字",
             i, main, "实录院史官", "建立权实录院同修撰始置节点。",
             attr_officer_type="非侍从史官")
    rel(w, institute(w), tid, "编制隶属", i, main,
        "权实录院同修撰隶实录院。", staff_type="非侍从史官")
    rel(w, tid, ft(w, fe(w, "实录院同修撰", "官职"),
                   "南宋绍兴二十七年十一月二十六日"),
        "前后演变", i, main, "非侍从官迁侍从官后落权字为同修撰。")
    w.commit()


def entry1521():
    i = 1521
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("实录院检讨官", "官职", "本条直接定义实录院检讨官。",
                   quotation=main)
    origin = tp(w, eid, "北宋天圣元年二月十一日",
                "始置真宗实录检讨官，尚未冠实录院名",
                i, main, "实录史官名源", "建立实录检讨名源节点。",
                attr_officer_type="非侍从史官", chain="none")
    start = tp(w, eid, "南宋绍兴九年三月二十二日",
               "始置实录院检讨官，掌实录撰写",
               i, main, "实录院史官", "建立实录院检讨官始置节点。",
               attr_officer_type="非侍从史官", chain="none")
    quota = tp(w, eid, "南宋庆元六年", "编制六员",
               i, main, "实录院史官", "建立实录院检讨官庆元编制节点。",
               attr_officer_type="史官", chain="none")
    alias(w, start, i)
    chain_all(w, eid, [origin, start, quota], "连接实录院检讨官名源、始置与编制节点。")
    rel(w, institute(w), start, "编制隶属", i, main,
        "实录院检讨官隶实录院。", staff_quota=6,
        staff_type="非侍从史官")
    w.commit()


def entry1522():
    i = 1522
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("国史实录院编修检讨官", "官职",
                   "本条定义国史院编修官、实录院检讨官连称。",
                   quotation=main)
    total = tp(w, eid, "南宋国史院实录院并置时期",
               "国史院编修官与实录院检讨官相兼通借的连称",
               i, main, "两院史官连称", "建立国史实录院编修检讨官节点。",
               attr_officer_type="复合官衔")
    alias(w, total, i)
    for title, time in (
        ("国史院编修", "宋代国史院时期"),
        ("实录院检讨官", "南宋绍兴九年三月二十二日"),
    ):
        rel(w, total, ft(w, fe(w, title, "官职"), time),
            "统称与实例", i, main, f"{title}是该连称的组成官职。")
    w.commit()


def entry1523():
    i = 1523
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    eid = w.entity("日历所", "机构", "本条直接定义修日历机构。",
                   quotation=main)
    specs = [
        ("唐永贞元年九月六日", "令史官修撰日历，为修日历之始"),
        ("宋初", "修日历归史馆，监修国史提举，史馆官分纂"),
        ("北宋仁宗朝", "于编修院修日历，始见编修院日历所之称"),
        ("北宋元丰改制后", "修日历事归秘书省国史案"),
        ("北宋绍圣二年以后", "改秘书省日历案，或称秘书省日历所"),
        ("北宋宣和二年八月二十三日", "罢日历所"),
        ("南宋绍兴元年四月八日", "设置修日历所"),
        ("南宋绍兴四年五月二十四日", "修日历所改名史馆"),
        ("南宋绍兴十年二月二十二日", "史馆罢，由秘书省国史案主修日历"),
        ("南宋绍兴十年四月二十八日", "国史案改名国史日历所"),
    ]
    nodes = [
        tp(w, eid, time, event, i, history,
           "修日历机构" if not time.startswith("唐") else "前代职源",
           f"建立日历所{time}节点。", "职源与沿革", chain="none")
        for time, event in specs
    ]
    cite(w, "Timepoints", nodes[6], i, duty, "补证日历所职掌。", "职掌")
    cite(w, "Timepoints", nodes[6], i, staff, "补证日历所编制。", "编制")
    alias(w, nodes[6], i)
    chain_all(w, eid, nodes, "连接日历所唐代名源、北宋沿革、宣和罢置与南宋改名节点。")
    for parent_title, parent_time, node_index in (
        ("史馆", "宋初", 1),
        ("编修院", "北宋天圣九年五月二十九日", 2),
        ("秘书省", "北宋元丰五年五月", 3),
        ("秘书省", "北宋元丰五年五月", 4),
        ("秘书省", "南宋绍兴元年二月十九日", 6),
    ):
        rel(w, ft(w, fe(w, parent_title, "机构"), parent_time), nodes[node_index],
            "上下级机构", i, history, f"该期日历所隶{parent_title}。")
    w.commit()


def entry1524():
    i = 1524
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("国史日历所", "机构", "本条直接定义南宋国史日历所。",
                   quotation=main)
    name = tp(w, eid, "南宋绍兴三年十一月",
              "修日历所改称修国史日历所",
              i, main, "秘书省修史机构", "建立修国史日历所名源节点。",
              chain="none")
    formal = tp(w, eid, "南宋绍兴十年四月二十八日",
                "秘书省国史案改名国史日历所，主修日历，终南宋不变",
                i, main, "秘书省修史机构", "建立国史日历所正式节点。",
                chain="none")
    alias(w, formal, i)
    existing = ft(w, eid, "南宋隆兴元年五月十九日")
    chain_all(w, eid, [name, formal, existing],
              "连接修国史日历所名源、正式节点与既有编类圣政所并入节点。")
    rel(w, ft(w, fe(w, "秘书省", "机构"), "南宋绍兴元年二月十九日"),
        formal, "上下级机构", i, main, "国史日历所隶秘书省。")
    rel(w, ft(w, fe(w, "日历所", "机构"), "南宋绍兴十年四月二十八日"),
        formal, "前后演变", i, main, "绍兴十年秘书省国史案改名国史日历所。")
    w.commit()


def entry1525():
    i = 1525
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提举修日历官", "官职", "本条直接定义提举修日历官。",
                   quotation=main)
    regular = tp(w, eid, "宋代修日历时期",
                 "由宰相兼、以监修国史系衔，兼提修日历大纲",
                 i, main, "修日历兼官", "建立提举修日历官常制节点。",
                 attr_officer_type="宰相兼官", chain="none")
    late = tp(w, eid, "南宋淳祐十二年以后",
              "宰臣领日历所带提举日历所衔",
              i, main, "修日历兼官", "建立提举日历所系衔节点。",
              attr_officer_type="宰相兼官", chain="none")
    chain_all(w, eid, [regular, late], "连接提举修日历官常制与淳祐后系衔节点。")
    rel(w, ft(w, fe(w, "国史日历所", "机构"), "南宋绍兴十年四月二十八日"),
        late, "编制隶属", i, main, "宰臣提举国史日历所。",
        staff_type="宰相兼官")
    w.commit()


def entry1526():
    i = 1526
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("日历所检讨官", "官职", "本条直接定义日历所检讨官。",
                   quotation=main)
    tid = tp(w, eid, "南宋绍兴二十七年",
             "由秘书省正字权兼，掌修日历，仅除授一人后不复除",
             i, main, "日历所史官", "建立日历所检讨官绍兴节点。",
             attr_officer_type="兼官")
    rel(w, ft(w, fe(w, "国史日历所", "机构"), "南宋绍兴十年四月二十八日"),
        tid, "编制隶属", i, main, "日历所检讨官隶国史日历所。",
        staff_quota=1, staff_type="兼官")
    w.commit()


def entry1527():
    i = 1527
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("日历修书官", "官职", "本条定义各期实际修日历官的总称。",
                   quotation=main)
    north = tp(w, eid, "北宋前期", "史馆修撰、直史馆主纂，判史馆事、史馆检讨参修",
               i, main, "修日历官统称", "建立北宋前期日历修书官节点。",
               attr_officer_type="修书官统称", chain="none")
    reform = tp(w, eid, "北宋元丰改制后", "著作郎、著作佐郎专纂日历，称第一等修书官",
                i, main, "修日历官统称", "建立元丰后日历修书官节点。",
                attr_officer_type="修书官统称", chain="none")
    south = tp(w, eid, "南宋绍兴三年至二十九年",
               "著作郎、佐郎与史馆修撰、史馆检讨共同纂修日历",
               i, main, "修日历官统称", "建立绍兴日历修书官节点。",
               attr_officer_type="修书官统称", chain="none")
    late = tp(w, eid, "南宋绍兴二十九年八月二十四日以后",
              "史馆修撰、检讨罢后，由秘书省著作官专职修纂日历",
              i, main, "修日历官统称", "建立绍兴二十九年后节点。",
              attr_officer_type="修书官统称", chain="none")
    chain_all(w, eid, [north, reform, south, late], "连接两宋日历修书官制度节点。")
    for parent_tid, child_title, child_time in (
        (north, "史馆修撰", "宋初"),
        (north, "直史馆", "北宋太平兴国以前"),
        (north, "判史馆事", "宋初"),
        (north, "史馆检讨", "北宋淳化二年十月二日"),
        (reform, "著作郎", "北宋元丰五年五月"),
        (reform, "著作佐郎", "北宋元丰五年五月"),
        (south, "史馆修撰", "南宋绍兴三年八月二十三日"),
        (south, "史馆检讨", "南宋绍兴初"),
    ):
        rel(w, parent_tid, ft(w, fe(w, child_title, "官职"), child_time),
            "统称与实例", i, main, f"{child_title}是该期日历修书官实例。")
    w.commit()


def entry1528():
    i = 1528
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("日历所编类圣政检讨官", "官职",
                   "本条直接定义日历所编类圣政检讨官。", quotation=main)
    tid = tp(w, eid, "南宋隆兴元年七月",
             "始置，以秘书省正字以下官兼，纂修编类圣政文字",
             i, main, "日历所史官", "建立编类圣政检讨官始置节点。",
             attr_officer_type="兼官")
    alias(w, tid, i)
    rel(w, ft(w, fe(w, "国史日历所", "机构"), "南宋绍兴十年四月二十八日"),
        tid, "编制隶属", i, main, "编类圣政检讨官隶日历所。",
        staff_type="兼官")
    w.commit()


def entry1529():
    i = 1529
    main, history, duty, staff = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    eid = w.entity("编修国朝会要所", "机构", "本条直接定义修本朝会要机构。",
                   quotation=main)
    specs = [
        ("唐贞元间", "苏冕修唐会要，会要之名始于此", "前代职源"),
        ("北宋天圣末", "于修史院修纂会要", "修会要机构"),
        ("北宋庆历间", "于编修院置局修会要", "修会要机构"),
        ("北宋熙宁间", "于崇文院置局，称编修会要所", "修会要机构"),
        ("北宋元丰改制后", "在秘书省著作局置所修会要", "秘书省修史机构"),
        ("北宋崇宁以后", "称编修国朝会要所", "秘书省修史机构"),
        ("南宋", "沿置并隶秘书省，或称编纂会要所", "秘书省修史机构"),
    ]
    nodes = [
        tp(w, eid, time, event, i, history, category,
           f"建立编修国朝会要所{time}节点。", "职源与沿革", chain="none")
        for time, event, category in specs
    ]
    cite(w, "Timepoints", nodes[-1], i, duty, "补证会要所职掌。", "职掌")
    cite(w, "Timepoints", nodes[-1], i, staff, "补证会要所编制。", "编制")
    alias(w, nodes[-1], i)
    chain_all(w, eid, nodes, "连接会要名源及两宋会要所沿革节点。")
    for parent_title, parent_time, node_index in (
        ("修史院", "北宋雍熙四年九月", 1),
        ("编修院", "北宋天圣九年五月二十九日", 2),
        ("崇文院", "北宋太平兴国三年二月一日", 3),
        ("著作局", "北宋元丰五年", 4),
        ("秘书省", "南宋绍兴元年二月十九日", 6),
    ):
        rel(w, ft(w, fe(w, parent_title, "机构"), parent_time), nodes[node_index],
            "上下级机构", i, history, f"该期会要所设于或隶{parent_title}。")
    w.commit()


def entry1530():
    i = 1530
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提举编修国朝会要", "官职",
                   "本条直接定义提举编修国朝会要兼官。", quotation=main)
    tid = tp(w, eid, "宋代会要所时期",
             "右相兼或参知政事权兼，总提会要所编修事",
             i, main, "会要所兼官", "建立提举编修国朝会要节点。",
             attr_officer_type="宰执兼官")
    rel(w, ft(w, fe(w, "编修国朝会要所", "机构"), "南宋"), tid,
        "编制隶属", i, main, "提举编修国朝会要总领会要所。",
        staff_type="宰执兼官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1511, 1531)] == [
        "专切提举监修实录", "提举修实录", "提举史馆实录院", "提举实录院",
        "提领实录院", "修实录", "权提举实录院", "实录院修撰",
        "实录院同修撰", "权实录院同修撰", "实录院检讨官",
        "国史实录院编修检讨官", "日历所", "国史日历所", "提举修日历官",
        "日历所检讨官", "日历修书官", "日历所编类圣政检讨官",
        "编修国朝会要所", "提举编修国朝会要",
    ]
    entry1511()
    entry1512()
    entry1513()
    entry1514()
    entry1515()
    entry1516()
    entry1517()
    entry1518()
    entry1519()
    entry1520()
    entry1521()
    entry1522()
    entry1523()
    entry1524()
    entry1525()
    entry1526()
    entry1527()
    entry1528()
    entry1529()
    entry1530()


if __name__ == "__main__":
    main()
