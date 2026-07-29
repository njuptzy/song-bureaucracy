#!/usr/bin/env python3
"""提取 chapter2t4 第1391–1410条：司天监生徒、三科与科内官属。"""
import extract_2t4_1371_1390 as x


base = x.base
base.F = {i: base.load(i) for i in range(1391, 1411)}
F = base.F
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def ft_any(w, entity_id, *times):
    for time in times:
        tid = w.find_timepoint(entity_id, time)
        if tid:
            return tid
    raise AssertionError((entity_id, times))


def monitor_parent(w):
    return ft(w, fe(w, "司天监", "机构"), "北宋端拱元年九月")


def alias_citation(w, tid, i):
    if "简称" not in F[i]["fields"]:
        return
    cite(
        w, "Timepoints", tid, i, field(i, "简称"),
        f"{F[i]['title']}的简称仅作称谓证据。",
        "简称", note="纯简称或别名",
    )


def set_staff_attrs(w, relationship_id, quota, staff_type, decision):
    old = w.conn.execute(
        "select staff_quota,staff_type from Relationships where id=?",
        (relationship_id,),
    ).fetchone()
    assert old, relationship_id
    new = (
        quota if quota is not None else old[0],
        staff_type if staff_type is not None else old[1],
    )
    if tuple(old) != new:
        w.conn.execute(
            "update Relationships set staff_quota=?,staff_type=? where id=?",
            (*new, relationship_id),
        )
        w._br(
            "Relationships", relationship_id,
            f"{decision} staff_quota {old[0]}->{new[0]}、"
            f"staff_type {old[1]}->{new[1]}。",
        )


def entry1391():
    i = 1391
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "司天监礼生", "官职")
    origin = tp(
        w, eid, "唐代", "始置礼生",
        i, main, "前代职源", "建立司天监礼生唐代职源节点。",
        chain="none",
    )
    current = refine(
        w, ft(w, eid, "北宋端拱元年九月以后"), i, main,
        "专条细化司天监礼生职掌与员额。",
        event="供司天监行遣文字，编制五人",
        category="司天监吏人", officer="吏",
    )
    chain_all(w, eid, [origin, current], "连接司天监礼生唐代职源与北宋节点。")
    rid = rel(
        w, monitor_parent(w), current, "编制隶属",
        i, main, "司天监置礼生五人。",
        staff_quota=5, staff_type="吏",
    )
    set_staff_attrs(w, rid, 5, "吏", "据礼生专条补足五人员额。")
    w.commit()


def entry1392():
    i = 1392
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "司天监历生", "官职")
    origin = tp(
        w, eid, "隋代", "始置历生",
        i, main, "前代职源", "建立司天监历生隋代职源节点。",
        chain="none",
    )
    current = refine(
        w, ft(w, eid, "北宋端拱元年九月以后"), i, main,
        "专条细化司天监历生职掌。",
        event="学习历法并供司天监行遣文字",
        category="司天监吏人", officer="吏",
    )
    chain_all(w, eid, [origin, current], "连接司天监历生隋代职源与北宋节点。")
    rel(
        w, monitor_parent(w), current, "编制隶属",
        i, main, "历生在司天监学习历法并行遣文字。",
        staff_type="吏",
    )
    w.commit()


def entry1393():
    i = 1393
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "司天监监生", "官职")
    current = refine(
        w,
        ft_any(
            w, eid,
            "北宋端拱元年九月以后",
            "北宋景德二年六月二十七日",
        ),
        i, main, "专条将司天监监生始置时间细化到景德二年六月二十七日。",
        time="北宋景德二年六月二十七日",
        event="始置；选司天监学生中考试优秀、精熟历算者充任，月给俸钱，无定员",
        category="司天监吏人", officer="吏",
    )
    alias_citation(w, current, i)
    chain_all(w, eid, [current], "确认司天监监生单节点完整时间链。")
    rel(
        w, monitor_parent(w), current, "编制隶属",
        i, main, "景德二年始置司天监监生，无定员。",
        staff_type="吏",
    )
    w.commit()


def entry1395():
    i = 1395
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "司天监学生", "官职")
    current = refine(
        w, ft(w, eid, "北宋端拱元年九月以后"), i, main,
        "专条细化司天监学生所学、待遇及递迁。",
        event="分科学习天文、历算、三式；考试录取，月支食钱而无俸给，试优者迁监生",
        category="司天监生徒", officer="学生",
    )
    alias_citation(w, current, i)
    chain_all(w, eid, [current], "确认司天监学生单节点完整时间链。")
    rid = rel(
        w, monitor_parent(w), current, "编制隶属",
        i, main, "学生在司天监分科学习。",
        staff_type="学生",
    )
    set_staff_attrs(w, rid, None, "学生", "据学生专条将官属类型细化为学生。")
    rel(
        w, current,
        ft(
            w, fe(w, "司天监监生", "官职"),
            "北宋景德二年六月二十七日",
        ),
        "前后演变", i, main,
        "司天监学生考试优等者可迁为监生。",
    )
    w.commit()


def science_office(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        title, "机构", f"第{i}条直接定义{title}为司天监所属机构。",
        quotation=main,
    )
    tid = tp(
        w, eid, "北宋（司天监时期）", event,
        i, main, "司天监教学机构", f"建立{title}北宋节点。",
    )
    alias_citation(w, tid, i)
    rel(
        w, monitor_parent(w), tid, "上下级机构",
        i, main, f"{title}为司天监所属机构。",
    )
    w.commit()


