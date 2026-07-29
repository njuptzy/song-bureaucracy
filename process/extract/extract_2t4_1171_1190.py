#!/usr/bin/env python3
"""提取 chapter2t4 第1171–1190条：兵部长贰、十案、四司及职方司总条。"""
import extract_2t4_1151_1170 as x


base = x.base
base.F = {i: base.load(i) for i in range(1170, 1191)}
base.F[1166] = base.load(1166)
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


def entry1171():
    i = 1171
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("兵部甲库", "机构", "本条直接定义宋前期兵部甲库。", quotation=main)
    tid = tp(
        w, eid, "宋前期", "收受武臣除授制、敕",
        i, main, "兵部附属机构", "建立兵部甲库宋前期节点。",
    )
    parent = ft(w, fe(w, "兵部", "机构"), "宋前期")
    rel(w, parent, tid, "上下级机构", i, main, "宋前期兵部甲库隶兵部。")

    staff = Q(1166, F[1166]["fields"]["编制"], "编制")
    post_e = w.entity("兵部甲库令史", "官职", "兵部总条明确兵部甲库有令史二人。", quotation=staff)
    post_t = tp(
        w, post_e, "宋前期", "办理兵部甲库文书",
        1166, staff, "兵部胥吏", "据兵部编制建立兵部甲库令史节点。", "编制",
    )
    rel(w, tid, post_t, "编制隶属", 1166, staff, "宋前期兵部甲库置令史二人。", "编制",
        staff_quota=2, staff_type="吏")
    w.commit()


def entry1172():
    i = 1172
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "兵部尚书", "官职")
    xwei = tp(
        w, eid, "西魏废帝元年", "始见兵部尚书之称",
        i, origin, "兵部长官", "建立兵部尚书西魏名源节点。",
        "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "始置为尚书省六部之一的兵部尚书",
        i, origin, "兵部长官", "建立兵部尚书隋代机构长官节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代", "宋前期"), i, duty,
        "专条细化兵部尚书宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为文臣迁转寄禄官阶，元丰后寄禄官易银青光禄大夫",
        category="文臣迁转官阶", grade="正三品",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期正三品。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为兵部长官，领本部职事，大礼时充卤簿使",
        i, duty, "兵部长官", "建立兵部尚书元丰职事节点。",
        "职掌", chain="none", attr_grade="从二品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从二品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [xwei, sui, song, reform],
              "连接兵部尚书西魏名源、隋、宋前期与元丰节点。")
    parent_e = fe(w, "兵部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期兵部尚书为无职事阶官。", "职掌", staff_quota=1, staff_type="官")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        "元丰兵部置尚书一人为长官。", "职掌", staff_quota=1, staff_type="官")
    w.commit()


def entry1173():
    i = 1173
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "权兵部尚书", "官职")
    old = ft(w, eid, "北宋元祐三年闰十二月二十八日")
    new = tp(
        w, eid, "北宋元祐三年闰十二月十八日", "始置，以安排资格未及而职务需要的新进之士",
        i, origin, "权摄六部长官", "据专条保留十八日异文节点。",
        "职源", chain="none", attr_grade="正三品",
    )
    mark_citation_conflict(
        w, "Timepoints", new, i, origin,
        "本条作闰十二月十八日；第955条‘权六部尚书’作闰十二月二十八日。",
        "两条辞典原文日期相差十日，双节点保留。", "职源",
    )
    cite(w, "Timepoints", new, i, duty, "补证与兵部尚书同为一部长官。", "职掌")
    cite(w, "Timepoints", new, i, rank, "补证正三品及位次。", "品位")
    cite(w, "Timepoints", new, i, aliases, "简称与别名仅作称谓证据。",
         "简称与别名", note="纯简称")
    old_citations = w.conn.execute(
        "select id from Citations where target_table='Timepoints' and target_id=? and conflict_flag=0",
        (old,),
    ).fetchall()
    for (citation_id,) in old_citations:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?",
            ("第955条作闰十二月二十八日；第1173条专条作闰十二月十八日。", citation_id),
        )
        w._br("Citations", citation_id, "将权兵部尚书二十八日旧证与专条十八日异文显式标冲突。")
    chain_all(w, eid, [new, old], "按十八日、二十八日顺序保留权兵部尚书日期异文。")
    rel(w, ft(w, fe(w, "兵部", "机构"), "北宋元丰新制"), new,
        "编制隶属", i, duty, "权兵部尚书为兵部长官权官。", "职掌", staff_type="官")
    w.commit()


