#!/usr/bin/env python3
"""提取 chapter2t4 第911–930条：国用司、榷货务都茶场及茶务机构。"""
import extract_2t4_811_830 as x


x.b.F = {i: x.b.load(i) for i in range(911, 931)}
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
current_chain = x.current_chain


def entry911():
    i = 911
    name = Q(i, "京局名。")
    history = Q(
        i,
        "乾道三年正月十一日置。五年二月二十二日罢",
        "职源与沿革",
    )
    duty = Q(i, x.b.F[i]["fields"]["职能"], "职能")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "三省户房国用司",
        "机构",
        "本条直接定义三省户房国用司。",
        quotation=name,
    )
    start = tp(
        w,
        eid,
        "南宋乾道三年正月十一日",
        "置司，处理财政出纳文书、登记审计并申报违法稽误事项",
        i,
        history,
        "中央财政机构",
        "建立三省户房国用司始置节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证国用司财政文书与审计职能。", "职能")
    end = tp(
        w,
        eid,
        "南宋乾道五年二月二十二日",
        "罢置，所行事务归并三省户房",
        i,
        history,
        "中央财政机构",
        "建立三省户房国用司罢置节点。",
        "职源与沿革",
        chain="none",
    )
    cite(
        w,
        "Timepoints",
        end,
        i,
        aliases,
        "简称字段补证乾道五年罢国用司后，事务归并三省户房。",
        "简称",
    )
    chain_all(w, eid, [start, end], "连接三省户房国用司始置、罢置节点。")

    for title, quota in (
        ("三省户房国用司点检文字", 2),
        ("三省户房国用司主管文字", 5),
        ("三省户房国用司掌管文书守阙", 2),
        ("三省户房国用司书写文字", 10),
    ):
        role_e = w.entity(
            title,
            "官职",
            f"编制字段明列{title.removeprefix('三省户房国用司')}。",
            quotation=staff,
        )
        role_t = tp(
            w,
            role_e,
            "南宋乾道三年正月十一日",
            f"三省户房国用司始置吏额，{quota}人",
            i,
            staff,
            "财政机构吏职",
            f"国用司始置条明示{title}{quota}人。",
            "编制",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            staff,
            f"三省户房国用司置{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type="吏",
        )
    w.commit()


def entry911_officials():
    """按第911条“官额参国用司条”的明确指引，补齐乾道国用司两项官额。"""
    i = 911
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    role_source = Q(913, x.b.F[913]["fields"]["编制"], "编制")
    w = W(i)
    institute = ft(
        w,
        fe(w, "三省户房国用司", "机构"),
        "南宋乾道三年正月十一日",
    )
    created = []
    for title in ("国用司参计官", "国用司同参计官"):
        eid = fe(w, title, "官职")
        existing = current_chain(w, eid)
        tid = tp(
            w,
            eid,
            "南宋乾道三年正月十一日",
            "三省户房国用司官额",
            i,
            staff,
            "财政属官",
            f"第911条明确官额参国用司条，据第913条官额明细补建{title}乾道节点。",
            "编制",
            chain="none",
        )
        if tid not in existing:
            existing.insert(0, tid)
        chain_all(w, eid, existing, f"将{title}乾道节点接入开禧节点之前。")
        rel(
            w,
            institute,
            tid,
            "编制隶属",
            i,
            staff,
            f"第911条明确官额参国用司条；{title}为第913条所列官额之一，原文未明示员额。",
            "编制",
            staff_type="官",
        )
        created.append(tid)
    w.commit()

    w913 = W(913)
    for tid, title in zip(created, ("国用司参计官", "国用司同参计官")):
        cite(
            w913,
            "Timepoints",
            tid,
            913,
            role_source,
            f"第913条编制字段提供第911条所指的{title}官额明细。",
            "编制",
        )
    w913.commit()


def entry912():
    i = 912
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "国用使",
        "官职",
        "本条直接定义南宋嘉泰年间的国用使。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "南宋嘉泰三年",
        "用孝宗乾道故事始置，由右丞相兼任；官名较制国用使去“制”字",
        i,
        main,
        "财政兼官",
        "建立国用使嘉泰三年始置节点。",
        chain="none",
        attr_officer_type="右丞相兼",
    )
    end = tp(
        w,
        eid,
        "南宋开禧三年十一月二日",
        "罢置",
        i,
        main,
        "财政兼官",
        "建立国用使开禧三年罢置节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接国用使嘉泰始置、开禧罢置节点。")
    rel(
        w,
        ft(w, fe(w, "制国用使", "官职"), "南宋乾道五年二月二十二日"),
        start,
        "前后演变",
        i,
        main,
        "嘉泰三年采用乾道制国用使旧制而去“制”字，连接旧制终止与新官始置节点。",
    )

    same_e = fe(w, "同知国用事", "官职")
    existing = current_chain(w, same_e)
    same_t = tp(
        w,
        same_e,
        "南宋嘉泰三年",
        "由参知政事兼任，与国用使共同领国用事",
        i,
        main,
        "财政兼官",
        "本条直接补证嘉泰三年参知政事兼同知国用事。",
        chain="none",
        attr_officer_type="参知政事兼",
    )
    if same_t not in existing:
        existing.append(same_t)
    chain_all(w, same_e, existing, "将嘉泰三年复置节点接入同知国用事完整时间链。")
    w.commit()


