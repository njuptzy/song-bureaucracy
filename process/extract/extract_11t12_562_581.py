#!/usr/bin/env python3
"""提取 chapter11t12 第562-581条：宫观使、宫观官与提举内外宫观。"""

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
    "extract_11t12_542_561_helpers", HERE / "extract_11t12_542_561.py"
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


F = {entry_id: load(entry_id) for entry_id in range(562, 582)}


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


def field_quote(entry_id, field_name, needle):
    value = F[entry_id]["fields"][field_name]
    assert needle in value, (entry_id, field_name, needle)
    return needle


def find_timepoint(writer, title, time, entity_type="官职"):
    entity = writer.find_entity(title, entity_type)
    assert entity is not None, (title, entity_type)
    timepoint = writer.find_timepoint(entity, time)
    assert timepoint is not None, (title, time)
    return timepoint


def link_group(writer, entry_id, group_title, group_time, member, quote, decision):
    group = find_timepoint(writer, group_title, group_time)
    return relation(
        writer, entry_id, group, member, "统称与实例", quote, decision
    )


def link_institution(writer, entry_id, institution, office, quote, decision):
    return relation(
        writer, entry_id, institution, office, "编制隶属", quote, decision
    )


def evolve(writer, entry_id, old, new, quote, decision):
    return relation(writer, entry_id, old, new, "前后演变", quote, decision)


def extract_jingling_palace_commissioner():
    entry_id = 562
    writer = W(entry_id)
    build = sentence(entry_id, "北宋大中祥符五年十一月")
    _, palace = typed_state_event(
        writer, entry_id, "景灵宫", "机构",
        "北宋真宗大中祥符五年十一月", "始建，以奉圣祖及圣祖母",
        build, "建立景灵宫始建节点。", category="宫观",
        sort_order=101211000,
    )
    start = sentence(entry_id, "祥符七年八月")
    _, office = state_event(
        writer, entry_id, "景灵宫使", "北宋真宗大中祥符七年八月",
        "始以宰相向敏中领使", start, "建立景灵宫使始置节点。",
        category="宫观使", officer="宫观使", sort_order=101408000,
    )
    link_institution(
        writer, entry_id, palace, office, start, "景灵宫设置景灵宫使。"
    )
    link_group(
        writer, entry_id, "宫观使", "北宋真宗大中祥符四年十一月",
        office, start, "景灵宫使为宫观使实例。",
    )
    sinecure = sentence(entry_id, "仁宗明道中")
    _, sinecure_tp = state_event(
        writer, entry_id, "景灵宫使", "北宋仁宗明道中",
        "使相钱惟演领使，始为祠禄官", sinecure,
        "记录景灵宫使转为祠禄官。", category="祠禄官",
        officer="宫观使", sort_order=103200000,
    )
    evolve(
        writer, entry_id, office, sinecure_tp, sinecure,
        "景灵宫使在仁宗明道中始具祠禄官性质。",
    )
    link_group(
        writer, entry_id, "祠禄官", "宋代", sinecure_tp, sinecure,
        "景灵宫使专条明示其为祠禄官。",
    )
    writer.commit()


