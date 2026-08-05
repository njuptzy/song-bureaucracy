#!/usr/bin/env python3
"""提取第一编第621-640条：后苑作、三阁管勾与翰林天文机构。"""

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


WORKSHOPS = (
    "生色作", "缕作", "金作", "烧朱作", "腰带作", "钑作", "打造作", "面花作",
    "结条作", "玉作", "真珠作", "犀作", "琥珀作", "玳瑁作", "花作", "蜡裹作",
    "装銮作", "小木作", "锯匠作", "漆作", "雕木作", "平拨作", "钙作", "旋作",
    "宝装作", "缨络作", "染牙作", "砑作", "胎素作", "竹作", "镞镂作", "糊粘作",
    "像生作", "靴作", "折竹作", "棱作", "匙筋作", "拍金作", "铁作", "小炉作",
    "错磨作", "乐器作", "球子作", "抢棒作", "球仗作", "丝鞋作", "镀金作", "穰洗作",
    "牙作", "梢子作", "裁缝作", "拽条作", "钉子作", "克丝作", "绣作", "织罗作",
    "绦作", "伤裹作", "藤作", "打弦作", "铜碌作", "绵胭脂作", "胭脂作", "桶作",
    "杂钉作", "响铁作", "油衣作", "染作", "戎具作", "扇子作", "鞍作", "冷坠作",
    "伞作", "剑鞘作", "扣线作", "金线作", "裹剑作", "冠子作", "角衬作", "浮动作",
    "沥水作", "照子作",
)


def repair_dictionary_source():
    """据原书第74-77页恢复#633并修复本批明显OCR。"""
    roster622 = (
        "监官三人，以内侍充。监门兵校及工匠四百三十六人。吏额有专、典，十二人。"
        f"所内领有八十一作：{'、'.join(WORKSHOPS)}。"
    )
    text633 = (
        "差遣名。南宋时改勾当官为干办官。"
        "《宋会要·职官》36之93：“吴玫特添差干办御前忠佐军头、引见司。”"
    )
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(f"SELECT fields FROM {table} WHERE id=622").fetchone()
            assert row and row[0]
            f622 = json.loads(row[0])
            f622["职掌"] = f622["职掌"].replace("官庭生活所需", "宫庭生活所需")
            f622["编制"] = roster622
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=622",
                (json.dumps(f622, ensure_ascii=False),),
            )

            row = conn.execute(f"SELECT fields FROM {table} WHERE id=628").fetchone()
            assert row and row[0]
            f628 = json.loads(row[0])
            f628["别名"] = f628["别名"].replace("管阁龙图阁", "管勾龙图阁")
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=628",
                (json.dumps(f628, ensure_ascii=False),),
            )

            row = conn.execute(f"SELECT fields FROM {table} WHERE id=632").fetchone()
            assert row and row[0]
            f632 = json.loads(row[0])
            f632["职源与沿革"] = f632["职源与沿革"].replace(
                "端拱二年(989)", "端拱二年（989）"
            )
            f632["编制"] = "勾当官五人（《宋史·职官志》6《入内内侍省内侍省》）。"
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=632",
                (json.dumps(f632, ensure_ascii=False),),
            )
            conn.execute(
                f"UPDATE {table} SET title=?,text=?,fields=NULL WHERE id=633",
                ("干办军头、引见司", text633),
            )

            row = conn.execute(f"SELECT text,fields FROM {table} WHERE id=638").fetchone()
            assert row and row[0] and row[1]
            f638 = json.loads(row[1])
            f638["职源与沿革"] = (
                f638["职源与沿革"]
                .replace("（998—1001)之间(", "（998—1001）之间（")
                .replace("三年(1129)", "三年（1129）")
                .replace("元年(1131)", "元年（1131）")
                .replace("《宋会要·运历》1之6)", "《宋会要·运历》1之6）")
                .replace("（同前书31之6)", "（同前书31之6）")
                .replace("（《要录》卷46)", "（《要录》卷46）")
            )
            conn.execute(
                f"UPDATE {table} SET text=?,fields=? WHERE id=638",
                (row[0].rstrip("。") + "。", json.dumps(f638, ensure_ascii=False)),
            )
            row = conn.execute(f"SELECT text FROM {table} WHERE id=640").fetchone()
            assert row and row[0]
            conn.execute(
                f"UPDATE {table} SET text=? WHERE id=640",
                (row[0].replace("七年(1180)", "七年（1180）"),),
            )


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(621, 641)}


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


