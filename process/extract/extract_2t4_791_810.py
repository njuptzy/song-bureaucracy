#!/usr/bin/env python3
"""提取 chapter2t4 第791–810条：中书后省官属与检正官系统。"""
import extract_2t4_771_790 as b


b.F = {i: b.load(i) for i in range(791, 811)}
W = b.W
Q = b.Q
fe = b.fe
ft = b.ft
cite = b.cite
tp = b.tp
rel = b.rel
chain_all = b.chain_all
refine = b.refine
relation_id = b.relation_id
set_rel_attrs = b.set_rel_attrs
mark_citation_conflict = b.mark_citation_conflict


def entry791():
    i = 791
    origin = Q(
        i,
        "中书舍人之名始于晋。《晋中兴书》：“刘起迁中书舍人。”"
        "中书省舍人始于唐武德二年",
        "职源",
    )
    duty = Q(
        i,
        "②元丰新制，为职事官，舍人六员轮直草拟诏命，并分工签押本省"
        "吏、户、礼、兵、刑、工六房文书，如发现事有失当或除授非妥，许封还词头",
        "职掌",
    )
    south_duty = Q(
        i,
        "③南宋之制，为中书后省长官，一员领吏房左选及兵工房，"
        "一员领吏部右选及礼刑上房、礼刑下房，掌行诰命，签押中书省诸房文书，"
        "及为召试吏人出选题、考试等",
        "职掌",
    )
    grade = Q(
        i,
        "① 宋前期，依唐制为正五品上。② 元丰新制正四品",
        "官品",
    )
    w = W(i)
    eid = fe(w, "中书舍人", "官职")
    jin = tp(
        w, eid, "晋", "始有中书舍人之名", i, origin,
        "中书官", "建中书舍人官名源流节点。", "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐武德二年", "中书省始置舍人", i, origin,
        "中书官", "建中书省舍人始置节点。", "职源", chain="none",
    )
    song = refine(
        w, ft(w, eid, "宋前期"), i, grade,
        "专条补证宋前期中书舍人为迁转官阶及其品位。", "官品",
        event="无职事，为文臣迁转官阶", category="阶官", grade="正五品上",
    )
    tianxi = ft(w, eid, "北宋天禧元年八月")
    cite(w, "Timepoints", tianxi, i, duty, "专条补证中书舍人后来正名职掌。", "职掌")
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制（中书省）"), i, duty,
        "专条细化元丰中书舍人草诏、签押六房与封还词头之职。", "职掌",
        event="正名为职事官，轮直草诏、签押六房文书并可封还词头",
        category="职事官", grade="正四品",
    )
    cite(w, "Timepoints", yuanfeng, i, grade, "专条补证元丰品位为正四品。", "官品")
    south = refine(
        w, ft(w, eid, "南宋（未载具体年月）"), i, south_duty,
        "专条细化南宋中书舍人为后省长官及分房职掌。", "职掌",
        event="为中书后省长官，分领诸房，掌诰命、签押及召试吏人",
        category="职事官",
    )
    chain_all(w, eid, [jin, tang, song, tianxi, yuanfeng, south],
              "连接中书舍人晋唐源流、宋前期阶官及元丰以后职事官节点。")
    rid = relation_id(
        w, "中书后省", "中书舍人", "编制隶属",
        "北宋元丰四年十月", "北宋元丰新制（中书省）",
    )
    assert rid
    cite(w, "Relationships", rid, i, duty,
         "专条补证元丰中书后省设中书舍人六员。", "职掌")
    rid = relation_id(
        w, "中书后省", "中书舍人", "编制隶属",
        "南宋建炎三年", "南宋（未载具体年月）",
    )
    assert rid
    cite(w, "Relationships", rid, i, south_duty,
         "专条补证南宋中书舍人为后省长官且常除二员。", "职掌")
    w.commit()


def entry792():
    i = 792
    alias = Q(i, "权舍人。见上引《朝野杂记》。", "简称")
    w = W(i)
    eid = fe(w, "权中书舍人", "官职")
    cite(
        w, "Timepoints", ft(w, eid, "北宋元丰改制"), i, alias,
        "专条仅载权中书舍人的简称“权舍人”，附于既有制度节点。", "简称",
    )
    w.commit()


