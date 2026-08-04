#!/usr/bin/env python3
"""提取 chapter5t7 第1321-1340条：皇城司、禁兵、探事司与冰井务。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1301_1320 as previous


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


F = {i: load(i) for i in range(1321, 1341)}
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
    "北宋建隆二年": 961,
    "北宋太平兴国六年十一月十日": 981.87,
    "北宋真宗朝": 1010,
    "北宋天圣元年": 1023,
    "北宋天圣九年": 1031,
    "北宋前期": 1050,
    "北宋熙宁五年九月十日": 1072.69,
    "北宋熙宁五年九月十二日": 1072.70,
    "北宋熙宁六年十二月": 1073.95,
    "北宋元丰五年": 1082,
    "北宋元丰六年": 1083,
    "北宋哲宗朝": 1090,
    "北宋政和五年十一月": 1115.87,
    "南宋建炎初": 1127.1,
    "南宋绍兴元年二月三日": 1131.09,
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
              decision, field_name=None, *, entity_type="机构",
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
    relation(
        w, i, source, target, "前后演变", quotation, decision, field_name,
    )
    return source, target


def palace_staff(i, title, time, event, staff_type, *, quota=None,
                 parent="皇城司", quotation=None, field_name=None):
    quotation = quotation or F[i]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, parent, title, time, quotation,
        f"{title}为{parent}编制职事。", field_name,
        quota=quota, staff_type=staff_type,
        office_event=f"设置{title}", post_event=event,
    )
    finish(w, touched, f"整理{title}的{parent}编制隶属、职掌、序位与员额。")


def entry1321():
    i, main = 1321, F[1321]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "押队、拥队的连称，均为队一级一等职事",
        ("押队", "拥队"), main,
        "正文直接定义押拥队为押队、拥队连称。",
    )
    finish(w, touched, "建立押拥队统称及押队、拥队两个实例。")


def entry1322():
    i, main = 1322, F[1322]["text"]
    w, touched = W(i), set()
    node(
        w, touched, i, F[i]["title"], "官职", "宋代",
        "大朝会时披甲立于殿陛四角的特种禁军卫士", main,
        "朝会禁卫", "保存镇殿将军的禁军卫士性质与朝会职掌。",
        officer="禁军卫士", update_event=True,
    )
    finish(w, touched, "整理镇殿将军的禁军性质及大朝会殿陛卫护职掌。")


def entry1323():
    i, main, aliases = 1323, F[1323]["text"], field(1323, "别名")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, F[i]["title"], "机构", "宋代",
        "殿前司、侍卫亲军马军司、侍卫亲军步军司所置推狱的合称",
        ("殿前司推狱", "侍卫亲军马军司推狱", "侍卫亲军步军司推狱"),
        main, "正文明确三衙三司各置推狱。",
    )
    for parent_title, child_title in (
        ("殿前司", "殿前司推狱"),
        ("侍卫亲军马军司", "侍卫亲军马军司推狱"),
        ("侍卫亲军步军司", "侍卫亲军步军司推狱"),
    ):
        parent = node(
            w, touched, i, parent_title, "机构", "宋代",
            f"设置{child_title}", main, "三衙机构",
            f"建立{parent_title}同期承载节点。",
        )
        child = node(
            w, touched, i, child_title, "机构", "宋代",
            f"隶属{parent_title}的监狱", main, "三衙监狱",
            f"建立{child_title}。",
        )
        relation(
            w, i, parent, child, "上下级机构", main,
            f"正文明确{parent_title}置推狱。",
        )
    alias_note(w, i, group, aliases, "别名")
    finish(w, touched, "整理三衙推狱的三司实例、分别隶属及别名证据。")


def entry1324():
    i, main = 1324, F[1324]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    _, palace = evolution(
        w, touched, i, "武德司", "皇城司",
        "北宋太平兴国六年十一月十日", origin,
        "太平兴国六年十一月十日武德司改称皇城司。", "职源与沿革",
        source_event="旧名武德司，改称皇城司",
        target_event="由武德司改称，掌宫城禁卫事务",
    )
    mobile, _ = evolution(
        w, touched, i, "皇城司", "行宫禁卫所", "南宋建炎初", origin,
        "南宋初皇城司制度以行宫禁卫所名义运行。", "职源与沿革",
        source_event="南宋初改为行宫禁卫所",
        target_event="南宋建炎初设置，承接皇城禁卫事务",
    )
    evolution(
        w, touched, i, "行宫禁卫所", "行在皇城司",
        "南宋绍兴元年二月三日", origin,
        "绍兴元年二月三日行宫禁卫所改称行在皇城司。", "职源与沿革",
        source_event="一分为行在皇城司、主管禁卫所",
        target_event="由行宫禁卫所改称",
    )
    cite(w, "Timepoints", palace, i, duty, "保存皇城司宫门管钥、敕号审验及宫廷供役职掌。", "职掌")
    cite(w, "Timepoints", palace, i, roster, "保存北宋皇城司禁兵、官额、吏额及所属官司编制。", "编制")
    cite(w, "Timepoints", mobile, i, roster, "保存南宋皇城司禁兵、官额、吏额编制证据。", "编制")
    alias_note(w, i, palace, aliases, "简称与别名")
    for post_title, quota, staff_type in (
        ("亲从官", "五指挥近三千人", "禁兵"),
        ("亲事官", "六指挥", "禁兵"),
        ("入内院子", "五百人", "禁兵"),
        ("快行", "一百人（与长行合计）", "禁兵"),
        ("司圜", "三人", "禁兵"),
    ):
        post = node(
            w, touched, i, post_title, "官职", "宋代（具体年月未载）",
            f"隶皇城司，{quota}", roster, "皇城司禁兵",
            f"按皇城司编制建立{post_title}。", "编制",
        )
        generic_palace = node(
            w, touched, i, "皇城司", "机构", "宋代（具体年月未载）",
            "统辖禁兵与所属官司", roster, "皇城禁卫机构",
            "建立皇城司无具体年月的编制承载节点。", "编制",
        )
        staff(
            w, i, generic_palace, post, roster,
            f"皇城司编制明确列有{post_title}。", "编制",
            quota=quota, staff_type=staff_type,
        )
    ice = node(
        w, touched, i, "冰井务", "机构", "宋代（具体年月未载）",
        "隶皇城司", roster, "皇城司所属官司",
        "按编制建立冰井务所属节点。", "编制",
    )
    generic_palace = node(
        w, touched, i, "皇城司", "机构", "宋代（具体年月未载）",
        "统辖禁兵与所属官司", roster, "皇城禁卫机构",
        "复用皇城司无具体年月的编制承载节点。", "编制",
    )
    relation(w, i, generic_palace, ice, "上下级机构", roster,
             "编制明确冰井务为皇城司所属官司。", "编制")
    finish(w, touched, "整理皇城司从武德司到行宫禁卫所、行在皇城司的沿革及编制职掌。")


def entry1325():
    i, main, aliases = 1325, F[1325]["text"], field(1325, "简称")
    w, touched = W(i), set()
    source, target = evolution(
        w, touched, i, "武德司", "皇城司",
        "北宋太平兴国六年十一月十日", main,
        "武德司于太平兴国六年十一月十日改名皇城司。",
        source_event="旧名武德司，改称皇城司",
        target_event="由武德司改称，掌宫城禁卫事务",
    )
    alias_note(w, i, source, aliases, "简称")
    cite(w, "Timepoints", target, i, aliases, "以简称字段引文互证皇城司本名武德司及改名。", "简称")
    finish(w, touched, "以武德司词条互证太平兴国六年改称皇城司及简称。")


def entry1326():
    i, main = 1326, F[1326]["text"]
    origin = field(i, "职源与沿革")
    duty, roster = field(i, "职掌"), field(i, "编制")
    rank, aliases = field(i, "品位"), field(i, "别称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "皇城司", F[i]["title"],
        "北宋太平兴国六年十一月十日", origin,
        "皇城司设置时即置勾当官。", "职源与沿革",
        staff_type="主管官", office_event="即置勾当官",
        post_event="领皇城司公事",
    )
    cite(w, "Timepoints", post, i, duty, "保存勾当皇城司公事的禁令、宿卫、宫门与督察职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存差充资格与官品。", "品位")
    yuanfeng = node(
        w, touched, i, F[i]["title"], "官职", "北宋元丰六年",
        "官额定为十员", roster, "皇城司主管官",
        "记录元丰六年勾当官定额。", "编制", update_event=True,
    )
    palace = node(
        w, touched, i, "皇城司", "机构", "北宋元丰六年",
        "置勾当公事官十员", roster, "皇城禁卫机构",
        "建立皇城司元丰六年编制节点。", "编制",
    )
    staff(w, i, palace, yuanfeng, roster, "元丰六年勾当皇城司公事定为十员。", "编制",
          quota="十员", staff_type="主管官")
    source, target = evolution(
        w, touched, i, F[i]["title"], "干办皇城司公事", "南宋",
        origin, "南宋勾当皇城司公事改称干办皇城司公事。", "职源与沿革",
        entity_type="官职", source_event="南宋改称干办皇城司公事",
        target_event="由勾当皇城司公事改称",
    )
    alias_note(w, i, post, aliases, "别称")
    finish(w, touched, "整理勾当皇城司公事的始置、职掌、品位、元丰定额及南宋改称。")


def entry1327():
    i, main, aliases = 1327, F[1327]["text"], field(1327, "简称")
    w, touched = W(i), set()
    source, target = evolution(
        w, touched, i, "勾当皇城司公事", F[i]["title"], "南宋", main,
        "南宋将勾当皇城司公事改称干办皇城司公事。",
        entity_type="官职", source_event="南宋改称干办皇城司公事",
        target_event="由勾当皇城司公事改称",
    )
    parent = node(
        w, touched, i, "行在皇城司", "机构", "南宋",
        "置干办皇城司公事", main, "南宋皇城禁卫机构",
        "建立行在皇城司南宋编制承载节点。",
    )
    staff(w, i, parent, target, main, "干办皇城司公事为南宋皇城司机构属官。",
          quota="五员", staff_type="干办官")
    alias_note(w, i, target, aliases, "简称")
    finish(w, touched, "互证南宋勾当改干办，并整理干办官的行在皇城司隶属、员额与简称。")


def entry1328():
    palace_staff(
        1328, "提举皇城司", "南宋",
        "位在干办官之上，以资深位高者充，许直达闻奏",
        "提举官", quota="一员", parent="行在皇城司",
    )


def entry1329():
    palace_staff(
        1329, "提点皇城司", "南宋",
        "位在干办官之上、提举官之下",
        "提点官", quota="二员至六员", parent="行在皇城司",
    )


def entry1330():
    i, main = 1330, F[1330]["text"]
    w, touched = W(i), set()
    palace = node(
        w, touched, i, "皇城司", "机构", "北宋真宗朝",
        "统辖探事司", main, "皇城禁卫机构",
        "建立皇城司真宗朝承载节点。",
    )
    spy = node(
        w, touched, i, F[i]["title"], "机构", "北宋真宗朝",
        "隶皇城司，派亲事官侦探京师流言与图谋不轨者，逻卒四十人",
        main, "侦察机构", "记录探事司隶属、职掌及真宗朝编制。",
        update_event=True,
    )
    relation(w, i, palace, spy, "上下级机构", main, "正文明确探事司隶皇城司。")
    node(
        w, touched, i, F[i]["title"], "机构", "北宋哲宗朝",
        "增加编制", main, "侦察机构",
        "记录哲宗朝探事司增编。", update_event=True,
    )
    finish(w, touched, "整理皇城司探事司的隶属、侦察职掌与真宗哲宗两朝编制变化。")


def entry1331():
    i, main, aliases = 1331, F[1331]["text"], field(1331, "别称")
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "皇城司探事司", F[i]["title"], "北宋真宗朝", main,
        "逻卒为探事司亲事官，在京城伺察并按季轮换。",
        staff_type="侦察卒", office_event="派遣逻卒伺察京城",
        post_event="于京城伺察，每月给钱、每季轮换",
    )
    eid = w.find_entity(F[i]["title"], "官职")
    tid = w.find_timepoint(eid, "北宋真宗朝")
    alias_note(w, i, tid, aliases, "别称")
    finish(w, touched, "整理逻卒的探事司编制、侦察职掌、轮换给钱及别称察子。")


def entry1332():
    i, main = 1332, F[1332]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "皇城司", F[i]["title"], "宋代", main,
        "亲从官为皇城司最亲近禁兵，掌管钥契勘、巡察、宿卫与洒扫。",
        staff_type="禁兵", office_event="统辖亲从官",
        post_event="由亲事官材勇者挑选，后改招募",
    )
    post = node(
        w, touched, i, F[i]["title"], "官职", "北宋政和五年十一月",
        "皇城亲从司五指挥，共2970人", main, "皇城司禁兵",
        "记录政和五年亲从官指挥数与总兵额。", update_event=True,
    )
    palace = node(
        w, touched, i, "皇城司", "机构", "北宋政和五年十一月",
        "亲从官五指挥", main, "皇城禁卫机构",
        "建立皇城司政和五年编制节点。",
    )
    staff(w, i, palace, post, main, "政和五年皇城亲从司有五指挥、2970人。",
          quota="五指挥，共2970人", staff_type="禁兵")
    finish(w, touched, "整理亲从官的皇城司隶属、职掌、来源及政和五年编制。")


def entry1333():
    i, main = 1333, F[1333]["text"]
    w, touched = W(i), set()
    stages = (
        ("北宋前期", "三指挥，掌皇城宿卫、守门及四色敕号稽验", "三指挥"),
        ("北宋元丰五年", "增一指挥守卫景灵宫", None),
        ("北宋政和五年十一月", "增一指挥守西京大内宫，又增内园司一指挥", None),
    )
    for time, event, quota in stages:
        post = node(
            w, touched, i, F[i]["title"], "官职", time, event, main,
            "皇城司禁兵", f"记录亲事官{time}编制与职掌。", update_event=True,
        )
        palace = node(
            w, touched, i, "皇城司", "机构", time,
            f"统辖亲事官：{event}", main, "皇城禁卫机构",
            f"建立皇城司{time}编制节点。",
        )
        staff(w, i, palace, post, main, f"亲事官{time}隶皇城司。",
              quota=quota, staff_type="禁兵")
    finish(w, touched, "整理亲事官北宋前期、元丰五年、政和五年的完整编制变化链。")


def entry1334():
    i, main = 1334, F[1334]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "宋代",
        "亲从官、亲事官的连称", ("亲从官", "亲事官"), main,
        "正文直接定义亲从亲事为亲从官、亲事官连称。",
    )
    finish(w, touched, "建立亲从亲事统称及亲从官、亲事官两个实例。")


def entry1335():
    i, main = 1335, F[1335]["text"]
    w, touched = W(i), set()
    for time, event, quota in (
        ("北宋天圣元年", "拣年纪大的亲事官充，在宫内供祗候差使", "一指挥（五百人）"),
        ("北宋天圣九年", "改选六十岁以上辇官充，在宫内供祗候差使", "一指挥（五百人）"),
        ("南宋", "在宫内供祗候差使，减为一百人", "一百人"),
    ):
        post = node(w, touched, i, F[i]["title"], "官职", time, event, main,
                    "皇城司禁兵", f"记录入内院子{time}来源、职掌与编制。",
                    update_event=True)
        parent_title = "行在皇城司" if time == "南宋" else "皇城司"
        parent = node(w, touched, i, parent_title, "机构", time,
                      "统辖入内院子", main, "皇城禁卫机构",
                      f"建立{parent_title}{time}编制节点。")
        staff(w, i, parent, post, main, f"{time}入内院子隶{parent_title}。",
              quota=quota, staff_type="禁兵")
    finish(w, touched, "整理入内院子天圣元年、九年与南宋来源和兵额变化。")


def entry1336():
    palace_staff(
        1336, "守阙入内院子", "南宋",
        "拣五十至六十岁不入队三衙兵充，供内外祗应差使",
        "禁兵", parent="行在皇城司",
    )


def entry1337():
    palace_staff(
        1337, "快行", "宋代",
        "由亲从官中健步者充，供传唤及驾出仗卫等祗应差使",
        "禁兵",
    )


def entry1338():
    palace_staff(
        1338, "司圜", "宋代",
        "专事打扫皇城内厕所", "禁兵",
    )


def entry1339():
    i, main = 1339, F[1339]["text"]
    origin, duty, roster = field(i, "职源"), field(i, "职掌"), field(i, "编制")
    w, touched = W(i), set()
    for time, event in (
        ("北宋建隆二年", "设置，位于开封夷门内"),
        ("北宋熙宁五年九月十二日", "罢置"),
        ("北宋熙宁六年十二月", "复置"),
    ):
        tid = node(w, touched, i, F[i]["title"], "机构", time, event, origin,
                   "皇城司所属官局", f"记录冰井务{time}{event}。", "职源",
                   update_event=True)
        cite(w, "Timepoints", tid, i, duty, "保存冰井务藏冰、荐享及宫廷百司供冰职掌。", "职掌")
    generic_palace = node(w, touched, i, "皇城司", "机构", "宋代（具体年月未载）",
                          "统辖冰井务", main, "皇城禁卫机构",
                          "建立皇城司无具体年月所属节点。")
    generic_ice = node(w, touched, i, F[i]["title"], "机构", "宋代（具体年月未载）",
                       "隶皇城司，位于开封夷门内", main, "皇城司所属官局",
                       "记录冰井务隶属与所在。", update_event=True)
    relation(w, i, generic_palace, generic_ice, "上下级机构", main,
             "正文明确冰井务隶皇城司。")
    monitor = node(w, touched, i, "监冰井务", "官职", "宋代（具体年月未载）",
                   "由内侍充，监掌冰井务", roster, "监当官",
                   "按编制建立监冰井务官。", "编制", update_event=True)
    staff(w, i, generic_ice, monitor, roster, "冰井务设监官一人，由内侍充。", "编制",
          quota="一人", staff_type="监当官")
    node(w, touched, i, "监冰井务", "官职", "北宋熙宁五年九月十日",
         "罢监官，卒吏拨归琼林苑", roster, "监当官",
         "记录熙宁五年九月十日罢监官。", "编制", update_event=True)
    node(w, touched, i, "监冰井务", "官职", "北宋熙宁六年十二月",
         "随冰井务复置而复", roster, "监当官",
         "记录熙宁六年十二月复置监官。", "编制", update_event=True)
    finish(w, touched, "整理冰井务建隆始置、熙宁罢复、皇城司隶属、职掌及监官编制链。")


def entry1340():
    i, main = 1340, F[1340]["text"]
    w, touched = W(i), set()
    source, mobile_early = evolution(
        w, touched, i, "皇城司", "行宫禁卫所", "南宋建炎初", main,
        "建炎初以皇城司官权领主管禁卫所，称行宫禁卫所。",
        source_event="南宋初改为行宫禁卫所",
        target_event="南宋建炎初设置，承接皇城禁卫事务",
    )
    mobile_late, residence = evolution(
        w, touched, i, "行宫禁卫所", "行在皇城司",
        "南宋绍兴元年二月三日", main,
        "绍兴元年二月三日行宫禁卫所改为行在皇城司。",
        source_event="一分为行在皇城司、主管禁卫所",
        target_event="由行宫禁卫所改称",
    )
    supervisor_early = node(
        w, touched, i, "主管禁卫所主管官", "官职", "南宋建炎初",
        "由皇城司官权领，主管行宫禁卫所", main, "禁卫所主管官",
        "建立建炎初主管禁卫所。", officer="主管官", update_event=True,
    )
    staff(w, i, mobile_early, supervisor_early, main,
          "建炎初差皇城司官权领主管行宫禁卫所。",
          quota="一员", staff_type="主管官")
    supervisor_after = node(
        w, touched, i, "主管禁卫所主管官", "官职", "南宋绍兴元年二月三日",
        "机构改名行在皇城司后仍置一员", main, "禁卫所主管官",
        "保存机构改名后主管禁卫所官继续设置。", officer="主管官",
        update_event=True,
    )
    staff(w, i, residence, supervisor_after, main,
          "行宫禁卫所改名后，禁卫所主管官仍置一员。",
          quota="一员", staff_type="主管官")
    finish(w, touched, "整理行宫禁卫所建炎设置、绍兴改名及主管官跨机构改名继续存在。")


def main():
    for i in range(1321, 1341):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