def alias_citation(w, i, tp_id, name="别名"):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；称谓不另建实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


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


def inner_province_tp(w):
    return find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构")


def inner_official_tp(w):
    return find_tp(w, "内侍官", "宋代（具体时间未载）", "官职")


def back_garden_tp(w):
    return find_tp(w, "后苑", "宋代（具体时间未载）", "机构")


def hanlin_tp(w):
    return find_tp(w, "翰林院", "宋代（具体时间未载）", "机构")


def entry621():
    i = 621
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("书状官", "官职", "正式词头定义通问使、国信使副亲吏。", quotation=main)
    timepoint(
        w, i, eid, "宋代（具体时间未载）",
        "通问使或国信使、副使亲吏，掌管使、副私信",
        main, "建立书状官节点。", category="国信使属吏", officer_type="吏人",
    )
    w.commit()


def entry622():
    i = 622
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    eid = w.entity(F[i]["title"], "机构", "正式词头定义内庭造作机构。", quotation=main)
    start = timepoint(
        w, i, eid, "北宋咸平三年（1000）", "生活所与后苑作合并，创置本所",
        history, "建立后苑作、制造御前生活所始置节点。", "职源与沿革",
        category="入内内侍省属造作机构",
    )
    wartime = timepoint(
        w, i, eid, "北宋靖康元年（1126）正月三日",
        "内外司局大罢时独留，以供奉太上皇徽宗等所需",
        history, "建立靖康元年保留节点。", "职源与沿革",
        category="入内内侍省属造作机构",
    )
    south = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "后苑沿存",
        history, "建立南宋沿存节点。", "职源与沿革",
        category="内庭造作机构",
    )
    cite(w, "Timepoints", start, i, duty, "补证制造宫庭生活所需及皇族婚娶名物职掌。", "职掌")
    cite(
        w, "Timepoints", start, i, roster,
        "补证监官、吏额、工匠及原书所称八十一作编制。", "编制",
        note="原书称八十一作，但逐项列举共有八十二项；全部照录",
        conflict_flag=1,
    )
    relation(w, i, inner_province_tp(w), start, "上下级机构", main, "本所隶入内内侍省。")

    monitor_e = w.entity(
        "后苑作、制造御前生活所监官", "官职",
        "编制明确设置三名监官。", quotation=roster,
    )
    monitor = timepoint(
        w, i, monitor_e, "北宋时期（具体时间未载）", "以内侍充，三人",
        roster, "建立本所监官编制。", "编制", category="后苑作主管官",
        officer_type="内侍差遣",
    )
    relation(
        w, i, start, monitor, "编制隶属", roster, "监官主管本所。", "编制",
        staff_type="监官", staff_quota="三人",
    )
    workers_e = w.entity(
        "后苑作监门兵校及工匠", "官职",
        "编制合记监门兵校及工匠总额。", quotation=roster,
    )
    workers = timepoint(
        w, i, workers_e, "北宋时期（具体时间未载）", "合计四百三十六人",
        roster, "建立监门兵校及工匠合计编制。", "编制", category="后苑作役员",
    )
    relation(
        w, i, start, workers, "编制隶属", roster, "监门兵校及工匠隶本所。", "编制",
        staff_type="监门兵校及工匠", staff_quota="四百三十六人",
    )
    clerks_e = w.entity("后苑作吏", "官职", "编制记吏额及吏名。", quotation=roster)
    clerks = timepoint(
        w, i, clerks_e, "北宋时期（具体时间未载）", "吏名专、典，十二人",
        roster, "建立本所吏额。", "编制", category="后苑作吏员",
    )
    relation(
        w, i, start, clerks, "编制隶属", roster, "专、典等吏人隶本所。", "编制",
        staff_type="吏人（专、典）", staff_quota="十二人",
    )
    for title in WORKSHOPS:
        workshop_e = distinct_entity(
            w, title, "机构", roster, f"据本所逐项列举的造作编制建立{title}。"
        )
        workshop = timepoint(
            w, i, workshop_e, "北宋时期（具体时间未载）", "后苑作生活所所属造作工坊",
            roster, f"建立{title}节点。", "编制", category="后苑作所属工坊",
        )
        relation(
            w, i, start, workshop, "上下级机构", roster,
            f"编制明确列举{title}为本所所属造作之一。", "编制",
        )
    alias_citation(w, i, start, "简称")
    w.commit()


