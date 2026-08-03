#!/usr/bin/env python3
"""提取 chapter5t7 第1161-1180条：刑部、纠察在京刑狱司与殿前司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1141_1160 as previous


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


F = {i: load(i) for i in range(1161, 1181)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
relation = base.relation
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
parent_child = previous.previous.parent_child
group_instances = previous.previous.previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "后周广顺二年": 952,
    "后周显德三年十二月十四日": 956.96,
    "后周显德末": 959,
    "宋初": 960,
    "北宋建隆二年闰三月初一日": 961.22,
    "北宋建隆二年七月九日": 961.53,
    "北宋淳化元年五月十七日": 990.38,
    "北宋淳化二年八月": 991.6,
    "北宋大中祥符二年七月四日": 1009.51,
    "宋前期": 1050,
    "北宋熙宁七年": 1074,
    "北宋元丰元年十二月十八日": 1078.96,
    "北宋元丰三年": 1080,
    "北宋元丰新制": 1082,
    "北宋景德二年正月十九日": 1005.05,
    "宋代": 1100,
    "南宋初": 1127.1,
    "南宋绍兴五年至七年": 1136,
    "南宋绍兴五年十二月以后": 1135.95,
    "南宋": 1150,
    "南宋乾道初": 1165,
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


def entry1161():
    i = 1161
    origin, duty = field(i, "职源"), field(i, "职掌")
    rank, aliases = field(i, "品位"), field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "审刑院", "审刑院详议官", "北宋淳化二年八月",
        origin, "审刑院置详议官六人。", "职源", quota=6,
        staff_type="审刑院详议官", office_event="设置详议官六人",
        post_event="由朝官差充，覆议大理寺初判、刑部覆审案件",
        officer="朝官",
    )
    cite(w, "Timepoints", post, i, duty, "保存详议、论定并进奏职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存朝官差充且本身无官品。", "品位")
    node(w, touched, i, "审刑院详议官", "官职", "北宋元丰三年",
         "随审刑院罢归刑部而罢置", origin, "废罢差遣",
         "记录审刑院罢归刑部时详议官罢置。", "职源", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理审刑院详议官的始置、六员编制、差充职掌、别名及元丰罢置。")


def entry1162():
    i = 1162
    origin, duty = field(i, "职源"), field(i, "职掌")
    rank, aliases = field(i, "官品"), field(i, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "刑部", "判尚书省刑部事", "宋前期", duty,
        "宋前期判刑部事一或二人领刑部。", "职掌", quota="1-2",
        staff_type="刑部长官差遣", office_event="由一或二员主判",
        post_event="领刑部事，复审判处死刑的大案",
        officer="侍御史知杂事以上朝官",
    )
    cite(w, "Timepoints", post, i, origin, "保存隋代同名领判制度源流。", "职源")
    cite(w, "Timepoints", post, i, rank, "保存差充资格及随本官定品规则。", "官品")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理判尚书省刑部事的隶属、员额、职掌、资格、品位与别称。")


def entry1163():
    i = 1163
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, aliases = field(i, "品位"), field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "刑部详覆官", "官职", "宋初",
         "已有详覆官", origin, "刑部差遣官", "记录宋初已有详覆官。",
         "职源与沿革", update_event=True)
    _, post, _ = office_staff(
        w, touched, i, "刑部", "刑部详覆官", "北宋淳化元年五月十七日",
        origin, "明令以京朝官充刑部详覆官。", "职源与沿革",
        staff_type="刑部详覆官", office_event="设置详覆官",
        post_event="以京朝官差充，审阅大理寺定刑案件", officer="京朝官",
    )
    cite(w, "Timepoints", post, i, duty, "保存详覆案件与核对法卷流程。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存朝官或京官差充。", "品位")
    node(w, touched, i, "刑部详覆官", "官职", "北宋元丰新制",
         "罢置，职事归刑部郎官", origin, "废罢差遣",
         "记录元丰新制罢详覆官。", "职源与沿革", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理刑部详覆官宋初设置、淳化差充、职掌与元丰罢置。")


def entry1164():
    i, main = 1164, F[1164]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "刑部", "刑部详覆习学公事", "北宋熙宁七年",
        main, "熙宁七年置详覆习学公事，由选人充。", quota=6,
        staff_type="详覆习学官", office_event="详覆及习学官不超过六员",
        post_event="由选人充，在详覆官任上实习，三年可改京官", officer="选人",
    )
    finish(w, touched, "建立刑部详覆习学公事的熙宁设置、隶属、差充、员额与改官规则。")


def entry1165():
    i, main = 1165, F[1165]["text"]
    w, touched = W(i), set()
    source = node(w, touched, i, "大理寺详断官", "官职",
                  "北宋元丰元年十二月十八日", "划归刑部", main,
                  "演变前", "记录大理寺详断官划归刑部。", update_event=True)
    _, target, _ = office_staff(
        w, touched, i, "刑部", "刑部详断官", "北宋元丰元年十二月十八日",
        main, "大理寺详断官划归刑部，改隶为刑部详断官。",
        staff_type="刑部定刑官", office_event="接收大理寺详断官",
        post_event="由大理寺详断官划归，负责定刑",
    )
    relation(w, i, source, target, "前后演变", main,
             "大理寺详断官划归刑部后为刑部详断官。")
    node(w, touched, i, "刑部详断官", "官职", "北宋元丰新制",
         "罢置", main, "废罢差遣", "记录元丰官制行后罢置。", update_event=True)
    finish(w, touched, "整理刑部详断官由大理寺划归、刑部隶属及元丰罢置。")


def entry1166():
    i, main = 1166, F[1166]["text"]
    w, touched = W(i), set()
    office_staff(w, touched, i, "刑部", "刑部检法官", "宋前期", main,
                 "刑部检法官由京官差充。", staff_type="刑部检法官",
                 office_event="设置检法官", post_event="由京官差充，检阅本部律令格式",
                 officer="京官")
    finish(w, touched, "建立刑部检法官的刑部隶属、京官差充及检阅律令格式职掌。")


def entry1167():
    i = 1167
    origin, duty, rank = field(i, "职源"), field(i, "职掌"), field(i, "官品")
    w, touched = W(i), set()
    node(w, touched, i, "刑部法直官", "官职", "后唐长兴二年",
         "刑部置法直官二人", origin, "前代官职源流",
         "记录后唐始置二人。", "职源", update_event=True)
    _, post, _ = office_staff(w, touched, i, "刑部", "刑部法直官", "宋前期",
                 duty, "宋前期刑部法直官由选人充。", "职掌",
                 staff_type="刑部法直官", office_event="设置法直官",
                 post_event="由选人充，检阅本部律令格式，改京官后称检法官",
                 officer="选人")
    cite(w, "Timepoints", post, i, rank, "保存选人差充及随本阶定品。", "官品")
    finish(w, touched, "整理刑部法直官后唐源流、宋前期隶属、差充与职掌。")


def entry1168():
    i, main = 1168, F[1168]["text"]
    assert main == "参“尚书六部门”条。"
    w = W(i)
    eid = w.find_entity("刑部", "机构")
    assert eid
    tid = w.conn.execute(
        "select id from Timepoints where entity_id=? order by id limit 1", (eid,)
    ).fetchone()[0]
    cite(w, "Timepoints", tid, i, main,
         "本条仅参见尚书六部门，复用既有刑部实体，不另造事实。",
         note="纯参见条；已查阅并复用刑部")
    w.commit()


def entry1169():
    i = 1169
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称与别名")
    w, touched = W(i), set()
    office = node(w, touched, i, "纠察在京刑狱司", "机构",
                  "北宋大中祥符二年七月四日",
                  "始置，纠察京师诸狱过失与滥刑", origin,
                  "中央司法监察机构", "记录纠察司始置。", "职源与沿革",
                  update_event=True)
    cite(w, "Timepoints", office, i, duty, "保存纠察诸狱范围与受诉职掌。", "职掌")
    cite(w, "Timepoints", office, i, roster, "保存纠察官、手力与兵士编制。", "编制")
    source = node(w, touched, i, "纠察在京刑狱司", "机构", "北宋元丰三年",
                  "并归刑部纠察案", origin, "机构省并",
                  "记录元丰三年并归。", "职源与沿革", update_event=True)
    target = node(w, touched, i, "刑部纠察案", "机构", "北宋元丰三年",
                  "接收纠察在京刑狱司职事", origin, "刑部办事机构",
                  "记录刑部纠察案接收职事。", "职源与沿革", update_event=True)
    relation(w, i, source, target, "前后演变", origin,
             "纠察在京刑狱司元丰三年并归刑部纠察案。", "职源与沿革")
    alias_note(w, i, office, aliases, "简称与别名")
    finish(w, touched, "整理纠察在京刑狱司始置、职掌编制、别称及元丰并归刑部纠察案。")


def entry1170():
    i, main = 1170, F[1170]["text"]
    origin, rank, aliases = field(i, "职源"), field(i, "官品"), field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "纠察在京刑狱司", "纠察在京刑狱",
        "北宋大中祥符二年七月四日", origin, "纠察官二人，以两制以上充。",
        "职源", quota=2, staff_type="纠察官", office_event="置纠察官二人",
        post_event="以两制以上朝官充，领纠察司事", officer="两制以上朝官",
    )
    cite(w, "Timepoints", post, i, main, "补证本条为北宋前期差遣官。")
    cite(w, "Timepoints", post, i, rank, "保存差充资格及随本官定品。", "官品")
    node(w, touched, i, "纠察在京刑狱", "官职", "北宋元丰三年",
         "随纠察在京刑狱司并归刑部而罢置", origin, "废罢差遣",
         "记录元丰三年罢置。", "职源", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理纠察在京刑狱的始置、二员编制、差充资格、简称及元丰罢置。")


def entry1171():
    i, main = 1171, F[1171]["text"]
    w, touched = W(i), set()
    group_instances(w, touched, i, "两司", "机构", "宋初",
                    "殿前司与侍卫亲军司合称",
                    ("殿前司", "侍卫亲军司"), main,
                    "原文明示宋初两司的两个实例。")
    group_instances(w, touched, i, "三衙", "官职", "宋初",
                    "三位禁军都指挥使合称",
                    ("殿前司都指挥使", "侍卫马军都指挥使", "侍卫步军都指挥使"),
                    main, "原文明示宋初三衙称谓所指三位管军官。")
    finish(w, touched, "分别建立宋初两司机构统称与三衙管军官统称。")


def entry1172():
    i, main, aliases = 1172, F[1172]["text"], field(1172, "别称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "三衙", "机构", "北宋景德二年正月十九日",
        "侍卫司不再单独置司后形成三衙体制，三司互不统属",
        ("殿前司", "侍卫亲军马军司", "侍卫亲军步军司"), main,
        "原文明确三衙由三个最高禁军指挥机构组成。",
    )
    node(w, touched, i, "三衙", "机构", "南宋初", "体制几近废坏",
         main, "禁军最高指挥机构统称", "记录建炎初废坏。", update_event=True)
    node(w, touched, i, "三衙", "机构", "南宋绍兴五年至七年", "渐次恢复三衙体制",
         main, "禁军最高指挥机构统称", "记录绍兴间恢复。", update_event=True)
    quota = node(w, touched, i, "三衙", "机构", "南宋乾道初", "禁兵以七万三千为额",
                 main, "禁军最高指挥机构统称", "记录乾道初兵额。", update_event=True)
    alias_note(w, i, group, aliases, "别称")
    cite(w, "Timepoints", quota, i, main, "补证乾道初三衙禁兵总额。")
    finish(w, touched, "整理三衙景德形成、三个机构实例、南宋废复、兵额与别称。")


def entry1173():
    i = 1173
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "殿前司", "机构", "后周广顺二年", "制度源流始置",
         origin, "禁军指挥机构", "记录后周始置源流。", "职源与沿革", update_event=True)
    song = node(w, touched, i, "殿前司", "机构", "宋代", "两宋沿置，掌殿前禁军",
                origin, "禁军指挥机构", "记录两宋沿置。", "职源与沿革", update_event=True)
    cite(w, "Timepoints", song, i, duty, "保存名籍、训练、宿卫戍守、迁补赏罚职掌。", "职掌")
    reform = node(w, touched, i, "殿前司", "机构", "北宋元丰新制",
                  "吏二十八人，分六案", roster, "禁军指挥机构",
                  "记录元丰吏额与分案。", "编制", update_event=True)
    south = node(w, touched, i, "殿前司", "机构", "南宋绍兴五年十二月以后",
                 "神武中军隶入，形成南宋殿司诸军体制", roster,
                 "禁军指挥机构", "记录神武中军隶入。", "编制", update_event=True)
    alias_note(w, i, song, aliases, "简称与别名")
    assert reform and south
    finish(w, touched, "整理殿前司后周源流、两宋沿置职掌、元丰吏额及南宋军制变化。")


def entry1174():
    i = 1174
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster, aliases = field(i, "品位"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(w, touched, i, "殿前司", "殿前司都点检",
                 "后周显德三年十二月十四日", origin, "后周始置殿前都点检。",
                 "职源与沿革", staff_type="殿前司最高军职",
                 office_event="设置都点检", post_event="始置，统领殿前禁军")
    cite(w, "Timepoints", post, i, duty, "保存宋初最高军职职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存位次。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存宋初仅除一人。", "编制")
    node(w, touched, i, "殿前司都点检", "官职", "北宋建隆二年闰三月初一日",
         "罢置，此后不复置", origin, "废罢军职", "记录建隆二年罢置。",
         "职源与沿革", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理殿前司都点检始置、职掌位次、员额、简称及建隆罢置。")


def entry1175():
    i = 1175
    origin, duty, rank, aliases = (field(i, x) for x in ("职源与沿革", "职掌", "品位", "简称"))
    w, touched = W(i), set()
    _, post, _ = office_staff(w, touched, i, "殿前司", "殿前司副都点检",
                 "后周显德末", origin, "后周显德末始置。", "职源与沿革",
                 staff_type="殿前司副统领", office_event="设置副都点检",
                 post_event="殿前司副统领官")
    cite(w, "Timepoints", post, i, duty, "保存副统领职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存军职位次。", "品位")
    node(w, touched, i, "殿前司副都点检", "官职", "北宋建隆二年七月九日",
         "罢置，此后不复置", origin, "废罢军职", "记录建隆二年罢置。",
         "职源与沿革", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理殿前司副都点检始置、职掌位次、简称及建隆罢置。")


def entry1176():
    i = 1176
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster, aliases = field(i, "品位"), field(i, "编制"), field(i, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(w, touched, i, "殿前司", "殿前司都指挥使",
                 "后周广顺二年", origin, "后周始置，两宋沿置。", "职源与沿革",
                 quota=1, staff_type="殿前司最高统领",
                 office_event="设置都指挥使", post_event="始置，两宋沿置，定员一人",
                 grade="从二品")
    cite(w, "Timepoints", post, i, duty, "保存点检罢后成为最高统领。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存从二品及位次。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存一人员额及南宋虚位替代规则。", "编制")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理殿前司都指挥使始置沿置、最高统领职掌、品位员额与别称。")


def entry1177():
    i, main, aliases = 1177, F[1177]["text"], field(1177, "别称")
    w, touched = W(i), set()
    _, office = parent_child(w, touched, i, "殿前司", "殿前司都指挥使司",
                             "宋代", main, "殿前司都指挥使司为殿前司所属治所。",
                             parent_event="下设都指挥使司治所",
                             child_event="殿前都指挥使治所，置孔目、勾押等吏")
    alias_note(w, i, office, aliases, "别称")
    finish(w, touched, "建立殿前司都指挥使司的殿前司隶属、治所职能、吏额与别称。")


def entry1178():
    i, main, aliases = 1178, F[1178]["text"], field(1178, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(w, touched, i, "殿前司", "主管殿前司公事", "南宋",
                 main, "南宋都指挥使虚位时以资浅者主管殿前司公事。",
                 staff_type="殿前司主管军职", office_event="都指挥使虚位时置主管公事",
                 post_event="由官阶不至节度使或新除节度使者领殿前司")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "建立主管殿前司公事的南宋隶属、设置条件与简称。")


def entry1179():
    i, main = 1179, F[1179]["text"]
    w, touched = W(i), set()
    office_staff(w, touched, i, "殿前司", "权主管殿前司公事", "南宋", main,
                 "资更浅者以权主管名义领殿前司公事。", staff_type="权摄主管军职",
                 office_event="以权主管公事领司", post_event="资更浅者权领殿前司公事")
    finish(w, touched, "建立权主管殿前司公事的南宋隶属、权摄性质与简称证据。")


def entry1180():
    i, main = 1180, F[1180]["text"]
    w, touched = W(i), set()
    parent_child(w, touched, i, "殿前司", "主管殿前司", "南宋", main,
                 "主管殿前司为主管殿前司公事的治所。",
                 parent_event="下设主管殿前司治所",
                 child_event="主管殿前司公事治所，置都吏、副都吏等吏")
    finish(w, touched, "建立主管殿前司机构的殿前司隶属、治所性质与吏额。")


def main():
    for i in range(1161, 1181):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
