#!/usr/bin/env python3
"""提取 chapter2t4 第431–450条：帐司、宣徽院与群牧司前段。"""
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
    return {"title": row[0], "page": row[1], "text": row[2] or "",
            "fields": json.loads(row[3] or "{}")}


F = {i: load(i) for i in range(431, 451)}


def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])
def C(i): return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'


def entity(w, title, type_, quotation, decision):
    return w.entity(title, type_, decision, quotation=quotation)


def cite(w, table, rid, i, quotation, decision, **kw):
    return w.citation(table, rid, C(i), quotation, decision, **kw)


def tp(w, eid, time, event, i, quotation, category, decision, citation_kw=None, **kw):
    tid = w.timepoint(eid, time, event, decision, quotation, attr_category=category, **kw)
    cite(w, "Timepoints", tid, i, quotation, decision, **(citation_kw or {}))
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


def entry431_433():
    i = 431; z = F[i]["text"]; w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "本条明载为与提举官并置的差遣。")
    tid = tp(w, eid, "北宋熙宁五年十一月十一日", "始置，两提举官中资历稍浅者带‘同’字",
             i, z, "财政稽核差遣", "建同提举官始置节点。", attr_officer_type="朝官")
    office = node(w, "提举三司帐司、勾院磨勘司", "北宋熙宁五年十一月十一日", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "提举官并置二人时资浅者为同提举。", staff_quota=1, staff_type="官")
    w.commit()

    i = 432; z = F[i]["text"]; a = F[i]["fields"]["简称"]; w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "本条明载为资浅者补提举官缺的权发遣差遣。")
    tid = tp(w, eid, "北宋前期（未载具体年月）", "三司帐司勾院磨勘司缺提举官时，资浅者补缺带权发遣提举",
             i, z, "财政稽核差遣", "建权发遣提举官无确年节点。")
    cite(w, "Timepoints", tid, i, a, "补证该差遣可简称提举三司帐司。", note="简称")
    office = node(w, "提举三司帐司、勾院磨勘司", "北宋熙宁五年十一月十一日", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "该差遣补三司帐司勾院磨勘司提举官缺。", staff_type="官")
    w.commit()

    i = 433; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; d = F[i]["fields"]["职掌"]; w = W(i)
    eid = entity(w, F[i]["title"], "机构", z, "本条明载三司帐司为官署。")
    start = tp(w, eid, "北宋熙宁五年十一月", "始置，追查清理诸州军上送三司的陈年旧帐",
               i, h, "财政稽核机构", "建三司帐司始置节点。", chain="none")
    cite(w, "Timepoints", start, i, d, "补证三司帐司职掌。", note="职掌")
    end = tp(w, eid, "北宋元丰三年", "废罢", i, h, "财政稽核机构", "建三司帐司废罢节点。", chain="none")
    chain(w, [start, end], "连接三司帐司置罢节点。")
    w.commit()


