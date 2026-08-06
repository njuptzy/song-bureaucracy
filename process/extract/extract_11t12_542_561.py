#!/usr/bin/env python3
"""提取 chapter11t12 第542-561条：检校官末九阶、功臣、宪衔、试秩与祠禄官。"""

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
    "extract_11t12_522_541_helpers", HERE / "extract_11t12_522_541.py"
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


F = {entry_id: load(entry_id) for entry_id in (528, *range(542, 562))}


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
state = base.state
relation = base.relation
append_event = base.append_event


def nested_attr(module, name):
    current = module
    while current is not None:
        if hasattr(current, name):
            return getattr(current, name)
        current = getattr(current, "base", None)
    raise AttributeError(name)


typed_state = nested_attr(base, "typed_state")


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


def state_event(
    writer, entry_id, title, time, event, quote, decision, *,
    category=None, officer="职官", grade=None, sort_order=None,
):
    entity, timepoint = state(
        writer, entry_id, title, time, event, quote, decision,
        category=category, officer=officer, grade=grade, sort_order=sort_order,
    )
    append_event(
        writer, timepoint, event, decision,
        category=category, officer=officer, grade=grade,
    )
    return entity, timepoint


def typed_state_event(
    writer, entry_id, title, entity_type, time, event, quote, decision, *,
    category=None, officer=None, grade=None, sort_order=None,
):
    entity, timepoint = typed_state(
        writer, entry_id, title, entity_type, time, event, quote, decision,
        category=category, officer=officer, grade=grade, sort_order=sort_order,
    )
    append_event(
        writer, timepoint, event, decision,
        category=category, officer=officer, grade=grade,
    )
    return entity, timepoint


def find_timepoint(writer, title, time, entity_type="官职"):
    entity = writer.find_entity(title, entity_type)
    assert entity is not None, (title, entity_type)
    timepoint = writer.find_timepoint(entity, time)
    assert timepoint is not None, (title, time)
    return timepoint


INSPECTION_RANKS = {
    542: ("检校户部尚书", "第十一阶"),
    543: ("检校刑部尚书", "第十二阶"),
    544: ("检校礼部尚书", "第十三阶"),
    545: ("检校工部尚书", "第十四阶"),
    546: ("检校左散骑常侍", "第十五阶"),
    547: ("检校右散骑常侍", "第十六阶"),
    548: ("检校太子宾客", "第十七职（原书用字）"),
    549: ("检校国子祭酒", "第十八阶"),
    550: ("检校水部员外郎", "第十九阶，即最末一阶"),
}


def abolish_inspection_rank(writer, entry_id, title, quote):
    old = find_timepoint(writer, title, "北宋前期")
    _, end = state_event(
        writer, entry_id, title, "北宋神宗元丰三年九月十七日",
        "停止此检校官阶", quote, f"建立{title}停止节点。",
        category="检校官阶改革", officer="检校虚衔",
        sort_order=108009017,
    )
    relation(
        writer, entry_id, old, end, "前后演变", quote,
        f"原文明示{title}在元丰三年九月十七日停止。",
    )


