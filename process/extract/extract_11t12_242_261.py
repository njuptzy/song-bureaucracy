#!/usr/bin/env python3
"""提取 chapter11t12 第242-261条：正任末三阶、遥郡官与横行武阶。"""

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


F = {entry_id: load(entry_id) for entry_id in range(242, 262)}
helpers.F = F
helpers.ENTRY_DB = ENTRY_DB
helpers.NEW_SORT = {}

W = helpers.W
Q = helpers.Q
state = helpers.state
relation = helpers.relation


def field_quote(entry_id, field, needle):
    value = F[entry_id]["fields"].get(field, "")
    assert needle in value, (entry_id, field, needle)
    return needle


def cite_existing(writer, entry_id, title, time, quote, decision):
    row = writer.conn.execute(
        "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id "
        "WHERE e.title=? AND e.type='官职' AND t.time=? ORDER BY t.id LIMIT 1",
        (title, time),
    ).fetchone()
    assert row, (title, time)
    helpers.cite(writer, "Timepoints", row[0], entry_id, quote, decision)
    return row[0]


def add_group_members(
    writer,
    entry_id,
    group_title,
    time,
    event,
    quote,
    members,
    sort_order,
    *,
    category,
    group_officer="职官总名",
    member_officer="武阶",
):
    _, group_tp = state(
        writer, entry_id, group_title, time, event, quote,
        f"据原文建立或复用{group_title}统称节点。",
        category=category, officer=group_officer, sort_order=sort_order,
    )
    member_tps = {}
    for title in members:
        _, member_tp = state(
            writer, entry_id, title, time, f"属于{group_title}所指范围", quote,
            f"据原文明列建立或复用{title}实例节点。",
            category=category, officer=member_officer, sort_order=sort_order,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示{group_title}包括{title}。",
        )
        member_tps[title] = member_tp
    return group_tp, member_tps


def add_evolution(
    writer,
    entry_id,
    old_title,
    new_title,
    time,
    quote,
    sort_order,
    *,
    category,
    old_event=None,
    new_event=None,
):
    _, old_tp = state(
        writer, entry_id, old_title, time,
        old_event or f"改名或升为{new_title}", quote,
        f"据原文建立或复用{old_title}演变节点。",
        category=category, officer="武阶", sort_order=sort_order,
    )
    _, new_tp = state(
        writer, entry_id, new_title, time,
        new_event or f"由{old_title}改名或升转", quote,
        f"据原文建立或复用{new_title}承接节点。",
        category=category, officer="武阶", sort_order=sort_order,
    )
    relation(
        writer, entry_id, old_tp, new_tp, "前后演变", quote,
        f"原文明示{old_title}在{time}演变为{new_title}。",
    )
    return old_tp, new_tp


