#!/usr/bin/env python3
"""提取 chapter2t4 第1251–1270条：工部长贰、工部四司及其郎官。"""
import extract_2t4_1231_1250 as x


base = x.base
base.F = {i: base.load(i) for i in range(1251, 1271)}
base.F[1246] = base.load(1246)
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
remove_stale_staff_relations = x.remove_stale_staff_relations
mark_citation_conflict = base.mark_citation_conflict


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def remove_stale_parent_relation(w, parent_timepoint, office_entity, keep_relation):
    """移除早期泛化数据把宋前期工部误连到元丰四司节点的关系。"""
    rows = w.conn.execute(
        "select r.id from Relationships r join Timepoints o on o.id=r.object_id "
        "where r.subject_id=? and r.relation_type='上下级机构' and o.entity_id=?",
        (parent_timepoint, office_entity),
    ).fetchall()
    for (relationship_id,) in rows:
        if relationship_id == keep_relation:
            continue
        citation_ids = [
            row[0] for row in w.conn.execute(
                "select id from Citations "
                "where target_table='Relationships' and target_id=?",
                (relationship_id,),
            )
        ]
        for citation_id in citation_ids:
            w.conn.execute(
                "delete from BuildRecords "
                "where target_table='Citations' and target_id=?",
                (citation_id,),
            )
        w.conn.execute(
            "delete from Citations "
            "where target_table='Relationships' and target_id=?",
            (relationship_id,),
        )
        w.conn.execute(
            "delete from BuildRecords "
            "where target_table='Relationships' and target_id=?",
            (relationship_id,),
        )
        w.conn.execute("delete from Relationships where id=?", (relationship_id,))
        w._br(
            "Relationships",
            keep_relation,
            f"移除宋前期工部误连元丰四司节点的旧关系 {relationship_id}；"
            "保留专条建立的同阶段关系。",
        )


def refine_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    tid = refine(
        w, ft(w, eid, "北宋元丰新制"), i, main,
        f"专条细化{title}职掌。", None,
        event=event, category="工部办事机构",
    )
    chain_all(w, eid, [tid], f"确认{title}现有完整时间链。")
    w.commit()


def entry1254():
    i = 1254
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity(
        "判尚书省工部事", "官职", "本条直接定义宋前期判工部差遣。",
        quotation=main,
    )
    song = tp(
        w, eid, "宋前期", "判工部事，守部而几无职事",
        i, duty, "六部判部差遣", "建立判尚书省工部事宋前期节点。",
        "职掌",
    )
    cite(
        w, "Timepoints", song, i, origin,
        "隋代同名判工部尚书事与宋代职任不同，仅作判名来源证据。",
        "职源", note="异制同名，不建前后演变",
    )
    cite(w, "Timepoints", song, i, rank, "补证以两制以上朝官充任。", "品位")
    cite(
        w, "Timepoints", song, i, aliases,
        "简称‘判工部’仅作称谓证据。", "简称", note="纯简称",
    )
    office = ft(w, fe(w, "工部", "机构"), "宋前期")
    rel(
        w, office, song, "编制隶属", i, aliases,
        "宋前期工部置判部事一人。", "简称",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1255():
    i = 1255
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "工部尚书", "官职")
    sui = tp(
        w, eid, "隋", "工部尚书之名始置，隶尚书省",
        i, origin, "工部长官", "建立工部尚书隋代职源节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代", "宋前期"), i, duty,
        "专条细化工部尚书宋前期阶官性质。", "职掌",
        time="宋前期",
        event="无职事，为文臣寄禄官阶，元丰后寄禄官易银青光禄大夫",
        category="文臣迁转官阶", grade="正三品",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期正三品。", "官品")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化工部尚书元丰职事。", "职掌",
        event="工部长官，领工部职事", category="工部长官", grade="从二品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从二品。", "官品")
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与拟古称谓仅作称谓证据。",
        "简称与别名", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [sui, song, reform], "连接工部尚书隋、宋前期与元丰节点。")
    office_e = fe(w, "工部", "机构")
    rel(
        w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期工部尚书为无职事阶官。", "职掌", staff_type="官",
    )
    rel(
        w, ft(w, office_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        "元丰工部尚书为一部长官。", "职掌",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1256():
    i = 1256
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "权工部尚书", "官职")
    old = ft(w, eid, "北宋元祐三年闰十二月二十八日")
    new = tp(
        w, eid, "北宋元祐三年闰十二月十八日",
        "始置，以安排资格未及而职务需要的新进之士",
        i, origin, "权摄六部长官", "据专条保留十八日异文节点。",
        "职源", chain="none", attr_grade="正三品",
    )
    mark_citation_conflict(
        w, "Timepoints", new, i, origin,
        "本条作闰十二月十八日；第955条‘权六部尚书’作闰十二月二十八日。",
        "两条辞典原文日期相差十日，双节点保留。", "职源",
    )
    cite(w, "Timepoints", new, i, duty, "补证与工部尚书职掌相同。", "职掌")
    cite(w, "Timepoints", new, i, rank, "补证正三品及位次。", "品位")
    cite(
        w, "Timepoints", new, i, aliases,
        "简称仅作称谓证据。", "简称", note="纯简称",
    )
    cite(w, "Timepoints", new, i, main, "正文补证为职事官。")
    old_citations = w.conn.execute(
        "select id from Citations "
        "where target_table='Timepoints' and target_id=? and conflict_flag=0",
        (old,),
    ).fetchall()
    for (citation_id,) in old_citations:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?",
            (
                "第955条作闰十二月二十八日；"
                "第1256条专条作闰十二月十八日。",
                citation_id,
            ),
        )
        w._br(
            "Citations", citation_id,
            "将权工部尚书二十八日旧证与专条十八日异文显式标冲突。",
        )
    chain_all(w, eid, [new, old], "按十八日、二十八日顺序保留权工部尚书日期异文。")
    rel(
        w, ft(w, fe(w, "工部", "机构"), "北宋元丰新制"), new,
        "编制隶属", i, duty, "权工部尚书为工部长官权官。",
        "职掌", staff_type="官",
    )
    w.commit()