def entry793():
    i = 793
    origin = Q(
        i,
        "隋炀帝大业三年置内史省起居舍人，即唐初之中书省起居舍人之任",
        "职源",
    )
    duty = Q(
        i,
        "②元丰新制，与起居郎共为史官，记录皇帝言行、群臣殿上进对、"
        "朝廷发命的命令、敕宥、文武臣除授、礼乐法度增删、气候、符瑞、"
        "户口增减、州县废置等国事活动，以送史馆修史之用",
        "职掌",
    )
    grade = Q(
        i,
        "① 宋前期依唐制为从六品上。② 元丰新制后，从六品",
        "官品",
    )
    w = W(i)
    eid = fe(w, "起居舍人", "官职")
    sui = tp(
        w, eid, "隋大业三年", "内史省始置起居舍人", i, origin,
        "起居官", "建起居舍人隋代源流节点。", "职源", chain="none",
    )
    song = refine(
        w, ft(w, eid, "宋初"), i, grade,
        "专条补证宋前期起居舍人为迁转阶官及其品位。", "官品",
        time="宋前期", event="无职守，为文臣迁转叙禄官阶",
        category="阶官", grade="从六品上",
    )
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, duty,
        "专条细化元丰起居舍人的记注史官职掌。", "职掌",
        event="与起居郎共任史官，记录国事送史馆修史",
        category="起居官", grade="从六品",
    )
    cite(w, "Timepoints", yuanfeng, i, grade, "专条补证元丰后从六品。", "官品")
    south = ft(w, eid, "南宋建炎三年（中书后省）")
    cite(w, "Timepoints", south, i, duty, "南宋沿元丰起居史官制度。", "职掌")
    chain_all(w, eid, [sui, song, yuanfeng, south],
              "连接起居舍人隋代源流、宋前期阶官与元丰正名节点。")
    for rid in (
        relation_id(w, "中书后省", "起居舍人", "编制隶属",
                    "北宋元丰四年十月", "北宋元丰五年五月"),
        relation_id(w, "中书省", "起居舍人", "编制隶属",
                    "北宋元丰新制", "北宋元丰五年五月"),
    ):
        assert rid
        cite(w, "Relationships", rid, i, duty,
             "专条补证元丰起居舍人隶中书省后省并举史官职。", "职掌")
    w.commit()


def entry794():
    i = 794
    origin = Q(
        i,
        "散骑常侍之名始置于曹魏黄初初年。散骑常侍之分左、右始于唐显庆二年",
        "职源",
    )
    duty = Q(
        i,
        "①名为谏官之长，宋前期无职守，为文臣迁转官阶。"
        "②元丰正名后，因品位高，为宰相所压，亦未曾除人",
        "职掌",
    )
    grade = Q(
        i,
        "① 宋前期依唐制，为正三品下。元丰新制，右散骑常侍正三品",
        "官品",
    )
    w = W(i)
    eid = fe(w, "右散骑常侍", "官职")
    cao = tp(
        w, eid, "曹魏黄初初年", "始置散骑常侍", i, origin,
        "谏官", "建散骑常侍曹魏源流节点。", "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐显庆二年", "散骑常侍始分左、右", i, origin,
        "谏官", "建右散骑常侍形成节点。", "职源", chain="none",
    )
    song = refine(
        w, ft(w, eid, "宋代（未载具体年月）"), i, duty,
        "专条细化宋前期右散骑常侍为无职守迁转官阶。", "职掌",
        time="宋前期", event="名为谏官之长，实无职守，为文臣迁转官阶",
        category="阶官", grade="正三品下",
    )
    cite(w, "Timepoints", song, i, grade, "专条补证宋前期品位。", "官品")
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰新制（中书省）"), i, duty,
        "专条补证元丰正名后右散骑常侍仍未除人。", "职掌",
        event="正名为中书后省谏官之长，因品位高而未曾除人",
        category="谏官", grade="正三品",
    )
    cite(w, "Timepoints", yuanfeng, i, grade, "专条补证元丰正三品。", "官品")
    south = ft(w, eid, "南宋建炎三年（中书后省）")
    chain_all(w, eid, [cao, tang, song, yuanfeng, south],
              "连接右散骑常侍曹魏、唐及宋代制度节点。")
    for subject_time, object_time in (
        ("北宋元丰四年十月", "北宋元丰新制（中书省）"),
        ("南宋建炎三年", "南宋建炎三年（中书后省）"),
    ):
        rid = relation_id(
            w, "中书后省", "右散骑常侍", "编制隶属",
            subject_time, object_time,
        )
        assert rid
        cite(w, "Relationships", rid, i, duty,
             "专条补证右散骑常侍属于中书后省官额。", "职掌")
    w.commit()