def back_garden_post(i, title, time, event, staff_type):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(title, "官职", f"正式词头定义{title}差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, time, event, main, f"建立{title}节点。",
        category="后苑差遣", officer_type=staff_type,
    )
    relation(
        w, i, back_garden_tp(w), tp, "编制隶属", main, f"{title}隶后苑。",
        staff_type=staff_type,
    )
    if F[i]["fields"].get("别名"):
        alias_citation(w, i, tp)
    w.commit()


def entry623():
    i = 623
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("后苑使", "官职", "正式词头定义提纲后苑公事差遣。", quotation=main)
    north = timepoint(
        w, i, eid, "北宋初", "单置后苑时置使，提纲后苑公事",
        main, "建立北宋初后苑使节点。", category="后苑主管官",
    )
    south = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "单置后苑时置使，提纲后苑公事",
        main, "建立南宋后苑使节点。", category="后苑主管官",
    )
    relation(w, i, back_garden_tp(w), north, "编制隶属", main, "后苑使提纲后苑公事。", staff_type="使")
    relation(w, i, back_garden_tp(w), south, "编制隶属", main, "南宋后苑使提纲后苑公事。", staff_type="使")
    w.commit()


def entry624():
    back_garden_post(624, "权干办后苑官", "南宋时期（1127—1279）", "监视后苑内事", "干办官")


def entry625():
    back_garden_post(625, "后苑大主管使臣", "宋代（具体时间未载）", "由内侍充，供奉禁中暖烫", "主管使臣")


def entry626():
    i = 626
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正式词头定义后苑作生活所提举官。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋徽宗朝（1100—1126）", "设置，总领后苑作生活所",
        main, "建立提举后苑作生活所节点。", category="后苑作主管官",
    )
    parent_e = find_entity(w, "后苑作、制造御前生活所", "机构")
    parent = timepoint(
        w, i, parent_e, "北宋徽宗朝（1100—1126）", "大兴土木，设置提举官总领",
        main, "建立徽宗朝后苑作承载节点。", category="入内内侍省属造作机构",
    )
    relation(w, i, parent, tp, "编制隶属", main, "提举官总领后苑作生活所。", staff_type="提举官")
    alias_citation(w, i, tp)
    w.commit()


def gallery_post(i, gallery_title, emperor):
    w = W(i)
    main = F[i]["text"]
    office_e = w.entity(gallery_title, "机构", f"正文明确{gallery_title}藏奉制度。", quotation=main)
    office = timepoint(
        w, i, office_e, "北宋时期（具体时间未载）",
        f"收藏{emperor}文书、符瑞、宝玩并安设肖像以崇奉",
        main, f"建立{gallery_title}节点。", category="祖宗阁藏",
    )
    post_title = F[i]["title"]
    post_e = w.entity(post_title, "官职", f"正式词头定义{gallery_title}管勾官。", quotation=main)
    post = timepoint(
        w, i, post_e, "北宋时期（具体时间未载）",
        f"以入内内侍充，掌{gallery_title}藏奉事务",
        main, f"建立{post_title}节点。", category="祖宗阁主管官",
        officer_type="内侍差遣",
    )
    relation(w, i, office, post, "编制隶属", main, f"{post_title}主管{gallery_title}。", staff_type="管勾官")
    if F[i]["fields"].get("别名"):
        alias_citation(w, i, post)
    if "南宋时" in main:
        supervisor_title = post_title.replace("管勾", "主管", 1)
        supervisor_e = w.entity(supervisor_title, "官职", "正文记南宋改称主管官。", quotation=main)
        supervisor = timepoint(
            w, i, supervisor_e, "南宋时期（1127—1279）", f"由{post_title}改称",
            main, f"建立{supervisor_title}节点。", category="祖宗阁主管官",
            officer_type="内侍差遣",
        )
        relation(w, i, post, supervisor, "前后演变", main, f"南宋{post_title}改称{supervisor_title}。")
        relation(w, i, office, supervisor, "编制隶属", main, f"{supervisor_title}主管{gallery_title}。", staff_type="主管官")
    w.commit()


