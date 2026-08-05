#!/usr/bin/env python3
"""提取第一编第181-200条：尚功末段、宫正与政和尚书内省六司。"""

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


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter1 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(181, 201)}


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
    source = F[i]["fields"][name] if name else F[i]["text"]
    assert quotation in source, (i, name, quotation)
    return w.citation(
        table, target_id, C(i, name), quotation, decision, **kwargs
    )


def timepoint(
    w, i, entity_id, time, event, quotation, decision, name=None,
    category=None, grade=None, chain="tail",
):
    target_id = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_grade=grade, chain=chain,
    )
    cite(w, "Timepoints", target_id, i, quotation, decision, name)
    return target_id


def relation(
    w, i, subject, object_, kind, quotation, decision, name=None,
    staff_quota=None, staff_type=None,
):
    target_id = w.relationship(
        subject, object_, kind, decision, quotation,
        staff_quota=staff_quota, staff_type=staff_type,
    )
    cite(w, "Relationships", target_id, i, quotation, decision, name)
    return target_id


def find_entity(w, title, type_="官职"):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    return entity_id


def find_tp(w, title, time, type_="官职"):
    entity_id = find_entity(w, title, type_)
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time)
    return target_id


def cite_fields(w, i, tp_id):
    for name, quotation in F[i]["fields"].items():
        cite(
            w, "Timepoints", tp_id, i, quotation,
            f"补证{F[i]['title']}的{name}。", name,
        )


