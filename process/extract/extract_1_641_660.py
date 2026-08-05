#!/usr/bin/env python3
"""提取第一编第641-660条：翰林天文属员、图画院与御书院。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
MERGED_DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db")
)


SOUTH_IMPERIAL_LIBRARY_STAFF = (
    ("干办翰林御书院", "干办官", "一员"),
    ("翰林御书院押宿官", "押宿官", "二员"),
    ("翰林御书院书写待诏", "技术官", "三人"),
    ("翰林御书院书艺学", "技术官", "七人"),
    ("翰林御书院书学祗候", "技术官", "十四人"),
    ("翰林御书院书学生", "学生", "不限员（无俸给）"),
    ("翰林御书院弹琴祗应人", "祗应人", "一名"),
    ("翰林御书院着棋祗应人", "祗应人", "一名"),
    ("翰林御书院擘阮祗应人", "祗应人", "一名"),
    ("翰林御书院镌字祗应人", "祗应人", "三人"),
    ("翰林御书院点笔班祗应人", "祗应人", "一名"),
    ("翰林御书院描边花祗应人", "祗应人", "一名"),
    ("翰林御书院装界祗应人", "祗应人", "三人"),
    ("翰林御书院造墨祗应人", "祗应人", "一名"),
    ("翰林御书院雕字祗应人", "祗应人", "二人"),
    ("翰林御书院画细文祗应人", "祗应人", "一名"),
    ("翰林御书院打碑祗应人", "祗应人", "二人"),
    ("翰林御书院砑纸兼印书祗应人", "祗应人", "二人"),
    ("翰林御书院系笔祗应人", "祗应人", "三人"),
    ("翰林御书院系飞白笔祗应人", "祗应人", "一名"),
    ("翰林御书院造琴、阮祗应人", "祗应人", "一名"),
    ("翰林御书院裁缝祗应人", "祗应人", "一名"),
    ("翰林御书院漆作祗应人", "祗应人", "一名"),
    ("翰林御书院小木祗应人", "祗应人", "一名"),
    ("翰林御书院镞作祗应人", "祗应人", "一名"),
    ("翰林御书院剪字祗应人", "祗应人", "一名"),
    ("翰林御书院钑作祗应人", "祗应人", "一名"),
    ("翰林御书院专知官", "胥吏", "一名"),
    ("翰林御书院前行兼副专知", "胥吏", "一名"),
    ("翰林御书院后行", "胥吏", "二人"),
    ("翰林御书院贴司", "胥吏", "二人"),
    ("翰林御书院库子", "胥吏", "四人"),
    ("翰林御书院背印、守门、投送文字亲事官", "亲事官", "共四人"),
    ("翰林御书院杂役兵士", "杂役兵士", "十人（内节级二人）"),
)


def repair_dictionary_source():
    """据原书第77-78页恢复#658并修复本批明显OCR。"""
    text658 = "即勾当翰林御书院。南宋时改名。"
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            for entry_id in (641, 642):
                row = conn.execute(f"SELECT title FROM {table} WHERE id=?", (entry_id,)).fetchone()
                assert row and row[0]
                conn.execute(
                    f"UPDATE {table} SET title=? WHERE id=?",
                    (row[0].replace("(局)", "（局）"), entry_id),
                )

            row = conn.execute(f"SELECT text,fields FROM {table} WHERE id=649").fetchone()
            assert row and row[0] and row[1]
            f649 = json.loads(row[1])
            f649["职源与沿革"] = (
                f649["职源与沿革"].replace("元年(984)", "元年（984）")
            )
            conn.execute(
                f"UPDATE {table} SET text=?,fields=? WHERE id=649",
                (
                    row[0].replace("五年(1073—1082)", "五年（1073—1082）"),
                    json.dumps(f649, ensure_ascii=False),
                ),
            )

            row = conn.execute(f"SELECT text,fields FROM {table} WHERE id=655").fetchone()
            assert row and row[0] and row[1]
            f655 = json.loads(row[1])
            f655["编制"] = (
                f655["编制"]
                .replace("于办官一员", "干办官一员")
                .replace("剪字一名，镞作一名", "剪字一名，钑作一名")
            )
            conn.execute(
                f"UPDATE {table} SET text=?,fields=? WHERE id=655",
                (row[0].rstrip("。") + "。", json.dumps(f655, ensure_ascii=False)),
            )

            row = conn.execute(f"SELECT fields FROM {table} WHERE id=657").fetchone()
            assert row and row[0]
            f657 = json.loads(row[0])
            f657["别称"] = f657["别称"].split("干办翰林御书院", 1)[0].rstrip()
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=657",
                (json.dumps(f657, ensure_ascii=False),),
            )
            conn.execute(
                f"UPDATE {table} SET title=?,text=?,fields=NULL WHERE id=658",
                ("干办翰林御书院", text658),
            )

            row = conn.execute(f"SELECT fields FROM {table} WHERE id=659").fetchone()
            assert row and row[0]
            f659 = json.loads(row[0])
            f659["职源"] = f659["职源"].replace("七年(982)", "七年（982）")
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=659",
                (json.dumps(f659, ensure_ascii=False),),
            )
            row = conn.execute(f"SELECT fields FROM {table} WHERE id=660").fetchone()
            assert row and row[0]
            f660 = json.loads(row[0])
            f660["简称与别名"] = f660["简称与别名"].replace("卷68已未", "卷68己未")
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=660",
                (json.dumps(f660, ensure_ascii=False),),
            )


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(641, 661)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def field(i, name):
    value = F[i]["fields"][name]
    assert value
    return value


