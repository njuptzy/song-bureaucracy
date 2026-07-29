#!/usr/bin/env python3
"""提取 chapter2t4 第1291–1310条：秘书省馆职、著作局与校读检阅官。"""
import extract_2t4_1271_1290 as x


base = x.base
base.F = {i: base.load(i) for i in range(1291, 1311)}
base.F[1285] = base.load(1285)
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
ft_any = x.ft_any
mark_citation_conflict = base.mark_citation_conflict


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def rename_secretary_assistant(w):
    """把总条预建的同一官职规范到专条标题“秘书丞”上。"""
    old = w.find_entity("秘书省丞", "官职")
    new = w.find_entity("秘书丞", "官职")
    if old and not new:
        w.conn.execute("update Entities set title=? where id=?", ("秘书丞", old))
        w._br(
            "Entities", old,
            "第1294条原书正式词头为“秘书丞”；将第1285条按编制语句预建的"
            "“秘书省丞”规范为同一官职，不另造别名实体。",
        )
        return old
    assert new and (not old or old == new), (old, new)
    return new


def secretary_parent(w, time):
    return ft(w, fe(w, "秘书省", "机构"), time)


def office_staff_relation(w, office_t, post_t, i, quotation, decision,
                          quota=None, staff_type="官"):
    return rel(
        w, office_t, post_t, "编制隶属", i, quotation, decision,
        "编制" if "编制" in F[i]["fields"] else None,
        staff_quota=quota, staff_type=staff_type,
    )


def entry1292():
    i = 1292
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "秘书省少监", "官职")
    sui = tp(
        w, eid, "隋大业三年", "始置秘书省少监",
        i, history, "秘书省副长官", "建立秘书省少监隋代职源节点。",
        "职源与沿革", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "文臣寄禄官阶，无职事；元丰后寄禄阶易朝议大夫",
        i, duty, "文臣寄禄官阶", "建立秘书省少监宋前期节点。",
        "职掌", chain="none", attr_grade="从四品上",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, duty,
        "专条细化元丰秘书省少监职掌。", "职掌",
        event="秘书省副长官，佐监领本省事",
        category="秘书省副长官", grade="从五品",
    )
    abolish = tp(
        w, eid, "南宋建炎三年四月十三日", "随秘书省罢置",
        i, history, "秘书省副长官", "建立秘书省少监建炎罢置节点。",
        "职源与沿革", chain="none",
    )
    restore = tp(
        w, eid, "南宋绍兴元年二月十六日",
        "复置，编制一人，监与少监通常不并置",
        i, history, "秘书省副长官", "建立秘书省少监绍兴复置节点。",
        "职源与沿革", chain="none", attr_grade="从五品",
    )
    for target, quotation, decision, key in (
        (song, grade, "补证宋初品位。", "品位"),
        (reform, grade, "补证元丰后从五品。", "品位"),
        (reform, staff, "补证元丰编制一人。", "编制"),
        (restore, staff, "补证南宋监、少监多不并置。", "编制"),
        (reform, aliases, "简称与别名仅作称谓证据。", "简称与别名"),
        (reform, main, "正文补证元丰前后官制性质变化。", None),
    ):
        cite(w, "Timepoints", target, i, quotation, decision, key)
    chain_all(
        w, eid, [sui, song, reform, abolish, restore],
        "连接秘书省少监隋代至南宋绍兴完整时间链。",
    )
    office_staff_relation(
        w, secretary_parent(w, "宋前期"), song, i, staff,
        "宋前期秘书省少监为寄禄官阶。", quota=1,
    )
    office_staff_relation(
        w, secretary_parent(w, "北宋元丰五年五月"), reform, i, staff,
        "元丰秘书省置少监一人。", quota=1,
    )
    office_staff_relation(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), restore, i, staff,
        "绍兴复置秘书省，监与少监多不并置。",
        quota=1, staff_type="官（监、少监不并置）",
    )
    w.commit()


def collective(i, title, time, instances, *, alias_field=None, category="官职合称"):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}为官职合称。",
                   quotation=main)
    tid = tp(
        w, eid, time, "官职合称",
        i, main, category, f"建立{title}{time}节点。",
    )
    if alias_field:
        cite(
            w, "Timepoints", tid, i, field(i, alias_field),
            f"{title}别名仅作称谓证据。", alias_field, note="纯别名",
        )
    for instance_title, instance_time in instances:
        instance_e = fe(w, instance_title, "官职")
        rel(
            w, tid, ft(w, instance_e, instance_time), "统称与实例",
            i, main, f"{instance_title}是{title}的实例。",
        )
    chain_all(w, eid, [tid], f"确认{title}单节点完整时间链。")
    w.commit()


