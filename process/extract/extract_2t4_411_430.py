#!/usr/bin/env python3
"""提取 chapter2t4 第411–430条：河渠、推勘、粮料与帐勾磨勘。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get("SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db"))


def load(i):
    with sqlite3.connect(DICT_DB) as c:
        row = c.execute("select title,page,text,fields from chapter2t4 where id=?", (i,)).fetchone()
    fields = json.loads(row[3] or "{}")
    return {"title": row[0], "page": row[1], "text": row[2] or "", "fields": fields,
            "values": [row[2] or ""] + [str(v) for k, v in fields.items() if not k.startswith("_")]}


F = {i: load(i) for i in range(411, 431)}


def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])
def C(i): return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'


def entity(w, title, type_, quotation, decision):
    return w.entity(title, type_, decision, quotation=quotation)


def cite(w, table, rid, i, quotation, decision, **kw):
    return w.citation(table, rid, C(i), quotation, decision, **kw)


def tp(w, eid, time, event, i, quotation, category, decision, **kw):
    tid = w.timepoint(eid, time, event, decision, quotation, attr_category=category, **kw)
    cite(w, "Timepoints", tid, i, quotation, decision)
    return tid


def rel(w, source, target, kind, i, quotation, decision, **kw):
    rid = w.relationship(source, target, kind, decision, quotation, **kw)
    cite(w, "Relationships", rid, i, quotation, decision)
    return rid


def node(w, title, time, type_=None):
    eid = w.find_entity(title, type_); assert eid, f"缺实体：{title}"
    tid = w.find_timepoint(eid, time); assert tid, f"{title}缺时间点：{time}"
    return eid, tid


def chain(w, tids, decision):
    assert len(tids) == len(set(tids)), tids
    for pos, tid in enumerate(tids):
        w.relink(tid, decision,
                 prev_id=tids[pos - 1] if pos else None,
                 succ_id=tids[pos + 1] if pos + 1 < len(tids) else None)


def chain_times(w, eid, times, decision):
    tids = [w.find_timepoint(eid, time) for time in times]
    assert all(tids), list(zip(times, tids))
    chain(w, tids, decision)


def sansi_tp(w, i, time, event, quotation):
    eid = w.find_entity("三司", "机构"); assert eid
    tid = w.find_timepoint(eid, time)
    if not tid:
        tid = tp(w, eid, time, event, i, quotation, "财政机构",
                 f"据第{i}条补建三司在{time}的制度节点。", chain="none")
    return tid


def seed_officers():
    for i, title in ((412, "都大提举河渠司"), (413, "勾当河渠司公事"),
                     (415, "知三司推勘院事"), (416, "管勾三司推勘官"),
                     (419, "在京都粮料使"), (420, "西京粮料院使"),
                     (422, "勾当诸司粮料院公事"), (424, "勾当马军粮料院公事"),
                     (426, "勾当步军粮料院公事"), (428, "勾当马步军专勾司公事")):
        z = F[i]["text"] or next(iter(F[i]["fields"].values()))
        w = W(i); entity(w, title, "官职", z, f"第{i}条独立定义{title}为差遣。")
        w.commit()


def entry411_413():
    i = 411; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = w.find_entity("三司河渠司", "机构") or entity(w, "三司河渠司", "机构", z, "本条明载三司河渠司为官司。")
    old = w.find_timepoint(eid, "宋代（未载具体年月）")
    if old and not w.find_timepoint(eid, "北宋皇祐三年五月二十三日"):
        w.conn.execute("update Timepoints set time=?,event=?,quotation=?,attr_category=? where id=?",
                       ("北宋皇祐三年五月二十三日", "始置，提举黄河、汴河等河堤修筑工料", h, "河渠机构", old))
        w._br("Timepoints", old, "本条给出确切始置时间，将原无确年节点更新为皇祐三年。")
        start = old
    else:
        start = tp(w, eid, "北宋皇祐三年五月二十三日", "始置，提举黄河、汴河等河堤修筑工料",
                   i, h, "河渠机构", "建三司河渠司始置节点。", chain="none")
    cite(w, "Timepoints", start, i, h, "补证三司河渠司始置。", note="职源")
    end = tp(w, eid, "北宋嘉祐三年十一月二十二日", "罢，代之以都水监",
             i, h, "河渠机构", "建三司河渠司废罢节点。", chain="none")
    chain(w, [start, end], "连接三司河渠司置罢节点。")
    parent = sansi_tp(w, i, "北宋皇祐三年五月二十三日", "始置河渠司", h)
    rel(w, parent, start, "上下级机构", i, z, "三司河渠司隶三司。")
    water_e = entity(w, "都水监", "机构", h, "原文明载河渠司罢后代之以都水监。")
    water_t = tp(w, water_e, "北宋嘉祐三年十一月二十二日", "承接三司河渠司职事",
                 i, h, "河渠机构", "建都水监承接节点。")
    rel(w, end, water_t, "前后演变", i, h, "三司河渠司罢后由都水监承接。")
    for title in ("都大提举河渠司", "勾当河渠司公事"):
        oe = w.find_entity(title, "官职"); assert oe
        ot = tp(w, oe, "北宋皇祐三年五月二十三日", "随河渠司设置，参领河渠公事",
                i, comp, "河渠差遣", f"据河渠司编制建{title}节点。")
        quota = 2 if title == "勾当河渠司公事" else None
        rel(w, start, ot, "编制隶属", i, comp, f"河渠司官额有{title}。", staff_quota=quota, staff_type="官")
    w.commit()

    i = 412; z = F[i]["text"]; w = W(i)
    tid = node(w, "都大提举河渠司", "北宋皇祐三年五月二十三日", "官职")[1]
    w.conn.execute("update Timepoints set attr_officer_type='文臣升朝官' where id=?", (tid,))
    w._br("Timepoints", tid, "本条明载由文臣升朝官中谙熟水利者差充。")
    cite(w, "Timepoints", tid, i, z, "补证都大提举河渠司任官资格与职掌。", note="品位、职掌")
    w.commit()

    i = 413; z = F[i]["text"]; w = W(i)
    tid = node(w, "勾当河渠司公事", "北宋皇祐三年五月二十三日", "官职")[1]
    cite(w, "Timepoints", tid, i, z, "补证勾当河渠司公事职掌、二员编制与序位。", note="职掌、编制")
    office = node(w, "三司河渠司", "北宋皇祐三年五月二十三日", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "勾当河渠司公事为河渠司属官二员。", staff_quota=2, staff_type="官")
    w.commit()


def entry414_416():
    i = 414; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = entity(w, "三司推勘院", "机构", z, "本条明载三司推勘院为三司属署。")
    start = tp(w, eid, "北宋开宝八年十一月十日", "始置，掌理三司狱案",
               i, h, "司法机构", "建三司推勘院始置节点。", chain="none")
    end = tp(w, eid, "北宋开宝八年后不久", "罢院，改置推勘官",
             i, h, "司法机构", "建三司推勘院不久罢院节点。", chain="none")
    chain(w, [start, end], "连接三司推勘院置罢节点。")
    parent = sansi_tp(w, i, "北宋开宝八年十一月十日", "始置推勘院", h)
    rel(w, parent, start, "上下级机构", i, z, "三司推勘院隶三司。")
    officer_e = w.find_entity("知三司推勘院事", "官职"); assert officer_e
    officer_t = tp(w, officer_e, "北宋开宝八年十一月十日", "推勘院主管官",
                   i, comp, "司法差遣", "据推勘院编制建主管官节点。")
    rel(w, start, officer_t, "编制隶属", i, comp, "推勘院官额有知推勘院事。", staff_type="官")
    w.commit()

    i = 415; z = F[i]["text"]; w = W(i)
    tid = node(w, "知三司推勘院事", "北宋开宝八年十一月十日", "官职")[1]
    w.conn.execute("update Timepoints set attr_officer_type='京官' where id=?", (tid,))
    w._br("Timepoints", tid, "本条明载推勘院主管官以京官充任。")
    cite(w, "Timepoints", tid, i, z, "补证始置时间、主管身份与任官类型。")
    w.commit()

    i = 416; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("管勾三司推勘官", "官职"); assert eid
    start = tp(w, eid, "北宋开宝八年后不久", "罢推勘院后置推勘官一员",
               i, z, "司法差遣", "建管勾三司推勘官始置节点。", chain="none")
    end = tp(w, eid, "北宋治平三年", "废罢",
             i, z, "司法差遣", "建管勾三司推勘官废罢节点。", chain="none")
    restore = tp(w, eid, "北宋熙宁二年九月", "复置",
                 i, z, "司法差遣", "建管勾三司推勘官复置节点。", chain="none")
    chain(w, [start, end, restore], "连接管勾三司推勘官置罢复置节点。")
    parent = sansi_tp(w, i, "北宋熙宁二年九月", "复置推勘官", z)
    rel(w, parent, restore, "编制隶属", i, z, "复置管勾三司推勘官一员。", staff_quota=1, staff_type="官")
    w.commit()


def entry417():
    i = 417; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = entity(w, "三司勾当公事", "官职", z, "本条明载三司勾当公事为差遣。")
    start = tp(w, eid, "北宋庆历元年正月七日", "始置，分左右厢检计、定夺、点检财物",
               i, h, "财政差遣", "建三司勾当公事始置节点。", chain="none")
    end = tp(w, eid, "北宋至和间", "废罢",
             i, h, "财政差遣", "建三司勾当公事至和间废罢节点。", chain="none")
    restore = tp(w, eid, "北宋熙宁二年九月", "复置",
                 i, h, "财政差遣", "建三司勾当公事复置节点。", chain="none")
    chain(w, [start, end, restore], "连接三司勾当公事置罢复置节点。")
    p1 = sansi_tp(w, i, "北宋庆历元年正月七日", "始置勾当公事官", h)
    p2 = sansi_tp(w, i, "北宋熙宁二年九月", "复置勾当公事官", h)
    rel(w, p1, start, "编制隶属", i, comp, "三司勾当公事二员。", staff_quota=2, staff_type="官")
    rel(w, p2, restore, "编制隶属", i, comp, "三司复置勾当公事官。", staff_quota=2, staff_type="官")
    w.commit()


GRAIN_INSTITUTIONS = ("诸司粮料院", "马军粮料院", "步军粮料院")


def seed_grain_entities():
    for i, title in ((421, "诸司粮料院"), (423, "马军粮料院"), (425, "步军粮料院")):
        z = F[i]["text"]; w = W(i); entity(w, title, "机构", z, f"第{i}条独立定义{title}为官署。")
        w.commit()


def entry418():
    i = 418; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; w = W(i)
    eid = entity(w, "粮料院", "机构", z, "本条明载粮料院为三司属司。")
    song = tp(w, eid, "宋初", "已置于京师安定坊",
              i, h, "俸禄发放机构", "建粮料院宋初节点。", chain="none")
    split = tp(w, eid, "北宋太平兴国五年正月二十八日", "一分为诸司、马军、步军三粮料院",
               i, h, "俸禄发放机构", "建粮料院分院节点。", chain="none")
    chain(w, [song, split], "连接粮料院宋初设置与分院节点。")
    parent_song = node(w, "三司", "宋初", "机构")[1]
    parent_split = sansi_tp(w, i, "北宋太平兴国五年正月二十八日", "粮料院一分为三", h)
    rel(w, parent_song, song, "上下级机构", i, z, "粮料院隶三司。")
    combined_e = entity(w, "马步军粮料院", "机构", h, "太平兴国八年马、步军粮料院合为一院。")
    combined_start = tp(w, combined_e, "北宋太平兴国八年", "由马军、步军粮料院合并",
                        i, h, "俸禄发放机构", "建马步军粮料院合置节点。", chain="none")
    combined_end = tp(w, combined_e, "北宋端拱后", "复分为马军、步军粮料院",
                      i, h, "俸禄发放机构", "建马步军粮料院复分节点。", chain="none")
    chain(w, [combined_start, combined_end], "连接马步军粮料院合分节点。")
    child_t = {}
    for title in GRAIN_INSTITUTIONS:
        ce = w.find_entity(title, "机构"); assert ce
        first = tp(w, ce, "北宋太平兴国五年正月二十八日", "由在京粮料院分出",
                   i, h, "俸禄发放机构", f"建{title}分出节点。", chain="none")
        child_t[(title, "first")] = first
        rel(w, split, first, "前后演变", i, h, f"粮料院分出{title}。")
        rel(w, parent_split, first, "上下级机构", i, z, f"{title}隶三司。")
    horse_end = tp(w, w.find_entity("马军粮料院", "机构"), "北宋太平兴国八年", "与步军粮料院合并",
                   i, h, "俸禄发放机构", "建马军粮料院合并节点。", chain="none")
    foot_end = tp(w, w.find_entity("步军粮料院", "机构"), "北宋太平兴国八年", "与马军粮料院合并",
                  i, h, "俸禄发放机构", "建步军粮料院合并节点。", chain="none")
    rel(w, horse_end, combined_start, "前后演变", i, h, "马军粮料院并入马步军粮料院。")
    rel(w, foot_end, combined_start, "前后演变", i, h, "步军粮料院并入马步军粮料院。")
    horse_restore = tp(w, w.find_entity("马军粮料院", "机构"), "北宋端拱后", "由马步军粮料院复分",
                       i, h, "俸禄发放机构", "建马军粮料院复分节点。", chain="none")
    foot_restore = tp(w, w.find_entity("步军粮料院", "机构"), "北宋端拱后", "由马步军粮料院复分",
                      i, h, "俸禄发放机构", "建步军粮料院复分节点。", chain="none")
    chain(w, [child_t[("马军粮料院", "first")], horse_end, horse_restore], "连接马军粮料院沿革。")
    chain(w, [child_t[("步军粮料院", "first")], foot_end, foot_restore], "连接步军粮料院沿革。")
    rel(w, combined_end, horse_restore, "前后演变", i, h, "马步军粮料院复分出马军粮料院。")
    rel(w, combined_end, foot_restore, "前后演变", i, h, "马步军粮料院复分出步军粮料院。")
    w.commit()


def entry419_420():
    for i, title, office_title in ((419, "在京都粮料使", "粮料院"), (420, "西京粮料院使", "西京粮料院")):
        z = F[i]["text"]; w = W(i); eid = w.find_entity(title, "官职"); assert eid
        five = tp(w, eid, "五代", "已置，由三司大将担任", i, z, "粮料差遣", f"建{title}五代节点。", chain="none")
        song = tp(w, eid, "宋初", "沿置，由三司大将担任", i, z, "粮料差遣", f"建{title}宋初节点。", chain="none")
        change = tp(w, eid, "北宋开宝六年二月", "改由文臣京官担任", i, z, "粮料差遣",
                    f"建{title}任官变化节点。", attr_officer_type="文臣京官", chain="none")
        chain(w, [five, song, change], f"连接{title}沿置与任官变化。")
        if office_title == "西京粮料院":
            oe = entity(w, office_title, "机构", z, "本条明载西京粮料院使掌西京粮料院事。")
            ot = tp(w, oe, "宋初", "西京粮料机构", i, z, "俸禄发放机构", "建西京粮料院宋初节点。")
        else:
            ot = node(w, office_title, "宋初", "机构")[1]
        rel(w, ot, song, "编制隶属", i, z, f"{title}掌{office_title}事。", staff_type="官")
        w.commit()


def direct_grain_entry(i, office, officer, quota=None):
    z = F[i]["text"]; source = F[i]["fields"].get("职源", z); w = W(i)
    office_e = w.find_entity(office, "机构"); assert office_e
    start = w.find_timepoint(office_e, "北宋太平兴国五年正月二十八日"); assert start
    cite(w, "Timepoints", start, i, z, f"本条补证{office}分置、隶属与职掌。", note="职源、职掌")
    yuan = tp(w, office_e, "北宋元丰改制", "改隶太府寺",
              i, z, "俸禄发放机构", f"建{office}元丰改隶节点。", chain="none")
    existing_times = ["北宋太平兴国五年正月二十八日"]
    if office in ("马军粮料院", "步军粮料院"):
        existing_times += ["北宋太平兴国八年", "北宋端拱后"]
    chain_times(w, office_e, existing_times + ["北宋元丰改制"], f"连接{office}完整沿革。")
    temple_e = w.find_entity("太府寺", "机构") or entity(w, "太府寺", "机构", z, "粮料院条明确元丰后改隶太府寺。")
    temple_t = w.find_timepoint(temple_e, "北宋元丰改制") or tp(w, temple_e, "北宋元丰改制", "承接三粮料院",
                                                                  i, z, "财政机构", "建太府寺承接节点。")
    rel(w, temple_t, yuan, "上下级机构", i, z, f"元丰改制后{office}隶太府寺。")
    w.commit()

    oi = i + 1; z = F[oi]["text"]; source = F[oi]["fields"].get("职源", z); w = W(oi)
    officer_e = w.find_entity(officer, "官职"); assert officer_e
    ot = tp(w, officer_e, "北宋太平兴国五年正月", f"始置，监领{office}",
            oi, source, "粮料差遣", f"建{officer}始置节点。", chain="none")
    for field in ("品位", "编制"):
        if field in F[oi]["fields"]:
            cite(w, "Timepoints", ot, oi, F[oi]["fields"][field], f"补证{officer}{field}。", note=field)
    office_start = node(w, office, "北宋太平兴国五年正月二十八日", "机构")[1]
    rel(w, office_start, ot, "编制隶属", oi, z, f"{officer}监领{office}。", staff_quota=quota, staff_type="官")
    w.commit()


def entry421_426():
    direct_grain_entry(421, "诸司粮料院", "勾当诸司粮料院公事")
    direct_grain_entry(423, "马军粮料院", "勾当马军粮料院公事", 1)
    direct_grain_entry(425, "步军粮料院", "勾当步军粮料院公事", 1)


def entry427_428():
    i = 427; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    merged_e = entity(w, "马步军专勾司", "机构", z, "本条明载马步军专勾司为官署。")
    separate = []
    for title in ("马军专勾司", "步军专勾司"):
        eid = entity(w, title, "机构", h, f"淳化三年始置{title}。")
        start = tp(w, eid, "北宋淳化三年十一月", "始置", i, h, "军籍审核机构", f"建{title}始置节点。", chain="none")
        end = tp(w, eid, "北宋淳化五年", "两专勾司合并", i, h, "军籍审核机构", f"建{title}合并节点。", chain="none")
        chain(w, [start, end], f"连接{title}置并节点。")
        separate.append((title, start, end))
    merged_t = tp(w, merged_e, "北宋淳化五年", "马军、步军两专勾司合二为一",
                  i, h, "军籍审核机构", "建马步军专勾司合置节点。")
    for title, _, end in separate:
        rel(w, end, merged_t, "前后演变", i, h, f"{title}并为马步军专勾司。")
    officer_e = w.find_entity("勾当马步军专勾司公事", "官职"); assert officer_e
    officer_t = tp(w, officer_e, "北宋淳化五年", "随两专勾司合并始置",
                   i, comp, "军籍审核差遣", "据编制建合并后勾当官节点。")
    rel(w, merged_t, officer_t, "编制隶属", i, comp, "马步军专勾司置勾当官一人。", staff_quota=1, staff_type="官")
    w.commit()

    i = 428; z = F[i]["text"]; h = F[i]["fields"]["职源"]; w = W(i)
    main_t = node(w, "勾当马步军专勾司公事", "北宋淳化五年", "官职")[1]
    cite(w, "Timepoints", main_t, i, h, "补证合并后始置勾当马步军专勾司公事。", note="职源")
    for title, office in (("勾当马军专勾司公事", "马军专勾司"), ("勾当步军专勾司公事", "步军专勾司")):
        eid = entity(w, title, "官职", h, f"淳化三年始置{title}一名。")
        start = tp(w, eid, "北宋淳化三年十一月", "始置一名",
                   i, h, "军籍审核差遣", f"建{title}始置节点。", chain="none")
        end = tp(w, eid, "北宋淳化五年", "随两专勾司合并改置",
                 i, h, "军籍审核差遣", f"建{title}改置节点。", chain="none")
        chain(w, [start, end], f"连接{title}置并节点。")
        office_t = node(w, office, "北宋淳化三年十一月", "机构")[1]
        rel(w, office_t, start, "编制隶属", i, h, f"{office}置{title}一名。", staff_quota=1, staff_type="官")
        rel(w, end, main_t, "前后演变", i, h, f"{title}合并改为勾当马步军专勾司公事。")
    w.commit()


def entry429_430():
    i = 429; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; comp = F[i]["fields"]["编制"]; w = W(i)
    official_e = entity(w, "提举三司帐司、勾院磨勘司", "官职", z, "本条明载为差遣名。")
    official_start = tp(w, official_e, "北宋熙宁五年十一月十一日", "始置，覆校清查三司积年帐册",
                        i, h, "财政稽核差遣", "建提举官始置节点。", attr_officer_type="朝官", chain="none")
    official_end = tp(w, official_e, "北宋元丰三年", "废罢",
                      i, h, "财政稽核差遣", "建提举官废罢节点。", chain="none")
    chain(w, [official_start, official_end], "连接提举帐勾磨勘司置罢节点。")
    office_e = entity(w, "提举三司帐司、勾院磨勘司", "机构", comp, "原文明确提举司下设附属机构和吏额。")
    office_start = tp(w, office_e, "北宋熙宁五年十一月十一日", "始置提举司，统领三司帐册清查",
                      i, h, "财政稽核机构", "建提举司机构节点。", chain="none")
    office_end = tp(w, office_e, "北宋元丰三年", "废罢",
                    i, h, "财政稽核机构", "建提举司机构废罢节点。", chain="none")
    chain(w, [office_start, office_end], "连接提举司机构置罢节点。")
    parent = sansi_tp(w, i, "北宋熙宁五年十一月十一日", "始置帐司勾院磨勘提举司", h)
    sansi_tp(w, i, "北宋元丰三年", "罢帐司勾院磨勘提举司", h)
    rel(w, parent, office_start, "上下级机构", i, z, "提举司清查三司帐册。")
    rel(w, office_start, official_start, "编制隶属", i, comp, "提举司设提举官一员。", staff_quota=1, staff_type="官")
    for title in ("催驱司", "印司", "知杂司"):
        ce = w.find_entity(title, "机构") or entity(w, title, "机构", comp, f"提举司附属机构明确列{title}。")
        ct = w.find_timepoint(ce, "北宋熙宁五年十一月十一日") or tp(w, ce, "北宋熙宁五年十一月十一日",
                                                                      "提举司附属机构", i, comp, "财政稽核属司", f"建{title}属司节点。")
        rel(w, office_start, ct, "上下级机构", i, comp, f"提举司下设{title}。")
    cite(w, "Timepoints", office_start, i, comp, "补证提举司官额及吏额六百余人。", note="编制")
    w.commit()

    i = 430; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("提举三司帐司、勾院磨勘司", "官职"); assert eid
    title_tp = tp(w, eid, "北宋熙宁五年十一月二十二日", "确定上奏申陈文书衔名为提举三司帐勾磨勘司",
                  i, z, "财政稽核差遣", "建上奏衔名确定节点。", chain="none")
    start = w.find_timepoint(eid, "北宋熙宁五年十一月十一日"); end = w.find_timepoint(eid, "北宋元丰三年")
    chain(w, [start, title_tp, end], "插入熙宁五年十一月二十二日衔名确定节点。")
    w.commit()


def finalize_sansi_chain():
    w = W(429); eid = w.find_entity("三司", "机构"); assert eid
    times = ["唐天祐三年三月", "宋初", "北宋开宝五年十二月", "北宋开宝八年十一月十日",
             "北宋太平兴国五年正月二十八日", "北宋太平兴国五年十月",
             "北宋太平兴国八年三月七日", "北宋雍熙二年", "北宋雍熙三年八月",
             "北宋淳化二年", "北宋淳化三年七月一日", "北宋淳化四年五月",
             "北宋淳化四年五月二十一日", "北宋淳化四年十月", "北宋淳化五年十二月二十五日",
             "北宋至道二年闰七月", "北宋至道二年十月二十七日", "北宋至道三年十一月五日",
             "北宋咸平元年", "北宋咸平六年", "北宋咸平六年七月十六日",
             "北宋天禧三年正月", "北宋乾兴元年", "北宋天圣三年六月二十六日",
             "北宋庆历元年正月七日", "北宋皇祐三年五月二十三日", "北宋熙宁二年九月",
             "北宋熙宁五年十一月十一日", "北宋熙宁七年", "北宋元丰三年", "北宋元丰五年五月"]
    chain_times(w, eid, times, "按历史顺序插入本批三司河渠、推勘、粮料及提举司节点。")
    w.commit()


def main():
    seed_officers(); entry411_413(); entry414_416(); entry417()
    seed_grain_entities(); entry418(); entry419_420(); entry421_426()
    entry427_428(); entry429_430(); finalize_sansi_chain()


if __name__ == "__main__":
    main()
