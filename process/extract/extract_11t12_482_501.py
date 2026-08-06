#!/usr/bin/env python3
"""提取 chapter11t12 第482-501条：医官末阶、天文官十六阶与爵制开端。"""

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
    "extract_11t12_462_481_helpers", HERE / "extract_11t12_462_481.py"
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


F = {entry_id: load(entry_id) for entry_id in range(482, 502)}


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
relation = base.base.relation
typed_state = base.base.typed_state


def source(entry_id):
    return f'《宋代官制辞典》第{F[entry_id]["page"]}页“{F[entry_id]["title"]}”条'


def cite(writer, target_table, target_id, entry_id, quotation, decision):
    return writer.citation(
        target_table, target_id, source(entry_id), quotation, decision
    )


def sentence(entry_id, start_text):
    text = F[entry_id]["text"]
    start = text.index(start_text)
    return text[start:text.index("。", start) + 1]


def append_event(writer, timepoint_id, text, decision, *, category=None,
                 officer=None, grade=None):
    row = writer.conn.execute(
        "SELECT event,attr_category,attr_officer_type,attr_grade "
        "FROM Timepoints WHERE id=?", (timepoint_id,)
    ).fetchone()
    assert row, timepoint_id
    event = row[0] or ""
    additions = []
    if text and text not in event:
        event = f"{event}；{text}" if event else text
        additions.append("event")
    values = {
        "attr_category": row[1] or category,
        "attr_officer_type": row[2] or officer,
        "attr_grade": row[3] or grade,
    }
    for key, old, new in (
        ("attr_category", row[1], values["attr_category"]),
        ("attr_officer_type", row[2], values["attr_officer_type"]),
        ("attr_grade", row[3], values["attr_grade"]),
    ):
        if old != new:
            additions.append(key)
    if not additions:
        return
    writer.conn.execute(
        "UPDATE Timepoints SET event=?,attr_category=?,attr_officer_type=?,"
        "attr_grade=? WHERE id=?",
        (event, values["attr_category"], values["attr_officer_type"],
         values["attr_grade"], timepoint_id),
    )
    writer._br(
        "Timepoints", timepoint_id,
        f"补充时间点字段 {', '.join(additions)}：{decision}",
    )


def correct_spring_official_date(writer):
    entity_id = writer.find_entity("春官大夫", "官职")
    assert entity_id is not None
    wrong = writer.find_timepoint(entity_id, "南宋淳熙三年十二月十二日")
    correct = writer.find_timepoint(entity_id, "南宋淳熙三年十二月二日")
    if wrong is not None:
        assert correct is None, (wrong, correct)
        writer.conn.execute(
            "DELETE FROM NormalizedTimes WHERE timepoint_id=?", (wrong,)
        )
        writer.conn.execute(
            "UPDATE Timepoints SET time=? WHERE id=?",
            ("南宋淳熙三年十二月二日", wrong),
        )
        writer._br(
            "Timepoints", wrong,
            "据天文官十六阶总条及春官大夫专条一致纪年，将旧录十二月十二日修正为十二月二日。",
        )
        correct = wrong
    assert correct is not None
    return correct


def extract_last_medical_rank():
    entry_id = 482
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "北宋政和三年八月二十五日新增医职八阶之一，为医官二十二阶之第二十二阶。无品。不理为官户。",
    )
    _, member = state(
        writer, entry_id, "翰林祗候", "北宋徽宗政和三年八月二十五日",
        "新增，为医官二十二阶之第二十二阶；无品；不理为官户", quote,
        "建立翰林祗候医阶节点并记录品级、官户属性。",
        category="医官阶", officer="医阶", grade="无品",
        sort_order=111308025,
    )
    group_entity = writer.find_entity("医官二十二阶", "官职")
    assert group_entity is not None
    group = writer.find_timepoint(
        group_entity, "北宋徽宗政和三年八月二十五日"
    )
    assert group is not None
    relation(
        writer, entry_id, group, member, "统称与实例", quote,
        "原文明示翰林祗候为医官二十二阶第二十二阶。",
    )
    writer.commit()


