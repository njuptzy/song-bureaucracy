#!/usr/bin/env python3
"""提取第一编第321-340条：宗女夫婿封号、亲王府及王府官属。"""

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
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch1t7.db"),
)


def repair_dictionary_source():
    """据原书第38-41页影像修正确定无疑的OCR字误。"""
    replacements = {
        323: {
            "职源": (
                ("驴马都尉之名", "驸马都尉之名"),
                ("《嫌真子录》", "《嬾真子录》"),
            ),
            "简称与别名": (
                ("① 驴马。", "① 驸马。"),
                ("吴元泉谨谦逊", "吴元扆谨谦逊"),
            ),
        },
        326: {
            "省称与别名": (("以爵则臥于五等", "以爵则躐于五等"),),
        },
        334: {
            "品位": (("不见其官品《宋史·职官志》8）", "不见其官品（《宋史·职官志》8）"),),
        },
        336: {
            "职源与沿革": (("诸王府置谘仪参军事", "诸王府置谘议参军事"),),
            "简称": (
                ("① 谩议。", "① 谘议。"),
                ("② 谢。", "② 谘。"),
            ),
        },
    }
    for db_path, table in (
        (DICT_DB, "chapter1"),
        (MERGED_DICT_DB, "chapter1t7"),
    ):
        with sqlite3.connect(db_path) as conn:
            for entry_id, field_replacements in replacements.items():
                row = conn.execute(
                    f"SELECT fields FROM {table} WHERE id=?", (entry_id,)
                ).fetchone()
                assert row and row[0], (db_path, table, entry_id)
                fields = json.loads(row[0])
                changed = False
                for name, pairs in field_replacements.items():
                    value = fields[name]
                    for old, new in pairs:
                        if old in value:
                            value = value.replace(old, new)
                            changed = True
                        else:
                            assert new in value, (entry_id, name, old, new, value)
                    fields[name] = value
                if changed:
                    conn.execute(
                        f"UPDATE {table} SET fields=? WHERE id=?",
                        (json.dumps(fields, ensure_ascii=False), entry_id),
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


F = {i: load(i) for i in range(321, 341)}


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
    source = F[i]["fields"][name] if name else F[i]["text"]
    assert quotation in source, (i, name, quotation)
    return w.citation(table, target_id, C(i, name), quotation, decision, **kwargs)


def timepoint(
    w, i, entity_id, time, event, quotation, decision, name=None,
    category=None, officer_type=None, grade=None, chain="tail",
):
    target_id = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer_type,
        attr_grade=grade, chain=chain,
    )
    cite(w, "Timepoints", target_id, i, quotation, decision, name)
    return target_id


def relation(
    w, i, subject, object_, kind, quotation, decision, name=None,
    staff_type=None, staff_quota=None,
):
    target_id = w.relationship(
        subject, object_, kind, decision, quotation,
        staff_type=staff_type, staff_quota=staff_quota,
    )
    cite(w, "Relationships", target_id, i, quotation, decision, name)
    return target_id


def find_entity(w, title, type_="官职"):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    return entity_id


def find_tp(w, title, time, type_="官职"):
    entity_id = find_entity(w, title, type_)
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time, type_)
    return target_id


def alias_citation(w, i, tp_id, name):
    quotation = field(i, name)
    cite(
        w, "Timepoints", tp_id, i, quotation,
        f"补证{F[i]['title']}的{name}；不另建称谓实体。", name,
        note=f"{name}仅作称谓证据，不另建实体",
    )


def palace(w):
    return find_tp(w, "亲王府", "宋代（具体时间未载）", "机构")


def palace_group(w):
    return find_tp(w, "亲王府官属", "宋代（具体时间未载）")


def palace_relation(w, i, tp_id, quotation, name=None, staff_type=None):
    return relation(
        w, i, palace(w), tp_id, "编制隶属", quotation,
        f"{F[i]['title']}为亲王府官属。", name, staff_type=staff_type,
    )


