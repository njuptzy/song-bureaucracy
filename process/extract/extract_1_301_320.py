#!/usr/bin/env python3
"""提取第一编第301-320条：东宫诸率府、公主宅官与公主封号。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(297, 321)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def field(i, name):
    value = F[i]["fields"][name]
    assert value
    return value


def C(i, name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{name}字段）" if name else "")


def cite(w, table, target_id, i, quotation, decision, name=None, **kwargs):
    source = F[i]["fields"][name] if name else F[i]["text"]
    assert quotation in source, (i, name, quotation)
    return w.citation(
        table, target_id, C(i, name), quotation, decision, **kwargs
    )


def timepoint(
    w, i, entity_id, time, event, quotation, decision, name=None,
    category=None, officer_type=None, grade=None, chain="tail",
):
    target_id = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer_type,
        attr_grade=grade, chain=chain,
    )
    cite(w, "Timepoints", target_id, i, quotation, decision, name)
    return target_id


def relation(
    w, i, subject, object_, kind, quotation, decision, name=None,
    staff_type=None, staff_quota=None,
):
    target_id = w.relationship(
        subject, object_, kind, decision, quotation,
        staff_type=staff_type, staff_quota=staff_quota,
    )
    cite(w, "Relationships", target_id, i, quotation, decision, name)
    return target_id


def find_entity(w, title, type_="官职"):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    return entity_id


def find_tp(w, title, time, type_="官职"):
    entity_id = find_entity(w, title, type_)
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time, type_)
    return target_id


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；不另建称谓实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def rate_pair(i, points):
    """建立诸率府某一府的职源及宋代实例节点。"""
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职",
        f"词头及正文确定{F[i]['title']}为东宫武官。", quotation=main,
    )
    song_tp = None
    for time, event, name, is_song in points:
        quotation = field(i, name) if name else main
        tp_id = timepoint(
            w, i, entity_id, time, event, quotation,
            f"建立{F[i]['title']}的{time}节点。", name,
            category="东宫武官" if is_song else None,
            grade="率从七品；副率从八品" if is_song else None,
        )
        if is_song and song_tp is None:
            song_tp = tp_id
    assert song_tp
    w.commit()
    return song_tp


def entry301():
    rate_pair(301, ((
        "宋代（具体时间未载）",
        "司御率府率、副率分左、右设置，曾巩文集见太子右司御率府副率",
        None, True,
    ),))


def entry302():
    rate_pair(302, (
        ("唐高宗龙朔二年（662）", "左右虞候府改为左右清道率府", "职源", False),
        ("宋太宗至道元年（995）", "王继英任左清道率府副率兼左春坊谒者", "职源", True),
    ))


def entry303():
    rate_pair(303, ((
        "宋代（具体时间未载）", "清道率府率、副率分左、右设置", None, True,
    ),))


def entry304():
    rate_pair(304, (
        ("隋文帝时", "已置左、右监门率府率、副率", "职源", False),
        ("宋代", "沿置太子左监门率府率、副率", "职源", True),
        ("南宋", "备作环卫阶官", "职源", True),
    ))


def entry305():
    rate_pair(305, ((
        "宋真宗天禧二年（1018）",
        "殿直夏元亨任右监门率府副率并兼春坊谒者", None, True,
    ),))


def entry306():
    rate_pair(306, (
        ("隋文帝时", "始置太子左内率府率、副率", None, False),
        ("宋代（具体时间未载）", "宋沿置的东宫武官", None, True),
    ))


def entry307():
    # “嘉泰二年”已据原书第37页影像核对，并非OCR误识。
    rate_pair(307, ((
        "宋宁宗嘉泰二年（1202）",
        "宗子赵与谈授右内率府副率，为资善堂伴读", None, True,
    ),))


def link_rate_members():
    """总条逐一列举十率；用总条原文连接本批七个实例。"""
    i = 297
    main = F[i]["text"]
    w = W(i)
    group_tp = find_tp(w, "太子诸率府率、副率", "宋代（具体时间未载）")
    members = {
        "太子右司御率府率、副率": "宋代（具体时间未载）",
        "太子左清道率府率、副率": "宋太宗至道元年（995）",
        "太子右清道率府率、副率": "宋代（具体时间未载）",
        "太子左监门率府率、副率": "宋代",
        "太子右监门率府率、副率": "宋真宗天禧二年（1018）",
        "太子左内率府率、副率": "宋代（具体时间未载）",
        "太子右内率府率、副率": "宋宁宗嘉泰二年（1202）",
    }
    for title, time in members.items():
        relation(
            w, i, group_tp, find_tp(w, title, time), "统称与实例", main,
            f"总条逐一列明十率府，{title}为太子诸率府率、副率的实例。",
        )
    w.commit()


def entry308():
    i = 308
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    rank = field(i, "品位")
    w = W(i)
    entity_id = w.entity("公主", "官职", "正文定义公主为皇帝女封号。", quotation=main)
    timepoint(w, i, entity_id, "周朝中叶", "因同姓诸侯主天子女婚事而有公主之名", history, "建立公主名号起源节点。", "职源与沿革")
    timepoint(w, i, entity_id, "秦汉时期", "沿用公主名号，以帝女为公主", history, "建立秦汉沿用节点。", "职源与沿革")
    song_tp = timepoint(
        w, i, entity_id, "两宋（政和三年改称前）", "皇女封为公主",
        history, "建立宋代公主封号节点。", "职源与沿革",
        category="皇帝女封号", grade="秩视亲王，正一品",
    )
    rename_tp = timepoint(
        w, i, entity_id, "宋徽宗政和三年（1113）闰四月六日",
        "诏改公主为帝姬，公主称号停用", history,
        "建立公主改称帝姬节点。", "职源与沿革", category="改称",
    )
    restore_tp = timepoint(
        w, i, entity_id, "宋高宗建炎元年（1127）六月六日",
        "罢帝姬号，恢复公主称号", history,
        "建立建炎复称公主节点。", "职源与沿革",
        category="皇帝女封号", grade="秩视亲王，正一品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证公主为皇帝女封号。")
    cite(w, "Timepoints", song_tp, i, rank, "补证公主品位和封号规则。", "品位")
    cite(w, "Timepoints", restore_tp, i, rank, "补证复称后公主品位。", "品位")
    alias_citation(w, i, song_tp, "简称")

    imperial = w.entity("帝姬", "官职", "沿革字段明确公主改称帝姬。", quotation=history)
    imperial_start = timepoint(
        w, i, imperial, "宋徽宗政和三年（1113）闰四月六日",
        "由公主改称帝姬，开始施行", history,
        "建立帝姬称号开始节点。", "职源与沿革", category="皇帝女封号",
    )
    imperial_end = timepoint(
        w, i, imperial, "宋高宗建炎元年（1127）六月六日",
        "帝姬称号罢止，复称公主", history,
        "建立帝姬称号罢止节点。", "职源与沿革", category="废罢称号",
    )
    relation(w, i, rename_tp, imperial_start, "前后演变", history, "政和三年公主改称帝姬。", "职源与沿革")
    relation(w, i, imperial_end, restore_tp, "前后演变", history, "建炎元年帝姬复称公主。", "职源与沿革")
    w.commit()


def entry309():
    i = 309
    main = F[i]["text"]
    w = W(i)
    start = find_tp(w, "帝姬", "宋徽宗政和三年（1113）闰四月六日")
    end = find_tp(w, "帝姬", "宋高宗建炎元年（1127）六月六日")
    old_end = find_tp(w, "公主", "宋徽宗政和三年（1113）闰四月六日")
    restored = find_tp(w, "公主", "宋高宗建炎元年（1127）六月六日")
    cite(w, "Timepoints", start, i, main, "帝姬专条补证称号施行起点。")
    cite(w, "Timepoints", end, i, main, "帝姬专条补证称号施行终点。")
    relation(w, i, old_end, start, "前后演变", main, "帝姬专条补证公主改名为帝姬。")
    relation(w, i, end, restored, "前后演变", main, "帝姬专条的行用截止时间补证建炎复名。")
    w.commit()


def public_house(w, i):
    entity_id = w.entity(
        "公主宅", "机构", "公主宅官名及正文所称公主家共同证明该机构。",
        quotation=F[i]["text"],
    )
    return timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "公主居宅及家事务管理体系",
        F[i]["text"], "建立公主宅机构节点。", category="公主宅第机构",
    )


def house_post(i, event, officer_type):
    main = F[i]["text"]
    w = W(i)
    parent = public_house(w, i)
    entity_id = w.entity(F[i]["title"], "官职", f"正文定义{F[i]['title']}为差遣。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", event, main,
        f"建立{F[i]['title']}宋代节点。", category="公主宅差遣",
        officer_type=officer_type,
    )
    relation(
        w, i, parent, tp_id, "编制隶属", main,
        f"{F[i]['title']}在公主宅任事。", staff_type=officer_type,
    )
    w.commit()


def entry310():
    house_post(310, "由内侍充任，监管公主家事务", "内侍")


def entry311():
    house_post(311, "由内侍充任，主管公主家事务", "内侍")


def entry312():
    house_post(
        312,
        "由四十岁以上内侍与五十岁以上三班使臣充任，办理公主家事务，位次管勾官",
        "内侍、三班使臣（小武臣）",
    )


def entry313():
    house_post(313, "由十五岁以下小内侍充任，在公主家服侍", "小内侍")


def entry314():
    i = 314
    main = F[i]["text"]
    w = W(i)
    parent = public_house(w, i)
    entity_id = w.entity("帝姬宅教授", "官职", "正文定义帝姬宅教授为学官。", quotation=main)
    active = timepoint(
        w, i, entity_id, "北宋（具体时间未载）", "在公主宅教导训学",
        main, "建立帝姬宅教授北宋任职节点。", category="公主宅学官",
    )
    timepoint(
        w, i, entity_id, "宋钦宗靖康元年（1126）正月四日", "罢置",
        main, "建立帝姬宅教授罢置节点。", category="废罢官职",
    )
    relation(w, i, parent, active, "编制隶属", main, "帝姬宅教授于公主宅执教导训学之事。")
    w.commit()


def entry315():
    i = 315
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    rank = field(i, "品位")
    w = W(i)
    entity_id = w.entity("长公主", "官职", "正文定义长公主为皇帝姐妹封号。", quotation=main)
    timepoint(w, i, entity_id, "西汉时期", "长公主之名用于皇女中最长者", history, "建立长公主名称起源节点。", "职源与沿革")
    timepoint(w, i, entity_id, "东汉时期", "帝妹开始有长公主之封", history, "建立长公主用于帝妹节点。", "职源与沿革")
    song_tp = timepoint(
        w, i, entity_id, "宋代（政和三年改称前）", "皇帝姐妹封为长公主",
        main, "建立宋代长公主封号节点。", category="皇帝姐妹封号", grade="视真一品",
    )
    cite(w, "Timepoints", song_tp, i, rank, "补证长公主品位与封号规则。", "品位")
    alias_citation(w, i, song_tp, "简称")
    w.commit()


def entry316():
    i = 316
    main = F[i]["text"]
    w = W(i)
    old = find_entity(w, "长公主")
    old_end = timepoint(
        w, i, old, "宋徽宗政和三年（1113）闰四月", "长公主改称长帝姬",
        main, "据长帝姬专条建立长公主改称节点。", category="改称",
    )
    restored = timepoint(
        w, i, old, "宋高宗建炎元年（1127）六月", "长帝姬称号停用，恢复长公主之称",
        main, "据长帝姬专条施行终点建立复称节点。", category="皇帝姐妹封号", grade="视真一品",
    )
    renamed = w.entity("长帝姬", "官职", "正文明确长帝姬为长公主改名。", quotation=main)
    start = timepoint(
        w, i, renamed, "宋徽宗政和三年（1113）闰四月", "由长公主改称，开始施行",
        main, "建立长帝姬称号开始节点。", category="皇帝姐妹封号",
    )
    end = timepoint(
        w, i, renamed, "宋高宗建炎元年（1127）六月", "长帝姬称号停用，复称长公主",
        main, "建立长帝姬称号结束节点。", category="废罢称号",
    )
    relation(w, i, old_end, start, "前后演变", main, "政和三年长公主改称长帝姬。")
    relation(w, i, end, restored, "前后演变", main, "建炎元年长帝姬复称长公主。")
    w.commit()

    # 原书“长公主”条误作“大长帝姬/大长公主”，与专条直接冲突；保留冲突证据。
    history = field(315, "职源与沿革")
    w = W(315)
    cite(
        w, "Timepoints", old_end, 315, history,
        "保留长公主条与长帝姬专条冲突的原文，不据此建立错误演变。", "职源与沿革",
        note="本条误作改称大长帝姬、复称大长公主；演变以长帝姬专条为准",
        conflict_flag=1,
    )
    w.commit()


def entry317():
    i = 317
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("大长公主", "官职", "正文定义大长公主为皇帝姑封号。", quotation=main)
    timepoint(w, i, entity_id, "汉代", "帝姑封为大长公主", history, "建立大长公主汉制起源节点。", "职源与沿革")
    song_tp = timepoint(
        w, i, entity_id, "宋代（政和三年改称前）", "皇帝姑封为大长公主",
        main, "建立宋代大长公主封号节点。", category="皇帝姑封号", grade="正一品",
    )
    old_end = timepoint(
        w, i, entity_id, "宋徽宗政和三年（1113）闰四月", "改称大长帝姬",
        history, "建立大长公主改称节点。", "职源与沿革", category="改称",
    )
    restored = timepoint(
        w, i, entity_id, "宋高宗建炎元年（1127）六月", "恢复大长公主之名",
        history, "建立大长公主复称节点。", "职源与沿革", category="皇帝姑封号", grade="正一品",
    )
    cite(w, "Timepoints", song_tp, i, rank, "补证大长公主官品和封号规则。", "官品")
    alias_citation(w, i, song_tp, "简称")
    renamed = w.entity("大长帝姬", "官职", "沿革字段明确大长公主改称大长帝姬。", quotation=history)
    start = timepoint(
        w, i, renamed, "宋徽宗政和三年（1113）闰四月", "由大长公主改称，开始施行",
        history, "建立大长帝姬称号开始节点。", "职源与沿革", category="皇帝姑封号",
    )
    end = timepoint(
        w, i, renamed, "宋高宗建炎元年（1127）六月", "大长帝姬称号停用，复称大长公主",
        history, "建立大长帝姬称号结束节点。", "职源与沿革", category="废罢称号",
    )
    relation(w, i, old_end, start, "前后演变", history, "政和三年大长公主改称大长帝姬。", "职源与沿革")
    relation(w, i, end, restored, "前后演变", history, "建炎元年大长帝姬复称大长公主。", "职源与沿革")
    w.commit()


def entry318():
    i = 318
    main = F[i]["text"]
    w = W(i)
    start = find_tp(w, "大长帝姬", "宋徽宗政和三年（1113）闰四月")
    end = find_tp(w, "大长帝姬", "宋高宗建炎元年（1127）六月")
    old_end = find_tp(w, "大长公主", "宋徽宗政和三年（1113）闰四月")
    restored = find_tp(w, "大长公主", "宋高宗建炎元年（1127）六月")
    cite(w, "Timepoints", start, i, main, "大长帝姬专条补证称号开始。")
    cite(w, "Timepoints", end, i, main, "大长帝姬专条补证称号结束。")
    relation(w, i, old_end, start, "前后演变", main, "专条补证大长公主改名为大长帝姬。")
    relation(w, i, end, restored, "前后演变", main, "专条施行截止时间补证建炎复名。")
    w.commit()


def entry319():
    i = 319
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duties = field(i, "职能")
    w = W(i)
    entity_id = w.entity("郡主", "官职", "正文定义郡主为亲王女封号。", quotation=main)
    timepoint(w, i, entity_id, "汉代", "已有郡主之称，用于封功臣女", history, "建立郡主汉代起源节点。", "职源与沿革")
    timepoint(w, i, entity_id, "唐代", "皇太子女封郡主", history, "建立唐代郡主制度节点。", "职源与沿革")
    song_tp = timepoint(
        w, i, entity_id, "北宋（政和三年改称前）", "亲王女等封郡主",
        history, "建立北宋郡主封号节点。", "职源与沿革", category="亲王女封号",
    )
    old_end = timepoint(
        w, i, entity_id, "宋徽宗政和三年（1113）闰四月", "郡主改称宗姬",
        history, "建立郡主改称宗姬节点。", "职源与沿革", category="改称",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证郡主为亲王女封号。")
    cite(w, "Timepoints", song_tp, i, duties, "补证宋代郡主所封对象。", "职能")
    renamed = w.entity("宗姬", "官职", "沿革字段明确郡主改名宗姬。", quotation=history)
    start = timepoint(
        w, i, renamed, "宋徽宗政和三年（1113）闰四月", "由郡主改称，开始施行",
        history, "建立宗姬称号开始节点。", "职源与沿革", category="亲王女封号",
    )
    relation(w, i, old_end, start, "前后演变", history, "政和三年郡主改称宗姬。", "职源与沿革")
    w.commit()


def entry320():
    i = 320
    main = F[i]["text"]
    w = W(i)
    start = find_tp(w, "宗姬", "宋徽宗政和三年（1113）闰四月")
    cite(w, "Timepoints", start, i, main, "宗姬专条补证称号起点及来源。")
    renamed = find_entity(w, "宗姬")
    end = timepoint(
        w, i, renamed, "宋高宗建炎元年（1127）六月", "宗姬称号停止施行，复称郡主",
        main, "据宗姬专条的施行终点建立停用节点。", category="废罢称号",
    )
    restored = timepoint(
        w, i, find_entity(w, "郡主"), "宋高宗建炎元年（1127）六月", "宗姬停用，恢复郡主称号",
        main, "据宗姬行用截止时间建立郡主复称节点。", category="亲王女封号",
    )
    old_end = find_tp(w, "郡主", "宋徽宗政和三年（1113）闰四月")
    relation(w, i, old_end, start, "前后演变", main, "宗姬专条补证郡主改名为宗姬。")
    relation(w, i, end, restored, "前后演变", main, "宗姬施行至建炎元年六月，随后恢复郡主旧称。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(301, 321)] == [
        "太子右司御率府率、副率", "太子左清道率府率、副率", "太子右清道率府率、副率",
        "太子左监门率府率、副率", "太子右监门率府率、副率", "太子左内率府率、副率",
        "太子右内率府率、副率", "公主", "帝姬", "公主宅都监", "管勾公主宅事",
        "勾当公主宅事", "公主宅入位祗应", "帝姬宅教授", "长公主", "长帝姬",
        "大长公主", "大长帝姬", "郡主", "宗姬",
    ]
    entry301()
    entry302()
    entry303()
    entry304()
    entry305()
    entry306()
    entry307()
    link_rate_members()
    entry308()
    entry309()
    entry310()
    entry311()
    entry312()
    entry313()
    entry314()
    entry315()
    entry316()
    entry317()
    entry318()
    entry319()
    entry320()


if __name__ == "__main__":
    main()
