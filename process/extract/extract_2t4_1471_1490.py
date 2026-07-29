#!/usr/bin/env python3
"""提取 chapter2t4 第1471–1490条：太史局学生司辰群体与造历局。"""
import extract_2t4_1451_1470 as x

base = x.base
base.F = {i: base.load(i) for i in range(1471, 1491)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def bureau(w, south=False):
    time = "南宋绍兴元年二月十九日" if south else "北宋元丰五年五月"
    return ft(w, fe(w, "太史局", "机构"), time)


def alias(w, tid, i):
    for key in ("简称", "别称"):
        if key in F[i]["fields"]:
            cite(w, "Timepoints", tid, i, field(i, key),
                 f"{F[i]['title']}称谓仅作名称证据。", key,
                 note="纯简称或别称")


def entry1471():
    i = 1471
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "太史局礼生", "官职")
    tid = refine(
        w, ft(w, eid, "宋代太史局时期"), i, main,
        "专条细化太史局礼生来源、职掌与出职条件。",
        event="由局学生迁补，掌行遣文字；头名满五年且到局祗应满二十年，可出职补进义副尉",
        category="太史局吏人", officer="吏",
    )
    chain_all(w, eid, [tid], "确认太史局礼生单节点完整时间链。")
    rel(w, bureau(w), tid, "编制隶属", i, main, "礼生隶太史局。",
        staff_type="吏")
    w.commit()


def entry1472():
    i = 1472
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("太史局学生", "官职", "本条直接定义太史局学生。",
                   quotation=main)
    tid = tp(
        w, eid, "宋代太史局时期",
        "习学天文、历算、三式并随所祗应；分祠祭、瞻望及额内、额外，积年劳考试可升礼生、历生或局生",
        i, main, "太史局学生", "建立太史局学生节点。",
        attr_officer_type="学生",
    )
    alias(w, tid, i)
    rel(w, bureau(w), tid, "编制隶属", i, main, "学生隶太史局。",
        staff_type="学生")
    for title, time in (
        ("太史局礼生", "宋代太史局时期"),
        ("太史局历生", "宋代太史局时期"),
        ("局生", "南宋淳熙四年八月十四日"),
    ):
        rel(w, tid, ft(w, fe(w, title, "官职"), time),
            "前后演变", i, main, f"太史局学生积年劳并经考试可升为{title}。")
    w.commit()


def entry1473():
    i = 1473
    main, history, duty = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌")
    w = W(i)
    eid = w.entity("司辰", "官职", "本条直接定义宋代四院司辰武吏。",
                   quotation=main)
    sui = tp(w, eid, "隋代", "始置司辰师，掌刻漏时辰",
             i, history, "前代职源", "建立司辰隋代职源节点。",
             "职源与沿革", attr_officer_type="技术官", chain="none")
    tang = tp(w, eid, "唐代", "挈壶正属官有司辰",
              i, history, "前代职源", "建立司辰唐代节点。",
              "职源与沿革", attr_officer_type="技术官", chain="none")
    song = tp(
        w, eid, "北宋宣和二年九月以后",
        "宋不置司辰官，改以太史局诸处供职节级、卒伍为司辰总称，掌看守、供役、押送文书",
        i, history, "太史局武吏总称", "建立宋代司辰武吏节点。",
        "职源与沿革", attr_officer_type="武吏", chain="none",
    )
    cite(w, "Timepoints", song, i, duty, "补证宋代司辰职掌待遇。",
         "职掌")
    chain_all(w, eid, [sui, tang, song], "连接司辰隋、唐与宋代节点。")
    for parent, time in (
        ("太史局", "北宋元丰五年五月"),
        ("太史局天文院", "北宋元丰五年"),
        ("钟鼓院", "北宋元丰五年五月"),
        ("测验浑仪刻漏所", "北宋元丰五年五月"),
    ):
        rel(w, ft(w, fe(w, parent, "机构"), time), song,
            "编制隶属", i, main, f"司辰分隶{parent}。", staff_type="武吏")
    w.commit()


