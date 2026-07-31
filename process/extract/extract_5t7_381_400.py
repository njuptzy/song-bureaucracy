#!/usr/bin/env python3
"""提取 chapter5t7 第381-400条：街仗司官吏、六军仪仗司与羽林军。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_361_380 as previous


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


F = {i: load(i) for i in range(381, 401)}
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
    "秦汉": -221, "西汉武帝太初元年": -104,
    "唐代": 618, "唐代（三卫）": 700,
    "唐龙朔二年": 662, "唐兴元元年正月二十九日": 784.08,
    "唐贞元间": 785, "五代藩镇": 907,
    "宋代": 960, "宋代（金吾引驾仗司）": 960.06,
    "宋代（金吾街仗司官吏）": 960.07,
    "宋代（六军仪仗司）": 960.08,
    "宋代大驾卤簿（年月未载）": 960.09,
    "宋初": 960.1, "宋初南郊（年月未载）": 960.11,
    "北宋初（州郡胥府）": 960.25, "北宋": 970,
    "北宋至道元年": 995,
    "北宋咸平元年十一月十九日": 998.86,
    "北宋嘉祐二年二月十五日": 1057.12,
    "北宋治平三年九月": 1066.70,
    "北宋元丰五年": 1082,
    "南宋": 1127, "南宋淳熙十四年": 1187,
    "南宋绍熙二年": 1191, "南宋绍熙三年": 1192,
    "南宋孝宗朝": 1162,
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


def entry381():
    i, main, aliases = 381, F[381]["text"], field(381, "简称")
    w = W(i)
    eid = w.find_entity("右金吾街仗司", "机构")
    assert eid
    merged = tp(w, "右金吾街仗司", "机构", "南宋淳熙十四年")
    right_street = tp(w, "右金吾街司", "机构", "南宋淳熙十四年")
    right_guard = tp(w, "右金吾引驾仗司", "机构", "南宋淳熙十四年")
    relation(w, i, merged, right_street, "统称与实例", main,
             "右金吾街司为右金吾街仗司合称所含实例。")
    relation(w, i, merged, right_guard, "统称与实例", main,
             "右金吾引驾仗司为右金吾街仗司合称所含实例。")
    cite(w, "Timepoints", merged, i, main,
         "确认右金吾街仗司为右街司与右引驾仗司合称。")
    _, report = exact_state(
        w, i, "右金吾街仗司", "机构", "南宋绍熙三年",
        "申报沿用淳熙十四年裁减指挥，右司仍以一百二十一人为额",
        aliases, "金吾街仗机构", "建立绍熙三年右街仗司复申定额节点。", "简称",
        note="纯简称、别名不另建实体",
    )
    rechain(w, eid, "整理右金吾街仗司合称、改编与定额时间链。")
    w.commit()


def entry382():
    i, main = 382, F[382]["text"]
    w = W(i)
    touched = set()
    generic_eid, north = exact_state(
        w, i, "左、右金吾街仗司", "机构", "北宋",
        "左、右金吾街司与左、右金吾引驾仗司四司的总称，常以一判官总辖",
        main, "机构统称", "建立北宋四司总称。",
    )
    _, concurrent = exact_state(
        w, i, "左、右金吾街仗司", "机构", "北宋嘉祐二年二月十五日",
        "勾当官兼管六军仪仗司，统辖仪卫、禁卫、仪物修饰与金吾兵迁补",
        main, "京城仪卫机构统称", "建立嘉祐二年兼管六军仪仗司节点。",
    )
    _, south = exact_state(
        w, i, "左、右金吾街仗司", "机构", "南宋淳熙十四年",
        "左金吾街仗司、右金吾街仗司两司的总称", main,
        "机构统称", "建立淳熙十四年左右街仗司总称。",
    )
    for title, time in (
        ("左、右金吾街司", "北宋元丰五年"),
        ("左、右金吾引驾仗司", "北宋元丰五年"),
    ):
        relation(w, i, north, tp(w, title, "机构", time), "统称与实例", main,
                 f"{title}为北宋左、右金吾街仗司总称实例。")
    for title in ("左金吾街仗司", "右金吾街仗司"):
        relation(w, i, south, tp(w, title, "机构", "南宋淳熙十四年"),
                 "统称与实例", main, f"{title}为南宋左、右金吾街仗司实例。")
    touched.add(generic_eid)
    rechain(w, generic_eid, "整理左、右金吾街仗司两种组合与兼领职掌时间链。")
    w.commit()


def entry383():
    i, main = 383, F[383]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "判左、右金吾街仗司", "官职", "北宋",
        "街司、仗司总辖官，以环卫官或六统军将军以上充",
        main, "金吾街仗司总辖官", "建立判左、右金吾街仗司任用与职掌。",
        officer="环卫官或六统军将军以上差遣",
    )
    staff(w, i, tp(w, "左、右金吾街仗司", "机构", "北宋"), post,
          main, "北宋左、右金吾街仗司置判司总辖官。",
          staff_type="环卫官或六统军将军以上差遣")
    rechain(w, eid, "整理判左、右金吾街仗司时间链。")
    w.commit()


def entry384():
    i, main = 384, F[384]["text"]
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "左、右金吾都监兼勾当街仗司事", "官职", "北宋至道元年",
        "始置，由内侍充，分左、右二官，总辖新募金吾兵并管领街司、仗司，位次判街仗司事",
        main, "金吾街仗司差遣统称", "建立至道元年左右金吾都监兼勾当街仗司事。",
        officer="内侍差遣",
    )
    staff(w, i, tp(w, "左、右金吾街仗司", "机构", "北宋"), generic,
          main, "左、右金吾街仗司分置左右都监兼勾当官二人。",
          quota=2, staff_type="内侍差遣")
    touched.add(generic_eid)
    for side in ("左", "右"):
        title = f"{side}金吾都监兼勾当街仗司事"
        eid, post = exact_state(
            w, i, title, "官职", "北宋至道元年",
            f"{side}金吾都监兼勾当街仗司事，内侍充", main,
            "金吾街仗司差遣", f"建立{title}实例。", officer="内侍差遣",
        )
        relation(w, i, generic, post, "统称与实例", main,
                 f"{title}为左、右金吾都监兼勾当街仗司事实例。")
        touched.add(eid)
    soldier_eid, soldiers = exact_state(
        w, i, "金吾兵", "官职", "北宋至道元年",
        "新招募二千人，由左、右金吾都监总辖", main,
        "金吾街仗司兵役", "建立至道元年新募金吾兵定额。", officer="兵士",
    )
    staff(w, i, tp(w, "左、右金吾街仗司", "机构", "北宋"), soldiers,
          main, "左右金吾街仗司新募金吾兵二千人。", quota=2000, staff_type="兵士")
    touched.add(soldier_eid)
    for eid in touched:
        rechain(w, eid, "整理左右金吾都监、实例与金吾兵时间链。")
    w.commit()


def entry385():
    i, main = 385, F[385]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "勾当左右金吾街仗、六军仪仗司事", "官职",
        "北宋嘉祐二年二月十五日",
        "一官兼任左右金吾街仗司勾当官与六军仪仗司主管，整肃皇帝仪卫、禁卫",
        main, "仪卫机构兼领差遣", "建立兼领街仗司与六军仪仗司的勾当官。", officer="勾当官",
    )
    six_eid, six = exact_state(
        w, i, "六军仪仗司", "机构", "北宋嘉祐二年二月十五日",
        "由勾当左右金吾街仗司官兼领", main,
        "宫廷仪仗机构", "建立嘉祐二年六军仪仗司兼领节点。",
    )
    staff(w, i, tp(w, "左、右金吾街仗司", "机构", "北宋嘉祐二年二月十五日"),
          post, main, "勾当官一人兼领左右金吾街仗司。", quota=1, staff_type="勾当官")
    staff(w, i, six, post, main, "同一勾当官兼领六军仪仗司。", quota=1, staff_type="勾当官")
    rechain(w, eid, "整理街仗司、六军仪仗司兼领差遣时间链。")
    rechain(w, six_eid, "整理六军仪仗司兼领时间链。")
    w.commit()


def entry386():
    i, main = 386, F[386]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "干办左、右金吾街仗司事", "官职", "南宋",
        "南宋由勾当官改称干办官，以大夫以上充，干办左右金吾街仗司事务",
        main, "金吾街仗司差遣", "恢复并建立南宋干办左、右金吾街仗司事。",
        officer="大夫以上差遣",
    )
    staff(w, i, tp(w, "左、右金吾街仗司", "机构", "南宋淳熙十四年"),
          post, main, "南宋左、右金吾街仗司置干办官。", staff_type="大夫以上差遣")
    rechain(w, eid, "整理干办左、右金吾街仗司事时间链。")
    w.commit()


def street_guard_clerk(i, title, event, *, parent="street_guard", officer="公吏"):
    main = F[i]["text"]
    w = W(i)
    time = (
        "宋代（金吾街仗司官吏）"
        if parent == "street_guard" else "宋代（金吾引驾仗司）"
    )
    category = "金吾街仗司人吏" if parent == "street_guard" else "金吾引驾仗司官吏"
    eid, post = exact_state(
        w, i, title, "官职", time, event, main,
        category, f"补足{title}的金吾街仗司语境职掌。", officer=officer,
    )
    parent_tp = (
        tp(w, "左、右金吾街仗司", "机构", "北宋")
        if parent == "street_guard"
        else tp(w, "左、右金吾引驾仗司", "机构", "北宋初")
    )
    staff(w, i, parent_tp, post, main, f"本司设置{title}。", staff_type=officer)
    rechain(w, eid, f"整理{title}职源及金吾仪仗职掌时间链。")
    w.commit()


def entry387():
    street_guard_clerk(
        387, "孔目官",
        "左、右金吾街仗司皆置，为吏人资序最高者，承办本司事务并点检文书",
    )


def entry388():
    i, main = 388, F[388]["text"]
    w = W(i)
    eid, five_dynasties = exact_state(
        w, i, "勾押官", "官职", "五代藩镇",
        "节度使自辟州郡吏，位次孔目官", main,
        "前代吏职", "建立勾押官五代职源。", officer="州郡吏",
    )
    _, current = exact_state(
        w, i, "勾押官", "官职", "宋代（金吾街仗司官吏）",
        "左、右金吾街仗司皆置，位次孔目官，相当于主事，承办本司事务",
        main, "金吾街仗司人吏", "补足勾押官在金吾街仗司的位次与职掌。", officer="公吏",
    )
    staff(w, i, tp(w, "左、右金吾街仗司", "机构", "北宋"), current,
          main, "左、右金吾街仗司设置勾押官。", staff_type="公吏")
    rechain(w, eid, "整理勾押官五代职源与金吾街仗司职掌时间链。")
    w.commit()


def entry389():
    street_guard_clerk(
        389, "引驾官", "隶左、右金吾引驾仗司，承办大驾中引驾等仪仗事务",
        parent="guard",
    )


def entry390():
    i, main = 390, F[390]["text"]
    w = W(i)
    touched = set()
    eid = None
    for time, event, category, officer in (
        ("唐代", "押牙旗武职", "前代武职", "武职"),
        ("五代藩镇", "节度使自辟牙职，有左、右都押衙或都押衙", "前代牙职", "牙职"),
        ("北宋初（州郡胥府）", "州郡胥府中沿置左、右押衙、都押衙名目", "州郡胥吏", "胥吏"),
        ("宋代（金吾引驾仗司）", "左、右金吾街仗司吏职，负责卤簿中押金吾衙门旗", "金吾引驾仗司官吏", "公吏"),
    ):
        eid, node = exact_state(
            w, i, "都押衙", "官职", time, event, main,
            category, f"建立都押衙{time}节点。", officer=officer,
        )
    staff(w, i, tp(w, "左、右金吾引驾仗司", "机构", "北宋初"), node,
          main, "左、右金吾街仗司设置都押衙。", staff_type="公吏")
    rechain(w, eid, "整理都押衙从唐五代至宋金吾街仗司的完整时间链。")
    w.commit()


def entry391():
    street_guard_clerk(
        391, "勾画都知", "隶左、右金吾引驾仗司，承行大驾卤簿勘箭仪式等事务",
        parent="guard",
    )


def entry392():
    i, main = 392, F[392]["text"]
    w = W(i)
    touched = set()
    eid, tang = exact_state(
        w, i, "四色官", "官职", "唐代（三卫）",
        "三卫官下司阶、中候、执戈、执戟四官合称", main,
        "前代武职统称", "建立唐代四色官职源。", officer="武职统称",
    )
    touched.add(eid)
    for title in ("司阶", "中候", "执戈", "执戟"):
        meid, member = exact_state(
            w, i, title, "官职", "唐代（三卫）", "唐代四色官之一", main,
            "前代武职", f"建立{title}为唐代四色官实例。", officer="武职",
        )
        relation(w, i, tang, member, "统称与实例", main,
                 f"{title}为唐代四色官实例。")
        touched.add(meid)
    _, song = exact_state(
        w, i, "四色官", "官职", "宋代（金吾引驾仗司）",
        "沿用四色官之名但不除授唐代四官，成为金吾仗司公吏，排列卤簿仪仗并正衙喝唱",
        main, "金吾引驾仗司官吏", "补足宋代四色官性质与职掌。", officer="公吏",
    )
    _, six = exact_state(
        w, i, "四色官", "官职", "宋代大驾卤簿（年月未载）",
        "大驾卤簿编制六人", main,
        "金吾仪仗公吏", "建立大驾卤簿四色官定额。", officer="公吏",
    )
    _, reduced = exact_state(
        w, i, "四色官", "官职", "南宋孝宗朝",
        "由六人省为二人", main,
        "金吾仪仗公吏", "建立孝宗朝四色官减额节点。", officer="公吏",
    )
    parent = tp(w, "左、右金吾引驾仗司", "机构", "北宋初")
    staff(w, i, parent, song, main, "金吾仗司设置四色官。", staff_type="公吏")
    staff(w, i, parent, six, main, "大驾卤簿金吾四色官六人。", quota=6, staff_type="公吏")
    staff(w, i, tp(w, "左、右金吾引驾仗司", "机构", "南宋"), reduced,
          main, "孝宗朝四色官省为二人。", quota=2, staff_type="公吏")
    for eid in touched:
        rechain(w, eid, "整理四色官唐代职源、宋代性质与定额时间链。")
    w.commit()


def entry393():
    i, main = 393, F[393]["text"]
    w = W(i)
    eid, origin = exact_state(
        w, i, "穰稍官", "官职", "秦汉",
        "穰稍之名已见，穰稍为刻牺牛图形于槊首的仪仗", main,
        "仪仗职源", "建立穰稍官秦汉名源。", officer="仪仗官吏",
        note="本文中的牺槊为穰稍别称，不另建实体",
    )
    _, song = exact_state(
        w, i, "穰稍官", "官职", "宋代大驾卤簿（年月未载）",
        "押卤簿第一队穰稍队，穰稍十二并骑", main,
        "金吾仪仗公吏", "建立宋代穰稍官职掌与定额。", officer="仪从吏",
    )
    _, reduced = exact_state(
        w, i, "穰稍官", "官职", "南宋孝宗朝",
        "穰稍由十二省为八", main,
        "金吾仪仗公吏", "建立孝宗朝穰稍减额节点。", officer="仪从吏",
    )
    parent = tp(w, "左、右金吾引驾仗司", "机构", "北宋初")
    staff(w, i, parent, song, main, "金吾引驾仗司设置穰稍官。", quota=12, staff_type="仪从吏")
    staff(w, i, tp(w, "左、右金吾引驾仗司", "机构", "南宋"), reduced,
          main, "孝宗朝穰稍省为八。", quota=8, staff_type="仪从吏")
    rechain(w, eid, "整理穰稍官名源、职掌与定额时间链。")
    w.commit()


def entry394():
    street_guard_clerk(
        394, "知箭门仗官",
        "隶左、右金吾引驾仗司，保管勘箭契笥，车驾归阙时与禁中箭镞合契并应答",
        parent="guard",
    )


def entry395():
    i, main = 395, F[395]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "探头", "官职", "宋代（金吾引驾仗司）",
        "扈从仪仗中的引唱吏，先行引唱，由喝探兵士传呼使行人趋避",
        main, "金吾引驾仗司官吏", "补足探头引唱职掌。", officer="仪从吏",
    )
    staff(w, i, tp(w, "左、右金吾引驾仗司", "机构", "北宋初"), post,
          main, "金吾引驾仗司设置探头。", staff_type="仪从吏")
    drink_eid, drink = exact_state(
        w, i, "喝探", "官职", "宋初南郊（年月未载）",
        "南郊扈从仪仗使用喝探兵士二百六十人", main,
        "金吾仪仗兵士", "建立宋初南郊喝探兵额。", officer="兵士",
    )
    staff(w, i, tp(w, "左、右金吾引驾仗司", "机构", "北宋初"), drink,
          main, "宋初南郊使用喝探兵士二百六十人。", quota=260, staff_type="兵士")
    rechain(w, eid, "整理探头引唱职掌时间链。")
    rechain(w, drink_eid, "整理喝探宋初南郊兵额时间链。")
    w.commit()


def entry396():
    i, main = 396, F[396]["text"]
    w = W(i)
    eid, soldiers = exact_state(
        w, i, "喝探", "官职", "宋代（金吾引驾仗司）",
        "隶左、右金吾引驾仗司，在皇帝扈从仪仗中传呼喝道",
        main, "金吾仪仗兵士", "建立喝探隶属与职掌。", officer="兵士",
    )
    staff(w, i, tp(w, "左、右金吾引驾仗司", "机构", "北宋初"), soldiers,
          main, "金吾引驾仗司设置喝探兵士。", staff_type="兵士")
    rechain(w, eid, "整理喝探兵额与扈从仪仗职掌时间链。")
    w.commit()


def entry397():
    i, main = 397, F[397]["text"]
    history, duty, roster = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    touched = set()
    army_eid, tang = exact_state(
        w, i, "六军", "机构", "唐贞元间",
        "左、右羽林军、左、右龙武军、左、右神武军合称，各置统军一人",
        history, "禁军番号统称", "建立唐代六军体系。", "职源与沿革",
    )
    _, song_armies = exact_state(
        w, i, "六军", "机构", "宋代（六军仪仗司）",
        "沿用六军名目排办仪仗，不领常备军", roster,
        "仪仗军号统称", "建立宋代六军仪仗语境。", "编制",
    )
    office_eid, north = exact_state(
        w, i, "六军仪仗司", "机构", "北宋",
        "始见官署名，掌郊祀、朝会排办六军仪仗，无领兵职事",
        history, "宫廷仪仗机构", "建立北宋六军仪仗司始置与性质。", "职源与沿革",
    )
    cite(w, "Timepoints", north, i, duty, "补充郊祀、朝会仪仗职掌。", "职掌")
    reform = tp(w, "六军仪仗司", "机构", "北宋元丰五年")
    cite(w, "Timepoints", reform, i, main, "确认六军仪仗司隶卫尉寺。")
    relation(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), reform,
             "上下级机构", main, "六军仪仗司隶卫尉寺。")
    relation(w, i, north, song_armies, "上下级机构", roster,
             "六军仪仗司以六军名目排办仪仗。", "编制")
    touched.update((army_eid, office_eid))

    commander_eid, tang_commanders = exact_state(
        w, i, "六军统军", "官职", "唐贞元间",
        "唐贞元敕令六军各置统军一人", history,
        "唐代六军武官", "建立唐贞元间六军统军节点。", "职源与沿革",
        officer="统军",
    )
    staff(w, i, tang, tang_commanders, history,
          "唐贞元敕令六军各置统军一人。", "职源与沿革",
          quota=6, staff_type="统军")
    touched.add(commander_eid)

    six_members = []
    for pair, left, right in (
        ("左、右羽林军", "左羽林军", "右羽林军"),
        ("左、右龙武军", "左龙武军", "右龙武军"),
        ("左、右神武军", "左神武军", "右神武军"),
    ):
        peid, pair_node = exact_state(
            w, i, pair, "机构", "宋代（六军仪仗司）",
            "六军所指左右军号之一组", roster,
            "仪仗军号统称", f"建立{pair}的六军仪仗语境。", "编制",
        )
        touched.add(peid)
        for title in (left, right):
            eid, member = exact_state(
                w, i, title, "机构", "宋代（六军仪仗司）",
                "六军所指军号之一，无常备军，仅供仪仗", roster,
                "仪仗军号", f"建立{title}为六军实例。", "编制",
            )
            relation(w, i, pair_node, member, "统称与实例", roster,
                     f"{title}为{pair}实例。", "编制")
            relation(w, i, song_armies, member, "统称与实例", roster,
                     f"{title}为宋代六军实例。", "编制")
            six_members.append(member)
            touched.add(eid)

    for title, event, staff_type in (
        ("六军统军", "六军各置统军", "统军"),
        ("六军大将军", "六军各置大将军", "大将军"),
        ("六军将军", "六军各置将军", "将军"),
    ):
        eid, post = exact_state(
            w, i, title, "官职", "宋代（六军仪仗司）", event, roster,
            "六军武官", f"建立{title}。", "编制", officer=staff_type,
        )
        staff(w, i, song_armies, post, roster, f"宋代六军设置{title}名目。", "编制",
              staff_type=staff_type)
        touched.add(eid)
    clerk_eid, clerk_group = exact_state(
        w, i, "六军仪仗司属员", "官职", "宋代（六军仪仗司）",
        "都头、排仗官、通直官、大将军仪仗押当官、催驱官、警场、喝探、节级、探头等属员合称",
        roster, "六军仪仗司属员统称", "建立六军仪仗司属员统称。", "编制", officer="官兵统称",
    )
    staff(w, i, north, clerk_group, roster, "六军仪仗司设置各类属员。", "编制", staff_type="官兵")
    touched.add(clerk_eid)
    for title in (
        "都头", "排仗官", "通直官", "大将军仪仗押当官", "催驱官",
        "警场", "喝探", "节级", "探头",
    ):
        eid, post = exact_state(
            w, i, title, "官职", "宋代（六军仪仗司）",
            "六军仪仗司属员之一", roster,
            "六军仪仗司属员", f"建立{title}的六军仪仗司语境。", "编制", officer="官兵",
        )
        relation(w, i, clerk_group, post, "统称与实例", roster,
                 f"{title}为六军仪仗司属员实例。", "编制")
        touched.add(eid)
    judge = tp(w, "判左、右金吾街仗司", "官职", "北宋")
    staff(w, i, north, judge, roster, "宋初由判左右金吾街仗司官兼判六军仪仗司。",
          "编制", staff_type="兼判官")
    for eid in touched:
        rechain(w, eid, "整理六军、六军仪仗司、军号与属员完整时间链。")
    w.commit()


def entry398():
    i, main = 398, F[398]["text"]
    w = W(i)
    touched = set()
    feather_eid, han = exact_state(
        w, i, "羽林", "机构", "西汉武帝太初元年",
        "羽林之名始见", main,
        "禁军名号职源", "建立羽林名号西汉职源。",
    )
    pair_eid, tang = exact_state(
        w, i, "左、右羽林军", "机构", "唐龙朔二年",
        "左右羽林军之名始见", main,
        "禁军番号统称", "建立唐代左右羽林军名号。",
    )
    _, song = exact_state(
        w, i, "左、右羽林军", "机构", "宋代",
        "沿置局名而无常备军，应奉朝会、郊祀大礼并排办六军仪仗",
        main, "仪仗军号统称", "建立宋代左右羽林军性质与职掌。",
    )
    touched.update((feather_eid, pair_eid))
    relation(w, i, han, tang, "前后演变", main,
             "西汉羽林名号演为唐代左、右羽林军。")
    for title in ("左羽林军", "右羽林军"):
        node = tp(w, title, "机构", "宋代（六军仪仗司）")
        relation(w, i, song, node, "统称与实例", main,
                 f"{title}为宋代左、右羽林军实例。")
    for title, event, staff_type in (
        ("羽林军都头", "左、右羽林军仪仗属官", "都头"),
        ("羽林军排仗官", "左、右羽林军仪仗属官", "排仗官"),
    ):
        eid, post = exact_state(
            w, i, title, "官职", "宋代（六军仪仗司）", event, main,
            "羽林军仪仗官", f"建立{title}。", officer=staff_type,
        )
        staff(w, i, song, post, main, f"宋代左、右羽林军设置{title}名目。",
              staff_type=staff_type)
        touched.add(eid)
    for eid in touched:
        rechain(w, eid, "整理羽林名号、左右羽林军与仪仗属官时间链。")
    w.commit()


def entry399():
    i, main, aliases = 399, F[399]["text"], field(399, "简称")
    w = W(i)
    touched = set()
    eid, tang = exact_state(
        w, i, "左、右羽林军统军", "官职", "唐兴元元年正月二十九日",
        "始置左右羽林军统军", main,
        "羽林军武官统称", "建立唐代左右羽林军统军始置节点。", officer="统军",
    )
    _, song = exact_state(
        w, i, "左、右羽林军统军", "官职", "宋代（六军仪仗司）",
        "宋沿置，多为排办六军仪仗临时差摄，左右各一员",
        main, "羽林军仪仗武官统称", "建立宋代左右羽林军统军性质与定额。", officer="统军差摄",
    )
    staff(w, i, tp(w, "左、右羽林军", "机构", "宋代"), song,
          aliases, "宋代左、右羽林军统军二员。", "简称", quota=2, staff_type="统军差摄")
    touched.add(eid)
    for side in ("左", "右"):
        title = f"{side}羽林军统军"
        meid, post = exact_state(
            w, i, title, "官职", "宋代（六军仪仗司）",
            f"{side}羽林军统军，排办六军仪仗时临时差摄", aliases,
            "羽林军仪仗武官", f"建立{title}实例。", "简称", officer="统军差摄",
        )
        relation(w, i, song, post, "统称与实例", aliases,
                 f"{title}为左、右羽林军统军实例。", "简称")
        touched.add(meid)
    tang_generic = tp(w, "六军统军", "官职", "唐贞元间")
    relation(w, i, tang_generic, tang, "统称与实例", aliases,
             "唐代左、右羽林军统军为六军统军所指实例。", "简称")
    song_generic = tp(w, "六军统军", "官职", "宋代（六军仪仗司）")
    relation(w, i, song_generic, song, "统称与实例", aliases,
             "左、右羽林军统军为六军统军所指实例。", "简称")
    alias_note(w, i, song, aliases, "简称")
    for eid in touched:
        rechain(w, eid, "整理左右羽林军统军唐代始置与宋代差摄时间链。")
    w.commit()


def entry400():
    i, main = 400, F[400]["text"]
    w = W(i)
    eid, start = exact_state(
        w, i, "右羽林军上将军", "官职", "北宋咸平元年十一月十九日",
        "始置，无职事，为加官；六军本无上将军，此置为有司失误",
        main, "羽林军加官", "建立右羽林军上将军误置节点。", officer="加官",
    )
    _, abolished = exact_state(
        w, i, "右羽林军上将军", "官职", "北宋治平三年九月",
        "因言官论列而诏罢，后不复除", main,
        "羽林军加官", "建立治平三年罢置节点。", officer="加官",
    )
    staff(w, i, tp(w, "右羽林军", "机构", "宋代（六军仪仗司）"), start,
          main, "右羽林军上将军为无职事加官。", staff_type="加官")
    rechain(w, eid, "整理右羽林军上将军始置、误置性质与罢置时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(381, 401)] == [
        "右金吾街仗司", "左、右金吾街仗司", "判左、右金吾街仗司",
        "左、右金吾都监兼勾当街仗司事", "勾当左右金吾街仗、六军仪仗司事",
        "干办左、右金吾街仗司事", "孔目官", "勾押官", "引驾官",
        "都押衙", "勾画都知", "四色官", "穰稍官", "知箭门仗官",
        "探头", "喝探", "六军仪仗司", "左、右羽林军",
        "左、右羽林军统军", "右羽林军上将军",
    ]
    for i in range(381, 401):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
