#!/usr/bin/env python3
"""提取 chapter11t12 第62-81条：文阶总制、北宋前期本官阶及元丰易官。"""

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


F = {entry_id: load(entry_id) for entry_id in range(62, 82)}
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


def existing_sort(writer, timepoint_id):
    if timepoint_id in NEW_SORT:
        return NEW_SORT[timepoint_id]
    row = writer.conn.execute(
        "SELECT sort_order FROM NormalizedTimes WHERE timepoint_id=?",
        (timepoint_id,),
    ).fetchone()
    return row[0] if row else None


def place_new_timepoint(writer, entity_id, timepoint_id, sort_order, decision):
    """把 chain='none' 新节点按既有标准化顺序插入唯一时间链。"""
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
        candidate_sort = existing_sort(writer, candidate)
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
        timepoint_id,
        decision,
        prev_id=predecessor,
        succ_id=successor,
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
    cite(writer, "Relationships", relation_id, entry_id, quotation, decision)
    return relation_id


def group_member(writer, entry_id, group_title, time, member_tp, quotation, member_title,
                 sort_order):
    _, group_tp = state(
        writer,
        entry_id,
        group_title,
        time,
        f"{group_title}在{time}的制度范围",
        quotation,
        f"据{F[entry_id]['title']}条建立或复用{group_title}类别节点。",
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
        f"原文明示{member_title}属于{group_title}。",
    )
    return group_tp


def extract_62():
    i = 62
    writer = W(i)
    tang_quote = Q(i, "唐采历朝以来校尉旧名，置陪戎校尉，并置副尉。")
    _, tang_tp = state(
        writer, i, "陪戎副尉", "唐", "作为武散官设置", tang_quote,
        "陪戎副尉条直接记载唐代设置。", category="武散官", sort_order=61800000,
    )
    group_member(
        writer, i, "武散官", "唐", tang_tp, tang_quote, "陪戎副尉", 61800000
    )
    north_quote = Q(
        i,
        "北宋前期列入武散官二十九阶之第二十九阶。从九品下。"
        "武臣荫补官千牛备身，授陪戎副尉以上武散官阶",
    )
    _, north_tp = state(
        writer,
        i,
        "陪戎副尉",
        "北宋前期",
        "列武散官二十九阶之第二十九阶；武臣荫补官千牛备身授此阶以上",
        north_quote,
        "建立陪戎副尉北宋前期阶次、品位及荫补授阶节点。",
        category="武散官二十九阶第二十九阶",
        grade="从九品下",
        sort_order=96000000,
    )
    group_member(
        writer, i, "武散官", "北宋前期", north_tp, north_quote,
        "陪戎副尉", 96000000,
    )
    writer.commit()


