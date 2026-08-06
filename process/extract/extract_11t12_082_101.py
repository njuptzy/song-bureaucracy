#!/usr/bin/env python3
"""提取 chapter11t12 第82-101条：北宋前期朝官本官阶及元丰易官。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch11t12.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t12.db"),
)


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


F = {entry_id: load(entry_id) for entry_id in range(82, 102)}
NEW_SORT = {}


def W(entry_id):
    return EntryWriter(ENTRY_DB, F[entry_id]["title"], F[entry_id]["page"])


def Q(entry_id, needle):
    assert needle in F[entry_id]["text"], (entry_id, needle)
    return needle


def C(entry_id):
    return f'《宋代官制辞典》第{F[entry_id]["page"]}页"{F[entry_id]["title"]}"条'


def cite(writer, table, target_id, entry_id, quotation, decision):
    return writer.citation(table, target_id, C(entry_id), quotation, decision)


def normalized_sort(writer, timepoint_id):
    if timepoint_id in NEW_SORT:
        return NEW_SORT[timepoint_id]
    row = writer.conn.execute(
        "SELECT sort_order FROM NormalizedTimes WHERE timepoint_id=?", (timepoint_id,)
    ).fetchone()
    return row[0] if row else None


def place_new_timepoint(writer, entity_id, timepoint_id, sort_order, decision):
    """把 chain='none' 的新节点按既有标准化顺序插入唯一时间链。"""
    NEW_SORT[timepoint_id] = sort_order
    rows = writer.conn.execute(
        "SELECT id,prev_id,succ_id FROM Timepoints WHERE entity_id=? AND id<>?",
        (entity_id, timepoint_id),
    ).fetchall()
    if not rows:
        return
    by_id = {row[0]: row for row in rows}
    heads = [row[0] for row in rows if row[1] is None]
    assert len(heads) == 1, (entity_id, "pre-existing disconnected chain", heads)
    chain = []
    current = heads[0]
    while current is not None:
        assert current not in chain, (entity_id, "cycle", current)
        chain.append(current)
        current = by_id[current][2]
    assert len(chain) == len(rows), (entity_id, "pre-existing disconnected chain")

    successor = None
    seen_comparable = False
    for candidate in chain:
        candidate_sort = normalized_sort(writer, candidate)
        if candidate_sort is None:
            if seen_comparable:
                successor = candidate
                break
            continue
        seen_comparable = True
        if candidate_sort > sort_order:
            successor = candidate
            break
    predecessor = by_id[successor][1] if successor is not None else chain[-1]
    writer.relink(
        timepoint_id, decision, prev_id=predecessor, succ_id=successor
    )
    if predecessor is not None:
        writer.relink(predecessor, decision, succ_id=timepoint_id)
    if successor is not None:
        writer.relink(successor, decision, prev_id=timepoint_id)


def state(
    writer,
    entry_id,
    title,
    time,
    event,
    quotation,
    decision,
    *,
    category=None,
    officer="阶官",
    grade=None,
    sort_order=None,
):
    entity_id = writer.entity(title, "官职", decision, quotation=quotation)
    before = {
        row[0]
        for row in writer.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id=?", (entity_id,)
        )
    }
    timepoint_id = writer.timepoint(
        entity_id,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        attr_officer_type=officer,
        attr_grade=grade,
        chain="none",
    )
    if timepoint_id not in before and sort_order is not None:
        place_new_timepoint(
            writer,
            entity_id,
            timepoint_id,
            sort_order,
            f"按历史顺序插入{title}{time}节点：{decision}",
        )
    cite(writer, "Timepoints", timepoint_id, entry_id, quotation, decision)
    return entity_id, timepoint_id


def relation(
    writer, entry_id, subject_id, object_id, relation_type, quotation, decision
):
    relationship_id = writer.relationship(
        subject_id, object_id, relation_type, decision, quotation
    )
    cite(
        writer, "Relationships", relationship_id, entry_id, quotation, decision
    )
    return relationship_id


def group_member(
    writer, entry_id, time, member_tp, quotation, member_title, sort_order
):
    _, group_tp = state(
        writer,
        entry_id,
        "朝官",
        time,
        f"朝官在{time}的制度范围",
        quotation,
        f"据{F[entry_id]['title']}条建立或复用朝官类别节点。",
        category="文阶官职类别",
        officer="职官总名",
        sort_order=sort_order,
    )
    relation(
        writer,
        entry_id,
        group_tp,
        member_tp,
        "统称与实例",
        quotation,
        f"原文明示{member_title}属于朝官本官阶或元丰寄禄朝官。",
    )


SPECS = {
    82: {
        "olds": ("起居郎", "起居舍人"), "new": "朝散郎",
        "current": "文阶朝官名。北宋前期朝官本官阶。转兵部员外郎，带待制以上职转礼部郎中。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝散郎",
    },
    83: {
        "olds": ("侍御史",), "new": "朝请郎",
        "current": "文阶朝官名。北宋前期朝官本官阶。转司封郎中。",
        "reform": "元丰三年九月新订《元丰寄禄格》，罢其本官阶名。其阶易为朝请郎",
    },
    84: {
        "olds": ("前行员外郎",), "new": "朝请郎",
        "current": "文阶朝官名。北宋前期朝官本官阶。转后行郎中。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝请郎",
    },
    85: {
        "olds": ("后行郎中",), "new": "朝奉大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。转中行郎中。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝奉大夫阶",
    },
    86: {
        "olds": ("中行郎中",), "new": "朝散大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。转前行郎中。带待制以上转左、右司郎中。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝散大夫阶",
    },
    87: {
        "olds": ("前行郎中",), "new": "朝请大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。有出身转太常少卿，无出身转司农少卿。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝请大夫阶",
    },
    88: {
        "olds": ("左司郎中", "右司郎中"), "new": "朝议大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。左、右司郎中带待制以上职分别转左、右谏议大夫阶，带翰林学士转中书舍人阶。",
        "reform": "《元丰寄禄格》以阶易官，其官易为朝议大夫阶",
    },
    89: {
        "olds": ("卫尉少卿", "司农少卿"), "new": "朝议大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。转光禄少卿。带馆职转光禄卿。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝议大夫阶",
    },
    90: {
        "olds": ("光禄少卿",), "new": "朝议大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。转司农卿。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝议大夫阶",
    },
    91: {
        "olds": ("太常少卿", "秘书少监"), "new": "朝议大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。转光禄卿。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝议大夫阶",
    },
    92: {
        "olds": ("司农卿",), "new": None,
        "current": "文阶朝官名。北宋前期朝官本官阶。转少府监，带馆职转光禄卿。",
        "reform": "元丰三年九月新订《元丰寄禄格》，罢其本官阶",
    },
    93: {
        "olds": ("少府监",), "new": "中散大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。转卫尉卿，带馆职转光禄卿。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为中散大夫阶",
    },
    94: {
        "olds": ("卫尉卿",), "new": "中散大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。转光禄卿。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为中散大夫阶",
    },
    95: {
        "olds": ("光禄卿",), "new": "中散大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。光禄卿转秘书监。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其阶易为中散大夫阶",
    },
    96: {
        "olds": ("秘书监",), "new": "中大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。光禄卿转秘书监，秘书监转太子宾客。",
        "reform": "元丰三年九月新订《元丰寄禄格》以阶易官，其官易为中大夫阶",
    },
    97: {
        "olds": ("中书舍人",), "new": "太中大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。左、右司郎中带翰林学士职转中书舍人阶，中书舍人转礼部侍郎。",
        "reform": "元丰三年九月新订《元丰寄禄格》，罢其本官阶，其阶易为太中大夫",
    },
    98: {
        "olds": ("左谏议大夫", "右谏议大夫"), "new": "太中大夫",
        "current": "文阶朝官名。北宋前期朝官本官阶。右司郎中带待制以上职转右谏议大夫，左司郎中带待制以上职转左谏议大夫；左、右谏议大夫转给事中。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为太中大夫阶",
    },
    99: {
        "olds": ("给事中",), "new": "通议大夫",
        "current": "文阶名。北宋前期朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为通议大夫阶",
    },
    100: {
        "olds": ("太子宾客",), "new": None,
        "current": "文阶名。北宋前期朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，罢其本官阶",
    },
    101: {
        "olds": ("工部侍郎",), "new": "正议大夫",
        "current": "文阶名。北宋前期朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为正议大夫阶",
    },
}


def extract_entry(entry_id):
    spec = SPECS[entry_id]
    writer = W(entry_id)
    current_quote = Q(entry_id, spec["current"])
    for old_title in spec["olds"]:
        _, current_tp = state(
            writer,
            entry_id,
            old_title,
            "北宋前期",
            "作为朝官本官阶并依原文所列途径迁转",
            current_quote,
            f"据{F[entry_id]['title']}条建立或复用{old_title}北宋前期朝官本官阶节点。",
            category="文阶朝官本官阶",
            sort_order=96000000,
        )
        group_member(
            writer, entry_id, "北宋前期", current_tp, current_quote,
            old_title, 96000000,
        )

    reform_quote = Q(entry_id, spec["reform"])
    old_ends = {}
    for old_title in spec["olds"]:
        _, old_end = state(
            writer,
            entry_id,
            old_title,
            "北宋神宗元丰三年九月",
            (f"本官阶易为{spec['new']}" if spec["new"] else "本官阶被罢"),
            reform_quote,
            f"建立{old_title}在元丰三年以阶易官时的终结节点。",
            category="北宋前期本官阶终结",
            sort_order=10800900,
        )
        old_ends[old_title] = old_end

    if spec["new"]:
        new_title = spec["new"]
        _, new_tp = state(
            writer,
            entry_id,
            new_title,
            "北宋神宗元丰三年九月",
            f"由{F[entry_id]['title']}所列本官阶易名而来",
            reform_quote,
            f"建立{new_title}在元丰三年《元丰寄禄格》中的启用节点。",
            category="元丰寄禄官阶",
            sort_order=10800900,
        )
        group_member(
            writer, entry_id, "北宋神宗元丰三年九月", new_tp,
            reform_quote, new_title, 10800900,
        )
        for old_title, old_end in old_ends.items():
            relation(
                writer,
                entry_id,
                old_end,
                new_tp,
                "前后演变",
                reform_quote,
                f"元丰三年以阶易官，{old_title}本官阶易为{new_title}。",
            )
    writer.commit()


def main():
    expected = [
        "起居郎、起居舍人", "侍御史", "前行员外郎（吏、兵部诸司员外郎）",
        "后行郎中（礼、工部诸司郎中）", "中行郎中（户、刑部诸司郎中）",
        "前行郎中（吏、兵部诸司郎中）", "左司郎中、右司郎中",
        "卫尉少卿、司农少卿", "光禄少卿", "太常少卿、秘书少监",
        "司农卿", "少府监", "卫尉卿", "光禄卿", "秘书监", "中书舍人",
        "左谏议大夫、右谏议大夫", "给事中", "太子宾客", "工部侍郎",
    ]
    assert [F[i]["title"] for i in range(82, 102)] == expected
    for entry_id in range(82, 102):
        extract_entry(entry_id)


if __name__ == "__main__":
    main()
