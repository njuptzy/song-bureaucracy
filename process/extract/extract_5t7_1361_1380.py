#!/usr/bin/env python3
"""提取 chapter5t7 第1361-1380条：御前忠佐散员、横行五司与阁职。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1341_1360 as previous


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


F = {i: load(i) for i in range(1361, 1381)}
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
office_staff = previous.office_staff
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "五代": 950,
    "宋初": 960,
    "北宋": 970,
    "北宋雍熙四年": 987,
    "北宋端拱元年": 988,
    "北宋端拱元年后": 988.5,
    "北宋淳化中": 992,
    "北宋咸平元年四月十六日": 998.29,
    "北宋大中祥符二年正月二十七日": 1009.07,
    "北宋大中祥符七年": 1014,
    "北宋景祐二年": 1035,
    "北宋熙宁二年": 1069,
    "北宋熙宁四年七月二十一日": 1071.55,
    "北宋熙宁四年十二月二十二日": 1071.96,
    "北宋元丰二年": 1079,
    "北宋政和二年前": 1111.9,
    "北宋政和二年": 1112,
    "北宋政和二年后": 1112.1,
    "北宋政和六年八月以前": 1116.59,
    "北宋政和六年八月": 1116.6,
    "北宋政和六年八月后": 1116.61,
    "南宋": 1127,
    "南宋绍兴二十六年十一月": 1156.84,
    "南宋绍兴二十九年四月十六日": 1159.29,
    "南宋乾道六年八月": 1170.6,
    "宋代（具体年月未载）": 1100.1,
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


def evolution(w, touched, i, source_title, target_title, time, quotation,
              decision, field_name=None, *, entity_type="官职",
              source_event=None, target_event=None):
    source = node(
        w, touched, i, source_title, entity_type, time,
        source_event or f"改称{target_title}", quotation, "演变前",
        f"建立或复用{source_title}演变节点。", field_name,
        update_event=True,
    )
    target = node(
        w, touched, i, target_title, entity_type, time,
        target_event or f"由{source_title}改称", quotation, "演变后",
        f"建立或复用{target_title}演变节点。", field_name,
        update_event=True,
    )
    relation(w, i, source, target, "前后演变", quotation, decision, field_name)
    return source, target


def office_child(w, touched, i, parent_title, child_title, time, quotation,
                 decision, field_name=None, *, parent_event=None,
                 child_event=None):
    parent = node(
        w, touched, i, parent_title, "机构", time,
        parent_event or f"统辖{child_title}", quotation, "上级机构",
        f"建立或复用{parent_title}同期节点。", field_name,
    )
    child = node(
        w, touched, i, child_title, "机构", time,
        child_event or f"隶属{parent_title}", quotation, "所属机构",
        f"建立或复用{child_title}同期节点。", field_name,
    )
    relation(w, i, parent, child, "上下级机构", quotation, decision, field_name)
    return parent, child


SIX_RANKS = (
    "御前忠佐马步军都军头", "御前忠佐马步军副都军头",
    "御前忠佐马军都军头", "御前忠佐马军副都军头",
    "御前忠佐步军都军头", "御前忠佐步军副都军头",
)


def entry1361():
    i, main, aliases = 1361, F[1361]["text"], field(1361, "简称")
    w, touched = W(i), set()
    post = node(
        w, touched, i, F[i]["title"], "官职", "宋代",
        "御前忠佐六资最末一等，位于马军副都军头之后", main,
        "御前忠佐禁秩", "补全步军副都军头的六资末等序位。",
        update_event=True,
    )
    group = node(
        w, touched, i, "御前忠佐六资", "官职", "宋代",
        "御前忠佐军头引见司六等迁转禁秩", main, "禁军位秩统称",
        "复用御前忠佐六资同期统称节点。",
    )
    relation(w, i, group, post, "统称与实例", main,
             "御前忠佐步军副都军头是六资最末一等。")
    office = node(
        w, touched, i, "御前忠佐军头、引见司", "机构", "宋代",
        "掌御前忠佐六资名籍", main, "御前忠佐禁军机构",
        "建立军头引见司宋代编制承载节点。",
    )
    staff(w, i, office, post, main,
          "御前忠佐步军副都军头为军头引见司六资之一。",
          staff_type="御前忠佐禁秩")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "补全步军副都军头的序位、统称、隶属与简称。")


def entry1362():
    i, main, aliases = 1362, F[1362]["text"], field(1362, "别名")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, F[i]["title"], "官职", "宋代",
        "军头引见司将校六等禁秩，不统兵，多作诸军将校寄资",
        SIX_RANKS, main, "正文逐一列出御前忠佐六资。",
    )
    office = node(
        w, touched, i, "御前忠佐军头、引见司", "机构", "宋代",
        "总掌御前忠佐六资名籍", main, "御前忠佐禁军机构",
        "复用军头引见司宋代承载节点。",
    )
    staff(w, i, office, group, main,
          "御前忠佐六资为御前忠佐军头引见司将校。",
          staff_type="将校禁秩统称")
    alias_note(w, i, group, aliases, "别名")
    finish(w, touched, "整理御前忠佐六资定义、六个实例、军头引见司隶属与别名。")


def entry1363():
    i, main, aliases = 1363, F[1363]["text"], field(1363, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, F[i]["title"], "官职", "宋代",
        "御前忠佐六资自马步军都军头至步军副都军头的通称",
        SIX_RANKS, main, "正文明确御前忠佐军头是六资通称。",
    )
    office = node(
        w, touched, i, "御前忠佐军头、引见司", "机构", "宋代",
        "总掌御前忠佐军头名籍并受理机密奏陈", main,
        "御前忠佐禁军机构", "复用军头引见司同期承载节点。",
    )
    staff(w, i, office, group, main,
          "御前忠佐军头名籍总掌于御前忠佐军头引见司。",
          staff_type="御前忠佐将校统称")
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理御前忠佐军头通称、六个实例、名籍隶属与简称。")


def entry1364():
    i, main, aliases = 1364, F[1364]["text"], field(1364, "简称")
    w, touched = W(i), set()
    _, north, _ = office_staff(
        w, touched, i, "御前忠佐军头、引见司", F[i]["title"], "北宋",
        main, "北宋祗候军员隶军头引见司。", staff_type="禁军兵级",
        office_event="差遣祗候军员", post_event="选殿前司有功军头、十将、节级充",
    )
    _, south, _ = office_staff(
        w, touched, i, "御前忠佐军头、引见司", F[i]["title"], "南宋",
        main, "南宋祗候军员仍隶军头引见司。", staff_type="禁军兵级",
        office_event="差遣祗候军员", post_event="由枢密院军马司差取兵级填阙，供本司差使",
    )
    cite(w, "Timepoints", north, i, main, "保存北宋选补来源和差使。")
    cite(w, "Timepoints", south, i, main, "保存南宋填阙、外差和便殿祗应职掌。")
    alias_note(w, i, south, aliases, "简称")
    finish(w, touched, "整理祗候军员的北宋、南宋选补和军头引见司隶属。")


def entry1365():
    i, main = 1365, F[1365]["text"]
    history, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    collective = node(
        w, touched, i, F[i]["title"], "机构", "北宋端拱元年后",
        "马直、步直两指挥并置，供军头引见司白直驱使", history,
        "军头引见司禁军编制", "建立马直、步直合称节点。", "职源与沿革",
        update_event=True,
    )
    office = node(
        w, touched, i, "御前忠佐军头、引见司", "机构", "北宋端拱元年后",
        "统制马直、步直两指挥", history, "御前忠佐禁军机构",
        "建立军头引见司统制两直节点。", "职源与沿革",
    )
    relation(w, i, office, collective, "上下级机构", history,
             "马直、步直为军头引见司所属禁军编制。", "职源与沿革")
    for title, time, event in (
        ("马直", "北宋雍熙四年", "始置，供军头引见司白直驱使"),
        ("步直", "北宋端拱元年", "始置，供军头引见司白直驱使"),
    ):
        node(w, touched, i, title, "机构", time, event, history,
             "军头引见司禁军直", f"记录{title}始置。", "职源与沿革",
             update_event=True)
        member = node(
            w, touched, i, title, "机构", "北宋端拱元年后",
            "马直、步直合称实例", history, "两直实例",
            f"建立{title}合称实例节点。", "职源与沿革",
        )
        relation(w, i, collective, member, "统称与实例", history,
                 f"{title}是马直、步直两直之一。", "职源与沿革")
        cite(w, "Timepoints", member, i, duty,
             f"保存{title}不出差屯戍、仅供白直驱使职掌。", "职掌")
        cite(w, "Timepoints", member, i, roster,
             f"保存{title}一指挥及军官编制。", "编制")
    evolution(
        w, touched, i, "马直", "云骑", "北宋熙宁四年十二月二十二日",
        aliases, "熙宁四年马直并入殿前司云骑。", "简称",
        entity_type="机构", source_event="罢并入云骑",
        target_event="接收军头司马直",
    )
    evolution(
        w, touched, i, "步直", "虎翼", "北宋熙宁四年十二月二十二日",
        aliases, "熙宁四年步直并入步军司虎翼。", "简称",
        entity_type="机构", source_event="罢并入虎翼",
        target_event="接收军头司步直",
    )
    alias_note(w, i, collective, aliases, "简称")
    finish(w, touched, "整理马直、步直始置、合称、编制职掌及熙宁四年并废。")


def entry1366():
    i, main = 1366, F[1366]["text"]
    origin, duty = field(i, "职源"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    evolution(
        w, touched, i, "许州员僚剩员", F[i]["title"], "北宋淳化中",
        origin, "淳化中许州员僚剩员立为军头司散员一班。", "职源",
        entity_type="机构", source_event="改立军头司散员一班",
        target_event="立为军头司散员一班",
    )
    _, unit = office_child(
        w, touched, i, "御前忠佐军头、引见司", F[i]["title"],
        "北宋淳化中", origin, "军头司祗候散员班隶军头引见司。", "职源",
        parent_event="统辖祗候散员班", child_event="立班供本司差使",
    )
    cite(w, "Timepoints", unit, i, duty,
         "保存散员班外差、降配安置和后殿另班职掌。", "职掌")
    for title, staff_type in (
        ("军头司祗候指挥使", "散员班将校"),
        ("军头司祗候副指挥使", "散员班将校"),
        ("军头司散员班都军头", "散员班将校"),
        ("军头司散员副兵马使", "散员班将校"),
        ("军头司散员副都头", "散员班将校"),
        ("军头司散指挥使", "散员班将校"),
        ("御前忠佐散员", "军兵"),
        ("御前忠佐剩员", "军兵"),
        ("御前忠佐曹司", "军兵"),
    ):
        _, post, _ = office_staff(
            w, touched, i, F[i]["title"], title,
            "北宋大中祥符二年正月二十七日", roster,
            f"{title}列入军头司祗候散员班编制。", "编制",
            staff_type=staff_type, office_event=f"编制列有{title}",
            post_event="列入祗候散员班编制",
        )
        cite(w, "Timepoints", post, i, roster, f"保存{title}编制身份。", "编制")
    alias_note(w, i, unit, aliases, "简称")
    finish(w, touched, "整理祗候散员班沿革、隶属、职掌、将校和军兵编制。")


def entry1367():
    i, main = 1367, F[1367]["text"]
    w, touched = W(i), set()
    members = (
        "军头司祗候指挥使", "军头司祗候副指挥使",
        "军头司散员班都军头", "军头司散员副兵马使",
        "军头司散员副都头",
    )
    group = group_instances(
        w, touched, i, F[i]["title"], "官职", "北宋",
        "祗候指挥使、副指挥使、都军头、副兵马使、副都头的合称",
        members, main, "正文逐一列出散员班将校。",
    )
    unit = node(
        w, touched, i, "御前忠佐军头司祗候散员班", "机构", "北宋",
        "编制散员班将校安置降补军人", main, "禁军散员班",
        "建立散员班同期承载节点。",
    )
    staff(w, i, unit, group, main, "散员班将校隶御前忠佐军头司散员班。",
          staff_type="将校统称")
    finish(w, touched, "建立散员班将校统称、五个实例及散员班隶属。")


def entry1368():
    i, main = 1368, F[1368]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "御前忠佐军头司祗候散员班", F[i]["title"],
        "北宋", main, "副兵马使为军头司散员班将校之一。",
        staff_type="骑兵将校", office_event="编制副兵马使",
        post_event="散员班骑兵将校",
    )
    group = node(
        w, touched, i, "御前忠佐军头司散员班将校", "官职", "北宋",
        "散员班将校统称", main, "散员班将校统称",
        "复用散员班将校统称节点。",
    )
    relation(w, i, group, post, "统称与实例", main,
             "军头司散员副兵马使是散员班将校之一。")
    finish(w, touched, "整理军头司散员副兵马使的散员班隶属和统称关系。")


def entry1369():
    i, main, aliases = 1369, F[1369]["text"], field(1369, "别名")
    w, touched = W(i), set()
    _, old, _ = office_staff(
        w, touched, i, "军头司", F[i]["title"], "五代", main,
        "伴饭都指挥使隶军头司，用于安置立功而无军职及降责军校。",
        staff_type="安置军职", office_event="安置伴饭都指挥使",
        post_event="始置，安置无军职可授或降责军校",
    )
    evolution(
        w, touched, i, F[i]["title"], "军头司散指挥使",
        "北宋大中祥符二年正月二十七日", main,
        "大中祥符二年伴饭都指挥使改名军头司散指挥使。",
        source_event="改名军头司散指挥使",
        target_event="由伴饭都指挥使改名",
    )
    alias_note(w, i, old, aliases, "别名")
    finish(w, touched, "整理伴饭都指挥使五代设置、军头司隶属、安置性质及改名。")


def entry1370():
    i, main = 1370, F[1370]["text"]
    origin, duty = field(i, "职源"), field(i, "职能")
    w, touched = W(i), set()
    _, post = evolution(
        w, touched, i, "伴饭都指挥使", F[i]["title"],
        "北宋大中祥符二年正月二十七日", origin,
        "大中祥符二年军头司伴饭都指挥使改名散指挥使。", "职源",
        source_event="改名军头司散指挥使",
        target_event="由伴饭都指挥使改名",
    )
    office = node(
        w, touched, i, "御前忠佐军头、引见司", "机构",
        "北宋大中祥符二年正月二十七日", "编制散指挥使",
        main, "御前忠佐禁军机构", "建立军头引见司同期承载节点。",
    )
    staff(w, i, office, post, main, "军头司散指挥使隶御前忠佐军头引见司。",
          staff_type="安置军职")
    later = node(
        w, touched, i, F[i]["title"], "官职", "北宋大中祥符七年",
        "用于安置因罪降责禁军军校", duty, "安置军职",
        "保存散指挥使降责安置职能。", "职能", update_event=True,
    )
    cite(w, "Timepoints", later, i, duty, "保存张捷降隶实例。", "职能")
    finish(w, touched, "整理军头司散指挥使改名、隶属和降责安置职能。")


def entry1371():
    i, main, aliases = 1371, F[1371]["text"], field(1371, "简称")
    w, touched = W(i), set()
    _, unit = office_child(
        w, touched, i, "御前忠佐军头、引见司", F[i]["title"], "宋代",
        main, "东京司备军隶御前忠佐军头引见司。",
        parent_event="统辖东京司备军", child_event="原额一千九百六十人，供白直差使",
    )
    reduced = node(
        w, touched, i, F[i]["title"], "机构", "北宋熙宁二年",
        "员额由一千九百六十人减至一千人", main, "禁军编制",
        "记录熙宁二年备军减额。", update_event=True,
    )
    later = node(
        w, touched, i, F[i]["title"], "机构", "北宋元丰二年",
        "仍由军头引见司统辖，供借事差科", aliases, "禁军编制",
        "记录元丰二年东京司备军仍存及差科。", "简称", update_event=True,
    )
    cite(w, "Timepoints", unit, i, main, "保存备军原额、职能和隶属。")
    cite(w, "Timepoints", reduced, i, aliases, "保存熙宁减额引文。", "简称")
    alias_note(w, i, later, aliases, "简称")
    finish(w, touched, "整理东京司备军隶属、原额、熙宁减额、元丰沿置和简称。")


def entry1372():
    i, main = 1372, F[1372]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "御前忠佐军头、引见司", F[i]["title"], "宋代",
        main, "等子隶军头引见司，供车驾扈从和后殿禁卫。",
        staff_type="禁卫兵员", office_event="统辖等子",
        post_event="由强壮材勇者充，扈从车驾并处置唐突拦驾者",
    )
    for subtype in ("准备等子", "正额等子"):
        member = node(
            w, touched, i, subtype, "官职", "宋代",
            f"{F[i]['title']}所分兵员类别", main, "等子类别",
            f"建立{subtype}节点。",
        )
        relation(w, i, post, member, "统称与实例", main,
                 f"正文明确等子分为{subtype}。")
    later = node(
        w, touched, i, F[i]["title"], "官职", "南宋绍兴二十六年十一月",
        "许知阁门官、提举军头司每日轮差二人随从", main, "禁卫兵员",
        "记录绍兴二十六年等子轮差制度。", update_event=True,
    )
    cite(w, "Timepoints", later, i, main, "保存等子轮差和出职转补将校制度。")
    finish(w, touched, "整理等子军头引见司隶属、禁卫职掌、两类实例和绍兴轮差。")


def entry1373():
    i, main = 1373, F[1373]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "御前忠佐军头、引见司", F[i]["title"], "宋代",
        main, "相扑隶军头引见司，供扈从车驾禁卫祗应。",
        staff_type="禁卫兵员", office_event="统辖相扑",
        post_event="选少壮有筋力者充，供车驾禁卫祗应",
    )
    finish(w, touched, "整理相扑的军头引见司隶属、选补条件和禁卫职掌。")


def entry1374():
    i, main = 1374, F[1374]["text"]
    origin, duty, rank = field(i, "职源与沿革"), field(i, "职能"), field(i, "品位")
    w, touched = W(i), set()
    old = node(
        w, touched, i, F[i]["title"], "官职", "宋初",
        "始置，佩弓箭袋、御剑扈从近卫", origin, "皇帝近卫",
        "建立御带宋初节点。", "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", old, i, duty, "保存御带扈从近卫职能。", "职能")
    cite(w, "Timepoints", old, i, rank, "保存御带选补范围和亲信性质。", "品位")
    evolution(
        w, touched, i, F[i]["title"], "带御器械",
        "北宋咸平元年四月十六日", origin,
        "咸平元年御带改名带御器械。", "职源与沿革",
        source_event="改名带御器械", target_event="由御带改名，近侍宿卫",
    )
    finish(w, touched, "整理御带宋初设置、近卫职能、品位和咸平改名。")


def entry1375():
    i, main = 1375, F[1375]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster = field(i, "品位"), field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    _, post = evolution(
        w, touched, i, "御带", F[i]["title"],
        "北宋咸平元年四月十六日", origin,
        "咸平元年旧名御带改为带御器械。", "职源与沿革",
        source_event="改名带御器械", target_event="由御带改名，近侍宿卫",
    )
    cite(w, "Timepoints", post, i, duty,
         "保存带御器械在京宿卫和外任军中带职两类职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存官品随本官阶及叙位。", "品位")
    quota = node(
        w, touched, i, F[i]["title"], "官职", "北宋景祐二年",
        "定员六人", roster, "皇帝近卫", "记录景祐二年定员。", "编制",
        update_event=True,
    )
    south = node(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "南宋沿置", origin, "皇帝近卫", "记录南宋沿置。", "职源与沿革",
        update_event=True,
    )
    increased = node(
        w, touched, i, F[i]["title"], "官职", "南宋绍兴二十九年四月十六日",
        "增置四员", roster, "皇帝近卫", "记录绍兴二十九年增员。", "编制",
        update_event=True,
    )
    cite(w, "Timepoints", quota, i, roster, "保存北宋定员六人。", "编制")
    cite(w, "Timepoints", south, i, origin, "保存南宋沿置。", "职源与沿革")
    alias_note(w, i, increased, aliases, "简称与别名")
    finish(w, touched, "整理带御器械改名、职掌、品位、北宋定员、南宋沿置增员和别名。")


def entry1376():
    i, main = 1376, F[1376]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "机构", "宋代（具体年月未载）",
        "东上阁门司、西上阁门司、引进司、客省司、四方馆司的总称",
        ("东上阁门司", "西上阁门司", "引进司", "客省司", "四方馆司"),
        main, "正文直接定义横行五司的五个机构实例。",
    )
    finish(w, touched, "建立横行五司及东、西上阁门司、引进司、客省司、四方馆司实例。")


def add_office_post(w, touched, i, office, post, time, quotation, decision):
    return office_staff(
        w, touched, i, office, post, time, quotation, decision,
        staff_type="阁门官", office_event=f"设置{post}",
        post_event=f"任{office}职事",
    )[1]


def entry1377():
    i, main, aliases = 1377, F[1377]["text"], field(1377, "简称")
    w, touched = W(i), set()
    early = (
        ("东上阁门司", "东上阁门使"), ("东上阁门司", "东上阁门副使"),
        ("西上阁门司", "西上阁门使"), ("西上阁门司", "西上阁门副使"),
    )
    early_group = group_instances(
        w, touched, i, F[i]["title"], "官职", "北宋政和二年前",
        "东、西上阁门使及副使的总称", tuple(post for _, post in early),
        main, "正文明确政和二年前阁门官实例。",
    )
    for office, post in early:
        add_office_post(w, touched, i, office, post, "北宋政和二年前", main,
                        f"{post}隶{office}。")
    reform = group_instances(
        w, touched, i, F[i]["title"], "官职", "北宋政和二年后",
        "政和二年后知东、西上阁门事的总称",
        ("知东上阁门事", "知西上阁门事"), main,
        "正文明确政和二年阁门官改称实例。",
    )
    add_office_post(w, touched, i, "东上阁门司", "知东上阁门事",
                    "北宋政和二年后", main, "知东上阁门事隶东上阁门司。")
    add_office_post(w, touched, i, "西上阁门司", "知西上阁门事",
                    "北宋政和二年后", main, "知西上阁门事隶西上阁门司。")
    south_members = (
        "知阁门事", "同知阁门事", "主管阁门公事", "同主管阁门公事",
        "阁门宣赞舍人", "阁门祗候", "阁门舍人",
    )
    south = group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "南宋知阁门事以下诸阁门官的总称", south_members, main,
        "正文逐一列出南宋阁门官实例。",
    )
    for post in south_members:
        add_office_post(w, touched, i, "阁门", post, "南宋", main,
                        f"{post}为南宋阁门官。")
    evolution(
        w, touched, i, "阁门通事舍人", "阁门宣赞舍人",
        "北宋政和六年八月", main,
        "政和六年八月阁门通事舍人改名阁门宣赞舍人。",
        source_event="改名阁门宣赞舍人", target_event="由阁门通事舍人改名",
    )
    created = node(
        w, touched, i, "阁门舍人", "官职", "南宋乾道六年八月",
        "创置，列为阁门官", main, "阁门官",
        "记录乾道六年阁门舍人创置。", update_event=True,
    )
    alias_note(w, i, south, aliases, "简称")
    cite(w, "Timepoints", created, i, main, "保存阁门舍人创置时间。")
    assert early_group and reform and south
    finish(w, touched, "分期整理阁门官统称、东/西上阁门和南宋实例、编制及改名创置。")


def entry1378():
    i, main = 1378, F[1378]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "北宋政和六年八月以前",
        "阁门通事舍人、阁门祗候二等武臣清选",
        ("阁门通事舍人", "阁门祗候"), main,
        "正文明确早期阁职分通事舍人、祗候二等。",
    )
    group_instances(
        w, touched, i, F[i]["title"], "官职", "北宋政和六年八月后",
        "阁门宣赞舍人、阁门祗候二等武臣清选",
        ("阁门宣赞舍人", "阁门祗候"), main,
        "正文明确政和六年通事舍人改名后的阁职实例。",
    )
    late = group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋乾道六年八月",
        "增阁门舍人后，与宣赞舍人、祗候同属阁职",
        ("阁门宣赞舍人", "阁门祗候", "阁门舍人"), main,
        "正文明确乾道六年阁门舍人也属阁职。",
    )
    office = node(
        w, touched, i, "阁门", "机构", "南宋乾道六年八月",
        "设置三类阁职", main, "阁门机构", "建立阁门同期节点。",
    )
    staff(w, i, office, late, main, "阁职为阁门所属武臣清选统称。",
          staff_type="武臣清选统称")
    finish(w, touched, "分期整理阁职的通事/宣赞舍人、祗候和乾道新增舍人实例。")


def entry1379():
    i, main, aliases = 1379, F[1379]["text"], field(1379, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "阁门", F[i]["title"], "宋代（具体年月未载）",
        main, "点检阁门簿书公事为阁门兼官。", staff_type="兼官",
        office_event="设置点检簿书兼官",
        post_event="由宣赞或通事舍人、阁门祗候兼带，审验簿书并催驱文字",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理点检阁门簿书公事的阁门隶属、兼带来源、职掌与简称。")


def entry1380():
    i, main = 1380, F[1380]["text"]
    origin, duty = field(i, "职源"), field(i, "职掌")
    rank, roster, aliases = field(i, "品位"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "阁门", F[i]["title"],
        "北宋熙宁四年七月二十一日", origin,
        "熙宁四年始置阁门看班祗候六人。", "职源",
        quota="六人", staff_type="职事官",
        office_event="始置看班祗候", post_event="始置，前后殿逐日祗应",
    )
    cite(w, "Timepoints", post, i, duty,
         "保存看班祗候逐日祗应及五年迁阁门祗候制度。", "职掌")
    cite(w, "Timepoints", post, i, rank,
         "保存三班院选补范围和位次。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存定员六人。", "编制")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理阁门看班祗候始置、阁门隶属、职掌、品位、员额与简称。")


def main():
    for i in range(1361, 1381):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