def repair_domestic_guest_title():
    """用 p641 正式词头合并旧 OCR 误名“内容省使”，不丢既有关系证据。"""
    entry_id = 257
    quote = Q(entry_id, "横行武阶名。")
    writer = W(entry_id)
    wrong = writer.find_entity("内容省使", "官职")
    correct = writer.find_entity("内客省使", "官职")
    if wrong and correct and wrong != correct:
        moved = writer.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id", (correct,)
        ).fetchall()
        for (timepoint_id,) in moved:
            writer.conn.execute(
                "UPDATE Timepoints SET entity_id=? WHERE id=?", (wrong, timepoint_id)
            )
            writer._br(
                "Timepoints", timepoint_id,
                "据 p641 正式词头，将内客省使既有节点并入旧 OCR 误名实体后统一更名。",
            )
        writer.conn.execute(
            "UPDATE BuildRecords SET target_id=? "
            "WHERE target_table='Entities' AND target_id=?",
            (wrong, correct),
        )
        writer.conn.execute("DELETE FROM Entities WHERE id=?", (correct,))
        writer.conn.execute(
            "UPDATE Entities SET title='内客省使' WHERE id=?", (wrong,)
        )
        writer._br(
            "Entities", wrong,
            "原书 p641 正式词头为内客省使；合并旧 OCR 误名内容省使与既有同名实体。",
        )
        correct = wrong
    elif wrong and not correct:
        writer.conn.execute(
            "UPDATE Entities SET title='内客省使' WHERE id=?", (wrong,)
        )
        writer._br(
            "Entities", wrong,
            "原书 p641 正式词头为内客省使，校正旧 OCR 误名内容省使。",
        )
        correct = wrong
    assert correct

    replacements = (("Timepoints", "event", "内容省使", "内客省使"),)
    for table, column, old, new in replacements:
        rows = writer.conn.execute(
            f"SELECT id,{column} FROM {table} WHERE {column} LIKE ?", (f"%{old}%",)
        ).fetchall()
        for target_id, value in rows:
            writer.conn.execute(
                f"UPDATE {table} SET {column}=? WHERE id=?",
                (value.replace(old, new), target_id),
            )
            writer._br(table, target_id, f"随正式词头校正{column}中的旧 OCR 误名。")

    rows = writer.conn.execute(
        "SELECT t.id,COALESCE(n.sort_order,999999999) sort_order "
        "FROM Timepoints t LEFT JOIN NormalizedTimes n ON n.timepoint_id=t.id "
        "WHERE t.entity_id=? ORDER BY sort_order,t.id",
        (correct,),
    ).fetchall()
    for index, (timepoint_id, _) in enumerate(rows):
        writer.relink(
            timepoint_id,
            "合并同一官名实体后按既有标准化时间重建完整互反链。",
            prev_id=rows[index - 1][0] if index else None,
            succ_id=rows[index + 1][0] if index + 1 < len(rows) else None,
        )
    helpers.cite(
        writer, "Timepoints", rows[0][0], entry_id, quote,
        "以正式词头补证内客省使实体并完成旧 OCR 误名合并。",
    )
    writer.commit()


