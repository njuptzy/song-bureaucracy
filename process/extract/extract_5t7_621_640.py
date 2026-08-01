#!/usr/bin/env python3
"""提取 chapter5t7 第621-640条：太府寺诸案与左藏库系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_601_620 as previous


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


F = {i: load(i) for i in range(621, 641)}
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
    "晋": 265, "唐": 618, "宋初": 960,
    "北宋太平兴国二年正月五日": 977.02,
    "北宋淳化三年十一月": 992.88,
    "北宋淳化四年": 993,
    "北宋大中祥符二年冬": 1009.9,
    "北宋大中祥符八年十二月二十五日": 1015.98,
    "北宋熙宁九年后": 1076.3,
    "北宋元丰新制": 1082.1,
    "北宋元符三年五月十七日": 1100.38,
    "北宋政和六年": 1116,
    "南宋": 1127, "南宋绍兴元年二月四日": 1131.09,
    "南宋绍兴元年": 1131.1,
    "南宋（太府寺八案制）": 1145,
    "南宋绍兴二十七年": 1157,
    "南宋绍兴三十二年七月十八日": 1162.55,
    "南宋隆兴元年七月二十四日": 1163.55,
    "南宋淳熙十年六月二十八日": 1183.48,
    "南宋淳熙十二年正月十三日": 1185.04,
    "南宋绍熙元年十月二日": 1190.76,
    "南宋嘉定三年四月": 1210.27,
    "南宋嘉定七年": 1214,
    "南宋绍定六年": 1233,
    "宋代（左藏库官属）": 1050,
    "南宋绍兴元年（左藏东、西库吏额）": 1131.2,
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


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def south_treasury_case(w, i, title, event):
    main = F[i]["text"]
    parent_eid, parent = exact_state(
        w, i, "太府寺", "机构", "南宋（太府寺八案制）",
        "设置八案分掌财赋、俸给、采购、药材与监交事务",
        main, "南宋财货机构", "建立南宋太府寺八案制承载节点。",
    )
    group_eid, group = exact_state(
        w, i, "太府寺八案", "机构", "南宋（太府寺八案制）",
        "南宋太府寺八个办事案的统称", main, "太府寺办事案统称",
        "建立南宋太府寺八案统称。",
    )
    case_eid, case = exact_state(
        w, i, title, "机构", "南宋（太府寺八案制）", event,
        main, "太府寺办事案", f"建立{title}职掌节点。",
    )
    relation(w, i, parent, group, "上下级机构", main,
             "南宋太府寺设置八案。")
    relation(w, i, group, case, "统称与实例", main,
             f"{title}是南宋太府寺八案之一。")
    relation(w, i, parent, case, "上下级机构", main,
             f"{title}隶南宋太府寺。")
    return {parent_eid, group_eid, case_eid}, case


def add_case_children(w, i, case, touched, titles):
    main = F[i]["text"]
    for title in titles:
        eid, child = exact_state(
            w, i, title, "机构", "南宋（太府寺八案制）",
            "由太府寺办事案管辖", main, "太府寺所属局务",
            f"建立{F[i]['title']}所辖{title}节点。",
        )
        relation(w, i, case, child, "上下级机构", main,
                 f"{F[i]['title']}辖{title}。")
        touched.add(eid)


def entry621():
    i, main = 621, F[621]["text"]
    w = W(i)
    source_eid, source = exact_state(
        w, i, "太府寺市易案", "机构", "北宋元丰新制",
        "太府寺九案之一，掌市易平准事务", main,
        "太府寺办事案", "复用太府寺市易案改名前节点。",
    )
    eid, target = exact_state(
        w, i, "太府寺平准案", "机构", "北宋元符三年五月十七日",
        "由太府寺市易案改名", main, "太府寺办事案",
        "建立太府寺平准案改名节点。",
    )
    relation(w, i, source, target, "前后演变", main,
             "元符三年五月十七日市易案改名平准案。")
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), target,
             "上下级机构", main, "平准案为太府寺办事案。")
    finish(w, {source_eid, eid}, "整理太府寺市易案改名平准案时间链。")


def entry622():
    i = 622
    w = W(i)
    touched, case = south_treasury_case(
        w, i, "太府寺第一案",
        "掌批发官员俸料文历、宗室孤遗钱米及诸司局所请给，辖四粮料院与四审计司",
    )
    add_case_children(w, i, case, touched, ("四粮料院", "四审计司"))
    finish(w, touched, "整理太府寺第一案职掌、八案实例与所辖机构时间链。")


def entry623():
    i = 623
    w = W(i)
    touched, _ = south_treasury_case(
        w, i, "太府寺第二案", "职掌与第一案相同，内部另有分工",
    )
    finish(w, touched, "整理太府寺第二案职掌与八案实例时间链。")


def entry624():
    i = 624
    w = W(i)
    touched, case = south_treasury_case(
        w, i, "太府寺第三案",
        "掌支付或采购三省、枢密院、六部等处所需钱物",
    )
    add_case_children(
        w, i, case, touched,
        ("杂买务", "杂卖场", "编估局", "打套局", "交引库", "祗候库"),
    )
    finish(w, touched, "整理太府寺第三案职掌、八案实例与所辖机构时间链。")


def entry625():
    i = 625
    w = W(i)
    touched, _ = south_treasury_case(
        w, i, "太府寺第四案", "职掌与第三案相同，内部另有分工",
    )
    finish(w, touched, "整理太府寺第四案职掌与八案实例时间链。")


def entry626():
    i = 626
    w = W(i)
    touched, case = south_treasury_case(
        w, i, "太府寺第五案",
        "掌拘押催理四方财赋交纳左藏库、纲运钱物起发及押纲官酬赏",
    )
    add_case_children(w, i, case, touched, ("左藏东库", "左藏西库"))
    finish(w, touched, "整理太府寺第五案职掌、八案实例与所辖二库时间链。")


def entry627():
    i = 627
    w = W(i)
    touched, _ = south_treasury_case(
        w, i, "太府寺第六案", "职掌与第五案相同，内部另有分工",
    )
    finish(w, touched, "整理太府寺第六案职掌与八案实例时间链。")


def entry628():
    i = 628
    w = W(i)
    touched, case = south_treasury_case(
        w, i, "太府寺药案",
        "掌催促点检药材收买及修和汤药，以供诸药局给卖",
    )
    add_case_children(w, i, case, touched, ("和剂局", "杂买务", "药材所"))
    finish(w, touched, "整理太府寺药案职掌、八案实例与所辖机构时间链。")


def entry629():
    i = 629
    w = W(i)
    touched, _ = south_treasury_case(
        w, i, "太府寺监交案",
        "随太府寺丞、主簿赴左藏库监督交纳纲运钱物并审验诈伪隐漏",
    )
    finish(w, touched, "整理太府寺监交案职掌与八案实例时间链。")


def entry630():
    i, main = 630, F[630]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "牙人", "官职", "南宋绍兴元年二月四日",
        "召募平民充，替和剂局收买并鉴别药材、说合交易，定额四员",
        main, "太府寺公人", "建立太府寺牙人身份、职掌与定额。",
        officer="公人",
    )
    parent_eid, parent = exact_state(
        w, i, "太府寺", "机构", "南宋绍兴元年",
        "复置后设置牙人四员", main, "南宋财货机构",
        "建立绍兴元年太府寺牙人编制承载节点。",
    )
    staff(w, i, parent, post, main, "绍兴元年太府寺置牙人四员。",
          quota=4, staff_type="公人")
    finish(w, {eid, parent_eid}, "整理太府寺牙人职掌、来源与定额时间链。")


def entry631():
    i, main = 631, F[631]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w, touched = W(i), set()
    eid, jin = exact_state(
        w, i, "左藏库", "机构", "晋", "‘左藏’名称始见",
        history, "中央财库", "建立左藏名称源流。", "职源与沿革",
    )
    _, tang = exact_state(
        w, i, "左藏库", "机构", "唐", "始设左藏库",
        history, "中央财库", "建立唐代左藏库源流。", "职源与沿革",
    )
    _, song = exact_state(
        w, i, "左藏库", "机构", "宋初",
        "沿置，受纳四方财赋，以供经费、俸禄与赐赉",
        main, "中央财库", "建立宋初左藏库及职能节点。",
    )
    cite(w, "Timepoints", song, i, duty, "补充左藏库总体职能。", "职能")
    _, three = exact_state(
        w, i, "左藏库", "机构", "北宋太平兴国二年正月五日",
        "分为三库，分别储藏钱币、金银与匹帛",
        history, "中央财库", "建立太平兴国二年分库节点。", "职源与沿革",
    )
    _, split = exact_state(
        w, i, "左藏库", "机构", "北宋淳化三年十一月",
        "与右藏库分掌支给和收纳，左藏库主支给",
        history, "中央财库", "建立淳化三年左右藏分置节点。", "职源与沿革",
    )
    right_eid, right = exact_state(
        w, i, "右藏库", "机构", "北宋淳化三年十一月",
        "由左藏库分出，主收纳", history, "中央财库",
        "建立右藏库分置节点。", "职源与沿革",
    )
    relation(w, i, three, right, "前后演变", history,
             "淳化三年左藏库分出右藏库。", "职源与沿革")
    _, reunified = exact_state(
        w, i, "左藏库", "机构", "北宋淳化四年",
        "右藏库废并后，下分四类库藏", history, "中央财库",
        "建立淳化四年并库节点。", "职源与沿革",
    )
    _, right_abolished = exact_state(
        w, i, "右藏库", "机构", "北宋淳化四年", "废置并归左藏库",
        history, "中央财库", "建立右藏库废置节点。", "职源与沿革",
    )
    relation(w, i, right_abolished, reunified, "前后演变", history,
             "淳化四年废右藏库，并归左藏库。", "职源与沿革")
    for title in (
        "左藏钱库", "左藏金银库", "左藏丝绵库",
        "左藏生色匹帛、杂色匹帛库",
    ):
        child_eid, child = exact_state(
            w, i, title, "机构", "北宋淳化四年", "左藏库下分库藏",
            history, "左藏分库", f"建立淳化四年{title}节点。", "职源与沿革",
        )
        relation(w, i, reunified, child, "上下级机构", history,
                 f"淳化四年左藏库下分{title}。", "职源与沿革")
        touched.add(child_eid)
    _, merged = exact_state(
        w, i, "左藏库", "机构", "北宋大中祥符二年冬",
        "钱库、金银库、丝绵库合并，与生色匹库、杂色匹库合为三库",
        history, "中央财库", "建立大中祥符二年并库节点。", "职源与沿革",
    )
    _, two = exact_state(
        w, i, "左藏库", "机构", "北宋大中祥符八年十二月二十五日",
        "并生色、杂色匹帛二库，分左藏南库、左藏北库二库",
        history, "中央财库", "建立大中祥符八年二库节点。", "职源与沿革",
    )
    north_south = []
    for title in ("左藏南库", "左藏北库"):
        child_eid, child = exact_state(
            w, i, title, "机构", "北宋大中祥符八年十二月二十五日",
            "左藏库所分二库之一", history, "左藏分库",
            f"建立{title}节点。", "职源与沿革",
        )
        relation(w, i, two, child, "上下级机构", history,
                 f"大中祥符八年左藏库分{title}。", "职源与沿革")
        north_south.append(child)
        touched.add(child_eid)
    _, east_west = exact_state(
        w, i, "左藏库", "机构", "北宋政和六年",
        "新建二库东、西并立，改称左藏东库、左藏西库",
        history, "中央财库", "建立政和六年东、西库节点。", "职源与沿革",
    )
    east_west_tps = []
    for old, title, content in zip(
        north_south, ("左藏东库", "左藏西库"),
        ("储钱币、帛绳", "储金银丝纩"),
    ):
        child_eid, child = exact_state(
            w, i, title, "机构", "北宋政和六年", content,
            history, "左藏分库", f"建立政和六年{title}节点。", "职源与沿革",
        )
        cite(w, "Timepoints", child, i, duty, f"补充{title}储藏职能。", "职能")
        relation(w, i, old, child, "前后演变", history,
                 f"政和六年旧库改称{title}。", "职源与沿革")
        relation(w, i, east_west, child, "上下级机构", history,
                 f"政和六年左藏库分{title}。", "职源与沿革")
        east_west_tps.append(child)
        touched.add(child_eid)
    _, reform_treasury = exact_state(
        w, i, "左藏库", "机构", "北宋元丰新制",
        "元丰改制后隶太府寺、户部",
        main, "中央财库", "建立元丰改制后隶属节点。",
    )
    for parent_title in ("三司", "太府寺", "户部"):
        parent_eid, parent = exact_state(
            w, i, parent_title, "机构", "北宋元丰新制" if parent_title != "三司" else "宋前期",
            f"左藏库曾隶{parent_title}", main,
            "中央财赋机构", f"建立左藏库隶{parent_title}的承载节点。",
        )
        child = song if parent_title == "三司" else reform_treasury
        relation(w, i, parent, child, "上下级机构", main,
                 f"左藏库在相应时期隶{parent_title}。")
        touched.add(parent_eid)
    _, south_system = exact_state(
        w, i, "左藏库", "机构", "南宋绍兴三十二年七月十八日",
        "御前桩管激赏库拨归后，增为东、西、南三库",
        history, "中央财库", "建立绍兴三十二年三库节点。", "职源与沿革",
    )
    south_eid, south = exact_state(
        w, i, "左藏南库", "机构", "南宋绍兴三十二年七月十八日",
        "御前桩管激赏库拨归左藏库后所称南库",
        history, "左藏分库", "建立左藏南库加入三库节点。", "职源与沿革",
    )
    relation(w, i, south_system, south, "上下级机构", history,
             "绍兴三十二年左藏库增设南库。", "职源与沿革")
    _, reduced = exact_state(
        w, i, "左藏库", "机构", "南宋淳熙十年六月二十八日",
        "南库拨隶户部后，仍分东、西二库",
        history, "中央财库", "建立淳熙十年恢复二库节点。", "职源与沿革",
    )
    touched.update((eid, right_eid, south_eid))

    monitor_eid, monitor = exact_state(
        w, i, "监左藏库", "官职", "宋代（左藏库官属）",
        "领左藏库事，通管左藏二库", roster, "左藏库监官",
        "建立左藏库监官早期定额。", "编制", officer="监官",
    )
    staff(w, i, song, monitor, roster, "左藏库监官四员，通管二库。",
          "编制", quota=4, staff_type="监官")
    _, monitor_parent = exact_state(
        w, i, "左藏库", "机构", "北宋熙宁九年后",
        "监官增为五员，分掌后称东、西二库的库藏",
        roster, "中央财库", "建立熙宁九年后监官承载节点。", "编制",
    )
    _, monitor_five = exact_state(
        w, i, "监左藏库", "官职", "北宋熙宁九年后",
        "增为五员：东库二员一文一武，西库三员二文一武",
        roster, "左藏库监官", "建立熙宁九年后监官定额。", "编制",
        officer="监官",
    )
    staff(w, i, monitor_parent, monitor_five, roster,
          "熙宁九年后左藏库监官增为五员。", "编制",
          quota=5, staff_type="监官")
    office_staff_tps = []
    for title in ("左藏东库", "左藏西库"):
        office_eid, office_tp = exact_state(
            w, i, title, "机构", "宋代（左藏库官属）",
            "设置官属", roster, "左藏分库",
            f"建立{title}官属承载节点。", "编制",
        )
        office_staff_tps.append(office_tp)
        touched.add(office_eid)
    for title, parent, event in (
        ("都门官", office_staff_tps[1], "左藏西库守门官"),
        ("中门官", office_staff_tps[0], "左藏东库守门官"),
    ):
        post_eid, post = exact_state(
            w, i, title, "官职", "宋代（左藏库官属）", event,
            roster, "左藏库门官", f"建立{title}编制。", "编制",
            officer="门官",
        )
        staff(w, i, parent, post, roster, f"左藏库置{title}一员。",
              "编制", quota=1, staff_type="门官")
        touched.add(post_eid)
    detention_eid, detention = exact_state(
        w, i, "拘押官", "官职", "宋代（左藏库官属）",
        "隶左藏东、西库", roster, "左藏库差遣官",
        "建立拘押官早期定额。", "编制", officer="小使臣",
    )
    for parent in office_staff_tps:
        staff(w, i, parent, detention, roster, "左藏东、西库置拘押官六员。",
              "编制", quota=6, staff_type="拘押官")
    detention_late_parents = []
    for title in ("左藏东库", "左藏西库"):
        office_eid, office_tp = exact_state(
            w, i, title, "机构", "南宋嘉定三年四月",
            "拘押官定为二员", roster, "左藏分库",
            f"建立嘉定三年{title}拘押官承载节点。", "编制",
        )
        detention_late_parents.append(office_tp)
        touched.add(office_eid)
    _, detention_two = exact_state(
        w, i, "拘押官", "官职", "南宋嘉定三年四月", "定为二员",
        roster, "左藏库差遣官", "建立嘉定三年拘押官定额。", "编制",
        officer="小使臣",
    )
    for parent in detention_late_parents:
        staff(w, i, parent, detention_two, roster, "嘉定三年拘押官定为二员。",
              "编制", quota=2, staff_type="拘押官")
    south_staff_parents = []
    for title in ("左藏东库", "左藏西库"):
        office_eid, office_tp = exact_state(
            w, i, title, "机构", "南宋绍兴元年（左藏东、西库吏额）",
            "分上、下界设置专知、副知、押司、手分、书手、库级与兵士",
            roster, "左藏分库", f"建立绍兴元年{title}吏额承载节点。", "编制",
        )
        south_staff_parents.append(office_tp)
        touched.add(office_eid)
    east_specs = (
        ("专知官", 2, "专知官"), ("副知", 2, "副知"),
        ("押司官", 2, "押司官"), ("手分", 12, "吏"),
        ("书手", 3, "吏"), ("库级", 20, "吏役"), ("兵士", 25, "兵士"),
    )
    west_specs = (
        ("专知官", 2, "专知官"), ("副知", 4, "副知"),
        ("押司官", 2, "押司官"), ("手分", 12, "吏"),
        ("书手", 3, "吏"), ("库级", 25, "吏役"), ("兵士", 25, "兵士"),
    )
    for parent, specs, label in zip(
        south_staff_parents, (east_specs, west_specs), ("左藏东库", "左藏西库")
    ):
        for title, quota, officer in specs:
            post_eid, post = exact_state(
                w, i, title, "官职", "南宋绍兴元年（左藏东、西库吏额）",
                f"绍兴元年左藏东、西库上、下界均置{title}",
                roster, "左藏库吏役", f"建立绍兴元年{label}{title}定额。", "编制",
                officer=officer,
            )
            staff(w, i, parent, post, roster, f"绍兴元年{label}置{title}{quota}名。",
                  "编制", quota=quota, staff_type=officer)
            touched.add(post_eid)
    group_eid, group = exact_state(
        w, i, "左藏东、西库", "机构", "南宋绍兴元年（左藏东、西库吏额）",
        "左藏东库与左藏西库的合称", roster, "左藏二库统称",
        "建立绍兴元年左藏东、西库合称节点。", "编制",
    )
    for member in south_staff_parents:
        relation(w, i, group, member, "统称与实例", roster,
                 "左藏东库或左藏西库是左藏东、西库的实例。", "编制")
    touched.add(group_eid)
    for title, quota, officer in (("门手分", 2, "吏"), ("库子", 2, "吏役")):
        post_eid, post = exact_state(
            w, i, title, "官职", "南宋绍兴元年（左藏东、西库吏额）",
            f"左藏东、西库门共置{title}{quota}名",
            roster, "左藏库吏役", f"建立绍兴元年左藏库{title}定额。", "编制",
            officer=officer,
        )
        staff(w, i, group, post, roster, f"左藏东、西库门共置{title}{quota}名。",
              "编制", quota=quota, staff_type=officer)
        touched.add(post_eid)
    touched.update((monitor_eid, detention_eid))
    alias_note(w, i, song, aliases, "简称与别名")
    finish(w, touched, "整理左藏库源流、分合改名、隶属、职能与主要编制时间链。")


def entry632():
    i, main, aliases = 632, F[632]["text"], field(632, "简称与别名")
    w = W(i)
    eid, post = exact_state(
        w, i, "监左藏库", "官职", "宋代（左藏库官属）",
        "领左藏库事，通管左藏二库",
        main, "左藏库监官", "补充监左藏库资格与职掌。",
        officer="差遣官", grade="文臣京朝官",
    )
    staff(w, i, tp(w, "左藏库", "机构", "宋初"), post, main,
          "监左藏库领左藏库事。", staff_type="监官")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, {eid}, "整理监左藏库职掌、资格与简称时间链。")


def entry633():
    i, main, aliases = 633, F[633]["text"], field(633, "简称")
    w, touched = W(i), set()
    eid, post = exact_state(
        w, i, "提辖左藏东、西库", "官职", "南宋绍兴二十七年",
        "由户部差寺监丞或主簿一员充，总辖左藏东、西库，为储才之地",
        main, "四院提辖官", "建立提辖左藏东、西库始置、资格与职掌。",
        officer="提辖官", grade="寺监丞或主簿",
    )
    for title in ("左藏东库", "左藏西库"):
        parent_eid, parent = exact_state(
            w, i, title, "机构", "南宋绍兴二十七年",
            "由提辖左藏东、西库总辖", main, "左藏分库",
            f"建立{title}提辖官承载节点。",
        )
        staff(w, i, parent, post, main, f"提辖官总辖{title}。",
              quota=1, staff_type="提辖官")
        touched.add(parent_eid)
    group_eid, group = exact_state(
        w, i, "四院提辖官", "官职", "南宋绍兴二十七年",
        "左藏库、榷货务都茶场、文思院、杂买务杂卖场四类提辖官的统称",
        main, "提辖官统称", "建立四院提辖官统称节点。",
        officer="提辖官",
    )
    relation(w, i, group, post, "统称与实例", main,
             "提辖左藏东、西库是四院提辖官之一。")
    alias_note(w, i, post, aliases, "简称")
    touched.update((eid, group_eid))
    finish(w, touched, "整理提辖左藏东、西库始置、总辖、品位去向与四院实例时间链。")


def entry634():
    i, main = 634, F[634]["text"]
    w, touched = W(i), set()
    eid, post = exact_state(
        w, i, "拘押官", "官职", "宋代（左藏库官属）",
        "隶左藏东、西库",
        main, "左藏库差遣官", "补充拘押官资格、职掌与任期。",
        officer="小使臣",
    )
    for title in ("左藏东库", "左藏西库"):
        parent_eid, parent = exact_state(
            w, i, title, "机构", "宋代（左藏库官属）",
            "设置官属",
            main, "左藏分库", f"建立{title}拘押官承载节点。",
        )
        staff(w, i, parent, post, main, f"拘押官隶{title}。",
              staff_type="拘押官")
        touched.add(parent_eid)
    touched.add(eid)
    finish(w, touched, "整理拘押官隶属、资格、职掌与任期时间链。")


def door_officer(i, title, parent_title):
    main = F[i]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, title, "官职", "宋代（左藏库官属）",
        f"{parent_title}守门官", main, "左藏库门官",
        f"建立{title}职掌节点。", officer="门官",
    )
    parent_eid, parent = exact_state(
        w, i, parent_title, "机构", "宋代（左藏库官属）",
        "设置官属", main, "左藏分库",
        f"建立{parent_title}门官承载节点。",
    )
    staff(w, i, parent, post, main, f"{title}为{parent_title}守门官。",
          staff_type="门官")
    finish(w, {eid, parent_eid}, f"整理{title}职掌与隶属时间链。")


def entry635():
    door_officer(635, "都门官", "左藏西库")


def entry636():
    door_officer(636, "中门官", "左藏东库")


def entry637():
    i, main, short = 637, F[637]["text"], field(637, "省称")
    w, touched = W(i), set()
    group_eid, group = exact_state(
        w, i, "左藏库都中门官", "官职", "宋代（左藏库官属）",
        "左藏西库都门官与左藏东库中门官的连称",
        main, "左藏库门官统称", "建立左藏库都中门官连称节点。",
        officer="门官统称",
    )
    for title, parent_title in (("都门官", "左藏西库"), ("中门官", "左藏东库")):
        member_eid, member = exact_state(
            w, i, title, "官职", "宋代（左藏库官属）",
            f"{parent_title}守门官", short, "左藏库门官",
            f"补充{title}为都中门官实例。", "省称", officer="门官",
        )
        relation(w, i, group, member, "统称与实例", main,
                 f"{title}是左藏库都中门官之一。")
        touched.add(member_eid)
    alias_note(w, i, group, short, "省称")
    touched.add(group_eid)
    finish(w, touched, "整理左藏库都中门官连称、实例与省称时间链。")


def entry638():
    i, main = 638, F[638]["text"]
    history, duty, aliases = field(i, "职源与沿革"), field(i, "职掌"), field(i, "简称")
    w, touched = W(i), set()
    source_eid, source = exact_state(
        w, i, "御前桩管激赏库", "机构", "南宋绍兴三十二年七月十八日",
        "直隶御前的激赏财库", history, "御前财库",
        "建立左藏南库改名前身。", "职源与沿革",
    )
    eid, south = exact_state(
        w, i, "左藏南库", "机构", "南宋隆兴元年七月二十四日",
        "由御前桩管激赏库改名，取诸路原供户部财赋以应副军期急需，直隶御前",
        history, "御前财库", "建立隆兴元年左藏南库节点。", "职源与沿革",
    )
    cite(w, "Timepoints", south, i, duty, "补充左藏南库职掌。", "职掌")
    relation(w, i, source, south, "前后演变", history,
             "隆兴元年御前桩管激赏库改名左藏南库。", "职源与沿革")
    _, transferred = exact_state(
        w, i, "左藏南库", "机构", "南宋淳熙十年六月二十八日",
        "改隶户部", main, "户部所属财库",
        "建立淳熙十年左藏南库改隶节点。",
    )
    parent_eid, parent = exact_state(
        w, i, "户部", "机构", "南宋淳熙十年六月二十八日",
        "接管左藏南库", main, "尚书省财赋机构",
        "建立户部接管左藏南库节点。",
    )
    relation(w, i, parent, transferred, "上下级机构", main,
             "淳熙十年左藏南库归隶户部。")
    target_eid, target = exact_state(
        w, i, "左藏西上库", "机构", "南宋淳熙十二年正月十三日",
        "由左藏南库改名，隶户部", history, "户部所属财库",
        "建立左藏西上库改名节点。", "职源与沿革",
    )
    relation(w, i, transferred, target, "前后演变", history,
             "淳熙十二年左藏南库改名左藏西上库。", "职源与沿革")
    alias_note(w, i, south, aliases, "简称")
    touched.update((source_eid, eid, parent_eid, target_eid))
    finish(w, touched, "整理左藏南库由来、御前与户部隶属、职掌及改名时间链。")


def entry639():
    i, main = 639, F[639]["text"]
    w, touched = W(i), set()
    source_eid, source = exact_state(
        w, i, "左藏南库", "机构", "南宋淳熙十年六月二十八日",
        "改隶户部",
        main, "户部所属财库", "复用左藏南库改名前节点。",
    )
    eid, current = exact_state(
        w, i, "左藏西上库", "机构", "南宋淳熙十二年正月十三日",
        "由左藏南库改名，隶户部",
        main, "户部所属财库", "建立左藏西上库节点。",
    )
    relation(w, i, source, current, "前后演变", main,
             "淳熙十二年左藏南库改名左藏西上库。")
    parent_eid, parent = exact_state(
        w, i, "户部", "机构", "南宋淳熙十二年正月十三日",
        "左藏西上库隶户部", main, "尚书省财赋机构",
        "建立左藏西上库隶户部承载节点。",
    )
    relation(w, i, parent, current, "上下级机构", main,
             "左藏西上库隶户部。")
    target_eid, target = exact_state(
        w, i, "封桩下库", "机构", "南宋绍熙元年十月二日",
        "由左藏西上库改名，隶户部", main, "户部所属财库",
        "建立封桩下库改名节点。",
    )
    relation(w, i, current, target, "前后演变", main,
             "绍熙元年左藏西上库改名封桩下库。")
    touched.update((source_eid, eid, parent_eid, target_eid))
    finish(w, touched, "整理左藏西上库由来、隶属与改名时间链。")


def entry640():
    i, main = 640, F[640]["text"]
    w, touched = W(i), set()
    source_eid, source = exact_state(
        w, i, "左藏西上库", "机构", "南宋淳熙十二年正月十三日",
        "由左藏南库改名，隶户部", main, "户部所属财库",
        "复用封桩下库改名前节点。",
    )
    eid, founded = exact_state(
        w, i, "封桩下库", "机构", "南宋绍熙元年十月二日",
        "由左藏西上库改名，隶户部",
        main, "户部所属财库", "建立封桩下库改名、位置与初置节点。",
    )
    relation(w, i, source, founded, "前后演变", main,
             "绍熙元年左藏西上库改名封桩下库。")
    ministry_eid, ministry = exact_state(
        w, i, "户部", "机构", "南宋绍熙元年十月二日",
        "封桩下库初隶户部", main, "尚书省财赋机构",
        "建立封桩下库初隶户部节点。",
    )
    relation(w, i, ministry, founded, "上下级机构", main,
             "封桩下库初隶户部。")
    overseer_eid, overseer = exact_state(
        w, i, "提辖封桩下库", "官职", "南宋绍熙元年十月二日",
        "初设，领封桩下库事，为四院提辖官之一",
        main, "四院提辖官", "建立封桩下库提辖官初置节点。",
        officer="提辖官",
    )
    staff(w, i, founded, overseer, main, "封桩下库初设提辖官一员。",
          quota=1, staff_type="提辖官")
    _, merged = exact_state(
        w, i, "封桩下库", "机构", "南宋嘉定七年",
        "并入提领封桩上库所，改隶尚书都司，与封桩上库分工",
        main, "尚书都司所属财库", "建立嘉定七年并所改隶节点。",
    )
    office_eid, office = exact_state(
        w, i, "提领封桩上库所", "机构", "南宋嘉定七年",
        "总领封桩上、下库", main, "尚书都司所属机构",
        "建立提领封桩上库所总领节点。",
    )
    department_eid, department = exact_state(
        w, i, "尚书都司", "机构", "南宋嘉定七年",
        "接管并入提领封桩上库所的封桩下库",
        main, "尚书省机构", "建立尚书都司接管节点。",
    )
    relation(w, i, department, office, "上下级机构", main,
             "嘉定七年提领封桩上库所隶尚书都司。")
    relation(w, i, office, merged, "上下级机构", main,
             "嘉定七年封桩下库并入提领封桩上库所。")
    for title, officer in (("封桩下库干办公事", "干办公事"), ("封桩下库掾属", "掾属")):
        post_eid, post = exact_state(
            w, i, title, "官职", "南宋绍定六年",
            f"封桩下库置{officer}一员", main, "封桩下库官属",
            f"建立{title}定额。", officer=officer,
        )
        staff(w, i, merged, post, main, f"绍定六年封桩下库置{officer}一员。",
              quota=1, staff_type=officer)
        touched.add(post_eid)
    touched.update((source_eid, eid, ministry_eid, overseer_eid, office_eid, department_eid))
    finish(w, touched, "整理封桩下库改名、隶属变化、主管机构与官属定额时间链。")


def main():
    assert [F[i]["title"] for i in range(621, 641)] == [
        "太府寺平准案", "太府寺第一案", "太府寺第二案", "太府寺第三案",
        "太府寺第四案", "太府寺第五案", "太府寺第六案", "太府寺药案",
        "太府寺监交案", "牙人", "左藏库", "监左藏库",
        "提辖左藏东、西库", "拘押官", "都门官", "中门官",
        "左藏库都中门官", "左藏南库", "左藏西上库", "封桩下库",
    ]
    for i in range(621, 641):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
