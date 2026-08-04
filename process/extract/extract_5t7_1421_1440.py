#!/usr/bin/env python3
"""提取 chapter5t7 第1421-1440条：三卫诸官与六军诸官。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1401_1420 as previous


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


F = {i: load(i) for i in range(1421, 1441)}
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


TIME_HINTS = {
    **previous.TIME_HINTS,
    "汉武帝太初元年": -104,
    "唐朝": 700,
    "唐德宗朝": 790,
    "唐兴元元年正月二十九日": 784.08,
    "宋初": 960,
    "宋代": 1000,
    "宋代（六军仪仗司）": 1000.1,
    "北宋": 970,
    "北宋咸平元年十一月十九日": 998.88,
    "北宋咸平五年十一月十九日": 1002.88,
    "北宋景德二年十一月": 1005.88,
    "北宋治平三年九月三日": 1066.69,
    "北宋治平三年九月": 1066.72,
    "北宋崇宁四年二月十日": 1105.10,
    "北宋崇宁四年二月二十六日": 1105.15,
    "北宋崇宁五年正月三十日": 1106.08,
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


def entity_id(w, title, type_):
    eid = w.find_entity(title, type_)
    assert eid is not None, (title, type_)
    return eid


def tp(w, title, type_, time):
    eid = entity_id(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid is not None, (title, type_, time)
    return tid


def mark_conflict(w, citation_id, note, decision):
    flag, saved_note = w.conn.execute(
        "select conflict_flag,note from Citations where id=?", (citation_id,)
    ).fetchone()
    if flag == 1 and saved_note == note:
        return
    w.conn.execute(
        "update Citations set conflict_flag=1,note=? where id=?",
        (note, citation_id),
    )
    w._br("Citations", citation_id, decision)


def conflict_targets(w, i, targets, quotation, note, decision, field_name=None):
    for table, target_id in targets:
        citation_id = cite(
            w, table, target_id, i, quotation, decision, field_name,
            conflict_flag=1, note=note,
        )
        mark_conflict(w, citation_id, note, decision)


def three_guard_staff(i, office, post, origin_name, grade, quota, staff_type):
    origin = field(i, origin_name)
    duty, rank, roster = field(i, "职掌"), field(i, "品位"), field(i, "编制")
    w, touched = W(i), set()
    office_tid = node(
        w, touched, i, office, "机构", "北宋崇宁四年二月十日",
        f"编制{post}{quota}", origin, "三卫府署",
        f"复用{office}始置节点。", origin_name,
    )
    post_tid = node(
        w, touched, i, post, "官职", "北宋崇宁四年二月十日",
        "始置，列入三卫府编制", origin, "三卫官",
        f"复用{post}始置节点并补足品位。", origin_name,
        officer=staff_type, grade=grade,
    )
    staff(
        w, i, office_tid, post_tid, roster,
        f"{office}置{post}{quota}。", "编制",
        quota=quota, staff_type=staff_type,
    )
    cite(w, "Timepoints", post_tid, i, duty, f"保存{post}职掌。", "职掌")
    cite(w, "Timepoints", post_tid, i, rank, f"保存{post}品位。", "品位")
    cite(w, "Timepoints", post_tid, i, roster, f"保存{post}员额。", "编制")
    ended = node(
        w, touched, i, post, "官职", "北宋崇宁五年正月三十日",
        "随三卫府罢置", origin, "三卫府罢置所及官吏",
        f"复用{post}罢置节点。", origin_name,
    )
    cite(w, "Timepoints", ended, i, origin, f"保存{post}罢置日期。", origin_name)
    aliases = F[i]["fields"].get("简称")
    if aliases:
        alias_note(w, i, post_tid, aliases, "简称")
    finish(w, touched, f"整理{post}始置、隶属、职掌、品位、员额及罢置时间链。")


def entry1421():
    three_guard_staff(1421, "三卫府", "三卫中郎", "职源与沿革", "正六品", "二员", "中郎")


def entry1422():
    three_guard_staff(1422, "三卫府", "三卫博士", "职源", "从七品", "二员", "博士")


def entry1423():
    three_guard_staff(1423, "三卫府", "三卫主簿", "职源", "从八品", "一员", "主簿")


def guard_pair(i, office, left, right, left_grade, right_grade, quotas):
    origin, duty = field(i, "职源"), field(i, "职掌")
    rank, roster, aliases = (
        field(i, "品位"), field(i, "编制"), field(i, "简称")
    )
    w, touched = W(i), set()
    group = node(
        w, touched, i, F[i]["title"], "官职", "北宋崇宁四年二月十日",
        f"{left}、{right}合称", origin, "三卫官统称",
        f"按正式词头建立{F[i]['title']}。", "职源", update_event=True,
    )
    office_tid = node(
        w, touched, i, office, "机构", "北宋崇宁四年二月十日",
        f"编制{left}、{right}", origin, "三卫府署",
        f"复用{office}始置节点。", "职源",
    )
    for title, grade, quota in (
        (left, left_grade, quotas[0]), (right, right_grade, quotas[1]),
    ):
        post = node(
            w, touched, i, title, "官职", "北宋崇宁四年二月十日",
            f"列入{office}编制", origin, "三卫官",
            f"复用{title}并补足品位。", "职源",
            officer="三卫郎", grade=grade,
        )
        relation(
            w, i, group, post, "统称与实例", roster,
            f"{title}是{F[i]['title']}的实例。", "编制",
        )
        staff(
            w, i, office_tid, post, roster,
            f"{office}置{title}{quota}。", "编制",
            quota=quota, staff_type="三卫郎",
        )
        cite(w, "Timepoints", post, i, duty, f"保存{title}仪卫职掌。", "职掌")
        cite(w, "Timepoints", post, i, rank, f"保存{title}品位。", "品位")
        cite(w, "Timepoints", post, i, roster, f"保存{title}员额。", "编制")
        alias_note(w, i, post, aliases, "简称")
    cite(w, "Timepoints", group, i, duty, "保存合称所指两职共同职掌。", "职掌")
    cite(w, "Timepoints", group, i, rank, "保存合称所指两职品位。", "品位")
    cite(w, "Timepoints", group, i, aliases, "保存本词头简称证据。", "简称")
    finish(w, touched, f"整理{F[i]['title']}正式合称、两个实例及三卫府编制。")


def entry1424():
    guard_pair(1424, "亲卫府", "亲卫郎", "亲卫中郎", "正七品", "从七品", ("十员", "十员"))


def entry1425():
    guard_pair(1425, "勋卫府", "勋卫郎", "勋卫中郎", "正八品", "从八品", ("十员", "十员"))


def entry1426():
    guard_pair(1426, "翊卫府", "翊卫郎", "翊卫中郎", "从八品", "正九品", ("二十员", "二十员"))


def entry1427():
    i, main = 1427, F[1427]["text"]
    w, touched = W(i), set()
    group = node(
        w, touched, i, F[i]["title"], "官职", "北宋崇宁四年二月十日",
        "三卫府及亲卫、勋卫、翊卫三府官员总称", main,
        "三卫官统称", "按正式词头建立三卫官统称。", update_event=True,
    )
    members = (
        ("三卫郎", "北宋崇宁四年二月十日"),
        ("三卫侍郎", "北宋崇宁四年二月二十六日"),
        ("三卫中郎", "北宋崇宁四年二月十日"),
        ("三卫博士", "北宋崇宁四年二月十日"),
        ("三卫主簿", "北宋崇宁四年二月十日"),
        ("亲卫郎", "北宋崇宁四年二月十日"),
        ("亲卫中郎", "北宋崇宁四年二月十日"),
        ("勋卫郎", "北宋崇宁四年二月十日"),
        ("勋卫中郎", "北宋崇宁四年二月十日"),
        ("翊卫郎", "北宋崇宁四年二月十日"),
        ("翊卫中郎", "北宋崇宁四年二月十日"),
    )
    for title, time in members:
        member = node(
            w, touched, i, title, "官职", time,
            "三卫官所指实例", main, "三卫官实例",
            f"复用{title}作为三卫官实例。",
        )
        relation(
            w, i, group, member, "统称与实例", main,
            f"正文明确{title}属于三卫官。",
        )
    finish(w, touched, "整理三卫官正式统称及十一项明确实例。")


def six_army_core(w, touched, i, quotation, field_name=None):
    office = node(
        w, touched, i, "六军仪仗司", "机构", "北宋",
        "掌郊祀、朝会六军仪仗排办", quotation, "宫廷仪仗机构",
        "复用六军仪仗司北宋节点。", field_name,
    )
    armies = node(
        w, touched, i, "六军", "机构", "宋代（六军仪仗司）",
        "左、右羽林、龙武、神武六军总名", quotation, "仪仗军号统称",
        "复用宋代六军统称节点。", field_name,
    )
    relation(
        w, i, office, armies, "上下级机构", quotation,
        "六军仪仗司以六军名目排办仪仗。", field_name,
    )
    return office, armies


def entry1428():
    i = 1428
    origin, duty, roster = field(i, "职源"), field(i, "职掌"), field(i, "编制")
    w, touched = W(i), set()
    tang = node(
        w, touched, i, "六军", "机构", "唐贞元间",
        "左、右羽林、龙武、神武六军合称", origin, "禁军番号统称",
        "复用唐代六军节点并追加本条职源证据。", "职源",
    )
    office, armies = six_army_core(w, touched, i, roster, "编制")
    cite(w, "Timepoints", armies, i, origin, "保存宋初沿置证据。", "职源")
    cite(w, "Timepoints", armies, i, duty, "保存六军仪仗及宗室寄禄性质。", "职掌")
    cite(w, "Timepoints", office, i, duty, "保存郊祀、朝会仪仗职掌。", "职掌")
    assert tang
    for title in (
        "左羽林军", "右羽林军", "左龙武军", "右龙武军", "左神武军", "右神武军",
    ):
        member = tp(w, title, "机构", "宋代（六军仪仗司）")
        relation(w, i, armies, member, "统称与实例", F[i]["text"],
                 f"{title}是六军实例。")
    for title, staff_type in (
        ("六军统军", "统军"), ("六军大将军", "大将军"), ("六军将军", "将军"),
    ):
        post = node(
            w, touched, i, title, "官职", "宋代（六军仪仗司）",
            f"六军各置{staff_type}", roster, "六军武官",
            f"复用{title}并追加本条证据。", "编制", officer=staff_type,
        )
        staff(w, i, armies, post, roster, f"六军各置{staff_type}。", "编制",
              staff_type=staff_type)
        cite(w, "Timepoints", post, i, duty, "保存无职事、宗室寄禄官性质。", "职掌")
    judge = node(
        w, touched, i, "判六军仪仗司事", "官职", "宋初",
        "判六军仪仗司事务，由判左、右金吾街仗司事兼任", roster,
        "六军仪仗司长官", "按正式官名建立判六军仪仗司事。", "编制",
        officer="判官", update_event=True,
    )
    staff(w, i, office, judge, roster, "六军仪仗司置判司事一人。", "编制",
          quota="一人", staff_type="判官")
    street_judge = tp(w, "判左、右金吾街仗司", "官职", "北宋")
    staff(w, i, office, street_judge, roster,
          "判六军仪仗司事由判左、右金吾街仗司事兼任。", "编制",
          staff_type="兼判官")

    date_note = (
        "与第1431、1438条所载咸平五年十一月十九日始误置六军上将军冲突；"
        "本条作咸平元年十一月，原书两说并存。"
    )
    mistaken = []
    for title in ("右羽林军上将军", "左神武军上将军"):
        start = node(
            w, touched, i, title, "官职", "北宋咸平元年十一月十九日",
            "六军本无上将军，属有司误置", roster, "错误六军官名",
            f"建立或复用{title}咸平元年误置节点。", "编制",
            officer="错误除授",
        )
        end_time = "北宋治平三年九月"
        if title == "左神武军上将军":
            eid = entity_id(w, title, "官职")
            if w.find_timepoint(eid, "北宋治平三年九月三日") is not None:
                end_time = "北宋治平三年九月三日"
        ended = node(
            w, touched, i, title, "官职", end_time,
            "错误六军上将军官名罢止", roster, "错误六军官名",
            f"建立或复用{title}治平三年罢止节点。", "编制",
            officer="错误除授",
        )
        mistaken.extend((start, ended))
    conflict_targets(
        w, i, [("Timepoints", tid) for tid in mistaken], roster, date_note,
        "标记咸平元年与五年始误置的辞典内部冲突。", "编制",
    )
    finish(w, touched, "整理六军总名、六军仪仗司编制及上将军误置冲突。")


def entry1429():
    i, main = 1429, F[1429]["text"]
    w, touched = W(i), set()
    office, armies = six_army_core(w, touched, i, main)
    judge = node(
        w, touched, i, "判六军仪仗司事", "官职", "宋初",
        "由判左、右金吾街仗司事兼任", main, "六军仪仗司长官",
        "复用判六军仪仗司事并追加本条证据。", officer="判官",
    )
    staff(w, i, office, judge, main, "六军仪仗司置判司事。",
          quota="一人", staff_type="判官")
    for title in (
        "排仗官", "通直官", "大将军仪仗押当官", "催驱官", "警场", "探头",
    ):
        post = node(
            w, touched, i, title, "官职", "宋代（六军仪仗司）",
            "六军仪仗司局职事", main, "六军仪仗司属员",
            f"复用{title}六军仪仗司节点。", officer="官兵",
        )
        staff(w, i, office, post, main, f"六军仪仗司下设{title}。",
              staff_type="局职事")
    assert armies
    finish(w, touched, "补足六军仪仗司职掌、判官及明确局职事的直接编制关系。")


def commander_entry(i, pair_title, left, right, army_pair, tang_time):
    origin, duty, rank, roster, aliases = (
        field(i, "职源"), field(i, "职能"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    tang = node(
        w, touched, i, pair_title, "官职", tang_time,
        "唐朝始置左、右统军", origin, "六军统军合称",
        f"建立或复用{pair_title}唐代节点。", "职源", officer="统军",
    )
    song = node(
        w, touched, i, pair_title, "官职", "宋代（六军仪仗司）",
        "宋沿置，为宗室官秩、武臣赠官及六军仪仗官衔，无定员且不常置",
        duty, "六军仪仗武官合称", f"建立或复用{pair_title}宋代节点。",
        "职能", officer="统军",
    )
    cite(w, "Timepoints", tang, i, origin, "保存唐代职源。", "职源")
    cite(w, "Timepoints", song, i, rank, "保存六军统军班位次序。", "品位")
    cite(w, "Timepoints", song, i, roster, "保存无定员、不常置。", "编制")
    alias_note(w, i, song, aliases, "简称")
    generic = node(
        w, touched, i, "六军统军", "官职", "宋代（六军仪仗司）",
        "六军各置统军", duty, "六军武官", "复用六军统军总称。", "职能",
        officer="统军",
    )
    relation(w, i, generic, song, "统称与实例", duty,
             f"{pair_title}是六军统军的实例组。", "职能")
    army = node(
        w, touched, i, army_pair, "机构", "宋代（六军仪仗司）",
        f"编制{pair_title}", duty, "仪仗军号统称",
        f"复用{army_pair}宋代节点。", "职能",
    )
    staff(w, i, army, song, duty, f"{army_pair}设置{pair_title}。", "职能",
          staff_type="统军")
    for side_title, army_title in ((left, left.replace("统军", "")), (right, right.replace("统军", ""))):
        member = node(
            w, touched, i, side_title, "官职", "宋代（六军仪仗司）",
            f"{pair_title}所指{side_title}", aliases, "六军仪仗武官",
            f"复用{side_title}作为左右实例。", "简称", officer="统军",
        )
        relation(w, i, song, member, "统称与实例", aliases,
                 f"{side_title}是{pair_title}实例。", "简称")
        relation(w, i, generic, member, "统称与实例", duty,
                 f"{side_title}是六军统军的具体实例。", "职能")
        army_member = node(
            w, touched, i, army_title, "机构", "宋代（六军仪仗司）",
            f"编制{side_title}", duty, "仪仗军号",
            f"复用{army_title}宋代节点。", "职能",
        )
        staff(w, i, army_member, member, duty, f"{army_title}设置{side_title}。",
              "职能", staff_type="统军")
    finish(w, touched, f"整理{pair_title}唐宋沿置、左右实例、六军统军归属及证据。")


def entry1430():
    commander_entry(1430, "左、右羽林军统军", "左羽林军统军", "右羽林军统军", "左、右羽林军", "唐兴元元年正月二十九日")


def entry1431():
    i, main, aliases = 1431, F[1431]["text"], field(1431, "简称")
    w, touched = W(i), set()
    group = node(
        w, touched, i, F[i]["title"], "官职", "北宋咸平五年十一月十九日",
        "楚王元佐误授羽林军上将军，六军本无上将军，应为统军",
        main, "错误六军官名统称", "按正式词头建立左右羽林军上将军。",
        update_event=True, officer="错误除授",
    )
    side_note = (
        "本条两种史源分别作右羽林军上将军、左羽林军上将军，左右互异；"
        "且与第1428条咸平元年十一月始误置的日期冲突，均按原书保留。"
    )
    targets = [("Timepoints", group)]
    for title, event in (
        ("右羽林军上将军", "一说楚王元佐误授右羽林军上将军"),
        ("左羽林军上将军", "一说楚王元佐误授左羽林军上将军"),
    ):
        member = node(
            w, touched, i, title, "官职", "北宋咸平五年十一月十九日",
            event, main, "错误六军官名候选",
            f"保存{title}这一史源异说。", officer="错误除授",
        )
        rid = relation(w, i, group, member, "统称与实例", main,
                       f"{title}是正式左右合称词头所指候选实例。")
        targets.extend((('Timepoints', member), ('Relationships', rid)))
    cite(w, "Timepoints", group, i, aliases, "保存上将军简称及两种史源。", "简称")
    conflict_targets(w, i, targets, main, side_note,
                     "标记左右异说及咸平元年、五年日期冲突。")
    finish(w, touched, "整理左右羽林军上将军错误除授、左右异说及日期冲突。")


def rank_pair_entry(i, family, rank_name, generic_title):
    origin, duty, rank = field(i, "职源"), field(i, "职能"), field(i, "品位")
    roster = F[i]["fields"].get("编制")
    aliases = F[i]["fields"].get("简称")
    w, touched = W(i), set()
    pair_title = F[i]["title"]
    left, right = f"左{family}{rank_name}", f"右{family}{rank_name}"
    for time, quote, field_name, event in (
        ("唐朝", origin, "职源", "唐朝已置"),
        ("宋代（六军仪仗司）", duty, "职能", "宋沿置，为宗室官秩、武臣赠官或责降官，无定员且不常置"),
    ):
        pair = node(
            w, touched, i, pair_title, "官职", time,
            f"{left}、{right}合称；{event}", quote, "六军武官合称",
            f"按正式词头建立{pair_title}{time}节点。", field_name,
            officer=rank_name, update_event=True,
        )
        for member_title in (left, right):
            member = node(
                w, touched, i, member_title, "官职", time,
                f"{pair_title}所指实例；{event}", quote, "六军武官",
                f"建立或复用{member_title}{time}实例。", field_name,
                officer=rank_name,
            )
            relation(w, i, pair, member, "统称与实例", quote,
                     f"{member_title}是{pair_title}实例。", field_name)
        if time.startswith("宋代"):
            cite(w, "Timepoints", pair, i, rank, "保存本级班位和六军内部次序。", "品位")
            if roster:
                cite(w, "Timepoints", pair, i, roster, "保存无定员、不常置。", "编制")
            if aliases:
                alias_note(w, i, pair, aliases, "简称")
            generic = node(
                w, touched, i, generic_title, "官职", time,
                f"六军各置{rank_name}", duty, "六军武官总称",
                f"复用{generic_title}。", "职能", officer=rank_name,
            )
            relation(w, i, generic, pair, "统称与实例", duty,
                     f"{pair_title}是{generic_title}实例组。", "职能")
            army_pair = node(
                w, touched, i, f"左、右{family}", "机构", time,
                f"编制{pair_title}", duty, "仪仗军号统称",
                f"复用左、右{family}。", "职能",
            )
            staff(w, i, army_pair, pair, duty, f"左、右{family}设置{pair_title}。",
                  "职能", staff_type=rank_name)
            for member_title in (left, right):
                member = tp(w, member_title, "官职", time)
                relation(w, i, generic, member, "统称与实例", duty,
                         f"{member_title}是{generic_title}具体实例。", "职能")
                army_title = member_title.removeprefix("左").removeprefix("右").removesuffix(rank_name)
                side = member_title[0]
                army = node(
                    w, touched, i, f"{side}{army_title}", "机构", time,
                    f"编制{member_title}", duty, "仪仗军号",
                    f"复用{side}{army_title}。", "职能",
                )
                staff(w, i, army, member, duty, f"{side}{army_title}设置{member_title}。",
                      "职能", staff_type=rank_name)
    finish(w, touched, f"整理{pair_title}唐宋沿置、左右实例及{generic_title}实例关系。")


def entry1432():
    rank_pair_entry(1432, "羽林军", "大将军", "六军大将军")


def entry1433():
    rank_pair_entry(1433, "羽林军", "将军", "六军将军")


def entry1434():
    commander_entry(1434, "左、右龙武军统军", "左龙武军统军", "右龙武军统军", "左、右龙武军", "唐兴元元年正月二十九日")


def entry1435():
    rank_pair_entry(1435, "龙武军", "大将军", "六军大将军")


def entry1436():
    rank_pair_entry(1436, "龙武军", "将军", "六军将军")


def entry1437():
    commander_entry(1437, "左、右神武军统军", "左神武军统军", "右神武军统军", "左、右神武军", "唐兴元元年正月二十九日")


def entry1438():
    i, main = 1438, F[1438]["text"]
    w, touched = W(i), set()
    source_eid = entity_id(w, "左神武军上将军", "官职")
    old = w.find_timepoint(source_eid, "北宋治平三年九月")
    exact = w.find_timepoint(source_eid, "北宋治平三年九月三日")
    if old is not None and exact is None:
        w.conn.execute(
            "update Timepoints set time=? where id=?",
            ("北宋治平三年九月三日", old),
        )
        w._br("Timepoints", old, "据本条将治平三年九月罢止细化到九月三日。")
        exact = old
    assert exact is not None
    normalized = ("错误赠官名改为左骁卫上将军", "错误官名纠正", "赠官纠正")
    saved = w.conn.execute(
        "select event,attr_category,attr_officer_type from Timepoints where id=?",
        (exact,),
    ).fetchone()
    if saved != normalized:
        w.conn.execute(
            "update Timepoints set event=?,attr_category=?,attr_officer_type=? where id=?",
            (*normalized, exact),
        )
        w._br("Timepoints", exact, "据本条规范左神武军上将军治平三年纠正事件。")
    cite(w, "Timepoints", exact, i, main, "保存治平三年九月三日纠正证据。")
    target = node(
        w, touched, i, "左骁卫上将军", "官职", "北宋治平三年九月三日",
        "由误赠左神武军上将军纠正", main, "环卫官赠官",
        "建立左骁卫上将军纠正承接节点。", officer="赠官", update_event=True,
    )
    rid = relation(w, i, exact, target, "前后演变", main,
                   "郭斌误赠左神武军上将军改为左骁卫上将军。")
    date_note = (
        "与第1428条咸平元年十一月始误置六军上将军冲突；"
        "本条追述咸平五年十一月十九日，保留两说。"
    )
    pair = tp(w, "左、右羽林军上将军", "官职", "北宋咸平五年十一月十九日")
    conflict_targets(
        w, i, (("Timepoints", pair), ("Timepoints", exact), ("Relationships", rid)),
        main, date_note, "标记咸平元年、五年日期冲突并保存纠正演变。",
    )
    touched.add(source_eid)
    finish(w, touched, "整理左神武军上将军误名及治平三年纠正演变。")


def entry1439():
    rank_pair_entry(1439, "神武军", "大将军", "六军大将军")


def entry1440():
    rank_pair_entry(1440, "神武军", "将军", "六军将军")


def main():
    expected = [
        "三卫中郎", "三卫博士", "三卫主簿", "亲卫府郎、中郎",
        "勋卫府郎、中郎", "翊卫府郎、中郎", "三卫官", "六军",
        "六军仪仗司", "左、右羽林军统军", "左、右羽林军上将军",
        "左、右羽林军大将军", "左、右羽林军将军", "左、右龙武军统军",
        "左、右龙武军大将军", "左、右龙武军将军", "左、右神武军统军",
        "左神武军上将军", "左、右神武军大将军", "左、右神武军将军",
    ]
    assert [F[i]["title"] for i in range(1421, 1441)] == expected
    for i in range(1421, 1441):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