def C(i, name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{name}字段）" if name else "")


def cite(w, table, target_id, i, quotation, decision, name=None, **kwargs):
    source = field(i, name) if name else F[i]["text"]
    assert quotation in source, (i, name, quotation)
    return w.citation(table, target_id, C(i, name), quotation, decision, **kwargs)


def timepoint(
    w, i, entity_id, time, event, quotation, decision, name=None,
    category=None, officer_type=None, grade=None, chain="tail", **cite_kwargs,
):
    tid = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer_type,
        attr_grade=grade, chain=chain,
    )
    cite(w, "Timepoints", tid, i, quotation, decision, name, **cite_kwargs)
    return tid


def relation(
    w, i, subject, object_, kind, quotation, decision, name=None,
    staff_type=None, staff_quota=None, **cite_kwargs,
):
    rid = w.relationship(
        subject, object_, kind, decision, quotation,
        staff_type=staff_type, staff_quota=staff_quota,
    )
    cite(w, "Relationships", rid, i, quotation, decision, name, **cite_kwargs)
    return rid


def find_entity(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def find_tp(w, title, time, type_=None):
    eid = find_entity(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


def distinct_entity(w, title, type_, quotation, decision):
    row = w.conn.execute(
        "SELECT id FROM Entities WHERE title=? AND type=? AND quotation=? ORDER BY id LIMIT 1",
        (title, type_, quotation),
    ).fetchone()
    if row:
        return row[0]
    return w._insert(
        "INSERT INTO Entities (title,type,quotation) VALUES (?,?,?)",
        (title, type_, quotation), "Entities", decision,
    )


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；称谓不另建实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def astronomy_academy_tp(w):
    return find_tp(w, "翰林天文院", "北宋真宗咸平元年至四年（998—1001）", "机构")


def astronomy_bureau_tp(w):
    return find_tp(w, "翰林天文局", "北宋崇宁四年（1105）", "机构")


def restored_astronomy_bureau_tp(w):
    return find_tp(w, "翰林天文局", "南宋绍兴元年（1131）七月八日", "机构")


def hanlin_tp(w):
    return find_tp(w, "翰林院", "宋代", "机构")


def gallery_tp(w):
    return find_tp(w, "翰林图画院", "北宋雍熙元年（984）", "机构")


def imperial_library_tp(w):
    return find_tp(w, "翰林御书院", "北宋太平兴国七年（982）", "机构")


def entry641():
    i = 641
    w = W(i)
    main = F[i]["text"]
    aliases = field(i, "简称")
    eid = w.entity(F[i]["title"], "官职", "正式词头定义翰林天文院、局天文官。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）",
        "昼夜观测星象天候，校对历法并奏报天文休咎",
        main, "建立翰林院（局）天文官节点。", category="翰林天文技术官",
        officer_type="天文官",
    )
    relation(
        w, i, astronomy_academy_tp(w), tp, "编制隶属", main,
        "正式词头表明天文官亦隶翰林天文院。", staff_type="天文官",
        note="机构隶属由正式词头“翰林院（局）天文官”直接表明",
    )
    relation(
        w, i, astronomy_bureau_tp(w), tp, "编制隶属", aliases,
        "翰林天文局旧额天官四员。", "简称", staff_type="天文官", staff_quota="四员",
    )
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry642():
    i = 642
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正式词头定义翰林天文院、局学生总名。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）", "瞻天象、书写等诸类学生总名，属吏人编制",
        main, "建立翰林天文院（局）学生节点。", category="翰林天文学生",
        officer_type="吏人",
    )
    relation(w, i, astronomy_academy_tp(w), tp, "编制隶属", main, "学生隶翰林天文院。", staff_type="学生")
    relation(w, i, astronomy_bureau_tp(w), tp, "编制隶属", main, "学生隶翰林天文局。", staff_type="学生")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry643():
    i = 643
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正式词头定义天文局生。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（翰林天文局）", "额内学生供职五年后经升补成为局生",
        main, "建立翰林天文局生节点。", category="翰林天文吏员", officer_type="局生",
    )
    relation(w, i, astronomy_bureau_tp(w), tp, "编制隶属", main, "局生在翰林天文局供职。", staff_type="局生")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry644():
    i = 644
    w = W(i)
    main = F[i]["text"]
    old_e = w.entity("翰林天文院节级", "官职", "正文记司辰旧为节级等供给使人员。", quotation=main)
    old = timepoint(
        w, i, old_e, "北宋宣和二年（1120）九月以前", "天文院武职节级、卒伍等供给使人员",
        main, "建立司辰前身节点。", category="翰林天文武职吏人",
    )
    eid = w.entity(F[i]["title"], "官职", "正式词头定义宣和改称后的司辰。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋宣和二年（1120）九月", "由天文局节级、卒伍等供给使人员改称",
        main, "建立翰林天文局司辰改称节点。", category="翰林天文武职吏人",
        officer_type="司辰",
    )
    relation(w, i, old, tp, "前后演变", main, "宣和二年天文局节级等改称司辰。")
    relation(w, i, astronomy_bureau_tp(w), tp, "编制隶属", main, "司辰隶翰林天文局。", staff_type="司辰")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry645():
    i = 645
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    old = timepoint(
        w, i, eid, "北宋时期（宣和二年前）",
        "供职年限满且无过犯者可试天文专业，合格升转司天监保章正",
        main, "补建翰林天文院节级升转节点。", category="翰林天文武职吏人",
    )
    relation(w, i, astronomy_academy_tp(w), old, "编制隶属", main, "节级在翰林天文院供职。", staff_type="节级")
    new = find_tp(w, "翰林天文局司辰", "北宋宣和二年（1120）九月", "官职")
    relation(w, i, old, new, "前后演变", main, "宣和二年九月翰林天文院节级改名司辰。")
    promoted = find_tp(w, "司天监保章正", "北宋端拱元年九月以后", "官职")
    relation(w, i, old, promoted, "前后演变", main, "节级考试合格可升转司天监保章正。")
    alias_citation(w, i, old, "简称")
    w.commit()


