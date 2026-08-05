#!/usr/bin/env python3
"""提取第一编第381-400条：郡王府官、宗室称号与学士院。"""

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


MISSING_HANLIN_ALIASES = (
    "⑥凤。《宋东京考》卷7《翰林院》引《庐陵集注》：“太宗时，贾黄中、宋白、李至、吕蒙正、"
    "苏易简，同时拜学士、承旨。扈蒙赠诗曰：‘五凤齐飞入翰林。’”"
    "⑦坡。《石林燕语》卷5：“俗称翰林学士为坡。”"
    "⑧翰墨。《水心别集》卷3《官法》：“故谏官、御史无人焉，翰墨、制诰或无人焉，大抵至于"
    "宰相之位或无人焉。”"
    "⑨词臣。《周文忠公全集》卷140《奏议》卷7《翰林学士选德殿对札子三首·自叙》：“自唐至本"
    "朝优待词臣，异乎他官，非专取其翰墨之工也，谓其居近侍之职，无簿书之冗。”《翰林续志》：“太宗曰："
    "‘词臣，实神仙之职也。’玉堂东西壁，延袤数丈，悉画水以布之，风涛浩渺，拟瀛洲之象也。”"
)


def repair_dictionary_source():
    """据原书第45-48页修复#389-390、#396-397切分及确定OCR字误。"""
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            row389 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=389"
            ).fetchone()
            row390 = conn.execute(
                f"SELECT text,fields FROM {table} WHERE id=390"
            ).fetchone()
            assert row389 and row390
            fields389 = json.loads(row389[0] or "{}")
            if row390[0]:
                assert row390[1] is None
                assert row390[0].startswith("①皇帝之子。")
            else:
                mixed = fields389["别称"]
                marker = "①皇帝之子。"
                assert marker in mixed
                own_aliases, prince_text = mixed.split(marker, 1)
                fields389["别称"] = own_aliases.replace("雪州（湖州）", "霅州（湖州）")
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=389",
                    (json.dumps(fields389, ensure_ascii=False),),
                )
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=NULL WHERE id=390",
                    (marker + prince_text,),
                )

            row392 = conn.execute(
                f"SELECT text FROM {table} WHERE id=392"
            ).fetchone()
            assert row392 and row392[0]
            fixed392 = row392[0].replace("《宋会要，帝系》", "《宋会要·帝系》")
            conn.execute(f"UPDATE {table} SET text=? WHERE id=392", (fixed392,))

            row395 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=395"
            ).fetchone()
            assert row395 and row395[0]
            fields395 = json.loads(row395[0])
            aliases395 = fields395["简称与别名"]
            for old, new in (
                ("《玉悔》", "《玉海》"),
                ("少府览铸", "少府监铸"),
                ("张培为学士", "张说为学士"),
            ):
                aliases395 = aliases395.replace(old, new)
            fields395["简称与别名"] = aliases395
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=395",
                (json.dumps(fields395, ensure_ascii=False),),
            )

            row396 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=396"
            ).fetchone()
            row397 = conn.execute(
                f"SELECT text,fields FROM {table} WHERE id=397"
            ).fetchone()
            assert row396 and row397
            if row397[0]:
                assert row397[0] == "差遣名、职事官名。"
                assert row397[1]
            else:
                f396 = json.loads(row396[0])
                source396, source397 = f396["职源"].split("唐朝开元年间", 1)
                duty396, duty397 = f396["职掌"].split("①带“知制诰”三字", 1)
                staff396, staff397 = f396["编制"].split("宋前期六员", 1)
                alias396, mixed397 = f396["简称与别名"].split(
                    "翰林学士 差遣名、职事官名。", 1
                )
                assert mixed397.startswith("①翰林。")
                aliases397 = mixed397
                marker10 = "⑩天子私人。"
                assert marker10 in aliases397 and "⑥凤。" not in aliases397
                aliases397 = aliases397.replace(marker10, MISSING_HANLIN_ALIASES + marker10)

                f397 = {
                    "职源": ("唐朝开元年间" + source397).replace("陆贲传", "陆贽传"),
                    "职掌": "①带“知制诰”三字" + duty397,
                    "官品": f396.pop("官品"),
                    "编制": "宋前期六员" + staff397,
                    "简称与别名": aliases397,
                }
                f396["职源"] = source396.replace("郑细", "郑絪")
                f396["职掌"] = duty396
                f396["编制"] = staff396
                f396["简称与别名"] = alias396
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=396",
                    (json.dumps(f396, ensure_ascii=False),),
                )
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=? WHERE id=397",
                    (
                        "差遣名、职事官名。",
                        json.dumps(f397, ensure_ascii=False),
                    ),
                )

            row398 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=398"
            ).fetchone()
            assert row398 and row398[0]
            f398 = json.loads(row398[0])
            f398["职源与沿革"] = f398["职源与沿革"].replace(
                "同翰苑给含议事状", "同翰苑给舍议事状"
            )
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=398",
                (json.dumps(f398, ensure_ascii=False),),
            )

            row400 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=400"
            ).fetchone()
            assert row400 and row400[0]
            f400 = json.loads(row400[0])
            for key, value in list(f400.items()):
                if isinstance(value, str):
                    f400[key] = value.replace("知制造", "知制诰")
            f400["职源"] = f400["职源"].replace(
                "《直学士院、权直学士院》，或称",
                "《直学士院、权直学士院》），或称",
            )
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=400",
                (json.dumps(f400, ensure_ascii=False),),
            )


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(381, 401)}


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
    source = field(i, name) if name else F[i]["text"]
    assert quotation in source, (i, name, quotation)
    return w.citation(table, target_id, C(i, name), quotation, decision, **kwargs)


