#!/usr/bin/env python3
"""提取第一编第401-420条：学士院权直、经筵机构与讲读官。"""

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
    """据原书第49-51页修复#411-412、#417-418错并及确定OCR字误。"""
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            row405 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=405"
            ).fetchone()
            assert row405 and row405[0]
            f405 = json.loads(row405[0])
            if "编制" not in f405:
                duty, staffing = f405["职掌"].split("编制 ", 1)
                f405["职掌"] = duty
                f405["编制"] = staffing
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=405",
                    (json.dumps(f405, ensure_ascii=False),),
                )
            else:
                assert "编制 " not in f405["职掌"]

            row406 = conn.execute(
                f"SELECT text FROM {table} WHERE id=406"
            ).fetchone()
            assert row406 and row406[0]
            conn.execute(
                f"UPDATE {table} SET text=? WHERE id=406",
                (row406[0].replace("还英阁", "迩英阁"),),
            )

            row407 = conn.execute(
                f"SELECT text FROM {table} WHERE id=407"
            ).fetchone()
            assert row407 and row407[0]
            fixed407 = row407[0].replace("《宋会要·职官》6之74)", "《宋会要·职官》6之74）")
            conn.execute(f"UPDATE {table} SET text=? WHERE id=407", (fixed407,))

            row408 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=408"
            ).fetchone()
            assert row408 and row408[0]
            f408 = json.loads(row408[0])
            f408["省称"] = f408["省称"].replace("迥英", "迩英")
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=408",
                (json.dumps(f408, ensure_ascii=False),),
            )

            row411 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=411"
            ).fetchone()
            row412 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=412"
            ).fetchone()
            assert row411 and row412
            if row412[1]:
                assert row412[0] in ("待读", "侍读")
                assert row412[1] == "官名。" and row412[2]
            else:
                f411 = json.loads(row411[0])
                duty411, duty412 = f411["职掌"].split("①宋初之制", 1)
                grade411, grade412 = f411["品位"].split("①宋初，依本官而定。", 1)
                aliases411, text412 = f411["简称与别名"].split("侍读 官名。", 1)
                assert not text412
                f412 = {
                    "职源与沿革": f411.pop("职源与沿革"),
                    "职掌": "①宋初之制" + duty412,
                    "品位": "①宋初，依本官而定。" + grade412,
                }
                f411["职掌"] = duty411
                f411["品位"] = grade411
                f411["简称与别名"] = aliases411
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=411",
                    (json.dumps(f411, ensure_ascii=False),),
                )
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=412",
                    ("侍读", "官名。", json.dumps(f412, ensure_ascii=False)),
                )
            conn.execute(
                f"UPDATE {table} SET title='侍读' WHERE id=412 AND title='待读'"
            )

            row416 = conn.execute(
                f"SELECT title,fields FROM {table} WHERE id=416"
            ).fetchone()
            assert row416 and row416[0] == "侍讲" and row416[1]
            f416 = json.loads(row416[1])
            f416.pop("_catalog_name", None)
            f416.pop("__status__", None)
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=416",
                (json.dumps(f416, ensure_ascii=False),),
            )

            row417 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=417"
            ).fetchone()
            row418 = conn.execute(
                f"SELECT text,fields FROM {table} WHERE id=418"
            ).fetchone()
            assert row417 and row418
            if row418[0]:
                assert row418[0].startswith("官名。仁宗朝偶尔置之") and row418[1] is None
            else:
                f417 = json.loads(row417[0])
                aliases417, text418 = f417["简称"].split("翰林侍讲 官名。", 1)
                f417["简称"] = aliases417
                f417["官品"] = f417["官品"].replace(
                    "“国子祭酒”邢昺守本官充翰林侍讲学士”",
                    "“国子祭酒邢昺守本官充翰林侍讲学士”",
                )
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=417",
                    (json.dumps(f417, ensure_ascii=False),),
                )
                conn.execute(
                    f"UPDATE {table} SET text=?,fields=NULL WHERE id=418",
                    ("官名。" + text418,),
                )

            row420 = conn.execute(
                f"SELECT fields FROM {table} WHERE id=420"
            ).fetchone()
            assert row420 and row420[0]
            f420 = json.loads(row420[0])
            value = f420["省称"]
            for old, new in (
                ("万俟中丞芮", "万俟中丞卨"),
                ("罗谏议汝概", "罗谏议汝楫"),
                ("万俟芮", "万俟卨"),
                ("罗汝概", "罗汝楫"),
            ):
                value = value.replace(old, new)
            f420["省称"] = value
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=420",
                (json.dumps(f420, ensure_ascii=False),),
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


