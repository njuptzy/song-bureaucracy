#!/usr/bin/env python3
"""提取 chapter5t7 第61-80条：斋郎、籍田司及教坊前半系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_041_060 as previous


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


F = {i: load(i) for i in range(61, 81)}


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


def relationship(w, i, subject_id, object_id, relation_type, quotation,
                 decision, field_name=None, **kwargs):
    rid = w.relationship(
        subject_id, object_id, relation_type, decision, quotation, **kwargs
    )
    cite(w, "Relationships", rid, i, quotation, decision, field_name)
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
    "西汉文帝时": -170, "隋": 581, "唐武德间": 618,
    "唐开元二年": 714, "北宋太宗至道三年": 997,
    "北宋元丰三年后": 1080, "北宋元丰五年": 1082,
    "北宋崇宁四年八月": 1105, "南宋初": 1127,
    "南宋绍兴十四年二月十日": 1144,
    "南宋绍兴十五年": 1145, "南宋绍兴三十一年六月": 1161.5,
    "南宋绍兴三十一年": 1161, "南宋绍兴三十一年后": 1162,
    "南宋孝宗朝": 1163,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    m = re.search(r"(\d{3,4})", time or "")
    if m:
        return (int(m.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, entity_id, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (entity_id,)
    ).fetchall()
    ordered = [r[0] for r in sorted(rows, key=lambda r: time_key(r[1], r[0]))]
    for n, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[n - 1] if n else None,
            succ_id=ordered[n + 1] if n + 1 < len(ordered) else None,
        )


def parent_state(w, i, title, time, event, quotation, category, field_name=None):
    return state(
        w, i, title, "机构", time, event, quotation, category,
        f"据{F[i]['title']}条建立{title}{time}制度状态。", field_name,
    )


def staff(w, i, parent_tp, post_tp, quotation, decision, field_name=None,
          *, quota=None, staff_type="官"):
    return relationship(
        w, i, parent_tp, post_tp, "编制隶属", quotation, decision,
        field_name, staff_quota=quota, staff_type=staff_type,
    )


def alias_note(w, i, tid, field_name):
    cite(
        w, "Timepoints", tid, i, field(i, field_name),
        f"{F[i]['title']}纯简称、别名只作名称证据，不另建实体。",
        field_name, note="纯简称、别名不另建实体",
    )


def entry61():
    i = 61
    main, history, duty, order, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职能"),
        field(i, "序位"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    office_eid, sui_office = state(
        w, i, "郊社署", "机构", "隋", "置斋郎", history,
        "太常寺所属祠祭机构", "建立郊社署隋代节点。", "职源与沿革",
    )
    eid, sui = state(
        w, i, "郊社斋郎", "官职", "隋", "郊社署始置斋郎", history,
        "前代祠祭官", "建立郊社斋郎隋代职源节点。", "职源与沿革",
        officer="非品官",
    )
    _, song = state(
        w, i, "郊社斋郎", "官职", "北宋", "沿置；兼祠祭行事官与荫补起家官",
        history, "太常寺非品祠祭官", "建立郊社斋郎北宋沿置节点。", "职源与沿革",
        officer="非品官",
    )
    _, quota = state(
        w, i, "郊社斋郎", "官职", "北宋建隆四年六月",
        "与太庙斋郎合计每年奏补十五人，后多无定额", roster,
        "太常寺非品祠祭官", "提取建隆四年斋郎合计奏补员额。", "编制",
        officer="非品官", note="十五人为太庙、郊社斋郎合计，不单计为本职员额",
    )
    _, promotion = state(
        w, i, "郊社斋郎", "官职", "北宋奏补满五年",
        "可迁掌坐，由掌坐可望补选品官", order, "太常寺非品祠祭官",
        "记录郊社斋郎奏补满五年的迁转资格。", "序位", officer="非品官",
    )
    cite(w, "Timepoints", song, i, duty, "记录郊社斋郎荫补与祠祭职能。", "职能")
    cite(w, "Timepoints", song, i, main, "正文明确郊社斋郎隶太常寺。")
    alias_note(w, i, song, "简称")
    temple = parent_state(w, i, "太常寺", "北宋", "沿置郊社斋郎", main,
                          "中央礼制机构")[1]
    staff(w, i, sui_office, sui, history, "隋郊社署置斋郎。", "职源与沿革",
          staff_type="非品官")
    staff(w, i, temple, song, main, "北宋郊社斋郎隶太常寺。", staff_type="非品官")
    rechain(w, office_eid, "整理郊社署时间链。")
    rechain(w, eid, "整理郊社斋郎隋、建隆、北宋及迁转节点。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入郊社斋郎相关太常寺节点。")
    assert quota and promotion
    w.commit()


def entry62():
    i = 62
    main = F[i]["text"]
    w = W(i)
    eid, generic = state(
        w, i, "斋郎", "官职", "宋代", "郊社斋郎、太庙斋郎通称",
        main, "非品祠祭官统称", "建立斋郎通称节点。", officer="非品官",
    )
    for title, time in (
        ("郊社斋郎", "北宋"),
        ("太庙斋郎", "北宋大中祥符七年八月庚辰"),
    ):
        relationship(w, i, generic, timepoint_id(w, title, "官职", time),
                     "统称与实例", main, f"斋郎是{title}等两类官的通称。")
    rechain(w, eid, "确认斋郎宋代通称节点。")
    w.commit()


def entry63():
    i = 63
    main, history, duty, grade, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职能"),
        field(i, "品位"), field(i, "别名"),
    )
    w = W(i)
    office_eid, tang_office = state(
        w, i, "郊社署", "机构", "唐", "下设掌坐", history,
        "太常寺所属祠祭机构", "建立郊社署唐代掌坐编制节点。", "职源与沿革",
    )
    eid, tang = state(
        w, i, "掌坐", "官职", "唐", "郊社署下设，掌郊坛神御之物", history,
        "前代祠祭官", "建立掌坐唐代职源节点。", "职源与沿革", officer="非品官",
    )
    _, song = state(
        w, i, "掌坐", "官职", "北宋", "沿置；为郊社斋郎迁转阶",
        history, "太常寺非品祠祭官", "建立掌坐北宋沿置节点。", "职源与沿革",
        officer="非品官",
    )
    cite(w, "Timepoints", song, i, duty, "记录掌坐为斋郎迁转阶。", "职能")
    cite(w, "Timepoints", song, i, grade, "记录掌坐无品及序位。", "品位")
    cite(w, "Timepoints", song, i, main, "正文明确掌坐隶太常寺。")
    alias_note(w, i, song, "别名")
    temple = timepoint_id(w, "太常寺", "机构", "北宋")
    staff(w, i, tang_office, tang, history, "唐郊社署下设掌坐。", "职源与沿革",
          staff_type="非品官")
    staff(w, i, temple, song, main, "北宋掌坐隶太常寺。", staff_type="非品官")
    rechain(w, office_eid, "整理郊社署隋唐时间链。")
    rechain(w, eid, "整理掌坐唐与北宋时间链。")
    w.commit()


def entry64():
    i = 64
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid, tp = state(
        w, i, "挽郎", "官职", "北宋太宗至道三年", "始见置；门荫官兼大葬行事官",
        main, "荫补行事官", "建立挽郎至道三年始见置节点。", officer="非品官",
    )
    alias_note(w, i, tp, "简称")
    rechain(w, eid, "确认挽郎至道三年节点。")
    assert aliases
    w.commit()


def entry65():
    i = 65
    main = F[i]["text"]
    w = W(i)
    eid, early = state(
        w, i, "礼官", "官职", "宋前期", "太常礼院、礼仪院官泛称",
        main, "礼制官统称", "建立礼官宋前期通称节点。",
    )
    _, reform = state(
        w, i, "礼官", "官职", "北宋元丰正名后",
        "礼部官及太常寺卿至少卿、博士、丞、主簿等泛称", main,
        "礼制官统称", "建立礼官元丰正名后通称节点。",
    )
    instances = (
        ("礼部侍郎", "北宋元丰新制"),
        ("礼部郎中", "北宋元丰新制"),
        ("礼部员外郎", "北宋元丰五年"),
        ("祠部司郎中", "北宋元丰新制"),
        ("祠部司员外郎", "北宋元丰新制"),
        ("太常寺卿", "北宋元丰改制后"),
        ("太常寺少卿", "北宋元丰五年新制"),
        ("太常寺博士", "北宋元丰改制后"),
        ("太常寺丞", "北宋元丰新制"),
        ("太常寺主簿", "北宋元丰新制"),
    )
    for title, time in instances:
        relationship(w, i, reform, timepoint_id(w, title, "官职", time),
                     "统称与实例", main, f"元丰正名后{title}属于礼官实例。")
    rechain(w, eid, "连接礼官宋前期与元丰正名后节点。")
    assert early
    w.commit()


def entry66():
    i = 66
    main, history, duty, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    )
    w = W(i)
    eid, han = state(
        w, i, "籍田司", "机构", "西汉文帝时", "始置籍田令丞，以官为司",
        history, "籍田礼事务机构", "建立籍田司西汉职源节点。", "职源与沿革",
    )
    _, north = state(
        w, i, "籍田司", "机构", "北宋", "设置但不常置", history,
        "太常寺所属籍田机构", "建立籍田司北宋状态。", "职源与沿革",
    )
    _, restore = state(
        w, i, "籍田司", "机构", "南宋绍兴十五年", "复置", history,
        "太常寺所属籍田机构", "建立籍田司绍兴十五年复置节点。", "职源与沿革",
    )
    _, abolish = state(
        w, i, "籍田司", "机构", "南宋绍兴三十一年", "罢置", history,
        "太常寺所属籍田机构", "建立籍田司绍兴三十一年罢置节点。", "职源与沿革",
    )
    _, again = state(
        w, i, "籍田司", "机构", "南宋绍兴三十一年后", "后又复置", history,
        "太常寺所属籍田机构", "建立籍田司绍兴三十一年后复置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", north, i, duty, "记录籍田司筹备亲耕及祠祭礼料职掌。", "职掌")
    cite(w, "Timepoints", north, i, roster, "记录籍田司设籍田令等编制。", "编制")
    cite(w, "Timepoints", north, i, main, "正文明确籍田司隶太常寺。")
    temple = parent_state(w, i, "太常寺", "北宋", "籍田司隶属", main,
                          "中央礼制机构")[1]
    relationship(w, i, temple, north, "上下级机构", main, "北宋籍田司隶太常寺。")
    for time, office_tp in (
        ("南宋绍兴十五年", restore),
        ("南宋绍兴三十一年后", again),
    ):
        temple_tp = parent_state(w, i, "太常寺", time, "籍田司复置", history,
                                 "中央礼制机构", "职源与沿革")[1]
        relationship(w, i, temple_tp, office_tp, "上下级机构", main,
                     f"{time}复置的籍田司隶太常寺。")
    rechain(w, eid, "整理籍田司西汉、北宋及南宋复罢时间链。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入籍田司相关太常寺节点。")
    assert han and abolish
    w.commit()


def entry67():
    i = 67
    main, history, duty, grade, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "简称"),
    )
    w = W(i)
    eid, han = state(
        w, i, "籍田司令", "官职", "西汉文帝时", "始置籍田令", history,
        "前代籍田官", "建立籍田司令西汉职源节点。", "职源与沿革", officer="长官",
    )
    _, song = state(
        w, i, "籍田司令", "官职", "两宋", "沿置而不常", history,
        "籍田司长官", "建立籍田司令两宋沿置节点。", "职源与沿革", officer="长官",
        grade="正九品",
    )
    _, yuanfeng = state(
        w, i, "籍田司令", "官职", "北宋元丰三年后", "隶太常寺，领籍田司事",
        main, "太常寺籍田官", "建立籍田司令元丰三年后节点。", officer="差遣官",
        grade="正九品",
    )
    cite(w, "Timepoints", yuanfeng, i, duty, "记录籍田司令领司事。", "职掌")
    cite(w, "Timepoints", yuanfeng, i, grade, "记录籍田司令正九品。", "品位")
    _, restore = state(
        w, i, "籍田司令", "官职", "南宋绍兴十五年", "复置并初除籍田令",
        aliases, "籍田司长官", "提取绍兴十五年籍田令复置。", "简称", officer="差遣官",
        grade="正九品",
    )
    _, abolish = state(
        w, i, "籍田司令", "官职", "南宋绍兴三十一年", "随籍田司权罢",
        aliases, "籍田司长官", "提取绍兴三十一年籍田令罢置。", "简称", officer="差遣官",
        grade="正九品",
    )
    _, again = state(
        w, i, "籍田司令", "官职", "南宋绍兴三十一年后", "后复置",
        aliases, "籍田司长官", "提取绍兴三十一年后籍田令复置。", "简称",
        officer="差遣官", grade="正九品",
    )
    alias_note(w, i, again, "简称")
    assistant_eid, assistant_han = state(
        w, i, "籍田丞", "官职", "西汉文帝时", "与籍田令同时始置", history,
        "前代籍田官", "建立籍田丞西汉职源节点。", "职源与沿革", officer="佐贰官",
    )
    _, assistant_song = state(
        w, i, "籍田丞", "官职", "两宋", "沿置而不常", history,
        "籍田司佐贰官", "建立籍田丞两宋沿置节点。", "职源与沿革", officer="佐贰官",
    )
    office_yuanfeng = state(
        w, i, "籍田司", "机构", "北宋元丰三年后", "籍田司令隶太常寺并领司事",
        main, "太常寺所属籍田机构", "建立籍田司元丰三年后节点。",
    )[1]
    temple_yuanfeng = parent_state(w, i, "太常寺", "北宋元丰三年后",
                                   "籍田司令隶属", main, "中央礼制机构")[1]
    relationship(w, i, temple_yuanfeng, office_yuanfeng, "上下级机构", main,
                 "元丰三年后籍田司隶太常寺。")
    staff(w, i, office_yuanfeng, yuanfeng, aliases, "籍田令二员。", "简称",
          quota=2, staff_type="差遣官")
    for time, post_tp in (
        ("南宋绍兴十五年", restore),
        ("南宋绍兴三十一年后", again),
    ):
        staff(w, i, timepoint_id(w, "籍田司", "机构", time), post_tp, aliases,
              f"{time}籍田司置籍田令。", "简称", staff_type="差遣官")
    for touched in (eid, assistant_eid, entity_id(w, "籍田司", "机构"),
                    entity_id(w, "太常寺", "机构")):
        rechain(w, touched, "插入籍田司令相关节点并按历史顺序重链。")
    assert han and song and abolish and assistant_han and assistant_song
    w.commit()


def entry68():
    assert F[68]["title"] == "甲头"
    assert "农人" in F[68]["text"]
    # 原文明确是籍田司农人，而非机构或官职；四表对象范围不支持，故不伪造数据。


def entry69():
    i = 69
    main = F[i]["text"]
    w = W(i)
    eid, tp = state(
        w, i, "耕籍使", "官职", "宋代", "宰相兼任，陪侍亲耕行三推礼，事毕即罢",
        main, "籍田礼临时行事官", "建立耕籍使宋代临时行事节点。", officer="行事官",
    )
    rechain(w, eid, "确认耕籍使宋代节点。")
    assert tp
    w.commit()


def entry70():
    i = 70
    main, history, duty, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    )
    w = W(i)
    eid, tang = state(
        w, i, "教坊", "机构", "唐武德间", "置于禁门之内，掌俳优、杂剧",
        history, "宫廷音乐机构", "建立教坊唐代职源节点。", "职源与沿革",
    )
    _, song = state(
        w, i, "教坊", "机构", "宋前期", "沿置，隶宣徽院", main,
        "宣徽院所属音乐机构", "建立教坊宋前期隶属节点。",
    )
    _, song_roster = state(
        w, i, "教坊", "机构", "宋初", "分部、分色并设置伶官与书吏",
        roster, "宫廷音乐机构", "建立教坊宋初编制节点。", "编制",
    )
    _, song_general = state(
        w, i, "教坊", "机构", "宋代", "设置伶官及诸部、诸色",
        roster, "宫廷音乐机构", "建立教坊宋代官属承载节点。", "编制",
    )
    _, reform = state(
        w, i, "教坊", "机构", "北宋元丰五年", "新官制改隶太常寺", main,
        "太常寺所属音乐机构", "建立教坊元丰五年改隶节点。",
    )
    _, dacheng = state(
        w, i, "教坊", "机构", "北宋崇宁四年八月", "改隶大晟府", main,
        "大晟府所属音乐机构", "建立教坊崇宁四年改隶节点。",
    )
    _, south_end = state(
        w, i, "教坊", "机构", "南宋初", "省罢", history,
        "宫廷音乐机构", "建立教坊南宋初省罢节点。", "职源与沿革",
    )
    _, south_restore = state(
        w, i, "教坊", "机构", "南宋绍兴十四年二月十日", "复设，乐工四百六十人",
        history, "宫廷音乐机构", "建立教坊绍兴十四年复设节点。", "职源与沿革",
    )
    cite(w, "Timepoints", south_restore, i, roster, "补证绍兴十四年教坊乐工四百六十人。", "编制")
    _, south_abolish = state(
        w, i, "教坊", "机构", "南宋绍兴三十一年六月", "罢置", history,
        "宫廷音乐机构", "建立教坊绍兴三十一年罢置节点。", "职源与沿革",
    )
    _, xiaozong = state(
        w, i, "教坊", "机构", "南宋孝宗朝", "曾权置", history,
        "宫廷音乐机构", "建立教坊孝宗朝权置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", song_general, i, duty, "记录教坊演奏、教习和考核职掌。", "职掌")

    xuanhui = parent_state(w, i, "宣徽院", "宋前期", "教坊所属上级", main,
                           "中央宫廷机构")[1]
    temple = parent_state(w, i, "太常寺", "北宋元丰五年", "教坊改隶",
                          main, "中央礼乐机构")[1]
    relationship(w, i, xuanhui, song, "上下级机构", main, "宋前期教坊隶宣徽院。")
    relationship(w, i, temple, reform, "上下级机构", main, "元丰五年教坊改隶太常寺。")
    relationship(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月"),
                 dacheng, "上下级机构", main, "崇宁四年八月教坊改隶大晟府。")

    parts_quote = Q(
        i,
        "宋初,教坊分四部(法曲部、龟兹部、鼓笛部、方响部),后又增贴部。"
        "南宋时已有筚篥部、大鼓部、拍板部等部名",
        "编制",
    )
    for title, time in (
        ("法曲部", "宋初"), ("龟兹部", "宋初"), ("鼓笛部", "宋初"),
        ("方响部", "宋初"), ("贴部", "宋初"),
        ("筚篥部", "南宋"), ("大鼓部", "南宋"), ("拍板部", "南宋"),
    ):
        _, child = state(
            w, i, title, "机构", time, "教坊所属部", parts_quote,
            "教坊内部乐部", f"据教坊编制建立{title}。", "编制",
        )
        parent = song_roster if time == "宋初" else south_restore
        relationship(w, i, parent, child, "上下级机构", parts_quote,
                     f"{title}为教坊所属乐部。", "编制")
        rechain(w, entity_id(w, title, "机构"), f"确认{title}时间链。")

    colors_quote = Q(
        i,
        "色有杂剧色、板色、歌色、琵琶色、箜篌色、笙色、筝色、箫色、"
        "觱篥色、方响色、笛色、头板色、拍板色、参军色、杖头色、大鼓色、"
        "羯鼓色、舞旋色等。",
        "编制",
    )
    colors = (
        "杂剧色", "板色", "歌色", "琵琶色", "箜篌色", "笙色", "筝色", "箫色",
        "觱篥色", "方响色", "笛色", "头板色", "拍板色", "参军色", "杖头色",
        "大鼓色", "羯鼓色", "舞旋色",
    )
    for title in colors:
        _, child = state(
            w, i, title, "机构", "宋代", "教坊所属色", colors_quote,
            "教坊内部乐色", f"据教坊编制建立{title}。", "编制",
        )
        relationship(w, i, song_general, child, "上下级机构", colors_quote,
                     f"{title}为教坊所属乐色。", "编制")

    officials_quote = Q(
        i,
        "伶官有教坊使一人、教坊副使二人。此外有判官、都色长、都部头、"
        "色长、部头、高班都知、都知、教头等,以及制撰文字、同制撰文字,"
        "其员额不定。",
        "编制",
    )
    officials = (
        ("教坊使", "伶官", 1), ("教坊副使", "伶官", 2),
        ("教坊判官", "伶官", None), ("都色长", "乐工", None),
        ("都部头", "乐工", None), ("色长", "乐工", None),
        ("部头", "乐工", None), ("高班都知", "伶官", None),
        ("都知", "伶官", None), ("教头", "乐工", None),
        ("制撰文字", "杂流官", None), ("同制撰文字", "杂流官", None),
    )
    for title, officer, quota in officials:
        _, post = state(
            w, i, title, "官职", "宋代", f"教坊置{title}", officials_quote,
            "教坊官属", f"据教坊编制建立{title}。", "编制", officer=officer,
        )
        staff(w, i, song_general, post, officials_quote, f"教坊编制列{title}。", "编制",
              quota=quota, staff_type=officer)

    clerk_quote = Q(
        i,
        "天圣间以内侍二人为钤辖官,别置钤辖教坊所。书吏有手分、贴司各二人",
        "编制",
    )
    _, control = state(
        w, i, "钤辖教坊所", "机构", "北宋天圣间", "别置，钤辖教坊",
        clerk_quote, "教坊监督机构", "建立钤辖教坊所天圣节点。", "编制",
    )
    _, tian_sheng = state(
        w, i, "教坊", "机构", "北宋天圣间", "别置钤辖教坊所",
        clerk_quote, "宫廷音乐机构", "建立教坊天圣间监督机构节点。", "编制",
    )
    relationship(w, i, tian_sheng, control, "上下级机构", clerk_quote,
                 "教坊系统别置钤辖教坊所。", "编制")
    for title, officer, quota in (
        ("钤辖教坊", "内侍差遣", 2), ("手分", "书吏", 2), ("贴司", "书吏", 2),
    ):
        _, post = state(
            w, i, title, "官职", "北宋天圣间", f"钤辖教坊所置{title}", clerk_quote,
            "钤辖教坊所官属", f"据教坊编制建立{title}。", "编制", officer=officer,
        )
        staff(w, i, control, post, clerk_quote, f"钤辖教坊所置{title}{quota}人。", "编制",
              quota=quota, staff_type=officer)

    touched = {eid, entity_id(w, "宣徽院", "机构"), entity_id(w, "太常寺", "机构")}
    touched.update(entity_id(w, title, "官职") for title, _, _ in officials)
    touched.update(entity_id(w, title, "机构") for title in colors)
    touched.update(entity_id(w, title, "官职") for title in ("钤辖教坊", "手分", "贴司"))
    touched.add(entity_id(w, "钤辖教坊所", "机构"))
    for touched_eid in touched:
        rechain(w, touched_eid, "插入教坊编制节点并按历史顺序重链。")
    assert tang and south_end and south_abolish and xiaozong
    w.commit()


def entry71():
    i = 71
    main, history, duty, grade, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "别名"),
    )
    w = W(i)
    eid = entity_id(w, "教坊使", "官职")
    tang = state(
        w, i, "教坊使", "官职", "唐开元二年", "以内臣为教坊使", history,
        "前代伶官", "建立教坊使唐开元二年职源节点。", "职源与沿革", officer="伶官",
    )[1]
    song = timepoint_id(w, "教坊使", "官职", "宋代")
    cite(w, "Timepoints", song, i, history, "补证宋沿置教坊使。", "职源与沿革")
    cite(w, "Timepoints", song, i, duty, "记录教坊使领教坊并审阅考核职掌。", "职掌")
    cite(w, "Timepoints", song, i, grade, "记录教坊使伶官地位与外调限制。", "品位")
    cite(w, "Timepoints", song, i, roster, "补证教坊使一人。", "编制")
    cite(w, "Timepoints", song, i, main, "正文明确教坊使为伶官。")
    alias_note(w, i, song, "别名")
    rechain(w, eid, "整理教坊使唐与宋时间链。")
    assert tang and aliases
    w.commit()


def entry72():
    assert F[72]["text"] == ""
    assert F[72]["fields"].get("__status__") == "placeholder"
    # 核第五编 PDF p306，无独立“排优”词条；目录误列，保留占位且不伪造四表数据。


def simple_office(i, title, time, event, category, officer, *, quota=None):
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, title, "官职") if w.find_entity(title, "官职") else None
    if eid is None:
        eid, tp = state(
            w, i, title, "官职", time, event, main, category,
            f"建立{title}{time}节点。", officer=officer,
        )
    else:
        _, tp = state(
            w, i, title, "官职", time, event, main, category,
            f"据专条建立或复用{title}{time}节点。", officer=officer,
        )
    parent = timepoint_id(w, "教坊", "机构", time if w.find_timepoint(entity_id(w, "教坊", "机构"), time) else "宋代")
    staff(w, i, parent, tp, main, f"{title}隶教坊。", quota=quota, staff_type=officer)
    rechain(w, entity_id(w, title, "官职"), f"整理{title}时间链。")
    w.commit()


def entry73_80():
    simple_office(73, "教坊副使", "宋代", "二人，为教坊佐贰官", "教坊官属", "伶官", quota=2)
    simple_office(74, "教坊判官", "宋代", "参领教坊事", "教坊官属", "伶官")

    i = 75
    main = F[i]["text"]
    w = W(i)
    eid, tp = state(
        w, i, "高班都知", "官职", "北宋", "二人；总管诸部诸色教习、排演与演出",
        main, "教坊官属", "建立高班都知北宋编制职掌节点。", officer="伶官",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋前期"), tp, main,
          "北宋教坊置高班都知二人。", quota=2, staff_type="伶官")
    rechain(w, eid, "整理高班都知宋代与北宋节点。")
    w.commit()

    i = 76
    main = F[i]["text"]
    w = W(i)
    eid, tp = state(
        w, i, "都知", "官职", "宋初", "四人；资深者迁高班都知，职掌与之同",
        main, "教坊官属", "建立都知宋初编制职掌节点。", officer="伶官",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋初"), tp, main,
          "宋初教坊都知四人。", quota=4, staff_type="伶官")
    rechain(w, eid, "整理都知宋代与宋初节点。")
    w.commit()

    i = 77
    main = F[i]["text"]
    w = W(i)
    old_eid = entity_id(w, "都知", "官职")
    old_end = state(
        w, i, "都知", "官职", "南宋", "改称都管", main,
        "教坊官属", "建立都知南宋改名终点。", officer="伶官",
    )[1]
    new_eid, new = state(
        w, i, "都管", "官职", "南宋", "由都知改称；总领诸部诸色教习及演奏",
        main, "教坊官属", "建立都管南宋改称节点。", officer="伶官",
    )
    relationship(w, i, old_end, new, "前后演变", main, "南宋都知改称都管。")
    staff(w, i, timepoint_id(w, "教坊", "机构", "南宋绍兴十四年二月十日"),
          new, main, "南宋教坊置都管。", staff_type="伶官")
    rechain(w, old_eid, "整理都知南宋改名链。")
    rechain(w, new_eid, "确认都管南宋节点。")
    w.commit()

    i = 78
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid, tp = state(
        w, i, "掌仪范", "官职", "宋代", "掌教习伶人演奏礼仪规范，位都知或都管之下",
        main, "教坊官属", "建立掌仪范宋代职掌节点。", officer="伶官",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋代"), tp, main,
          "掌仪范隶教坊。", staff_type="伶官")
    alias_note(w, i, tp, "简称")
    rechain(w, eid, "确认掌仪范宋代节点。")
    assert aliases
    w.commit()

    i = 79
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid, tp = state(
        w, i, "管干教头", "官职", "宋代", "掌教习并兼演出", main,
        "教坊官属", "建立管干教头宋代职掌节点。", officer="伶官",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋代"), tp, main,
          "管干教头隶教坊。", staff_type="伶官")
    alias_note(w, i, tp, "简称")
    rechain(w, eid, "确认管干教头宋代节点。")
    assert aliases
    w.commit()

    i = 80
    main = F[i]["text"]
    w = W(i)
    eid, tp = state(
        w, i, "都部头", "官职", "北宋", "二人；领部演奏，由部头升迁",
        main, "教坊官属", "建立都部头北宋编制职掌节点。", officer="乐工",
    )
    staff(w, i, timepoint_id(w, "教坊", "机构", "宋前期"), tp, main,
          "北宋教坊都部头二人。", quota=2, staff_type="乐工")
    rechain(w, eid, "整理都部头宋代与北宋节点。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(61, 81)] == [
        "郊社斋郎", "斋郎", "掌坐", "挽郎", "礼官", "籍田司", "籍田司令",
        "甲头", "耕籍使", "教坊", "教坊使", "排优", "教坊副使", "教坊判官",
        "高班都知", "都知", "都管", "掌仪范", "管干教头", "都部头",
    ]
    entry61()
    entry62()
    entry63()
    entry64()
    entry65()
    entry66()
    entry67()
    entry68()
    entry69()
    entry70()
    entry71()
    entry72()
    entry73_80()


if __name__ == "__main__":
    main()
