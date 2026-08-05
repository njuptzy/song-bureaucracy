#!/usr/bin/env python3
"""提取第一编第421-440条：经筵官、入内内侍省及其宋初前身官属。"""

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
    """据原书第51-53页修复词头误字、条目错并和确定OCR字误。"""
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            row422 = conn.execute(f"SELECT fields FROM {table} WHERE id=422").fetchone()
            assert row422 and row422[0]
            f422 = json.loads(row422[0])
            f422 = {
                key: value.replace("內", "内").replace(
                    "内侍长官有都知、副都知、都知、押班",
                    "内侍长官有都都知、副都知、都知、押班",
                )
                for key, value in f422.items()
            }
            conn.execute(
                f"UPDATE {table} SET fields=? WHERE id=422",
                (json.dumps(f422, ensure_ascii=False),),
            )

            row423 = conn.execute(f"SELECT text FROM {table} WHERE id=423").fetchone()
            assert row423 and row423[0]
            fixed423 = row423[0].replace(
                "并入入内内侍省《宋会要", "并入入内内侍省（《宋会要"
            )
            conn.execute(f"UPDATE {table} SET text=? WHERE id=423", (fixed423,))

            row424 = conn.execute(f"SELECT text FROM {table} WHERE id=424").fetchone()
            assert row424 and row424[0]
            conn.execute(
                f"UPDATE {table} SET text=? WHERE id=424",
                (row424[0].replace("并入人内内侍省", "并入入内内侍省"),),
            )

            row425 = conn.execute(f"SELECT text FROM {table} WHERE id=425").fetchone()
            row426 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=426"
            ).fetchone()
            assert row425 and row425[0] and row426
            if not row426[1]:
                text425, text426 = row425[0].split("入内内班都知 宜官名。", 1)
                text425 = text425.replace("内中商品班院", "内中高品班院")
                text426 = "宦官名。" + text426.replace("人内内班院", "入内内班院")
                conn.execute(f"UPDATE {table} SET text=? WHERE id=425", (text425,))
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=NULL WHERE id=426",
                    ("入内内班都知", text426),
                )
            else:
                assert row426[0] == "入内内班都知"
                assert row426[1].startswith("宦官名。") and row426[2] is None
                conn.execute(
                    f"UPDATE {table} SET text=? WHERE id=425",
                    (row425[0].replace("内中商品班院", "内中高品班院"),),
                )

            row427 = conn.execute(
                f"SELECT text,fields FROM {table} WHERE id=427"
            ).fetchone()
            row428 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=428"
            ).fetchone()
            assert row427 and row427[0] and row427[1] and row428
            if not row428[1]:
                f427 = json.loads(row427[1])
                alias427, merged428 = f427["简称"].split(
                    "入内黄门班院 宋初宦寺名。", 1
                )
                text428, alias428 = merged428.split("黄门。", 1)
                f427["简称"] = alias427
                f428 = {"简称": "黄门。" + alias428}
                conn.execute(
                    f"UPDATE {table} SET fields=? WHERE id=427",
                    (json.dumps(f427, ensure_ascii=False),),
                )
                conn.execute(
                    f"UPDATE {table} SET title=?,text=?,fields=? WHERE id=428",
                    (
                        "入内黄门班院",
                        "宋初宦寺名。" + text428,
                        json.dumps(f428, ensure_ascii=False),
                    ),
                )
            else:
                assert row428[0] == "入内黄门班院"
                assert row428[1].startswith("宋初宦寺名。") and row428[2]

            row433 = conn.execute(f"SELECT text FROM {table} WHERE id=433").fetchone()
            assert row433 and row433[0]
            fixed433 = row433[0].replace("宜官名。", "宦官名。")
            if not fixed433.endswith("。"):
                fixed433 += "。"
            conn.execute(f"UPDATE {table} SET text=? WHERE id=433", (fixed433,))


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


F = {i: load(i) for i in range(421, 441)}


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
    note=None,
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
    cite(w, "Relationships", target_id, i, quotation, decision, name, note=note)
    return target_id


def find_entity(w, title, type_=None):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    return entity_id


