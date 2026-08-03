#!/usr/bin/env python3
"""提取 chapter5t7 第1021-1040条：御史台三院及其主要台官。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1001_1020 as previous


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


F = {i: load(i) for i in range(1021, 1041)}
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
evolution = previous.evolution
group_instances = previous.group_instances


TIME_HINTS = {
    "西汉武帝时": -140,
    "三国魏": 230,
    "隋开皇三年": 583,
    "唐贞观初": 627,
    "唐武则天时": 690,
    "唐元和二年": 807,
    "唐代": 800,
    "宋代": 959,
    "宋初": 960,
    "北宋太平兴国三年": 978,
    "北宋大中祥符五年": 1012,
    "北宋天禧元年二月八日": 1017.1,
    "北宋天禧元年以后（具体年月未载）": 1025,
    "北宋景祐元年四月二十四日": 1034.3,
    "北宋庆历五年正月十八日": 1045.05,
    "宋前期（具体年月未载）": 1070,
    "北宋元丰七年以前（具体年月未载）": 1070.1,
    "北宋元丰新制": 1082.1,
    "北宋元丰七年二月十七日": 1084.13,
    "北宋元丰七年以后": 1084.2,
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


def entry1021():
    i, main = 1021, F[1021]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "侍御史知杂事", "官职", "唐元和二年",
         "唐代由资格最深的侍御史一人兼知杂事", origin,
         "御史台副贰源流", "记录唐代侍御史兼知杂事旧制。", "职源与沿革",
         update_event=True)
    _, post, rid = office_staff(
        w, touched, i, "御史台", "侍御史知杂事",
        "宋前期（具体年月未载）", roster,
        "宋前期侍御史知杂事编制一人。", "编制",
        quota=1, staff_type="副台长",
        office_event="设置侍御史知杂事一人",
        post_event="御史台副长官，专掌台务，中丞阙则代判台事",
        officer="郎中、员外郎资格人", grade="从六品下，特赐五品服",
    )
    cite(w, "Relationships", rid, i, duty, "补证其为御史台副长官。", "职掌")
    cite(w, "Timepoints", post, i, duty, "补证专掌台务及中丞阙时代判台事。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证位次、差充资格及服色。", "品位")
    abolished = node(
        w, touched, i, "侍御史知杂事", "官职",
        "北宋元丰七年二月十七日", "罢兼知杂事，职名并入侍御史",
        origin, "废罢差遣", "记录元丰七年罢兼知杂事。", "职源与沿革",
        update_event=True,
    )
    evolution(
        w, touched, i, "侍御史知杂事", "侍御史",
        "北宋元丰七年二月十七日", origin,
        "元丰七年罢侍御史兼知杂事，改为侍御史。", "职源与沿革",
        source_type="官职", target_type="官职",
        source_event="罢兼知杂事", target_event="升为御史台副贰",
    )
    alias_note(w, i, post, aliases, "简称与别名")
    assert main and abolished
    finish(w, touched, "整理侍御史知杂事唐宋源流、御史台副贰编制、职掌品位及元丰改称。")


def entry1022():
    i, main = 1022, F[1022]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "丞杂", "官职",
        "北宋元丰七年以前（具体年月未载）",
        "御史中丞与侍御史知杂事的连称",
        ("御史中丞", "侍御史知杂事"), main,
        "原文明确丞杂是二官连称，元丰七年以后旧制已罢。",
    )
    finish(w, touched, "建立丞杂统称及御史中丞、侍御史知杂事两个实例。")


def entry1023():
    i, main = 1023, F[1023]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "御史台三院", "机构", "唐代",
         "台院、殿院、察院三院之名始见", main, "机构统称",
         "记录三院之名始于唐。", update_event=True)
    group = group_instances(
        w, touched, i, "御史台三院", "机构", "宋代",
        "台院、殿院、察院的连称",
        ("台院", "殿院", "察院"), main,
        "原文逐一说明三院及各院所隶御史。",
    )
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "建立御史台三院统称、唐代源流及台院殿院察院三个实例。")


def entry1024():
    i, main = 1024, F[1024]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "御史台", "判御史台三院事",
        "北宋开宝六年十月", main,
        "太祖朝判御史台三院事领三院御史事务。",
        staff_type="兼领三院官", office_event="曾置判三院事",
        post_event="领台院、殿院、察院御史事务",
    )
    finish(w, touched, "建立判御史台三院事的太祖朝设置、御史台隶属与职掌。")


def entry1025():
    i, main = 1025, F[1025]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "三院御史", "官职", "宋前期（具体年月未载）",
        "侍御史、殿中侍御史、监察御史合称，编制四至六人",
        ("侍御史", "殿中侍御史", "监察御史"), main,
        "原文明确三类御史因分隶三院而合称三院御史。",
    )
    finish(w, touched, "建立三院御史统称、三个正式台官实例及共同弹劾言事职掌。")


def entry1026():
    i, main = 1026, F[1026]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "台院", "机构", "唐代", "唐代已有台院之称",
         main, "御史台属院源流", "记录台院唐代源流。", update_event=True)
    parent_child(
        w, touched, i, "御史台", "台院", "宋代", main,
        "台院隶御史台。", parent_event="下辖台院",
        child_event="隶御史台，为侍御史公廨",
    )
    office_staff(
        w, touched, i, "台院", "侍御史", "宋代", main,
        "台院为侍御史所属公廨。", staff_type="所属台官",
        office_event="为侍御史公廨", post_event="隶台院",
    )
    finish(w, touched, "整理台院唐代源流、御史台隶属及侍御史所属关系。")


def entry1027():
    i, main = 1027, F[1027]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "侍御史", "官职", "西汉武帝时", "始置侍御史",
         origin, "前代御史源流", "记录侍御史始置。", "职源与沿革",
         update_event=True)
    node(w, touched, i, "侍御史", "官职", "宋初",
         "宋沿置，依唐制从六品下", rank, "御史台台官",
         "记录宋初品位。", "品位", grade="从六品下", update_event=True)
    node(w, touched, i, "侍御史", "官职", "北宋大中祥符五年",
         "定有专职在台弹纠并参与推勘台狱", duty, "台院御史",
         "记录大中祥符五年专职化。", "职掌", update_event=True)
    reform = node(
        w, touched, i, "侍御史", "官职", "北宋元丰七年二月十七日",
        "由侍御史知杂事正名，升为御史台副贰", duty, "御史台副长官",
        "记录元丰七年职掌变化。", "职掌", grade="从六品",
        update_event=True,
    )
    _, _, rid = office_staff(
        w, touched, i, "台院", "侍御史", "宋代", roster,
        "侍御史隶台院，编制一人。", "编制",
        quota=1, staff_type="台院御史", office_event="设置侍御史一人",
        post_event="隶台院，编制一人",
    )
    cite(w, "Relationships", rid, i, main, "补证侍御史隶御史台台院。")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后品位及台内位次。", "品位")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理侍御史汉代源流、宋初品位、祥符专职、元丰副贰及台院编制。")


def entry1028():
    i, main = 1028, F[1028]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "殿院", "机构", "唐代", "唐代已有殿院之称",
         main, "御史台属院源流", "记录殿院唐代源流。", update_event=True)
    parent_child(
        w, touched, i, "御史台", "殿院", "宋代", main,
        "殿院隶御史台。", parent_event="下辖殿院",
        child_event="隶御史台，为殿中侍御史公廨",
    )
    office_staff(
        w, touched, i, "殿院", "殿中侍御史", "宋代", main,
        "殿院为殿中侍御史所属公廨。", staff_type="所属台官",
        office_event="为殿中侍御史公廨", post_event="隶殿院",
    )
    finish(w, touched, "整理殿院唐代源流、御史台隶属及殿中侍御史所属关系。")


def entry1029():
    i, main = 1029, F[1029]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "殿中侍御史", "官职", "三国魏",
         "兰台遣二御史居殿中伺察非法，为本官之始", origin,
         "前代御史源流", "记录殿中侍御史职源。", "职源与沿革",
         update_event=True)
    node(w, touched, i, "殿中侍御史", "官职", "宋初",
         "宋沿置，依唐制从七品下", rank, "殿院御史",
         "记录宋初品位。", "品位", grade="从七品下", update_event=True)
    node(w, touched, i, "殿中侍御史", "官职", "北宋大中祥符五年",
         "定有专职在台弹纠、推勘台狱并分纠朝会礼仪", duty,
         "殿院御史", "记录大中祥符五年专职化。", "职掌",
         update_event=True)
    reform = node(
        w, touched, i, "殿中侍御史", "官职",
        "北宋元丰七年二月十七日",
        "兼领原言事御史之职，掌言事、察事及朝会班序",
        duty, "殿院御史", "记录元丰七年职掌变化。", "职掌",
        grade="正七品", update_event=True,
    )
    _, _, rid = office_staff(
        w, touched, i, "殿院", "殿中侍御史", "北宋元丰新制", roster,
        "元丰新制殿中侍御史二人。", "编制",
        quota=2, staff_type="殿院御史", office_event="设置殿中侍御史二人",
        post_event="隶殿院，编制二人", grade="正七品",
    )
    cite(w, "Relationships", rid, i, main, "补证殿中侍御史隶御史台殿院。")
    cite(w, "Timepoints", reform, i, rank, "补证元丰品位及班次。", "品位")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理殿中侍御史魏代源流、宋初品位、祥符专职、元丰职掌编制及别称。")


def entry1030():
    i, main = 1030, F[1030]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "殿中侍御史里行", "官职", "唐武则天时",
         "唐御史台已有殿中里行", origin, "御史里行源流",
         "记录唐代职源。", "职源与沿革", update_event=True)
    _, start, _ = office_staff(
        w, touched, i, "殿院", "殿中侍御史里行",
        "北宋景祐元年四月二十四日", main,
        "景祐元年始置殿中侍御史里行，隶御史台殿院。",
        staff_type="实习御史", office_event="始置殿中侍御史里行",
        post_event="始置，职掌同殿中侍御史",
        officer="曾任知县的三丞以上京官",
    )
    cite(w, "Timepoints", start, i, origin, "补证景祐始置年月。", "职源与沿革")
    cite(w, "Timepoints", start, i, duty, "补证职掌同殿中侍御史。", "职掌")
    cite(w, "Timepoints", start, i, rank, "补证里行的实习性质与差充资格。", "品位")
    node(w, touched, i, "殿中侍御史里行", "官职", "北宋元丰新制",
         "罢置", origin, "废罢差遣", "记录元丰新制罢置。", "职源与沿革",
         update_event=True)
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理殿中侍御史里行唐代源流、景祐始置、殿院隶属、资格职掌及元丰罢置。")


def entry1031():
    i, main = 1031, F[1031]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    _, start, _ = office_staff(
        w, touched, i, "御史台", "言事御史",
        "北宋天禧元年二月八日", main,
        "天禧元年始置言事御史，隶御史台。",
        staff_type="言事台官", office_event="始置言事御史",
        post_event="始置，专任言事，使台官兼谏职",
    )
    cite(w, "Timepoints", start, i, origin, "补证天禧始置及后续罢复。", "职源与沿革")
    cite(w, "Timepoints", start, i, duty, "补证台官由此兼谏职。", "职掌")
    node(w, touched, i, "言事御史", "官职",
         "北宋天禧元年以后（具体年月未载）", "其后不置",
         origin, "废罢差遣", "记录天禧后曾停置。", "职源与沿革",
         update_event=True)
    _, restored, rid = office_staff(
        w, touched, i, "御史台", "言事御史",
        "北宋庆历五年正月十八日", roster,
        "庆历五年复置言事御史，旧额二员而通常只除一员。", "编制",
        quota=1, staff_type="言事台官（旧额二员）",
        office_event="复置言事御史",
        post_event="复置，通常实除一员",
    )
    cite(w, "Relationships", rid, i, origin, "补证庆历五年复置。", "职源与沿革")
    cite(w, "Timepoints", restored, i, rank, "补证品位约同两院御史。", "品位")
    node(w, touched, i, "言事御史", "官职",
         "北宋元丰七年二月十七日", "罢置，言责归殿中侍御史",
         origin, "废罢差遣", "记录元丰七年罢置。", "职源与沿革",
         update_event=True)
    evolution(
        w, touched, i, "言事御史", "殿中侍御史",
        "北宋元丰七年二月十七日", origin,
        "元丰七年罢言事御史，其言责归殿中侍御史。", "职源与沿革",
        source_type="官职", target_type="官职",
        source_event="罢置", target_event="接收言事御史言责",
    )
    alias_note(w, i, start, aliases, "简称与别名")
    finish(w, touched, "整理言事御史天禧始置、停置、庆历复置、编制职掌及元丰归并。")


def entry1032():
    i, main = 1032, F[1032]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "察院", "机构", "唐代", "唐代已有察院之称",
         main, "御史台属院源流", "记录察院唐代源流。", update_event=True)
    _, child = parent_child(
        w, touched, i, "御史台", "察院", "宋代", main,
        "察院隶御史台。", parent_event="下辖察院",
        child_event="隶御史台，为监察御史公廨，下辖院杂司及一司四房",
    )
    cite(w, "Timepoints", child, i, main,
         "记录察院下辖院杂司、兵房、吏房、户房、礼房及其吏额。")
    finish(w, touched, "整理察院唐代源流、御史台隶属、监察御史公廨性质及一司四房编制。")


def simple_chayuan_clerk(i, title, event, staff_type, quota=None):
    main = F[i]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "察院", title, "宋代", main,
        f"{title}隶察院并{event}。", quota=quota, staff_type=staff_type,
        office_event=f"设置{title}", post_event=event,
    )
    finish(w, touched, f"整理{title}的察院隶属、吏职性质、员额与行遣职掌。")


def entry1033():
    simple_chayuan_clerk(1033, "察院都承旨", "总管本院行遣公事", "总管吏")


def entry1034():
    simple_chayuan_clerk(1034, "察院副都承旨", "佐都承旨管察院行遣公事", "佐贰吏")


def entry1035():
    simple_chayuan_clerk(1035, "察院承旨", "分管察院一司四房行遣公事", "承旨吏")


def entry1036():
    simple_chayuan_clerk(
        1036, "察院逐房副承旨", "分隶兵、吏、户、礼四房主行遣公事",
        "逐房副承旨", quota=4,
    )


def entry1037():
    i, main = 1037, F[1037]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "监察御史", "官职", "秦",
         "监御史为监察御史名称源流", origin, "前代御史源流",
         "记录秦代名称源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "监察御史", "官职", "隋开皇三年",
         "改检校御史为监察御史，正称始此", origin, "前代御史源流",
         "记录监察御史正称始置。", "职源与沿革", update_event=True)
    node(w, touched, i, "监察御史", "官职", "宋初",
         "宋沿置，依唐制正八品上", rank, "察院御史",
         "记录宋初品位。", "品位", grade="正八品上", update_event=True)
    node(w, touched, i, "监察御史", "官职", "北宋太平兴国三年",
         "置专职在台弹劾并兼监祭使，三院御史自此正名", duty,
         "察院御史", "记录太平兴国三年专职化。", "职掌",
         update_event=True)
    _, reform, rid = office_staff(
        w, touched, i, "察院", "监察御史",
        "北宋元丰七年二月十七日", roster,
        "元丰新制定监察御史六人。", "编制",
        quota=6, staff_type="察院御史", office_event="设置监察御史六人",
        post_event="领六察，分察六部以下百司并许言事",
        grade="从七品",
    )
    cite(w, "Relationships", rid, i, main, "补证监察御史隶御史台察院。")
    cite(w, "Timepoints", reform, i, duty, "补证元丰七年后六察职掌。", "职掌")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从七品及位次。", "品位")
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "整理监察御史秦隋源流、宋初品位、太平兴国专职及元丰六察编制职掌。")


def entry1038():
    i, main = 1038, F[1038]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "监察御史里行", "官职", "唐贞观初",
         "唐太宗以布衣马周为监察御史里行，为御史里行之始",
         origin, "御史里行源流", "记录唐代职源。", "职源与沿革",
         update_event=True)
    _, start, _ = office_staff(
        w, touched, i, "察院", "监察御史里行",
        "北宋景祐元年四月二十四日", main,
        "景祐元年始置监察御史里行，隶御史台察院。",
        staff_type="实习御史", office_event="始置监察御史里行",
        post_event="始置，职掌同监察御史",
        officer="曾任知县的三丞以上京官",
    )
    cite(w, "Timepoints", start, i, origin, "补证景祐始置年月。", "职源与沿革")
    cite(w, "Timepoints", start, i, duty, "补证职掌同监察御史。", "职掌")
    cite(w, "Timepoints", start, i, rank, "补证里行资格条件与实习性质。", "品位")
    node(w, touched, i, "监察御史里行", "官职", "北宋元丰新制",
         "罢置", origin, "废罢差遣", "记录元丰改制罢置。", "职源与沿革",
         update_event=True)
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理监察御史里行唐代源流、景祐始置、察院隶属、资格职掌及元丰罢置。")


def entry1039():
    i, main = 1039, F[1039]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "察院", "权监察御史里行",
        "宋前期（具体年月未载）", main,
        "资格不及三丞而入察院为御史里行者带权字。",
        staff_type="权御史里行", office_event="可置权监察御史里行",
        post_event="资格不及三丞而权充监察御史里行",
        officer="三丞以下京官，如太子中允",
    )
    finish(w, touched, "整理权监察御史里行的察院隶属、带权条件及差充资格。")


def entry1040():
    i, main = 1040, F[1040]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "两院御史", "官职", "宋代",
        "殿中侍御史、监察御史总名",
        ("殿中侍御史", "监察御史"), main,
        "《御史台令》明确两院御史所指二官。",
    )
    finish(w, touched, "建立两院御史统称及殿中侍御史、监察御史两个正式实例。")


def main():
    for i in range(1021, 1041):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
