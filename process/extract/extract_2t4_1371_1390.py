#!/usr/bin/env python3
"""提取 chapter2t4 第1371–1390条：司天监差遣、五官正与技术官。"""
import extract_2t4_1351_1370 as x


base = x.base
base.F = {i: base.load(i) for i in range(1371, 1391)}
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


def monitor_parent(w):
    return ft(w, fe(w, "司天监", "机构"), "北宋端拱元年九月")


def alias_citation(w, tid, i, key="简称"):
    cite(
        w, "Timepoints", tid, i, field(i, key),
        f"{F[i]['title']}称谓仅作名称证据。", key, note="纯简称或别名",
    )


def simple_dispatch(i, title, event, *, time="北宋（司天监时期）",
                    extra_time=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}差遣。",
                   quotation=main)
    current = tp(
        w, eid, time, event,
        i, main, "司天监差遣", f"建立{title}{time}节点。",
        attr_officer_type="差遣", chain="none",
    )
    alias_citation(w, current, i)
    nodes = [current]
    if extra_time:
        origin = tp(
            w, eid, extra_time, f"{extra_time}已有{title}",
            i, main, "司天监差遣", f"建立{title}{extra_time}职源节点。",
            attr_officer_type="差遣", chain="none",
        )
        nodes.insert(0, origin)
    chain_all(w, eid, nodes, f"连接{title}完整时间链。")
    rel(
        w, monitor_parent(w), current, "编制隶属",
        i, main, f"{title}领司天监事务。",
        staff_type="差遣",
    )
    w.commit()


def entry1373():
    i = 1373
    main = Q(i, F[i]["text"])
    duty = field(i, "职掌")
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "提举司天监公事", "官职", "本条直接定义提举司天监公事差遣。",
        quotation=main,
    )
    tid = tp(
        w, eid, "北宋熙宁六年六月",
        "大两省官领司天监事，位高于知、判监事；除占候密奏外指挥其余公事",
        i, main, "司天监提举差遣", "建立提举司天监公事熙宁节点。",
        attr_officer_type="差遣",
    )
    cite(w, "Timepoints", tid, i, duty, "补证提举官指挥范围。", "职掌")
    cite(
        w, "Timepoints", tid, i, alias,
        "简称“提举司天监”仅作称谓证据。", "简称", note="纯简称",
    )
    rel(
        w, monitor_parent(w), tid, "编制隶属",
        i, main, "提举司天监公事领司天监事务。",
        staff_type="差遣",
    )
    w.commit()


def entry1374():
    i = 1374
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "同提举司天监公事", "官职",
        "本条直接定义同提举司天监公事差遣。",
        quotation=main,
    )
    tid = tp(
        w, eid, "北宋熙宁七年六月二十一日",
        "京官充提举者带同字，位次提举司天监",
        i, main, "司天监提举差遣", "建立同提举司天监公事熙宁节点。",
        attr_officer_type="差遣",
    )
    cite(
        w, "Timepoints", tid, i, alias,
        "简称“同提举司天监、同提举官”仅作称谓证据。",
        "简称", note="纯简称",
    )
    rel(
        w, monitor_parent(w), tid, "编制隶属",
        i, main, "同提举司天监公事领司天监事务。",
        staff_type="差遣",
    )
    w.commit()


def entry1376():
    i = 1376
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "提举司天监公事所", "机构",
        "本条直接定义提举司天监公事官治事厅。",
        quotation=main,
    )
    active = tp(
        w, eid, "北宋熙宁六年六月以后",
        "提举官治事厅，统领司天监官属及公事，可直达奏闻",
        i, main, "司天监上级机构", "建立提举司天监公事所北宋节点。",
        chain="none",
    )
    cite(
        w, "Timepoints", active, i, alias,
        "简称“提举所”仅作称谓证据。", "简称", note="纯简称",
    )
    end = tp(
        w, eid, "北宋元丰五年", "元丰改制后罢置",
        i, main, "司天监上级机构", "建立提举司天监公事所罢置节点。",
        chain="none",
    )
    chain_all(w, eid, [active, end], "连接提举司天监公事所设置与罢置节点。")
    rel(
        w, active, monitor_parent(w), "上下级机构",
        i, main, "提举司天监公事所统领司天监官属及公事。",
    )
    post_t = ft(
        w, fe(w, "提举司天监公事", "官职"), "北宋熙宁六年六月"
    )
    rel(
        w, active, post_t, "编制隶属", i, main,
        "提举司天监公事官在提举所治事。",
        staff_type="差遣",
    )
    w.commit()


