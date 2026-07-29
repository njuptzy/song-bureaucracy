#!/usr/bin/env python3
"""提取 chapter2t4 第1231–1250条：都官、比部、司门郎官及工部前段。"""
import extract_2t4_1211_1230 as x


base = x.base
base.F = {i: base.load(i) for i in range(1231, 1251)}
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


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def office_post(i, title, office_title, origin_nodes, song_event, reform_event,
                song_grade, reform_grade, aliases_field, category,
                quota=1):
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
            time="宋前期", event=song_event, category="文臣迁转官阶", grade=song_grade,
        )
    else:
        song = tp(
            w, eid, "宋前期", song_event, i, duty, "文臣迁转官阶",
            f"建立{title}宋前期阶官节点。", "职掌", chain="none",
            attr_grade=song_grade,
        )
    cite(w, "Timepoints", song, i, grade, f"补证宋前期{song_grade}。", "官品")
    reform_existing = w.find_timepoint(eid, "北宋元丰新制")
    if reform_existing:
        reform = refine(
            w, reform_existing, i, duty, f"专条细化{title}元丰职事。", "职掌",
            event=reform_event, category=category, grade=reform_grade,
        )
    else:
        reform = tp(
            w, eid, "北宋元丰新制", reform_event, i, duty, category,
            f"建立{title}元丰职事节点。", "职掌", chain="none",
            attr_grade=reform_grade,
        )
    cite(w, "Timepoints", reform, i, grade, f"补证元丰后{reform_grade}。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         aliases_field, note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, ordered + [song, reform], f"重建{title}职源至元丰完整时间链。")
    office_e = fe(w, office_title, "机构")
    rel(w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        f"宋前期{title}为无职事阶官。", "职掌",
        staff_quota=quota, staff_type="官")
    office_reform = ft(w, office_e, "北宋元丰新制")
    correct_rel = rel(
        w, office_reform, reform, "编制隶属", i, duty,
        f"元丰{office_title}置{title}{quota}人。", "职掌",
        staff_quota=quota, staff_type="官",
    )
    remove_stale_staff_relations(w, office_reform, eid, reform, correct_rel)
    w.commit()


def entry1235():
    i = 1235
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "比部司", "机构")
    wei = tp(w, eid, "三国魏", "已有比部曹之称", i, origin, "刑部所属司",
             "建立比部司三国魏职源节点。", "职源", chain="none")
    sui = tp(w, eid, "隋开皇三年", "始置尚书省刑部比部司", i, origin, "刑部所属司",
             "建立比部司隋代始置节点。", "职源", chain="none")
    song = tp(w, eid, "宋前期", "沿置但无职事，审计职事归三司勾院、磨勘理欠司",
              i, duty, "刑部所属司", "建立比部司宋前期无职事节点。", "职掌", chain="none")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化比部司元丰审计职掌。", "职掌",
        event="掌审核内外帐籍、追查侵吞经费并催索场务仓库欠物",
        category="中央审计机构",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎官、五案与吏额。", "编制")
    cite(w, "Timepoints", reform, i, grade, "补证官品参照刑部司员外郎。", "官品")
    yuanyou1 = tp(
        w, eid, "北宋元祐元年七月", "勾覆中外帐籍权划归户部仓部司",
        i, duty, "中央审计机构", "建立比部司元祐元年审计权转出节点。",
        "职掌", chain="none",
    )
    yuanyou3 = tp(
        w, eid, "北宋元祐三年", "勾覆、理欠、凭由及印发钞引职事由仓部司归还比部司",
        i, duty, "中央审计机构", "建立比部司元祐三年审计权恢复节点。",
        "职掌", chain="none",
    )
    jianyan = tp(
        w, eid, "南宋建炎三年", "不单独置郎官，由都官郎兼权比部司事",
        i, staff, "刑部所属司", "建立比部司建炎兼领节点。", "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与别名仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证比部司为刑部四司之一及中央审计机构。")
    chain_all(w, eid, [wei, sui, song, reform, yuanyou1, yuanyou3, jianyan],
              "重建比部司三国魏职源至南宋建炎完整时间链。")
    parent_e = fe(w, "刑部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期比部司为刑部所属四司之一。")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰比部司隶刑部并恢复审计职事。", "职掌")

    judge_e = w.entity("判比部司事", "官职", "编制明确宋前期置判比部司事一人。",
                       quotation=staff)
    judge_t = tp(w, judge_e, "宋前期", "主判比部司事", i, staff,
                 "判司差遣", "建立判比部司事宋前期节点。", "编制")
    rel(w, song, judge_t, "编制隶属", i, staff, "宋前期比部司置判司事一人。",
        "编制", staff_quota=1, staff_type="官")
    for title, event in (("比部司郎中", "比部司长官"), ("比部司员外郎", "比部司副长官")):
        post_e = w.entity(title, "官职", f"编制明确元丰置{title}一人。", quotation=staff)
        post_t = tp(w, post_e, "北宋元丰新制", event, i, staff, "比部司郎官",
                    f"建立{title}元丰节点。", "编制", chain="none")
        correct_rel = rel(w, reform, post_t, "编制隶属", i, staff,
                          f"元丰比部司置{title}一人。", "编制",
                          staff_quota=1, staff_type="官")
        remove_stale_staff_relations(w, reform, post_e, post_t, correct_rel)

    cases = ("比部司勾覆案", "比部司磨勘案", "比部司理欠案", "比部司凭由案", "比部司知杂案")
    for title in cases:
        case_e = w.entity(title, "机构", f"比部司编制列举{title}。", quotation=staff)
        case_t = tp(w, case_e, "北宋元丰新制", "比部司所属常设办事案", i, staff,
                    "比部司办事机构", f"建立{title}元丰节点。", "编制")
        rel(w, reform, case_t, "上下级机构", i, staff, f"{title}隶比部司。", "编制")
    w.commit()