def find_tp(w, title, time, type_=None):
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
        f"补证{F[i]['title']}的{name}；不为称谓另建实体。",
        name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def normalize_prior_entry422_citations():
    """把旧校对误挂的#430引文改为#422本条实际原文，保留引用ID。"""
    quotation = (
        "宋开国之初，为内中高品班院；淳化五年改名入内内班院，又改为入内黄门班院，"
        "又改内侍省入内内侍班院。至真宗景德三年二月方立省"
    )
    assert quotation in field(422, "职源与沿革")
    with sqlite3.connect(ENTRY_DB) as conn:
        for citation_id in (20824, 20825, 20826):
            row = conn.execute(
                "SELECT quotation FROM Citations WHERE id=?", (citation_id,)
            ).fetchone()
            assert row, citation_id
            if row[0] == quotation:
                continue
            conn.execute(
                "UPDATE Citations SET quotation=? WHERE id=?",
                (quotation, citation_id),
            )
            conn.execute(
                "INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision) "
                "VALUES(?,?,?,?,?)",
                (
                    "Citations",
                    citation_id,
                    F[422]["title"],
                    F[422]["page"],
                    "旧引用误用了#430专条文字而出处标为#422；改为#422职源与沿革字段逐字原文，保留引用ID。",
                ),
            )


def entry421():
    i = 421
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("经筵官", "官职", "正文定义经筵官为御前讲解经史诸官的总名。", quotation=main)
    group = timepoint(
        w,
        i,
        entity_id,
        "宋代（具体时间未载）",
        "翰林侍读学士、翰林侍讲学士、侍读、侍讲、崇政殿说书的总名",
        main,
        "建立经筵官统称节点。",
        category="御前讲读官统称",
    )
    for title, when in (
        ("翰林侍读学士", "宋真宗咸平二年（999）七月二十六日"),
        ("翰林侍讲学士", "宋真宗咸平二年（999）七月二十六日"),
        ("侍读", "宋太宗太平兴国八年（983）"),
        ("侍讲", "北宋仁宗朝（1022—1063）"),
        ("崇政殿说书", "宋仁宗景祐元年（1034）正月二十六日"),
    ):
        relation(
            w,
            i,
            group,
            find_tp(w, title, when, "官职"),
            "统称与实例",
            main,
            f"经筵官为总名，{title}为正文明列实例。",
        )
    alias_citation(w, i, group, "省称")
    w.commit()


