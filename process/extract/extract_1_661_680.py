#!/usr/bin/env python3
"""提取第一编第661-680条：御书院迁转职掌与翰林医官院。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1.db")
MERGED_DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch1t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db")
)


MEDICAL_DAIFU_RANKS = (
    "和安大夫", "成和大夫", "成安大夫", "成全大夫", "保和大夫", "保安大夫", "翰林良医",
)
MEDICAL_LANG_RANKS = (
    "和安郎", "成和郎", "成安郎", "成全郎", "保和郎", "保安郎", "翰林医官",
)
MEDICAL_EIGHT_RANKS = (
    "翰林医效", "翰林医痊", "翰林医愈", "翰林医证",
    "翰林医诊", "翰林医候", "翰林医学", "翰林祗候",
)
MEDICAL_SPECIALTIES = (
    ("翰林医官局大方脉兼风科医官", "大方脉兼风科", "十五员"),
    ("翰林医官局小方脉科医官", "小方脉科", "四员"),
    ("翰林医官局针科医官", "针科", "二员"),
    ("翰林医官局疮肿科兼折伤科医官", "疮肿科兼折伤科", "二员"),
    ("翰林医官局金镞科兼书禁科医官", "金镞科兼书禁科", "三员"),
    ("翰林医官局口齿科兼咽喉科医官", "口齿科兼咽喉科", "一员"),
)


def repair_dictionary_source():
    """据原书第79-80页恢复#675并修复本批明显OCR。"""
    text674 = "御书院祗应人。专门陪侍皇帝下棋。编制四人（《宋会要·职官》36之96）。"
    text675 = "御书院祗应人。专事拨阮（一种乐器），以侍奉御前生活。编制一名（《宋会要·职官》36之96）。"
    for db_path, table in ((DICT_DB, "chapter1"), (MERGED_DICT_DB, "chapter1t7")):
        with sqlite3.connect(db_path) as conn:
            conn.execute(f"UPDATE {table} SET text=? WHERE id=674", (text674,))
            conn.execute(
                f"UPDATE {table} SET title=?,text=?,fields=NULL WHERE id=675",
                ("擘阮", text675),
            )
            row = conn.execute(f"SELECT text,fields FROM {table} WHERE id=677").fetchone()
            assert row and row[0] and row[1]
            f677 = json.loads(row[1])
            f677["编制"] = f677["编制"].replace("政和三年(1113)", "政和三年（1113）")
            conn.execute(
                f"UPDATE {table} SET text=?,fields=? WHERE id=677",
                (row[0].rstrip("。") + "。", json.dumps(f677, ensure_ascii=False)),
            )


repair_dictionary_source()


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "SELECT title,page,text,fields FROM chapter1 WHERE id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(661, 681)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def field(i, name):
    value = F[i]["fields"][name]
    assert value
    return value


def C(i, name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{name}字段）" if name else "")


def cite(w, table, target_id, i, quotation, decision, name=None, **kwargs):
    source = field(i, name) if name else F[i]["text"]
    assert quotation in source, (i, name, quotation)
    return w.citation(table, target_id, C(i, name), quotation, decision, **kwargs)


def timepoint(
    w, i, entity_id, time, event, quotation, decision, name=None,
    category=None, officer_type=None, grade=None, chain="tail", **cite_kwargs,
):
    tid = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer_type,
        attr_grade=grade, chain=chain,
    )
    cite(w, "Timepoints", tid, i, quotation, decision, name, **cite_kwargs)
    return tid


def relation(
    w, i, subject, object_, kind, quotation, decision, name=None,
    staff_type=None, staff_quota=None, **cite_kwargs,
):
    rid = w.relationship(
        subject, object_, kind, decision, quotation,
        staff_type=staff_type, staff_quota=staff_quota,
    )
    cite(w, "Relationships", rid, i, quotation, decision, name, **cite_kwargs)
    return rid