def extract_63():
    i = 63
    writer = W(i)
    division_quote = Q(
        i, "宋代文官官阶，分京官、朝官与选人阶官三部分。"
    )
    _, wen_tp = state(
        writer, i, "文阶", "宋代", "文官官阶分京官、朝官与选人阶官三部分",
        division_quote, "文阶条明定宋代文阶的三部分。",
        category="职官总名", officer="职官总名", sort_order=96000000,
    )
    for title in ("京官", "朝官", "选人阶官"):
        _, child_tp = state(
            writer, i, title, "宋代", f"宋代文阶组成类别：{title}", division_quote,
            f"文阶条明列{title}为宋代文官官阶类别。",
            category="文阶官职类别", officer="职官总名", sort_order=96000000,
        )
        relation(
            writer, i, wen_tp, child_tp, "统称与实例", division_quote,
            f"文阶统称包含{title}。",
        )

    yuanfeng_quote = Q(
        i,
        "京朝官阶官，以北宋神宗元丰三年九月为界，分北宋前期本官阶"
        "（自诸寺监主簿至著作佐郎、秘书郎五阶为京官；自太子中允、赞善大夫以上至使为升朝官，即朝官。至三师）"
        "与《元丰寄禄格》（自承务郎、宣教郎五阶为京官，自通直郎以上为升朝官，即朝官。至开府仪同三司）两种。",
    )
    state(
        writer, i, "文阶", "北宋神宗元丰三年九月",
        "京朝官阶由北宋前期本官阶转入《元丰寄禄格》体系",
        yuanfeng_quote, "记录文阶京朝官制度以元丰三年九月为界的变化。",
        category="元丰寄禄格", officer="职官总名", sort_order=10800900,
    )
    count_quote = Q(
        i,
        "元丰三年所定文臣京朝官寄禄官二十五阶（如自特进算起为二十四阶），"
        "大观增置宣奉大夫等五阶，共为三十阶。",
    )
    state(
        writer, i, "文阶", "北宋神宗元丰三年", "文臣京朝官寄禄官定为二十五阶",
        count_quote, "记录元丰三年寄禄官阶数。", category="文臣寄禄官二十五阶",
        officer="职官总名", sort_order=10800000,
    )
    state(
        writer, i, "文阶", "北宋徽宗大观年间", "增置宣奉大夫等五阶，寄禄官合为三十阶",
        count_quote, "记录大观年间文臣寄禄官增阶。", category="文臣寄禄官三十阶",
        officer="职官总名", sort_order=11070000,
    )
    selection_quote = Q(
        i,
        "选人阶官，以徽宗崇宁二年九月二十五日为界，分北宋前期幕职州县官"
        "（自节察判官至判司簿尉）七等与新定选人阶官七阶（自承直郎至将仕郎）两种。",
    )
    state(
        writer, i, "选人阶官", "北宋徽宗崇宁二年九月二十五日",
        "由北宋前期幕职州县官七等改为新定选人阶官七阶",
        selection_quote, "记录选人阶官在崇宁二年的制度分界。",
        category="新定选人阶官七阶", officer="职官总名", sort_order=11030925,
    )
    zhenghe_quote = Q(
        i,
        "崇宁二年所定选人七阶，于政和六年十一月新增从政郎、修职郎、迪功郎三阶，合为十阶。",
    )
    state(
        writer, i, "选人阶官", "北宋徽宗政和六年十一月",
        "新增从政郎、修职郎、迪功郎三阶，合为十阶",
        zhenghe_quote, "记录政和六年选人阶官增至十阶。",
        category="选人阶官十阶", officer="职官总名", sort_order=11161100,
    )
    for title in ("从政郎", "修职郎", "迪功郎"):
        _, member_tp = state(
            writer, i, title, "北宋徽宗政和六年十一月",
            "新增为选人阶官", zhenghe_quote,
            f"文阶条明确记载政和六年新增{title}阶。",
            category="选人阶官新增阶", sort_order=11161100,
        )
        group_member(
            writer, i, "选人阶官", "北宋徽宗政和六年十一月",
            member_tp, zhenghe_quote, title, 11161100,
        )
    writer.commit()


def extract_64():
    i = 64
    writer = W(i)
    system_quote = Q(
        i,
        "元丰改制前，京朝官以上文臣形成了本官阶迁转序列，其中又分“有出身”、"
        "“无出身”、“带馆职”、“特旨”、“两府官”、“后族”、“中书堂后官”、"
        "“带待制”、“带翰林学士”、“宰相”、“赃罪叙复”等不同迁转途径，"
        "即自最低阶诸寺监主簿、秘书省校书郎、秘书省正字、助教至最高阶太师的本官阶序列。",
    )
    _, system_tp = state(
        writer, i, "宋前期京朝官本官阶", "北宋前期",
        "承担文臣迁转阶官与寄禄职能，依资历形成多种迁转途径",
        system_quote, "建立北宋前期京朝官本官阶制度节点。",
        category="京朝官本官阶", officer="职官总名", sort_order=96000000,
    )
    for group_title in ("京官", "朝官"):
        _, group_tp = state(
            writer, i, group_title, "北宋前期", f"宋前期京朝官本官阶中的{group_title}序列",
            system_quote, f"本官阶条明确分为{group_title}序列。",
            category="文阶官职类别", officer="职官总名", sort_order=96000000,
        )
        relation(
            writer, i, system_tp, group_tp, "统称与实例", system_quote,
            f"宋前期京朝官本官阶包含{group_title}序列。",
        )

    rank_quotes = [
        ("京官五阶：①校书郎、秘书正字、将作监主簿；", 1,
         ("校书郎", "正字", "将作监主簿")),
        ("②太常寺太祝、奉礼郎；", 2, ("太常寺太祝", "太常寺奉礼郎")),
        ("③大理评事；", 3, ("大理评事",)),
        ("④光禄寺丞、卫尉寺丞、将作鉴丞；", 4,
         ("光禄寺丞", "卫尉寺丞", "将作监丞")),
        ("⑤著作佐郎、秘书郎、大理寺丞。", 5,
         ("著作佐郎", "秘书郎", "大理寺丞")),
    ]
    for raw_quote, order, titles in rank_quotes:
        quotation = Q(i, raw_quote)
        for title in titles:
            _, member_tp = state(
                writer, i, title, "北宋前期", f"列京官五阶之第{order}阶",
                quotation, f"本官阶条将{title}列入京官第五序列的第{order}阶。",
                category=f"京官五阶第{order}阶", sort_order=96000000,
            )
            group_member(
                writer, i, "京官", "北宋前期", member_tp, quotation,
                title, 96000000,
            )

    court_quote = Q(
        i,
        "朝官二十阶：太子中允、赞善大夫、洗马、太子中舍，以上至使相。",
    )
    for title in (
        "太子中允", "太子左赞善大夫", "太子右赞善大夫",
        "太子洗马", "太子中舍", "使相",
    ):
        _, member_tp = state(
            writer, i, title, "北宋前期", "列入朝官二十阶序列",
            court_quote, f"本官阶条把{title}列入北宋前期朝官序列。",
            category="朝官二十阶", sort_order=96000000,
        )
        group_member(
            writer, i, "朝官", "北宋前期", member_tp,
            court_quote, title, 96000000,
        )

    end_quote = Q(
        i,
        "神宗元丰三年九月，以官易阶，新订了《元丰寄禄格》，官复原职，"
        "京朝官本官阶的职能即随之消失",
    )
    state(
        writer, i, "宋前期京朝官本官阶", "北宋神宗元丰三年九月",
        "以官易阶，京朝官本官阶职能消失", end_quote,
        "建立元丰三年京朝官本官阶制度终结节点。",
        category="本官阶终结", officer="职官总名", sort_order=10800900,
    )
    writer.commit()