def entry422():
    i = 422
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    staffing = field(i, "编制")
    grade = field(i, "品位")
    w = W(i)
    entity_id = find_entity(w, "入内内侍省", "机构")
    tp1006 = find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构")
    cite(w, "Timepoints", tp1006, i, history, "补证入内内侍省合并三司置省及其前身沿革。", "职源与沿革")
    cite(w, "Timepoints", tp1006, i, duty, "补证入内内侍省的内庭侍奉、内外沟通及外差督察职掌。", "职掌")

    yuanfeng = find_tp(w, "入内内侍省", "北宋元丰七年八月", "机构")
    jingkang = find_tp(w, "入内内侍省", "北宋靖康元年正月五日", "机构")
    chongning = timepoint(
        w, i, entity_id, "北宋崇宁二年五月四日", "改定三项领省长官名称", staffing,
        "建立崇宁二年长官改名节点。", "编制", category="内庭宦官署", chain="none"
    )
    zhenghe = timepoint(
        w, i, entity_id, "北宋政和二年（1112）", "改定内侍六等及祗候班三项名称", staffing,
        "建立政和二年内侍官称改革节点。", "编制", category="内庭宦官署", chain="none"
    )
    w.relink(yuanfeng, succ_id=chongning, decision="在元丰七年与靖康元年之间插入崇宁二年节点")
    w.relink(chongning, prev_id=yuanfeng, succ_id=zhenghe, decision="连接崇宁二年与政和二年节点")
    w.relink(zhenghe, prev_id=chongning, succ_id=jingkang, decision="连接政和二年与靖康元年节点")
    w.relink(jingkang, prev_id=zhenghe, decision="靖康复旧节点前接政和改名节点")
    cite(w, "Timepoints", jingkang, i, staffing, "补证靖康元年罢政和改名、恢复元丰旧称。", "编制")

    shaoxing = find_tp(w, "入内内侍省", "南宋绍兴三十年九月", "机构")
    cite(w, "Timepoints", shaoxing, i, staffing, "补证绍兴三十年内侍省并入、两省合一。", "编制")
    longxing = timepoint(
        w, i, entity_id, "南宋隆兴元年（1163）", "内侍定员二百人，分房五，吏额三十五人",
        staffing, "建立隆兴元年编制节点。", "编制", category="内庭宦官署"
    )
    cite(w, "Timepoints", longxing, i, grade, "补证后省位遇高于前省及历代官品制度。", "品位")
    alias_citation(w, i, tp1006, "简称与别名")

    leader_specs = (
        ("入内内侍省都都知", "总领省事"),
        ("入内内侍省副都知", "领省事"),
        ("入内内侍省都知", "领省事"),
        ("入内内侍省押班", "领省事"),
    )
    leader_tps = {}
    for title, role in leader_specs:
        eid = w.entity(title, "官职", "编制字段明载入内内侍省建立后设置该长官。", quotation=staffing)
        tp = timepoint(
            w, i, eid, "北宋景德三年（1006）以后", f"入内内侍省建立后置，{role}", staffing,
            f"建立{title}置于入内内侍省后的节点。", "编制", category="入内内侍省长官", officer_type=role
        )
        relation(w, i, tp1006, tp, "编制隶属", staffing, f"{title}为入内内侍省领省长官。", "编制", staff_type=role)
        leader_tps[title] = tp

    renames = (
        ("入内内侍省都知", "知入内内侍省事"),
        ("入内内侍省副都知", "同知入内内侍省事"),
        ("入内内侍省押班", "签书入内内侍省事"),
    )
    for old_title, new_title in renames:
        old_eid = find_entity(w, old_title, "官职")
        old_end = timepoint(
            w, i, old_eid, "北宋崇宁二年五月四日", f"改名{new_title}", staffing,
            f"建立{old_title}改名节点。", "编制", category="改名"
        )
        new_eid = w.entity(new_title, "官职", "编制字段明载崇宁二年改定该长官名。", quotation=staffing)
        new_begin = timepoint(
            w, i, new_eid, "北宋崇宁二年五月四日", f"由{old_title}改名", staffing,
            f"建立{new_title}始置节点。", "编制", category="入内内侍省长官", officer_type="领省事"
        )
        relation(w, i, old_end, new_begin, "前后演变", staffing, f"崇宁二年{old_title}改名{new_title}。", "编制")
        relation(w, i, chongning, new_begin, "编制隶属", staffing, f"{new_title}为崇宁二年改定的入内内侍省长官。", "编制", staff_type="领省事")
        new_end = timepoint(
            w, i, new_eid, "北宋靖康元年（1126）", f"罢政和改名制度，复称{old_title}", staffing,
            f"建立{new_title}复旧终结节点。", "编制", category="改名"
        )
        old_return = timepoint(
            w, i, old_eid, "北宋靖康元年（1126）", f"罢政和改名制度，恢复{old_title}", staffing,
            f"建立{old_title}靖康复称节点。", "编制", category="入内内侍省长官", officer_type="领省事"
        )
        relation(w, i, new_end, old_return, "前后演变", staffing, f"靖康元年恢复{old_title}旧称。", "编制")
        relation(w, i, jingkang, old_return, "编制隶属", staffing, f"靖康元年恢复的{old_title}仍属入内内侍省。", "编制", staff_type="领省事")

    subordinate_quote = "其所属官司有：御药院、内东门司、合同凭由司、管勾往来国信所、造作所、后苑、军头引见司、翰林院、及诸阁勾当官等"
    for title in (
        "御药院", "内东门司", "合同凭由司", "管勾往来国信所",
        "造作所", "后苑", "军头引见司", "翰林院",
    ):
        child = w.entity(title, "机构", "编制字段明列为入内内侍省所属官司。", quotation=staffing)
        child_tp = w.find_timepoint(child, "宋代（具体时间未载）")
        if child_tp is None:
            child_tp = timepoint(
                w, i, child, "宋代（具体时间未载）", "列为入内内侍省所属官司",
                staffing, f"建立{title}所属关系承载节点。", "编制", category="入内内侍省属司"
            )
        else:
            cite(w, "Timepoints", child_tp, i, staffing, f"补证{title}为入内内侍省所属官司。", "编制")
        relation(w, i, shaoxing, child_tp, "上下级机构", subordinate_quote, f"入内内侍省统辖{title}。", "编制")
    officer = w.entity("诸阁勾当官", "官职", "编制字段明列诸阁勾当官为入内内侍省所属官。", quotation=staffing)
    officer_tp = timepoint(
        w, i, officer, "宋代（具体时间未载）", "列为入内内侍省所属勾当官",
        staffing, "建立诸阁勾当官节点。", "编制", category="入内内侍省属官"
    )
    relation(w, i, shaoxing, officer_tp, "编制隶属", subordinate_quote, "诸阁勾当官属入内内侍省。", "编制", staff_type="勾当官")
    w.commit()


