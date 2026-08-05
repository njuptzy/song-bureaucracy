#!/usr/bin/env python3
"""提取第一编第261-280条：春坊差遣、东宫僚属与讲读体系。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
MERGED_DICT_DB = os.path.join(
    ROOT, "data/database/song_bureaucracy_dictionary_ch1t7.db"
)
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)


def repair_dictionary_source():
    """据原书第31-32、34页修复跨页续文和一处正文 OCR。"""
    placeholder = json.dumps(
        {
            "_placeholder": True,
            "__status__": "placeholder",
            "reason": "原目录项实际为第261条简称字段跨页续文，原书无独立词条",
        },
        ensure_ascii=False,
    )
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            row261 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=261"
            ).fetchone()
            row262 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=262"
            ).fetchone()
            row277 = conn.execute(
                f"SELECT title,text FROM {table} WHERE id=277"
            ).fetchone()
            assert row261 and row261[0] == "管勾左、右春坊事", row261
            assert row262 and row262[0] == "左、右春坊", row262
            assert row277 and row277[0] == "太子侍读", row277

            fields261 = json.loads(row261[2] or "{}")
            short = fields261.get("简称", "")
            if row262[1]:
                assert short.endswith("②主管"), short
                assert row262[1].startswith("事。南宋避高宗讳"), row262[1]
                fields261["简称"] = short + row262[0] + row262[1]
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=261",
                    (json.dumps(fields261, ensure_ascii=False),),
                )
                conn.execute(
                    f"UPDATE {table} SET text='',fields=? WHERE id=262",
                    (placeholder,),
                )
            else:
                assert "②主管左、右春坊事。南宋避高宗讳" in short, short
                status = json.loads(row262[2] or "{}")
                assert status.get("__status__") == "placeholder", status

            if row277[1] == "东官官名。":
                conn.execute(
                    f"UPDATE {table} SET text='东宫官名。' WHERE id=277"
                )
            else:
                assert row277[1] == "东宫官名。", row277[1]


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


F = {i: load(i) for i in range(261, 281)}


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


def alias_citation(w, i, tp_id, name="简称"):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；不另建称谓实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def east_group(w, i, tp_id, quotation):
    return relation(
        w, i, find_tp(w, "东宫官", "宋代"), tp_id,
        "统称与实例", quotation,
        f"东宫官为总称，{F[i]['title']}为具体东宫官或官类。",
    )


def spring_office(w):
    return find_tp(
        w, "皇太子宫左、右春坊司", "宋代（具体时间未载）", "机构"
    )


def palace(w):
    return find_tp(w, "皇太子宫", "宋代（具体时间未载）", "机构")


def entry261():
    i = 261
    main = F[i]["text"]
    names = field(i, "简称")
    w = W(i)
    entity_id = w.entity(
        "管勾左、右春坊事", "官职", "正文定义其为北宋皇太子宫差遣官。", quotation=main
    )
    old_tp = timepoint(
        w, i, entity_id, "北宋神宗升储时（具体年月未载）",
        "由内侍兼充，地位高于勾当左、右春坊事",
        main, "建立管勾左、右春坊事的北宋见置节点。",
        category="东宫差遣官", officer_type="内侍",
    )
    current = w.entity(
        "主管左、右春坊事", "官职",
        "简称字段明载南宋避高宗讳，管勾改称主管。", quotation=names,
    )
    current_tp = timepoint(
        w, i, current, "南宋",
        "避高宗讳，由管勾左、右春坊事改称；乾道七年皇太子府置二员",
        names, "建立南宋主管左、右春坊事改称节点。", "简称",
        category="东宫差遣官", officer_type="内侍",
    )
    relation(
        w, i, old_tp, current_tp, "前后演变", names,
        "南宋避高宗讳，管勾左、右春坊事改称主管左、右春坊事。", "简称",
    )
    relation(
        w, i, spring_office(w), old_tp, "编制隶属", main,
        "管勾左、右春坊事为皇太子宫左、右春坊司差遣官。",
        staff_type="内侍",
    )
    relation(
        w, i, spring_office(w), current_tp, "编制隶属", names,
        "主管左、右春坊事为南宋皇太子宫左、右春坊司差遣官。", "简称",
        staff_type="内侍", staff_quota="二员",
    )
    cite(
        w, "Timepoints", old_tp, i, names,
        "补证管勾省称及南宋避讳改称。", "简称",
        note="管勾为省称；左、右春坊亦可省称本差遣",
    )
    w.commit()


def entry262():
    assert not F[262]["text"]
    assert F[262]["fields"].get("__status__") == "placeholder"


def entry263():
    i = 263
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "同主管左、右春坊事", "官职", "正文定义其为武臣差充主管时所带称谓。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "南宋（具体时间未载）",
        "武臣差充主管左、右春坊事时带同字",
        main, "原文未载确切年月，建立同主管差遣节点。",
        category="东宫差遣官", officer_type="武臣",
    )
    alias_citation(w, i, tp_id)
    relation(
        w, i, find_tp(w, "主管左、右春坊事", "南宋"), tp_id,
        "统称与实例", main,
        "主管左、右春坊事为基本差遣，同主管为武臣兼充时的具体称谓。",
    )
    relation(
        w, i, spring_office(w), tp_id, "编制隶属", main,
        "同主管左、右春坊事为左右春坊司差遣官。", staff_type="武臣",
    )
    w.commit()


def entry264():
    i = 264
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "提举左、右春坊事", "官职", "正文定义其为北宋皇太子宫差遣官。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "北宋立皇太子期间（具体年月未载）",
        "由内侍兼充，位高于管勾左、右春坊事；立储时置、即位省罢",
        main, "建立提举左、右春坊事的条件性设罢节点。",
        category="东宫差遣官", officer_type="内侍",
    )
    alias_citation(w, i, tp_id)
    relation(
        w, i, spring_office(w), tp_id, "编制隶属", main,
        "提举左、右春坊事为左右春坊司高位差遣官。", staff_type="内侍",
    )
    w.commit()


def entry265():
    i = 265
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    w = W(i)
    entity_id = w.entity(
        "左、右春坊谒者", "官职", "正文定义其为皇太子宫差遣官。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋太宗至道元年（995）八月",
        "始置，主要由内侍充任，偶以士人担任；掌导引、传宣通报",
        origin, "建立左、右春坊谒者始置节点。", "职源",
        category="东宫差遣官", officer_type="内侍（偶以士人）",
    )
    cite(w, "Timepoints", tp_id, i, main, "补证春坊谒者的差遣官性质及充任者。")
    cite(w, "Timepoints", tp_id, i, duties, "补证春坊谒者职掌。", "职掌")
    alias_citation(w, i, tp_id)
    relation(
        w, i, spring_office(w), tp_id, "编制隶属", main,
        "左、右春坊谒者为皇太子宫左右春坊差遣官。",
        staff_type="内侍（偶以士人）",
    )
    w.commit()


def palace_temp_post(i, event, officer_type="内侍"):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为皇太子宫差遣官。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代立皇太子期间（具体年月未载）",
        event, main, f"建立{F[i]['title']}的临时差遣节点。",
        category="东宫差遣官", officer_type=officer_type,
    )
    if F[i]["fields"]:
        alias_citation(w, i, tp_id)
    relation(
        w, i, palace(w), tp_id, "编制隶属", main,
        f"{F[i]['title']}为皇太子宫差遣官。", staff_type=officer_type,
    )
    w.commit()


def entry266():
    palace_temp_post(266, "临时设置、皇太子登位即罢，掌皇太子府庶务监督")


def entry267():
    palace_temp_post(267, "临时设置、皇太子登位即罢，位低于太子宫都监，备听差干事")


def entry268():
    palace_temp_post(268, "临时设置，承受传宣旨意并实际管辖东宫事务，位在主管左右春坊官之上")


def paired_east_office(
    i, group_title, origin_points, song_time, song_event, reform_event,
    old_grade, new_grade, child_titles, child_event, later_points=(),
):
    main = F[i]["text"]
    origin_name = "职源与沿革" if "职源与沿革" in F[i]["fields"] else "职源"
    origin = field(i, origin_name)
    duties = field(i, "职掌")
    rank_name = "官品"
    rank = field(i, rank_name)
    staffing = field(i, "编制") if "编制" in F[i]["fields"] else None
    w = W(i)
    entity_id = w.entity(
        group_title, "官职", f"正文定义{group_title}为东宫官属。", quotation=main
    )
    for time, event in origin_points:
        timepoint(
            w, i, entity_id, time, event, origin,
            f"建立{group_title}前代职源节点。", origin_name,
        )
    song_tp = timepoint(
        w, i, entity_id, song_time, song_event,
        duties, f"建立{group_title}宋代制度节点。", "职掌",
        category="东宫官", grade=old_grade,
    )
    reform_tp = timepoint(
        w, i, entity_id, "北宋元丰改制后", reform_event,
        rank, f"建立{group_title}元丰改制后官品节点。", rank_name,
        category="东宫官", grade=new_grade,
    )
    for time, event in later_points:
        assert staffing
        timepoint(
            w, i, entity_id, time, event, staffing,
            f"建立{group_title}南宋编制节点。", "编制",
            category="东宫官", grade=new_grade,
        )
    cite(w, "Timepoints", song_tp, i, main, f"补证{group_title}为东宫官属。")
    cite(w, "Timepoints", song_tp, i, rank, f"补证{group_title}宋初官品。", rank_name)
    if staffing:
        cite(w, "Timepoints", reform_tp, i, staffing, f"补证{group_title}编制。", "编制")
    alias_citation(w, i, song_tp)
    east_group(w, i, song_tp, main)

    for title in child_titles:
        child = w.entity(
            title, "官职", f"简称与编制字段明确列出{title}。",
            quotation=field(i, "简称"),
        )
        child_tp = timepoint(
            w, i, child, "宋代（具体时间未载）", child_event,
            duties, f"建立{title}的宋代节点。", "职掌",
            category="东宫官",
        )
        relation(
            w, i, song_tp, child_tp, "统称与实例", field(i, "简称"),
            f"{group_title}为并称，{title}为其中一职。", "简称",
        )
    w.commit()


def entry269():
    paired_east_office(
        269, "太子左、右庶子",
        (("三代时期", "已有庶子之名"),
         ("汉代", "置太子庶子"),
         ("隋代", "始分太子左庶子、太子右庶子")),
        "宋初",
        "立储时随宜设置、无定员，多为兼官，或轮值、代讲经史",
        "官品由正四品上改为从五品",
        "正四品上", "从五品",
        ("太子左庶子", "太子右庶子"),
        "立储时随宜设置，多为兼官，轮流入宫值班或代讲经史",
        (("南宋孝宗乾道年间", "仅置太子左庶子，不置右庶子"),
         ("南宋孝宗淳熙年间", "复置太子左、右庶子各一员")),
    )


def entry270():
    paired_east_office(
        270, "太子左、右谕德",
        (("唐高宗龙朔二年（662）", "始置太子左、右谕德"),),
        "宋初",
        "立储时设置、登位即罢，多为兼官，轮值或代讲经史",
        "官品由正四品下改为正六品，南宋不变",
        "正四品下", "正六品",
        ("太子左谕德", "太子右谕德"),
        "立储时设置，多为兼官，轮流入宫值班或代讲经史",
        (("南宋孝宗乾道以后", "仅置太子左谕德一人，不置右谕德"),),
    )


def ordinary_east_office(
    i, origin_points, song_time, song_event, grade_name, old_grade,
    reform=None, later=(),
):
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, grade_name)
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为东宫官属。", quotation=main
    )
    for time, event in origin_points:
        timepoint(w, i, entity_id, time, event, origin, f"建立{F[i]['title']}职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, song_time, song_event,
        duties, f"建立{F[i]['title']}宋代节点。", "职掌",
        category="东宫官", grade=old_grade,
    )
    if reform:
        timepoint(
            w, i, entity_id, "北宋元丰改制后", reform[0], rank,
            f"建立{F[i]['title']}元丰改制后官品节点。", grade_name,
            category="东宫官", grade=reform[1],
        )
    for time, event, source_name in later:
        q = field(i, source_name)
        timepoint(
            w, i, entity_id, time, event, q,
            f"建立{F[i]['title']}明确见任或职掌节点。", source_name,
            category="东宫官", grade=reform[1] if reform else old_grade,
        )
    cite(w, "Timepoints", song_tp, i, main, f"补证{F[i]['title']}为东宫官属。")
    cite(w, "Timepoints", song_tp, i, rank, f"补证{F[i]['title']}官品。", grade_name)
    alias_citation(w, i, song_tp)
    east_group(w, i, song_tp, main)
    w.commit()


def entry271():
    ordinary_east_office(
        271, (("西晋咸宁四年（278）", "始置太子中舍人"),),
        "宋前期", "兼作文臣迁转本官阶及立储时无实职的东宫官属",
        "官品", "正五品上", ("官品改为从七品", "从七品"),
    )


def entry272():
    ordinary_east_office(
        272, (("西汉时期", "已有太子舍人"),),
        "宋初", "立储时备东宫官僚，多由他官兼任",
        "品位", "正六品上", ("官品改为从七品，位次太子中舍人", "从七品"),
        (("宋徽宗政和、宣和年间", "分工撰述皇太子宫章表文字，每五日赴东宫干事一次", "职掌"),),
    )


def entry273():
    ordinary_east_office(
        273, (("秦汉时期", "已有太子家令"),),
        "宋初", "旧掌皇太子饮食，宋代罕置，以兼官代摄而无实际职事",
        "官品", "从四品上", None,
        (("宋徽宗政和五年（1115）", "刘渊、梁平等见任太子家令", "简称"),),
    )


def entry274():
    ordinary_east_office(
        274, (("秦汉时期", "已有太子率更令，掌知漏刻"),),
        "宋初", "不常置，以兼官充摄，备东宫僚属而无实际职司",
        "官品", "从四品上", None,
        (("宋太祖开宝九年（976）正月", "徐铉见任太子率更令", "简称"),),
    )


def entry275():
    i = 275
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "品位")
    w = W(i)
    entity_id = w.entity("太子仆", "官职", "正文定义太子仆为东宫官属。", quotation=main)
    timepoint(w, i, entity_id, "秦汉时期", "为詹事属官", origin, "建立太子仆职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋初", "沿唐五代旧制存名，无实际职事，位在家令、率更令之下",
        duties, "建立宋初太子仆节点。", "职掌",
        category="东宫官", grade="从四品上",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证太子仆为东宫官属。")
    cite(w, "Timepoints", song_tp, i, rank, "补证太子仆品位与次序。", "品位")
    east_group(w, i, song_tp, main)
    w.commit()


def entry276():
    i = 276
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "太子三卿", "官职", "正文定义太子三卿为家令、率更令、太子仆总称。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "太子家令、太子率更令、太子仆三官总称",
        main, "原文未载确切年月，建立太子三卿统称节点。",
        category="东宫官属统称",
    )
    east_group(w, i, tp_id, main)
    for title in ("太子家令", "太子率更令", "太子仆"):
        relation(
            w, i, tp_id, find_tp(w, title, "宋初"),
            "统称与实例", main, f"太子三卿为总称，{title}为其中一职。",
        )
    w.commit()


def entry277():
    i = 277
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duties = field(i, "职掌")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("太子侍读", "官职", "正文定义太子侍读为东宫官。", quotation=main)
    timepoint(
        w, i, entity_id, "唐太宗贞观十七年（643）", "始置太子侍读",
        history, "建立太子侍读唐代职源节点。", "职源与沿革",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋英宗治平三年（1066）十二月",
        "英宗立赵顼为皇太子，宋朝初置太子侍读，实掌讲解经史",
        history, "建立宋朝太子侍读始置节点。", "职源与沿革",
        category="东宫讲读官", grade="正七品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证太子侍读为东宫官。")
    cite(w, "Timepoints", song_tp, i, duties, "补证太子侍读为有实际职事的讲读官。", "职掌")
    cite(w, "Timepoints", song_tp, i, rank, "补证太子侍读官品。", "官品")
    alias_citation(w, i, song_tp)
    east_group(w, i, song_tp, main)
    w.commit()


def entry278():
    i = 278
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("太子侍讲", "官职", "正文定义太子侍讲为东宫官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋英宗治平三年（1066）十二月",
        "始置太子侍讲，实掌为太子讲解经史，序位在太子侍读之后",
        origin, "建立太子侍讲始置节点。", "职源",
        category="东宫讲读官", grade="正七品",
    )
    cite(w, "Timepoints", tp_id, i, main, "补证太子侍讲为东宫官。")
    cite(w, "Timepoints", tp_id, i, duties, "补证太子侍讲职掌。", "职掌")
    cite(w, "Timepoints", tp_id, i, rank, "补证太子侍讲官品与序位。", "官品")
    alias_citation(w, i, tp_id)
    east_group(w, i, tp_id, main)
    w.commit()


def entry279():
    i = 279
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "东宫讲读官", "官职", "正文定义其为太子侍读、太子侍讲总称。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "太子侍读、太子侍讲官总称，负责东宫经史讲读",
        main, "原文未载确切年月，建立东宫讲读官统称节点。",
        category="东宫官属统称",
    )
    alias_citation(w, i, tp_id, "省称")
    east_group(w, i, tp_id, main)
    relation(
        w, i, tp_id, find_tp(w, "太子侍读", "宋英宗治平三年（1066）十二月"),
        "统称与实例", main, "东宫讲读官为总称，太子侍读为其一职。",
    )
    relation(
        w, i, tp_id, find_tp(w, "太子侍讲", "宋英宗治平三年（1066）十二月"),
        "统称与实例", main, "东宫讲读官为总称，太子侍讲为其一职。",
    )
    w.commit()


def entry280():
    i = 280
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "皇太子宫讲堂", "机构", "正文定义其为皇太子建东宫后的听学之所。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋孝宗淳熙八年（1181）十月十一日",
        "皇太子宫讲堂见讲《周礼》，学官为太子侍读、侍讲等",
        main, "建立皇太子宫讲堂明确见用节点。", category="东宫讲学机构",
    )
    relation(
        w, i, palace(w), tp_id, "上下级机构", main,
        "皇太子宫为上级机构，讲堂为其听学场所。",
    )
    relation(
        w, i, tp_id, find_tp(w, "东宫讲读官", "宋代（具体时间未载）"),
        "编制隶属", main, "太子侍读、侍讲等为皇太子宫讲堂学官。",
        staff_type="讲读官",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(261, 281)] == [
        "管勾左、右春坊事", "左、右春坊", "同主管左、右春坊事", "提举左、右春坊事",
        "左、右春坊谒者", "皇太子宫都监", "皇太子宫祗候", "皇太子宫承受",
        "太子左、右庶子", "太子左、右谕德", "太子中舍人", "太子舍人",
        "太子家令", "太子率更令", "太子仆", "太子三卿", "太子侍读",
        "太子侍讲", "东宫讲读官", "皇太子宫讲堂",
    ]
    entry261()
    entry262()
    entry263()
    entry264()
    entry265()
    entry266()
    entry267()
    entry268()
    entry269()
    entry270()
    entry271()
    entry272()
    entry273()
    entry274()
    entry275()
    entry276()
    entry277()
    entry278()
    entry279()
    entry280()


if __name__ == "__main__":
    main()