REFORMS = {
    65: {
        "group": "京官",
        "olds": ("诸寺监主簿", "校书郎", "正字", "助教"),
        "new": "承务郎",
        "current": "文阶京官名。北宋前期本官阶之末阶。",
        "reform": "元丰三年九月，新订《元丰寄禄格》以阶易官，其官名易为承务郎",
    },
    66: {
        "group": "京官", "olds": ("太常寺太祝", "太常寺奉礼郎"),
        "new": "承奉郎", "current": "文阶京官名。北宋前期本官阶。",
        "reform": "元丰三年九月，《元丰寄禄格》易为承奉郎",
    },
    67: {
        "group": "京官", "olds": ("大理评事",), "new": "承事郎",
        "current": "文阶京官名。北宋前期京官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，易为承事郎",
    },
    68: {
        "group": "京官", "olds": ("诸寺监丞", "光禄寺丞"), "new": "宣义郎",
        "current": "文阶京官名。北宋前期京官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为宣义郎阶",
    },
    69: {
        "group": "京官", "olds": ("大理寺丞", "秘书郎"), "new": "宣德郎",
        "current": "文阶京官名。北宋前期京官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为宣德郎阶。",
        "later": ("北宋徽宗政和年间", "宣德郎", "宣教郎", "政和改为宣教郎", 11110000),
    },
    70: {
        "group": "京官", "olds": ("著作佐郎",), "new": "宣德郎",
        "current": "文阶京官名。北宋前期京官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为宣德郎阶。",
        "later": ("北宋徽宗政和年间", "宣德郎", "宣教郎", "政和改为宣教郎", 11110000),
    },
    71: {
        "group": "朝官",
        "olds": ("太子左赞善大夫", "太子右赞善大夫", "太子中舍", "太子洗马"),
        "new": "通直郎", "current": "文阶朝官名。北宋前期朝官本官阶",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官名易为通直郎",
    },
    72: {
        "group": "朝官", "olds": ("太子中允",), "new": "通直郎",
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官名改为通直郎",
    },
    73: {
        "group": "朝官", "olds": ("太常丞", "宗正丞", "秘书丞", "著作郎"),
        "new": "奉议郎", "current": "朝官名。北宋前期朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官名易为奉议郎",
    },
    74: {
        "group": "朝官", "olds": ("殿中丞",), "new": "奉议郎",
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为奉议郎阶",
    },
    75: {
        "group": "朝官", "olds": ("太常博士", "国子博士"), "new": "承议郎",
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为承议郎阶",
    },
    76: {
        "group": "朝官", "olds": ("左正言", "右正言"), "new": "承议郎",
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为承议郎阶",
    },
    77: {
        "group": "朝官", "olds": ("监察御史",), "new": None,
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，罢其本官阶名",
    },
    78: {
        "group": "朝官", "olds": ("后行员外郎",), "new": "朝奉郎",
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝奉郎",
    },
    79: {
        "group": "朝官", "olds": ("左司谏", "右司谏"), "new": "朝奉郎",
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝奉郎",
    },
    80: {
        "group": "朝官", "olds": ("殿中侍御史",), "new": "朝奉郎",
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，为朝奉郎",
    },
    81: {
        "group": "朝官", "olds": ("中行员外郎",), "new": "朝散郎",
        "current": "文阶朝官名。北宋前期京朝官本官阶。",
        "reform": "元丰三年九月新订《元丰寄禄格》，以阶易官，其官易为朝散郎",
    },
}


