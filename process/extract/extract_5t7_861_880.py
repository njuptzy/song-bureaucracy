#!/usr/bin/env python3
"""提取 chapter5t7 第861-880条：诸学统称、职事人与医学。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_841_860 as previous


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


F = {i: load(i) for i in range(861, 881)}
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
    "宋初": 960, "北宋": 1000, "北宋元丰新制前": 1077,
    "北宋元丰官制格子": 1080, "北宋元丰二年": 1079,
    "北宋哲宗朝": 1090, "北宋庆历四年前科场年": 1043,
    "北宋治平二年七月二十四日": 1065.55,
    "北宋熙宁四年十月十七日": 1071.80,
    "北宋崇宁二年九月十五日": 1103.72,
    "北宋崇宁间": 1104, "北宋崇宁五年正月十二日": 1106.04,
    "北宋崇宁五年四月十二日": 1106.30,
    "北宋徽宗朝（年月未载）": 1107,
    "北宋大观元年二月十八日": 1107.13,
    "北宋大观四年三月二日": 1110.17,
    "北宋政和三年闰四月一日": 1113.30,
    "北宋宣和二年七月二十一日": 1120.56,
    "南宋": 1130, "南宋绍兴五年": 1135,
    "南宋绍兴十三年至二十六年": 1143,
    "南宋嘉定七年": 1214, "南宋嘉定十年": 1217,
    "两宋（年月未载）": 959.5, "北宋（年月未载）": 960.1,
    "宋代（未载具体年月）": 1100, "南宋（年月未载）": 1127.1,
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


def group_members(w, touched, i, group_title, type_, time, event, members,
                  quotation, decision, field_name=None):
    group_tid = node(
        w, touched, i, group_title, type_, time, event, quotation,
        f"{type_}统称", f"建立或复用{group_title}{time}统称节点。", field_name,
    )
    for member_title in members:
        member_tid = node(
            w, touched, i, member_title, type_, time,
            f"{group_title}在{time}所指实例", quotation,
            f"{group_title}实例", f"建立或复用{member_title}{time}实例节点。",
            field_name,
        )
        relation(
            w, i, group_tid, member_tid, "统称与实例", quotation,
            f"{member_title}是{group_title}在{time}的实例。", field_name,
        )
    return group_tid


def entry861():
    i, quote = 861, F[861]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "宗子学", "正斋仆", "南宋嘉定十年", quote,
        "嘉定十年宗学两廊四斋置正斋仆二人。", quota=2,
        staff_type="公人", office_event="两廊四斋置正斋仆二人",
        post_event="正员斋仆，在学斋干杂事供役使",
    )
    group_members(
        w, touched, i, "斋仆", "官职", "南宋嘉定十年",
        "分正斋仆与贴斋仆", ("正斋仆", "贴斋仆"), quote,
        "原文明确斋仆分为正斋仆与贴斋仆。",
    )
    finish(w, touched, "整理宗学正斋仆二人编制、正员身份、职役及斋仆分类。")


def entry862():
    i, quote = 862, F[862]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "宗子学", "贴斋仆", "南宋嘉定十年", quote,
        "嘉定十年宗学四斋各设贴斋仆一名，共四名。", quota=4,
        staff_type="非正员公人", office_event="四斋各置贴斋仆一名",
        post_event="非正员，位次正斋仆，在斋内干杂役",
    )
    group_members(
        w, touched, i, "斋仆", "官职", "南宋嘉定十年",
        "分正斋仆与贴斋仆", ("正斋仆", "贴斋仆"), quote,
        "贴斋仆条补证斋仆的正员、非正员分类。",
    )
    finish(w, touched, "整理宗学贴斋仆每斋一名、非正员位次、职役及斋仆分类。")


def entry863():
    i, quote = 863, F[863]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "五学", "机构", "北宋元丰官制格子",
        "国子学、太学、武学、律学、算学合称",
        ("国子学", "太学", "武学", "律学", "算学"), quote,
        "《元丰官制格子》明确五学的五个实例。",
    )
    group_members(
        w, touched, i, "五学", "机构", "北宋哲宗朝",
        "国子学、太学、武学、律学、小学合称",
        ("国子学", "太学", "武学", "律学", "在京小学"), quote,
        "哲宗朝五学所称小学按正式词头复用在京小学。",
    )
    group_members(
        w, touched, i, "五学", "机构", "北宋崇宁间",
        "太学、武学、律学、算学、艺学合称",
        ("太学", "武学", "律学", "算学", "艺学"), quote,
        "崇宁间五学明确包含五个实例。",
    )
    finish(w, touched, "完整整理元丰、哲宗、崇宁三个时期五学所指实例变化。")


def entry864():
    i, quote = 864, F[864]["text"]
    w, touched = W(i), set()
    members = ("书学", "画学", "算学", "医学")
    group_members(
        w, touched, i, "四学", "机构", "北宋崇宁间",
        "书学、画学、算学、医学合称", members, quote,
        "崇宁间四学明确包含书、画、算、医四学。",
    )
    node(
        w, touched, i, "四学", "机构", "北宋崇宁五年四月十二日",
        "四学并罢", quote, "官学统称",
        "建立崇宁五年四学并罢节点。",
    )
    for title in members:
        node(
            w, touched, i, title, "机构", "北宋崇宁五年四月十二日",
            "随四学诏并罢", quote, "国子监所属官学",
            f"建立{title}崇宁五年四月十二日并罢节点。",
        )
    finish(w, touched, "整理崇宁四学正式统称、四个实例及四月十二日并罢节点。")


def entry865():
    i, quote = 865, F[865]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "三学", "机构", "北宋元丰新制前",
        "太学、律学、武学合称", ("太学", "律学", "武学"), quote,
        "北宋元丰新制前三学所指三个实例。",
    )
    group_members(
        w, touched, i, "三学", "机构", "南宋",
        "太学、武学、宗学合称", ("太学", "武学", "宗子学"), quote,
        "南宋三学所称宗学按正式词头复用宗子学。",
    )
    finish(w, touched, "整理北宋元丰前与南宋三学所指实例的变化。")


def entry866():
    i, quote = 866, F[866]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "三馆", "机构", "北宋庆历四年前科场年",
        "开科场时临设广文馆、太学、律学，罢场即散",
        ("广文馆", "太学", "律学"), quote,
        "本条三馆为国子监临时三馆，不与文馆三馆另造同名实体。",
    )
    finish(w, touched, "在既有三馆正式词头补入庆历四年前学校三馆含义和三个实例。")


def entry867():
    i, quote = 867, F[867]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "二学", "机构", "北宋",
        "国子学、太学合称", ("国子学", "太学"), quote,
        "北宋二学所指国子学与太学。",
    )
    group_members(
        w, touched, i, "二学", "机构", "南宋",
        "文、武二学，即太学与武学", ("太学", "武学"), quote,
        "南宋文武二学所指太学与武学。",
    )
    finish(w, touched, "整理北宋与南宋二学所指实例变化。")


def entry868():
    i, quote = 868, F[868]["text"]
    w, touched = W(i), set()
    members = (
        "国子监祭酒", "国子监司业", "国子监博士", "太学博士",
        "武学博士", "国子监丞", "国子监主簿", "国子正", "国子录",
        "太学正", "太学录", "武学谕",
    )
    group_members(
        w, touched, i, "监学官", "官职", "南宋绍兴十三年至二十六年",
        "国子监及所属太学、武学、律学、小学诸学官总称",
        members, quote, "题名所列祭酒、司业、博士、丞、簿、正、录、武学谕均属监学官。",
    )
    finish(w, touched, "整理监学官正式统称及题名所见十二类官职实例。")


def entry869():
    i, quote = 869, F[869]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "太学", "学谕", "北宋熙宁四年十月十七日", quote,
        "熙宁四年太学置职事学谕，每经二员，五经合十员。", quota=10,
        staff_type="学生职事人", office_event="增广太学并置职事学谕十员",
        post_event="上舍生充，分经传谕并季终考校行艺", officer="太学上舍生",
    )
    group_members(
        w, touched, i, "学谕", "官职", "宋代（未载具体年月）",
        "依任职身份分职事学谕与命官学谕", ("职事学谕", "命官学谕"),
        quote, "学谕分学生充任的职事学谕与命官学谕。",
    )
    group_members(
        w, touched, i, "命官学谕", "官职", "宋代（未载具体年月）",
        "武学谕、宗学谕属于命官学谕", ("武学谕", "宗子学谕"), quote,
        "宗学谕按正式词头复用宗子学谕。",
    )
    for school in ("辟雍", "算学", "书学", "画学", "州县学"):
        office_staff(
            w, touched, i, school, "学谕", "北宋徽宗朝（年月未载）", quote,
            f"北宋徽宗朝{school}设置学谕。", staff_type="学谕",
            office_event="设置学谕", post_event=f"在{school}传谕考校",
        )
    cite(w, "Timepoints", post, i, quote,
         "补证太学学谕传经、兼讲与考校职掌。")
    finish(w, touched, "整理学谕熙宁始置、十员额、职事与命官分类及诸学设置。")


def entry870():
    i, quote = 870, F[870]["text"]
    w, touched = W(i), set()
    _, command_post, _ = office_staff(
        w, touched, i, "国子监", "命官直学",
        "北宋治平二年七月二十四日", quote,
        "治平二年始见国子监置命官直学。", staff_type="命官学官",
        office_event="始置命官直学", post_event="掌学生名籍、校门出入及斋仆",
        officer="命官",
    )
    group_members(
        w, touched, i, "直学", "官职", "宋代（未载具体年月）",
        "依任职身份分职事直学与命官直学", ("职事直学", "命官直学"),
        quote, "直学兼有学生职事人与命官学官两种性质。",
    )
    for school, time in (
        ("太学", "两宋（年月未载）"),
        ("辟雍", "北宋徽宗朝（年月未载）"),
        ("宗子学", "南宋（年月未载）"),
        ("武学", "两宋（年月未载）"),
        ("州县学", "两宋（年月未载）"),
    ):
        office_staff(
            w, touched, i, school, "职事直学", time, quote,
            f"{school}设置职事直学。", staff_type="学生职事人",
            office_event="设置职事直学",
            post_event="掌学生名籍、纠察出入校门并管斋仆", officer="学生",
        )
    for school in ("太学", "辟雍"):
        office_staff(
            w, touched, i, school, "命官直学", "北宋徽宗朝（年月未载）", quote,
            f"徽宗朝{school}设置命官直学。", staff_type="命官学官",
            office_event="设置命官直学", post_event="以命官充直学", officer="命官",
        )
    cite(w, "Timepoints", command_post, i, quote,
         "补证直学掌名籍、校门出入与斋仆。")
    finish(w, touched, "整理直学治平始见、命官与职事分类、职掌及各学设置。")


def entry871():
    i, quote = 871, F[871]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "太学", "斋长", "北宋元丰二年", quote,
        "元丰二年太学八十斋，每斋置斋长一员。", quota=80,
        staff_type="学生小职事", office_event="八十斋各设斋长一员",
        post_event="为斋生表率，执行斋规并月考行艺", officer="学生",
    )
    office_staff(
        w, touched, i, "宗子学", "斋长", "南宋嘉定七年", quote,
        "嘉定七年宗学六斋，每斋置斋长一员。", quota=6,
        staff_type="学生小职事", office_event="六斋各设斋长一员",
        post_event="由学生充，经学谕、正录、博士荐定", officer="学生",
    )
    for school, time in (
        ("辟雍", "北宋（年月未载）"),
        ("律学", "两宋（年月未载）"),
        ("武学", "两宋（年月未载）"),
        ("在京小学", "两宋（年月未载）"),
        ("州县学", "两宋（年月未载）"),
    ):
        office_staff(
            w, touched, i, school, "斋长", time, quote,
            f"{school}分斋并设置斋长。", staff_type="学生小职事",
            office_event="分斋设置斋长", post_event="一斋学生表率并执行斋规",
            officer="学生",
        )
    finish(w, touched, "整理斋长在太学、宗学及诸学的设置、分斋员额、学生身份和职掌。")


def entry872():
    i, quote = 872, F[872]["text"]
    w, touched = W(i), set()
    for school, time in (
        ("太学", "两宋（年月未载）"),
        ("辟雍", "北宋（年月未载）"),
        ("律学", "两宋（年月未载）"),
        ("武学", "两宋（年月未载）"),
        ("在京小学", "两宋（年月未载）"),
        ("宗子学", "南宋（年月未载）"),
        ("州县学", "两宋（年月未载）"),
    ):
        office_staff(
            w, touched, i, school, "斋谕", time, quote,
            f"{school}每斋设置斋谕一员。",
            staff_type="学生小职事", office_event="每斋设置斋谕一员",
            post_event="佐斋长管理本斋、执行斋规并月考行艺", officer="学生",
        )
    finish(w, touched, "据斋谕条及所参斋长条整理诸学每斋斋谕、学生身份与共同职掌。")


def entry873():
    i, quote = 873, F[873]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "长谕", "官职", "宋代（未载具体年月）",
        "斋长、斋谕连称", ("斋长", "斋谕"), quote,
        "长谕是斋长与斋谕的连称。",
    )
    finish(w, touched, "整理长谕正式连称及斋长、斋谕两个实例。")


def entry874():
    i, quote = 874, F[874]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "职事人", "官职", "宋代（未载具体年月）",
        "学生充任而非命官的学校职事总称",
        ("职事学正", "职事学录", "职事学谕", "职事直学", "斋长", "斋谕"),
        quote, "原文明确职事人的六类实例。",
    )
    group_members(
        w, touched, i, "职事人", "官职", "南宋嘉定七年",
        "分大职事与小职事", ("大职事", "小职事"), quote,
        "宗学材料明确职事人分大、小职事。",
    )
    office_staff(
        w, touched, i, "宗子学", "职事人", "南宋绍兴五年", quote,
        "绍兴五年宗学生一百员中大学、小学职事人各五，共十人。", quota=10,
        staff_type="学生职事人", office_event="大学、小学职事人各五",
        post_event="学生充任的大、小职事共十人", officer="宗学生",
    )
    finish(w, touched, "整理职事人总称、六类实例、大细职事分类及宗学十人编制。")


def entry875():
    i, quote, aliases = 875, F[875]["text"], field(875, "别称")
    w, touched = W(i), set()
    group_tp = group_members(
        w, touched, i, "大职事", "官职", "宋代（未载具体年月）",
        "职事学正、学录、学谕、直学合称",
        ("职事学正", "职事学录", "职事学谕", "职事直学"), quote,
        "大职事明确包括四类学生职事人。",
    )
    office_staff(
        w, touched, i, "武学", "大职事", "宋代（未载具体年月）", quote,
        "武学大职事三名。", quota=3, staff_type="学生大职事",
        office_event="设置大职事三名", post_event="由学生充任学正录谕直学",
        officer="学生",
    )
    alias_note(w, i, group_tp, aliases, "别称")
    finish(w, touched, "整理大职事四个实例、武学三名编制及前廊职事别称。")


def entry876():
    i, quote = 876, F[876]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "小职事", "官职", "宋代（未载具体年月）",
        "学生充任的斋长、斋谕合称", ("斋长", "斋谕"), quote,
        "小职事明确包括斋长、斋谕。",
    )
    office_staff(
        w, touched, i, "武学", "小职事", "宋代（未载具体年月）", quote,
        "武学小职事十一人。", quota=11, staff_type="学生小职事",
        office_event="设置小职事十一人", post_event="由学生充任斋长、斋谕",
        officer="学生",
    )
    finish(w, touched, "整理小职事两个实例、学生身份及武学十一人编制。")


def entry877():
    i = 877
    main, origin, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别称"),
    )
    w, touched = W(i), set()
    stages = (
        ("北宋崇宁二年九月十五日", "始置"),
        ("北宋崇宁五年正月十二日", "罢置"),
        ("北宋大观元年二月十八日", "复置"),
        ("北宋大观四年三月二日", "又罢，医学生并入太医局"),
        ("北宋政和三年闰四月一日", "复置并改称太医学"),
        ("北宋宣和二年七月二十一日", "罢在京医学，医学三舍生并入太学"),
    )
    for time, event in stages:
        node(w, touched, i, "医学", "机构", time, event, origin,
             "中央医学官学", f"建立医学{time}沿革节点。", "职源与沿革")
    for time in (
        "北宋崇宁二年九月十五日", "北宋大观元年二月十八日",
        "北宋政和三年闰四月一日",
    ):
        parent_child(
            w, touched, i, "国子监", "医学", time, main,
            f"{time}医学隶国子监。",
            parent_event="统辖医学", child_event="隶国子监",
        )
    function_tp = node(
        w, touched, i, "医学", "机构", "北宋崇宁二年九月十五日",
        "于太医局外教养上医，为州县输送医学教授等技术人",
        duty, "中央医学官学", "补证医学教养与输送技术人才职掌。", "职掌",
    )
    for post, quota, staff_type in (
        ("医学博士", 4, "博士"), ("医学正", 4, "学正"), ("医学录", 4, "学录"),
    ):
        office_staff(
            w, touched, i, "医学", post, "北宋崇宁二年九月十五日", roster,
            f"在京医学设置{post}{quota}员。", "编制", quota=quota,
            staff_type=staff_type, office_event="设置医学官与学生",
            post_event=f"在京医学{post}，编制{quota}员",
        )
    for section in ("方脉科", "针科", "伤科", "风科"):
        parent_child(
            w, touched, i, "医学", section, "北宋崇宁二年九月十五日", roster,
            f"医学设置{section}。", "编制",
            parent_event="设置四科", child_event="医学所属教学科",
        )
    office_staff(
        w, touched, i, "医学", "医学生", "北宋崇宁二年九月十五日", roster,
        "医学招医学生三百人。", "编制", quota=300, staff_type="学生",
        office_event="医学生三百人，分三舍", post_event="三舍学生总额三百人",
    )
    for title, quota in (
        ("医学上舍生", 40), ("医学内舍生", 60), ("医学外舍生", 200),
    ):
        office_staff(
            w, touched, i, "医学", title, "北宋崇宁二年九月十五日", roster,
            f"医学{title}编制{quota}人。", "编制", quota=quota,
            staff_type="学生", office_event="医学生三百人，分三舍",
            post_event=f"医学三舍学生，编制{quota}人",
        )
    group_members(
        w, touched, i, "医学生", "官职", "北宋崇宁二年九月十五日",
        "分上舍、内舍、外舍三类",
        ("医学上舍生", "医学内舍生", "医学外舍生"), roster,
        "医学生三百人按三舍分为三个实例。", "编制",
    )
    cite(w, "Timepoints", function_tp, i, roster,
         "补证医学官额、四科与三舍生额。", "编制")
    alias_note(w, i, function_tp, aliases, "别称")
    finish(w, touched, "整理医学崇宁至宣和置废、国子监隶属、职掌、官额、四科、三舍生额与太医学别称。")


def entry878():
    i, quote = 878, F[878]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "医学", "医学博士", "北宋崇宁二年九月十五日", quote,
        "崇宁二年始置医学博士四人。", quota=4, staff_type="博士",
        office_event="始置医学博士四员", post_event="分科教养医学生",
    )
    node(
        w, touched, i, "医学博士", "官职", "北宋宣和二年七月二十一日",
        "随在京医学罢废", quote, "医学医官",
        "建立医学博士宣和二年罢废节点。",
    )
    cite(w, "Timepoints", post, i, quote, "补证医学博士其后或罢或置及分科教养职掌。")
    finish(w, touched, "整理医学博士崇宁始置、四人编制、分科教养与宣和罢废链。")


def medical_discipline_office(i, title, duty):
    quote = F[i]["text"]
    w, touched = W(i), set()
    stages = (
        ("北宋崇宁二年九月十五日", "始置", True),
        ("北宋崇宁五年正月十二日", "随医学罢置", False),
        ("北宋大观元年二月十八日", "随医学复置", True),
        ("北宋大观四年三月二日", "随医学又罢", False),
        ("北宋政和三年闰四月一日", "随医学复置", True),
        ("北宋宣和二年七月二十一日", "随在京医学罢废", False),
    )
    for time, event, active in stages:
        if active:
            office_staff(
                w, touched, i, "医学", title, time, quote,
                f"{title}置废沿革与医学相同，复置时编制四人。", quota=4,
                staff_type="医官", office_event=f"复置并设置{title}四人",
                post_event=duty,
            )
        else:
            node(
                w, touched, i, title, "官职", time, event, quote,
                "医学医官", f"建立{title}{time}罢置节点。",
            )
    finish(w, touched, f"按医学完整置废链整理{title}四人编制与职掌。")


def entry879():
    medical_discipline_office(879, "医学正", "掌纠行医学生规矩")


def entry880():
    medical_discipline_office(880, "医学录", "佐医学正纠行学生规矩")


def main():
    for i in range(861, 881):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