F = {i: load(i) for i in range(401, 421)}


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


def conflict_timepoint(
    w,
    i,
    entity_id,
    time,
    event,
    quotation,
    decision,
    name,
    note,
    category=None,
    chain="tail",
):
    target_id = w.timepoint(
        entity_id,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        chain=chain,
    )
    cite(
        w,
        "Timepoints",
        target_id,
        i,
        quotation,
        decision,
        name,
        note=note,
        conflict_flag=1,
    )
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


def conflict_relation(
    w,
    i,
    subject,
    object_,
    kind,
    quotation,
    decision,
    name,
    note,
    staff_quota=None,
):
    target_id = w.relationship(
        subject,
        object_,
        kind,
        decision,
        quotation,
        staff_quota=staff_quota,
    )
    cite(
        w,
        "Relationships",
        target_id,
        i,
        quotation,
        decision,
        name,
        note=note,
        conflict_flag=1,
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
        w,
        "Timepoints",
        tp_id,
        i,
        quotation,
        f"补证{F[i]['title']}的{name}；不为简称、别名另建实体。",
        name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def normalize_prior_waiting_office():
    """将#395按机构语境暂定的“学士院待诏”规范到#405正式词头。"""
    with sqlite3.connect(ENTRY_DB) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        old = conn.execute(
            "SELECT id FROM Entities WHERE title='学士院待诏' AND type='官职'"
        ).fetchone()
        new = conn.execute(
            "SELECT id FROM Entities WHERE title='翰林待诏' AND type='官职'"
        ).fetchone()
        if old:
            assert not new, (old, new)
            conn.execute(
                "UPDATE Entities SET title=?,quotation=? WHERE id=?",
                ("翰林待诏", F[405]["text"], old[0]),
            )
            conn.execute(
                "INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision) VALUES(?,?,?,?,?)",
                (
                    "Entities",
                    old[0],
                    F[405]["title"],
                    F[405]["page"],
                    "#405正式词头为翰林待诏，将#395依语境暂定的学士院待诏规范为正式名。",
                ),
            )
        else:
            assert new, "缺少#395已建待诏实体"


def entry401():
    i = 401
    main = F[i]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    w = W(i)
    entity_id = w.entity("翰林权直", "官职", "正文定义翰林权直为职事官。", quotation=main)
    tp_id = timepoint(
        w,
        i,
        entity_id,
        "宋孝宗乾道九年（1173）十二月二十四日",
        "始置；学士俱阙时以他官兼任，暂行学士院文书",
        origin,
        "建立翰林权直始置节点。",
        "职源",
        category="学士院临时职事官",
        officer_type="他官兼任",
        grade="依本官品",
    )
    cite(w, "Timepoints", tp_id, i, duty, "补证翰林权直暂行学士院文书。", "职掌")
    cite(w, "Timepoints", tp_id, i, grade, "补证翰林权直为他官兼，官品依本官。", "官品")
    relation(w, i, find_tp(w, "学士院", "宋代", "机构"), tp_id, "编制隶属", duty, "翰林权直暂行学士院文书。", "职掌", staff_type="他官兼任")
    alias_citation(w, i, tp_id, "简称")
    w.commit()


def entry402():
    i = 402
    main = F[i]["text"]
    w = W(i)
    old_entity = find_entity(w, "翰林权直")
    old_end = timepoint(
        w,
        i,
        old_entity,
        "宋孝宗淳熙五年（1178）九月",
        "因翰林之名不正，改名学士院权直；但旧名后仍习用",
        main,
        "建立翰林权直改名节点。",
        category="改名但与新名并用",
    )
    entity_id = w.entity("学士院权直", "官职", "正文定义学士院权直为职事官。", quotation=main)
    new_tp = timepoint(
        w,
        i,
        entity_id,
        "宋孝宗淳熙五年（1178）九月",
        "由翰林权直改名；此后两名互除不废",
        main,
        "建立学士院权直始置节点。",
        category="学士院临时职事官",
        officer_type="他官兼任",
    )
    relation(w, i, old_end, new_tp, "前后演变", main, "淳熙五年翰林权直改名学士院权直，后两名仍并用。")
    relation(w, i, find_tp(w, "学士院", "宋代", "机构"), new_tp, "编制隶属", main, "学士院权直为学士院职事官。", staff_type="他官兼任")
    alias_citation(w, i, new_tp, "简称")
    w.commit()


def entry403():
    i = 403
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("员外学士", "官职", "正文定义员外学士为超出学士院六员定额的入院学士。", quotation=main)
    north = timepoint(w, i, entity_id, "北宋前期", "超出学士院六员定额的入院学士称员外学士", main, "建立北宋前期员外学士制度节点。", category="学士院超额学士", officer_type="超额增员")
    timepoint(w, i, entity_id, "宋仁宗至和元年（1054）", "王洙为第七员学士，时号员外学士", main, "建立至和元年员外学士见例节点。", category="学士院超额学士", officer_type="超额增员")
    relation(w, i, find_tp(w, "学士院", "北宋前期", "机构"), north, "编制隶属", main, "员外学士是学士院超出六员定额的入院学士。", staff_type="超额增员")
    w.commit()


def entry404():
    i = 404
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("双宣学士", "官职", "正文定义双宣学士为锁院时预先宣召的二学士。", quotation=main)
    tp_id = timepoint(w, i, entity_id, "宋代（具体时间未载）", "学士院锁院草白麻制三道以上时，宣召二学士入院分撰", main, "建立双宣学士制度节点。", category="学士院临时组合学士", officer_type="锁院临时宣召")
    relation(w, i, find_tp(w, "学士院", "宋代", "机构"), tp_id, "编制隶属", main, "双宣学士为学士院锁院时宣召的二学士。", staff_type="锁院临时宣召", staff_quota=2)
    alias_citation(w, i, tp_id, "简称")
    w.commit()


def entry405():
    i = 405
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    staffing = field(i, "编制")
    note = "#405职源与沿革记宋初翰林待诏十人，编制字段又记宋初六人，两说并存。"
    w = W(i)
    entity_id = find_entity(w, "翰林待诏")
    yongxi = timepoint(w, i, entity_id, "宋太宗雍熙年间（984—987）", "翰林待诏增为十人", staffing, "建立雍熙间翰林待诏编制节点。", "编制", category="学士院待诏", chain="head")
    song_six = conflict_timepoint(w, i, entity_id, "宋初（编制字段记六人）", "编制字段记翰林待诏六人", staffing, "保留编制字段的宋初六人说。", "编制", note, category="学士院待诏", chain="head")
    song_ten = conflict_timepoint(w, i, entity_id, "宋初（职源与沿革字段记十人）", "职源与沿革字段记学士院置翰林待诏十人", history, "保留职源与沿革字段的宋初十人说。", "职源与沿革", note, category="学士院待诏", chain="head")
    tang = timepoint(w, i, entity_id, "唐玄宗开元初", "北门学士改为翰林待诏", history, "建立翰林待诏唐代始置节点。", "职源与沿革", category="唐代翰林官", chain="head")
    cite(w, "Timepoints", song_ten, i, duty, "补证宋初翰林待诏仅掌抄写书诏、麻制。", "职掌")

    north = find_tp(w, "翰林待诏", "北宋前期")
    cite(w, "Timepoints", north, i, staffing, "翰林待诏雍熙后减为三人，补证北宋前期三人编制。", "编制")
    reform = timepoint(w, i, entity_id, "宋神宗元丰改制后", "翰林待诏定员三人", staffing, "补证元丰改制后翰林待诏三人编制。", "编制", category="学士院待诏")

    north_gate = w.entity("北门学士", "官职", "职源与沿革字段明言唐高宗乾封以后始称北门学士。", quotation=history)
    north_gate_tp = timepoint(w, i, north_gate, "唐高宗乾封以后", "召入草制者始称北门学士", history, "建立北门学士节点。", "职源与沿革", category="唐代翰林官")
    offering = w.entity("翰林供奉", "官职", "职源与沿革字段明言翰林待诏后改翰林供奉。", quotation=history)
    offering_tp = timepoint(w, i, offering, "唐玄宗初", "翰林待诏改为翰林供奉", history, "建立翰林供奉节点。", "职源与沿革", category="唐代翰林官")
    relation(w, i, north_gate_tp, tang, "前后演变", history, "唐玄宗初北门学士改为翰林待诏。", "职源与沿革")
    relation(w, i, tang, offering_tp, "前后演变", history, "翰林待诏又改为翰林供奉。", "职源与沿革")

    clerk = w.entity("隶书待诏", "官职", "职源与沿革字段明载宋初学士院置隶书待诏六人。", quotation=history)
    clerk_tp = timepoint(w, i, clerk, "宋初", "学士院置隶书待诏六人", history, "建立宋初隶书待诏编制节点。", "职源与沿革", category="学士院待诏")

    academy_song = find_tp(w, "学士院", "宋代", "机构")
    academy_north = find_tp(w, "学士院", "北宋前期", "机构")
    academy_reform = find_tp(w, "学士院", "宋神宗元丰改制后", "机构")
    conflict_relation(w, i, academy_song, song_ten, "编制隶属", history, "职源与沿革记宋初学士院翰林待诏十人。", "职源与沿革", note, staff_quota=10)
    conflict_relation(w, i, academy_song, song_six, "编制隶属", staffing, "编制字段记宋初翰林待诏六人。", "编制", note, staff_quota=6)
    relation(w, i, academy_song, yongxi, "编制隶属", staffing, "雍熙间学士院翰林待诏十人。", "编制", staff_quota=10)
    relation(w, i, academy_north, north, "编制隶属", staffing, "雍熙后翰林待诏减为三人。", "编制", staff_quota=3)
    relation(w, i, academy_reform, reform, "编制隶属", staffing, "元丰改制后翰林待诏三人。", "编制", staff_quota=3)
    relation(w, i, academy_song, clerk_tp, "编制隶属", history, "宋初学士院置隶书待诏六人。", "职源与沿革", staff_quota=6)
    alias_citation(w, i, north, "简称")
    w.commit()


def entry406():
    i = 406
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("经筵", "机构", "正文定义经筵为皇帝听讲经史的场所统称。", quotation=main)
    group = timepoint(w, i, entity_id, "宋代（具体时间未载）", "皇帝听讲读官讲解经史的场所统称", main, "建立经筵统称机构节点。", category="御前讲读场所统称")
    lecture_pavilion = w.entity("讲筵阁", "机构", "经筵引文明列讲筵阁为经筵场所。", quotation=main)
    lecture_pavilion_tp = timepoint(w, i, lecture_pavilion, "宋代（具体时间未载）", "皇帝听讲经史的经筵场所", main, "建立讲筵阁机构节点。", category="御前讲读场所")
    relation(w, i, group, lecture_pavilion_tp, "统称与实例", main, "经筵为统称，讲筵阁为引文明列实例。")
    alias_citation(w, i, group, "别称")
    w.commit()


def entry407():
    i = 407
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("说书所", "机构", "正文定义说书所为官司。", quotation=main)
    timepoint(w, i, entity_id, "宋初", "始置，为皇帝听讲读官讲解经史的场所，寓资善堂", main, "建立说书所始置节点。", category="御前讲读场所")
    timepoint(w, i, entity_id, "宋仁宗庆历初（1041）", "改名讲筵所", main, "建立说书所改名终结节点。", category="改名")
    w.commit()


def entry408():
    i = 408
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("迩英阁", "机构", "正文定义迩英阁为官司及皇帝听课处。", quotation=main)
    tp_id = timepoint(w, i, entity_id, "宋仁宗景祐二年（1035）正月二十八日", "始置，为皇帝听课之处", main, "建立迩英阁始置节点。", category="御前讲读场所")
    alias_citation(w, i, tp_id, "省称")
    w.commit()


def entry409():
    i = 409
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("延义阁", "机构", "正文定义延义阁为官司及皇帝听课处。", quotation=main)
    tp_id = timepoint(w, i, entity_id, "宋仁宗景祐二年（1035）正月二十八日", "始置，为皇帝听课之处", main, "建立延义阁始置节点。", category="御前讲读场所")
    alias_citation(w, i, tp_id, "省称")
    w.commit()


def entry410():
    i = 410
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("讲筵所", "机构", "正文定义讲筵所为官司。", quotation=main)
    new_tp = timepoint(w, i, entity_id, "宋仁宗庆历初（1041）", "说书所改名讲筵所，为皇帝听讲经史场所", main, "建立讲筵所始置节点。", category="御前讲读场所")
    relation(w, i, find_tp(w, "说书所", "宋仁宗庆历初（1041）", "机构"), new_tp, "前后演变", main, "仁宗庆历初说书所改名讲筵所。")
    alias_citation(w, i, new_tp, "简称")
    w.commit()


def link_jingyan_instances():
    i = 406
    main = F[i]["text"]
    w = W(i)
    group = find_tp(w, "经筵", "宋代（具体时间未载）", "机构")
    members = (
        ("说书所", "宋初"),
        ("讲筵所", "宋仁宗庆历初（1041）"),
        ("迩英阁", "宋仁宗景祐二年（1035）正月二十八日"),
        ("延义阁", "宋仁宗景祐二年（1035）正月二十八日"),
        ("资善堂", "宋真宗大中祥符九年（1016）"),
    )
    for title, when in members:
        relation(w, i, group, find_tp(w, title, when, "机构"), "统称与实例", main, f"经筵为皇帝听讲场所统称，{title}为正文明列实例。")
    w.commit()


def entry411():
    i = 411
    main = F[i]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    w = W(i)
    predecessor = w.entity("崇政殿讲书", "官职", "职源字段记开宝八年始以崇政殿讲书命官。", quotation=origin)
    timepoint(w, i, predecessor, "宋太祖开宝八年（975）", "始以崇政殿讲书命官", origin, "建立崇政殿讲书始置节点。", "职源", category="御前讲读官")
    entity_id = w.entity("崇政殿说书", "官职", "正文定义崇政殿说书为官名。", quotation=main)
    begin = timepoint(w, i, entity_id, "宋仁宗景祐元年（1034）正月二十六日", "始置，给皇帝讲读经史，秩卑资浅者为说书", origin, "建立崇政殿说书始置节点。", "职源", category="御前讲读官", officer_type="庞官")
    cite(w, "Timepoints", begin, i, duty, "补证崇政殿说书的讲读职掌与资历层级。", "职掌")
    cite(w, "Timepoints", begin, i, grade, "补证宋前期崇政殿说书依本官定品，例从六品。", "品位")
    reform = timepoint(w, i, entity_id, "宋神宗元丰新制", "定为从七品，由庞官充任", grade, "建立元丰新制崇政殿说书品位节点。", "品位", category="御前讲读官", officer_type="庞官", grade="从七品")
    alias_citation(w, i, begin, "简称与别名")
    assert reform
    w.commit()


def entry412():
    i = 412
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    w = W(i)
    entity_id = w.entity("侍读", "官职", "正文定义侍读为官名。", quotation=main)
    timepoint(w, i, entity_id, "唐玄宗开元三年（715）", "集贤殿书院始置侍读，备皇帝顾问史籍疑义", history, "建立侍读唐代源流节点。", "职源与沿革", category="御前读官")
    song = timepoint(w, i, entity_id, "宋太宗太平兴国八年（983）", "宋代始置，备皇帝顾问经史，侍读《文选》及词赋", history, "建立宋代侍读始置节点。", "职源与沿革", category="御前读官", grade="依本官品")
    cite(w, "Timepoints", song, i, duty, "补证侍读宋初职掌及元丰后进读时制。", "职掌")
    cite(w, "Timepoints", song, i, grade, "补证宋初侍读依本官定品。", "品位")
    w.commit()


def entry413():
    i = 413
    main = F[i]["text"]
    w = W(i)
    old_end = timepoint(w, i, find_entity(w, "侍读"), "宋太宗太平兴国八年（983）稍后", "侍读寻改名翰林侍读", main, "建立侍读改名节点。", category="改名")
    entity_id = w.entity("翰林侍读", "官职", "正文定义翰林侍读为由侍读改名的官名。", quotation=main)
    new_tp = timepoint(w, i, entity_id, "宋太宗太平兴国八年（983）稍后", "侍读改名翰林侍读", main, "建立翰林侍读始置节点。", category="御前读官")
    relation(w, i, old_end, new_tp, "前后演变", main, "太平兴国八年侍读寻改翰林侍读。")
    w.commit()


def entry414():
    i = 414
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    w = W(i)
    old_hanlin_end = timepoint(w, i, find_entity(w, "翰林侍读"), "宋真宗咸平二年（999）七月二十六日", "改名翰林侍读学士", history, "建立翰林侍读改名节点。", "职源与沿革", category="改名")
    entity_id = w.entity("翰林侍读学士", "官职", "正文定义翰林侍读学士为官名。", quotation=main)
    begin = timepoint(w, i, entity_id, "宋真宗咸平二年（999）七月二十六日", "翰林侍读改名翰林侍读学士", history, "建立翰林侍读学士始置节点。", "职源与沿革", category="御前读官", grade="依本官品")
    cite(w, "Timepoints", begin, i, duty, "补证翰林侍读学士的讲经、顾问职掌。", "职掌")
    cite(w, "Timepoints", begin, i, grade, "补证翰林侍读学士依所带本官定品。", "品位")
    reform_end = timepoint(w, i, entity_id, "宋神宗元丰改制", "去翰林、学士四字，复称侍读", history, "建立元丰改制改称节点。", "职源与沿革", category="改名")
    reader_reform = timepoint(w, i, find_entity(w, "侍读"), "宋神宗元丰改制", "翰林侍读学士去翰林、学士四字，复称侍读；定为正七品", history, "建立元丰改制侍读复称节点。", "职源与沿革", category="御前读官", grade="正七品")
    reader_1092 = timepoint(w, i, find_entity(w, "侍读"), "宋哲宗元祐七年（1092）", "复称翰林侍读学士，侍读之名暂止", history, "建立元祐七年侍读改名节点。", "职源与沿革", category="改名")
    scholar_1092 = timepoint(w, i, entity_id, "宋哲宗元祐七年（1092）", "复翰林侍读学士之名", history, "建立元祐七年复置节点。", "职源与沿革", category="御前读官")
    scholar_1098 = timepoint(w, i, entity_id, "宋哲宗元符元年（1098）", "又复称侍读", history, "建立元符元年改名节点。", "职源与沿革", category="改名")
    reader_1098 = timepoint(w, i, find_entity(w, "侍读"), "宋哲宗元符元年（1098）", "翰林侍读学士又复称侍读", history, "建立元符元年侍读复称节点。", "职源与沿革", category="御前读官")
    relation(w, i, old_hanlin_end, begin, "前后演变", history, "咸平二年翰林侍读改翰林侍读学士。", "职源与沿革")
    relation(w, i, reform_end, reader_reform, "前后演变", history, "元丰改制翰林侍读学士复称侍读。", "职源与沿革")
    relation(w, i, reader_1092, scholar_1092, "前后演变", history, "元祐七年侍读复称翰林侍读学士。", "职源与沿革")
    relation(w, i, scholar_1098, reader_1098, "前后演变", history, "元符元年翰林侍读学士又复称侍读。", "职源与沿革")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry415():
    i = 415
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("读官", "官职", "正文定义读官为侍读系讲读官的通称。", quotation=main)
    group = timepoint(w, i, entity_id, "宋代（具体时间未载）", "侍读、翰林侍读、翰林侍读学士的通称，地位比讲官高", main, "建立读官统称节点。", category="御前读官统称")
    for title, when in (
        ("侍读", "宋太宗太平兴国八年（983）"),
        ("翰林侍读", "宋太宗太平兴国八年（983）稍后"),
        ("翰林侍读学士", "宋真宗咸平二年（999）七月二十六日"),
    ):
        relation(w, i, group, find_tp(w, title, when), "统称与实例", main, f"读官为通称，{title}为正文明列实例。")
    w.commit()


def entry416():
    i = 416
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    w = W(i)
    tang = w.entity("集贤院侍讲学士", "官职", "职源字段明言唐代有集贤院侍讲学士。", quotation=history)
    timepoint(w, i, tang, "唐代（具体时间未载）", "集贤院置侍讲学士", history, "建立集贤院侍讲学士唐代节点。", "职源与沿革", category="唐代讲官")
    entity_id = w.entity("侍讲", "官职", "正文定义侍讲为官名。", quotation=main)
    begin = timepoint(w, i, entity_id, "北宋仁宗朝（1022—1063）", "始置侍讲，与翰林侍讲学士并存但不常置", history, "建立侍讲始置节点。", "职源与沿革", category="御前讲官")
    cite(w, "Timepoints", begin, i, duty, "补证侍讲掌讲读经史，地位比侍读低。", "职掌")
    reform = timepoint(w, i, entity_id, "宋神宗元丰新制", "皇帝讲官止称侍讲，不带学士、翰林四字，定为正七品", history, "建立元丰新制侍讲节点。", "职源与沿革", category="御前讲官", grade="正七品")
    cite(w, "Timepoints", reform, i, grade, "补证元丰新制侍讲正七品。", "官品")
    w.commit()


def entry417():
    i = 417
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    w = W(i)
    entity_id = w.entity("翰林侍讲学士", "官职", "正文定义翰林侍讲学士为官名。", quotation=main)
    begin = timepoint(w, i, entity_id, "宋真宗咸平二年（999）七月二十六日", "始置翰林侍讲学士，为增崇讲官增学士之号", history, "建立翰林侍讲学士始置节点。", "职源与沿革", category="御前讲官", grade="依本官品")
    cite(w, "Timepoints", begin, i, duty, "补证翰林侍讲学士职掌与侍讲同。", "职掌")
    cite(w, "Timepoints", begin, i, grade, "补证翰林侍讲学士依本官定品。", "官品")
    reform_end = timepoint(w, i, entity_id, "宋神宗元丰新制", "省翰林、学士四字，只称侍讲", history, "建立元丰新制改称节点。", "职源与沿革", category="改名")
    lecturer_reform = find_tp(w, "侍讲", "宋神宗元丰新制")
    lecturer_1092 = timepoint(w, i, find_entity(w, "侍讲"), "宋哲宗元祐七年（1092）七月十二日", "复称翰林侍讲学士，侍讲之名暂止", history, "建立元祐七年侍讲改名节点。", "职源与沿革", category="改名")
    scholar_1092 = timepoint(w, i, entity_id, "宋哲宗元祐七年（1092）七月十二日", "复称翰林侍讲学士", history, "建立元祐七年复置节点。", "职源与沿革", category="御前讲官")
    scholar_1098 = timepoint(w, i, entity_id, "宋哲宗元符元年（1098）二月十三日", "复称侍讲", history, "建立元符元年改名节点。", "职源与沿革", category="改名")
    lecturer_1098 = timepoint(w, i, find_entity(w, "侍讲"), "宋哲宗元符元年（1098）二月十三日", "翰林侍讲学士复称侍讲", history, "建立元符元年侍讲复称节点。", "职源与沿革", category="御前讲官")
    relation(w, i, reform_end, lecturer_reform, "前后演变", history, "元丰新制翰林侍讲学士省称侍讲。", "职源与沿革")
    relation(w, i, lecturer_1092, scholar_1092, "前后演变", history, "元祐七年侍讲复称翰林侍讲学士。", "职源与沿革")
    relation(w, i, scholar_1098, lecturer_1098, "前后演变", history, "元符元年翰林侍讲学士复称侍讲。", "职源与沿革")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry418():
    i = 418
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("翰林侍讲", "官职", "正文定义翰林侍讲为官名。", quotation=main)
    timepoint(w, i, entity_id, "宋仁宗朝（1022—1063）", "偶尔设置，为不带学士的讲读官", main, "建立翰林侍讲节点。", category="御前讲官")
    w.commit()


def entry419():
    i = 419
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("讲官", "官职", "正文定义讲官为侍讲系官职的通称。", quotation=main)
    group = timepoint(w, i, entity_id, "宋代（具体时间未载）", "侍讲、翰林侍讲、翰林侍讲学士的通称", main, "建立讲官统称节点。", category="御前讲官统称")
    for title, when in (
        ("侍讲", "北宋仁宗朝（1022—1063）"),
        ("翰林侍讲", "宋仁宗朝（1022—1063）"),
        ("翰林侍讲学士", "宋真宗咸平二年（999）七月二十六日"),
    ):
        relation(w, i, group, find_tp(w, title, when), "统称与实例", main, f"讲官为通称，{title}为正文明列实例。")
    w.commit()


def entry420():
    i = 420
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("讲读官", "官职", "正文定义讲读官为讲官与读官总称。", quotation=main)
    group = timepoint(w, i, entity_id, "宋代（具体时间未载）", "讲官与读官总称，包括侍读、侍讲及翰林读讲学士等", main, "建立讲读官统称节点。", category="御前讲读官统称")
    relation(w, i, group, find_tp(w, "讲官", "宋代（具体时间未载）"), "统称与实例", main, "讲读官为讲官与读官总称，讲官为其一类。")
    relation(w, i, group, find_tp(w, "读官", "宋代（具体时间未载）"), "统称与实例", main, "讲读官为讲官与读官总称，读官为其一类。")
    for title, when in (
        ("侍读", "宋太宗太平兴国八年（983）"),
        ("侍讲", "北宋仁宗朝（1022—1063）"),
        ("翰林侍讲", "宋仁宗朝（1022—1063）"),
        ("翰林侍读", "宋太宗太平兴国八年（983）稍后"),
        ("翰林侍讲学士", "宋真宗咸平二年（999）七月二十六日"),
        ("翰林侍读学士", "宋真宗咸平二年（999）七月二十六日"),
    ):
        relation(w, i, group, find_tp(w, title, when), "统称与实例", main, f"讲读官为总称，{title}为正文明列实例。")
    alias_citation(w, i, group, "省称")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(401, 421)] == [
        "翰林权直",
        "学士院权直",
        "员外学士",
        "双宣学士",
        "翰林待诏",
        "经筵",
        "说书所",
        "迩英阁",
        "延义阁",
        "讲筵所",
        "崇政殿说书",
        "侍读",
        "翰林侍读",
        "翰林侍读学士",
        "读官",
        "侍讲",
        "翰林侍讲学士",
        "翰林侍讲",
        "讲官",
        "讲读官",
    ]
    assert F[412]["text"] == "官名。" and "职源与沿革" in F[412]["fields"]
    assert F[418]["text"].startswith("官名。仁宗朝偶尔置之") and not F[418]["fields"]

    normalize_prior_waiting_office()
    entry401()
    entry402()
    entry403()
    entry404()
    entry405()
    entry406()
    entry407()
    entry408()
    entry409()
    entry410()
    link_jingyan_instances()
    entry411()
    entry412()
    entry413()
    entry414()
    entry415()
    entry416()
    entry417()
    entry418()
    entry419()
    entry420()


if __name__ == "__main__":
    main()