def entry321():
    i = 321
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    duties = field(i, "职能")
    w = W(i)
    entity_id = w.entity("县主", "官职", "正文定义县主为亲王女封号。", quotation=main)
    timepoint(w, i, entity_id, "汉代", "已有县主封号，授功臣之女", history, "建立县主汉代起源节点。", "职源与沿革")
    timepoint(w, i, entity_id, "唐代", "亲王女封县主", history, "建立唐代县主制度节点。", "职源与沿革")
    song_tp = timepoint(
        w, i, entity_id, "北宋（政和三年改称前）", "亲王女封县主",
        history, "建立北宋县主封号节点。", "职源与沿革", category="亲王女封号",
    )
    old_end = timepoint(
        w, i, entity_id, "宋徽宗政和三年（1113）闰四月", "县主改称族姬",
        history, "建立县主改称族姬节点。", "职源与沿革", category="改称",
    )
    restored = timepoint(
        w, i, entity_id, "宋高宗建炎元年（1127）六月", "恢复县主称号",
        history, "建立建炎复称县主节点。", "职源与沿革", category="亲王女封号",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证县主为亲王女封号。")
    cite(w, "Timepoints", song_tp, i, duties, "补证宋代县主所封对象。", "职能")
    alias_citation(w, i, song_tp, "别名")
    renamed = w.entity("族姬", "官职", "沿革字段明确县主改称族姬。", quotation=history)
    start = timepoint(
        w, i, renamed, "宋徽宗政和三年（1113）闰四月", "由县主改称，开始施行",
        history, "建立族姬开始节点。", "职源与沿革", category="亲王女封号",
    )
    end = timepoint(
        w, i, renamed, "宋高宗建炎元年（1127）六月", "族姬称号停用，复称县主",
        history, "建立族姬停用节点。", "职源与沿革", category="废罢称号",
    )
    relation(w, i, old_end, start, "前后演变", history, "政和三年县主改称族姬。", "职源与沿革")
    relation(w, i, end, restored, "前后演变", history, "建炎元年族姬复称县主。", "职源与沿革")
    w.commit()


def entry322():
    i = 322
    main = F[i]["text"]
    w = W(i)
    start = find_tp(w, "族姬", "宋徽宗政和三年（1113）闰四月")
    end = find_tp(w, "族姬", "宋高宗建炎元年（1127）六月")
    old_end = find_tp(w, "县主", "宋徽宗政和三年（1113）闰四月")
    restored = find_tp(w, "县主", "宋高宗建炎元年（1127）六月")
    cite(w, "Timepoints", start, i, main, "族姬专条补证称号开始。")
    cite(w, "Timepoints", end, i, main, "族姬专条补证称号结束。")
    relation(w, i, old_end, start, "前后演变", main, "族姬专条补证县主改名。")
    relation(w, i, end, restored, "前后演变", main, "族姬专条施行终点补证复称县主。")
    w.commit()


def entry323():
    i = 323
    main = F[i]["text"]
    origin = field(i, "职源")
    rank = field(i, "品位")
    w = W(i)
    entity_id = w.entity("驸马都尉", "官职", "正文定义驸马都尉为帝婿官号。", quotation=main)
    timepoint(w, i, entity_id, "汉武帝时期", "掌御马，并非皇帝女婿", origin, "建立驸马都尉汉代职源节点。", "职源")
    timepoint(w, i, entity_id, "三国魏时期", "何晏尚魏公主拜驸马都尉，始用于帝婿", origin, "建立驸马都尉转为帝婿官号节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "大长公主、长公主、公主之夫均授此官号，除责罚外终身不变",
        main, "建立宋代驸马都尉节点。", category="帝婿官号",
        officer_type="大长公主、长公主、公主之夫", grade="从五品",
    )
    cite(w, "Timepoints", song_tp, i, rank, "补证驸马都尉品位与婚后迁官规则。", "品位")
    cite(w, "Timepoints", song_tp, i, field(i, "位遇"), "补证驸马都尉恩遇。", "位遇")
    alias_citation(w, i, song_tp, "简称与别名")
    w.commit()


def simple_husband_title(i, title, category, aliases=None):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(title, "官职", f"正文定义{title}为宗女之夫官称。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", main,
        main, f"建立{title}宋代节点。", category=category,
    )
    if aliases:
        alias_citation(w, i, tp_id, aliases)
    w.commit()


def entry324():
    simple_husband_title(324, "郡马", "郡主之夫官称", "别称")


def entry325():
    simple_husband_title(325, "县马", "县主之夫官称")


def entry326():
    i = 326
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    rank = field(i, "官品")
    w = W(i)
    entity_id = w.entity("国王", "官职", "正文定义国王为官名、爵名。", quotation=main)
    timepoint(w, i, entity_id, "西汉时期", "皇帝之下始封国王", origin, "建立国王爵号起源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）",
        "皇帝叔伯、兄弟及诸子封王，开亲王府而无治国之实",
        origin, "建立宋代国王爵位节点。", "职源", category="亲王爵位", grade="正一品",
    )
    cite(w, "Timepoints", song_tp, i, duties, "补证宋代国王职掌与遥领差遣。", "职掌")
    cite(w, "Timepoints", song_tp, i, rank, "补证国王官品。", "官品")
    alias_citation(w, i, song_tp, "省称与别名")
    w.commit()


def entry327():
    i = 327
    main = F[i]["text"]
    origin = field(i, "职源")
    staffing = field(i, "编制")
    w = W(i)
    entity_id = w.entity("亲王府", "机构", "正文定义亲王府为官司。", quotation=main)
    timepoint(w, i, entity_id, "唐代", "官品令正式称王府为亲王府", origin, "建立亲王府唐代职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "亲王开府置官，官属不备置、无定员、因时而置",
        staffing, "建立宋代亲王府节点。", "编制", category="亲王府署",
    )
    cite(w, "Timepoints", song_tp, i, main, "补证亲王府为官司。")
    alias_citation(w, i, song_tp, "简称与别名")
    group = w.entity("亲王府官属", "官职", "编制字段明确列举宋代亲王府官属。", quotation=staffing)
    group_tp = timepoint(
        w, i, group, "宋代（具体时间未载）", "傅、长史、司马、谘议参军事、友、记室参军事、翊善、侍读、侍讲、教授、小学教授等的统称",
        staffing, "建立亲王府官属统称节点。", "编制", category="王府官属统称",
    )
    relation(
        w, i, song_tp, group_tp, "编制隶属", staffing,
        "亲王府官属为亲王府编制，诸官不备置、无定员、因时而置。", "编制",
        staff_type="不备置、无定员、因时而置",
    )
    w.commit()


def entry328():
    i = 328
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("亲王诸宫司", "机构", "正文定义亲王诸宫司为官司。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "总掌亲王府出纳事务",
        main, "建立亲王诸宫司宋代节点。", category="亲王府事务机构",
    )
    relation(w, i, palace(w), tp_id, "上下级机构", main, "亲王诸宫司掌亲王府出纳，为亲王府下属机构。")
    w.commit()


def palace_admin_post(i, event, officer_type):
    main = F[i]["text"]
    w = W(i)
    parent = find_tp(w, "亲王诸宫司", "宋代（具体时间未载）", "机构")
    entity_id = w.entity(F[i]["title"], "官职", f"正文定义{F[i]['title']}为诸宫司主管官。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", event, main,
        f"建立{F[i]['title']}宋代节点。", category="亲王诸宫司主管官",
        officer_type=officer_type,
    )
    relation(
        w, i, parent, tp_id, "编制隶属", main,
        f"{F[i]['title']}为亲王诸宫司主管官。", staff_type=officer_type,
    )
    w.commit()


def entry329():
    palace_admin_post(329, "主管亲王诸宫司，由武臣诸司使充任", "武臣诸司使")


def entry330():
    palace_admin_post(330, "诸宫司使缺员时设置，主管诸宫司，由内侍充任", "内侍")


def entry331():
    palace_admin_post(331, "与都大管勾同为诸宫司主管官，由内侍充任", "内侍")


def entry332():
    i = 332
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity("亲王夫人", "官职", "正文定义亲王夫人为内命妇。", quotation=main)
    timepoint(w, i, entity_id, "西汉时期", "皇孙妻称夫人", origin, "建立亲王夫人前身称谓节点。", "职源")
    timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "亲王妻不称王妃而称夫人",
        origin, "建立宋代亲王夫人节点。", "职源", category="内命妇",
    )
    w.commit()


