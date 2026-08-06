#!/usr/bin/env python3
"""提取 chapter11t12 第222-241条：正任官、节度使及观察使。"""

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


F = {entry_id: load(entry_id) for entry_id in range(222, 242)}
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


def group_members(
    entry_id,
    group_title,
    group_time,
    group_event,
    quote,
    members,
    sort_order,
    *,
    category,
    member_officer="武阶",
):
    writer = W(entry_id)
    _, group_tp = state(
        writer, entry_id, group_title, group_time, group_event, quote,
        f"据原文建立或复用{group_title}统称节点。",
        category=category, officer="职官总名", sort_order=sort_order,
    )
    for title, time, member_sort in members:
        _, member_tp = state(
            writer, entry_id, title, time, f"属于{group_title}所指范围",
            quote, f"据原文建立或复用{title}作为{group_title}实例的节点。",
            category=category, officer=member_officer, sort_order=member_sort,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示{group_title}包括{title}。",
        )
    writer.commit()


def exact_evolution(
    writer,
    entry_id,
    old_title,
    new_title,
    time,
    quote,
    sort_order,
    *,
    category="正任武阶",
    grade=None,
):
    _, old_tp = state(
        writer, entry_id, old_title, time, f"改名为{new_title}", quote,
        f"据原文建立或复用{old_title}改名终结节点。",
        category=category, officer="武阶", sort_order=sort_order,
    )
    _, new_tp = state(
        writer, entry_id, new_title, time, f"由{old_title}改名", quote,
        f"据原文建立或复用{new_title}启用节点。",
        category=category, officer="武阶", grade=grade, sort_order=sort_order,
    )
    relation(
        writer, entry_id, old_tp, new_tp, "前后演变", quote,
        f"原文明示{old_title}在{time}改名为{new_title}。",
    )
    return old_tp, new_tp


def extract_regular_commissions():
    entry_id = 222
    quote = Q(
        entry_id,
        "正任阶官名。节度使、节度观察留后（政和七年改为承宣使）、观察使、防御使、团练使、刺史为正任。",
    )
    group_members(
        entry_id, "正任官", "宋代", "宋代正任武阶六阶的统称", quote,
        [(title, "宋代", 96000000) for title in (
            "节度使", "节度观察留后", "观察使", "防御使", "团练使", "刺史",
        )],
        96000000, category="正任武阶六阶",
    )


def extract_military_governor():
    entry_id = 223
    writer = W(entry_id)
    general_quote = Q(entry_id, "正任武阶名、加官名。")
    state(
        writer, entry_id, "节度使", "宋代", "作为正任最高武阶及加官",
        general_quote, "据词条定义建立或复用节度使宋代性质节点。",
        category="正任武阶最高阶", officer="正任武阶、加官", sort_order=96000000,
    )
    origin_quote = field_quote(
        entry_id, "职源与沿革",
        "景云元年（710）始设节度使官",
    )
    state(
        writer, entry_id, "节度使", "唐景云元年", "始正式设置节度使官",
        origin_quote, "建立节度使唐代正式设置节点。",
        category="前代职源", officer="武阶", sort_order=71000000,
    )
    song_quote = field_quote(
        entry_id, "职能",
        "宋初削藩镇之权，节度使不必赴镇，无职事，但为武官之秩，属正任最高一阶",
    )
    state(
        writer, entry_id, "节度使", "宋初",
        "削藩镇之权，不必赴镇，无职事，列正任最高一阶",
        song_quote, "建立节度使宋初转为无职事武阶的节点。",
        category="正任武阶最高阶", officer="正任武阶", sort_order=96000000,
    )
    yuanfeng_quote = field_quote(
        entry_id, "品位", "北宋元丰改制后为正三品，南宋绍兴后为从二品",
    )
    state(
        writer, entry_id, "节度使", "北宋神宗元丰改制后", "官品定为正三品",
        yuanfeng_quote, "建立节度使元丰后官品节点。",
        category="正任武阶最高阶", officer="正任武阶", grade="正三品",
        sort_order=108000000,
    )
    state(
        writer, entry_id, "节度使", "南宋高宗绍兴以后", "官品改为从二品",
        yuanfeng_quote, "建立节度使绍兴后官品节点。",
        category="正任武阶最高阶", officer="正任武阶", grade="从二品",
        sort_order=116200000,
    )
    writer.commit()


