#!/usr/bin/env python3
"""提取 chapter2t4 第711–730条：门下省吏、通进司及进奏院系统。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")
)


def load(i):
    with sqlite3.connect(DICT_DB) as c:
        row = c.execute(
            "select title,page,text,fields from chapter2t4 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(711, 731)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, field=None):
    return F[i]["fields"][field] if field else F[i]["text"]


def C(i, field=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field}字段）" if field else "")


def en(w, title, typ, quotation, decision):
    return w.entity(title, typ, decision, quotation=quotation)


def fe(w, title, typ=None):
    eid = w.find_entity(title, typ)
    assert eid, (title, typ)
    return eid


def ft(w, entity_id, time):
    tid = w.find_timepoint(entity_id, time)
    assert tid, (entity_id, time)
    return tid


def ac(w, table, target_id, i, quotation, decision, field=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field), quotation, decision, **kwargs
    )


def tp(
    w,
    entity_id,
    time,
    event,
    i,
    quotation,
    category,
    decision,
    field=None,
    **kwargs,
):
    tid = w.timepoint(
        entity_id,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        **kwargs,
    )
    ac(w, "Timepoints", tid, i, quotation, decision, field)
    return tid


def rel(
    w,
    subject_id,
    object_id,
    relation_type,
    i,
    quotation,
    decision,
    field=None,
    **kwargs,
):
    rid = w.relationship(
        subject_id,
        object_id,
        relation_type,
        decision,
        quotation,
        **kwargs,
    )
    ac(w, "Relationships", rid, i, quotation, decision, field)
    return rid


def chain(w, timepoint_ids, decision):
    assert timepoint_ids and len(timepoint_ids) == len(set(timepoint_ids))
    for n, tid in enumerate(timepoint_ids):
        w.relink(
            tid,
            decision,
            prev_id=timepoint_ids[n - 1] if n else None,
            succ_id=timepoint_ids[n + 1] if n + 1 < len(timepoint_ids) else None,
        )


def refine(
    w,
    tid,
    i,
    quotation,
    decision,
    field=None,
    *,
    event=None,
    category=None,
    grade=None,
    replace_quotation=False,
):
    old = w.conn.execute(
        "select event,attr_category,attr_grade,quotation from Timepoints where id=?",
        (tid,),
    ).fetchone()
    assert old, tid
    new = (
        event if event is not None else old[0],
        category if category is not None else old[1],
        grade if grade is not None else old[2],
        quotation if replace_quotation else old[3],
    )
    if new != old:
        w.conn.execute(
            "update Timepoints set event=?,attr_category=?,attr_grade=?,quotation=? "
            "where id=?",
            (*new, tid),
        )
        w._br(
            "Timepoints",
            tid,
            f"据专条细化时间点：event {old[0]}->{new[0]}；"
            f"category {old[1]}->{new[1]}；grade {old[2]}->{new[2]}。{decision}",
        )
    ac(w, "Timepoints", tid, i, quotation, decision, field)
    return tid


def retime(w, tid, time, event, i, quotation, category, decision, field=None):
    old = w.conn.execute(
        "select entity_id,time,event,attr_category from Timepoints where id=?", (tid,)
    ).fetchone()
    assert old, tid
    clash = w.conn.execute(
        "select id from Timepoints where entity_id=? and time=? and id<>?",
        (old[0], time, tid),
    ).fetchone()
    assert not clash, (tid, time, clash)
    w.conn.execute(
        "update Timepoints set time=?,event=?,attr_category=?,quotation=? where id=?",
        (time, event, category or old[3], quotation, tid),
    )
    w._br(
        "Timepoints",
        tid,
        f"据专条细化 time {old[1]}->{time}、event {old[2]}->{event}：{decision}",
    )
    ac(w, "Timepoints", tid, i, quotation, decision, field)
    return tid


def set_relation_attrs(w, rid, quota, staff_type, decision):
    old = w.conn.execute(
        "select staff_quota,staff_type from Relationships where id=?", (rid,)
    ).fetchone()
    assert old, rid
    new = (
        quota if quota is not None else old[0],
        staff_type if staff_type is not None else old[1],
    )
    if tuple(old) != new:
        w.conn.execute(
            "update Relationships set staff_quota=?,staff_type=? where id=?",
            (*new, rid),
        )
        w._br(
            "Relationships",
            rid,
            f"补充编制属性 quota {old[0]}->{new[0]}、"
            f"staff_type {old[1]}->{new[1]}：{decision}",
        )


def relation_id(w, subject_title, object_title, relation_type, subject_time=None, object_time=None):
    sql = (
        "select r.id from Relationships r "
        "join Timepoints a on a.id=r.subject_id "
        "join Entities ea on ea.id=a.entity_id "
        "join Timepoints b on b.id=r.object_id "
        "join Entities eb on eb.id=b.entity_id "
        "where ea.title=? and eb.title=? and r.relation_type=?"
    )
    params = [subject_title, object_title, relation_type]
    if subject_time is not None:
        sql += " and a.time=?"
        params.append(subject_time)
    if object_time is not None:
        sql += " and b.time=?"
        params.append(object_time)
    row = w.conn.execute(sql + " order by r.id limit 1", params).fetchone()
    return row[0] if row else None


def entry711():
    i = 711
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    grade = Q(i, "品位")
    staff = Q(i, "编制")
    w = W(i)
    eid = fe(w, "守当官", "官职")
    early = ft(w, eid, "宋前期")
    ac(w, "Timepoints", early, i, origin, "补证北宋初中书吏已有守当官。", "职源")
    rule = tp(
        w,
        eid,
        "北宋熙宁三年十一月",
        "无品；任满五年遇郊礼可自陈补三班奉职",
        i,
        grade,
        "吏职",
        "建守当官出职制度节点。",
        "品位",
        chain="none",
    )
    yf = ft(w, eid, "北宋元丰新制（门下省）")
    refine(
        w,
        yf,
        i,
        duty,
        "据专条细化门下省守当官职掌。",
        "职掌",
        event="门下省吏，掌用印及分掌诸房簿书文字，十九人",
        category="吏职",
        replace_quotation=True,
    )
    ac(w, "Timepoints", yf, i, main, "补证守当官隶门下省。")
    ac(w, "Timepoints", yf, i, staff, "补证元丰新制十九人。", "编制", note="编制")
    chain(
        w,
        [early, rule, yf, ft(w, eid, "南宋嘉定五年")],
        "把熙宁出职条例、元丰门下省编制接入守当官沿革链。",
    )
    rid = relation_id(
        w, "门下省", "守当官", "编制隶属", "北宋元丰新制", "北宋元丰新制（门下省）"
    )
    assert rid
    set_relation_attrs(w, rid, 19, "吏", "守当官专条明载元丰员额。")
    ac(w, "Relationships", rid, i, staff, "补证门下省置守当官十九人。", "编制")
    w.commit()


def entry712():
    i = 712
    main = Q(i)
    w = W(i)
    eid = fe(w, "守阙守当官", "官职")
    tid = ft(w, eid, "北宋绍圣三年")
    refine(
        w,
        tid,
        i,
        main,
        "专条补足守阙守当官身份、职掌与员额。",
        event="门下省候补守当官，掌诸房书写文字，增置一百人",
        category="吏职",
        replace_quotation=True,
    )
    rid = relation_id(
        w, "门下省", "守阙守当官", "编制隶属", "北宋绍圣三年", "北宋绍圣三年"
    )
    assert rid
    set_relation_attrs(w, rid, 100, "吏", "专条明载绍圣三年增置一百人。")
    ac(w, "Relationships", rid, i, main, "补证守阙守当官隶门下省且一百人为额。")
    w.commit()


def entry713():
    i = 713
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    staff = Q(i, "编制")
    aliases = Q(i, "别称")
    w = W(i)
    eid = fe(w, "通进司", "机构")
    start = tp(
        w,
        eid,
        "北宋初",
        "始置于垂拱殿门内，隶枢密院",
        i,
        origin,
        "中央奏牍机构",
        "建通进司北宋初始置节点。",
        "职源",
        chain="none",
    )
    moved = ft(w, eid, "北宋淳化四年八月十八日")
    ac(w, "Timepoints", moved, i, origin, "补证通进司北宋初始置背景。", "职源")
    taboo = tp(
        w,
        eid,
        "北宋真宗朝（未载具体年月）",
        "因避章献太后父刘通名讳，改称承进司",
        i,
        aliases,
        "中央奏牍机构",
        "建通进司避讳改称节点；承进司仅为别称，不另建实体。",
        "别称",
        chain="none",
    )
    combined = tp(
        w,
        eid,
        "宋前期（与银台司合置后，未载年月）",
        "与银台司合署，属中书门下；承受并进呈、分发章奏文牍",
        i,
        staff,
        "中央奏牍机构",
        "建通进司与银台司合署后的隶属节点。",
        "编制",
        chain="none",
    )
    ac(w, "Timepoints", combined, i, duty, "补证宋前期承接、进呈和分发章奏职掌。", "职掌")
    yf = tp(
        w,
        eid,
        "北宋元丰新制",
        "单独置司，隶门下省给事中；昼夜承接、编目、进呈并发付奏牍",
        i,
        duty,
        "中央奏牍机构",
        "建通进司元丰新制节点。",
        "职掌",
        chain="none",
    )
    ac(w, "Timepoints", yf, i, staff, "补证元丰新制隶属与官吏编制。", "编制", note="编制")
    chain(w, [start, moved, taboo, combined, yf], "连接通进司北宋初至元丰沿革。")
    rel(
        w,
        ft(w, fe(w, "枢密院", "机构"), "宋初"),
        start,
        "上下级机构",
        i,
        staff,
        "宋初通进司隶枢密院。",
        "编制",
    )
    rel(
        w,
        ft(w, fe(w, "中书门下", "机构"), "宋前期"),
        combined,
        "上下级机构",
        i,
        staff,
        "与银台司合署后，通进司属中书门下。",
        "编制",
    )
    rel(
        w,
        ft(w, fe(w, "门下省", "机构"), "北宋元丰新制"),
        yf,
        "上下级机构",
        i,
        staff,
        "元丰新制通进司归隶门下省。",
        "编制",
    )
    rel(
        w,
        yf,
        ft(w, fe(w, "给事中", "官职"), "北宋元丰新制"),
        "编制隶属",
        i,
        staff,
        "元丰新制通进司归门下省给事中主管。",
        "编制",
        staff_type="官",
    )
    role_specs = (
        ("点检通进司公事", "官职", 1, "官", "点检通进司官一员"),
        ("监通进司官", "官职", 2, "官", "监通进司官二员"),
        ("奏禀使臣", "官职", 2, "官", "奏禀使臣二员"),
        ("主管通进司文字", "官职", 4, "吏", "主管文字四员"),
        ("发敕官", "官职", None, "吏", "发敕官若干"),
    )
    for title, typ, quota, staff_type, event in role_specs:
        role_e = en(w, title, typ, staff, f"通进司总条编制明列{title}。")
        role_t = tp(
            w,
            role_e,
            "北宋元丰新制",
            event,
            i,
            staff,
            "差遣官" if staff_type == "官" else "吏职",
            f"按通进司总条建{title}元丰编制节点。",
            "编制",
            chain="none",
        )
        rel(
            w,
            yf,
            role_t,
            "编制隶属",
            i,
            staff,
            f"通进司总条明载{event}。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )

    # 总条还明确记载元丰前通进司有监官二人、书令史二人。
    monitor_e = fe(w, "监通进司官", "官职")
    monitor_pre = tp(
        w,
        monitor_e,
        "宋前期（通进司，未载具体年月）",
        "通进司监官二人",
        i,
        staff,
        "差遣官",
        "建元丰前通进司监官编制节点。",
        "编制",
        chain="none",
    )
    monitor_yf = ft(w, monitor_e, "北宋元丰新制")
    chain(w, [monitor_pre, monitor_yf], "连接通进司监官宋前期与元丰新制节点。")
    rel(
        w,
        combined,
        monitor_pre,
        "编制隶属",
        i,
        staff,
        "宋前期通进司置监官二人。",
        "编制",
        staff_quota=2,
        staff_type="官",
    )
    clerk_e = fe(w, "书令史", "官职")
    clerk_t = tp(
        w,
        clerk_e,
        "宋前期（通进司）",
        "通进司书令史二人",
        i,
        staff,
        "吏职",
        "建宋前期通进司书令史编制节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        combined,
        clerk_t,
        "编制隶属",
        i,
        staff,
        "宋前期通进司置书令史二人。",
        "编制",
        staff_quota=2,
        staff_type="吏",
    )
    w.commit()


def entry714():
    i = 714
    main = Q(i)
    duty = Q(i, "职掌")
    aliases = Q(i, "简称")
    w = W(i)
    eid = en(w, "点检通进司公事", "官职", main, "本条明确为官名，建官职实体。")
    tid = ft(w, eid, "北宋元丰新制")
    refine(
        w,
        tid,
        i,
        duty,
        "建点检通进司公事元丰节点。",
        "职掌",
        event="由门下后省长官兼任，检查通进司文字承接、发付及稽滞",
        category="兼任差遣",
        replace_quotation=True,
    )
    ac(w, "Timepoints", tid, i, main, "补证非专职、由门下后省长官兼。")
    ac(w, "Timepoints", tid, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    rid = relation_id(
        w, "通进司", "点检通进司公事", "编制隶属",
        "北宋元丰新制", "北宋元丰新制",
    )
    assert rid
    ac(w, "Relationships", rid, i, main, "专条补证点检通进司公事属通进司。")
    w.commit()


def entry715():
    i = 715
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    staff = Q(i, "编制")
    aliases = Q(i, "简称")
    w = W(i)
    eid = en(w, "监通进司官", "官职", main, "本条明确为差遣官名，建官职实体。")
    tid = ft(w, eid, "北宋元丰新制")
    refine(
        w,
        tid,
        i,
        origin,
        "建监通进司官元丰节点。",
        "职源",
        event="由宦官充，轮值检察文字承接、封发有无稽留舞弊，二员",
        category="差遣官",
        replace_quotation=True,
    )
    ac(w, "Timepoints", tid, i, duty, "补证监通进司官检察及御封文字封发职掌。", "职掌")
    ac(w, "Timepoints", tid, i, staff, "补证二员轮值。", "编制", note="编制")
    ac(w, "Timepoints", tid, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    rid = relation_id(
        w, "通进司", "监通进司官", "编制隶属",
        "北宋元丰新制", "北宋元丰新制",
    )
    assert rid
    ac(w, "Relationships", rid, i, staff, "专条补证监通进司官二员轮值。", "编制")
    w.commit()


def entries716_718():
    nodes = {}
    for i, title in ((716, "承转承接亲从官"), (717, "承转承接亲事官")):
        main = Q(i)
        w = W(i)
        eid = en(w, title, "官职", main, f"本条明确{title}为通进司吏名。")
        w.commit()

        # 具体吏名来自本专条；元丰时期及通进司编制背景来自第713条总条。
        total = W(713)
        total_staff = Q(713, "编制")
        tid = tp(
            total,
            eid,
            "北宋元丰新制",
            f"通进司承转承接吏职（{title}）",
            713,
            total_staff,
            "吏职",
            f"总条明载元丰通进司置承转承接亲从亲事官；结合专条建立{title}节点。",
            "编制",
            chain="none",
        )
        rid = rel(
            total,
            ft(total, fe(total, "通进司", "机构"), "北宋元丰新制"),
            tid,
            "编制隶属",
            713,
            total_staff,
            f"元丰通进司置承转承接吏职，{title}为其专条所列具体职名。",
            "编制",
            staff_type="吏",
        )
        total.commit()

        w = W(i)
        event = (
            "由皇城司亲从官执役，承接通进司文字并专送内降御封文字"
            if i == 716
            else "由皇城司亲事官执役，专一承转承接通进司文字"
        )
        refine(
            w,
            tid,
            i,
            main,
            f"建{title}元丰通进司节点。",
            event=event,
            category="吏职",
            replace_quotation=True,
        )
        ac(w, "Relationships", rid, i, main, f"专条补证{title}在通进司执役。")
        nodes[title] = tid
        w.commit()

    # 第718条只是上述两种吏职的合称，不创建“承转承接亲从亲事官”实体。
    i = 718
    main = Q(i)
    w = W(i)
    for title, tid in nodes.items():
        ac(
            w,
            "Timepoints",
            tid,
            i,
            main,
            f"本条补证{title}属于‘承转承接亲从、亲事官’合称；合称不另建实体。",
            note="统称证据",
        )
    w.commit()


def entry719():
    i = 719
    main = Q(i)
    duty = Q(i, "职掌")
    w = W(i)
    eid = en(w, "奏禀使臣", "官职", main, "本条明确为差遣名，建官职实体。")
    tid = ft(w, eid, "北宋元丰新制")
    refine(
        w,
        tid,
        i,
        duty,
        "建奏禀使臣元丰通进司节点。",
        "职掌",
        event="由入内内侍省内侍充；奏禀逾三日未批的进呈文字，二员",
        category="差遣",
        replace_quotation=True,
    )
    ac(w, "Timepoints", tid, i, main, "补证奏禀使臣由内侍充。")
    rid = relation_id(
        w, "通进司", "奏禀使臣", "编制隶属",
        "北宋元丰新制", "北宋元丰新制",
    )
    assert rid
    ac(w, "Relationships", rid, i, duty, "专条补证奏禀使臣的催促职掌。", "职掌")
    w.commit()


def entry720():
    i = 720
    main = Q(i)
    w = W(i)
    eid = en(w, "主管通进司文字", "官职", main, "本条明确为通进司吏名，建官职实体。")
    tid = ft(w, eid, "北宋元丰新制")
    refine(
        w,
        tid,
        i,
        main,
        "建主管通进司文字元丰节点。",
        event="由门下后省当职吏人差充，书写、题封并轮流值宿，四员",
        category="吏职",
        replace_quotation=True,
    )
    rid = relation_id(
        w, "通进司", "主管通进司文字", "编制隶属",
        "北宋元丰新制", "北宋元丰新制",
    )
    assert rid
    ac(w, "Relationships", rid, i, main, "专条补证主管通进司文字的来源、职掌及四员编制。")
    w.commit()


def entry721():
    i = 721
    main = Q(i)
    w = W(i)
    eid = fe(w, "发敕官", "官职")
    yf = ft(w, eid, "北宋元丰新制")
    refine(
        w,
        yf,
        i,
        main,
        "建发敕官在通进司的元丰节点。",
        event="由中书省五房五院行首司按名次填充，发放内降文字",
        category="吏职",
        replace_quotation=True,
    )
    south = tp(
        w,
        eid,
        "南宋淳熙三年",
        "改由发敕官亲自发放御封文字，不得令亲从、亲事官承发",
        i,
        main,
        "吏职",
        "建淳熙三年发敕制度变化节点。",
        chain="none",
    )
    chain(w, [yf, south], "连接通进司发敕官元丰、淳熙节点。")
    rid = relation_id(
        w, "通进司", "发敕官", "编制隶属",
        "北宋元丰新制", "北宋元丰新制",
    )
    assert rid
    ac(w, "Relationships", rid, i, main, "专条补证发敕官隶通进司及其职掌变化。")
    w.commit()


def entry722():
    i = 722
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    staff = Q(i, "编制")
    aliases = Q(i, "别名")
    w = W(i)
    eid = en(w, "进奏院", "机构", main, "本条明确为官署名，建机构实体。")
    tang = tp(
        w,
        eid,
        "唐大历十二年",
        "上都留后改称上都知进奏院，进奏院之名始见",
        i,
        origin,
        "地方驻京奏报机构",
        "建进奏院唐代职源节点。",
        "职源",
        chain="none",
    )
    early = tp(
        w,
        eid,
        "宋初",
        "节镇、州军监及转运司场务各置驻京进奏院，收发地方与朝廷文书",
        i,
        duty,
        "地方驻京奏报机构",
        "建宋初诸进奏院节点。",
        "职掌",
        chain="none",
    )
    ac(w, "Timepoints", early, i, staff, "补证宋初各地进奏院设置与吏额。", "编制", note="编制")
    merged = tp(
        w,
        eid,
        "北宋太平兴国七年十月",
        "诸州进奏院归并都进奏院，实体官署实废但各州朱记名仍存",
        i,
        staff,
        "地方驻京奏报机构",
        "建诸进奏院归并节点。",
        "编制",
        chain="none",
    )
    yf = tp(
        w,
        eid,
        "北宋元丰新制",
        "所收章奏交门下省章奏房；边防机密可直投通进司",
        i,
        duty,
        "地方驻京奏报机构",
        "建元丰进奏院文书投递节点。",
        "职掌",
        chain="none",
    )
    ac(w, "Timepoints", yf, i, aliases, "侯邸为别称，不另建实体。", "别名", note="纯别名")
    chain(w, [tang, early, merged, yf], "连接进奏院唐代、宋初归并与元丰节点。")
    w.commit()


def entry723():
    i = 723
    main = Q(i)
    history = Q(i, "职源与沿革")
    duty = Q(i, "职掌")
    staff = Q(i, "编制")
    aliases = Q(i, "简称与别名")
    w = W(i)
    eid = en(w, "都进奏院", "机构", main, "本条明确为官署名，建机构实体。")
    start = tp(
        w,
        eid,
        "北宋太平兴国七年十月二十一日",
        "合并诸道进奏院而置，总领天下邮递；进奏官一百五十人",
        i,
        history,
        "中央邮递奏报机构",
        "建都进奏院始置节点。",
        "职源与沿革",
        chain="none",
    )
    ac(w, "Timepoints", start, i, duty, "补证宋前期收发地方章奏和中央文书职掌。", "职掌")
    ac(w, "Timepoints", start, i, staff, "补证初置进奏官一百五十人。", "编制", note="编制")
    later = tp(
        w,
        eid,
        "北宋太平兴国七年后（未载具体年月）",
        "进奏官后定一百二十人",
        i,
        staff,
        "中央邮递奏报机构",
        "建都进奏院宋前期改额节点。",
        "编制",
        chain="none",
    )
    yf = tp(
        w,
        eid,
        "北宋元丰新制",
        "收章奏交门下省章奏房，收三省枢密院等文书递送诸路；进奏官一百人",
        i,
        duty,
        "中央邮递奏报机构",
        "建都进奏院元丰节点。",
        "职掌",
        chain="none",
    )
    ac(w, "Timepoints", yf, i, staff, "补证元丰进奏官一百人为额。", "编制", note="编制")
    south = tp(
        w,
        eid,
        "南宋初",
        "进奏官八十一人，另有守阙进奏官十六人及守阙副知、书写人",
        i,
        staff,
        "中央邮递奏报机构",
        "建都进奏院南宋初编制节点。",
        "编制",
        chain="none",
    )
    ac(w, "Timepoints", yf, i, aliases, "全文扫描简称别名字段；均为纯别称，不另建实体。", "简称与别名", note="纯别称")
    chain(w, [start, later, yf, south], "连接都进奏院始置、改额、元丰与南宋节点。")
    source_end = ft(w, fe(w, "进奏院", "机构"), "北宋太平兴国七年十月")
    rel(w, source_end, start, "前后演变", i, history, "诸道进奏院合并为都进奏院。", "职源与沿革")

    # 总条先建立钤辖、监官及进奏官的编制；后续专条再补职源、职掌。
    controller_e = en(w, "钤辖诸道进奏院", "官职", staff, "总条编制明列初设钤辖二人。")
    controller_t = tp(
        w,
        controller_e,
        "北宋太平兴国七年",
        "初设钤辖诸道进奏院二人",
        i,
        staff,
        "差遣官",
        "按都进奏院总条建钤辖官始置编制节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        start,
        controller_t,
        "编制隶属",
        i,
        staff,
        "都进奏院初设钤辖二人。",
        "编制",
        staff_quota=2,
        staff_type="官",
    )

    monitor_e = en(w, "监都进奏院", "官职", staff, "总条编制明列后改置监都进奏院官二人。")
    monitor_t = tp(
        w,
        monitor_e,
        "北宋（都进奏院改置监官后，未载年月）",
        "改置监都进奏院官二人",
        i,
        staff,
        "差遣官",
        "按总条建监官改置编制节点；具体最早纪年由专条细化。",
        "编制",
        chain="none",
    )
    rel(
        w,
        start,
        monitor_t,
        "编制隶属",
        i,
        staff,
        "都进奏院后改置监官二人。",
        "编制",
        staff_quota=2,
        staff_type="官",
    )

    officer_e = en(w, "进奏官", "官职", staff, "都进奏院总条编制明列进奏官。")
    officer_nodes = (
        (start, "北宋太平兴国七年十月", "进奏官一百五十人", 150),
        (later, "北宋太平兴国七年后（未载具体年月）", "进奏官后定一百二十人", 120),
        (yf, "北宋元丰新制", "进奏官一百人", 100),
        (south, "南宋初", "进奏官八十一人", 81),
    )
    for parent_t, time, event, quota in officer_nodes:
        officer_t = tp(
            w,
            officer_e,
            time,
            event,
            i,
            staff,
            "公吏",
            f"按都进奏院总条建进奏官{quota}人节点。",
            "编制",
            chain="none",
        )
        rel(
            w,
            parent_t,
            officer_t,
            "编制隶属",
            i,
            staff,
            f"都进奏院在该时期置进奏官{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type="吏",
        )

    waiting_e = en(w, "守阙进奏官", "官职", staff, "南宋初编制明列守阙进奏官十六人。")
    waiting_t = tp(
        w,
        waiting_e,
        "宋代（未载具体年月）",
        "都进奏院进奏官候补，后改名拣中副知",
        i,
        staff,
        "公吏",
        "建守阙进奏官及其后改名背景节点。",
        "编制",
        chain="none",
    )
    selected_e = en(w, "拣中副知", "官职", staff, "总条明载守阙进奏官后改名拣中副知。")
    selected_t = tp(
        w,
        selected_e,
        "宋代（守阙进奏官改名后，未载年月）",
        "由守阙进奏官改名",
        i,
        staff,
        "公吏",
        "建拣中副知改名节点。",
        "编制",
        chain="none",
    )
    rel(w, waiting_t, selected_t, "前后演变", i, staff, "守阙进奏官后改名拣中副知。", "编制")
    rel(
        w,
        south,
        selected_t,
        "编制隶属",
        i,
        staff,
        "南宋初都进奏院置改名后的拣中副知十六人。",
        "编制",
        staff_quota=16,
        staff_type="吏",
    )

    deputy_e = en(w, "守阙副知", "官职", staff, "总条编制明列守阙副知。")
    deputy_t = tp(
        w,
        deputy_e,
        "南宋初",
        "每名进奏官配备一名守阙副知",
        i,
        staff,
        "公吏",
        "建南宋初守阙副知编制节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        south,
        deputy_t,
        "编制隶属",
        i,
        staff,
        "南宋初每名进奏官配守阙副知一名。",
        "编制",
        staff_type="吏",
    )

    writer_e = fe(w, "书写人", "官职")
    writer_t = tp(
        w,
        writer_e,
        "南宋初（都进奏院）",
        "都进奏院置书写人若干",
        i,
        staff,
        "公吏",
        "建南宋初都进奏院书写人编制节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        south,
        writer_t,
        "编制隶属",
        i,
        staff,
        "南宋初都进奏院置书写人若干。",
        "编制",
        staff_type="吏",
    )
    w.commit()


def entry724():
    i = 724
    main = Q(i)
    aliases = Q(i, "简称")
    w = W(i)
    eid = en(w, "钤辖诸道进奏院", "官职", main, "修复切分后的专条明确为差遣官名。")
    start = ft(w, eid, "北宋太平兴国七年")
    refine(
        w,
        start,
        i,
        main,
        "建钤辖诸道进奏院始置节点。",
        event="由供奉官充，二人；整编诸道进奏官并管辖都进奏院",
        category="差遣官",
        replace_quotation=True,
    )
    end = tp(
        w,
        eid,
        "北宋（都进奏院设监官后，未载年月）",
        "不复置",
        i,
        main,
        "差遣官",
        "建钤辖官被监官取代节点。",
        chain="none",
    )
    ac(w, "Timepoints", start, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    chain(w, [start, end], "连接钤辖诸道进奏院始置与停置节点。")
    rid = relation_id(
        w, "都进奏院", "钤辖诸道进奏院", "编制隶属",
        "北宋太平兴国七年十月二十一日", "北宋太平兴国七年",
    )
    assert rid
    ac(w, "Relationships", rid, i, main, "专条补证钤辖官整编进奏官并管辖都进奏院。")
    w.commit()


def entry725():
    i = 725
    main = Q(i)
    origin = Q(i, "职源")
    duty = Q(i, "职掌")
    grade = Q(i, "官品")
    aliases = Q(i, "简称与别名")
    w = W(i)
    eid = en(w, "监都进奏院", "官职", main, "本条明确为差遣、职事官名。")
    start = retime(
        w,
        ft(w, eid, "北宋（都进奏院改置监官后，未载年月）"),
        "北宋淳化三年",
        "已见监都进奏院官；总掌收发中央与地方文书，二人",
        i,
        origin,
        "差遣官",
        "建监都进奏院最早可考节点。",
        "职源",
    )
    ac(w, "Timepoints", start, i, duty, "补证监都进奏院总掌文书收发职掌。", "职掌")
    ac(w, "Timepoints", start, i, grade, "补证宋前期由京朝官或三班使臣充。", "官品", note="官品")
    yf = tp(
        w,
        eid,
        "北宋元丰改制后",
        "改为职事官，仍为都进奏院长官",
        i,
        main,
        "职事官",
        "建监都进奏院元丰改制节点。",
        chain="none",
    )
    ac(w, "Timepoints", yf, i, aliases, "全文扫描简称别名字段；纯别称不另建实体。", "简称与别名", note="纯别称")
    chain(w, [start, yf], "连接监都进奏院宋前期与元丰节点。")
    rid = relation_id(
        w, "都进奏院", "监都进奏院", "编制隶属",
        "北宋太平兴国七年十月二十一日", "北宋淳化三年",
    )
    assert rid
    ac(w, "Relationships", rid, i, duty, "专条补证监都进奏院总掌文书收发。", "职掌")
    w.commit()


def entry726():
    i = 726
    main = Q(i)
    aliases = Q(i, "简称")
    w = W(i)
    eid = en(w, "勾当都进奏院公事", "官职", main, "本条明确为差遣官名。")
    start = tp(
        w,
        eid,
        "北宋熙宁四年二月",
        "置为提举都进奏院属官，行监官事",
        i,
        main,
        "差遣官",
        "建勾当都进奏院公事始置节点。",
        chain="none",
    )
    end = tp(
        w,
        eid,
        "北宋元丰新制",
        "罢知银台司官提举后不复置",
        i,
        main,
        "差遣官",
        "建勾当都进奏院公事罢置节点。",
        chain="none",
    )
    ac(w, "Timepoints", start, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    chain(w, [start, end], "连接勾当都进奏院公事始置、罢置节点。")
    rel(
        w,
        ft(w, fe(w, "都进奏院", "机构"), "北宋太平兴国七年后（未载具体年月）"),
        start,
        "编制隶属",
        i,
        main,
        "勾当都进奏院公事为提举都进奏院属官。",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def entry727():
    i = 727
    main = Q(i)
    w = W(i)
    eid = en(w, "进奏官", "官职", main, "本条明确为公吏名。")
    early = tp(
        w,
        eid,
        "宋初",
        "隶各节镇、州进奏院，收发本州军与朝廷文书",
        i,
        main,
        "公吏",
        "建进奏官宋初节点。",
        chain="none",
    )
    tp7 = ft(w, eid, "北宋太平兴国七年十月")
    refine(
        w,
        tp7,
        i,
        main,
        "建进奏官归并都进奏院节点。",
        event="简选一百五十人统属都进奏院，可兼管二三州军",
        category="公吏",
        replace_quotation=True,
    )
    rule = tp(
        w,
        eid,
        "北宋大中祥符二年后",
        "改为每逢郊祀大礼许前五名出职为八品武官",
        i,
        main,
        "公吏",
        "建进奏官出职制度变化节点。",
        chain="none",
    )
    later = ft(w, eid, "北宋太平兴国七年后（未载具体年月）")
    yf = ft(w, eid, "北宋元丰新制")
    south = ft(w, eid, "南宋初")
    chain(w, [early, tp7, later, rule, yf, south], "连接进奏官宋初至南宋沿革与改额。")
    rid = relation_id(
        w, "都进奏院", "进奏官", "编制隶属",
        "北宋太平兴国七年十月二十一日", "北宋太平兴国七年十月",
    )
    assert rid
    ac(w, "Relationships", rid, i, main, "专条补证进奏官经整顿后统属都进奏院。")
    w.commit()


def entry728():
    i = 728
    main = Q(i)
    aliases = Q(i, "简称")
    w = W(i)
    eid = en(w, "知后官", "官职", main, "本条明确为公吏名。")
    start = tp(
        w,
        eid,
        "宋初",
        "军监场务及转运司驻京进奏院公吏，职掌同进奏官而地位较低",
        i,
        main,
        "公吏",
        "建知后官宋初节点。",
        chain="none",
    )
    end = tp(
        w,
        eid,
        "北宋太平兴国七年十月",
        "罢知后官之名",
        i,
        main,
        "公吏",
        "建知后官罢名节点。",
        chain="none",
    )
    ac(w, "Timepoints", end, i, aliases, "全文扫描简称字段；纯简称不另建实体。", "简称", note="纯简称")
    chain(w, [start, end], "连接知后官宋初与罢名节点。")
    rel(
        w,
        ft(w, fe(w, "进奏院", "机构"), "宋初"),
        start,
        "编制隶属",
        i,
        main,
        "知后官为宋初军监场务等进奏院公吏。",
        staff_type="吏",
    )
    w.commit()


def entry729():
    i = 729
    main = Q(i)
    aliases = Q(i, "别称")
    w = W(i)
    eid = en(w, "私名副知", "官职", main, "本条明确为进奏院公吏名。")
    start = tp(
        w,
        eid,
        "北宋太平兴国七年十月后",
        "未中选进奏官者改称私名副知，掌抄写文书",
        i,
        main,
        "公吏",
        "建私名副知始置节点。",
        chain="none",
    )
    end = tp(
        w,
        eid,
        "北宋咸平四年九月",
        "改称书写人",
        i,
        main,
        "公吏",
        "建私名副知改名节点。",
        chain="none",
    )
    chain(w, [start, end], "连接私名副知始置与改名节点。")
    writer_e = fe(w, "书写人", "官职")
    writer_t = tp(
        w,
        writer_e,
        "北宋咸平四年九月（都进奏院）",
        "由私名副知改名，掌抄写都进奏院文书",
        i,
        aliases,
        "公吏",
        "建都进奏院书写人改名节点。",
        "别称",
        chain="none",
    )
    rel(w, end, writer_t, "前后演变", i, main, "咸平四年私名副知改称书写人。")
    rel(
        w,
        ft(w, fe(w, "都进奏院", "机构"), "北宋太平兴国七年后（未载具体年月）"),
        start,
        "编制隶属",
        i,
        main,
        "私名副知在都进奏院掌抄写文书。",
        staff_type="吏",
    )
    w.commit()


def entry730():
    i = 730
    main = Q(i)
    w = W(i)
    eid = en(w, "守阙副知", "官职", main, "修复跨页切分后的专条明确为公吏名。")
    tid = tp(
        w,
        eid,
        "北宋咸平四年九月",
        "置为都进奏院进奏官候补人，每名进奏官配一人，非正额",
        i,
        main,
        "公吏",
        "建守阙副知始置节点。",
        chain="none",
    )
    chain(
        w,
        [tid, ft(w, eid, "南宋初")],
        "连接守阙副知咸平始置与南宋初编制节点。",
    )
    rel(
        w,
        ft(w, fe(w, "都进奏院", "机构"), "北宋太平兴国七年后（未载具体年月）"),
        tid,
        "编制隶属",
        i,
        main,
        "守阙副知为都进奏院候补吏，每名进奏官配一人。",
        staff_type="吏",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(711, 731)] == [
        "守当官",
        "守阙守当官",
        "通进司",
        "点检通进司公事",
        "监通进司官",
        "承转承接亲从官",
        "承转承接亲事官",
        "承转承接亲从亲事官",
        "奏禀使臣",
        "主管通进司文字",
        "发敕官",
        "进奏院",
        "都进奏院",
        "钤辖诸道进奏院",
        "监都进奏院",
        "勾当都进奏院公事",
        "进奏官",
        "知后官",
        "私名副知",
        "守阙副知",
    ]
    entry711()
    entry712()
    entry713()
    entry714()
    entry715()
    entries716_718()
    entry719()
    entry720()
    entry721()
    entry722()
    entry723()
    entry724()
    entry725()
    entry726()
    entry727()
    entry728()
    entry729()
    entry730()


if __name__ == "__main__":
    main()