def entry795():
    i = 795
    origin = Q(
        i,
        "谏议大夫始置于后汉（《后汉书·百官志》）。"
        "唐德宗贞元四年（787）始分左、右，右谏议大夫隶中书省",
        "职源",
    )
    duty = Q(
        i,
        "①宋前期，谏议大夫不亲掌言事，仅天禧三年曾除职事官，其后又罢，"
        "主要用作文臣迁转叙位禄阶官，元丰寄禄易为正议大夫",
        "职掌",
    )
    new_duty = Q(
        i,
        "②元丰新制，任言职，谏正朝政失误、任人不当、三省以至百司违失",
        "职掌",
    )
    grade = Q(
        i,
        "①宋初沿唐制为正四品下。②元丰新制从四品",
        "官品",
    )
    w = W(i)
    eid = fe(w, "右谏议大夫", "官职")
    han = tp(
        w, eid, "后汉", "始置谏议大夫", i, origin,
        "谏官", "建谏议大夫后汉源流节点。", "职源", chain="none",
    )
    tang = tp(
        w, eid, "唐贞元四年", "谏议大夫始分左、右，右谏议大夫隶中书省", i, origin,
        "谏官", "建右谏议大夫形成节点。", "职源", chain="none",
    )
    song = refine(
        w, ft(w, eid, "北宋元丰改制前"), i, duty,
        "专条细化宋前期右谏议大夫主要为迁转阶官。", "职掌",
        time="宋前期", event="主要为文臣迁转叙位禄阶官，天禧三年曾短暂任言职",
        category="阶官", grade="正四品下",
    )
    cite(w, "Timepoints", song, i, grade, "专条补证宋初正四品下。", "官品")
    yuanfeng = refine(
        w, ft(w, eid, "北宋元丰改制后"), i, new_duty,
        "专条细化元丰右谏议大夫言职。", "职掌",
        time="北宋元丰新制",
        event="任言职，谏正朝政、用人及三省百司违失",
        category="谏官", grade="从四品",
    )
    cite(w, "Timepoints", yuanfeng, i, grade, "专条补证元丰从四品。", "官品")
    generic = ft(w, eid, "宋代（未载具体年月）")
    cite(w, "Timepoints", generic, i, new_duty, "专条补证其为大两省谏官。", "职掌")
    south = ft(w, eid, "南宋")
    chain_all(w, eid, [han, tang, song, yuanfeng, generic, south],
              "连接右谏议大夫后汉、唐及宋代制度节点。")
    for subject_time, object_time in (
        ("北宋元丰四年十月", "北宋元丰新制"),
        ("南宋建炎三年", "南宋"),
    ):
        rid = relation_id(
            w, "中书后省", "右谏议大夫", "编制隶属",
            subject_time, object_time,
        )
        assert rid
        cite(w, "Relationships", rid, i, new_duty,
             "专条补证右谏议大夫属于中书后省谏官。", "职掌")
    w.commit()