ASTRONOMICAL_RANKS = {
    484: ("春官大夫", "首", "从六品", "服紫"),
    485: ("夏官大夫", "第二", "从六品", "服紫"),
    486: ("中官大夫", "第三", "从六品", "服紫"),
    487: ("秋官大夫", "第四", "正七品", "服紫"),
    488: ("冬官大夫", "第五", "正七品", "服紫"),
    489: ("太史局春官正", "第六", "正八品", "服紫"),
    490: ("太史局夏官正", "第七", "正八品", "服紫"),
    491: ("太史局中官正", "第八", "正八品", "服紫"),
    492: ("太史局秋官正", "第九", "正八品", "服紫"),
    493: ("太史局冬官正", "第十", "正八品", "服紫"),
    494: ("太史局丞", "第十一", "从八品", "服绯"),
    495: ("太史局直长", "第十二", "从八品", "服绿"),
    496: ("太史局灵台郎", "第十三", "从八品", "服绿"),
    497: ("太史局保章正", "第十四", "从八品", "服绿"),
    498: ("太史局挈壶正", "第十五", "正九品", "服绿"),
    499: ("局生", "第十六", "无品", "服绿"),
}


def extract_astronomical_ranks():
    entry_id = 483
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "南宋淳熙三年十二月二日，天文官增置春官、夏官、中官、秋官、冬官大夫五阶，合旧太史局局生至春官正十一阶，共为十六阶，年劳理作一百零四年，构成天文官迁转资阶",
    )
    _, group = state(
        writer, entry_id, "天文官十六阶", "南宋淳熙三年十二月二日",
        "增置五官大夫五阶，合旧太史局十一阶为十六阶；年劳合计一百零四年",
        quote, "建立天文官十六阶总制节点。",
        category="天文官阶", officer="职官总名", sort_order=117612002,
    )
    _, bureau = typed_state(
        writer, entry_id, "太史局", "机构", "南宋淳熙三年十二月二日",
        "所属天文官增置五官大夫并合为十六阶", quote,
        "据原文建立太史局淳熙三年制度节点。",
        category="太史局", sort_order=117612002,
    )
    relation(
        writer, entry_id, bureau, group, "编制隶属", quote,
        "天文官十六阶为太史局天文官迁转资阶。",
    )
    writer.commit()

    for entry_id, (canonical, ordinal, grade, attire) in ASTRONOMICAL_RANKS.items():
        writer = W(entry_id)
        if entry_id == 484:
            correct_spring_official_date(writer)
        date_phrase = (
            "南宋淳熙三年十二月二日增置"
            if entry_id <= 488 else "南宋淳熙三年十二月二日所定"
        )
        quote = sentence(entry_id, date_phrase)
        _, member = state(
            writer, entry_id, canonical, "南宋淳熙三年十二月二日",
            f"列为太史局天文官十六阶之{ordinal}阶；{grade}；{attire}", quote,
            f"建立或复用{canonical}在天文官十六阶中的节点。",
            category="天文官十六阶", officer="天文阶官", grade=grade,
            sort_order=117612002,
        )
        append_event(
            writer, member,
            f"列为太史局天文官十六阶之{ordinal}阶；{grade}；{attire}",
            f"据第{entry_id}条补足序位、品级与服色。",
            category="天文官十六阶", officer="天文阶官", grade=grade,
        )
        group_entity = writer.find_entity("天文官十六阶", "官职")
        assert group_entity is not None
        group = writer.find_timepoint(
            group_entity, "南宋淳熙三年十二月二日"
        )
        assert group is not None
        relation(
            writer, entry_id, group, member, "统称与实例", quote,
            f"原文明示{F[entry_id]['title']}为太史局天文官十六阶之{ordinal}阶。",
        )
        writer.commit()


def add_regime(writer, entry_id, time, event, members, quote, order):
    _, group = state(
        writer, entry_id, "爵", time, event, quote,
        f"据原文建立或复用爵制在{time}的制度节点。",
        category="爵制", officer="职官总名", sort_order=order,
    )
    for title in members:
        _, member = state(
            writer, entry_id, title, time, f"列入{event}", quote,
            f"原文明列{title}为{time}爵等实例。",
            category="爵制", officer="爵位", sort_order=order,
        )
        relation(
            writer, entry_id, group, member, "统称与实例", quote,
            f"原文明示{time}爵制包括{title}。",
        )
    return group


def add_policy(writer, entry_id, time, event, quote, order):
    _, timepoint = state(
        writer, entry_id, "爵", time, event, quote,
        f"记录爵制在{time}的制度规则。",
        category="爵制", officer="职官总名", sort_order=order,
    )
    append_event(
        writer, timepoint, event, f"补充{time}爵制规则。",
        category="爵制", officer="职官总名",
    )
    cite(writer, "Timepoints", timepoint, entry_id, quote, f"补证{event}。")
    return timepoint