def entry1294():
    i = 1294
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    staff = field(i, "编制")
    alias = field(i, "简称")
    w = W(i)
    eid = rename_secretary_assistant(w)
    han = tp(
        w, eid, "东汉建安二十年", "置秘书左、右丞，为秘书丞之始",
        i, history, "秘书省佐贰官", "建立秘书丞东汉职源节点。",
        "职源与沿革", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "文臣迁转官阶，无职事；元丰后寄禄阶易奉议郎",
        i, duty, "文臣迁转官阶", "建立秘书丞宋前期节点。",
        "职掌", chain="none", attr_grade="从五品上",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, duty,
        "专条细化元丰秘书丞职掌。", "职掌",
        event="参领秘书省事", category="秘书省佐贰官", grade="从七品",
    )
    abolish = tp(
        w, eid, "南宋建炎三年四月十三日", "随秘书省罢置",
        i, history, "秘书省佐贰官", "建立秘书丞建炎罢置节点。",
        "职源与沿革", chain="none",
    )
    restore = tp(
        w, eid, "南宋绍兴元年二月十六日", "复置，编制一人",
        i, history, "秘书省佐贰官", "建立秘书丞绍兴复置节点。",
        "职源与沿革", chain="none", attr_grade="从七品",
    )
    for target, quotation, decision, key in (
        (song, grade, "补证宋初从五品上。", "品位"),
        (reform, grade, "补证元丰后从七品。", "品位"),
        (reform, staff, "补证编制一人。", "编制"),
        (reform, alias, "简称“秘丞”仅作称谓证据。", "简称"),
        (reform, main, "正文补证元丰前后官制性质变化。", None),
    ):
        cite(w, "Timepoints", target, i, quotation, decision, key)
    chain_all(
        w, eid, [han, song, reform, abolish, restore],
        "连接秘书丞东汉职源至南宋绍兴完整时间链。",
    )
    office_staff_relation(
        w, secretary_parent(w, "宋前期"), song, i, staff,
        "宋前期秘书丞为迁转官阶。", quota=1,
    )
    office_staff_relation(
        w, secretary_parent(w, "北宋元丰五年五月"), reform, i, staff,
        "元丰秘书省置丞一人。", quota=1,
    )
    office_staff_relation(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), restore, i, staff,
        "绍兴复置秘书丞一人。", quota=1,
    )
    w.commit()


