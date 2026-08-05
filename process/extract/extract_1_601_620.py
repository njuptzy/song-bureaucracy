#!/usr/bin/env python3
"""提取第一编第601-620条：合同凭由司与国信机构职官。"""

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
    """据原书第73-74页修复#603、#606-607、#618明显OCR。"""
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(f"SELECT text,fields FROM {table} WHERE id=603").fetchone()
            assert row and row[0] and row[1]
            f603 = json.loads(row[1])
            f603["编制"] = f603["编制"].replace("掌仪苑", "掌仪范")
            conn.execute(
                f"UPDATE {table} SET text=?,fields=? WHERE id=603",
                (
                    row[0].replace("入内 内侍省", "入内内侍省"),
                    json.dumps(f603, ensure_ascii=False),
                ),
            )
            row = conn.execute(f"SELECT text FROM {table} WHERE id=606").fetchone()
            assert row and row[0]
            fixed606 = row[0].replace("卷64)职掌", "卷64）。职掌").replace("卷64）职掌", "卷64）。职掌")
            conn.execute(f"UPDATE {table} SET text=? WHERE id=606", (fixed606,))
            row = conn.execute(f"SELECT text FROM {table} WHERE id=607").fetchone()
            assert row and row[0]
            conn.execute(f"UPDATE {table} SET text=? WHERE id=607", (row[0].replace(")", "）"),))
            row = conn.execute(f"SELECT fields FROM {table} WHERE id=618").fetchone()
            assert row and row[0]
            f618 = json.loads(row[0])
            f618["职源与沿革"] = f618["职源与沿革"].replace("绍兴三年(1133)", "绍兴三年（1133）")
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=618",
                (json.dumps(f618, ensure_ascii=False),),
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


F = {i: load(i) for i in range(601, 621)}


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


def inner_province_tp(w):
    return find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构")


def honglu_tp(w):
    return find_tp(w, "鸿胪寺", "宋前期", "机构")


def contract_tp(w):
    return find_tp(w, "合同凭由司", "北宋天禧五年（1021）十月以前", "机构")


def central_signal_tp(w):
    return find_tp(w, "管勾往来国信所", "北宋景德四年（1007）八月", "机构")


def alias_citation(w, i, tp_id, name):
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


def entry601():
    i = 601
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    old_e = w.entity("入内内侍省传宣合同司", "机构", "职源字段记载合同凭由司前身。", quotation=history)
    old = timepoint(
        w, i, old_e, "北宋天禧三年（1019）正月",
        "始置；太平兴国四年仅置合同凭由印、尚未置司",
        history, "建立传宣合同司始置节点。", "职源与沿革", category="内廷取索机构",
    )
    eid = find_entity(w, "合同凭由司", "机构")
    current = timepoint(
        w, i, eid, "北宋天禧五年（1021）十月以前",
        "由入内内侍省传宣合同司改名合同凭由司",
        history, "建立合同凭由司改名节点。", "职源与沿革",
        category="入内内侍省属司", chain="head",
    )
    generic = find_tp(w, "合同凭由司", "宋代（具体时间未载）", "机构")
    for name in ("职掌", "编制"):
        cite(w, "Timepoints", current, i, field(i, name), f"补证合同凭由司{name}。", name)
    relation(w, i, old, current, "前后演变", history, "天禧年间传宣合同司改名合同凭由司。", "职源与沿革")
    relation(w, i, inner_province_tp(w), current, "上下级机构", main, "合同凭由司隶入内内侍省。")
    alias_citation(w, i, current, "简称")
    w.commit()


def entry602():
    i = 602
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("监合同凭由司", "官职", "正式词头定义合同凭由司主管差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（具体时间未载）",
        "主管合同凭由司，掌御前及宫中取索和支领财物的合同证明文书",
        main, "建立监合同凭由司节点。", category="合同凭由司主管官",
    )
    relation(w, i, contract_tp(w), tp, "编制隶属", main, "监合同凭由司主管合同凭由司公事。", staff_type="监官", staff_quota="二人")
    w.commit()