def entry913_core():
    i = 913
    name = Q(i, "京局名。为宰执兼领国用事而设")
    history = Q(i, x.b.F[i]["fields"]["职源与沿革"], "职源与沿革")
    duty = Q(i, x.b.F[i]["fields"]["职能"], "职能")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    w = W(i)

    # 本条开头所述乾道三年事实对应正式条名“三省户房国用司”，不另造国用司别称节点。
    three_e = fe(w, "三省户房国用司", "机构")
    three_start = ft(w, three_e, "南宋乾道三年正月十一日")
    cite(
        w,
        "Timepoints",
        three_start,
        i,
        history,
        "国用司条补证乾道三年三省户房设国用司。",
        "职源与沿革",
    )

    eid = w.entity(
        "国用司",
        "机构",
        "本条直接定义开禧年间单置的国用司；乾道年间简称事实归入三省户房国用司。",
        quotation=name,
    )
    start = tp(
        w,
        eid,
        "南宋开禧元年正月十七日",
        "单独设置，总会内外官司帐目、量入为出并审核防弊",
        i,
        history,
        "中央财政机构",
        "建立开禧年间国用司单置节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证国用司审核内外账目的职能。", "职能")
    end = tp(
        w,
        eid,
        "南宋开禧二年正月十九日",
        "改为国用参计所",
        i,
        history,
        "中央财政机构",
        "建立国用司改为国用参计所的终止节点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接开禧国用司单置、改置节点。")

    for title in ("国用司参计官", "国用司同参计官"):
        role_e = w.entity(
            title,
            "官职",
            f"国用司编制字段明列{title.removeprefix('国用司')}。",
            quotation=staff,
        )
        role_t = tp(
            w,
            role_e,
            "南宋开禧元年正月十七日",
            "国用司官额",
            i,
            staff,
            "财政属官",
            f"国用司单置条的编制字段明列{title}。",
            "编制",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            staff,
            f"国用司官额包括{title}；原文未明示员额，不填写 staff_quota。",
            "编制",
            staff_type="官",
        )

    for title, quota, staff_type in (
        ("国用司承受兼提点文字", 2, "吏"),
        ("国用司点检文字", 1, "吏"),
        ("国用司主管文字", 9, "吏"),
        ("国用司开拆发放文字", 2, "吏"),
        ("国用司攒算", 2, "吏"),
        ("国用司进奏官", 1, "吏"),
        ("国用司承应铺兵", 2, "吏"),
    ):
        role_e = w.entity(
            title,
            "官职",
            f"国用司吏额明列{title.removeprefix('国用司')}。",
            quotation=staff,
        )
        role_t = tp(
            w,
            role_e,
            "南宋开禧元年正月十七日",
            f"国用司单置吏额，{quota}人",
            i,
            staff,
            "财政机构吏职",
            f"国用司单置条明示{title}{quota}人。",
            "编制",
        )
        rel(
            w,
            start,
            role_t,
            "编制隶属",
            i,
            staff,
            f"国用司置{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )
    w.commit()


def entry914():
    i = 914
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = fe(w, "国用司参计官", "官职")
    tid = refine(
        w,
        ft(w, eid, "南宋开禧元年正月十七日"),
        i,
        main,
        "专条补证国用司参计官的选任与职掌。",
        event="由才识过人、奉公爱民的侍从官充任，协助国用使与同知国用事并实掌国用司常务",
        category="财政属官",
        officer="侍从官充",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段含参计官任职史料；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    w.commit()


def entry915():
    i = 915
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = fe(w, "国用司同参计官", "官职")
    refine(
        w,
        ft(w, eid, "南宋开禧元年正月十七日"),
        i,
        main,
        "专条补证国用司同参计官的选任与职掌。",
        event="由才识通练、奉公爱民的卿监官充任，资浅者带“同”字，职掌与参计官同",
        category="财政属官",
        officer="卿监官充",
    )
    w.commit()


def entry916():
    i = 916
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "国用参计所",
        "机构",
        "本条直接定义国用参计所。",
        quotation=main,
    )
    start = tp(
        w,
        eid,
        "南宋开禧二年正月十九日",
        "始置，为参计官治所",
        i,
        main,
        "中央财政机构",
        "建立国用参计所始置节点。",
    )
    rel(
        w,
        ft(w, fe(w, "国用司", "机构"), "南宋开禧二年正月十九日"),
        start,
        "前后演变",
        i,
        main,
        "国用司于同日改为国用参计所。",
    )
    w.commit()


def entry917_core():
    i = 917
    main = Q(i, x.b.F[i]["text"])
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "榷货务都茶场",
        "机构",
        "本条直接定义榷货务都茶场。",
        quotation=main,
    )
    north = tp(
        w,
        eid,
        "北宋徽宗朝",
        "榷货务与都茶场两司统一管理，置提领、监官",
        i,
        origin,
        "中央专卖机构",
        "建立北宋徽宗朝榷货务都茶场统一管理节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", north, i, duty, "补证茶盐等专卖与钞引职掌。", "职掌")
    south = tp(
        w,
        eid,
        "南宋",
        "称行在所榷货务都茶场；有行在、镇江、建康三务，设提辖、监官通衔管领",
        i,
        origin,
        "中央专卖机构",
        "建立南宋行在榷货务都茶场制度节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", south, i, staff, "补证南宋三务场及官吏编制。", "编制")
    qd7 = tp(
        w,
        eid,
        "南宋乾道七年",
        "增置干办榷货务都茶场公事一员",
        i,
        staff,
        "中央专卖机构",
        "建立乾道七年增置干办公事的编制变化节点。",
        "编制",
        chain="none",
    )
    chain_all(w, eid, [north, south, qd7], "连接榷货务都茶场北宋、南宋及乾道七年节点。")
    rel(
        w,
        ft(w, fe(w, "尚书都省", "机构"), "北宋元丰五年十月十七日"),
        north,
        "上下级机构",
        i,
        main,
        "原文明确榷货务都茶场隶尚书省都司；按既有数据口径复用尚书都省。",
    )

    lead_e = w.entity(
        "提领榷货务都茶场官",
        "官职",
        "职源字段明确北宋徽宗朝设置提领官。",
        quotation=origin,
    )
    lead_north = tp(
        w,
        lead_e,
        "北宋徽宗朝",
        "提领榷货务与都茶场的统一管理",
        i,
        origin,
        "财政专卖官",
        "建立北宋提领榷货务都茶场官节点。",
        "职源",
        chain="none",
    )
    lead_south = tp(
        w,
        lead_e,
        "南宋",
        "提领三处榷货务都茶场",
        i,
        staff,
        "财政专卖官",
        "建立南宋提领榷货务都茶场官节点。",
        "编制",
        chain="none",
    )
    chain_all(w, lead_e, [lead_north, lead_south], "连接提领官北宋、南宋任职节点。")
    rel(
        w,
        north,
        lead_north,
        "编制隶属",
        i,
        origin,
        "北宋徽宗朝榷货务都茶场置提领官。",
        "职源",
        staff_type="官",
    )
    rel(
        w,
        south,
        lead_south,
        "编制隶属",
        i,
        staff,
        "南宋三榷货务都茶场由尚书省都司提领。",
        "编制",
        staff_type="官",
    )

    for title, quota in (
        ("榷货务都茶场押号簿官", 12),
        ("榷货务都茶场专知官", None),
        ("榷货务都茶场副知", None),
        ("榷货务都茶场使臣", None),
    ):
        role_e = w.entity(
            title,
            "官职",
            f"南宋编制字段明列{title.removeprefix('榷货务都茶场')}。",
            quotation=staff,
        )
        event = (
            f"南宋榷货务都茶场吏额，{quota}员"
            if quota is not None
            else "南宋榷货务都茶场吏额，若干"
        )
        role_t = tp(
            w,
            role_e,
            "南宋",
            event,
            i,
            staff,
            "专卖机构吏职",
            f"建立{title}南宋编制节点。",
            "编制",
        )
        rel(
            w,
            south,
            role_t,
            "编制隶属",
            i,
            staff,
            f"榷货务都茶场编制明列{title}；仅对明确数字填写员额。",
            "编制",
            staff_quota=quota,
            staff_type="吏",
        )
    cite(
        w,
        "Timepoints",
        south,
        i,
        aliases,
        "简称字段含务场迁置事实与史料用例；纯简称不另建实体。",
        "简称",
        note="纯简称；迁置细节未形成独立正式机构名变化",
    )
    w.commit()