def entry1377():
    i = 1377
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    staff = field(i, "编制")
    alias = field(i, "简称")
    w = W(i)
    eid = fe(w, "司天监少监", "官职")
    origin = tp(
        w, eid, "五代十国", "已有司天少监",
        i, history, "司天监副长官", "建立司天监少监五代职源节点。",
        "职源与沿革", chain="none",
    )
    current = refine(
        w, ft(w, eid, "北宋端拱元年九月以后"), i, duty,
        "专条细化司天监少监职掌。", "职掌",
        event="佐大监领天文历法；官品高不常除，多由他官兼知、权知",
        category="司天监副长官", grade="从四品下",
    )
    cite(w, "Timepoints", current, i, grade, "补证从四品下及位次。", "品位")
    cite(w, "Timepoints", current, i, staff, "补证或置一员。", "编制")
    cite(
        w, "Timepoints", current, i, alias,
        "简称“少监”仅作称谓证据。", "简称", note="纯简称",
    )
    end = tp(
        w, eid, "北宋元丰五年", "随司天监罢置",
        i, history, "司天监副长官", "建立司天监少监元丰罢置节点。",
        "职源与沿革", chain="none",
    )
    chain_all(w, eid, [origin, current, end], "连接司天监少监五代至元丰节点。")
    relation_id = rel(
        w, monitor_parent(w), current, "编制隶属",
        i, staff, "司天监少监或置一员。", "编制",
        staff_quota=1, staff_type="技术官",
    )
    old = w.conn.execute(
        "select staff_quota from Relationships where id=?", (relation_id,)
    ).fetchone()[0]
    if old != 1:
        w.conn.execute(
            "update Relationships set staff_quota=1,staff_type='技术官' where id=?",
            (relation_id,),
        )
        w._br(
            "Relationships", relation_id,
            f"据少监专条将总条未载的员额 {old} 细化为一员。",
        )
    w.commit()


def entry1379():
    i = 1379
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    alias = field(i, "简称")
    w = W(i)
    eid = fe(w, "司天监丞", "官职")
    han = tp(
        w, eid, "汉代", "有太史丞",
        i, history, "前代职源", "建立司天监丞汉代职源节点。",
        "职源与沿革", chain="none",
    )
    tang = tp(
        w, eid, "唐贞观元年", "始置浑仪监丞，后改司天台不置丞",
        i, history, "前代职源", "建立司天监丞唐代职源节点。",
        "职源与沿革", chain="none",
    )
    current = refine(
        w, ft(w, eid, "北宋端拱元年九月以后"), i, duty,
        "专条细化司天监丞职掌。", "职掌",
        event="依所能临时差充造历法或测验浑仪",
        category="司天监技术官", grade="正七品",
    )
    cite(w, "Timepoints", current, i, grade, "补证正七品及位次。", "品位")
    cite(
        w, "Timepoints", current, i, alias,
        "简称“监丞”仅作称谓证据。", "简称", note="纯简称",
    )
    successor = successor_role(w, i, "太史局丞", "太史局技术官", history)
    chain_all(w, eid, [han, tang, current], "连接司天监丞前代职源与北宋节点。")
    rel(
        w, current, successor, "前后演变", i, history,
        "元丰新制司天监丞改为太史局丞。",
        "职源与沿革",
    )
    w.commit()


def entry1380():
    i = 1380
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    alias = field(i, "别名")
    w = W(i)
    eid = fe(w, "司天监主簿", "官职")
    current_id = (
        w.find_timepoint(eid, "北宋端拱元年九月以后")
        or w.find_timepoint(eid, "北宋开宝九年十一月")
    )
    assert current_id, eid
    current = refine(
        w, current_id, i, history,
        "专条将司天监主簿细化到见置之始。", "职源与沿革",
        time="北宋开宝九年十一月",
        event="马韶破格擢为司天监主簿，为监簿见置之始",
        category="司天监技术官", grade="从七品下",
    )
    cite(w, "Timepoints", current, i, duty, "补证天文官职掌。", "职掌")
    cite(w, "Timepoints", current, i, grade, "补证从七品下及位次。", "品位")
    cite(
        w, "Timepoints", current, i, alias,
        "别名仅作称谓证据。", "别名", note="纯别名",
    )
    end = tp(
        w, eid, "北宋元丰五年", "司天监改太史局后不置主簿",
        i, history, "司天监技术官", "建立司天监主簿元丰不置节点。",
        "职源与沿革", chain="none",
    )
    chain_all(w, eid, [current, end], "连接司天监主簿始置与元丰不置节点。")
    w.commit()


