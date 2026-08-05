#!/usr/bin/env python3
"""提取 chapter11t12 第42-61条：武散官第九至第二十八阶。"""

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


F = {entry_id: load(entry_id) for entry_id in range(42, 62)}


def W(entry_id):
    return EntryWriter(ENTRY_DB, F[entry_id]["title"], F[entry_id]["page"])


def Q(entry_id, needle):
    assert needle in F[entry_id]["text"], (entry_id, needle)
    return needle


def C(entry_id):
    return f'《宋代官制辞典》第{F[entry_id]["page"]}页"{F[entry_id]["title"]}"条'


def cite(writer, table, target_id, entry_id, quotation, decision):
    return writer.citation(
        table, target_id, C(entry_id), quotation, decision
    )


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
    officer=None,
    grade=None,
):
    entity_id = writer.entity(title, "官职", decision, quotation=quotation)
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
    cite(writer, "Timepoints", timepoint_id, entry_id, quotation, decision)
    return entity_id, timepoint_id


def relation(
    writer,
    entry_id,
    subject_id,
    object_id,
    relation_type,
    quotation,
    decision,
):
    relation_id = writer.relationship(
        subject_id, object_id, relation_type, decision, quotation
    )
    cite(
        writer, "Relationships", relation_id, entry_id, quotation, decision
    )
    return relation_id


TIME_ORDER = {
    "西汉武帝时": -141,
    "汉武帝时": -141,
    "三国魏": 220,
    "晋朝": 266,
    "梁": 502,
    "唐": 618,
    "唐贞观": 627,
    "唐显庆元年": 656,
    "唐贞元十一年正月十九日": 795,
    "宋初": 960,
    "北宋": 960,
    "北宋前期": 961,
    "北宋太宗淳化元年正月": 990,
    "北宋神宗元丰五年正月二十六日": 1082,
}