def simple_institution(i, title, start_time, start_event, end_time=None, end_event=None):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(title, "机构", "正文定义该条为宦官所领官署。", quotation=main)
    start = timepoint(w, i, entity_id, start_time, start_event, main, f"建立{title}始置节点。", category="内庭宦官署")
    end = None
    if end_time:
        end = timepoint(w, i, entity_id, end_time, end_event, main, f"建立{title}终结节点。", category="合并或改名")
    w.commit()
    return start, end


def entry423():
    i = 423
    main = F[i]["text"]
    start, end = simple_institution(i, "入内都知司", "宋初", "始置", "北宋景德三年（1006）二月", "并入入内内侍省")
    w = W(i)
    relation(w, i, end, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), "前后演变", main, "景德三年入内都知司并入入内内侍省。")
    w.commit()


def entry424():
    i = 424
    main = F[i]["text"]
    start, end = simple_institution(i, "东门都知司", "宋初", "始置", "北宋景德三年（1006）二月", "并入入内内侍省")
    w = W(i)
    relation(w, i, end, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), "前后演变", main, "景德三年东门都知司并入入内内侍省。")
    w.commit()


def entry432():
    i = 432
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("内中高品班院", "机构", "正文定义内中高品班院为宋初宦寺。", quotation=main)
    timepoint(w, i, entity_id, "宋开国之初", "设置，内臣编制不过五十人", main, "建立内中高品班院始置节点。", category="内庭宦官署")
    timepoint(w, i, entity_id, "北宋淳化五年（994）", "改名入内内班院", main, "建立内中高品班院改名节点。", category="改名")
    w.commit()


def entry425():
    i = 425
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("入内内班院", "机构", "正文定义入内内班院为宋初宦寺。", quotation=main)
    begin = timepoint(w, i, entity_id, "北宋淳化五年（994）初", "由内中高品班院改名", main, "建立入内内班院始置节点。", category="内庭宦官署")
    end = timepoint(w, i, entity_id, "北宋淳化五年（994）稍后", "又改名入内黄门班院", main, "建立入内内班院改名节点。", category="改名")
    relation(w, i, find_tp(w, "内中高品班院", "北宋淳化五年（994）", "机构"), begin, "前后演变", main, "淳化五年内中高品班院改名入内内班院。")
    w.commit()


def entry433():
    i = 433
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("内中高品都知", "官职", "正文定义内中高品都知为班院总领。", quotation=main)
    begin = timepoint(w, i, entity_id, "宋初", "任内中高品班院总领班", main, "建立内中高品都知节点。", category="内庭宦官长官", officer_type="总领班")
    end = timepoint(w, i, entity_id, "北宋淳化五年（994）", "随班院改名为入内内班都知", main, "建立内中高品都知改名承载节点。", category="改名")
    relation(w, i, find_tp(w, "内中高品班院", "宋开国之初", "机构"), begin, "编制隶属", main, "内中高品都知总领内中高品班院。", staff_type="总领班")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry434():
    i = 434
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("里面内班小底都知", "官职", "正文正式词头为里面内班小底都知。", quotation=main)
    tp = timepoint(w, i, entity_id, "北宋太祖朝（960—976）", "置为内朝侍奉宦官总领，原文推测为内中高品都知前身", main, "建立里面内班小底都知节点并保留推测语气。", category="内庭宦官长官")
    relation(w, i, tp, find_tp(w, "内中高品都知", "宋初", "官职"), "前后演变", main, "原文以“盖即”推测其为内中高品都知前身。", note="原文作“盖即”，前身判断具有推测性")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry435():
    i = 435
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("内中高品押班", "官职", "正文定义内中高品押班为班院副总管。", quotation=main)
    begin = timepoint(w, i, entity_id, "宋初", "为内中高品班院副总管，仅次于都知", main, "建立内中高品押班节点。", category="内庭宦官长官", officer_type="副总管")
    timepoint(w, i, entity_id, "北宋淳化五年（994）", "以入内高品押班之名改称入内内班押班", main, "建立内中高品押班改名节点。", category="改名")
    relation(w, i, find_tp(w, "内中高品班院", "宋开国之初", "机构"), begin, "编制隶属", main, "内中高品押班为内中高品班院副总管。", staff_type="副总管")
    alias_citation(w, i, begin, "别称")
    w.commit()