def entry646():
    i = 646
    w = W(i)
    main = F[i]["text"]
    eid = distinct_entity(
        w, F[i]["title"], "机构", main,
        "本条明言隶翰林天文院（局），与司天监、太史局同名机构分建。",
    )
    tp = timepoint(
        w, i, eid, "宋代（翰林天文院、局）",
        "测验浑仪窥察天象，考验并校正历法疏密",
        main, "建立翰林天文系统测验浑仪刻漏所节点。", category="翰林天文院属所",
    )
    relation(w, i, astronomy_academy_tp(w), tp, "上下级机构", main, "本所隶翰林天文院。")
    relation(w, i, astronomy_bureau_tp(w), tp, "上下级机构", main, "改称后本所隶翰林天文局。")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry647():
    i = 647
    w = W(i)
    main = F[i]["text"]
    office_e = distinct_entity(
        w, "测验浑仪刻漏所", "机构", F[646]["text"],
        "复用翰林天文院系统的同名测验所。",
    )
    office = w.find_timepoint(office_e, "宋代（翰林天文院、局）")
    assert office
    eid = w.entity(F[i]["title"], "官职", "正式词头定义测验所技术官。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）", "观测记录天象、分析休咎并校对历法",
        main, "建立测验官节点。", category="测验浑仪刻漏所技术官",
    )
    relation(w, i, office, tp, "编制隶属", main, "测验官隶翰林天文院（局）测验浑仪刻漏所。", staff_type="技术官")
    w.commit()