def entry918():
    i = 918
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    group_e = w.entity(
        "三务场",
        "机构",
        "本条直接定义南宋三个榷货务都茶场的总称。",
        quotation=main,
    )
    group_t = tp(
        w,
        group_e,
        "南宋",
        "行在、建康府、镇江府三处榷货务都茶场总称",
        i,
        main,
        "机构统称",
        "建立三务场统称节点。",
    )
    instance_ids = {
        title: w.entity(
            title,
            "机构",
            f"三务场条明确列举{title}。",
            quotation=main,
        )
        for title in (
            "行在榷货务都茶场",
            "建康府榷货务都茶场",
            "镇江府榷货务都茶场",
        )
    }
    zhenjiang_t = tp(
        w,
        instance_ids["镇江府榷货务都茶场"],
        "南宋",
        "南宋三务场之一",
        i,
        main,
        "专卖机构",
        "原文未载镇江府务场始置年月，按南宋制度语境建立节点。",
    )
    w.commit()

    # 第917条简称字段保存了行在、建康两务的明确迁置时间，必须由实际出处建节点。
    migration = Q(917, x.b.F[917]["fields"]["简称"], "简称")
    w917 = W(917)
    xingzai_t = tp(
        w917,
        fe(w917, "行在榷货务都茶场", "机构"),
        "南宋绍兴五年",
        "随行在移置临安",
        917,
        migration,
        "专卖机构",
        "简称字段明载绍兴五年行在务场随移临安。",
        "简称",
    )
    shaoxing_e = w917.entity(
        "绍兴府榷货务都茶场",
        "机构",
        "简称字段明确记载绍兴府榷货务都茶场。",
        quotation=migration,
    )
    shaoxing_end = tp(
        w917,
        shaoxing_e,
        "南宋绍兴二年闰四月九日",
        "移于建康府置局",
        917,
        migration,
        "专卖机构",
        "建立绍兴府榷货务都茶场迁往建康节点。",
        "简称",
    )
    jiankang_t = tp(
        w917,
        fe(w917, "建康府榷货务都茶场", "机构"),
        "南宋绍兴二年闰四月九日",
        "由绍兴府榷货务都茶场移置",
        917,
        migration,
        "专卖机构",
        "建立建康府榷货务都茶场迁入节点。",
        "简称",
    )
    rel(
        w917,
        shaoxing_end,
        jiankang_t,
        "前后演变",
        917,
        migration,
        "绍兴府榷货务都茶场移于建康府置局。",
        "简称",
    )
    w917.commit()

    w = W(i)
    instance_tps = {
        "行在榷货务都茶场": xingzai_t,
        "建康府榷货务都茶场": jiankang_t,
        "镇江府榷货务都茶场": zhenjiang_t,
    }
    for title, instance_t in instance_tps.items():
        cite(
            w,
            "Timepoints",
            instance_t,
            i,
            main,
            f"三务场条补证{title}为南宋三务之一。",
        )
        rel(
            w,
            group_t,
            instance_t,
            "统称与实例",
            i,
            main,
            f"原文明确{title}为三务场之一。",
        )
    w.commit()