def entry426():
    i = 426
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("入内内班都知", "官职", "正文定义入内内班都知为班院总领。", quotation=main)
    begin = timepoint(w, i, entity_id, "北宋淳化五年（994）初", "由内中高品都知改名，总领入内内班院供奉事务", main, "建立入内内班都知始置节点。", category="内庭宦官长官", officer_type="总领")
    end = timepoint(w, i, entity_id, "北宋淳化五年（994）稍后", "随班院改名为入内黄门都知", main, "建立入内内班都知改名节点。", category="改名")
    relation(w, i, find_tp(w, "内中高品都知", "北宋淳化五年（994）", "官职"), begin, "前后演变", main, "内中高品都知随班院改名为入内内班都知。")
    relation(w, i, find_tp(w, "入内内班院", "北宋淳化五年（994）初", "机构"), begin, "编制隶属", main, "入内内班都知总领入内内班院。", staff_type="总领")
    w.commit()


def entry427():
    i = 427
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("入内内班押班", "官职", "正文定义入内内班押班为都知佐贰。", quotation=main)
    tp = timepoint(w, i, entity_id, "北宋淳化五年（994）", "由入内高品押班改名，为都知佐贰", main, "建立入内内班押班节点。", category="内庭宦官长官", officer_type="都知佐贰")
    relation(w, i, find_tp(w, "内中高品押班", "北宋淳化五年（994）", "官职"), tp, "前后演变", main, "淳化五年入内高品押班改名入内内班押班。")
    relation(w, i, find_tp(w, "入内内班院", "北宋淳化五年（994）初", "机构"), tp, "编制隶属", main, "入内内班押班为入内内班院都知佐贰。", staff_type="都知佐贰")
    alias_citation(w, i, tp, "简称")
    w.commit()


def entry428():
    i = 428
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("入内黄门班院", "机构", "正文定义入内黄门班院为宋初宦寺。", quotation=main)
    begin = timepoint(w, i, entity_id, "北宋淳化五年（994）稍后", "由入内内班院改名", main, "建立入内黄门班院始置节点。", category="内庭宦官署")
    end = timepoint(w, i, entity_id, "北宋淳化五年（994）再改", "又改名内侍省入内内侍班院", main, "建立入内黄门班院改名节点。", category="改名")
    relation(w, i, find_tp(w, "入内内班院", "北宋淳化五年（994）稍后", "机构"), begin, "前后演变", main, "淳化五年入内内班院改名入内黄门班院。")
    alias_citation(w, i, begin, "简称")
    w.commit()


def entry429():
    i = 429
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("入内黄门都知", "官职", "正文定义入内黄门都知为班院都知。", quotation=main)
    begin = timepoint(w, i, entity_id, "北宋淳化五年（994）稍后", "由入内内班院都知改名", main, "建立入内黄门都知节点。", category="内庭宦官长官", officer_type="都知")
    end = timepoint(w, i, entity_id, "北宋淳化五年（994）再改", "随班院改名为内侍省入内内侍都知", main, "建立入内黄门都知改名承载节点。", category="改名")
    relation(w, i, find_tp(w, "入内内班都知", "北宋淳化五年（994）稍后", "官职"), begin, "前后演变", main, "淳化五年入内内班都知改名入内黄门都知。")
    relation(w, i, find_tp(w, "入内黄门班院", "北宋淳化五年（994）稍后", "机构"), begin, "编制隶属", main, "入内黄门都知总领入内黄门班院。", staff_type="都知")
    w.commit()


def entry430():
    i = 430
    main = F[i]["text"]
    w = W(i)
    begin = find_tp(w, "内侍省入内内侍班院", "北宋淳化五年", "机构")
    end = find_tp(w, "内侍省入内内侍班院", "北宋景德三年二月十四日", "机构")
    cite(w, "Timepoints", begin, i, main, "补证淳化五年由入内黄门班院改名。")
    cite(w, "Timepoints", end, i, main, "补证景德三年改为入内内侍省。")
    relation(w, i, find_tp(w, "入内黄门班院", "北宋淳化五年（994）再改", "机构"), begin, "前后演变", main, "淳化五年入内黄门班院改名内侍省入内内侍班院。")
    relation(w, i, end, find_tp(w, "入内内侍省", "北宋景德三年二月十四日", "机构"), "前后演变", main, "景德三年内侍省入内内侍班院改为入内内侍省。")
    w.commit()


