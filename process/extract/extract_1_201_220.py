#!/usr/bin/env python3
"""提取第一编第201-220条：后宫内职、旧名改称与直笔。"""

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
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(201, 221)}


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
    return w.citation(
        table, target_id, C(i, name), quotation, decision, **kwargs
    )


def timepoint(
    w, i, entity_id, time, event, quotation, decision, name=None,
    category=None, grade=None, chain="tail",
):
    target_id = w.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_grade=grade, chain=chain,
    )
    cite(w, "Timepoints", target_id, i, quotation, decision, name)
    return target_id


def relation(w, i, subject, object_, kind, quotation, decision, name=None):
    target_id = w.relationship(subject, object_, kind, decision, quotation)
    cite(w, "Relationships", target_id, i, quotation, decision, name)
    return target_id


def find_entity(w, title, type_="官职"):
    entity_id = w.find_entity(title, type_)
    assert entity_id, (title, type_)
    return entity_id


def find_tp(w, title, time, type_="官职"):
    entity_id = find_entity(w, title, type_)
    target_id = w.find_timepoint(entity_id, time)
    assert target_id, (title, time)
    return target_id


def group_as_palace_official(w, i, tp_id, quotation):
    return relation(
        w, i, find_tp(w, "宫官", "宋初"), tp_id,
        "统称与实例", quotation,
        f"宫官为宫人女官总称，{F[i]['title']}为具体女官或职事。",
    )


def entry201():
    i = 201
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("祗候人", "官职", "正文定义祗候人为后宫内职。", quotation=main)
    timepoint(
        w, i, entity_id, "宋太宗朝以前（具体时间未载）",
        "后宫内职，无品，有亲近皇帝机会，后改为御侍", main,
        "原书只说明后改御侍，建立太宗改名前承载节点。",
        category="后宫内职", grade="无品",
    )
    w.commit()


def entry202():
    i = 202
    main = F[i]["text"]
    alias = field(i, "别称")
    w = W(i)
    entity_id = w.entity("御侍", "官职", "正文定义御侍为后宫内职。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋太宗朝",
        "祗候人改称御侍，无品，可亲近侍奉并接幸皇帝", main,
        "建立太宗朝御侍改称节点。", category="后宫内职", grade="无品",
    )
    cite(
        w, "Timepoints", tp_id, i, alias, "补证御侍别称侍御；别称不另建实体。", "别称",
        note="侍御为御侍别称，不另建实体",
    )
    relation(
        w, i, find_tp(w, "祗候人", "宋太宗朝以前（具体时间未载）"), tp_id,
        "前后演变", main, "太宗朝祗候人改称御侍。",
    )
    w.commit()


def entry203():
    i = 203
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("侍御行首", "官职", "正文定义侍御行首为御侍班头。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋真宗朝", "始置侍御行首，为御侍班头", main,
        "建立真宗朝侍御行首节点。", category="御侍班头",
    )
    relation(
        w, i, find_tp(w, "御侍", "宋太宗朝"), tp_id,
        "统称与实例", main, "御侍为职类，侍御行首为其班头等级。",
    )
    w.commit()


def entry204():
    i = 204
    main = F[i]["text"]
    alias = field(i, "别称")
    w = W(i)
    entity_id = w.entity("殿直", "官职", "正文定义殿直为后宫内职。", quotation=main)
    timepoint(
        w, i, entity_id, "唐代", "已置殿直，号裹头内人", main,
        "建立殿直唐代职源节点。", category="后宫内职",
    )
    song_tp = timepoint(
        w, i, entity_id, "宋代",
        "内官中贵者，与御侍同可亲近供奉皇帝，作男子拜", main,
        "建立宋代殿直节点。", category="后宫内职",
    )
    cite(
        w, "Timepoints", song_tp, i, alias, "补证殿直别称小殿直；别称不另建实体。", "别称",
        note="小殿直为殿直别称，不另建实体",
    )
    relation(
        w, i, find_tp(w, "内官", "宋仁宗朝"), song_tp,
        "统称与实例", main, "原文明称殿直为内官中贵者，内官为总称。",
    )
    w.commit()


def entry205():
    i = 205
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("押班殿直", "官职", "正文定义押班殿直为殿直等级名号。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋真宗朝", "见置押班殿直，为殿直等级名号之一，简称押班", main,
        "建立真宗朝押班殿直节点。", category="殿直等级名号",
    )
    relation(
        w, i, find_tp(w, "殿直", "宋代"), tp_id,
        "统称与实例", main, "殿直为总类，押班殿直为其等级名号。",
    )
    w.commit()


