#!/usr/bin/env python3
"""提取 chapter5t7 第321-340条：卫尉寺属官、内弓箭库与军器库。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_301_320 as previous


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


F = {i: load(i) for i in range(321, 341)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
state = base.state
relation = base.relation
staff = base.staff
tp = base.tp
alias_note = base.alias_note


TIME_HINTS = {
    "秦汉": -221, "西汉": -206, "南朝梁": 502, "北齐": 550, "隋初": 581,
    "宋代": 960, "宋初": 960.1, "宋前期": 970, "北宋初": 960.2,
    "北宋天圣以前（年月未载）": 1020, "北宋天圣三年三月八日": 1025.20,
    "北宋天圣间": 1023, "北宋庆历二年十一月": 1042.87,
    "北宋嘉祐元年十二月二十八日": 1056.99,
    "北宋熙宁元年": 1068, "北宋熙宁六年正月": 1073.04,
    "北宋熙宁六年七月十三日": 1073.54,
    "北宋熙宁十年十一月四日": 1077.86,
    "北宋熙宁间": 1070, "北宋元丰间": 1080,
    "北宋元丰五年": 1082, "北宋元丰新制": 1080.1,
    "南宋建炎三年四月十三日": 1129.29,
    "南宋建炎四年二月十日": 1130.12,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    m = re.search(r"(-?\d{3,4})", time or "")
    if m:
        return (int(m.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [r[0] for r in sorted(rows, key=lambda r: time_key(r[1], r[0]))]
    for n, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[n - 1] if n else None,
            succ_id=ordered[n + 1] if n + 1 < len(ordered) else None,
        )


def set_event(w, tid, event, decision):
    old = w.conn.execute("select event from Timepoints where id=?", (tid,)).fetchone()[0]
    if old != event:
        w.conn.execute("update Timepoints set event=? where id=?", (event, tid))
        w._br("Timepoints", tid, f"事件说明由‘{old}’规范为‘{event}’：{decision}")


def exact_state(w, i, title, type_, time, event, quotation, category, decision,
                field_name=None, *, officer=None, grade=None, note=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade, note=note,
    )
    set_event(w, tid, event, decision)
    return eid, tid


def entry321():
    i, main, aliases = 321, F[321]["text"], field(321, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "判卫尉寺事", "官职", "宋初",
        "卫尉寺无所掌时或置，以郎官以上朝官充，守领本寺，编制一人",
        main, "卫尉寺长官", "补足判卫尉寺事任用、职掌与定额。", officer="差遣",
    )
    cite(w, "Timepoints", post, i, main,
         "南朝梁知卫尉寺仅作前代职源说明，不另建宋制判寺事的前后演变关系。")
    staff(w, i, tp(w, "卫尉寺", "机构", "宋前期"), post, aliases,
          "宋初卫尉寺置判寺事一人。", "简称", quota=1, staff_type="郎官以上朝官")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理判卫尉寺事时间链。")
    w.commit()


def entry322():
    i = 322
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    specs = (
        ("北齐", "始置卫尉寺少卿", history, "前代职源", None, "职事官"),
        ("北宋初", "无职掌，为文臣寄禄官", duty, "寄禄官", "从四品上", "阶官"),
        ("北宋元丰五年", "改为职事官，任本寺副贰，参领寺事", duty, "卫尉寺副长官", "正六品", "职事官"),
        ("南宋建炎三年四月十三日", "随卫尉寺罢置", history, "卫尉寺副长官", "正六品", "职事官"),
    )
    nodes = {}
    for time, event, quote, category, grade, officer in specs:
        eid, nodes[time] = exact_state(
            w, i, "卫尉寺少卿", "官职", time, event, quote, category,
            f"建立或补足卫尉寺少卿{time}节点。",
            "职掌" if quote == duty else "职源与沿革", officer=officer, grade=grade,
        )
    cite(w, "Timepoints", nodes["北宋初"], i, rank, "记录宋前期卫尉寺少卿品位。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, rank, "记录元丰后品位及杂压位次。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")
    staff(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], roster,
          "元丰新制卫尉寺少卿一人。", "编制", quota=1)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")
    rechain(w, eid, "整理卫尉寺少卿完整时间链。")
    w.commit()


def entry323():
    i = 323
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    specs = (
        ("秦汉", "已有卫尉丞", history, "前代职源", None, "职事官"),
        ("北齐", "始置卫尉寺丞", history, "前代职源", None, "职事官"),
        ("北宋初", "无职事，为文臣寄禄官", duty, "寄禄官", "从六品上", "阶官"),
        ("北宋元丰五年", "改为职事官，参领本寺事", duty, "卫尉寺属官", "正八品", "职事官"),
        ("南宋建炎三年四月十三日", "随卫尉寺罢置", history, "卫尉寺属官", "正八品", "职事官"),
    )
    nodes = {}
    for time, event, quote, category, grade, officer in specs:
        eid, nodes[time] = exact_state(
            w, i, "卫尉寺丞", "官职", time, event, quote, category,
            f"建立或补足卫尉寺丞{time}节点。",
            "职掌" if quote == duty else "职源与沿革", officer=officer, grade=grade,
        )
    for time in ("北宋初", "北宋元丰五年"):
        cite(w, "Timepoints", nodes[time], i, rank, "记录卫尉寺丞相应时期品位。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")
    staff(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], roster,
          "元丰新制卫尉寺丞一人。", "编制", quota=1)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")
    rechain(w, eid, "整理卫尉寺丞完整时间链。")
    w.commit()


def entry324():
    i = 324
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "官品"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    specs = (
        ("西汉", "卫尉下已有主簿", history, "前代职源", None, "吏职"),
        ("隋初", "始置卫尉寺主簿", history, "前代职源", None, "职事官"),
        ("北宋初", "无职事，为文臣迁转官阶", duty, "寄禄官", "从七品上", "阶官"),
        ("北宋元丰五年", "改为职事官，专掌勾考簿书", duty, "卫尉寺属官", "从八品", "职事官"),
        ("北宋元祐元年八月以后", "许通管本寺公事", duty, "卫尉寺属官", "从八品", "职事官"),
        ("南宋建炎三年四月十三日", "实际罢置，虽南宋条制仍存九寺主簿泛称", history, "卫尉寺属官", "从八品", "职事官"),
    )
    nodes = {}
    for time, event, quote, category, grade, officer in specs:
        eid, nodes[time] = exact_state(
            w, i, "卫尉寺主簿", "官职", time, event, quote, category,
            f"建立或补足卫尉寺主簿{time}节点。",
            "职掌" if quote == duty else "职源与沿革", officer=officer, grade=grade,
        )
    for time in ("北宋初", "北宋元丰五年"):
        cite(w, "Timepoints", nodes[time], i, rank, "记录卫尉寺主簿相应时期官品。", "官品")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")
    staff(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], roster,
          "元丰新制卫尉寺主簿一人。", "编制", quota=1)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")
    rechain(w, eid, "整理卫尉寺主簿完整时间链。")
    w.commit()


def entry325():
    i, main = 325, F[325]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "卫尉寺府史", "官职", "宋前期",
        "承行卫尉寺事务，编制二人；职源近于隋九寺府史",
        main, "卫尉寺吏", "补足卫尉寺府史职掌、定额与职源。", officer="吏",
    )
    staff(w, i, tp(w, "卫尉寺", "机构", "宋前期"), post, main,
          "宋前期卫尉寺置府史二人。", quota=2, staff_type="吏")
    rechain(w, eid, "整理卫尉寺府史时间链。")
    w.commit()


def entry326():
    i, main = 326, F[326]["text"]
    w = W(i)
    parent_eid, parent = exact_state(
        w, i, "卫尉寺", "机构", "北宋嘉祐元年十二月二十八日",
        "许差提印剩员四人供使唤、承办公事", main,
        "寺监机构", "建立提印剩员设置时的卫尉寺同期节点。",
    )
    eid, post = exact_state(
        w, i, "提印剩员", "官职", "北宋嘉祐元年十二月二十八日",
        "由得替卫尉卿、少卿资级及任差遣职事者差充，供使唤承办公事，四人",
        main, "卫尉寺公吏", "建立提印剩员任用来源、职掌与定额。", officer="公吏",
    )
    staff(w, i, parent, post, main, "嘉祐元年卫尉寺许差提印剩员四人。", quota=4, staff_type="公吏")
    for x in (parent_eid, eid):
        rechain(w, x, "整理卫尉寺嘉祐元年与提印剩员时间链。")
    w.commit()


def entry327():
    i, main = 327, F[327]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    specs = (
        ("宋初", "始置内弓箭库，储藏御弓矢、戎具及多种御用器械", history, "宫廷军器库"),
        ("北宋熙宁元年", "分为南、内、外库", history, "宫廷军器库"),
        ("北宋元丰五年", "改隶卫尉寺", main, "卫尉寺所属机构"),
    )
    nodes = {}
    for time, event, quote, category in specs:
        eid, nodes[time] = exact_state(
            w, i, "内弓箭库", "机构", time, event, quote, category,
            f"建立或补足内弓箭库{time}节点。",
            "职源与沿革" if quote == history else None,
        )
        touched.add(eid)
    cite(w, "Timepoints", nodes["宋初"], i, duty, "记录内弓箭库储藏职能。", "职能")
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"],
             "上下级机构", main, "元丰改制后内弓箭库隶卫尉寺。")
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")
    for title, quota, officer, event in (
        ("内弓箭库勾当官", 4, "监当官", "由诸司使副或内侍充任"),
        ("内弓箭库监门官", 2, "杂职", "由三班使臣或内侍充任"),
        ("内弓箭库兵校及匠", 131, "兵校及工匠", "内弓箭库兵校与工匠合额"),
    ):
        peid, post = exact_state(
            w, i, title, "官职", "宋前期", event, roster,
            "内弓箭库官役", f"按内弓箭库语境建立{title}。", "编制", officer=officer,
        )
        staff(w, i, nodes["宋初"], post, roster, f"内弓箭库置{title}{quota}人。", "编制", quota=quota, staff_type=officer)
        touched.add(peid)
    for title in ("提举内弓箭库", "提点内弓箭库"):
        peid, post = exact_state(
            w, i, title, "官职", "宋前期", "直属监领内弓箭库",
            main, "内弓箭库监领官", f"按宋前期直隶提举、提点官建立{title}。", officer="差遣",
        )
        staff(w, i, nodes["宋初"], post, main, f"宋前期内弓箭库直隶{title}。", staff_type="监领官")
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理内弓箭库沿革、改隶及官役时间链。")
    w.commit()


def entry328():
    i, main = 328, F[328]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "都大提点弓箭库", "官职", "宋前期",
        "在内弓箭库之外另置，监临内弓箭库事",
        main, "内弓箭库监领官", "建立都大提点弓箭库及其监临职掌。", officer="差遣",
    )
    staff(w, i, tp(w, "内弓箭库", "机构", "宋初"), post, main,
          "都大提点弓箭库监临内弓箭库。", staff_type="监领官")
    rechain(w, eid, "整理都大提点弓箭库时间链。")
    w.commit()


def inner_bow_branch(i, title, start_time, start_event):
    main = F[i]["text"]
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, title, "机构", start_time, start_event,
        main, "内弓箭库分库", f"建立{title}始见或始置节点。",
    )
    _, merged = exact_state(
        w, i, title, "机构", "南宋建炎四年二月十日",
        "并入内军器库", main, "内弓箭库分库",
        f"建立{title}并入内军器库节点。",
    )
    inner_eid, inner = exact_state(
        w, i, "内军器库", "机构", "南宋建炎四年二月十日",
        "接收行在军器衣甲库及内弓箭南、内、外库，合并为一库；为南宋唯一正称的合并军器库",
        main, "南宋宫廷军器库", "建立内军器库合并承接节点。",
    )
    relation(w, i, merged, inner, "前后演变", main, f"建炎四年{title}并入内军器库。")
    touched.update((eid, inner_eid))
    for x in touched:
        rechain(w, x, f"整理{title}与内军器库合并时间链。")
    w.commit()


def entry329():
    inner_bow_branch(
        329, "内弓箭南库", "北宋熙宁六年七月十三日",
        "始置，储藏御前所修制军器",
    )


def entry330():
    inner_bow_branch(
        330, "内弓箭外库", "北宋熙宁十年十一月四日", "已见置",
    )


def entry331():
    inner_bow_branch(
        331, "内弓箭内库", "北宋熙宁十年十一月四日", "已见置",
    )


def entry332():
    i, main = 332, F[332]["text"]
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "内弓箭南、内、外库", "机构", "北宋元丰间",
        "内弓箭南库、内库、外库三库合称", main,
        "机构统称", "建立内弓箭南、内、外库统称。",
    )
    touched.add(generic_eid)
    branch_nodes = []
    for title, time in (
        ("内弓箭南库", "北宋熙宁六年七月十三日"),
        ("内弓箭内库", "北宋熙宁十年十一月四日"),
        ("内弓箭外库", "北宋熙宁十年十一月四日"),
    ):
        node = tp(w, title, "机构", time)
        relation(w, i, generic, node, "统称与实例", main, f"{title}为内弓箭南、内、外库实例。")
        branch_nodes.append(tp(w, title, "机构", "南宋建炎四年二月十日"))
    traveling_eid, traveling = exact_state(
        w, i, "行在军器衣甲库", "机构", "南宋建炎四年二月十日",
        "与内弓箭南、内、外库一同并入内军器库",
        main, "南宋军器库", "建立行在军器衣甲库并省节点。",
    )
    inner = tp(w, "内军器库", "机构", "南宋建炎四年二月十日")
    relation(w, i, traveling, inner, "前后演变", main, "行在军器衣甲库并入内军器库。")
    for node in branch_nodes:
        relation(w, i, node, inner, "前后演变", main, "内弓箭南、内、外库并入内军器库。")
    touched.add(traveling_eid)
    for x in touched:
        rechain(w, x, "整理内弓箭三库统称及建炎四年四库合并时间链。")
    w.commit()


def entry333():
    i, main = 333, F[333]["text"]
    w = W(i)
    eid, generic = exact_state(
        w, i, "内弓箭库南外库", "机构", "北宋熙宁六年七月十三日",
        "内弓箭库与新置内弓箭南库二局的合称",
        main, "机构统称", "建立内弓箭库南、外库合称。",
    )
    relation(w, i, generic, tp(w, "内弓箭库", "机构", "北宋熙宁元年"),
             "统称与实例", main, "内弓箭库为内弓箭库南、外库实例。")
    relation(w, i, generic, tp(w, "内弓箭南库", "机构", "北宋熙宁六年七月十三日"),
             "统称与实例", main, "内弓箭南库为内弓箭库南、外库实例。")
    rechain(w, eid, "整理内弓箭库南、外库统称时间链。")
    w.commit()


def entry334():
    i, main = 334, F[334]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "别名"),
    )
    w = W(i)
    touched = set()
    arsenal_eid, han = exact_state(
        w, i, "武库", "机构", "西汉", "已有武库令所领武库",
        history, "前代军器机构", "建立军器库前代职源武库。", "职源与沿革",
    )
    _, liang = exact_state(
        w, i, "武库", "机构", "南朝梁", "隶卫尉卿，置武库令",
        history, "前代军器机构", "补足南朝梁武库职源。", "职源与沿革",
    )
    store_eid, song = exact_state(
        w, i, "军器库", "机构", "宋初", "始置，掌兵器、铠甲及供军什器收受出纳",
        history, "宫廷军器库", "建立北宋军器库始置节点。", "职源与沿革",
    )
    _, reform = exact_state(
        w, i, "军器库", "机构", "北宋元丰五年", "改隶卫尉寺",
        main, "卫尉寺所属机构", "建立元丰新制军器库改隶节点。",
    )
    _, merged = exact_state(
        w, i, "军器库", "机构", "南宋建炎四年二月十日",
        "诸军器库合并为内军器库一库", history,
        "宫廷军器库", "建立军器库并为内军器库节点。", "职源与沿革",
    )
    inner_eid, inner = exact_state(
        w, i, "内军器库", "机构", "南宋建炎四年二月十日",
        "接收行在军器衣甲库及内弓箭南、内、外库，合并为一库；为南宋唯一正称的合并军器库", aliases,
        "南宋宫廷军器库", "确认建炎四年后内军器库正称。", "别名",
    )
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), reform,
             "上下级机构", main, "元丰新制军器库隶卫尉寺。")
    relation(w, i, merged, inner, "前后演变", history, "建炎四年军器诸库并为内军器库。", "职源与沿革")
    cite(w, "Timepoints", song, i, duty, "记录军器库职能。", "职能")
    alias_note(w, i, inner, aliases, "别名")
    touched.update((arsenal_eid, store_eid, inner_eid))

    parent_eid, old_parent = exact_state(
        w, i, "都大提举在京诸司库务司", "机构", "宋前期",
        "本条省称都大提举诸司库务所，原领军器库及军器衣甲库",
        main, "在京库务管理机构", "复用既有全称并记录军器库宋前期归隶。",
    )
    relation(w, i, old_parent, song, "上下级机构", main, "宋前期军器库隶都大提举诸司库务所。")
    touched.add(parent_eid)

    # 三库、四库、五库为军器库下属库群随数量增加的不同阶段。
    groups = (
        ("军器三库", "北宋天圣以前（年月未载）", ("军器衣甲库", "军器弓枪库", "军器弩剑箭库")),
        ("军器四库", "北宋天圣间", ("军器衣甲库", "军器弓枪库", "军器弩剑箭库", "军器什物库")),
        ("军器五库", "北宋熙宁间", ("军器衣甲库", "军器弓枪库", "军器弩剑箭库", "军器什物库", "拣选衣甲器械库")),
    )
    group_nodes = []
    for group_title, time, members in groups:
        geid, generic = exact_state(
            w, i, group_title, "机构", time,
            (
                "军器衣甲、弓枪、弩剑箭、什物、拣选衣甲器械五库合称，兵校共四百五十人"
                if group_title == "军器五库"
                else f"军器库所属{len(members)}库的合称"
            ), roster,
            "机构统称", f"建立{group_title}阶段性统称。", "编制",
        )
        relation(w, i, song, generic, "上下级机构", roster, f"{group_title}为军器库所辖库群。", "编制")
        group_nodes.append(generic)
        touched.add(geid)
        for member in members:
            meid, office = state(
                w, i, member, "机构", time, f"{group_title}实例之一",
                roster, "军器库所属机构", f"建立或复用{member}的{group_title}语境节点。", "编制",
            )
            relation(w, i, generic, office, "统称与实例", roster, f"{member}为{group_title}实例。", "编制")
            touched.add(meid)
    relation(w, i, group_nodes[0], group_nodes[1], "前后演变", roster, "军器库由三库增为四库。", "编制")
    relation(w, i, group_nodes[1], group_nodes[2], "前后演变", roster, "军器库由四库增为五库。", "编制")

    for title, officer in (
        ("都大提举军器库", "监领官"), ("都大提点军器库", "监领官"),
        ("管勾军器库", "监当官"), ("监军器库", "监当官"),
        ("军器库监门官", "杂职"), ("军器库公吏", "公吏"),
    ):
        peid, post = exact_state(
            w, i, title, "官职", "北宋熙宁间", "总监领或分库承办军器库事务",
            roster, "军器库官吏", f"据军器库编制建立{title}。", "编制", officer=officer,
        )
        staff(w, i, group_nodes[2], post, roster, f"军器诸库置{title}。", "编制", staff_type=officer)
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理军器库职源、改隶、库群演变及官吏时间链。")
    w.commit()


def entry335():
    i, main = 335, F[335]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "管勾制置军器司", "官职", "北宋庆历二年十一月",
        "由权三司使、殿前副都指挥使、马军副都指挥使三人充，统管军器库事",
        main, "军器库监领官", "建立管勾制置军器司任用、职掌与三人编制。", officer="差遣",
    )
    staff(w, i, tp(w, "军器库", "机构", "宋初"), post, main,
          "庆历二年三人管勾制置军器司并统管军器库。", quota=3, staff_type="差遣")
    rechain(w, eid, "整理管勾制置军器司时间链。")
    w.commit()


def entry336():
    i, main, aliases = 336, F[336]["text"], field(336, "简称")
    w = W(i)
    eid, office = exact_state(
        w, i, "都大提点军器库所", "机构", "北宋熙宁间",
        "都大提点军器官治所，监领军器库逐库事务，位次于都大提举所",
        main, "军器库监领机构", "建立都大提点军器库所及位次。",
    )
    relation(w, i, office, tp(w, "军器五库", "机构", "北宋熙宁间"),
             "上下级机构", main, "都大提点军器库所监领军器诸库。")
    alias_note(w, i, office, aliases, "简称")
    rechain(w, eid, "整理都大提点军器库所时间链。")
    w.commit()


def entry337():
    i, main, aliases = 337, F[337]["text"], field(337, "简称")
    w = W(i)
    eid, office = exact_state(
        w, i, "都大提举内军器库所", "机构", "北宋天圣三年三月八日",
        "置治所总监诸军器库公事，位在都大提点官之上",
        main, "军器库监领机构", "建立都大提举内军器库所始置、职掌与位次。",
    )
    relation(w, i, office, tp(w, "军器库", "机构", "宋初"),
             "上下级机构", main, "都大提举内军器库所总监军器库。")
    alias_note(w, i, office, aliases, "简称")
    rechain(w, eid, "整理都大提举内军器库所时间链。")
    w.commit()


def entry338():
    i, main = 338, F[338]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "都大提举内弓箭军器库", "官职", "北宋天圣三年三月八日",
        "由内侍官充，总监内弓箭库、军器库公事",
        main, "军器库监领官", "建立都大提举内弓箭军器库始置、资格与职掌。", officer="内侍差遣",
    )
    staff(w, i, tp(w, "内弓箭库", "机构", "宋初"), post, main,
          "都大提举官总监内弓箭库。", staff_type="内侍差遣")
    staff(w, i, tp(w, "军器库", "机构", "宋初"), post, main,
          "都大提举官总监军器库。", staff_type="内侍差遣")
    rechain(w, eid, "整理都大提举内弓箭军器库时间链。")
    w.commit()


def entry339():
    i, main, aliases = 339, F[339]["text"], field(339, "别名")
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "军器五库", "机构", "北宋熙宁间",
        "军器衣甲、弓枪、弩剑箭、什物、拣选衣甲器械五库合称，兵校共四百五十人",
        main, "机构统称", "按军器库专条体系确认军器五库构成与兵校总额。",
    )
    touched.add(generic_eid)
    for title in ("军器衣甲库", "军器弓枪库", "军器弩剑箭库", "军器什物库", "拣选衣甲器械库"):
        eid, office = state(
            w, i, title, "机构", "北宋熙宁间", "军器五库实例之一",
            main, "军器库所属机构", f"建立或复用{title}的军器五库语境节点。",
        )
        relation(w, i, generic, office, "统称与实例", main, f"{title}为本条军器五库实例。")
        touched.add(eid)
    soldier_eid, soldiers = exact_state(
        w, i, "军器五库兵校", "官职", "北宋熙宁间",
        "五库共有四百五十人管库", main,
        "军器库兵役", "建立军器五库兵校总额。", officer="兵校",
    )
    staff(w, i, generic, soldiers, main, "军器五库共有兵校四百五十人。", quota=450, staff_type="兵校")
    alias_note(w, i, generic, aliases, "别名")
    touched.add(soldier_eid)
    for x in touched:
        rechain(w, x, "整理军器五库专条体系、实例及兵校时间链。")
    w.commit()


def entry340():
    i, main, aliases = 340, F[340]["text"], field(340, "简称")
    w = W(i)
    touched = set()
    eid, early = exact_state(
        w, i, "军器衣甲库", "机构", "宋前期",
        "军器库之一，熙宁五年以前隶都大提举诸司库务所",
        main, "宫廷军器库", "建立军器衣甲库宋前期归隶节点。",
    )
    _, direct = exact_state(
        w, i, "军器衣甲库", "机构", "北宋熙宁六年正月",
        "改为直隶都大提举军器库所", main,
        "军器库所属机构", "建立熙宁六年改隶节点。",
    )
    _, reform = exact_state(
        w, i, "军器衣甲库", "机构", "北宋元丰五年",
        "改隶卫尉寺", main, "卫尉寺所属机构",
        "确认元丰后军器衣甲库隶卫尉寺。",
    )
    _, merged = exact_state(
        w, i, "军器衣甲库", "机构", "南宋建炎四年二月十日",
        "并入内军器库", main, "宫廷军器库",
        "建立军器衣甲库并入内军器库节点。",
    )
    old_parent_eid, old_parent = exact_state(
        w, i, "都大提举在京诸司库务司", "机构", "宋前期",
        "本条省称都大提举诸司库务所，原领军器库及军器衣甲库",
        main, "在京库务管理机构", "复用既有全称承载军器衣甲库原归隶。",
    )
    relation(w, i, old_parent, early, "上下级机构", main, "熙宁五年前军器衣甲库隶都大提举诸司库务所。")
    relation(w, i, tp(w, "都大提举内军器库所", "机构", "北宋天圣三年三月八日"), direct,
             "上下级机构", main, "熙宁六年后军器衣甲库直隶都大提举军器库所。")
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), reform,
             "上下级机构", main, "元丰改制后军器衣甲库隶卫尉寺。")
    relation(w, i, merged, tp(w, "内军器库", "机构", "南宋建炎四年二月十日"),
             "前后演变", main, "建炎四年军器衣甲库并入内军器库。")
    alias_note(w, i, reform, aliases, "简称")
    touched.update((eid, old_parent_eid))
    for x in touched:
        rechain(w, x, "整理军器衣甲库多次改隶及并省时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(321, 341)] == [
        "判卫尉寺事", "卫尉寺少卿", "卫尉寺丞", "卫尉寺主簿", "府史",
        "提印剩员", "内弓箭库", "都大提点弓箭库", "内弓箭南库",
        "内弓箭外库", "内弓箭内库", "内弓箭南、内、外库",
        "内弓箭库南外库", "军器库", "管勾制置军器司", "都大提点军器库所",
        "都大提举内军器库所", "都大提举内弓箭军器库", "军器五库", "军器衣甲库",
    ]
    entry321()
    entry322()
    entry323()
    entry324()
    entry325()
    entry326()
    entry327()
    entry328()
    entry329()
    entry330()
    entry331()
    entry332()
    entry333()
    entry334()
    entry335()
    entry336()
    entry337()
    entry338()
    entry339()
    entry340()


if __name__ == "__main__":
    main()
