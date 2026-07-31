#!/usr/bin/env python3
"""提取 chapter5t7 第441-460条：驼坊属员、养象所、车营致远务与御辇院。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_421_440 as previous


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch5t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter5t7 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(441, 461)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
state = base.state
relation = base.relation
staff = base.staff
tp = base.tp
alias_note = base.alias_note


TIME_HINTS = {
    "北宋乾德五年八月": 967.62,
    "北宋开宝五年": 972,
    "北宋景德四年十一月": 1007.88,
    "北宋天禧五年正月": 1021.04,
    "北宋天圣元年闰九月": 1023.72,
    "北宋元丰五年七月": 1082.54,
    "北宋元丰改制后": 1082.6,
    "北宋（改隶驾部年月未载）": 1090,
    "北宋崇宁二年二月十二日": 1103.12,
    "北宋崇宁二年二月十四日": 1103.13,
    "北宋靖康元年正月四日": 1126.02,
    "南宋": 1127,
    "南宋建炎三年": 1129,
    "南宋绍兴八年九月三十日": 1138.75,
    "南宋绍兴十二年十二月二十九日": 1142.99,
    "南宋乾道九年": 1173,
    "南宋淳熙十三年十二月九日": 1186.95,
    "南宋淳熙十六年": 1189,
    "南宋景定间": 1260,
    "宋代（养象所郊祀大礼）": 1050,
    "宋代（车营务）": 1000,
    "宋代（御辇院北宋编制）": 1050.1,
    "宋代（御辇院公吏）": 1050.2,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    m = re.search(r"(-?\d{3,4})", time or "")
    if m:
        return (int(m.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [r[0] for r in sorted(rows, key=lambda r: time_key(r[1], r[0]))]
    for n, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[n - 1] if n else None,
            succ_id=ordered[n + 1] if n + 1 < len(ordered) else None,
        )


def set_event(w, tid, event, decision):
    old = w.conn.execute("select event from Timepoints where id=?", (tid,)).fetchone()[0]
    if old != event:
        w.conn.execute("update Timepoints set event=? where id=?", (event, tid))
        w._br("Timepoints", tid, f"事件说明由‘{old}’规范为‘{event}’：{decision}")


def exact_state(w, i, title, type_, time, event, quotation, category, decision,
                field_name=None, *, officer=None, grade=None, note=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade, note=note,
    )
    set_event(w, tid, event, decision)
    return eid, tid


def simple_post(i, title, event, category, *, time="宋代（御辇院北宋编制）",
                officer=None, quota=None, parent_time="宋代（御辇院北宋编制）"):
    main = F[i]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, title, "官职", time, event, main, category,
        f"建立{title}在御辇院的职掌与位次。", officer=officer or title,
    )
    staff(
        w, i, tp(w, "供御营", "机构", parent_time), post, main,
        f"御辇院供御营设置{title}。", quota=quota, staff_type=officer or title,
    )
    rechain(w, eid, f"整理{title}时间链。")
    w.commit()


def entry441():
    i, main = 441, F[441]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "同干办驼坊公事", "官职", "南宋绍兴八年九月三十日",
        "始置，兼领皮剥所公事，编制一员", main,
        "驼坊差遣", "建立同干办驼坊公事始置、职掌与定额。",
        officer="差遣",
    )
    staff(w, i, tp(w, "驼坊", "机构", "南宋"), post, main,
          "绍兴八年置同干办驼坊公事。", quota=1, staff_type="差遣")
    rechain(w, eid, "整理同干办驼坊公事时间链。")
    w.commit()


def entry442():
    i = 442
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "养象所", "机构", "北宋乾德五年八月",
        "始置于开封玉津园，调驯大象，供郊祀大驾卤簿仪仗前导引",
        history, "太仆寺属局", "建立养象所始置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充养象所职掌。", "职掌")
    _, few = exact_state(
        w, i, "养象所", "机构", "北宋天禧五年正月",
        "所养大象减至三头，此前最多四十五头", roster,
        "太仆寺属局", "建立天禧五年养象规模节点。", "编制",
    )
    _, south = exact_state(
        w, i, "养象所", "机构", "南宋",
        "沿置于御马院，归驼坊兼管", history,
        "驼坊属局", "建立南宋养象所沿置与隶属节点。", "职源与沿革",
    )
    relation(w, i, tp(w, "驼坊", "机构", "南宋"), south,
             "上下级机构", F[i]["text"], "南宋养象所归驼坊兼管。")
    _, tribute = exact_state(
        w, i, "养象所", "机构", "南宋乾道九年",
        "豢养安南进贡大象十五头", roster,
        "驼坊属局", "建立乾道九年养象规模节点。", "编制",
    )
    alias_note(w, i, south, aliases, "简称与别名")
    touched.add(eid)
    ceremony_eid, ceremony = exact_state(
        w, i, "养象所郊祀大礼差设", "机构", "宋代（养象所郊祀大礼）",
        "郊祀大礼时临时差置监官、专典、人员、曹司、教头、簇象兵士及驾部职级手分",
        roster, "临时编制", "建立养象所郊祀临时差设编制。", "编制",
    )
    relation(w, i, start, ceremony, "上下级机构", roster,
             "养象所行郊祀大礼时临时差设人员。", "编制")
    touched.add(ceremony_eid)
    for title, officer, quota in (
        ("养象所监官", "监官", 3), ("专典", "专典", 3),
        ("养象所人员", "人员", 2), ("养象所曹司", "曹司", 1),
        ("养象所教头", "教头", 6), ("簇象兵士", "兵士", 49),
        ("养象所驾部职级、手分", "驾部职级、手分", 3),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（养象所郊祀大礼）",
            f"养象所行郊祀大礼时临时差置{officer}{quota}人", roster,
            "养象所临时属员", f"建立养象所郊祀所置{officer}。", "编制",
            officer=officer,
        )
        staff(w, i, ceremony, post, roster, f"郊祀时差置{officer}{quota}人。",
              "编制", quota=quota, staff_type=officer)
        touched.add(seid)
    for entity_id in touched:
        rechain(w, entity_id, "整理养象所及郊祀临时差设完整时间链。")
    w.commit()


def entry443():
    i, main = 443, F[443]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "专典", "官职", "宋代（养象所郊祀大礼）",
        "公吏名；专知官、副知均可别称专典，掌管押官物；养象所郊祀时置三人",
        main, "公吏", "补充专典释名、职掌与养象所用例。", officer="公吏",
    )
    staff(w, i, tp(w, "养象所郊祀大礼差设", "机构", "宋代（养象所郊祀大礼）"),
          post, main, "养象所郊祀监官三员、专典三人。", quota=3, staff_type="专典")
    rechain(w, eid, "整理专典时间链。")
    w.commit()


def entry444():
    i, main = 444, F[444]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职能"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    eid, start = exact_state(
        w, i, "车营务", "机构", "北宋开宝五年",
        "已置于开封敦教坊，掌养驴牛、驾车运物及安置苦役",
        origin, "监当局", "建立车营务最早见置节点。", "职源",
    )
    cite(w, "Timepoints", start, i, duty, "补充车营务职能。", "职能")
    _, roster_node = exact_state(
        w, i, "车营务", "机构", "宋代（车营务）",
        "设监官三人、役卒四千四百零一人", roster,
        "监当局", "建立车营务编制节点。", "编制",
    )
    relation(w, i, tp(w, "太仆寺", "机构", "宋前期"), start,
             "上下级机构", main, "车营务先隶太仆寺。")
    _, later = exact_state(
        w, i, "车营务", "机构", "北宋（改隶驾部年月未载）",
        "由太仆寺改隶驾部，具体年月未载", main,
        "驾部属局", "补足车营务后隶驾部节点。",
    )
    relation(w, i, tp(w, "驾部", "机构", "北宋（未载改隶具体年月）"), later,
             "上下级机构", main, "车营务后隶驾部。")
    alias_note(w, i, roster_node, aliases, "简称")
    rechain(w, eid, "整理车营务时间链。")
    w.commit()


def entry445():
    i, main, aliases = 445, F[445]["text"], field(445, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "监车营务", "官职", "宋代（车营务）",
        "由内侍或三班使臣、文臣京朝官、武臣诸司使副充，掌纠领车营务，编制三人",
        main, "车营务监官", "建立监车营务任用、职掌与定额。", officer="监当差遣",
    )
    staff(w, i, tp(w, "车营务", "机构", "宋代（车营务）"), post, main,
          "车营务置监官三人。", quota=3, staff_type="监官")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理监车营务时间链。")
    w.commit()


def entry446():
    i, main = 446, F[446]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    eid, start = exact_state(
        w, i, "致远务", "机构", "北宋景德四年十一月",
        "见置于开封永泰坊，掌饲养驴骡并运载乘舆行幸什器与边防军装",
        origin, "监当局", "建立致远务见置节点。", "职源",
    )
    cite(w, "Timepoints", start, i, duty, "补充致远务职掌。", "职掌")
    _, reform = exact_state(
        w, i, "致远务", "机构", "北宋元丰改制后",
        "隶太仆寺，监官三人由监车营务官兼领，兵校一千六百二十四人",
        roster, "太仆寺属局", "建立致远务编制与兼领节点。", "编制",
    )
    relation(w, i, tp(w, "太仆寺", "机构", "北宋元丰五年五月一日"), reform,
             "上下级机构", main, "致远务先后隶太仆寺。")
    _, later = exact_state(
        w, i, "致远务", "机构", "北宋（改隶驾部年月未载）",
        "由太仆寺改隶驾部，具体年月未载", main,
        "驾部属局", "补足致远务后隶驾部节点。",
    )
    relation(w, i, tp(w, "驾部", "机构", "北宋（未载改隶具体年月）"), later,
             "上下级机构", main, "致远务后隶驾部。")
    staff(w, i, reform, tp(w, "监车营务", "官职", "宋代（车营务）"), roster,
          "致远务监官由监车营务官兼领。", "编制", quota=3, staff_type="兼领监官")
    alias_note(w, i, reform, aliases, "简称")
    rechain(w, eid, "整理致远务时间链。")
    w.commit()


def entry447():
    i, main = 447, F[447]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, early = exact_state(
        w, i, "御辇院", "机构", "宋前期",
        "置于京师右承天门外，掌皇帝步辇供奉及后宫乘车祗应，初隶提举在京诸司库务司、太仆寺",
        history, "御前应奉机构", "建立御辇院宋前期节点。", "职源与沿革",
    )
    cite(w, "Timepoints", early, i, duty, "补充御辇院职掌。", "职掌")
    supervisor_eid, supervisor = exact_state(
        w, i, "提举在京诸司库务司", "机构", "宋前期",
        "御辇院初隶机构之一", main, "京师库务提举机构",
        "据御辇院初隶关系建立提举在京诸司库务司节点。",
    )
    relation(w, i, supervisor, early, "上下级机构", main,
             "御辇院初隶提举在京诸司库务司。")
    relation(w, i, tp(w, "太仆寺", "机构", "宋前期"), early,
             "上下级机构", main, "御辇院初隶太仆寺。")
    _, direct = exact_state(
        w, i, "御辇院", "机构", "北宋元丰五年七月",
        "定不隶省寺，专隶于皇帝", main,
        "御前应奉机构", "建立元丰五年直属皇帝节点。",
    )
    _, merged = exact_state(
        w, i, "御辇院", "机构", "北宋崇宁二年二月十二日",
        "职事并入殿中省尚辇局", duty,
        "御前应奉机构", "建立职事并入尚辇局节点。", "职掌",
    )
    _, renamed = exact_state(
        w, i, "御辇院", "机构", "北宋崇宁二年二月十四日",
        "改名中车院", aliases,
        "御前应奉机构", "建立改名中车院节点。", "简称与别名",
    )
    middle_eid, middle = exact_state(
        w, i, "中车院", "机构", "北宋崇宁二年二月十四日",
        "御辇院改名而来", aliases,
        "御前应奉机构", "建立中车院承接节点。", "简称与别名",
    )
    relation(w, i, renamed, middle, "前后演变", aliases,
             "崇宁二年御辇院改为中车院。", "简称与别名")
    relation(w, i, merged, tp(w, "尚辇局", "机构", "北宋崇宁二年二月"),
             "前后演变", duty, "御辇院供御职事并入尚辇局。", "职掌")
    _, restored = exact_state(
        w, i, "御辇院", "机构", "北宋靖康元年正月四日",
        "殿中省及尚辇局罢，原职事复归御辇院", duty,
        "御前应奉机构", "建立靖康元年复归节点。", "职掌",
    )
    relation(w, i, tp(w, "尚辇局", "机构", "北宋靖康元年"), restored,
             "前后演变", duty, "靖康元年尚辇局罢，职事复归御辇院。", "职掌")
    _, south = exact_state(
        w, i, "御辇院", "机构", "南宋",
        "南宋沿置", history, "御前应奉机构",
        "建立南宋沿置节点。", "职源与沿革",
    )
    _, fixed = exact_state(
        w, i, "御辇院", "机构", "南宋绍兴十二年十二月二十九日",
        "与下都营合定一千人为额：供御辇官二百、次供御辇官一百五十、下都营六百五十",
        roster, "御前应奉机构", "建立绍兴十二年定额节点。", "编制",
    )
    alias_note(w, i, direct, aliases, "简称与别名")
    touched.update((eid, middle_eid, supervisor_eid))
    for title, event in (
        ("供御营", "御辇院所辖供御辇官营"),
        ("次供御营", "御辇院所辖次供御辇官营"),
        ("下都营", "御辇院所辖辇官营"),
        ("车子院", "御辇院所辖车子兵士机构"),
    ):
        seid, child = exact_state(
            w, i, title, "机构", "宋代（御辇院北宋编制）", event, roster,
            "御辇院属营院", f"建立御辇院所辖{title}。", "编制",
        )
        relation(w, i, early, child, "上下级机构", roster,
                 f"御辇院辖有{title}。", "编制")
        touched.add(seid)
    for title, officer, quota in (
        ("供御辇官", "供御辇官", 92), ("次供御辇官", "次供御辇官", 77),
        ("下都辇官", "辇官", 578), ("车子院兵士", "兵士", 89),
    ):
        parent = "车子院" if title == "车子院兵士" else (
            "下都营" if title == "下都辇官" else
            ("次供御营" if title == "次供御辇官" else "供御营")
        )
        seid, post = exact_state(
            w, i, title, "官职", "宋代（御辇院北宋编制）",
            f"御辇院北宋编制所置{officer}{quota}人", roster,
            "御辇院应奉人", f"建立御辇院北宋{officer}定额。", "编制", officer=officer,
        )
        staff(w, i, tp(w, parent, "机构", "宋代（御辇院北宋编制）"), post,
              roster, f"{parent}置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    for title, officer, quota, parent in (
        ("供御辇官", "供御辇官", 200, "供御营"),
        ("次供御辇官", "次供御辇官", 150, "次供御营"),
        ("下都辇官", "辇官", 650, "下都营"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "南宋绍兴十二年十二月二十九日",
            f"御辇院与下都营合定一千人时，{officer}定额{quota}人", roster,
            "御辇院应奉人", f"建立绍兴十二年{officer}定额。", "编制", officer=officer,
        )
        parent_eid, parent_node = exact_state(
            w, i, parent, "机构", "南宋绍兴十二年十二月二十九日",
            f"御辇院绍兴十二年定额所含{parent}", roster,
            "御辇院属营院", f"建立绍兴十二年{parent}节点。", "编制",
        )
        relation(w, i, fixed, parent_node, "上下级机构", roster,
                 f"御辇院绍兴十二年定额包含{parent}。", "编制")
        staff(w, i, parent_node, post, roster, f"{parent}置{officer}{quota}人。",
              "编制", quota=quota, staff_type=officer)
        touched.update((seid, parent_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理御辇院、改名机构及属营院完整时间链。")
    w.commit()


def entry448():
    i, main, aliases = 448, F[448]["text"], field(448, "简称")
    w = W(i)
    eid, normal = exact_state(
        w, i, "监御辇院", "官职", "宋代（御辇院北宋编制）",
        "由入内省内侍官和诸司使武臣充，掌纠领御辇院公事，通常三至四人",
        main, "御辇院监官", "建立监御辇院任用、职掌与常额。", officer="监官",
    )
    staff(w, i, tp(w, "御辇院", "机构", "宋前期"), normal, main,
          "御辇院置监官三至四人。", staff_type="监官")
    _, reduced = exact_state(
        w, i, "监御辇院", "官职", "南宋建炎三年",
        "曾减为二人", main, "御辇院监官",
        "建立建炎三年减额节点。", officer="监官",
    )
    alias_note(w, i, normal, aliases, "简称")
    rechain(w, eid, "整理监御辇院时间链。")
    w.commit()


def entry449():
    simple_post(449, "供御指挥使", "御辇院供御营长官，总辖本营，编制一人",
                "供御营长官", officer="指挥使", quota=1)


def entry450():
    simple_post(450, "供御都虞候", "御辇院供御营部辖官，位次于指挥使、高于军使，编制一人",
                "供御营部辖官", officer="都虞候", quota=1)


def entry451():
    simple_post(451, "供御军使", "御辇院供御营部辖官，位次于都虞候、高于副兵马使，编制一人",
                "供御营部辖官", officer="军使", quota=1)


def entry452():
    simple_post(452, "供御副兵马使", "御辇院供御营部辖官，位次于军使、高于十将，编制三人",
                "供御营部辖官", officer="副兵马使", quota=3)


def entry453():
    simple_post(453, "供御十将", "御辇院供御营部辖小校，位次于副兵马使、高于将虞候，编制三人",
                "供御营小校", officer="十将", quota=3)


def entry454():
    i, main = 454, F[454]["text"]
    w = W(i)
    parent_eid, parent = exact_state(
        w, i, "供御营", "机构", "北宋天圣元年闰九月",
        "御辇院供御营于此时新添将虞候", main,
        "御辇院属营院", "建立供御将虞候始置时的供御营节点。",
    )
    eid, post = exact_state(
        w, i, "供御将虞候", "官职", "北宋天圣元年闰九月",
        "于御辇院新添置，由节级依次迁补", main,
        "供御营小校", "建立供御将虞候始置与迁补节点。", officer="将虞候",
    )
    staff(w, i, parent, post, main, "供御营于天圣元年新添将虞候。",
          staff_type="将虞候")
    rechain(w, parent_eid, "整理供御营完整时间链。")
    rechain(w, eid, "整理供御将虞候时间链。")
    w.commit()


def entry455():
    simple_post(455, "管押节级", "管押随行车驾的衣褥等官物",
                "供御营部辖人员", officer="节级")


def entry456():
    simple_post(456, "祇应节级", "部辖辇官抬、擎、扛御前物色等祗应事",
                "供御营部辖人员", officer="节级")


def entry457():
    i, main, aliases = 457, F[457]["text"], field(457, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "供御辇官", "官职", "宋代（御辇院北宋编制）",
        "轮班擎抬御辇，亲近皇帝，出缺从次供御辇官中按身高、目力、体健、过犯和年龄严选",
        main, "御辇院应奉人", "补足供御辇官职任与选拔条件。", officer="应奉人",
    )
    staff(w, i, tp(w, "供御营", "机构", "宋代（御辇院北宋编制）"), post,
          main, "供御营由供御辇官组成。", staff_type="辇官")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理供御辇官时间链。")
    w.commit()


def entry458():
    i, main, aliases = 458, F[458]["text"], field(458, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "次供御辇官", "官职", "宋代（御辇院北宋编制）",
        "轮班随乘舆抬御衣箱，编制或七十七人、或一百五十人",
        main, "御辇院应奉人", "补足次供御辇官职任与编制。", officer="应奉人",
    )
    staff(w, i, tp(w, "次供御营", "机构", "宋代（御辇院北宋编制）"), post,
          main, "次供御营由次供御辇官组成。", staff_type="辇官")
    _, reduced = exact_state(
        w, i, "次供御辇官", "官职", "南宋淳熙十三年十二月九日",
        "御辇院减次供御辇二十人", aliases,
        "御辇院应奉人", "建立淳熙十三年减额节点。", "简称", officer="应奉人",
    )
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理次供御辇官时间链。")
    w.commit()


def entry459():
    i, main = 459, F[459]["text"]
    w = W(i)
    eid, unit = exact_state(
        w, i, "供御营", "机构", "南宋绍兴十二年十二月二十九日",
        "在京厢军番号，由御辇院供御辇官组成，定额二百人，归供御指挥使、副兵马使管",
        main, "在京厢军", "建立绍兴十二年供御营定额与管辖。",
    )
    relation(w, i, tp(w, "御辇院", "机构", "南宋绍兴十二年十二月二十九日"),
             unit, "上下级机构", main, "供御营为御辇院所辖在京厢军。")
    staff(w, i, unit, tp(w, "供御辇官", "官职", "南宋绍兴十二年十二月二十九日"),
          main, "供御营由供御辇官组成，绍兴十二年定额二百人。",
          quota=200, staff_type="系兵籍应奉人")
    rechain(w, eid, "整理供御营时间链。")
    w.commit()


def entry460():
    i, main = 460, F[460]["text"]
    w = W(i)
    eid, unit = exact_state(
        w, i, "次供御营", "机构", "南宋绍兴十二年十二月二十九日",
        "在京厢军番号，由御辇院次供御辇官组成，定额一百五十人，归供御指挥使、副兵马使管辖",
        main, "在京厢军", "建立绍兴十二年次供御营定额与管辖。",
    )
    relation(w, i, tp(w, "御辇院", "机构", "南宋绍兴十二年十二月二十九日"),
             unit, "上下级机构", main, "次供御营为御辇院所辖在京厢军。")
    staff(w, i, unit, tp(w, "次供御辇官", "官职", "南宋绍兴十二年十二月二十九日"),
          main, "次供御营由次供御辇官组成，绍兴十二年定额一百五十人。",
          quota=150, staff_type="系军籍应奉人")
    rechain(w, eid, "整理次供御营时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(441, 461)] == [
        "同干办驼坊公事", "养象所", "专典", "车营务", "监车营务",
        "致远务", "御辇院", "监御辇院", "供御指挥使", "供御都虞候",
        "供御军使", "供御副兵马使", "供御十将", "供御将虞候",
        "管押节级", "祇应节级", "供御辇官", "次供御辇官",
        "供御营", "次供御营",
    ]
    for i in range(441, 461):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