def entry919():
    i = 919
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    group_t = ft(w, fe(w, "三务场", "机构"), "南宋")
    cite(
        w,
        "Timepoints",
        group_t,
        i,
        main,
        "本条明确“见三务场”并列举行在、建康、镇江三务；作为异称出处追加，不另建榷货三务实体。",
        note="纯异称；岁收数字不是当前四表可表达的制度属性",
    )
    for title in (
        "行在榷货务都茶场",
        "建康府榷货务都茶场",
        "镇江府榷货务都茶场",
    ):
        instance_time = {
            "行在榷货务都茶场": "南宋绍兴五年",
            "建康府榷货务都茶场": "南宋绍兴二年闰四月九日",
            "镇江府榷货务都茶场": "南宋",
        }[title]
        rid = relation_id(
            w,
            "三务场",
            title,
            "统称与实例",
            "南宋",
            instance_time,
        )
        assert rid, title
        cite(
            w,
            "Relationships",
            rid,
            i,
            main,
            f"榷货三务条再次列举{title}，补证三务场构成。",
        )
    w.commit()


def entry920():
    i = 920
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    group_e = w.entity(
        "提领三榷货务都茶场所",
        "机构",
        "修复目录OCR后，本条直接定义南宋三个提领所的总称。",
        quotation=main,
    )
    group_start = tp(
        w,
        group_e,
        "南宋（未载具体年月）",
        "行在、建康、镇江三处提领榷货务都茶场所并存",
        i,
        aliases,
        "财政专卖管理机构统称",
        "简称字段明确列举南宋三处提领所，但未记各所始置年月。",
        "简称",
        chain="none",
    )
    cite(w, "Timepoints", group_start, i, main, "补证三处提领所的职能与提领官选任。")
    group_qd7 = tp(
        w,
        group_e,
        "南宋乾道七年",
        "提领三务场管茶盐，课额浩大",
        i,
        aliases,
        "财政专卖管理机构统称",
        "简称字段明载乾道七年提领三务场管茶盐。",
        "简称",
        chain="none",
    )
    chain_all(
        w,
        group_e,
        [group_start, group_qd7],
        "连接提领三榷货务都茶场所南宋泛时节点与乾道七年明确节点。",
    )
    for title in (
        "提领行在榷货务都茶场所",
        "提领建康府榷货务都茶场所",
        "提领镇江府榷货务都茶场所",
    ):
        instance_e = w.entity(
            title,
            "机构",
            f"简称字段明确列举{title}。",
            quotation=aliases,
        )
        instance_t = tp(
            w,
            instance_e,
            "南宋（未载具体年月）",
            "三处提领榷货务都茶场所之一",
            i,
            aliases,
            "财政专卖管理机构",
            f"简称字段明确列举{title}，但未记始置年月。",
            "简称",
        )
        rel(
            w,
            group_start,
            instance_t,
            "统称与实例",
            i,
            aliases,
            f"原文明确{title}为南宋三处提领所之一。",
            "简称",
        )
    lead_t = refine(
        w,
        ft(w, fe(w, "提领榷货务都茶场官", "官职"), "南宋"),
        i,
        main,
        "本条细化南宋提领官的兼任来源与职掌。",
        event="提领三处榷货务都茶场，通管茶盐专卖与茶引印卖",
        category="财政专卖官",
        officer="左、右司郎官或户部侍郎兼",
    )
    rel(
        w,
        group_start,
        lead_t,
        "编制隶属",
        i,
        main,
        "三处提领所由提领官统领；原文未明示员额，不填写 staff_quota。",
        staff_type="官",
    )
    w.commit()


