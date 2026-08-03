#!/usr/bin/env python3
"""提取 chapter5t7 第1001-1020条：都水监治河属司与御史台前半。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_981_1000 as previous


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


F = {i: load(i) for i in range(1001, 1021)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
relation = base.relation
staff = base.staff
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
parent_child = previous.parent_child
evolution = previous.evolution
group_instances = previous.group_instances


TIME_HINTS = {
    "秦": -221,
    "西汉": -100,
    "东汉": 25,
    "北宋淳化间": 992,
    "宋初": 960,
    "宋代": 959,
    "宋前期（具体年月未载）": 1000,
    "北宋景德四年六月": 1007.45,
    "北宋天禧元年": 1017,
    "北宋天圣元年五月": 1023.35,
    "北宋天圣七年闰二月二十四日": 1029.16,
    "北宋宝元元年六月二十日": 1038.47,
    "北宋庆历以后（具体年月未载）": 1045,
    "北宋嘉祐以后（具体年月未载）": 1060,
    "北宋熙宁五年二月": 1072.12,
    "北宋元丰二年二月二十一日": 1079.13,
    "北宋元丰三年": 1080,
    "北宋元丰三年五月二十二日": 1080.38,
    "北宋元丰五年": 1082,
    "北宋元丰新制": 1082.1,
    "北宋元丰八年五月（具体日期异文）": 1085.35,
    "北宋元祐二年": 1087,
    "北宋元祐四年": 1089,
    "北宋元祐五年十月二日": 1090.76,
    "北宋元祐官品令": 1090.8,
    "北宋元符元年四月二十二日": 1098.29,
    "北宋徽宗朝": 1101,
    "北宋（南、北外丞司并置期间，具体年月未载）": 1100,
    "北宋（都大提举修河司设置期间，具体年月未载）": 1090,
    "北宋（街道司设置期间，具体年月未载）": 1070,
    "宋代（都水监官通称，具体年月未载）": 1100.1,
    "南宋": 1127,
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


def entry1001():
    i, main = 1001, F[1001]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "北外都水监丞司", "知北外都水监丞司公事",
        "北宋元丰三年九月二十八日", main,
        "知北外都水监丞司公事隶都水监并掌领北外司。",
        quota=1, staff_type="北外监丞", office_event="设置知司公事一人",
        post_event="由知外都水监丞北司公事改名，掌领北外司",
    )
    evolution(
        w, touched, i, "知外都水监丞北司公事", "知北外都水监丞司公事",
        "北宋元丰三年九月二十八日", main,
        "元丰三年九月二十八日随司名改称。",
        source_type="官职", target_type="官职",
        source_event="改称知北外都水监丞司公事",
        target_event="由知外都水监丞北司公事改名，掌领北外司",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理知北外都水监丞司公事改名、编制隶属、职掌与简称。")


def entry1002():
    i, main = 1002, F[1002]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "南、北外两丞司", "机构",
        "北宋（南、北外丞司并置期间，具体年月未载）",
        "南外都水监丞司、北外都水监丞司合称",
        ("南外都水监丞司", "北外都水监丞司"), main,
        "原文明确南、北外两丞司是南外司与北外司的合称。",
    )
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "建立南、北外两丞司统称及两个正式机构实例，保存简称证据。")


def entry1003():
    i, main = 1003, F[1003]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "都大提举修河司", "机构",
         "北宋庆历以后（具体年月未载）",
         "沿黄河南北岸因兴修水利分段置司，随所在地命名",
         main, "治河机构总称", "记录庆历以后因河患分段置修河司。",
         update_event=True)
    reform = node(
        w, touched, i, "都大提举修河司", "机构", "北宋元丰三年",
        "黄河南、北岸各设四都大提举河事司",
        main, "治河机构总称", "记录元丰三年南北岸八司配置。",
        update_event=True,
    )
    parent_child(
        w, touched, i, "都水监", "都大提举修河司", "北宋元丰三年",
        main, "都水监之下沿黄河分段设置都大提举修河司。",
        parent_event="统辖沿河都大提举修河司",
        child_event="黄河南北岸分设八司",
    )
    node(w, touched, i, "都大提举修河司", "机构", "北宋元祐二年",
         "复置", main, "复置治河机构", "记录元祐二年复置。",
         update_event=True)
    node(w, touched, i, "都大提举修河司", "机构",
         "北宋元祐五年十月二日", "罢置", main, "废罢机构",
         "记录元祐五年罢置。", update_event=True)
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "整理都大提举修河司庆历后设置、元丰八司、元祐复罢与简称。")


def entry1004():
    i, main = 1004, F[1004]["text"]
    aliases = field(i, "简称")
    time = "北宋（都大提举修河司设置期间，具体年月未载）"
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "都水监", "都大提举河事官", time, main,
        "都大提举河事官是都水监所属诸修河司提举官总名。",
        staff_type="治河提举官总名",
        office_event="设置所属诸都大修河司提举官",
        post_event="总领所在司治河及下属监埽官",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理都大提举河事官总名、都水监编制归属、职掌与简称。")


def entry1005():
    i, main = 1005, F[1005]["text"]
    aliases = field(i, "简称")
    time = "北宋（都大提举修河司设置期间，具体年月未载）"
    w, touched = W(i), set()
    group = node(
        w, touched, i, "都大提举河事官", "官职", time,
        "都水监所属诸都大修河司提举官总名", main,
        "治河提举官总名", "复用都大提举河事官统称节点。",
    )
    post = node(
        w, touched, i, "都大提举大名府界金堤", "官职", time,
        "总领黄河北岸北京金堤界分修堤事务，一员差充",
        main, "都大提举河事官实例", "建立大名府界金堤提举官。",
        officer="承务郎以上文臣，或经都水监奏举、水部司审批的武臣",
        update_event=True,
    )
    relation(w, i, group, post, "统称与实例", main,
             "都大提举大名府界金堤是都大提举河事官之一。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理都大提举大名府界金堤的统称归属、界分职掌、差充与简称。")


def entry1006():
    i, main = 1006, F[1006]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "都水监", "都大提举导洛通汴司",
        "北宋元丰二年二月二十一日", main,
        "都大提举导洛通汴司始置并隶都水监。",
        parent_event="设置并统辖导洛通汴司",
        child_event="始置，主管导洛入汴工程",
    )
    office_staff(
        w, touched, i, "都大提举导洛通汴司", "都大提举导洛通汴",
        "北宋元丰二年二月二十一日", roster,
        "导洛通汴司设都大提举官一员。", "编制",
        quota=1, staff_type="都大提举官",
        office_event="始置并设都大提举官一员",
        post_event="监领导洛通汴工程",
        officer="入内东头供奉官充",
    )
    start = node(
        w, touched, i, "都大提举导洛通汴司", "机构",
        "北宋元丰二年二月二十一日", "始置，主管导洛入汴工程",
        origin, "水利工程机构", "补证始置年月。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补证五十一里运河工程职掌。", "职掌")
    evolution(
        w, touched, i, "都大提举导洛通汴司", "都大提举汴河堤岸司",
        "北宋元丰三年五月二十二日", origin,
        "元丰三年五月二十二日导洛通汴司改为汴河堤岸司。", "职源与沿革",
        source_event="使命完成后改称都大提举汴河堤岸司",
        target_event="由都大提举导洛通汴司改称",
    )
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理导洛通汴司始置、都水监隶属、工程职掌编制及改名。")


def entry1007():
    i, main = 1007, F[1007]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "都大提举导洛通汴司", "都大提举导洛通汴",
        "北宋元丰二年二月二十一日", main,
        "都大提举导洛通汴由内侍官充，掌监领导洛通汴司。",
        quota=1, staff_type="都大提举官",
        office_event="始置并设都大提举官一员",
        post_event="掌监领导洛通汴司公事",
        officer="入内东头供奉官充",
    )
    finish(w, touched, "整理恢复后的都大提举导洛通汴正式词头、差充与监领职掌。")


def entry1008():
    i, main = 1008, F[1008]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "都水监", "都大提举汴河堤岸司",
        "北宋元丰三年五月二十二日", main,
        "都大提举汴河堤岸司由导洛通汴司改置并隶都水监。",
        parent_event="统辖汴河堤岸司",
        child_event="由导洛通汴司改置，主管汴河航运课利与堤岸",
    )
    source, start = evolution(
        w, touched, i, "都大提举导洛通汴司", "都大提举汴河堤岸司",
        "北宋元丰三年五月二十二日", origin,
        "元丰三年五月二十二日导洛通汴司改为汴河堤岸司。", "职源",
        source_event="完成开河并主管一年后改置",
        target_event="由导洛通汴司改置，主管新运河",
    )
    cite(w, "Timepoints", start, i, duty, "补证航运、课利与堤岸保护职掌。", "职掌")
    node(w, touched, i, "都大提举汴河堤岸司", "机构", "北宋元丰八年五月（具体日期异文）",
         "罢置", aliases, "废罢机构", "记录元丰八年五月罢置，具体日期原书引文有异。",
         "简称", update_event=True)
    node(w, touched, i, "都大提举汴河堤岸司", "机构", "北宋元符元年四月二十二日",
         "复置", aliases, "复置机构", "记录元符元年复置。", "简称",
         update_event=True)
    node(w, touched, i, "都大提举汴河堤岸司", "机构", "北宋徽宗朝",
         "沿置", origin, "水利机构", "记录徽宗朝沿置。", "职源", update_event=True)
    alias_note(w, i, start, aliases, "简称")
    assert source
    finish(w, touched, "整理汴河堤岸司改置、都水监隶属、职掌、元丰罢元符复及简称。")


def entry1009():
    i, main = 1009, F[1009]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "都大提举汴河堤岸司", "都大提举汴河堤岸",
        "北宋元丰三年五月二十二日", main,
        "都大提举汴河堤岸监领汴河堤岸司公事。",
        staff_type="都大提举官", office_event="设置都大提举官",
        post_event="监领汴河堤岸司公事",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理恢复后的都大提举汴河堤岸正式词头、监领职掌与简称。")


def entry1010():
    i, main = 1010, F[1010]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    node(w, touched, i, "河埽司", "机构", "北宋淳化间",
         "沿黄河已有河埽建置，与主埽使臣有别",
         origin, "河防基层机构", "记录淳化间已有河埽建置。", "职源",
         update_event=True)
    formal = node(
        w, touched, i, "河埽司", "机构", "北宋元祐四年",
        "河埽司正称见于记载，掌备料、制埽、埽岸及巡视河堤",
        origin, "河防基层机构", "记录河埽司正式称名。", "职源",
        update_event=True,
    )
    cite(w, "Timepoints", formal, i, duty, "补证备料、制埽、埽岸及巡堤职掌。", "职掌")
    parent_child(
        w, touched, i, "外都水监丞司", "河埽司",
        "北宋嘉祐以后（具体年月未载）", main,
        "原书称河埽司嘉祐后隶‘外部都水监丞司’，按本门正式机构外都水监丞司建模。",
        parent_event="统辖河埽司",
        child_event="嘉祐后隶外部都水监丞司",
    )
    for post in ("管勾官", "监官"):
        office_staff(
            w, touched, i, "河埽司", post, "北宋元祐四年", roster,
            "河埽司设管勾官或监官。", "编制",
            staff_type="管勾官或监官", office_event="设置管勾官或监官",
            post_event="掌监河埽司公事",
        )
    finish(w, touched, "整理河埽司淳化源流、元祐正称、外都水监丞司隶属、职掌与编制。")


def entry1011():
    i, main = 1011, F[1011]["text"]
    time = "宋代（都水监官通称，具体年月未载）"
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "水官", "官职", time,
        "都水监官通称",
        (
            "判都水监事", "同判都水监事", "勾当都水监公事",
            "知都水监丞公事", "知都水监主簿公事", "都水监使者",
            "都水监丞", "都水监主簿", "外都水监使者",
            "南外都水监丞", "北外都水监丞", "都水监都提举官",
            "都大提举河事官", "都水监监埽官",
        ),
        main, "原文明确水官是都水监官的通称，复用本门已有都水监属官为实例。",
    )
    finish(w, touched, "建立水官通称及本门已有都水监属官实例。")


def entry1012():
    i, main = 1012, F[1012]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    node(w, touched, i, "街道司", "机构", "北宋景德四年六月",
         "与东、西八作司合为一司", origin, "京师道路机构",
         "记录景德四年并司。", "职源与沿革", update_event=True)
    node(w, touched, i, "街道司", "机构", "北宋天圣元年五月",
         "又分出独立置司", origin, "京师道路机构",
         "记录天圣元年复分独立。", "职源与沿革", update_event=True)
    node(w, touched, i, "街道司", "机构", "北宋宝元元年六月二十日",
         "罢置", origin, "废罢机构", "记录宝元元年罢置。", "职源与沿革",
         update_event=True)
    parent, restored = parent_child(
        w, touched, i, "都水监", "街道司",
        "北宋嘉祐以后（具体年月未载）", main,
        "仁宗嘉祐后街道司复置并隶都水监。",
        parent_event="统辖复置的街道司",
        child_event="嘉祐后复置，隶都水监，修治京师道路",
    )
    cite(w, "Timepoints", restored, i, origin, "补证嘉祐后复置及南宋不置。", "职源与沿革")
    cite(w, "Timepoints", restored, i, duty, "补证京师道路整修与疏水职掌。", "职掌")
    cite(w, "Timepoints", restored, i, roster, "补证勾当官及五百兵士编制。", "编制")
    node(w, touched, i, "街道司", "机构", "南宋", "不置",
         origin, "未置机构", "记录南宋不置街道司。", "职源与沿革",
         update_event=True)
    assert parent
    finish(w, touched, "整理街道司景德并司、天圣复分、宝元罢、嘉祐复置隶属及南宋不置。")


def entry1013():
    i, main = 1013, F[1013]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "街道司", "管勾街道司公事",
        "北宋（街道司设置期间，具体年月未载）", main,
        "管勾街道司公事二人，由武臣差充，监领本司。",
        quota=2, staff_type="勾当官",
        office_event="设置勾当官二人",
        post_event="监领街道司公事，编制二人",
        officer="武臣大使臣或三班使臣充",
    )
    finish(w, touched, "整理管勾街道司公事的差充、监领职掌与两人员额。")


YUANFENG_CENSORATE_ROSTER = (
    ("御史中丞", 1, "台长", "御史台实际长官", "从三品"),
    ("侍御史", 1, "副台长", "御史台副长官", "从六品"),
    ("殿中侍御史", 2, "监察官", "掌殿院监察", "正七品"),
    ("监察御史", 6, "监察官", "掌察院监察", "从七品"),
    ("御史台检法官", 1, "检法官", "掌检法", "从八品"),
    ("御史台主簿", 1, "主簿", "掌台簿书", "从八品"),
)


def entry1014():
    i, main = 1014, F[1014]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    evolution(
        w, touched, i, "御史府", "御史台", "东汉", origin,
        "西汉称御史府，东汉始称御史台。", "职源与沿革",
        source_event="西汉监察机构称御史府",
        target_event="东汉始称御史台，或称兰台寺",
    )
    song = node(
        w, touched, i, "御史台", "机构", "宋代",
        "宋沿置，直隶皇帝，掌纠察百官与诉讼审理",
        main, "中央监察机构", "建立宋代御史台正式机构节点。",
        update_event=True,
    )
    cite(w, "Timepoints", song, i, origin, "补证宋沿置及台谏制度强化。", "职源与沿革")
    cite(w, "Timepoints", song, i, duty, "补证纠察、弹劾、审讯及诉讼职掌。", "职掌")
    cite(w, "Timepoints", song, i, rank, "补证御史台与中书、枢密不相统属。", "品位")
    node(w, touched, i, "御史台", "机构", "北宋天禧元年",
         "始置言事御史，台谏合一", origin, "中央监察机构",
         "记录天禧元年言事御史设置。", "职源与沿革", update_event=True)
    for post, quota, kind, event in (
        ("御史中丞", 1, "台长", "御史大夫不除时为实际台长"),
        ("判御史台事", None, "兼领官", "以他官兼判御史台事"),
        ("侍御史知杂事", None, "副贰", "御史台副贰，掌台院"),
    ):
        office_staff(
            w, touched, i, "御史台", post, "宋前期（具体年月未载）",
            roster, f"宋前期御史台设置或兼领{post}。", "编制",
            quota=quota, staff_type=kind, office_event="宋前期御史台官制",
            post_event=event,
        )
    reform = node(
        w, touched, i, "御史台", "机构", "北宋元丰新制",
        "罢言事御史、御史里行、推直官，定台官与十一案编制",
        roster, "中央监察机构", "记录元丰新制御史台官额。", "编制",
        update_event=True,
    )
    for post, quota, kind, event, grade in YUANFENG_CENSORATE_ROSTER:
        office_staff(
            w, touched, i, "御史台", post, "北宋元丰新制", roster,
            f"元丰新制定{post}{quota}人。", "编制",
            quota=quota, staff_type=kind,
            office_event="元丰新制定台官、十一案与吏额",
            post_event=event, grade=grade,
        )
    south = node(
        w, touched, i, "御史台", "机构", "南宋",
        "台官额遵元丰新制定员，吏额后有裁减",
        roster, "中央监察机构", "记录南宋御史台官吏编制。", "编制",
        update_event=True,
    )
    cite(w, "Timepoints", reform, i, rank, "补证元丰新制台官品位。", "品位")
    cite(w, "Timepoints", south, i, duty, "补证南宋延续监察职掌。", "职掌")
    alias_note(w, i, song, aliases, "简称与别名")
    finish(w, touched, "整理御史台汉代源流、宋沿置、天禧台谏合一、宋前期与元丰南宋编制。")


def entry1015():
    assert F[1015]["text"] == ""
    assert F[1015]["fields"].get("_placeholder") is True


def entry1016():
    i, main = 1016, F[1016]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "御史台", "判御史台事", "宋初", main,
        "宋初以他官判御史台事，位次正官御史中丞。",
        staff_type="兼领官", office_event="正官之外可由他官判台事",
        post_event="以他官领御史台，位次御史中丞",
    )
    finish(w, touched, "整理判御史台事宋初兼领性质及与御史中丞的位次。")


def entry1017():
    i, main = 1017, F[1017]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "御史台", "管勾御史台事",
        "宋前期（具体年月未载）", main,
        "御史中丞阙时，以他官暂领御史台公事。",
        staff_type="暂领官", office_event="中丞阙时暂置管勾官",
        post_event="御史中丞阙时暂领御史台公事",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理管勾御史台事的暂领条件、职掌与简称。")


def entry1018():
    i, main = 1018, F[1018]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "御史大夫", "官职", "秦",
         "始置", origin, "前代监察官源流", "记录秦置御史大夫。", "职源",
         update_event=True)
    early = node(
        w, touched, i, "御史大夫", "官职", "宋前期（具体年月未载）",
        "作为检校官所带宪衔，不任御史台实际长官",
        main, "兼官", "记录宋前期兼官性质。", update_event=True,
        grade="正三品",
    )
    cite(w, "Timepoints", early, i, duty, "补证检校官兼带宪衔。", "职掌")
    reform = node(
        w, touched, i, "御史大夫", "官职", "北宋元丰新制",
        "改为职事官但虚存其名，不除人",
        main, "职事官虚衔", "记录元丰新制后的虚置性质。",
        grade="从二品", update_event=True,
    )
    cite(w, "Timepoints", reform, i, duty, "补证元丰后虚存不除。", "职掌")
    cite(w, "Timepoints", reform, i, rank, "补证元丰从二品及名义台主地位。", "品位")
    node(w, touched, i, "御史大夫", "官职", "北宋元祐官品令",
         "官品升为正二品，仍名义为一台之主", rank,
         "职事官虚衔", "记录元祐官品。", "品位", grade="正二品",
         update_event=True)
    node(w, touched, i, "御史大夫", "官职", "南宋",
         "仍虚而不除，官品从二品", rank, "职事官虚衔",
         "记录南宋官品。", "品位", grade="从二品", update_event=True)
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "整理御史大夫秦源流、宋前期兼官、元丰虚置及历朝品位。")


def entry1019():
    i, main = 1019, F[1019]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "御史中丞", "官职", "秦",
         "御史大夫置两丞，其中一称御史中丞",
         origin, "前代监察官源流", "记录御史中丞始置于秦。", "职源",
         update_event=True)
    early = node(
        w, touched, i, "御史中丞", "官职", "宋初",
        "宋沿置，为御史台实际长官，须由皇帝亲擢",
        main, "御史台长官", "记录宋初御史中丞职事官性质。",
        grade="正四品", update_event=True,
    )
    cite(w, "Timepoints", early, i, duty, "补证御史台长官职掌。", "职掌")
    cite(w, "Timepoints", early, i, rank, "补证宋初正四品及实际台长地位。", "品位")
    office_staff(
        w, touched, i, "御史台", "御史中丞", "宋初", roster,
        "御史中丞一人，为御史台实际长官。", "编制",
        quota=1, staff_type="台长", office_event="以中丞为实际台长",
        post_event="御史台实际长官，编制一人", grade="正四品",
    )
    node(w, touched, i, "御史中丞", "官职",
         "北宋天圣七年闰二月二十四日", "始须带理检使",
         roster, "御史台长官", "记录天圣七年始带理检使。", "编制",
         update_event=True)
    reform = node(
        w, touched, i, "御史中丞", "官职", "北宋元丰新制",
        "元丰五年改制罢带理检使，定为从三品",
        roster, "御史台长官", "记录元丰改制官品及罢带使名。", "编制",
        grade="从三品", update_event=True,
    )
    cite(w, "Timepoints", reform, i, rank, "补证元丰从三品。", "品位")
    node(w, touched, i, "御史中丞", "官职", "北宋元祐官品令",
         "官品升为正三品", rank, "御史台长官",
         "记录元祐官品。", "品位", grade="正三品", update_event=True)
    node(w, touched, i, "御史中丞", "官职", "南宋",
         "复为从三品，仍为御史台实际长官", rank, "御史台长官",
         "记录南宋官品。", "品位", grade="从三品", update_event=True)
    alias_note(w, i, early, aliases, "简称与别名")
    finish(w, touched, "整理御史中丞秦源流、宋代台长、带理检使沿革、编制品位与别名。")


def entry1020():
    i, main = 1020, F[1020]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "御史台", "权御史中丞事",
        "宋前期（具体年月未载）", main,
        "正官御史中丞阙时，以给事中、谏议大夫权领。",
        staff_type="权领台长", office_event="中丞阙时置权中丞",
        post_event="正官中丞阙时权领御史台，以给事中或谏议大夫充",
    )
    node(w, touched, i, "权御史中丞事", "官职", "北宋熙宁五年二月",
         "自邓绾始，权中丞不再必须迁谏议大夫",
         main, "权领台长", "记录熙宁五年差充资格变化。", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理权御史中丞事的设置条件、差充资格、熙宁变化与简称。")


def main():
    for i in range(1001, 1021):
        globals()[f"entry{i}"]()
        suffix = " placeholder skipped" if i == 1015 else " done"
        print(f"#{i} {F[i]['title']}{suffix}")


if __name__ == "__main__":
    main()
