#!/usr/bin/env python3
"""提取 chapter5t7 第781-800条：国子监胥吏、三京国子监与太学系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_761_780 as previous


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


F = {i: load(i) for i in range(781, 801)}
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
    "西汉武帝时": -140, "西汉": -120, "东晋": 320,
    "北魏": 450, "隋朝": 600, "隋唐": 700,
    "宋初": 960, "宋初礼部科举试期间": 965,
    "北宋初": 970, "北宋仁宗朝": 1022, "北宋皇祐间": 1050,
    "北宋皇祐二年七月": 1050.55, "北宋皇祐三年": 1051,
    "北宋嘉祐间": 1057, "北宋嘉祐元年十一月十五日": 1056.88,
    "北宋嘉祐三年七月": 1058.55, "北宋嘉祐四年": 1059,
    "北宋景德四年二月八日": 1007.10,
    "北宋景祐元年五月十三日": 1034.36,
    "北宋庆历三年十二月二十五日": 1043.96,
    "北宋庆历四年四月二十一日": 1044.30,
    "北宋熙宁元年正月": 1068.02,
    "北宋熙宁二年十二月二十四日": 1069.95,
    "北宋熙宁四年十月": 1071.80,
    "北宋熙宁五年": 1072,
    "北宋元丰二年八月": 1079.62,
    "北宋元丰三年正月十七日": 1080.05,
    "北宋元丰新制": 1082,
    "北宋崇宁元年八月": 1102.62,
    "北宋崇宁三年": 1104,
    "北宋崇宁四年七月一日": 1105.52,
    "北宋宣和元年": 1119, "北宋宣和三年三月九日": 1121.20,
    "南宋初": 1127, "南宋绍兴十二年十二月": 1142.94,
    "南宋绍兴十二年十二月十二日": 1142.95,
    "南宋绍兴十三年二月二十三日": 1143.13,
    "南宋绍兴十三年六月十九日": 1143.47,
    "南宋绍兴十三年七月": 1143.55,
    "南宋绍兴十五年": 1145, "南宋绍兴十六年正月": 1146.04,
    "南宋绍兴三十一年六月": 1161.47,
    "南宋乾道二年二月八日": 1166.10,
    "南宋度宗咸淳三年": 1267,
    "宋代（未载具体年月）": 1100,
    "北宋真宗、仁宗朝以后": 1020,
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
    rid = staff(
        w, i, office_tid, post_tid, quotation, decision, field_name,
        quota=quota, staff_type=staff_type,
    )
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
    relation(
        w, i, parent_tid, child_tid, "上下级机构", quotation,
        decision, field_name,
    )
    return parent_tid, child_tid


def evolution(w, touched, i, source_title, target_title, time, quotation,
              decision, field_name=None, *, source_event=None,
              target_event=None):
    source_tid = node(
        w, touched, i, source_title, "官职", time,
        source_event or f"递迁为{target_title}", quotation, "演变前",
        f"建立或复用{source_title}{time}演变节点。", field_name,
    )
    target_tid = node(
        w, touched, i, target_title, "官职", time,
        target_event or f"由{source_title}递迁", quotation, "演变后",
        f"建立或复用{target_title}{time}演变节点。", field_name,
    )
    relation(
        w, i, source_tid, target_tid, "前后演变", quotation,
        decision, field_name,
    )
    return source_tid, target_tid


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
        relation(
            w, i, group_tid, member_tid, "统称与实例", quotation,
            f"{member_title}是{group_title}的实例。", field_name,
        )
    return group_tid


def entry781():
    i, quote = 781, F[781]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "胥史", "宋代（未载具体年月）", quote,
        "国子监置胥史一人，供行遣文字及承办公事。",
        quota=1, staff_type="吏", office_event="设置胥史一人",
        post_event="位次胥长，供行遣文字及承办公事",
    )
    evolution(
        w, touched, i, "胥佐", "胥史", "宋代（未载具体年月）", quote,
        "国子监胥史由胥佐递迁。",
    )
    finish(w, touched, "整理胥史在国子监的位次、职掌、吏额及递迁关系。")


def entry782():
    i, quote = 782, F[782]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "胥佐", "宋代（未载具体年月）", quote,
        "国子监置胥佐六人，位次胥史。",
        quota=6, staff_type="吏", office_event="设置胥佐六人",
        post_event="位次胥史，供行遣文字及承办公事",
    )
    finish(w, touched, "整理胥佐在国子监的位次、职掌和六人吏额。")


def entry783():
    i, quote = 783, F[783]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "贴书", "宋代（未载具体年月）", quote,
        "国子监置贴书六人，供书写文字。",
        quota=6, staff_type="吏", office_event="设置贴书六人",
        post_event="供书写文字",
    )
    finish(w, touched, "整理贴书在国子监的书写职掌及六人吏额。")


def entry784():
    i, quote = 784, F[784]["text"]
    w, touched = W(i), set()
    members = tuple((title, "机构") for title in (
        "西京国子监", "南京国子监", "北京国子监",
    ))
    group_members(
        w, touched, i, "三京国子监", "机构", "北宋真宗、仁宗朝以后",
        "西京、南京、北京分别所置国子监的合称", members, quote,
        "原文明确三京国子监及三处实例。",
    )
    for time, event in (
        ("北宋景德四年二月八日", "西京国子监始置"),
        ("北宋景祐元年五月十三日", "改河南府学为西京国子监"),
    ):
        node(w, touched, i, "西京国子监", "机构", time, event, quote,
             "三京官学", f"建立西京国子监{time}沿革节点。")
    node(
        w, touched, i, "南京国子监", "机构",
        "北宋庆历三年十二月二十五日", "改南京应天府学为国子监",
        quote, "三京官学", "建立南京国子监庆历三年设置节点。",
    )
    for office in ("西京国子监", "南京国子监", "北京国子监"):
        office_staff(
            w, touched, i, office, "判监", "北宋真宗、仁宗朝以后", quote,
            f"{office}置判监官一人。", quota=1, staff_type="判监官",
            office_event="设置判监官一人", post_event=f"判领{office}事",
        )
        office_staff(
            w, touched, i, office, "同判监", "北宋熙宁二年十二月二十四日",
            quote, f"{office}增置同判监官一员。", quota=1,
            staff_type="同判监官", office_event="增置同判监官一员",
            post_event=f"同判{office}事",
        )
        office_staff(
            w, touched, i, office, "国子监司业", "北宋崇宁四年七月一日",
            quote, f"崇宁四年{office}罢判、同判，仅置司业一员。",
            quota=1, staff_type="司业", office_event="罢判、同判，仅置司业一员",
            post_event=f"领{office}事，编制一员",
        )
    finish(w, touched, "整理三京国子监实例、各京设置沿革及判监、同判、司业编制链。")


def entry785():
    i, quote = 785, F[785]["text"]
    w = W(i)
    eid = w.find_entity("西京国子监", "机构")
    assert eid
    tid = w.conn.execute(
        "select id from Timepoints where entity_id=? order by id limit 1", (eid,)
    ).fetchone()[0]
    cite(
        w, "Timepoints", tid, i, quote,
        "西监是西京国子监省称，只补名称证据，不另建实体。",
        note="纯省称不另建实体",
    )
    w.commit()


def entry786():
    i = 786
    main, origin, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别名"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("西汉武帝时", "创置太学"),
        ("隋朝", "始为国子监所属太学"),
        ("北宋庆历四年四月二十一日", "始立太学于锡庆院"),
        ("南宋绍兴十三年七月", "复置太学"),
    ):
        node(w, touched, i, "太学", "机构", time, event, origin,
             "中央官学", f"建立太学{time}沿革节点。", "职源与沿革")
    for time in ("隋朝", "北宋庆历四年四月二十一日", "南宋绍兴十三年七月"):
        parent_child(
            w, touched, i, "国子监", "太学", time,
            origin if time != "北宋庆历四年四月二十一日" else main,
            f"{time}太学隶国子监。",
            "职源与沿革" if time != "北宋庆历四年四月二十一日" else None,
            parent_event="统辖太学", child_event="隶国子监",
        )
    duty_tp = node(
        w, touched, i, "太学", "机构", "北宋宣和元年",
        "恢复科举取士后，专掌训导学生", duty, "中央官学",
        "建立宣和恢复科举后太学职能节点。", "职掌",
    )
    node(
        w, touched, i, "太学", "机构", "北宋崇宁元年八月",
        "以岁试上舍生代替礼部科举试", duty, "中央官学",
        "建立崇宁以太学上舍试代科举节点。", "职掌",
    )
    for post, quota, time in (
        ("太学博士", 10, "北宋元丰三年正月十七日"),
        ("太学博士", 3, "南宋绍兴十二年十二月十二日"),
        ("太学正", 3, "北宋元丰新制"),
        ("太学录", 3, "北宋元丰新制"),
        ("太学正", 1, "南宋绍兴十三年七月"),
        ("太学录", 1, "南宋绍兴十三年七月"),
    ):
        office_staff(
            w, touched, i, "太学", post, time, roster,
            f"太学在{time}置{post}{quota}人。", "编制",
            quota=quota, staff_type="学官", office_event=f"设置{post}{quota}人",
            post_event=f"太学学官，编制{quota}人",
        )
    office_staff(
        w, touched, i, "太学", "太学内舍生",
        "北宋庆历四年四月二十一日", roster,
        "庆历四年初置太学时，太学内舍生二百人为额。", "编制",
        quota=200, staff_type="学生", office_event="设置内舍生二百人",
        post_event="太学内舍生，编制二百人",
    )
    for post, time, quota, office in (
        ("太学上舍生", "北宋熙宁四年十月", 100, "太学"),
        ("太学内舍生", "北宋熙宁四年十月", 200, "太学"),
        ("太学外舍生", "北宋熙宁四年十月", None, "太学"),
        ("太学外舍生", "北宋熙宁五年", 700, "太学"),
        ("太学上舍生", "北宋元丰二年八月", 100, "太学"),
        ("太学内舍生", "北宋元丰二年八月", 300, "太学"),
        ("太学外舍生", "北宋元丰二年八月", 2000, "太学"),
        ("太学上舍生", "北宋崇宁三年", 200, "太学"),
        ("太学内舍生", "北宋崇宁三年", 600, "太学"),
        ("太学外舍生", "北宋崇宁三年", 3000, "辟雍外学"),
        ("太学外舍生", "南宋绍兴十五年", 700, "太学"),
        ("太学内舍生", "南宋绍兴十五年", 100, "太学"),
        ("太学上舍生", "南宋绍兴十五年", 30, "太学"),
        ("太学外舍生", "南宋度宗咸淳三年", 1400, "太学"),
        ("太学内舍生", "南宋度宗咸淳三年", 206, "太学"),
        ("太学上舍生", "南宋度宗咸淳三年", 30, "太学"),
        ("国子生", "南宋度宗咸淳三年", 80, "太学"),
    ):
        office_staff(
            w, touched, i, office, post, time, roster,
            f"原文记载{time}{post}生额。", "编制",
            quota=quota, staff_type="学生", office_event=f"设置{post}",
            post_event=f"{post}编制" + (f"{quota}人" if quota is not None else "不限额"),
        )
    for time, quota in (
        ("南宋绍兴十二年十二月", 200),
        ("南宋绍兴十五年", 830),
        ("南宋绍兴十六年正月", 1000),
        ("南宋度宗咸淳三年", 1716),
    ):
        office_staff(
            w, touched, i, "太学", "太学生", time, roster,
            f"原文记载{time}太学生制度或总额。", "编制",
            quota=quota, staff_type="学生", office_event="太学生制度与生额",
            post_event="在太学就读并按学制升补",
        )
    alias_note(w, i, duty_tp, aliases, "别名")
    finish(w, touched, "整理太学前代职源、宋代建置复置、国子监隶属、职掌、学官与学生编制链。")


def entry787():
    i, quote = 787, F[787]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "太学", "管勾太学公事", "北宋嘉祐间", quote,
        "嘉祐间置管勾太学公事，掌治太学公事。",
        staff_type="差遣", office_event="设置管勾太学公事",
        post_event="掌治太学公事",
    )
    finish(w, touched, "整理管勾太学公事嘉祐间设置、太学隶属与职掌。")


def entry788():
    i, quote = 788, F[788]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "太学", "同管勾太学公事", "北宋嘉祐四年", quote,
        "嘉祐四年管勾告假，由同管勾暂代本学公事。",
        staff_type="暂代差遣", office_event="管勾告假，置同管勾暂代",
        post_event="暂代管勾太学公事",
    )
    finish(w, touched, "整理同管勾太学公事嘉祐四年暂代关系。")


def entry789():
    i, quote = 789, F[789]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "太学", "权管勾太学公事",
        "宋代（未载具体年月）", quote,
        "本条未载具体年月；同管勾告假，由权管勾暂代理太学公事。",
        staff_type="权摄差遣", office_event="同管勾告假，置权管勾暂代",
        post_event="权摄代理太学公事",
    )
    finish(w, touched, "整理权管勾太学公事嘉祐四年权摄关系。")


def entry790():
    i = 790
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("西汉", "博士教授太学生，但博士隶太常，太学博士仅为便称"),
        ("东晋", "始以太学博士命官"),
        ("北宋初", "于太学馆置太学博士"),
        ("北宋元丰三年正月十七日", "由国子监直讲改置"),
        ("南宋初", "罢置"),
        ("南宋绍兴十三年二月二十三日", "复置"),
    ):
        node(w, touched, i, "太学博士", "官职", time, event, origin,
             "太学学官", f"建立太学博士{time}沿革节点。", "职源与沿革",
             grade="从八品" if "宋" in time else None)
    evolution(
        w, touched, i, "国子监直讲", "太学博士",
        "北宋元丰三年正月十七日", origin,
        "元丰三年国子监直讲改为太学博士。", "职源与沿革",
        source_event="改为太学博士", target_event="由国子监直讲改置",
    )
    for time, quota in (
        ("北宋元丰三年正月十七日", 10),
        ("南宋绍兴十二年十二月十二日", 3),
    ):
        _, post_tid, _ = office_staff(
            w, touched, i, "国子监", "太学博士", time, roster,
            f"{time}太学博士编制{quota}人。", "编制",
            quota=quota, staff_type="学官", office_event=f"设置太学博士{quota}人",
            post_event=f"专经教授太学生，编制{quota}人", grade="从八品",
        )
        cite(w, "Timepoints", post_tid, i, duty,
             "补证太学博士教授、考校和训导职掌。", "职掌")
        cite(w, "Timepoints", post_tid, i, rank,
             "补证太学博士从八品及班序。", "品位")
    alias_note(w, i, post_tid, aliases, "简称与别名")
    cite(w, "Timepoints", post_tid, i, main, "正文明确太学博士隶国子监。")
    finish(w, touched, "整理太学博士职源、直讲改置、南宋罢复、职掌、品位与编制链。")


def entry791():
    i = 791
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("北宋皇祐间", "胡瑗掌太学时始见"),
        ("南宋初", "罢置"),
        ("南宋绍兴十二年十二月", "复置"),
        ("南宋绍兴三十一年六月", "罢置"),
        ("南宋乾道二年二月八日", "复置一员"),
    ):
        node(w, touched, i, "太学正", "官职", time, event, origin if time != "南宋绍兴三十一年六月" and time != "南宋乾道二年二月八日" else roster,
             "太学学官", f"建立太学正{time}沿革节点。",
             "职源与沿革" if time not in ("南宋绍兴三十一年六月", "南宋乾道二年二月八日") else "编制",
             grade="正九品")
    for time, quota in (
        ("北宋元丰新制", 5),
        ("北宋宣和元年", 3),
        ("北宋宣和三年三月九日", 5),
        ("南宋绍兴十二年十二月十二日", 1),
        ("南宋乾道二年二月八日", 1),
    ):
        _, post_tid, _ = office_staff(
            w, touched, i, "国子监", "太学正", time, roster,
            f"{time}太学正编制{quota}人。", "编制",
            quota=quota, staff_type="学官", office_event=f"设置太学正{quota}人",
            post_event=f"太学学官，编制{quota}人", grade="正九品",
        )
    cite(w, "Timepoints", post_tid, i, duty,
         "补证太学正施行学规、惩处违犯及考校职掌。", "职掌")
    cite(w, "Timepoints", post_tid, i, rank,
         "补证太学正正九品及班序。", "品位")
    cite(w, "Timepoints", post_tid, i, main, "正文明确太学正隶国子监。")
    alias_note(w, i, post_tid, aliases, "简称")
    finish(w, touched, "整理太学正始见、南宋罢复、职掌、品位和分期编制链。")


def entry792():
    i, quote = 792, F[792]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "职事学正", "北宋仁宗朝", quote,
        "仁宗朝太学正从学生中选充，为无品职事人。",
        staff_type="无品职事人", office_event="从学生中选充职事学正",
        post_event="由学生或上舍生选充，职掌同命官太学正",
        officer="学生或上舍生",
    )
    finish(w, touched, "整理职事学正学生选充、无品、国子监隶属及同太学正职掌。")


def entry793():
    i = 793
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("北宋皇祐间", "胡瑗掌太学时始见"),
        ("南宋初", "罢置"),
        ("南宋绍兴十三年六月十九日", "复置"),
        ("南宋绍兴三十一年六月", "罢置"),
        ("南宋乾道二年二月八日", "复置"),
    ):
        node(w, touched, i, "太学录", "官职", time, event,
             origin if time not in ("南宋绍兴三十一年六月", "南宋乾道二年二月八日") else roster,
             "太学学官", f"建立太学录{time}沿革节点。",
             "职源与沿革" if time not in ("南宋绍兴三十一年六月", "南宋乾道二年二月八日") else "编制",
             grade="正九品")
    for time, quota in (
        ("北宋元丰新制", 5),
        ("北宋宣和元年", 3),
        ("北宋宣和三年三月九日", 5),
        ("南宋绍兴十二年十二月十二日", 1),
        ("南宋乾道二年二月八日", 1),
    ):
        _, post_tid, _ = office_staff(
            w, touched, i, "太学", "太学录", time, roster,
            f"{time}太学录编制{quota}人。", "编制",
            quota=quota, staff_type="学官", office_event=f"设置太学录{quota}人",
            post_event=f"佐太学正纠察、考校，编制{quota}人", grade="正九品",
        )
    cite(w, "Timepoints", post_tid, i, duty,
         "补证太学录纠察与季考后十日考校职掌。", "职掌")
    cite(w, "Timepoints", post_tid, i, rank,
         "补证太学录正九品及班序。", "品位")
    alias_note(w, i, post_tid, aliases, "简称")
    finish(w, touched, "整理太学录始见、南宋罢复、职掌、品位和分期编制链。")


def entry794():
    i, quote = 794, F[794]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "国子监", "职事学录", "北宋熙宁四年十月", quote,
        "熙宁增广太学时，职事学录从上舍生中选充，无品。",
        staff_type="无品职事人", office_event="从上舍生中选充职事学录",
        post_event="从上舍生中选充，无品，职掌同命官太学录",
        officer="太学上舍生",
    )
    office_staff(
        w, touched, i, "国子监", "职事学录", "北宋元丰新制", quote,
        "元丰新制职事学录设五人。", quota=5,
        staff_type="无品职事人", office_event="设置职事学录五人",
        post_event="编制五人，有添支食钱，行艺尤异者可荐为学官",
        officer="太学上舍生",
    )
    finish(w, touched, "整理职事学录学生选充、无品、元丰五人编制及荐为学官条件。")


def entry795():
    i = 795
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    group_tid = group_members(
        w, touched, i, "太学正录", "官职", "宋代（未载具体年月）",
        "太学正、太学录连称", (("太学正", "官职"), ("太学录", "官职")),
        main, "原文明确太学正录是太学正、太学录连称。",
    )
    alias_note(w, i, group_tid, aliases, "简称")
    finish(w, touched, "整理太学正录统称、太学正与太学录两个实例及简称证据。")


def entry796():
    i = 796
    origin, duty, rank = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
    )
    w, touched = W(i), set()
    for time, event, quotation, field_name in (
        ("北魏", "始置", origin, "职源与沿革"),
        ("隋唐", "国子监太学置助教", origin, "职源与沿革"),
        ("北宋皇祐二年七月", "授李觏，未莅职，不理选限，实为散官", duty, "职掌"),
        ("北宋嘉祐元年十一月十五日", "授黄晞，未莅职，后不复置", duty, "职掌"),
    ):
        node(w, touched, i, "太学助教", "官职", time, event, quotation,
             "太学学官名或散官", f"建立太学助教{time}节点。", field_name,
             officer="草泽经术之士" if "北宋" in time else None)
    last = node(
        w, touched, i, "太学助教", "官职", "北宋嘉祐元年十一月十五日",
        "授黄晞，未莅职，后不复置", rank, "太学学官名或散官",
        "补证任官资格及不出选人之阶。", "品位", officer="草泽经术之士",
    )
    cite(w, "Timepoints", last, i, duty,
         "北宋所授太学助教均未莅职，不能建作常设职事编制。", "职掌",
         note="所除者未莅职，实为散官；不建常设编制隶属关系")
    finish(w, touched, "整理太学助教前代职源与北宋两次授官，保留未莅职散官边界。")


def entry797():
    i, quote = 797, F[797]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "太学", "太学说书", "北宋嘉祐三年七月", quote,
        "嘉祐三年始除太学说书，赴太学详究制度，后不复设。",
        staff_type="差遣", office_event="始置太学说书，后不复设",
        post_event="始除人，赴太学供职，详究太学制度，后不复设",
    )
    finish(w, touched, "整理太学说书嘉祐三年始除、职掌与后不复设。")


def entry798():
    i = 798
    main, aliases = F[i]["text"], field(i, "别名")
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "太学馆", "太学生", "宋初礼部科举试期间", main,
        "宋初礼部科举试期间国子监临时开太学馆，录取临时太学生。",
        staff_type="临时学生", office_event="礼部科举试期间临时开馆，省试后解散",
        post_event="经考试入馆随秋试取解，省试后解散",
    )
    office_staff(
        w, touched, i, "太学", "太学生", "北宋庆历四年四月二十一日", main,
        "庆历建太学后正式招收八品以下官僚子弟与平民为太学生。",
        staff_type="学生", office_event="建校并正式招生",
        post_event="就读太学，专治一经",
    )
    members = tuple((title, "官职") for title in (
        "太学外舍生", "太学内舍生", "太学上舍生",
    ))
    group_tp = group_members(
        w, touched, i, "太学生", "官职", "北宋熙宁四年十月",
        "三舍外舍生、内舍生、上舍生的总称", members, main,
        "原文明言三舍学生总称太学生。",
    )
    evolution(
        w, touched, i, "太学外舍生", "太学内舍生",
        "北宋熙宁四年十月", main, "外舍生经升舍进入内舍。",
        source_event="经考试升内舍", target_event="由外舍生升入",
    )
    evolution(
        w, touched, i, "太学内舍生", "太学上舍生",
        "北宋熙宁四年十月", main, "内舍生按考试与行艺成绩升上舍。",
        source_event="按考试与行艺成绩升上舍", target_event="由内舍生升入",
    )
    alias_note(w, i, group_tp, aliases, "别名")
    finish(w, touched, "区分宋初临时太学馆学生与庆历后正式太学生，整理三舍统称、实例和升舍链。")


def entry799():
    i = 799
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    for time, quota, office, office_event, post_event in (
        ("北宋熙宁元年正月", 100, "太学", "始置外舍生一百人",
         "自费就读，候内舍有阙试补"),
        ("北宋熙宁四年十月", None, "太学", "实行三舍法",
         "三舍最低等，初入学者为外舍生，由官府给食钱"),
        ("北宋熙宁五年", 700, "太学", "外舍生限额七百人",
         "编制七百人"),
        ("北宋元丰二年八月", 2000, "太学", "新定太学条制",
         "外舍生二千人"),
        ("北宋崇宁三年", None, "辟雍外学", "辟雍建成，承接外舍生",
         "从太学迁至辟雍外学就读"),
        ("北宋宣和三年三月九日", None, "太学", "复元丰学制",
         "复按元丰学制在太学为外舍生"),
        ("南宋绍兴十三年七月", None, "太学", "复建太学并沿用三舍制",
         "南宋沿用三舍制的低等太学生"),
    ):
        _, post_tid, _ = office_staff(
            w, touched, i, office, "太学外舍生", time, main,
            f"{time}{office}设置或承接太学外舍生。",
            quota=quota, staff_type="学生", office_event=office_event,
            post_event=post_event,
        )
    evolution(
        w, touched, i, "太学外舍生", "太学内舍生",
        "北宋熙宁四年十月", main, "外舍生依三舍法升内舍。",
        source_event="经考试升内舍", target_event="由外舍生升入",
    )
    alias_note(w, i, post_tid, aliases, "简称")
    finish(w, touched, "整理太学外舍生始置、三舍等级、分期生额、辟雍迁移、复制与南宋沿用链。")


def entry800():
    i = 800
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    for time, quota, office_event, post_event in (
        ("北宋皇祐三年", 200, "设置内舍生二百人",
         "官府给食钱，为太学生中等"),
        ("北宋熙宁四年十月", None, "实行三舍法",
         "位于上舍生下、外舍生上，按考试和行艺升上舍"),
        ("北宋元丰二年八月", 300, "新定太学条制",
         "内舍生三百人"),
        ("北宋崇宁元年八月", 300, "三舍制度下定额",
         "内舍生三百人"),
        ("南宋绍兴十五年", 100, "增广太学生额",
         "内舍生一百人"),
    ):
        _, post_tid, _ = office_staff(
            w, touched, i, "太学", "太学内舍生", time, main,
            f"{time}太学内舍生制度或编制。", quota=quota,
            staff_type="学生", office_event=office_event, post_event=post_event,
        )
    evolution(
        w, touched, i, "太学内舍生", "太学上舍生",
        "北宋熙宁四年十月", main,
        "内舍生经上舍试并按行艺成绩升上舍。",
        source_event="两年一次赴上舍试，按考试与行艺升上舍",
        target_event="由内舍生升入",
    )
    alias_note(w, i, post_tid, aliases, "简称")
    finish(w, touched, "整理太学内舍生中等等级、供给、升舍方式和分期定额链。")


def main():
    for i in range(781, 801):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
