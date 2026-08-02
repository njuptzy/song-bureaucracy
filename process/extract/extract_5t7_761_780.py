#!/usr/bin/env python3
"""提取 chapter5t7 第761-780条：国子监官属、国子学与三窠。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_741_760 as previous


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


F = {i: load(i) for i in range(761, 781)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
state = base.state
relation = base.relation
staff = base.staff
cite = base.cite
alias_note = base.alias_note


TIME_HINTS = {
    "战国": -300, "西汉": -200, "西汉武帝建元五年": -136,
    "西晋咸宁四年": 278, "北齐": 550, "隋初": 590,
    "隋大业三年": 607, "隋唐": 700, "唐初": 618,
    "宋初": 960, "宋前期": 970, "北宋前期": 970,
    "北宋太平兴国八年": 983, "北宋淳化五年二月十六日": 994.13,
    "北宋淳化五年三月十六日": 994.2, "北宋淳化五年": 994.3,
    "北宋至道二年": 996, "北宋真宗大中祥符间": 1010,
    "北宋真宗天禧十月": 1017.8, "北宋景祐二年": 1035,
    "北宋景祐二年三月十三日": 1035.2, "北宋庆历四年": 1044,
    "北宋庆历四年四月二十一日": 1044.3,
    "北宋皇祐四年五月": 1052.4, "北宋熙宁四年": 1071,
    "北宋元丰元年": 1078, "北宋元丰二年": 1079,
    "北宋元丰三年正月十七日": 1080.05,
    "北宋元丰三年二月九日": 1080.12, "北宋元丰新制": 1082,
    "北宋元丰五年改制前": 1082.2, "北宋元丰寄禄格": 1082.3,
    "北宋元丰八年": 1085, "北宋元祐元年闰二月": 1086.18,
    "北宋元祐元年七月十三日": 1086.55, "北宋绍圣四年二月": 1097.15,
    "北宋元符元年": 1098, "北宋元符二年": 1099,
    "北宋元符三年十一月二十七日": 1100.9,
    "北宋崇宁元年七月二十八日": 1102.55, "北宋崇宁二年": 1103,
    "北宋大观元年三月二十四日": 1107.2,
    "北宋大观三年八月十二日": 1109.65,
    "北宋大观四年八月十二日": 1110.65,
    "南宋初": 1127.05, "南宋建炎三年四月十三日": 1129.3,
    "南宋建炎三年四月": 1129.31,
    "南宋绍兴三年六月二十四日": 1133.48,
    "南宋绍兴十二年十二月": 1142.9,
    "南宋绍兴十三年五月十六日": 1143.4,
    "南宋绍兴十三年七月四日": 1143.55,
    "南宋绍兴三十一年": 1161, "南宋隆兴元年": 1163,
    "南宋乾道七年": 1171, "南宋前期": 1150,
    "南宋庆元时": 1195, "南宋": 1130,
    "宋代（未载具体年月）": 1100,
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
    rid = staff(w, i, office_tid, post_tid, quotation, decision, field_name,
                quota=quota, staff_type=staff_type)
    return office_tid, post_tid, rid


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


def evolution(w, touched, i, source_title, target_title, type_, time,
              quotation, decision, field_name=None, *, source_event=None,
              target_event=None):
    source_tid = node(
        w, touched, i, source_title, type_, time,
        source_event or f"改为{target_title}", quotation, "演变前",
        f"建立或复用{source_title}{time}演变节点。", field_name,
    )
    target_tid = node(
        w, touched, i, target_title, type_, time,
        target_event or f"由{source_title}改置", quotation, "演变后",
        f"建立或复用{target_title}{time}演变节点。", field_name,
    )
    relation(w, i, source_tid, target_tid, "前后演变", quotation,
             decision, field_name)
    return source_tid, target_tid


def group_members(w, touched, i, group_title, time, members, quotation,
                  decision):
    group_tid = node(
        w, touched, i, group_title, "官职", time,
        f"{group_title}为五类经学博士合称", quotation, "官职统称",
        f"建立{group_title}{time}统称节点。",
    )
    for title in members:
        member_tid = node(
            w, touched, i, title, "官职", time,
            f"{group_title}所指经学博士之一", quotation, "官职实例",
            f"建立或复用{title}{time}实例节点。",
        )
        relation(w, i, group_tid, member_tid, "统称与实例", quotation,
                 f"原文将{title}列为{group_title}实例。")
    return group_tid


def entry761():
    i = 761
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("隋大业三年", "始置"), ("宋初", "沿置"),
        ("南宋初", "罢置"), ("南宋绍兴十二年十二月", "复置"),
    ):
        node(w, touched, i, "国子监司业", "官职", time, event, origin,
             "国子监副长官", f"建立国子监司业{time}沿革节点。", "职源与沿革")
    office_staff(
        w, touched, i, "国子监", "国子监司业", "北宋元丰新制", roster,
        "国子监司业编制一人。", "编制",
        quota=1, staff_type="司业", office_event="设置司业一人",
        post_event="国子监副长官，编制一人", grade="正六品",
    )
    node(w, touched, i, "国子监司业", "官职", "北宋元丰新制",
         "副长官，佐祭酒总领诸学政令与教法", duty, "国子监副长官",
         "补证国子监司业职掌。", "职掌", grade="正六品")
    rank_tp = node(
        w, touched, i, "国子监司业", "官职", "北宋元丰新制",
        "正六品，班位在七寺少卿下、诸寺监与都水使者上", rank,
        "国子监副长官", "补证司业元丰品位与班序。", "品位", grade="正六品",
    )
    alias_note(w, i, rank_tp, aliases, "简称与别名")
    finish(w, touched, "整理国子监司业始置、宋代罢复、职掌、品位与编制链。")


def entry762():
    i = 762
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("隋大业三年", "始置"), ("宋初", "沿置，兼有迁转官阶性质"),
        ("北宋景祐二年", "始以直讲官一员兼监丞，成为职事官"),
        ("南宋建炎三年四月十三日", "罢置"),
        ("南宋绍兴十二年十二月", "复置"),
    ):
        node(w, touched, i, "国子监丞", "官职", time, event, origin,
             "国子监属官", f"建立国子监丞{time}沿革节点。", "职源与沿革")
    office_staff(
        w, touched, i, "国子监", "国子监丞", "北宋景祐二年", origin,
        "景祐二年始以本监直讲官一员兼监丞。", "职源与沿革",
        quota=1, staff_type="丞", office_event="始置兼任监丞一员",
        post_event="由本监直讲官一员兼任",
    )
    office_staff(
        w, touched, i, "国子监", "国子监丞", "北宋元丰新制", roster,
        "元丰新制国子监丞编制一人。", "编制",
        quota=1, staff_type="丞", office_event="元丰正名后置丞一人",
        post_event="国子监丞编制一人", grade="正八品",
    )
    node(w, touched, i, "国子监丞", "官职", "宋前期",
         "或为迁转官阶，或由本监学官兼任并领钱谷出纳", duty,
         "国子监属官", "补证国子监丞宋前期职掌。", "职掌")
    node(w, touched, i, "国子监丞", "官职", "北宋元丰新制",
         "元丰正名后参领本监事", duty, "国子监属官",
         "补证国子监丞元丰职掌。", "职掌", grade="正八品")
    rank_tp = node(
        w, touched, i, "国子监丞", "官职", "北宋元丰新制",
        "正八品，班位在七寺丞下、诸寺监丞上", rank, "国子监属官",
        "补证国子监丞元丰品位与班序。", "品位", grade="正八品",
    )
    alias_note(w, i, rank_tp, aliases, "简称与别名")
    finish(w, touched, "整理国子监丞官阶与职事官演变、罢复、职掌及品位链。")


def entry763():
    i = 763
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("北齐", "国子寺已置主簿"), ("隋初", "国子监主簿始置"),
        ("北宋景祐二年三月十三日", "始以本监京朝官兼主簿"),
        ("北宋元丰元年", "省罢"),
        ("北宋元丰三年二月九日", "复置"),
        ("南宋初", "罢置"), ("南宋前期", "后复置，年月未载"),
    ):
        node(w, touched, i, "国子监主簿", "官职", time, event, origin,
             "国子监属官", f"建立国子监主簿{time}沿革节点。", "职源与沿革")
    office_staff(
        w, touched, i, "国子监", "国子监主簿", "北宋元丰三年二月九日", roster,
        "国子监主簿编制一人。", "编制",
        quota=1, staff_type="主簿", office_event="复置主簿一人",
        post_event="复置主簿一人", grade="从八品",
    )
    node(w, touched, i, "国子监主簿", "官职", "北宋元丰三年二月九日",
         "掌文书簿籍并勾考出入有无稽违", duty, "国子监属官",
         "补证国子监主簿职掌。", "职掌", grade="从八品")
    rank_tp = node(
        w, touched, i, "国子监主簿", "官职", "北宋元丰新制",
        "从八品，位在诸学博士下、国子监正与太学正上", rank,
        "国子监属官", "补证主簿元丰品位与班序。", "品位", grade="从八品",
    )
    alias_note(w, i, rank_tp, aliases, "简称与别名")
    finish(w, touched, "整理国子监主簿前代职源、景祐始兼、元丰与南宋罢复链。")


def entry764():
    i = 764
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("战国", "齐、魏均置博士，为职源"),
        ("西晋咸宁四年", "初置国子博士"),
        ("隋大业三年", "始置国子监博士"),
        ("宋初", "沿置，但仅为文官迁转官阶，无职守"),
        ("北宋元丰新制", "新制不置国子博士"),
        ("北宋大观元年三月二十四日", "始置职事官国子博士"),
        ("北宋大观三年八月十二日", "省罢，由太学博士兼"),
        ("南宋建炎三年四月", "罢置"),
        ("南宋绍兴三年六月二十四日", "复置"),
    ):
        node(w, touched, i, "国子监博士", "官职", time, event, origin,
             "国子监学官", f"建立国子监博士{time}沿革节点。", "职源与沿革")
    evolution(
        w, touched, i, "国子监博士", "承议郎", "官职", "北宋元丰寄禄格",
        duty, "元丰寄禄格将无职守的国子监博士阶官易为承议郎。", "职掌",
        source_event="作为迁转阶官至元丰改换寄禄官",
        target_event="承接国子监博士寄禄阶官",
    )
    office_staff(
        w, touched, i, "国子监", "国子监博士", "北宋大观元年三月二十四日",
        duty, "大观元年始置职事官，训导国子生与随行亲生员。", "职掌",
        staff_type="博士", office_event="始置职事官国子博士",
        post_event="专掌训导国子生、随行亲生员",
    )
    office_staff(
        w, touched, i, "国子监", "太学博士", "北宋大观三年八月十二日",
        origin, "大观三年省国子博士，由太学博士兼其职。", "职源与沿革",
        staff_type="兼国子博士职", office_event="省国子博士，改由太学博士兼",
        post_event="兼领国子博士职事",
    )
    rank_tp = node(
        w, touched, i, "国子监博士", "官职", "南宋庆元时",
        "正八品；南宋前期曾为从八品", rank, "国子监学官",
        "整理国子监博士宋代品位变化。", "品位", grade="正八品",
    )
    alias_note(w, i, rank_tp, aliases, "简称")
    finish(w, touched, "整理国子监博士阶官至职事官演变、罢复、兼领与品位链。")


def entry765():
    i, quote = 765, F[765]["text"]
    w, touched = W(i), set()
    members = ("《春秋》博士", "《礼记》博士", "《毛诗》博士", "《尚书》博士", "《周易》博士")
    group_members(w, touched, i, "五经博士", "宋初", members, quote,
                  "原文明确五类经学博士合称五经博士。")
    for time, event in (
        ("西汉武帝建元五年", "始置五经博士"),
        ("宋初", "沿唐制存名，班位在国子博士下、都水监使者上"),
        ("北宋淳化二年十一月", "奏请置国子学五经博士，未见除授"),
        ("北宋真宗天禧十月", "再次奏请设置，未见除授"),
    ):
        node(w, touched, i, "五经博士", "官职", time, event, quote,
             "经学博士统称", f"建立五经博士{time}沿革节点。")
    evolution(
        w, touched, i, "五经博士", "国子监直讲", "官职", "宋初", quote,
        "宋代五经博士未见实际除授，其职事实由国子监直讲替代。",
        source_event="存名而未见除授，职事由直讲替代",
        target_event="实际承担五经讲授职事",
    )
    finish(w, touched, "整理五经博士合称、五个实例、宋代存名未授及职事替代链。")


def entry766():
    i = 766
    main, origin, duty, rank, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("西汉", "已置"),
        ("北宋元丰八年", "奏请于太学设置，未获准且奏请者受罚"),
        ("北宋元祐元年闰二月", "礼部请置"),
        ("北宋元祐元年七月十三日", "始除人"),
        ("北宋绍圣四年二月", "随春秋科罢置"),
        ("北宋元符元年", "复置"), ("北宋元符二年", "又罢"),
        ("北宋元符三年十一月二十七日", "复置"),
        ("北宋崇宁元年七月二十八日", "罢置"),
    ):
        node(w, touched, i, "《春秋》博士", "官职", time, event, origin,
             "太学经学博士", f"建立《春秋》博士{time}沿革节点。", "职源与沿革")
    _, _, rid = office_staff(
        w, touched, i, "太学", "《春秋》博士", "北宋元祐元年七月十三日",
        roster, "《春秋》博士编制二员。", "编制",
        quota=2, staff_type="博士", office_event="设置《春秋》博士二员",
        post_event="编制二员", grade="从八品",
    )
    cite(w, "Relationships", rid, i, main,
         "本条正文明确《春秋》博士隶太学。")
    node(w, touched, i, "《春秋》博士", "官职", "北宋元祐元年七月十三日",
         "掌讲解《春秋》经", duty, "太学经学博士",
         "补证《春秋》博士职掌。", "职掌", grade="从八品")
    node(w, touched, i, "《春秋》博士", "官职", "北宋元祐元年七月十三日",
         "为太学博士之一，从八品", rank, "太学经学博士",
         "补证《春秋》博士品位。", "品位", grade="从八品")
    finish(w, touched, "整理《春秋》博士太学隶属、元祐至崇宁屡罢屡复及品位链。")


def entry767():
    i, quote = 767, F[767]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "御书院", "国子书博士", "北宋太平兴国八年", quote,
        "国子书博士为御书院临时祇应官，仅授善篆者一人，不隶国子监。",
        quota=1, staff_type="祇应官", office_event="临时设置善书祇应一人",
        post_event="非品官，权借国子之名，授御书院善书祇应人",
    )
    node(w, touched, i, "国子书博士", "官职", "北宋太平兴国八年",
         "仅除一人，后不复设；明确不隶国子监", quote, "御书院临时祇应官",
         "补证该官仅一人且后不复设。")
    finish(w, touched, "整理国子书博士临时设置、御书院隶属及不隶国子监边界。")


def entry768():
    i = 768
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "国子监说书", "北宋庆历四年", aliases,
        "庆历四年国子监说书以四员为额。", "简称",
        quota=4, staff_type="说书", office_event="说书官定额四员",
        post_event="选人经试充任，位次国子监直讲", officer="选人",
    )
    ending = node(
        w, touched, i, "国子监说书", "官职", "北宋元丰新制",
        "元丰新制后不置", main, "国子监学官", "建立说书元丰罢置节点。",
        officer="选人",
    )
    alias_note(w, i, ending, aliases, "简称")
    finish(w, touched, "整理国子监说书资格、庆历定额、位次与元丰罢置链。")


def entry769():
    i = 769
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    evolution(
        w, touched, i, "国子学讲书", "国子监讲书", "官职",
        "北宋淳化五年三月十六日", main,
        "淳化五年国子学讲书改称国子监讲书。",
        source_event="国子学所置讲书，随机构复名而改称",
        target_event="由国子学讲书改称",
    )
    office_staff(
        w, touched, i, "国子监", "国子监讲书", "北宋真宗大中祥符间", main,
        "大中祥符间复置讲书，以通经术、能讲解的选人充。",
        staff_type="讲书", office_event="复置讲书",
        post_event="位次直讲，以通经术能讲解的选人充", officer="选人",
    )
    evolution(
        w, touched, i, "国子监讲书", "国子监直讲", "官职",
        "北宋真宗大中祥符间", main, "国子监讲书递迁国子监直讲。",
        source_event="可递迁直讲", target_event="由讲书递迁",
    )
    target = node(
        w, touched, i, "国子监讲书", "官职", "北宋真宗大中祥符间",
        "位次直讲，以通经术能讲解的选人充", main, "国子监学官",
        "复用讲书大中祥符职事节点。", officer="选人",
    )
    alias_note(w, i, target, aliases, "简称")
    finish(w, touched, "整理国子监讲书淳化改称、大中祥符复置、资格与递迁链。")


def entry770():
    i = 770
    origin, duty, officer_q, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    node(w, touched, i, "国子监直讲", "官职", "唐初", "始置直讲", origin,
         "国子监学官", "建立直讲唐代职源节点。", "职源与沿革")
    evolution(
        w, touched, i, "国子学讲书", "国子监直讲", "官职",
        "北宋淳化五年二月十六日", origin,
        "本条记载淳化五年国子学讲书改为国子监直讲。", "职源与沿革",
        source_event="改为国子监直讲",
        target_event="由国子学讲书改置",
    )
    evolution(
        w, touched, i, "国子监直讲", "太学博士", "官职",
        "北宋元丰三年正月十七日", origin,
        "元丰三年国子监直讲改为太学博士。", "职源与沿革",
        source_event="元丰三年改为太学博士",
        target_event="由国子监直讲改置",
    )
    for time, quota in (("北宋至道二年", 10), ("北宋熙宁四年", 10)):
        office_staff(
            w, touched, i, "国子监", "国子监直讲", time, roster,
            f"{time}国子监直讲置十人，每二人共讲一经。", "编制",
            quota=quota, staff_type="直讲", office_event="直讲定额十人",
            post_event="每二人共讲一经，掌教授诸经",
        )
    duty_tp = node(
        w, touched, i, "国子监直讲", "官职", "北宋皇祐四年五月",
        "掌教授诸经，每二人共讲一经，亦可临时充贡院试官",
        duty, "国子监学官", "整理直讲职掌。", "职掌",
        officer="通经术、有德行且年四十以上的京官或选人",
    )
    node(w, touched, i, "国子监直讲", "官职", "北宋皇祐四年五月",
         "须年满四十、有老成之器且堪为监生表率；选人到监五年改京官",
         officer_q, "国子监学官", "整理皇祐后直讲任职资格。", "品位",
         officer="通经术、有德行且年四十以上的京官或选人")
    alias_note(w, i, duty_tp, aliases, "简称与别名")
    finish(w, touched, "整理国子监直讲唐代职源、淳化改置、元丰改太学博士及编制链。")


def entry771():
    i = 771
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("北宋大观元年三月二十四日", "始置"),
        ("南宋建炎三年四月十三日", "罢置"),
        ("南宋绍兴十三年五月十六日", "复置"),
    ):
        node(w, touched, i, "国子监正", "官职", time, event, origin,
             "国子监学官", f"建立国子监正{time}沿革节点。", "职源与沿革")
    office_staff(
        w, touched, i, "国子监", "国子监正", "南宋绍兴十三年五月十六日",
        roster, "国子监正编制二员或一员。", "编制",
        staff_type="学正", office_event="复置国子监正",
        post_event="编制二员或一员不定", grade="正九品",
    )
    node(w, touched, i, "国子监正", "官职", "南宋绍兴十三年五月十六日",
         "掌执行学规并按五等罚处理违章国子学生", duty, "国子监学官",
         "补证国子监正职掌。", "职掌", grade="正九品")
    rank_tp = node(
        w, touched, i, "国子监正", "官职", "南宋",
        "正九品，位在五监主簿下、武学谕与律学正上", rank,
        "国子监学官", "补证国子监正南宋品位与班序。", "品位", grade="正九品",
    )
    alias_note(w, i, rank_tp, aliases, "简称")
    finish(w, touched, "整理国子监正大观始置、南宋罢复、职掌与品位链。")


def entry772():
    i = 772
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("北齐", "国子寺已有录事，为职源"),
        ("隋唐", "国子监置录事，为职源"),
        ("北宋大观元年三月二十四日", "始称国子监录"),
        ("南宋建炎三年四月十三日", "罢置"),
        ("南宋绍兴十三年五月十六日", "复置"),
    ):
        node(w, touched, i, "国子监录", "官职", time, event, origin,
             "国子监学官", f"建立国子监录{time}沿革节点。", "职源与沿革")
    office_staff(
        w, touched, i, "国子监", "国子监录", "南宋绍兴十三年五月十六日",
        roster, "国子监录编制二员或一员。", "编制",
        staff_type="学录", office_event="复置国子监录",
        post_event="编制二员或一员不定", grade="正九品",
    )
    node(w, touched, i, "国子监录", "官职", "南宋绍兴十三年五月十六日",
         "佐国子监正纠察国子学生不守学规者", duty, "国子监学官",
         "补证国子监录职掌。", "职掌", grade="正九品")
    rank_tp = node(
        w, touched, i, "国子监录", "官职", "南宋",
        "正九品，位在国子正、太学正、武学谕下，律学正、太医局丞上",
        rank, "国子监学官", "补证国子监录南宋品位与班序。", "品位",
        grade="正九品",
    )
    alias_note(w, i, rank_tp, aliases, "简称与别名")
    finish(w, touched, "整理国子监录前代录事职源、大观始称、南宋罢复及职掌链。")


def entry773():
    i = 773
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    evolution(
        w, touched, i, "国子监印书钱物所", "国子监书库", "机构",
        "北宋淳化五年", origin, "淳化五年印书钱物所改为国子监书库。",
        "职源与沿革", source_event="改为国子监书库",
        target_event="由印书钱物所改置",
    )
    for time, event in (
        ("北宋淳化五年", "随国子监书库改置始置监书库官"),
        ("北宋元丰三年二月九日", "罢置"), ("北宋崇宁二年", "复置"),
        ("北宋大观四年八月十二日", "罢置"),
        ("南宋绍兴十三年七月四日", "复置"),
        ("南宋绍兴三十一年", "减一员"),
        ("南宋隆兴元年", "改由国子监主簿兼任"),
        ("南宋乾道七年", "复单置一员"),
    ):
        node(w, touched, i, "监国子监书库", "官职", time, event, origin,
             "国子监书库差遣", f"建立监国子监书库{time}沿革节点。", "职源与沿革")
    for time, quota, event in (
        ("南宋绍兴十三年七月四日", None, "复置书库官"),
        ("南宋绍兴三十一年", 1, "减为一员"),
        ("南宋乾道七年", 1, "复单置一员"),
    ):
        office_staff(
            w, touched, i, "国子监书库", "监国子监书库", time, duty,
            f"{time}{event}，掌雕印、校书、颁卖书籍。", "职掌",
            quota=quota, staff_type="书库官", office_event=event,
            post_event="掌雕印校定、颁发出卖书籍并收利纳左藏库",
            officer="选人" if time.startswith("南宋") else None,
        )
    office_staff(
        w, touched, i, "国子监书库", "国子监主簿", "南宋隆兴元年", origin,
        "隆兴元年国子监主簿兼书库官。", "职源与沿革",
        quota=1, staff_type="兼书库官", office_event="书库官由主簿兼任",
        post_event="兼领国子监书库事务",
    )
    rank_tp = node(
        w, touched, i, "监国子监书库", "官职", "宋代（未载具体年月）",
        "北宋多由京官或朝官充，南宋多由选人充", rank,
        "国子监书库差遣", "整理书库官任职官资。", "品位",
    )
    alias_note(w, i, rank_tp, aliases, "简称与别名")
    finish(w, touched, "整理监国子监书库机构改名、历次罢复、主簿兼领与编制链。")


def entry774():
    i, quote = 774, F[774]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监公厨", "监国子监公厨",
        "宋代（未载具体年月）", quote, "监国子监公厨掌本监公厨公事。",
        staff_type="监厨官", office_event="设置监厨差遣",
        post_event="由使臣充，掌本监公厨", officer="使臣",
    )
    office_staff(
        w, touched, i, "武学厨", "监国子监公厨",
        "宋代（未载具体年月）", quote, "监国子监公厨兼监武学厨。",
        staff_type="兼监厨官", office_event="由国子监公厨官兼监",
        post_event="兼监武学厨", officer="使臣",
    )
    finish(w, touched, "整理监国子监公厨本职、使臣资格及兼监武学厨关系。")


def entry775():
    i, quote = 775, F[775]["text"]
    w, touched = W(i), set()
    for time, event in (
        ("西晋咸宁四年", "始置国子学助教"),
        ("隋唐", "置国子监助教"), ("宋初", "沿置"),
        ("北宋元丰新制", "新制不置"),
    ):
        node(w, touched, i, "国子监助教", "官职", time, event, quote,
             "国子监学官", f"建立国子监助教{time}沿革节点。")
    office_staff(
        w, touched, i, "国子监", "国子监助教", "宋初", quote,
        "宋初国子监沿置助教。", staff_type="助教",
        office_event="沿置助教", post_event="隶国子监的学官",
    )
    finish(w, touched, "整理国子监助教西晋职源、隋唐沿革、宋初隶属及元丰罢置链。")


def entry776():
    i = 776
    origin, function, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    node(w, touched, i, "国子学", "机构", "西晋咸宁四年", "初立", origin,
         "中央官学", "建立国子学西晋职源节点。", "职源与沿革")
    parent_child(
        w, touched, i, "国子监", "国子学", "隋大业三年", origin,
        "隋代国子学为国子监所辖诸学之一。", "职源与沿革",
        parent_event="统辖国子学等诸学", child_event="隶国子监",
    )
    node(w, touched, i, "国子学", "机构", "宋初",
         "与国子监合二为一，两名通用，兼为官学与官司", origin,
         "中央官学兼官司", "建立宋初国子学监学合一节点。", "职源与沿革")
    parent_child(
        w, touched, i, "国子监", "国子学", "北宋庆历四年四月二十一日",
        origin, "庆历四年后国子学从国子监分离后成为所辖诸学之一。",
        "职源与沿革", parent_event="统辖分离后的国子学",
        child_event="与国子监分离，作为独立官学",
    )
    parent_child(
        w, touched, i, "太学", "国子学", "北宋庆历四年四月二十一日",
        origin, "庆历四年后国子学地位下降，置于太学之内。", "职源与沿革",
        parent_event="内置国子学", child_event="置于太学之内并向太学化演变",
    )
    evolution(
        w, touched, i, "国子学", "太学", "机构", "南宋", origin,
        "南宋已无国子学之名，国子生附于太学。", "职源与沿革",
        source_event="名称消失，国子生并入太学系统",
        target_event="承接南宋国子生教育",
    )
    for time, quota, office, event in (
        ("宋初", 70, "国子学", "系籍国子生，招七品以上官僚子弟"),
        ("北宋元丰二年", 200, "国子学", "《学令》定国子学生二百员"),
        ("南宋", 80, "太学", "国子生八十人为额，附于太学"),
    ):
        office_staff(
            w, touched, i, office, "国子生", time, roster,
            f"{time}{event}。", "编制", quota=quota, staff_type="学生",
            office_event=event, post_event=event,
        )
    function_tp = node(
        w, touched, i, "国子学", "机构", "北宋庆历四年四月二十一日",
        "招收官僚子弟、命官清要官亲戚及随行亲生员，掌训导荐送",
        function, "国子监所属官学", "整理庆历后国子学招生对象与职能。", "职能",
    )
    alias_note(w, i, function_tp, aliases, "简称")
    finish(w, touched, "整理国子学前代职源、宋初监学合一、庆历分离、南宋并入太学及生额链。")


def entry777():
    i, quote = 777, F[777]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "国子监", "学窠", "南宋", quote,
        "学窠为南宋国子监办事机构。",
        parent_event="设置学窠办理学校考试事务",
        child_event="掌文武学公私试、发解试及升补考选行艺",
    )
    finish(w, touched, "整理学窠正式词头、南宋国子监隶属与职掌。")


def entry778():
    i, quote = 778, F[778]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "国子监", "厨库窠", "南宋", quote,
        "厨库窠为南宋国子监办事机构。",
        parent_event="设置厨库窠办理钱粮书籍事务",
        child_event="掌太学钱粮、书籍及学制学令条册",
    )
    finish(w, touched, "整理厨库窠正式词头、南宋国子监隶属与职掌。")


def entry779():
    i, quote = 779, F[779]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "国子监", "知杂窠", "南宋", quote,
        "知杂窠为南宋国子监办事机构。",
        parent_event="设置知杂窠办理杂务",
        child_event="掌本监及诸学杂务",
    )
    finish(w, touched, "整理知杂窠正式词头、南宋国子监隶属与职掌。")


def entry780():
    i, quote = 780, F[780]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "胥长", "宋代（未载具体年月）", quote,
        "国子监置胥长一人，为吏人最高位，承办行遣。",
        quota=1, staff_type="吏", office_event="设置胥长一人",
        post_event="吏人位次最高，供行遣文字并承办公事",
    )
    evolution(
        w, touched, i, "胥史", "胥长", "官职", "宋代（未载具体年月）",
        quote, "国子监胥长由胥史递迁。",
        source_event="递迁为胥长", target_event="由胥史递迁",
    )
    finish(w, touched, "整理胥长在国子监的吏额、职掌及由胥史递迁关系。")


def main():
    for i in range(761, 781):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