def entry648():
    i = 648
    w = W(i)
    main = F[i]["text"]
    group_e = w.entity(F[i]["title"], "官职", "正式词头定义三类天文局属员连称。", quotation=main)
    group = timepoint(
        w, i, group_e, "宋代（翰林天文局）",
        "司辰、额内瞻望局生、额内学生三者连称",
        main, "建立三类属员连称节点。", category="翰林天文属员合称",
    )
    instances = (
        ("翰林天文局司辰", "司辰"),
        ("翰林天文局额内瞻望局生", "额内瞻望局生"),
        ("翰林天文局额内学生", "额内学生"),
    )
    for title, staff_type in instances:
        eid = w.entity(title, "官职", f"正文明确列举{staff_type}。", quotation=main)
        tp = timepoint(
            w, i, eid, "宋代（翰林天文局）", f"三类连称中的{staff_type}",
            main, f"建立{title}节点。", category="翰林天文属员", officer_type=staff_type,
        )
        relation(w, i, group, tp, "统称与实例", main, f"{title}为本连称实例。")
        relation(w, i, astronomy_bureau_tp(w), tp, "编制隶属", main, f"{title}隶翰林天文局。", staff_type=staff_type)
    w.commit()


def gallery_staff(w, i, parent, title, time, quotation, staff_type, quota, decision, conflict=False):
    eid = w.entity(title, "官职", f"编制明确列举{title}。", quotation=quotation)
    tp = timepoint(
        w, i, eid, time, decision, quotation, f"建立{title}编制节点。", "编制",
        category="翰林图画院技术官属", officer_type=staff_type,
        note=("总条记祗候四人，专条记四十人；两说并存" if conflict else None),
        conflict_flag=(1 if conflict else 0),
    )
    relation(
        w, i, parent, tp, "编制隶属", quotation, f"{title}隶翰林图画院。", "编制",
        staff_type=staff_type, staff_quota=quota,
        note=("总条记祗候四人，专条记四十人；两说并存" if conflict else None),
        conflict_flag=(1 if conflict else 0),
    )
    return tp


