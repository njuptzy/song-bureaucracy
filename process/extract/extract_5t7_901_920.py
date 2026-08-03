#!/usr/bin/env python3
"""提取 chapter5t7 第901-920条：文思院吏额、少府监所属诸院。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_881_900 as previous


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


F = {i: load(i) for i in range(901, 921)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
state = base.state
relation = base.relation
staff = base.staff
cite = base.cite
alias_note = base.alias_note


TIME_HINTS = {
    "唐": 618,
    "宋初": 960,
    "北宋乾德四年": 966,
    "北宋乾德五年十月一日": 967.75,
    "北宋前期（先后隶属，具体年月未载）": 970,
    "北宋开宝八年五月十三日": 975.36,
    "北宋开宝九年七月": 976.54,
    "北宋太平兴国二年": 977,
    "北宋端拱元年": 988,
    "北宋咸平元年": 998,
    "北宋咸平二年": 999,
    "北宋（具体年月未载）": 1000,
    "北宋（文思院，具体年月未载）": 1000.1,
    "宋代（文思院公吏迁转，具体年月未载）": 1050,
    "北宋天圣元年": 1023,
    "北宋元丰新制后": 1081,
    "北宋崇宁三年三月八日": 1104.18,
    "南宋（具体年月未载）": 1140,
    "南宋（文思院，具体年月未载）": 1140.1,
    "南宋（四提辖，具体年月未载）": 1140.2,
    "宋代（文思院，具体年月未载）": 1100,
    "宋代（铸印司，具体年月未载）": 1100.1,
    "宋代（绫锦院，具体年月未载）": 1100.2,
    "宋代（西染院，具体年月未载）": 1100.3,
    "宋代（裁造院，具体年月未载）": 1100.4,
    "北宋（文绣院，具体年月未载）": 1100.5,
    "北宋（裁造院，天圣元年前）": 1000.2,
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


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def set_event(w, tid, event, decision):
    old = w.conn.execute("select event from Timepoints where id=?", (tid,)).fetchone()[0]
    if old == event:
        return
    w.conn.execute("update Timepoints set event=? where id=?", (event, tid))
    w._br("Timepoints", tid, f"事件说明由‘{old}’规范为‘{event}’：{decision}")


def node(w, touched, i, title, type_, time, event, quotation, category,
         decision, field_name=None, *, officer=None, grade=None,
         update_event=False):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )
    if update_event:
        set_event(w, tid, event, decision)
    touched.add(eid)
    return tid


def office_staff(w, touched, i, office, post, time, quotation, decision,
                 field_name=None, *, quota=None, staff_type="官",
                 office_event=None, post_event=None, officer=None):
    office_tid = node(
        w, touched, i, office, "机构", time,
        office_event or f"设置{post}", quotation, "办事机构",
        f"建立或复用{office}{time}编制节点。", field_name,
    )
    post_tid = node(
        w, touched, i, post, "官职", time,
        post_event or f"领{office}事", quotation, "职事或差遣官",
        f"建立或复用{post}{time}节点。", field_name, officer=officer,
    )
    rid = staff(
        w, i, office_tid, post_tid, quotation, decision, field_name,
        quota=quota, staff_type=staff_type,
    )
    return office_tid, post_tid, rid


def parent_child(w, touched, i, parent, child, time, quotation, decision,
                 field_name=None, *, parent_event=None, child_event=None):
    parent_tid = node(
        w, touched, i, parent, "机构", time,
        parent_event or f"统辖{child}", quotation, "上级机构",
        f"建立或复用{parent}{time}节点。", field_name,
    )
    child_tid = node(
        w, touched, i, child, "机构", time,
        child_event or f"隶属{parent}", quotation, "所属机构",
        f"建立或复用{child}{time}节点。", field_name,
    )
    relation(
        w, i, parent_tid, child_tid, "上下级机构", quotation,
        decision, field_name,
    )
    return parent_tid, child_tid


def evolution(w, touched, i, source_title, target_title, time, quotation,
              decision, field_name=None, *, source_type="机构",
              target_type="机构", source_event=None, target_event=None):
    source_tid = node(
        w, touched, i, source_title, source_type, time,
        source_event or f"转为{target_title}", quotation, "演变前",
        f"建立或复用{source_title}{time}演变节点。", field_name,
    )
    target_tid = node(
        w, touched, i, target_title, target_type, time,
        target_event or f"由{source_title}转入", quotation, "演变后",
        f"建立或复用{target_title}{time}演变节点。", field_name,
    )
    relation(
        w, i, source_tid, target_tid, "前后演变", quotation,
        decision, field_name,
    )
    return source_tid, target_tid


def group_members(w, touched, i, group_title, time, event, members,
                  quotation, decision, field_name=None):
    group_tid = node(
        w, touched, i, group_title, "官职", time, event, quotation,
        "官职统称", f"建立或复用{group_title}{time}统称节点。", field_name,
        update_event=True,
    )
    for member_title, member_time in members:
        member_tid = node(
            w, touched, i, member_title, "官职", member_time,
            f"{group_title}所指实例", quotation, f"{group_title}实例",
            f"建立或复用{member_title}{member_time}实例节点。", field_name,
        )
        relation(
            w, i, group_tid, member_tid, "统称与实例", quotation,
            f"{member_title}是{group_title}的实例。{decision}", field_name,
        )
    return group_tid


BOUNDARY_TIME = "宋代（文思院两界，具体年月未载）"


def dual_boundary_clerk(i, title, event):
    quote = F[i]["text"]
    w, touched = W(i), set()
    for boundary in ("文思院上界", "文思院下界"):
        office_staff(
            w, touched, i, boundary, title, BOUNDARY_TIME, quote,
            f"文思院上、下界均置{title}。", quota=None, staff_type="公吏",
            office_event=f"设置{title}", post_event=event, officer="公吏",
        )
    finish(w, touched, f"整理{title}在文思院上、下界的设置与职掌。")


def entry901():
    dual_boundary_clerk(901, "库子", "掌管收支现存官物")


def entry902():
    i, quote = 902, F[902]["text"]
    w, touched = W(i), set()
    for boundary in ("文思院上界", "文思院下界"):
        office_staff(
            w, touched, i, boundary, "手分", BOUNDARY_TIME, quote,
            "文思院上、下界均置手分。", staff_type="公吏",
            office_event="设置手分", post_event="掌行遣本界文字", officer="公吏",
        )
    evolution(
        w, touched, i, "手分", "押司官", "北宋（文思院，具体年月未载）",
        quote, "北宋文思院手分递迁押司官。", source_type="官职",
        target_type="官职", source_event="可递迁押司官",
        target_event="由手分递迁",
    )
    for target in ("副知", "专知官"):
        evolution(
            w, touched, i, "手分", target, "南宋（文思院，具体年月未载）",
            quote, f"南宋文思院手分改迁{target}。", source_type="官职",
            target_type="官职", source_event="不再迁押司官，改迁副知或专知官",
            target_event="由手分递迁",
        )
    finish(w, touched, "整理手分两界设置、文字职掌及北宋南宋迁转变化。")


def entry903():
    i, quote = 903, F[903]["text"]
    w, touched = W(i), set()
    for boundary in ("文思院上界", "文思院下界"):
        office_staff(
            w, touched, i, boundary, "贴司", BOUNDARY_TIME, quote,
            "文思院上、下界均置贴司。", staff_type="公吏",
            office_event="设置贴司", post_event="应付抄写文字等公事", officer="公吏",
        )
    time = "宋代（文思院公吏迁转，具体年月未载）"
    evolution(
        w, touched, i, "门司", "贴司", time, quote,
        "门司递迁贴司。", source_type="官职", target_type="官职",
        source_event="位次低于贴司，可递迁贴司",
        target_event="由门司递迁，位次低于手分",
    )
    evolution(
        w, touched, i, "贴司", "手分", time, quote,
        "贴司递迁手分。", source_type="官职", target_type="官职",
        source_event="可递迁手分", target_event="由贴司递迁",
    )
    finish(w, touched, "整理贴司两界设置、文书职掌、位次与门司至手分迁转链。")


def entry904():
    i, main = 904, F[904]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    for boundary in ("文思院上界", "文思院下界"):
        office_staff(
            w, touched, i, boundary, "专知官", "南宋（文思院，具体年月未载）",
            main, "南宋文思院上、下界均置专知官。", staff_type="公吏",
            office_event="设置专知官",
            post_event="掌官物计帐结帐并催促造作，位在库子、门司、贴司、手分之上",
            officer="公吏",
        )
    post = node(
        w, touched, i, "专知官", "官职", "南宋（文思院，具体年月未载）",
        "满二年界并通理入仕十七年可出职补进义副尉", main,
        "公吏", "整理专知官界满出职条件。", update_event=True,
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理专知官南宋两界设置、职掌位次、迁补与二年界出职制度。")


def entry905():
    assert not F[905]["text"]
    assert F[905]["fields"].get("__status__") == "placeholder"


def entry906():
    i, quote = 906, F[906]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "文思院下界", "副知", "南宋（文思院，具体年月未载）",
        quote, "南宋仅文思院下界置副知。", staff_type="公吏",
        office_event="设置副知",
        post_event="职同专知而位略次，手分可递迁；二年界满可按条件出职进义副尉",
        officer="公吏",
    )
    cite(w, "Timepoints", post, i, quote, "补证副知职掌、位次、迁补和出职制度。")
    finish(w, touched, "整理副知南宋下界设置、位次、手分迁补与二年界出职制度。")


def entry907():
    i, quote = 907, F[907]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "专副", "宋代（文思院，具体年月未载）",
        "专知官、副知连称",
        (("专知官", "宋代（文思院，具体年月未载）"),
         ("副知", "宋代（文思院，具体年月未载）")),
        quote, "本条明定专副是专知官、副知的连称。",
    )
    finish(w, touched, "整理专副统称及专知官、副知两个实例。")


def entry908():
    i, quote = 908, F[908]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "文思院", "押司官", "北宋（文思院，具体年月未载）",
        quote, "北宋文思院置押司官。", staff_type="公吏",
        office_event="设置押司官", post_event="监押看守本院官物出入，头名满三年补进武副尉",
        officer="公吏",
    )
    finish(w, touched, "整理押司官北宋文思院设置、官物监押职掌及头名出职制度。")


def entry909():
    i, quote = 909, F[909]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "文思院", "作家", "宋代（文思院，具体年月未载）",
        quote, "文思院官工中置作家。", staff_type="官工",
        office_event="设置官工作家",
        post_event="掌和雇承揽、打造器皿并管辖作头工匠造作", officer="官工",
    )
    finish(w, touched, "整理作家作为文思院官工及其造作、承揽和工匠管理职掌。")


def entry910():
    i, main = 910, F[910]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    group = group_members(
        w, touched, i, "四提辖", "南宋（四提辖，具体年月未载）",
        "南宋四个提辖官合称，为储才之地",
        (
            ("提辖榷货务都茶场", "南宋绍兴六年"),
            ("提辖杂买务杂卖场", "南宋绍兴六年"),
            ("提辖文思院上下界", "南宋绍兴六年正月"),
            ("提辖左藏东、西库", "南宋绍兴二十七年"),
        ),
        main, "正文明确列举四提辖的四个正式实例。",
    )
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理四提辖统称、四个正式词头实例、储才性质与简称证据。")


def entry911():
    i, quote = 911, F[911]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "少府监", "铸印司", "北宋（具体年月未载）", quote,
        "北宋铸印司隶少府监。", parent_event="统辖铸印司",
        child_event="隶少府监，铸造官印、朱记",
    )
    parent_child(
        w, touched, i, "文思院", "铸印司", "南宋（具体年月未载）", quote,
        "南宋铸印司隶文思院。", parent_event="统辖铸印司",
        child_event="隶文思院，铸造官印、朱记",
    )
    for post in ("铸印司篆文官", "副篆文官"):
        office_staff(
            w, touched, i, "铸印司", post, "宋代（铸印司，具体年月未载）",
            quote, f"铸印司置{post}一人。", quota=1, staff_type="差遣官",
            office_event="铸造官印、朱记，置篆文官、副篆文官各一人",
            post_event="掌铸印司印文事务，编制一人",
        )
    finish(w, touched, "整理铸印司南北宋隶属、铸印职掌及篆文官编制。")


def entry912():
    i, main = 912, F[912]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "铸印司", "铸印司篆文官", "宋代（铸印司，具体年月未载）",
        main, "铸印司设篆文官，掌官印、朱记印文书写。", staff_type="差遣官",
        office_event="设置篆文官、副篆文官",
        post_event="掌官印、朱记印文书写，因多用篆文得名",
    )
    office_staff(
        w, touched, i, "铸印司", "副篆文官", "宋代（铸印司，具体年月未载）",
        main, "铸印司另有副篆文官。", staff_type="差遣官",
        office_event="设置篆文官、副篆文官", post_event="为篆文官之副",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理铸印司篆文官正式词头、印文职掌、副篆文官编制与简称证据。")


def entry913():
    i, main = 913, F[913]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "绫锦院", "机构", "北宋乾德五年十月一日",
        "始置绫锦院", origin, "监当局", "记录绫锦院始置时间。",
        "职源与沿革", update_event=True,
    )
    parent_child(
        w, touched, i, "少府监", "绫锦院", "北宋（具体年月未载）", main,
        "北宋绫锦院隶少府监。", parent_event="统辖绫锦院",
        child_event="隶少府监，在开封昭庆坊",
    )
    for target in ("西绫锦院", "东绫锦院"):
        evolution(
            w, touched, i, "绫锦院", target, "北宋太平兴国二年", origin,
            f"太平兴国二年绫锦院分为{target}。", "职源与沿革",
            source_event="分为西绫锦院、东绫锦院",
            target_event="由绫锦院分置",
        )
        evolution(
            w, touched, i, target, "绫锦院", "北宋端拱元年", origin,
            f"端拱元年{target}复合为绫锦院。", "职源与沿革",
            source_event="与另一院复合为绫锦院",
            target_event="东、西绫锦院复合为一院",
        )
    duty_tp = node(
        w, touched, i, "绫锦院", "机构", "北宋咸平元年",
        "掌织锦绮；此后兼织绢，供进御服饰", duty, "监当局",
        "记录咸平元年后兼织绢的职掌变化。", "职掌", update_event=True,
    )
    parent_child(
        w, touched, i, "工部", "绫锦院", "南宋（具体年月未载）", main,
        "南宋绫锦院拨隶工部。", parent_event="统辖绫锦院",
        child_event="拨隶工部",
    )
    office_staff(
        w, touched, i, "绫锦院", "监绫锦院", "宋代（绫锦院，具体年月未载）",
        roster, "绫锦院置监绫锦院三人。", "编制", quota=3,
        staff_type="监官", office_event="置监官三人并领兵匠一千零三十四人",
        post_event="掌领绫锦院公事，编制三人",
    )
    office_staff(
        w, touched, i, "绫锦院", "绫锦院兵匠", "宋代（绫锦院，具体年月未载）",
        roster, "绫锦院拥有兵匠一千零三十四人。", "编制", quota=1034,
        staff_type="兵匠", office_event="拥有兵匠一千零三十四人",
        post_event="从事织锦绮、绢等造作", officer="兵匠",
    )
    cite(w, "Timepoints", start, i, main, "补证绫锦院监当局性质与北宋地点。")
    cite(w, "Timepoints", duty_tp, i, roster, "补证绫锦院织锦机与兵匠规模。", "编制")
    finish(w, touched, "整理绫锦院始置、分合、南北宋隶属、职掌及监官兵匠编制。")


def entry914():
    i, main = 914, F[914]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "绫锦院", "监绫锦院", "宋代（绫锦院，具体年月未载）",
        main, "监绫锦院掌领院事，编制三人。", quota=3, staff_type="监官",
        office_event="置监绫锦院三人",
        post_event="掌领绫锦院公事，由京朝官、诸司使副、内侍分别差充",
        officer="文臣京朝官、武臣诸司使副、内侍官差充",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理监绫锦院三人编制、职掌、差充来源与简称证据。")


def entry915():
    i, main = 915, F[915]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    evolution(
        w, touched, i, "染署", "染坊", "唐", origin,
        "唐代染署后改称染坊。", "职源与沿革",
        source_event="后改称染坊", target_event="由染署改称",
    )
    node(
        w, touched, i, "染坊", "机构", "宋初", "宋初沿称染坊", origin,
        "监当局前身", "记录宋初沿称染坊。", "职源与沿革", update_event=True,
    )
    evolution(
        w, touched, i, "染坊", "染院", "北宋开宝八年五月十三日", origin,
        "开宝八年五月十三日染坊见称染院。", "职源与沿革",
        source_event="改见称染院", target_event="由染坊改称",
    )
    for target in ("东染院", "西染院"):
        evolution(
            w, touched, i, "染院", target, "北宋开宝九年七月", origin,
            f"开宝九年七月染院分为{target}。", "职源与沿革",
            source_event="分为东、西染院", target_event="由染院分置",
        )
    evolution(
        w, touched, i, "东染院", "西染院", "北宋咸平二年", origin,
        "咸平二年东染院并入西染院。", "职源与沿革",
        source_event="并入西染院", target_event="接收东染院",
    )
    early_time = "北宋前期（先后隶属，具体年月未载）"
    for parent in ("三司", "提举在京诸司库务司"):
        parent_child(
            w, touched, i, parent, "西染院", early_time, main,
            f"北宋前期西染院分隶{parent}。",
            parent_event="北宋前期分辖西染院",
            child_event="北宋前期分隶三司、提举在京诸司库务司",
        )
    parent_child(
        w, touched, i, "少府监", "西染院", "北宋元丰新制", main,
        "元丰新制后西染院隶少府监。", parent_event="统辖西染院",
        child_event="元丰新制后隶少府监",
    )
    parent_child(
        w, touched, i, "工部", "西染院", "南宋（具体年月未载）", main,
        "南宋西染院拨归工部。", parent_event="统辖西染院",
        child_event="南宋拨归工部",
    )
    duty_tp = node(
        w, touched, i, "西染院", "机构", "宋代（西染院，具体年月未载）",
        "为丝帛苎麻绦线绳及皮革纸张等物染色，供宫廷官府", duty,
        "监当局", "整理西染院染色职掌。", "职掌", update_event=True,
    )
    for post, quota, kind in (
        ("监西染院", 2, "监官"), ("西染院监门官", 1, "监门官"),
        ("西染院工匠", 613, "工匠"),
    ):
        office_staff(
            w, touched, i, "西染院", post, "宋代（西染院，具体年月未载）",
            roster, f"西染院置{post}{quota}人。", "编制", quota=quota,
            staff_type=kind, office_event="置监官、监门官并领工匠",
            post_event=f"西染院{kind}，编制{quota}人", officer=kind,
        )
    cite(w, "Timepoints", duty_tp, i, roster, "补证西染院监官、监门官与工匠编制。", "编制")
    alias_note(w, i, duty_tp, aliases, "简称")
    finish(w, touched, "整理西染院唐宋源流、东染院分合、南北宋隶属、职掌编制与别称证据。")


def entry916():
    i, main = 916, F[916]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "西染院", "监西染院", "宋代（西染院，具体年月未载）",
        main, "监西染院掌领染色公事，编制二人。", quota=2,
        staff_type="监官", office_event="置监西染院二人",
        post_event="掌领本院染色公事，由京朝官、诸司使副或内侍差充",
        officer="京朝官、诸司使副或内侍差充",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理监西染院二人编制、染色职掌、差充来源与简称证据。")


def entry917():
    i, quote = 917, F[917]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "西染院", "勾当染院公事", "北宋元丰新制后",
        quote, "元丰后见置勾当染院公事，由京朝官差充。",
        staff_type="勾当官", office_event="元丰后或置勾当公事官",
        post_event="职掌同监官，由京朝官差充", officer="京朝官差充",
    )
    finish(w, touched, "整理勾当染院公事元丰后设置、差充来源与职掌。")


def entry918():
    i, main = 918, F[918]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "别称")
    w, touched = W(i), set()
    node(
        w, touched, i, "针线院", "机构", "宋初", "北宋初为针线院", origin,
        "监当局前身", "记录裁造院宋初前身。", "职源", update_event=True,
    )
    evolution(
        w, touched, i, "针线院", "裁造院", "北宋乾德四年", origin,
        "乾德四年始置裁造院，承接针线院。", "职源",
        source_event="改置为裁造院", target_event="始置，前身为针线院",
    )
    parent_child(
        w, touched, i, "少府监", "裁造院", "北宋（具体年月未载）", main,
        "北宋裁造院隶少府监。", parent_event="统辖裁造院",
        child_event="隶少府监，先在利仁坊后徙延康坊",
    )
    parent_child(
        w, touched, i, "工部", "裁造院", "南宋（具体年月未载）", main,
        "南宋裁造院拨归工部。", parent_event="统辖裁造院",
        child_event="南宋拨归工部",
    )
    duty_tp = node(
        w, touched, i, "裁造院", "机构", "宋代（裁造院，具体年月未载）",
        "裁制服饰、卧房设施及仪鸾司什物，供邦国使用", duty,
        "监当局", "整理裁造院职掌。", "职掌", update_event=True,
    )
    for post, quota, kind in (
        ("监裁造院", 2, "监官或勾当官"),
        ("裁造院监门官", 1, "监门官"),
        ("裁造院工匠", 267, "工匠"),
    ):
        office_staff(
            w, touched, i, "裁造院", post, "宋代（裁造院，具体年月未载）",
            roster, f"裁造院置{post}{quota}人。", "编制", quota=quota,
            staff_type=kind, office_event="置监官、勾当官、监门官并领工匠",
            post_event=f"裁造院{kind}，编制{quota}人", officer=kind,
        )
    office_staff(
        w, touched, i, "裁造院", "裁造院女工", "北宋（裁造院，天圣元年前）",
        roster, "裁造院曾招女工。", "编制", staff_type="女工",
        office_event="招用女工", post_event="受招从事裁造", officer="女工",
    )
    node(
        w, touched, i, "裁造院女工", "官职", "北宋天圣元年",
        "放归女工，此后不复招收", roster, "终止编制",
        "记录天圣元年女工放归及停止招收。", "编制", officer="女工",
        update_event=True,
    )
    cite(w, "Timepoints", duty_tp, i, roster, "补证裁造院官额、工匠和女工制度。", "编制")
    alias_note(w, i, duty_tp, aliases, "别称")
    finish(w, touched, "整理裁造院前身始置、南北宋隶属、职掌、官匠女工编制与别称证据。")


def entry919():
    i, main = 919, F[919]["text"]
    aliases = field(i, "别称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "裁造院", "监裁造院", "宋代（裁造院，具体年月未载）",
        main, "监裁造院掌领院事，编制二人。", quota=2,
        staff_type="监官", office_event="置监裁造院二人",
        post_event="掌领裁造院公事，由京朝官、三班使臣或内侍充任",
        officer="京朝官、三班使臣或内侍充任",
    )
    alias_note(w, i, post, aliases, "别称")
    finish(w, touched, "整理监裁造院二人编制、职掌、差充来源与别称证据。")


def entry920():
    i, main = 920, F[920]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    node(
        w, touched, i, "文绣院", "机构", "北宋崇宁三年三月八日",
        "始置文绣院", origin, "监当局", "记录文绣院始置时间。", "职源",
        update_event=True,
    )
    parent_child(
        w, touched, i, "少府监", "文绣院", "北宋（文绣院，具体年月未载）", main,
        "北宋文绣院隶少府监。",
        parent_event="统辖文绣院", child_event="北宋隶少府监",
    )
    duty_tp = node(
        w, touched, i, "文绣院", "机构", "北宋（文绣院，具体年月未载）",
        "刺绣服饰、法物，供皇帝以下至宾客祭祀使用", duty,
        "监当局", "整理文绣院始置后的职掌。", "职掌", update_event=True,
    )
    office_staff(
        w, touched, i, "文绣院", "文绣院绣工", "北宋（文绣院，具体年月未载）",
        roster, "文绣院有绣工三百人。", "编制", quota=300,
        staff_type="绣工", office_event="领绣工三百人",
        post_event="从事服饰法物刺绣，编制三百人", officer="绣工",
    )
    cite(w, "Timepoints", duty_tp, i, main, "补证文绣院监当局性质及北宋隶属。")
    finish(w, touched, "整理文绣院崇宁始置、少府监隶属、刺绣职掌与绣工编制。")


def main():
    for i in range(901, 921):
        globals()[f"entry{i}"]()
        suffix = " placeholder skipped" if i == 905 else " done"
        print(f"#{i} {F[i]['title']}{suffix}")


if __name__ == "__main__":
    main()
