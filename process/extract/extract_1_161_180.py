#!/usr/bin/env python3
"""提取第一编第161-180条：尚寝后段与尚功前段宫官。"""

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


IDS = [i for i in range(161, 181) if i != 169]
F = {i: load(i) for i in IDS}


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
    note=None, conflict_flag=0,
):
    target_id = w.relationship(subject, object_, kind, decision, quotation)
    cite(
        w, "Relationships", target_id, i, quotation, decision, name,
        note=note, conflict_flag=conflict_flag,
    )
    return target_id


def find_entity(w, title):
    entity_id = w.find_entity(title, "官职")
    assert entity_id, title
    return entity_id


def find_tp(w, title, time):
    entity_id = find_entity(w, title)
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time)
    return target_id


def cite_fields(w, i, tp_id, conflict_field=None, conflict_note=None):
    for name, quotation in F[i]["fields"].items():
        is_conflict = name == conflict_field
        cite(
            w, "Timepoints", tp_id, i, quotation,
            f"补证{F[i]['title']}的{name}。", name,
            note=conflict_note if is_conflict else None,
            conflict_flag=1 if is_conflict else 0,
        )


OFFICES = {
    161: ("隋炀帝时", "始置掌设", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典设同为司设佐贰", "二十四掌", "二十四掌之一", "正八品"),
    162: ("隋炀帝时", "始置司舆", "宋真宗朝", "宋朝设置，掌舆辇、伞扇并执持羽仪，下辖典舆、掌舆及女史", "二十四司", "二十四司之一", "正七品"),
    163: ("隋炀帝时", "始置典舆", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司舆佐贰", "二十四典", "二十四典之一", "不明"),
    164: ("隋炀帝时", "始置掌舆", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典舆同为司舆佐贰", "二十四掌", "二十四掌之一", "正八品"),
    165: ("隋炀帝时", "始置司苑", "宋真宗朝", "宋朝设置，掌园苑种植及蔬菜瓜果，下辖典苑、掌苑及女史", "二十四司", "二十四司之一", "正七品"),
    166: ("隋炀帝时", "始置典苑", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司苑佐贰", "二十四典", "二十四典之一", "不明"),
    167: ("隋炀帝时", "始置掌苑", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典苑同为司苑佐贰", "二十四掌", "二十四掌之一", "正八品"),
    168: ("隋炀帝时", "始置司灯", "宋仁宗朝", "宋朝见置，掌灯油、火烛，下辖典灯、掌灯及女史", "二十四司", "二十四司之一", "正七品"),
    170: ("隋炀帝时", "始置典灯", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司灯佐贰", "二十四典", "二十四典之一", "不明"),
    171: ("隋炀帝时", "始置掌灯", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典灯同为司灯佐贰", "二十四掌", "二十四掌之一", "正八品"),
    173: ("隋文帝时", "始置司制", "宋真宗朝", "宋朝设置，掌裁缝衣服及编织，下辖典制、掌制及女史", "二十四司", "二十四司之一", "正七品"),
    174: ("隋炀帝时", "始置典制", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司制佐贰", "二十四典", "二十四典之一", "不明"),
    175: ("隋炀帝时", "始置掌制", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典制同为司制佐贰", "二十四掌", "二十四掌之一", "正八品"),
    179: ("隋炀帝时", "始置司彩", "宋真宗朝", "宋朝设置，掌锦缎、绸丝及苎布，下辖典彩、掌彩及女史", "二十四司", "二十四司之一", "正七品"),
    180: ("隋炀帝时", "始置典彩", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司彩佐贰", "二十四典", "二十四典之一", "不明"),
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
    conflict_note = None
    if i == 180:
        conflict_note = "原书典彩条职掌印作‘为司珍官之佐贰’，与本条标题及品阶所列司彩系统不一致，原文照录并标冲突"
    cite_fields(
        w, i, song_tp,
        conflict_field="职掌" if i == 180 else None,
        conflict_note=conflict_note,
    )
    relation(
        w, i, find_tp(w, group, "宋仁宗以后"), song_tp,
        "统称与实例", main,
        f"{group}为统称，正文明确{F[i]['title']}为其一例。",
    )
    w.commit()


def entry172():
    i = 172
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    current = w.entity("尚功", "官职", "正文定义尚功为六尚之一。", quotation=main)
    predecessor = w.entity(
        "尚工", "官职", "职源明示尚功在隋文帝时称尚工。", quotation=origin
    )
    predecessor_tp = timepoint(
        w, i, predecessor, "隋文帝时", "置尚工，为六尚之一", origin,
        "建立尚功改称前的尚工节点。", "职源",
    )
    tang_tp = timepoint(
        w, i, current, "唐代", "尚工改称尚功", origin,
        "建立唐代改称尚功节点。", "职源",
    )
    song_tp = timepoint(
        w, i, current, "宋真宗朝", "沿唐制设尚功，掌女工，管辖司制、司珍、司彩、司计", origin,
        "建立尚功的宋代见置节点。", "职源",
        category="六尚之一", grade="正五品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证尚功为六尚之一。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, predecessor_tp, tang_tp, "前后演变", origin,
        "原文明示隋代尚工至唐代改称尚功。", "职源",
    )
    relation(
        w, i, find_tp(w, "六尚书", "宋仁宗以后"), song_tp,
        "统称与实例", main, "六尚书为统称，尚功为其一例。",
    )
    w.commit()


def treasure_entry(i, predecessor, current, song_time, category, grade):
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    predecessor_entity = find_entity(w, predecessor)
    current_entity = w.entity(
        current, "官职", f"正文定义{current}为宫人女官官名。", quotation=main
    )
    predecessor_tp = timepoint(
        w, i, predecessor_entity, "隋炀帝时",
        f"尚功所属官称{predecessor}", origin,
        f"建立{current}改称前的{predecessor}节点。", "职源", chain="head",
    )
    # 司珍已有崇宁年间同名尚食局节点，先前插宋代节点，再前插唐代节点。
    if current == "司珍":
        song_tp = timepoint(
            w, i, current_entity, song_time, "宋朝沿置，掌金玉珠宝财货", origin,
            "将尚功司珍的宋代节点前插至既有崇宁同名节点之前。", "职源",
            category=category, grade=grade, chain="head",
        )
        tang_tp = timepoint(
            w, i, current_entity, "唐代", f"{predecessor}改称{current}", origin,
            f"建立唐代改称{current}节点。", "职源", chain="head",
        )
    else:
        tang_tp = timepoint(
            w, i, current_entity, "唐代", f"{predecessor}改称{current}", origin,
            f"建立唐代改称{current}节点。", "职源",
        )
        song_event = {
            "典珍": "宋朝始见置，为司珍佐贰",
            "掌珍": "宋朝见置，与典珍同为司珍佐贰",
        }[current]
        song_tp = timepoint(
            w, i, current_entity, song_time, song_event,
            origin, f"建立{current}的宋代见置节点。", "职源",
            category=category, grade=grade,
        )
    cite(w, "Timepoints", song_tp, i, main, f"补证{current}属于{category}。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, predecessor_tp, tang_tp, "前后演变", origin,
        f"原文明示{predecessor}在唐代改称{current}。", "职源",
    )
    group = {"二十四司之一": "二十四司", "二十四典之一": "二十四典", "二十四掌之一": "二十四掌"}[category]
    relation(
        w, i, find_tp(w, group, "宋仁宗以后"), song_tp,
        "统称与实例", main, f"{group}为统称，正文明确{current}为其一例。",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in IDS] == [
        "掌设", "司舆", "典舆", "掌舆", "司苑", "典苑", "掌苑", "司灯", "典灯", "掌灯",
        "尚功", "司制", "典制", "掌制", "司珍", "典珍", "掌珍", "司彩", "典彩",
    ]
    for i in (161, 162, 163, 164, 165, 166, 167, 168, 170, 171):
        office_entry(i)
    entry172()
    for i in (173, 174, 175):
        office_entry(i)
    treasure_entry(176, "司宝", "司珍", "宋真宗朝", "二十四司之一", "正七品")
    treasure_entry(177, "典宝", "典珍", "宋仁宗天圣年间", "二十四典之一", "不明")
    treasure_entry(178, "掌宝", "掌珍", "宋仁宗天圣年间", "二十四掌之一", "正八品")
    office_entry(179)
    office_entry(180)


if __name__ == "__main__":
    main()