def refine_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    tid = refine(w, ft(w, eid, "北宋元丰新制"), i, main,
                 f"专条细化{title}职掌。", None,
                 event=event, category="比部司办事机构")
    chain_all(w, eid, [tid], f"确认{title}现有完整时间链。")
    w.commit()


def entry1243():
    i = 1243
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "司门司", "机构")
    zhou = tp(w, eid, "先秦《周礼》", "已有司门官名，为司门司名源", i, origin,
              "刑部所属司", "建立司门司《周礼》名源节点。", "职源", chain="none")
    sui = tp(w, eid, "隋", "始置尚书省刑部司门司", i, origin,
             "刑部所属司", "建立司门司隋代始置节点。", "职源", chain="none")
    song = tp(w, eid, "宋前期", "沿置但无职事，门关归皇城司，桥渡道路归州县",
              i, duty, "刑部所属司", "建立司门司宋前期无职事节点。", "职掌", chain="none")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化司门司元丰职掌。", "职掌",
        event="掌门关、桥梁、渡口、辇道禁令及桥梁道路废置修复",
        category="刑部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎中、员外郎各一人。", "编制")
    longxing = tp(
        w, eid, "南宋隆兴元年后", "都官、比部、司门三司共置郎官一员",
        i, staff, "刑部所属司", "建立司门司隆兴后三司合置节点。", "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证司门司为刑部四司之一。")
    chain_all(w, eid, [zhou, sui, song, reform, longxing],
              "重建司门司《周礼》名源至南宋隆兴完整时间链。")
    parent_e = fe(w, "刑部", "机构")
    rel(w, ft(w, parent_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期司门司为刑部所属四司之一。")
    rel(w, ft(w, parent_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰司门司隶刑部并恢复职事。", "职掌")

    judge_e = w.entity("判司门司事", "官职", "编制明确宋前期置判司门司事一人。",
                       quotation=staff)
    judge_t = tp(w, judge_e, "宋前期", "主判司门司事", i, staff,
                 "判司差遣", "建立判司门司事宋前期节点。", "编制")
    rel(w, song, judge_t, "编制隶属", i, staff, "宋前期司门司置判司事一人。",
        "编制", staff_quota=1, staff_type="官")
    for title, event in (("司门司郎中", "司门司长官"), ("司门司员外郎", "司门司副长官")):
        post_e = w.entity(title, "官职", f"编制明确元丰置{title}一人。", quotation=staff)
        post_t = tp(w, post_e, "北宋元丰新制", event, i, staff, "司门司郎官",
                    f"建立{title}元丰节点。", "编制", chain="none")
        correct_rel = rel(w, reform, post_t, "编制隶属", i, staff,
                          f"元丰司门司置{title}一人。", "编制",
                          staff_quota=1, staff_type="官")
        remove_stale_staff_relations(w, reform, post_e, post_t, correct_rel)
    w.commit()


def entry1246():
    i = 1246
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "工部", "机构")
    western = tp(w, eid, "西魏", "始有工部之名", i, origin, "尚书省六部",
                 "建立工部西魏名源节点。", "职源", chain="none")
    zhou = tp(w, eid, "北周", "冬官府属置工部中大夫", i, origin, "尚书省六部",
              "建立工部北周职源节点。", "职源", chain="none")
    sui = tp(w, eid, "隋", "始置为尚书省六部之一", i, origin, "尚书省六部",
             "建立工部隋代入尚书省节点。", "职源", chain="none")
    song = refine(
        w, ft_any(w, eid, "宋代", "宋前期"), i, duty,
        "专条细化工部宋前期职权旁落。", "职掌",
        time="宋前期", event="土木建筑、工役归三司修造案，本部几无所掌",
        category="中央行政机构",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判工部一人。", "编制")
    reform = tp(
        w, eid, "北宋元丰新制", "掌城池屋宇街道桥梁修造、舟车器械制作及铸造钱宝",
        i, duty, "尚书省六部", "建立工部元丰恢复职事节点。", "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰十官、四司与六案。", "编制")
    shaoxing3 = tp(
        w, eid, "南宋绍兴三年", "少府监并入工部，长贰互置一员",
        i, staff, "尚书省六部", "建立工部绍兴三年并入少府监节点。", "编制", chain="none",
    )
    shaoxing5 = tp(
        w, eid, "南宋绍兴五年", "增立御前军器案",
        i, staff, "尚书省六部", "建立工部绍兴五年增案节点。", "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴后", "工部四司由一员郎官通领",
        i, staff, "尚书省六部", "建立工部隆兴后四司合领节点。", "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证工部为尚书省六部之一。")
    chain_all(w, eid, [western, zhou, sui, song, reform, shaoxing3, shaoxing5, longxing],
              "重建工部西魏名源至南宋隆兴完整时间链。")
    shangshu_e = fe(w, "尚书省", "机构")
    rel(w, ft(w, shangshu_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期工部为尚书省六部之一。")
    rel(w, ft(w, shangshu_e, "北宋元丰新制"), reform, "上下级机构", i, staff,
        "元丰工部为尚书省六部之一。", "编制")

    for title, event in (("工部尚书", "工部长官"), ("工部侍郎", "工部副长官")):
        post_e = fe(w, title, "官职")
        post_t = tp(w, post_e, "北宋元丰新制", event, i, staff, "工部长贰",
                    f"据工部编制建立{title}元丰节点。", "编制", chain="none")
        existing = [row[0] for row in w.conn.execute(
            "select id from Timepoints where entity_id=? and id<>? order by id",
            (post_e, post_t),
        )]
        chain_all(w, post_e, existing + [post_t], f"连接{title}既有节点与元丰节点。")
        rel(w, reform, post_t, "编制隶属", i, staff, f"元丰工部置{title}一人。",
            "编制", staff_quota=1, staff_type="官")

    for title in ("工部司", "屯田司", "虞部司", "水部司"):
        office_e = fe(w, title, "机构")
        office_t = refine(
            w, ft_any(w, office_e, "宋代（尚书二十四司）", "北宋元丰新制"),
            i, staff, f"工部总条明确{title}为元丰所属四司之一。", "编制",
            time="北宋元丰新制", event="工部所属四司之一", category="工部所属司",
        )
        chain_all(w, office_e, [office_t], f"确认{title}现有完整时间链。")
        rel(w, reform, office_t, "上下级机构", i, staff, f"元丰{title}隶工部。", "编制")

    for title in ("工部工作案", "工部营造案", "工部材料案", "工部兵匠案",
                  "工部检法案", "工部知杂案"):
        case_e = w.entity(title, "机构", f"工部编制列举{title}。", quotation=staff)
        case_t = tp(w, case_e, "北宋元丰新制", "工部所属常设办事案", i, staff,
                    "工部办事机构", f"建立{title}元丰节点。", "编制")
        rel(w, reform, case_t, "上下级机构", i, staff, f"{title}隶工部。", "编制")
    w.commit()


def refine_gongbu_case(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    tid = refine(w, ft(w, eid, "北宋元丰新制"), i, main,
                 f"专条细化{title}职掌。", None,
                 event=event, category="工部办事机构")
    chain_all(w, eid, [tid], f"确认{title}现有完整时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1231, 1251)] == [
        "都官司郎中", "都官司员外郎", "尚书", "都官司", "比部司",
        "比部司勾覆案", "比部司磨勘案", "比部司凭由案", "比部司理欠案",
        "比部司知杂案", "比部司郎中", "比部司员外郎", "司门司",
        "司门司郎中", "司门司员外郎", "尚书省工部", "工部工作案",
        "工部", "工部营造案", "工部材料案",
    ]
    assert all(F[i]["fields"].get("__status__") == "placeholder" for i in (1233, 1234, 1248))
    office_post(
        1231, "都官司郎中", "都官司",
        (("魏晋以下", "已有都官曹郎中之设"), ("唐武德三年", "始置都官司郎中")),
        "无职事，为中行郎中寄禄官阶，元丰后寄禄官易朝散大夫",
        "都官司长官，参掌刑徒、配隶与吏籍", "从五品上", "从六品",
        "简称", "都官司郎官",
    )
    office_post(
        1232, "都官司员外郎", "都官司",
        (("隋开皇六年", "始置都官司员外郎"),),
        "无职事，为中行员外郎阶，元丰后寄禄官易朝散郎",
        "都官司副长官，佐郎中掌本司事", "从六品上", "正七品",
        "简称与别名", "都官司郎官",
    )
    entry1235()
    refine_case(1236, "比部司勾覆案", "审核京师百司及诸路转运司钱谷百物出纳帐籍")
    refine_case(1237, "比部司磨勘案", "覆查审验勾覆案所核帐目")
    refine_case(1238, "比部司凭由案", "复验在京官物支付数额并签印、收回勾销凭由")
    refine_case(1239, "比部司理欠案", "追查百司侵吞经费并催索场务仓库欠物")
    refine_case(1240, "比部司知杂案", "办理比部司杂务与后勤")
    office_post(
        1241, "比部司郎中", "比部司",
        (("三国魏", "已有比部郎中"), ("唐武德三年", "始置尚书省刑部比部司郎中")),
        "为中行郎中寄禄官阶，元丰后寄禄官易朝散大夫",
        "比部司长官，掌审核内外帐籍、追索侵吞欠物与验签凭由",
        "从五品上", "从六品", "简称与别名", "比部司郎官",
    )
    office_post(
        1242, "比部司员外郎", "比部司",
        (("隋开皇三年", "始置比部司员外郎"),),
        "无职事，为中行员外郎阶，元丰后寄禄官易朝散郎",
        "比部司副长官，佐郎中参领本司事", "从六品上", "正七品",
        "简称与别名", "比部司郎官",
    )
    entry1243()
    office_post(
        1244, "司门司郎中", "司门司",
        (("北周", "司门下大夫为职任近似的前身"), ("隋", "先称司门侍郎，炀帝改司门郎"),
         ("唐武德三年", "始有司门司郎中之名")),
        "无职事，为中行郎中阶，元丰后寄禄官易朝散大夫",
        "司门司长官，领本司事", "从五品上", "从六品",
        "简称", "司门司郎官",
    )
    office_post(
        1245, "司门司员外郎", "司门司",
        (("隋开皇六年", "始置司门司员外郎"),),
        "无职事，为中行员外郎阶，元丰后寄禄官易朝散郎",
        "司门司副长官，佐郎中参掌本司事", "从六品上", "正七品",
        "简称", "司门司郎官",
    )
    entry1246()
    refine_gongbu_case(1247, "工部工作案", "掌舟、车、器械、钱货等百工制作")
    refine_gongbu_case(1249, "工部营造案", "掌城池、宫室、屋宇、街道与桥梁修造")
    refine_gongbu_case(1250, "工部材料案", "掌计划、采伐建筑与铸造所需材料")


if __name__ == "__main__":
    main()
