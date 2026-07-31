#!/usr/bin/env python3
"""提取 chapter5t7 第361-380条：仪鸾司、金吾街司与引驾仗司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_341_360 as previous


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


F = {i: load(i) for i in range(361, 381)}
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
    "汉代": -206, "北齐": 550, "隋代": 581,
    "唐玄宗朝": 712, "唐代": 618, "五代十国": 907,
    "宋代": 960, "宋代（仪鸾司）": 960.01,
    "宋代（仪鸾司押司官制度）": 960.02,
    "宋代（内军器库选补制度）": 960.04,
    "宋代（金吾街司）": 960.05,
    "宋代（金吾引驾仗司）": 960.06,
    "宋初": 960.1, "北宋初": 960.2,
    "北宋太宗朝": 976, "北宋淳化以后": 994,
    "北宋淳化以后（年月未载）": 994.1,
    "北宋太宗朝后（年月未载）": 1000,
    "北宋大中祥符二年六月": 1009.45,
    "北宋大中祥符九年": 1016,
    "北宋大礼（年月未载）": 1020,
    "北宋天圣八年": 1030,
    "北宋天圣八年五月以前": 1030.30,
    "北宋天圣八年五月": 1030.35,
    "北宋元丰五年": 1082,
    "北宋元丰改制后": 1082.1,
    "北宋徽宗朝": 1100,
    "北宋崇宁二年二月": 1103.12,
    "北宋靖康元年": 1126,
    "南宋": 1127,
    "南宋绍兴二年": 1132,
    "南宋绍兴三年": 1133,
    "南宋乾道间": 1167,
    "南宋淳熙十四年": 1187,
    "南宋绍熙二年": 1191,
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


def mark_citation_conflict(w, table, target_id, i, quotation, decision,
                           field_name, note):
    cid = cite(w, table, target_id, i, quotation, decision, field_name)
    row = w.conn.execute(
        "select conflict_flag,note from Citations where id=?", (cid,)
    ).fetchone()
    if row[0] != 1 or row[1] != note:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?", (note, cid)
        )
        w._br("Citations", cid, f"标记原文内部数字冲突：{note}")
    return cid


OFFICIAL_HELPER_EVENT = "为仪鸾司工匠的帮手，编制一百十四人"
LEFT_MERGED_EVENT = "由左金吾街司与左金吾引驾仗司合并编制而成"
RIGHT_MERGED_EVENT = "由右金吾街司与右金吾引驾仗司合并编制而成"


def rank_promotion(i, title, event):
    main = F[i]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, title, "官职", "宋代（内军器库选补制度）",
        event, main, "管库兵阶级", f"建立{title}的管库兵选补规则。",
        officer="兵校职名",
    )
    relation(
        w, i,
        tp(w, "管库兵五阶级", "官职", "宋代（军器七库至内军器库）"),
        post, "统称与实例", main, f"{title}为管库兵五阶级实例。",
    )
    rechain(w, eid, f"整理{title}的管库兵选补时间链。")
    w.commit()


def entry361():
    rank_promotion(361, "十将", "管库兵五阶级之一，出缺时由将虞候选补")


def entry362():
    rank_promotion(
        362, "副都头",
        "管库兵五阶级之一，出缺时由十将选补，任满三年转指挥使",
    )


def entry363():
    i, main, aliases = 363, F[363]["text"], field(363, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "指挥使", "官职", "宋代（内军器库选补制度）",
        "管库兵五阶级中最高阶级，副都头任满三年可转任",
        main, "管库兵阶级", "建立指挥使的管库兵最高阶级节点。", officer="兵校职名",
    )
    relation(
        w, i,
        tp(w, "管库兵五阶级", "官职", "宋代（军器七库至内军器库）"),
        post, "统称与实例", main, "指挥使为管库兵五阶级实例。",
    )
    cite(w, "Timepoints", post, i, aliases,
         "补充副都头三年转指挥使的选补证据；简称只作名称证据。", "简称",
         note="纯简称、别名不另建实体")
    rechain(w, eid, "整理指挥使的管库兵阶级时间链。")
    w.commit()


def entry364():
    i, main = 364, F[364]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()

    palace_eid, palace = exact_state(
        w, i, "守宫署", "机构", "北齐",
        "隶光禄寺，掌宫中帐设", history,
        "前代供帐机构", "建立仪鸾司的北齐职源守宫署。", "职源与沿革",
    )
    supply_eid, supply = exact_state(
        w, i, "供帐库", "机构", "隋代",
        "供帐机构，因鸾鸟集其上而改名仪鸾", history,
        "前代供帐机构", "建立隋代供帐库职源。", "职源与沿革",
    )
    office_eid, sui = exact_state(
        w, i, "仪鸾司", "机构", "隋代",
        "由供帐库改名，属卫尉寺供帐机构", history,
        "宫廷供帐机构", "建立隋代仪鸾司名源节点。", "职源与沿革",
    )
    _, song = exact_state(
        w, i, "仪鸾司", "机构", "宋初",
        "北宋供帐职事归本司，掌朝会、亲祠、巡幸、宴享及宫殿幕帘幄帐供设",
        history, "宫廷供帐机构", "建立北宋仪鸾司职掌节点。", "职源与沿革",
    )
    cite(w, "Timepoints", song, i, duty, "补充仪鸾司供设职掌。", "职掌")
    reform = tp(w, "仪鸾司", "机构", "北宋元丰五年")
    cite(w, "Timepoints", reform, i, main, "确认仪鸾司隶卫尉寺。")
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), reform,
             "上下级机构", main, "元丰新制仪鸾司隶卫尉寺。")
    _, transferred = exact_state(
        w, i, "仪鸾司", "机构", "北宋崇宁二年二月",
        "供御职事划归殿中省尚舍局", duty,
        "宫廷供帐机构", "建立崇宁二年供御职事划归尚舍局节点。", "职掌",
    )
    _, restored = exact_state(
        w, i, "仪鸾司", "机构", "北宋靖康元年",
        "殿中省六尚局罢后，供御职事依旧归本司", duty,
        "宫廷供帐机构", "建立靖康元年职事复归节点。", "职掌",
    )
    cite(w, "Timepoints", tp(w, "尚舍局", "机构", "北宋崇宁二年二月"),
         i, duty, "补充尚舍局接收仪鸾司供御职事证据。", "职掌")
    cite(w, "Timepoints", tp(w, "尚舍局", "机构", "北宋靖康元年"),
         i, duty, "补充尚舍局罢后职事归还仪鸾司证据。", "职掌")
    _, south = exact_state(
        w, i, "仪鸾司", "机构", "南宋",
        "南宋沿置，继续掌宫廷供帐", history,
        "宫廷供帐机构", "建立南宋仪鸾司沿置节点。", "职源与沿革",
    )
    touched.update((palace_eid, supply_eid, office_eid))
    relation(w, i, palace, sui, "前后演变", history,
             "北齐守宫署为仪鸾司供帐职事来源。", "职源与沿革")
    relation(w, i, supply, sui, "前后演变", history,
             "隋代供帐库改名仪鸾司。", "职源与沿革")

    # 主管官与门司等官。
    for title, time, event, quota, staff_type in (
        ("勾当仪鸾司事", "宋初", "勾当仪鸾司事务", 5, "勾当官"),
        ("干办仪鸾司事", "南宋", "南宋改称干办官，干办仪鸾司事务", None, "干办官"),
        ("提举仪鸾司", "宋代（仪鸾司）", "提举仪鸾司事务", None, "提举官"),
        ("点检仪鸾司", "宋代（仪鸾司）", "点检仪鸾司事务", None, "点检官"),
        ("监仪鸾司", "宋代（仪鸾司）", "监领仪鸾司事务", None, "监官"),
        ("仪鸾司门司", "宋代（仪鸾司）", "仪鸾司门司官", None, "门司官"),
    ):
        eid, post = exact_state(
            w, i, title, "官职", time, event, roster,
            "仪鸾司官属", f"建立{title}编制。", "编制", officer=staff_type,
        )
        parent = song if time != "南宋" else south
        staff(w, i, parent, post, roster, f"仪鸾司设置{title}。", "编制",
              quota=quota, staff_type=staff_type)
        touched.add(eid)

    _, xiangfu = exact_state(
        w, i, "仪鸾司", "机构", "北宋大中祥符九年",
        "兵校及匠人二百九十一人，官小一百十四人", roster,
        "宫廷供帐机构", "建立大中祥符九年仪鸾司编制节点。", "编制",
    )
    soldier_eid, soldiers = exact_state(
        w, i, "仪鸾司兵校及匠人", "官职", "北宋大中祥符九年",
        "兵校及匠人二百九十一人", roster,
        "仪鸾司兵匠", "建立仪鸾司兵校及匠人定额。", "编制", officer="兵校、工匠",
    )
    helper_eid, helpers = exact_state(
        w, i, "官小", "官职", "北宋大中祥符九年",
        OFFICIAL_HELPER_EVENT, roster,
        "仪鸾司工匠帮手", "建立仪鸾司官小定额。", "编制", officer="工匠帮手",
    )
    staff(w, i, xiangfu, soldiers, roster, "大中祥符九年仪鸾司兵校及匠人二百九十一人。",
          "编制", quota=291, staff_type="兵校、工匠")
    staff(w, i, xiangfu, helpers, roster, "大中祥符九年仪鸾司官小一百十四人。",
          "编制", quota=114, staff_type="工匠帮手")
    touched.update((soldier_eid, helper_eid))
    for time, count, event in (
        ("北宋徽宗朝", 700, "所管工匠七百人"),
        ("南宋乾道间", 350, "所管工匠压缩为三百五十人"),
    ):
        _, parent = exact_state(
            w, i, "仪鸾司", "机构", time, event, roster,
            "宫廷供帐机构", f"建立仪鸾司{time}工匠编制节点。", "编制",
        )
        eid, workers = exact_state(
            w, i, "仪鸾司工匠", "官职", time, event, roster,
            "仪鸾司工匠", f"建立{time}仪鸾司工匠定额。", "编制", officer="工匠",
        )
        staff(w, i, parent, workers, roster, f"{time}仪鸾司工匠定额。", "编制",
              quota=count, staff_type="工匠")
        touched.add(eid)

    # 人吏与三组库。
    clerk_eid, clerk_group = exact_state(
        w, i, "仪鸾司人吏", "官职", "宋代（仪鸾司）",
        "专知、副知、押司官等人吏的合称", roster,
        "仪鸾司人吏统称", "建立仪鸾司人吏统称。", "编制", officer="人吏统称",
    )
    staff(w, i, song, clerk_group, roster, "仪鸾司设置专知、副知、押司官等人吏。",
          "编制", staff_type="人吏")
    touched.add(clerk_eid)
    for title in ("专知官", "副知", "押司官"):
        eid, clerk = exact_state(
            w, i, title, "官职", "宋代（仪鸾司）",
            "仪鸾司人吏之一", roster,
            "仪鸾司人吏", f"建立{title}的仪鸾司语境节点。", "编制", officer="人吏",
        )
        relation(w, i, clerk_group, clerk, "统称与实例", roster,
                 f"{title}为仪鸾司人吏实例。", "编制")
        touched.add(eid)
    store_group_eid, stores = exact_state(
        w, i, "仪鸾司三库", "机构", "宋代（仪鸾司）",
        "仪鸾司所辖三组库的合称", roster,
        "机构统称", "建立仪鸾司三库统称。", "编制",
    )
    relation(w, i, song, stores, "上下级机构", roster,
             "仪鸾司下辖三组库。", "编制")
    touched.add(store_group_eid)
    for title, event in (
        ("仪鸾司第一、第二等库", "储金银器皿、帘幕什物"),
        ("仪鸾司第三、第四等库", "储香烛、帘幕什物"),
        ("仪鸾司毯油床椅铁器什物库", "储毯、油、床、椅、铁器什物"),
    ):
        eid, store = exact_state(
            w, i, title, "机构", "宋代（仪鸾司）", event, roster,
            "仪鸾司所属库", f"建立{title}。", "编制",
        )
        relation(w, i, stores, store, "统称与实例", roster,
                 f"{title}为仪鸾司三库实例。", "编制")
        touched.add(eid)
        for post_title, post_event, post_type in (
            ("仪鸾司监库官", "监领仪鸾司所属库", "监库官"),
            ("仪鸾司监秤", "监秤仪鸾司所属库物", "监秤"),
        ):
            peid, post = exact_state(
                w, i, post_title, "官职", "宋代（仪鸾司）",
                post_event, roster, "仪鸾司库官",
                f"建立{post_title}。", "编制", officer=post_type,
            )
            staff(w, i, store, post, roster, f"{title}设置{post_title}。", "编制",
                  staff_type=post_type)
            touched.add(peid)
    alias_note(w, i, reform, aliases, "简称与别名")
    for eid in touched:
        rechain(w, eid, "整理仪鸾司职源、职掌、编制与所属库完整时间链。")
    w.commit()


def entry365():
    i, main = 365, F[365]["text"]
    w = W(i)
    touched = set()
    camp_eid, north = exact_state(
        w, i, "仪鸾司营", "机构", "北宋大中祥符九年",
        "设于开封拱辰门外嘉平坊，分南营、北营，兵校及工匠二百九十一人，官小一百十四人",
        main, "仪鸾司兵匠营", "建立北宋仪鸾司营及编制。",
    )
    _, ceremony = exact_state(
        w, i, "仪鸾司营", "机构", "北宋大礼（年月未载）",
        "遇大礼仪鸾司兵士五千人", main,
        "仪鸾司兵匠营", "记录大礼时仪鸾司兵士规模。",
    )
    _, reformed = exact_state(
        w, i, "仪鸾司营", "机构", "北宋天圣八年",
        "南、北两营分为四都，罢南北营都虞候，每营各置正、副指挥使一人",
        main, "仪鸾司兵匠营", "建立天圣八年四都改编节点。",
    )
    _, south = exact_state(
        w, i, "仪鸾司营", "机构", "南宋",
        "设于临安丽正门外、候潮门外", main,
        "仪鸾司兵匠营", "建立南宋仪鸾司营驻地节点。",
    )
    relation(w, i, tp(w, "仪鸾司", "机构", "北宋大中祥符九年"), north,
             "上下级机构", main, "仪鸾司营隶仪鸾司。")
    relation(w, i, tp(w, "仪鸾司", "机构", "南宋"), south,
             "上下级机构", main, "南宋仪鸾司营隶仪鸾司。")
    touched.add(camp_eid)

    camp_nodes = {}
    for title, location, reform_event in (
        ("仪鸾司北营", "北营，设于开封拱辰门外嘉平坊",
         "下辖第一、第二都，每营各置正、副指挥使一人"),
        ("仪鸾司南营", "南营，设于开封拱辰门外嘉平坊",
         "下辖第三、第四都，每营各置正、副指挥使一人"),
    ):
        eid, initial = exact_state(
            w, i, title, "机构", "北宋大中祥符九年", location, main,
            "仪鸾司所属营", f"建立{title}。",
        )
        _, current = exact_state(
            w, i, title, "机构", "北宋天圣八年", reform_event, main,
            "仪鸾司所属营", f"建立{title}天圣八年分都节点。",
        )
        relation(w, i, north, initial, "统称与实例", main,
                 f"{title}为仪鸾司营实例。")
        relation(w, i, reformed, current, "统称与实例", main,
                 f"天圣八年{title}仍为仪鸾司营实例。")
        camp_nodes[title] = current
        touched.add(eid)
    four_eid, four = exact_state(
        w, i, "仪鸾司四都", "机构", "北宋天圣八年",
        "北营第一、第二都与南营第三、第四都的合称", main,
        "机构统称", "建立仪鸾司四都统称。",
    )
    relation(w, i, reformed, four, "上下级机构", main,
             "天圣八年仪鸾司两营下分四都。")
    touched.add(four_eid)
    for title, parent in (
        ("仪鸾司第一都", "仪鸾司北营"),
        ("仪鸾司第二都", "仪鸾司北营"),
        ("仪鸾司第三都", "仪鸾司南营"),
        ("仪鸾司第四都", "仪鸾司南营"),
    ):
        eid, unit = exact_state(
            w, i, title, "机构", "北宋天圣八年",
            f"{parent}所属都", main,
            "仪鸾司所属都", f"建立{title}。",
        )
        relation(w, i, four, unit, "统称与实例", main,
                 f"{title}为仪鸾司四都实例。")
        relation(w, i, camp_nodes[parent], unit, "上下级机构", main,
                 f"{title}隶{parent}。")
        touched.add(eid)
    for title, event, quota, staff_type in (
        ("仪鸾司营指挥使", "每营正指挥使", 1, "指挥使"),
        ("仪鸾司营副指挥使", "每营副指挥使", 1, "副指挥使"),
    ):
        eid, post = exact_state(
            w, i, title, "官职", "北宋天圣八年", event, main,
            "仪鸾司营武职", f"建立{title}。", officer=staff_type,
        )
        for parent in camp_nodes.values():
            staff(w, i, parent, post, main, f"仪鸾司每营各置{title}一人。",
                  quota=quota, staff_type=staff_type)
        touched.add(eid)
    for title, event, staff_type in (
        ("仪鸾司都头", "仪鸾司四都部辖职名", "都头"),
        ("仪鸾司副都头", "仪鸾司四都部辖职名", "副都头"),
        ("仪鸾司十将", "仪鸾司四都部辖职名", "十将"),
        ("仪鸾司将虞候", "仪鸾司四都部辖职名", "将虞候"),
        ("仪鸾司节级", "仪鸾司四都部辖职名", "节级"),
    ):
        eid, post = exact_state(
            w, i, title, "官职", "北宋天圣八年", event, main,
            "仪鸾司营武职", f"建立{title}。", officer=staff_type,
        )
        staff(w, i, four, post, main, f"仪鸾司四都设置{title}。",
              staff_type=staff_type)
        touched.add(eid)
    # 复用第364条所建兵匠、官小节点补充营制证据。
    soldiers = tp(w, "仪鸾司兵校及匠人", "官职", "北宋大中祥符九年")
    helpers = tp(w, "官小", "官职", "北宋大中祥符九年")
    staff(w, i, north, soldiers, main, "仪鸾司营有兵校及工匠二百九十一人。",
          quota=291, staff_type="兵校、工匠")
    staff(w, i, north, helpers, main, "仪鸾司营有官小一百十四人。",
          quota=114, staff_type="工匠帮手")
    for eid in touched:
        rechain(w, eid, "整理仪鸾司营南北营、四都改编与武职时间链。")
    w.commit()


def entry366():
    i, main, aliases = 366, F[366]["text"], field(366, "简称")
    w = W(i)
    eid, active = exact_state(
        w, i, "仪鸾司南北营都虞候", "官职", "北宋天圣八年五月以前",
        "总管仪鸾司南、北营兵校与工匠，位在指挥使之上，编制一人",
        main, "仪鸾司营武职", "建立南北营都虞候职掌与位次。", officer="都虞候",
    )
    _, abolished = exact_state(
        w, i, "仪鸾司南北营都虞候", "官职", "北宋天圣八年五月",
        "罢置，不再添填", main,
        "仪鸾司营武职", "建立天圣八年五月罢置节点。", officer="都虞候",
    )
    staff(w, i, tp(w, "仪鸾司营", "机构", "北宋大中祥符九年"), active,
          main, "仪鸾司南北营置都虞候一人总管。", quota=1, staff_type="都虞候")
    alias_note(w, i, abolished, aliases, "简称")
    rechain(w, eid, "整理仪鸾司南北营都虞候设置与罢置时间链。")
    w.commit()


def entry367():
    i, main = 367, F[367]["text"]
    w = W(i)
    node = tp(w, "官小", "官职", "北宋大中祥符九年")
    set_event(w, node, OFFICIAL_HELPER_EVENT, "统一官小的仪鸾司工匠帮手定义与定额。")
    cite(w, "Timepoints", node, i, main, "补充官小职掌、隶属和一百十四人定额。")
    staff(w, i, tp(w, "仪鸾司", "机构", "北宋大中祥符九年"), node,
          main, "大中祥符九年仪鸾司官小一百十四人。", quota=114, staff_type="工匠帮手")
    w.commit()


def entry368():
    i, main = 368, F[368]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "押司官", "官职", "宋代（仪鸾司押司官制度）",
        "隶仪鸾司，排办本司事务兼点检文字，年满出职可填补专知、副知",
        main, "仪鸾司人吏", "建立押司官的仪鸾司职掌与迁补规则。", officer="公吏",
    )
    staff(w, i, tp(w, "仪鸾司", "机构", "宋初"), post,
          main, "仪鸾司设置押司官。", staff_type="公吏")
    rechain(w, eid, "整理押司官在仪鸾司的职掌时间链。")
    w.commit()


def entry369():
    i, main = 369, F[369]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    group_eid, taizong = exact_state(
        w, i, "左、右金吾街司", "机构", "北宋太宗朝",
        "分左、右司，各置兵士一千人，分四营五都部辖",
        roster, "京城巡警机构统称", "建立北宋太宗朝左右金吾街司编制。", "编制",
    )
    _, first_name = exact_state(
        w, i, "左、右金吾街司", "机构", "北宋大中祥符二年六月",
        "始见金吾街司官署称，掌巡街、报点、警场、清道与纠察不法",
        history, "京城巡警机构统称", "建立金吾街司官署名始见节点。", "职源与沿革",
    )
    cite(w, "Timepoints", first_name, i, duty, "补充金吾街司巡警职掌。", "职掌")
    _, reform = exact_state(
        w, i, "左、右金吾街司", "机构", "北宋元丰五年",
        "隶卫尉寺，分左、右二司", main,
        "卫尉寺所属机构统称", "建立元丰新制隶属节点。",
    )
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), reform,
             "上下级机构", main, "左、右金吾街司隶卫尉寺。")
    _, reduced = exact_state(
        w, i, "左、右金吾街司", "机构", "北宋太宗朝后（年月未载）",
        "左、右街司兵士各由一千人减为八百人", roster,
        "京城巡警机构统称", "建立左右街司兵额减置节点。", "编制",
    )
    _, south = exact_state(
        w, i, "左、右金吾街司", "机构", "南宋",
        "南宋沿置，继续掌巡警京城街道", history,
        "京城巡警机构统称", "建立南宋沿置节点。", "职源与沿革",
    )
    _, shao2 = exact_state(
        w, i, "左、右金吾街司", "机构", "南宋绍兴二年",
        "左右金吾街仗司通共二百人为额", roster,
        "京城巡警机构统称", "建立绍兴二年街仗司总额节点。", "编制",
    )
    _, chunxi = exact_state(
        w, i, "左、右金吾街司", "机构", "南宋淳熙十四年",
        "街司与引驾仗司按左右重新合编为左、右金吾街仗司",
        roster, "京城巡警机构统称", "建立淳熙十四年街仗司改编节点。", "编制",
    )
    touched.add(group_eid)
    individual = {}
    for title in ("左金吾街司", "右金吾街司"):
        eid, early = exact_state(
            w, i, title, "机构", "北宋太宗朝",
            "金吾街司之一，置兵士一千人", roster,
            "京城巡警机构", f"建立{title}北宋太宗朝编制。", "编制",
        )
        _, after = exact_state(
            w, i, title, "机构", "北宋太宗朝后（年月未载）",
            "兵士减为八百人", roster,
            "京城巡警机构", f"建立{title}减额节点。", "编制",
        )
        _, transition = exact_state(
            w, i, title, "机构", "南宋淳熙十四年",
            "与同侧金吾引驾仗司合并编制", roster,
            "京城巡警机构", f"建立{title}淳熙十四年改编节点。", "编制",
        )
        relation(w, i, taizong, early, "统称与实例", roster,
                 f"{title}为左、右金吾街司实例。", "编制")
        individual[title] = (early, after, transition)
        touched.add(eid)
    soldier_eid, thousand = exact_state(
        w, i, "金吾街司兵士", "官职", "北宋太宗朝",
        "左、右街司各置一千人", roster,
        "金吾街司兵役", "建立北宋太宗朝街司兵士定额。", "编制", officer="兵士",
    )
    _, eight_hundred = exact_state(
        w, i, "金吾街司兵士", "官职", "北宋太宗朝后（年月未载）",
        "左、右街司各减为八百人", roster,
        "金吾街司兵役", "建立街司兵士减额节点。", "编制", officer="兵士",
    )
    for title in individual:
        staff(w, i, individual[title][0], thousand, roster,
              f"{title}置兵士一千人。", "编制", quota=1000, staff_type="兵士")
        staff(w, i, individual[title][1], eight_hundred, roster,
              f"{title}兵士后减为八百人。", "编制", quota=800, staff_type="兵士")
    touched.add(soldier_eid)
    structure_eid, structure = exact_state(
        w, i, "金吾街司四营五都", "机构", "北宋太宗朝",
        "左、右街司兵士分四营五都部辖", roster,
        "金吾街司兵营编制", "建立金吾街司四营五都编制。", "编制",
    )
    relation(w, i, taizong, structure, "上下级机构", roster,
             "左、右金吾街司下设四营五都。", "编制")
    touched.add(structure_eid)
    for title, event, time, staff_type in (
        ("勾当左、右金吾街司事", "勾当左、右金吾街司事务", "北宋淳化以后", "勾当官"),
        ("干办左、右金吾街司事", "南宋改称干办官，干办左、右金吾街司事务", "南宋", "干办官"),
        ("知左、右街司事", "知左、右街司事务", "宋代（金吾街司）", "差遣"),
    ):
        eid, post = exact_state(
            w, i, title, "官职", time, event, roster,
            "金吾街司差遣", f"建立{title}编制。", "编制", officer=staff_type,
        )
        staff(w, i, first_name if time != "南宋" else south, post, roster,
              f"左、右金吾街司设置{title}。", "编制", staff_type=staff_type)
        touched.add(eid)
    clerk_eid, clerk_group = exact_state(
        w, i, "金吾街司人吏", "官职", "宋代（金吾街司）",
        "孔目官、表奏官等人吏的合称", roster,
        "金吾街司人吏统称", "建立金吾街司人吏统称。", "编制", officer="人吏统称",
    )
    staff(w, i, first_name, clerk_group, roster,
          "左、右金吾街司设置孔目官、表奏官等人吏。", "编制", staff_type="人吏")
    touched.add(clerk_eid)
    for title in ("孔目官", "表奏官"):
        eid, clerk = exact_state(
            w, i, title, "官职", "宋代（金吾街司）",
            "金吾街司人吏之一", roster,
            "金吾街司人吏", f"建立{title}的金吾街司语境节点。", "编制", officer="人吏",
        )
        relation(w, i, clerk_group, clerk, "统称与实例", roster,
                 f"{title}为金吾街司人吏实例。", "编制")
        touched.add(eid)
    # 淳熙十四年按左右改编为新的街仗司。
    merged_nodes = {}
    for title, event, source_title in (
        ("左金吾街仗司", LEFT_MERGED_EVENT, "左金吾街司"),
        ("右金吾街仗司", RIGHT_MERGED_EVENT, "右金吾街司"),
    ):
        eid, merged = exact_state(
            w, i, title, "机构", "南宋淳熙十四年", event, roster,
            "金吾街仗机构", f"建立{title}淳熙十四年改编节点。", "编制",
        )
        relation(w, i, individual[source_title][2], merged, "前后演变", roster,
                 f"淳熙十四年{source_title}改编入{title}。", "编制")
        merged_nodes[title] = merged
        touched.add(eid)
    _, left_quota = exact_state(
        w, i, "左金吾街仗司", "机构", "南宋绍熙二年",
        "立定一百三十一人为额", roster,
        "金吾街仗机构", "建立绍熙二年左街仗司定额。", "编制",
    )
    _, right_quota = exact_state(
        w, i, "右金吾街仗司", "机构", "南宋绍熙二年",
        "立定一百二十一人为额", roster,
        "金吾街仗机构", "建立绍熙二年右街仗司定额。", "编制",
    )
    combined_eid, combined = exact_state(
        w, i, "左、右金吾街仗司", "机构", "南宋绍兴二年",
        "左右金吾街仗司通共二百人为额", roster,
        "机构统称", "建立绍兴二年左右金吾街仗司总称及定额。", "编制",
    )
    relation(w, i, combined, south, "统称与实例", roster,
             "绍兴二年左右金吾街仗司所含街司部分。", "编制")
    touched.add(combined_eid)
    alias_note(w, i, reform, aliases, "简称")
    for eid in touched:
        rechain(w, eid, "整理左、右金吾街司沿革、兵额与淳熙改编时间链。")
    w.commit()


def entry370():
    i, main, aliases = 370, F[370]["text"], field(370, "简称")
    w = W(i)
    node = tp(w, "左金吾街司", "机构", "北宋太宗朝")
    relation(w, i, tp(w, "左、右金吾街司", "机构", "北宋太宗朝"), node,
             "统称与实例", main, "左金吾街司为金吾街司左、右二局之一。")
    cite(w, "Timepoints", node, i, main, "确认左金吾街司与右司职事相同。")
    alias_note(w, i, node, aliases, "简称")
    w.commit()


def entry371():
    i, main, aliases = 371, F[371]["text"], field(371, "简称")
    w = W(i)
    node = tp(w, "右金吾街司", "机构", "北宋太宗朝")
    relation(w, i, tp(w, "左、右金吾街司", "机构", "北宋太宗朝"), node,
             "统称与实例", main, "右金吾街司为金吾街司左、右二局之一。")
    cite(w, "Timepoints", node, i, main, "确认右金吾街司与左司职事相同。")
    alias_note(w, i, node, aliases, "简称")
    w.commit()


def entry372():
    i, main = 372, F[372]["text"]
    history, duty, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    group_eid = None
    nodes = {}
    for time, event in (
        ("唐玄宗朝", "始设左、右街使"),
        ("五代十国", "沿置左、右街使"),
        ("宋初", "沿置，掌街司巡警、纠治不法与街鼓报点"),
        ("北宋淳化以后", "多改为判、知或管勾左、右街司事等差遣"),
    ):
        group_eid, nodes[time] = exact_state(
            w, i, "左、右街使", "官职", time, event,
            duty if time == "宋初" else history,
            "金吾街司职事官统称", f"建立左、右街使{time}节点。",
            "职掌" if time == "宋初" else "职源与沿革", officer="职事官",
        )
    touched.add(group_eid)
    for title in ("左街使", "右街使"):
        eid, post = exact_state(
            w, i, title, "官职", "宋初",
            "左、右街使之一，掌本街司巡警与街鼓报点", main,
            "金吾街司职事官", f"建立{title}实例。", officer="职事官",
        )
        relation(w, i, nodes["宋初"], post, "统称与实例", main,
                 f"{title}为左、右街使实例。")
        touched.add(eid)
    staff(w, i, tp(w, "左、右金吾街司", "机构", "北宋大中祥符二年六月"),
          nodes["宋初"], main, "左、右街使总掌本街司职事。", staff_type="职事官")
    alias_note(w, i, nodes["宋初"], aliases, "简称")
    for eid in touched:
        rechain(w, eid, "整理左、右街使从唐至北宋的沿革时间链。")
    w.commit()


def entry373():
    i, main = 373, F[373]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "知右街司事", "官职", "北宋淳化以后（年月未载）",
        "以诸司使充，领右街司事", main,
        "金吾街司差遣", "建立知右街司事任用与职掌。", officer="诸司使差遣",
    )
    staff(w, i, tp(w, "右金吾街司", "机构", "北宋太宗朝后（年月未载）"),
          post, main, "右金吾街司设置知右街司事。", staff_type="诸司使差遣")
    relation(w, i, tp(w, "知左、右街司事", "官职", "宋代（金吾街司）"), post,
             "统称与实例", main, "知右街司事为知左、右街司事所指实例。")
    rechain(w, eid, "整理知右街司事时间链。")
    w.commit()


def entry374():
    assert F[374]["title"] == "街司"
    assert F[374]["text"] == ""
    assert F[374]["fields"].get("__status__") == "placeholder"


def entry375():
    i, main, aliases = 375, F[375]["text"], field(375, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "判左、右金吾街司事", "官职", "北宋淳化以后（年月未载）",
        "以环卫官将军以上充，总领本司事，编制一人", main,
        "金吾街司差遣", "建立判左、右金吾街司事任用、职掌与定额。", officer="环卫官将军以上差遣",
    )
    staff(w, i, tp(w, "左、右金吾街司", "机构", "北宋大中祥符二年六月"),
          post, main, "左、右金吾街司置判司事一人。", quota=1,
          staff_type="环卫官将军以上差遣")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理判左、右金吾街司事时间链。")
    w.commit()


def entry376():
    i, main = 376, F[376]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    han_eid, han = exact_state(
        w, i, "执金吾", "官职", "汉代",
        "持攻守兵器防御非常", history,
        "前代宫卫官", "建立金吾引驾仗司的汉代职源。", "职源与沿革", officer="宫卫官",
    )
    sui_eid, sui = exact_state(
        w, i, "左、右武候", "官职", "隋代",
        "承执金吾宫卫之职", history,
        "前代宫卫官", "建立隋代左、右武候职源。", "职源与沿革", officer="宫卫官",
    )
    tang_eid, tang = exact_state(
        w, i, "左、右金吾卫", "机构", "唐代",
        "由隋左、右武候改置", history,
        "前代宫卫机构", "建立唐代左、右金吾卫职源。", "职源与沿革",
    )
    office_eid, early = exact_state(
        w, i, "左、右金吾引驾仗司", "机构", "北宋初",
        "别置于无职事的左、右金吾卫环卫官之外，掌殿内宿卫及巡幸勘箭、唱和、喝探",
        history, "宫廷宿卫机构统称", "建立北宋左、右金吾引驾仗司。", "职源与沿革",
    )
    cite(w, "Timepoints", early, i, duty, "补充金吾引驾仗司宿卫职掌。", "职掌")
    _, reform = exact_state(
        w, i, "左、右金吾引驾仗司", "机构", "北宋元丰五年",
        "隶卫尉寺，分左、右二司", main,
        "卫尉寺所属机构统称", "建立元丰新制隶属节点。",
    )
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), reform,
             "上下级机构", main, "左、右金吾引驾仗司隶卫尉寺。")
    _, yuanfeng = exact_state(
        w, i, "左、右金吾引驾仗司", "机构", "北宋元丰改制后",
        "所隶兵士曾增为八百人", roster,
        "宫廷宿卫机构统称", "建立元丰改制后兵额节点。", "编制",
    )
    _, south = exact_state(
        w, i, "左、右金吾引驾仗司", "机构", "南宋",
        "南宋沿置", history,
        "宫廷宿卫机构统称", "建立南宋沿置节点。", "职源与沿革",
    )
    _, shao3 = exact_state(
        w, i, "左、右金吾引驾仗司", "机构", "南宋绍兴三年",
        "立定兵士一百五十人", roster,
        "宫廷宿卫机构统称", "建立绍兴三年兵额节点。", "编制",
    )
    _, chunxi = exact_state(
        w, i, "左、右金吾引驾仗司", "机构", "南宋淳熙十四年",
        "与街司按左右混合编制", roster,
        "宫廷宿卫机构统称", "建立淳熙十四年街仗混编节点。", "编制",
    )
    touched.update((han_eid, sui_eid, tang_eid, office_eid))
    relation(
        w, i,
        tp(w, "左、右金吾街仗司", "机构", "南宋绍兴二年"), south,
        "统称与实例", roster,
        "绍兴二年左右金吾街仗司所含引驾仗司部分。", "编制",
    )
    relation(w, i, han, sui, "前后演变", history,
             "汉执金吾职演为隋左、右武候。", "职源与沿革")
    relation(w, i, sui, tang, "前后演变", history,
             "隋左、右武候改为唐左、右金吾卫。", "职源与沿革")
    relation(w, i, tang, early, "前后演变", history,
             "北宋在金吾卫环卫官名目之外别置金吾引驾仗司承职。", "职源与沿革")

    guard_nodes = {}
    for title in ("左金吾引驾仗司", "右金吾引驾仗司"):
        eid, start = exact_state(
            w, i, title, "机构", "北宋初",
            "左、右金吾引驾仗司之一，所隶兵士五十三人", roster,
            "宫廷宿卫机构", f"建立{title}北宋初编制。", "编制",
        )
        relation(w, i, early, start, "统称与实例", roster,
                 f"{title}为左、右金吾引驾仗司实例。", "编制")
        _, transition = exact_state(
            w, i, title, "机构", "南宋淳熙十四年",
            "与同侧金吾街司合并编制", roster,
            "宫廷宿卫机构", f"建立{title}淳熙十四年改编节点。", "编制",
        )
        guard_nodes[title] = (start, transition)
        touched.add(eid)
    conflict_note = "原文称左、右司兵士各五十三人，合计应为一百零六人，却又称总一百二十六人"
    mark_citation_conflict(
        w, "Timepoints", early, i, roster,
        "保留北宋初各司兵额与总额的原文内部不一致。", "编制", conflict_note,
    )
    soldier_eid, start_soldiers = exact_state(
        w, i, "金吾引驾仗司兵士", "官职", "北宋初",
        "左、右司各五十三人，原文另称总一百二十六人", roster,
        "金吾引驾仗司兵役", "建立北宋初兵额并保留原文数字不一致。", "编制", officer="兵士",
    )
    _, yf_soldiers = exact_state(
        w, i, "金吾引驾仗司兵士", "官职", "北宋元丰改制后",
        "曾增为八百人", roster,
        "金吾引驾仗司兵役", "建立元丰改制后兵额。", "编制", officer="兵士",
    )
    _, south_soldiers = exact_state(
        w, i, "金吾引驾仗司兵士", "官职", "南宋绍兴三年",
        "立定一百五十人", roster,
        "金吾引驾仗司兵役", "建立绍兴三年兵额。", "编制", officer="兵士",
    )
    for start, _ in guard_nodes.values():
        staff(w, i, start, start_soldiers, roster, "北宋初每司兵士五十三人。",
              "编制", quota=53, staff_type="兵士")
    staff(w, i, yuanfeng, yf_soldiers, roster, "元丰改制后兵士曾增为八百人。",
          "编制", quota=800, staff_type="兵士")
    staff(w, i, shao3, south_soldiers, roster, "绍兴三年立定兵士一百五十人。",
          "编制", quota=150, staff_type="兵士")
    touched.add(soldier_eid)
    clerk_eid, clerk_group = exact_state(
        w, i, "金吾引驾仗司官吏", "官职", "宋代（金吾引驾仗司）",
        "孔目官、勾押官、引驾官、都押衙、勾画都知、节级、四色官、穰稍官、知箭门仗官、探头等属官人吏的合称",
        roster, "金吾引驾仗司官吏统称", "建立金吾引驾仗司官吏统称。", "编制",
        officer="属官、人吏统称",
    )
    staff(w, i, early, clerk_group, roster,
          "左、右金吾引驾仗司设置属官、人吏。", "编制", staff_type="属官、人吏")
    touched.add(clerk_eid)
    for title in (
        "孔目官", "勾押官", "引驾官", "都押衙", "勾画都知", "节级",
        "四色官", "穰稍官", "知箭门仗官", "探头",
    ):
        eid, clerk = exact_state(
            w, i, title, "官职", "宋代（金吾引驾仗司）",
            "金吾引驾仗司属官或人吏之一", roster,
            "金吾引驾仗司官吏", f"建立{title}的金吾引驾仗司语境节点。", "编制",
            officer="属官或人吏",
        )
        relation(w, i, clerk_group, clerk, "统称与实例", roster,
                 f"{title}为金吾引驾仗司官吏实例。", "编制")
        touched.add(eid)
    # 与第369条已建的新左右街仗司接续。
    for guard_title, merged_title in (
        ("左金吾引驾仗司", "左金吾街仗司"),
        ("右金吾引驾仗司", "右金吾街仗司"),
    ):
        relation(w, i, guard_nodes[guard_title][1],
                 tp(w, merged_title, "机构", "南宋淳熙十四年"),
                 "前后演变", roster,
                 f"淳熙十四年{guard_title}并入同侧{merged_title}。", "编制")
    alias_note(w, i, reform, aliases, "简称")
    for eid in touched:
        rechain(w, eid, "整理左、右金吾引驾仗司职源、兵额与淳熙改编时间链。")
    w.commit()


def entry377():
    i, main, aliases = 377, F[377]["text"], field(377, "简称")
    w = W(i)
    node = tp(w, "左金吾引驾仗司", "机构", "北宋初")
    relation(w, i, tp(w, "左、右金吾引驾仗司", "机构", "北宋初"), node,
             "统称与实例", main, "左金吾引驾仗司为左、右二司之一。")
    cite(w, "Timepoints", node, i, main, "确认左金吾引驾仗司与右司职事相同。")
    alias_note(w, i, node, aliases, "简称")
    w.commit()


def entry378():
    i, main, aliases = 378, F[378]["text"], field(378, "简称")
    w = W(i)
    node = tp(w, "右金吾引驾仗司", "机构", "北宋初")
    relation(w, i, tp(w, "左、右金吾引驾仗司", "机构", "北宋初"), node,
             "统称与实例", main, "右金吾引驾仗司为左、右二司之一。")
    cite(w, "Timepoints", node, i, main,
         "确认右司与左司职事相同、分部部辖本司兵士。")
    alias_note(w, i, node, aliases, "简称")
    w.commit()


def entry379():
    i, main, aliases = 379, F[379]["text"], field(379, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "判左、右金吾引驾仗司事", "官职", "宋代",
        "以环卫官或六统军将军以上充，总领本司公事，编制一人",
        main, "金吾引驾仗司差遣", "建立判左、右金吾引驾仗司事任用、职掌与定额。",
        officer="环卫官或六统军将军以上差遣",
    )
    staff(w, i, tp(w, "左、右金吾引驾仗司", "机构", "北宋初"), post,
          aliases, "左、右金吾引驾仗司置判司事一人。", "简称",
          quota=1, staff_type="环卫官或六统军将军以上差遣")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理判左、右金吾引驾仗司事时间链。")
    w.commit()


def entry380():
    i, main, aliases = 380, F[380]["text"], field(380, "简称")
    w = W(i)
    eid = w.find_entity("左金吾街仗司", "机构")
    assert eid
    merged = tp(w, "左金吾街仗司", "机构", "南宋淳熙十四年")
    left_street = tp(w, "左金吾街司", "机构", "南宋淳熙十四年")
    left_guard = tp(w, "左金吾引驾仗司", "机构", "南宋淳熙十四年")
    relation(w, i, merged, left_street, "统称与实例", main,
             "左金吾街司为左金吾街仗司合称所含实例。")
    relation(w, i, merged, left_guard, "统称与实例", main,
             "左金吾引驾仗司为左金吾街仗司合称所含实例。")
    cite(w, "Timepoints", merged, i, main,
         "确认左金吾街仗司为左街司与左引驾仗司合称。")
    quota = tp(w, "左金吾街仗司", "机构", "南宋绍熙二年")
    cite(w, "Timepoints", quota, i, aliases,
         "补充绍熙二年左街仗司一百三十一人定额；简称只作名称证据。", "简称",
         note="纯简称、别名不另建实体")
    rechain(w, eid, "整理左金吾街仗司合称、改编与定额时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(361, 381)] == [
        "十将", "副都头", "指挥使", "仪鸾司", "仪鸾司营",
        "仪鸾司南北营都虞候", "官小", "押司官", "左、右金吾街司",
        "左金吾街司", "右金吾街司", "左、右街使", "知右街司事",
        "街司", "判左、右金吾街司事", "左、右金吾引驾仗司",
        "左金吾引驾仗司", "右金吾引驾仗司",
        "判左、右金吾引驾仗司事", "左金吾街仗司",
    ]
    for i in range(361, 381):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
