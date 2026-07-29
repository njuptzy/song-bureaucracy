#!/usr/bin/env python3
"""提取 chapter2t4 第1211–1230条：刑部诸案、长贰、刑部司与都官司。"""
import extract_2t4_1191_1210 as x


base = x.base
base.F = {i: base.load(i) for i in range(1211, 1231)}
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


def remove_stale_staff_relations(w, subject_id, post_entity_id, keep_object_id, keep_relation_id):
    """移除早期二十四司泛化关系在专条细化后留下的错时端点。"""
    rows = w.conn.execute(
        "select r.id from Relationships r join Timepoints o on o.id=r.object_id "
        "where r.subject_id=? and r.relation_type='编制隶属' and o.entity_id=? "
        "and r.object_id<>?",
        (subject_id, post_entity_id, keep_object_id),
    ).fetchall()
    for (relationship_id,) in rows:
        citation_ids = [row[0] for row in w.conn.execute(
            "select id from Citations where target_table='Relationships' and target_id=?",
            (relationship_id,),
        )]
        for citation_id in citation_ids:
            w.conn.execute(
                "delete from BuildRecords where target_table='Citations' and target_id=?",
                (citation_id,),
            )
        w.conn.execute(
            "delete from Citations where target_table='Relationships' and target_id=?",
            (relationship_id,),
        )
        w.conn.execute(
            "delete from BuildRecords where target_table='Relationships' and target_id=?",
            (relationship_id,),
        )
        w.conn.execute("delete from Relationships where id=?", (relationship_id,))
        w._br(
            "Relationships", keep_relation_id,
            f"移除旧泛化编制关系 {relationship_id}；专条已将郎官区分为宋前期阶官与元丰职事官。",
        )


def refine_case(i, title, north_event=None, south_event=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    ordered = []
    north = w.find_timepoint(eid, "北宋元丰新制")
    if north is not None:
        north = refine(
            w, north, i, main, f"专条细化{title}元丰职掌。", None,
            event=north_event, category="刑部办事机构",
        )
        ordered.append(north)
    south = w.find_timepoint(eid, "南宋初") or w.find_timepoint(eid, "南宋绍兴后")
    if south is not None:
        south = refine(
            w, south, i, main, f"专条细化{title}绍兴后职掌。", None,
            time="南宋绍兴后", event=south_event or north_event, category="刑部办事机构",
        )
        ordered.append(south)
    chain_all(w, eid, ordered, f"确认{title}现有完整时间链。")
    w.commit()


def entry1223():
    i = 1223
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "刑部尚书", "官职")
    sui = tp(
        w, eid, "隋开皇三年", "改都官尚书为刑部尚书，始有本名",
        i, origin, "刑部长官", "建立刑部尚书隋代职源节点。", "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代", "宋前期"), i, duty,
        "专条细化刑部尚书宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为文臣迁转阶官，元丰后寄禄官易银青光禄大夫",
        category="文臣迁转官阶", grade="正三品",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期正三品。", "官品")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化刑部尚书元丰职掌。", "职掌",
        event="刑部长官，总掌刑法政令、重大刑狱复核、官员叙复、平反冤狱及修理条法",
        category="刑部长官", grade="从二品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从二品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [sui, song, reform], "重建刑部尚书隋至元丰完整时间链。")
    parent_e = fe(w, "刑部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期刑部尚书为无职事阶官。", "职掌", staff_quota=1, staff_type="官")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        "元丰刑部置尚书一人为长官。", "职掌", staff_quota=1, staff_type="官")
    w.commit()


def entry1224():
    i = 1224
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "权刑部尚书", "官职")
    old = ft(w, eid, "北宋元祐三年闰十二月二十八日")
    new = tp(
        w, eid, "北宋元祐三年闰十二月十八日", "始置，以安排资格未及的新进之士",
        i, origin, "权摄六部长官", "据专条保留十八日异文节点。",
        "职源", chain="none", attr_grade="正三品",
    )
    mark_citation_conflict(
        w, "Timepoints", new, i, origin,
        "本条作闰十二月十八日；第955条‘权六部尚书’作闰十二月二十八日。",
        "两条辞典原文日期相差十日，双节点保留。", "职源",
    )
    cite(w, "Timepoints", new, i, duty, "补证职掌与刑部尚书同。", "职掌")
    cite(w, "Timepoints", new, i, grade, "补证正三品。", "官品")
    cite(w, "Timepoints", new, i, aliases, "简称仅作称谓证据。", "简称与别名", note="纯简称")
    cite(w, "Timepoints", new, i, main, "正文补证为元祐初始置职事官。")
    rows = w.conn.execute(
        "select id from Citations where target_table='Timepoints' and target_id=? and conflict_flag=0",
        (old,),
    ).fetchall()
    for (citation_id,) in rows:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?",
            ("第955条作闰十二月二十八日；第1224条专条作闰十二月十八日。", citation_id),
        )
        w._br("Citations", citation_id, "将权刑部尚书二十八日旧证与专条十八日异文显式标冲突。")
    chain_all(w, eid, [new, old], "按十八日、二十八日顺序保留权刑部尚书日期异文。")
    rel(w, ft(w, fe(w, "刑部", "机构"), "北宋元丰新制"), new,
        "编制隶属", i, duty, "权刑部尚书为刑部长官权官。", "职掌", staff_type="官")
    w.commit()


