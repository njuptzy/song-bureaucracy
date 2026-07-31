#!/usr/bin/env python3
"""提取 chapter5t7 第241-260条：敦宗院官属、玉牒所与光禄寺。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_221_240 as previous


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


F = {i: load(i) for i in range(241, 261)}
previous.F = F
previous.ENTRY_DB = ENTRY_DB

W = previous.W
Q = previous.Q
field = previous.field
C = previous.C
cite = previous.cite
state = previous.state
relation = previous.relation
staff = previous.staff
tp = previous.tp
alias_note = previous.alias_note


TIME_HINTS = {
    "秦": -221, "西汉武帝太初元年": -104, "东汉": 25,
    "北齐": 550, "唐朝太和二年六月": 828.45,
    "宋代": 960, "北宋": 960, "北宋沿置": 960.1,
    "宋前期": 970, "北宋太宗至道元年": 995,
    "北宋大中祥符八年": 1015, "北宋大中祥符九年后": 1016,
    "北宋元丰新制": 1080, "北宋元丰五年": 1082,
    "北宋大观二年八月二十二日": 1108.64,
    "北宋徽宗朝": 1101,
    "南宋": 1127, "南宋初": 1127.1, "南宋中兴以来": 1127.2,
    "南宋建炎三年四月十三日": 1129.29,
    "南宋裁减后": 1130,
    "南宋绍兴十二年五月九日": 1142.36,
    "南宋绍兴十二年以后": 1142.4,
    "南宋绍兴二十三年二月十七日": 1153.13,
    "南宋乾道二年": 1166,
    "南宋乾道八年六月十六日": 1172.46,
    "南宋淳熙四年七月三十日": 1177.58,
    "南宋淳熙十六年二月": 1189.12,
    "南宋隆兴元年七月二十六日": 1163.56,
    "南宋乾道八年六月十六日（玉牒殿）": 1172.461,
    "南宋淳熙四年七月三十日（玉牒殿）": 1177.581,
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


def entity_id(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def entry241():
    i, main, aliases = 241, F[241]["text"], field(241, "简称与别名")
    w = W(i)
    eid, generic = state(
        w, i, "两京敦宗院", "机构", "北宋",
        "西京敦宗院、南京敦宗院合称", main,
        "机构统称", "建立两京敦宗院统称。",
    )
    relation(w, i, generic, tp(w, "西京敦宗院", "机构", "北宋崇宁元年十一月十二日"), "统称与实例", main, "西京敦宗院为两京敦宗院实例。")
    relation(w, i, generic, tp(w, "南京敦宗院", "机构", "北宋崇宁元年十一月十二日"), "统称与实例", main, "南京敦宗院为两京敦宗院实例。")
    alias_note(w, i, generic, aliases, "简称与别名")
    rechain(w, eid, "确认两京敦宗院统称时间链。")
    w.commit()


def entry242():
    i, main = 242, F[242]["text"]
    w = W(i)
    eid, start = state(
        w, i, "保州敦宗院", "机构", "北宋大观二年八月二十二日",
        "创置于保州，收皇族未官者三十余人", main,
        "敦宗院实例", "建立保州敦宗院创置节点。",
    )
    _, end = state(
        w, i, "保州敦宗院", "机构", "南宋",
        "已不存", main, "敦宗院实例", "记录保州敦宗院南宋已不存。",
    )
    relation(w, i, tp(w, "敦宗院", "机构", "北宋崇宁元年十一月十二日"), start, "统称与实例", main, "保州敦宗院为宋代第三处敦宗院实例。")
    rechain(w, eid, "连接保州敦宗院创置与南宋不存节点。")
    w.commit()


def entry243():
    i, main = 243, F[243]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别名"),
    )
    w = W(i)
    eid, north = state(
        w, i, "管勾敦宗院", "官职", "北宋崇宁元年十一月十二日",
        "随西京、南京敦宗院始置，文武官各一员", history,
        "敦宗院官", "建立管勾敦宗院始置节点。", "职源与沿革",
        officer="职事官",
    )
    cite(w, "Timepoints", north, i, duty, "记录管勾敦宗院职掌。", "职掌")
    cite(w, "Timepoints", north, i, roster, "记录文、武官各一员，合计二人。", "编制")
    staff(w, i, tp(w, "敦宗院", "机构", "北宋崇宁元年十一月十二日"), north, roster, "每处敦宗院置管勾官二人，文武各一。", "编制", quota=2)
    new_eid, south = state(
        w, i, "主管敦宗院", "官职", "南宋",
        "管勾敦宗院改称主管敦宗院", aliases,
        "敦宗院官", "南宋名称发生正式改称，建立主管敦宗院。", "别名",
        officer="职事官",
    )
    relation(w, i, north, south, "前后演变", history, "南宋改管勾敦宗院为主管敦宗院。", "职源与沿革")
    staff(w, i, tp(w, "敦宗院", "机构", "南宋初"), south, aliases, "南宋敦宗院置主管官二员。", "别名", quota=2)
    for x in (eid, new_eid):
        rechain(w, x, "整理管勾、主管敦宗院名称演变时间链。")
    w.commit()


def entry244():
    i, main, aliases = 244, F[244]["text"], field(244, "别称")
    w = W(i)
    eid, north = state(
        w, i, "监敦宗院门", "官职", "北宋",
        "两京敦宗院各置二员，讥察宗室出入", main,
        "敦宗院官", "建立监敦宗院门北宋编制与职掌。", officer="职事官",
    )
    _, reduced = state(
        w, i, "监敦宗院门", "官职", "南宋裁减后",
        "由二员裁减后留一员", aliases,
        "敦宗院官", "记录南外敦宗院监门官裁减后的编制。", "别称",
        officer="职事官",
    )
    staff(w, i, tp(w, "敦宗院", "机构", "北宋崇宁元年十一月十二日"), north, main, "两京敦宗院各置监门官二员。", quota=2)
    staff(w, i, tp(w, "敦宗院", "机构", "南宋初"), reduced, aliases, "裁减后监门官留一员。", "别称", quota=1)
    alias_note(w, i, north, aliases, "别称")
    rechain(w, eid, "连接监敦宗院门北宋二员与南宋裁减节点。")
    w.commit()


def entry245():
    i, main = 245, F[245]["text"]
    w = W(i)
    eid, clerk = state(
        w, i, "敦宗院监门军典", "官职", "宋代",
        "在敦宗院监门官下供给使", main,
        "敦宗院吏", "按所隶机构消歧，补足敦宗院监门军典职掌。", officer="吏",
    )
    staff(w, i, tp(w, "敦宗院", "机构", "北宋崇宁元年十一月十二日"), clerk, main, "敦宗院监门官下置军典一名。", quota=1, staff_type="吏")
    rechain(w, eid, "确认敦宗院监门军典时间链。")
    w.commit()


def entry246():
    i, main, aliases = 246, F[246]["text"], field(246, "别称")
    w = W(i)
    eid, post = state(
        w, i, "敦宗院教授", "官职", "宋代",
        "两京敦宗院各置一员，教导本院大小学宗学生", main,
        "宗学官", "补足敦宗院教授定额与职掌。", officer="职事官",
    )
    staff(w, i, tp(w, "敦宗院", "机构", "北宋崇宁元年十一月十二日"), post, main, "两京敦宗院各置教授一员。", quota=1)
    alias_note(w, i, post, aliases, "别称")
    rechain(w, eid, "确认敦宗院教授时间链。")
    w.commit()


def entry247():
    i, main = 247, F[247]["text"]
    w = W(i)
    eid, post = state(
        w, i, "都尊长", "官职", "宋代",
        "教诱同宗、留心学校，检察冒宗请给并防举宗子犯法", main,
        "敦宗院宗官", "建立都尊长归隶、资格与职掌。", officer="宗官",
    )
    staff(w, i, tp(w, "敦宗院", "机构", "南宋初"), post, main, "都尊长隶敦宗院。", staff_type="宗官")
    rechain(w, eid, "确认都尊长时间链。")
    w.commit()


def entry248():
    i, main = 248, F[248]["text"]
    w = W(i)
    eid, post = state(
        w, i, "尊长", "官职", "宋代",
        "州郡有宗室处置以训治在外宗子；诸王宫院每位置一人率教戒", main,
        "宗官", "建立尊长的两类设置场景与职掌。", officer="宗官",
    )
    rechain(w, eid, "确认尊长时间链。")
    w.commit()


def entry249():
    i, main = 249, F[249]["text"]
    history, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    office_title = "宗正寺玉牒所"
    office_eid = entity_id(w, office_title, "机构")
    nodes = {}
    for time, event in (
        ("北宋太宗至道元年", "北宋修玉牒始设官置局"),
        ("北宋大中祥符八年", "建玉牒殿、属籍堂"),
        ("北宋徽宗朝", "改由宰臣提举，时称玉牒局"),
        ("南宋初", "停罢"),
        ("南宋绍兴十二年五月九日", "复置，以宰辅提举，与宗正寺实为同一官府"),
    ):
        _, nodes[time] = state(
            w, i, office_title, "机构", time, event, history,
            "宗正寺所属机构", f"据专条建立玉牒所{time}节点。", "职源与沿革",
        )
    cite(w, "Timepoints", nodes["北宋太宗至道元年"], i, duty, "记录玉牒所编修历代皇帝玉牒的职掌。", "职掌")
    relation(w, i, tp(w, "宗正寺", "机构", "宋前期"), nodes["北宋太宗至道元年"], "上下级机构", main, "北宋玉牒所隶宗正寺。")
    cite(w, "Timepoints", nodes["北宋徽宗朝"], i, roster, "‘玉牒局’为徽宗朝时期称谓，不另建实体。", "编制", note="时期别称不另建实体")
    temple_eid, temple_tang = state(
        w, i, "宗正寺", "机构", "唐朝太和二年六月",
        "已置修玉牒官隶宗正寺", history,
        "宗室管理机构", "为唐代修玉牒官建立宗正寺同期节点。", "职源与沿革",
    )
    touched = {office_eid, temple_eid}
    post_specs = (
        ("宗正寺修玉牒官", "唐朝太和二年六月", "始置并隶宗正寺", "兼官", None, temple_tang, history, "职源与沿革"),
        ("宗正寺修玉牒官", "北宋大中祥符九年后", "设一至二员", "兼官", 2, nodes["北宋大中祥符八年"], roster, "编制"),
        ("宗正寺修玉牒官", "北宋元丰新制", "宗正寺官均预纂修", "兼官", None, tp(w, "宗正寺玉牒所", "机构", "北宋元丰新制"), roster, "编制"),
        ("宗正寺修玉牒官", "南宋绍兴十二年五月九日", "侍从官一员兼修玉牒官", "兼官", 1, nodes["南宋绍兴十二年五月九日"], roster, "编制"),
        ("提举编修玉牒", "北宋徽宗朝", "宰臣提举玉牒所", "兼官", 1, nodes["北宋徽宗朝"], roster, "编制"),
        ("提举编修玉牒", "南宋绍兴十二年五月九日", "以宰辅一员或二员提举", "兼官", 2, nodes["南宋绍兴十二年五月九日"], roster, "编制"),
        ("玉牒所检讨官", "南宋绍兴十二年五月九日", "以它官兼，置废不常", "兼官", None, nodes["南宋绍兴十二年五月九日"], roster, "编制"),
        ("玉牒所点检文字", "南宋绍兴十二年五月九日", "玉牒所吏人之一", "吏", None, nodes["南宋绍兴十二年五月九日"], roster, "编制"),
    )
    for title, time, event, officer, quota, parent, quote, field_name in post_specs:
        eid, post = state(
            w, i, title, "官职", time, event, quote,
            "玉牒所官吏", f"据玉牒所材料建立{title}{time}节点。", field_name,
            officer=officer,
        )
        staff(w, i, parent, post, quote, f"玉牒所或宗正寺置{title}。", field_name, quota=quota, staff_type=officer)
        touched.add(eid)
    for x in touched:
        rechain(w, x, "整理玉牒所及其官吏时间链。")
    w.commit()


def entry250():
    i, main, aliases = 250, F[250]["text"], field(250, "简称")
    w = W(i)
    eid = entity_id(w, "提举编修玉牒", "官职")
    for time in ("北宋徽宗朝", "南宋绍兴十二年五月九日"):
        tid = tp(w, "提举编修玉牒", "官职", time)
        cite(w, "Timepoints", tid, i, main, "补充提举编修玉牒由宰执兼、总领修玉牒事。")
    alias_note(w, i, tp(w, "提举编修玉牒", "官职", "南宋绍兴十二年五月九日"), aliases, "简称")
    rechain(w, eid, "确认提举编修玉牒时间链。")
    w.commit()


def entry251():
    i, main = 251, F[251]["text"]
    w = W(i)
    eid, tid = state(
        w, i, "提举编修玉牒", "官职", "南宋乾道二年",
        "汤思退因避父名‘举’，挂衔特改称‘提领编修玉牒’", main,
        "玉牒所提举官", "避父讳形成的个人挂衔称谓记入原官时间点，不另建实体。",
        officer="兼官", note="避父讳称谓不另建实体",
    )
    rechain(w, eid, "将乾道二年避讳挂衔节点纳入提举编修玉牒时间链。")
    w.commit()


def entry252():
    i, main, aliases = 252, F[252]["text"], field(252, "简称")
    w = W(i)
    title = "宗正寺修玉牒官"
    eid, north = state(
        w, i, title, "官职", "宋前期",
        "无专官，侍从官兼差，宗正卿少以下悉与修纂", main,
        "玉牒所官", "沿用既有消歧实体，补足北宋兼差方式。", officer="兼官",
    )
    staff(w, i, tp(w, "宗正寺玉牒所", "机构", "北宋太宗至道元年"), north, main, "修玉牒官参与玉牒所修纂。", staff_type="兼官")
    alias_note(w, i, north, aliases, "简称")
    rechain(w, eid, "整理宗正寺修玉牒官时间链。")
    w.commit()


def entry253():
    i, main, aliases = 253, F[253]["text"], field(253, "简称")
    w = W(i)
    eid, post = state(
        w, i, "玉牒所检讨官", "官职", "南宋绍兴十二年五月九日",
        "多以侍从官兼，参预修皇帝玉牒，置废不常", main,
        "玉牒所官", "补足玉牒所检讨官任用、职掌与置废。", officer="兼官",
    )
    staff(w, i, tp(w, "宗正寺玉牒所", "机构", "南宋绍兴十二年五月九日"), post, main, "玉牒所置检讨官，置废不常。", staff_type="兼官")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "确认玉牒所检讨官时间链。")
    w.commit()


def entry254():
    i, main = 254, F[254]["text"]
    w = W(i)
    hall_eid, hall = state(
        w, i, "玉牒所玉牒殿", "机构", "北宋大中祥符八年",
        "建殿珍藏历朝皇帝玉牒", main,
        "玉牒所所属机构", "建立玉牒殿及珍藏职能。",
    )
    relation(w, i, tp(w, "宗正寺玉牒所", "机构", "北宋大中祥符八年"), hall, "上下级机构", main, "玉牒殿隶玉牒所。")
    post_eid, post = state(
        w, i, "玉牒所玉牒殿主管香火", "官职", "北宋大中祥符八年",
        "由内侍充，专看管玉牒殿并行香尊奉", main,
        "玉牒殿官", "建立玉牒殿主管香火。", officer="内侍差遣",
    )
    staff(w, i, hall, post, main, "玉牒殿置主管香火官。", staff_type="内侍差遣")
    for x in (hall_eid, post_eid):
        rechain(w, x, "整理玉牒殿及主管香火时间链。")
    w.commit()


def entry255():
    i, main = 255, F[255]["text"]
    w = W(i)
    hall_eid, hall = state(
        w, i, "玉牒所玉牒殿", "机构", "南宋乾道八年六月十六日",
        "张官置吏，增设专知、副知", main,
        "玉牒所所属机构", "建立玉牒殿乾道八年张官置吏节点。",
    )
    old = tp(w, "玉牒所玉牒殿主管香火", "官职", "北宋大中祥符八年")
    post_eid, post = state(
        w, i, "干办玉牒所玉牒殿", "官职", "南宋乾道八年六月十六日",
        "由主管香火改名，内侍官三人、武官一人差充", main,
        "玉牒殿官", "建立干办玉牒所玉牒殿改名节点。", officer="内侍官、武官",
    )
    relation(w, i, old, post, "前后演变", main, "乾道八年主管香火改名干办玉牒所玉牒殿。")
    staff(w, i, hall, post, main, "干办玉牒所玉牒殿由内侍三人、武官一人差充。", quota=4, staff_type="内侍官、武官")
    for x in (hall_eid, post_eid):
        rechain(w, x, "整理玉牒殿乾道八年改名与编制时间链。")
    w.commit()


def entry256():
    i, main = 256, F[256]["text"]
    w = W(i)
    time = "南宋乾道八年六月十六日（玉牒殿）"
    touched = set()
    generic_eid, generic = state(
        w, i, "专副", "官职", time,
        "玉牒殿专知官、副知的连称", main,
        "玉牒殿吏人统称", "为既有通用吏称建立玉牒殿语境节点。", officer="吏称",
    )
    touched.add(generic_eid)
    hall = tp(w, "玉牒所玉牒殿", "机构", "南宋乾道八年六月十六日")
    for title in ("专知官", "副知"):
        eid, post = state(
            w, i, title, "官职", time,
            "玉牒殿管官物吏人，专知位在副知前", main,
            "玉牒殿吏", f"为既有通用吏名建立玉牒殿语境节点：{title}。", officer="吏",
        )
        relation(w, i, generic, post, "统称与实例", main, f"{title}为玉牒殿专副实例。")
        staff(w, i, hall, post, main, f"玉牒殿置{title}一员。", quota=1, staff_type="吏")
        touched.add(eid)
    for x in touched:
        rechain(w, x, "整理专副、专知官、副知的玉牒殿语境时间链。")
    w.commit()


def entry257():
    i, main = 257, F[257]["text"]
    w = W(i)
    time = "南宋淳熙四年七月三十日（玉牒殿）"
    eid, post = state(
        w, i, "库子", "官职", time,
        "增设四名，轮流宿直玉牒殿并看守殿内官物", main,
        "玉牒殿吏", "为既有库子实体建立玉牒殿语境节点。", officer="吏",
    )
    hall_eid, hall = state(
        w, i, "玉牒所玉牒殿", "机构", "南宋淳熙四年七月三十日",
        "增设库子四名轮流宿直看守", main,
        "玉牒所所属机构", "建立玉牒殿淳熙四年增置库子节点。",
    )
    staff(w, i, hall, post, main, "玉牒殿增设库子四名。", quota=4, staff_type="背印亲事官、皇城司亲事官")
    rechain(w, eid, "将玉牒殿库子节点纳入库子完整时间链。")
    rechain(w, hall_eid, "将淳熙四年增置库子纳入玉牒殿时间链。")
    w.commit()


def entry258():
    i, main = 258, F[258]["text"]
    w = W(i)
    eid, generic = state(
        w, i, "宗官", "官职", "宋代",
        "宗正寺、大宗正司及西南两外宗正司等宗室管理机构属官的泛称", main,
        "官职统称", "建立宗官泛称。",
    )
    instances = (
        ("宗正寺卿", "宋前期"),
        ("判大宗正司事", "南宋"),
        ("知南外宗正事", "南宋"),
        ("知西外宗正事", "南宋"),
    )
    for title, time in instances:
        relation(w, i, generic, tp(w, title, "官职", time), "统称与实例", main, f"{title}为宗官实例。")
    rechain(w, eid, "确认宗官统称时间链。")
    w.commit()


def entry259():
    i, main = 259, F[259]["text"]
    w = W(i)
    eid = entity_id(w, "宗官", "官职")
    generic = tp(w, "宗官", "官职", "宋代")
    cite(w, "Timepoints", generic, i, main, "‘宗职’为宗官别称，不另建实体。", note="纯别称不另建实体")
    rechain(w, eid, "确认宗官别称证据所在时间链。")
    w.commit()


def canonicalize_guanglu_merge(w, quotation):
    eid = entity_id(w, "光禄寺", "机构")
    broad = w.find_timepoint(eid, "南宋隆兴元年七月")
    exact = w.find_timepoint(eid, "南宋隆兴元年七月二十六日")
    if broad and not exact:
        w.conn.execute(
            "update Timepoints set time=?,event=?,quotation=?,attr_category=? where id=?",
            ("南宋隆兴元年七月二十六日", "并入太常寺", quotation, "寺监机构", broad),
        )
        w._br("Timepoints", broad, "据光禄寺专条将隆兴元年七月并省节点规范到二十六日。")
        exact = broad
    assert exact
    return eid, exact


def entry260():
    i, main = 260, F[260]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    lang_eid, lang = state(
        w, i, "郎中令", "机构", "秦", "掌宫殿掖门户", history,
        "宫廷事务机构", "建立光禄寺秦代前身郎中令。", "职源与沿革",
    )
    xun_eid, xun = state(
        w, i, "光禄勋", "机构", "西汉武帝太初元年",
        "郎中令改名光禄勋，掌宫殿掖门户", history,
        "宫廷事务机构", "建立西汉光禄勋改名节点。", "职源与沿革",
    )
    _, eastern = state(
        w, i, "光禄勋", "机构", "东汉", "增掌郊祀三献", history,
        "宫廷事务机构", "建立东汉光禄勋职掌变化。", "职源与沿革",
    )
    guanglu_eid, north_qi = state(
        w, i, "光禄寺", "机构", "北齐", "始有光禄寺之称", history,
        "寺监机构", "建立光禄寺北齐始称节点。", "职源与沿革",
    )
    _, north_song = state(
        w, i, "光禄寺", "机构", "北宋沿置", "北宋沿置", history,
        "寺监机构", "建立光禄寺北宋沿置节点。", "职源与沿革",
    )
    _, reform = state(
        w, i, "光禄寺", "机构", "北宋元丰五年",
        "正名后扩大职掌，统掌或监视朝会宴享酒醴膳羞及禁令格式", duty,
        "寺监机构", "建立元丰五年正名及职掌扩大节点。", "职掌",
    )
    cite(w, "Timepoints", reform, i, roster, "元丰改制后分案五；案名未载，不另建实体。", "编制", note="分案五但无案名")
    _, merged_rites = state(
        w, i, "光禄寺", "机构", "南宋建炎三年四月十三日",
        "并归礼部", history, "寺监机构", "建立建炎三年并归礼部节点。", "职源与沿革",
    )
    _, restored = state(
        w, i, "光禄寺", "机构", "南宋绍兴二十三年二月十七日",
        "复置", history, "寺监机构", "建立绍兴二十三年复置节点。", "职源与沿革",
    )
    _, merged_taichang = canonicalize_guanglu_merge(w, history)
    relation(w, i, lang, xun, "前后演变", history, "西汉太初元年郎中令改名光禄勋。", "职源与沿革")
    relation(w, i, eastern, north_qi, "前后演变", history, "北齐光禄勋制度演成光禄寺。", "职源与沿革")
    relation(w, i, merged_rites, tp(w, "礼部", "机构", "南宋中兴以来"), "前后演变", history, "建炎三年光禄寺并归礼部。", "职源与沿革")
    relation(w, i, merged_taichang, tp(w, "太常寺", "机构", "南宋隆兴元年七月"), "前后演变", history, "隆兴元年光禄寺并入太常寺。", "职源与沿革")
    cite(w, "Timepoints", north_song, i, duty, "记录宋前期光禄寺职掌。", "职掌")
    alias_note(w, i, north_song, aliases, "简称")
    touched.update((lang_eid, xun_eid, guanglu_eid))

    # 宋前期官吏编制。
    for title, quota, officer in (
        ("判光禄寺事", 1, "兼官"),
        ("光禄寺府史", 4, "吏"),
        ("光禄寺驱使官", 2, "吏"),
        ("光禄寺供官", 15, "吏"),
    ):
        eid, post = state(
            w, i, title, "官职", "宋前期", "光禄寺官吏编制之一", roster,
            "光禄寺官吏", f"据宋前期编制建立{title}。", "编制", officer=officer,
        )
        staff(w, i, north_song, post, roster, f"宋前期光禄寺置{title}{quota}人。", "编制", quota=quota, staff_type=officer)
        touched.add(eid)

    # 元丰改制后的长贰属官；前四者沿用既有实体。
    for title, quota in (
        ("光禄寺卿", 1), ("光禄寺少卿", 1), ("光禄寺丞", 1),
        ("光禄寺主簿", 1), ("太官令", 1),
    ):
        eid, post = state(
            w, i, title, "官职", "北宋元丰五年",
            "元丰改制后光禄寺官额之一", roster,
            "光禄寺官", f"据元丰改制后编制建立或补足{title}。", "编制", officer="职事官",
        )
        staff(w, i, reform, post, roster, f"元丰改制后光禄寺置{title}{quota}人。", "编制", quota=quota)
        touched.add(eid)
    clerk_eid, clerks = state(
        w, i, "光禄寺吏人", "官职", "北宋元丰五年",
        "元丰改制后吏额十人", roster,
        "光禄寺吏", "建立元丰改制后光禄寺总吏额。", "编制", officer="吏",
    )
    staff(w, i, reform, clerks, roster, "元丰改制后光禄寺吏额十人。", "编制", quota=10, staff_type="吏")
    touched.add(clerk_eid)

    for title in (
        "法酒库", "内酒坊", "御厨", "翰林司", "牛羊司",
        "牛羊供应所", "乳酪院", "太官物料库", "外物料库", "油醋库",
    ):
        eid, office = state(
            w, i, title, "机构", "北宋元丰五年",
            "光禄寺所辖十局之一", roster,
            "光禄寺所属机构", f"据编制建立光禄寺所辖{title}。", "编制",
        )
        relation(w, i, reform, office, "上下级机构", roster, f"{title}为光禄寺所辖十局之一。", "编制")
        touched.add(eid)

    for title in ("御厨", "法酒库"):
        eid, _ = state(
            w, i, title, "机构", "宋前期",
            "承接光禄寺古制四局职事", duty,
            "宫廷膳酒机构", f"记录宋前期光禄寺古制四局职事分隶{title}。", "职掌",
        )
        touched.add(eid)

    for x in touched:
        rechain(w, x, "整理光禄寺源流、沿革、官属及所辖机构时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(241, 261)] == [
        "两京敦宗院", "保州敦宗院", "管勾敦宗院", "监敦宗院门",
        "军典", "敦宗院教授", "都尊长", "尊长", "玉牒所",
        "提举编修玉牒", "提领编修玉牒", "修玉牒官", "玉牒所检讨官",
        "玉牒所玉牒殿主管香火", "干办玉牒所玉牒殿", "专副", "库子",
        "宗官", "宗职", "光禄寺",
    ]
    entry241()
    entry242()
    entry243()
    entry244()
    entry245()
    entry246()
    entry247()
    entry248()
    entry249()
    entry250()
    entry251()
    entry252()
    entry253()
    entry254()
    entry255()
    entry256()
    entry257()
    entry258()
    entry259()
    entry260()


if __name__ == "__main__":
    main()