def find_entity(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def find_tp(w, title, time, type_=None):
    eid = find_entity(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；称谓不另建实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def imperial_library_north_tp(w):
    return find_tp(w, "翰林御书院", "北宋太平兴国七年（982）", "机构")


def imperial_library_south_tp(w):
    return find_tp(w, "翰林御书院", "南宋绍兴十六年（1146）十一月十七日", "机构")


def medical_academy_tp(w):
    return find_tp(w, "翰林医官院", "北宋景德元年（1004）八月", "机构")


def medical_bureau_tp(w):
    return find_tp(w, "翰林医官局", "北宋元丰五年（1082）六月十四日", "机构")


def medical_bureau_south_tp(w):
    return find_tp(w, "翰林医官局", "南宋绍兴二年（1132）", "机构")


def entry661():
    i = 661
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    early = timepoint(
        w, i, eid, "宋初至真宗朝以前", "初隶学士院，由翰林书艺升迁",
        main, "建立翰林待诏早期隶属节点。", category="书写技术官", officer_type="待诏",
        chain="head",
    )
    later = timepoint(
        w, i, eid, "北宋真宗朝以后", "改隶御书院，职掌同御书待诏",
        main, "建立真宗朝后改隶御书院节点。", category="翰林御书院技术官",
        officer_type="待诏",
    )
    relation(w, i, find_tp(w, "学士院", "宋代", "机构"), early, "编制隶属", main, "宋初翰林待诏隶学士院。", staff_type="待诏")
    relation(w, i, imperial_library_north_tp(w), later, "编制隶属", main, "真宗朝后翰林待诏隶御书院。", staff_type="待诏")
    source = find_tp(w, "翰林御书院书艺", "北宋时期（翰林御书院）", "官职")
    relation(w, i, source, later, "前后演变", main, "翰林书艺可升迁翰林待诏。")
    alias_citation(w, i, later, "简称")
    w.commit()


def entry662():
    i = 662
    w = W(i)
    main = F[i]["text"]
    aliases = field(i, "简称")
    eid = w.entity(F[i]["title"], "官职", "正式词头定义御书院书艺学。", quotation=main)
    generic = timepoint(
        w, i, eid, "宋代（具体时间未载）",
        "位次于御书待诏，高于书学祗候，可升翰林待诏，供职十年可出职",
        main, "建立翰林书艺学节点。", category="翰林御书院技术官", officer_type="书艺学",
        grade="出职补保义郎（正九品）",
    )
    south = timepoint(
        w, i, eid, "南宋绍兴十六年（1146）十一月十七日", "御书院复置编制七人",
        aliases, "建立南宋书艺学编制节点。", "简称", category="翰林御书院技术官",
        officer_type="书艺学",
    )
    relation(w, i, imperial_library_north_tp(w), generic, "编制隶属", main, "书艺学隶御书院。", staff_type="书艺学")
    relation(w, i, imperial_library_south_tp(w), south, "编制隶属", aliases, "绍兴复置御书院书艺学七人。", "简称", staff_type="书艺学", staff_quota="七人")
    waiting = find_tp(w, "翰林御书院翰林待诏", "北宋真宗朝以后", "官职")
    relation(w, i, generic, waiting, "前后演变", main, "书艺学可升迁翰林待诏。")
    alias_citation(w, i, generic, "简称")
    w.commit()


def entry663():
    i = 663
    w = W(i)
    main = F[i]["text"]
    aliases = field(i, "简称")
    eid = find_entity(w, F[i]["title"], "官职")
    north = timepoint(
        w, i, eid, "北宋时期（御书院祗候）", "应奉写书人中最低一等，编制十七人",
        aliases, "建立北宋祗候十七人编制。", "简称", category="翰林御书院技术官",
        officer_type="祗候",
    )
    south = find_tp(w, F[i]["title"], "南宋绍兴十六年（1146）十一月十七日", "官职")
    cite(w, "Timepoints", south, i, aliases, "补证南宋书学祗候十四人。", "简称")
    cite(w, "Timepoints", north, i, main, "补证祗候职掌、出职与品位。")
    relation(w, i, imperial_library_north_tp(w), north, "编制隶属", aliases, "北宋御书院祗候十七人。", "简称", staff_type="祗候", staff_quota="十七人")
    relation(w, i, imperial_library_south_tp(w), south, "编制隶属", aliases, "南宋书学祗候十四人。", "简称", staff_type="书学祗候", staff_quota="十四人")
    w.commit()


def migration_rank(i, source_title, title, event):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(title, "官职", "正式词头定义御书院四等迁转职掌。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋时期（御书院四等迁转）", event,
        main, f"建立{title}迁转节点。", category="御书院四等迁转职掌",
    )
    relation(w, i, imperial_library_south_tp(w), tp, "编制隶属", main, f"{title}属御书院迁转职掌。", staff_type="迁转职掌")
    source = find_tp(w, source_title, "南宋时期（御书院四等迁转）", "官职") if i > 664 else find_tp(w, "翰林御书院翰林书艺学", "宋代（具体时间未载）", "官职")
    relation(w, i, source, tp, "前后演变", main, f"{source_title}迁转为{title}。")
    w.commit()


def entry664(): migration_rank(664, "翰林艺学", "着绿待诏", "由翰林艺学迁转，服绿")
def entry665(): migration_rank(665, "着绿待诏", "赐绯待诏", "由着绿待诏迁转，官品未及绯而赐绯")
def entry666(): migration_rank(666, "赐绯待诏", "赐紫待诏", "由赐绯待诏迁转，官品未及紫而赐紫")
def entry667(): migration_rank(667, "赐紫待诏", "庙令差遣待诏", "赐紫待诏在院满十年可迁转")


def entry668():
    i = 668
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    tp = find_tp(w, F[i]["title"], "南宋绍兴十六年（1146）十一月十七日", "官职")
    cite(w, "Timepoints", tp, i, main, "补证书学生实习、无俸、无限员及择优迁补。")
    relation(w, i, imperial_library_south_tp(w), tp, "编制隶属", main, "书学生隶御书院。", staff_type="书学生", staff_quota="不限员（无俸给）")
    target = find_tp(w, "翰林御书院书学祗候", "南宋绍兴十六年（1146）十一月十七日", "官职")
    relation(w, i, tp, target, "前后演变", main, "书学生遇阙经试可择优迁补祗候。")
    alias_citation(w, i, tp, "简称")
    w.commit()


def library_clerk(i, title, rank):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(title, "官职", f"正式词头定义御书院{rank}。", quotation=main)
    north = timepoint(
        w, i, eid, "北宋熙宁四年（1071）十二月以前", f"管理御书院物品，{rank}",
        main, f"建立{title}北宋节点。", category="翰林御书院吏员", officer_type=rank,
        chain="head",
    )
    abolished = timepoint(
        w, i, eid, "北宋熙宁四年（1071）十二月", "罢",
        main, f"建立{title}罢置节点。", category="吏员废罢",
    )
    south = timepoint(
        w, i, eid, "南宋绍兴年间（1131—1162）", "复置",
        main, f"建立{title}南宋复置节点。", category="翰林御书院吏员", officer_type=rank,
    )
    relation(w, i, imperial_library_north_tp(w), north, "编制隶属", main, f"{title}隶御书院。", staff_type=rank)
    relation(w, i, imperial_library_south_tp(w), south, "编制隶属", main, f"南宋复置{title}。", staff_type=rank)
    w.commit()


def entry669(): library_clerk(669, "翰林御书院专知官", "专知官")
def entry670(): library_clerk(670, "翰林御书院副知官", "副知官")


def entry671():
    i = 671
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(F[i]["title"], "官职", "正式词头定义专知官、副知官连称。", quotation=main)
    group = timepoint(
        w, i, eid, "宋代（具体时间未载）", "专知官、副知官连称",
        main, "建立御书院专副连称节点。", category="御书院吏员合称",
    )
    for title in ("翰林御书院专知官", "翰林御书院副知官"):
        instance = find_tp(w, title, "北宋熙宁四年（1071）十二月以前", "官职")
        relation(w, i, group, instance, "统称与实例", main, f"{title}为御书院专副实例。")
    w.commit()


def entry672():
    i = 672
    w = W(i)
    main = F[i]["text"]
    eid = find_entity(w, F[i]["title"], "官职")
    tp = find_tp(w, F[i]["title"], "南宋绍兴十六年（1146）十一月十七日", "官职")
    cite(w, "Timepoints", tp, i, main, "补证押宿官职掌、来源与二人员额。")
    relation(w, i, imperial_library_south_tp(w), tp, "编制隶属", main, "押宿官隶御书院。", staff_type="押宿官", staff_quota="二人")
    source = find_tp(w, "翰林御书院翰林待诏", "北宋真宗朝以后", "官职")
    relation(w, i, source, tp, "前后演变", main, "书写待诏出职后可择补押宿官。")
    alias_citation(w, i, tp, "简称")
    w.commit()


def library_service(i, title, quota, staff_type="祗应人", conflict=False):
    w = W(i)
    main = F[i]["text"]
    eid = w.entity(title, "官职", f"正式词头定义御书院{title}祗应职。", quotation=main)
    tp = timepoint(
        w, i, eid, "南宋绍兴十六年（1146）十一月十七日", main,
        main, f"建立{title}祗应节点。", category="翰林御书院祗应人", officer_type=staff_type,
        note=("本专条记着棋四人；御书院总条记一名" if conflict else None),
        conflict_flag=(1 if conflict else 0),
    )
    relation(
        w, i, imperial_library_south_tp(w), tp, "编制隶属", main, f"{title}隶御书院。",
        staff_type=staff_type, staff_quota=quota,
        note=("本专条记着棋四人；御书院总条记一名" if conflict else None),
        conflict_flag=(1 if conflict else 0),
    )
    w.commit()


def entry673(): library_service(673, "弹琴", "一人")
def entry674(): library_service(674, "着棋", "四人", conflict=True)
def entry675(): library_service(675, "擘阮", "一名")
def entry676(): library_service(676, "点笔班", "一名")


def med_post(w, i, parent, title, time, quotation, staff_type, quota, event=None):
    eid = w.entity(title, "官职", f"医官编制明确列举{title}。", quotation=quotation)
    tp = timepoint(
        w, i, eid, time, event or f"翰林医官院（局）所属{staff_type}",
        quotation, f"建立{title}编制节点。", "编制", category="翰林医官院属员",
        officer_type=staff_type,
    )
    relation(
        w, i, parent, tp, "编制隶属", quotation, f"{title}隶翰林医官院（局）。", "编制",
        staff_type=staff_type, staff_quota=quota,
    )
    return tp


def rank_group(w, i, parent, title, time, quotation, quota, instances):
    eid = w.entity(title, "官职", f"编制将{title}列为职级组。", quotation=quotation)
    group = timepoint(
        w, i, eid, time, f"医官局职级组，共{quota}",
        quotation, f"建立{title}节点。", "编制", category="翰林医官局职级组",
    )
    relation(w, i, parent, group, "编制隶属", quotation, f"{title}隶医官局。", "编制", staff_type="医职阶官", staff_quota=quota)
    for rank in instances:
        rank_e = w.entity(rank, "官职", f"编制明确列举{rank}。", quotation=quotation)
        rank_tp = timepoint(
            w, i, rank_e, time, f"{title}所含医职阶官",
            quotation, f"建立{rank}节点。", "编制", category="翰林医官局医职",
        )
        relation(w, i, group, rank_tp, "统称与实例", quotation, f"{rank}为{title}实例。", "编制")
    return group


def entry677():
    i = 677
    w = W(i)
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duty = field(i, "职掌")
    grade = field(i, "品位")
    roster = field(i, "编制")
    eid = find_entity(w, "翰林医官院", "机构")
    start = timepoint(
        w, i, eid, "北宋景德元年（1004）八月", "翰林医官院之名最早见载；翰林医官使名雍熙二年已见",
        history, "建立翰林医官院最早见载节点。", "职源与沿革", category="翰林院属医疗机构",
        chain="head",
    )
    cite(w, "Timepoints", start, i, duty, "补证宫廷医疗、奉诏诊治及国家医药政令职掌。", "职掌")
    cite(w, "Timepoints", start, i, grade, "补证按七品论罪赎刑及高于太医局的地位。", "品位")
    relation(w, i, find_tp(w, "翰林院", "宋代", "机构"), start, "上下级机构", main, "翰林医官院隶翰林院。")

    bureau_e = find_entity(w, "翰林医官局", "机构")
    existing_south = find_tp(w, "翰林医官局", "南宋时期（1127—1279）", "机构")
    reform = timepoint(
        w, i, bureau_e, "北宋元丰五年（1082）六月十四日", "翰林医官院改称翰林医官局",
        history, "建立元丰改称医官局节点。", "职源与沿革", category="翰林院属医疗机构",
        chain="none",
    )
    zhenghe = timepoint(
        w, i, bureau_e, "北宋政和三年（1113）八月二十五日", "改医职名并立定十四阶、八阶编制",
        roster, "建立政和三年新编制节点。", "编制", category="翰林院属医疗机构", chain="none",
    )
    south = timepoint(
        w, i, bureau_e, "南宋绍兴二年（1132）", "沿置并压缩编制",
        roster, "建立绍兴二年压缩编制节点。", "编制", category="翰林院属医疗机构", chain="none",
    )
    w.relink(reform, "按纪年重排医官局时间链。", prev_id=None, succ_id=zhenghe)
    w.relink(zhenghe, "按纪年重排医官局时间链。", prev_id=reform, succ_id=existing_south)
    w.relink(existing_south, "按纪年重排医官局时间链。", prev_id=zhenghe, succ_id=south)
    w.relink(south, "按纪年重排医官局时间链。", prev_id=existing_south, succ_id=None)
    relation(w, i, start, reform, "前后演变", history, "元丰五年翰林医官院改称医官局。", "职源与沿革")
    relation(w, i, find_tp(w, "翰林院", "南宋时期（1127—1279）", "机构"), south, "上下级机构", main, "南宋翰林医官局仍隶翰林院。")

    north_posts = (
        ("提举翰林医官院", "提举官", None),
        ("翰林医官使", "医官使", "二人"),
        ("翰林医官副使", "医官副使", "二人"),
        ("翰林医官院直院", "直院", "四人"),
        ("尚药奉御", "尚药奉御", "六员"),
        ("翰林医官", "医官", "三十人"),
        ("翰林医学", "医学", "四十人"),
        ("祗候医人", "祗候医人", "十三人"),
    )
    north_tps = {}
    for title, staff_type, quota in north_posts:
        north_tps[title] = med_post(
            w, i, start, title, "北宋前期（仁宗宝元二年制）", roster, staff_type, quota
        )
    early_envoy = timepoint(
        w, i, find_entity(w, "翰林医官使", "官职"), "北宋雍熙二年（985）三月",
        "翰林医官使之名已见置", history, "补足翰林医官使最早见载节点。", "职源与沿革",
        category="翰林医官院属员", officer_type="医官使", chain="head",
    )
    assert early_envoy and north_tps["翰林医官使"]

    daifu = rank_group(w, i, zhenghe, "翰林医官局大夫七阶", "北宋政和三年（1113）", roster, "二十员", MEDICAL_DAIFU_RANKS)
    lang = rank_group(w, i, zhenghe, "翰林医官局正郎七阶", "北宋政和三年（1113）", roster, "三十员", MEDICAL_LANG_RANKS)
    eight = rank_group(w, i, zhenghe, "翰林医官局医效至祗候八阶", "北宋政和三年（1113）", roster, "三百人", MEDICAL_EIGHT_RANKS)
    relation(w, i, north_tps["翰林医官使"], daifu, "前后演变", roster, "旧医官使阶改为大夫七阶。", "编制")
    relation(w, i, north_tps["翰林医官副使"], lang, "前后演变", roster, "旧医官副使阶改为正郎七阶。", "编制")
    relation(w, i, north_tps["翰林医官院直院"], eight, "前后演变", roster, "旧直院至祗候医人诸阶改为医效至祗候八阶。", "编制")
    relation(w, i, north_tps["祗候医人"], eight, "前后演变", roster, "旧直院至祗候医人诸阶改为医效至祗候八阶。", "编制")
    med_post(w, i, zhenghe, "翰林医效", "北宋政和三年（1113）定额", roster, "医职", "七人")
    med_post(w, i, zhenghe, "翰林医痊", "北宋政和三年（1113）定额", roster, "医职", "十人")
    remaining = rank_group(
        w, i, zhenghe, "翰林医官局医愈至祗候六阶", "北宋政和三年（1113）定额",
        roster, "二百八十三人", MEDICAL_EIGHT_RANKS[2:],
    )
    assert daifu and lang and eight and remaining

    rank_group(w, i, south, "翰林医官局大夫七阶", "南宋绍兴二年（1132）", roster, "五员", MEDICAL_DAIFU_RANKS)
    rank_group(w, i, south, "翰林医官局正郎七阶", "南宋绍兴二年（1132）", roster, "四员", MEDICAL_LANG_RANKS)
    med_post(w, i, south, "翰林医效", "南宋绍兴二年（1132）", roster, "医职", "二员")
    med_post(w, i, south, "翰林医痊", "南宋绍兴二年（1132）", roster, "医职", "一员")
    south_six_e = find_entity(w, "翰林医官局医愈至祗候六阶", "官职")
    south_six = timepoint(
        w, i, south_six_e, "南宋绍兴二年（1132）", "医愈至祗候充六类分科医官",
        roster, "建立南宋医愈至祗候六阶分科节点。", "编制", category="翰林医官局职级组",
    )
    relation(
        w, i, south, south_six, "编制隶属", roster, "医愈至祗候六阶隶医官局并分充六科。", "编制",
        staff_type="医职阶官",
    )
    specialty_tps = []
    for title, specialty, quota in MEDICAL_SPECIALTIES:
        specialty_tps.append(med_post(
            w, i, south, title, "南宋绍兴二年（1132）", roster, "分科医官", quota,
            event=f"翰林医愈至祗候充{specialty}",
        ))
    for (title, specialty, _), specialty_tp in zip(MEDICAL_SPECIALTIES, specialty_tps):
        relation(
            w, i, south_six, specialty_tp, "统称与实例", roster,
            f"医愈至祗候六阶分充{specialty}。", "编制",
        )

    for title in ("医师", "御医", "驻泊医官"):
        post_e = w.entity(title, "官职", "编制明确列为医官局差遣职事。", quotation=roster)
        post = timepoint(
            w, i, post_e, "宋代（翰林医官局差遣）", "医官局差遣职事",
            roster, f"建立{title}医官局差遣节点。", "编制", category="翰林医官局差遣",
        )
        relation(w, i, reform, post, "编制隶属", roster, f"{title}为医官局差遣职事。", "编制", staff_type="差遣职事")
    supervisor_e = w.entity("主管翰林医官局", "官职", "南宋编制明确设置主管官。", quotation=roster)
    supervisor = timepoint(
        w, i, supervisor_e, "南宋绍兴二年（1132）", "以内侍充，主管医官局，一员",
        roster, "建立主管医官局编制节点。", "编制", category="翰林医官局主管官",
        officer_type="内侍差遣",
    )
    relation(w, i, south, supervisor, "编制隶属", roster, "主管官督领医官局。", "编制", staff_type="主管官", staff_quota="一员")
    alias_citation(w, i, start, "简称")
    w.commit()


def entry678():
    i = 678
    w = W(i)
    main = F[i]["text"]
    post = find_tp(w, F[i]["title"], "北宋前期（仁宗宝元二年制）", "官职")
    cite(w, "Timepoints", post, i, main, "补证提举官由内侍充及其行政监督职掌。")
    office_e = w.entity("提举翰林医官院所", "机构", "正文明确提举官治所名称。", quotation=main)
    office = timepoint(
        w, i, office_e, "北宋时期（具体时间未载）", "提举翰林医官院官治所",
        main, "建立提举翰林医官院所节点。", category="翰林医官院属所",
    )
    relation(w, i, medical_academy_tp(w), office, "上下级机构", main, "提举翰林医官院所为医官院所属治所。")
    relation(w, i, office, post, "编制隶属", main, "提举官在提举翰林医官院所治事。", staff_type="提举官")
    w.commit()


def entry679():
    i = 679
    w = W(i)
    main = F[i]["text"]
    old = medical_academy_tp(w)
    new = medical_bureau_tp(w)
    cite(w, "Timepoints", new, i, main, "补证元丰五年六月十四日改称医官局。")
    relation(w, i, old, new, "前后演变", main, "元丰五年翰林医官院改称翰林医官局。")
    alias_citation(w, i, new, "简称")
    w.commit()


def entry680():
    i = 680
    w = W(i)
    main = F[i]["text"]
    tp = find_tp(w, F[i]["title"], "南宋绍兴二年（1132）", "官职")
    cite(w, "Timepoints", tp, i, main, "补证绍兴初主管官由入内省内侍充及其行政职掌。")
    relation(w, i, medical_bureau_south_tp(w), tp, "编制隶属", main, "主管官督领翰林医官局。", staff_type="主管官", staff_quota="一员")
    alias_citation(w, i, tp, "别称")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(661, 681)] == [
        "翰林御书院翰林待诏", "翰林御书院翰林书艺学", "翰林御书院书学祗候",
        "着绿待诏", "赐绯待诏", "赐紫待诏", "庙令差遣待诏", "翰林御书院书学生",
        "翰林御书院专知官", "翰林御书院副知官", "御书院专副", "翰林御书院押宿官",
        "弹琴", "着棋", "擘阮", "点笔班", "翰林医官院", "提举翰林医官院",
        "翰林医官局", "主管翰林医官局",
    ]
    assert F[674]["text"].endswith("编制四人（《宋会要·职官》36之96）。")
    assert F[675]["text"].startswith("御书院祗应人。专事拨阮")
    assert "政和三年（1113）" in field(677, "编制") and F[677]["text"].endswith("。")
    entry661(); entry662(); entry663(); entry664(); entry665(); entry666(); entry667(); entry668()
    entry669(); entry670(); entry671(); entry672(); entry673(); entry674(); entry675(); entry676()
    entry677(); entry678(); entry679(); entry680()


if __name__ == "__main__":
    main()
