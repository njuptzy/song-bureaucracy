#!/usr/bin/env python3
"""提取 chapter11t12 第122-141条：旧本官阶终结及元丰寄禄官前七阶。"""

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


F = {entry_id: load(entry_id) for entry_id in range(122, 142)}
helpers.F = F
helpers.ENTRY_DB = ENTRY_DB
helpers.NEW_SORT = {}

W = helpers.W
Q = helpers.Q
state = helpers.state
relation = helpers.relation
group_member = helpers.group_member


def stipend_group(writer, entry_id, time, event, quotation, sort_order):
    return state(
        writer,
        entry_id,
        "寄禄官",
        time,
        event,
        quotation,
        "据原文建立或复用寄禄官制度节点。",
        category="文臣阶官总称",
        officer="职官总名",
        sort_order=sort_order,
    )[1]


def stipend_member(
    writer, entry_id, time, member_tp, quotation, member_title, sort_order
):
    group_tp = stipend_group(
        writer,
        entry_id,
        time,
        f"寄禄官在{time}的制度范围",
        quotation,
        sort_order,
    )
    relation(
        writer,
        entry_id,
        group_tp,
        member_tp,
        "统称与实例",
        quotation,
        f"原文明示{member_title}属于寄禄官阶。",
    )


def extract_old_ranks():
    common = "文阶名。北宋前期朝官本官阶。"
    for entry_id in range(122, 128):
        writer = W(entry_id)
        title = F[entry_id]["title"]
        current_quote = Q(entry_id, common)
        _, current_tp = state(
            writer,
            entry_id,
            title,
            "北宋前期",
            "作为朝官本官阶",
            current_quote,
            f"据{title}条建立或复用北宋前期朝官本官阶节点。",
            category="文阶朝官本官阶",
            sort_order=96000000,
        )
        group_member(
            writer, entry_id, "北宋前期", current_tp, current_quote,
            title, 96000000,
        )
        reform_needle = {
            122: "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
            123: "元丰三年九月新订《元丰寄禄格》，以阶易官，其官未被纳入新格阶列之中。",
            124: "元丰三年九月新订《元丰寄禄格》，以阶易官，其官未被纳入新格阶列之中。",
            125: "元丰三年九月新订《元丰寄禄格》，以阶易官，其官未被纳入新格阶列之中。",
            126: "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
            127: "元丰三年九月新订《元丰寄禄格》，未被纳入新格阶列之中。",
        }[entry_id]
        reform_quote = Q(entry_id, reform_needle)
        state(
            writer,
            entry_id,
            title,
            "北宋神宗元丰三年九月",
            "未被纳入元丰新格阶列，本官阶功能终结",
            reform_quote,
            f"据原文建立{title}元丰三年退出本官阶制度的节点。",
            category="北宋前期本官阶终结",
            sort_order=10800900,
        )
        writer.commit()


