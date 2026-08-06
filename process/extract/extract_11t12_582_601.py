#!/usr/bin/env python3
"""提取 chapter11t12 第582-601条：提点、管勾、岳庙、义官与散官前六等。"""

import importlib.util
import json
import os
import sqlite3
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DICT_DB = ROOT / "data/database/song_bureaucracy_dictionary_ch11t12.db"
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    str(ROOT / "data/database/song_bureaucracy_entries_ch1t12.db"),
)

base_spec = importlib.util.spec_from_file_location(
    "extract_11t12_562_581_helpers", HERE / "extract_11t12_562_581.py"
)
base = importlib.util.module_from_spec(base_spec)
assert base_spec.loader is not None
base_spec.loader.exec_module(base)


def load(entry_id):
    with sqlite3.connect(DICT_DB) as connection:
        row = connection.execute(
            "SELECT title,page,text,fields FROM chapter11t12 WHERE id=?", (entry_id,)
        ).fetchone()
    assert row, entry_id
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {entry_id: load(entry_id) for entry_id in range(582, 602)}


def configure(module):
    module.F = F
    module.ENTRY_DB = ENTRY_DB
    child = getattr(module, "base", None)
    if child is not None:
        configure(child)
    helpers = getattr(module, "helpers", None)
    if helpers is not None:
        helpers.F = F
        helpers.ENTRY_DB = ENTRY_DB
        helpers.NEW_SORT = {}


configure(base)

W = base.W
Q = base.Q
state_event = base.state_event
typed_state_event = base.typed_state_event
relation = base.relation
append_event = base.append_event


def source(entry_id):
    return f'《宋代官制辞典》第{F[entry_id]["page"]}页“{F[entry_id]["title"]}”条'


def cite(writer, target_table, target_id, entry_id, quotation, decision, **kwargs):
    return writer.citation(
        target_table, target_id, source(entry_id), quotation, decision, **kwargs
    )


def sentence(entry_id, start_text):
    text = F[entry_id]["text"]
    start = text.index(start_text)
    return text[start:text.index("。", start) + 1]


def find_timepoint(writer, title, time, entity_type="官职"):
    entity = writer.find_entity(title, entity_type)
    assert entity is not None, (title, entity_type)
    timepoint = writer.find_timepoint(entity, time)
    assert timepoint is not None, (title, time)
    return timepoint


def link(writer, entry_id, subject, object_, kind, quote, decision):
    return relation(writer, entry_id, subject, object_, kind, quote, decision)


def group_link(writer, entry_id, group_title, group_time, member, quote, decision):
    group = find_timepoint(writer, group_title, group_time)
    return link(writer, entry_id, group, member, "统称与实例", quote, decision)


def institution(writer, entry_id, title, time, quote, order):
    _, tp = typed_state_event(
        writer, entry_id, title, "机构", time, f"{title}宫观机构",
        quote, f"据差遣官名建立{title}机构节点。",
        category="宫观", sort_order=order,
    )
    return tp


def office_with_groups(entry_id, title, time, event, quote, *, order,
                       institution_title=None, groups=(), officer="祠禄官"):
    writer = W(entry_id)
    _, office = state_event(
        writer, entry_id, title, time, event, quote,
        f"建立{title}{time}节点。", category="祠禄官",
        officer=officer, sort_order=order,
    )
    if institution_title:
        inst = institution(writer, entry_id, institution_title, time, quote, order)
        link(writer, entry_id, inst, office, "编制隶属", quote,
             f"{institution_title}设{title}差遣。")
    for group_title, group_time in groups:
        group_link(writer, entry_id, group_title, group_time, office, quote,
                   f"{title}为{group_title}实例。")
    writer.commit()