def entry627(): gallery_post(627, "龙图阁", "太宗")
def entry628(): gallery_post(628, "天章阁", "真宗")
def entry629(): gallery_post(629, "宝文阁", "仁宗")


def collective_gallery_post(i, group_title, prefix, time, instances):
    w = W(i)
    main = F[i]["text"]
    group_e = w.entity(group_title, "官职", "正式词头定义诸阁主管官合称。", quotation=main)
    group = timepoint(
        w, i, group_e, time, main, main, f"建立{group_title}合称节点。",
        category="诸阁主管官合称",
    )
    for gallery in instances:
        post_title = f"{prefix}{gallery}"
        post_e = w.entity(post_title, "官职", f"正文列举{gallery}{prefix}官。", quotation=main)
        post = timepoint(
            w, i, post_e, time, f"掌{gallery}藏奉或检阅事务",
            main, f"建立{post_title}节点。", category="祖宗阁主管官",
            officer_type="内侍差遣",
        )
        relation(w, i, group, post, "统称与实例", main, f"{post_title}是{group_title}所含实例。")
        office_e = w.entity(gallery, "机构", f"正文列举{gallery}为内廷阁藏。", quotation=main)
        office = timepoint(
            w, i, office_e, time, f"设{prefix}官掌管",
            main, f"建立{gallery}承载节点。", category="内廷阁藏",
        )
        relation(w, i, office, post, "编制隶属", main, f"{post_title}掌管{gallery}。", staff_type=f"{prefix}官")
    w.commit()


def entry630():
    collective_gallery_post(
        630, "勾当龙图、天章、宝文阁", "管勾", "北宋时期（具体时间未载）",
        ("龙图阁", "天章阁", "宝文阁", "太清楼"),
    )


def entry631():
    collective_gallery_post(
        631, "主管龙图、天章、宝文阁", "主管", "南宋时期（1127—1279）",
        ("龙图阁", "天章阁", "宝文阁", "太清楼"),
    )


def entry632():
    i = 632
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    grade = field(i, "品位")
    old = find_tp(w, "御前忠佐军头、引见司", "北宋端拱二年正月", "机构")
    office_e = find_entity(w, "军头引见司", "机构")
    office = timepoint(
        w, i, office_e, "北宋元丰改制后", "止称军头、引见司",
        history, "建立元丰后军头、引见司复名节点。", "职源与沿革",
        category="御前忠佐禁军机构",
    )
    south = find_tp(w, "御前忠佐军头、引见司", "南宋", "机构")
    relation(w, i, old, office, "前后演变", history, "元丰新制去御前忠佐之称。", "职源与沿革")
    relation(w, i, office, south, "前后演变", history, "南宋恢复御前忠佐军头、引见司正称。", "职源与沿革")
    post_e = w.entity(F[i]["title"], "官职", "正式词头定义军头、引见司勾当官。", quotation=main)
    post = timepoint(
        w, i, post_e, "北宋元丰改制后", "由内侍两省都知、押班及阁门通事舍人以上充任",
        main, "建立勾当军头、引见司节点。", category="军头引见司主管官",
        officer_type="勾当官", grade="品视所充本官",
    )
    cite(w, "Timepoints", post, i, duty, "补证禁卫引见与军官名籍职掌。", "职掌")
    cite(w, "Timepoints", post, i, grade, "补证品位随所充本官而定。", "品位")
    cite(w, "Timepoints", post, i, roster, "补证勾当官五人。", "编制")
    relation(
        w, i, office, post, "编制隶属", main, "勾当官掌领军头、引见司。",
        staff_type="勾当官", staff_quota="五人",
    )
    w.commit()


def entry633():
    i = 633
    w = W(i)
    main = F[i]["text"]
    old = find_tp(w, "勾当军头、引见司", "北宋元丰改制后", "官职")
    eid = w.entity(F[i]["title"], "官职", "恢复原书正式词头，定义南宋干办官。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "由勾当官改称，掌御前忠佐军头、引见司",
        main, "建立干办军头、引见司节点。", category="军头引见司主管官",
        officer_type="干办官",
    )
    relation(w, i, old, tp, "前后演变", main, "南宋勾当军头、引见司改称干办军头、引见司。")
    relation(
        w, i, find_tp(w, "御前忠佐军头、引见司", "南宋", "机构"), tp,
        "编制隶属", main, "干办官掌御前忠佐军头、引见司。", staff_type="干办官",
    )
    w.commit()