def entry333():
    i = 333
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity("亲王府傅", "官职", "正文定义亲王府傅为王府官。", quotation=main)
    timepoint(w, i, entity_id, "西汉时期", "诸侯王官属置太傅", origin, "建立王傅汉代职源节点。", "职源")
    timepoint(w, i, entity_id, "西汉成帝时", "诸侯王太傅改称傅", origin, "建立王傅改称节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋代（具体时间未载）", "有其官而未见除授，名义辅导亲王",
        origin, "建立宋代亲王府傅节点。", "职源", category="亲王府官属", grade="正三品",
    )
    cite(w, "Timepoints", song_tp, i, field(i, "职掌"), "补证亲王府傅职掌。", "职掌")
    cite(w, "Timepoints", song_tp, i, field(i, "官品"), "补证亲王府傅官品。", "官品")
    alias_citation(w, i, song_tp, "简称")
    palace_relation(w, i, song_tp, origin, "职源")
    w.commit()


def entry334():
    i = 334
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    w = W(i)
    entity_id = w.entity("亲王府长史", "官职", "正文定义亲王府长史为王府官。", quotation=main)
    timepoint(w, i, entity_id, "三国吴时期", "长沙桓王府始有长史属官", history, "建立王府长史职源节点。", "职源与沿革")
    song_tp = timepoint(
        w, i, entity_id, "宋代（亲王判府时，具体年月未载）", "或置长史，不常置，可掌王府僚属及府中钱谷、讼牒",
        history, "建立宋代亲王府长史节点。", "职源与沿革", category="亲王府官属", grade="从四品上",
    )
    later = timepoint(
        w, i, entity_id, "宋孝宗淳熙元年（1174）", "魏王府见置长史苏谔",
        field(i, "简称"), "建立淳熙元年王府长史实见节点。", "简称", category="亲王府官属",
    )
    cite(w, "Timepoints", song_tp, i, field(i, "职掌"), "补证王府长史职掌。", "职掌")
    cite(w, "Timepoints", song_tp, i, field(i, "品位"), "补证王府长史班序和官品。", "品位")
    cite(w, "Timepoints", later, i, field(i, "简称"), "补证王府长史简称与实见。", "简称", note="长史为简称，不另建实体")
    palace_relation(w, i, song_tp, history, "职源与沿革")
    w.commit()