def entry1174():
    i = 1174
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "兵部侍郎", "官职")
    sui = tp(
        w, eid, "隋大业三年", "尚书省兵部侍郎始置",
        i, origin, "兵部副长官", "建立兵部侍郎隋代职源节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "北宋元丰改制前", "宋前期"), i, duty,
        "专条细化兵部侍郎宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为前行侍郎寄禄官阶，元丰后寄禄官易正议大夫",
        category="文臣迁转官阶", grade="正四品下",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期正四品下。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为兵部副长官，佐尚书领本部事",
        i, duty, "兵部副长官", "建立兵部侍郎元丰职事节点。",
        "职掌", chain="none", attr_grade="从三品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从三品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [sui, song, reform], "连接兵部侍郎隋代、宋前期与元丰节点。")
    parent_e = fe(w, "兵部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期兵部侍郎为无职事阶官。", "职掌", staff_quota=1, staff_type="官")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        "元丰兵部置侍郎一人为副长官。", "职掌", staff_quota=1, staff_type="官")
    w.commit()


def entry1175():
    i = 1175
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    w = W(i)
    eid = fe(w, "权兵部侍郎", "官职")
    tid = refine(
        w, ft_any(w, eid, "北宋元祐二年", "北宋元祐二年七月四日"), i, origin,
        "专条给出权兵部侍郎精确始置日期。", "职源",
        time="北宋元祐二年七月四日", event="始置，未历两省及待制以上者带权字",
        category="权摄六部副长官", grade="从四品",
    )
    cite(w, "Timepoints", tid, i, duty, "补证职掌与兵部侍郎同。", "职掌")
    cite(w, "Timepoints", tid, i, rank, "补证从四品、带权条件及班位。", "品位")
    cite(w, "Timepoints", tid, i, main, "正文补证为职事官。")
    rel(w, ft(w, fe(w, "兵部", "机构"), "北宋元丰新制"), tid,
        "编制隶属", i, duty, "权兵部侍郎为兵部侍郎权官。", "职掌", staff_type="官")
    w.commit()


def bingbu_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "机构", f"第{i}条直接定义{title}。", quotation=main)
    tid = tp(
        w, eid, "北宋元丰新制", event,
        i, main, "兵部办事机构", f"建立{title}元丰节点。",
    )
    rel(w, ft(w, fe(w, "兵部", "机构"), "北宋元丰新制"), tid,
        "上下级机构", i, main, f"{title}为兵部常设办事机构。")
    w.commit()