def entry634():
    i = 634
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    eid = find_entity(w, "翰林院", "机构")
    tang = timepoint(
        w, i, eid, "唐开元初", "始置，为文人待诏之所",
        history, "建立唐代翰林院源流节点。", "职源与沿革",
        category="待诏机构", chain="head",
    )
    song = find_tp(w, "翰林院", "宋代", "机构")
    south = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "沿置，掌供奉技艺",
        history, "建立南宋翰林院沿置节点。", "职源与沿革",
        category="入内内侍省属供奉机构",
    )
    cite(w, "Timepoints", song, i, history, "补证宋代翰林院与学士院分途。", "职源与沿革")
    cite(w, "Timepoints", song, i, duty, "补证书画、捏塑、琴棋、医术、天文供奉职掌。", "职掌")
    cite(w, "Timepoints", song, i, roster, "补证主管官、所属四局、吏额与分案。", "编制")
    relation(w, i, inner_province_tp(w), hanlin_tp(w), "上下级机构", main, "翰林院隶入内内侍省。")
    for title in ("翰林御书院", "翰林医官院", "翰林天文院", "翰林图画院"):
        sub_e = w.entity(title, "机构", "北宋所属四局编制明确列举。", quotation=roster)
        sub = timepoint(
            w, i, sub_e, "北宋时期（具体时间未载）", "翰林院所属供奉机构",
            roster, f"建立{title}北宋节点。", "编制", category="翰林院属局",
        )
        relation(w, i, song, sub, "上下级机构", roster, f"北宋{title}隶翰林院。", "编制")
    for title in ("翰林医官局", "翰林天文局"):
        sub_e = w.entity(title, "机构", "南宋所属二局编制明确列举。", quotation=roster)
        sub = timepoint(
            w, i, sub_e, "南宋时期（1127—1279）", "翰林院所属供奉机构",
            roster, f"建立{title}南宋节点。", "编制", category="翰林院属局",
        )
        relation(w, i, south, sub, "上下级机构", roster, f"南宋{title}隶翰林院。", "编制")
    alias_citation(w, i, song, "简称")
    w.commit()


def hanlin_post(i, time, event, staff_type):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", f"正式词头定义{F[i]['title']}差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, time, event, main, f"建立{F[i]['title']}节点。",
        category="翰林院主管官", officer_type=staff_type,
    )
    relation(w, i, hanlin_tp(w), tp, "编制隶属", main, f"{F[i]['title']}领翰林院。", staff_type=staff_type)
    w.commit()


def entry635():
    hanlin_post(635, "宋前期及元丰新制", "由内侍省押班或都知充，领翰林院", "勾当官")


def entry636():
    hanlin_post(636, "南宋绍兴二年（1132）八月十一日", "内侍省押班或都知差领翰林院时称提举", "提举官")


def entry637():
    i = 637
    w = W(i)
    main = F[i]["text"]
    group_e = w.entity("提点翰林院", "官职", "正式词头定义绍兴三十年后的翰林院提点官。", quotation=main)
    group = timepoint(
        w, i, group_e, "南宋绍兴三十年（1160）九月以后",
        "内侍省罢后，以入内内侍省都知、押班兼领翰林院",
        main, "建立提点翰林院节点。", category="翰林院主管官", officer_type="提点官",
    )
    relation(w, i, hanlin_tp(w), group, "编制隶属", main, "提点官兼领翰林院。", staff_type="提点官")
    same_e = w.entity("同提点翰林院", "官职", "正文明确同提点之称。", quotation=main)
    same = timepoint(
        w, i, same_e, "南宋绍兴三十年（1160）九月以后", "与提点并称，兼领翰林院",
        main, "建立同提点翰林院节点。", category="翰林院主管官", officer_type="同提点官",
    )
    relation(w, i, hanlin_tp(w), same, "编制隶属", main, "同提点官兼领翰林院。", staff_type="同提点官")
    w.commit()


