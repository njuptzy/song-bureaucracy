#!/usr/bin/env python3
"""提取 chapter5t7 第481-500条：鸿胪寺馆驿、传法院与译经诸官。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_461_480 as previous


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


F = {i: load(i) for i in range(481, 501)}
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
    "汉代": -200, "唐代": 618, "唐开元十五年": 727,
    "唐天宝十三年三月二十七日": 754.23,
    "五代后晋": 936, "后周": 951,
    "宋初": 960.1, "北宋太祖朝": 960.2,
    "北宋太平兴国二年八月": 977.62,
    "北宋太平兴国七年六月": 982.46,
    "北宋太平兴国八年": 983, "北宋太平兴国八年六月": 983.46,
    "北宋景德三年": 1006.1, "北宋景德三年十二月十三日": 1006.96,
    "北宋大中祥符间": 1010,
    "北宋天禧五年十一月六日": 1021.86,
    "北宋庆历五年四月二十三日": 1045.31,
    "宋代（鸿胪寺馆驿编制）": 1050,
    "宋代（传法院译官）": 1050.1,
    "北宋熙宁三年五月二十九日": 1070.41,
    "北宋熙宁八年闰四月十八日": 1075.37,
    "北宋熙宁九年四月四日": 1076.27,
    "北宋元丰元年七月九日": 1078.53,
    "北宋元丰三年十月十九日": 1080.80,
    "北宋元丰新制": 1080.9,
    "北宋元丰五年七月八日": 1082.54,
    "北宋（隶都大提举在京诸司库务所年月未载）": 1090,
    "南宋初": 1127.1, "南宋": 1127.2,
    "南宋绍兴二十五年": 1155,
    "南宋乾道二年八月十一日": 1166.62,
    "南宋乾道九年": 1173,
    "南宋（隶礼部年月未载）": 1180,
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


def flag_target_citations(w, target_table, target_id, note):
    rows = w.conn.execute(
        "select id,conflict_flag,note from Citations where target_table=? and target_id=?",
        (target_table, target_id),
    ).fetchall()
    assert rows, (target_table, target_id)
    for cid, flag, old_note in rows:
        if flag != 1 or old_note != note:
            w.conn.execute(
                "update Citations set conflict_flag=1,note=? where id=?", (note, cid)
            )
            w._br("Citations", cid, f"标记礼宾院存废冲突：{note}")


def entry481():
    i, main = 481, F[481]["text"]
    w = W(i)
    target = tp(w, "往来国信所", "机构", "北宋元丰新制")
    cite(w, "Timepoints", target, i, main,
         "本条仅作参见与同名机构存在证据，不另造无时间节点。")
    w.commit()


def entry482():
    i, main = 482, F[482]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "别称"),
    )
    w = W(i)
    touched = set()
    eid, han = exact_state(
        w, i, "都亭驿", "机构", "汉代",
        "驿名源于汉代邮骑传递之馆", history,
        "馆驿", "建立都亭驿名称源流节点。", "职源与沿革",
    )
    _, tang = exact_state(
        w, i, "都亭驿", "机构", "唐开元十五年",
        "都亭驿之名已见", history,
        "馆驿", "建立唐代都亭驿名见载节点。", "职源与沿革",
    )
    old_eid, old = exact_state(
        w, i, "怀信驿", "机构", "后周",
        "后周世宗置东京怀信驿", history,
        "馆驿", "建立怀信驿前身节点。", "职源与沿革",
    )
    _, renamed = exact_state(
        w, i, "都亭驿", "机构", "北宋太平兴国二年八月",
        "东京怀信驿改名都亭驿，位于东京西大街街北，接待辽使",
        history, "馆驿", "建立太平兴国二年改名节点。", "职源与沿革",
    )
    cite(w, "Timepoints", renamed, i, duty, "补充北宋接待辽使职能。", "职能")
    relation(w, i, old, renamed, "前后演变", history,
             "怀信驿改名都亭驿。", "职源与沿革")
    _, yuanfeng = exact_state(
        w, i, "都亭驿", "机构", "北宋元丰新制",
        "隶鸿胪寺，接待辽国使者", main,
        "鸿胪寺属馆驿", "建立鸿胪寺所隶节点。",
    )
    relation(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), yuanfeng,
             "上下级机构", main, "都亭驿先隶鸿胪寺。")
    # “都大提举在京诸司库务所”是正文对正式机构的异称；第110页正式
    # 词头明确熙宁六年都亭驿归隶，复用该日正式节点，不另建简称实体。
    treasury = tp(
        w, "都大提举在京诸司库务司", "机构", "北宋熙宁六年正月五日"
    )
    _, treasury_stage = exact_state(
        w, i, "都亭驿", "机构", "北宋（隶都大提举在京诸司库务所年月未载）",
        "改隶都大提举在京诸司库务所", main,
        "馆驿", "建立都亭驿中期隶属节点。",
    )
    relation(w, i, treasury, treasury_stage, "上下级机构", main,
             "都亭驿曾隶都大提举在京诸司库务所。")
    ritual_eid, ritual = exact_state(
        w, i, "礼部", "机构", "南宋（隶礼部年月未载）",
        "统领南宋馆驿", main, "尚书省六部",
        "建立礼部统领南宋馆驿节点。",
    )
    _, south = exact_state(
        w, i, "都亭驿", "机构", "南宋（隶礼部年月未载）",
        "沿置于临安候潮门里，隶礼部，接待金国使者",
        history, "礼部属馆驿", "建立南宋沿置、隶属与职能节点。", "职源与沿革",
    )
    cite(w, "Timepoints", south, i, duty, "补充南宋接待金使职能。", "职能")
    relation(w, i, ritual, south, "上下级机构", main, "都亭驿后隶礼部。")
    alias_note(w, i, south, aliases, "别称")
    touched.update((eid, old_eid, ritual_eid))
    for title, officer, quota in (
        ("监都亭驿", "监官", 1), ("都亭驿专知官", "专知官", 1),
        ("都亭驿副知", "副知", 1), ("都亭驿手分", "手分", 1),
        ("都亭驿贴司", "贴司", 1), ("都亭驿库级", "库级", 1),
        ("都亭驿库子", "库子", 2), ("都亭驿院子", "院子", 7),
        ("都亭驿兵级", "兵级", 40),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（鸿胪寺馆驿编制）",
            f"都亭驿所置{officer}，编制{quota}人", roster,
            "都亭驿属员", f"建立{title}定额。", "编制", officer=officer,
        )
        staff(w, i, yuanfeng, post, roster, f"都亭驿置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    for x in touched:
        rechain(w, x, "整理都亭驿前身、隶属及属员完整时间链。")
    w.commit()


def entry483():
    i, main = 483, F[483]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职能"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "都亭西驿", "机构", "北宋大中祥符间",
        "始置于东京皇城西掖门外，接待河西蕃部及西夏使者",
        origin, "馆驿", "建立都亭西驿始置节点。", "职源",
    )
    cite(w, "Timepoints", start, i, duty, "补充接待河西蕃部职能。", "职能")
    _, reform = exact_state(
        w, i, "都亭西驿", "机构", "北宋元丰新制",
        "隶鸿胪寺，掌河西蕃部贡奉", main,
        "鸿胪寺属馆驿", "补足鸿胪寺所隶节点。",
    )
    relation(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "都亭西驿先隶鸿胪寺。")
    _, south = exact_state(
        w, i, "都亭西驿", "机构", "南宋（隶礼部年月未载）",
        "后隶礼部", main, "礼部属馆驿", "建立后隶礼部节点。",
    )
    relation(w, i, tp(w, "礼部", "机构", "南宋（隶礼部年月未载）"), south,
             "上下级机构", main, "都亭西驿后隶礼部。")
    office_eid, office = exact_state(
        w, i, "管勾都亭西驿所", "机构", "宋代（鸿胪寺馆驿编制）",
        "都亭西驿管勾官办事机构，置管勾官二人", roster,
        "都亭西驿属所", "建立管勾都亭西驿所及定额。", "编制",
    )
    relation(w, i, reform, office, "上下级机构", roster,
             "都亭西驿置管勾所。", "编制")
    post_eid, post = exact_state(
        w, i, "管勾都亭西驿所官", "官职", "宋代（鸿胪寺馆驿编制）",
        "由诸司使、副以下至三班使臣充，掌河西蕃部贡奉，编制二人",
        aliases, "都亭西驿管勾官", "建立都亭西驿管勾官任用与定额。", "简称",
        officer="管勾官",
    )
    staff(w, i, office, post, roster, "管勾都亭西驿所置管勾官二人。", "编制",
          quota=2, staff_type="管勾官")
    alias_note(w, i, reform, aliases, "简称")
    touched.update((eid, office_eid, post_eid))
    for x in touched:
        rechain(w, x, "整理都亭西驿、管勾所及管勾官时间链。")
    w.commit()


def entry484():
    i, main, aliases = 484, F[484]["text"], field(484, "简称")
    w = W(i)
    eid, office = exact_state(
        w, i, "管勾都亭西驿所", "机构", "宋代（鸿胪寺馆驿编制）",
        "都亭西驿管勾官办事机构，掌外国使者接待及河西蕃部入境后的迎接、管押、供须、赐物备办",
        main, "都亭西驿属所", "补足管勾都亭西驿所职掌。",
    )
    relation(w, i, tp(w, "都亭西驿", "机构", "北宋元丰新制"), office,
             "上下级机构", main, "管勾都亭西驿所为都亭西驿办事机构。")
    alias_note(w, i, office, aliases, "简称")
    rechain(w, eid, "整理管勾都亭西驿所时间链。")
    w.commit()


def entry485():
    i, main = 485, F[485]["text"]
    origin, duty, roster = field(i, "职源"), field(i, "职能"), field(i, "编制")
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "怀远驿", "机构", "北宋景德三年十二月十三日",
        "始置，接待交州、占城、龟兹、大食、于阗等西南蕃国使者",
        origin, "馆驿", "建立怀远驿始置节点。", "职源",
    )
    cite(w, "Timepoints", start, i, duty, "补充接待西南蕃国职能。", "职能")
    _, reform = exact_state(
        w, i, "怀远驿", "机构", "北宋元丰新制",
        "隶鸿胪寺，接待西南蕃国贡使", main,
        "鸿胪寺属馆驿", "补足元丰所隶节点。",
    )
    relation(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "怀远驿先隶鸿胪寺。")
    for time, event in (
        ("南宋初", "罢置"),
        ("南宋绍兴二十五年", "复设"),
        ("南宋乾道二年八月十一日", "废罢"),
        ("南宋乾道九年", "临时以贡院充作怀远驿，事毕即罢"),
    ):
        exact_state(w, i, "怀远驿", "机构", time, event, origin,
                    "礼部属馆驿", f"建立怀远驿{time}存废节点。", "职源")
    south = tp(w, "怀远驿", "机构", "南宋绍兴二十五年")
    relation(w, i, tp(w, "礼部", "机构", "南宋（隶礼部年月未载）"), south,
             "上下级机构", main, "南宋怀远驿后隶礼部。")
    monitor_eid, monitor = exact_state(
        w, i, "监怀远驿", "官职", "宋代（鸿胪寺馆驿编制）",
        "怀远驿监官，编制二员", roster,
        "怀远驿监官", "建立监怀远驿定额。", "编制", officer="监官",
    )
    staff(w, i, reform, monitor, roster, "怀远驿置监官二员。", "编制",
          quota=2, staff_type="监官")
    touched.update((eid, monitor_eid))
    for x in touched:
        rechain(w, x, "整理怀远驿存废、隶属及监官时间链。")
    w.commit()


def entry486():
    i, main = 486, F[486]["text"]
    origin, duty, roster = field(i, "职源"), field(i, "职能"), field(i, "编制")
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "来远驿", "机构", "北宋熙宁三年五月二十九日",
        "始置，隶鸿胪寺，接待四方蕃客", origin,
        "鸿胪寺属馆驿", "建立来远驿始置节点。", "职源",
    )
    cite(w, "Timepoints", start, i, duty, "补充接待四方蕃客职能。", "职能")
    relation(w, i, tp(w, "鸿胪寺", "机构", "宋前期"), start,
             "上下级机构", main, "来远驿隶鸿胪寺。")
    _, concurrent = exact_state(
        w, i, "来远驿", "机构", "北宋熙宁八年闰四月十八日",
        "由都亭西驿监官兼管勾", roster,
        "鸿胪寺属馆驿", "建立熙宁八年兼管节点。", "编制",
    )
    monitor_eid, monitor = exact_state(
        w, i, "监都亭西驿", "官职", "北宋熙宁八年闰四月十八日",
        "兼管勾来远驿", roster,
        "馆驿监官", "建立都亭西驿监官兼管来远驿节点。", "编制", officer="监官",
    )
    staff(w, i, concurrent, monitor, roster, "都亭西驿监官兼管勾来远驿。", "编制",
          staff_type="兼管勾官")
    touched.update((eid, monitor_eid))
    for x in touched:
        rechain(w, x, "整理来远驿及兼管监官时间链。")
    w.commit()


def entry487():
    i, main = 487, F[487]["text"]
    w = W(i)
    touched = set()
    eid, tang = exact_state(
        w, i, "樟亭驿", "机构", "唐代",
        "始置，隶杭州", main, "杭州属馆驿", "建立樟亭驿唐代始置节点。",
    )
    _, song = exact_state(
        w, i, "樟亭驿", "机构", "北宋",
        "沿置后改名浙江亭", main, "杭州属馆驿", "建立北宋改名节点。",
    )
    successor_eid, successor = exact_state(
        w, i, "浙江亭", "机构", "北宋",
        "由樟亭驿改名，位于钱塘县旧治南五里", main,
        "杭州属馆驿", "建立浙江亭承接节点。",
    )
    relation(w, i, song, successor, "前后演变", main, "樟亭驿改为浙江亭。")
    _, south = exact_state(
        w, i, "浙江亭", "机构", "南宋",
        "宰执辞官、免官后出居此驿等待朝命", main,
        "杭州属馆驿", "建立南宋浙江亭职能节点。",
    )
    touched.update((eid, successor_eid))
    for x in touched:
        rechain(w, x, "整理樟亭驿改名浙江亭时间链。")
    w.commit()


def entry488():
    i, main, aliases = 488, F[488]["text"], field(488, "简称")
    w = W(i)
    eid, jin = exact_state(
        w, i, "班荆馆", "机构", "五代后晋",
        "置于汴州城外", main, "馆驿", "建立后晋班荆馆节点。",
    )
    _, song = exact_state(
        w, i, "班荆馆", "机构", "宋初",
        "以陈桥驿为班荆馆，供辽使迎饯", main,
        "馆驿", "建立宋初班荆馆节点。",
    )
    _, south = exact_state(
        w, i, "班荆馆", "机构", "南宋",
        "沿置于临安赤岸港，接待外国宾客", main,
        "馆驿", "建立南宋班荆馆节点。",
    )
    alias_note(w, i, south, aliases, "简称")
    rechain(w, eid, "整理班荆馆完整时间链。")
    w.commit()


def entry489():
    i, main = 489, F[489]["text"]
    history, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    touched = set()
    eid, tang = exact_state(
        w, i, "礼宾院", "机构", "唐天宝十三年三月二十七日",
        "鸿胪寺已有礼宾院", history,
        "鸿胪寺属院", "建立礼宾院唐代见载节点。", "职源与沿革",
    )
    _, north = exact_state(
        w, i, "礼宾院", "机构", "北宋景德三年",
        "北宋沿置于京师归德坊，蕃驿院并入，掌外国宾客安顿、物料供应及互市翻译",
        history, "鸿胪寺属院", "建立景德三年蕃驿院并入节点。", "职源与沿革",
    )
    cite(w, "Timepoints", north, i, main, "补充礼宾院位置。")
    cite(w, "Timepoints", north, i, duty, "补充礼宾院职掌。", "职掌")
    predecessor_eid, predecessor = exact_state(
        w, i, "蕃驿院", "机构", "宋初",
        "外国宾客馆驿机构，景德三年并入礼宾院", history,
        "馆驿", "建立蕃驿院前身节点。", "职源与沿革",
    )
    relation(w, i, predecessor, north, "前后演变", history,
             "景德三年蕃驿院并入礼宾院。", "职源与沿革")
    _, abolished = exact_state(
        w, i, "礼宾院", "机构", "北宋熙宁九年四月四日",
        "罢废", history, "鸿胪寺属院",
        "建立熙宁九年罢废节点。", "职源与沿革",
    )
    conflict_note = "本条载熙宁九年罢礼宾院，与‘鸿胪寺’条列其为元丰新制所隶官司冲突，双证据并存。"
    flag_target_citations(w, "Timepoints", abolished, conflict_note)
    yuanfeng = tp(w, "礼宾院", "机构", "北宋元丰新制")
    flag_target_citations(w, "Timepoints", yuanfeng, conflict_note)
    relrow = w.conn.execute(
        "select id from Relationships where subject_id=? and object_id=? and relation_type='上下级机构'",
        (tp(w, "鸿胪寺", "机构", "北宋元丰新制"), yuanfeng),
    ).fetchone()
    assert relrow
    flag_target_citations(w, "Relationships", relrow[0], conflict_note)
    touched.update((eid, predecessor_eid))
    for title, officer, quota in (
        ("监礼宾院", "监官", 2), ("礼宾院通事", "通事", None),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "北宋景德三年",
            "礼宾院所置" + officer + (f"，编制{quota}人" if quota else "，通晓诸蕃语言"),
            roster, "礼宾院属员", f"建立{title}编制。", "编制", officer=officer,
        )
        staff(w, i, north, post, roster, f"礼宾院设置{officer}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    for x in touched:
        rechain(w, x, "整理礼宾院、蕃驿院及属员完整时间链。")
    w.commit()


def entry490():
    i, main = 490, F[490]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "编制"), field(i, "别名"),
    )
    w = W(i)
    touched = set()
    predecessor_eid, predecessor = exact_state(
        w, i, "译经院", "机构", "北宋太平兴国七年六月",
        "建于太平兴国寺，翻译梵文佛经", origin,
        "译经机构", "建立译经院前身节点。", "职源",
    )
    eid, renamed = exact_state(
        w, i, "传法院", "机构", "北宋太平兴国八年",
        "译经院赐额‘传法’后改称，翻译梵文佛经", origin,
        "鸿胪寺属院", "建立传法院赐额节点。", "职源",
    )
    cite(w, "Timepoints", renamed, i, duty, "补充翻译梵文佛经职掌。", "职掌")
    relation(w, i, predecessor, renamed, "前后演变", origin,
             "译经院赐额传法后改称传法院。", "职源")
    _, reform = exact_state(
        w, i, "传法院", "机构", "北宋元丰新制",
        "隶鸿胪寺，翻译梵文佛经", main,
        "鸿胪寺属院", "补足元丰鸿胪寺所隶节点。",
    )
    relation(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "传法院隶鸿胪寺。")
    alias_note(w, i, renamed, aliases, "别名")
    touched.update((eid, predecessor_eid))
    for title, officer in (("传法院译经僧官", "译经僧官"), ("传法院译语官", "译语官")):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（传法院译官）",
            f"传法院所置{officer}", roster,
            "传法院属员", f"建立{title}。", "编制", officer=officer,
        )
        staff(w, i, renamed, post, roster, f"传法院设置{officer}。", "编制",
              staff_type=officer)
        touched.add(seid)
    for x in touched:
        rechain(w, x, "整理译经院改称传法院及译官时间链。")
    w.commit()


def entry491():
    i, main, aliases = 491, F[491]["text"], field(491, "别称")
    w = W(i)
    eid, start = exact_state(
        w, i, "译经院", "机构", "北宋太平兴国七年六月",
        "建成，专事佛经翻译，次年赐额‘传法’并改称传法院", main,
        "译经机构", "补足译经院始建与职掌。",
    )
    relation(w, i, start, tp(w, "传法院", "机构", "北宋太平兴国八年"),
             "前后演变", main, "译经院赐额传法后改称传法院。")
    alias_note(w, i, start, aliases, "别称")
    rechain(w, eid, "整理译经院时间链。")
    w.commit()


def entry492():
    i, main = 492, F[492]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "知译经院", "官职", "北宋太平兴国七年六月",
        "以文臣朝官充，掌佛经翻译润色", main,
        "译经院差遣", "建立知译经院始置、任用与职掌。", officer="文臣朝官差遣",
    )
    staff(w, i, tp(w, "译经院", "机构", "北宋太平兴国七年六月"), post,
          main, "太平兴国七年置知译经院。", staff_type="知院差遣")
    rechain(w, eid, "整理知译经院时间链。")
    w.commit()


def entry493():
    i, main = 493, F[493]["text"]
    origin, duty, aliases = field(i, "职源"), field(i, "职掌"), field(i, "简称")
    w = W(i)
    eid, tang = exact_state(
        w, i, "译经使兼润文", "官职", "唐代",
        "已有宰相兼译经使之制", origin,
        "译经兼官", "建立唐代制度源流节点。", "职源", officer="宰相兼官",
    )
    _, start = exact_state(
        w, i, "译经使兼润文", "官职", "北宋天禧五年十一月六日",
        "始由宰相同中书门下平章事兼任，挂衔提领传法院译佛经事",
        origin, "译经兼官", "建立北宋始置节点。", "职源", officer="宰相兼官",
    )
    cite(w, "Timepoints", start, i, duty, "补充提领传法院译经职掌。", "职掌")
    staff(w, i, tp(w, "传法院", "机构", "北宋太平兴国八年"), start,
          main, "传法院译经使兼润文由宰相兼领。", staff_type="宰相兼官")
    _, titled = exact_state(
        w, i, "译经使兼润文", "官职", "北宋庆历五年四月二十三日",
        "降麻制始正式入衔", origin,
        "译经兼官", "建立庆历五年入衔节点。", "职源", officer="宰相兼官",
    )
    _, abolished = exact_state(
        w, i, "译经使兼润文", "官职", "北宋元丰五年七月八日",
        "废罢", origin, "译经兼官",
        "建立元丰五年罢官节点。", "职源", officer="宰相兼官",
    )
    alias_note(w, i, titled, aliases, "简称")
    rechain(w, eid, "整理译经使兼润文完整时间链。")
    w.commit()


def entry494():
    i, main = 494, F[494]["text"]
    w = W(i)
    eid, office = exact_state(
        w, i, "译经润文使司", "机构", "北宋天禧五年十一月六日",
        "译经使兼润文虽为挂衔官，仍置官印，以‘译经润文使司’为文",
        main, "传法院属司", "建立译经润文使司机构与官印。",
    )
    relation(w, i, tp(w, "传法院", "机构", "北宋太平兴国八年"), office,
             "上下级机构", main, "译经润文使司办理传法院润文使事务。")
    _, abolished = exact_state(
        w, i, "译经润文使司", "机构", "北宋元丰五年七月八日",
        "废罢", main, "传法院属司", "建立元丰五年废罢节点。",
    )
    rechain(w, eid, "整理译经润文使司时间链。")
    w.commit()


def entry495():
    i, main = 495, F[495]["text"]
    origin, duty, aliases = field(i, "职源"), field(i, "职掌"), field(i, "简称")
    w = W(i)
    eid, start = exact_state(
        w, i, "译经润文官", "官职", "北宋太平兴国八年六月",
        "始置，由朝官参详润色梵学僧所译佛经文字",
        origin, "译经兼官", "建立译经润文官始置节点。", "职源", officer="朝官兼官",
    )
    cite(w, "Timepoints", start, i, duty, "补充初设润色译经职掌。", "职掌")
    staff(w, i, tp(w, "传法院", "机构", "北宋太平兴国八年"), start,
          main, "传法院设置译经润文官。", staff_type="朝官兼官")
    _, renzong = exact_state(
        w, i, "译经润文官", "官职", "北宋仁宗朝",
        "改由执政官兼，多挂名以增重其事", origin,
        "译经兼官", "建立仁宗朝任用变化节点。", "职源", officer="执政官兼官",
    )
    cite(w, "Timepoints", renzong, i, duty, "补充后期多为挂名性质。", "职掌")
    _, abolished = exact_state(
        w, i, "译经润文官", "官职", "北宋元丰五年七月八日",
        "废罢", origin, "译经兼官", "建立元丰五年罢官节点。", "职源", officer="兼官",
    )
    alias_note(w, i, renzong, aliases, "简称")
    rechain(w, eid, "整理译经润文官完整时间链。")
    w.commit()


def entry496():
    i, main, aliases = 496, F[496]["text"], field(496, "简称")
    w = W(i)
    touched = set()
    eid, post = exact_state(
        w, i, "西天译经三藏", "官职", "宋代（传法院译官）",
        "隶鸿胪寺传法院，专译梵文佛经，为译官僧中位次最高者",
        main, "传法院译经僧官", "建立西天译经三藏隶属、职掌与位次。", officer="译经僧官",
    )
    staff(w, i, tp(w, "传法院", "机构", "北宋太平兴国八年"), post,
          main, "传法院设置西天译经三藏。", staff_type="译经僧官")
    touched.add(eid)
    for title, event in (
        ("西天同译经三藏", "位次于西天译经三藏，从事梵文佛经翻译"),
        ("梵学笔受", "位次在同译经三藏之后，笔受梵经译文"),
        ("译经缀文", "传法院译经僧官之一，负责缀文"),
        ("证义", "传法院译经僧官之一，负责证义"),
    ):
        seid, child = exact_state(
            w, i, title, "官职", "宋代（传法院译官）", event, main,
            "传法院译经僧官", f"建立{title}位次实例。", officer="译经僧官",
        )
        staff(w, i, tp(w, "传法院", "机构", "北宋太平兴国八年"), child,
              main, f"传法院设置{title}。", staff_type="译经僧官")
        touched.add(seid)
    alias_note(w, i, post, aliases, "简称")
    for x in touched:
        rechain(w, x, "整理传法院译经僧官位次时间链。")
    w.commit()


def entry497():
    i, main = 497, F[497]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "西天同译经三藏", "官职", "宋代（传法院译官）",
        "隶鸿胪寺传法院，从事梵文佛经翻译，位次于西天译经三藏",
        main, "传法院译经僧官", "补足西天同译经三藏隶属、职掌与位次。", officer="译经僧官",
    )
    staff(w, i, tp(w, "传法院", "机构", "北宋太平兴国八年"), post,
          main, "传法院设置西天同译经三藏。", staff_type="译经僧官")
    rechain(w, eid, "整理西天同译经三藏时间链。")
    w.commit()


def entry498():
    i, main = 498, F[498]["text"]
    w = W(i)
    touched = set()
    eid, target = exact_state(
        w, i, "译经三藏大法师", "官职", "北宋元丰三年十月十九日",
        "罢僧官所带正卿官名，改授译经三藏大法师师号",
        main, "译经僧官师号", "建立译经三藏大法师改授节点。", officer="译经僧官师号",
    )
    for title, officer in (
        ("试光禄卿译经僧官", "试光禄卿旧衔"),
        ("试鸿胪卿译经僧官", "试鸿胪卿旧衔"),
    ):
        source_eid, source = exact_state(
            w, i, title, "官职", "北宋元丰三年十月十九日以前",
            f"传法院译经僧官所带{officer}", main,
            "译经僧官旧衔", f"建立元丰改制前{title}。", officer=officer,
        )
        relation(w, i, source, target, "前后演变", main,
                 f"元丰三年罢{officer}，改授译经三藏大法师。")
        touched.add(source_eid)
    staff(w, i, tp(w, "传法院", "机构", "北宋元丰新制"), target,
          main, "传法院译经僧官改授译经三藏大法师。", staff_type="译经僧官师号")
    touched.add(eid)
    for x in touched:
        rechain(w, x, "整理译经僧官正卿旧衔改授师号时间链。")
    w.commit()


def entry499():
    i, main = 499, F[499]["text"]
    w = W(i)
    touched = set()
    eid, target = exact_state(
        w, i, "译经三藏法师", "官职", "北宋元丰三年十月十九日",
        "罢僧官所带少卿官名，改授译经三藏法师师号",
        main, "译经僧官师号", "建立译经三藏法师改授节点。", officer="译经僧官师号",
    )
    for title, officer in (
        ("试光禄少卿译经僧官", "试光禄少卿旧衔"),
        ("试鸿胪少卿译经僧官", "试鸿胪少卿旧衔"),
    ):
        source_eid, source = exact_state(
            w, i, title, "官职", "北宋元丰三年十月十九日以前",
            f"传法院译经僧官所带{officer}", main,
            "译经僧官旧衔", f"建立元丰改制前{title}。", officer=officer,
        )
        relation(w, i, source, target, "前后演变", main,
                 f"元丰三年罢{officer}，改授译经三藏法师。")
        touched.add(source_eid)
    staff(w, i, tp(w, "传法院", "机构", "北宋元丰新制"), target,
          main, "传法院译经僧官改授译经三藏法师。", staff_type="译经僧官师号")
    touched.add(eid)
    for x in touched:
        rechain(w, x, "整理译经僧官少卿旧衔改授师号时间链。")
    w.commit()


def entry500():
    i, main, aliases = 500, F[500]["text"], field(500, "简称")
    w = W(i)
    eid, tang = exact_state(
        w, i, "梵学笔受", "官职", "唐代",
        "笔受之名始于唐，由通梵文朝官充", main,
        "译经属官", "建立梵学笔受唐代源流节点。", officer="笔受",
    )
    _, song = exact_state(
        w, i, "梵学笔受", "官职", "北宋太平兴国七年六月",
        "译经院始设梵学僧笔受，从事佛经翻译，宋代以通梵文僧人充",
        main, "译经院属官", "建立北宋梵学笔受始置节点。", officer="译经僧官",
    )
    staff(w, i, tp(w, "译经院", "机构", "北宋太平兴国七年六月"), song,
          main, "译经院设置梵学笔受。", staff_type="译经僧官")
    alias_note(w, i, song, aliases, "简称")
    rechain(w, eid, "整理梵学笔受完整时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(481, 501)] == [
        "往来国信所", "都亭驿", "都亭西驿", "管勾都亭西驿所", "怀远驿",
        "来远驿", "樟亭驿", "班荆馆", "礼宾院", "传法院",
        "译经院", "知译经院", "译经使兼润文", "译经润文使司",
        "译经润文官", "西天译经三藏", "西天同译经三藏",
        "译经三藏大法师", "译经三藏法师", "梵学笔受",
    ]
    for i in range(481, 501):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
