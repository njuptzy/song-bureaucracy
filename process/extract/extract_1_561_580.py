#!/usr/bin/env python3
"""提取第一编第561-580条：寄班诸官、内侍称谓与御药院。"""

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


def repair_dictionary_source():
    """据原书第69-71页拆回#566-568，并修复本批明显OCR字误。"""
    text566 = "宦官名。隶内侍省寄班。"
    fields566 = {
        "简称": (
            "小底。《北辕录》：“小底入报，传旨免礼。”《宋会要·职官》57之8《俸禄》4："
            "“寄班小底四石。”原注：“旧式，除小底外，供奉官、殿头并三石。”同前书36之2"
            "《内侍省》：“又有寄班供奉、侍禁、殿直、奉职、小底，日奉内朝，以备乘传急诏；"
            "凡天子巡幸，则执乘御、服御。”"
        )
    }
    text567 = "宦官名。隶内侍省。"
    fields567 = {
        "职源": "宋初已置，真宗朝已改为内品、散内品（《宋会要·职官》36之6）。",
        "职能": "安排责降宦官。",
        "品位": "“决杖配洒扫班”，位遇卑下（《宋史·王仁睿传》）。",
        "编制": "有洒扫院子若干（《宋会要·职官》36之2）。",
        "简称": (
            "洒扫班。《宋史·王仁睿传》：“决杖配洒扫班。”《长编》卷190甲午："
            "“诏置狱，配宗礼西京洒扫班。”同前书卷192庚申：“梁怀吉配西京洒扫班。”"
        ),
    }
    text568 = "责降宦官名。隶内侍省洒扫班。"
    fields568 = {
        "职源与沿革": "宋初已置，大中祥符二年九月，改为散内品（《宋会要·职官》36之6）。",
        "职掌": "供给使、服差役。",
        "简称": (
            "院子。《宋会要·职官》36之6：“（大中祥符二年）九月，改洒扫院子为散内品，"
            "诸色请受、差役悉如院子。”"
        ),
    }
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(f"SELECT text FROM {table} WHERE id=561").fetchone()
            assert row and row[0]
            conn.execute(
                f"UPDATE {table} SET text=? WHERE id=561",
                (row[0].replace("宜官名", "宦官名"),),
            )
            for entry_id in (563, 564):
                row = conn.execute(f"SELECT text FROM {table} WHERE id=?", (entry_id,)).fetchone()
                assert row and row[0]
                conn.execute(
                    f"UPDATE {table} SET text=? WHERE id=?",
                    (row[0].replace(")", "）"), entry_id),
                )
            conn.execute(
                f"UPDATE {table} SET text=?,fields=? WHERE id=566",
                (text566, json.dumps(fields566, ensure_ascii=False)),
            )
            conn.execute(
                f"UPDATE {table} SET title='西京洒扫班',text=?,fields=? WHERE id=567",
                (text567, json.dumps(fields567, ensure_ascii=False)),
            )
            conn.execute(
                f"UPDATE {table} SET title='洒扫院子',text=?,fields=? WHERE id=568",
                (text568, json.dumps(fields568, ensure_ascii=False)),
            )
            row = conn.execute(f"SELECT text FROM {table} WHERE id=569").fetchone()
            assert row and row[0]
            conn.execute(
                f"UPDATE {table} SET text=? WHERE id=569",
                (row[0].replace("内容省使至内侍省内品", "内客省使至内侍省内品"),),
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


F = {i: load(i) for i in range(561, 581)}


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


def province_tp(w):
    return find_tp(w, "内侍省", "北宋景德三年（1006）五月", "机构")


def inner_province_tp(w):
    return find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构")


def waiting_group_tp(w):
    return find_tp(w, "内侍省寄班", "北宋咸平三年（1000）正月以前", "官职")


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；称谓不另建实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def detailed_waiting_office(i, time, event, aliases=()):
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    tp = timepoint(
        w, i, eid, time, event, main,
        f"建立{F[i]['title']}专条始见节点。",
        category="寄班使臣",
    )
    relation(
        w, i, waiting_group_tp(w), tp, "统称与实例", main,
        f"内侍省寄班为统称，{F[i]['title']}为实例。",
    )
    relation(
        w, i, province_tp(w), tp, "编制隶属", main,
        f"{F[i]['title']}隶内侍省。", staff_type="寄班",
    )
    for name in aliases:
        alias_citation(w, i, tp, name)
    w.commit()


def entry561():
    detailed_waiting_office(
        561, "北宋咸平三年（1000）正月六日", "已见设置"
    )


def entry562():
    detailed_waiting_office(562, "北宋景德初（1004—1006）", "已设置")


def entry563():
    detailed_waiting_office(
        563, "北宋景德初（1004—1006）", "已设置", aliases=("简称",)
    )


def entry564():
    detailed_waiting_office(564, "北宋景德初（1004—1006）", "已设置")


def entry565():
    detailed_waiting_office(565, "北宋熙宁七年（1074）", "已见设置")


def entry566():
    i = 566
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, "寄班小底", "官职")
    tp = find_tp(w, "寄班小底", "北宋时期（具体时间未载）", "官职")
    cite(w, "Timepoints", tp, i, main, "补证寄班小底隶内侍省寄班。")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry567():
    i = 567
    w = W(i)
    main = F[i]["text"]
    origin = field(i, "职源")
    eid = w.entity("西京洒扫班", "官职", "正式词头定义责降宦官所属洒扫班。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋初", "设置，安排责降宦官；真宗朝已改为内品、散内品",
        origin, "建立西京洒扫班宋初节点。", "职源", category="责降宦官班",
    )
    for name in ("职能", "品位", "编制"):
        cite(w, "Timepoints", tp, i, field(i, name), f"补证西京洒扫班{name}。", name)
    relation(
        w, i, province_tp(w), tp, "编制隶属", main,
        "西京洒扫班隶内侍省。", staff_type="责降宦官班",
    )
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry568():
    i = 568
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, "洒扫院子", "官职")
    early = timepoint(
        w, i, eid, "宋初", "作为责降宦官，隶内侍省洒扫班，供给使、服差役",
        history, "建立洒扫院子宋初节点。", "职源与沿革", category="责降宦官",
        chain="head",
    )
    cite(w, "Timepoints", early, i, field(i, "职掌"), "补证供给使、服差役职掌。", "职掌")
    changed = timepoint(
        w, i, eid, "北宋大中祥符二年（1009）九月", "改为散内品",
        history, "建立洒扫院子改名节点。", "职源与沿革", category="改名",
    )
    relation(
        w, i, find_tp(w, "西京洒扫班", "宋初", "官职"), early,
        "统称与实例", main, "西京洒扫班为统称，洒扫院子为其编制实例。",
    )
    relation(
        w, i, province_tp(w), early, "编制隶属", main,
        "洒扫院子隶内侍省洒扫班，间接隶内侍省。", staff_type="责降宦官",
    )
    relation(
        w, i, changed,
        find_tp(w, "散内品", "北宋大中祥符二年（1009）九月", "官职"),
        "前后演变", history, "大中祥符二年九月，洒扫院子改为散内品。", "职源与沿革",
    )
    alias_citation(w, i, early, "简称")
    w.commit()


