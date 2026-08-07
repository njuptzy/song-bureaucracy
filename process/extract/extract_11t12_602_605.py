#!/usr/bin/env python3
"""提取 chapter11t12 第602-605条：政和十等散官的后四等。"""

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
    "extract_11t12_582_601_helpers", HERE / "extract_11t12_582_601.py"
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


F = {entry_id: load(entry_id) for entry_id in range(602, 606)}


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
relation = base.relation
append_event = base.append_event


RANKS = {
    602: ("州司马", 7, "正九品"),
    603: ("州司士参军", 8, "从九品"),
    604: ("州文学参军", 9, "从九品"),
    605: ("州助教", 10, "从九品"),
}


def extract_sanguan_ranks():
    for entry_id, (title, rank, grade) in RANKS.items():
        writer = W(entry_id)
        quote = Q(entry_id, F[entry_id]["text"])
        _, member = state_event(
            writer,
            entry_id,
            title,
            "北宋徽宗政和三年十二月以后",
            f"十等散官之第{rank}等",
            quote,
            f"据{title}专条建立政和改定后的第{rank}等散官节点。",
            category="散官制",
            officer="散官",
            grade=grade,
            sort_order=111312000,
        )
        group = writer.find_timepoint(6581, "北宋徽宗政和三年十二月")
        assert group is not None
        relation(
            writer,
            entry_id,
            group,
            member,
            "统称与实例",
            quote,
            f"{title}为政和所定十等散官之第{rank}等。",
        )
        append_event(
            writer,
            member,
            F[entry_id]["text"],
            f"以{title}专条补足官衔、位次与除授用途。",
            category="散官制",
            officer="散官",
            grade=grade,
        )
        writer.citation(
            "Timepoints",
            member,
            f'《宋代官制辞典》第{F[entry_id]["page"]}页“{title}”条',
            quote,
            f"补证{title}的散官位次、品级及用途。",
        )
        writer.commit()


def main():
    expected = ["州司马", "州司士参军", "州文学参军", "州助教"]
    assert [F[i]["title"] for i in range(602, 606)] == expected
    extract_sanguan_ranks()


if __name__ == "__main__":
    main()
