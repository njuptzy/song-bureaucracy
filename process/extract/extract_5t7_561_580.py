#!/usr/bin/env python3
"""提取 chapter5t7 第561-580条：司农寺属官、仓场与提点仓草场系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_541_560 as previous


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


F = {i: load(i) for i in range(561, 581)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
state = base.state
relation = base.relation
staff = base.staff
tp = base.tp
alias_note = base.alias_note


TIME_HINTS = {
    "东汉": 25, "北齐": 550, "宋初": 960, "宋前期": 980,
    "宋前期（置所年月未载）": 980.1,
    "宋前期（未载具体年月）": 980.2,
    "北宋开宝三年": 970, "北宋端拱二年": 989,
    "北宋淳化元年": 990, "北宋淳化二年": 991,
    "北宋大中祥符二年": 1009, "北宋治平三年六月": 1066.45,
    "北宋熙宁三年五月十七日": 1070.38,
    "北宋熙宁三年八月三日": 1070.60,
    "北宋熙宁五年七月十八日": 1072.54,
    "北宋熙宁六年十二月十六日": 1073.96,
    "北宋熙宁九年十二月四日": 1076.93,
    "北宋熙宁九年至元丰四年": 1078,
    "北宋元丰三年": 1080, "北宋元丰四年六月十五日": 1081.46,
    "北宋元丰五年": 1082, "北宋元丰新制": 1082.1,
    "北宋绍圣四年二月九日": 1097.10,
    "南宋": 1127, "南宋建炎三年四月十三日": 1129.28,
    "南宋绍兴三年十月二十九日": 1133.83,
    "南宋绍兴三年十二月九日至乾道二年闰十一月二十七日": 1133.95,
    "南宋绍兴四年五月二十六日": 1134.38,
    "南宋绍兴十年十月": 1140.80,
    "南宋隆兴元年八月二十三日": 1163.63,
    "南宋隆兴二年闰十一月二十七日": 1164.94,
    "宋代（司农寺所属吏员）": 1050,
    "宋代（司农寺仓）": 1050.1,
    "宋代（司农寺草料场）": 1050.2,
    "宋代（仓场监专）": 1050.3,
    "北宋开宝三年至元丰五年前": 1025,
    "北宋（郑州三水磨务，置时未载）": 1050.4,
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


def set_event(w, tid, event, decision):
    old = w.conn.execute("select event from Timepoints where id=?", (tid,)).fetchone()[0]
    if old != event:
        w.conn.execute("update Timepoints set event=? where id=?", (event, tid))
        w._br("Timepoints", tid, f"事件说明由‘{old}’规范为‘{event}’：{decision}")


def exact_state(w, i, title, type_, time, event, quotation, category, decision,
                field_name=None, *, officer=None, grade=None, note=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade, note=note,
    )
    set_event(w, tid, event, decision)
    return eid, tid


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def canonicalize_entity(w, old_title, new_title, type_, decision):
    old_id = w.find_entity(old_title, type_)
    new_id = w.find_entity(new_title, type_)
    if old_id is None:
        assert new_id is not None, (old_title, new_title)
        return new_id
    assert new_id is None or new_id == old_id, (old_id, new_id)
    w.conn.execute("update Entities set title=? where id=?", (new_title, old_id))
    w._br("Entities", old_id, decision)
    return old_id


def flag_relationship_citations(w, relationship_ids, note):
    for rid in relationship_ids:
        rows = w.conn.execute(
            "select id,conflict_flag,note from Citations "
            "where target_table='Relationships' and target_id=?", (rid,)
        ).fetchall()
        assert rows, rid
        for cid, flag, old_note in rows:
            if flag != 1 or old_note != note:
                w.conn.execute(
                    "update Citations set conflict_flag=1,note=? where id=?",
                    (note, cid),
                )
                w._br("Citations", cid, f"标记原书异说：{note}")


def entry561():
    i, main, aliases = 561, F[561]["text"], field(561, "简称")
    w = W(i)
    eid, early = exact_state(
        w, i, "同判司农寺事", "官职", "宋前期",
        "判寺官二人中资序稍浅者带同字，与主判官共同领寺事",
        main, "司农寺同判官", "建立同判司农寺事宋前期差遣制度。",
        officer="差遣官",
    )
    staff(w, i, tp(w, "司农寺", "机构", "宋前期"), early, main,
          "宋前期司农寺判寺官二人中一员称同判。", quota=1,
          staff_type="同判寺官")
    _, reform = exact_state(
        w, i, "同判司农寺事", "官职", "北宋熙宁三年五月十七日",
        "新法付司农寺后与判寺官共同领常平新法及农田、差役、水利事",
        aliases, "司农寺同判官", "建立熙宁三年新法职掌节点。", "简称",
        officer="差遣官",
    )
    staff(w, i, tp(w, "司农寺", "机构", "北宋熙宁三年至元丰五年"),
          reform, aliases, "熙宁三年司农寺同判官参与领新法事。", "简称",
          staff_type="同判寺官")
    alias_note(w, i, early, aliases, "简称")
    finish(w, {eid}, "整理同判司农寺事宋前期至熙宁新法时期完整时间链。")


def entry562():
    i = 562
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, origin = exact_state(
        w, i, "司农寺卿", "官职", "北齐", "始置司农寺卿",
        history, "司农寺长官", "建立司农寺卿名称源流。", "职源与沿革",
        officer="卿",
    )
    _, early = exact_state(
        w, i, "司农寺卿", "官职", "宋前期",
        "无实际职事，为本官阶之一，元丰寄禄格易为中散大夫阶",
        duty, "阶官", "建立宋前期阶官职掌。", "职掌", officer="卿",
        grade="从四品",
    )
    cite(w, "Timepoints", early, i, rank, "补充宋前期及元丰后品位。", "品位")
    _, reform = exact_state(
        w, i, "司农寺卿", "官职", "北宋元丰新制",
        "改为职事官，掌仓储委积政令，总苑囿库务并谨出纳，编制一人",
        duty, "司农寺长官", "规范元丰新制职掌与定额。", "职掌",
        officer="卿", grade="从四品",
    )
    cite(w, "Timepoints", reform, i, roster, "补充元丰新制卿一人。", "编制")
    staff(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制司农寺置卿一人。", "编制", quota=1, staff_type="卿")
    _, abolished = exact_state(
        w, i, "司农寺卿", "官职", "南宋建炎三年四月十三日", "罢置",
        history, "司农寺长官", "建立建炎三年罢置节点。", "职源与沿革",
        officer="卿",
    )
    _, restored = exact_state(
        w, i, "司农寺卿", "官职", "南宋绍兴四年五月二十六日",
        "复置一员", history, "司农寺长官", "建立绍兴四年复置节点。",
        "职源与沿革", officer="卿",
    )
    cite(w, "Timepoints", restored, i, aliases, "补充复置与简称证据。", "简称与别名")
    alias_note(w, i, early, aliases, "简称与别名")
    finish(w, {eid}, "整理司农寺卿源流、阶职转换、存废与品位完整时间链。")


def entry563():
    i = 563
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, origin = exact_state(
        w, i, "司农寺少卿", "官职", "北齐", "始置司农寺少卿",
        history, "司农寺副长官", "建立司农寺少卿名称源流。", "职源与沿革",
        officer="少卿",
    )
    _, early = exact_state(
        w, i, "司农寺少卿", "官职", "宋前期",
        "无实际职事，为本官阶，元丰寄禄格易为朝议大夫阶",
        duty, "阶官", "建立宋前期阶官职掌。", "职掌", officer="少卿",
    )
    _, reform = exact_state(
        w, i, "司农寺少卿", "官职", "北宋元丰新制",
        "改为职事官，副贰司农寺卿、佐卿总领寺事，编制一人",
        duty, "司农寺副长官", "规范元丰新制职掌与定额。", "职掌",
        officer="少卿", grade="正六品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰后品位班次。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补充少卿一人。", "编制")
    staff(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制司农寺置少卿一人。", "编制", quota=1, staff_type="少卿")
    _, abolished = exact_state(
        w, i, "司农寺少卿", "官职", "南宋建炎三年四月十三日", "罢置",
        history, "司农寺副长官", "建立建炎三年罢置节点。", "职源与沿革",
        officer="少卿",
    )
    _, restored = exact_state(
        w, i, "司农寺少卿", "官职", "南宋绍兴四年五月二十六日",
        "复置一员", history, "司农寺副长官", "建立绍兴四年复置节点。",
        "职源与沿革", officer="少卿",
    )
    alias_note(w, i, early, aliases, "简称与别名")
    finish(w, {eid}, "整理司农寺少卿源流、阶职转换、存废与品位完整时间链。")


def entry564():
    i = 564
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    eid, origin = exact_state(
        w, i, "司农寺丞", "官职", "北齐", "始置司农寺丞",
        history, "司农寺属官", "建立司农寺丞名称源流。", "职源与沿革",
        officer="丞",
    )
    _, early = exact_state(
        w, i, "司农寺丞", "官职", "宋前期",
        "初不除人，为文臣所带本官阶而无实际职事",
        history, "阶官", "建立宋前期沿置而不除人节点。", "职源与沿革",
        officer="丞",
    )
    cite(w, "Timepoints", early, i, duty, "补充宋前期无职事。", "职掌")
    cite(w, "Timepoints", early, i, rank, "补充宋初沿唐品位。", "品位")
    changes = (
        ("北宋熙宁三年八月三日", "始除人一员，参与新法事务", 1),
        ("北宋熙宁五年七月十八日", "增至二员", 2),
        ("北宋熙宁九年十二月四日", "增至四员，一员为都丞，其余三丞分管三局", 4),
        ("北宋元丰四年六月十五日", "减为一员", 1),
    )
    parent = tp(w, "司农寺", "机构", "北宋熙宁三年至元丰五年")
    for time, event, quota in changes:
        _, post = exact_state(
            w, i, "司农寺丞", "官职", time, event,
            roster, "司农寺属官", f"建立司农寺丞{time}编制变化。", "编制",
            officer="丞",
        )
        staff(w, i, parent, post, roster, f"{time}司农寺丞{quota}员。", "编制",
              quota=quota, staff_type="丞")
    _, reform = exact_state(
        w, i, "司农寺丞", "官职", "北宋元丰新制",
        "参领司农寺事，定额一员", duty, "司农寺属官",
        "规范元丰新制职掌。", "职掌", officer="丞", grade="正八品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰新制品位班次。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补充元丰新制定额。", "编制")
    staff(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制司农寺置丞一员。", "编制", quota=1, staff_type="丞")
    _, later = exact_state(
        w, i, "司农寺丞", "官职", "北宋绍圣四年二月九日", "定额二员",
        roster, "司农寺属官", "建立绍圣四年定额节点。", "编制", officer="丞",
    )
    _, abolished = exact_state(
        w, i, "司农寺丞", "官职", "南宋建炎三年四月十三日", "罢置",
        history, "司农寺属官", "建立建炎三年罢置节点。", "职源与沿革",
        officer="丞",
    )
    _, restored = exact_state(
        w, i, "司农寺丞", "官职", "南宋绍兴三年十月二十九日", "复置",
        history, "司农寺属官", "建立绍兴三年复置节点。", "职源与沿革",
        officer="丞",
    )
    _, south_quota = exact_state(
        w, i, "司农寺丞", "官职",
        "南宋绍兴三年十二月九日至乾道二年闰十一月二十七日",
        "此期编制二员", roster, "司农寺属官", "建立南宋定额节点。", "编制",
        officer="丞",
    )
    alias_note(w, i, early, aliases, "简称与别名")
    touched.add(eid)
    finish(w, touched, "整理司农寺丞源流、职掌、存废及历次定额完整时间链。")


def entry565():
    i = 565
    history, duty, rank, roster = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid, created = exact_state(
        w, i, "司农寺都丞", "官职", "北宋熙宁九年十二月四日",
        "始置一员，总管水利、免役、保甲三局丞",
        history, "司农寺属官", "建立司农寺都丞始置节点。", "职源与沿革",
        officer="都丞", grade="位比路提点刑狱公事",
    )
    cite(w, "Timepoints", created, i, duty, "补充总管三局职掌。", "职掌")
    cite(w, "Timepoints", created, i, rank, "补充选任及班位。", "品位")
    cite(w, "Timepoints", created, i, roster, "补充都丞一员。", "编制")
    staff(w, i, tp(w, "司农寺", "机构", "北宋熙宁三年至元丰五年"),
          created, roster, "熙宁九年司农寺置都丞一员。", "编制",
          quota=1, staff_type="都丞")
    _, abolished = exact_state(
        w, i, "司农寺都丞", "官职", "北宋元丰四年六月十五日", "罢置",
        history, "司农寺属官", "建立元丰四年罢置节点。", "职源与沿革",
        officer="都丞",
    )
    finish(w, {eid}, "整理司农寺都丞始置、职掌与罢废完整时间链。")


def entry566():
    i, main = 566, F[566]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "权司农寺都丞", "官职", "北宋熙宁九年至元丰四年",
        "资序浅、不能正称司农寺都丞者所带权衔",
        main, "司农寺都丞权官", "建立权司农寺都丞资序制度。",
        officer="权官", grade="资序低于正司农寺都丞",
    )
    staff(w, i, tp(w, "司农寺", "机构", "北宋熙宁三年至元丰五年"), post,
          main, "司农寺都丞制度存续期可差权司农寺都丞。",
          staff_type="权都丞")
    finish(w, {eid}, "整理权司农寺都丞资序及隶属时间链。")


def entry567():
    i, main, aliases = 567, F[567]["text"], field(567, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "权发遣司农寺都丞", "官职", "北宋熙宁九年至元丰四年",
        "差充者资格比权司农寺都丞更浅，故带权发遣",
        main, "司农寺都丞权发遣官", "建立权发遣司农寺都丞资序制度。",
        officer="权发遣官", grade="资序低于权司农寺都丞",
    )
    staff(w, i, tp(w, "司农寺", "机构", "北宋熙宁三年至元丰五年"), post,
          main, "司农寺都丞制度存续期可差权发遣司农寺都丞。",
          staff_type="权发遣都丞")
    alias_note(w, i, post, aliases, "简称")
    finish(w, {eid}, "整理权发遣司农寺都丞资序、简称与隶属时间链。")


def entry568():
    i = 568
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, origin = exact_state(
        w, i, "司农寺主簿", "官职", "北齐", "始置司农寺主簿",
        history, "司农寺属官", "建立司农寺主簿名称源流。", "职源与沿革",
        officer="主簿",
    )
    _, created = exact_state(
        w, i, "司农寺主簿", "官职", "北宋治平三年六月",
        "北宋始实除一员", history, "司农寺属官", "规范治平三年始除节点。",
        "职源与沿革", officer="主簿",
    )
    cite(w, "Timepoints", created, i, roster, "补充初置一员。", "编制")
    changes = (
        ("北宋熙宁五年七月十八日", "增为二员", 2),
        ("北宋熙宁九年十二月四日", "增为五员", 5),
        ("北宋元丰四年六月十五日", "此前增至六员，此日减为三员", 3),
    )
    parent = tp(w, "司农寺", "机构", "北宋熙宁三年至元丰五年")
    for time, event, quota in changes:
        _, post = exact_state(
            w, i, "司农寺主簿", "官职", time, event, roster,
            "司农寺属官", f"建立司农寺主簿{time}定额变化。", "编制",
            officer="主簿",
        )
        staff(w, i, parent, post, roster, f"{time}司农寺主簿定额记为{quota}员。",
              "编制", quota=quota, staff_type="主簿")
    _, reform = exact_state(
        w, i, "司农寺主簿", "官职", "北宋元丰新制",
        "勾稽本寺簿书、检法，定额一员", duty, "司农寺属官",
        "规范元丰新制职掌与定额。", "职掌", officer="主簿",
    )
    cite(w, "Timepoints", reform, i, roster, "补充元丰新制一员。", "编制")
    _, abolished = exact_state(
        w, i, "司农寺主簿", "官职", "北宋绍圣四年二月九日", "罢置",
        history, "司农寺属官", "建立绍圣四年罢置节点。", "职源与沿革",
        officer="主簿",
    )
    _, restored = exact_state(
        w, i, "司农寺主簿", "官职", "南宋绍兴十年十月",
        "复置，参预签书公事", history, "司农寺属官",
        "建立绍兴十年复置节点。", "职源与沿革", officer="主簿",
    )
    cite(w, "Timepoints", restored, i, duty, "补充南渡后职掌。", "职掌")
    _, reduced = exact_state(
        w, i, "司农寺主簿", "官职", "南宋隆兴元年八月二十三日", "减省",
        history, "司农寺属官", "建立隆兴元年减省节点。", "职源与沿革",
        officer="主簿",
    )
    _, restored_again = exact_state(
        w, i, "司农寺主簿", "官职", "南宋隆兴二年闰十一月二十七日", "复置",
        history, "司农寺属官", "建立隆兴二年复置节点。", "职源与沿革",
        officer="主簿",
    )
    alias_note(w, i, created, aliases, "简称与别名")
    finish(w, {eid}, "整理司农寺主簿源流、职掌、存废及动态定额完整时间链。")


def entry569():
    i = 569
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid = canonicalize_entity(
        w, "司农寺勾当公事官", "司农寺勾当公事", "官职",
        "以正式词头‘司农寺勾当公事’规范第559条编制中预建的同一差遣官实体。",
    )
    _, created = exact_state(
        w, i, "司农寺勾当公事", "官职", "北宋熙宁六年十二月十六日",
        "始置四员，与寺丞、主簿轮流按察诸路州军推行常平新法等事",
        history, "司农寺差遣官", "建立司农寺勾当公事始置节点。",
        "职源与沿革", officer="差遣官", grade="以京官或选人差充",
    )
    cite(w, "Timepoints", created, i, duty, "补充按察诸路职掌。", "职掌")
    cite(w, "Timepoints", created, i, rank, "补充差充资格。", "品位")
    cite(w, "Timepoints", created, i, roster, "补充初置四员。", "编制")
    staff(w, i, tp(w, "司农寺", "机构", "北宋熙宁三年至元丰五年"),
          created, roster, "熙宁六年司农寺置勾当公事四员。", "编制",
          quota=4, staff_type="勾当公事")
    _, abolished = exact_state(
        w, i, "司农寺勾当公事", "官职", "北宋熙宁九年十二月四日", "罢置",
        history, "司农寺差遣官", "建立熙宁九年罢置节点。", "职源与沿革",
        officer="差遣官",
    )
    alias_note(w, i, created, aliases, "简称与别名")
    finish(w, {eid}, "整理司农寺勾当公事始置、职掌、资格与罢废完整时间链。")


def undated_agriculture_clerk(i, title, event, staff_type):
    main = F[i]["text"]
    w, touched = W(i), set()
    parent_eid, parent = exact_state(
        w, i, "司农寺", "机构", "宋代（司农寺所属吏员）",
        "所属吏员设置见于抱历曹司、手分、贴书等条目",
        main, "九寺之一", "建立司农寺无明确年月的吏员编制承载节点。",
    )
    eid, clerk = exact_state(
        w, i, title, "官职", "宋代（司农寺所属吏员）", event,
        main, "司农寺吏员", f"建立司农寺{title}职掌节点。", officer=staff_type,
    )
    staff(w, i, parent, clerk, main, f"{title}隶司农寺。", staff_type=staff_type)
    touched.update((parent_eid, eid))
    finish(w, touched, f"整理司农寺{title}职掌与隶属时间链。")


def entry570():
    undated_agriculture_clerk(
        570, "抱历曹司",
        "掌月支官吏禄廪及将士军粮之历，发粮前送粮仓作为支纳凭证及抽差斗子依据",
        "吏",
    )


def entry571():
    undated_agriculture_clerk(571, "手分", "掌行遣文字", "吏")


def entry572():
    undated_agriculture_clerk(572, "贴书", "掌行遣文字", "吏")


def entry573():
    i, main = 573, F[573]["text"]
    w, touched = W(i), set()
    eid = canonicalize_entity(
        w, "司农寺粮仓", "司农寺仓", "机构",
        "以正式词头‘司农寺仓’规范第559条预建的同一所属粮仓实体。",
    )
    office_eid, office = exact_state(
        w, i, "提点在京仓草场所", "机构", "宋前期（置所年月未载）",
        "设于东京汴阳坊，受都大提点司统领，置武臣提点官二人，"
        "掌京师诸粮仓、常平仓及草料场公事",
        main, "仓草场主管机构",
        "为司农寺仓宋前期隶属建立提点所承载节点。",
    )
    _, early = exact_state(
        w, i, "司农寺仓", "机构", "宋前期",
        "隶提点在京仓草场所，掌九谷储藏及官吏、军兵、宗室禄食供给",
        main, "京师粮仓统称", "建立司农寺仓宋前期隶属与职掌节点。",
    )
    relation(w, i, office, early, "上下级机构", main,
             "宋前期司农寺仓隶提点在京仓草场所。")
    _, reform = exact_state(
        w, i, "司农寺仓", "机构", "北宋元丰新制",
        "改隶司农寺；所属仓数原书分别记二十四、二十五两说",
        main, "司农寺所属粮仓", "规范元丰改制后隶属并并列仓数异说。",
    )
    parent = tp(w, "司农寺", "机构", "北宋元丰新制")
    rid = relation(w, i, parent, reform, "上下级机构", main,
                   "元丰改制后司农寺仓改隶司农寺，共有二十五仓。")
    conflict_note = (
        "第559条编制字段称元丰新制所属粮仓二十四；第573条正文称司农寺仓"
        "共有二十五仓。两说并存，暂不裁决。"
    )
    flag_relationship_citations(w, [rid], conflict_note)
    _, group = exact_state(
        w, i, "司农寺仓", "机构", "宋代（司农寺仓）",
        "诸仓统称，包括船仓、税仓、折中仓、富国仓、万盈仓、广衍仓等",
        main, "京师粮仓统称", "建立诸仓及属员关系承载节点。",
    )
    for title in ("船仓", "税仓", "富国仓", "万盈仓", "广衍仓"):
        seid, instance = exact_state(
            w, i, title, "机构", "宋代（司农寺仓）", "司农寺诸仓之一",
            main, "京师粮仓", f"建立{title}为司农寺仓实例。",
        )
        relation(w, i, group, instance, "统称与实例", main,
                 f"{title}是司农寺仓的实例。")
        touched.add(seid)
    for title, officer in (
        ("监官", "监官"), ("专知", "吏人"), ("副知", "吏人"), ("斗子", "吏人"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（司农寺仓）", "每仓所设官吏",
            main, "司农寺仓官吏", f"建立司农寺仓{title}编制。", officer=officer,
        )
        staff(w, i, group, post, main, f"司农寺每仓设{title}。", staff_type=officer)
        touched.add(seid)
    touched.update((eid, office_eid))
    finish(w, touched, "整理司农寺仓隶属、仓数异说、实例及属员完整时间链。")


def entry574():
    i, main = 574, F[574]["text"]
    w, touched = W(i), set()
    eid, created = exact_state(
        w, i, "折中仓", "机构", "北宋端拱二年",
        "始置，受纳商人输粟，优价给券，使赴江淮领取相当茶盐",
        main, "京师粮仓", "建立折中仓始置与职掌节点。",
    )
    relation(w, i, tp(w, "司农寺仓", "机构", "宋代（司农寺仓）"),
             created, "统称与实例", main, "折中仓是京师二十五仓之一。")
    successor_eid, renamed = exact_state(
        w, i, "折博仓", "机构", "北宋淳化二年", "由折中仓改名",
        main, "京师粮仓", "建立折博仓改名节点。",
    )
    relation(w, i, created, renamed, "前后演变", main,
             "淳化二年折中仓改名折博仓。")
    touched.update((eid, successor_eid))
    finish(w, touched, "整理折中仓始置、职掌及改名折博仓时间链。")


def entry575():
    i, main = 575, F[575]["text"]
    duty, aliases, history, roster = (
        field(i, "职掌"), field(i, "简称与别名"),
        field(i, "职源与沿革"), field(i, "编制"),
    )
    w, touched = W(i), set()
    eid = canonicalize_entity(
        w, "水磨务", "水碾磨务", "机构",
        "以核原书恢复的正式词头‘水碾磨务’规范第559条预建实体。",
    )
    _, early = exact_state(
        w, i, "水碾磨务", "机构", "北宋开宝三年至元丰五年前",
        "隶三司，掌水硙碾磨麦、米、豆等粮食以供尚食及内外之用",
        main, "监当局", "建立水碾磨务宋前期隶属与职掌节点。",
    )
    cite(w, "Timepoints", early, i, duty, "补充水碾磨务职掌。", "职掌")
    relation(w, i, tp(w, "三司", "机构", "宋初"), early, "上下级机构", main,
             "水碾磨务宋前期隶三司。")
    _, reform = exact_state(
        w, i, "水碾磨务", "机构", "北宋元丰新制",
        "改隶司农寺，继续掌水硙碾磨粮食",
        main, "司农寺所属监当局", "规范元丰改制后隶属。",
    )
    relation(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "元丰改制后水碾磨务隶司农寺。")
    _, group = exact_state(
        w, i, "水碾磨务", "机构", "北宋开宝三年",
        "始置东、西水碾磨务", history, "监当局统称",
        "建立东、西水碾磨务始置节点。", "职源与沿革",
    )
    instances = (
        ("东水碾磨务", "北宋开宝三年", "始置于京师永顺坊"),
        ("西水碾磨务", "北宋开宝三年", "始置于京师嘉庆坊"),
        ("大通门水磨务", "北宋淳化元年", "始置"),
        ("郑州三水磨务", "北宋（郑州三水磨务，置时未载）", "郑州所设三处水磨务"),
    )
    instance_nodes = {}
    for title, time, event in instances:
        seid, instance = exact_state(
            w, i, title, "机构", time, event, history,
            "水碾磨务实例", f"建立{title}实例。", "职源与沿革",
        )
        relation(w, i, group, instance, "统称与实例", history,
                 f"{title}是水碾磨务的实例。", "职源与沿革")
        instance_nodes[title] = instance
        touched.add(seid)
    for title in ("东水碾磨务", "西水碾磨务"):
        for post_title, quota, staff_type in (
            ("监官", 2, "使臣或内侍"),
        ):
            seid, post = exact_state(
                w, i, post_title, "官职", f"北宋开宝三年（{title}）",
                f"{title}所置监官", roster, "水碾磨务官吏",
                f"建立{title}监官定额。", "编制", officer="监官",
            )
            staff(w, i, instance_nodes[title], post, roster,
                  f"{title}置监官二员。", "编制", quota=quota,
                  staff_type=staff_type)
            touched.add(seid)
    miller_eid, miller = exact_state(
        w, i, "磨匠", "官职", "北宋开宝三年（东、西水碾磨务）",
        "东、西水碾磨务磨匠共二百零五人", roster, "水碾磨务匠役",
        "建立东、西水碾磨务磨匠总额。", "编制", officer="匠役",
    )
    staff(w, i, group, miller, roster, "东、西水碾磨务磨匠共二百零五人。",
          "编制", quota=205, staff_type="磨匠")
    monitor_eid, monitor = exact_state(
        w, i, "监官", "官职", "北宋淳化元年（大通门水磨务）",
        "大通门水磨务置监官一人，大中祥符二年改由西内染院监官兼领",
        roster, "水碾磨务官吏", "建立大通门水磨务监官定额。", "编制",
        officer="监官",
    )
    staff(w, i, instance_nodes["大通门水磨务"], monitor, roster,
          "大通门水磨务置监官一人。", "编制", quota=1, staff_type="监官")
    miller2_eid, miller2 = exact_state(
        w, i, "磨匠", "官职", "北宋淳化元年（大通门水磨务）",
        "大通门水磨务磨匠二十九人", roster, "水碾磨务匠役",
        "建立大通门水磨务磨匠定额。", "编制", officer="匠役",
    )
    staff(w, i, instance_nodes["大通门水磨务"], miller2, roster,
          "大通门水磨务磨匠二十九人。", "编制", quota=29, staff_type="磨匠")
    alias_note(w, i, early, aliases, "简称与别名")
    touched.update((eid, miller_eid, monitor_eid, miller2_eid))
    finish(w, touched, "整理水碾磨务隶属、职掌、实例与属员定额完整时间链。")


def entry576():
    i, main, aliases = 576, F[576]["text"], field(576, "简称")
    w, touched = W(i), set()
    eid = canonicalize_entity(
        w, "司农寺草场", "司农寺草料场", "机构",
        "以正式词头‘司农寺草料场’规范第559条预建的同一所属草场实体。",
    )
    office = tp(w, "提点在京仓草场所", "机构", "宋前期（置所年月未载）")
    _, early = exact_state(
        w, i, "司农寺草料场", "机构", "宋前期",
        "隶提点在京仓草场所，掌受纳刍秸、豆麦等以供诸官马饲料",
        main, "京师草料场统称", "建立宋前期隶属与职掌节点。",
    )
    relation(w, i, office, early, "上下级机构", main,
             "宋前期司农寺草料场隶提点在京仓草场所。")
    _, reform = exact_state(
        w, i, "司农寺草料场", "机构", "北宋元丰新制",
        "改隶司农寺；草场数原书分别记十、十二两说",
        main, "司农寺所属草料场", "规范元丰改制后隶属并并列场数异说。",
    )
    rid = relation(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform,
                   "上下级机构", main,
                   "元丰改制后司农寺草料场改隶司农寺，共有草场十二。")
    conflict_note = (
        "第559条编制字段称元丰新制所属草场十；第576条正文称元丰改制后"
        "共有草场十二。两说并存，暂不裁决。"
    )
    flag_relationship_citations(w, [rid], conflict_note)
    _, south = exact_state(
        w, i, "司农寺草料场", "机构", "南宋",
        "京师草料场一，建敖十二，掌受纳饲草豆麦供应官马",
        main, "京师草料场", "建立南宋草料场节点。",
    )
    _, group = exact_state(
        w, i, "司农寺草料场", "机构", "宋代（司农寺草料场）",
        "每场设监官、剩员、专知、副知掌管看守",
        main, "京师草料场统称", "建立草料场属员承载节点。",
    )
    for title, officer in (
        ("监官", "监官"), ("剩员", "使臣"), ("专知", "吏人"), ("副知", "吏人"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（司农寺草料场）", "每场所设官吏",
            main, "司农寺草料场官吏", f"建立草料场{title}编制。", officer=officer,
        )
        staff(w, i, group, post, main, f"司农寺每草料场设{title}。",
              staff_type=officer)
        touched.add(seid)
    alias_note(w, i, early, aliases, "简称")
    touched.add(eid)
    finish(w, touched, "整理司农寺草料场隶属、场数异说、南宋状态与属员时间链。")


def entry577():
    i, main = 577, F[577]["text"]
    w, touched = W(i), set()
    eid, group = exact_state(
        w, i, "监专", "官职", "宋代（仓场监专）",
        "诸仓、草场监官与专知、副知的合称，须巡视并值宿看守",
        main, "仓场官吏统称", "建立仓场监专统称及职责节点。",
        officer="官吏统称",
    )
    for title, officer in (("监官", "使臣"), ("专知", "吏人"), ("副知", "吏人")):
        seid, instance = exact_state(
            w, i, title, "官职", "宋代（仓场监专）",
            "仓场监专的具体官吏，须巡视所在仓场并值宿看守",
            main, "仓场官吏", f"建立{title}为监专实例。", officer=officer,
        )
        relation(w, i, group, instance, "统称与实例", main,
                 f"{title}是仓场监专的具体实例。")
        touched.add(seid)
    touched.add(eid)
    finish(w, touched, "整理仓场监专统称、实例及职责时间链。")


def entry578():
    i, main, aliases = 578, F[578]["text"], field(578, "简称")
    w, touched = W(i), set()
    eid, office = exact_state(
        w, i, "提点在京仓草场所", "机构", "宋前期（置所年月未载）",
        "设于东京汴阳坊，受都大提点司统领，置武臣提点官二人，"
        "掌京师诸粮仓、常平仓及草料场公事",
        main, "仓草场主管机构", "规范提点在京仓草场所位置与职掌。",
    )
    for title, time in (
        ("司农寺仓", "宋前期"), ("司农寺草料场", "宋前期"),
    ):
        relation(w, i, office, tp(w, title, "机构", time), "上下级机构", main,
                 f"提点在京仓草场所掌{title}公事。")
    _, abolished = exact_state(
        w, i, "提点在京仓草场所", "机构", "北宋元丰五年",
        "新官制下罢置，京师仓场改隶司农寺，旧职事归户部右曹",
        main, "仓草场主管机构", "建立元丰五年罢置与职事归并节点。",
    )
    alias_note(w, i, office, aliases, "简称")
    touched.add(eid)
    finish(w, touched, "整理提点在京仓草场所职掌、下辖仓场及罢置时间链。")


def entry579():
    i, main = 579, F[579]["text"]
    w, touched = W(i), set()
    eid, upper = exact_state(
        w, i, "都大提点在京仓草场司", "机构", "宋前期（未载具体年月）",
        "都大提点在京仓草场官之治所，职掌与提点所同，受理提点所申报公事",
        main, "仓草场主管机构", "建立都大提点司职掌与层级节点。",
    )
    office_eid, office = exact_state(
        w, i, "提点在京仓草场所", "机构", "宋前期（置所年月未载）",
        "设于东京汴阳坊，受都大提点司统领，置武臣提点官二人，"
        "掌京师诸粮仓、常平仓及草料场公事",
        main, "仓草场主管机构", "建立提点所受都大提点司统领节点。",
    )
    relation(w, i, upper, office, "上下级机构", main,
             "提点在京仓草场所公事须申都大提点在京仓草场司。")
    touched.update((eid, office_eid))
    finish(w, touched, "整理都大提点在京仓草场司与提点所上下级关系时间链。")


def entry580():
    i, main, aliases = 580, F[580]["text"], field(580, "简称")
    w, touched = W(i), set()
    office_eid, office = exact_state(
        w, i, "提点在京仓草场所", "机构", "宋前期（置所年月未载）",
        "设于东京汴阳坊，受都大提点司统领，置武臣提点官二人，"
        "掌京师诸粮仓、常平仓及草料场公事",
        main, "仓草场主管机构", "补充提点所属官编制承载节点。",
    )
    eid, post = exact_state(
        w, i, "提点在京仓草场", "官职", "宋前期（置所年月未载）",
        "由阁门祗候以上武臣二人充，钤辖京师诸粮仓、常平仓与草料场",
        main, "提点在京仓草场所长官", "建立提点在京仓草场差遣与职掌节点。",
        officer="武臣差遣官", grade="阁门祗候以上",
    )
    staff(w, i, office, post, aliases, "提点在京仓草场所以武臣二人充提点官。",
          "简称", quota=2, staff_type="武臣")
    alias_note(w, i, post, aliases, "简称")
    touched.update((office_eid, eid))
    finish(w, touched, "整理提点在京仓草场差遣、资格、定额与职掌时间链。")


def main():
    assert [F[i]["title"] for i in range(561, 581)] == [
        "同判司农寺事", "司农寺卿", "司农寺少卿", "司农寺丞",
        "司农寺都丞", "权司农寺都丞", "权发遣司农寺都丞",
        "司农寺主簿", "司农寺勾当公事", "抱历曹司", "手分", "贴书",
        "司农寺仓", "折中仓", "水碾磨务", "司农寺草料场", "监专",
        "提点在京仓草场所", "都大提点在京仓草场司", "提点在京仓草场",
    ]
    for i in range(561, 581):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
