#!/usr/bin/env python3
"""提取第一编第141-160条：尚服后段、尚食及尚寝前段宫官。"""

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


F = {i: load(i) for i in range(141, 161)}


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


def relation(w, i, subject, object_, quotation, decision):
    target_id = w.relationship(
        subject, object_, "统称与实例", decision, quotation
    )
    cite(w, "Relationships", target_id, i, quotation, decision)
    return target_id


def find_tp(w, title, time):
    entity_id = w.find_entity(title, "官职")
    assert entity_id, title
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time)
    return target_id


def cite_fields(w, i, tp_id):
    for name, quotation in F[i]["fields"].items():
        cite(
            w, "Timepoints", tp_id, i, quotation,
            f"补证{F[i]['title']}的{name}。", name,
        )


OFFICES = {
    141: ("隋炀帝时", "始置掌饰", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典饰同为司饰佐贰", "二十四掌", "二十四掌之一", "正八品"),
    142: ("隋炀帝时", "始置司仗，掌后宫仗卫武器", "宋真宗朝", "宋朝设置，掌后宫仗卫兵器，下辖典仗、掌仗及女史", "二十四司", "二十四司之一", "正七品"),
    143: ("隋炀帝时", "始置典仗", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司仗佐贰", "二十四典", "二十四典之一", "不明"),
    144: ("隋炀帝时", "始置掌仗", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典仗同为司仗佐贰", "二十四掌", "二十四掌之一", "正八品"),
    146: ("隋炀帝时", "始置司膳，掌膳食美味", "宋真宗朝", "宋朝设置，掌膳食、菜肴及器皿，下辖典膳、掌膳及女史", "二十四司", "二十四司之一", "正七品"),
    147: ("隋炀帝时", "始置典膳", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司膳佐贰", "二十四典", "二十四典之一", "不明"),
    148: ("隋炀帝时", "始置掌膳", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典膳同为司膳佐贰", "二十四掌", "二十四掌之一", "正八品"),
    149: ("隋炀帝时", "始置司酝", "宋真宗朝", "宋朝设置，掌酒醴，下辖典酝、掌酝及女史", "二十四司", "二十四司之一", "正七品"),
    150: ("隋炀帝时", "始置典酝", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司酝佐贰", "二十四典", "二十四典之一", "不明"),
    151: ("隋炀帝时", "始置掌酝", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典酝同为司酝佐贰", "二十四掌", "二十四掌之一", "正八品"),
    152: ("隋炀帝时", "始置司药，掌医巫、药剂", "宋太宗朝", "宋朝设置，掌医药，下辖典药、掌药及女史", "二十四司", "二十四司之一", "正七品"),
    153: ("隋炀帝时", "始置典药", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司药佐贰", "二十四典", "二十四典之一", "不明"),
    154: ("隋炀帝时", "始置掌药", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典药同为司药佐贰", "二十四掌", "二十四掌之一", "正八品"),
    155: ("隋炀帝时", "始置司饎，掌宫人伙食、柴炭", "宋真宗朝", "宋朝设置，掌宫人膳食及柴火、木炭，下辖典饎、掌饎及女史", "二十四司", "二十四司之一", "正七品"),
    156: ("隋炀帝时", "始置典饎", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司饎佐贰", "二十四典", "二十四典之一", "不明"),
    157: ("隋炀帝时", "始置掌饎", "宋仁宗天圣年间", "《内命妇品职令》中始见，与典饎同为司饎佐贰", "二十四掌", "二十四掌之一", "正八品"),
    159: ("隋炀帝时", "始置司设，掌床席帷帐、铺设洒扫", "宋真宗朝", "宋朝设置，掌帷帐床褥及洒扫铺设，下辖典设、掌设及女史", "二十四司", "二十四司之一", "正七品"),
    160: ("隋炀帝时", "始置典设", "宋仁宗天圣年间", "《内命妇品职令》中始见，为司设佐贰", "二十四典", "二十四典之一", "不明"),
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
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, group, "宋仁宗以后"), song_tp, main,
        f"{group}为统称，正文明确{F[i]['title']}为其一例。",
    )
    w.commit()


def entry145():
    i = 145
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    w = W(i)
    entity_id = w.entity(
        "尚食", "官职", "正文定义尚食为六尚之一。", quotation=main
    )
    timepoint(
        w, i, entity_id, "秦代（说法未见实例）",
        "或谓秦已置六尚并有尚食，但原书说明未见实例", history,
        "保留原书带不确定性的秦代职源说法。", "职源与沿革",
    )
    timepoint(
        w, i, entity_id, "西汉惠帝时", "已见置，为五尚之一", history,
        "建立尚食在西汉惠帝时的确证职源节点。", "职源与沿革",
    )
    timepoint(
        w, i, entity_id, "隋文帝时", "六尚之一", history,
        "建立隋文帝时六尚制度节点。", "职源与沿革",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋真宗朝",
        "宋朝始设，掌进御膳先尝，管辖司膳、司酝、司药、司饎", history,
        "建立尚食的宋代见置节点。", "职源与沿革",
        category="六尚之一", grade="正五品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证尚食为六尚之一。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "六尚书", "宋仁宗以后"), song_tp, main,
        "六尚书为统称，尚食为其一例。",
    )
    w.commit()


def entry158():
    i = 158
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(
        "尚寝", "官职", "正文定义尚寝为六尚之一。", quotation=main
    )
    timepoint(
        w, i, entity_id, "隋文帝时", "置六尚，尚寝为其一", origin,
        "建立尚寝的隋代职源节点。", "职源", chain="head",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋真宗朝",
        "宋朝始设，总掌帷帐床褥、洒扫铺设、舆扇羽仪、园苑及灯烛，管辖司设、司舆、司苑、司灯",
        origin, "建立尚寝的宋代见置节点。", "职源",
        category="六尚之一", grade="正五品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证尚寝为六尚之一。")
    cite_fields(w, i, song_tp)
    relation(
        w, i, find_tp(w, "六尚书", "宋仁宗以后"), song_tp, main,
        "六尚书为统称，尚寝为其一例。",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(141, 161)] == [
        "掌饰", "司仗", "典仗", "掌仗", "尚食", "司膳", "典膳", "掌膳", "司酝", "典酝",
        "掌酝", "司药", "典药", "掌药", "司饎", "典饎", "掌饎", "尚寝", "司设", "典设",
    ]
    for i in range(141, 145):
        office_entry(i)
    entry145()
    for i in range(146, 158):
        office_entry(i)
    entry158()
    office_entry(159)
    office_entry(160)


if __name__ == "__main__":
    main()
