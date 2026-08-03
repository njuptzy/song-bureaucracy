#!/usr/bin/env python3
"""提取 chapter5t7 第801-820条：太学上舍生、辟雍及其官属。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_781_800 as previous


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


F = {i: load(i) for i in range(801, 821)}
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
    "西周": -1000, "唐龙朔二年": 662,
    "北宋熙宁四年十月": 1071.80,
    "北宋元丰旧制": 1080, "北宋元丰二年": 1079,
    "北宋崇宁元年": 1102, "北宋崇宁元年八月二十七日": 1102.64,
    "北宋崇宁二年": 1103, "北宋崇宁三年": 1104,
    "北宋崇宁间": 1104.2,
    "北宋崇宁四年闰二月十七日": 1105.16,
    "北宋崇宁、大观年间": 1106,
    "北宋大观间": 1108,
    "北宋大观四年八月十二日": 1110.65,
    "北宋大观四年以后（年月未载）": 1110.70,
    "北宋宣和元年三月": 1119.20,
    "北宋宣和三年二月": 1121.12,
    "北宋宣和三年二月二十日": 1121.13,
    "北宋崇宁三年至宣和三年二月": 1104,
    "北宋崇宁至宣和间": 1102,
    "南宋绍兴十五年": 1145,
    "南宋淳熙间": 1175,
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


def group_members(w, touched, i, group_title, time, event, members,
                  quotation, decision, field_name=None):
    group_tid = node(
        w, touched, i, group_title, "官职", time, event, quotation,
        "官职统称", f"建立{group_title}{time}统称节点。", field_name,
    )
    for member_title in members:
        member_tid = node(
            w, touched, i, member_title, "官职", time,
            f"{group_title}在{time}所指实例", quotation,
            f"{group_title}实例", f"建立或复用{member_title}{time}实例节点。",
            field_name,
        )
        relation(
            w, i, group_tid, member_tid, "统称与实例", quotation,
            f"{member_title}是{group_title}的实例。", field_name,
        )
    return group_tid


def canonicalize_biyong(w, i, quotation):
    canonical = w.find_entity("辟雍", "机构")
    old = w.find_entity("辟雍外学", "机构")
    if canonical is not None:
        assert old is None, "辟雍与辟雍外学不应并存为两个实体"
        return canonical
    assert old is not None, "前批应已建立辟雍外学实体"
    w.conn.execute("update Entities set title='辟雍' where id=?", (old,))
    w._br(
        "Entities", old,
        "第805条正式词头为辟雍，别称字段明确外学只是别称；将前批按正文建立的"
        "辟雍外学实体规范为辟雍，保留原ID及全部关系。",
    )
    return old


def entry801():
    i = 801
    main, aliases = F[i]["text"], field(i, "简称与别名")
    w, touched = W(i), set()
    for time, quota, event in (
        ("北宋熙宁四年十月", 100, "三舍法始创上舍生，以一百员为额"),
        ("北宋崇宁间", 200, "上舍生曾增至二百员"),
        ("南宋绍兴十五年", 30, "太学初复，上舍生三十员，后不变"),
    ):
        office_staff(
            w, touched, i, "太学", "太学上舍生", time, main,
            f"{time}太学上舍生编制{quota}人。",
            quota=quota, staff_type="学生", office_event=event,
            post_event=event,
        )
    evolution(
        w, touched, i, "太学内舍生", "太学上舍生",
        "北宋熙宁四年十月", main,
        "三舍法下内舍生经上舍试与行艺考核升上舍生。",
        source_event="经上舍试与行艺考核升上舍",
        target_event="由内舍生升入，分上中下三等",
    )
    group_members(
        w, touched, i, "太学上舍生", "宋代（未载具体年月）",
        "依上舍试与行艺成绩分上、中、下三等",
        ("上等上舍生", "中等上舍生", "下等上舍生"), main,
        "原文明言上舍生分为三等。",
    )
    last = node(
        w, touched, i, "太学上舍生", "官职", "南宋淳熙间",
        "两优释褐恩例改视进士第二人，入等者许直赴廷对",
        main, "太学生上等", "建立淳熙间两优释褐恩例变化节点。",
    )
    alias_note(w, i, last, aliases, "简称与别名")
    finish(w, touched, "整理太学上舍生始置、分期生额、三等分类、升舍与南宋恩例链。")


def entry802():
    i = 802
    main, aliases = F[i]["text"], field(i, "简称与别名")
    w, touched = W(i), set()
    evolution(
        w, touched, i, "太学内舍生", "太学两优释褐人",
        "北宋元丰旧制", main,
        "内舍校定优等且上舍试又入优等者称太学两优释褐人。",
        source_event="校定优等并赴上舍试再入优等",
        target_event="两优释褐，恩例视状元，即命京官并除学官",
    )
    south = node(
        w, touched, i, "太学两优释褐人", "官职", "南宋淳熙间",
        "改为先除选人，代还再改职事官，恩例视进士第二人",
        main, "太学释褐称谓", "建立淳熙两优释褐授官恩例变化节点。",
        officer="先除选人，代还改职事官",
    )
    cite(
        w, "Timepoints", south, i, aliases,
        "补证两优释褐简称及最高分者称释褐状元。", "简称与别名",
        note="简称和最高分者称谓只作名称证据，不另建实体",
    )
    finish(w, touched, "整理太学两优释褐人的形成条件、北宋授官与南宋淳熙恩例变化链。")


def entry803():
    i, quote = 803, F[803]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "太学三舍生", "北宋元丰二年",
        "太学外舍生、内舍生、上舍生合称",
        ("太学外舍生", "太学内舍生", "太学上舍生"), quote,
        "原文明确太学三舍生及三个实例。",
    )
    finish(w, touched, "整理太学三舍生正式统称及外舍、内舍、上舍三个实例。")


def entry804():
    i, quote = 804, F[804]["text"]
    w, touched = W(i), set()
    node(
        w, touched, i, "俊士", "官职", "宋代（未载具体年月）",
        "外舍生升为内舍生时的称谓", quote, "太学生升舍称谓",
        "建立俊士正式词头及其升舍含义。",
    )
    finish(w, touched, "整理俊士为外舍生升内舍生之称谓。")


def entry805():
    i = 805
    origin, function, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "别称"),
    )
    w, touched = W(i), set()
    biyong_eid = canonicalize_biyong(w, i, aliases)
    touched.add(biyong_eid)
    for time, event in (
        ("西周", "学校已有辟雍之名"),
        ("北宋崇宁元年八月二十七日", "于京师南薰门建外学，赐名辟雍"),
        ("北宋崇宁三年", "建成"),
        ("北宋宣和三年二月二十日", "罢置"),
    ):
        node(w, touched, i, "辟雍", "机构", time, event, origin,
             "中央外学", f"建立辟雍{time}沿革节点。", "职源与沿革")
    function_tp = node(
        w, touched, i, "辟雍", "机构", "北宋崇宁三年",
        "接收州学贡士；外学生每年考核，合格者升太学",
        function, "中央外学", "补证辟雍承接州学、升太学的职能。", "职能",
    )
    office_staff(
        w, touched, i, "辟雍", "太学外舍生", "北宋崇宁三年", roster,
        "辟雍招收外舍生三千人。", "编制", quota=3000,
        staff_type="学生", office_event="建成一百斋，招外舍生三千人",
        post_event="在辟雍外学就读，编制三千人",
    )
    alias_note(w, i, function_tp, aliases, "别称")
    finish(w, touched, "规范辟雍正式词头，整理西周职源、崇宁建置、宣和罢置、职能与生额链。")


def entry806():
    i = 806
    main, origin, duty, rank, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "简称"),
    )
    w, touched = W(i), set()
    node(
        w, touched, i, "辟雍大司成", "官职", "唐龙朔二年",
        "以唐代国子监大司成为职源", origin, "辟雍长官",
        "建立辟雍大司成唐代职源节点。", "职源与沿革",
    )
    _, post, _ = office_staff(
        w, touched, i, "辟雍", "辟雍大司成", "北宋崇宁二年", origin,
        "崇宁二年辟雍置大司成。", "职源与沿革",
        quota=1, staff_type="长官", office_event="设置大司成一员",
        post_event="领辟雍外学公事，为师儒之首",
    )
    office_staff(
        w, touched, i, "国子监", "辟雍大司成", "北宋崇宁二年", main,
        "辟雍大司成隶国子监。", staff_type="所属学官",
        office_event="统辖辟雍大司成", post_event="隶国子监并领辟雍公事",
    )
    evolution(
        w, touched, i, "辟雍大司成", "太学大司成",
        "北宋崇宁四年闰二月十七日", origin,
        "崇宁四年辟雍大司成改为太学大司成。", "职源与沿革",
        source_event="改名太学大司成", target_event="由辟雍大司成改名",
    )
    cite(w, "Timepoints", post, i, duty, "补证领辟雍公事与训导职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证辟雍大司成班位。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理辟雍大司成职源、崇宁设置、国子监隶属、职掌品位及改名链。")


def entry807():
    i = 807
    origin, duty, rank, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "简称"),
    )
    w, touched = W(i), set()
    evolution(
        w, touched, i, "辟雍大司成", "太学大司成",
        "北宋崇宁四年闰二月十七日", origin,
        "崇宁四年辟雍大司成改名太学大司成。", "职源与沿革",
        source_event="改名太学大司成", target_event="由辟雍大司成改名",
    )
    _, post, _ = office_staff(
        w, touched, i, "国子监", "太学大司成",
        "北宋崇宁四年闰二月十七日", duty,
        "太学大司成总掌国子监及内、外学公事。", "职掌",
        staff_type="总掌学官", office_event="设置太学大司成总掌内外学",
        post_event="总掌国子监及太学、辟雍公事，学校事许直达皇帝",
    )
    node(
        w, touched, i, "太学大司成", "官职",
        "北宋宣和三年二月二十日", "罢置", origin,
        "国子监总掌学官", "建立太学大司成宣和三年罢置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", post, i, rank, "补证太学大司成班位。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理太学大司成由辟雍大司成改名、总掌内外学、品位与宣和罢置链。")


def entry808():
    i, main, aliases = 808, F[808]["text"], field(808, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "辟雍", "辟雍司业", "北宋崇宁元年", main,
        "崇宁元年辟雍置司业一人。", quota=1, staff_type="司业",
        office_event="设置司业一人", post_event="佐大司成掌外学训导，品位视国子监司业",
    )
    node(w, touched, i, "辟雍司业", "官职", "北宋宣和三年二月",
         "罢置", main, "辟雍学官", "建立辟雍司业宣和三年罢置节点。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理辟雍司业崇宁设置、职掌品位与宣和罢置链。")


def entry809():
    i, main, aliases = 809, F[809]["text"], field(809, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "辟雍", "辟雍丞", "北宋崇宁元年", main,
        "崇宁元年辟雍置丞一人。", quota=1, staff_type="丞",
        office_event="设置丞一人", post_event="参领辟雍外学公事，品位视国子监丞",
    )
    node(w, touched, i, "辟雍丞", "官职", "北宋宣和三年二月二十日",
         "罢置", main, "辟雍学官", "建立辟雍丞宣和三年罢置节点。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理辟雍丞崇宁设置、职掌品位与宣和罢置链。")


def entry810():
    i, quote = 810, F[810]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "辟雍", "辟雍主簿", "北宋崇宁元年", quote,
        "崇宁元年辟雍置主簿，掌簿书勾考。", staff_type="主簿",
        office_event="设置主簿", post_event="掌本学簿书勾考，品位视五监主簿",
    )
    node(w, touched, i, "辟雍主簿", "官职", "北宋宣和三年二月二十日",
         "罢置", quote, "辟雍职事官", "建立辟雍主簿宣和三年罢置节点。")
    finish(w, touched, "整理辟雍主簿崇宁设置、簿书勾考职掌、品位与宣和罢置链。")


def entry811():
    i, main, aliases = 811, F[811]["text"], field(811, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "辟雍", "辟雍博士", "北宋崇宁元年", main,
        "崇宁元年辟雍置博士十人，每经二人。", quota=10,
        staff_type="博士", office_event="设置博士十人",
        post_event="分经讲授、考校外学生程文，每经二人",
    )
    node(w, touched, i, "辟雍博士", "官职", "北宋宣和三年二月二十日",
         "罢置", main, "辟雍学官", "建立辟雍博士宣和三年罢置节点。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理辟雍博士崇宁设置、十人编制、训导职掌与宣和罢置链。")


def entry812():
    i, main, aliases = 812, F[812]["text"], field(812, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "辟雍", "辟雍正", "北宋崇宁元年", main,
        "崇宁元年辟雍置正五员。", quota=5, staff_type="学正",
        office_event="设置学正五员",
        post_event="施行学规、处分违规则生员并考校训导报博士",
    )
    node(w, touched, i, "辟雍正", "官职", "北宋宣和三年二月二十日",
         "罢置", main, "辟雍学官", "建立辟雍正宣和三年罢置节点。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理辟雍正崇宁设置、五人编制、学规考校职掌与宣和罢置链。")


def entry813():
    i, quote = 813, F[813]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "辟雍", "辟雍录", "北宋崇宁元年", quote,
        "崇宁元年辟雍置录五人。", quota=5, staff_type="学录",
        office_event="设置学录五人",
        post_event="佐辟雍正纠察、考校外学生，编制五人",
    )
    node(w, touched, i, "辟雍录", "官职", "北宋宣和三年二月二十日",
         "罢置", quote, "辟雍学官", "建立辟雍录宣和三年罢置节点。")
    cite(w, "Timepoints", post, i, quote, "补证辟雍录简称为录。",
         note="纯简称不另建实体")
    finish(w, touched, "整理辟雍录崇宁设置、五人编制、纠察考校职掌与宣和罢置链。")


def entry814():
    i, quote = 814, F[814]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "命官正录", "北宋崇宁年间",
        "以享有秩禄、由朝廷除授的命官充任正、录者的合称",
        ("辟雍正", "辟雍录"), quote,
        "命官正录相对于学生或职事正录，原文明确包括命官充任的正、录。",
    )
    finish(w, touched, "整理命官正录正式统称及辟雍正、辟雍录实例。")


def entry815():
    i, quote = 815, F[815]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "辟雍", "辟雍直学", "北宋崇宁元年", quote,
        "崇宁元年初建辟雍时置学生职事直学四人。", quota=4,
        staff_type="学生职事直学", office_event="设置学生直学四人",
        post_event="由学生充，掌学生名册及监视出入校门",
        officer="学生",
    )
    office_staff(
        w, touched, i, "辟雍", "辟雍直学", "北宋大观间", quote,
        "大观间辟雍置命官直学。", staff_type="命官直学",
        office_event="设置命官直学", post_event="由朝廷命官差充",
        officer="命官",
    )
    for time, event in (
        ("北宋大观四年八月十二日", "罢置命官直学"),
        ("北宋大观四年以后（年月未载）", "后复置"),
        ("北宋宣和元年三月", "诏除授如博士、正、录，给告命"),
    ):
        node(w, touched, i, "辟雍直学", "官职", time, event, quote,
             "辟雍学官", f"建立辟雍直学{time}节点。",
             officer="命官" if time != "北宋大观四年八月十二日" else None)
    group_members(
        w, touched, i, "辟雍直学", "北宋崇宁、大观年间",
        "依充任者身份分命官直学与学生直学",
        ("命官直学", "学生直学"), quote,
        "原文明确辟雍直学有命官与学生充任两类。",
    )
    finish(w, touched, "整理辟雍直学学生与命官两类、职掌、大观罢复及宣和给告命链。")


def entry816():
    i, quote = 816, F[816]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "辟雍", "命官直学", "北宋崇宁、大观年间", quote,
        "命官辟雍直学由朝廷除授命官差充并给告。",
        staff_type="命官直学", office_event="设置命官直学",
        post_event="朝廷除授命官差充，给告", officer="命官",
    )
    finish(w, touched, "整理命官直学与学生直学之别、朝廷除授和给告制度。")


def entry817():
    i, quote = 817, F[817]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "辟雍", "学生直学", "北宋崇宁元年", quote,
        "辟雍学生直学由学生充任，无视品，给敕而不给告。",
        staff_type="学生职事人", office_event="由学生充任直学",
        post_event="无视品，月支添食钱，给敕而不给告", officer="学生",
    )
    finish(w, touched, "整理学生直学的学生身份、无视品、添食钱及给敕不给告。")


def entry818():
    i, quote = 818, F[818]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "辟雍", "贡士",
        "北宋崇宁三年至宣和三年二月", quote,
        "崇宁三年至宣和三年二月，州学选试升辟雍者称贡士。",
        staff_type="学生", office_event="接收州学选试升入的贡士",
        post_event="由州学选试升辟雍，分文、武两类",
    )
    finish(w, touched, "整理贡士在崇宁至宣和间由州学升辟雍及文武分类。")


def entry819():
    i, quote = 819, F[819]["text"]
    w, touched = W(i), set()
    node(
        w, touched, i, "进士", "官职", "北宋崇宁至宣和间",
        "文士由乡升县学、再由县学升州学时的通称",
        quote, "学校生员称谓", "建立崇宁至宣和间学校进士称谓节点。",
    )
    finish(w, touched, "整理崇宁至宣和间文士由乡、县学升州学时通称进士。")


def entry820():
    i, quote = 820, F[820]["text"]
    w, touched = W(i), set()
    node(
        w, touched, i, "文士", "官职", "宋代（未载具体年月）",
        "攻读经术、律法、算学并报考太学或律学、算学等专门学者的泛称",
        quote, "学校生员泛称", "建立文士正式词头及其所指范围。",
    )
    finish(w, touched, "整理文士为报考太学及律、算等专门学者的泛称。")


def main():
    for i in range(801, 821):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