def entry603():
    i = 603
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    old_e = w.entity("排办礼信所", "机构", "职源字段记载朝廷国信机构前身。", quotation=history)
    old = timepoint(
        w, i, old_e, "北宋景德初（1004—1007）", "设置",
        history, "建立排办礼信所节点。", "职源与沿革", category="朝廷外事机构",
    )
    eid = find_entity(w, "管勾往来国信所", "机构")
    start = timepoint(
        w, i, eid, "北宋景德四年（1007）八月", "特置管勾往来国信所",
        history, "建立朝廷管勾往来国信所始置节点。", "职源与沿革",
        category="朝廷外事机构", chain="head",
    )
    south = timepoint(
        w, i, eid, "南宋绍兴初（1131—1134）", "曾改称奉使大金国信所，和议后称主管往来国信所",
        history, "建立南宋名称演变承载节点。", "职源与沿革", category="朝廷外事机构",
    )
    for name in ("职掌", "编制"):
        cite(w, "Timepoints", start, i, field(i, name), f"补证管勾往来国信所{name}。", name)
    relation(w, i, old, start, "前后演变", history, "景德四年排办礼信所改置为管勾往来国信所。", "职源与沿革")
    relation(w, i, inner_province_tp(w), start, "上下级机构", main, "管勾往来国信所分隶入内内侍省。")
    relation(w, i, honglu_tp(w), start, "上下级机构", main, "管勾往来国信所亦分隶鸿胪寺。")
    alias_citation(w, i, start, "简称")
    w.commit()


def entry604():
    i = 604
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("机宜司", "机构", "正式词头定义雄州边境军要机构。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋咸平初（998—1000）", "雄州设置，掌边境军要机密",
        main, "建立雄州机宜司节点。", category="地方军要机构",
    )
    w.commit()


def entry605():
    i = 605
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("知雄州机宜司", "官职", "正式词头定义雄州机宜司长官差遣。", quotation=main)
    start = timepoint(
        w, i, eid, "北宋咸平初（998—1000）", "设置，为雄州机宜司长官",
        main, "建立知雄州机宜司始置节点。", category="地方军要机构长官",
    )
    timepoint(
        w, i, eid, "北宋景德二年（1005）三月十八日", "罢置",
        main, "建立知雄州机宜司罢置节点。", category="废罢",
    )
    relation(w, i, find_tp(w, "机宜司", "北宋咸平初（998—1000）", "机构"), start, "编制隶属", main, "知雄州机宜司为雄州机宜司长官。", staff_type="长官")
    w.commit()


def entry606():
    i = 606
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("国信司", "机构", "正式词头定义雄州接送辽使机构。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋景德三年（1006）十二月",
        "宋辽议和后由机宜司改名，掌接送辽国使者",
        main, "建立雄州国信司改名节点。", category="地方外事机构",
    )
    relation(w, i, find_tp(w, "机宜司", "北宋咸平初（998—1000）", "机构"), tp, "前后演变", main, "景德三年十二月，雄州机宜司改名国信司。")
    w.commit()


def entry607():
    i = 607
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("国信使", "官职", "正式词头定义接送辽使差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋大中祥符以后（1008以后）",
        "始置，负责接送辽国使者入境赴阙及出境回国",
        main, "建立国信使始置节点。", category="国信差遣",
    )
    relation(w, i, find_tp(w, "国信司", "北宋景德三年（1006）十二月", "机构"), tp, "编制隶属", main, "国信使承担国信司接送辽使事务。", staff_type="正使")
    w.commit()


def entry608():
    i = 608
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("国信副使", "官职", "正式词头定义国信副使差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋大中祥符以后（1008以后）", "始置，位次于国信使",
        main, "建立国信副使始置节点。", category="国信差遣",
    )
    relation(w, i, find_tp(w, "国信司", "北宋景德三年（1006）十二月", "机构"), tp, "编制隶属", main, "国信副使为国信司副使差遣。", staff_type="副使")
    w.commit()


def entry609():
    i = 609
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = w.entity("管勾国信", "官职", "正式词头定义往来国信所主管差遣。", quotation=main)
    start = timepoint(
        w, i, eid, "北宋景德四年（1007）八月", "始置，主掌辽使与宋朝廷往还交聘",
        history, "建立管勾国信始置节点。", "职源与沿革", category="国信所主管官",
    )
    south = timepoint(
        w, i, eid, "南宋时期（1127—1279）", "称主管往来国信所",
        history, "建立南宋改称节点。", "职源与沿革", category="国信所主管官",
    )
    for name in ("职掌", "品位", "编制"):
        cite(w, "Timepoints", start, i, field(i, name), f"补证管勾国信{name}。", name)
    relation(w, i, central_signal_tp(w), start, "编制隶属", main, "管勾国信隶管勾往来国信所。", staff_type="管勾官", staff_quota="二员")
    w.commit()