def entry1186():
    i = 1186
    main = Q(i, F[i]["text"])
    aliases = field(i, "别称")
    staff = Q(1166, F[1166]["fields"]["编制"], "编制")
    w = W(i)
    eid = w.entity("兵部四司", "机构", "本条直接定义兵部四司合称。", quotation=main)
    reform = tp(
        w, eid, "北宋元丰新制", "兵部司、职方司、驾部司、库部司的合称",
        1166, staff, "机构统称", "据兵部元丰四司编制建立兵部四司节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, main, "专条补证兵部四司的四个实例。")
    jianyan = tp(
        w, eid, "南宋建炎三年", "兵部司兼领职方司，驾部司兼领库部司",
        i, main, "机构统称", "建立兵部四司机构建炎兼领节点。",
        chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴初", "四司合为一，由驾部、兵部郎官共一员",
        i, main, "机构统称", "建立兵部四司隆兴合一节点。",
        chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "别称‘兵曹四司’仅作称谓证据。", "别称", note="纯简称")
    chain_all(w, eid, [reform, jianyan, longxing], "连接兵部四司元丰、建炎与隆兴节点。")
    for title in ("兵部司", "职方司", "驾部司", "库部司"):
        office_e = fe(w, title, "机构")
        rel(w, reform, ft(w, office_e, "北宋元丰新制"), "统称与实例", i, main,
            f"兵部四司包括{title}。")
        rel(w, jianyan, ft(w, office_e, "南宋建炎三年"), "统称与实例", i, main,
            f"建炎兼领格局下兵部四司仍包括{title}。")
        rel(w, longxing, ft_any(w, office_e, "南宋隆兴初", "南宋隆兴元年"), "统称与实例", i, main,
            f"隆兴四司合一所指实例包括{title}。")
    w.commit()


def entry1187():
    i = 1187
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "兵部司", "机构")
    sui = tp(
        w, eid, "隋初", "始有尚书省兵部兵部司之称",
        i, origin, "兵部所属司", "建立兵部司隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事，未见设置职事官",
        i, duty, "兵部所属司", "建立兵部司宋前期节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期未见职事官。", "编制")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化兵部司元丰职掌。", "职掌",
        event="设郎中、员外郎，佐参兵部尚书、侍郎事", category="兵部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎中、员外郎各一人。", "编制")
    jianyan = refine(
        w, ft(w, eid, "南宋建炎三年"), i, aliases,
        "简称引文补证建炎兵部司兼职方司。", "简称与别名",
        event="兵部司郎官兼领职方司", category="兵部所属司",
    )
    longxing = refine(
        w, ft_any(w, eid, "南宋隆兴初", "南宋隆兴元年"), i, staff,
        "编制补证南宋四司合一。", "编制",
        time="南宋隆兴元年", event="四司合一，仅置郎官一员兼领", category="兵部所属司",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与别名仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兵部司为兵部所属四司之一。")
    chain_all(w, eid, [sui, song, reform, jianyan, longxing],
              "重建兵部司隋初至南宋隆兴完整时间链。")
    parent_e = fe(w, "兵部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期兵部司隶兵部。")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰兵部司隶兵部并恢复职事。", "职掌")
    w.commit()


def entry1188():
    i = 1188
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "兵部司郎中", "官职")
    qinhan = tp(
        w, eid, "秦汉", "已有郎中之名，为远源",
        i, origin, "兵部司郎官", "建立兵部司郎中秦汉名源节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐武德三年", "始有兵部司郎中之名",
        i, origin, "兵部司郎官", "建立兵部司郎中唐代正名节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化兵部司郎中宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为前行郎中寄禄官阶，元丰后寄禄官易朝请大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为兵部司长官，参掌本部长贰之事",
        i, duty, "兵部司长官", "建立兵部司郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    jianyan = tp(
        w, eid, "南宋建炎三年四月十三日", "兵部郎官一员兼领职方司",
        i, aliases, "兵部司郎官", "建立兵部司郎中建炎兼职节点。",
        "简称与别名", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴元年", "驾部、兵部郎官共一员兼领四司",
        i, aliases, "兵部司郎官", "建立兵部司郎中隆兴四司合领节点。",
        "简称与别名", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [qinhan, tang, song, reform, jianyan, longxing],
              "连接兵部司郎中秦汉名源至南宋隆兴完整时间链。")
    parent_e = fe(w, "兵部司", "机构")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        "元丰兵部司置郎中一人。", "职掌", staff_quota=1, staff_type="官")
    rel(w, ft(w, parent_e, "南宋建炎三年"), jianyan, "编制隶属", i, aliases,
        "建炎兵部郎官一员兼职方。", "简称与别名", staff_quota=1, staff_type="官")
    rel(w, ft(w, parent_e, "南宋隆兴元年"), longxing, "编制隶属", i, aliases,
        "隆兴四司由一员郎官兼领。", "简称与别名", staff_quota=1, staff_type="官")
    w.commit()