def entry569():
    i = 569
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("内侍官", "官职", "正文定义其为宋代宦官正式通称。", quotation=main)
    base = timepoint(
        w, i, eid, "宋代（具体时间未载）", "宋代宦官通称",
        main, "建立内侍官宋代通称节点。", category="宦官通称",
    )
    north_quote = "北宋徽宗政和二年定官称，自入内内侍省、内侍省长官（知入内省事、内侍省都知）至诸内品止，统称为内侍官"
    north = timepoint(
        w, i, eid, "北宋政和二年（1112）",
        "定官称：自两省长官至诸内品统称内侍官",
        north_quote, "建立政和二年定官称节点。", category="宦官通称",
    )
    south_quote = "南宋时，除入内省、内侍省宦官称“内侍官”之外，还包括内侍班官内客省使、延福宫使、景福殿使、宣庆使、宣政使、昭宣使"
    south = timepoint(
        w, i, eid, "南宋时期（1127—1279）",
        "范围包括两省宦官及内客省使等六种内侍班官",
        south_quote, "建立南宋内侍官范围节点。", category="宦官通称",
    )
    for title, when in (
        ("入内内侍省内侍班", "北宋大中祥符二年（1009）二月"),
        ("入内内侍省祗候班", "北宋政和二年（1112）"),
        ("入内内侍省寄班", "宋代（具体时间未载）"),
        ("内侍省内侍班", "北宋大中祥符二年（1009）二月"),
        ("内侍省祗候班", "北宋元丰改制"),
        ("内侍省寄班", "北宋时期（具体时间未载）"),
    ):
        relation(
            w, i, north, find_tp(w, title, when, "官职"), "统称与实例",
            north_quote, f"政和二年内侍官统称覆盖{title}所属官员。",
        )
    for title in ("内客省使", "延福宫使", "景福殿使", "宣庆使", "宣政使", "昭宣使"):
        child_e = w.entity(title, "官职", "南宋内侍官范围正文明列该内侍班官。", quotation=south_quote)
        child_tp = timepoint(
            w, i, child_e, "南宋时期（1127—1279）", "列入内侍官范围",
            south_quote, f"建立{title}南宋内侍班官节点。", category="内侍班官",
        )
        relation(
            w, i, south, child_tp, "统称与实例", south_quote,
            f"内侍官为统称，{title}为南宋明列实例。",
        )
    cite(
        w, "Timepoints", base, i, field(i, "别名"),
        "补证内侍官各类异称；均仅作称谓证据，不逐一建实体。", "别名",
        note="别名字段诸称谓仅作证据，不另建实体",
    )
    w.commit()