def extract_old_full_style():
    entry_id = 224
    writer = W(entry_id)
    old_title = "使持节某州诸军事、某州刺史、充某军节度、某州管内观察处置等使"
    old_quote = Q(
        entry_id,
        "官衔名。宋沿唐旧制，在政和二年前，凡除节度使必冠此衔。",
    )
    state(
        writer, entry_id, old_title, "北宋徽宗政和二年九月二十五日以前",
        "节度使依唐旧制所冠完整官衔", old_quote,
        "建立政和二年前节度使完整官衔节点。",
        category="节度使系衔", officer="官衔", sort_order=111201825,
    )
    reform_quote = Q(
        entry_id,
        "徽宗政和二年九月二十五日，诏节度使以下不带“持节”等，只称“某军节度使”之类",
    )
    exact_evolution(
        writer, entry_id, old_title, "某军节度使",
        "北宋徽宗政和二年九月二十五日", reform_quote, 111201825,
        category="节度使系衔",
    )
    writer.commit()


def extract_three_seals_evidence():
    entry_id = 225
    writer = W(entry_id)
    time = "北宋徽宗政和二年九月二十五日以前"
    sort_order = 111201825
    specs = (
        (
            "节度使",
            "节度使印，归节度使",
            "节度州三印制度中节度使印归节度使",
        ),
        (
            "观察使",
            "观察使印，归长吏（知州或判州）",
            "节度州三印制度中观察使印归长吏",
        ),
        (
            "录事参军",
            "州印，昼付录事参军掌用、暮归长吏",
            "节度州州印白昼由录事参军掌用",
        ),
        (
            "知州",
            "带有节度使衔之知州上奏章，则用节度使，不用观察使印",
            "带节度使衔上奏时使用节度使印",
        ),
    )
    for title, needle, event in specs:
        quote = Q(entry_id, needle)
        state(
            writer, entry_id, title, time, event, quote,
            f"据节度州三印条为{title}补充政和前用印制度节点。",
            category="节度州三印制度", officer="官职", sort_order=sort_order,
        )
    writer.commit()


def add_governor_variant(entry_id, title, time, event, quote, sort_order):
    writer = W(entry_id)
    _, group_tp = state(
        writer, entry_id, "节度使", time, "节度使系衔范围", quote,
        "建立或复用节度使总称语境节点。",
        category="节度使系衔", officer="正任武阶", sort_order=sort_order,
    )
    _, variant_tp = state(
        writer, entry_id, title, time, event, quote,
        f"据原文建立或复用{title}系衔节点。",
        category="节度使系衔", officer="官衔", sort_order=sort_order,
    )
    relation(
        writer, entry_id, group_tp, variant_tp, "统称与实例", quote,
        f"原文明示{title}是节度使的具体系衔形式。",
    )
    writer.commit()


def extract_ungranted_command_names():
    specs = (
        (226, "河阳三城节度使", "宋代", "孟州未赐军额而冠河阳三城之名", 96000000),
        (227, "山南东道节度使", "北宋", "襄州未赐军额而径称山南东道节度", 96000000),
        (228, "山南西道节度使", "北宋", "兴元府未赐军额而沿称山南西道节度使", 96000000),
        (231, "荆南节度使", "宋代", "江陵府未赐军额而沿称荆南节度", 96000000),
        (232, "河东节度使", "宋代", "太原府未赐军额而沿称河东节度", 96000000),
        (233, "淮南节度使", "宋代", "扬州未赐军额而称淮南节度", 96000000),
    )
    for entry_id, title, time, event, sort_order in specs:
        quote = F[entry_id]["text"]
        assert quote.startswith("未赐军额的节镇使名")
        add_governor_variant(entry_id, title, time, event, quote, sort_order)

    entry_id = 229
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "宋乾德四年赐“静戎军”、太平兴国三年改赐“安静军”。端拱二年复唐旧称，不用军额",
    )
    state(
        writer, entry_id, "剑南东川节度", "北宋太宗端拱二年",
        "复唐旧称，不用军额", quote,
        "建立剑南东川节度复旧称节点。",
        category="未赐军额节度使系衔", officer="官衔", sort_order=98900000,
    )
    _, group_tp = state(
        writer, entry_id, "节度使", "北宋太宗端拱二年", "节度使系衔范围",
        quote, "建立或复用节度使总称语境节点。",
        category="节度使系衔", officer="正任武阶", sort_order=98900000,
    )
    variant_tp = writer.conn.execute(
        "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id "
        "WHERE e.title='剑南东川节度' AND t.time='北宋太宗端拱二年'"
    ).fetchone()[0]
    relation(
        writer, entry_id, group_tp, variant_tp, "统称与实例", quote,
        "剑南东川节度是未赐军额的节度使系衔。",
    )
    writer.commit()

    entry_id = 230
    writer = W(entry_id)
    changes = (
        ("北宋太宗太平兴国六年", "降为益州并罢节度", 98100000),
        ("北宋太宗端拱元年", "复为成都府、剑南西川节度", 98800000),
        ("北宋太宗淳化五年", "再降益州并罢节度", 99400000),
        ("北宋仁宗嘉祐四年", "复升成都府", 105900000),
        ("北宋仁宗嘉祐六年", "复为剑南西川节度，未赐军额", 106100000),
    )
    quote = F[entry_id]["text"]
    for time, event, sort_order in changes:
        state(
            writer, entry_id, "剑南西川节度", time, event, quote,
            f"据原文建立剑南西川节度{time}制度变化节点。",
            category="未赐军额节度使系衔", officer="官衔", sort_order=sort_order,
        )
    _, group_tp = state(
        writer, entry_id, "节度使", "北宋仁宗嘉祐六年", "节度使系衔范围",
        quote, "建立或复用节度使总称语境节点。",
        category="节度使系衔", officer="正任武阶", sort_order=106100000,
    )
    variant_tp = writer.conn.execute(
        "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id "
        "WHERE e.title='剑南西川节度' AND t.time='北宋仁宗嘉祐六年'"
    ).fetchone()[0]
    relation(
        writer, entry_id, group_tp, variant_tp, "统称与实例", quote,
        "剑南西川节度是未赐军额的节度使系衔。",
    )
    writer.commit()


