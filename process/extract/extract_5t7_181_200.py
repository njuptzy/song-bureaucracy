#!/usr/bin/env python3
"""提取 chapter5t7 第181-200条：陵台令、攒宫司与大宗正司长官。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_161_180 as previous


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


F = {i: load(i) for i in range(181, 201)}


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


def entity_id(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def upsert_state(w, i, title, type_, time, event, quotation, category, decision,
                 field_name=None, *, officer=None, grade=None, note=None):
    eid = w.entity(title, type_, decision, quotation=quotation)
    tid = w.find_timepoint(eid, time)
    if tid is None:
        tid = w.timepoint(
            eid, time, event, decision, quotation,
            attr_category=category, attr_officer_type=officer,
            attr_grade=grade, chain="none",
        )
    else:
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
                f"据第{i}条校订 {title} 的 {time} 节点：{decision}",
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


TIME_HINTS = {
    "西汉": -200, "东汉": 25, "北齐": 550, "唐贞观间": 635,
    "唐天宝十载": 751, "宋代": 960, "北宋": 960,
    "北宋太宗雍熙二年五月": 985.35,
    "北宋真宗景德四年正月": 1007.04,
    "北宋真宗景德四年七月六日": 1007.52,
    "北宋景祐三年七月十九日": 1036.55,
    "北宋庆历四年": 1044,
    "北宋治平元年六月十三日": 1064.45,
    "北宋英宗治平三年": 1066,
    "北宋元丰改制后": 1082.5,
    "南宋": 1127, "南宋建炎、绍兴初": 1128,
    "南宋绍兴元年十月九日": 1131.77,
    "南宋绍兴二十七年六月九日": 1157.43,
    "南宋绍兴二十九年九月十日": 1159.69,
    "南宋孝宗乾道间": 1170,
    "南宋乾道七年十月十六日": 1171.78,
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


def tp(w, title, type_, time):
    eid = entity_id(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


def alias_note(w, i, tid, quotation, field_name):
    cite(
        w, "Timepoints", tid, i, quotation,
        f"{F[i]['title']}的简称、别名只作名称证据，不另建实体。",
        field_name, note="纯简称、别名不另建实体",
    )


def parent_state(w, i, title, type_, time, event, quotation, category,
                 field_name=None):
    eid = w.find_entity(title, type_)
    if eid is None:
        return upsert_state(
            w, i, title, type_, time, event, quotation, category,
            f"为本条下级机构或官职建立 {title} 同期节点。", field_name,
        )
    tid = w.find_timepoint(eid, time)
    if tid is None:
        eid, tid = upsert_state(
            w, i, title, type_, time, event, quotation, category,
            f"为本条下级机构或官职建立 {title} 同期节点。", field_name,
        )
    else:
        cite(
            w, "Timepoints", tid, i, quotation,
            f"为 {title} 既有同期节点补充本条证据，不覆盖综合事件。", field_name,
        )
    rechain(w, eid, f"将 {title} 的 {time} 节点纳入完整全局时间链。")
    return eid, tid


def entry181():
    i, main = 181, F[181]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "诸陵勾当香火内品", "官职", "北宋",
        "由内侍充，掌诸陵香火供奉及将迎使客", main,
        "诸陵所内品", "据专条补足诸陵勾当香火内品的充任与职掌。",
        officer="内品",
    )
    for tomb in previous.EIGHT_TOMBS:
        staff(
            w, i, tp(w, tomb, "机构", "北宋"), tid, main,
            f"诸陵勾当香火内品掌{tomb}香火供奉等事；沿用第175条已明载的各陵设置。",
            staff_type="内品",
        )
    rechain(w, eid, "确认诸陵勾当香火内品时间链。")
    w.commit()


def canonicalize_lingtai(w, quotation):
    canonical = w.find_entity("陵台令", "官职")
    old = w.find_entity("宗正寺陵台令", "官职")
    if canonical is None:
        assert old is not None
        w.conn.execute(
            "update Entities set title='陵台令' where id=?", (old,)
        )
        w._br(
            "Entities", old,
            "据陵台令专条将先前依宗正寺编制暂名的‘宗正寺陵台令’规范为‘陵台令’。",
        )
        canonical = old
    assert old is None or old == canonical
    broad = w.find_timepoint(canonical, "宋前期")
    exact = w.find_timepoint(canonical, "北宋")
    if broad and not exact:
        w.conn.execute(
            "update Timepoints set time='北宋',event=?,quotation=?,"
            "attr_category='陵台令',attr_officer_type='职事官',attr_grade='从七品' "
            "where id=?",
            ("宋代沿置，无专官，由陵寝所在县县令或知县兼", quotation, broad),
        )
        w._br(
            "Timepoints", broad,
            "据陵台令专条将宽泛‘宋前期’节点规范为‘北宋’，补足职掌、官类与品位。",
        )
    return canonical


def entry182_183():
    i = 182
    main, history, duty, roster, rank, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "品位"), field(i, "简称"),
    )
    w = W(i)
    eid = canonicalize_lingtai(w, history)
    specs = (
        ("西汉", "庙寝令始置", history, "陵寝官源流", None),
        ("东汉", "有陵令，隶太常", history, "陵寝官源流", None),
        ("唐天宝十载", "始有陵台令之名", history, "陵寝官源流", None),
        ("北宋", "沿置，无专官，由陵寝所在县县令或知县兼；掌供奉陵寝、园庙、会圣宫取索事",
         history, "陵台令", "从七品"),
        ("南宋", "沿置，由会稽知县兼；掌帝后陵寝园陵供奉祭祀、修葺等取索事",
         history, "陵台令", "从七品"),
    )
    tids = {}
    for time, event, quotation, category, grade in specs:
        eid, tids[time] = upsert_state(
            w, i, "陵台令", "官职", time, event, quotation, category,
            f"据专条建立或校订陵台令 {time} 节点。", "职源与沿革",
            officer="职事官" if time in {"北宋", "南宋"} else None,
            grade=grade,
        )
    cite(w, "Timepoints", tids["北宋"], i, duty, "记录北宋陵台令供奉、取索职掌。", "职掌")
    cite(w, "Timepoints", tids["南宋"], i, duty, "记录南宋会稽陵台令供奉、取索职掌。", "职掌")
    cite(w, "Timepoints", tids["南宋"], i, rank, "记录陵台令从七品及兼衔知县的优异待遇。", "品位")
    office_eid, office_tp = upsert_state(
        w, i, "陵台令司", "机构", "北宋",
        "北宋创置，置于永安县一处，掌陵寝、园庙、会圣宫取索事", roster,
        "陵寝管理机构", "建立陵台令司的北宋设置、所在与职掌。", "编制",
    )
    staff(w, i, office_tp, tids["北宋"], roster, "陵台令司设陵台令，由永安知县兼。", "编制", quota=1, staff_type="职事官")
    alias_note(w, i, tids["北宋"], aliases, "简称")
    rechain(w, eid, "重建陵台令西汉源流至南宋的完整时间链。")
    rechain(w, office_eid, "确认陵台令司时间链。")
    w.commit()

    assert F[183]["fields"].get("__status__") == "placeholder"


def entry184():
    i, main = 184, F[184]["text"]
    w = W(i)
    eid, start = upsert_state(
        w, i, "巩县令兼陵台令事", "官职", "北宋太宗雍熙二年五月",
        "巩县令注官开始兼带‘兼陵台令事’衔", main,
        "陵台令兼差", "建立巩县令兼陵台令事始置节点。", officer="兼差官",
    )
    _, end = upsert_state(
        w, i, "巩县令兼陵台令事", "官职", "北宋真宗景德四年正月",
        "永安镇升县，巩县令兼衔至此停止", main,
        "陵台令兼差", "建立巩县令兼陵台令事终止节点。", officer="兼差官",
    )
    relationship(w, i, tp(w, "陵台令", "官职", "北宋"), start, "统称与实例", main, "巩县令兼陵台令事是北宋陵台令的具体兼衔实例。")
    rechain(w, eid, "连接巩县令兼陵台令事始置与终止节点。")
    w.commit()


def entry185():
    i, main = 185, F[185]["text"]
    w = W(i)
    office_eid, office = upsert_state(
        w, i, "陵台令司", "机构", "北宋真宗景德四年七月六日",
        "永安县设陵台令司，由知永安县事兼陵台令", main,
        "陵寝管理机构", "建立永安县陵台令司正式设置节点。",
    )
    eid, tid = upsert_state(
        w, i, "知陵台令兼永安县事", "官职", "北宋真宗景德四年七月六日",
        "始置，以奉诸陵寝园庙公事为主，知陵台令事衔冠于知县事之前", main,
        "陵台令兼差", "建立知陵台令兼永安县事始置与职掌节点。", officer="兼差官",
    )
    staff(w, i, office, tid, main, "永安县陵台令司由知永安县事兼领。", staff_type="兼差官")
    relationship(w, i, tp(w, "陵台令", "官职", "北宋"), tid, "统称与实例", main, "知陵台令兼永安县事是陵台令的永安县实例。")
    rechain(w, office_eid, "整理陵台令司北宋时间链。")
    rechain(w, eid, "确认知陵台令兼永安县事时间链。")
    w.commit()


def entry186_187():
    i, main = 186, F[186]["text"]
    w = W(i)
    first_eid, first = upsert_state(
        w, i, "知会稽县事兼主管攒宫事务", "官职", "南宋绍兴二十九年九月十日",
        "始置，主管南宋皇陵供奉事，职实与陵台令同；属堂除阙，许借绯服", main,
        "陵台令兼差", "建立会稽知县主管攒宫事务的始置、职掌和待遇节点。", officer="兼差官",
    )
    relationship(w, i, tp(w, "陵台令", "官职", "南宋"), first, "统称与实例", main, "原文明言其职实与陵台令同，作为南宋会稽实例。")
    rechain(w, first_eid, "确认知会稽县事兼主管攒宫事务时间链。")
    w.commit()

    i, main = 187, F[187]["text"]
    w = W(i)
    office_eid, office = upsert_state(
        w, i, "陵台令司", "机构", "南宋孝宗乾道间",
        "会稽主管攒宫事务改以陵台令名义运行", main,
        "陵寝管理机构", "建立南宋会稽陵台令司名称恢复节点。",
    )
    eid, tid = upsert_state(
        w, i, "知会稽县事兼陵台令", "官职", "南宋孝宗乾道间",
        "由主管攒宫事改称兼陵台令", main,
        "陵台令兼差", "建立知会稽县事兼陵台令改称节点。", officer="兼差官",
    )
    staff(w, i, office, tid, main, "南宋会稽陵台令司由知会稽县事兼陵台令主管。", staff_type="兼差官")
    relationship(w, i, tp(w, "陵台令", "官职", "南宋"), tid, "统称与实例", main, "知会稽县事兼陵台令是南宋陵台令实例。")
    relationship(w, i, tp(w, "知会稽县事兼主管攒宫事务", "官职", "南宋绍兴二十九年九月十日"), tid, "前后演变", main, "主管攒宫事改称兼陵台令。")
    rechain(w, office_eid, "整理陵台令司北宋至南宋时间链。")
    rechain(w, eid, "确认知会稽县事兼陵台令时间链。")
    w.commit()


PALACE_INSTANCES = (
    "昭慈园陵攒宫", "永祐陵攒宫", "永思陵攒宫", "永阜陵攒宫",
    "永崇陵攒宫", "永茂陵攒宫", "永穆陵攒宫", "永绍陵攒宫",
)


def entry188_189():
    i, main, duty, roster = 188, F[188]["text"], field(188, "职掌"), field(188, "编制")
    w = W(i)
    collective_eid, collective = upsert_state(
        w, i, "攒宫司", "机构", "南宋",
        "管理南宋帝后陵寝、园陵，掌看守、朔望祭祀与修治等事", main,
        "皇陵管理机构统称", "建立攒宫司统称、管理范围与职掌。",
    )
    cite(w, "Timepoints", collective, i, duty, "记录攒宫司看守、朔望祭祀与修治职掌。", "职掌")
    touched = {collective_eid}
    for title in PALACE_INSTANCES:
        eid, tid = upsert_state(
            w, i, title, "机构", "南宋", "南宋诸攒宫司所管理的帝后陵寝或园陵", main,
            "皇陵管理机构", f"原文明列{title}为南宋攒宫司实例。",
        )
        relationship(w, i, collective, tid, "统称与实例", main, f"攒宫司包括{title}。")
        touched.add(eid)
    post_tps = {}
    for title, event, officer in (
        ("攒宫都监", "攒宫司所置，管理祭祀及守卫事务", "差遣官"),
        ("攒宫提辖", "攒宫司所置，提辖守卫军兵使臣", "使臣"),
        ("攒宫巡检", "高宗朝攒宫司守卫使臣称巡检", "使臣"),
    ):
        eid = w.find_entity(title, "官职")
        tid = w.find_timepoint(eid, "南宋") if eid else None
        if tid is None:
            eid, tid = upsert_state(
                w, i, title, "官职", "南宋", event, roster,
                "攒宫司差遣官", f"据攒宫司编制建立{title}。", "编制", officer=officer,
            )
        else:
            cite(
                w, "Timepoints", tid, i, roster,
                f"为{title}既有专条节点补充攒宫司编制证据，不覆盖专条事件。", "编制",
            )
        staff(w, i, collective, tid, roster, f"攒宫司设置{title}。", "编制", staff_type=officer)
        post_tps[title] = tid
        touched.add(eid)
    cite(w, "Timepoints", collective, i, roster, "记录各攒宫看守兵士三百、百或七十八人等不定额，不误合并为统一定额。", "编制")
    for eid in touched:
        rechain(w, eid, "整理攒宫司、实例及所属差遣官时间链。")
    w.commit()

    i, main = 189, F[189]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "攒宫都监", "官职", "南宋",
        "差太祝官（文臣有出身人）充，朔望祭祀陪位并供养牙盘食、酒果", main,
        "攒宫司差遣官", "据专条补足攒宫都监的充任资格与祭祀职掌。", officer="差遣官",
    )
    staff(w, i, tp(w, "攒宫司", "机构", "南宋"), tid, main, "攒宫都监隶攒宫司并掌祭祀事务。", staff_type="差遣官")
    rechain(w, eid, "确认攒宫都监时间链。")
    w.commit()


def entry196():
    i = 196
    main, history, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别称"),
    )
    w = W(i)
    specs = (
        ("北齐", "已有大宗正寺之名", history, "宗室管理机构源流"),
        ("北宋景祐三年七月十九日", "始置大宗正司，统掌皇族教育、训谕、政令，纠察违失并裁决宗室纠纷词诉", history, "中央宗室管理机构"),
        ("宋代", "设六案及官吏，统掌皇族宗室事务", roster, "中央宗室管理机构"),
        ("南宋建炎、绍兴初", "大宗正司由建康迁广州、又迁绍兴，称大宗正行司", history, "中央宗室管理机构"),
        ("南宋绍兴元年十月九日", "另于行在置行在大宗正司", history, "中央宗室管理机构"),
        ("南宋乾道七年十月十六日", "绍兴府大宗正行司并归临安行在大宗正司，合二为一", history, "中央宗室管理机构"),
    )
    tids = {}
    for time, event, quotation, category in specs:
        eid, tids[time] = upsert_state(
            w, i, "大宗正司", "机构", time, event, quotation, category,
            f"据专条建立或校订大宗正司 {time} 节点。",
            "编制" if quotation == roster else "职源与沿革",
        )
    cite(w, "Timepoints", tids["北宋景祐三年七月十九日"], i, duty, "记录大宗正司教育训谕、纠察裁决及奏闻职掌。", "职掌")
    cite(w, "Timepoints", tids["宋代"], i, roster, "记录大宗正司长官、属官、六案与吏额。", "编制")
    alias_note(w, i, tids["宋代"], aliases, "简称与别称")

    branch_tps = {}
    for title, time, event in (
        ("绍兴府大宗正行司", "南宋建炎、绍兴初", "大宗正司迁至绍兴后的行司"),
        ("行在大宗正司", "南宋绍兴元年十月九日", "于行在所另置"),
    ):
        branch_eid, branch_tp = upsert_state(
            w, i, title, "机构", time, event, history,
            "南宋宗室管理机构", f"据沿革建立{title}节点。", "职源与沿革",
        )
        relationship(w, i, tids[time], branch_tp, "统称与实例", history, f"南宋大宗正司包括{title}这一具体分支。", "职源与沿革")
        branch_tps[title] = (branch_eid, branch_tp)
    _, merged = upsert_state(
        w, i, "行在大宗正司", "机构", "南宋乾道七年十月十六日",
        "绍兴府大宗正行司并入，合二为一", history,
        "南宋宗室管理机构", "建立两司合并节点。", "职源与沿革",
    )
    relationship(w, i, branch_tps["绍兴府大宗正行司"][1], merged, "前后演变", history, "绍兴府大宗正行司并归行在大宗正司。", "职源与沿革")

    for short in ("士案", "户案", "仪案", "兵案", "刑案", "工案"):
        case_title = f"大宗正司{short}"
        case_eid, case_tp = upsert_state(
            w, i, case_title, "机构", "宋代", "大宗正司六案之一", roster,
            "大宗正司办事机构", f"据编制明列建立{case_title}。", "编制",
        )
        relationship(w, i, tids["宋代"], case_tp, "上下级机构", roster, f"{case_title}为大宗正司六案之一。", "编制")
        rechain(w, case_eid, f"确认{case_title}时间链。")
    for touched in (eid, *(v[0] for v in branch_tps.values())):
        rechain(w, touched, "整理大宗正司北齐源流、北宋始置及南宋分合时间链。")
    w.commit()


def entry190():
    i, main, history, duty = 190, F[190]["text"], field(190, "职源"), field(190, "职掌")
    w = W(i)
    parent_eid, parent = parent_state(
        w, i, "大宗正司", "机构", "南宋绍兴二十七年六月九日",
        "辖检察宫陵所", main, "中央宗室管理机构",
    )
    eid, tid = upsert_state(
        w, i, "检察宫陵所", "机构", "南宋绍兴二十七年六月九日",
        "始置，隶大宗正司；检察诸攒宫司公事并承受皇陵诏旨、省札及申奏文字", history,
        "皇陵监察机构", "建立检察宫陵所始置与归隶节点。", "职源",
    )
    cite(w, "Timepoints", tid, i, duty, "记录检察宫陵所的检察、承受和申奏职掌。", "职掌")
    relationship(w, i, parent, tid, "上下级机构", main, "原文明确检察宫陵所隶宗正司；宗正司为大宗正司简称。")
    rechain(w, parent_eid, "将大宗正司绍兴二十七年节点纳入完整时间链。")
    rechain(w, eid, "确认检察宫陵所时间链。")
    w.commit()


def entry191_193():
    i, main = 191, F[191]["text"]
    w = W(i)
    eid, tang = upsert_state(
        w, i, "山陵使", "官职", "唐贞观间", "已见设置", main,
        "丧礼行事官", "建立山陵使唐代源流节点。",
    )
    _, song = upsert_state(
        w, i, "山陵使", "官职", "宋代",
        "以亲王或宰相充，主持大行皇帝及太皇太后、皇太后丧葬与葬礼", main,
        "丧礼行事官", "建立宋代山陵使充任与职掌节点。", officer="行事官",
    )
    rechain(w, eid, "连接山陵使唐代源流与宋代节点。")
    w.commit()

    i, main = 192, F[192]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "园陵使", "官职", "宋代",
        "以宰执官差充，主持太后、皇后及太妃等丧葬与葬礼", main,
        "丧礼行事官", "建立园陵使的充任对象与职掌。", officer="行事官",
    )
    rechain(w, eid, "确认园陵使时间链。")
    w.commit()

    i, main = 193, F[193]["text"]
    w = W(i)
    eid, generic = upsert_state(
        w, i, "陵官", "官职", "宋代", "诸陵使、副使等奉祀陵寝官的通称", main,
        "奉祀陵寝官通称", "建立陵官统称。", officer="差遣官",
    )
    for title in ("陵使", "宗正寺诸陵副使"):
        relationship(w, i, generic, tp(w, title, "官职", "北宋"), "统称与实例", main, f"{title}属于陵官所指诸陵使、副使。")
    rechain(w, eid, "确认陵官通称时间链。")
    w.commit()


def entry194_195():
    i = 194
    main, history, duty = F[i]["text"], field(i, "职源与沿革"), field(i, "职掌")
    w = W(i)
    eid, western = upsert_state(
        w, i, "园令", "官职", "西汉", "太常官下已有园令、丞", history,
        "园陵官源流", "建立园令西汉源流节点。", "职源与沿革",
    )
    _, song = upsert_state(
        w, i, "园令", "官职", "北宋英宗治平三年",
        "见置，以大使臣充，掌亲王园出纳神主等事", history,
        "亲王园职事官", "建立北宋园令设置、充任与职掌节点。", "职源与沿革", officer="职事官",
    )
    cite(w, "Timepoints", song, i, duty, "记录园令掌亲王园出纳神主等职掌。", "职掌")
    rechain(w, eid, "连接园令西汉源流与北宋节点。")
    w.commit()

    i, main = 195, F[195]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "知园令", "官职", "宋代",
        "园令以朝臣充者称知园令；京官、大使臣充者不带知字", main,
        "亲王园职事官", "建立知园令的充任与命名规则。", officer="职事官",
    )
    relationship(w, i, tp(w, "园令", "官职", "北宋英宗治平三年"), tid, "统称与实例", main, "知园令是园令由朝臣充任时的具体称法。")
    rechain(w, eid, "确认知园令时间链。")
    w.commit()


def dzz_parent(w, i, time, event, quotation, field_name=None):
    return parent_state(
        w, i, "大宗正司", "机构", time, event, quotation,
        "中央宗室管理机构", field_name,
    )


def entry197():
    i = 197
    main, history, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    specs = (
        ("北宋庆历四年", "始置，以知大宗正司事赵允让改任，总领大宗正司事", history),
        ("北宋元丰改制后", "元丰后仍保留判衔，为官司带判者中的特例", rank),
        ("南宋", "沿置，总领大宗正司事", history),
    )
    tids = {}
    for time, event, quotation in specs:
        eid, tids[time] = upsert_state(
            w, i, "判大宗正司事", "官职", time, event, quotation,
            "大宗正司长官", f"据专条建立判大宗正司事 {time} 节点。",
            "品位" if quotation == rank else "职源与沿革", officer="职事官",
        )
        _, parent = dzz_parent(w, i, time, "置判大宗正司事", quotation, "品位" if quotation == rank else "职源与沿革")
        staff(w, i, parent, tids[time], quotation, "判大宗正司事总领大宗正司事。", "品位" if quotation == rank else "职源与沿革", quota=1 if time == "北宋庆历四年" else None, staff_type="职事官")
    cite(w, "Timepoints", tids["北宋庆历四年"], i, duty, "记录判大宗正司事总领本司职掌。", "职掌")
    cite(w, "Timepoints", tids["北宋庆历四年"], i, roster, "记录判大宗正司事一员。", "编制")
    alias_note(w, i, tids["北宋庆历四年"], aliases, "简称与别名")
    rechain(w, eid, "整理判大宗正司事北宋至南宋时间链。")
    w.commit()


def entry198():
    i, main, aliases = 198, F[198]["text"], field(198, "简称")
    w = W(i)
    eid, tid = upsert_state(
        w, i, "同判大宗正司事", "官职", "宋代",
        "大宗正司置判官二员时，位次者带同字；同判可递迁为判", main,
        "大宗正司长官", "建立同判大宗正司事的设置条件、序位与递迁。", officer="职事官",
    )
    _, parent = dzz_parent(w, i, "宋代", "或置同判大宗正司事", main)
    staff(w, i, parent, tid, main, "同判大宗正司事为置判二员时的次位长官。", staff_type="职事官")
    relationship(w, i, tid, tp(w, "判大宗正司事", "官职", "北宋庆历四年"), "前后演变", main, "原文明言同判递迁为判。")
    alias_note(w, i, tid, aliases, "简称")
    rechain(w, eid, "确认同判大宗正司事时间链。")
    w.commit()


def entry199():
    i = 199
    main, history, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    tids = {}
    for time, event in (
        ("北宋景祐三年七月十九日", "始置，领大宗正司事并统掌皇族宗室政令、训导与纠察"),
        ("南宋", "沿置，领大宗正司事"),
    ):
        eid, tids[time] = upsert_state(
            w, i, "知大宗正司事", "官职", time, event, history,
            "大宗正司长官", f"据专条建立知大宗正司事 {time} 节点。", "职源与沿革",
            officer="职事官", grade="宗室团练使（从五品）以上充" if time.startswith("北宋") else None,
        )
        _, parent = dzz_parent(w, i, time, "置知大宗正司事", history, "职源与沿革")
        staff(w, i, parent, tids[time], history, "知大宗正司事领本司事。", "职源与沿革", quota=1 if time.startswith("北宋") else None, staff_type="职事官")
    cite(w, "Timepoints", tids["北宋景祐三年七月十九日"], i, duty, "记录知大宗正司事训导、纠察并统掌宗室政令的职掌。", "职掌")
    cite(w, "Timepoints", tids["北宋景祐三年七月十九日"], i, rank, "记录由宗室团练使以上且行谊堪为表率者充。", "品位")
    cite(w, "Timepoints", tids["北宋景祐三年七月十九日"], i, roster, "记录知大宗正司事一人。", "编制")
    alias_note(w, i, tids["北宋景祐三年七月十九日"], aliases, "简称")
    rechain(w, eid, "整理知大宗正司事北宋至南宋时间链。")
    w.commit()


def entry200():
    i, main, aliases = 200, F[200]["text"], field(200, "简称")
    w = W(i)
    eid, tid = upsert_state(
        w, i, "同知大宗正司事", "官职", "北宋治平元年六月十三日",
        "始置，位次于知大宗正司事，职掌与知大宗正司事同", main,
        "大宗正司长官", "建立同知大宗正司事始置、序位和职掌节点。", officer="职事官",
    )
    _, parent = dzz_parent(w, i, "北宋治平元年六月十三日", "始置同知大宗正司事", main)
    staff(w, i, parent, tid, main, "同知大宗正司事为本司次位长官。", quota=1, staff_type="职事官")
    alias_note(w, i, tid, aliases, "简称")
    rechain(w, eid, "确认同知大宗正司事时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(181, 201)] == [
        "诸陵勾当香火内品", "陵台令司", "陵台令", "巩县令兼陵台令事",
        "知陵台令兼永安县事", "知会稽县事兼主管攒宫事务", "知会稽县事兼陵台令",
        "攒宫司", "攒宫都监", "检察宫陵所", "山陵使", "园陵使", "陵官",
        "园令", "知园令", "大宗正司", "判大宗正司事", "同判大宗正司事",
        "知大宗正司事", "同知大宗正司事",
    ]
    entry181()
    entry182_183()
    entry184()
    entry185()
    entry186_187()
    entry188_189()
    entry196()
    entry190()
    entry191_193()
    entry194_195()
    entry197()
    entry198()
    entry199()
    entry200()


if __name__ == "__main__":
    main()
