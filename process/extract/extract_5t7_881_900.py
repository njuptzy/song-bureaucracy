#!/usr/bin/env python3
"""提取 chapter5t7 第881-900条：正录、少府监与文思院。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_861_880 as previous


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


F = {i: load(i) for i in range(881, 901)}
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
    "秦汉": -150, "西晋": 280, "隋大业三年": 607, "唐": 618,
    "宋初": 960, "宋前期": 970,
    "宋代（文思院，具体年月未载）": 978.1,
    "宋代（文思院两界，具体年月未载）": 978.2,
    "北宋太平兴国三年": 978,
    "北宋熙宁三年前": 1069.9, "北宋熙宁三年": 1070,
    "北宋熙宁四年十二月后": 1071.95,
    "北宋元丰新制前": 1079.9, "北宋元丰新制": 1080,
    "北宋元丰五年": 1082, "北宋崇宁间": 1104,
    "南宋建炎三年四月十三日": 1129.29,
    "南宋绍兴三年": 1133, "南宋绍兴六年正月": 1136.04,
    "南宋（具体年月未载）": 1140,
    "南宋隆兴二年六月": 1164.45, "南宋淳熙十三年": 1186,
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


def set_event(w, tid, event, decision):
    old = w.conn.execute("select event from Timepoints where id=?", (tid,)).fetchone()[0]
    if old == event:
        return
    w.conn.execute("update Timepoints set event=? where id=?", (event, tid))
    w._br("Timepoints", tid, f"事件说明由‘{old}’规范为‘{event}’：{decision}")


def node(w, touched, i, title, type_, time, event, quotation, category,
         decision, field_name=None, *, officer=None, grade=None,
         update_event=False):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )
    if update_event:
        set_event(w, tid, event, decision)
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


def evolution(w, touched, i, source_title, source_type, target_title,
              target_type, time, quotation, decision, field_name=None,
              *, source_event=None, target_event=None):
    source_tid = node(
        w, touched, i, source_title, source_type, time,
        source_event or f"转由{target_title}承接", quotation, "演变前",
        f"建立或复用{source_title}{time}演变节点。", field_name,
    )
    target_tid = node(
        w, touched, i, target_title, target_type, time,
        target_event or f"承接{source_title}职事", quotation, "演变后",
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
        "官职统称", f"建立或复用{group_title}{time}统称节点。", field_name,
        update_event=True,
    )
    for member_title, member_time in members:
        member_tid = node(
            w, touched, i, member_title, "官职", member_time,
            f"{group_title}所指实例", quotation, f"{group_title}实例",
            f"建立或复用{member_title}{member_time}实例节点。", field_name,
        )
        relation(
            w, i, group_tid, member_tid, "统称与实例", quotation,
            f"{member_title}是{group_title}的实例。{decision}", field_name,
        )
    return group_tid


def entry881():
    i, quote = 881, F[881]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "正录", "北宋崇宁间", "医学正、医学录连称",
        (
            ("医学正", "北宋崇宁二年九月十五日"),
            ("医学录", "北宋崇宁二年九月十五日"),
        ),
        quote, "本条明确正录是医学正、医学录的连称。",
    )
    finish(w, touched, "整理正录统称及医学正、医学录两个实例。")


def canonicalize_court_supply_director(w, quote):
    short = w.find_entity("少府监", "官职")
    formal = w.find_entity("少府监监", "官职")
    if short is not None:
        assert formal is None or formal == short, (short, formal)
        w.conn.execute(
            "update Entities set title='少府监监',quotation=? where id=?",
            (quote, short),
        )
        w._br(
            "Entities", short,
            "第884条明确全称为少府监监；将既有官职实体少府监规范为正式词头，"
            "与同名机构少府监继续按类型区分。",
        )
        formal = short
    assert formal is not None
    cite(
        w, "Entities", formal, 884, quote,
        "正式词头及简称段明确官职全称为少府监监。",
    )
    return formal


def entry884():
    i = 884
    main = F[i]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    eid = canonicalize_court_supply_director(w, main)
    touched.add(eid)
    node(
        w, touched, i, "少府监监", "官职", "隋大业三年",
        "始置少府监监", origin, "前代官制源流",
        "记录少府监监隋代始置。", "职源与沿革", update_event=True,
    )
    node(
        w, touched, i, "少府监监", "官职", "宋前期",
        "无职事，作为文臣迁转官阶", duty, "阶官",
        "记录元丰前少府监监为阶官。", "职掌", update_event=True,
    )
    old_tp = node(
        w, touched, i, "少府监监", "官职", "北宋元丰新制前",
        "旧阶官将按寄禄格易为中散大夫", duty, "阶官",
        "建立少府监监改制前阶官节点。", "职掌", update_event=True,
    )
    new_rank = node(
        w, touched, i, "中散大夫", "官职", "北宋元丰新制",
        "由旧少府监监阶转为中散大夫阶", duty, "寄禄官",
        "建立中散大夫承接旧少府监监阶节点。", "职掌",
    )
    relation(
        w, i, old_tp, new_rank, "前后演变", duty,
        "元丰寄禄格明确旧少府监监阶易为中散大夫阶。", "职掌",
    )
    _, post, _ = office_staff(
        w, touched, i, "少府监", "少府监监", "北宋元丰新制", duty,
        "元丰新制正名后少府监监为本监长官。", "职掌",
        quota=1, staff_type="长官", office_event="实行元丰新制",
        post_event="为少府监长官，总掌百工技巧政令", grade="从四品",
    )
    node(
        w, touched, i, "少府监监", "官职", "宋初",
        "沿唐制为从三品", rank, "阶官", "记录宋初沿唐品位。", "品位",
        grade="从三品", update_event=True,
    )
    cite(w, "Timepoints", post, i, rank, "补证元丰后少府监监从四品。", "品位")
    node(
        w, touched, i, "少府监监", "官职", "南宋建炎三年四月十三日",
        "随少府监罢置", origin, "罢置官职",
        "建立少府监监建炎三年罢置节点。", "职源与沿革",
        update_event=True,
    )
    cite(w, "Timepoints", post, i, roster, "补证元丰新制少府监监一人。", "编制")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理少府监监正式词头、隋宋沿革、元丰阶职分离、品位编制与建炎罢置。")


def entry882():
    i = 882
    main = F[i]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(
        w, touched, i, "少府监", "机构", "秦汉",
        "少府之名始于秦汉", origin, "前代官制源流",
        "记录少府名称的秦汉源流。", "职源与沿革", update_event=True,
    )
    node(
        w, touched, i, "少府监", "机构", "隋大业三年",
        "始置少府监", origin, "前代官制源流",
        "记录少府监隋代始置。", "职源与沿革", update_event=True,
    )
    early = node(
        w, touched, i, "少府监", "机构", "宋前期",
        "北宋沿设；职事分隶文思院、后苑造作所，本监掌祭器法物等制造",
        duty, "中央制造监司", "整理少府监宋前期职掌。", "职掌",
        update_event=True,
    )
    reform = node(
        w, touched, i, "少府监", "机构", "北宋元丰新制",
        "掌百工技巧政令及乘舆服御、礼乐器服、册宝符节、度量衡制造",
        duty, "中央制造监司", "整理少府监元丰新制职掌。", "职掌",
        update_event=True,
    )
    cite(w, "Timepoints", early, i, roster, "补证宋前期设判少府监事。", "编制")
    cite(w, "Timepoints", reform, i, roster, "补证元丰后四官一员、四案八吏及五个所属机构。", "编制")
    for child in ("文思院", "绫锦院", "染院", "裁造院", "文绣院"):
        parent_child(
            w, touched, i, "少府监", child, "北宋元丰新制", roster,
            f"元丰新制{child}为少府监所隶官属。", "编制",
            parent_event="统辖五个官属", child_event="列为少府监所隶官属",
        )
    for post in ("少府监监", "少府监少监", "少府监丞", "少府监主簿"):
        office_staff(
            w, touched, i, "少府监", post, "北宋元丰新制", roster,
            f"元丰改制少府监置{post}一人。", "编制", quota=1,
            staff_type="官", office_event="置监、少监、丞、主簿各一人",
            post_event="少府监官属，编制一人",
        )
    abolition = node(
        w, touched, i, "少府监", "机构", "南宋建炎三年四月十三日",
        "罢少府监，职事并归工部", origin, "废罢机构",
        "记录少府监建炎三年罢并归工部。", "职源与沿革",
        update_event=True,
    )
    evolution(
        w, touched, i, "少府监", "机构", "工部", "机构",
        "南宋建炎三年四月十三日", origin,
        "少府监罢后职事并归工部。", "职源与沿革",
        source_event="罢置并将职事归工部", target_event="承接少府监职事",
    )
    later = node(
        w, touched, i, "少府监", "机构", "南宋绍兴三年",
        "不复置，原职事总于复置的将作监", origin, "废罢机构",
        "记录绍兴三年少府监不复。", "职源与沿革", update_event=True,
    )
    evolution(
        w, touched, i, "少府监", "机构", "将作监", "机构",
        "南宋绍兴三年", origin,
        "绍兴三年少府监不复，其事总于将作监。", "职源与沿革",
        source_event="不复置，原职事转归将作监",
        target_event="复置并总领原少府监职事",
    )
    alias_note(w, i, later, aliases, "简称")
    cite(w, "Timepoints", abolition, i, main, "词头定义补证少府监官司属性。")
    finish(w, touched, "整理少府监隋宋沿革、前后期职掌、元丰官属与建炎绍兴职能归并。")


def entry883():
    i, quote = 883, F[883]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "少府监", "判少府监事", "宋前期", quote,
        "宋前期以朝官差判少府监公事。", quota=None, staff_type="判监官",
        office_event="设判少府监事官", post_event="以朝官差充，领少府监公事",
        officer="朝官差充",
    )
    old = node(
        w, touched, i, "判少府监事", "官职", "北宋元丰五年",
        "新制正名后罢判监", quote, "废罢差遣",
        "建立判少府监事元丰五年罢置节点。", update_event=True,
    )
    new = node(
        w, touched, i, "少府监监", "官职", "北宋元丰五年",
        "新制置监，取代判少府监事", quote, "职事官",
        "建立少府监监元丰五年正名节点。",
    )
    relation(
        w, i, old, new, "前后演变", quote,
        "元丰五年少府监置监并罢判监。",
    )
    finish(w, touched, "整理判少府监事宋前期差遣及元丰五年被少府监监取代。")


def subordinate_officer(i, title, origin_time, origin_event, early_event,
                        reform_event, reform_grade, abolition_event,
                        *, early_grade=None, extra_origins=()):
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称")
    roster = F[i]["fields"].get("编制")
    w, touched = W(i), set()
    node(
        w, touched, i, title, "官职", origin_time, origin_event, origin,
        "前代官制源流", f"记录{title}前代始置。", "职源与沿革",
        update_event=True,
    )
    for extra_time, extra_event in extra_origins:
        node(
            w, touched, i, title, "官职", extra_time, extra_event, origin,
            "前代官制源流", f"补充{title}{extra_time}源流节点。", "职源与沿革",
            update_event=True,
        )
    early = node(
        w, touched, i, title, "官职", "宋前期", early_event, duty,
        "阶官", f"整理{title}宋前期阶官性质。", "职掌",
        grade=early_grade, update_event=True,
    )
    _, reform, _ = office_staff(
        w, touched, i, "少府监", title, "北宋元丰新制", duty,
        f"元丰新制{title}为少府监职事官。", "职掌",
        quota=1 if roster else None, staff_type="官",
        office_event=f"设置{title}", post_event=reform_event,
        grade=reform_grade,
    )
    cite(w, "Timepoints", reform, i, rank, f"补证{title}元丰后品位。", "品位")
    if early_grade:
        cite(w, "Timepoints", early, i, rank, f"补证{title}宋初沿袭品位。", "品位")
    if roster:
        cite(w, "Timepoints", reform, i, roster, f"补证{title}一人编制。", "编制")
    abolished = node(
        w, touched, i, title, "官职", "南宋建炎三年四月十三日",
        abolition_event, origin, "罢置官职",
        f"建立{title}建炎三年罢置节点。", "职源与沿革",
        update_event=True,
    )
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, f"整理{title}前代源流、宋前期阶官、元丰职事官、品位编制与建炎罢置。")


def entry885():
    subordinate_officer(
        885, "少府监少监", "隋大业三年", "始置少府监少监",
        "无职事，为阶官", "佐监领百工技巧政令", "从六品",
        "随少府监罢置",
    )


def entry886():
    subordinate_officer(
        886, "少府监丞", "秦汉", "秦汉已置少府丞",
        "无职事，或作文臣迁转官阶", "参领少府监事", "从八品",
        "随少府监罢置",
        extra_origins=(("隋大业三年", "始置少府监丞"),),
    )


def entry887():
    subordinate_officer(
        887, "少府监主簿", "西晋", "西晋少府卿下始设主簿",
        "无职事，或作文臣迁转官阶", "专勾考本监簿书，他事不得预",
        "从八品", "随少府监罢置", early_grade="从七品下",
        extra_origins=(("隋大业三年", "始置少府监主簿"),),
    )


BOUNDARY_TIME = "宋代（文思院两界，具体年月未载）"


def entry888():
    i = 888
    main = F[i]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(
        w, touched, i, "文思院", "机构", "唐", "文思院名称始于唐",
        origin, "前代机构源流", "记录文思院唐代名称源流。", "职源与沿革",
        update_event=True,
    )
    start = node(
        w, touched, i, "文思院", "机构", "北宋太平兴国三年",
        "始置文思院，北宋隶少府监", origin, "中央制造机构",
        "记录太平兴国三年始置及北宋隶属。", "职源与沿革",
        update_event=True,
    )
    node(
        w, touched, i, "文思院", "机构", "北宋熙宁四年十二月后",
        "除原有制造外并掌斗秤制造", duty, "中央制造机构",
        "记录熙宁四年十二月后增掌斗秤制造。", "职掌", update_event=True,
    )
    south = node(
        w, touched, i, "文思院", "机构", "南宋绍兴三年",
        "少府监并入文思院，文思院归隶工部", origin, "中央制造机构",
        "整理绍兴三年文思院沿革与隶属。", "职源与沿革",
        update_event=True,
    )
    evolution(
        w, touched, i, "礼物局", "机构", "文思院", "机构",
        "南宋隆兴二年六月", origin,
        "隆兴二年六月礼物局并入文思院。", "职源与沿革",
        source_event="并入文思院", target_event="接收礼物局职事",
    )
    cite(w, "Timepoints", start, i, duty, "补证文思院制造帝后所需及舆辇法物器服职掌。", "职掌")
    for boundary in ("文思院上界", "文思院下界"):
        parent_child(
            w, touched, i, "文思院", boundary, BOUNDARY_TIME, roster,
            f"文思院分为{boundary}。", "编制",
            parent_event="分上、下两界，共领四十二作",
            child_event="文思院两界之一",
        )
    office_staff(
        w, touched, i, "文思院", "提辖文思院上下界", "南宋（具体年月未载）",
        roster, "南宋文思院置提辖官一人。", "编制", quota=1,
        staff_type="提辖官", office_event="置提辖、监官与监门官",
        post_event="通管文思院上、下界",
    )
    office_staff(
        w, touched, i, "文思院", "文思院两界监官", "南宋（具体年月未载）",
        roster, "南宋文思院监官共四人。", "编制", quota=4,
        staff_type="监官", office_event="置提辖、监官与监门官",
        post_event="监文思院两界制造",
    )
    office_staff(
        w, touched, i, "文思院", "监门官", "南宋（具体年月未载）",
        roster, "南宋文思院监门官共二人。", "编制", quota=2,
        staff_type="监门官", office_event="置提辖、监官与监门官",
        post_event="分掌文思院中门、大门",
    )
    for boundary in ("文思院上界", "文思院下界"):
        for post in ("手分", "库经司", "花料司", "门司", "专知官", "副知", "秤子", "库子"):
            office_staff(
                w, touched, i, boundary, post, BOUNDARY_TIME, roster,
                f"文思院上、下界均置{post}。", "编制", staff_type="吏",
                office_event="设置两界吏额", post_event="文思院两界吏额",
            )
    alias_note(w, i, south, aliases, "简称")
    finish(w, touched, "整理文思院唐宋沿革、职掌、两界、南宋官额及两界吏额。")


def interface_supervisor(i, boundary, title, craft):
    quote = F[i]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, boundary, title, BOUNDARY_TIME, quote,
        f"两宋{title}掌监造{craft}，编制二人或三人。",
        quota=None, staff_type="差遣官", office_event=f"掌造{craft}",
        post_event=f"掌监造{craft}，编制二人或三人",
        officer="文臣京朝官、武臣诸使副或三班使臣差充",
    )
    office_staff(
        w, touched, i, boundary, title, "北宋熙宁三年前", quote,
        f"熙宁三年前{title}由内侍一员充任。", quota=1,
        staff_type="内侍监官", office_event=f"掌造{craft}",
        post_event="熙宁三年前由内侍一员充监官", officer="内侍",
    )
    finish(w, touched, f"整理{title}两宋设置、监造职掌、二至三人编制及熙宁前内侍员额。")


def entry889():
    interface_supervisor(889, "文思院上界", "监文思院上界", "金银、珠玉")


def entry890():
    interface_supervisor(890, "文思院下界", "监文思院下界", "铜、铁、竹、木杂料生活")


def entry891():
    i, quote = 891, F[891]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    group_members(
        w, touched, i, "文思院两界监官", BOUNDARY_TIME,
        "监文思院上界、监文思院下界合称",
        (("监文思院上界", BOUNDARY_TIME), ("监文思院下界", BOUNDARY_TIME)),
        quote, "本条明定文思院两界监官的两个实例。",
    )
    reform = group_members(
        w, touched, i, "文思院两界监官", "北宋熙宁三年",
        "定文臣一员、武臣一员，罢内侍监官",
        (
            ("监文思院上界", "北宋熙宁三年"),
            ("监文思院下界", "北宋熙宁三年"),
        ),
        quote, "熙宁三年两界监官定文武各一员并罢内侍。",
    )
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "整理文思院两界监官统称、上下界实例及熙宁三年文武员额改革。")


def entry892():
    i = 892
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "文思院", "提辖文思院上下界", "南宋绍兴六年正月",
        origin, "绍兴六年正月始置提辖文思院官。", "职源", quota=1,
        staff_type="提辖官", office_event="始置提辖文思院官",
        post_event="通管文思院上、下界财货出纳", officer="南宋四辖官",
    )
    cite(w, "Timepoints", post, i, duty, "补证提辖官通管上下界财货出纳。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证提辖文思院为四辖官及其迁转待遇。", "品位")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理提辖文思院上下界绍兴始置、一人编制、职掌、四辖官性质与别称。")


def entry893():
    i, quote = 893, F[893]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "文思院", "拘押官", "南宋（具体年月未载）", quote,
        "南宋文思院置拘押官，掌管押两界官物生活。",
        staff_type="拘押官", office_event="设置拘押官",
        post_event="管押文思院两界官物生活",
        officer="枢密院使臣或转运司现任指使差充",
    )
    finish(w, touched, "整理南宋文思院拘押官差充来源、两界官物管押职掌与待遇依据。")


def entry894():
    i, quote = 894, F[894]["text"]
    w, touched = W(i), set()
    for boundary in ("文思院上界", "文思院下界"):
        office_staff(
            w, touched, i, boundary, "监门官", BOUNDARY_TIME, quote,
            f"{boundary}置监门官一人，分掌文思院中门、大门。", quota=1,
            staff_type="监门官", office_event="设置监门官",
            post_event="由三班使臣差充，分掌中门、大门，晚间轮值",
            officer="三班使臣差充",
        )
    for boundary, event in (
        ("文思院上界", "充外门监官"),
        ("文思院下界", "充中门监官"),
    ):
        office_staff(
            w, touched, i, boundary, "监门官", "南宋淳熙十三年", quote,
            f"淳熙十三年两界两门合并后，{boundary}监门官{event}。",
            quota=1, staff_type="监门官", office_event="两界两门并为一门出入",
            post_event=f"两门合并后{event}", officer="三班使臣差充",
        )
    finish(w, touched, "整理文思院两界监门官设置、门务轮值及淳熙十三年外门中门分工。")


def repair_case(i, title, boundary, duty):
    quote = F[i]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, boundary, title, "宋代（文思院，具体年月未载）",
        quote, f"{title}为{boundary}所属案。",
        parent_event="分设修造案", child_event=duty,
    )
    finish(w, touched, f"整理{title}所属文思院界别与承行职掌。")


def entry895():
    repair_case(895, "文思院上界修造案", "文思院上界", "承行金银珠玉等应奉生活文字")


def entry896():
    repair_case(896, "文思院下界修造案", "文思院下界", "承行织造、漆木、铜铁等生活文字")


def dual_boundary_clerk(i, title, duty):
    quote = F[i]["text"]
    w, touched = W(i), set()
    for boundary in ("文思院上界", "文思院下界"):
        office_staff(
            w, touched, i, boundary, title, BOUNDARY_TIME, quote,
            f"文思院上、下界均置{title}。", staff_type="公吏",
            office_event=f"设置{title}", post_event=duty, officer="公吏",
        )
    finish(w, touched, f"整理{title}在文思院上、下界的设置与职掌。")


def entry897():
    dual_boundary_clerk(897, "库经司", "承办造作生活帐状及抄转收支赤历")


def entry898():
    dual_boundary_clerk(898, "花料司", "承行造作生活计料")


def entry899():
    dual_boundary_clerk(899, "门司", "登记本界门官物收支出入并抄转赤历")


def entry900():
    dual_boundary_clerk(900, "秤子", "掌管秤盘并收支官物")


def main():
    order = [881, 884, 882, 883, *range(885, 901)]
    for i in order:
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