def simple_inner_post(i, time, event, grade=None):
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity(
        F[i]["title"], "官职", f"正文定义{F[i]['title']}为后宫内职。", quotation=main
    )
    tp_id = timepoint(
        w, i, entity_id, time, event, main,
        f"建立{F[i]['title']}的{time}节点。", category="后宫内职", grade=grade,
    )
    w.commit()
    return tp_id


def entry206():
    simple_inner_post(206, "宋太祖朝", "置乐使", "无品")


def entry207():
    i = 207
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("仙韶使", "官职", "正文定义仙韶使为后宫内职名号。", quotation=main)
    tp_id = timepoint(w, i, entity_id, "宋太宗朝", "乐使改称仙韶使", main, "建立太宗朝仙韶使改称节点。", category="后宫内职", grade="无品")
    relation(w, i, find_tp(w, "乐使", "宋太祖朝"), tp_id, "前后演变", main, "太宗朝乐使改称仙韶使。")
    w.commit()


def entry208():
    simple_inner_post(208, "宋太宗朝", "增置乐使副使", "无品")


def entry209():
    i = 209
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("仙韶副使", "官职", "正文定义仙韶副使为后宫内职名号。", quotation=main)
    tp_id = timepoint(w, i, entity_id, "宋太宗朝", "乐使副使改称仙韶副使", main, "建立太宗朝仙韶副使改称节点。", category="后宫内职")
    relation(w, i, find_tp(w, "乐使副使", "宋太宗朝"), tp_id, "前后演变", main, "太宗朝乐使副使改称仙韶副使。")
    w.commit()


def entry210():
    i = 210
    main = F[i]["text"]
    alias = field(i, "别称")
    w = W(i)
    entity_id = w.entity("管勾仙韶公事", "官职", "正文定义管勾仙韶公事为后宫女职。", quotation=main)
    timepoint(w, i, entity_id, "北宋", "见置管勾仙韶公事", main, "建立北宋见置节点。", category="后宫女职")
    southern_tp = timepoint(
        w, i, entity_id, "南宋", "避高宗讳，追改称主管仙韶", alias,
        "建立南宋避讳改称状态；主管仙韶作为别称不另建实体。", "别称", category="后宫女职",
    )
    cite(
        w, "Timepoints", southern_tp, i, alias, "补证主管仙韶为避讳追改称谓。", "别称",
        note="主管仙韶为管勾仙韶公事的避讳追改称谓，不另建实体",
    )
    w.commit()


def entry211():
    i = 211
    main = F[i]["text"]
    alias = field(i, "别称")
    w = W(i)

    # “大监”另有“诸监长官的通称”同名条目，必须按原书同名异职分建实体。
    row = w.conn.execute(
        "SELECT id FROM Entities WHERE title='大监' AND type='官职'"
        " AND quotation=? ORDER BY id LIMIT 1",
        (main,),
    ).fetchone()
    if row:
        entity_id = row[0]
    else:
        entity_id = w._insert(
            "INSERT INTO Entities (title, type, quotation) VALUES (?,?,?)",
            ("大监", "官职", main),
            "Entities",
            "本条大监是后宫女官，与既有诸监长官通称同名异职，按原书正式词头另建实体。",
        )

    # 兼容本脚本早期误把女官节点挂到诸监长官通称实体的状态：原位拆链后迁移。
    moved = w.conn.execute(
        "SELECT t.id,t.entity_id,t.prev_id,t.succ_id FROM Timepoints t"
        " JOIN Entities e ON e.id=t.entity_id"
        " WHERE e.title='大监' AND e.type='官职' AND t.time='宋太宗朝'"
        " AND t.quotation=? ORDER BY t.id LIMIT 1",
        (main,),
    ).fetchone()
    if moved and moved[1] != entity_id:
        tp_id, _old_entity_id, old_prev, old_succ = moved
        if old_prev is not None:
            w.relink(
                old_prev, succ_id=old_succ,
                decision="拆除误并入诸监长官通称实体的后宫女官大监节点",
            )
        if old_succ is not None:
            w.relink(
                old_succ, prev_id=old_prev,
                decision="拆除误并入诸监长官通称实体的后宫女官大监节点",
            )
        w.conn.execute(
            "UPDATE Timepoints SET entity_id=?,prev_id=NULL,succ_id=NULL WHERE id=?",
            (entity_id, tp_id),
        )
        w._br(
            "Timepoints", tp_id,
            "将宋太宗朝后宫女官大监节点迁至同名异职的新实体，并清除原错误链指针。",
        )
    elif moved:
        tp_id = moved[0]
    else:
        tp_id = timepoint(
            w, i, entity_id, "宋太宗朝",
            "始置后宫女官大监，与尚宫并知内省事，号称尚书", main,
            "建立同名异职的后宫女官大监节点。",
            category="后宫女官",
        )
    cite(
        w, "Timepoints", tp_id, i, alias, "补证后宫女官大监别称太监。", "别称",
        note="本条太监为后宫女官大监别称，不另建实体",
    )
    relation(w, i, find_tp(w, "内省", "宋太宗朝", "机构"), tp_id, "编制隶属", main, "大监与尚宫并知内省事，隶属内省。")
    group_as_palace_official(w, i, tp_id, main)
    w.commit()