def entry610():
    i = 610
    w = W(i)
    main = F[i]["text"]
    agency_e = w.entity("主管往来国信所", "机构", "正文第一义定义南宋官司。", quotation=main)
    agency = timepoint(
        w, i, agency_e, "南宋绍兴四年（1134）七月", "始称主管往来国信所，掌金使往还交聘",
        main, "建立主管往来国信所机构节点。", category="朝廷外事机构",
    )
    settled = timepoint(
        w, i, agency_e, "南宋绍兴十二年（1142）以后", "绍兴和议后主管宋金往还交聘",
        main, "建立绍兴和议后职掌节点。", category="朝廷外事机构",
    )
    office_e = w.entity("主管往来国信所", "官职", "正文第二义定义南宋主管官差遣。", quotation=main)
    office = timepoint(
        w, i, office_e, "南宋绍兴四年（1134）七月",
        "主管往来国信所主管官，由入内内侍省押班以上中贵充任",
        main, "建立同名主管官节点。", category="国信所主管官",
    )
    relation(w, i, agency, office, "编制隶属", main, "主管往来国信所机构置同名主管官。", staff_type="主管官")
    relation(w, i, inner_province_tp(w), agency, "上下级机构", main, "主管往来国信所主管官由入内内侍省内侍充任，机构归属内侍系统。", note="正文明确主管官由入内内侍省押班以上充任")
    relation(
        w, i, find_tp(w, "管勾国信", "南宋时期（1127—1279）", "官职"),
        office, "前后演变", main, "南宋管勾国信改称主管往来国信所主管官。",
    )
    alias_citation(w, i, agency, "简称")
    w.commit()


def entry611():
    i = 611
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("国信所回易库干办公事", "官职", "正式词头定义国信所回易库主管差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋绍兴十七年（1147）一月十六日",
        "设置，掌领国信所回易库及贸易经营",
        main, "建立回易库干办公事节点。", category="国信所属官",
    )
    relation(w, i, find_tp(w, "主管往来国信所", "南宋绍兴十二年（1142）以后", "机构"), tp, "编制隶属", main, "国信所回易库干办公事隶主管往来国信所。", staff_type="干办官", staff_quota="二员")
    w.commit()


def entry612():
    i = 612
    w = W(i)
    main = F[i]["text"]
    eid = distinct_entity(w, "掌仪范", "官职", main, "本条掌仪范隶国信所，与既有教坊同名官职分建实体。")
    tp = timepoint(
        w, i, eid, "宋代（国信所，具体时间未载）",
        "掌引接外国使者到阙时应遵行的礼貌与规范",
        main, "建立国信所掌仪范节点。", category="国信所属官",
    )
    relation(w, i, central_signal_tp(w), tp, "编制隶属", main, "掌仪范隶管勾往来国信所。", staff_type="掌仪")
    relation(w, i, find_tp(w, "主管往来国信所", "南宋绍兴十二年（1142）以后", "机构"), tp, "编制隶属", main, "南宋掌仪范隶主管往来国信所。", staff_type="掌仪")
    alias_citation(w, i, tp, "简称")
    w.commit()


def signal_office(i, category, officer_type=None):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正式词头定义国信所差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "宋代（国信所，具体时间未载）", main,
        main, f"建立{F[i]['title']}国信所节点。", category=category, officer_type=officer_type,
    )
    relation(w, i, find_tp(w, "管勾往来国信所", "宋代（具体时间未载）", "机构"), tp, "编制隶属", main, f"{F[i]['title']}隶国信所。", staff_type=category)
    w.commit()


def entry613(): signal_office(613, "国信所通事", "品官")
def entry614(): signal_office(614, "国信所通事", "非品官")


