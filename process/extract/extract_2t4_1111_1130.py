#!/usr/bin/env python3
"""提取 chapter2t4 第1111–1130条：仓部余项、户部架阁与礼部总制。"""
import extract_2t4_1091_1110 as x


base = x.x.x.b
base.F = {i: base.load(i) for i in range(1110, 1131)}
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


def repair_warehouse_forage():
    """把上一批按旧OCR预建的“巢籴案”及整段旧引文修正为原书“柴采案”。"""
    i = 1110
    new_staff = field(i, "编制")
    old_staff = new_staff.replace("柴采", "巢籴")
    assert old_staff != new_staff
    w = W(i)
    old_eid = w.find_entity("仓部司巢籴案", "机构")
    if old_eid is not None:
        assert w.find_entity("仓部司柴采案", "机构") is None
        w.conn.execute(
            "update Entities set title=? where id=?",
            ("仓部司柴采案", old_eid),
        )
        w._br(
            "Entities", old_eid,
            "核原书p232，将旧OCR实体名‘仓部司巢籴案’改为‘仓部司柴采案’，保留实体ID。",
        )
    else:
        old_eid = fe(w, "仓部司柴采案", "机构")

    for table in ("Entities", "Timepoints", "Relationships"):
        rows = w.conn.execute(
            f"select id from {table} where quotation=? order by id",
            (old_staff,),
        ).fetchall()
        for (target_id,) in rows:
            w.conn.execute(
                f"update {table} set quotation=? where id=?",
                (new_staff, target_id),
            )
            w._br(
                table, target_id,
                "核原书p232，将仓部司编制整段引文中的OCR误字‘巢籴’改为‘柴采’。",
            )
    rows = w.conn.execute(
        "select id from Citations where quotation=? order by id",
        (old_staff,),
    ).fetchall()
    for (citation_id,) in rows:
        w.conn.execute(
            "update Citations set quotation=? where id=?",
            (new_staff, citation_id),
        )
        w._br(
            "Citations", citation_id,
            "核原书p232，将仓部司编制引文中的OCR误字‘巢籴’改为‘柴采’。",
        )
    w.commit()


def entry1111():
    i = 1111
    main = Q(i, F[i]["text"])
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity("判仓部司事", "官职", "本条直接定义宋前期判仓部司事。", quotation=main)
    song = tp(
        w, eid, "宋前期", "以无职事朝官充任，仓库出纳归三司，实无所掌",
        i, main, "判司差遣", "建立判仓部司事宋前期节点。",
        chain="none",
    )
    abolished = tp(
        w, eid, "北宋元丰改制", "随仓部司恢复职事而罢",
        i, main, "判司差遣", "建立判仓部司事元丰罢止节点。",
        chain="none",
    )
    cite(w, "Timepoints", song, i, aliases, "简称补证仓部判司一人。", "简称", note="纯简称")
    chain_all(w, eid, [song, abolished], "连接判仓部司事宋前期与元丰罢止节点。")
    rel(
        w, ft(w, fe(w, "仓部司", "机构"), "宋前期"), song,
        "编制隶属", i, main, "宋前期仓部司置判仓部司事一人。",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def warehouse_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    tid = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        f"专条细化{title}职掌。", None,
        event=event, category="仓部司办事机构",
    )
    chain_all(w, eid, [tid], f"确认{title}现有完整时间链。")
    w.commit()


def entry1117():
    i = 1117
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("仓部司勾覆案", "机构", "本条直接定义仓部司临时勾覆案。", quotation=main)
    tid = tp(
        w, eid, "北宋元祐元年十月四日", "临时设置，掌本司帐籍审核及印发钞引",
        i, main, "仓部司临时办事机构", "建立仓部司勾覆案精确始置节点。",
    )
    rel(
        w, ft(w, fe(w, "仓部司", "机构"), "北宋元丰新制"), tid,
        "上下级机构", i, main, "仓部司勾覆案为仓部司临时办事机构。",
    )
    w.commit()