def extract_regular_last_ranks():
    entry_id = 242
    writer = W(entry_id)
    quote = Q(entry_id, "凡除观察使，皆带州名。")
    add_group_members(
        writer, entry_id, "观察使", "北宋", "除授观察使时皆带州名", quote,
        ("某州观察使",), 96000000,
        category="正任武阶系衔", group_officer="正任武阶", member_officer="官衔",
    )
    writer.commit()

    entry_id = 243
    writer = W(entry_id)
    intro = Q(entry_id, "正任武阶名。")
    state(
        writer, entry_id, "防御使", "宋代", "作为正任武阶", intro,
        "据词条定义补证防御使宋代性质。",
        category="正任武阶", officer="正任武阶", sort_order=96000000,
    )
    origin = field_quote(entry_id, "职源与沿革", "唐武则天圣历元年（698），以夏州领防御使，是置防御使之始")
    state(
        writer, entry_id, "防御使", "唐武则天圣历元年", "始置防御使",
        origin, "建立防御使唐代职源节点。",
        category="前代职源", officer="武阶", sort_order=69800000,
    )
    grade = field_quote(entry_id, "品位", "元丰后，从五品")
    state(
        writer, entry_id, "防御使", "北宋神宗元丰改制后", "官品定为从五品",
        grade, "建立防御使元丰后官品节点。",
        category="正任武阶", officer="正任武阶", grade="从五品", sort_order=108000000,
    )
    writer.commit()

    entry_id = 244
    writer = W(entry_id)
    quote = Q(entry_id, "宋制，除防御使，必带防御州名。")
    add_group_members(
        writer, entry_id, "防御使", "宋代", "除授防御使时必带防御州名", quote,
        ("某州防御使",), 96000000,
        category="正任武阶系衔", group_officer="正任武阶", member_officer="官衔",
    )
    writer.commit()

    entry_id = 245
    writer = W(entry_id)
    intro = Q(entry_id, "正任武阶名。")
    state(
        writer, entry_id, "团练使", "宋代", "作为正任武阶", intro,
        "据词条定义补证团练使宋代性质。",
        category="正任武阶", officer="正任武阶", sort_order=96000000,
    )
    origin = field_quote(entry_id, "职源与沿革", "唐肃宗乾德元年（758）始置")
    state(
        writer, entry_id, "团练使", "唐肃宗乾元元年", "始置团练使",
        origin, "原文年号作乾德而括注 758；按对应纪年规范为唐乾元元年。",
        category="前代职源", officer="武阶", sort_order=75800000,
    )
    grade = field_quote(entry_id, "品位", "元丰后从五品")
    state(
        writer, entry_id, "团练使", "北宋神宗元丰改制后", "官品定为从五品",
        grade, "建立团练使元丰后官品节点。",
        category="正任武阶", officer="正任武阶", grade="从五品", sort_order=108000000,
    )
    writer.commit()

    entry_id = 246
    writer = W(entry_id)
    quote = Q(entry_id, "宋制，除团练使必曰“某州团练使”，团练州、军事州均可注授。")
    add_group_members(
        writer, entry_id, "团练使", "宋代", "除授团练使时带州名", quote,
        ("某州团练使",), 96000000,
        category="正任武阶系衔", group_officer="正任武阶", member_officer="官衔",
    )
    writer.commit()

    entry_id = 247
    writer = W(entry_id)
    intro = Q(entry_id, "正任武官阶。")
    state(
        writer, entry_id, "刺史", "宋代", "作为正任末阶", intro,
        "据词条定义补证刺史宋代正任末阶性质。",
        category="正任武阶末阶", officer="正任武阶", sort_order=96000000,
    )
    origin = field_quote(entry_id, "职源与沿革", "西汉武帝元封五年（前106）置部刺史")
    state(
        writer, entry_id, "刺史", "西汉武帝元封五年", "始置部刺史",
        origin, "建立刺史前代职源节点。",
        category="前代职源", officer="官职", sort_order=-10600000,
    )
    reform = field_quote(
        entry_id, "职源与沿革",
        "政和二年九月二十五日，诏节度使以下至刺史皆不带“使持节某州诸军事”衔",
    )
    state(
        writer, entry_id, "刺史", "北宋徽宗政和二年九月二十五日",
        "此后不再带使持节某州诸军事衔", reform,
        "建立刺史政和二年系衔变化节点。",
        category="正任武阶末阶", officer="正任武阶", sort_order=111201825,
    )
    grade = field_quote(entry_id, "品位", "元丰后从五品")
    state(
        writer, entry_id, "刺史", "北宋神宗元丰改制后", "官品定为从五品",
        grade, "建立刺史元丰后官品节点。",
        category="正任武阶末阶", officer="正任武阶", grade="从五品", sort_order=108000000,
    )
    writer.commit()

    entry_id = 248
    writer = W(entry_id)
    quote = Q(entry_id, "宋除刺史，必带军事州名。")
    add_group_members(
        writer, entry_id, "刺史", "宋代", "除授刺史时必带军事州名", quote,
        ("某州刺史",), 96000000,
        category="正任武阶系衔", group_officer="正任武阶", member_officer="官衔",
    )
    writer.commit()


REMOTE_MEMBERS = (
    "遥郡节度观察留后", "遥郡观察使", "遥郡防御使", "遥郡团练使", "遥郡刺史",
)


def extract_remote_ranks():
    entry_id = 249
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "节度观察留后（政和改承宣使）、观察使、防御使、团练使、刺史五阶兼领诸司使、副及横行使、副（政和后改为大夫、郎）等官阶者，为遥郡官",
    )
    add_group_members(
        writer, entry_id, "遥郡官", "宋代", "遥郡五阶的总称", quote,
        REMOTE_MEMBERS, 96000000, category="遥郡武阶",
    )
    writer.commit()

    entry_id = 250
    writer = W(entry_id)
    quote = Q(entry_id, "政和二年九月，随节度观察留后改名承宣使而称遥郡承宣使。")
    add_evolution(
        writer, entry_id, "遥郡节度观察留后", "遥郡承宣使",
        "北宋徽宗政和二年九月", quote, 111201800,
        category="遥郡武阶", old_event="改名为遥郡承宣使",
        new_event="由遥郡节度观察留后改名",
    )
    writer.commit()

    specs = (
        (251, "遥郡承宣使", "承宣使", "如落阶官，即升为正任承宣使。"),
        (252, "遥郡观察使", "观察使", "如落阶官，即升为正任观察使。"),
        (253, "遥郡防御使", "防御使", "落阶官即升为正任防御使。"),
        (254, "遥郡团练使", "团练使", "落阶官即升任正任团练使。"),
        (255, "遥郡刺史", "刺史", "落阶官即升为正任刺史。"),
    )
    for entry_id, old_title, new_title, needle in specs:
        writer = W(entry_id)
        quote = Q(entry_id, needle)
        add_evolution(
            writer, entry_id, old_title, new_title, "宋代落阶官时", quote, 96000001,
            category="遥郡转正任", old_event=f"落阶官，升为正任{new_title}",
            new_event=f"由{old_title}落阶官升任",
        )
        writer.commit()

    for entry_id, old_title, new_title, needle in (
        (253, "遥郡防御使", "遥郡观察使", "按常调，遥郡防御使转遥郡观察使。"),
        (254, "遥郡团练使", "遥郡防御使", "按常调，遥郡团练使转遥郡防御使"),
        (255, "遥郡刺史", "遥郡团练使", "依常调，遥郡刺史转遥郡团练使"),
    ):
        writer = W(entry_id)
        quote = Q(entry_id, needle)
        add_evolution(
            writer, entry_id, old_title, new_title, "宋代常调迁转时", quote, 96000002,
            category="遥郡常调迁转", old_event=f"按常调转{new_title}",
            new_event=f"按常调由{old_title}迁转",
        )
        writer.commit()


