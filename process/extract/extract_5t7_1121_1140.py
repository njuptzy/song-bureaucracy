#!/usr/bin/env python3
"""提取 chapter5t7 第1121-1140条：大理寺左断刑案司与右治狱厅。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1101_1120 as previous


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


F = {i: load(i) for i in range(1121, 1141)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
parent_child = previous.parent_child


TIME_HINTS = {
    **previous.TIME_HINTS,
    "北宋元丰元年十二月十八日": 1078.96,
    "北宋元丰五年": 1082.4,
    "北宋元祐元年正月十日": 1086.03,
    "北宋元祐元年四月四日": 1086.25,
    "北宋元祐三年五月二日": 1088.35,
    "北宋绍圣二年七月二十三日": 1095.55,
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


def left_office_entry(i, event):
    main = F[i]["text"]
    title = F[i]["title"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "大理寺左断刑厅", title, "北宋元丰五年",
        main, f"{title}是大理寺左断刑厅所属办事机构。",
        parent_event="下设左断刑案司与库",
        child_event=event,
    )
    finish(w, touched, f"建立{title}的左断刑厅所属关系及职掌。")


def right_office_entry(i, event):
    main = F[i]["text"]
    title = F[i]["title"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "大理寺右治狱厅", title, "北宋元丰五年",
        main, f"{title}是大理寺右治狱厅所属办事机构。",
        parent_event="下设右治狱案司",
        child_event=event,
    )
    finish(w, touched, f"建立{title}的右治狱厅所属关系及职掌。")


def entry1121():
    left_office_entry(1121, "掌批会吏部等处选人改官有无犯过事")


def entry1122():
    left_office_entry(1122, "掌犯罪命官奏案断讫指挥的宣、草")


def entry1123():
    left_office_entry(1123, "掌分发、收取诸案文书")


def entry1124():
    i, main = 1124, F[1124]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "大理寺左断刑厅", "左断刑详断案",
        "北宋元丰五年", main, "左断刑详断案隶大理寺左断刑厅。",
        parent_event="下设左断刑详断案",
        child_event="掌定断诸路申奏狱案，分八房处办公事",
    )
    office_staff(
        w, touched, i, "左断刑详断案", "大理寺评事", "北宋元丰五年",
        main, "详断案分八房，每房一名大理评事。", quota=8,
        staff_type="详断案八房官", office_event="分八房处办公事",
        post_event="分管诸路申奏狱案，以雷、霆、号、令、星、斗、文、章为号",
    )
    finish(w, touched, "建立左断刑详断案隶属、八房职掌及八名大理评事编制。")


def entry1125():
    left_office_entry(1125, "拘催详断案八房断议狱案，兼办旬申月奏文字")


def entry1126():
    i, main = 1126, F[1126]["text"]
    assert main.startswith("大理司左断刑办事部门之一。")
    left_office_entry(1126, "掌有关投进文字的收接")


def entry1127():
    left_office_entry(1127, "掌大理寺左断刑诸杂务的管理")


def entry1128():
    left_office_entry(1128, "掌详断狱案时参考的条例等文字")


def entry1129():
    i, main = 1129, F[1129]["text"]
    aliases = field(i, "别名")
    w, touched = W(i), set()
    _, store = parent_child(
        w, touched, i, "大理寺左断刑厅", "左断刑架阁库",
        "北宋元丰五年", main, "左断刑架阁库隶大理寺左断刑厅。",
        parent_event="下设左断刑架阁库",
        child_event="收管已了结狱案的架阁文书",
    )
    _, clerk, _ = office_staff(
        w, touched, i, "左断刑架阁库", "大理寺主簿",
        "北宋元祐元年四月四日", aliases,
        "元祐元年诏大理寺左断刑架阁库专委主簿主管。", "别名",
        staff_type="主管官", office_event="专委大理寺主簿主管",
        post_event="主管左断刑架阁库",
    )
    alias_note(w, i, store, aliases, "别名")
    assert clerk
    finish(w, touched, "建立左断刑架阁库隶属、档案职掌、敕库别名及大理寺主簿主管关系。")


def entry1130():
    i, main = 1130, F[1130]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "大理寺左断刑厅", "断司", "北宋元丰五年",
        main, "断司是左断刑厅决断公案刑名的办事机构。",
        parent_event="下设断司", child_event="详断案草并由大理正审核签印",
    )
    for title, staff_type, event in (
        ("大理寺评事", "断司详断官", "依法详断案草"),
        ("大理寺司直", "断司详断官", "依法详断案草"),
        ("大理寺正", "断司审定官", "审核案草当否、批书签印"),
    ):
        office_staff(
            w, touched, i, "断司", title, "北宋元丰五年", main,
            f"{title}是断司组成官员。", staff_type=staff_type,
            office_event="由评事、司直、正组成",
            post_event=event,
        )
    finish(w, touched, "建立断司的左断刑厅隶属、三类组成官员及详断审定流程。")


def entry1131():
    i, main = 1131, F[1131]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "大理寺左断刑厅", "议司", "北宋元丰五年",
        main, "议司是左断刑厅覆议断司案草的办事机构。",
        parent_event="下设议司", child_event="覆议断司案草，审定后判成录奏",
    )
    for title, staff_type, event in (
        ("大理寺左断刑丞", "议司覆议官", "覆议断司所决案草并签署改正意见"),
        ("大理寺卿", "议司长官", "作为长贰审定案草"),
        ("大理寺断刑少卿", "议司长官", "作为长贰审定案草"),
    ):
        office_staff(
            w, touched, i, "议司", title, "北宋元丰五年", main,
            f"{title}是议司组成官员。", staff_type=staff_type,
            office_event="由断刑寺丞、大理寺卿、断刑少卿组成",
            post_event=event,
        )
    finish(w, touched, "建立议司的左断刑厅隶属、三类组成官员及覆议审定流程。")


def entry1132():
    i, main = 1132, F[1132]["text"]
    aliases = field(i, "简称")
    assert main.startswith("官署名。")
    w, touched = W(i), set()
    node(
        w, touched, i, "大理寺右治狱厅", "机构",
        "北宋元丰元年十二月十八日", "制度前身大理寺狱始置，专主鞫狱事",
        main, "治狱机构前身", "记录元丰元年置大理寺狱。", update_event=True,
    )
    _, reform = parent_child(
        w, touched, i, "大理寺", "大理寺右治狱厅", "北宋元丰五年",
        main, "元丰五年大理寺分左、右二厅，右厅专一推鞫重密公案。",
        parent_event="分设左断刑、右治狱二厅",
        child_event="始置，专一推鞫内降重密公案及侵贪冤抑事件",
    )
    for title, quota, staff_type, event in (
        ("大理寺治狱少卿", 1, "右治狱副长官", "分领右治狱"),
        ("大理寺右治狱丞", 4, "右治狱推丞", "专掌推鞫狱事"),
        ("大理寺卿", None, "总领长官", "总领左断刑、右治狱"),
    ):
        office_staff(
            w, touched, i, "大理寺右治狱厅", title, "北宋元丰五年",
            main, f"{title}隶右治狱厅。", quota=quota, staff_type=staff_type,
            office_event="配置右治狱官属", post_event=event,
        )
    node(w, touched, i, "大理寺右治狱厅", "机构",
         "北宋元祐三年五月二日", "罢置", main, "废罢机构",
         "记录元祐三年罢右治狱。", update_event=True)
    _, restored = parent_child(
        w, touched, i, "大理寺", "大理寺右治狱厅",
        "北宋绍圣二年七月二十三日", main, "绍圣二年复置右治狱。",
        parent_event="复置右治狱厅", child_event="复置右治狱并增设司直一名",
    )
    office_staff(
        w, touched, i, "大理寺右治狱厅", "大理寺司直",
        "北宋绍圣二年七月二十三日", main, "复置右治狱时增设司直一名。",
        quota=1, staff_type="右治狱纠察官", office_event="增设司直一名",
        post_event="兼纠察右治狱稽违、赃罚事",
    )
    parent_child(
        w, touched, i, "大理寺", "大理寺右治狱厅", "南宋", main,
        "南宋右治狱沿置但编制调整。", parent_event="统辖右治狱厅",
        child_event="沿置，不置司直，增大理寺正一员，推丞减为二员",
    )
    for title, quota, staff_type, event in (
        ("大理寺正", 1, "右治狱审定官", "审定左、右二推判案"),
        ("大理寺右治狱丞", 2, "右治狱推丞", "专掌推鞫狱事"),
    ):
        office_staff(
            w, touched, i, "大理寺右治狱厅", title, "南宋", main,
            f"南宋右治狱置{title}{quota}人。", quota=quota,
            staff_type=staff_type, office_event="南宋调整右治狱官属",
            post_event=event,
        )
    alias_note(w, i, restored or reform, aliases, "简称")
    finish(w, touched, "整理右治狱厅元丰前身与分厅、官属职掌、元祐罢置、绍圣复置及南宋编制变化。")


def push_entry(i, title, transfer_target):
    main = F[i]["text"]
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "大理寺右治狱厅", title, "北宋元丰五年", main,
        f"{title}是右治狱厅所属二推之一。",
        parent_event="下设左推、右推", child_event="与另一推分管审讯根究并作出判决",
    )
    node(w, touched, i, title, "机构", "北宋元祐元年正月十日",
         "左、右二推合并为一", main, "治狱机构合并",
         "记录元祐元年左右二推合并。", update_event=True)
    node(w, touched, i, title, "机构", "北宋元祐三年五月二日", "罢置",
         main, "废罢机构", "记录元祐三年随右治狱罢置。", update_event=True)
    parent_child(
        w, touched, i, "大理寺右治狱厅", title,
        "北宋绍圣二年七月二十三日", main, f"绍圣二年复置{title}。",
        parent_event="复置左推、右推", child_event="复置，翻案送另一推覆审",
    )
    office_staff(
        w, touched, i, title, "大理寺右治狱丞",
        "北宋绍圣二年七月二十三日", main,
        f"{title}置治狱寺丞二员。", quota=2, staff_type="分推推丞",
        office_event="置治狱寺丞二员", post_event=f"分管{title}审讯推鞫",
    )
    parent_child(
        w, touched, i, "大理寺右治狱厅", title, "南宋", main,
        f"南宋{title}沿置。", parent_event="统辖左推、右推",
        child_event=f"沿置，翻案送{transfer_target}覆审",
    )
    office_staff(
        w, touched, i, title, "大理寺右治狱丞", "南宋", main,
        f"南宋{title}治狱寺丞减为一员。", quota=1, staff_type="分推推丞",
        office_event="治狱寺丞减为一员", post_event=f"分管{title}审讯推鞫",
    )
    if i == 1133:
        office_staff(
            w, touched, i, "大理寺右治狱厅", "大理寺正", "南宋", main,
            "南宋增大理寺正一名，审左、右二推判案。", quota=1,
            staff_type="二推审定官", office_event="增大理寺正审定二推判案",
            post_event="审定左、右二推判案",
        )
        office_staff(
            w, touched, i, "大理寺右治狱厅", "大理寺治狱少卿", "南宋", main,
            "治狱少卿一员总领左、右二推。", quota=1,
            staff_type="二推总领官", office_event="由治狱少卿总领",
            post_event="总领左、右二推",
        )
    first = node(w, touched, i, title, "机构", "北宋元丰五年",
                 "与另一推分管审讯根究并作出判决", main, "右治狱所属狱",
                 f"复用{title}始置节点承载别名证据。")
    alias_note(w, i, first, aliases, "简称与别名")
    finish(w, touched, f"整理{title}元丰设置、元祐合并罢置、绍圣复置、翻案互送、推丞与南宋官属。")


def entry1133():
    push_entry(1133, "大理寺左推", "大理寺右推")


def entry1134():
    assert F[1134]["text"].endswith("余与“左推”同。")
    push_entry(1134, "大理寺右推", "大理寺左推")


def entry1135():
    right_office_entry(1135, "狱案判决执行后收理案犯并追取赃物")


def entry1136():
    right_office_entry(1136, "追取、核对左右二推所追究的官物、官钱与文书")


def entry1137():
    right_office_entry(1137, "点检左右推所断狱案并提供法律条例")


def entry1138():
    right_office_entry(1138, "管理与承办本狱杂务、杂物")


def entry1139():
    right_office_entry(1139, "收接有关狱案投进文字")


def entry1140():
    right_office_entry(1140, "承办旬申月奏文字")


def main():
    for i in range(1121, 1141):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