def extract_inspection_ranks():
    for entry_id, (title, rank) in INSPECTION_RANKS.items():
        writer = W(entry_id)
        quote = Q(entry_id, F[entry_id]["text"])
        _, member = state_event(
            writer, entry_id, title, "北宋前期",
            f"检校官十九阶之{rank}", quote,
            f"建立或复用{title}北宋前期检校官阶节点。",
            category="检校官十九阶", officer="检校虚衔",
            sort_order=96000000,
        )
        group = find_timepoint(writer, "检校官", "北宋前期")
        relation(
            writer, entry_id, group, member, "统称与实例", quote,
            f"原文明示{title}属于北宋前期检校官十九阶。",
        )

        if entry_id != 545:
            end_quote = Q(entry_id, "元丰三年九月十七日罢")
            abolish_inspection_rank(writer, entry_id, title, end_quote)

        uses = {
            545: "宗室特除诸司使或换授诸司使以上官，加检校工部尚书",
            547: "宗室除诸司副使加检校右散骑常侍",
            548: "除阁门通事舍人、内殿崇班以上，初授及加恩带检校太子宾客",
            549: "武臣副率以上、三班使臣及吏职、蕃官军员加恩带检校国子祭酒",
        }
        if entry_id in uses:
            use_quote = Q(entry_id, uses[entry_id])
            append_event(writer, member, uses[entry_id], f"补充{title}的加授对象。")
            cite(
                writer, "Timepoints", member, entry_id, use_quote,
                f"补证{title}的加授对象。",
            )
        writer.commit()

    # 检校工部尚书专条未复述裁撤日期，但明示参“检校官”条；总条明确
    # 元丰三年仅留前六阶、余十三阶皆罢，故以总条证据补足第十四阶终点。
    entry_id = 528
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "神宗元丰三年九月十七日，除检校太师、太傅、太保与检校太尉、司徒、司空六阶保留外，余十三阶检校官皆罢",
    )
    abolish_inspection_rank(writer, entry_id, "检校工部尚书", quote)
    writer.commit()


def extract_secretariat_marshal_title():
    entry_id = 551
    writer = W(entry_id)
    quote = Q(entry_id, "文臣任枢密使带检校太尉，故有此称谓")
    marshal = find_timepoint(writer, "检校太尉", "北宋前期")
    append_event(
        writer, marshal, "文臣任枢密使时所带，故称枢密太尉",
        "以称谓条补充检校太尉的加授语境。",
    )
    cite(
        writer, "Timepoints", marshal, entry_id, quote,
        "补证文臣枢密使带检校太尉及枢密太尉称谓来源。",
    )
    commissioner = find_timepoint(writer, "枢密使", "北宋初")
    append_event(
        writer, commissioner, "文臣任枢密使皆带检校太尉，称枢密太尉",
        "以称谓条补充北宋旧制。",
    )
    cite(
        writer, "Timepoints", commissioner, entry_id,
        Q(entry_id, "盖旧制，文臣为枢密使皆带检校太尉"),
        "补证北宋文臣枢密使皆带检校太尉。",
    )
    writer.commit()


def extract_meritorious_titles():
    entry_id = 552
    writer = W(entry_id)
    origin = sentence(entry_id, "唐开元中始有")
    _, tang = state_event(
        writer, entry_id, "功臣", "唐开元中至唐末",
        "始有功臣号，唐中后期渐用于有功将相", origin,
        "建立功臣号的唐代职源。", category="功臣号",
        officer="职官范畴", sort_order=71300000,
    )
    north_quote = Q(entry_id, "北宋沿置")
    _, north = state_event(
        writer, entry_id, "功臣", "北宋",
        "沿置功臣号", north_quote, "建立北宋功臣号节点。",
        category="功臣号", officer="职官范畴", sort_order=96000000,
    )
    grant_quote = Q(
        entry_id,
        "功臣号分赐二府大臣、皇子、皇亲、文武臣僚、外臣及诸班直将士等",
    )
    append_event(
        writer, north,
        "分赐二府大臣、皇子、皇亲、文武臣僚、外臣及诸班直将士",
        "补充北宋功臣号授予范围。",
    )
    cite(writer, "Timepoints", north, entry_id, grant_quote, "补证功臣号授予范围。")

    stop_quote = Q(entry_id, "神宗元丰元年十一月罢功臣号")
    _, stopped = state_event(
        writer, entry_id, "功臣", "北宋神宗元丰元年十一月",
        "罢功臣号", stop_quote, "记录元丰元年罢功臣号。",
        category="功臣号改革", officer="职官范畴", sort_order=107811000,
    )
    relation(
        writer, entry_id, north, stopped, "前后演变", stop_quote,
        "北宋功臣号在元丰元年十一月停止。",
    )
    restore_quote = sentence(entry_id, "南宋绍兴六年四月十二日")
    _, restored = state_event(
        writer, entry_id, "功臣", "南宋高宗绍兴六年四月十二日",
        "复赐功臣号，专授决胜强敌、收复境土之文武臣僚",
        restore_quote, "记录绍兴六年恢复功臣号。",
        category="功臣号改革", officer="职官范畴", sort_order=113604012,
    )
    relation(
        writer, entry_id, stopped, restored, "前后演变", restore_quote,
        "南宋绍兴六年恢复此前停止的功臣号。",
    )
    writer.commit()