def extract_external_superintendents():
    entry_id = 582
    quote = Q(entry_id, "外祠官之一")
    office_with_groups(
        entry_id, "提举杭州洞霄宫", "宋代", "外祠差遣", quote,
        order=96000000, institution_title="杭州洞霄宫",
        groups=(("提举在外宫观", "北宋神宗熙宁三年"), ("外祠", "宋代")),
        officer="外祠提举",
    )

    entry_id = 583
    quote = Q(entry_id, F[entry_id]["text"])
    writer = W(entry_id)
    _, office = state_event(
        writer, entry_id, "提举南京鸿庆宫", "北宋神宗熙宁三年以前",
        "五旧宫观之一的外祠提举差遣", quote,
        "建立提举南京鸿庆宫北宋节点。", category="祠禄官",
        officer="外祠提举", sort_order=106905000,
    )
    palace = institution(writer, entry_id, "南京鸿庆宫", "北宋神宗熙宁三年以前", quote, 106905000)
    link(writer, entry_id, palace, office, "编制隶属", quote,
         "南京鸿庆宫设提举官。")
    group_link(writer, entry_id, "提举在外宫观", "北宋神宗熙宁三年五月以前", office, quote,
               "提举南京鸿庆宫为早期在外宫观提举实例。")
    group_link(writer, entry_id, "外祠", "宋代", office, quote,
               "专条明示提举南京鸿庆宫为外祠官。")
    _, south = state_event(
        writer, entry_id, "提举南京鸿庆宫", "南宋",
        "沿置；除实任一员外，其余祠禄官听便居住不赴任", quote,
        "建立南宋沿置节点。", category="祠禄官", officer="外祠提举",
        sort_order=112700000,
    )
    link(writer, entry_id, office, south, "前后演变", quote,
         "提举南京鸿庆宫由北宋沿置至南宋。")
    writer.commit()


def extract_palace_inspectors():
    entry_id = 584
    writer = W(entry_id)
    first = sentence(entry_id, "北宋仁宗朝")
    _, group = state_event(
        writer, entry_id, "提点宫观", "北宋仁宗朝", "已见提点某观公事官",
        first, "建立提点宫观始见节点。", category="祠禄官",
        officer="提点宫观总名", sort_order=102200000,
    )
    group_link(writer, entry_id, "祠禄官", "宋代", group, first,
               "提点宫观专条明示其为祠禄官总名。")
    for time, start, event, order in (
        ("北宋神宗熙宁五年十月十七日", "熙宁五年十月十七日", "定武臣、内侍充提举或提点的资序", 107210017),
        ("北宋徽宗政和三年八月二十四日", "至于文臣，政和三年八月二十四日", "定文臣充提点的资序", 111308024),
        ("南宋高宗绍兴五年闰二月二十二日", "南宋绍兴五年闰二月二十二日", "定陈乞宫观文臣充提点的资序", 113502022),
    ):
        quote = sentence(entry_id, start)
        _, new = state_event(
            writer, entry_id, "提点宫观", time, event, quote,
            f"建立提点宫观{time}制度节点。", category="祠禄官",
            officer="提点宫观总名", sort_order=order,
        )
        link(writer, entry_id, group, new, "前后演变", quote,
             "记录提点宫观资序规则的后续变化。")
        group = new
    writer.commit()

    for entry_id, title, palace_title in (
        (585, "提点万寿观公事", "万寿观"),
        (586, "提点佑神观公事", "佑神观"),
    ):
        quote = Q(entry_id, F[entry_id]["text"])
        writer = W(entry_id)
        _, office = state_event(
            writer, entry_id, title, "宋代", "内祠提点官，位次于提举而高于管勾（主管）",
            quote, f"建立{title}宋代节点。", category="祠禄官",
            officer="内祠提点", sort_order=96000000,
        )
        palace = institution(writer, entry_id, palace_title, "宋代", quote, 96000000)
        link(writer, entry_id, palace, office, "编制隶属", quote, f"{palace_title}设{title}。")
        group_link(writer, entry_id, "提点宫观", "北宋仁宗朝", office, quote,
                   f"{title}为提点宫观实例。")
        group_link(writer, entry_id, "内祠", "宋代", office, quote,
                   f"{title}专条明示其为内祠官。")
        writer.commit()


