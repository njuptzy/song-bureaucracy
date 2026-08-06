#!/usr/bin/env python3
"""提取 chapter11t12 第502-521条：爵位专条、食邑实封与勋制前六转。"""

import importlib.util
import json
import os
import sqlite3
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DICT_DB = ROOT / "data/database/song_bureaucracy_dictionary_ch11t12.db"
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    str(ROOT / "data/database/song_bureaucracy_entries_ch1t12.db"),
)

base_spec = importlib.util.spec_from_file_location(
    "extract_11t12_482_501_helpers", HERE / "extract_11t12_482_501.py"
)
base = importlib.util.module_from_spec(base_spec)
assert base_spec.loader is not None
base_spec.loader.exec_module(base)


def load(entry_id):
    with sqlite3.connect(DICT_DB) as connection:
        row = connection.execute(
            "SELECT title,page,text,fields FROM chapter11t12 WHERE id=?", (entry_id,)
        ).fetchone()
    assert row, entry_id
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {entry_id: load(entry_id) for entry_id in range(502, 522)}


def configure(module):
    module.F = F
    module.ENTRY_DB = ENTRY_DB
    child = getattr(module, "base", None)
    if child is not None:
        configure(child)
    helpers = getattr(module, "helpers", None)
    if helpers is not None:
        helpers.F = F
        helpers.ENTRY_DB = ENTRY_DB
        helpers.NEW_SORT = {}


configure(base)

W = base.W
Q = base.Q
state = base.state
relation = base.relation
append_event = base.append_event


def source(entry_id):
    return f'《宋代官制辞典》第{F[entry_id]["page"]}页“{F[entry_id]["title"]}”条'


def cite(writer, target_table, target_id, entry_id, quotation, decision, **kwargs):
    return writer.citation(
        target_table, target_id, source(entry_id), quotation, decision, **kwargs
    )


def sentence(entry_id, start_text):
    text = F[entry_id]["text"]
    start = text.index(start_text)
    return text[start:text.index("。", start) + 1]


def delete_target_citations(writer, target_table, target_id):
    citation_ids = [
        row[0] for row in writer.conn.execute(
            "SELECT id FROM Citations WHERE target_table=? AND target_id=?",
            (target_table, target_id),
        )
    ]
    for citation_id in citation_ids:
        writer.conn.execute(
            "DELETE FROM BuildRecords WHERE target_table='Citations' AND target_id=?",
            (citation_id,),
        )
    writer.conn.execute(
        "DELETE FROM Citations WHERE target_table=? AND target_id=?",
        (target_table, target_id),
    )


def remove_bad_membership(writer, time, member_title):
    peerage_sources = {
        '《宋代官制辞典》第663页“爵”条',
        '《宋代官制辞典》第663页"爵"条',
    }
    group_entity = writer.find_entity("爵", "官职")
    member_entity = writer.find_entity(member_title, "官职")
    assert group_entity is not None and member_entity is not None
    group = writer.find_timepoint(group_entity, time)
    member = writer.find_timepoint(member_entity, time)
    if member is None:
        return
    assert group is not None
    relationship_row = writer.conn.execute(
        "SELECT id FROM Relationships WHERE subject_id=? AND object_id=? "
        "AND relation_type='统称与实例'",
        (group, member),
    ).fetchone()
    if relationship_row:
        relationship_id = relationship_row[0]
        sources = {
            row[0] for row in writer.conn.execute(
                "SELECT citation FROM Citations WHERE target_table='Relationships' "
                "AND target_id=?", (relationship_id,)
            )
        }
        assert sources <= peerage_sources, (
            time, member_title, sources
        )
        delete_target_citations(writer, "Relationships", relationship_id)
        writer.conn.execute(
            "DELETE FROM BuildRecords WHERE target_table='Relationships' AND target_id=?",
            (relationship_id,),
        )
        writer.conn.execute("DELETE FROM Relationships WHERE id=?", (relationship_id,))

    remaining = writer.conn.execute(
        "SELECT COUNT(*) FROM Relationships WHERE subject_id=? OR object_id=?",
        (member, member),
    ).fetchone()[0]
    if remaining:
        return
    citation_sources = {
        row[0] for row in writer.conn.execute(
            "SELECT citation FROM Citations WHERE target_table='Timepoints' AND target_id=?",
            (member,),
        )
    }
    assert citation_sources <= peerage_sources, (
        time, member_title, citation_sources
    )
    row = writer.conn.execute(
        "SELECT prev_id,succ_id FROM Timepoints WHERE id=?", (member,)
    ).fetchone()
    assert row
    prev_id, succ_id = row
    if prev_id is not None:
        writer.relink(
            prev_id, f"删除误列的{member_title}{time}节点后接续时间链。",
            succ_id=succ_id,
        )
    if succ_id is not None:
        writer.relink(
            succ_id, f"删除误列的{member_title}{time}节点后接续时间链。",
            prev_id=prev_id,
        )
    delete_target_citations(writer, "Timepoints", member)
    writer.conn.execute("DELETE FROM NormalizedTimes WHERE timepoint_id=?", (member,))
    writer.conn.execute(
        "DELETE FROM BuildRecords WHERE target_table='Timepoints' AND target_id=?",
        (member,),
    )
    writer.conn.execute("DELETE FROM Timepoints WHERE id=?", (member,))


