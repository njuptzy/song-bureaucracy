#!/usr/bin/env python3
"""提取 chapter11t12 第522-541条：勋级末六转与检校官前十阶。"""

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
    "extract_11t12_502_521_helpers", HERE / "extract_11t12_502_521.py"
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


F = {entry_id: load(entry_id) for entry_id in range(522, 542)}


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


def find_timepoint(writer, title, time):
    entity = writer.find_entity(title, "官职")
    assert entity is not None, (title, time)
    timepoint = writer.find_timepoint(entity, time)
    assert timepoint is not None, (title, time)
    return timepoint


def group_membership(writer, entry_id, group_title, title, time, event, quote,
                     order, *, category, member_officer):
    _, group = state(
        writer, entry_id, group_title, time, f"{group_title}制度状态", quote,
        f"建立或复用{group_title}{time}统称节点。",
        category=category, officer="职官总名", sort_order=order,
    )
    _, member = state(
        writer, entry_id, title, time, event, quote,
        f"建立或复用{title}{time}实例节点。",
        category=category, officer=member_officer, sort_order=order,
    )
    relation(
        writer, entry_id, group, member, "统称与实例", quote,
        f"原文明示{title}属于{group_title}。",
    )
    return member


MERIT_DETAILS = {
    522: ("上骑都尉", 6, "正五品"),
    523: ("骑都尉", 5, None),
    524: ("骁骑尉", 4, "正六品上"),
    525: ("飞骑尉", 3, "从六品上"),
    526: ("云骑尉", 2, "正七品上"),
    527: ("武骑尉", 1, "从七品上"),
}


def enrich_merit_rank(writer, entry_id, title, turn, grade):
    quote = Q(entry_id, F[entry_id]["text"])
    north = find_timepoint(writer, title, "北宋")
    grade_text = f"；{grade}" if grade else ""
    append_event(
        writer, north, f"勋官十二转之第{turn}转{grade_text}",
        f"据{title}专条补足北宋勋级位次和品级。",
        category="勋制", officer="勋官", grade=grade,
    )
    cite(
        writer, "Timepoints", north, entry_id, quote,
        f"补证{title}为北宋勋官第{turn}转及其品级。",
    )
    group = find_timepoint(writer, "勋", "北宋")
    relation(
        writer, entry_id, group, north, "统称与实例", quote,
        f"原文明示{title}属于北宋勋官十二转。",
    )