def successor_role(w, i, title, event, quotation, source_field="职源与沿革"):
    bureau_e = fe(w, "太史局", "机构")
    eid = w.entity(title, "官职", f"本条明确元丰新制改为{title}。",
                   quotation=quotation)
    tid = tp(
        w, eid, "北宋元丰五年五月", event,
        i, quotation, "太史局官属", f"建立{title}元丰节点。",
        source_field, attr_officer_type="技术官",
    )
    rel(
        w, ft(w, bureau_e, "北宋元丰五年五月"), tid, "编制隶属",
        i, quotation, f"{title}隶太史局。", source_field,
        staff_type="技术官",
    )
    return tid


def entry1381():
    i = 1381
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "司天监五官正", "官职", "本条直接定义五官正合称。",
        quotation=main,
    )
    tang = tp(
        w, eid, "唐乾元元年", "始置五官正，隶司天台",
        i, history, "天文官合称", "建立司天监五官正唐代职源节点。",
        "职源与沿革", chain="none", attr_grade="正五品",
    )
    song = tp(
        w, eid, "北宋（司天监时期）",
        "春、夏、中、秋、冬官正合称；观习天文、占候风气，可兼判监事",
        i, duty, "司天监技术官合称", "建立司天监五官正北宋节点。",
        "职掌", chain="none", attr_grade="正五品",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋初沿唐正五品及位次。", "品位")
    cite(
        w, "Timepoints", song, i, alias,
        "简称仅作称谓证据。", "简称", note="纯简称",
    )
    chain_all(w, eid, [tang, song], "连接五官正唐代与北宋节点。")
    successor = successor_role(
        w, i, "太史局五官正", "太史局五官正合称", history
    )
    rel(
        w, song, successor, "前后演变", i, history,
        "元丰五年司天监五官正改为太史局五官正。",
        "职源与沿革",
    )
    for title in (
        "司天监春官正", "司天监夏官正", "司天监中官正",
        "司天监秋官正", "司天监冬官正",
    ):
        rel(
            w, song, ft(w, fe(w, title, "官职"), "北宋端拱元年九月以后"),
            "统称与实例", i, main,
            f"{title}是司天监五官正的实例。",
        )
    w.commit()


def five_official(i, title, successor_title):
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = fe(w, title, "官职")
    current = refine(
        w, ft(w, eid, "北宋端拱元年九月以后"), i, main,
        f"专条细化{title}。", None,
        event="司天监五官正之一，元丰五年改太史局同名官",
        category="司天监五官正", officer="技术官",
    )
    cite(
        w, "Timepoints", current, i, alias,
        f"{title}简称仅作称谓证据。", "简称", note="纯简称",
    )
    successor = successor_role(
        w, i, successor_title, "太史局五官正之一", main, None
    )
    chain_all(w, eid, [current], f"确认{title}单节点完整时间链。")
    rel(
        w, current, successor, "前后演变", i, main,
        f"元丰五年{title}改为{successor_title}。",
    )
    w.commit()


def technical_post(i, title, origins, duty_event, grade_value, successor_title):
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    alias = field(i, "简称") if "简称" in F[i]["fields"] else None
    w = W(i)
    eid = fe(w, title, "官职")
    nodes = []
    for time, event in origins:
        nodes.append(tp(
            w, eid, time, event,
            i, history, "前代职源", f"建立{title}{time}职源节点。",
            "职源与沿革", chain="none",
        ))
    current = refine(
        w, ft(w, eid, "北宋端拱元年九月以后"), i, duty,
        f"专条细化{title}职掌。", "职掌",
        event=duty_event, category="司天监技术官", grade=grade_value,
    )
    cite(w, "Timepoints", current, i, grade, f"补证{title}品位。", "品位")
    if alias:
        cite(
            w, "Timepoints", current, i, alias,
            f"{title}简称仅作称谓证据。", "简称", note="纯简称",
        )
    successor = successor_role(
        w, i, successor_title, f"{successor_title}技术官", history
    )
    chain_all(w, eid, nodes + [current], f"连接{title}前代职源与北宋节点。")
    rel(
        w, current, successor, "前后演变", i, history,
        f"元丰五年{title}改为{successor_title}。",
        "职源与沿革",
    )
    w.commit()


def entry1390():
    i = 1390
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "司天监官", "官职", "本条直接定义司天监差遣、技术官总称。",
        quotation=main,
    )
    tid = tp(
        w, eid, "北宋（司天监时期）",
        "自判监以下至挈壶正等差遣、技术官的总称，不含监生、学生等人吏",
        i, main, "司天监官属统称", "建立司天监官北宋节点。",
        attr_officer_type="差遣、技术官",
    )
    cite(
        w, "Timepoints", tid, i, alias,
        "简称“监官”仅作称谓证据。", "简称", note="纯简称",
    )
    for title in (
        "判司天监事", "同判司天监事", "权判司天监事",
        "司天监丞", "司天监主簿", "司天监五官正",
        "司天监春官正", "司天监夏官正", "司天监中官正",
        "司天监秋官正", "司天监冬官正", "司天监灵台郎",
        "司天监保章正", "司天监挈壶正",
    ):
        target_e = fe(w, title, "官职")
        target_time = (
            "北宋（司天监时期）"
            if title in ("判司天监事", "同判司天监事", "权判司天监事",
                         "司天监五官正")
            else (
                "北宋开宝九年十一月"
                if title == "司天监主簿"
                else "北宋端拱元年九月以后"
            )
        )
        rel(
            w, tid, ft(w, target_e, target_time), "统称与实例",
            i, main, f"{title}属于司天监官总称。",
        )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1371, 1391)] == [
        "权判司天监事", "知司天监事", "提举司天监公事",
        "同提举司天监公事", "同提举官", "提举司天监公事所",
        "司天监少监", "权知司天监少监事", "司天监丞",
        "司天监主簿", "司天监五官正", "司天监春官正",
        "司天监夏官正", "司天监中官正", "司天监秋官正",
        "司天监冬官正", "司天监灵台郎", "司天监保章正",
        "司天监挈壶正", "司天监官",
    ]
    assert F[1375]["fields"].get("__status__") == "placeholder"
    simple_dispatch(1371, "权判司天监事", "权代判司天监事，位次判监事")
    simple_dispatch(
        1372, "知司天监事",
        "监、少监阙时由五官正等日官权代，位次监、少监，高于判监事",
        extra_time="五代十国",
    )
    entry1373()
    entry1374()
    entry1376()
    entry1377()
    simple_dispatch(
        1378, "权知司天监少监事",
        "少监阙时由他官兼充，位次少监、高于判监事",
    )
    entry1379()
    entry1380()
    entry1381()
    five_official(1382, "司天监春官正", "太史局春官正")
    five_official(1383, "司天监夏官正", "太史局夏官正")
    five_official(1384, "司天监中官正", "太史局中官正")
    five_official(1385, "司天监秋官正", "太史局秋官正")
    five_official(1386, "司天监冬官正", "太史局冬官正")
    technical_post(
        1387, "司天监灵台郎",
        [("东汉", "有灵台丞"),
         ("唐长安四年", "浑仪监置灵台郎，乾元元年称五官灵台郎")],
        "候察天象、教习学生", "正八品下", "太史局灵台郎",
    )
    technical_post(
        1388, "司天监保章正",
        [("先秦《周礼》", "已有保章氏之名"),
         ("北周", "春官府置保章上士、中士"),
         ("唐长安四年", "改历博士为保章正")],
        "掌历法，测验晷影与分至表准", "从八品上", "太史局保章正",
    )
    technical_post(
        1389, "司天监挈壶正",
        [("先秦《周礼》", "有挈壶氏"),
         ("唐长安二年", "始置挈壶正")],
        "掌漏刻时辰", "从八品下", "太史局挈壶正",
    )
    entry1390()


if __name__ == "__main__":
    main()