def extract_xiangyuan_and_liquan_commissioners():
    entry_id = 563
    writer = W(entry_id)
    build = sentence(entry_id, "北宋天禧元年")
    _, temple = typed_state_event(
        writer, entry_id, "祥源观", "机构", "北宋真宗天禧二年闰四月",
        "于真武堂侧出泉之地建观", build, "建立祥源观始建节点。",
        category="宫观", sort_order=101804500,
    )
    start = Q(entry_id, "仁宗乾兴元年七月，始以枢密副使钱惟演领祥源观使")
    _, office = state_event(
        writer, entry_id, "祥源观使", "北宋仁宗乾兴元年七月",
        "始以枢密副使钱惟演领使", start, "建立祥源观使始置节点。",
        category="宫观使", officer="宫观使", sort_order=102207000,
    )
    link_institution(
        writer, entry_id, temple, office, start, "祥源观设置祥源观使。"
    )
    link_group(
        writer, entry_id, "宫观使", "北宋真宗大中祥符四年十一月",
        office, start, "祥源观使为宫观使实例。",
    )
    charge = Q(entry_id, "天圣六年十二月，以参知政事鲁宗道充祥源观使")
    _, charge_tp = state_event(
        writer, entry_id, "祥源观使", "北宋仁宗天圣六年十二月",
        "以参知政事鲁宗道充使", charge, "记录天圣六年祥源观使除授。",
        category="宫观使", officer="宫观使", sort_order=102812000,
    )
    evolve(writer, entry_id, office, charge_tp, charge, "祥源观使除授沿续。")
    change = Q(entry_id, "天圣七年七月，罢宰辅领宫观使")
    _, changed = state_event(
        writer, entry_id, "祥源观使", "北宋仁宗天圣七年七月",
        "罢宰辅领宫观使", change, "记录祥源观使领使规则变化。",
        category="宫观使改革", officer="宫观使", sort_order=102907000,
    )
    evolve(
        writer, entry_id, charge_tp, changed, change,
        "天圣七年罢宰辅领宫观使。",
    )
    writer.commit()

    entry_id = 564
    writer = W(entry_id)
    rename = sentence(entry_id, "旧有祥源观")
    old = find_timepoint(writer, "祥源观", "北宋真宗天禧二年闰四月", "机构")
    _, new_temple = typed_state_event(
        writer, entry_id, "醴泉观", "机构",
        "北宋仁宗至和二年十二月二十九日",
        "祥源观火灾后重修新观，易名醴泉观", rename,
        "建立醴泉观改名节点。", category="宫观", sort_order=105512029,
    )
    evolve(
        writer, entry_id, old, new_temple, rename,
        "祥源观火灾后重修并改名醴泉观。",
    )
    start = sentence(entry_id, "英宗治平三年八月")
    _, new_office = state_event(
        writer, entry_id, "醴泉观使", "北宋英宗治平三年八月",
        "以武康军节度使李端愿领使，始为祠禄官", start,
        "建立醴泉观使始置及祠禄官节点。", category="祠禄官",
        officer="宫观使", sort_order=106608000,
    )
    link_institution(
        writer, entry_id, new_temple, new_office, start,
        "醴泉观设置醴泉观使。",
    )
    old_office = find_timepoint(writer, "祥源观使", "北宋仁宗天圣七年七月")
    evolve(
        writer, entry_id, old_office, new_office, start,
        "祥源观改名醴泉观后，治平三年置醴泉观使。",
    )
    link_group(
        writer, entry_id, "宫观使", "北宋仁宗天圣七年七月",
        new_office, start, "醴泉观使为宫观使实例。",
    )
    link_group(
        writer, entry_id, "祠禄官", "宋代", new_office, start,
        "醴泉观使专条明示其始为祠禄官。",
    )
    south = Q(entry_id, "南宋时，前宰相奉祠多得醴泉观使")
    _, south_tp = state_event(
        writer, entry_id, "醴泉观使", "南宋",
        "前宰相奉祠多授此使", south, "记录南宋醴泉观使除授对象。",
        category="祠禄官", officer="宫观使", sort_order=112700000,
    )
    evolve(
        writer, entry_id, new_office, south_tp, south,
        "醴泉观使沿用于南宋前宰相奉祠。",
    )
    writer.commit()


def extract_joint_liquan_commissioner():
    entry_id = 565
    writer = W(entry_id)
    start = sentence(entry_id, "北宋元祐八年六月十二日")
    _, office = state_event(
        writer, entry_id, "同醴泉观使", "北宋哲宗元祐八年六月十二日",
        "为执政梁焘特置，以资政殿学士领同使", start,
        "建立同醴泉观使特置节点。", category="祠禄官",
        officer="宫观使", sort_order=109306012,
    )
    temple = find_timepoint(
        writer, "醴泉观", "北宋仁宗至和二年十二月二十九日", "机构"
    )
    link_institution(
        writer, entry_id, temple, office, start, "醴泉观特置同醴泉观使。"
    )
    link_group(
        writer, entry_id, "宫观使", "北宋神宗熙宁以后",
        office, start, "同醴泉观使为宫观使实例。",
    )
    link_group(
        writer, entry_id, "祠禄官", "宋代", office, start,
        "同醴泉观使专条明示其为祠禄官。",
    )
    end = Q(entry_id, "其后，即有以前二府官为学士带宫观使者，同使不复除")
    _, stopped = state_event(
        writer, entry_id, "同醴泉观使", "北宋哲宗元祐八年以后",
        "此后同使不复除", end, "记录同醴泉观使停止除授。",
        category="宫观使改革", officer="宫观使", sort_order=109306013,
    )
    evolve(
        writer, entry_id, office, stopped, end,
        "特置同醴泉观使后，同使不再除授。",
    )
    writer.commit()


