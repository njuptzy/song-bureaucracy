#!/usr/bin/env python3
"""提取第一编第341-360条：王府讲读官、南北宅及诸王宫宗学官。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
MERGED_DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)


def repair_dictionary_source():
    """据原书第41-43页修复#344 OCR及#345-346错误切分。"""
    marker = "皇侄、皇孙教授 "
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            row344 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=344"
            ).fetchone()
            row345 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=345"
            ).fetchone()
            row346 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=346"
            ).fetchone()
            assert row344 and row345 and row346

            fields344 = json.loads(row344[0] or "{}")
            short = fields344["简称"]
            if "人为皇子，即拜说书" in short:
                fields344["简称"] = short.replace(
                    "人为皇子，即拜说书", "入为皇子，即拜说书"
                )
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=344",
                    (json.dumps(fields344, ensure_ascii=False),),
                )
            else:
                assert "入为皇子，即拜说书" in short, short

            if not row346[1]:
                assert row345[0] == "皇子位伴读", row345[0]
                assert marker in row345[1], row345[1]
                text345, text346 = row345[1].split(marker, 1)
                assert row345[2], row345
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=NULL WHERE id=345",
                    (text345.rstrip(),),
                )
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=346",
                    ("皇侄、皇孙教授", text346, row345[2]),
                )
            else:
                assert row346[0] == "皇侄、皇孙教授", row346[0]
                assert row345[2] is None, row345[2]
                assert row346[2], row346
                assert marker not in row345[1], row345[1]


repair_dictionary_source()


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


F = {i: load(i) for i in range(341, 361)}


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
    return w.citation(table, target_id, C(i, name), quotation, decision, **kwargs)


def timepoint(
    w, i, entity_id, time, event, quotation, decision, name=None,
    category=None, officer_type=None, grade=None, chain="tail",
    citation_kwargs=None,
):
    target_id = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer_type,
        attr_grade=grade, chain=chain,
    )
    cite(
        w, "Timepoints", target_id, i, quotation, decision, name,
        **(citation_kwargs or {}),
    )
    return target_id


def relation(
    w, i, subject, object_, kind, quotation, decision, name=None,
    staff_type=None, staff_quota=None, citation_kwargs=None,
):
    target_id = w.relationship(
        subject, object_, kind, decision, quotation,
        staff_type=staff_type, staff_quota=staff_quota,
    )
    cite(
        w, "Relationships", target_id, i, quotation, decision, name,
        **(citation_kwargs or {}),
    )
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


def palace(w):
    return find_tp(w, "亲王府", "宋代（具体时间未载）", "机构")


def palace_group(w):
    return find_tp(w, "亲王府官属", "宋代（具体时间未载）")


def palace_member(w, i, tp_id, quotation, name=None):
    relation(
        w, i, palace(w), tp_id, "编制隶属", quotation,
        f"{F[i]['title']}为亲王府官属。", name,
    )
    relation(
        w, i, palace_group(w), tp_id, "统称与实例", quotation,
        f"亲王府官属为统称，{F[i]['title']}为具体实例。", name,
    )


def institution(w, i, title, time, event, quotation, decision, name=None):
    entity_id = w.entity(title, "机构", decision, quotation=quotation)
    return timepoint(
        w, i, entity_id, time, event, quotation, decision, name,
        category="宗室教育机构",
    )


def entry341():
    i = 341
    main = F[i]["text"]
    short = field(i, "简称")
    w = W(i)
    entity_id = find_entity(w, "亲王府直讲")
    start = timepoint(
        w, i, entity_id, "宋徽宗政和七年（1117）", "由亲王府侍讲改称",
        main, "亲王府直讲专条补证政和改称节点。", category="亲王府官属", grade="从七品",
    )
    timepoint(
        w, i, entity_id, "南宋", "沿用亲王府直讲之名不变",
        main, "建立南宋沿用亲王府直讲节点。", category="亲王府官属", grade="从七品",
    )
    alias_citation(w, i, start, "简称")
    relation(
        w, i, find_tp(w, "亲王府侍讲", "宋徽宗政和七年（1117）"),
        start, "前后演变", main, "专条补证政和七年侍讲改称直讲。",
    )
    palace_member(w, i, start, short, "简称")
    w.commit()