def repair_ten_rank_memberships():
    writer = W(502)
    for member in ("侯", "伯", "子", "男"):
        remove_bad_membership(writer, "北宋哲宗元祐官品令", member)
    for member in ("郡公", "县公", "侯", "伯", "子", "男"):
        remove_bad_membership(writer, "南宋宁宗庆元官品令", member)
    writer.commit()


def enrich_membership(writer, entry_id, title, time, ordinal, grade, quote, order):
    grade_text = f"；{grade}" if grade else ""
    _, member = state(
        writer, entry_id, title, time,
        f"列为{time}爵等之第{ordinal}等{grade_text}", quote,
        f"据{F[entry_id]['title']}专条补证{time}爵等位次和官品。",
        category="爵制", officer="爵位", grade=grade, sort_order=order,
    )
    append_event(
        writer, member, f"第{ordinal}等{grade_text}",
        f"据专条补足{title}在{time}的位次和官品。",
        category="爵制", officer="爵位", grade=grade,
    )
    _, group = state(
        writer, entry_id, "爵", time, f"{time}爵制", quote,
        f"复用{time}爵制统称节点。",
        category="爵制", officer="职官总名", sort_order=order,
    )
    relation(
        writer, entry_id, group, member, "统称与实例", quote,
        f"原文明示{title}为{time}爵等第{ordinal}等。",
    )
    return member


PEERAGE_SPECS = {
    502: ("嗣王", "从一品", (("北宋前期", "二", 96000000),
                              ("南宋宁宗庆元官品令", "二", 119500000))),
    503: ("郡王", "从一品", (("北宋前期", "三", 96000000),
                              ("北宋哲宗元祐官品令", "三", 108600000),
                              ("南宋宁宗庆元官品令", "三", 119500000))),
    504: ("国公", "从一品", (("北宋前期", "四", 96000000),
                              ("北宋哲宗元祐官品令", "四", 108600000),
                              ("南宋宁宗庆元官品令", "四", 119500000))),
    505: ("郡公", "从一品", (("北宋前期", "五", 96000000),
                              ("北宋哲宗元祐官品令", "五", 108600000))),
    506: ("开国公", None, (("北宋前期", "六", 96000000),)),
    507: ("开国郡公", "正二品", (("北宋前期", "七", 96000000),
                                  ("南宋宁宗庆元官品令", "五", 119500000))),
    508: ("开国县公", "从二品", (("北宋前期", "八", 96000000),
                                  ("南宋宁宗庆元官品令", "六", 119500000))),
    509: ("开国侯", "从三品", (("北宋前期", "九", 96000000),
                                ("北宋哲宗元祐官品令", "七", 108600000),
                                ("南宋宁宗庆元官品令", "七", 119500000))),
    510: ("开国伯", "正四品", (("北宋前期", "十", 96000000),
                                ("北宋哲宗元祐官品令", "八", 108600000),
                                ("南宋宁宗庆元官品令", "八", 119500000))),
    511: ("开国子", "正五品", (("北宋前期", "十一", 96000000),
                                ("北宋哲宗元祐官品令", "九", 108600000),
                                ("南宋宁宗庆元官品令", "九", 119500000))),
    512: ("开国男", "从五品", (("北宋前期", "十二", 96000000),
                                ("北宋哲宗元祐官品令", "十", 108600000),
                                ("南宋宁宗庆元官品令", "十", 119500000))),
}