OLD_HORIZONTAL = (
    "内客省使", "客省使", "引进使", "四方馆使", "东上阁门使", "西上阁门使",
    "客省副使", "引进副使", "东上阁门副使", "西上阁门副使",
)
REFORM_TWELVE = (
    "通侍大夫", "正侍大夫", "中侍大夫", "中亮大夫", "中卫大夫", "拱卫大夫",
    "左武大夫", "右武大夫", "中亮郎", "中卫郎", "左武郎", "右武郎",
)
FINAL_DAFU = (
    "通侍大夫", "正侍大夫", "宣正大夫", "履正大夫", "协忠大夫", "中侍大夫",
    "中亮大夫", "中卫大夫", "翊卫大夫", "亲卫大夫", "拱卫大夫", "左武大夫", "右武大夫",
)
FINAL_LANG = (
    "正侍郎", "宣正郎", "履正郎", "协忠郎", "中侍郎", "中亮郎",
    "中卫郎", "翊卫郎", "亲卫郎", "拱卫郎", "左武郎", "右武郎",
)


def extract_horizontal_group():
    entry_id = 256
    writer = W(entry_id)
    old_quote = Q(
        entry_id,
        "北宋前期，横行阶包括：内客省使、客省使、引进使、四方馆使、东上阁门使、西上阁门使、客省副使、引进副使、东上阁门副使、西上阁门副使",
    )
    add_group_members(
        writer, entry_id, "横行", "北宋前期", "北宋前期横行十阶的总称",
        old_quote, OLD_HORIZONTAL, 96000000, category="横行武阶",
    )
    reform_quote = Q(
        entry_id,
        "徽宗政和二年九月二十五日，改武选官名，横行阶易为十二阶：通侍大夫、正侍大夫、中侍大夫、中亮大夫、中卫大夫、拱卫大夫、左武大夫、右武大夫、中亮郎、中卫郎、左武郎、右武郎",
    )
    add_group_members(
        writer, entry_id, "横行", "北宋徽宗政和二年九月二十五日",
        "改武选官名后横行十二阶的总称", reform_quote, REFORM_TWELVE,
        111201825, category="横行武阶",
    )
    add_quote = Q(entry_id, "政和二年十一月五日，横行增拱卫郎阶，在左武郎之上")
    add_group_members(
        writer, entry_id, "横行", "北宋徽宗政和二年十一月五日",
        "增拱卫郎后的横行武阶", add_quote, ("拱卫郎",),
        111202205, category="横行武阶",
    )
    final_quote = Q(
        entry_id,
        "至此，横行大夫十三阶，“为要官”，即：通侍大夫、正侍大夫、宣正大夫、履正大夫、协忠大夫、中侍大夫、中亮大夫、中卫大夫、翊卫大夫、亲卫大夫、拱卫大夫、左武大夫、右武大夫。横行郎十二阶，即：正侍郎、宣正郎、履正郎、协忠郎、中侍郎、中亮郎、中卫郎、翊卫郎、亲卫郎、拱卫郎、左武郎、右武郎",
    )
    final_time = "北宋徽宗政和六年十一月三十日以后"
    horizontal_tp, horizontal_members = add_group_members(
        writer, entry_id, "横行", final_time, "政和六年增阶后的横行武阶范围",
        final_quote, FINAL_DAFU + FINAL_LANG, 111601130, category="横行武阶",
    )
    for group_title, members in (("横行大夫", FINAL_DAFU), ("横行郎", FINAL_LANG)):
        group_tp, _ = add_group_members(
            writer, entry_id, group_title, final_time, f"{group_title}的正式阶目总称",
            final_quote, members, 111601130, category="横行武阶分组",
        )
        relation(
            writer, entry_id, horizontal_tp, group_tp, "统称与实例", final_quote,
            f"原文明示{group_title}是横行武阶的分组。",
        )
        assert all(title in horizontal_members for title in members)
    writer.commit()


