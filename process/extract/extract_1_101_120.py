#!/usr/bin/env python3
"""提取第一编第101-120条：尚书内省及尚宫、尚仪所属宫官。"""

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
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(101, 121)}


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
):
    relation_id = w.relationship(
        subject_tp, object_tp, relation_type, decision, quotation
    )
    cite(w, "Relationships", relation_id, i, quotation, decision)
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


def cite_fields(w, i, tp_id, names):
    for name in names:
        quotation = field(i, name)
        cite(
            w,
            "Timepoints",
            tp_id,
            i,
            quotation,
            f"补证{F[i]['title']}的{name}。",
            name,
        )


def entry101():
    i = 101
    history = field(i, "沿革")
    alias = field(i, "别称")
    w = W(i)
    entity_id = w.entity(
        "尚书内省",
        "机构",
        "沿革字段明言内省在太宗朝改名为尚书内省。",
        quotation=history,
    )
    taizong_tp = add_timepoint(
        w,
        i,
        entity_id,
        "宋太宗朝",
        "内省改名为尚书内省",
        history,
        "建立尚书内省由内省改名而来的太宗朝节点。",
        "沿革",
        category="后宫宫人管理机构",
    )
    reform_tp = add_timepoint(
        w,
        i,
        entity_id,
        "宋徽宗政和三年（1113）五月",
        "改定职事并确立尚书内省，其下分六司，收受外朝尚书省六部奏事",
        history,
        "建立政和三年五月改定尚书内省职事的关键制度节点。",
        "沿革",
        category="后宫宫人管理机构",
    )
    cite(
        w,
        "Timepoints",
        reform_tp,
        i,
        alias,
        "补证尚书内省又称内尚书省、大内内侍省；别称不另建实体。",
        "别称",
        note="内尚书省、大内内侍省均为尚书内省别称，不另建实体",
    )
    add_relation(
        w,
        i,
        find_tp(w, "内省", "宋太宗朝", "机构"),
        taizong_tp,
        "前后演变",
        history,
        "原文明言太宗朝内省改名为尚书内省，建立改名前后的机构演变。",
    )
    w.commit()


def entry102():
    i = 102
    main = F[i]["text"]
    alias = field(i, "简称")
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", "正文定义为总掌尚书内省事务的后宫差遣官。", quotation=main
    )
    office_tp = add_timepoint(
        w,
        i,
        entity_id,
        "宋太宗朝",
        "始置，总掌尚书内省事务，由宫人女官担任",
        main,
        "正文明确太宗朝始置及其职掌、任职者，建立差遣节点。",
        category="后宫差遣官",
    )
    cite(
        w,
        "Timepoints",
        office_tp,
        i,
        alias,
        "补证知尚书内省公事的两种简称；简称不另建实体。",
        "简称",
        note="知尚书内省事、知尚书内省均为简称，不另建实体",
    )
    add_relation(
        w,
        i,
        find_tp(w, "尚书内省", "宋太宗朝", "机构"),
        office_tp,
        "编制隶属",
        main,
        "该官总掌尚书内省事务，建立机构至主管官的编制隶属。",
    )
    add_relation(
        w,
        i,
        find_tp(w, "宫官", "宋初"),
        office_tp,
        "统称与实例",
        main,
        "宫官为宫人女官总称，由宫人女官担任的该差遣为其实例。",
    )
    w.commit()


def entry103():
    i = 103
    main = F[i]["text"]
    alias = field(i, "别称")
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", "正文定义为尚书内省的后宫差遣官。", quotation=main
    )
    office_tp = add_timepoint(
        w,
        i,
        entity_id,
        "宋哲宗元祐八年（1093）",
        "见管干尚书内省公事，位次于知尚书内省公事",
        alias,
        "别称字段的元祐八年诏令提供明确见置时间。",
        "别称",
        category="后宫差遣官",
    )
    cite(w, "Timepoints", office_tp, i, main, "补证该差遣位次于知尚书内省公事。")
    cite(
        w,
        "Timepoints",
        office_tp,
        i,
        alias,
        "补证管干尚书内省公事为别称；不另建实体。",
        "别称",
        note="管干尚书内省公事为别称，不另建实体",
    )
    add_relation(
        w,
        i,
        find_tp(w, "尚书内省", "宋太宗朝", "机构"),
        office_tp,
        "编制隶属",
        main,
        "官名直接指明这是尚书内省差遣，建立机构至官职的编制隶属。",
    )
    w.commit()