def peerage_intro(entry_id):
    text = F[entry_id]["text"]
    end = 0
    for _ in range(3):
        next_end = text.find("。", end)
        if next_end < 0:
            break
        end = next_end + 1
    return text[:end]


def instance(writer, entry_id, parent, child, time, event, quote, order):
    _, parent_tp = state(
        writer, entry_id, parent, time, f"{parent}爵位实例见载", quote,
        f"建立或复用{parent}{time}节点以连接具体封号。",
        category="爵制", officer="爵位", sort_order=order,
    )
    _, child_tp = state(
        writer, entry_id, child, time, event, quote,
        f"原文明列{child}为{parent}爵位实例。",
        category="爵位封号", officer="爵位", sort_order=order,
    )
    relation(
        writer, entry_id, parent_tp, child_tp, "统称与实例", quote,
        f"{child}是{parent}的具体封号实例。",
    )
    return child_tp


def extract_peerage_entries():
    for entry_id, (title, grade, regimes) in PEERAGE_SPECS.items():
        writer = W(entry_id)
        intro = peerage_intro(entry_id)
        for time, ordinal, order in regimes:
            enrich_membership(
                writer, entry_id, title, time, ordinal, grade, intro, order
            )

        if entry_id == 502:
            quote = Q(entry_id, "如元丰七年，以宗晖为“嗣濮王”，濮国是小国名")
            instance(
                writer, entry_id, "嗣王", "嗣濮王", "北宋神宗元丰七年",
                "宗晖承继濮王爵，濮国为小国", quote, 108400000,
            )
        elif entry_id == 503:
            quote = Q(
                entry_id,
                "如赵枢（徽宗第五子）封建安郡王、赵桓（徽宗子）封河间郡王，张俊封河清郡王、秦桧封建康郡王等。",
            )
            for child, event in (
                ("建安郡王", "赵枢所封"), ("河间郡王", "赵桓所封"),
                ("河清郡王", "张俊所封"), ("建康郡王", "秦桧所封"),
            ):
                instance(
                    writer, entry_id, "郡王", child, "宋代（具体年未载）",
                    event, quote, 96000000,
                )
        elif entry_id == 504:
            tang = Q(entry_id, "如裴度以同中书门下平章事封晋国公")
            instance(
                writer, entry_id, "国公", "晋国公", "唐代",
                "裴度以同中书门下平章事封", tang, 80000000,
            )
            south = Q(
                entry_id,
                "入南宋，宰相径封国公，不必等候所封食邑至万户。",
            )
            _, south_tp = state(
                writer, entry_id, "国公", "南宋",
                "宰相可径封，不必待食邑满万户", south,
                "记录南宋国公封授门槛变化。",
                category="爵制", officer="爵位", grade="从一品",
                sort_order=112700000,
            )
            cite(writer, "Timepoints", south_tp, entry_id, south, "补证南宋国公封授规则。")
        elif entry_id == 505:
            absent = Q(entry_id, "南宋诸官品令无此爵位")
            _, absent_tp = state(
                writer, entry_id, "郡公", "南宋诸官品令",
                "明确不列郡公爵位", absent,
                "记录郡公未列入南宋官品令。",
                category="爵制排除", officer="爵位", sort_order=112700000,
            )
            cite(writer, "Timepoints", absent_tp, entry_id, absent, "补证南宋官品令不列郡公。")
        elif entry_id == 506:
            example = Q(
                entry_id,
                "（淳熙十一年）通奉大夫、知枢密院事、荥阳郡开国公、食邑二千六百户、食实封六百户周必大",
            )
            instance(
                writer, entry_id, "开国公", "荥阳郡开国公",
                "南宋孝宗淳熙十一年", "周必大所封，食邑二千六百户、食实封六百户",
                example, 118400000,
            )
            rule = Q(entry_id, "北宋元丰改制后，侍从官以上始得开国五等爵，少卿监以下不许。食邑二千户以上封开国公。凡开国公，皆系以郡名")
            _, rule_tp = state(
                writer, entry_id, "开国公", "北宋元丰改制后",
                "侍从官以上始得；少卿监以下不许；食邑二千户以上；皆系郡名",
                rule, "记录开国公元丰后封授规则。",
                category="爵制", officer="爵位", sort_order=108000000,
            )
            cite(writer, "Timepoints", rule_tp, entry_id, rule, "补证开国公封授规则。")
        elif entry_id == 507:
            limit = Q(entry_id, "臣僚（不包括宰相、特封）封爵至开国郡公止")
            _, limit_tp = state(
                writer, entry_id, "开国郡公", "宋代",
                "臣僚常制封爵止阶，宰相及特封除外", limit,
                "记录臣僚封爵至开国郡公止。",
                category="爵制", officer="爵位", grade="正二品",
                sort_order=96000000,
            )
            cite(writer, "Timepoints", limit_tp, entry_id, limit, "补证开国郡公止阶规则。")
        elif entry_id in (509, 510, 511, 512):
            title_rules = {
                509: "侍从官以上、食邑一千户，许封开国侯",
                510: "侍从官以上、食邑七百户封开国伯",
                511: "侍从官以上、食邑五百户封开国子",
                512: "宋沿唐、五代之制，开国男系以县名",
            }
            rule = Q(entry_id, title_rules[entry_id])
            _, rule_tp = state(
                writer, entry_id, title, "宋代", title_rules[entry_id], rule,
                f"记录{title}封授门槛或名号规则。",
                category="爵制", officer="爵位", grade=grade,
                sort_order=96000000,
            )
            cite(writer, "Timepoints", rule_tp, entry_id, rule, f"补证{title}封授规则。")

        if entry_id == 512:
            conflict = Q(entry_id, "侍从官以上、食邑三百户，封开国子。")
            north_entity = writer.find_entity("开国男", "官职")
            assert north_entity is not None
            north_tp = writer.find_timepoint(north_entity, "北宋前期")
            assert north_tp is not None
            cite(
                writer, "Timepoints", north_tp, entry_id, conflict,
                "原书开国男条此处作‘三百户封开国子’，与本条标题、紧随实例及爵条‘三百户封开国男’冲突，保留原文但不据此建立错误关系。",
                note="原书内部冲突：应与爵条及本条实例合参",
                conflict_flag=1,
            )
        writer.commit()


