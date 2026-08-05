#!/usr/bin/env python3
"""提取第一编第221-240条：直笔等级、后宫内职与霞帔位号。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
MERGED_DICT_DB = os.path.join(
    ROOT, "data/database/song_bureaucracy_dictionary_ch1t7.db"
)
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)


ENTRY_229_TEXT = (
    "南宋后宫差遣官，掌皇后阁至贵夫人阁内命妇事务。十阁为：皇后阁、贵妃阁、"
    "淑妃阁、德妃阁、贤妃阁、嫔阁、婕妤阁、美人阁、才人阁、贵人阁。实为三兼官，"
    "系后宫内职之最高位。《宋会要·后妃》4之28：“嘉定元年正月十四日，诏主管大内"
    "公事、知尚书内省事、兼提举十阁分事、惠国庄顺夫人为从顺。”"
)
ENTRY_230_TEXT = "后宫内职名，宋真宗时置（《宋会要·后妃》4之1）。"


def repair_dictionary_split():
    """修复“辇头”正文误并入“提举十阁分”的源切分错误。"""
    bad_suffix = "孽头 " + ENTRY_230_TEXT
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            row229 = conn.execute(
                f"SELECT title,text FROM {table} WHERE id=229"
            ).fetchone()
            row230 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=230"
            ).fetchone()
            assert row229 and row229[0] == "提举十阁分", row229
            assert row230 and row230[0] == "辇头", row230
            if row229[1] != ENTRY_229_TEXT:
                assert row229[1] == ENTRY_229_TEXT + bad_suffix, row229[1]
                conn.execute(
                    f"UPDATE {table} SET text=? WHERE id=229", (ENTRY_229_TEXT,)
                )
            if row230[1] != ENTRY_230_TEXT or row230[2] is not None:
                assert not row230[1], row230[1]
                status = json.loads(row230[2] or "{}")
                assert status.get("__status__") == "placeholder", status
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=NULL WHERE id=230",
                    (ENTRY_230_TEXT,),
                )


repair_dictionary_split()


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


F = {i: load(i) for i in range(221, 241)}


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


def find_entity(w, title, type_="官职"):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    return entity_id


def find_tp(w, title, time, type_="官职"):
    entity_id = find_entity(w, title, type_)
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time, type_)
    return target_id


def exact_entity(w, title, type_, quotation, decision):
    """按原文定位同名异职实体，避免 EntryWriter.entity() 复用另一义项。"""
    row = w.conn.execute(
        "SELECT id FROM Entities WHERE title=? AND type=? AND quotation=?"
        " ORDER BY id LIMIT 1",
        (title, type_, quotation),
    ).fetchone()
    if row:
        return row[0]
    return w._insert(
        "INSERT INTO Entities (title,type,quotation) VALUES (?,?,?)",
        (title, type_, quotation), "Entities", decision,
    )


def group_palace_official(w, i, tp_id, quotation, group_time="宋初"):
    return relation(
        w, i, find_tp(w, "宫官", group_time), tp_id,
        "统称与实例", quotation,
        f"宫官为后宫女官及内职总称，{F[i]['title']}为具体实例。",
    )


def direct_writer_rank(i, title):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        title, "官职", f"正文定义{title}为带特定宫人阶衔的直笔。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", main, main,
        f"原文未给确切年月，建立{title}的宋代制度节点。",
        category="直笔等级",
    )
    for name, quotation in F[i]["fields"].items():
        cite(
            w, "Timepoints", tp_id, i, quotation,
            f"补证{title}的{name}；异序称谓不另建实体。", name,
            note=f"{name}仅作称谓证据，不另建实体",
        )
    relation(
        w, i, find_tp(w, "直笔", "宋太宗朝"), tp_id,
        "统称与实例", main, f"直笔为职事总称，{title}为按阶衔区分的实例。",
    )
    w.commit()


def simple_palace_post(i, time, event):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为后宫内职。",
        quotation=main,
    )
    tp_id = timepoint(
        w, i, entity_id, time, event, main,
        f"建立{F[i]['title']}的{time}节点。", category="后宫内职",
    )
    group_palace_official(w, i, tp_id, main)
    w.commit()


def entry221():
    direct_writer_rank(221, "尚字直笔")


def entry222():
    direct_writer_rank(222, "司字直笔")


def entry223():
    direct_writer_rank(223, "典字直笔")


def entry224():
    simple_palace_post(224, "宋真宗朝", "始置散直")


def headed_scattered_post(i, event):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为散直班职。",
        quotation=main,
    )
    tp_id = timepoint(
        w, i, entity_id, "宋真宗朝", event, main,
        f"建立{F[i]['title']}的真宗朝节点。", category="散直班职",
    )
    relation(
        w, i, find_tp(w, "散直", "宋真宗朝"), tp_id,
        "统称与实例", main, f"散直为班职总称，{F[i]['title']}为其班头等级。",
    )
    w.commit()


def entry225():
    headed_scattered_post(225, "始置，为散直班头")


def entry226():
    headed_scattered_post(226, "始置，位高于散直行首")


def entry227():
    simple_palace_post(227, "宋真宗朝", "始置乐长")


def entry228():
    i = 228
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "主管大内公事", "官职", "正文定义其为南宋后宫差遣官。", quotation=main
    )
    general = timepoint(
        w, i, entity_id, "南宋", "后宫高位差遣，常兼知尚书内省公事，仅次于提举十阁分",
        main, "建立主管大内公事的南宋制度节点。", category="后宫差遣官",
    )
    timepoint(
        w, i, entity_id, "宋宁宗庆元二年（1196）八月十三日",
        "杨从慧由知尚书内省事除主管大内公事，仍兼知尚书内省事，转崇国夫人",
        main, "保留庆元二年明确任命时间。", category="后宫差遣官",
    )
    group_palace_official(w, i, general, main, "宋仁宗以后")
    w.commit()


TEN_PAVILIONS = (
    "皇后阁", "贵妃阁", "淑妃阁", "德妃阁", "贤妃阁",
    "嫔阁", "婕妤阁", "美人阁", "才人阁", "贵人阁",
)


def entry229():
    i = 229
    main = F[i]["text"]
    w = W(i)
    office = w.entity(
        "提举十阁分", "官职", "正文定义其为南宋后宫最高位差遣官。", quotation=main
    )
    office_general = timepoint(
        w, i, office, "南宋", "掌皇后阁至贵人阁内命妇事务，实为三兼官，为后宫内职最高位",
        main, "建立提举十阁分的南宋制度节点。", category="后宫差遣官",
    )
    timepoint(
        w, i, office, "宋宁宗嘉定元年（1208）正月十四日",
        "惠国庄顺夫人兼提举十阁分事，并兼主管大内公事、知尚书内省事",
        main, "保留嘉定元年明确任命时间。", category="后宫差遣官",
    )
    group_palace_official(w, i, office_general, main, "宋仁宗以后")

    group = w.entity(
        "十阁", "机构", "原文明列皇后阁至贵人阁十个后宫阁分，建立统称机构。", quotation=main
    )
    group_tp = timepoint(
        w, i, group, "南宋", "皇后阁至贵人阁十个后宫阁分的统称",
        main, "建立十阁统称节点。", category="后宫阁分统称",
    )
    relation(
        w, i, group_tp, office_general, "编制隶属", main,
        "提举十阁分掌十阁内命妇事务，作为十阁系统的差遣官。",
    )
    for title in TEN_PAVILIONS:
        entity_id = w.entity(
            title, "机构", f"原文明列{title}为十阁之一。", quotation=main
        )
        tp_id = timepoint(
            w, i, entity_id, "南宋", f"十阁之一，由提举十阁分掌其内命妇事务",
            main, f"建立{title}的南宋节点。", category="后宫阁分",
        )
        relation(
            w, i, group_tp, tp_id, "统称与实例", main,
            f"十阁为统称，{title}为原文明列的一阁。",
        )
    w.commit()


def entry230():
    simple_palace_post(230, "宋真宗朝", "始置辇头")


def entry231():
    simple_palace_post(231, "宋真宗朝", "始置引客")


def renamed_palace_post(i, old_title, new_title, event):
    main = F[i]["text"]
    w = W(i)
    old = w.entity(
        old_title, "官职", f"原文明载{old_title}为{new_title}的旧名。", quotation=main
    )
    old_tp = timepoint(
        w, i, old, "宋太宗朝以前（具体时间未载）", f"后宫内职，后改称{new_title}",
        main, f"建立{old_title}改名前节点。", category="后宫内职",
    )
    if new_title == "直阁":
        current = exact_entity(
            w, new_title, "官职", main,
            "本条直阁是掌御寝阁值班的后宫内职，与馆阁贴职直阁同名异职，另建实体。",
        )
    else:
        current = w.entity(
            new_title, "官职", f"正文定义{new_title}为后宫内职。", quotation=main
        )
    current_tp = timepoint(
        w, i, current, "宋太宗朝", event, main,
        f"建立太宗朝{new_title}改称节点。", category="后宫内职",
    )
    relation(
        w, i, old_tp, current_tp, "前后演变", main,
        f"宋太宗朝{old_title}改称{new_title}。",
    )
    group_palace_official(w, i, current_tp, main)
    w.commit()


def entry232():
    renamed_palace_post(232, "掌御阁", "直阁", "掌御阁改称直阁，掌御寝阁值班")


def entry233():
    renamed_palace_post(233, "掌宫门", "直门", "掌宫门改称直门，掌直宫门")


def entry234():
    renamed_palace_post(234, "掌从物", "直仗", "掌从物改称直仗，掌侍从器物")


def entry235():
    simple_palace_post(235, "宋太宗朝", "始置监班，由司言兼充")


def entry236():
    direct_writer_rank(236, "宫正直笔")


def entry237():
    simple_palace_post(237, "宋太宗朝", "始置承宣，由司仪兼充")


def entry238():
    i = 238
    main = F[i]["text"]
    alias = field(i, "简称")
    w = W(i)
    entity_id = w.entity(
        "知书省", "官职", "正文定义知书省为后宫内职。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋真宗朝", "始置知书省", main,
        "建立真宗朝知书省节点。", category="后宫内职",
    )
    cite(
        w, "Timepoints", tp_id, i, alias, "补证知书省简称书省。", "简称",
        note="书省为简称，不另建实体",
    )
    group_palace_official(w, i, tp_id, main)
    w.commit()


def entry239():
    i = 239
    main = F[i]["text"]
    origin = field(i, "职源")
    rank = field(i, "品阶")
    short = field(i, "省称")
    w = W(i)
    group = w.entity(
        "霞帔", "官职", "职源字段明确霞帔为红、紫霞帔的位号统称。", quotation=origin
    )
    group_tp = timepoint(
        w, i, group, "宋神宗朝", "始见霞帔名号，用于封赐女官",
        origin, "建立霞帔统称的始见节点。", "职源",
        category="宫人位号统称",
    )
    entity_id = w.entity(
        "红霞帔", "官职", "正文定义红霞帔为宫人低级位号。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋哲宗元符三年（1100）",
        "红霞帔之称始见，为宫人迁转之阶，高于紫霞帔；向上可转入掌字阶",
        origin, "建立红霞帔称谓始见节点。", "职源",
        category="宫人位号", grade="无品秩",
    )
    cite(w, "Timepoints", tp_id, i, main, "补证红霞帔为宫人低级位号。")
    cite(w, "Timepoints", tp_id, i, rank, "补证红霞帔品阶与迁转次序。", "品阶")
    cite(
        w, "Timepoints", tp_id, i, short, "补证红霞帔省称红帔。", "省称",
        note="红帔为省称，不另建实体",
    )
    relation(
        w, i, find_tp(w, "宫人", "宋代"), tp_id,
        "统称与实例", main, "宫人为总称，红霞帔为宫人低级位号实例。",
    )
    relation(
        w, i, group_tp, tp_id, "统称与实例", origin,
        "霞帔为位号统称，红霞帔为其红色等级实例。", "职源",
    )
    w.commit()


def entry240():
    i = 240
    main = F[i]["text"]
    origin = field(i, "职源")
    rank = field(i, "品阶")
    w = W(i)
    entity_id = w.entity(
        "紫霞帔", "官职", "正文定义紫霞帔为宫人低级称号。", quotation=main
    )
    general = timepoint(
        w, i, entity_id, "南宋（具体时间未载）",
        "霞帔分红、紫二等，紫霞帔为南宋常见宫人名号",
        origin, "建立紫霞帔制度源流节点。", "职源",
        category="宫人位号", grade="无品",
    )
    cite(w, "Timepoints", general, i, main, "补证紫霞帔为宫人低级称号。")
    timepoint(
        w, i, entity_id, "宋高宗绍兴十年（1140）九月二十七日",
        "吴氏为紫霞帔，绍兴十三年六月转红霞帔",
        rank, "保留绍兴十年明确实例时间。", "品阶",
        category="宫人位号", grade="无品",
    )
    relation(
        w, i, find_tp(w, "宫人", "宋代"), general,
        "统称与实例", main, "宫人为总称，紫霞帔为宫人低级位号实例。",
    )
    group_tp = find_tp(w, "霞帔", "宋神宗朝")
    cite(w, "Timepoints", group_tp, i, origin, "补证霞帔名号始见于神宗朝。", "职源")
    relation(
        w, i, group_tp, general, "统称与实例", origin,
        "霞帔为位号统称，紫霞帔为其紫色等级实例。", "职源",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(221, 241)] == [
        "尚字直笔", "司字直笔", "典字直笔", "散直", "散直行首", "散直都行首",
        "乐长", "主管大内公事", "提举十阁分", "辇头", "引客", "直阁", "直门",
        "直仗", "监班", "宫正直笔", "承宣", "知书省", "红霞帔", "紫霞帔",
    ]
    entry221()
    entry222()
    entry223()
    entry224()
    entry225()
    entry226()
    entry227()
    entry228()
    entry229()
    entry230()
    entry231()
    entry232()
    entry233()
    entry234()
    entry235()
    entry236()
    entry237()
    entry238()
    entry239()
    entry240()


if __name__ == "__main__":
    main()
