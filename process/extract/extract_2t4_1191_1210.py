#!/usr/bin/env python3
"""提取 chapter2t4 第1191–1210条：职方、驾部、库部郎官及刑部诸案。"""
import extract_2t4_1171_1190 as x


base = x.base
base.F = {i: base.load(i) for i in range(1190, 1211)}
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


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def entry1191():
    i = 1191
    main = Q(i, F[i]["text"])
    duty = field(i, "职掌")
    grade = field(i, "官品")
    w = W(i)
    eid = fe(w, "判职方司事", "官职")
    tid = refine(
        w, ft(w, eid, "宋前期"), i, duty,
        "专条细化判职方司事职掌。", "职掌",
        event="掌受诸路州府所贡地图及图经", category="判司差遣",
    )
    cite(w, "Timepoints", tid, i, grade, "补证品位随兼判朝官官阶。", "官品")
    cite(w, "Timepoints", tid, i, main, "正文补证为宋前期差遣官。")
    chain_all(w, eid, [tid], "确认判职方司事现有完整时间链。")
    rel(w, ft(w, fe(w, "职方司", "机构"), "宋前期"), tid,
        "编制隶属", i, main, "宋前期职方司置判司事一人。",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1192():
    i = 1192
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称")
    staff = Q(1190, F[1190]["fields"]["编制"], "编制")
    w = W(i)
    eid = fe(w, "职方司郎中", "官职")
    sui = tp(
        w, eid, "隋", "先称职方侍郎，炀帝改为职方郎",
        i, origin, "职方司郎官", "建立职方司郎中隋代职源节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐武德三年", "职方郎改称职方郎中，始有本名",
        i, origin, "职方司郎官", "建立职方司郎中唐代正名节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化职方司郎中宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为前行郎中寄禄官阶，元丰后寄禄官易朝请大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), 1190, staff,
        "职方司总条补证元丰置郎中一人。", "编制",
        event="职方司长官，掌领本司事", category="职方司郎官", grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [sui, tang, song, reform], "重建职方司郎中隋至元丰完整时间链。")
    office_e = fe(w, "职方司", "机构")
    rel(w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期职方司郎中为无职事阶官。", "职掌", staff_quota=1, staff_type="官")
    rel(w, ft(w, office_e, "北宋元丰新制"), reform, "编制隶属", 1190, staff,
        "元丰职方司置郎中一人。", "编制", staff_quota=1, staff_type="官")
    w.commit()


def entry1193():
    i = 1193
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "职方司员外郎", "官职")
    sui = tp(
        w, eid, "隋开皇六年", "始有职方司员外郎之名",
        i, origin, "职方司郎官", "建立职方司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事，为前行员外郎寄禄官阶，元丰后寄禄官易朝请郎",
        i, duty, "文臣迁转官阶", "建立职方司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化职方司员外郎元丰职事。", "职掌",
        event="职方司副长官，佐郎中掌领本司事", category="职方司郎官", grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, [sui, song, reform], "重建职方司员外郎隋至元丰完整时间链。")
    office_e = fe(w, "职方司", "机构")
    rel(w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        "宋前期职方司员外郎为无职事阶官。", "职掌", staff_quota=1, staff_type="官")
    rel(w, ft(w, office_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        "元丰职方司置员外郎一人。", "职掌", staff_quota=1, staff_type="官")
    w.commit()


def entry1194():
    i = 1194
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "驾部司", "机构")
    wei = tp(
        w, eid, "曹魏", "已有驾部郎之名，为驾部司职源",
        i, origin, "兵部所属司", "建立驾部司曹魏职源节点。", "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "始置尚书省兵部驾部司",
        i, origin, "兵部所属司", "建立驾部司隋代始置节点。", "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "沿置但无职事",
        i, duty, "兵部所属司", "建立驾部司宋前期无职事节点。", "职掌", chain="none",
    )
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化驾部司元丰职掌。", "职掌",
        event="参掌舆辇、车马、驿置与厩牧事务", category="兵部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎中、员外郎各一人。", "编制")
    jianyan = refine(
        w, ft(w, eid, "南宋建炎三年"), i, staff,
        "专条补证驾部司兼库部司及太仆寺归属。", "编制",
        event="驾部郎中兼库部郎中，二司合一，太仆寺并归驾部司", category="兵部所属司",
    )
    longxing = refine(
        w, ft_any(w, eid, "南宋隆兴初", "南宋隆兴元年"), i, staff,
        "专条给出四司合一确切年次。", "编制",
        time="南宋隆兴元年", event="四司合一，仅置郎官一员通管", category="兵部所属司",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与别名仅作称谓证据。", "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证驾部司为兵部四司之一。")
    chain_all(w, eid, [wei, sui, song, reform, jianyan, longxing],
              "重建驾部司曹魏职源至南宋隆兴完整时间链。")
    bingbu_e = fe(w, "兵部", "机构")
    rel(w, ft(w, bingbu_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期驾部司为兵部所属四司之一。")
    rel(w, ft(w, bingbu_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰驾部司隶兵部并参掌车马驿置。", "职掌")
    w.commit()


def simple_judge(i, title, office_title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}。", quotation=main)
    tid = tp(w, eid, "宋前期", event, i, main, "判司差遣", f"建立{title}宋前期节点。")
    rel(w, ft(w, fe(w, office_title, "机构"), "宋前期"), tid,
        "编制隶属", i, main, f"宋前期{office_title}置{title}一人。",
        staff_quota=1, staff_type="官")
    w.commit()


def langguan_entry(i, title, office_title, origin_nodes, song_event, reform_event,
                   song_grade, reform_grade, category, aliases_field="简称"):
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, aliases_field)
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}。", quotation=main)
    ordered = []
    for time, event in origin_nodes:
        ordered.append(tp(
            w, eid, time, event, i, origin, category,
            f"建立{title}{time}职源节点。", "职源", chain="none",
        ))
    existing_song = w.find_timepoint(eid, "宋代（尚书二十四司）") or w.find_timepoint(eid, "宋前期")
    if existing_song:
        song = refine(
            w, existing_song, i, duty, f"专条细化{title}宋前期阶官性质。", "职掌",
            time="宋前期", event=song_event, category="文臣迁转官阶", grade=song_grade,
        )
    else:
        song = tp(
            w, eid, "宋前期", song_event, i, duty, "文臣迁转官阶",
            f"建立{title}宋前期阶官节点。", "职掌", chain="none", attr_grade=song_grade,
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
            f"建立{title}元丰职事节点。", "职掌", chain="none", attr_grade=reform_grade,
        )
    cite(w, "Timepoints", reform, i, grade, f"补证元丰后{reform_grade}。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", aliases_field, note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具阶官名与职事官名。")
    chain_all(w, eid, ordered + [song, reform], f"重建{title}职源至元丰完整时间链。")
    office_e = fe(w, office_title, "机构")
    rel(w, ft(w, office_e, "宋前期"), song, "编制隶属", i, duty,
        f"宋前期{title}为无职事阶官。", "职掌", staff_quota=1, staff_type="官")
    rel(w, ft(w, office_e, "北宋元丰新制"), reform, "编制隶属", i, duty,
        f"元丰{office_title}置{title}一人。", "职掌", staff_quota=1, staff_type="官")
    w.commit()


def entry1198():
    i = 1198
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "库部司", "机构")
    wei = tp(w, eid, "曹魏", "已有库部郎之名，为库部司职源", i, origin,
             "兵部所属司", "建立库部司曹魏职源节点。", "职源", chain="none")
    sui = tp(w, eid, "隋", "始置尚书省兵部库部司", i, origin,
             "兵部所属司", "建立库部司隋代始置节点。", "职源", chain="none")
    song = tp(w, eid, "宋前期", "沿置但无职事", i, duty,
              "兵部所属司", "建立库部司宋前期无职事节点。", "职掌", chain="none")
    reform = refine(
        w, ft(w, eid, "北宋元丰新制"), i, duty,
        "专条细化库部司元丰职掌。", "职掌",
        event="掌军器、仪仗、卤簿、随军与防城什物及供帐", category="兵部所属司",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎中、员外郎及吏案编制。", "编制")
    jianyan = ft(w, eid, "南宋建炎三年")
    longxing = ft_any(w, eid, "南宋隆兴初", "南宋隆兴元年")
    shaoxi = tp(
        w, eid, "南宋绍熙三年", "兵、职、驾、库四司吏人合并为四十二人",
        i, staff, "兵部所属司", "建立库部司绍熙三年吏额合并节点。", "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与别名仅作称谓证据。", "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证库部司为兵部四司之一。")
    chain_all(w, eid, [wei, sui, song, reform, jianyan, longxing, shaoxi],
              "重建库部司曹魏职源至绍熙三年完整时间链。")
    bingbu_e = fe(w, "兵部", "机构")
    rel(w, ft(w, bingbu_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期库部司为兵部所属四司之一。")
    rel(w, ft(w, bingbu_e, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰库部司隶兵部并掌军器仪仗。", "职掌")
    w.commit()


def entry1202():
    i = 1202
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称与别名")
    w = W(i)
    archive_e = w.entity("礼、兵部架阁库", "机构", "职掌明确礼兵二部共用架阁档案库。", quotation=duty)
    archive_t = tp(
        w, archive_e, "南宋绍兴十五年", "礼部、兵部合置架阁库，储藏二部结案二年以上文书",
        i, origin, "六部档案机构", "建立礼、兵部架阁库绍兴合置节点。", "职源",
    )
    cite(w, "Timepoints", archive_t, i, duty, "补证档案编目、登记、保存与检索职掌。", "职掌")
    eid = w.entity("主管尚书省礼、兵部架阁文字", "官职", "本条直接定义礼兵二部合置架阁官。", quotation=main)
    tid = tp(
        w, eid, "南宋绍兴十五年", "始置一员，主管礼部、兵部架阁库档案",
        i, origin, "礼兵二部档案官", "建立主管礼兵部架阁文字绍兴始置节点。", "职源",
    )
    cite(w, "Timepoints", tid, i, duty, "补证二部档案移交、编目、登记与检索职掌。", "职掌")
    cite(w, "Timepoints", tid, i, grade, "补证由进士出身选人充任，品位随所带官阶。", "官品")
    cite(w, "Timepoints", tid, i, aliases, "简称仅作称谓证据。", "简称与别名", note="纯简称")
    cite(w, "Timepoints", tid, i, main, "正文补证为职事官。")
    rel(w, archive_t, tid, "编制隶属", i, origin, "绍兴十五年礼兵二部合置主管架阁官一员。",
        "职源", staff_quota=1, staff_type="官")
    rel(w, ft(w, fe(w, "主管尚书某部架阁文字", "官职"), "南宋绍兴十五年"), tid,
        "统称与实例", i, aliases, "主管尚书某部架阁文字包括礼兵二部合置实例。", "简称与别名")
    w.commit()


def entry1203():
    i = 1203
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "刑部", "机构")
    zhou = tp(w, eid, "北周", "始有刑部之名", i, origin, "尚书省六部",
              "建立刑部北周名源节点。", "职源", chain="none")
    sui = tp(w, eid, "隋开皇三年", "改都官尚书为刑部尚书，刑部成为尚书省六部之一",
             i, origin, "尚书省六部", "建立刑部隋代入尚书省节点。", "职源", chain="none")
    song = refine(
        w, ft_any(w, eid, "宋代", "宋前期"), i, duty,
        "专条细化刑部宋前期复核职权。", "职掌",
        time="宋前期", event="职事为审刑院所分，主要覆审大辟及办理犯罪官员叙复理雪文牒",
        category="中央司法机构",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判部、详覆官、法直官与吏额。", "编制")
    reform = tp(
        w, eid, "北宋元丰新制", "罢审刑院归刑部，掌律法、天下狱讼、疑案复议及赦宥叙复",
        i, duty, "尚书省六部", "建立刑部元丰恢复专职节点。", "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰长贰、四司、分案与吏额。", "编制")
    jianyan = tp(w, eid, "南宋建炎三年", "长贰仅置一人、郎官二人，吏额减半", i, staff,
                 "尚书省六部", "建立刑部建炎减员节点。", "编制", chain="none")
    longxing = tp(w, eid, "南宋隆兴元年", "吏额四十五人", i, staff,
                  "尚书省六部", "建立刑部隆兴吏额节点。", "编制", chain="none")
    qiandao = tp(w, eid, "南宋乾道六年", "吏额减为三十五人", i, staff,
                 "尚书省六部", "建立刑部乾道减吏节点。", "编制", chain="none")
    chunxi = tp(w, eid, "南宋淳熙十三年", "吏额减为三十一人", i, staff,
                "尚书省六部", "建立刑部淳熙减吏节点。", "编制", chain="none")
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。", "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证刑部为尚书省六部之一。")
    chain_all(w, eid, [zhou, sui, song, reform, jianyan, longxing, qiandao, chunxi],
              "重建刑部北周名源至南宋淳熙完整时间链。")
    shangshu_e = fe(w, "尚书省", "机构")
    rel(w, ft(w, shangshu_e, "宋前期"), song, "上下级机构", i, main,
        "宋前期刑部为尚书省六部之一。")
    rel(w, ft(w, shangshu_e, "北宋元丰新制"), reform, "上下级机构", i, staff,
        "元丰刑部为尚书省六部之一。", "编制")
    posts = (("刑部尚书", 1, "刑部长官"), ("刑部侍郎", 2, "刑部副长官"))
    for title, quota, event in posts:
        post_e = fe(w, title, "官职")
        post_t = tp(w, post_e, "北宋元丰新制", event, i, staff,
                    "刑部长贰", f"据刑部编制建立{title}元丰职事节点。", "编制", chain="none")
        existing = [r[0] for r in w.conn.execute(
            "select id from Timepoints where entity_id=? and id<>? order by id", (post_e, post_t)
        )]
        chain_all(w, post_e, existing + [post_t], f"连接{title}既有节点与元丰职事节点。")
        rel(w, reform, post_t, "编制隶属", i, staff, f"元丰刑部置{title}{quota}人。", "编制",
            staff_quota=quota, staff_type="官")
    for title in ("刑部司", "都官司", "比部司", "司门司"):
        office_e = fe(w, title, "机构")
        office_t = refine(
            w, ft_any(w, office_e, "宋代（尚书二十四司）", "北宋元丰新制"), i, staff,
            f"刑部总条明确{title}为元丰所属四司之一。", "编制",
            time="北宋元丰新制", event="刑部所属四司之一", category="刑部所属司",
        )
        chain_all(w, office_e, [office_t], f"确认{title}现有完整时间链。")
        rel(w, reform, office_t, "上下级机构", i, staff, f"元丰{title}隶刑部。", "编制")
    w.commit()


EIGHT_CASES = (
    "刑部制勘案", "刑部体量案", "刑部详覆案", "刑部注籍点检案",
    "刑部随时拨却行案", "刑部随时拨却不行案", "刑部举叙案", "刑部进拟案",
)

THIRTEEN_CASES = (
    "刑部制勘案", "刑部体量案", "刑部定夺案", "刑部举叙案", "刑部纠察案",
    "刑部检法案", "刑部颁降案", "刑部追毁案", "刑部会问案", "刑部详覆案",
    "刑部捕盗案", "刑部帐籍案", "刑部进拟案",
)


def collective_cases(i, collective_title, time, titles, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    collective_e = w.entity(collective_title, "机构", f"第{i}条直接定义{collective_title}。", quotation=main)
    collective_t = tp(w, collective_e, time, event, i, main, "机构统称",
                      f"建立{collective_title}{time}节点。")
    parent_t = ft(w, fe(w, "刑部", "机构"), "北宋元丰新制" if i == 1204 else "南宋建炎三年")
    for title in titles:
        case_e = w.entity(title, "机构", f"{collective_title}原文列举{title}。", quotation=main)
        case_time = (
            "南宋绍兴后"
            if i == 1205 and title in ("刑部体量案", "刑部详覆案")
            else time
        )
        case_t = tp(w, case_e, case_time, f"{collective_title}所属常设办事案", i, main,
                    "刑部办事机构", f"据{collective_title}列举建立{title}{time}节点。")
        rel(w, collective_t, case_t, "统称与实例", i, main, f"{collective_title}包括{title}。")
        rel(w, parent_t, case_t, "上下级机构", i, main, f"{title}为刑部常设办事机构。")
    w.commit()


def refine_case(i, title, north_event, south_event=None, south_time="南宋初"):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    north = refine(w, ft(w, eid, "北宋元丰新制"), i, main,
                   f"专条细化{title}元丰职掌。", None,
                   event=north_event, category="刑部办事机构")
    ordered = [north]
    south = w.find_timepoint(eid, "南宋初") or w.find_timepoint(eid, south_time)
    if south is not None:
        south = refine(w, south, i, main, f"专条细化{title}南宋职掌。", None,
                       time=south_time, event=south_event or north_event, category="刑部办事机构")
        ordered.append(south)
    chain_all(w, eid, ordered, f"确认{title}现有完整时间链。")
    w.commit()


def entry1208():
    i = 1208
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("刑部制勘体量案", "机构", "本条直接定义制勘、体量合案。", quotation=main)
    merged = tp(w, eid, "北宋元祐四年", "制勘案与体量案合并，避免文书往还", i, main,
                "刑部办事机构", "建立制勘体量案元祐合并节点。")
    for title in ("刑部制勘案", "刑部体量案"):
        source_e = fe(w, title, "机构")
        rel(w, ft(w, source_e, "北宋元丰新制"), merged, "前后演变", i, main,
            f"元祐四年{title}并入制勘体量案。")
        south = ft_any(w, source_e, "南宋初", "南宋绍兴后")
        rel(w, merged, south, "前后演变", i, main, f"南宋制勘体量复分为{title}。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1191, 1211)] == [
        "判职方司事", "职方司郎中", "职方司员外郎", "驾部司", "判驾部司事",
        "驾部司郎中", "驾部司员外郎", "库部司", "判库部司事", "库部司郎中",
        "库部司员外郎", "主管尚书省礼、兵部架阁文字", "尚书省刑部", "刑部八案",
        "刑部十三案", "刑部制勘案", "刑部体量案", "刑部制勘体量案",
        "刑部详覆案", "刑部注籍点检案",
    ]
    entry1191()
    entry1192()
    entry1193()
    entry1194()
    simple_judge(1195, "判驾部司事", "驾部司", "无职事，以朝官兼充，看守本司")
    langguan_entry(
        1196, "驾部司郎中", "驾部司",
        (("北魏", "尚书三十六曹已有驾部郎中"), ("北齐", "殿中尚书统驾部曹郎中"),
         ("隋", "兵部驾部司先称侍郎、郎"), ("唐武德三年", "始有驾部司郎中之名")),
        "无职事，为前行郎中寄禄官阶，元丰后寄禄官易朝请大夫",
        "驾部司长官，掌车马驿递与内外牧监", "从五品上", "从六品", "驾部司郎官",
        "简称与别名",
    )
    langguan_entry(
        1197, "驾部司员外郎", "驾部司", (("隋开皇六年", "始有驾部司员外郎之名"),),
        "无职事，为前行员外郎寄禄官阶，元丰后寄禄官易朝请郎",
        "驾部司副长官，佐郎中参领本司事", "从六品上", "正七品", "驾部司郎官",
    )
    entry1198()
    simple_judge(1199, "判库部司事", "库部司", "无职事，以朝官兼充，看守本司")
    langguan_entry(
        1200, "库部司郎中", "库部司",
        (("南朝宋、北齐", "已有尚书库部郎中之称"), ("唐武德三年", "始有兵部库部司郎中之名")),
        "无职事，为前行郎中寄禄官阶，元丰后寄禄官易朝请大夫",
        "库部司长官，掌领本司事", "从五品上", "从六品", "库部司郎官",
    )
    langguan_entry(
        1201, "库部司员外郎", "库部司", (("隋开皇六年", "始有库部司员外郎之名，唐宋沿用"),),
        "为前行员外郎寄禄官阶，元丰后寄禄官易朝请郎",
        "库部司副长官，佐郎中掌本司事", "从六品上", "正七品", "库部司郎官",
    )
    entry1202()
    entry1203()
    collective_cases(1204, "刑部八案", "北宋元丰新制", EIGHT_CASES,
                     "刑部制勘、体量、详覆等八个办事案的合称")
    collective_cases(1205, "刑部十三案", "南宋初", THIRTEEN_CASES,
                     "南宋刑狱增繁后十三个办事案的合称")
    refine_case(1206, "刑部制勘案", "审理案犯", "审理诸路上奏刑狱公事")
    refine_case(1207, "刑部体量案", "审问调查并追究犯罪事实", "职掌与元丰同",
                south_time="南宋绍兴后")
    entry1208()
    refine_case(1209, "刑部详覆案", "覆审诸路所上大辟案", "职掌与北宋同",
                south_time="南宋绍兴后")
    refine_case(1210, "刑部注籍点检案", "备案检察本部及诸路大辟案并纠正量刑失误")


if __name__ == "__main__":
    main()
