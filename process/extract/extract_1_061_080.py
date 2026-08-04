#!/usr/bin/env python3
"""提取第一编第61-80条：内官、内命妇、四妃与诸嫔前段。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter1 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(61, 81)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field_name=None):
    source = F[i]["fields"][field_name] if field_name else F[i]["text"]
    assert needle in source, (i, field_name, needle)
    return needle


def field(i, field_name):
    return Q(i, F[i]["fields"][field_name], field_name)


def C(i, field_name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(w, table, target_id, i, quotation, decision, field_name=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field_name), quotation, decision, **kwargs
    )


def add_timepoint(
    w,
    i,
    entity_id,
    time,
    event,
    quotation,
    decision,
    field_name=None,
    category=None,
    grade=None,
    chain="tail",
):
    timepoint_id = w.timepoint(
        entity_id,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        attr_grade=grade,
        chain=chain,
    )
    cite(w, "Timepoints", timepoint_id, i, quotation, decision, field_name)
    return timepoint_id


def add_relation(w, i, subject_tp, object_tp, quotation, decision, field_name=None):
    relation_id = w.relationship(
        subject_tp,
        object_tp,
        "统称与实例",
        decision,
        quotation,
    )
    cite(
        w,
        "Relationships",
        relation_id,
        i,
        quotation,
        decision,
        field_name,
    )
    return relation_id


def find_tp(w, title, time):
    entity_id = w.find_entity(title, "官职")
    assert entity_id, title
    timepoint_id = w.find_timepoint(entity_id, time)
    assert timepoint_id, (title, time)
    return timepoint_id


def cite_regency(i, title, quotation, decision):
    w = W(i)
    target_id = find_tp(w, title, "宋代")
    cite(
        w,
        "Timepoints",
        target_id,
        i,
        quotation,
        decision,
        note="该条为具体人物生平，人物本身不建实体；仅追加其直接证明的临朝职掌事实",
    )
    w.commit()


def entry61():
    i = 61
    quotation = Q(i, "宁宗崩，赵昀继位，是为宋理宗。尊为皇太后，垂帘听政。")
    cite_regency(
        i,
        "皇太后",
        quotation,
        "宁宗杨皇后条补证皇太后在新帝即位后垂帘听政。",
    )


def entry62():
    i = 62
    quotation = Q(i, "恭宗年方四岁，谢太后临朝称制。")
    cite_regency(
        i,
        "太皇太后",
        quotation,
        "理宗谢皇后条补证幼帝即位时太皇太后临朝称制。",
    )


def entry64():
    i = 64
    main = Q(i, "内命妇与宫官通称。")
    history = field(i, "职源与沿革")
    alias = field(i, "别称")

    w = W(i)
    entity_id = w.entity(
        "内官",
        "官职",
        "正文定义为内命妇与宫官的通称，建为官职统称实体。",
        quotation=main,
    )
    add_timepoint(
        w, i, entity_id, "《周礼》所载制度",
        "有夫人、嫔、世妇、女御之位",
        history, "建立内官制度的先秦源流节点。", "职源与沿革",
    )
    add_timepoint(
        w, i, entity_id, "隋朝",
        "始有定制，同时设内命妇位号与六尚宫官",
        history, "建立隋朝内官定制节点。", "职源与沿革",
    )
    add_timepoint(
        w, i, entity_id, "唐代", "沿置隋朝内官制度",
        history, "建立唐代沿置节点。", "职源与沿革",
    )
    add_timepoint(
        w, i, entity_id, "宋初", "内官临时而置，未具规模",
        history, "建立宋初内官制度状态。", "职源与沿革",
    )
    renzong_tp = add_timepoint(
        w, i, entity_id, "宋仁宗朝",
        "定《内命妇品职令》，内官制度始见完整",
        history, "建立仁宗朝内官制度完备节点。", "职源与沿革",
    )
    add_timepoint(
        w, i, entity_id, "宋徽宗政和年间",
        "尚书内省增六司，为一时之制",
        history, "建立徽宗政和年间的增置节点。", "职源与沿革",
    )
    add_timepoint(
        w, i, entity_id, "南宋", "复仁宗朝内官旧制",
        history, "建立南宋恢复仁宗旧制节点。", "职源与沿革",
    )
    cite(
        w, "Timepoints", renzong_tp, i, alias,
        "补证内官别称内职；别称不另建实体。", "别称",
        note="内职是内官别称，不另建实体",
    )

    inner_women = w.entity(
        "内命妇", "官职",
        "内命妇是内官通称所包含的一类正式位号。", quotation=main,
    )
    inner_women_tp = add_timepoint(
        w, i, inner_women, "宋仁宗朝",
        "内命妇为内官的一类",
        main, "建立内命妇作为内官实例的承载节点。",
        category="内官之一类",
    )
    palace_officials = w.entity(
        "宫官", "官职",
        "宫官是内官通称所包含的一类女官。", quotation=main,
    )
    palace_officials_tp = add_timepoint(
        w, i, palace_officials, "宋仁宗朝",
        "宫官为内官的一类",
        main, "建立宫官作为内官实例的承载节点。",
        category="内官之一类",
    )
    add_relation(w, i, renzong_tp, inner_women_tp, main, "内官是内命妇的通称。")
    add_relation(w, i, renzong_tp, palace_officials_tp, main, "内官是宫官的通称。")
    w.commit()


TIANSHENG_TIME = "宋仁宗朝（《天圣内命妇品职令》）"


def create_title_entry(i, origin_specs, song_event, song_quote, category, grade):
    """建立正式位号及其职源、宋代制度节点。"""
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        F[i]["title"],
        "官职",
        "词条正文定义为皇帝妾或内命妇的正式位号。",
        quotation=main,
    )
    for time, event, quotation, field_name in origin_specs:
        add_timepoint(
            w, i, entity_id, time, event, quotation,
            f"建立{F[i]['title']}的{time}职源或沿革节点。", field_name,
        )
    song_tp = add_timepoint(
        w, i, entity_id, TIANSHENG_TIME, song_event, song_quote,
        f"建立{F[i]['title']}的宋代内命妇制度节点。",
        category=category, grade=grade,
    )
    if main != song_quote:
        cite(
            w, "Timepoints", song_tp, i, main,
            f"补证{F[i]['title']}的位号定义。",
        )
    w.commit()


def entry66():
    i = 66
    origin = field(i, "职源")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [("南朝宋孝武帝孝建三年（456）", "始置贵妃位号", origin, "职源")],
        "内命妇夫人阶四妃之首，正一品，秩视三公",
        rank, "夫人阶", "正一品",
    )
    w = W(i)
    tp = find_tp(w, "贵妃", TIANSHENG_TIME)
    aliases = field(i, "省称与别名")
    cite(w, "Timepoints", tp, i, aliases, "补证贵妃的省称与雅称，均不另建实体。", "省称与别名")
    w.commit()


def entry67():
    i = 67
    origin = field(i, "职源")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [("三国魏明帝曹叡时", "始置淑妃名号", origin, "职源")],
        "内命妇夫人阶四妃之一，正一品，秩视三公",
        rank, "夫人阶", "正一品",
    )
    w = W(i)
    tp = find_tp(w, "淑妃", TIANSHENG_TIME)
    aliases = field(i, "简称与别名")
    cite(w, "Timepoints", tp, i, aliases, "补证淑妃的简称与雅称，均不另建实体。", "简称与别名")
    w.commit()


def entry68():
    i = 68
    origin = field(i, "职源")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [("隋炀帝时", "三夫人中始置德妃", origin, "职源")],
        "内命妇夫人阶四妃之一，正一品，秩视三公",
        rank, "夫人阶", "正一品",
    )
    w = W(i)
    tp = find_tp(w, "德妃", TIANSHENG_TIME)
    alias = field(i, "简称")
    cite(w, "Timepoints", tp, i, alias, "补证德妃简称妃；简称不另建实体。", "简称")
    w.commit()


def entry69():
    i = 69
    origin = field(i, "职源")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [("唐代", "在隋三夫人之后新添贤妃，始立四妃", origin, "职源")],
        "内命妇夫人阶四妃之末，正一品，秩视三公",
        rank, "夫人阶", "正一品",
    )
    w = W(i)
    tp = find_tp(w, "贤妃", TIANSHENG_TIME)
    aliases = field(i, "简称与别名")
    cite(w, "Timepoints", tp, i, aliases, "补证贤妃的简称与雅称，均不另建实体。", "简称与别名")
    w.commit()


def entry70():
    i = 70
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "皇妃", "官职",
        "正文定义为四妃通称；虽非独立位号，但是正式统称。", quotation=main,
    )
    group_tp = add_timepoint(
        w, i, entity_id, "宋代", "贵妃、淑妃、德妃、贤妃之通称，非独立位号",
        main, "建立皇妃的宋代统称状态。", category="四妃通称",
    )
    for title in ("贵妃", "淑妃", "德妃", "贤妃"):
        add_relation(
            w, i, group_tp, find_tp(w, title, TIANSHENG_TIME), main,
            f"皇妃是{title}等四妃的通称，{title}为其实例。",
        )
    w.commit()


def entry71():
    i = 71
    history = field(i, "职源与沿革")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [
            ("唐德宗贞元六年（790）七月", "始设太仪，原用于封公主母", history, "职源与沿革"),
            ("宋真宗景德二年（1005）七月", "以太仪封赠雍王元份之母任氏", history, "职源与沿革"),
        ],
        "内命妇嫔阶之首，正二品",
        rank, "嫔阶", "正二品",
    )


def entry73():
    i = 73
    history = field(i, "职源与沿革")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [
            ("晋武帝时", "始置淑仪", history, "职源与沿革"),
            ("宋真宗大中祥符六年（1013）", "宋朝始置淑仪", history, "职源与沿革"),
        ],
        "内命妇嫔阶，初从一品，后改正二品",
        rank, "嫔阶", "初从一品，后改正二品",
    )
    w = W(i)
    tp = find_tp(w, "淑仪", TIANSHENG_TIME)
    alias = field(i, "别名")
    cite(w, "Timepoints", tp, i, alias, "补证淑仪的嫔阶通称；通称不另建实体。", "别名")
    w.commit()


def entry74():
    i = 74
    origin = field(i, "职源")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [("宋仁宗乾兴元年（1022）四月", "特置贵仪，用于加恩太宗臧淑仪", origin, "职源")],
        "内命妇嫔阶，位于淑仪之上，从一品",
        rank, "嫔阶", "从一品",
    )


def entry75():
    i = 75
    history = field(i, "职源与沿革")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [
            ("南朝宋明帝泰始三年（467）", "始置淑容", history, "职源与沿革"),
            ("宋真宗大中祥符六年（1013）", "宋朝始置淑容", history, "职源与沿革"),
        ],
        "内命妇嫔阶，初从一品，后改正二品",
        rank, "嫔阶", "初从一品，后改正二品",
    )


def entry76():
    i = 76
    history = field(i, "职源与沿革")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [
            ("隋炀帝时", "始置顺仪，为九嫔之一", history, "职源与沿革"),
            ("宋真宗大中祥符六年（1013）", "宋朝始置顺仪", history, "职源与沿革"),
        ],
        "内命妇嫔阶，正二品，位在淑容之下、顺容之上",
        rank, "嫔阶", "正二品",
    )


def entry77():
    i = 77
    history = field(i, "职源与沿革")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [
            ("隋炀帝时", "始置顺容，为九嫔之一", history, "职源与沿革"),
            ("宋真宗大中祥符六年（1013）", "宋朝始置顺容", history, "职源与沿革"),
        ],
        "内命妇嫔阶，正二品，位在顺仪之下、婉仪之上",
        rank, "嫔阶", "正二品",
    )


def entry78():
    i = 78
    history = field(i, "职源与沿革")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [
            ("北齐武成帝河清年间（562—565）", "始见婉仪", history, "职源与沿革"),
            ("宋真宗大中祥符六年（1013）", "宋朝始置婉仪", history, "职源与沿革"),
        ],
        "内命妇嫔阶，初从一品，后改正二品，位列婉容之上",
        rank, "嫔阶", "初从一品，后改正二品",
    )


def entry79():
    i = 79
    origin = field(i, "职源")
    rank = field(i, "品阶")
    create_title_entry(
        i,
        [("宋真宗大中祥符六年（1013）", "宋朝始置婉容", origin, "职源")],
        "内命妇嫔阶，初从一品，后改正二品，位列昭仪之上",
        rank, "嫔阶", "初从一品，后改正二品",
    )


def entry80():
    i = 80
    origin = field(i, "职源")
    rank = field(i, "品阶")
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        "昭仪", "官职", "词条正文定义为皇帝妾的正式名号。", quotation=main,
    )
    add_timepoint(
        w, i, entity_id, "西汉元帝永光二年（前42年）", "始置昭仪",
        origin, "建立昭仪的西汉职源节点。", "职源",
    )
    add_timepoint(
        w, i, entity_id, "宋初", "沿唐制设昭仪，位于四妃之下、诸嫔之上",
        origin, "建立昭仪的宋初位次节点。", "职源", "嫔阶", "正二品",
    )
    song_tp = add_timepoint(
        w, i, entity_id, "宋真宗大中祥符六年（1013）",
        "增置淑仪等六嫔后，昭仪位于婉容之下、昭容之上",
        origin, "建立大中祥符六年后昭仪位次变化节点。", "职源", "嫔阶", "正二品",
    )
    cite(w, "Timepoints", song_tp, i, rank, "补证昭仪属嫔阶、正二品。", "品阶")
    w.commit()


def entry65():
    """在专条位号节点建立后，补齐内命妇的全部明列实例。"""
    i = 65
    main = F[i]["text"]
    tian_sheng_quote = Q(
        i,
        "仁宗《天圣内命妇品职令》定制，内命妇分五等："
        "一、夫人（贵妃、淑妃、德妃、贤妃）；二、嫔（太仪、贵仪、淑仪、淑容、"
        "顺仪、顺容、婉仪、婉容、昭仪、昭容、昭媛、修仪、修容、修媛、充仪、充容、充媛）；"
        "三、婕妤；四、美人；五、才人、贵人。",
    )
    huizong_quote = Q(i, "徽宗朝又见置宝林、御女、采女")
    categories = {
        "夫人阶": ("贵妃", "淑妃", "德妃", "贤妃"),
        "嫔阶": (
            "太仪", "贵仪", "淑仪", "淑容", "顺仪", "顺容", "婉仪", "婉容", "昭仪",
            "昭容", "昭媛", "修仪", "修容", "修媛", "充仪", "充容", "充媛",
        ),
        "婕妤阶": ("婕妤",),
        "美人阶": ("美人",),
        "才人、贵人阶": ("才人", "贵人"),
    }

    w = W(i)
    entity_id = w.find_entity("内命妇", "官职")
    assert entity_id
    group_tp = w.timepoint(
        entity_id,
        TIANSHENG_TIME,
        "《天圣内命妇品职令》定内命妇五等及其位号",
        "建立天圣内命妇品职令的分等状态。",
        tian_sheng_quote,
        attr_category="内命妇总称",
    )
    cite(w, "Timepoints", group_tp, i, main, "补证内命妇是皇帝妃嫔至贵人的位号总称。")

    for category, titles in categories.items():
        for title in titles:
            child_entity = w.entity(
                title, "官职",
                f"《天圣内命妇品职令》明列{title}为内命妇位号。",
                quotation=tian_sheng_quote,
            )
            child_tp = w.timepoint(
                child_entity,
                TIANSHENG_TIME,
                f"《天圣内命妇品职令》列为{category}",
                f"建立{title}在天圣品职令中的{category}成员状态。",
                tian_sheng_quote,
                attr_category=category,
            )
            cite(
                w, "Timepoints", child_tp, i, tian_sheng_quote,
                f"天圣品职令明列{title}为{category}内命妇。",
            )
            add_relation(
                w, i, group_tp, child_tp, tian_sheng_quote,
                f"内命妇为总称，{title}为天圣品职令明列的{category}实例。",
            )

    huizong_tp = add_timepoint(
        w, i, entity_id, "宋徽宗朝", "内命妇又见置宝林、御女、采女",
        huizong_quote, "建立徽宗朝内命妇增见位号节点。",
        category="内命妇总称",
    )
    for title in ("宝林", "御女", "采女"):
        child_entity = w.entity(
            title, "官职", f"正文明言徽宗朝又见置{title}位号。", quotation=huizong_quote,
        )
        child_tp = w.timepoint(
            child_entity, "宋徽宗朝", f"又见置{title}为内命妇位号",
            f"建立{title}在徽宗朝的内命妇位号节点。", huizong_quote,
            attr_category="内命妇位号",
        )
        cite(w, "Timepoints", child_tp, i, huizong_quote, f"徽宗朝又见置{title}。")
        add_relation(
            w, i, huizong_tp, child_tp, huizong_quote,
            f"内命妇为总称，{title}为徽宗朝又见的实例。",
        )
    w.commit()


SKIPPED_ENTRIES = {
    63: "具体人物的册立、入元与出家生平，无新的制度性职掌",
    72: "空 placeholder 词条",
}


def main():
    assert [F[i]["title"] for i in range(61, 81)] == [
        "宁宗杨皇后", "理宗谢皇后", "度宗全皇后", "内官", "内命妇",
        "贵妃", "淑妃", "德妃", "贤妃", "皇妃", "太仪", "内命妇名号",
        "淑仪", "贵仪", "淑容", "顺仪", "顺容", "婉仪", "婉容", "昭仪",
    ]
    entry61()
    entry62()
    entry64()
    entry66()
    entry67()
    entry68()
    entry69()
    entry70()
    entry71()
    entry73()
    entry74()
    entry75()
    entry76()
    entry77()
    entry78()
    entry79()
    entry80()
    entry65()
    for i, reason in SKIPPED_ENTRIES.items():
        print(f"#{i} {F[i]['title']}: skipped ({reason})")


if __name__ == "__main__":
    main()