def extract_palace_managers():
    entry_id = 587
    writer = W(entry_id)
    early_quote = sentence(entry_id, "北宋神宗朝以前")
    _, early = state_event(
        writer, entry_id, "管勾宫观", "北宋神宗朝以前",
        "管勾某宫观公事等名目，由宰辅或翰林学士兼领，尚非祠禄官",
        early_quote, "建立管勾宫观早期制度节点。", category="宫观差遣",
        officer="管勾宫观总名", sort_order=106700000,
    )
    t7_quote = sentence(entry_id, "仁宗天圣七年")
    _, t7 = state_event(
        writer, entry_id, "管勾宫观", "北宋仁宗天圣七年",
        "以学士、中书舍人充景灵宫、会灵观、祥源观管勾官", t7_quote,
        "建立天圣七年管勾宫观除授节点。", category="宫观差遣",
        officer="管勾宫观总名", sort_order=102900000,
    )
    link(writer, entry_id, early, t7, "前后演变", t7_quote, "补记天圣七年管勾宫观的除授对象。")
    xining_quote = sentence(entry_id, "神宗熙宁三年五月")
    _, xining = state_event(
        writer, entry_id, "管勾宫观", "北宋神宗熙宁三年五月以后",
        "内外祠管勾官成为祠禄官", xining_quote,
        "建立熙宁以后管勾宫观转为祠禄官节点。", category="祠禄官",
        officer="管勾宫观总名", sort_order=107005000,
    )
    link(writer, entry_id, t7, xining, "前后演变", xining_quote, "管勾宫观于熙宁后转为祠禄官。")
    group_link(writer, entry_id, "祠禄官", "宋代", xining, xining_quote,
               "原文明示熙宁后管勾宫观为祠禄官。")
    south_quote = Q(entry_id, "南宋时改为主管某宫、某观公事")
    _, south = state_event(
        writer, entry_id, "主管宫观", "南宋", "管勾宫观改称主管某宫、某观公事",
        south_quote, "建立南宋主管宫观总名节点。", category="祠禄官",
        officer="主管宫观总名", sort_order=112700000,
    )
    link(writer, entry_id, xining, south, "前后演变", south_quote,
         "南宋管勾宫观改称主管宫观。")
    writer.commit()

    entry_id = 588
    writer = W(entry_id)
    start = sentence(entry_id, "北宋真宗天禧元年正月")
    _, office = state_event(
        writer, entry_id, "管勾祥源观公事", "北宋真宗天禧元年正月",
        "以宰相管勾新修祥源观，尚非祠禄官", start,
        "建立管勾祥源观公事始见节点。", category="宫观差遣",
        officer="内祠管勾", sort_order=101701000,
    )
    temple = find_timepoint(writer, "祥源观", "北宋真宗天禧二年闰四月", "机构")
    link(writer, entry_id, temple, office, "编制隶属", start, "祥源观设管勾公事官。")
    group_link(writer, entry_id, "管勾宫观", "北宋神宗朝以前", office, start,
               "管勾祥源观公事为管勾宫观实例。")
    group_link(writer, entry_id, "内祠", "宋代", office, Q(entry_id, "内祠官名"),
               "专条明示管勾祥源观公事为内祠官。")
    finish = sentence(entry_id, "天禧五年十月六日")
    _, finished = state_event(
        writer, entry_id, "管勾祥源观公事", "北宋真宗天禧五年十月六日",
        "祥源观修成，仍置管勾公事官", finish, "建立天禧五年沿置节点。",
        category="宫观差遣", officer="内祠管勾", sort_order=102110006,
    )
    link(writer, entry_id, office, finished, "前后演变", finish, "祥源观修成后仍置管勾公事官。")
    after = Q(entry_id, "熙宁后为祠禄官")
    _, sinecure = state_event(
        writer, entry_id, "管勾祥源观公事", "北宋神宗熙宁以后", "转为祠禄官",
        after, "建立熙宁后转为祠禄官节点。", category="祠禄官",
        officer="内祠管勾", sort_order=107000000,
    )
    link(writer, entry_id, finished, sinecure, "前后演变", after, "管勾祥源观公事于熙宁后转为祠禄官。")
    end = Q(entry_id, "南宋不置")
    _, abolished = state_event(
        writer, entry_id, "管勾祥源观公事", "南宋", "不置", end,
        "建立南宋不置节点。", category="祠禄官裁罢", officer="内祠管勾",
        sort_order=112700000,
    )
    link(writer, entry_id, sinecure, abolished, "前后演变", end, "南宋不再设管勾祥源观公事。")
    writer.commit()


