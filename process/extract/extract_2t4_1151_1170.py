#!/usr/bin/env python3
"""提取 chapter2t4 第1151–1170条：度牒、主客、膳部、贡院与兵部前期。"""
import extract_2t4_1131_1150 as x


base = x.base
base.F = {i: base.load(i) for i in range(1150, 1171)}
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


def entry1151():
    i = 1151
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "监度牒库", "官职")
    tid = refine(
        w, ft(w, eid, "宋代"), i, main,
        "专条细化监度牒库职掌。", None,
        event="主管度牒库及库内工匠、专知官、库子、巡逻兵士，有正阙与添差",
        category="监当官",
    )
    chain_all(w, eid, [tid], "确认监度牒库现有完整时间链。")
    rel(w, ft(w, fe(w, "度牒库", "机构"), "宋代"), tid,
        "编制隶属", i, main, "监度牒库为度牒库主管官。",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1152():
    i = 1152
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提领度牒所", "机构", "本条直接定义南宋提领新法度牒所。", quotation=main)
    start = tp(
        w, eid, "南宋建炎三年八月", "始置，改革度牒旧法",
        i, main, "度牒专门机构", "建立提领度牒所精确始置节点。",
        chain="none",
    )
    end = tp(
        w, eid, "南宋建炎四年八月", "罢废，前后存在一年",
        i, main, "度牒专门机构", "建立提领度牒所精确罢废节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接提领度牒所始置与罢废节点。")
    w.commit()


def entry1153():
    i = 1153
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提举京城所", "机构", "本条直接定义徽宗朝提举京城所。", quotation=main)
    tp(
        w, eid, "北宋徽宗朝", "出卖公私空名牒、紫衣及师号",
        i, main, "度牒专门机构", "原文仅载徽宗朝，建立朝代节点。",
    )
    w.commit()


def entry1154():
    i = 1154
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "主客司", "机构")
    han = tp(
        w, eid, "西汉成帝时", "尚书客曹为主客司远源",
        i, origin, "礼部所属司", "建立主客司西汉远源节点。",
        "职源", chain="none",
    )
    eastern_han = tp(
        w, eid, "东汉初", "南、北主客曹掌外国夷狄事务，为后世主客司先声",
        i, origin, "礼部所属司", "建立主客司东汉远源节点。",
        "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "始置为尚书省礼部所属主客司",
        i, origin, "礼部所属司", "建立主客司隋代机构节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化主客司宋前期无职事状态。", "职掌",
        time="宋前期", event="无职事，外国朝贡事务归客省",
        category="礼部所属司",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判司一人与胥吏二人。", "编制")
    reform = tp(
        w, eid, "北宋元丰新制", "掌外国朝贡、国信使礼物及后周陵寝祭享、柴氏承袭",
        i, duty, "礼部所属司", "建立主客司元丰恢复职事节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎官、吏人与分案四。", "编制")
    zhezong = tp(
        w, eid, "北宋哲宗元祐、绍圣间", "主客司与膳部司郎官互兼，仅置一员",
        i, staff, "礼部所属司", "建立主客司哲宗朝互兼节点。",
        "编制", chain="none",
    )
    jianyan = tp(
        w, eid, "南宋建炎三年", "由礼部郎官一员兼任主客司郎官",
        i, staff, "礼部所属司", "建立主客司建炎兼领节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证主客司为官司。")
    chain_all(w, eid, [han, eastern_han, sui, song, reform, zhezong, jianyan],
              "重建主客司西汉远源至南宋建炎完整时间链。")
    libu = fe(w, "礼部", "机构")
    rel(w, ft(w, libu, "宋前期"), song, "上下级机构", i, origin,
        "主客司为尚书省礼部所属子司。", "职源")
    rel(w, ft(w, libu, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰主客司隶礼部并恢复职事。", "职掌")
    w.commit()


def entry1155():
    i = 1155
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "主客司郎中", "官职")
    eastern_jin = tp(
        w, eid, "东晋", "主客郎之名为远源",
        i, origin, "主客郎官", "建立主客司郎中东晋名源节点。",
        "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐武德间", "始有主客司郎中之名",
        i, origin, "主客司郎官", "建立主客司郎中唐代正名节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化主客司郎中宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为后行郎中迁转阶，元丰后寄禄官易朝奉大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，实领主客司事",
        i, duty, "主客司长官", "建立主客司郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官性质。")
    chain_all(w, eid, [eastern_jin, tang, song, reform],
              "连接主客司郎中东晋名源、唐代、宋前期与元丰节点。")
    rel(w, ft(w, fe(w, "主客司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰主客司郎中实领本司事。", "职掌",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1156():
    i = 1156
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    staff = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity("主客司员外郎", "官职", "本条直接定义主客司员外郎。", quotation=main)
    sui = tp(
        w, eid, "隋开皇六年", "主客司员外郎之名始置",
        i, origin, "主客司郎官", "建立主客司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事，为后行员外郎迁转阶，元丰后寄禄官易朝奉郎",
        i, duty, "文臣迁转官阶", "建立主客司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为主客司副长官，佐郎中领本司事",
        i, duty, "主客司副长官", "建立主客司员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证元丰编制一人。", "编制")
    jianyan = tp(
        w, eid, "南宋建炎三年四月十五日", "不再专置，由礼部郎官一员兼主客",
        i, staff, "主客司郎官", "建立主客司员外郎建炎兼领节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", jianyan, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    chain_all(w, eid, [sui, song, reform, jianyan],
              "连接主客司员外郎隋代、宋前期、元丰与建炎节点。")
    rel(w, ft(w, fe(w, "主客司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, staff, "元丰主客司置员外郎一人。", "编制",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1158():
    i = 1158
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("知杂封袭朝贡案", "机构", "本条直接定义南宋主客司合并案。", quotation=main)
    tid = tp(
        w, eid, "南宋", "疑由知杂、封爵、承袭、朝贡四案合并，掌朝贡、柴氏承袭、颁历与本司文书",
        i, main, "主客司办事机构", "原文明确作‘疑即’，保留推测语气建立南宋节点。",
    )
    rel(w, ft(w, fe(w, "主客司", "机构"), "南宋建炎三年"), tid,
        "上下级机构", i, main, "南宋知杂封袭朝贡案为主客司合并后的常设办事部门。")
    parent_north = ft(w, fe(w, "主客司", "机构"), "北宋元丰新制")
    for title in ("主客司知杂案", "主客司封爵案", "主客司承袭案", "主客司朝贡案"):
        old_e = w.entity(
            title, "机构", f"辞典原文作‘疑即由知杂、封爵、承袭、朝贡四案合而为一’，"
            f"据此以推测身份建立{title}。", quotation=main,
        )
        old_north = tp(
            w, old_e, "北宋元丰新制", "疑为主客司四案之一",
            i, main, "主客司办事机构", f"保留原文‘疑即’语气建立{title}元丰推测节点。",
            chain="none",
        )
        old_merged = tp(
            w, old_e, "南宋", "疑并入知杂封袭朝贡案",
            i, main, "主客司办事机构", f"保留原文‘疑即’语气建立{title}南宋并案节点。",
            chain="none",
        )
        chain_all(w, old_e, [old_north, old_merged], f"连接{title}元丰推测与南宋并案节点。")
        rel(w, parent_north, old_north, "上下级机构", i, main,
            f"据辞典‘疑即’说明，{title}疑为元丰主客司四案之一。")
        rel(w, old_merged, tid, "前后演变", i, main,
            f"据辞典‘疑即’说明，{title}疑并入知杂封袭朝贡案。")
    w.commit()


def entry1159():
    i = 1159
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "膳部司", "机构")
    beiji = tp(
        w, eid, "北齐", "膳部之名始见",
        i, origin, "礼部所属司", "建立膳部司北齐名源节点。",
        "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "始有尚书省礼部膳部司之名",
        i, origin, "礼部所属司", "建立膳部司隋代机构节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化膳部司宋前期无职事状态。", "职掌",
        time="宋前期", event="无职事，为空架子",
        category="礼部所属司",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判司一人与令史二人。", "编制")
    reform = tp(
        w, eid, "北宋元丰新制", "恢复职事，掌供进酒膳、祠祭牲牢礼料及藏冰",
        i, duty, "礼部所属司", "建立膳部司元丰恢复职事节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰郎官、吏人与分案七。", "编制")
    zhezong = tp(
        w, eid, "北宋哲宗朝以后", "与主客司郎官通置一员",
        i, staff, "礼部所属司", "建立膳部司哲宗以后互兼节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证膳部司为官司。")
    ordered = [beiji, sui, song, reform, zhezong]
    south = w.find_timepoint(eid, "南宋")
    if south is not None:
        ordered.append(south)
    chain_all(w, eid, ordered, "重建膳部司北齐名源至南宋完整时间链。")
    libu = fe(w, "礼部", "机构")
    rel(w, ft(w, libu, "宋前期"), song, "上下级机构", i, origin,
        "膳部司为尚书省礼部所属子司。", "职源")
    rel(w, ft(w, libu, "北宋元丰新制"), reform, "上下级机构", i, duty,
        "元丰膳部司隶礼部并恢复职事。", "职掌")
    w.commit()


def entry1160():
    i = 1160
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    staff = field(i, "编制")
    aliases = field(i, "简称")
    w = W(i)
    eid = fe(w, "膳部司郎中", "官职")
    tang = tp(
        w, eid, "唐初", "膳部司郎中之名始置",
        i, origin, "膳部司郎官", "建立膳部司郎中唐代职源节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代（尚书二十四司）", "宋前期"), i, duty,
        "专条细化膳部司郎中宋前期阶官性质。", "职掌",
        time="宋前期", event="无职事，为后行郎中迁转阶，元丰后寄禄官易朝奉大夫",
        category="文臣迁转官阶", grade="从五品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从五品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为职事官，实领膳部司公事",
        i, duty, "膳部司长官", "建立膳部司郎中元丰职事节点。",
        "职掌", chain="none", attr_grade="从六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后从六品。", "官品")
    cite(w, "Timepoints", reform, i, staff, "补证元丰编制一人。", "编制")
    cite(w, "Timepoints", reform, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    chain_all(w, eid, [tang, song, reform], "连接膳部司郎中唐代、宋前期与元丰节点。")
    rel(w, ft(w, fe(w, "膳部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, staff, "元丰膳部司置郎中一人。", "编制",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1161():
    i = 1161
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    grade = field(i, "官品")
    aliases = field(i, "别名")
    w = W(i)
    eid = w.entity("膳部司员外郎", "官职", "本条直接定义膳部司员外郎。", quotation=main)
    sui = tp(
        w, eid, "隋开皇六年", "膳部司员外郎始置",
        i, origin, "膳部司郎官", "建立膳部司员外郎隋代职源节点。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "无职事，为后行员外郎迁转阶，元丰后寄禄官易朝奉郎",
        i, duty, "文臣迁转官阶", "建立膳部司员外郎宋前期阶官节点。",
        "职掌", chain="none", attr_grade="从六品上",
    )
    cite(w, "Timepoints", song, i, grade, "补证宋前期从六品上。", "官品")
    reform = tp(
        w, eid, "北宋元丰新制", "改为膳部司副长官，佐郎中参掌本司事",
        i, duty, "膳部司副长官", "建立膳部司员外郎元丰职事节点。",
        "职掌", chain="none", attr_grade="正七品",
    )
    cite(w, "Timepoints", reform, i, grade, "补证元丰后正七品。", "官品")
    cite(w, "Timepoints", reform, i, aliases, "礼部四司郎官通用别名仅作称谓证据。",
         "别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兼具官阶名与职事官名。")
    chain_all(w, eid, [sui, song, reform], "连接膳部司员外郎隋代、宋前期与元丰节点。")
    rel(w, ft(w, fe(w, "膳部司", "机构"), "北宋元丰新制"), reform,
        "编制隶属", i, duty, "元丰膳部司员外郎佐郎中掌本司事。", "职掌",
        staff_quota=1, staff_type="官")
    w.commit()


def merge_shanbu_cases(i, combined_title, old_titles, combined_event):
    main = Q(i, F[i]["text"])
    w = W(i)
    parent_e = fe(w, "膳部司", "机构")
    parent_south = w.find_timepoint(parent_e, "南宋")
    if parent_south is None:
        parent_south = tp(
            w, parent_e, "南宋", "元丰七案省并为二案",
            i, main, "礼部所属司", "据办事案专条建立膳部司南宋省案节点。",
            chain="none",
        )
    else:
        cite(w, "Timepoints", parent_south, i, main, "补证南宋膳部司七案省并为二。")
    parent_order = [
        ft(w, parent_e, "北齐"), ft(w, parent_e, "隋"), ft(w, parent_e, "宋前期"),
        ft(w, parent_e, "北宋元丰新制"), ft(w, parent_e, "北宋哲宗朝以后"), parent_south,
    ]
    chain_all(w, parent_e, parent_order, "补全膳部司至南宋省案节点的完整时间链。")
    combined_e = w.entity(combined_title, "机构", f"第{i}条直接定义南宋{combined_title}。", quotation=main)
    combined_t = tp(
        w, combined_e, "南宋", combined_event,
        i, main, "膳部司办事机构", f"建立{combined_title}南宋合并节点。",
    )
    rel(w, parent_south, combined_t, "上下级机构", i, main,
        f"南宋{combined_title}为膳部司省并后的二案之一。")
    for old_title in old_titles:
        old_e = w.entity(old_title, "机构", f"据第{i}条合并说明恢复元丰{old_title}。", quotation=main)
        old_north = tp(
            w, old_e, "北宋元丰新制", "膳部司七案之一",
            i, main, "膳部司办事机构", f"建立{old_title}元丰节点。",
            chain="none",
        )
        old_merged = tp(
            w, old_e, "南宋", f"并入{combined_title}",
            i, main, "膳部司办事机构", f"建立{old_title}南宋并省节点。",
            chain="none",
        )
        chain_all(w, old_e, [old_north, old_merged], f"连接{old_title}元丰与南宋并省节点。")
        rel(w, ft(w, parent_e, "北宋元丰新制"), old_north, "上下级机构", i, main,
            f"元丰{old_title}为膳部司七案之一。")
        rel(w, old_merged, combined_t, "前后演变", i, main,
            f"南宋{old_title}并入{combined_title}。")
    w.commit()


def entry1164():
    i = 1164
    main = Q(i, F[i]["text"])
    origin = field(i, "职源与沿革")
    duty = field(i, "职能")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = w.entity("礼部贡院", "机构", "本条直接定义礼部贡院。", quotation=main)
    tang = tp(
        w, eid, "唐代", "进士科考试贡院设于礼部南院",
        i, origin, "贡举考试机构", "建立礼部贡院唐代职源节点。",
        "职源与沿革", chain="none",
    )
    song = tp(
        w, eid, "五代、宋", "沿置为贡举试场，收卷、封弥、誊录、考校并排定省试等第",
        i, duty, "贡举考试机构", "建立礼部贡院五代宋沿置节点。",
        "职能", chain="none",
    )
    cite(w, "Timepoints", song, i, origin, "补证五代、宋沿置。", "职源与沿革")
    huizong = tp(
        w, eid, "北宋徽宗崇宁至政和后", "州郡亦普遍设置贡院",
        i, origin, "贡举考试机构", "建立徽宗朝贡院推广节点。",
        "职源与沿革", chain="none",
    )
    cite(w, "Timepoints", song, i, staff, "补证主判、知举、考校官与附属机构编制。", "编制")
    cite(w, "Timepoints", song, i, aliases, "简称与典故称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    chain_all(w, eid, [tang, song, huizong], "连接礼部贡院唐代、五代宋与徽宗节点。")
    rel(w, ft(w, fe(w, "礼部", "机构"), "宋前期"), song,
        "上下级机构", i, main, "礼部贡院隶尚书省礼部。")

    offices = (
        "礼部贡院试院", "礼部贡院封弥院", "礼部贡院誊录院", "礼部贡院编排所",
        "礼部贡院对读所", "礼部贡院别试所", "礼部贡院过落司",
    )
    for title in offices:
        sub_e = w.entity(title, "机构", f"礼部贡院编制明确列有{title.removeprefix('礼部贡院')}。", quotation=staff)
        sub_t = tp(
            w, sub_e, "宋代贡举考试期间", "礼部贡院附属考试机构",
            i, staff, "贡院附属机构", f"建立{title}宋代节点。", "编制",
        )
        rel(w, song, sub_t, "上下级机构", i, staff, f"{title}隶礼部贡院。", "编制")

    posts = (
        "判贡院事", "知礼部贡举事", "考官", "覆考官", "封弥官", "誊录官",
        "点检试卷官", "巡捕官", "编排官", "详定官", "对读官", "历程官", "监门官",
    )
    for title in posts:
        post_e = w.entity(title, "官职", f"礼部贡院编制明确列有{title}。", quotation=staff)
        event = "平时主判礼部贡院" if title == "判贡院事" else "贡举考试期间任职"
        post_t = tp(
            w, post_e, "宋代", event,
            i, staff, "贡院考试官", f"据礼部贡院编制建立{title}宋代节点。", "编制",
        )
        rel(w, song, post_t, "编制隶属", i, staff, f"礼部贡院置{title}。", "编制", staff_type="官")
    w.commit()


def entry1165():
    i = 1165
    main = Q(i, F[i]["text"])
    aliases = field(i, "简称与别名")
    w = W(i)
    office_t = ft(w, fe(w, "礼部贡院", "机构"), "五代、宋")
    eid = fe(w, "知礼部贡举事", "官职")
    tid = refine(
        w, ft(w, eid, "宋代"), i, main,
        "专条细化知礼部贡举事的临时差遣与锁院制度。", None,
        event="贡举考试时临时领举，受诏后锁院，试毕即罢并复设判院官",
        category="贡院考试官",
    )
    cite(w, "Timepoints", tid, i, aliases, "简称与别名仅作称谓证据。",
         "简称与别名", note="纯简称")
    rel(w, office_t, tid, "编制隶属", i, main, "贡举考试时礼部贡院临时置知举官。", staff_type="官")

    same_e = w.entity("同知礼部贡举事", "官职", "正文明确知举官下可设同知。", quotation=main)
    same_t = tp(
        w, same_e, "北宋太宗淳化三年正月六日", "苏易简等同知贡举，受诏后径赴贡院锁院；其后成为常制",
        i, main, "贡院考试官", "建立同知贡举精确锁院节点。",
    )
    rel(w, office_t, same_t, "编制隶属", i, main, "知举官之下可设同知贡举。", staff_type="官")
    acting_e = w.entity("权知礼部贡举事", "官职", "正文明确资稍浅者称权知贡举。", quotation=main)
    acting_t = tp(
        w, acting_e, "宋代", "资序稍浅者权知贡举",
        i, main, "贡院考试官", "建立权知礼部贡举事宋代节点。",
    )
    rel(w, office_t, acting_t, "编制隶属", i, main, "礼部贡院考试时可置权知贡举。", staff_type="官")
    w.commit()


def entry1166():
    i = 1166
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid = fe(w, "兵部", "机构")
    zhou = tp(
        w, eid, "北周", "已有兵部之名，为夏官府大司马属官",
        i, origin, "尚书省六部", "建立兵部北周名源节点。",
        "职源", chain="none",
    )
    sui = tp(
        w, eid, "隋", "始有尚书省兵部之称",
        i, origin, "尚书省六部", "建立兵部隋代入尚书省节点。",
        "职源", chain="none",
    )
    song = refine(
        w, ft_any(w, eid, "宋代", "宋前期"), i, duty,
        "专条细化兵部宋前期职权旁落。", "职掌",
        time="宋前期", event="职事多归枢密院、三班院，仅掌仪卫与武人科举等",
        category="中央行政机构",
    )
    cite(w, "Timepoints", song, i, staff, "补证宋前期判部与吏额。", "编制")
    xining = tp(
        w, eid, "北宋熙宁八年", "因掌诸路保甲教阅，增同判、主簿与勾当公事官",
        i, staff, "中央行政机构", "建立兵部熙宁八年增员节点。",
        "编制", chain="none",
    )
    reform = tp(
        w, eid, "北宋元丰新制", "仍受枢密院与吏部制约，掌民兵、厢军名籍、蕃官加恩及所属司局",
        i, duty, "尚书省六部", "建立兵部元丰职事节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", reform, i, staff, "补证元丰十官、四司、九案与吏额。", "编制")
    yuanyou = tp(
        w, eid, "北宋元祐初", "省驾部郎中，并由职方郎中兼库部郎中，减官额二员",
        i, staff, "尚书省六部", "建立兵部元祐减员节点。",
        "编制", chain="none",
    )
    jianyan = tp(
        w, eid, "南宋建炎三年", "四司并为二，兵部司兼职方司、驾部司兼库部司",
        i, staff, "尚书省六部", "建立兵部建炎四司并二节点。",
        "编制", chain="none",
    )
    longxing = tp(
        w, eid, "南宋隆兴初", "四司合一，仅置一郎官兼领，长贰亦裁并",
        i, staff, "尚书省六部", "建立兵部隆兴四司合一节点。",
        "编制", chain="none",
    )
    cite(w, "Timepoints", reform, i, aliases, "简称与拟古称谓仅作称谓证据。",
         "简称与别名", note="纯简称")
    cite(w, "Timepoints", reform, i, main, "正文补证兵部为尚书省六部之一。")
    chain_all(w, eid, [zhou, sui, song, xining, reform, yuanyou, jianyan, longxing],
              "重建兵部北周名源至南宋隆兴完整时间链。")
    shangshu = fe(w, "尚书省", "机构")
    rel(w, ft(w, shangshu, "宋前期"), song, "上下级机构", i, main,
        "宋前期兵部为尚书省六部之一。")
    rel(w, ft(w, shangshu, "北宋元丰新制"), reform, "上下级机构", i, staff,
        "元丰兵部为尚书省六部之一。", "编制")

    offices = ("兵部司", "职方司", "驾部司", "库部司")
    for title in offices:
        office_e = fe(w, title, "机构")
        north = refine(
            w, ft_any(w, office_e, "宋代（尚书二十四司）", "北宋元丰新制"), i, staff,
            f"兵部总条明确{title}为元丰所属四司之一。", "编制",
            time="北宋元丰新制", event="兵部所属四司之一", category="兵部所属司",
        )
        south_event = (
            "由兵部司郎官兼领" if title == "职方司" else
            "兼领职方司" if title == "兵部司" else
            "由驾部司郎官兼领" if title == "库部司" else "兼领库部司"
        )
        south = tp(
            w, office_e, "南宋建炎三年", south_event,
            i, staff, "兵部所属司", f"建立{title}建炎兼领节点。", "编制", chain="none",
        )
        merged = tp(
            w, office_e, "南宋隆兴初", "四司合置一员郎官兼领",
            i, staff, "兵部所属司", f"建立{title}隆兴四司合领节点。", "编制", chain="none",
        )
        chain_all(w, office_e, [north, south, merged], f"连接{title}元丰、建炎与隆兴节点。")
        rel(w, reform, north, "上下级机构", i, staff, f"元丰{title}隶兵部。", "编制")
        rel(w, jianyan, south, "上下级机构", i, staff, f"建炎{title}仍属兵部并实行兼领。", "编制")
        rel(w, longxing, merged, "上下级机构", i, staff, f"隆兴{title}属兵部四司合领范围。", "编制")

    posts = (
        ("同判尚书省兵部事", "同判兵部，协助掌诸路保甲教阅", 1),
        ("兵部主簿", "掌诸路保甲教阅簿书", 2),
        ("兵部勾当公事", "赴诸路州军提举保甲教阅训练", 10),
    )
    for title, event, quota in posts:
        post_e = w.entity(title, "官职", f"兵部熙宁八年编制明确增置{title}。", quotation=staff)
        post_t = (
            w.find_timepoint(post_e, "北宋熙宁八年九月")
            if title == "同判尚书省兵部事"
            else None
        )
        if post_t is None:
            post_t = tp(
                w, post_e, "北宋熙宁八年", event,
                i, staff, "兵部变法差遣", f"据兵部编制建立{title}熙宁始置节点。", "编制",
            )
        else:
            cite(w, "Timepoints", post_t, i, staff,
                 "兵部总条补证熙宁八年增同判兵部事一人。", "编制")
        rel(w, xining, post_t, "编制隶属", i, staff, f"熙宁八年兵部置{title}。", "编制",
            staff_quota=quota, staff_type="官")
    w.commit()


def entry1167():
    i = 1167
    main = Q(i, F[i]["text"])
    origin = field(i, "职源")
    duty = field(i, "职掌")
    rank = field(i, "官品")
    aliases = field(i, "简称")
    w = W(i)
    eid = w.entity("判尚书省兵部事", "官职", "本条直接定义宋前期判兵部事。", quotation=main)
    sui = tp(
        w, eid, "隋开皇三年", "有尚书左仆射判兵部尚书事之同名领衔，性质异于宋代差遣",
        i, origin, "判部差遣", "建立判兵部事隋代同名职源节点并保留性质区别。",
        "职源", chain="none",
    )
    song = tp(
        w, eid, "宋前期", "掌仪仗、车驾、卤簿、字图、武举与武成王庙释奠",
        i, duty, "判部差遣", "建立判兵部事宋前期节点。",
        "职掌", chain="none",
    )
    cite(w, "Timepoints", song, i, rank, "补证由两制以上朝官充。", "官品")
    cite(w, "Timepoints", song, i, aliases, "简称仅作称谓证据。", "简称", note="纯简称")
    cite(w, "Timepoints", song, i, main, "正文补证为宋前期差遣官。")
    chain_all(w, eid, [sui, song], "连接判兵部事隋代同名职源与宋前期节点。")
    rel(w, ft(w, fe(w, "兵部", "机构"), "宋前期"), song,
        "编制隶属", i, main, "宋前期兵部置判部事一人。",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1168():
    i = 1168
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "同判尚书省兵部事", "官职")
    tid = refine(
        w, ft_any(w, eid, "北宋熙宁八年", "北宋熙宁八年九月"), i, main,
        "专条补足同判兵部精确始置月份。", None,
        time="北宋熙宁八年九月", event="因兵部掌诸路保甲训练而增置一人",
        category="兵部变法差遣",
    )
    chain_all(w, eid, [tid], "确认同判尚书省兵部事现有完整时间链。")
    rel(w, ft(w, fe(w, "兵部", "机构"), "北宋熙宁八年"), tid,
        "编制隶属", i, main, "熙宁八年九月兵部增同判一人。",
        staff_quota=1, staff_type="官")
    w.commit()


def entry1169():
    i = 1169
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "兵部勾当公事", "官职")
    start = refine(
        w, ft(w, eid, "北宋熙宁八年"), i, main,
        "专条细化兵部勾当公事职掌。", None,
        event="始置，赴诸路州军提举保甲教阅训练", category="兵部变法差遣",
    )
    end = tp(
        w, eid, "北宋元丰三年", "罢废",
        i, main, "兵部变法差遣", "建立兵部勾当公事元丰三年罢废节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接兵部勾当公事始置与罢废节点。")
    rel(w, ft(w, fe(w, "兵部", "机构"), "北宋熙宁八年"), start,
        "编制隶属", i, main, "熙宁八年兵部置勾当公事官赴诸路教阅保甲。",
        staff_quota=10, staff_type="官")
    w.commit()


def entry1170():
    i = 1170
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "兵部主簿", "官职")
    tid = refine(
        w, ft(w, eid, "北宋熙宁八年"), i, main,
        "专条细化兵部主簿职掌。", None,
        event="掌诸路保甲教阅簿书", category="兵部变法差遣",
    )
    chain_all(w, eid, [tid], "确认兵部主簿现有完整时间链。")
    rel(w, ft(w, fe(w, "兵部", "机构"), "北宋熙宁八年"), tid,
        "编制隶属", i, main, "兵部主簿掌诸路保甲教阅簿书。",
        staff_quota=2, staff_type="官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1151, 1171)] == [
        "监度牒库", "提领度牒所", "提举京城所", "主客司", "主客司郎中",
        "主客司员外郎", "员郎", "知杂封袭朝贡案", "膳部司", "膳部司郎中",
        "膳部司员外郎", "祠祭生料知杂案", "宴设馆客供进给赐案", "礼部贡院",
        "知礼部贡举事", "尚书省兵部", "判尚书省兵部事", "同判尚书省兵部事",
        "兵部勾当公事", "兵部主簿",
    ]
    assert F[1157]["fields"].get("__status__") == "placeholder" and not F[1157]["text"]
    entry1151()
    entry1152()
    entry1153()
    entry1154()
    entry1155()
    entry1156()
    entry1158()
    entry1159()
    entry1160()
    entry1161()
    merge_shanbu_cases(
        1162, "祠祭生料知杂案", ("膳部司祠祭案", "膳部司生料案", "膳部司知杂案"),
        "由祠祭、生料、知杂三案省并，掌祠祭饔饩、藏冰与本司杂事",
    )
    merge_shanbu_cases(
        1163, "宴设馆客供进给赐案",
        ("膳部司宴设案", "膳部司馆客案", "膳部司供进案", "膳部司给赐案"),
        "由宴设、馆客、供进、给赐四案省并，掌宴席外宾酒食、乳酪、藏冰及所属司局",
    )
    entry1164()
    entry1165()
    entry1166()
    entry1167()
    entry1168()
    entry1169()
    entry1170()


if __name__ == "__main__":
    main()