def entry434_441():
    i = 434; z = F[i]["text"]; h = F[i]["fields"]["职源"]; duty = F[i]["fields"]["职掌"]; comp = F[i]["fields"]["编制"]; w = W(i)
    eid = entity(w, F[i]["title"], "机构", z, "本条明载金耀门书库为隶三司的职局。")
    start = tp(w, eid, "北宋景德三年冬", "创置，掌贮存三司历年文案",
               i, h, "档案机构", "建金耀门书库创置节点。")
    cite(w, "Timepoints", start, i, duty, "补证金耀门书库职掌。", note="职掌")
    sansi = w.find_entity("三司", "机构"); assert sansi
    parent = tp(w, sansi, "北宋景德三年冬", "创置金耀门书库", i, h, "财政机构", "建三司创置书库节点。", chain="none")
    before = w.find_timepoint(sansi, "北宋咸平六年七月十六日"); after = w.find_timepoint(sansi, "北宋天禧三年正月")
    w.relink(before, "将景德三年节点插入三司时间链。", succ_id=parent)
    w.relink(parent, "将景德三年节点插入三司时间链。", prev_id=before, succ_id=after)
    w.relink(after, "将景德三年节点插入三司时间链。", prev_id=parent)
    rel(w, parent, start, "上下级机构", i, z, "金耀门书库明载隶三司。")
    w.commit()

    i = 435; z = F[i]["text"]; w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "本条明载监金耀门书库为差遣。")
    tid = tp(w, eid, "北宋景德三年冬", "随书库设置，监领本库官物等公事",
             i, z, "档案差遣", "建监金耀门书库设置节点。", attr_officer_type="三班院使臣")
    office = node(w, "金耀门书库", "北宋景德三年冬", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "金耀门书库置监官监领本库公事。", staff_quota=1, staff_type="官")
    w.commit()

    for i, category, quota in ((436, "三司衙职", None), (437, "三司衙职", 1500),
                               (438, "三司吏职", None), (439, "三司吏职", 3),
                               (440, "三司吏职", 3)):
        z = F[i]["text"]; w = W(i); eid = entity(w, F[i]["title"], "官职", z, f"第{i}条独立定义{F[i]['title']}为{category}。")
        if i == 437:
            time, event = "北宋熙宁七年三月九日", "大将、军将合定一千五百人为额"
        elif i == 440:
            time, event = "宋初", "三司三部各置勾覆官一人"
        else:
            time, event = "北宋（未载具体年月）", z.split("。")[0]
        tid = tp(w, eid, time, event, i, z, category, f"建{F[i]['title']}制度节点。")
        sansi = w.find_entity("三司", "机构"); assert sansi
        parent_time = "北宋熙宁七年" if i == 437 else "宋初"
        parent = w.find_timepoint(sansi, parent_time); assert parent
        staff_quota = quota
        if i == 437: staff_quota = None  # 一千五百人为大将、军将合额，不误写为大将单项员额
        if i == 439: staff_quota = 3  # 三部各一人
        if i == 440: staff_quota = 3  # 三部各一人
        rel(w, parent, tid, "编制隶属", i, z, f"{F[i]['title']}为三司衙职或吏职。", staff_quota=staff_quota, staff_type="吏" if i >= 438 else "衙职")
        w.commit()

    i = 441; z = F[i]["text"]; w = W(i)
    eid = entity(w, F[i]["title"], "机构", z, "本条明载三司会计司为临时官署。")
    start = tp(w, eid, "北宋熙宁七年十月十六日", "始置，考核审查三司及诸路财赋帐目",
               i, z, "临时财政稽核机构", "建三司会计司始置节点。", chain="none")
    end = tp(w, eid, "北宋熙宁八年九月十一日", "废罢", i, z, "临时财政稽核机构", "建三司会计司废罢节点。", chain="none")
    chain(w, [start, end], "连接三司会计司置罢节点。")
    parent = node(w, "中书门下", "宋前期", "机构")[1]
    rel(w, parent, start, "上下级机构", i, z, "三司会计司明载归隶中书门下。")
    w.commit()


