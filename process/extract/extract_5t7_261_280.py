#!/usr/bin/env python3
"""提取 chapter5t7 第261-280条：光禄寺属官、太官令与御厨。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_241_260 as previous


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


F = {i: load(i) for i in range(261, 281)}
previous.F = F
previous.ENTRY_DB = ENTRY_DB
previous.previous.F = F
previous.previous.ENTRY_DB = ENTRY_DB

W = previous.W
field = previous.field
cite = previous.cite
state = previous.state
relation = previous.relation
staff = previous.staff
tp = previous.tp
alias_note = previous.alias_note


TIME_HINTS = {
    "秦汉": -221, "西汉武帝太初元年": -104, "西晋": 265,
    "北魏": 386, "南朝梁天监七年": 508, "北齐": 550,
    "唐昭宗天祐元年四月": 904.3, "五代": 907,
    "宋代": 960, "宋代（御厨）": 960.01, "宋初": 960.02,
    "北宋": 960.03, "北宋初": 960.04, "北宋沿置": 960.05,
    "北宋前期": 970,
    "宋前期": 970, "北宋东京元额（御厨）": 1050,
    "北宋元丰新制": 1080, "北宋元丰五年新制": 1082.01,
    "北宋元丰五年": 1082,
    "北宋元祐元年五月十五日": 1086.37,
    "北宋元祐二年正月十五日": 1087.04,
    "北宋元祐三年": 1088,
    "北宋元祐元年以后": 1086.5,
    "北宋哲宗朝以后": 1086.6,
    "北宋崇宁二年五月十四日": 1103.37,
    "北宋靖康元年正月四日": 1126.01,
    "南宋": 1127, "南宋建炎三年四月十三日": 1129.29,
    "南宋绍兴二十三年二月十七日": 1153.13,
    "南宋裁减至七百人（年月未载）": 1155.1,
    "南宋裁减至五百人（年月未载）": 1155.2,
    "南宋隆兴元年七月二十六日": 1163.56,
    "南宋乾道六年七月": 1170.55,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    m = re.search(r"(-?\d{3,4})", time or "")
    if m:
        return (int(m.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [r[0] for r in sorted(rows, key=lambda r: time_key(r[1], r[0]))]
    for n, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[n - 1] if n else None,
            succ_id=ordered[n + 1] if n + 1 < len(ordered) else None,
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


def existing_entity(w, title, type_):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def entry261():
    i, main, aliases = 261, F[261]["text"], field(261, "简称")
    w = W(i)
    eid, active = exact_state(
        w, i, "判光禄寺事", "官职", "宋前期",
        "以朝官以上充，掌领光禄寺职事", main,
        "光禄寺长官", "补足判光禄寺事的任职资格与职掌。",
        officer="差遣",
    )
    _, abolished = exact_state(
        w, i, "判光禄寺事", "官职", "北宋元丰五年", "行新官制后罢置",
        main, "光禄寺长官", "建立元丰五年罢判光禄寺事节点。",
        officer="差遣",
    )
    parent = tp(w, "光禄寺", "机构", "北宋沿置")
    staff(w, i, parent, active, main, "宋前期光禄寺置判寺官一员。", quota=1, staff_type="差遣")
    alias_note(w, i, active, aliases, "简称")
    rechain(w, eid, "连接判光禄寺事任职与元丰罢置节点。")
    w.commit()


def entry262():
    i = 262
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    specs = (
        ("南朝梁天监七年", "由光禄勋改为光禄卿", history, "前代职源", None),
        ("北齐", "始有光禄寺卿官名", history, "前代职源", None),
        ("北宋初", "无职事，为文臣迁转官阶", duty, "寄禄官", "从三品"),
        ("北宋元丰五年", "改为职事官，任光禄寺长官，领寺事并充祠祭行事官", duty, "光禄寺长官", "从四品"),
        ("北宋元祐三年", "卿、少卿不并置，二职合置一员", roster, "光禄寺长官", "从四品"),
        ("南宋建炎三年四月十三日", "光禄寺罢后不复置卿", history, "光禄寺长官", "从四品"),
    )
    nodes = {}
    for time, event, quote, category, grade in specs:
        eid, nodes[time] = exact_state(
            w, i, "光禄寺卿", "官职", time, event, quote, category,
            f"建立或补足光禄寺卿{time}节点。",
            {history: "职源与沿革", duty: "职掌", roster: "编制"}[quote],
            officer="阶官" if time == "北宋初" else "职事官", grade=grade,
        )
        touched.add(eid)
    cite(w, "Timepoints", nodes["北宋初"], i, rank, "记录宋初光禄寺卿品位。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, rank, "记录元丰改制后品位及九寺中的位次。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")
    staff(w, i, tp(w, "光禄寺", "机构", "北宋沿置"), nodes["北宋初"], duty, "宋初光禄寺卿为无职事阶官。", "职掌", staff_type="阶官")
    staff(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], roster, "元丰新制光禄寺卿一员。", "编制", quota=1)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称与别名")
    for eid in touched:
        rechain(w, eid, "整理光禄寺卿完整时间链。")
    w.commit()


def entry263():
    i = 263
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    specs = (
        ("北魏", "置光禄勋少卿，或省称光禄少卿", history, "前代职源", None, "职事官"),
        ("北齐", "始有光禄寺少卿官名", history, "前代职源", None, "职事官"),
        ("北宋初", "无职事，为文臣迁转官阶", duty, "寄禄官", "从四品上", "阶官"),
        ("北宋元丰五年", "改为职事官，任光禄寺副贰，佐正卿领寺事", duty, "光禄寺副长官", "正六品", "职事官"),
        ("北宋元祐三年", "卿、少卿共置一人，不并置", roster, "光禄寺副长官", "正六品", "职事官"),
        ("南宋建炎三年四月十三日", "光禄寺罢后不复置少卿", history, "光禄寺副长官", "正六品", "职事官"),
    )
    nodes = {}
    for time, event, quote, category, grade, officer in specs:
        eid, nodes[time] = exact_state(
            w, i, "光禄寺少卿", "官职", time, event, quote, category,
            f"建立或补足光禄寺少卿{time}节点。",
            {history: "职源与沿革", duty: "职掌", roster: "编制"}[quote],
            officer=officer, grade=grade,
        )
    cite(w, "Timepoints", nodes["北宋初"], i, rank, "记录宋初光禄寺少卿品位。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, rank, "记录元丰改制后品位与杂压位次。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")
    staff(w, i, tp(w, "光禄寺", "机构", "北宋沿置"), nodes["北宋初"], duty, "宋初光禄寺少卿为无职事阶官。", "职掌", staff_type="阶官")
    staff(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], roster, "元丰新制光禄寺少卿一员。", "编制", quota=1)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")
    rechain(w, eid, "整理光禄寺少卿完整时间链。")
    w.commit()


def entry264():
    i = 264
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    specs = (
        ("西汉武帝太初元年", "郎中令丞改为光禄勋丞", history, "前代职源", None, "职事官"),
        ("北齐", "始有光禄寺丞官称", history, "前代职源", None, "职事官"),
        ("北宋初", "无职事，为文臣迁转官阶", duty, "寄禄官", "从六品上", "阶官"),
        ("北宋元丰五年", "改为职事官，参领本寺祠祭礼料等事", duty, "光禄寺属官", "正八品", "职事官"),
        ("南宋建炎三年四月十三日", "随光禄寺罢置", history, "光禄寺属官", "正八品", "职事官"),
        ("南宋绍兴二十三年二月十七日", "复置一员，专掌祠祭礼料", history, "光禄寺属官", "正八品", "职事官"),
        ("南宋隆兴元年七月二十六日", "罢置", history, "光禄寺属官", "正八品", "职事官"),
    )
    nodes = {}
    for time, event, quote, category, grade, officer in specs:
        eid, nodes[time] = exact_state(
            w, i, "光禄寺丞", "官职", time, event, quote, category,
            f"建立或补足光禄寺丞{time}节点。",
            "职掌" if quote == duty else "职源与沿革",
            officer=officer, grade=grade,
        )
    for time in ("北宋初", "北宋元丰五年"):
        cite(w, "Timepoints", nodes[time], i, rank, "记录光禄寺丞相应时期品位。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")
    cite(w, "Timepoints", nodes["南宋绍兴二十三年二月十七日"], i, roster, "记录南宋复置一员。", "编制")
    staff(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], roster, "元丰新制光禄寺丞一员。", "编制", quota=1)
    staff(w, i, tp(w, "光禄寺", "机构", "南宋绍兴二十三年二月十七日"), nodes["南宋绍兴二十三年二月十七日"], roster, "绍兴二十三年复置光禄寺丞一员。", "编制", quota=1)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")
    rechain(w, eid, "整理光禄寺丞完整时间链。")
    w.commit()


def entry265():
    i = 265
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    specs = (
        ("西晋", "光禄勋下设主簿", history, "前代职源", None, "吏职"),
        ("北齐", "始置光禄寺主簿", history, "前代职源", None, "职事官"),
        ("北宋初", "无职事，为文臣迁转官阶", duty, "寄禄官", "从七品上", "阶官"),
        ("北宋元丰五年", "正名为职事官，钩考本寺簿书", duty, "光禄寺属官", "从八品", "职事官"),
        ("北宋元祐元年以后", "许通掌本寺公事", duty, "光禄寺属官", "从八品", "职事官"),
        ("南宋建炎三年四月十三日", "光禄寺罢后不复置主簿", history, "光禄寺属官", "从八品", "职事官"),
    )
    nodes = {}
    for time, event, quote, category, grade, officer in specs:
        eid, nodes[time] = exact_state(
            w, i, "光禄寺主簿", "官职", time, event, quote, category,
            f"建立或补足光禄寺主簿{time}节点。",
            "职掌" if quote == duty else "职源与沿革",
            officer=officer, grade=grade,
        )
    for time in ("北宋初", "北宋元丰五年"):
        cite(w, "Timepoints", nodes[time], i, rank, "记录光禄寺主簿相应时期品位。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")
    staff(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], roster, "元丰新制光禄寺主簿一员。", "编制", quota=1)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")
    rechain(w, eid, "整理光禄寺主簿完整时间链。")
    w.commit()


def entry266():
    i = 266
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    specs = (
        ("秦汉", "少府属官，掌进饭、肉事", history, "前代职源", None),
        ("西晋", "改隶光禄勋", history, "前代职源", None),
        ("北齐", "始置光禄寺太官署令", history, "前代职源", None),
        ("北宋元丰五年", "光禄寺始置，掌供御膳禁令、察视等事", duty, "光禄寺属官", "正九品"),
        ("北宋元祐元年五月十五日", "罢置", history, "光禄寺属官", "正九品"),
        ("北宋元祐二年正月十五日", "复置", history, "光禄寺属官", "正九品"),
        ("北宋崇宁二年五月十四日", "随太官事务并入殿中省尚食局太官局，改掌祠祭荐羞", history, "太官局职事官", "正九品"),
        ("北宋靖康元年正月四日", "殿中省六尚局罢后仍归隶光禄寺", roster, "光禄寺属官", "正九品"),
        ("南宋隆兴元年七月二十六日", "归隶太常寺", roster, "太常寺属官", "正九品"),
    )
    nodes = {}
    for time, event, quote, category, grade in specs:
        eid, nodes[time] = exact_state(
            w, i, "太官令", "官职", time, event, quote, category,
            f"建立或补足太官令{time}节点。",
            "职掌" if quote == duty else ("编制" if quote == roster else "职源与沿革"),
            officer="职事官", grade=grade,
        )
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, rank, "记录元丰改制后太官令品位。", "品位")
    cite(w, "Timepoints", nodes["北宋崇宁二年五月十四日"], i, duty, "记录并入太官局后止掌祠祭荐羞。", "职掌")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")

    # 为每次实际改隶建立同期机构节点，关系保持机构→官职方向。
    parent_specs = (
        ("光禄寺", "北宋元丰五年", "元丰改制后置太官令", duty, "寺监机构", nodes["北宋元丰五年"]),
        ("太官局", "北宋崇宁二年五月十四日", "御厨等并入后置太官令", history, "尚食局所属机构", nodes["北宋崇宁二年五月十四日"]),
        ("光禄寺", "北宋靖康元年正月四日", "殿中省六尚局罢后复领太官令", roster, "寺监机构", nodes["北宋靖康元年正月四日"]),
        ("太常寺", "南宋隆兴元年七月二十六日", "光禄寺并省后接领太官令", roster, "中央礼制机构", nodes["南宋隆兴元年七月二十六日"]),
    )
    touched = {eid}
    for title, time, event, quote, category, post in parent_specs:
        peid, parent = exact_state(
            w, i, title, "机构", time, event, quote, category,
            f"为太官令改隶建立{title}{time}同期节点。",
            "职掌" if quote == duty else ("编制" if quote == roster else "职源与沿革"),
        )
        staff(w, i, parent, post, quote, f"太官令在{time}隶{title}。",
              "职掌" if quote == duty else ("编制" if quote == roster else "职源与沿革"),
              quota=1)
        touched.add(peid)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")
    for x in touched:
        rechain(w, x, "整理太官令及其所隶机构完整时间链。")
    w.commit()


def simple_guanglu_clerk(i, title, time, event, quota, officer="吏"):
    main = F[i]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, title, "官职", time, event, main, "光禄寺吏",
        f"补足{title}的职掌、时期与定额。", officer=officer,
    )
    parent_time = "北宋沿置" if time == "宋前期" else "南宋绍兴二十三年二月十七日"
    staff(w, i, tp(w, "光禄寺", "机构", parent_time), post, main,
          f"光禄寺置{title}{quota}人。", quota=quota, staff_type=officer)
    rechain(w, eid, f"整理{title}时间链。")
    w.commit()


def entry267():
    simple_guanglu_clerk(267, "光禄寺府史", "宋前期", "承办光禄寺具体事务，编制四人", 4)


def entry268():
    simple_guanglu_clerk(268, "光禄寺驱使官", "宋前期", "递送文书、催办寺事等，编制二人", 2)


def entry269():
    simple_guanglu_clerk(269, "光禄寺供官", "宋前期", "祠祭时供给使，编制十五人", 15)


def entry270():
    simple_guanglu_clerk(
        270, "光禄寺胥佐", "南宋绍兴二十三年二月十七日",
        "承办寺务，位次于胥长、高于胥史，复寺时置一名", 1,
    )


def entry271():
    simple_guanglu_clerk(
        271, "光禄寺贴书", "南宋绍兴二十三年二月十七日",
        "抄写文字，复寺时置二名", 2,
    )


def entry272():
    i, main = 272, F[272]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    specs = (
        ("宋代", "掌承办御膳、赐宴赐食及祠祭膳羞等御厨事务", main, "宫廷膳食机构"),
        ("唐昭宗天祐元年四月", "已有御厨使", history, "宫廷膳食机构"),
        ("五代", "有御食厨", history, "宫廷膳食机构"),
        ("北宋初", "光禄寺太官、珍馐、良酝、掌醢职事分隶御厨", history, "宫廷膳食机构"),
        ("北宋元丰五年", "隶光禄寺，掌御膳、赐宴赐食及祠祭膳羞等事", duty, "光禄寺所属机构"),
        ("北宋崇宁二年五月十四日", "并入殿中省尚食局太官局", history, "宫廷膳食机构"),
        ("南宋", "沿置，隶礼部膳部司", main, "礼部膳部司所属机构"),
        ("北宋东京元额（御厨）", "官吏与工役依东京元额设置，工匠、库子、院子共一千五百二十一人", roster, "宫廷膳食机构"),
        ("南宋裁减至七百人（年月未载）", "御厨人员裁减至七百人", roster, "宫廷膳食机构"),
        ("南宋裁减至五百人（年月未载）", "御厨人员再减至五百人", roster, "宫廷膳食机构"),
        ("南宋乾道六年七月", "立定御厨人员编制四百人", roster, "宫廷膳食机构"),
    )
    nodes = {}
    for time, event, quote, category in specs:
        eid, nodes[time] = exact_state(
            w, i, "御厨", "机构", time, event, quote, category,
            f"建立或补足御厨{time}节点。",
            None if quote == main else ({history: "职源与沿革", duty: "职掌", roster: "编制"}[quote]),
        )
        touched.add(eid)
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, history, "补充御厨元丰改隶光禄寺。", "职源与沿革")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, aliases, "记录御厨简称、别名与地望。", "简称与别名", note="纯简称、别名不另建实体")
    relation(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], "上下级机构", history, "元丰新制御厨隶光禄寺。", "职源与沿革")
    relation(w, i, nodes["北宋崇宁二年五月十四日"], tp(w, "太官局", "机构", "北宋崇宁二年五月十四日"), "前后演变", history, "崇宁二年御厨并入太官局。", "职源与沿革")
    relation(w, i, tp(w, "膳部司", "机构", "南宋"), nodes["南宋"], "上下级机构", main, "南宋御厨隶礼部膳部司。")

    north = nodes["北宋东京元额（御厨）"]
    role_specs = (
        ("勾当御厨官", 4, "差遣"), ("监御厨官", 4, "差遣"),
        ("押司官", 3, "吏"), ("手分", 14, "吏"),
        ("正名书手", 13, "吏"), ("私名书手", 15, "吏"),
        ("副知", None, "吏"), ("后行", None, "吏"),
        ("厨子", None, "杂职"), ("库子", None, "杂职"),
        ("门子", None, "杂职"), ("库院子", None, "杂职"),
    )
    for title, quota, officer in role_specs:
        # 后续专条会把部分通用编制说明细化为具体职掌；这里不反向覆盖。
        reid, post = state(
            w, i, title, "官职", "北宋东京元额（御厨）",
            "御厨官吏或杂职之一", roster, "御厨官吏",
            f"据御厨编制建立{title}的御厨语境节点。", "编制", officer=officer,
        )
        staff(w, i, north, post, roster, f"北宋东京御厨置{title}。", "编制", quota=quota, staff_type=officer)
        touched.add(reid)
    cite(w, "Timepoints", tp(w, "厨子", "官职", "北宋东京元额（御厨）"), i, roster,
         "北宋御厨厨子称食手；纯称谓不另建重复实体。", "编制", note="北宋称食手")
    for x in touched:
        rechain(w, x, "整理御厨及官吏、杂职完整时间链。")
    w.commit()


def entry273():
    i, main, aliases = 273, F[273]["text"], field(273, "简称与别名")
    w = W(i)
    north_eid, north = exact_state(
        w, i, "勾当御厨官", "官职", "北宋东京元额（御厨）",
        "由内侍或京朝官、诸司使副充，掌领御厨职事，编制四人",
        main, "御厨长官", "补足勾当御厨官任用、职掌与定额。", officer="差遣",
    )
    south_eid, south = exact_state(
        w, i, "御厨干办官", "官职", "南宋",
        "南宋改勾当为干办，掌领御厨职事", aliases,
        "御厨长官", "按正式改称建立御厨干办官。", "简称与别名", officer="差遣",
    )
    relation(w, i, north, south, "前后演变", aliases, "南宋勾当御厨官改称御厨干办官。", "简称与别名")
    staff(w, i, tp(w, "御厨", "机构", "南宋"), south, aliases, "南宋御厨置干办官。", "简称与别名", staff_type="差遣")
    alias_note(w, i, north, aliases, "简称与别名")
    for eid in (north_eid, south_eid):
        rechain(w, eid, "整理勾当御厨官至御厨干办官演变链。")
    w.commit()


def entry274():
    i, main = 274, F[274]["text"]
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "御厨五局", "机构", "宋代", "御厨按分工划分的五局合称",
        main, "机构统称", "建立御厨五局统称。",
    )
    touched.add(generic_eid)
    parent = tp(w, "御厨", "机构", "宋代")
    for title in ("肉从食餬饼局", "铛食面粉局", "蒸作炙爆局", "脍锤笼局", "盘饭口味局"):
        eid, office = exact_state(
            w, i, title, "机构", "宋代（御厨）", "御厨五局之一",
            main, "御厨所属机构", f"按原文逐字建立御厨所属{title}。",
        )
        relation(w, i, generic, office, "统称与实例", main, f"{title}为御厨五局实例。")
        relation(w, i, parent, office, "上下级机构", main, f"御厨下分{title}。")
        touched.add(eid)
    cite(w, "Timepoints", generic, i, main, "记录大宴时每局差内侍官一人管勾。")
    for eid in touched:
        rechain(w, eid, "整理御厨五局统称与实例时间链。")
    w.commit()


def entry275():
    i, main = 275, F[275]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "监御厨官", "官职", "北宋东京元额（御厨）",
        "由内侍官或武官充，监视御厨公事是否符合条制程式，编制四人",
        main, "御厨官", "补足监御厨官任用、职掌和定额。", officer="差遣",
    )
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), post, main,
          "御厨置监御厨官四人。", quota=4, staff_type="差遣")
    cite(w, "Timepoints", post, i, main, "‘监官’仅为简称，不另建实体。", note="纯简称不另建实体")
    rechain(w, eid, "整理监御厨官时间链。")
    w.commit()


def entry276():
    i, main = 276, F[276]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "拘押官物使臣", "官职", "宋代",
        "由副知出职补官者递迁，主掌御厨官物", main,
        "御厨官", "建立拘押官物使臣的归隶、来源与职掌。", officer="差遣",
    )
    staff(w, i, tp(w, "御厨", "机构", "宋代"), post, main,
          "拘押官物使臣隶御厨。", staff_type="差遣")
    rechain(w, eid, "整理拘押官物使臣时间链。")
    w.commit()


def entry277():
    i, main = 277, F[277]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "副知", "官职", "北宋东京元额（御厨）",
        "隶御厨，主管官物；界满三年通理入仕，满二十年出职补承信郎",
        main, "御厨吏", "为既有副知建立御厨语境节点并补迁转规则。", officer="吏",
    )
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), post, main,
          "副知隶御厨并主管官物。", staff_type="吏")
    rechain(w, eid, "将御厨副知纳入副知完整时间链。")
    w.commit()


def entry278():
    i, main = 278, F[278]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "押司官", "官职", "北宋东京元额（御厨）",
        "承办御厨事务及点检文字，由手分依法迁补，编制三人",
        main, "御厨吏", "为既有押司官建立御厨语境节点。", officer="吏",
    )
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), post, main,
          "御厨置押司官。", quota=3, staff_type="吏")
    rechain(w, eid, "将御厨押司官纳入完整时间链。")
    w.commit()


def entry279():
    i, main = 279, F[279]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "手分", "官职", "北宋东京元额（御厨）",
        "抄写文书并兼搬物料等杂事，可迁补押司官，位在正名书手之上",
        main, "御厨吏", "为既有手分建立御厨语境节点。", officer="吏",
    )
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), post, main,
          "御厨置手分十四人。", quota=14, staff_type="吏")
    rechain(w, eid, "将御厨手分纳入完整时间链。")
    w.commit()


def entry280():
    i, main = 280, F[280]["text"]
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "书手", "官职", "北宋东京元额（御厨）",
        "御厨抄写吏人，分正名、守阙正名、私名三类，不能递迁为手分",
        main, "御厨吏统称", "建立御厨书手统称及迁转限制。", officer="吏",
    )
    touched.add(generic_eid)
    for title, event in (
        ("正名书手", "御厨正额书手"),
        ("守阙正名书手", "御厨候补书手"),
        ("私名书手", "御厨非正额书手"),
    ):
        eid, post = exact_state(
            w, i, title, "官职", "北宋东京元额（御厨）", event,
            main, "御厨吏", f"建立或补足{title}。", officer="吏",
        )
        relation(w, i, generic, post, "统称与实例", main, f"{title}为御厨书手实例。")
        touched.add(eid)
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), generic, main,
          "书手隶御厨。", staff_type="吏")
    for eid in touched:
        rechain(w, eid, "整理御厨书手统称与三类实例时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(261, 281)] == [
        "判光禄寺事", "光禄寺卿", "光禄寺少卿", "光禄寺丞",
        "光禄寺主簿", "太官令", "府史", "驱使官", "供官", "胥佐",
        "贴书", "御厨", "勾当御厨官", "御厨五局", "监御厨官",
        "拘押官物使臣", "副知", "押司官", "手分", "书手",
    ]
    entry261()
    entry262()
    entry263()
    entry264()
    entry265()
    entry266()
    entry267()
    entry268()
    entry269()
    entry270()
    entry271()
    entry272()
    entry273()
    entry274()
    entry275()
    entry276()
    entry277()
    entry278()
    entry279()
    entry280()


if __name__ == "__main__":
    main()