def cite_existing_evolution(i, old_title, old_time, new_title, new_time, group_old=True):
    main = F[i]["text"]
    w = W(i)
    old_tp = find_tp(w, old_title, old_time)
    new_tp = find_tp(w, new_title, new_time)
    cite(w, "Timepoints", old_tp, i, main, f"补证{old_title}为改名前女官名。")
    cite(w, "Timepoints", new_tp, i, main, f"补证{old_title}在太宗朝改称{new_title}。")
    relation(w, i, old_tp, new_tp, "前后演变", main, f"太宗朝{old_title}改称{new_title}。")
    if group_old:
        group_as_palace_official(w, i, old_tp, main)
    w.commit()


def entry212():
    cite_existing_evolution(212, "衣服", "宋初", "司衣", "宋太宗朝")


def entry213():
    cite_existing_evolution(213, "梳篦", "宋初", "司饰", "宋太宗朝")


def entry214():
    i = 214
    main = F[i]["text"]
    w = W(i)
    old = w.entity("枕被", "官职", "正文定义枕被为后宫女官旧名。", quotation=main)
    old_tp = timepoint(w, i, old, "宋太宗朝以前（具体时间未载）", "后宫女官名，后改司寝", main, "建立枕被改名前节点。", category="后宫女官")
    current = w.entity("司寝", "官职", "正文定义司寝为枕被改名后的女官。", quotation=main)
    current_tp = timepoint(w, i, current, "宋太宗朝", "枕被改称司寝", main, "建立太宗朝司寝改称节点。", category="二十四司之一")
    relation(w, i, old_tp, current_tp, "前后演变", main, "太宗朝枕被改称司寝。")
    relation(w, i, find_tp(w, "二十四司", "宋仁宗以后"), current_tp, "统称与实例", main, "原文明言司寝后属二十四司之一。")
    group_as_palace_official(w, i, old_tp, main)
    w.commit()


def entry215():
    i = 215
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("司给", "官职", "正文定义司给为后宫女官。", quotation=main)
    tp_id = timepoint(w, i, entity_id, "宋太祖朝", "置司给", main, "建立太祖朝司给节点。", category="后宫女官")
    group_as_palace_official(w, i, tp_id, main)
    w.commit()


def entry216():
    i = 216
    main = F[i]["text"]
    w = W(i)
    entity_id = find_entity(w, "司寝")
    tp_id = timepoint(w, i, entity_id, "宋真宗朝", "见任司寝，可接幸皇帝", main, "据李宸妃事建立真宗朝司寝节点。", category="后宫女官")
    group_as_palace_official(w, i, tp_id, main)
    w.commit()


def entry217():
    i = 217
    main = F[i]["text"]
    w = W(i)
    old = w.entity("汤药", "官职", "正文定义汤药为后宫女官旧名。", quotation=main)
    old_tp = timepoint(w, i, old, "宋太宗朝以前（具体时间未载）", "后宫女官名，后改司药", main, "建立汤药改名前节点。", category="后宫女官")
    new_tp = find_tp(w, "司药", "宋太宗朝")
    cite(w, "Timepoints", new_tp, i, main, "补证汤药在太宗朝改称司药。")
    relation(w, i, old_tp, new_tp, "前后演变", main, "太宗朝汤药改称司药。")
    group_as_palace_official(w, i, old_tp, main)
    w.commit()


