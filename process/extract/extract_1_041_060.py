#!/usr/bin/env python3
"""提取第一编第41-60条：后妃人物条中的临朝职掌与皇后虚位例外。"""

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


F = {i: load(i) for i in range(41, 61)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field_name=None):
    source = F[i]["fields"][field_name] if field_name else F[i]["text"]
    assert needle in source, (i, field_name, needle)
    return needle


def C(i, field_name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(w, table, target_id, i, quotation, decision, field_name=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field_name), quotation, decision, **kwargs
    )


def timepoint_id(w, title, time):
    entity_id = w.find_entity(title, "官职")
    assert entity_id, title
    result = w.find_timepoint(entity_id, time)
    assert result, (title, time)
    return result


def cite_regency(i, title, quotation, decision):
    w = W(i)
    target_id = timepoint_id(w, title, "宋代")
    cite(
        w,
        "Timepoints",
        target_id,
        i,
        quotation,
        decision,
        note="该条为具体人物生平，人物本身不建实体；仅追加其直接证明的临朝职掌事实",
    )
    w.commit()


def entry42():
    i = 42
    quotation = Q(
        i,
        "嘉祐八年(1063)英宗即位，尊为皇太后。因英宗患病，曹太后垂帘听政。"
        "治平元年(1064)五月，还政于英宗赵曙。",
    )
    cite_regency(
        i,
        "皇太后",
        quotation,
        "仁宗曹皇后条补证皇太后在皇帝患病时垂帘听政并还政。",
    )


def entry43():
    i = 43
    quotation = Q(
        i,
        "元丰八年（1085），年方九岁的赵煦(哲宗)即皇帝位，尊为太皇太后，临朝称制。",
    )
    cite_regency(
        i,
        "太皇太后",
        quotation,
        "英宗高皇后条补证幼帝即位时太皇太后临朝称制。",
    )


def entry44():
    i = 44
    quotation = Q(
        i,
        "哲宗崩，决策立端王赵佶继位，是为徽宗。自元符三年（1100）二月"
        "垂帘听政，至七月还政。",
    )
    cite_regency(
        i,
        "皇太后",
        quotation,
        "神宗向皇后条补证皇太后参与皇位决策、垂帘听政并还政。",
    )


def entry47():
    i = 47
    quotation = Q(
        i,
        "建炎三年三月，禁卫扈从军统制官苗傅、刘正彦发动兵变，逼高宗逊位于皇子，"
        "请隆祐太后垂帘听政。四月初，太后还政于宋高宗。",
    )
    cite_regency(
        i,
        "皇太后",
        quotation,
        "哲宗孟皇后条补证兵变期间皇太后垂帘听政并还政。",
    )


def entry53():
    i = 53
    quotation = Q(i, "高宗不知，虚皇后位以待。")
    w = W(i)
    target_id = timepoint_id(w, "皇后", "宋代")
    cite(
        w,
        "Timepoints",
        target_id,
        i,
        quotation,
        "高宗邢皇后条记载高宗未知其已崩，实际虚后位以待，作为规范性‘不能虚位’的历史例外。",
        note="与‘皇后不能有二人，也不能虚位’的规范性表述形成历史例外；邢皇后人物本身不建实体",
        conflict_flag=1,
    )
    w.commit()


def entry54():
    i = 54
    quotation = Q(
        i,
        "绍熙五年（1194）夏，孝宗崩，尊为太皇太后。光宗病，不能主持孝宗丧礼。"
        "吴皇后因宰执之请，垂帘听政，立皇子嘉王为皇帝（是为宁宗），光宗退位。次日，撤帘。",
    )
    cite_regency(
        i,
        "太皇太后",
        quotation,
        "高宗吴皇后条补证太皇太后在皇帝患病时垂帘、立帝并次日撤帘。",
    )


SKIPPED_ENTRIES = {
    41: "具体人物的册立、废黜与生平",
    45: "具体人物位号迁转，皇太妃设置已由专条提取",
    46: "具体人物的进封与追谥",
    48: "具体人物位号迁转",
    49: "具体人物的册立与生平",
    50: "具体人物位号迁转",
    51: "具体人物生平与个人尊号",
    52: "具体人物的册立与生平",
    55: "具体人物的册立与生平",
    56: "具体人物的追封",
    57: "具体人物的册立与生平",
    58: "具体人物位号迁转",
    59: "具体人物生平与实际擅政",
    60: "具体人物的册立与生平",
}


def main():
    assert [F[i]["title"] for i in range(41, 61)] == [
        "仁宗郭皇后", "仁宗曹皇后", "英宗高皇后", "神宗向皇后", "神宗钦成德妃",
        "神宗陈美人", "哲宗孟皇后", "哲宗刘皇后", "徽宗王皇后", "徽宗郑皇后",
        "徽宗韦贤妃", "钦宗朱皇后", "高宗邢皇后", "高宗吴皇后", "高宗潘贤妃",
        "孝宗郭夫人", "孝宗夏皇后", "孝宗谢皇后", "光宗李皇后", "宁宗韩皇后",
    ]
    entry42()
    entry43()
    entry44()
    entry47()
    entry53()
    entry54()
    for i, reason in SKIPPED_ENTRIES.items():
        print(f"#{i} {F[i]['title']}: skipped ({reason})")


if __name__ == "__main__":
    main()
