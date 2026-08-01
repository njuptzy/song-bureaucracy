#!/usr/bin/env python3
"""提取 chapter5t7 第601-620条：南宋排岸、司农属局与太府寺。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_581_600 as previous


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


F = {i: load(i) for i in range(601, 621)}
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
    "南朝梁": 502, "北魏": 386, "北齐": 550,
    "宋初": 960, "宋前期": 980,
    "宋代（京师船搬仓）": 1020,
    "宋代（都曲院）": 1020.1,
    "北宋（熙宁三年前已置）": 1069,
    "北宋熙宁三年": 1070,
    "北宋熙宁三年十二月六日": 1070.93,
    "北宋（元丰改制前）": 1075,
    "北宋元丰新制": 1082.1,
    "北宋元符元年七月": 1098.55,
    "北宋崇宁间": 1103,
    "北宋宣和三年十一月": 1121.88,
    "北宋政和间": 1115,
    "南宋": 1127, "南宋绍兴元年五月二十三日": 1131.39,
    "南宋绍兴三年": 1133, "南宋绍兴三年十二月九日": 1133.95,
    "南宋绍兴四年五月二十六日": 1134.38,
    "南宋绍兴十年正月二十九日": 1140.08,
    "南宋绍兴十一年正月": 1141.04,
    "南宋绍兴末至隆兴初": 1162,
    "南宋隆兴元年七月二十六日": 1163.56,
    "南宋隆兴二年闰十一月二十七日": 1164.94,
    "南宋（行在排岸司阶段）": 1135,
    "南宋（司农寺排岸司阶段）": 1140,
    "南宋（司农寺排岸司官吏）": 1140.1,
    "南宋（临安府排岸司监追）": 1133.1,
    "南宋建炎三年四月十三日": 1129.28,
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


def entry601():
    i, main, aliases = 601, F[601]["text"], field(601, "简称与别名")
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, "临安府排岸司", "机构", "南宋绍兴三年",
        "设文官一员、手分一名，掌行在水运纲船下卸与检察",
        aliases, "南宋排岸机构", "建立临安府排岸司节点。", "简称与别名",
    )
    middle_eid, middle = exact_state(
        w, i, "行在排岸司", "机构", "南宋（行在排岸司阶段）",
        "由临安府排岸司改名，专掌行在排岸事务",
        main, "南宋排岸机构", "建立行在排岸司改名节点。",
    )
    relation(w, i, old, middle, "前后演变", main,
             "临安府排岸司改名行在排岸司。")
    for title, officer, unit, event in (
        ("临安府排岸司文官", "文官", "员", "绍兴三年临安府排岸司添文官一员"),
        ("手分", "吏", "名", "绍兴三年临安府排岸司添手分一名"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "南宋绍兴三年", event,
            aliases, "临安府排岸司官吏", f"建立临安府排岸司{officer}定额。",
            "简称与别名", officer=officer,
        )
        staff(w, i, old, post, aliases, f"绍兴三年临安府排岸司添{title}一{unit}。",
              "简称与别名", quota=1, staff_type=officer)
        touched.add(seid)
    eid, office = exact_state(
        w, i, "司农寺排岸司", "机构", "南宋（司农寺排岸司阶段）",
        "由行在排岸司改称，设于临安前洋街，掌拘押、下卸上供粮斛并检察已卸纲船",
        main, "司农寺所属监当局", "建立司农寺排岸司改称、位置与职掌节点。",
    )
    relation(w, i, middle, office, "前后演变", main,
             "行在排岸司改称司农寺排岸司。")
    relation(w, i, tp(w, "司农寺", "机构", "南宋"), office,
             "上下级机构", main, "司农寺排岸司隶司农寺。")
    roles = (
        ("监官", "监官", 1, "监官一人，主管排岸司"),
        ("手分", "吏", None, "排岸司吏额手分"),
        ("前行", "吏", None, "司农寺排岸司置前行一名"),
        ("下卸兵士", "兵士", 170, "下辖下卸兵士一百七十余人"),
    )
    for title, officer, quota, event in roles:
        seid, post = exact_state(
            w, i, title, "官职", "南宋（司农寺排岸司官吏）",
            event, main, "司农寺排岸司官吏",
            f"建立司农寺排岸司{title}编制。", officer=officer,
        )
        staff(w, i, office, post, main, f"司农寺排岸司置{title}。",
              quota=quota, staff_type=officer)
        touched.add(seid)
    prison_eid, prison = exact_state(
        w, i, "司农寺排岸司监狱", "机构", "南宋（司农寺排岸司阶段）",
        "司农寺排岸司所设监狱", main, "监当局属狱",
        "建立司农寺排岸司所属监狱。",
    )
    relation(w, i, office, prison, "上下级机构", main,
             "司农寺排岸司设置监狱。")
    alias_note(w, i, office, aliases, "简称与别名")
    touched.update((old_eid, middle_eid, eid, prison_eid))
    finish(w, touched, "整理南宋排岸司两次改名、职掌、隶属与编制时间链。")


def entry602():
    i, main = 602, F[602]["text"]
    w, touched = W(i), set()
    parent_eid, parent = exact_state(
        w, i, "京师船搬仓", "机构", "宋代（京师船搬仓）",
        "设置所由，负责纲船下卸至入仓间巡防",
        main, "京师仓储机构", "建立船搬仓所属吏额承载节点。",
    )
    eid, post = exact_state(
        w, i, "所由", "官职", "宋代（京师船搬仓）",
        "巡防纲船下卸钱物至入仓过程中的滋事与偷盗",
        main, "船搬仓公人", "建立所由职掌节点。", officer="公人",
    )
    staff(w, i, parent, post, main, "京师船搬仓吏额内置所由。", staff_type="公人")
    touched.update((parent_eid, eid))
    finish(w, touched, "整理所由职掌与船搬仓隶属时间链。")


def entry603():
    i, main = 603, F[603]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "前行", "官职", "南宋（司农寺排岸司官吏）",
        "司农寺排岸司置前行一名",
        main, "司农寺排岸司吏员", "规范排岸司前行职掌与定额。", officer="吏",
    )
    staff(w, i, tp(w, "司农寺排岸司", "机构", "南宋（司农寺排岸司阶段）"),
          post, main, "司农寺排岸司置前行一名。", quota=1, staff_type="吏")
    finish(w, {eid}, "整理司农寺排岸司前行职掌与定额时间链。")


def entry604():
    i, main = 604, F[604]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "排岸兼管船场公事", "官职", "北宋政和间",
        "两浙路杭州、镇江府、常州、秀州、湖州、平江府各置，掌水运纲船并整葺舟船",
        main, "排岸船场职事官", "建立排岸兼管船场公事设置范围与职掌。",
        officer="职事官",
    )
    finish(w, {eid}, "整理排岸兼管船场公事设置范围与职掌时间链。")


def entry605():
    i, main = 605, F[605]["text"]
    w, touched = W(i), set()
    eid, early = exact_state(
        w, i, "下卸司", "机构", "北宋（熙宁三年前已置）",
        "掌领装卸五指挥兵士，供诸排岸司下卸纲运",
        main, "监当局", "建立下卸司早期职掌节点。",
    )
    _, expanded = exact_state(
        w, i, "下卸司", "机构", "北宋熙宁三年十二月六日",
        "增掌诸仓斗子三百九十人，按名次差拨各仓支纳粮斛",
        main, "监当局", "建立熙宁三年增掌斗子节点。",
    )
    soldier_eid, soldiers = exact_state(
        w, i, "下卸兵士", "官职", "北宋（熙宁三年前已置）",
        "隶下卸司五指挥，供诸排岸司等下卸纲运粮斛",
        main, "下卸司兵士", "建立下卸司五指挥兵士。", officer="兵士",
    )
    staff(w, i, early, soldiers, main, "下卸司掌领装卸五指挥兵士。",
          staff_type="兵士")
    porter_eid, porters = exact_state(
        w, i, "斗子", "官职", "北宋熙宁三年十二月六日",
        "由下卸司按名次差拨各仓，供支纳粮斛，编制三百九十人",
        main, "下卸司仓场吏役", "建立下卸司斗子定额。", officer="吏役",
    )
    staff(w, i, expanded, porters, main, "下卸司掌诸仓斗子三百九十人。",
          quota=390, staff_type="斗子")
    _, reform = exact_state(
        w, i, "下卸司", "机构", "北宋元丰新制",
        "隶司农寺，掌装卸兵士及诸仓斗子差拨",
        main, "司农寺所属监当局", "规范元丰新制后隶属与职掌。",
    )
    relation(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "元丰新制后下卸司隶司农寺。")
    touched.update((eid, soldier_eid, porter_eid))
    finish(w, touched, "整理下卸司职掌、兵士、斗子与元丰隶属时间链。")


def entry606():
    i, main = 606, F[606]["text"]
    w = W(i)
    eid, soldiers = exact_state(
        w, i, "下卸兵士", "官职", "北宋（熙宁三年前已置）",
        "隶下卸司五指挥，供诸排岸司等下卸纲运粮斛",
        main, "下卸司兵士", "规范下卸兵士隶属与职掌。", officer="兵士",
    )
    staff(w, i, tp(w, "下卸司", "机构", "北宋（熙宁三年前已置）"), soldiers,
          main, "下卸兵士五指挥隶下卸司。", staff_type="兵士")
    finish(w, {eid}, "整理下卸兵士隶属与职掌时间链。")


def entry607():
    i, main = 607, F[607]["text"]
    w, touched = W(i), set()
    eid, group = exact_state(
        w, i, "散从官", "官职", "北宋熙宁三年",
        "承符直、人力当直、散从直的统称，差税户或坊郭有行止人充，追催公事",
        main, "州府役吏统称", "建立熙宁三年散从官统称及职掌。", officer="公人",
    )
    for title in ("承符直", "人力当直", "散从直"):
        seid, instance = exact_state(
            w, i, title, "官职", "北宋熙宁三年",
            "熙宁三年统一称为散从官，追催公事",
            main, "州府役吏", f"建立{title}为散从官实例。", officer="役人",
        )
        relation(w, i, group, instance, "统称与实例", main,
                 f"{title}是熙宁三年统称散从官的具体实例。")
        touched.add(seid)
    _, south = exact_state(
        w, i, "散从官", "官职", "南宋（临安府排岸司监追）",
        "临安府排岸司纲运短欠时，由临安府拨散从官监追",
        main, "临安府役吏", "建立绍兴三年排岸司监追实例。", officer="公人",
    )
    staff(w, i, tp(w, "临安府排岸司", "机构", "南宋绍兴三年"), south,
          main, "临安府排岸司纲运有少欠时拨散从官监追。",
          staff_type="临时监追公人")
    touched.add(eid)
    finish(w, touched, "整理散从官统称、实例、职掌及南宋监追时间链。")


def agriculture_suboffice(i, title, duty, *, alias_field=None):
    main = F[i]["text"]
    aliases = field(i, alias_field) if alias_field else None
    w, touched = W(i), set()
    eid, early = exact_state(
        w, i, title, "机构", "北宋（元丰改制前）",
        f"隶都大提举在京诸司库务司，{duty}",
        main, "在京库务监当局", f"建立{title}元丰前职掌与隶属节点。",
    )
    relation(w, i, tp(w, "都大提举在京诸司库务司", "机构", "宋前期"), early,
             "上下级机构", main, f"{title}先隶都大提举在京诸司库务司。")
    _, reform = exact_state(
        w, i, title, "机构", "北宋元丰新制",
        f"改隶司农寺，{duty}", main, "司农寺所属监当局",
        f"规范{title}元丰新制后隶属与职掌。",
    )
    relation(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, f"{title}后隶司农寺。")
    if aliases:
        alias_note(w, i, early, aliases, alias_field)
    touched.add(eid)
    return w, touched, early, reform


def entry608():
    i, main, aliases = 608, F[608]["text"], field(608, "简称")
    w, touched, early, reform = agriculture_suboffice(
        i, "都曲院", "设于开封敦义坊，掌造曲供内酒库酿酒及市上出售",
        alias_field="简称",
    )
    monitor_eid, monitor = exact_state(
        w, i, "都曲院监官", "官职", "北宋（元丰改制前）",
        "由京朝官、诸司使副或内侍充，编制二人",
        main, "都曲院监当官", "建立都曲院监官资格与定额。", officer="监官",
    )
    staff(w, i, early, monitor, main, "都曲院置监官二人。",
          quota=2, staff_type="监官")
    soldier_eid, soldiers = exact_state(
        w, i, "都曲院供役兵士", "官职", "北宋（元丰改制前）",
        "供都曲院造曲等役，编制四百二十八人",
        main, "都曲院役卒", "建立都曲院供役兵士定额。", officer="兵士",
    )
    staff(w, i, early, soldiers, main, "都曲院辖供役兵士四百二十八人。",
          quota=428, staff_type="兵士")
    touched.update((monitor_eid, soldier_eid))
    finish(w, touched, "整理都曲院隶属、职掌、监官、兵士及简称时间链。")


def entry609():
    i, main = 609, F[609]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "小博士", "官职", "宋代（都曲院）",
        "沽卖官酒的酒户，欠官府酒钱时许都曲院催理",
        main, "官酒承销酒户", "建立小博士身份及都曲院催理关系说明。", officer="酒户",
    )
    finish(w, {eid}, "整理小博士官酒承销身份与都曲院催理事实时间链。")


def entry610():
    assert F[610]["text"] == ""
    assert F[610]["fields"].get("_placeholder") is True


def entry611():
    i, main = 611, F[611]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "杂职", "官职", "宋代（都曲院）",
        "由排岸司抽差，供都曲院听差使唤、追催公事，三周年役满归农",
        main, "都曲院公人", "建立都曲院杂职来源、职掌与役期。", officer="公人",
    )
    staff(w, i, tp(w, "都曲院", "机构", "北宋（元丰改制前）"), post,
          main, "都曲院杂职由排岸司抽差。", staff_type="公人")
    finish(w, {eid}, "整理都曲院杂职抽差来源、职掌与役期时间链。")


def entry612():
    w, touched, early, reform = agriculture_suboffice(
        612, "内柴炭库", "储备薪柴、木炭，供应宫中并赐宿卫禁军诸班值",
    )
    finish(w, touched, "整理内柴炭库先后隶属与职掌时间链。")


def entry613():
    w, touched, early, reform = agriculture_suboffice(
        613, "炭场", "储备木炭，供在京百司使用",
    )
    finish(w, touched, "整理炭场先后隶属与职掌时间链。")


def entry614():
    i, main = 614, F[614]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    eid, origin = exact_state(
        w, i, "太府寺", "机构", "北齐", "太府寺之名始见",
        history, "九寺之一", "建立太府寺名称源流。", "职源与沿革",
    )
    _, early = exact_state(
        w, i, "太府寺", "机构", "宋前期",
        "库藏贸易、贡赋俸给归三司，仅掌祠祭用香币帨巾、神位席及标准度量衡器具",
        duty, "闲散寺监机构", "规范宋前期职掌。", "职掌",
    )
    _, reform = exact_state(
        w, i, "太府寺", "机构", "北宋元丰新制",
        "依新官制掌库藏、出纳、商税、度量、市易、平准、店宅等事",
        duty, "财货出纳主管机构", "规范元丰新制职掌。", "职掌",
    )
    _, abolished = exact_state(
        w, i, "太府寺", "机构", "南宋建炎三年四月十三日",
        "罢置，职事并入户部金部司", history, "九寺之一",
        "建立建炎三年罢置节点。", "职源与沿革",
    )
    finance_eid, finance = exact_state(
        w, i, "金部司", "机构", "南宋建炎三年四月十三日",
        "接收罢置太府寺职事", history, "户部所属司",
        "建立金部司接收太府寺职事节点。", "职源与沿革",
    )
    relation(w, i, abolished, finance, "前后演变", history,
             "建炎三年太府寺罢并于户部金部司。", "职源与沿革")
    _, restored = exact_state(
        w, i, "太府寺", "机构", "南宋绍兴元年五月二十三日", "复置",
        history, "九寺之一", "建立绍兴元年复置节点。", "职源与沿革",
    )
    alias_note(w, i, early, aliases, "简称与别名")
    touched.update((eid, finance_eid))

    early_roles = (
        ("判太府寺事", "判寺官", 1),
        ("同判太府寺事", "同判寺官", 1),
        ("太府寺府史", "府史", 3),
        ("太府寺驱使官", "驱使官", 1),
        ("太府寺后行", "后行", 2),
        ("监斗秤务官", "监当官", 2),
        ("法物都知", "都知", 2),
    )
    for title, officer, quota in early_roles:
        event = (
            "以带职朝官或两制官充，领本府寺"
            if title == "判太府寺事"
            else f"太府寺宋前期所置{officer}，编制{quota}人"
        )
        seid, post = exact_state(
            w, i, title, "官职", "宋前期",
            event,
            roster, "太府寺官吏", f"建立{title}宋前期定额。", "编制",
            officer=officer,
        )
        staff(w, i, early, post, roster, f"太府寺宋前期置{officer}{quota}人。",
              "编制", quota=quota, staff_type=officer)
        touched.add(seid)

    reform_specs = (
        ("太府寺卿", "卿", 1,
         "掌国家财货政令，总领库藏出纳、贸易、平准、店宅等事，编制一人"),
        ("太府寺少卿", "少卿", 1,
         "佐正卿领本寺事，元丰新制编制一人"),
        ("太府寺丞", "丞", 2,
         "参领太府寺事并专掌书押交引库钞引，元丰新制定员二人"),
        ("太府寺主簿", "主簿", 2,
         "勾考本寺簿书；元丰新制定额异载（二员／一员）"),
    )
    for title, officer, quota, event in reform_specs:
        seid, post = exact_state(
            w, i, title, "官职", "北宋元丰新制", event,
            roster, "太府寺属官", f"建立{title}元丰新制定额。", "编制",
            officer=officer,
        )
        staff(w, i, reform, post, roster, f"元丰新制太府寺置{officer}{quota}人。",
              "编制", quota=quota, staff_type=officer)
        touched.add(seid)
    clerks_eid, clerks = exact_state(
        w, i, "太府寺吏", "官职", "北宋元丰新制",
        "太府寺元丰新制吏额六十五人", roster, "太府寺官吏",
        "建立元丰新制太府寺吏额。", "编制", officer="吏",
    )
    staff(w, i, reform, clerks, roster, "元丰新制太府寺吏额六十五人。",
          "编制", quota=65, staff_type="吏")
    touched.add(clerks_eid)
    for title, category, event in (
        ("太府寺九案", "太府寺办事案", "元丰新制分案九"),
        ("太府寺二十四官司", "太府寺所属官司总称", "元丰新制所隶官司二十四"),
    ):
        seid, child = exact_state(
            w, i, title, "机构", "北宋元丰新制", event,
            roster, category, f"建立{title}。", "编制",
        )
        relation(w, i, reform, child, "上下级机构", roster,
                 f"{title}为元丰新制太府寺所属机构。", "编制")
        touched.add(seid)

    south_parent_eid, south_parent = exact_state(
        w, i, "太府寺", "机构", "南宋绍兴末至隆兴初",
        "官额、案额与吏额形成绍兴末隆兴初编制", roster,
        "南宋财货机构", "建立南宋编制快照。", "编制",
    )
    south_specs = (
        ("太府寺卿", "卿", 1), ("太府寺少卿", "少卿", 1),
        ("太府寺丞", "丞", 3), ("太府寺主簿", "主簿", 1),
        ("胥长", "胥长", 1), ("胥史", "胥史", 2),
        ("胥佐", "胥佐", 17), ("贴司", "贴司", 4),
        ("书状司", "书状司", 1),
    )
    for title, officer, quota in south_specs:
        seid, post = exact_state(
            w, i, title, "官职", "南宋绍兴末至隆兴初",
            f"太府寺南宋所置{officer}，编制{quota}人",
            roster, "太府寺官吏", f"建立南宋{title}定额。", "编制",
            officer=officer,
        )
        staff(w, i, south_parent, post, roster, f"南宋太府寺置{officer}{quota}人。",
              "编制", quota=quota, staff_type=officer)
        touched.add(seid)
    seven_eid, seven = exact_state(
        w, i, "太府寺七案", "机构", "南宋绍兴末至隆兴初",
        "南宋太府寺设案七", roster, "太府寺办事案",
        "建立南宋太府寺七案。", "编制",
    )
    relation(w, i, south_parent, seven, "上下级机构", roster,
             "南宋绍兴末隆兴初太府寺设案七。", "编制")
    touched.update((south_parent_eid, seven_eid))
    finish(w, touched, "整理太府寺源流、职掌、存废与宋前后期完整编制时间链。")


def entry615():
    i, main, aliases = 615, F[615]["text"], field(615, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "判太府寺事", "官职", "宋前期",
        "以带职朝官或两制官充，领本府寺",
        main, "太府寺判寺官", "建立判太府寺事资格与职掌。",
        officer="差遣官", grade="带职朝官或两制官",
    )
    staff(w, i, tp(w, "太府寺", "机构", "宋前期"), post, aliases,
          "宋前期太府寺置判寺事一人。", "简称", quota=1,
          staff_type="判寺官")
    alias_note(w, i, post, aliases, "简称")
    finish(w, {eid}, "整理判太府寺事资格、职掌、简称与编制时间链。")


def entry616():
    i = 616
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, liang = exact_state(
        w, i, "太府寺卿", "官职", "南朝梁", "始置太府卿",
        history, "太府寺长官", "建立梁代太府卿名称源流。", "职源与沿革",
        officer="卿",
    )
    _, origin = exact_state(
        w, i, "太府寺卿", "官职", "北齐", "始置太府寺卿",
        history, "太府寺长官", "建立太府寺卿名称源流。", "职源与沿革",
        officer="卿",
    )
    _, reform = exact_state(
        w, i, "太府寺卿", "官职", "北宋元丰新制",
        "掌国家财货政令，总领库藏出纳、贸易、平准、店宅等事，编制一人",
        duty, "太府寺长官", "规范元丰新制职掌与定额。", "职掌",
        officer="卿", grade="从四品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰后品位班次。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补充卿一人或阙置。", "编制")
    staff(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制太府寺卿一人或阙置。", "编制", quota=1,
          staff_type="卿")
    _, abolished = exact_state(
        w, i, "太府寺卿", "官职", "南宋建炎三年四月十三日", "罢置",
        history, "太府寺长官", "建立建炎三年罢置节点。", "职源与沿革",
        officer="卿",
    )
    _, restored = exact_state(
        w, i, "太府寺卿", "官职", "南宋绍兴四年五月二十六日", "复置",
        history, "太府寺长官", "建立绍兴四年复置节点。", "职源与沿革",
        officer="卿",
    )
    staff(w, i, tp(w, "太府寺", "机构", "南宋绍兴末至隆兴初"), restored,
          roster, "南宋复置太府寺卿，编制一人或阙置。", "编制", quota=1,
          staff_type="卿")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, {eid}, "整理太府寺卿源流、职掌、品位与存废时间链。")


def entry617():
    i = 617
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, wei = exact_state(
        w, i, "太府寺少卿", "官职", "北魏", "始置太府少卿",
        history, "太府寺副长官", "建立北魏太府少卿名称源流。", "职源与沿革",
        officer="少卿",
    )
    _, origin = exact_state(
        w, i, "太府寺少卿", "官职", "北齐", "始置太府寺少卿",
        history, "太府寺副长官", "建立太府寺少卿名称源流。", "职源与沿革",
        officer="少卿",
    )
    _, reform = exact_state(
        w, i, "太府寺少卿", "官职", "北宋元丰新制",
        "佐正卿领本寺事，元丰新制编制一人",
        duty, "太府寺副长官", "规范元丰新制职掌与定额。", "职掌",
        officer="少卿", grade="正六品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰后品位班次。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补充元丰新制定额。", "编制")
    staff(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制太府寺少卿一人。", "编制", quota=1,
          staff_type="少卿")
    _, doubled = exact_state(
        w, i, "太府寺少卿", "官职", "北宋崇宁间", "编制二人",
        roster, "太府寺副长官", "建立崇宁间二少卿节点。", "编制",
        officer="少卿",
    )
    staff(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), doubled, roster,
          "崇宁间太府寺少卿二人。", "编制", quota=2,
          staff_type="少卿")
    _, abolished = exact_state(
        w, i, "太府寺少卿", "官职", "南宋建炎三年四月十三日", "罢置",
        history, "太府寺副长官", "建立建炎三年罢置节点。", "职源与沿革",
        officer="少卿",
    )
    _, restored = exact_state(
        w, i, "太府寺少卿", "官职", "南宋绍兴四年五月二十六日", "复置",
        history, "太府寺副长官", "建立绍兴四年复置节点。", "职源与沿革",
        officer="少卿", grade="正六品",
    )
    cite(w, "Timepoints", restored, i, rank, "补充南宋太府寺少卿品位。", "品位")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, {eid}, "整理太府寺少卿源流、职掌、品位、定额与存废时间链。")


def entry618():
    i = 618
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, liang = exact_state(
        w, i, "太府寺丞", "官职", "南朝梁", "始置太府丞",
        history, "太府寺属官", "建立梁代太府丞名称源流。", "职源与沿革",
        officer="丞",
    )
    _, origin = exact_state(
        w, i, "太府寺丞", "官职", "北齐", "始置太府寺丞",
        history, "太府寺属官", "建立太府寺丞名称源流。", "职源与沿革",
        officer="丞",
    )
    _, reform = exact_state(
        w, i, "太府寺丞", "官职", "北宋元丰新制",
        "参领太府寺事并专掌书押交引库钞引，元丰新制定员二人",
        duty, "太府寺属官", "规范元丰新制职掌与定额。", "职掌",
        officer="丞", grade="正八品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰后品位班次。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补充元丰新制定额。", "编制")
    north_parent = tp(w, "太府寺", "机构", "北宋元丰新制")
    south_parent = tp(w, "太府寺", "机构", "南宋绍兴末至隆兴初")
    staff(w, i, north_parent, reform, roster, "元丰新制太府寺丞二人。",
          "编制", quota=2, staff_type="丞")
    changes = (
        ("北宋元符元年七月", "增为三员", 3),
        ("北宋崇宁间", "丞四员，其中增置一员专行点检京师七药局事", 4),
        ("北宋宣和三年十一月", "复为三员", 3),
        ("南宋绍兴元年五月二十三日", "复置一员", 1),
        ("南宋绍兴三年十二月九日", "增为二员", 2),
        ("南宋绍兴十一年正月", "增为三员", 3),
    )
    for time, event, quota in changes:
        _, post = exact_state(
            w, i, "太府寺丞", "官职", time, event,
            roster, "太府寺属官", f"建立太府寺丞{time}定额变化。", "编制",
            officer="丞",
        )
        staff(
            w, i, south_parent if time.startswith("南宋") else north_parent,
            post, roster, f"{time}太府寺丞定额{quota}员。", "编制",
            quota=quota, staff_type="丞",
        )
        if time == "北宋崇宁间":
            cite(w, "Timepoints", post, i, duty,
                 "补充增置一丞专行点检京师七药局事。", "职掌")
        if time == "南宋绍兴元年五月二十三日":
            cite(w, "Timepoints", post, i, history,
                 "补充绍兴元年复置沿革。", "职源与沿革")
    _, abolished = exact_state(
        w, i, "太府寺丞", "官职", "南宋建炎三年四月十三日", "罢置",
        history, "太府寺属官", "建立建炎三年罢置节点。", "职源与沿革",
        officer="丞",
    )
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, {eid}, "整理太府寺丞源流、职掌、品位、存废及历次定额时间链。")


def entry619():
    i = 619
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, liang = exact_state(
        w, i, "太府寺主簿", "官职", "南朝梁", "始置太府主簿",
        history, "太府寺属官", "建立梁代太府主簿名称源流。", "职源与沿革",
        officer="主簿",
    )
    _, origin = exact_state(
        w, i, "太府寺主簿", "官职", "北齐", "始置太府寺主簿",
        history, "太府寺属官", "建立太府寺主簿名称源流。", "职源与沿革",
        officer="主簿",
    )
    _, reform = exact_state(
        w, i, "太府寺主簿", "官职", "北宋元丰新制",
        "勾考本寺簿书；元丰新制定额异载（二员／一员）",
        duty, "太府寺属官", "规范元丰新制职掌与定额。", "职掌",
        officer="主簿", grade="从八品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰后品位班次。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补充主簿一员。", "编制")
    parent = tp(w, "太府寺", "机构", "北宋元丰新制")
    rid = w.relationship(
        parent, reform, "编制隶属", "太府寺主簿仍隶本寺；本条定额与第614条冲突。",
        roster, staff_quota=1, staff_type="主簿",
    )
    cite(
        w, "Relationships", rid, i, roster,
        "第619条记一员，而第614条编制字段记太府寺丞、主簿各二人；保留冲突证据。",
        "编制", conflict_flag=1,
        note="定额冲突：第614条记二人，本条记一员；关系值暂保留第614条二人。",
    )
    _, abolished = exact_state(
        w, i, "太府寺主簿", "官职", "南宋建炎三年四月十三日", "罢置",
        history, "太府寺属官", "建立建炎三年罢置节点。", "职源与沿革",
        officer="主簿",
    )
    _, restored = exact_state(
        w, i, "太府寺主簿", "官职", "南宋绍兴十年正月二十九日", "复置",
        history, "太府寺属官", "建立绍兴十年复置节点。", "职源与沿革",
        officer="主簿",
    )
    south_parent = tp(w, "太府寺", "机构", "南宋绍兴末至隆兴初")
    staff(w, i, south_parent, restored, roster, "南宋复置太府寺主簿一员。",
          "编制", quota=1, staff_type="主簿")
    _, reduced = exact_state(
        w, i, "太府寺主簿", "官职", "南宋隆兴元年七月二十六日", "省罢",
        history, "太府寺属官", "建立隆兴元年省罢节点。", "职源与沿革",
        officer="主簿",
    )
    _, restored_again = exact_state(
        w, i, "太府寺主簿", "官职", "南宋隆兴二年闰十一月二十七日", "复置",
        history, "太府寺属官", "建立隆兴二年复置节点。", "职源与沿革",
        officer="主簿",
    )
    staff(w, i, south_parent, restored_again, roster,
          "隆兴二年复置太府寺主簿一员。", "编制", quota=1,
          staff_type="主簿")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, {eid}, "整理太府寺主簿源流、职掌、品位及多次存废时间链。")


def entry620():
    i, main = 620, F[620]["text"]
    w = W(i)
    eid, case = exact_state(
        w, i, "太府寺市易案", "机构", "北宋元丰新制",
        "太府寺九案之一，掌平滞销货物价格，由市易务或平准务收进并按市场需求赊售或平价抛出",
        main, "太府寺办事案", "建立太府寺市易案职掌节点。",
    )
    relation(w, i, tp(w, "太府寺九案", "机构", "北宋元丰新制"), case,
             "统称与实例", main, "太府寺市易案是太府寺九案之一。")
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), case,
             "上下级机构", main, "太府寺市易案隶太府寺。")
    finish(w, {eid}, "整理太府寺市易案职掌与九案实例关系时间链。")


def main():
    assert [F[i]["title"] for i in range(601, 621)] == [
        "司农寺排岸司", "所由", "前行", "排岸兼管船场公事", "下卸司",
        "下卸兵士", "散从官", "都曲院", "小博士", "都曲院", "杂职",
        "内柴炭库", "炭场", "太府寺", "判太府寺事", "太府寺卿",
        "太府寺少卿", "太府寺丞", "太府寺主簿", "太府寺市易案",
    ]
    for i in range(601, 621):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
