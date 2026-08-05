#!/usr/bin/env python3
"""提取第一编第281-300条：资善堂学官、东宫堂所与诸率府率。"""

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
    """据原书第35-37页修复正文切分、正式词头与 OCR。"""
    split_marker = "太子诸率府率、副率 "
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            rows = {
                i: conn.execute(
                    f"SELECT title,text,fields FROM {table} WHERE id=?", (i,)
                ).fetchone()
                for i in (289, 294, 296, 297, 300)
            }
            assert rows[289] and rows[289][0] == "皇太子宫小学教授", rows[289]
            assert rows[294] and rows[294][0] == "资善堂小学教授", rows[294]
            assert rows[296] and rows[296][0] == "东宫射堂", rows[296]
            assert rows[297], rows[297]
            assert rows[300] and rows[300][0] == "太子左司御率府率、副率", rows[300]

            fields289 = json.loads(rows[289][2] or "{}")
            if "东官小学教授" in fields289.get("别名", ""):
                fields289["别名"] = fields289["别名"].replace(
                    "东官小学教授", "东宫小学教授"
                )
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=289",
                    (json.dumps(fields289, ensure_ascii=False),),
                )
            else:
                assert "东宫小学教授" in fields289.get("别名", ""), fields289

            fields294 = json.loads(rows[294][2] or "{}")
            if "《攻魄集》" in fields294.get("简称", ""):
                fields294["简称"] = fields294["简称"].replace(
                    "《攻魄集》", "《攻媿集》"
                )
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=294",
                    (json.dumps(fields294, ensure_ascii=False),),
                )

            fields296 = json.loads(rows[296][2] or "{}")
            if not rows[297][1]:
                joined = fields296["别名"]
                assert split_marker in joined, joined
                alias296, text297 = joined.split(split_marker, 1)
                fields297 = {
                    "职掌": fields296.pop("职掌"),
                    "通称": fields296.pop("通称"),
                }
                fields296["别名"] = alias296
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=296",
                    (json.dumps(fields296, ensure_ascii=False),),
                )
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=297",
                    (
                        "太子诸率府率、副率",
                        text297.replace("《职源摄要·官品》", "《职源撮要·官品》"),
                        json.dumps(fields297, ensure_ascii=False),
                    ),
                )
            else:
                assert rows[297][0] == "太子诸率府率、副率", rows[297][0]
                assert set(json.loads(rows[297][2] or "{}")) == {"职掌", "通称"}
                assert set(fields296) == {"别名"}, fields296
                if "《职源摄要·官品》" in rows[297][1]:
                    conn.execute(
                        f"UPDATE {table} SET text=? WHERE id=297",
                        (rows[297][1].replace(
                            "《职源摄要·官品》", "《职源撮要·官品》"
                        ),),
                    )

            fields300 = json.loads(rows[300][2] or "{}")
            if "唐龙翔二年" in fields300.get("职源", ""):
                fields300["职源"] = fields300["职源"].replace(
                    "唐龙翔二年", "唐龙朔二年"
                )
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=300",
                    (json.dumps(fields300, ensure_ascii=False),),
                )
            else:
                assert "唐龙朔二年" in fields300.get("职源", ""), fields300


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


F = {i: load(i) for i in range(281, 301)}


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


def palace(w):
    return find_tp(w, "皇太子宫", "宋代（具体时间未载）", "机构")


def east_group(w, i, tp_id, quotation):
    return relation(
        w, i, find_tp(w, "东宫官", "宋代"), tp_id,
        "统称与实例", quotation,
        f"东宫官为总称，{F[i]['title']}为具体东宫官或官类。",
    )


def entry281():
    i = 281
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("新益堂", "机构", "正文定义新益堂为南宋东宫讲堂。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋理宗景定年间（1260—1264）",
        "设置为东宫讲堂",
        main, "建立新益堂景定年间设置节点。", category="东宫讲学机构",
    )
    relation(w, i, palace(w), tp_id, "上下级机构", main, "新益堂为皇太子宫东宫讲堂。")
    w.commit()


def ensure_tongzhilang(w, i, quotation, name):
    entity_id = w.entity(
        "通直郎", "官职", "元丰新制以通直郎寄禄官阶承接旧东宫阶官。", quotation=quotation
    )
    return timepoint(
        w, i, entity_id, "北宋元丰改制后",
        "寄禄官阶，承接太子中允、赞善大夫、太子洗马等旧阶官",
        quotation, "建立元丰新制通直郎承接节点。", name,
        category="文臣寄禄官阶",
    )