def extract_external_managers():
    entry_id = 589
    quote = Q(entry_id, F[entry_id]["text"])
    office_with_groups(
        entry_id, "管勾兖州仙源县景灵宫太极观公事", "北宋神宗熙宁三年五月以前",
        "增置外州府宫观差遣前已置", quote, order=106905000,
        institution_title="兖州仙源县景灵宫太极观",
        groups=(("管勾宫观", "北宋神宗朝以前"), ("外祠", "宋代")),
        officer="外祠管勾",
    )

    entry_id = 590
    quote = Q(entry_id, F[entry_id]["text"])
    office_with_groups(
        entry_id, "主管台州崇道观", "南宋", "外祠主管差遣", quote,
        order=112700000, institution_title="台州崇道观",
        groups=(("主管宫观", "南宋"), ("外祠", "宋代")), officer="外祠主管",
    )

    entry_id = 591
    writer = W(entry_id)
    quote = Q(entry_id, F[entry_id]["text"])
    palace = institution(writer, entry_id, "成都府玉局观", "宋代", quote, 96000000)
    _, north = state_event(
        writer, entry_id, "管勾成都府玉局观", "北宋", "外祠管勾差遣；非自陈而特差者属黜降官",
        quote, "拆分混合词目，建立北宋管勾玉局观节点。", category="祠禄官",
        officer="外祠管勾", sort_order=96000000,
    )
    _, south = state_event(
        writer, entry_id, "主管成都府玉局观", "南宋", "管勾改称主管；非自陈而特差者属黜降官",
        quote, "拆分混合词目，建立南宋主管玉局观节点。", category="祠禄官",
        officer="外祠主管", sort_order=112700000,
    )
    link(writer, entry_id, palace, north, "编制隶属", quote, "成都府玉局观北宋设管勾差遣。")
    link(writer, entry_id, palace, south, "编制隶属", quote, "成都府玉局观南宋设主管差遣。")
    link(writer, entry_id, north, south, "前后演变", quote, "北宋管勾差遣至南宋改称主管。")
    group_link(writer, entry_id, "管勾宫观", "北宋神宗熙宁三年五月以后", north, quote, "管勾玉局观为管勾宫观实例。")
    group_link(writer, entry_id, "主管宫观", "南宋", south, quote, "主管玉局观为主管宫观实例。")
    group_link(writer, entry_id, "外祠", "宋代", north, quote, "管勾玉局观为外祠实例。")
    group_link(writer, entry_id, "外祠", "宋代", south, quote, "主管玉局观为外祠实例。")
    writer.commit()


def extract_temple_sinecures():
    entry_id = 592
    quote = Q(entry_id, F[entry_id]["text"])
    writer = W(entry_id)
    _, office = state_event(
        writer, entry_id, "监岳庙", "北宋神宗熙宁三年五月",
        "五岳庙监官列为祠禄官；或留一员掌庙事，余不赴任", quote,
        "建立监岳庙祠禄差遣节点。", category="祠禄官",
        officer="岳庙差遣", sort_order=107005000,
    )
    temple = find_timepoint(writer, "五岳庙", "宋代（未载具体年月）", "机构")
    link(writer, entry_id, temple, office, "编制隶属", quote, "五岳庙设监庙差遣。")
    group_link(writer, entry_id, "祠禄官", "宋代", office, quote, "监岳庙专条明示其为祠禄官。")
    group_link(writer, entry_id, "外祠", "北宋神宗熙宁三年以后", office, quote, "五岳庙差遣属熙宁后外祠。")
    writer.commit()

    entry_id = 593
    quote = Q(entry_id, F[entry_id]["text"])
    writer = W(entry_id)
    _, special = state_event(
        writer, entry_id, "破格岳庙", "南宋初",
        "选人无部阙可差者许给一次，月给比正差减半", quote,
        "建立南宋初破格岳庙节点。", category="祠禄官",
        officer="岳庙特殊差遣", sort_order=112700000,
    )
    general = find_timepoint(writer, "监岳庙", "北宋神宗熙宁三年五月")
    link(writer, entry_id, general, special, "统称与实例", quote, "破格岳庙为岳庙祠禄差遣的特殊实例。")
    group_link(writer, entry_id, "祠禄官", "宋代", special, quote, "破格岳庙专条明示其为祠禄官。")
    later = sentence(entry_id, "乾道二年八月")
    _, qd = state_event(
        writer, entry_id, "破格岳庙", "南宋孝宗乾道二年八月",
        "十三处战功显著人任满无阙可差者，再给一次", later,
        "建立乾道二年破格岳庙规则节点。", category="祠禄官",
        officer="岳庙特殊差遣", sort_order=116608000,
    )
    link(writer, entry_id, special, qd, "前后演变", later, "乾道二年扩展破格岳庙给授规则。")
    writer.commit()