def extract_general_system():
    entry_id = 128
    writer = W(entry_id)
    system_quote = Q(
        entry_id,
        "宋代文臣阶官，自北宋元丰三年九月制订《元丰寄禄格》之后，迄南宋，总称寄禄官。“寄禄”，决定俸料之意。",
    )
    stipend_group(
        writer,
        entry_id,
        "北宋神宗元丰三年九月",
        "《元丰寄禄格》制订后，宋代文臣阶官总称寄禄官",
        system_quote,
        10800900,
    )
    changes = [
        (
            "北宋神宗元丰三年九月",
            "《元丰寄禄格》定开府仪同三司至承务郎二十五阶，选人七阶不在新格内",
            "①《元丰寄禄格》定开府仪同三司至承务郎为二十五阶。选人自两使职官至判司簿尉七阶不在新格之内",
            10800900,
        ),
        (
            "北宋哲宗元祐三年二月六日",
            "六个寄禄官阶名分左、右",
            "②哲宗元祐三年二月六日，寄禄官部分阶名分左、右：左、右金紫光禄大夫，左、右银青光禄大夫，左、右光禄大夫，左、右正议大夫，左、右中散大夫，左、右朝议大夫",
            10830206,
        ),
        (
            "北宋哲宗元祐四年十一月四日",
            "朝请大夫至承务郎十四阶增分左、右，二十阶均分左右",
            "③元祐四年十一月四日，又增朝请大夫至承务郎十四阶分左、右。至此，寄禄官除开府仪同三司、特进、通议大夫、太中大夫、中大夫五阶不分左、右外，其余二十阶均分左、右",
            10891104,
        ),
        (
            "北宋哲宗绍圣二年四月三日",
            "罢十四阶及金紫光禄大夫左、右之分",
            "④绍圣二年四月三日，罢元祐四年朝请大夫至承务郎十四阶左、右之分，并罢金紫光禄大夫分左、右，仍各作一资；余不变",
            10950403,
        ),
        (
            "北宋徽宗大观二年六月二十七日",
            "罢寄禄官左右之分，新增五阶，寄禄官共三十阶",
            "⑤徽宗大观二年六月二十七日，罢分左、右，在《元丰寄禄格》基础上，新增置了宣奉、正奉、通奉、中奉、奉直大夫五阶，寄禄官总为三十阶",
            11080627,
        ),
        (
            "南宋高宗绍兴元年十二月二十二日",
            "恢复并扩大寄禄官左右之分",
            "⑥南宋高宗绍兴元年十二月二十二日，恢复元祐分左、右之制，并扩大至选人阶及大观新增五阶、元祐时未分左右之通议、太中、中大夫三阶",
            11311222,
        ),
        (
            "南宋孝宗淳熙元年二月",
            "罢寄禄官分左右",
            "⑦孝宗淳熙元年二月，罢寄禄官分左右",
            11740200,
        ),
        (
            "北宋徽宗崇宁二年九月二十五日",
            "选人七阶改名",
            "①徽宗崇宁二年九月二十五日，改选人七阶名为承直、儒林、文林、从事、通仕、登仕、将仕郎",
            11030925,
        ),
        (
            "北宋徽宗政和六年十一月",
            "选人七阶增为十阶并改名",
            "②政和六年十一月，选人七阶增为十阶",
            11161100,
        ),
    ]
    for time, event, needle, sort_order in changes:
        quote = Q(entry_id, needle)
        stipend_group(writer, entry_id, time, event, quote, sort_order)
    writer.commit()


RANK_SPECS = {
    129: ("开府仪同三司", ("使相",), "从一品", "首", "北宋元丰三年九月由使相（节度使兼侍中、中书令，或兼同中书门下平章事）改名。"),
    130: ("特进", ("尚书左仆射", "尚书右仆射"), "从一品", "第二", "北宋神宗元丰三年九月，由尚书左、右仆射改名。"),
    131: ("金紫光禄大夫", ("吏部尚书",), "正二品", "第三", "北宋神宗元丰三年九月，由吏部尚书阶改名。"),
    133: ("银青光禄大夫", ("户部尚书", "礼部尚书", "兵部尚书", "刑部尚书", "工部尚书"), "从二品", "第四", "北宋神宗元丰三年九月，由五部（户、礼、兵、刑、工）尚书改名。"),
    135: ("光禄大夫", ("尚书左丞", "尚书右丞"), "正三品", "第五", "北宋神宗元丰三年九月，由尚书左、右丞阶改名。"),
}


def extract_yuanfeng_ranks():
    for entry_id, (new_title, old_titles, grade, ordinal, needle) in RANK_SPECS.items():
        writer = W(entry_id)
        quote = Q(entry_id, needle)
        old_summary = "、".join(old_titles)
        _, new_tp = state(
            writer,
            entry_id,
            new_title,
            "北宋神宗元丰三年九月",
            f"由{old_summary}改名，为寄禄官三十阶之{ordinal}阶",
            quote,
            f"据原文建立或复用{new_title}元丰寄禄官节点。",
            category="文臣京朝官寄禄官三十阶",
            officer="寄禄官",
            grade=grade,
            sort_order=10800900,
        )
        stipend_member(
            writer, entry_id, "北宋神宗元丰三年九月", new_tp,
            quote, new_title, 10800900,
        )
        for old_title in old_titles:
            _, old_tp = state(
                writer,
                entry_id,
                old_title,
                "北宋神宗元丰三年九月",
                f"改名为{new_title}",
                quote,
                f"据原文建立或复用{old_title}改名节点。",
                category="北宋前期本官阶终结",
                sort_order=10800900,
            )
            relation(
                writer, entry_id, old_tp, new_tp, "前后演变", quote,
                f"元丰三年{old_title}本官阶改名为{new_title}寄禄官阶。",
            )
        writer.commit()


