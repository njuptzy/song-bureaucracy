#!/usr/bin/env python3
"""提取 chapter5t7 第1241-1260条：殿前步军与侍卫亲军马步军司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1221_1240 as previous


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch5t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter5t7 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(1241, 1261)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
relation = base.relation
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "五代后梁": 910,
    "五代后唐长兴二年": 931,
    "五代后唐天成二年十月二十五日": 927.82,
    "五代后晋天福三年十一月十三日": 938.87,
    "五代后晋天福三年": 938,
    "五代后汉": 950,
    "后周显德元年": 954,
    "宋初": 960,
    "北宋乾德中": 965,
    "北宋乾德中以后（具体年月未载）": 970,
    "北宋开宝间": 972,
    "北宋太平兴国二年正月十九日": 977.05,
    "北宋太平兴国四年": 979,
    "北宋太平兴国中": 980,
    "北宋雍熙三年六月": 986.46,
    "北宋雍熙四年": 987,
    "北宋雍熙四年以后（具体年月未载）": 987.1,
    "北宋端拱元年十月十一日": 988.79,
    "北宋淳化二年": 991,
    "北宋淳化四年": 993,
    "北宋咸平五年": 1002,
    "北宋景德元年": 1004,
    "北宋景德二年正月十九日": 1005.05,
    "北宋大中祥符二年": 1009,
    "北宋明道元年十月": 1032.8,
    "北宋熙宁三年十二月": 1070.95,
    "北宋熙宁二年": 1069,
    "北宋熙宁六年": 1073,
    "北宋元丰元年十月": 1078.8,
    "北宋元丰二年八月十二日": 1079.62,
    "北宋元丰四年": 1081,
    "北宋元祐二年八月": 1087.6,
    "北宋绍圣元年十一月": 1094.87,
    "宋代": 1100,
    "南宋": 1150,
    "南宋建炎初": 1127.1,
    "南宋绍兴十五年": 1145,
    "南宋绍兴十八年": 1148,
    "南宋孝宗朝": 1170,
    "南宋乾道七年十二月": 1171.95,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    match = re.search(r"(-?\d{3,4})", time or "")
    if match:
        return (int(match.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def palace_command_relations(w, touched, i, member_tid, quotation, time,
                             *, foot_group="殿前司步军诸指挥"):
    command = node(w, touched, i, "殿前司", "机构", time,
                   f"统辖{F[i]['title']}", quotation, "禁军指挥机构",
                   "建立殿前司同期承载节点。")
    group = node(w, touched, i, foot_group, "机构", time,
                 f"包括{F[i]['title']}", quotation, "禁军编制总称",
                 f"建立{foot_group}同期承载节点。")
    relation(w, i, command, member_tid, "上下级机构", quotation,
             f"{F[i]['title']}隶殿前司。")
    relation(w, i, group, member_tid, "统称与实例", quotation,
             f"{F[i]['title']}是{foot_group}之一。")


def evolution_edge(w, i, source, target, quotation, decision, field_name=None):
    relation(w, i, source, target, "前后演变", quotation, decision, field_name)


def entry1241():
    i, main = 1241, F[1241]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "捧日上三军", "机构", "宋代",
        "捧日左、右厢各前三军精锐劲旅的合称",
        ("捧日左厢第一军", "捧日左厢第二军", "捧日左厢第三军",
         "捧日右厢第一军", "捧日右厢第二军", "捧日右厢第三军"),
        main, "正文逐一明确左、右厢前三军为上三军。",
    )
    finish(w, touched, "建立捧日上三军统称及左、右厢六个明确实例。")


def entry1242():
    i, main = 1242, F[1242]["text"]
    w, touched = W(i), set()
    stages = (
        ("骁雄军", "北宋乾德中", "选诸州骑兵送京师始建"),
        ("骁猛军", "北宋乾德中以后（具体年月未载）", "由骁雄军改名"),
        ("拱辰军", "北宋雍熙四年", "由骁猛军改名"),
        ("殿前司拱圣军", "北宋雍熙四年以后（具体年月未载）",
         "由拱辰军不久改名，驻京师，共二十一指挥"),
    )
    tids = [node(w, touched, i, title, "机构", time, event, main,
                 "禁军骑兵编制", f"记录{title}沿革。", update_event=True)
            for title, time, event in stages]
    for a, b, (title, _, _) in zip(tids, tids[1:], stages[1:]):
        evolution_edge(w, i, a, b, main, f"禁军番号依次改为{title}。")
    target = tids[-1]
    palace_command_relations(
        w, touched, i, target, main,
        "北宋雍熙四年以后（具体年月未载）",
        foot_group="殿前司骑军诸指挥",
    )
    node(w, touched, i, "殿前司拱圣军", "机构", "北宋熙宁六年",
         "二十一指挥并为十一指挥", main, "禁军骑兵编制",
         "记录熙宁六年裁并。", update_event=True)
    node(w, touched, i, "殿前司拱圣军", "机构", "南宋", "沿置",
         main, "禁军骑兵编制", "记录南宋沿置。", update_event=True)
    finish(w, touched, "整理拱圣军骁雄、骁猛、拱辰、拱圣演变，隶属、指挥数与南宋沿置。")


def entry1243():
    i, main = 1243, F[1243]["text"]
    w, touched = W(i), set()
    start = node(w, touched, i, "殿前司骁骑军", "机构", "北宋太平兴国四年",
                 "始置，分上、下军共二十三指挥，驻京师", main,
                 "禁军骑兵编制", "记录骁骑军始置与初制。", update_event=True)
    palace_command_relations(
        w, touched, i, start, main, "北宋太平兴国四年",
        foot_group="殿前司骑军诸指挥",
    )
    group_instances(
        w, touched, i, "殿前司骁骑军", "机构", "北宋咸平五年",
        "上军、下军改为左厢、右厢",
        ("殿前司骁骑左厢", "殿前司骁骑右厢"), main,
        "正文明确咸平五年改称左、右厢。",
    )
    node(w, touched, i, "殿前司骁骑军", "机构", "北宋熙宁六年",
         "二十三指挥并为十四指挥，上骁骑、弩手、殿前小底皆废",
         main, "禁军骑兵编制", "记录熙宁六年裁并。", update_event=True)
    finish(w, touched, "整理骁骑军始置、骑军归属、咸平左右厢与熙宁裁并。")


def entry1244():
    i = 1244
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "别称")
    w, touched = W(i), set()
    node(w, touched, i, "殿前司步军诸指挥", "机构", "后周显德元年",
         "后周控鹤步军为其源流", origin, "禁军步兵编制源流",
         "记录后周控鹤步军源流。", "职源与沿革", update_event=True)
    group = group_instances(
        w, touched, i, "殿前司步军诸指挥", "机构", "宋代",
        "殿前司所属步军诸军指挥总称",
        ("天武左、右厢", "殿前司虎翼军", "殿前司神勇军",
         "殿前司宣武军", "殿前司广勇军", "殿前司广德军",
         "殿前司龙骑军"), roster,
        "编制字段明确列出主要步军番号。", "编制",
    )
    command = node(w, touched, i, "殿前司", "机构", "宋代",
                   "统辖步军诸指挥", main, "禁军指挥机构",
                   "建立殿前司同期承载节点。")
    relation(w, i, command, group, "上下级机构", main,
             "殿前司步军诸指挥隶殿前司。")
    cite(w, "Timepoints", group, i, origin, "保存后周控鹤及北宋天武等沿革。", "职源与沿革")
    cite(w, "Timepoints", group, i, duty, "保存守京、征戍与仪卫职掌。", "职掌")
    cite(w, "Timepoints", group, i, roster, "保存步军番号、编制单位与军职层级。", "编制")
    alias_note(w, i, group, aliases, "别称")
    finish(w, touched, "整理殿前司步军诸指挥源流、殿前司隶属、主要实例、职掌编制与别称。")


def entry1245():
    i = 1245
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称与旧称")
    w, touched = W(i), set()
    old = node(w, touched, i, "控鹤军", "机构", "后周显德元年",
               "殿前禁军旧号", origin, "禁军步兵旧号",
               "记录后周控鹤旧号。", "职源与沿革", update_event=True)
    grouped = group_instances(
        w, touched, i, "天武左、右厢", "机构",
        "北宋太平兴国二年正月十九日",
        "控鹤改名天武并分左、右厢，为上四军之一和殿前司步军主力",
        ("天武左厢", "天武右厢"), origin,
        "正式词头及编制明确左、右二厢。", "职源与沿革",
    )
    evolution_edge(w, i, old, grouped, origin,
                   "太平兴国二年控鹤改名天武。", "职源与沿革")
    palace_command_relations(
        w, touched, i, grouped, main, "北宋太平兴国二年正月十九日",
    )
    cite(w, "Timepoints", grouped, i, duty, "保存守京、征戍、仪卫及分管军务职掌。", "职掌")
    cite(w, "Timepoints", grouped, i, roster, "保存左右厢军额、指挥数变化与军职层级。", "编制")
    alias_note(w, i, grouped, aliases, "简称与旧称")
    finish(w, touched, "整理天武左右厢由控鹤改名、左右实例、步军归属、职掌编制与旧称。")


def entry1246():
    i = 1246
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    old = node(w, touched, i, "宽衣控鹤指挥", "机构", "后周显德元年",
               "宽衣天武旧号", origin, "禁军步兵旧号",
               "记录后周宽衣控鹤旧号。", "职源与沿革", update_event=True)
    current = node(
        w, touched, i, "宽衣天武指挥", "机构",
        "北宋太平兴国二年正月十九日", "由宽衣控鹤改名，一指挥",
        origin, "禁军步兵编制", "记录太平兴国二年改名。", "职源与沿革",
        update_event=True,
    )
    evolution_edge(w, i, old, current, origin,
                   "宽衣控鹤于太平兴国二年改名宽衣天武。", "职源与沿革")
    parent = node(w, touched, i, "天武左、右厢", "机构",
                  "北宋太平兴国二年正月十九日", "下设宽衣天武指挥",
                  main, "禁军步兵编制", "建立天武左右厢同期节点。")
    relation(w, i, parent, current, "上下级机构", main,
             "宽衣天武指挥隶殿前司天武左、右厢。")
    cite(w, "Timepoints", current, i, duty, "保存内门宿卫、围子与太后仪卫职掌。", "职掌")
    cite(w, "Timepoints", current, i, roster, "保存一指挥及军职层级。", "编制")
    node(w, touched, i, "宽衣天武指挥", "机构", "北宋元丰元年十月",
         "罢置", origin, "禁军步兵编制", "记录元丰罢置。", "职源与沿革",
         update_event=True)
    node(w, touched, i, "宽衣天武指挥", "机构", "北宋绍圣元年十一月",
         "复置", origin, "禁军步兵编制", "记录绍圣复置。", "职源与沿革",
         update_event=True)
    alias_note(w, i, current, aliases, "简称")
    finish(w, touched, "整理宽衣天武由宽衣控鹤改名、天武隶属、宿卫职掌、编制及罢复。")


def entry1247():
    i = 1247
    main, origin = F[i]["text"], field(i, "职源")
    duty, rank, aliases = field(i, "职掌"), field(i, "品位"), field(i, "简称与别名")
    w, touched = W(i), set()
    four = group_instances(
        w, touched, i, "殿前司捧日天武四厢", "机构",
        "北宋端拱元年十月十一日", "捧日左、右厢与天武左、右厢合称",
        ("捧日左、右厢", "天武左、右厢"), duty,
        "职掌明确总领捧日、天武左、右四厢。", "职掌",
    )
    _, post, _ = office_staff(
        w, touched, i, "殿前司捧日天武四厢",
        "殿前司捧日天武四厢都指挥使", "北宋端拱元年十月十一日",
        origin, "端拱元年始置四厢都指挥使。", "职源",
        staff_type="四厢最高指挥官", office_event="设置四厢都指挥使",
        post_event="始置，总领捧日、天武左、右四厢禁军公事",
        grade="从五品",
    )
    assert four
    cite(w, "Timepoints", post, i, duty, "保存总领四厢及后渐为虚衔的职掌变化。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存从五品与管军序位。", "品位")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理捧日天武四厢都指挥使始置、四厢统辖、职掌、品位与别称。")


def entry1248():
    i = 1248
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称与旧称")
    w, touched = W(i), set()
    old = node(w, touched, i, "上铁林军", "机构", "北宋太平兴国中",
               "拣雄武弩手始立", origin, "禁军步兵旧号",
               "记录上铁林始立。", "职源与沿革", update_event=True)
    current = node(w, touched, i, "殿前司虎翼军", "机构", "北宋雍熙四年",
                   "由上铁林改名", origin, "禁军步兵编制",
                   "记录雍熙四年改名虎翼。", "职源与沿革", update_event=True)
    evolution_edge(w, i, old, current, origin,
                   "雍熙四年上铁林改为殿前司虎翼军。", "职源与沿革")
    palace_command_relations(w, touched, i, current, main, "北宋雍熙四年")
    cite(w, "Timepoints", current, i, duty, "保存守京与征戍职掌。", "职掌")
    cite(w, "Timepoints", current, i, roster, "保存左右军、虎翼水军及指挥数变化。", "编制")
    node(w, touched, i, "殿前司虎翼军", "机构", "北宋元丰二年八月十二日",
         "尚与侍卫步军司虎翼军并置", origin, "禁军步兵编制",
         "记录元丰二年仍与同名军并置。", "职源与沿革", update_event=True)
    alias_note(w, i, current, aliases, "简称与旧称")
    finish(w, touched, "整理殿前司虎翼军由上铁林改名、步军归属、职掌编制与旧称。")


def entry1249():
    i = 1249
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称与旧称")
    w, touched = W(i), set()
    old = node(w, touched, i, "广武军", "机构", "北宋淳化二年",
               "拣强壮善射禁军创立", origin, "禁军步兵旧号",
               "记录广武军创立。", "职源与沿革", update_event=True)
    current = node(w, touched, i, "殿前司广勇军", "机构", "北宋大中祥符二年",
                   "由广武军改名", origin, "禁军步兵编制",
                   "记录大中祥符二年改名。", "职源与沿革", update_event=True)
    evolution_edge(w, i, old, current, origin,
                   "大中祥符二年广武军改为广勇军。", "职源与沿革")
    palace_command_relations(w, touched, i, current, main, "北宋大中祥符二年")
    cite(w, "Timepoints", current, i, duty, "保存守京征戍与驻京、驻外指挥数。", "职掌")
    cite(w, "Timepoints", current, i, roster, "保存分军、指挥总数与军职层级。", "编制")
    node(w, touched, i, "殿前司广勇军", "机构", "北宋元祐二年八月",
         "增置左、右第三军第一指挥，共四十五指挥", roster,
         "禁军步兵编制", "记录元祐增置。", "编制", update_event=True)
    alias_note(w, i, current, aliases, "简称与旧称")
    finish(w, touched, "整理广勇军由广武改名、步军归属、职掌编制与元祐增置。")


def entry1250():
    i, main = 1250, F[1250]["text"]
    w, touched = W(i), set()
    stages = (
        ("雄威军", "北宋乾德中", "选诸军强壮魁梧者创立"),
        ("雄勇军", "北宋太平兴国二年正月十九日", "由雄威军改名"),
        ("殿前司神勇军", "北宋雍熙四年", "由雄勇军改名，驻京师"),
    )
    tids = [node(w, touched, i, title, "机构", time, event, main,
                 "禁军步兵编制", f"记录{title}沿革。", update_event=True)
            for title, time, event in stages]
    evolution_edge(w, i, tids[0], tids[1], main, "雄威军改名雄勇军。")
    evolution_edge(w, i, tids[1], tids[2], main, "雍熙四年雄勇军改名神勇军。")
    palace_command_relations(w, touched, i, tids[2], main, "北宋雍熙四年")
    node(w, touched, i, "殿前司神勇军", "机构", "北宋淳化四年",
         "选武艺超群者为上神勇指挥", main, "禁军步兵编制",
         "记录淳化四年上神勇指挥。", update_event=True)
    node(w, touched, i, "殿前司神勇军", "机构", "北宋熙宁六年",
         "上、下二军二十一指挥并为十四指挥，罢上神勇", main,
         "禁军步兵编制", "记录熙宁六年裁并。", update_event=True)
    source = node(w, touched, i, "殿前司神勇军", "机构", "南宋孝宗朝",
                  "改为护圣军", main, "禁军步兵旧号",
                  "记录南宋孝宗朝改名。", update_event=True)
    target = node(w, touched, i, "护圣军", "机构", "南宋孝宗朝",
                  "由殿前司神勇军改名", main, "南宋禁军步兵编制",
                  "建立护圣军后继节点。", update_event=True)
    evolution_edge(w, i, source, target, main, "南宋孝宗朝神勇军改为护圣军。")
    finish(w, touched, "整理神勇军雄威、雄勇、神勇沿革，步军归属、编制变化及南宋改护圣军。")


def entry1251():
    i, main = 1251, F[1251]["text"]
    w, touched = W(i), set()
    post = node(w, touched, i, "殿前司胜捷军", "机构", "南宋建炎初",
                "始置，为殿前司步军诸军之一", main, "禁军步兵编制",
                "建立胜捷军建炎始置节点。", update_event=True)
    palace_command_relations(w, touched, i, post, main, "南宋建炎初")
    finish(w, touched, "建立殿前司胜捷军南宋建炎始置、殿前司隶属与步军实例关系。")


def entry1252():
    i, main, aliases = 1252, F[1252]["text"], field(1252, "简称与别称")
    w, touched = W(i), set()
    old = node(w, touched, i, "奇兵", "机构", "南宋绍兴十五年",
               "以陈敏、周虎臣两家善战家丁一千人始置", main,
               "禁军步兵旧号", "记录奇兵始置。", update_event=True)
    current = node(w, touched, i, "殿前司左翼军", "机构", "南宋绍兴十八年",
                   "奇兵改名并增至二千人，设统制官，屯驻福建",
                   main, "禁军编制", "记录绍兴十八年改名扩编。", update_event=True)
    evolution_edge(w, i, old, current, main, "绍兴十八年奇兵改为殿前司左翼军。")
    palace_command_relations(
        w, touched, i, current, main, "南宋绍兴十八年",
        foot_group="殿前司骑军诸指挥",
    )
    alias_note(w, i, current, aliases, "简称与别称")
    finish(w, touched, "整理殿前司左翼军由奇兵改名、扩编、统制、屯驻与殿前司马军归属。")


def entry1253():
    i = 1253
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "侍卫亲军司", "机构", "五代后梁",
         "侍卫马步军制度始置", origin, "禁军指挥机构源流",
         "记录后梁侍卫马步军源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "侍卫亲军司", "机构", "五代后汉",
         "已见侍卫司之名", origin, "禁军指挥机构源流",
         "记录后汉侍卫司称谓。", "职源与沿革", update_event=True)
    office = node(w, touched, i, "侍卫亲军司", "机构", "宋初",
                  "北宋沿置，与殿前司合称二司", origin, "禁军指挥机构",
                  "记录北宋沿置。", "职源与沿革", update_event=True)
    cite(w, "Timepoints", office, i, main, "确认侍卫亲军司为禁军官司。")
    cite(w, "Timepoints", office, i, duty, "保存总马军、步军政令职掌。", "职掌")
    cite(w, "Timepoints", office, i, roster, "保存马步两司、军职与吏属编制。", "编制")
    for child_title in ("侍卫亲军马军司", "侍卫亲军步军司"):
        child = node(w, touched, i, child_title, "机构", "宋初",
                     "隶侍卫亲军司", roster, "所属禁军指挥机构",
                     f"建立{child_title}宋初承载节点。", "编制")
        relation(w, i, office, child, "上下级机构", roster,
                 f"宋初{child_title}由侍卫亲军司统领。", "编制")
    split = node(w, touched, i, "侍卫亲军司", "机构",
                 "北宋景德二年正月十九日", "分为马军司、步军司",
                 origin, "机构分拆", "记录景德二年分司。", "职源与沿革",
                 update_event=True)
    for child_title in ("侍卫亲军马军司", "侍卫亲军步军司"):
        child = node(w, touched, i, child_title, "机构",
                     "北宋景德二年正月十九日", "由侍卫亲军司分置",
                     origin, "三衙机构", f"建立{child_title}分司节点。",
                     "职源与沿革", update_event=True)
        evolution_edge(w, i, split, child, origin,
                       f"景德二年侍卫亲军司分为{child_title}。", "职源与沿革")
    alias_note(w, i, office, aliases, "简称")
    finish(w, touched, "整理侍卫亲军司五代源流、宋初职掌编制及景德分马步二司。")


def combined_officer(i, start_time, current_time, end_time=None):
    title, main = F[i]["title"], F[i]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster = field(i, "品位"), field(i, "编制")
    aliases_name = "简称与别名" if "简称与别名" in F[i]["fields"] else "简称"
    aliases = field(i, aliases_name)
    w, touched = W(i), set()
    node(w, touched, i, title, "官职", start_time,
         "五代始置", origin, "侍卫亲军司军职源流",
         f"记录{title}五代始置。", "职源与沿革", update_event=True)
    _, post, _ = office_staff(
        w, touched, i, "侍卫亲军司", title, current_time, origin,
        f"{title}北宋沿置。", "职源与沿革", quota=1,
        staff_type="侍卫亲军司长官", office_event=f"设置{title}",
        post_event=duty,
    )
    cite(w, "Timepoints", post, i, main, f"确认{title}为军职。")
    cite(w, "Timepoints", post, i, duty, "保存统领或佐领本司公事职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存管军序位。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存一人员额。", "编制")
    if end_time:
        node(w, touched, i, title, "官职", end_time, "罢置或此后不复置",
             origin, "废罢军职", f"记录{title}罢置。", "职源与沿革",
             update_event=True)
    alias_note(w, i, post, aliases, aliases_name)
    finish(w, touched, f"整理{title}五代始置、宋代隶属、职掌、序位、员额、别称与罢置。")


def entry1254():
    combined_officer(1254, "五代后唐天成二年十月二十五日", "宋初",
                     "北宋雍熙三年六月")


def entry1255():
    combined_officer(1255, "五代后晋天福三年十一月十三日", "宋初")


def entry1256():
    combined_officer(1256, "五代后晋天福三年", "宋初",
                     "北宋景德二年正月十九日")


def entry1257():
    i = 1257
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "侍卫亲军马军司", "机构", "后周显德元年",
         "五代后周已置司", origin, "禁军指挥机构源流",
         "记录后周置司。", "职源与沿革", update_event=True)
    office = node(w, touched, i, "侍卫亲军马军司", "机构", "宋代",
                  "北宋沿置，为三衙之一", main, "三衙禁军指挥机构",
                  "建立宋代马军司。", update_event=True)
    three = node(w, touched, i, "三衙", "机构", "宋代",
                 "包括侍卫亲军马军司", main, "禁军最高指挥机构统称",
                 "建立三衙同期承载节点。")
    relation(w, i, three, office, "统称与实例", main,
             "侍卫亲军马军司为三衙之一。")
    cite(w, "Timepoints", office, i, origin, "保存后周源流、北宋沿置与乾道移屯。", "职源与沿革")
    cite(w, "Timepoints", office, i, duty, "保存名籍、训练、宿卫、戍守及赏罚职掌。", "职掌")
    cite(w, "Timepoints", office, i, roster, "保存长官、所领马军与军职层级。", "编制")
    source = node(w, touched, i, "侍卫亲军马军司", "机构", "南宋乾道七年十二月",
                  "移屯建康并称马军行司", origin, "机构移驻改称",
                  "记录乾道移屯改称。", "职源与沿革", update_event=True)
    target = node(w, touched, i, "马军行司", "机构", "南宋乾道七年十二月",
                  "侍卫亲军马军司移屯建康后的称呼", origin, "三衙行司",
                  "建立马军行司节点。", "职源与沿革", update_event=True)
    evolution_edge(w, i, source, target, origin,
                   "乾道七年马军司移屯建康，称马军行司。", "职源与沿革")
    alias_note(w, i, office, aliases, "简称")
    finish(w, touched, "整理侍卫亲军马军司后周源流、三衙实例、职掌编制与乾道移屯改称。")


def cavalry_officer(i, time, event, grade):
    title, main = F[i]["title"], F[i]["text"]
    origin_name = "职源与沿革" if "职源与沿革" in F[i]["fields"] else "职源"
    origin = field(i, origin_name)
    duty, rank, roster = field(i, "职掌"), field(i, "品位"), field(i, "编制")
    aliases_name = "简称与别名" if "简称与别名" in F[i]["fields"] else "简称"
    aliases = field(i, aliases_name)
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "侍卫亲军马军司", title, time, origin,
        f"{title}为侍卫亲军马军司长官。", origin_name,
        quota=1, staff_type="马军司长官", office_event=f"设置{title}",
        post_event=event, grade=grade,
    )
    cite(w, "Timepoints", post, i, main, f"确认{title}为军职。")
    cite(w, "Timepoints", post, i, duty, "保存马军司长官职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存官品与三衙管军序位。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存一人员额。", "编制")
    alias_note(w, i, post, aliases, aliases_name)
    finish(w, touched, f"整理{title}始置、马军司隶属、职掌、官品、员额与别称。")


def entry1258():
    i = 1258
    cavalry_officer(i, "五代后唐长兴二年",
                     "始见置，两宋沿置，为马军司长官，总本司政令",
                     "正五品")
    # 南宋罕置是设置频度变化，不另造废罢节点。


def entry1259():
    cavalry_officer(1259, "北宋景德元年",
                     "始见置；都指挥使阙时领本司公事，亦可带衔领兵在外",
                     "正五品")


def entry1260():
    cavalry_officer(1260, "北宋开宝间",
                     "始见置，为马军司长官之一，按程序申领本司公事",
                     "从五品")


def main():
    for i in range(1241, 1261):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
