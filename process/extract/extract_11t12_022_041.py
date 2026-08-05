#!/usr/bin/env python3
"""提取 chapter11t12 第22-41条：文散官末九阶及武散官首批。"""

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


F = {entry_id: load(entry_id) for entry_id in range(22, 42)}


def W(entry_id):
    return EntryWriter(ENTRY_DB, F[entry_id]["title"], F[entry_id]["page"])


def Q(entry_id, needle, field=None):
    source = F[entry_id]["fields"][field] if field else F[entry_id]["text"]
    assert needle in source, (entry_id, field, needle)
    return needle


def C(entry_id, field_name=None):
    base = f'《宋代官制辞典》第{F[entry_id]["page"]}页"{F[entry_id]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(writer, table, target_id, entry_id, quotation, decision, field_name=None):
    return writer.citation(
        table,
        target_id,
        C(entry_id, field_name),
        quotation,
        decision,
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
    entity_type="官职",
    field_name=None,
    entity_id=None,
):
    if entity_id is None:
        entity_id = writer.entity(
            title, entity_type, decision, quotation=quotation
        )
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
    cite(
        writer,
        "Timepoints",
        timepoint_id,
        entry_id,
        quotation,
        decision,
        field_name,
    )
    return entity_id, timepoint_id


def distinct_entity(writer, title, entity_type, quotation, decision, marker_time):
    """Reuse only the explicitly distinguished duplicate entity on reruns."""
    row = writer.conn.execute(
        """
        SELECT e.id FROM Entities e
        JOIN Timepoints t ON t.entity_id=e.id
        WHERE e.title=? AND e.type=? AND t.time=?
        ORDER BY e.id LIMIT 1
        """,
        (title, entity_type, marker_time),
    ).fetchone()
    if row:
        return row[0]
    return writer._insert(
        "INSERT INTO Entities(title,type,quotation) VALUES (?,?,?)",
        (title, entity_type, quotation),
        "Entities",
        decision,
    )


def relation(
    writer,
    entry_id,
    subject_id,
    object_id,
    relation_type,
    quotation,
    decision,
    *,
    field_name=None,
    staff_quota=None,
    staff_type=None,
):
    relation_id = writer.relationship(
        subject_id,
        object_id,
        relation_type,
        decision,
        quotation,
        staff_quota=staff_quota,
        staff_type=staff_type,
    )
    cite(
        writer,
        "Relationships",
        relation_id,
        entry_id,
        quotation,
        decision,
        field_name,
    )
    return relation_id


TIME_ORDER = {
    "西汉武帝元狩二年": -121,
    "东汉光武帝时": 25,
    "后汉献帝时": 189,
    "三国魏文帝时": 220,
    "三国魏": 220,
    "西晋平吴后": 280,
    "后魏": 386,
    "南朝梁": 502,
    "梁": 502,
    "隋": 581,
    "隋文帝时": 581,
    "隋炀帝时": 605,
    "唐": 618,
    "唐贞观": 627,
    "唐贞观元年后": 627,
    "唐贞观中": 633,
    "唐贞观后": 650,
    "唐显庆元年": 656,
    "唐贞元十一年正月十九日": 795,
    "五代十国时": 907,
    "宋初": 960,
    "北宋": 960,
    "北宋前期": 961,
    "北宋开宝九年十月": 976,
    "北宋太宗淳化元年正月": 990,
    "北宋乾兴元年": 1022,
    "北宋神宗正官名时": 1080,
    "北宋元丰寄禄格": 1080,
    "北宋元丰五年正月二十六日": 1082,
    "北宋神宗元丰五年正月二十六日": 1082,
}