def entry1119():
    i = 1119
    main = Q(i, F[i]["text"])
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "仓部司郎中", "官职")
    beiqi = tp(
        w, eid, "北齐", "已有仓部曹郎中之名",
        i, main, "仓部司郎官", "建立仓部司郎中北齐职源节点。",
        chain="none",
    )
    sui = tp(
        w, eid, "隋", "仓部曹改称仓部司，时属民部",
        i, main, "仓部司郎官", "建立仓部司郎中隋代沿革节点。",
        chain="none",
    )
    tang = tp(
        w, eid, "唐高宗即位之初", "始有尚书省户部仓部司郎中之称",
        i, main, "仓部司郎官", "建立仓部司郎中唐代正称节点。",
        chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化仓部司郎中宋前期阶官性质。", "职掌",
        time="宋前期", event="为无职事的中行郎中阶，元丰后寄禄官易为朝散大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，为仓部司长官，掌领本司事",
        i, duty, "仓部司长官", "建立仓部司郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [beiqi, sui, tang, song, reform], "重建仓部司郎中北齐至元丰完整时间链。")
    rel(
        w, ft(w, fe(w, "仓部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰仓部司置郎中为司长。",
        "职掌", staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1120():
    i = 1120
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity("仓部司员外郎", "官职", "本条直接定义仓部司员外郎。", quotation=main)
    sui = tp(
        w, eid, "隋开皇六年", "始有尚书省仓部司员外郎之名，时属民部",
        i, origin, "仓部司郎官", "建立仓部司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐贞观二十三年", "民部改户部，尚书省户部仓部司员外郎称谓确立",
        i, origin, "仓部司郎官", "建立仓部司员外郎唐代正称节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "为无职事的中行员外郎阶，元丰后寄禄官易为朝散郎",
        i, duty, "文臣迁转官阶", "建立仓部司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，为仓部司副长官，佐郎中掌本司事",
        i, duty, "仓部司副长官", "建立仓部司员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [sui, tang, song, reform], "连接仓部司员外郎隋、唐、宋前期与元丰节点。")
    rel(
        w, ft(w, fe(w, "仓部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰仓部司置员外郎为副长官。",
        "职掌", staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1121():
    i = 1121
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    archive_e = w.entity("户部架阁库", "机构", "职源明确崇宁间户部设置独立架阁库。", quotation=origin)
    archive_n = tp(
        w, archive_e, "北宋崇宁间", "仿吏部设置，保存户部结案二年以上文书",
        i, origin, "户部档案机构", "建立户部架阁库北宋始置节点。",
        "职源", chain="none",
    )
    cite(w, "Timepoints", archive_n, i, duty, "补证档案编目、登记、保存与检索职能。", "职掌")
    archive_s = tp(
        w, archive_e, "南宋绍兴十五年五月", "逐部复置架阁库",
        i, aliases, "户部档案机构", "建立户部架阁库南宋复置节点。",
        "简称与别名", chain="none",
    )
    chain_all(w, archive_e, [archive_n, archive_s], "连接户部架阁库崇宁始置与绍兴复置节点。")

    eid = w.entity("主管尚书省户部架阁文字", "官职", "本条直接定义主管户部架阁文字官。", quotation=main)
    north = tp(
        w, eid, "北宋崇宁间", "随户部架阁库始置，主管户部档案",
        i, origin, "户部档案官", "建立主管户部架阁文字北宋节点。",
        "职源", chain="none",
    )
    cite(w, "Timepoints", north, i, duty, "补证主管户部档案库职掌。", "职掌")
    cite(w, "Timepoints", north, i, grade, "补证选任资格及品位随寄禄官。", "官品")
    south = tp(
        w, eid, "南宋绍兴十五年五月", "逐部复置主管架阁官，主管户部档案",
        i, aliases, "户部档案官", "建立主管户部架阁文字南宋复置节点。",
        "简称与别名", chain="none",
    )
    cite(w, "Timepoints", south, i, aliases, "简称与拟汉官称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [north, south], "连接主管户部架阁文字崇宁与绍兴节点。")
    rel(w, archive_n, north, "编制隶属", i, origin, "崇宁间户部架阁库置主管官。", "职源", staff_quota=1, staff_type="官")
    rel(w, archive_s, south, "编制隶属", i, aliases, "绍兴十五年逐部复置主管架阁官。", "简称与别名", staff_quota=1, staff_type="官")
    rel(
        w, ft(w, fe(w, "管勾尚书六部架阁库", "官职"), "北宋崇宁间"), north,
        "前后演变", i, origin, "崇宁间六部架阁官由合置转为户部分置。", "职源",
    )
    rel(
        w, ft(w, fe(w, "主管尚书某部架阁文字", "官职"), "南宋绍兴十五年"), south,
        "统称与实例", i, aliases, "主管尚书某部架阁文字包括户部主管架阁文字。",
        "简称与别名",
    )
    w.commit()


LIBU_CASES = (
    "礼部礼乐案", "礼部贡举案", "礼部宗正案", "礼部奉使帐案", "礼部封册案",
    "礼部表奏案", "礼部宝印案", "礼部检法案", "礼部知杂案", "礼部开拆案",
)


def entry1122():
    i = 1122
    main = Q(i, F[i]["text"])
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "礼部", "机构")
    zhou = tp(
        w, eid, "北周", "始有礼部之名",
        i, origin, "尚书省六部", "建立礼部北周职源节点。",
        "职源与沿革", chain="none",
    )
    sui = tp(
        w, eid, "隋", "置为尚书省六部之一",
        i, origin, "尚书省六部", "建立礼部隋代入尚书省节点。",
        "职源与沿革", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代", "宋前期"), i, duty,
        "专条细化礼部宋前期职权旁落。", "职掌",
        time="宋前期", event="主要职事为太常礼院与贡院所侵，本部仅掌少量章表等事",
        category="中央行政机构",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判礼部事二人及吏额。", "编制")
    reform = tp(
        w, eid, "北宋元丰新制", "恢复职事，掌礼乐、祭祀、朝会、科举、印记、图书及祥瑞政令",
        i, duty, "尚书省六部", "建立礼部元丰振职节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰十官额、十案及吏额。", "编制")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证尚书省礼部为官司。")
    chain_all(w, eid, [zhou, sui, song, reform], "重建礼部北周、隋、宋前期与元丰完整时间链。")
    rel(
        w, ft(w, fe(w, "尚书省", "机构"), "北宋元丰新制"), reform,
        "上下级机构", i, staff, "元丰礼部为尚书省六部之一。", "编制",
    )
    for title in LIBU_CASES:
        case_e = w.entity(title, "机构", f"礼部编制逐名列出{title}。", quotation=staff)
        case_t = tp(
            w, case_e, "北宋元丰新制", "礼部十案之一",
            i, staff, "礼部办事机构", f"据礼部编制建立{title}元丰节点。",
            "编制",
        )
        rel(w, reform, case_t, "上下级机构", i, staff, f"元丰{title}隶礼部。", "编制")
    w.commit()


def entry1123():
    i = 1123
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    staff = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity("判礼部事", "官职", "本条直接定义判礼部事差遣。", quotation=main)
    sui = tp(
        w, eid, "隋开皇三年", "已有尚书左仆射判礼部事之领衔兼管名目",
        i, origin, "判部差遣", "建立判礼部事隋代同名职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "掌制举、斋郎室长补奏、谥号集议及牌印出纳",
        i, duty, "判部差遣", "建立判礼部事宋前期节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", song, i, rank, "补证由两制官及带职朝官充任。", "品位")
    cite(w, "Timepoints", song, i, staff, "补证编制二人。", "编制")
    cite(w, "Timepoints", song, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    chain_all(w, eid, [sui, song], "连接判礼部事隋代同名职源与宋前期差遣节点。")
    rel(
        w, ft(w, fe(w, "礼部", "机构"), "宋前期"), song,
        "编制隶属", i, staff, "宋前期礼部置判礼部事二人。",
        "编制", staff_quota=2, staff_type="官",
    )
    w.commit()


def entry1124():
    i = 1124
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "礼部尚书", "官职")
    sui = tp(
        w, eid, "隋", "始置礼部尚书",
        i, origin, "礼部长官", "建立礼部尚书隋代职源节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代", "宋前期"), i, duty,
        "专条细化礼部尚书宋前期阶官性质。", "职掌",
        time="宋前期", event="无职掌，为文臣迁转寄禄官阶，元丰后寄禄官易银青光禄大夫",
        category="文臣迁转官阶", grade="正三品",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期正三品。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，为礼部长官，总掌礼乐祭祀、学校贡举等政令",
        i, duty, "礼部长官", "建立礼部尚书元丰职事节点。",
        "职掌", chain="none", attr_grade="从二品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从二品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [sui, song, reform], "连接礼部尚书隋、宋前期与元丰节点。")
    rel(
        w, ft(w, fe(w, "礼部", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰礼部置尚书一人总掌本部。",
        "职掌", staff_quota=1, staff_type="官",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    w.commit()


def entry1125():
    i = 1125
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    w = W(i)
    eid = fe(w, "权礼部尚书", "官职")
    old = ft(w, eid, "北宋元祐三年闰十二月二十八日")
    new = tp(
        w, eid, "北宋元祐三年闰十二月十八日", "始置，以安排资格尚浅而职务所需的新进之士",
        i, origin, "权摄六部长官", "据专条保留十八日异文节点。",
        "职源", chain="none", attr_grade="正三品",
    )
    mark_citation_conflict(
        w, "Timepoints", new, i, origin,
        "本条作闰十二月十八日；第955条“权六部尚书”作闰十二月二十八日。",
        "两条辞典原文日期相差十日，双节点保留。", "职源",
    )
    cite(w, "Timepoints", new, i, duty, "补证职掌与正礼部尚书同。", "职掌")
    cite(w, "Timepoints", new, i, grade, "补证正三品。", "官品")
    old_citations = w.conn.execute(
        "select id from Citations where target_table='Timepoints' and target_id=? and conflict_flag=0",
        (old,),
    ).fetchall()
    for (citation_id,) in old_citations:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?",
            ("第955条作闰十二月二十八日；第1125条专条作闰十二月十八日。", citation_id),
        )
        w._br("Citations", citation_id, "将权礼部尚书二十八日旧证与专条十八日异文显式标冲突。")
    chain_all(w, eid, [new, old], "按十八日、二十八日顺序保留权礼部尚书日期异文。")
    rel(
        w, ft(w, fe(w, "礼部", "机构"), "北宋元丰新制"), new,
        "编制隶属", i, origin, "权礼部尚书为礼部长官权官。", "职源", staff_type="官",
    )
    w.commit()


def entry1126():
    i = 1126
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "礼部侍郎", "官职")
    wendi = tp(
        w, eid, "隋文帝时", "已有礼部侍郎之名，地位相当于礼部司郎官",
        i, origin, "礼部郎官", "建立礼部侍郎隋文帝时名目节点。",
        "职源", chain="none",
    )
    yangdi = tp(
        w, eid, "隋炀帝时", "始置为礼部尚书佐贰",
        i, origin, "礼部副长官", "建立礼部侍郎隋炀帝时副长官节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "北宋元丰改制前", "宋前期"), i, duty,
        "专条细化礼部侍郎宋前期阶官性质。", "职掌",
        time="宋前期", event="不治本部事，为文官迁转寄禄官阶，元丰后寄禄官易正议大夫",
        category="文臣迁转官阶", grade="正四品下",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期正四品下。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，为礼部副长官，佐尚书掌本部事",
        i, duty, "礼部副长官", "建立礼部侍郎元丰职事节点。",
        "职掌", chain="none", attr_grade="从三品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从三品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证元丰编制一人。", "编制")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟称仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [wendi, yangdi, song, reform], "重建礼部侍郎隋文帝至元丰完整时间链。")
    rel(
        w, ft(w, fe(w, "礼部", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, staff, "元丰礼部置侍郎一人。", "编制",
        staff_quota=1, staff_type="官",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    w.commit()


def entry1127():
    i = 1127
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "权礼部侍郎", "官职")
    tid = refine(
        w, ft_any(w, eid, "北宋元祐二年", "北宋元祐二年七月四日"), i, origin,
        "专条给出权礼部侍郎精确始置日期。", "职源",
        time="北宋元祐二年七月四日", event="始置，资格与位遇低于正员礼部侍郎",
        category="权摄六部副长官", grade="从四品",
    )
    cite(w, "Timepoints", tid, i, duty, "补证职掌与正礼部侍郎同。", "职掌")
    cite(w, "Timepoints", tid, i, rank, "补证从四品及带权条件、班位。", "品位")
    cite(w, "Timepoints", tid, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    rel(
        w, ft(w, fe(w, "礼部", "机构"), "北宋元丰新制"), tid,
        "编制隶属", i, origin, "权礼部侍郎为礼部侍郎权官。", "职源", staff_type="官",
    )
    cite(w, "Timepoints", tid, i, main, "正文补证为职事官。")
    w.commit()


def entry1128():
    i = 1128
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "礼部奉使帐案", "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        "专条细化礼部奉使帐案职掌。", None,
        event="掌国使礼物及外事机构帐目检察", category="礼部办事机构",
    )
    merged = tp(
        w, eid, "南宋建炎三年", "并入礼部宗正案",
        i, main, "礼部办事机构", "建立奉使帐案建炎并省节点。",
        chain="none",
    )
    chain_all(w, eid, [north, merged], "连接奉使帐案元丰与建炎并省节点。")
    target_e = fe(w, "礼部宗正案", "机构")
    target_n = ft(w, target_e, "北宋元丰新制")
    target_s = tp(
        w, target_e, "南宋建炎三年", "接收并入的奉使帐案职事",
        i, main, "礼部办事机构", "建立宗正案接收奉使帐案节点。",
        chain="none",
    )
    chain_all(w, target_e, [target_n, target_s], "连接宗正案元丰与建炎接收职事节点。")
    rel(w, merged, target_s, "前后演变", i, main, "建炎三年奉使帐案并入宗正案。")
    w.commit()


def entry1129():
    i = 1129
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "礼部封册案", "机构")
    tid = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        "专条细化礼部封册案职掌。", None,
        event="掌册立后妃、册封宗室所用宝册、章服、旌节及赏赐",
        category="礼部办事机构",
    )
    ordered = [tid]
    south = w.find_timepoint(eid, "南宋建炎三年")
    if south is not None:
        ordered.append(south)
    chain_all(w, eid, ordered, "确认礼部封册案现有完整时间链。")
    w.commit()


def entry1130():
    i = 1130
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "礼部表奏案", "机构")
    north = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        "专条细化礼部表奏案职掌。", None,
        event="掌后妃宗室奏表章词撰写及祥瑞孝行表彰",
        category="礼部办事机构",
    )
    merged = tp(
        w, eid, "南宋建炎三年", "并入礼部封册案",
        i, main, "礼部办事机构", "建立表奏案建炎并省节点。",
        chain="none",
    )
    chain_all(w, eid, [north, merged], "连接表奏案元丰与建炎并省节点。")
    target_e = fe(w, "礼部封册案", "机构")
    target_n = ft(w, target_e, "北宋元丰新制")
    target_s = tp(
        w, target_e, "南宋建炎三年", "接收并入的表奏案职事",
        i, main, "礼部办事机构", "建立封册案接收表奏案节点。",
        chain="none",
    )
    chain_all(w, target_e, [target_n, target_s], "连接封册案元丰与建炎接收职事节点。")
    rel(w, merged, target_s, "前后演变", i, main, "建炎三年表奏案并入封册案。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1111, 1131)] == [
        "判仓部司事", "仓部司仓场案", "仓部司上供案", "仓部司柴采案",
        "仓部司给纳案", "仓部司开拆案", "仓部司勾覆案", "仓部司知杂案",
        "仓部司郎中", "仓部司员外郎", "主管尚书省户部架阁文字", "尚书省礼部",
        "判礼部事", "礼部尚书", "权礼部尚书", "礼部侍郎", "权礼部侍郎",
        "礼部奉使帐案", "礼部封册案", "礼部表奏案",
    ]
    repair_warehouse_forage()
    entry1111()
    warehouse_case(1112, "仓部司仓场案", "掌诸路粮草收支、出纳及折欠")
    warehouse_case(1113, "仓部司上供案", "掌年额漕运上供及封桩粮草")
    warehouse_case(1114, "仓部司柴采案", "掌粮草柴采及坐仓折纳")
    warehouse_case(1115, "仓部司给纳案", "掌官吏米麦禄廪、救济及杂给")
    warehouse_case(1116, "仓部司开拆案", "掌本司文书收发")
    entry1117()
    warehouse_case(1118, "仓部司知杂案", "掌本司杂务，相当于后勤总管")
    entry1119()
    entry1120()
    entry1121()
    entry1122()
    entry1123()
    entry1124()
    entry1125()
    entry1126()
    entry1127()
    entry1128()
    entry1129()
    entry1130()


if __name__ == "__main__":
    main()
