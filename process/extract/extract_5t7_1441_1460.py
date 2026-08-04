#!/usr/bin/env python3
"""提取 chapter5t7 第1441-1460条：六统军、环卫官与金吾卫至武卫诸官。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1421_1440 as previous


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch5t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter5t7 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(1441, 1461)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
relation = base.relation
cite = base.cite
alias_note = base.alias_note

node = previous.node


TIME_HINTS = {
    **previous.TIME_HINTS,
    "春秋": -500,
    "战国": -350,
    "秦": -221,
    "秦汉": -100,
    "西晋武帝时": 270,
    "南朝梁": 502,
    "隋朝": 590,
    "隋开皇末": 600,
    "隋大业十三年": 617,
    "唐朝": 650,
    "唐初": 620,
    "唐武德五年": 622,
    "唐前期": 650.1,
    "唐龙朔元年": 661,
    "唐龙朔二年": 662,
    "唐德宗朝": 790,
    "五代": 930,
    "北宋初": 960,
    "北宋": 970,
    "北宋元丰新制": 1080,
    "北宋政和二年": 1112,
    "南宋高宗朝": 1140,
    "南宋乾道二年": 1166,
    "南宋淳熙四年二月": 1177.1,
    "南宋嘉泰元年": 1201,
    "宋代（六军仪仗司）": 1000.1,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    match = re.search(r"(-?\d{3,4})", time or "")
    if match:
        return (int(match.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


FAMILIES = (
    "金吾卫", "卫", "骁卫", "武卫", "屯卫", "领军卫", "监门卫", "千牛卫",
)
RANKS = ("上将军", "大将军", "将军", "中郎将", "郎将")
GENERIC_RANKS = {
    "上将军": "诸卫上将军",
    "大将军": "诸卫大将军",
    "将军": "诸卫将军",
    "中郎将": "环卫中郎将",
    "郎将": "环卫郎将",
}


def pair_title(family, rank):
    return f"左、右{family}{rank}"


def member_titles(family, rank):
    return f"左{family}{rank}", f"右{family}{rank}"


def system_members(w, touched, i, time, ranks, quotation, event):
    system = node(
        w, touched, i, "环卫官", "官职", time, event, quotation,
        "环卫官统称", f"建立或复用环卫官{time}体系节点。",
        officer="环卫官统称",
    )
    for rank in ranks:
        generic_title = GENERIC_RANKS[rank]
        generic = node(
            w, touched, i, generic_title, "官职", time,
            f"八卫左、右{rank}总称", quotation, "环卫官等级统称",
            f"建立{generic_title}{time}统称节点。", officer=f"{rank}统称",
        )
        relation(
            w, i, system, generic, "统称与实例", quotation,
            f"{generic_title}是环卫官五等之一。",
        )
        for family in FAMILIES:
            grouped_title = pair_title(family, rank)
            grouped = node(
                w, touched, i, grouped_title, "官职", time,
                f"{generic_title}所含左、右{family}{rank}", quotation,
                "环卫官左右合称", f"建立{grouped_title}{time}体系节点。",
                officer=rank,
            )
            relation(
                w, i, generic, grouped, "统称与实例", quotation,
                f"{grouped_title}是{generic_title}的实例组。",
            )
            for member_title in member_titles(family, rank):
                member = node(
                    w, touched, i, member_title, "官职", time,
                    f"{grouped_title}所指实例", quotation, "环卫官",
                    f"建立{member_title}{time}体系节点。", officer=rank,
                )
                relation(
                    w, i, grouped, member, "统称与实例", quotation,
                    f"{member_title}是{grouped_title}的左右实例。",
                )
    return system


def entry1441():
    i, main = 1441, F[1441]["text"]
    w, touched = W(i), set()
    group = node(
        w, touched, i, "六统军", "官职", "宋代（六军仪仗司）",
        "左、右龙武军、羽林军、神武军统军六职总称", main,
        "六军统军合称", "复用六统军正式统称并追加本条证据。",
        update_event=True, officer="统军合称",
    )
    for grouped_title in (
        "左、右龙武军统军", "左、右羽林军统军", "左、右神武军统军",
    ):
        grouped = node(
            w, touched, i, grouped_title, "官职", "宋代（六军仪仗司）",
            "六统军所指左右实例组", main, "六军统军合称",
            f"复用{grouped_title}。", officer="统军",
        )
        relation(w, i, group, grouped, "统称与实例", main,
                 f"{grouped_title}是六统军实例组。")
    for family in ("龙武军", "羽林军", "神武军"):
        for member_title in member_titles(family, "统军"):
            member = node(
                w, touched, i, member_title, "官职", "宋代（六军仪仗司）",
                "六统军所指具体实例", main, "六军统军",
                f"复用{member_title}。", officer="统军",
            )
            relation(w, i, group, member, "统称与实例", main,
                     f"{member_title}是六统军具体实例。")
    finish(w, touched, "补足六统军正式词头、三个左右实例组和六个具体实例。")


def entry1442():
    i, main, aliases = 1442, F[1442]["text"], field(1442, "简称与别名")
    w, touched = W(i), set()
    for time, event in (
        ("唐朝", "唐已置，领宿卫兵，如宋代三衙"),
        ("北宋初", "沿置而无职事，不统兵；设八卫左右上将军、大将军、将军四十八阶"),
        ("北宋元丰新制", "宗室依旧除授，外臣概不授与"),
        ("北宋政和二年", "武官制改革而环卫官四十八阶不改，因无职事不统兵"),
        ("南宋高宗朝", "除授不常"),
        ("南宋乾道二年", "复除环卫官，八卫备置中郎将、郎将，共八十阶"),
        ("南宋淳熙四年二月", "改定武臣兼领环卫官格式，并限制戚里与非战功人除授"),
        ("南宋嘉泰元年", "定编制十员"),
    ):
        node(
            w, touched, i, "环卫官", "官职", time, event, main,
            "环卫官统称", f"建立环卫官{time}制度节点。",
            update_event=True, officer="环卫官统称",
        )
    system_members(
        w, touched, i, "北宋初", RANKS[:3], main,
        "八卫左右上将军、大将军、将军四十八阶总称",
    )
    latest = system_members(
        w, touched, i, "南宋乾道二年", RANKS, main,
        "复除并备置五等八十阶环卫官",
    )
    cite(w, "Timepoints", latest, i, aliases, "保存环卫、卫官、环列、环尹等简称与别名。", "简称与别名")
    alias_note(w, i, latest, aliases, "简称与别名")
    finish(w, touched, "建立环卫官唐宋制度时间线及北宋四十八阶、南宋八十阶完整实例体系。")


def pair_entry(i, family, rank, origin_specs, current_time, grade=None):
    main = F[i]["text"]
    fields = F[i]["fields"]
    origin = field(i, "职源")
    duty = fields.get("职能", origin)
    rank_quote = fields.get("品位")
    roster = fields.get("编制")
    aliases = fields.get("简称")
    grouped_title = pair_title(family, rank)
    assert grouped_title == F[i]["title"], (i, grouped_title, F[i]["title"])
    w, touched = W(i), set()

    for time, event in origin_specs:
        grouped = node(
            w, touched, i, grouped_title, "官职", time, event, origin,
            "环卫官左右合称", f"建立{grouped_title}{time}职源节点。", "职源",
            officer=rank,
        )
        for member_title in member_titles(family, rank):
            member = node(
                w, touched, i, member_title, "官职", time,
                f"{grouped_title}所指实例；{event}", origin, "环卫官",
                f"建立{member_title}{time}职源节点。", "职源", officer=rank,
            )
            relation(w, i, grouped, member, "统称与实例", origin,
                     f"{member_title}是{grouped_title}实例。", "职源")

    grouped = node(
        w, touched, i, grouped_title, "官职", current_time,
        "宋代环卫官，无职事，用作宗室官秩、武臣加官赠官或责降散官",
        duty, "环卫官左右合称", f"复用{grouped_title}{current_time}体系节点。",
        "职能" if "职能" in fields else "职源", officer=rank, grade=grade,
    )
    cite(w, "Timepoints", grouped, i, origin, "保存本职职源与沿置证据。", "职源")
    if rank_quote:
        cite(w, "Timepoints", grouped, i, rank_quote, "保存官品和环卫内部序位。", "品位")
    if roster:
        cite(w, "Timepoints", grouped, i, roster, "保存无定员编制。", "编制")
    if aliases:
        alias_note(w, i, grouped, aliases, "简称")

    system = node(
        w, touched, i, "环卫官", "官职", current_time,
        "环卫官五等体系", main, "环卫官统称",
        f"复用环卫官{current_time}体系节点。", officer="环卫官统称",
    )
    generic_title = GENERIC_RANKS[rank]
    generic = node(
        w, touched, i, generic_title, "官职", current_time,
        f"八卫左、右{rank}总称", main, "环卫官等级统称",
        f"复用{generic_title}{current_time}节点。", officer=f"{rank}统称",
    )
    relation(w, i, system, generic, "统称与实例", main,
             f"{generic_title}是环卫官等级之一。")
    relation(w, i, generic, grouped, "统称与实例", main,
             f"{grouped_title}是{generic_title}实例组。")
    for member_title in member_titles(family, rank):
        member = node(
            w, touched, i, member_title, "官职", current_time,
            f"{grouped_title}所指宋代实例", duty, "环卫官",
            f"复用{member_title}{current_time}体系节点。",
            "职能" if "职能" in fields else "职源", officer=rank, grade=grade,
        )
        relation(w, i, grouped, member, "统称与实例", main,
                 f"{member_title}是{grouped_title}左右实例。")
        cite(w, "Timepoints", member, i, duty, f"保存{member_title}职能。",
             "职能" if "职能" in fields else "职源")
        if rank_quote:
            cite(w, "Timepoints", member, i, rank_quote,
                 f"保存{member_title}官品与序位。", "品位")
    finish(w, touched, f"整理{grouped_title}职源、宋代职能品位、左右实例及环卫官归属。")


def entry1443():
    pair_entry(1443, "金吾卫", "上将军", (("唐德宗朝", "唐德宗朝始置，五代、宋沿置"),), "北宋初", "从二品")


def entry1444():
    pair_entry(1444, "金吾卫", "大将军", (("唐前期", "唐前期始置"),), "北宋初", "正四品")


def entry1445():
    pair_entry(1445, "金吾卫", "将军", (("唐龙朔二年", "唐龙朔二年始设"),), "北宋初", "从四品")


def entry1446():
    pair_entry(1446, "金吾卫", "中郎将", (("北宋初", "北宋初始置"),), "北宋初")


def entry1447():
    pair_entry(1447, "金吾卫", "郎将", (("北宋初", "北宋初始置"),), "北宋初")


def entry1448():
    i, main = 1448, F[1448]["text"]
    w, touched = W(i), set()
    node(
        w, touched, i, "四色官", "官职", "唐朝",
        "唐诸卫司阶、司戈、中候、执戟四官合称，有职事", main,
        "前代武职统称", "建立四色官唐诸卫语境节点。", officer="武职统称",
        update_event=True,
    )
    north = node(
        w, touched, i, "四色官", "官职", "北宋",
        "诸卫不置职事官；左、右金吾卫官一员于百官朝班时唱‘前殿不坐’，时称四色官",
        main, "金吾朝班仪仗官", "建立四色官北宋朝班喝唱节点。",
        officer="仪仗官", update_event=True,
    )
    cite(w, "Timepoints", north, i, main, "保存北宋四色官一员、朝班位置与喝唱职掌。")
    finish(w, touched, "区分四色官唐诸卫职事官统称与北宋金吾朝班仪仗官语境。")


def entry1449():
    pair_entry(1449, "卫", "上将军", (("唐德宗朝", "唐德宗朝始置"),), "北宋初", "从二品")


def entry1450():
    pair_entry(
        1450, "卫", "大将军",
        (("西晋武帝时", "西晋武帝分置左、右二卫，各置大将军"),
         ("隋开皇末", "罢置"),
         ("隋大业十三年", "复置左、右卫大将军")),
        "北宋初", "正四品",
    )


def entry1451():
    pair_entry(
        1451, "卫", "将军",
        (("南朝梁", "南朝梁始置"),
         ("隋朝", "改称左、右翊卫将军"),
         ("唐武德五年", "由左、右翊卫将军改回左、右卫将军")),
        "北宋初", "从四品",
    )
    i, origin = 1451, field(1451, "职源")
    w, touched = W(i), set()
    source = node(
        w, touched, i, "左、右卫将军", "官职", "隋朝",
        "改称左、右翊卫将军", origin, "演变前",
        "复用隋朝改称前节点。", "职源",
    )
    renamed = node(
        w, touched, i, "左、右翊卫将军", "官职", "隋朝",
        "由左、右卫将军改称", origin, "演变后",
        "建立隋朝左、右翊卫将军。", "职源", officer="将军",
    )
    relation(w, i, source, renamed, "前后演变", origin,
             "隋朝左、右卫将军改称左、右翊卫将军。", "职源")
    restored_source = node(
        w, touched, i, "左、右翊卫将军", "官职", "唐武德五年",
        "改回左、右卫将军", origin, "演变前",
        "建立唐武德五年改回前节点。", "职源", officer="将军",
    )
    restored = node(
        w, touched, i, "左、右卫将军", "官职", "唐武德五年",
        "由左、右翊卫将军改回", origin, "演变后",
        "复用唐武德五年复名节点。", "职源", officer="将军",
    )
    relation(w, i, restored_source, restored, "前后演变", origin,
             "唐武德五年左、右翊卫将军改回左、右卫将军。", "职源")
    finish(w, touched, "补足左、右卫将军在隋唐间两次改称演变。")


def compact_pair_entry(i, family, rank, current_time, grade=None):
    origin = field(i, "职源")
    pair_entry(
        i, family, rank,
        ((current_time, origin.split("。")[0] + "。"),),
        current_time, grade,
    )


def entry1452():
    compact_pair_entry(1452, "卫", "中郎将", "北宋初")


def entry1453():
    compact_pair_entry(1453, "卫", "郎将", "北宋初")


def entry1454():
    pair_entry(1454, "骁卫", "上将军", (("唐德宗朝", "唐德宗朝始置"),), "北宋初", "从三品")


def entry1455():
    pair_entry(1455, "骁卫", "大将军", (("隋朝", "隋朝始置"),), "北宋初", "正四品")


def entry1456():
    pair_entry(1456, "骁卫", "将军", (("隋朝", "隋朝始置"),), "北宋初", "从四品")


def main_only_pair_entry(i, family, rank, grade=None):
    main = F[i]["text"]
    w, touched = W(i), set()
    grouped_title = pair_title(family, rank)
    assert grouped_title == F[i]["title"]
    grouped = node(
        w, touched, i, grouped_title, "官职", "南宋乾道二年",
        "始置，列入南宋八卫五等环卫官", main, "环卫官左右合称",
        f"建立或复用{grouped_title}乾道二年节点。", officer=rank,
        grade=grade, update_event=True,
    )
    system = node(
        w, touched, i, "环卫官", "官职", "南宋乾道二年",
        "复除并备置五等八十阶环卫官", main, "环卫官统称",
        "复用乾道二年环卫官体系。", officer="环卫官统称",
    )
    generic_title = GENERIC_RANKS[rank]
    generic = node(
        w, touched, i, generic_title, "官职", "南宋乾道二年",
        f"八卫左、右{rank}总称", main, "环卫官等级统称",
        f"复用{generic_title}乾道二年节点。", officer=f"{rank}统称",
    )
    relation(w, i, system, generic, "统称与实例", main,
             f"{generic_title}是环卫官等级之一。")
    relation(w, i, generic, grouped, "统称与实例", main,
             f"{grouped_title}是{generic_title}实例组。")
    for member_title in member_titles(family, rank):
        member = node(
            w, touched, i, member_title, "官职", "南宋乾道二年",
            f"{grouped_title}所指实例", main, "环卫官",
            f"复用{member_title}乾道二年节点。", officer=rank, grade=grade,
        )
        relation(w, i, grouped, member, "统称与实例", main,
                 f"{member_title}是{grouped_title}左右实例。")
    finish(w, touched, f"整理{grouped_title}乾道二年始置、环卫等级和左右实例。")


def entry1457():
    main_only_pair_entry(1457, "骁卫", "中郎将")


def entry1458():
    main_only_pair_entry(1458, "骁卫", "郎将")


def entry1459():
    pair_entry(1459, "武卫", "上将军", (("唐德宗朝", "唐德宗朝始置"),), "北宋初", "从三品")


def entry1460():
    pair_entry(
        1460, "武卫", "大将军",
        (("隋朝", "隋左、右武卫府始置大将军"), ("唐初", "唐初沿置")),
        "北宋初", "正四品",
    )


def main():
    expected = [
        "六统军", "环卫官", "左、右金吾卫上将军", "左、右金吾卫大将军",
        "左、右金吾卫将军", "左、右金吾卫中郎将", "左、右金吾卫郎将",
        "四色官", "左、右卫上将军", "左、右卫大将军", "左、右卫将军",
        "左、右卫中郎将", "左、右卫郎将", "左、右骁卫上将军",
        "左、右骁卫大将军", "左、右骁卫将军", "左、右骁卫中郎将",
        "左、右骁卫郎将", "左、右武卫上将军", "左、右武卫大将军",
    ]
    assert [F[i]["title"] for i in range(1441, 1461)] == expected
    for i in range(1441, 1461):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
