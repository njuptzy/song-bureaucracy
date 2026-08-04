#!/usr/bin/env python3
"""提取 chapter5t7 第1221-1240条：御龙诸直、五重禁卫与殿前司骑军。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1201_1220 as previous


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


F = {i: load(i) for i in range(1221, 1241)}
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
    "唐代": 700,
    "宋初": 960,
    "北宋太平兴国二年正月十九日": 977.05,
    "北宋太平兴国二年正月十九日以后（具体年月未载）": 977.06,
    "北宋咸平元年正月": 998.05,
    "宋代": 1100,
    "北宋": 1050,
    "南宋宁宗时": 1210,
    "五代": 930,
    "后周显德元年十月": 954.8,
    "北宋雍熙四年五月十九日": 987.38,
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


def dragon_parents(w, touched, i, member_tid, quotation, time):
    command = node(
        w, touched, i, "殿前司", "机构", time, "统辖殿前御龙诸直",
        quotation, "禁军指挥机构", "建立殿前司同期承载节点。",
    )
    dragon = node(
        w, touched, i, "殿前御龙诸直", "机构", time,
        "皇帝近身步兵诸直总称", quotation, "禁军步兵编制总称",
        "建立殿前御龙诸直同期承载节点。",
    )
    relation(w, i, command, member_tid, "上下级机构", quotation,
             f"{F[i]['title']}隶殿前司。")
    relation(w, i, dragon, member_tid, "统称与实例", quotation,
             f"{F[i]['title']}是殿前御龙诸直所含班直。")


def entry1221():
    i = 1221
    main, origin = F[i]["text"], field(i, "职源")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    node(
        w, touched, i, "殿前御龙诸直", "机构",
        "北宋太平兴国二年正月十九日",
        "御龙诸直名称体系形成", origin, "禁军步兵编制总称",
        "记录御龙诸直名称体系形成的精确时间。", "职源",
        update_event=True,
    )
    group = group_instances(
        w, touched, i, "殿前御龙诸直", "机构", "宋代",
        "包括御龙左右直、骨朵子左右直、弓箭五直与弩五直",
        ("御龙左直、右直", "御龙骨朵子左直、右直",
         "御龙弓箭直", "御龙弩直"),
        roster, "编制字段明确列出四类御龙诸直。", "编制",
    )
    command = node(
        w, touched, i, "殿前司", "机构", "宋代",
        "统辖殿前御龙诸直", main, "禁军指挥机构",
        "建立殿前司同期承载节点。",
    )
    relation(w, i, command, group, "上下级机构", main,
             "殿前御龙诸直隶殿前司。")
    cite(w, "Timepoints", group, i, duty,
         "保存近身宿卫、扈从乘舆与内三重禁卫职掌。", "职掌")
    cite(w, "Timepoints", group, i, roster,
         "保存四类诸直、军职层级及诸班诸直总兵额。", "编制")
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理殿前御龙诸直名称形成、殿前司隶属、四类实例、职掌编制与简称。")


def entry1222():
    i, main = 1222, F[1222]["text"]
    w, touched = W(i), set()
    old = node(w, touched, i, "簇御马直", "机构", "宋初",
               "殿前诸直旧称", main, "禁军班直旧称", "建立宋初旧称节点。",
               update_event=True)
    middle = node(
        w, touched, i, "簇御龙直", "机构", "北宋太平兴国二年正月十九日",
        "由簇御马直改名", main, "禁军班直沿革",
        "记录太平兴国二年改名。", update_event=True,
    )
    grouped = group_instances(
        w, touched, i, "御龙左直、右直", "机构", "北宋咸平元年正月",
        "已称御龙直，分左直、右直，为皇宫步兵近卫和仪卫",
        ("御龙左直", "御龙右直"), main,
        "正式词头明确左、右二直。",
    )
    relation(w, i, old, middle, "前后演变", main,
             "簇御马直于太平兴国二年改为簇御龙直。")
    relation(w, i, middle, grouped, "前后演变", main,
             "簇御龙直后改为御龙直，咸平元年正月已有御龙直之称。")
    dragon_parents(w, touched, i, grouped, main, "北宋咸平元年正月")
    finish(w, touched, "整理御龙左右直由簇御马直、簇御龙直演变及左右实例与隶属。")


def entry1223():
    i, main, aliases = 1223, F[1223]["text"], field(1223, "简称")
    w, touched = W(i), set()
    old = node(w, touched, i, "骨朵子直", "机构", "宋初", "殿前诸直旧称",
               main, "禁军班直旧称", "建立宋初旧称节点。", update_event=True)
    middle = node(
        w, touched, i, "御龙散手直", "机构", "北宋太平兴国二年正月十九日",
        "由骨朵子直改名", main, "禁军班直沿革",
        "记录太平兴国二年改名。", update_event=True,
    )
    grouped = group_instances(
        w, touched, i, "御龙骨朵子左直、右直", "机构",
        "北宋太平兴国二年正月十九日以后（具体年月未载）",
        "由御龙散手直后改，分左直、右直，为皇宫步兵近卫和仪卫",
        ("御龙骨朵子左直", "御龙骨朵子右直"), main,
        "正式词头明确左、右二直。",
    )
    relation(w, i, old, middle, "前后演变", main,
             "骨朵子直于太平兴国二年改为御龙散手直。")
    relation(w, i, middle, grouped, "前后演变", main,
             "御龙散手直后来改为御龙骨朵子直。")
    dragon_parents(
        w, touched, i, grouped, main,
        "北宋太平兴国二年正月十九日以后（具体年月未载）",
    )
    alias_note(w, i, grouped, aliases, "简称")
    finish(w, touched, "整理御龙骨朵子左右直两次改名、左右实例、隶属与简称。")


def five_dragon_class(i, members, event):
    main, aliases, title = F[i]["text"], field(i, "简称"), F[i]["title"]
    w, touched = W(i), set()
    grouped = group_instances(
        w, touched, i, title, "机构", "宋代", event, members, main,
        "正文明确分第一至第五直。",
    )
    dragon_parents(w, touched, i, grouped, main, "宋代")
    alias_note(w, i, grouped, aliases, "简称")
    finish(w, touched, f"整理{title}五直实例、殿前司隶属、御龙诸直归属、职能与简称。")


def entry1224():
    five_dragon_class(
        1224, tuple(f"御龙弓箭直第{n}直" for n in "一二三四五"),
        "分第一至第五直，选诸军材貌魁伟者充，为皇宫步兵近卫和仪卫",
    )


def entry1225():
    five_dragon_class(
        1225, tuple(f"御龙弩直第{n}直" for n in "一二三四五"),
        "分第一至第五直，为皇宫步兵近卫和仪卫",
    )


def entry1226():
    i, main, aliases = 1226, F[1226]["text"], field(1226, "简称与别名")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "诸班直", "机构", "宋代",
        "殿前诸班与殿前御龙诸直合称，专充扈卫",
        ("殿前诸班", "殿前御龙诸直"), main,
        "正文明确诸班直是两类禁旅的合称。",
    )
    north = node(w, touched, i, "诸班直", "机构", "北宋",
                 "禁旅三千六百余人", main, "禁军班直合称",
                 "记录北宋兵额。", update_event=True)
    south = node(w, touched, i, "诸班直", "机构", "南宋宁宗时",
                 "立定二千二百五十二人员额", main, "禁军班直合称",
                 "记录南宋宁宗时兵额。", update_event=True)
    alias_note(w, i, group, aliases, "简称与别名")
    assert north and south
    finish(w, touched, "整理诸班直的两类实例、宿卫性质、北宋与南宋兵额及别称。")


OFFICER_EVENTS = {
    1227: ("四直都虞候", "御龙四直最高指挥官", "御龙四直最高指挥官"),
    1228: ("诸直都虞候", "各直最高指挥官，位次于四直都虞候", "各直都虞候"),
    1229: ("诸直指挥使", "各直统兵官，位次于都虞候", "各直指挥使"),
    1230: ("诸直副指挥使", "各直副统兵官，位次于指挥使", "各直副指挥使"),
    1231: ("诸直都头", "各直都统兵官，一都约一百人", "各直都头"),
    1232: ("诸直副都头", "各直都副统兵官，位次于都头", "各直副都头"),
    1233: ("诸直十将", "各直都的基层领兵官之一，或分左、右", "各直十将"),
    1234: ("诸直将虞候", "各直军职，位次于十将", "各直将虞候"),
    1235: ("诸直队长", "禁卫军最基层队级军职，每队约五十人", "各直队长"),
}


def officer_entry(i):
    main = F[i]["text"]
    title, event, staff_type = OFFICER_EVENTS[i]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "殿前御龙诸直", title, "宋代", main,
        f"{title}为殿前御龙诸直军职。", staff_type=staff_type,
        office_event=f"设置{title}", post_event=event,
    )
    finish(w, touched, f"建立{title}的御龙诸直编制隶属、军职性质与位次。")


def entry1227(): officer_entry(1227)
def entry1228(): officer_entry(1228)
def entry1229(): officer_entry(1229)
def entry1230(): officer_entry(1230)
def entry1231(): officer_entry(1231)
def entry1232(): officer_entry(1232)
def entry1233(): officer_entry(1233)
def entry1234(): officer_entry(1234)
def entry1235(): officer_entry(1235)


def entry1236():
    i, main = 1236, F[1236]["text"]
    w, touched = W(i), set()
    group = node(w, touched, i, "五重禁卫军", "机构", "宋代",
                 "条令规定的天子禁卫五重编组", main, "禁卫层级统称",
                 "建立五重禁卫军条令编组。", update_event=True)
    layers = (
        ("五重禁卫军第一重", "皇城司亲从官把守"),
        ("五重禁卫军第二重", "殿前司天武左、右厢宽衣天武官把守"),
        ("五重禁卫军第三重", "殿前司御龙弓箭直、御龙弩直卫士把守"),
        ("五重禁卫军第四重", "殿前司御龙骨朵子直卫士把守"),
        ("五重禁卫军第五重", "殿前司御龙直卫士把守"),
    )
    for title, event in layers:
        layer = node(w, touched, i, title, "机构", "宋代", event, main,
                     "禁卫层级", f"建立{title}及其卫士组成。", update_event=True)
        relation(w, i, group, layer, "统称与实例", main,
                 f"{title}是条令所定五重禁卫军的一重，不作常设上下级机构。")
    finish(w, touched, "按条令建立五重禁卫军及五个层级实例，避免误作永久上下级机构。")


def entry1237():
    i, main = 1237, F[1237]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "奉宸队", "机构", "唐代",
         "千牛卫营曾改名奉宸，为名称源流", main, "仪卫编制源流",
         "记录奉宸名称唐代源流。", update_event=True)
    node(w, touched, i, "奉宸队", "机构", "宋代",
         "由殿前司诸御龙直充，分左右排列，为大驾扈从禁卫", main,
         "临时仪卫编制", "记录宋代奉宸队组成与职掌。", update_event=True)
    finish(w, touched, "整理奉宸队唐代名称源流与宋代御龙诸直充任的仪卫职掌。")


def entry1238():
    i, main = 1238, F[1238]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "捧日队", "机构", "宋代",
         "由殿前诸班充，每队三十一人，为大驾卤簿亲兵扈从", main,
         "临时仪卫编制", "建立捧日队组成、员额与职掌。", update_event=True)
    finish(w, touched, "整理捧日队由殿前诸班充任、三十一人员额与扈从职掌。")


def entry1239():
    i = 1239
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "别称")
    w, touched = W(i), set()
    node(w, touched, i, "殿前司骑军诸指挥", "机构", "后周显德元年十月",
         "殿前司铁骑马军为其源流", origin, "禁军骑兵编制源流",
         "记录后周铁骑马军源流。", "职源与沿革", update_event=True)
    office = node(w, touched, i, "殿前司骑军诸指挥", "机构", "宋代",
                  "北宋沿置，为殿前司所属骑军编制", main, "禁军骑兵编制总称",
                  "建立宋代殿前司骑军诸指挥。", update_event=True)
    command = node(w, touched, i, "殿前司", "机构", "宋代",
                   "统辖骑军诸指挥", main, "禁军指挥机构",
                   "建立殿前司同期承载节点。")
    relation(w, i, command, office, "上下级机构", main,
             "殿前司骑军诸指挥隶殿前司。")
    cite(w, "Timepoints", office, i, origin, "保存后周铁骑及宋代捧日等番号沿革。", "职源与沿革")
    cite(w, "Timepoints", office, i, duty, "保存守京师、备征戍职掌。", "职掌")
    cite(w, "Timepoints", office, i, roster, "保存骑军番号与军职层级，不预建后续正式词条。", "编制")
    alias_note(w, i, office, aliases, "别称")
    finish(w, touched, "整理殿前司骑军诸指挥后周源流、宋代隶属、职掌编制与别称。")


def entry1240():
    i = 1240
    main, origin = F[i]["text"], field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称与旧称")
    w, touched = W(i), set()
    old = node(w, touched, i, "小底", "机构", "五代", "捧日军前身番号",
               origin, "禁军番号旧称", "记录五代小底旧号。", "职源与沿革",
               update_event=True)
    iron = node(w, touched, i, "铁骑", "机构", "后周显德元年十月",
                "由小底改号，为殿前司骑军", origin, "禁军骑军番号",
                "记录后周改号铁骑。", "职源与沿革", update_event=True)
    day = node(w, touched, i, "日骑", "机构", "北宋太平兴国二年正月十九日",
               "由铁骑改号", origin, "禁军骑军番号",
               "记录太平兴国二年改号日骑。", "职源与沿革", update_event=True)
    grouped = group_instances(
        w, touched, i, "捧日左、右厢", "机构", "北宋雍熙四年五月十九日",
        "由日骑改为捧日，分左、右厢，为上四军之一和殿前司骑军主力",
        ("捧日左厢", "捧日右厢"), origin,
        "正式词头及编制明确分左、右厢。", "职源与沿革",
    )
    relation(w, i, old, iron, "前后演变", origin,
             "后周显德元年小底改号铁骑。", "职源与沿革")
    relation(w, i, iron, day, "前后演变", origin,
             "太平兴国二年铁骑改号日骑。", "职源与沿革")
    relation(w, i, day, grouped, "前后演变", origin,
             "雍熙四年日骑改号捧日，正式词头分左、右厢。", "职源与沿革")
    command = node(w, touched, i, "殿前司", "机构", "北宋雍熙四年五月十九日",
                   "统辖捧日左、右厢", main, "禁军指挥机构",
                   "建立殿前司同期承载节点。")
    cavalry = node(
        w, touched, i, "殿前司骑军诸指挥", "机构", "北宋雍熙四年五月十九日",
        "包括捧日左、右厢", main, "禁军骑兵编制总称",
        "建立骑军诸指挥同期承载节点。",
    )
    relation(w, i, command, grouped, "上下级机构", main,
             "捧日左、右厢隶殿前司。")
    relation(w, i, cavalry, grouped, "统称与实例", main,
             "捧日左、右厢是殿前司骑军诸指挥之一。")
    cite(w, "Timepoints", grouped, i, duty, "保存守京师、备征戍与分管马军公事职掌。", "职掌")
    cite(w, "Timepoints", grouped, i, roster, "保存左右厢军额、指挥数变化与军职层级。", "编制")
    alias_note(w, i, grouped, aliases, "简称与旧称")
    finish(w, touched, "整理捧日左右厢小底至铁骑、日骑、捧日演变，左右实例、隶属、职掌编制与旧称。")


def main():
    for i in range(1221, 1241):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