def entry1225():
    i = 1225
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "刑部侍郎", "官职")
    sui = tp(
        w, eid, "隋大业三年", "始置尚书省刑部侍郎",
        i, origin, "刑部副长官", "建立刑部侍郎隋代职源节点。", "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "北宋元丰改制前", "宋前期"), i, duty,
        "专条细化刑部侍郎宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为中行侍郎寄禄官阶",
        category="文臣迁转官阶", grade="正四品下",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期正四品下。", "官品")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化刑部侍郎元丰职掌。", "职掌",
        event="刑部副长官，二员分左厅覆查大案、右厅叙复申理冤案，一员时通治两厅",
        category="刑部副长官", grade="从三品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从三品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [sui, song, reform], "重建刑部侍郎隋至元丰完整时间链。")
    parent_e = fe(w, "刑部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期刑部侍郎为无职事阶官。", "职掌", staff_quota=2, staff_type="官")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        "元丰刑部置侍郎二人分治左右厅。", "职掌", staff_quota=2, staff_type="官")
    w.commit()


def entry1226():
    i = 1226
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "别名")
    w = W(i)
    eid = fe(w, "权刑部侍郎", "官职")
    tid = refine(
        w, ft_any(w, eid, "北宋元祐二年", "北宋元祐二年七月四日"), i, origin,
        "专条给出权刑部侍郎精确始置日期。", "职源",
        time="北宋元祐二年七月四日", event="始置，资格低于正侍郎",
        category="权摄六部副长官", grade="从四品",
    )
    cite(w, "Timepoints", tid, i, duty, "补证职掌与刑部侍郎同而资格较低。", "职掌")
    cite(w, "Timepoints", tid, i, rank, "补证从四品及班位。", "品位")
    cite(w, "Timepoints", tid, i, aliases, "别名仅作称谓证据。", "别名", note="纯简称")
    cite(w, "Timepoints", tid, i, main, "正文补证为职事官。")
    chain_all(w, eid, [tid], "确认权刑部侍郎现有完整时间链。")
    rel(w, ft(w, fe(w, "刑部", "机构"), "北宋元丰新制"), tid,
        "编制隶属", i, duty, "权刑部侍郎为刑部侍郎权官。", "职掌", staff_type="官")
    w.commit()


def entry1227():
    i = 1227
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "刑部司", "机构")
    zhou = tp(w, eid, "北周", "秋官府属官已有刑部之称", i, origin,
              "刑部所属司", "建立刑部司北周名源节点。", "职源", chain="none")
    sui = tp(w, eid, "隋初", "始置都官尚书所属刑部司", i, origin,
             "刑部所属司", "建立刑部司隋初始置节点。", "职源", chain="none")
    kaihuang = tp(w, eid, "隋开皇三年", "都官尚书改刑部尚书，刑部司成为刑部头司", i, origin,
                  "刑部所属司", "建立刑部司隋开皇改隶节点。", "职源", chain="none")
    song = tp(w, eid, "宋前期", "沿置但无职事", i, duty,
              "刑部所属司", "建立刑部司宋前期无职事节点。", "职掌", chain="none")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化刑部司元丰职掌。", "职掌",
        event="分左、右曹治事，左掌详覆，右掌官员叙复与平反冤案", category="刑部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎中、员外郎各二人。", "编制")
    south = tp(w, eid, "南宋", "置郎官二员", i, staff,
               "刑部所属司", "建立刑部司南宋郎官编制节点。", "编制", chain="none")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证刑部司为刑部四司之一。")
    chain_all(w, eid, [zhou, sui, kaihuang, song, reform, south],
              "重建刑部司北周名源至南宋完整时间链。")
    parent_e = fe(w, "刑部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期刑部司为刑部所属四司之一。")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰刑部司隶刑部并分左右曹治事。", "职掌")
    w.commit()