def entry342():
    i = 342
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = find_entity(w, "亲王府侍读")
    # 上批总条先建了宋代泛称节点；按倒序链首前插，保持南齐→979→宋代泛称。
    song_start = timepoint(
        w, i, entity_id, "宋太宗太平兴国四年（979）", "宋代始置，讲读经史，职在训导",
        origin, "建立宋代亲王府侍读始置节点。", "职源", category="亲王府官属", grade="从七品", chain="head",
    )
    timepoint(
        w, i, entity_id, "南齐时期", "始置王府侍读",
        origin, "建立亲王府侍读职源节点。", "职源", chain="head",
    )
    cite(w, "Timepoints", song_start, i, field(i, "职掌"), "补证亲王府侍读职掌。", "职掌")
    cite(w, "Timepoints", song_start, i, field(i, "品位"), "补证亲王府侍读官品和服色待遇。", "品位")
    palace_member(w, i, song_start, origin, "职源")
    w.commit()


def entry343():
    i = 343
    main = F[i]["text"]
    short = field(i, "简称")
    w = W(i)
    old = find_entity(w, "亲王府侍读")
    old_end = timepoint(
        w, i, old, "宋徽宗政和七年（1117）八月", "改称亲王府赞读",
        main, "建立亲王府侍读改称赞读节点。", category="改称",
    )
    entity_id = w.entity("亲王府赞读", "官职", "正文明确赞读由亲王府侍读改名。", quotation=main)
    start = timepoint(
        w, i, entity_id, "宋徽宗政和七年（1117）八月", "由亲王府侍读改称",
        main, "建立亲王府赞读开始节点。", category="亲王府官属", grade="从七品",
    )
    timepoint(
        w, i, entity_id, "南宋", "沿用亲王府赞读之名不变",
        main, "建立南宋沿用赞读节点。", category="亲王府官属", grade="从七品",
    )
    alias_citation(w, i, start, "简称")
    relation(w, i, old_end, start, "前后演变", main, "政和七年八月亲王府侍读改称赞读。")
    palace_member(w, i, start, short, "简称")
    w.commit()


def ensure_prince_position(w, i, quotation):
    return institution(
        w, i, "皇子位", "宋仁宗嘉祐七年（1062）八月",
        "赵曙立为皇子后建立皇子位，设置说书、伴读等学官",
        quotation, "建立皇子位及其讲学编制节点。",
    )


def entry344():
    i = 344
    main = F[i]["text"]
    w = W(i)
    parent = ensure_prince_position(w, i, main)
    entity_id = w.entity("皇子位说书", "官职", "正文定义皇子位说书为未封王皇子学官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋仁宗嘉祐七年（1062）八月", "始置，为未封王皇子讲学",
        main, "建立皇子位说书始置节点。", category="皇子位学官",
    )
    alias_citation(w, i, tp_id, "简称")
    relation(w, i, parent, tp_id, "编制隶属", main, "皇子位说书为皇子位所设学官。")
    w.commit()


def entry345():
    i = 345
    main = F[i]["text"]
    w = W(i)
    parent = ensure_prince_position(w, i, main)
    entity_id = w.entity("皇子位伴读", "官职", "正文定义皇子位伴读为未封王皇子学官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋仁宗嘉祐七年（1062）八月", "始置，为未封王皇子伴读",
        main, "建立皇子位伴读始置节点。", category="皇子位学官",
    )
    relation(w, i, parent, tp_id, "编制隶属", main, "皇子位伴读为皇子位所设学官。")
    w.commit()


