#!/usr/bin/env python3
"""提取 chapter5t7 第1201-1220条：殿前诸班班直、军职、殿侍与祗应。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1181_1200 as previous


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


F = {i: load(i) for i in range(1201, 1221)}
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
parent_child = previous.parent_child
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "五代后汉": 947,
    "北宋太平兴国初": 976,
    "北宋太平兴国三年": 978,
    "北宋太平兴国年间": 980,
    "北宋淳化三年": 992,
    "北宋景祐二年十月": 1035.8,
    "北宋景祐三年八月十三日": 1036.62,
    "北宋": 1050,
    "北宋熙宁五年七月": 1072.55,
    "北宋政和时": 1112,
    "北宋政和二年九月二十五日": 1112.73,
    "北宋政和六年三月二日": 1116.18,
    "宋代": 1100,
    "南宋": 1127,
    "南宋绍兴三十年正月十八日": 1160.05,
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


def relation_to_parents(w, touched, i, member_tid, quotation,
                        *, time="宋代", group=True, parent="殿前司"):
    parent_tid = node(
        w, touched, i, parent, "机构", time, f"统辖{F[i]['title']}",
        quotation, "禁军指挥机构", f"建立{parent}{time}承载节点。",
    )
    relation(w, i, parent_tid, member_tid, "上下级机构", quotation,
             f"{F[i]['title']}隶{parent}。")
    if group:
        group_tid = node(
            w, touched, i, "殿前诸班", "机构", time,
            "皇帝近卫骑兵诸班总称", quotation, "禁军班直统称",
            "建立殿前诸班同期承载节点。",
        )
        relation(w, i, group_tid, member_tid, "统称与实例", quotation,
                 f"{F[i]['title']}是殿前诸班之一。")


def paired_class_entry(i, members, event, time="宋代"):
    main, title = F[i]["text"], F[i]["title"]
    w, touched = W(i), set()
    grouped = group_instances(
        w, touched, i, title, "机构", time, event, members, main,
        "合列正式词头明确列出各班实例。",
    )
    relation_to_parents(w, touched, i, grouped, main, time=time)
    finish(w, touched, f"整理{title}的合列实例、殿前司隶属与殿前诸班关系。")


def entry1201():
    i, main = 1201, F[1201]["text"]
    w, touched = W(i), set()
    grouped = group_instances(
        w, touched, i, "金枪左、右班", "机构", "北宋太平兴国初",
        "由内直改名，选军中善用枪槊者充",
        ("金枪左班", "金枪右班"), main,
        "正式词头明确包括金枪左班、右班。",
    )
    relation_to_parents(
        w, touched, i, grouped, main, time="北宋太平兴国初",
    )
    finish(w, touched, "整理金枪左右班改名、成员实例、殿前司隶属与近卫性质。")


def entry1202():
    paired_class_entry(
        1202,
        ("散直左第一班", "散直左第二班", "散直右第一班", "散直右第二班"),
        "殿前诸班近卫禁旅",
    )


def entry1203():
    i, main, aliases = 1203, F[1203]["text"], field(1203, "别称")
    w, touched = W(i), set()
    node(w, touched, i, "殿前东西班", "机构", "五代后汉",
         "称东、西班承旨", main, "禁军班直源流",
         "记录五代后汉旧称。", update_event=True)
    music = node(
        w, touched, i, "殿前东西班", "机构", "北宋太平兴国年间",
        "选擅长音乐卫士组成军乐队，随驾奏乐", main,
        "殿前诸班班直", "记录太平兴国间军乐职能。", update_event=True,
    )
    relation_to_parents(w, touched, i, music, main, time="北宋太平兴国年间")
    jingyou = node(
        w, touched, i, "殿前东西班", "机构", "北宋景祐二年十月",
        "包括十二班", main, "殿前诸班班直",
        "记录景祐二年十二班编制。", update_event=True,
    )
    node(w, touched, i, "殿前东西班", "机构", "北宋政和时",
         "包括十班", main, "殿前诸班班直",
         "记录政和时十班编制。", update_event=True)
    node(w, touched, i, "殿前东西班", "机构", "南宋",
         "减为八班", main, "殿前诸班班直",
         "记录南宋八班编制。", update_event=True)
    alias_note(w, i, jingyou, aliases, "别称")
    finish(w, touched, "整理殿前东西班五代旧称、宋代隶属、班额变化、军乐职能与别称。")


def entry1204():
    i, main, aliases = 1204, F[1204]["text"], field(1204, "别称")
    w, touched = W(i), set()
    east_west = node(w, touched, i, "殿前东西班", "机构", "南宋",
                     "包括东第三班", main, "殿前诸班班直",
                     "建立东西班南宋承载节点。")
    post = node(w, touched, i, "东第三班", "机构", "南宋",
                "殿前东西班所属禁卫班，又称长入祗候", main,
                "殿前诸班班直", "建立东第三班。", update_event=True)
    relation(w, i, east_west, post, "上下级机构", main,
             "东第三班是殿前东西班所属禁卫班。")
    relation_to_parents(w, touched, i, post, main, time="南宋")
    alias_note(w, i, post, aliases, "别称")
    finish(w, touched, "整理东第三班的东西班所属、殿前司隶属、诸班实例与别称。")


def entry1205():
    i = 1205
    main, origin, duty = F[i]["text"], field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    source = node(w, touched, i, "引龙直", "机构", "北宋太平兴国三年",
                  "始置", origin, "军乐班直前身",
                  "记录引龙直始置。", "职源与沿革", update_event=True)
    target = group_instances(
        w, touched, i, "钧容直第一、二班", "机构", "北宋淳化三年",
        "由引龙直改名，为殿前司军乐队",
        ("钧容直第一班", "钧容直第二班"), origin,
        "淳化三年改称钧容直，正式词头列第一、二班。", "职源与沿革",
    )
    relation(w, i, source, target, "前后演变", origin,
             "引龙直于淳化三年改名钧容直。", "职源与沿革")
    relation_to_parents(w, touched, i, target, origin, time="北宋淳化三年")
    cite(w, "Timepoints", target, i, duty, "保存随驾奏乐与宫廷应奉职掌。", "职掌")
    cite(w, "Timepoints", target, i, roster, "保存乐工及官额编制。", "编制")
    alias_note(w, i, target, aliases, "简称")
    node(w, touched, i, "钧容直第一、二班", "机构",
         "南宋绍兴三十年正月十八日", "罢置", origin, "废罢班直",
         "记录绍兴三十年罢置。", "职源与沿革", update_event=True)
    finish(w, touched, "整理钧容直前身改名、左右班实例、殿前司隶属、职掌编制与罢置。")


def tea_class_entry(i):
    main, title = F[i]["text"], F[i]["title"]
    w, touched = W(i), set()
    north_parent = node(w, touched, i, "殿前东西班", "机构", "北宋",
                        f"包括{title}", main, "殿前诸班班直",
                        "建立东西班北宋承载节点。")
    north = node(w, touched, i, title, "机构", "北宋",
                 "隶殿前东西班，为宫廷侍卫禁旅", main,
                 "殿前诸班班直", f"建立{title}北宋节点。", update_event=True)
    relation(w, i, north_parent, north, "上下级机构", main,
             f"北宋{title}隶殿前东西班。")
    relation_to_parents(w, touched, i, north, main, time="北宋")
    south = node(w, touched, i, title, "机构", "南宋",
                 "从东西班分出单独设置", main, "殿前诸班班直",
                 f"记录南宋{title}独立设置。", update_event=True)
    relation_to_parents(w, touched, i, south, main, time="南宋")
    finish(w, touched, f"整理{title}北宋隶东西班、南宋独立设置及殿前司隶属。")


def entry1206(): tea_class_entry(1206)
def entry1207(): tea_class_entry(1207)


def entry1208():
    i, main = 1208, F[1208]["text"]
    w, touched = W(i), set()
    parent = node(w, touched, i, "殿前东西班", "机构",
                  "北宋景祐三年八月十三日", "辖招箭班", main,
                  "殿前诸班班直", "建立东西班同期节点。")
    post = node(w, touched, i, "招箭班", "机构",
                "北宋景祐三年八月十三日",
                "隶殿前东西班，为皇宫近卫并表演射技", main,
                "殿前诸班班直", "建立招箭班。", update_event=True)
    relation(w, i, parent, post, "上下级机构", main, "招箭班隶殿前东西班。")
    relation_to_parents(w, touched, i, post, main,
                        time="北宋景祐三年八月十三日")
    finish(w, touched, "整理招箭班的东西班所属、殿前司隶属、近卫与射技职能。")


def entry1209():
    i, main = 1209, F[1209]["text"]
    w, touched = W(i), set()
    post = node(w, touched, i, "银枪班", "机构", "南宋",
                "设置，为皇宫近卫", main, "殿前诸班班直",
                "建立银枪班南宋节点。", update_event=True)
    relation_to_parents(w, touched, i, post, main, time="南宋")
    finish(w, touched, "整理银枪班南宋设置、殿前司隶属与诸班实例关系。")


OFFICER_EVENTS = {
    1210: ("诸班都指挥使", "诸班或置，为本班最高长官", "诸班最高长官"),
    1211: ("诸班都虞候", "殿前诸班长官，位次于都指挥使", "诸班长官"),
    1212: ("诸班指挥使", "殿前诸班长官，位次于都虞候", "诸班长官"),
    1213: ("诸班都知", "殿前诸班军官，位次于指挥使、高于副都知", "诸班军官"),
    1214: ("诸班副都知", "殿前诸班军官，位次于都知、高于押班", "诸班军官"),
    1215: ("诸班押班", "殿前诸班军官，位次于副都知", "诸班军官"),
}


def officer_entry(i):
    main = F[i]["text"]
    title, event, staff_type = OFFICER_EVENTS[i]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "殿前诸班", title, "宋代", main,
        f"{title}为殿前诸班军职。", staff_type=staff_type,
        office_event=f"设置{title}", post_event=event,
    )
    finish(w, touched, f"建立{title}的殿前诸班编制隶属、军职性质与位次。")


def entry1210(): officer_entry(1210)
def entry1211(): officer_entry(1211)
def entry1212(): officer_entry(1212)
def entry1213(): officer_entry(1213)
def entry1214(): officer_entry(1214)
def entry1215(): officer_entry(1215)


def entry1216():
    i, main = 1216, F[1216]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "殿前诸班", "殿侍", "宋代", main,
        "殿侍作为侍卫军人隶殿前司东西班等诸班。",
        staff_type="侍卫卫士", office_event="配置殿侍",
        post_event="参班应奉朝殿侍卫祗应，亦为未入流武阶最低等",
    )
    cite(w, "Timepoints", post, i, main, "保存殿侍卫士与武阶双重性质。")
    finish(w, touched, "整理殿侍的诸班隶属、侍卫差役与政和前最低武阶性质。")


def entry1217():
    i, main = 1217, F[1217]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "殿前东西班", "东、西班殿侍院", "宋代", main,
        "东、西班殿侍院为殿前东西班所属殿侍廨舍。",
        parent_event="设置殿侍廨舍", child_event="东、西班所属殿侍廨舍",
    )
    finish(w, touched, "建立东、西班殿侍院的殿前东西班隶属与廨舍性质。")


def entry1218():
    i, main = 1218, F[1218]["text"]
    w, touched = W(i), set()
    parent = node(w, touched, i, "殿前诸班", "机构", "北宋熙宁五年七月",
                  "设置殿侍班", main, "禁军班直统称",
                  "建立殿前诸班同期节点。")
    child = node(w, touched, i, "殿侍班", "机构", "北宋熙宁五年七月",
                 "在朝到班公参应奉祗应殿侍编制，殿侍共一千二百零五人",
                 main, "殿侍编制", "建立殿侍班及兵额。", update_event=True)
    relation(w, i, parent, child, "上下级机构", main,
             "殿侍班是殿前诸班所属殿侍编制。")
    finish(w, touched, "整理殿侍班的诸班所属、在班与差外区分及熙宁兵额。")


def entry1219():
    i, main = 1219, F[1219]["text"]
    w, touched = W(i), set()
    source = node(w, touched, i, "殿侍", "官职", "北宋政和六年三月二日",
                  "非在朝应奉者改称祗应", main, "侍卫卫士旧称",
                  "记录非在朝殿侍改名。", update_event=True)
    target = node(w, touched, i, "祗应", "官职", "北宋政和六年三月二日",
                  "由非在朝应奉殿侍改名", main, "诸班祗应卫士",
                  "建立祗应改名节点。", update_event=True)
    relation(w, i, source, target, "前后演变", main,
             "政和六年非在朝应奉殿侍改称祗应。")
    finish(w, touched, "建立祗应由非在朝殿侍改名的精确时间与前后演变。")


def entry1220():
    i, main = 1220, F[1220]["text"]
    w, touched = W(i), set()
    source = node(w, touched, i, "殿侍", "官职",
                  "北宋政和二年九月二十五日",
                  "武阶殿侍改名下班祗应", main, "未入流武阶旧称",
                  "记录武阶殿侍改名。", update_event=True)
    target = node(w, touched, i, "下班祗应", "官职",
                  "北宋政和二年九月二十五日",
                  "由武阶殿侍改名，为未入流武阶最低等",
                  main, "未入流武阶", "建立下班祗应。", update_event=True)
    relation(w, i, source, target, "前后演变", main,
             "政和二年武阶殿侍改称下班祗应。")
    finish(w, touched, "建立下班祗应由武阶殿侍改名、品级位置与精确时间。")


def main():
    for i in range(1201, 1221):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
