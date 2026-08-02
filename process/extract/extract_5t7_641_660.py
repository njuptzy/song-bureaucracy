#!/usr/bin/env python3
"""提取 chapter5t7 第641-660条：封桩诸库、内藏库系统与商税度量衡机构。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_621_640 as previous


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


F = {i: load(i) for i in range(641, 661)}
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
    "宋初": 960, "北宋建隆元年": 960.1,
    "北宋乾德三年三月": 965.2,
    "北宋太平兴国三年十月": 978.75,
    "北宋咸平六年前": 1002.9, "北宋咸平六年": 1003,
    "北宋景德四年四月二十六日": 1007.32,
    "北宋大中祥符二年五月十二日": 1009.36,
    "北宋大中祥符八年": 1015,
    "北宋康定元年九月": 1040.72,
    "宋前期": 980,
    "北宋（元丰改制前）": 1000,
    "北宋（先隶三司）": 1000.1,
    "宋代（未载具体年月）": 1000.2,
    "北宋熙宁三年三月十四日": 1070.2,
    "北宋熙宁三年十二月十一日": 1070.94,
    "北宋（隶都提举市易司）": 1072,
    "北宋熙宁八年五月二十四日": 1075.39,
    "北宋熙宁十年三月": 1077.2,
    "北宋元丰元年六月十二日": 1078.45,
    "北宋元丰元年十二月二十七日": 1078.98,
    "北宋元丰三年": 1080, "北宋元丰新制": 1082.1,
    "北宋元祐三年三月十八日": 1088.21,
    "北宋崇宁二年五月十四日": 1103.36,
    "北宋政和四年": 1114,
    "南宋": 1127, "南宋初": 1127.1,
    "南宋淳熙六年八月": 1179.62,
    "南宋绍熙元年十月二日": 1190.76,
    "宋代（商税务）": 1050.4,
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
    """建立或复用关系端点；复用时不覆盖该实体同时点已有事件。"""
    return state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def entry641():
    i, main = 641, F[641]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "提辖封桩下库", "官职", "南宋绍熙元年十月二日",
        "初设，领封桩下库事，为四院提辖官之一", main,
        "封桩下库差遣", "复用封桩下库提辖官节点并补本条证据。",
        officer="提辖官",
    )
    parent = tp(w, "封桩下库", "机构", "南宋绍熙元年十月二日")
    staff(w, i, parent, post, main, "提辖封桩下库领本库事。",
          quota=1, staff_type="提辖官")
    finish(w, {eid}, "补证提辖封桩下库职掌与四辖官身份。")


def entry642():
    i, main, origin, duty = 642, F[642]["text"], field(642, "职源"), field(642, "职掌")
    w, touched = W(i), set()
    parent_eid, parent = support_state(
        w, i, "尚书都司", "机构", "南宋淳熙六年八月",
        "主管新置封桩上库", main, "尚书省都司",
        "建立尚书都司主管封桩上库的承载节点。",
    )
    eid, store = exact_state(
        w, i, "封桩上库", "机构", "南宋淳熙六年八月",
        "创置，隶尚书都司，收管封桩钱供备紧急支用", origin,
        "尚书都司监当库", "建立封桩上库创置节点。", "职源",
    )
    relation(w, i, parent, store, "上下级机构", main,
             "封桩上库隶尚书省都司。")
    post_eid, post = exact_state(
        w, i, "提辖封桩上库", "官职", "南宋淳熙六年八月",
        "封桩上库设提辖官领库事", duty, "封桩上库差遣",
        "建立提辖封桩上库节点。", "职掌", officer="提辖官",
    )
    staff(w, i, store, post, duty, "封桩上库设提辖官。", "职掌",
          quota=1, staff_type="提辖官")
    touched.update((parent_eid, eid, post_eid))
    finish(w, touched, "整理封桩上库创置、隶属、职掌与提辖官时间链。")


def entry643():
    i, main = 643, F[643]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "提辖封桩上库", "官职", "南宋淳熙六年八月",
        "封桩上库设提辖官领库事", main, "封桩上库差遣",
        "复用提辖封桩上库节点并补本条证据。", officer="提辖官",
    )
    staff(w, i, tp(w, "封桩上库", "机构", "南宋淳熙六年八月"),
          post, main, "提辖封桩上库领本库事。",
          quota=1, staff_type="提辖官")
    finish(w, {eid}, "补证提辖封桩上库职掌与四辖官身份。")


def entry644():
    i = 644
    main, origin, function, roster = (
        F[i]["text"], field(i, "职源"), field(i, "职能"), field(i, "编制")
    )
    w, touched = W(i), set()
    source_eid, source = exact_state(
        w, i, "左藏北库", "机构", "北宋太平兴国三年十月",
        "分出内藏库", origin, "左藏库所属库",
        "建立左藏北库分出内藏库节点。", "职源",
    )
    eid, early = exact_state(
        w, i, "内藏库", "机构", "北宋太平兴国三年十月",
        "分左藏北库始置，为皇帝特藏库，备邦国非常之用", origin,
        "御前监当库", "建立内藏库始置节点。", "职源",
    )
    relation(w, i, source, early, "前后演变", origin,
             "太平兴国三年分左藏北库为内藏库。", "职源")
    west_eid, west = exact_state(
        w, i, "内藏西库", "机构", "北宋景德四年四月二十六日",
        "增设，并以景福殿库归隶", origin, "内藏库分库",
        "建立内藏西库增设节点。", "职源",
    )
    _, parent_west = support_state(
        w, i, "内藏库", "机构", "北宋景德四年四月二十六日",
        "增设内藏西库", origin, "御前监当库",
        "建立内藏库增设西库承载节点。", "职源",
    )
    relation(w, i, parent_west, west, "上下级机构", origin,
             "内藏库增设内藏西库。", "职源")
    hall_eid, hall = exact_state(
        w, i, "景福殿库", "机构", "北宋景德四年四月二十六日",
        "归隶内藏西库", origin, "内藏西库所属库",
        "建立景福殿库归隶节点。", "职源",
    )
    relation(w, i, west, hall, "上下级机构", origin,
             "景福殿库归隶内藏西库。", "职源")
    _, four = exact_state(
        w, i, "内藏库", "机构", "北宋大中祥符八年",
        "分为金银、珠玉香药、锦帛、钱四库", origin, "御前监当库",
        "建立内藏库分四库节点。", "职源",
    )
    for title in ("金银库", "珠玉香药库", "锦帛库", "钱库"):
        child_eid, child = exact_state(
            w, i, title, "机构", "北宋大中祥符八年",
            "内藏库所分四库之一", origin, "内藏库分库",
            f"建立内藏库所分{title}节点。", "职源",
        )
        relation(w, i, four, child, "上下级机构", origin,
                 f"{title}为大中祥符八年内藏库所分之库。", "职源")
        touched.add(child_eid)
    _, south = exact_state(
        w, i, "内藏库", "机构", "南宋", "南宋沿置", origin,
        "御前监当库", "建立内藏库南宋沿置节点。", "职源",
    )
    roles = (
        ("监内藏库", "监官", None, "诸司使副、内侍充监官"),
        ("勾当内藏库", "勾当官", None, "诸司使副、内侍充勾当官"),
        ("都监内藏库", "都监", None, "诸司使副、内侍充都监"),
        ("点检内藏库", "高品内侍官", 1, "高品内侍官一人点检内藏库"),
        ("提点内藏库", "提点官", None, "点检官依秩品升迁可称提点内藏库"),
        ("提举内藏库", "提举官", None, "点检官依秩品升迁可称提举内藏库"),
        ("内藏库专知", "吏", None, "内藏库吏额专知"),
        ("内藏库副知", "吏", None, "内藏库吏额副知"),
    )
    for title, officer, quota, event in roles:
        role_eid, post = exact_state(
            w, i, title, "官职", "北宋太平兴国三年十月", event,
            roster, "内藏库官吏", f"建立{title}职名与职制。", "编制", officer=officer,
        )
        staff(w, i, early, post, roster, f"内藏库设{title}。", "编制",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    cite(w, "Timepoints", early, i, function, "补证内藏库所备邦国非常之用。", "职能")
    touched.update((source_eid, eid, west_eid, hall_eid))
    finish(w, touched, "整理内藏库始置、分库、南宋沿置与官吏时间链。")


def entry645():
    assert F[645]["text"] == ""
    assert F[645]["fields"] == {"_placeholder": True, "__status__": "placeholder"}


def entry646():
    i = 646
    main, origin, duty = F[i]["text"], field(i, "职源与沿革"), field(i, "职掌")
    assert F[i]["page"] == "368"
    w, touched = W(i), set()
    group_eid, group = exact_state(
        w, i, "宜圣殿五库", "机构", "宋初",
        "分藏平定南北诸国所得瑰宝、金玉等的五库统称", origin,
        "内庭宝库统称", "建立宜圣殿五库统称节点。", "职源与沿革",
    )
    sources = []
    for title in ("宜圣殿内库", "穆清殿库", "崇圣殿库", "崇圣殿受纳真珠库", "崇圣乐器库"):
        child_eid, child = exact_state(
            w, i, title, "机构", "宋初", "宜圣殿五库之一", origin,
            "内庭宝库", f"建立{title}宋初节点。", "职源与沿革",
        )
        relation(w, i, group, child, "统称与实例", origin,
                 f"{title}是宜圣殿五库之一。", "职源与沿革")
        sources.append(child)
        touched.add(child_eid)
    eid, merged = exact_state(
        w, i, "奉宸库", "机构", "北宋康定元年九月",
        "宜圣殿五库合并为奉宸库，掌珠宝金银供宫廷消费", origin,
        "御前内庭宝库", "建立奉宸库合并创置节点。", "职源与沿革",
    )
    for child in sources:
        relation(w, i, child, merged, "前后演变", origin,
                 "康定元年宜圣殿五库合并为奉宸库。", "职源与沿革")
    _, ending = exact_state(
        w, i, "奉宸库", "机构", "北宋政和四年", "并入内藏库", origin,
        "御前内庭宝库", "建立奉宸库并入节点。", "职源与沿革",
    )
    inner_eid, inner = support_state(
        w, i, "内藏库", "机构", "北宋政和四年", "接收并入的奉宸库", origin,
        "御前监当库", "建立内藏库接收奉宸库承载节点。", "职源与沿革",
    )
    relation(w, i, ending, inner, "前后演变", origin,
             "政和四年奉宸库并入内藏库。", "职源与沿革")
    cite(w, "Timepoints", merged, i, duty, "补证奉宸库供宫廷消费的职掌。", "职掌")
    touched.update((group_eid, eid, inner_eid))
    finish(w, touched, "整理宜圣殿五库统称、合并为奉宸库及并入内藏库时间链。")


def entry647():
    i, main = 647, F[647]["text"]
    w, touched = W(i), set()
    three_eid, three = support_state(
        w, i, "三司", "机构", "北宋（元丰改制前）", "元丰改制前领祗候库", main,
        "北宋中央财政机构", "建立三司早期主管祗候库节点。",
    )
    eid, early = exact_state(
        w, i, "祗候库", "机构", "北宋（元丰改制前）",
        "设于开封横门外，隶三司，掌收贮钱帛器物以备传诏须索与殿廷赐予", main,
        "三司监当库", "建立祗候库元丰前节点。",
    )
    relation(w, i, three, early, "上下级机构", main, "祗候库早期隶三司。")
    _, reform = exact_state(
        w, i, "祗候库", "机构", "北宋元丰新制", "改隶太府寺", main,
        "太府寺所属监当库", "建立祗候库元丰后隶属节点。",
    )
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "祗候库元丰后隶太府寺。")
    clothes_eid, clothes = exact_state(
        w, i, "尚衣库", "机构", "北宋崇宁二年五月十四日",
        "并入祗候库", main, "宫廷服御库", "建立尚衣库并入节点。",
    )
    _, merged = exact_state(
        w, i, "祗候库", "机构", "北宋崇宁二年五月十四日",
        "并入尚衣库", main, "太府寺所属监当库", "建立祗候库接收尚衣库节点。",
    )
    relation(w, i, clothes, merged, "前后演变", main,
             "崇宁二年尚衣库并入祗候库。")
    role_eid, post = exact_state(
        w, i, "监祗候库", "官职", "北宋（元丰改制前）",
        "监管祗候库，设三人，由武臣诸司使副及内侍充", main,
        "祗候库监官", "建立监祗候库编制。", officer="监官",
    )
    staff(w, i, early, post, main, "祗候库设监官三人。", quota=3, staff_type="监官")
    touched.update((three_eid, eid, clothes_eid, role_eid))
    finish(w, touched, "整理祗候库隶属、尚衣库并入与监官编制时间链。")


def entry648():
    i, main = 648, F[648]["text"]
    w, touched = W(i), set()
    eid, origin = exact_state(
        w, i, "封桩库", "机构", "北宋乾德三年三月",
        "太祖于讲武殿后置内库，号封桩库，掌岁终国用赢余以备北伐与饥荒", main,
        "御前监当库", "建立北宋封桩库始置节点。",
    )
    _, end = exact_state(
        w, i, "封桩库", "机构", "北宋太平兴国三年十月",
        "改名景福内库", main, "御前监当库", "建立封桩库改名节点。",
    )
    target_eid, target = exact_state(
        w, i, "景福内库", "机构", "北宋太平兴国三年十月",
        "由封桩库改名，积岁余经费以备非常之用", main,
        "御前监当库", "建立景福内库改名始置节点。",
    )
    relation(w, i, end, target, "前后演变", main,
             "太平兴国三年封桩库改名景福内库。")
    touched.update((eid, target_eid))
    finish(w, touched, "整理北宋封桩库始置及改名景福内库时间链。")


def entry649():
    i, main = 649, F[649]["text"]
    w = W(i)
    eid, early = support_state(
        w, i, "景福内库", "机构", "北宋太平兴国三年十月",
        "由封桩库改名，积岁余经费以备非常之用", main,
        "御前监当库", "复用景福内库始置节点并补本条证据。",
    )
    _, expanded = exact_state(
        w, i, "景福内库", "机构", "北宋元丰元年十二月二十七日",
        "扩建以积聚金帛作恢复幽燕兵费，先后置以诗字命名的五十二库", main,
        "御前监当库", "建立景福内库元丰扩建节点。",
    )
    alias_note(w, i, expanded, field(i, "简称与别名"), "简称与别名")
    finish(w, {eid}, "整理景福内库改名来源、元丰扩建与简称时间链。")


def entry650():
    i, main = 650, F[650]["text"]
    w, touched = W(i), set()
    eid, origin = exact_state(
        w, i, "元丰库", "机构", "北宋元丰三年",
        "始置，掌朝廷封桩青苗、役法、坊场宽剩钱物", main,
        "中央封桩库", "建立元丰库始置与职掌节点。",
    )
    _, source = exact_state(
        w, i, "元丰库", "机构", "北宋元祐三年三月十八日",
        "与元祐库合并为元丰南库、元丰北库", main,
        "中央封桩库", "建立元丰库合并节点。",
    )
    you_eid, you = exact_state(
        w, i, "元祐库", "机构", "北宋元祐三年三月十八日",
        "与元丰库合并为元丰南库、元丰北库", main,
        "中央封桩库", "建立元祐库参与合并节点。",
    )
    group_eid, group = exact_state(
        w, i, "元丰南、北库", "机构", "北宋元祐三年三月十八日",
        "元丰库、元祐库合并后所分二库的统称", main,
        "中央封桩库统称", "建立元丰南、北库统称节点。",
    )
    relation(w, i, source, group, "前后演变", main,
             "元丰库参与合并为元丰南、北库。")
    relation(w, i, you, group, "前后演变", main,
             "元祐库参与合并为元丰南、北库。")
    for title in ("元丰南库", "元丰北库"):
        child_eid, child = exact_state(
            w, i, title, "机构", "北宋元祐三年三月十八日",
            "元丰库、元祐库合并后所分二库之一", main,
            "中央封桩库", f"建立{title}节点。",
        )
        relation(w, i, group, child, "统称与实例", main,
                 f"{title}是元丰南、北库之一。")
        touched.add(child_eid)
    post_eid, post = exact_state(
        w, i, "监元丰库", "官职", "北宋元丰三年",
        "监管元丰库，由承务郎以上曾任亲民官者充", main,
        "元丰库监官", "建立监元丰库差遣。", officer="监官",
    )
    staff(w, i, origin, post, main, "元丰库设监官。", staff_type="监官")
    touched.update((eid, you_eid, group_eid, post_eid))
    finish(w, touched, "整理元丰库始置、与元祐库合并、南北库实例与监官时间链。")


def entry651():
    i, main = 651, F[651]["text"]
    w, touched = W(i), set()
    three_eid, three = support_state(
        w, i, "三司", "机构", "北宋建隆元年", "领布库", main,
        "北宋中央财政机构", "建立三司早期主管布库节点。",
    )
    eid, origin = exact_state(
        w, i, "布库", "机构", "北宋建隆元年",
        "设于开封常乐坊，隶三司，掌收受诸州上供布以供国用", main,
        "中央布帛监当库", "建立布库创置与早期隶属节点。",
    )
    relation(w, i, three, origin, "上下级机构", main, "布库早期隶三司。")
    _, moved = exact_state(
        w, i, "布库", "机构", "北宋熙宁八年五月二十四日",
        "从常乐坊迁至顺城坊", main, "中央布帛监当库", "建立布库迁址节点。",
    )
    _, keys = exact_state(
        w, i, "布库", "机构", "北宋熙宁十年三月",
        "罢每日赴大内钥匙库请领锁钥，改由监门官收掌", main,
        "中央布帛监当库", "建立布库锁钥管理变更节点。",
    )
    _, reform = exact_state(
        w, i, "布库", "机构", "北宋元丰新制", "改隶太府寺", main,
        "太府寺所属监当库", "建立布库元丰后隶属节点。",
    )
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "布库后隶太府寺。")
    for title, officer, quota, event in (
        ("监布库", "监官", 2, "监管布库，文臣京朝官、武臣三班使臣充"),
        ("布库监门官", "内侍", 1, "收掌布库门禁与锁钥，由内侍充"),
    ):
        role_eid, post = exact_state(
            w, i, title, "官职", "北宋熙宁十年三月", event, main,
            "布库官属", f"建立{title}编制。", officer=officer,
        )
        staff(w, i, keys, post, main, f"布库设{title}。", quota=quota, staff_type=officer)
        touched.add(role_eid)
    touched.update((three_eid, eid))
    finish(w, touched, "整理布库设置、迁址、锁钥管理、隶属与官属时间链。")


def entry652():
    i, main = 652, F[652]["text"]
    w, touched = W(i), set()
    parent_eid, parent = support_state(
        w, i, "三司百官案", "机构", "北宋（元丰改制前）",
        "辖药蜜库", main, "三司办事案", "建立三司百官案辖药蜜库节点。",
    )
    eid, store = exact_state(
        w, i, "药蜜库", "机构", "北宋（元丰改制前）",
        "隶三司百官案，收贮糖、蜂蜜、药物供禁军马匹食用", main,
        "三司监当库", "建立药蜜库隶属与职掌节点。",
    )
    relation(w, i, parent, store, "上下级机构", main, "药蜜库隶三司百官案。")
    role_eid, post = exact_state(
        w, i, "监药蜜库", "官职", "北宋（元丰改制前）",
        "监管药蜜库，设三员", main, "药蜜库监官", "建立监药蜜库编制。", officer="监官",
    )
    staff(w, i, store, post, main, "药蜜库设监官三员。", quota=3, staff_type="监官")
    touched.update((parent_eid, eid, role_eid))
    finish(w, touched, "整理药蜜库隶属、职掌与监官编制时间链。")


def entry653():
    i, main = 653, F[653]["text"]
    w, touched = W(i), set()
    source_eid, source = exact_state(
        w, i, "茶库", "机构", "北宋咸平六年前", "初分二库", main,
        "中央茶叶监当库", "建立都茶库合并前茶库节点。",
    )
    eid, merged = exact_state(
        w, i, "都茶库", "机构", "北宋咸平六年",
        "二库合为一库并加‘都’字，掌收受诸路茶叶以供俸给、军食、赏赐与出售", main,
        "中央茶叶监当库", "建立都茶库合并改名节点。",
    )
    relation(w, i, source, merged, "前后演变", main, "咸平六年茶库二库合一加都字。")
    parent = tp(
        w, "都大提举在京诸司库务司", "机构",
        "北宋景德二年十月十五日",
    )
    relation(w, i, parent, merged, "上下级机构", main,
             "都茶库早期隶都大提举在京诸司库务司。")
    _, reform = exact_state(
        w, i, "都茶库", "机构", "北宋元丰新制", "改隶太府寺", main,
        "太府寺所属监当库", "建立都茶库元丰后隶属节点。",
    )
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "都茶库后隶太府寺。")
    role_eid, post = exact_state(
        w, i, "监都茶库", "官职", "北宋咸平六年", "监管都茶库，设二人", main,
        "都茶库监官", "建立监都茶库编制。", officer="监官",
    )
    staff(w, i, merged, post, main, "都茶库设监官二人。", quota=2, staff_type="监官")
    alias_note(w, i, merged, field(i, "简称"), "简称")
    touched.update((source_eid, eid, role_eid))
    finish(w, touched, "整理茶库合并改名都茶库、隶属与监官时间链。")


def entry654():
    i, main = 654, F[654]["text"]
    w, touched = W(i), set()
    sources = []
    for title in ("在京瓷器库", "药蜜库"):
        source_eid, source = exact_state(
            w, i, title, "机构", "北宋熙宁三年三月十四日",
            "并入杂物库", main, "中央监当库", f"建立{title}并入杂物库节点。",
        )
        sources.append(source)
        touched.add(source_eid)
    eid, merged = exact_state(
        w, i, "杂物库", "机构", "北宋熙宁三年三月十四日",
        "并入在京瓷器库、药蜜库，掌收受纸、瓷器等杂物以供支用", main,
        "中央杂物监当库", "建立杂物库接收两库与职掌节点。",
    )
    for source in sources:
        relation(w, i, source, merged, "前后演变", main,
                 "熙宁三年在京瓷器库、药蜜库并入杂物库。")
    _, reform = exact_state(
        w, i, "杂物库", "机构", "北宋元丰新制", "隶太府寺", main,
        "太府寺所属监当库", "建立杂物库元丰后隶属节点。",
    )
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "杂物库元丰后隶太府寺。")
    for title, officer, quota, event in (
        ("监瓷器库官", "兼领官", None, "兼领杂物库"),
        ("药蜜库官", "管勾官", 1, "留一员管勾杂物库"),
    ):
        role_eid, post = exact_state(
            w, i, title, "官职", "北宋熙宁三年三月十四日", event, main,
            "杂物库官属", f"建立{title}兼领或管勾杂物库节点。", officer=officer,
        )
        staff(w, i, merged, post, main, f"杂物库由{title}兼领或管勾。",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    touched.add(eid)
    finish(w, touched, "整理杂物库接收瓷器库、药蜜库、元丰隶属与官属时间链。")


def entry655():
    i = 655
    main, origin, duty = F[i]["text"], field(i, "职源"), field(i, "职掌")
    w, touched = W(i), set()
    eid, early = exact_state(
        w, i, "在京斗秤务", "机构", "宋前期",
        "宋初已置，分隶太府寺与三司，掌监制并校正斗、秤、升、尺", origin,
        "中央度量衡监当局", "建立在京斗秤务宋初节点。", "职源",
    )
    three_eid, three = support_state(
        w, i, "三司", "机构", "宋前期", "与太府寺分领在京斗秤务", main,
        "北宋中央财政机构", "建立三司分领在京斗秤务节点。",
    )
    temple_eid, temple = support_state(
        w, i, "太府寺", "机构", "宋前期", "与三司分领在京斗秤务", main,
        "宋前期寺监", "建立太府寺分领在京斗秤务节点。",
    )
    relation(w, i, three, early, "上下级机构", main, "在京斗秤务早期分隶三司。")
    relation(w, i, temple, early, "上下级机构", main, "在京斗秤务早期分隶太府寺。")
    academy_eid, academy = support_state(
        w, i, "文思院", "机构", "北宋熙宁三年十二月十一日",
        "接收在京斗秤务", main, "中央制造机构", "建立文思院接收斗秤务节点。",
    )
    _, moved = exact_state(
        w, i, "在京斗秤务", "机构", "北宋熙宁三年十二月十一日",
        "拨入文思院，后直隶三司", main, "中央度量衡监当局",
        "建立在京斗秤务熙宁三年转隶节点。",
    )
    relation(w, i, academy, moved, "上下级机构", main, "熙宁三年在京斗秤务拨入文思院。")
    _, reform = exact_state(
        w, i, "在京斗秤务", "机构", "北宋元丰新制", "随文思院隶少府监", main,
        "少府监所属监当局", "建立在京斗秤务元丰隶属节点。",
    )
    relation(w, i, tp(w, "少府监", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "元丰新制在京斗秤务随文思院隶少府监。")
    _, south = exact_state(
        w, i, "在京斗秤务", "机构", "南宋初", "少府监罢后由提辖官领", main,
        "南宋度量衡监当局", "建立在京斗秤务南宋初管理节点。",
    )
    roles = (
        ("监斗秤务官", "三班院使臣", 2, "掌制造与精确校定斗、尺、升、秤"),
        ("都料", "吏", None, "在京斗秤务吏额都料"),
        ("专知官", "吏", None, "在京斗秤务吏额专知官"),
    )
    for title, officer, quota, event in roles:
        role_eid, post = exact_state(
            w, i, title, "官职", "宋前期", event, duty, "斗秤务官吏",
            f"建立在京斗秤务{title}编制。", "职掌", officer=officer,
        )
        staff(w, i, early, post, duty, f"在京斗秤务设{title}。", "职掌",
              quota=quota, staff_type=officer)
        touched.add(role_eid)
    leader_eid, leader = exact_state(
        w, i, "提辖在京斗秤务", "官职", "南宋初", "少府监罢后领在京斗秤务", main,
        "南宋斗秤务差遣", "建立提辖在京斗秤务节点。", officer="提辖官",
    )
    staff(w, i, south, leader, main, "南宋初在京斗秤务由提辖官领。", staff_type="提辖官")
    touched.update((eid, three_eid, temple_eid, academy_eid, leader_eid))
    finish(w, touched, "整理在京斗秤务创置、三次隶属变化、南宋提辖与官吏时间链。")


def entry656():
    i, main = 656, F[656]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "监斗秤务官", "官职", "宋前期",
        "掌制造与精确校定斗、尺、升、秤", main, "斗秤务官吏",
        "复用监斗秤务官节点并补本条证据。", officer="三班院使臣",
    )
    staff(w, i, tp(w, "在京斗秤务", "机构", "宋前期"), post, main,
          "在京斗秤务官由三班院使臣充，编制二人。", quota=2, staff_type="三班院使臣")
    finish(w, {eid}, "补证监斗秤务官充任资格、定额与职掌。")


def entry657():
    i, main, origin, duty, roster = (
        657, F[657]["text"], field(657, "职源"), field(657, "职掌"), field(657, "编制")
    )
    w, touched = W(i), set()
    roads_eid, roads = exact_state(
        w, i, "诸路", "机构", "北宋元丰元年六月十二日",
        "各路转运司治所在州各置斗秤务", origin, "地方行政区统称",
        "建立诸路设置斗秤务的统称承载节点。", "职源",
    )
    eid, bureau = exact_state(
        w, i, "斗秤务", "机构", "北宋元丰元年六月十二日",
        "于诸路转运司治所在州各置，各隶所在路，造作校定度量衡器", origin,
        "路级度量衡监当局", "建立诸路斗秤务设置与隶属节点。", "职源",
    )
    relation(w, i, roads, bureau, "上下级机构", main, "斗秤务各隶所在路。")
    role_eid, post = exact_state(
        w, i, "路兵马都监", "官职", "北宋元丰元年六月十二日",
        "兼管辖各路斗秤务", roster, "路级兼管官",
        "建立路兵马都监兼管斗秤务节点。", "编制", officer="兵马都监",
    )
    staff(w, i, bureau, post, roster, "各路斗秤务由路兵马都监兼管。", "编制",
          staff_type="兼管官")
    cite(w, "Timepoints", bureau, i, duty, "补证诸路斗秤务造作校定并交诸州商税务出售的职掌。", "职掌")
    touched.update((roads_eid, eid, role_eid))
    finish(w, touched, "整理诸路斗秤务设置、隶属、职掌与兼管官时间链。")


def entry658():
    i, main = 658, F[658]["text"]
    w, touched = W(i), set()
    three_eid, three = support_state(
        w, i, "三司", "机构", "北宋（先隶三司）", "早期统辖都商税院", main,
        "北宋中央财政机构", "建立三司早期统辖都商税院节点。",
    )
    eid, early = exact_state(
        w, i, "都商税院", "机构", "北宋（先隶三司）",
        "设于开封义和坊，隶三司，掌征收京师商税、审验地头引、抓偷税及出售度量衡器", main,
        "京师商税监当机构", "建立都商税院早期隶属与职掌节点。",
    )
    relation(w, i, three, early, "上下级机构", main, "都商税院早期隶三司。")
    market_eid, market = support_state(
        w, i, "都提举市易司", "机构", "北宋（隶都提举市易司）",
        "一度统辖都商税院", main, "市易主管机构", "建立都提举市易司统辖都商税院节点。",
    )
    _, middle = exact_state(
        w, i, "都商税院", "机构", "北宋（隶都提举市易司）", "改隶都提举市易司", main,
        "京师商税监当机构", "建立都商税院隶都提举市易司节点。",
    )
    relation(w, i, market, middle, "上下级机构", main, "都商税院一度隶都提举市易司。")
    _, reform = exact_state(
        w, i, "都商税院", "机构", "北宋元丰新制", "改隶太府寺", main,
        "太府寺所属监当机构", "建立都商税院元丰后隶属节点。",
    )
    relation(w, i, tp(w, "太府寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "都商税院后隶太府寺。")
    _, south = exact_state(
        w, i, "都商税院", "机构", "南宋", "置于临安羊坝头市东，继续征收京师商税", main,
        "临安商税监当机构", "建立都商税院南宋沿置节点。",
    )
    for title, officer, quota, event in (
        ("监都商税院", "监官", 3, "监管都商税院，由京朝官、诸司使副、三班使臣充"),
        ("拦头", "公吏", None, "拘收税钱并审验商旅地头引"),
        ("数钱", "公吏", None, "都商税院专掌税钱数目"),
    ):
        role_eid, post = exact_state(
            w, i, title, "官职", "北宋（先隶三司）", event, main,
            "都商税院官吏", f"建立都商税院{title}编制或职掌。", officer=officer,
        )
        staff(w, i, early, post, main, f"都商税院设{title}。", quota=quota, staff_type=officer)
        touched.add(role_eid)
    touched.update((three_eid, eid, market_eid))
    finish(w, touched, "整理都商税院三段隶属、南宋沿置、职掌与官吏时间链。")


def entry659():
    i, main = 659, F[659]["text"]
    w = W(i)
    eid, post = support_state(
        w, i, "拦头", "官职", "北宋（先隶三司）",
        "拘收税钱并审验商旅所执地头引以放行", main, "都商税院公吏",
        "复用拦头节点并补本条职掌证据。", officer="公吏",
    )
    staff(w, i, tp(w, "都商税院", "机构", "北宋（先隶三司）"), post, main,
          "拦头为都商税院拘收税钱、审验地头引的公吏。", staff_type="公吏")
    finish(w, {eid}, "补证拦头身份、职掌与都商税院隶属。")


def entry660():
    i, main = 660, F[660]["text"]
    w, touched = W(i), set()
    local_eid, local = exact_state(
        w, i, "商税务", "机构", "宋代（商税务）",
        "诸路州军县镇设置的商税征收机构", main, "地方商税机构",
        "建立诸路州军县镇商税务统称节点。",
    )
    eid, post = exact_state(
        w, i, "专栏", "官职", "宋代（商税务）",
        "收掌指税印章，专事征收商税", main, "商税机构公吏",
        "建立专栏身份与职掌节点。", officer="公吏",
    )
    staff(w, i, local, post, main, "诸路州军县镇商税务均设专栏。", staff_type="公吏")
    court = tp(w, "都商税院", "机构", "北宋（先隶三司）")
    staff(w, i, court, post, main, "在京都商税院设专栏。", staff_type="公吏")
    touched.update((local_eid, eid))
    finish(w, touched, "整理专栏在京与诸路商税机构的职掌与隶属时间链。")


def main():
    for i in range(641, 661):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