def entry921():
    i = 921
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "提辖榷货务兼都茶场",
        "官职",
        "本条直接定义提辖榷货务兼都茶场。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋绍兴六年",
        "始置，提辖榷货务并兼提辖都茶场，位次提领官和提举官而直接管理场务",
        i,
        main,
        "财政专卖官",
        "建立提辖榷货务兼都茶场始置节点。",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段含多种省称及正式全称说明；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    rel(
        w,
        ft(w, fe(w, "榷货务都茶场", "机构"), "南宋"),
        tid,
        "编制隶属",
        i,
        main,
        "提辖官是榷货务都茶场的直接管理官。",
        staff_type="官",
    )
    w.commit()

    staff = Q(917, x.b.F[917]["fields"]["编制"], "编制")
    w917 = W(917)
    for title, time in (
        ("行在榷货务都茶场", "南宋绍兴五年"),
        ("建康府榷货务都茶场", "南宋绍兴二年闰四月九日"),
        ("镇江府榷货务都茶场", "南宋"),
    ):
        rel(
            w917,
            ft(w917, fe(w917, title, "机构"), time),
            tid,
            "编制隶属",
            917,
            staff,
            f"榷货务都茶场总条明示每务设提辖官一员；{title}为三务之一。",
            "编制",
            staff_quota=1,
            staff_type="官",
        )
    w917.commit()


def entry922():
    i = 922
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "提辖榷货务都茶场司",
        "机构",
        "本条直接定义提辖榷货务都茶场司。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋（未载具体年月）",
        "榷货务都茶场提辖官办事机构",
        i,
        main,
        "财政专卖管理机构",
        "主条未载提辖司办事机构的始置年月，按南宋制度语境建立节点。",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段补证提辖司、榷辖司省称及建炎四年提辖官仍兼领的制度背景。",
        "简称",
        note="建炎四年原文直接记提辖官兼领，不据此推断办事机构始置日",
    )
    rel(
        w,
        ft(w, fe(w, "榷货务都茶场", "机构"), "南宋"),
        tid,
        "上下级机构",
        i,
        main,
        "提辖司是榷货务都茶场提辖官的办事机构。",
    )
    w.commit()


def entry923():
    i = 923
    main = Q(i, x.b.F[i]["text"])
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "监榷货务都茶场",
        "官职",
        "本条直接定义监榷货务都茶场。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋",
        "每务二员，分工监管榷货务、都茶场两司并通衔管干，由武臣或备选通判的文臣担任",
        i,
        main,
        "财政专卖官",
        "建立监榷货务都茶场南宋节点。",
        attr_officer_type="武臣或准备选拔为通判的文臣",
    )
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段补证正式官衔及监场官省称；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    w.commit()

    staff = Q(917, x.b.F[917]["fields"]["编制"], "编制")
    w917 = W(917)
    for title, time in (
        ("行在榷货务都茶场", "南宋绍兴五年"),
        ("建康府榷货务都茶场", "南宋绍兴二年闰四月九日"),
        ("镇江府榷货务都茶场", "南宋"),
    ):
        rel(
            w917,
            ft(w917, fe(w917, title, "机构"), time),
            tid,
            "编制隶属",
            917,
            staff,
            f"榷货务都茶场总条明示每务设监官二员；{title}为三务之一。",
            "编制",
            staff_quota=2,
            staff_type="官",
        )
    w917.commit()