def fixed_sanguan_state(writer, entry_id, time, event, quote, decision, *, grade=None):
    entity_id = 6581
    row = writer.conn.execute(
        "SELECT title,type FROM Entities WHERE id=?", (entity_id,)
    ).fetchone()
    assert row == ("散官", "官职"), row
    before = writer.find_timepoint(entity_id, time)
    tp = writer.timepoint(
        entity_id, time, event, decision, quote, attr_category="散官制",
        attr_officer_type="散官总名", attr_grade=grade, chain="tail",
    )
    append_event(writer, tp, event, decision, category="散官制", officer="散官总名", grade=grade)
    cite(writer, "Timepoints", tp, entry_id, quote, decision)
    return tp, before is None


def extract_honorary_offices():
    entry_id = 594
    quote = Q(entry_id, "道官、僧官称义官，或称冠带官")
    writer = W(entry_id)
    state_event(
        writer, entry_id, "义官", "宋代", "道官、僧官的称谓，又称冠带官", quote,
        "仅据条目定义建立宋代义官节点；不将明代例证写成宋代制度事实。",
        category="特殊官称", officer="道释官称", sort_order=96000000,
    )
    writer.commit()

    entry_id = 595
    quote = sentence(entry_id, "北宋政和三年十二月")
    writer = W(entry_id)
    north, _ = fixed_sanguan_state(
        writer, entry_id, "北宋徽宗政和三年十二月",
        "定散官为十等；用于安置贬降官、授纳粟人、恩泽恩例及特奏名授官",
        quote, "在真正的散官制度实体 id=6581 上建立政和十等节点。",
    )
    south_quote = Q(entry_id, "南宋沿置之")
    south, _ = fixed_sanguan_state(
        writer, entry_id, "南宋", "沿置北宋政和所定十等散官", south_quote,
        "在散官制度实体 id=6581 上建立南宋沿置节点。",
    )
    link(writer, entry_id, north, south, "前后演变", south_quote, "政和十等散官为南宋沿置。")
    writer.commit()


RANKS = {
    596: ("节度副使", 1, "从八品"),
    597: ("节度行军司马", 2, "从八品"),
    598: ("防御副使", 3, "从八品"),
    599: ("团练副使", 4, "从八品"),
    600: ("州别驾", 5, "正九品"),
    601: ("州长史", 6, "正九品"),
}


def extract_sanguan_ranks():
    for entry_id, (title, rank, grade) in RANKS.items():
        writer = W(entry_id)
        detail = Q(entry_id, F[entry_id]["text"])
        _, member = state_event(
            writer, entry_id, title, "北宋徽宗政和三年十二月以后",
            f"十等散官之第{rank}等", detail,
            f"据散官总条建立{title}政和改定后节点。", category="散官制",
            officer="散官", grade=grade, sort_order=111312000,
        )
        group = writer.find_timepoint(6581, "北宋徽宗政和三年十二月")
        assert group is not None
        link(writer, entry_id, group, member, "统称与实例", detail,
             f"{title}为政和所定十等散官之第{rank}等。")
        append_event(writer, member, F[entry_id]["text"], f"以{title}专条补足制沿与用途。", category="散官制", officer="散官", grade=grade)
        cite(writer, "Timepoints", member, entry_id, detail, f"补证{title}的位次、品级及用途。")
        writer.commit()


def main():
    expected = [
        "提举杭州洞霄宫", "提举南京鸿庆宫", "提点宫观", "提点万寿观公事",
        "提点佑神观公事", "管勾宫观", "管勾祥源观公事",
        "管勾兖州仙源县景灵宫太极观公事", "主管台州崇道观",
        "管勾（主管）成都府玉局观", "监岳庙", "破格岳庙", "义官", "散官",
        "节度副使", "节度行军司马", "防御副使", "团练副使", "州别驾", "州长史",
    ]
    assert [F[i]["title"] for i in range(582, 602)] == expected
    extract_external_superintendents()
    extract_palace_inspectors()
    extract_palace_managers()
    extract_external_managers()
    extract_temple_sinecures()
    extract_honorary_offices()
    extract_sanguan_ranks()


if __name__ == "__main__":
    main()