def insert_taizong_zhangdeng(w, i, quotation):
    entity_id = find_entity(w, "掌灯")
    existing = w.find_timepoint(entity_id, "宋太宗朝")
    if existing:
        return existing
    prev_tp = find_tp(w, "掌灯", "隋炀帝时")
    succ_tp = find_tp(w, "掌灯", "宋仁宗天圣年间")
    new_tp = timepoint(
        w, i, entity_id, "宋太宗朝", "掌灯火改称掌灯", quotation,
        "在隋代职源与天圣见置之间插入太宗改称节点。", category="二十四掌之一", chain="none",
    )
    w.relink(prev_tp, succ_id=new_tp, decision="太宗改称节点插入隋代掌灯之后")
    w.relink(new_tp, prev_id=prev_tp, succ_id=succ_tp, decision="连接隋代与天圣掌灯节点")
    w.relink(succ_tp, prev_id=new_tp, decision="太宗改称节点插入天圣掌灯之前")
    return new_tp


def entry218():
    i = 218
    main = F[i]["text"]
    w = W(i)
    old = w.entity("掌灯火", "官职", "正文定义掌灯火为后宫女官旧名。", quotation=main)
    old_tp = timepoint(w, i, old, "宋太宗朝以前（具体时间未载）", "后宫女官名，后改掌灯", main, "建立掌灯火改名前节点。", category="后宫女官")
    new_tp = insert_taizong_zhangdeng(w, i, main)
    cite(w, "Timepoints", new_tp, i, main, "补证掌灯火在太宗朝改称掌灯。")
    relation(w, i, old_tp, new_tp, "前后演变", main, "太宗朝掌灯火改称掌灯。")
    relation(w, i, find_tp(w, "二十四掌", "宋仁宗以后"), new_tp, "统称与实例", main, "原文明言掌灯后属二十四掌之一。")
    group_as_palace_official(w, i, old_tp, main)
    w.commit()


def entry219():
    i = 219
    main = F[i]["text"]
    w = W(i)
    old = w.entity("弟子", "官职", "正文定义弟子为后宫职员旧名。", quotation=main)
    old_tp = timepoint(w, i, old, "宋太宗朝以前（具体时间未载）", "后宫职员名，后改供奉", main, "建立弟子改名前节点。", category="后宫职员")
    new = w.entity("供奉", "官职", "正文定义供奉为弟子改名后的后宫职员。", quotation=main)
    new_tp = timepoint(w, i, new, "宋太宗朝", "弟子改称供奉", main, "建立太宗朝供奉改称节点。", category="后宫职员")
    relation(w, i, old_tp, new_tp, "前后演变", main, "太宗朝弟子改称供奉。")
    w.commit()


def entry220():
    i = 220
    main = F[i]["text"]
    w = W(i)
    entity_id = w.entity("直笔", "官职", "正文定义直笔为后宫女官职事。", quotation=main)
    tp_id = timepoint(
        w, i, entity_id, "宋太宗朝",
        "始置直笔，掌书写内令、记录，依尚字、司字、典字、掌字区分等级与俸禄",
        main, "建立太宗朝直笔节点。", category="后宫女官职事",
    )
    timepoint(
        w, i, entity_id, "宋孝宗淳熙三年（1176）正月四日",
        "见直笔司字吴氏因差误加恩锁院而降紫霞帔", main,
        "建立淳熙三年直笔司字实例节点。", category="后宫女官职事",
    )
    group_as_palace_official(w, i, tp_id, main)
    w.commit()


def main():
    assert [F[i]["title"] for i in range(201, 221)] == [
        "祗候人", "御侍", "侍御行首", "殿直", "押班殿直", "乐使", "仙韶使", "乐使副使", "仙韶副使", "管勾仙韶公事",
        "大监", "衣服", "梳篦", "枕被", "司给", "司寝", "汤药", "掌灯火", "弟子", "直笔",
    ]
    entry201()
    entry202()
    entry203()
    entry204()
    entry205()
    entry206()
    entry207()
    entry208()
    entry209()
    entry210()
    entry211()
    entry212()
    entry213()
    entry214()
    entry215()
    entry216()
    entry217()
    entry218()
    entry219()
    entry220()


if __name__ == "__main__":
    main()