def entry335():
    i = 335
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity("亲王府司马", "官职", "正文定义亲王府司马为王府官。", quotation=main)
    timepoint(w, i, entity_id, "北魏时期", "始置王府司马", origin, "建立王府司马职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋初", "沿置，亲王判府时与长史同掌钱谷、讼牒",
        origin, "建立宋初亲王府司马节点。", "职源", category="亲王府官属", grade="从四品下",
    )
    later = timepoint(
        w, i, entity_id, "宋孝宗淳熙元年（1174）", "魏王府见置司马陈苍",
        field(i, "简称"), "建立淳熙元年王府司马实见节点。", "简称", category="亲王府官属",
    )
    cite(w, "Timepoints", song_tp, i, field(i, "职掌"), "补证王府司马职掌。", "职掌")
    cite(w, "Timepoints", song_tp, i, field(i, "品位"), "补证王府司马官品和班序。", "品位")
    cite(w, "Timepoints", later, i, field(i, "简称"), "补证司马简称与实见。", "简称", note="司马为简称，不另建实体")
    palace_relation(w, i, song_tp, origin, "职源")
    w.commit()


def entry336():
    i = 336
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    w = W(i)
    entity_id = w.entity("亲王府谘议参军", "官职", "正文定义谘议参军为王府官。", quotation=main)
    timepoint(w, i, entity_id, "南朝至隋唐", "诸王府置谘议参军事", history, "建立王府谘议职源节点。", "职源与沿革")
    song_tp = timepoint(
        w, i, entity_id, "宋初", "沿置以备王府官僚，实无明确职责",
        history, "建立宋初亲王府谘议参军节点。", "职源与沿革", category="亲王府官属", grade="正五品上",
    )
    timepoint(
        w, i, entity_id, "宋真宗朝以后", "罕置",
        history, "建立真宗朝以后罕置节点。", "职源与沿革", category="亲王府官属",
    )
    cite(w, "Timepoints", song_tp, i, field(i, "职掌"), "补证宋代谘议参军职掌。", "职掌")
    cite(w, "Timepoints", song_tp, i, field(i, "官品"), "补证谘议参军官品。", "官品")
    alias_citation(w, i, song_tp, "简称")
    palace_relation(w, i, song_tp, history, "职源与沿革")
    w.commit()