def entry442_446():
    i = 442; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; w = W(i)
    eid = w.find_entity("宣徽院", "机构") or entity(w, "宣徽院", "机构", z, "本条明载宣徽院为内廷官署。")
    tang = tp(w, eid, "唐大历年间", "始见宣徽之称", i, h, "内廷机构", "建宣徽之称的宋前源流节点。", chain="none")
    song = w.find_timepoint(eid, "宋初"); assert song
    cite(w, "Timepoints", song, i, h, "补证宣徽院宋初沿置。", note="沿革")
    end = tp(w, eid, "北宋元丰四年十一月二十一日", "废罢", i, h, "内廷机构", "建宣徽院废罢节点。", chain="none")
    chain(w, [tang, song, end], "连接宣徽院源流、沿置和废罢节点。")
    w.commit()

    i = 443; z = F[i]["text"]; h = F[i]["fields"]["职源"]; duty = F[i]["fields"]["职掌"]; w = W(i)
    eid = entity(w, F[i]["title"], "机构", z, "本条明载宣徽南院为宣徽院分院。")
    tang = tp(w, eid, "唐天祐元年", "已有宣徽南院、北院之分", i, h, "内廷机构", "建宣徽南院宋前源流节点。", chain="none")
    song = tp(w, eid, "宋前期", "与北院分厅办事，实为一院，资望稍高于北院", i, duty, "内廷机构", "建宣徽南院宋代职掌节点。", chain="none")
    chain(w, [tang, song], "连接宣徽南院唐宋节点。")
    parent = node(w, "宣徽院", "宋初", "机构")[1]
    rel(w, parent, song, "上下级机构", i, z, "宣徽南院明载为宣徽院分院。")
    w.commit()

    i = 444; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; duty = F[i]["fields"]["职掌"]; w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "本条明载宣徽南院使为职事官或加官。")
    tids = [tp(w, eid, "唐咸通九年或十年", "已见宣徽使之称", i, h, "内廷差遣", "建宋前源流节点。", chain="none"),
            tp(w, eid, "宋初", "沿置宣徽南院使", i, h, "内廷差遣", "建宋初沿置节点。", chain="none"),
            tp(w, eid, "北宋元丰六年三月", "不置使", i, h, "内廷差遣", "建元丰废罢节点。", chain="none"),
            tp(w, eid, "北宋元祐三年十月", "复置", i, h, "内廷差遣", "建元祐复置节点。", chain="none"),
            tp(w, eid, "北宋绍圣三年四月", "复罢", i, h, "内廷差遣", "建绍圣复罢节点。", chain="none")]
    chain(w, tids, "连接宣徽南院使置罢时间链。")
    office = node(w, "宣徽南院", "宋前期", "机构")[1]
    rel(w, office, tids[1], "编制隶属", i, duty, "南院使与北院使分领宣徽南、北院职掌。", staff_quota=1, staff_type="官")
    w.commit()

    i = 445; z = F[i]["text"]; duty = F[i]["fields"]["职源、职掌"]; w = W(i)
    eid = w.find_entity(F[i]["title"], "机构") or entity(w, F[i]["title"], "机构", z, "本条明载宣徽北院为宣徽院分院。")
    tid = w.find_timepoint(eid, "北宋淳化四年八月十八日"); assert tid
    cite(w, "Timepoints", tid, i, duty, "以与宣徽南院同职掌的交叉引用补证北院。", note="职源、职掌")
    parent = node(w, "宣徽院", "宋初", "机构")[1]
    rel(w, parent, tid, "上下级机构", i, z, "宣徽北院明载为宣徽院分院。")
    w.commit()

    i = 446; z = F[i]["text"]; cross = F[i]["fields"]["职源、沿革、职掌、品位"]; w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "本条明载宣徽北院使为职事官或加官。")
    times_events = [("唐咸通九年或十年", "已见宣徽使之称"), ("宋初", "沿置宣徽北院使"),
                    ("北宋元丰六年三月", "不置使"), ("北宋元祐三年十月", "复置"),
                    ("北宋绍圣三年四月", "复罢")]
    tids = [tp(w, eid, t, e, i, cross, "内廷差遣", "据‘与宣徽南院使同’的交叉引用建对应节点。", chain="none") for t, e in times_events]
    chain(w, tids, "连接宣徽北院使置罢时间链。")
    office = node(w, "宣徽北院", "北宋淳化四年八月十八日", "机构")[1]
    rel(w, office, tids[1], "编制隶属", i, cross, "据与宣徽南院使相同的交叉引用，北院使分领宣徽北院职掌。", staff_quota=1, staff_type="官")
    w.commit()


