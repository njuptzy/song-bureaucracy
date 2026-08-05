#!/usr/bin/env python3
"""提取第一编第361-380条：宗室宅院、王府官与郡王府。"""

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
    """据原书第43-44页修复#367-368切分及确定OCR字误。"""
    marker = "管勾睦亲、广亲宅所 "
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            row367 = conn.execute(
                f"SELECT title,text FROM {table} WHERE id=367"
            ).fetchone()
            row368 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=368"
            ).fetchone()
            assert row367 and row368
            if not row368[1]:
                assert marker in row367[1], row367[1]
                text367, text368 = row367[1].split(marker, 1)
                conn.execute(
                    f"UPDATE {table} SET text=? WHERE id=367", (text367.rstrip(),)
                )
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=NULL WHERE id=368",
                    ("管勾睦亲、广亲宅所", text368),
                )
            else:
                assert row368[0] == "管勾睦亲、广亲宅所", row368[0]
                assert row368[2] is None, row368[2]
                assert marker not in row367[1], row367[1]

            row375 = conn.execute(
                f"SELECT text,fields FROM {table} WHERE id=375"
            ).fetchone()
            assert row375 and row375[0] and row375[1]
            text375 = row375[0]
            fields375 = json.loads(row375[1])
            changed = False
            for old, new in (
                ("《宋王府》", "《亲王府》"),
            ):
                if old in text375:
                    text375 = text375.replace(old, new)
                    changed = True
                else:
                    assert new in text375, (old, new, text375)
            aliases = fields375["别名"]
            if "《攻瑰集》" in aliases:
                fields375["别名"] = aliases.replace("《攻瑰集》", "《攻媿集》")
                changed = True
            else:
                assert "《攻媿集》" in aliases, aliases
            if changed:
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=? WHERE id=375",
                    (text375, json.dumps(fields375, ensure_ascii=False)),
                )

            row380 = conn.execute(
                f"SELECT text FROM {table} WHERE id=380"
            ).fetchone()
            assert row380 and row380[0]
            if "于办郡王府公事" in row380[0]:
                conn.execute(
                    f"UPDATE {table} SET text=? WHERE id=380",
                    (row380[0].replace("于办郡王府公事", "干办郡王府公事"),),
                )
            else:
                assert "干办郡王府公事" in row380[0], row380[0]


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


F = {i: load(i) for i in range(361, 381)}


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


def residence(w, i, title, time, event, quotation, decision, name=None, chain="tail"):
    entity_id = w.entity(title, "机构", decision, quotation=quotation)
    return timepoint(
        w, i, entity_id, time, event, quotation, decision, name,
        category="宗室聚居机构", chain=chain,
    )


def entry361():
    i = 361
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("诸王宫都讲", "官职", "正文定义诸王宫都讲为逐宫院设置的宗学官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋英宗治平元年（1064）",
        "诸王宫逐宫院与教授、小学教授同时设置，掌教导宫室，各系所在宅院名",
        main, "建立诸王宫都讲始置节点。", category="宗学学官统称",
    )
    relation(
        w, i, tp_id, find_tp(w, "睦亲宅都讲", "宋英宗治平元年（1064）六月"),
        "统称与实例", main, "诸王宫都讲为统称，睦亲宅都讲为原文明举实例。",
    )
    relation(
        w, i, find_tp(w, "诸王宫大学、小学", "宋哲宗元祐六年（1091）", "机构"),
        tp_id, "编制隶属", main, "诸王宫都讲为诸王宫宗学体系讲官。",
    )
    w.commit()


def entry362():
    i = 362
    main = F[i]["text"]
    aliases = field(i, "别名")
    w = W(i)
    entity_id = find_entity(w, "睦亲宅", "机构")
    timepoint(
        w, i, entity_id, "宋真宗大中祥符六年（1013）五月二十四日",
        "增修怀远驿为南宅", aliases, "建立南宅兴建节点。", "别名", category="宗室聚居机构",
    )
    begin = timepoint(
        w, i, entity_id, "宋仁宗景祐二年（1035）九月",
        "营作睦亲宅以聚皇族", aliases, "建立睦亲宅营作节点。", "别名", category="宗室聚居机构",
    )
    finished = timepoint(
        w, i, entity_id, "宋仁宗景祐三年（1036）九月",
        "睦亲宅建成，为太祖、太宗九亲王后裔所居", main,
        "建立睦亲宅建成节点。", category="宗室聚居机构",
    )
    cite(w, "Timepoints", begin, i, aliases, "补证睦亲宅营作时间及南宫、南宅别名。", "别名")
    cite(w, "Timepoints", finished, i, aliases, "补证睦亲宅别名。", "别名", note="南宫、南宅为别名，不另建实体")
    w.commit()