def entry615():
    i = 615
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("通事", "官职", "正文定义大通事、小通事通称。", quotation=main)
    tp = timepoint(w, i, eid, "宋代（国信所，具体时间未载）", "大通事、小通事通称", main, "建立通事统称节点。", category="国信所通事总称")
    for title in ("大通事", "小通事"):
        relation(w, i, tp, find_tp(w, title, "宋代（国信所，具体时间未载）", "官职"), "统称与实例", main, f"通事为统称，{title}为实例。")
    w.commit()


def entry616():
    i = 616
    w = W(i)
    main = F[i]["text"]
    eid = w.entity("通事殿侍", "官职", "正式词头定义以殿侍充通事的差遣。", quotation=main)
    tp = timepoint(w, i, eid, "宋代（国信所，具体时间未载）", "以殿侍充通事差遣", main, "建立通事殿侍节点。", category="国信所通事")
    relation(w, i, find_tp(w, "通事", "宋代（国信所，具体时间未载）", "官职"), tp, "统称与实例", main, "通事为统称，通事殿侍为实例。")
    relation(w, i, find_tp(w, "管勾往来国信所", "宋代（具体时间未载）", "机构"), tp, "编制隶属", main, "通事殿侍隶国信所。", staff_type="通事")
    w.commit()


def entry617(): signal_office(617, "国信所译语", "殿侍")


def entry618():
    i = 618
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    eid = w.entity("奉使大金国信所", "机构", "正式词头定义南宋对金外事机构。", quotation=main)
    start = timepoint(
        w, i, eid, "南宋绍兴三年（1133）三月", "始见设置",
        history, "建立奉使大金国信所始见节点。", "职源与沿革", category="朝廷外事机构",
    )
    replaced = timepoint(
        w, i, eid, "南宋绍兴十二年（1142）", "绍兴和议后由主管往来国信所取代",
        history, "建立绍兴和议后被取代节点。", "职源与沿革", category="机构演变",
    )
    restored = timepoint(
        w, i, eid, "南宋乾道七年（1171）", "再置，与主管往来国信所并存",
        history, "建立乾道七年再置节点。", "职源与沿革", category="朝廷外事机构",
    )
    cite(w, "Timepoints", start, i, field(i, "职掌"), "补证奉使大金国信所属官与吏额。", "职掌")
    relation(
        w, i, find_tp(w, "管勾往来国信所", "南宋绍兴初（1131—1134）", "机构"),
        start, "前后演变", history, "南宋绍兴初管勾往来国信所曾改称奉使大金国信所。", "职源与沿革",
    )
    relation(
        w, i, replaced,
        find_tp(w, "主管往来国信所", "南宋绍兴十二年（1142）以后", "机构"),
        "前后演变", history, "绍兴和议后奉使大金国信所由主管往来国信所取代。", "职源与沿革",
    )
    alias_citation(w, i, start, "简称")
    w.commit()


def embassy_office(i, title):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(title, "官职", "正式词头定义奉使所差遣。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋时期（奉使大金国信所，具体时间未载）", main,
        main, f"建立{title}奉使所节点。", category="奉使所属官",
    )
    relation(w, i, find_tp(w, "奉使大金国信所", "南宋绍兴三年（1133）三月", "机构"), tp, "编制隶属", main, f"{title}隶奉使大金国信所。", staff_type="奉使所属官")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry619(): embassy_office(619, "都辖礼物官")
def entry620(): embassy_office(620, "引接仪范")


def main():
    assert [F[i]["title"] for i in range(601, 621)] == [
        "合同凭由司", "监合同凭由司", "管勾往来国信所", "机宜司", "知雄州机宜司",
        "国信司", "国信使", "国信副使", "管勾国信", "主管往来国信所",
        "国信所回易库干办公事", "掌仪范", "大通事", "小通事", "通事", "通事殿侍",
        "译语殿侍", "奉使大金国信所", "都辖礼物官", "引接仪范",
    ]
    assert "入内内侍省与鸿胪寺" in F[603]["text"] and "掌仪范" in field(603, "编制")
    assert "卷64）。职掌" in F[606]["text"] and ")" not in F[607]["text"]
    assert "绍兴三年（1133）" in field(618, "职源与沿革")
    entry601(); entry602(); entry603(); entry604(); entry605(); entry606(); entry607(); entry608()
    entry609(); entry610(); entry611(); entry612(); entry613(); entry614(); entry615(); entry616()
    entry617(); entry618(); entry619(); entry620()


if __name__ == "__main__":
    main()