def entry104():
    i = 104
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(F[i]["title"], "官职", "正文定义为宫人女官。", quotation=main)
    tp_id = add_timepoint(
        w,
        i,
        entity_id,
        "宋真宗大中祥符六年（1013）二月一日",
        "始置以加恩宫正邵氏，后立为定制，总领后宫女官事",
        origin,
        "职源提供精确始置日期，建立司宫令节点。",
        "职源",
        category="宫人女官",
        grade="正四品",
    )
    cite(w, "Timepoints", tp_id, i, main, "补证司宫令为宫人女官。")
    cite_fields(w, i, tp_id, ("职掌", "官品"))
    add_relation(
        w,
        i,
        find_tp(w, "宫官", "宋初"),
        tp_id,
        "统称与实例",
        main,
        "宫官为宫人女官总称，司宫令为其具体官名。",
    )
    w.commit()


OFFICES = {
    105: {
        "origin_time": "隋文帝时", "origin_event": "已置尚宫，掌导引皇后等事",
        "song_time": "宋太宗朝", "song_event": "宋朝始见置，初与太监并知内省事",
        "later_time": "宋真宗朝", "later_event": "位于司宫令之下，掌导引皇后，总管五尚物品出纳，并辖司记、司言、司簿、司闱",
        "group": "六尚书", "category": "六尚之一", "grade": "正五品",
    },
    106: {
        "origin_time": "隋炀帝时", "origin_event": "始置司言",
        "song_time": "宋太宗朝", "song_event": "宋朝始见置，掌传宣奏、启事，下辖典言、掌言及女史",
        "group": "二十四司", "category": "二十四司之一", "grade": "正七品",
    },
    107: {
        "origin_time": "隋炀帝时", "origin_event": "始置典言",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，为司言佐贰",
        "group": "二十四典", "category": "二十四典之一", "grade": "不明",
    },
    108: {
        "origin_time": "隋炀帝时", "origin_event": "始置掌言",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，与典言同为司言佐贰",
        "group": "二十四掌", "category": "二十四掌之一", "grade": "正八品",
    },
    109: {
        "song_time": "宋太宗朝", "song_event": "始置司记，初置时兼知尚书内省事",
        "later_time": "宋真宗朝以后", "later_event": "掌后宫诸司文书进出、审讫付行及监督用印，下辖典记、掌记及女史",
        "group": "二十四司", "category": "二十四司之一", "grade": "正七品",
    },
    110: {
        "origin_time": "隋炀帝时", "origin_event": "始置典记",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，为司记佐贰",
        "group": "二十四典", "category": "二十四典之一", "grade": "不明",
    },
    111: {
        "origin_time": "隋炀帝时", "origin_event": "始置掌记",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，与典记同为司记佐贰",
        "group": "二十四掌", "category": "二十四掌之一", "grade": "正八品",
    },
    112: {
        "origin_time": "隋炀帝时", "origin_event": "始置司簿，掌宫人名册及财务",
        "song_time": "宋太祖朝", "song_event": "宋朝沿置，掌宫人名簿、禄赐，下辖典簿、掌簿及女史",
        "group": "二十四司", "category": "二十四司之一", "grade": "正七品",
    },
    113: {
        "origin_time": "隋炀帝时", "origin_event": "始置典簿",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，为司簿佐贰",
        "group": "二十四典", "category": "二十四典之一", "grade": "不明",
    },
    114: {
        "origin_time": "隋炀帝时", "origin_event": "始置掌簿",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，与典簿同为司簿佐贰",
        "group": "二十四掌", "category": "二十四掌之一", "grade": "正八品",
    },
    115: {
        "origin_time": "隋炀帝时", "origin_event": "始置司闱，掌后宫门阁、钥匙",
        "song_time": "宋真宗朝", "song_event": "宋朝始见置，掌后宫门阁钥匙，下设典闱、掌闱及女史",
        "group": "二十四司", "category": "二十四司之一", "grade": "正七品",
    },
    116: {
        "origin_time": "隋炀帝时", "origin_event": "始置典闱",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，为司闱佐贰",
        "group": "二十四典", "category": "二十四典之一", "grade": "不明",
    },
    117: {
        "origin_time": "隋炀帝时", "origin_event": "始置掌闱",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，与典闱同为司闱佐贰",
        "group": "二十四掌", "category": "二十四掌之一", "grade": "正八品",
    },
    118: {
        "origin_time": "隋文帝时", "origin_event": "已置尚仪，掌后宫礼仪教学",
        "song_time": "宋真宗朝", "song_event": "宋朝始置，掌后宫礼仪、起居，管辖司籍、司乐、司宾、司赞",
        "group": "六尚书", "category": "六尚之一", "grade": "正五品",
    },
    119: {
        "origin_time": "隋炀帝时", "origin_event": "已置司籍",
        "song_time": "宋真宗朝", "song_event": "宋朝设置，掌经籍、教学及纸笔几案，下辖典籍、掌籍及女史",
        "group": "二十四司", "category": "二十四司之一", "grade": "正七品",
    },
    120: {
        "origin_time": "隋炀帝时", "origin_event": "始置典籍",
        "song_time": "宋仁宗天圣年间", "song_event": "《内命妇品职令》中始见，为司籍佐贰",
        "group": "二十四典", "category": "二十四典之一", "grade": "不明",
    },
}


