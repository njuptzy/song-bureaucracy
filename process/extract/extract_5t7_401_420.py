#!/usr/bin/env python3
"""提取 chapter5t7 第401-420条：六统军、太仆寺与飞龙、天厩、骐骥院。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_381_400 as previous


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


F = {i: load(i) for i in range(401, 421)}
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
    "西周穆王时": -950, "秦汉": -221, "后汉": 25,
    "南朝梁天监七年": 508, "北齐": 550, "隋初": 581,
    "唐代": 618, "唐贞观中": 627, "唐万岁通天元年": 696,
    "唐开元二十六年": 738, "唐肃宗至德二年": 757,
    "唐兴元元年正月二十九日": 784.08,
    "五代后唐长兴元年": 930,
    "宋代": 960, "宋代（六军仪仗司）": 960.08,
    "宋初": 960.1, "北宋初": 960.2, "宋前期": 970,
    "北宋太平兴国五年正月七日": 980.02,
    "北宋雍熙二年十月十六日": 985.79,
    "北宋咸平三年九月十一日以前": 1000.68,
    "北宋咸平三年九月十一日": 1000.69,
    "北宋咸平三年九月十一日以后": 1000.70,
    "北宋元丰新制": 1080.1,
    "北宋元丰五年新制": 1082.01,
    "北宋元丰五年五月一日": 1082.34,
    "北宋元丰改制后": 1082.4,
    "北宋哲宗朝": 1085,
    "北宋元祐元年八月六日": 1086.60,
    "北宋元祐三年": 1088,
    "北宋崇宁二年": 1103,
    "南宋建炎三年四月十三日": 1129.29,
    "南宋": 1127, "南宋绍兴间": 1140,
    "南宋淳熙十四年": 1187,
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


def army_pair(i, pair, left, right, tang_states):
    main = F[i]["text"]
    w = W(i)
    touched = set()
    for time, event in tang_states:
        peid, pair_node = exact_state(
            w, i, pair, "机构", time, event, main,
            "禁军番号统称", f"建立{pair}的{time}节点。",
        )
        touched.add(peid)
        for title in (left, right):
            eid, member = exact_state(
                w, i, title, "机构", time,
                f"{pair}所含{title}番号", main,
                "禁军番号", f"建立{title}的{time}节点。",
            )
            relation(w, i, pair_node, member, "统称与实例", main,
                     f"{title}为{pair}实例。")
            touched.add(eid)
    peid, song = exact_state(
        w, i, pair, "机构", "宋代（六军仪仗司）",
        "沿置局名，无常备军，应奉朝会、郊祀大礼并排办六军仪仗",
        main, "仪仗军号统称", f"补足宋代{pair}的性质与职掌。",
    )
    touched.add(peid)
    for title in (left, right):
        member = tp(w, title, "机构", "宋代（六军仪仗司）")
        relation(w, i, song, member, "统称与实例", main,
                 f"{title}为宋代{pair}实例。")
    for title in ("都头", "排仗官"):
        staff(w, i, song, tp(w, title, "官职", "宋代（六军仪仗司）"),
              main, f"宋代{pair}设置{title}。", staff_type=title)
    for eid in touched:
        rechain(w, eid, f"整理{pair}及左右实例的完整时间链。")
    w.commit()


def commander_pair(i, pair, left, right, army_pair_title):
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    touched = set()
    peid, tang = exact_state(
        w, i, pair, "官职", "唐兴元元年正月二十九日",
        "始置，为从二品", main, "六军统军合称",
        f"建立唐代{pair}始置节点。", officer="统军", grade="从二品",
    )
    _, song = exact_state(
        w, i, pair, "官职", "宋代（六军仪仗司）",
        "宋沿置，多为排办六军仪仗临时差摄，左右各一员",
        main, "六军仪仗武官合称", f"建立宋代{pair}差摄节点。",
        officer="统军差摄",
    )
    touched.add(peid)
    for title in (left, right):
        eid, post = exact_state(
            w, i, title, "官职", "宋代（六军仪仗司）",
            f"{title}，排办六军仪仗时临时差摄", aliases,
            "六军仪仗武官", f"建立{title}实例。", "简称",
            officer="统军差摄",
        )
        relation(w, i, song, post, "统称与实例", aliases,
                 f"{title}为{pair}实例。", "简称")
        touched.add(eid)
    staff(w, i, tp(w, army_pair_title, "机构", "宋代（六军仪仗司）"),
          song, aliases, f"宋代{army_pair_title}置{pair}二员。", "简称",
          quota=2, staff_type="统军差摄")
    alias_note(w, i, song, aliases, "简称")
    for eid in touched:
        rechain(w, eid, f"整理{pair}及左右实例时间链。")
    w.commit()


def entry401():
    army_pair(
        401, "左、右龙武军", "左龙武军", "右龙武军",
        [("唐贞观中", "始置左、右龙武军番号")],
    )


def entry402():
    commander_pair(
        402, "左、右龙武统军", "左龙武军统军", "右龙武军统军",
        "左、右龙武军",
    )


def entry403():
    army_pair(
        403, "左、右神武军", "左神武军", "右神武军",
        [
            ("唐开元二十六年", "由左、右羽林军分置，后曾罢"),
            ("唐肃宗至德二年", "复置左、右神武军"),
        ],
    )
    i, main = 403, F[403]["text"]
    w = W(i)
    relation(
        w, i,
        tp(w, "左、右羽林军", "机构", "唐龙朔二年"),
        tp(w, "左、右神武军", "机构", "唐开元二十六年"),
        "前后演变", main, "唐开元二十六年分左、右羽林军置左、右神武军。",
    )
    w.commit()


def entry404():
    commander_pair(
        404, "左、右神武军统军", "左神武军统军", "右神武军统军",
        "左、右神武军",
    )


def entry405():
    i, main = 405, F[405]["text"]
    w = W(i)
    eid, soldiers = exact_state(
        w, i, "喝探", "官职", "宋代（六军仪仗司）",
        "夜间禁更仪卫兵士，十余队围列唱和，自初更至五更传喝五使名",
        main, "六军仪仗司兵士", "补足喝探的南宋禁更仪卫职掌。", officer="兵士",
    )
    staff(w, i, tp(w, "六军仪仗司", "机构", "北宋"), soldiers,
          main, "六军仪仗司设置喝探兵士。", staff_type="兵士")
    rechain(w, eid, "整理喝探在金吾引驾仗司与六军仪仗司的完整时间链。")
    w.commit()


def entry406():
    i, main = 406, F[406]["text"]
    w = W(i)
    eid, soldiers = exact_state(
        w, i, "警场", "官职", "南宋",
        "又称武严兵士，大礼车驾宿斋殿时在丽正门外执画鼓、画角奏严，约二百人",
        main, "六军仪仗司兵士", "建立南宋警场戒严仪卫节点。", officer="兵士",
    )
    staff(w, i, tp(w, "六军仪仗司", "机构", "北宋"), soldiers,
          main, "六军仪仗司所隶警场兵士约二百人。",
          quota=200, staff_type="兵士")
    rechain(w, eid, "整理警场六军仪仗司属员与南宋戒严职掌时间链。")
    w.commit()


def entry407():
    i, main = 407, F[407]["text"]
    w = W(i)
    eid, armies = exact_state(
        w, i, "六军", "机构", "宋代（六军仪仗司）",
        "左、右羽林、龙武、神武六军合称，置统军、大将军、将军等官而不常置",
        main, "仪仗军号统称", "补足宋代六军定义与置官性质。",
        note="‘六军’泛指禁军的词义只作释名，不另建实体关系",
    )
    cite(w, "Timepoints", armies, i, main,
         "‘六军’泛指禁军的用法只作语词释义，不另建机构实体。",
         note="泛称词义，不等同于具体编制关系")
    rechain(w, eid, "整理六军唐宋时间链。")
    w.commit()


def entry408():
    i, main = 408, F[408]["text"]
    w = W(i)
    eid, generic = exact_state(
        w, i, "六统军", "官职", "宋代（六军仪仗司）",
        "左、右羽林军统军、左、右龙武军统军、左、右神武军统军总称",
        main, "六军统军合称", "建立六统军及其六个实例。", officer="统军合称",
    )
    six_armies = tp(w, "六军", "机构", "宋代（六军仪仗司）")
    staff(w, i, six_armies, generic, main, "宋代六军所置六统军。",
          quota=6, staff_type="统军")
    for title in (
        "左、右羽林军统军", "左、右龙武统军", "左、右神武军统军",
    ):
        node = tp(w, title, "官职", "宋代（六军仪仗司）")
        relation(w, i, generic, node, "统称与实例", main,
                 f"{title}为六统军所指实例组。")
    for title in (
        "左羽林军统军", "右羽林军统军", "左龙武军统军",
        "右龙武军统军", "左神武军统军", "右神武军统军",
    ):
        node = tp(w, title, "官职", "宋代（六军仪仗司）")
        relation(w, i, generic, node, "统称与实例", main,
                 f"{title}为六统军所指具体实例。")
    rechain(w, eid, "整理六统军时间链。")
    w.commit()


def entry409():
    i = 409
    history = field(i, "职掌与沿革")
    duty, roster, aliases = (
        field(i, "职掌"), field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, qing = exact_state(
        w, i, "太仆寺", "机构", "北齐", "始置太仆寺",
        history, "马政寺监", "建立太仆寺北齐职源。", "职掌与沿革",
    )
    _, early = exact_state(
        w, i, "太仆寺", "机构", "宋前期",
        "沿置，掌皇帝及后妃王公车辂、祭祀牲畜供应，其余厩牧车舆分隶别司",
        duty, "马政寺监", "建立宋前期太仆寺职掌。", "职掌",
    )
    _, reform = exact_state(
        w, i, "太仆寺", "机构", "北宋元丰五年五月一日",
        "元丰正名承接群牧司职事，统掌内外厩牧、车舆政令",
        duty, "马政寺监", "补足元丰太仆寺职权。", "职掌",
    )
    _, reduced = exact_state(
        w, i, "太仆寺", "机构", "北宋崇宁二年",
        "京师外马政、车舆事务拨归枢密院与尚书驾部",
        duty, "马政寺监", "建立崇宁二年职权调整节点。", "职掌",
    )
    _, abolished = exact_state(
        w, i, "太仆寺", "机构", "南宋建炎三年四月十三日",
        "罢太仆寺，职事并归兵部驾部",
        history, "马政寺监", "建立建炎三年罢寺节点。", "职掌与沿革",
    )
    relation(w, i, tp(w, "群牧司", "机构", "北宋元丰五年五月一日"),
             reform, "前后演变", duty, "元丰罢群牧司，职事归太仆寺。", "职掌")
    relation(w, i, abolished, tp(w, "驾部", "机构", "南宋中兴以来"),
             "前后演变", history, "建炎三年太仆寺职事并归兵部驾部。",
             "职掌与沿革")
    touched.add(eid)

    cases_eid, cases = exact_state(
        w, i, "太仆寺五案", "机构", "北宋元丰改制后",
        "太仆寺分设五案", roster, "太仆寺办事机构统称",
        "建立元丰新制太仆寺五案。", "编制",
    )
    relation(w, i, reform, cases, "上下级机构", roster,
             "元丰新制太仆寺分案五。", "编制")
    clerks_eid, clerks = exact_state(
        w, i, "太仆寺吏", "官职", "北宋元丰改制后",
        "太仆寺置吏十八人", roster, "太仆寺公吏统称",
        "建立元丰新制太仆寺吏定额。", "编制", officer="吏人",
    )
    staff(w, i, reform, clerks, roster, "元丰新制太仆寺置吏十八人。", "编制",
          quota=18, staff_type="吏人")
    touched.update((cases_eid, clerks_eid))

    for title in (
        "车辂院", "左、右骐骥院", "左、右天驷监", "鞍辔库",
        "养象所", "驼坊", "车营", "致远务", "牧养上、下监",
        "左右天厩坊", "孳生监",
    ):
        subordinate_event = (
            "改隶太仆寺，继续领坊监国马饲养"
            if title == "左、右骐骥院"
            else "太仆寺元丰新制所辖局之一"
        )
        seid, subordinate = exact_state(
            w, i, title, "机构", "北宋元丰改制后",
            subordinate_event, roster,
            "太仆寺属局", f"建立太仆寺所辖{title}。", "编制",
        )
        relation(w, i, reform, subordinate, "上下级机构", roster,
                 f"元丰新制太仆寺下辖{title}。", "编制")
        touched.add(seid)

    judge_eid, judge = exact_state(
        w, i, "判太仆寺事", "官职", "宋前期",
        "以朝官以上充，一人，掌皇帝辇舆、后妃王公车辂及大中小祀牲畜", roster,
        "太仆寺判寺官", "建立宋前期判太仆寺事编制。", "编制", officer="判寺官",
    )
    staff(w, i, early, judge, roster, "宋前期太仆寺置判寺官一人。", "编制",
          quota=1, staff_type="判寺官")
    touched.add(judge_eid)
    post_specs = (
        ("太仆寺卿", "北宋元丰新制", "寺卿", 1,
         "本寺长官，掌车辂、厩马政令，一员，从四品"),
        ("太仆寺少卿", "北宋元丰五年新制", "少卿", 1,
         "本寺副贰，佐正卿总马政，一人，正六品"),
        ("太仆寺丞", "北宋元丰新制", "寺丞", 1,
         "参领本寺事，一人，正八品"),
        ("太仆寺主簿", "北宋元丰新制", "主簿", 1,
         "掌勾考本寺簿书，从八品"),
    )
    for title, time, staff_type, quota, event in post_specs:
        peid, post = exact_state(
            w, i, title, "官职", time,
            event, roster,
            "太仆寺职事官", f"建立元丰新制{title}编制。", "编制",
            officer=staff_type,
        )
        staff(w, i, reform, post, roster, f"元丰新制太仆寺置{title}一人。", "编制",
              quota=quota, staff_type=staff_type)
        touched.add(peid)
    for time, event, quota in (
        ("北宋哲宗朝", "太仆寺主簿增为二员", 2),
        ("北宋元祐三年", "罢太仆寺主簿一员，复为一员", 1),
    ):
        _, office_node = exact_state(
            w, i, "太仆寺", "机构", time, event, roster,
            "马政寺监", f"建立{time}太仆寺编制节点。", "编制",
        )
        _, post = exact_state(
            w, i, "太仆寺主簿", "官职", time, event, roster,
            "太仆寺职事官", f"建立{time}太仆寺主簿定额节点。", "编制",
            officer="主簿",
        )
        staff(w, i, office_node, post, roster, event, "编制",
              quota=quota, staff_type="主簿")
    alias_note(w, i, reform, aliases, "简称与别名")
    for entity_id in touched:
        rechain(w, entity_id, "整理太仆寺、属局与职官完整时间链。")
    rechain(w, w.find_entity("太仆寺主簿", "官职"), "整理太仆寺主簿定额时间链。")
    w.commit()


def entry410():
    i, main, aliases = 410, F[410]["text"], field(410, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "判太仆寺事", "官职", "宋前期",
        "以朝官以上充，一人，掌皇帝辇舆、后妃王公车辂及大中小祀牲畜",
        main, "太仆寺判寺官", "补足判太仆寺事任用、定额与职掌。",
        officer="朝官以上差遣",
    )
    staff(w, i, tp(w, "太仆寺", "机构", "宋前期"), post, main,
          "宋前期太仆寺置判寺事一人。", quota=1, staff_type="朝官以上差遣")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理判太仆寺事时间链。")
    w.commit()


def entry411():
    i, main = 411, F[411]["text"]
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    source_eid, source = exact_state(
        w, i, "太仆正", "官职", "西周穆王时", "太仆正职名已见",
        history, "太仆寺卿职源", "建立西周太仆正职源。", "职源与沿革", officer="太仆正",
    )
    name_eid, han = exact_state(
        w, i, "太仆卿", "官职", "后汉", "太仆卿之称已见，卿字未必入衔",
        history, "太仆寺卿职源", "建立后汉太仆卿称谓节点。", "职源与沿革", officer="太仆卿",
    )
    _, liang = exact_state(
        w, i, "太仆卿", "官职", "南朝梁天监七年", "太仆卿正式成为官衔",
        history, "太仆寺卿职源", "建立梁天监七年太仆卿官衔节点。", "职源与沿革", officer="太仆卿",
    )
    eid, qing = exact_state(
        w, i, "太仆寺卿", "官职", "北齐", "始置太仆寺卿",
        history, "太仆寺长官", "建立北齐太仆寺卿节点。", "职源与沿革", officer="寺卿",
    )
    _, early = exact_state(
        w, i, "太仆寺卿", "官职", "宋前期",
        "无职事，为文臣寄禄官，宋初因唐制为从三品上",
        duty, "太仆寺长官", "建立宋前期寄禄官节点。", "职掌",
        officer="寄禄官", grade="从三品上（因唐制）",
    )
    cite(w, "Timepoints", early, i, rank, "补充宋初太仆寺卿品位。", "品位")
    _, reform = exact_state(
        w, i, "太仆寺卿", "官职", "北宋元丰新制",
        "本寺长官，掌车辂、厩马政令，一员，从四品",
        duty, "太仆寺长官", "建立元丰职事官节点。", "职掌",
        officer="寺卿", grade="从四品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰太仆寺卿品位。", "品位")
    cite(w, "Timepoints", reform, i, roster, "确认元丰新制定额一员。", "编制")
    relation(w, i, source, han, "前后演变", history,
             "西周太仆正为后世太仆卿职源。", "职源与沿革")
    relation(w, i, liang, qing, "前后演变", history,
             "梁太仆卿官衔演为北齐太仆寺卿。", "职源与沿革")
    rank_eid, new_rank = exact_state(
        w, i, "中散大夫", "官职", "北宋元丰新制",
        "元丰寄禄格中太仆寺卿旧寄禄官阶所易新阶",
        duty, "文臣寄禄阶", "建立太仆寺卿元丰易阶结果。", "职掌",
        officer="寄禄官",
    )
    relation(w, i, early, new_rank, "前后演变", duty,
             "元丰正名后太仆寺卿旧寄禄阶易为中散大夫。", "职掌")
    staff(w, i, tp(w, "太仆寺", "机构", "北宋元丰五年五月一日"), reform,
          roster, "元丰新制太仆寺置卿一员。", "编制", quota=1, staff_type="寺卿")
    alias_note(w, i, reform, aliases, "简称")
    touched.update((source_eid, name_eid, eid, rank_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理太仆正、太仆卿与太仆寺卿完整时间链。")
    w.commit()


def entry412():
    i, main = 412, F[412]["text"]
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    eid, early = exact_state(
        w, i, "太仆寺少卿", "官职", "北宋前期",
        "无职事，为文臣迁转官阶，宋初因唐制为从四品上",
        duty, "太仆寺副长官", "建立宋前期寄禄官节点。", "职掌",
        officer="寄禄官", grade="从四品上（因唐制）",
    )
    cite(w, "Timepoints", early, i, history,
         "原文将北齐职源写作‘卫尉寺少卿’，与本条词头不合，不据此建立太仆寺少卿北齐节点。",
         "职源与沿革", note="原文字样与词头不合，暂不结构化该职源")
    cite(w, "Timepoints", early, i, rank, "补充宋初品位。", "品位")
    _, reform = exact_state(
        w, i, "太仆寺少卿", "官职", "北宋元丰五年新制",
        "本寺副贰，佐正卿总马政，一人，正六品",
        duty, "太仆寺副长官", "建立元丰职事官节点。", "职掌",
        officer="少卿", grade="正六品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰品位。", "品位")
    cite(w, "Timepoints", reform, i, roster, "确认元丰新制定额一人。", "编制")
    rank_eid, new_rank = exact_state(
        w, i, "朝议大夫", "官职", "北宋元丰五年新制",
        "元丰正名后太仆寺少卿旧寄禄官阶所易新阶",
        duty, "文臣寄禄阶", "建立太仆寺少卿元丰易阶结果。", "职掌",
        officer="寄禄官",
    )
    relation(w, i, early, new_rank, "前后演变", duty,
             "元丰正名后太仆寺少卿旧寄禄阶易为朝议大夫。", "职掌")
    staff(w, i, tp(w, "太仆寺", "机构", "北宋元丰五年五月一日"), reform,
          roster, "元丰新制太仆寺置少卿一人。", "编制", quota=1, staff_type="少卿")
    alias_note(w, i, reform, aliases, "简称")
    rechain(w, eid, "整理太仆寺少卿完整时间链。")
    rechain(w, rank_eid, "整理朝议大夫时间链。")
    w.commit()


def entry413():
    i, main = 413, F[413]["text"]
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    source_eid, source = exact_state(
        w, i, "太仆丞", "官职", "秦汉", "秦汉已有太仆丞",
        history, "太仆寺丞职源", "建立秦汉太仆丞职源。", "职源与沿革", officer="太仆丞",
    )
    eid, qing = exact_state(
        w, i, "太仆寺丞", "官职", "北齐", "始置太仆寺丞",
        history, "太仆寺职事官", "建立北齐太仆寺丞节点。", "职源与沿革", officer="寺丞",
    )
    _, early = exact_state(
        w, i, "太仆寺丞", "官职", "宋前期",
        "不掌本司事，为文臣迁转官阶，从六品上（因唐制）",
        duty, "太仆寺职事官", "建立宋前期寄禄官节点。", "职掌",
        officer="寄禄官", grade="从六品上（因唐制）",
    )
    cite(w, "Timepoints", early, i, rank, "补充宋前期品位。", "品位")
    _, reform = exact_state(
        w, i, "太仆寺丞", "官职", "北宋元丰新制",
        "参领本寺事，一人，正八品", duty,
        "太仆寺职事官", "建立元丰职事官节点。", "职掌",
        officer="寺丞", grade="正八品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰品位。", "品位")
    cite(w, "Timepoints", reform, i, roster, "确认元丰新制定额一人。", "编制")
    relation(w, i, source, qing, "前后演变", history,
             "秦汉太仆丞演为北齐太仆寺丞。", "职源与沿革")
    staff(w, i, tp(w, "太仆寺", "机构", "北宋元丰五年五月一日"), reform,
          roster, "元丰新制太仆寺置丞一人。", "编制", quota=1, staff_type="寺丞")
    alias_note(w, i, reform, aliases, "简称")
    for entity_id in (source_eid, eid):
        rechain(w, entity_id, "整理太仆丞与太仆寺丞完整时间链。")
    w.commit()


def entry414():
    i, main = 414, F[414]["text"]
    history, duty, rank, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "简称"),
    )
    w = W(i)
    eid, sui = exact_state(
        w, i, "太仆寺主簿", "官职", "隋初", "始置太仆寺主簿",
        history, "太仆寺职事官", "建立隋初职源节点。", "职源与沿革", officer="主簿",
    )
    _, early = exact_state(
        w, i, "太仆寺主簿", "官职", "宋前期",
        "无职事，为空官或文臣迁转官阶，从七品上（因唐制）",
        duty, "太仆寺职事官", "建立宋前期寄禄官节点。", "职掌",
        officer="寄禄官", grade="从七品上（因唐制）",
    )
    cite(w, "Timepoints", early, i, rank, "补充宋前期品位。", "品位")
    _, reform = exact_state(
        w, i, "太仆寺主簿", "官职", "北宋元丰新制",
        "掌勾考本寺簿书，从八品", duty,
        "太仆寺职事官", "建立元丰职事官节点。", "职掌",
        officer="主簿", grade="从八品",
    )
    cite(w, "Timepoints", reform, i, rank, "补充元丰品位。", "品位")
    _, managed = exact_state(
        w, i, "太仆寺主簿", "官职", "北宋元祐元年八月六日",
        "许通管本寺事", duty, "太仆寺职事官",
        "建立元祐元年主簿通管本寺事节点。", "职掌", officer="主簿",
    )
    _, office_managed = exact_state(
        w, i, "太仆寺", "机构", "北宋元祐元年八月六日",
        "太仆寺主簿获准通管本寺事", duty, "马政寺监",
        "建立主簿通管本寺事的同期机构节点。", "职掌",
    )
    staff(w, i, office_managed, managed, duty, "元祐元年主簿许通管本寺事。", "职掌",
          staff_type="主簿")
    _, abolished = exact_state(
        w, i, "太仆寺主簿", "官职", "南宋建炎三年四月十三日",
        "随太仆寺罢废", history, "太仆寺职事官",
        "建立建炎三年罢废节点。", "职源与沿革", officer="主簿",
    )
    cite(w, "Timepoints", abolished, i, history, "确认南宋建炎三年罢。", "职源与沿革")
    alias_note(w, i, reform, aliases, "简称")
    rechain(w, eid, "整理太仆寺主簿隋、宋完整时间链。")
    rechain(w, w.find_entity("太仆寺", "机构"), "整理太仆寺主簿通管同期机构链。")
    w.commit()


def entry415():
    i, main = 415, F[415]["text"]
    w = W(i)
    eid, clerk = exact_state(
        w, i, "府史", "官职", "宋前期",
        "隶太仆寺判寺官，承办本寺事务", main,
        "太仆寺公吏", "建立太仆寺府史。", officer="公吏",
    )
    staff(w, i, tp(w, "太仆寺", "机构", "宋前期"), clerk, main,
          "宋前期太仆寺判寺官下置府史。", staff_type="公吏")
    rechain(w, eid, "整理府史时间链。")
    w.commit()


def entry416():
    i, main = 416, F[416]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    source_eid, tang = exact_state(
        w, i, "飞龙院", "机构", "唐代", "已有飞龙院、小马坊之号",
        history, "马政机构职源", "建立唐代飞龙院职源。", "职源与沿革",
    )
    eid, later_tang = exact_state(
        w, i, "左、右飞龙院", "机构", "五代后唐长兴元年",
        "始置左、右飞龙院", history, "马政机构",
        "建立后唐左右飞龙院节点。", "职源与沿革",
    )
    _, song = exact_state(
        w, i, "左、右飞龙院", "机构", "宋初",
        "沿置，养国马以供军国之用", duty,
        "马政机构", "建立宋初左右飞龙院职掌。", "职掌",
    )
    _, renamed = exact_state(
        w, i, "左、右飞龙院", "机构", "北宋太平兴国五年正月七日",
        "改名左、右天厩院", history, "马政机构",
        "建立太平兴国五年改名节点。", "职源与沿革",
    )
    relation(w, i, tang, later_tang, "前后演变", history,
             "唐飞龙院名号演为后唐左、右飞龙院。", "职源与沿革")
    touched.update((source_eid, eid))
    for title in ("左飞龙院", "右飞龙院"):
        seid, member = exact_state(
            w, i, title, "机构", "宋初", f"{title}养国马以供军国之用",
            main, "马政机构", f"建立{title}实例。",
        )
        relation(w, i, song, member, "统称与实例", main,
                 f"{title}为左、右飞龙院实例。")
        touched.add(seid)
    post_eid, post = exact_state(
        w, i, "左、右飞龙使", "官职", "宋初",
        "沿置，分领左、右飞龙院，掌国马养牧，左右各二人", roster,
        "飞龙院监官", "建立宋初左右飞龙使编制。", "编制", officer="飞龙使",
    )
    staff(w, i, song, post, roster, "左、右飞龙院各置飞龙使二人。", "编制",
          quota=4, staff_type="飞龙使")
    touched.add(post_eid)
    relation(w, i, song, tp(w, "养马务", "机构", "北宋初"),
             "上下级机构", roster, "宋初左、右飞龙院下辖养马务四。", "编制")
    alias_note(w, i, song, aliases, "简称")
    for entity_id in touched:
        rechain(w, entity_id, "整理飞龙院、左右飞龙院及监官完整时间链。")
    w.commit()


def entry417():
    i, main = 417, F[417]["text"]
    history, duty, roster = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制"),
    )
    w = W(i)
    touched = set()
    source_eid, tang = exact_state(
        w, i, "内飞龙使", "官职", "唐万岁通天元年",
        "殿中省仗内飞龙厩所置使职", history,
        "飞龙使职源", "建立唐代内飞龙使职源。", "职源与沿革", officer="内飞龙使",
    )
    eid, song = exact_state(
        w, i, "左、右飞龙使", "官职", "宋初",
        "沿置，分领左、右飞龙院，掌国马养牧，左右各二人",
        duty, "飞龙院监官", "补足宋初左右飞龙使职掌。", "职掌", officer="飞龙使",
    )
    _, abolished = exact_state(
        w, i, "左、右飞龙使", "官职", "北宋太平兴国五年正月七日",
        "罢左、右飞龙使", history, "飞龙院监官",
        "建立太平兴国五年罢使节点。", "职源与沿革", officer="飞龙使",
    )
    relation(w, i, tang, song, "前后演变", history,
             "唐内飞龙使为北宋左、右飞龙使职源。", "职源与沿革")
    for title in ("左飞龙使", "右飞龙使"):
        seid, member = exact_state(
            w, i, title, "官职", "宋初", f"{title}领本院马政，编制二人",
            roster, "飞龙院监官", f"建立{title}实例。", "编制", officer="飞龙使",
        )
        relation(w, i, song, member, "统称与实例", roster,
                 f"{title}为左、右飞龙使实例。", "编制")
        touched.add(seid)
    staff(w, i, tp(w, "左、右飞龙院", "机构", "宋初"), song,
          roster, "左、右飞龙院各置飞龙使二人。", "编制",
          quota=4, staff_type="飞龙使")
    touched.update((source_eid, eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理内飞龙使、左右飞龙使及实例时间链。")
    w.commit()


def entry418():
    i, main = 418, F[418]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "左、右天厩院", "机构", "北宋太平兴国五年正月七日",
        "由左、右飞龙院改名，掌国马养牧以供军国之用",
        history, "马政机构", "建立左右天厩院始置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充国马养牧职掌。", "职掌")
    _, renamed = exact_state(
        w, i, "左、右天厩院", "机构", "北宋雍熙二年十月十六日",
        "改名左、右骐骥院", history, "马政机构",
        "建立雍熙二年改名节点。", "职源与沿革",
    )
    relation(w, i, tp(w, "左、右飞龙院", "机构", "北宋太平兴国五年正月七日"),
             start, "前后演变", history, "左右飞龙院改名左右天厩院。", "职源与沿革")
    target_eid, target = exact_state(
        w, i, "左、右骐骥院", "机构", "北宋雍熙二年十月十六日",
        "由左、右天厩院改名，统国马之政", history, "马政机构",
        "建立左右骐骥院改名承接节点。", "职源与沿革",
    )
    relation(w, i, renamed, target, "前后演变", history,
             "左右天厩院改名左右骐骥院。", "职源与沿革")
    post_eid, post = exact_state(
        w, i, "左、右天厩使", "官职", "北宋太平兴国五年正月七日",
        "由左、右飞龙使改名，各领本院马政", roster,
        "天厩院监官", "建立左右天厩使编制节点。", "编制", officer="天厩使",
    )
    staff(w, i, start, post, roster, "左、右天厩院设置左、右天厩使。", "编制",
          quota=2, staff_type="天厩使")
    sub_eid, monitors = exact_state(
        w, i, "左、右天驷监", "机构", "北宋太平兴国五年正月七日",
        "隶左、右天厩院", roster, "牧马监",
        "建立天厩院所辖左、右天驷监。", "编制",
    )
    relation(w, i, start, monitors, "上下级机构", roster,
             "左、右天厩院下辖左、右天驷监。", "编制")
    alias_note(w, i, start, aliases, "简称")
    touched.update((eid, target_eid, post_eid, sub_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理天厩院、骐骥院、天厩使与天驷监时间链。")
    w.commit()


def entry419():
    i, main, aliases = 419, F[419]["text"], field(419, "简称")
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "左、右天厩使", "官职", "北宋太平兴国五年正月七日",
        "由左、右飞龙使改名，各领本院马政", main,
        "天厩院监官", "补足左右天厩使改名与职掌。", officer="天厩使",
    )
    _, abolished = exact_state(
        w, i, "左、右天厩使", "官职", "北宋雍熙二年十月十六日",
        "罢左、右天厩使", main, "天厩院监官",
        "建立雍熙二年罢使节点。", officer="天厩使",
    )
    relation(w, i, tp(w, "左、右飞龙使", "官职", "北宋太平兴国五年正月七日"),
             start, "前后演变", main, "左、右飞龙使改为左、右天厩使。")
    for title in ("左天厩使", "右天厩使"):
        seid, member = exact_state(
            w, i, title, "官职", "北宋太平兴国五年正月七日",
            f"{title}领本院马政", main, "天厩院监官",
            f"建立{title}实例。", officer="天厩使",
        )
        relation(w, i, start, member, "统称与实例", main,
                 f"{title}为左、右天厩使实例。")
        touched.add(seid)
    staff(w, i, tp(w, "左、右天厩院", "机构", "北宋太平兴国五年正月七日"),
          start, main, "左、右天厩使各领本院马政。", quota=2, staff_type="天厩使")
    alias_note(w, i, start, aliases, "简称")
    touched.add(eid)
    for entity_id in touched:
        rechain(w, entity_id, "整理左右天厩使及实例时间链。")
    w.commit()


def entry420():
    i, main = 420, F[420]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "左、右骐骥院", "机构", "北宋雍熙二年十月十六日",
        "由左、右天厩院改名，统国马之政", history,
        "马政机构", "补足左右骐骥院始置与职掌。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充咸平三年以前总国马之政。", "职能")
    _, before = exact_state(
        w, i, "左、右骐骥院", "机构", "北宋咸平三年九月十一日以前",
        "总国马之政", duty, "马政机构", "建立咸平三年以前职掌节点。", "职能",
    )
    _, herd = exact_state(
        w, i, "左、右骐骥院", "机构", "北宋咸平三年九月十一日",
        "马政总领权归群牧司，本院领所属六坊、监饲养国马",
        duty, "马政机构", "建立改隶群牧司后的职掌节点。", "职能",
    )
    _, reform = exact_state(
        w, i, "左、右骐骥院", "机构", "北宋元丰改制后",
        "改隶太仆寺，继续领坊监国马饲养", main,
        "马政机构", "建立元丰改隶太仆寺节点。",
    )
    _, south = exact_state(
        w, i, "左、右骐骥院", "机构", "南宋",
        "沿置，领坊监及牧马兵", history,
        "马政机构", "建立南宋沿置节点。", "职源与沿革",
    )
    relation(w, i, tp(w, "群牧司", "机构", "北宋咸平三年九月十六日"),
             herd, "上下级机构", main, "咸平三年后左、右骐骥院隶群牧司。")
    relation(w, i, tp(w, "太仆寺", "机构", "北宋元丰五年五月一日"),
             reform, "上下级机构", main, "元丰改制后左、右骐骥院隶太仆寺。")
    touched.add(eid)
    for title in ("左骐骥院", "右骐骥院"):
        seid, member = exact_state(
            w, i, title, "机构", "北宋雍熙二年十月十六日",
            f"{title}为左、右骐骥院之一", history,
            "马政机构", f"建立{title}实例。", "职源与沿革",
        )
        relation(w, i, start, member, "统称与实例", history,
                 f"{title}为左、右骐骥院实例。", "职源与沿革")
        touched.add(seid)
    for title in ("左、右天驷监", "左右天厩坊"):
        seid, subordinate = exact_state(
            w, i, title, "机构", "北宋咸平三年九月十一日以后",
            "隶左、右骐骥院，承担国马饲养", roster,
            "骐骥院属局", f"建立骐骥院所辖{title}。", "编制",
        )
        relation(w, i, herd, subordinate, "上下级机构", roster,
                 f"左、右骐骥院下辖{title}。", "编制")
        touched.add(seid)
    camp_eid, camp_north = exact_state(
        w, i, "左、右教骏营", "机构", "北宋",
        "隶左、右骐骥院，设四指挥，牧马军士共二千九百四十人",
        roster, "骐骥院牧马军", "建立北宋教骏营编制。", "编制",
    )
    relation(w, i, herd, camp_north, "上下级机构", roster,
             "左、右骐骥院所隶牧马兵包括左、右教骏四指挥。", "编制")
    soldiers_eid, soldiers_north = exact_state(
        w, i, "教骏军士", "官职", "北宋",
        "左、右教骏四指挥牧马兵，共二千九百四十人", roster,
        "骐骥院牧马兵", "建立北宋教骏军士定额。", "编制", officer="军士",
    )
    staff(w, i, camp_north, soldiers_north, roster, "北宋教骏军士共二千九百四十人。",
          "编制", quota=2940, staff_type="军士")
    _, camp_south = exact_state(
        w, i, "左、右教骏营", "机构", "南宋绍兴间",
        "四指挥，每指挥一百人，共四百人", roster,
        "骐骥院牧马军", "建立南宋绍兴间教骏营定额。", "编制",
    )
    _, soldiers_south = exact_state(
        w, i, "教骏军士", "官职", "南宋绍兴间",
        "四指挥共四百人，每指挥一百人", roster,
        "骐骥院牧马兵", "建立南宋绍兴间教骏军士定额。", "编制", officer="军士",
    )
    staff(w, i, camp_south, soldiers_south, roster, "南宋绍兴间教骏军士共四百人。",
          "编制", quota=400, staff_type="军士")
    direct_eid, direct = exact_state(
        w, i, "骑御马左、右直", "机构", "北宋",
        "隶左、右骐骥院，牧马兵元额一百三十一人", roster,
        "骐骥院牧马军", "建立骑御马左、右直北宋定额。", "编制",
    )
    relation(w, i, herd, direct, "上下级机构", roster,
             "左、右骐骥院所隶牧马兵包括骑御马左、右直。", "编制")
    rank_eid, rank = exact_state(
        w, i, "骑御马直军士", "官职", "北宋",
        "骑御马左、右直牧马兵，元额一百三十一人", roster,
        "骐骥院牧马兵", "建立骑御马直军士元额。", "编制", officer="军士",
    )
    staff(w, i, direct, rank, roster, "骑御马直军士元额一百三十一人。", "编制",
          quota=131, staff_type="军士")
    _, direct_reduced = exact_state(
        w, i, "骑御马左、右直", "机构", "南宋淳熙十四年",
        "牧马兵减为一百十一人", roster,
        "骐骥院牧马军", "建立淳熙十四年减额节点。", "编制",
    )
    _, rank_reduced = exact_state(
        w, i, "骑御马直军士", "官职", "南宋淳熙十四年",
        "减为一百十一人", roster,
        "骐骥院牧马兵", "建立淳熙十四年减额节点。", "编制", officer="军士",
    )
    staff(w, i, direct_reduced, rank_reduced, roster,
          "淳熙十四年骑御马直军士减为一百十一人。", "编制",
          quota=111, staff_type="军士")
    alias_note(w, i, south, aliases, "简称与别名")
    touched.update((camp_eid, soldiers_eid, direct_eid, rank_eid))
    for entity_id in touched:
        rechain(w, entity_id, "整理骐骥院、左右实例、属局与牧马兵完整时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(401, 421)] == [
        "左、右龙武军", "左、右龙武统军", "左、右神武军",
        "左、右神武军统军", "喝探", "警场", "六军", "六统军",
        "太仆寺", "判太仆寺事", "太仆寺卿", "太仆寺少卿",
        "太仆寺丞", "太仆寺主簿", "府史", "左、右飞龙院",
        "左、右飞龙使", "左、右天厩院", "左、右天厩使",
        "左、右骐骥院",
    ]
    for i in range(401, 421):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
