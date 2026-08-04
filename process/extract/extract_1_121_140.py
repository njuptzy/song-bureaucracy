#!/usr/bin/env python3
"""提取第一编第121-140条：尚仪后段与尚服所属宫官。"""

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


F = {i: load(i) for i in range(121, 141)}


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


def relation(w, i, subject, object_, kind, quotation, decision, name=None):
    target_id = w.relationship(subject, object_, kind, decision, quotation)
    cite(w, "Relationships", target_id, i, quotation, decision, name)
    return target_id


def find_tp(w, title, time, type_="官职"):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time)
    return target_id


def cite_fields(w, i, tp_id, names=None):
    selected = names or F[i]["fields"].keys()
    for name in selected:
        quotation = field(i, name)
        cite(
            w, "Timepoints", tp_id, i, quotation,
            f"补证{F[i]['title']}的{name}。", name,
        )


OFFICES = {
    121: ("隋炀帝时", "始置掌籍", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典籍同为司籍佐贰", "二十四掌", "二十四掌之一", "正八品"),
    122: ("隋文帝时", "始置司乐", "宋真宗朝", "宋朝设置，掌音律，下设典乐、掌乐及女史", "二十四司", "二十四司之一", "正七品"),
    124: ("隋炀帝时", "始置掌乐", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典乐同为司乐佐贰", "二十四掌", "二十四掌之一", "正八品"),
    125: ("隋炀帝时", "始置司宾", "宋太祖朝", "宋朝始置，掌女宾客参见及朝会引导，下辖典宾、掌宾及女史", "二十四司", "二十四司之一", "正七品"),
    126: ("隋炀帝时", "始置典宾", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司宾佐贰", "二十四典", "二十四典之一", "不明"),
    127: ("隋炀帝时", "始置掌宾", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典宾同为司宾佐贰", "二十四掌", "二十四掌之一", "正八品"),
    128: ("隋炀帝时", "始置司赞，掌礼仪赞相导引", "宋真宗朝", "宋朝设置，掌礼仪、班序、设版位、赞拜，下辖典赞、掌赞、女史及彤史", "二十四司", "二十四司之一", "正七品"),
    130: ("隋文帝时", "始置典赞", "宋真宗朝", "宋朝始见置，为司赞佐贰", "二十四典", "二十四典之一", "不明"),
    131: ("隋炀帝时", "始置掌赞", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典赞同为司赞佐贰", "二十四掌", "二十四掌之一", "正八品"),
    132: ("隋文帝时", "已置尚服，掌服章、宝藏", "宋真宗朝", "宋朝始见置，总掌珍宝、符契、图籍、服饰及仗卫兵器，管辖司宝、司衣、司饰、司仗", "六尚书", "六尚之一", "正五品"),
    135: ("隋炀帝时", "始置掌宝", "宋太宗朝", "宋朝已置，由司簿兼任，为司宝佐贰", "二十四掌", "二十四掌之一", "正八品"),
    137: ("隋炀帝时", "始置典衣", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司衣佐贰", "二十四典", "二十四典之一", "不明"),
    138: ("隋炀帝时", "始置掌衣", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典衣同为司衣佐贰", "二十四掌", "二十四掌之一", "正八品"),
    140: ("隋炀帝时", "始置典饰", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司饰佐贰", "二十四典", "二十四典之一", "不明"),
}


def office_entry(i):
    origin_time, origin_event, song_time, song_event, group, category, grade = OFFICES[i]
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职",
        f"正文定义{F[i]['title']}为宫人女官官名。", quotation=main,
    )
    origin_tp = timepoint(
        w, i, entity_id, origin_time, origin_event, origin,
        f"建立{F[i]['title']}的前代职源节点。", "职源", chain="head",
    )
    song_tp = timepoint(
        w, i, entity_id, song_time, song_event, origin,
        f"建立{F[i]['title']}的宋代见置节点。", "职源",
        category=category, grade=grade,
    )
    # 典乐已有大晟府同名官的北宋后期节点；宫官节点必须前插而非接到链尾。
    if i == 123:
        assert origin_tp and song_tp
    cite(w, "Timepoints", song_tp, i, main, f"补证{F[i]['title']}属于{category}。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, group, "宋仁宗以后"), song_tp, "统称与实例", main,
        f"{group}为统称，正文明确{F[i]['title']}为其一例。",
    )
    w.commit()


def entry123():
    """典乐与既有大晟府典乐同名，复用实体并把早期宫官节点前插。"""
    i = 123
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.find_entity("典乐", "官职")
    assert entity_id
    song_tp = timepoint(
        w, i, entity_id, "宋仁宗天圣年间",
        "《内命妇品职令》中始见，为司乐佐贰", origin,
        "复用同名典乐实体，将宫官见置节点前插至大晟府典乐节点之前。", "职源",
        category="二十四典之一", grade="不明", chain="head",
    )
    timepoint(
        w, i, entity_id, "隋炀帝时", "始置典乐", origin,
        "建立典乐的隋代宫官职源节点。", "职源", chain="head",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证典乐为二十四典之一。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "二十四典", "宋仁宗以后"), song_tp,
        "统称与实例", main, "二十四典为统称，典乐为其一例。",
    )
    w.commit()


def entry129():
    i = 129
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(
        "彤史", "官职", "修复后的正文定义彤史为尚仪所属司赞内的宫人女官。", quotation=main
    )
    timepoint(
        w, i, entity_id, "唐代", "尚仪局司赞设彤史，为正六品", origin,
        "建立彤史的唐代职源节点。", "职源", grade="正六品",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋仁宗天圣年间",
        "《内命妇品职令》中始见，手书所领职事的文书记录", origin,
        "建立彤史的宋代见置节点。", "职源",
        category="宫人女官", grade="正七品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证彤史为尚仪所属司赞内的宫人女官。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "宫官", "宋仁宗以后"), song_tp,
        "统称与实例", main, "宫官为宫人女官总称，彤史为其具体官名。",
    )
    w.commit()


def renamed_entry(
    i, predecessor, predecessor_time, predecessor_event,
    current_origin_time, current_origin_event, song_time, song_event,
    group, category, grade, relation_to_song=False,
):
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    current_entity = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为宫人女官官名。", quotation=main
    )
    predecessor_entity = w.entity(
        predecessor, "官职", f"职源明示{predecessor}是{F[i]['title']}改称前的正式官名。", quotation=origin
    )
    predecessor_tp = timepoint(
        w, i, predecessor_entity, predecessor_time, predecessor_event, origin,
        f"建立改称前官名{predecessor}的时间点。", "职源",
    )
    current_origin_tp = timepoint(
        w, i, current_entity, current_origin_time, current_origin_event, origin,
        f"建立{F[i]['title']}改称形成节点。", "职源", chain="head",
    )
    song_tp = timepoint(
        w, i, current_entity, song_time, song_event, origin,
        f"建立{F[i]['title']}的宋代见置节点。", "职源",
        category=category, grade=grade,
    )
    cite(w, "Timepoints", song_tp, i, main, f"补证{F[i]['title']}属于{category}。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, predecessor_tp, song_tp if relation_to_song else current_origin_tp,
        "前后演变", origin,
        f"原文明示{predecessor}改称{F[i]['title']}。", "职源",
    )
    relation(
        w, i, find_tp(w, group, "宋仁宗以后"), song_tp, "统称与实例", main,
        f"{group}为统称，正文明确{F[i]['title']}为其一例。",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(121, 141)] == [
        "掌籍", "司乐", "典乐", "掌乐", "司宾", "典宾", "掌宾", "司赞", "彤史", "典赞",
        "掌赞", "尚服", "司宝", "典宝", "掌宝", "司衣", "典衣", "掌衣", "司饰", "典饰",
    ]
    for i in (121, 122):
        office_entry(i)
    entry123()
    for i in range(124, 129):
        office_entry(i)
    entry129()
    office_entry(130)
    office_entry(131)
    office_entry(132)
    renamed_entry(
        133, "司玺", "隋炀帝时", "置司玺，掌玺印",
        "唐代", "司玺改称司宝", "宋太宗朝", "宋朝设置，掌宝印、符节、图籍、珍宝",
        "二十四司", "二十四司之一", "正七品",
    )
    renamed_entry(
        134, "典玺", "隋炀帝时", "置典玺",
        "唐代", "典玺改称典宝", "宋真宗朝", "宋朝始见置，为司宝佐贰",
        "二十四典", "二十四典之一", "不明",
    )
    office_entry(135)
    renamed_entry(
        136, "衣服", "宋初", "尚服所属官称衣服",
        "隋炀帝时", "始置司衣，掌衣服", "宋太宗朝", "衣服改称司衣，掌皇后衣服、首饰",
        "二十四司", "二十四司之一", "正七品", relation_to_song=True,
    )
    office_entry(137)
    office_entry(138)
    renamed_entry(
        139, "梳篦", "宋初", "尚服所属官称梳篦",
        "隋炀帝时", "始置司饰，掌梳洗、服玩", "宋太宗朝", "梳篦改称司饰，掌膏沐、巾栉、服玩",
        "二十四司", "二十四司之一", "正七品", relation_to_song=True,
    )
    office_entry(140)


if __name__ == "__main__":
    main()
