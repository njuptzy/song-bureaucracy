#!/usr/bin/env python3
"""提取 chapter5t7 第1261-1280条：侍卫马步军、上四军与厢军编制。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1241_1260 as previous


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


F = {i: load(i) for i in range(1261, 1281)}
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
    "唐初": 620,
    "唐肃宗至德三载": 758,
    "五代后晋": 940,
    "五代后唐长兴元年四月": 930.3,
    "后周广顺元年": 951,
    "北宋建隆二年": 961,
    "北宋乾德三年": 965,
    "北宋太平兴国二年": 977,
    "北宋太平兴国二年正月十九日": 977.05,
    "北宋雍熙四年": 987,
    "北宋端拱元年十月十一日": 988.79,
    "北宋大中祥符元年正月": 1008.05,
    "北宋元丰二年六月十八日前": 1079.45,
    "北宋元丰二年六月十八日以后": 1079.46,
    "北宋元丰二年六月十八日": 1079.46,
    "南宋乾道七年十一月": 1171.87,
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


def evolution_edge(w, i, source, target, quotation, decision, field_name=None):
    relation(w, i, source, target, "前后演变", quotation, decision, field_name)


def three_commands(w, touched, i, member_tid, quotation, time):
    group = node(w, touched, i, "三衙", "机构", time,
                 f"包括{F[i]['title']}", quotation, "禁军最高指挥机构统称",
                 "建立三衙同期承载节点。")
    relation(w, i, group, member_tid, "统称与实例", quotation,
             f"{F[i]['title']}为三衙之一。")


def entry1261():
    i, main, aliases = 1261, F[1261]["text"], field(1261, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "侍卫亲军马军司", F[i]["title"], "南宋", main,
        "南宋以后资浅马帅以此名领马军司事。", quota=1,
        staff_type="马军司主管官", office_event="由主管官领本司事",
        post_event="资浅马帅以此名领本司事",
    )
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理主管侍卫亲军马军司公事的南宋设置、隶属、职掌与别称。")


def entry1262():
    i = 1262
    main, origin = F[i]["text"], field(i, "职源")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    old = node(w, touched, i, "侍卫亲军马军司", "机构", "南宋乾道七年十一月",
               "由临安移屯建康并改称", origin, "三衙机构",
               "记录马军司移屯改称。", "职源", update_event=True)
    office = node(w, touched, i, F[i]["title"], "机构", "南宋乾道七年十一月",
                  "移屯建康后设置，为三衙之一", origin, "三衙行司",
                  "建立马军行司。", "职源", update_event=True)
    evolution_edge(w, i, old, office, origin,
                   "乾道七年十一月马军司移屯建康，改称马军行司。", "职源")
    three_commands(w, touched, i, office, main, "南宋乾道七年十一月")
    cite(w, "Timepoints", office, i, duty, "保存北伐备战与沿用原马军司职事。", "职掌")
    cite(w, "Timepoints", office, i, roster, "保存所属六军、兵额、官额与军职层级。", "编制")
    alias_note(w, i, office, aliases, "简称")
    finish(w, touched, "整理马军行司的移屯改称、三衙实例、职掌编制与简称。")


def entry1263():
    i, main, aliases = 1263, F[1263]["text"], field(1263, "简称")
    w, touched = W(i), set()
    old = node(w, touched, i, "主管侍卫亲军马军司公事", "官职",
               "南宋乾道七年十一月", "随马军司移屯而改名", main,
               "马军司主管官", "建立改名前主管官节点。", update_event=True)
    _, post, _ = office_staff(
        w, touched, i, "侍卫亲军马军行司", F[i]["title"],
        "南宋乾道七年十一月", main,
        "机构移屯改称后，主管官随之易名并由边帅兼任。",
        staff_type="马军行司主管官", office_event="设置主管官",
        post_event="由边帅兼任，统领马军行司公事",
    )
    evolution_edge(w, i, old, post, main,
                   "马军司主管官随机构改称为马军行司主管官。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理主管马军行司公事的乾道改名、隶属、兼任与简称。")


def entry1264():
    i = 1264
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster = field(i, "职掌"), field(i, "编制")
    aliases = field(i, "简称与旧名")
    w, touched = W(i), set()
    old = node(w, touched, i, "护圣军", "机构", "五代后晋",
               "龙卫左、右厢旧号", origin, "禁军骑兵旧号",
               "记录护圣旧号。", "职源与沿革", update_event=True)
    middle = node(w, touched, i, "龙捷左、右厢", "机构", "后周广顺元年",
                  "护圣军改名并分左、右厢", origin, "禁军骑兵编制",
                  "记录后周改名龙捷。", "职源与沿革", update_event=True)
    current = group_instances(
        w, touched, i, F[i]["title"], "机构",
        "北宋太平兴国二年正月十九日",
        "龙捷改名龙卫，分左、右厢，为上四军之一和马军司主力",
        ("龙卫左厢", "龙卫右厢"), origin,
        "正式词头及编制明确分左、右厢。", "职源与沿革",
    )
    evolution_edge(w, i, old, middle, origin, "护圣军于后周广顺元年改为龙捷左右厢。", "职源与沿革")
    evolution_edge(w, i, middle, current, origin, "太平兴国二年龙捷改为龙卫。", "职源与沿革")
    command = node(w, touched, i, "侍卫亲军马军司", "机构",
                   "北宋太平兴国二年正月十九日", "统辖龙卫左、右厢",
                   main, "三衙机构", "建立马军司同期节点。")
    relation(w, i, command, current, "上下级机构", main, "龙卫左、右厢隶侍卫亲军马军司。")
    cite(w, "Timepoints", current, i, duty, "保存守京、征戍及分管军务职掌。", "职掌")
    cite(w, "Timepoints", current, i, roster, "保存左右厢、军、指挥及军职层级。", "编制")
    alias_note(w, i, current, aliases, "简称与旧名")
    finish(w, touched, "整理龙卫左右厢由护圣、龙捷演变，左右实例、马军司隶属及编制旧名。")


def entry1265():
    i, main = 1265, F[1265]["text"]
    members = tuple(f"龙卫{side}厢第{number}军" for side in "左右" for number in "一二三四")
    w, touched = W(i), set()
    group_instances(w, touched, i, F[i]["title"], "机构", "北宋元丰二年六月十八日前",
                    "龙卫左、右厢各第一至第四军的合称，共八军", members,
                    main, "正文明确第一至第四军称龙卫上四军。")
    finish(w, touched, "建立龙卫上四军统称及左右厢八个实例。")


def entry1266():
    i, main = 1266, F[1266]["text"]
    w, touched = W(i), set()
    old = node(w, touched, i, "左、右备征", "机构", "五代后周",
               "云骑军的五代旧番号", main, "禁军骑兵旧号",
               "记录云骑军旧番号。", update_event=True)
    current = node(w, touched, i, F[i]["title"], "机构", "北宋建隆二年",
                   "左、右备征改称云骑军，共十五指挥", main,
                   "禁军骑兵编制", "记录建隆二年改名。", update_event=True)
    evolution_edge(w, i, old, current, main, "建隆二年左、右备征改称云骑军。")
    command = node(w, touched, i, "侍卫亲军马军司", "机构", "北宋建隆二年",
                   "统辖云骑军", main, "三衙机构", "建立马军司同期节点。")
    relation(w, i, command, current, "上下级机构", main, "云骑军隶侍卫亲军马军司。")
    finish(w, touched, "整理云骑军旧号、建隆改名、马军司隶属与指挥数。")


def entry1267():
    i, main = 1267, F[1267]["text"]
    w, touched = W(i), set()
    parent = node(w, touched, i, "云骑军", "机构", "宋代", "拣汰年高退卒另编剩员指挥",
                  main, "禁军骑兵编制", "建立云骑军承载节点。")
    child = node(w, touched, i, F[i]["title"], "机构", "宋代",
                 "由云骑军中年高退卒组成，四百人为额，驻外且不给马",
                 main, "禁军剩员指挥", "建立云骑带甲剩员指挥。", update_event=True)
    relation(w, i, parent, child, "上下级机构", main,
             "云骑带甲剩员指挥由云骑军拣汰的年高退卒组成。")
    finish(w, touched, "整理云骑带甲剩员指挥的云骑军归属、构成、员额与待遇。")


def entry1268():
    i = 1268
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "机构", "五代后周", "已置司",
         origin, "禁军指挥机构源流", "记录后周源流。", "职源与沿革", update_event=True)
    office = node(w, touched, i, F[i]["title"], "机构", "宋代",
                  "北宋沿置，为三衙之一", main, "三衙禁军指挥机构",
                  "建立宋代步军司。", update_event=True)
    three_commands(w, touched, i, office, main, "宋代")
    cite(w, "Timepoints", office, i, duty, "保存名籍、统制、训练、宿卫、戍守与赏罚职掌。", "职掌")
    cite(w, "Timepoints", office, i, roster, "保存本司官额、所领步军及军职层级。", "编制")
    for child_title in ("神卫左、右厢", "步军司虎翼军", "武卫军", "雄武军", "奉节军", "步武军"):
        child = node(w, touched, i, child_title, "机构", "宋代", "隶侍卫亲军步军司",
                     roster, "所属禁军步军", f"建立{child_title}同期节点。", "编制")
        relation(w, i, office, child, "上下级机构", roster,
                 f"编制字段明确{child_title}为步军司所领步军。", "编制")
    alias_note(w, i, office, aliases, "简称")
    finish(w, touched, "整理步军司后周源流、三衙实例、职掌、官额、所领诸军与简称。")


def foot_officer(i, time, origin_name, event, grade):
    main, origin = F[i]["text"], field(i, origin_name)
    duty, rank = field(i, "职掌"), field(i, "品位")
    roster, aliases = field(i, "编制"), field(i, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "侍卫亲军步军司", F[i]["title"], time, origin,
        f"{F[i]['title']}为步军司长官，员额一人。", origin_name,
        quota=1, staff_type="步军司长官", office_event=f"设置{F[i]['title']}",
        post_event=event, grade=grade,
    )
    cite(w, "Timepoints", post, i, main, f"确认{F[i]['title']}为军职。")
    cite(w, "Timepoints", post, i, duty, "保存步军司长官职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存官品与三衙管军序位。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存一人员额。", "编制")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, f"整理{F[i]['title']}始置、步军司隶属、职掌、官品、员额与别称。")


def entry1269():
    foot_officer(1269, "五代后唐长兴元年四月", "职源与沿革",
                 "五代始见置，两宋沿置，总本司政令", "正五品")


def entry1270():
    foot_officer(1270, "北宋大中祥符元年正月", "职源",
                 "始见置，为本司长官之一，必要时领本司公事或带衔在外", "正五品")


def entry1271():
    foot_officer(1271, "北宋乾德三年", "职源",
                 "始见置，为本司长官之一，按程序申领本司公事", "从五品")


def entry1272():
    i, main, aliases = 1272, F[1272]["text"], field(1272, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "侍卫亲军步军司", F[i]["title"], "南宋", main,
        "南宋以后资浅步帅以此名领步军司事。", quota=1,
        staff_type="步军司主管官", office_event="由主管官领本司事",
        post_event="资浅步帅以此名领本司事",
    )
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理主管侍卫亲军步军司公事的南宋设置、隶属、职掌与别称。")


def entry1273():
    i = 1273
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称与旧名")
    w, touched = W(i), set()
    old = node(w, touched, i, "奉国军", "机构", "五代后晋", "神卫左、右厢旧号",
               origin, "禁军步兵旧号", "记录后晋奉国旧号。", "职源与沿革", update_event=True)
    middle = node(w, touched, i, "虎捷左、右厢", "机构", "五代后周",
                  "奉国军改为虎捷", origin, "禁军步兵编制",
                  "记录后周虎捷旧号。", "职源与沿革", update_event=True)
    current = group_instances(
        w, touched, i, F[i]["title"], "机构", "北宋太平兴国二年正月十九日",
        "虎捷改名神卫，分左、右厢，为上四军之一和步军司主力",
        ("神卫左厢", "神卫右厢"), origin,
        "正式词头及编制明确分左、右厢。", "职源与沿革",
    )
    evolution_edge(w, i, old, middle, origin, "后周奉国军改为虎捷。", "职源与沿革")
    evolution_edge(w, i, middle, current, origin, "太平兴国二年虎捷改为神卫。", "职源与沿革")
    command = node(w, touched, i, "侍卫亲军步军司", "机构",
                   "北宋太平兴国二年正月十九日", "统辖神卫左、右厢",
                   main, "三衙机构", "建立步军司同期节点。")
    relation(w, i, command, current, "上下级机构", main, "神卫左、右厢隶侍卫亲军步军司。")
    cite(w, "Timepoints", current, i, duty, "保存守京、征戍及分管军务职掌。", "职掌")
    cite(w, "Timepoints", current, i, roster, "保存左右厢、诸军、剩员与军职层级。", "编制")
    alias_note(w, i, current, aliases, "简称与旧名")
    finish(w, touched, "整理神卫左右厢由奉国、虎捷演变，左右实例、步军司隶属及编制旧名。")


def entry1274():
    i = 1274
    main, origin = F[i]["text"], field(i, "职源")
    duty, rank, aliases = field(i, "职掌"), field(i, "品位"), field(i, "简称与别名")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "马步军龙卫神卫四厢", "机构",
        "北宋端拱元年十月十一日", "龙卫、神卫左右四厢的合称",
        ("龙卫左厢", "龙卫右厢", "神卫左厢", "神卫右厢"), duty,
        "职掌明确总领龙卫、神卫左右四厢。", "职掌",
    )
    post = node(w, touched, i, F[i]["title"], "官职", "北宋端拱元年十月十一日",
                "始置，总领龙卫、神卫左右四厢，后渐为递迁虚衔",
                origin, "四厢统兵官", "记录精确始置时间。", "职源",
                grade="从五品", update_event=True)
    relation(w, i, group, post, "编制隶属", duty,
             "该官职总领马步军龙卫神卫四厢。", "职掌", staff_type="四厢统兵官")
    cite(w, "Timepoints", post, i, main, "确认该词条为军职。")
    cite(w, "Timepoints", post, i, duty, "保存总领范围及后期虚衔性质。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存从五品及管军序位。", "品位")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理马步军龙卫神卫四厢都指挥使始置、四厢实例、职掌、官品与别称。")


def entry1275():
    i = 1275
    main, origin = F[i]["text"], field(i, "职源")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    old = node(w, touched, i, "下铁林", "机构", "北宋太平兴国二年",
               "以雄武弩手次等者组成", origin, "禁军步兵旧号",
               "记录下铁林源流。", "职源", update_event=True)
    current = node(w, touched, i, F[i]["title"], "机构", "北宋雍熙四年",
                   "下铁林改名，隶侍卫亲军步军司", origin,
                   "禁军步兵编制", "记录雍熙四年改名。", "职源", update_event=True)
    evolution_edge(w, i, old, current, origin, "雍熙四年下铁林改为步军司虎翼军。", "职源")
    command = node(w, touched, i, "侍卫亲军步军司", "机构", "北宋雍熙四年",
                   "统辖步军司虎翼军", main, "三衙机构", "建立步军司同期节点。")
    relation(w, i, command, current, "上下级机构", main, "步军司虎翼军隶侍卫亲军步军司。")
    cite(w, "Timepoints", current, i, duty, "保存守京与征戍职掌。", "职掌")
    cite(w, "Timepoints", current, i, roster, "保存左右十军、指挥数及军职层级。", "编制")
    alias_note(w, i, current, aliases, "简称")
    finish(w, touched, "整理步军司虎翼军由下铁林改名、步军司隶属、职掌编制与简称。")


def four_armies_members(last_number):
    return tuple(
        f"{guard}{side}厢第{number}军"
        for guard in ("捧日", "天武", "龙卫", "神卫")
        for side in "左右"
        for number in "一二三四"[:last_number]
    )


def entry1276():
    i, main = 1276, F[1276]["text"]
    w, touched = W(i), set()
    before = group_instances(
        w, touched, i, F[i]["title"], "机构", "北宋元丰二年六月十八日前",
        "捧日、天武、龙卫、神卫左右厢各第一至第四军的待遇等级合称，共三十二军",
        four_armies_members(4), main,
        "原文明确元丰改制前左右各四军待遇均一，合称上四军。",
    )
    after = group_instances(
        w, touched, i, F[i]["title"], "机构", "北宋元丰二年六月十八日以后",
        "各第四军降为中军后，改指捧日、天武、龙卫、神卫左右厢各前三军，共二十四军",
        four_armies_members(3), main,
        "原文明确元丰二年六月十八日后上四军只包括左右厢第一至第三军。",
    )
    assert before != after
    finish(w, touched, "按元丰二年六月十八日前后分别建立上四军的三十二军与二十四军实例范围。")


def entry1277():
    i, main = 1277, F[1277]["text"]
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "机构", "唐肃宗至德三载",
         "英武军已采用左、右厢编制", main, "禁军编制单位源流",
         "记录左、右厢编制源流。", update_event=True)
    node(w, touched, i, F[i]["title"], "机构", "宋代",
         "三衙上四军及部分骑军、步军采用的编制单位", main,
         "禁军编制单位", "记录宋代左、右厢适用范围。", update_event=True)
    finish(w, touched, "整理左、右厢的唐代源流及宋代禁军编制单位性质，不把示例军队误作无时限实例。")


def entry1278():
    i, main, aliases = 1278, F[1278]["text"], field(1278, "别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "左、右厢", F[i]["title"], "宋代", main,
        "禁军左、右厢各置厢都指挥使。", staff_type="厢级指挥官",
        office_event="设置厢级指挥官", post_event="左厢、右厢的指挥官",
    )
    alias_note(w, i, post, aliases, "别名")
    finish(w, touched, "整理厢都指挥使的厢级编制隶属与别名。")


def entry1279():
    i, main = 1279, F[1279]["text"]
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "机构", "唐初",
         "李靖兵法已见厢下设军", main, "禁军编制单位源流",
         "记录军编制的唐初源流。", update_event=True)
    node(w, touched, i, F[i]["title"], "机构", "宋代",
         "厢下一级编制；不设厢者可直接以军为最高编制，每十指挥为一军",
         main, "禁军编制单位", "记录宋代军编制层级。", update_event=True)
    finish(w, touched, "整理军的唐初源流与宋代编制层级，不把列举番号误作无时限实例。")


def entry1280():
    i, main, aliases = 1280, F[1280]["text"], field(1280, "别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "军", F[i]["title"], "宋代", main,
        "军一级编制设置都指挥使为长官。", quota=1,
        staff_type="军级长官", office_event="设置军级长官",
        post_event="军一级编制长官；升迁遥领刺史，再迁为厢都指挥使",
    )
    alias_note(w, i, post, aliases, "别名")
    finish(w, touched, "整理军都指挥使的军级编制隶属、员额、升迁规则与别名。")


def main():
    for i in range(1261, 1281):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