def entry1257():
    i = 1257
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "工部侍郎", "官职")
    sui = tp(
        w, eid, "隋大业三年", "尚书省工部侍郎始置",
        i, origin, "工部副长官", "建立工部侍郎隋代职源节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "北宋元丰改制前", "宋前期"), i, duty,
        "专条细化工部侍郎宋前期阶官性质。", "职掌",
        time="宋前期",
        event="无职事，为后行侍郎寄禄官阶，元丰后寄禄官易正议大夫",
        category="文臣迁转官阶", grade="正四品下",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期正四品下。", "官品")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化工部侍郎元丰职事。", "职掌",
        event="工部副长官，佐尚书领部事", category="工部副长官", grade="从三品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从三品。", "官品")
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与拟古称谓仅作称谓证据。",
        "简称与别名", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [sui, song, reform], "连接工部侍郎隋、宋前期与元丰节点。")
    office_e = fe(w, "工部", "机构")
    rel(
        w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期工部侍郎为无职事阶官。", "职掌", staff_type="官",
    )
    rel(
        w, ft(w, office_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        "元丰工部置侍郎一人为副长官。", "职掌",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1258():
    i = 1258
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "官品")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "权工部侍郎", "官职")
    tid = refine(
        w, ft_any(w, eid, "北宋元祐二年", "北宋元祐二年七月四日"),
        i, origin, "专条给出权工部侍郎精确始置日期。", "职源",
        time="北宋元祐二年七月四日",
        event="始置，未历两省及待制以上者任侍郎例带权字",
        category="权摄六部副长官", grade="从四品",
    )
    cite(w, "Timepoints", tid, i, duty, "补证职掌与正工部侍郎同。", "职掌")
    cite(w, "Timepoints", tid, i, rank, "补证从四品。", "官品")
    cite(
        w, "Timepoints", tid, i, aliases,
        "简称仅作称谓证据。", "简称", note="纯简称",
    )
    cite(w, "Timepoints", tid, i, main, "正文补证为职事官。")
    rel(
        w, ft(w, fe(w, "工部", "机构"), "北宋元丰新制"), tid,
        "编制隶属", i, duty, "权工部侍郎为工部侍郎权官。",
        "职掌", staff_type="官",
    )
    w.commit()