def entry346():
    i = 346
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity("皇侄、皇孙教授", "官职", "修复后的正文定义其为宗室学官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋太宗至道元年（995）正月",
        "始置，凡王亲年幼未封公、封王而带环卫阶者，其学官称教授，以别于太子侍读",
        origin, "建立皇侄、皇孙教授始置节点。", "职源", category="宗室学官",
    )
    cite(w, "Timepoints", tp_id, i, main, "补证皇侄、皇孙教授的任教对象。")
    alias_citation(w, i, tp_id, "别名")
    w.commit()


def ensure_muqin(w, i, quotation, name=None):
    return institution(
        w, i, "睦亲宅", "宋真宗咸平元年（998）正月八日",
        "又称南宅，为太祖、太宗诸亲王子孙聚居所，并置教授",
        quotation, "建立睦亲宅（南宅）机构节点。", name,
    )


def ensure_guangqin(w, i, quotation):
    return institution(
        w, i, "广亲宅", "宋真宗咸平元年（998）正月八日",
        "又称北宅，为魏悼王廷美子孙聚居所，并置教授",
        quotation, "建立广亲宅（北宅）机构节点。",
    )


def school_post(i, title, parent_func, time, event, aliases=None, duties=None, officer_type=None):
    main = F[i]["text"]
    w = W(i)
    parent = parent_func(w, i, main)
    entity_id = w.entity(title, "官职", f"正文定义{title}为宗学学官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, time, event, main,
        f"建立{title}始置节点。", category="宗学学官", officer_type=officer_type,
    )
    if duties:
        cite(w, "Timepoints", tp_id, i, field(i, duties), f"补证{title}职掌。", duties)
    if aliases:
        alias_citation(w, i, tp_id, aliases)
    relation(
        w, i, parent, tp_id, "编制隶属", main,
        f"{title}为{('睦亲宅' if parent_func is ensure_muqin else '广亲宅')}学官。",
        staff_type=officer_type,
    )
    w.commit()


def entry347():
    school_post(
        347, "南宅教授", ensure_muqin, "宋真宗咸平元年（998）正月八日",
        "始置，由王府讲读官兼充", "别名", officer_type="王府讲读官兼充",
    )


def entry348():
    school_post(
        348, "北宅教授", ensure_guangqin, "宋真宗咸平元年（998）正月八日",
        "始置，由王府讲读官兼充", "别名", officer_type="王府讲读官兼充",
    )


def entry349():
    school_post(
        349, "南宫侍教", ensure_muqin, "宋真宗咸平四年（1001）九月",
        "始置，为环卫官以下王子族人讲读经史", duties="职掌",
    )


def entry350():
    school_post(
        350, "北宅侍讲", ensure_guangqin, "宋真宗大中祥符二年（1009）二月",
        "始见置，为环卫官大将军以下王子族属讲读经史", duties="职掌",
    )


def entry351():
    i = 351
    main = F[i]["text"]
    aliases = field(i, "简称与别名")
    w = W(i)
    group = w.entity("南、北宅伴读", "官职", "正文定义其为南北宅伴读合称。", quotation=main)
    group_tp = timepoint(
        w, i, group, "宋真宗咸平年间（998—1003）", "南宅与北宅伴读合称，无定数",
        main, "建立南、北宅伴读统称节点。", category="宗学学官统称",
    )
    alias_citation(w, i, group_tp, "简称与别名")
    for title, time, parent_func in (
        ("南宅伴读", "宋真宗咸平元年（998）", ensure_muqin),
        ("北宅伴读", "宋真宗咸平五年（1002）正月", ensure_guangqin),
    ):
        child = w.entity(title, "官职", f"正文分别记载{title}始见时间。", quotation=main)
        child_tp = timepoint(
            w, i, child, time, "始见设置，陪伴宗子讲读经史",
            main, f"建立{title}始见节点。", category="宗学学官",
        )
        relation(w, i, group_tp, child_tp, "统称与实例", main, f"南、北宅伴读为合称，{title}为实例。")
        relation(w, i, parent_func(w, i, main), child_tp, "编制隶属", aliases, f"{title}为相应宅院学官。", "简称与别名")
    w.commit()


