#!/usr/bin/env python3
"""提取第一编第21-40条：太上皇帝与后妃正式称号。"""

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


F = {i: load(i) for i in range(21, 41)}


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
):
    timepoint_id = w.timepoint(
        entity_id,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
    )
    cite(
        w,
        "Timepoints",
        timepoint_id,
        i,
        quotation,
        decision,
        field_name,
    )
    return timepoint_id


def entry21():
    i = 21
    entity_quote = Q(i, "尊衔。皇帝禅位后，尊为太上皇帝。")
    song_quote = Q(
        i,
        "皇帝禅位后，尊为太上皇帝。无实权，不参预政治；"
        "但仍居宫殿，享用自如。",
    )
    origin_dead = Q(
        i,
        "秦始皇二十六年（前221），追尊其父庄襄王为太上皇"
        "（见《史记·秦始皇本纪》）。",
        "职源",
    )
    origin_living = Q(
        i,
        "汉高祖七年（前200），刘邦尊其父为太上皇，此为活人"
        "尊称“太上皇”之始（见《汉书·高帝纪》）。",
        "职源",
    )
    song_example = Q(
        i,
        "《宋史·徽宗纪》4：“宣和七年十二月庚申，诏内禅，皇太子即帝位。"
        "尊帝为教主道君、太上皇帝，居于龙德宫。”",
        "简称",
    )

    w = W(i)
    entity_id = w.entity(
        "太上皇帝",
        "官职",
        "正文明言‘尊衔’及皇帝禅位后的正式称号，建为官职实体。",
        quotation=entity_quote,
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "秦始皇二十六年（前221）",
        "秦始皇追尊其父庄襄王为太上皇",
        origin_dead,
        "建立太上皇称号的追尊职源节点。",
        "职源",
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "汉高祖七年（前200）",
        "活人尊称太上皇之始",
        origin_living,
        "建立活人尊称太上皇的起点节点。",
        "职源",
    )
    song_id = add_timepoint(
        w,
        i,
        entity_id,
        "宋代",
        "皇帝禅位后尊为太上皇帝，无实权，不参预政治",
        song_quote,
        "建立太上皇帝的宋代制度状态。",
        category="尊衔",
    )
    cite(
        w,
        "Timepoints",
        song_id,
        i,
        song_example,
        "宣和七年徽宗内禅后尊为太上皇帝，补证宋代称号实例。",
        "简称",
        note="太上皇、太上、太皇、上皇均为简称或代称，不另建实体",
    )
    w.commit()


def entry27():
    i = 27
    main = Q(i, "皇帝正妻之官称。")
    origin = field(i, "职源")
    duty = field(i, "职掌")
    staffing = field(i, "编制")

    w = W(i)
    entity_id = w.entity(
        "皇后",
        "官职",
        "正文明言皇后是皇帝正妻的官称，建为官职实体。",
        quotation=main,
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "秦汉时",
        "皇帝正妻称皇后",
        origin,
        "建立皇后称号的秦汉职源节点。",
        "职源",
        "皇帝正妻官称",
    )
    song_id = add_timepoint(
        w,
        i,
        entity_id,
        "宋代",
        "皇帝正妻之官称，总领内职，编制一人",
        main,
        "建立皇后在宋代的官称状态。",
        category="皇帝正妻官称",
    )
    cite(w, "Timepoints", song_id, i, duty, "补证皇后总领内职的职掌。", "职掌")
    cite(
        w,
        "Timepoints",
        song_id,
        i,
        staffing,
        "补证皇后一人、不并置且不得虚位的编制规则。",
        "编制",
    )
    w.commit()


def entry28():
    i = 28
    main = Q(i, "皇帝母之官称。")
    origin = field(i, "职源")
    duty = field(i, "职掌")

    w = W(i)
    entity_id = w.entity(
        "皇太后",
        "官职",
        "正文明言皇太后是皇帝母亲的官称，建为官职实体。",
        quotation=main,
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "秦汉以后",
        "皇帝母均称皇太后",
        origin,
        "建立皇太后称号的秦汉职源节点。",
        "职源",
        "皇帝母官称",
    )
    song_id = add_timepoint(
        w,
        i,
        entity_id,
        "宋代",
        "皇帝母之官称；垂帘听政时有权处分军国事",
        main,
        "建立皇太后的宋代官称状态。",
        category="皇帝母官称",
    )
    cite(
        w,
        "Timepoints",
        song_id,
        i,
        duty,
        "补证垂帘听政的皇太后有权处分军国事。",
        "职掌",
    )
    w.commit()