def split_or_merge_state(
    writer, entry_id, title, time, event, quotation, sort_order
):
    return state(
        writer,
        entry_id,
        title,
        time,
        event,
        quotation,
        f"据原文建立或复用{title}{time}的左右分合节点。",
        category="文臣京朝官寄禄官三十阶",
        officer="寄禄官",
        sort_order=sort_order,
    )[1]


def add_split(writer, entry_id, base, left, right, time, quote, sort_order):
    base_tp = split_or_merge_state(
        writer, entry_id, base, time, f"分置{left}、{right}", quote, sort_order
    )
    for title in (left, right):
        child_tp = split_or_merge_state(
            writer, entry_id, title, time, f"由{base}分置", quote, sort_order
        )
        relation(
            writer, entry_id, base_tp, child_tp, "前后演变", quote,
            f"原文明示{base}在{time}分为{title}。",
        )
        stipend_member(writer, entry_id, time, child_tp, quote, title, sort_order)


def add_merge(writer, entry_id, base, left, right, time, quote, sort_order):
    base_tp = split_or_merge_state(
        writer, entry_id, base, time, "罢左右之分", quote, sort_order
    )
    stipend_member(writer, entry_id, time, base_tp, quote, base, sort_order)
    for title in (left, right):
        child_tp = split_or_merge_state(
            writer, entry_id, title, time, f"罢分，并回{base}", quote, sort_order
        )
        relation(
            writer, entry_id, child_tp, base_tp, "前后演变", quote,
            f"原文明示{title}在{time}罢分，并回{base}。",
        )


def extract_left_right_entries():
    specs = {
        132: (
            "金紫光禄大夫", "左金紫光禄大夫", "右金紫光禄大夫",
            [
                ("split", "北宋哲宗元祐三年二月", "金紫光禄大夫于北宋哲宗元祐三年二月分左、右", 10830200),
                ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 10950400),
                ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分", 11311200),
                ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月又罢分", 11740300),
            ],
        ),
        134: (
            "银青光禄大夫", "左银青光禄大夫", "右银青光禄大夫",
            [
                ("split", "北宋哲宗元祐三年二月", "银青光禄大夫于北宋哲宗元祐三年二月分左、右", 10830200),
                ("merge", "北宋徽宗大观二年六月", "大观二年六月罢分", 11080600),
                ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 11311200),
                ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月又罢", 11740300),
            ],
        ),
        136: (
            "光禄大夫", "左光禄大夫", "右光禄大夫",
            [
                ("split", "北宋哲宗元祐三年二月", "光禄大夫于北宋哲宗元祐三年二月分左、右", 10830200),
                ("merge", "北宋徽宗大观二年六月", "徽宗大观二年六月罢分", 11080600),
                ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分", 11311200),
                ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢分", 11740300),
            ],
        ),
    }
    for entry_id, (base, left, right, changes) in specs.items():
        writer = W(entry_id)
        for kind, time, needle, sort_order in changes:
            quote = Q(entry_id, needle)
            if kind == "split":
                add_split(writer, entry_id, base, left, right, time, quote, sort_order)
            else:
                add_merge(writer, entry_id, base, left, right, time, quote, sort_order)
        writer.commit()