def entry649():
    i = 649
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    eid = find_entity(w, "翰林图画院", "机构")
    start = timepoint(
        w, i, eid, "北宋雍熙元年（984）", "始置",
        history, "建立翰林图画院始置节点。", "职源与沿革",
        category="翰林院属局", chain="head",
    )
    transferred = timepoint(
        w, i, eid, "北宋熙宁六年至元丰五年（1073—1082）",
        "改隶都大提举诸司库务",
        main, "建立改隶诸司库务节点。", category="内廷绘画机构",
    )
    returned = timepoint(
        w, i, eid, "北宋元丰五年（1082）以后", "复隶翰林院",
        main, "建立元丰五年后复隶节点。", category="翰林院属局",
    )
    cite(w, "Timepoints", start, i, duty, "补证绘画、捏塑供奉职掌。", "职掌")
    cite(w, "Timepoints", start, i, roster, "补证主管官、技术官、学生与工匠编制。", "编制")
    relation(w, i, hanlin_tp(w), start, "上下级机构", main, "翰林图画院隶翰林院。")
    finance_e = w.entity("都大提举诸司库务", "机构", "正文明确图画院改隶该机构。", quotation=main)
    finance = timepoint(
        w, i, finance_e, "北宋熙宁六年至元丰五年（1073—1082）",
        "管辖翰林图画院",
        main, "建立都大提举诸司库务承载节点。", category="内廷库务主管机构",
    )
    relation(w, i, finance, transferred, "上下级机构", main, "熙宁六年至元丰五年图画院改隶都大提举诸司库务。")
    relation(w, i, hanlin_tp(w), returned, "上下级机构", main, "元丰五年后图画院复隶翰林院。")

    bureau_e = find_entity(w, "翰林图画局", "机构")
    renamed = timepoint(
        w, i, bureau_e, "北宋绍圣二年（1095）", "由翰林图画院改称",
        history, "建立绍圣二年改称图画局节点。", "职源与沿革",
        category="翰林院属局", chain="head",
        note="本条作绍圣二年改称；图画局专条作元丰新制改称",
        conflict_flag=1,
    )
    relation(
        w, i, returned, renamed, "前后演变", history, "本条记绍圣二年改称翰林图画局。", "职源与沿革",
        note="本条作绍圣二年改称；图画局专条作元丰新制改称",
        conflict_flag=1,
    )
    timepoint(
        w, i, bureau_e, "北宋靖康年间（1126—1127）", "罢局，南宋未见复置",
        history, "建立靖康罢局节点。", "职源与沿革", category="机构废罢",
    )

    gallery_staff(w, i, start, "勾当翰林图画院", "北宋时期（具体时间未载）", roster, "勾当官", "二人", "掌督察图画院公事")
    gallery_staff(w, i, start, "翰林图画院待诏", "北宋时期（具体时间未载）", roster, "待诏", "三人", "专职绘画官")
    gallery_staff(w, i, start, "翰林图画院艺学", "北宋时期（具体时间未载）", roster, "艺学", "六人", "位次于待诏")
    gallery_staff(w, i, start, "翰林图画院祗候", "北宋（总条编制）", roster, "祗候", "四人", "总条编制记祗候四人", conflict=True)
    gallery_staff(w, i, start, "翰林图画院学生", "北宋时期（具体时间未载）", roster, "学生", "四十人", "图画院学生")
    workers = gallery_staff(w, i, start, "翰林图画院工匠", "北宋初额", roster, "工匠", "十四人", "工匠初额十四人")
    reduced = gallery_staff(w, i, start, "翰林图画院工匠", "北宋后减额", roster, "工匠", "六人", "工匠后减为六人")
    relation(w, i, workers, reduced, "前后演变", roster, "图画院工匠由十四人减为六人。", "编制")
    alias_citation(w, i, start, "简称")
    w.commit()


def entry650():
    i = 650
    w = W(i)
    main = F[i]["text"]
    old = find_tp(w, "翰林图画院", "北宋元丰五年（1082）以后", "机构")
    eid = find_entity(w, "翰林图画局", "机构")
    tp = timepoint(
        w, i, eid, "北宋元丰五年（1082）新制", "由翰林图画院改称图画局",
        main, "建立元丰新制改称图画局异说节点。", category="翰林院属局",
        chain="head",
        note="本专条作元丰新制改称；图画院总条作绍圣二年改称",
        conflict_flag=1,
    )
    relation(
        w, i, old, tp, "前后演变", main, "专条记元丰新制改称图画局。",
        note="本专条作元丰新制改称；图画院总条作绍圣二年改称",
        conflict_flag=1,
    )
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry651():
    i = 651
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    tp = timepoint(
        w, i, eid, "北宋时期（具体时间未载）", "由内侍充，掌督察图画院公事，二人",
        main, "补证勾当翰林图画院节点。", category="翰林图画院主管官",
        officer_type="内侍差遣",
    )
    relation(w, i, gallery_tp(w), tp, "编制隶属", main, "勾当官主管翰林图画院。", staff_type="勾当官", staff_quota="二人")
    w.commit()