CONSTITUTIONAL_TITLES = (
    "御史大夫", "御史中丞", "侍御史", "殿中侍御史", "监察御史",
)


def extract_constitutional_titles():
    entry_id = 553
    writer = W(entry_id)
    definition = Q(
        entry_id,
        "宪的本义，指御史台官：御史大夫、御史中丞、侍御史、殿中侍御史、监察御史",
    )
    origin = sentence(entry_id, "宪官而成为带衔，始于唐玄宗开元时")
    state_event(
        writer, entry_id, "宪衔", "唐玄宗开元时",
        "外任官始带御史台官为宪衔", origin,
        "建立宪衔的唐代职源。", category="宪衔",
        officer="职官范畴", sort_order=71300000,
    )
    north_quote = sentence(entry_id, "传至宋初")
    _, group = state_event(
        writer, entry_id, "宪衔", "宋初",
        "军制以御史官为品秩，武臣内职、军职及刺史以上带检校官、兼宪官",
        north_quote, "建立宋初宪衔制度节点。", category="宪衔",
        officer="职官总名", sort_order=96000000,
    )
    for title in CONSTITUTIONAL_TITLES:
        _, member = state_event(
            writer, entry_id, title, "宋初", "作为所带宪衔",
            definition, f"建立或复用{title}作为宋初宪衔的节点。",
            category="宪衔", officer="宪衔所带官", sort_order=96000000,
        )
        relation(
            writer, entry_id, group, member, "统称与实例", definition,
            f"原文明列{title}为宪衔所用御史台官。",
        )
    stop_quote = Q(
        entry_id,
        "元丰三年九月十七日，罢加恩授宪衔、检校官及银青光禄大夫，止许加勋转武骑尉",
    )
    _, stopped = state_event(
        writer, entry_id, "宪衔", "北宋神宗元丰三年九月十七日",
        "罢加恩授宪衔", stop_quote, "记录元丰三年罢授宪衔。",
        category="宪衔改革", officer="职官总名", sort_order=108009017,
    )
    relation(
        writer, entry_id, group, stopped, "前后演变", stop_quote,
        "宋初沿用的宪衔在元丰三年停止加授。",
    )
    writer.commit()


def extract_silver_wine_inspection_merit():
    entry_id = 554
    writer = W(entry_id)
    definition = Q(
        entry_id,
        "银酒监武为银青光禄大夫、检校国子祭酒、监察御史、武骑尉的连称",
    )
    _, group = state_event(
        writer, entry_id, "银酒监武", "北宋前期",
        "银青光禄大夫、检校国子祭酒、监察御史、武骑尉四官名连称",
        definition, "建立银酒监武官名连称节点。", category="官名连称",
        officer="职官总名", sort_order=96000000,
    )
    member_times = {
        "银青光禄大夫": "北宋前期",
        "检校国子祭酒": "北宋前期",
        "监察御史": "北宋前期",
        "武骑尉": "北宋",
    }
    for title, time in member_times.items():
        member = find_timepoint(writer, title, time)
        relation(
            writer, entry_id, group, member, "统称与实例", definition,
            f"原文明示{title}为银酒监武连称的组成实例。",
        )
    grant = sentence(entry_id, "北宋前期")
    append_event(
        writer, group,
        "禁军班直及军职、三班使臣、吏职未受加恩者遇大礼授此四衔",
        "补充银酒监武的加授对象与场合。",
    )
    cite(writer, "Timepoints", group, entry_id, grant, "补证银酒监武的加授对象。")
    writer.commit()


