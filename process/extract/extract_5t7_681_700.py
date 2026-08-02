#!/usr/bin/env python3
"""提取 chapter5t7 第681-700条：店宅、养济、药局、石炭场与汴蔡河锁。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_661_680 as previous


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


F = {i: load(i) for i in range(681, 701)}
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
    "宋初": 960,
    "北宋太平兴国中": 980,
    "北宋端拱二年": 989,
    "北宋淳化五年": 994,
    "北宋至道三年": 997,
    "北宋咸平元年": 998,
    "北宋咸平六年": 1003,
    "北宋景德三年": 1006,
    "北宋大中祥符元年": 1008,
    "北宋大中祥符六年": 1013,
    "北宋天圣四年": 1026,
    "北宋明道元年九月二十一日": 1032.72,
    "宋代（左右厢店宅务）": 1050,
    "宋代（未载具体年月）": 1050.1,
    "北宋熙宁九年六月": 1076.45,
    "北宋元丰元年四月": 1078.28,
    "北宋元丰新制": 1082.1,
    "北宋元祐四年十二月": 1089.95,
    "北宋崇宁中": 1104,
    "北宋崇宁三年": 1104.1,
    "北宋徽宗朝": 1110,
    "南宋": 1127,
    "南宋初": 1127.1,
    "南宋绍兴六年正月四日": 1136.01,
    "南宋绍兴十三年": 1143,
    "南宋绍兴十八年闰八月二十三日": 1148.68,
    "南宋绍兴二十一年闰四月二日": 1151.32,
    "南宋孝宗朝以后": 1163,
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
                field_name=None, *, officer=None, grade=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )
    set_event(w, tid, event, decision)
    return eid, tid


def support_state(w, i, title, type_, time, event, quotation, category, decision,
                  field_name=None, *, officer=None, grade=None):
    return state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def entry681():
    i, main = 681, F[681]["text"]
    w, touched = W(i), set()
    eid, early = exact_state(
        w, i, "楼店务", "机构", "宋初",
        "始置，掌收官屋、邸店房廊税", main,
        "官屋邸店监当局", "建立楼店务宋初始置节点。",
    )
    _, ending = exact_state(
        w, i, "楼店务", "机构", "北宋太平兴国中",
        "改称左右厢店宅务", main,
        "官屋邸店监当局", "建立楼店务北宋改名节点。",
    )
    target_eid, target = exact_state(
        w, i, "左右厢店宅务", "机构", "北宋太平兴国中",
        "由楼店务改称", main, "官屋邸店监当局",
        "建立左右厢店宅务改称节点。",
    )
    relation(w, i, ending, target, "前后演变", main,
             "太平兴国中楼店务改称左右厢店宅务。")
    _, south = exact_state(
        w, i, "楼店务", "机构", "南宋",
        "移置临安府治东中和坊，仍称楼店务，岁收房廊税三十余万贯",
        main, "临安官屋邸店监当局", "建立南宋临安楼店务节点。",
    )
    touched.update((eid, target_eid))
    finish(w, touched, "整理楼店务宋初始置、北宋改名及南宋临安沿置时间链。")


def entry682():
    i = 682
    main, origin, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()

    def node(title, time, event, decision):
        eid, tid = exact_state(
            w, i, title, "机构", time, event, origin,
            "官屋邸店监当局", decision, "职源与沿革",
        )
        touched.add(eid)
        return tid

    source = node("楼店务", "宋初", "始置，掌收官屋、邸店房廊税",
                  "补证楼店务前身节点。")
    left_right = node("左右厢店宅务", "北宋太平兴国中",
                      "由楼店务改称",
                      "补证左右厢店宅务最初改称节点。")
    relation(w, i, source, left_right, "前后演变", origin,
             "宋初楼店务于太平兴国中改称左右厢店宅务。", "职源与沿革")
    end_lr = node("左右厢店宅务", "北宋端拱二年", "改为邸店宅务",
                  "建立左右厢店宅务端拱改名节点。")
    residence = node("邸店宅务", "北宋端拱二年", "由左右厢店宅务改称",
                     "建立邸店宅务改称节点。")
    relation(w, i, end_lr, residence, "前后演变", origin,
             "端拱二年左右厢店宅务改为邸店宅务。", "职源与沿革")
    end_residence = node("邸店宅务", "北宋淳化五年", "分为左、右厢店宅务",
                         "建立邸店宅务分置节点。")
    divided = node("左右厢店宅务", "北宋淳化五年", "分为左、右两厢",
                   "建立左右厢店宅务淳化分置节点。")
    relation(w, i, end_residence, divided, "前后演变", origin,
             "淳化五年邸店宅务分为左、右厢店宅务。", "职源与沿革")
    node("左右厢店宅务", "北宋至道三年", "左、右两厢合并为一局",
         "建立左右厢店宅务至道合局节点。")
    end_combined = node("左右厢店宅务", "北宋咸平元年",
                        "改为都大店宅务兼修造司",
                        "建立左右厢店宅务咸平改名节点。")
    combined = node("都大店宅务兼修造司", "北宋咸平元年",
                    "由左右厢店宅务改名，兼领修造司",
                    "建立都大店宅务兼修造司节点。")
    relation(w, i, end_combined, combined, "前后演变", origin,
             "咸平元年左右厢店宅务改为都大店宅务兼修造司。", "职源与沿革")
    combined_end = node("都大店宅务兼修造司", "北宋咸平六年", "修造司析出",
                        "建立兼修造司析出节点。")
    great = node("都大店宅务", "北宋咸平六年", "修造司析出后单设",
                 "建立都大店宅务节点。")
    repair = node("修造司", "北宋咸平六年", "自都大店宅务兼修造司析出",
                  "建立修造司析出节点。")
    relation(w, i, combined_end, great, "前后演变", origin,
             "咸平六年修造司析出后仍置都大店宅务。", "职源与沿革")
    relation(w, i, combined_end, repair, "前后演变", origin,
             "咸平六年修造司自都大店宅务兼修造司析出。", "职源与沿革")
    great_end = node("都大店宅务", "北宋景德三年", "再次兼领修造司",
                     "建立都大店宅务景德兼领节点。")
    repair_end = node("修造司", "北宋景德三年", "再次并入都大店宅务",
                      "建立修造司景德并入节点。")
    combined_again = node("都大店宅务兼修造司", "北宋景德三年",
                          "都大店宅务再次兼领修造司",
                          "建立再次兼修造司节点。")
    relation(w, i, great_end, combined_again, "前后演变", origin,
             "景德三年都大店宅务再次兼修造司。", "职源与沿革")
    relation(w, i, repair_end, combined_again, "前后演变", origin,
             "景德三年修造司再次并入都大店宅务。", "职源与沿革")
    combined_again_end = node("都大店宅务兼修造司", "北宋大中祥符元年",
                              "修造司改隶八作司",
                              "建立兼修造司终止节点。")
    great_again = node("都大店宅务", "北宋大中祥符元年",
                       "修造司改隶八作司后单设",
                       "建立都大店宅务大中祥符节点。")
    relation(w, i, combined_again_end, great_again, "前后演变", origin,
             "大中祥符元年修造司改隶后仍为都大店宅务。", "职源与沿革")
    _, repair_under = support_state(
        w, i, "修造司", "机构", "北宋大中祥符元年", "改隶八作司",
        origin, "修造机构", "建立修造司改隶节点。", "职源与沿革",
    )
    eight_eid, eight = support_state(
        w, i, "八作司", "机构", "北宋大中祥符元年", "统辖修造司",
        origin, "营造主管机构", "建立八作司统辖修造司节点。", "职源与沿革",
    )
    relation(w, i, eight, repair_under, "上下级机构", origin,
             "大中祥符元年修造司隶八作司。", "职源与沿革")
    great_end2 = node("都大店宅务", "北宋大中祥符六年",
                      "改称左右厢店宅务",
                      "建立都大店宅务最终改名节点。")
    later_lr = node("左右厢店宅务", "北宋大中祥符六年",
                    "由都大店宅务改称",
                    "建立左右厢店宅务复名节点。")
    relation(w, i, great_end2, later_lr, "前后演变", origin,
             "大中祥符六年都大店宅务改为左右厢店宅务。", "职源与沿革")

    _, office = exact_state(
        w, i, "左右厢店宅务", "机构", "北宋天圣四年",
        "掌官屋邸店出租、收课利并修缮房屋；监官六人、勾当官二人",
        duty, "官屋邸店监当局", "建立天圣四年职掌编制节点。", "职掌",
    )
    roles = (
        ("提举制置左右厢店宅务", "提举制置官", None),
        ("监左右厢店宅务", "监官", 6),
        ("勾当左厢店宅务公事", "勾当官", 1),
        ("勾当右厢店宅务公事", "勾当官", 1),
        ("店宅务专知官", "吏", None),
        ("店宅务副知官", "吏", None),
        ("店宅务前行", "吏", 1),
        ("掠钱亲事官", "公吏", 50),
        ("店宅务看管兵士", "兵士", 20),
        ("修选指挥", "兵士", 500),
    )
    for title, officer, quota in roles:
        role_eid, post = exact_state(
            w, i, title, "官职", "北宋天圣四年",
            f"左右厢店宅务所置{title}", roster,
            "左右厢店宅务官吏", f"建立{title}编制节点。", "编制",
            officer=officer,
        )
        staff(w, i, office, post, roster, f"左右厢店宅务设{title}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    cite(w, "Timepoints", office, i, roster, "补证天圣四年左右厢店宅务官吏额。", "编制")
    alias_note(w, i, later_lr, aliases, "简称与别名")
    touched.add(eight_eid)
    finish(w, touched, "整理左右厢店宅务历次改名、分合、职掌与官吏时间链。")


def entry683():
    i, main, aliases = 683, F[683]["text"], field(683, "简称与别名")
    w = W(i)
    eid, post = support_state(
        w, i, "监左右厢店宅务", "官职", "北宋天圣四年",
        "由京朝官、三班、内侍差充，掌领店宅务事",
        main, "左右厢店宅务监官", "复用监左右厢店宅务节点并补职掌证据。",
        officer="监官",
    )
    staff(w, i, tp(w, "左右厢店宅务", "机构", "北宋天圣四年"),
          post, main, "监左右厢店宅务掌领本务，人数三、四人不定。",
          staff_type="监官")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, {eid}, "补证监左右厢店宅务的充任、职掌、编制变化与别称。")


def entry684():
    i, main = 684, F[684]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "掠钱亲事官", "官职", "北宋天圣四年",
        "店宅务亲事官，按地区催收赁屋房钱，一年一替",
        main, "店宅务公吏", "复用掠钱亲事官并补职掌证据。", officer="公吏",
    )
    staff(w, i, tp(w, "左右厢店宅务", "机构", "北宋天圣四年"), post,
          main, "掠钱亲事官隶店宅务，专掌催收房钱。", staff_type="公吏")
    finish(w, {eid}, "补证掠钱亲事官隶属、职掌与替换方式。")


def entry685():
    i, main = 685, F[685]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "店宅务专知官", "官职", "北宋天圣四年",
        "由懂钱谷、有行止的军大将充，掌算帐、造帐",
        main, "店宅务公吏", "复用店宅务专知官并补职掌证据。", officer="吏",
    )
    staff(w, i, tp(w, "左右厢店宅务", "机构", "北宋天圣四年"), post,
          main, "店宅务专知官隶店宅务，掌算帐、造帐。", staff_type="吏")
    finish(w, {eid}, "补证店宅务专知官隶属、充任与职掌。")


def entry686():
    i, main = 686, F[686]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "店宅务勾押官", "官职", "宋代（左右厢店宅务）",
        "与专知、副知共同收管官钱", main,
        "店宅务公吏", "建立店宅务勾押官节点。", officer="公吏",
    )
    _, office = support_state(
        w, i, "左右厢店宅务", "机构", "宋代（左右厢店宅务）",
        "设置勾押官收管官钱", main, "官屋邸店监当局",
        "建立店宅务勾押官隶属承载节点。",
    )
    staff(w, i, office, post, main, "店宅务勾押官隶左右厢店宅务。",
          staff_type="公吏")
    finish(w, {eid, w.find_entity("左右厢店宅务", "机构")},
           "整理店宅务勾押官隶属与职掌时间链。")


def entry687():
    i, main = 687, F[687]["text"]
    w, touched = W(i), set()
    eid, ward = exact_state(
        w, i, "病坊", "机构", "北宋元祐四年十二月",
        "苏轼在杭州集公款并捐私财创办，收养疫病及老疾贫乏者",
        main, "杭州医疗救济机构", "建立杭州病坊创办节点。",
    )
    _, ward_end = exact_state(
        w, i, "病坊", "机构", "宋代（未载具体年月）",
        "改名安乐坊", main, "杭州医疗救济机构", "建立病坊改名节点。",
    )
    peace_eid, peace = exact_state(
        w, i, "安乐坊", "机构", "宋代（未载具体年月）",
        "由病坊改名", main, "杭州医疗救济机构", "建立安乐坊节点。",
    )
    relation(w, i, ward_end, peace, "前后演变", main, "病坊后改名安乐坊。")
    _, peace_end = exact_state(
        w, i, "安乐坊", "机构", "北宋崇宁三年",
        "赐名安济坊", main, "杭州医疗救济机构", "建立安乐坊赐名节点。",
    )
    relief_eid, relief = exact_state(
        w, i, "安济坊", "机构", "北宋崇宁三年",
        "由安乐坊赐名", main, "杭州医疗救济机构", "建立安济坊节点。",
    )
    relation(w, i, peace_end, relief, "前后演变", main,
             "崇宁三年安乐坊赐名安济坊。")
    residence_eid, _ = exact_state(
        w, i, "居养院", "机构", "北宋崇宁三年",
        "与安济坊同时设置，收养老疾贫乏者", main,
        "社会救济机构", "建立居养院设置节点。",
    )
    touched.update((eid, peace_eid, relief_eid, residence_eid))
    finish(w, touched, "整理病坊创办、改名安乐坊、赐名安济坊及置居养院时间链。")


def entry688():
    i, main = 688, F[688]["text"]
    w, touched = W(i), set()
    source_eid, source = support_state(
        w, i, "安济坊", "机构", "南宋绍兴十三年",
        "病坊、安乐坊、安济坊系统发展为养济院",
        main, "医疗救济机构", "建立安济坊发展为养济院的承载节点。",
    )
    eid,院 = exact_state(
        w, i, "养济院", "机构", "南宋绍兴十三年",
        "置于临安府，安置老疾贫困者及乞丐，冬春给米钱并医治疾病",
        main, "临安社会救济机构", "建立养济院创置与职掌节点。",
    )
    relation(w, i, source, 院, "前后演变", main,
             "绍兴十三年养济院由病坊、安乐坊、安济坊系统发展而来。")
    touched.update((source_eid, eid))
    finish(w, touched, "整理养济院来源、创置地点、救济对象与职掌时间链。")


def entry689():
    i = 689
    main, origin, duty, roster, alias = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别名"),
    )
    w, touched = W(i), set()
    source_eid, source = support_state(
        w, i, "太医局熟药所", "机构", "北宋熙宁九年六月",
        "神宗朝设置，后增为和剂局、惠民局",
        origin, "中央熟药机构", "建立太医局熟药所前身承载节点。", "职源与沿革",
    )
    _, source_end = exact_state(
        w, i, "太医局熟药所", "机构", "北宋崇宁中",
        "增局并改称惠民局、和剂局，后称太平惠民局", origin,
        "中央熟药机构", "建立太医局熟药所崇宁增局节点。", "职源与沿革",
    )
    eid, bureau = exact_state(
        w, i, "和剂局", "机构", "北宋崇宁中",
        "由太医局熟药所增置，配方制药供各熟药所出卖及朝廷宣赐",
        origin, "中央制药监当局", "建立和剂局始置节点。", "职源与沿革",
    )
    relation(w, i, source_end, bureau, "前后演变", origin,
             "崇宁中太医局熟药所增置和剂局。", "职源与沿革")
    _, ended = exact_state(
        w, i, "和剂局", "机构", "南宋初", "罢置", origin,
        "中央制药监当局", "建立和剂局南宋初罢置节点。", "职源与沿革",
    )
    travel_eid, travel = exact_state(
        w, i, "行在和剂局", "机构", "南宋绍兴六年正月四日",
        "复置，配方制药供惠民局出卖及朝廷宣赐",
        origin, "行在制药监当局", "建立行在和剂局复置节点。", "职源与沿革",
    )
    relation(w, i, ended, travel, "前后演变", origin,
             "绍兴六年复置行在和剂局。", "职源与沿革")
    parent_eid, parent = support_state(
        w, i, "太府寺", "机构", "南宋绍兴六年正月四日",
        "统辖行在和剂局", main, "中央财赋机构",
        "建立太府寺统辖行在和剂局节点。",
    )
    relation(w, i, parent, travel, "上下级机构", main, "和剂局隶太府寺。")
    roles = (
        ("监和剂局", "监官", 2), ("和剂局修合官", "修合官", 1),
        ("和剂局专知官", "吏", 1), ("和剂局手分", "吏", 2),
        ("和剂局库子", "吏", 1), ("和剂局秤子", "吏", 1),
        ("和剂局书手", "吏", 2), ("和剂局巡防兵士节级", "兵士", 10),
        ("和剂局搬担兵士", "兵士", 15), ("和剂局搬担兵士节级", "兵士", 1),
    )
    for title, officer, quota in roles:
        role_eid, post = exact_state(
            w, i, title, "官职", "南宋绍兴六年正月四日",
            f"行在和剂局所置{title}", roster, "和剂局官吏",
            f"建立{title}编制节点。", "编制", officer=officer,
        )
        staff(w, i, travel, post, roster, f"行在和剂局设{title}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    cite(w, "Timepoints", travel, i, duty, "补证和剂局配方制药职掌。", "职掌")
    _, old_name = exact_state(
        w, i, "和剂局", "机构", "南宋孝宗朝以后",
        "改称惠民和剂局", alias, "中央制药监当局",
        "建立和剂局孝宗后改名节点。", "别名",
    )
    renamed_eid, renamed = exact_state(
        w, i, "惠民和剂局", "机构", "南宋孝宗朝以后",
        "由和剂局改称", alias, "中央制药监当局",
        "建立惠民和剂局改称节点。", "别名",
    )
    relation(w, i, old_name, renamed, "前后演变", alias,
             "南宋孝宗朝以后和剂局改称惠民和剂局。", "别名")
    touched.update((source_eid, eid, travel_eid, parent_eid, renamed_eid))
    finish(w, touched, "整理和剂局始置、罢复、隶属、职掌、编制与改名时间链。")


def entry690():
    i, main = 690, F[690]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "和剂局修合官", "官职", "南宋绍兴六年正月四日",
        "监管和剂局配料制药", main, "和剂局差遣",
        "复用和剂局修合官并补职掌证据。", officer="修合官",
    )
    staff(w, i, tp(w, "行在和剂局", "机构", "南宋绍兴六年正月四日"),
          post, main, "和剂局修合官隶和剂局，监管配料制药。",
          quota=1, staff_type="修合官")
    finish(w, {eid}, "补证和剂局修合官隶属与职掌。")


def _medicine_four(w, i, quotation, field_name):
    group_eid, group = exact_state(
        w, i, "行在太医局熟药东、西、南、北四所", "机构",
        "南宋绍兴六年正月四日", "复置为行在太医局熟药东、西、南、北四所", quotation,
        "行在熟药所统称", "建立行在四熟药所统称节点。", field_name,
    )
    touched = {group_eid}
    for direction in ("东", "西", "南", "北"):
        title = f"行在太医局熟药{direction}所"
        eid, child = exact_state(
            w, i, title, "机构", "南宋绍兴六年正月四日",
            "行在太医局熟药东、西、南、北四所之一", quotation,
            "行在熟药所", f"建立{title}节点。", field_name,
        )
        relation(w, i, group, child, "统称与实例", quotation,
                 f"{title}是行在太医局熟药东、西、南、北四所之一。", field_name)
        touched.add(eid)
    return group, touched


def entry691():
    i = 691
    main, origin, duty, roster, short = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    source_eid, source = exact_state(
        w, i, "太医局熟药所", "机构", "北宋熙宁九年六月",
        "开局，出卖熟药", origin, "中央熟药机构",
        "建立太医局熟药所开局节点。", "职源与沿革",
    )
    _, source_end = exact_state(
        w, i, "太医局熟药所", "机构", "北宋崇宁中",
        "增局并改称惠民局、和剂局，后称太平惠民局", origin,
        "中央熟药机构", "建立熟药所增局节点。", "职源与沿革",
    )
    mercy_eid, mercy = exact_state(
        w, i, "惠民局", "机构", "北宋崇宁中",
        "太医局熟药所所增七局中的五局，出卖熟药",
        origin, "中央售药监当局", "建立惠民局节点。", "职源与沿革",
    )
    relation(w, i, source_end, mercy, "前后演变", origin,
             "崇宁间太医局熟药所增设惠民局。", "职源与沿革")
    _, mercy_end = exact_state(
        w, i, "惠民局", "机构", "北宋徽宗朝",
        "改称太平惠民局", origin, "中央售药监当局",
        "建立惠民局徽宗朝改名节点。", "职源与沿革",
    )
    eid, north = exact_state(
        w, i, "太平惠民局", "机构", "北宋徽宗朝",
        "由惠民局改称，出卖和剂局熟药以普济四方",
        origin, "中央售药监当局", "建立太平惠民局北宋节点。", "职源与沿革",
    )
    relation(w, i, mercy_end, north, "前后演变", origin,
             "徽宗朝惠民局改称太平惠民局。", "职源与沿革")
    _, north_end = exact_state(
        w, i, "太平惠民局", "机构", "南宋初", "罢置", origin,
        "中央售药监当局", "建立太平惠民局南宋初罢置节点。", "职源与沿革",
    )
    four, four_touched = _medicine_four(w, i, origin, "职源与沿革")
    touched.update(four_touched)
    four_end_eid, four_end = exact_state(
        w, i, "行在太医局熟药东、西、南、北四所", "机构",
        "南宋绍兴十八年闰八月二十三日", "改名太平惠民局",
        origin, "行在熟药所统称", "建立行在四熟药所改名节点。", "职源与沿革",
    )
    south_eid, south = exact_state(
        w, i, "太平惠民局", "机构", "南宋绍兴十八年闰八月二十三日",
        "由行在太医局熟药东、西、南、北四所改名，置五局出卖熟药",
        origin, "行在售药监当局", "建立南宋太平惠民局改名节点。", "职源与沿革",
    )
    relation(w, i, four_end, south, "前后演变", origin,
             "绍兴十八年行在熟药所改名太平惠民局。", "职源与沿革")
    parent_eid, parent = support_state(
        w, i, "太府寺", "机构", "南宋绍兴十八年闰八月二十三日",
        "统辖太平惠民局", main, "中央财赋机构",
        "建立太府寺统辖太平惠民局节点。",
    )
    relation(w, i, parent, south, "上下级机构", main, "太平惠民局隶太府寺。")
    for title in ("太平惠民南局", "太平惠民西局", "太平惠民北局",
                  "太平惠民南外局", "太平惠民北外局"):
        child_eid, child = exact_state(
            w, i, title, "机构", "南宋绍兴十八年闰八月二十三日",
            "南宋五太平惠民局之一", roster,
            "太平惠民局分局", f"建立五惠民局实例{title}。", "编制",
        )
        relation(w, i, south, child, "统称与实例", roster,
                 f"{title}是南宋五太平惠民局之一。", "编制")
        touched.add(child_eid)
    roles = (
        ("监太平惠民局", "监官"), ("太平惠民局专知", "吏"),
        ("太平惠民局书手", "吏"), ("太平惠民局卖药库子", "吏"),
    )
    for title, officer in roles:
        role_eid, post = exact_state(
            w, i, title, "官职", "南宋绍兴十八年闰八月二十三日",
            f"太平惠民局所置{title}", roster, "太平惠民局官吏",
            f"建立{title}编制节点。", "编制", officer=officer,
        )
        staff(w, i, south, post, roster, f"太平惠民局设{title}。", "编制",
              staff_type=officer)
        touched.add(role_eid)
    cite(w, "Timepoints", south, i, duty, "补证太平惠民局出卖熟药职掌。", "职掌")
    alias_note(w, i, south, short, "简称")
    touched.update((source_eid, mercy_eid, eid, four_end_eid, south_eid, parent_eid))
    finish(w, touched, "整理太平惠民局来源、罢复、改名、五局实例与官吏时间链。")


def entry692():
    i, main = 692, F[692]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "监太平惠民局", "官职", "南宋绍兴十八年闰八月二十三日",
        "领太平惠民局公事；南、西、北三局置监官，南外、北外由税官兼领",
        main, "太平惠民局监官", "复用监太平惠民局并补职掌证据。", officer="监官",
    )
    staff(w, i, tp(w, "太平惠民局", "机构", "南宋绍兴十八年闰八月二十三日"),
          post, main, "监太平惠民局领南、西、北三局公事。", staff_type="监官")
    finish(w, {eid}, "补证监太平惠民局职掌及五局分领方式。")


def entry693():
    i, main = 693, F[693]["text"]
    assert not F[i]["fields"]
    w, touched = W(i), set()
    eid, post = exact_state(
        w, i, "监行在太平惠民和剂局", "官职", "南宋",
        "总领太平惠民局、和剂局之事，或冠行在之名",
        main, "行在药局总领官", "建立监行在太平惠民和剂局节点。", officer="监官",
    )
    for title, time in (
        ("太平惠民局", "南宋绍兴十八年闰八月二十三日"),
        ("行在和剂局", "南宋绍兴六年正月四日"),
    ):
        parent = tp(w, title, "机构", time)
        staff(w, i, parent, post, main,
              f"监行在太平惠民和剂局总领{title}之事。", staff_type="监官")
    touched.add(eid)
    finish(w, touched, "整理监行在太平惠民和剂局的名称、职掌及双局隶属。")


def entry694():
    i = 694
    main, origin, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    assert main == "监当局名。"
    w, touched = W(i), set()
    eid, start = exact_state(
        w, i, "太医局熟药所", "机构", "北宋熙宁九年六月",
        "开局，出卖熟药", origin, "中央熟药监当局",
        "规范太医局熟药所开局节点。", "职源与沿革",
    )
    _, change = exact_state(
        w, i, "太医局熟药所", "机构", "北宋崇宁中",
        "增局并改称惠民局、和剂局，后称太平惠民局",
        origin, "中央熟药监当局", "规范太医局熟药所崇宁改制节点。", "职源与沿革",
    )
    for title in ("和剂局", "惠民局"):
        target_eid, target = support_state(
            w, i, title, "机构", "北宋崇宁中",
            "由太医局熟药所增置改称", origin,
            "中央药局", f"复用{title}崇宁节点并补本条证据。", "职源与沿革",
        )
        relation(w, i, change, target, "前后演变", origin,
                 f"崇宁中太医局熟药所增局并称{title}。", "职源与沿革")
        touched.add(target_eid)
    _, stopped = exact_state(
        w, i, "太医局熟药所", "机构", "南宋初", "罢置",
        origin, "中央熟药监当局", "建立太医局熟药所南宋初罢置节点。", "职源与沿革",
    )
    four, four_touched = _medicine_four(w, i, origin, "职源与沿革")
    touched.update(four_touched)
    group_eid, local = exact_state(
        w, i, "诸路州军熟药所", "机构", "南宋绍兴六年正月四日",
        "诸路常平司所在州、军设置熟药所", origin,
        "地方熟药所统称", "建立诸路州军熟药所统称节点。", "职源与沿革",
    )
    _, local_end = exact_state(
        w, i, "诸路州军熟药所", "机构", "南宋绍兴二十一年闰四月二日",
        "改称太平惠民局", origin, "地方熟药所统称",
        "建立州军熟药所改名节点。", "职源与沿革",
    )
    renamed_eid, renamed = exact_state(
        w, i, "诸路州军太平惠民局", "机构", "南宋绍兴二十一年闰四月二日",
        "由诸路州军熟药所改称", origin, "地方售药局统称",
        "建立诸路州军太平惠民局节点。", "职源与沿革",
    )
    relation(w, i, local_end, renamed, "前后演变", origin,
             "绍兴二十一年州军熟药所改称太平惠民局。", "职源与沿革")
    role_eid, post = exact_state(
        w, i, "监太医局熟药所", "官职", "南宋绍兴六年正月四日",
        "每所置一员，由文臣选人、京官或武臣小使臣充",
        roster, "太医局熟药所监官", "建立熟药所监官复置编制节点。", "编制",
        officer="监官",
    )
    staff(w, i, four, post, roster, "行在四熟药所每所置监官一员。", "编制",
          quota=4, staff_type="监官")
    for title in ("太医局熟药所专知官", "太医局熟药所书手", "太医局熟药所卖药库子"):
        servant_eid, servant = exact_state(
            w, i, title, "官职", "南宋绍兴六年正月四日",
            f"太医局熟药所所置{title}", roster, "太医局熟药所吏额",
            f"建立{title}编制节点。", "编制", officer="吏",
        )
        staff(w, i, four, servant, roster, f"行在熟药所设{title}。", "编制",
              staff_type="吏")
        touched.add(servant_eid)
    cite(w, "Timepoints", start, i, duty, "补证太医局熟药所出卖熟药职掌。", "职掌")
    alias_note(w, i, start, aliases, "简称与别名")
    touched.update((eid, group_eid, renamed_eid, role_eid))
    finish(w, touched, "整理太医局熟药所开局、改制、罢复、地方改名与官吏时间链。")


def entry695():
    i, main = 695, F[695]["text"]
    w, touched = W(i), set()
    parent_eid, parent = support_state(
        w, i, "太医局熟药所", "机构", "北宋元丰元年四月",
        "设置监官", main, "中央熟药监当局", "建立元丰监官隶属承载节点。",
    )
    eid, post = exact_state(
        w, i, "监太医局熟药所", "官职", "北宋元丰元年四月",
        "领太医局熟药所公事，由文臣选人、京官或武臣三班使臣充",
        main, "太医局熟药所监官", "建立监太医局熟药所北宋节点。", officer="监官",
    )
    staff(w, i, parent, post, main, "监太医局熟药所领本所公事。", staff_type="监官")
    touched.update((parent_eid, eid))
    finish(w, touched, "整理监太医局熟药所北宋任职、充任范围与隶属时间链。")


def entry696():
    i = 696
    main, origin, duty, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    )
    w, touched = W(i), set()
    local_eid, _ = exact_state(
        w, i, "真定府石炭务", "机构", "北宋明道元年九月二十一日",
        "废罢；此前官府已置石炭场务课利", origin,
        "地方石炭监当务", "建立最早有纪年的真定府石炭务节点。", "职源与沿革",
    )
    eid, bureau = exact_state(
        w, i, "石炭场", "机构", "北宋元丰新制",
        "京师至迟已置，官营收购石炭转卖", origin,
        "太府寺所属石炭监当场", "建立京师石炭场节点。", "职源与沿革",
    )
    parent_eid, parent = support_state(
        w, i, "太府寺", "机构", "北宋元丰新制", "统辖石炭场",
        main, "中央财赋机构", "建立太府寺统辖石炭场节点。",
    )
    relation(w, i, parent, bureau, "上下级机构", main, "石炭场隶太府寺。")
    group_eid, group = exact_state(
        w, i, "京师十二石炭场", "机构", "北宋元丰新制",
        "元丰在京十二石炭场的统称", roster,
        "京师石炭场统称", "建立京师十二石炭场统称节点。", "编制",
    )
    for number in range(1, 11):
        title = f"河南第{number}石炭场"
        child_eid, child = exact_state(
            w, i, title, "机构", "北宋元丰新制", "京师十二石炭场之一",
            roster, "京师石炭场", f"建立{title}实例。", "编制",
        )
        relation(w, i, group, child, "统称与实例", roster,
                 f"{title}是京师十二石炭场之一。", "编制")
        touched.add(child_eid)
    for title in ("抽买石炭场", "丰济石炭场"):
        child_eid, child = exact_state(
            w, i, title, "机构", "北宋元丰新制", "京师十二石炭场之一",
            roster, "京师石炭场", f"建立{title}实例。", "编制",
        )
        relation(w, i, group, child, "统称与实例", roster,
                 f"{title}是京师十二石炭场之一。", "编制")
        touched.add(child_eid)
    monitor_eid, monitor = exact_state(
        w, i, "监石炭场", "官职", "北宋元丰新制",
        "由选人充任石炭场监官", roster, "石炭场监官",
        "建立监石炭场节点。", "编制", officer="监官",
    )
    staff(w, i, bureau, monitor, roster, "石炭场置监官，由选人充。", "编制",
          staff_type="监官")
    cite(w, "Timepoints", bureau, i, duty, "补证石炭场官营收购转卖职掌。", "职掌")
    touched.update((local_eid, eid, parent_eid, group_eid, monitor_eid))
    finish(w, touched, "整理石炭场最早记载、京师设置、隶属、十二场实例与监官时间链。")


def _river_lock(i, title, event):
    main = F[i]["text"]
    w, touched = W(i), set()
    eid, lock = exact_state(
        w, i, title, "机构", "宋代（未载具体年月）", event,
        main, "太府寺所属河运税关", f"建立{title}职掌节点。",
    )
    parent_eid, parent = support_state(
        w, i, "太府寺", "机构", "宋代（未载具体年月）",
        f"统辖{title}", main, "中央财赋机构", f"建立太府寺统辖{title}节点。",
    )
    relation(w, i, parent, lock, "上下级机构", main, f"{title}隶太府寺。")
    touched.update((eid, parent_eid))
    finish(w, touched, f"整理{title}隶属与河运税关职掌时间链。")


def entry697():
    _river_lock(697, "汴河上锁", "汴河通京师税关，征免过往船载官私物及木筏税")


def entry698():
    _river_lock(698, "汴河下锁", "汴河通京师税关，职掌与汴河上锁相同")


def entry699():
    i, main = 699, F[699]["text"]
    w, touched = W(i), set()
    eid, group = exact_state(
        w, i, "汴河锁", "机构", "宋代（未载具体年月）",
        "汴河上锁、汴河下锁的连称", main,
        "汴河税关统称", "建立汴河锁统称节点。",
    )
    for title in ("汴河上锁", "汴河下锁"):
        child_eid, child = support_state(
            w, i, title, "机构", "宋代（未载具体年月）",
            "汴河上、下二锁之一", main, "太府寺所属河运税关",
            f"复用{title}节点并补连称证据。",
        )
        relation(w, i, group, child, "统称与实例", main,
                 f"{title}是汴河锁所连称的两锁之一。")
        touched.add(child_eid)
    touched.add(eid)
    finish(w, touched, "整理汴河锁统称及汴河上、下锁实例时间链。")


def entry700():
    _river_lock(700, "蔡河上锁", "蔡河通京师税关，征免过往船载官私物及木筏税")


def main():
    for i in range(681, 701):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