def prebuild_posts(w, i, office_timepoint, office_title, staff_quote,
                   titles=("郎中", "员外郎")):
    result = {}
    for suffix in titles:
        title = office_title + suffix
        event = f"{office_title}长官" if suffix == "郎中" else f"{office_title}副长官"
        post_e = w.entity(
            title, "官职", f"编制明确元丰置{title}一人。",
            quotation=staff_quote,
        )
        post_t = tp(
            w, post_e, "北宋元丰新制", event,
            i, staff_quote, f"{office_title}郎官", f"建立{title}元丰节点。",
            "编制", chain="none",
        )
        correct = rel(
            w, office_timepoint, post_t, "编制隶属", i, staff_quote,
            f"元丰{office_title}置{suffix}一人。", "编制",
            staff_quota=1, staff_type="官",
        )
        remove_stale_staff_relations(
            w, office_timepoint, post_e, post_t, correct,
        )
        result[suffix] = (post_e, post_t)
    return result


def entry1259():
    i = 1259
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "工部司", "机构")
    sui = tp(
        w, eid, "隋", "尚书省工部工部司之名始置",
        i, origin, "工部所属司", "建立工部司隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "沿置但无职事",
        i, duty, "工部所属司", "建立工部司宋前期无职事节点。",
        "职掌", chain="none",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化工部司元丰职掌。", "职掌",
        event="佐工部长贰，按程式分授制作、修造、计划与采伐材物",
        category="工部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证郎官各一人。", "编制")
    jianyan = tp(
        w, eid, "南宋建炎、绍兴间", "工部司郎官兼领虞部司郎官",
        i, staff, "工部所属司", "建立工部司建炎绍兴兼领节点。",
        "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴元年", "工部四司合一，由一员郎官统领",
        i, staff, "工部所属司", "建立工部司隆兴四司合一节点。",
        "编制", chain="none",
    )
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称仅作称谓证据。", "简称", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证工部司为四司头司。")
    chain_all(
        w, eid, [sui, song, reform, jianyan, longxing],
        "连接工部司隋至南宋隆兴完整时间链。",
    )
    parent_e = fe(w, "工部", "机构")
    song_rel = rel(
        w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期工部司为工部所属四司头司。",
    )
    remove_stale_parent_relation(
        w, ft(w, parent_e, "宋前期"), eid, song_rel,
    )
    rel(
        w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰工部司隶工部。", "职掌",
    )
    rel(
        w, ft(w, parent_e, "南宋隆兴后"), longxing, "上下级机构", i, staff,
        "隆兴工部四司合一后仍隶工部。", "编制",
    )
    prebuild_posts(w, i, reform, "工部司", staff)
    w.commit()