def entry29():
    i = 29
    main = Q(i, "皇帝生母不能尊为皇太后时所用名号。")
    origin = Q(
        i,
        "晋哀帝时（362—365），尊崇其生母周贵人为皇太妃"
        "（见《古今事物考》卷1《太妃》）。",
        "职源与沿革",
    )
    song = Q(
        i,
        "宋哲宗元祐元年（1086），设皇太妃名号，以尊称其生母——神宗朱德妃。"
        "因哲宗初即位时，神宗向皇后已先立为皇太后，皇太后自古不并置，"
        "故特置此称（见《旧闻证误》卷3、《宋史·后妃传》下《钦成朱皇后》）。",
        "职源与沿革",
    )
    rank = field(i, "品阶")

    w = W(i)
    entity_id = w.entity(
        "皇太妃",
        "官职",
        "正文定义为皇帝生母不能尊为皇太后时的正式名号。",
        quotation=main,
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "晋哀帝时（362—365）",
        "尊生母周贵人为皇太妃",
        origin,
        "建立皇太妃称号的晋代职源节点。",
        "职源与沿革",
    )
    song_id = add_timepoint(
        w,
        i,
        entity_id,
        "宋哲宗元祐元年（1086）",
        "设皇太妃名号，用于皇太后不并置时尊称皇帝生母",
        song,
        "原文明言元祐元年设皇太妃名号，建立宋代设置节点。",
        "职源与沿革",
        "皇帝生母名号",
    )
    cite(
        w,
        "Timepoints",
        song_id,
        i,
        rank,
        "补证皇太妃位比皇后、奉给超过皇后。",
        "品阶",
    )
    w.commit()


def entry30():
    i = 30
    main = Q(i, "皇帝祖母官称。")
    origin = field(i, "职源")
    duty = field(i, "职掌")

    w = W(i)
    entity_id = w.entity(
        "太皇太后",
        "官职",
        "正文明言太皇太后是皇帝祖母的官称，建为官职实体。",
        quotation=main,
    )
    add_timepoint(
        w,
        i,
        entity_id,
        "秦汉时",
        "秦汉已有太皇太后之称，皇帝祖母称太皇太后",
        origin,
        "建立太皇太后称号的秦汉职源节点。",
        "职源",
        "皇帝祖母官称",
    )
    song_id = add_timepoint(
        w,
        i,
        entity_id,
        "宋代",
        "皇帝祖母官称；临朝称制时有权处分军国事",
        main,
        "建立太皇太后的宋代官称状态。",
        category="皇帝祖母官称",
    )
    cite(
        w,
        "Timepoints",
        song_id,
        i,
        duty,
        "补证临朝称制的太皇太后有权处分军国事。",
        "职掌",
    )
    w.commit()


def entry31():
    i = 31
    entity_quote = Q(i, "太上皇帝正妻官称。与太皇太后有别。")
    use_quote = Q(i, "高宗内禅，手诏后称太上皇后。")

    w = W(i)
    entity_id = w.entity(
        "太上皇后",
        "官职",
        "正文明言这是太上皇帝正妻的官称，且与太皇太后有别。",
        quotation=entity_quote,
    )
    timepoint_id = add_timepoint(
        w,
        i,
        entity_id,
        "高宗内禅后",
        "手诏后称太上皇后",
        use_quote,
        "原文明言高宗内禅后诏称太上皇后，建立宋代使用节点。",
        category="太上皇帝正妻官称",
    )
    cite(
        w,
        "Timepoints",
        timepoint_id,
        i,
        entity_quote,
        "补证太上皇后的官称定义及其与太皇太后的区别。",
    )
    w.commit()


def entry39():
    i = 39
    example = Q(
        i,
        "真宗崩，遗诏尊皇后为皇太后，权处分军国重事。"
        "仁宗赵祯即位年幼，垂帘听政达十一年之久。",
    )
    w = W(i)
    entity_id = w.find_entity("皇太后", "官职")
    assert entity_id
    timepoint_id = w.find_timepoint(entity_id, "宋代")
    assert timepoint_id
    cite(
        w,
        "Timepoints",
        timepoint_id,
        i,
        example,
        "真宗刘皇后例补证皇太后可权处分军国重事并垂帘听政。",
        note="该条为具体人物生平，人物本身不建实体；仅追加其直接证明的皇太后职掌事实",
    )
    w.commit()


SKIPPED_ENTRIES = {
    22: "宋太祖、宋太宗的人物合称",
    23: "徽宗、钦宗的人物合称",
    24: "宫城内建筑总名，是空间与建筑而非机构或官职",
    25: "数处宫殿的合称，不是机构或官职",
    26: "皇帝寝阁别称，为空间称谓",
    32: "具体人物生平",
    33: "空 placeholder 词条",
    34: "具体人物生平",
    35: "具体人物生平",
    36: "具体人物生平",
    37: "具体人物生平",
    38: "具体人物生平",
    40: "具体人物生平",
}


def main():
    assert [F[i]["title"] for i in range(21, 41)] == [
        "太上皇帝", "祖宗", "二圣", "大内", "数内", "内阁", "皇后", "皇太后",
        "皇太妃", "太皇太后", "太上皇后", "杜皇太后", "宋太宗生母", "太祖王皇后",
        "太祖宋皇后", "太宗李皇后", "太宗李夫人", "真宗郭皇后", "真宗刘皇后", "真宗李宸妃",
    ]
    entry21()
    entry27()
    entry28()
    entry29()
    entry30()
    entry31()
    entry39()
    for i, reason in SKIPPED_ENTRIES.items():
        print(f"#{i} {F[i]['title']}: skipped ({reason})")


if __name__ == "__main__":
    main()