def entry638():
    i = 638
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    eid = find_entity(w, "翰林天文院", "机构")
    start = timepoint(
        w, i, eid, "北宋真宗咸平元年至四年（998—1001）", "创置",
        history, "建立翰林天文院创置节点。", "职源与沿革", category="翰林院属局",
        chain="head",
    )
    cite(w, "Timepoints", start, i, duty, "补证天象观测、占卜验证及季绘星图职掌。", "职掌")
    cite(w, "Timepoints", start, i, roster, "补证天文官、司辰、学生、吏役及设施编制。", "编制")
    relation(w, i, find_tp(w, "翰林院", "宋代", "机构"), start, "上下级机构", main, "翰林天文院隶翰林院。")
    alias_citation(w, i, start, "简称与别名")
    w.commit()


def entry639():
    i = 639
    w = W(i)
    main = F[i]["text"]
    old = find_tp(w, "翰林天文院", "北宋真宗咸平元年至四年（998—1001）", "机构")
    eid = find_entity(w, "翰林天文局", "机构")
    renamed = timepoint(
        w, i, eid, "北宋崇宁四年（1105）", "翰林天文院改称翰林天文局",
        main, "建立崇宁四年改称节点。", category="翰林院属局", chain="head",
    )
    merged = timepoint(
        w, i, eid, "南宋建炎三年（1129）四月十三日", "罢，并入太史局",
        main, "建立建炎三年并入太史局节点。", category="机构演变",
    )
    relation(w, i, old, renamed, "前后演变", main, "翰林天文院于崇宁四年改称翰林天文局。")
    taishi_e = find_entity(w, "太史局", "机构")
    taishi = timepoint(
        w, i, taishi_e, "南宋建炎三年（1129）四月十三日", "接收并入的翰林天文局",
        main, "建立太史局接收天文局节点。", category="天文机构",
    )
    relation(w, i, merged, taishi, "前后演变", main, "建炎三年翰林天文局并入太史局。")
    alias_citation(w, i, renamed, "简称")
    w.commit()


def entry640():
    i = 640
    history = field(638, "职源与沿革")
    source_w = W(638)
    office_e = find_entity(source_w, "翰林天文局", "机构")
    restored = source_w.timepoint(
        office_e, "南宋绍兴元年（1131）七月八日", "复置",
        "据翰林天文院职源字段补建绍兴元年复置节点。", history,
        attr_category="翰林院属局",
    )
    cite(
        source_w, "Timepoints", restored, 638, history,
        "据翰林天文院职源字段补建绍兴元年复置节点。", "职源与沿革",
    )
    source_w.commit()

    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正式词头定义翰林天文局主管官。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋淳熙七年（1180）六月十日", "由太史局天文官一员充专职主管官",
        main, "建立主管翰林天文局节点。", category="翰林天文局主管官",
        officer_type="主管官",
    )
    relation(
        w, i, restored, tp, "编制隶属", main, "主管官专领翰林天文局。",
        staff_type="主管官", staff_quota="一人",
    )
    w.commit()


def main():
    # 原书自称八十一作，但逐项列名实际为八十二项，全部照录。
    assert len(WORKSHOPS) == 82
    assert [F[i]["title"] for i in range(621, 641)] == [
        "书状官", "后苑作、制造御前生活所", "后苑使", "权干办后苑官", "后苑大主管使臣",
        "提举后苑作生活所", "管勾龙图阁", "管勾天章阁", "管勾宝文阁",
        "勾当龙图、天章、宝文阁", "主管龙图、天章、宝文阁", "勾当军头、引见司",
        "干办军头、引见司", "翰林院", "勾当翰林院", "提举翰林院", "提点翰林院",
        "翰林天文院", "翰林天文局", "主管翰林天文局",
    ]
    assert "宫庭生活所需" in field(622, "职掌") and "镞镂作" in field(622, "编制")
    assert F[633]["text"].startswith("差遣名。南宋时改勾当官为干办官。")
    assert "998—1001）之间（" in field(638, "职源与沿革")
    assert ")" not in field(638, "职源与沿革")
    assert "淳熙七年（1180）" in F[640]["text"]
    entry621(); entry622(); entry623(); entry624(); entry625(); entry626(); entry627(); entry628()
    entry629(); entry630(); entry631(); entry632(); entry633(); entry634(); entry635(); entry636()
    entry637(); entry638(); entry639(); entry640()


if __name__ == "__main__":
    main()
