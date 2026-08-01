#!/usr/bin/env python3
"""提取 chapter5t7 第521-540条：道录院、道正司及左右街道官系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_501_520 as previous


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


F = {i: load(i) for i in range(521, 541)}
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
    "北朝": 450, "北周": 557, "隋唐": 600, "唐": 618,
    "后周": 951, "宋初": 960, "宋前期": 980,
    "北宋（始置年月未载）": 990,
    "北宋大中祥符二年十一月": 1009.86,
    "北宋天禧五年": 1021,
    "宋代（左右街道录院编制）": 1050,
    "北宋熙宁间": 1070,
    "北宋元丰三年十月": 1080.8,
    "北宋（增置都、副道录后）": 1090,
    "北宋徽宗朝": 1105,
    "北宋政和六年": 1116, "北宋政和七年": 1117,
    "北宋政和八年": 1118, "北宋宣和元年": 1119,
    "北宋宣和三年": 1121, "北宋宣和五年": 1123,
    "北宋宣和七年": 1125, "南宋": 1127,
    "南宋绍兴二十年": 1150, "南宋宁宗朝": 1200,
    "南宋庆元三年五月二十三日": 1197.39,
    "南宋庆元四年五月十七日": 1198.38,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    match = re.search(r"(-?\d{3,4})", time or "")
    if match:
        return (int(match.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
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


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def placeholder(i):
    assert F[i]["text"] == ""
    assert F[i]["fields"].get("_placeholder") is True


def entry521():
    placeholder(521)


def entry522():
    i, main = 522, F[522]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "编制"),
        field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    eid, early = exact_state(
        w, i, "左、右街道录院", "机构", "宋前期",
        "沿置，归礼部祠部司管，掌在京及诸路宫观、道士、女冠帐籍与斋醮等事",
        main, "中央道教事务机构", "建立宋前期道录院隶属与职掌。",
    )
    cite(w, "Timepoints", early, i, duty, "补充道录院职掌。", "职掌")
    relation(w, i, tp(w, "祠部司", "机构", "宋前期"), early,
             "上下级机构", main, "左、右街道录院归礼部祠部司管。")
    _, zhenghe = exact_state(
        w, i, "左、右街道录院", "机构", "北宋政和六年",
        "改隶秘书省", main, "秘书省所属道教事务机构",
        "建立政和六年改隶秘书省节点。",
    )
    relation(w, i, tp(w, "秘书省", "机构", "北宋政和六年"), zhenghe,
             "上下级机构", main, "政和六年左、右街道录院改隶秘书省。")
    _, restored = exact_state(
        w, i, "左、右街道录院", "机构", "北宋宣和五年",
        "道德院已复旧名左、右街道录院", origin,
        "中央道教事务机构", "建立宣和五年复名节点。", "职源",
    )
    _, south = exact_state(
        w, i, "左、右街道录院", "机构", "南宋",
        "沿置，隶礼部祠部司", main, "礼部祠部司所属道教事务机构",
        "建立南宋沿置与隶属节点。",
    )
    ritual_eid, ritual = exact_state(
        w, i, "祠部司", "机构", "南宋", "统管南宋道录院",
        main, "礼部所属司", "建立祠部司南宋统管道录院节点。",
    )
    relation(w, i, ritual, south, "上下级机构", main,
             "南宋左、右街道录院隶礼部祠部司。")
    _, establishment = exact_state(
        w, i, "左、右街道录院", "机构", "宋代（左右街道录院编制）",
        "置都道录、副道录、左街道录、右街道录、都监、首座、鉴义等道官",
        roster, "中央道教事务机构", "建立道录院编制节点。", "编制",
    )
    for title, officer in (
        ("都道录", "都道录"), ("副都道录", "副道录"),
        ("左街道录", "左街道录"), ("右街道录", "右街道录"),
        ("道录院都监", "都监"), ("道录院首座", "首座"),
        ("道录院鉴义", "鉴义"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（左右街道录院编制）",
            f"左、右街道录院所置{officer}", roster, "道录院道官",
            f"建立{officer}编制关系。", "编制", officer=officer,
        )
        staff(w, i, establishment, post, roster, f"左、右街道录院置{officer}。",
              "编制", staff_type=officer)
        touched.add(seid)
    alias_note(w, i, restored, aliases, "简称与别名")
    touched.update((eid, ritual_eid))
    finish(w, touched, "整理左、右街道录院源流、隶属与编制完整时间链。")


def entry523():
    i, main = 523, F[523]["text"]
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, "左、右街道录院", "机构", "北宋宣和元年",
        "改名道德院", main, "中央道教事务机构",
        "建立宣和元年改名起点。",
    )
    eid, renamed = exact_state(
        w, i, "道德院", "机构", "北宋宣和元年",
        "由左、右街道录院改名", main, "中央道教事务机构",
        "建立道德院改名节点。",
    )
    relation(w, i, old, renamed, "前后演变", main,
             "宣和元年左、右街道录院改名道德院。")
    _, ended = exact_state(
        w, i, "道德院", "机构", "北宋宣和五年",
        "复旧名左、右街道录院", main, "中央道教事务机构",
        "建立宣和五年复旧节点。",
    )
    relation(w, i, ended, tp(w, "左、右街道录院", "机构", "北宋宣和五年"),
             "前后演变", main, "宣和五年道德院复旧名左、右街道录院。")
    touched.update((old_eid, eid))
    finish(w, touched, "整理道德院改名与复旧时间链。")


def entry524():
    i, main = 524, F[524]["text"]
    origin, duty, rank, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "别称"),
    )
    w, touched = W(i), set()
    eid, office = exact_state(
        w, i, "提举秘书省左右街道录院", "机构", "北宋政和七年",
        "始置，由大学士领左右街道录院事，置提举官一人、管勾文字官二人",
        origin, "秘书省属机构", "建立提举秘书省左右街道录院始置节点。", "职源",
    )
    cite(w, "Timepoints", office, i, duty, "补充大学士领院职掌。", "职掌")
    relation(w, i, tp(w, "秘书省", "机构", "北宋政和六年"), office,
             "上下级机构", main, "提举秘书省左右街道录院隶秘书省。")
    relation(w, i, office, tp(w, "左、右街道录院", "机构", "北宋政和六年"),
             "上下级机构", duty, "提举机构统领左右街道录院事。", "职掌")
    for title, officer, quota, grade in (
        ("提举秘书省道录院", "提举官", 1,
         "观文殿大学士以上至三公，使相、宰相官可充"),
        ("提举秘书省道录院管勾文字", "管勾文字官", 2, None),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "北宋政和七年",
            f"提举秘书省左右街道录院所置{officer}，编制{quota}人",
            roster, "道录院属官", f"建立{officer}定额。", "编制",
            officer=officer, grade=grade,
        )
        if grade:
            cite(w, "Timepoints", post, i, rank, "补充提举官充任资格。", "品位")
        staff(w, i, office, post, roster, f"置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    alias_note(w, i, office, aliases, "别称")
    touched.add(eid)
    finish(w, touched, "整理提举秘书省左右街道录院及属官时间链。")


def entry525():
    i, main = 525, F[525]["text"]
    history, duty = field(i, "职源与沿革"), field(i, "职掌")
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, "左、右街道录院", "机构", "北宋熙宁间",
        "改名道录司", history, "中央道教事务机构",
        "建立熙宁间改名起点。", "职源与沿革",
    )
    eid, renamed = exact_state(
        w, i, "道录司", "机构", "北宋熙宁间",
        "由左、右街道录院改名，掌府、州、军道观、道士、女冠事务",
        history, "中央道教事务机构", "建立道录司改名节点。", "职源与沿革",
    )
    cite(w, "Timepoints", renamed, i, duty, "补充道录司职掌。", "职掌")
    relation(w, i, old, renamed, "前后演变", history,
             "熙宁间左、右街道录院改名道录司。", "职源与沿革")
    _, ended = exact_state(
        w, i, "道录司", "机构", "北宋徽宗朝", "复道录院旧称",
        history, "中央道教事务机构", "建立徽宗朝复旧节点。", "职源与沿革",
    )
    _, restored = exact_state(
        w, i, "左、右街道录院", "机构", "北宋徽宗朝",
        "由道录司复旧称", history, "中央道教事务机构",
        "建立徽宗朝恢复道录院节点。", "职源与沿革",
    )
    relation(w, i, ended, restored, "前后演变", history,
             "徽宗朝道录司复道录院旧称。", "职源与沿革")
    touched.update((old_eid, eid))
    finish(w, touched, "整理道录司改名与复旧时间链。")


def entry526():
    i, main, duty = 526, F[526]["text"], field(526, "职掌")
    w = W(i)
    eid, placed = exact_state(
        w, i, "道正司", "机构", "北宋宣和三年",
        "置于地方州军，掌道观、道士、女冠事务；节镇置道正、副各一员，余州置道正一员",
        main, "地方道教事务机构", "建立宣和三年地方设置节点。",
    )
    _, south = exact_state(
        w, i, "道正司", "机构", "南宋庆元四年五月十七日",
        "为毁失度牒的僧道保明原牒有无", duty, "地方道教事务机构",
        "建立庆元四年职掌见载节点。", "职掌",
    )
    finish(w, {eid}, "整理道正司设置与职掌时间链。")


def entry527():
    i, main, duty = 527, F[527]["text"], field(527, "职掌")
    w = W(i)
    eid, early = exact_state(
        w, i, "道正", "官职", "北宋大中祥符二年十一月",
        "诸州道官依资可转至道正，主管州军道正司",
        duty, "地方道官", "建立大中祥符二年道正升转与职掌节点。", "职掌",
        officer="道官",
    )
    _, placed = exact_state(
        w, i, "道正", "官职", "北宋宣和三年",
        "节镇置道正一员，余州置道正一员", duty,
        "地方道官", "建立宣和三年道正置额节点。", "职掌", officer="道官",
    )
    staff(w, i, tp(w, "道正司", "机构", "北宋宣和三年"), placed,
          duty, "道正司置道正一员。", "职掌", quota=1, staff_type="道正")
    finish(w, {eid}, "整理道正升转、职掌与置额时间链。")


def entry528():
    i, main = 528, F[528]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "副道正", "官职", "北宋宣和三年",
        "道正司副官，节镇置一员", main, "地方道官",
        "建立副道正职掌与置额。", officer="副道正",
    )
    staff(w, i, tp(w, "道正司", "机构", "北宋宣和三年"), post,
          main, "节镇道正司置副道正一员。", quota=1, staff_type="副道正")
    finish(w, {eid}, "整理副道正时间链。")


def entry529():
    i, main = 529, F[529]["text"]
    w = W(i)
    eid, _ = exact_state(
        w, i, "山门道正司", "机构", "南宋宁宗朝",
        "经官方批准建立，管理道山事务", main, "地方道山管理机构",
        "建立南宋宁宗朝山门道正司节点。",
    )
    finish(w, {eid}, "整理山门道正司时间链。")


def entry530():
    i, main, aliases = 530, F[530]["text"], field(530, "简称")
    w = W(i)
    eid, old = exact_state(
        w, i, "都道录", "官职", "北宋（政和八年前）",
        "总掌左、右街道录院教门事", main, "中央道官",
        "建立都道录政和改名前节点。", officer="道官",
    )
    _, restored = exact_state(
        w, i, "都道录", "官职", "北宋宣和七年",
        "由知左右街道录院事复元丰旧名", main, "中央道官",
        "建立宣和七年复旧名节点。", officer="道官",
    )
    alias_note(w, i, old, aliases, "简称")
    finish(w, {eid}, "整理都道录改名与复旧时间链。")


def entry531():
    i, main = 531, F[531]["text"]
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, "都道录", "官职", "北宋政和八年",
        "改名知左右街道录院事", main, "中央道官",
        "建立政和八年改名起点。", officer="道官",
    )
    eid, renamed = exact_state(
        w, i, "知左右街道录院事", "官职", "北宋政和八年",
        "由都道录改名，掌道教事", main, "中央道官",
        "建立知左右街道录院事改名节点。", officer="道官",
    )
    relation(w, i, old, renamed, "前后演变", main,
             "政和八年都道录改名知左右街道录院事。")
    _, ended = exact_state(
        w, i, "知左右街道录院事", "官职", "北宋宣和七年",
        "复旧名都道录", main, "中央道官",
        "建立宣和七年复旧节点。", officer="道官",
    )
    relation(w, i, ended, tp(w, "都道录", "官职", "北宋宣和七年"),
             "前后演变", main, "宣和七年复旧名都道录。")
    staff(w, i, tp(w, "左、右街道录院", "机构", "北宋政和六年"), renamed,
          main, "知左右街道录院事掌道录院教事。", staff_type="道官")
    touched.update((old_eid, eid))
    finish(w, touched, "整理知左右街道录院事改名与复旧时间链。")


def entry532():
    i, main = 532, F[532]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制与品位"), field(i, "简称"),
    )
    w = W(i)
    eid, south = exact_state(
        w, i, "左右街都道录", "官职", "南宋",
        "南宋复置，总知道士、女冠教门公事，一人，位在左、右街道录之上",
        history, "中央道官", "建立南宋左右街都道录节点。", "职源与沿革",
        officer="道官",
    )
    cite(w, "Timepoints", south, i, duty, "补充总知教门职掌。", "职掌")
    cite(w, "Timepoints", south, i, roster, "补充一人定额与位次。", "编制与品位")
    _, shaoxing = exact_state(
        w, i, "左右街都道录", "官职", "南宋绍兴二十年",
        "改授左右街都道录并仍领能真观事", aliases, "中央道官",
        "建立绍兴二十年授官实例节点。", "简称", officer="道官",
    )
    alias_note(w, i, south, aliases, "简称")
    staff(w, i, tp(w, "左、右街道录院", "机构", "南宋"), south,
          roster, "南宋道录院置左右街都道录一人。", "编制与品位",
          quota=1, staff_type="都道录")
    finish(w, {eid}, "整理左右街都道录南宋复置与授官时间链。")


def entry533():
    i, main = 533, F[533]["text"]
    w = W(i)
    eid, old = exact_state(
        w, i, "副都道录", "官职", "北宋（政和八年前）",
        "位次都道录，分掌左、右街道录院教门事", main,
        "中央道官", "建立副都道录政和改名前节点。", officer="道官",
    )
    _, restored = exact_state(
        w, i, "副都道录", "官职", "北宋宣和七年",
        "由同知左右街道录院事复旧名", main, "中央道官",
        "建立宣和七年复旧名节点。", officer="道官",
    )
    finish(w, {eid}, "整理副都道录改名与复旧时间链。")


def entry534():
    i, main = 534, F[534]["text"]
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, "副都道录", "官职", "北宋政和八年",
        "改名同知左右街道录院事", main, "中央道官",
        "建立副都道录改名起点。", officer="道官",
    )
    eid, renamed = exact_state(
        w, i, "同知左右街道录院事", "官职", "北宋政和八年",
        "由副都道录改名", main, "中央道官",
        "建立同知左右街道录院事改名节点。", officer="道官",
    )
    relation(w, i, old, renamed, "前后演变", main,
             "政和八年副都道录改名同知左右街道录院事。")
    _, ended = exact_state(
        w, i, "同知左右街道录院事", "官职", "北宋宣和七年",
        "复旧名副都道录", main, "中央道官",
        "建立宣和七年复旧节点。", officer="道官",
    )
    relation(w, i, ended, tp(w, "副都道录", "官职", "北宋宣和七年"),
             "前后演变", main, "宣和七年复旧名副都道录。")
    staff(w, i, tp(w, "左、右街道录院", "机构", "北宋政和六年"), renamed,
          main, "同知左右街道录院事分掌道录院教事。", staff_type="道官")
    touched.update((old_eid, eid))
    finish(w, touched, "整理同知左右街道录院事改名与复旧时间链。")


def entry535():
    placeholder(535)


def entry536():
    i, main, aliases = 536, F[536]["text"], field(536, "简称")
    w = W(i)
    eid, early = exact_state(
        w, i, "左街道录", "官职", "宋初",
        "北宋初为道官之首，后位次都道录、副都道录，仍在右街道录之上",
        main, "中央道官", "建立左街道录宋初位次节点。", officer="道官",
    )
    _, later = exact_state(
        w, i, "左街道录", "官职", "北宋（增置都、副道录后）",
        "位次都道录、副都道录，参掌道教事", main, "中央道官",
        "建立增置都、副道录后的位次节点。", officer="道官",
    )
    _, restored = exact_state(
        w, i, "左街道录", "官职", "北宋宣和七年",
        "由知左街道录院事复旧名", main, "中央道官",
        "建立宣和七年复旧名节点。", officer="道官",
    )
    alias_note(w, i, early, aliases, "简称")
    finish(w, {eid}, "整理左街道录位次、改名与复旧时间链。")


def entry537():
    i, main = 537, F[537]["text"]
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, "左街道录", "官职", "北宋政和八年",
        "改名知左街道录院事", main, "中央道官",
        "建立左街道录改名起点。", officer="道官",
    )
    eid, renamed = exact_state(
        w, i, "知左街道录院事", "官职", "北宋政和八年",
        "由左街道录改名", main, "中央道官",
        "建立知左街道录院事改名节点。", officer="道官",
    )
    relation(w, i, old, renamed, "前后演变", main,
             "政和八年左街道录改名知左街道录院事。")
    _, ended = exact_state(
        w, i, "知左街道录院事", "官职", "北宋宣和七年",
        "复旧名左街道录", main, "中央道官",
        "建立宣和七年复旧节点。", officer="道官",
    )
    relation(w, i, ended, tp(w, "左街道录", "官职", "北宋宣和七年"),
             "前后演变", main, "宣和七年复旧名左街道录。")
    staff(w, i, tp(w, "左、右街道录院", "机构", "北宋政和六年"), renamed,
          main, "知左街道录院事参掌道录院教事。", staff_type="道官")
    touched.update((old_eid, eid))
    finish(w, touched, "整理知左街道录院事改名与复旧时间链。")


def entry538():
    placeholder(538)


def entry539():
    i, main, duty = 539, F[539]["text"], field(539, "职掌")
    w = W(i)
    eid, early = exact_state(
        w, i, "右街道录", "官职", "北宋元丰三年十月",
        "位次左街道录，分掌黄冠道流宫观山门事，并请定补道职考试经目与科义",
        main, "中央道官", "建立元丰三年右街道录职掌节点。", officer="道官",
    )
    cite(w, "Timepoints", early, i, duty, "补充右街道录分掌与奏请考试内容。", "职掌")
    _, restored = exact_state(
        w, i, "右街道录", "官职", "北宋宣和七年",
        "由知右街道录院事复旧名", main, "中央道官",
        "建立宣和七年复旧名节点。", officer="道官",
    )
    finish(w, {eid}, "整理右街道录职掌、改名与复旧时间链。")


def entry540():
    i, main = 540, F[540]["text"]
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, "右街道录", "官职", "北宋政和八年",
        "改名知右街道录院事", main, "中央道官",
        "建立右街道录改名起点。", officer="道官",
    )
    eid, renamed = exact_state(
        w, i, "知右街道录院事", "官职", "北宋政和八年",
        "由右街道录改名", main, "中央道官",
        "建立知右街道录院事改名节点。", officer="道官",
    )
    relation(w, i, old, renamed, "前后演变", main,
             "政和八年右街道录改名知右街道录院事。")
    _, ended = exact_state(
        w, i, "知右街道录院事", "官职", "北宋宣和七年",
        "复旧名右街道录", main, "中央道官",
        "建立宣和七年复旧节点。", officer="道官",
    )
    relation(w, i, ended, tp(w, "右街道录", "官职", "北宋宣和七年"),
             "前后演变", main, "宣和七年复旧名右街道录。")
    staff(w, i, tp(w, "左、右街道录院", "机构", "北宋政和六年"), renamed,
          main, "知右街道录院事参掌道录院教事。", staff_type="道官")
    touched.update((old_eid, eid))
    finish(w, touched, "整理知右街道录院事改名与复旧时间链。")


def main():
    assert [F[i]["title"] for i in range(521, 541)] == [
        "道录院", "左、右街道录院", "道德院", "提举秘书省左右街道录院",
        "道录司", "道正司", "道正", "副道正", "山门道正司", "都道录",
        "知左右街道录院事", "左右街都道录", "副都道录",
        "同知左右街道录院事", "同知", "左街道录", "知左街道录院事",
        "都道", "右街道录", "知右街道录院事",
    ]
    for i in range(521, 541):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