def role_entry(i, title, origins, song_grade, reform_grade, reform_event,
               reform_quota, *, shaoxing_quota=None, combined_quota=False):
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade_key = "官品" if "官品" in F[i]["fields"] else "品位"
    grade = field(i, grade_key)
    staff = field(i, "编制")
    alias_key = "简称与别名" if "简称与别名" in F[i]["fields"] else "简称"
    aliases = field(i, alias_key)
    w = W(i)
    eid = fe(w, title, "官职")
    nodes = []
    for time, event in origins:
        nodes.append(tp(
            w, eid, time, event, i, history, "前代职源",
            f"建立{title}{time}职源节点。", "职源与沿革", chain="none",
        ))
    song = tp(
        w, eid, "宋前期", "寄禄官阶，无职事",
        i, duty, "文臣寄禄官阶", f"建立{title}宋前期节点。",
        "职掌", chain="none", attr_grade=song_grade,
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, duty,
        f"专条细化{title}元丰职掌。", "职掌",
        event=reform_event, category="秘书省馆职", grade=reform_grade,
    )
    abolish = tp(
        w, eid, "南宋建炎三年四月十三日", "随秘书省罢置",
        i, history, "秘书省馆职", f"建立{title}建炎罢置节点。",
        "职源与沿革", chain="none",
    )
    restore = tp(
        w, eid, "南宋绍兴元年二月十六日", "随秘书省复置",
        i, history, "秘书省馆职", f"建立{title}绍兴复置节点。",
        "职源与沿革", chain="none", attr_grade=reform_grade,
    )
    shaoxing = None
    if shaoxing_quota is not None:
        event = (
            f"与同组馆职合计十二人"
            if combined_quota else f"增置为{shaoxing_quota}人"
        )
        shaoxing = tp(
            w, eid, "南宋绍兴五年八月三日", event,
            i, staff, "秘书省馆职", f"建立{title}绍兴五年编制节点。",
            "编制", chain="none", attr_grade=reform_grade,
        )
    later = refine(
        w, ft_any(
            w, eid, "北宋元祐以后至南宋", "南宋隆兴二年闰十一月三日"
        ), i, staff,
        f"专条将泛化馆职节点细化为隆兴以后不定员。", "编制",
        time="南宋隆兴二年闰十一月三日",
        event="不立定额", category="秘书省馆职", grade=reform_grade,
    )
    for target, quotation, decision, key in (
        (song, grade, f"补证{title}宋初品位。", grade_key),
        (reform, grade, f"补证{title}元丰后品位。", grade_key),
        (reform, staff, f"补证{title}元丰编制。", "编制"),
        (reform, aliases, f"{title}简称与别名仅作称谓证据。", alias_key),
        (reform, main, f"正文补证{title}隶秘书省及元丰前后性质。", None),
    ):
        cite(w, "Timepoints", target, i, quotation, decision, key)
    ordered = nodes + [song, reform, abolish, restore]
    if shaoxing:
        ordered.append(shaoxing)
    ordered.append(later)
    chain_all(w, eid, ordered, f"重建{title}前代职源至南宋隆兴完整时间链。")
    office_staff_relation(
        w, secretary_parent(w, "宋前期"), song, i, staff,
        f"宋前期{title}为寄禄官阶。",
    )
    reform_rel = office_staff_relation(
        w, secretary_parent(w, "北宋元丰五年五月"), reform, i, staff,
        f"元丰秘书省置{title}{reform_quota}人。", quota=reform_quota,
    )
    office_staff_relation(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), restore, i, history,
        f"绍兴元年秘书省复置{title}。",
    )
    if shaoxing:
        office_staff_relation(
            w, secretary_parent(w, "南宋绍兴五年八月三日"), shaoxing, i, staff,
            f"绍兴五年秘书省调整{title}编制。",
            quota=12 if combined_quota else shaoxing_quota,
            staff_type="官（合计）" if combined_quota else "官",
        )
    office_staff_relation(
        w, secretary_parent(w, "南宋隆兴二年闰十一月三日"), later, i, staff,
        f"隆兴二年以后{title}不立定额。",
        staff_type="官（不定额）",
    )
    return w, reform_rel


def entry1296():
    w, _ = role_entry(
        1296, "著作郎",
        [("东汉", "东观有著作，尚非正式官名"),
         ("西晋元康二年", "中书省著作郎改隶秘书省")],
        "从五品上", "从七品",
        "修时政记、起居注、日历及祭祀祝辞", 1, shaoxing_quota=2,
    )
    w.commit()


def entry1297():
    w, _ = role_entry(
        1297, "秘书郎", [("东汉", "始置秘书郎")],
        "从六品上", "正八品",
        "掌四库经籍图书分类典藏、校刊与抄写", 2, shaoxing_quota=2,
    )
    w.commit()


def entry1298():
    i = 1298
    w, relationship_id = role_entry(
        i, "著作佐郎",
        [("魏晋", "置佐著作郎"),
         ("南朝宋齐以后", "改称著作佐郎")],
        "从六品上", "正八品",
        "佐著作郎修时政记、起居注、日历及祭祀祝辞",
        1, shaoxing_quota=2,
    )
    specialist_staff = field(i, "编制")
    total_staff = field(1285, "编制")
    old_citation_note = (
        "第1285条秘书省总编制记著作佐郎二人；第1298条专条明确元丰新制一人。"
        "两说冲突，结构字段按专条取一人。"
    )
    new_citation_note = (
        "第1298条专条记元丰新制一人；第1285条秘书省总编制记二人。"
        "两说冲突，结构字段按专条取一人。"
    )
    mark_citation_conflict(
        w, "Relationships", relationship_id, 1285, total_staff,
        old_citation_note, "把总条的二人说显式标为冲突。", field="编制",
    )
    mark_citation_conflict(
        w, "Relationships", relationship_id, i, specialist_staff,
        new_citation_note, "把专条的一人说显式标为冲突。", field="编制",
    )
    old_quota = w.conn.execute(
        "select staff_quota from Relationships where id=?", (relationship_id,)
    ).fetchone()[0]
    if old_quota != 1:
        w.conn.execute(
            "update Relationships set staff_quota=1 where id=?",
            (relationship_id,),
        )
        w._br(
            "Relationships", relationship_id,
            f"著作佐郎元丰编制按专条由{old_quota}人细化为1人；"
            "总条二人说与专条一人说均保留并标冲突。",
        )
    w.commit()