def extract_named_and_multiple_commands():
    entry_id = 234
    quote = Q(
        entry_id,
        "宋代节度使，虽不赴镇治事，仍冠以某节度州军额名。",
    )
    add_governor_variant(
        entry_id, "某军节度使", "宋代",
        "节度使冠以所领节度州军额名", quote, 96000000,
    )

    for entry_id, title, time, event, sort_order in (
        (235, "两镇", "宋代", "同时除授两处节度使的称谓", 96000000),
        (236, "三镇", "南宋高宗绍兴初", "同时除授三处节度使，通常不超过三镇", 113100000),
    ):
        writer = W(entry_id)
        quote = F[entry_id]["text"]
        _, group_tp = state(
            writer, entry_id, title, time, event, quote,
            f"据原文建立{title}称谓节点。",
            category="节度使兼镇称谓", officer="职官总名", sort_order=sort_order,
        )
        _, member_tp = state(
            writer, entry_id, "节度使", time, f"作为{title}所指除授对象", quote,
            f"建立或复用节度使作为{title}实例的节点。",
            category="节度使兼镇称谓", officer="正任武阶", sort_order=sort_order,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示{title}指同时除授相应数量的节度使。",
        )
        writer.commit()


def extract_lieutenant_and_commissioner():
    entry_id = 237
    writer = W(entry_id)
    origin_quote = field_quote(
        entry_id, "职源与沿革",
        "唐开元十六年（738）之后，节度使入朝或遥领不临镇，乃辟亲信留主后务，称留后",
    )
    state(
        writer, entry_id, "节度观察留后", "唐开元十六年以后",
        "节度使入朝或遥领时以亲信留主后务，形成留后称谓",
        origin_quote, "建立节度观察留后前代职源节点。",
        category="前代职源", officer="武阶", sort_order=73800000,
    )
    song_quote = field_quote(
        entry_id, "职源与沿革",
        "北宋沿唐、五代之旧名以节度观察留后为一正任官阶。",
    )
    state(
        writer, entry_id, "节度观察留后", "北宋",
        "沿唐、五代旧名列为正任官阶", song_quote,
        "建立节度观察留后北宋正任武阶节点。",
        category="正任武阶", officer="正任武阶", sort_order=96000000,
    )
    grade_quote = field_quote(entry_id, "官品", "元丰后正四品")
    state(
        writer, entry_id, "节度观察留后", "北宋神宗元丰改制后",
        "官品定为正四品", grade_quote,
        "建立节度观察留后元丰后官品节点。",
        category="正任武阶", officer="正任武阶", grade="正四品",
        sort_order=108000000,
    )
    reform_quote = field_quote(
        entry_id, "职源与沿革",
        "徽宗政和七年六月十七日，改节度观察留后为承宣使",
    )
    _, new_tp = exact_evolution(
        writer, entry_id, "节度观察留后", "承宣使",
        "北宋徽宗政和七年六月十七日", reform_quote, 111701217,
        grade="正四品",
    )
    _, group_tp = state(
        writer, entry_id, "正任官", "北宋徽宗政和七年六月十七日",
        "承宣使承接节度观察留后的正任阶位", reform_quote,
        "建立或复用正任官政和七年制度节点。",
        category="正任武阶六阶", officer="职官总名", sort_order=111701217,
    )
    relation(
        writer, entry_id, group_tp, new_tp, "统称与实例", reform_quote,
        "承宣使改名后仍属正任官序列。",
    )
    writer.commit()

    entry_id = 238
    quote = F[entry_id]["text"]
    add_governor_lieutenant_variant(
        entry_id, "节度观察留后", "某军节度观察留后", "北宋",
        "除授时冠以所领某州军额名", quote, 96000000,
    )

    entry_id = 239
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "北宋徽宗政和七年六月十七日，由节度观察留后改名",
    )
    exact_evolution(
        writer, entry_id, "节度观察留后", "承宣使",
        "北宋徽宗政和七年六月十七日", quote, 111701217,
        grade="正四品",
    )
    writer.commit()

    entry_id = 240
    quote = F[entry_id]["text"]
    add_governor_lieutenant_variant(
        entry_id, "承宣使", "某军承宣使", "北宋徽宗政和七年六月十七日以后",
        "承宣使除授时冠以所领某州军额名", quote, 111701217,
    )