def extract_huiling_and_jixi_commissioners():
    entry_id = 566
    writer = W(entry_id)
    build = sentence(entry_id, "北宋真宗大中祥符五年九月")
    _, temple = typed_state_event(
        writer, entry_id, "会灵观", "机构", "北宋真宗大中祥符七年九月",
        "奉祀五岳帝之观改名会灵观", build, "建立会灵观改名节点。",
        category="宫观", sort_order=101409000,
    )
    start = Q(entry_id, "天禧元年三月，以宰相王钦若领会灵观使")
    _, office = state_event(
        writer, entry_id, "会灵观使", "北宋真宗天禧元年三月",
        "以宰相王钦若领使", start, "建立会灵观使始置节点。",
        category="宫观使", officer="宫观使", sort_order=101703000,
    )
    link_institution(
        writer, entry_id, temple, office, start, "会灵观设置会灵观使。"
    )
    link_group(
        writer, entry_id, "宫观使", "北宋真宗大中祥符四年十一月",
        office, start, "会灵观使为宫观使实例。",
    )
    change = Q(entry_id, "仁宗天圣七年七月罢宰辅领宫观使")
    _, changed = state_event(
        writer, entry_id, "会灵观使", "北宋仁宗天圣七年七月",
        "罢宰辅领宫观使", change, "记录会灵观使领使规则变化。",
        category="宫观使改革", officer="宫观使", sort_order=102907000,
    )
    evolve(writer, entry_id, office, changed, change, "天圣七年罢宰辅领宫观使。")
    revival = Q(entry_id, "钦宗靖康朝，宰辅仍领本使")
    _, revival_tp = state_event(
        writer, entry_id, "会灵观使", "北宋钦宗靖康朝",
        "宰辅仍领本使", revival, "记录靖康朝会灵观使仍置。",
        category="宫观使", officer="宫观使", sort_order=112600000,
    )
    evolve(
        writer, entry_id, changed, revival_tp, revival,
        "会灵观使至靖康朝仍由宰辅领。",
    )
    writer.commit()

    entry_id = 568
    writer = W(entry_id)
    rename = sentence(entry_id, "北宋仁宗皇祐五年六月十八日")
    old_temple = find_timepoint(
        writer, "会灵观", "北宋真宗大中祥符七年九月", "机构"
    )
    _, new_temple = typed_state_event(
        writer, entry_id, "集禧观", "机构",
        "北宋仁宗皇祐五年六月十八日",
        "会灵观改名集禧观，供祀五岳帝", rename,
        "建立集禧观改名节点。", category="宫观", sort_order=105306018,
    )
    evolve(writer, entry_id, old_temple, new_temple, rename, "会灵观改名集禧观。")
    start = sentence(entry_id, "神宗即位")
    _, office = state_event(
        writer, entry_id, "集禧观使", "北宋英宗治平四年九月",
        "以观文殿大学士富弼领使，为祠禄官", start,
        "建立集禧观使祠禄官节点。", category="祠禄官",
        officer="宫观使", sort_order=106709000,
    )
    link_institution(
        writer, entry_id, new_temple, office, start, "集禧观设置集禧观使。"
    )
    old_office = find_timepoint(writer, "会灵观使", "北宋仁宗天圣七年七月")
    evolve(
        writer, entry_id, old_office, office, start,
        "会灵观改名集禧观后，治平间置集禧观使。",
    )
    link_group(
        writer, entry_id, "宫观使", "北宋仁宗天圣七年七月",
        office, start, "集禧观使为宫观使实例。",
    )
    link_group(
        writer, entry_id, "祠禄官", "宋代", office, start,
        "集禧观使专条明示其为祠禄官。",
    )
    writer.commit()


def extract_wanshou_commissioner():
    entry_id = 567
    writer = W(entry_id)
    fire = sentence(entry_id, "北宋真宗天圣七年六月二十日")
    _, hall = typed_state_event(
        writer, entry_id, "长生崇寿殿", "机构",
        "北宋仁宗天圣七年六月二十日",
        "玉清昭应宫火灾后独存", fire, "建立长生崇寿殿火灾后存续节点。",
        category="宫观", sort_order=102906020,
    )
    _, temple = typed_state_event(
        writer, entry_id, "万寿观", "机构", "北宋仁宗天圣七年七月八日",
        "长生崇寿殿改名万寿观", fire, "建立万寿观改名节点。",
        category="宫观", sort_order=102907008,
    )
    evolve(
        writer, entry_id, hall, temple, fire,
        "长生崇寿殿在天圣七年七月改名万寿观。",
    )
    start = sentence(entry_id, "南宋绍兴七年八月十四日")
    _, office = state_event(
        writer, entry_id, "万寿观使", "南宋高宗绍兴七年八月十四日",
        "始以前宰相赵鼎领使", start, "建立万寿观使始置节点。",
        category="祠禄官", officer="宫观使", sort_order=113708014,
    )
    link_institution(
        writer, entry_id, temple, office, start, "万寿观设置万寿观使。"
    )
    link_group(
        writer, entry_id, "宫观使", "南宋", office, start,
        "万寿观使为南宋宫观使实例。",
    )
    link_group(
        writer, entry_id, "祠禄官", "南宋", office, start,
        "万寿观使专条明示其为祠禄官。",
    )
    later = Q(entry_id, "此后，宗室、戚里奉祠多得万寿观使")
    append_event(
        writer, office, "此后宗室、戚里奉祠多授此使",
        "补充万寿观使的除授对象。",
    )
    cite(writer, "Timepoints", office, entry_id, later, "补证万寿观使除授对象。")
    writer.commit()