def entry282():
    i = 282
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职能")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("太子中允", "官职", "正文定义太子中允为宋前期阶官。", quotation=main)
    timepoint(w, i, entity_id, "东汉时期", "太子官属已有太子中允", origin, "建立太子中允职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋前期", "作为文臣迁转阶官，无实际职事",
        duties, "建立宋前期太子中允阶官节点。", "职能",
        category="东宫阶官", grade="正五品下",
    )
    end_tp = timepoint(
        w, i, entity_id, "北宋元丰改制时",
        "太子中允废罢，改易为寄禄官通直郎阶",
        duties, "建立元丰改制废罢节点。", "职能", category="废罢阶官",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证太子中允为宋前期阶官。")
    cite(w, "Timepoints", song_tp, i, rank, "补证太子中允宋初官品。", "官品")
    alias_citation(w, i, song_tp, "省称")
    east_group(w, i, song_tp, main)
    successor = ensure_tongzhilang(w, i, duties, "职能")
    relation(w, i, end_tp, successor, "前后演变", duties, "元丰新制以通直郎阶承接太子中允。", "职能")
    w.commit()


def entry283():
    i = 283
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职能")
    rank = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    entity_id = w.entity(
        "太子左、右赞善大夫", "官职", "正文定义左右赞善大夫为宋初阶官。", quotation=main
    )
    timepoint(w, i, entity_id, "唐高宗龙朔二年（662）", "始置左右赞善大夫，分别代中允、中舍人", origin, "建立赞善大夫始置节点。", "职源")
    timepoint(w, i, entity_id, "唐高宗咸亨元年（670）", "复中允、中舍后，左右赞善大夫别自为官", origin, "建立赞善大夫独立设官节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋初", "作为文臣迁转阶官，无实际职事",
        duties, "建立宋初左右赞善大夫阶官节点。", "职能",
        category="东宫阶官", grade="正五品下",
    )
    end_tp = timepoint(
        w, i, entity_id, "北宋元丰改制时",
        "左右赞善大夫废罢，改易为寄禄官通直郎阶",
        duties, "建立元丰改制废罢节点。", "职能", category="废罢阶官",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证左右赞善大夫为宋初阶官。")
    cite(w, "Timepoints", song_tp, i, rank, "补证左右赞善大夫宋初官品。", "官品")
    alias_citation(w, i, song_tp, "简称与别名")
    east_group(w, i, song_tp, main)
    successor = ensure_tongzhilang(w, i, duties, "职能")
    relation(w, i, end_tp, successor, "前后演变", duties, "元丰新制以通直郎阶承接左右赞善大夫。", "职能")
    for title in ("太子左赞善大夫", "太子右赞善大夫"):
        child = w.entity(title, "官职", f"简称字段明确列出{title}。", quotation=aliases)
        child_tp = timepoint(
            w, i, child, "宋初", "赞善大夫阶官，无实际职事",
            duties, f"建立{title}宋初节点。", "职能",
            category="东宫阶官", grade="正五品下",
        )
        relation(
            w, i, song_tp, child_tp, "统称与实例", aliases,
            f"太子左、右赞善大夫为并称，{title}为其中一职。", "简称与别名",
        )
    w.commit()


def entry284():
    i = 284
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("太子洗马", "官职", "正文定义太子洗马为宋初官阶。", quotation=main)
    timepoint(w, i, entity_id, "西汉时期", "已有太子先马，为太子太傅、少傅属官", origin, "建立太子洗马职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋初", "沿置而无实际职事，仅作文臣迁转官阶",
        duties, "建立宋初太子洗马阶官节点。", "职掌",
        category="东宫阶官", grade="从五品下",
    )
    end_tp = timepoint(
        w, i, entity_id, "北宋元丰改制时", "太子洗马废罢，改易为寄禄官通直郎阶",
        duties, "建立元丰改制废罢节点。", "职掌", category="废罢阶官",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证太子洗马为宋初官阶。")
    cite(w, "Timepoints", song_tp, i, rank, "补证太子洗马官品与序位。", "官品")
    alias_citation(w, i, song_tp, "简称")
    east_group(w, i, song_tp, main)
    successor = ensure_tongzhilang(w, i, duties, "职掌")
    relation(w, i, end_tp, successor, "前后演变", duties, "元丰新制以通直郎阶承接太子洗马。", "职掌")
    w.commit()


def entry285():
    i = 285
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职能")
    staffing = field(i, "编制")
    w = W(i)
    entity_id = w.entity("资善堂", "机构", "正文定义资善堂为学习之所。", quotation=main)
    timepoint(w, i, entity_id, "宋真宗大中祥符八年（1015）", "于元符观南置学堂", origin, "建立资善堂前身学堂节点。", "职源")
    tp_id = timepoint(
        w, i, entity_id, "宋真宗大中祥符九年（1016）", "学堂定名资善堂，供未出阁皇太子、皇子就学，亦可议政或设讲筵",
        origin, "建立资善堂定名节点。", "职源", category="皇储皇子讲学机构",
    )
    cite(w, "Timepoints", tp_id, i, main, "补证资善堂为学习之所。")
    cite(w, "Timepoints", tp_id, i, duties, "补证资善堂职能。", "职能")
    cite(w, "Timepoints", tp_id, i, staffing, "补证资善堂学官与事务官编制。", "编制")
    alias_citation(w, i, tp_id, "简称与别名")
    w.commit()


def study_post(
    i, time, event, origin_name, parent_title="资善堂",
    parent_type="机构", officer_type=None, later=(),
):
    main = F[i]["text"]
    origin = field(i, origin_name) if origin_name else main
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为学官或堂属。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, time, event,
        origin, f"建立{F[i]['title']}始见或始置节点。", origin_name,
        category="东宫或皇子学官", officer_type=officer_type,
    )
    for later_time, later_event, source_name in later:
        q = field(i, source_name)
        timepoint(
            w, i, entity_id, later_time, later_event, q,
            f"建立{F[i]['title']}后续见置节点。", source_name,
            category="东宫或皇子学官", officer_type=officer_type,
        )
    for name in F[i]["fields"]:
        if name not in {origin_name} and all(name != x[2] for x in later):
            if name in {"简称", "别名"}:
                alias_citation(w, i, tp_id, name)
            else:
                cite(w, "Timepoints", tp_id, i, field(i, name), f"补证{F[i]['title']}的{name}。", name)
    if parent_title == "皇太子宫":
        parent_tp = palace(w)
    else:
        parent_tp = find_tp(w, parent_title, "宋真宗大中祥符九年（1016）", parent_type)
    relation(
        w, i, parent_tp, tp_id, "编制隶属", main,
        f"{F[i]['title']}为{parent_title}学官或僚属。", staff_type=officer_type,
    )
    w.commit()


def entry286():
    study_post(
        286, "宋徽宗宣和元年（1119）四月", "始置，为未出阁皇太子或皇子讲学、授书法",
        "职源", later=(("宋高宗绍兴五年（1135）", "范冲见兼资善堂翊善", "简称"),),
    )


def entry287():
    study_post(
        287, "宋徽宗宣和元年（1119）四月", "始置，掌训导，与翊善同",
        "职源", later=(("宋高宗绍兴五年（1135）", "朱震见兼资善堂赞读", "简称"),),
    )


def entry288():
    study_post(
        288, "宋徽宗宣和元年（1119）四月", "初置，训导资善堂皇子或皇储",
        "职源与沿革", later=(("宋高宗绍兴五年（1135）", "沿置资善堂直讲", "职源与沿革"),),
    )


def entry289():
    study_post(
        289, "宋孝宗淳熙七年（1180）正月二十六日", "始见，以儒臣兼任，为皇孙教导",
        "职源", parent_title="皇太子宫", officer_type="儒臣",
    )


def entry290():
    study_post(
        290, "宋宁宗开禧元年（1205）七月", "初置，掌训导讲学",
        "职源",
    )


def entry291():
    study_post(
        291, "宋真宗大中祥符九年（1016）二月十八日",
        "始置，管理资善堂事务并照护就学皇子，由高级内侍兼充",
        "职源", officer_type="高级内侍",
    )


def entry292():
    study_post(
        292, "宋真宗天禧年间", "开资善堂后置，由内侍兼充，属事务官",
        None, officer_type="内侍",
    )


def entry293():
    study_post(
        293, "宋宁宗嘉泰二年（1202）", "始见，以太子右内率府副率赵与谈充任伴读",
        None,
    )


def entry294():
    study_post(
        294, "宋宁宗庆元六年（1200）四月", "创置，因皇子年幼而借皇太子宫小学教授之名",
        "职源",
    )


def entry295():
    i = 295
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duties = field(i, "职能")
    w = W(i)
    old = w.entity("内东门司", "机构", "职源字段明确议事堂由内东门司改置。", quotation=history)
    old_tp = timepoint(
        w, i, old, "宋孝宗淳熙十四年（1187）十一月二日以前（具体年月未载）",
        "原为内东门司，后改作议事堂",
        history, "建立议事堂改置前的内东门司节点。", "职源与沿革",
        category="宫内机构",
    )
    current = w.entity("议事堂", "机构", "正文定义议事堂为官司。", quotation=main)
    current_tp = timepoint(
        w, i, current, "宋孝宗淳熙十四年（1187）十一月二日",
        "以内东门司改置，供皇太子赵惇隔日与宰执论决军国大事",
        history, "建立议事堂改置节点。", "职源与沿革", category="东宫议政机构",
    )
    timepoint(
        w, i, current, "宋孝宗淳熙十六年（1189）二月七日",
        "孝宗禅位光宗，议事堂撤罢",
        history, "建立议事堂撤罢节点。", "职源与沿革", category="撤罢机构",
    )
    cite(w, "Timepoints", current_tp, i, main, "补证议事堂为官司。")
    cite(w, "Timepoints", current_tp, i, duties, "补证议事堂职能。", "职能")
    relation(w, i, old_tp, current_tp, "前后演变", history, "淳熙十四年以内东门司改为议事堂。", "职源与沿革")
    relation(w, i, palace(w), current_tp, "上下级机构", duties, "议事堂为皇太子议政之所，属皇太子宫体系。", "职能")
    w.commit()


def entry296():
    i = 296
    main = F[i]["text"]
    alias = field(i, "别名")
    w = W(i)
    entity_id = w.entity("东宫射堂", "机构", "正文定义东宫射堂为东宫机构。", quotation=main)
    start_tp = timepoint(
        w, i, entity_id, "宋孝宗淳熙二年（1175）", "建为皇太子练武之所",
        main, "建立东宫射堂始建节点。", category="东宫练武机构",
    )
    later_tp = timepoint(
        w, i, entity_id, "宋理宗景定年间（1260—1264）", "取名凝华堂",
        alias, "建立东宫射堂景定命名节点。", "别名", category="东宫练武机构",
    )
    cite(w, "Timepoints", later_tp, i, alias, "补证凝华堂为东宫射堂别名。", "别名", note="凝华堂为别名，不另建实体")
    relation(w, i, palace(w), start_tp, "上下级机构", main, "东宫射堂为皇太子宫练武机构。")
    w.commit()


def entry297():
    i = 297
    main = F[i]["text"]
    duties = field(i, "职掌")
    common = field(i, "通称")
    w = W(i)
    entity_id = w.entity(
        "太子诸率府率、副率", "官职", "正文定义其为东宫导引仪仗、武卫官总名。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "十率府率及各府副率总名；率从七品、副率从八品，名义掌东宫导引武卫而多无实职",
        main, "原文未载确切年月，建立诸率府率、副率统称节点。",
        category="东宫武卫官统称", grade="率从七品；副率从八品",
    )
    cite(w, "Timepoints", tp_id, i, duties, "补证诸率府率、副率职掌与宋代实际状态。", "职掌")
    alias_citation(w, i, tp_id, "通称")
    east_group(w, i, tp_id, main)
    w.commit()


def rate_pair(i, origin_points=()):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义或参见确定{F[i]['title']}为东宫武官。", quotation=main
    )
    if origin_points:
        origin = field(i, "职源")
        for time, event in origin_points:
            timepoint(
                w, i, entity_id, time, event, origin,
                f"建立{F[i]['title']}职源节点。", "职源",
            )
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "太子率府正、副武官，具体制度参见太子诸率府率、副率总条",
        main, f"建立{F[i]['title']}宋代节点。",
        category="东宫武官", grade="率从七品；副率从八品",
    )
    w.commit()
    return tp_id


