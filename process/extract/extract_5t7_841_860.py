#!/usr/bin/env python3
"""提取 chapter5t7 第841-860条：在京小学、广文馆、四门学与宗子学。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_821_840 as previous


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


F = {i: load(i) for i in range(841, 861)}
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
    "后魏太和二十年": 496, "北齐": 550, "隋唐": 600,
    "唐": 618, "唐天宝九载": 750, "宋初": 960,
    "北宋太宗朝": 980, "北宋前期": 970,
    "北宋（六宅诸王宫学）": 1000,
    "北宋真宗咸平三年十月八日": 1000.77,
    "北宋庆历二年闰九月": 1042.75,
    "北宋庆历四年": 1044,
    "北宋元丰初": 1078, "北宋元丰二年五月十七日": 1079.38,
    "北宋元丰间": 1080, "北宋元丰改制后": 1082.2,
    "北宋哲宗朝": 1090, "北宋元祐六年": 1091,
    "北宋元祐七年六月十三日": 1092.48,
    "北宋绍圣二年三月二十八日": 1095.23,
    "北宋建中靖国元年四月九日": 1101.27,
    "北宋崇宁元年十一月十二日": 1102.87,
    "北宋崇宁四年": 1105,
    "北宋崇宁五年十二月二十三日": 1106.96,
    "北宋政和四年": 1114, "北宋政和时（年月未载）": 1114.1,
    "北宋宣和三年七月十九日": 1121.55,
    "南宋前期（睦亲宅宫学）": 1132,
    "南宋绍兴四年": 1134, "南宋绍兴五年": 1135,
    "南宋绍兴十四年四月": 1144.28,
    "南宋绍兴十四年六月五日": 1144.45,
    "南宋嘉定七年": 1214, "南宋嘉定七年八月二十六日": 1214.66,
    "南宋嘉定八年": 1215, "南宋嘉定九年": 1216,
    "南宋嘉定九年十二月五日": 1216.94,
    "南宋嘉定十年": 1217, "南宋嘉定十三年": 1220,
    "南宋嘉定十四年": 1221,
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
        source_event or f"转为{target_title}", quotation, "演变前",
        f"建立或复用{source_title}{time}演变节点。", field_name,
    )
    target_tid = node(
        w, touched, i, target_title, "官职", time,
        target_event or f"由{source_title}转入", quotation, "演变后",
        f"建立或复用{target_title}{time}演变节点。", field_name,
    )
    relation(
        w, i, source_tid, target_tid, "前后演变", quotation,
        decision, field_name,
    )
    return source_tid, target_tid


def canonicalize_capital_primary_school(w, quotation):
    """把前批按叙述性名称建立的同一机构归并到正式词头。"""
    canonical = w.find_entity("在京小学", "机构")
    short = w.find_entity("小学", "机构")
    long = w.find_entity("国子监小学", "机构")
    if canonical is None:
        canonical = short or long
        assert canonical is not None, "前批应已建立小学或国子监小学"
        old_title = "小学" if canonical == short else "国子监小学"
        w.conn.execute(
            "update Entities set title='在京小学',quotation=? where id=?",
            (quotation, canonical),
        )
        w._br(
            "Entities", canonical,
            f"第841条正式词头为在京小学；将前批叙述性名称{old_title}规范为正式词头。",
        )
    for duplicate in (short, long):
        if duplicate is None or duplicate == canonical:
            continue
        duplicate_times = {
            row[0] for row in w.conn.execute(
                "select time from Timepoints where entity_id=?", (duplicate,)
            )
        }
        canonical_times = {
            row[0] for row in w.conn.execute(
                "select time from Timepoints where entity_id=?", (canonical,)
            )
        }
        assert duplicate_times.isdisjoint(canonical_times), (
            "归并在京小学出现同名时间点", duplicate_times & canonical_times
        )
        w.conn.execute(
            "update Timepoints set entity_id=? where entity_id=?",
            (canonical, duplicate),
        )
        w.conn.execute(
            "update BuildRecords set target_id=? where target_table='Entities' "
            "and target_id=?",
            (canonical, duplicate),
        )
        w.conn.execute(
            "update Citations set target_id=? where target_table='Entities' "
            "and target_id=?",
            (canonical, duplicate),
        )
        w.conn.execute("delete from Entities where id=?", (duplicate,))
        w._br(
            "Entities", canonical,
            "第841条确认小学、国子监小学均指正式词头在京小学；归并实体并保留原时间点、关系和追溯。",
        )
    return canonical


def entry841():
    i = 841
    main, origin, function, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"),
    )
    w, touched = W(i), set()
    touched.add(canonicalize_capital_primary_school(w, main))
    for time, event in (
        ("后魏太和二十年", "后魏已有四门小学，为制度职源"),
        ("北宋元丰初", "已置在京小学"),
        ("南宋绍兴十四年四月", "于国子监复置小学"),
    ):
        node(w, touched, i, "在京小学", "机构", time, event, origin,
             "中央小学", f"建立在京小学{time}沿革节点。", "职源与沿革")
    for time in ("北宋元丰初", "南宋绍兴十四年四月"):
        parent_child(
            w, touched, i, "国子监", "太学", time, main,
            f"{time}国子监统辖太学。",
            parent_event="统辖太学", child_event="隶国子监",
        )
        parent_child(
            w, touched, i, "太学", "在京小学", time, main,
            f"{time}在京小学隶国子监太学。",
            parent_event="统辖在京小学", child_event="隶国子监太学",
        )
    school_tp = node(
        w, touched, i, "在京小学", "机构", "北宋元丰初",
        "招收八至十二岁儿童，训诲考校，公试合格可升太学外舍",
        function, "中央小学", "补证招生、教学、考校与升太学职能。", "职能",
    )
    student_tp = node(
        w, touched, i, "小学生", "官职", "宋代（未载具体年月）",
        "公试合格可升太学外舍生", function, "学生",
        "建立小学生升太学外舍生的来源节点。", "职能",
    )
    outer_tp = node(
        w, touched, i, "太学外舍生", "官职", "宋代（未载具体年月）",
        "可由小学生公试合格升入", function, "太学生",
        "建立太学外舍生承接小学升学节点。", "职能",
    )
    relation(
        w, i, student_tp, outer_tp, "前后演变", function,
        "小学生公试合格可升为太学外舍生。", "职能",
    )
    for time, quota, event in (
        ("北宋元丰间", None, "设就傅、初筮两斋"),
        ("北宋政和四年", 1000, "学生近一千人，分十斋"),
    ):
        office_staff(
            w, touched, i, "在京小学", "小学生", time, roster,
            f"{time}在京小学学生编制。", "编制", quota=quota,
            staff_type="学生", office_event=event, post_event=event,
        )
    cite(w, "Timepoints", school_tp, i, roster,
         "补证在京小学所设学官与职事人。", "编制")
    finish(w, touched, "规范在京小学正式词头并整理职源、分期隶属、职能、生额与升学链。")


def entry842():
    i = 842
    main, origin, duty, roster, aliases = (
        F[i]["text"], field(i, "职源"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "在京小学", "小学教谕",
        "北宋元丰二年五月十七日", origin,
        "元丰二年已有小学教谕，元丰时一员。", "职源",
        quota=1, staff_type="命官学官", office_event="设置小学教谕一员",
        post_event="掌小学训导考校责罚",
    )
    for time, quota in (
        ("北宋政和时（年月未载）", 10),
        ("北宋宣和三年七月十九日", 2),
    ):
        office_staff(
            w, touched, i, "在京小学", "职事教谕", time, roster,
            f"{time}职事教谕编制{quota}人。", "编制", quota=quota,
            staff_type="职事教谕", office_event=f"设置职事教谕{quota}人",
            post_event="由学生或贡士充任，掌小学教导",
        )
    cite(w, "Timepoints", post, i, main, "补证小学教谕隶国子监。")
    cite(w, "Timepoints", post, i, duty, "补证小学教谕职掌。", "职掌")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理小学教谕元丰始见、命官与职事教谕分期编制及职掌链。")


def entry843():
    i, quote = 843, F[843]["text"]
    w, touched = W(i), set()
    group_tp = node(
        w, touched, i, "小学教谕", "官职", "宋代（未载具体年月）",
        "依任职身份分命官小学教谕与职事教谕", quote, "学官统称",
        "建立小学教谕两类任职者的统称节点。",
    )
    for title, event, officer in (
        ("命官小学教谕", "由命官担任的小学教谕", "命官"),
        ("职事教谕", "由大学生或贡士差充的小学教谕", "大学生或贡士"),
    ):
        member_tp = node(
            w, touched, i, title, "官职", "宋代（未载具体年月）",
            event, quote, "小学教谕实例", f"建立或复用{title}实例节点。",
            officer=officer,
        )
        relation(
            w, i, group_tp, member_tp, "统称与实例", quote,
            f"{title}是小学教谕依任职身份区分的实例。",
        )
    finish(w, touched, "整理职事教谕与命官小学教谕的身份差别和统称实例关系。")


def entry844():
    i, quote = 844, F[844]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "在京小学", "小学录", "宋代（未载具体年月）",
        quote, "小学录隶在京小学，掌本学规矩事。", staff_type="学官",
        office_event="设置小学录", post_event="掌本学规矩事",
    )
    finish(w, touched, "整理小学录所隶与掌管学规职能。")


def entry845():
    i = 845
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    node(
        w, touched, i, "小学学长", "官职", "北宋真宗咸平三年十月八日",
        "学长之名始见于东宫内宦官办学", origin, "职源",
        "建立小学学长之前代学长职源节点。", "职源与沿革",
    )
    _, post, _ = office_staff(
        w, touched, i, "在京小学", "小学学长", "北宋元丰间", roster,
        "元丰间在京小学置学长二人，每教谕斋一人。", "编制",
        quota=2, staff_type="学生职事人", office_event="设置学长二人",
        post_event="由太学生充，每教谕斋一人", officer="太学生",
    )
    evolution(
        w, touched, i, "小学学长", "小长",
        "北宋崇宁五年十二月二十三日", origin,
        "崇宁五年因与县学长同名，改小学学长为小长。", "职源与沿革",
        source_event="改名小长", target_event="由小学学长改名",
    )
    cite(w, "Timepoints", post, i, main, "补证小学学长隶国子监。")
    cite(w, "Timepoints", post, i, duty, "补证小学学长职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证由太学生充且非命官。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理小学学长职源、元丰置额、职掌身份与崇宁改名小长链。")


def entry846():
    i, quote = 846, F[846]["text"]
    w, touched = W(i), set()
    source, target = evolution(
        w, touched, i, "小学学长", "小长",
        "北宋崇宁五年十二月二十三日", quote,
        "崇宁五年改小学学长为小长，以别于县学长。",
        source_event="改名小长", target_event="由小学学长改名",
    )
    office_staff(
        w, touched, i, "在京小学", "小长",
        "北宋崇宁五年十二月二十三日", quote,
        "改名后小长仍为在京小学职事人。", staff_type="学生职事人",
        office_event="小学学长改称小长", post_event="小学学长改名",
    )
    finish(w, touched, "以独立词条补证小学学长改小长的完整演变与所隶。")


def entry847():
    i, main, aliases = 847, F[847]["text"], field(847, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "在京小学", "小学集正", "北宋哲宗朝", main,
        "哲宗朝在京小学置集正二人，每教谕斋一人。", quota=2,
        staff_type="学生职事人", office_event="每教谕斋置集正一人",
        post_event="由太学生充，登记名册并纠察课业", officer="太学生",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理小学集正哲宗朝所隶、学生选充、职掌与每斋置额。")


def entry848():
    i = 848
    main, origin, function, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("唐天宝九载", "始置"),
        ("北宋太宗朝", "为三馆之一，科场临时设置，罢场即散"),
        ("北宋元祐七年六月十三日", "复立广文馆生"),
        ("北宋绍圣二年三月二十八日", "罢置"),
    ):
        node(w, touched, i, "广文馆", "机构", time, event, origin,
             "中央官学", f"建立广文馆{time}沿革节点。", "职源与沿革")
    for time in ("北宋太宗朝", "北宋元祐七年六月十三日"):
        parent_child(
            w, touched, i, "国子监", "广文馆", time, main,
            f"{time}广文馆隶国子监。",
            parent_event="统辖广文馆", child_event="隶国子监",
        )
    function_tp = node(
        w, touched, i, "广文馆", "机构", "北宋元祐七年六月十三日",
        "招收四方应举人，贡举年考试，十人取一名解额",
        function, "中央官学", "补证哲宗朝广文馆招生与取解职能。", "职能",
    )
    office_staff(
        w, touched, i, "广文馆", "广文生", "北宋元祐七年六月十三日",
        roster, "广文馆招收广文生二千四百名。", "编制", quota=2400,
        staff_type="学生", office_event="广文生二千四百名，解额二百四十名",
        post_event="馆生二千四百名，十人取一解额",
    )
    cite(w, "Timepoints", function_tp, i, roster,
         "补证广文馆生额与解额。", "编制")
    finish(w, touched, "整理广文馆唐代始置、宋初临时馆、元祐复立、绍圣罢置、隶属与生额链。")


def entry849():
    i, main, aliases = 849, F[849]["text"], field(849, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "广文馆博士", "官职", "唐", "始置", main,
         "广文馆学官", "建立广文馆博士唐代职源节点。")
    _, post, _ = office_staff(
        w, touched, i, "广文馆", "广文馆博士", "宋初", main,
        "宋初广文馆沿置博士，掌教导。", staff_type="博士",
        office_event="设置广文馆博士", post_event="掌教导",
    )
    node(
        w, touched, i, "广文馆博士", "官职", "北宋庆历四年",
        "太学建立后不复置", main, "广文馆学官",
        "建立庆历四年后不复置节点。",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理广文馆博士唐代职源、宋初沿置教导与庆历四年停置链。")


def entry850():
    i = 850
    main, origin, function, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("后魏太和二十年", "始置，以设于京师四门得名"),
        ("北宋庆历二年闰九月", "始立四门学"),
        ("北宋庆历四年", "太学建立后废置"),
    ):
        node(w, touched, i, "四门学", "机构", time, event, origin,
             "中央官学", f"建立四门学{time}沿革节点。", "职源与沿革")
    parent_child(
        w, touched, i, "国子监", "四门学", "北宋庆历二年闰九月", main,
        "庆历二年四门学隶国子监。",
        parent_event="统辖四门学", child_event="隶国子监",
    )
    function_tp = node(
        w, touched, i, "四门学", "机构", "北宋庆历二年闰九月",
        "招收八品以下官员子弟和平民子弟，考试合格补正员监生",
        function, "中央官学", "补证四门学招生与考校职能。", "职能",
    )
    office_staff(
        w, touched, i, "四门学", "国子监四门助教",
        "北宋庆历二年闰九月", roster,
        "四门学设置国子监四门助教等学官。", "编制",
        staff_type="学官", office_event="设置四门助教等学官",
        post_event="掌四门学教学",
    )
    cite(w, "Timepoints", function_tp, i, roster,
         "补证四门学设四门助教学官。", "编制")
    finish(w, touched, "整理四门学后魏职源、庆历建废、国子监隶属、职能与学官链。")


def entry851():
    i = 851
    main, origin, function, rank, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职能"),
        field(i, "品位"), field(i, "简称"),
    )
    w, touched = W(i), set()
    for time, event, category in (
        ("北齐", "国子寺已有四门助教，为职源", "职源"),
        ("隋唐", "国子监四门助教始设", "职源"),
        ("北宋前期", "沿置，并可授聚徒讲学有声望的地方名士", "散官兼学官"),
        ("北宋元丰改制后", "新制不设", "旧制散官或学官"),
    ):
        node(w, touched, i, "国子监四门助教", "官职", time, event,
             origin, category, f"建立四门助教{time}沿革节点。", "职源与沿革")
    _, school_post, _ = office_staff(
        w, touched, i, "四门学", "国子监四门助教",
        "北宋庆历二年闰九月", function,
        "庆历四门学以四门助教为学官，掌教导。", "职能",
        staff_type="学官", office_event="设置四门助教",
        post_event="作为四门学学官掌教导",
    )
    early = node(
        w, touched, i, "国子监四门助教", "官职", "宋初",
        "依唐制，班位在国子监、广文馆、太学助教之下",
        rank, "散官兼学官", "建立宋初品位班序节点。", "品位",
        grade="从八品上",
    )
    cite(w, "Timepoints", school_post, i, main,
         "补证四门助教兼具散官、学官两种性质。")
    alias_note(w, i, early, aliases, "简称")
    finish(w, touched, "区分国子监四门助教散官与庆历学官性质，整理职源、品位及元丰停置链。")


def entry852():
    i = 852
    main, origin, function, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("北宋（六宅诸王宫学）", "六宅各置大、小学，皆有学官"),
        ("北宋元祐六年", "始建专门宗学，竣工后赐蔡确家，未实际延续"),
        ("北宋建中靖国元年四月九日", "复置宗学"),
        ("北宋崇宁元年十一月十二日", "诸王宫置大、小二学，总称宗学，实为宫学"),
        ("南宋前期（睦亲宅宫学）", "于睦亲宅建宫学"),
        ("南宋嘉定七年", "诏改宫学为宗学"),
        ("南宋嘉定九年", "宗学舍建成后正式改宫学为宗学"),
    ):
        node(w, touched, i, "宗子学", "机构", time, event, origin,
             "中央宗室学校", f"建立宗子学{time}沿革节点。", "职源与沿革")
    for time in ("北宋建中靖国元年四月九日", "南宋绍兴五年"):
        parent_child(
            w, touched, i, "宗正寺", "宗子学", time, main,
            f"{time}宗子学隶宗正寺。",
            parent_event="统辖宗子学", child_event="隶宗正寺",
        )
    for time in ("南宋嘉定七年", "南宋嘉定八年"):
        parent_child(
            w, touched, i, "国子监", "宗子学", time, main,
            f"{time}宗子学改隶国子监。",
            parent_event="统辖宗子学", child_event="改隶国子监",
        )
    function_tp = node(
        w, touched, i, "宗子学", "机构", "北宋崇宁元年十一月十二日",
        "宗子分大学、小学入学，按年龄分学并参加宗学取解",
        function, "中央宗室学校", "补证宗学招生年龄、考试与解额制度。", "职能",
    )
    for time, quota, event in (
        ("北宋政和四年", 1000, "小学生近一千人，分十斋"),
        ("南宋绍兴五年", 100, "生员一百名：大学生五十、小学生四十、职事各五"),
    ):
        office_staff(
            w, touched, i, "宗子学", "宗子生", time, roster,
            f"{time}宗子学生员编制{quota}人。", "编制", quota=quota,
            staff_type="学生", office_event=event, post_event=event,
        )
    node(
        w, touched, i, "宗子学", "机构", "南宋嘉定十四年",
        "宗学博士一员与诸王宫大、小学教授一员并置",
        roster, "中央宗室学校", "建立嘉定十四年学官并置节点。", "编制",
    )
    cite(w, "Timepoints", function_tp, i, aliases,
         "补证宗子学的宗学、宗庠、麟庠名称。", "简称与别名",
         note="纯简称、别名不另建实体")
    finish(w, touched, "整理宗子学北宋六宅至南宋嘉定建置、宗正寺与国子监分期隶属、职能生额及别名链。")


def entry853():
    i = 853
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    evolution(
        w, touched, i, "诸王宫大、小学教授", "宗子学博士",
        "北宋崇宁四年", origin,
        "崇宁四年改诸王宫大、小学教授为宗子学博士。", "职源与沿革",
        source_event="改为宗子学博士", target_event="由诸王宫大、小学教授改置",
    )
    evolution(
        w, touched, i, "宗子学博士", "诸王宫大、小学教授",
        "南宋绍兴四年", origin,
        "绍兴四年宗子学博士复称诸王宫大、小学教授。", "职源与沿革",
        source_event="复称诸王宫大、小学教授", target_event="由宗子学博士复称",
    )
    for school in ("诸王宫大学", "诸王宫小学"):
        office_staff(
            w, touched, i, school, "宗子学博士", "北宋崇宁四年", roster,
            f"崇宁时{school}各置宗子学博士二员。", "编制", quota=2,
            staff_type="博士", office_event="设置宗子学博士二员",
            post_event="教导本学宗子，编制二员", grade="正八品",
        )
    _, post, _ = office_staff(
        w, touched, i, "宗子学", "宗子学博士",
        "南宋嘉定七年八月二十六日", origin,
        "嘉定七年诏置宗子学博士一员。", "职源与沿革", quota=1,
        staff_type="博士", office_event="诏置宗学博士一员",
        post_event="教导宗子学生", grade="正八品",
    )
    evolution(
        w, touched, i, "诸王宫大、小学教授", "宗子学博士",
        "南宋嘉定九年", origin,
        "嘉定九年宫学教授改为宗子学博士。", "职源与沿革",
        source_event="宫学改宗学时改为宗子学博士",
        target_event="由宫学教授改置",
    )
    cite(w, "Timepoints", post, i, main, "补证宗子学博士隶宗子学。")
    cite(w, "Timepoints", post, i, duty, "补证教导本学宗子职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证正八品及班序。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理宗子学博士崇宁改置、绍兴复称、嘉定诏置与再改、职掌品位及分期编制链。")


def entry854():
    i = 854
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "宗子学", "宗子学谕",
        "南宋嘉定七年八月二十六日", origin,
        "嘉定七年诏置宗子学谕一员。", "职源", quota=1,
        staff_type="学谕", office_event="诏置宗子学谕一员",
        post_event="与宗子学博士共掌教导", grade="正九品",
    )
    evolution(
        w, touched, i, "诸王宫大、小学教授", "宗子学谕",
        "南宋嘉定九年十二月五日", origin,
        "嘉定九年宗学舍建成，宫学教授改宗学教授、宗子学谕并始除人。", "职源",
        source_event="宫学改宗学时分改宗学教授、宗子学谕",
        target_event="由宫学教授改置并始除人",
    )
    office_staff(
        w, touched, i, "宗子学", "宗子学谕",
        "南宋嘉定九年十二月五日", roster,
        "嘉定九年宗子学谕始除人，编制一员。", "编制", quota=1,
        staff_type="学谕", office_event="宗学舍建成并置学谕一员",
        post_event="始正式除人，编制一员", grade="正九品",
    )
    cite(w, "Timepoints", post, i, main, "补证宗子学谕学官性质与所隶。")
    cite(w, "Timepoints", post, i, duty, "补证与宗学博士共掌教导。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证正九品及班序。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理宗子学谕嘉定诏置、始除、所隶、职掌、品位、一员编制及简称链。")


def simple_clan_school_staff(i, title, time, quota, staff_type, event,
                             *, office="宗子学", officer=None):
    quote = F[i]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, office, title, time, quote,
        f"{time}{office}设置{title}{quota}人。", quota=quota,
        staff_type=staff_type, office_event=f"设置{title}{quota}人",
        post_event=event, officer=officer,
    )
    finish(w, touched, f"整理{title}在{office}的设置时间、职掌、身份与编制。")


def entry855():
    simple_clan_school_staff(
        855, "书铺", "南宋嘉定十年", 2, "公人",
        "受纳公私试与补试试卷并誊录复本",
    )


def entry856():
    simple_clan_school_staff(
        856, "专知官", "南宋嘉定十三年", 1, "公吏",
        "掌宗学官钱、官物、书籍与柴禾", officer="刑部差副尉",
    )


def entry857():
    simple_clan_school_staff(
        857, "库子", "南宋嘉定十年", 1, "公人",
        "与专知官共管钱物书籍柴禾，须有家产抵当",
    )


def entry858():
    simple_clan_school_staff(
        858, "攒司", "南宋嘉定十年", 1, "公人",
        "掌书写与记帐目",
    )


def entry859():
    i, quote = 859, F[859]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "宗子学", "宗学公厨", "南宋嘉定十年", quote,
        "嘉定十年宗子学设置公厨。",
        parent_event="设置公厨", child_event="隶宗子学并供办伙食",
    )
    office_staff(
        w, touched, i, "宗学公厨", "厨子", "南宋嘉定十年", quote,
        "宗学公厨置厨子二名。", quota=2, staff_type="公人",
        office_event="设置厨子二名", post_event="掌炊制伙食",
    )
    finish(w, touched, "整理宗学公厨所隶及厨子二名编制职掌。")


def entry860():
    simple_clan_school_staff(
        860, "饭局抬盘子", "南宋嘉定十年", 1, "公人",
        "在公厨下供行遣杂事", office="宗学公厨",
    )


def main():
    for i in range(841, 861):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