def entry337():
    i = 337
    main = F[i]["text"]
    origin = field(i, "职源")
    w = W(i)
    entity_id = w.entity("亲王府记室参军事", "官职", "正文定义记室参军事为王府官。", quotation=main)
    timepoint(w, i, entity_id, "南朝梁时期", "诸王府置记室参军", origin, "建立王府记室职源节点。", "职源")
    song_tp = timepoint(
        w, i, entity_id, "宋初", "沿置，备王府官僚，可兼南、北宫教授",
        origin, "建立宋初王府记室参军事节点。", "职源", category="亲王府官属", grade="从六品上",
    )
    timepoint(
        w, i, entity_id, "北宋元祐时期", "官品令定为从八品",
        field(i, "官品"), "建立元祐官品节点。", "官品", category="亲王府官属", grade="从八品",
    )
    old_end = timepoint(
        w, i, entity_id, "北宋政和年间", "去参军二字，改称记室",
        origin, "建立政和改称记室节点。", "职源", category="改称",
    )
    restored = timepoint(
        w, i, entity_id, "南宋", "恢复王府记室参军之称",
        origin, "建立南宋复称记室参军节点。", "职源", category="亲王府官属",
    )
    cite(w, "Timepoints", song_tp, i, field(i, "职掌"), "补证王府记室参军事职掌。", "职掌")
    alias_citation(w, i, song_tp, "简称")
    renamed = w.entity("亲王府记室", "官职", "职源明确政和中去参军二字，只称记室。", quotation=origin)
    start = timepoint(
        w, i, renamed, "北宋政和年间", "由亲王府记室参军事改称",
        origin, "建立亲王府记室开始节点。", "职源", category="亲王府官属",
    )
    end = timepoint(
        w, i, renamed, "南宋", "记室称号停用，复称王府记室参军",
        origin, "建立亲王府记室停用节点。", "职源", category="废罢称号",
    )
    relation(w, i, old_end, start, "前后演变", origin, "政和中记室参军事改称记室。", "职源")
    relation(w, i, end, restored, "前后演变", origin, "南宋恢复王府记室参军之称。", "职源")
    palace_relation(w, i, song_tp, origin, "职源")
    palace_relation(w, i, start, origin, "职源")
    w.commit()


