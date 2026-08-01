#!/usr/bin/env python3
"""提取 chapter5t7 第581-600条：仓场吏役、园苑与四排岸司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_561_580 as previous


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


F = {i: load(i) for i in range(581, 601)}
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
    "宋初": 960, "北宋建隆三年": 962,
    "北宋（元丰改制前）": 1000,
    "北宋（先隶三司）": 1000.1,
    "北宋（四园苑选官提举后）": 1070,
    "北宋熙宁四年八月四日": 1071.60,
    "北宋熙宁九年四月十三日": 1076.28,
    "北宋元丰中": 1080, "北宋元丰新制": 1082.1,
    "北宋元祐六年八月": 1091.62,
    "北宋绍圣元年": 1094,
    "宋代（提点仓场所吏额）": 1050,
    "宋代（诸仓草料场）": 1050.1,
    "宋代（诸仓脚子）": 1050.2,
    "南宋": 1127, "南宋（诸省仓）": 1150,
    "南宋（仓草场顶替执役）": 1150.1,
    "南宋孝宗朝": 1170, "南宋理宗后": 1230,
    "北宋（改名前，年月未载）": 1000.2,
    "北宋（由含芳苑改名后）": 1000.3,
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


def office_staff_parent(w, i, quotation):
    eid, parent = exact_state(
        w, i, "提点在京仓草场所", "机构", "宋代（提点仓场所吏额）",
        "置手分、后行等吏员，负责仓场点检、催驱、计帐等事务",
        quotation, "仓草场主管机构", "建立提点仓场所无明确年月的吏额承载节点。",
    )
    return eid, parent


def entry581():
    i, main = 581, F[581]["text"]
    w, touched = W(i), set()
    office = tp(w, "都大提点在京仓草场司", "机构", "宋前期（未载具体年月）")
    eid, post = exact_state(
        w, i, "都大提点在京仓草场", "官职", "宋前期（未载具体年月）",
        "总辖在京粮仓、草料场，品秩高于提点官，独自签书提点官所申公事",
        main, "都大提点司长官", "建立都大提点在京仓草场差遣及职掌。",
        officer="横行使副差遣", grade="品秩高于提点官",
    )
    staff(w, i, office, post, main, "都大提点司由横行使、副差领都大提点官。",
          staff_type="都大提点官")
    touched.add(eid)
    finish(w, touched, "整理都大提点在京仓草场差遣、品秩与职掌时间链。")


def entry582():
    i, main = 582, F[582]["text"]
    w, touched = W(i), set()
    parent_eid, parent = office_staff_parent(w, i, main)
    eid, clerk = exact_state(
        w, i, "手分", "官职", "宋代（提点仓场所吏额）",
        "往来诸仓库务及四河卸纳纲船处，点检并催驱发遣粮草、钱谷官物",
        main, "提点仓场所吏员", "建立提点仓场所手分职掌节点。", officer="吏",
    )
    staff(w, i, parent, clerk, main, "提点仓场所置手分。", staff_type="吏")
    touched.update((parent_eid, eid))
    finish(w, touched, "整理提点仓场所手分职掌与隶属时间链。")


def entry583():
    i, main = 583, F[583]["text"]
    w, touched = W(i), set()
    parent_eid, parent = office_staff_parent(w, i, main)
    eid, clerk = exact_state(
        w, i, "后行", "官职", "宋代（提点仓场所吏额）",
        "由正名贴司中拣试通晓书算者充，掌计帐核算，编制五人",
        main, "提点仓场所吏员", "建立提点仓场所后行职掌与定额。", officer="吏",
    )
    staff(w, i, parent, clerk, main, "提点仓场所置后行五人。",
          quota=5, staff_type="吏")
    touched.update((parent_eid, eid))
    finish(w, touched, "整理提点仓场所后行职掌、资格与定额时间链。")


def warehouse_yard_staff(i, title, event, *, grade=None):
    main = F[i]["text"]
    w, touched = W(i), set()
    eid, post = exact_state(
        w, i, title, "官职", "宋代（诸仓草料场）", event,
        main, "仓草场吏员", f"建立诸仓草料场{title}职掌节点。",
        officer="吏", grade=grade,
    )
    for parent_title, parent_time in (
        ("司农寺仓", "宋代（司农寺仓）"),
        ("司农寺草料场", "宋代（司农寺草料场）"),
    ):
        staff(w, i, tp(w, parent_title, "机构", parent_time), post, main,
              f"诸{parent_title}均置{title}。", staff_type="吏")
    touched.add(eid)
    finish(w, touched, f"整理诸仓草料场{title}职掌与隶属时间链。")


def entry584():
    warehouse_yard_staff(584, "专知官", "主持给纳官物事务")


def entry585():
    warehouse_yard_staff(585, "副知", "位次专知官，主持给纳官物事务",
                         grade="位次于专知官")


def entry586():
    i, main = 586, F[586]["text"]
    w, touched = W(i), set()
    eid, substitute = exact_state(
        w, i, "衙前", "官职", "南宋（仓草场顶替执役）",
        "仓、草场专知或副知缺员时，由临安府系籍正额衙前上名者顶替，主持官物给纳",
        main, "州府役吏", "建立衙前顶替仓草场专副知节点。", officer="役吏",
    )
    for parent_title, parent_time in (
        ("司农寺仓", "宋代（司农寺仓）"),
        ("司农寺草料场", "宋代（司农寺草料场）"),
    ):
        staff(w, i, tp(w, parent_title, "机构", parent_time), substitute, main,
              f"{parent_title}专知、副知缺员时以衙前临时顶替。",
              staff_type="临时顶替役吏")
    touched.add(eid)
    finish(w, touched, "整理衙前仓草场临时顶替职掌时间链。")


def entry587():
    i, main = 587, F[587]["text"]
    w = W(i)
    eid, laborer = exact_state(
        w, i, "脚子", "官职", "宋代（诸仓脚子）",
        "专职从纲船卸货并搬运入仓", main, "仓场公人",
        "建立诸仓脚子职掌节点。", officer="役人",
    )
    staff(w, i, tp(w, "司农寺仓", "机构", "宋代（司农寺仓）"), laborer,
          main, "诸仓置脚子承担卸货搬运。", staff_type="役人")
    finish(w, {eid}, "整理诸仓脚子职掌与隶属时间链。")


def entry588():
    i, main = 588, F[588]["text"]
    w, touched = W(i), set()
    eid, named = exact_state(
        w, i, "攒司", "官职", "北宋元丰中",
        "始有此吏名，由经书算考试合格者选补，掌记帐事务",
        main, "仓场吏员", "建立攒司名称出现及资格职掌节点。", officer="吏",
    )
    warehouse_eid, warehouses = exact_state(
        w, i, "诸省仓", "机构", "南宋（诸省仓）",
        "南宋诸省仓皆置攒司", main, "地方仓储机构",
        "建立南宋诸省仓攒司编制承载节点。",
    )
    _, south = exact_state(
        w, i, "攒司", "官职", "南宋（诸省仓）",
        "诸省仓皆置，掌记帐等事务", main, "仓场吏员",
        "建立南宋诸省仓攒司节点。", officer="吏",
    )
    staff(w, i, warehouses, south, main, "南宋诸省仓皆置攒司。", staff_type="吏")
    touched.update((eid, warehouse_eid))
    finish(w, touched, "整理攒司名称、选补、职掌及南宋隶属时间链。")


def entry589():
    i, main = 589, F[589]["text"]
    w, touched = W(i), set()
    eid, restored = exact_state(
        w, i, "提辖修仓所", "机构", "北宋元祐六年八月",
        "复置，掌修葺在京诸仓屋宇", main, "司农寺属修仓机构",
        "建立提辖修仓所复置与职掌节点。",
    )
    agriculture_eid, agriculture = exact_state(
        w, i, "司农寺", "机构", "北宋元祐六年八月",
        "所辖提辖修仓所掌修葺在京诸仓屋宇", main, "九寺之一",
        "建立司农寺同期承载节点。",
    )
    relation(w, i, agriculture, restored, "上下级机构", main,
             "元祐六年复置提辖修仓所，由司农寺统辖。")
    _, abolished = exact_state(
        w, i, "提辖修仓所", "机构", "北宋绍圣元年",
        "罢置，修仓职事归将作监", main, "司农寺属修仓机构",
        "建立绍圣元年罢置节点。",
    )
    works_eid, works = exact_state(
        w, i, "将作监", "机构", "北宋绍圣元年",
        "接收提辖修仓所修葺在京诸仓屋宇的职事", main, "营造机构",
        "建立将作监接收修仓职事节点。",
    )
    relation(w, i, abolished, works, "前后演变", main,
             "绍圣元年提辖修仓所罢，修仓职事归将作监。")
    touched.update((eid, agriculture_eid, works_eid))
    finish(w, touched, "整理提辖修仓所复置、职掌、隶属与罢归将作监时间链。")


def entry590():
    i, main = 590, F[590]["text"]
    w, touched = W(i), set()
    eid = canonicalize_entity(
        w, "司农寺园苑", "四园苑", "机构",
        "以正式词头‘四园苑’规范第559条预建的同一园苑总称实体。",
    )
    _, early = exact_state(
        w, i, "四园苑", "机构", "北宋（先隶三司）",
        "京师四大御花园总称，掌种植时花鲜果供进并修筑亭阁备游幸，先隶三司",
        main, "御花园统称", "建立四园苑宋前期职掌与隶属节点。",
    )
    relation(w, i, tp(w, "三司", "机构", "宋初"), early,
             "上下级机构", main, "四园苑先隶三司。")
    supervisor_eid, supervisor = exact_state(
        w, i, "提举司", "机构", "北宋（四园苑选官提举后）",
        "选差官提举四园苑，四园苑不再隶三司", main,
        "四园苑主管机构", "建立四园苑提举司节点。",
    )
    _, supervised = exact_state(
        w, i, "四园苑", "机构", "北宋（四园苑选官提举后）",
        "选差官提举，不再隶三司", main, "御花园统称",
        "建立四园苑改隶提举司节点。",
    )
    relation(w, i, supervisor, supervised, "上下级机构", main,
             "选差官提举后四园苑隶提举司。")
    _, reform = exact_state(
        w, i, "四园苑", "机构", "北宋元丰新制",
        "改隶司农寺，掌种植时花鲜果供进及修筑亭阁备游幸",
        main, "司农寺所属园苑", "规范元丰新制后隶属与职掌。",
    )
    relation(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "四园苑后隶司农寺。")
    instances = (
        ("玉津园", "北宋", "京师四大御花园之一"),
        ("瑞圣苑", "北宋（由含芳苑改名后）",
         "由含芳苑改名，为京师四大御花园之一"),
        ("宜春苑", "北宋", "京师四大御花园之一"),
        ("琼林苑", "北宋", "京师四大御花园之一"),
    )
    for title, time, event in instances:
        seid, instance = exact_state(
            w, i, title, "机构", time, event, main, "御花园",
            f"建立{title}为四园苑实例。",
        )
        relation(w, i, early, instance, "统称与实例", main,
                 f"{title}是北宋四园苑之一。")
        _, supervised_instance = exact_state(
            w, i, title, "机构", "北宋（四园苑选官提举后）",
            f"随四园苑改隶提举司，仍为四园苑之一", main, "御花园",
            f"建立{title}改隶提举司同期实例节点。",
        )
        relation(w, i, supervised, supervised_instance, "统称与实例", main,
                 f"四园苑改隶提举司后，{title}仍为其具体实例。")
        _, reform_instance = exact_state(
            w, i, title, "机构", "北宋元丰新制",
            f"随四园苑改隶司农寺，仍为四园苑之一", main, "御花园",
            f"建立{title}元丰新制同期实例节点。",
        )
        relation(w, i, reform, reform_instance, "统称与实例", main,
                 f"元丰新制四园苑改隶司农寺后，{title}仍为其具体实例。")
        touched.add(seid)
    touched.update((eid, supervisor_eid))
    finish(w, touched, "整理四园苑职掌、三次隶属及四园实例完整时间链。")


def garden_entry(i, title, event):
    main = F[i]["text"]
    w = W(i)
    eid, garden = exact_state(
        w, i, title, "机构", "北宋", event, main, "御花园",
        f"补充{title}北宋四园苑实例证据。",
    )
    relation(w, i, tp(w, "四园苑", "机构", "北宋（先隶三司）"), garden,
             "统称与实例", main, f"{title}是北宋四园苑之一。")
    finish(w, {eid}, f"整理{title}四园苑实例时间链。")


def entry591():
    i, main = 591, F[591]["text"]
    w = W(i)
    eid, north = exact_state(
        w, i, "玉津园", "机构", "北宋", "京师四大御花园之一",
        main, "御花园", "补充玉津园北宋实例证据。",
    )
    relation(w, i, tp(w, "四园苑", "机构", "北宋（先隶三司）"), north,
             "统称与实例", main, "玉津园是北宋四园苑之一。")
    _, south = exact_state(
        w, i, "玉津园", "机构", "南宋", "在临安沿置",
        main, "御花园", "建立玉津园南宋沿置节点。",
    )
    finish(w, {eid}, "整理玉津园北宋实例与南宋沿置时间链。")


def entry592():
    i, main = 592, F[592]["text"]
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, "含芳苑", "机构", "北宋（改名前，年月未载）",
        "瑞圣苑原名", main, "御花园", "建立含芳苑前身节点。",
    )
    eid, renamed = exact_state(
        w, i, "瑞圣苑", "机构", "北宋（由含芳苑改名后）",
        "由含芳苑改名，为京师四大御花园之一", main, "御花园",
        "规范瑞圣苑改名后节点。",
    )
    relation(w, i, old, renamed, "前后演变", main, "含芳苑改名瑞圣苑。")
    relation(w, i, tp(w, "四园苑", "机构", "北宋（先隶三司）"), renamed,
             "统称与实例", main, "瑞圣苑是北宋四园苑之一。")
    touched.update((old_eid, eid))
    finish(w, touched, "整理含芳苑改名瑞圣苑及四园实例时间链。")


def entry593():
    garden_entry(593, "宜春苑", "京师四大御花园之一")


def entry594():
    garden_entry(594, "琼林苑", "京师四大御花园之一")


def entry595():
    i, main, aliases = 595, F[595]["text"], field(595, "别名")
    w = W(i)
    eid, created = exact_state(
        w, i, "聚景园", "机构", "南宋孝宗朝",
        "建于临安清波门外，供太上皇赵构休养",
        main, "南宋京师御花园", "建立聚景园建置、位置与用途节点。",
    )
    _, declined = exact_state(
        w, i, "聚景园", "机构", "南宋理宗后", "罕临幸，日渐荒落",
        main, "南宋京师御花园", "建立理宗后荒落节点。",
    )
    alias_note(w, i, created, aliases, "别名")
    finish(w, {eid}, "整理聚景园建置、用途、荒落及别名时间链。")


def entry596():
    i, main, aliases = 596, F[596]["text"], field(596, "简称")
    w, touched = W(i), set()
    eid = canonicalize_entity(
        w, "司农寺排岸司", "四排岸司", "机构",
        "以正式词头‘四排岸司’规范第559条预建的同一排岸司总称实体。",
    )
    _, early = exact_state(
        w, i, "四排岸司", "机构", "北宋（元丰改制前）",
        "京东、京南、京西、京北排岸司总称，掌水运纲船送纳、雇直，隶提点在京仓草场所",
        main, "排岸司统称", "建立四排岸司元丰前职掌与隶属节点。",
    )
    relation(w, i, tp(w, "提点在京仓草场所", "机构", "宋前期（置所年月未载）"),
             early, "上下级机构", main, "四排岸司元丰改制前隶提点在京仓草场所。")
    _, reform = exact_state(
        w, i, "四排岸司", "机构", "北宋元丰新制",
        "改隶司农寺，统辖京东、京南、京西、京北四排岸司",
        main, "司农寺所属排岸司", "规范元丰新制后隶属与实例。",
    )
    relation(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "四排岸司元丰改制后隶司农寺。")
    instances = (
        ("京东排岸司",
         "设于开封广济坊，掌汴河东运及长江、淮河等水路粮纲输送、搬卸、入仓；"
         "隶提点在京仓草场所"),
        ("京南排岸司",
         "设于开封建宁坊，掌惠民河、蔡河纲船运输、下卸、入仓；"
         "隶提点在京仓草场所"),
        ("京西排岸司",
         "设于开封顺城坊，掌汴河上锁粮纲与杂货运输、下卸、入仓；"
         "隶提点在京仓草场所"),
        ("京北排岸司",
         "隶提点在京仓草场所，领广济河纲船运输、下卸、入仓、雇直"),
    )
    for title, event in instances:
        seid, instance = exact_state(
            w, i, title, "机构", "北宋（元丰改制前）",
            event, main, "监当局", f"建立{title}为四排岸司实例。",
        )
        relation(w, i, early, instance, "统称与实例", main,
                 f"{title}是四排岸司的具体实例。")
        touched.add(seid)
    alias_note(w, i, early, aliases, "简称")
    touched.add(eid)
    finish(w, touched, "整理四排岸司职掌、隶属与四司实例完整时间链。")


def bank_office_base(i, title, location, duty, aliases, alias_field):
    main = F[i]["text"]
    w, touched = W(i), set()
    eid, early = exact_state(
        w, i, title, "机构", "北宋（元丰改制前）",
        f"设于{location}，{duty}；隶提点在京仓草场所",
        main, "监当局", f"建立{title}元丰前位置、职掌与隶属节点。",
    )
    relation(w, i, tp(w, "提点在京仓草场所", "机构", "宋前期（置所年月未载）"),
             early, "上下级机构", main, f"{title}元丰改制前隶提点在京仓草场所。")
    relation(w, i, tp(w, "四排岸司", "机构", "北宋（元丰改制前）"), early,
             "统称与实例", main, f"{title}是四排岸司的具体实例。")
    _, reform = exact_state(
        w, i, title, "机构", "北宋元丰新制",
        f"改隶司农寺，继续{duty}", main, "司农寺所属监当局",
        f"建立{title}元丰改制后隶属节点。",
    )
    relation(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, f"{title}元丰改制后隶司农寺。")
    relation(w, i, tp(w, "四排岸司", "机构", "北宋元丰新制"), reform,
             "统称与实例", main, f"{title}在元丰新制后仍是四排岸司的具体实例。")
    if aliases:
        alias_note(w, i, early, aliases, alias_field)
    touched.add(eid)
    return w, touched, early, reform


def entry597():
    i, main, aliases = 597, F[597]["text"], field(597, "简称与别名")
    w, touched, early, reform = bank_office_base(
        i, "京东排岸司", "开封广济坊",
        "掌汴河东运及长江、淮河等水路粮纲输送、搬卸、入仓",
        aliases, "简称与别名",
    )
    post_eid, post = exact_state(
        w, i, "勾当京东排岸司", "官职", "北宋（元丰改制前）",
        "文臣、武臣各一人共同勾当，编制二人", main, "排岸司监当官",
        "建立勾当京东排岸司官定额。", officer="监当官",
    )
    staff(w, i, early, post, main, "京东排岸司置勾当官二人，文武各一。",
          quota=2, staff_type="文武监当官")
    unit_eid, unit = exact_state(
        w, i, "京东排岸司广济装卸役卒", "机构", "北宋（元丰改制前）",
        "所属装卸役卒五指挥", main, "装卸役卒",
        "建立京东排岸司所属五指挥。",
    )
    relation(w, i, early, unit, "上下级机构", main,
             "京东排岸司下辖广济装卸役卒五指挥。")
    touched.update((post_eid, unit_eid))
    finish(w, touched, "整理京东排岸司位置、职掌、隶属、监当官与役卒时间链。")


def entry598():
    i, main, aliases = 598, F[598]["text"], field(598, "简称")
    w, touched, early, reform = bank_office_base(
        i, "京西排岸司", "开封顺城坊",
        "掌汴河上锁粮纲与杂货运输、下卸、入仓",
        aliases, "简称",
    )
    post_eid, post = exact_state(
        w, i, "勾当京西排岸司", "官职", "北宋（元丰改制前）",
        "以京官或朝官一人勾当", main, "排岸司监当官",
        "建立勾当京西排岸司官定额。", officer="文臣监当官",
    )
    staff(w, i, early, post, main, "京西排岸司置京官或朝官一人勾当。",
          quota=1, staff_type="文臣监当官")
    labor_eid, labor = exact_state(
        w, i, "京西排岸司装卸役卒", "官职", "北宋（元丰改制前）",
        "下辖装卸役卒五百零二人", main, "排岸司役卒",
        "建立京西排岸司装卸役卒定额。", officer="役卒",
    )
    staff(w, i, early, labor, main, "京西排岸司下辖装卸役卒五百零二人。",
          quota=502, staff_type="役卒")
    touched.update((post_eid, labor_eid))
    finish(w, touched, "整理京西排岸司位置、职掌、隶属、监当官与役卒时间链。")


def entry599():
    i, main, aliases = 599, F[599]["text"], field(599, "简称")
    w, touched, early, reform = bank_office_base(
        i, "京南排岸司", "开封建宁坊",
        "掌惠民河、蔡河纲船运输、下卸、入仓",
        aliases, "简称",
    )
    post_eid, post = exact_state(
        w, i, "勾当京南排岸司", "官职", "北宋（元丰改制前）",
        "由文臣一员勾当", aliases, "排岸司监当官",
        "建立勾当京南排岸司官定额。", "简称", officer="文臣监当官",
    )
    staff(w, i, early, post, aliases, "京南排岸司置文臣一员勾当。", "简称",
          quota=1, staff_type="文臣监当官")
    labor_eid, labor = exact_state(
        w, i, "京南排岸司广济役卒", "官职", "北宋（元丰改制前）",
        "辖广济两指挥役卒一千人", main, "排岸司役卒",
        "建立京南排岸司广济役卒定额。", officer="役卒",
    )
    staff(w, i, early, labor, main, "京南排岸司辖广济两指挥役卒一千人。",
          quota=1000, staff_type="役卒")
    touched.update((post_eid, labor_eid))
    finish(w, touched, "整理京南排岸司位置、职掌、隶属、监当官与役卒时间链。")


def entry600():
    i, main = 600, F[600]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    eid, created = exact_state(
        w, i, "京北排岸司", "机构", "北宋建隆三年",
        "始置于开封崇庆坊", origin, "监当局",
        "建立京北排岸司始置节点。", "职源",
    )
    cite(w, "Timepoints", created, i, main, "补充京北排岸司先后隶属与位置。")
    _, early = exact_state(
        w, i, "京北排岸司", "机构", "北宋（元丰改制前）",
        "隶提点在京仓草场所，领广济河纲船运输、下卸、入仓、雇直",
        main, "监当局", "建立京北排岸司元丰前职掌与隶属节点。",
    )
    cite(w, "Timepoints", early, i, duty, "补充京北排岸司职掌。", "职掌")
    relation(w, i, tp(w, "提点在京仓草场所", "机构", "宋前期（置所年月未载）"),
             early, "上下级机构", main, "京北排岸司元丰改制前隶提点在京仓草场所。")
    relation(w, i, tp(w, "四排岸司", "机构", "北宋（元丰改制前）"), early,
             "统称与实例", main, "京北排岸司是四排岸司的具体实例。")
    _, merged = exact_state(
        w, i, "京北排岸司", "机构", "北宋熙宁四年八月四日",
        "归京西排岸司就便管勾", roster, "监当局",
        "建立熙宁四年归京西管勾节点。", "编制",
    )
    west_eid, west = exact_state(
        w, i, "京西排岸司", "机构", "北宋熙宁四年八月四日",
        "就便管勾京北排岸司", roster, "监当局",
        "建立京西排岸司兼管京北节点。", "编制",
    )
    relation(w, i, west, merged, "上下级机构", roster,
             "熙宁四年京北排岸司归京西排岸司就便管勾。", "编制")
    _, restored = exact_state(
        w, i, "京北排岸司", "机构", "北宋熙宁九年四月十三日",
        "复置京北排岸司管勾官一员", roster, "监当局",
        "建立熙宁九年复置节点。", "编制",
    )
    post_eid, post = exact_state(
        w, i, "勾当京北排岸司", "官职", "北宋熙宁九年四月十三日",
        "复置一员", roster, "排岸司监当官",
        "建立勾当京北排岸司官定额。", "编制", officer="监当官",
    )
    staff(w, i, restored, post, roster, "熙宁九年复置京北排岸司官一员。",
          "编制", quota=1, staff_type="监当官")
    unit_eid, unit = exact_state(
        w, i, "京北排岸司广济十五指挥", "机构", "北宋（元丰改制前）",
        "下辖广济十五指挥，元额七千五百人", roster, "排岸司役卒单位",
        "建立京北排岸司广济十五指挥及元额。", "编制",
    )
    relation(w, i, early, unit, "上下级机构", roster,
             "京北排岸司下辖广济十五指挥，元额七千五百人。", "编制")
    _, reform = exact_state(
        w, i, "京北排岸司", "机构", "北宋元丰新制",
        "改隶司农寺，领广济河纲船运输、下卸、入仓、雇直",
        main, "司农寺所属监当局", "建立元丰新制后隶属节点。",
    )
    relation(w, i, tp(w, "司农寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "京北排岸司元丰改制后隶司农寺。")
    relation(w, i, tp(w, "四排岸司", "机构", "北宋元丰新制"), reform,
             "统称与实例", main, "京北排岸司在元丰新制后仍是四排岸司的具体实例。")
    alias_note(w, i, created, aliases, "简称")
    touched.update((eid, west_eid, post_eid, unit_eid))
    finish(w, touched, "整理京北排岸司始置、职掌、管勾变化、编制与隶属时间链。")


def main():
    assert [F[i]["title"] for i in range(581, 601)] == [
        "都大提点在京仓草场", "手分", "后行", "专知官", "副知",
        "衙前", "脚子", "攒司", "提辖修仓所", "四园苑", "玉津园",
        "瑞圣苑", "宜春苑", "琼林苑", "聚景园", "四排岸司",
        "京东排岸司", "京西排岸司", "京南排岸司", "京北排岸司",
    ]
    for i in range(581, 601):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