def office_post(i, title, office_title, origin_nodes, song_event, reform_event,
                song_grade, reform_grade, aliases_field, category,
                later_nodes=()):
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, aliases_field)
    w = W(i)
    eid = fe(w, title, "官职")
    ordered = []
    for time, event in origin_nodes:
        ordered.append(tp(
            w, eid, time, event, i, origin, category,
            f"建立{title}{time}职源节点。", "职源", chain="none",
        ))
    generic = (
        w.find_timepoint(eid, "宋代（尚书二十四司）")
        or w.find_timepoint(eid, "宋前期")
    )
    if generic:
        song = refine(
            w, generic, i, duty, f"专条细化{title}宋前期阶官性质。", "职掌",
            time="宋前期", event=song_event, category="文臣迁转官阶",
            grade=song_grade,
        )
    else:
        song = tp(
            w, eid, "宋前期", song_event, i, duty, "文臣迁转官阶",
            f"建立{title}宋前期阶官节点。", "职掌", chain="none",
            attr_grade=song_grade,
        )
    cite(w, "Timepoints", song, i, grade, f"补证宋前期{song_grade}。", "官品")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        f"专条细化{title}元丰职事。", "职掌",
        event=reform_event, category=category, grade=reform_grade,
    )
    cite(w, "Timepoints", reform, i, grade, f"补证元丰后{reform_grade}。", "官品")
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与别名仅作称谓证据。",
        aliases_field, note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    later = []
    for time, event, source_i, quotation, source_field in later_nodes:
        later.append(tp(
            w, eid, time, event, source_i, quotation, category,
            f"建立{title}{time}编制变化节点。",
            source_field, chain="none", attr_grade=reform_grade,
        ))
    chain_all(
        w, eid, ordered + [song, reform] + later,
        f"重建{title}职源至宋代完整时间链。",
    )
    office_e = fe(w, office_title, "机构")
    rel(
        w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        f"宋前期{title}为无职事阶官。", "职掌", staff_type="官",
    )
    rel(
        w, ft(w, office_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        f"元丰{office_title}置{title}一人。", "职掌",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry1262():
    i = 1262
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    water_staff = field(1269, "编制")
    w = W(i)
    eid = fe(w, "屯田司", "机构")
    jin = tp(
        w, eid, "晋", "已有尚书屯田郎，为屯田司名源",
        i, origin, "工部所属司", "建立屯田司晋代名源节点。",
        "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "始置尚书省工部屯田司",
        i, origin, "工部所属司", "建立屯田司隋代始置节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "沿置但无职事，屯田事归三司",
        i, duty, "工部所属司", "建立屯田司宋前期无职事节点。",
        "职掌", chain="none",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化屯田司元丰职掌。", "职掌",
        event="掌屯田、营田、职分田、官庄、塘泊及租入等事务",
        category="工部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证郎官、三案与吏额。", "编制")
    shaosheng = tp(
        w, eid, "北宋绍圣元年", "与虞部司互置一员郎官兼领",
        i, staff, "工部所属司", "建立屯田司绍圣兼领节点。",
        "编制", chain="none",
    )
    jianyan = tp(
        w, eid, "南宋建炎三年", "屯田郎官兼领水部司郎官",
        1269, water_staff, "工部所属司", "据水部司编制建立屯田司建炎兼领节点。",
        "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴元年", "工部四司合一，由一员郎官统领",
        i, staff, "工部所属司", "建立屯田司隆兴四司合一节点。",
        "编制", chain="none",
    )
    chunxi = tp(
        w, eid, "南宋淳熙九年", "复置屯田司员外郎一员，此后不罢",
        i, staff, "工部所属司", "建立屯田司淳熙恢复员外郎节点。",
        "编制", chain="none",
    )
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与别名仅作称谓证据。",
        "简称与别名", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证屯田司为工部四司之一。")
    chain_all(
        w, eid, [jin, sui, song, reform, shaosheng, jianyan, longxing, chunxi],
        "连接屯田司晋代名源至南宋淳熙完整时间链。",
    )
    parent_e = fe(w, "工部", "机构")
    song_rel = rel(
        w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期屯田司为工部所属四司之一。",
    )
    remove_stale_parent_relation(
        w, ft(w, parent_e, "宋前期"), eid, song_rel,
    )
    rel(
        w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰屯田司隶工部。", "职掌",
    )
    rel(
        w, ft(w, parent_e, "南宋隆兴后"), longxing, "上下级机构", i, staff,
        "隆兴屯田司并入四司合领格局。", "编制",
    )
    judge_e = w.entity(
        "判屯田司事", "官职", "编制明确宋前期置判屯田司事一人。",
        quotation=staff,
    )
    judge_t = tp(
        w, judge_e, "宋前期", "主判屯田司事",
        i, staff, "判司差遣", "建立判屯田司事宋前期节点。",
        "编制",
    )
    rel(
        w, song, judge_t, "编制隶属", i, staff,
        "宋前期屯田司置判司事一人。", "编制",
        staff_quota=1, staff_type="官",
    )
    prebuild_posts(w, i, reform, "屯田司", staff)
    w.commit()


def entry1265():
    i = 1265
    main = Q(i, F[i]["text"])
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "虞部司", "机构")
    wei = tp(
        w, eid, "三国魏", "已有虞曹",
        i, origin, "工部所属司", "建立虞部司三国魏职源节点。",
        "职源与沿革", chain="none",
    )
    zhou = tp(
        w, eid, "北周", "已有虞部之称",
        i, origin, "工部所属司", "建立虞部司北周名源节点。",
        "职源与沿革", chain="none",
    )
    sui = tp(
        w, eid, "隋初", "始置尚书省虞部司",
        i, origin, "工部所属司", "建立虞部司隋代始置节点。",
        "职源与沿革", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "沿置但无职事",
        i, duty, "工部所属司", "建立虞部司宋前期无职事节点。",
        "职掌", chain="none",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化虞部司元丰职掌。", "职掌",
        event="掌山林湖泊物产开采、猎取、废置等政令与事务",
        category="工部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证郎官、三案与吏额。", "编制")
    shaosheng = tp(
        w, eid, "北宋绍圣元年", "与屯田司共置一员郎官兼领",
        i, staff, "工部所属司", "建立虞部司绍圣兼领节点。",
        "编制", chain="none",
    )
    jianyan = tp(
        w, eid, "南宋建炎三年", "由工部司郎官兼领",
        i, staff, "工部所属司", "建立虞部司建炎兼领节点。",
        "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴元年", "工部四司合一，共置一员郎官",
        i, staff, "工部所属司", "建立虞部司隆兴四司合一节点。",
        "编制", chain="none",
    )
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与别名仅作称谓证据。",
        "简称与别名", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证虞部司为工部四司之一。")
    chain_all(
        w, eid, [wei, zhou, sui, song, reform, shaosheng, jianyan, longxing],
        "连接虞部司三国魏职源至南宋隆兴完整时间链。",
    )
    parent_e = fe(w, "工部", "机构")
    song_rel = rel(
        w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期虞部司为工部所属四司之一。",
    )
    remove_stale_parent_relation(
        w, ft(w, parent_e, "宋前期"), eid, song_rel,
    )
    rel(
        w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰虞部司隶工部。", "职掌",
    )
    rel(
        w, ft(w, parent_e, "南宋隆兴后"), longxing, "上下级机构", i, staff,
        "隆兴虞部司并入四司合领格局。", "编制",
    )
    judge_e = w.entity(
        "判虞部司事", "官职", "编制明确宋前期置判虞部司事一人。",
        quotation=staff,
    )
    judge_t = tp(
        w, judge_e, "宋前期", "主判虞部司事",
        i, staff, "判司差遣", "建立判虞部司事宋前期节点。",
        "编制",
    )
    rel(
        w, song, judge_t, "编制隶属", i, staff,
        "宋前期虞部司置判司事一人。", "编制",
        staff_quota=1, staff_type="官",
    )
    prebuild_posts(w, i, reform, "虞部司", staff)
    w.commit()


def entry1269():
    i = 1269
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "水部司", "机构")
    wei = tp(
        w, eid, "三国魏", "已有水部曹之名",
        i, origin, "工部所属司", "建立水部司三国魏职源节点。",
        "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "始置尚书省工部水部司",
        i, origin, "工部所属司", "建立水部司隋代始置节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "沿置但无职守",
        i, duty, "工部所属司", "建立水部司宋前期无职事节点。",
        "职掌", chain="none",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化水部司元丰职掌。", "职掌",
        event="掌河流、水渠、堤防、渡桥、舟船漕运与水碾等事务",
        category="工部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证郎官、四案与吏额。", "编制")
    jianyan = tp(
        w, eid, "南宋建炎三年", "由屯田司郎官兼领",
        i, staff, "工部所属司", "建立水部司建炎兼领节点。",
        "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴元年", "工部四司合一，由一员郎官通治",
        i, staff, "工部所属司", "建立水部司隆兴四司合一节点。",
        "编制", chain="none",
    )
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称与别名仅作称谓证据。",
        "简称与别名", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证水部司为工部四司之一。")
    chain_all(
        w, eid, [wei, sui, song, reform, jianyan, longxing],
        "连接水部司三国魏职源至南宋隆兴完整时间链。",
    )
    parent_e = fe(w, "工部", "机构")
    song_rel = rel(
        w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期水部司为工部所属四司之一。",
    )
    remove_stale_parent_relation(
        w, ft(w, parent_e, "宋前期"), eid, song_rel,
    )
    rel(
        w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰水部司隶工部。", "职掌",
    )
    rel(
        w, ft(w, parent_e, "南宋隆兴后"), longxing, "上下级机构", i, staff,
        "隆兴水部司并入四司合领格局。", "编制",
    )
    judge_e = w.entity(
        "判水部司事", "官职", "编制明确宋前期置判水部司事一人。",
        quotation=staff,
    )
    judge_t = tp(
        w, judge_e, "宋前期", "主判水部司事",
        i, staff, "判司差遣", "建立判水部司事宋前期节点。",
        "编制",
    )
    rel(
        w, song, judge_t, "编制隶属", i, staff,
        "宋前期水部司置判司事一人。", "编制",
        staff_quota=1, staff_type="官",
    )
    prebuild_posts(w, i, reform, "水部司", staff)
    w.commit()


