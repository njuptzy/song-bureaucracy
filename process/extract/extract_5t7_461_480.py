#!/usr/bin/env python3
"""提取 chapter5t7 第461-480条：御辇院后续、车辂御马诸院与鸿胪寺。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_441_460 as previous


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


F = {i: load(i) for i in range(461, 481)}
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
    "汉代": -104, "北魏太和十五年": 491, "南朝梁天监七年": 508,
    "北齐": 550, "秦汉至北齐": 0,
    "宋初": 960.1, "北宋太祖朝": 960.2, "宋前期": 970,
    "北宋淳化元年四月": 990.29,
    "宋代（御辇院北宋编制）": 1050.1,
    "宋代（御辇院公吏）": 1050.2,
    "宋代（车辂院）": 1050.3,
    "宋代（鸿胪寺摄官）": 1050.4,
    "北宋元丰新制": 1080.1, "北宋元丰改制后": 1082.4,
    "北宋（改隶驾部年月未载）": 1090,
    "南宋建炎三年四月十三日": 1129.28,
    "南宋建炎三年六月": 1129.46,
    "南宋绍兴十二年十二月二十九日": 1142.99,
    "南宋绍兴十三年七月十二日": 1143.53,
    "南宋绍兴二十五年十月六日": 1155.77,
    "南宋绍兴二十五年十月二十三日": 1155.82,
    "南宋绍兴二十七年": 1157,
    "南宋淳熙十三年": 1186, "南宋淳熙十六年": 1189,
    "南宋淳熙、庆元间": 1190,
    "南宋孝宗以后": 1190.1, "南宋绍兴三十年": 1160,
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


def entry461():
    i, main, aliases = 461, F[461]["text"], field(461, "简称")
    w = W(i)
    touched = set()
    eid, north = exact_state(
        w, i, "下都营", "机构", "宋代（御辇院北宋编制）",
        "隶御辇院，给宫中及皇亲肩舆；设指挥使、军使、副兵马使及长行，北宋辇官五百七十八人，共分二营",
        main, "在京厢军", "补足下都营职掌、北宋定额与两营编制。",
    )
    relation(w, i, tp(w, "御辇院", "机构", "宋前期"), north,
             "上下级机构", main, "下都营隶御辇院。")
    _, south = exact_state(
        w, i, "下都营", "机构", "南宋绍兴十二年十二月二十九日",
        "辇官定以六百五十人为额", main,
        "在京厢军", "补足绍兴十二年下都营定额。",
    )
    touched.add(eid)
    for title, officer, quota in (
        ("下都指挥使", "指挥使", 1), ("下都军使", "军使", 4),
        ("下都副兵马使", "副兵马使", 3),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（御辇院北宋编制）",
            f"下都营所置{officer}，编制{quota}人", main,
            "下都营部辖官", f"建立{title}及定额。", officer=officer,
        )
        staff(w, i, north, post, main, f"下都营置{officer}{quota}人。",
              quota=quota, staff_type=officer)
        touched.add(seid)
    staff(w, i, south,
          tp(w, "下都辇官", "官职", "南宋绍兴十二年十二月二十九日"),
          main, "绍兴十二年下都辇官定额六百五十人。",
          quota=650, staff_type="辇官")
    alias_note(w, i, north, aliases, "简称")
    for x in touched:
        rechain(w, x, "整理下都营及部辖官完整时间链。")
    w.commit()


def entry462():
    i, main = 462, F[462]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "下都辇官长行", "官职", "宋代（御辇院北宋编制）",
        "下都辇官中有职名身份、资格深于一般辇官者，依次可迁补节级、将虞候等",
        main, "下都营应奉人", "建立下都辇官长行身份与迁补资格。", officer="长行",
    )
    staff(w, i, tp(w, "下都营", "机构", "宋代（御辇院北宋编制）"), post,
          main, "下都营设置下都辇官长行。", staff_type="辇官长行")
    rechain(w, eid, "整理下都辇官长行时间链。")
    w.commit()


def entry463():
    i, main, aliases = 463, F[463]["text"], field(463, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "下都辇官", "官职", "宋代（御辇院北宋编制）",
        "隶御辇院下都营，系军籍，搬运擎抬御前物色并给后宫及皇亲肩舆",
        main, "下都营应奉人", "补足下都辇官隶属、身份与职掌。", officer="应奉人",
    )
    staff(w, i, tp(w, "下都营", "机构", "宋代（御辇院北宋编制）"), post,
          main, "下都营由下都辇官应奉。", staff_type="系军籍应奉人")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理下都辇官时间链。")
    w.commit()


def entry464():
    i, main = 464, F[464]["text"]
    w = W(i)
    touched = set()
    eid, collective = exact_state(
        w, i, "辇官", "官职", "宋代（御辇院北宋编制）",
        "御辇院所属供御辇官、次供御辇官、下都辇官的通称",
        main, "御辇院应奉人通称", "建立辇官通称。", officer="应奉人通称",
    )
    touched.add(eid)
    for title in ("供御辇官", "次供御辇官", "下都辇官"):
        member_eid = w.find_entity(title, "官职")
        member = tp(w, title, "官职", "宋代（御辇院北宋编制）")
        relation(w, i, collective, member, "统称与实例", main,
                 f"{title}为辇官实例。")
        touched.add(member_eid)
    for x in touched:
        rechain(w, x, "整理辇官通称及三类实例时间链。")
    w.commit()


def entry465():
    i, main = 465, F[465]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "下都辇直", "官职", "宋代（御辇院北宋编制）",
        "下都营支差某处当直的辇官", main,
        "下都营应奉人", "建立下都辇直释义。", officer="当直辇官",
    )
    staff(w, i, tp(w, "下都营", "机构", "宋代（御辇院北宋编制）"), post,
          main, "下都辇直为下都营支差当直辇官。", staff_type="当直辇官")
    rechain(w, eid, "整理下都辇直时间链。")
    w.commit()


def entry466():
    i, main = 466, F[466]["text"]
    w = W(i)
    touched = set()
    eid, collective = exact_state(
        w, i, "御辇院公吏", "官职", "宋代（御辇院公吏）",
        "御辇院所属公吏合称，分专知官、副知官、押司、手分四等，依次递迁",
        main, "御辇院公吏合称", "建立御辇院公吏四等序列。", officer="公吏合称",
    )
    touched.add(eid)
    parent = tp(w, "御辇院", "机构", "宋前期")
    staff(w, i, parent, collective, main, "御辇院所属公吏合称。", staff_type="公吏")
    for title, event in (
        ("专知官", "御辇院公吏四等中最高等"),
        ("副知官", "御辇院公吏四等之一，位次于专知官"),
        ("押司", "御辇院公吏四等之一，位次于副知官"),
        ("手分", "御辇院公吏四等中初等"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（御辇院公吏）", event, main,
            "御辇院公吏", f"建立御辇院{title}节点。", officer="公吏",
        )
        relation(w, i, collective, post, "统称与实例", main,
                 f"{title}为御辇院公吏实例。")
        staff(w, i, parent, post, main, f"御辇院设置{title}。", staff_type="公吏")
        touched.add(seid)
    for x in touched:
        rechain(w, x, "整理御辇院公吏及四等实例完整时间链。")
    w.commit()


def entry467():
    i, main = 467, F[467]["text"]
    w = W(i)
    touched = set()
    eid, collective = exact_state(
        w, i, "专副", "官职", "宋代（御辇院公吏）",
        "主管官物的专知官、副知官连称", main,
        "公吏连称", "建立御辇院语境下专副释义。", officer="公吏连称",
    )
    touched.add(eid)
    for title in ("专知官", "副知官"):
        seid = w.find_entity(title, "官职")
        post = tp(w, title, "官职", "宋代（御辇院公吏）")
        relation(w, i, collective, post, "统称与实例", main,
                 f"{title}为专副所含职名。")
        touched.add(seid)
    for x in touched:
        rechain(w, x, "整理专副及专知官、副知官时间链。")
    w.commit()


def entry468():
    i, main, aliases = 468, F[468]["text"], field(468, "简称")
    w = W(i)
    touched = set()
    eid, office = exact_state(
        w, i, "车子院", "机构", "宋代（御辇院北宋编制）",
        "隶御辇院，分配宫中、诸王宫、王子院及公主宅驾车，兵士八十九人",
        main, "御辇院属局", "补足车子院隶属、职掌与定额。",
    )
    relation(w, i, tp(w, "御辇院", "机构", "宋前期"), office,
             "上下级机构", main, "车子院隶御辇院。")
    soldier_eid, soldier = exact_state(
        w, i, "车子院兵士", "官职", "宋代（御辇院北宋编制）",
        "掌禁中及诸宫院驾车，编制八十九人", main,
        "车子院兵士", "补足车子院兵士定额。", officer="兵士",
    )
    staff(w, i, office, soldier, main, "车子院置兵士八十九人。",
          quota=89, staff_type="兵士")
    alias_note(w, i, office, aliases, "简称")
    touched.update((eid, soldier_eid))
    for x in touched:
        rechain(w, x, "整理车子院及兵士时间链。")
    w.commit()


def entry469():
    i, main = 469, F[469]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别名"),
    )
    w = W(i)
    touched = set()
    eid, early = exact_state(
        w, i, "车辂院", "机构", "北宋太祖朝",
        "已置于东京升龙门东北，宋前期职事归群牧司",
        history, "车舆监当局", "建立车辂院北宋太祖朝见置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", early, i, duty, "补充宋前期职事归群牧司。", "职掌")
    herd_eid, herd = exact_state(
        w, i, "群牧司", "机构", "宋前期",
        "统领车辂院宋前期职事", duty,
        "马政机构", "据车辂院职事归属补足群牧司节点。", "职掌",
    )
    relation(w, i, herd, early, "上下级机构", duty,
             "宋前期车辂院职事归群牧司。", "职掌")
    _, reform = exact_state(
        w, i, "车辂院", "机构", "北宋元丰改制后",
        "元丰新制正名举职，掌皇帝礼仪所用大驾、法驾、小驾辇辂及奉引属车",
        history, "太仆寺属局", "补足元丰正名职掌节点。", "职源与沿革",
    )
    cite(w, "Timepoints", reform, i, duty, "补充元丰后车辂院职掌。", "职掌")
    relation(w, i, tp(w, "太仆寺", "机构", "北宋元丰五年五月一日"), reform,
             "上下级机构", main, "车辂院先隶太仆寺。")
    _, later = exact_state(
        w, i, "车辂院", "机构", "北宋（改隶驾部年月未载）",
        "由太仆寺改隶驾部，具体年月未载", main,
        "驾部属局", "补足车辂院后隶驾部节点。",
    )
    relation(w, i, tp(w, "驾部", "机构", "北宋（未载改隶具体年月）"), later,
             "上下级机构", main, "车辂院后隶驾部。")
    _, south = exact_state(
        w, i, "车辂院", "机构", "南宋",
        "沿置于皇宫嘉会门外", history,
        "驾部属局", "建立南宋车辂院沿置节点。", "职源与沿革",
    )
    touched.update((eid, herd_eid))
    for title in ("玉辂库", "金银车库", "金象辂库", "革辂、木辂库"):
        seid, store = exact_state(
            w, i, title, "机构", "北宋元丰改制后",
            "车辂院所辖四库之一", roster,
            "车辂院属库", f"建立车辂院所辖{title}。", "编制",
        )
        relation(w, i, reform, store, "上下级机构", roster,
                 f"{title}为车辂院下设库。", "编制")
        touched.add(seid)
    monitor_eid, monitor = exact_state(
        w, i, "监车辂院", "官职", "宋代（车辂院）",
        "车辂院监官，编制三员", roster,
        "车辂院监官", "建立监车辂院定额。", "编制", officer="监官",
    )
    staff(w, i, reform, monitor, roster, "车辂院置监官三员。", "编制",
          quota=3, staff_type="监官")
    touched.add(monitor_eid)
    alias_note(w, i, reform, aliases, "别名")
    for x in touched:
        rechain(w, x, "整理车辂院、群牧司、属库及监官完整时间链。")
    w.commit()


def entry470():
    i, main, aliases = 470, F[470]["text"], field(470, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "监车辂院门", "官职", "宋代（车辂院）",
        "掌纠察出入车辂院门人、物，由使臣或武人差充",
        main, "车辂院监当官", "建立监车辂院门职掌与任用。", officer="监当差遣",
    )
    staff(w, i, tp(w, "车辂院", "机构", "北宋元丰改制后"), post,
          main, "车辂院设置监门官。", staff_type="监门官")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理监车辂院门时间链。")
    w.commit()


def entry471():
    i, main = 471, F[471]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "御前马院", "机构", "南宋建炎三年六月",
        "始见置于临安皇城嘉会门内外，饲养御马、胡羊、驴并教习骑御马，奉朝会、典礼、行幸祗应",
        history, "御前马政监当局", "建立御前马院始见置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充御前马院职能。", "职能")
    _, seal = exact_state(
        w, i, "御前马院", "机构", "南宋绍兴十三年七月十二日",
        "铸行‘御马院之印’，差置手分四人、副知一名兼前行",
        aliases, "御前马政监当局", "建立绍兴十三年铸印与公吏节点。", "简称",
    )
    _, later = exact_state(
        w, i, "御前马院", "机构", "南宋孝宗以后",
        "孝宗以后诸朝沿置", history,
        "御前马政监当局", "建立孝宗以后沿置节点。", "职源与沿革",
    )
    alias_note(w, i, seal, aliases, "简称")
    touched.add(eid)
    for title, officer, quota, event in (
        ("御前马院教骏士", "教骏士", 250, "由骐骥教骏士拨充，喂养御马"),
        ("御前马院习马使效", "习马使效", 120, "由三衙或诸军将校及效用抽差，骑习御马"),
        ("御前马院手分", "手分", 4, "御前马院公吏"),
        ("御前马院副知兼前行", "副知兼前行", 1, "御前马院公吏"),
        ("御前马院库子", "库子", 2, "御前马院公吏"),
        ("御前马院脚夫", "脚夫", 58, "临安府每日差拨搬运草料"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "南宋建炎三年六月",
            f"{event}，编制{quota}人", roster,
            "御前马院属员", f"建立{title}定额。", "编制", officer=officer,
        )
        staff(w, i, start, post, roster, f"御前马院置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    for x in touched:
        rechain(w, x, "整理御前马院及属员完整时间链。")
    w.commit()


def entry472():
    i, main = 472, F[472]["text"]
    w = W(i)
    touched = set()
    eid, collective = exact_state(
        w, i, "御前马院习马使效", "官职", "南宋淳熙十六年",
        "御前马院骑习御马祗应的习马使臣与效用士合称，定额一百二十人；使臣罢军中兼职后可选择归军或留院",
        main, "御前马院属员合称", "建立习马使效释义、改革与定额。", officer="习马使效合称",
    )
    staff(w, i, tp(w, "御前马院", "机构", "南宋孝宗以后"), collective,
          main, "御前马院习马使效定额一百二十人。",
          quota=120, staff_type="习马使效")
    touched.add(eid)
    for title, event in (
        ("御前马院习马使臣", "诸军将校差在御前马院供骑习御马祗应"),
        ("御前马院效用士", "效用士在御前马院供骑习御马祗应"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "南宋淳熙十六年", event, main,
            "御前马院属员", f"建立{title}实例。", officer=title.removeprefix("御前马院"),
        )
        relation(w, i, collective, post, "统称与实例", main,
                 f"{title}为御前马院习马使效组成部分。")
        staff(w, i, tp(w, "御前马院", "机构", "南宋孝宗以后"), post,
              main, f"御前马院设置{title}。", staff_type=title.removeprefix("御前马院"))
        touched.add(seid)
    for x in touched:
        rechain(w, x, "整理御前马院习马使效及组成职名时间链。")
    w.commit()


def entry473():
    i, main = 473, F[473]["text"]
    history, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    touched = set()
    royal_eid, separated = exact_state(
        w, i, "御前马院", "机构", "南宋绍兴二十七年",
        "原寄养御前良马的职事分出，改由新建良马院专掌",
        duty, "御前马政监当局", "建立良马职事分出节点。", "职掌",
    )
    eid, start = exact_state(
        w, i, "良马院", "机构", "南宋绍兴二十七年",
        "见置于皇宫嘉会门外，与车辂院毗邻；专养御前良马，与御前马院分开",
        history, "御前马政监当局", "建立良马院见置与分职节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, main, "补充良马院位置。")
    cite(w, "Timepoints", start, i, duty, "补充良马院专掌良马职事。", "职掌")
    relation(w, i, separated, start, "前后演变", duty,
             "御前良马由御前马院寄养改由良马院专掌。", "职掌")
    _, quota = exact_state(
        w, i, "良马院", "机构", "南宋淳熙、庆元间",
        "养马军兵定额七百八十人", roster,
        "御前马政监当局", "建立良马院养马军兵定额。", "编制",
    )
    soldier_eid, soldier = exact_state(
        w, i, "良马院养马军兵", "官职", "南宋淳熙、庆元间",
        "良马院养马军兵，定额七百八十人", roster,
        "良马院属员", "建立良马院养马军兵定额。", "编制", officer="养马军兵",
    )
    staff(w, i, quota, soldier, roster, "良马院养马军兵定额七百八十人。", "编制",
          quota=780, staff_type="养马军兵")
    touched.update((royal_eid, eid, soldier_eid))
    for x in touched:
        rechain(w, x, "整理御前马院分职、良马院及养马军兵时间链。")
    w.commit()


def entry474():
    i, main = 474, F[474]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, han = exact_state(
        w, i, "鸿胪寺", "机构", "汉代",
        "汉武帝太初元年改大行令为大鸿胪，鸿胪之名始此",
        history, "宾客礼仪机构", "建立鸿胪名称源流节点。", "职源与沿革",
    )
    _, northern = exact_state(
        w, i, "鸿胪寺", "机构", "北齐",
        "始称鸿胪寺，为九寺之一", history,
        "宾客礼仪机构", "建立鸿胪寺名称始置节点。", "职源与沿革",
    )
    _, early = exact_state(
        w, i, "鸿胪寺", "机构", "宋前期",
        "北宋沿置，掌祭祀朝会陪位、陵庙祭享、丧葬监护仪仗与赙赠等",
        history, "九寺之一", "补足宋前期鸿胪寺职掌节点。", "职源与沿革",
    )
    cite(w, "Timepoints", early, i, duty, "补充宋前期职掌。", "职掌")
    _, reform = exact_state(
        w, i, "鸿胪寺", "机构", "北宋元丰新制",
        "正名举职，掌蕃国宾客、丧葬赙赠、后周陵庙祭享、柴氏袭封与道释籍帐等；分案三、设吏九",
        duty, "九寺之一", "建立元丰新制职掌节点。", "职掌",
    )
    _, merged = exact_state(
        w, i, "鸿胪寺", "机构", "南宋建炎三年四月十三日",
        "鸿胪寺并入礼部", history,
        "九寺之一", "建立建炎三年并入礼部节点。", "职源与沿革",
    )
    ritual_eid, ritual = exact_state(
        w, i, "礼部", "机构", "南宋建炎三年四月十三日",
        "接收鸿胪寺职事", history,
        "尚书省六部", "建立礼部接收鸿胪寺节点。", "职源与沿革",
    )
    relation(w, i, merged, ritual, "前后演变", history,
             "建炎三年鸿胪寺并入礼部。", "职源与沿革")
    _, restored = exact_state(
        w, i, "鸿胪寺", "机构", "南宋绍兴二十五年十月六日",
        "复置鸿胪寺", history,
        "九寺之一", "建立绍兴二十五年短暂复置节点。", "职源与沿革",
    )
    _, ended = exact_state(
        w, i, "鸿胪寺", "机构", "南宋绍兴二十五年十月二十三日",
        "复置十七日后又罢，此后不再置司", history,
        "九寺之一", "建立绍兴二十五年再罢节点。", "职源与沿革",
    )
    touched.update((eid, ritual_eid))
    for title in (
        "往来国信所", "都亭西驿", "礼宾院", "怀远驿", "中太一宫",
        "醴泉观", "万寿观", "奉慈宫", "集禧观", "崇真院", "资圣院",
        "建隆观提点所", "在京寺务司", "提点在京寺务司", "传法院",
        "左、右街僧录司", "同文馆", "管勾同文馆所",
    ):
        seid, child = exact_state(
            w, i, title, "机构", "北宋元丰新制",
            "元丰新制鸿胪寺所隶官司之一", roster,
            "鸿胪寺属司", f"建立鸿胪寺所隶{title}。", "编制",
        )
        relation(w, i, reform, child, "上下级机构", roster,
                 f"{title}隶鸿胪寺。", "编制")
        touched.add(seid)
    for title, officer, quota, parent, time in (
        ("鸿胪寺府史", "府史", 3, early, "宋前期"),
        ("鸿胪寺驱使官", "驱使官", 1, early, "宋前期"),
        ("摄鸿胪少卿", "临时摄官", None, early, "宋前期"),
        ("鸿胪寺吏", "吏", 9, reform, "北宋元丰新制"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", time,
            f"鸿胪寺所置{officer}" + (f"，编制{quota}人" if quota else "，临时差摄"),
            roster, "鸿胪寺属员", f"建立{title}编制。", "编制", officer=officer,
        )
        staff(w, i, parent, post, roster, f"鸿胪寺设置{officer}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    alias_note(w, i, reform, aliases, "简称与别名")
    for x in touched:
        rechain(w, x, "整理鸿胪寺、礼部承接及元丰属司完整时间链。")
    w.commit()


def entry475():
    i, main = 475, F[475]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "判鸿胪寺事", "官职", "宋前期",
        "因职事分散于国信所、诸驿与礼宾院，本寺止差朝官以上文官一员判事",
        main, "鸿胪寺长官差遣", "建立判鸿胪寺事任用、职掌与定额。", officer="朝官以上文官差遣",
    )
    staff(w, i, tp(w, "鸿胪寺", "机构", "宋前期"), post, main,
          "宋前期鸿胪寺置判寺事一员。", quota=1, staff_type="判寺事")
    rechain(w, eid, "整理判鸿胪寺事时间链。")
    w.commit()


def entry476():
    i, main = 476, F[476]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "摄鸿胪卿", "官职", "宋代（鸿胪寺摄官）",
        "接待外国使者时，为提高馆伴身份，令低阶官临时假借鸿胪卿品位行事",
        main, "鸿胪寺临时摄官", "建立摄鸿胪卿释义与馆伴用例。", officer="临时摄官",
    )
    staff(w, i, tp(w, "鸿胪寺", "机构", "宋前期"), post, main,
          "鸿胪寺接待外国使者时可临时授摄鸿胪卿。", staff_type="临时摄官")
    rechain(w, eid, "整理摄鸿胪卿时间链。")
    w.commit()


def entry477():
    i = 477
    origin, duty, grade, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, liang = exact_state(
        w, i, "鸿胪寺卿", "官职", "南朝梁天监七年",
        "鸿胪卿官名始置", origin, "鸿胪寺长官",
        "建立鸿胪卿官名源流节点。", "职源", officer="寺卿",
    )
    _, northern = exact_state(
        w, i, "鸿胪寺卿", "官职", "北齐",
        "鸿胪寺卿之名始置", origin, "鸿胪寺长官",
        "建立鸿胪寺卿名称始置节点。", "职源", officer="寺卿",
    )
    _, early = exact_state(
        w, i, "鸿胪寺卿", "官职", "宋前期",
        "北宋沿置但无实际职事", duty, "鸿胪寺长官",
        "建立宋前期无职事节点。", "职掌", officer="寺卿",
    )
    _, reform = exact_state(
        w, i, "鸿胪寺卿", "官职", "北宋元丰新制",
        "正名为鸿胪寺长官，总掌外国使者朝贡迎送赐宴、丧葬赙赠、祠庙宫观道释籍帐及后周陵庙祭享等",
        duty, "鸿胪寺长官", "建立元丰新制正名举职节点。", "职掌",
        officer="寺卿", grade="从四品",
    )
    cite(w, "Timepoints", reform, i, grade, "补充从四品品位。", "品位")
    staff(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制鸿胪寺卿一员。", "编制", quota=1, staff_type="寺卿")
    _, abolished = exact_state(
        w, i, "鸿胪寺卿", "官职", "南宋建炎三年四月十三日",
        "随鸿胪寺并入礼部而罢", origin, "鸿胪寺长官",
        "建立建炎三年罢官节点。", "职源", officer="寺卿",
    )
    alias_note(w, i, reform, aliases, "简称与别名")
    touched.add(eid)
    for x in touched:
        rechain(w, x, "整理鸿胪寺卿完整时间链。")
    w.commit()


def entry478():
    i = 478
    history, duty, grade, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    eid, wei = exact_state(
        w, i, "鸿胪寺少卿", "官职", "北魏太和十五年",
        "始设大鸿胪少卿", history, "鸿胪寺副长官",
        "建立鸿胪少卿源流节点。", "职源与沿革", officer="少卿",
    )
    _, northern = exact_state(
        w, i, "鸿胪寺少卿", "官职", "北齐",
        "鸿胪寺少卿始置", history, "鸿胪寺副长官",
        "建立鸿胪寺少卿名称始置节点。", "职源与沿革", officer="少卿",
    )
    _, early = exact_state(
        w, i, "鸿胪寺少卿", "官职", "北宋前期",
        "虽沿置而罕除", history, "鸿胪寺副长官",
        "建立北宋前期罕除节点。", "职源与沿革", officer="少卿", grade="从四品下",
    )
    _, revival = exact_state(
        w, i, "鸿胪寺少卿", "官职", "北宋淳化元年四月",
        "为振起寺监副贰曾授人", history, "鸿胪寺副长官",
        "建立淳化元年授官节点。", "职源与沿革", officer="少卿",
    )
    _, reform = exact_state(
        w, i, "鸿胪寺少卿", "官职", "北宋元丰新制",
        "正名为寺卿副贰，佐卿领寺事，正六品，编制一员",
        duty, "鸿胪寺副长官", "建立元丰新制职掌、品位与定额。", "职掌",
        officer="少卿", grade="正六品",
    )
    cite(w, "Timepoints", reform, i, grade, "补充元丰后正六品及班序。", "品位")
    staff(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制鸿胪寺少卿一员。", "编制", quota=1, staff_type="少卿")
    _, abolished = exact_state(
        w, i, "鸿胪寺少卿", "官职", "南宋建炎三年四月十三日",
        "随鸿胪寺并入礼部而罢", history, "鸿胪寺副长官",
        "建立建炎三年罢官节点。", "职源与沿革", officer="少卿",
    )
    _, restored = exact_state(
        w, i, "鸿胪寺少卿", "官职", "南宋绍兴二十五年十月六日",
        "复置一员", history, "鸿胪寺副长官",
        "建立绍兴二十五年复置节点。", "职源与沿革", officer="少卿",
    )
    staff(w, i, tp(w, "鸿胪寺", "机构", "南宋绍兴二十五年十月六日"), restored,
          roster, "绍兴二十五年复置鸿胪寺少卿一员。", "编制",
          quota=1, staff_type="少卿")
    _, ended = exact_state(
        w, i, "鸿胪寺少卿", "官职", "南宋绍兴二十五年十月二十三日",
        "随鸿胪寺再次罢废", history, "鸿胪寺副长官",
        "建立绍兴二十五年再罢节点。", "职源与沿革", officer="少卿",
    )
    alias_note(w, i, reform, aliases, "简称")
    rechain(w, eid, "整理鸿胪寺少卿完整时间链。")
    w.commit()


def entry479():
    i = 479
    history, duty, grade, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    eid, origin = exact_state(
        w, i, "鸿胪寺丞", "官职", "秦汉至北齐",
        "由秦典客丞、西汉大行治礼丞、北魏大鸿胪卿丞演变，北齐称鸿胪寺丞",
        history, "鸿胪寺属官", "建立鸿胪寺丞前代源流节点。", "职源与沿革", officer="寺丞",
    )
    _, early = exact_state(
        w, i, "鸿胪寺丞", "官职", "宋前期",
        "北宋沿置，无职事，或作文臣迁转官阶",
        duty, "阶官兼职事官", "补足宋前期阶官性质。", "职掌",
        officer="寺丞", grade="从六品下",
    )
    cite(w, "Timepoints", early, i, grade, "补充宋初依唐制从六品下。", "品位")
    _, reform = exact_state(
        w, i, "鸿胪寺丞", "官职", "北宋元丰新制",
        "正名后参领本寺事，正八品，编制一人",
        duty, "鸿胪寺属官", "建立元丰新制职掌、品位与定额。", "职掌",
        officer="寺丞", grade="正八品",
    )
    cite(w, "Timepoints", reform, i, grade, "补充元丰后正八品及班序。", "品位")
    staff(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制鸿胪寺丞一人。", "编制", quota=1, staff_type="寺丞")
    _, abolished = exact_state(
        w, i, "鸿胪寺丞", "官职", "南宋建炎三年四月十三日",
        "随鸿胪寺并入礼部而罢", history, "鸿胪寺属官",
        "建立建炎三年罢官节点。", "职源与沿革", officer="寺丞",
    )
    alias_note(w, i, reform, aliases, "简称")
    rechain(w, eid, "整理鸿胪寺丞完整时间链。")
    w.commit()


def entry480():
    i = 480
    history, duty, grade, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    eid, han = exact_state(
        w, i, "鸿胪寺主簿", "官职", "汉代",
        "汉朝已有鸿胪主簿", history, "鸿胪寺属官",
        "建立鸿胪主簿源流节点。", "职源与沿革", officer="主簿",
    )
    _, northern = exact_state(
        w, i, "鸿胪寺主簿", "官职", "北齐",
        "鸿胪寺主簿始见", history, "鸿胪寺属官",
        "建立鸿胪寺主簿名称始见节点。", "职源与沿革", officer="主簿",
    )
    _, early = exact_state(
        w, i, "鸿胪寺主簿", "官职", "宋前期",
        "北宋沿置", history, "鸿胪寺属官",
        "建立北宋沿置节点。", "职源与沿革", officer="主簿",
    )
    _, reform = exact_state(
        w, i, "鸿胪寺主簿", "官职", "北宋元丰新制",
        "勾考本寺簿书，不得签书公事，从八品，编制一人",
        duty, "鸿胪寺属官", "建立元丰新制职掌、品位与定额。", "职掌",
        officer="主簿", grade="从八品",
    )
    cite(w, "Timepoints", reform, i, grade, "补充从八品及班序。", "品位")
    staff(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), reform, roster,
          "元丰新制鸿胪寺主簿一人。", "编制", quota=1, staff_type="主簿")
    _, abolished = exact_state(
        w, i, "鸿胪寺主簿", "官职", "南宋建炎三年四月十三日",
        "随鸿胪寺并入礼部而罢", history, "鸿胪寺属官",
        "建立建炎三年罢官节点。", "职源与沿革", officer="主簿",
    )
    alias_note(w, i, reform, aliases, "简称")
    rechain(w, eid, "整理鸿胪寺主簿完整时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(461, 481)] == [
        "下都营", "下都辇官长行", "下都辇官", "辇官", "下都辇直",
        "御辇院公吏", "专副", "车子院", "车辂院", "监车辂院门",
        "御前马院", "御前马院习马使效", "良马院", "鸿胪寺",
        "判鸿胪寺事", "摄鸿胪卿", "鸿胪寺卿", "鸿胪寺少卿",
        "鸿胪寺丞", "鸿胪寺主簿",
    ]
    for i in range(461, 481):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