def entry338():
    i = 338
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("记谘", "官职", "正文定义记谘为记室、谘议的连称官语。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋初（具体年月未载）", "御史中丞或侍御史上任仪式判案后所署官语，为记室、谘议参军连称",
        main, "建立记谘官语节点。", category="官职连称",
    )
    relation(
        w, i, tp_id, find_tp(w, "亲王府记室参军事", "宋初"), "统称与实例", main,
        "记谘为记室参军与谘议参军连称，记室参军为其中一项。",
    )
    relation(
        w, i, tp_id, find_tp(w, "亲王府谘议参军", "宋初"), "统称与实例", main,
        "记谘为记室参军与谘议参军连称，谘议参军为其中一项。",
    )
    w.commit()


def entry339():
    i = 339
    main = F[i]["text"]
    origin = field(i, "职源")
    duties = field(i, "职掌")
    w = W(i)
    entity_id = w.entity("亲王府翊善", "官职", "正文定义亲王府翊善为王府官。", quotation=main)
    start = timepoint(
        w, i, entity_id, "宋太宗太平兴国四年（979）", "始置，为王府属官，讲经史并谕亲王以义理",
        origin, "建立亲王府翊善始置节点。", "职源", category="亲王府官属", grade="从七品",
    )
    timepoint(
        w, i, entity_id, "宋孝宗淳熙末（1189）", "黄裳任嘉王府专职翊善，为一时之制",
        duties, "建立淳熙末专职翊善节点。", "职掌", category="亲王府官属", officer_type="专职",
    )
    timepoint(
        w, i, entity_id, "宋光宗绍熙二年（1191）", "黄裳以起居舍人兼翊善，此后不复有专职",
        duties, "建立绍熙二年恢复兼官节点。", "职掌", category="亲王府官属", officer_type="兼官",
    )
    cite(w, "Timepoints", start, i, duties, "补证亲王府翊善职掌与任职方式。", "职掌")
    cite(w, "Timepoints", start, i, field(i, "官品"), "补证亲王府翊善官品。", "官品")
    alias_citation(w, i, start, "简称")
    palace_relation(w, i, start, origin, "职源")
    w.commit()


def entry340():
    i = 340
    main = F[i]["text"]
    history = field(i, "职源与沿革")
    w = W(i)
    entity_id = w.entity("亲王府侍讲", "官职", "正文定义亲王府侍讲为王府官。", quotation=main)
    start = timepoint(
        w, i, entity_id, "宋太宗太平兴国四年（979）", "始置，为皇子讲经史，职在训导",
        history, "建立亲王府侍讲始置节点。", "职源与沿革", category="亲王府官属", grade="从七品",
    )
    old_1080 = timepoint(
        w, i, entity_id, "宋神宗元丰三年（1080）", "改称王府讲书，侍讲名暂止",
        history, "建立元丰三年侍讲改称节点。", "职源与沿革", category="改称",
    )
    restored = timepoint(
        w, i, entity_id, "宋神宗元丰八年（1085）", "恢复侍讲之称",
        history, "建立元丰八年侍讲复称节点。", "职源与沿革", category="亲王府官属", grade="从七品",
    )
    old_1117 = timepoint(
        w, i, entity_id, "宋徽宗政和七年（1117）", "改称亲王府直讲",
        history, "建立政和七年侍讲改称直讲节点。", "职源与沿革", category="改称",
    )
    cite(w, "Timepoints", start, i, field(i, "职掌"), "补证亲王府侍讲职掌。", "职掌")
    cite(w, "Timepoints", start, i, field(i, "官品"), "补证亲王府侍讲官品。", "官品")
    alias_citation(w, i, start, "别名")

    lecture = w.entity("王府讲书", "官职", "沿革字段明确元丰三年侍讲改名王府讲书。", quotation=history)
    lecture_start = timepoint(
        w, i, lecture, "宋神宗元丰三年（1080）", "由亲王府侍讲改称",
        history, "建立王府讲书开始节点。", "职源与沿革", category="亲王府官属",
    )
    lecture_end = timepoint(
        w, i, lecture, "宋神宗元丰八年（1085）", "讲书称号停用，恢复侍讲",
        history, "建立王府讲书停用节点。", "职源与沿革", category="废罢称号",
    )
    direct = w.entity("亲王府直讲", "官职", "沿革字段明确政和七年侍讲改名亲王府直讲。", quotation=history)
    direct_start = timepoint(
        w, i, direct, "宋徽宗政和七年（1117）", "由亲王府侍讲改称",
        history, "建立亲王府直讲开始节点。", "职源与沿革", category="亲王府官属",
    )
    relation(w, i, old_1080, lecture_start, "前后演变", history, "元丰三年亲王府侍讲改称王府讲书。", "职源与沿革")
    relation(w, i, lecture_end, restored, "前后演变", history, "元丰八年恢复亲王府侍讲之称。", "职源与沿革")
    relation(w, i, old_1117, direct_start, "前后演变", history, "政和七年亲王府侍讲改称亲王府直讲。", "职源与沿革")
    palace_relation(w, i, start, history, "职源与沿革")
    palace_relation(w, i, lecture_start, history, "职源与沿革")
    palace_relation(w, i, direct_start, history, "职源与沿革")
    w.commit()


