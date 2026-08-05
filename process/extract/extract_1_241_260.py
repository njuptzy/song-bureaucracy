#!/usr/bin/env python3
"""提取第一编第241-260条：宫人身份、皇太子与东宫官属。"""

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


CORRECT_252_ALIAS = (
    "贰宫师。贰，副之意。副宫师，即指太子少师。《攻媿集》卷37《同知枢密院事余端礼"
    "初除封赠父赠通议大夫、太子少师》：“独贰宫师之选。”"
)


def repair_dictionary_fields():
    """据原书第30页修复太子少师异体字及太子宾客字段切分。"""
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            row252 = conn.execute(
                f"SELECT title,fields FROM {table} WHERE id=252"
            ).fetchone()
            row256 = conn.execute(
                f"SELECT title,fields FROM {table} WHERE id=256"
            ).fetchone()
            assert row252 and row252[0] == "太子少师", row252
            assert row256 and row256[0] == "太子宾客", row256

            fields252 = json.loads(row252[1] or "{}")
            current252 = fields252.get("别名")
            if current252 != CORRECT_252_ALIAS:
                assert current252 and current252.startswith("箍宫师。簡，副之意。"), current252
                fields252["别名"] = CORRECT_252_ALIAS
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=252",
                    (json.dumps(fields252, ensure_ascii=False),),
                )

            fields256 = json.loads(row256[1] or "{}")
            if "简称和别名" not in fields256:
                broken = fields256.pop("简称")
                assert broken.startswith("和别名 "), broken
                fields256["简称和别名"] = broken.removeprefix("和别名 ")
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=256",
                    (json.dumps(fields256, ensure_ascii=False),),
                )


repair_dictionary_fields()


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


F = {i: load(i) for i in range(241, 261)}


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
        f"补证{F[i]['title']}的{name}；简称与别名均不另建实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def link_east_palace_group(w, i, tp_id, quotation):
    return relation(
        w, i, find_tp(w, "东宫官", "宋代"), tp_id,
        "统称与实例", quotation,
        f"东宫官为总称，{F[i]['title']}为其具体官职或官类。",
    )


def entry241():
    i = 241
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "未出请受官身", "官职", "正文定义其为尚未获取俸禄的一类宫人。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "尚未领取俸禄，地位略高于初入选宫人，可迁听宣或红霞帔后支取请受",
        main, "原文无确切年月，建立宫人身份节点。",
        category="宫人身份", grade="未出请受",
    )
    relation(
        w, i, find_tp(w, "宫人", "宋代"), tp_id,
        "统称与实例", main, "宫人为总称，未出请受官身为其中一种身份。",
    )
    w.commit()