def extract_taiyi_and_youshen_commissioners():
    entry_id = 569
    writer = W(entry_id)
    build = Q(entry_id, "北宋神宗熙宁六年四月十七日建成中太乙宫")
    _, temple = typed_state_event(
        writer, entry_id, "中太乙宫", "机构",
        "北宋神宗熙宁六年四月十七日", "建成",
        build, "建立中太乙宫建成节点。", category="宫观",
        sort_order=107304017,
    )
    start = sentence(entry_id, "熙宁八年四月二十一日")
    _, office = state_event(
        writer, entry_id, "中太乙宫使", "北宋神宗熙宁八年四月二十一日",
        "以宣徽北院使张方平领使，为祠禄官", start,
        "建立中太乙宫使祠禄官节点。", category="祠禄官",
        officer="宫观使", sort_order=107504021,
    )
    link_institution(
        writer, entry_id, temple, office, start, "中太乙宫设置中太乙宫使。"
    )
    link_group(
        writer, entry_id, "宫观使", "北宋神宗熙宁以后",
        office, start, "中太乙宫使为宫观使实例。",
    )
    link_group(
        writer, entry_id, "祠禄官", "宋代", office, start,
        "中太乙宫使专条明示其为祠禄官。",
    )
    writer.commit()

    entry_id = 570
    writer = W(entry_id)
    start = sentence(entry_id, "北宋徽宗大观元年三月十一日")
    _, office = state_event(
        writer, entry_id, "佑神观使", "北宋徽宗大观元年三月十一日",
        "右相赵挺之以观文殿大学士领使致仕", start,
        "建立佑神观使祠禄官节点。", category="祠禄官",
        officer="宫观使", sort_order=110703011,
    )
    link_group(
        writer, entry_id, "宫观使", "北宋神宗熙宁以后",
        office, start, "佑神观使为宫观使实例。",
    )
    link_group(
        writer, entry_id, "祠禄官", "宋代", office, start,
        "佑神观使专条明示其为祠禄官。",
    )
    south = Q(entry_id, "南宋时，除前宰相得醴泉观使、宗戚得万寿观使外，其余则得佑神观使")
    _, south_tp = state_event(
        writer, entry_id, "佑神观使", "南宋",
        "除前宰相、宗戚外，其余奉祠者多授此使", south,
        "记录南宋佑神观使除授范围。", category="祠禄官",
        officer="宫观使", sort_order=112700000,
    )
    evolve(
        writer, entry_id, office, south_tp, south,
        "佑神观使沿用于南宋奉祠。",
    )
    writer.commit()