def entry1189():
    i = 1189
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity("兵部司员外郎", "官职", "本条直接定义兵部司员外郎。", quotation=main)
    sui = tp(
        w, eid, "隋文帝六年", "员外郎始置",
        i, origin, "兵部司郎官", "建立兵部司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事，为前行员外郎寄禄官阶，元丰后寄禄官易朝请郎",
        i, duty, "文臣迁转官阶", "建立兵部司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为兵部司副长官，与郎中佐参本部长贰事",
        i, duty, "兵部司副长官", "建立兵部司员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    south = tp(
        w, eid, "南宋", "四司郎官并省，或仅置一员通治曹事",
        i, duty, "兵部司郎官", "建立兵部司员外郎南宋并省节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [sui, song, reform, south],
              "连接兵部司员外郎隋代、宋前期、元丰与南宋节点。")
    rel(w, ft(w, fe(w, "兵部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰兵部司置员外郎一人。", "职掌",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1190():
    i = 1190
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "职方司", "机构")
    zhouli = tp(
        w, eid, "先秦《周礼》", "职方氏掌天下图地，为职方司名源",
        i, origin, "兵部所属司", "建立职方司《周礼》名源节点。",
        "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "始置尚书省兵部职方司",
        i, origin, "兵部所属司", "建立职方司隋代机构节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "收受诸州闰年图、图经并汇绘天下图经",
        i, duty, "兵部所属司", "建立职方司宋前期职掌节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判职方司事一人。", "编制")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化职方司元丰职掌。", "职掌",
        event="掌州县废复、四夷归附及全国分路分州地图、城寨烽候之数",
        category="兵部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎中、员外郎各一人。", "编制")
    jianyan = refine(
        w, ft(w, eid, "南宋建炎三年"), i, staff,
        "专条补证建炎兵部司郎中兼职方司郎中。", "编制",
        event="由兵部司郎中兼领职方司", category="兵部所属司",
    )
    longxing = ft_any(w, eid, "南宋隆兴初", "南宋隆兴元年")
    shaoxi = tp(
        w, eid, "南宋绍熙三年六月", "职方司与驾部司吏额并入兵部司、库部司",
        i, staff, "兵部所属司", "建立职方司绍熙三年吏额并省节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证职方司为兵部四司之一。")
    chain_all(w, eid, [zhouli, sui, song, reform, jianyan, longxing, shaoxi],
              "重建职方司《周礼》名源至绍熙三年完整时间链。")
    parent_e = fe(w, "兵部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期职方司隶兵部。")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰职方司隶兵部并掌地图版籍。", "职掌")

    judge_e = w.entity("判职方司事", "官职", "职方司编制明确宋前期设判司事一人。", quotation=staff)
    judge_t = tp(
        w, judge_e, "宋前期", "主判职方司事",
        i, staff, "判司差遣", "据职方司编制建立判职方司事宋前期节点。", "编制",
    )
    rel(w, song, judge_t, "编制隶属", i, staff, "宋前期职方司置判职方司事一人。", "编制",
        staff_quota=1, staff_type="官")

    lang_e = fe(w, "职方司郎中", "官职")
    lang_general = ft(w, lang_e, "宋代（尚书二十四司）")
    lang_reform = tp(
        w, lang_e, "北宋元丰新制", "职方司长官",
        i, staff, "职方司郎官", "据职方司编制建立郎中元丰节点。", "编制", chain="none",
    )
    chain_all(w, lang_e, [lang_general, lang_reform], "连接职方司郎中既有宋代节点与元丰节点。")
    rel(w, reform, lang_reform, "编制隶属", i, staff, "元丰职方司置郎中一人。", "编制",
        staff_quota=1, staff_type="官")
    yuan_e = w.entity("职方司员外郎", "官职", "职方司编制明确元丰置员外郎一人。", quotation=staff)
    yuan_t = tp(
        w, yuan_e, "北宋元丰新制", "职方司副长官",
        i, staff, "职方司郎官", "据职方司编制建立员外郎元丰节点。", "编制",
    )
    rel(w, reform, yuan_t, "编制隶属", i, staff, "元丰职方司置员外郎一人。", "编制",
        staff_quota=1, staff_type="官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1171, 1191)] == [
        "兵部甲库", "兵部尚书", "权兵部尚书", "兵部侍郎", "权兵部侍郎",
        "兵部赏功案", "兵部民兵仗卫案", "兵部厢兵案", "兵部人从看详案",
        "兵部帐籍告身案", "兵部武举案", "兵部蕃官案", "兵部检法案",
        "兵部开拆案", "兵部知杂案", "兵部四司", "兵部司", "兵部司郎中",
        "兵部司员外郎", "职方司",
    ]
    entry1171()
    entry1172()
    entry1173()
    entry1174()
    entry1175()
    bingbu_case(1176, "兵部赏功案", "掌民兵、厢军、土军、蕃兵军功赏给")
    bingbu_case(1177, "兵部民兵仗卫案", "掌民兵与仗卫")
    bingbu_case(1178, "兵部厢兵案", "掌厢军充役")
    bingbu_case(1179, "兵部人从看详案", "掌文武官因公差借兵士、剩员供役")
    bingbu_case(1180, "兵部帐籍告身案", "掌军兵名籍、兵帐及颁给告身")
    bingbu_case(1181, "兵部武举案", "掌武人贡举")
    bingbu_case(1182, "兵部蕃官案", "掌蕃官、属户授官封装")
    bingbu_case(1183, "兵部检法案", "掌兵部法令条例检阅")
    bingbu_case(1184, "兵部开拆案", "掌兵部文书收发")
    bingbu_case(1185, "兵部知杂案", "掌兵部具体事务与后勤总务")
    entry1186()
    entry1187()
    entry1188()
    entry1189()
    entry1190()


if __name__ == "__main__":
    main()