def entry242():
    i = 242
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(
        "乳母", "官职", "正文定义乳母为入后宫供奶喂养皇子者。", quotation=main
    )
    timepoint(
        w, i, entity_id, "汉唐时期", "已有乳母之名，并可封夫人、受禄赐",
        origin, "建立乳母的汉唐职源节点。", "职源",
        category="后宫供奉人员",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋太宗至道三年（997）八月十七日",
        "太宗乳母齐国夫人刘氏封秦国延寿保圣夫人",
        origin, "保留至道三年乳母受封的明确时间。", "职源",
        category="后宫供奉人员",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证乳母的宫内供奉职能。")
    relation(
        w, i, find_tp(w, "宫人", "宋代"), song_tp,
        "统称与实例", main, "广义宫人为后宫女性人员总称，乳母为供奉御乳的具体人员。",
    )
    w.commit()


def entry243():
    i = 243
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    w = W(i)
    entity_id = w.entity("内谒者", "官职", "正文定义内谒者为女官。", quotation=main)
    timepoint(
        w, i, entity_id, "战国时期", "齐、秦等国已置内谒者，掌传命，以宿卫士充",
        origin, "建立内谒者的战国职源节点。", "职源",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "由宫女充任，守皇帝寝宫门，掌内外传达通报",
        origin, "建立宋代女官内谒者节点。", "职源",
        category="宫人女官",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证内谒者的女官性质。")
    cite(w, "Timepoints", song_tp, i, duties, "补证内谒者职掌。", "职掌")
    alias_citation(w, i, song_tp, "简称与别名")
    relation(
        w, i, find_tp(w, "宫官", "宋初"), song_tp,
        "统称与实例", main, "宫官为宫人女官总称，内谒者为具体女官。",
    )
    w.commit()


def entry244():
    i = 244
    main = F[i]["text"]
    origin = field(i, "职源")
    staffing = field(i, "编制")
    status = field(i, "位遇")
    w = W(i)
    entity_id = w.entity("皇太子", "官职", "正文定义皇太子为官名。", quotation=main)
    timepoint(
        w, i, entity_id, "西汉高祖五年（前202）二月",
        "始以皇太子为正式称号",
        origin, "建立皇太子称号的汉代职源节点。", "职源",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋太宗至道元年（995）八月",
        "立寿王元侃为皇太子，宋朝建储制度始立，皇太子为法定皇位继承人",
        origin, "建立宋朝皇太子制度始置节点。", "职源",
        category="储君", grade="一人",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证皇太子为官名。")
    cite(w, "Timepoints", song_tp, i, staffing, "补证皇太子一人及宋代立嗣制度。", "编制")
    cite(w, "Timepoints", song_tp, i, status, "补证皇太子位遇及设置东宫官属。", "位遇")
    alias_citation(w, i, song_tp, "简称与别名")
    w.commit()


def entry245():
    i = 245
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity(
        "皇太子妃", "官职", "正文定义皇太子妃为太子正妻位号。", quotation=main
    )
    timepoint(
        w, i, entity_id, "汉代", "太子正妻已称太子妃",
        origin, "建立皇太子妃的汉代职源节点。", "职源",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋孝宗乾道七年（1171）",
        "李氏立为皇太子妃，宋代正称皇太子妃",
        origin, "建立宋代皇太子妃明确实例节点。", "职源",
        category="东宫内命位号",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证皇太子妃为太子正妻位号。")
    w.commit()


def entry246():
    i = 246
    main = F[i]["text"]
    aliases = field(i, "简称与别名")
    w = W(i)
    entity_id = w.entity(
        "皇太子宫", "机构", "正文定义皇太子宫为皇太子册立后所居宫殿。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "皇太子册立后所居宫殿，位于丽正门内",
        main, "原文未载确切年月，建立皇太子宫制度节点。",
        category="东宫机构",
    )
    cite(
        w, "Timepoints", tp_id, i, aliases,
        "补证皇太子宫的简称与别名；均不另建实体。", "简称与别名",
        note="太子宫、青宫、东宫、春宫、春坊、皇太子府均作称谓证据",
    )
    w.commit()


def entry247():
    i = 247
    main = F[i]["text"]
    aliases = field(i, "简称与别名")
    w = W(i)
    entity_id = w.entity(
        "东宫官", "官职", "正文定义东宫官为皇太子府官属总名。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代",
        "皇太子府官属总名；立储时临时除授，多无定员、由宰执近臣兼充，宋前期部分又仅作阶官",
        main, "建立宋代东宫官统称节点。", category="东宫官属统称",
    )
    cite(
        w, "Timepoints", tp_id, i, aliases,
        "补证东宫官简称与别名；均不另建实体。", "简称与别名",
        note="宫官、宫臣、春官、春坊、宫僚、随龙官吏、随龙、储僚均作称谓证据",
    )
    relation(
        w, i, find_tp(w, "皇太子宫", "宋代（具体时间未载）", "机构"), tp_id,
        "编制隶属", main, "东宫官为皇太子宫官属总名。",
    )
    w.commit()


def entry248():
    i = 248
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "品位")
    w = W(i)
    entity_id = w.entity(
        "太子六傅", "官职", "正文定义太子六傅为东宫三师、三少总名。", quotation=main
    )
    timepoint(
        w, i, entity_id, "西晋武帝咸宁年间（275—279）",
        "已备太子太师、太傅、太保、少师、少傅、少保六傅之职",
        origin, "建立太子六傅职源节点。", "职源",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋代",
        "六傅无专职，多作文臣迁转官阶或宰执致仕所带衔；三师从一品、三少从二品",
        duties, "建立宋代太子六傅制度节点。", "职掌",
        category="东宫官属统称",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证太子六傅所含六官。")
    cite(w, "Timepoints", song_tp, i, rank, "补证六傅品位。", "品位")
    alias_citation(w, i, song_tp, "简称与别名")
    link_east_palace_group(w, i, song_tp, main)
    w.commit()


def six_office(
    i, origin_points, song_time, song_event, later_points=(), grade=None,
):
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为东宫官。", quotation=main
    )
    for time, event in origin_points:
        timepoint(
            w, i, entity_id, time, event, origin,
            f"建立{F[i]['title']}的前代职源节点。", "职源",
        )
    song_tp = timepoint(
        w, i, entity_id, song_time, song_event, duties,
        f"建立{F[i]['title']}的宋代制度节点。", "职掌",
        category="东宫官", grade=grade,
    )
    for time, event in later_points:
        timepoint(
            w, i, entity_id, time, event, duties,
            f"建立{F[i]['title']}的职掌变化节点。", "职掌",
            category="有职事东宫官", grade=grade,
        )
    cite(w, "Timepoints", song_tp, i, main, f"补证{F[i]['title']}为东宫官。")
    cite(w, "Timepoints", song_tp, i, rank, f"补证{F[i]['title']}官品。", "官品")
    alias_name = "简称与别名" if "简称与别名" in F[i]["fields"] else "别名"
    alias_citation(w, i, song_tp, alias_name)
    link_east_palace_group(w, i, song_tp, main)
    w.commit()


def entry249():
    six_office(
        249,
        (("秦孝公时", "置太子师，为太子太师职源"),
         ("西晋时期", "始置太子太师，因避司马师讳改称太子太帅")),
        "宋前期", "无实职，作文臣迁转官阶或宰相致仕所带官衔",
        grade="从一品",
    )


def entry250():
    six_office(
        250, (("秦汉时期", "已有太子太傅之官"),),
        "宋前期", "无实职，作文臣迁转官阶或宰执致仕所带官衔",
        grade="从一品",
    )


def entry251():
    six_office(
        251,
        (("战国秦孝公时", "置太子太保"),
         ("西晋咸宁年间（275—279）", "六傅始备，太子太保为其一")),
        "宋前期", "无实职，作文臣迁转官阶或宰执致仕所带官衔",
        grade="从一品",
    )


def entry252():
    six_office(
        252, (("西晋咸宁年间（275—279）", "始置太子少师"),),
        "宋初", "无职事，为执政致仕所带官衔或文臣迁转散阶",
        (("宋真宗天禧四年（1020）", "皇太子同听政，以宰相兼太子少师，成为有辅导职事的东宫官"),
         ("宋宁宗嘉定二年（1209）", "复以右相兼太子少师")),
        grade="从二品",
    )


def entry253():
    six_office(
        253, (("西汉高祖时", "张良行太子少傅事，为太子少傅设置之始"),),
        "宋前期", "不常设、无专职，作文臣迁转散阶或执政致仕所带官衔",
        (("宋真宗天禧四年（1020）", "皇太子同听政，以枢密使兼太子少傅，成为有辅导职事的东宫官"),
         ("宋宁宗朝", "曾以右相兼太子少傅")),
        grade="从二品",
    )


def entry254():
    six_office(
        254, (("西晋咸宁年间（275—279）", "始置太子少保"),),
        "宋初", "无职事，作文臣迁转散阶或执政致仕所带官衔",
        (("宋真宗天禧四年（1020）", "皇太子同听政，以执政兼太子少保，成为有辅导职事的东宫官"),),
        grade="从二品",
    )


SIX_MEMBERS = (
    ("太子太师", "宋前期"), ("太子太傅", "宋前期"), ("太子太保", "宋前期"),
    ("太子少师", "宋初"), ("太子少傅", "宋前期"), ("太子少保", "宋初"),
)


def link_six_members():
    i = 248
    main = F[i]["text"]
    w = W(i)
    group_tp = find_tp(w, "太子六傅", "宋代")
    for title, time in SIX_MEMBERS:
        relation(
            w, i, group_tp, find_tp(w, title, time),
            "统称与实例", main, f"太子六傅为总称，{title}为原文明列的一职。",
        )
    w.commit()


def entry255():
    i = 255
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "东宫三少官", "官职", "正文定义东宫三少官为太子少师、少傅、少保总名。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "太子少师、少傅、少保三官总名",
        main, "原文未载确切年月，建立东宫三少官统称节点。",
        category="东宫官属统称",
    )
    relation(
        w, i, find_tp(w, "太子六傅", "宋代"), tp_id,
        "统称与实例", main, "太子六傅包含三师与三少，东宫三少官为其三少子类。",
    )
    for title, time in SIX_MEMBERS[3:]:
        relation(
            w, i, tp_id, find_tp(w, title, time),
            "统称与实例", main, f"东宫三少官为总称，{title}为其一职。",
        )
    w.commit()


def entry256():
    i = 256
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("太子宾客", "官职", "正文定义太子宾客为东宫官。", quotation=main)
    timepoint(w, i, entity_id, "西汉高祖末年", "以商山四皓为宾客辅翼太子，尚未成为官名", origin, "建立宾客名称源流节点。", "职源")
    timepoint(w, i, entity_id, "唐太宗贞观十八年（644）", "以宰相兼太子宾客", origin, "建立唐代兼官节点。", "职源")
    timepoint(w, i, entity_id, "唐高宗显庆年间（656—660）", "始设太子宾客官", origin, "建立太子宾客正式设官节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋太宗至道元年（995）八月",
        "宋朝始置太子宾客二人，以他官兼，掌训导调护太子",
        origin, "建立宋朝太子宾客始置节点。", "职源",
        category="东宫官", grade="从三品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证太子宾客为东宫官。")
    cite(w, "Timepoints", song_tp, i, duties, "补证太子宾客职掌。", "职掌")
    cite(w, "Timepoints", song_tp, i, rank, "补证太子宾客官品。", "官品")
    alias_citation(w, i, song_tp, "简称和别名")
    link_east_palace_group(w, i, song_tp, main)
    w.commit()


def entry257():
    i = 257
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("太子詹事", "官职", "正文定义太子詹事为东宫官。", quotation=main)
    timepoint(w, i, entity_id, "秦汉时期", "皇太子府置詹事，称太子詹事", origin, "建立太子詹事职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "立太子时或置，多以他官兼充，名义除授而不掌本宫事",
        duties, "建立宋代太子詹事常制节点。", "职掌",
        category="东宫官", grade="从三品",
    )
    timepoint(
        w, i, entity_id, "宋孝宗乾道七年（1171）",
        "非常制置专职太子詹事二人，陪侍皇太子赵惇",
        duties, "建立乾道七年专职例外节点。", "职掌",
        category="专职东宫官", grade="从三品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证太子詹事为东宫官。")
    cite(w, "Timepoints", song_tp, i, rank, "补证太子詹事官品。", "官品")
    alias_citation(w, i, song_tp, "简称与别名")
    link_east_palace_group(w, i, song_tp, main)
    w.commit()


def entry258():
    i = 258
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("太子少詹事", "官职", "正文定义太子少詹事为东宫官。", quotation=main)
    timepoint(w, i, entity_id, "唐初", "始置，为太子詹事副贰", origin, "建立太子少詹事职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "作为太子詹事副贰，名义除授而无实际职司",
        duties, "建立宋代太子少詹事节点。", "职掌",
        category="东宫官", grade="正六品",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证太子少詹事为东宫官。")
    cite(w, "Timepoints", song_tp, i, rank, "补证太子少詹事官品。", "官品")
    alias_citation(w, i, song_tp, "简称")
    link_east_palace_group(w, i, song_tp, main)
    w.commit()


def entry259():
    i = 259
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    staffing = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    entity_id = w.entity(
        "皇太子宫左、右春坊司", "机构", "正文定义其为东宫官司。", quotation=main
    )
    timepoint(w, i, entity_id, "北齐时期", "置门下坊、典书坊，为左、右春坊前身", origin, "建立左右春坊前身节点。", "职源")
    timepoint(w, i, entity_id, "唐高宗龙朔二年（662）", "门下坊、典书坊改为左春坊、右春坊", origin, "建立左右春坊改名节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "名义比拟中书、门下省，宋代名存实废，立储时由内侍或武官勾当，平时多省",
        duties, "建立宋代左右春坊司节点。", "职掌",
        category="东宫官司",
    )
    timepoint(
        w, i, entity_id, "宋孝宗乾道七年（1171）",
        "置主管左、右春坊事二员及同主管二员，分别以内侍、武臣兼充",
        staffing, "建立乾道七年左右春坊编制节点。", "编制",
        category="东宫官司",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证左右春坊司为东宫官司。")
    cite(w, "Timepoints", song_tp, i, aliases, "补证左右春坊司简称；不另建称谓实体。", "简称", note="简称仅作称谓证据")
    relation(
        w, i, find_tp(w, "皇太子宫", "宋代（具体时间未载）", "机构"), song_tp,
        "上下级机构", duties, "皇太子宫为上级，左、右春坊司为其官司。", "职掌",
    )
    children = {
        "左春坊": "名义比拟门下省，下属左庶子、中允、左谕德、左赞善大夫、洗马等",
        "右春坊": "名义比拟中书省，下属右庶子、中舍人、舍人、右谕德、右赞善大夫、通事舍人等",
    }
    for title, event in children.items():
        child = w.entity(title, "机构", f"职掌字段明确列出{title}及其下属官。", quotation=duties)
        child_tp = timepoint(
            w, i, child, "宋代（具体时间未载）", event,
            duties, f"建立{title}宋代节点。", "职掌", category="东宫官司",
        )
        relation(
            w, i, song_tp, child_tp, "统称与实例", duties,
            f"皇太子宫左、右春坊司为并称，{title}为其中一司。", "职掌",
        )
    w.commit()


def entry260():
    i = 260
    main = F[i]["text"]
    short = field(i, "省称")
    w = W(i)
    entity_id = w.entity(
        "勾当左、右春坊事", "官职", "正文定义其为北宋皇太子宫差遣官。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, "北宋立皇太子期间（具体年月未载）",
        "立皇太子时置、由内侍兼充，掌皇太子宫庶务；皇太子登位即罢",
        main, "建立勾当左、右春坊事的条件性设罢节点。",
        category="东宫差遣官", officer_type="内侍",
    )
    cite(
        w, "Timepoints", tp_id, i, short,
        "补证勾当左、右春坊事省称左、右春坊；不另建实体。", "省称",
        note="左、右春坊在本条为差遣省称，不另建官职实体",
    )
    relation(
        w, i, find_tp(w, "皇太子宫左、右春坊司", "宋代（具体时间未载）", "机构"),
        tp_id, "编制隶属", main,
        "勾当左、右春坊事为皇太子宫左、右春坊司差遣官。",
        staff_type="内侍",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(241, 261)] == [
        "未出请受官身", "乳母", "内谒者", "皇太子", "皇太子妃", "皇太子宫",
        "东宫官", "太子六傅", "太子太师", "太子太傅", "太子太保", "太子少师",
        "太子少傅", "太子少保", "东宫三少官", "太子宾客", "太子詹事",
        "太子少詹事", "皇太子宫左、右春坊司", "勾当左、右春坊事",
    ]
    entry241()
    entry242()
    entry243()
    entry244()
    entry245()
    entry246()
    entry247()
    entry248()
    entry249()
    entry250()
    entry251()
    entry252()
    entry253()
    entry254()
    link_six_members()
    entry255()
    entry256()
    entry257()
    entry258()
    entry259()
    entry260()


if __name__ == "__main__":
    main()
