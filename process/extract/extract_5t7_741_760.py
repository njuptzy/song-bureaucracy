#!/usr/bin/env python3
"""提取 chapter5t7 第741-760条：寄桩库、五监通称与国子监系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_721_740 as previous


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


F = {i: load(i) for i in range(741, 761)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
state = base.state
relation = base.relation
staff = base.staff
alias_note = base.alias_note


TIME_HINTS = {
    "战国": -300, "西晋咸宁四年": 278, "北齐": 550,
    "隋大业三年": 607, "隋代": 610, "后周显德二年": 955,
    "宋初": 960, "宋前期": 970, "北宋前期": 970,
    "北宋端拱二年二月": 989.12, "北宋淳化五年三月二十四日": 994.22,
    "北宋庆历三、四年": 1044, "北宋熙宁六年六月二十七日": 1073.45,
    "北宋元丰新制": 1082, "北宋元丰五年五月": 1082.35,
    "北宋元丰五年新制": 1082.4, "北宋元丰六年七月": 1083.55,
    "北宋崇宁三年六月": 1104.45, "北宋崇宁五年四月": 1106.3,
    "北宋大观四年": 1110, "宋代（未载具体年月）": 1100,
    "南宋初": 1127.05, "南宋建炎三年四月十四日": 1129.3,
    "南宋": 1130, "南宋绍兴三年六月二十四日": 1133.48,
    "南宋绍兴十年": 1140, "南宋绍兴十一年四月": 1141.3,
    "南宋绍兴十二年十二月十二日": 1142.95,
    "南宋绍兴十三年正月九日": 1143.03,
    "南宋绍兴十四年六月五日": 1144.45,
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


def node(w, touched, i, title, type_, time, event, quotation, category,
         decision, field_name=None, *, officer=None, grade=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )
    touched.add(eid)
    return tid


def parent_child(w, touched, i, parent, child, time, quotation, decision,
                 field_name=None, *, parent_event=None, child_event=None):
    parent_tid = node(
        w, touched, i, parent, "机构", time,
        parent_event or f"统辖{child}", quotation, "上级机构",
        f"建立或复用{parent}{time}节点。", field_name,
    )
    child_tid = node(
        w, touched, i, child, "机构", time,
        child_event or f"隶属{parent}", quotation, "所属机构",
        f"建立或复用{child}{time}节点。", field_name,
    )
    relation(w, i, parent_tid, child_tid, "上下级机构", quotation,
             decision, field_name)
    return parent_tid, child_tid


def office_staff(w, touched, i, office, post, time, quotation, decision,
                 field_name=None, *, quota=None, staff_type="官",
                 office_event=None, post_event=None, officer=None, grade=None):
    office_tid = node(
        w, touched, i, office, "机构", time,
        office_event or f"设置{post}", quotation, "办事机构",
        f"建立或复用{office}{time}编制节点。", field_name,
    )
    post_tid = node(
        w, touched, i, post, "官职", time,
        post_event or f"领{office}事", quotation, "职事或差遣官",
        f"建立或复用{post}{time}节点。", field_name,
        officer=officer, grade=grade,
    )
    staff(w, i, office_tid, post_tid, quotation, decision, field_name,
          quota=quota, staff_type=staff_type)
    return office_tid, post_tid


def group_members(w, touched, i, group_title, group_type, time, event,
                  members, quotation, decision, field_name=None):
    group_tid = node(
        w, touched, i, group_title, group_type, time, event, quotation,
        f"{group_type}统称", f"建立{group_title}{time}统称节点。", field_name,
    )
    for member_title, member_type in members:
        member_tid = node(
            w, touched, i, member_title, member_type, time,
            f"{group_title}在{time}所指实例", quotation,
            f"{group_title}实例", f"建立或复用{member_title}{time}实例节点。",
            field_name,
        )
        relation(w, i, group_tid, member_tid, "统称与实例", quotation,
                 f"{member_title}是{group_title}的实例。", field_name)
    return group_tid


def entry741():
    i, quote = 741, F[741]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "打套局", "库经司", "南宋绍兴八年后", quote,
        "库经司为打套局吏人，在本局承办行遣。", staff_type="吏",
        office_event="设置库经司承办行遣",
        post_event="打套局吏人，在本局承办行遣事",
    )
    finish(w, touched, "补证库经司隶属打套局及承办行遣职掌。")


def entry742():
    i, quote = 742, F[742]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "太府寺", "寄桩库", "南宋", quote,
        "南宋寄桩库隶太府寺。",
        parent_event="统辖寄桩库",
        child_event="拘管左藏南库及封桩库编估出卖官物与收钱文历",
    )
    for post, staff_type in (("提领寄桩军官", "提领官"), ("监寄桩库", "监官")):
        office_staff(
            w, touched, i, "寄桩库", post, "南宋", quote,
            f"寄桩库置{post}一员。", quota=1, staff_type=staff_type,
            office_event="设置提领军官、监官各一员",
            post_event="领寄桩库拘管官物与收钱文历事务",
        )
    finish(w, touched, "整理寄桩库太府寺隶属、职掌及两类监领官编制链。")


def entry743():
    i, quote = 743, F[743]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "五监", "机构", "北宋元丰新制",
        "元丰定制的国子、少府、将作、军器、都水五监合称",
        [(x, "机构") for x in ("国子监", "少府监", "将作监", "军器监", "都水监")],
        quote, "建立北宋元丰五监及五个实例。",
    )
    for source_title, target_title, source_time, target_time in (
        ("司天监", "太史局", "北宋元丰五年五月", "北宋元丰五年五月"),
        ("秘书监", "秘书省", "北宋元丰新制", "北宋元丰新制"),
    ):
        source = node(
            w, touched, i, source_title, "机构", source_time,
            f"元丰新制改为{target_title}", quote, "元丰改制前机构",
            f"建立或复用{source_title}元丰改名节点。",
        )
        target = node(
            w, touched, i, target_title, "机构", target_time,
            f"由{source_title}改置", quote, "元丰改制后机构",
            f"建立或复用{target_title}元丰改置节点。",
        )
        relation(w, i, source, target, "前后演变", quote,
                 f"元丰新制{source_title}改为{target_title}。")
    finish(w, touched, "整理五监统称及司天、秘书两监元丰改置链。")


def entry744():
    i, quote = 744, F[744]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "三监", "机构", "南宋",
        "秘书省、军器监、将作监的合称",
        [(x, "机构") for x in ("秘书省", "军器监", "将作监")],
        quote, "建立南宋三监及三个实例。",
    )
    node(w, touched, i, "少府监", "机构", "南宋建炎三年四月十四日",
         "建炎三年罢置，未列入南宋三监", quote, "罢置监司",
         "建立少府监南宋罢置节点。")
    node(w, touched, i, "都水监", "机构", "南宋绍兴十年",
         "绍兴十年罢置，未列入南宋三监", quote, "罢置监司",
         "建立都水监南宋罢置节点。")
    finish(w, touched, "整理南宋三监实例及少府、都水二监罢置链。")


def entry745():
    i, quote = 745, F[745]["text"]
    w, touched = W(i), set()
    group = group_members(
        w, touched, i, "判监", "官职", "宋前期",
        "诸监以他官领监事、称判某监事的通称",
        [("判国子监事", "官职"), ("判将作监事", "官职")],
        quote, "建立宋前期判监统称及原文明见实例。",
    )
    ending = node(
        w, touched, i, "判监", "官职", "北宋元丰新制",
        "元丰正名，各以监长领事，遂罢判监", quote, "监司差遣通称",
        "建立判监元丰罢置节点。",
    )
    successor = node(
        w, touched, i, "正监", "官职", "北宋元丰新制",
        "元丰正名后由各监长官领本监事", quote, "监司长官通称",
        "建立正监承接监事节点。",
    )
    relation(w, i, ending, successor, "前后演变", quote,
             "元丰新制罢判监，改由正监领本监事。")
    finish(w, touched, "整理宋前期判监统称及元丰正名后罢置链。")


MONITOR_HEADS = ("司天监", "将作监", "少府监", "军器监", "秘书监")
MONITOR_DEPUTIES = ("司天少监", "将作少监", "少府少监", "军器少监", "秘书省少监")


def entry746():
    i, quote = 746, F[746]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "大监", "官职", "宋代（未载具体年月）",
        "除国子监祭酒、都水监使者外诸监长官的通称",
        [(x, "官职") for x in MONITOR_HEADS], quote,
        "建立大监通称及五类监长实例。",
    )
    finish(w, touched, "整理大监通称及五类监长实例链。")


def entry747():
    i, quote = 747, F[747]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "正监", "官职", "宋代（未载具体年月）",
        "诸监监长官的通称，与少监相对",
        [(x, "官职") for x in MONITOR_HEADS], quote,
        "建立正监通称及五类监长实例。",
    )
    finish(w, touched, "整理正监通称及五类监长实例链。")


def entry748():
    i, quote = 748, F[748]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "副监", "官职", "宋代（未载具体年月）",
        "诸监少监的别称",
        [(x, "官职") for x in MONITOR_DEPUTIES], quote,
        "建立副监通称及五类少监实例。",
    )
    finish(w, touched, "整理副监通称及五类少监实例链。")


def entry749():
    i, quote = 749, F[749]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "监少", "官职", "南宋绍兴十一年四月",
        "诸监监与少监的连称",
        [("正监", "官职"), ("副监", "官职")], quote,
        "建立监少连称及正监、副监实例。",
    )
    finish(w, touched, "整理监少连称与正副监实例链。")


def entry750():
    i, quote = 750, F[750]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "监长贰", "官职", "宋前期",
        "元丰正名前有职事的判监、同判监之别称",
        [("判监", "官职"), ("同判监", "官职")], quote,
        "建立宋前期监长贰及判监、同判监实例。",
    )
    group_members(
        w, touched, i, "监长贰", "官职", "北宋元丰新制",
        "正监、少监及国子、都水两监长贰的总称",
        [(x, "官职") for x in (
            "正监", "副监", "国子监祭酒", "国子监司业", "都水监使者", "都水监丞",
        )], quote, "建立元丰新制监长贰及六类实例。",
    )
    finish(w, touched, "整理监长贰在元丰前后的实例范围链。")


MONITOR_ASSISTANTS = ("国子监丞", "少府监丞", "将作监丞", "军器监丞", "都水监丞")
MONITOR_CLERKS = ("国子监主簿", "少府监主簿", "将作监主簿", "军器监主簿", "都水监主簿")


def entry751():
    i, quote = 751, F[751]["text"]
    w, touched = W(i), set()
    group = node(
        w, touched, i, "监丞", "官职", "北宋元丰新制",
        "五监丞的通称；国子监丞正八品，余四监丞从八品", quote,
        "监丞统称", "建立监丞统称节点。",
    )
    for title in MONITOR_ASSISTANTS:
        grade = "正八品" if title == "国子监丞" else "从八品"
        member = node(
            w, touched, i, title, "官职", "北宋元丰新制",
            f"五监丞实例，品位{grade}", quote, "监丞实例",
            f"建立或复用{title}元丰节点。", grade=grade,
        )
        relation(w, i, group, member, "统称与实例", quote,
                 f"{title}是监丞实例。")
    finish(w, touched, "整理监丞统称、五监丞实例及品位链。")


def entry752():
    i, quote = 752, F[752]["text"]
    w, touched = W(i), set()
    group = node(
        w, touched, i, "监簿", "官职", "北宋元丰六年七月",
        "五监主簿通称，专掌簿书，均为从八品", quote,
        "监主簿统称", "建立监簿统称节点。",
        grade="从八品",
    )
    for title in MONITOR_CLERKS:
        member = node(
            w, touched, i, title, "官职", "北宋元丰六年七月",
            "监簿实例，专掌簿书，从八品", quote, "监簿实例",
            f"建立或复用{title}元丰六年节点。", grade="从八品",
        )
        relation(w, i, group, member, "统称与实例", quote,
                 f"{title}是监簿实例。")
    finish(w, touched, "整理监簿通称、五监主簿实例及从八品属性链。")


def entry753():
    i, quote = 753, F[753]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "五监主簿", "官职", "北宋元丰新制",
        "国子、少府、将作、军器、都水五监主簿的合称",
        [(x, "官职") for x in MONITOR_CLERKS], quote,
        "建立五监主簿统称及五个实例。",
    )
    finish(w, touched, "整理五监主簿统称与五个主簿实例链。")


def entry754():
    i = 754
    main = F[i]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    node(w, touched, i, "国子寺", "机构", "北齐",
         "作为教育管理机构已置", origin, "前代教育管理机构",
         "建立国子寺北齐职源节点。", "职源与沿革")
    source = node(w, touched, i, "国子寺", "机构", "隋大业三年",
                  "改置国子监", origin, "前代教育管理机构",
                  "建立国子寺隋代改置节点。", "职源与沿革")
    target = node(w, touched, i, "国子监", "机构", "隋大业三年",
                  "始置国子监", origin, "教育管理机构兼官学",
                  "建立国子监隋代始置节点。", "职源与沿革")
    relation(w, i, source, target, "前后演变", origin,
             "隋大业三年国子寺改置国子监。", "职源与沿革")
    node(w, touched, i, "国子监", "机构", "后周显德二年",
         "营造国子监并置学舍", origin, "教育管理机构兼官学",
         "建立后周国子监营造节点。", "职源与沿革")
    song = node(w, touched, i, "国子监", "机构", "宋初",
                "北宋沿置于开封，兼教育管理机构与官学", origin,
                "中央教育管理机构兼官学", "建立北宋沿置节点。", "职源与沿革")
    rename = node(w, touched, i, "国子监", "机构", "北宋端拱二年二月",
                  "改称国子学", origin, "中央教育管理机构兼官学",
                  "建立国子监端拱改名节点。", "职源与沿革")
    school = node(w, touched, i, "国子学", "机构", "北宋端拱二年二月",
                  "由国子监改称，仍为管理机构与学校合一", origin,
                  "中央教育管理机构兼官学", "建立国子学改称节点。", "职源与沿革")
    relation(w, i, rename, school, "前后演变", origin,
             "端拱二年国子监改称国子学。", "职源与沿革")
    school_end = node(w, touched, i, "国子学", "机构", "北宋淳化五年三月二十四日",
                      "复改称国子监", origin, "中央教育管理机构兼官学",
                      "建立国子学淳化复名节点。", "职源与沿革")
    restored = node(w, touched, i, "国子监", "机构", "北宋淳化五年三月二十四日",
                    "由国子学复改称", origin, "中央教育管理机构兼官学",
                    "建立国子监淳化复名节点。", "职源与沿革")
    relation(w, i, school_end, restored, "前后演变", origin,
             "淳化五年国子学复称国子监。", "职源与沿革")
    abolished = node(w, touched, i, "国子监", "机构", "南宋建炎三年四月十四日",
                     "并归礼部", origin, "中央教育管理机构",
                     "建立国子监建炎并省节点。", "职源与沿革")
    ministry = node(w, touched, i, "尚书省礼部", "机构", "南宋建炎三年四月十四日",
                    "接收国子监职事", origin, "尚书省部门",
                    "复用尚书省礼部并建立接收国子监节点。", "职源与沿革")
    relation(w, i, abolished, ministry, "前后演变", origin,
             "建炎三年国子监并归礼部。", "职源与沿革")
    revived = node(w, touched, i, "国子监", "机构", "南宋绍兴三年六月二十四日",
                   "复置，称行在国子监，位于临安", origin,
                   "中央教育管理机构兼官学", "建立行在国子监复置节点。", "职源与沿革")

    for time, event in (
        ("宋初", "聚生徒讲学，与国子学合一，并掌刻印、出卖经书"),
        ("北宋庆历三、四年", "州县及诸学发展后，统管教授荐送、刻印书籍等教育事务"),
        ("北宋元丰新制", "掌国子、太学、律学、武学、算学五学政令训导与刻书"),
        ("南宋", "专掌天下学校，仍雕印出卖监本书"),
    ):
        tid = node(w, touched, i, "国子监", "机构", time, event, duty,
                   "中央教育管理机构兼官学", f"建立国子监{time}职掌节点。", "职掌")

    early_office = node(w, touched, i, "国子监", "机构", "宋前期",
                        "设判监、同判或管勾、同管勾领事", roster,
                        "中央教育管理机构兼官学", "建立宋前期国子监编制节点。", "编制")
    for post, quota, staff_type in (
        ("判国子监事", 1, "判监"), ("同判国子监事", 1, "同判监"),
        ("国子监丞", 1, "丞"), ("国子监主簿", 1, "主簿"),
    ):
        _, post_tid = office_staff(
            w, touched, i, "国子监", post, "宋前期", roster,
            f"宋前期国子监置{post}{quota}人。", "编制", quota=quota,
            staff_type=staff_type, office_event="形成宋前期官额",
            post_event="国子监宋前期官属",
        )
    for post, quota in (("国子监直讲", 8), ("国子监讲书", None), ("国子监说书", None)):
        office_staff(w, touched, i, "国子监", post, "宋前期", roster,
                     f"宋前期国子监置{post}。", "编制", quota=quota,
                     staff_type="教官", office_event="设置讲学官",
                     post_event="讲授经术")
    for school_title in (
        "国子学", "太学", "律学", "广文馆", "四门学", "武学", "国子监书库",
    ):
        parent_child(
            w, touched, i, "国子监", school_title, "宋前期", roster,
            f"宋前期{school_title}隶国子监。", "编制",
            parent_event="统辖宋前期诸学及书库",
            child_event="宋前期隶国子监",
        )

    reform_posts = (
        ("国子监祭酒", 1, "祭酒"), ("国子监司业", 1, "司业"),
        ("国子监丞", 1, "丞"), ("国子监主簿", 1, "主簿"),
        ("太学博士", 12, "博士"), ("国子正", 5, "学官"),
        ("国子录", 5, "学官"), ("武学博士", 2, "博士"),
        ("律学博士", 1, "博士"), ("律学正", 1, "学官"),
        ("太学录", 5, "学官"), ("武学正", 1, "学官"),
        ("武学录", 1, "学官"),
    )
    for post, quota, staff_type in reform_posts:
        office_staff(w, touched, i, "国子监", post, "北宋元丰新制", roster,
                     f"元丰新制国子监置{post}{quota}人。", "编制", quota=quota,
                     staff_type=staff_type, office_event="形成元丰新制官学官额",
                     post_event="国子监元丰新制官属")
    for school_title in ("国子学", "太学", "律学", "武学", "小学", "算学", "国子监书库"):
        child = node(w, touched, i, school_title, "机构", "北宋元丰新制",
                     "隶国子监", roster, "国子监所属官学或书库",
                     f"建立{school_title}元丰隶属节点。", "编制")
        office = node(w, touched, i, "国子监", "机构", "北宋元丰新制",
                      "统辖六学及国子监书库", roster, "中央教育管理机构兼官学",
                      "复用国子监元丰编制节点。", "编制")
        relation(w, i, office, child, "上下级机构", roster,
                 f"元丰新制{school_title}隶国子监。", "编制")

    for time, school_title, event in (
        ("北宋崇宁三年六月", "书学", "建置并隶国子监"),
        ("北宋崇宁三年六月", "画学", "建置并隶国子监"),
        ("北宋崇宁三年六月", "医学", "建置并隶国子监"),
        ("北宋崇宁三年六月", "算学", "重建并隶国子监"),
    ):
        parent_child(w, touched, i, "国子监", school_title, time, roster,
                     f"崇宁三年{school_title}隶国子监。", "编制",
                     parent_event="增建四学", child_event=event)
    for school_title in ("医学", "算学"):
        node(w, touched, i, school_title, "机构", "北宋崇宁五年四月",
             "罢置", roster, "国子监所属官学",
             f"建立{school_title}崇宁五年罢置节点。", "编制")
    for school_title, doctor_title in (("书学", "书学博士"), ("画学", "画学博士")):
        parent_child(
            w, touched, i, "国子监", school_title, "北宋崇宁五年四月", roster,
            f"崇宁五年{school_title}罢独立学制后附国子监。", "编制",
            parent_event="书学、画学附国子监",
            child_event="罢独立学制后附国子监",
        )
        office_staff(
            w, touched, i, school_title, doctor_title, "北宋崇宁五年四月", roster,
            f"崇宁五年{school_title}附国子监，置{doctor_title}一员。", "编制",
            quota=1, staff_type="博士", office_event="附国子监并置博士一员",
            post_event=f"掌{school_title}教学",
        )
    for school_title, target_title in (("书学", "翰林书艺局"), ("画学", "翰林图画局")):
        source_tp = node(w, touched, i, school_title, "机构", "北宋大观四年",
                         f"并入{target_title}", roster, "国子监所属官学",
                         f"建立{school_title}大观并入节点。", "编制")
        target_tp = node(w, touched, i, target_title, "机构", "北宋大观四年",
                         f"接收{school_title}", roster, "翰林技艺机构",
                         f"建立{target_title}接收节点。", "编制")
        relation(w, i, source_tp, target_tp, "前后演变", roster,
                 f"大观四年{school_title}并入{target_title}。", "编制")

    office_staff(w, touched, i, "国子监", "国子监博士",
                 "南宋绍兴三年六月二十四日", roster,
                 "绍兴三年复置博士二员。", "编制", quota=2, staff_type="博士",
                 office_event="复置并设博士二员、监生三十六人",
                 post_event="复置初期国子监教官")
    office_staff(w, touched, i, "国子监", "国子监监生",
                 "南宋绍兴三年六月二十四日", roster,
                 "绍兴三年以随驾学生三十六人为监生。", "编制", quota=36,
                 staff_type="监生", office_event="复置并设博士二员、监生三十六人",
                 post_event="随驾学生充监生")
    for post, quota, staff_type in (
        ("国子监祭酒", 1, "祭酒"), ("国子监司业", 1, "司业"),
        ("国子正", 1, "学官"), ("国子录", 1, "学官"),
        ("国子监博士", 3, "博士"),
    ):
        office_staff(w, touched, i, "国子监", post,
                     "南宋绍兴十二年十二月十二日", roster,
                     f"绍兴十二年国子监置{post}{quota}员。", "编制",
                     quota=quota, staff_type=staff_type,
                     office_event="恢复祭酒司业并调整学官额",
                     post_event="绍兴十二年国子监官属")
    parent_child(w, touched, i, "国子监", "太学",
                 "南宋绍兴十三年正月九日", roster,
                 "绍兴十三年在临安建国子监太学。", "编制",
                 parent_event="在临安建国子监太学",
                 child_event="作为国子监太学复建")
    office_staff(w, touched, i, "太学", "太学生",
                 "南宋绍兴十三年正月九日", roster,
                 "绍兴十三年太学生以三百人为额。", "编制", quota=300,
                 staff_type="学生", office_event="太学生以三百人为额",
                 post_event="定额三百人")
    parent_child(w, touched, i, "国子监", "国子监小学",
                 "南宋绍兴十四年六月五日", roster,
                 "绍兴十四年建国子监小学。", "编制",
                 parent_event="建置国子监小学", child_event="始建并隶国子监")
    alias_note(w, i, revived, aliases, "简称与别名")
    finish(w, touched, "整理国子监前代职源、宋代改名省复、分期职掌、所属诸学与官额链。")


def entry755():
    i = 755
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "判国子监事", "宋前期", main,
        "宋前期国子监置判国子监事一员。", quota=1, staff_type="判监",
        office_event="由待制以上朝官判监事，共二员含同判",
        post_event="待制以上朝官领国子监事",
        officer="待制以上朝官",
    )
    _, joint = office_staff(
        w, touched, i, "国子监", "同判国子监事", "宋前期", main,
        "宋前期判监二员中一员称同判。", quota=1, staff_type="同判监",
        office_event="由待制以上朝官判监事，共二员含同判",
        post_event="判监二员中一员带同判衔",
        officer="待制以上朝官",
    )
    post = node(w, touched, i, "判国子监事", "官职", "宋前期",
                "待制以上朝官领国子监事", main, "国子监差遣",
                "复用判国子监事节点。", officer="待制以上朝官")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理判国子监事、同判编制及简称证据链。")


def entry756():
    i = 756
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    _, post = office_staff(
        w, touched, i, "国子监", "同判国子监事", "宋前期", main,
        "国子监二员判监中一员称同判。", quota=1, staff_type="同判监",
        office_event="祭酒司业阙时差二员朝官判监事",
        post_event="侍从官以上充，二员中一员称同判",
        officer="侍从官以上",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理同判国子监事编制、资格与简称证据链。")


def entry757():
    i = 757
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    _, post = office_staff(
        w, touched, i, "国子监", "管勾国子监公事", "宋前期", main,
        "非侍从文官领国子监事称管勾。", quota=1, staff_type="管勾官",
        office_event="长贰不除人时差文官领监事",
        post_event="非侍从官充，位次判监事",
        officer="非侍从文官",
    )
    judge = node(w, touched, i, "判国子监事", "官职", "宋前期",
                 "待制以上领监事，位次高于管勾", main, "国子监差遣",
                 "复用判国子监事资格节点。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理管勾国子监公事资格、位次、编制及简称链。")


def entry758():
    i, quote = 758, F[758]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "管勾国子监公事", "北宋前期", quote,
        "北宋前期国子监差非侍从朝官管勾领事。", quota=1,
        staff_type="管勾官", office_event="差朝官二员领监事",
        post_event="非侍从官领监事称管勾",
    )
    office_staff(
        w, touched, i, "国子监", "同管勾国子监公事", "北宋前期", quote,
        "管勾二员中一员带同字。", quota=1, staff_type="同管勾官",
        office_event="差朝官二员领监事",
        post_event="管勾二员中一员带同字",
    )
    finish(w, touched, "整理同管勾国子监公事与管勾二员编制链。")


def entry759():
    i = 759
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    source = node(w, touched, i, "判国子监事", "官职", "北宋端拱二年二月",
                  "随国子监改称国子学而改称判国子学事", main,
                  "国子监差遣", "建立判国子监事端拱改称节点。")
    target = node(w, touched, i, "判国子学事", "官职", "北宋端拱二年二月",
                  "由判国子监事改称，职事相同", main,
                  "国子学差遣", "建立判国子学事改称节点。")
    relation(w, i, source, target, "前后演变", main,
             "端拱二年国子监改国子学，判监事改称判国子学事。")
    ending = node(w, touched, i, "判国子学事", "官职",
                  "北宋淳化五年三月二十四日", "随国子学复称国子监而复名判国子监事",
                  main, "国子学差遣", "建立判国子学事淳化复名节点。")
    restored = node(w, touched, i, "判国子监事", "官职",
                    "北宋淳化五年三月二十四日", "由判国子学事复名，职事不变",
                    main, "国子监差遣", "建立判国子监事淳化复名节点。")
    relation(w, i, ending, restored, "前后演变", main,
             "淳化五年国子学复称国子监，判国子学事复称判国子监事。")
    school = node(w, touched, i, "国子学", "机构", "北宋端拱二年二月",
                  "管理机构与学校合一", main, "中央教育管理机构兼官学",
                  "复用国子学端拱节点。")
    staff(w, i, school, target, main, "判国子学事领国子学管理机构事务。",
          staff_type="判学官")
    alias_note(w, i, target, aliases, "简称")
    finish(w, touched, "整理判国子学事在端拱至淳化间的两次改称与编制链。")


def entry760():
    i = 760
    main = F[i]["text"]
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("战国", "荀子在齐三为祭酒，祭酒称谓职源"),
        ("西晋咸宁四年", "国子祭酒之名始见"),
        ("隋大业三年", "国子监祭酒之官始置"),
        ("宋前期", "存其名而不常除人"),
        ("北宋元丰新制", "正名后始常除人，为国子监长官"),
        ("南宋初", "罢置"),
        ("南宋绍兴十二年十二月十二日", "复置"),
    ):
        node(w, touched, i, "国子监祭酒", "官职", time, event, origin,
             "国子监长官", f"建立国子监祭酒{time}沿革节点。", "职源与沿革",
             officer="职事官")
    duty_tp = node(w, touched, i, "国子监祭酒", "官职", "北宋元丰新制",
                   "为国子监长官，掌诸学政令与教法", duty,
                   "国子监长官", "补证祭酒职掌。", "职掌", officer="职事官",
                   grade="从四品")
    rank_early = node(w, touched, i, "国子监祭酒", "官职", "宋初",
                      "依唐制为从三品", rank, "国子监长官",
                      "建立祭酒宋初品位节点。", "品位", grade="从三品")
    rank_reform = node(w, touched, i, "国子监祭酒", "官职", "北宋元丰新制",
                       "改制后从四品，位九卿下、诸寺大监上", rank,
                       "国子监长官", "建立祭酒元丰品位节点。", "品位",
                       grade="从四品")
    office_staff(w, touched, i, "国子监", "国子监祭酒", "北宋元丰新制",
                 roster, "国子监祭酒编制一人。", "编制", quota=1,
                 staff_type="祭酒", office_event="设置祭酒一人",
                 post_event="为国子监长官，编制一人", grade="从四品")
    alias_note(w, i, duty_tp, aliases, "简称与别名")
    finish(w, touched, "整理国子监祭酒前代职源、宋代罢复、职掌、品位与编制链。")


def main():
    for i in range(741, 761):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