TRIAL_RANKS = {
    "助教": "助教",
    "诸寺监主簿": "寺监主簿",
    "正字": "正字",
    "校书郎": "校书郎",
    "大理评事": "大理评事",
    "大理司直": "大理司直",
    "斋郎": "斋郎",
}


def extract_trial_rank():
    entry_id = 555
    writer = W(entry_id)
    origin = sentence(entry_id, "宋代试秩源于唐代试官之一种")
    state_event(
        writer, entry_id, "试秩", "唐代",
        "源于唐代试官：或经试转真拜，或仅试假官衔",
        origin, "建立试秩的唐代职源。", category="试秩",
        officer="职官范畴", sort_order=61800000,
    )
    definition = Q(entry_id, "宋代试秩，亦称试衔，无职事，但有表示资格、阶秩之义")
    _, group = state_event(
        writer, entry_id, "试秩", "宋代",
        "亦称试衔，无职事，用以表示资格、阶秩",
        definition, "建立宋代试秩制度节点。", category="试秩",
        officer="职官总名", sort_order=96000000,
    )
    ranks = sentence(entry_id, "授予试秩者，有二种类型")
    append_event(
        writer, group,
        "授幕职州县官初授及无官人解褐所带的助教、寺监主簿、正字、校书郎、大理评事、大理司直、斋郎等",
        "补充试秩授予对象和所带官衔。",
    )
    cite(writer, "Timepoints", group, entry_id, ranks, "补证试秩授予对象和官衔范围。")
    for title, source_title in TRIAL_RANKS.items():
        _, member = state_event(
            writer, entry_id, title, "宋代", "作为试秩所带官衔",
            ranks, f"建立或复用{title}作为试秩官衔的节点。",
            category="试秩", officer="试秩所带官", sort_order=96000000,
        )
        relation(
            writer, entry_id, group, member, "统称与实例", ranks,
            f"原文所列“{source_title}”属于宋代试秩所带官衔。",
        )
    selection = sentence(entry_id, "太平兴国二年三月一日起")
    _, selectable = state_event(
        writer, entry_id, "试秩", "北宋太宗太平兴国二年三月一日",
        "试衔官经七选后许赴选集", selection,
        "记录太平兴国二年试衔官取得选集资格。", category="试秩改革",
        officer="职官总名", sort_order=97703001,
    )
    relation(
        writer, entry_id, group, selectable, "前后演变", selection,
        "太平兴国二年起试衔官经七选可赴选集。",
    )
    writer.commit()

    entry_id = 556
    writer = W(entry_id)
    alias = Q(entry_id, "即“试秩”")
    group = find_timepoint(writer, "试秩", "宋代")
    cite(writer, "Timepoints", group, entry_id, alias, "补证试衔即试秩，不另建别名实体。")
    selection = Q(entry_id, "诏应授试衔等人，特定七选赴集。试衔有选，自擢等始也")
    selectable = find_timepoint(writer, "试秩", "北宋太宗太平兴国二年三月一日")
    cite(writer, "Timepoints", selectable, entry_id, selection, "补证试衔七选赴集制度。")
    writer.commit()


