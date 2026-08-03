#!/usr/bin/env python3
"""提取 chapter5t7 第1061-1080条：御史台台案、前司与四推吏职。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1041_1060 as previous


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


F = {i: load(i) for i in range(1061, 1081)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
relation = base.relation
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
parent_child = previous.parent_child
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "北宋太祖、太宗朝": 960,
    "宋初": 960.1,
    "北宋咸平元年": 998,
    "宋前期（具体年月未载）": 1050,
    "北宋元丰新制": 1082.1,
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


def entry1061():
    i, main = 1061, F[1061]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "御史台", "监香使",
        "宋前期（具体年月未载）", main,
        "监香使隶御史台，由御史于国忌行香时临时差充。",
        staff_type="临时使职", office_event="临时差御史充监香使",
        post_event="国忌行香时纠察", officer="御史",
    )
    cite(w, "Timepoints", post, i, main, "保存监香使的国忌行香纠察职掌。")
    finish(w, touched, "整理监香使御史台隶属、御史差充及国忌行香纠察职掌。")


def entry1062():
    i, main = 1062, F[1062]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "台案", "机构", "宋初",
         "御史台吏人办事机构，共有内弹、外弹、杂事十四案",
         main, "御史台办事机构", "记录宋初台案性质及十四案规模。",
         update_event=True)
    parent_child(
        w, touched, i, "御史台", "台案", "宋初", main,
        "台案是御史台所属吏人办事机构。",
        parent_event="下设台案", child_event="御史台所属吏人办事机构",
    )
    for child in ("内弹案", "外弹案", "杂事案"):
        parent_child(
            w, touched, i, "台案", child, "宋初", main,
            f"{child}是台案所含办事案类。",
            parent_event="包括内弹、外弹、杂事诸案",
            child_event=f"台案所属{child}",
        )
    node(w, touched, i, "台案", "机构", "北宋咸平元年",
         "由宋初十四案裁并为十案", main, "御史台办事机构",
         "记录咸平元年台案存十案。", update_event=True)
    node(w, touched, i, "台案", "机构", "北宋元丰新制",
         "改制为十一案", main, "御史台办事机构",
         "记录元丰改制台案为十一案。", update_event=True)
    finish(w, touched, "整理台案御史台隶属、内外弹与杂事三类及宋初至元丰案数变化。")


INNER_CASES = ("百司案", "待制案", "两县案", "新赐案", "职田案", "内弹六品案")
INNER_RETAINED = ("百司案", "待制案", "两县案")
OUTER_CASES = ("刑狱案", "色役案", "外弹六品案")
OUTER_RETAINED = ("刑狱案", "色役案")


def entry1063():
    i, main = 1063, F[1063]["text"]
    aliases = F[i]["fields"]["简称"]
    w, touched = W(i), set()
    early = group_instances(
        w, touched, i, "内弹案", "机构", "北宋太祖、太宗朝",
        "内弹六案的统称", INNER_CASES, main,
        "原书六个词头中有两个同名六品案；此处按所属案区分为内弹六品案。",
    )
    current = group_instances(
        w, touched, i, "内弹案", "机构", "北宋咸平元年",
        "存百司案、待制案、两县案三案", INNER_RETAINED, main,
        "真宗咸平时内弹仅存三案。",
    )
    alias_note(w, i, current, aliases, "简称")
    assert early
    finish(w, touched, "建立内弹案统称、太祖太宗朝六个实例及咸平时存续三案。")


def inner_case_entry(i, title, duty=None, abolished=False):
    main = F[i]["text"]
    w, touched = W(i), set()
    if duty:
        for time in ("北宋太祖、太宗朝", "北宋咸平元年"):
            node(w, touched, i, title, "机构", time, duty, main,
                 "内弹案所属办事案", f"记录{title}职掌及咸平时仍存。",
                 update_event=True)
    if abolished:
        node(w, touched, i, title, "机构", "北宋咸平元年",
             "真宗朝以后不置", main, "内弹案废罢办事案",
             f"记录{title}真宗朝以后不置。", update_event=True)
    finish(w, touched, f"整理{title}的内弹案所属、职掌及咸平存废。")


def entry1064():
    inner_case_entry(1064, "百司案", "弹纠在京百司案牍及行遣文字")


def entry1065():
    inner_case_entry(1065, "待制案", "弹纠待制以上侍从官案牍及行遣文字")


def entry1066():
    inner_case_entry(1066, "两县案", "弹纠开封、祥符两县官司官吏案牍及行遣文字")


def entry1067():
    inner_case_entry(1067, "新赐案", abolished=True)


def entry1068():
    inner_case_entry(1068, "职田案", abolished=True)


def entry1069():
    inner_case_entry(1069, "内弹六品案", abolished=True)


def entry1070():
    i, main = 1070, F[1070]["text"]
    aliases = F[i]["fields"]["简称"]
    w, touched = W(i), set()
    early = group_instances(
        w, touched, i, "外弹案", "机构", "北宋太祖、太宗朝",
        "外弹三案的统称", OUTER_CASES, main,
        "原书六个词头中有两个同名六品案；此处按所属案区分为外弹六品案。",
    )
    current = group_instances(
        w, touched, i, "外弹案", "机构", "北宋咸平元年",
        "存刑狱案、色役案二案", OUTER_RETAINED, main,
        "真宗咸平元年外弹仅存二案。",
    )
    alias_note(w, i, current, aliases, "简称")
    assert early
    finish(w, touched, "建立外弹案统称、太祖太宗朝三个实例及咸平时存续二案。")


def outer_case_entry(i, title, duty=None, abolished=False):
    main = F[i]["text"]
    w, touched = W(i), set()
    if duty:
        for time in ("北宋太祖、太宗朝", "北宋咸平元年"):
            node(w, touched, i, title, "机构", time, duty, main,
                 "外弹案所属办事案", f"记录{title}职掌及咸平时仍存。",
                 update_event=True)
    if abolished:
        node(w, touched, i, title, "机构", "北宋咸平元年",
             "真宗朝以后不置", main, "外弹案废罢办事案",
             f"记录{title}真宗朝以后不置。", update_event=True)
    finish(w, touched, f"整理{title}的外弹案所属、职掌及咸平存废。")


def entry1071():
    outer_case_entry(1071, "刑狱案", "掌外推刑名案牍及行遣文字")


def entry1072():
    outer_case_entry(1072, "色役案", "掌各种名目差役词讼案牍及行遣文字")


def entry1073():
    outer_case_entry(1073, "外弹六品案", abolished=True)


def entry1074():
    i, main = 1074, F[1074]["text"]
    w, touched = W(i), set()
    node(w, touched, i, "杂事案", "机构", "宋初",
         "御史台台案之一，下有礼钱案、赃罚案、月申案、支计案、解补案",
         main, "台案所属办事案", "记录杂事案的御史台归属与五种所属案。",
         update_event=True)
    finish(w, touched, "整理杂事案御史台台案性质及原文列举的五种所属案，不强建无独立词头实体。")


def entry1075():
    i, main = 1075, F[1075]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "御史台", "前司", "宋前期（具体年月未载）",
        main, "前司是御史台除六察吏以外台吏公廨的总称。",
        parent_event="下设台吏前司",
        child_event="除六察吏以外的台吏公廨总称",
    )
    finish(w, touched, "建立前司作为御史台台吏公廨总称及其机构隶属。")


def entry1076():
    i, main = 1076, F[1076]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "前司", "驱使官",
        "宋前期（具体年月未载）", main,
        "本条驱使官隶御史台前司。",
        staff_type="台吏", office_event="设置驱使官",
        post_event="赍牒追取推勘公事相关人员、文字及物事",
    )
    cite(w, "Timepoints", post, i, main, "保存御史台前司驱使官的具体职掌。")
    finish(w, touched, "在既有同名驱使官实体上补建御史台前司时点、编制隶属与职掌。")


def four_push_staff(i, title, event, staff_type):
    main = F[i]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "御史台四推", title,
        "宋前期（具体年月未载）", main,
        f"{title}隶御史台四推。",
        staff_type=staff_type, office_event=f"设置{title}", post_event=event,
    )
    cite(w, "Timepoints", post, i, main, f"保存{title}的四推职掌。")
    finish(w, touched, f"整理{title}的御史台四推隶属、吏职性质与职掌。")


def entry1077():
    four_push_staff(
        1077, "主推", "为推直官下手，勘鞫时供给使、用刑；四年无过失可出职授三班奉职",
        "台狱吏",
    )


def entry1078():
    four_push_staff(1078, "推司", "职事与主推同，位次于主推", "台狱吏")


def entry1079():
    four_push_staff(1079, "四推令史", "看押犯人，每日与直官点名并锁牢门", "狱吏")


def entry1080():
    four_push_staff(
        1080, "四推书吏",
        "审讯时记录口供、抄写文案；三年无过失转主推，再二年出职授三班奉职",
        "狱吏",
    )


def main():
    for i in range(1061, 1081):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