def extract_three_guanglu():
    entry_id = 137
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "寄禄官金紫光禄大夫、银青光禄大夫、光禄大夫合称。"
        "《玉海》卷119《元丰新定官制》：“（元祐三年二月）"
        "诏三光禄、正议、中散、朝议大夫六阶各分左右。”",
    )
    _, group_tp = state(
        writer,
        entry_id,
        "三光禄",
        "北宋哲宗元祐三年二月",
        "金紫光禄大夫、银青光禄大夫、光禄大夫合称三光禄",
        quote,
        "据原文建立三光禄统称节点。",
        category="寄禄官合称",
        officer="职官总名",
        sort_order=10830200,
    )
    for title in ("金紫光禄大夫", "银青光禄大夫", "光禄大夫"):
        _, member_tp = state(
            writer,
            entry_id,
            title,
            "北宋哲宗元祐三年二月",
            "列入三光禄合称范围",
            quote,
            f"据原文建立或复用{title}列入三光禄的节点。",
            category="文臣京朝官寄禄官三十阶",
            officer="寄禄官",
            sort_order=10830200,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示三光禄是包括{title}在内的合称。",
        )
    writer.commit()


def extract_new_daguan_ranks():
    specs = {
        138: ("宣奉大夫", "左光禄大夫", "第六", "正三品", "北宋徽宗大观二年六月二十七日所增置之新阶名，换左光禄大夫阶"),
        140: ("正奉大夫", "右光禄大夫", "第七", "正三品", "北宋徽宗大观二年六月二十七日新置阶名，换右光禄大夫。"),
    }
    for entry_id, (new_title, old_title, ordinal, grade, needle) in specs.items():
        writer = W(entry_id)
        quote = Q(entry_id, needle)
        old_tp = split_or_merge_state(
            writer, entry_id, old_title, "北宋徽宗大观二年六月二十七日",
            f"罢分，阶名换为{new_title}", quote, 11080627,
        )
        _, new_tp = state(
            writer,
            entry_id,
            new_title,
            "北宋徽宗大观二年六月二十七日",
            f"新增寄禄官阶，换{old_title}阶，为三十阶之{ordinal}阶",
            quote,
            f"据原文建立{new_title}大观二年新增节点。",
            category="文臣京朝官寄禄官三十阶",
            officer="寄禄官",
            grade=grade,
            sort_order=11080627,
        )
        relation(
            writer, entry_id, old_tp, new_tp, "前后演变", quote,
            f"大观二年新增{new_title}，换{old_title}阶。",
        )
        stipend_member(
            writer, entry_id, "北宋徽宗大观二年六月二十七日",
            new_tp, quote, new_title, 11080627,
        )
        writer.commit()


def extract_southern_left_right():
    specs = {
        139: ("宣奉大夫", "左宣奉大夫", "右宣奉大夫", "宣奉大夫于南宋绍兴元年十二月分左、右", "淳熙元年三月罢分左、右"),
        141: ("正奉大夫", "左正奉大夫", "右正奉大夫", "正奉大夫于南宋绍兴元年十二月分左、右", "孝宗淳熙元年三月罢分左、右"),
    }
    for entry_id, (base, left, right, split_needle, merge_needle) in specs.items():
        writer = W(entry_id)
        split_quote = Q(entry_id, split_needle)
        add_split(
            writer, entry_id, base, left, right,
            "南宋高宗绍兴元年十二月", split_quote, 11311200,
        )
        merge_quote = Q(entry_id, merge_needle)
        add_merge(
            writer, entry_id, base, left, right,
            "南宋孝宗淳熙元年三月", merge_quote, 11740300,
        )
        writer.commit()


def main():
    expected = [
        "太子太傅", "太子太师", "太保", "太傅", "太尉", "太师",
        "元丰以后寄禄官", "开府仪同三司", "特进", "金紫光禄大夫",
        "左、右金紫光禄大夫", "银青光禄大夫", "左、右银青光禄大夫",
        "光禄大夫", "左、右光禄大夫", "三光禄", "宣奉大夫",
        "左、右宣奉大夫", "正奉大夫", "左、右正奉大夫",
    ]
    assert [F[i]["title"] for i in range(122, 142)] == expected
    extract_old_ranks()
    extract_general_system()
    extract_yuanfeng_ranks()
    extract_left_right_entries()
    extract_three_guanglu()
    extract_new_daguan_ranks()
    extract_southern_left_right()


if __name__ == "__main__":
    main()