def entry797():
    i = 797
    history = Q(
        i,
        "唐则天皇帝垂拱元年(685)初置（《新唐书·百官志》2）。北宋初沿置。"
        "端拱元年改右补阙为右司谏（《长编》卷29）。"
        "南宋淳熙十五年复置右补阙，绍熙二年又改为右司谏",
        "职源与沿革",
    )
    duty = Q(
        i,
        "宋初，言事官需在谏院供职，右补阙无职守，为文臣迁转官阶。",
        "职掌",
    )
    south = Q(
        i,
        "南宋淳熙复置，是专职谏官、不兼纠弹之职",
        "职掌",
    )
    w = W(i)
    eid = fe(w, "右补阙", "官职")
    for time in ("唐垂拱元年", "北宋端拱元年二月八日", "南宋绍熙二年"):
        cite(w, "Timepoints", ft(w, eid, time), i, history,
             "专条补证右补阙置改沿革。", "职源与沿革")
    cite(w, "Timepoints", ft(w, eid, "北宋初"), i, duty,
         "专条补证宋初右补阙为无职守迁转阶官。", "职掌")
    cite(w, "Timepoints", ft(w, eid, "南宋淳熙十五年"), i, south,
         "专条补证南宋复置后专任谏职且不兼纠弹。", "职掌")
    for subject_time, object_time in (
        ("北宋端拱元年二月八日", "北宋端拱元年二月八日"),
        ("南宋绍熙二年", "南宋"),
    ):
        rid = relation_id(
            w, "右补阙", "右司谏", "前后演变", subject_time, object_time
        )
        if rid:
            cite(w, "Relationships", rid, i, history,
                 "专条补证右补阙改为右司谏。", "职源与沿革")
        else:
            rel(
                w,
                ft(w, eid, subject_time),
                ft(w, fe(w, "右司谏", "官职"), object_time),
                "前后演变",
                i,
                history,
                "专条补建绍熙二年右补阙再改右司谏关系。",
                "职源与沿革",
            )
    w.commit()


def entry798():
    i = 798
    origin = Q(
        i,
        "北宋端拱元年二月八日始置右司谏",
        "职源",
    )
    duty = Q(
        i,
        "①端拱元年改左、右补阙为左、右司谏，举行谏官之职，"
        "论朝政之得失、刑政之烦苛。②不久，成为差遣官兼官，起本官阶叙位禄之用。"
        "③元丰新制正名，为职事官，掌规谏朝政阙失、用人不当，并兼弹纠",
        "职掌",
    )
    w = W(i)
    eid = fe(w, "右司谏", "官职")
    for time in (
        "北宋端拱元年二月八日",
        "北宋端拱以后（未载具体年月）",
        "北宋元丰新制",
        "南宋",
    ):
        cite(w, "Timepoints", ft(w, eid, time), i, duty,
             "专条补证右司谏由初置职事官转为兼官、元丰再正名的沿革。", "职掌")
    cite(w, "Timepoints", ft(w, eid, "北宋端拱元年二月八日"), i, origin,
         "专条补证右司谏确切始置日。", "职源")
    rid = relation_id(
        w, "右补阙", "右司谏", "前后演变",
        "北宋端拱元年二月八日", "北宋端拱元年二月八日",
    )
    assert rid
    cite(w, "Relationships", rid, i, duty,
         "专条补证右补阙改为右司谏。", "职掌")
    w.commit()


def entry799():
    i = 799
    history = Q(
        i,
        "唐垂拱元年始置《新唐书·百官志》2《门下省》)。北宋初沿置。"
        "端拱元年二月八日，改右拾遗为右正言",
        "职源与沿革",
    )
    south_history = Q(
        i,
        "南宋淳熙十五年正月八日，复置右拾遗（《朝野杂记》甲集卷10《拾遗、补阙》）。"
        "绍熙二年，又改右拾遗为右正言",
        "职源与沿革",
    )
    duty = Q(
        i,
        "①宋初无职守，为文臣差遣所带阶官。②南宋淳熙十五年复置，"
        "为职事官，职掌谏诤（但不兼弹劾）",
        "职掌",
    )
    w = W(i)
    eid = fe(w, "右拾遗", "官职")
    for time in ("唐垂拱元年", "北宋初", "北宋端拱元年二月八日"):
        cite(w, "Timepoints", ft(w, eid, time), i, history,
             "专条补证右拾遗唐宋置改沿革。", "职源与沿革")
    for time in ("南宋淳熙十五年正月八日", "南宋绍熙二年"):
        cite(w, "Timepoints", ft(w, eid, time), i, south_history,
             "专条补证右拾遗南宋复置再改沿革。", "职源与沿革")
    for time in ("北宋初", "南宋淳熙十五年正月八日"):
        cite(w, "Timepoints", ft(w, eid, time), i, duty,
             "专条补证右拾遗宋初与南宋职掌差异。", "职掌")
    rid = relation_id(
        w, "右拾遗", "右正言", "前后演变",
        "北宋端拱元年二月八日", "北宋端拱元年二月八日",
    )
    assert rid
    cite(w, "Relationships", rid, i, history,
         "专条补证右拾遗改为右正言。", "职源与沿革")
    rel(
        w,
        ft(w, eid, "南宋绍熙二年"),
        ft(w, fe(w, "右正言", "官职"), "南宋"),
        "前后演变",
        i,
        south_history,
        "专条补建绍熙二年右拾遗再改右正言关系。",
        "职源与沿革",
    )
    w.commit()