def extract_shenxiao_commissioner():
    entry_id = 571
    writer = W(entry_id)
    rename = Q(entry_id, "北宋徽宗政和七年五月十六日，改玉清和阳宫为玉清神霄宫")
    _, old = typed_state_event(
        writer, entry_id, "玉清和阳宫", "机构",
        "北宋徽宗政和七年五月十六日前", "原名玉清和阳宫",
        rename, "建立玉清和阳宫改名前节点。", category="宫观",
        sort_order=111705015,
    )
    _, renamed = typed_state_event(
        writer, entry_id, "玉清神霄宫", "机构",
        "北宋徽宗政和七年五月十六日", "玉清和阳宫改名",
        rename, "建立玉清神霄宫改名节点。", category="宫观",
        sort_order=111705016,
    )
    evolve(writer, entry_id, old, renamed, rename, "玉清和阳宫改名玉清神霄宫。")
    start = Q(
        entry_id,
        "政和八年七月二日，以宰臣兼神霄玉清万寿宫使，执政官充副使，侍从为判官",
    )
    _, national_palace = typed_state_event(
        writer, entry_id, "神霄玉清万寿宫", "机构",
        "北宋徽宗政和八年七月二日", "全国诸州府盛建，并设置宫使、副使、判官",
        start, "建立神霄玉清万寿宫设官节点。", category="宫观",
        sort_order=111807002,
    )
    _, office = state_event(
        writer, entry_id, "神霄玉清万寿宫使",
        "北宋徽宗政和八年七月二日", "以宰臣兼领",
        start, "建立神霄玉清万寿宫使节点。", category="宫观使",
        officer="宫观使", sort_order=111807002,
    )
    link_institution(
        writer, entry_id, national_palace, office, start,
        "神霄玉清万寿宫设置宫使。",
    )
    link_group(
        writer, entry_id, "宫观使", "北宋徽宗政和八年七月二日",
        office, start, "神霄玉清万寿宫使为宫观使实例。",
    )
    continuation = Q(entry_id, "钦宗靖康朝沿置")
    _, continued = state_event(
        writer, entry_id, "神霄玉清万寿宫使", "北宋钦宗靖康朝",
        "沿置", continuation, "记录靖康朝沿置本使。", category="宫观使",
        officer="宫观使", sort_order=112600000,
    )
    evolve(
        writer, entry_id, office, continued, continuation,
        "神霄玉清万寿宫使沿置至靖康朝。",
    )
    writer.commit()


def extract_deshou_commissioner():
    entry_id = 572
    writer = W(entry_id)
    build = sentence(entry_id, "南宋绍兴三十二年六月四日")
    _, palace = typed_state_event(
        writer, entry_id, "德寿宫", "机构", "南宋高宗绍兴三十二年六月四日",
        "以秦桧旧第新葺宫室为德寿宫", build, "建立德寿宫始置节点。",
        category="宫殿", sort_order=116206004,
    )
    start = sentence(entry_id, "乾道元年正月十日")
    _, office = state_event(
        writer, entry_id, "德寿宫使", "南宋孝宗乾道元年正月十日",
        "钱端礼兼任，为德寿宫置使之始", start,
        "建立德寿宫使始置节点。", category="宫观使",
        officer="宫观使", sort_order=116501010,
    )
    link_institution(
        writer, entry_id, palace, office, start, "德寿宫设置德寿宫使。"
    )
    link_group(
        writer, entry_id, "宫观使", "南宋", office, start,
        "德寿宫使为南宋宫观使实例。",
    )
    rename = sentence(entry_id, "淳熙十六年二月二日")
    _, renamed = typed_state_event(
        writer, entry_id, "重华宫", "机构", "南宋孝宗淳熙十六年二月二日",
        "德寿宫改名重华宫", rename, "建立重华宫改名节点。",
        category="宫殿", sort_order=118902002,
    )
    evolve(writer, entry_id, palace, renamed, rename, "德寿宫改名重华宫。")
    _, stopped = state_event(
        writer, entry_id, "德寿宫使", "南宋孝宗淳熙十六年二月二日",
        "此后不复设置", rename, "记录德寿宫使停止节点。",
        category="宫观使改革", officer="宫观使", sort_order=118902002,
    )
    evolve(
        writer, entry_id, office, stopped, rename,
        "德寿宫改名重华宫后不复设置德寿宫使。",
    )
    writer.commit()