def entry1270():
    i = 1270
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty_and_grade = field(i, "职掌")
    aliases = field(i, "简称")
    water_staff = field(1269, "编制")
    w = W(i)
    eid = fe(w, "水部司郎中", "官职")
    tang = tp(
        w, eid, "唐武德三年", "始置尚书省工部水部司郎中",
        i, origin, "水部司郎官", "建立水部司郎中唐代职源节点。",
        "职源", chain="none",
    )
    generic = ft_any(w, eid, "宋代（尚书二十四司）", "宋前期")
    song = refine(
        w, generic, i, duty_and_grade,
        "专条细化水部司郎中宋前期阶官性质。", "职掌",
        time="宋前期",
        event="无职事，为后行郎中寄禄官阶，元丰后寄禄官易朝奉大夫",
        category="文臣迁转官阶",
    )
    old_song_grade = w.conn.execute(
        "select attr_grade from Timepoints where id=?", (song,)
    ).fetchone()[0]
    if old_song_grade is not None:
        w.conn.execute(
            "update Timepoints set attr_grade=null where id=?", (song,)
        )
        w._br(
            "Timepoints", song,
            "原泛化节点的从六品属于元丰职事官；专条未载宋前期品级，"
            "细分宋前期节点时清除错带官品。",
        )
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), 1269, water_staff,
        "水部司总条补证元丰置郎中一人。", "编制",
        event="水部司长官", category="水部司郎官", grade="从六品",
    )
    cite(
        w, "Timepoints", reform, i, duty_and_grade,
        "原书将元丰后从六品排在职掌栏下，据其内容补证官品。",
        "职掌", note="原书栏目标作职掌，内容为官品",
    )
    cite(
        w, "Timepoints", reform, i, aliases,
        "简称仅作称谓证据。", "简称", note="纯简称",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(
        w, eid, [tang, song, reform],
        "连接水部司郎中唐代职源、宋前期与元丰节点。",
    )
    office_e = fe(w, "水部司", "机构")
    rel(
        w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty_and_grade,
        "宋前期水部司郎中为无职事阶官。", "职掌", staff_type="官",
    )
    rel(
        w, ft(w, office_e, "北宋元丰新制"), reform, "编制隶属",
        1269, water_staff, "元丰水部司置郎中一人。", "编制",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def finalize_four_offices():
    i = 1259
    main = Q(i, F[i]["text"])
    aliases = field(i, "简称")
    staff = field(i, "编制")
    yu_staff = field(1265, "编制")
    water_staff = field(1269, "编制")
    w = W(i)
    eid = w.entity(
        "工部四司", "机构", "本条列明工部四司及其四个实例。",
        quotation=aliases,
    )
    reform = tp(
        w, eid, "北宋元丰新制", "工部司、屯田司、虞部司、水部司的合称",
        i, aliases, "机构统称", "建立工部四司元丰节点。",
        "简称", chain="none",
    )
    cite(w, "Timepoints", reform, i, main, "正文补证工部司为四司头司。")
    jianyan = tp(
        w, eid, "南宋建炎三年",
        "四司仍存，分别由工部、屯田郎官兼领虞部、水部郎官",
        1265, yu_staff, "机构统称", "建立工部四司建炎兼领节点。",
        "编制", chain="none",
    )
    cite(
        w, "Timepoints", jianyan, 1269, water_staff,
        "补证屯田郎官兼领水部郎官。", "编制",
    )
    longxing = tp(
        w, eid, "南宋隆兴元年", "四司合一，由一员郎官统领",
        i, staff, "机构统称", "建立工部四司隆兴合一节点。",
        "编制", chain="none",
    )
    chain_all(w, eid, [reform, jianyan, longxing], "连接工部四司元丰、建炎与隆兴节点。")
    office_times = {
        "工部司": ("南宋建炎、绍兴间", yu_staff),
        "屯田司": ("南宋建炎三年", water_staff),
        "虞部司": ("南宋建炎三年", yu_staff),
        "水部司": ("南宋建炎三年", water_staff),
    }
    for title in ("工部司", "屯田司", "虞部司", "水部司"):
        office_e = fe(w, title, "机构")
        rel(
            w, reform, ft(w, office_e, "北宋元丰新制"), "统称与实例",
            i, aliases, f"元丰工部四司包括{title}。", "简称",
        )
        middle_time, middle_quote = office_times[title]
        source_i = 1265 if title in ("工部司", "虞部司") else 1269
        rel(
            w, jianyan, ft(w, office_e, middle_time), "统称与实例",
            source_i, middle_quote, f"建炎兼领格局下工部四司包括{title}。",
            "编制",
        )
        rel(
            w, longxing, ft(w, office_e, "南宋隆兴元年"), "统称与实例",
            i, staff, f"隆兴合一格局下工部四司包括{title}。", "编制",
        )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1251, 1271)] == [
        "工部兵匠案", "工部检法案", "工部知杂案", "判尚书省工部事",
        "工部尚书", "权工部尚书", "工部侍郎", "权工部侍郎",
        "工部司", "工部司郎中", "工部司员外郎", "屯田司",
        "屯田司郎中", "屯田司员外郎", "虞部司", "虞部司郎中",
        "主簿", "虞部司员外郎", "水部司", "水部司郎中",
    ]
    assert F[1267]["fields"].get("__status__") == "placeholder"
    refine_case(1251, "工部兵匠案", "掌工部所辖院、所、场、务等服役兵匠")
    refine_case(1252, "工部检法案", "检阅工部有关诏令、条法")
    refine_case(1253, "工部知杂案", "料理工部具体杂务与后勤")
    entry1254()
    entry1255()
    entry1256()
    entry1257()
    entry1258()
    entry1259()
    office_post(
        1260, "工部司郎中", "工部司",
        (("唐武德三年", "始置工部司郎中"),),
        "无职事，为后行郎中寄禄官阶，元丰后寄禄官易朝奉大夫",
        "工部司长官，掌本司事", "从五品上", "从六品",
        "简称", "工部司郎官",
    )
    office_post(
        1261, "工部司员外郎", "工部司",
        (("隋开皇六年", "始置工部司员外郎"),),
        "无职事，为后行员外郎寄禄官阶，元丰后寄禄官易朝奉郎",
        "工部司副长官，佐领本司事", "从六品上", "正七品",
        "简称与别名", "工部司郎官",
    )
    entry1262()
    office_post(
        1263, "屯田司郎中", "屯田司",
        (("三国魏", "已有屯田郎中之名"), ("唐武德三年", "始置屯田司郎中")),
        "无职事，为后行郎中寄禄官阶，元丰后寄禄官易朝奉大夫",
        "屯田司长官，领本司职事", "从五品上", "从六品",
        "简称", "屯田司郎官",
    )
    tuntian_staff = field(1262, "编制")
    office_post(
        1264, "屯田司员外郎", "屯田司",
        (("隋开皇六年", "始置屯田司员外郎"),),
        "无职事，为后行员外郎寄禄官阶，元丰后寄禄官易朝奉郎",
        "屯田司副长官，佐郎中掌本司事", "从六品上", "正七品",
        "简称与别名", "屯田司郎官",
        later_nodes=((
            "南宋淳熙九年", "复置一员，此后不罢",
            1262, tuntian_staff, "编制",
        ),),
    )
    entry1265()
    office_post(
        1266, "虞部司郎中", "虞部司",
        (("三国魏", "已有虞曹郎中"), ("唐武德三年", "始置虞部司郎中")),
        "无职事，为后行郎中寄禄官阶，元丰后寄禄官易朝奉大夫",
        "虞部司长官，领本司事", "从五品上", "从六品",
        "简称", "虞部司郎官",
    )
    office_post(
        1268, "虞部司员外郎", "虞部司",
        (
            ("隋开皇六年", "始置虞部司员外郎"),
            ("隋大业年间", "改称虞部司承务郎"),
            ("唐武德三年", "复称虞部司员外郎"),
        ),
        "无职事，为后行员外郎寄禄官阶，元丰后寄禄官易朝奉郎",
        "虞部司副长官，佐郎中掌本司事", "从六品上", "正七品",
        "简称与别名", "虞部司郎官",
    )
    entry1269()
    entry1270()
    finalize_four_offices()


if __name__ == "__main__":
    main()