def entry352():
    i = 352
    main = F[i]["text"]
    w = W(i)
    group = w.entity("南、北宅讲书", "官职", "正文定义其为南北宅讲书合称。", quotation=main)
    group_tp = timepoint(
        w, i, group, "宋英宗治平元年（1064）六月五日", "始置，教授三十岁以上南、北宅宗子",
        main, "建立南、北宅讲书始置节点。", category="宗学学官统称",
    )
    alias_citation(w, i, group_tp, "简称")
    for title, parent_func in (("南宅讲书", ensure_muqin), ("北宅讲书", ensure_guangqin)):
        child = w.entity(title, "官职", f"合称词头明确包含{title}。", quotation=main)
        child_tp = timepoint(
            w, i, child, "宋英宗治平元年（1064）六月五日", "始置，教授三十岁以上宗子",
            main, f"建立{title}节点。", category="宗学学官",
        )
        relation(w, i, group_tp, child_tp, "统称与实例", main, f"南、北宅讲书为合称，{title}为实例。")
        relation(w, i, parent_func(w, i, main), child_tp, "编制隶属", main, f"{title}为相应宅院学官。")
    w.commit()


def entry353():
    i = 353
    main = F[i]["text"]
    w = W(i)
    parent = institution(
        w, i, "亲贤宅", "南宋绍兴初", "英宗赵曙子孙聚居宅院，设置教授后改讲书",
        main, "建立亲贤宅机构节点。",
    )
    professor = w.entity("亲贤宅教授", "官职", "正文明确亲贤宅讲书由亲贤宅教授改名。", quotation=main)
    professor_end = timepoint(
        w, i, professor, "南宋绍兴初", "改称亲贤宅讲书",
        main, "建立亲贤宅教授改称节点。", category="改称",
    )
    lecture = w.entity("亲贤宅讲书", "官职", "正文定义亲贤宅讲书为宗子学官。", quotation=main)
    lecture_start = timepoint(
        w, i, lecture, "南宋绍兴初", "由亲贤宅教授改称，教授英宗近属子弟",
        main, "建立亲贤宅讲书开始节点。", category="宗学学官",
    )
    lecture_end = timepoint(
        w, i, lecture, "宋高宗绍兴十二年（1142）", "改称王府教授",
        main, "建立亲贤宅讲书改称节点。", category="改称",
    )
    generic = find_entity(w, "亲王府教授")
    generic_tp = timepoint(
        w, i, generic, "宋高宗绍兴十二年（1142）", "由亲贤宅讲书改称王府教授",
        main, "建立王府教授绍兴十二年节点。", category="亲王府官属",
    )
    relation(w, i, professor_end, lecture_start, "前后演变", main, "绍兴初亲贤宅教授改名讲书。")
    relation(w, i, lecture_end, generic_tp, "前后演变", main, "绍兴十二年亲贤宅讲书复改王府教授。")
    relation(w, i, parent, lecture_start, "编制隶属", main, "亲贤宅讲书为亲贤宅学官。")
    w.commit()


def entry354():
    i = 354
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    parent = ensure_muqin(w, i, field(i, "职掌"), "职掌")
    entity_id = w.entity("睦亲宅小学教授", "官职", "正文定义其为宗子学官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋英宗治平元年（1064）六月五日", "始置，教训十四岁以下宗子",
        origin, "建立睦亲宅小学教授始置节点。", "职源", category="宗学学官",
    )
    cite(w, "Timepoints", tp_id, i, field(i, "职掌"), "补证小学教授职掌。", "职掌")
    alias_citation(w, i, tp_id, "简称")
    relation(w, i, parent, tp_id, "编制隶属", field(i, "职掌"), "睦亲宅小学教授为睦亲宅学官。", "职掌")
    w.commit()


def entry355():
    i = 355
    main = F[i]["text"]
    w = W(i)
    parent = ensure_guangqin(w, i, main)
    entity_id = w.entity("广亲宅小学教授", "官职", "正文定义其为宗子学官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋英宗治平元年（1064）六月五日", "依睦亲宅小学教授制度，教训十四岁以下宗子",
        main, "建立广亲宅小学教授节点。", category="宗学学官",
    )
    relation(w, i, parent, tp_id, "编制隶属", main, "广亲宅小学教授为广亲宅学官。")
    w.commit()