def entry1474():
    i = 1474
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("四院司辰", "官职", "本条定义四院司辰总名。",
                   quotation=main)
    total = tp(w, eid, "宋代太史局时期",
               "太史局、天文院、钟鼓院、测验浑仪刻漏所司辰总名",
               i, main, "太史局武吏统称", "建立四院司辰统称节点。",
               attr_officer_type="武吏统称")
    for title, parent, parent_time in (
        ("太史局司辰", "太史局", "北宋元丰五年五月"),
        ("天文院司辰", "太史局天文院", "北宋元丰五年"),
        ("钟鼓院司辰", "钟鼓院", "北宋元丰五年五月"),
        ("浑仪刻漏所司辰", "测验浑仪刻漏所", "北宋元丰五年五月"),
    ):
        child_e = w.entity(title, "官职", f"四院司辰条明确列举{title}。",
                           quotation=main)
        child_t = tp(w, child_e, "宋代太史局时期", f"{parent}所属司辰",
                     i, main, "太史局武吏", f"建立{title}节点。",
                     attr_officer_type="武吏")
        rel(w, total, child_t, "统称与实例", i, main,
            f"{title}是四院司辰实例。")
        rel(w, ft(w, fe(w, parent, "机构"), parent_time), child_t,
            "编制隶属", i, main, f"{title}隶{parent}。", staff_type="武吏")
    w.commit()


def entry1475():
    i = 1475
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("太史局官生学生", "官职",
                   "本条定义太史局官、局生、礼生、历生、学生总名。",
                   quotation=main)
    total = tp(w, eid, "宋代太史局时期",
               "太史局官、局生、礼生、历生及学生总名",
               i, main, "太史局官生统称", "建立太史局官生学生统称节点。",
               attr_officer_type="官生学生统称")
    alias(w, total, i)
    official_e = w.entity("太史局官", "官职", "本条明确列举太史局官。",
                          quotation=main)
    official_t = tp(w, official_e, "宋代太史局时期", "太史局官员总称",
                    i, main, "太史局官员统称", "建立太史局官节点。",
                    attr_officer_type="技术官统称")
    children = [
        official_t,
        ft(w, fe(w, "局生", "官职"), "南宋淳熙四年八月十四日"),
        ft(w, fe(w, "太史局礼生", "官职"), "宋代太史局时期"),
        ft(w, fe(w, "太史局历生", "官职"), "宋代太史局时期"),
        ft(w, fe(w, "太史局学生", "官职"), "宋代太史局时期"),
    ]
    labels = ["太史局官", "局生", "太史局礼生", "太史局历生", "太史局学生"]
    for label, child in zip(labels, children):
        rel(w, total, child, "统称与实例", i, main,
            f"{label}属于太史局官生学生总名。")
    w.commit()


def compound_group(i, title, description, child_specs):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}连称或总称。",
                   quotation=main)
    total = tp(w, eid, "宋代太史局时期", description,
               i, main, "太史局官生复合统称", f"建立{title}节点。",
               attr_officer_type="复合统称")
    for child_title, event in child_specs:
        child_e = w.find_entity(child_title, "官职")
        if child_e:
            row = w.conn.execute(
                "select id from Timepoints where entity_id=? order by id limit 1",
                (child_e,),
            ).fetchone()
            child_t = row[0]
            cite(w, "Timepoints", child_t, i, main,
                 f"{title}条补证{child_title}是其组成名目。")
        else:
            child_e = w.entity(child_title, "官职",
                               f"{title}条明确列举{child_title}。",
                               quotation=main)
            child_t = tp(w, child_e, "宋代太史局时期", event,
                         i, main, "太史局官生名目",
                         f"建立{child_title}节点。",
                         attr_officer_type="武吏或学生")
        rel(w, total, child_t, "统称与实例", i, main,
            f"{child_title}是{title}的组成名目。")
    w.commit()


def entry1482():
    i = 1482
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("造历局", "机构", "本条直接定义临时造历局。",
                   quotation=main)
    tid = tp(w, eid, "宋代造新历期间",
             "造新历时临时置局差官，事毕罢局，无固定机构",
             i, main, "临时造历机构", "建立造历局临时节点。")
    w.commit()