def add_governor_lieutenant_variant(
    entry_id, group_title, variant_title, time, event, quote, sort_order
):
    writer = W(entry_id)
    _, group_tp = state(
        writer, entry_id, group_title, time, f"{group_title}系衔范围", quote,
        f"建立或复用{group_title}总称语境节点。",
        category=f"{group_title}系衔", officer="正任武阶", sort_order=sort_order,
    )
    _, variant_tp = state(
        writer, entry_id, variant_title, time, event, quote,
        f"据原文建立{variant_title}系衔节点。",
        category=f"{group_title}系衔", officer="官衔", sort_order=sort_order,
    )
    relation(
        writer, entry_id, group_tp, variant_tp, "统称与实例", quote,
        f"原文明示{variant_title}是{group_title}的具体系衔形式。",
    )
    writer.commit()


def extract_observation_commissioner():
    entry_id = 241
    writer = W(entry_id)
    intro = Q(entry_id, "正任武阶名。")
    state(
        writer, entry_id, "观察使", "宋代", "作为正任武阶",
        intro, "据词条定义建立或复用观察使宋代性质节点。",
        category="正任武阶", officer="正任武阶", sort_order=96000000,
    )
    origin_quote = field_quote(
        entry_id, "职源与沿革",
        "唐肃宗至德元年（756）置东畿观察使",
    )
    state(
        writer, entry_id, "观察使", "唐肃宗至德元年", "始置东畿观察使",
        origin_quote, "建立观察使唐代职源节点。",
        category="前代职源", officer="武阶", sort_order=75600000,
    )
    concurrent_quote = field_quote(
        entry_id, "职源与沿革",
        "大中祥符七年三月十六日，诏依唐故事，观察使兼本州刺史",
    )
    state(
        writer, entry_id, "观察使", "北宋真宗大中祥符七年三月十六日",
        "依唐故事兼本州刺史", concurrent_quote,
        "建立观察使兼本州刺史节点。",
        category="正任武阶", officer="正任武阶", sort_order=101400616,
    )
    grade_quote = field_quote(
        entry_id, "品位", "元丰后正五品",
    )
    state(
        writer, entry_id, "观察使", "北宋神宗元丰改制后", "官品定为正五品",
        grade_quote, "建立观察使元丰后官品节点。",
        category="正任武阶", officer="正任武阶", grade="正五品",
        sort_order=108000000,
    )
    reform_quote = field_quote(
        entry_id, "职源与沿革",
        "政和二年九月二十五日后，不复带“持节”",
    )
    state(
        writer, entry_id, "观察使", "北宋徽宗政和二年九月二十五日",
        "此后不再带使持节官衔", reform_quote,
        "建立观察使政和二年系衔变化节点。",
        category="正任武阶", officer="正任武阶", sort_order=111201825,
    )
    writer.commit()


def main():
    expected = [
        "正任官", "节度使",
        "使持节某州诸军事、某州刺史、充某军节度、某州管内观察处置等使",
        "节度州三印", "河阳三城节度使", "山南东道节度使",
        "山南西道节度使", "剑南东川节度", "剑南西川节度", "荆南节度使",
        "河东节度使", "淮南节度使", "某军节度使", "两镇", "三镇",
        "节度观察留后", "某军节度观察留后", "承宣使", "某军承宣使", "观察使",
    ]
    assert [F[i]["title"] for i in range(222, 242)] == expected
    assert "编制" in F[237]["fields"] and "编制" in F[241]["fields"]
    extract_regular_commissions()
    extract_military_governor()
    extract_old_full_style()
    extract_three_seals_evidence()
    extract_ungranted_command_names()
    extract_named_and_multiple_commands()
    extract_lieutenant_and_commissioner()
    extract_observation_commissioner()


if __name__ == "__main__":
    main()
