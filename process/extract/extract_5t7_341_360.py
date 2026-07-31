#!/usr/bin/env python3
"""提取 chapter5t7 第341-360条：军器诸库、内军器库与管库兵阶级。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_321_340 as previous


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


F = {i: load(i) for i in range(341, 361)}
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
    "宋代": 960,
    "宋代（军器诸库）": 960.01,
    "宋代（内弓箭军器诸库）": 960.02,
    "宋代（军器七库至内军器库）": 960.03,
    "宋代（内军器库选补制度）": 960.04,
    "宋初": 960.1, "宋前期": 970,
    "北宋（军器七库，年月未载）": 1067.1,
    "北宋神宗朝": 1067.2,
    "北宋熙宁间": 1070,
    "北宋元丰五年": 1082,
    "南宋": 1127,
    "南宋初": 1127.1,
    "南宋（内军器库）": 1127.2,
    "南宋（内军器库库子制度）": 1127.21,
    "南宋建炎四年二月十日": 1130.12,
    "南宋建炎四年八月以后": 1130.65,
    "南宋绍兴三年五月十二日以前": 1133.35,
    "南宋绍兴三年五月十二日": 1133.36,
    "南宋绍兴八年": 1138,
    "南宋绍兴十年": 1140,
    "南宋（内军器库增额后，年月未载）": 1140.1,
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


def monitor_entry(i, post_title, store_title, store_time, event,
                  *, aliases=None, alias_field="简称", staff_type):
    main = F[i]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, post_title, "官职", store_time, event,
        main, "军器库监官", f"建立{post_title}的任用、定额与职掌。",
        officer=staff_type,
    )
    parent = tp(w, store_title, "机构", store_time)
    staff(w, i, parent, post, main, f"{store_title}置{post_title}二人。",
          quota=2, staff_type=staff_type)
    if aliases:
        alias_note(w, i, post, aliases, alias_field)
    rechain(w, eid, f"整理{post_title}时间链。")
    w.commit()


def existing_five_store(i, title, aliases=None):
    main = F[i]["text"]
    w = W(i)
    member = tp(w, title, "机构", "北宋熙宁间")
    generic = tp(w, "军器五库", "机构", "北宋熙宁间")
    relation(w, i, generic, member, "统称与实例", main,
             f"{title}为北宋熙宁间军器五库实例。")
    cite(w, "Timepoints", member, i, main, f"补充{title}的机构性质与军器库归属证据。")
    if aliases:
        alias_note(w, i, member, aliases, "简称")
    w.commit()


def entry341():
    monitor_entry(
        341, "监军器衣甲库", "军器衣甲库", "北宋熙宁间",
        "由诸司使副、内侍充，二人，通领本库储藏与出纳",
        staff_type="诸司使副、内侍差遣",
    )


def entry342():
    existing_five_store(342, "军器弓枪库", field(342, "简称"))


def entry343():
    monitor_entry(
        343, "监军器弓枪库", "军器弓枪库", "北宋熙宁间",
        "由诸司使副或三班使臣、内侍充，二人，通领本库储藏与出纳",
        aliases=field(343, "别称"), alias_field="别称",
        staff_type="诸司使副或三班使臣、内侍差遣",
    )


def entry344():
    existing_five_store(344, "军器弩剑箭库", field(344, "简称"))


def entry345():
    monitor_entry(
        345, "监弩剑箭库", "军器弩剑箭库", "北宋熙宁间",
        "由诸司使副及内侍官充，编制二人",
        staff_type="诸司使副、内侍差遣",
    )


def entry346():
    existing_five_store(346, "军器什物库", field(346, "简称"))


def entry347():
    monitor_entry(
        347, "监军器什物库", "军器什物库", "北宋熙宁间",
        "由三班使臣、内侍官充，二人，监领本库事务",
        staff_type="三班使臣、内侍差遣",
    )


def entry348():
    i, main = 348, F[348]["text"]
    w = W(i)
    node = tp(w, "拣选衣甲器械库", "机构", "北宋熙宁间")
    generic = tp(w, "军器五库", "机构", "北宋熙宁间")
    relation(w, i, generic, node, "统称与实例", main,
             "拣选衣甲器械库为北宋熙宁间军器五库实例。")
    cite(w, "Timepoints", node, i, main,
         "记录拣选合格衣甲器械送库、不合格者退回修补的职掌。")
    w.commit()


def entry349():
    monitor_entry(
        349, "监拣选衣甲器械库", "拣选衣甲器械库", "北宋熙宁间",
        "由诸司使副、内侍充，二人，监领本库事务",
        staff_type="诸司使副、内侍差遣",
    )


def entry350():
    i, main = 350, F[350]["text"]
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "军器库掾", "官职", "宋代（军器诸库）",
        "军器诸库专知官、副知、库子、前行、手分等祗应公人的泛称",
        main, "军器诸库公人统称", "建立军器库掾统称。", officer="公人统称",
    )
    touched.add(generic_eid)
    for title in ("专知官", "副知", "库子", "前行", "手分"):
        eid, role = exact_state(
            w, i, title, "官职", "宋代（军器诸库）",
            "军器诸库祗应公人之一", main,
            "军器诸库公人", f"建立{title}的军器诸库语境节点。", officer="公人",
        )
        relation(w, i, generic, role, "统称与实例", main,
                 f"{title}为军器库掾所指实例。")
        touched.add(eid)
    for eid in touched:
        rechain(w, eid, "整理军器库掾及其公人实例时间链。")
    w.commit()


def entry351():
    i, main = 351, F[351]["text"]
    w = W(i)
    touched = set()
    generic_eid, north = exact_state(
        w, i, "军器七库", "机构", "北宋神宗朝",
        "卫尉寺所隶内弓箭南、外二库及军器衣甲、弓枪、弩剑箭、什物、拣选衣甲器械五库合称",
        main, "机构统称", "建立北宋神宗朝军器七库体系。",
    )
    touched.add(generic_eid)
    north_members = (
        ("内弓箭南库", "北宋熙宁六年七月十三日"),
        ("内弓箭外库", "北宋熙宁十年十一月四日"),
        ("军器衣甲库", "北宋元丰五年"),
        ("军器弓枪库", "北宋元丰五年"),
        ("军器弩剑箭库", "北宋熙宁间"),
        ("军器什物库", "北宋元丰五年"),
        ("拣选衣甲器械库", "北宋熙宁间"),
    )
    for title, time in north_members:
        relation(w, i, north, tp(w, title, "机构", time), "统称与实例", main,
                 f"{title}为北宋神宗朝军器七库实例。")
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), north,
             "上下级机构", main, "北宋神宗朝军器七库隶卫尉寺。")

    _, south = exact_state(
        w, i, "军器七库", "机构", "南宋建炎四年八月以后",
        "军器衣甲、弓枪、弩剑箭、什物与内弓箭南、外、内七库合称，管库兵一千余人，逐步并为内军器库一库",
        main, "机构统称", "建立南宋初并省语境的军器七库体系。",
    )
    inner_eid, inner_progress = exact_state(
        w, i, "内军器库", "机构", "南宋建炎四年八月以后",
        "军器七库继续逐步合并为一库", main,
        "南宋宫廷军器库", "建立军器七库继续并省的内军器库节点。",
    )
    touched.add(inner_eid)
    south_members = (
        ("军器衣甲库", "南宋建炎四年二月十日", None),
        ("内弓箭南库", "南宋建炎四年二月十日", None),
        ("内弓箭外库", "南宋建炎四年二月十日", None),
        ("内弓箭内库", "南宋建炎四年二月十日", None),
        ("军器弓枪库", "南宋建炎四年八月以后", "军器七库逐步并入内军器库"),
        ("军器弩剑箭库", "南宋建炎四年八月以后", "军器七库逐步并入内军器库"),
        ("军器什物库", "南宋建炎四年八月以后", "军器七库逐步并入内军器库"),
    )
    for title, time, event in south_members:
        if event:
            eid, node = exact_state(
                w, i, title, "机构", time, event, main,
                "南宋军器库", f"建立{title}逐步并入内军器库节点。",
            )
            touched.add(eid)
            relation(w, i, node, inner_progress, "前后演变", main,
                     f"{title}逐步并入内军器库。")
        else:
            node = tp(w, title, "机构", time)
        relation(w, i, south, node, "统称与实例", main,
                 f"{title}为南宋初军器七库实例。")
    relation(w, i, south, inner_progress, "前后演变", main,
             "南宋建炎四年八月以后军器七库逐步并为内军器库一库。")
    for eid in touched:
        rechain(w, eid, "整理军器七库南北体系与内军器库并省时间链。")
    w.commit()


def entry352():
    i = 352
    main = F[i]["text"]
    history, duty, roster = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    touched = set()
    # 熙宁间“内军器库”只是军器库的别称，不与南宋正置内军器库混为同一制度状态。
    cite(w, "Timepoints", tp(w, "军器库", "机构", "宋初"), i, history,
         "北宋熙宁间内军器库仅为军器库别称，不另建实体或演变关系。",
         "职源与沿革", note="北宋别称与南宋正置机构分开处理")
    start = tp(w, "内军器库", "机构", "南宋建炎四年二月十日")
    cite(w, "Timepoints", start, i, history,
         "补充建炎四年二月十日四库并为内军器库的沿革证据。", "职源与沿革")
    cite(w, "Timepoints", start, i, duty, "记录内军器库储藏、出纳职掌。", "职掌")

    inner_eid, before = exact_state(
        w, i, "内军器库", "机构", "南宋绍兴三年五月十二日以前",
        "此前军器弓枪库、军器弩剑箭库已并入", history,
        "南宋宫廷军器库", "建立绍兴三年前两库已并入内军器库节点。", "职源与沿革",
    )
    _, shao3 = exact_state(
        w, i, "内军器库", "机构", "南宋绍兴三年五月十二日",
        "军器什物库并入，七库并省过程完成", history,
        "南宋宫廷军器库", "建立绍兴三年军器什物库并入节点。", "职源与沿革",
    )
    touched.add(inner_eid)
    for title in ("军器弓枪库", "军器弩剑箭库"):
        eid, merged = exact_state(
            w, i, title, "机构", "南宋绍兴三年五月十二日以前",
            "此前已并入内军器库", history,
            "南宋军器库", f"建立{title}在绍兴三年前并入节点。", "职源与沿革",
        )
        relation(w, i, merged, before, "前后演变", history,
                 f"{title}在绍兴三年五月十二日前并入内军器库。", "职源与沿革")
        touched.add(eid)
    misc_eid, misc = exact_state(
        w, i, "军器什物库", "机构", "南宋绍兴三年五月十二日",
        "并入内军器库", history, "南宋军器库",
        "建立军器什物库绍兴三年并入节点。", "职源与沿革",
    )
    relation(w, i, misc, shao3, "前后演变", history,
             "绍兴三年五月十二日军器什物库并入内军器库。", "职源与沿革")
    touched.add(misc_eid)

    _, shao10 = exact_state(
        w, i, "内军器库", "机构", "南宋绍兴十年",
        "设人兵一百四十八人，并有五阶级管库兵职名与多种人吏",
        roster, "南宋宫廷军器库", "建立绍兴十年编制节点。", "编制",
    )
    for title, event, quota, staff_type in (
        ("都大提点内军器库", "监领内军器库公事", None, "监领官"),
        ("监内军器库门", "监守内军器库门", 2, "监门官"),
    ):
        eid, post = exact_state(
            w, i, title, "官职", "南宋", event, roster,
            "内军器库官属", f"建立{title}编制。", "编制", officer=staff_type,
        )
        staff(w, i, start, post, roster, f"内军器库设置{title}。", "编制",
              quota=quota, staff_type=staff_type)
        touched.add(eid)
    soldier_eid, soldiers = exact_state(
        w, i, "内军器库兵校", "官职", "南宋绍兴十年",
        "人兵一百四十八人，含指挥使、都头、十将、将虞候、节级五阶级职名",
        roster, "内军器库兵役", "建立内军器库兵校定额。", "编制", officer="兵校",
    )
    staff(w, i, shao10, soldiers, roster, "绍兴十年内军器库人兵一百四十八人。",
          "编制", quota=148, staff_type="兵校")
    touched.add(soldier_eid)

    generic_eid, clerks = exact_state(
        w, i, "内军器库人吏", "官职", "南宋绍兴十年",
        "架子头、专知、副知、前行、手分、库子等公人和吏人的合称",
        roster, "内军器库人吏统称", "建立内军器库人吏统称。", "编制", officer="公人、吏人统称",
    )
    staff(w, i, shao10, clerks, roster, "内军器库设置公人、吏人。", "编制", staff_type="公人、吏人")
    touched.add(generic_eid)
    for title in ("架子头", "专知官", "副知", "前行", "手分", "库子"):
        eid, role = exact_state(
            w, i, title, "官职", "南宋（内军器库）",
            "内军器库人吏之一", roster, "内军器库人吏",
            f"建立{title}的内军器库语境节点。", "编制", officer="公人或吏人",
        )
        relation(w, i, clerks, role, "统称与实例", roster,
                 f"{title}为内军器库人吏实例。", "编制")
        touched.add(eid)
    for eid in touched:
        rechain(w, eid, "整理内军器库分阶段并省、官兵与人吏时间链。")
    w.commit()


def entry353():
    i, main, aliases = 353, F[353]["text"], field(353, "简称")
    w = W(i)
    eid, office = exact_state(
        w, i, "都大提点内军器库所", "机构", "南宋初",
        "始置，监领内军器库公事", main,
        "内军器库监领机构", "建立都大提点内军器库所。",
    )
    relation(w, i, office, tp(w, "内军器库", "机构", "南宋建炎四年二月十日"),
             "上下级机构", main, "都大提点内军器库所监领内军器库。")
    alias_note(w, i, office, aliases, "简称")
    rechain(w, eid, "整理都大提点内军器库所时间链。")
    w.commit()


def entry354():
    i, main = 354, F[354]["text"]
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "监专", "官职", "宋代（军器诸库）",
        "监库官与专知官的合称；军器四库监官建议以三年为任期", main,
        "军器库官吏统称", "建立监专统称。", officer="官吏统称",
    )
    monitor_eid, monitor = exact_state(
        w, i, "监库官", "官职", "宋代（军器诸库）",
        "军器诸库监官，监专所指实例之一", main,
        "军器库监官", "建立监库官实例。", officer="监官",
    )
    specialist = tp(w, "专知官", "官职", "宋代（军器诸库）")
    cite(w, "Timepoints", specialist, i, main, "确认专知官为监专实例。")
    relation(w, i, generic, monitor, "统称与实例", main, "监库官为监专实例。")
    relation(w, i, generic, specialist, "统称与实例", main, "专知官为监专实例。")
    touched.update((generic_eid, monitor_eid))
    for eid in touched:
        rechain(w, eid, "整理监专及监库官时间链。")
    w.commit()


def entry355():
    i, main = 355, F[355]["text"]
    w = W(i)
    eid, north = exact_state(
        w, i, "库子", "官职", "宋代（内弓箭军器诸库）",
        "掌受纳、排垛军器，可迁补节级阙", main,
        "军器诸库公吏", "建立库子的内弓箭军器诸库语境节点。", officer="公吏",
    )
    _, south = exact_state(
        w, i, "库子", "官职", "南宋（内军器库库子制度）",
        "内军器库人吏之一，掌受纳、排垛军器，可迁补节级阙", main,
        "内军器库人吏", "补足库子在内军器库的职掌与迁补规则。", officer="公吏",
    )
    staff(w, i, tp(w, "内弓箭库", "机构", "宋初"), north, main,
          "内弓箭军器诸库设置库子。", staff_type="公吏")
    staff(w, i, tp(w, "内军器库", "机构", "南宋建炎四年二月十日"), south,
          main, "南宋内军器库设置库子。", staff_type="公吏")
    rechain(w, eid, "整理库子在军器诸库的职掌时间链。")
    w.commit()


def entry356():
    i, main = 356, F[356]["text"]
    w = W(i)
    eid, north = exact_state(
        w, i, "架子头", "官职", "北宋（军器七库，年月未载）",
        "在军器七库听差执役，可迁补节级阙", main,
        "军器七库公吏", "建立北宋军器七库架子头。", officer="公吏",
    )
    _, south = exact_state(
        w, i, "架子头", "官职", "南宋绍兴八年",
        "内军器库置十六人，听差执役，可迁补节级阙，请给依前行标准",
        main, "内军器库人吏", "建立绍兴八年内军器库架子头定额。", officer="公吏",
    )
    staff(w, i, tp(w, "军器七库", "机构", "北宋神宗朝"), north,
          main, "北宋军器七库设置架子头。", staff_type="公吏")
    staff(w, i, tp(w, "内军器库", "机构", "南宋绍兴三年五月十二日"), south,
          main, "绍兴八年内军器库置架子头十六人。", quota=16, staff_type="公吏")
    rechain(w, eid, "整理架子头南北军器库时间链。")
    w.commit()


def entry357():
    i, main = 357, F[357]["text"]
    w = W(i)
    eid, north = exact_state(
        w, i, "内军器库营", "机构", "北宋（军器七库，年月未载）",
        "原为北宋诸军器库营兵士，编制一千余人", main,
        "军器库兵营", "建立内军器库营的北宋来源。",
    )
    _, early = exact_state(
        w, i, "内军器库营", "机构", "南宋初",
        "随高宗移温州时以一百人为额，供看管逐库兵器", main,
        "内军器库兵营", "建立南宋初内军器库营节点。",
    )
    _, later = exact_state(
        w, i, "内军器库营", "机构", "南宋（内军器库增额后，年月未载）",
        "设在临安府清波门内沿城之南，增至一百四十八人，供看管逐库兵器",
        main, "内军器库兵营", "建立内军器库营增额及驻地节点。",
    )
    relation(w, i, tp(w, "军器七库", "机构", "北宋神宗朝"), north,
             "上下级机构", main, "北宋诸军器库营兵隶军器七库体系。")
    relation(w, i, tp(w, "内军器库", "机构", "南宋建炎四年二月十日"), early,
             "上下级机构", main, "南宋内军器库营隶内军器库。")
    rechain(w, eid, "整理内军器库营沿革与定额时间链。")
    w.commit()


def entry358():
    i, main = 358, F[358]["text"]
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "管库兵五阶级", "官职", "宋代（军器七库至内军器库）",
        "节级、将虞候、十将、副都头、指挥使五种领兵职名的合称；七库兵校一千余人，内军器库兵校一百四十八人",
        main, "管库兵职名统称", "建立管库兵五阶级统称及南北定额。", officer="兵校职名统称",
    )
    touched.add(generic_eid)
    for title in ("节级", "将虞候", "十将", "副都头", "指挥使"):
        eid, rank = exact_state(
            w, i, title, "官职", "宋代（军器七库至内军器库）",
            "管库兵五阶级职名之一", main,
            "管库兵阶级", f"建立{title}的管库兵语境节点。", officer="兵校职名",
        )
        relation(w, i, generic, rank, "统称与实例", main,
                 f"{title}为管库兵五阶级实例。")
        touched.add(eid)
    staff(w, i, tp(w, "军器七库", "机构", "北宋神宗朝"), generic,
          main, "北宋军器七库管库兵以五阶级领兵。", staff_type="兵校职名")
    staff(w, i, tp(w, "内军器库", "机构", "南宋绍兴十年"), generic,
          main, "南宋内军器库一百四十八名兵校以五阶级领兵。",
          quota=148, staff_type="兵校职名")
    for eid in touched:
        rechain(w, eid, "整理管库兵五阶级及实例时间链。")
    w.commit()


def entry359():
    i, main = 359, F[359]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "节级", "官职", "宋代（内军器库选补制度）",
        "管库兵五阶级之一，出缺时从架子头、库子中选择年资最高者补充",
        main, "管库兵阶级", "建立节级选补规则。", officer="兵校职名",
    )
    generic = tp(w, "管库兵五阶级", "官职", "宋代（军器七库至内军器库）")
    relation(w, i, generic, post, "统称与实例", main, "节级为管库兵五阶级实例。")
    rechain(w, eid, "整理节级的管库兵语境与选补时间链。")
    w.commit()


def entry360():
    i, main = 360, F[360]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "将虞候", "官职", "宋代（内军器库选补制度）",
        "管库兵五阶级之一，出缺时由节级选补",
        main, "管库兵阶级", "建立将虞候选补规则。", officer="兵校职名",
    )
    generic = tp(w, "管库兵五阶级", "官职", "宋代（军器七库至内军器库）")
    relation(w, i, generic, post, "统称与实例", main, "将虞候为管库兵五阶级实例。")
    rechain(w, eid, "整理将虞候的管库兵语境与选补时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(341, 361)] == [
        "监军器衣甲库", "军器弓枪库", "监军器弓枪库", "军器弩剑箭库",
        "监弩剑箭库", "军器什物库", "监军器什物库", "拣选衣甲器械库",
        "监拣选衣甲器械库", "军器库掾", "军器七库", "内军器库",
        "都大提点内军器库所", "监专", "库子", "架子头", "内军器库营",
        "管库兵五阶级", "节级", "将虞候",
    ]
    for i in range(341, 361):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