PALACE_OFFICES = {
    181: ("隋炀帝时", "始置掌彩", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典彩同为司彩佐贰", "二十四掌", "二十四掌之一", "正八品"),
    183: ("隋炀帝时", "始置典计", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司计佐贰", "二十四典", "二十四典之一", "不明"),
    184: ("隋炀帝时", "始置掌计", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典计同为司计佐贰", "二十四掌", "二十四掌之一", "正八品"),
}


def palace_office(i):
    origin_time, origin_event, song_time, song_event, group, category, grade = PALACE_OFFICES[i]
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为宫人女官官名。", quotation=main
    )
    timepoint(
        w, i, entity_id, origin_time, origin_event, origin,
        f"建立{F[i]['title']}的前代职源节点。", "职源", chain="head",
    )
    song_tp = timepoint(
        w, i, entity_id, song_time, song_event, origin,
        f"建立{F[i]['title']}的宋代见置节点。", "职源",
        category=category, grade=grade,
    )
    cite(w, "Timepoints", song_tp, i, main, f"补证{F[i]['title']}属于{category}。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, group, "宋仁宗以后"), song_tp,
        "统称与实例", main, f"{group}为统称，{F[i]['title']}为其一例。",
    )
    w.commit()


def entry182():
    """司计复用既有武学同名实体，并把宫官节点前插。"""
    i = 182
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = find_entity(w, "司计")
    song_tp = timepoint(
        w, i, entity_id, "宋太宗朝",
        "宋朝设置，掌计划及准备衣服、饮食、柴炭、什物，下辖典计、掌计及女史",
        origin, "将尚功司计节点前插至既有崇宁武学司计节点之前。", "职源",
        category="二十四司之一", grade="正七品", chain="head",
    )
    timepoint(
        w, i, entity_id, "唐代", "始置司计", origin,
        "建立司计的唐代宫官职源节点。", "职源", chain="head",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证司计为二十四司之一。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "二十四司", "宋仁宗以后"), song_tp,
        "统称与实例", main, "二十四司为统称，司计为其一例。",
    )
    w.commit()


def entry185():
    i = 185
    main = F[i]["text"]
    history = field(i, "职源")
    w = W(i)
    entity_id = w.entity("女史", "官职", "正文定义女史为宫人职员。", quotation=main)
    timepoint(w, i, entity_id, "《周礼》所载制度", "女史掌王后礼职及文书", history, "建立女史先秦职源节点。", "职源")
    timepoint(w, i, entity_id, "隋炀帝时", "六司二十四司内各置女史，无定员", history, "建立隋代女史节点。", "职源")
    timepoint(w, i, entity_id, "唐代", "内官六局二十四司沿置女史，各有定员，掌宫中文书", history, "建立唐代女史节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋仁宗天圣年间",
        "《内命妇品职令》中始见，掌后宫女官各局司文书，六尚书二十四司共定编九十八人",
        history, "建立宋代女史节点。", "职源",
        category="宫人职员", grade="流外，无品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证女史为宫人职员。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "宫官", "宋仁宗以后"), song_tp,
        "统称与实例", main, "宫官为宫人女官职员总称，女史为其具体职员。",
    )
    w.commit()


def entry186():
    i = 186
    main = F[i]["text"]
    history = field(i, "职源")
    w = W(i)
    entity_id = w.entity("宫正", "官职", "正文定义宫正为宫人女官。", quotation=main)
    timepoint(w, i, entity_id, "《周礼》所载制度", "始见宫正，掌王宫戒令与纠察", history, "建立宫正先秦职源节点。", "职源")
    timepoint(w, i, entity_id, "唐代", "复置宫正为内官", history, "建立唐代复置节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋真宗朝", "宋朝始置，总掌宫内格、式及违法处罚",
        history, "建立宋代宫正节点。", "职源", category="宫人女官", grade="不明",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证宫正为宫人女官。")
    cite_fields(w, i, song_tp)
    relation(w, i, find_tp(w, "宫官", "宋初"), song_tp, "统称与实例", main, "宫官为总称，宫正为其具体女官。")
    w.commit()


def entry187():
    i = 187
    main = F[i]["text"]
    history = field(i, "职源")
    w = W(i)
    entity_id = w.entity("司正", "官职", "正文定义司正为宫人女官。", quotation=main)
    timepoint(w, i, entity_id, "隋炀帝时", "始置司正，属尚官，掌格式、推鞠及处罚宫人", history, "建立司正隋代职源节点。", "职源")
    timepoint(w, i, entity_id, "唐代", "独立于六尚二十四司之外", history, "建立唐代制度位置节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋真宗朝", "宋朝始置，独立于六尚二十四司之外",
        history, "建立宋代司正节点。", "职源", category="宫人女官",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证司正为宫人女官。")
    relation(w, i, find_tp(w, "宫官", "宋初"), song_tp, "统称与实例", main, "宫官为总称，司正为独立于六尚外的具体女官。")
    w.commit()


REFORM_TIME = "宋徽宗政和三年（1113）五月"


def entry188():
    i = 188
    main = F[i]["text"]
    history = field(i, "职源")
    w = W(i)
    entity_id = w.entity("内宰", "官职", "正文定义内宰为女官。", quotation=main)
    timepoint(w, i, entity_id, "《周礼》所载制度", "始见内宰", history, "建立内宰先秦职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, REFORM_TIME, "始设内宰，总领尚书内省六司",
        history, "建立政和改制内宰节点。", "职源",
        category="尚书内省主管女官", grade="不明",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证内宰为女官。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "尚书内省", REFORM_TIME, "机构"), song_tp,
        "编制隶属", field(i, "职掌"), "内宰总领尚书内省六司，隶属尚书内省。", "职掌",
        staff_quota="二人", staff_type="主管女官",
    )
    w.commit()


def entry189():
    i = 189
    main = F[i]["text"]
    history = field(i, "职源")
    w = W(i)
    entity_id = w.entity("副宰", "官职", "正文定义副宰为女官。", quotation=main)
    song_tp = timepoint(
        w, i, entity_id, REFORM_TIME, "与内宰同时设置，辅佐内宰总领六司",
        history, "据‘与内宰设置时间同’建立政和三年五月节点。", "职源",
        category="尚书内省主管女官", grade="不明",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证副宰为女官。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "尚书内省", REFORM_TIME, "机构"), song_tp,
        "编制隶属", field(i, "职掌"), "副宰辅佐内宰总领尚书内省六司，隶属尚书内省。", "职掌",
        staff_quota="四人", staff_type="主管女官",
    )
    w.commit()


def entry190():
    i = 190
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "尚书内省六司", "机构", "正文定义其为司治、司教、司仪、司政、司宪、司缮总名。", quotation=main
    )
    group_tp = timepoint(
        w, i, entity_id, REFORM_TIME,
        "尚书内省分六司：司治、司教、司仪、司政、司宪、司缮，分别对应外朝六部",
        main, "建立政和三年五月尚书内省六司机构统称节点。",
        category="尚书内省所属六司机构统称",
    )
    relation(
        w, i, find_tp(w, "尚书内省", REFORM_TIME, "机构"), group_tp,
        "上下级机构", main, "尚书内省为上级，六司为其下分机构总称。",
    )
    w.commit()


SIX_OFFICES = {
    191: ("司治", "掌受尚书省吏部奏事，视吏部职事", "尚书内省六司之首"),
    192: ("司教", "掌受尚书省户部奏事，视户部职事", "尚书内省六司第二"),
    193: ("司仪", "掌受尚书省礼部奏事，视礼部职事", "尚书内省六司第三"),
    194: ("司政", "掌受尚书省兵部奏事，视兵部职事", "尚书内省六司第四"),
    195: ("司宪", "掌受尚书省刑部奏事，视刑部职事", "尚书内省六司第五"),
    196: ("司缮", "掌受尚书省工部奏事，视工部职事", "尚书内省六司之末"),
}


