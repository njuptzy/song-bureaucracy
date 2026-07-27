#!/usr/bin/env python3
"""提取 chapter2t4 第 113–120 条：太常礼院系统与详定编敕所。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")


def load(i):
    with sqlite3.connect(DICT_DB) as c:
        r = c.execute(
            "SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (i,)
        ).fetchone()
    return r[0], r[1], (r[2] or "") + "\n" + "\n".join(
        str(v) for k, v in json.loads(r[3] or "{}").items() if not k.startswith("_")
    )


FULL = {i: load(i) for i in range(113, 121)}


def q(i, s):
    assert s in FULL[i][2], f"#{i} 不含：{s}"
    return s


def writer(i):
    return EntryWriter(ENTRY_DB, FULL[i][0], FULL[i][1])


def cite(i):
    return f"《宋代官制辞典》第{FULL[i][1]}页“{FULL[i][0]}”条"


def ac(w, table, row_id, i, quote, decision, **kwargs):
    return w.citation(table, row_id, cite(i), quote, decision, **kwargs)


def entity(w, title, typ, i, quote, decision):
    return w.entity(title, typ, decision, quotation=quote)


def tp(w, entity_id, time, event, i, quote, category, decision, **kwargs):
    row_id = w.timepoint(
        entity_id, time, event, decision, quote, attr_category=category, **kwargs
    )
    ac(w, "Timepoints", row_id, i, quote, decision)
    return row_id


def rel(w, subject, obj, kind, i, quote, decision, **kwargs):
    row_id = w.relationship(subject, obj, kind, decision, quote, **kwargs)
    ac(w, "Relationships", row_id, i, quote, decision)
    return row_id


def node(w, title, time, typ=None):
    entity_id = w.find_entity(title, typ)
    assert entity_id, f"缺实体 {title}"
    row_id = w.find_timepoint(entity_id, time)
    assert row_id, f"{title} 缺 {time}"
    return entity_id, row_id


def rechain(w, ids, decision):
    for n, row_id in enumerate(ids):
        w.relink(
            row_id,
            decision,
            prev_id=ids[n - 1] if n else None,
            succ_id=ids[n + 1] if n + 1 < len(ids) else None,
        )


def entry113():
    i = 113
    qname = q(i, "官司名。名义上隶太常寺，其实专达于上")
    qtang = q(i, "唐开元十九年（731）四月四日始置礼院")
    qsong = q(i, "宋初沿置")
    qend = q(i, "元丰五年五月行新制，罢礼院")
    qduty = q(i, "宋前期侵太常寺职权，掌礼乐制度、仪式事")
    qstaff = q(i, "先后有判太常礼院、同判太常礼院、知太常礼院、同知太常礼院等差遣。判院与同知院共四人")
    qclerks = q(i, "吏人有礼院生等")
    qxining = q(i, "熙宁三年，诏以太常礼院为审官西院，其礼院归太常寺置局")
    w = writer(i)
    office = entity(w, "太常礼院", "机构", i, qname, "辞典明载为官司。")
    tang = tp(w, office, "唐开元十九年四月四日", "始置礼院", i, qtang, "官司名", "建唐代职源节点。")
    song = tp(w, office, "宋初", "沿置；名义上隶太常寺而专达于上", i, qsong, "官司名", "建宋初沿置节点。")
    ac(w, "Timepoints", song, i, qname, "补充宋初机构地位。", note="机构地位")
    early = tp(w, office, "宋前期", "掌礼乐制度、仪式事", i, qduty, "官司名", "建宋前期职掌节点。")
    xining = tp(w, office, "北宋熙宁三年", "礼院归太常寺置局", i, qxining, "官司名", "建熙宁三年机构调整节点。")
    end = tp(w, office, "北宋元丰五年五月", "行新制，罢礼院", i, qend, "官司名", "建元丰罢废节点。")

    temple = w.find_entity("太常寺", "机构") or entity(
        w, "太常寺", "机构", i, qname, "太常礼院隶属关系明确提及太常寺。"
    )
    temple_song = w.find_timepoint(temple, "宋初") or tp(
        w, temple, "宋初", "太常礼院名义上的上级机构", i, qname, "官司名", "建隶属关系的同期端点。"
    )
    temple_xining = w.find_timepoint(temple, "北宋熙宁三年") or tp(
        w, temple, "北宋熙宁三年", "礼院归太常寺置局", i, qxining, "官司名", "建熙宁调整的同期端点。"
    )
    rel(w, temple_song, song, "上下级机构", i, qname, "太常礼院名义上隶太常寺。")
    rel(w, temple_xining, xining, "上下级机构", i, qxining, "熙宁三年礼院归太常寺置局。")

    for title in ("判太常礼院", "同判太常礼院", "知太常礼院", "同知太常礼院"):
        post = w.find_entity(title, "官职") or entity(
            w, title, "官职", i, qstaff, f"太常礼院编制明列{title}。"
        )
        row = w.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id=? ORDER BY"
            " CASE WHEN prev_id IS NULL THEN 0 ELSE 1 END,id LIMIT 1", (post,)
        ).fetchone()
        if row:
            post_tp = row[0]
            ac(w, "Timepoints", post_tp, i, qstaff, "总条补充太常礼院所设差遣证据。", note="编制总述")
        else:
            post_tp = w.ensure_placeholder(post, "总条无精确设置时间，暂建待分条复用的承载节点。")
            ac(w, "Timepoints", post_tp, i, qstaff, "总条补充太常礼院所设差遣证据。", note="编制总述")
        rel(w, early, post_tp, "编制隶属", i, qstaff, f"太常礼院先后设{title}。", staff_type="官")
    ac(w, "Timepoints", early, i, qstaff, "补充判院与同知院合计四人的编制证据。", note="判院与同知院共四人，无法按单职拆分 quota")

    clerk = w.find_entity("礼院生", "官职") or entity(
        w, "礼院生", "官职", i, qclerks, "太常礼院吏额明确列礼院生。"
    )
    clerk_tp = w.find_timepoint(clerk, "宋前期") or tp(
        w, clerk, "宋前期", "太常礼院所设吏职", i, qclerks, "吏名", "建宋前期吏职承载节点。"
    )
    rel(w, early, clerk_tp, "编制隶属", i, qclerks, "太常礼院吏人有礼院生。", staff_type="吏")
    rechain(w, [tang, song, early, xining, end], "按唐代始置、宋初沿置、宋前期、熙宁调整、元丰罢废排序")
    rechain(w, [temple_song, temple_xining], "按宋初与熙宁三年排序")
    w.commit()


def entry114():
    i = 114
    qmain = q(i, "差遣名。掌领礼院有关仪注、典礼公事。以待制以上侍从官兼判")
    qchange = q(i, "康定元年十一月，礼院言：‘奉常礼乐之司，请改判院为判寺兼礼仪事。’……乙丑，改命李仲容兼礼仪事判太常礼院")
    w = writer(i)
    post = w.find_entity("判太常礼院", "官职") or entity(w, "判太常礼院", "官职", i, qmain, "辞典明载为差遣。")
    start = w.find_timepoint(post, "北宋天圣元年四月八日") or tp(
        w, post, "北宋天圣元年四月八日", "由知礼仪院事改置", i, qmain, "差遣名", "复用既有始置语境。"
    )
    ac(w, "Timepoints", start, i, qmain, "补充职掌与充任资格。", note="掌仪注、典礼；待制以上侍从官兼判")
    change = tp(w, post, "北宋康定元年十一月", "礼院请改判院为判寺兼礼仪事，后仍命判太常礼院", i, qchange, "差遣名", "建康定元年制度调整节点。")
    _, office = node(w, "太常礼院", "宋前期", "机构")
    rel(w, office, start, "编制隶属", i, qmain, "判太常礼院掌领礼院公事。", staff_type="官")
    rechain(w, [start, change], "按天圣改置、康定调整排序")
    w.commit()


def entry115():
    i = 115
    qmain = q(i, "差遣名。资稍浅者判礼院事，带“同”字。同判院多带馆职。同判院官四员，轮值礼院")
    qend = q(i, "天圣元年，改同判院为同知院，即博士也")
    qend2 = q(i, "天圣元年四月辛丑：“同判太常礼院官为同知院。”")
    w = writer(i)
    post = w.find_entity("同判太常礼院", "官职") or entity(w, "同判太常礼院", "官职", i, qmain, "辞典明载为差遣。")
    early = w.find_timepoint(post, "宋前期") or tp(w, post, "宋前期", "资稍浅者带同字判礼院，多带馆职；四员轮值", i, qmain, "差遣名", "建宋前期职掌与编制节点。")
    ac(w, "Timepoints", early, i, qmain, "补充员额与轮值制度。", note="四员")
    end = tp(w, post, "北宋天圣元年四月八日", "改为同知太常礼院", i, qend2, "差遣名", "建天圣改名终结节点。")
    successor = w.find_entity("同知太常礼院", "官职") or entity(w, "同知太常礼院", "官职", i, qend, "本条明确同判院的后继差遣。")
    successor_tp = w.find_timepoint(successor, "北宋天圣元年四月八日") or tp(w, successor, "北宋天圣元年四月八日", "由同判太常礼院改置", i, qend, "差遣名", "建后继差遣节点。")
    rel(w, end, successor_tp, "前后演变", i, qend2, "同判太常礼院改为同知太常礼院。")
    _, office = node(w, "太常礼院", "宋前期", "机构")
    rel(w, office, early, "编制隶属", i, qmain, "太常礼院置同判院四员轮值。", staff_quota=4, staff_type="官")
    rechain(w, [early, end], "按宋前期设置、天圣改名排序")
    w.commit()


def entry116():
    i = 116
    qmain = q(i, "差遣名。宋前期太常礼院，或置知院官、同知院官，轮值礼院，“点检本院典礼公事”")
    qrank = q(i, "位次于判礼院")
    qnames = q(i, "如止置一员，则称知礼院；若置数员，则称同知礼院")
    w = writer(i)
    post = w.find_entity("知太常礼院", "官职") or entity(w, "知太常礼院", "官职", i, qmain, "辞典明载为差遣。")
    early = w.find_timepoint(post, "宋前期") or tp(w, post, "宋前期", "轮值礼院，点检本院典礼公事，位次于判礼院", i, qmain, "差遣名", "建宋前期职掌节点。")
    ac(w, "Timepoints", early, i, qrank, "补充位次。", note="位次于判礼院")
    ac(w, "Timepoints", early, i, qnames, "补充一员称知院、数员称同知院的配置规则。", note="员额称谓规则")
    _, office = node(w, "太常礼院", "宋前期", "机构")
    rel(w, office, early, "编制隶属", i, qmain, "太常礼院或置知院官轮值。", staff_type="官")
    w.commit()


def entry117():
    i = 117
    qchange = q(i, "天圣元年（1023）四月八日罢礼仪院，以知礼仪院官判太常礼院，即以原同判太常礼院官改为同知礼院官")
    qstaff = q(i, "同知院四员，与知院轮值礼院，点检本院典礼公事")
    qlater = q(i, "同知院四员，日更直本院，其后或别领职事，因循废直，请如故事")
    w = writer(i)
    post = w.find_entity("同知太常礼院", "官职") or entity(w, "同知太常礼院", "官职", i, qchange, "辞典明载为差遣。")
    start = w.find_timepoint(post, "北宋天圣元年四月八日") or tp(w, post, "北宋天圣元年四月八日", "由同判太常礼院改置", i, qchange, "差遣名", "建天圣改置节点。")
    ac(w, "Timepoints", start, i, qchange, "补充由原同判太常礼院官改置的证据。", note="沿革")
    ac(w, "Timepoints", start, i, qstaff, "补充四员轮值与职掌。", note="四员，与知院轮值")
    later = tp(w, post, "北宋天圣元年后", "或别领职事，因循废直", i, qlater, "差遣名", "建天圣以后轮值制度变化节点。")
    _, office = node(w, "太常礼院", "宋前期", "机构")
    rel(w, office, start, "编制隶属", i, qstaff, "太常礼院设同知院四员轮值。", staff_quota=4, staff_type="官")
    _, source_tp = node(w, "同判太常礼院", "北宋天圣元年四月八日", "官职")
    rel(w, source_tp, start, "前后演变", i, qchange, "原同判太常礼院官改为同知礼院官。")
    rechain(w, [start, later], "按天圣改置及其后废直排序")
    w.commit()


def entry118():
    i = 118
    qstart = q(i, "差遣官，嘉祐六年（1061）二月始置，编修《太常因革礼》")
    qend = q(i, "治平二年九月成书")
    w = writer(i)
    post = entity(w, "太常礼院编纂礼书", "官职", i, qstart, "辞典明载为差遣官。")
    start = tp(w, post, "北宋嘉祐六年二月", "始置，编修《太常因革礼》", i, qstart, "差遣官", "建始置节点。")
    end = tp(w, post, "北宋治平二年九月", "《太常因革礼》成书", i, qend, "差遣官", "建成书节点。")
    office_en, _ = node(w, "太常礼院", "宋前期", "机构")
    office_start = tp(w, office_en, "北宋嘉祐六年二月", "始置太常礼院编纂礼书", i, qstart, "官司名", "建差遣设置的同期机构端点。", chain="none")
    rel(w, office_start, start, "编制隶属", i, qstart, "太常礼院置编纂礼书差遣。", staff_type="官")
    office_order = [w.find_timepoint(office_en, t) for t in ("唐开元十九年四月四日", "宋初", "宋前期", "北宋嘉祐六年二月", "北宋熙宁三年", "北宋元丰五年五月")]
    assert all(office_order)
    rechain(w, office_order, "插入嘉祐六年编纂礼书节点并按历史顺序重排")
    rechain(w, [start, end], "按始置与成书排序")
    w.commit()


def entry119():
    i = 119
    qtang = q(i, "唐太常寺礼院已置礼生")
    qsong = q(i, "宋沿置")
    qduty = q(i, "典礼、祠祭时，协助赞导、安置等具体事务")
    w = writer(i)
    post = w.find_entity("礼院生", "官职") or entity(w, "礼院生", "官职", i, qsong, "辞典明载为吏名。")
    tang = tp(w, post, "唐代", "太常寺礼院已置礼生", i, qtang, "吏名", "建唐代职源节点。", chain="none")
    song = tp(w, post, "宋初", "沿置，典礼祠祭时协助赞导、安置", i, qsong, "吏名", "建宋初沿置节点。", chain="none")
    ac(w, "Timepoints", song, i, qduty, "补充职掌。", note="职掌")
    _, office = node(w, "太常礼院", "宋初", "机构")
    rel(w, office, song, "编制隶属", i, qsong, "宋沿置礼院生。", staff_type="吏")
    existing = w.find_timepoint(post, "宋前期")
    assert existing
    rechain(w, [tang, song, existing], "按唐代职源、宋初沿置、宋前期配置排序")
    w.commit()


def entry120():
    i = 120
    qmain = q(i, "编修法令机构名。仁宗天圣间编敕，“始有详定编敕所”，由宰执官提举")
    w = writer(i)
    office = entity(w, "详定编敕所", "机构", i, qmain, "辞典明载为编修法令机构。")
    tp(w, office, "北宋仁宗天圣间", "始置，由宰执官提举，编修法令", i, qmain, "编修法令机构名", "建天圣间始置与主管节点。")
    w.commit()


def main():
    entry113()
    entry114()
    entry115()
    entry116()
    entry117()
    entry118()
    entry119()
    entry120()


if __name__ == "__main__":
    main()