def dispatch_post(i, title, office_title, specialty):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        title, "官职", f"第{i}条直接定义{title}差遣。",
        quotation=main,
    )
    active = tp(
        w, eid, "北宋治平三年五月以后",
        f"由司天监官充任；为补偿罢兼监诸仓库、草场门后的收入而增设，"
        f"于{specialty}职事无实际补益",
        i, main, f"{office_title}差遣", f"建立{title}治平增设节点。",
        attr_officer_type="差遣", chain="none",
    )
    end = tp(
        w, eid, "北宋元丰五年六月十六日", "罢置",
        i, main, f"{office_title}差遣", f"建立{title}元丰罢置节点。",
        attr_officer_type="差遣", chain="none",
    )
    chain_all(w, eid, [active, end], f"连接{title}增设与罢置节点。")
    rel(
        w,
        ft(w, fe(w, office_title, "机构"), "北宋（司天监时期）"),
        active, "编制隶属",
        i, main, f"{title}名义隶属{office_title}。",
        staff_type="差遣",
    )
    w.commit()


def technical_post(i, title, office_title, event, *, officer="技术官"):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        title, "官职", f"第{i}条直接定义{title}技术官。",
        quotation=main,
    )
    tid = tp(
        w, eid, "北宋（司天监时期）", event,
        i, main, f"{office_title}技术官", f"建立{title}北宋节点。",
        attr_officer_type=officer,
    )
    alias_citation(w, tid, i)
    rel(
        w,
        ft(w, fe(w, office_title, "机构"), "北宋（司天监时期）"),
        tid, "编制隶属",
        i, main, f"{title}隶属{office_title}。",
        staff_type=officer,
    )
    w.commit()


def entry1406():
    i = 1406
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(
        "司天监三式科", "机构",
        "本条直接定义司天监三式科为司天监所属阴阳卜筮教学机构。",
        quotation=main,
    )
    tid = tp(
        w, eid, "北宋（司天监时期）",
        "习学阴阳卜筮并传授生徒；含六壬、太乙、遁甲三专业，严禁民间私习",
        i, main, "司天监教学机构", "建立司天监三式科北宋节点。",
    )
    alias_citation(w, tid, i)
    rel(
        w, monitor_parent(w), tid, "上下级机构",
        i, main, "三式科为司天监所属机构。",
    )
    for title, event in (
        ("司天监三式科六壬", "三式科六壬专业"),
        ("司天监三式科太乙", "三式科太乙专业"),
        ("司天监三式科遁甲", "三式科遁甲专业"),
    ):
        child_e = w.entity(
            title, "官职", f"三式科条明确列举{title.removeprefix('司天监三式科')}专业。",
            quotation=main,
        )
        child_t = tp(
            w, child_e, "北宋（司天监时期）", event,
            i, main, "司天监三式技术官", f"建立{title}北宋专业节点。",
            attr_officer_type="技术官",
        )
        rel(
            w, tid, child_t, "编制隶属",
            i, main, f"{title}为司天监三式科专业。",
            staff_type="技术官",
        )
    w.commit()


def entry1410():
    i = 1410
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "司天监三式科六壬", "官职")
    tid = refine(
        w, ft(w, eid, "北宋（司天监时期）"), i, main,
        "专条细化司天监三式科六壬职掌。",
        event="用六壬占卜天时",
        category="司天监三式技术官", officer="技术官",
    )
    alias_citation(w, tid, i)
    chain_all(w, eid, [tid], "确认司天监三式科六壬单节点完整时间链。")
    rel(
        w,
        ft(w, fe(w, "司天监三式科", "机构"), "北宋（司天监时期）"),
        tid, "编制隶属",
        i, main, "司天监三式科六壬隶属三式科。",
        staff_type="技术官",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1391, 1411)] == [
        "司天监礼生", "司天监历生", "司天监监生", "历算",
        "司天监学生", "司天监历算科", "司天监历算科令",
        "司天监历算科丞", "司天监历算科主簿", "司天监历算",
        "司天监天文科", "司天监天文科令", "司天监天文科丞",
        "司天监天文科主簿", "司天监天文官", "司天监三式科",
        "司天监三式科令", "司天监三式科丞", "司天监三式科主簿",
        "司天监三式科六壬",
    ]
    assert F[1394]["fields"].get("__status__") == "placeholder"
    entry1391()
    entry1392()
    entry1393()
    entry1395()
    science_office(
        1396, "司天监历算科",
        "习学天文算术、造历并传授历算生徒",
    )
    dispatch_post(1397, "司天监历算科令", "司天监历算科", "历算")
    dispatch_post(1398, "司天监历算科丞", "司天监历算科", "历算")
    dispatch_post(1399, "司天监历算科主簿", "司天监历算科", "历算")
    technical_post(
        1400, "司天监历算", "司天监历算科", "推步历算",
    )
    science_office(
        1401, "司天监天文科",
        "习学观测日月星辰、风云变化以占吉凶并传授生徒",
    )
    dispatch_post(1402, "司天监天文科令", "司天监天文科", "天文")
    dispatch_post(1403, "司天监天文科丞", "司天监天文科", "天文")
    dispatch_post(1404, "司天监天文科主簿", "司天监天文科", "天文")
    technical_post(
        1405, "司天监天文官", "司天监天文科",
        "观测天象并教授生徒",
    )
    entry1406()
    dispatch_post(1407, "司天监三式科令", "司天监三式科", "三式")
    dispatch_post(1408, "司天监三式科丞", "司天监三式科", "三式")
    dispatch_post(1409, "司天监三式科主簿", "司天监三式科", "三式")
    entry1410()


if __name__ == "__main__":
    main()