def group_member(writer, entry_id, group_title, member_title, time, event,
                 quote, order, *, category, group_officer="职官总名",
                 member_officer="加封名号"):
    _, group = state(
        writer, entry_id, group_title, time, f"{group_title}总称", quote,
        f"建立或复用{group_title}{time}总称节点。",
        category=category, officer=group_officer, sort_order=order,
    )
    _, member = state(
        writer, entry_id, member_title, time, event, quote,
        f"建立或复用{member_title}{time}节点。",
        category=category, officer=member_officer, sort_order=order,
    )
    relation(
        writer, entry_id, group, member, "统称与实例", quote,
        f"原文明示{member_title}属于{group_title}。",
    )
    return member


def extract_food_fiefs():
    entry_id = 513
    writer = W(entry_id)
    origin = Q(entry_id, "加封名号。食邑系封爵之产物。")
    food = group_member(
        writer, entry_id, "爵制加封名号", "食邑", "宋代",
        "封爵所生加封名号；虚封，与进爵等联系", origin,
        96000000, category="爵制加封",
    )
    han = Q(entry_id, "汉武帝以后，诸侯唯得衣食租税，则食所封境内民户之租税，此为后世加封食邑之滥觞")
    state(
        writer, entry_id, "食邑", "西汉武帝以后",
        "诸侯食所封境内民户租税，成为后世加封食邑滥觞", han,
        "建立食邑西汉职源节点。", category="前代职源",
        officer="加封名号", sort_order=-14000000,
    )
    wei = Q(entry_id, "三国魏黄初三年，爵号自关内侯以下“皆不食租”，此则食邑虚封之始")
    state(
        writer, entry_id, "食邑", "三国魏黄初三年",
        "关内侯以下皆不食租，食邑虚封之始", wei,
        "建立食邑虚封起点。", category="前代职源",
        officer="加封名号", sort_order=22200000,
    )
    split = Q(entry_id, "至隋、唐，户封增为食邑与食实封（真食）二种")
    group_member(
        writer, entry_id, "户封", "食邑", "隋唐时期",
        "户封二种之一", split, 60000000, category="户封制度",
    )
    group_member(
        writer, entry_id, "户封", "食实封", "隋唐时期",
        "户封二种之一，又称真食", split, 60000000, category="户封制度",
    )
    song = Q(entry_id, "宋沿唐制，每遇大礼，文武臣、宗室有加食邑之制")
    append_event(writer, food, "每遇大礼，文武臣及宗室可加食邑", "补充宋代食邑加封时机。")
    cite(writer, "Timepoints", food, entry_id, song, "补证宋代沿唐加食邑制度。")
    levels = Q(entry_id, "食邑最高为一万户，最低为二百户，其间有八千户、七千户、六千户、五千户、四千户、三千户、二千户、一千户、七百户、五百户、四百户、三百户，总共为十四等。")
    append_event(writer, food, "最高一万户、最低二百户，共十四等", "补充食邑十四等。")
    cite(writer, "Timepoints", food, entry_id, levels, "补证食邑户数十四等。")
    increments = Q(entry_id, "加食邑之式为：①知制诰（中书舍人）、待制及文臣少卿监、武臣诸司副使、宗室副率以上，内殿承制、内殿崇班与军员，初得恩例加食邑三百户；承制、崇班、军员再加止二百户。②宗室环卫大将军以上每加四百户。③宣徽使、三司使、观文殿大学士以下至直学士，文臣侍郎、武臣观察使、宗室正任以上、皇子环卫上将军、附马都尉等，每加五百户。④执政官、使相、节度使每加七百户，宰相、亲王、枢密使每加一千户。二千户上有加例而无定法。")
    append_event(writer, food, "依官资分每次加二百、三百、四百、五百、七百或一千户；二千户以上无定法", "补充食邑加户等差。")
    cite(writer, "Timepoints", food, entry_id, increments, "补证食邑加户等差。")
    threshold = Q(entry_id, "食邑至一千户以上封侯爵，满万户封国公。食邑系虚封，是一种仅与进爵等有联系的虚衔")
    append_event(writer, food, "一千户以上封侯、满万户封国公；本身为虚封", "补充食邑与进爵门槛。")
    cite(writer, "Timepoints", food, entry_id, threshold, "补证食邑进爵门槛及虚封性质。")
    real = Q(entry_id, "食邑加至一千五百户以上，如加实封，则称“食实封”若干户")
    _, real_tp = state(
        writer, entry_id, "食实封", "宋代",
        "食邑一千五百户以上方可加，称食实封若干户", real,
        "建立食实封宋代门槛节点。", category="爵制加封",
        officer="加封名号", sort_order=96000000,
    )
    group = writer.find_entity("爵制加封名号", "官职")
    assert group is not None
    group_tp = writer.find_timepoint(group, "宋代")
    assert group_tp is not None
    relation(
        writer, entry_id, group_tp, real_tp, "统称与实例", real,
        "食实封为宋代爵制加封名号。",
    )
    writer.commit()

    entry_id = 514
    writer = W(entry_id)
    sui = Q(entry_id, "食实封源于隋朝“真食若干户”")
    state(
        writer, entry_id, "食实封", "隋朝", "真食若干户，为食实封职源", sui,
        "建立食实封隋代职源节点。", category="前代职源",
        officer="加封名号", sort_order=58100000,
    )
    tang = Q(entry_id, "至唐，则改称“赐实封若干户”、“加实封若干户”")
    state(
        writer, entry_id, "食实封", "唐代",
        "改称赐实封或加实封若干户，渐变为内府给缯布", tang,
        "建立食实封唐代沿革节点。", category="前代职源",
        officer="加封名号", sort_order=61800000,
    )
    late = Q(entry_id, "唐末及五代，罢食实封实物之给，而创置特加邑户")
    state(
        writer, entry_id, "食实封", "唐末五代",
        "停止实物之给，改创特加邑户", late,
        "记录唐末五代食实封制度变化。", category="前代职源",
        officer="加封名号", sort_order=90000000,
    )
    song = Q(entry_id, "宋代沿唐中期之制，加食邑与食实封并存")
    real_entity = writer.find_entity("食实封", "官职")
    assert real_entity is not None
    song_tp = writer.find_timepoint(real_entity, "宋代")
    assert song_tp is not None
    append_event(writer, song_tp, "与食邑并存", "补充宋代食实封制度。")
    cite(writer, "Timepoints", song_tp, entry_id, song, "补证食邑与食实封并存。")
    cash = Q(entry_id, "食实封每户给钱二十五文，南宋理宗朝时已罢，成为虚封")
    state(
        writer, entry_id, "食实封", "南宋理宗朝",
        "停止每户给钱二十五文，成为虚封", cash,
        "记录理宗朝食实封钱给停止。", category="爵制加封",
        officer="加封名号", sort_order=122400000,
    )
    grades = Q(entry_id, "按常制，食实封最高一千户，最低一百户，其间有八百户、五百户、四百户、三百户、二百户，共七等。亲王、重臣有特加至数千户者。")
    append_event(writer, song_tp, "常制最高一千户、最低一百户，共七等；亲王重臣可特加数千户", "补充食实封七等。")
    cite(writer, "Timepoints", song_tp, entry_id, grades, "补证食实封户数七等。")
    method = Q(entry_id, "其加法为：①宰相、亲王遇恩加四百户。②执政、使相、节度使、宣徽使，皇子环卫上将军及宗室、驸马都尉带正任观察使以上加三百户。③观文殿学士、宗室带正任刺史至防御使以上、勋级至骑都尉加二百户。武臣内殿崇班、宗室副率以上加一百户。五百户以上有加例而无定法。实封以增户数为差，而与爵级无关")
    append_event(writer, song_tp, "依官资每次加一百至四百户；五百户以上无定法；与爵级无关", "补充食实封加户等差。")
    cite(writer, "Timepoints", song_tp, entry_id, method, "补证食实封加户等差。")
    writer.commit()