def rechain(writer, entity_id, decision):
    rows = writer.conn.execute(
        "SELECT id,time FROM Timepoints WHERE entity_id=?", (entity_id,)
    ).fetchall()
    unknown = [row for row in rows if row[1] not in TIME_ORDER]
    assert not unknown, (entity_id, unknown)
    ordered = [
        row[0]
        for row in sorted(rows, key=lambda row: (TIME_ORDER[row[1]], row[0]))
    ]
    for index, timepoint_id in enumerate(ordered):
        writer.relink(
            timepoint_id,
            decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def group_member(
    writer, entry_id, time, member_tp, quotation, member_title
):
    group_id, group_tp = state(
        writer,
        entry_id,
        "武散官",
        time,
        f"武散官统称在{time}的制度状态",
        quotation,
        f"据{member_title}条对武散官的明确归类建立或复用统称节点。",
        category="职官总名",
    )
    relation(
        writer,
        entry_id,
        group_tp,
        member_tp,
        "统称与实例",
        quotation,
        f"{member_title}是{time}武散官的实例。",
    )
    return group_id


SPECS = {
    42: {
        "order": "第九阶", "grade": "从四品下",
        "origin": ("明威将军", "梁", "作为杂号将军", "梁所置杂号将军。"),
        "tang": "唐以为武散官。",
        "current": "北宋前期列入武散官二十九阶之第九阶。从四品下",
    },
    43: {
        "order": "第十阶", "grade": "正五品上",
        "origin": ("定远将军", "梁", "作为杂号将军", "梁置杂号将军。"),
        "tang": "唐以为武散官。",
        "current": "北宋前期属武散官二十九阶之第十阶。正五品上",
    },
    44: {
        "order": "第十一阶", "grade": "正五品下",
        "origin": ("宁远将军", "晋朝", "始置", "晋朝始置。"),
        "tang": "唐以为武散官。",
        "current": "北宋前期为武散官二十九阶之第十一阶。正五品下",
    },
    45: {
        "order": "第十二阶", "grade": "从五品上",
        "origin": ("游骑将军", "三国魏", "始置", "三国魏置。"),
        "tang": "唐以为武散官。",
        "current": "北宋前期列入武散官二十九阶之第十二阶。从五品上",
    },
    46: {
        "order": "第十三阶", "grade": "从五品下",
        "origin": ("游击将军", "西汉武帝时", "始置", "西汉武帝时始置。"),
        "tang": "唐以为武散官。",
        "current": "北宋前期为武散官二十九阶之第十三阶。从五品下。",
        "usage": "使相、节度使武官散官阶至冠军大将军，如遇丁忧起复，改授游击将军。有职事吏人服色借绯者，如遇赦许加游击将军一次",
    },
    47: {
        "order": "第十四阶", "grade": "正六品上",
        "generic_origin": ("西汉武帝时", "校尉之名始置", "校尉之名始置于西汉武帝时。"),
        "tang": "唐采历朝以来校尉旧名，设昭武校尉，列入武散官。",
        "current": "北宋前期属武散官二十九阶之第十四阶。正六品上",
    },
    48: {
        "order": "第十五阶", "grade": "正六品下", "base": "昭武校尉",
        "tang": "唐朝采历朝以来校尉旧名，置昭武校尉，并置副尉。",
        "current": "北宋前期列入武散官二十九阶之第十五阶。正六品下",
    },
    49: {
        "order": "第十六阶", "grade": "从六品上",
        "generic_origin": ("西汉武帝时", "校尉之名始置", "校尉之名始置于西汉武帝时。"),
        "tang": "唐采历朝以来校尉旧名，设振威校尉为武散官。",
        "current": "北宋前期列入武散官二十九阶之第十六阶。从六品上",
    },
    50: {
        "order": "第十七阶", "grade": "从六品下", "base": "振威校尉",
        "tang": "唐朝采历朝以来校尉旧名，设振威校尉，并置副尉，为武散官。",
        "current": "北宋前期列入武散官二十九阶之第十七阶。从六品下",
    },
    51: {
        "order": "第十八阶", "grade": "正七品上",
        "generic_origin": ("西汉武帝时", "校尉之名始置", "校尉之名，始于西汉武帝时。"),
        "tang": "唐朝采历朝以来校尉旧名，设致果校尉为武散官。",
        "current": "北宋前期列入武散官二十九阶之第十八阶。正七品上",
    },
    52: {
        "order": "第十九阶", "grade": "正七品下", "base": "致果校尉",
        "tang": "唐朝采历朝以来校尉旧名，置致果校尉，并置副尉。",
        "current": "北宋前期列入武散官二十九阶之第十九阶。正七品下",
    },
    53: {
        "order": "第二十阶", "grade": "从七品上",
        "generic_origin": ("汉武帝时", "校尉之名始置", "校尉之名始于汉武帝时。"),
        "tang": "唐采历朝以来校尉旧名，设翊麾校尉，为武散官。",
        "current": "北宋前期列入武散官二十九阶之第二十阶。从七品上",
    },
    54: {
        "order": "第二十一阶", "grade": "从七品下", "base": "翊麾校尉",
        "tang": "唐朝采历代以来校尉旧名，置翊麾校尉，并置副尉，为武散官。",
        "current": "北宋前期列入武散官二十九阶之第二十一阶。从七品下",
    },
    55: {
        "order": "第二十二阶", "grade": "正八品上",
        "generic_origin": ("汉武帝时", "校尉之名始置", "校尉之名始于汉武帝时。"),
        "tang": "唐采历朝以来校尉旧名，设宣节校尉，为武散官。",
        "current": "北宋前期列入武散官二十九阶之第二十二阶。正八品上",
    },
    56: {
        "order": "第二十三阶", "grade": "正八品下", "base": "宣节校尉",
        "tang": "唐采历朝以来校尉旧名，设宣节校尉，并置副尉。",
        "current": "北宋前期列入武散官二十九阶之第二十三阶。正八品下",
    },
    57: {
        "order": "第二十四阶", "grade": "从八品上",
        "generic_origin": ("西汉武帝时", "校尉之名始置", "校尉之名始于西汉武帝时。"),
        "tang": "唐采历朝以来校尉旧名，设御武校尉，为武散官。",
        "current": "北宋前期列入武散官二十九阶之第二十四阶。从八品上",
    },
    58: {
        "order": "第二十五阶", "grade": "从八品下", "base": "御武校尉",
        "tang": "唐采历朝以来校尉旧名，设御武校尉，并置副尉。",
        "current": "北宋前期列入武散官二十九阶之第二十五阶。从八品下",
    },
    59: {
        "order": "第二十六阶", "grade": "正九品上",
        "generic_origin": ("西汉武帝时", "校尉之名始置", "校尉之名始于西汉武帝时。"),
        "tang": "唐采历朝以来校尉旧名，设仁勇校尉。",
        "current": "北宋前期列入武散官二十九阶之第二十六阶。正九品上",
    },
    60: {
        "order": "第二十七阶", "grade": "从九品上", "base": "仁勇校尉",
        "tang": "唐采历朝以来校尉旧名设仁勇校尉，并置副尉。",
        "current": "北宋前期列入武散官二十九阶之第二十七阶。从九品上",
    },
    61: {
        "order": "第二十八阶", "grade": "从九品上", "deputy": "陪戎副尉",
        "generic_origin": ("西汉武帝时", "校尉之名始置", "校尉之名始于西汉武帝时。"),
        "tang": "唐采历朝以来校尉旧名，设陪戎校尉，并置副尉。",
        "current": "北宋前期列入武散官二十九阶之第二十八阶。从九品上",
    },
}


def extract_entry(entry_id):
    spec = SPECS[entry_id]
    title = F[entry_id]["title"]
    writer = W(entry_id)
    touched = set()

    if spec.get("origin"):
        origin_title, time, event, raw_quote = spec["origin"]
        quotation = Q(entry_id, raw_quote)
        entity_id, _ = state(
            writer, entry_id, origin_title, time, event, quotation,
            f"据{title}条建立{origin_title}{time}职源节点。", category="前代职源",
        )
        touched.add(entity_id)

    if spec.get("generic_origin"):
        time, event, raw_quote = spec["generic_origin"]
        quotation = Q(entry_id, raw_quote)
        generic_id, _ = state(
            writer, entry_id, "校尉", time, event, quotation,
            f"{title}条直接记载校尉官名的汉代职源。", category="前代职源",
        )
        touched.add(generic_id)

    quotation = Q(entry_id, spec["tang"])
    tang_entities = []
    if spec.get("base"):
        tang_entities.append(spec["base"])
        tang_entities.append(title)
    else:
        tang_entities.append(title)
        if spec.get("deputy"):
            tang_entities.append(spec["deputy"])
    for tang_title in tang_entities:
        entity_id, tang_tp = state(
            writer, entry_id, tang_title, "唐", "列入武散官", quotation,
            f"据{title}条建立{tang_title}唐代武散官节点。",
            category="武散官", officer="阶官",
        )
        touched.add(entity_id)
        touched.add(
            group_member(writer, entry_id, "唐", tang_tp, quotation, tang_title)
        )

    quotation = Q(entry_id, spec["current"])
    main_id, current_tp = state(
        writer,
        entry_id,
        title,
        "北宋前期",
        f"列武散官二十九阶之{spec['order']}",
        quotation,
        f"建立{title}北宋前期阶次与品位节点。",
        category=f"武散官二十九阶{spec['order']}",
        officer="阶官",
        grade=spec["grade"],
    )
    touched.add(main_id)
    touched.add(
        group_member(writer, entry_id, "北宋前期", current_tp, quotation, title)
    )

    if spec.get("usage"):
        quotation = Q(entry_id, spec["usage"])
        _, usage_tp = state(
            writer,
            entry_id,
            title,
            "北宋",
            "使相、节度使丁忧起复及借绯吏人遇赦所授",
            quotation,
            "补录游击将军在北宋的明确授用制度。",
            category="武散官",
            officer="阶官",
        )
        touched.add(main_id)

    for entity_id in touched:
        rechain(writer, entity_id, f"按历史先后重建{title}相关时间链。")
    writer.commit()


def main():
    assert [F[entry_id]["title"] for entry_id in range(42, 62)] == [
        "明威将军", "定远将军", "宁远将军", "游骑将军", "游击将军",
        "昭武校尉", "昭武副尉", "振威校尉", "振威副尉", "致果校尉",
        "致果副尉", "翊麾校尉", "翊麾副尉", "宣节校尉", "宣节副尉",
        "御武校尉", "御武副尉", "仁勇校尉", "仁勇副尉", "陪戎校尉",
    ]
    for entry_id in range(42, 62):
        extract_entry(entry_id)


if __name__ == "__main__":
    main()