def entry356():
    i = 356
    main = F[i]["text"]
    w = W(i)
    group = w.entity("诸王宫大学、小学", "机构", "正文定义诸王宫大学、小学为宗学。", quotation=main)
    group_tp = timepoint(
        w, i, group, "宋哲宗元祐六年（1091）", "逐宫院分置大学、小学；十至十九岁入小学，二十岁以上入大学",
        main, "建立诸王宫大学、小学分置节点。", category="宗室教育机构",
    )
    alias_citation(w, i, group_tp, "省称")
    for title, event in (
        ("诸王宫大学", "分置大学，收二十岁以上宗子"),
        ("诸王宫小学", "分置小学，收十至十九岁宗子"),
    ):
        entity_id = find_entity(w, title, "机构")
        child_tp = timepoint(
            w, i, entity_id, "宋哲宗元祐六年（1091）", event,
            main, f"补建{title}元祐六年始置节点。", chain="head", category="宗室教育机构",
        )
        relation(w, i, group_tp, child_tp, "统称与实例", main, f"诸王宫大学、小学为合称，{title}为其中一学。")
    w.commit()


def entry357():
    i = 357
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("诸宫院大学教授", "官职", "词头及正文确定大学教授为宗学学官。", quotation=main)
    start = timepoint(
        w, i, entity_id, "宋英宗治平元年（1064）", "宫院教授与小学教授分置，原教授相对视为大学教授",
        main, "建立诸宫院大学教授制度起点。", category="宗学学官",
    )
    timepoint(
        w, i, entity_id, "宋英宗治平四年（1067）", "诏文正式并称诸宫院大、小学教授",
        main, "建立治平四年正式称名节点。", category="宗学学官",
    )
    relation(
        w, i, find_tp(w, "诸王宫大学、小学", "宋哲宗元祐六年（1091）", "机构"),
        start, "编制隶属", main, "诸宫院大学教授为诸王宫大学、小学体系中的大学学官。",
    )
    w.commit()


def entry358():
    i = 358
    main = F[i]["text"]
    w = W(i)
    entity_id = find_entity(w, "诸王宫大、小学教授")
    # 既有链首为崇宁四年；倒序前插崇宁三年、治平四年，保持全局链有序。
    timepoint(
        w, i, entity_id, "宋徽宗崇宁三年（1104）", "大学教授开始可兼小学教授",
        main, "补建崇宁三年兼任制度节点。", category="宗学学官", chain="head",
    )
    start = timepoint(
        w, i, entity_id, "宋英宗治平四年（1067）", "诸宫院大、小学教授已见于诏文，后成为在京宗子学官总名",
        main, "补建诸王宫大、小学教授早期节点。", category="宗学学官", grade="正八品", chain="head",
    )
    cite(w, "Timepoints", start, i, field(i, "官品"), "补证诸王宫大、小学教授官品。", "官品")
    alias_citation(w, i, start, "简称与别名")
    parent = find_tp(w, "诸王宫大学、小学", "宋哲宗元祐六年（1091）", "机构")
    relation(w, i, parent, start, "编制隶属", main, "诸王宫大、小学教授为诸王宫大学、小学学官总名。")
    for title, time in (
        ("诸宫院大学教授", "宋英宗治平元年（1064）"),
        ("睦亲宅小学教授", "宋英宗治平元年（1064）六月五日"),
        ("广亲宅小学教授", "宋英宗治平元年（1064）六月五日"),
    ):
        relation(
            w, i, start, find_tp(w, title, time), "统称与实例", main,
            f"诸王宫大、小学教授为总名，{title}为具体宫院学官。",
        )
    w.commit()