def entry298():
    rate_pair(
        298,
        (("秦代", "已有卫率府"),
         ("西汉时期", "太子詹事属官置卫率，掌门卫")),
    )


def entry299():
    rate_pair(299)


def entry300():
    rate_pair(
        300,
        (("唐高宗龙朔二年（662）", "左右宗卫率改为左、右司御率府"),),
    )


def link_rate_members():
    i = 297
    main = F[i]["text"]
    w = W(i)
    group_tp = find_tp(w, "太子诸率府率、副率", "宋代（具体时间未载）")
    for title in (
        "太子左卫率府率、副率",
        "太子右卫率府率、副率",
        "太子左司御率府率、副率",
    ):
        relation(
            w, i, group_tp, find_tp(w, title, "宋代（具体时间未载）"),
            "统称与实例", main,
            f"太子诸率府率、副率为总称，{title}为原文明列的一府正、副率。",
        )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(281, 301)] == [
        "新益堂", "太子中允", "太子左、右赞善大夫", "太子洗马", "资善堂",
        "资善堂翊善", "资善堂赞读", "资善堂直讲", "皇太子宫小学教授",
        "资善堂说书", "资善堂都监", "勾当资善堂", "资善堂伴读",
        "资善堂小学教授", "议事堂", "东宫射堂", "太子诸率府率、副率",
        "太子左卫率府率、副率", "太子右卫率府率、副率", "太子左司御率府率、副率",
    ]
    entry281()
    entry282()
    entry283()
    entry284()
    entry285()
    entry286()
    entry287()
    entry288()
    entry289()
    entry290()
    entry291()
    entry292()
    entry293()
    entry294()
    entry295()
    entry296()
    entry297()
    entry298()
    entry299()
    entry300()
    link_rate_members()


if __name__ == "__main__":
    main()
