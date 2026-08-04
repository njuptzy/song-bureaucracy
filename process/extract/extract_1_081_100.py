#!/usr/bin/env python3
"""提取第一编第81-100条：诸嫔后段、宸妃及内省宫官。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)
TIANSHENG_TIME = "宋仁宗朝（《天圣内命妇品职令》）"


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter1 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(81, 101)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field_name=None):
    source = F[i]["fields"][field_name] if field_name else F[i]["text"]
    assert needle in source, (i, field_name, needle)
    return needle


def field(i, field_name):
    return Q(i, F[i]["fields"][field_name], field_name)


def C(i, field_name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(w, table, target_id, i, quotation, decision, field_name=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field_name), quotation, decision, **kwargs
    )


def add_timepoint(
    w,
    i,
    entity_id,
    time,
    event,
    quotation,
    decision,
    field_name=None,
    category=None,
    grade=None,
    chain="tail",
):
    timepoint_id = w.timepoint(
        entity_id,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        attr_grade=grade,
        chain=chain,
    )
    cite(w, "Timepoints", timepoint_id, i, quotation, decision, field_name)
    return timepoint_id


def add_relation(
    w,
    i,
    subject_tp,
    object_tp,
    relation_type,
    quotation,
    decision,
    field_name=None,
):
    relation_id = w.relationship(
        subject_tp, object_tp, relation_type, decision, quotation
    )
    cite(
        w,
        "Relationships",
        relation_id,
        i,
        quotation,
        decision,
        field_name,
    )
    return relation_id


def find_entity(w, title, type_="官职"):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    return entity_id


def find_tp(w, title, time, type_="官职"):
    entity_id = find_entity(w, title, type_)
    timepoint_id = w.find_timepoint(entity_id, time)
    assert timepoint_id, (title, time)
    return timepoint_id


LATE_CONSORTS = {
    81: (
        "南朝宋孝武帝孝建三年（456）",
        "始置昭容",
        "宋初沿唐内职之制设昭容",
        "正二品",
    ),
    82: ("隋朝", "始置昭媛", "宋初沿置昭媛", "正二品"),
    83: ("三国魏明帝时", "始置修仪", "宋初沿置修仪", "正二品"),
    84: ("三国魏文帝时", "始置修容", "宋初沿置修容", "正二品"),
    85: ("北齐", "始置修媛", "宋初沿置修媛", "正二品"),
    86: ("隋炀帝时", "始置充仪", "宋初沿置充仪", "正二品"),
    87: ("隋朝", "始置充容", "宋初沿置充容", "正二品"),
    88: ("隋朝", "始置充媛", "宋初沿置充媛", "正二品"),
}


def late_consort(i):
    title = F[i]["title"]
    origin_time, origin_event, song_event, grade = LATE_CONSORTS[i]
    origin = field(i, "职源")
    rank = field(i, "品阶")
    w = W(i)
    entity_id = find_entity(w, title)
    song_tp = add_timepoint(
        w,
        i,
        entity_id,
        "宋初",
        song_event,
        origin,
        f"建立{title}的宋初沿置节点。",
        "职源",
        category="嫔阶",
        grade=grade,
        chain="head",
    )
    cite(
        w,
        "Timepoints",
        song_tp,
        i,
        rank,
        f"补证{title}属内命妇嫔阶、{grade}及其位次。",
        "品阶",
    )
    add_timepoint(
        w,
        i,
        entity_id,
        origin_time,
        origin_event,
        origin,
        f"建立{title}的{origin_time}职源节点。",
        "职源",
        chain="head",
    )
    w.commit()


def entry89():
    i = 89
    main = F[i]["text"]
    w = W(i)
    imperial_consort_tp = find_tp(w, "皇妃", "宋代")
    cite(
        w,
        "Timepoints",
        imperial_consort_tp,
        i,
        main,
        "补证四妃在宋代宫中俗称‘娘子’。",
        note="娘子是四妃与部分诸嫔的俗称，不另建实体",
    )
    inner_women_tp = find_tp(w, "内命妇", TIANSHENG_TIME)
    cite(
        w,
        "Timepoints",
        inner_women_tp,
        i,
        main,
        "补证内命妇中自淑仪至充媛诸嫔俗称‘娘子’。",
        note="娘子仅是四妃与淑仪至充媛诸嫔的俗称，不另建实体",
    )
    w.commit()


def simple_rank_entry(i, origin_time, origin_event, grade, category):
    title = F[i]["title"]
    origin = field(i, "职源")
    rank = field(i, "品阶")
    w = W(i)
    entity_id = find_entity(w, title)
    group_tp = w.timepoint(
        entity_id,
        TIANSHENG_TIME,
        f"《天圣内命妇品职令》列为{category}",
        f"复用{title}的天圣品职令节点，补充品阶。",
        rank,
        attr_category=category,
        attr_grade=grade,
    )
    cite(
        w,
        "Timepoints",
        group_tp,
        i,
        rank,
        f"补证{title}在内命妇中的{category}、{grade}及位次。",
        "品阶",
    )
    add_timepoint(
        w,
        i,
        entity_id,
        origin_time,
        origin_event,
        origin,
        f"建立{title}的{origin_time}职源节点。",
        "职源",
        chain="head",
    )
    w.commit()


def entry90():
    simple_rank_entry(90, "西汉武帝时", "始置婕妤", "正三品", "婕妤阶")


def entry91():
    simple_rank_entry(
        91,
        "战国秦惠文王时（前337年—前311年）",
        "始置美人",
        "正四品",
        "美人阶",
    )


def entry92():
    simple_rank_entry(92, "晋武帝时", "始置才人", "正五品", "才人阶")


def entry93():
    i = 93
    title = F[i]["title"]
    origin = field(i, "职源")
    rank = field(i, "品阶")
    w = W(i)
    entity_id = find_entity(w, title)
    group_tp = w.timepoint(
        entity_id,
        TIANSHENG_TIME,
        "《天圣内命妇品职令》列为贵人阶",
        "复用贵人的天圣品职令节点，补充无视品品阶。",
        rank,
        attr_category="贵人阶",
        attr_grade="无视品",
    )
    cite(w, "Timepoints", group_tp, i, rank, "补证贵人属内命妇末阶、无视品。", "品阶")
    add_timepoint(
        w,
        i,
        entity_id,
        "宋真宗大中祥符二年（1009）",
        "宋朝特置贵人",
        origin,
        "建立贵人的宋代特置节点。",
        "职源",
        chain="head",
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "东汉光武帝建武元年（25）",
        "始置贵人",
        origin,
        "建立贵人的东汉职源节点。",
        "职源",
        chain="head",
    )
    w.commit()


def entry94():
    i = 94
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    w = W(i)
    entity_id = w.entity(
        "宸妃",
        "官职",
        "原书正文明言宸妃为内命妇特置封号。",
        quotation=main,
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "唐高宗时",
        "已有宸妃名号",
        history,
        "建立宸妃在唐高宗时的职源节点。",
        "职源与沿革",
    )
    chenfei_tp = add_timepoint(
        w,
        i,
        entity_id,
        "宋仁宗明道元年（1032）二月",
        "特置宸妃，用以追赠仁宗生母、真宗顺容李氏",
        history,
        "原文明言明道元年二月特置宸妃，建立宋代节点。",
        "职源与沿革",
        category="内命妇特置封号",
    )
    cite(w, "Timepoints", chenfei_tp, i, main, "补证宸妃的内命妇特置封号性质。")
    add_relation(
        w,
        i,
        find_tp(w, "内命妇", TIANSHENG_TIME),
        chenfei_tp,
        "统称与实例",
        main,
        "内命妇为总称，宸妃为仁宗朝特置的内命妇封号实例。",
    )
    w.commit()


def lower_rank_entry(i, origin_time, has_song_gap):
    title = F[i]["title"]
    origin = field(i, "职源")
    rank = field(i, "品阶")
    w = W(i)
    entity_id = find_entity(w, title)
    huizong_tp = w.timepoint(
        entity_id,
        "宋徽宗朝",
        f"徽宗朝见置{title}为内命妇位号",
        f"复用{title}的徽宗朝节点，补充品阶。",
        rank,
        attr_category="内命妇位号",
        attr_grade="无视品",
    )
    cite(w, "Timepoints", huizong_tp, i, origin, f"补证{title}在徽宗朝见置。", "职源")
    cite(w, "Timepoints", huizong_tp, i, rank, f"补证{title}无视品及其位次。", "品阶")
    if has_song_gap:
        add_timepoint(
            w,
            i,
            entity_id,
            "宋初",
            f"{title}或不置",
            origin,
            f"建立{title}在宋初或不置的制度状态。",
            "职源",
            chain="head",
        )
    add_timepoint(
        w,
        i,
        entity_id,
        origin_time,
        f"始置{title}",
        origin,
        f"建立{title}的{origin_time}职源节点。",
        "职源",
        chain="head",
    )
    w.commit()


def entry95():
    lower_rank_entry(95, "隋炀帝时", True)


def entry96():
    lower_rank_entry(96, "隋炀帝时", True)


def entry97():
    lower_rank_entry(97, "隋炀帝时", False)


def entry98():
    i = 98
    main = F[i]["text"]
    alias = field(i, "别称")
    system_quote = Q(
        i,
        "宋仁宗以后，复遵隋唐旧制，形成了以尚书内省六尚二十四司、"
        "二十四典、二十四掌为中心的宫官体制。",
    )
    grade_quote = Q(
        i,
        "《宋会要·后妃》4之2：“宫人女官品：六尚书正五品，二十四司、"
        "司正、彤史正七品，二十四掌正八品。”",
    )
    w = W(i)
    entity_id = find_entity(w, "宫官")
    song_early = add_timepoint(
        w,
        i,
        entity_id,
        "宋初",
        "宫官名称较杂乱",
        main,
        "建立宫官在宋初的制度状态。",
        category="宫人女官总称",
        chain="head",
    )
    system_tp = add_timepoint(
        w,
        i,
        entity_id,
        "宋仁宗以后",
        "复遵隋唐旧制，形成以六尚、二十四司、二十四典、二十四掌为中心的宫官体制",
        system_quote,
        "建立仁宗以后宫官体制成型节点。",
        category="宫人女官总称",
    )
    cite(w, "Timepoints", song_early, i, alias, "补证宫官别称女官、宫人女官，不另建实体。", "别称")
    cite(w, "Timepoints", system_tp, i, grade_quote, "补证宫官各类别的品阶。")

    groups = (
        ("六尚书", "尚书内省六尚女官总称", "正五品"),
        ("二十四司", "尚书内省二十四司女官总称", "正七品"),
        ("二十四典", "尚书内省二十四典女官总称", None),
        ("二十四掌", "尚书内省二十四掌女官总称", "正八品"),
    )
    for title, event, grade in groups:
        group_entity = w.entity(
            title,
            "官职",
            f"正文明列{title}为仁宗以后宫官体制的组成类别。",
            quotation=system_quote,
        )
        group_tp = w.timepoint(
            group_entity,
            "宋仁宗以后",
            event,
            f"建立{title}在仁宗以后宫官体制中的类别节点。",
            system_quote,
            attr_category="宫官类别",
            attr_grade=grade,
        )
        cite(w, "Timepoints", group_tp, i, system_quote, f"补证{title}是宫官体制的组成类别。")
        if grade:
            cite(w, "Timepoints", group_tp, i, grade_quote, f"补证{title}品阶为{grade}。")
        add_relation(
            w,
            i,
            system_tp,
            group_tp,
            "统称与实例",
            system_quote,
            f"宫官为总称，{title}为仁宗以后宫官体制的明列组成类别。",
        )
    w.commit()


def entry99():
    i = 99
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "内省",
        "机构",
        "正文定义为管理后宫宫人事务的机构。",
        quotation=main,
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "宋太祖朝",
        "已置内省，管理后宫宫人事务",
        main,
        "原文明言太祖朝已置内省，建立机构节点。",
        category="后宫宫人管理机构",
    )
    w.commit()


def entry100():
    i = 100
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "知内省事",
        "官职",
        "正文定义为总掌内省事务的差遣官名。",
        quotation=main,
    )
    office_tp = add_timepoint(
        w,
        i,
        entity_id,
        "宋太宗朝",
        "置知内省事，总掌内省事务，由尚宫及太监等女官担任",
        main,
        "原文明言太宗置知内省事，建立差遣节点。",
        category="差遣官",
    )
    inner_province = find_entity(w, "内省", "机构")
    province_tp = add_timepoint(
        w,
        i,
        inner_province,
        "宋太宗朝",
        "内省设知内省事总掌事务",
        main,
        "建立内省在太宗朝设主管官的机构状态。",
        category="后宫宫人管理机构",
    )
    add_relation(
        w,
        i,
        province_tp,
        office_tp,
        "编制隶属",
        main,
        "知内省事总掌内省事务，建内省至知内省事的机构—官职隶属。",
    )
    add_relation(
        w,
        i,
        find_tp(w, "宫官", "宋初"),
        office_tp,
        "统称与实例",
        main,
        "宫官为宫人女官总称，由女官担任的知内省事为其差遣实例。",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(81, 101)] == [
        "昭容", "昭媛", "修仪", "修容", "修媛", "充仪", "充容", "充媛", "娘子", "婕妤",
        "美人", "才人", "贵人", "宸妃", "宝林", "御女", "采女", "宫官", "内省", "知内省事",
    ]
    for i in range(81, 89):
        late_consort(i)
    entry89()
    entry90()
    entry91()
    entry92()
    entry93()
    entry94()
    entry95()
    entry96()
    entry97()
    entry98()
    entry99()
    entry100()


if __name__ == "__main__":
    main()