def timepoint(
    w,
    i,
    entity_id,
    time,
    event,
    quotation,
    decision,
    name=None,
    category=None,
    officer_type=None,
    grade=None,
    chain="tail",
):
    target_id = w.timepoint(
        entity_id,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        attr_officer_type=officer_type,
        attr_grade=grade,
        chain=chain,
    )
    cite(w, "Timepoints", target_id, i, quotation, decision, name)
    return target_id


def relation(
    w,
    i,
    subject,
    object_,
    kind,
    quotation,
    decision,
    name=None,
    staff_type=None,
    staff_quota=None,
):
    target_id = w.relationship(
        subject,
        object_,
        kind,
        decision,
        quotation,
        staff_type=staff_type,
        staff_quota=staff_quota,
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
        w,
        "Timepoints",
        tp_id,
        i,
        quotation,
        f"补证{F[i]['title']}的{name}；不为简称、别名另建实体。",
        name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def entry381():
    i = 381
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("郡王府教授", "官职", "正文定义郡王府教授为郡王府学官。", quotation=main)
    tp_id = timepoint(
        w,
        i,
        entity_id,
        "宋代（具体时间未载）",
        "为郡王讲读经史",
        main,
        "建立郡王府教授职掌节点。",
        category="郡王府学官",
    )
    relation(
        w,
        i,
        find_tp(w, "郡王府", "宋代郡王出阁时（具体年月未载）", "机构"),
        tp_id,
        "编制隶属",
        main,
        "郡王府教授为郡王府学官。",
    )
    w.commit()


def entry382():
    i = 382
    main = F[i]["text"]
    origin = field(i, "职源")
    treatment = field(i, "位遇")
    w = W(i)
    entity_id = w.entity("郡王友", "官职", "正文定义郡王友为郡王师友官。", quotation=main)
    tp_id = timepoint(
        w,
        i,
        entity_id,
        "宋真宗大中祥符九年（1016）正月",
        "始置；以德才兼备者兼任，郡王以宾礼答拜",
        origin,
        "建立郡王友始置节点。",
        "职源",
        category="郡王师友官",
        officer_type="兼官",
    )
    cite(w, "Timepoints", tp_id, i, treatment, "补证郡王友的宾礼位遇及兼官性质。", "位遇")
    alias_citation(w, i, tp_id, "简称")
    relation(
        w,
        i,
        find_tp(w, "郡王府", "宋代郡王出阁时（具体年月未载）", "机构"),
        tp_id,
        "编制隶属",
        main,
        "郡王友是服务郡王的师友官。",
        staff_type="兼官",
    )
    w.commit()


def simple_princely_office(i, title, event, category):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(title, "官职", f"正文定义{title}为郡王府属官。", quotation=main)
    tp_id = timepoint(
        w,
        i,
        entity_id,
        "宋代（具体时间未载）",
        event,
        main,
        f"建立{title}制度节点。",
        category=category,
    )
    relation(
        w,
        i,
        find_tp(w, "郡王府", "宋代郡王出阁时（具体年月未载）", "机构"),
        tp_id,
        "编制隶属",
        main,
        f"{title}为郡王府属官。",
    )
    w.commit()


def entry383_385():
    simple_princely_office(383, "郡王府翊善", "为郡王府属官", "郡王府辅导官")
    simple_princely_office(384, "郡王府侍讲", "为郡王讲读经史", "郡王府讲读官")
    simple_princely_office(385, "郡王府记室参军", "为郡王府记室属官", "郡王府幕职官")


def title_timepoint(w, i, title, time, event, quotation, decision, name=None, chain="tail"):
    entity_id = w.entity(title, "官职", decision, quotation=quotation)
    return timepoint(
        w,
        i,
        entity_id,
        time,
        event,
        quotation,
        decision,
        name,
        category="宗室封爵",
        chain=chain,
    )


def entry386():
    i = 386
    main = F[i]["text"]
    aliases = field(i, "别称")
    w = W(i)
    title_timepoint(w, i, "齐王", "宋太宗时期（具体年月未载）", "赵廷美先后所封王爵之一", main, "正文明言齐为赵廷美所封王国名。")
    title_timepoint(w, i, "秦王", "宋太宗时期（具体年月未载）", "赵廷美先后所封王爵之一", main, "正文明言秦为赵廷美所封王国名。")
    title_timepoint(w, i, "魏王", "宋徽宗朝（1100—1126）", "追封赵廷美为魏王", main, "正文记徽宗时追封魏王。")
    title_timepoint(
        w,
        i,
        "涪陵县公",
        "宋太宗太平兴国六年（981）九月",
        "秦王赵廷美降封涪陵县公",
        aliases,
        "别称字段明言赵廷美降封涪陵县公。",
        "别称",
    )
    w.commit()


def entry387():
    i = 387
    main = F[i]["text"]
    w = W(i)
    title_timepoint(w, i, "荣王", "宋真宗即位时", "赵元俨进封荣王", main, "正文记真宗即位时赵元俨进封荣王。")
    title_timepoint(w, i, "燕王", "宋仁宗时期（具体年月未载）", "赠赵元俨燕王爵", main, "正文记仁宗时赠燕王。")
    w.commit()


def entry388():
    i = 388
    main = F[i]["text"]
    w = W(i)
    prince_tp = find_tp(w, "郡王", "宋代（具体时间未载）")
    cite(w, "Timepoints", prince_tp, i, main, "赵允让生封郡王，补证宋代郡王封授。")
    pu = title_timepoint(w, i, "濮王", "宋代（具体时间未载）", "追封赵允让为濮王", main, "正文记赵允让追封濮王。")
    pu_succession = timepoint(
        w,
        i,
        find_entity(w, "濮王"),
        "宋神宗元丰七年（1084）",
        "诏准濮王爵袭封，后继者称嗣濮王",
        main,
        "建立濮王开始袭封的制度节点。",
        category="宗室封爵",
    )
    generic = title_timepoint(w, i, "嗣王", "宋神宗元丰七年（1084）", "北宋开始嗣王袭封制", main, "正文明言此为北宋始启嗣王爵之封。")
    instance = title_timepoint(w, i, "嗣濮王", "宋神宗元丰七年（1084）", "濮王爵开始袭封后的后继爵称", main, "正文明言濮王袭封称嗣濮王。")
    relation(w, i, generic, instance, "统称与实例", main, "嗣王为袭封王爵统称，嗣濮王为本条明举实例。")
    relation(w, i, pu_succession, instance, "前后演变", main, "濮王爵准许袭封后，后继爵称为嗣濮王。")
    assert pu
    alias_citation(w, i, pu, "别称")
    w.commit()


def entry389():
    i = 389
    main = F[i]["text"]
    aliases = field(i, "别称")
    w = W(i)
    ji = title_timepoint(w, i, "济王", "宋宁宗崩后（具体月日未载）", "赵竑被封济王，徙第湖州", main, "正文记赵竑封济王。")
    ji_end = timepoint(
        w,
        i,
        find_entity(w, "济王"),
        "宋理宗宝庆元年（1225）",
        "湖州之变后降爵为巴陵郡公",
        main,
        "建立济王降爵终结节点。",
        category="降爵",
    )
    ba = title_timepoint(w, i, "巴陵郡公", "宋理宗宝庆元年（1225）", "赵竑由济王降爵为巴陵郡公", main, "正文明言赵竑被贬为巴陵郡公。")
    relation(w, i, ji_end, ba, "前后演变", main, "济王降爵后改封巴陵郡公。")
    cite(w, "Timepoints", ji, i, aliases, "济邸为济王的别称证据，不另建实体。", "别称", note="别称不另建实体")
    cite(w, "Timepoints", ba, i, aliases, "补证巴陵为巴陵郡公省称及降爵事实。", "别称", note="巴陵为省称，不另建实体")
    w.commit()


def entry390():
    i = 390
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("皇子", "官职", "正文区分皇子的自然称与法称。", quotation=main)
    timepoint(
        w,
        i,
        entity_id,
        "宋代（具体时间未载）",
        "既可指皇帝之子的自然称，也可作为指定皇位继承人的法称",
        main,
        "建立皇子称号的双重制度含义。",
        category="皇族法称",
    )
    w.commit()


def entry391():
    i = 391
    main = F[i]["text"]
    aliases = field(i, "简称与别名")
    w = W(i)
    entity_id = w.entity("嫡皇孙", "官职", "正文定义嫡皇孙为皇太子所生之子的法称。", quotation=main)
    tp_id = timepoint(
        w,
        i,
        entity_id,
        "宋代（具体时间未载）",
        "皇太子所生之子的法称，可入官衔",
        main,
        "建立嫡皇孙法称节点。",
        category="皇族法称",
    )
    cite(w, "Timepoints", tp_id, i, aliases, "补证嫡皇孙的简称与别名，不另建实体。", "简称与别名", note="简称、别名不另建实体")
    w.commit()


def entry395():
    i = 395
    main = F[i]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staffing = field(i, "编制")
    w = W(i)
    entity_id = w.entity("学士院", "机构", "正文定义学士院为官司。", quotation=main)
    timepoint(w, i, entity_id, "唐玄宗开元二十六年（738）", "始置学士院", "学士院之名，始于唐玄宗开元二十六年（738）。", "建立学士院唐代源流节点。", "职源", category="内制机构")
    song = timepoint(w, i, entity_id, "宋代", "沿置为正式官司，为皇帝秘书处，掌制诰、国书、赦书等内制", "宋代沿置，学士院为正式官司名。", "建立学士院宋代沿置节点。", "职源", category="内制机构")
    cite(w, "Timepoints", song, i, duty, "补证学士院掌撰述内制及轮直、宿直之职掌。", "职掌")
    north = timepoint(w, i, entity_id, "北宋前期", "翰林学士定员六名，最资深者一员充承旨，待诏三人", "①北宋前期，翰林学士定员六名，其中资格最深者一员充翰林学士承旨；待诏三人。", "建立北宋前期学士院编制节点。", "编制", category="内制机构")
    chunhua = timepoint(w, i, entity_id, "宋太宗淳化二年（991）以后", "翰林学士开始兼领他局，在院专掌制诰者带知制诰衔", staffing, "建立淳化二年后学士职任分化节点。", "编制", category="内制机构")
    reform = timepoint(w, i, entity_id, "宋神宗元丰改制后", "翰林学士定员二人并带知制诰；另有直学士院、权直学士院等", "②元丰改制后，翰林学士定员二人带“知制诰”；又有直学士院、权直学士院、翰林权直、学士院权直之名，以授他官入院而未除学士或暂领学士之职者；待诏三人、吏额有录事一人、孔目官六人、表奏官八人，给使有驱使官二十人（《宋会要·职官》6之51、53，《却扫编》卷下、《宋史·职官志》2《翰林学士院》、《潜研堂文集》卷28《跋中兴学士院题名》）。", "建立元丰改制后学士院编制节点。", "编制", category="内制机构")

    distinct_quote = "宋代又有翰林院，为供奉之司，与学士院非同一机构。"
    hanlin_yuan = w.entity("翰林院", "机构", "职源字段明确翰林院为供奉之司，与学士院不同。", quotation=distinct_quote)
    timepoint(w, i, hanlin_yuan, "宋代", "供奉之司，与学士院非同一机构", distinct_quote, "建立翰林院与学士院分立的制度节点。", "职源", category="供奉机构")

    for title in ("翰林待诏",):
        role = w.entity(title, "官职", "编制字段明载学士院待诏员额；依#405正式词头规范为翰林待诏。", quotation=staffing)
        north_role = timepoint(w, i, role, "北宋前期", "学士院待诏三人", staffing, "建立北宋前期学士院待诏编制。", "编制", category="学士院吏额")
        reform_role = timepoint(w, i, role, "宋神宗元丰改制后", "学士院待诏三人", staffing, "建立元丰改制后学士院待诏编制。", "编制", category="学士院吏额")
        relation(w, i, north, north_role, "编制隶属", staffing, "北宋前期学士院置待诏三人。", "编制", staff_quota=3)
        relation(w, i, reform, reform_role, "编制隶属", staffing, "元丰改制后学士院置待诏三人。", "编制", staff_quota=3)

    for title, quota, staff_type in (
        ("学士院录事", 1, "吏额"),
        ("学士院孔目官", 6, "吏额"),
        ("学士院表奏官", 8, "吏额"),
        ("学士院驱使官", 20, "给使"),
    ):
        role = w.entity(title, "官职", f"元丰改制后编制明载{title}员额。", quotation=staffing)
        role_tp = timepoint(w, i, role, "宋神宗元丰改制后", f"学士院{title.removeprefix('学士院')}编制{quota}人", staffing, f"建立{title}的元丰后编制节点。", "编制", category="学士院吏额", officer_type=staff_type)
        relation(w, i, reform, role_tp, "编制隶属", staffing, f"元丰改制后学士院置{title.removeprefix('学士院')}{quota}人。", "编制", staff_type=staff_type, staff_quota=quota)

    alias_citation(w, i, song, "简称与别名")
    assert chunhua
    w.commit()


def entry396():
    i = 396
    main = F[i]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    staffing = field(i, "编制")
    w = W(i)
    entity_id = w.entity("翰林学士承旨", "官职", "正文定义翰林学士承旨为差遣、职事官。", quotation=main)
    timepoint(w, i, entity_id, "唐宪宗永贞元年（805）", "始置翰林学士承旨，位居诸学士之上", origin, "建立翰林学士承旨唐代源流节点。", "职源", category="学士院长官")
    song = timepoint(w, i, entity_id, "宋代", "沿置，掌内制并备皇帝咨询顾问，以入院最久者一人充任", origin, "建立宋代翰林学士承旨节点。", "职源", category="学士院长官")
    cite(w, "Timepoints", song, i, duty, "补证翰林学士承旨的内制、顾问职掌。", "职掌")
    cite(w, "Timepoints", song, i, staffing, "补证翰林学士承旨不常置、一人充任的编制。", "编制")
    reform = timepoint(w, i, entity_id, "宋神宗元丰改制后", "官品正三品，位在诸翰林学士之上", grade, "建立元丰改制后品位节点。", "品位", category="学士院长官", grade="正三品")
    relation(w, i, find_tp(w, "学士院", "宋代", "机构"), song, "编制隶属", staffing, "翰林学士承旨为学士院不常置长官，一人充任。", "编制", staff_type="不常置", staff_quota=1)
    alias_citation(w, i, song, "简称与别名")
    assert reform
    w.commit()


def entry397():
    i = 397
    main = F[i]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staffing = field(i, "编制")
    grade = field(i, "官品")
    w = W(i)
    entity_id = w.entity("翰林学士", "官职", "正文定义翰林学士为差遣、职事官。", quotation=main)
    timepoint(w, i, entity_id, "唐朝开元年间", "学士院置学士，或称翰林学士", origin, "建立翰林学士唐代源流节点。", "职源", category="内制官")
    timepoint(w, i, entity_id, "唐肃宗朝", "翰林院亦置学士，称翰林学士", origin, "建立唐肃宗朝翰林院学士节点。", "职源", category="内制官")
    song = timepoint(w, i, entity_id, "宋代", "沿置；在学士院掌内制者带知制诰，兼领他官者可不掌内制", origin, "建立宋代翰林学士节点。", "职源", category="内制官", grade="正三品")
    cite(w, "Timepoints", song, i, duty, "补证宋代翰林学士掌内制与兼领他官两种任职形态。", "职掌")
    cite(w, "Timepoints", song, i, grade, "补证翰林学士官品正三品。", "官品")
    north = timepoint(w, i, entity_id, "北宋前期", "学士院翰林学士定员六人", staffing, "建立北宋前期翰林学士编制节点。", "编制", category="内制官")
    reform = timepoint(w, i, entity_id, "宋神宗元丰改制后", "学士院翰林学士定员二人，专典内制者带知制诰", staffing, "建立元丰改制后翰林学士编制节点。", "编制", category="内制官")
    relation(w, i, find_tp(w, "学士院", "北宋前期", "机构"), north, "编制隶属", staffing, "北宋前期学士院置翰林学士六人。", "编制", staff_quota=6)
    alias_citation(w, i, song, "简称与别名")
    assert reform
    w.commit()


def entry398():
    i = 398
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    w = W(i)
    entity_id = w.entity("翰林学士·知制诰", "官职", "正文定义该复合官衔为差遣、职事官。", quotation=main)
    timepoint(w, i, entity_id, "唐代（具体时间未载）", "翰林学士开始带知制诰衔，以别于不草拟文书者", history, "建立翰林学士带知制诰的唐代源流节点。", "职源与沿革", category="内制官")
    song = timepoint(w, i, entity_id, "宋代", "沿置，知制诰正式系于翰林学士官衔，在学士院掌内制", history, "建立宋代翰林学士·知制诰节点。", "职源与沿革", category="内制官")
    cite(w, "Timepoints", song, i, duty, "补证在学士院撰述内制之职。", "职掌")
    reform = timepoint(w, i, entity_id, "宋神宗元丰改制后", "专典内制的翰林学士一律带知制诰", history, "建立元丰改制后翰林学士官衔节点。", "职源与沿革", category="内制官")
    academy_reform = find_tp(w, "学士院", "宋神宗元丰改制后", "机构")
    relation(w, i, find_tp(w, "学士院", "宋代", "机构"), song, "编制隶属", duty, "翰林学士·知制诰在学士院供职，掌内制。", "职掌")
    relation(w, i, academy_reform, reform, "编制隶属", history, "元丰改制后学士院置带知制诰的翰林学士二人。", "职源与沿革", staff_quota=2)
    relation(w, i, find_tp(w, "翰林学士", "宋神宗元丰改制后"), reform, "前后演变", history, "元丰改制后专典内制的翰林学士一律带知制诰。", "职源与沿革")
    w.commit()


def entry399():
    i = 399
    main = F[i]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    w = W(i)
    entity_id = w.entity("直学士院", "官职", "正文定义直学士院为差遣、职事官。", quotation=main)
    tp_id = timepoint(w, i, entity_id, "宋太祖开宝二年（969）十一月二十七日", "始置；在学士院掌内制，不带知制诰，官品依原差遣官或职事官", origin, "建立直学士院始置节点。", "职源", category="学士院兼官", officer_type="差遣、职事官", grade="依原官品")
    cite(w, "Timepoints", tp_id, i, duty, "补证直学士院职掌与不带知制诰。", "职掌")
    cite(w, "Timepoints", tp_id, i, grade, "补证直学士院的官品依原差遣或职事官。", "官品")
    relation(w, i, find_tp(w, "学士院", "宋代", "机构"), tp_id, "编制隶属", duty, "直学士院为学士院职事官。", "职掌")
    alias_citation(w, i, tp_id, "简称")
    w.commit()


def entry400():
    i = 400
    main = F[i]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    w = W(i)
    entity_id = w.entity("权直学士院", "官职", "正文定义权直学士院为差遣、职事官。", quotation=main)
    tp_id = timepoint(w, i, entity_id, "宋太祖开宝六年（973）四月十九日", "初置；学士院俱阙学士时以他官临时顶阙，不带知制诰，官品依原官", origin, "建立权直学士院初置节点。", "职源", category="学士院临时职事官", officer_type="临时顶阙官", grade="依原官品")
    cite(w, "Timepoints", tp_id, i, duty, "补证权直学士院掌内制而不带知制诰。", "职掌")
    cite(w, "Timepoints", tp_id, i, grade, "补证权直学士院为临时顶阙官，官品依原官。", "品位")
    relation(w, i, find_tp(w, "学士院", "宋代", "机构"), tp_id, "编制隶属", grade, "权直学士院是学士院阙学士时的临时顶阙官。", "品位", staff_type="临时顶阙")
    alias_citation(w, i, tp_id, "别名")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(381, 401)] == [
        "郡王府教授",
        "郡王友",
        "郡王府翊善",
        "郡王府侍讲",
        "郡王府记室参军",
        "秦王赵廷美",
        "燕王赵元俨",
        "濮王赵允让",
        "济王赵竑",
        "皇子",
        "嫡皇孙",
        "大宗",
        "小宗",
        "宗子",
        "学士院",
        "翰林学士承旨",
        "翰林学士",
        "翰林学士·知制诰",
        "直学士院",
        "权直学士院",
    ]
    assert F[390]["text"].startswith("①皇帝之子。") and not F[390]["fields"]
    assert F[397]["text"] == "差遣名、职事官名。" and "职源" in F[397]["fields"]

    entry381()
    entry382()
    entry383_385()
    entry386()
    entry387()
    entry388()
    entry389()
    entry390()
    entry391()
    # #392大宗、#393小宗、#394宗子是宗法类别/人群，非机构或正式官职，不落四表。
    entry395()
    entry396()
    entry397()
    entry398()
    entry399()
    entry400()


if __name__ == "__main__":
    main()