def entry800():
    i = 800
    origin = Q(i, "太宗端拱元年二月八日始置", "职源")
    duty = Q(
        i,
        "宋初无言事职守，为文臣迁转官阶。真宗天禧元年(1017)"
        "在中书、门下两省置谏官，右正言为职事官。",
        "职掌",
    )
    new_duty = Q(
        i,
        "元丰改制，任谏职并兼弹纠",
        "职掌",
    )
    w = W(i)
    eid = fe(w, "右正言", "官职")
    cite(w, "Timepoints", ft(w, eid, "北宋端拱元年二月八日"), i, origin,
         "专条补证右正言始置日。", "职源")
    for time in ("宋前期（未载具体年月）", "北宋天禧元年"):
        cite(w, "Timepoints", ft(w, eid, time), i, duty,
             "专条补证右正言由迁转阶官到职事谏官的变化。", "职掌")
    cite(w, "Timepoints", ft(w, eid, "北宋元丰新制"), i, new_duty,
         "专条补证元丰右正言任谏职并兼弹纠。", "职掌")
    rid = relation_id(
        w, "右拾遗", "右正言", "前后演变",
        "北宋端拱元年二月八日", "北宋端拱元年二月八日",
    )
    assert rid
    cite(w, "Relationships", rid, i, duty,
         "专条补证右正言由右拾遗改置。", "职掌")
    w.commit()


def entry801():
    i = 801
    history = Q(
        i,
        "古无此官，熙宁三年（1070）九月一日首创（《长编》卷215）。"
        "元丰五年改制罢，其职事归中书舍人、给事中、都司郎官。",
        "职源与沿革",
    )
    duty = Q(
        i,
        "检查、核对、纠正、催促中书门下处理的公务，权任颇重",
        "职掌",
    )
    quota = Q(i, "一人（《石林燕语》卷9）。", "编制")
    w = W(i)
    eid = fe(w, "检正中书五房公事", "官职")
    start = refine(
        w, ft(w, eid, "北宋熙宁三年九月一日"), i, duty,
        "专条细化都检正的检核、厘正、催促职掌。", "职掌",
        event="始置一人，检查、核对、纠正并催促中书门下公务",
        category="宰属官",
    )
    cite(w, "Timepoints", start, i, history, "专条补证确切始置日。", "职源与沿革")
    cite(w, "Timepoints", start, i, quota, "专条补证编制一人。", "编制")
    end = refine(
        w, ft(w, eid, "北宋元丰五年"), i, history,
        "专条补证元丰改制罢检正五房公事及职事归属。", "职源与沿革",
        event="改制罢，职事归中书舍人、给事中、都司郎官",
        category="宰属官",
    )
    chain_all(w, eid, [start, end], "连接检正中书五房公事置罢节点。")
    rid = relation_id(
        w, "中书门下", "检正中书五房公事", "编制隶属",
        "宋前期", "北宋熙宁三年九月一日",
    )
    assert rid
    set_rel_attrs(w, rid, 1, "官", "专条补证都检正编制一人。")
    cite(w, "Relationships", rid, i, quota,
         "专条补证检正中书五房公事隶中书门下且置一人。", "编制")
    w.commit()