def extract_merit_details():
    for entry_id, (title, turn, grade) in MERIT_DETAILS.items():
        writer = W(entry_id)
        enrich_merit_rank(writer, entry_id, title, turn, grade)

        if entry_id == 522:
            origin = Q(entry_id, "“骑都尉”之名，始于西汉高祖元年")
            state(
                writer, entry_id, title, "西汉高祖元年（前206年）",
                "骑都尉之名始见；后为上骑都尉名源", origin,
                "建立上骑都尉的西汉名源节点。", category="前代职源",
                officer="勋官", sort_order=-20600000,
            )
        elif entry_id == 523:
            origin = Q(entry_id, "西汉高祖元年（前206），以建武侯靳歙为骑都尉")
            state(
                writer, entry_id, title, "西汉高祖元年（前206年）",
                "以建武侯靳歙为骑都尉", origin,
                "建立骑都尉西汉职源节点。", category="前代职源",
                officer="勋官", sort_order=-20600000,
            )
            tang = Q(entry_id, "唐沿袭，但为勋官之一转，无职事")
            tang_tp = find_timepoint(writer, title, "唐武德七年")
            append_event(writer, tang_tp, "作为勋官，无职事", "补充唐代骑都尉性质。")
            cite(writer, "Timepoints", tang_tp, entry_id, tang, "补证唐代骑都尉无职事。")

            early = Q(entry_id, "太宗淳化元年正月，定朝官以上加勋级，始自骑都尉")
            state(
                writer, entry_id, title, "北宋太宗淳化元年正月",
                "定为朝官以上加勋始级", early,
                "记录淳化元年骑都尉为加勋始级。", category="勋制",
                officer="勋官", sort_order=99001000,
            )
            change = Q(entry_id, "元丰六年十二月，又改为始自武骑尉")
            _, old = state(
                writer, entry_id, title, "北宋神宗元丰六年十二月",
                "不再作为朝官加勋始级，改始于武骑尉", change,
                "记录元丰六年骑都尉始级地位变化。", category="勋制",
                officer="勋官", sort_order=108312000,
            )
            _, new = state(
                writer, entry_id, "武骑尉", "北宋神宗元丰六年十二月",
                "改为朝官加勋始级", change,
                "建立武骑尉元丰六年十二月始级节点。", category="勋制",
                officer="勋官", sort_order=108312000,
            )
            relation(
                writer, entry_id, old, new, "前后演变", change,
                "元丰六年十二月朝官加勋始级由骑都尉改为武骑尉。",
            )
        else:
            origin = Q(entry_id, "隋文帝开皇三年始置，为武散官八尉之一")
            state(
                writer, entry_id, title, "隋文帝开皇三年",
                "始置，为武散官八尉之一", origin,
                f"建立{title}隋代职源节点。", category="前代职源",
                officer="勋官", sort_order=58300000,
            )

        if entry_id == 527:
            november = Q(entry_id, "元丰六年十一月，朝官加勋自武骑尉始")
            state(
                writer, entry_id, title, "北宋神宗元丰六年十一月",
                "朝官加勋自武骑尉始", november,
                "记录元丰六年十一月武骑尉始级节点。", category="勋制",
                officer="勋官", sort_order=108311000,
            )
            initial = Q(entry_id, "太宗定为幕职州县官、京官加勋之始级")
            _, initial_tp = state(
                writer, entry_id, title, "北宋太宗时期",
                "定为幕职州县官、京官加勋始级", initial,
                "记录太宗朝武骑尉为幕职州县官、京官加勋始级。",
                category="勋制", officer="勋官", sort_order=97600000,
            )
            cite(writer, "Timepoints", initial_tp, entry_id, initial, "补证太宗朝加勋始级。")

        if entry_id in (523, 527):
            civil = Q(
                entry_id,
                "政和三年二月八日罢文官加勋"
                if entry_id == 523
                else "徽宗政和三年二月八日，罢文官加勋",
            )
            group_civil = find_timepoint(writer, "勋", "北宋徽宗政和三年二月八日")
            cite(writer, "Timepoints", group_civil, entry_id, civil, "专条补证停止文官加勋。")
            military = Q(
                entry_id,
                "南宋绍兴三年二月八日罢武官加勋"
                if entry_id == 523
                else "南宋绍兴三年二月八日，罢武官加勋",
            )
            group_military = find_timepoint(writer, "勋", "南宋高宗绍兴三年二月八日")
            cite(writer, "Timepoints", group_military, entry_id, military, "专条补证停止武官加勋。")
        writer.commit()


NINETEEN_FIRST = (
    "检校太师", "检校太尉", "检校太傅", "检校太保", "检校司徒", "检校司空",
)
YUANFENG_SIX = NINETEEN_FIRST
ZHENGHE_SIX = (
    "检校太师", "检校太傅", "检校太保", "检校少师", "检校少傅", "检校少保",
)


def inspection_group(writer, entry_id, time, event, quote, order):
    _, group = state(
        writer, entry_id, "检校官", time, event, quote,
        f"建立或复用检校官{time}制度节点。", category="检校官阶",
        officer="职官总名", sort_order=order,
    )
    return group


def inspection_member(writer, entry_id, title, time, event, quote, order):
    group = inspection_group(
        writer, entry_id, time, f"{time}检校官阶", quote, order
    )
    _, member = state(
        writer, entry_id, title, time, event, quote,
        f"建立或复用{title}{time}检校官节点。", category="检校官阶",
        officer="检校虚衔", sort_order=order,
    )
    relation(
        writer, entry_id, group, member, "统称与实例", quote,
        f"原文明示{title}属于{time}检校官阶。",
    )
    return member


