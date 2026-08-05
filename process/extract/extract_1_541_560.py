#!/usr/bin/env python3
"""提取第一编第541-560条：内侍省祗候班诸内品与内侍省寄班。"""

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
    "SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db")
)


def repair_dictionary_source():
    """据原书第67-68页修复#546-547、#549及#554-555的OCR与错并。"""
    proper_554 = "宦官名。隶内侍省祗候班。真宗朝已见置（《宋会要·职官》57之2）。"
    proper_555 = "宦官名。隶内侍省祗候班。真宗朝已见置（《宋会要·职官》57之2）。"
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            for entry_id in (546, 547, 549):
                row = conn.execute(f"SELECT text FROM {table} WHERE id=?", (entry_id,)).fetchone()
                assert row and row[0]
                fixed = row[0].replace("宜官名", "宦官名")
                conn.execute(f"UPDATE {table} SET text=? WHERE id=?", (fixed, entry_id))

            row554 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=554"
            ).fetchone()
            row555 = conn.execute(
                f"SELECT title,text,fields FROM {table} WHERE id=555"
            ).fetchone()
            assert row554 and row555 and row554[0] == "西京北班内品"
            assert "真宗朝已见置" in (row554[1] or "")
            assert row555[0] in ("鄂州内品", "郢州内品")
            conn.execute(
                f"UPDATE {table} SET text=?,fields=NULL WHERE id=554", (proper_554,)
            )
            conn.execute(
                f"UPDATE {table} SET title='郢州内品',text=?,fields=NULL WHERE id=555",
                (proper_555,),
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


F = {i: load(i) for i in range(541, 561)}


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
    return w.citation(
        table, target_id, C(i, name), quotation, decision, **kwargs
    )


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
    **cite_kwargs,
):
    tid = w.timepoint(
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
    cite(w, "Timepoints", tid, i, quotation, decision, name, **cite_kwargs)
    return tid


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
    **cite_kwargs,
):
    rid = w.relationship(
        subject,
        object_,
        kind,
        decision,
        quotation,
        staff_type=staff_type,
        staff_quota=staff_quota,
    )
    cite(w, "Relationships", rid, i, quotation, decision, name, **cite_kwargs)
    return rid