def inner_title(i, time, event, category):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正式词头定义内侍称谓或差使。", quotation=main)
    tp = timepoint(
        w, i, eid, time, event, main,
        f"建立{F[i]['title']}节点。", category=category,
    )
    relation(
        w, i, find_tp(w, "内侍官", "宋代（具体时间未载）", "官职"), tp,
        "统称与实例", main, f"内侍官为统称，{F[i]['title']}为其称谓或差使实例。",
    )
    w.commit()


def entry570():
    inner_title(570, "宋代（具体时间未载）", "衔命出使的内侍称中使", "内侍奉使称谓")


def entry571():
    inner_title(571, "宋代（具体时间未载）", "接近帝后且有权势的大宦官称中贵或中贵人", "内侍称谓")


def entry572():
    inner_title(572, "北宋宣和年间（1119—1125）", "内臣传宣诏敕于外称诏使", "内侍奉使称谓")


def entry573():
    inner_title(573, "宋代（具体时间未载）", "中使的尊称", "内侍尊称")


def entry574():
    inner_title(574, "宋代（具体时间未载）", "阁长以上内侍官的俗称，称谓始于唐", "内侍上等称谓")


def entry575():
    inner_title(575, "宋代（具体时间未载）", "中等内侍的俗称", "内侍中等称谓")


def entry576():
    i = 576
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("宫都监", "官职", "正式词头定义由内侍充任的宫中都监差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）",
        "诸后宫、太上皇宫及东宫等所设都监，由内侍充，管领宫中日常生活事务",
        main, "建立宫都监差遣节点。", category="内侍差遣",
    )
    relation(
        w, i, find_tp(w, "内侍官", "宋代（具体时间未载）", "官职"), tp,
        "统称与实例", main, "宫都监由内侍充任，是内侍官差遣实例。",
    )
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry577():
    i = 577
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("都监", "官职", "正式词头定义内侍在内庭、在京百司所充都监差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）",
        "内侍在内庭、在京百司充任，监督人吏、财物出纳及排办公事",
        main, "建立内侍都监差遣节点。", category="内侍差遣",
    )
    relation(
        w, i, tp, find_tp(w, "宫都监", "宋代（具体时间未载）", "官职"),
        "统称与实例", main, "都监为内侍差遣通称，宫都监为正文明列诸宫都监实例。",
    )
    relation(
        w, i, find_tp(w, "内侍官", "宋代（具体时间未载）", "官职"), tp,
        "统称与实例", main, "都监为内侍官差遣实例。",
    )
    w.commit()


