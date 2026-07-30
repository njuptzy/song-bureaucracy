#!/usr/bin/env python3
"""提取 chapter5t7 第41-60条：太乐、鼓吹、宫闱及太庙斋郎室长系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_021_040 as previous


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


F = {i: load(i) for i in range(41, 61)}


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
    "秦汉": -150, "汉朝": -100, "两晋": 280, "北齐": 550,
    "隋大业三年": 607, "唐": 700, "北宋初": 960, "宋初": 960,
    "北宋乾德四年六月": 966, "北宋咸平元年五月五日": 998,
    "北宋景德二年": 1005, "北宋景德三年八月": 1006,
    "北宋大中祥符六年四月": 1013, "北宋真宗朝": 1010,
    "北宋仁宗朝": 1030, "北宋皇祐二年": 1050,
    "北宋皇祐二年闰十一月": 1050.9, "北宋皇祐五年五月": 1053,
    "北宋英宗朝": 1064, "北宋英宗朝以后": 1065,
    "北宋元丰改制后": 1080,
    "北宋崇宁四年八月": 1105, "北宋崇宁四年八月二十六日后": 1105.8,
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


def parent_state(w, i, title, time, event, quotation, category):
    return state(
        w, i, title, "机构", time, event, quotation, category,
        f"据{F[i]['title']}条建立{title}{time}制度状态。",
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
        f"{F[i]['title']}的纯简称、别称只作名称证据，不另建实体。",
        field_name, note="纯简称、别称不另建实体",
    )


def entry41():
    i = 41
    main, history, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别称"),
    )
    w = W(i)
    old_eid, qi = state(
        w, i, "太乐署", "机构", "北齐", "置太常寺太乐署", history,
        "太常寺所属音乐机构", "建立太乐署北齐职源节点。", "职源与沿革",
    )
    _, song = state(
        w, i, "太乐署", "机构", "北宋初", "太常寺附设太乐署", history,
        "太常寺所属音乐机构", "建立太乐署北宋沿置节点。", "职源与沿革",
    )
    _, jingde = state(
        w, i, "太乐署", "机构", "北宋景德二年", "淘汰冗滥乐工五十人", roster,
        "太常寺所属音乐机构", "提取景德二年淘汰乐工的制度变化。", "编制",
    )
    _, old_end = state(
        w, i, "太乐署", "机构", "北宋英宗朝", "避讳改称太乐局", history,
        "太常寺所属音乐机构", "建立太乐署改名终点。", "职源与沿革",
    )
    new_eid, new = state(
        w, i, "太乐局", "机构", "北宋英宗朝", "由太乐署避讳改称", history,
        "太常寺所属音乐机构", "建立太乐局英宗改名节点。", "职源与沿革",
    )
    _, dacheng = state(
        w, i, "太乐局", "机构", "北宋崇宁四年八月二十六日后",
        "并归大晟府", history, "大晟府所属音乐机构",
        "建立太乐局并归大晟府节点。", "职源与沿革",
    )
    cite(w, "Timepoints", new, i, duty, "记录太乐局职掌。", "职掌")
    cite(w, "Timepoints", new, i, main, "正文明确太乐局隶太常寺。")
    alias_note(w, i, new, "别称")
    relationship(w, i, old_end, new, "前后演变", history,
                 "英宗朝太乐署避讳改称太乐局。", "职源与沿革")

    temple_song = parent_state(w, i, "太常寺", "北宋初", "附设太乐署", history,
                               "中央礼乐机构")[1]
    temple_new = parent_state(w, i, "太常寺", "北宋英宗朝", "太乐署改称太乐局",
                              history, "中央礼乐机构")[1]
    dacheng_parent = timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月")
    relationship(w, i, temple_song, song, "上下级机构", main,
                 "北宋初太乐署隶太常寺。")
    relationship(w, i, temple_new, new, "上下级机构", main,
                 "英宗朝太乐局隶太常寺。")
    relationship(w, i, dacheng_parent, dacheng, "上下级机构", history,
                 "崇宁四年八月以后太乐局并归大晟府。", "职源与沿革")

    for title, officer, quota in (
        ("太乐局令", "长官", 1), ("太乐局丞", "佐贰官", 1),
        ("乐正", "乐工", 2), ("副乐正", "乐工", 2),
    ):
        _, tp = state(
            w, i, title, "官职", "北宋英宗朝以后", f"太乐局置{title}", roster,
            "太乐局官属", f"据太乐局编制建立{title}员额状态。", "编制",
            officer=officer,
        )
        staff(w, i, new, tp, roster, f"太乐局编制列{title}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        rechain(w, entity_id(w, title, "官职"), f"整理{title}时间链。")

    for eid in (old_eid, new_eid, entity_id(w, "太常寺", "机构")):
        rechain(w, eid, "插入太乐署、局相关节点并按历史顺序重链。")
    assert qi and jingde
    w.commit()


def entry42():
    i = 42
    main, aliases = F[i]["text"], field(i, "别称")
    w = W(i)
    old_eid = entity_id(w, "太乐署", "机构")
    song = w.find_timepoint(old_eid, "北宋初")
    end = w.find_timepoint(old_eid, "北宋英宗朝")
    cite(w, "Timepoints", song, i, main, "补证宋初沿称太乐署。")
    cite(w, "Timepoints", end, i, main, "补证英宗朝避讳改称太乐局。")
    _, qian = state(
        w, i, "太乐署", "机构", "北宋乾德四年六月", "旧制宫悬、登歌陈设见载",
        aliases, "太常寺所属音乐机构", "提取乾德四年太乐署制度实例。", "别称",
    )
    _, xiangfu = state(
        w, i, "太乐署", "机构", "北宋大中祥符六年四月",
        "受太宗乐曲、琴阮谱", aliases, "太常寺所属音乐机构",
        "提取大中祥符六年太乐署制度活动。", "别称",
    )
    jingde = w.find_timepoint(old_eid, "北宋景德二年")
    cite(w, "Timepoints", jingde, i, aliases, "补证景德二年太乐署淘汰滥吹者。", "别称")
    rechain(w, old_eid, "插入太乐署乾德、大中祥符节点。")
    assert qian and xiangfu
    w.commit()


def entry43():
    i = 43
    main, history, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    old_eid, qin = state(
        w, i, "太乐署令", "官职", "秦汉", "奉常（太常）属官太乐令", history,
        "前代乐官", "建立太乐署令秦汉职源节点。", "职源与沿革", officer="长官",
    )
    _, qi = state(
        w, i, "太乐署令", "官职", "北齐", "太常寺太乐署置令", history,
        "太乐署官属", "建立太乐署令北齐节点。", "职源与沿革", officer="长官",
    )
    _, song = state(
        w, i, "太乐署令", "官职", "北宋初", "沿置太乐署令", history,
        "太乐署官属", "建立太乐署令宋初沿置节点。", "职源与沿革", officer="长官",
    )
    new_eid = entity_id(w, "太乐局令", "官职")
    new = w.find_timepoint(new_eid, "北宋英宗朝以后")
    cite(w, "Timepoints", new, i, history, "补证后改称太乐局令。", "职源与沿革")
    cite(w, "Timepoints", new, i, duty, "补证太乐局令为本局长官。", "职掌")
    cite(w, "Timepoints", new, i, roster, "补证太乐局令一人。", "编制")
    cite(w, "Timepoints", new, i, main, "正文明确太乐局令隶太乐局。")
    alias_note(w, i, new, "简称")
    relationship(w, i, song, new, "前后演变", history,
                 "北宋初太乐署令后改称太乐局令。", "职源与沿革")
    _, late = state(
        w, i, "太乐令", "官职", "北宋崇宁四年八月", "太乐局并入大晟府后置太乐令",
        history, "大晟府乐官", "建立大晟府太乐令节点。", "职源与沿革", officer="长官",
    )
    relationship(w, i, new, late, "前后演变", history,
                 "崇宁四年太乐局令随并府改为大晟府太乐令。", "职源与沿革")
    old_office = timepoint_id(w, "太乐署", "机构", "北宋初")
    new_office = timepoint_id(w, "太乐局", "机构", "北宋英宗朝")
    dacheng = timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月")
    staff(w, i, old_office, song, history, "北宋初太乐署置令。", "职源与沿革",
          quota=1, staff_type="长官")
    staff(w, i, new_office, new, roster, "太乐局令编制一人。", "编制",
          quota=1, staff_type="长官")
    staff(w, i, dacheng, late, history, "太乐局并入大晟府后有太乐令。", "职源与沿革",
          staff_type="长官")
    for eid in (old_eid, new_eid, entity_id(w, "太乐令", "官职")):
        rechain(w, eid, "整理太乐令官名演变相关时间链。")
    assert qin and qi
    w.commit()


def entry44_45():
    i = 44
    main, history, duty, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    )
    w = W(i)
    old_eid, qin = state(
        w, i, "太乐署丞", "官职", "秦汉", "奉常（太常）属官太乐丞", history,
        "前代乐官", "建立太乐署丞秦汉职源节点。", "职源与沿革", officer="佐贰官",
    )
    _, qi = state(
        w, i, "太乐署丞", "官职", "北齐", "太常寺太乐署置丞", history,
        "太乐署官属", "建立太乐署丞北齐节点。", "职源与沿革", officer="佐贰官",
    )
    _, song = state(
        w, i, "太乐署丞", "官职", "北宋初", "沿置太乐署丞", history,
        "太乐署官属", "建立太乐署丞宋初节点。", "职源与沿革", officer="佐贰官",
    )
    new_eid = entity_id(w, "太乐局丞", "官职")
    new = w.find_timepoint(new_eid, "北宋英宗朝以后")
    for quote, field_name, decision in (
        (history, "职源与沿革", "补证后设太乐局丞。"),
        (duty, "职掌", "补证太乐局丞参领本局事。"),
        (roster, "编制", "补证太乐局丞一人。"),
        (main, None, "正文明确太乐局丞隶太乐局。"),
    ):
        cite(w, "Timepoints", new, i, quote, decision, field_name)
    relationship(w, i, song, new, "前后演变", history,
                 "北宋太乐署丞后改置太乐局丞。", "职源与沿革")
    staff(w, i, timepoint_id(w, "太乐署", "机构", "北宋初"), song, history,
          "北宋初太乐署置丞。", "职源与沿革", quota=1, staff_type="佐贰官")
    rechain(w, old_eid, "整理太乐署丞时间链。")
    rechain(w, new_eid, "整理太乐局丞时间链。")
    assert qin and qi
    w.commit()

    i = 45
    main = F[i]["text"]
    w = W(i)
    old_eid = entity_id(w, "太乐署丞", "官职")
    song = w.find_timepoint(old_eid, "北宋初")
    cite(w, "Timepoints", song, i, main, "补证太乐署丞宋初设置且即太乐局丞。")
    new = timepoint_id(w, "太乐局丞", "官职", "北宋英宗朝以后")
    cite(w, "Timepoints", new, i, main, "太乐署丞条明确其与太乐局丞为改名前后同职。")
    w.commit()


def entry46():
    i = 46
    main, history, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别称"),
    )
    w = W(i)
    eid = entity_id(w, "乐正", "官职")
    sui = state(
        w, i, "乐正", "官职", "隋大业三年", "太乐署乐师改为乐正", history,
        "前代乐官", "建立乐正隋代职源节点。", "职源与沿革", officer="乐工",
    )[1]
    north = w.find_timepoint(eid, "北宋英宗朝以后")
    cite(w, "Timepoints", north, i, history, "补证两宋沿置乐正。", "职源与沿革")
    cite(w, "Timepoints", north, i, duty, "记录乐正指挥、教乐、制舞仪职掌。", "职掌")
    cite(w, "Timepoints", north, i, roster, "补证乐正二人。", "编制")
    cite(w, "Timepoints", north, i, main, "正文明确北宋乐正隶太乐局。")
    south = state(
        w, i, "乐正", "官职", "南宋", "不置太乐局，乐正改隶太常寺", aliases,
        "太常寺乐官", "建立乐正南宋隶属状态。", "别称", officer="乐工",
    )[1]
    alias_note(w, i, south, "别称")
    temple = parent_state(w, i, "太常寺", "南宋", "不置太乐局而沿设乐正", aliases,
                          "中央礼乐机构")[1]
    staff(w, i, temple, south, aliases, "南宋不置太乐局，乐正隶太常寺。", "别称",
          quota=2, staff_type="乐工")
    rechain(w, eid, "整理乐正隋、北宋、南宋时间链。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入南宋乐正隶属节点。")
    assert sui
    w.commit()


def entry47():
    i = 47
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, "副乐正", "官职")
    state(
        w, i, "副乐正", "官职", "北宋景德三年八月", "见置；位次于乐正",
        main, "太常寺乐工", "建立副乐正景德三年见置节点。", officer="乐工",
    )[1]
    later = w.find_timepoint(eid, "北宋英宗朝以后")
    cite(w, "Timepoints", later, i, main, "副乐正条补证该职位次于乐正。")
    rechain(w, eid, "整理副乐正景德与英宗以后节点。")
    w.commit()


def entry48():
    i = 48
    main, history, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    old_eid, qi = state(
        w, i, "鼓吹署", "机构", "北齐", "置太常寺鼓吹署", history,
        "太常寺所属音乐机构", "建立鼓吹署北齐职源节点。", "职源与沿革",
    )
    _, song = state(
        w, i, "鼓吹署", "机构", "北宋初", "沿置太常寺鼓吹署", history,
        "太常寺所属音乐机构", "建立鼓吹署宋初沿置节点。", "职源与沿革",
    )
    _, old_end = state(
        w, i, "鼓吹署", "机构", "北宋英宗朝", "避讳改称鼓吹局", history,
        "太常寺所属音乐机构", "建立鼓吹署改名终点。", "职源与沿革",
    )
    new_eid, new = state(
        w, i, "鼓吹局", "机构", "北宋英宗朝", "由鼓吹署避讳改称", history,
        "太常寺所属音乐机构", "建立鼓吹局英宗改名节点。", "职源与沿革",
    )
    _, late = state(
        w, i, "鼓吹局", "机构", "北宋崇宁四年八月", "归隶大晟府", history,
        "大晟府所属音乐机构", "建立鼓吹局归大晟府节点。", "职源与沿革",
    )
    cite(w, "Timepoints", new, i, duty, "记录鼓吹局职掌鼓吹十二案。", "职掌")
    cite(w, "Timepoints", new, i, main, "正文明确鼓吹局隶太常寺。")
    alias_note(w, i, new, "简称")
    relationship(w, i, old_end, new, "前后演变", history,
                 "英宗朝鼓吹署避讳改称鼓吹局。", "职源与沿革")
    temple_song = parent_state(w, i, "太常寺", "北宋初", "沿置鼓吹署", history,
                               "中央礼乐机构")[1]
    temple_new = parent_state(w, i, "太常寺", "北宋英宗朝", "鼓吹署改称鼓吹局",
                              history, "中央礼乐机构")[1]
    relationship(w, i, temple_song, song, "上下级机构", main,
                 "北宋初鼓吹署隶太常寺。")
    relationship(w, i, temple_new, new, "上下级机构", main,
                 "英宗朝鼓吹局隶太常寺。")
    relationship(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月"),
                 late, "上下级机构", history, "崇宁四年鼓吹局归隶大晟府。",
                 "职源与沿革")
    for title, officer, quota in (("鼓吹局令", "长官", 1), ("鼓吹局丞", "佐贰官", 1)):
        _, tp = state(
            w, i, title, "官职", "北宋英宗朝以后", f"鼓吹局置{title}", roster,
            "鼓吹局官属", f"据鼓吹局编制建立{title}员额状态。", "编制",
            officer=officer,
        )
        staff(w, i, new, tp, roster, f"鼓吹局置{title}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        rechain(w, entity_id(w, title, "官职"), f"整理{title}时间链。")
    for eid in (old_eid, new_eid, entity_id(w, "太常寺", "机构")):
        rechain(w, eid, "插入鼓吹署、局相关节点并按历史顺序重链。")
    assert qi
    w.commit()


def entry49():
    i = 49
    main = F[i]["text"]
    w = W(i)
    cite(w, "Timepoints", timepoint_id(w, "鼓吹署", "机构", "北宋初"), i, main,
         "补证宋初沿唐五代旧名鼓吹署。")
    cite(w, "Timepoints", timepoint_id(w, "鼓吹署", "机构", "北宋英宗朝"), i, main,
         "补证英宗朝鼓吹署改称鼓吹局。")
    cite(w, "Timepoints", timepoint_id(w, "鼓吹局", "机构", "北宋英宗朝"), i, main,
         "补证鼓吹局为鼓吹署改名后机构。")
    w.commit()


def entry50():
    i = 50
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, "鼓吹局令", "官职")
    old = state(
        w, i, "鼓吹局令", "官职", "两晋", "太常卿属官有鼓吹令", main,
        "前代乐官", "建立鼓吹局令两晋职源节点。", officer="长官",
    )[1]
    song = w.find_timepoint(eid, "北宋英宗朝以后")
    cite(w, "Timepoints", song, i, main, "补证北宋鼓吹局令一人并领局事。")
    staff(w, i, timepoint_id(w, "鼓吹局", "机构", "北宋英宗朝"), song, main,
          "北宋鼓吹局令一人，领鼓吹局事。", quota=1, staff_type="长官")
    rechain(w, eid, "整理鼓吹局令两晋与北宋节点。")
    assert old
    w.commit()


def entry51():
    i = 51
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    old_eid, qi = state(
        w, i, "鼓吹署丞", "官职", "北齐", "太常寺鼓吹署置丞", main,
        "鼓吹署官属", "建立鼓吹署丞北齐职源节点。", officer="佐贰官",
    )
    _, song = state(
        w, i, "鼓吹署丞", "官职", "北宋初", "沿置鼓吹署丞", main,
        "鼓吹署官属", "建立鼓吹署丞宋初节点。", officer="佐贰官",
    )
    new_eid = entity_id(w, "鼓吹局丞", "官职")
    new = w.find_timepoint(new_eid, "北宋英宗朝以后")
    cite(w, "Timepoints", new, i, main, "补证英宗朝改鼓吹署为鼓吹局并置丞一人。")
    alias_note(w, i, new, "简称")
    relationship(w, i, song, new, "前后演变", main,
                 "宋初鼓吹署丞在英宗改局后称鼓吹局丞。")
    staff(w, i, timepoint_id(w, "鼓吹署", "机构", "北宋初"), song, main,
          "宋初鼓吹署沿置丞。", quota=1, staff_type="佐贰官")
    rechain(w, old_eid, "整理鼓吹署丞时间链。")
    rechain(w, new_eid, "整理鼓吹局丞时间链。")
    assert qi and aliases
    w.commit()


def entry52():
    i = 52
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid, start = state(
        w, i, "详定大乐所", "机构", "北宋皇祐二年闰十一月丁巳",
        "置；讨论、修订大乐制度",
        main, "临时音乐制度机构", "建立详定大乐所皇祐二年始置节点。",
    )
    later = state(
        w, i, "详定大乐所", "机构", "北宋皇祐五年五月", "继续参定大乐制度",
        aliases, "临时音乐制度机构", "从简称字段引文提取皇祐五年制度活动。", "简称",
    )[1]
    alias_note(w, i, later, "简称")
    rechain(w, eid, "连接详定大乐所皇祐二年与五年节点。")
    assert start
    w.commit()


def entry53():
    i = 53
    main, history, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    office_eid, sui = state(
        w, i, "宫闱局", "机构", "隋", "始置宫闱局，隶内侍省", history,
        "内侍机构", "建立宫闱局隋代职源节点。", "职源与沿革",
    )
    eid, early = state(
        w, i, "太庙宫闱令", "官职", "北宋初", "内侍省沿置但罕以除人", history,
        "太庙祠祭差遣", "建立太庙宫闱令宋初状态。", "职源与沿革", officer="差遣官",
    )
    _, start = state(
        w, i, "太庙宫闱令", "官职", "北宋咸平元年五月五日",
        "始置有职事太庙宫闱令", history, "太庙祠祭差遣",
        "建立有职事太庙宫闱令始置节点。", "职源与沿革", officer="差遣官",
    )
    _, south = state(
        w, i, "太庙宫闱令", "官职", "南宋", "沿置", history,
        "太庙祠祭差遣", "建立太庙宫闱令南宋沿置节点。", "职源与沿革", officer="差遣官",
    )
    cite(w, "Timepoints", start, i, duty, "记录太庙宫闱令职掌。", "职掌")
    cite(w, "Timepoints", start, i, roster, "记录常额一至二人及大礼权差员额。", "编制")
    cite(w, "Timepoints", start, i, main, "正文明确太庙宫闱令分隶太常寺与内侍省。")
    alias_note(w, i, start, "简称")
    temple = parent_state(w, i, "太常寺", "北宋咸平元年五月五日",
                          "始置有职事太庙宫闱令", history, "中央礼制机构")[1]
    inner_eid, inner = state(
        w, i, "内侍省", "机构", "北宋初", "沿置宫闱令", history,
        "宫廷内侍机构", "建立内侍省宋初宫闱令编制状态。", "职源与沿革",
    )
    _, inner_sui = state(
        w, i, "内侍省", "机构", "隋", "宫闱局所属机构", history,
        "宫廷内侍机构", "建立内侍省隋代宫闱局所属节点。", "职源与沿革",
    )
    relationship(w, i, inner_sui, sui, "上下级机构", history,
                 "隋朝宫闱局隶内侍省。", "职源与沿革")
    staff(w, i, temple, start, main, "有职事太庙宫闱令隶太常寺。",
          staff_type="差遣官")
    staff(w, i, inner, start, main, "太庙宫闱令同时由内侍省系统差充。",
          staff_type="差遣官")
    _, shaoxing = state(
        w, i, "太庙宫闱令", "官职", "南宋绍兴五年二月",
        "迎奉神主时临时权差二十二员", roster, "太庙祠祭差遣",
        "提取绍兴五年迎奉神主临时权差二十二员。", "编制", officer="差遣官",
    )
    temple_shaoxing = parent_state(
        w, i, "太常寺", "南宋绍兴五年二月", "权差太庙宫闱令迎奉神主",
        roster, "中央礼制机构",
    )[1]
    staff(w, i, temple_shaoxing, shaoxing, roster,
          "绍兴五年迎奉神主时权差二十二员宫闱令。", "编制",
          quota=22, staff_type="临时权差")
    rechain(w, eid, "整理太庙宫闱令北宋初、咸平及南宋节点。")
    rechain(w, office_eid, "整理宫闱局时间链。")
    rechain(w, inner_eid, "整理内侍省时间链。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入咸平宫闱令节点。")
    assert sui and early and south
    w.commit()


def entry54_56():
    for i, title, time in (
        (54, "太庙宫闱丞", "北宋真宗朝"),
        (55, "皇后庙宫闱令", "北宋真宗朝"),
        (56, "奉慈庙宫闱令", "北宋仁宗朝"),
    ):
        main = F[i]["text"]
        w = W(i)
        event = {
            54: "见置；由内侍充，为宫闱令佐贰",
            55: "始见置；由内侍充，掌皇后庙神主及庙内洁除",
            56: "见置；由内侍充，掌奉慈庙太后神主相关事务",
        }[i]
        eid, tp = state(
            w, i, title, "官职", time, event, main, "宫闱祠祭差遣",
            f"建立{title}{time}制度节点。", officer="差遣官",
        )
        if i == 55:
            alias_note(w, i, tp, "简称")
            aliases = field(i, "简称")
            state(
                w, i, title, "官职", "北宋景德三年十二月",
                "诏与太庙宫闱令同宿庙内", aliases, "宫闱祠祭差遣",
                "提取景德三年十二月皇后庙宫闱令宿庙制度。", "简称",
                officer="差遣官",
            )
        rechain(w, eid, f"整理{title}时间链。")
        w.commit()


def entry57():
    i = 57
    main = F[i]["text"]
    w = W(i)
    generic_eid = entity_id(w, "宫闱令", "官职")
    generic = state(
        w, i, "宫闱令", "官职", "北宋", "太庙、皇后庙、奉慈庙宫闱令通称",
        main, "宫闱祠祭差遣统称", "建立宫闱令作为三类差遣通称的节点。",
        officer="差遣官",
    )[1]
    for title, time in (
        ("太庙宫闱令", "北宋咸平元年五月五日"),
        ("皇后庙宫闱令", "北宋真宗朝"),
        ("奉慈庙宫闱令", "北宋仁宗朝"),
    ):
        instance = timepoint_id(w, title, "官职", time)
        relationship(w, i, generic, instance, "统称与实例", main,
                     f"宫闱令是{title}等三类差遣的通称。")
    rechain(w, generic_eid, "插入宫闱令通称节点。")
    w.commit()


def entry58():
    i = 58
    main, history, duty, order, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "序位"), field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, han = state(
        w, i, "太庙斋郎", "官职", "汉朝", "始有太庙斋郎", history,
        "前代祠祭官", "建立太庙斋郎汉代职源节点。", "职源与沿革", officer="非品官",
    )
    _, tang = state(
        w, i, "太庙斋郎", "官职", "唐", "始与郊社斋郎分置", history,
        "前代祠祭官", "建立太庙斋郎唐代分置节点。", "职源与沿革", officer="非品官",
    )
    _, song = state(
        w, i, "太庙斋郎", "官职", "北宋大中祥符七年八月庚辰",
        "见沿置；兼为祠祭行事官与荫补起家官",
        history, "太常寺非品祠祭官", "建立太庙斋郎北宋沿置节点。", "职源与沿革",
        officer="非品官",
    )
    _, quota = state(
        w, i, "太庙斋郎", "官职", "北宋建隆四年六月",
        "与郊社斋郎合计每岁荫补十五人为额", roster, "太常寺非品祠祭官",
        "提取建隆四年太庙、郊社斋郎合计员额。", "编制", officer="非品官",
        note="十五人为太庙斋郎、郊社斋郎合计，不单计为本职员额",
    )
    cite(w, "Timepoints", song, i, duty, "记录太庙斋郎祠祭与荫补双重职掌。", "职掌")
    cite(w, "Timepoints", song, i, order, "记录太庙斋郎在非品官中的序位。", "序位")
    cite(w, "Timepoints", song, i, main, "正文明确太庙斋郎非品官并隶太常寺。")
    alias_note(w, i, song, "简称与别名")
    temple = parent_state(w, i, "太常寺", "北宋大中祥符七年八月庚辰",
                          "沿置太庙斋郎", main,
                          "中央礼制机构")[1]
    staff(w, i, temple, song, main, "太庙斋郎隶太常寺。", staff_type="非品官")
    rechain(w, eid, "整理太庙斋郎汉、唐、北宋及建隆节点。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入北宋太庙斋郎节点。")
    assert han and tang and quota
    w.commit()


def entry59():
    i = 59
    main, history, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, tang = state(
        w, i, "太庙室长", "官职", "唐", "始置，十年可授品官", history,
        "前代祠祭官", "建立太庙室长唐代职源节点。", "职源与沿革", officer="非品官",
    )
    _, song = state(
        w, i, "太庙室长", "官职", "北宋大中祥符七年八月庚辰",
        "见沿置；为祠祭行事官及斋郎迁转阶",
        history, "太常寺非品祠祭官", "建立太庙室长北宋沿置节点。", "职源与沿革",
        officer="非品官",
    )
    cite(w, "Timepoints", song, i, duty, "记录太庙室长祠祭与荫补迁转职掌。", "职掌")
    cite(w, "Timepoints", song, i, roster,
         "记录每室可设或数室共设、事罢即已且迁补无定员。", "编制")
    cite(w, "Timepoints", song, i, main, "正文明确太庙室长为非品官并隶太常寺。")
    alias_note(w, i, song, "简称与别名")
    temple = timepoint_id(w, "太常寺", "机构", "北宋大中祥符七年八月庚辰")
    staff(w, i, temple, song, main, "太庙室长隶太常寺。", staff_type="非品官")
    rechain(w, eid, "整理太庙室长唐与北宋节点。")
    assert tang
    w.commit()


def entry60():
    i = 60
    main = F[i]["text"]
    w = W(i)
    generic = timepoint_id(w, "太庙室长", "官职", "北宋大中祥符七年八月庚辰")
    eid, fourth = state(
        w, i, "第四室长", "官职", "宋代", "太庙第四室所设室长；见实除荫补官",
        main, "太常寺非品祠祭官", "建立第四室长北宋实例节点。", officer="非品官",
    )
    relationship(w, i, generic, fourth, "统称与实例", main,
                 "太庙室长按庙室编号，第四室长是明确实例。")
    rechain(w, eid, "确认第四室长北宋节点。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(41, 61)] == [
        "太乐局", "太乐署", "太乐局令", "太乐局丞", "太乐署丞",
        "乐正", "副乐正", "鼓吹局", "鼓吹署", "鼓吹局令",
        "鼓吹局丞", "详定大乐所", "太庙宫闱令", "太庙宫闱丞",
        "皇后庙宫闱令", "奉慈庙宫闱令", "宫闱令", "太庙斋郎",
        "太庙室长", "第四室长",
    ]
    entry41()
    entry42()
    entry43()
    entry44_45()
    entry46()
    entry47()
    entry48()
    entry49()
    entry50()
    entry51()
    entry52()
    entry53()
    entry54_56()
    entry57()
    entry58()
    entry59()
    entry60()


if __name__ == "__main__":
    main()