MERIT_RANKS = (
    "上柱国", "柱国", "上护军", "护军", "上轻车都尉", "轻车都尉",
    "上骑都尉", "骑都尉", "骁骑尉", "飞骑尉", "云骑尉", "武骑尉",
)


def merit_group(writer, entry_id, time, event, quote, order):
    _, group = state(
        writer, entry_id, "勋", time, event, quote,
        f"建立或复用勋制{time}节点。", category="勋制",
        officer="职官总名", sort_order=order,
    )
    result = {}
    for index, title in enumerate(MERIT_RANKS):
        turn = 12 - index
        _, member = state(
            writer, entry_id, title, time, f"勋官十二转之第{turn}转", quote,
            f"原文明列{title}为勋官十二转第{turn}转。",
            category="勋制", officer="勋官", sort_order=order,
        )
        relation(
            writer, entry_id, group, member, "统称与实例", quote,
            f"原文明示{title}属于勋官十二转。",
        )
        result[title] = member
    return group, result


def extract_merit_system():
    entry_id = 515
    writer = W(entry_id)
    western = Q(entry_id, "北朝西魏置柱国，作为无职事而赏勤劳之秩")
    state(
        writer, entry_id, "勋", "北朝西魏",
        "置柱国，作为无职事而赏勤劳之秩", western,
        "建立勋制西魏职源节点。", category="前代职源",
        officer="职官总名", sort_order=53500000,
    )
    zhou = Q(entry_id, "北周建德四年初，置上大将军至柱国七秩")
    state(
        writer, entry_id, "勋", "北周建德四年初",
        "置上大将军至柱国七秩", zhou,
        "建立北周勋制七秩节点。", category="前代职源",
        officer="职官总名", sort_order=57500000,
    )
    sui = Q(entry_id, "隋高祖承北周之制而加改革，设上柱国、柱国至都督十一等")
    state(
        writer, entry_id, "勋", "隋高祖时期",
        "改革北周制度，设上柱国至都督十一等", sui,
        "建立隋代勋制十一等节点。", category="前代职源",
        officer="职官总名", sort_order=58100000,
    )
    roster = Q(entry_id, "唐武德七年（624），定勋官十二转：上柱国、柱国、上护军、护军、上轻车都尉、轻车都尉、上骑都尉、骑都尉、骁骑尉、飞骑尉、云骑尉、武骑尉共十二转")
    merit_group(
        writer, entry_id, "唐武德七年", "定勋官十二转", roster,
        62400000,
    )
    song = Q(entry_id, "北宋勋制沿唐制不变")
    merit_group(
        writer, entry_id, "北宋", "沿唐制设置勋官十二转", song,
        96000000,
    )
    civil = Q(entry_id, "徽宗政和三年二月八日，罢文官带勋转")
    state(
        writer, entry_id, "勋", "北宋徽宗政和三年二月八日",
        "文官停止带勋转，勋制仅部分停止", civil,
        "记录政和三年停止文官带勋转。", category="勋制",
        officer="职官总名", sort_order=111302008,
    )
    military = Q(entry_id, "南宋绍兴三年二月八日，罢武臣赐勋。蕃官如安南、南丹州等仍旧")
    state(
        writer, entry_id, "勋", "南宋高宗绍兴三年二月八日",
        "武臣停止赐勋；安南、南丹州等蕃官仍旧", military,
        "记录绍兴三年停止武臣赐勋而蕃官保留。", category="勋制",
        officer="职官总名", sort_order=113302008,
    )
    writer.commit()


