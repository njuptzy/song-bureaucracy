#!/usr/bin/env python3
"""提取 chapter5t7 第1341-1360条：主管禁卫所与御前忠佐军头引见司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1321_1340 as previous


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


F = {i: load(i) for i in range(1341, 1361)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
relation = base.relation
staff = base.staff
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "五代后周": 955,
    "宋初": 960,
    "北宋初": 960.1,
    "北宋端拱二年正月": 989.05,
    "北宋真宗朝后": 1010,
    "北宋熙宁二年": 1069,
    "北宋熙宁四年十二月": 1071.95,
    "北宋熙宁七年九月": 1074.70,
    "南宋绍兴三十二年九月二日": 1162.70,
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


def evolution(w, touched, i, source_title, target_title, time, quotation,
              decision, field_name=None, *, entity_type="机构",
              source_event=None, target_event=None):
    source = node(
        w, touched, i, source_title, entity_type, time,
        source_event or f"改称{target_title}", quotation, "演变前",
        f"建立或复用{source_title}演变节点。", field_name,
        update_event=True,
    )
    target = node(
        w, touched, i, target_title, entity_type, time,
        target_event or f"由{source_title}改称", quotation, "演变后",
        f"建立或复用{target_title}演变节点。", field_name,
        update_event=True,
    )
    relation(w, i, source, target, "前后演变", quotation, decision, field_name)
    return source, target


def canonicalize_guard_supervisor(w, quotation):
    old = w.find_entity("主管禁卫所", "官职")
    formal = w.find_entity("主管禁卫所主管官", "官职")
    if old is not None:
        assert formal is None or formal == old, (old, formal)
        w.conn.execute(
            "update Entities set title='主管禁卫所主管官',quotation=? where id=?",
            (quotation, old),
        )
        w._br(
            "Entities", old,
            "第1341条明确‘主管禁卫所’是官司；将上一批据‘主管官一员’"
            "建立的同名官职规范为‘主管禁卫所主管官’，区分机构与属官。",
        )
        formal = old
    assert formal is not None
    return formal


def combined_staff(w, touched, i, title, time, quotation, event,
                   staff_type, *, quota=None, field_name=None):
    return office_staff(
        w, touched, i, "御前忠佐军头、引见司", title, time, quotation,
        f"{title}隶御前忠佐军头、引见司。", field_name,
        quota=quota, staff_type=staff_type,
        office_event=f"设置{title}", post_event=event,
    )


def six_rank_staff(i, event, *, aliases_name=None):
    main = F[i]["text"]
    w, touched = W(i), set()
    _, post, _ = combined_staff(
        w, touched, i, F[i]["title"], "宋代", main, event,
        "御前忠佐禁秩",
    )
    ranked = node(
        w, touched, i, F[i]["title"], "官职", "宋代", event, main,
        "御前忠佐禁秩", f"保存{F[i]['title']}的六资序位。",
        update_event=True,
    )
    assert ranked == post
    if aliases_name:
        alias_note(w, i, post, field(i, aliases_name), aliases_name)
    group = node(
        w, touched, i, "御前忠佐六资", "官职", "宋代",
        "御前忠佐军头引见司六等迁转禁秩", main,
        "禁军位秩统称", "建立御前忠佐六资同期统称节点。",
    )
    relation(w, i, group, post, "统称与实例", main,
             f"{F[i]['title']}为御前忠佐六资之一。")
    finish(w, touched, f"整理{F[i]['title']}的禁秩序位、军头引见司隶属与简称。")


def entry1341():
    i, main, aliases = 1341, F[1341]["text"], field(1341, "简称")
    w, touched = W(i), set()
    supervisor_eid = canonicalize_guard_supervisor(w, main)
    source, office = evolution(
        w, touched, i, "行宫禁卫所", "主管禁卫所",
        "南宋绍兴元年二月三日", main,
        "绍兴元年二月三日行宫禁卫所一分为二，分出主管禁卫所。",
        source_event="一分为行在皇城司、主管禁卫所",
        target_event="由行宫禁卫所分出，掌车驾行幸扈从禁旅及禁卫诸班直",
    )
    cite(w, "Timepoints", office, i, main,
         "保存主管禁卫所职掌与主管官、使臣、手分等编制。")
    supervisor = node(
        w, touched, i, "主管禁卫所主管官", "官职",
        "南宋绍兴元年二月三日", "主管本所禁卫事务", main,
        "主管禁卫所主管官", "复用并规范主管禁卫所主管官。",
        officer="主管官", update_event=True,
    )
    assert w.conn.execute(
        "select entity_id from Timepoints where id=?", (supervisor,)
    ).fetchone()[0] == supervisor_eid
    staff(w, i, office, supervisor, main, "主管禁卫所置主管官一员。",
          quota="一员", staff_type="主管官")
    for title, quota, staff_type in (
        ("主管禁卫所使臣", "二名", "使臣"),
        ("主管禁卫所手分", "二人", "吏员"),
        ("主管禁卫所装界人", "一名", "技术吏员"),
        ("主管禁卫所作画人", "一名", "技术吏员"),
        ("主管禁卫所投送文字亲事官", None, "禁兵差役"),
    ):
        post = node(
            w, touched, i, title, "官职", "南宋绍兴元年二月三日",
            f"主管禁卫所编制：{quota or '员额未载'}", main,
            "主管禁卫所属员", f"据编制建立{title}。",
        )
        staff(w, i, office, post, main, f"主管禁卫所编制列有{title}。",
              quota=quota, staff_type=staff_type)
    alias_note(w, i, office, aliases, "简称")
    finish(w, touched, "整理主管禁卫所从行宫禁卫所分出、职掌、主管官和属员编制。")


def entry1342():
    i, main = 1342, F[1342]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "主管禁卫所", F[i]["title"], "南宋", main,
        "内等子由内侍充，隶主管禁卫所，扈从时捋袖擎拳高声喝叫。",
        staff_type="禁卫人员", office_event="统辖内等子",
        post_event="由内侍充，扈从禁卫",
    )
    finish(w, touched, "整理内等子的主管禁卫所隶属、内侍来源与扈从职事。")


def entry1343():
    i, main = 1343, F[1343]["text"]
    origin = field(i, "职源与沿革")
    duty, roster, aliases = field(i, "职掌"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    old = node(
        w, touched, i, "军头引见司", "机构", "宋初",
        "设置，后殿引见与军头事务合称", origin, "军头引见机构前身",
        "记录宋初军头引见司。", "职源与沿革", update_event=True,
    )
    combined = node(
        w, touched, i, F[i]["title"], "机构", "北宋端拱二年正月",
        "军头司、引见司分别加御前忠佐名，名二司而后实为一司",
        origin, "御前忠佐禁军机构", "建立端拱二年御前忠佐军头、引见司。",
        "职源与沿革", update_event=True,
    )
    relation(w, i, old, combined, "前后演变", origin,
             "宋初军头引见司至端拱二年分别冠御前忠佐名。", "职源与沿革")
    true_zong = node(
        w, touched, i, F[i]["title"], "机构", "北宋真宗朝后",
        "御前忠佐军头司、引见司名为二司，实为一司", origin,
        "御前忠佐禁军机构", "记录真宗朝后两司合一状态。",
        "职源与沿革", update_event=True,
    )
    node(w, touched, i, F[i]["title"], "机构", "南宋",
         "沿置", origin, "御前忠佐禁军机构", "记录南宋沿置。",
         "职源与沿革", update_event=True)
    for member_title in ("御前忠佐军头司", "御前忠佐引见司"):
        member = node(
            w, touched, i, member_title, "机构", "北宋真宗朝后",
            "名为二司、实属军头引见一司", origin, "合一机构名义分司",
            f"建立{member_title}真宗朝后承载节点。", "职源与沿革",
        )
        relation(w, i, true_zong, member, "统称与实例", origin,
                 f"{member_title}是御前忠佐军头、引见司的名义分司。",
                 "职源与沿革")
    cite(w, "Timepoints", true_zong, i, duty,
         "保存后殿引见、军员呈试、罪人引对决遣、拦驾审奏及武举复试职掌。",
         "职掌")
    cite(w, "Timepoints", true_zong, i, roster,
         "保存所总禁军、职事官、吏额、六资及散员军职编制。", "编制")
    alias_note(w, i, true_zong, aliases, "简称")
    for title, quota, event in (
        ("马直", "一指挥", "所总禁军，熙宁四年十二月罢"),
        ("步直", "一指挥", "所总禁军，熙宁四年十二月罢"),
        ("御前忠佐散指挥班", "一班", "所总禁军散指挥班"),
        ("军头司祗候指挥", "备员元额1960人", "所总禁军祗候指挥"),
    ):
        unit = node(
            w, touched, i, title, "机构", "北宋", event, roster,
            "御前忠佐所总禁军", f"据编制建立{title}。", "编制",
        )
        parent = node(
            w, touched, i, F[i]["title"], "机构", "北宋",
            "统辖所总禁军", roster, "御前忠佐禁军机构",
            "建立北宋编制承载节点。", "编制",
        )
        relation(w, i, parent, unit, "上下级机构", roster,
                 f"编制明确{title}为本司所总禁军。", "编制")
    for title in ("马直", "步直"):
        node(w, touched, i, title, "机构", "北宋熙宁四年十二月",
             "拨出并罢本司所属指挥", roster, "禁军指挥罢隶",
             f"记录{title}熙宁四年十二月罢本司编制。", "编制",
             update_event=True)
    node(w, touched, i, "军头司祗候指挥", "机构", "北宋熙宁二年",
         "原额1960人中罢960人", roster, "禁军指挥减额",
         "记录军头司祗候指挥熙宁二年减额。", "编制", update_event=True)
    ranks = (
        "御前忠佐马步军都军头", "御前忠佐马步军副都军头",
        "御前忠佐马军都军头", "御前忠佐马军副都军头",
        "御前忠佐步军都军头", "御前忠佐步军副都军头",
    )
    group_instances(
        w, touched, i, "御前忠佐六资", "官职", "宋代",
        "御前忠佐将校六等迁转禁秩", ranks, roster,
        "编制明确列出御前忠佐六资。", "编制",
    )
    parent = node(
        w, touched, i, F[i]["title"], "机构", "宋代",
        "掌御前忠佐将校六资名籍", roster, "御前忠佐禁军机构",
        "建立本司六资编制承载节点。", "编制",
    )
    for title in ranks:
        rank = node(w, touched, i, title, "官职", "宋代",
                    "御前忠佐六资之一", roster, "御前忠佐禁秩",
                    f"复用{title}六资节点。", "编制")
        staff(w, i, parent, rank, roster, f"{title}名籍隶本司。", "编制",
              staff_type="御前忠佐禁秩")
    for title, time, quota, staff_type in (
        ("勾当御前忠佐军头引见司", "北宋", "五人", "勾当官"),
        ("干办御前忠佐军头引见司", "南宋", None, "干办官"),
        ("提点御前忠佐军头引见司", "南宋", None, "提点官"),
    ):
        combined_staff(w, touched, i, title, time, roster,
                       f"掌领本司公事，{staff_type}", staff_type,
                       quota=quota, field_name="编制")
    finish(w, touched, "整理御前忠佐军头引见司沿革、两名义分司、职掌、禁军及六资编制。")


def entry1344():
    i, main = 1344, F[1344]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    source, target = evolution(
        w, touched, i, "军头司", F[i]["title"], "北宋端拱二年正月",
        origin, "端拱二年正月军头司改称御前忠佐军头司。", "职源与沿革",
        source_event="改称御前忠佐军头司",
        target_event="由军头司改称，真宗朝后与引见司实合一",
    )
    cite(w, "Timepoints", target, i, duty,
         "保存崇政殿供奉官及诸州驻泊、捕捉、权管事务职掌。", "职掌")
    cite(w, "Timepoints", target, i, roster, "编制参见军头引见司总条。", "编制")
    alias_note(w, i, target, aliases, "简称")
    finish(w, touched, "整理御前忠佐军头司端拱改名、职掌、合一状态与简称。")


def entry1345():
    i, main, aliases = 1345, F[1345]["text"], field(1345, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "御前忠佐军头司", F[i]["title"], "北宋", main,
        "勾当官由马步军都军头、诸司使副或内侍都知押班充，掌领本司公事。",
        quota="五人", staff_type="勾当官",
        office_event="置勾当官", post_event="掌领本司公事",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理勾当御前忠佐军头司的差充资格、职掌、员额与简称。")


def entry1346():
    i, main = 1346, F[1346]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    source, target = evolution(
        w, touched, i, "引见司", F[i]["title"], "北宋端拱二年正月",
        origin, "端拱二年正月引见司改称御前忠佐引见司。", "职源与沿革",
        source_event="改称御前忠佐引见司",
        target_event="由引见司改称",
    )
    true_zong = node(
        w, touched, i, F[i]["title"], "机构", "北宋真宗朝后",
        "与御前忠佐军头司名二司而实合一", origin,
        "合一机构名义分司", "记录真宗朝后与军头司合一。", "职源与沿革",
        update_event=True,
    )
    cite(w, "Timepoints", true_zong, i, duty,
         "保存军头名籍、诸军拣阅引见分配及后殿祗候政令职掌。", "职掌")
    cite(w, "Timepoints", true_zong, i, roster, "编制参见军头引见司总条。", "编制")
    alias_note(w, i, true_zong, aliases, "简称")
    node(w, touched, i, F[i]["title"], "机构", "北宋熙宁四年十二月",
         "马直、步直拨出，本司兵罢而机构未罢", origin,
         "御前忠佐引见机构", "区分引见司兵罢与机构废罢。", "职源与沿革",
         update_event=True)
    node(w, touched, i, F[i]["title"], "机构", "北宋熙宁七年九月",
         "仍以军头引见司合称存在", origin, "御前忠佐引见机构",
         "记录熙宁七年仍存军头引见司合称。", "职源与沿革", update_event=True)
    node(w, touched, i, F[i]["title"], "机构", "南宋",
         "沿置，亦称御前忠佐军头引见司", origin, "御前忠佐引见机构",
         "记录南宋沿置。", "职源与沿革", update_event=True)
    finish(w, touched, "整理御前忠佐引见司改名、合一、兵罢而司存、南宋沿置及职掌。")


def entry1347():
    i, main, aliases = 1347, F[1347]["text"], field(1347, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "御前忠佐引见司", F[i]["title"], "北宋", main,
        "勾当官由马步军都军头、诸司使副或内侍都知押班充，掌领本司公事。",
        staff_type="勾当官", office_event="置勾当官",
        post_event="掌领本司公事",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理勾当御前忠佐引见司的差充资格、职掌与简称。")


def entry1348():
    i, main, aliases = 1348, F[1348]["text"], field(1348, "简称")
    w, touched = W(i), set()
    _, post, _ = combined_staff(
        w, touched, i, F[i]["title"], "北宋", main,
        "军头、引见名二司而实一司，勾当官互兼领，五人为额",
        "勾当官", quota="五人",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理勾当御前忠佐军头引见司的合一兼领、五人员额与简称。")


def entry1349():
    i, main = 1349, F[1349]["text"]
    w, touched = W(i), set()
    combined_staff(
        w, touched, i, F[i]["title"], "南宋", main,
        "或置主管官领本司事，职同干办、提点，位次于干办官",
        "主管官",
    )
    finish(w, touched, "整理主管御前忠佐军头引见司的南宋设置、职掌与序位。")


def entry1350():
    i, main, aliases = 1350, F[1350]["text"], field(1350, "简称")
    w, touched = W(i), set()
    source, target = evolution(
        w, touched, i, "勾当御前忠佐军头引见司", F[i]["title"],
        "南宋", main, "南宋改勾当为干办。", entity_type="官职",
        source_event="南宋改称干办御前忠佐军头引见司",
        target_event="由勾当御前忠佐军头引见司改称",
    )
    parent = node(w, touched, i, "御前忠佐军头、引见司", "机构", "南宋",
                  "置干办官", main, "御前忠佐禁军机构",
                  "建立南宋本司编制承载节点。")
    staff(w, i, parent, target, main, "干办官掌领南宋军头引见司公事。",
          staff_type="干办官")
    alias_note(w, i, target, aliases, "简称")
    finish(w, touched, "整理南宋勾当改干办、军头引见司隶属与简称。")


def entry1351():
    i, main = 1351, F[1351]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "干办军头司、主管军头司的连称",
        ("干办御前忠佐军头引见司", "主管御前忠佐军头引见司"),
        main, "正文直接定义干管官为干办军头司、主管军头司连称。",
    )
    finish(w, touched, "建立干管官统称及干办、主管军头引见司两个实例。")


def entry1352():
    i, main = 1352, F[1352]["text"]
    w, touched = W(i), set()
    source, target = evolution(
        w, touched, i, "干办御前忠佐军头引见司", F[i]["title"],
        "南宋绍兴三十二年九月二日", main,
        "绍兴三十二年九月二日，知阁门事兼干办军头引见司者改称提点。",
        entity_type="官职", source_event="知阁门事兼干办者改称提点",
        target_event="由知阁门事兼干办军头引见司者改称，以别普通干办官",
    )
    parent = node(
        w, touched, i, "御前忠佐军头、引见司", "机构",
        "南宋绍兴三十二年九月二日", "设置提点官", main,
        "御前忠佐禁军机构", "建立本司绍兴三十二年编制节点。",
    )
    staff(w, i, parent, target, main, "本司于绍兴三十二年设置提点官。",
          staff_type="提点官")
    finish(w, touched, "整理提点御前忠佐军头引见司的绍兴三十二年改称与隶属。")


def entry1353():
    i, main, aliases = 1353, F[1353]["text"], field(1353, "简称")
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "官职", "五代后周", "已置",
         main, "禁军职名源流", "记录五代后周已置内外马步军都军头。",
         update_event=True)
    node(w, touched, i, F[i]["title"], "官职", "北宋初", "沿置",
         main, "禁军职名源流", "记录北宋初沿置。", update_event=True)
    source, target = evolution(
        w, touched, i, F[i]["title"], "御前忠佐马步军都军头",
        "北宋端拱二年正月", main,
        "端拱二年正月随军头引见司加御前忠佐名。",
        entity_type="官职", source_event="改称御前忠佐马步军都军头",
        target_event="六资最高一资，名籍隶军头引见司",
    )
    alias_note(w, i, source, aliases, "简称")
    finish(w, touched, "整理内外马步军都军头五代源流、北宋沿置及端拱改名。")


def entry1354():
    i, main, aliases = 1354, F[1354]["text"], field(1354, "简称")
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "官职", "五代后周", "已置",
         main, "禁军职名源流", "记录五代后周已置内外马步军副都军头。",
         update_event=True)
    source, target = evolution(
        w, touched, i, F[i]["title"], "御前忠佐马步军副都军头",
        "北宋端拱二年正月", main,
        "端拱二年正月改称御前忠佐马步军副都军头。",
        entity_type="官职", source_event="改称御前忠佐马步军副都军头",
        target_event="由内外马步军副都军头改称",
    )
    alias_note(w, i, source, aliases, "简称")
    finish(w, touched, "整理内外马步军副都军头五代源流、端拱改名与简称。")


def entry1355():
    i, main = 1355, F[1355]["text"]
    w, touched = W(i), set()
    evolution(
        w, touched, i, F[i]["title"], "御前忠佐步军都军头",
        "北宋端拱二年正月", main,
        "端拱二年正月内外步军都军头改称御前忠佐步军都军头。",
        entity_type="官职", source_event="改称御前忠佐步军都军头",
        target_event="由内外步军都军头改称",
    )
    finish(w, touched, "整理内外步军都军头端拱二年改名。")


def entry1356():
    i, main, aliases = 1356, F[1356]["text"], field(1356, "简称")
    w, touched = W(i), set()
    source, target = evolution(
        w, touched, i, "内外马步军都军头", F[i]["title"],
        "北宋端拱二年正月", main,
        "端拱二年正月随司名改冠御前忠佐并去内外二字。",
        entity_type="官职", source_event="改称御前忠佐马步军都军头",
        target_event="六资最高一资，名籍隶军头引见司",
    )
    parent = node(w, touched, i, "御前忠佐军头、引见司", "机构",
                  "北宋端拱二年正月", "掌御前忠佐将校名籍", main,
                  "御前忠佐禁军机构", "建立本司端拱二年编制节点。")
    staff(w, i, parent, target, main, "马步军都军头名籍隶军头引见司。",
          staff_type="御前忠佐禁秩")
    group = node(w, touched, i, "御前忠佐六资", "官职", "宋代",
                 "御前忠佐六等迁转禁秩", main, "禁军位秩统称",
                 "建立御前忠佐六资节点。")
    rank = node(w, touched, i, F[i]["title"], "官职", "宋代",
                "六资中最高一资", main, "御前忠佐禁秩",
                "记录六资序位。", update_event=True)
    relation(w, i, group, rank, "统称与实例", main,
             "御前忠佐马步军都军头为六资最高一资。")
    alias_note(w, i, rank, aliases, "简称")
    finish(w, touched, "整理御前忠佐马步军都军头改名、最高禁秩、名籍隶属与简称。")


def entry1357():
    six_rank_staff(
        1357, "非统兵官，为六资第二资，仅次于马步军都军头，名籍隶本司",
        aliases_name="简称",
    )


def entry1358():
    six_rank_staff(
        1358, "六资之一，次于马步军副都军头、高于马军副都军头",
        aliases_name="简称",
    )


def entry1359():
    six_rank_staff(
        1359, "六资之一，次于步军都军头、高于步军副都军头",
        aliases_name="简称",
    )


def entry1360():
    six_rank_staff(
        1360, "六资之一，次于马军都军头、高于马军副都军头",
        aliases_name="简称",
    )


def main():
    for i in range(1341, 1361):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
