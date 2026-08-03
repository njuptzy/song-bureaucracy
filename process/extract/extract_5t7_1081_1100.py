#!/usr/bin/env python3
"""提取 chapter5t7 第1081-1100条：御史台吏、三京留台、谏院与大理寺。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1061_1080 as previous


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


F = {i: load(i) for i in range(1081, 1101)}
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
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "春秋晋国": -600,
    "西汉景帝中元六年": -144,
    "北齐": 550,
    "唐代": 700,
    "北宋雍熙初": 984,
    "宋初": 960,
    "北宋明道元年七月": 1032.5,
    "北宋庆历五年九月十八日": 1045.72,
    "北宋庆历五年以后（具体年月未载）": 1045.8,
    "北宋庆历七年六月二十一日": 1047.47,
    "北宋庆历七年六月二十一日以后（具体年月未载）": 1047.48,
    "宋前期（具体年月未载）": 1050,
    "宋前期（元丰七年前，具体年月未载）": 1070,
    "北宋熙宁二年十二月二十五日": 1069.96,
    "北宋熙宁二年以后": 1070.1,
    "宋代（御史台六察司设置期间，具体年月未载）": 1083,
    "北宋元丰元年十二月": 1078.96,
    "北宋元丰五年五月": 1082.35,
    "北宋元丰五年": 1082.4,
    "北宋元丰七年以后": 1084.2,
    "南宋": 1127,
    "南宋初": 1127.1,
    "南宋建炎三年三月六日": 1129.18,
    "南宋绍兴二年": 1132,
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


def simple_staff(i, office, title, event, staff_type, time="宋前期（具体年月未载）"):
    main = F[i]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, office, title, time, main,
        f"{title}隶{office}。", staff_type=staff_type,
        office_event=f"设置{title}", post_event=event,
    )
    cite(w, "Timepoints", post, i, main, f"保存{title}职掌。")
    finish(w, touched, f"整理{title}的{office}编制隶属、吏职性质与职掌。")


def entry1081():
    simple_staff(
        1081, "御史台四推", "书写人",
        "御史台狱书吏不足时特添差，供抄写文字", "台狱吏",
    )


def entry1082():
    simple_staff(
        1082, "前司", "主管班次",
        "掌朝会、典礼殿下班次仪范规矩", "台吏",
    )


def entry1083():
    simple_staff(
        1083, "前司", "引赞官",
        "掌朝会、典礼殿下班次导引，位次于主管班次", "台吏",
    )


def entry1084():
    simple_staff(
        1084, "前司", "知班官",
        "朝会编排侍立班次，祠祭大礼纠察禁卫导从秩序", "台吏",
    )


def entry1085():
    simple_staff(
        1085, "御史台六察司", "贴司", "书写六察文字", "六察吏",
        time="宋代（御史台六察司设置期间，具体年月未载）",
    )


def entry1086():
    i = 1086
    origin = field(i, "职源")
    duty = field(i, "职能")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "西京留守司御史台", "机构", "唐代",
         "唐东都留台为留守司御史台制度源流", origin,
         "前代留台源流", "记录唐代东都留台源流。", "职源",
         update_event=True)
    start = node(
        w, touched, i, "西京留守司御史台", "机构", "宋初",
        "宋初已置，初为前执政重臣休老养病之所",
        origin, "三京留台", "记录宋初始置。", "职源", update_event=True,
    )
    cite(w, "Timepoints", start, i, duty,
         "补证宋初留台职能与纠察郡政多不举行。", "职能")
    reform = node(
        w, touched, i, "西京留守司御史台", "机构",
        "北宋熙宁二年十二月二十五日",
        "增管勾官或权判一员，转为安置不拥护新法的监司以上官员",
        roster, "三京留台", "记录熙宁二年增员及职能变化。", "编制",
        update_event=True,
    )
    cite(w, "Timepoints", reform, i, duty, "补证熙宁后留台职能变化。", "职能")
    node(w, touched, i, "西京留守司御史台", "机构", "南宋",
         "罢置", origin, "废罢机构", "记录南宋罢置。", "职源",
         update_event=True)
    alias_note(w, i, start, aliases, "简称与别名")
    finish(w, touched, "整理西京留守司御史台唐代源流、宋初始置、熙宁增员转用及南宋罢置。")


def entry1087():
    i, main = 1087, F[1087]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "西京留守司御史台",
        "管勾西京留守司御史台公事", "宋前期（具体年月未载）",
        aliases, "西京留台管勾台事编制一人。", "简称",
        quota=1, staff_type="留台主管官",
        office_event="设置管勾留台事一人",
        post_event="国忌拜表行香并纠察班列，实为养老退闲差遣",
        officer="不及三品朝官",
    )
    cite(w, "Timepoints", post, i, main,
         "补证不及三品朝官差充资格及国忌行香职掌。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理管勾西京留守司御史台公事的资格、编制隶属、职掌与简称。")


def entry1088():
    i, main = 1088, F[1088]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "西京留守司御史台",
        "判西京留守司御史台", "宋前期（具体年月未载）",
        main, "三品以上朝官判领西京留台。",
        staff_type="留台主管官", office_event="由三品以上官判领",
        post_event="三品以上称判，不及三品称管勾或权判",
        officer="三品以上朝官",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理判西京留守司御史台的差遣资格、隶属与简称。")


def entry1089():
    i = 1089
    origin = field(i, "职源")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "南京留守司御史台", "机构",
        "北宋庆历五年九月十八日", "始置，职掌编制同西京留台",
        origin, "三京留台", "记录南京留台始置。", "职源",
        update_event=True,
    )
    node(w, touched, i, "南京留守司御史台", "机构", "南宋",
         "罢置", origin, "废罢机构", "记录南宋罢置。", "职源",
         update_event=True)
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理南京留守司御史台庆历始置、沿用西京职掌编制及南宋罢置。")


def entry1090():
    i, main = 1090, F[1090]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "南京留守司御史台",
        "管勾南京留守司御史台公事",
        "北宋庆历五年以后（具体年月未载）", aliases,
        "南京留台管勾台事编制一人。", "简称", quota=1,
        staff_type="留台主管官", office_event="设置管勾台事一人",
        post_event="国忌拜表行香，初为重臣养老散地",
    )
    cite(w, "Timepoints", post, i, main,
         "补证国忌行香、重臣养老及熙宁后转用。")
    node(w, touched, i, "管勾南京留守司御史台公事", "官职",
         "北宋熙宁二年以后", "用于安置不拥护新法而退下的监司以上官员",
         main, "留台主管官", "记录熙宁以后用途变化。", update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理管勾南京留台公事的隶属、员额、职掌、熙宁后转用及简称。")


def entry1091():
    i, main = 1091, F[1091]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "南京留守司御史台",
        "判南京留守司御史台",
        "北宋庆历五年以后（具体年月未载）", main,
        "三品以上朝官判领南京留台。",
        staff_type="留台主管官", office_event="由三品以上官判领",
        post_event="三品以上称判，不及三品称权判或管勾",
        officer="三品以上朝官",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理判南京留守司御史台的差遣资格、隶属与简称。")


def entry1092():
    i = 1092
    origin = field(i, "职源与沿革")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "北京留守司御史台", "机构",
        "北宋庆历七年六月二十一日", "始置，职掌编制同西京留台",
        origin, "三京留台", "记录北京留台始置。", "职源与沿革",
        update_event=True,
    )
    node(w, touched, i, "北京留守司御史台", "机构", "南宋", "罢置",
         origin, "废罢机构", "记录南宋罢置。", "职源与沿革",
         update_event=True)
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理北京留守司御史台庆历始置、沿用西京职掌编制及南宋罢置。")


def entry1093():
    i, main = 1093, F[1093]["text"]
    duty = field(i, "职掌")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "北京留守司御史台",
        "管勾北京留守司御史台公事",
        "北宋庆历七年六月二十一日", aliases,
        "北京留台始置时即差马绛管勾。", quota=1,
        staff_type="留台主管官", office_event="始置并差马绛管勾",
        post_event="管勾北京留台，职掌同管勾南京留台",
    )
    cite(w, "Timepoints", post, i, main, "补证本条为差遣名。")
    cite(w, "Timepoints", post, i, duty, "补证职掌同管勾南京留台。", "职掌")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理管勾北京留台公事庆历始置、隶属、员额、职掌与简称。")


THREE_CENSORATES = (
    "西京留守司御史台", "南京留守司御史台", "北京留守司御史台",
)


def entry1094():
    i, main = 1094, F[1094]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    group = group_instances(
        w, touched, i, "三京留守司御史台", "机构",
        "北宋庆历七年六月二十一日以后（具体年月未载）",
        "西京、南京、北京留守司御史台合称",
        THREE_CENSORATES, main, "原文明确列举三京留台三个实例。",
    )
    node(w, touched, i, "三京留守司御史台", "机构", "南宋",
         "三个留台均罢置", main, "机构统称废罢",
         "记录南宋三京留台均罢。", update_event=True)
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "建立三京留守司御史台统称、三个正式实例及南宋废罢。")


EARLY_CENSORS = (
    "御史大夫", "御史中丞", "侍御史知杂事", "侍御史", "殿中侍御史",
    "言事御史", "监察御史", "殿中侍御史里行", "监察御史里行",
)
REFORM_CENSORS = (
    "御史大夫", "御史中丞", "侍御史", "殿中侍御史", "监察御史",
)


def entry1095():
    i, main = 1095, F[1095]["text"]
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    group_instances(
        w, touched, i, "御史台官", "官职",
        "宋前期（元丰七年前，具体年月未载）",
        "御史大夫、中丞及三院御史、言事御史、里行等台官统称",
        EARLY_CENSORS, main, "原文逐一列出元丰七年前御史台官。",
    )
    reform = group_instances(
        w, touched, i, "御史台官", "官职", "北宋元丰七年以后",
        "不再包括侍御史知杂事、言事御史与两种里行",
        REFORM_CENSORS, main, "原文明确元丰七年后的台官范围。",
    )
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "建立御史台官统称及元丰七年前后成员变化。")


def entry1096():
    i, main = 1096, F[1096]["text"]
    w, touched = W(i), set()
    tid = node(
        w, touched, i, "三京留守司御史台", "机构",
        "北宋庆历七年六月二十一日以后（具体年月未载）",
        "西京、南京、北京留守司御史台合称", main,
        "机构统称", "复用三京留台统称节点承载官员别称证据。",
    )
    cite(
        w, "Timepoints", tid, i, main,
        "留都獬豸是三京留守司御史台官的别称，只作名称证据，不另建实体。",
        note="纯别称不另建实体",
    )
    finish(w, touched, "保存留都獬豸别称证据，不把别称另建为历史实体。")


def entry1097():
    i = 1097
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "别名")
    w, touched = W(i), set()
    node(w, touched, i, "谏院", "机构", "北宋雍熙初",
         "已见谏院之名，为谏官治事之所", origin,
         "谏官机构", "记录雍熙初已有谏院。", "职源与沿革",
         update_event=True)
    founded = node(
        w, touched, i, "谏院", "机构", "北宋明道元年七月",
        "以门下省为谏院，专门置局", origin, "谏官机构",
        "记录明道元年专门置局。", "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", founded, i, duty,
         "补证拾遗补阙及谏正朝政职掌。", "职掌")
    office_staff(
        w, touched, i, "谏院", "知谏院", "宋前期（具体年月未载）",
        roster, "北宋前期谏院置知谏院官六人。", "编制",
        quota=6, staff_type="谏院言事官", office_event="置知谏院官六人",
        post_event="入谏院供职，谏正朝政阙失",
    )
    node(w, touched, i, "谏院", "机构", "北宋元丰五年",
         "改制罢谏院之名", origin, "废罢机构",
         "记录元丰五年罢谏院名。", "职源与沿革", update_event=True)
    node(w, touched, i, "谏院", "机构", "南宋初",
         "中书、门下后省谏官仍以谏院为称", origin,
         "谏官机构", "记录南宋初恢复使用谏院名。", "职源与沿革",
         update_event=True)
    independent = node(
        w, touched, i, "谏院", "机构", "南宋建炎三年三月六日",
        "不隶两省，专门置局于都堂近侧", origin, "独立谏官机构",
        "记录建炎三年独立置局。", "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", independent, i, duty,
         "补证南宋谏院谏正百官百司职掌。", "职掌")
    for title in ("左谏议大夫", "右谏议大夫", "左司谏", "右司谏", "左正言", "右正言"):
        office_staff(
            w, touched, i, "谏院", title, "南宋", roster,
            f"南宋谏院置{title}一人。", "编制", quota=1,
            staff_type="谏官", office_event="设置六类正职谏官",
            post_event="谏院正职谏官",
        )
    alias_note(w, i, founded, aliases, "别名")
    finish(w, touched, "整理谏院雍熙至南宋建炎沿革、职掌、北宋知谏院编制及南宋六类谏官。")


def entry1098():
    i, main = 1098, F[1098]["text"]
    duty = field(i, "职掌")
    aliases = field(i, "别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "谏院", "知谏院", "宋前期（具体年月未载）",
        main, "知谏院是北宋前期在谏院实际供奉言事的差遣官。",
        quota=6, staff_type="谏院言事官", office_event="置知谏院官六人",
        post_event="由非言事官兼领，实际供奉言事",
    )
    node(w, touched, i, "知谏院", "官职", "宋前期（具体年月未载）",
         "谏诤朝政阙失，大则廷议、小则上封", duty,
         "谏院言事官", "记录知谏院职掌。", "职掌", update_event=True)
    alias_note(w, i, post, aliases, "别名")
    finish(w, touched, "整理知谏院的差遣性质、谏院隶属、员额、职掌与别名。")


def entry1099():
    i, main = 1099, F[1099]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "大理寺", "机构", "春秋晋国",
         "已有大理官，为大理名称源流", origin, "司法机构源流",
         "记录春秋大理官源流。", "职源", update_event=True)
    node(w, touched, i, "大理寺", "机构", "西汉景帝中元六年",
         "廷尉改名大理，为九卿之一", origin, "司法机构源流",
         "记录西汉大理名称沿革。", "职源", update_event=True)
    node(w, touched, i, "大理寺", "机构", "北齐",
         "大理寺官司名始置", origin, "司法机构源流",
         "记录北齐始有大理寺官司名。", "职源", update_event=True)
    early = node(
        w, touched, i, "大理寺", "机构", "宋前期",
        "推鞫覆审内外诸司冤诉与上奏刑案，送审刑院详议后同签上奏",
        duty, "中央司法机构", "记录宋前期职掌。", "职掌",
        update_event=True,
    )
    cite(w, "Timepoints", early, i, roster,
         "补证宋前期判寺、详断、法直官及府史承阙编制。", "编制")
    office_staff(
        w, touched, i, "大理寺", "判大理寺事", "宋前期", roster,
        "宋前期判大理寺事编制一员或二员。", "编制",
        quota="1-2", staff_type="大理寺主管官",
        office_event="置判大理寺事一员或二员",
        post_event="兼领大理寺公事",
    )
    node(w, touched, i, "大理寺", "机构", "北宋元丰元年十二月",
         "试置大理寺狱，专掌治狱，原奏案覆审归刑部、审刑院",
         duty, "中央司法机构", "记录元丰试行新制。", "职掌",
        update_event=True)
    reform = node(
        w, touched, i, "大理寺", "机构", "北宋元丰五年五月",
        "行新制，掌断刑兼治狱，职务分左断刑、右治狱",
        duty, "中央司法机构", "记录元丰五年新制职掌。", "职掌",
        update_event=True,
    )
    cite(w, "Timepoints", reform, i, roster,
         "补证元丰新制左右两局官吏与案司编制。", "编制")
    alias_note(w, i, reform, aliases, "简称与别名")
    assert main == "官司名。"
    finish(w, touched, "整理大理寺前代源流、宋前期覆审、元丰试制与断刑治狱分职。")


def entry1100():
    i, main = 1100, F[1100]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "大理寺", "判大理寺事", "宋前期",
        main, "判大理寺事掌领本寺并决断全国冤疑案件。",
        staff_type="大理寺主管官", office_event="设置判大理寺事",
        post_event="掌领本寺，决断冤疑案件，送审刑院覆议后同签上奏",
        officer="六部尚书以上台省长官或升朝官",
    )
    node(w, touched, i, "判大理寺事", "官职", "宋前期",
         "掌领本寺，决断冤疑案件，送审刑院覆议后同签上奏",
         main, "大理寺主管官", "记录判大理寺事职掌。", update_event=True)
    node(w, touched, i, "判大理寺事", "官职", "北宋元丰五年",
         "改制罢置", main, "废罢差遣", "记录元丰五年罢置。",
         update_event=True)
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理判大理寺事的差遣资格、隶属、职掌、员额、简称及元丰罢置。")


def main():
    for i in range(1081, 1101):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
