#!/usr/bin/env python3
"""提取 chapter5t7 第661-680条：市易、交子、杂买杂卖及抵当机构。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_641_660 as previous


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


F = {i: load(i) for i in range(661, 681)}
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
    "唐代": 700,
    "宋初": 960,
    "宋初（市买司）": 961,
    "北宋太平兴国四年十二月": 979.95,
    "北宋至道间": 996,
    "北宋咸平年间": 1000,
    "北宋景德四年五月": 1007.36,
    "北宋大中祥符元年": 1008,
    "北宋天圣元年十一月二十八日": 1023.90,
    "宋前期（隶都大提举库务司）": 1030,
    "宋代（都商税院）": 1050,
    "宋代（杂买务）": 1050.1,
    "宋代（杂卖场）": 1050.2,
    "宋代（未载具体年月）": 1050.3,
    "北宋（始置时间未详）": 1060,
    "北宋熙宁三年六月": 1070.45,
    "北宋熙宁五年三月二十六日": 1072.23,
    "北宋熙宁五年七月五日": 1072.51,
    "北宋熙宁六年十月二日": 1073.76,
    "北宋熙宁八年": 1075,
    "北宋熙宁八年数月后": 1075.5,
    "北宋元丰新制": 1082.1,
    "北宋元丰四年十二月八日": 1081.94,
    "北宋元丰七年四月十二日": 1084.29,
    "北宋大观元年": 1107,
    "北宋崇宁四年六月二十三日": 1105.48,
    "南宋绍兴四年": 1134,
    "南宋绍兴四年（杂买务杂卖场）": 1134.1,
    "南宋绍兴六年": 1136,
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
                field_name=None, *, officer=None, grade=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )
    set_event(w, tid, event, decision)
    return eid, tid


def support_state(w, i, title, type_, time, event, quotation, category, decision,
                  field_name=None, *, officer=None, grade=None):
    return state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )


def formalize_entity(w, old_title, new_title, type_, quotation, decision):
    """把既有简称实体规范为本批辞典正式词头；重复运行时保持不变。"""
    new_id = w.find_entity(new_title, type_)
    old_id = w.find_entity(old_title, type_)
    if new_id:
        assert not old_id or old_id == new_id, (old_title, new_title, old_id, new_id)
        return new_id
    assert old_id, old_title
    w.conn.execute(
        "update Entities set title=?,quotation=? where id=?",
        (new_title, quotation, old_id),
    )
    w._br("Entities", old_id, decision)
    return old_id


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def entry661():
    i, main = 661, F[661]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "曹司", "官职", "北宋（先隶三司）",
        "都商税院公人，供收税钱行遣", main,
        "都商税院公人", "建立曹司在都商税院的职掌节点。", officer="公人",
    )
    parent = tp(w, "都商税院", "机构", "北宋（先隶三司）")
    staff(w, i, parent, post, main, "曹司隶都商税院。", staff_type="公人")
    finish(w, {eid}, "整理曹司在都商税院的身份、职掌与隶属时间链。")


def entry662():
    i, main = 662, F[662]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "数钱", "官职", "北宋（先隶三司）",
        "都商税院专掌税钱数目", main,
        "都商税院公吏", "复用数钱节点并补本条证据。", officer="公吏",
    )
    staff(w, i, tp(w, "都商税院", "机构", "北宋（先隶三司）"),
          post, main, "数钱隶都商税院。", staff_type="公吏")
    finish(w, {eid}, "补证数钱隶属与职掌。")


def entry663():
    i, main, short = 663, F[663]["text"], field(663, "简称")
    w, touched = W(i), set()
    qinfeng_eid, qinfeng = exact_state(
        w, i, "秦凤路市易司", "机构", "北宋熙宁三年六月",
        "王韶奏请后已见设置，为市易务创置之滥觞", main,
        "地方市易机构", "建立秦凤路市易司先导节点。",
    )
    eid, bureau = exact_state(
        w, i, "在京市易务", "机构", "北宋熙宁五年三月二十六日",
        "创置，以内藏库钱为本，平价收敛货物并贷钱给行人、牙人贸易",
        main, "京师市易监当局", "建立在京市易务创置与职掌节点。",
    )
    relation(w, i, qinfeng, bureau, "前后演变", main,
             "秦凤路市易司是市易务创置的滥觞。")
    roles = (
        ("监在京市易务", "监官", 2, "监管在京市易务，设二员"),
        ("提举在京市易务", "提举官", 1, "领京师市易务公事，设一员"),
        ("勾当在京市易务公事", "勾当公事官", 1, "勾当在京市易务公事，设一员"),
    )
    for title, officer, quota, event in roles:
        role_eid, post = exact_state(
            w, i, title, "官职", "北宋熙宁五年三月二十六日",
            event, main, "在京市易务官属", f"建立{title}编制。", officer=officer,
        )
        staff(w, i, bureau, post, main, f"在京市易务设{title}。",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    alias_note(w, i, bureau, short, "简称")
    touched.update((qinfeng_eid, eid))
    finish(w, touched, "整理在京市易务的先导、创置、职掌与官属时间链。")


def entry664():
    i, main = 664, F[664]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "提举在京市易务", "官职", "北宋熙宁五年三月二十六日",
        "由三司判官充，领京师市易务公事", main,
        "在京市易务提举官", "复用提举在京市易务节点并补充充任资格。",
        officer="提举官",
    )
    staff(w, i, tp(w, "在京市易务", "机构", "北宋熙宁五年三月二十六日"),
          post, main, "提举在京市易务领本务公事。", quota=1, staff_type="提举官")
    finish(w, {eid}, "补证提举在京市易务的充任资格与职掌。")


def entry665():
    i = 665
    main, origin, duty, roster, short = (
        F[i]["text"], field(i, "职源"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    source_eid, source = exact_state(
        w, i, "提举在京市易务司", "机构", "北宋熙宁六年十月二日",
        "改为都提举市易司", origin, "京师市易主管司",
        "建立提举在京市易务司改名节点。", "职源",
    )
    eid, office = exact_state(
        w, i, "都提举市易司", "机构", "北宋熙宁六年十月二日",
        "由提举在京市易务司改名，设于开封太平坊，总辖京师及诸路市易务",
        origin, "市易主管机构", "建立都提举市易司改名创置节点。", "职源",
    )
    relation(w, i, source, office, "前后演变", origin,
             "提举在京市易务司改为都提举市易司。", "职源")
    three_eid, three = support_state(
        w, i, "三司", "机构", "北宋熙宁六年十月二日",
        "统辖都提举市易司", main, "北宋中央财政机构",
        "建立三司统辖都提举市易司承载节点。",
    )
    relation(w, i, three, office, "上下级机构", main, "都提举市易司先隶三司。")
    _, reform = exact_state(
        w, i, "都提举市易司", "机构", "北宋元丰新制",
        "改隶太府寺", main, "太府寺所属市易主管机构",
        "建立都提举市易司改隶太府寺节点。",
    )
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "都提举市易司后隶太府寺。")
    roads_eid, roads = exact_state(
        w, i, "诸路州军市易务", "机构", "北宋熙宁六年十月二日",
        "全国诸路州军所置市易务的统称", duty,
        "地方市易机构统称", "建立诸路州军市易务统称节点。", "职掌",
    )
    relation(w, i, office, roads, "上下级机构", duty,
             "都提举市易司总辖全国诸路州军市易务。", "职掌")
    roles = (
        ("都提举市易司公事", "都提举官", 1, "掌领都提举市易司公事"),
        ("同都提举市易司公事", "同都提举官", 1, "同掌都提举市易司公事"),
        ("勾当都提举市易司公事", "勾当公事官", None, "勾当都提举市易司公事"),
    )
    for title, officer, quota, event in roles:
        role_eid, post = exact_state(
            w, i, title, "官职", "北宋熙宁六年十月二日", event,
            roster, "都提举市易司官属", f"建立{title}编制。", "编制", officer=officer,
        )
        staff(w, i, office, post, roster, f"都提举市易司设{title}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    cite(w, "Timepoints", office, i, duty, "补证都提举市易司职掌。", "职掌")
    alias_note(w, i, office, short, "简称")
    touched.update((source_eid, eid, three_eid, roads_eid))
    finish(w, touched, "整理都提举市易司改名、隶属、职掌与官属时间链。")


def entry666():
    i, main, short = 666, F[666]["text"], field(666, "简称")
    w = W(i)
    eid, post = support_state(
        w, i, "都提举市易司公事", "官职", "北宋熙宁六年十月二日",
        "掌领都提举市易司公事", main, "都提举市易司长官",
        "复用都提举市易司公事节点并补本条职掌证据。", officer="都提举官",
    )
    staff(w, i, tp(w, "都提举市易司", "机构", "北宋熙宁六年十月二日"),
          post, main, "都提举市易司置都提举公事官。", quota=1, staff_type="都提举官")
    alias_note(w, i, post, short, "简称")
    finish(w, {eid}, "补证都提举市易司公事的职掌与简称。")


def entry667():
    i, main, short = 667, F[667]["text"], field(667, "简称")
    w, touched = W(i), set()
    _, source = exact_state(
        w, i, "在京市易务", "机构", "北宋熙宁五年七月五日",
        "榷货务并入后改为东务上界", main,
        "京师市易监当局", "建立在京市易务改为上界节点。",
    )
    eid, upper = exact_state(
        w, i, "在京市易东务上界", "机构", "北宋熙宁五年七月五日",
        "由在京市易务改置，掌京师官钱贷赊与平抑物价", main,
        "京师市易上界", "建立在京市易东务上界节点。",
    )
    relation(w, i, source, upper, "前后演变", main,
             "在京市易务改为在京市易东务上界。")
    _, under = exact_state(
        w, i, "在京市易东务上界", "机构", "北宋熙宁六年十月二日",
        "隶都提举市易司", main, "都提举市易司所属上界",
        "建立在京市易东务上界改隶节点。",
    )
    relation(w, i, tp(w, "都提举市易司", "机构", "北宋熙宁六年十月二日"),
             under, "上下级机构", main, "在京市易东务上界隶都提举市易司。")
    for title, officer in (
        ("提举在京市易务", "提举官"),
        ("监在京市易务", "监官"),
        ("勾当在京市易务公事", "勾当官"),
    ):
        role_eid, post = support_state(
            w, i, title, "官职", "北宋熙宁六年十月二日",
            f"任在京市易东务上界{officer}", main,
            "在京市易上界官属", f"建立{title}任上界官的承载节点。", officer=officer,
        )
        staff(w, i, under, post, main, f"在京市易东务上界设{officer}。",
              staff_type=officer)
        touched.add(role_eid)
    _, ending = exact_state(
        w, i, "在京市易东务上界", "机构", "北宋元丰七年四月十二日",
        "去‘上界’二字，仍改为在京市易务", main,
        "京师市易上界", "建立上界复名节点。",
    )
    _, restored = exact_state(
        w, i, "在京市易务", "机构", "北宋元丰七年四月十二日",
        "由在京市易东务上界复名", main,
        "京师市易监当局", "建立在京市易务复名节点。",
    )
    relation(w, i, ending, restored, "前后演变", main,
             "元丰七年在京市易东务上界复为在京市易务。")
    alias_note(w, i, upper, short, "简称")
    touched.add(eid)
    touched.add(w.find_entity("在京市易务", "机构"))
    finish(w, touched, "整理在京市易东务上界改置、隶属与复名时间链。")


def entry668():
    i, main, short = 668, F[668]["text"], field(668, "简称")
    w, touched = W(i), set()
    eid = formalize_entity(
        w, "市易西务下界", "在京市易西务下界", "机构", main,
        "按本批正式词头将既有简称实体‘市易西务下界’规范为‘在京市易西务下界’。",
    )
    source_eid, source = exact_state(
        w, i, "在京榷货务", "机构", "北宋熙宁五年七月五日",
        "改为在京市易西务下界", main,
        "京师榷货机构", "补证在京榷货务改置节点。",
    )
    _, lower = exact_state(
        w, i, "在京市易西务下界", "机构", "北宋熙宁五年七月五日",
        "由在京榷货务改置，并入在京市易务，掌飞钱给券以通边籴", main,
        "京师市易下界", "规范在京市易西务下界改置与职掌节点。",
    )
    relation(w, i, source, lower, "前后演变", main,
             "在京榷货务改为在京市易西务下界。")
    relation(w, i, tp(w, "在京市易务", "机构", "北宋熙宁五年七月五日"),
             lower, "上下级机构", main, "在京市易西务下界并入在京市易务。")
    _, under = exact_state(
        w, i, "在京市易西务下界", "机构", "北宋熙宁六年十月二日",
        "由都提举市易司总辖", main, "都提举市易司所属下界",
        "建立在京市易西务下界由都提举市易司总辖节点。",
    )
    relation(w, i, tp(w, "都提举市易司", "机构", "北宋熙宁六年十月二日"),
             under, "上下级机构", main, "都提举市易司总辖在京市易西务下界。")
    _, ending = exact_state(
        w, i, "在京市易西务下界", "机构", "北宋元丰七年四月十二日",
        "复为在京榷货务", main, "京师市易下界", "规范下界复名节点。",
    )
    _, restored = exact_state(
        w, i, "在京榷货务", "机构", "北宋元丰七年四月十二日",
        "由在京市易西务下界复名", main,
        "京师榷货机构", "补证在京榷货务复名节点。",
    )
    relation(w, i, ending, restored, "前后演变", main,
             "元丰七年在京市易西务下界复为在京榷货务。")
    alias_note(w, i, lower, short, "简称")
    touched.update((eid, source_eid))
    finish(w, touched, "整理在京市易西务下界改置、隶属与复名时间链。")


def entry669():
    i, main = 669, F[669]["text"]
    origin, duty, roster = field(i, "职源"), field(i, "职掌"), field(i, "编制")
    w, touched = W(i), set()
    eid, early = exact_state(
        w, i, "在京交子务", "机构", "北宋（始置时间未详）",
        "始置时间未详，掌印卖交子并更造换界", origin,
        "京师纸币监当局", "建立在京交子务未详始置节点。", "职源",
    )
    _, ending = exact_state(
        w, i, "在京交子务", "机构", "北宋崇宁四年六月二十三日",
        "罢置，官吏并入榷货务买钞所", origin,
        "京师纸币监当局", "规范在京交子务罢并节点。", "职源",
    )
    target_eid, target = support_state(
        w, i, "买钞所", "机构", "北宋崇宁四年六月二十三日",
        "接收在京交子务官吏", origin,
        "榷货务买钞机构", "复用买钞所接收节点并补本条证据。", "职源",
    )
    relation(w, i, ending, target, "前后演变", origin,
             "在京交子务官吏并入榷货务买钞所。", "职源")
    role_eid, post = exact_state(
        w, i, "提举在京交子务", "官职", "北宋（始置时间未详）",
        "提举在京交子务", roster, "在京交子务提举官",
        "建立提举在京交子务官职节点。", "编制", officer="提举官",
    )
    staff(w, i, early, post, roster, "在京交子务设提举官。", "编制", staff_type="提举官")
    cite(w, "Timepoints", early, i, duty, "补证在京交子务职掌。", "职掌")
    touched.update((eid, target_eid, role_eid))
    finish(w, touched, "整理在京交子务职掌、编制与并入买钞所时间链。")


def entry670():
    i, main = 670, F[670]["text"]
    w, touched = W(i), set()
    eid, bureau = exact_state(
        w, i, "益州交子务", "机构", "北宋天圣元年十一月二十八日",
        "成立官营交子务于成都，又称四川交子务", main,
        "四川纸币监当局", "建立益州交子务官营创置节点。",
    )
    _, ending = exact_state(
        w, i, "益州交子务", "机构", "北宋大观元年",
        "改为钱引务，罢交子", main,
        "四川纸币监当局", "建立益州交子务改制节点。",
    )
    target_eid, target = exact_state(
        w, i, "钱引务", "机构", "北宋大观元年",
        "由四川交子务改置", main,
        "四川纸币监当局", "建立钱引务改置节点。",
    )
    relation(w, i, ending, target, "前后演变", main,
             "大观元年四川交子务改为钱引务。")
    cite(w, "Timepoints", bureau, i, main,
         "‘四川交子务’为益州交子务同一机构的名称证据，不另建实体。",
         note="纯别称不另建实体")
    touched.update((eid, target_eid))
    finish(w, touched, "整理益州交子务官营创置、别称及改为钱引务时间链。")


def entry671():
    i = 671
    main, origin, duty, roster, short = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    tang_eid, tang = exact_state(
        w, i, "官市", "机构", "唐代", "官府采购机构", origin,
        "宫廷采购机构", "建立唐代官市前身节点。", "职源与沿革",
    )
    source_eid, source = exact_state(
        w, i, "市买司", "机构", "宋初（市买司）",
        "宋初沿唐官市而置", origin, "宫廷采购机构",
        "建立市买司前身节点。", "职源与沿革",
    )
    relation(w, i, tang, source, "前后演变", origin,
             "唐代官市入宋称市买司。", "职源与沿革")
    eid, origin_tp = exact_state(
        w, i, "杂买务", "机构", "北宋太平兴国四年十二月",
        "由市买司改名，掌宫中和市百物以应宫廷、官府采购", origin,
        "中央采购监当局", "建立杂买务改名创置节点。", "职源与沿革",
    )
    relation(w, i, source, origin_tp, "前后演变", origin,
             "太平兴国四年市买司改为杂买务。", "职源与沿革")
    _, stopped = exact_state(
        w, i, "杂买务", "机构", "北宋至道间", "罢置", origin,
        "中央采购监当局", "建立杂买务至道间罢置节点。", "职源与沿革",
    )
    _, restored = exact_state(
        w, i, "杂买务", "机构", "北宋咸平年间", "复置", origin,
        "中央采购监当局", "建立杂买务咸平复置节点。", "职源与沿革",
    )
    parent_eid, parent = support_state(
        w, i, "都大提举在京诸司库务司", "机构", "宋前期（隶都大提举库务司）",
        "统辖杂买务", main, "在京库务统辖机构",
        "建立都大提举库务司统辖杂买务节点。",
    )
    relation(w, i, parent, restored, "上下级机构", main,
             "杂买务早期隶都大提举在京诸司库务司。")
    _, merged = exact_state(
        w, i, "杂买务", "机构", "北宋熙宁八年",
        "并入在京市易务", origin, "中央采购监当局",
        "建立杂买务并入市易务节点。", "职源与沿革",
    )
    market_eid, market = support_state(
        w, i, "在京市易务", "机构", "北宋熙宁八年",
        "接收并入的杂买务", origin, "京师市易监当局",
        "建立在京市易务接收杂买务节点。", "职源与沿革",
    )
    relation(w, i, merged, market, "前后演变", origin,
             "熙宁八年杂买务并入在京市易务。", "职源与沿革")
    market_parent_eid, market_parent = support_state(
        w, i, "都提举市易司", "机构", "北宋熙宁八年",
        "统辖杂买务", main, "市易主管机构",
        "建立都提举市易司统辖杂买务节点。",
    )
    relation(w, i, market_parent, merged, "上下级机构", main,
             "杂买务一度隶都提举市易司。")
    _, restored2 = exact_state(
        w, i, "杂买务", "机构", "北宋熙宁八年数月后",
        "并入市易务数月后复置", origin, "中央采购监当局",
        "建立杂买务数月后复置节点。", "职源与沿革",
    )
    _, reform = exact_state(
        w, i, "杂买务", "机构", "北宋元丰新制", "改隶太府寺", main,
        "太府寺所属监当局", "建立杂买务元丰后隶属节点。",
    )
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "杂买务后隶太府寺。")
    _, ending = exact_state(
        w, i, "杂买务", "机构", "南宋绍兴四年",
        "与杂卖场合并为杂买务杂卖场", origin,
        "太府寺所属监当局", "建立杂买务合并节点。", "职源与沿革",
    )
    combined_eid, combined = exact_state(
        w, i, "杂买务杂卖场", "机构", "南宋绍兴四年",
        "杂买务与杂卖场合并为一局", origin,
        "太府寺所属监当局", "建立杂买务杂卖场合局节点。", "职源与沿革",
    )
    relation(w, i, ending, combined, "前后演变", origin,
             "绍兴四年杂买务并入杂买务杂卖场。", "职源与沿革")
    _, role_parent = support_state(
        w, i, "杂买务", "机构", "宋代（杂买务）",
        "设置监官、勾当官及诸吏役", roster, "中央采购监当局",
        "建立杂买务官吏编制承载节点。", "编制",
    )
    roles = (
        ("监杂买务", "监官", 3), ("勾当杂买务", "勾当官", None),
        ("专知", "吏", None), ("副知", "吏", None), ("库子", "吏", None),
        ("攒司", "吏", None), ("手分", "吏", None), ("秤子", "公人", None),
        ("外催", "公人", None),
    )
    for title, officer, quota in roles:
        role_eid, post = support_state(
            w, i, title, "官职", "宋代（杂买务）",
            f"杂买务所置{title}", roster, "杂买务官吏",
            f"建立杂买务{title}职制。", "编制", officer=officer,
        )
        staff(w, i, role_parent, post, roster, f"杂买务置{title}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    cite(w, "Timepoints", origin_tp, i, duty, "补证杂买务职掌。", "职掌")
    alias_note(w, i, origin_tp, short, "简称")
    touched.update((tang_eid, source_eid, eid, parent_eid, market_eid,
                    market_parent_eid, combined_eid))
    finish(w, touched, "整理杂买务来源、罢复、并市易务、隶属、合局与官吏时间链。")


def entry672():
    i, main = 672, F[672]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "辨验药材官", "官职", "宋代（杂买务）",
        "选差翰林医官院近上医官充，为和剂局辨别、审验采购药材", main,
        "杂买务差遣", "建立辨验药材官职掌与充任节点。", officer="差遣官",
    )
    staff(w, i, tp(w, "杂买务", "机构", "宋代（杂买务）"),
          post, main, "辨验药材官隶杂买务。", staff_type="差遣官")
    finish(w, {eid}, "整理辨验药材官隶属、职掌与充任资格。")


def entry673():
    i, main = 673, F[673]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "外催", "官职", "宋代（杂买务）",
        "赴下州府或京城收买、催办杂买务所需物品", main,
        "杂买务公人", "规范外催在杂买务的职掌节点。", officer="公人",
    )
    staff(w, i, tp(w, "杂买务", "机构", "宋代（杂买务）"),
          post, main, "外催隶杂买务。", staff_type="公人")
    finish(w, {eid}, "补证外催在杂买务的身份、隶属与职掌。")


def entry674():
    i, main = 674, F[674]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "秤子", "官职", "宋代（杂买务）",
        "杂买务公人，主秤量成交货物", main,
        "杂买务公人", "规范秤子在杂买务的职掌节点。", officer="公人",
    )
    staff(w, i, tp(w, "杂买务", "机构", "宋代（杂买务）"),
          post, main, "秤子隶杂买务。", staff_type="公人")
    finish(w, {eid}, "补证秤子在杂买务的身份、隶属与职掌。")


def entry675():
    i = 675
    main, origin, duty, roster, short = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    eid, bureau = exact_state(
        w, i, "杂卖场", "机构", "北宋景德四年五月",
        "创置，掌受内外粗劣、剩余官物计直出卖或折支", origin,
        "中央官物变卖监当局", "建立杂卖场创置节点。", "职源与沿革",
    )
    store_eid, store = exact_state(
        w, i, "积尺剜子库", "机构", "北宋大中祥符元年",
        "并入杂卖场", origin, "中央官物库",
        "建立积尺剜子库并入节点。", "职源与沿革",
    )
    _, receiver = exact_state(
        w, i, "杂卖场", "机构", "北宋大中祥符元年",
        "接收积尺剜子库", origin, "中央官物变卖监当局",
        "建立杂卖场接收积尺剜子库节点。", "职源与沿革",
    )
    relation(w, i, store, receiver, "前后演变", origin,
             "大中祥符元年积尺剜子库并入杂卖场。", "职源与沿革")
    parent_eid, parent = support_state(
        w, i, "都大提举在京诸司库务司", "机构", "宋前期（隶都大提举库务司）",
        "统辖杂卖场", main, "在京库务统辖机构",
        "建立都大提举库务司统辖杂卖场节点。",
    )
    relation(w, i, parent, bureau, "上下级机构", main,
             "杂卖场早期隶都大提举在京诸司库务司。")
    _, merged = exact_state(
        w, i, "杂卖场", "机构", "北宋熙宁八年", "并入在京市易务", origin,
        "中央官物变卖监当局", "建立杂卖场并入市易务节点。", "职源与沿革",
    )
    market_eid, market = support_state(
        w, i, "在京市易务", "机构", "北宋熙宁八年",
        "接收并入的杂卖场", origin, "京师市易监当局",
        "复用在京市易务接收节点并补杂卖场证据。", "职源与沿革",
    )
    relation(w, i, merged, market, "前后演变", origin,
             "熙宁八年杂卖场并入在京市易务。", "职源与沿革")
    market_parent_eid, market_parent = support_state(
        w, i, "都提举市易司", "机构", "北宋熙宁八年",
        "统辖杂卖场", main, "市易主管机构",
        "复用都提举市易司熙宁八年节点并补杂卖场证据。",
    )
    relation(w, i, market_parent, merged, "上下级机构", main,
             "杂卖场一度隶都提举市易司。")
    _, restored = exact_state(
        w, i, "杂卖场", "机构", "北宋熙宁八年数月后", "数月后复置", origin,
        "中央官物变卖监当局", "建立杂卖场数月后复置节点。", "职源与沿革",
    )
    _, reform = exact_state(
        w, i, "杂卖场", "机构", "北宋元丰新制", "改隶太府寺", main,
        "太府寺所属监当局", "建立杂卖场元丰后隶属节点。",
    )
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "杂卖场后隶太府寺。")
    _, ending = exact_state(
        w, i, "杂卖场", "机构", "南宋绍兴四年",
        "与杂买务合并为杂买务杂卖场", origin,
        "太府寺所属监当局", "建立杂卖场合并节点。", "职源与沿革",
    )
    combined = tp(w, "杂买务杂卖场", "机构", "南宋绍兴四年")
    relation(w, i, ending, combined, "前后演变", origin,
             "绍兴四年杂卖场并入杂买务杂卖场。", "职源与沿革")
    _, role_parent = support_state(
        w, i, "杂卖场", "机构", "宋代（杂卖场）",
        "设置监官与掌库", roster, "中央官物变卖监当局",
        "建立杂卖场官吏编制承载节点。", "编制",
    )
    roles = (
        ("监杂卖场", "监官", 2, "由内侍及三班使臣充监官"),
        ("掌库", "吏", 8, "杂卖场吏额掌库八人"),
    )
    for title, officer, quota, event in roles:
        role_eid, post = exact_state(
            w, i, title, "官职", "宋代（杂卖场）", event, roster,
            "杂卖场官吏", f"建立杂卖场{title}编制。", "编制", officer=officer,
        )
        staff(w, i, role_parent, post, roster, f"杂卖场置{title}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    combined_roles = (
        ("专知", "吏", 1), ("手分", "吏", 1), ("库子", "吏", 2),
        ("秤子", "公人", 1), ("巡防兵士", "兵士", 21),
    )
    for title, officer, quota in combined_roles:
        role_eid, post = support_state(
            w, i, title, "官职", "南宋绍兴四年（杂买务杂卖场）",
            f"杂买务杂卖场定额{title}{quota}名", roster,
            "杂买务杂卖场官吏", f"建立合局后{title}定额。", "编制", officer=officer,
        )
        staff(w, i, combined, post, roster, f"杂买务杂卖场定额置{title}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    cite(w, "Timepoints", bureau, i, duty, "补证杂卖场职掌。", "职掌")
    alias_note(w, i, bureau, short, "简称")
    touched.update((eid, store_eid, parent_eid, market_eid, market_parent_eid))
    finish(w, touched, "整理杂卖场创置、库并入、市易并复、隶属、合局与编制时间链。")


def entry676():
    i, main, short = 676, F[676]["text"], field(676, "简称")
    w, touched = W(i), set()
    eid, post = exact_state(
        w, i, "专知官", "官职", "宋代（杂卖场）",
        "由曾经历库务的副尉小使臣差充，三年一替，掌管杂卖场官物", main,
        "杂卖场吏", "建立专知官在杂卖场的任用与职掌节点。", officer="吏",
    )
    parent_eid, parent = support_state(
        w, i, "杂卖场", "机构", "宋代（杂卖场）",
        "设置专知官掌管本场官物", main,
        "中央官物变卖监当局", "建立杂卖场专知官承载节点。",
    )
    staff(w, i, parent, post, main, "杂卖场设专知官。", quota=1, staff_type="吏")
    alias_note(w, i, post, short, "简称")
    touched.update((eid, parent_eid))
    finish(w, touched, "整理杂卖场专知官的任用、职掌、隶属与简称。")


def entry677():
    i, main = 677, F[677]["text"]
    w, touched = W(i), set()
    eid, post = exact_state(
        w, i, "提辖杂买务杂卖场", "官职", "南宋绍兴六年",
        "始置，总辖杂买务杂卖场事，为储才之地", main,
        "太府寺四辖官", "建立提辖杂买务杂卖场节点。", officer="提辖官",
    )
    combined = tp(w, "杂买务杂卖场", "机构", "南宋绍兴四年")
    staff(w, i, combined, post, main, "杂买务杂卖场设提辖官总辖局事。",
          quota=1, staff_type="提辖官")
    group_eid, group = exact_state(
        w, i, "四辖", "官职", "南宋绍兴六年",
        "太府寺四种提辖官的通称", main,
        "太府寺提辖官统称", "建立四辖统称节点。", officer="提辖官统称",
    )
    instances = (
        ("提辖杂买务杂卖场", post),
        ("提辖左藏库", None),
        ("提辖文思院", None),
        ("提辖榷货务都茶场", None),
    )
    for title, existing in instances:
        if existing is None:
            child_eid, child = exact_state(
                w, i, title, "官职", "南宋绍兴六年",
                "四辖之一", main, "太府寺提辖官",
                f"建立四辖实例{title}。", officer="提辖官",
            )
            touched.add(child_eid)
        else:
            child = existing
        relation(w, i, group, child, "统称与实例", main, f"{title}是四辖之一。")
    touched.update((eid, group_eid))
    finish(w, touched, "整理提辖杂买务杂卖场职掌及四辖全部实例时间链。")


def entry678():
    i, main, alias = 678, F[678]["text"], field(678, "别称")
    w, touched = W(i), set()
    eid, bureau = exact_state(
        w, i, "交引库", "机构", "宋代（未载具体年月）",
        "隶太府寺，专掌印发与回笼茶盐钞引以便利通商", main,
        "太府寺所属监当局", "建立交引库隶属与职掌节点。",
    )
    parent_eid, parent = support_state(
        w, i, "太府寺", "机构", "宋代（未载具体年月）",
        "统辖交引库", main, "宋代寺监",
        "建立太府寺统辖交引库承载节点。",
    )
    relation(w, i, parent, bureau, "上下级机构", main, "交引库隶太府寺。")
    alias_note(w, i, bureau, alias, "别称")
    touched.update((eid, parent_eid))
    finish(w, touched, "整理交引库隶属、职掌与别称时间链。")


def entry679():
    i, main, alias = 679, F[679]["text"], field(679, "别名")
    w, touched = W(i), set()
    eid, bureau = exact_state(
        w, i, "抵当所", "机构", "宋前期",
        "先后隶开封府、都提举市易司、太府寺，以官钱为本受理典当、存钱及免行钱", main,
        "中央抵当监当局", "建立抵当所宋前期职掌与沿革节点。",
    )
    for parent_title, time, event in (
        ("开封府", "宋前期", "早期统辖抵当所"),
        ("都提举市易司", "北宋熙宁六年十月二日", "一度统辖抵当所"),
        ("太府寺", "北宋元丰新制", "后统辖抵当所"),
    ):
        parent_eid, parent = support_state(
            w, i, parent_title, "机构", time, event, main,
            "中央主管机构", f"建立{parent_title}统辖抵当所承载节点。",
        )
        child_eid, child = support_state(
            w, i, "抵当所", "机构", time,
            f"隶{parent_title}", main, "中央抵当监当局",
            f"建立抵当所隶{parent_title}节点。",
        )
        relation(w, i, parent, child, "上下级机构", main, f"抵当所先后隶{parent_title}。")
        touched.update((parent_eid, child_eid))
    group_eid, group = exact_state(
        w, i, "抵当所五窠", "机构", "宋前期",
        "宋前期抵当所所分五窠的统称", main,
        "抵当本钱窠统称", "建立抵当所五窠统称节点。",
    )
    for title in ("检校小儿钱窠", "开封府杂供库窠", "国子监、律、武学窠", "军器、都水监窠", "市易窠"):
        child_eid, child = exact_state(
            w, i, title, "机构", "宋前期", "抵当所五窠之一", main,
            "抵当本钱窠", f"建立抵当所五窠实例{title}。",
        )
        relation(w, i, group, child, "统称与实例", main, f"{title}是抵当所五窠之一。")
        touched.add(child_eid)
    four_eid, four = exact_state(
        w, i, "东、南、西、北四抵当所", "机构", "北宋元丰四年十二月八日",
        "开封新旧城内外所置四抵当所的统称", main,
        "京师抵当所统称", "建立四抵当所统称节点。",
    )
    for title in ("东抵当所", "南抵当所", "西抵当所", "北抵当所"):
        child_eid, child = exact_state(
            w, i, title, "机构", "北宋元丰四年十二月八日",
            "开封新旧城内外四抵当所之一", main,
            "京师抵当所", f"建立四抵当所实例{title}。",
        )
        relation(w, i, four, child, "统称与实例", main, f"{title}是东、南、西、北四抵当所之一。")
        touched.add(child_eid)
    alias_note(w, i, bureau, alias, "别名")
    touched.update((eid, group_eid, four_eid))
    finish(w, touched, "整理抵当所职掌、三段隶属、五窠及四抵当所实例时间链。")


def entry680():
    i, main = 680, F[680]["text"]
    w = W(i)
    eid, _ = exact_state(
        w, i, "抵当库", "机构", "宋代（未载具体年月）",
        "诸路州军所置，以官钱召人或官司典当财物并收取月息", main,
        "地方抵当监当局", "建立抵当库分布范围与职掌节点。",
    )
    finish(w, {eid}, "整理诸路州军抵当库的性质、分布与职掌时间链。")


def main():
    for i in range(661, 681):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
