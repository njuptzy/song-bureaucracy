#!/usr/bin/env python3
"""提取 chapter5t7 第1381-1400条：阁门诸职与四方馆。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1361_1380 as previous


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


F = {i: load(i) for i in range(1381, 1401)}
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
    "东晋": 317,
    "南朝陈": 560,
    "唐代": 700,
    "唐中期": 850,
    "五代十国": 930,
    "宋初": 960,
    "北宋乾德五年四月": 967.3,
    "北宋真宗刘皇后时": 1020,
    "北宋咸平四年七月五日": 1001.51,
    "北宋天禧二年十二月": 1018.95,
    "北宋仁宗明道间": 1032,
    "北宋淳化四年": 993,
    "北宋嘉祐三年": 1058,
    "北宋熙宁间": 1070,
    "北宋元丰官制": 1080,
    "北宋元丰五年": 1082,
    "北宋政和二年九月二十五日": 1112.72,
    "北宋政和二年十一月六日": 1112.84,
    "北宋政和六年七月二日": 1116.51,
    "北宋政和六年八月二日": 1116.59,
    "北宋靖康元年五月": 1126.4,
    "南宋建炎元年十二月二十一日": 1127.96,
    "南宋初至绍兴五年六月九日": 1132,
    "南宋绍兴五年六月九日": 1135.43,
    "南宋绍兴间": 1145,
    "南宋乾道六年八月": 1170.6,
    "宋代（具体年月未载）": 1100.1,
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
              decision, field_name=None, *, entity_type="官职",
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


def office_child(w, touched, i, parent_title, child_title, time, quotation,
                 decision, field_name=None, *, parent_event=None,
                 child_event=None):
    parent = node(
        w, touched, i, parent_title, "机构", time,
        parent_event or f"统辖{child_title}", quotation, "上级机构",
        f"建立或复用{parent_title}同期节点。", field_name,
    )
    child = node(
        w, touched, i, child_title, "机构", time,
        child_event or f"隶属{parent_title}", quotation, "所属机构",
        f"建立或复用{child_title}同期节点。", field_name,
    )
    relation(w, i, parent, child, "上下级机构", quotation, decision, field_name)
    return parent, child


def canonicalize_four_directions(w, quotation):
    old = w.find_entity("四方馆司", "机构")
    formal = w.find_entity("四方馆", "机构")
    if old is not None:
        assert formal is None or formal == old, (old, formal)
        w.conn.execute(
            "update Entities set title='四方馆',quotation=? where id=?",
            (quotation, old),
        )
        w._br(
            "Entities", old,
            "据正式辞典词头‘四方馆’规范上一批由横行五司原文‘四方馆司’"
            "建立的同一机构名称，保留既有关系与证据。",
        )
        formal = old
    assert formal is not None
    return formal


def entry1381():
    i, main = 1381, F[1381]["text"]
    origin, duty = field(i, "职源"), field(i, "职掌")
    rank, aliases = field(i, "品位"), field(i, "简称与别名")
    w, touched = W(i), set()
    office, post, _ = office_staff(
        w, touched, i, "阁门", F[i]["title"], "南宋乾道六年八月",
        origin, "乾道六年始置阁门舍人，隶阁门。", "职源",
        staff_type="阁职",
        office_event="创置阁门舍人", post_event="始置，专掌觉察诸殿失仪",
    )
    cite(w, "Timepoints", post, i, duty,
         "保存觉察失仪、侍立、导引亲王及武举储材职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank,
         "保存班位、武臣清选和十年补外制度。", "品位")
    group = node(
        w, touched, i, "阁职", "官职", "南宋乾道六年八月",
        "阁门舍人、宣赞舍人、祗候等武臣清选", origin, "阁职统称",
        "复用乾道六年阁职节点。", "职源",
    )
    relation(w, i, group, post, "统称与实例", origin,
             "阁门舍人是乾道六年创置的阁职。", "职源")
    staff(w, i, office, post, aliases, "乾道六年阁门舍人定员十。",
          "简称与别名", quota="十员", staff_type="阁职")
    alias_note(w, i, post, aliases, "简称与别名")
    assert office
    finish(w, touched, "整理阁门舍人始置、编制隶属、阁职实例、职掌品位与别名。")


def entry1382():
    i, main = 1382, F[1382]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster = field(i, "品位"), field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    combined = node(
        w, touched, i, "通事舍人兼阁门祗候", "官职", "宋初",
        "沿唐制由中书省通事舍人赴阁门祗应", origin, "阁门祗应兼官",
        "记录宋初阁门祗候前身。", "职源与沿革", update_event=True,
    )
    _, post = evolution(
        w, touched, i, "通事舍人兼阁门祗候", F[i]["title"],
        "北宋咸平四年七月五日", origin,
        "咸平四年直除阁门通事舍人后，阁门祗候分为独立一职。",
        "职源与沿革", source_event="分为阁门通事舍人、阁门祗候二职",
        target_event="与阁门通事舍人分为二职",
    )
    office = node(
        w, touched, i, "阁门", "机构", "北宋咸平四年七月五日",
        "设置独立阁门祗候", origin, "阁门机构",
        "建立阁门咸平四年节点。", "职源与沿革",
    )
    staff(w, i, office, post, origin, "阁门祗候在阁门供职。", "职源与沿革",
          staff_type="阁职")
    cite(w, "Timepoints", post, i, duty, "保存传宣、赞谒、侍卫班列及外任带职。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存从八品、大使臣和武臣清选品位。", "品位")
    for time, event, quota in (
        ("北宋熙宁间", "员额二十三员", "二十三员"),
        ("北宋元丰官制", "定员十二员", "十二员"),
        ("北宋靖康元年五月", "员额曾达七十六员", "七十六员"),
    ):
        office_staff(
            w, touched, i, "阁门", F[i]["title"], time, roster,
            f"{time}{event}。", "编制", quota=quota, staff_type="阁职",
            office_event=f"编制阁门祗候{quota}", post_event=event,
        )
    south = node(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "南宋沿置", origin, "阁职", "记录南宋沿置。", "职源与沿革",
        update_event=True,
    )
    alias_note(w, i, south, aliases, "简称与别名")
    assert combined
    finish(w, touched, "整理阁门祗候前身、咸平分职、职掌品位、分期员额与南宋沿置。")


def entry1383():
    i, main, aliases = 1383, F[1383]["text"], field(1383, "简称与别名")
    w, touched = W(i), set()
    _, post = evolution(
        w, touched, i, "阁门通事舍人", F[i]["title"],
        "北宋政和六年八月二日", main,
        "政和六年八月二日阁门通事舍人改名阁门宣赞舍人。",
        source_event="改名阁门宣赞舍人",
        target_event="由阁门通事舍人改名",
    )
    office = node(
        w, touched, i, "阁门", "机构", "北宋政和六年八月二日",
        "设置阁门宣赞舍人", main, "阁门机构",
        "建立阁门政和六年节点。",
    )
    staff(w, i, office, post, main, "阁门宣赞舍人在阁门供职。",
          staff_type="阁职")
    south = node(
        w, touched, i, F[i]["title"], "官职", "南宋绍兴间",
        "定员四十，注授内外差遣赴任即免阁门供职", main, "阁职",
        "记录绍兴间员额和离职规则。", update_event=True,
    )
    south_office = node(
        w, touched, i, "阁门", "机构", "南宋绍兴间",
        "编制阁门宣赞舍人四十员", main, "阁门机构",
        "建立阁门绍兴间编制节点。",
    )
    staff(w, i, south_office, south, main,
          "绍兴间阁门宣赞舍人定员四十。",
          quota="四十员", staff_type="阁职")
    alias_note(w, i, south, aliases, "简称与别名")
    finish(w, touched, "整理阁门宣赞舍人政和改名、阁门隶属、绍兴员额与别名。")


def entry1384():
    i, main, aliases = 1384, F[1384]["text"], field(1384, "简称")
    w, touched = W(i), set()
    _, taboo = evolution(
        w, touched, i, "阁门通事舍人", F[i]["title"],
        "北宋真宗刘皇后时", main,
        "因刘皇后父名通避讳，阁门通事舍人改称阁门宣事舍人。",
        source_event="因避讳改称阁门宣事舍人",
        target_event="避讳称",
    )
    evolution(
        w, touched, i, F[i]["title"], "阁门通事舍人",
        "北宋仁宗明道间", main,
        "仁宗明道间阁门宣事舍人恢复旧称阁门通事舍人。",
        source_event="复旧称阁门通事舍人",
        target_event="恢复旧称",
    )
    alias_note(w, i, taboo, aliases, "简称")
    finish(w, touched, "整理阁门宣事舍人的避讳改称、明道复旧与简称。")


def entry1385():
    i, main = 1385, F[1385]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster = field(i, "品位"), field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    early = node(
        w, touched, i, F[i]["title"], "官职", "北宋乾德五年四月",
        "始见名目，仍沿唐制由中书省通事舍人赴阁门", origin, "阁职",
        "记录乾德五年始见阁门通事舍人。", "职源与沿革",
        update_event=True,
    )
    direct = node(
        w, touched, i, F[i]["title"], "官职", "北宋咸平四年七月五日",
        "始直授，与阁门祗候分为二职", origin, "阁职",
        "记录咸平四年直授。", "职源与沿革", update_event=True,
    )
    office = node(
        w, touched, i, "阁门", "机构", "北宋咸平四年七月五日",
        "直授阁门通事舍人", origin, "阁门机构",
        "建立阁门咸平四年承载节点。", "职源与沿革",
    )
    staff(w, i, office, direct, origin, "阁门通事舍人在阁门供职。",
          staff_type="阁职")
    titled = node(
        w, touched, i, F[i]["title"], "官职", "北宋天禧二年十二月",
        "仪制图与告命止称通事舍人，去阁门二字", origin, "阁职",
        "记录天禧二年制授称谓。", "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", direct, i, duty,
         "保存在京宣传赞谒、察觉失仪及外任带职职掌。", "职掌")
    cite(w, "Timepoints", direct, i, rank,
         "保存从七品及武臣清选品位。", "品位")
    office_staff(
        w, touched, i, "阁门", F[i]["title"], "北宋元丰五年", roster,
        "元丰五年阁门通事舍人定员十员。", "编制",
        quota="十员", staff_type="阁职", office_event="编制通事舍人十员",
        post_event="定员十员",
    )
    evolution(
        w, touched, i, F[i]["title"], "阁门宣赞舍人",
        "北宋政和六年七月二日", origin,
        "政和六年七月二日阁门通事舍人改为阁门宣赞舍人。",
        "职源与沿革", source_event="改为阁门宣赞舍人",
        target_event="由阁门通事舍人改名",
    )
    _, renamed, _ = office_staff(
        w, touched, i, "阁门", "阁门宣赞舍人", "北宋靖康元年五月",
        roster, "靖康元年五月宣赞舍人由一百零八员定为十员。", "编制",
        quota="十员", staff_type="阁职", office_event="裁定宣赞舍人十员",
        post_event="此前溢至一百零八员，五月定为十员",
    )
    alias_note(w, i, titled, aliases, "简称与别名")
    cite(w, "Timepoints", renamed, i, roster, "保存政宣溢员和靖康裁定。", "编制")
    assert early
    finish(w, touched, "整理阁门通事舍人始见、直授、称谓、职掌品位、员额和政和改名。")


def entry1386():
    i, main, aliases = 1386, F[1386]["text"], field(1386, "简称与别名")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "阁门主管官", "官职", "南宋初至绍兴五年六月九日",
        "主管阁门公事、同主管阁门公事的统称",
        ("主管阁门公事", F[i]["title"]), main,
        "主管官置二员以上时，同置者带同字。",
    )
    _, post, _ = office_staff(
        w, touched, i, "阁门", F[i]["title"],
        "南宋初至绍兴五年六月九日", main,
        "同主管阁门公事为南宋初阁门主管官。",
        staff_type="阁门主管官", office_event="置同主管阁门公事",
        post_event="主管官二员以上时带同字",
    )
    alias_note(w, i, post, aliases, "简称与别名")
    assert group
    finish(w, touched, "整理同主管阁门公事的同置规则、阁门隶属、统称实例与别名。")


def entry1387():
    i, main = 1387, F[1387]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "阁门", F[i]["title"],
        "南宋初至绍兴五年六月九日", main,
        "主管阁门公事为南宋初领阁门事称谓。",
        staff_type="阁门主管官", office_event="置主管阁门公事",
        post_event="南宋初领阁门事",
    )
    ended = node(
        w, touched, i, F[i]["title"], "官职", "南宋绍兴五年六月九日",
        "此后不复使用主管称谓", main, "阁门主管官",
        "记录绍兴五年停用称谓。", update_event=True,
    )
    cite(w, "Timepoints", post, i, main, "保存主管称谓使用时段。")
    cite(w, "Timepoints", ended, i, main, "保存绍兴五年停用时间。")
    finish(w, touched, "整理主管阁门公事南宋初使用和绍兴五年停用。")


def entry1388():
    i, main, aliases = 1388, F[1388]["text"], field(1388, "简称与别名")
    w, touched = W(i), set()
    canonicalize_four_directions(w, main)
    predecessor, post = evolution(
        w, touched, i, "东、西上阁门副使", F[i]["title"],
        "南宋绍兴五年六月九日", main,
        "同知阁门事即旧阁门副使之职。",
        source_event="旧职转为同知阁门事",
        target_event="武阶未及右武大夫者领阁门事，同兼客省、四方馆事",
    )
    for office_title in ("阁门", "客省司", "四方馆"):
        office = node(
            w, touched, i, office_title, "机构", "南宋绍兴五年六月九日",
            f"由{F[i]['title']}兼领", main, "阁门关联机构",
            f"建立{office_title}同期节点。",
        )
        staff(w, i, office, post, main,
              f"同知阁门事同兼{office_title}事。", staff_type="兼领官")
    alias_note(w, i, post, aliases, "简称与别名")
    assert predecessor
    finish(w, touched, "整理同知阁门事绍兴定名、旧副使演变、三机构兼领与别名。")


def entry1389():
    i, main, aliases = 1389, F[1389]["text"], field(1389, "简称与别名")
    w, touched = W(i), set()
    canonicalize_four_directions(w, main)
    east = node(
        w, touched, i, "东上阁门司", "机构", "南宋建炎元年十二月二十一日",
        "与西上阁门司合并", main, "演变前",
        "建立东上阁门司合并节点。", update_event=True,
    )
    west = node(
        w, touched, i, "西上阁门司", "机构", "南宋建炎元年十二月二十一日",
        "与东上阁门司合并", main, "演变前",
        "建立西上阁门司合并节点。", update_event=True,
    )
    gate = node(
        w, touched, i, "阁门", "机构", "南宋建炎元年十二月二十一日",
        "东、西上阁门司合并为阁门", main, "演变后",
        "建立合并后的阁门节点。", update_event=True,
    )
    relation(w, i, east, gate, "前后演变", main,
             "建炎元年东上阁门司并入阁门。")
    relation(w, i, west, gate, "前后演变", main,
             "建炎元年西上阁门司并入阁门。")
    _, head, _ = office_staff(
        w, touched, i, "阁门", F[i]["title"],
        "南宋建炎元年十二月二十一日", main,
        "合并后阁门长官总名知阁门事。", staff_type="阁门长官",
        office_event="合并并设置知阁门事", post_event="阁门司长官总名",
    )
    for office_title in ("客省司", "四方馆"):
        office = node(
            w, touched, i, office_title, "机构", "南宋绍兴五年六月九日",
            f"由{F[i]['title']}兼知", main, "阁门关联机构",
            f"建立{office_title}同期节点。",
        )
        post = node(
            w, touched, i, F[i]["title"], "官职", "南宋绍兴五年六月九日",
            "右武大夫以上称知阁门事，兼知客省、四方馆事", main,
            "阁门长官", "建立知阁门事绍兴五年节点。", update_event=True,
        )
        staff(w, i, office, post, main, f"知阁门事兼知{office_title}事。",
              staff_type="兼知官")
    alias_note(w, i, head, aliases, "简称与别名")
    finish(w, touched, "整理建炎阁门合并、知阁门事长官设置、绍兴兼知与别名。")


def entry1390():
    i, main, aliases = 1390, F[1390]["text"], field(1390, "简称与别名")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, F[i]["title"], "官职",
        "北宋政和二年十一月六日",
        "知东上阁门事、知西上阁门事的合称，编制共四员",
        ("知东上阁门事", "知西上阁门事"), main,
        "正文明确知东、西上阁门事两种实例。",
    )
    for office_title, post_title in (
        ("东上阁门司", "知东上阁门事"),
        ("西上阁门司", "知西上阁门事"),
    ):
        office_staff(
            w, touched, i, office_title, post_title,
            "北宋政和二年十一月六日", main,
            f"{post_title}由内外官兼领{office_title}事。",
            quota="二员", staff_type="知阁门事",
            office_event=f"设置{post_title}二员", post_event="由内外官兼领",
        )
    cite(w, "Timepoints", group, i, main, "保存合计四员（东二、西二）的编制。")
    alias_note(w, i, group, aliases, "简称与别名")
    finish(w, touched, "整理知东、西上阁门事政和设置、两个实例、分司隶属和四员编制。")


def entry1391():
    i, main = 1391, F[1391]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职能")
    rank, aliases = field(i, "品位"), field(i, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, F[i]["title"], "官职", "北宋",
        "东上阁门副使、西上阁门副使的合称",
        ("东上阁门副使", "西上阁门副使"), main,
        "正式词头直接合称东、西上阁门副使。",
    )
    for office_title, post_title in (
        ("东上阁门司", "东上阁门副使"),
        ("西上阁门司", "西上阁门副使"),
    ):
        _, post, _ = office_staff(
            w, touched, i, office_title, post_title, "北宋", origin,
            f"{post_title}佐正使领本司公事。", "职源与沿革",
            staff_type="阁门副使", office_event=f"设置{post_title}",
            post_event="佐正使领本司公事及承旨禀命",
        )
        cite(w, "Timepoints", post, i, duty, "保存本司佐职和横行武阶迁转。", "职能")
        cite(w, "Timepoints", post, i, rank, "保存宋前期与元丰品位。", "品位")
    evolution(
        w, touched, i, "东上阁门副使", "左武郎",
        "北宋政和二年九月二十五日", origin,
        "政和二年东上阁门副使武阶易为左武郎。", "职源与沿革",
        source_event="武阶易为左武郎", target_event="承接东上阁门副使武阶",
    )
    evolution(
        w, touched, i, "西上阁门副使", "右武郎",
        "北宋政和二年九月二十五日", origin,
        "政和二年西上阁门副使武阶易为右武郎。", "职源与沿革",
        source_event="武阶易为右武郎", target_event="承接西上阁门副使武阶",
    )
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理东、西上阁门副使统称实例、分司隶属、职能品位及政和改阶。")


def entry1392():
    i, main = 1392, F[1392]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "阁门", F[i]["title"], "宋初", main,
        "宋初以他官判阁门公事。", staff_type="差遣",
        office_event="置判阁门事", post_event="以他官判阁门公事",
    )
    finish(w, touched, "整理判阁门事宋初设置、阁门隶属和差遣性质。")


def entry1393():
    i, main = 1393, F[1393]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职能")
    rank, roster, aliases = field(i, "品位"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, F[i]["title"], "官职", "北宋",
        "东上阁门使、西上阁门使的合称",
        ("东上阁门使", "西上阁门使"), main,
        "正式词头直接合称东、西上阁门使。",
    )
    for office_title, post_title in (
        ("东上阁门司", "东上阁门使"),
        ("西上阁门司", "西上阁门使"),
    ):
        _, post, _ = office_staff(
            w, touched, i, office_title, post_title, "北宋", origin,
            f"{post_title}掌领本司公事。", "职源与沿革",
            staff_type="阁门使", office_event=f"设置{post_title}",
            post_event="掌领本司事及承旨禀命",
        )
        cite(w, "Timepoints", post, i, duty, "保存本司长官和横行武阶职能。", "职能")
        cite(w, "Timepoints", post, i, rank, "保存宋前期与元丰品位。", "品位")
    for time, quota, event in (
        ("北宋嘉祐三年", "六员", "东、西上阁门使合计增至六员"),
        ("北宋元丰官制", "各三员", "东、西上阁门使各三员"),
    ):
        current = node(
            w, touched, i, F[i]["title"], "官职", time, event, roster,
            "阁门使统称", f"记录{time}编制。", "编制", update_event=True,
        )
        cite(w, "Timepoints", current, i, roster, f"保存{quota}编制。", "编制")
    evolution(
        w, touched, i, "东上阁门使", "左武大夫",
        "北宋政和二年九月二十五日", origin,
        "政和二年东上阁门使武阶易为左武大夫。", "职源与沿革",
        source_event="武阶易为左武大夫", target_event="承接东上阁门使武阶",
    )
    evolution(
        w, touched, i, "西上阁门使", "右武大夫",
        "北宋政和二年九月二十五日", origin,
        "政和二年西上阁门使武阶易为右武大夫。", "职源与沿革",
        source_event="武阶易为右武大夫", target_event="承接西上阁门使武阶",
    )
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理东、西上阁门使统称实例、分司隶属、职能品位、员额与政和改阶。")


def entry1394():
    i, main = 1394, F[1394]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, F[i]["title"], "机构", "北宋",
        "东上阁门司、西上阁门司的合称",
        ("东上阁门司", "西上阁门司"), main,
        "正文明确北宋分东、西上阁门司。",
    )
    for superior in ("门下省", "台察", "中书省"):
        parent = node(
            w, touched, i, superior, "机构", "宋代（具体年月未载）",
            "先后统辖东、西上阁门司", main, "上级机构",
            f"建立{superior}无具体年月承载节点。",
        )
        relation(w, i, parent, group, "上下级机构", main,
                 f"正文记东、西上阁门司先后隶{superior}。")
    for title in ("东上阁门司", "西上阁门司"):
        tid = node(
            w, touched, i, title, "机构", "北宋", f"设在紫宸殿南廊",
            origin, "阁门机构", f"保存{title}北宋设置。", "职源与沿革",
        )
        cite(w, "Timepoints", tid, i, duty, f"保存{title}吉礼或凶礼职掌。", "职掌")
    for office_title, post_title, quota, staff_type in (
        ("东上阁门司", "东上阁门使", "三员", "使"),
        ("西上阁门司", "西上阁门使", "三员", "使"),
        ("东上阁门司", "东上阁门副使", "二员", "副使"),
        ("西上阁门司", "西上阁门副使", "二员", "副使"),
        (F[i]["title"], "阁门通事舍人", "十员", "阁职"),
        (F[i]["title"], "阁门祗候", "十二员", "阁职"),
        (F[i]["title"], "阁门看班祗候", "六员", "阁职"),
        (F[i]["title"], "点检阁门簿书公事", None, "兼官"),
        (F[i]["title"], "阁门提点承受", "十一员", "承受官"),
        (F[i]["title"], "东、西上阁门司吏", "八人", "吏员"),
    ):
        office_staff(
            w, touched, i, office_title, post_title, "北宋元丰官制", roster,
            f"元丰官制{post_title}列入{office_title}编制。", "编制",
            quota=quota, staff_type=staff_type,
            office_event=f"编制{post_title}", post_event=f"列入元丰阁门编制",
        )
    reform = node(
        w, touched, i, "知东、西上阁门事", "官职",
        "北宋政和二年十一月六日", "编制共八员（东六、西二）",
        roster, "知阁门事统称", "记录续文所载政和编制。", "编制",
    )
    conflict_citation = cite(
        w, "Timepoints", reform, i, roster,
        "本条记共八员，与‘知东、西上阁门事’条所记共四员冲突，保留两说。",
        "编制", conflict_flag=1,
        note="与第1390条所载编制共四员（东二、西二）冲突。",
    )
    conflict_note = "与第1390条所载编制共四员（东二、西二）冲突。"
    saved_flag, saved_note = w.conn.execute(
        "select conflict_flag,note from Citations where id=?", (conflict_citation,)
    ).fetchone()
    if saved_flag != 1 or saved_note != conflict_note:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?",
            (conflict_note, conflict_citation),
        )
        w._br(
            "Citations", conflict_citation,
            "标记本条共八员与第1390条共四员的编制冲突，并保留两说。",
        )
    east = node(
        w, touched, i, "东上阁门司", "机构", "南宋建炎元年十二月二十一日",
        "与西上阁门司合并", origin, "演变前",
        "建立东上阁门司合并节点。", "职源与沿革", update_event=True,
    )
    west = node(
        w, touched, i, "西上阁门司", "机构", "南宋建炎元年十二月二十一日",
        "与东上阁门司合并", origin, "演变前",
        "建立西上阁门司合并节点。", "职源与沿革", update_event=True,
    )
    gate = node(
        w, touched, i, "阁门", "机构", "南宋建炎元年十二月二十一日",
        "东、西上阁门司合并为阁门", origin, "演变后",
        "建立合并后的阁门节点。", "职源与沿革", update_event=True,
    )
    relation(w, i, east, gate, "前后演变", origin,
             "建炎元年东上阁门司并入阁门。", "职源与沿革")
    relation(w, i, west, gate, "前后演变", origin,
             "建炎元年西上阁门司并入阁门。", "职源与沿革")
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理东、西上阁门司层级、实例、职掌、元丰编制、政和冲突与建炎合并。")


def entry1395():
    i, main = 1395, F[1395]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "北宋",
        "东、西上阁门使及东、西上阁门副使的合称",
        ("东上阁门使", "西上阁门使", "东上阁门副使", "西上阁门副使"),
        main, "正文直接定义阁门使副的四个实例。",
    )
    finish(w, touched, "恢复阁门使副正式词条并建立四个使、副使实例。")


def entry1396():
    assert not F[1396]["text"] and F[1396]["fields"].get("__status__") == "placeholder"


def entry1397():
    assert not F[1397]["text"] and F[1397]["fields"].get("__status__") == "placeholder"


def entry1398():
    i, main = 1398, F[1398]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    formal_eid = canonicalize_four_directions(w, main)
    source, office = evolution(
        w, touched, i, "南、北宾客馆", F[i]["title"], "宋初", origin,
        "北宋初南、北宾客馆后改四方馆。", "职源与沿革",
        entity_type="机构", source_event="后改四方馆",
        target_event="由南、北宾客馆改置",
    )
    assert w.conn.execute(
        "select entity_id from Timepoints where id=?", (office,)
    ).fetchone()[0] == formal_eid
    for superior in ("台察", "中书省"):
        parent = node(
            w, touched, i, superior, "机构", "宋代（具体年月未载）",
            "先后统辖四方馆", main, "上级机构",
            f"建立{superior}无具体年月承载节点。",
        )
        undated = node(
            w, touched, i, F[i]["title"], "机构", "宋代（具体年月未载）",
            "先后隶台察、中书省", main, "内诸司",
            "建立四方馆无具体年月隶属节点。", update_event=True,
        )
        relation(w, i, parent, undated, "上下级机构", main,
                 f"正文记四方馆先后隶{superior}。")
    cite(w, "Timepoints", office, i, duty, "保存章表收进、朝会版位和宣赞名籍职掌。", "职掌")
    for time, post_title, quota, staff_type in (
        ("宋初", "判四方馆事", None, "差遣"),
        ("北宋淳化四年", "四方馆使", None, "馆长"),
        ("北宋元丰官制", "四方馆使", "二员", "馆长"),
        ("北宋政和二年十一月六日", "知四方馆事", "二员", "知馆事"),
        ("南宋", "四方馆官", None, "馆官统称"),
        ("南宋", "四方馆令史", "一人", "吏员"),
        ("南宋", "四方馆表奏官", "一人", "吏员"),
        ("南宋", "四方馆驱使官", "一人", "吏员"),
    ):
        office_staff(
            w, touched, i, F[i]["title"], post_title, time, roster,
            f"{post_title}列入四方馆编制。", "编制", quota=quota,
            staff_type=staff_type, office_event=f"编制{post_title}",
            post_event=f"列入四方馆编制",
        )
    four = node(
        w, touched, i, F[i]["title"], "机构", "南宋建炎元年十二月二十一日",
        "并入东上阁门司，后止称阁门司", origin, "演变前",
        "建立四方馆并入节点。", "职源与沿革", update_event=True,
    )
    gate = node(
        w, touched, i, "阁门", "机构", "南宋建炎元年十二月二十一日",
        "接收四方馆", origin, "演变后", "建立阁门接收节点。", "职源与沿革",
    )
    relation(w, i, four, gate, "前后演变", origin,
             "建炎元年四方馆并入东上阁门司，后归阁门。", "职源与沿革")
    for post_title in ("知阁门事", "同知阁门事"):
        _, post, _ = office_staff(
            w, touched, i, F[i]["title"], post_title, "南宋", roster,
            f"南宋四方馆事由{post_title}兼领。", "编制",
            staff_type="兼领官", office_event=f"由{post_title}兼领馆事",
            post_event="兼领四方馆事",
        )
        cite(w, "Timepoints", post, i, roster, "保存南宋兼领四方馆事。", "编制")
    alias_note(w, i, office, aliases, "简称")
    assert source
    finish(w, touched, "规范四方馆词头并整理源流、层级、职掌、历代编制、建炎并入和简称。")


def entry1399():
    i, main, aliases = 1399, F[1399]["text"], field(1399, "别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "四方馆", F[i]["title"], "宋初", main,
        "宋初以检校官或通事舍人判四方馆事。",
        staff_type="差遣", office_event="置判四方馆事",
        post_event="以检校官或通事舍人判馆事",
    )
    evolution(
        w, touched, i, F[i]["title"], "四方馆使", "北宋淳化四年",
        main, "淳化四年置四方馆使后，判四方馆事罢置。",
        source_event="四方馆使置后罢置", target_event="取代判四方馆事",
    )
    alias_note(w, i, post, aliases, "别名")
    finish(w, touched, "整理判四方馆事唐宋沿置、四方馆隶属、淳化罢置和别名。")


def entry1400():
    i, main = 1400, F[1400]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职能")
    rank, roster = field(i, "品位"), field(i, "编制")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "四方馆", F[i]["title"], "北宋淳化四年",
        origin, "淳化四年始置四方馆使，为本馆之长。", "职源与沿革",
        staff_type="馆长", office_event="始置四方馆使",
        post_event="始置，领四方馆公事",
    )
    cite(w, "Timepoints", post, i, duty, "保存馆长、兼领阁门和横行武阶职能。", "职能")
    cite(w, "Timepoints", post, i, rank, "保存正六品和迁转序阶。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存二员编制。", "编制")
    office = node(
        w, touched, i, "四方馆", "机构", "北宋淳化四年",
        "设置四方馆使", roster, "内诸司",
        "复用四方馆淳化四年节点。", "编制",
    )
    staff(w, i, office, post, roster, "四方馆使编制二员。", "编制",
          quota="二员", staff_type="馆长")
    group = node(
        w, touched, i, "横行五使", "官职", "北宋",
        "横行武臣迁转五使统称", duty, "横行武阶统称",
        "建立横行五使统称节点。", "职能", update_event=True,
    )
    member = node(
        w, touched, i, F[i]["title"], "官职", "北宋",
        "横行五使之一", duty, "横行武阶",
        "建立四方馆使横行武阶节点。", "职能",
    )
    relation(w, i, group, member, "统称与实例", duty,
             "四方馆使为横行五使之一。", "职能")
    evolution(
        w, touched, i, F[i]["title"], "拱卫大夫",
        "北宋政和二年九月二十五日", origin,
        "政和二年四方馆使武阶易为拱卫大夫。", "职源与沿革",
        source_event="武阶易为拱卫大夫", target_event="承接四方馆使武阶",
    )
    finish(w, touched, "整理四方馆使始置、馆长隶属、职能品位员额、横行五使实例和政和改阶。")


def main():
    for i in range(1381, 1401):
        globals()[f"entry{i}"]()
        suffix = " placeholder" if not F[i]["text"] else " done"
        print(f"#{i} {F[i]['title']}{suffix}")


if __name__ == "__main__":
    main()