def find_entity(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def find_tp(w, title, time, type_=None):
    eid = find_entity(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


def province_tp(w):
    return find_tp(w, "内侍省", "北宋景德三年（1006）五月", "机构")


def waiting_class_tp(w):
    return find_tp(w, "内侍省祗候班", "北宋大中祥符二年（1009）", "官职")


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w,
        "Timepoints",
        tp_id,
        i,
        quotation,
        f"补证{F[i]['title']}的{name}；称谓不另建实体。",
        name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def waiting_office(
    i,
    time,
    event,
    history_name="职源",
    grade="从九品",
    aliases=(),
    duty_name=None,
):
    """写入祗候班单项官名、时间证据、品位及两类隶属关系。"""
    w = W(i)
    main = F[i]["text"]
    history = field(i, history_name) if history_name else main
    eid = w.entity(F[i]["title"], "官职", "正式词头定义该祗候班官名。", quotation=main)
    tp = timepoint(
        w,
        i,
        eid,
        time,
        event,
        history,
        f"建立{F[i]['title']}有据时间点。",
        history_name,
        category="祗候班",
        grade=grade,
    )
    if "品位" in F[i]["fields"]:
        cite(w, "Timepoints", tp, i, field(i, "品位"), f"补证{F[i]['title']}品位与班序。", "品位")
    if duty_name and duty_name in F[i]["fields"]:
        cite(w, "Timepoints", tp, i, field(i, duty_name), f"补证{F[i]['title']}职掌。", duty_name)
    relation(w, i, waiting_class_tp(w), tp, "统称与实例", main,
             f"内侍省祗候班为统称，{F[i]['title']}为实例。")
    relation(w, i, province_tp(w), tp, "编制隶属", main,
             f"{F[i]['title']}隶内侍省。", staff_type="祗候班")
    for alias in aliases:
        alias_citation(w, i, tp, alias)
    w.commit()


def entry541():
    waiting_office(
        541,
        "北宋大中祥符二年以后至熙宁七年以前（1009—1074）",
        "设置，居内侍省祗候班最高位",
        aliases=("简称",),
    )


def entry542():
    i = 542
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源")
    eid = w.entity("祗候高班内品", "官职", "正式词头定义该祗候班官名。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋大中祥符八年（1015）五月十二日",
        "由内侍省高班内品改为前殿祗候高班内品，为内侍省祗候高班内品设置之始",
        history, "建立祗候高班内品始置节点。", "职源", category="祗候班", grade="从九品",
    )
    cite(w, "Timepoints", tp, i, field(i, "品位"), "补证品位、比拟武阶与班序。", "品位")
    cite(w, "Timepoints", tp, i, field(i, "职掌"), "补证职掌同内侍省祗候班。", "职掌")
    relation(w, i, find_tp(w, "内侍省高班内品", "北宋景德三年（1006）五月", "官职"),
             tp, "前后演变", history, "内侍省高班内品改为前殿祗候高班内品。", "职源")
    relation(w, i, waiting_class_tp(w), tp, "统称与实例", main,
             "内侍省祗候班为统称，祗候高班内品为实例。")
    relation(w, i, province_tp(w), tp, "编制隶属", main,
             "祗候高班内品隶内侍省。", staff_type="祗候班")
    w.commit()


def entry543():
    waiting_office(543, "北宋大中祥符二年（1009）", "已定置", duty_name="职掌")


def entry544():
    waiting_office(544, "北宋嘉祐六年（1061）", "已见设置", duty_name="职掌")


def entry545():
    waiting_office(545, "北宋熙宁七年（1074）", "已见设置", duty_name="职掌")


def entry546():
    waiting_office(
        546,
        "北宋大中祥符二年（1009）以前",
        "至迟已置",
        aliases=("别名",),
        duty_name="职掌",
    )


def entry547():
    i = 547
    waiting_office(
        i,
        "北宋大中祥符二年（1009）以前",
        "与把门内品同，至迟已置",
        history_name="职源、职掌",
    )


def entry548():
    waiting_office(
        548,
        "北宋大中祥符二年以后至熙宁七年以前（1009—1074）",
        "设置",
        aliases=("简称",),
        duty_name="职掌",
    )


def entry549():
    i = 549
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源")
    old_e = w.entity("洒扫院子", "官职", "职源字段记载改名前官名。", quotation=history)
    old_tp = timepoint(
        w, i, old_e, "北宋大中祥符二年及其后（1009以后）",
        "改名前称洒扫院子", history, "建立洒扫院子前身承载节点。", "职源", category="宦官差役",
    )
    eid = w.entity("北班内品", "官职", "正式词头定义该祗候班官名。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋大中祥符二年以后某年七月（1009以后）",
        "由洒扫院子改名", history, "建立北班内品改名节点。", "职源", category="祗候班", grade="从九品",
    )
    cite(w, "Timepoints", tp, i, field(i, "品位"), "补证品位、比拟武阶与班序。", "品位")
    relation(w, i, old_tp, tp, "前后演变", history, "洒扫院子改名为北班内品。", "职源")
    relation(w, i, waiting_class_tp(w), tp, "统称与实例", main,
             "内侍省祗候班为统称，北班内品为实例。")
    relation(w, i, province_tp(w), tp, "编制隶属", main,
             "北班内品隶内侍省。", staff_type="祗候班")
    w.commit()


def entry550():
    i = 550
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源")
    old_e = find_entity(w, "洒扫院子", "官职")
    old_tp = find_tp(w, "洒扫院子", "北宋大中祥符二年及其后（1009以后）", "官职")
    eid = w.entity("散内品", "官职", "正式词头定义该祗候班官名。", quotation=main)
    tp = timepoint(
        w, i, eid, "北宋大中祥符二年（1009）九月",
        "由洒扫院子改名，供洒扫殿庭院子等差役", history,
        "建立散内品改名节点。", "职源", category="祗候班", grade="从九品",
    )
    cite(w, "Timepoints", tp, i, field(i, "职掌"), "补证供洒扫殿庭院子等差役。", "职掌")
    cite(w, "Timepoints", tp, i, field(i, "品位"), "补证品位与班序。", "品位")
    relation(w, i, old_tp, tp, "前后演变", history, "洒扫院子改名为散内品。", "职源")
    relation(w, i, waiting_class_tp(w), tp, "统称与实例", main,
             "内侍省祗候班为统称，散内品为实例。")
    relation(w, i, province_tp(w), tp, "编制隶属", main,
             "散内品隶内侍省。", staff_type="祗候班")
    w.commit()


def entry551():
    waiting_office(
        551,
        "北宋大中祥符二年（1009）九月",
        "与散内品同，列祗候班末等",
        history_name=None,
    )


def true_reign_office(i, event="真宗朝已见设置"):
    waiting_office(i, "北宋真宗朝（997—1022）", event, history_name=None)


def entry552(): true_reign_office(552)
def entry553(): true_reign_office(553)
def entry554(): true_reign_office(554)
def entry555(): true_reign_office(555)


def entry556():
    waiting_office(
        556,
        "北宋大中祥符五年（1012）十一月",
        "已见唐州内品；内侍杨怀愚受罚后隶此",
        history_name=None,
    )


def entry557(): true_reign_office(557)


SEVEN = (
    "寄班祗候", "寄班供奉", "寄班侍禁", "寄班殿直", "寄班奉职", "寄班借职", "寄班小底"
)


def entry558():
    i = 558
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源")
    eid = find_entity(w, "内侍省寄班", "官职")
    base = find_tp(w, "内侍省寄班", "北宋时期（具体时间未载）", "官职")
    cite(w, "Timepoints", base, i, main, "补证内侍省寄班隶内侍省。")
    begin = timepoint(
        w, i, eid, "北宋咸平三年（1000）正月以前",
        "不迟于此时设置，已见寄班供奉官", history,
        "建立内侍省寄班始见节点。", "职源", category="寄班使臣总称",
    )
    cite(w, "Timepoints", begin, i, field(i, "职掌"), "补证侍奉内朝、驿传急诏及行幸扈从职掌。", "职掌")
    cite(w, "Timepoints", begin, i, field(i, "品位"), "补证位次低于入内内侍省寄班。", "品位")
    staffing = field(i, "编制")
    cite(w, "Timepoints", begin, i, staffing, "补证内侍省寄班七项编制。", "编制")
    relation(w, i, province_tp(w), base, "编制隶属", main,
             "内侍省寄班隶内侍省；关系挂在正式定名后的总称节点，避免把1000年始见节点误接到1006年才定名的机构节点。",
             staff_type="寄班")
    for title in SEVEN:
        child_e = find_entity(w, title, "官职")
        child_tp = timepoint(
            w, i, child_e, "北宋时期（具体时间未载）",
            "列入内侍省寄班", staffing,
            f"建立{title}列入内侍省寄班的专属节点。", "编制", category="寄班使臣",
        )
        relation(w, i, begin, child_tp, "统称与实例", staffing,
                 f"内侍省寄班为统称，{title}为实例。", "编制")
        relation(w, i, province_tp(w), child_tp, "编制隶属", main,
                 f"{title}作为内侍省寄班官隶内侍省。", staff_type="寄班")
    alias_citation(w, i, begin, "简称与别名")
    w.commit()


def entry560():
    i = 560
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源")
    eid = find_entity(w, "寄班祗候", "官职")
    start = timepoint(
        w, i, eid, "北宋天禧四年（1020）四月十六日以前",
        "不迟于此日设置", history, "建立寄班祗候始见节点。", "职源", category="寄班使臣",
    )
    cite(w, "Timepoints", start, i, field(i, "职能"), "补证安排皇亲戚族子弟及迁转阁门祗候。", "职能")
    cite(w, "Timepoints", start, i, field(i, "品位"), "补证居内侍省寄班最高位及亲近皇帝。", "品位")
    yuanfeng = timepoint(
        w, i, eid, "北宋元丰法（1078—1085）",
        "定员十五员", field(i, "编制"), "建立元丰法定额节点。", "编制", category="编制",
    )
    reaffirm = timepoint(
        w, i, eid, "南宋绍兴九年（1139）六月二十三日",
        "绍兴间沿置；重申依元丰法以十五员为额", field(i, "编制"),
        "建立绍兴九年重申定额节点。", "编制", category="编制",
    )
    cite(w, "Timepoints", reaffirm, i, history, "补证南宋绍兴间仍沿置。", "职源")
    class_tp = find_tp(w, "内侍省寄班", "北宋咸平三年（1000）正月以前", "官职")
    relation(w, i, class_tp, start, "统称与实例", main,
             "内侍省寄班为统称，寄班祗候为实例。")
    relation(w, i, province_tp(w), start, "编制隶属", main,
             "寄班祗候隶内侍省。", staff_type="寄班", staff_quota="十五员（元丰法；绍兴九年重申）")
    alias_citation(w, i, start, "简称")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(541, 561)] == [
        "祗候高品", "祗候高班内品", "祗候内品", "贴祗候内品", "内品", "把门内品",
        "后苑内品", "后苑勾当事内品", "北班内品", "散内品", "后苑散内品",
        "在京黄门内品", "外处拣来内品", "西京北班内品", "郢州内品", "唐州内品",
        "复州内品", "内侍省寄班", "寄班使臣", "寄班祗候",
    ]
    assert F[554]["text"] == F[555]["text"]
    assert not F[555]["fields"]
    assert F[559]["fields"].get("__status__") == "placeholder" and not F[559]["text"]
    entry541(); entry542(); entry543(); entry544(); entry545(); entry546(); entry547(); entry548()
    entry549(); entry550(); entry551(); entry552(); entry553(); entry554(); entry555(); entry556()
    entry557(); entry558(); entry560()


if __name__ == "__main__":
    main()
