#!/usr/bin/env python3
"""提取 chapter5t7 第961-980条：将作监属司与都水监前半。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_941_960 as previous


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


F = {i: load(i) for i in range(961, 981)}
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

node = previous.node
office_staff = previous.office_staff
parent_child = previous.parent_child
evolution = previous.evolution
group_instances = previous.group_instances


TIME_HINTS = {
    "东汉": 100,
    "西晋武帝时": 270,
    "隋仁寿元年": 601,
    "隋炀帝时": 610,
    "北宋建隆元年": 960,
    "北宋建隆中": 963,
    "北宋太平兴国二年": 977,
    "北宋太平兴国二年至景德四年六月": 977.1,
    "北宋太平兴国七年": 982,
    "北宋淳化、至道年间（具体年月未载）": 992,
    "北宋淳化三年": 992.1,
    "北宋淳化五年": 994,
    "北宋景德三年": 1006,
    "北宋景德四年六月": 1007.45,
    "北宋景德四年六月至天圣元年五月十六日前": 1007.46,
    "北宋景德四年七月十三日": 1007.54,
    "北宋大中祥符二年五月三日": 1009.34,
    "北宋大中祥符四年": 1011,
    "北宋天圣元年五月十六日": 1023.37,
    "北宋天圣元年五月十六日以后": 1023.371,
    "北宋天圣四年四月": 1026.29,
    "北宋前期（先后隶属，具体年月未载）": 1040,
    "北宋嘉祐三年十一月二十二日": 1058.89,
    "北宋熙宁二年五月二十八日": 1069.40,
    "北宋熙宁以后（具体年月未载）": 1070,
    "北宋元丰新制": 1080,
    "北宋元丰五年": 1082,
    "北宋元丰八年": 1085,
    "北宋元祐间（具体年月未载）": 1090,
    "宋代（京西河洛抽税竹木务，具体年月未载）": 1050,
    "宋代（事材场，具体年月未载）": 1050.1,
    "宋代（东西退材场，具体年月未载）": 1050.2,
    "宋代（京东抽税竹箔场，具体年月未载）": 1050.3,
    "宋代（东、西窑务，具体年月未载）": 1050.4,
    "宋代（东、西窑务十种工匠，具体年月未载）": 1050.5,
    "南宋建炎三年": 1129,
    "南宋绍兴九年": 1139,
    "南宋绍兴十年": 1140,
    "西汉武帝时": -120,
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


def canonicalize_wheat_bran_yard(w, quotation):
    old = w.find_entity("麦娟场", "机构")
    formal = w.find_entity("麦䴸场", "机构")
    if old is not None:
        assert formal is None or formal == old, (old, formal)
        w.conn.execute(
            "update Entities set title='麦䴸场',quotation=? where id=?",
            (quotation, old),
        )
        w._br(
            "Entities", old,
            "第974条原书正式词头为麦䴸场；将既有OCR误名麦娟场恢复为正式字形。",
        )
        formal = old
    return formal


KILN_WORKERS = (
    "瓦匠", "砖匠", "装窑匠", "火色匠", "粘胶匠",
    "鸟兽匠", "青作匠", "积匠", "牵窑匠", "合药匠",
)


def entry961():
    i, main = 961, F[961]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    time = "北宋景德四年六月至天圣元年五月十六日前"
    _, post, _ = office_staff(
        w, touched, i, "东、西八作司", "勾当东西八作司公事", time,
        main, "景德四年并司后至天圣复分前，勾当官不分东、西。",
        quota=4, staff_type="勾当官", office_event="东、西八作司并为一司",
        post_event="不分东、西，领八作司修造公事，旧监官四员",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理勾当东西八作司公事在并司期的设置、职掌、旧额与简称。")


def _split_workshop_supervisor(i, office, post):
    quote = F[i]["text"]
    w, touched = W(i), set()
    for time, quota, event in (
        ("北宋太平兴国二年至景德四年六月", None, "分司期设置"),
        ("北宋天圣元年五月十六日以后", 3, "复分后设置监官三员"),
    ):
        office_staff(
            w, touched, i, office, post, time, quote,
            f"{post}在东、西八作司分司时期设置。",
            quota=quota, staff_type="勾当官",
            office_event=event,
            post_event="点检修盖官物与文字，签书公事，逐月申报工程",
        )
    finish(w, touched, f"整理{post}两段设置时期、天圣后员额与修造点检职掌。")


def entry962():
    _split_workshop_supervisor(962, "东八作司", "勾当东八作司公事")


def entry963():
    _split_workshop_supervisor(963, "西八作司", "勾当西八作司公事")


def entry964():
    i, main = 964, F[964]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "提点修造司", "机构", "北宋太平兴国七年",
        "始置，监修督促京城营缮及京畿屯兵营舍修葺",
        origin, "京城修造检察机构", "记录提点修造司始置。", "职源与沿革",
        update_event=True,
    )
    node(w, touched, i, "提点修造司", "机构", "北宋淳化三年",
         "分左、右厢", origin, "京城修造检察机构",
         "记录淳化三年分厢。", "职源与沿革", update_event=True)
    merged = node(
        w, touched, i, "提点修造司", "机构", "北宋淳化五年",
        "左、右厢仍合为一所，并设提举官", origin,
        "京城修造检察机构", "记录淳化五年合所。", "职源与沿革",
        update_event=True,
    )
    office_staff(
        w, touched, i, "提点修造司", "提点修造司提点官",
        "北宋太平兴国七年", roster, "提点修造司设提点官。", "编制",
        staff_type="提点官", office_event="始置并设提点官",
        post_event="监修督促京城营缮", officer="内侍或三班使臣充",
    )
    abolished = node(
        w, touched, i, "提点修造司", "机构", "北宋熙宁二年五月二十八日",
        "罢置", origin, "废罢机构", "记录熙宁二年罢置。", "职源与沿革",
        update_event=True,
    )
    cite(w, "Timepoints", start, i, main, "补证提点修造司所在坊位。")
    cite(w, "Timepoints", merged, i, duty, "补证合所后的修造检察职掌。", "职掌")
    cite(w, "Timepoints", abolished, i, duty, "补证罢前职掌范围。", "职掌")
    finish(w, touched, "整理提点修造司太平兴国始置、淳化分合、提点官编制及熙宁罢置。")


def entry965():
    i, quote = 965, F[965]["text"]
    w, touched = W(i), set()
    office = node(
        w, touched, i, "提举修造司", "机构", "北宋淳化三年",
        "始置提举官二员，直隶并监领修造司",
        quote, "京城修造监领机构", "记录提举修造司始置及直隶性质。",
        update_event=True,
    )
    repair = node(
        w, touched, i, "提点修造司", "机构", "北宋淳化三年",
        "受提举修造司监领", quote, "被监领修造机构",
        "复用提点修造司淳化三年节点。",
    )
    relation(w, i, office, repair, "上下级机构", quote,
             "提举修造司监领修造司，职事与提点修造司同。")
    office_staff(
        w, touched, i, "提举修造司", "提举修造司提举官",
        "北宋淳化三年", quote, "提举修造司始置提举官二员。",
        quota=2, staff_type="提举官", office_event="始置提举官二员",
        post_event="以品位较高者监领修造司",
        officer="诸司使副及内侍差充",
    )
    finish(w, touched, "整理提举修造司淳化始置、直隶、两员编制及对修造司的监领。")


def _successive_subordination(w, touched, i, child, quotation):
    for parent in ("三司", "提举在京诸司库务司"):
        parent_child(
            w, touched, i, parent, child,
            "北宋前期（先后隶属，具体年月未载）", quotation,
            f"原文称{child}先后隶{parent}，未载改隶年月。",
            parent_event=f"先后统辖{child}",
            child_event="先后隶三司、提举在京诸司库务司",
        )
    parent_child(
        w, touched, i, "将作监", child, "北宋元丰新制", quotation,
        f"元丰以后{child}隶将作监。",
        parent_event=f"元丰新制统辖{child}", child_event="元丰以后隶将作监",
    )


def entry966():
    i, main = 966, F[966]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "京西河洛抽税竹木务", "机构",
         "北宋淳化、至道年间（具体年月未载）", "已经设置",
         origin, "竹木抽税职局", "记录太宗朝已置。", "职源", update_event=True)
    merged = node(
        w, touched, i, "京西河洛抽税竹木务", "机构", "北宋大中祥符四年",
        "京东西抽税竹木场并入", origin, "竹木抽税职局",
        "记录大中祥符四年并场。", "职源", update_event=True,
    )
    _successive_subordination(w, touched, i, "京西河洛抽税竹木务", main)
    duty_tp = node(
        w, touched, i, "京西河洛抽税竹木务", "机构",
        "宋代（京西河洛抽税竹木务，具体年月未载）",
        "收受水运竹木竹索并抽算诸河商贩竹木，供内外使用",
        duty, "竹木抽税职局", "整理竹木务职掌。", "职掌", update_event=True,
    )
    office_staff(
        w, touched, i, "京西河洛抽税竹木务", "勾当京西竹木务公事",
        "宋代（京西河洛抽税竹木务，具体年月未载）", roster,
        "竹木务设勾当官一人。", "编制", quota=1, staff_type="勾当官",
        office_event="设置勾当官", post_event="监领竹木务公事，编制一人",
        officer="京朝官或阁门祗候充",
    )
    cite(w, "Timepoints", merged, i, duty, "补证并场后职掌。", "职掌")
    alias_note(w, i, duty_tp, aliases, "简称")
    finish(w, touched, "整理京西河洛抽税竹木务太宗朝始见、祥符并场、先后改隶、职掌编制与简称。")


def entry967():
    i, main = 967, F[967]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "京西河洛抽税竹木务", "勾当京西竹木务公事",
        "宋代（京西河洛抽税竹木务，具体年月未载）", main,
        "勾当京西竹木务公事一人，掌监领竹木务。", quota=1,
        staff_type="勾当官", office_event="设置勾当官",
        post_event="掌监领竹木务公事，编制一人",
        officer="京朝官或阁门祗候充",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理恢复后的勾当京西竹木务公事正式词头、员额、差充、职掌与简称。")


def entry968():
    i, main = 968, F[968]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "事材场", "机构", "北宋太平兴国七年",
        "创置，计度并初步加工修缮木料", origin,
        "营造木料加工职局", "记录事材场创置。", "职源", update_event=True,
    )
    _successive_subordination(w, touched, i, "事材场", main)
    duty_tp = node(
        w, touched, i, "事材场", "机构", "宋代（事材场，具体年月未载）",
        "计度、砍截木料后供八作司等内外诸司修缮",
        duty, "营造木料加工职局", "整理事材场职掌。", "职掌", update_event=True,
    )
    for post, quota, kind, event in (
        ("勾当事材场公事", 4, "勾当官", "监领事材场公事"),
        ("事材场工匠", 1653, "工匠", "分三等加工营造木料"),
        ("事材场杂役", 304, "杂役", "承担场内杂役"),
    ):
        office_staff(
            w, touched, i, "事材场", post, "宋代（事材场，具体年月未载）",
            roster, f"事材场置{post}{quota}人。", "编制", quota=quota,
            staff_type=kind, office_event="设置勾当官、工匠与杂役",
            post_event=event, officer=kind,
        )
    evolution(
        w, touched, i, "西造船务打造舟船人匠", "事材场工匠",
        "北宋天圣四年四月", roster, "天圣四年西造船务打造舟船人匠并入事材场。",
        "编制", source_type="官职", target_type="官职",
        source_event="并入事材场工匠", target_event="接收西造船务打造舟船人匠",
    )
    cite(w, "Timepoints", start, i, main, "补证事材场地点及先后隶属。")
    cite(w, "Timepoints", duty_tp, i, roster, "补证事材场人员编制。", "编制")
    finish(w, touched, "整理事材场创置、改隶、木料职掌、官匠杂役编制及造船人匠并入。")


def entry969():
    i, quote = 969, F[969]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "事材场", "勾当事材场公事",
        "宋代（事材场，具体年月未载）", quote,
        "勾当事材场公事四人，掌监领本场。", quota=4,
        staff_type="勾当官", office_event="设置勾当官四人",
        post_event="掌监领事材场公事，编制四人",
        officer="诸司使副、阁门祗候及内侍充",
    )
    finish(w, touched, "整理勾当事材场公事四人员额、监领职掌与差充来源。")


def entry970():
    i, main = 970, F[970]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "东西退材场", "机构", "北宋太平兴国七年",
        "创置，收授京城内外废退材木", origin,
        "退材收储职局", "记录东西退材场创置。", "职源与沿革", update_event=True,
    )
    node(w, touched, i, "东西退材场", "机构", "北宋景德三年",
         "省监官，改由事材场监官兼领", origin, "退材收储职局",
         "记录景德三年省监官。", "职源与沿革", update_event=True)
    evolution(
        w, touched, i, "东西退材场", "东、西退材场",
        "北宋熙宁以后（具体年月未载）", origin,
        "熙宁以后东西退材场称东、西退材场。", "职源与沿革",
        source_event="改称东、西退材场", target_event="由东西退材场改称",
    )
    _successive_subordination(w, touched, i, "东西退材场", main)
    duty_tp = node(
        w, touched, i, "东西退材场", "机构",
        "宋代（东西退材场，具体年月未载）",
        "分类收储废退材木，供营建、杂器与烧柴",
        duty, "退材收储职局", "整理东西退材场职掌。", "职掌", update_event=True,
    )
    office_staff(
        w, touched, i, "东西退材场", "东西退材场监官",
        "宋代（东西退材场，具体年月未载）", roster,
        "东西退材场监官一人。", "编制", quota=1, staff_type="监官",
        office_event="设置监官", post_event="监领退材场，编制一人",
    )
    cite(w, "Timepoints", start, i, main, "补证东西退材场职局性质与改隶。")
    alias_note(w, i, duty_tp, aliases, "简称")
    finish(w, touched, "整理东西退材场创置、省监官、熙宁改称、先后隶属、职掌编制与简称。")


def entry971():
    i, main = 971, F[971]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "京东抽税竹箔场", "机构", "北宋建隆元年",
        "创置，抽算竹木蒲席芦苇苇箔", origin,
        "竹箔抽税职局", "记录京东抽税竹箔场创置。", "职源", update_event=True,
    )
    parent_child(
        w, touched, i, "将作监", "京东抽税竹箔场", "北宋元丰新制",
        main, "元丰以后京东抽税竹箔场隶将作监。",
        parent_event="元丰新制统辖京东抽税竹箔场",
        child_event="元丰以后隶将作监，在崇善坊",
    )
    duty_tp = node(
        w, touched, i, "京东抽税竹箔场", "机构",
        "宋代（京东抽税竹箔场，具体年月未载）",
        "抽算竹木、蒲席、芦苇、苇箔，供内外苇箔",
        duty, "竹箔抽税职局", "整理竹箔场职掌。", "职掌", update_event=True,
    )
    office_staff(
        w, touched, i, "京东抽税竹箔场", "监京东抽税竹箔场",
        "宋代（京东抽税竹箔场，具体年月未载）", roster,
        "京东抽税竹箔场置监官二人。", "编制", quota=2,
        staff_type="监官", office_event="设置监官二人",
        post_event="监领抽税竹箔场，编制二人",
    )
    cite(w, "Timepoints", start, i, main, "补证正式类别为职局及所在坊位。")
    alias_note(w, i, duty_tp, aliases, "简称与别名")
    finish(w, touched, "整理京东抽税竹箔场建隆创置、将作监隶属、职掌、监官编制与别名。")


def entry972():
    i, quote = 972, F[972]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "京东抽税竹箔场", "监京东抽税竹箔场",
        "宋代（京东抽税竹箔场，具体年月未载）", quote,
        "监京东抽税竹箔场掌监领本场。", staff_type="监官",
        office_event="设置监官", post_event="掌监领抽税竹箔场公事",
        officer="京朝官、三班使臣或内侍充",
    )
    finish(w, touched, "整理监京东抽税竹箔场监领职掌与京朝官、使臣、内侍差充。")


def entry973():
    i, main = 973, F[973]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "甄官", "机构", "东汉",
         "掌造砖瓦，为窑务职事之始", origin, "前代窑务源流",
         "记录东汉甄官职事源流，不据此强建机构演变关系。", "职源与沿革",
         update_event=True)
    node(w, touched, i, "东、西窑务", "机构", "北宋建隆中",
         "已置东、西二窑务", origin, "砖瓦陶器制造职局统称",
         "记录建隆中已置二窑务。", "职源与沿革", update_event=True)
    node(w, touched, i, "东、西窑务", "机构", "北宋景德四年七月十三日",
         "废东、西窑务", origin, "废罢职局",
         "记录景德四年废罢。", "职源与沿革", update_event=True)
    group = group_instances(
        w, touched, i, "东、西窑务", "机构", "北宋大中祥符二年五月三日",
        "复置东窑务，并以京西受纳场改为西窑务",
        ("东窑务", "西窑务"), origin,
        "东、西窑务是东窑务与西窑务的合称。", "职源与沿革",
    )
    evolution(
        w, touched, i, "京西受纳场", "西窑务",
        "北宋大中祥符二年五月三日", origin,
        "大中祥符二年京西受纳场改为西窑务。", "职源与沿革",
        source_event="改为西窑务", target_event="由京西受纳场改置",
    )
    _successive_subordination(w, touched, i, "东、西窑务", main)
    duty_tp = node(
        w, touched, i, "东、西窑务", "机构",
        "宋代（东、西窑务，具体年月未载）",
        "炼土制砖瓦及瓶罐器皿，供营建与日用",
        duty, "砖瓦陶器制造职局统称", "整理东、西窑务职掌。", "职掌",
        update_event=True,
    )
    office_staff(
        w, touched, i, "东、西窑务", "东、西窑务监官",
        "宋代（东、西窑务，具体年月未载）", roster,
        "东、西窑务设监官三人。", "编制", quota=3,
        staff_type="监官", office_event="设置监官与工匠",
        post_event="监领窑务，编制三人",
    )
    workers = group_instances(
        w, touched, i, "东、西窑务十种工匠", "官职",
        "宋代（东、西窑务十种工匠，具体年月未载）",
        "东、西窑务一千二百名工匠所分十种", KILN_WORKERS,
        roster, "原文逐一列明窑务十种工匠。", "编制",
    )
    staff(w, i, duty_tp, workers, roster,
          "东、西窑务工匠一千二百人，分为十种。", "编制",
          quota=1200, staff_type="工匠")
    cite(w, "Timepoints", group, i, main, "补证东、西窑务先后隶属。")
    alias_note(w, i, duty_tp, aliases, "简称")
    finish(w, touched, "整理东、西窑务前代源流、建隆始见、景德罢祥符复、改隶、职掌及十类工匠。")


def entry974():
    i, quote = 974, F[974]["text"]
    w, touched = W(i), set()
    eid = canonicalize_wheat_bran_yard(w, quote)
    if eid is not None:
        touched.add(eid)
    parent_child(
        w, touched, i, "将作监", "麦䴸场", "北宋元丰新制", quote,
        "元丰以后麦䴸场隶将作监。", parent_event="元丰新制统辖麦䴸场",
        child_event="元丰以后隶将作监，在嘉庆坊，收夏租麦䴸供营建",
    )
    finish(w, touched, "恢复麦䴸场正式词头并整理将作监隶属、地点及营建材料职掌。")


def entry975():
    i, quote = 975, F[975]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "将作监", "丹粉所", "北宋元丰新制", quote,
        "元丰改制后丹粉所隶将作监。", parent_event="元丰新制统辖丹粉所",
        child_event="隶将作监，烧制变丹粉供图绘装饰",
    )
    office_staff(
        w, touched, i, "丹粉所", "丹粉所监官", "北宋元丰新制", quote,
        "丹粉所置监官一人，由内侍充。", quota=1, staff_type="监官",
        office_event="设置监官一人", post_event="监领丹粉所，编制一人",
        officer="内侍充",
    )
    finish(w, touched, "整理丹粉所元丰后将作监隶属、烧制职掌与内侍监官编制。")


def entry976():
    i, main = 976, F[976]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "都水监", "机构", "西晋武帝时",
         "水衡改为都水台", origin, "前代水利机构源流",
         "记录西晋都水台源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "都水监", "机构", "隋仁寿元年",
         "始置都水监", origin, "前代水利机构源流",
         "记录隋仁寿元年始置。", "职源与沿革", update_event=True)
    source, start = evolution(
        w, touched, i, "三司河渠司", "都水监",
        "北宋嘉祐三年十一月二十二日", origin,
        "嘉祐三年罢三司河渠司，初置都水监。", "职源与沿革",
        source_event="罢置，职事由都水监承接",
        target_event="初置，承接三司河渠司职事",
    )
    cite(w, "Timepoints", start, i, duty, "补证都水监内外河渠、桥梁、堤堰、渡口职掌。", "职掌")
    for post, quota, kind, event in (
        ("判都水监事", 1, "判监官", "领都水监公事"),
        ("同判都水监事", 1, "同判监官", "佐判监领都水监公事"),
        ("知都水监丞公事", 2, "知丞事", "参领监事并轮一员出外治河"),
        ("知都水监主簿公事", 1, "知主簿事", "掌都水监簿书"),
    ):
        office_staff(
            w, touched, i, "都水监", post,
            "北宋嘉祐三年十一月二十二日", roster,
            f"嘉祐初置都水监时置{post}{quota}人。", "编制",
            quota=quota, staff_type=kind, office_event="嘉祐初置并设判监、丞、主簿",
            post_event=event,
        )
    parent_child(
        w, touched, i, "都水监", "外都水监丞司",
        "北宋嘉祐三年十一月二十二日", roster,
        "嘉祐初轮监丞一员在外治河，置外都水监丞司。", "编制",
        parent_event="设置外都水监丞司",
        child_event="监丞一员轮外治河的办事机构",
    )
    office_staff(
        w, touched, i, "外都水监丞司", "知都水监丞公事",
        "北宋嘉祐三年十一月二十二日", roster,
        "知都水监丞公事二人中轮一员在外治河。", "编制",
        quota=1, staff_type="外治河监丞", office_event="置局于外治河",
        post_event="轮一员出外治河",
    )
    reform = node(
        w, touched, i, "都水监", "机构", "北宋元丰新制",
        "元丰正名，置使者、丞、主簿及南北外丞",
        roster, "中央水利机构", "整理元丰正名编制。", "编制", update_event=True,
    )
    for post, quota, kind in (
        ("都水监使者", 1, "长官"), ("都水监丞", 2, "属官"),
        ("都水监主簿", 1, "属官"), ("南外都水监丞", 1, "外丞"),
        ("北外都水监丞", 1, "外丞"),
    ):
        office_staff(
            w, touched, i, "都水监", post, "北宋元丰新制", roster,
            f"元丰正名都水监置{post}{quota}人。", "编制", quota=quota,
            staff_type=kind, office_event="元丰正名设置使者、丞、主簿及南北外丞",
            post_event=f"都水监{kind}，编制{quota}人",
        )
    parent_child(
        w, touched, i, "都水监", "提举汴河堤岸司", "北宋元丰八年",
        roster, "元丰八年提举汴河堤岸司归隶都水监。", "编制",
        parent_event="接收提举汴河堤岸司",
        child_event="归隶都水监",
    )
    for post, quota, kind in (
        ("外都水使者", 1, "外使者"),
        ("勾当都水监公事", 1, "勾当官"),
        ("都水监都提举官", 8, "都提举官"),
        ("都水监监埽官", 35, "监埽官"),
    ):
        office_staff(
            w, touched, i, "都水监", post,
            "北宋元祐间（具体年月未载）", roster,
            f"元祐间及其后都水监置{post}{quota}人。", "编制", quota=quota,
            staff_type=kind, office_event="增置外使者、勾当及治河提举监埽官",
            post_event=f"参与治河事务，编制{quota}人",
        )
    parent_child(
        w, touched, i, "都水监", "街道司", "北宋元丰新制", roster,
        "都水监所隶官司包括街道司。", "编制",
        parent_event="统辖街道司及堤堰渡口",
        child_event="列为都水监所隶官司",
    )
    office_staff(
        w, touched, i, "都水监", "都水监使者", "南宋建炎三年", roster,
        "建炎三年都水监置使者一员。", "编制", quota=1,
        staff_type="长官", office_event="南宋水官裁减，仅置使者",
        post_event="建炎三年置一员",
    )
    for post in ("南外都水监丞", "北外都水监丞"):
        office_staff(
            w, touched, i, "都水监", post, "南宋绍兴九年", roster,
            f"绍兴九年置{post}一员。", "编制", quota=1,
            staff_type="外丞", office_event="议和归河南地后置南北外丞",
            post_event="绍兴九年置一员",
        )
    abolished = node(
        w, touched, i, "都水监", "机构", "南宋绍兴十年",
        "罢置", origin, "废罢机构", "记录绍兴十年罢都水监。", "职源与沿革",
        update_event=True,
    )
    cite(w, "Timepoints", reform, i, duty, "补证元丰后都水监水利职掌。", "职掌")
    cite(w, "Timepoints", abolished, i, roster, "补证南宋水官裁减及绍兴十年罢置。", "编制")
    alias_note(w, i, reform, aliases, "简称")
    assert source
    finish(w, touched, "补全都水监西晋隋源流、嘉祐创置、元丰正名编制、元祐增官及南宋裁减罢置。")


def entry977():
    i, main = 977, F[977]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "都水监", "判都水监事",
        "北宋嘉祐三年十一月二十二日", origin,
        "嘉祐三年始置判都水监事一人。", "职源与沿革", quota=1,
        staff_type="判监官", office_event="初置都水监并设判监事",
        post_event="领内外河渠、堤堰、渡口等都水监公事",
        officer="初以侍御史知杂事，后以员外郎以上充",
    )
    cite(w, "Timepoints", post, i, duty, "补证判都水监事职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证判都水监事差充品位。", "品位")
    cite(w, "Timepoints", post, i, roster, "补证编制一人。", "编制")
    node(w, touched, i, "判都水监事", "官职", "北宋元丰五年",
         "新官制行，罢置", origin, "废罢差遣",
         "记录元丰五年罢判都水监事。", "职源与沿革", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理判都水监事嘉祐始置、员额、职掌、差充、简称及元丰罢置。")


def entry978():
    i, main = 978, F[978]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "都水监", "同判都水监事",
        "北宋嘉祐三年十一月二十二日", main,
        "嘉祐初置都水监时，同判都水监事一人。", quota=1,
        staff_type="同判监官", office_event="初置判监官二员",
        post_event="判监官中资序稍浅者带同字", officer="朝官以上充",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理同判都水监事嘉祐始置、一员编制、资序与简称。")


def entry979():
    i, main = 979, F[979]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "都水监使者", "官职", "西汉武帝时",
         "水衡都尉属官有左、右都水使者", origin, "前代水官源流",
         "记录西汉源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "都水监使者", "官职", "隋炀帝时",
         "始置都水监使者", origin, "前代水官源流",
         "记录隋代始置。", "职源与沿革", update_event=True)
    _, reform, _ = office_staff(
        w, touched, i, "都水监", "都水监使者", "北宋元丰五年",
        origin, "元丰五年始设都水监使者一人。", "职源与沿革",
        quota=1, staff_type="长官", office_event="元丰新制设置使者",
        post_event="都水监长官，领水利疏凿浚治", grade="正六品",
    )
    cite(w, "Timepoints", reform, i, duty, "补证都水监使者长官职掌。", "职掌")
    cite(w, "Timepoints", reform, i, rank, "补证正六品及班位。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补证编制一人。", "编制")
    node(w, touched, i, "都水监使者", "官职", "南宋绍兴十年",
         "随都水监罢置", origin, "废罢官职",
         "记录绍兴十年罢置。", "职源与沿革", update_event=True)
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "整理都水监使者汉隋源流、元丰职事官长官、品位编制、简称及绍兴罢置。")


def entry980():
    i, main = 980, F[980]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "都水监", "知都水监丞公事",
        "北宋嘉祐三年十一月二十二日", origin,
        "嘉祐三年始置知都水监丞公事二人。", "职源与沿革",
        quota=2, staff_type="知丞事", office_event="初置并设知监丞事",
        post_event="参领监事，轮一员出外治河", officer="朝官充",
    )
    cite(w, "Timepoints", post, i, duty, "补证参领及轮外治河职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证以朝官充。", "品位")
    cite(w, "Timepoints", post, i, roster, "补证编制二人。", "编制")
    evolution(
        w, touched, i, "知都水监丞公事", "都水监丞", "北宋元丰五年",
        origin, "元丰新制知都水监丞公事正名为都水监丞。", "职源与沿革",
        source_type="官职", target_type="官职",
        source_event="正名为都水监丞", target_event="由知都水监丞公事正名",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理知都水监丞公事嘉祐始置、两人员额、轮外治河、差充简称及元丰正名。")


def main():
    order = [974, *range(961, 974), 975, *range(976, 981)]
    for i in order:
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