def extract_peerage_system():
    entry_id = 500
    writer = W(entry_id)
    add_regime(
        writer, entry_id, "西周（或说）", "或说西周五等爵",
        ("公", "侯", "伯", "子", "男"),
        Q(entry_id, "或说西周立爵五等：公、侯、伯、子、男"),
        0,
    )
    add_regime(
        writer, entry_id, "唐代", "唐代九等爵",
        ("王", "郡王", "国公", "郡公", "县公", "县侯", "县伯", "县子", "县男"),
        Q(entry_id, "唐爵分九等：王、郡王、国公、郡公、县公、县侯、县伯、县子、县男"),
        61800000,
    )
    north_quote = Q(
        entry_id,
        "北宋前期为十二等：王、嗣王、郡王、国公、郡公、开国公、开国郡公、开国县公、开国侯、开国伯、开国子、开国男。",
    )
    add_regime(
        writer, entry_id, "北宋前期", "北宋前期十二等爵",
        ("王", "嗣王", "郡王", "国公", "郡公", "开国公", "开国郡公",
         "开国县公", "开国侯", "开国伯", "开国子", "开国男"),
        north_quote, 96000000,
    )
    reform_quote = Q(
        entry_id,
        "北宋神宗官制定为九等：王、郡王、国公、郡公、县公、侯、伯、子、男",
    )
    add_regime(
        writer, entry_id, "北宋神宗官制", "神宗官制九等爵",
        ("王", "郡王", "国公", "郡公", "县公", "侯", "伯", "子", "男"),
        reform_quote, 108000000,
    )
    ten_quote = Q(
        entry_id,
        "北宋神宗官制定为九等：王、郡王、国公、郡公、县公、侯、伯、子、男（《宋会要·职官》9之17引《神宗正史职官志》）。又有嗣王之爵等，列入《元祐官品令》、《庆元官品令》，计为十等。",
    )
    ten_members = ("王", "嗣王", "郡王", "国公", "郡公", "县公", "侯", "伯", "子", "男")
    add_regime(
        writer, entry_id, "北宋哲宗元祐官品令", "元祐官品令十等爵",
        ten_members, ten_quote, 108600000,
    )
    add_regime(
        writer, entry_id, "南宋宁宗庆元官品令", "庆元官品令十等爵",
        ten_members, ten_quote, 119500000,
    )

    add_policy(
        writer, entry_id, "宋代",
        "宗室封公、侯、伯、子、男；文武官封授冠以开国名",
        Q(entry_id, "公、侯、伯、子、男，封宗室；文武官封授时冠以“开国”名"),
        96000000,
    )
    add_policy(
        writer, entry_id, "北宋前期",
        "文臣少卿监、武臣内殿崇班以上可封爵；进爵至开国郡公止",
        Q(entry_id, "北宋前期，文臣少卿监、武臣内殿崇班以上有封爵，丞郎、学士、刺史、大将军、诸司使以上带食实封，不系爵邑，但以所增食邑与食实封户数为等差，超过其爵等所定户数，则进爵。爵等进至开国郡公止"),
        96000000,
    )
    add_policy(
        writer, entry_id, "宋代",
        "食邑分五等；一千五百户以上始加实封；官品不同则加食邑与实封户数有差",
        Q(entry_id, "凡封爵所定食邑为五等：食邑三百户，封开国男；五百户，封开国子；七百户，封开国伯；千户，封开国侯；二千户，封开国公。食邑一千五百户以上，始加实封。凡加食邑与实封，也有等差：宰相加食邑千户、实封四百户；余降麻官食邑七百户、实封三百户；直学士以上食邑五百户、实封二百户；中书舍人、待制、诸尚书至少卿监以上实封一百户。"),
        96000000,
    )
    add_policy(
        writer, entry_id, "北宋仁宗庆历七年",
        "南郊后不到万户的使相亦可封国公",
        Q(entry_id, "北宋仁宗庆历七年南郊，不到万户之使相亦封国公。"),
        104700000,
    )
    add_policy(
        writer, entry_id, "宋代",
        "臣僚封爵以国公为顶；异姓原则上不生封或追封王爵，后有赵普追封韩王及张俊、秦桧生封郡王之变例",
        Q(entry_id, "臣僚封爵至国公封顶。宋代稽汉朝“非刘氏不王”之故事，异姓不生封王爵或追封王爵；然北宋名相赵普始得追封韩王、南宋又有张俊、秦桧生封郡王，其制始变"),
        96000000,
    )
    add_policy(
        writer, entry_id, "南宋理宗朝",
        "罢封爵食实封每户月俸加二十五文之制",
        Q(entry_id, "宋代封爵带食实封者，每户于月俸中加二十五文，南宋理宗朝已罢"),
        122400000,
    )
    writer.commit()


