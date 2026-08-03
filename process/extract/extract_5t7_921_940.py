#!/usr/bin/env python3
"""提取 chapter5t7 第921-940条：军器监、作坊及所属局库。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_901_920 as previous


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


F = {i: load(i) for i in range(921, 941)}
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
    "北周武帝四年": 564,
    "北周": 570,
    "唐武德初": 620,
    "唐开元三年": 715,
    "宋建隆初": 960,
    "北宋初": 960.1,
    "北宋真宗、仁宗朝（具体年月未载）": 1020,
    "北宋开宝九年九月": 976.70,
    "北宋景德元年": 1004,
    "北宋景德三年": 1006,
    "北宋前期（南、北作坊先后隶属，具体年月未载）": 1030,
    "北宋前期（作坊物料库先后隶属，具体年月未载）": 1030.1,
    "北宋熙宁三年十二月十二日": 1070.95,
    "北宋熙宁五年五月一日": 1072.34,
    "北宋熙宁六年六月二十七日": 1073.49,
    "北宋熙宁十年四月十七日": 1077.29,
    "北宋元丰新制": 1080,
    "北宋元丰五年": 1082,
    "北宋元祐时": 1088,
    "宋代（军器监，具体年月未载）": 1100,
    "宋代（作坊，具体年月未载）": 1100.1,
    "宋代（东、西作坊五十一作，具体年月未载）": 1100.2,
    "宋代（作坊物料库，具体年月未载）": 1100.3,
    "宋代（皮角场库，具体年月未载）": 1100.4,
    "宋代（斩马刀局，具体年月未载）": 1100.5,
    "南宋建炎三年四月十三日": 1129.29,
    "南宋绍兴三年四月九日": 1133.27,
    "南宋绍兴三年十月二十九日": 1133.83,
    "南宋绍兴十一年四月二十二日": 1141.30,
    "南宋隆兴元年七月二十六日": 1163.56,
    "南宋乾道五年四月": 1169.29,
    "南宋乾道六年十一月": 1170.88,
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


def evolution(w, touched, i, source_title, target_title, time, quotation,
              decision, field_name=None, *, source_type="机构",
              target_type="机构", source_event=None, target_event=None):
    source_tid = node(
        w, touched, i, source_title, source_type, time,
        source_event or f"转为{target_title}", quotation, "演变前",
        f"建立或复用{source_title}{time}演变节点。", field_name,
    )
    target_tid = node(
        w, touched, i, target_title, target_type, time,
        target_event or f"由{source_title}转入", quotation, "演变后",
        f"建立或复用{target_title}{time}演变节点。", field_name,
    )
    relation(
        w, i, source_tid, target_tid, "前后演变", quotation,
        decision, field_name,
    )
    return source_tid, target_tid


def group_instances(w, touched, i, group_title, type_, time, event, members,
                    quotation, decision, field_name=None):
    group_tid = node(
        w, touched, i, group_title, type_, time, event, quotation,
        f"{type_}统称", f"建立或复用{group_title}{time}统称节点。", field_name,
        update_event=True,
    )
    for member_title in members:
        member_tid = node(
            w, touched, i, member_title, type_, time,
            f"{group_title}所指实例", quotation, f"{group_title}实例",
            f"建立或复用{member_title}{time}实例节点。", field_name,
        )
        relation(
            w, i, group_tid, member_tid, "统称与实例", quotation,
            f"{member_title}是{group_title}的实例。{decision}", field_name,
        )
    return group_tid


def entry921():
    i, quote = 921, F[921]["text"]
    w, touched = W(i), set()
    node(
        w, touched, i, "旌节官告使", "官职",
        "北宋真宗、仁宗朝（具体年月未载）",
        "临时奉使蕃国，送交官告与节度使旌节，事毕即罢",
        quote, "临时差遣", "记录旌节官告使的设置时期、使命和事毕即罢性质。",
        officer="临时奉使官", update_event=True,
    )
    finish(w, touched, "整理旌节官告使在真宗仁宗朝的临时差遣性质与奉送使命。")


def entry922():
    i, main = 922, F[922]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(
        w, touched, i, "军器监", "机构", "北周武帝四年",
        "前代始置军器监", origin, "前代机构源流",
        "记录军器监北周始置源流。", "职源与沿革", update_event=True,
    )
    node(
        w, touched, i, "军器监", "机构", "北宋初",
        "具官无员，军器制造分归作坊、弓弩院及诸州作院",
        origin, "具名空官司", "记录北宋初具官无员状态。", "职源与沿革",
        update_event=True,
    )
    evolution(
        w, touched, i, "胄案", "军器监", "北宋熙宁六年六月二十七日",
        duty, "熙宁六年以三司胄案实置军器监，总内外军器之政。", "职掌",
        source_event="改置为军器监",
        target_event="由三司胄案实置，总内外军器之政",
    )
    reform = node(
        w, touched, i, "军器监", "机构", "北宋元丰新制",
        "元丰正名，职掌不变，判监、同判监改为监、少监等",
        duty, "中央军器监司", "整理军器监元丰正名。", "职掌",
        update_event=True,
    )
    parent_child(
        w, touched, i, "工部", "军器监", "宋代（军器监，具体年月未载）",
        main, "军器监隶工部。", parent_event="统辖军器监",
        child_event="隶工部，北宋在兴国坊，南宋在保民坊",
    )
    for child in ("东、西作坊", "作坊物料库", "皮角场库", "广备指挥"):
        parent_child(
            w, touched, i, "军器监", child, "北宋元丰新制", roster,
            f"元丰新制军器监总领{child}。", "编制",
            parent_event="元丰新制总领五局",
            child_event="列为军器监所总领机构",
        )
    for post, quota, kind in (
        ("军器监监", 1, "长官"), ("军器监少监", 1, "贰官"),
        ("军器监丞", 2, "属官"), ("军器监主簿", 1, "属官"),
    ):
        office_staff(
            w, touched, i, "军器监", post, "北宋元丰新制", roster,
            f"元丰新制军器监置{post}{quota}人。", "编制", quota=quota,
            staff_type=kind, office_event="元丰新制置监、少监、丞、主簿",
            post_event=f"军器监{kind}，编制{quota}人",
        )
    abolished = node(
        w, touched, i, "军器监", "机构", "南宋建炎三年四月十三日",
        "罢军器监，职事并归工部", origin, "废罢机构",
        "记录建炎三年罢军器监。", "职源与沿革", update_event=True,
    )
    evolution(
        w, touched, i, "军器监", "工部", "南宋建炎三年四月十三日",
        roster, "建炎三年军器监并归工部。", "编制",
        source_event="罢置并归工部", target_event="承接军器监职事",
    )
    restored = node(
        w, touched, i, "军器监", "机构", "南宋绍兴三年十月二十九日",
        "复置军器监并置监丞一员", origin, "复置机构",
        "记录绍兴三年复置。", "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", restored, i, roster, "补证复置时先置监丞一员。", "编制")
    office_staff(
        w, touched, i, "军器监", "军器监丞", "南宋绍兴三年十月二十九日",
        roster, "绍兴三年复置军器监丞一员。", "编制", quota=1,
        staff_type="属官", office_event="复置并先置监丞一员",
        post_event="随军器监复置，编制一员",
    )
    for post, kind in (("军器监监", "长官"), ("军器监少监", "贰官")):
        office_staff(
            w, touched, i, "军器监", post, "南宋绍兴十一年四月二十二日",
            roster, f"绍兴十一年复置{post}一人。", "编制", quota=1,
            staff_type=kind, office_event="复置监、少监各一员",
            post_event=f"复置为军器监{kind}，编制一员",
        )
    for post in ("军器监监", "军器监少监"):
        node(
            w, touched, i, post, "官职", "南宋隆兴元年七月二十六日",
            "省罢", roster, "废罢官职",
            f"记录隆兴元年省{post}。", "编制", update_event=True,
        )
    office_staff(
        w, touched, i, "军器监", "军器监少监", "南宋乾道五年四月",
        roster, "乾道五年复置军器监少监。", "编制", quota=1,
        staff_type="贰官", office_event="复置少监",
        post_event="复置为军器监贰官",
    )
    office_staff(
        w, touched, i, "军器监", "军器监监", "南宋乾道六年十一月",
        roster, "乾道六年复置军器监监。", "编制", quota=1,
        staff_type="长官", office_event="复置监",
        post_event="复置为军器监长官",
    )
    cite(w, "Timepoints", reform, i, main, "补证军器监官司性质、隶属及京城地点。")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理军器监前代源流、北宋实置与元丰正名、五局官属及南宋罢复链。")


def entry923():
    i, main = 923, F[923]["text"]
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "军器监", "判军器监事", "北宋熙宁六年六月二十七日",
        main, "熙宁六年始设判军器监事一员。", quota=1,
        staff_type="判监官", office_event="始实置并设判监官",
        post_event="始设，掌内外军器之政", officer="两制、侍从官充",
    )
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理判军器监事熙宁始置、一员编制、差充、职掌与简称。")


def entry924():
    i, main = 924, F[924]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "军器监", "同判军器监事", "北宋熙宁六年六月二十七日",
        main, "熙宁六年始设同判军器监事一员。", quota=1,
        staff_type="同判监官", office_event="始实置并设同判监官",
        post_event="资序稍浅的判监官带同字", officer="两制以上侍从官充",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理同判军器监事熙宁始置、一员编制、差充与简称。")


def canonicalize_armament_director(w, quotation):
    short = w.find_entity("军器监", "官职")
    formal = w.find_entity("军器监监", "官职")
    if short is not None:
        assert formal is None or formal == short, (short, formal)
        w.conn.execute(
            "update Entities set title='军器监监',quotation=? where id=?",
            (quotation, short),
        )
        w._br(
            "Entities", short,
            "第925条正式词头为军器监监；将既有官职实体军器监规范为正式词头，"
            "与同名机构军器监继续按类型区分。",
        )
        formal = short
    assert formal is not None
    return formal


def entry925():
    i, main = 925, F[925]["text"]
    origin = field(i, "职源与沿革")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    eid = canonicalize_armament_director(w, main)
    touched.add(eid)
    node(
        w, touched, i, "军器监监", "官职", "北周",
        "北周有军器大监", origin, "前代官制源流",
        "记录军器监监北周源流。", "职源与沿革", update_event=True,
    )
    node(
        w, touched, i, "军器监监", "官职", "唐开元三年",
        "以军器使改为军器监监", origin, "前代官制源流",
        "记录唐代军器监监源流。", "职源与沿革", update_event=True,
    )
    node(
        w, touched, i, "军器监监", "官职", "北宋初",
        "具官无员", origin, "空衔官职", "记录北宋前期无员。", "职源与沿革",
        update_event=True,
    )
    _, reform, _ = office_staff(
        w, touched, i, "军器监", "军器监监", "北宋元丰五年",
        origin, "元丰五年始置军器监监。", "职源与沿革", quota=1,
        staff_type="长官", office_event="元丰正名后置监长",
        post_event="始置为军器监长官", grade="正六品",
    )
    cite(w, "Timepoints", reform, i, rank, "补证军器监监正六品及班位。", "品位")
    for time, event in (
        ("南宋建炎三年四月十三日", "随军器监罢置"),
        ("南宋绍兴十一年四月二十二日", "复置军器监监"),
        ("南宋隆兴元年七月二十六日", "省罢"),
        ("南宋乾道六年十一月", "复置军器监监"),
    ):
        node(
            w, touched, i, "军器监监", "官职", time, event, origin,
            "军器监长官", f"记录军器监监{time}废复。", "职源与沿革",
            grade="正六品", update_event=True,
        )
    cite(w, "Timepoints", reform, i, roster, "补证南宋军器监监废置不常。", "编制")
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "规范军器监监正式词头并整理前代源流、元丰始置、品位及南宋废复。")


def entry926():
    i, main = 926, F[926]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "军器监少监", "官职", "北周", "有军器副监",
         origin, "前代官制源流", "记录北周源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "军器监少监", "官职", "唐武德初", "有武器少监",
         origin, "前代官制源流", "记录唐代源流。", "职源与沿革", update_event=True)
    _, reform, _ = office_staff(
        w, touched, i, "军器监", "军器监少监", "北宋元丰新制",
        origin, "元丰新制始设军器监少监一人。", "职源与沿革", quota=1,
        staff_type="贰官", office_event="始设军器监少监",
        post_event="佐正监领本监公事", grade="从六品",
    )
    cite(w, "Timepoints", reform, i, duty, "补证少监佐正监领事。", "职掌")
    cite(w, "Timepoints", reform, i, rank, "补证少监从六品及班位。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补证少监一人及南宋废置不常。", "编制")
    for time, event in (
        ("南宋建炎三年四月十三日", "随军器监罢置"),
        ("南宋绍兴十一年四月二十二日", "复置军器监少监"),
        ("南宋隆兴元年七月二十六日", "省罢"),
        ("南宋乾道五年四月", "复置军器监少监"),
    ):
        node(w, touched, i, "军器监少监", "官职", time, event, origin,
             "军器监贰官", f"记录少监{time}废复。", "职源与沿革",
             grade="从六品", update_event=True)
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理军器监少监前代源流、元丰始设、职掌品位及南宋废复。")


def entry927():
    i, main = 927, F[927]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "军器监丞", "官职", "唐武德初", "始置武器监丞",
         origin, "前代官制源流", "记录唐代始置。", "职源与沿革", update_event=True)
    node(w, touched, i, "军器监丞", "官职", "唐开元三年", "改称军器监丞",
         origin, "前代官制源流", "记录唐开元改称。", "职源与沿革", update_event=True)
    _, north, _ = office_staff(
        w, touched, i, "军器监", "军器监丞", "北宋熙宁六年六月二十七日",
        origin, "熙宁六年实置军器监时置丞。", "职源与沿革",
        staff_type="属官", office_event="实置并设丞",
        post_event="参领军器监公事", grade="从八品",
    )
    cite(w, "Timepoints", north, i, duty, "补证军器监丞参领监事。", "职掌")
    cite(w, "Timepoints", north, i, rank, "补证军器监丞从八品及班位。", "品位")
    node(w, touched, i, "军器监丞", "官职", "南宋建炎三年四月十三日",
         "随军器监罢置", origin, "废罢官职", "记录建炎罢置。", "职源与沿革", update_event=True)
    office_staff(
        w, touched, i, "军器监", "军器监丞", "南宋绍兴三年十月二十九日",
        origin, "绍兴三年复置军器监丞。", "职源与沿革", quota=1,
        staff_type="属官", office_event="复置军器监丞",
        post_event="复置并参领本监公事", grade="从八品",
    )
    alias_note(w, i, north, aliases, "简称与别名")
    finish(w, touched, "整理军器监丞唐宋沿革、参领职掌、品位与南宋罢复。")


def entry928():
    i, main = 928, F[928]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "军器监主簿", "官职", "唐", "唐代始置",
         origin, "前代官制源流", "记录唐代始置。", "职源与沿革", update_event=True)
    _, north, _ = office_staff(
        w, touched, i, "军器监", "军器监主簿", "北宋熙宁六年六月二十七日",
        origin, "熙宁六年实置军器监时置主簿。", "职源与沿革", quota=1,
        staff_type="属官", office_event="实置并设主簿",
        post_event="掌勾考簿书", grade="从八品",
    )
    cite(w, "Timepoints", north, i, duty, "补证主簿掌勾考簿书。", "职掌")
    cite(w, "Timepoints", north, i, rank, "补证主簿从八品及班位。", "品位")
    cite(w, "Timepoints", north, i, roster, "补证主簿一人编制。", "编制")
    node(w, touched, i, "军器监主簿", "官职", "南宋建炎三年四月十三日",
         "随军器监罢置", origin, "废罢官职", "记录建炎罢置。", "职源与沿革", update_event=True)
    office_staff(
        w, touched, i, "军器监", "军器监主簿", "南宋绍兴三年十月二十九日",
        origin, "绍兴三年复置军器监主簿。", "职源与沿革", quota=1,
        staff_type="属官", office_event="复置军器监主簿",
        post_event="复置并掌勾考簿书", grade="从八品",
    )
    alias_note(w, i, north, aliases, "简称")
    finish(w, touched, "整理军器监主簿唐宋沿革、勾考职掌、品位编制与南宋罢复。")


def entry929():
    i, main = 929, F[929]["text"]
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "军器监", "勾当军器监公事",
        "北宋熙宁十年四月十七日", main,
        "熙宁十年始置勾当军器监公事一员。", quota=1,
        staff_type="属官", office_event="始置主簿及勾当公事官",
        post_event="始设，承办本监公事",
    )
    node(w, touched, i, "勾当军器监公事", "官职", "北宋元丰五年",
         "元丰新制正名后罢置", main, "废罢差遣",
         "记录元丰五年罢勾当军器监公事。", update_event=True)
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理勾当军器监公事熙宁始置、属员职掌、元丰罢置与别名。")


def entry930():
    i, quote = 930, F[930]["text"]
    w, touched = W(i), set()
    start = node(w, touched, i, "作坊", "机构", "宋建隆初",
                 "始置京师作坊，诸州置作院，制造兵器并旬进御览",
                 quote, "兵器制造机构", "记录作坊始置与职掌。", update_event=True)
    for post, kind in (("作坊使", "使"), ("作坊副使", "副使")):
        office_staff(w, touched, i, "作坊", post, "宋建隆初", quote,
                     f"作坊置{post}领坊事。", staff_type=kind,
                     office_event="始置并设使、副使", post_event="领作坊公事")
    for target in ("南作坊", "北作坊"):
        evolution(w, touched, i, "作坊", target, "北宋开宝九年九月", quote,
                  f"开宝九年作坊分为{target}。",
                  source_event="分为南作坊、北作坊并另置弓弩院",
                  target_event="由作坊分置")
    cite(w, "Timepoints", start, i, quote, "补证作坊兵器旬进、御览及五库存储。")
    finish(w, touched, "整理作坊建隆始置、兵器制造、使副编制与开宝南北分坊。")


def entry931():
    i, quote = 931, F[931]["text"]
    w, touched = W(i), set()
    office_staff(w, touched, i, "作坊", "作坊使", "宋代（作坊，具体年月未载）",
                 quote, "作坊使由诸司使充，领作坊事。", staff_type="使",
                 office_event="设置作坊使", post_event="由诸司使充，领作坊公事",
                 officer="诸司使充")
    finish(w, touched, "整理作坊使差充来源与领坊职掌。")


def entry932():
    i, quote = 932, F[932]["text"]
    w, touched = W(i), set()
    office_staff(w, touched, i, "作坊", "作坊副使", "宋建隆初",
                 quote, "建隆初作坊副使由诸司副使充，掌作坊事。",
                 staff_type="副使", office_event="设置作坊副使",
                 post_event="由诸司副使充，掌作坊公事", officer="诸司副使充")
    finish(w, touched, "整理作坊副使建隆实例、差充来源与职掌。")


def entry933():
    i, main = 933, F[933]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "南、北作坊", "机构", "北宋开宝九年九月",
        "由作坊分为南作坊、北作坊", ("南作坊", "北作坊"), origin,
        "南、北作坊是南作坊与北作坊的合称。", "职源与沿革")
    time = "北宋前期（南、北作坊先后隶属，具体年月未载）"
    for parent in ("三司", "提举在京诸司库务司"):
        parent_child(w, touched, i, parent, "南、北作坊", time, main,
                     f"南、北作坊先后隶{parent}。",
                     parent_event="先后统辖南、北作坊",
                     child_event="先后隶三司、提举在京诸司库务司")
    node(w, touched, i, "南、北作坊", "机构", "北宋开宝九年九月",
         "掌制造兵器及军用什物，总领五十一作", duty,
         "兵器制造机构统称", "整理南、北作坊职掌。", "职掌")
    cite(w, "Timepoints", group, i, roster, "补证两坊兵校工匠规模及五十一作。", "编制")
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理南北作坊统称、开宝分置、先后隶属、职掌编制与简称。")


def entry934():
    i, main = 934, F[934]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    evolution(w, touched, i, "南、北作坊", "东、西作坊",
              "北宋熙宁三年十二月十二日", origin,
              "熙宁三年南、北作坊改称东、西作坊。", "职源与沿革",
              source_event="改称东、西作坊", target_event="由南、北作坊改称")
    group = group_instances(
        w, touched, i, "东、西作坊", "机构", "北宋熙宁三年十二月十二日",
        "由南、北作坊改称，包括东作坊、西作坊", ("东作坊", "西作坊"),
        origin, "东、西作坊是东作坊与西作坊的合称。", "职源与沿革")
    parent_child(w, touched, i, "军器监", "东、西作坊", "北宋元丰新制",
                 main, "东、西作坊隶军器监。",
                 parent_event="总领东、西作坊", child_event="隶军器监")
    duty_tp = node(w, touched, i, "东、西作坊", "机构", "北宋元丰新制",
                   "制造兵器旗帜戎帐等物，输武库储藏，供邦国之用",
                   duty, "兵器制造机构统称", "整理东、西作坊职掌。", "职掌",
                   update_event=True)
    for post, quota, kind in (
        ("东、西作坊监官", 2, "监官"),
        ("东、西作坊监门官", 2, "监门官"),
    ):
        office_staff(w, touched, i, "东、西作坊", post, "北宋元丰新制",
                     roster, f"东、西作坊置{post}{quota}人。", "编制",
                     quota=quota, staff_type=kind,
                     office_event="设监官、监门官并总领五十一作",
                     post_event=f"编制{quota}人",
                     officer="京朝官、诸司使副、内侍差充" if kind == "监官" else "内侍充")
    parent_child(w, touched, i, "东、西作坊", "东、西作坊五十一作",
                 "北宋元丰新制", roster, "东、西作坊总领五十一作。", "编制",
                 parent_event="总领五十一作", child_event="东、西作坊所属五十一作统称")
    evolution(w, touched, i, "东、西作坊", "军器所",
              "南宋绍兴三年四月九日", origin,
              "绍兴三年东、西作坊并入军器所。", "职源与沿革",
              source_event="并入军器所", target_event="接收东、西作坊")
    cite(w, "Timepoints", group, i, main, "补证东、西作坊职局性质及军器监隶属。")
    cite(w, "Timepoints", duty_tp, i, roster, "补证监官、监门官及所属指挥编制。", "编制")
    alias_note(w, i, duty_tp, aliases, "简称")
    finish(w, touched, "整理东西作坊统称、熙宁改称、军器监隶属、职掌编制及绍兴并所。")


WORKSHOP_51 = (
    "木作", "鼓作", "藤席作", "锁子作", "竹作", "漆作", "马甲作", "大弩作",
    "条作", "棕作", "胡鞍作", "油衣作", "马甲生叶作", "打绳作", "漆衣甲作",
    "剑作", "糊粘作", "戎具作", "掐素作", "雕木作", "蜡烛作", "地衣作",
    "铁甲作", "钉钗作", "铁身作", "马甲造熟作", "磨剑作", "皮甲作",
    "钉头竿作", "铜作", "弩桩作", "钉弩桩红破皮作", "针作", "漆器作",
    "画作", "镴摆作", "纲甲作", "亲甲作", "大炉作", "小炉作", "器械作",
    "错磨作", "漩作", "鳞子作", "银作", "打线作", "打磨线作", "枪作",
    "角作", "锅炮作", "磨头牟作",
)


def entry935():
    i, quote = 935, F[935]["text"]
    assert len(WORKSHOP_51) == 51
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "东、西作坊五十一作", "机构",
        "宋代（东、西作坊五十一作，具体年月未载）",
        "东、西作坊制造军器及军用什物所分五十一作",
        WORKSHOP_51, quote, "本条逐一列明五十一作的正式实例。")
    finish(w, touched, "整理东、西作坊五十一作统称及原文列明的五十一个实例。")


def entry936():
    i, main = 936, F[936]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "作坊物料库", "机构", "北宋初", "初分三库",
         origin, "军器物料库", "记录宋初三库形态。", "职源与沿革", update_event=True)
    node(w, touched, i, "作坊物料库", "机构", "北宋景德元年", "三库合为一库",
         origin, "军器物料库", "记录景德合库。", "职源与沿革", update_event=True)
    time = "北宋前期（作坊物料库先后隶属，具体年月未载）"
    for parent in ("三司", "提举在京诸司库务司"):
        parent_child(w, touched, i, parent, "作坊物料库", time, main,
                     f"作坊物料库先后隶{parent}。",
                     parent_event="先后统辖作坊物料库",
                     child_event="先后隶三司、提举在京诸司库务司")
    parent_child(w, touched, i, "军器监", "作坊物料库", "北宋元丰新制",
                 main, "元丰正名后作坊物料库隶军器监。",
                 parent_event="统辖作坊物料库", child_event="元丰正名后隶军器监")
    duty_tp = node(w, touched, i, "作坊物料库", "机构",
                   "宋代（作坊物料库，具体年月未载）",
                   "收纳采购铁木铅锡等物料，供作坊及弓弩院制造军器",
                   duty, "军器物料库", "整理物料库职掌。", "职掌", update_event=True)
    office_staff(w, touched, i, "作坊物料库", "作坊物料库监官",
                 "宋代（作坊物料库，具体年月未载）", roster,
                 "作坊物料库置监官三人。", "编制", quota=3, staff_type="监官",
                 office_event="置监官三人", post_event="监领物料库，编制三人",
                 officer="京朝官、内侍差充")
    alias_note(w, i, duty_tp, aliases, "简称")
    finish(w, touched, "整理作坊物料库合库沿革、先后隶属、物料职掌、监官编制与简称。")


def entry937():
    i, main = 937, F[937]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "皮角场库", "机构", "北宋初",
         "已置皮角一场三库", origin, "军器物料场库",
         "记录宋初一场三库。", "职源与沿革", update_event=True)
    node(w, touched, i, "皮角场库", "机构", "北宋景德三年",
         "皮角一场三库并为皮角场库", origin, "军器物料场库",
         "记录景德三年合并。", "职源与沿革", update_event=True)
    node(w, touched, i, "皮角场库", "机构", "北宋元祐时",
         "仍为一场三库，合称皮角四场库", origin, "军器物料场库统称",
         "记录元祐时一场三库及合称。", "职源与沿革", update_event=True)
    parent_child(w, touched, i, "军器监", "皮角场库", "北宋元丰新制",
                 main, "元丰后皮角场库隶军器监。",
                 parent_event="统辖皮角场库", child_event="元丰后隶军器监")
    duty_tp = node(w, touched, i, "皮角场库", "机构",
                   "宋代（皮角场库，具体年月未载）",
                   "收纳采购动物皮角筋骨脂硝，供作坊制造军器鞍辔毡毯",
                   duty, "军器物料场库", "整理皮角场库职掌。", "职掌", update_event=True)
    office_staff(w, touched, i, "皮角场库", "皮角场库监官",
                 "宋代（皮角场库，具体年月未载）", roster,
                 "皮角场库置监官二人。", "编制", quota=2,
                 staff_type="监官", office_event="置监官二人",
                 post_event="监领皮角场库，编制二人")
    alias_note(w, i, duty_tp, aliases, "简称")
    finish(w, touched, "整理皮角场库一场三库沿革、军器监隶属、职掌编制与简称。")


def entry938():
    i, main = 938, F[938]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "皮角场库", "监在京皮角四场库务",
        "宋代（皮角场库，具体年月未载）", main,
        "监在京皮角四场库务掌监领皮角场库。", staff_type="监当官",
        office_event="设置监当官", post_event="监领皮角场库公事",
        officer="文臣京朝官、三班使臣、内侍官差充")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理监在京皮角四场库务职掌、差充来源与简称。")


def entry939():
    i, main = 939, F[939]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    node(w, touched, i, "斩马刀局", "机构", "北宋熙宁五年五月一日",
         "始设斩马刀局", origin, "兵器制造局",
         "记录斩马刀局始设时间。", "职源", update_event=True)
    parent_child(w, touched, i, "东、西作坊", "斩马刀局",
                 "宋代（斩马刀局，具体年月未载）", main,
                 "斩马刀局隶东、西作坊。",
                 parent_event="统辖斩马刀局", child_event="隶东、西作坊")
    duty_tp = node(w, touched, i, "斩马刀局", "机构", "北宋熙宁五年五月一日",
                   "专造供实战及颁赐边将的斩马大刀", duty,
                   "兵器制造局", "整理斩马刀局职掌。", "职掌")
    office_staff(w, touched, i, "斩马刀局", "管勾作坊造斩马刀",
                 "宋代（斩马刀局，具体年月未载）", roster,
                 "斩马刀局设管勾官。", "编制", staff_type="管勾官",
                 office_event="设管勾官、作头并由禁军轮值",
                 post_event="管勾斩马刀局造作")
    office_staff(w, touched, i, "斩马刀局", "斩马刀局作头",
                 "宋代（斩马刀局，具体年月未载）", roster,
                 "斩马刀局诸作有作头。", "编制", staff_type="作头",
                 office_event="设管勾官、作头并由禁军轮值",
                 post_event="管领诸作人匠")
    office_staff(w, touched, i, "斩马刀局", "斩马刀局看守禁军",
                 "宋代（斩马刀局，具体年月未载）", roster,
                 "斩马刀局由禁军一百人轮值看守。", "编制", quota=100,
                 staff_type="禁军", office_event="设管勾官、作头并由禁军轮值",
                 post_event="轮值看守斩马刀局，编制一百人", officer="禁军")
    cite(w, "Timepoints", duty_tp, i, main, "补证斩马刀局职局性质及东、西作坊隶属。")
    finish(w, touched, "整理斩马刀局熙宁始置、东西作坊隶属、造刀职掌及管勾作头禁军编制。")


def entry940():
    i, quote = 940, F[940]["text"]
    w, touched = W(i), set()
    office_staff(w, touched, i, "斩马刀局", "管勾作坊造斩马刀",
                 "宋代（斩马刀局，具体年月未载）", quote,
                 "管勾作坊造斩马刀由内侍差充，掌监领斩马刀局。",
                 staff_type="管勾官", office_event="设置管勾作坊造斩马刀",
                 post_event="由内侍差充，掌监领斩马刀局公事", officer="内侍差充")
    finish(w, touched, "整理管勾作坊造斩马刀差充来源与监领职掌。")


def main():
    order = [921, 925, 922, 923, 924, *range(926, 941)]
    for i in order:
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