def six_office(i):
    title, event, category = SIX_OFFICES[i]
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(title, "机构", "正文定义其为尚书内省六司之一。", quotation=main)
    office_tp = timepoint(
        w, i, entity_id, REFORM_TIME, f"始置，{event}", origin,
        f"建立{title}政和三年五月始置节点。", "职源", category=category,
    )
    cite(w, "Timepoints", office_tp, i, main, f"补证{title}为尚书内省六司之一。")
    cite_fields(w, i, office_tp)
    group_tp = find_tp(w, "尚书内省六司", REFORM_TIME, "机构")
    relation(w, i, group_tp, office_tp, "统称与实例", main, f"尚书内省六司为统称，{title}为具体一司。")
    relation(
        w, i, find_tp(w, "尚书内省", REFORM_TIME, "机构"), office_tp,
        "上下级机构", main, f"{title}是尚书内省下属六司之一。",
    )
    w.commit()


def entry197():
    i = 197
    main = F[i]["text"]
    history = field(i, "职源")
    w = W(i)
    entity_id = w.entity("内史", "官职", "正文定义内史为隶尚书内省的内庭官。", quotation=main)
    timepoint(w, i, entity_id, "西周昭王时", "已有内史官名", history, "建立内史西周职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, REFORM_TIME, "始设为尚书内省六司司长，各领一司",
        history, "建立政和改制内史节点。", "职源",
        category="尚书内省六司长官", grade="不明",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证内史隶尚书内省。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "尚书内省六司", REFORM_TIME, "机构"), song_tp,
        "编制隶属", field(i, "职掌"), "内史为六司逐司司长，隶属尚书内省六司。", "职掌",
        staff_quota="每司一员，共六员", staff_type="司长",
    )
    w.commit()


def entry198():
    i = 198
    main = F[i]["text"]
    history = field(i, "职源")
    w = W(i)
    entity_id = w.entity("治中", "官职", "正文定义治中为隶尚书内省的内庭官。", quotation=main)
    timepoint(w, i, entity_id, "东汉", "有治中从事，为州刺史助理", history, "建立治中东汉职源节点。", "职源")
    tang_tp = timepoint(w, i, entity_id, "唐武德年间", "始正式称治中", history, "建立治中正式官名节点。", "职源")
    sima = w.entity("司马", "官职", "原文明言治中因避唐高宗李治讳改称司马。", quotation=history)
    sima_tp = timepoint(w, i, sima, "唐高宗时", "治中避李治讳改称司马", history, "建立唐高宗时司马改称节点。", "职源")
    relation(w, i, tang_tp, sima_tp, "前后演变", history, "治中因避唐高宗李治讳改称司马。", "职源")
    song_tp = timepoint(
        w, i, entity_id, REFORM_TIME, "尚书内省复设治中女官，为内史佐贰，每司一人",
        history, "建立政和改制治中女官节点。", "职源",
        category="尚书内省六司佐官", grade="不明",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证治中隶尚书内省。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "尚书内省六司", REFORM_TIME, "机构"), song_tp,
        "编制隶属", field(i, "编制"), "治中为六司逐司一人的内史佐官。", "编制",
        staff_quota="每司一人，共六人", staff_type="内史佐贰",
    )
    w.commit()


def entry199():
    i = 199
    main = F[i]["text"]
    alias = field(i, "别称")
    w = W(i)
    entity_id = w.entity("宫人", "官职", "正文定义宫人为入后宫备选御侍或嫔嫡的宫女通称。", quotation=main)
    song_tp = timepoint(
        w, i, entity_id, "宋代",
        "宫女通称；狭义指未有品位者，广义亦包括有位号者，太后宫与太皇太后宫亦有宫人",
        main, "建立宋代宫人身份节点。", category="宫女通称",
    )
    cite(
        w, "Timepoints", song_tp, i, alias, "补证宫人别称内人；别称不另建实体。", "别称",
        note="内人为宫人别称，不另建实体",
    )
    w.commit()


def entry200():
    i = 200
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("侍儿", "官职", "正文定义侍儿为宫人的一种。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代",
        "无品，服侍太后殿，可遴选为皇后宫人并有机会接幸皇帝",
        main, "建立宋代侍儿身份节点。", category="宫人之一种", grade="无品",
    )
    relation(
        w, i, find_tp(w, "宫人", "宋代"), tp_id,
        "统称与实例", main, "宫人为统称，侍儿为其一种。",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(181, 201)] == [
        "掌彩", "司计", "典计", "掌计", "女史", "宫正", "司正", "内宰", "副宰", "尚书内省六司",
        "司治", "司教", "司仪", "司政", "司宪", "司缮", "内史", "治中", "宫人", "侍儿",
    ]
    palace_office(181)
    entry182()
    palace_office(183)
    palace_office(184)
    entry185()
    entry186()
    entry187()
    entry188()
    entry189()
    entry190()
    for i in range(191, 197):
        six_office(i)
    entry197()
    entry198()
    entry199()
    entry200()


if __name__ == "__main__":
    main()
