#!/usr/bin/env python3
"""提取 chapter2t4 第301–320条：三司长官层级、三部及三部使副使。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (i,)
        ).fetchone()
    assert row, i
    fields = json.loads(row[3] or "{}")
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": fields,
        "all": "\n".join(
            [row[2] or ""]
            + [str(v) for k, v in fields.items() if not k.startswith("_")]
        ),
    }


F = {i: load(i) for i in range(301, 321)}


def q(i, text):
    assert text in F[i]["all"], f"#{i} 不含：{text}"
    return text


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def C(i):
    return f"《宋代官制辞典》第{F[i]['page']}页“{F[i]['title']}”条"


def cite(w, table, rid, i, quotation, decision, **kw):
    return w.citation(table, rid, C(i), quotation, decision, **kw)


def entity(w, title, type_, quotation, decision):
    return w.entity(title, type_, decision, quotation=quotation)


def tp(w, eid, time, event, i, quotation, category, decision, **kw):
    tid = w.timepoint(
        eid,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        **kw,
    )
    cite(w, "Timepoints", tid, i, quotation, decision)
    return tid


def rel(w, source, target, kind, i, quotation, decision, **kw):
    rid = w.relationship(source, target, kind, decision, quotation, **kw)
    cite(w, "Relationships", rid, i, quotation, decision)
    return rid


def node(w, title, time, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, f"缺实体：{title}"
    tid = w.find_timepoint(eid, time)
    assert tid, f"{title} 缺时间点：{time}"
    return eid, tid


def first_node(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, f"缺实体：{title}"
    row = w.conn.execute(
        "SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (eid,)
    ).fetchone()
    assert row
    return eid, row[0]


def chain(w, tids, decision):
    assert len(tids) == len(set(tids)), f"时间链含重复节点：{tids}"
    for pos, tid in enumerate(tids):
        w.relink(
            tid,
            decision,
            prev_id=tids[pos - 1] if pos else None,
            succ_id=tids[pos + 1] if pos + 1 < len(tids) else None,
        )


def repair_entry156_trailing_newlines():
    """清除第156条旧脚本把拼接尾换行写入两条 Citation 的遗留。"""
    i = 156
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (i,)
        ).fetchone()
    fields = json.loads(row[3] or "{}")
    source = "\n".join(
        [row[2] or ""] + [str(v) for k, v in fields.items() if not k.startswith("_")]
    )
    citation = f"《宋代官制辞典》第{row[1]}页“{row[0]}”条"
    w = EntryWriter(ENTRY_DB, row[0], row[1])
    rows = w.conn.execute(
        "SELECT id,quotation FROM Citations WHERE citation=? AND quotation LIKE ?",
        (citation, "%\n"),
    ).fetchall()
    for cid, quotation in rows:
        fixed = quotation.rstrip()
        assert fixed in source
        w.conn.execute("UPDATE Citations SET quotation=? WHERE id=?", (fixed, cid))
        w._br(
            "Citations",
            cid,
            "清除旧提取脚本拼接全文时误带的尾随换行；正文内容及出处不变。",
        )
    w.commit()


def entry301():
    i = 301
    q_start = q(i, "五代后晋开运二年(945)正月已见置判留司三司公事(《旧五代史·晋书》9《少帝纪》3)。")
    q_duty = q(i, "领留守司三司，掌理诸路钱谷事。")
    w = W(i)
    eid = entity(w, "判留守司三司公事", "官职", F[i]["text"], "辞典明载为临时差遣。")
    tid = tp(w, eid, "五代后晋开运二年正月", "已见置，领留守司三司", i, q_start,
             "临时差遣", "建五代始见节点。")
    cite(w, "Timepoints", tid, i, q_duty, "补充掌理诸路钱谷职掌。", note="职掌")
    office = node(w, "留守司三司", "宋代（未载具体年月）", "机构")[1]
    rel(w, office, tid, "编制隶属", i, q_duty, "判留守司三司公事领留守司三司。", staff_type="官")
    w.commit()


def entry302():
    i = 302
    z = F[i]["text"]
    w = W(i)
    office_e = w.find_entity("行在三司", "机构")
    assert office_e
    office_t = tp(w, office_e, "北宋太平兴国四年四月", "太宗亲征北汉时置，驾回则罢", i,
                  z, "临时机构", "补建行在三司的太平兴国四年设置实例。", chain="none")
    generic = w.find_timepoint(office_e, "宋代（未载具体年月）")
    if generic:
        chain(w, [office_t, generic], "把太平兴国四年实例接在行在三司概括节点之前。")
    eid = entity(w, "判行在三司公事", "官职", z, "辞典明载为临时差遣。")
    tid = tp(w, eid, "北宋太平兴国四年四月", "置以领行在三司公事，驾回则罢", i, z,
             "临时差遣", "建判行在三司公事置罢节点。")
    rel(w, office_t, tid, "编制隶属", i, z, "判行在三司公事领行在三司。", staff_type="官")
    w.commit()


def entry303():
    i = 303
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "权三司使公事", "官职", z, "辞典明载为三司使缺时所置差遣。")
    tid = tp(w, eid, "北宋咸平六年后", "三司使缺时置代，位于三司使之下", i, z,
             "财政长官", "建咸平六年后三司长官代理制度节点。")
    tri = node(w, "三司", "北宋咸平六年", "机构")[1]
    rel(w, tri, tid, "编制隶属", i, z, "权三司使公事为三司使缺时的代理长官。", staff_type="官")
    w.commit()


def entry304():
    i = 304
    z = F[i]["text"]
    assert z and not F[i]["fields"].get("__status__"), "权三司使切分尚未修复"
    q_start = q(i, "仁宗庆历三年（1043），叶清臣以知永兴军、翰林学士再入三司，为权三司使。")
    q_rank = q(i, "从此，三司长官分为三司使、权三司使公事、权三司使三等。权三司使位在翰林学士之下（《宋朝事实类苑》卷27《三司使班》）。")
    w = W(i)
    eid = entity(w, "权三司使", "官职", z, "切分修复后的正文明确其为差遣官。")
    tid = tp(w, eid, "北宋庆历三年", "始置，三司长官自此分为三等", i, q_start,
             "财政长官", "建庆历三年始置节点。")
    cite(w, "Timepoints", tid, i, q_rank, "补充三司长官分等及权三司使位次。", note="品位")
    tri = node(w, "三司", "北宋咸平六年", "机构")[1]
    rel(w, tri, tid, "编制隶属", i, q_start, "权三司使为三司长官之一。", staff_type="官")
    w.commit()


def entry305():
    i = 305
    z = F[i]["text"]
    q_start = q(i, "天圣四年（1026）十二月五日始置。")
    w = W(i)
    eid = entity(w, "权发遣三司使公事", "官职", z, "辞典明载为暂时代理差遣。")
    tid = tp(w, eid, "北宋天圣四年十二月五日", "始置；三司使及权三司使公事俱缺时代理", i,
             z, "临时差遣", "建天圣四年始置节点。")
    cite(w, "Timepoints", tid, i, q_start, "精确补证始置日期。")
    tri = node(w, "三司", "北宋咸平六年", "机构")[1]
    rel(w, tri, tid, "编制隶属", i, z, "权发遣三司使公事为三司长官缺员时的下一级代理。", staff_type="官")
    w.commit()


def entry306():
    i = 306
    z = F[i]["all"]
    q_hist = q(i, "①五代后唐同光末（926），已见置三司副使（《旧五代史·张格传》）。②北宋于太宗太平兴国元年（976）十二月二十五日始置（《长编》卷17）。③太平兴国七年（982）二月七日罢三司副使不置（《宋史·职官志》2《三司使》）。")
    q_duty = q(i, "为三司使副贰，即三司副长官。")
    q_quota = q(i, "一人（参《宋史·李符传》）。")
    w = W(i)
    eid = entity(w, "三司副使", "官职", F[i]["text"], "辞典明载为差遣官。")
    a = tp(w, eid, "五代后唐同光末", "已见置", i, q_hist, "财政副长官", "建五代始见节点。", chain="none")
    b = tp(w, eid, "北宋太平兴国元年十二月二十五日", "始置，为三司使副贰", i, q_hist,
           "财政副长官", "建北宋始置节点。", chain="none")
    c = tp(w, eid, "北宋太平兴国七年二月七日", "罢，不置", i, q_hist,
           "财政副长官", "建北宋罢置节点。", chain="none")
    chain(w, [a, b, c], "连接三司副使始见、北宋始置与罢置。")
    cite(w, "Timepoints", b, i, q_duty, "补充副长官职掌。", note="职掌")
    tri = node(w, "三司", "宋初", "机构")[1]
    rel(w, tri, b, "编制隶属", i, q_quota, "三司置副使一人。", staff_quota=1, staff_type="官")
    w.commit()


def entry307():
    i = 307
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "行在三司副使", "官职", z, "辞典明载为临时差遣官。")
    tid = tp(w, eid, "宋代（未载具体年月）", "佐行在三司使备办车驾所需物事", i, z,
             "临时差遣", "建行在三司副使概括节点。")
    office = node(w, "行在三司", "宋代（未载具体年月）", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "行在三司副使为行在三司属官。", staff_type="官")
    w.commit()


def entry309():
    i = 309
    q_comp = q(i, "①官额：其一，宋初至太平兴国八年，不设部副使，但置判官、推官，咸平六年后，置副使一人。其二，自为主司时，设盐铁使一人，其后不置。②分案：初分五，后为八或七案。③吏人：156人（景德元年定）。④子司：盐铁勾院、开拆司、凭由司、理欠司、磨勘司。")
    q_duty = q(i, "掌全国山川湖泊的出产，及关市、河渠、军器等事，以助邦国之用（《宋史·职官志》2《三司使》）。")
    w = W(i)
    eid = w.find_entity("盐铁", "机构")
    assert eid
    song = tp(w, eid, "宋初", "为三司分部，置判官、推官，不设部副使", i, q_comp,
              "财政机构", "补建盐铁宋初分部节点。", chain="none")
    old = [node(w, "盐铁", t, "机构")[1] for t in (
        "北宋太平兴国八年三月七日", "北宋淳化四年五月二十一日",
        "北宋淳化五年十二月二十四日", "北宋咸平六年")]
    chain(w, [song, *old], "把盐铁宋初分部节点接到既有分合时间链之前。")
    cite(w, "Timepoints", song, i, q_duty, "补充盐铁职掌。", note="职掌")
    cite(w, "Timepoints", old[-1], i, q_comp, "补充咸平六年后副使一人及盐铁编制。", note="编制")
    w.commit()


def entry310():
    i = 310
    q_hist = q(i, "盐铁、度支、户部作为相对独立的财政机构，形成于唐德宗贞元年间（《新唐书》卷55《食货志》5）。北宋始于太平兴国八年三月三司分三部。其作为三司之一部，则始于宋初。")
    q_comp = q(i, "① 官额：自立为主司时，设度支使、副使（不常置），隶三司为分部时，设副使，其余设判官、推官、主簿（罕置）等。② 分案：初分十四案，后为八案（《宋会要·食货》56之9、《宋史·职官志》2）。③ 吏人：182人（景德元年后）。④ 子司：度支勾院、开拆司、凭由司、理欠司、磨勘司。")
    q_duty = q(i, "掌诸路财赋上送之总数，每年计量出入，以规划朝廷之用（《宋史·职官志》2）。")
    w = W(i)
    eid = w.find_entity("度支", "机构")
    assert eid
    tang = tp(w, eid, "唐德宗贞元年间", "形成相对独立财政机构", i, q_hist,
              "财政机构", "补建度支唐代源流节点。", chain="none")
    song = tp(w, eid, "宋初", "作为三司分部", i, q_hist, "财政机构",
              "补建度支宋初分部节点。", chain="none")
    old = [node(w, "度支", t, "机构")[1] for t in (
        "北宋太平兴国八年三月七日", "北宋淳化四年五月二十一日",
        "北宋淳化五年十二月二十四日", "北宋咸平六年")]
    chain(w, [tang, song, *old], "把度支唐代源流、宋初分部节点接入既有分合链。")
    cite(w, "Timepoints", song, i, q_comp, "补充度支官额、分案、吏额与子司。", note="编制")
    cite(w, "Timepoints", song, i, q_duty, "补充度支职掌。", note="职掌")
    w.commit()


def entry311():
    i = 311
    q_hist = q(i, "唐贞元四年（788），作为三司之一的“户部”已建立（《旧唐书·德宗纪》、《新唐书·食货志》5）。参“三司”与“三部”。")
    q_comp = q(i, "①官额：自为主司时，设户部使，或副使（不常置），隶三司为分部时，设副使。其余设判官、推官、巡官（不常置）、主簿（罕置）等。②分案：宋初为四案，后为八案、五案，不定。③吏人：217人（景德元年）。④子司：户部勾院、开拆司、凭由司、理欠司、磨勘司。")
    q_duty = q(i, "掌全国户口、税赋、簿籍。酒类专卖、百工制作、官服军服储备等事（《宋史·职官志》2）。")
    w = W(i)
    eid = w.find_entity("户部", "机构")
    assert eid
    tang = tp(w, eid, "唐贞元四年", "作为三司之一已经建立", i, q_hist,
              "财政机构", "补建户部唐代源流节点。", chain="none")
    song = tp(w, eid, "宋初", "作为三司分部", i, q_hist, "财政机构",
              "补建户部宋初分部节点。", chain="none")
    old = [node(w, "户部", t, "机构")[1] for t in (
        "北宋太平兴国八年三月七日", "北宋淳化四年五月二十一日",
        "北宋淳化五年十二月二十四日", "北宋咸平六年", "北宋元丰五年五月")]
    chain(w, [tang, song, *old], "把户部唐代源流、宋初分部节点接入既有分合链。")
    cite(w, "Timepoints", song, i, q_comp, "补充户部官额、分案、吏额与子司。", note="编制")
    cite(w, "Timepoints", song, i, q_duty, "补充户部职掌。", note="职掌")
    w.commit()


def entry308():
    i = 308
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "三部", "机构", z, "原文明载为盐铁、度支、户部三司合称。")
    stages = (
        ("宋初至北宋太平兴国八年三月", "三司分部，均不置使"),
        ("北宋太平兴国八年至淳化四年十月", "三部分治，各自为主司"),
        ("北宋淳化五年十二月至咸平六年六月", "三部分治，各自为主司"),
        ("北宋咸平六年六月至元丰五年五月", "三司分部，均不置使"),
    )
    total_tps = [tp(w, eid, time, event, i, z, "财政机构合称", f"建三部{time}制度时段。", chain="none")
                 for time, event in stages]
    chain(w, total_tps, "按原文四个连续制度时段连接三部时间链。")
    instance_times = (
        "宋初",
        "北宋太平兴国八年三月七日",
        "北宋淳化五年十二月二十四日",
        "北宋咸平六年",
    )
    for total_tp, inst_time in zip(total_tps, instance_times):
        for title in ("盐铁", "度支", "户部"):
            inst = node(w, title, inst_time, "机构")[1]
            rel(w, total_tp, inst, "统称与实例", i, z, f"三部是{title}等三司的合称。")
    tri_song = node(w, "三司", "宋初", "机构")[1]
    tri_1003 = node(w, "三司", "北宋咸平六年", "机构")[1]
    for title in ("盐铁", "度支", "户部"):
        rel(w, tri_song, node(w, title, "宋初", "机构")[1], "上下级机构", i, z,
            f"宋初{title}为三司分部。")
        rel(w, tri_1003, node(w, title, "北宋咸平六年", "机构")[1], "上下级机构", i, z,
            f"咸平六年六月后{title}为三司分部。")
    w.commit()


def entry312():
    i = 312
    z = F[i]["text"]
    w = W(i)
    total_e = entity(w, "三部使", "官职", z, "原文明载为盐铁使、度支使、户部使合称。")
    stage_defs = (
        ("北宋太平兴国八年三月七日", "三司分三部，各部置使"),
        ("北宋淳化四年五月二十一日", "罢"),
        ("北宋淳化五年十二月二十四日", "复置"),
        ("北宋咸平六年六月二十九日", "罢，不复再设"),
    )
    total_tps = [tp(w, total_e, time, event, i, z, "财政长官合称", f"建三部使{time}节点。", chain="none")
                 for time, event in stage_defs]
    chain(w, total_tps, "连接三部使两次置罢沿革。")
    for title in ("盐铁使", "度支使", "户部使"):
        inst_e = entity(w, title, "官职", z, f"三部使条明确列出实例{title}。")
        inst_tps = [tp(w, inst_e, time, event, i, z, "财政长官", f"据三部使条建{title}{time}节点。", chain="none")
                    for time, event in stage_defs]
        source_time = {"盐铁使": "唐乾元元年", "度支使": "唐乾元二年", "户部使": "唐元和六年"}[title]
        source_tp = w.find_timepoint(inst_e, source_time)
        ordered = ([source_tp] if source_tp else []) + inst_tps
        chain(w, ordered, f"连接{title}唐代源流及北宋两次置罢沿革。")
        for pos in (0, 2):
            rel(w, total_tps[pos], inst_tps[pos], "统称与实例", i, z,
                f"三部使在该期包括{title}。")
    w.commit()


def entry313():
    i = 313
    z = F[i]["all"]
    q_hist = q(i, "①太平兴国八年三月三司分为三部，各部置副使，至端拱元年罢。②至道元年又置（《宋史·宋太初传》）。至道三年四月又罢（《宋史·真宗纪》1）。③咸平六年六日复置，直至元丰五年置三司归户部（《长编》卷55）。")
    w = W(i)
    total_e = entity(w, "三部副使", "官职", F[i]["text"], "原文明载为三部副使的合称。")
    stage_defs = (
        ("北宋太平兴国八年三月", "三司分三部，各部置副使"),
        ("北宋端拱元年", "罢"),
        ("北宋至道元年", "复置"),
        ("北宋至道三年四月", "又罢"),
        ("北宋咸平六年", "复置"),
        ("北宋元丰五年", "三司归户部，三部副使终结"),
    )
    total_tps = [tp(w, total_e, time, event, i, q_hist, "财政副长官合称", f"建三部副使{time}节点。", chain="none")
                 for time, event in stage_defs]
    chain(w, total_tps, "连接三部副使三次置罢沿革。")
    for title in ("三司盐铁副使", "三司度支副使", "三司户部副使"):
        inst_e = entity(w, title, "官职", F[i]["text"], f"三部副使条明确列出实例{title}。")
        inst_tps = [tp(w, inst_e, time, event, i, q_hist, "财政副长官", f"据三部副使条建{title}{time}节点。", chain="none")
                    for time, event in stage_defs]
        ordered = inst_tps
        if title == "三司盐铁副使":
            detail_times = ("北宋淳化三年", "北宋淳化四年十月", "北宋咸平六年六月")
            detail = [w.find_timepoint(inst_e, time) for time in detail_times]
            if all(detail):
                ordered = [inst_tps[0], inst_tps[1], detail[0], detail[1],
                           inst_tps[2], inst_tps[3], inst_tps[4], detail[2], inst_tps[5]]
        chain(w, ordered, f"连接{title}三次置罢沿革，并保留已有精确月份节点。")
        for pos in (0, 2, 4):
            rel(w, total_tps[pos], inst_tps[pos], "统称与实例", i, F[i]["text"],
                f"三部副使在该期包括{title}。")
    w.commit()


def attach_envoy(i, title, office, tang_time, tang_quote, duty_quote, grade_note=None):
    w = W(i)
    eid = w.find_entity(title, "官职")
    assert eid
    tang = tp(w, eid, tang_time, "始见或始置", i, tang_quote, "财政长官",
              f"补建{title}唐代源流节点。", chain="none")
    existing = [node(w, title, t, "官职")[1] for t in (
        "北宋太平兴国八年三月七日", "北宋淳化四年五月二十一日",
        "北宋淳化五年十二月二十四日", "北宋咸平六年六月二十九日")]
    chain(w, [tang, *existing], f"把{title}唐代源流接到北宋两次置罢链之前。")
    cite(w, "Timepoints", existing[0], i, duty_quote, f"补充{title}职掌。", note="职掌")
    if grade_note:
        cite(w, "Timepoints", existing[0], i, grade_note, f"补充{title}品位。", note="品位")
    office_starts = (
        node(w, office, "北宋太平兴国八年三月七日", "机构")[1],
        node(w, office, "北宋淳化五年十二月二十四日", "机构")[1],
    )
    for office_tp, official_tp in zip(office_starts, (existing[0], existing[2])):
        quota_quote = F[i]["fields"]["编制"]
        rid = rel(w, office_tp, official_tp, "编制隶属", i, quota_quote,
                  f"{office}自立为主司时置{title}一人。", staff_quota=1, staff_type="官")
        cite(w, "Relationships", rid, 312, F[312]["text"], "三部使条补证各部置使。")
    w.commit()


def entry314():
    attach_envoy(
        314, "盐铁使", "盐铁", "唐乾元元年",
        q(314, "始置于唐乾元元年（758）（《册府元龟》卷483《邦计部·总序》）。"),
        q(314, "统领本部事，上奏及签署案、检（《宋史·职官志》2《三司使》）。"),
    )


def entry315():
    i = 315
    z = F[i]["all"]
    q_hist = q(i, "太平兴国八年三司分三部各置使，或置副使，端拱元年罢。淳化三年复置，四年十月又省。至道元年又置（《宋史·职官志》2《三部副使》)。至道三年四月十三日罢(《宋史·真宗纪》1)。②咸平六年六月复置，直至元丰改制（《长编》卷55)。三部使合为三司使，不置三司副使，但盐铁、度支、户部逐部各置副使。")
    q_duty = q(i, "①三部分治时，盐铁副使为本部正使的佐贰。②三部合一为三司之后，盐铁副使与盐铁判官主管盐铁部事（《长编》卷55，咸平六年六月丁亥）。")
    w = W(i)
    eid = w.find_entity("三司盐铁副使", "官职")
    assert eid
    base_times = ("北宋太平兴国八年三月", "北宋端拱元年", "北宋至道元年",
                  "北宋至道三年四月", "北宋咸平六年", "北宋元丰五年")
    base = {t: node(w, "三司盐铁副使", t, "官职")[1] for t in base_times}
    chunhua3 = tp(w, eid, "北宋淳化三年", "复置", i, q_hist, "财政副长官",
                  "补建盐铁副使淳化三年复置节点。", chain="none")
    chunhua4 = tp(w, eid, "北宋淳化四年十月", "又省", i, q_hist, "财政副长官",
                  "补建盐铁副使淳化四年又省节点。", chain="none")
    xiangping = tp(w, eid, "北宋咸平六年六月", "复置，主管盐铁部事", i, q_hist,
                   "财政副长官", "补建盐铁副使咸平六年六月复置节点。", chain="none")
    chain(w, [base[base_times[0]], base[base_times[1]], chunhua3, chunhua4,
              base[base_times[2]], base[base_times[3]], base[base_times[4]], xiangping,
              base[base_times[5]]], "按本条精确沿革重排盐铁副使时间链。")
    cite(w, "Timepoints", xiangping, i, q_duty, "补充三部合一后盐铁副使职掌。", note="职掌")
    office_nodes = (
        node(w, "盐铁", "北宋太平兴国八年三月七日", "机构")[1],
        node(w, "盐铁", "北宋淳化五年十二月二十四日", "机构")[1],
        node(w, "盐铁", "北宋咸平六年", "机构")[1],
    )
    official_nodes = (base[base_times[0]], base[base_times[2]], xiangping)
    for pos, (office_tp, official_tp) in enumerate(zip(office_nodes, official_nodes)):
        quota = 1 if pos == 2 else None
        rid = rel(w, office_tp, official_tp, "编制隶属", i, q_hist,
                  "盐铁分部或自立主司时置盐铁副使。", staff_quota=quota, staff_type="官")
        if pos == 2:
            cite(w, "Relationships", rid, 309, F[309]["fields"]["编制"],
                 "盐铁条明载咸平六年后副使一人。")
    w.commit()


def entry316():
    attach_envoy(
        316, "度支使", "度支", "唐乾元二年",
        q(316, "始置于唐乾元二年(759)(《旧唐书·吕湮传》)。"),
        q(316, "统领本部事，及上奏、签署检、案等文书（《宋史·职官志》2《三司使》）。"),
        q(316, "视所带本官阶，位次于盐铁使（《宋史·职官志》2《三司使》）。"),
    )


def attach_deputy(i, title, office, duty_quote, grade_quote=None):
    w = W(i)
    eid = w.find_entity(title, "官职")
    assert eid
    active_times = ("北宋太平兴国八年三月", "北宋至道元年", "北宋咸平六年")
    official_nodes = [node(w, title, t, "官职")[1] for t in active_times]
    cite(w, "Timepoints", official_nodes[-1], i, duty_quote, f"补充{title}分合时期职掌。", note="职掌")
    q_quota = q(i, "一人（《宋史·职官志》2《三部副使》）。")
    for tid in official_nodes:
        cite(w, "Timepoints", tid, i, q_quota, f"补充{title}一人员额。", note="编制")
    if grade_quote:
        cite(w, "Timepoints", official_nodes[-1], i, grade_quote, f"补充{title}品位。", note="品位")
    office_nodes = (
        node(w, office, "北宋太平兴国八年三月七日", "机构")[1],
        node(w, office, "北宋淳化五年十二月二十四日", "机构")[1],
        node(w, office, "北宋咸平六年", "机构")[1],
    )
    for office_tp, official_tp in zip(office_nodes, official_nodes):
        rid = rel(w, office_tp, official_tp, "编制隶属", i, q_quota,
                  f"{office}置{title}一人。", staff_quota=1, staff_type="官")
        cite(w, "Relationships", rid, 313, F[313]["all"], "三部副使条补证各部置副使。")
    w.commit()


def entry317():
    attach_deputy(
        317, "三司度支副使", "度支",
        q(317, "①三部分治时，为度支使佐贰。②三部合一为三司时，度支副使与度支判官主管本部事，三司使止在案、检等文书上签字而已（《长编》卷55）。"),
        q(317, "视所带本官阶，多以员外郎以上充。仅次于盐铁副使。"),
    )


def entry318():
    attach_envoy(
        318, "户部使", "户部", "唐元和六年",
        q(318, "唐元和六年已见置户部使（《唐会要》卷58《户部侍郎》）。"),
        q(318, "领本部事、及上奏签署案、检等文书（《宋史·职官志》2《三司使》）。"),
        q(318, "官品视所带本官阶，位次于度支使。《宋史·魏羽传》：“再为户部、度支使。”"),
    )


def entry319():
    attach_deputy(
        319, "三司户部副使", "户部",
        q(319, "①三部分治时，为户部使佐贰。②三部使合一为三司使时，与本部判官主管三司户部事，三司使止在案、检文书上签字而已（《长编》卷55，丁亥）。"),
        q(319, "官品视所带本官阶。位次于盐铁、度支副使。“历户部、度支、盐铁副使”（《宋史·蒋堂传》）。"),
    )


def entry320():
    i = 320
    z = F[i]["text"]
    w = W(i)
    eid = entity(w, "权三司盐铁副使", "官职", z, "辞典明载为资浅盐铁副使所带差遣名。")
    tid = tp(w, eid, "宋代（未载具体年月）", "盐铁副使资浅者带“权”字", i, z,
             "财政副长官", "建权三司盐铁副使概括节点。")
    office = node(w, "盐铁", "北宋咸平六年", "机构")[1]
    rel(w, office, tid, "编制隶属", i, z, "权三司盐铁副使为盐铁部副长官。", staff_type="官")
    w.commit()


def main():
    repair_entry156_trailing_newlines()
    entry301(); entry302(); entry303(); entry304(); entry305()
    entry306(); entry307()
    entry309(); entry310(); entry311(); entry308()
    entry312(); entry313(); entry314(); entry315(); entry316()
    entry317(); entry318(); entry319(); entry320()


if __name__ == "__main__":
    main()