def entry652():
    i = 652
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    tp = timepoint(
        w, i, eid, "北宋太宗朝（976—997）", "始置，为图画院专职绘画官，三人",
        main, "建立翰林图画院待诏始置节点。", category="翰林图画院技术官",
        officer_type="待诏",
    )
    relation(w, i, gallery_tp(w), tp, "编制隶属", main, "待诏隶翰林图画院。", staff_type="待诏", staff_quota="三人")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry653():
    i = 653
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    before = timepoint(
        w, i, eid, "北宋熙宁二年（1069）十一月以前", "永为艺学，无递迁之制，六人",
        main, "建立艺学旧制节点。", category="翰林图画院技术官", officer_type="艺学",
    )
    after = timepoint(
        w, i, eid, "北宋熙宁二年（1069）十一月以后", "待诏有阙时经试择优迁补，六人",
        main, "建立艺学迁补新制节点。", category="翰林图画院技术官", officer_type="艺学",
    )
    relation(w, i, gallery_tp(w), before, "编制隶属", main, "艺学隶翰林图画院。", staff_type="艺学", staff_quota="六人")
    relation(w, i, gallery_tp(w), after, "编制隶属", main, "熙宁新制后艺学仍隶图画院。", staff_type="艺学", staff_quota="六人")
    relation(w, i, after, find_tp(w, "翰林图画院待诏", "北宋太宗朝（976—997）", "官职"), "前后演变", main, "艺学经试可迁补待诏。")
    w.commit()


def entry654():
    i = 654
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    tp = timepoint(
        w, i, eid, "北宋（专条编制）", "位次于艺学，熙宁二年后由优秀学生经试迁补，专条记四十人",
        main, "建立祗候专条编制节点。", category="翰林图画院技术官", officer_type="祗候",
        note="本专条记祗候四十人；图画院总条记四人",
        conflict_flag=1,
    )
    relation(
        w, i, gallery_tp(w), tp, "编制隶属", main, "祗候隶翰林图画院。",
        staff_type="祗候", staff_quota="四十人",
        note="本专条记祗候四十人；图画院总条记四人",
        conflict_flag=1,
    )
    student = find_tp(w, "翰林图画院学生", "北宋时期（具体时间未载）", "官职")
    relation(w, i, student, tp, "前后演变", main, "熙宁二年后优秀学生可经试迁补祗候。")
    w.commit()