def inspection_evolution(writer, entry_id, old_title, new_title, time, quote,
                         order):
    _, old = state(
        writer, entry_id, old_title, time, f"旧检校官名改为{new_title}", quote,
        f"建立{old_title}政和改名节点。", category="检校官阶改革",
        officer="检校虚衔", sort_order=order,
    )
    _, new = state(
        writer, entry_id, new_title, time, f"由{old_title}改名而来", quote,
        f"建立{new_title}政和承接节点。", category="检校官阶改革",
        officer="检校虚衔", sort_order=order,
    )
    relation(
        writer, entry_id, old, new, "前后演变", quote,
        f"原文明示{old_title}在政和改为{new_title}。",
    )


def extract_inspection_system():
    entry_id = 528
    writer = W(entry_id)
    origin = Q(entry_id, "“检校”之名始于东晋太元中（376—396），以吴混之为检校御史，系正式职事官；其前身为西晋司隶校尉")
    state(
        writer, entry_id, "检校官", "东晋太元年间（376—396）",
        "检校之名始见，以吴混之为检校御史，属正式职事官", origin,
        "建立检校官东晋名源节点。", category="前代职源",
        officer="职官总名", sort_order=37600000,
    )
    tang_early = Q(entry_id, "唐初虽非正官，但有实职，含有代办某官事、点检某官事之义")
    state(
        writer, entry_id, "检校官", "唐初",
        "虽非正官但有实职，代办或点检某官事", tang_early,
        "建立唐初检校官实职节点。", category="前代职源",
        officer="职官总名", sort_order=61800000,
    )
    tang_late = Q(entry_id, "唐玄宗以后，检校官变为虚衔，地方使职带检校三公、三师及台省官之类，表示迁转经历和尊崇的地位，其后渐渐形成了自三公、三师、尚书左右仆射至水部郎检校官十三阶")
    state(
        writer, entry_id, "检校官", "唐玄宗以后",
        "由实职变为虚衔，表示迁转经历与尊崇地位，渐成十三阶", tang_late,
        "建立唐玄宗以后检校官虚衔化节点。", category="前代职源",
        officer="职官总名", sort_order=71300000,
    )
    north = Q(entry_id, "北宋沿置，自检校太师、太尉、太傅、太保、司徒、司空至国子祭酒、水部员外郎，共十九阶")
    north_group = inspection_group(
        writer, entry_id, "北宋前期", "沿置检校官十九阶", north,
        96000000,
    )
    for index, title in enumerate(NINETEEN_FIRST, 1):
        _, member = state(
            writer, entry_id, title, "北宋前期",
            f"检校官十九阶前六阶之一（第{index}阶）", north,
            f"总条明列{title}为北宋检校官十九阶前六阶之一。",
            category="检校官十九阶", officer="检校虚衔",
            sort_order=96000000,
        )
        relation(
            writer, entry_id, north_group, member, "统称与实例", north,
            f"{title}为北宋前期检校官十九阶实例。",
        )

    reform = Q(entry_id, "神宗元丰三年九月十七日，除检校太师、太傅、太保与检校太尉、司徒、司空六阶保留外，余十三阶检校官皆罢")
    yuanfeng_group = inspection_group(
        writer, entry_id, "北宋神宗元丰三年九月十七日",
        "保留太师、太尉、太傅、太保、司徒、司空六阶，余十三阶停止",
        reform, 108009017,
    )
    for index, title in enumerate(YUANFENG_SIX, 1):
        _, member = state(
            writer, entry_id, title, "北宋神宗元丰三年九月十七日",
            f"元丰检校官六阶之第{index}阶", reform,
            f"总条明列{title}为元丰保留六阶之一。",
            category="元丰检校官六阶", officer="检校虚衔",
            sort_order=108009017,
        )
        relation(
            writer, entry_id, yuanfeng_group, member, "统称与实例", reform,
            f"{title}为元丰检校官六阶实例。",
        )
    relation(
        writer, entry_id, north_group, yuanfeng_group, "前后演变", reform,
        "元丰三年检校官十九阶裁并为六阶。",
    )

    zhenghe = Q(entry_id, "徽宗政和二年九月二十五日改定三公、三少官名，与之相应，检校三师易为检校三公（检校太师、太傅、太保），检校三公易为检校三少（检校少师、少傅、少保）")
    zhenghe_group = inspection_group(
        writer, entry_id, "北宋徽宗政和二年九月二十五日",
        "改为检校三公、三少六阶", zhenghe, 111209025,
    )
    for index, title in enumerate(ZHENGHE_SIX, 1):
        _, member = state(
            writer, entry_id, title, "北宋徽宗政和二年九月二十五日",
            f"政和检校官六阶之第{index}阶", zhenghe,
            f"总条明列{title}为政和检校官六阶实例。",
            category="政和检校官六阶", officer="检校虚衔",
            sort_order=111209025,
        )
        relation(
            writer, entry_id, zhenghe_group, member, "统称与实例", zhenghe,
            f"{title}为政和检校官六阶实例。",
        )
    relation(
        writer, entry_id, yuanfeng_group, zhenghe_group, "前后演变", zhenghe,
        "政和二年元丰检校六阶改定为检校三公、三少六阶。",
    )
    for old_title, new_title in (
        ("检校太尉", "检校少师"),
        ("检校司徒", "检校少傅"),
        ("检校司空", "检校少保"),
    ):
        inspection_evolution(
            writer, entry_id, old_title, new_title,
            "北宋徽宗政和二年九月二十五日", zhenghe, 111209025,
        )

    progression = Q(entry_id, "文臣累加至检校少师，则为开府仪同三司；武臣累加至检校少师，则为太尉")
    append_event(
        writer, zhenghe_group,
        "文臣累加至检校少师转开府仪同三司；武臣至检校少师转太尉",
        "补充检校官累加终点。",
    )
    cite(writer, "Timepoints", zhenghe_group, entry_id, progression, "补证检校官累加终点。")
    south = Q(entry_id, "南宋后期（宁宗朝以后），文武官除节度使后，便抹过检校官阶，径除开府仪同三司，至三少、三公")
    state(
        writer, entry_id, "检校官", "南宋后期（宁宗朝以后）",
        "除节度使后越过检校官阶，径除开府仪同三司，进至三少、三公",
        south, "记录南宋后期检校官阶被越过。", category="检校官阶",
        officer="职官总名", sort_order=119500000,
    )
    writer.commit()


