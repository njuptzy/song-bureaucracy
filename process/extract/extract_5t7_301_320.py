#!/usr/bin/env python3
"""提取 chapter5t7 第301-320条：翰林司营、牛羊司与卫尉寺。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_281_300 as previous


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


F = {i: load(i) for i in range(301, 321)}
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
    "西汉": -206, "东汉": 25, "北齐": 550,
    "宋代": 960, "宋代（牛羊司）": 960.01,
    "宋初": 960.1, "宋前期": 970, "北宋": 960.2, "北宋初": 960.3,
    "北宋太祖开宝二年六月": 969.45,
    "北宋大中祥符三年": 1010, "北宋大中祥符四年": 1011,
    "北宋嘉祐五年": 1060, "北宋熙宁八年七月": 1075.55,
    "北宋元丰五年": 1082, "北宋元丰新制": 1080,
    "南宋": 1127, "南宋建炎三年四月十三日": 1129.29,
    "南宋淳熙十三年": 1186,
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


def entry301():
    i, main = 301, F[301]["text"]
    w = W(i)
    touched = set()
    camp_eid, north = exact_state(
        w, i, "翰林司营", "机构", "北宋",
        "与翰林司并置，营兵校三百人，承担守门、搬运、百司执役及使者粗重劳役",
        main, "翰林司所属兵营", "建立北宋翰林司营及兵校职役。",
    )
    _, south = exact_state(
        w, i, "翰林司营", "机构", "南宋",
        "与翰林司并置，设在京畿第二将南", main,
        "翰林司所属兵营", "建立南宋翰林司营位置节点。",
    )
    _, reduced = exact_state(
        w, i, "翰林司营", "机构", "南宋淳熙十三年",
        "兵校裁减三十人", main, "翰林司所属兵营",
        "记录淳熙十三年裁减兵校三十人。",
    )
    relation(w, i, tp(w, "翰林司", "机构", "北宋元丰五年"), north,
             "上下级机构", main, "翰林司营为翰林司所属兵营。")
    relation(w, i, tp(w, "翰林司", "机构", "南宋"), south,
             "上下级机构", main, "南宋翰林司营与翰林司并置。")
    soldier_eid, soldier = exact_state(
        w, i, "翰林司兵校", "官职", "北宋（翰林司）",
        "承差守门、搬运物料、在京百司执役及出国使者粗重劳役，编制三百人",
        main, "翰林司兵役", "补足翰林司兵校职役与北宋编制。", officer="兵校",
    )
    _, soldier_reduced = exact_state(
        w, i, "翰林司兵校", "官职", "南宋淳熙十三年",
        "裁减三十人", main, "翰林司兵役",
        "记录淳熙十三年兵校裁减人数，不推算裁后总额。", officer="兵校",
    )
    staff(w, i, north, soldier, main, "北宋翰林司营置兵校三百人。", quota=300, staff_type="兵校")
    staff(w, i, reduced, soldier_reduced, main, "淳熙十三年翰林司营兵校裁减三十人。", staff_type="兵校")
    touched.update((camp_eid, soldier_eid))
    for eid in touched:
        rechain(w, eid, "整理翰林司营与兵校完整时间链。")
    w.commit()


def entry302():
    i, main = 302, F[302]["text"]
    history, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    touched = set()
    specs = (
        ("北宋太祖开宝二年六月", "已见创置", history, "光禄寺所属机构"),
        ("北宋元丰五年", "隶光禄寺，掌御厨与祭祀所需牲畜饲养管理", duty, "光禄寺所属机构"),
        ("宋代", "辖广牧二指挥、三栈圈及多种官吏杂职", roster, "宫廷牲畜机构"),
        ("南宋", "沿置不废", history, "宫廷牲畜机构"),
    )
    nodes = {}
    for time, event, quote, category in specs:
        eid, nodes[time] = exact_state(
            w, i, "牛羊司", "机构", time, event, quote, category,
            f"建立或补足牛羊司{time}节点。",
            "职掌" if quote == duty else ("编制" if quote == roster else "职源与沿革"),
        )
        touched.add(eid)
    relation(w, i, tp(w, "光禄寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"],
             "上下级机构", main, "牛羊司隶光禄寺。")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, duty, "记录牛羊司职掌。", "职掌")
    command_eid, command = exact_state(
        w, i, "广牧指挥", "机构", "宋代（牛羊司）",
        "牛羊司辖两指挥，兵额合计一千一百二十六人",
        roster, "牛羊司所属军额", "建立牛羊司所辖广牧指挥。", "编制",
    )
    pen_eid, pens = exact_state(
        w, i, "牛羊司栈圈", "机构", "宋代（牛羊司）",
        "牛羊司设三处栈圈，每栈圈置勾当官",
        roster, "牛羊司所属设施", "建立牛羊司三栈圈承载实体。", "编制",
    )
    relation(w, i, nodes["宋代"], command, "上下级机构", roster, "牛羊司辖广牧二指挥。", "编制")
    relation(w, i, nodes["宋代"], pens, "上下级机构", roster, "牛羊司辖三栈圈。", "编制")
    touched.update((command_eid, pen_eid))

    main_roles = (
        ("勾当牛羊司", "差遣"), ("监牛羊司", "差遣"),
        ("牧羊群头", "公吏"), ("牧子", "公吏"),
        ("手分", "公吏"), ("估羊节级", "武职公人"),
        ("曹司", "公吏"), ("宰手", "公吏"), ("副知", "公吏"),
        ("贴司", "公吏"), ("揣子", "公吏"), ("秤子", "公吏"),
        ("门子", "杂职"), ("牛羊司兵士", "兵士"),
    )
    for title, officer in main_roles:
        peid, post = state(
            w, i, title, "官职", "宋代（牛羊司）", "牛羊司官吏杂职之一",
            roster, "牛羊司官吏", f"据牛羊司编制建立{title}语境节点。", "编制", officer=officer,
        )
        staff(w, i, nodes["宋代"], post, roster, f"牛羊司置{title}。", "编制", staff_type=officer)
        touched.add(peid)

    command_roles = (
        ("广牧指挥使", "武职"), ("广牧副指挥使", "武职"),
        ("广牧都头", "武职"), ("广牧副都头", "武职"),
        ("巡羊十将", "武职"), ("巡羊员僚", "武职"), ("承局", "武职公人"),
    )
    for title, officer in command_roles:
        peid, post = state(
            w, i, title, "官职", "宋代（牛羊司）", "广牧指挥员僚或兵级之一",
            roster, "广牧指挥官兵", f"据牛羊司编制建立{title}。", "编制", officer=officer,
        )
        staff(w, i, command, post, roster, f"广牧指挥置{title}。", "编制", staff_type=officer)
        touched.add(peid)
    for x in touched:
        rechain(w, x, "整理牛羊司、广牧指挥、栈圈及官吏时间链。")
    w.commit()


def entry303():
    i, main = 303, F[303]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "勾当牛羊司", "官职", "宋代（牛羊司）",
        "由武臣差充，领牛羊司公事", main,
        "牛羊司长官", "补足勾当牛羊司任用与职掌。", officer="差遣",
    )
    staff(w, i, tp(w, "牛羊司", "机构", "宋代"), post, main,
          "牛羊司置勾当官。", staff_type="武臣差充")
    rechain(w, eid, "整理勾当牛羊司时间链。")
    w.commit()


def entry304():
    i, main, aliases = 304, F[304]["text"], field(304, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "监牛羊司", "官职", "宋代（牛羊司）",
        "由文臣京朝官、武臣诸司使副及三班使臣差充，督领本司公事，编制三人",
        main, "牛羊司长官", "补足监牛羊司任用、职掌与定额。", officer="差遣",
    )
    staff(w, i, tp(w, "牛羊司", "机构", "宋代"), post, main,
          "牛羊司置监官三人。", quota=3, staff_type="差遣")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理监牛羊司时间链。")
    w.commit()


def simple_cattle_role(i, title, event, *, officer="公吏", parent="牛羊司"):
    main = F[i]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, title, "官职", "宋代（牛羊司）", event,
        main, "牛羊司官吏", f"补足{title}的归隶、职掌与位次。", officer=officer,
    )
    parent_tp = tp(w, parent, "机构", "宋代（牛羊司）" if parent == "广牧指挥" else "宋代")
    staff(w, i, parent_tp, post, main, f"{title}隶{parent}。", staff_type=officer)
    rechain(w, eid, f"整理{title}时间链。")
    w.commit()


def entry305():
    i, main, aliases = 305, F[305]["text"], field(305, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "牧羊群头", "官职", "宋代（牛羊司）",
        "主管放牧牛羊，位高于牧子", main,
        "牛羊司公吏", "补足牧羊群头职掌与位次。", officer="公吏",
    )
    staff(w, i, tp(w, "牛羊司", "机构", "宋代"), post, main,
          "牧羊群头隶牛羊司。", staff_type="公吏")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理牧羊群头时间链。")
    w.commit()


def entry306():
    simple_cattle_role(306, "牧子", "放牧牛羊，位次于牧羊群头")


def entry307():
    simple_cattle_role(
        307, "揣子", "估量牛羊重量以决定宰杀与否，并估价出卖死羊"
    )


def entry308():
    simple_cattle_role(
        308, "估羊节级", "专职悬估死羊、活羊每口重量", officer="武职公人"
    )


def entry309():
    simple_cattle_role(
        309, "巡羊十将", "广牧指挥牧羊兵级小头目，位于群头之上、员僚之下",
        officer="武职", parent="广牧指挥",
    )


def entry310():
    simple_cattle_role(
        310, "巡羊员僚", "由都头、副都头差充，部领十将以下兵级牧羊职事",
        officer="武职", parent="广牧指挥",
    )


def entry311():
    i, main, aliases = 311, F[311]["text"], field(311, "别称")
    w = W(i)
    eid, post = exact_state(
        w, i, "巡羊使臣", "官职", "宋代（牛羊司）",
        "三班使臣承差管领外群牧羊公事，位在广牧指挥员僚、十将之上，给军士五人服侍",
        main, "牛羊司武职", "建立巡羊使臣资格、职掌、位次与给使待遇。", officer="武职",
    )
    staff(w, i, tp(w, "牛羊司", "机构", "宋代"), post, main,
          "巡羊使臣承差管领牛羊司外群牧羊公事。", staff_type="三班使臣")
    alias_note(w, i, post, aliases, "别称")
    rechain(w, eid, "整理巡羊使臣时间链。")
    w.commit()


def entry312():
    i, main = 312, F[312]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "曹司", "官职", "宋代（牛羊司）",
        "隶牛羊司；辞典据相关材料推测为记帐公人",
        main, "牛羊司公吏", "记录曹司归隶，并明确保留辞典‘盖为’推测语气。",
        officer="公吏", note="辞典推测为记帐公人",
    )
    staff(w, i, tp(w, "牛羊司", "机构", "宋代"), post, main,
          "曹司隶牛羊司。", staff_type="公吏")
    rechain(w, eid, "整理牛羊司曹司时间链。")
    w.commit()


def entry313():
    simple_cattle_role(
        313, "承局", "广牧指挥节级之一种", officer="武职公人", parent="广牧指挥"
    )


def entry314():
    simple_cattle_role(314, "宰手", "专职屠宰牛羊")


def entry315():
    simple_cattle_role(315, "秤子", "专职过秤")


def entry316():
    i, main, aliases = 316, F[316]["text"], field(316, "别名")
    w = W(i)
    touched = set()
    office_eid, subordinate = exact_state(
        w, i, "宰杀务", "机构", "宋初",
        "隶牛羊司，专掌宰杀供应御厨与祠祭用牲",
        main, "牛羊司所属机构", "建立宋初宰杀务及职掌。",
    )
    _, independent = exact_state(
        w, i, "宰杀务", "机构", "北宋大中祥符四年",
        "从牛羊司析出，独立为司", main,
        "独立监当局", "建立大中祥符四年宰杀务析出节点。",
    )
    _, merged = exact_state(
        w, i, "宰杀务", "机构", "北宋嘉祐五年",
        "并回牛羊司", main, "牛羊司所属机构",
        "建立嘉祐五年宰杀务并回节点。",
    )
    cattle_eid, cattle_start = exact_state(
        w, i, "牛羊司", "机构", "宋初", "下辖宰杀务",
        main, "宫廷牲畜机构", "为宰杀务原隶建立牛羊司宋初节点。",
    )
    _, cattle_merge = exact_state(
        w, i, "牛羊司", "机构", "北宋嘉祐五年", "重新并入宰杀务",
        main, "宫廷牲畜机构", "为宰杀务并回建立牛羊司嘉祐五年节点。",
    )
    relation(w, i, cattle_start, subordinate, "上下级机构", main, "宋初宰杀务隶牛羊司。")
    relation(w, i, merged, cattle_merge, "前后演变", main, "嘉祐五年宰杀务并入牛羊司。")
    alias_note(w, i, independent, aliases, "别名")
    touched.update((office_eid, cattle_eid))
    for x in touched:
        rechain(w, x, "整理宰杀务析出、独立、并回及牛羊司同期时间链。")
    w.commit()


def entry317():
    i, main = 317, F[317]["text"]
    w = W(i)
    eid, office = exact_state(
        w, i, "牛羊供应所", "机构", "北宋元丰五年",
        "《哲宗正史职官志》载名；辞典推测承接旧供庖务职事并再从牛羊司析出",
        main, "光禄寺所属机构", "补足牛羊供应所载名，并保留辞典‘盖即’推测语气。",
        note="承接旧供庖务为辞典推测",
    )
    old = tp(w, "宰杀务", "机构", "北宋嘉祐五年")
    rid = w.relationship(
        old, office, "前后演变",
        "辞典以‘盖即’推测牛羊供应所承接旧供庖务职事；关系保留不确定性说明。",
        main,
    )
    cite(
        w, "Relationships", rid, i, main,
        "辞典以‘盖即’推测牛羊供应所承接旧供庖务职事。",
        note="辞典推测关系，非确定改名",
    )
    rechain(w, eid, "整理牛羊供应所时间链。")
    w.commit()


def entry318():
    i, main = 318, F[318]["text"]
    w = W(i)
    pen_eid, pens = exact_state(
        w, i, "牛羊司栈圈", "机构", "北宋大中祥符三年",
        "三栈圈每年分养三万三千口羊", main,
        "牛羊司所属设施", "建立大中祥符三年三栈圈定制。",
    )
    eid, post = exact_state(
        w, i, "勾当栈圈官", "官职", "北宋大中祥符三年",
        "每栈圈一人，由三班使臣差充，勾当栈羊事务",
        main, "牛羊司栈圈官", "建立勾当栈圈官资格、职掌及每圈定额。", officer="差遣",
    )
    staff(w, i, pens, post, main, "每栈圈置勾当官一人；关系不推算三栈圈总员额。", staff_type="三班使臣")
    for x in (pen_eid, eid):
        rechain(w, x, "整理牛羊司栈圈与勾当官时间链。")
    w.commit()


def entry319():
    i, main = 319, F[319]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    specs = (
        ("西汉", "已有卫尉寺称谓，但‘寺’仅指卫尉官廨，尚未成为官署官衔", history, "前代职源"),
        ("北齐", "正式设置卫尉寺官司", history, "寺监机构"),
        ("北宋沿置", "北宋沿置", history, "寺监机构"),
        ("宋前期", "无所掌，职事分隶仪鸾司、内库、军器库", duty, "寺监机构"),
        ("北宋元丰五年", "正名后掌军用武器装备、仪卫器仗什物、帐幕供设及政令", duty, "寺监机构"),
        ("南宋建炎三年四月十三日", "罢归兵部，后不复置", history, "寺监机构"),
    )
    nodes = {}
    for time, event, quote, category in specs:
        eid, nodes[time] = exact_state(
            w, i, "卫尉寺", "机构", time, event, quote, category,
            f"建立或补足卫尉寺{time}节点。",
            "职掌" if quote == duty else "职源与沿革",
        )
        touched.add(eid)
    cite(w, "Timepoints", nodes["宋前期"], i, duty,
         "仪鸾司、内库、军器库仅作为职事实际分隶对象记录，不据此编造上下级关系。", "职掌")
    relation(w, i, nodes["南宋建炎三年四月十三日"], tp(w, "兵部", "机构", "南宋建炎三年"),
             "前后演变", history, "建炎三年卫尉寺罢归兵部。", "职源与沿革")
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称")

    for title, quota, officer, parent in (
        ("判卫尉寺事", 1, "差遣", nodes["宋前期"]),
        ("卫尉寺府史", 2, "吏", nodes["宋前期"]),
        ("卫尉寺卿", 1, "职事官", nodes["北宋元丰五年"]),
        ("卫尉寺少卿", 1, "职事官", nodes["北宋元丰五年"]),
        ("卫尉寺丞", 1, "职事官", nodes["北宋元丰五年"]),
        ("卫尉寺主簿", 1, "职事官", nodes["北宋元丰五年"]),
        ("卫尉寺吏人", 10, "吏", nodes["北宋元丰五年"]),
    ):
        time = "宋前期" if parent == nodes["宋前期"] else "北宋元丰五年"
        peid, post = state(
            w, i, title, "官职", time, "卫尉寺官吏编制之一",
            roster, "卫尉寺官吏", f"据卫尉寺编制建立或补足{title}。", "编制", officer=officer,
        )
        staff(w, i, parent, post, roster, f"卫尉寺置{title}{quota}人。", "编制", quota=quota, staff_type=officer)
        touched.add(peid)

    five_eid, five = exact_state(
        w, i, "军器五库", "机构", "北宋元丰五年",
        "军器衣甲、弓枪、弩、剑、箭五库合称", roster,
        "机构统称", "建立卫尉寺军器五库统称。", "编制",
    )
    touched.add(five_eid)
    five_titles = ("军器衣甲库", "军器弓枪库", "军器弩库", "军器剑库", "军器箭库")
    bureau_titles = (
        "内弓箭库", "南外库", *five_titles, "仪鸾司", "军器什物库",
        "宣德门什物库", "大礼板木库", "左右金吾街仗司", "六军仪仗司",
    )
    for title in bureau_titles:
        beid, office = exact_state(
            w, i, title, "机构", "北宋元丰五年", "卫尉寺所总十三局之一",
            roster, "卫尉寺所属机构", f"据编制建立卫尉寺所总{title}。", "编制",
        )
        relation(w, i, nodes["北宋元丰五年"], office, "上下级机构", roster,
                 f"{title}为卫尉寺所总十三局之一。", "编制")
        if title in five_titles:
            relation(w, i, five, office, "统称与实例", roster, f"{title}为军器五库实例。", "编制")
        touched.add(beid)
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster,
         "卫尉寺分案四但原文未载案名，不另建四案实体。", "编制", note="案名未载")
    for x in touched:
        rechain(w, x, "整理卫尉寺源流、沿革、官吏及十三局时间链。")
    w.commit()


def entry320():
    i = 320
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    specs = (
        ("东汉", "已有卫尉卿之称", history, "前代职源", None, "职事官"),
        ("北齐", "始有卫尉寺卿之称", history, "前代职源", None, "职事官"),
        ("北宋初", "无职事，为文臣寄禄官", duty, "寄禄官", "从三品", "阶官"),
        ("北宋元丰五年", "正名为卫尉寺长官，领寺事并总军器库藏、仪卫仪物与帐幕供设", duty, "卫尉寺长官", "从四品", "职事官"),
        ("南宋建炎三年四月十三日", "卫尉寺罢后不复置卿", history, "卫尉寺长官", "从四品", "职事官"),
    )
    nodes = {}
    for time, event, quote, category, grade, officer in specs:
        eid, nodes[time] = exact_state(
            w, i, "卫尉寺卿", "官职", time, event, quote, category,
            f"建立或补足卫尉寺卿{time}节点。",
            "职掌" if quote == duty else "职源与沿革",
            officer=officer, grade=grade,
        )
    cite(w, "Timepoints", nodes["北宋初"], i, rank, "记录宋初卫尉寺卿品位。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, rank, "记录元丰后品位及九寺中的位次。", "品位")
    cite(w, "Timepoints", nodes["北宋元丰五年"], i, roster, "记录元丰新制定员一人。", "编制")
    staff(w, i, tp(w, "卫尉寺", "机构", "北宋元丰五年"), nodes["北宋元丰五年"], roster,
          "元丰新制卫尉寺卿一人。", "编制", quota=1)
    alias_note(w, i, nodes["北宋元丰五年"], aliases, "简称与别名")
    rechain(w, eid, "整理卫尉寺卿完整时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(301, 321)] == [
        "翰林司营", "牛羊司", "勾当牛羊司", "监牛羊司", "牧羊群头",
        "牧子", "揣子", "估羊节级", "巡羊十将", "巡羊员僚",
        "巡羊使臣", "曹司", "承局", "宰手", "秤子", "宰杀务",
        "牛羊供应所", "勾当栈圈官", "卫尉寺", "卫尉寺卿",
    ]
    entry301()
    entry302()
    entry303()
    entry304()
    entry305()
    entry306()
    entry307()
    entry308()
    entry309()
    entry310()
    entry311()
    entry312()
    entry313()
    entry314()
    entry315()
    entry316()
    entry317()
    entry318()
    entry319()
    entry320()


if __name__ == "__main__":
    main()