def entry447_450():
    i = 447; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; duty = F[i]["fields"]["职掌"]; w = W(i)
    eid = entity(w, F[i]["title"], "机构", z, "本条明载群牧司为官司。")
    start = tp(w, eid, "北宋咸平三年九月十六日", "始置，总领内外国马之政",
               i, h, "马政机构", "建群牧司始置节点。", chain="none",
               citation_kw={"note": "第449条另记制置群牧使于同月六日始置，早于本条群牧司始置日十日。", "conflict_flag": 1})
    cite(w, "Timepoints", start, i, duty, "补证群牧司职掌。", note="职掌")
    end = tp(w, eid, "北宋元丰五年五月一日", "废罢，职事归太仆寺", i, h, "马政机构", "建群牧司废罢节点。", chain="none")
    chain(w, [start, end], "连接群牧司置罢节点。")
    taipusi = w.find_entity("太仆寺", "机构"); assert taipusi
    successor = tp(w, taipusi, "北宋元丰五年五月一日", "承接群牧司职事", i, h, "马政机构", "建太仆寺承接群牧司职事节点。")
    rel(w, end, successor, "前后演变", i, h, "群牧司罢后职事归太仆寺。")
    w.commit()

    i = 448; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; duty = F[i]["fields"]["职掌"]; w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "本条明载群牧制置使为差遣。")
    te = [("北宋景德四年八月十二日", "始置"), ("北宋明道二年五月十二日", "废罢"),
          ("北宋景祐二年十月十三日", "复置"), ("北宋宝元二年五月二十三日", "又罢"),
          ("北宋宝元二年以后（未载具体年月）", "复置"), ("北宋元丰五年", "行新制罢")]
    tids = [tp(w, eid, t, e, i, h, "马政差遣", f"建群牧制置使{e}节点。", chain="none") for t, e in te]
    chain(w, tids, "连接群牧制置使置罢时间链。")
    office = node(w, "群牧司", "北宋咸平三年九月十六日", "机构")[1]
    rel(w, office, tids[0], "编制隶属", i, duty, "群牧制置使为群牧司最高长官。", staff_quota=1, staff_type="官")
    w.commit()

    i = 449; z = F[i]["text"]; h = F[i]["fields"]["职源与沿革"]; duty = F[i]["fields"]["职掌"]; w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "本条明载制置群牧使为差遣。")
    start = tp(w, eid, "北宋咸平三年九月六日", "始置，为群牧司最高长官",
               i, h, "马政差遣", "建制置群牧使始置节点。", chain="none",
               citation_kw={"note": "第447条另记群牧司于同月十六日始置，晚于本条长官始置日十日。", "conflict_flag": 1})
    end = tp(w, eid, "北宋景德二年七月三日", "去制置之号，改称群牧使",
             i, h, "马政差遣", "建制置群牧使改称节点。", chain="none")
    chain(w, [start, end], "连接制置群牧使始置与改称节点。")
    successor_e = entity(w, "群牧使", "官职", h, "原文明载制置群牧使改称群牧使。")
    successor_t = tp(w, successor_e, "北宋景德二年七月三日", "由制置群牧使改称",
                     i, h, "马政差遣", "建群牧使改称承接节点。")
    rel(w, end, successor_t, "前后演变", i, h, "制置群牧使去制置之号改称群牧使。")
    office = node(w, "群牧司", "北宋咸平三年九月十六日", "机构")[1]
    rel(w, office, start, "编制隶属", i, duty, "制置群牧使为群牧司最高长官。", staff_quota=1, staff_type="官")
    w.commit()

    i = 450; z = F[i]["text"]; w = W(i)
    eid = entity(w, F[i]["title"], "官职", z, "本条明载权群牧制置使为差遣。")
    tid = tp(w, eid, "北宋治平二年六月", "以枢密院副使陈升之差充，带权字，下正使一等",
             i, z, "马政差遣", "建权群牧制置使设置节点。", attr_officer_type="枢密院副使")
    office = node(w, "群牧司", "北宋咸平三年九月十六日", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "权群牧制置使为群牧司长官差遣。", staff_quota=1, staff_type="官")
    w.commit()


def main():
    entry431_433()
    entry434_441()
    entry442_446()
    entry447_450()


if __name__ == "__main__":
    main()
