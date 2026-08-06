#!/usr/bin/env python3
"""提取 chapter11t12 第382-401条：政和新武阶第二十二至三十六阶。"""

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
    "extract_11t12_322_341_helpers", HERE / "extract_11t12_322_341.py"
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


F = {entry_id: load(entry_id) for entry_id in range(382, 402)}
base.F = F
base.base.F = F
base.base.helpers.F = F
base.ENTRY_DB = ENTRY_DB
base.base.ENTRY_DB = ENTRY_DB
base.base.helpers.ENTRY_DB = ENTRY_DB
base.base.helpers.NEW_SORT = {}

W = base.W
Q = base.Q
state = base.state
add_evolution = base.add_evolution
add_grade = base.add_grade
group_members = base.group_members


CN_ORDINAL = {
    17: "十七", 18: "十八", 19: "十九", 20: "二十", 21: "二十一",
    22: "二十二", 23: "二十三", 24: "二十四", 25: "二十五",
    26: "二十六", 27: "二十七", 28: "二十八", 29: "二十九",
    30: "三十", 31: "三十一", 32: "三十二", 33: "三十三",
    34: "三十四", 35: "三十五", 36: "三十六",
}


REGULAR_DAFU = {
    382: ("武显大夫", ("左藏库使", "东作坊使", "西作坊使"), 17, "正七品"),
    383: ("武节大夫", ("庄宅使", "六宅使", "文思使"), 18, "正七品"),
    384: ("武略大夫", ("内园使", "洛苑使", "如京使", "崇仪使"), 19, "正七品"),
    385: ("武经大夫", ("西京左藏库使",), 20, "正七品"),
    386: ("武义大夫", ("西京作坊使", "东染院使", "西染院使", "礼宾使"), 21, "正七品"),
    387: ("武翼大夫", ("供备库使",), 22, "正七品"),
}


def regular_origin_quote(entry_id):
    text = F[entry_id]["text"]
    start = text.index("北宋政和二年九月二十五日")
    end = text.index("。", start) + 1
    return text[start:end]


def add_rank_state(writer, entry_id, title, ordinal, grade, rank_quote, grade_quote):
    state(
        writer, entry_id, title, "南宋高宗绍兴厘定",
        f"列入品武阶五十二阶之第{CN_ORDINAL[ordinal]}阶", rank_quote,
        f"记录{title}绍兴厘定序位。", category="绍兴武阶",
        officer="武阶", sort_order=113100000,
    )
    add_grade(
        writer, entry_id, title, "南宋高宗绍兴厘定", grade,
        grade_quote, 113100000, "绍兴武阶",
    )


def extract_regular_dafu():
    for entry_id, (title, old_titles, ordinal, grade) in REGULAR_DAFU.items():
        writer = W(entry_id)
        intro = Q(entry_id, "武阶名。属诸司正使八阶列。")
        group_members(
            writer, entry_id, "诸司正使",
            "北宋徽宗政和二年九月二十五日",
            "改武选官名后合并为八阶大夫", (title,), intro,
            111201825, "诸司正使武阶",
        )
        origin = regular_origin_quote(entry_id)
        for old_title in old_titles:
            add_evolution(
                writer, entry_id, old_title, title,
                "北宋徽宗政和二年九月二十五日", origin, 111201825,
                category="诸司正使武阶", old_event=f"阶名改为{title}",
                new_event=f"承接{old_title}武阶",
            )
        ordinal_text = CN_ORDINAL[ordinal]
        if entry_id in (382, 383):
            rank_quote = Q(entry_id, f"绍兴厘定入品武阶之第{ordinal_text}阶")
        else:
            rank_quote = Q(entry_id, f"绍兴厘定入品武阶五十二阶之第{ordinal_text}阶")
        if entry_id == 383:
            grade_quote = Q(entry_id, "资料出处参“武功大夫”条。")
        else:
            grade_quote = Q(entry_id, grade)
        add_rank_state(
            writer, entry_id, title, ordinal, grade, rank_quote, grade_quote
        )
        writer.commit()


HENGXING_LANG = {
    388: ("正侍郎", (), "北宋徽宗政和六年十一月三十日", 111602230, 23),
    389: ("宣正郎", (), "北宋徽宗政和六年十一月三十日", 111602230, 24),
    390: ("履正郎", (), "北宋徽宗政和六年十一月三十日", 111602230, 25),
    391: ("协忠郎", (), "北宋徽宗政和六年十一月三十日", 111602230, 26),
    392: ("中侍郎", (), "北宋徽宗政和六年十一月三十日", 111602230, 27),
    393: ("中亮郎", ("客省副使",), "北宋徽宗政和二年九月二十五日", 111201825, 28),
    394: ("中卫郎", ("引进副使",), "北宋徽宗政和二年九月二十五日", 111201825, 29),
    395: ("翊卫郎", (), "北宋徽宗政和六年十一月三十日", 111602230, 30),
    396: ("亲卫郎", (), "北宋徽宗政和六年十一月三十日", 111602230, 31),
    397: ("拱卫郎", (), "北宋徽宗政和二年十一月五日", 111202205, 32),
    398: ("左武郎", ("东上阁门副使",), "北宋徽宗政和二年九月二十五日", 111201825, 33),
    399: ("右武郎", ("西上阁门副使",), "北宋徽宗政和二年九月二十五日", 111201825, 34),
}


