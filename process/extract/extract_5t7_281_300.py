#!/usr/bin/env python3
"""提取 chapter5t7 第281-300条：御厨杂役、光禄寺诸库与翰林司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_261_280 as previous


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


F = {i: load(i) for i in range(281, 301)}
base = previous.previous.previous
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
    "五代": 907, "唐代": 618,
    "宋代": 960, "宋代（御厨）": 960.01, "宋代（翰林司）": 960.02,
    "宋初": 960.1, "宋前期": 970, "北宋初": 960.2,
    "北宋太平兴国三年": 978, "北宋太平兴国三年以前": 977.9,
    "北宋景德二年": 1005, "北宋大中祥符二年": 1009,
    "北宋大中祥符七年": 1014,
    "北宋大中祥符七年以后（年月未载）": 1014.1,
    "北宋大中祥符九年": 1016,
    "北宋东京元额（御厨）": 1050,
    "北宋熙宁五年正月九日": 1072.02,
    "北宋元丰五年": 1082, "北宋（翰林司）": 1080,
    "北宋崇宁二年五月十四日": 1103.37,
    "北宋崇宁五年": 1106,
    "南宋": 1127, "南宋建炎三年四月十三日": 1129.29,
    "南宋乾道六年": 1170, "南宋乾道六年七月": 1170.55,
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


def entry281():
    i, main = 281, F[281]["text"]
    w = W(i)
    touched = set()
    generic_eid, generic = exact_state(
        w, i, "食手", "官职", "宋代（御厨）",
        "御厨厨子、供食院子等公吏的总称；与兵校合计一千六十九人",
        main, "御厨公吏统称", "建立御厨语境的食手统称。", officer="公吏统称",
    )
    touched.add(generic_eid)
    for title, event in (
        ("厨子", "在御厨执役做菜、做饭"),
        ("供食院子", "在御厨祗应供食等杂事"),
    ):
        eid, post = state(
            w, i, title, "官职", "北宋东京元额（御厨）", event,
            main, "御厨杂职", f"据食手条建立或复用{title}实例。", officer="公吏",
        )
        relation(w, i, generic, post, "统称与实例", main, f"{title}为御厨食手实例。")
        touched.add(eid)
    staff(w, i, tp(w, "御厨", "机构", "宋代"), generic, main,
          "食手为御厨公吏总称。", staff_type="公吏统称")
    for eid in touched:
        rechain(w, eid, "整理食手及其厨子、供食院子实例时间链。")
    w.commit()


def entry282():
    i, main = 282, F[282]["text"]
    w = W(i)
    eid, north = exact_state(
        w, i, "厨子", "官职", "北宋东京元额（御厨）",
        "在御厨执役做菜、做饭，正式编员之外缺额时可和雇百姓",
        main, "御厨杂职", "补足御厨厨子的职掌与和雇制度。", officer="杂职",
    )
    _, south = exact_state(
        w, i, "厨子", "官职", "南宋乾道六年",
        "排办御筵缺人时由临安府和雇百姓厨子一百人",
        main, "御厨杂职", "记录乾道六年临时和雇厨子。", officer="临时和雇",
    )
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), north, main,
          "御厨正式编制中置厨子。", staff_type="杂职")
    staff(w, i, tp(w, "御厨", "机构", "南宋乾道六年七月"), south, main,
          "乾道六年御厨临时和雇厨子一百人。", quota=100, staff_type="临时和雇")
    rechain(w, eid, "连接御厨厨子正式编员与乾道六年和雇节点。")
    w.commit()


def entry283():
    i, main, aliases = 283, F[283]["text"], field(283, "简称与别名")
    w = W(i)
    eid, post = exact_state(
        w, i, "供食院子", "官职", "北宋东京元额（御厨）",
        "在御厨祗应供食等杂事，或差往诸宫院，编额二百五十九人",
        main, "御厨公吏", "补足供食院子的职掌、去向与定额。", officer="公吏",
    )
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), post, main,
          "北宋御厨置供食院子二百五十九人。", quota=259, staff_type="公吏")
    alias_note(w, i, post, aliases, "简称与别名")
    rechain(w, eid, "整理供食院子时间链。")
    w.commit()


def entry284():
    i, main = 284, F[284]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "门子", "官职", "北宋东京元额（御厨）",
        "看守御厨前门诸色人及物料出入", main,
        "御厨杂职", "补足御厨门子职掌。", officer="杂职",
    )
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), post, main,
          "门子隶御厨。", staff_type="杂职")
    rechain(w, eid, "整理御厨门子时间链。")
    w.commit()


def entry285():
    i, main = 285, F[285]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "供御厨库子", "官职", "宋代（御厨）",
        "在御厨执役，按格给纳物料", main,
        "御厨公吏", "按专名建立供御厨库子。", officer="公吏",
    )
    staff(w, i, tp(w, "御厨", "机构", "宋代"), post, main,
          "供御厨库子隶御厨。", staff_type="公吏")
    rechain(w, eid, "整理供御厨库子时间链。")
    w.commit()


def entry286():
    i, main = 286, F[286]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "库院子", "官职", "北宋东京元额（御厨）",
        "在御厨下诸库执役搬运、给纳物料", main,
        "御厨杂职", "补足库院子职掌。", officer="杂职",
    )
    staff(w, i, tp(w, "御厨", "机构", "北宋东京元额（御厨）"), post, main,
          "库院子隶御厨诸库。", staff_type="杂职")
    rechain(w, eid, "整理御厨库院子时间链。")
    w.commit()


def entry287():
    i, main = 287, F[287]["text"]
    w = W(i)
    parent_eid, palace = exact_state(
        w, i, "皇城司", "机构", "宋代",
        "入内院子原隶机构", main, "宫禁机构",
        "为入内院子建立原隶皇城司同期节点。",
    )
    eid, post = exact_state(
        w, i, "入内院子", "官职", "宋代",
        "以年高亲事官或辇官充，差往御厨供看守、巡守等给使",
        main, "皇城司差役", "建立入内院子的来源与差往职掌。", officer="差役",
    )
    staff(w, i, palace, post, main, "入内院子原隶皇城司。", staff_type="亲事官或辇官")
    staff(w, i, tp(w, "御厨", "机构", "宋代"), post, main,
          "入内院子由皇城司差往御厨给使。", staff_type="差往给使")
    for x in (parent_eid, eid):
        rechain(w, x, "整理皇城司与入内院子时间链。")
    w.commit()


def entry288():
    i, main = 288, F[288]["text"]
    w = W(i)
    kitchen_eid, parent = exact_state(
        w, i, "御厨", "机构", "北宋大中祥符九年",
        "御厨内创置御膳素厨", main, "宫廷膳食机构",
        "建立御膳素厨创置时的御厨同期节点。",
    )
    eid, office = exact_state(
        w, i, "御膳素厨", "机构", "北宋大中祥符九年",
        "创置于御厨内，专供皇帝行幸烧香及吃素月分的御用素食",
        main, "御厨所属机构", "建立御膳素厨创置与职掌。",
    )
    relation(w, i, parent, office, "上下级机构", main, "御膳素厨设于御厨内。")
    monitor_eid, monitor = exact_state(
        w, i, "监御厨官", "官职", "北宋大中祥符九年",
        "兼领御膳素厨", main, "御厨官", "建立监御厨官兼领素厨节点。", officer="兼领",
    )
    staff(w, i, office, monitor, main, "御膳素厨由监御厨官兼领。", staff_type="兼领")
    for x in (kitchen_eid, eid, monitor_eid):
        rechain(w, x, "整理御膳素厨及兼领官时间链。")
    w.commit()


def entry289():
    i, main, aliases = 289, F[289]["text"], field(289, "别名")
    w = W(i)
    touched = set()
    eid, office = exact_state(
        w, i, "法酒库", "机构", "宋前期",
        "设于内酒坊，掌造供御、祠祭及给赐臣僚法酒",
        main, "光禄寺所属机构", "补足法酒库设置、职掌与产品用途。",
    )
    touched.add(eid)
    relation(w, i, tp(w, "光禄寺", "机构", "宋前期"), office,
             "上下级机构", main, "法酒库隶光禄寺。")
    cite(w, "Timepoints", office, i, main,
         "供御酒、祠祭酒、常供酒为法酒种类，不属于机构或官职，不另建实体。",
         note="产品名不入四表实体")
    alias_note(w, i, office, aliases, "别名")
    for title, quota, officer, event in (
        ("监法酒库官", 3, "监当官", "由京朝官、内侍或诸司使副分充"),
        ("法酒库监门", 2, "杂职", "看守法酒库门户"),
        ("法酒库酒匠", 14, "工匠", "酿造法酒"),
        ("法酒库兵校", 110, "兵校", "法酒库兵校编制"),
    ):
        peid, post = exact_state(
            w, i, title, "官职", "宋前期", event,
            main, "法酒库官役", f"按法酒库语境建立{title}。", officer=officer,
        )
        staff(w, i, office, post, main, f"法酒库置{title}{quota}人。", quota=quota, staff_type=officer)
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理法酒库及其官役时间链。")
    w.commit()


def entry290():
    i, main = 290, F[290]["text"]
    w = W(i)
    touched = set()
    eid, office = exact_state(
        w, i, "内酒坊", "机构", "宋初",
        "唐酒坊入宋后加‘内’字，设于东京内城外西北隅，掌造法糯酒、糯酒、常料酒",
        main, "光禄寺所属机构", "建立内酒坊宋初名称与职掌。",
    )
    touched.add(eid)
    relation(w, i, tp(w, "光禄寺", "机构", "宋前期"), office,
             "上下级机构", main, "内酒坊隶光禄寺。")
    cite(w, "Timepoints", office, i, main, "记录内酒坊三类酒及其供给对象。")
    for title, quota, officer in (
        ("监内酒坊官", 3, "监当官"), ("内酒坊监门官", 2, "杂职"),
        ("内酒坊酒匠", 19, "工匠"), ("内酒坊兵校", 139, "兵校"),
        ("内酒坊掌库", 14, "公吏"),
    ):
        peid, post = exact_state(
            w, i, title, "官职", "宋初", "内酒坊官役编制之一",
            main, "内酒坊官役", f"按内酒坊语境建立{title}。", officer=officer,
        )
        staff(w, i, office, post, main, f"内酒坊置{title}{quota}人。", quota=quota, staff_type=officer)
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理内酒坊及其官役时间链。")
    w.commit()


def entry291():
    i, main = 291, F[291]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别名"),
    )
    w = W(i)
    touched = set()
    supply_eid, supply = exact_state(
        w, i, "供备库", "机构", "宋初", "珍馐署下设置，隶御厨",
        history, "御厨所属机构", "建立内物料库前身供备库。", "职源与沿革",
    )
    inner_eid, renamed = exact_state(
        w, i, "内物料库", "机构", "北宋太平兴国三年",
        "供备库改名，掌太官膳羞物料出入", history,
        "御厨所属机构", "建立太平兴国三年内物料库改名节点。", "职源与沿革",
    )
    _, merged = exact_state(
        w, i, "内物料库", "机构", "北宋熙宁五年正月九日",
        "并入御厨，罢内物料库之名", history,
        "御厨所属机构", "建立熙宁五年并入御厨节点。", "职源与沿革",
    )
    material_eid, reform = exact_state(
        w, i, "太官物料库", "机构", "北宋元丰五年",
        "元丰改制后为光禄寺所隶诸局之一，即内物料库",
        history, "光禄寺所属机构", "补足太官物料库与内物料库承接关系。", "职源与沿革",
    )
    _, chongning = exact_state(
        w, i, "太官物料库", "机构", "北宋崇宁五年",
        "仍称内物料官，归隶殿中省尚食局太官局",
        aliases, "太官局所属机构", "建立崇宁五年改隶太官局节点。", "别名",
    )
    kitchen_eid, kitchen = exact_state(
        w, i, "御厨", "机构", "宋初", "供备库所隶机构",
        history, "宫廷膳食机构", "为供备库建立宋初御厨同期节点。", "职源与沿革",
    )
    _, kitchen_merged = exact_state(
        w, i, "御厨", "机构", "北宋熙宁五年正月九日",
        "接收并省的内物料库", history, "宫廷膳食机构",
        "建立熙宁五年接收内物料库的御厨节点。", "职源与沿革",
    )
    relation(w, i, kitchen, supply, "上下级机构", history, "宋初供备库隶御厨。", "职源与沿革")
    relation(w, i, supply, renamed, "前后演变", history, "太平兴国三年供备库改名内物料库。", "职源与沿革")
    relation(w, i, merged, kitchen_merged, "前后演变", history, "熙宁五年内物料库并入御厨。", "职源与沿革")
    relation(w, i, merged, reform, "前后演变", history, "元丰改制后以太官物料库承接内物料库职事。", "职源与沿革")
    relation(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), reform, "上下级机构", history, "元丰后太官物料库隶光禄寺。", "职源与沿革")
    taiguan_eid, taiguan = exact_state(
        w, i, "太官局", "机构", "北宋崇宁五年",
        "兼领内物料库", aliases, "尚食局所属机构",
        "为内物料库崇宁五年改隶建立太官局同期节点。", "别名",
    )
    relation(w, i, taiguan, chongning, "上下级机构", aliases, "崇宁五年内物料库归太官局。", "别名")
    cite(w, "Timepoints", renamed, i, duty, "记录内物料库职掌。", "职掌")
    alias_note(w, i, chongning, aliases, "别名")
    touched.update((supply_eid, inner_eid, material_eid, taiguan_eid, kitchen_eid))
    for title, quota, officer, event in (
        ("监内物料库官", 2, "监当官", "以内侍及三班使臣充任"),
        ("内物料库监门官", 1, "杂职", "以三班使臣充任"),
        ("内物料库主秤", 3, "公吏", "内物料库主秤公吏"),
        ("内物料库掌库", 6, "公吏", "内物料库掌库公吏"),
    ):
        peid, post = exact_state(
            w, i, title, "官职", "北宋太平兴国三年",
            event, roster,
            "内物料库官吏", f"按内物料库语境建立{title}。", "编制", officer=officer,
        )
        staff(w, i, renamed, post, roster, f"内物料库置{title}{quota}人。", "编制", quota=quota, staff_type=officer)
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理内物料库沿革、改隶及官吏时间链。")
    w.commit()


def entry292():
    i, main = 292, F[292]["text"]
    history, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    touched = set()
    bran_eid, bran = exact_state(
        w, i, "麸面库", "机构", "宋初", "外物料库前身",
        history, "宫廷物料机构", "建立外物料库前身麸面库。", "职源与沿革",
    )
    material_eid, material = exact_state(
        w, i, "物料库", "机构", "北宋大中祥符七年",
        "麸面库改称物料库", history, "宫廷物料机构",
        "建立大中祥符七年物料库节点。", "职源与沿革",
    )
    outer_eid, outer = exact_state(
        w, i, "外物料库", "机构", "北宋大中祥符七年以后（年月未载）",
        "物料库后又改称外物料库，收储颁给诸王宫院及宗室所需物料",
        history, "光禄寺所属机构", "建立外物料库改称节点。", "职源与沿革",
    )
    _, reform = exact_state(
        w, i, "外物料库", "机构", "北宋元丰五年",
        "元丰后供应范围扩大到百司", duty,
        "光禄寺所属机构", "补足元丰后外物料库职掌扩大。", "职掌",
    )
    relation(w, i, bran, material, "前后演变", history, "大中祥符七年麸面库改称物料库。", "职源与沿革")
    relation(w, i, material, outer, "前后演变", history, "物料库后改称外物料库。", "职源与沿革")
    relation(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), reform,
             "上下级机构", main, "外物料库隶光禄寺。")
    cite(w, "Timepoints", outer, i, duty, "记录外物料库原有职掌。", "职掌")
    touched.update((bran_eid, material_eid, outer_eid))
    for title, quota, officer in (
        ("监外物料库官", 2, "监当官"), ("外物料库掌库", 11, "公吏"),
        ("外物料库兵士", 10, "兵士"),
    ):
        peid, post = exact_state(
            w, i, title, "官职", "北宋元丰五年", "外物料库官役编制之一",
            roster, "外物料库官役", f"按外物料库语境建立{title}。", "编制", officer=officer,
        )
        staff(w, i, reform, post, roster, f"外物料库置{title}{quota}人。", "编制", quota=quota, staff_type=officer)
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理外物料库名称沿革及官役时间链。")
    w.commit()


def entry293():
    i, main = 293, F[293]["text"]
    history, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    touched = set()
    parent_eid, parent = exact_state(
        w, i, "左骐骥院", "机构", "宋初", "南、北乳酪院原隶机构",
        main, "马政机构", "建立乳酪院原隶左骐骥院同期节点。",
    )
    generic_eid, generic = exact_state(
        w, i, "南、北乳酪院", "机构", "宋初", "南乳酪院、北乳酪院合称",
        history, "机构统称", "建立宋初南、北乳酪院统称。", "职源与沿革",
    )
    nodes = []
    for title in ("南乳酪院", "北乳酪院"):
        eid, office = exact_state(
            w, i, title, "机构", "宋初", "乳酪院分设机构之一",
            history, "左骐骥院所属机构", f"建立宋初{title}。", "职源与沿革",
        )
        relation(w, i, generic, office, "统称与实例", history, f"{title}为南、北乳酪院实例。", "职源与沿革")
        relation(w, i, parent, office, "上下级机构", main, f"{title}隶左骐骥院。")
        nodes.append(office)
        touched.add(eid)
    milk_eid, combined = exact_state(
        w, i, "乳酪院", "机构", "北宋景德二年",
        "南乳酪院、北乳酪院合并为一院，制造酥酪乳饼供御厨",
        history, "宫廷乳品机构", "建立景德二年乳酪院合并节点。", "职源与沿革",
    )
    for node in nodes:
        relation(w, i, node, combined, "前后演变", history, "景德二年南、北乳酪院合并为乳酪院。", "职源与沿革")
    _, reform = exact_state(
        w, i, "乳酪院", "机构", "北宋元丰五年",
        "改隶光禄寺，制造乳品供御厨", duty,
        "光禄寺所属机构", "补足元丰后乳酪院改隶与职掌。", "职掌",
    )
    relation(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), reform,
             "上下级机构", main, "乳酪院后隶光禄寺。")
    _, merged = exact_state(
        w, i, "乳酪院", "机构", "南宋建炎三年四月十三日",
        "并入牛羊司", history, "宫廷乳品机构",
        "建立建炎三年乳酪院并入牛羊司节点。", "职源与沿革",
    )
    cattle_eid, cattle = exact_state(
        w, i, "牛羊司", "机构", "南宋建炎三年四月十三日",
        "接收乳酪院职事", history, "宫廷牲畜机构",
        "为乳酪院并入建立牛羊司同期节点。", "职源与沿革",
    )
    relation(w, i, merged, cattle, "前后演变", history, "建炎三年乳酪院并入牛羊司。", "职源与沿革")
    cite(w, "Timepoints", combined, i, duty, "记录乳酪院加工乳品供御厨。", "职掌")
    touched.update((parent_eid, generic_eid, milk_eid, cattle_eid))
    for title, quota, officer, event in (
        ("乳酪院监官", None, "兼充", "由骐骥院监官及专知、副知兼充"),
        ("乳酪院乳匠", 7, "工匠", "加工牛羊奶、制造酥酪乳饼"),
        ("乳酪院节级", None, "杂职", "乳酪院杂职之一"),
        ("乳酪院工匠", None, "工匠", "乳酪院工匠"),
        ("乳酪院养喂长行", None, "杂职", "乳酪院养喂杂职"),
    ):
        peid, post = exact_state(
            w, i, title, "官职", "北宋景德二年", event,
            roster, "乳酪院官役", f"按乳酪院语境建立{title}。", "编制", officer=officer,
        )
        staff(w, i, combined, post, roster, f"乳酪院置{title}。", "编制", quota=quota, staff_type=officer)
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理乳酪院分设、合并、改隶及官役时间链。")
    w.commit()


def entry294():
    i, main = 294, F[294]["text"]
    w = W(i)
    touched = set()
    predecessors = []
    for title in ("油库", "醋库"):
        eid, office = exact_state(
            w, i, title, "机构", "宋初", "油醋库合并前分设机构之一",
            main, "宫廷膳食物料机构", f"建立宋初分设的{title}。",
        )
        predecessors.append(office)
        touched.add(eid)
    oil_eid, combined = exact_state(
        w, i, "油醋库", "机构", "北宋大中祥符二年",
        "油库、醋库合并为一库，掌造三等油及醋",
        main, "宫廷膳食物料机构", "建立大中祥符二年油醋库合并节点。",
    )
    for node in predecessors:
        relation(w, i, node, combined, "前后演变", main, "大中祥符二年油库、醋库合并为油醋库。")
    _, reform = exact_state(
        w, i, "油醋库", "机构", "北宋元丰五年",
        "元丰改制后加制咸肉，供邦国膳羞内外之用",
        main, "光禄寺所属机构", "补足元丰后油醋库职掌。",
    )
    touched.add(oil_eid)
    for title, quota, officer in (
        ("监油醋库官", 2, "监当官"), ("油醋库油匠", 60, "工匠"),
        ("油醋库醋匠", 4, "工匠"), ("油醋库副知", None, "公吏"),
        ("油醋库杂役", None, "杂役"), ("油醋库斗子", None, "杂役"),
    ):
        peid, post = exact_state(
            w, i, title, "官职", "北宋元丰五年", "油醋库官役编制之一",
            main, "油醋库官役", f"按油醋库语境建立{title}。", officer=officer,
        )
        staff(w, i, reform, post, main, f"油醋库置{title}。", quota=quota, staff_type=officer)
        touched.add(peid)
    cite(w, "Timepoints", reform, i, main, "副知、杂役、斗子合计八人，无法分配到单一名目，关系不分别填八人。")
    for x in touched:
        rechain(w, x, "整理油醋库合并、职掌及官役时间链。")
    w.commit()


def entry295():
    i, main = 295, F[295]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "别名"),
    )
    w = W(i)
    touched = set()
    specs = (
        ("北宋太平兴国三年以前", "至迟已设翰林司", history, "内诸司"),
        ("北宋元丰五年", "隶光禄寺，供奉御酒茶汤及内外筵设等事", duty, "光禄寺所属机构"),
        ("北宋崇宁二年五月十四日", "并入殿中省太官局但保留官司", history, "太官局所属机构"),
        ("南宋", "与翰林院、学士院并置不废", history, "内诸司"),
    )
    nodes = {}
    for time, event, quote, category in specs:
        eid, nodes[time] = exact_state(
            w, i, "翰林司", "机构", time, event, quote, category,
            f"建立或补足翰林司{time}节点。",
            "职掌" if quote == duty else "职源与沿革",
        )
        touched.add(eid)
    cite(w, "Timepoints", nodes["北宋太平兴国三年以前"], i, history,
         "五代茶酒库使、翰林茶酒使及北宋初茶床使、翰林使仅作职源说明，不据此另建机构。",
         "职源与沿革", note="近似职源不另建实体")
    relation(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"],
             "上下级机构", history, "元丰改制后翰林司隶光禄寺。", "职源与沿革")
    relation(w, i, tp(w, "太官局", "机构", "北宋崇宁二年五月十四日"), nodes["北宋崇宁二年五月十四日"],
             "上下级机构", history, "崇宁二年翰林司并入太官局但存官司。", "职源与沿革")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, duty, "记录翰林司职掌。", "职掌")
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "别名")
    for title, quota, officer, time, event in (
        ("勾当翰林司公事", 4, "差遣", "宋代（翰林司）", "掌领翰林司事"),
        ("翰林司兵校", 300, "兵校", "北宋（翰林司）", "翰林司兵校编制"),
        ("药童", 11, "公吏", "北宋（翰林司）", "翰林司供御祗应杂职"),
        ("专知官", None, "公吏", "宋代（翰林司）", "主管翰林司官物"),
        ("副知", None, "公吏", "宋代（翰林司）", "主管翰林司官物"),
        ("翰林司监官", None, "监官", "南宋", "南宋翰林司所设监官"),
    ):
        peid, post = state(
            w, i, title, "官职", time, event,
            roster, "翰林司官吏", f"据翰林司编制建立{title}语境节点。", "编制", officer=officer,
        )
        staff(w, i, nodes["北宋元丰五年"], post, roster, f"翰林司置{title}。", "编制", quota=quota, staff_type=officer)
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理翰林司沿革、改隶及官吏时间链。")
    w.commit()


def entry296():
    i, main, aliases = 296, F[296]["text"], field(296, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "勾当翰林司公事", "官职", "宋代（翰林司）",
        "以诸司使、副使及内侍官充，掌领翰林司事，编制四员",
        main, "翰林司长官", "补足勾当翰林司公事任用、职掌与定额。", officer="差遣",
    )
    staff(w, i, tp(w, "翰林司", "机构", "北宋元丰五年"), post, aliases,
          "翰林司置勾当官四员。", "简称", quota=4, staff_type="差遣")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理勾当翰林司公事时间链。")
    w.commit()


def entry297():
    i, main = 297, F[297]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "药童", "官职", "北宋（翰林司）",
        "隶翰林司，在殿内供御祗应，如端送盛开水的金盆",
        main, "翰林司杂职", "为既有药童建立翰林司语境节点。", officer="杂职",
    )
    staff(w, i, tp(w, "翰林司", "机构", "北宋元丰五年"), post, main,
          "翰林司置药童十一人。", quota=11, staff_type="杂职")
    rechain(w, eid, "将翰林司药童纳入完整时间链。")
    w.commit()


def entry298():
    i, main = 298, F[298]["text"]
    w = W(i)
    old = tp(w, "药童", "官职", "北宋（翰林司）")
    eid, post = exact_state(
        w, i, "供御人", "官职", "南宋",
        "翰林司供御祗应人，南宋名称", main,
        "翰林司杂职", "按南宋正式名称建立供御人。", officer="杂职",
    )
    relation(w, i, old, post, "前后演变", main, "翰林司供御祗应人北宋称药童、南宋称供御人。")
    staff(w, i, tp(w, "翰林司", "机构", "南宋"), post, main,
          "南宋翰林司置供御人。", staff_type="杂职")
    rechain(w, eid, "整理供御人南宋时间链。")
    w.commit()


def entry299():
    i, main = 299, F[299]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "专知官", "官职", "宋代（翰林司）",
        "隶翰林司，主管翰林司官物", main,
        "翰林司公吏", "为既有专知官建立翰林司语境节点。", officer="公吏",
    )
    staff(w, i, tp(w, "翰林司", "机构", "北宋元丰五年"), post, main,
          "翰林司置专知官。", staff_type="公吏")
    rechain(w, eid, "将翰林司专知官纳入完整时间链。")
    w.commit()


def entry300():
    i, main = 300, F[300]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "副知", "官职", "宋代（翰林司）",
        "隶翰林司，主管官物，可迁为专知", main,
        "翰林司公吏", "为既有副知建立翰林司语境节点并记录迁补规则。", officer="公吏",
    )
    staff(w, i, tp(w, "翰林司", "机构", "北宋元丰五年"), post, main,
          "翰林司置副知。", staff_type="公吏")
    rechain(w, eid, "将翰林司副知纳入完整时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(281, 301)] == [
        "食手", "厨子", "供食院子", "门子", "供御厨库子", "库院子",
        "入内院子", "御膳素厨", "法酒库", "内酒坊", "内物料库",
        "外物料库", "乳酪院", "油醋库", "翰林司", "勾当翰林司公事",
        "药童", "供御人", "专知官", "副知",
    ]
    entry281()
    entry282()
    entry283()
    entry284()
    entry285()
    entry286()
    entry287()
    entry288()
    entry289()
    entry290()
    entry291()
    entry292()
    entry293()
    entry294()
    entry295()
    entry296()
    entry297()
    entry298()
    entry299()
    entry300()


if __name__ == "__main__":
    main()
