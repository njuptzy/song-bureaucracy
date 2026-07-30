#!/usr/bin/env python3
"""提取 chapter5t7 第1-20条：寺监统称与太常寺系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


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
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(1, 21)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field=None):
    source = F[i]["fields"][field] if field else F[i]["text"]
    assert needle in source, (i, field, needle)
    return needle


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def C(i, field_name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(w, table, target_id, i, quotation, decision, field_name=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field_name), quotation, decision, **kwargs
    )


def state(
    w,
    i,
    title,
    type_,
    time,
    event,
    quotation,
    category,
    decision,
    field_name=None,
    *,
    officer=None,
    grade=None,
):
    eid = w.entity(title, type_, decision, quotation=quotation)
    tid = w.timepoint(
        eid,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        attr_officer_type=officer,
        attr_grade=grade,
        chain="none",
    )
    cite(w, "Timepoints", tid, i, quotation, decision, field_name)
    return eid, tid


def relationship(
    w,
    i,
    subject_id,
    object_id,
    relation_type,
    quotation,
    decision,
    field_name=None,
    **kwargs,
):
    rid = w.relationship(
        subject_id,
        object_id,
        relation_type,
        decision,
        quotation,
        **kwargs,
    )
    cite(w, "Relationships", rid, i, quotation, decision, field_name)
    return rid


PRE_SONG_ORDER = {
    "秦": -221,
    "西汉初": -202,
    "东汉": 25,
    "北齐": 550,
    "唐": 618,
    "五代后晋": 936,
}
ERA_START = {
    "建隆": 960, "乾德": 963, "开宝": 968, "太平兴国": 976,
    "雍熙": 984, "端拱": 988, "淳化": 990, "至道": 995,
    "咸平": 998, "景德": 1004, "大中祥符": 1008, "天禧": 1017,
    "乾兴": 1022, "天圣": 1023, "明道": 1032, "景祐": 1034,
    "宝元": 1038, "康定": 1040, "庆历": 1041, "皇祐": 1049,
    "至和": 1054, "嘉祐": 1056, "治平": 1064, "熙宁": 1068,
    "元丰": 1078, "元祐": 1086, "绍圣": 1094, "元符": 1098,
    "崇宁": 1102, "大观": 1107, "政和": 1111, "宣和": 1119,
    "靖康": 1126, "建炎": 1127, "绍兴": 1131, "隆兴": 1163,
    "乾道": 1165, "淳熙": 1174, "绍熙": 1190, "庆元": 1195,
}
ERA_RE = re.compile("|".join(sorted(ERA_START, key=len, reverse=True)))


def time_key(time, row_id):
    if time == "未知":
        return (-10000, 0, row_id)
    if time in PRE_SONG_ORDER:
        return (PRE_SONG_ORDER[time], 0, row_id)
    if time in ("宋代", "两宋"):
        return (959, 0, row_id)
    if time == "宋初":
        return (960, 0, row_id)
    if time in ("宋前期", "北宋前期"):
        return (970, 0, row_id)
    if time.startswith("南宋中兴"):
        return (1127, 0, row_id)
    if time == "南宋":
        return (1127, 1, row_id)
    if "绍兴以后" in time:
        return (1131, 9, row_id)
    match = ERA_RE.search(time)
    if match:
        year = ERA_START[match.group(0)]
        number = re.search(r"([一二三四五六七八九十元]+)年", time[match.end():])
        if number:
            raw = number.group(1)
            values = {
                "元": 1, "一": 1, "二": 2, "三": 3, "四": 4,
                "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
                "十": 10, "十一": 11, "十二": 12,
            }
            year += values.get(raw, 1) - 1
        return (year, 0, row_id)
    if time.startswith("北宋"):
        return (1000, 0, row_id)
    if time.startswith("南宋"):
        return (1150, 0, row_id)
    return (0, 0, row_id)


def rechain(w, entity_id, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (entity_id,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid,
            decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


TEMPLES = (
    "太常寺", "宗正寺", "光禄寺", "卫尉寺", "鸿胪寺",
    "大理寺", "太仆寺", "司农寺", "太府寺",
)
SEVEN_TEMPLES = (
    "光禄寺", "卫尉寺", "太仆寺", "大理寺", "鸿胪寺", "司农寺", "太府寺",
)
FIVE_MONITORS = ("国子监", "少府监", "将作监", "军器监", "都水监")
OLD_THREE_MONITORS = ("秘书监", "少府监", "将作监")
SOUTH_THREE_MONITORS = ("秘书省", "军器监", "将作监")


def officer_names(suffix, temples=TEMPLES):
    return tuple(f"{title}{suffix}" for title in temples)


TEMPLE_HEADS = officer_names("卿")
TEMPLE_DEPUTIES = officer_names("少卿")
TEMPLE_ASSISTANTS = officer_names("丞")
TEMPLE_CLERKS = officer_names("主簿")


def group_entry(i, title, group_type, states):
    quote = F[i]["text"]
    w = W(i)
    touched = set()
    group_eid = None
    for time, event, members in states:
        group_eid, group_tid = state(
            w, i, title, group_type, time, event, quote,
            f"{group_type}统称", f"建立{title}{time}统称状态。",
        )
        touched.add(group_eid)
        for member_title, member_type in members:
            member_eid, member_tid = state(
                w, i, member_title, member_type, time,
                f"{title}在{time}所指实例", quote,
                f"{title}实例", f"据{title}条建立或复用{member_title}{time}状态。",
            )
            touched.add(member_eid)
            relationship(
                w, i, group_tid, member_tid, "统称与实例", quote,
                f"{member_title}是{title}在{time}的实例。",
            )
    for eid in touched:
        rechain(w, eid, f"按历史先后重建{title}及其实例时间链。")
    w.commit()


def entry1():
    i = 1
    quote = F[i]["text"]
    group_entry(
        i, "九寺五监", "机构",
        [("北宋元丰新制", "元丰定制的九寺与五监合称", [(x, "机构") for x in TEMPLES + FIVE_MONITORS])],
    )
    w = W(i)
    source = w.find_entity("司天监", "机构")
    target = w.find_entity("太史局", "机构")
    assert source and target
    source_tp = w.find_timepoint(source, "北宋元丰五年")
    target_tp = w.find_timepoint(target, "北宋元丰五年五月")
    assert source_tp and target_tp
    cite(w, "Timepoints", source_tp, i, quote, "补证司天监在元丰新制改称太史局。")
    cite(w, "Timepoints", target_tp, i, quote, "补证太史局由司天监改名。")
    relationship(w, i, source_tp, target_tp, "前后演变", quote,
                 "元丰新制司天监改名太史局。")
    w.commit()


def entry2():
    all_temple_members = [(x, "机构") for x in TEMPLES]
    group_entry(
        2, "九寺三监", "机构",
        [
            ("宋前期", "九寺与秘书监、少府监、将作监的合称",
             all_temple_members + [(x, "机构") for x in OLD_THREE_MONITORS]),
            ("南宋", "南宋名义上的九寺与秘书省、军器监、将作监合称",
             all_temple_members + [(x, "机构") for x in SOUTH_THREE_MONITORS]),
            ("南宋绍兴以后", "绍兴以后实际留存的五寺三监",
             [(x, "机构") for x in ("太常寺", "宗正寺", "大理寺", "太府寺", "司农寺") + SOUTH_THREE_MONITORS]),
        ],
    )

    i = 2
    quote = F[i]["text"]
    w = W(i)
    touched = set()
    merge_map = {
        "卫尉寺": "兵部",
        "太仆寺": "驾部",
        "太府寺": "户部",
        "司农寺": "户部",
        "光禄寺": "礼部",
        "鸿胪寺": "礼部",
    }
    for source_title, target_title in merge_map.items():
        source_eid, source_tp = state(
            w, i, source_title, "机构", "南宋中兴以来",
            f"省并，职事归{target_title}", quote, "寺监机构",
            f"建立{source_title}南宋省并节点。",
        )
        target_eid, target_tp = state(
            w, i, target_title, "机构", "南宋中兴以来",
            f"接收{source_title}职事", quote, "尚书省部门或所属司",
            f"建立{target_title}接收{source_title}职事节点。",
        )
        touched.update((source_eid, target_eid))
        relationship(w, i, source_tp, target_tp, "前后演变", quote,
                     f"南宋中兴以来{source_title}省并，其职事归{target_title}。")
    for title in ("宗正寺", "太府寺", "司农寺"):
        eid, _ = state(
            w, i, title, "机构", "南宋绍兴以后", "绍兴复置", quote,
            "寺监机构", f"建立{title}绍兴复置节点。",
        )
        touched.add(eid)
    for eid in touched:
        rechain(w, eid, "按历史先后连接南宋寺监省并与复置节点。")
    w.commit()


def entry3():
    song_heads = list(TEMPLE_HEADS) + ["秘书监", "少府监", "将作监"]
    reform_heads = list(TEMPLE_HEADS) + [
        "国子监祭酒", "少府监", "将作监", "军器监", "都水监使者",
    ]
    south_heads = list(TEMPLE_HEADS) + ["秘书省监", "军器监", "将作监"]
    group_entry(
        3, "寺监长官", "官职",
        [
            ("宋前期", "九寺三监长官连称", [(x, "官职") for x in song_heads]),
            ("北宋元丰新制", "九寺卿与五监长官合称", [(x, "官职") for x in reform_heads]),
            ("南宋", "九寺三监长官连称", [(x, "官职") for x in south_heads]),
        ],
    )


def entry4():
    early = list(TEMPLE_DEPUTIES) + [
        "秘书省少监", "殿中省少监", "少府少监", "将作少监",
    ]
    reform = list(TEMPLE_DEPUTIES) + [
        "国子监司业", "少府少监", "将作少监", "军器少监", "都水监丞",
    ]
    south = list(TEMPLE_DEPUTIES) + [
        "秘书省少监", "军器少监", "将作少监", "少府少监", "都水监丞",
    ]
    group_entry(
        4, "寺监副贰", "官职",
        [
            ("北宋前期", "九寺少卿与秘书、殿中、少府、将作少监连称",
             [(x, "官职") for x in early]),
            ("北宋元丰五年新制", "九寺少卿与五监副贰连称",
             [(x, "官职") for x in reform]),
            ("南宋绍兴以后", "南宋诸寺监副贰连称",
             [(x, "官职") for x in south]),
        ],
    )


def entry5():
    early = list(TEMPLE_ASSISTANTS) + ["秘书丞", "少府监丞", "将作监丞"]
    reform = list(TEMPLE_ASSISTANTS) + [
        "国子监丞", "少府监丞", "将作监丞", "军器监丞", "都水监丞",
    ]
    group_entry(
        5, "诸寺监丞", "官职",
        [
            ("宋前期", "九寺三监丞总名，作为文臣迁转官阶",
             [(x, "官职") for x in early]),
            ("北宋元丰新制", "九寺五监丞总名，参领本寺监事并与长贰签书公事",
             [(x, "官职") for x in reform]),
        ],
    )


def entry6():
    early = list(TEMPLE_CLERKS) + ["秘书省主簿", "少府监主簿", "将作监主簿"]
    reform = list(TEMPLE_CLERKS) + [
        "国子监主簿", "少府监主簿", "将作监主簿", "军器监主簿", "都水监主簿",
    ]
    group_entry(
        6, "诸寺监主簿", "官职",
        [
            ("宋前期", "九寺三监主簿总名，作为文臣迁转官阶",
             [(x, "官职") for x in early]),
            ("北宋元丰新制", "九寺五监主簿总名，专掌勾考簿书",
             [(x, "官职") for x in reform]),
            ("南宋", "可与丞以上寺监官签书本寺监公事",
             [(x, "官职") for x in reform]),
        ],
    )

    i = 6
    quote = F[i]["text"]
    alias_quote = field(i, "简称")
    w = W(i)
    eid = w.find_entity("诸寺监主簿", "官职")
    assert eid
    _, yuanfeng = state(
        w, i, "诸寺监主簿", "官职", "北宋元丰六年七月",
        "诏寺监主簿止专掌簿书，公事由丞以上通议施行",
        alias_quote, "寺监主簿统称", "建立元丰六年职守节点。", "简称",
        officer="职事官", grade="从八品",
    )
    _, yuanyou = state(
        w, i, "诸寺监主簿", "官职", "北宋元祐元年八月六日",
        "诏许通管寺事，太常寺、国子监主簿只通管本司杂务",
        quote, "寺监主簿统称", "建立元祐元年通管寺事节点。",
        officer="职事官", grade="从八品",
    )
    assert yuanfeng and yuanyou
    rechain(w, eid, "连接诸寺监主簿宋前期、元丰、元祐与南宋节点。")
    w.commit()


def simple_group(i, title, members, *, group_type="官职", time="宋代", event=None):
    group_entry(
        i, title, group_type,
        [(time, event or f"{title}统称", [(x, group_type) for x in members])],
    )


def entry7_to_16():
    simple_group(7, "九卿", TEMPLE_HEADS, event="宋代九寺长官总称")
    simple_group(8, "九寺少卿", TEMPLE_DEPUTIES, event="宋代九寺副长官总称")
    simple_group(
        9, "卿少", TEMPLE_HEADS + TEMPLE_DEPUTIES,
        event="九寺卿与少卿或某寺卿与少卿的连称",
    )
    simple_group(10, "九寺丞", TEMPLE_ASSISTANTS,
                 event="九寺所置丞的总称")
    simple_group(11, "九寺主簿", TEMPLE_CLERKS,
                 event="九寺所置主簿的总称")
    simple_group(12, "七寺", SEVEN_TEMPLES, group_type="机构",
                 event="太常寺、宗正寺以外七寺的合称")
    simple_group(13, "七寺卿", officer_names("卿", SEVEN_TEMPLES),
                 event="太常卿、宗正卿以外七寺卿的总称")
    simple_group(14, "七寺少卿", officer_names("少卿", SEVEN_TEMPLES),
                 event="太常少卿、宗正少卿以外七寺少卿的总称")
    simple_group(15, "七寺丞", officer_names("丞", SEVEN_TEMPLES),
                 event="太常寺丞、宗正寺丞以外七寺丞的总称，均为正八品")
    simple_group(16, "三丞", ("宗正寺丞", "太常寺丞", "秘书丞"),
                 event="宗正寺丞、太常寺丞、秘书省丞的合称，均为从七品")


def entry17():
    i = 17
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    touched = set()

    feng_eid, feng_start = state(
        w, i, "奉常", "机构", "秦", "掌宗庙礼仪", history,
        "前代礼制机构", "建立秦奉常职源节点。", "职源与沿革",
    )
    _, feng_end = state(
        w, i, "奉常", "机构", "西汉初", "改称太常", history,
        "前代礼制机构", "建立奉常改称太常节点。", "职源与沿革",
    )
    chang_eid, chang_start = state(
        w, i, "太常", "机构", "西汉初", "由奉常改称", history,
        "前代礼制机构", "建立西汉太常节点。", "职源与沿革",
    )
    _, chang_end = state(
        w, i, "太常", "机构", "北齐", "改为太常寺之称", history,
        "前代礼制机构", "建立太常改称太常寺节点。", "职源与沿革",
    )
    temple_eid, northern_qi = state(
        w, i, "太常寺", "机构", "北齐", "始有太常寺之称", history,
        "礼制机构", "建立太常寺北齐职源节点。", "职源与沿革",
    )
    _, early = state(
        w, i, "太常寺", "机构", "宋前期",
        "大部职事为礼院、礼仪院所占，仅掌社稷、武成王庙、诸坛、斋宫及习乐",
        duty, "中央礼制机构", "建立太常寺宋前期职掌节点。", "职掌",
    )
    _, kangding = state(
        w, i, "太常寺", "机构", "北宋康定元年十一月",
        "改判礼院事为判太常寺事并兼礼仪事，收回部分职事",
        duty, "中央礼制机构", "建立太常寺康定收回职事节点。", "职掌",
    )
    _, reform = state(
        w, i, "太常寺", "机构", "北宋元丰改制后",
        "礼院职事罢归，统掌礼乐、郊庙、社稷、陵寝、医药等事",
        duty, "中央礼制机构", "建立太常寺元丰改制节点。", "职掌",
    )
    _, music_split = state(
        w, i, "太常寺", "机构", "北宋崇宁四年八月",
        "大晟府专掌乐后，太常寺专掌礼",
        duty, "中央礼制机构", "建立太常寺崇宁礼乐分掌节点。", "职掌",
    )
    _, receive = state(
        w, i, "太常寺", "机构", "南宋隆兴元年七月",
        "光禄寺并入太常寺", history,
        "中央礼制机构", "建立太常寺隆兴接收光禄寺节点。", "职源与沿革",
    )
    touched.update((feng_eid, chang_eid, temple_eid))
    relationship(w, i, feng_end, chang_start, "前后演变", history,
                 "西汉初奉常改称太常。", "职源与沿革")
    relationship(w, i, chang_end, northern_qi, "前后演变", history,
                 "北齐太常机构始称太常寺。", "职源与沿革")

    old_liguan = w.find_entity("判太常礼院", "官职")
    if old_liguan:
        old_tp = w.find_timepoint(old_liguan, "北宋康定元年十一月")
        assert old_tp
        new_post_eid, new_post_tp = state(
            w, i, "判太常寺", "官职", "北宋康定元年十一月",
            "由判礼院事改置并兼礼仪事", duty,
            "太常寺差遣", "建立判太常寺康定改置节点。", "职掌",
            officer="差遣",
        )
        touched.add(new_post_eid)
        relationship(w, i, old_tp, new_post_tp, "前后演变", duty,
                     "康定元年改判礼院事为判太常寺事。", "职掌")

    old_office = w.find_entity("太常礼院", "机构")
    if old_office:
        old_tp = w.find_timepoint(old_office, "北宋元丰五年五月")
        assert old_tp
        relationship(w, i, old_tp, reform, "前后演变", duty,
                     "元丰改制罢礼院，职事归太常寺。", "职掌")

    music_eid, music_tp = state(
        w, i, "大晟府", "机构", "北宋崇宁四年八月", "始建，专掌乐",
        duty, "中央音乐机构", "建立大晟府始置节点。", "职掌",
    )
    touched.add(music_eid)
    light_eid, light_end = state(
        w, i, "光禄寺", "机构", "南宋隆兴元年七月", "并入太常寺",
        history, "寺监机构", "建立光禄寺隆兴并入节点。", "职源与沿革",
    )
    touched.add(light_eid)
    relationship(w, i, light_end, receive, "前后演变", history,
                 "隆兴元年七月光禄寺并入太常寺。", "职源与沿革")

    cite(w, "Timepoints", reform, i, rank,
         "补证太常寺在九寺中冠首、地位清重。", "品位")
    cite(w, "Timepoints", reform, i, aliases,
         "简称与典故称谓段同时补证三丞的制度地位。", "简称与别名",
         note="纯简称不另建实体；其中三丞制度事实已由第16条提取")

    officer_specs = (
        ("太常寺卿", 1), ("太常寺少卿", 1), ("太常寺丞", 1),
        ("太常寺博士", 4), ("太常寺主簿", 1), ("太常寺协律郎", 1),
        ("太常寺奉礼郎", 1), ("太常寺太祝", 1),
        ("籍田令", None), ("宫闱令", None), ("太庙令", None), ("郊社令", None),
        ("赞引使", 4), ("正礼直官", 2), ("副礼直官", 2),
        ("正名赞者", 8), ("守阙赞者", 7), ("私名赞者", 7),
        ("胥长", 1), ("胥吏", 1), ("胥佐", 4), ("贴司", 1),
        ("书表司", 1), ("诸司局供官", 27), ("乐正", 3),
        ("鼓吹令", None), ("专知官", None), ("库子", None),
    )
    for title, quota in officer_specs:
        eid, tid = state(
            w, i, title, "官职", "北宋元丰改制后",
            f"太常寺编制所列{title}", staff,
            "太常寺官吏", f"据太常寺编制建立{title}节点。", "编制",
            officer="官或公吏",
        )
        touched.add(eid)
        relationship(
            w, i, reform, tid, "编制隶属", staff,
            f"{title}列入太常寺编制。", "编制",
            staff_quota=quota, staff_type="官或公吏",
        )

    case_titles = (
        "太常寺礼仪案", "太常寺祠祭案", "太常寺坛庙案", "太常寺大乐案",
        "太常寺法物案", "太常寺廪牺案", "太常寺太医案", "太常寺掌法案",
        "太常寺知杂案",
    )
    subordinate_titles = (
        "太医局", "教场", "提点管勾郊庙祭器所", "太庙奉安所",
        "诸陵祠坟所", "太庙什物库",
    )
    for title in case_titles + subordinate_titles:
        eid, tid = state(
            w, i, title, "机构", "北宋元丰改制后",
            f"太常寺所辖或所设{title}", staff,
            "太常寺所属机构", f"据太常寺编制建立{title}节点。", "编制",
        )
        touched.add(eid)
        relationship(w, i, reform, tid, "上下级机构", staff,
                     f"{title}为太常寺所设或所辖机构。", "编制")

    for eid in touched:
        rechain(w, eid, "按历史先后连接太常寺系统时间点。")
    w.commit()


def entry18():
    i = 18
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    rank = field(i, "品位")
    staff = field(i, "编制")
    duty = field(i, "职掌")
    aliases = field(i, "简称")
    w = W(i)
    touched = set()
    eid, jin = state(
        w, i, "判太常寺", "官职", "五代后晋", "已有判太常寺事",
        history, "前代职源", "建立判太常寺后晋职源节点。", "职源与沿革",
        officer="差遣",
    )
    _, early = state(
        w, i, "判太常寺", "官职", "宋初", "始置，掌太常寺所存职事",
        history, "太常寺差遣", "建立判太常寺宋初节点。", "职源与沿革",
        officer="三品以上官或两制官兼充",
    )
    _, kangding = state(
        w, i, "判太常寺", "官职", "北宋康定元年十一月十四日",
        "兼礼仪事", history, "太常寺差遣", "建立判太常寺康定节点。",
        "职源与沿革", officer="三品以上官或两制官兼充",
    )
    _, end = state(
        w, i, "判太常寺", "官职", "北宋元丰五年", "改制正名后罢置",
        history, "太常寺差遣", "建立判太常寺元丰罢置节点。", "职源与沿革",
        officer="差遣",
    )
    touched.add(eid)
    cite(w, "Timepoints", early, i, duty, "补证判太常寺宋前期职掌。", "职掌")
    cite(w, "Timepoints", early, i, rank, "补证判太常寺充任资格。", "品位")
    cite(w, "Timepoints", kangding, i, aliases,
         "简称段补证康定置判寺并兼礼仪事。", "简称", note="简称本身不另建实体")
    cite(w, "Timepoints", early, i, staff, "补证编制一人或二人。", "编制")

    temple_eid = w.find_entity("太常寺", "机构")
    assert temple_eid
    for parent_time, post_tp in (
        ("宋前期", early),
        ("北宋康定元年十一月", kangding),
    ):
        parent_tp = w.find_timepoint(temple_eid, parent_time)
        assert parent_tp
        relationship(w, i, parent_tp, post_tp, "编制隶属", history,
                     f"{parent_time}太常寺置判太常寺差遣。", "职源与沿革",
                     staff_type="三品以上官或两制官兼充")
    rechain(w, eid, "连接判太常寺后晋、宋初、康定与元丰罢置节点。")
    w.commit()


def entry19():
    i = 19
    main = F[i]["text"]
    aliases = field(i, "简称")
    w = W(i)
    eid, tid = state(
        w, i, "同判太常寺", "官职", "北宋康定元年十一月十四日",
        "始置，兼礼仪事，位次判寺官后，职掌与判太常寺同",
        main, "太常寺差遣", "建立同判太常寺始置节点。",
        officer="差遣",
    )
    cite(w, "Timepoints", tid, i, aliases,
         "简称段补证同判寺兼礼仪事。", "简称", note="简称本身不另建实体")
    temple_eid = w.find_entity("太常寺", "机构")
    parent = w.find_timepoint(temple_eid, "北宋康定元年十一月")
    assert parent
    relationship(w, i, parent, tid, "编制隶属", main,
                 "康定元年太常寺始置同判太常寺。", staff_type="差遣")
    rechain(w, eid, "确认同判太常寺时间链。")
    w.commit()


def entry20():
    i = 20
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    staff = field(i, "编制")
    aliases = field(i, "简称与别名")
    w = W(i)
    eid, han = state(
        w, i, "太常寺卿", "官职", "东汉", "始有太常卿之称",
        history, "前代职源", "建立太常寺卿东汉名源节点。", "职源与沿革",
        officer="长官",
    )
    _, qi = state(
        w, i, "太常寺卿", "官职", "北齐", "始置太常寺卿",
        history, "前代职源", "建立太常寺卿北齐职源节点。", "职源与沿革",
        officer="长官",
    )
    _, early = state(
        w, i, "太常寺卿", "官职", "宋前期",
        "无职事，杂压存其名，行礼时为行事官",
        duty, "文臣迁转官阶", "建立太常寺卿宋前期节点。", "职掌",
        officer="阶官", grade="正三品",
    )
    _, reform = state(
        w, i, "太常寺卿", "官职", "北宋元丰改制后",
        "太常寺长官，总领寺事，掌礼乐、郊庙、社稷、坛壝、陵寝、医药",
        duty, "太常寺长官", "建立太常寺卿元丰职事官节点。", "职掌",
        officer="职事官", grade="正四品",
    )
    cite(w, "Timepoints", early, i, rank, "补证宋前期正三品。", "品位")
    cite(w, "Timepoints", reform, i, rank,
         "补证元丰后正四品及在九卿中的位次。", "品位")
    cite(w, "Timepoints", reform, i, staff,
         "补证太常寺卿一人、不常置。", "编制")
    cite(w, "Timepoints", reform, i, aliases,
         "简称与拟古称谓仅作名称证据。", "简称与别名", note="纯简称、别名不另建实体")
    cite(w, "Timepoints", reform, i, main,
         "正文明确区分宋前期阶官与元丰新制职事官。")

    temple_eid = w.find_entity("太常寺", "机构")
    assert temple_eid
    for parent_time, post_tp, quote, field_name in (
        ("宋前期", early, duty, "职掌"),
        ("北宋元丰改制后", reform, duty, "职掌"),
    ):
        parent = w.find_timepoint(temple_eid, parent_time)
        assert parent
        relationship(
            w, i, parent, post_tp, "编制隶属", quote,
            f"{parent_time}太常寺与太常寺卿的编制关系。", field_name,
            staff_quota=1 if parent_time == "北宋元丰改制后" else None,
            staff_type="职事官" if parent_time == "北宋元丰改制后" else "阶官",
        )
    rechain(w, eid, "连接太常寺卿东汉、北齐、宋前期与元丰节点。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1, 21)] == [
        "九寺五监", "九寺三监", "寺监长官", "寺监副贰", "诸寺监丞",
        "诸寺监主簿", "九卿", "九寺少卿", "卿少", "九寺丞",
        "九寺主簿", "七寺", "七寺卿", "七寺少卿", "七寺丞",
        "三丞", "太常寺", "判太常寺", "同判太常寺", "太常寺卿",
    ]
    entry1()
    entry2()
    entry3()
    entry4()
    entry5()
    entry6()
    entry7_to_16()
    entry17()
    entry18()
    entry19()
    entry20()


if __name__ == "__main__":
    main()