def extract_palace_subofficers():
    entry_id = 573
    writer = W(entry_id)
    origin = sentence(entry_id, "北宋真宗朝")
    _, early = state_event(
        writer, entry_id, "宫观副使", "北宋真宗朝",
        "在京宫观或置，由丞郎、学士以上充", origin,
        "建立北宋真宗朝宫观副使节点。", category="宫观官",
        officer="宫观副使", sort_order=99700000,
    )
    stop = Q(entry_id, "仁宗天圣七年七月罢宫观副使")
    _, stopped = state_event(
        writer, entry_id, "宫观副使", "北宋仁宗天圣七年七月",
        "罢宫观副使", stop, "记录天圣七年罢宫观副使。",
        category="宫观官改革", officer="宫观副使", sort_order=102907000,
    )
    evolve(writer, entry_id, early, stopped, stop, "宫观副使在天圣七年停止。")
    restore = Q(entry_id, "徽宗政和八年七月二日，以执政为神霄玉清宫副使")
    _, restored = state_event(
        writer, entry_id, "宫观副使", "北宋徽宗政和八年七月二日",
        "以执政官充神霄玉清宫副使", restore,
        "记录政和八年恢复宫观副使。", category="宫观官",
        officer="宫观副使", sort_order=111807002,
    )
    evolve(
        writer, entry_id, stopped, restored, restore,
        "政和八年以执政充神霄玉清宫副使。",
    )
    palace = find_timepoint(
        writer, "神霄玉清万寿宫", "北宋徽宗政和八年七月二日", "机构"
    )
    link_institution(
        writer, entry_id, palace, restored, restore,
        "神霄玉清万寿宫设置宫观副使。",
    )
    south = Q(entry_id, "南宋不置")
    _, ended = state_event(
        writer, entry_id, "宫观副使", "南宋",
        "不置", south, "记录南宋不置宫观副使。", category="宫观官改革",
        officer="宫观副使", sort_order=112700000,
    )
    evolve(writer, entry_id, restored, ended, south, "南宋不置宫观副使。")
    writer.commit()

    entry_id = 574
    writer = W(entry_id)
    origin = Q(entry_id, F[entry_id]["text"])
    _, early = state_event(
        writer, entry_id, "宫观判官", "北宋前期",
        "在京宫观由两省官或五品以上朝官充，位次于副使",
        origin, "建立北宋前期宫观判官节点。", category="宫观官",
        officer="宫观判官", sort_order=96000000,
    )
    stop = Q(entry_id, "天圣七年七月罢")
    _, stopped = state_event(
        writer, entry_id, "宫观判官", "北宋仁宗天圣七年七月",
        "罢宫观判官", stop, "记录天圣七年罢宫观判官。",
        category="宫观官改革", officer="宫观判官", sort_order=102907000,
    )
    evolve(writer, entry_id, early, stopped, stop, "宫观判官在天圣七年停止。")
    restore = Q(entry_id, "徽宗政和八年七月二日，以侍从官充神霄玉清万寿宫判官")
    _, restored = state_event(
        writer, entry_id, "宫观判官", "北宋徽宗政和八年七月二日",
        "以侍从官充神霄玉清万寿宫判官", restore,
        "记录政和八年恢复宫观判官。", category="宫观官",
        officer="宫观判官", sort_order=111807002,
    )
    evolve(
        writer, entry_id, stopped, restored, restore,
        "政和八年以侍从官充神霄玉清万寿宫判官。",
    )
    palace = find_timepoint(
        writer, "神霄玉清万寿宫", "北宋徽宗政和八年七月二日", "机构"
    )
    link_institution(
        writer, entry_id, palace, restored, restore,
        "神霄玉清万寿宫设置宫观判官。",
    )
    south = Q(entry_id, "南宋不置")
    _, ended = state_event(
        writer, entry_id, "宫观判官", "南宋",
        "不置", south, "记录南宋不置宫观判官。", category="宫观官改革",
        officer="宫观判官", sort_order=112700000,
    )
    evolve(writer, entry_id, restored, ended, south, "南宋不置宫观判官。")
    writer.commit()

    entry_id = 575
    writer = W(entry_id)
    origin = Q(entry_id, F[entry_id]["text"])
    _, office = state_event(
        writer, entry_id, "宫观都监", "北宋前期",
        "在京宫观由内侍官或武臣诸司使、副使充，位次于判官",
        origin, "建立北宋前期宫观都监节点。", category="宫观官",
        officer="宫观都监", sort_order=96000000,
    )
    for institution, time in (
        ("玉清昭应宫", "北宋真宗大中祥符四年十一月"),
        ("会灵观", "北宋真宗大中祥符七年九月"),
    ):
        place = find_timepoint(writer, institution, time, "机构")
        link_institution(
            writer, entry_id, place, office, origin,
            f"原文举例{institution}设置宫观都监。",
        )
    stop = Q(entry_id, "仁宗天圣七年七月罢")
    _, stopped = state_event(
        writer, entry_id, "宫观都监", "北宋仁宗天圣七年七月",
        "罢宫观都监", stop, "记录天圣七年罢宫观都监。",
        category="宫观官改革", officer="宫观都监", sort_order=102907000,
    )
    evolve(writer, entry_id, office, stopped, stop, "宫观都监在天圣七年停止。")
    writer.commit()