def entry1301():
    i = 1301
    main = Q(i, F[i]["text"])
    alias = field(i, "别称")
    w = W(i)
    eid = w.entity("著作局", "机构", "本条直接定义秘书省著作局。",
                   quotation=main)
    tid = tp(
        w, eid, "宋代（具体年月未载）",
        "著作郎、著作佐郎纂修日历、时政记、起居注的公廨",
        i, main, "秘书省所属机构", "建立著作局宋代节点。",
    )
    cite(
        w, "Timepoints", tid, i, alias,
        "别称“著作庭”仅作称谓证据。", "别称", note="纯别称",
    )
    rel(
        w, secretary_parent(w, "北宋元丰五年五月"), tid, "上下级机构",
        i, main, "著作局是秘书省公廨之一。",
    )
    for title in ("著作郎", "著作佐郎"):
        rel(
            w, tid, ft(w, fe(w, title, "官职"), "北宋元丰五年五月"),
            "编制隶属", i, main, f"{title}在著作局主持纂修。",
            staff_type="官",
        )
    w.commit()


def entry1307():
    i = 1307
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("秘阁校勘", "官职", "本条直接定义秘阁校勘职事官。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋绍定元年正月",
        "始置，校勘秘书省文字或参与修史，无品",
        i, main, "秘书省馆职", "建立秘阁校勘绍定始置节点。",
        attr_officer_type="选人资序", attr_grade="无品",
    )
    earlier = [
        row[0] for row in w.conn.execute(
            "select id from Timepoints where entity_id=? and id<>? order by id",
            (eid, tid),
        )
    ]
    chain_all(
        w, eid, earlier + [tid],
        "连接秘阁校勘北宋馆职旧节点与南宋绍定新置职事官节点。",
    )
    rel(
        w, secretary_parent(w, "南宋绍熙以后"), tid, "编制隶属",
        i, main, "秘阁校勘隶秘书省。",
        staff_type="官",
    )
    w.commit()


def entry1306():
    i = 1306
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "馆职", "官职")
    tid = refine(
        w, ft(w, eid, "北宋元祐以后至南宋"), i, main,
        "专条补证元丰改制后秘书省正字以上省官也称馆职。",
        event="秘书省正字以上省官的通称",
        category="秘书省官属统称",
    )
    ordered_times = (
        "北宋元丰改制前", "北宋元丰五年", "北宋元祐元年三月",
        "北宋政和六年九月", "北宋元祐以后至南宋",
    )
    chain_all(
        w, eid, [ft(w, eid, time) for time in ordered_times],
        "保持馆职从旧馆阁职到秘书省馆职的完整既有时间链。",
    )
    for title in ("著作郎", "秘书郎", "著作佐郎", "校书郎", "正字"):
        instance_t = ft(
            w, fe(w, title, "官职"), "南宋隆兴二年闰十一月三日"
        )
        rel(
            w, tid, instance_t, "统称与实例", i, main,
            f"元丰改制后{title}属于秘书省馆职。",
        )
    w.commit()


def temporary_post(i, title, start_time, start_event, *, end_time=None,
                   end_event=None, parent_time="北宋元丰五年五月",
                   alias_field="简称"):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}。",
                   quotation=main)
    start = tp(
        w, eid, start_time, start_event,
        i, main, "秘书省特置官", f"建立{title}始置节点。",
        chain="none",
    )
    if alias_field in F[i]["fields"]:
        cite(
            w, "Timepoints", start, i, field(i, alias_field),
            f"{title}简称仅作称谓证据。", alias_field, note="纯简称",
        )
    nodes = [start]
    if end_time:
        end = tp(
            w, eid, end_time, end_event,
            i, main, "秘书省特置官", f"建立{title}罢置节点。",
            chain="none",
        )
        nodes.append(end)
    chain_all(w, eid, nodes, f"连接{title}完整时间链。")
    rel(
        w, secretary_parent(w, parent_time), start, "编制隶属",
        i, main, f"{title}隶秘书省。",
        staff_type="官",
    )
    w.commit()


