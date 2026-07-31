#!/usr/bin/env python3
"""提取 chapter5t7 第421-440条：骐骥院坊监、牧马兵、鞍辔库与驼坊。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_401_420 as previous


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


F = {i: load(i) for i in range(421, 441)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
state = base.state
relation = base.relation
staff = base.staff
tp = base.tp
alias_note = base.alias_note


TIME_HINTS = {
    "唐代": 618, "宋初": 960.1, "北宋太祖朝": 960.2,
    "北宋建隆二年": 961, "北宋开宝二年": 969,
    "北宋太平兴国二年": 977, "北宋太平兴国四年五月": 979.35,
    "北宋太平兴国五年正月七日": 980.02,
    "北宋太平兴国八年": 983,
    "北宋雍熙二年十月十六日": 985.79,
    "北宋咸平元年": 998, "北宋景德二年二月": 1005.12,
    "北宋景德五年": 1008,
    "北宋大中祥符四年正月": 1011.04,
    "北宋大中祥符四年十一月": 1011.88,
    "北宋天禧三年四月": 1019.29,
    "北宋熙宁三年三月六日以前": 1070.17,
    "北宋熙宁三年三月六日": 1070.18,
    "北宋熙宁八年二月十一日": 1075.12,
    "北宋元丰改制后": 1082.4,
    "北宋元祐元年五月十七日": 1086.38,
    "南宋": 1127, "南宋建炎三年四月十三日": 1129.29,
    "南宋绍兴八年十月十日": 1138.78,
    "南宋绍兴十三年十二月十九日": 1143.96,
    "南宋绍兴二十八年八月二十一日": 1158.64,
    "南宋绍兴二十九年": 1159,
    "南宋淳熙十四年": 1187,
    "南宋绍熙二年六月": 1191.46,
    "宋代（骐骥院牧兵）": 960.31,
    "宋代（骐骥院诸坊监）": 960.32,
    "北宋（天厩坊存续）": 1000,
    "北宋（左、右骐骥八直，年月未载）": 1020,
    "北宋（改隶卫尉寺，年月未载）": 1083,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    m = re.search(r"(-?\d{3,4})", time or "")
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


def set_event(w, tid, event, decision):
    old = w.conn.execute("select event from Timepoints where id=?", (tid,)).fetchone()[0]
    if old != event:
        w.conn.execute("update Timepoints set event=? where id=?", (event, tid))
        w._br("Timepoints", tid, f"事件说明由‘{old}’规范为‘{event}’：{decision}")


def exact_state(w, i, title, type_, time, event, quotation, category, decision,
                field_name=None, *, officer=None, grade=None, note=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade, note=note,
    )
    set_event(w, tid, event, decision)
    return eid, tid


def move_timepoint(w, title, type_, old_time, new_time, decision):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    old = w.find_timepoint(eid, old_time)
    new = w.find_timepoint(eid, new_time)
    if old is not None and new is None:
        w.conn.execute("update Timepoints set time=? where id=?", (new_time, old))
        w._br("Timepoints", old, decision)
        return old
    assert old is None and new is not None, (title, old_time, new_time, old, new)
    return new


def mark_conflict(w, target_id, i, quotation, field_name, note):
    cid = cite(
        w, "Timepoints", target_id, i, quotation,
        "保留相互冲突的减额年月并标记。", field_name,
    )
    row = w.conn.execute(
        "select conflict_flag,note from Citations where id=?", (cid,)
    ).fetchone()
    if row[0] != 1 or row[1] != note:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?", (note, cid)
        )
        w._br("Citations", cid, f"标记减额年月冲突：{note}")
    return cid


def entry421():
    i, main, aliases = 421, F[421]["text"], field(421, "简称与别名")
    w = W(i)
    eid, post = exact_state(
        w, i, "勾当左、右骐骥院", "官职", "北宋雍熙二年十月十六日",
        "置骐骥院后不设院使，置勾当官，以武官使臣或内侍使臣充，总国马之政",
        main, "骐骥院监官", "建立勾当左、右骐骥院始置、任用与职掌。",
        officer="武官使臣或内侍使臣差遣",
    )
    staff(w, i, tp(w, "左、右骐骥院", "机构", "北宋雍熙二年十月十六日"),
          post, main, "左、右骐骥院置勾当官总国马之政。",
          staff_type="武官使臣或内侍使臣差遣")
    alias_note(w, i, post, aliases, "简称与别名")
    rechain(w, eid, "整理勾当左、右骐骥院时间链。")
    w.commit()


def entry422():
    i, main = 422, F[422]["text"]
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "养马务", "机构", "北宋太祖朝",
        "始置，隶左、右飞龙院；初有二务，后增为四务，分置外地",
        main, "牧马监当局", "建立养马务宋太祖朝始置与编制节点。",
    )
    relation(w, i, tp(w, "左、右飞龙院", "机构", "宋初"), start,
             "上下级机构", main, "宋太祖朝养马务隶左、右飞龙院。")
    touched.add(eid)
    zheng_eid, zheng = exact_state(
        w, i, "郑州养马务", "机构", "北宋太祖朝",
        "外地养马务之一，收养病马", main,
        "牧马监当局", "建立郑州养马务实例。",
    )
    relation(w, i, start, zheng, "统称与实例", main,
             "郑州养马务为养马务实例。")
    capital_eid, capital = exact_state(
        w, i, "在京养马务", "机构", "北宋景德二年二月",
        "郑州养马务移置京师开封，专医治病马", main,
        "牧马监当局", "建立在京养马务移置节点。",
    )
    relation(w, i, zheng, capital, "前后演变", main,
             "景德二年郑州养马务移置开封，称在京养马务。")
    relation(w, i, start, capital, "统称与实例", main,
             "在京养马务为养马务实例。")
    touched.update((zheng_eid, capital_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理养马务、郑州养马务与在京养马务时间链。")
    w.commit()


def entry423():
    i, main = 423, F[423]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, prepared = exact_state(
        w, i, "左、右天驷监", "机构", "北宋太平兴国四年五月",
        "平北汉得战马四万二千余匹，于景阳门外置天驷四监牧厩，春夏入牧、秋冬入厩",
        duty, "牧马监", "建立天驷四监筹置与职能节点。", "职能",
    )
    _, four = exact_state(
        w, i, "左、右天驷监", "机构", "北宋太平兴国五年正月七日",
        "始置天驷四监，初隶左、右天厩院，位于牟驼岗",
        history, "牧马监", "补足天驷四监始置节点。", "职源与沿革",
    )
    touched.add(eid)
    old_members = []
    for title in (
        "天驷左第一监", "天驷左第二监", "天驷右第一监", "天驷右第二监",
    ):
        seid, member = exact_state(
            w, i, title, "机构", "北宋太平兴国五年正月七日",
            "天驷四监之一", roster, "牧马监",
            f"建立{title}为天驷四监实例。", "编制",
        )
        relation(w, i, four, member, "统称与实例", roster,
                 f"{title}为天驷四监实例。", "编制")
        old_members.append(member)
        touched.add(seid)
    _, merged = exact_state(
        w, i, "左、右天驷监", "机构", "北宋熙宁三年三月六日",
        "天驷四监合并为左、右天驷二监，改隶左、右骐骥院",
        history, "牧马监", "建立熙宁三年合并节点。", "职源与沿革",
    )
    relation(w, i, four, merged, "前后演变", history,
             "熙宁三年天驷四监合并为左、右天驷二监。", "职源与沿革")
    for title in ("左天驷监", "右天驷监"):
        seid, member = exact_state(
            w, i, title, "机构", "北宋熙宁三年三月六日",
            "天驷四监合并后所置左、右二监之一", roster,
            "牧马监", f"建立{title}实例。", "编制",
        )
        relation(w, i, merged, member, "统称与实例", roster,
                 f"{title}为合并后的左、右天驷监实例。", "编制")
        touched.add(seid)
    qiji_eid, qiji = exact_state(
        w, i, "左、右骐骥院", "机构", "北宋熙宁三年三月六日",
        "分领合并后的左、右天驷监", roster,
        "马政机构", "建立骐骥院分领天驷二监同期节点。", "编制",
    )
    relation(w, i, qiji, merged, "上下级机构", main,
             "熙宁三年后左、右天驷监隶左、右骐骥院。")
    alias_note(w, i, merged, aliases, "简称与别名")
    touched.add(qiji_eid)
    for entity_id in touched:
        rechain(w, entity_id, "整理天驷四监合并为左右二监的完整时间链。")
    w.commit()


def entry424():
    i, main, aliases = 424, F[424]["text"], field(424, "简称")
    w = W(i)
    eid = w.find_entity("天驷左第一监", "机构")
    assert eid
    node = tp(w, "天驷左第一监", "机构", "北宋太平兴国五年正月七日")
    cite(w, "Timepoints", node, i, main, "确认天驷左第一监为天驷四监之一。")
    alias_note(w, i, node, aliases, "简称")
    rechain(w, eid, "整理天驷左第一监时间链。")
    w.commit()


def entry425():
    i, main = 425, F[425]["text"]
    history, duty, aliases = (
        field(i, "职源与沿革"), field(i, "职能"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "左右天厩坊", "机构", "北宋雍熙二年十月十六日",
        "始置天厩坊，牧养国马", history,
        "牧马坊", "建立天厩坊始置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充牧养国马职能。", "职能")
    _, split = exact_state(
        w, i, "左右天厩坊", "机构", "北宋咸平元年",
        "分为左、右天厩二坊，隶左、右骐骥院", history,
        "牧马坊", "建立咸平元年分坊节点。", "职源与沿革",
    )
    for title in ("左天厩坊", "右天厩坊"):
        seid, member = exact_state(
            w, i, title, "机构", "北宋咸平元年",
            f"{title}为左右天厩坊之一，牧养国马", main,
            "牧马坊", f"建立{title}实例。",
        )
        relation(w, i, split, member, "统称与实例", main,
                 f"{title}为左右天厩坊实例。")
        touched.add(seid)
    relation(w, i, tp(w, "左、右骐骥院", "机构", "北宋咸平三年九月十一日"),
             split, "上下级机构", main, "左右天厩坊隶左、右骐骥院。")
    _, abolished = exact_state(
        w, i, "左右天厩坊", "机构", "北宋熙宁八年二月十一日",
        "罢左右天厩坊", history, "牧马坊",
        "建立熙宁八年罢坊节点。", "职源与沿革",
    )
    _, restored = exact_state(
        w, i, "左右天厩坊", "机构", "北宋元祐元年五月十七日",
        "复置，许民间承租牧地养马", history, "牧马坊",
        "建立元祐元年复置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", restored, i, duty, "补充民间承租牧地养马职能。", "职能")
    alias_note(w, i, restored, aliases, "简称")
    touched.add(eid)
    for entity_id in touched:
        rechain(w, entity_id, "整理左右天厩坊始置、分坊、罢复时间链。")
    w.commit()


def entry426():
    i, main = 426, F[426]["text"]
    w = W(i)
    touched = set()
    eid, six = exact_state(
        w, i, "左、右骐骥、六坊监", "机构", "北宋熙宁三年三月六日以前",
        "左、右骐骥两院、天驷四监、左、右天厩二坊合称",
        main, "马政机构统称", "建立左、右骐骥、六坊监体系。",
    )
    touched.add(eid)
    for title, time in (
        ("左骐骥院", "北宋雍熙二年十月十六日"),
        ("右骐骥院", "北宋雍熙二年十月十六日"),
        ("天驷左第一监", "北宋太平兴国五年正月七日"),
        ("天驷左第二监", "北宋太平兴国五年正月七日"),
        ("天驷右第一监", "北宋太平兴国五年正月七日"),
        ("天驷右第二监", "北宋太平兴国五年正月七日"),
        ("左天厩坊", "北宋咸平元年"),
        ("右天厩坊", "北宋咸平元年"),
    ):
        relation(w, i, six, tp(w, title, "机构", time), "统称与实例", main,
                 f"{title}为左、右骐骥、六坊监实例。")
    _, seen = exact_state(
        w, i, "左、右骐骥、六坊监", "机构", "北宋景德五年",
        "见饲马一万七千匹", main,
        "马政机构统称", "建立景德五年见饲马数节点。",
    )
    four_eid, four = exact_state(
        w, i, "左、右骐骥、四坊监", "机构", "北宋熙宁三年三月六日",
        "天驷四监合并为左、右二监后，六坊监改称四坊监",
        main, "马政机构统称", "建立左、右骐骥、四坊监体系。",
    )
    relation(w, i, six, four, "前后演变", main,
             "熙宁三年天驷四监并为二监，六坊监改称四坊监。")
    for title, time in (
        ("左骐骥院", "北宋雍熙二年十月十六日"),
        ("右骐骥院", "北宋雍熙二年十月十六日"),
        ("左天驷监", "北宋熙宁三年三月六日"),
        ("右天驷监", "北宋熙宁三年三月六日"),
        ("左天厩坊", "北宋咸平元年"),
        ("右天厩坊", "北宋咸平元年"),
    ):
        relation(w, i, four, tp(w, title, "机构", time), "统称与实例", main,
                 f"{title}为左、右骐骥、四坊监实例。")
    touched.add(four_eid)
    for entity_id in touched:
        rechain(w, entity_id, "整理六坊监改称四坊监时间链。")
    w.commit()


def entry427():
    i, main = 427, F[427]["text"]
    history, duty, aliases = (
        field(i, "职源与沿革"), field(i, "职能"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    tang_eid, tang = exact_state(
        w, i, "上、下牧监", "机构", "唐代",
        "唐太仆寺所辖上、下牧监", history,
        "牧马监", "建立唐代上、下牧监职源。", "职源与沿革",
    )
    tang_office_eid, tang_office = exact_state(
        w, i, "太仆寺", "机构", "唐代",
        "下辖上、下牧监", history,
        "马政寺监", "建立唐代太仆寺同期节点。", "职源与沿革",
    )
    relation(w, i, tang_office, tang, "上下级机构", history,
             "唐太仆寺下有上、下牧监。", "职源与沿革")
    eid, start = exact_state(
        w, i, "牧养上、下监", "机构", "北宋大中祥符四年十一月",
        "始置，初隶群牧司，收养治疗病马并申报驹数",
        history, "牧马监", "建立北宋牧养上、下监始置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充病马分送与驹数申报职能。", "职能")
    relation(w, i, tp(w, "群牧司", "机构", "北宋咸平三年九月十六日"),
             start, "上下级机构", main, "牧养上、下监初隶群牧司。")
    _, transferred = exact_state(
        w, i, "牧养上、下监", "机构", "北宋（改隶卫尉寺，年月未载）",
        "后改隶卫尉寺", main, "牧马监",
        "建立改隶卫尉寺节点。",
    )
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"),
             transferred, "上下级机构", main, "牧养上、下监后隶卫尉寺。")
    for title, event in (
        ("牧养上监", "收治病轻马"), ("牧养下监", "收治病重马"),
    ):
        seid, member = exact_state(
            w, i, title, "机构", "北宋大中祥符四年十一月",
            event, duty, "牧马监", f"建立{title}实例。", "职能",
        )
        relation(w, i, start, member, "统称与实例", duty,
                 f"{title}为牧养上、下监实例。", "职能")
        touched.add(seid)
    alias_note(w, i, start, aliases, "简称")
    touched.update((tang_eid, tang_office_eid, eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理唐上、下牧监与宋牧养上、下监时间链。")
    w.commit()


def entry428():
    i, main = 428, F[428]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    old_eid, old = exact_state(
        w, i, "左、右备征", "机构", "宋初",
        "左、右教骏营旧称", history,
        "牧马禁军", "建立宋初左、右备征节点。", "职源与沿革",
    )
    eid, renamed = exact_state(
        w, i, "左、右教骏营", "机构", "北宋建隆二年",
        "左、右备征改名左、右教骏，牧养、看守国马",
        history, "牧马禁军", "建立建隆二年改名节点。", "职源与沿革",
    )
    cite(w, "Timepoints", renamed, i, duty, "补充牧养、看守国马职能。", "职能")
    relation(w, i, old, renamed, "前后演变", history,
             "建隆二年左、右备征改名左、右教骏。", "职源与沿革")
    _, qiji_period = exact_state(
        w, i, "左、右教骏营", "机构", "北宋雍熙二年十月十六日",
        "隶左、右骐骥院，共四指挥", main,
        "牧马禁军", "建立骐骥院所隶教骏营节点。",
    )
    relation(w, i, tp(w, "左、右骐骥院", "机构", "北宋雍熙二年十月十六日"),
             qiji_period, "上下级机构", main, "左、右教骏营隶左、右骐骥院。")
    command_eid, commands = exact_state(
        w, i, "左、右教骏四指挥", "机构", "北宋",
        "左、右教骏营所辖四个指挥", roster,
        "牧马禁军指挥统称", "建立左、右教骏四指挥。", "编制",
    )
    relation(w, i, tp(w, "左、右教骏营", "机构", "北宋"), commands,
             "上下级机构", roster, "左、右教骏营共有四指挥。", "编制")
    move_timepoint(
        w, "左、右教骏营", "机构", "南宋绍兴间",
        "南宋绍兴二十八年八月二十一日",
        "据本条精确年月，将上一条概称绍兴间四百人的节点规范为绍兴二十八年八月二十一日。",
    )
    move_timepoint(
        w, "教骏军士", "官职", "南宋绍兴间",
        "南宋绍兴二十八年八月二十一日",
        "据本条精确年月，将上一条概称绍兴间四百人的节点规范为绍兴二十八年八月二十一日。",
    )
    _, north = exact_state(
        w, i, "左、右教骏营", "机构", "北宋",
        "四指挥，共二千九百四十人", roster,
        "牧马禁军", "补足北宋教骏营定额。", "编制",
    )
    _, north_soldiers = exact_state(
        w, i, "教骏军士", "官职", "北宋",
        "左、右教骏四指挥牧马兵，共二千九百四十人", roster,
        "骐骥院牧马兵", "补足北宋教骏军士定额。", "编制", officer="军士",
    )
    staff(w, i, north, north_soldiers, roster, "北宋教骏军士共二千九百四十人。",
          "编制", quota=2940, staff_type="军士")
    _, eight = exact_state(
        w, i, "左、右教骏营", "机构", "南宋绍兴八年十月十日",
        "定每指挥五十人，四指挥共二百人", roster,
        "牧马禁军", "建立绍兴八年教骏营定额。", "编制",
    )
    soldiers_eid, eight_soldiers = exact_state(
        w, i, "教骏军士", "官职", "南宋绍兴八年十月十日",
        "四指挥共二百人，每指挥五十人", roster,
        "骐骥院牧马兵", "建立绍兴八年教骏军士定额。", "编制", officer="军士",
    )
    staff(w, i, eight, eight_soldiers, roster, "绍兴八年教骏军士共二百人。",
          "编制", quota=200, staff_type="军士")
    _, twenty_eight = exact_state(
        w, i, "左、右教骏营", "机构", "南宋绍兴二十八年八月二十一日",
        "定每指挥一百人，四指挥共四百人", roster,
        "牧马禁军", "补足绍兴二十八年教骏营定额。", "编制",
    )
    _, twenty_eight_soldiers = exact_state(
        w, i, "教骏军士", "官职", "南宋绍兴二十八年八月二十一日",
        "四指挥共四百人，每指挥一百人", roster,
        "骐骥院牧马兵", "补足绍兴二十八年教骏军士定额。", "编制", officer="军士",
    )
    staff(w, i, twenty_eight, twenty_eight_soldiers, roster,
          "绍兴二十八年教骏军士共四百人。", "编制",
          quota=400, staff_type="军士")
    alias_note(w, i, twenty_eight, aliases, "简称")
    touched.update((old_eid, eid, command_eid, soldiers_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理左、右备征、教骏营、四指挥与军士定额时间链。")
    w.commit()


def entry429():
    i, main = 429, F[429]["text"]
    w = W(i)
    eid, soldiers = exact_state(
        w, i, "教骏军士", "官职", "宋代（骐骥院牧兵）",
        "隶左、右教骏营，承担牧马事务", main,
        "骐骥院牧马兵", "建立教骏军士隶属与职掌。", officer="军士",
    )
    staff(w, i, tp(w, "左、右教骏营", "机构", "北宋"), soldiers,
          main, "教骏军士隶左、右教骏营。", staff_type="军士")
    rechain(w, eid, "整理教骏军士定额与职掌时间链。")
    w.commit()


def entry430():
    i, main = 430, F[430]["text"]
    w = W(i)
    touched = set()
    eid, post = exact_state(
        w, i, "教骏军使", "官职", "宋代（骐骥院牧兵）",
        "隶左、右教骏营，位于教骏指挥使下、十将之上",
        main, "教骏营将校", "建立教骏军使隶属与序位。", officer="军使",
    )
    staff(w, i, tp(w, "左、右教骏营", "机构", "北宋"), post,
          main, "左、右教骏营设置教骏军使。", staff_type="军使")
    generic_eid, generic = exact_state(
        w, i, "教骏员僚", "官职", "宋代（骐骥院牧兵）",
        "骑兵指挥所置军使、副兵马使合称", main,
        "教骏营将校统称", "建立教骏员僚统称。", officer="员僚统称",
    )
    for title, officer in (("教骏军使", "军使"), ("教骏副兵马使", "副兵马使")):
        if title == "教骏军使":
            member = post
            seid = eid
        else:
            seid, member = exact_state(
                w, i, title, "官职", "宋代（骐骥院牧兵）",
                "左、右教骏营骑兵指挥员僚之一", main,
                "教骏营将校", f"建立{title}。", officer=officer,
            )
            staff(w, i, tp(w, "左、右教骏营", "机构", "北宋"), member,
                  main, f"左、右教骏营设置{title}。", staff_type=officer)
        relation(w, i, generic, member, "统称与实例", main,
                 f"{title}为教骏员僚实例。")
        touched.add(seid)
    touched.update((eid, generic_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理教骏军使、副兵马使与员僚时间链。")
    w.commit()


def entry431():
    i, main = 431, F[431]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "骑御马左、右直", "机构", "北宋太平兴国二年",
        "始置骑御马直", history,
        "骐骥院牧马禁军", "建立骑御马直属置节点。", "职源与沿革",
    )
    _, two = exact_state(
        w, i, "骑御马左、右直", "机构", "北宋太平兴国八年",
        "分为左、右二直", history,
        "骐骥院牧马禁军", "建立太平兴国八年分直节点。", "职源与沿革",
    )
    for title in ("骑御马左直", "骑御马右直"):
        seid, member = exact_state(
            w, i, title, "机构", "北宋太平兴国八年",
            f"{title}为骑御马左、右直之一", history,
            "骐骥院牧马禁军", f"建立{title}实例。", "职源与沿革",
        )
        relation(w, i, two, member, "统称与实例", history,
                 f"{title}为骑御马左、右直实例。", "职源与沿革")
        touched.add(seid)
    _, eight = exact_state(
        w, i, "骑御马左、右直", "机构", "北宋（左、右骐骥八直，年月未载）",
        "北宋曾增置八直", history,
        "骐骥院牧马禁军", "建立北宋八直节点。", "职源与沿革",
    )
    _, south = exact_state(
        w, i, "骑御马左、右直", "机构", "南宋",
        "减作左、右二直，应奉常朝御马及车驾行幸引驾、从马祗应",
        duty, "骐骥院牧马禁军", "建立南宋二直与职掌节点。", "职能",
    )
    cite(w, "Timepoints", south, i, roster, "补充南宋二直编制。", "编制")
    _, reduced = exact_state(
        w, i, "骑御马左、右直", "机构", "南宋绍熙二年六月",
        "由元额一百三十一人裁减为一百十一人", roster,
        "骐骥院牧马禁军", "建立绍熙二年减额节点。", "编制",
    )
    soldiers_eid, soldiers = exact_state(
        w, i, "骑御马直军士", "官职", "南宋绍熙二年六月",
        "由元额一百三十一人裁减为一百十一人", roster,
        "骐骥院牧马兵", "建立绍熙二年军士减额节点。", "编制", officer="军士",
    )
    staff(w, i, reduced, soldiers, roster, "绍熙二年骑御马直军士减为一百十一人。",
          "编制", quota=111, staff_type="军士")
    note = "#420记淳熙十四年减为111人，本条编制字段记绍熙二年六月，年月相冲突"
    mark_conflict(w, reduced, i, roster, "编制", note)
    mark_conflict(w, soldiers, i, roster, "编制", note)
    for old_node in (
        tp(w, "骑御马左、右直", "机构", "南宋淳熙十四年"),
        tp(w, "骑御马直军士", "官职", "南宋淳熙十四年"),
    ):
        old_citations = w.conn.execute(
            "select id from Citations where target_table='Timepoints' and target_id=? "
            "and citation like '%左、右骐骥院%';", (old_node,)
        ).fetchall()
        assert old_citations
        for (cid,) in old_citations:
            row = w.conn.execute(
                "select conflict_flag,note from Citations where id=?", (cid,)
            ).fetchone()
            if row[0] != 1 or row[1] != note:
                w.conn.execute(
                    "update Citations set conflict_flag=1,note=? where id=?", (note, cid)
                )
                w._br("Citations", cid, f"标记减额年月冲突：{note}")
    alias_note(w, i, reduced, aliases, "简称与别名")
    touched.update((eid, soldiers_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理骑御马左、右直始置、分直、职掌与减额时间链。")
    w.commit()


def entry432():
    i, main, aliases = 432, F[432]["text"], field(432, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "骑御马直小底", "官职", "宋代（骐骥院牧兵）",
        "隶骑御马左、右直，职掌调教上乘马", main,
        "骑御马直军吏", "建立骑御马直小底隶属与职掌。", officer="小底",
    )
    staff(w, i, tp(w, "骑御马左、右直", "机构", "北宋"), post,
          main, "骑御马左、右直设置小底。", staff_type="小底")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理骑御马直小底时间链。")
    w.commit()


def entry433():
    i, main, aliases = 433, F[433]["text"], field(433, "简称")
    w = W(i)
    touched = set()
    eid, commander = exact_state(
        w, i, "骑御马直指挥使", "官职", "宋代（骐骥院牧兵）",
        "骑御马左、右直指挥长官", main,
        "骑御马直将校", "建立骑御马直指挥使。", officer="指挥使",
    )
    unit = tp(w, "骑御马左、右直", "机构", "北宋")
    staff(w, i, unit, commander, main, "骑御马左、右直置指挥使。", staff_type="指挥使")
    generic_eid, generic = exact_state(
        w, i, "骑御马直属官", "官职", "宋代（骐骥院牧兵）",
        "骑御马直指挥使及其下副指挥使、军使、副兵马使、十将、节级、小底合称",
        main, "骑御马直将校统称", "建立骑御马直属官统称。", officer="将校统称",
    )
    relation(w, i, generic, commander, "统称与实例", main,
             "骑御马直指挥使为骑御马直属官实例。")
    touched.update((eid, generic_eid))
    for title, officer in (
        ("骑御马直副指挥使", "副指挥使"),
        ("骑御马直军使", "军使"),
        ("骑御马直副兵马使", "副兵马使"),
        ("骑御马直十将", "十将"),
        ("骑御马直节级", "节级"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（骐骥院牧兵）",
            f"骑御马直指挥使下所置{officer}", main,
            "骑御马直将校", f"建立{title}。", officer=officer,
        )
        staff(w, i, unit, post, main, f"骑御马左、右直设置{title}。", staff_type=officer)
        relation(w, i, generic, post, "统称与实例", main,
                 f"{title}为骑御马直属官实例。")
        touched.add(seid)
    relation(w, i, generic,
             tp(w, "骑御马直小底", "官职", "宋代（骐骥院牧兵）"),
             "统称与实例", main, "骑御马直小底为骑御马直属官实例。")
    alias_note(w, i, commander, aliases, "简称")
    for entity_id in touched:
        rechain(w, entity_id, "整理骑御马直指挥使及属官时间链。")
    w.commit()


def entry434():
    assert not F[434]["text"] and F[434]["fields"].get("__status__") == "placeholder"


def entry435():
    i, main, aliases = 435, F[435]["text"], field(435, "别名")
    w = W(i)
    eid, post = exact_state(
        w, i, "兽医", "官职", "宋代（骐骥院诸坊监）",
        "骐骥院及诸坊、监均置，职掌治疗病马，并有指挥建制",
        main, "牧马军吏", "建立兽医在骐骥院诸坊监的职掌与编制。", officer="兽医",
    )
    staff(w, i, tp(w, "左、右骐骥院", "机构", "北宋咸平三年九月十一日"),
          post, main, "左、右骐骥院设置兽医。", staff_type="兽医")
    command_eid, command = exact_state(
        w, i, "兽医指挥", "机构", "宋代（骐骥院诸坊监）",
        "兽医具有指挥建制", main,
        "牧马军编制", "建立兽医指挥建制。",
    )
    staff(w, i, command, post, main, "兽医有指挥建制。", staff_type="兽医")
    alias_note(w, i, post, aliases, "别名")
    for entity_id in (eid, command_eid):
        rechain(w, entity_id, "整理兽医及兽医指挥时间链。")
    w.commit()


def entry436():
    i, main = 436, F[436]["text"]
    w = W(i)
    touched = set()
    eid, post = exact_state(
        w, i, "长行", "官职", "宋代（骐骥院诸坊监）",
        "牧马院、务、坊、监均置，照管养马等给使，为牧马兵职资级之一",
        main, "牧马军吏", "建立长行在牧马机构的职掌与资级。", officer="长行",
    )
    parent_specs = (
        ("左、右骐骥院", "北宋咸平三年九月十一日"),
        ("养马务", "北宋太祖朝"),
        ("左右天厩坊", "北宋咸平元年"),
        ("左、右天驷监", "北宋太平兴国五年正月七日"),
        ("牧养上、下监", "北宋大中祥符四年十一月"),
    )
    for title, time in parent_specs:
        staff(w, i, tp(w, title, "机构", time), post, main,
              f"{title}设置长行。", staff_type="长行")
    brush_eid, brush = exact_state(
        w, i, "刷刨", "官职", "宋代（骐骥院诸坊监）",
        "牧马兵职资级，由长行可迁补", main,
        "牧马军吏", "建立刷刨及其选补来源。", officer="刷刨",
    )
    relation(w, i, post, brush, "前后演变", main,
             "长行可迁补刷刨。")
    touched.update((eid, brush_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理长行与刷刨选补时间链。")
    w.commit()


def entry437():
    i, main, aliases = 437, F[437]["text"], field(437, "简称")
    w = W(i)
    touched = set()
    eid, generic = exact_state(
        w, i, "左右骐骥院将校兵级", "官职", "宋代（骐骥院牧兵）",
        "骐骥院所属教骏营等牧马将校、兵级总称",
        main, "骐骥院牧兵统称", "建立左右骐骥院将校兵级统称。", officer="将校兵级统称",
    )
    staff(w, i, tp(w, "左、右骐骥院", "机构", "北宋咸平三年九月十一日"),
          generic, main, "左右骐骥院设置各类将校兵级。", staff_type="将校兵级")
    touched.add(eid)
    for title, officer in (
        ("骐骥院提举官", "提举官"), ("骐骥院指挥使", "指挥使"),
        ("骐骥院副指挥使", "副指挥使"), ("骐骥院员僚", "员僚"),
        ("骐骥院军使", "军使"), ("骐骥院副兵马使", "副兵马使"),
        ("骐骥院都头", "都头"), ("骐骥院副都头", "副都头"),
        ("骐骥院十将", "十将"), ("骐骥院节级", "节级"),
        ("兽医", "兽医"), ("骐骥院槽头", "槽头"),
        ("长行", "长行"), ("骐骥院小库", "小库"),
        ("骐骥院军兵", "军兵"),
    ):
        if title == "兽医":
            member = tp(w, title, "官职", "宋代（骐骥院诸坊监）")
            seid = w.find_entity(title, "官职")
        elif title == "长行":
            member = tp(w, title, "官职", "宋代（骐骥院诸坊监）")
            seid = w.find_entity(title, "官职")
        else:
            seid, member = exact_state(
                w, i, title, "官职", "宋代（骐骥院牧兵）",
                f"左右骐骥院将校兵级所含{officer}", main,
                "骐骥院牧兵", f"建立{title}实例。", officer=officer,
            )
        relation(w, i, generic, member, "统称与实例", main,
                 f"{title}为左右骐骥院将校兵级实例。")
        touched.add(seid)
    alias_note(w, i, generic, aliases, "简称")
    for entity_id in touched:
        rechain(w, entity_id, "整理左右骐骥院将校兵级及实例时间链。")
    w.commit()


def entry438():
    i, main = 438, F[438]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别称"),
    )
    w = W(i)
    touched = set()
    source_eid, source = exact_state(
        w, i, "架阁御鞍库房", "机构", "北宋大中祥符四年正月",
        "始置，为鞍辔库设置之始", history,
        "御马鞍辔库职源", "建立架阁御鞍库房职源。", "职源与沿革",
    )
    eid, named = exact_state(
        w, i, "鞍辔库", "机构", "北宋天禧三年四月",
        "已见鞍辔库正称，掌御马金玉鞍勒及给赐鞍辔名物",
        history, "御马鞍辔库", "建立鞍辔库正称节点。", "职源与沿革",
    )
    cite(w, "Timepoints", named, i, duty, "补充鞍辔库职掌。", "职掌")
    relation(w, i, source, named, "前后演变", history,
             "架阁御鞍库房为鞍辔库设置之始。", "职源与沿革")
    _, early = exact_state(
        w, i, "鞍辔库", "机构", "宋前期",
        "隶群牧司", main, "御马鞍辔库", "建立宋前期隶群牧司节点。",
    )
    relation(w, i, tp(w, "群牧司", "机构", "北宋咸平三年九月十六日"),
             early, "上下级机构", main, "宋前期鞍辔库隶群牧司。")
    _, reform = exact_state(
        w, i, "鞍辔库", "机构", "北宋元丰改制后",
        "并入太仆寺", main, "御马鞍辔库", "补足元丰改隶太仆寺节点。",
    )
    relation(w, i, tp(w, "太仆寺", "机构", "北宋元丰五年五月一日"),
             reform, "上下级机构", main, "元丰改制鞍辔库并入太仆寺。")
    _, abolished = exact_state(
        w, i, "鞍辔库", "机构", "南宋建炎三年四月十三日",
        "减罢，并入右骐骥院", history,
        "御马鞍辔库", "建立建炎三年减罢节点。", "职源与沿革",
    )
    right_eid, right = exact_state(
        w, i, "右骐骥院", "机构", "南宋建炎三年四月十三日",
        "接收减罢的鞍辔库职事", history,
        "马政机构", "建立右骐骥院接收鞍辔库同期节点。", "职源与沿革",
    )
    relation(w, i, abolished, right,
             "前后演变", history, "建炎三年鞍辔库减罢并入右骐骥院。", "职源与沿革")
    inner_eid, restored = exact_state(
        w, i, "内鞍辔库", "机构", "南宋绍兴十三年十二月十九日",
        "复置鞍辔库并改称内鞍辔库", history,
        "御马鞍辔库", "建立内鞍辔库复置节点。", "职源与沿革",
    )
    relation(w, i, abolished, restored, "前后演变", history,
             "绍兴十三年复置并改称内鞍辔库。", "职源与沿革")
    touched.update((source_eid, eid, right_eid, inner_eid))
    for title, officer, quota in (
        ("鞍辔库监官", "监官", 2), ("鞍辔库匠人", "匠人", 47),
        ("鞍辔库勾押官", "勾押官", 1), ("鞍辔库典", "典", 5),
        ("鞍辔库掌库", "掌库", 14),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋前期",
            f"鞍辔库所置{officer}，编制{quota}人", roster,
            "鞍辔库属员", f"建立{title}定额。", "编制", officer=officer,
        )
        staff(w, i, early, post, roster, f"宋前期鞍辔库置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    for title, officer in (
        ("军典", "军典"), ("内鞍辔库库子", "库子"),
        ("内鞍辔库专知官", "专知官"),
    ):
        post_event = (
            "隶内鞍辔库，专掌抄转、书写簿历等文书"
            if title == "军典" else f"内鞍辔库所置{officer}"
        )
        seid, post = exact_state(
            w, i, title, "官职", "南宋绍兴十三年十二月十九日",
            post_event, roster,
            "内鞍辔库属员", f"建立内鞍辔库{officer}。", "编制", officer=officer,
        )
        staff(w, i, restored, post, roster, f"南宋内鞍辔库设置{officer}。", "编制",
              staff_type=officer)
        touched.add(seid)
    cite(w, "Timepoints", restored, i, aliases,
         "‘内鞍辔库’不是泛称，而是绍兴十三年复置后的正式改称。", "别称")
    for entity_id in touched:
        rechain(w, entity_id, "整理鞍辔库、内鞍辔库及属员时间链。")
    w.commit()


def entry439():
    i, main = 439, F[439]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "军典", "官职", "南宋绍兴十三年十二月十九日",
        "隶内鞍辔库，专掌抄转、书写簿历等文书",
        main, "内鞍辔库公吏", "补足军典隶属与职掌。", officer="公吏",
    )
    staff(w, i, tp(w, "内鞍辔库", "机构", "南宋绍兴十三年十二月十九日"),
          post, main, "内鞍辔库设置军典。", staff_type="公吏")
    rechain(w, eid, "整理军典在皮剥所与内鞍辔库的完整时间链。")
    w.commit()


def entry440():
    i, main = 440, F[440]["text"]
    history, duty, roster = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "驼坊", "机构", "北宋开宝二年",
        "始置，驯养骆驼并运送官物", history,
        "太仆寺属局", "建立驼坊始置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充驯养骆驼、运送官物职掌。", "职掌")
    _, reform = exact_state(
        w, i, "驼坊", "机构", "北宋元丰改制后",
        "隶太仆寺，监官二人，管养兵校六百八十二人",
        roster, "太仆寺属局", "补足北宋驼坊编制。", "编制",
    )
    relation(w, i, tp(w, "太仆寺", "机构", "北宋元丰五年五月一日"),
             reform, "上下级机构", main, "驼坊隶太仆寺。")
    _, south = exact_state(
        w, i, "驼坊", "机构", "南宋",
        "沿置，驯养骆驼、骡子并运送官物", history,
        "太仆寺属局", "建立南宋沿置节点。", "职源与沿革",
    )
    _, reduced = exact_state(
        w, i, "驼坊", "机构", "南宋建炎三年四月十三日",
        "官吏减半", roster,
        "太仆寺属局", "建立建炎三年减员节点。", "编制",
    )
    _, fixed = exact_state(
        w, i, "驼坊", "机构", "南宋绍兴二十九年",
        "立定南宋官吏、军校与兵级编制，辖养象所",
        roster, "太仆寺属局", "建立绍兴二十九年定额节点。", "编制",
    )
    touched.add(eid)
    for title, officer, quota in (
        ("驼坊监官", "监官", 2), ("驼坊兵校", "兵校", 682),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "北宋元丰改制后",
            f"北宋驼坊所置{officer}，编制{quota}人", roster,
            "驼坊属员", f"建立北宋{title}定额。", "编制", officer=officer,
        )
        staff(w, i, reform, post, roster, f"北宋驼坊置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    range_eid, range_office = exact_state(
        w, i, "石州界都大提举管司", "机构", "北宋",
        "隶驼坊，负责放牧骆驼", roster,
        "驼坊属局", "建立石州界都大提举管司。", "编制",
    )
    relation(w, i, reform, range_office, "上下级机构", roster,
             "北宋驼坊下辖石州界都大提举管司。", "编制")
    touched.add(range_eid)
    generic_eid, generic = exact_state(
        w, i, "驼坊军校", "官职", "南宋绍兴二十九年",
        "军校共一百零三人，由副尉阶将校二人与兵级一百零一人组成",
        roster, "驼坊军校统称", "建立南宋驼坊军校总额。", "编制", officer="军校统称",
    )
    staff(w, i, fixed, generic, roster, "绍兴二十九年驼坊军校一百零三人。", "编制",
          quota=103, staff_type="军校")
    touched.add(generic_eid)
    for title, officer, quota in (
        ("驼坊监官", "监官", 2), ("驼坊人吏", "人吏", 1),
        ("驼坊兽医", "兽医", 1), ("驼坊副尉阶将校", "副尉阶将校", 2),
        ("驼坊兵级", "兵级", 101), ("驼坊曹司", "曹司", 1),
        ("驼坊节级", "节级", 2), ("驼坊把门", "把门", 4),
        ("驼坊打火", "打火", 4), ("驼坊养象", "养象", 90),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "南宋绍兴二十九年",
            f"南宋驼坊所置{officer}，编制{quota}人", roster,
            "驼坊属员", f"建立绍兴二十九年{title}定额。", "编制", officer=officer,
        )
        staff(w, i, fixed, post, roster, f"绍兴二十九年驼坊置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        if title in ("驼坊副尉阶将校", "驼坊兵级"):
            relation(w, i, generic, post, "统称与实例", roster,
                     f"{title}为驼坊军校组成部分。", "编制")
        touched.add(seid)
    elephant_eid, elephant = exact_state(
        w, i, "养象所", "机构", "南宋绍兴二十九年",
        "隶驼坊", roster, "驼坊属局",
        "建立南宋驼坊所辖养象所。", "编制",
    )
    relation(w, i, fixed, elephant, "上下级机构", roster,
             "南宋驼坊下辖养象所。", "编制")
    touched.add(elephant_eid)
    for entity_id in touched:
        rechain(w, entity_id, "整理驼坊、属局及北宋南宋属员定额时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(421, 441)] == [
        "勾当左、右骐骥院", "养马务", "左、右天驷监", "天驷左第一监",
        "左右天厩坊", "左、右骐骥、六坊监", "牧养上、下监",
        "左、右教骏营", "教骏军士", "教骏军使", "骑御马左、右直",
        "骑御马直小底", "骑御马直指挥使", "骑马直指挥使", "兽医",
        "长行", "左右骐骥院将校兵级", "鞍辔库", "军典", "驼坊",
    ]
    for i in range(421, 441):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
