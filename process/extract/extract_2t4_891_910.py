#!/usr/bin/env python3
"""提取 chapter2t4 第891–910条：御营余项、御营宿卫使司、修政局与制国用使。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(891, 911)}
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine


def entry891():
    i = 891
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营使司左军都统制",
        "官职",
        "本条直接定义御营使司左军都统制。",
        quotation=main,
    )
    tp(
        w,
        eid,
        "南宋建炎年间",
        "御营司统兵官；任官者武阶升为节度使时，在统制前加“都”字",
        i,
        main,
        "统兵武官",
        "条目所在御营使司制度段落属于建炎年间；照录加“都”字的任职形态，不把个人升阶误写为官名改置。",
    )
    w.commit()


def entry892():
    i = 892
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营使司右军都统制",
        "官职",
        "本条直接定义御营使司右军都统制。",
        quotation=main,
    )
    tp(
        w,
        eid,
        "南宋初",
        "御营司统兵官；任官者武阶升为节度使时，在统制前加“都”字",
        i,
        main,
        "统兵武官",
        "沿用本组右军统制官专条明确的南宋初制度语境；不把个人升阶误写为官名改置。",
    )
    w.commit()


def entry893():
    i = 893
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "御营使司平寇左将军",
        "官职",
        "本条直接定义御营使司平寇左将军这一加官。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "宋代（御营使司）",
        "加授御营左军统制，以示尊宠",
        i,
        main,
        "武官加官",
        "原文未载具体年月，只按御营使司的宋代制度语境建立节点。",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段同时保存该加官的史料用例；“将军”为简称，不另建实体。",
        "简称",
        note="纯简称",
    )
    w.commit()


def entry894():
    i = 894
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营使司平寇前将军",
        "官职",
        "本条直接定义御营使司平寇前将军这一加官。",
        quotation=main,
    )
    tp(
        w,
        eid,
        "宋代（御营使司）",
        "加授御营使司同都统制，以示尊宠",
        i,
        main,
        "武官加官",
        "原文未载具体年月，只按御营使司的宋代制度语境建立节点。",
    )
    w.commit()


def entry895():
    i = 895
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营使司主管机宜文字",
        "官职",
        "本条直接定义御营使司主管机宜文字。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "宋代（御营使司）",
        "掌管军中机密文书",
        i,
        main,
        "军事幕职",
        "原文未载具体年月，按所属御营使司的宋代制度语境建立节点。",
    )
    rel(
        w,
        ft(w, fe(w, "御营使司", "机构"), "南宋建炎元年五月八日"),
        tid,
        "编制隶属",
        i,
        main,
        "原文明确称其为御营司属官；无独立关系年月，按规则连接所属机构首个南宋真实节点。",
        staff_type="官",
    )
    w.commit()


def entry896():
    i = 896
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营使司激赏库",
        "机构",
        "本条直接定义御营使司激赏库。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "宋代（御营使司）",
        "供颁降军中文书、烽火急奏及派遣间谍等费用；每料银五百两、钱一千贯，奉皇帝画旨支用",
        i,
        main,
        "军事经费库",
        "原文未载具体年月，按御营使司的宋代制度语境建立节点。",
    )
    rel(
        w,
        ft(w, fe(w, "御营使司", "机构"), "南宋建炎元年五月八日"),
        tid,
        "上下级机构",
        i,
        main,
        "条目正式名称及库的专用职能表明该库属于御营使司；无独立关系年月，连接所属机构首个南宋真实节点。",
    )
    w.commit()


def entry897():
    i = 897
    name = Q(i, "官署名。")
    history = Q(
        i,
        "绍兴三十一年十月二十四日置司，罢于绍兴三十二年五月十二日",
        "职源与沿革",
    )
    duty = Q(
        i,
        "为应付高宗亲临长江防线督阵，临时而设，"
        "不复与建炎初擅掌兵柄的御营使司相比",
        "职能",
    )
    staff = Q(
        i,
        "统御营宿卫五军（先锋、前军、右军、中军、左军）共四万余人，"
        "设御营宿卫使、统制官等。",
        "编制",
    )
    w = W(i)
    eid = w.entity(
        "御营宿卫使司",
        "机构",
        "本条直接定义御营宿卫使司。",
        quotation=name,
    )
    start = tp(
        w,
        eid,
        "南宋绍兴三十一年十月二十四日",
        "置司，为高宗亲临长江防线督阵而临时设置；统御营宿卫五军四万余人",
        i,
        history,
        "临时军事指挥机构",
        "建立御营宿卫使司始置节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证临时设置的目的。", "职能")
    cite(w, "Timepoints", start, i, staff, "补证统领五军及其编制。", "编制")
    end = tp(
        w,
        eid,
        "南宋绍兴三十二年五月十二日",
        "罢置",
        i,
        history,
        "临时军事指挥机构",
        "建立御营宿卫使司罢置节点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接御营宿卫使司始置、罢置两节点。")
    w.commit()


def entry898():
    i = 898
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "御营宿卫使",
        "官职",
        "修复切分后，本条直接定义御营宿卫使。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋绍兴三十一年十月二十四日",
        "始置，以和义郡王杨沂中任职，统领御营五军",
        i,
        main,
        "高级统兵武官",
        "建立御营宿卫使始置节点。",
    )
    rid = rel(
        w,
        ft(
            w,
            fe(w, "御营宿卫使司", "机构"),
            "南宋绍兴三十一年十月二十四日",
        ),
        tid,
        "编制隶属",
        i,
        main,
        "御营宿卫使统领御营五军，是御营宿卫使司长官；原文未明示员额，不填写 staff_quota。",
        staff_type="官",
    )
    w.commit()

    staff = Q(
        897,
        "统御营宿卫五军（先锋、前军、右军、中军、左军）共四万余人，"
        "设御营宿卫使、统制官等。",
        "编制",
    )
    w897 = W(897)
    cite(
        w897,
        "Relationships",
        rid,
        897,
        staff,
        "御营宿卫使司总条的编制字段直接补证该司设置御营宿卫使。",
        "编制",
    )
    w897.commit()


def entry899():
    _entry_host_guard(899, "御营宿卫使司先锋军都统制", "统率先锋军兵马")


def entry900():
    _entry_host_guard(900, "御营宿卫使司前军都统制", "统率前军兵马")


def entry901():
    _entry_host_guard(901, "御营宿卫使司右军统制", "统率右军兵马")


def entry902():
    _entry_host_guard(902, "御营宿卫使司左军统制", "统率左军兵马")


def entry903():
    _entry_host_guard(903, "御营宿卫使司中军统制", "统率中军兵马")


def _entry_host_guard(i, title, event):
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        title,
        "官职",
        f"本条直接定义{title}。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋绍兴年间（御营宿卫使司）",
        event,
        i,
        main,
        "统兵武官",
        "原文未载具体年月，按御营宿卫使司的绍兴年间制度语境建立节点。",
    )
    if i in (901, 902, 903):
        aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
        cite(
            w,
            "Timepoints",
            tid,
            i,
            aliases,
            "简称字段含任职史料用例；纯简称不另建实体。",
            "简称",
            note="纯简称",
        )
    rel(
        w,
        ft(
            w,
            fe(w, "御营宿卫使司", "机构"),
            "南宋绍兴三十一年十月二十四日",
        ),
        tid,
        "编制隶属",
        i,
        main,
        f"原文明确{title}为御营宿卫使司五军长官之一；不另造五军载体实体，未明示员额，不填写 staff_quota。",
        staff_type="官",
    )
    w.commit()


def entry904():
    _entry_host_staff(
        904,
        "御营宿卫使司随军都转运使",
        "负责筹措并及时供应御营五军兵马给养",
    )


def entry905():
    _entry_host_staff(
        905,
        "御营宿卫使司书写机宜文字",
        "掌本司上奏、下发军政文书的草拟",
    )


def _entry_host_staff(i, title, event):
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        title,
        "官职",
        f"本条直接定义{title}。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋绍兴年间（御营宿卫使司）",
        event,
        i,
        main,
        "军事属官",
        "原文未载具体年月，按御营宿卫使司的绍兴年间制度语境建立节点；不臆造完整起止范围。",
    )
    rel(
        w,
        ft(
            w,
            fe(w, "御营宿卫使司", "机构"),
            "南宋绍兴三十一年十月二十四日",
        ),
        tid,
        "编制隶属",
        i,
        main,
        f"原文明确{title}为御营宿卫使司属官；未明示员额，不填写 staff_quota。",
        staff_type="官",
    )
    w.commit()


def entry906():
    i = 906
    name = Q(i, "京局名。宰执官兼领")
    history = Q(
        i,
        "绍兴二年五月二十七日于尚书都省置局，"
        "同年九月二日因彗星出而罢",
        "职源与沿革",
    )
    duty = Q(
        i,
        "令百官条陈政事利弊得失，省并司局。以修内政；"
        "并督修车马、器械，以外御入侵之敌",
        "职能",
    )
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    w = W(i)
    eid = w.entity(
        "修政局",
        "机构",
        "本条直接定义修政局。",
        quotation=name,
    )
    start = tp(
        w,
        eid,
        "南宋绍兴二年五月二十七日",
        "于尚书都省置局，由宰执官兼领；令百官条陈利弊、省并司局并督修军备",
        i,
        history,
        "临时中央政务机构",
        "建立修政局始置节点；“于尚书都省置局”保留在事件中，不强解为上下级机构关系。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, name, "补证修政局由宰执官兼领。")
    cite(w, "Timepoints", start, i, duty, "补证修政局内政与军备职能。", "职能")
    end = tp(
        w,
        eid,
        "南宋绍兴二年九月二日",
        "因彗星出现而罢",
        i,
        history,
        "临时中央政务机构",
        "建立修政局罢置节点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接修政局始置、罢置两节点。")

    role_specs = (
        ("提举修政局", 1, "官"),
        ("同提举修政局", 1, "官"),
        ("修政局参详官", 1, "官"),
        ("修政局参议官", 2, "官"),
        ("修政局检讨官", 4, "官"),
        ("修政局检阅文字", 2, "吏"),
        ("修政局主管文字", 4, "吏"),
        ("修政局书写文字", 4, "吏"),
    )
    for title, quota, staff_type in role_specs:
        role_e = w.entity(
            title,
            "官职",
            f"修政局编制字段明列{title.removeprefix('修政局')}。",
            quotation=staff,
        )
        role_t = tp(
            w,
            role_e,
            "南宋绍兴二年五月二十七日",
            f"修政局始置编制，{quota}人",
            i,
            staff,
            "修政局官吏",
            f"修政局始置条的编制字段明示{title}{quota}人。",
            "编制",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            staff,
            f"修政局编制明示{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )
    w.commit()


def entry907():
    i = 907
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "提举修政局", "官职")
    refine(
        w,
        ft(w, eid, "南宋绍兴二年五月二十七日"),
        i,
        main,
        "专条补证提举修政局由右相兼领。",
        event="修政局始置编制一人，由尚书右仆射、同中书门下平章事兼领",
        category="兼官",
        officer="宰相兼",
    )
    w.commit()


def entry908():
    i = 908
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "同提举修政局", "官职")
    refine(
        w,
        ft(w, eid, "南宋绍兴二年五月二十七日"),
        i,
        main,
        "专条补证同提举修政局由资浅执政兼任。",
        event="修政局始置编制一人，由参知政事等资浅执政兼任",
        category="兼官",
        officer="执政兼",
    )
    w.commit()


def entry909():
    i = 909
    name = Q(i, "宰相兼官名。")
    history = Q(
        i,
        "乾道二年（1166）十二月二十二日始以宰相带"
        "（《中兴圣政》卷29）。五年二月二十二日罢",
        "职源与沿革",
    )
    duty = Q(i, "以宰相兼总制国家钱谷出纳大纲", "职掌")
    w = W(i)
    eid = w.entity(
        "制国用使",
        "官职",
        "本条直接定义制国用使。",
        quotation=name,
    )
    start = tp(
        w,
        eid,
        "南宋乾道二年十二月二十二日",
        "始置，以宰相兼任，总制国家钱谷出纳大纲",
        i,
        history,
        "财政兼官",
        "建立制国用使始置节点。",
        "职源与沿革",
        chain="none",
        attr_officer_type="宰相兼",
    )
    cite(w, "Timepoints", start, i, duty, "补证制国用使职掌。", "职掌")
    end = tp(
        w,
        eid,
        "南宋乾道五年二月二十二日",
        "罢置",
        i,
        history,
        "财政兼官",
        "建立制国用使罢置节点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接制国用使始置、罢置两节点。")
    w.commit()


def entry910():
    i = 910
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "同知国用事",
        "官职",
        "本条直接定义同知国用事，并明确其余制度沿用制国用使条。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "南宋乾道二年十二月二十二日",
        "始置，由参知政事兼任，佐宰相总领国家财赋大纲",
        i,
        main,
        "财政兼官",
        "本条明言“余与制国用使同”，据其明确跳转沿用制国用使始置时间。",
        chain="none",
        attr_officer_type="参知政事兼",
    )
    end = tp(
        w,
        eid,
        "南宋乾道五年二月二十二日",
        "随制国用使罢置",
        i,
        main,
        "财政兼官",
        "本条明言“余与制国用使同”，据其明确跳转沿用制国用使罢置时间。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接同知国用事随制国用使始置、罢置两节点。")
    w.commit()

    # 第910条只给出明确跳转；具体日期实际写在第909条，必须把实际出处挂回两节点。
    source = Q(
        909,
        "乾道二年（1166）十二月二十二日始以宰相带"
        "（《中兴圣政》卷29）。五年二月二十二日罢",
        "职源与沿革",
    )
    w909 = W(909)
    for tid, event in ((start, "始置"), (end, "罢置")):
        audit = (
            f"显式跳转补证：第910条“余与制国用使同”，"
            f"第909条提供同知国用事沿用的{event}日期。"
        )
        cite(
            w909,
            "Timepoints",
            tid,
            909,
            source,
            f"第910条明确称其余与制国用使同；第909条是{event}日期的实际出处。",
            "职源与沿革",
        )
        exists = w909.conn.execute(
            "select 1 from BuildRecords where target_table='Timepoints' "
            "and target_id=? and source_entry=? and source_page=? and decision=?",
            (tid, x.b.F[909]["title"], x.b.F[909]["page"], audit),
        ).fetchone()
        if not exists:
            w909._br("Timepoints", tid, audit)
    w909.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(891, 911)] == [
        "御营使司左军都统制",
        "御营使司右军都统制",
        "御营使司平寇左将军",
        "御营使司平寇前将军",
        "御营使司主管机宜文字",
        "御营使司激赏库",
        "御营宿卫使司",
        "御营宿卫使",
        "御营宿卫使司先锋军都统制",
        "御营宿卫使司前军都统制",
        "御营宿卫使司右军统制",
        "御营宿卫使司左军统制",
        "御营宿卫使司中军统制",
        "御营宿卫使司随军都转运使",
        "御营宿卫使司书写机宜文字",
        "修政局",
        "提举修政局",
        "同提举修政局",
        "制国用使",
        "同知国用事",
    ]
    entry891()
    entry892()
    entry893()
    entry894()
    entry895()
    entry896()
    entry897()
    entry898()
    entry899()
    entry900()
    entry901()
    entry902()
    entry903()
    entry904()
    entry905()
    entry906()
    entry907()
    entry908()
    entry909()
    entry910()


if __name__ == "__main__":
    main()