def entry578():
    i = 578
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = find_entity(w, "御药院", "机构")
    song = timepoint(
        w, i, eid, "北宋至道三年（997）", "始置，隶入内内侍省",
        history, "建立御药院北宋始置节点。", "职源与沿革",
        category="内廷供药机构", chain="head",
    )
    tang = timepoint(
        w, i, eid, "唐代", "殿中省尚药局已有御药院",
        history, "建立御药院唐代职源节点。", "职源与沿革",
        category="前代职源", chain="head",
    )
    for name in ("职掌", "编制", "位遇"):
        cite(w, "Timepoints", song, i, field(i, name), f"补证御药院{name}。", name)
    relation(
        w, i, inner_province_tp(w), song, "上下级机构", main,
        "御药院初隶入内内侍省；上级节点采用景德三年正式设置节点。",
        note="御药院始置早于入内内侍省正式定名，按辞典所载归属连接后者正式节点",
    )
    chongning = find_tp(w, "御药院", "北宋崇宁二年二月", "机构")
    cite(w, "Timepoints", chongning, i, history, "补证崇宁二年二月并入殿中省并改名。", "职源与沿革")
    relation(
        w, i,
        find_tp(w, "殿中省", "北宋崇宁二年二月十二日", "机构"),
        chongning, "上下级机构", history,
        "崇宁二年二月十二日，御药院并入殿中省。", "职源与沿革",
    )
    inner_e = find_entity(w, "内药局", "机构")
    inner_feb = timepoint(
        w, i, inner_e, "北宋崇宁二年二月十二日",
        "本条记御药院并入殿中省并改名内药局；与另据五月九日改名的记录日期不一",
        history, "保留本条所载二月十二日改名说。", "职源与沿革",
        category="内廷供药机构", chain="head", conflict_flag=1,
        note="与既有五月九日改名记录日期不一，两说并存",
    )
    relation(
        w, i, chongning, inner_feb, "前后演变", history,
        "本条记崇宁二年二月十二日御药院改名内药局。", "职源与沿革",
        conflict_flag=1, note="另有五月九日改名记录，两说并存",
    )
    restored = find_tp(w, "御药院", "北宋靖康元年正月五日", "机构")
    cite(w, "Timepoints", restored, i, history, "补证靖康元年罢殿中省后御药院复归入内省。", "职源与沿革")
    relation(
        w, i,
        find_tp(w, "入内内侍省", "北宋靖康元年正月五日", "机构"),
        restored, "上下级机构", history,
        "靖康元年御药院复归入内内侍省。", "职源与沿革",
    )
    south = find_tp(w, "御药院", "宋代（具体时间未载）", "机构")
    cite(w, "Timepoints", south, i, history, "补证南宋仍称御药院。", "职源与沿革")
    alias_citation(w, i, song, "简称与别名")
    w.commit()


def distinct_institution(w, title, quotation, decision):
    row = w.conn.execute(
        "SELECT id FROM Entities WHERE title=? AND type='机构' AND quotation=? ORDER BY id LIMIT 1",
        (title, quotation),
    ).fetchone()
    if row:
        return row[0]
    return w._insert(
        "INSERT INTO Entities (title,type,quotation) VALUES (?,'机构',?)",
        (title, quotation), "Entities", decision,
    )


def medicine_case(i):
    w = W(i)
    main = F[i]["text"]
    if F[i]["title"] == "杂事案":
        eid = distinct_institution(
            w, "杂事案", main,
            "本条为御药院杂事案，与既有御史台杂事案同名异机构，按正式词头分建实体。",
        )
    else:
        eid = w.entity(F[i]["title"], "机构", "正式词头定义御药院办事机构。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）", main,
        main, f"建立御药院{F[i]['title']}办事节点。", category="御药院办事机构",
    )
    relation(
        w, i, find_tp(w, "御药院", "宋代（具体时间未载）", "机构"),
        tp, "上下级机构", main, f"{F[i]['title']}为御药院办事机构。",
    )
    w.commit()


def entry579(): medicine_case(579)
def entry580(): medicine_case(580)


def main():
    assert [F[i]["title"] for i in range(561, 581)] == [
        "寄班供奉", "寄班侍禁", "寄班殿直", "寄班奉职", "寄班借职", "寄班小底",
        "西京洒扫班", "洒扫院子", "内侍官", "中使", "中贵、中贵人", "诏使",
        "日边人", "大官", "阁长", "宫都监", "都监", "御药院", "生熟药案", "杂事案",
    ]
    assert F[566]["text"] == "宦官名。隶内侍省寄班。"
    assert set(F[567]["fields"]) == {"职源", "职能", "品位", "编制", "简称"}
    assert set(F[568]["fields"]) == {"职源与沿革", "职掌", "简称"}
    assert "内客省使至内侍省内品" in F[569]["text"]
    entry561(); entry562(); entry563(); entry564(); entry565(); entry566(); entry567(); entry568()
    entry569(); entry570(); entry571(); entry572(); entry573(); entry574(); entry575(); entry576()
    entry577(); entry578(); entry579(); entry580()


if __name__ == "__main__":
    main()