def entry363():
    i = 363
    main = F[i]["text"]
    aliases = field(i, "别名")
    w = W(i)
    entity_id = find_entity(w, "广亲宅", "机构")
    tp_id = timepoint(
        w, i, entity_id, "宋仁宗庆历七年（1047）九月二十七日",
        "北宅经增修扩建，赐名广亲宅，为秦王廷美子孙聚居所",
        main, "建立广亲宅赐名节点。", category="宗室聚居机构",
    )
    cite(w, "Timepoints", tp_id, i, aliases, "补证北宫、北宅别名及庆历改名。", "别名", note="北宫、北宅为别名，不另建实体")
    w.commit()


def entry364():
    i = 364
    main = F[i]["text"]
    w = W(i)
    entity_id = find_entity(w, "亲贤宅", "机构")
    timepoint(
        w, i, entity_id, "宋哲宗元祐元年（1086）三月二十四日",
        "赐英宗吴王、益王二王外第名亲贤宅",
        main, "补建亲贤宅赐名节点。", category="宗室聚居机构", chain="head",
    )
    w.commit()


def entry365():
    i = 365
    main = F[i]["text"]
    w = W(i)
    residence(
        w, i, "棣华宅", "宋代（具体时间未载）", "神宗五王子孙聚居宅",
        main, "建立棣华宅机构节点。",
    )
    w.commit()


def entry366():
    i = 366
    main = F[i]["text"]
    w = W(i)
    old = residence(
        w, i, "懿亲宅", "宋代（具体时间未载）", "棣华宅旧名",
        main, "建立懿亲宅旧名实体及节点。",
    )
    current = find_tp(w, "棣华宅", "宋代（具体时间未载）", "机构")
    relation(w, i, old, current, "前后演变", main, "原文明确懿亲宅为棣华宅旧名。")
    w.commit()


def entry367():
    i = 367
    main = F[i]["text"]
    w = W(i)
    residence(
        w, i, "蕃衍宅", "宋徽宗朝（1100—1126）", "徽宗诸王子孙聚居宅",
        main, "建立蕃衍宅机构节点。",
    )
    w.commit()


def entry368():
    i = 368
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("管勾睦亲、广亲宅所", "机构", "修复后的正文定义其为管理二宅事务的官司。", quotation=main)
    timepoint(
        w, i, entity_id, "宋真宗大中祥符七年（1014）", "始置，主管睦亲、广亲二宅事务",
        main, "建立管勾二宅所始置节点。", category="宗室宅务机构",
    )
    end = timepoint(
        w, i, entity_id, "宋神宗熙宁三年（1070）五月十八日",
        "并入大宗正司", main, "建立管勾二宅所并省节点。", category="并省机构",
    )
    relation(
        w, i, end, find_tp(w, "大宗正司", "宋代", "机构"),
        "前后演变", main, "熙宁三年管勾睦亲、广亲宅所并入大宗正司。",
    )
    w.commit()


def residence_post(i, title, parent_title, event):
    main = F[i]["text"]
    w = W(i)
    parent_time = {
        "睦亲宅": "宋仁宗景祐三年（1036）九月",
        "广亲宅": "宋仁宗庆历七年（1047）九月二十七日",
        "睦亲西宅": "宋真宗大中祥符六年（1013）九月",
    }[parent_title]
    parent = find_tp(w, parent_title, parent_time, "机构")
    entity_id = w.entity(title, "官职", f"正文定义{title}为宅院差遣。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", event,
        main, f"建立{title}宋代节点。", category="宗室宅院差遣", officer_type="内侍官",
    )
    relation(w, i, parent, tp_id, "编制隶属", main, f"{title}为{parent_title}差遣。", staff_type="内侍官")
    w.commit()


def entry369():
    residence_post(369, "勾当南宫诸院公事", "睦亲宅", "由内侍官兼充，办理南宫诸院事务")


def entry370():
    residence_post(370, "勾当北宅诸院公事", "广亲宅", "由内侍官兼充，办理北宅诸院事务")