INSPECTION_DETAILS = {
    529: ("检校太师", 1, 1, 1),
    530: ("检校太尉", 2, 2, None),
    531: ("检校太傅", 3, 3, 2),
    532: ("检校太保", 4, 4, 3),
    533: ("检校司徒", 5, 5, None),
    534: ("检校司空", 6, 6, None),
    535: ("检校少师", None, None, 4),
    536: ("检校少傅", None, None, 5),
    537: ("检校少保", None, None, 6),
    538: ("检校尚书左仆射", 7, None, None),
    539: ("检校尚书右仆射", 8, None, None),
    540: ("检校吏部尚书", 9, None, None),
    541: ("检校兵部尚书", 10, None, None),
}


def abolish(writer, entry_id, title, source_time, end_time, quote, order):
    old = find_timepoint(writer, title, source_time)
    _, end = state(
        writer, entry_id, title, end_time, "停止此检校官阶", quote,
        f"建立{title}停止节点。", category="检校官阶改革",
        officer="检校虚衔", sort_order=order,
    )
    relation(
        writer, entry_id, old, end, "前后演变", quote,
        f"原文明示{title}在{end_time}停止。",
    )
    return end


def extract_inspection_details():
    for entry_id, (title, north_rank, yuanfeng_rank, zhenghe_rank) in INSPECTION_DETAILS.items():
        writer = W(entry_id)
        main = Q(entry_id, F[entry_id]["text"])
        if north_rank is not None:
            north = inspection_member(
                writer, entry_id, title, "北宋前期",
                f"检校官十九阶之第{north_rank}阶", main, 96000000,
            )
            append_event(
                writer, north, f"检校官十九阶之第{north_rank}阶",
                f"据{title}专条补足北宋位次。",
                category="检校官十九阶", officer="检校虚衔",
            )
            cite(writer, "Timepoints", north, entry_id, main, f"补证{title}北宋前期位次。")
        if yuanfeng_rank is not None:
            yuanfeng = inspection_member(
                writer, entry_id, title, "北宋神宗元丰三年九月十七日",
                f"元丰检校官六阶之第{yuanfeng_rank}阶", main, 108009017,
            )
            append_event(
                writer, yuanfeng, f"元丰检校官六阶之第{yuanfeng_rank}阶",
                f"据{title}专条补足元丰位次。",
                category="元丰检校官六阶", officer="检校虚衔",
            )
            cite(writer, "Timepoints", yuanfeng, entry_id, main, f"补证{title}元丰位次。")
        if zhenghe_rank is not None:
            zhenghe = inspection_member(
                writer, entry_id, title, "北宋徽宗政和二年九月二十五日",
                f"政和检校官六阶之第{zhenghe_rank}阶", main, 111209025,
            )
            append_event(
                writer, zhenghe, f"政和检校官六阶之第{zhenghe_rank}阶",
                f"据{title}专条补足政和位次。",
                category="政和检校官六阶", officer="检校虚衔",
            )
            cite(writer, "Timepoints", zhenghe, entry_id, main, f"补证{title}政和位次。")

        if entry_id in (530, 533, 534):
            end_quote = sentence(
                entry_id,
                {
                    530: "徽宗政和二年九月二十五日",
                    533: "政和二年九月二十五日",
                    534: "政和二年九月二十五日后",
                }[entry_id],
            )
            abolish(
                writer, entry_id, title,
                "北宋神宗元丰三年九月十七日",
                "北宋徽宗政和二年九月二十五日", end_quote, 111209025,
            )
        elif entry_id >= 538:
            end_quote = Q(entry_id, "元丰三年九月十七日罢")
            abolish(
                writer, entry_id, title, "北宋前期",
                "北宋神宗元丰三年九月十七日", end_quote, 108009017,
            )

        if entry_id == 530:
            use = Q(entry_id, "为文臣任枢密使、皇子初授官时所加官")
            north = find_timepoint(writer, title, "北宋前期")
            append_event(writer, north, "文臣任枢密使、皇子初授官时所加", "补充检校太尉加官对象。")
            cite(writer, "Timepoints", north, entry_id, use, "补证检校太尉加官对象。")
        elif entry_id == 531:
            use = Q(entry_id, "初授枢密使、使相，及曾任宰相、枢密使官除节度使，加检校太傅")
            north = find_timepoint(writer, title, "北宋前期")
            append_event(writer, north, "初授枢密使、使相等所加", "补充检校太傅加官对象。")
            cite(writer, "Timepoints", north, entry_id, use, "补证检校太傅加官对象。")
        elif entry_id == 532:
            use = Q(entry_id, "宣徽使、节度使初除，加“检校太保”")
            north = find_timepoint(writer, title, "北宋前期")
            append_event(writer, north, "宣徽使、节度使初除时所加", "补充检校太保加官对象。")
            cite(writer, "Timepoints", north, entry_id, use, "补证检校太保加官对象。")
        elif entry_id == 538:
            use = Q(entry_id, "宗室初除使相，加检校尚书左仆射")
            north = find_timepoint(writer, title, "北宋前期")
            append_event(writer, north, "宗室初除使相时所加", "补充检校尚书左仆射加官对象。")
            cite(writer, "Timepoints", north, entry_id, use, "补证宗室加官规则。")
        writer.commit()


def main():
    expected = [
        "上骑都尉", "骑都尉", "骁骑尉", "飞骑尉", "云骑尉", "武骑尉",
        "检校官", "检校太师", "检校太尉", "检校太傅", "检校太保",
        "检校司徒", "检校司空", "检校少师", "检校少傅", "检校少保",
        "检校尚书左仆射", "检校尚书右仆射", "检校吏部尚书", "检校兵部尚书",
    ]
    assert [F[i]["title"] for i in range(522, 542)] == expected
    extract_merit_details()
    extract_inspection_system()
    extract_inspection_details()


if __name__ == "__main__":
    main()