MERIT_DETAILS = {
    516: ("上柱国", 12, "正二品"),
    517: ("柱国", 11, "从二品"),
    518: ("上护军", 10, "正三品"),
    519: ("护军", 9, "从三品"),
    520: ("上轻车都尉", 8, "正四品"),
    521: ("轻车都尉", 7, "从四品"),
}


def extract_merit_details():
    for entry_id, (title, turn, grade) in MERIT_DETAILS.items():
        writer = W(entry_id)
        main = Q(entry_id, F[entry_id]["text"])
        entity = writer.find_entity(title, "官职")
        assert entity is not None
        north = writer.find_timepoint(entity, "北宋")
        assert north is not None
        append_event(
            writer, north,
            f"勋级第{turn}转{'，最高一等' if turn == 12 else ''}；{grade}",
            f"据{title}专条补足北宋勋级位次和官品。",
            category="勋制", officer="勋官", grade=grade,
        )
        cite(writer, "Timepoints", north, entry_id, main, f"补证{title}北宋位次及官品。")

        if entry_id == 516:
            origin = Q(entry_id, "战国楚官名")
            time, event = "先秦战国", "楚国已有上柱国官名"
        elif entry_id == 517:
            origin = Q(entry_id, "战国楚怀王六年（前323），始见置于楚国")
            time, event = "战国楚怀王六年（前323年）", "始见置于楚国"
        elif entry_id == 518:
            origin = Q(entry_id, "秦有护军都尉")
            time, event = "秦代", "已有护军都尉"
        elif entry_id == 519:
            origin = Q(entry_id, "西汉平帝元始元年有护军之名")
            time, event = "西汉平帝元始元年", "已有护军之名"
        elif entry_id == 520:
            origin = Q(entry_id, "西汉武帝时有轻车将军、轻车校尉")
            time, event = "西汉武帝时期", "已有轻车将军、轻车校尉"
        else:
            origin = Q(entry_id, "“轻车”之名，源于西汉武帝置轻车将军、轻车校尉")
            time, event = "西汉武帝时期", "轻车之名源于轻车将军、轻车校尉"
        state(
            writer, entry_id, title, time, event, origin,
            f"建立{title}前代名源节点。", category="前代职源",
            officer="勋官", sort_order=0,
        )
        writer.commit()


def main():
    expected = [
        "嗣王", "郡王", "国公", "郡公", "开国公", "开国郡公",
        "开国县公", "开国侯", "开国伯", "开国子", "开国男",
        "食邑", "食实封", "勋", "上柱国", "柱国", "上护军",
        "护军", "上轻车都尉", "轻车都尉",
    ]
    assert [F[i]["title"] for i in range(502, 522)] == expected
    repair_ten_rank_memberships()
    extract_peerage_entries()
    extract_food_fiefs()
    extract_merit_system()
    extract_merit_details()


if __name__ == "__main__":
    main()
