#!/usr/bin/env python3
"""提取 chapter5t7 第821-840条：武学、律学及其官属与学生。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_801_820 as previous


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


F = {i: load(i) for i in range(821, 841)}
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
    "西晋武帝咸宁四年": 278, "唐": 618, "唐开元间": 720,
    "唐贞元元年": 785, "宋初": 960, "宋初科场年": 970,
    "北宋初": 970, "北宋庆历二年十二月三日": 1042.94,
    "北宋庆历三年五月二十一日": 1043.39,
    "北宋庆历三年八月二十四日": 1043.64,
    "北宋熙宁五年六月二十七日": 1072.48,
    "北宋熙宁六年三月二十七日": 1073.22,
    "北宋熙宁六年四月二日": 1073.26,
    "北宋熙宁六年四月二十四日": 1073.32,
    "北宋熙宁十年六月": 1077.47,
    "北宋元丰五年": 1082, "北宋元丰新制": 1082.1,
    "北宋元丰后（年月未载）": 1083,
    "北宋元祐三年九月二十二日": 1088.72,
    "北宋崇宁间": 1104, "北宋崇宁以后（年月未载）": 1106,
    "北宋徽宗朝": 1107, "北宋崇宁至宣和初": 1104,
    "北宋崇宁至宣和三年": 1104.1, "北宋宣和二年": 1120,
    "南宋初": 1127, "南宋绍兴十六年三月初一": 1146.18,
    "南宋绍兴二十六年四月": 1156.30,
    "南宋绍兴二十六年以后": 1156.4,
    "南宋": 1130, "宋代（未载具体年月）": 1100,
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


def entry821():
    i = 821
    main, origin, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别称"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("唐开元间", "始置太公师父庙，尚未设武学校"),
        ("唐贞元元年", "尊吕尚为武成王并立庙，尚未设武学校"),
        ("北宋庆历三年五月二十一日", "始在武成王庙办武学"),
        ("北宋庆历三年八月二十四日", "罢置"),
        ("北宋熙宁五年六月二十七日", "复置"),
        ("南宋初", "罢置"),
        ("南宋绍兴十六年三月初一", "诏重建，实际未举行"),
        ("南宋绍兴二十六年四月", "始正式张官养士，成为南宋三学之一"),
    ):
        node(w, touched, i, "武学", "机构", time, event, origin,
             "中央官学", f"建立武学{time}沿革节点。", "职源与沿革")
    for time in (
        "北宋庆历三年五月二十一日", "北宋熙宁五年六月二十七日",
        "南宋绍兴二十六年四月",
    ):
        parent_child(
            w, touched, i, "国子监", "武学", time, main,
            f"{time}武学隶国子监。",
            parent_event="统辖武学", child_event="隶国子监",
        )
    node(
        w, touched, i, "武学", "机构", "北宋熙宁五年六月二十七日",
        "招收使臣、门荫子弟与草泽人，教兵法兵书和阵队实习，三年结业授武职",
        duty, "中央官学", "补证武学招生、教学、学制和授职。", "职掌",
    )
    for time, quota in (
        ("北宋熙宁五年六月二十七日", 100),
        ("北宋徽宗朝", 200),
        ("南宋绍兴二十六年四月", 100),
    ):
        office_staff(
            w, touched, i, "武学", "武学生", time, roster,
            f"{time}武学生总额{quota}人。", "编制",
            quota=quota, staff_type="学生", office_event=f"武学生定额{quota}人",
            post_event=f"武学生总额{quota}人，实行三舍法",
        )
    for time, quotas in (
        ("北宋徽宗朝", (("武学上舍生", 30), ("武学内舍生", 70), ("武学外舍生", 100))),
        ("南宋绍兴二十六年四月", (("武学上舍生", 10), ("武学内舍生", 20), ("武学外舍生", 70))),
    ):
        for post, quota in quotas:
            office_staff(
                w, touched, i, "武学", post, time, roster,
                f"{time}{post}编制{quota}人。", "编制",
                quota=quota, staff_type="学生", office_event=f"设置{post}{quota}人",
                post_event=f"三舍学生，编制{quota}人",
            )
    alias_tp = node(
        w, touched, i, "武学", "机构", "北宋熙宁五年六月二十七日",
        "复置", aliases, "中央官学", "补证武学别称右学。", "别称",
    )
    alias_note(w, i, alias_tp, aliases, "别称")
    finish(w, touched, "整理武学唐代庙学职源、宋代建置罢复、国子监隶属、职掌与三舍生额链。")


def entry822():
    i = 822
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("北宋庆历二年十二月三日", "诏置"),
        ("北宋庆历三年五月二十一日", "始除人"),
    ):
        node(w, touched, i, "武学教授", "官职", time, event, origin,
             "武学学官", f"建立武学教授{time}节点。", "职源与沿革")
    for time, quota in (
        ("北宋庆历三年五月二十一日", 1),
        ("北宋熙宁十年六月", 4),
    ):
        _, post, _ = office_staff(
            w, touched, i, "武学", "武学教授", time, roster,
            f"{time}武学教授编制{quota}人。", "编制",
            quota=quota, staff_type="教授", office_event=f"设置教授{quota}人",
            post_event="传授兵书武艺、编纂战史忠义并指导阵队演习",
        )
    evolution(
        w, touched, i, "武学教授", "武学博士", "北宋元丰五年", origin,
        "元丰五年武学教授改为武学博士。", "职源与沿革",
        source_event="改为武学博士", target_event="由武学教授改置",
    )
    cite(w, "Timepoints", post, i, main, "正文明确武学教授隶国子监。")
    cite(w, "Timepoints", post, i, duty, "补证武学教授训导职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证武学教授可由文武臣充任且品位不一。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理武学教授庆历设置、分期编制、职掌品位及元丰改博士链。")


def entry823():
    i, main, aliases = 823, F[823]["text"], field(823, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "武学", "武学传授", "北宋熙宁五年六月二十七日", main,
        "熙宁置武学传授，位于教授之下。", staff_type="传授",
        office_event="设置武学传授", post_event="佐教授讲释兵书兵法战史并训诱武学生",
    )
    office_staff(
        w, touched, i, "武学", "武学传授", "北宋熙宁十年六月", main,
        "熙宁十年武学传授编制二员。", quota=2, staff_type="传授",
        office_event="传授定额二员", post_event="编制二员",
    )
    evolution(
        w, touched, i, "武学传授", "武学谕", "北宋元丰五年", main,
        "武学传授之职由元丰新制后的武学谕承接。",
        source_event="职事由武学谕承接", target_event="承接武学传授职事",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理武学传授熙宁设置、两人编制、职掌及元丰后由武学谕承接链。")


def entry824():
    i = 824
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    evolution(
        w, touched, i, "武学教授", "武学博士", "北宋元丰五年", origin,
        "元丰五年武学教授改为武学博士。", "职源与沿革",
        source_event="改为武学博士", target_event="由武学教授改置",
    )
    for time, event in (
        ("南宋初", "罢置"),
        ("南宋绍兴十六年三月初一", "复置"),
    ):
        node(w, touched, i, "武学博士", "官职", time, event, origin,
             "武学学官", f"建立武学博士{time}节点。", "职源与沿革",
             grade="从八品")
    for time, quota in (
        ("北宋元丰新制", 3),
        ("南宋绍兴十六年三月初一", 1),
    ):
        _, post, _ = office_staff(
            w, touched, i, "武学", "武学博士", time, roster,
            f"{time}武学博士编制{quota}人。", "编制",
            quota=quota, staff_type="博士", office_event=f"设置博士{quota}人",
            post_event="以兵法七书和弓马技艺训诱武学生",
            grade="从八品",
        )
    cite(w, "Timepoints", post, i, main, "正文明确武学博士隶国子监。")
    cite(w, "Timepoints", post, i, duty, "补证武学博士职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证武学博士从八品与班位。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理武学博士元丰改置、南宋罢复、职掌品位与分期编制链。")


def entry825():
    i = 825
    origin, duty, roster, rank, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制"),
        field(i, "品位"), field(i, "简称"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("北宋元丰新制", "始置"),
        ("南宋初", "罢置"),
        ("南宋绍兴十六年三月初一", "复置"),
    ):
        node(w, touched, i, "武学谕", "官职", time, event, origin,
             "武学学官", f"建立武学谕{time}节点。", "职源与沿革",
             officer="武举出身人", grade="正九品")
    for time, quota in (
        ("北宋元丰新制", 2),
        ("南宋绍兴十六年三月初一", 1),
    ):
        _, post, _ = office_staff(
            w, touched, i, "武学", "武学谕", time, roster,
            f"{time}武学谕编制{quota}人。", "编制",
            quota=quota, staff_type="学谕", office_event=f"设置武学谕{quota}人",
            post_event="职掌同武学博士，差武举出身人充",
            officer="武举出身人", grade="正九品",
        )
    cite(w, "Timepoints", post, i, duty, "补证武学谕职掌同武学博士。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证武学谕任职资格及正九品。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理武学谕元丰始置、南宋罢复、职掌、品位和分期编制链。")


def entry826():
    i, main, aliases = 826, F[826]["text"], field(826, "简称")
    w, touched = W(i), set()
    for time, event, quota in (
        ("北宋元丰新制", "由武学生充，掌本学规矩", 1),
        ("南宋绍兴二十六年四月", "复置并兼学录", 1),
    ):
        _, post, _ = office_staff(
            w, touched, i, "武学", "武学正", time, main,
            f"{time}武学正一人。", quota=quota, staff_type="学生职事人",
            office_event="设置武学正一人", post_event=event,
            officer="武学生",
        )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理武学正由学生充、掌学规、南宋复置兼学录及一人编制。")


def entry827():
    i, main, aliases = 827, F[827]["text"], field(827, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "武学", "武学录", "北宋元丰新制", main,
        "北宋武学录一人，由武学生充。", quota=1,
        staff_type="学生职事人", office_event="设置武学录一人",
        post_event="由武学生充，佐正掌本学规矩", officer="武学生",
    )
    evolution(
        w, touched, i, "武学录", "武学正", "南宋绍兴二十六年四月", main,
        "南宋不单置武学录，其职由武学正兼。",
        source_event="不再单置，职事归武学正兼",
        target_event="兼掌武学录职事",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理武学录北宋学生选充与南宋不置、由武学正兼领链。")


def entry828():
    i, quote = 828, F[828]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "武学", "司计", "北宋崇宁间", quote,
        "崇宁间武学司计掌公厨会计，由三班使臣充。",
        staff_type="职事人", office_event="设置司计掌公厨会计",
        post_event="掌武学公厨会计，由三班使臣充", officer="三班使臣",
    )
    node(
        w, touched, i, "司计", "官职", "北宋崇宁以后（年月未载）",
        "后改由武学生充", quote, "武学职事人",
        "建立司计改由学生充任节点。", officer="武学生",
    )
    office_staff(
        w, touched, i, "武学", "武学直学", "南宋绍兴二十六年以后", quote,
        "绍兴二十六年后司计职事由武学直学兼。",
        staff_type="兼司计", office_event="司计职事改由直学兼",
        post_event="兼掌司计公厨会计事",
    )
    finish(w, touched, "整理司计武学隶属、崇宁充任身份变化及南宋由直学兼领链。")


def entry829():
    i, quote = 829, F[829]["text"]
    w, touched = W(i), set()
    for time, event in (
        ("北宋熙宁五年六月二十七日", "经保明及人材、弓马武艺考试入学，学制三年"),
        ("北宋崇宁至宣和三年", "在京武学生由州县武学武士升贡"),
        ("北宋宣和二年", "罢州县武学，恢复熙丰招生法"),
    ):
        node(w, touched, i, "武学生", "官职", time, event, quote,
             "武学生员", f"建立武学生{time}制度节点。")
    group_members(
        w, touched, i, "武学生", "宋代（未载具体年月）",
        "依太学三舍制分外舍、内舍、上舍",
        ("武学外舍生", "武学内舍生", "武学上舍生"), quote,
        "原文明言武学生依三舍法分为三个等级。",
    )
    finish(w, touched, "整理武学生招生、三年学制、结业授职、三舍分类及崇宁至宣和升贡变化。")


def entry830():
    i, quote = 830, F[830]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "武选士", "官职", "宋代（未载具体年月）",
         "武学外舍生之称谓", quote, "武学生称谓",
         "建立武选士正式词头及其所指等级。")
    finish(w, touched, "整理武选士为武学外舍生称谓。")


def entry831():
    i, quote = 831, F[831]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "武俊士", "官职", "宋代（未载具体年月）",
         "武学内舍生之称谓", quote, "武学生称谓",
         "建立武俊士正式词头及其所指等级。")
    finish(w, touched, "整理武俊士为武学内舍生称谓。")


def entry832():
    i, quote = 832, F[832]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "武士", "官职", "宋代（未载具体年月）",
         "未入在京武学前习武艺士人的泛称", quote, "习武士人泛称",
         "建立武士正式词头及其泛称含义。")
    evolution(
        w, touched, i, "武士", "武贡士", "北宋崇宁至宣和初", quote,
        "武士由乡、县、州武学经试补升贡入在京武学，称武贡士。",
        source_event="由乡升县、州武学，经试补升贡",
        target_event="升贡入在京武学",
    )
    node(w, touched, i, "武士", "官职", "北宋宣和二年",
         "州县武学罢置，恢复熙丰法", quote, "习武士人泛称",
         "建立宣和二年武学制度变化节点。")
    finish(w, touched, "整理武士泛称、崇宁至宣和升武贡士及宣和二年制度变化链。")


def entry833():
    i, quote = 833, F[833]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "国子监", "律学馆", "宋初科场年", quote,
        "宋初科场年国子监临时设置律学馆。",
        parent_event="科场年临时设置律学馆",
        child_event="收应举明法科品官子弟，科场罢即解散",
    )
    for post, staff_type in (("律学博士", "博士"), ("律学助教", "助教")):
        office_staff(
            w, touched, i, "律学馆", post, "宋初科场年", quote,
            f"宋初临时律学馆置{post}。", staff_type=staff_type,
            office_event=f"临时设置{post}", post_event="训导应举明法科学生",
        )
    finish(w, touched, "整理宋初科场年临时律学馆、国子监隶属、招生及博士助教设置。")


def entry834():
    i, quote = 834, F[834]["text"]
    w, touched = W(i), set()
    for time, event in (
        ("西晋武帝咸宁四年", "国子学助教始置，为职源"),
        ("唐", "国子监律学助教始置"),
        ("宋初", "沿置"),
        ("北宋熙宁六年四月二日", "建正式律学后不置"),
    ):
        node(w, touched, i, "律学助教", "官职", time, event, quote,
             "律学学官", f"建立律学助教{time}沿革节点。")
    office_staff(
        w, touched, i, "律学馆", "律学助教", "宋初科场年", quote,
        "宋初临时律学馆沿置律学助教。", staff_type="助教",
        office_event="设置律学助教", post_event="律学馆学官",
    )
    finish(w, touched, "整理律学助教西晋职源、唐代始置、宋初沿置及熙宁律学建成后停置链。")


def entry835():
    i = 835
    main, origin, function, roster = (
        F[i]["text"], field(i, "职源与沿革"),
        field(i, "职能"), field(i, "编制"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("唐", "始置，为国子监六学之一"),
        ("北宋初", "以临时律学馆形式存在"),
        ("北宋熙宁六年四月二日", "正式设置律学"),
        ("南宋", "不置，改以科举明法新科取习法之士"),
    ):
        node(w, touched, i, "律学", "机构", time, event, origin,
             "法律官学", f"建立律学{time}沿革节点。", "职源与沿革")
    parent_child(
        w, touched, i, "国子监", "律学", "北宋熙宁六年四月二日",
        main, "熙宁六年正式律学隶国子监。",
        parent_event="设置并统辖律学", child_event="隶国子监",
    )
    node(
        w, touched, i, "律学", "机构", "北宋熙宁六年四月二日",
        "招命官与举人学习刑名，分习律令与习断案，结业从政为法官",
        function, "法律官学", "补证律学招生、专业与培养职能。", "职能",
    )
    for post, quota, staff_type in (
        ("律学教授", 4, "教授"), ("律学正", 1, "学生职事人"),
        ("律学录", 1, "学生职事人"),
    ):
        office_staff(
            w, touched, i, "律学", post, "北宋熙宁六年四月二日", roster,
            f"熙宁创置律学时置{post}{quota}人。", "编制",
            quota=quota, staff_type=staff_type, office_event=f"设置{post}{quota}人",
            post_event=f"律学官属，编制{quota}人",
            officer="试中律学生" if post in ("律学正", "律学录") else None,
        )
    for title in ("命官斋", "举人斋"):
        parent_child(
            w, touched, i, "律学", title, "北宋熙宁六年四月二日", roster,
            f"律学分设{title}。", "编制",
            parent_event="分设命官斋、举人斋", child_event="律学二斋之一",
        )
    finish(w, touched, "整理律学唐代职源、北宋馆学演变、熙宁正式设置、国子监隶属、职能官属与南宋不置链。")


def entry836():
    i = 836
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "律学", "律学教授", "北宋熙宁六年三月二十七日",
        roster, "熙宁六年诏置律学教授四员。", "编制",
        quota=4, staff_type="教授", office_event="诏置律学教授四员",
        post_event="教授刑名之学，使学而后从政",
    )
    evolution(
        w, touched, i, "律学教授", "律学博士", "北宋元丰五年", origin,
        "元丰五年律学教授改为律学博士。", "职源与沿革",
        source_event="改为律学博士", target_event="由律学教授改置",
    )
    cite(w, "Timepoints", post, i, main, "正文明确律学教授隶国子监。")
    cite(w, "Timepoints", post, i, duty, "补证律学教授刑名教学职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证律学教授位遇视国子监直讲。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理律学教授熙宁设置、四人编制、职掌品位及元丰改博士链。")


def entry837():
    i = 837
    main, origin, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    for time, event in (
        ("西晋武帝咸宁四年", "廷尉下律博士为职源"),
        ("唐", "国子监律学博士始置"),
        ("北宋初", "虽无正式律学，仍置律学博士"),
        ("北宋熙宁六年四月二日", "办律学时不置"),
        ("南宋", "沿置"),
    ):
        node(w, touched, i, "律学博士", "官职", time, event, origin,
             "律学学官", f"建立律学博士{time}沿革节点。", "职源与沿革",
             grade="从八品" if "宋" in time else None)
    evolution(
        w, touched, i, "律学教授", "律学博士", "北宋元丰五年", origin,
        "元丰官制改律学教授为律学博士。", "职源与沿革",
        source_event="改为律学博士", target_event="由律学教授改置",
    )
    for time, quota in (
        ("北宋元丰新制", 1), ("北宋元丰后（年月未载）", 2),
    ):
        _, post, _ = office_staff(
            w, touched, i, "律学", "律学博士", time, roster,
            f"{time}律学博士编制{quota}人。", "编制",
            quota=quota, staff_type="博士", office_event=f"设置博士{quota}人",
            post_event="传授法律并校试学生", grade="从八品",
        )
    cite(w, "Timepoints", post, i, main, "正文明确律学博士隶国子监。")
    cite(w, "Timepoints", post, i, duty, "补证律学博士传法与校试职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证律学博士从八品与班位。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理律学博士前代职源、北宋馆学与正式律学变化、元丰改置、南宋沿置及编制品位链。")


def entry838():
    i = 838
    origin, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "律学", "律学正", "北宋熙宁六年四月二十四日",
        roster, "熙宁六年始置律学正一人。", "编制",
        quota=1, staff_type="学生职事人", office_event="设置律学正一人",
        post_event="掌本学规矩，由试中律学生充",
        officer="试中律学生", grade="正九品",
    )
    node(w, touched, i, "律学正", "官职", "南宋", "沿置", origin,
         "律学学官", "建立律学正南宋沿置节点。", "职源与沿革",
         grade="正九品")
    cite(w, "Timepoints", post, i, origin, "补证律学正始置时间。", "职源与沿革")
    cite(w, "Timepoints", post, i, duty, "补证律学正职掌与班位。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证律学正正九品。", "品位")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理律学正熙宁始置、学生选充、职掌品位、一人编制及南宋沿置链。")


def entry839():
    i, main, aliases = 839, F[839]["text"], field(839, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "律学", "律学录", "北宋熙宁六年四月二十四日", main,
        "熙宁六年初置律学录一人。", quota=1,
        staff_type="学生职事人", office_event="设置律学录一人",
        post_event="由试中律学生充，佐学正掌学规",
        officer="试中律学生",
    )
    node(w, touched, i, "律学录", "官职", "北宋元丰新制",
         "新制不置", main, "律学学生职事人",
         "建立律学录元丰不置节点。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理律学录熙宁始置、学生选充、佐学正规矩及元丰不置链。")


def entry840():
    i = 840
    main, aliases = F[i]["text"], field(i, "别称")
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "律学", "律学生", "北宋熙宁六年四月二日", main,
        "熙宁律学招收命官和举人律学生。", staff_type="学生",
        office_event="招收命官与举人律学生",
        post_event="学习律令或断案，结业后参政为法官",
    )
    group_tp = group_members(
        w, touched, i, "律学生", "北宋熙宁六年四月二日",
        "依入学身份分命官律学生与举人律学生",
        ("命官律学生", "举人律学生"), main,
        "原文明言命官与举人皆可成为律学生。",
    )
    node(
        w, touched, i, "律学生", "官职", "北宋元祐三年九月二十二日",
        "开始允许自费就读", main, "律学生员",
        "建立元祐三年自费就读制度节点。",
    )
    for hall, student in (("命官斋", "命官律学生"), ("举人斋", "举人律学生")):
        office_staff(
            w, touched, i, hall, student, "北宋熙宁六年四月二日", main,
            f"{hall}收纳{student}。", staff_type="学生",
            office_event=f"收纳{student}", post_event=f"在{hall}就读",
        )
    alias_note(w, i, group_tp, aliases, "别称")
    finish(w, touched, "整理律学生命官举人两类、入学公费与自费变化、两专业二斋及结业为法官。")


def main():
    for i in range(821, 841):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
