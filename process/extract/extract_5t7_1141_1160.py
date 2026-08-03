#!/usr/bin/env python3
"""提取 chapter5t7 第1141-1160条：大理寺右治狱公吏、大理寺官与审刑院。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1121_1140 as previous


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


F = {i: load(i) for i in range(1141, 1161)}
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
group_instances = previous.previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "北宋淳化二年八月十二日": 991.61,
    "宋前期": 1050,
    "北宋元丰五年以后": 1082.5,
    "北宋元丰三年": 1080,
    "宋代（大理寺，具体年月未载）": 1100,
    "宋代（右治狱厅，具体年月未载）": 1100.1,
    "宋代（左右二推，具体年月未载）": 1100.2,
    "南宋（乾道四年前，具体年月未载）": 1160,
    "南宋乾道四年五月二日": 1168.35,
    "南宋乾道四年五月二日以后": 1168.36,
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


def dali_clerk_entry(i, event, staff_type="大理寺公吏"):
    main = F[i]["text"]
    title = F[i]["title"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "大理寺", title, "宋代（大理寺，具体年月未载）",
        main, f"{title}是大理寺所属公吏。", staff_type=staff_type,
        office_event="设置大理寺公吏", post_event=event,
    )
    return w, touched, post


def two_push_servant_entry(i, event, staff_type="二推祇应公人"):
    main = F[i]["text"]
    title = F[i]["title"]
    w, touched = W(i), set()
    for office in ("大理寺左推", "大理寺右推"):
        office_staff(
            w, touched, i, office, title, "宋代（左右二推，具体年月未载）",
            main, f"{title}隶大理寺右治狱左、右推。", staff_type=staff_type,
            office_event="配置二推祇应公人", post_event=event,
        )
    finish(w, touched, f"建立{title}在大理寺左推、右推的双重隶属及祇应性质。")


def entry1141():
    i, main = 1141, F[1141]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "大理寺右治狱厅", "捉事使臣",
        "宋代（右治狱厅，具体年月未载）", main,
        "捉事使臣隶大理寺右治狱，由武臣使臣差充。",
        staff_type="追捕使臣", office_event="设置捉事使臣",
        post_event="由武臣使臣差充，追捕抓人", officer="武臣使臣",
    )
    finish(w, touched, "整理捉事使臣右治狱厅隶属、武臣差充及追捕职掌。")


def entry1142():
    i, main = 1142, F[1142]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, active, _ = office_staff(
        w, touched, i, "大理寺右治狱厅", "右治狱都辖使臣",
        "南宋（乾道四年前，具体年月未载）", main,
        "右治狱都辖使臣由武臣小使臣充，通管左右推推司。", quota=1,
        staff_type="二推都辖", office_event="置都辖使臣一人",
        post_event="由武臣小使臣充，通管左、右推推司",
        officer="武臣小使臣",
    )
    node(w, touched, i, "右治狱都辖使臣", "官职",
         "南宋乾道四年五月二日", "罢置", main, "废罢差遣",
         "记录乾道四年罢都辖使臣。", update_event=True)
    alias_note(w, i, active, aliases, "简称")
    finish(w, touched, "整理右治狱都辖使臣差充资格、二推管辖、员额、简称及乾道罢置。")


def entry1143():
    i, main = 1143, F[1143]["text"]
    aliases = field(i, "别称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "推司", "官职",
        "宋代（右治狱厅，具体年月未载）",
        "右治狱左、右推狱吏，分承勘推司与般押推司",
        ("承勘推司", "般押推司"), main,
        "原文明确推司分为承勘推司与般押推司。",
    )
    for office in ("大理寺左推", "大理寺右推"):
        office_staff(
            w, touched, i, office, "推司",
            "宋代（右治狱厅，具体年月未载）", main,
            "推司是右治狱左、右推狱吏。", staff_type="分推狱吏",
            office_event="设置推司", post_event="分承勘推司与般押推司",
        )
    alias_note(w, i, group, aliases, "别称")
    finish(w, touched, "建立推司总称、承勘与般押两个实例、左右二推隶属及推吏别称。")


def entry1144():
    i, main = 1144, F[1144]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "大理寺右治狱厅", "承勘推司",
        "宋代（右治狱厅，具体年月未载）", main,
        "承勘推司隶右治狱，承办重案密案。", staff_type="推司狱吏",
        office_event="设置承勘推司",
        post_event="承办情节严重或事关机密狱案，三年可出职补副尉",
    )
    node(w, touched, i, "承勘推司", "官职",
         "宋代（右治狱厅，具体年月未载）",
         "承办情节严重或事关机密狱案，三年可出职补副尉",
         main, "推司狱吏", "用正式词条职掌更新承勘推司实例节点。",
         update_event=True)
    assert post
    finish(w, touched, "整理承勘推司右治狱隶属、重案密案职掌、请给待遇及三年出职。")


def entry1145():
    i, main = 1145, F[1145]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "大理寺右治狱厅", "般押推司",
        "宋代（右治狱厅，具体年月未载）", main,
        "般押推司隶右治狱，抄写递送狱案文书。", staff_type="推司狱吏",
        office_event="设置般押推司",
        post_event="抄写狱案文字并递送案款给有关理官签押",
    )
    node(w, touched, i, "般押推司", "官职",
         "宋代（右治狱厅，具体年月未载）",
         "抄写狱案文字并递送案款给有关理官签押",
         main, "推司狱吏", "用正式词条职掌更新般押推司实例节点。",
         update_event=True)
    finish(w, touched, "整理般押推司右治狱隶属及抄写递送狱案文书职掌。")


def entry1146():
    i, main = 1146, F[1146]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, active, _ = office_staff(
        w, touched, i, "大理寺左推", "大理寺左推职级",
        "宋代（右治狱厅，具体年月未载）", main,
        "左推职级由武臣使臣充，总管左推推司。", quota=1,
        staff_type="分推职级", office_event="设置左推职级",
        post_event="由武臣使臣充，总管左推推司，由都辖递迁",
        officer="武臣使臣",
    )
    node(w, touched, i, "大理寺左推职级", "官职",
         "南宋乾道四年五月二日以后",
         "都辖使臣罢后，改由胥佐试补", main, "分推职级",
         "记录乾道四年以后左推职级补授来源变化。", update_event=True)
    alias_note(w, i, active, aliases, "简称")
    finish(w, touched, "整理大理寺左推职级的分推隶属、武臣差充、总管职掌、都辖递迁及乾道后试补。")


def entry1147():
    i, main = 1147, F[1147]["text"]
    aliases = field(i, "简称")
    assert "胥长" not in aliases
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "大理寺右推", "大理寺右推职级",
        "宋代（右治狱厅，具体年月未载）", main,
        "右推职级由武臣使臣充，总管右推推司。", quota=1,
        staff_type="分推职级", office_event="设置右推职级",
        post_event="由武臣使臣充，总管右推推司", officer="武臣使臣",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理大理寺右推职级的分推隶属、武臣差充、总管职掌与简称。")


def entry1148():
    assert F[1148]["title"] == "胥长" and F[1148]["text"]
    w, touched, _ = dali_clerk_entry(
        1148, "文职吏人中名次最高，掌管文字，缺由胥史试补",
    )
    finish(w, touched, "恢复胥长正式词条并建立大理寺隶属、吏职位次、掌管文字及试补来源。")


def entry1149():
    w, touched, _ = dali_clerk_entry(1149, "系书点检文字")
    finish(w, touched, "建立胥史的大理寺隶属与系书点检文字职掌。")


def entry1150():
    w, touched, _ = dali_clerk_entry(1150, "行遣文案，缺由正贴书试补")
    finish(w, touched, "建立胥佐的大理寺隶属、行遣文案职掌及正贴书试补来源。")


def entry1151():
    i = 1151
    aliases = field(i, "别称")
    w, touched, post = dali_clerk_entry(1151, "抄写文案，缺由守阙贴书试补")
    alias_note(w, i, post, aliases, "别称")
    finish(w, touched, "建立贴书的大理寺隶属、抄写职掌、守阙贴书试补及正贴书别称。")


def entry1152():
    w, touched, _ = dali_clerk_entry(
        1152, "非正式编制贴书，无请给但有食钱补贴",
        staff_type="非正式编制公吏",
    )
    finish(w, touched, "建立守阙贴书的大理寺隶属、非正式编制性质与待遇。")


def entry1153():
    w, touched, _ = dali_clerk_entry(1153, "抄写、誊录文案")
    finish(w, touched, "建立楷书的大理寺隶属与抄写誊录职掌。")


def entry1154():
    i, main = 1154, F[1154]["text"]
    w, touched = W(i), set()
    for office in ("大理寺左断刑厅", "大理寺右治狱厅"):
        office_staff(
            w, touched, i, office, "法司", "宋代（大理寺，具体年月未载）",
            main, "左断刑、右治狱均置法司吏。", staff_type="法司吏",
            office_event="设置法司吏",
            post_event="供断案、勘鞫所需条例",
        )
    finish(w, touched, "建立法司吏在左断刑、右治狱的双重编制隶属及供给条例职掌。")


def entry1155():
    two_push_servant_entry(1155, "祇应右治狱左、右推事务")


def entry1156():
    two_push_servant_entry(1156, "女公人，祇应右治狱左、右推事务", "二推祇应女公人")


def entry1157():
    two_push_servant_entry(1157, "祇应右治狱左、右推医务", "二推祇应医人")


EARLY_DALI_OFFICIALS = (
    "判大理寺事", "大理寺详断官", "大理寺法直官", "大理寺检法官",
)
REFORM_DALI_OFFICIALS = (
    "大理寺卿", "大理寺少卿", "大理寺正", "大理寺丞",
    "大理寺司直", "大理寺评事", "大理寺主簿",
)


def entry1158():
    i, main = 1158, F[1158]["text"]
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "大理寺官", "官职", "宋前期",
        "判大理寺事、详断官、法直官、检法官等职事官总称",
        EARLY_DALI_OFFICIALS, main,
        "原文明确列出宋前期大理寺职事官范围。",
    )
    reform = group_instances(
        w, touched, i, "大理寺官", "官职", "北宋元丰五年以后",
        "大理寺卿、少卿、正、丞、司直、评事、主簿等职事官总称",
        REFORM_DALI_OFFICIALS, main,
        "原文明确列出元丰改制后大理寺职事官范围。",
    )
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "建立大理寺官统称、元丰前后两组正式实例及简称别名。")


def entry1159():
    i, main = 1159, F[1159]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    founded = node(
        w, touched, i, "审刑院", "机构", "北宋淳化二年八月十二日",
        "始置，逐一收理上奏案件并评议大理寺判决、刑部覆审结果",
        origin, "中央司法机构", "记录审刑院始置。", "职源",
        update_event=True,
    )
    cite(w, "Timepoints", founded, i, main,
         "补证审刑院与大理寺、刑部同为北宋前期中央司法机构。")
    cite(w, "Timepoints", founded, i, duty,
         "保存审刑院收案、转大理寺判决、刑部覆审及再评议进奏流程。", "职掌")
    office_staff(
        w, touched, i, "审刑院", "知审刑院事", "北宋淳化二年八月十二日",
        roster, "知审刑院事一人或二人。", "编制", quota="1-2",
        staff_type="审刑院长官", office_event="置知审刑院事一人或二人",
        post_event="领审刑院事，审定详议结果",
    )
    office_staff(
        w, touched, i, "审刑院", "审刑院详议官", "北宋淳化二年八月十二日",
        roster, "审刑院详议官六人。", "编制", quota=6,
        staff_type="审刑院详议官", office_event="置详议官六人",
        post_event="详议大理寺断案与刑部覆审结果",
    )
    office_staff(
        w, touched, i, "审刑院", "令史", "北宋淳化二年八月十二日",
        roster, "审刑院令史十二人。", "编制", quota=12,
        staff_type="审刑院公吏", office_event="置令史十二人",
        post_event="承办审刑院文书事务",
    )
    alias_note(w, i, founded, aliases, "简称")
    finish(w, touched, "整理审刑院淳化始置、中央司法流程、知院详议官令史编制及简称。")


def entry1160():
    i, main = 1160, F[1160]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "官品")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    post = node(
        w, touched, i, "知审刑院事", "官职", "北宋淳化二年八月十二日",
        "由朝官以上差充，领审刑院事并与详议官评议奏裁",
        origin, "审刑院长官", "记录知审刑院事始置。", "职源",
        officer="朝官以上", update_event=True,
    )
    cite(w, "Timepoints", post, i, main, "补证本条为北宋前期差遣官。")
    cite(w, "Timepoints", post, i, duty, "保存知院事领院及评议奏裁职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存朝官以上差充及随带官定品规则。", "官品")
    source = node(
        w, touched, i, "审刑院", "机构", "北宋元丰三年",
        "罢归刑部", origin, "机构省并", "记录审刑院元丰三年罢归刑部。",
        "职源", update_event=True,
    )
    target = node(
        w, touched, i, "刑部", "机构", "北宋元丰三年",
        "接收审刑院职事", origin, "接收机构",
        "记录刑部接收审刑院职事。", "职源", update_event=True,
    )
    relation(w, i, source, target, "前后演变", origin,
             "元丰三年审刑院罢，其职事归刑部。", "职源")
    node(w, touched, i, "知审刑院事", "官职", "北宋元丰三年",
         "随审刑院罢归刑部而罢置", origin, "废罢差遣",
         "记录知审刑院事元丰三年罢置。", "职源", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理知审刑院事淳化始置、差充资格、评议奏裁职掌、简称及元丰罢归刑部。")


def main():
    for i in range(1141, 1161):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
