#!/usr/bin/env python3
"""提取 chapter5t7 第81-100条：教坊后半、教乐所、衙前乐及大晟府。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_061_080 as previous


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


F = {i: load(i) for i in range(81, 101)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field_name=None):
    source = F[i]["fields"][field_name] if field_name else F[i]["text"]
    assert needle in source, (i, field_name, needle)
    return needle


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def C(i, field_name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(w, table, target_id, i, quotation, decision, field_name=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field_name), quotation, decision, **kwargs
    )


def state(w, i, title, type_, time, event, quotation, category, decision,
          field_name=None, *, officer=None, grade=None, note=None):
    eid = w.entity(title, type_, decision, quotation=quotation)
    tid = w.timepoint(
        eid, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer, attr_grade=grade,
        chain="none",
    )
    cite(w, "Timepoints", tid, i, quotation, decision, field_name, note=note)
    return eid, tid


def refine(w, i, eid, time, event, quotation, category, decision,
           field_name=None, *, officer=None, grade=None):
    """用专条细化同一 time 的既有概括节点；不存在时仍按普通节点新建。"""
    tid = w.find_timepoint(eid, time)
    if tid is None:
        title, type_ = w.conn.execute(
            "select title,type from Entities where id=?", (eid,)
        ).fetchone()
        return state(
            w, i, title, type_, time, event, quotation, category, decision,
            field_name, officer=officer, grade=grade,
        )[1]
    row = w.conn.execute(
        "select event,attr_category,attr_officer_type,attr_grade,quotation "
        "from Timepoints where id=?", (tid,)
    ).fetchone()
    new = (event, category, officer, grade, quotation)
    if tuple(row) != new:
        w.conn.execute(
            "update Timepoints set event=?,attr_category=?,attr_officer_type=?,"
            "attr_grade=?,quotation=? where id=?", (*new, tid)
        )
        w._br(
            "Timepoints", tid,
            f"据专条细化既有 {time} 节点：event {row[0]}->{event}、"
            f"category {row[1]}->{category}：{decision}",
        )
    cite(w, "Timepoints", tid, i, quotation, decision, field_name)
    return tid


def relationship(w, i, subject_id, object_id, relation_type, quotation,
                 decision, field_name=None, **kwargs):
    rid = w.relationship(
        subject_id, object_id, relation_type, decision, quotation, **kwargs
    )
    cite(w, "Relationships", rid, i, quotation, decision, field_name)
    return rid


def staff(w, i, parent_tp, post_tp, quotation, decision, field_name=None,
          *, quota=None, staff_type="官"):
    rid = relationship(
        w, i, parent_tp, post_tp, "编制隶属", quotation, decision,
        field_name, staff_quota=quota, staff_type=staff_type,
    )
    row = w.conn.execute(
        "select staff_quota,staff_type from Relationships where id=?", (rid,)
    ).fetchone()
    updates, params = [], []
    if quota is not None and row[0] is None:
        updates.append("staff_quota=?")
        params.append(quota)
    if staff_type and not row[1]:
        updates.append("staff_type=?")
        params.append(staff_type)
    if updates:
        params.append(rid)
        w.conn.execute(
            f"update Relationships set {', '.join(updates)} where id=?", params
        )
        w._br("Relationships", rid, f"补充编制属性：{decision}")
    return rid


def entity_id(w, title, type_):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def timepoint_id(w, title, type_, time):
    eid = entity_id(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


TIME_HINTS = {
    "周代": -1046, "西汉武帝时": -140, "北魏": 386,
    "北宋天圣五年": 1027, "北宋徽宗朝": 1101,
    "北宋崇宁四年八月二十六日": 1105.8,
    "北宋宣和七年二月二十二日": 1125.2,
    "北宋宣和七年十二月二十二日": 1125.9,
    "南宋建炎初": 1127, "南宋建炎二年二月二十日": 1128.2,
    "南宋绍兴间": 1135, "南宋绍兴后": 1135,
    "南宋乾道、淳熙间": 1170, "南宋理宗、度宗朝": 1240,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    m = re.search(r"(\d{3,4})", time or "")
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


def alias_note(w, i, tid, field_name):
    cite(
        w, "Timepoints", tid, i, field(i, field_name),
        f"{F[i]['title']}的简称、别名只作名称证据，不另建实体。",
        field_name, note="纯简称、别名不另建实体",
    )


def entry81_87():
    i = 81
    main = F[i]["text"]
    w = W(i)
    eid, north = state(
        w, i, "部头", "官职", "北宋",
        "教坊每部设部头三人，领本部器乐演奏等事", main,
        "教坊官属", "建立部头北宋职掌、员额节点。", officer="乐工",
    )
    _, south = state(
        w, i, "部头", "官职", "南宋乾道、淳熙间",
        "员额增至十六人，资深者为都部头", main,
        "教坊官属", "建立部头南宋员额节点。", officer="乐工",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋前期"), north, main,
          "北宋教坊置部头三人。", quota=3, staff_type="乐工")
    staff(w, i, timepoint_id(w, "教坊", "机构", "南宋绍兴十四年二月十日"),
          south, main, "南宋教坊仍置部头，乾道、淳熙间十六人。",
          quota=16, staff_type="乐工")
    rechain(w, eid, "补入部头北宋与南宋节点。")
    w.commit()

    i = 82
    main = F[i]["text"]
    w = W(i)
    eid, tp = state(
        w, i, "副部头", "官职", "南宋", "部头副贰，南宋见置", main,
        "教坊官属", "建立副部头南宋节点。", officer="乐工",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "南宋绍兴十四年二月十日"),
          tp, main, "南宋教坊置副部头。", staff_type="乐工")
    rechain(w, eid, "确认副部头南宋节点。")
    w.commit()

    i = 83
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, "都色长", "官职")
    tp = refine(
        w, i, eid, "宋代", "管勾所辖诸色教习，员额或四人或二人", main,
        "教坊官属", "据专条细化都色长职掌、员额。", officer="乐工",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋代"), tp, main,
          "都色长隶教坊，管勾诸色教习。", staff_type="乐工")
    rechain(w, eid, "确认都色长宋代节点。")
    w.commit()

    i = 84
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, "色长", "官职")
    generic = refine(
        w, i, eid, "宋代", "教坊诸色长通称；掌本色教习、演奏及乐器修补", main,
        "教坊官属", "据专条细化色长的通称性质与职掌。", officer="乐工",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋代"), generic, main,
          "每色设色长，掌本色教习、演奏及乐器修补。", staff_type="乐工")
    rechain(w, eid, "确认色长宋代通称节点。")
    w.commit()

    i = 85
    main = F[i]["text"]
    w = W(i)
    eid, tp = state(
        w, i, "筝色长", "官职", "宋代", "筝色所设色长", main,
        "教坊官属", "建立筝色长这一明确实例。", officer="乐工",
    )
    relationship(
        w, i, timepoint_id(w, "色长", "官职", "宋代"), tp,
        "统称与实例", main, "色长是筝色长等各色长的通称。",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋代"), tp, main,
          "筝色长为教坊筝色所设乐工。", staff_type="乐工")
    rechain(w, eid, "确认筝色长宋代节点。")
    w.commit()

    for i, title in ((86, "制撰文字"), (87, "同制撰文字")):
        main = F[i]["text"]
        w = W(i)
        eid = entity_id(w, title, "官职")
        event = (
            "掌教坊乐所用曲调、歌乐词及俳语口号"
            if i == 86 else "制撰文字二人中后进者带同字"
        )
        tp = refine(
            w, i, eid, "宋代", event, main, "教坊官属",
            f"据专条细化{title}职掌或名义。", officer="杂流官",
        )
        quotation = field(i, "别名") if i == 86 else main
        staff(w, i, timepoint_id(w, "教坊", "机构", "宋代"), tp, quotation,
              f"教坊置{title}一人。", "别名" if i == 86 else None,
              quota=1, staff_type="杂流官")
        if i == 86:
            alias_note(w, i, tp, "别名")
        rechain(w, eid, f"确认{title}宋代节点。")
        w.commit()


def entry88_89():
    i = 88
    main, history, duty, rank, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid, start = state(
        w, i, "钤辖教坊所", "机构", "北宋天圣五年",
        "始置，以内侍充，监领、均束教坊事", history,
        "教坊监督机构", "建立钤辖教坊所天圣五年始置节点。", "职源与沿革",
    )
    _, end = state(
        w, i, "钤辖教坊所", "机构", "南宋建炎初", "罢置", history,
        "教坊监督机构", "建立钤辖教坊所建炎初罢置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "记录钤辖教坊所职掌。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录钤辖官所用内侍品位。", "品位")
    cite(w, "Timepoints", start, i, main, "正文确认其为官司。")
    posts = (
        ("钤辖教坊", "内侍差遣", 2),
        ("钤辖教坊所点检文字", "书吏", 1),
        ("钤辖教坊所前行", "书吏", 1),
        ("钤辖教坊所后行", "书吏", 3),
        ("贴司", "书吏", 2),
    )
    touched = {eid}
    for title, officer, quota in posts:
        post_eid, post = state(
            w, i, title, "官职", "北宋天圣五年",
            f"钤辖教坊所置{title}，员额{quota}人", roster,
            "钤辖教坊所官属", f"据专条编制建立{title}精确节点。", "编制",
            officer=officer,
        )
        staff(w, i, start, post, roster, f"钤辖教坊所置{title}{quota}人。",
              "编制", quota=quota, staff_type=officer)
        touched.add(post_eid)
    for touched_eid in touched:
        rechain(w, touched_eid, "补入钤辖教坊所天圣五年精确编制节点。")
    assert end
    w.commit()

    i = 89
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid, start = state(
        w, i, "钤辖教坊", "官职", "北宋天圣五年",
        "始置，以供奉官以下内侍官充", main,
        "钤辖教坊所官属", "建立钤辖教坊天圣五年始置节点。",
        officer="内侍差遣",
    )
    _, survive = state(
        w, i, "钤辖教坊", "官职", "南宋建炎初",
        "钤辖教坊所已罢，钤辖教坊官名尚存", main,
        "内侍差遣", "建立所罢而官名尚存节点。", officer="内侍差遣",
    )
    _, end = state(
        w, i, "钤辖教坊", "官职", "南宋建炎二年二月二十日",
        "罢内侍兼钤辖教坊官名，更不差置", main,
        "内侍差遣", "建立钤辖教坊官名正式罢止节点。", officer="内侍差遣",
    )
    staff(w, i, timepoint_id(w, "钤辖教坊所", "机构", "北宋天圣五年"),
          start, main, "天圣五年钤辖教坊隶钤辖教坊所。",
          quota=2, staff_type="内侍差遣")
    alias_note(w, i, end, "简称")
    rechain(w, eid, "整理钤辖教坊始置、所罢名存及官名罢止链。")
    assert aliases and survive
    w.commit()


def entry90_94():
    i = 90
    main, history, duty, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"),
    )
    w = W(i)
    repair_eid, repair = state(
        w, i, "修内司", "机构", "宋代", "下辖教乐所", main,
        "内廷修造机构", "据正文建立修内司承载节点。",
    )
    eid, generic = state(
        w, i, "教乐所", "机构", "宋代", "隶修内司", main,
        "宫廷音乐机构", "建立教乐所宋代隶属节点。",
    )
    _, huizong = state(
        w, i, "教乐所", "机构", "北宋徽宗朝", "见置", history,
        "宫廷音乐机构", "建立教乐所徽宗朝见置节点。", "职源与沿革",
    )
    _, first_end = state(
        w, i, "教乐所", "机构", "北宋宣和七年二月二十二日", "罢置",
        history, "宫廷音乐机构", "建立教乐所宣和七年罢置节点。", "职源与沿革",
    )
    _, restore = state(
        w, i, "教乐所", "机构", "南宋绍兴间", "复置", history,
        "宫廷音乐机构", "建立教乐所绍兴间复置节点。", "职源与沿革",
    )
    _, late = state(
        w, i, "教乐所", "机构", "南宋理宗、度宗朝", "仍设", history,
        "宫廷音乐机构", "建立教乐所理、度宗朝仍设节点。", "职源与沿革",
    )
    cite(w, "Timepoints", restore, i, duty, "记录教乐所点集衙前乐入所教习供奉。", "职掌")
    cite(w, "Timepoints", restore, i, roster, "记录教乐所模拟教坊的编制及乐人数。", "编制")
    relationship(w, i, repair, generic, "上下级机构", main,
                 "正文明确教乐所隶修内司。")
    yamen_eid, yamen = state(
        w, i, "衙前乐", "机构", "南宋绍兴后",
        "由教乐所点集入所教习，充当教坊乐部供奉", duty,
        "州府乐部", "据教乐所职掌建立衙前乐绍兴后承应节点。", "职掌",
    )
    for title, officer in (("都管", "伶官"), ("部头", "乐工"), ("色长", "乐工")):
        post_eid, post = state(
            w, i, title, "官职", "南宋绍兴间",
            f"教乐所模拟教坊编制设{title}，由州府衙前乐伶人充任", roster,
            "教乐所官属", f"建立{title}在教乐所模拟编制中的节点。", "编制",
            officer=officer,
        )
        staff(w, i, restore, post, roster, f"教乐所点集乐部时设{title}。",
              "编制", staff_type=officer)
        rechain(w, post_eid, f"补入{title}南宋绍兴间教乐所节点。")
    rechain(w, repair_eid, "确认修内司宋代节点。")
    rechain(w, eid, "整理教乐所徽宗、宣和、绍兴及理度宗节点。")
    rechain(w, yamen_eid, "建立衙前乐绍兴后节点。")
    assert huizong and first_end and late and yamen
    w.commit()

    i = 91
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid, generic = state(
        w, i, "衙前乐", "机构", "宋代", "州、府教集的乐部及妓女", main,
        "州府乐部", "建立衙前乐宋代制度节点。",
    )
    _, south = state(
        w, i, "衙前乐", "机构", "南宋绍兴后",
        "教乐所拨充教坊乐部，承应禁庭宣唤；都管以下三百人", main,
        "州府乐部", "补证衙前乐绍兴后职能与总人数。",
    )
    roles = (
        ("衙前乐都管", "杂流伶官"), ("衙前乐守阙都管", "杂流伶官"),
        ("管干教头", "伶官"), ("教头", "乐工"),
        ("衙前乐副都头", "杂流伶官"), ("色长", "乐工"),
        ("衙前乐节级", "杂流伶官"),
    )
    touched = {eid}
    for title, officer in roles:
        post_eid, post = state(
            w, i, title, "官职", "南宋绍兴后", f"衙前乐设{title}", main,
            "衙前乐官属", f"据衙前乐编制建立{title}。", officer=officer,
        )
        staff(w, i, south, post, main, f"衙前乐伶官列有{title}。",
              staff_type=officer)
        touched.add(post_eid)
    alias_note(w, i, south, "简称")
    for touched_eid in touched:
        rechain(w, touched_eid, "补入衙前乐绍兴后编制节点。")
    assert generic and aliases
    w.commit()

    assert F[92]["text"] == ""
    assert F[92]["fields"].get("__status__") == "placeholder"
    # 核第五编 PDF p307，原“衙前”条位是错误切分；保留占位且不写四表。

    i = 93
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid = entity_id(w, "衙前乐都管", "官职")
    tp = refine(
        w, i, eid, "南宋绍兴后",
        "正名都管二人，总领衙前乐部入宫演出事", main,
        "衙前乐官属", "补证衙前乐都管职掌与员额。", officer="杂流伶官",
    )
    staff(w, i, timepoint_id(w, "衙前乐", "机构", "南宋绍兴后"), tp, main,
          "衙前乐置正名都管二人。", quota=2, staff_type="杂流伶官")
    alias_note(w, i, tp, "简称")
    rechain(w, eid, "确认衙前乐都管绍兴后节点。")
    assert aliases
    w.commit()

    i = 94
    assert "和雇伶人名" in F[i]["text"]
    assert "候衙前乐有阙" in F[i]["text"]
    assert field(i, "简称")
    # “守阙衙前”是候补资格的和雇伶人称谓，不是机构或官职，不伪造实体。


def entry95():
    i = 95
    main, history, duty, order, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "序位"), field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, start = state(
        w, i, "大晟府", "机构", "北宋崇宁四年八月二十六日",
        "始置，专掌朝廷典礼所用乐", history,
        "中央音乐机构", "建立大晟府精确始置日节点。", "职源与沿革",
    )
    _, end = state(
        w, i, "大晟府", "机构", "北宋宣和七年十二月二十二日", "罢置",
        history, "中央音乐机构", "建立大晟府宣和七年罢置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "记录大晟府专掌典礼用乐。", "职掌")
    cite(w, "Timepoints", start, i, order, "记录大晟府与寺监同序且次太常寺。", "序位")
    cite(w, "Timepoints", start, i, main, "正文明确大晟府隶尚书省礼部。")
    alias_note(w, i, start, "简称与别名")

    ritual_eid, ritual = state(
        w, i, "礼部", "机构", "北宋崇宁四年八月二十六日",
        "下辖大晟府", history, "尚书省六部之一",
        "为大晟府精确隶属建立礼部同期节点。", "职源与沿革",
    )
    relationship(w, i, ritual, start, "上下级机构", main,
                 "大晟府隶尚书省礼部。")

    official_specs = (
        ("大司乐", "乐官"), ("典乐", "乐官"),
        ("大晟府大乐令", "乐官"), ("大晟府主簿", "职事官"),
        ("大晟府协律郎", "乐官"), ("大晟府按协声律", "乐官"),
        ("大晟府制撰文字", "杂流官"), ("大晟府运谱", "杂流官"),
        ("大晟府掌事", "杂流官"),
    )
    touched = {eid, ritual_eid}
    for title, officer in official_specs:
        post_eid, post = state(
            w, i, title, "官职", "北宋崇宁四年八月二十六日",
            f"大晟府始置时列官额：{title}", roster,
            "大晟府官属", f"据大晟府编制建立{title}。", "编制",
            officer=officer,
        )
        staff(w, i, start, post, roster, f"大晟府官额列{title}。", "编制",
              staff_type=officer)
        touched.add(post_eid)

    office_eid, office = state(
        w, i, "提举大晟府所", "机构", "北宋崇宁四年八月二十六日",
        "大晟府始置时见设，由内侍官充", roster, "大晟府相关官司",
        "编制明确另有提举大晟府所；按官司建实体，暂不推断隶属方向。", "编制",
    )
    touched.add(office_eid)
    assert office

    for title in ("教坊", "钤辖教坊所"):
        if title == "教坊":
            child_eid = entity_id(w, title, "机构")
            child = timepoint_id(w, title, "机构", "北宋崇宁四年八月")
        else:
            child_eid, child = state(
                w, i, title, "机构", "北宋崇宁四年八月二十六日",
                "隶大晟府", roster, "大晟府所属乐司",
                "建立钤辖教坊所隶大晟府节点。", "编制",
            )
        relationship(w, i, start, child, "上下级机构", roster,
                     f"大晟府所隶乐司有{title}。", "编制")
        touched.add(child_eid)

    for short in ("大乐", "鼓吹", "宴乐", "法物", "知杂", "掌法"):
        title = f"大晟府{short}案"
        case_eid, case = state(
            w, i, title, "机构", "北宋崇宁四年八月二十六日",
            f"大晟府下辖{short}案", roster, "大晟府所属案",
            f"据大晟府六案编制建立{title}。", "编制",
        )
        relationship(w, i, start, case, "上下级机构", roster,
                     f"{title}为大晟府六案之一。", "编制")
        touched.add(case_eid)

    for short in ("胥长", "胥史", "胥佐", "贴书", "专知", "副知", "库子"):
        title = f"大晟府{short}"
        post_eid, post = state(
            w, i, title, "官职", "北宋崇宁四年八月二十六日",
            f"大晟府吏额列{short}", roster, "大晟府吏额",
            f"据大晟府吏额建立{title}。", "编制", officer="书吏",
        )
        staff(w, i, start, post, roster, f"大晟府吏额列{short}。", "编制",
              staff_type="书吏")
        touched.add(post_eid)

    for short in (
        "乐正", "乐师", "色长", "引舞", "舞头", "舞郎",
        "上工", "中工", "下工", "舞师",
    ):
        title = f"大晟府{short}"
        post_eid, post = state(
            w, i, title, "官职", "北宋崇宁四年八月二十六日",
            f"大晟府乐工列{short}", roster, "大晟府乐工",
            f"据大晟府乐工编制建立{title}。", "编制", officer="乐工",
        )
        staff(w, i, start, post, roster, f"大晟府乐工列{short}。", "编制",
              staff_type="乐工")
        touched.add(post_eid)

    for touched_eid in touched:
        rechain(w, touched_eid, "补入大晟府精确始置及完整编制节点。")
    assert end and aliases
    w.commit()


def dacheng_post(i, title, history_name, duty_name, rank_name, event, category,
                 officer, grade=None, prehistory=None):
    main = F[i]["text"]
    history = field(i, history_name)
    duty = field(i, duty_name)
    rank = field(i, rank_name)
    w = W(i)
    eid = entity_id(w, title, "官职")
    if prehistory:
        old_time, old_event = prehistory
        state(
            w, i, title, "官职", old_time, old_event, history,
            "前代职源", f"建立{title}{old_time}职源节点。", history_name,
            officer="前代乐官",
        )
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日", event,
        history, category, f"据专条细化{title}始置节点。", history_name,
        officer=officer, grade=grade,
    )
    end = refine(
        w, i, eid, "北宋宣和七年十二月二十二日",
        "随大晟府罢置", history, category, f"建立{title}随府罢置节点。",
        history_name, officer=officer, grade=grade,
    )
    cite(w, "Timepoints", start, i, duty, f"记录{title}职掌。", duty_name)
    cite(w, "Timepoints", start, i, rank, f"记录{title}品位。", rank_name)
    cite(w, "Timepoints", start, i, main, f"正文明确{title}隶大晟府。")
    staff(
        w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
        start, main, f"{title}隶大晟府。", staff_type=officer,
    )
    rechain(w, eid, f"整理{title}职源、始置及罢置链。")
    assert end
    w.commit()


def entry96_100():
    dacheng_post(
        96, "大司乐", "职源与沿革", "职掌", "品位",
        "大晟府长官，总领本府事", "大晟府长官", "乐官", "正四品",
        prehistory=("周代", "《周礼》已有大司乐之职"),
    )
    dacheng_post(
        97, "典乐", "职源", "职掌", "品位",
        "大晟府副长官，佐领本府事", "大晟府副长官", "乐官", "从五品",
    )
    dacheng_post(
        98, "大晟府大乐令", "职源", "职掌", "品位",
        "参掌大晟府事", "大晟府乐官", "乐官", "从七品",
    )
    i = 98
    w = W(i)
    tp = timepoint_id(w, "大晟府大乐令", "官职", "北宋崇宁四年八月二十六日")
    alias_note(w, i, tp, "简称")
    w.commit()

    i = 99
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, "大晟府主簿", "官职")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日",
        "随大晟府置，勾考本府簿书及出纳事", main,
        "大晟府职事官", "补证大晟府主簿置废、职掌与品秩。",
        officer="职事官", grade="从八品",
    )
    end = refine(
        w, i, eid, "北宋宣和七年十二月二十二日",
        "随大晟府罢置", main, "大晟府职事官",
        "建立大晟府主簿随府罢置节点。", officer="职事官", grade="从八品",
    )
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "大晟府主簿隶大晟府。", staff_type="职事官")
    rechain(w, eid, "整理大晟府主簿始置与罢置链。")
    assert end
    w.commit()

    i = 100
    main, history, duty, rank = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品秩"),
    )
    w = W(i)
    old_eid = entity_id(w, "太常寺协律郎", "官职")
    for time in ("西汉武帝时", "北魏"):
        old = timepoint_id(w, "太常寺协律郎", "官职", time)
        cite(w, "Timepoints", old, i, history, "补证协律官职源。", "职源与沿革")
    eid = entity_id(w, "大晟府协律郎", "官职")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日",
        "随大晟府置，协调钟律", history, "大晟府乐官",
        "补证大晟府协律郎随府置废。", "职源与沿革", officer="乐官",
        grade="位从八品下、从九品上",
    )
    end = refine(
        w, i, eid, "北宋宣和七年十二月二十二日",
        "随大晟府罢置", history, "大晟府乐官",
        "建立大晟府协律郎随府罢置节点。", "职源与沿革", officer="乐官",
        grade="位从八品下、从九品上",
    )
    cite(w, "Timepoints", start, i, duty, "记录大晟府协律郎协调钟律。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录其班序在从八品与从九品官之间。", "品秩")
    cite(w, "Timepoints", start, i, main, "正文明确协律郎隶大晟府。")
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "大晟府协律郎隶大晟府。", staff_type="乐官")
    rechain(w, old_eid, "补充第100条对太常寺协律郎前代职源的证据。")
    rechain(w, eid, "整理大晟府协律郎始置与罢置链。")
    assert end
    w.commit()


def main():
    assert [F[i]["title"] for i in range(81, 101)] == [
        "部头", "副部头", "都色长", "色长", "筝色长", "制撰文字",
        "同制撰文字", "钤辖教坊所", "钤辖教坊", "教乐所", "衙前乐",
        "衙前", "衙前乐都管", "守阙衙前", "大晟府", "大司乐",
        "典乐", "大乐令", "主簿", "协律郎",
    ]
    entry81_87()
    entry88_89()
    entry90_94()
    entry95()
    entry96_100()


if __name__ == "__main__":
    main()