def langguan(i, title, origin_time, origin_event, aliases_field, song_event,
             reform_event, song_grade, reform_grade):
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, aliases_field)
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}。", quotation=main)
    old = tp(w, eid, origin_time, origin_event, i, origin,
             "刑部司郎官", f"建立{title}{origin_time}职源节点。", "职源", chain="none")
    generic = w.find_timepoint(eid, "宋代（尚书二十四司）") or w.find_timepoint(eid, "宋前期")
    if generic:
        song = refine(w, generic, i, duty, f"专条细化{title}宋前期阶官性质。", "职掌",
                      time="宋前期", event=song_event, category="文臣迁转官阶", grade=song_grade)
    else:
        song = tp(w, eid, "宋前期", song_event, i, duty, "文臣迁转官阶",
                  f"建立{title}宋前期阶官节点。", "职掌", chain="none", attr_grade=song_grade)
    cite(w, "Timepoints", song, i, grade, f"补证宋前期{song_grade}。", "官品")
    reform = tp(w, eid, "北宋元丰新制", reform_event, i, duty,
                "刑部司郎官", f"建立{title}元丰职事节点。", "职掌", chain="none",
                attr_grade=reform_grade)
    cite(w, "Timepoints", reform, i, grade, f"补证元丰后{reform_grade}。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", aliases_field, note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [old, song, reform], f"重建{title}职源至元丰完整时间链。")
    office_e = fe(w, "刑部司", "机构")
    rel(w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        f"宋前期{title}为无职事阶官。", "职掌", staff_quota=2, staff_type="官")
    office_reform = ft(w, office_e, "北宋元丰新制")
    correct_rel = rel(w, office_reform, reform, "编制隶属", i, duty,
                      f"元丰刑部司置{title}二人分治左右厅。", "职掌",
                      staff_quota=2, staff_type="官")
    remove_stale_staff_relations(w, office_reform, eid, reform, correct_rel)
    w.commit()