def extract_king_rank():
    entry_id = 501
    writer = W(entry_id)
    intro = Q(
        entry_id,
        "爵位名。正一品。宋九等爵或十二等爵之第一等，授予皇子、皇兄弟，称为亲王。",
    )
    _, king = state(
        writer, entry_id, "王", "宋代",
        "九等爵或十二等爵第一等；授皇子、皇兄弟，称亲王；正一品",
        intro, "建立王爵宋代制度节点。",
        category="爵制", officer="爵位", grade="正一品", sort_order=96000000,
    )
    _, peerage = state(
        writer, entry_id, "爵", "宋代", "宋代爵制总称", intro,
        "复用宋代爵制总称节点以连接王爵。",
        category="爵制", officer="职官总名", sort_order=96000000,
    )
    relation(
        writer, entry_id, peerage, king, "统称与实例", intro,
        "原文明示王为宋九等爵或十二等爵第一等。",
    )

    posthumous = Q(
        entry_id,
        "大臣无生封王爵，死后或有追封，如王安石于徽宗朝追封舒王、岳飞于宁宗朝追封鄂王等。",
    )
    append_event(
        writer, king, "大臣不生封，死后或追封",
        "补充王爵对大臣的封授规则。",
    )
    cite(writer, "Timepoints", king, entry_id, posthumous, "补证大臣王爵追封规则。")
    for title, time, person in (
        ("舒王", "北宋徽宗朝", "王安石死后追封"),
        ("鄂王", "南宋宁宗朝", "岳飞死后追封"),
    ):
        _, example = state(
            writer, entry_id, title, time, person, posthumous,
            f"原文明列{title}为大臣死后追封王爵实例。",
            category="王爵封号", officer="爵位",
            sort_order=110100000 if title == "舒王" else 119500000,
        )
        relation(
            writer, entry_id, king, example, "统称与实例", posthumous,
            f"{title}是王爵封号实例。",
        )

    kingdoms = Q(
        entry_id,
        "封王爵均有封国名，封国有大国、次国、小国之分，如晋王光义，晋国为大国；寿王赵恒，寿国为次国；康王赵构，康国为小国。",
    )
    append_event(
        writer, king, "均有封国名，封国分大国、次国、小国",
        "补充王爵封国等级规则。",
    )
    cite(writer, "Timepoints", king, entry_id, kingdoms, "补证王爵封国等级。")
    for title, event in (
        ("晋王", "光义所封，晋国为大国"),
        ("寿王", "赵恒所封，寿国为次国"),
        ("康王", "赵构所封，康国为小国"),
    ):
        _, example = state(
            writer, entry_id, title, "宋代（具体年未载）", event, kingdoms,
            f"原文明列{title}为王爵封号实例。",
            category="王爵封号", officer="爵位", sort_order=96000000,
        )
        relation(
            writer, entry_id, king, example, "统称与实例", kingdoms,
            f"{title}是王爵封号实例。",
        )

    restriction = Q(
        entry_id,
        "国名有定制，其中赵、梁、宋三国不封；其次，亲王升为皇帝后，该皇帝在亲王位上的封国，不再封",
    )
    append_event(
        writer, king, "赵、梁、宋三国不封；亲王升帝后的旧封国不再封",
        "补充王爵封国禁限。",
    )
    cite(writer, "Timepoints", king, entry_id, restriction, "补证王爵封国禁限。")
    writer.commit()


def main():
    expected = [
        "翰林祗候", "天文官十六阶", "春官大夫", "夏官大夫",
        "中官大夫", "秋官大夫", "冬官大夫", "春官正", "夏官正",
        "中官正", "秋官正", "冬官正", "太史局丞", "太史局直长",
        "灵台郎", "保章正", "挈壶正", "局生", "爵", "王",
    ]
    assert [F[i]["title"] for i in range(482, 502)] == expected
    extract_last_medical_rank()
    extract_astronomical_ranks()
    extract_peerage_system()
    extract_king_rank()


if __name__ == "__main__":
    main()