def calendar_post(i, title, event, officer_type, pay=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义造历局{title}。",
                   quotation=main)
    full_event = event + (f"；{pay}" if pay else "")
    tid = tp(w, eid, "宋代造新历期间", full_event,
             i, main, "造历局官吏", f"建立{title}造历局节点。",
             attr_officer_type=officer_type)
    alias(w, tid, i)
    rel(w, ft(w, fe(w, "造历局", "机构"), "宋代造新历期间"),
        tid, "编制隶属", i, main, f"{title}隶临时造历局。",
        staff_type=officer_type)
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1471, 1491)] == [
        "礼生", "学生", "司辰", "四院司辰", "太史局官生学生",
        "太史局额内局学生", "太史局额外祠祭局学生",
        "太史局额内外局生", "天文院司辰额内瞻望局学生",
        "浑仪所司辰额内瞻望局学生", "钟鼓院司辰局学生",
        "造历局", "提领造历官", "参定造历官", "演撰官",
        "提督推算", "推算官", "推算学生", "草泽应聘造历人",
        "向上人吏",
    ]
    entry1471()
    entry1472()
    entry1473()
    entry1474()
    entry1475()
    compound_group(1476, "太史局额内局学生", "太史局编制内局生、学生连称", [
        ("太史局额内局生", "太史局编制内局生"),
        ("太史局额内学生", "太史局编制内学生"),
    ])
    compound_group(1477, "太史局额外祠祭局学生",
                   "太史局编制外专供祠祭行事的局生、学生连称", [
        ("太史局额外祠祭局生", "编制外祠祭局生"),
        ("太史局额外祠祭学生", "编制外祠祭学生"),
    ])
    compound_group(1478, "太史局额内外局生", "太史局编制内外局生总称", [
        ("太史局额内局生", "太史局编制内局生"),
        ("太史局额外局生", "太史局编制外局生"),
    ])
    compound_group(1479, "天文院司辰额内瞻望局学生",
                   "天文院司辰、额内瞻望局生、额内瞻望学生连称", [
        ("天文院司辰", "天文院所属司辰"),
        ("天文院额内瞻望局生", "天文院额内瞻望局生"),
        ("天文院额内瞻望学生", "天文院额内瞻望学生"),
    ])
    compound_group(1480, "浑仪所司辰额内瞻望局学生",
                   "浑仪所司辰、额内瞻望局生、额内瞻望学生连称", [
        ("浑仪刻漏所司辰", "浑仪所所属司辰"),
        ("浑仪所额内瞻望局生", "浑仪所额内瞻望局生"),
        ("浑仪所额内瞻望学生", "浑仪所额内瞻望学生"),
    ])
    compound_group(1481, "钟鼓院司辰局学生",
                   "文德殿钟鼓院司辰、局生、学生连称", [
        ("钟鼓院司辰", "钟鼓院所属司辰"),
        ("钟鼓院局生", "钟鼓院局生"),
        ("钟鼓院学生", "钟鼓院学生"),
    ])
    entry1482()
    calendar_post(1483, "提领造历官", "由秘书省长官充，总掌造新历",
                  "差遣")
    calendar_post(1484, "参定造历官", "由稍通历书朝官兼充，参与论定新历",
                  "差遣")
    calendar_post(1485, "演撰官", "由精通历书局官充，为造历主要承担人",
                  "差遣", "每日支饭食钱八贯三十文")
    calendar_post(1486, "提督推算", "由精通历书局官充，掌领推算官、生运算",
                  "差遣")
    calendar_post(1487, "推算官", "由能运算的太史局局生充",
                  "差遣", "每日支食钱四贯")
    calendar_post(1488, "推算学生", "由能运算的太史局学生充，位次推算官",
                  "差遣", "每日支食钱四贯")
    calendar_post(1489, "草泽应聘造历人",
                  "开局造历时应榜入局的精通算术历法布衣",
                  "应聘人员", "每日支食钱六贯")
    calendar_post(1490, "向上人吏", "专掌对上司行遣文字", "吏")


if __name__ == "__main__":
    main()
