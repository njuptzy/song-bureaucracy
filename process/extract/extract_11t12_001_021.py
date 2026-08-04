#!/usr/bin/env python3
"""提取 chapter11t12 第1-21条：文散官总制及其第一至第二十阶。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch11t12.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch11t12.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter11t12 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {0: load(1), **{i: load(i + 1) for i in range(1, 21)}}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field=None):
    source = F[i]["fields"][field] if field else F[i]["text"]
    assert needle in source, (i, field, needle)
    return needle


def C(i, field_name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(w, table, target_id, i, quotation, decision, field_name=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field_name), quotation, decision, **kwargs
    )


def state(
    w,
    i,
    title,
    time,
    event,
    quotation,
    decision,
    *,
    category=None,
    officer=None,
    grade=None,
    field_name=None,
):
    eid = w.entity(title, "官职", decision, quotation=quotation)
    tid = w.timepoint(
        eid,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        attr_officer_type=officer,
        attr_grade=grade,
        chain="none",
    )
    cite(w, "Timepoints", tid, i, quotation, decision, field_name)
    return eid, tid


def relation(
    w, i, subject_tp, object_tp, relation_type, quotation, decision,
    field_name=None,
):
    rid = w.relationship(
        subject_tp, object_tp, relation_type, decision, quotation
    )
    cite(w, "Relationships", rid, i, quotation, decision, field_name)
    return rid


ERA_START = {
    "开宝": 968,
}
ERA_RE = re.compile("|".join(ERA_START))
PRE_SONG_ORDER = {
    "秦": -221,
    "西汉武帝太初元年": -104,
    "西汉成帝时": -32,
    "王莽新朝": 9,
    "南朝齐": 479,
    "西晋": 265,
    "魏晋以后": 265,
    "后魏": 386,
    "北周": 557,
    "北周、隋": 557,
    "隋": 581,
    "隋文帝时": 581,
    "隋炀帝时": 605,
    "唐": 618,
    "唐武德七年": 624,
    "唐贞观": 627,
    "唐贞观元年后": 627,
    "唐贞观中": 633,
    "唐贞观后": 650,
    "宋初": 960,
    "北宋前期": 961,
    "北宋神宗正官名时": 1080,
    "北宋元丰五年正月二十六日": 1082,
}


def time_key(time, row_id):
    if time in PRE_SONG_ORDER:
        return (PRE_SONG_ORDER[time], row_id)
    match = ERA_RE.search(time)
    if match:
        year = ERA_START[match.group(0)]
        number = re.search(r"([一二三四五六七八九十元]+)年", time[match.end():])
        values = {"元": 1, "一": 1, "二": 2, "三": 3, "四": 4,
                  "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
        if number:
            year += values.get(number.group(1), 1) - 1
        return (year, row_id)
    return (0, row_id)


def rechain(w, entity_id, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (entity_id,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid,
            decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def group_member(
    w, i, time, member_tp, quotation, member_title, field_name=None,
):
    group_eid, group_tp = state(
        w,
        i,
        "文散官",
        time,
        f"文散官统称在{time}的制度状态",
        quotation,
        f"据{member_title}条对文散官的明确归类建立或复用统称节点。",
        category="职官总名",
        field_name=field_name,
    )
    relation(
        w,
        i,
        group_tp,
        member_tp,
        "统称与实例",
        quotation,
        f"{member_title}是{time}文散官的实例。",
        field_name,
    )
    return group_eid


NORMAL = {
    1: {
        "grade": "从一品", "order": "首阶；宰相官所带阶；使相加阶",
        "current": "北宋因之，为前期文散官二十九阶之首阶。从一品。系宰相官所带阶",
        "past": [
            ("南朝齐", "开府仪同三司之名始见", "开府仪同三司之名始于南朝齐。", False),
            ("隋文帝时", "始作为散官", "隋文帝时始以为散官。", False),
            ("唐", "列于文散官", "唐列于文散官。", True),
        ],
    },
    2: {
        "grade": "正二品", "order": "第二阶；宰相所带阶；使相加阶",
        "current": "北宋因之，前期为文散官二十九阶之第二阶。正二品。系宰相所带阶",
        "past": [
            ("西汉成帝时", "已经设置", "西汉成帝时已置。", False),
            ("隋文帝时", "作为散官", "隋文帝以为散官，炀帝废罢。", False),
            ("隋炀帝时", "废罢", "隋文帝以为散官，炀帝废罢。", False),
            ("唐", "列入文散官", "唐列入文散官。", True),
        ],
    },
    3: {
        "grade": "从二品", "order": "第三阶；执政所带阶",
        "current": "宋因之。北宋前期为文散官二十九阶之第三阶。从二品。系执政所带阶",
        "past": [
            ("西汉武帝太初元年", "始置", "西汉武帝太初元年始置。", False),
            ("北周、隋", "作为散官", "北周、隋为散官。", False),
            ("唐贞观元年后", "列入文散官", "唐贞观元年后列入文散官。", True),
        ],
    },
    4: {
        "grade": "正三品", "order": "第四阶；执政所带阶",
        "current": "宋因之。北宋前期为文散官二十九阶之第四阶。正三品。系执政所带阶",
        "past": [
            ("魏晋以后", "光禄大夫位重者加金章紫绶，因称金紫光禄大夫",
             "魏晋以后，光禄大夫之位重者，加金章紫绶，因称金紫光禄大夫。", False),
            ("北周、隋", "作为散官", "北周、隋为散官。", False),
            ("唐贞观后", "列入文散官", "唐贞观后列入文散官。", True),
        ],
    },
    5: {
        "grade": "从三品", "order": "第五阶；执政所带阶",
        "current": "宋因之。北宋前期为文散官二十九阶之第五阶。从三品。系执政所带阶",
        "past": [
            ("西晋", "已有银青光禄大夫", "西晋有银青光禄大夫，实为不加金章紫绶之光禄大夫。", False),
            ("后魏", "与光禄大夫、金紫光禄大夫并置", "后魏光禄大夫、金紫光禄大夫，银青光禄大夫并置。", False),
            ("北周、隋", "作为散官", "北周、隋为散官。", False),
            ("唐贞观后", "列入文散官", "唐贞观后列入文散官。", True),
        ],
    },
    8: {
        "grade": "从四品上", "order": "第八阶",
        "current": "宋因之，北宋前期为文散官二十九阶之第八阶。从四品上",
        "past": [
            ("秦", "已有太中大夫官名", "秦官名。", False),
            ("北周", "作为散官", "北周为散官。", False),
            ("唐贞观后", "列入文散官", "唐贞观后列入文散官。", True),
        ],
    },
    9: {
        "grade": "从四品下", "order": "第九阶",
        "current": "宋因之，北宋前期为文散官二十九阶之第九阶。从四品下",
        "past": [
            ("秦", "已有中大夫官名", "秦官名。", False),
            ("唐", "列入文散官", "唐列入文散官。", True),
        ],
    },
    10: {
        "grade": "正五品上", "order": "第十阶",
        "current": "宋因之，北宋前期为文散官二十九阶之第十阶。正五品上",
        "past": [
            ("王莽新朝", "始置", "王莽新朝置。", False),
            ("北周", "作为散官", "北周为新官。", False),
            ("唐贞观", "列入文散官", "唐贞观列入文散官。", True),
        ],
    },
    12: {
        "grade": "从五品上", "order": "第十二阶",
        "current": "宋因之，北宋前期为文散官二十九阶之第十二阶。从五品上",
        "past": [
            ("隋", "始置为散官", "始置于隋，散官。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
    },
    13: {
        "grade": "从五品下", "order": "第十三阶",
        "current": "宋因之，北宋前期属文散官二十九阶之第十三阶。从五品下",
        "past": [
            ("隋", "始置为散官", "始置于隋，散官。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
    },
    17: {
        "grade": "从六品下", "order": "第十七阶",
        "current": "宋因之，北宋前期为文散官二十九阶之第十七阶。从六品下",
        "past": [
            ("隋", "设置为散官", "隋置散官，采晋宋以来诸官员须通同宿直官署之意。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
    },
    18: {
        "grade": "正七品上", "order": "第十八阶",
        "current": "宋因之，北宋前期为文散官二十九阶之第十八阶。正七品上",
        "past": [
            ("隋", "设置为散官", "隋置散官。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
    },
    19: {
        "grade": "正七品下", "order": "第十九阶",
        "current": "宋因之，北宋前期为文散官二十九阶之第十九阶。正七品下",
        "past": [
            ("隋", "设置为散官", "隋置散官。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
    },
    20: {
        "grade": "从七品上", "order": "第二十阶",
        "current": "宋因之，北宋前期为文散官二十九阶之第二十阶。从七品上",
        "past": [
            ("隋", "设置为散官", "隋置散官。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
    },
}


RENAMES = (
    ("正议大夫", "正奉大夫"),
    ("通议大夫", "通奉大夫"),
    ("朝议大夫", "朝奉大夫"),
    ("朝议郎", "朝奉郎"),
    ("承议郎", "承直郎"),
    ("奉议郎", "奉直郎"),
    ("宣议郎", "宣奉郎"),
)


def entry0_wensan():
    i = 0
    w = W(i)
    touched = set()
    q_tang = Q(i, "散官之分文、武，始于唐贞观年间。")
    group_eid, tang_tp = state(
        w, i, "文散官", "唐贞观", "散官开始分文、武", q_tang,
        "建立文散官唐贞观制度源流节点。", category="职官总名",
    )
    q_song = Q(i, "宋初，因唐制，文散官自开府仪同三司至将仕郎，共二十九阶。")
    _, song_tp = state(
        w, i, "文散官", "宋初", "因唐制设置二十九阶", q_song,
        "建立宋初文散官二十九阶总制节点。", category="职官总名",
    )
    q_rename = Q(
        i,
        "开宝九年十月，太宗登位，避光义之讳，改正议大夫、通议大夫、朝议大夫、朝议郎、承议郎、奉议郎、宣议郎为正奉大夫、通奉大夫、朝奉大夫、朝奉郎、承直郎、奉直郎、宣奉郎。",
    )
    _, rename_group_tp = state(
        w, i, "文散官", "北宋开宝九年十月",
        "太宗登位避讳，七阶改名", q_rename,
        "建立文散官开宝九年七阶改名节点。", category="职官总名",
    )
    q_end = Q(i, "神宗元丰五年正月二十六日，罢文散阶，蕃官依旧许加授")
    _, end_tp = state(
        w, i, "文散官", "北宋元丰五年正月二十六日",
        "罢文散阶，蕃官依旧许加授", q_end,
        "建立元丰五年罢文散阶节点。", category="职官总名",
    )
    touched.add(group_eid)

    q_grade = Q(
        i,
        "宋代文散官阶与官品等级同，官品自一品至三品分正从为六阶，自四品至九品分正从、并各分上下，共二十四阶，总计三十阶；文散官除无正一品外，开府仪同三司为从一品，特进为正二品，以下类推，至将仕郎从九品下，一官占一品位，正好二十九品阶。",
    )
    q_duty = Q(
        i,
        "文散官之职能，则用以标志官品，籍此决定带文散官官员之章服，三品以上服紫、五品以上服绯、九品以上服绿。此外，别无意义。",
    )
    q_award = Q(
        i,
        "其除授之法，每遇郊祀大礼加恩，京朝官于郎阶上每次加五阶、于大夫阶上每次加一阶；选人每次加一阶；至朝散大夫以上，须服紫方许加。内殿崇班初授加银青光禄大夫阶、诸司使以上使额高者，加金紫光禄大夫阶。其中，开府仪同三司、特进为宰相、使相加阶，光禄大夫、金紫光禄大夫、通奉大夫为执政加阶。",
    )
    cite(w, "Timepoints", song_tp, i, q_grade,
         "补证宋代文散官的阶数与官品对应规则。")
    cite(w, "Timepoints", song_tp, i, q_duty,
         "补证宋代文散官标志官品并决定章服的职能。")
    cite(w, "Timepoints", song_tp, i, q_award,
         "补证宋代文散官的除授规则及宰执所加阶。")

    for old_title, new_title in RENAMES:
        old_eid, old_song = state(
            w, i, old_title, "宋初", "沿唐制列入文散官", q_rename,
            f"据文散官总条建立{old_title}宋初状态。",
            category="文散官", officer="阶官",
        )
        _, old_end = state(
            w, i, old_title, "北宋开宝九年十月", f"避讳改名为{new_title}",
            q_rename, f"建立{old_title}开宝九年改名终点。",
            category="文散官", officer="阶官",
        )
        new_eid, new_start = state(
            w, i, new_title, "北宋开宝九年十月", f"由{old_title}避讳改名",
            q_rename, f"建立{new_title}开宝九年始名节点。",
            category="文散官", officer="阶官",
        )
        relation(w, i, old_end, new_start, "前后演变", q_rename,
                 f"开宝九年十月{old_title}避讳改名为{new_title}。")
        relation(w, i, song_tp, old_song, "统称与实例", q_song,
                 f"{old_title}是宋初文散官实例。")
        relation(w, i, rename_group_tp, new_start, "统称与实例", q_rename,
                 f"{new_title}是开宝九年改名后的文散官实例。")
        touched.update((old_eid, new_eid))

    for entity_id in touched:
        rechain(w, entity_id, "按历史先后重建文散官总制及七组改名链。")
    w.commit()


def normal_entry(i):
    spec = NORMAL[i]
    title = F[i]["title"]
    current_quote = Q(i, spec["current"])
    w = W(i)
    touched = set()
    eid, current_tp = state(
        w,
        i,
        title,
        "北宋前期",
        f"列北宋前期文散官二十九阶之{spec['order'].split('；')[0]}",
        current_quote,
        f"建立{title}北宋前期阶次与品位节点。",
        category=f"文散官二十九阶{spec['order']}",
        officer="阶官",
        grade=spec["grade"],
    )
    touched.add(eid)
    touched.add(group_member(w, i, "北宋前期", current_tp, current_quote, title))

    for time, event, raw_quote, is_group_member in spec["past"]:
        quote = Q(i, raw_quote)
        _, tp = state(
            w, i, title, time, event, quote,
            f"据{title}条建立{time}职源节点。",
            category="文散官" if is_group_member else "前代职源",
            officer="阶官" if is_group_member else None,
        )
        if is_group_member:
            touched.add(group_member(w, i, time, tp, quote, title))

    for entity_id in touched:
        rechain(w, entity_id, f"按历史先后重建{title}相关时间链。")
    w.commit()


def entry7():
    i = 7
    w = W(i)
    touched = set()
    q_sui = Q(i, "隋始置。")
    old_eid, sui_tp = state(
        w, i, "通议大夫", "隋", "始置", q_sui,
        "文散官总条明确通奉大夫旧名通议大夫，据本条补建隋代职源。",
        category="前代职源",
    )
    q_tang = Q(i, "唐列入文散官。")
    _, tang_tp = state(
        w, i, "通议大夫", "唐", "列入文散官", q_tang,
        "文散官总条明确通奉大夫旧名通议大夫，据本条补建唐代节点。",
        category="文散官", officer="阶官",
    )
    touched.add(group_member(w, i, "唐", tang_tp, q_tang, "通议大夫"))

    q_current = Q(
        i,
        "宋因之。北宋前期为文散官二十九阶之第七阶。正四品下",
    )
    new_eid, new_tp = state(
        w, i, "通奉大夫", "北宋开宝九年十月", "由通议大夫避讳改名",
        q_current, "补充通奉大夫北宋前期阶次与品位。",
        category="文散官二十九阶第七阶；执政加阶",
        officer="阶官", grade="正四品下",
    )
    old_end = w.find_timepoint(old_eid, "北宋开宝九年十月")
    group_eid = w.find_entity("文散官", "官职")
    assert old_end and group_eid
    group_tp = w.find_timepoint(group_eid, "北宋开宝九年十月")
    assert group_tp
    relation(w, i, group_tp, new_tp, "统称与实例", q_current,
             "通奉大夫为北宋前期文散官第七阶。")
    touched.update((old_eid, new_eid, group_eid))
    for entity_id in touched:
        rechain(w, entity_id, "按历史先后重建通奉大夫相关时间链。")
    w.commit()


def rename_entry(
    i,
    old_title,
    old_states,
    rename_time,
    rename_quote,
    grade,
    order,
    *,
    old_song_quote=None,
):
    new_title = F[i]["title"]
    w = W(i)
    touched = set()
    old_eid = old_last_tp = None

    for time, event, raw_quote, is_group_member in old_states:
        quote = Q(i, raw_quote)
        old_eid, old_last_tp = state(
            w, i, old_title, time, event, quote,
            f"据{new_title}条建立{old_title}{time}职源节点。",
            category="文散官" if is_group_member else "前代职源",
            officer="阶官" if is_group_member else None,
        )
        touched.add(old_eid)
        if is_group_member:
            touched.add(group_member(w, i, time, old_last_tp, quote, old_title))

    if old_song_quote:
        quote = Q(i, old_song_quote)
        old_eid, old_last_tp = state(
            w, i, old_title, "宋初", "沿前代名称设置", quote,
            f"建立{old_title}宋初沿置节点。",
            category="文散官", officer="阶官",
        )
        touched.add(old_eid)
        touched.add(group_member(w, i, "宋初", old_last_tp, quote, old_title))

    quote = Q(i, rename_quote)
    assert old_eid and old_last_tp
    old_end = state(
        w, i, old_title, rename_time, f"改名为{new_title}", quote,
        f"建立{old_title}改名终点。", category="文散官", officer="阶官",
    )[1]
    new_eid, new_tp = state(
        w, i, new_title, rename_time, f"由{old_title}改名", quote,
        f"建立{new_title}始名及北宋前期阶次节点。",
        category=f"文散官二十九阶{order}", officer="阶官", grade=grade,
    )
    touched.update((old_eid, new_eid))
    relation(
        w, i, old_end, new_tp, "前后演变", quote,
        f"{rename_time}{old_title}改名为{new_title}。",
    )
    touched.add(group_member(w, i, rename_time, new_tp, quote, new_title))
    for entity_id in touched:
        rechain(w, entity_id, f"按历史先后重建{new_title}相关时间链。")
    w.commit()


def entry6():
    rename_entry(
        6,
        "正议大夫",
        [
            ("隋", "始置为散官", "隋置正议大夫，为散官。", False),
            ("唐", "列入文散官", "唐列入文散官。", True),
        ],
        "北宋开宝九年十月",
        "开宝九年十月改为正奉大夫，属宋前期二十九阶之第六阶。正四品上。系执政所带阶",
        "正四品上",
        "第六阶；执政所带阶",
        old_song_quote="宋因之。",
    )

    # 简称不建实体；其中引文明确给出同一改名的异纪年及神宗复名事实。
    w = W(6)
    first_quote = Q(
        6,
        "太平兴国元年，诏改为正奉。",
        "简称",
    )
    for title in ("正议大夫", "正奉大夫"):
        eid = w.find_entity(title, "官职")
        assert eid
        tp = w.find_timepoint(eid, "北宋开宝九年十月")
        assert tp
        cite(
            w, "Timepoints", tp, 6, first_quote,
            "简称字段以太平兴国元年补证开宝九年十月的同一改名事件。",
            "简称",
        )

    restore_quote = Q(6, "神宗正官名，复曰正议。", "简称")
    zhengfeng = w.find_entity("正奉大夫", "官职")
    zhengyi = w.find_entity("正议大夫", "官职")
    assert zhengfeng and zhengyi
    _, zhengfeng_end = state(
        w, 6, "正奉大夫", "北宋神宗正官名时", "复名为正议大夫",
        restore_quote, "建立神宗正官名时正奉大夫复名终点。",
        category="文散官", officer="阶官", field_name="简称",
    )
    _, zhengyi_restore = state(
        w, 6, "正议大夫", "北宋神宗正官名时", "由正奉大夫复名",
        restore_quote, "建立神宗正官名时正议大夫复名节点。",
        category="文散官", officer="阶官", field_name="简称",
    )
    rid = w.relationship(
        zhengfeng_end, zhengyi_restore, "前后演变",
        "神宗正官名时正奉大夫复称正议大夫。", restore_quote,
    )
    cite(
        w, "Relationships", rid, 6, restore_quote,
        "神宗正官名时正奉大夫复称正议大夫。", "简称",
    )
    group_eid = group_member(
        w, 6, "北宋神宗正官名时", zhengyi_restore, restore_quote,
        "正议大夫", "简称",
    )
    for entity_id in (zhengfeng, zhengyi, group_eid):
        rechain(w, entity_id, "按历史先后补入神宗正官名时复名节点。")
    w.commit()


def entry11():
    rename_entry(
        11,
        "朝议大夫",
        [
            ("隋", "始置为散官", "原为朝议大夫，始置于隋，为散官。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
        "北宋开宝九年十月",
        "太宗即位，于开宝九年十月改名为朝奉大夫，属宋前期二十九阶之第十一阶。正五品上",
        "正五品上",
        "第十一阶",
        old_song_quote="宋初因之。",
    )


def entry14():
    rename_entry(
        14,
        "朝议郎",
        [
            ("隋", "始置为散官", "原为隋置散官朝议郎。", False),
            ("唐贞观中", "列入文散官", "唐贞观中列入文散官。", True),
        ],
        "北宋开宝九年十月",
        "宋因之，开宝九年十月改朝议郎为朝奉郎，属宋前期文散官二十九阶之第十四阶。正六品上",
        "正六品上",
        "第十四阶",
        old_song_quote="宋因之，开宝九年十月改朝议郎为朝奉郎",
    )


def entry15():
    rename_entry(
        15,
        "承议郎",
        [
            ("隋", "始置为散官", "原为隋所置散官承议郎。", False),
            ("唐贞观", "列入文散官", "唐贞观列入文散官。", True),
        ],
        "北宋开宝九年十月",
        "太宗即位，于开宝九年十月改承议郎为承直郎，属宋前期文散官二十九阶之第十五阶。正六品下",
        "正六品下",
        "第十五阶",
        old_song_quote="宋初因之",
    )


def entry16():
    i = 16
    w = W(i)
    touched = set()
    q_sui = Q(i, "原为隋所置散官通议郎。")
    tong_eid, tong_start = state(
        w, i, "通议郎", "隋", "始置为散官", q_sui,
        "建立通议郎隋代职源节点。", category="前代职源",
    )
    q_tang = Q(i, "唐武德七年改通议郎为奉议郎。")
    _, tong_end = state(
        w, i, "通议郎", "唐武德七年", "改名为奉议郎", q_tang,
        "建立通议郎改名终点。", category="前代职源",
    )
    feng_eid, feng_start = state(
        w, i, "奉议郎", "唐武德七年", "由通议郎改名", q_tang,
        "建立奉议郎唐武德七年始名节点。", category="文散官", officer="阶官",
    )
    relation(w, i, tong_end, feng_start, "前后演变", q_tang,
             "唐武德七年通议郎改名奉议郎。")

    q_song = Q(i, "宋因之")
    _, feng_song = state(
        w, i, "奉议郎", "宋初", "沿唐制设置", q_song,
        "建立奉议郎宋初沿置节点。", category="文散官", officer="阶官",
    )
    touched.add(group_member(w, i, "宋初", feng_song, q_song, "奉议郎"))

    q_rename = Q(
        i,
        "开宝九年十月，改奉议郎为奉直郎，属宋前期文散官二十九阶之第十六阶。从六品上",
    )
    _, feng_end = state(
        w, i, "奉议郎", "北宋开宝九年十月", "改名为奉直郎", q_rename,
        "建立奉议郎开宝改名终点。", category="文散官", officer="阶官",
    )
    new_eid, new_tp = state(
        w, i, "奉直郎", "北宋开宝九年十月", "由奉议郎改名", q_rename,
        "建立奉直郎始名、阶次和品位节点。",
        category="文散官二十九阶第十六阶", officer="阶官", grade="从六品上",
    )
    relation(w, i, feng_end, new_tp, "前后演变", q_rename,
             "北宋开宝九年十月奉议郎改名奉直郎。")
    touched.add(group_member(w, i, "北宋开宝九年十月", new_tp, q_rename, "奉直郎"))
    touched.update((tong_eid, feng_eid, new_eid))
    for entity_id in touched:
        rechain(w, entity_id, "按历史先后重建奉直郎相关改名链。")
    w.commit()


def supplement_wensan_carriers():
    i = 0
    quote = Q(
        i,
        "其中，开府仪同三司、特进为宰相、使相加阶，光禄大夫、金紫光禄大夫、通奉大夫为执政加阶。",
    )
    w = W(i)
    for title, time in (
        ("开府仪同三司", "北宋前期"),
        ("特进", "北宋前期"),
        ("光禄大夫", "北宋前期"),
        ("金紫光禄大夫", "北宋前期"),
        ("通奉大夫", "北宋开宝九年十月"),
    ):
        eid = w.find_entity(title, "官职")
        assert eid
        tp = w.find_timepoint(eid, time)
        assert tp
        cite(
            w, "Timepoints", tp, i, quote,
            f"文散官总条补证{title}为宰相、使相或执政所加阶。",
        )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1, 21)] == [
        "开府仪同三司", "特进", "光禄大夫", "金紫光禄大夫", "银青光禄大夫",
        "正奉大夫", "通奉大夫", "太中大夫", "中大夫", "中散大夫",
        "朝奉大夫", "朝请大夫", "朝散大夫", "朝奉郎", "承直郎",
        "奉直郎", "通直郎", "朝请郎", "宣德郎", "朝散郎",
    ]
    entry0_wensan()
    for i in (1, 2, 3, 4, 5):
        normal_entry(i)
    entry6()
    entry7()
    for i in (8, 9, 10):
        normal_entry(i)
    entry11()
    for i in (12, 13):
        normal_entry(i)
    entry14()
    entry15()
    entry16()
    for i in (17, 18, 19, 20):
        normal_entry(i)
    supplement_wensan_carriers()


if __name__ == "__main__":
    main()