def extract_horizontal_entries():
    specs = (
        (257, "内客省使", "通侍大夫", "唐朝", "唐官", None, None,
         "政和二年九月二十五日，易阶名为通侍大夫"),
        (258, "客省使", "中亮大夫", "唐天祐元年四月", "唐天祐元年已见置", "从五品", "哲宗《元祐官品令》定为从五品",
         "政和二年九月二十五日，易阶名为中亮大夫"),
        (259, "引进使", "中卫大夫", "五代后梁", "五代后梁已置", "从五品", "《元祐官品令》从五品",
         "政和二年九月二十五日易阶名为中卫大夫"),
        (260, "四方馆使", "拱卫大夫", "北宋淳化四年", "北宋淳化四年始置", "正六品", "《元祐官品令》正六品",
         "政和二年九月二十五日，易阶名为拱卫大夫"),
        (261, "西上阁门使", "右武大夫", "五代后梁", "五代后梁有西上阁门使", "正六品", "《元祐令》正六品",
         "政和二年九月二十五日，易阶名为右武大夫"),
    )
    for (
        entry_id, old_title, new_title, origin_time, origin_needle,
        grade, grade_needle, reform_needle,
    ) in specs:
        writer = W(entry_id)
        origin_quote = Q(entry_id, origin_needle)
        if entry_id in (258, 260):
            cite_existing(
                writer, entry_id, old_title, origin_time, origin_quote,
                f"本条补证{old_title}{origin_time}已见或始置。",
            )
        else:
            state(
                writer, entry_id, old_title, origin_time, origin_needle,
                origin_quote, f"建立或复用{old_title}职源节点。",
                category="前代职源" if entry_id != 260 else "横行武阶",
                officer="武阶", sort_order={257: 80000000, 259: 90700000, 261: 90700000}.get(entry_id),
            )
        if grade:
            grade_quote = Q(entry_id, grade_needle)
            state(
                writer, entry_id, old_title, "北宋哲宗元祐官品令",
                f"官品定为{grade}", grade_quote,
                f"建立{old_title}元祐官品节点。",
                category="横行武阶", officer="武阶", grade=grade, sort_order=108600000,
            )
        reform_quote = Q(entry_id, reform_needle)
        add_evolution(
            writer, entry_id, old_title, new_title,
            "北宋徽宗政和二年九月二十五日", reform_quote, 111201825,
            category="横行武阶", old_event=f"武阶易为{new_title}",
            new_event=f"承接{old_title}武阶",
        )
        writer.commit()


def main():
    expected = [
        "某州观察使", "防御使", "某州防御使", "团练使", "某州团练使",
        "刺史", "某州刺史", "遥郡官", "遥郡节度观察留后", "遥郡承宣使",
        "遥郡观察使", "遥郡防御使", "遥郡团练使", "遥郡刺史", "横行",
        "内客省使", "客省使", "引进使", "四方馆使", "西上阁门使",
    ]
    assert [F[i]["title"] for i in range(242, 262)] == expected
    assert "内客省使 横行武阶名。" not in F[256]["fields"].get("别名", "")
    assert F[257]["text"].startswith("横行武阶名。唐官")
    repair_domestic_guest_title()
    extract_regular_last_ranks()
    extract_remote_ranks()
    extract_horizontal_group()
    extract_horizontal_entries()


if __name__ == "__main__":
    main()