def entry924():
    i = 924
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "提领榷货务都茶场所干办公事",
        "官职",
        "本条直接定义提领榷货务都茶场所干办公事。",
        quotation=main,
    )
    tid = tp(
        w,
        eid,
        "南宋乾道七年",
        "始置，属提领榷货务都茶场所",
        i,
        main,
        "财政专卖属官",
        "建立干办公事乾道七年始置节点。",
    )
    w.commit()

    # 员额“一员”明写在第917条编制字段；第924条只明写所属与始置，不能单凭本条推成一员。
    staff = Q(917, x.b.F[917]["fields"]["编制"], "编制")
    w917 = W(917)
    rid = rel(
        w917,
        ft(
            w917,
            fe(w917, "提领三榷货务都茶场所", "机构"),
            "南宋乾道七年",
        ),
        tid,
        "编制隶属",
        917,
        staff,
        "榷货务都茶场总条明载乾道七年增置干办公事一员。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )
    w917.commit()

    w = W(i)
    cite(
        w,
        "Relationships",
        rid,
        i,
        main,
        "专条补证干办公事为提领榷货务都茶场所属官，乾道七年始置。",
    )
    w.commit()


def entry925():
    i = 925
    main = Q(i, x.b.F[i]["text"])
    history = Q(i, x.b.F[i]["fields"]["职源与沿革"], "职源与沿革")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    aliases = Q(i, x.b.F[i]["fields"]["简称与别名"], "简称与别名")
    w = W(i)
    eid = w.entity(
        "在京榷货务",
        "机构",
        "本条直接定义在京榷货务。",
        quotation=main,
    )
    taizu = tp(
        w,
        eid,
        "北宋太祖朝",
        "已经设置，办理茶盐钞引及香药、象牙、绢帛等宝货出卖",
        i,
        history,
        "中央专卖机构",
        "建立在京榷货务北宋太祖朝始见节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", taizu, i, duty, "补证在京榷货务职掌。", "职掌")
    change = tp(
        w,
        eid,
        "北宋熙宁五年七月",
        "改为市易西务下界",
        i,
        history,
        "中央专卖机构",
        "建立在京榷货务熙宁改置节点。",
        "职源与沿革",
        chain="none",
    )
    restore = tp(
        w,
        eid,
        "北宋元丰七年四月十二日",
        "由市易西务下界复为榷货务",
        i,
        history,
        "中央专卖机构",
        "建立在京榷货务元丰复置节点。",
        "职源与沿革",
        chain="none",
    )
    huizong = tp(
        w,
        eid,
        "北宋徽宗朝",
        "与都茶场趋于统一管领",
        i,
        history,
        "中央专卖机构",
        "建立徽宗朝在京榷货务与都茶场统一管领节点。",
        "职源与沿革",
        chain="none",
    )
    south_end = tp(
        w,
        eid,
        "南宋",
        "易为行在榷货务",
        i,
        history,
        "中央专卖机构",
        "建立在京榷货务南宋改为行在榷货务节点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(
        w,
        eid,
        [taizu, change, restore, huizong, south_end],
        "连接在京榷货务太祖朝至南宋的完整沿革链。",
    )

    market_e = w.entity(
        "市易西务下界",
        "机构",
        "职源字段明确熙宁五年在京榷货务改为市易西务下界。",
        quotation=history,
    )
    market_start = tp(
        w,
        market_e,
        "北宋熙宁五年七月",
        "由在京榷货务改置",
        i,
        history,
        "中央贸易机构",
        "建立市易西务下界始置节点。",
        "职源与沿革",
        chain="none",
    )
    market_end = tp(
        w,
        market_e,
        "北宋元丰七年四月十二日",
        "复改为在京榷货务",
        i,
        history,
        "中央贸易机构",
        "建立市易西务下界改回榷货务节点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, market_e, [market_start, market_end], "连接市易西务下界置、罢节点。")
    rel(w, change, market_start, "前后演变", i, history, "在京榷货务改为市易西务下界。", "职源与沿革")
    rel(w, market_end, restore, "前后演变", i, history, "市易西务下界复为在京榷货务。", "职源与沿革")

    field_e = w.entity(
        "行在榷货务",
        "机构",
        "职源字段明确在京榷货务至南宋易为行在榷货务。",
        quotation=history,
    )
    field_t = tp(
        w,
        field_e,
        "南宋",
        "由在京榷货务改置",
        i,
        history,
        "中央专卖机构",
        "建立行在榷货务南宋节点。",
        "职源与沿革",
    )
    rel(w, south_end, field_t, "前后演变", i, history, "在京榷货务至南宋易为行在榷货务。", "职源与沿革")
    rel(
        w,
        ft(w, fe(w, "太府寺", "机构"), "北宋元丰改制"),
        restore,
        "上下级机构",
        i,
        main,
        "原文概括在京榷货务先隶太府寺；以双方元丰真实节点承载无独立年月的隶属事实。",
    )
    rel(
        w,
        ft(w, fe(w, "尚书省左、右司", "机构"), "宋代（未载具体年月）"),
        huizong,
        "上下级机构",
        i,
        main,
        "原文概括在京榷货务后隶尚书省左、右司。",
    )
    cite(
        w,
        "Timepoints",
        taizu,
        i,
        aliases,
        "简称字段含在京榷货务正式全称及省称史料；纯简称不另建实体。",
        "简称与别名",
        note="纯简称与别名",
    )
    w.commit()


def entry926():
    i = 926
    name = Q(i, "监当局名。")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    aliases = Q(i, x.b.F[i]["fields"]["省称"], "省称")
    w = W(i)
    group_e = w.entity(
        "榷货务",
        "机构",
        "本条直接定义北宋江南地方榷货务。",
        quotation=name,
    )
    group_t = tp(
        w,
        group_e,
        "北宋",
        "江南交通要冲的茶叶专买专卖机构，共设六处",
        i,
        duty,
        "地方专卖机构统称",
        "建立北宋地方榷货务统称节点。",
        "职掌",
    )
    cite(
        w,
        "Timepoints",
        group_t,
        i,
        aliases,
        "省称字段再次列举六处榷货务；OCR省称原样保存，不另建实体。",
        "省称",
        note="原文OCR作“桓务”“六權务”，不据常识改写",
    )
    for title in (
        "江陵府榷货务",
        "真州榷货务",
        "海州榷货务",
        "汉阳军榷货务",
        "无为军榷货务",
        "蕲州蕲口榷货务",
    ):
        instance_e = w.entity(
            title,
            "机构",
            f"职掌字段明确列举{title}。",
            quotation=duty,
        )
        instance_t = tp(
            w,
            instance_e,
            "北宋",
            "江南六榷货务之一，专买专卖茶叶",
            i,
            duty,
            "地方专卖机构",
            f"建立{title}北宋节点。",
            "职掌",
        )
        rel(
            w,
            group_t,
            instance_t,
            "统称与实例",
            i,
            duty,
            f"原文明确{title}为江南六榷货务之一。",
            "职掌",
        )
    w.commit()


def entry927():
    i = 927
    main = Q(i, x.b.F[i]["text"])
    w = W(i)
    eid = w.entity(
        "山场",
        "机构",
        "本条直接定义北宋地方茶叶山场。",
        quotation=main,
    )
    tp(
        w,
        eid,
        "北宋",
        "地方官府专买专卖茶叶机构；淮南六州设十三山场，置官吏包买园户茶叶后出售",
        i,
        main,
        "地方专卖机构",
        "建立山场北宋制度节点；原文未列十三场正式名称，不创建地点或场名实体。",
    )
    w.commit()


def entry928():
    i = 928
    name = Q(i, "监当局名。隶榷货务。")
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    staff = Q(i, x.b.F[i]["fields"]["编制"], "编制")
    w = W(i)

    field_e = w.entity(
        "买钞场",
        "机构",
        "职源字段明确北宋熙宁间市易司设置买钞场。",
        quotation=origin,
    )
    tp(
        w,
        field_e,
        "北宋熙宁间",
        "市易司设置，给盐钞于指定盐场支盐",
        i,
        origin,
        "财政兑换机构",
        "建立买钞场熙宁间节点。",
        "职源",
    )

    eid = w.entity(
        "买钞所",
        "机构",
        "本条直接定义买钞所。",
        quotation=name,
    )
    start = tp(
        w,
        eid,
        "北宋崇宁二年十二月四日",
        "始置，募商入纳粮草换取盐钞及其他有价物",
        i,
        origin,
        "财政兑换机构",
        "建立买钞所始置节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证买钞所兑换职能。", "职掌")
    cite(w, "Timepoints", start, i, staff, "补证买钞所管勾官编制。", "编制")
    merge = tp(
        w,
        eid,
        "北宋崇宁四年六月二十三日",
        "在京交子务并入，扩大兑换钱引业务",
        i,
        origin,
        "财政兑换机构",
        "建立在京交子务并入买钞所节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", merge, i, duty, "补证并入后扩大钱引兑换业务。", "职掌")
    chain_all(w, eid, [start, merge], "连接买钞所始置、并入交子务节点。")
    rel(
        w,
        ft(w, fe(w, "在京榷货务", "机构"), "北宋徽宗朝"),
        start,
        "上下级机构",
        i,
        name,
        "原文明确买钞所隶榷货务；崇宁属徽宗朝，连接在京榷货务徽宗节点，避免误连地方六榷货务统称。",
    )

    jiaozi_e = w.entity(
        "在京交子务",
        "机构",
        "职源字段明确在京交子务于崇宁四年并入买钞所。",
        quotation=origin,
    )
    jiaozi_end = tp(
        w,
        jiaozi_e,
        "北宋崇宁四年六月二十三日",
        "并入买钞所",
        i,
        origin,
        "纸币管理机构",
        "建立在京交子务并入节点。",
        "职源",
    )
    rel(
        w,
        jiaozi_end,
        merge,
        "前后演变",
        i,
        origin,
        "在京交子务并入买钞所。",
        "职源",
    )

    role_e = w.entity(
        "买钞所管勾官",
        "官职",
        "编制字段明确三员共同作为买钞所管勾官。",
        quotation=staff,
    )
    role_t = tp(
        w,
        role_e,
        "北宋崇宁二年十二月四日",
        "由榷货务监官二员、使臣或选人一员组成，共三员",
        i,
        staff,
        "监当官",
        "建立买钞所管勾官始置编制节点。",
        "编制",
    )
    rel(
        w,
        start,
        role_t,
        "编制隶属",
        i,
        staff,
        "买钞所置管勾官共三员。",
        "编制",
        staff_quota=3,
        staff_type="官",
    )
    w.commit()


def entry929():
    i = 929
    name = Q(i, "监当局名。川蜀茶、马贸易机构名。")
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "博买都茶场",
        "机构",
        "本条直接定义博买都茶场。",
        quotation=name,
    )
    tid = tp(
        w,
        eid,
        "北宋元丰五年",
        "始置于成都府路，以官卖茶叶所得至边地买马",
        i,
        origin,
        "茶马贸易机构",
        "建立博买都茶场元丰五年始置节点。",
        "职源",
    )
    cite(w, "Timepoints", tid, i, duty, "补证卖茶买马职掌。", "职掌")
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段补证都茶场省称；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    w.commit()


def entry930():
    i = 930
    name = Q(i, "监当局名。")
    origin = Q(i, x.b.F[i]["fields"]["职源"], "职源")
    duty = Q(i, x.b.F[i]["fields"]["职掌"], "职掌")
    aliases = Q(i, x.b.F[i]["fields"]["简称"], "简称")
    w = W(i)
    eid = w.entity(
        "茶场司",
        "机构",
        "本条直接定义茶场司。",
        quotation=name,
    )
    tid = tp(
        w,
        eid,
        "北宋熙宁七年",
        "始置于成都府路诸州，垄断所隶茶民茶叶的包买转卖",
        i,
        origin,
        "地方茶叶专卖机构",
        "建立茶场司熙宁七年始置节点。",
        "职源",
    )
    cite(w, "Timepoints", tid, i, duty, "补证茶场司包买转卖职掌。", "职掌")
    cite(
        w,
        "Timepoints",
        tid,
        i,
        aliases,
        "简称字段补证茶司、茶场省称；纯简称不另建实体。",
        "简称",
        note="纯简称",
    )
    w.commit()


def main():
    assert [x.b.F[i]["title"] for i in range(911, 931)] == [
        "三省户房国用司",
        "国用使",
        "国用司",
        "国用司参计官",
        "国用司同参计官",
        "国用参计所",
        "榷货务都茶场",
        "三务场",
        "榷货三务",
        "提领三榷货务都茶场所",
        "提辖榷货务兼都茶场",
        "提辖榷货务都茶场司",
        "监榷货务都茶场",
        "提领榷货务都茶场所干办公事",
        "在京榷货务",
        "榷货务",
        "山场",
        "买钞所",
        "博买都茶场",
        "茶场司",
    ]
    entry911()
    entry912()
    entry913_core()
    entry914()
    entry915()
    entry911_officials()
    entry916()
    entry917_core()
    entry918()
    entry919()
    entry920()
    entry921()
    entry922()
    entry923()
    entry924()
    entry925()
    entry926()
    entry927()
    entry928()
    entry929()
    entry930()


if __name__ == "__main__":
    main()