def entry803():
    i = 803
    origin = Q(i, "与“检正中书五房公事”同。", "职源与沿革")
    duty = Q(i, "掌本房检查、核对、纠正、催促文书公事。", "职掌")
    quota = Q(
        i,
        "①熙宁三年初置，逐房各二员，以士人朝官充。②元丰元年，逐房检正官减员，"
        "五房共止置五员。户房检正公事二员，吏、礼、孔目房检正公事，"
        "三房各置一员",
        "编制",
    )
    w = W(i)
    generic_e = fe(w, "检正中书某房公事", "官职")
    generic_start = refine(
        w, ft(w, generic_e, "北宋熙宁三年九月一日"), i, duty,
        "专条细化逐房检正官职掌。", "职掌",
        event="逐房各置二员，以士人朝官充，检核、厘正并催促本房文书",
        category="宰属官",
    )
    cite(w, "Timepoints", generic_start, i, origin,
         "专条说明沿革同检正中书五房公事。", "职源与沿革")
    generic_reduce = tp(
        w, generic_e, "北宋元丰元年", "逐房检正减为五员", i, quota,
        "宰属官", "建逐房检正官减员节点。", "编制", chain="none",
    )
    generic_end = tp(
        w, generic_e, "北宋元丰五年", "随官制改革罢去", i, origin,
        "宰属官", "据与都检正同沿革建罢置节点。", "职源与沿革", chain="none",
    )
    chain_all(w, generic_e, [generic_start, generic_reduce, generic_end],
              "连接逐房检正官始置、减员与罢置节点。")

    specs = (
        ("检正中书孔目房公事", "制敕院孔目房", 1, "元丰元年减为一员"),
        ("检正中书吏房公事", "制敕院吏房", 1, "元丰元年减为一员"),
        ("检正中书户房公事", "制敕院户房", 2, "元丰元年仍置二员"),
        ("检正中书礼房公事", "制敕院兵、礼房", 1, "元丰元年减为一员"),
        ("检正中书刑房公事", "制敕院刑房", 0, "元丰元年减罢，不在五员之列"),
    )
    for title, office_title, reduced_quota, reduce_event in specs:
        eid = fe(w, title, "官职")
        start = ft(w, eid, "北宋熙宁三年九月一日")
        cite(w, "Timepoints", start, i, duty, f"专条补证{title}职掌。", "职掌")
        cite(w, "Timepoints", start, i, quota, f"专条补证{title}初置二员。", "编制")
        reduce = tp(
            w, eid, "北宋元丰元年", reduce_event, i, quota,
            "宰属官", f"建{title}元丰减员节点。", "编制", chain="none",
        )
        end = tp(
            w, eid, "北宋元丰五年", "随官制改革罢去", i, origin,
            "宰属官", f"据与都检正同沿革建{title}罢置节点。", "职源与沿革",
            chain="none",
        )
        chain_all(w, eid, [start, reduce, end],
                  f"连接{title}始置、减员与罢置节点。")
        start_rid = relation_id(
            w, office_title, title, "编制隶属",
            "北宋熙宁三年九月", "北宋熙宁三年九月一日",
        )
        assert start_rid
        set_rel_attrs(w, start_rid, 2, "官", "专条补证逐房检正初置各二员。")
        cite(w, "Relationships", start_rid, i, quota,
             f"专条补证{office_title}初置{title}二员。", "编制")
        if reduced_quota:
            office_e = fe(w, office_title, "机构")
            office_reduce = tp(
                w, office_e, "北宋元丰元年", "逐房检正官减员后沿置", i, quota,
                "中书门下办事机构", f"为{title}减员关系建立同期机构节点。", "编制",
                chain="none",
            )
            office_ids = [
                row[0] for row in w.conn.execute(
                    "select id from Timepoints where entity_id=? order by id", (office_e,)
                )
            ]
            ordered = sorted(
                office_ids,
                key=lambda tid: (
                    0 if tid == ft(w, office_e, "宋前期") else
                    1 if tid == ft(w, office_e, "北宋熙宁三年九月") else 2
                ),
            )
            chain_all(w, office_e, ordered, f"将{office_title}元丰元年节点接入时间链。")
            rel(
                w, office_reduce, reduce, "编制隶属", i, quota,
                f"元丰元年{office_title}仍置{title}{reduced_quota}员。",
                "编制", staff_quota=reduced_quota, staff_type="官",
            )
    w.commit()