def entry655():
    i = 655
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    roster = field(i, "编制")
    eid = find_entity(w, "翰林御书院", "机构")
    start = timepoint(
        w, i, eid, "北宋太平兴国七年（982）", "始设翰林侍书，宿直禁中御书院",
        history, "建立翰林御书院始置节点。", "职源与沿革", category="翰林院属局",
        chain="head",
    )
    book_bureau_e = find_entity(w, "翰林书艺局", "机构")
    book_bureau = timepoint(
        w, i, book_bureau_e, "北宋元丰五年（1082）新制", "翰林御书院改称书艺局",
        history, "建立元丰新制改称书艺局节点。", "职源与沿革",
        category="翰林院属局", chain="head",
    )
    south = timepoint(
        w, i, eid, "南宋初（1127—1129）", "复称御书院",
        history, "建立南宋初复称节点。", "职源与沿革", category="翰林院属局",
    )
    abolished = timepoint(
        w, i, eid, "南宋建炎三年（1129）", "罢御书院",
        history, "建立建炎三年罢院节点。", "职源与沿革", category="机构废罢",
    )
    restored = timepoint(
        w, i, eid, "南宋绍兴十六年（1146）十一月十七日", "复置",
        history, "建立绍兴十六年复置节点。", "职源与沿革", category="翰林院属局",
    )
    timepoint(
        w, i, eid, "南宋绍兴三十年（1160）正月十七日", "又罢",
        history, "建立绍兴三十年再罢节点。", "职源与沿革", category="机构废罢",
    )
    cite(w, "Timepoints", start, i, roster, "补证北宋及绍兴复置后的完整编制。", "编制")
    relation(w, i, start, book_bureau, "前后演变", history, "元丰新制御书院改称书艺局。", "职源与沿革")
    relation(w, i, book_bureau, south, "前后演变", history, "南宋初书艺局复称御书院。", "职源与沿革")
    relation(w, i, hanlin_tp(w), start, "上下级机构", main, "翰林御书院隶翰林院。")
    relation(w, i, find_tp(w, "翰林院", "南宋时期（1127—1279）", "机构"), south, "上下级机构", main, "南宋初御书院仍隶翰林院。")
    relation(w, i, find_tp(w, "翰林院", "南宋时期（1127—1279）", "机构"), restored, "上下级机构", main, "绍兴十六年复置御书院隶翰林院。")

    north_staff = (
        ("勾当翰林御书院", "勾当官", "三人"),
        ("翰林御书院书写待诏", "御书待诏", None),
        ("翰林御书院书艺", "翰林书艺", None),
        ("翰林御书院翰林待诏", "翰林待诏", None),
        ("翰林御书院祗候", "祗候", "十七人"),
        ("翰林御书院装界匠", "工匠", "九人"),
        ("翰林御书院印碑匠", "工匠", "六人"),
        ("翰林御书院雕字匠", "工匠", "五人"),
    )
    for title, staff_type, quota in north_staff:
        post_e = w.entity(title, "官职", f"北宋编制明确列举{title}。", quotation=roster)
        post = timepoint(
            w, i, post_e, "北宋时期（翰林御书院）", f"御书院所属{staff_type}",
            roster, f"建立{title}北宋编制节点。", "编制", category="翰林御书院属员",
            officer_type=staff_type,
        )
        relation(w, i, start, post, "编制隶属", roster, f"{title}隶翰林御书院。", "编制", staff_type=staff_type, staff_quota=quota)

    for title, staff_type, quota in SOUTH_IMPERIAL_LIBRARY_STAFF:
        post_e = w.entity(title, "官职", f"绍兴十六年复置编制明确列举{title}。", quotation=roster)
        post = timepoint(
            w, i, post_e, "南宋绍兴十六年（1146）十一月十七日",
            f"御书院复置时所属{staff_type}",
            roster, f"建立{title}南宋编制节点。", "编制", category="翰林御书院属员",
            officer_type=staff_type,
        )
        relation(w, i, restored, post, "编制隶属", roster, f"{title}隶复置后的翰林御书院。", "编制", staff_type=staff_type, staff_quota=quota)
    alias_citation(w, i, start, "简称")
    w.commit()


def entry656():
    i = 656
    w = W(i)
    main = F[i]["text"]
    old = imperial_library_tp(w)
    eid = find_entity(w, "翰林书艺局", "机构")
    tp = timepoint(
        w, i, eid, "北宋元丰五年（1082）新制", "翰林御书院改称翰林书艺局",
        main, "建立元丰五年改称书艺局节点。", category="翰林院属局", chain="head",
    )
    relation(w, i, old, tp, "前后演变", main, "元丰五年御书院改称书艺局。")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry657():
    i = 657
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    tp = timepoint(
        w, i, eid, "北宋时期（翰林御书院）", "由内侍充，掌督察御书院公事，三人",
        main, "补证勾当翰林御书院节点。", category="翰林御书院主管官",
        officer_type="内侍差遣",
    )
    relation(w, i, imperial_library_tp(w), tp, "编制隶属", main, "勾当官主管翰林御书院。", staff_type="勾当官", staff_quota="三人")
    alias_citation(w, i, tp, "别称")
    w.commit()


def entry658():
    i = 658
    w = W(i)
    main = F[i]["text"]
    old = find_tp(w, "勾当翰林御书院", "北宋时期（翰林御书院）", "官职")
    eid = find_entity(w, F[i]["title"], "官职")
    tp = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "由勾当翰林御书院改名",
        main, "建立干办翰林御书院节点。", category="翰林御书院主管官",
        officer_type="干办官",
    )
    relation(w, i, old, tp, "前后演变", main, "南宋勾当翰林御书院改称干办翰林御书院。")
    relation(w, i, find_tp(w, "翰林御书院", "南宋绍兴十六年（1146）十一月十七日", "机构"), tp, "编制隶属", main, "干办官掌南宋翰林御书院。", staff_type="干办官", staff_quota="一员")
    w.commit()