def link_palace_members():
    """按亲王府编制总条补全十一种官属及其直接隶属关系。"""
    i = 327
    staffing = field(i, "编制")
    w = W(i)
    group_tp = palace_group(w)
    parent_tp = palace(w)
    members = {
        "亲王府傅": "宋代（具体时间未载）",
        "亲王府长史": "宋代（亲王判府时，具体年月未载）",
        "亲王府司马": "宋初",
        "亲王府谘议参军": "宋初",
        "亲王府友": "宋代（具体时间未载）",
        "亲王府记室参军事": "宋初",
        "亲王府翊善": "宋太宗太平兴国四年（979）",
        "亲王府侍读": "宋代（具体时间未载）",
        "亲王府侍讲": "宋太宗太平兴国四年（979）",
        "亲王府教授": "宋代（具体时间未载）",
        "亲王府小学教授": "宋代（具体时间未载）",
    }
    for title, time in members.items():
        entity_id = w.find_entity(title, "官职")
        if entity_id is None:
            entity_id = w.entity(title, "官职", f"编制字段明列{title}。", quotation=staffing)
        tp_id = w.find_timepoint(entity_id, time)
        if tp_id is None:
            tp_id = timepoint(
                w, i, entity_id, time, "列入亲王府官属，因时而置、无定员",
                staffing, f"据亲王府编制总条建立{title}节点。", "编制", category="亲王府官属",
            )
        relation(
            w, i, group_tp, tp_id, "统称与实例", staffing,
            f"亲王府官属为统称，{title}为原文明列的实例。", "编制",
        )
        relation(
            w, i, parent_tp, tp_id, "编制隶属", staffing,
            f"亲王府编制字段明列{title}，属官不备置、无定员、因时而置。", "编制",
            staff_type="因时而置",
        )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(321, 341)] == [
        "县主", "族姬", "驸马都尉", "郡马", "县马", "国王", "亲王府", "亲王诸宫司",
        "亲王诸宫司使", "都大管勾亲王诸宫司", "亲王诸宫司都监", "亲王夫人",
        "亲王府傅", "亲王府长史", "亲王府司马", "亲王府谘议参军", "亲王府记室参军事",
        "记谘", "亲王府翊善", "亲王府侍讲",
    ]
    entry321()
    entry322()
    entry323()
    entry324()
    entry325()
    entry326()
    entry327()
    entry328()
    entry329()
    entry330()
    entry331()
    entry332()
    entry333()
    entry334()
    entry335()
    entry336()
    entry337()
    entry338()
    entry339()
    entry340()
    link_palace_members()


if __name__ == "__main__":
    main()