def entry806():
    i = 806
    history = Q(
        i,
        "熙宁三年十一月始设，以初入仕人为之（《宋会要·职官》3之26）。"
        "元丰新制罢去不置",
        "职源与沿革",
    )
    duty = Q(i, "实习中书政事，增广议论", "职掌")
    w = W(i)
    eid = w.entity(
        "中书逐房习学公事", "官职",
        "据专条建立熙宁间供初入仕者实习中书政事的宰属官。",
        quotation=history,
    )
    start = tp(
        w, eid, "北宋熙宁三年十一月", "始设，以初入仕者实习中书政事、增广议论",
        i, history, "宰属官", "建中书逐房习学公事始置节点。", "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "专条补证习学公事职掌。", "职掌")
    end = tp(
        w, eid, "北宋元丰五年", "新官制罢去不置", i, history,
        "宰属官", "建中书逐房习学公事罢置节点。", "职源与沿革", chain="none",
    )
    chain_all(w, eid, [start, end], "连接中书逐房习学公事置罢节点。")
    rel(
        w, ft(w, fe(w, "中书门下", "机构"), "宋前期"), start,
        "编制隶属", i, history, "中书门下设置逐房习学公事。",
        "职源与沿革", staff_type="官",
    )
    w.commit()


def entry807():
    i = 807
    origin = Q(
        i,
        "南宋建炎三年四月二十九日，中书省、门下省合为一省",
        "职源",
    )
    later = Q(i, "乾道八年二月罢三省长官之后，三省不废。", "职源")
    quota = Q(
        i,
        "吏额：并省后，自录事至守当官为二百三十八人",
        "编制",
    )
    w = W(i)
    eid = fe(w, "中书门下省", "机构")
    start = refine(
        w, ft(w, eid, "南宋建炎三年四月二十九日"), i, origin,
        "专条补证中书省、门下省合并为中书门下省。", "职源",
        event="中书省、门下省合并，兼行两省职事",
        category="中央政务机构",
    )
    cite(
        w, "Timepoints", start, i, quota,
        "专条称并省后吏额二百三十八人；与中书省条的八十九人另守阙一百五十人合计二百三十九不一致。",
        "编制",
        note="本条总称吏额238人；中书省条分项为正式吏额89人、守阙守当官150人，合计239人。",
        conflict_flag=1,
    )
    mark_citation_conflict(
        w, "Timepoints", start, i, quota,
        "本条总称吏额238人；中书省条分项为正式吏额89人、守阙守当官150人，合计239人。",
        "保留中书门下省吏额总数与既有分项合计不一致。",
        "编制",
    )
    end = tp(
        w, eid, "南宋乾道八年二月", "罢三省长官，但三省机构不废", i, later,
        "中央政务机构", "建乾道罢长官而三省不废节点。", "职源", chain="none",
    )
    chain_all(w, eid, [start, end], "连接中书门下省并省与乾道罢长官节点。")
    w.commit()


def entry808():
    i = 808
    history = Q(
        i,
        "南宋建炎三年五月二十二日始置（《宋会要·职官》3之46），"
        "四年九月十六日省，绍兴二年三月十五日复设",
        "职源与沿革",
    )
    duty = Q(
        i,
        "专检举通进司每日承受、进降、给发等文书，并检察中书门下省文字"
        "按限发放，不许留滞",
        "职掌",
    )
    quota = Q(
        i,
        "①建炎三年初置二员，一员分工检正吏、礼房，一员检正户、刑、工房。"
        "四年罢。②绍兴二年复置一员，后沿置",
        "编制",
    )
    w = W(i)
    eid = w.entity(
        "中书门下省检正诸房公事", "官职",
        "据专条建立南宋中书门下省检举、稽核文书的宰属官。",
        quotation=history,
    )
    start = tp(
        w, eid, "南宋建炎三年五月二十二日",
        "始置二员，分检吏礼房与户刑工房文书",
        i, history, "宰属官", "建检正诸房公事始置节点。", "职源与沿革",
        chain="none", attr_grade="正六品",
    )
    cite(w, "Timepoints", start, i, duty, "专条补证检举与按限发放职掌。", "职掌")
    cite(w, "Timepoints", start, i, quota, "专条补证初置二员及分工。", "编制")
    stop = tp(
        w, eid, "南宋建炎四年九月十六日", "省罢", i, history,
        "宰属官", "建检正诸房公事省罢节点。", "职源与沿革",
        chain="none", attr_grade="正六品",
    )
    restore = tp(
        w, eid, "南宋绍兴二年三月十五日", "复置一员，后沿置", i, history,
        "宰属官", "建检正诸房公事复置节点。", "职源与沿革",
        chain="none", attr_grade="正六品",
    )
    cite(w, "Timepoints", restore, i, quota, "专条补证复置后定额一员。", "编制")
    chain_all(w, eid, [start, stop, restore], "连接检正诸房公事始置、省罢与复置节点。")
    institute = fe(w, "中书门下省", "机构")
    institute_start = ft(w, institute, "南宋建炎三年四月二十九日")
    rel(
        w, institute_start, start, "编制隶属", i, quota,
        "中书门下省初置检正诸房公事二员。", "编制",
        staff_quota=2, staff_type="官",
    )
    rel(
        w, institute_start, restore, "编制隶属", i, quota,
        "中书门下省绍兴二年复置检正诸房公事一员。", "编制",
        staff_quota=1, staff_type="官",
    )
    w.commit()


def entry809():
    i = 809
    first = Q(
        i,
        "（乾道）六年三月二十三日，检正房状：‘依指挥并省吏额。’",
        "简称",
    )
    second = Q(
        i,
        "隆兴元年八月三日，中书门下省检正房状：‘依指挥并省吏额。’",
        "简称",
    )
    w = W(i)
    eid = w.entity(
        "中书门下省检正房", "机构",
        "据专条全称及上状记录建立中书门下省检正房机构。",
        quotation=second,
    )
    t1 = tp(
        w, eid, "南宋隆兴元年八月三日", "上状依指挥并省吏额", i, second,
        "中书门下省办事机构", "建检正房隆兴上状节点。", "简称", chain="none",
    )
    t2 = tp(
        w, eid, "南宋乾道六年三月二十三日", "上状依指挥并省吏额", i, first,
        "中书门下省办事机构", "建检正房乾道上状节点。", "简称", chain="none",
    )
    chain_all(w, eid, [t1, t2], "连接中书门下省检正房隆兴、乾道见载节点。")
    rel(
        w, ft(w, fe(w, "中书门下省", "机构"), "南宋建炎三年四月二十九日"),
        t1, "上下级机构", i, second,
        "全称表明检正房隶中书门下省。", "简称",
    )
    w.commit()


def entry810():
    i = 810
    main = Q(
        i,
        "淳熙十三年十二月九日，诏检正所减亲事官一人。",
        "简称",
    )
    w = W(i)
    eid = w.entity(
        "中书门下省检正所", "机构",
        "据专条全称与诏令记录建立中书门下省检正所机构。",
        quotation=main,
    )
    tid = tp(
        w, eid, "南宋淳熙十三年十二月九日", "奉诏减亲事官一人", i, main,
        "中书门下省办事机构", "建检正所减员节点。", "简称",
    )
    rel(
        w, ft(w, fe(w, "中书门下省", "机构"), "南宋建炎三年四月二十九日"),
        tid, "上下级机构", i, main,
        "全称表明检正所隶中书门下省。", "简称",
    )
    w.commit()


def main():
    entry791()
    entry792()
    entry793()
    entry794()
    entry795()
    # 第796条“直舍人院”无独立正文；已有第69条完整抽取，不凭空追加。
    entry797()
    entry798()
    entry799()
    entry800()
    entry801()
    # 第802条“都检正厅”无独立正文，不凭标题造数据。
    entry803()
    # 第804条为OCR误切后保留的空占位；第805条“检正厅”无独立正文。
    entry806()
    entry807()
    entry808()
    entry809()
    entry810()


if __name__ == "__main__":
    main()