def entry359():
    i = 359
    main = F[i]["text"]
    w = W(i)
    professor = find_entity(w, "诸王宫大、小学教授")
    old_1105 = find_tp(w, "诸王宫大、小学教授", "北宋崇宁四年")
    old_1134 = find_tp(w, "诸王宫大、小学教授", "南宋绍兴四年")
    old_1216 = find_tp(w, "诸王宫大、小学教授", "南宋嘉定九年")
    # 本条作崇宁五年，旧源作崇宁四年。增加并行时间证据并接入完整链。
    alt = timepoint(
        w, i, professor, "宋徽宗崇宁五年（1106）", "本条记为改名某王宫宗子博士，与崇宁四年记载相差一年",
        main, "保留崇宁五年改名的异文节点。", chain="none", category="改称",
        citation_kwargs={"note":"与既有史源所载崇宁四年相差一年", "conflict_flag":1},
    )
    w.relink(old_1105, succ_id=alt, decision="在崇宁四年与绍兴四年之间接入崇宁五年异文节点")
    w.relink(alt, prev_id=old_1105, succ_id=old_1134, decision="接入诸王宫大、小学教授全局时间链")
    w.relink(old_1134, prev_id=alt, decision="绍兴四年节点前接崇宁五年异文节点")

    entity_id = w.entity("某王宫宗子博士", "官职", "正式词头及正文明确为诸王宫大、小学教授改名。", quotation=main)
    start = timepoint(
        w, i, entity_id, "宋徽宗崇宁五年（1106）", "由诸王宫大、小学教授改称",
        main, "建立某王宫宗子博士改称节点。", category="宗学学官",
        citation_kwargs={"note":"改名年份与既有崇宁四年史源相差一年"},
    )
    end = timepoint(
        w, i, entity_id, "宋钦宗靖康年间（1126—1127）", "废辍，后复称诸王宫大、小学教授",
        main, "建立靖康间废辍节点。", category="废罢官职",
    )
    later = timepoint(
        w, i, entity_id, "宋宁宗嘉定九年（1216）", "再次改称宗子博士，同时仍存诸王宫大、小学教授一员",
        main, "建立嘉定九年再置节点。", category="宗学学官",
    )
    relation(
        w, i, alt, start, "前后演变", main, "本条记崇宁五年教授改名某王宫宗子博士。",
        citation_kwargs={"note":"与既有崇宁四年改名史源相差一年"},
    )
    relation(w, i, end, old_1134, "前后演变", main, "靖康废辍后，绍兴四年复称诸王宫大、小学教授。")
    relation(w, i, old_1216, later, "前后演变", main, "嘉定九年又改称宗子博士，同时保留教授一员。")
    w.commit()


def entry360():
    i = 360
    main = F[i]["text"]
    w = W(i)
    parent = ensure_muqin(w, i, main)
    entity_id = w.entity("睦亲宅都讲", "官职", "正文定义睦亲宅都讲为宗学官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋英宗治平元年（1064）六月", "始置，为宗子学讲官，位教授上",
        main, "建立睦亲宅都讲始置节点。", category="宗学学官",
    )
    relation(w, i, parent, tp_id, "编制隶属", main, "睦亲宅都讲为睦亲宅宗学讲官。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(341, 361)] == [
        "亲王府直讲", "亲王府侍读", "亲王府赞读", "皇子位说书", "皇子位伴读",
        "皇侄、皇孙教授", "南宅教授", "北宅教授", "南宫侍教", "北宅侍讲",
        "南、北宅伴读", "南、北宅讲书", "亲贤宅讲书", "睦亲宅小学教授",
        "广亲宅小学教授", "诸王宫大学、小学", "诸宫院大学教授",
        "诸王宫大、小学教授", "某王宫宗子博士", "睦亲宅都讲",
    ]
    entry341()
    entry342()
    entry343()
    entry344()
    entry345()
    entry346()
    entry347()
    entry348()
    entry349()
    entry350()
    entry351()
    entry352()
    entry353()
    entry354()
    entry355()
    entry356()
    entry357()
    entry358()
    entry359()
    entry360()


if __name__ == "__main__":
    main()