def rechain(writer, entity_id, decision):
    rows = writer.conn.execute(
        "SELECT id,time FROM Timepoints WHERE entity_id=?", (entity_id,)
    ).fetchall()
    unknown = [row for row in rows if row[1] not in TIME_ORDER]
    assert not unknown, (entity_id, unknown)
    ordered = [row[0] for row in sorted(rows, key=lambda row: (TIME_ORDER[row[1]], row[0]))]
    for index, timepoint_id in enumerate(ordered):
        writer.relink(
            timepoint_id,
            decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def group_member(
    writer,
    entry_id,
    group_title,
    time,
    member_tp,
    quotation,
    member_title,
):
    group_id, group_tp = state(
        writer,
        entry_id,
        group_title,
        time,
        f"{group_title}统称在{time}的制度状态",
        quotation,
        f"据{member_title}条对{group_title}的明确归类建立或复用统称节点。",
        category="职官总名",
    )
    relation(
        writer,
        entry_id,
        group_tp,
        member_tp,
        "统称与实例",
        quotation,
        f"{member_title}是{time}{group_title}的实例。",
    )
    return group_id


WENSAN_SIMPLE = {
    23: {
        "grade": "正八品上",
        "order": "第二十二阶",
        "states": [
            ("隋文帝时", "始置", "隋文帝始置。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
        "current": "宋因之，为北宋前期文散官二十九阶之第二十二阶。正八品上",
    },
    25: {
        "grade": "从八品上",
        "order": "第二十四阶",
        "states": [
            ("隋文帝时", "始置为散官", "隋文帝始置之散官。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
        "current": "宋因之，为北宋前期文散官二十九阶之第二十四阶。从八品上",
    },
    27: {
        "grade": "正九品上",
        "order": "第二十六阶",
        "states": [
            ("隋", "设置为散官", "隋置散官，取前朝正史中有儒林传之义。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
        "current": "宋因之，为北宋前期文散官二十九阶之第二十六阶。正九品上",
    },
    29: {
        "grade": "从九品上",
        "order": "第二十八阶",
        "states": [
            ("隋", "设置为散官", "隋置散官，取北齐文林馆征文学之士以充之义。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
        "current": "宋因之，为北宋前期文散官二十九阶之第二十八阶。从九品上",
    },
    30: {
        "grade": "从九品下",
        "order": "第二十九阶，即末阶",
        "states": [
            ("隋", "设置为散官", "隋置散官。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
        "current": "宋因之，为北宋前期文散官二十九阶之第二十九阶，即末阶。从九品下",
    },
}


def wensan_simple(entry_id):
    spec = WENSAN_SIMPLE[entry_id]
    writer = W(entry_id)
    title = F[entry_id]["title"]
    touched = set()
    for time, event, raw_quote, is_member in spec["states"]:
        quotation = Q(entry_id, raw_quote)
        entity_id, timepoint_id = state(
            writer,
            entry_id,
            title,
            time,
            event,
            quotation,
            f"据{title}条建立{time}制度节点。",
            category="文散官" if is_member else "前代职源",
            officer="阶官" if is_member else None,
        )
        touched.add(entity_id)
        if is_member:
            touched.add(
                group_member(
                    writer, entry_id, "文散官", time, timepoint_id, quotation, title
                )
            )
    quotation = Q(entry_id, spec["current"])
    entity_id, current_tp = state(
        writer,
        entry_id,
        title,
        "北宋前期",
        f"列文散官二十九阶之{spec['order']}",
        quotation,
        f"建立{title}北宋前期阶次与品位节点。",
        category=f"文散官二十九阶{spec['order']}",
        officer="阶官",
        grade=spec["grade"],
    )
    touched.add(entity_id)
    touched.add(
        group_member(
            writer, entry_id, "文散官", "北宋前期", current_tp, quotation, title
        )
    )
    for entity_id in touched:
        rechain(writer, entity_id, f"按历史先后重建{title}相关时间链。")
    writer.commit()


def entry22_xuanfeng():
    entry_id = 22
    writer = W(entry_id)
    touched = set()
    quotation = Q(entry_id, "南朝梁有宣义将军。")
    precursor_id, _ = state(
        writer, entry_id, "宣义将军", "南朝梁", "已有此官名", quotation,
        "建立宣奉郎条明确记载的南朝梁职源。", category="前代职源",
    )
    touched.add(precursor_id)
    quotation = Q(entry_id, "隋炀帝置宣议郎。")
    old_id, _ = state(
        writer, entry_id, "宣议郎", "隋炀帝时", "始置", quotation,
        "建立宣议郎隋代始置节点。", category="前代职源",
    )
    quotation = Q(entry_id, "唐贞观中列入文散官。")
    _, tang_tp = state(
        writer, entry_id, "宣议郎", "唐贞观中", "列入文散官", quotation,
        "建立宣议郎唐代文散官节点。", category="文散官", officer="阶官",
    )
    touched.add(group_member(writer, entry_id, "文散官", "唐贞观中", tang_tp, quotation, "宣议郎"))
    quotation = Q(
        entry_id,
        "宋因之，开宝九年十月改宣议郎为宣奉郎，属北宋前期文散官二十九阶之第二十一阶。从七品下",
    )
    _, song_tp = state(
        writer, entry_id, "宣议郎", "宋初", "沿唐制列入文散官", quotation,
        "建立宣议郎宋初沿置节点。", category="文散官", officer="阶官",
    )
    _, old_end = state(
        writer, entry_id, "宣议郎", "北宋开宝九年十月", "改名为宣奉郎", quotation,
        "建立宣议郎开宝九年改名终点。", category="文散官", officer="阶官",
    )
    new_id, new_tp = state(
        writer, entry_id, "宣奉郎", "北宋开宝九年十月", "由宣议郎改名", quotation,
        "建立宣奉郎始名、阶次与品位节点。",
        category="文散官二十九阶第二十一阶", officer="阶官", grade="从七品下",
    )
    relation(writer, entry_id, old_end, new_tp, "前后演变", quotation, "开宝九年十月宣议郎改名宣奉郎。")
    touched.add(group_member(writer, entry_id, "文散官", "宋初", song_tp, quotation, "宣议郎"))
    touched.add(group_member(writer, entry_id, "文散官", "北宋开宝九年十月", new_tp, quotation, "宣奉郎"))
    touched.update((old_id, new_id))
    for entity_id in touched:
        rechain(writer, entity_id, "按历史先后重建宣奉郎相关时间链。")
    writer.commit()


def entry24_chengshi():
    entry_id = 24
    writer = W(entry_id)
    touched = set()
    quotation = Q(entry_id, "隋炀帝始置征事郎。")
    old_id, _ = state(
        writer, entry_id, "征事郎", "隋炀帝时", "始置", quotation,
        "建立征事郎隋代始置节点。", category="前代职源",
    )
    quotation = Q(entry_id, "唐贞观中列入文散官。")
    _, tang_tp = state(
        writer, entry_id, "征事郎", "唐贞观中", "列入文散官", quotation,
        "建立征事郎唐代文散官节点。", category="文散官", officer="阶官",
    )
    touched.add(group_member(writer, entry_id, "文散官", "唐贞观中", tang_tp, quotation, "征事郎"))
    quotation = Q(
        entry_id,
        "宋因之，乾兴元年，避仁宗赵祯讳，改征事郎为承事郎，属北宋前期文散官二十九阶之第二十三阶。正八品下",
    )
    _, song_tp = state(
        writer, entry_id, "征事郎", "宋初", "沿唐制列入文散官", quotation,
        "建立征事郎宋初沿置节点。", category="文散官", officer="阶官",
    )
    _, old_end = state(
        writer, entry_id, "征事郎", "北宋乾兴元年", "避讳改名为承事郎", quotation,
        "建立征事郎乾兴元年改名终点。", category="文散官", officer="阶官",
    )
    new_id, new_tp = state(
        writer, entry_id, "承事郎", "北宋乾兴元年", "由征事郎避讳改名", quotation,
        "建立承事郎始名、阶次与品位节点。",
        category="文散官二十九阶第二十三阶", officer="阶官", grade="正八品下",
    )
    relation(writer, entry_id, old_end, new_tp, "前后演变", quotation, "乾兴元年征事郎避讳改名承事郎。")
    touched.add(group_member(writer, entry_id, "文散官", "宋初", song_tp, quotation, "征事郎"))
    touched.add(group_member(writer, entry_id, "文散官", "北宋乾兴元年", new_tp, quotation, "承事郎"))
    touched.update((old_id, new_id))
    for entity_id in touched:
        rechain(writer, entity_id, "按历史先后重建承事郎相关时间链。")
    writer.commit()


def entry26_chengwu():
    entry_id = 26
    writer = W(entry_id)
    touched = set()
    quotation = Q(entry_id, "隋朝尚书省二十四司有承务郎（即唐之员外郎），职事官。")
    entity_id, sui_tp = state(
        writer, entry_id, "承务郎", "隋", "尚书省二十四司职事官", quotation,
        "建立承务郎隋代职事官节点。", category="前代职源", officer="职事官",
    )
    shangshu_id, shangshu_tp = state(
        writer, entry_id, "尚书省", "隋", "二十四司置承务郎", quotation,
        "建立尚书省隋代二十四司配置节点。", entity_type="机构",
    )
    relation(
        writer, entry_id, shangshu_tp, sui_tp, "编制隶属", quotation,
        "隋朝尚书省二十四司置承务郎为职事官。", staff_type="职事官",
    )
    quotation = Q(entry_id, "唐因其名，列入文散官。")
    _, tang_tp = state(
        writer, entry_id, "承务郎", "唐", "借隋官名列入文散官", quotation,
        "建立承务郎唐代文散官节点。", category="文散官", officer="阶官",
    )
    group_id = group_member(writer, entry_id, "文散官", "唐", tang_tp, quotation, "承务郎")
    quotation = Q(entry_id, "宋沿置，为北宋前期文散官二十九阶之第二十五阶。从八品下")
    _, song_tp = state(
        writer, entry_id, "承务郎", "北宋前期", "列文散官二十九阶之第二十五阶", quotation,
        "建立承务郎北宋前期阶次与品位节点。",
        category="文散官二十九阶第二十五阶", officer="阶官", grade="从八品下",
    )
    group_id = group_member(writer, entry_id, "文散官", "北宋前期", song_tp, quotation, "承务郎")
    touched.update((entity_id, group_id))
    for touched_id in touched:
        rechain(writer, touched_id, "按历史先后重建承务郎相关时间链。")

    # 尚书省原库含一个未定时间的孤立历史节点；只把本次隋代节点插入已有
    # “南朝梁 -> 宋前期”主链，不擅自处理该旧节点。
    liang = writer.find_timepoint(shangshu_id, "南朝梁")
    song = writer.find_timepoint(shangshu_id, "宋前期")
    assert liang and song
    writer.relink(liang, "在南朝梁与宋前期之间插入隋代节点。", succ_id=shangshu_tp)
    writer.relink(shangshu_tp, "接入尚书省既有历史主链。", prev_id=liang, succ_id=song)
    writer.relink(song, "在南朝梁与宋前期之间插入隋代节点。", prev_id=shangshu_tp)
    writer.commit()


def entry28_dengshi():
    entry_id = 28
    writer = W(entry_id)
    touched = set()
    quotation = Q(entry_id, "隋炀帝改常从郎为登仕郎。")
    old_id, old_end = state(
        writer, entry_id, "常从郎", "隋炀帝时", "改名为登仕郎", quotation,
        "建立常从郎隋代改名终点。", category="前代职源",
    )
    new_id, sui_tp = state(
        writer, entry_id, "登仕郎", "隋炀帝时", "由常从郎改名", quotation,
        "建立登仕郎隋代始名节点。", category="前代职源",
    )
    relation(writer, entry_id, old_end, sui_tp, "前后演变", quotation, "隋炀帝改常从郎为登仕郎。")
    quotation = Q(entry_id, "唐因之，贞观中列入文散官。")
    _, tang_tp = state(
        writer, entry_id, "登仕郎", "唐贞观中", "列入文散官", quotation,
        "建立登仕郎唐代文散官节点。", category="文散官", officer="阶官",
    )
    group_id = group_member(writer, entry_id, "文散官", "唐贞观中", tang_tp, quotation, "登仕郎")
    quotation = Q(entry_id, "宋沿置，为北宋前期文散官二十九阶之第二十七阶。正九品下")
    _, song_tp = state(
        writer, entry_id, "登仕郎", "北宋前期", "列文散官二十九阶之第二十七阶", quotation,
        "建立登仕郎北宋前期阶次与品位节点。",
        category="文散官二十九阶第二十七阶", officer="阶官", grade="正九品下",
    )
    group_id = group_member(writer, entry_id, "文散官", "北宋前期", song_tp, quotation, "登仕郎")
    touched.update((old_id, new_id, group_id))
    for entity_id in touched:
        rechain(writer, entity_id, "按历史先后重建登仕郎相关时间链。")
    writer.commit()


WUSAN_SIMPLE = {
    32: {
        "grade": "从一品", "order": "首阶",
        "states": [
            ("骠骑将军", "西汉武帝元狩二年", "始置", "西汉武帝元狩二年，始以霍去病为骠骑将军。", False),
            ("骠骑大将军", "东汉光武帝时", "已有此官名", "东汉光武帝时，以景丹为骠骑大将军。", False),
            ("骠骑大将军", "唐显庆元年", "列为武散官", "唐显庆元年，以骠骑大将军为武散官。", True),
        ],
        "current": "宋沿置，为北宋前期武散官二十九阶之首阶。从一品。",
        "end": "元丰五年正月二十六日罢，蕃官依旧",
    },
    33: {
        "grade": "正二品", "order": "第二阶",
        "states": [
            ("辅国将军", "后汉献帝时", "始置", "后汉献帝时始置辅国将军", False),
            ("辅国大将军", "西晋平吴后", "已有此官名", "西晋平吴后，以王濬为辅国大将军。", False),
            ("辅国大将军", "唐", "列为武散官", "唐以为武散官。", True),
        ],
        "current": "北宋前期列入武散官二十九阶之第二阶。正二品。",
        "end": "神宗元丰五年正月二十六日罢，蕃官所带依旧",
    },
    36: {
        "grade": "正三品", "order": "附于第四阶；授蕃官",
        "states": [
            ("怀化大将军", "唐贞元十一年正月十九日", "始置", "唐贞元十一年正月十九日始置。", True),
        ],
        "current": "北宋前期，附于武散官二十九阶之第四阶，授蕃官。正三品",
    },
    37: {
        "grade": "从三品", "order": "第五阶；使相丁忧起复所授",
        "states": [
            ("云麾将军", "梁", "作为杂号将军", "梁所置杂号将军。", False),
            ("云麾将军", "唐", "列为武散官", "唐列为武散官。", True),
        ],
        "current": "北宋前期，属武散官二十九阶之第五阶。从三品。使相丁忧起复，授云麾将军",
    },
    38: {
        "grade": "从三品", "order": "附于第五阶；授蕃官",
        "states": [
            ("归德将军", "唐贞元十一年正月十九日", "始置以授蕃官", "唐贞元十一年正月十九日置，以授蕃官。", True),
        ],
        "current": "北宋前期附于武散官二十九阶之第五阶，授蕃官。从三品",
    },
    39: {
        "grade": "正四品上", "order": "第六阶",
        "states": [
            ("忠武将军", "梁", "作为杂号将军", "梁置杂号将军。", False),
            ("忠武将军", "唐", "列入武散官", "唐列入武散官。", True),
        ],
        "current": "北宋前期为武散官二十九阶之第六阶。正四品上",
    },
    40: {
        "grade": "正四品下", "order": "第七阶",
        "states": [
            ("壮武将军", "梁", "作为杂号将军", "梁置杂号将军。", False),
            ("壮武将军", "唐", "列入武散官", "唐列入武散官。", True),
        ],
        "current": "北宋前期为武散官二十九阶之第七阶。正四品下",
    },
    41: {
        "grade": "从四品上", "order": "第八阶",
        "states": [
            ("宣威将军", "后魏", "已有此官名", "后魏有宣威将军。", False),
            ("宣威将军", "唐", "列为武散官", "唐始列为武散官。", True),
        ],
        "current": "北宋前期为武散官二十九阶之第八阶。从四品上",
    },
}


def wusan_simple(entry_id):
    spec = WUSAN_SIMPLE[entry_id]
    writer = W(entry_id)
    main_title = F[entry_id]["title"]
    touched = set()
    for title, time, event, raw_quote, is_member in spec["states"]:
        quotation = Q(entry_id, raw_quote)
        entity_id, timepoint_id = state(
            writer, entry_id, title, time, event, quotation,
            f"据{main_title}条建立{title}{time}制度节点。",
            category="武散官" if is_member else "前代职源",
            officer="阶官" if is_member else None,
        )
        touched.add(entity_id)
        if is_member:
            touched.add(group_member(writer, entry_id, "武散官", time, timepoint_id, quotation, title))
    quotation = Q(entry_id, spec["current"])
    entity_id, current_tp = state(
        writer, entry_id, main_title, "北宋前期",
        f"列武散官二十九阶之{spec['order']}", quotation,
        f"建立{main_title}北宋前期阶次、品位与授官范围节点。",
        category=f"武散官二十九阶{spec['order']}", officer="阶官", grade=spec["grade"],
    )
    touched.add(entity_id)
    touched.add(group_member(writer, entry_id, "武散官", "北宋前期", current_tp, quotation, main_title))
    if spec.get("end"):
        quotation = Q(entry_id, spec["end"])
        _, end_tp = state(
            writer, entry_id, main_title, "北宋神宗元丰五年正月二十六日",
            "罢武散官，蕃官所带依旧", quotation,
            f"建立{main_title}元丰五年罢止节点。", category="武散官终止",
        )
        touched.add(entity_id)
    for entity_id in touched:
        rechain(writer, entity_id, f"按历史先后重建{main_title}相关时间链。")
    writer.commit()


def entry31_wusan():
    entry_id = 31
    writer = W(entry_id)
    touched = set()
    quotation = Q(entry_id, "隋朝始设“散官”，“以加文武官之德声者”（《隋书·百官志》下），然隋官无文、武之分")
    general_id = distinct_entity(
        writer,
        "散官",
        "官职",
        quotation,
        "另建职官总名散官；前库同名实体是尚书省具体吏额，语义不同。",
        "隋",
    )
    general_id, sui_tp = state(
        writer, entry_id, "散官", "隋", "始设，尚无文武之分", quotation,
        "建立隋代散官总制节点。", category="职官总名", entity_id=general_id,
    )
    quotation = Q(entry_id, "至唐，“贞观年，又分文武”，凡入仕者，都带文散官或武散官，称之为“本品”")
    _, tang_general = state(
        writer, entry_id, "散官", "唐贞观", "分为文散官、武散官", quotation,
        "建立唐贞观散官分文武节点。", category="职官总名", entity_id=general_id,
    )
    wusan_id, tang_wusan = state(
        writer, entry_id, "武散官", "唐贞观", "由散官分出的武散官体系", quotation,
        "建立武散官唐贞观制度源流节点。", category="职官总名",
    )
    wensan_id, tang_wensan = state(
        writer, entry_id, "文散官", "唐贞观", "由散官分出的文散官体系", quotation,
        "武散官总条同时明确唐贞观散官分文武，补证文散官节点。", category="职官总名",
    )
    relation(writer, entry_id, tang_general, tang_wusan, "统称与实例", quotation, "唐贞观散官分为武散官。")
    relation(writer, entry_id, tang_general, tang_wensan, "统称与实例", quotation, "唐贞观散官分为文散官。")
    quotation = Q(entry_id, "宋初因唐制，设武散官二十九阶（另有怀化将军、归德将军二阶多授蕃官，未计在内）。")
    _, song_tp = state(
        writer, entry_id, "武散官", "宋初", "因唐制设二十九阶，另有两种蕃官附阶", quotation,
        "建立宋初武散官阶制节点。", category="职官总名；二十九阶",
    )
    quotation_grade = Q(
        entry_id,
        "宋代武散官阶与官品等级同。官品自一品至三品分正、从，四品至九品正从各分上、下，总三十级，武散官除无正一品外，骠骑大将军为从一品，辅国大将军正二品，以下类推，至陪戎副尉从九品下，正好二十九阶品，一官占一品位。",
    )
    cite(writer, "Timepoints", song_tp, entry_id, quotation_grade, "补证宋代武散官二十九阶与官品对应规则。")
    quotation_function = Q(
        entry_id,
        "武散官之职能，宋初，与文散官均可用以荫子或赎刑；太宗淳化元年正月，诏罢散官荫赎。",
    )
    cite(writer, "Timepoints", song_tp, entry_id, quotation_function, "补证宋初武散官可荫子或赎刑。")
    _, yinshu_end = state(
        writer, entry_id, "武散官", "北宋太宗淳化元年正月", "罢散官荫赎", quotation_function,
        "建立淳化元年罢散官荫赎节点。", category="职官总名",
    )
    quotation_later = Q(
        entry_id,
        "其后，主要职能，用以标志官品，籍此决定带武散官官员之章服，三品以上服紫、五品以上服绯、九品以上服绿。或用作蕃官加官。实际上，武散官在北宋已不常用。",
    )
    _, later_tp = state(
        writer, entry_id, "武散官", "北宋", "主要标志官品、决定章服，或作蕃官加官，已不常用", quotation_later,
        "建立北宋武散官职能与使用状态节点。", category="职官总名",
    )
    quotation_awards = Q(
        entry_id,
        "仅千牛备身授陪戎副尉以上，使相丁忧起复授云麾将军；胥吏有职事而至借衣绯者，授游击将军（如中书主事、沿堂五院行首）；使相、节度使所带武散阶至冠军大将军，遇丁忧起复，则改授游击将军。",
    )
    for title, event in (
        ("陪戎副尉", "千牛备身所授武散阶下限"),
        ("云麾将军", "使相丁忧起复所授"),
        ("游击将军", "借衣绯胥吏及使相、节度使丁忧起复所授"),
        ("冠军大将军", "使相、节度使所带武散阶上限"),
    ):
        entity_id, timepoint_id = state(
            writer, entry_id, title, "北宋", event, quotation_awards,
            f"武散官总条直接记载{title}的授用制度。", category="武散官", officer="阶官",
        )
        touched.add(entity_id)
        touched.add(group_member(writer, entry_id, "武散官", "北宋", timepoint_id, quotation_awards, title))
    quotation_end = Q(entry_id, "神宗元丰五年正月二十六日，罢武散官，蕃官依旧除授")
    _, end_tp = state(
        writer, entry_id, "武散官", "北宋神宗元丰五年正月二十六日",
        "罢武散官，蕃官依旧除授", quotation_end,
        "建立元丰五年罢武散官节点。", category="职官总名",
    )
    touched.update((general_id, wusan_id, wensan_id))
    for entity_id in touched:
        rechain(writer, entity_id, "按历史先后重建武散官总制及直接涉及官名的时间链。")
    writer.commit()


def entry34_zhenguo():
    entry_id = 34
    writer = W(entry_id)
    touched = set()
    quotation = Q(entry_id, "三国魏文帝时始置镇军大将军。")
    old_id, _ = state(
        writer, entry_id, "镇军大将军", "三国魏文帝时", "始置", quotation,
        "建立镇军大将军三国魏职源节点。", category="前代职源",
    )
    quotation = Q(entry_id, "唐以为武散官。")
    _, tang_tp = state(
        writer, entry_id, "镇军大将军", "唐", "列为武散官", quotation,
        "建立镇军大将军唐代武散官节点。", category="武散官", officer="阶官",
    )
    group_id = group_member(writer, entry_id, "武散官", "唐", tang_tp, quotation, "镇军大将军")
    quotation = Q(entry_id, "五代十国时易“镇军”为“镇国”。")
    _, old_end = state(
        writer, entry_id, "镇军大将军", "五代十国时", "改名为镇国大将军", quotation,
        "建立镇军大将军五代十国改名终点。", category="武散官", officer="阶官",
    )
    new_id, new_start = state(
        writer, entry_id, "镇国大将军", "五代十国时", "由镇军大将军改名", quotation,
        "建立镇国大将军始名节点。", category="武散官", officer="阶官",
    )
    relation(writer, entry_id, old_end, new_start, "前后演变", quotation, "五代十国时镇军大将军改名镇国大将军。")
    quotation = Q(entry_id, "北宋前期列入武散官二十九阶之第三阶。从二品。")
    _, song_tp = state(
        writer, entry_id, "镇国大将军", "北宋前期", "列武散官二十九阶之第三阶", quotation,
        "建立镇国大将军北宋前期阶次与品位节点。",
        category="武散官二十九阶第三阶", officer="阶官", grade="从二品",
    )
    group_id = group_member(writer, entry_id, "武散官", "北宋前期", song_tp, quotation, "镇国大将军")
    quotation = Q(entry_id, "神宗元丰五年正月二十六日罢，蕃官依旧")
    _, end_tp = state(
        writer, entry_id, "镇国大将军", "北宋神宗元丰五年正月二十六日",
        "罢武散官，蕃官依旧", quotation,
        "建立镇国大将军元丰五年罢止节点。", category="武散官终止",
    )
    touched.update((old_id, new_id, group_id))
    for entity_id in touched:
        rechain(writer, entity_id, "按历史先后重建镇国大将军相关时间链。")
    writer.commit()


def entry35_guanjun():
    entry_id = 35
    writer = W(entry_id)
    touched = set()
    quotation = Q(entry_id, "三国魏始置冠军将军。")
    old_id, _ = state(
        writer, entry_id, "冠军将军", "三国魏", "始置", quotation,
        "建立冠军将军三国魏职源节点。", category="前代职源",
    )
    quotation = Q(entry_id, "隋朝为散号将军，无职事者为散官。")
    _, sui_tp = state(
        writer, entry_id, "冠军将军", "隋", "作为散号将军，无职事者为散官", quotation,
        "建立冠军将军隋代制度节点。", category="前代职源",
    )
    quotation = Q(entry_id, "唐称冠军大将军，列入武散官。")
    _, old_end = state(
        writer, entry_id, "冠军将军", "唐", "改称冠军大将军", quotation,
        "建立冠军将军唐代改称终点。", category="前代职源",
    )
    new_id, tang_tp = state(
        writer, entry_id, "冠军大将军", "唐", "由冠军将军改称并列入武散官", quotation,
        "建立冠军大将军唐代始名节点。", category="武散官", officer="阶官",
    )
    relation(writer, entry_id, old_end, tang_tp, "前后演变", quotation, "唐代冠军将军改称冠军大将军。")
    group_id = group_member(writer, entry_id, "武散官", "唐", tang_tp, quotation, "冠军大将军")
    quotation = Q(entry_id, "北宋前期为武散官二十九阶之第四阶。正三品")
    _, song_tp = state(
        writer, entry_id, "冠军大将军", "北宋前期", "列武散官二十九阶之第四阶", quotation,
        "建立冠军大将军北宋前期阶次与品位节点。",
        category="武散官二十九阶第四阶", officer="阶官", grade="正三品",
    )
    group_id = group_member(writer, entry_id, "武散官", "北宋前期", song_tp, quotation, "冠军大将军")
    touched.update((old_id, new_id, group_id))
    for entity_id in touched:
        rechain(writer, entity_id, "按历史先后重建冠军大将军相关时间链。")
    writer.commit()


def main():
    assert [F[entry_id]["title"] for entry_id in range(22, 42)] == [
        "宣奉郎", "给事郎", "承事郎", "承奉郎", "承务郎", "儒林郎", "登仕郎", "文林郎", "将仕郎",
        "武散官", "骠骑大将军", "辅国大将军", "镇国大将军", "冠军大将军", "怀化大将军",
        "云麾将军", "归德将军", "忠武将军", "壮武将军", "宣威将军",
    ]
    entry22_xuanfeng()
    wensan_simple(23)
    entry24_chengshi()
    wensan_simple(25)
    entry26_chengwu()
    wensan_simple(27)
    entry28_dengshi()
    wensan_simple(29)
    wensan_simple(30)
    entry31_wusan()
    for entry_id in (32, 33):
        wusan_simple(entry_id)
    entry34_zhenguo()
    entry35_guanjun()
    for entry_id in (36, 37, 38, 39, 40, 41):
        wusan_simple(entry_id)


if __name__ == "__main__":
    main()
