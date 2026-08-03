#!/usr/bin/env python3
"""提取 chapter5t7 第1041-1060条：御史台六察、四推与五使。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1021_1040 as previous


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


F = {i: load(i) for i in range(1041, 1061)}
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
parent_child = previous.parent_child
group_instances = previous.group_instances


TIME_HINTS = {
    "汉代": -100,
    "唐代": 700,
    "隋大业三年": 607,
    "宋初": 960,
    "宋前期（具体年月未载）": 1050,
    "北宋淳化元年五月十七日": 990.38,
    "北宋咸平元年": 998,
    "北宋咸平元年以后（具体年月未载）": 1005,
    "北宋熙宁十年": 1077,
    "北宋元丰二年": 1079,
    "北宋元丰二年十二月十二日": 1079.95,
    "北宋元丰二年案结后（具体年月未载）": 1080,
    "北宋元丰六年六月一日": 1083.42,
    "北宋元丰七年以前（具体年月未载）": 1083.9,
    "北宋元丰七年二月以后": 1084.15,
    "北宋元丰新制": 1082.1,
    "南宋": 1127,
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


SIX_INSPECTIONS = ("吏察", "户察", "刑察", "兵察", "礼察", "工察")


def entry1041():
    i, main = 1041, F[1041]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    status = field(i, "位遇")
    roster = field(i, "编制")
    w, touched = W(i), set()
    node(w, touched, i, "御史台六察司", "机构", "宋初",
         "遇入阁或国忌礼临时置六察官，但尚未置司", origin,
         "六察司设置前状态", "记录宋初仅临时置官而未置司。", "职源与沿革",
         update_event=True)
    _, founded = parent_child(
        w, touched, i, "御史台", "御史台六察司",
        "北宋元丰二年十二月十二日", origin,
        "元丰二年十二月十二日于御史台设六察司。", "职源与沿革",
        parent_event="设置并统辖六察司",
        child_event="始置，纠察在京百司簿领文字稽违",
    )
    cite(w, "Timepoints", founded, i, duty,
         "补证六察司纠察范围及明确排除的五类机构。", "职掌")
    cite(w, "Timepoints", founded, i, status,
         "位遇仅证明六察司受尚书省都司御史房监督；监督不等同机构隶属。",
         "位遇")
    six_office = node(
        w, touched, i, "御史台六察司", "机构",
        "北宋元丰六年六月一日",
        "定编六察各置御史一员、吏二人",
        roster, "中央监察机构", "记录元丰六年六察编制。", "编制",
        update_event=True,
    )
    for inspection in SIX_INSPECTIONS:
        child = node(
            w, touched, i, inspection, "机构", "北宋元丰六年六月一日",
            "六察司所属察案，置御史一员、吏二人", roster,
            "六察司所属察案", f"建立{inspection}编制节点。", "编制",
        )
        relation(w, i, six_office, child, "上下级机构", roster,
                 f"{inspection}是六察司下设六察之一。", "编制")
        _, _, rid = office_staff(
            w, touched, i, inspection, "察案御史",
            "北宋元丰六年六月一日", roster,
            f"{inspection}置御史一员。", "编制",
            quota=1, staff_type="察案御史",
            office_event="置御史一员、吏二人",
            post_event=f"分领{inspection}纠察事务",
        )
        assert rid
    office_staff(
        w, touched, i, "御史台六察司", "监察御史",
        "北宋元丰七年二月以后", roster,
        "元丰七年以后监察御史专任六察。", "编制",
        staff_type="六察官", office_event="由监察御史分领六察",
        post_event="专任六察官，六员或三员",
    )
    node(w, touched, i, "御史台六察司", "机构", "南宋",
         "沿置", origin, "中央监察机构", "记录南宋沿置。", "职源与沿革",
         update_event=True)
    finish(w, touched, "整理六察司宋初未置、元丰始置、监督关系、六察编制及南宋沿置。")


def inspection_entry(i, targets):
    main = F[i]["text"]
    title = F[i]["title"]
    w, touched = W(i), set()
    event = f"掌纠察{targets}文字，设察案御史一员、吏二人"
    tid = node(
        w, touched, i, title, "机构", "北宋元丰六年六月一日",
        event, main, "六察司所属察案", f"整理{title}纠察范围与编制。",
        update_event=True,
    )
    cite(w, "Timepoints", tid, i, main, f"保存{title}所辖纠察对象及吏额。")
    finish(w, touched, f"整理{title}的六察司所属性质、纠察范围、察案御史与吏额。")


def entry1042():
    inspection_entry(1042, "审官东、西院、三班院及元丰后的吏部")


def entry1043():
    inspection_entry(1043, "户部、三司及司农寺等司")


def entry1044():
    inspection_entry(1044, "刑部、大理寺、审刑院等司")


def entry1045():
    inspection_entry(1045, "兵部、武学等司")


def entry1046():
    inspection_entry(1046, "礼部、太常寺等司")


def entry1047():
    inspection_entry(1047, "少府监、将作监及工部")


def entry1048():
    i, main = 1048, F[1048]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "御史台六察案", "机构",
        "北宋元丰六年六月一日",
        "吏察、户察、刑察、礼察、兵察、工察总称",
        SIX_INSPECTIONS, main,
        "原文明确六察案所指六个察案。",
    )
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "建立御史台六察案统称、六个正式察案实例及简称证据。")


def entry1049():
    i, main = 1049, F[1049]["text"]
    aliases = field(i, "别称")
    w, touched = W(i), set()
    _, early, _ = office_staff(
        w, touched, i, "御史台六察司", "察案御史",
        "北宋元丰七年以前（具体年月未载）", main,
        "元丰七年前察案御史由殿中侍御史、监察御史等御史充任。",
        quota=6, staff_type="六察官", office_event="六察各置察案御史一员",
        post_event="由殿中侍御史、监察御史等分领六察",
    )
    node(w, touched, i, "察案御史", "官职", "北宋元丰七年二月以后",
         "六察官改为监察御史，由监察御史分充察案御史",
         main, "六察差遣", "记录元丰七年后差充变化。", update_event=True)
    alias_note(w, i, early, aliases, "别称")
    finish(w, touched, "整理察案御史的六察司隶属、元丰前后差充变化、员额与别称。")


def entry1050():
    i, main = 1050, F[1050]["text"]
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "御史台", "御史台四推",
        "宋前期（具体年月未载）", main,
        "御史台四推是御史台所属台狱。",
        parent_event="设置台一推、台二推、殿一推、殿二推",
        child_event="御史台所属台狱，由三院御史轮治",
    )
    group = group_instances(
        w, touched, i, "御史台四推", "机构",
        "宋前期（具体年月未载）",
        "台一推、台二推、殿一推、殿二推的总称",
        ("台一推", "台二推", "殿一推", "殿二推"), main,
        "原文逐一列出四推。",
    )
    node(w, touched, i, "御史台四推", "机构", "北宋元丰新制",
         "罢推直官，御史台狱废置不常", main, "台狱",
         "记录元丰改制后的变化。", update_event=True)
    node(w, touched, i, "御史台四推", "机构", "南宋",
         "台狱久废，仅厅尚存", main, "废罢台狱",
         "记录南宋台狱久废。", update_event=True)
    alias_note(w, i, group, aliases, "简称与别名")
    finish(w, touched, "整理御史台四推的台狱性质、四个实例、三院御史轮治及元丰南宋变化。")


def entry1051():
    i, main = 1051, F[1051]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "推直官", "官职", "唐代", "唐朝始置",
         main, "台狱审讯官源流", "记录唐代职源。", update_event=True)
    _, post, _ = office_staff(
        w, touched, i, "御史台", "推直官", "宋初", main,
        "宋初御史台置推直官，掌纠按谳狱。",
        staff_type="台狱审讯官", office_event="设置四推推直官",
        post_event="掌御史台狱纠按谳狱",
    )
    node(w, touched, i, "推直官", "官职", "北宋元丰新制",
         "罢置", main, "废罢差遣", "记录元丰改制罢置。", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理推直官唐代源流、宋初御史台隶属、台狱职掌及元丰罢置。")


def entry1052():
    i, main = 1052, F[1052]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "御史台", "推勘官",
        "北宋淳化元年五月十七日", main,
        "淳化元年始置推勘官二十员。", quota=20,
        staff_type="赴外审狱官", office_event="始置推勘官二十员",
        post_event="乘传赴诸路州县大狱审理", officer="京朝官",
    )
    office_staff(
        w, touched, i, "御史台", "推勘官", "北宋咸平元年", main,
        "咸平元年推勘官改置十员。", quota=10,
        staff_type="赴外审狱官", office_event="改置推勘官十员",
        post_event="编制十员，赴外审理大狱", officer="京朝官",
    )
    node(w, touched, i, "推勘官", "官职",
         "北宋咸平元年以后（具体年月未载）", "后不复置",
         main, "废罢差遣", "记录咸平以后不复置。", update_event=True)
    finish(w, touched, "整理推勘官淳化始置、咸平减员、御史台隶属、差充职掌及后罢。")


def entry1053():
    i, main = 1053, F[1053]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "御史台", "御史台根勘所", "北宋元丰二年",
        main, "元丰二年乌台诗案时奉旨临时设置根勘所。",
        parent_event="奉旨设置根勘所",
        child_event="临时诏狱机构，根勘苏轼诗案",
    )
    node(w, touched, i, "御史台根勘所", "机构",
         "北宋元丰二年案结后（具体年月未载）", "事毕即罢",
         main, "临时机构废罢", "记录根勘所事毕即罢。", update_event=True)
    finish(w, touched, "整理御史台根勘所元丰二年临时设置、诏狱职掌及事毕即罢。")


def entry1054():
    i, main = 1054, F[1054]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, start, rid = office_staff(
        w, touched, i, "御史台", "御史台检法官", "北宋熙宁十年",
        origin, "熙宁十年御史台始置检法官一人。", "职源与沿革",
        quota=1, staff_type="检法官", office_event="始置检法官一人",
        post_event="始置，检照法律条文并供台官审察适用",
        grade="从八品",
    )
    cite(w, "Relationships", rid, i, roster, "补证检法官编制一人。", "编制")
    cite(w, "Timepoints", start, i, main, "补证职事官名及御史台隶属。")
    cite(w, "Timepoints", start, i, duty, "补证检法职掌。", "职掌")
    cite(w, "Timepoints", start, i, rank, "补证品位及班次。", "品位")
    node(w, touched, i, "御史台检法官", "官职", "南宋",
         "沿置", origin, "检法官", "记录南宋沿置。", "职源与沿革",
         grade="从八品", update_event=True)
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理御史台检法官熙宁始置、御史台隶属、职掌品位编制及南宋沿置。")


def entry1055():
    i, main = 1055, F[1055]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "御史台主簿", "官职", "汉代",
         "汉御史大夫寺曾辟署主簿", origin, "御史台属官源流",
         "记录汉代主簿源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "御史台主簿", "官职", "隋大业三年",
         "御史台主簿正式始置", origin, "御史台属官源流",
         "记录隋代始置。", "职源与沿革", update_event=True)
    _, early, rid = office_staff(
        w, touched, i, "御史台", "御史台主簿", "宋初", roster,
        "宋沿置御史台主簿一人。", "编制",
        quota=1, staff_type="主簿", office_event="设置主簿一人",
        post_event="掌台簿书、钱谷并参与推勘刑狱", grade="从七品下",
    )
    cite(w, "Relationships", rid, i, main, "补证主簿隶御史台。")
    cite(w, "Timepoints", early, i, duty, "补证文书钱谷及推勘职掌。", "职掌")
    cite(w, "Timepoints", early, i, rank, "补证宋初品位。", "品位")
    reform = node(
        w, touched, i, "御史台主簿", "官职", "北宋元丰新制",
        "改定从八品", rank, "御史台属官", "记录元丰改制品位。", "品位",
        grade="从八品", update_event=True,
    )
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "整理御史台主簿汉隋源流、宋代御史台隶属、职掌编制及元丰品位。")


def entry1056():
    i, main = 1056, F[1056]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "御史台五使", "官职",
        "宋前期（具体年月未载）",
        "朝会祭祀时临时差御史充任的五种使职总称",
        ("右巡使", "左巡使", "监祭使", "廊下使", "监香使"), main,
        "原文明确列举五使，且说明均非正式官职。",
    )
    node(w, touched, i, "御史台五使", "官职", "北宋元丰新制",
         "罢使名", main, "废罢差遣统称", "记录元丰改制罢五使名。",
         update_event=True)
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "建立御史台五使统称、五个临时差遣实例及元丰罢使名时间点。")


def temporary_envoy(i, title, officer, duty_event, aliases_field=None,
                     origin_field=None):
    main = F[i]["text"]
    w, touched = W(i), set()
    origin = field(i, origin_field) if origin_field else main
    if origin_field:
        node(w, touched, i, title, "官职", "唐代",
             f"唐代已有{title}相关差遣源流", origin, "临时使职源流",
             f"记录{title}唐代源流。", origin_field, update_event=True)
    _, post, _ = office_staff(
        w, touched, i, "御史台", title,
        "宋前期（具体年月未载）", origin,
        f"宋前期{title}由御史临时差充。", origin_field,
        staff_type="临时使职", office_event=f"临时差御史充{title}",
        post_event=duty_event, officer=officer,
    )
    if main != origin:
        cite(w, "Timepoints", post, i, main, f"补证{title}御史台隶属。")
    node(w, touched, i, title, "官职", "北宋元丰新制",
         "罢置", origin, "废罢差遣", f"记录元丰改制罢{title}。",
         origin_field, update_event=True)
    if aliases_field:
        alias_note(w, i, post, field(i, aliases_field), aliases_field)
    finish(w, touched, f"整理{title}唐宋源流、御史台隶属、差充职掌及元丰罢置。")


def entry1057():
    temporary_envoy(
        1057, "右巡使", "殿中侍御史",
        "朝会纠察文官仪制，并掌文官班簿、请假与禄料",
        aliases_field="简称", origin_field="职源与沿革",
    )


def entry1058():
    main = F[1058]["text"]
    aliases = field(1058, "简称")
    w, touched = W(1058), set()
    _, post, _ = office_staff(
        w, touched, 1058, "御史台", "左巡使",
        "宋前期（具体年月未载）", main,
        "左巡使与右巡使同属御史台临时差遣。",
        staff_type="临时使职", office_event="临时差御史充左巡使",
        post_event="朝会纠察武官仪制，并掌武官班簿、请假与禄料",
        officer="殿中侍御史",
    )
    node(w, touched, 1058, "左巡使", "官职", "北宋元丰新制",
         "罢置", main, "废罢差遣", "依右巡使同条沿革记录元丰罢置。",
         update_event=True)
    alias_note(w, 1058, post, aliases, "简称")
    finish(w, touched, "整理左巡使御史台隶属、武官纠察职掌、差充及元丰罢置。")


def entry1059():
    temporary_envoy(
        1059, "监祭使", "监察御史",
        "祭祀大礼时检视受誓戒、致斋及有无出缺不敬",
        aliases_field="简称", origin_field="职源与沿革",
    )


def entry1060():
    main = F[1060]["text"]
    w, touched = W(1060), set()
    _, post, _ = office_staff(
        w, touched, 1060, "御史台", "廊下使",
        "宋前期（具体年月未载）", main,
        "宋前期廊下使由御史临时差充。",
        staff_type="临时使职", office_event="临时差御史充廊下使",
        post_event="后殿坐朝或廊下赐食时监食", officer="御史",
    )
    node(w, touched, 1060, "廊下使", "官职", "北宋元丰新制",
         "罢置", main, "废罢差遣", "记录元丰改制罢置。", update_event=True)
    assert post
    finish(w, touched, "整理廊下使御史台隶属、监食职掌、御史差充及元丰罢置。")


def main():
    for i in range(1041, 1061):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
