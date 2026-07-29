#!/usr/bin/env python3
"""提取 chapter2t4 第871–890条：尚书都省吏与御营使司系统。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(871, 891)}
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine
relation_id = x.relation_id
set_rel_attrs = x.b.set_rel_attrs
mark_citation_conflict = x.b.mark_citation_conflict
current_chain = x.current_chain


def append_to_chain(w, entity_id, timepoint_id, decision, *, after_id=None):
    ordered = current_chain(w, entity_id)
    if timepoint_id in ordered:
        return
    if after_id is None:
        ordered.append(timepoint_id)
    else:
        ordered.insert(ordered.index(after_id) + 1, timepoint_id)
    chain_all(w, entity_id, ordered, decision)


def entry871_872():
    for i, title in ((871, "手分"), (872, "书奏")):
        main = Q(i, x.b.F[i]["text"])
        w = W(i)
        eid = fe(w, title, "官职")
        existing = current_chain(w, eid)
        tid = tp(
            w, eid, "宋代（尚书都省，未载具体年月）",
            (
                "隶尚书省都司，主行试补本省吏人并考定都事以下功过"
                if title == "手分"
                else "隶尚书省都司，职掌同手分，试补吏人并考定功过"
            ),
            i, main, "吏职", f"建{title}在尚书都省的职掌节点。",
            chain="none",
        )
        # 两条均为宋代都省吏；置于既有泛宋节点之后、南宋专门节点之前。
        if tid not in existing:
            insert_at = 1 if title == "手分" else 0
            existing.insert(insert_at, tid)
        chain_all(w, eid, existing, f"把尚书都省{title}节点接入既有全局时间链。")
        rel(
            w,
            ft(w, fe(w, "尚书都省", "机构"), "北宋元丰五年十月十七日"),
            tid, "编制隶属", i, main, f"{title}隶尚书省都司。",
            staff_type="吏",
        )
        w.commit()


def entry873_core():
    i = 873
    origin = Q(
        i,
        "唐天祐元年(904)正月始置（《通鉴》卷264）。"
        "南宋建炎元年（1127）五月八日置，四年六月四日罢。"
        "隆兴元年（1162）六月复置，隆兴元年（1163）十月罢。",
        "职源",
    )
    duty = Q(
        i,
        "南宋初，三衙禁旅废弛，行在诸军不相统一，"
        "为加强对扈从诸军的统一指挥，特设本司，一度独擅兵柄",
        "职能",
    )
    w = W(i)
    eid = fe(w, "御营使司", "机构")
    tang = tp(
        w, eid, "唐天祐元年正月", "始置",
        i, origin, "军事指挥机构", "建御营使司唐代源流节点。",
        "职源", chain="none",
    )
    start = tp(
        w, eid, "南宋建炎元年五月八日",
        "置，统一指挥行在扈从诸军，一度独擅兵柄",
        i, origin, "中央军事指挥机构", "建南宋御营使司始置节点。",
        "职源", chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证建炎初设置背景与职能。", "职能")
    stop = w.find_timepoint(eid, "南宋建炎四年六月四日")
    if stop is None:
        stop = ft(w, eid, "南宋建炎四年六月")
    stop = refine(
        w, stop, i, origin,
        "专条细化御营使司建炎四年罢置确日。", "职源",
        time="南宋建炎四年六月四日", event="罢置，随后并入枢密院为机速房",
        category="中央军事指挥机构",
    )
    restore = tp(
        w, eid, "南宋隆兴元年（1162）六月", "复置",
        i, origin, "中央军事指挥机构", "照录辞典纪年建立隆兴复置节点。",
        "职源", chain="none",
    )
    end = tp(
        w, eid, "南宋隆兴元年（1163）十月", "罢置",
        i, origin, "中央军事指挥机构", "照录辞典纪年建立隆兴罢置节点。",
        "职源", chain="none",
    )
    note = "同一字段把隆兴元年分别括注为1162、1163，原样保留，待史料校核。"
    mark_citation_conflict(
        w, "Timepoints", restore, i, origin, note,
        "保留辞典纪年与公元年内部不一致。", "职源",
    )
    mark_citation_conflict(
        w, "Timepoints", end, i, origin, note,
        "保留辞典纪年与公元年内部不一致。", "职源",
    )
    chain_all(w, eid, [tang, start, stop, restore, end],
              "连接御营使司唐代源流及南宋两次置罢节点。")
    w.commit()


def entry874():
    i = 874
    origin = Q(
        i,
        "五代后晋天福八年(943)已有御营使之名",
        "职源与沿革",
    )
    duty = Q(i, "总齐行在五军政令，及有关边防措置等事", "职掌")
    grade = Q(i, "以宰相兼领", "品位")
    w = W(i)
    eid = w.entity(
        "御营使", "官职", "修复切分后的专条明确为兼官名。",
        quotation=Q(i, "御营使 兼官名。"),
    )
    source = tp(
        w, eid, "五代后晋天福八年", "已有御营使之名",
        i, origin, "官名源流", "建御营使五代源流节点。",
        "职源与沿革", chain="none",
    )
    south = tp(
        w, eid, "南宋建炎元年五月八日",
        "以宰相兼领，总齐行在五军政令及边防措置",
        i, duty, "兼官", "据御营使司始置时间建南宋御营使节点。",
        "职掌", chain="none", attr_officer_type="宰相兼领",
    )
    cite(w, "Timepoints", south, i, grade, "补证以宰相兼领。", "品位")
    chain_all(w, eid, [source, south], "连接御营使五代源流与南宋兼领节点。")
    w.commit()


def entry875():
    i = 875
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营副使", "官职", "本条明确为御营使副贰兼官。",
        quotation=main,
    )
    tp(
        w, eid, "南宋建炎元年五月",
        "初置，为御营使副贰，由执政官兼",
        i, main, "兼官", "建御营副使始置节点。",
        attr_officer_type="执政官兼",
    )
    w.commit()


def entry876():
    i = 876
    main = Q(i, x.b.F[i]["text"])
    dated = Q(
        i,
        "御营参赞军事（《宋史·高宗纪》2，建炎二年十二月）。",
        "简称",
    )
    w = W(i)
    eid = w.entity(
        "御营司参赞军事", "官职",
        "本条明确为御营使司属官。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋建炎二年十二月",
        "佐御营使司长贰谋议军事、教习将士，以侍从官兼",
        i, dated, "军事参谋官", "简称字段给出建炎二年在置事实。",
        "简称", attr_officer_type="侍从官兼",
    )
    cite(w, "Timepoints", tid, i, main, "补证参赞军事职掌。")
    w.commit()


def entry877():
    i = 877
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营司参议官", "官职",
        "本条明确为御营使司属官。",
        quotation=main,
    )
    tp(
        w, eid, "南宋建炎年间",
        "佐本司长贰或都统制谋议军政，或统兵，位次参赞军事",
        i, main, "军事参谋官",
        "御营使司仅在建炎年间首度运行，按机构上下文建立本条节点。",
    )
    w.commit()


def entry878():
    i = 878
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "提举御营使司一行事务", "官职",
        "本条明确为御营使司属官。",
        quotation=main,
    )
    tp(
        w, eid, "南宋建炎年间",
        "由大将兼任，总领御营使司事务",
        i, main, "军事长官",
        "据御营使司建炎存续期建立提举一行事务节点。",
        attr_officer_type="大将兼",
    )
    w.commit()


def entry879():
    i = 879
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "御营使司都统制司", "机构",
        "本条明确为御营司都统制所设军事指挥机构。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋建炎年间",
        "都统制所设军事指挥机构，下设前、后、中、左、右五军",
        i, main, "军事指挥机构",
        "按御营使司首度存续期建立都统制司节点。",
    )
    cite(w, "Timepoints", tid, i, aliases,
         "全文扫描简称字段；都统司为简称，不另建实体。", "简称",
         note="纯简称")
    rel(
        w, ft(w, fe(w, "御营使司", "机构"), "南宋建炎元年五月八日"),
        tid, "上下级机构", i, main, "御营使司下设都统制司。",
    )

    army_tps = {}
    for name in ("前军", "后军", "中军", "左军", "右军"):
        title = f"御营使司{name}"
        army_e = w.entity(
            title, "机构", f"都统制司专条明列{name}。",
            quotation=main,
        )
        army_t = tp(
            w, army_e, "南宋建炎年间", "御营使司五军之一",
            i, main, "军事编制机构", f"建御营使司{name}节点。",
        )
        rel(w, tid, army_t, "上下级机构", i, main,
            f"御营使司{name}隶都统制司。")
        army_tps[name] = army_t
    w.commit()


def entry880_882():
    i = 880
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营使司都统制", "官职",
        "修复切分后的专条明确为统领御营五军的武官。",
        quotation=main,
    )
    tp(
        w, eid, "南宋建炎元年五月八日",
        "统领御营五军的军事长官",
        i, main, "高级武官",
        "据御营使司始置及总条一员编制建立都统制节点。",
    )
    w.commit()

    i = 881
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营使司同都统制", "官职",
        "本条明确为统领御营五军的武官。",
        quotation=main,
    )
    tp(
        w, eid, "南宋建炎元年七月",
        "统领御营五军，位次都统制、提举一行事务，位在副都统制之上",
        i, main, "高级武官", "建同都统制建炎元年七月节点。",
    )
    w.commit()

    i = 882
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "御营使司副都统制", "官职",
        "本条明确为都统司副长官。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋建炎年间", "都统司副长官",
        i, main, "高级武官",
        "据御营使司建炎存续期建立副都统制节点。",
    )
    cite(w, "Timepoints", tid, i, aliases,
         "全文扫描简称字段；御营副都统制为简称，不另建实体。",
         "简称", note="纯简称")
    w.commit()


def entry883():
    i = 883
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营都副统制", "官职",
        "本条明确为御营使司都统制、副都统制连称。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋建炎年间",
        "御营使司都统制、副都统制连称",
        i, main, "职官统称", "建御营都副统制连称节点。",
    )
    rel(
        w, tid,
        ft(w, fe(w, "御营使司都统制", "官职"), "南宋建炎元年五月八日"),
        "统称与实例", i, main, "御营使司都统制为连称实例。",
    )
    rel(
        w, tid,
        ft(w, fe(w, "御营使司副都统制", "官职"), "南宋建炎年间"),
        "统称与实例", i, main, "御营使司副都统制为连称实例。",
    )
    w.commit()


def entry884_core():
    i = 884
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    eid = w.entity(
        "御营五军统制军马官", "官职",
        "本条明确为御营五军各军统制官的统称。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋建炎年间",
        "前、后、中、左、右五军统制官统称，每军一员、统一万人",
        i, main, "武官统称", "建御营五军统制军马官统称节点。",
    )
    cite(w, "Timepoints", tid, i, aliases,
         "全文扫描简称字段；纯简称不另建实体。", "简称与别名",
         note="纯简称")
    w.commit()


def entry885_889():
    specs = (
        (885, "御营使司前军统制官", "前军", "统制前军兵马"),
        (886, "御营使司后军统制官", "后军", "统制后军兵马"),
        (887, "御营使司左军统制官", "左军", "统率左军兵马"),
        (888, "御营使司右军统制官", "右军", "统率右军兵马"),
        (889, "御营使司中军统制官", "中军", "统率中军兵马"),
    )
    for i, title, army, event in specs:
        main = Q(i, x.b.F[i]["text"])
        w = W(i)
        eid = w.entity(title, "官职", f"本条明确为御营使司{army}统制武官。",
                       quotation=main)
        time = "南宋初" if i in (888, 889) else "南宋建炎年间"
        tid = tp(
            w, eid, time, event,
            i, main, "统兵武官", f"建{title}节点。",
        )
        if i == 889:
            aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
            cite(w, "Timepoints", tid, i, aliases,
                 "全文扫描简称字段；纯简称不另建实体。", "简称",
                 note="纯简称")
        rel(
            w,
            ft(w, fe(w, f"御营使司{army}", "机构"), "南宋建炎年间"),
            tid, "编制隶属", i, main,
            f"御营使司{army}置统制官一员。",
            staff_quota=1, staff_type="官",
        )
        w.commit()


def entry884_relations():
    i = 884
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    group_t = ft(w, fe(w, "御营五军统制军马官", "官职"), "南宋建炎年间")
    for title, time in (
        ("御营使司前军统制官", "南宋建炎年间"),
        ("御营使司后军统制官", "南宋建炎年间"),
        ("御营使司中军统制官", "南宋初"),
        ("御营使司左军统制官", "南宋建炎年间"),
        ("御营使司右军统制官", "南宋初"),
    ):
        rel(
            w, group_t, ft(w, fe(w, title, "官职"), time),
            "统称与实例", i, main, f"{title}为御营五军统制军马官实例。",
        )
    w.commit()


def entry890():
    i = 890
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营使司都统司统领", "官职",
        "本条明确为都统司或五军所属统领武官。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋建炎年间",
        "或直隶都统制，或分隶前、后、左、右、中军，位次统制官",
        i, main, "统兵武官",
        "据御营使司建炎存续期建立都统司统领节点。",
    )
    rel(
        w,
        ft(w, fe(w, "御营使司都统制司", "机构"), "南宋建炎年间"),
        tid, "编制隶属", i, main, "都统司可直辖统领官。",
        staff_type="官",
    )
    for army in ("前军", "后军", "左军", "右军", "中军"):
        rel(
            w, ft(w, fe(w, f"御营使司{army}", "机构"), "南宋建炎年间"),
            tid, "编制隶属", i, main, f"{army}可置所属统领官。",
            staff_type="官",
        )
    w.commit()


def entry873_staff():
    i = 873
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    w = W(i)
    institute = ft(w, fe(w, "御营使司", "机构"), "南宋建炎元年五月八日")
    specs = (
        ("御营使", "南宋建炎元年五月八日", None),
        ("御营副使", "南宋建炎元年五月", None),
        ("御营司参赞军事", "南宋建炎二年十二月", None),
        ("提举御营使司一行事务", "南宋建炎年间", None),
        ("御营使司都统制", "南宋建炎元年五月八日", 1),
    )
    for title, time, quota in specs:
        rel(
            w, institute, ft(w, fe(w, title, "官职"), time),
            "编制隶属", i, staff, f"御营使司总条编制明列{title}。",
            "编制", staff_quota=quota, staff_type="官",
        )
    rel(
        w, institute,
        ft(w, fe(w, "御营五军统制军马官", "官职"), "南宋建炎年间"),
        "编制隶属", i, staff,
        "御营使司总五军，每军置统制官一员。",
        "编制", staff_quota=5, staff_type="官",
    )
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(871, 891)] == [
        "手分",
        "书奏",
        "御营使司",
        "御营使",
        "御营副使",
        "御营司参赞军事",
        "御营司参议官",
        "提举御营使司一行事务",
        "御营使司都统制司",
        "御营使司都统制",
        "御营使司同都统制",
        "御营使司副都统制",
        "御营都副统制",
        "御营五军统制军马官",
        "御营使司前军统制官",
        "御营使司后军统制官",
        "御营使司左军统制官",
        "御营使司右军统制官",
        "御营使司中军统制官",
        "御营使司都统司统领",
    ]
    entry871_872()
    entry873_core()
    entry874()
    entry875()
    entry876()
    entry877()
    entry878()
    entry879()
    entry880_882()
    entry883()
    entry884_core()
    entry885_889()
    entry884_relations()
    entry890()
    entry873_staff()


if __name__ == "__main__":
    main()