def entry1310():
    i = 1310
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity("秘书省检阅文字", "官职",
                   "本条直接定义秘书省检阅文字。", quotation=main)
    north = tp(
        w, eid, "北宋（具体年月未载）",
        "会要所检阅文字，不执笔",
        i, main, "秘书省检阅官", "建立北宋检阅文字节点。",
        chain="none",
    )
    south = tp(
        w, eid, "南宋（具体年月未载）",
        "秘书省检阅文字，执笔修书，亦有布衣召入充任者",
        i, main, "秘书省检阅官", "建立南宋检阅文字节点。",
        chain="none",
    )
    cite(
        w, "Timepoints", south, i, alias,
        "简称“秘书省检阅”仅作称谓证据。", "简称", note="纯简称",
    )
    chain_all(w, eid, [north, south], "连接检阅文字北宋与南宋节点。")
    rel(
        w, secretary_parent(w, "宋前期"), north, "编制隶属",
        i, main, "北宋会要所已有检阅文字。",
        staff_type="官",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), south,
        "编制隶属", i, main, "南宋秘书省置检阅文字。",
        staff_type="官",
    )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1291, 1311)] == [
        "秘书省", "秘书省少监", "秘书监少", "秘书丞", "秘书少丞",
        "著作郎", "秘书郎", "著作佐郎", "著作郎佐", "秘书丞郎",
        "著作局", "校书郎", "石渠郎", "正字", "校正", "馆职",
        "秘阁校勘", "秘书省校对黄本书籍", "秘书省读书",
        "秘书省检阅文字",
    ]
    assert F[1291]["fields"].get("__status__") == "placeholder"
    entry1292()
    collective(
        1293, "秘书监少", "南宋绍兴元年二月十九日",
        [("秘书省监", "南宋绍兴元年二月十六日"),
         ("秘书省少监", "南宋绍兴元年二月十六日")],
        alias_field="别名",
    )
    entry1294()
    collective(
        1295, "秘书少丞", "南宋绍兴五年八月三日",
        [("秘书省少监", "南宋绍兴元年二月十六日"),
         ("秘书丞", "南宋绍兴元年二月十六日")],
    )
    entry1296()
    entry1297()
    entry1298()
    collective(
        1299, "著作郎佐", "宋代（具体年月未载）",
        [("著作郎", "北宋元丰五年五月"),
         ("著作佐郎", "北宋元丰五年五月")],
        alias_field="简称",
    )
    collective(
        1300, "秘书丞郎", "宋代（具体年月未载）",
        [("秘书丞", "北宋元丰五年五月"),
         ("秘书郎", "北宋元丰五年五月")],
    )
    entry1301()
    w, _ = role_entry(
        1302, "校书郎",
        [("两汉", "他官兼校书之职，尚非正式官名"),
         ("北魏", "始置秘书校书郎")],
        "正九品", "从八品",
        "与正字编辑、校正图籍", 4,
        shaoxing_quota=12, combined_quota=True,
    )
    w.commit()
    collective(
        1303, "石渠郎", "宋代（具体年月未载）",
        [("秘书郎", "北宋元丰五年五月"),
         ("著作郎", "北宋元丰五年五月"),
         ("著作佐郎", "北宋元丰五年五月"),
         ("校书郎", "北宋元丰五年五月")],
    )
    w, _ = role_entry(
        1304, "正字", [("北齐", "始置秘书省正字")],
        "正九品下", "从八品",
        "与校书郎编辑、校正图籍", 2,
        shaoxing_quota=12, combined_quota=True,
    )
    w.commit()
    collective(
        1305, "校正", "宋代（具体年月未载）",
        [("校书郎", "北宋元丰五年五月"),
         ("正字", "北宋元丰五年五月")],
    )
    entry1306()
    entry1307()
    temporary_post(
        1308, "秘书省校对黄本书籍",
        "北宋元祐五年六月四日",
        "始置，校对秘阁黄纸抄本供皇帝阅读",
        end_time="北宋绍圣元年四月二日", end_event="罢置",
        parent_time="北宋元丰五年五月",
    )
    temporary_post(
        1309, "秘书省读书",
        "南宋淳熙二年十一月十一日",
        "始置，授童科召试合格神童，给选人阶、俸禄与照护军兵",
        parent_time="南宋隆兴二年闰十一月三日",
    )
    entry1310()


if __name__ == "__main__":
    main()
