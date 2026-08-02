#!/usr/bin/env python3
"""修复 ch2t7 的1080年伪根节点：存废语义、缺失终点与层级分类。

本脚本只写入原文明载的结构化解释，并为每次更新补齐 Citations 与
BuildRecords。所有操作均幂等；正式库执行前应先制作文件级备份。
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data/database/song_bureaucracy_entries_ch2t7.db"
DEFAULT_DICTIONARY = REPO_ROOT / "data/database/song_bureaucracy_dictionary_ch2t7.db"


@dataclass(frozen=True)
class EventUpdate:
    timepoint_id: int
    entity: str
    old_event: str
    new_event: str
    source_entry: str
    source_page: str
    quotation: str
    decision: str


@dataclass(frozen=True)
class TerminalSpec:
    entity: str
    previous_timepoint_id: int
    time: str
    event: str
    source_entry: str
    source_page: str
    quotation: str
    decision: str


@dataclass(frozen=True)
class CategorySpec:
    timepoint_id: int
    entity: str
    category: str
    source_entry: str
    source_page: str
    quotation: str
    decision: str


@dataclass(frozen=True)
class EvolutionSpec:
    source_timepoint_id: int
    target_timepoint_id: int
    source_entry: str
    source_page: str
    quotation: str
    decision: str


EVENT_UPDATES = (
    EventUpdate(792, "三司", "三部重合为一司", "三部重合为三司",
                "三司", "125", "至咸平六年重合为一司",
                "原文在三司条中明确咸平六年重新合为三司；补明结果实体，避免旧关系无法替代实体自身的复置证据。"),
    EventUpdate(4406, "详定大乐所", "置；讨论、修订大乐制度", "始置；讨论、修订大乐制度",
                "详定大乐所", "303", "临时机构名。仁宗皇祐二年置。",
                "原文明确此临时机构于皇祐二年置；补明激活语义，使临时机构按本次活动证据形成有限时间窗。"),
    EventUpdate(5244, "牛羊司", "重新并入宰杀务", "接收重新并入的宰杀务",
                "牛羊司", "330", "至嘉祐五年（1060）并入",
                "原文的被并入者是宰杀务，不是牛羊司；修正主客体，避免误判牛羊司终止。"),
    EventUpdate(6979, "国子监", "由国子学复改称", "由国子学复改称国子监",
                "国子监", "380", "淳化五年三月二十四日复改称国子监",
                "原文明确国子学复改为国子监；补足结果实体名，使国子监正确重新激活。"),
    EventUpdate(6700, "都大店宅务兼修造司", "修造司改隶八作司",
                "废罢；修造司析出并隶八作司，复为都大店宅务",
                "左右厢店宅务", "372", "大中祥符元年修造司隶八作司",
                "原文明载大中祥符元年修造司析出改隶八作司；都大店宅务兼修造司这一复合机构随之终止。"),
    EventUpdate(250, "吏部尚书铨", "为差遣院所代", "废罢，为差遣院所代",
                "吏部尚书铨", "100", "为差遣院所代",
                "原文明确吏部尚书铨被差遣院取代；将终止语义规范为废罢。"),
    EventUpdate(390, "编修诸司敕式所(令式所)", "并入详定一司敕令所", "废罢，并入详定一司敕令所",
                "详定一司敕令所", "106", "并入“详定一司敕令所”",
                "原文明确各司编敕机构并入详定一司敕令所；规范终止语义。"),
    EventUpdate(436, "看详编修中书门下条例所", "编修中书条例司罢", "废罢，编修中书条例司罢",
                "看详编修中书门下条例所", "109", "编修中书条例司、修司农寺条例司皆罢",
                "原文明确编修中书条例司罢；规范当前实体终止语义。"),
    EventUpdate(463, "都大提举在京诸司库务司", "罢都大提举司", "废罢，都大提举司罢",
                "都大提举在京诸司库务司", "110", "元年（1078）十二月十九日罢",
                "原文明确都大提举司于元丰元年罢；规范当前实体终止语义。"),
    EventUpdate(685, "剥马务", "内、外务合为皮剥所", "废罢，内、外剥马务合为皮剥所",
                "剥马务", "121", "合内、外剥马务为一局",
                "原文明确内外剥马务合并并改称皮剥所；规范旧实体终止语义。"),
    EventUpdate(1216, "马步军粮料院", "复分为马军、步军粮料院", "废罢，复分为马军、步军粮料院",
                "粮料院", "139", "马、步粮料院复分为二院",
                "原文明确马步军粮料院复分为马军、步军粮料院；规范合设实体终止语义。"),
    EventUpdate(1239, "马军专勾司", "两专勾司合并", "废罢，马军、步军两专勾司合并为马步军专勾司",
                "马步军专勾司", "140", "两专勾司合二为一",
                "原文明确马军专勾司参与合并；规范旧实体终止语义。"),
    EventUpdate(1241, "步军专勾司", "两专勾司合并", "废罢，马军、步军两专勾司合并为马步军专勾司",
                "马步军专勾司", "140", "两专勾司合二为一",
                "原文明确步军专勾司参与合并；规范旧实体终止语义。"),
    EventUpdate(3772, "殿中省", "名存实废，仅办理大礼仪仗法物", "实体官署实废；名存实废，仅办理大礼仪仗法物",
                "殿中省", "287", "北宋前期名存实废",
                "原文明确北宋前期殿中省名存实废；标记实体官署当时不作为运行机构存在。"),
    EventUpdate(5688, "左、右骐骥、六坊监", "左、右骐骥两院、天驷四监、左、右天厩二坊合称",
                "废罢；天驷四监合并后，六坊监改称四坊监",
                "左、右骐骥、六坊监", "343", "“六坊监”得改称“四坊、监”",
                "原文明确熙宁三年后六坊监称谓退出并改称四坊监。"),
    EventUpdate(6800, "香药库", "别置内香药库后，香药库有内、外之分",
                "废罢；原单一香药库分为内香药库、外香药库",
                "香药库", "374", "天禧五年六月十七日，东华门外别置内香药库，香药库遂有内、外之分",
                "原文明载天禧五年香药库分为内、外两库；原单一香药库不应在分设后继续作为第三座具体库显示。"),
    EventUpdate(7110, "御书院", "临时设置善书祇应一人",
                "见有御书院，善书祗应人一人供职",
                "国子书博士", "383", "非品官，临时设置，以授御书院善书祗应人",
                "原文中的临时设置对象是国子书博士官，不是御书院；修正事件主语，避免把官职的临时性误记成机构存废。"),
)


TERMINALS = (
    TerminalSpec("详定编敕所", 375, "北宋熙宁八年九月", "废罢，并入详定一司敕令所",
                 "详定一司敕令所", "106", "熙宁八年九月，所有各司编敕机构并入“详定一司敕令所”",
                 "原文明载熙宁八年九月所有编敕机构并入详定一司敕令所；补建详定编敕所终点。"),
    TerminalSpec("印司", 1255, "北宋元丰三年", "废罢，随提举三司帐司、勾院磨勘司罢置",
                 "提举三司帐司、勾院磨勘司", "140", "元丰三年罢",
                 "印司是该临时提举司的附属机构；原文明载上级于元丰三年罢，补建其随上级终止节点。"),
    TerminalSpec("知杂司", 1256, "北宋元丰三年", "废罢，随提举三司帐司、勾院磨勘司罢置",
                 "提举三司帐司、勾院磨勘司", "140", "元丰三年罢",
                 "此知杂司时间点是该临时提举司的附属机构；原文明载上级于元丰三年罢，补建其随上级终止节点。"),
    TerminalSpec("司天台", 3466, "北宋端拱元年九月", "废罢，改称司天监",
                 "司天监", "268", "宋初沿唐制，称司天台。太宗端拱元年九月，始见有司天监之称",
                 "原文将宋初司天台与端拱元年始见的司天监连续叙述；补建司天台终点。"),
    TerminalSpec("提举在京诸司库务司", 5794, "北宋元丰元年十二月十九日",
                 "废罢，随都大提举在京诸司库务司罢置",
                 "都大提举在京诸司库务司", "110", "神宗元丰元年（1078）十二月十九日罢",
                 "该实体是都大提举在京诸司库务司的省称异名；原文明载本司元丰元年罢，补建终点。"),
    TerminalSpec("都大提举在京诸司库务所", 5916, "北宋元丰元年十二月十九日",
                 "废罢，随都大提举在京诸司库务司罢置",
                 "都大提举在京诸司库务司", "110", "神宗元丰元年（1078）十二月十九日罢",
                 "该实体是都大提举在京诸司库务司的治所异称；原文明载本司元丰元年罢，补建终点。"),
    TerminalSpec("茶库", 6558, "北宋咸平六年", "废罢，二库合并为都茶库",
                 "都茶库", "369", "初分二库，咸平六年合为一库加“都”字",
                 "原文明载原来的两茶库于咸平六年合为都茶库；补建茶库终点。"),
    TerminalSpec("左计司", 826, "北宋淳化五年十二月二十四日", "废罢，与总计司同时废止",
                 "左计司", "126", "置废时间与“总 计司”同。",
                 "左计司原文明确置废时间与总计司相同；补建淳化五年废止终点。"),
    TerminalSpec("右计司", 827, "北宋淳化五年十二月二十四日", "废罢，与总计司同时废止",
                 "左计司", "126", "置废时间与“总 计司”同。",
                 "右计司条详参左计；左计原文明确左右计司置废时间均与总计司相同。"),
    TerminalSpec("马步军粮料院", 1216, "北宋熙宁六年正月五日", "至迟已废罢，复分为马军、步军粮料院",
                 "都大提举在京诸司库务司", "110", "三粮料院等分别由三司、都大提举市易司、开封府归隶本司",
                 "原文明载熙宁六年已存在三粮料院，证明此前马步军粮料院已复分；补建可用于1080截面的最迟终点。"),
    TerminalSpec("天驷左第一监", 5674, "北宋熙宁三年三月六日", "废罢，并为左、右天驷二监",
                 "左、右天驷监", "342", "熙宁三年三月六日并为两监",
                 "原文明确天驷四监于熙宁三年合并为两监；补建旧实例终点。"),
    TerminalSpec("天驷左第二监", 5675, "北宋熙宁三年三月六日", "废罢，并为左、右天驷二监",
                 "左、右天驷监", "342", "熙宁三年三月六日并为两监",
                 "原文明确天驷四监于熙宁三年合并为两监；补建旧实例终点。"),
    TerminalSpec("天驷右第一监", 5676, "北宋熙宁三年三月六日", "废罢，并为左、右天驷二监",
                 "左、右天驷监", "342", "熙宁三年三月六日并为两监",
                 "原文明确天驷四监于熙宁三年合并为两监；补建旧实例终点。"),
    TerminalSpec("天驷右第二监", 5677, "北宋熙宁三年三月六日", "废罢，并为左、右天驷二监",
                 "左、右天驷监", "342", "熙宁三年三月六日并为两监",
                 "原文明确天驷四监于熙宁三年合并为两监；补建旧实例终点。"),
    TerminalSpec("架阁御鞍库房", 5741, "北宋天禧三年四月", "废罢，改称鞍辔库",
                 "鞍辔库", "344", "已见正称“鞍辔库”局名",
                 "原文明确架阁御鞍库房为鞍辔库设置之始，天禧三年已用鞍辔库正称；补建旧称终点。"),
    TerminalSpec("译经院", 5955, "北宋太平兴国八年", "废罢，赐额传法后改称传法院",
                 "传法院", "350", "八年，赐院额名“传法”",
                 "原文明确译经院次年赐额传法并改称传法院；补建旧称终点。"),
    TerminalSpec("折中仓", 6236, "北宋淳化二年", "废罢，改名折博仓",
                 "折中仓", "361", "淳化二年改名折博仓。",
                 "原文明确折中仓于淳化二年改名折博仓；补建旧称终点。"),
)


CATEGORIES = (
    CategorySpec(3694, "实录院", "临时修实录机构", "实录院", "282",
                 "元丰改制前，实录院于崇文院内临时设局",
                 "原文明载元丰改制前实录院为遇事临时设局；按临时机构的离散证据期参与年度截面。"),
    CategorySpec(6576, "诸路", "路级机构", "斗秤务", "369",
                 "诏于诸路转运司治所所在州各置斗秤务",
                 "原文明载该节点表示诸路转运司治所范围，不属于中央机构；归为路级。"),
    CategorySpec(6591, "秦凤路市易司", "路级机构", "在京市易务", "370",
                 "在秦凤路置市易司",
                 "原文明载该市易司设置于秦凤路；归为路级机构。"),
    CategorySpec(6617, "益州交子务", "路级机构", "益州交子务", "371",
                 "成立官营交子务于成都，即益州交子务，又称四川交子务",
                 "原文明载该务设于成都并服务四川；归为路级机构。"),
    CategorySpec(6668, "开封府", "州府机构", "抵当所", "372",
                 "先后隶开封府、都提举市易司、太府寺",
                 "开封府是府级地方行政机构，不属于中央机构；归为州府机构。"),
    CategorySpec(1320, "提举买马监牧司", "路级机构", "群牧行司", "145",
                 "在秦州、凤翔府等地往来应接督办买马公事",
                 "原文明载该司在秦州、凤翔府等地办理买马，归为路级机构。"),
    CategorySpec(1336, "提举陕西等路买马监牧司", "路级机构", "提举陕西等路买马监牧司", "148",
                 "专领本路监牧及买马公事",
                 "原文明载该司专领陕西本路监牧买马，归为路级机构。"),
    CategorySpec(1380, "提举秦凤等路买马监牧司", "路级机构", "提举秦凤等路买马监牧司", "148",
                 "专领秦凤等路分买马、养马、起发马纲等公事",
                 "原文明载该司专领秦凤等路买马养马，归为路级机构。"),
    CategorySpec(2419, "茶场司", "路级机构", "茶场司", "207",
                 "于成都府路诸州创置茶场司",
                 "原文明载茶场司设置于成都府路诸州，归为路级机构。"),
    CategorySpec(7185, "西京国子监", "州府机构", "三京国子监", "385",
                 "北宋西京河南府、南京应天府、北京大名府，于真宗、仁宗朝后，分别置国子监以代府学",
                 "原文明载西京国子监设于河南府并取代府学，不是东京中央国子监；归为州府机构。"),
    CategorySpec(7186, "南京国子监", "州府机构", "三京国子监", "385",
                 "北宋西京河南府、南京应天府、北京大名府，于真宗、仁宗朝后，分别置国子监以代府学",
                 "原文明载南京国子监设于应天府并取代府学，不是东京中央国子监；归为州府机构。"),
    CategorySpec(7187, "北京国子监", "州府机构", "三京国子监", "385",
                 "北宋西京河南府、南京应天府、北京大名府，于真宗、仁宗朝后，分别置国子监以代府学",
                 "原文明载北京国子监设于大名府并取代府学，不是东京中央国子监；归为州府机构。"),
    CategorySpec(7291, "太学馆", "临时科举试机构", "太学生", "388",
                 "国子监临时开太学馆",
                 "原文明载太学馆仅在礼部科举试期间临时开设，省试后即解散；按临时机构的离散证据期参与年度截面。"),
)


EVOLUTIONS = (
    EvolutionSpec(375, 386, "详定一司敕令所", "106",
                  "熙宁八年九月，所有各司编敕机构并入“详定一司敕令所”",
                  "原文明载详定编敕所并入详定一司敕令所；补建前后演变关系。"),
    EvolutionSpec(3466, 3472, "司天监", "268",
                  "宋初沿唐制，称司天台。太宗端拱元年九月，始见有司天监之称",
                  "原文连续叙述宋初司天台到司天监的称谓演变；补建前后演变关系。"),
)


def validate_quotations(dictionary_path: Path) -> None:
    dictionary = sqlite3.connect(dictionary_path)
    try:
        specs = (*EVENT_UPDATES, *TERMINALS, *CATEGORIES, *EVOLUTIONS)
        for spec in specs:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (spec.source_entry, spec.source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{spec.source_entry} 第{spec.source_page}页")
            if not any(spec.quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{spec.source_entry} / {spec.quotation}")
    finally:
        dictionary.close()


def timepoint_entity(connection: sqlite3.Connection, timepoint_id: int) -> tuple[int, str]:
    row = connection.execute(
        "SELECT e.id,e.title FROM Timepoints t JOIN Entities e ON e.id=t.entity_id WHERE t.id=?",
        (timepoint_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"时间点不存在：{timepoint_id}")
    return int(row[0]), str(row[1])


def append_audit(
    connection: sqlite3.Connection,
    target_table: str,
    target_id: int,
    source_entry: str,
    source_page: str,
    quotation: str,
    decision: str,
) -> None:
    exists = connection.execute(
        """
        SELECT 1 FROM BuildRecords
        WHERE target_table=? AND target_id=? AND source_entry=? AND decision=?
        """,
        (target_table, target_id, source_entry, decision),
    ).fetchone()
    if exists is None:
        connection.execute(
            """
            INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)
            VALUES (?,?,?,?,?)
            """,
            (target_table, target_id, source_entry, source_page, decision),
        )
    citation = f"《宋代官制辞典》第{source_page}页“{source_entry}”条"
    row = connection.execute(
        """
        SELECT id FROM Citations
        WHERE target_table=? AND target_id=? AND citation=? AND quotation=?
        ORDER BY id LIMIT 1
        """,
        (target_table, target_id, citation, quotation),
    ).fetchone()
    if row is None:
        cursor = connection.execute(
            """
            INSERT INTO Citations(target_table,target_id,citation,quotation,note,conflict_flag)
            VALUES (?,?,?,?,?,0)
            """,
            (target_table, target_id, citation, quotation, decision),
        )
        citation_id = int(cursor.lastrowid)
        connection.execute(
            """
            INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)
            VALUES ('Citations',?,?,?,'为1080年伪根节点修复保存同条辞典证据。')
            """,
            (citation_id, source_entry, source_page),
        )


def apply_repairs(db_path: Path, dictionary_path: Path = DEFAULT_DICTIONARY) -> dict[str, int]:
    validate_quotations(dictionary_path)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON")
    counts = {
        "events_updated": 0,
        "terminals_inserted": 0,
        "categories_updated": 0,
        "evolutions_inserted": 0,
        "reused": 0,
    }
    try:
        connection.execute("BEGIN IMMEDIATE")
        for spec in EVENT_UPDATES:
            _, title = timepoint_entity(connection, spec.timepoint_id)
            if title != spec.entity:
                raise ValueError(f"时间点实体不符：{spec.timepoint_id}={title}，预期{spec.entity}")
            current = connection.execute(
                "SELECT event FROM Timepoints WHERE id=?", (spec.timepoint_id,)
            ).fetchone()[0]
            if current == spec.new_event:
                counts["reused"] += 1
            elif current == spec.old_event:
                connection.execute(
                    "UPDATE Timepoints SET event=? WHERE id=?", (spec.new_event, spec.timepoint_id)
                )
                counts["events_updated"] += 1
            else:
                raise ValueError(f"时间点{spec.timepoint_id}事件已漂移：{current}")
            append_audit(connection, "Timepoints", spec.timepoint_id, spec.source_entry,
                         spec.source_page, spec.quotation, spec.decision)

        for spec in TERMINALS:
            entity_id, title = timepoint_entity(connection, spec.previous_timepoint_id)
            if title != spec.entity:
                raise ValueError(f"前序时间点实体不符：{spec.previous_timepoint_id}={title}，预期{spec.entity}")
            existing = connection.execute(
                "SELECT id FROM Timepoints WHERE entity_id=? AND time=? AND event=? ORDER BY id LIMIT 1",
                (entity_id, spec.time, spec.event),
            ).fetchone()
            if existing is None:
                previous = connection.execute(
                    "SELECT succ_id,attr_category,attr_officer_type,attr_grade FROM Timepoints WHERE id=?",
                    (spec.previous_timepoint_id,),
                ).fetchone()
                if previous[0] is not None:
                    raise ValueError(f"前序时间点{spec.previous_timepoint_id}已有后继{previous[0]}")
                cursor = connection.execute(
                    """
                    INSERT INTO Timepoints(
                        entity_id,time,event,prev_id,succ_id,
                        attr_category,attr_officer_type,attr_grade,quotation
                    ) VALUES (?,?,?,?,NULL,?,?,?,?)
                    """,
                    (entity_id, spec.time, spec.event, spec.previous_timepoint_id,
                     previous[1], previous[2], previous[3], spec.quotation),
                )
                terminal_id = int(cursor.lastrowid)
                connection.execute(
                    "UPDATE Timepoints SET succ_id=? WHERE id=?",
                    (terminal_id, spec.previous_timepoint_id),
                )
                counts["terminals_inserted"] += 1
            else:
                terminal_id = int(existing[0])
                counts["reused"] += 1
                connection.execute(
                    "UPDATE Timepoints SET succ_id=? WHERE id=? AND succ_id IS NULL",
                    (terminal_id, spec.previous_timepoint_id),
                )
            append_audit(connection, "Timepoints", terminal_id, spec.source_entry,
                         spec.source_page, spec.quotation, spec.decision)

        for spec in CATEGORIES:
            _, title = timepoint_entity(connection, spec.timepoint_id)
            if title != spec.entity:
                raise ValueError(f"分类时间点实体不符：{spec.timepoint_id}={title}，预期{spec.entity}")
            current = connection.execute(
                "SELECT attr_category FROM Timepoints WHERE id=?", (spec.timepoint_id,)
            ).fetchone()[0]
            if current == spec.category:
                counts["reused"] += 1
            else:
                connection.execute(
                    "UPDATE Timepoints SET attr_category=? WHERE id=?",
                    (spec.category, spec.timepoint_id),
                )
                counts["categories_updated"] += 1
            append_audit(connection, "Timepoints", spec.timepoint_id, spec.source_entry,
                         spec.source_page, spec.quotation, spec.decision)

        for spec in EVOLUTIONS:
            source_entity_id, _ = timepoint_entity(connection, spec.source_timepoint_id)
            target_entity_id, _ = timepoint_entity(connection, spec.target_timepoint_id)
            existing = connection.execute(
                """
                SELECT r.id FROM Relationships r
                JOIN Timepoints s ON s.id=r.subject_id
                JOIN Timepoints o ON o.id=r.object_id
                WHERE r.relation_type='前后演变' AND s.entity_id=? AND o.entity_id=?
                ORDER BY r.id LIMIT 1
                """,
                (source_entity_id, target_entity_id),
            ).fetchone()
            if existing is None:
                cursor = connection.execute(
                    """
                    INSERT INTO Relationships(subject_id,object_id,relation_type,staff_quota,staff_type,quotation)
                    VALUES (?,?,'前后演变',NULL,NULL,?)
                    """,
                    (spec.source_timepoint_id, spec.target_timepoint_id, spec.quotation),
                )
                relation_id = int(cursor.lastrowid)
                counts["evolutions_inserted"] += 1
            else:
                relation_id = int(existing[0])
                counts["reused"] += 1
            append_audit(connection, "Relationships", relation_id, spec.source_entry,
                         spec.source_page, spec.quotation, spec.decision)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    args = parser.parse_args()
    counts = apply_repairs(args.db.resolve(), args.dictionary.resolve())
    print(" ".join(f"{key}={value}" for key, value in counts.items()))
    print(f"db={args.db.resolve()}")


if __name__ == "__main__":
    main()