def hengxing_origin_quote(entry_id, old_titles):
    if not old_titles:
        if entry_id == 397:
            return Q(entry_id, "北宋政和二年十一月五日增置")
        return Q(entry_id, "政和六年十一月三十日创置")
    text = F[entry_id]["text"]
    start = text.index("北宋政和二年九月二十五日")
    end = text.index("。", start) + 1
    return text[start:end]


def extract_hengxing_lang():
    for entry_id, spec in HENGXING_LANG.items():
        title, old_titles, origin_time, origin_order, ordinal = spec
        writer = W(entry_id)
        intro = Q(entry_id, "武阶名。属横行副使十二阶列。")
        group_members(
            writer, entry_id, "横行副使",
            "北宋徽宗政和六年十一月三十日以后",
            "政和六年增阶后横行副使十二阶", (title,), intro,
            111602230, "横行武阶",
        )
        origin = hengxing_origin_quote(entry_id, old_titles)
        if old_titles:
            for old_title in old_titles:
                add_evolution(
                    writer, entry_id, old_title, title, origin_time,
                    origin, origin_order, category="横行武阶",
                    old_event=f"阶名改为{title}", new_event=f"承接{old_title}武阶",
                )
        else:
            state(
                writer, entry_id, title, origin_time,
                "增置" if entry_id == 397 else "创置", origin,
                f"建立{title}{origin_time}节点。", category="横行武阶",
                officer="武阶", sort_order=origin_order,
            )
        rank_quote = Q(
            entry_id,
            f"绍兴厘定入品武阶五十二阶之第{CN_ORDINAL[ordinal]}阶",
        )
        grade_quote = Q(entry_id, "从七品")
        add_rank_state(
            writer, entry_id, title, ordinal, "从七品", rank_quote, grade_quote
        )
        if entry_id == 388:
            reorder = Q(
                entry_id,
                "绍兴厘正之，正侍郎至右武郎十二阶置于武功大夫至武翼大夫八阶之下",
            )
            state(
                writer, entry_id, "横行副使", "南宋高宗绍兴厘定",
                "十二郎阶移置诸司正使八大夫阶之下", reorder,
                "记录横行副使十二阶绍兴厘正后的整体序位。",
                category="绍兴武阶", officer="职官总名", sort_order=113100000,
            )
        writer.commit()


def extract_regular_lang():
    entry_id = 400
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属诸司副使八阶列。")
    group_members(
        writer, entry_id, "诸司副使",
        "北宋徽宗政和二年九月二十五日",
        "改武选官名后合并为八阶郎", ("武功郎",), intro,
        111201825, "诸司副使武阶",
    )
    origin = Q(entry_id, "北宋政和二年九月二十五日，由皇城副使改")
    add_evolution(
        writer, entry_id, "皇城副使", "武功郎",
        "北宋徽宗政和二年九月二十五日", origin, 111201825,
        category="诸司副使武阶", old_event="阶名改为武功郎",
        new_event="承接皇城副使武阶",
    )
    rank = Q(entry_id, "绍兴厘定入品武阶五十二阶之第三十五阶")
    grade = Q(entry_id, "从七品")
    add_rank_state(writer, entry_id, "武功郎", 35, "从七品", rank, grade)
    promotion = Q(entry_id, "磨勘常调转右武郎")
    add_evolution(
        writer, entry_id, "武功郎", "右武郎", "南宋磨勘常调制度",
        promotion, 114000000, category="武阶迁转",
        old_event="磨勘常调转右武郎", new_event="由武功郎磨勘迁转",
    )
    cycle = Q(entry_id, "磨勘常调，即每五年一转")
    state(
        writer, entry_id, "武功郎", "南宋", "磨勘常调每五年一转",
        cycle, "记录武功郎磨勘周期。", category="武阶迁转",
        officer="武阶", sort_order=112700000,
    )
    writer.commit()

    entry_id = 401
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属诸司副使八阶列。")
    group_members(
        writer, entry_id, "诸司副使",
        "北宋徽宗政和二年九月二十五日",
        "改武选官名后合并为八阶郎", ("武德郎",), intro,
        111201825, "诸司副使武阶",
    )
    origin = Q(entry_id, "北宋政和二年九月二十五日，由宫苑副使、左右骐骥副使、内藏库副使改")
    for old_title in ("宫苑副使", "左骐骥副使", "右骐骥副使", "内藏库副使"):
        add_evolution(
            writer, entry_id, old_title, "武德郎",
            "北宋徽宗政和二年九月二十五日", origin, 111201825,
            category="诸司副使武阶", old_event="阶名改为武德郎",
            new_event=f"承接{old_title}武阶",
        )
    rank = Q(entry_id, "绍兴厘定入品武阶五十二阶之第三十六阶")
    grade = Q(entry_id, "从七品")
    add_rank_state(writer, entry_id, "武德郎", 36, "从七品", rank, grade)
    writer.commit()


def main():
    expected = [
        "武显大夫", "武节大夫", "武略大夫", "武经大夫", "武义大夫",
        "武翼大夫", "正侍郎", "宣正郎", "履正郎", "协忠郎",
        "中侍郎", "中亮郎", "中卫郎", "翊卫郎", "亲卫郎",
        "拱卫郎", "左武郎", "右武郎", "武功郎", "武德郎",
    ]
    assert [F[i]["title"] for i in range(382, 402)] == expected
    extract_regular_dafu()
    extract_hengxing_lang()
    extract_regular_lang()


if __name__ == "__main__":
    main()