def entry431():
    i = 431
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("内侍省入内内侍都知", "官职", "正文定义该官为班院都知。", quotation=main)
    begin = timepoint(w, i, entity_id, "北宋淳化五年（994）再改", "由入内黄门班院都知改名", main, "建立内侍省入内内侍都知始置节点。", category="内庭宦官长官", officer_type="都知")
    end = timepoint(w, i, entity_id, "北宋景德三年（1006）二月", "改名入内内侍省都知", main, "建立内侍省入内内侍都知改名节点。", category="改名")
    relation(w, i, find_tp(w, "入内黄门都知", "北宋淳化五年（994）再改", "官职"), begin, "前后演变", main, "入内黄门都知改名内侍省入内内侍都知。")
    relation(w, i, find_tp(w, "内侍省入内内侍班院", "北宋淳化五年", "机构"), begin, "编制隶属", main, "内侍省入内内侍都知总领班院。", staff_type="都知")
    target = find_tp(w, "入内内侍省都知", "北宋景德三年（1006）以后", "官职")
    relation(w, i, end, target, "前后演变", main, "景德三年内侍省入内内侍都知改名入内内侍省都知。")
    w.commit()


def entry436():
    i = 436
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("中黄门", "官职", "正文定义中黄门为宋初低级宦官。", quotation=main)
    timepoint(w, i, entity_id, "宋初", "设置，为低级宦官名", main, "建立中黄门节点。", category="内庭低级宦官")
    w.commit()


def entry437():
    i = 437
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("入内内品", "官职", "正文定义入内内品为宋初宦官。", quotation=main)
    tp = timepoint(w, i, entity_id, "宋初", "隶入内高品班院，为中黄门序进之官", main, "建立入内内品节点。", category="内庭宦官")
    relation(w, i, find_tp(w, "内中高品班院", "宋开国之初", "机构"), tp, "编制隶属", main, "入内内品隶入内高品班院；以正式机构名内中高品班院承载。", staff_type="序进官", note="太宗朝多称“入内”，此处复用正式词头内中高品班院")
    w.commit()


def entry438():
    i = 438
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("入内高班", "官职", "正文定义入内高班为宋初宦官。", quotation=main)
    timepoint(w, i, entity_id, "宋真宗咸平初（998）", "为入内内品序进之官，邓守恩见任", main, "建立入内高班节点。", category="内庭宦官")
    w.commit()


def entry439():
    i = 439
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("内中高品", "官职", "正文定义内中高品为宋初宦官。", quotation=main)
    begin = timepoint(w, i, entity_id, "北宋太祖朝（960—976）", "设置，为入内高班序进之官", main, "建立内中高品节点。", category="内庭宦官")
    timepoint(w, i, entity_id, "北宋太宗朝（976—997）", "改称入内高品", main, "建立内中高品改名节点。", category="改名")
    w.commit()


def entry440():
    i = 440
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("入内高品", "官职", "正文定义入内高品即内中高品。", quotation=main)
    begin = timepoint(w, i, entity_id, "北宋太宗朝（976—997）", "内中高品改称入内高品", main, "建立入内高品节点。", category="内庭宦官")
    relation(w, i, find_tp(w, "内中高品", "北宋太宗朝（976—997）", "官职"), begin, "前后演变", main, "太祖朝称内中高品，太宗朝以后改称入内高品。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(421, 441)] == [
        "经筵官", "入内内侍省", "入内都知司", "东门都知司", "入内内班院",
        "入内内班都知", "入内内班押班", "入内黄门班院", "入内黄门都知",
        "内侍省入内内侍班院", "内侍省入内内侍都知", "内中高品班院",
        "内中高品都知", "里面内班小底都知", "内中高品押班", "中黄门",
        "入内内品", "入内高班", "内中高品", "入内高品",
    ]
    assert F[426]["text"].startswith("宦官名。") and not F[426]["fields"]
    assert F[428]["text"].startswith("宋初宦寺名。") and "简称" in F[428]["fields"]

    normalize_prior_entry422_citations()
    entry421()
    entry422()
    entry423()
    entry424()
    entry432()
    entry425()
    entry433()
    entry434()
    entry435()
    entry426()
    entry427()
    entry428()
    entry429()
    entry430()
    entry431()
    entry436()
    entry437()
    entry438()
    entry439()
    entry440()


if __name__ == "__main__":
    main()
