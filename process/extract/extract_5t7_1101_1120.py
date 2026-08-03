#!/usr/bin/env python3
"""提取 chapter5t7 第1101-1120条：大理寺卿、少卿、寺正、寺丞及左断刑厅。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1081_1100 as previous


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


F = {i: load(i) for i in range(1101, 1121)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
parent_child = previous.parent_child
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "春秋晋文公时": -650,
    "秦代": -220,
    "西汉景帝中元六年": -144,
    "西汉宣帝地节三年": -68,
    "晋武帝咸宁中": 277,
    "北魏永安二年": 529,
    "北齐": 550,
    "隋代": 600,
    "宋初": 960,
    "北宋咸平二年": 999,
    "宋前期": 1050,
    "宋初（后增员，具体年月未载）": 980,
    "宋前期（大理寺，具体年月未载）": 1070,
    "北宋元丰元年十二月十八日": 1078.96,
    "北宋元丰二年": 1079,
    "北宋元丰二年至元丰五年四月": 1080,
    "北宋元丰五年四月": 1082.28,
    "北宋元丰五年": 1082.4,
    "南宋建炎三年四月": 1129.29,
    "南宋绍兴初": 1131,
    "南宋绍兴三十一年": 1161,
    "南宋隆兴二年以后": 1164,
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


def entry1101():
    i, main = 1101, F[1101]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, start, _ = office_staff(
        w, touched, i, "大理寺", "知大理寺卿事",
        "北宋元丰元年十二月十八日", main,
        "元丰元年置大理寺狱时置知卿事一人。", quota=1,
        staff_type="大理寺主管差遣",
        office_event="置卿一人，以朝官差充知卿事",
        post_event="由朝官差充，领大理寺事",
    )
    node(w, touched, i, "知大理寺卿事", "官职", "北宋元丰五年",
         "行新官制后罢置", main, "废罢差遣",
         "记录知大理寺卿事元丰五年罢置。", update_event=True)
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理知大理寺卿事元丰始置、员额、隶属、职掌、简称与罢置。")


def entry1102():
    i = 1102
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "大理寺卿", "官职", "春秋晋文公时",
         "已有大理官，掌察理刑狱", origin, "前代官职源流",
         "记录大理卿名称职掌的春秋源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "大理寺卿", "官职", "西汉景帝中元六年",
         "廷尉改称大理，为九卿之一", origin, "前代官职源流",
         "记录西汉大理源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "大理寺卿", "官职", "北齐",
         "大理寺卿官名始置", origin, "前代官职源流",
         "记录大理寺卿官名始置。", "职源与沿革", update_event=True)
    node(w, touched, i, "大理寺卿", "官职", "宋前期", "不置",
         origin, "未置职事官", "记录北宋前期不置。", "职源与沿革",
         update_event=True)
    node(w, touched, i, "大理寺卿", "官职", "北宋元丰二年",
         "虽置卿但不除人，以知大理寺卿事代领", origin, "职事官",
         "记录元丰二年名置而未命官。", "职源与沿革", update_event=True)
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺卿", "北宋元丰五年", roster,
        "元丰五年始正式命官，定员一人。", "编制", quota=1,
        staff_type="大理寺长官", office_event="置大理寺卿一人",
        post_event="始正式命官，总掌左断刑、右治狱",
        grade="从四品",
    )
    cite(w, "Timepoints", reform, i, origin, "补证元丰五年始正式命官。", "职源与沿革")
    cite(w, "Timepoints", reform, i, duty, "保存大理寺卿总掌左右两厅职掌。", "职掌")
    cite(w, "Timepoints", reform, i, rank, "保存元丰新制品位及后续品位证据。", "品位")
    node(w, touched, i, "大理寺卿", "官职", "南宋建炎三年四月",
         "并省寺监时省罢", roster, "省罢职事官",
         "记录建炎三年省卿。", "编制", update_event=True)
    _, restored, _ = office_staff(
        w, touched, i, "大理寺", "大理寺卿", "南宋绍兴初", roster,
        "绍兴初复置大理寺卿一人。", "编制", quota=1,
        staff_type="大理寺长官", office_event="复置大理寺卿",
        post_event="复置，总掌左断刑、右治狱", grade="从四品",
    )
    alias_note(w, i, restored, aliases, "简称与别名")
    finish(w, touched, "整理大理寺卿前代源流、北宋不置、元丰名置与实授、南宋省复、职掌品位编制及别名。")


def entry1103():
    i = 1103
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "大理寺少卿", "官职", "北齐",
         "大理寺少卿始置", origin, "前代官职源流",
         "记录北齐始置。", "职源与沿革", update_event=True)
    _, early, _ = office_staff(
        w, touched, i, "大理寺", "大理寺少卿", "宋前期", roster,
        "宋前期限朝官一员兼权大理少卿。", "编制", quota=1,
        staff_type="大理寺副长官", office_event="置兼权少卿一人",
        post_event="兼权，与判寺事官同掌疑狱冤案", officer="朝官",
    )
    cite(w, "Timepoints", early, i, duty, "保存宋前期少卿职掌。", "职掌")
    cite(w, "Timepoints", early, i, rank, "保存宋前期兼权性质与品位。", "品位")
    node(w, touched, i, "大理寺少卿", "官职", "北宋元丰元年十二月十八日",
         "置大理寺狱后管右治狱", duty, "大理寺副长官",
         "记录元丰元年管右治狱。", "职掌", update_event=True)
    node(w, touched, i, "大理寺少卿", "官职", "北宋元丰二年至元丰五年四月",
         "右治狱少卿一员", roster, "大理寺副长官",
         "记录元丰二年至五年的单员右治狱编制。", "编制",
         grade="正六品", update_event=True)
    reform = node(
        w, touched, i, "大理寺少卿", "官职", "北宋元丰五年四月",
        "分为左断刑少卿一人、右治狱少卿一人", roster,
        "大理寺副长官", "记录元丰新制左右分职。", "编制",
        grade="正六品", update_event=True,
    )
    cite(w, "Timepoints", reform, i, duty, "补证元丰五年分治左右两厅。", "职掌")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理大理寺少卿北齐源流、宋前期兼权、元丰管右治狱及左右分职。")


def entry1104():
    i, main = 1104, F[1104]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, early, _ = office_staff(
        w, touched, i, "大理寺", "大理寺治狱少卿",
        "北宋元丰二年至元丰五年四月", main,
        "右治狱少卿一员，专掌推治刑狱。", quota=1,
        staff_type="右治狱副长官", office_event="置右治狱少卿一员",
        post_event="分领右治狱，掌推治刑狱",
    )
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺治狱少卿",
        "北宋元丰五年四月", aliases,
        "元丰新制右治狱少卿一人。", "简称", quota=1,
        staff_type="右治狱副长官", office_event="左右分厅后置治狱少卿一员",
        post_event="分领右治狱，掌推治刑狱",
    )
    alias_note(w, i, reform, aliases, "简称")
    assert early
    finish(w, touched, "整理大理寺治狱少卿的右治狱分职、员额、隶属、职掌与简称。")


def entry1105():
    i, main = 1105, F[1105]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "大理寺", "大理寺断刑少卿",
        "北宋元丰五年四月", main,
        "元丰新制断刑少卿一人，分领左断刑。", quota=1,
        staff_type="左断刑副长官", office_event="左右分厅后置断刑少卿一员",
        post_event="分领左断刑，掌决断诸路狱案",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理大理寺断刑少卿的左断刑分职、员额、隶属、职掌与简称。")


def entry1106():
    i, main = 1106, F[1106]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "大理寺正", "官职", "秦代", "已有廷尉正",
         origin, "前代官职源流", "记录廷尉正源流。", "职源与沿革",
         update_event=True)
    node(w, touched, i, "大理寺正", "官职", "北齐",
         "大理寺正官名始置", origin, "前代官职源流",
         "记录北齐始置。", "职源与沿革", update_event=True)
    _, early, _ = office_staff(
        w, touched, i, "大理寺", "大理寺正", "宋初", duty,
        "宋初以朝官兼大理正为详断官。", staff_type="兼详断官",
        office_event="以朝官兼大理正", post_event="兼详断官，掌议断刑",
        officer="朝官",
    )
    cite(w, "Timepoints", early, i, rank, "保存宋初品位。", "品位")
    node(w, touched, i, "大理寺正", "官职", "北宋咸平二年",
         "省去兼正之名", origin, "旧名省罢",
         "记录咸平二年省去兼正名。", "职源与沿革", update_event=True)
    _, restored, _ = office_staff(
        w, touched, i, "大理寺", "大理寺正", "北宋元丰二年", roster,
        "复置大理寺正一人。", "编制", quota=1, staff_type="左断刑审定官",
        office_event="复置大理寺正一人", post_event="复置，审定议断案件",
        grade="从七品",
    )
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺正", "北宋元丰五年", roster,
        "元丰五年改制后定员二人。", "编制", quota=2,
        staff_type="左断刑审定官", office_event="置大理寺正二人",
        post_event="隶左断刑，审定司直、评事、丞议断案件",
        grade="从七品",
    )
    cite(w, "Timepoints", reform, i, duty, "保存元丰以后及南宋职掌。", "职掌")
    cite(w, "Timepoints", reform, i, main, "补证大理寺正隶左断刑。")
    alias_note(w, i, reform, aliases, "简称")
    assert restored
    finish(w, touched, "合并跨页正文后整理大理寺正前代源流、宋初兼详断、咸平省名、元丰复置及左断刑职掌编制。")


def entry1107():
    assert F[1107]["text"] == ""
    assert F[1107]["fields"].get("__status__") == "placeholder"


def entry1108():
    i, main = 1108, F[1108]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "大理寺", "判大理正事", "宋初", main,
        "判大理正事由朝官兼充，掌参议断刑。",
        staff_type="兼详断官", office_event="设置判大理正事",
        post_event="由朝官兼充，掌参议断刑", officer="朝官",
    )
    finish(w, touched, "整理判大理正事的宋初设置、朝官兼充、大理寺隶属与参议断刑职掌。")


def entry1109():
    i = 1109
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "大理寺丞", "官职", "晋武帝咸宁中",
         "始置廷尉丞", origin, "前代官职源流",
         "记录廷尉丞源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "大理寺丞", "官职", "北齐",
         "大理寺丞始置", origin, "前代官职源流",
         "记录北齐始置。", "职源与沿革", update_event=True)
    _, early, _ = office_staff(
        w, touched, i, "大理寺", "大理寺丞", "宋初", duty,
        "宋初由京官兼充大理寺丞，称详断官。", staff_type="兼详断官",
        office_event="以京官兼大理寺丞", post_event="兼详断官，参议断刑",
        officer="京官",
    )
    cite(w, "Timepoints", early, i, rank, "保存宋初品位。", "品位")
    node(w, touched, i, "大理寺丞", "官职", "北宋咸平二年",
         "罢兼丞之名，径称详断官", duty, "旧名省罢",
         "记录咸平二年罢兼丞名。", "职掌", update_event=True)
    node(w, touched, i, "大理寺丞", "官职", "宋前期",
         "无职事，为文臣迁转官阶", duty, "阶官",
         "记录宋前期无职事阶官性质。", "职掌", update_event=True)
    _, restored, _ = office_staff(
        w, touched, i, "大理寺", "大理寺丞", "北宋元丰元年十二月十八日",
        duty, "大理寺丞始单除授二员，专推治本寺狱。", "职掌", quota=2,
        staff_type="治狱职事官", office_event="始单除大理寺丞二员",
        post_event="始单除授，专推治本寺狱",
    )
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺丞", "北宋元丰五年", roster,
        "寺丞分治狱四人、断刑六人，共十人。", "编制", quota=10,
        staff_type="治狱与断刑职事官", office_event="置寺丞十人，分治狱与断刑",
        post_event="分为治狱寺丞四人、断刑寺丞六人", grade="正八品",
    )
    cite(w, "Timepoints", reform, i, duty, "保存元丰后治狱与断刑寺丞职掌。", "职掌")
    cite(w, "Timepoints", reform, i, rank, "保存元丰后品位与班次。", "品位")
    alias_note(w, i, reform, aliases, "简称与别名")
    assert restored
    finish(w, touched, "整理大理寺丞前代源流、宋初兼详断、咸平省名、宋前期阶官、元丰单除及分职编制。")


def entry1110():
    i, main = 1110, F[1110]["text"]
    aliases = field(i, "简称与别名")
    assert main.startswith("大理寺丞分隶右治狱者")
    w, touched = W(i), set()
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺右治狱丞", "北宋元丰五年",
        main, "元丰新制右治狱丞四人，专掌推鞫。", quota=4,
        staff_type="右治狱推丞", office_event="置右治狱丞四人",
        post_event="分隶右治狱，专掌审讯推鞫",
    )
    office_staff(
        w, touched, i, "大理寺", "大理寺右治狱丞", "南宋建炎三年四月",
        aliases, "建炎三年治狱寺丞减为二员。", "简称与别名", quota=2,
        staff_type="右治狱推丞", office_event="治狱寺丞减为二员",
        post_event="治狱寺丞减为二员，仍专掌推鞫",
    )
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理大理寺右治狱丞元丰与建炎员额、右治狱分隶、推鞫职掌及别名。")


def entry1111():
    i, main = 1111, F[1111]["text"]
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺左断刑丞", "北宋元丰五年",
        main, "元丰新制左断刑丞六人，复议司直、评事所断奏案。", quota=6,
        staff_type="左断刑断丞", office_event="置左断刑丞六人",
        post_event="分隶左断刑，复议司直、评事所断奏案",
    )
    office_staff(
        w, touched, i, "大理寺", "大理寺左断刑丞", "南宋建炎三年四月",
        aliases, "建炎三年断刑寺丞减为三员。", "简称与别名", quota=3,
        staff_type="左断刑断丞", office_event="断刑寺丞减为三员",
        post_event="断刑寺丞减为三员，仍复议奏案",
    )
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理大理寺左断刑丞元丰与建炎员额、左断刑分隶、复议职掌及别名。")


def entry1112():
    i = 1112
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "大理寺司直", "官职", "北魏永安二年",
         "廷尉置司直", origin, "前代官职源流",
         "记录北魏司直源流。", "职源", update_event=True)
    node(w, touched, i, "大理寺司直", "官职", "北齐",
         "大理寺司直始置", origin, "前代官职源流",
         "记录北齐始置。", "职源", update_event=True)
    _, start, _ = office_staff(
        w, touched, i, "大理寺", "大理寺司直", "北宋元丰二年", roster,
        "初置大理寺狱后置司直一人。", "编制", quota=1,
        staff_type="断刑详断官", office_event="置大理司直一人",
        post_event="与评事按法议出刑案初判", grade="正八品",
    )
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺司直", "北宋元丰五年", roster,
        "元丰新制左断刑置大理司直六人。", "编制", quota=6,
        staff_type="左断刑详断官", office_event="左断刑置司直六人",
        post_event="隶左断刑，与评事按法议出初判", grade="正八品",
    )
    _, extra, _ = office_staff(
        w, touched, i, "大理寺", "大理寺司直", "北宋绍圣二年", roster,
        "绍圣二年右治狱另置司直一人。", "编制", quota=1,
        staff_type="右治狱纠察官", office_event="右治狱另置司直一人",
        post_event="兼纠察右治狱稽违、赃罚事", grade="正八品",
    )
    cite(w, "Timepoints", reform, i, duty, "保存司直议刑初判职掌。", "职掌")
    cite(w, "Timepoints", extra, i, duty, "保存司直兼纠察右治狱职掌。", "职掌")
    cite(w, "Timepoints", start, i, rank, "保存司直品位与班次。", "品位")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理大理寺司直前代源流、元丰与绍圣左右分职员额、职掌品位及别名。")


def entry1113():
    i = 1113
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "大理寺评事", "官职", "西汉宣帝地节三年",
         "廷尉下置左、右评", origin, "前代官职源流",
         "记录廷尉评源流。", "职源", update_event=True)
    node(w, touched, i, "大理寺评事", "官职", "隋代",
         "始置大理寺评事", origin, "前代官职源流",
         "记录隋代始置。", "职源", update_event=True)
    node(w, touched, i, "大理寺评事", "官职", "宋前期",
         "无职事，为文臣迁转官阶", duty, "阶官",
         "记录宋前期阶官性质。", "职掌", update_event=True)
    _, start, _ = office_staff(
        w, touched, i, "大理寺", "大理寺评事", "北宋元丰二年", roster,
        "元丰二年大理寺评事八员。", "编制", quota=8,
        staff_type="左断刑详断官", office_event="置评事八员",
        post_event="由阶官转为职事官，依法议出刑案初判", grade="正八品",
    )
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺评事", "北宋元丰五年", roster,
        "元丰五年依唐六典定评事十二员。", "编制", quota=12,
        staff_type="左断刑详断官", office_event="置评事十二员",
        post_event="隶左断刑，与司直依法议出初判", grade="正八品",
    )
    office_staff(
        w, touched, i, "大理寺", "大理寺评事", "南宋绍兴三十一年", roster,
        "绍兴三十一年评事减为五员。", "编制", quota=5,
        staff_type="左断刑详断官", office_event="评事减为五员",
        post_event="隶左断刑，评事五员", grade="正八品",
    )
    _, eight, _ = office_staff(
        w, touched, i, "大理寺", "大理寺评事", "南宋隆兴二年以后", roster,
        "隆兴二年以后评事定为八员，各以一字为号。", "编制", quota=8,
        staff_type="左断刑详断官", office_event="评事定为八员",
        post_event="八员分别以雷、霆、号、令、星、斗、文、章为号",
        grade="正八品",
    )
    cite(w, "Timepoints", reform, i, duty, "保存评事左断刑详断职掌。", "职掌")
    cite(w, "Timepoints", start, i, rank, "保存评事品位与班次。", "品位")
    alias_note(w, i, eight, aliases, "简称与别名")
    finish(w, touched, "整理大理寺评事前代源流、宋前期阶官、元丰至隆兴员额变化、职掌品位及别名。")


def entry1114():
    i, main = 1114, F[1114]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "八评事", "官职", "南宋隆兴二年以后",
        "大理寺八员评事的合称，分别以雷、霆、号、令、星、斗、文、章为号",
        ("大理寺评事",), main,
        "八评事是隆兴二年以后定额八员的大理寺评事之称。",
    )
    finish(w, touched, "建立八评事统称及其所指大理寺评事实例与隆兴以后时间。")


def entry1115():
    i = 1115
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "大理寺主簿", "官职", "晋代",
         "已有廷尉主簿，为大理寺主簿前身", origin, "前代官职源流",
         "记录廷尉主簿源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "大理寺主簿", "官职", "北齐",
         "大理寺主簿始置", origin, "前代官职源流",
         "记录北齐始置。", "职源与沿革", update_event=True)
    _, reform, _ = office_staff(
        w, touched, i, "大理寺", "大理寺主簿", "北宋元丰五年", roster,
        "元丰官制定大理寺主簿二员。", "编制", quota=2,
        staff_type="大理寺属官", office_event="置主簿二员",
        post_event="勾稽本寺簿书，主管左断刑架阁库", grade="从八品",
    )
    cite(w, "Timepoints", reform, i, duty, "保存主簿职掌。", "职掌")
    cite(w, "Timepoints", reform, i, rank, "保存主簿品位与差充资格。", "品位")
    node(w, touched, i, "大理寺主簿", "官职", "南宋建炎三年四月",
         "罢置", roster, "省罢职事官", "记录建炎三年罢置。", "编制",
         update_event=True)
    _, restored, _ = office_staff(
        w, touched, i, "大理寺", "大理寺主簿", "南宋绍兴初", roster,
        "建炎罢后复置。", "编制", quota=2, staff_type="大理寺属官",
        office_event="复置主簿", post_event="复置，勾稽簿书并主管左断刑架阁库",
        grade="从八品",
    )
    alias_note(w, i, restored, aliases, "简称与别名")
    finish(w, touched, "整理大理寺主簿前代源流、元丰编制职掌、建炎罢置与后复及别名。")


def entry1116():
    i, main = 1116, F[1116]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, early, _ = office_staff(
        w, touched, i, "大理寺", "大理寺详断官", "宋初", main,
        "宋初详断官始定六员。", quota=6, staff_type="奏狱详断官",
        office_event="置详断官六员", post_event="评议、决断天下奏狱",
    )
    office_staff(
        w, touched, i, "大理寺", "大理寺详断官",
        "宋初（后增员，具体年月未载）", main,
        "详断官后增至十一员。", quota=11, staff_type="奏狱详断官",
        office_event="详断官增至十一员", post_event="评议、决断天下奏狱",
    )
    _, fixed, _ = office_staff(
        w, touched, i, "大理寺", "大理寺详断官", "北宋咸平二年", main,
        "咸平二年八月详断官定额八人。", quota=8,
        staff_type="奏狱详断官", office_event="详断官定额八人",
        post_event="去兼正、丞之名，评议决断奏狱",
    )
    node(w, touched, i, "大理寺详断官", "官职",
         "北宋元丰元年十二月十八日", "罢置", main, "废罢差遣",
         "记录元丰元年罢详断官。", update_event=True)
    alias_note(w, i, fixed, aliases, "简称")
    assert early
    finish(w, touched, "整理大理寺详断官宋初六员、后增十一员、咸平定八员及元丰罢置。")


def entry1117():
    i, main = 1117, F[1117]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "大理寺", "大理寺检法官", "宋前期", main,
        "宋前期以选人改京官后差充检法官，参与详断奏狱。",
        staff_type="奏狱检法官", office_event="设置检法官",
        post_event="由选人改京官后差充，参与详断奏狱",
        officer="选人改京官后",
    )
    office_staff(
        w, touched, i, "大理寺", "大理寺检法官",
        "北宋元丰元年十二月十八日", aliases,
        "元丰元年十二月检法官二人。", "简称", quota=2,
        staff_type="奏狱检法官", office_event="检法官二人",
        post_event="参与详断奏狱", officer="选人改京官后",
    )
    node(w, touched, i, "大理寺检法官", "官职", "北宋元丰五年",
         "行新制罢置", main, "废罢差遣",
         "记录元丰五年罢检法官。", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理大理寺检法官宋前期阶官来源、详断职掌、元丰元年员额及五年罢置。")


def entry1118():
    i, main = 1118, F[1118]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "大理寺", "大理寺法直官", "宋前期", main,
        "宋前期以幕职州县官差充法直官，详断天下奏狱。", quota=2,
        staff_type="奏狱法直官", office_event="设置法直官二人",
        post_event="由幕职州县官差充，详断天下奏狱",
        officer="幕职州县官（选人）",
    )
    node(w, touched, i, "大理寺法直官", "官职", "北宋元丰五年",
         "行新制罢置", main, "废罢差遣",
         "记录元丰五年罢法直官。", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理大理寺法直官宋前期选人差充、详断职掌、员额及元丰五年罢置。")


def entry1119():
    i, main = 1119, F[1119]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "大理寺", "府史", "宋前期（大理寺，具体年月未载）",
        main, "府史是宋前期大理寺沿用隋唐九寺五监制度的吏人。",
        staff_type="大理寺吏人", office_event="设置府史",
        post_event="承办大理寺事务，职事近于台省主事、令史",
    )
    finish(w, touched, "在通用府史实体上建立大理寺语境时点、编制隶属与吏职性质。")


def entry1120():
    i, main = 1120, F[1120]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, hall = parent_child(
        w, touched, i, "大理寺", "大理寺左断刑厅", "北宋元丰五年",
        main, "元丰五年大理寺分左、右二厅，左厅主详断刑狱奏牍。",
        parent_event="分设左断刑、右治狱二厅",
        child_event="始置，主详断刑狱奏牍",
    )
    roster = main
    for title, quota, staff_type, event in (
        ("大理寺断刑少卿", 1, "左断刑副长官", "分领左断刑"),
        ("大理寺正", 2, "左断刑审定官", "审定议断案件"),
        ("大理寺左断刑丞", 6, "左断刑断丞", "复议司直、评事所断案件"),
        ("大理寺司直", 6, "左断刑详断官", "与评事按法详断"),
        ("大理寺评事", 12, "左断刑详断官", "与司直按法详断"),
    ):
        office_staff(
            w, touched, i, "大理寺左断刑厅", title, "北宋元丰五年",
            roster, f"{title}隶左断刑厅，员额{quota}人。", quota=quota,
            staff_type=staff_type, office_event="配置左断刑官属",
            post_event=event,
        )
    office_staff(
        w, touched, i, "大理寺左断刑厅", "大理寺卿", "北宋元丰五年",
        roster, "大理寺卿总领左断刑厅。", staff_type="总领长官",
        office_event="由大理寺卿总领", post_event="总领左断刑、右治狱",
    )
    alias_note(w, i, hall, aliases, "简称")
    finish(w, touched, "建立大理寺左断刑厅元丰五年始置、上级机构、六类官属编制与简称；案司留待后续正式词条。")


def main():
    for i in range(1101, 1121):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