def entry371():
    i = 371
    main = F[i]["text"]
    w = W(i)
    west = residence(
        w, i, "睦亲西宅", "宋真宗大中祥符六年（1013）九月",
        "增建，赵惟正等皇族移居", main, "建立睦亲西宅增建节点。",
    )
    relation(
        w, i, find_tp(w, "睦亲宅", "宋真宗大中祥符六年（1013）五月二十四日", "机构"),
        west, "上下级机构", main, "睦亲西宅为睦亲宅增建部分。",
    )
    entity_id = w.entity("勾当睦亲西宅诸院公事", "官职", "正文定义其为睦亲西宅差遣。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "由内侍官兼充，办理睦亲西宅诸院事务",
        main, "建立勾当睦亲西宅诸院公事节点。", category="宗室宅院差遣", officer_type="内侍官",
    )
    relation(w, i, west, tp_id, "编制隶属", main, "该差遣办理睦亲西宅诸院事务。", staff_type="内侍官")
    w.commit()


def entry372():
    i = 372
    main = F[i]["text"]
    w = W(i)
    residence(w, i, "王宫", "宋代（具体时间未载）", "皇子居所，称某王宫", main, "建立王宫机构节点。")
    w.commit()


def entry373():
    i = 373
    main = F[i]["text"]
    w = W(i)
    tp_id = residence(w, i, "王院", "宋代（具体时间未载）", "王子分院居住之所", main, "建立王院机构节点。")
    alias_citation(w, i, tp_id, "别称")
    w.commit()


def entry374():
    i = 374
    main = F[i]["text"]
    w = W(i)
    residence(
        w, i, "宫院", "宋代（具体时间未载）", "皇族亲王、王子及近属聚居所泛称",
        main, "建立宫院统称机构节点。",
    )
    w.commit()


def entry375():
    i = 375
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("王府官", "官职", "正文定义王府官为王府僚属总称。", quotation=main)
    north = timepoint(
        w, i, entity_id, "北宋",
        "傅、长史、司马、谘议参军、友、记室参军、王府教授、小学教授等总称",
        main, "建立北宋王府官统称节点。", category="王府官属统称",
    )
    south = timepoint(
        w, i, entity_id, "南宋",
        "王府翊善、直讲、赞读、记室、诸王宫大、小学教授等总称",
        main, "建立南宋王府官统称节点。", category="王府官属统称",
    )
    alias_citation(w, i, north, "别名")
    alias_citation(w, i, south, "别名")
    groups = {
        north: (
            ("亲王府傅", "宋代（具体时间未载）"),
            ("亲王府长史", "宋代（亲王判府时，具体年月未载）"),
            ("亲王府司马", "宋初"),
            ("亲王府谘议参军", "宋初"),
            ("亲王府友", "宋代（具体时间未载）"),
            ("亲王府记室参军事", "宋初"),
            ("亲王府教授", "宋代（具体时间未载）"),
            ("亲王府小学教授", "宋代（具体时间未载）"),
        ),
        south: (
            ("亲王府翊善", "宋太宗太平兴国四年（979）"),
            ("亲王府直讲", "宋徽宗政和七年（1117）"),
            ("亲王府赞读", "宋徽宗政和七年（1117）八月"),
            ("亲王府记室", "北宋政和年间"),
            ("诸王宫大、小学教授", "南宋绍兴四年"),
        ),
    }
    for group_tp, members in groups.items():
        for title, time in members:
            relation(
                w, i, group_tp, find_tp(w, title, time), "统称与实例", main,
                f"王府官为总称，{title}为原文明列的王府官实例。",
            )
    w.commit()


def entry376():
    i = 376
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity("郡王", "官职", "正文定义郡王为封爵。", quotation=main)
    timepoint(w, i, entity_id, "南朝陈时期", "正式以郡王为爵名", origin, "建立郡王爵名起源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "皇帝近亲生封者可设官置吏、开府建第；其他受封者多为虚衔",
        main, "建立宋代郡王爵位节点。", category="郡王爵位", grade="从一品",
    )
    cite(w, "Timepoints", song_tp, i, field(i, "职能"), "补证郡王封授对象。", "职能")
    cite(w, "Timepoints", song_tp, i, field(i, "官品"), "补证郡王官品。", "官品")
    alias_citation(w, i, song_tp, "别名")
    w.commit()