def extract_reform(entry_id):
    spec = REFORMS[entry_id]
    writer = W(entry_id)
    current_quote = Q(entry_id, spec["current"])
    old_current = {}
    for old_title in spec["olds"]:
        _, current_tp = state(
            writer, entry_id, old_title, "北宋前期",
            f"作为{spec['group']}本官阶", current_quote,
            f"据{F[entry_id]['title']}条建立或复用{old_title}北宋前期本官阶节点。",
            category=f"文阶{spec['group']}本官阶", sort_order=96000000,
        )
        old_current[old_title] = current_tp
        group_member(
            writer, entry_id, spec["group"], "北宋前期", current_tp,
            current_quote, old_title, 96000000,
        )

    reform_quote = Q(entry_id, spec["reform"])
    old_ends = {}
    for old_title in spec["olds"]:
        _, old_end = state(
            writer, entry_id, old_title, "北宋神宗元丰三年九月",
            (f"本官阶名易为{spec['new']}" if spec["new"] else "本官阶名被罢"),
            reform_quote, f"建立{old_title}在元丰三年以阶易官时的终结节点。",
            category="北宋前期本官阶终结", sort_order=10800900,
        )
        old_ends[old_title] = old_end

    if spec["new"]:
        new_title = spec["new"]
        _, new_tp = state(
            writer, entry_id, new_title, "北宋神宗元丰三年九月",
            f"由{F[entry_id]['title']}所列本官阶易名而来",
            reform_quote, f"建立{new_title}在元丰三年《元丰寄禄格》中的启用节点。",
            category="元丰寄禄官阶", sort_order=10800900,
        )
        group_member(
            writer, entry_id, spec["group"], "北宋神宗元丰三年九月",
            new_tp, reform_quote, new_title, 10800900,
        )
        for old_title, old_end in old_ends.items():
            relation(
                writer, entry_id, old_end, new_tp, "前后演变", reform_quote,
                f"元丰三年以阶易官，{old_title}本官阶易为{new_title}。",
            )

    if spec.get("later"):
        time, old_title, new_title, raw_quote, sort_order = spec["later"]
        later_quote = Q(entry_id, raw_quote)
        _, old_end = state(
            writer, entry_id, old_title, time, f"改名为{new_title}", later_quote,
            f"建立{old_title}政和改名终点。", category="寄禄官改名",
            sort_order=sort_order,
        )
        _, new_tp = state(
            writer, entry_id, new_title, time, f"由{old_title}改名", later_quote,
            f"建立{new_title}政和改名起点。", category="寄禄官阶",
            sort_order=sort_order,
        )
        relation(
            writer, entry_id, old_end, new_tp, "前后演变", later_quote,
            f"政和年间{old_title}改名为{new_title}。",
        )
    writer.commit()


def main():
    expected = [
        "陪戎副尉", "文阶", "宋前期京朝官本官阶",
        "诸寺监主簿、秘书省校书郎、正字、助教", "太常寺太祝、奉礼郎",
        "大理评事", "诸寺监丞、光禄寺丞", "大理寺丞、秘书郎", "著作佐郎",
        "太子左右赞善大夫、中舍、洗马", "太子中允",
        "太常、宗正、秘书丞、著作郎", "殿中丞", "太常博士、国子博士",
        "左正言、右正言", "监察御史", "后行员外郎（礼、工部诸司员外郎）",
        "左司谏、右司谏", "殿中侍御史", "中行员外郎（户、刑部诸司员外郎）",
    ]
    assert [F[i]["title"] for i in range(62, 82)] == expected
    extract_62()
    extract_63()
    extract_64()
    for entry_id in range(65, 82):
        extract_reform(entry_id)


if __name__ == "__main__":
    main()