def extract_shrine_sinecures():
    entry_id = 557
    writer = W(entry_id)
    definition = Q(
        entry_id,
        "祠禄官为内祠（在京宫观）、外祠（在外诸州府宫观岳庙）差遣之总名",
    )
    _, group = state_event(
        writer, entry_id, "祠禄官", "宋代",
        "内祠、外祠差遣总名", definition, "建立祠禄官总名节点。",
        category="祠禄官", officer="职官总名", sort_order=96000000,
    )
    for title, event in (("内祠", "在京宫观官总类"), ("外祠", "在外宫观岳庙差遣总类")):
        _, member = state_event(
            writer, entry_id, title, "宋代", event, definition,
            f"建立{title}祠禄官分类节点。", category="祠禄官",
            officer="祠禄差遣总名", sort_order=96000000,
        )
        relation(
            writer, entry_id, group, member, "统称与实例", definition,
            f"原文明示{title}为祠禄官分类实例。",
        )
    origin = sentence(entry_id, "在京宫观官始置于唐")
    state_event(
        writer, entry_id, "祠禄官", "唐玄宗天宝间",
        "在京宫观官始置，已有太清宫使、九成宫使等",
        origin, "建立祠禄官的唐代职源。", category="祠禄官",
        officer="职官总名", sort_order=74200000,
    )
    dissent = field_quote(
        entry_id, "职能",
        "神宗熙宁二年十二月之后，祠禄官或用以安排持不同政见者，即与当轴者不合的官员，此类属贬黜官",
    )
    state_event(
        writer, entry_id, "祠禄官", "北宋神宗熙宁二年十二月以后",
        "或用于安排持不同政见者，作为略含优礼的贬黜官",
        dissent, "记录熙宁以后祠禄官的政治安置功能。", category="祠禄官职能",
        officer="职官总名", sort_order=106912000,
    )
    reform = field_quote(
        entry_id, "品位",
        "徽宗政和三年八月，改定：中散大夫（从五品）以上及监司资序人并充提举；朝奉郎（正七品）以上或曾任职事官监察御史以上、或曾带贴职，充提点；余官差充管勾官",
    )
    state_event(
        writer, entry_id, "祠禄官", "北宋徽宗政和三年八月",
        "改定提举、提点、管勾官的资序门槛", reform,
        "记录政和三年祠禄官差充资序改革。", category="祠禄官品位",
        officer="职官总名", sort_order=111308000,
    )
    quota = field_quote(
        entry_id, "编制",
        "总计一千八百人，此为堂除祠禄官。加上部阙祠禄官，两者合计在九千人",
    )
    state_event(
        writer, entry_id, "祠禄官", "南宋",
        "堂除额一千八百人；连同部阙合计约九千人", quota,
        "记录南宋祠禄官员额。", category="祠禄官编制",
        officer="职官总名", sort_order=112700000,
    )
    writer.commit()


def extract_inner_outer_shrines():
    entry_id = 558
    writer = W(entry_id)
    early = sentence(entry_id, "在外州府宫观、岳庙，宋初有")
    _, early_tp = state_event(
        writer, entry_id, "外祠", "宋初",
        "已有西京崇福宫等在外宫观、岳庙差遣", early,
        "建立外祠宋初节点。", category="祠禄官",
        officer="祠禄差遣总名", sort_order=96000000,
    )
    later = Q(entry_id, "熙宁三年后增置杭州洞霄宫")
    _, later_tp = state_event(
        writer, entry_id, "外祠", "北宋神宗熙宁三年以后",
        "增置杭州洞霄宫等在外宫观及五岳庙差遣", later,
        "记录熙宁三年后外祠扩充。", category="祠禄官",
        officer="祠禄差遣总名", sort_order=107000000,
    )
    relation(
        writer, entry_id, early_tp, later_tp, "前后演变", later,
        "外祠在熙宁三年后增置多处宫观岳庙差遣。",
    )
    staffing = Q(
        entry_id,
        "皆设提举或提点、管勾（南宋改主管）及监岳庙等，为外祠官",
    )
    append_event(
        writer, later_tp, "设提举、提点、管勾（南宋称主管）及监岳庙等",
        "补充外祠官差遣类型。",
    )
    cite(writer, "Timepoints", later_tp, entry_id, staffing, "补证外祠官差遣类型。")
    writer.commit()

    entry_id = 559
    writer = W(entry_id)
    definition = sentence(entry_id, "在京宫观官总名")
    _, inner = state_event(
        writer, entry_id, "内祠", "宋代",
        "在京宫观官总名，包括玉清昭应宫、景灵宫、会灵观等",
        definition, "补充内祠的定义与宫观范围。", category="祠禄官",
        officer="祠禄差遣总名", sort_order=96000000,
    )
    group = find_timepoint(writer, "祠禄官", "宋代")
    relation(
        writer, entry_id, group, inner, "统称与实例", definition,
        "内祠专条补证其为祠禄官分类。",
    )
    writer.commit()