def entry377():
    i = 377
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("郡王阁", "机构", "正文定义年幼未出阁郡王居所称阁。", quotation=main)
    timepoint(
        w, i, entity_id, "宋代郡王出阁前（具体年月未载）",
        "年幼郡王未从禁庭迁出外第时称阁", main, "建立郡王阁存在节点。", category="郡王居所机构",
    )
    old_end = timepoint(
        w, i, entity_id, "宋代郡王出阁时（具体年月未载）",
        "郡王出阁后，阁改称府", main, "建立郡王阁出阁改称节点。", category="改称",
    )
    mansion = w.entity("郡王府", "机构", "正文明确郡王出阁后称府。", quotation=main)
    mansion_tp = timepoint(
        w, i, mansion, "宋代郡王出阁时（具体年月未载）",
        "郡王出阁后开第建府", main, "建立郡王府开始节点。", category="郡王府署",
    )
    relation(w, i, old_end, mansion_tp, "前后演变", main, "郡王出阁后由阁改称府。")
    w.commit()


def entry378():
    i = 378
    main = F[i]["text"]
    w = W(i)
    parent = find_tp(w, "郡王阁", "宋代郡王出阁前（具体年月未载）", "机构")
    entity_id = w.entity("郡王阁管勾所", "机构", "正文定义其为掌郡王阁事务的官司。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "掌郡王阁事务",
        main, "建立郡王阁管勾所节点。", category="郡王阁事务机构",
    )
    relation(w, i, parent, tp_id, "上下级机构", main, "郡王阁管勾所为郡王阁事务机构。")
    w.commit()


def entry379():
    i = 379
    main = F[i]["text"]
    w = W(i)
    tp_id = find_tp(w, "郡王府", "宋代郡王出阁时（具体年月未载）", "机构")
    cite(w, "Timepoints", tp_id, i, main, "郡王府专条补证出阁后建第开府。")
    relation(
        w, i, find_tp(w, "郡王阁", "宋代郡王出阁时（具体年月未载）", "机构"),
        tp_id, "前后演变", main, "郡王府专条补证郡王出阁后由阁转为府。",
    )
    w.commit()


def entry380():
    i = 380
    main = F[i]["text"]
    w = W(i)
    parent = find_tp(w, "郡王府", "宋代郡王出阁时（具体年月未载）", "机构")
    entity_id = w.entity("郡王府都监", "官职", "正文定义郡王府都监为郡王府差遣。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "由内侍官充任，干办郡王府公事",
        main, "建立郡王府都监节点。", category="郡王府差遣", officer_type="内侍官",
    )
    relation(w, i, parent, tp_id, "编制隶属", main, "郡王府都监为郡王府差遣。", staff_type="内侍官")
    w.commit()


def link_palace_instances():
    i = 374
    main = F[i]["text"]
    w = W(i)
    group = find_tp(w, "宫院", "宋代（具体时间未载）", "机构")
    members = (
        ("王宫", "宋代（具体时间未载）"),
        ("王院", "宋代（具体时间未载）"),
        ("睦亲宅", "宋仁宗景祐三年（1036）九月"),
        ("广亲宅", "宋仁宗庆历七年（1047）九月二十七日"),
        ("亲贤宅", "宋哲宗元祐元年（1086）三月二十四日"),
        ("棣华宅", "宋代（具体时间未载）"),
        ("懿亲宅", "宋代（具体时间未载）"),
        ("蕃衍宅", "宋徽宗朝（1100—1126）"),
        ("睦亲西宅", "宋真宗大中祥符六年（1013）九月"),
        ("郡王阁", "宋代郡王出阁前（具体年月未载）"),
        ("郡王府", "宋代郡王出阁时（具体年月未载）"),
    )
    for title, time in members:
        relation(
            w, i, group, find_tp(w, title, time, "机构"), "统称与实例", main,
            f"宫院为皇族聚居所泛称，{title}为具体皇族居所。",
        )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(361, 381)] == [
        "诸王宫都讲", "睦亲宅", "广亲宅", "亲贤宅", "棣华宅", "懿亲宅", "蕃衍宅",
        "管勾睦亲、广亲宅所", "勾当南宫诸院公事", "勾当北宅诸院公事",
        "勾当睦亲西宅诸院公事", "王宫", "王院", "宫院", "王府官", "郡王",
        "郡王阁", "郡王阁管勾所", "郡王府", "郡王府都监",
    ]
    entry361()
    entry362()
    entry363()
    entry364()
    entry365()
    entry366()
    entry367()
    entry368()
    entry369()
    entry370()
    entry371()
    entry372()
    entry373()
    entry374()
    entry375()
    entry376()
    entry377()
    entry378()
    entry379()
    entry380()
    link_palace_instances()


if __name__ == "__main__":
    main()
