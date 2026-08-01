#!/usr/bin/env python3
"""提取 chapter5t7 第541-560条：左右街道官、宫观提点所与司农寺。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_521_540 as previous


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


F = {i: load(i) for i in range(541, 561)}
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
    "北齐": 550, "后周显德间": 955, "北宋建隆元年": 960,
    "宋初": 960.1, "宋前期": 980,
    "北宋太平兴国六年十月": 981.8,
    "北宋大中祥符初": 1008, "北宋大中祥符二年八月": 1009.62,
    "北宋天圣初": 1023, "北宋天禧五年至次年": 1021.5,
    "北宋（建隆观置所年月未载）": 1000,
    "宋代（道官体系）": 1050, "北宋治平三年": 1066,
    "北宋熙宁三年五月十七日": 1070.38,
    "北宋熙宁三年至元丰五年": 1075,
    "北宋熙宁五年": 1072, "北宋熙宁六年": 1073,
    "北宋熙宁九年": 1076, "北宋元丰四年": 1081,
    "北宋元丰新制": 1082, "北宋（政和八年前）": 1100,
    "北宋真宗朝": 1010, "北宋徽宗朝": 1105,
    "北宋政和八年": 1118, "北宋宣和七年": 1125,
    "南宋建炎三年四月十三日": 1129.28,
    "南宋绍兴三年十月二十九日": 1133.83,
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


def flag_relationship_citations(w, relationship_ids, note):
    for rid in relationship_ids:
        rows = w.conn.execute(
            "select id,conflict_flag,note from Citations "
            "where target_table='Relationships' and target_id=?", (rid,)
        ).fetchall()
        assert rows, rid
        for cid, flag, old_note in rows:
            if flag != 1 or old_note != note:
                w.conn.execute(
                    "update Citations set conflict_flag=1,note=? where id=?",
                    (note, cid),
                )
                w._br("Citations", cid, f"标记编制定额冲突：{note}")


def old_taoist_post(i, title, rank_event, *, aliases=None, examples=()):
    main = F[i]["text"]
    w = W(i)
    eid, old = exact_state(
        w, i, title, "官职", "北宋（政和八年前）", rank_event,
        main, "中央道官", f"建立{title}政和改名前位次与职掌。", officer="道官",
    )
    _, restored = exact_state(
        w, i, title, "官职", "北宋宣和七年",
        f"由政和新名复旧为{title}", main, "中央道官",
        f"建立{title}宣和七年复旧名节点。", officer="道官",
    )
    for time, event, quotation, field_name in examples:
        _, example = exact_state(
            w, i, title, "官职", time, event, quotation, "中央道官",
            f"建立{title}{time}任官实例。", field_name, officer="道官",
        )
    if aliases:
        alias_note(w, i, old, aliases, "简称")
    finish(w, {eid}, f"整理{title}位次、任官与复旧时间链。")


def renamed_taoist_post(i, old_title, new_title):
    main = F[i]["text"]
    w, touched = W(i), set()
    old_eid, old = exact_state(
        w, i, old_title, "官职", "北宋政和八年",
        f"改名{new_title}", main, "中央道官",
        f"建立{old_title}政和八年改名起点。", officer="道官",
    )
    eid, renamed = exact_state(
        w, i, new_title, "官职", "北宋政和八年",
        f"由{old_title}改名", main, "中央道官",
        f"建立{new_title}改名节点。", officer="道官",
    )
    relation(w, i, old, renamed, "前后演变", main,
             f"政和八年{old_title}改名{new_title}。")
    _, ended = exact_state(
        w, i, new_title, "官职", "北宋宣和七年",
        f"复旧名{old_title}", main, "中央道官",
        f"建立{new_title}宣和七年复旧节点。", officer="道官",
    )
    relation(w, i, ended, tp(w, old_title, "官职", "北宋宣和七年"),
             "前后演变", main, f"宣和七年{new_title}复旧名{old_title}。")
    staff(w, i, tp(w, "左、右街道录院", "机构", "北宋政和六年"), renamed,
          main, f"{new_title}参掌道录院教事。", staff_type="道官")
    touched.update((old_eid, eid))
    finish(w, touched, f"整理{old_title}与{new_title}改名、复旧完整时间链。")


def entry541():
    old_taoist_post(541, "左街副道录", "位次右街道录，参掌教事")


def entry542():
    renamed_taoist_post(542, "左街副道录", "同知左街道录院事")


def entry543():
    old_taoist_post(543, "右街副道录", "位次左街副道录，参掌教事")


def entry544():
    renamed_taoist_post(544, "右街副道录", "同知右街道录院事")


def entry545():
    i, aliases = 545, field(545, "简称")
    old_taoist_post(
        i, "左街都监", "位次道录，参掌教事", aliases=aliases,
        examples=((
            "北宋天圣初", "由右街都监迁左街都监，加大法师",
            aliases, "简称",
        ),),
    )


def entry546():
    renamed_taoist_post(546, "左街都监", "签书左街道录院事")


def entry547():
    i, aliases = 547, field(547, "简称")
    old_taoist_post(i, "右街都监", "位次左街都监，参掌教事", aliases=aliases)


def entry548():
    renamed_taoist_post(548, "右街都监", "签书右街道录院事")


def entry549():
    i, aliases = 549, field(549, "简称")
    old_taoist_post(i, "左街副都监", "位次右街都监，参掌教事", aliases=aliases)


def entry550():
    renamed_taoist_post(550, "左街副都监", "同签书左街道录院事")


def entry551():
    i, aliases = 551, field(551, "简称")
    old_taoist_post(i, "右街副都监", "位次左街副都监，参掌教事", aliases=aliases)


def entry552():
    renamed_taoist_post(552, "右街副都监", "同签书右街道录院事")


def entry553():
    i, main = 553, F[553]["text"]
    w, touched = W(i), set()
    eid, group = exact_state(
        w, i, "道官", "官职", "宋代（道官体系）",
        "宋代道官统称：中央由道录院辖左右街道官，地方州军置道正",
        main, "道官统称", "建立宋代道官统称节点。", officer="道官",
    )
    for title in (
        "都道录", "副都道录", "左街道录", "右街道录",
        "左街副道录", "右街副道录", "道录院首座", "道录院都监",
        "道录院鉴义", "道正",
    ):
        seid, instance = exact_state(
            w, i, title, "官职", "宋代（道官体系）",
            "宋代道官体系的具体道职", main, "道官",
            f"据道官条建立{title}实例状态。", officer="道官",
        )
        relation(w, i, group, instance, "统称与实例", main,
                 f"{title}是宋代道官的具体实例。")
        touched.add(seid)
    _, zhenzong = exact_state(
        w, i, "道官", "官职", "北宋真宗朝",
        "真宗置道教宫观使，以宰相兼任，掌奉斋醮",
        main, "道官统称", "建立真宗朝宫观使道官节点。", officer="道官",
    )
    for title in ("玉清宫使", "昭应宫使", "景灵宫使", "会灵观使"):
        seid, instance = exact_state(
            w, i, title, "官职", "北宋真宗朝",
            "由宰相兼任，掌奉斋醮", main, "道教宫观使",
            f"建立{title}兼任与职掌节点。", officer="宫观使",
        )
        relation(w, i, zhenzong, instance, "统称与实例", main,
                 f"{title}是宋真宗朝道官实例。")
        touched.add(seid)
    _, huizong = exact_state(
        w, i, "道官", "官职", "北宋徽宗朝",
        "徽宗提高道官地位，改道教事由祠部隶秘书省，并置道阶、道科",
        main, "道官统称", "建立徽宗朝道官制度节点。", officer="道官",
    )
    supervisor_eid, supervisor = exact_state(
        w, i, "提举秘书省道录院", "官职", "北宋徽宗朝",
        "蔡攸受命提举秘书省并左右街道籙院", main, "中央道官",
        "补充徽宗朝提举道录院实例。", officer="提举官",
    )
    relation(w, i, huizong, supervisor, "统称与实例", main,
             "提举秘书省道录院是徽宗朝道官实例。")
    touched.update((eid, supervisor_eid))
    finish(w, touched, "整理道官统称、中央地方实例及宫观使完整时间链。")


def honglu_office(i, office_title, office_time, office_event, parent_title,
                  parent_event, origin, duty, *, predecessor=None):
    main = F[i]["text"]
    w, touched = W(i), set()
    parent_eid, parent = exact_state(
        w, i, parent_title, "机构", office_time, parent_event, origin,
        "道教宫观或寺院", f"建立{parent_title}相关历史节点。", "职源",
    )
    eid, office = exact_state(
        w, i, office_title, "机构", office_time, office_event, origin,
        "鸿胪寺属宫观提点所", f"建立{office_title}节点。", "职源",
    )
    cite(w, "Timepoints", office, i, duty, f"补充{office_title}职掌。", "职掌")
    relation(w, i, parent, office, "上下级机构", origin,
             f"{office_title}为{parent_title}提点官办事机构。", "职源")
    honglu_eid, honglu = exact_state(
        w, i, "鸿胪寺", "机构", office_time, f"统辖{office_title}", main,
        "九寺", f"建立鸿胪寺统辖{office_title}节点。",
    )
    relation(w, i, honglu, office, "上下级机构", main,
             f"{office_title}隶鸿胪寺。")
    if predecessor:
        old_title, old_time, old_event, renamed_time, renamed_event = predecessor
        old_eid, old = exact_state(
            w, i, old_title, "机构", old_time, old_event, origin,
            "道教宫观", f"建立{old_title}前身节点。", "职源",
        )
        _, renamed_parent = exact_state(
            w, i, parent_title, "机构", renamed_time, renamed_event, origin,
            "道教宫观", f"建立{parent_title}改名节点。", "职源",
        )
        relation(w, i, old, renamed_parent, "前后演变", origin,
                 f"{old_title}改名{parent_title}。", "职源")
        touched.add(old_eid)
    touched.update((parent_eid, eid, honglu_eid))
    finish(w, touched, f"整理{office_title}源流、隶属与职掌时间链。")


def entry554():
    i, origin, duty = 554, field(554, "职源"), field(554, "职掌")
    honglu_office(
        i, "提点中太一宫所", "北宋熙宁五年",
        "中太一宫建成后置提点官、提点所，掌屋宇、斋宫、器用仪物及币帛陈设",
        "中太一宫", "建于京师，归五岳观", origin, duty,
    )


def entry555():
    i, origin, duty = 555, field(555, "职源"), field(555, "职掌")
    honglu_office(
        i, "提点建隆观所", "北宋（建隆观置所年月未载）",
        "建隆观设置提点官、提点所，掌殿宇、斋宫、器用仪物与陈设",
        "建隆观", "观内设置提点官、提点所", origin, duty,
        predecessor=(
            "太清观", "后周显德间", "置于开封",
            "北宋建隆元年", "太清观改名建隆观，观内置道士住持",
        ),
    )


def entry556():
    i, origin, duty = 556, field(556, "职源"), field(556, "职掌")
    honglu_office(
        i, "提点资圣院所", "北宋天禧五年至次年",
        "资圣院建成并置提点官、提点司，掌屋宇、斋宫、器用仪物及币帛陈设",
        "资圣院", "为阵亡将士追福而置，次年建成", origin, duty,
    )


def entry557():
    i, main = 557, F[557]["text"]
    origin, duty, aliases = field(i, "职源"), field(i, "职掌"), field(i, "别称")
    w, touched = W(i), set()
    parent_eid, parent = exact_state(
        w, i, "崇真资圣院", "机构", "宋初", "已有此尼姑院",
        origin, "尼姑院", "建立崇真资圣院宋初节点。", "职源",
    )
    _, princess = exact_state(
        w, i, "崇真资圣院", "机构", "北宋大中祥符二年八月",
        "太宗女陈国长公主出家居此，赐号报慈正觉大师",
        origin, "尼姑院", "建立大中祥符二年公主居院节点。", "职源",
    )
    eid, office = exact_state(
        w, i, "提点崇真资圣禅院所", "机构", "北宋大中祥符二年八月",
        "设置提点官所，掌本院屋宇、斋宫、器用仪物及陈设",
        origin, "尼姑院提点所", "建立提点崇真资圣禅院所节点。", "职源",
    )
    cite(w, "Timepoints", office, i, duty, "补充提点所职掌。", "职掌")
    cite(w, "Timepoints", princess, i, aliases,
         "补充崇真资圣院俗称七公主院。", "别称")
    relation(w, i, princess, office, "上下级机构", origin,
             "提点崇真资圣禅院所为崇真资圣院提点官办事机构。", "职源")
    touched.update((parent_eid, eid))
    finish(w, touched, "整理崇真资圣院及提点所源流、职掌时间链。")


def entry558():
    assert F[558]["text"] == ""
    assert F[558]["fields"].get("_placeholder") is True


def entry559():
    i, main = 559, F[559]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    eid, origin = exact_state(
        w, i, "司农寺", "机构", "北齐", "司农寺之名始见",
        history, "九寺之一", "建立司农寺名称源流节点。", "职源与沿革",
    )
    _, early = exact_state(
        w, i, "司农寺", "机构", "宋前期",
        "沿置而职事多归三司，仅掌籍田祭祀供物、常平仓平籴利农等事",
        duty, "闲散寺监机构", "建立宋前期职掌节点。", "职掌",
    )
    _, reform = exact_state(
        w, i, "司农寺", "机构", "北宋熙宁三年至元丰五年",
        "事权大增，兼为财务和新法政务机构，督领各路提举常平司及官属",
        duty, "新法财务政务机构", "建立熙宁至元丰五年事权节点。", "职掌",
    )
    local_eid, local = exact_state(
        w, i, "诸路提举常平司", "机构", "北宋熙宁三年至元丰五年",
        "受司农寺督领，推行常平、免役、坊场、青苗、农田水利等法",
        duty, "路级新法机构", "建立诸路提举常平司受领节点。", "职掌",
    )
    relation(w, i, reform, local, "上下级机构", duty,
             "熙宁至元丰五年司农寺督领诸路提举常平司。", "职掌")
    _, new_system = exact_state(
        w, i, "司农寺", "机构", "北宋元丰新制",
        "依六典正名，不再治京师之外事，掌仓场出纳、园苑种植、上供禄粟支遣、酒曲薪炭与籍田等",
        duty, "仓场园苑主管机构", "建立元丰五年新制职掌节点。", "职掌",
    )
    right_eid, right = exact_state(
        w, i, "户部右曹", "机构", "北宋元丰新制",
        "接收司农寺旧有京外新法职事", duty, "户部所属曹",
        "补充户部右曹接收司农寺旧职节点。", "职掌",
    )
    relation(w, i, reform, right, "前后演变", duty,
             "元丰五年司农寺旧有京外新法职事并归户部右曹。", "职掌")
    _, abolished = exact_state(
        w, i, "司农寺", "机构", "南宋建炎三年四月十三日", "罢置",
        history, "九寺之一", "建立建炎三年罢置节点。", "职源与沿革",
    )
    _, restored = exact_state(
        w, i, "司农寺", "机构", "南宋绍兴三年十月二十九日", "复置",
        history, "九寺之一", "建立绍兴三年复置节点。", "职源与沿革",
    )
    alias_note(w, i, early, aliases, "简称与别名")
    touched.update((eid, local_eid, right_eid))

    for time, parent, specs in (
        ("宋前期", early, (
            ("判司农寺事", "官职", "判寺官", 1),
            ("常平案", "机构", "办事案", 1),
            ("司农寺府史", "官职", "府史", 1),
            ("司农寺驱使官", "官职", "驱使官", 4),
            ("常平案前行", "官职", "前行", 1),
            ("常平案后行", "官职", "后行", 8),
        )),
        ("北宋元丰四年", reform, (
            ("判司农寺事", "官职", "判寺官", 1),
            ("同判司农寺事", "官职", "同判寺官", 1),
            ("司农寺三局十二案", "机构", "三局十二案", 12),
            ("司农寺丞", "官职", "丞", 4),
            ("司农寺主簿", "官职", "主簿", 6),
        )),
        ("北宋元丰新制", new_system, (
            ("司农寺卿", "官职", "卿", 1),
            ("司农寺少卿", "官职", "少卿", 1),
            ("司农寺丞", "官职", "丞", 1),
            ("司农寺主簿", "官职", "主簿", 1),
            ("司农寺六案", "机构", "办事案", 6),
            ("司农寺粮仓", "机构", "粮仓", 24),
            ("司农寺草场", "机构", "草场", 10),
            ("司农寺排岸司", "机构", "排岸司", 4),
            ("司农寺园苑", "机构", "园苑", 4),
            ("下卸司", "机构", "所属机构", None),
            ("都曲院", "机构", "所属机构", None),
            ("水磨务", "机构", "所属机构", None),
            ("内柴炭库", "机构", "所属机构", None),
            ("炭场", "机构", "所属机构", None),
        )),
    ):
        for title, type_, officer, quota in specs:
            event = (
                "宋前期掌领司农寺的判寺官"
                if title == "判司农寺事" and time == "宋前期"
                else f"司农寺{time}所置{officer}"
                     + (f"，编制{quota}" if quota else "")
            )
            seid, child = exact_state(
                w, i, title, type_, time, event,
                roster, "司农寺属员" if type_ == "官职" else "司农寺所属机构",
                f"建立{title}{time}编制。", "编制",
                officer=officer if type_ == "官职" else None,
            )
            if type_ == "机构":
                relation(w, i, parent, child, "上下级机构", roster,
                         f"{title}为司农寺{time}所属机构。", "编制")
            else:
                staff(w, i, parent, child, roster,
                      f"司农寺{time}置{officer}" + (f"{quota}人。" if quota else "。"),
                      "编制", quota=quota, staff_type=officer)
            touched.add(seid)

    registry_eid, registry = exact_state(
        w, i, "司农寺主簿", "官职", "北宋治平三年",
        "始置一员", roster, "司农寺属官",
        "建立治平三年司农寺主簿始置与定额。", "编制", officer="主簿",
    )
    staff(w, i, early, registry, roster, "治平三年司农寺置主簿一人。",
          "编制", quota=1, staff_type="主簿")
    touched.add(registry_eid)

    clerk_eid, clerk = exact_state(
        w, i, "司农寺勾当公事官", "官职", "北宋熙宁六年",
        "始置，参与司农寺新法事务", roster, "司农寺属官",
        "建立熙宁六年勾当公事官始置节点。", "编制", officer="勾当公事官",
    )
    _, clerk_ended = exact_state(
        w, i, "司农寺勾当公事官", "官职", "北宋熙宁九年", "罢置",
        roster, "司农寺属官", "建立熙宁九年罢置节点。", "编制", officer="勾当公事官",
    )
    staff(w, i, reform, clerk, roster, "熙宁六年司农寺置勾当公事官。",
          "编制", staff_type="勾当公事官")
    touched.add(clerk_eid)
    finish(w, touched, "整理司农寺源流、职权、存废、属官与所属机构完整时间链。")


def entry560():
    i, main, aliases = 560, F[560]["text"], field(560, "简称与别名")
    w = W(i)
    eid, early = exact_state(
        w, i, "判司农寺事", "官职", "宋前期",
        "宋前期掌领司农寺的判寺官",
        main, "司农寺主判官", "建立宋前期判司农寺事任用、定额与职掌。",
        officer="差遣官",
    )
    parent = tp(w, "司农寺", "机构", "宋前期")
    two_rid = staff(
        w, i, parent, early, main,
        "宋前期司农寺差文臣二员判寺事。", quota=2, staff_type="判寺官",
    )
    one_rids = [
        row[0] for row in w.conn.execute(
            "select id from Relationships where subject_id=? and object_id=? "
            "and relation_type='编制隶属' and staff_quota=1", (parent, early)
        )
    ]
    assert len(one_rids) == 1, one_rids
    conflict_note = (
        "第559条编制字段称宋前期判司农寺官一人；第560条正文与引文称"
        "朝官以上文臣二员判寺事。两说并存，暂不裁决。"
    )
    flag_relationship_citations(w, one_rids + [two_rid], conflict_note)
    _, reform = exact_state(
        w, i, "判司农寺事", "官职", "北宋熙宁三年五月十七日",
        "新法付司农寺后，判寺官事权渐重", main, "司农寺主判官",
        "建立熙宁三年事权加重节点。", officer="差遣官",
    )
    staff(w, i, tp(w, "司农寺", "机构", "北宋熙宁三年至元丰五年"), reform,
          main, "新法付司农寺后判寺官掌领本寺。", staff_type="判寺官")
    alias_note(w, i, early, aliases, "简称与别名")
    finish(w, {eid}, "整理判司农寺事宋前期至熙宁新法时期完整时间链。")


def main():
    assert [F[i]["title"] for i in range(541, 561)] == [
        "左街副道录", "同知左街道录院事", "右街副道录",
        "同知右街道录院事", "左街都监", "签书左街道录院事",
        "右街都监", "签书右街道录院事", "左街副都监",
        "同签书左街道录院事", "右街副都监", "同签书右街道录院事",
        "道官", "提点中太一宫所", "提点建隆观所", "提点资圣院所",
        "提点崇真资圣禅院所", "提点", "司农寺", "判司农寺事",
    ]
    for i in range(541, 561):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