def entry659():
    i = 659
    w = W(i)
    main = F[i]["text"]
    origin = field(i, "职源")
    eid = w.entity(F[i]["title"], "官职", "正式词头定义寓直御书院的翰林侍书。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋太平兴国七年（982）六月", "始置，寓直御书院，以善书法备顾问应奉",
        origin, "建立翰林侍书始置节点。", "职源", category="翰林御书院技术官",
        officer_type="侍书",
    )
    cite(w, "Timepoints", tp, i, field(i, "职掌"), "补证书法顾问与应奉职掌。", "职掌")
    cite(w, "Timepoints", tp, i, field(i, "品位"), "补证品位视所带官。", "品位")
    relation(w, i, imperial_library_tp(w), tp, "编制隶属", main, "翰林侍书寓直御书院。", staff_type="侍书")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry660():
    i = 660
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    old_e = w.entity("隶书待诏", "官职", "职源字段记御书院建立前学士院所设待诏。", quotation=history)
    old = timepoint(
        w, i, old_e, "宋初（御书院建立前）", "学士院设置",
        history, "建立隶书待诏前身节点。", "职源与沿革", category="学士院技术官",
    )
    eid = find_entity(w, F[i]["title"], "官职")
    north = timepoint(
        w, i, eid, "北宋太平兴国中（976—984）", "御书院建立后始设，随御书院罢置",
        history, "建立书写待诏北宋节点。", "职源与沿革", category="翰林御书院技术官",
        officer_type="书写待诏",
    )
    south = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "称书写待诏，三人",
        field(i, "编制"), "建立书写待诏南宋编制节点。", "编制", category="翰林御书院技术官",
        officer_type="书写待诏",
    )
    cite(w, "Timepoints", north, i, field(i, "职掌"), "补证诏命、国书、赐目及节庆祠祭书写职掌。", "职掌")
    cite(w, "Timepoints", north, i, field(i, "品位"), "补证待诏无品及出职规则。", "品位")
    relation(w, i, old, north, "前后演变", history, "御书院建立后由学士院隶书待诏发展为书写待诏。", "职源与沿革")
    relation(w, i, imperial_library_tp(w), north, "编制隶属", main, "书写待诏隶翰林御书院。", staff_type="书写待诏")
    relation(w, i, find_tp(w, "翰林御书院", "南宋绍兴十六年（1146）十一月十七日", "机构"), south, "编制隶属", field(i, "编制"), "南宋书写待诏隶复置后的御书院。", "编制", staff_type="书写待诏", staff_quota="三人")
    alias_citation(w, i, north, "简称与别名")
    w.commit()


def main():
    assert len(SOUTH_IMPERIAL_LIBRARY_STAFF) == 34
    assert [F[i]["title"] for i in range(641, 661)] == [
        "翰林院（局）天文官", "翰林天文院（局）学生", "翰林天文局生", "翰林天文局司辰",
        "翰林天文院节级", "测验浑仪刻漏所", "测验官", "翰林天文局司辰额内瞻望局学生",
        "翰林图画院", "翰林图画局", "勾当翰林图画院", "翰林图画院待诏",
        "翰林图画院艺学", "翰林图画院祗候", "翰林御书院", "翰林书艺局",
        "勾当翰林御书院", "干办翰林御书院", "翰林侍书", "翰林御书院书写待诏",
    ]
    assert "1073—1082）" in F[649]["text"] and "雍熙元年（984）" in field(649, "职源与沿革")
    assert "干办官一员" in field(655, "编制") and "剪字一名，钑作一名" in field(655, "编制")
    assert F[658]["text"] == "即勾当翰林御书院。南宋时改名。"
    assert "太平兴国七年（982）" in field(659, "职源") and "卷68己未" in field(660, "简称与别名")
    entry641(); entry642(); entry643(); entry644(); entry645(); entry646(); entry647(); entry648()
    entry649(); entry650(); entry651(); entry652(); entry653(); entry654(); entry655(); entry656()
    entry657(); entry658(); entry659(); entry660()


if __name__ == "__main__":
    main()