def extract_superintending_shrines():
    entry_id = 576
    writer = W(entry_id)
    definition = Q(entry_id, "提举内外某宫公事、提举内外某观公事之合称")
    _, early = state_event(
        writer, entry_id, "提举宫观", "北宋真宗朝",
        "已有提举东太一宫、西太一宫公事，掌斋醮，尚非祠禄官",
        sentence(entry_id, "北宋真宗朝"), "建立真宗朝提举宫观节点。",
        category="宫观官", officer="提举宫观总名", sort_order=99700000,
    )
    first = sentence(entry_id, "仁宗康定元年九月")
    _, sinecure = state_event(
        writer, entry_id, "提举宫观", "北宋仁宗康定元年九月",
        "李若谷罢参知政事后提举会灵观，侍从官以上奉祠多授提举宫观",
        first, "建立提举宫观转为祠禄官节点。", category="祠禄官",
        officer="提举宫观总名", sort_order=104009000,
    )
    evolve(
        writer, entry_id, early, sinecure, first,
        "康定元年后提举宫观用于侍从官奉祠。",
    )
    link_group(
        writer, entry_id, "祠禄官", "宋代", sinecure, definition,
        "提举宫观为祠禄官总类实例。",
    )
    military = sentence(entry_id, "神宗熙宁五年十月")
    _, military_tp = state_event(
        writer, entry_id, "提举宫观", "北宋神宗熙宁五年十月",
        "定武臣横行使以上、内侍两省押班以上奉祠为提举，余官为提点",
        military, "记录熙宁五年武臣内侍提举资序。", category="祠禄官资序",
        officer="提举宫观总名", sort_order=107210000,
    )
    evolve(
        writer, entry_id, sinecure, military_tp, military,
        "熙宁五年改定武臣、内侍提举宫观资序。",
    )
    civil = Q(
        entry_id,
        "六年四月，定文臣大卿监、诸路监司及自来管勾宫观公事的知州，奉祠得提举",
    )
    _, civil_tp = state_event(
        writer, entry_id, "提举宫观", "北宋神宗熙宁六年四月",
        "定文臣大卿监、诸路监司及有关知州奉祠得提举",
        civil, "记录熙宁六年文臣提举资序。", category="祠禄官资序",
        officer="提举宫观总名", sort_order=107304000,
    )
    evolve(
        writer, entry_id, military_tp, civil_tp, civil,
        "熙宁六年补定文臣提举宫观资序。",
    )
    writer.commit()


def extract_huiling_and_central_jubilee_superintendents():
    entry_id = 577
    writer = W(entry_id)
    start = sentence(entry_id, "北宋仁宗康定元年九月十二日")
    _, office = state_event(
        writer, entry_id, "提举会灵观公事",
        "北宋仁宗康定元年九月十二日",
        "李若谷罢参知政事后差充，为北宋提举宫观官之始",
        start, "建立提举会灵观公事始置节点。", category="祠禄官",
        officer="提举宫观", sort_order=104009012,
    )
    link_group(
        writer, entry_id, "提举宫观", "北宋仁宗康定元年九月",
        office, start, "提举会灵观公事为提举宫观实例。",
    )
    link_group(
        writer, entry_id, "内祠", "宋代", office,
        Q(entry_id, "属内祠官"), "提举会灵观公事专条明示其属内祠。",
    )
    temple = find_timepoint(writer, "会灵观", "北宋真宗大中祥符七年九月", "机构")
    link_institution(
        writer, entry_id, temple, office, start, "会灵观设置提举会灵观公事。"
    )
    writer.commit()

    entry_id = 578
    writer = W(entry_id)
    start = Q(
        entry_id,
        "（元丰）八年五月十四日，诏资政殿大学士兼侍读吕公著提举中太一宫兼集禧观公事",
    )
    _, office = state_event(
        writer, entry_id, "提举中太一宫兼集禧观公事",
        "北宋神宗元丰八年五月十四日",
        "吕公著以资政殿大学士兼侍读提举", start,
        "建立提举中太一宫兼集禧观公事节点。", category="祠禄官",
        officer="提举宫观", sort_order=108505014,
    )
    link_group(
        writer, entry_id, "提举宫观", "北宋神宗熙宁六年四月",
        office, start, "提举中太一宫兼集禧观公事为提举宫观实例。",
    )
    link_group(
        writer, entry_id, "内祠", "宋代", office,
        Q(entry_id, "属内祠官"),
        "提举中太一宫兼集禧观公事专条明示其属内祠。",
    )
    central = find_timepoint(
        writer, "中太乙宫", "北宋神宗熙宁六年四月十七日", "机构"
    )
    jubilee = find_timepoint(
        writer, "集禧观", "北宋仁宗皇祐五年六月十八日", "机构"
    )
    for place, name in ((central, "中太一宫（中太乙宫）"), (jubilee, "集禧观")):
        link_institution(
            writer, entry_id, place, office, start,
            f"{name}共同设置此兼领提举差遣。",
        )
    writer.commit()


