#!/usr/bin/env python3
"""提取 chapter2t4 第831–850条：尚书省诸房、长官、丞与统称。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(831, 851)}
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
mark_citation_conflict = x.b.mark_citation_conflict


def repair_formal_titles():
    for i, old, new, proof in (
        (
            838,
            "尚书左仆射",
            "尚书省左仆射",
            Q(838, "①尚书左仆射。全称应为尚书省左仆射。", "简称与别名"),
        ),
        (
            839,
            "尚书右仆射",
            "尚书省右仆射",
            Q(839, "①尚书右仆射。全称应为尚书省右仆射。", "简称与别名"),
        ),
    ):
        w = W(i)
        eid = fe(w, old, "官职")
        assert w.find_entity(new, "官职") is None
        w.conn.execute(
            "update Entities set title=?,quotation=? where id=?",
            (new, proof, eid),
        )
        w._br(
            "Entities", eid,
            f"据专条“全称应为”将{old}原位规范为正式全称{new}，保留ID、关系与追溯。",
        )
        w.commit()


def entry831_833():
    for i in range(831, 834):
        main = Q(i, x.b.F[i]["text"])
        title = x.b.F[i]["title"]
        w = W(i)
        eid = w.entity(title, "机构", f"据专条建立{title}。", quotation=main)
        tid = tp(
            w, eid, "北宋元丰新制", main, i, main,
            "尚书省办事部门", f"建{title}元丰职掌节点。",
        )
        rel(
            w, ft(w, fe(w, "尚书省", "机构"), "北宋元丰新制"), tid,
            "上下级机构", i, main, f"{title}为尚书省办事部门。",
        )
        w.commit()


def entry834():
    i = 834
    main = Q(i, x.b.F[i]["text"])
    duty = Q(
        i,
        "中书门下批状送印，领都省事，及集议定谥、掌百官受誓戒等。",
        "职掌",
    )
    quota = Q(
        i,
        "三品以上官或学士院翰林学士兼充。",
        "官品",
    )
    w = W(i)
    eid = w.entity(
        "权判尚书都省事", "官职",
        "据专条建立宋前期权判尚书都省的差遣。",
        quotation=main,
    )
    tid = tp(
        w, eid, "宋前期", "以三品以上官或翰林学士一员兼充，领都省事",
        i, quota, "差遣官", "建权判尚书都省事节点。",
    )
    cite(w, "Timepoints", tid, i, duty, "专条补证领都省、定谥与誓戒职掌。", "职掌")
    rel(
        w, ft(w, fe(w, "尚书都省", "机构"), "北宋元丰五年十月十七日"),
        tid, "编制隶属", i, quota,
        "权判尚书都省事为都省长官差遣，通常一员。",
        "官品", staff_quota=1, staff_type="官",
    )
    w.commit()


def entry835_836():
    i = 836
    office = Q(i, x.b.F[i]["text"])
    w = W(i)
    office_e = w.entity(
        "行在尚书省", "机构",
        "据专条建立皇帝巡幸时随驾临时设置的尚书省。",
        quotation=office,
    )
    office_t = tp(
        w, office_e, "北宋巡幸、封禅期间",
        "随驾临时设置，负责祠祀前誓百官等事务",
        i, office, "临时中央机构", "建行在尚书省随驾节点。",
    )
    rel(
        w, ft(w, fe(w, "尚书省", "机构"), "宋前期"), office_t,
        "上下级机构", i, office,
        "行在尚书省是尚书省随驾时临时设置的对应机构。",
    )
    w.commit()

    i = 835
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "权判行在尚书省", "官职",
        "据专条建立临时权判行在尚书省差遣。",
        quotation=main,
    )
    tid = tp(
        w, eid, "北宋大中祥符四年", "祀汾阴时以翰林学士晁迥权判",
        i, main, "临时差遣", "建权判行在尚书省实例节点。",
    )
    rel(
        w, ft(w, office_e, "北宋巡幸、封禅期间"), tid,
        "编制隶属", i, main,
        "行在尚书省临时设置权判官。",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry837():
    i = 837
    history = Q(
        i,
        "秦、汉时已有尚书令之名，为少府属官",
        "职源与沿革",
    )
    changes = Q(
        i,
        "北宋沿设。政和二年九月二十五日罢"
        "（《宋诏令》卷163《三公辅弼手诏》）。宣和七年四月二十七日复置"
        "（《宋会要·职官》1之42、43）。南宋乾道八年二月六日，罢置",
        "职源与沿革",
    )
    early = Q(
        i,
        "① 宋前期为亲王加官，不预政事，起阶官作用。或用作大臣赠官。不单拜除",
        "职掌",
    )
    reform = Q(
        i,
        "② 元丰新制，为尚书省长官，仍虚设而已",
        "职掌",
    )
    grade = Q(i, "官品为正一品。", "品位")
    w = W(i)
    eid = fe(w, "尚书令", "官职")
    qin = tp(
        w, eid, "秦汉", "为少府属官，已有尚书令之名", i, history,
        "官名源流", "建尚书令秦汉源流节点。", "职源与沿革", chain="none",
    )
    song = refine(
        w, ft(w, eid, "宋代（未载具体年月）"), i, early,
        "专条细化宋前期尚书令为不预政事的加官、赠官。", "职掌",
        time="宋前期", event="亲王加官或大臣赠官，不预政事，不单拜除",
        category="加官、赠官", grade="正一品",
    )
    cite(w, "Timepoints", song, i, grade, "专条补证正一品。", "品位")
    yuanfeng = tp(
        w, eid, "北宋元丰新制", "名为尚书省长官，实际虚设", i, reform,
        "职事官名", "建元丰尚书令虚设节点。", "职掌",
        chain="none", attr_grade="正一品",
    )
    stop = tp(
        w, eid, "北宋政和二年九月二十五日", "罢置", i, changes,
        "职事官名", "建政和尚书令罢置节点。", "职源与沿革",
        chain="none", attr_grade="正一品",
    )
    restore = tp(
        w, eid, "北宋宣和七年四月二十七日", "复置", i, changes,
        "职事官名", "建宣和尚书令复置节点。", "职源与沿革",
        chain="none", attr_grade="正一品",
    )
    end = refine(
        w, ft(w, eid, "南宋乾道八年二月"), i, changes,
        "专条细化乾道罢置确日。", "职源与沿革",
        time="南宋乾道八年二月六日", event="罢置",
        category="职事官名", grade="正一品",
    )
    chain_all(w, eid, [qin, song, yuanfeng, stop, restore, end],
              "连接尚书令秦汉源流、宋前期加官及元丰以后置罢节点。")
    w.commit()


def entry838():
    i = 838
    history = Q(
        i,
        "①仆射之名，起于周（《朱子语类》卷112《论官》）。仆射官名始自秦"
        "（《史记·秦始皇本纪》）。尚书仆射分左、右，始于东汉建安四年"
        "（《后汉书·百官志》）。尚书省左仆射即源于梁武帝时",
        "职源与沿革",
    )
    changes = Q(
        i,
        "北宋政和二年(1112)九月，改尚书左仆射为太宰。"
        "靖康元年(1126)十一月，仍依元丰官制改为尚书左仆射",
        "职源与沿革",
    )
    end_q = Q(i, "③南宋乾道八年二月罢", "职源与沿革")
    early = Q(
        i,
        "① 宋前期无职事，为文臣迁转、叙位禄官阶名；元丰寄禄易为特进",
        "职掌",
    )
    reform = Q(
        i,
        "② 元丰新制，为职事官，宰相之任，即尚书省左仆射兼门下侍郎"
        "行侍中职事，为左相",
        "职掌",
    )
    w = W(i)
    eid = fe(w, "尚书省左仆射", "官职")
    source_nodes = [
        tp(w, eid, "周", "已有仆射之名", i, history, "官名源流",
           "建仆射周代源流节点。", "职源与沿革", chain="none"),
        tp(w, eid, "秦", "始有仆射官名", i, history, "官名源流",
           "建仆射秦代官名节点。", "职源与沿革", chain="none"),
        tp(w, eid, "东汉建安四年", "尚书仆射始分左、右", i, history, "官名源流",
           "建左右仆射分置节点。", "职源与沿革", chain="none"),
        tp(w, eid, "南朝梁", "始有尚书省左仆射", i, history, "官名源流",
           "建尚书省左仆射形成节点。", "职源与沿革", chain="none"),
        tp(w, eid, "宋前期", "无职事，为文臣迁转叙位禄阶官", i, early, "阶官",
           "建宋前期左仆射阶官节点。", "职掌", chain="none", attr_grade="从二品"),
    ]
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制"), i, reform,
        "专条细化元丰左仆射为职事官及宰相之任。", "职掌",
        event="为尚书省职事长官；兼门下侍郎者行侍中职事、任左相",
        category="职事官", grade="从一品",
    )
    change = tp(
        w, eid, "北宋政和二年九月", "改名太宰", i, changes,
        "职事官", "建左仆射改太宰节点。", "职源与沿革",
        chain="none", attr_grade="从一品",
    )
    restore = refine(
        w, ft(w, eid, "北宋靖康元年十一月"), i, changes,
        "专条补证靖康复尚书省左仆射旧名。", "职源与沿革",
        event="由太宰恢复旧名，仍依元丰官制",
        category="职事官", grade="从一品",
    )
    end = tp(
        w, eid, "南宋乾道八年二月", "罢置", i, end_q,
        "职事官", "建乾道罢左仆射节点。", "职源与沿革",
        chain="none", attr_grade="从一品",
    )
    chain_all(w, eid, [*source_nodes, yuanfeng, change, restore, end],
              "连接尚书省左仆射源流、宋代阶职变化与置改节点。")
    w.commit()


def entry839():
    i = 839
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "尚书省右仆射", "官职")
    song = tp(
        w, eid, "宋前期", "无职事，为文臣迁转阶官，位次左仆射",
        i, main, "阶官", "建宋前期右仆射阶官节点。",
        chain="none", attr_grade="从二品",
    )
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        "专条细化元丰右仆射为职事官及右相之任。",
        event="为尚书省职事长官；兼中书侍郎者为右相，位次左相",
        category="职事官", grade="从一品",
    )
    change = tp(
        w, eid, "北宋政和二年九月", "改名少宰", i, main,
        "职事官", "建右仆射改少宰节点。", chain="none", attr_grade="从一品",
    )
    restore = refine(
        w, ft(w, eid, "北宋靖康元年十一月"), i, main,
        "专条补证靖康恢复尚书省右仆射旧名。",
        event="由少宰恢复旧名", category="职事官", grade="从一品",
    )
    south = tp(
        w, eid, "南宋建炎三年", "以尚书右仆射、同中书门下平章事为右相",
        i, main, "职事官", "建建炎右仆射右相节点。",
        chain="none", attr_grade="从一品",
    )
    end = tp(
        w, eid, "南宋乾道八年二月", "罢置", i, main,
        "职事官", "建乾道罢右仆射节点。",
        chain="none", attr_grade="从一品",
    )
    chain_all(w, eid, [song, yuanfeng, change, restore, south, end],
              "连接尚书省右仆射宋前期、元丰、政和靖康及南宋节点。")
    w.commit()


def entry840_841():
    i = 840
    main = Q(i, x.b.F[i]["text"])
    history = Q(
        i,
        "春秋时已有太宰之官（《左传·隐公十一年》）。西晋时，太师改名为大宰，"
        "避景帝司马师之讳",
        "职源与沿革",
    )
    song = Q(
        i,
        "北宋徽宗政和二年(1112)九月，改尚书左仆射为太宰"
        "（《十朝纲要》）。至靖康元年十二月罢",
        "职源与沿革",
    )
    w = W(i)
    eid = w.entity("太宰", "官职", "据专条建立太宰官名。", quotation=main)
    spring = tp(w, eid, "春秋", "已有太宰之官", i, history, "官名源流",
                "建太宰春秋源流节点。", "职源与沿革", chain="none")
    west = tp(w, eid, "西晋", "太师避讳改名大宰", i, history, "官名源流",
              "建大宰异写源流节点。", "职源与沿革", chain="none")
    start = tp(
        w, eid, "北宋政和二年九月", "由尚书省左仆射改名", i, song,
        "宰相官名", "建宋代太宰始置节点。", "职源与沿革", chain="none",
    )
    end = tp(
        w, eid, "北宋靖康元年十二月", "罢，复尚书省左仆射旧名", i, song,
        "宰相官名", "建太宰罢置节点。", "职源与沿革", chain="none",
    )
    chain_all(w, eid, [spring, west, start, end], "连接太宰源流与宋代置罢节点。")
    left_e = fe(w, "尚书省左仆射", "官职")
    rel(w, ft(w, left_e, "北宋政和二年九月"), start, "前后演变",
        i, song, "政和改尚书省左仆射为太宰。", "职源与沿革")
    restore_rel = rel(
        w, end, ft(w, left_e, "北宋靖康元年十一月"), "前后演变",
        i, song, "靖康罢太宰并恢复尚书省左仆射。", "职源与沿革",
    )
    mark_citation_conflict(
        w, "Relationships", restore_rel, i, song,
        "太宰条称靖康元年十二月罢，尚书省左仆射条称十一月已恢复旧名，月序不一致。",
        "保留太宰十二月罢与左仆射十一月复名的原文冲突。",
        "职源与沿革",
    )
    w.commit()

    i = 841
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity("少宰", "官职", "据专条建立少宰官名。", quotation=main)
    start = tp(
        w, eid, "北宋政和二年九月", "由尚书省右仆射改名",
        i, main, "宰相官名", "建少宰始置节点。", chain="none",
    )
    end = tp(
        w, eid, "北宋靖康元年十二月", "罢，复尚书省右仆射旧名",
        i, main, "宰相官名", "建少宰罢置节点。", chain="none",
    )
    chain_all(w, eid, [start, end], "连接少宰政和始置与靖康复旧节点。")
    right_e = fe(w, "尚书省右仆射", "官职")
    rel(w, ft(w, right_e, "北宋政和二年九月"), start, "前后演变",
        i, main, "政和改尚书省右仆射为少宰。")
    restore_rel = rel(
        w, end, ft(w, right_e, "北宋靖康元年十一月"), "前后演变",
        i, main, "靖康罢少宰并恢复尚书省右仆射。",
    )
    mark_citation_conflict(
        w, "Relationships", restore_rel, i, main,
        "少宰条称行用于靖康元年十二月间，既有右仆射复名节点据同制系于十一月，月序不一致。",
        "保留少宰运行至十二月与右仆射十一月复名的原文冲突。",
    )
    w.commit()


def ensure_halls(i, quotation):
    w = W(i)
    halls = []
    for title in ("尚书省左仆射厅", "尚书省右仆射厅", "尚书令厅"):
        eid = w.entity(title, "机构", f"据朝堂专条建立{title}。", quotation=quotation)
        tid = tp(
            w, eid, "北宋元丰新制", "为尚书省长官厅事",
            i, quotation, "尚书省官署", f"建{title}节点。",
        )
        halls.append(tid)
        rel(
            w, ft(w, fe(w, "尚书省", "机构"), "北宋元丰新制"), tid,
            "上下级机构", i, quotation, f"{title}为尚书省长官官署。",
        )
    w.commit()
    return halls


def entry842():
    i = 842
    main = Q(i, x.b.F[i]["text"])
    halls = ensure_halls(i, main)
    w = W(i)
    eid = w.entity("朝堂", "机构", "据专条建立三处长官厅事的总称。", quotation=main)
    tid = tp(
        w, eid, "宋代（未载具体年月）",
        "尚书省左、右仆射厅及尚书令厅的总称，为宰相发布政令之地",
        i, main, "官署统称", "建朝堂统称节点。",
    )
    for hall in halls:
        rel(w, tid, hall, "统称与实例", i, main,
            "朝堂是三处尚书省长官厅的同时代总称。")
    w.commit()


def entry843_845():
    i = 843
    history = Q(
        i,
        "尚书丞为秦官。尚书丞分左、右，始于东汉初",
        "职源与沿革",
    )
    change = Q(
        i,
        "北宋沿置。至南宋建炎三年四月，罢尚书左、右丞",
        "职源与沿革",
    )
    duty = Q(
        i,
        "②元丰新制，为职事官，升任执政（副相）",
        "职掌",
    )
    w = W(i)
    eid = fe(w, "尚书省左丞", "官职")
    for time, quotation, field in (
        ("秦", history, "职源与沿革"),
        ("东汉初", history, "职源与沿革"),
        ("宋前期", duty, "职掌"),
        ("北宋元丰新制", duty, "职掌"),
        ("南宋建炎三年四月", change, "职源与沿革"),
    ):
        cite(w, "Timepoints", ft(w, eid, time), i, quotation,
             "专条补证尚书省左丞源流与职掌。", field)
    w.commit()

    i = 845
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "尚书省右丞", "官职")
    for time in ("东汉初", "宋前期", "北宋元丰新制", "南宋建炎三年四月"):
        cite(w, "Timepoints", ft(w, eid, time), i, main,
             "专条说明尚书省右丞沿革、职掌、品位与左丞同而位次稍低。")
    w.commit()


def collective(i, title, instances, event):
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"据专条建立同时代职官统称{title}。",
                   quotation=main)
    tid = tp(
        w, eid, "宋代（未载具体年月）", event, i, main,
        "职官统称", f"建{title}统称节点。",
    )
    for instance_title, instance_time in instances:
        rel(
            w, tid, ft(w, fe(w, instance_title, "官职"), instance_time),
            "统称与实例", i, main, f"{instance_title}是{title}的实例。",
        )
    w.commit()
    return tid


def entry846_850():
    collective(
        846, "仆射丞",
        (
            ("尚书省左仆射", "北宋元丰新制"),
            ("尚书省右仆射", "北宋元丰新制"),
            ("尚书省左丞", "北宋元丰新制"),
            ("尚书省右丞", "北宋元丰新制"),
        ),
        "尚书省左、右仆射与左、右丞的连称",
    )
    collective(
        847, "二丞",
        (
            ("尚书省左丞", "北宋元丰新制"),
            ("尚书省右丞", "北宋元丰新制"),
        ),
        "尚书省左、右丞合称，亦写作贰丞",
    )
    collective(
        848, "中台二辖",
        (
            ("尚书省左丞", "北宋元丰新制"),
            ("尚书省右丞", "北宋元丰新制"),
        ),
        "尚书省左丞、右丞合称",
    )

    i = 849
    main = Q(i, x.b.F[i]["text"])
    halls = ensure_halls(i, main)
    for hall in halls[:2]:
        w = W(i)
        cite(w, "Timepoints", hall, i, main, "专条补证尚书省左、右丞厅官署。")
        w.commit()

    i = 850
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    six_e = w.entity(
        "六部侍郎", "官职",
        "据尚书丞郎专条建立六部侍郎同时代总称。",
        quotation=main,
    )
    six_t = tp(
        w, six_e, "北宋元丰改制前", "吏、户、礼、兵、刑、工六部侍郎总称",
        i, main, "职官统称", "建六部侍郎总称节点。",
    )
    group_e = w.entity(
        "尚书丞郎", "官职",
        "据专条建立元丰改制前左、右丞与六部侍郎的总称。",
        quotation=main,
    )
    group_t = tp(
        w, group_e, "北宋元丰改制前", "尚书省左、右丞与六部侍郎总称",
        i, main, "职官统称", "建尚书丞郎统称节点。",
    )
    rel(w, group_t, ft(w, fe(w, "尚书省左丞", "官职"), "宋前期"),
        "统称与实例", i, main, "尚书省左丞是尚书丞郎实例。")
    rel(w, group_t, ft(w, fe(w, "尚书省右丞", "官职"), "宋前期"),
        "统称与实例", i, main, "尚书省右丞是尚书丞郎实例。")
    rel(w, group_t, six_t, "统称与实例", i, main,
        "六部侍郎是尚书丞郎所含的一组实例。")
    w.commit()


def main():
    repair_formal_titles()
    entry831_833()
    entry834()
    entry835_836()
    entry837()
    entry838()
    entry839()
    entry840_841()
    entry842()
    entry843_845()
    # 第844条“贰揆臣”为空占位，不凭别称标题造实体。
    entry846_850()


if __name__ == "__main__":
    main()