def entry1230():
    i = 1230
    main = Q(i, F[i]["text"])
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "都官司", "机构")
    han = tp(w, eid, "西汉", "都官之名源于京师诸官府与从中都官徒", i, history,
             "刑部所属司", "建立都官司西汉名源节点。", "职源与沿革", chain="none")
    eastern = tp(w, eid, "东汉", "司隶校尉下设都官从事", i, history,
                 "刑部所属司", "建立都官司东汉职源节点。", "职源与沿革", chain="none")
    pre = tp(w, eid, "魏晋南朝", "沿有都官郎、都官郎中，但职任异于唐宋", i, history,
             "刑部所属司", "建立都官司魏晋南朝同名职源节点。", "职源与沿革", chain="none")
    sui = tp(w, eid, "隋", "始置都官曹司掌配隶，属尚书省刑部", i, history,
             "刑部所属司", "建立都官司隋代实质始置节点。", "职源与沿革", chain="none")
    song = tp(w, eid, "宋前期", "沿置但无职事", i, duty,
              "刑部所属司", "建立都官司宋前期无职事节点。", "职掌", chain="none")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化都官司元丰职掌。", "职掌",
        event="掌刑徒配隶、谋反家属没官、抄家及吏员废置增减出职", category="刑部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎官、四案与吏额。", "编制")
    jianyan = tp(w, eid, "南宋建炎三年", "都官郎一员，兼权比部司、司门司事", i, staff,
                 "刑部所属司", "建立都官司建炎兼领节点。", "编制", chain="none")
    longxing = tp(w, eid, "南宋隆兴后", "都官、比部、司门三司共置郎官一员", i, staff,
                  "刑部所属司", "建立都官司隆兴后三司合置节点。", "编制", chain="none")
    chunxi = tp(w, eid, "南宋淳熙十三年", "吏额由十二人减为九人", i, staff,
                "刑部所属司", "建立都官司淳熙减吏节点。", "编制", chain="none")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证都官司为刑部四司之一。")
    chain_all(w, eid, [han, eastern, pre, sui, song, reform, jianyan, longxing, chunxi],
              "重建都官司西汉名源至南宋淳熙完整时间链。")
    parent_e = fe(w, "刑部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期都官司为刑部所属四司之一。")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰都官司隶刑部并恢复职事。", "职掌")

    judge_e = w.entity("判都官司事", "官职", "编制明确宋前期置判都官司事一员。", quotation=staff)
    judge_t = tp(w, judge_e, "宋前期", "主判都官司事", i, staff,
                 "判司差遣", "建立判都官司事宋前期节点。", "编制")
    rel(w, song, judge_t, "编制隶属", i, staff, "宋前期都官司置判司事一员。", "编制",
        staff_quota=1, staff_type="官")
    for title, event in (("都官司郎中", "都官司长官"), ("都官司员外郎", "都官司副长官")):
        post_e = w.entity(title, "官职", f"编制明确元丰置{title}一人。", quotation=staff)
        post_t = tp(w, post_e, "北宋元丰新制", event, i, staff,
                    "都官司郎官", f"建立{title}元丰节点。", "编制", chain="none")
        existing = [row[0] for row in w.conn.execute(
            "select id from Timepoints where entity_id=? and id<>? order by id", (post_e, post_t)
        )]
        chain_all(w, post_e, existing + [post_t], f"连接{title}既有节点与元丰节点。")
        correct_rel = rel(
            w, reform, post_t, "编制隶属", i, staff, f"元丰都官司置{title}一人。", "编制",
            staff_quota=1, staff_type="官",
        )
        remove_stale_staff_relations(w, reform, post_e, post_t, correct_rel)

    north_cases = ("都官司军大将案", "都官司吏籍案", "都官司配隶案", "都官司知杂案")
    south_cases = ("都官司差次案", "都官司磨勘案", "都官司吏籍案", "都官司配隶案", "都官司知杂案")
    for title in north_cases:
        case_e = w.entity(title, "机构", f"都官司编制列举元丰{title}。", quotation=staff)
        case_t = tp(w, case_e, "北宋元丰新制", "都官司所属办事案", i, staff,
                    "都官司办事机构", f"建立{title}元丰节点。", "编制", chain="none")
        rel(w, reform, case_t, "上下级机构", i, staff, f"元丰{title}隶都官司。", "编制")
    for title in south_cases:
        case_e = w.entity(title, "机构", f"都官司编制列举南宋{title}。", quotation=staff)
        case_t = tp(w, case_e, "南宋隆兴后", "都官司所属办事案", i, staff,
                    "都官司办事机构", f"建立{title}南宋节点。", "编制", chain="none")
        ids = [row[0] for row in w.conn.execute(
            "select id from Timepoints where entity_id=? order by id", (case_e,)
        )]
        if len(ids) > 1:
            chain_all(w, case_e, ids, f"连接{title}元丰与南宋节点。")
        rel(w, longxing, case_t, "上下级机构", i, staff, f"南宋{title}隶都官司。", "编制")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1211, 1231)] == [
        "刑部举叙案", "刑部进拟案", "刑部随时拨却行案", "刑部随时拨却不行案",
        "刑部定夺案", "刑部纠察案", "刑部检法案", "刑部颁降案", "刑部追毁案",
        "刑部会问案", "刑部捕盗案", "刑部帐籍案", "刑部尚书", "权刑部尚书",
        "刑部侍郎", "权刑部侍郎", "刑部司", "刑部司郎中", "刑部司员外郎", "都官司",
    ]
    refine_case(1211, "刑部举叙案", "犯罪官员经大赦重新按格录用", "职掌与元丰同")
    refine_case(1212, "刑部进拟案", "上奏定案罪名文书", "职掌与元丰同")
    refine_case(1213, "刑部随时拨却行案", "移放罪人")
    refine_case(1214, "刑部随时拨却不行案", "移放编配罪人并登记备案")
    refine_case(1215, "刑部定夺案", south_event="办理冤案申诉与平反")
    refine_case(1216, "刑部纠察案", south_event="审问大辟案疑点")
    refine_case(1217, "刑部检法案", south_event="查照本部刑律条例并提供咨询")
    refine_case(1218, "刑部颁降案", south_event="遇赦宥颁布赦罪条法与规定")
    refine_case(1219, "刑部追毁案", south_event="追回并销毁犯法官员任命凭证")
    refine_case(1220, "刑部会问案", south_event="组织案犯会审对质")
    refine_case(1221, "刑部捕盗案", south_event="限期追捕奸盗")
    refine_case(1222, "刑部帐籍案", south_event="掌京师库务财会出纳帐册并督催失欠")
    entry1223()
    entry1224()
    entry1225()
    entry1226()
    entry1227()
    langguan(
        1228, "刑部司郎中", "唐武德三年", "始有尚书省刑部刑部司郎中之名", "简称与别名",
        "无职事，为中行郎中阶，元丰后寄禄官易朝散大夫",
        "刑部司长官，二员分领左右厅详覆、叙复和平反事务", "从五品上", "从六品",
    )
    langguan(
        1229, "刑部司员外郎", "隋开皇六年", "始置尚书省刑部刑部司员外郎", "简称",
        "无职事，为中行员外郎，元丰后寄禄官易朝散郎",
        "刑部司副长官，二员分治左右厅详覆、叙复和平反事务", "从六品上", "正七品",
    )
    entry1230()


if __name__ == "__main__":
    main()