def extract_external_superintendents():
    entry_id = 579
    writer = W(entry_id)
    definition = Q(
        entry_id,
        "提举某京、某府、某州、某军某宫或某观公事合称。属外祠官",
    )
    _, group = state_event(
        writer, entry_id, "提举在外宫观", "北宋神宗熙宁三年",
        "增置在外州府宫观、岳庙差遣，设提举官、管勾官",
        sentence(entry_id, "北宋熙宁三年"),
        "建立熙宁三年提举在外宫观节点。", category="祠禄官",
        officer="外祠提举总名", sort_order=107000000,
    )
    link_group(
        writer, entry_id, "提举宫观", "北宋仁宗康定元年九月",
        group, definition, "提举在外宫观为提举宫观实例。",
    )
    link_group(
        writer, entry_id, "外祠", "北宋神宗熙宁三年以后",
        group, definition, "提举在外宫观专条明示其属外祠。",
    )
    terms = Q(
        entry_id,
        "凡在外州、府提举宫观，均同分司官、致仕官，任便居住，无职事，请祠禄官俸给",
    )
    append_event(
        writer, group, "任便居住，无职事，领取祠禄官俸给",
        "补充提举在外宫观的任职方式。",
    )
    cite(writer, "Timepoints", group, entry_id, terms, "补证在外宫观提举任职方式。")
    writer.commit()

    entry_id = 580
    writer = W(entry_id)
    start = Q(entry_id, "熙宁三年五月增置外宫观岳庙差遣之前，已有，并置提举官")
    _, office = state_event(
        writer, entry_id, "提举西京嵩山崇福宫",
        "北宋神宗熙宁三年五月以前",
        "增置外宫观岳庙差遣前已置提举官", start,
        "建立提举西京嵩山崇福宫早期节点。", category="祠禄官",
        officer="外祠提举", sort_order=106905000,
    )
    _, early_group = state_event(
        writer, entry_id, "提举在外宫观",
        "北宋神宗熙宁三年五月以前",
        "已有西京嵩山崇福宫提举官", start,
        "补足熙宁三年增置前已有的在外宫观提举。", category="祠禄官",
        officer="外祠提举总名", sort_order=106905000,
    )
    relation(
        writer, entry_id, early_group, office, "统称与实例", start,
        "提举西京嵩山崇福宫为提举在外宫观实例。",
    )
    link_group(
        writer, entry_id, "外祠", "宋代", office,
        Q(entry_id, "为外祠官之一"),
        "提举西京嵩山崇福宫专条明示其属外祠。",
    )
    writer.commit()

    entry_id = 581
    writer = W(entry_id)
    start = field_quote(
        entry_id, "简称",
        "（元符三年）九月，诏还故秩，复太中大夫、提举凤翔府上清太平宫，任便居住",
    )
    _, office = state_event(
        writer, entry_id, "提举凤翔府上清太平宫",
        "北宋哲宗元符三年九月",
        "苏辙复太中大夫并提举本宫，任便居住", start,
        "建立提举凤翔府上清太平宫实例节点。", category="祠禄官",
        officer="外祠提举", sort_order=110009000,
    )
    group = find_timepoint(writer, "提举在外宫观", "北宋神宗熙宁三年")
    relation(
        writer, entry_id, group, office, "统称与实例", start,
        "提举凤翔府上清太平宫为提举在外宫观实例。",
    )
    link_group(
        writer, entry_id, "外祠", "北宋神宗熙宁三年以后",
        office, Q(entry_id, "外祠官之一"),
        "提举凤翔府上清太平宫专条明示其属外祠。",
    )
    writer.commit()


def main():
    expected = [
        "景灵宫使", "祥源观使", "醴泉观使", "同醴泉观使", "会灵观使",
        "万寿观使", "集禧观使", "中太乙宫使", "佑神观使",
        "神霄玉清万寿宫使", "德寿宫使", "宫观副使", "宫观判官",
        "宫观都监", "提举宫观", "提举会灵观公事",
        "提举中太一宫兼集禧观公事", "提举在外宫观",
        "提举西京嵩山崇福宫", "提举凤翔府上清太平宫",
    ]
    assert [F[i]["title"] for i in range(562, 582)] == expected
    extract_jingling_palace_commissioner()
    extract_xiangyuan_and_liquan_commissioners()
    extract_joint_liquan_commissioner()
    extract_huiling_and_jixi_commissioners()
    extract_wanshou_commissioner()
    extract_taiyi_and_youshen_commissioners()
    extract_shenxiao_commissioner()
    extract_deshou_commissioner()
    extract_palace_subofficers()
    extract_superintending_shrines()
    extract_huiling_and_central_jubilee_superintendents()
    extract_external_superintendents()


if __name__ == "__main__":
    main()