def extract_palace_temple_offices():
    # 总条所载昭应宫修建、改名和设官过程，同时建立机构与宫使的编制隶属。
    entry_id = 557
    writer = W(entry_id)
    build = Q(
        entry_id,
        "北宋真宗大中祥符元年四月十六日修昭应宫（二年七月十八日改名玉清昭应宫）",
    )
    _, old_palace = typed_state_event(
        writer, entry_id, "昭应宫", "机构", "北宋真宗大中祥符元年四月十六日",
        "修建昭应宫", build, "建立昭应宫修建节点。", category="宫观",
        sort_order=100804016,
    )
    _, renamed_palace = typed_state_event(
        writer, entry_id, "玉清昭应宫", "机构", "北宋真宗大中祥符二年七月十八日",
        "昭应宫改名玉清昭应宫", build, "建立玉清昭应宫改名节点。", category="宫观",
        sort_order=100907018,
    )
    relation(
        writer, entry_id, old_palace, renamed_palace, "前后演变", build,
        "昭应宫在大中祥符二年改名玉清昭应宫。",
    )
    first = Q(
        entry_id,
        "祥符四年十一月，以首相兼玉清昭应宫使，此为宋代置宫观使之始",
    )
    _, palace_active = typed_state_event(
        writer, entry_id, "玉清昭应宫", "机构", "北宋真宗大中祥符四年十一月",
        "设置玉清昭应宫使", first, "建立玉清昭应宫设使节点。", category="宫观",
        sort_order=101111000,
    )
    _, office = state_event(
        writer, entry_id, "玉清昭应宫使", "北宋真宗大中祥符四年十一月",
        "始置，以首相兼领", first, "建立玉清昭应宫使始置节点。",
        category="宫观使", officer="祠禄官", sort_order=101111000,
    )
    relation(
        writer, entry_id, palace_active, office, "编制隶属", first,
        "玉清昭应宫设置玉清昭应宫使。",
    )
    completed = Q(entry_id, "祥符七年十月二十七日，玉清昭应宫建成")
    typed_state_event(
        writer, entry_id, "玉清昭应宫", "机构",
        "北宋真宗大中祥符七年十月二十七日", "建成",
        completed, "记录玉清昭应宫建成。", category="宫观",
        sort_order=101410027,
    )
    writer.commit()

    entry_id = 560
    writer = W(entry_id)
    definition = Q(entry_id, "宫观使为某宫使、某观使合称")
    first = sentence(entry_id, "北宋真宗大中祥符四年十一月")
    _, group = state_event(
        writer, entry_id, "宫观使", "北宋真宗大中祥符四年十一月",
        "以首相领玉清昭应宫使，为宋代宫观使之始",
        first, "建立宋代宫观使始置节点。", category="宫观使",
        officer="祠禄官总名", sort_order=101111000,
    )
    office = find_timepoint(writer, "玉清昭应宫使", "北宋真宗大中祥符四年十一月")
    relation(
        writer, entry_id, group, office, "统称与实例", definition,
        "玉清昭应宫使为宫观使实例。",
    )
    shrine = find_timepoint(writer, "祠禄官", "宋代")
    relation(
        writer, entry_id, shrine, group, "统称与实例",
        Q(entry_id, "祠禄官名"), "宫观使专条明示其为祠禄官实例。",
    )
    abolition = sentence(entry_id, "仁宗天圣七年七月")
    _, changed = state_event(
        writer, entry_id, "宫观使", "北宋仁宗天圣七年七月",
        "罢宰执官兼宫观使，其后限使相、节度使等领使",
        abolition, "记录天圣七年宫观使领使规则变化。", category="宫观使",
        officer="祠禄官总名", sort_order=102907000,
    )
    relation(
        writer, entry_id, group, changed, "前后演变", abolition,
        "天圣七年罢宰执兼宫观使并调整领使范围。",
    )
    outside = Q(entry_id, "熙宁后，始有领宫观使居外州、府者")
    _, outside_tp = state_event(
        writer, entry_id, "宫观使", "北宋神宗熙宁以后",
        "始有领宫观使而居外州府者", outside,
        "记录熙宁以后宫观使居外制度。", category="宫观使",
        officer="祠禄官总名", sort_order=106800000,
    )
    relation(
        writer, entry_id, changed, outside_tp, "前后演变", outside,
        "熙宁以后出现领宫观使居外州府的制度。",
    )
    zhenghe = Q(entry_id, "徽宗政和八年七月二日，以宰相兼神霄玉清万寿宫使")
    state_event(
        writer, entry_id, "宫观使", "北宋徽宗政和八年七月二日",
        "宰相兼神霄玉清万寿宫使", zhenghe,
        "记录政和八年宰相兼宫观使。", category="宫观使",
        officer="祠禄官总名", sort_order=111807002,
    )
    south = sentence(entry_id, "南宋时")
    state_event(
        writer, entry_id, "宫观使", "南宋",
        "前执政任经筵官皆带宫观使；他官须使相以上，居外者须三少以上",
        south, "记录南宋宫观使除授规则。", category="宫观使",
        officer="祠禄官总名", sort_order=112700000,
    )
    writer.commit()

    entry_id = 561
    writer = W(entry_id)
    start = sentence(entry_id, "北宋大中祥符四年十一月")
    _, office = state_event(
        writer, entry_id, "玉清昭应宫使", "北宋真宗大中祥符四年十一月",
        "始设，以首相兼领", start, "专条补证玉清昭应宫使始置。",
        category="宫观使", officer="祠禄官", sort_order=101111000,
    )
    group = find_timepoint(writer, "宫观使", "北宋真宗大中祥符四年十一月")
    relation(
        writer, entry_id, group, office, "统称与实例", start,
        "玉清昭应宫使专条补证其为宫观使实例。",
    )
    stop = Q(entry_id, "仁宗天圣七年七月罢使名")
    _, stopped = state_event(
        writer, entry_id, "玉清昭应宫使", "北宋仁宗天圣七年七月",
        "罢使名", stop, "记录玉清昭应宫使罢名。", category="宫观使改革",
        officer="祠禄官", sort_order=102907000,
    )
    relation(
        writer, entry_id, office, stopped, "前后演变", stop,
        "玉清昭应宫使在天圣七年七月罢名。",
    )
    writer.commit()


def main():
    expected = [
        "检校户部尚书", "检校刑部尚书", "检校礼部尚书", "检校工部尚书",
        "检校左散骑常侍", "检校右散骑常侍", "检校太子宾客",
        "检校国子祭酒", "检校水部员外郎", "枢密太尉", "功臣", "宪衔",
        "银酒监武", "试秩（试衔）", "试衔", "祠禄官", "外祠", "内祠",
        "宫观使", "玉清昭应宫使",
    ]
    assert [F[i]["title"] for i in range(542, 562)] == expected
    extract_inspection_ranks()
    extract_secretariat_marshal_title()
    extract_meritorious_titles()
    extract_constitutional_titles()
    extract_silver_wine_inspection_merit()
    extract_trial_rank()
    extract_shrine_sinecures()
    extract_inner_outer_shrines()
    extract_palace_temple_offices()


if __name__ == "__main__":
    main()
