#!/usr/bin/env python3
"""提取 chapter11t12 第102-121条：侍郎、尚书、东宫官及三公本官阶。"""

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

# 复用上一连续批次已通过双跑和全库链校验的写入、引文及按年插链助手。
helper_spec = importlib.util.spec_from_file_location(
    "extract_11t12_082_101_helpers", HERE / "extract_11t12_082_101.py"
)
helpers = importlib.util.module_from_spec(helper_spec)
assert helper_spec.loader is not None
helper_spec.loader.exec_module(helpers)


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


F = {entry_id: load(entry_id) for entry_id in range(102, 122)}
helpers.F = F
helpers.ENTRY_DB = ENTRY_DB
helpers.NEW_SORT = {}

W = helpers.W
Q = helpers.Q
state = helpers.state
relation = helpers.relation
group_member = helpers.group_member


SPECS = {
    102: {
        "olds": ("礼部侍郎",), "new": "正议大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为正议大夫阶",
    },
    103: {
        "olds": ("刑部侍郎",), "new": "正议大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为正议大夫。",
    },
    104: {
        "olds": ("户部侍郎",), "new": "正议大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为正议大夫阶",
    },
    105: {
        "olds": ("兵部侍郎",), "new": "正议大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为正议大夫阶",
    },
    106: {
        "olds": ("吏部侍郎",), "new": "正议大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为正议大夫阶",
    },
    107: {
        "olds": ("尚书左丞", "尚书右丞"), "new": "光禄大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为光禄大夫阶",
    },
    108: {
        "olds": ("工部尚书",), "new": "银青光禄大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为银青光禄大夫阶",
    },
    109: {
        "olds": ("礼部尚书",), "new": "银青光禄大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为银青光禄大夫阶",
    },
    110: {
        "olds": ("刑部尚书",), "new": "银青光禄大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为银青光禄大夫阶",
    },
    111: {
        "olds": ("户部尚书",), "new": "银青光禄大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为银青光禄大夫阶",
    },
    112: {
        "olds": ("兵部尚书",), "new": "银青光禄大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为银青光禄大夫阶",
    },
    113: {
        "olds": ("吏部尚书",), "new": "金紫光禄大夫",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为金紫光禄大夫阶",
    },
    114: {
        "olds": ("太子少保",), "new": None,
        "reform": "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
    },
    115: {
        "olds": ("尚书右仆射",), "new": "特进",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为特进阶",
    },
    116: {
        "olds": ("太子少傅",), "new": None,
        "reform": "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
    },
    117: {
        "olds": ("尚书左仆射",), "new": "特进",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为特进阶",
    },
    118: {
        "olds": ("司空",), "new": None,
        "reform": "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
    },
    119: {
        "olds": ("太子少师",), "new": None,
        "reform": "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
    },
    120: {
        "olds": ("司徒",), "new": None,
        "reform": "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
    },
    121: {
        "olds": ("太子太保",), "new": None,
        "reform": "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
    },
}


CURRENT_QUOTE = "文阶名。北宋前期朝官本官阶。"


def extract_entry(entry_id):
    spec = SPECS[entry_id]
    writer = W(entry_id)
    current_quote = Q(entry_id, CURRENT_QUOTE)
    for old_title in spec["olds"]:
        _, current_tp = state(
            writer,
            entry_id,
            old_title,
            "北宋前期",
            "作为朝官本官阶",
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
        if spec["new"]:
            event = f"本官阶易为{spec['new']}"
        else:
            event = "未被纳入元丰新格阶列，本官阶功能终结"
        _, old_end = state(
            writer,
            entry_id,
            old_title,
            "北宋神宗元丰三年九月",
            event,
            reform_quote,
            f"建立{old_title}在元丰三年本官阶制度变化节点。",
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
        "礼部侍郎", "刑部侍郎", "户部侍郎", "兵部侍郎", "吏部侍郎",
        "尚书左丞、尚书右丞", "工部尚书", "礼部尚书", "刑部尚书",
        "户部尚书", "兵部尚书", "吏部尚书", "太子少保", "尚书右仆射",
        "太子少傅", "尚书左仆射", "司空", "太子少师", "司徒", "太子太保",
    ]
    assert [F[i]["title"] for i in range(102, 122)] == expected
    for entry_id in range(102, 122):
        extract_entry(entry_id)


if __name__ == "__main__":
    main()