def office_entry(i):
    d = OFFICES[i]
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(
        F[i]["title"],
        "官职",
        f"正文定义{F[i]['title']}为宫人女官正式官名。",
        quotation=main,
    )
    if d.get("origin_time"):
        add_timepoint(
            w,
            i,
            entity_id,
            d["origin_time"],
            d["origin_event"],
            origin,
            f"建立{F[i]['title']}的前代职源节点。",
            "职源",
            chain="head",
        )
    song_tp = add_timepoint(
        w,
        i,
        entity_id,
        d["song_time"],
        d["song_event"],
        origin,
        f"建立{F[i]['title']}的宋代见置节点。",
        "职源",
        category=d["category"],
        grade=d["grade"],
    )
    current_tp = song_tp
    if d.get("later_time"):
        current_tp = add_timepoint(
            w,
            i,
            entity_id,
            d["later_time"],
            d["later_event"],
            field(i, "职掌"),
            f"建立{F[i]['title']}后续职掌状态节点。",
            "职掌",
            category=d["category"],
            grade=d["grade"],
        )
    cite(w, "Timepoints", current_tp, i, main, f"补证{F[i]['title']}属于{d['category']}。")
    cite_fields(
        w,
        i,
        current_tp,
        tuple(name for name in ("职掌", "编制", "品阶", "别称") if name in F[i]["fields"]),
    )
    add_relation(
        w,
        i,
        find_tp(w, d["group"], "宋仁宗以后"),
        current_tp,
        "统称与实例",
        main,
        f"{d['group']}为统称，{F[i]['title']}正文明确为其一例。",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(101, 121)] == [
        "尚书内省", "知尚书内省公事", "管勾尚书内省公事", "司宫令", "尚宫",
        "司言", "典言", "掌言", "司记", "典记", "掌记", "司簿", "典簿", "掌簿",
        "司闱", "典闱", "掌闱", "尚仪", "司籍", "典籍",
    ]
    entry101()
    entry102()
    entry103()
    entry104()
    for i in range(105, 121):
        office_entry(i)


if __name__ == "__main__":
    main()
