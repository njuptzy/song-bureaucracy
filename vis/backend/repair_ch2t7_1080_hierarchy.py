#!/usr/bin/env python3
"""补建 ch2t7 中原文明载、且在 1080 年适用的上下级机构关系。

只复用现有时间点，不创建实体或时间点。每条关系同时写入 Citations 与
BuildRecords，并以实体对 + 关系类型幂等去重。
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
class RelationSpec:
    parent: str
    child: str
    subject_timepoint_id: int
    object_timepoint_id: int
    source_entry: str
    source_page: str
    quotation: str
    decision: str


SPECS = (
    RelationSpec("户部", "衣粮案", 1041, 1046, "三司户部诸案", "135",
                 "户部所领吏人办事机构。大中祥符七年以后定为五案：两税案、曲案，由一员判官通领；上供案，判官一员掌领；修造案、衣粮案，判官一员掌领（《分纪》卷13《三司》）。",
                 "原文明载大中祥符七年以后衣粮案为户部所领五案之一。"),
    RelationSpec("崇文院", "三馆", 1617, 1596, "三馆", "159",
                 "昭文馆、史馆、集贤院凡三馆，并隶崇文院。",
                 "原文明载宋前期三馆并隶崇文院；以天禧元年三馆时间点表达1080年前已生效的关系。"),
    RelationSpec("门下省", "编修院", 1830, 3680, "编修院", "280",
                 "修史机构名。隶门下省。",
                 "原文明载编修院隶门下省，且编修院自天圣九年至元丰四年存在。"),
    RelationSpec("群牧司", "左骐骥院", 1286, 5657, "左、右骐骥院", "342",
                 "官司名。咸平三年后隶群牧司。元丰改制后隶太仆寺。",
                 "原文明载咸平三年后左、右骐骥院隶群牧司；1080年尚在元丰改制前。"),
    RelationSpec("群牧司", "右骐骥院", 1286, 5658, "左、右骐骥院", "342",
                 "官司名。咸平三年后隶群牧司。元丰改制后隶太仆寺。",
                 "原文明载咸平三年后左、右骐骥院隶群牧司；1080年尚在元丰改制前。"),
    RelationSpec("仪鸾司", "仪鸾司北营", 5412, 5433, "仪鸾司营", "335",
                 "仪鸾司所属供杂役的禁兵与工匠营，有南营、北营之分，设都虞候总管。",
                 "原文明载北营为仪鸾司所属营。"),
    RelationSpec("仪鸾司", "仪鸾司南营", 5412, 5435, "仪鸾司营", "335",
                 "仪鸾司所属供杂役的禁兵与工匠营，有南营、北营之分，设都虞候总管。",
                 "原文明载南营为仪鸾司所属营。"),
    RelationSpec("左、右骐骥院", "左天驷监", 5681, 5679, "左、右天驷监", "342",
                 "监当局名。初隶天厩院，后隶骐骥院。",
                 "原文明载天驷监后隶骐骥院；左天驷监为熙宁三年合并后实例。"),
    RelationSpec("左、右骐骥院", "右天驷监", 5681, 5680, "左、右天驷监", "342",
                 "监当局名。初隶天厩院，后隶骐骥院。",
                 "原文明载天驷监后隶骐骥院；右天驷监为熙宁三年合并后实例。"),
    RelationSpec("左、右骐骥院", "左天厩坊", 5655, 5684, "左右天厩坊", "343",
                 "监当局名。隶左、右骐骥院。",
                 "原文明载左天厩坊所属统称隶左、右骐骥院。"),
    RelationSpec("左、右骐骥院", "右天厩坊", 5655, 5685, "左右天厩坊", "343",
                 "监当局名。隶左、右骐骥院。",
                 "原文明载右天厩坊所属统称隶左、右骐骥院。"),
    RelationSpec("群牧司", "牧养上监", 1286, 5695, "牧养上、下监", "343",
                 "监当局名。初隶群牧司，后隶卫尉寺。",
                 "原文明载牧养上监初隶群牧司；1080年尚在元丰改制前。"),
    RelationSpec("群牧司", "牧养下监", 1286, 5696, "牧养上、下监", "343",
                 "监当局名。初隶群牧司，后隶卫尉寺。",
                 "原文明载牧养下监初隶群牧司；1080年尚在元丰改制前。"),
    RelationSpec("三司", "东水碾磨务", 788, 6240, "水碾磨务", "361",
                 "监当局名。先后隶三司、司农寺。",
                 "原文明载东水碾磨务所属统称先隶三司；1080年尚在元丰改制前。"),
    RelationSpec("三司", "西水碾磨务", 788, 6241, "水碾磨务", "361",
                 "监当局名。先后隶三司、司农寺。",
                 "原文明载西水碾磨务所属统称先隶三司；1080年尚在元丰改制前。"),
    RelationSpec("三司", "大通门水磨务", 788, 6242, "水碾磨务", "361",
                 "监当局名。先后隶三司、司农寺。",
                 "原文明载大通门水磨务所属统称先隶三司；1080年尚在元丰改制前。"),
    RelationSpec("户部", "户税案", 1041, 1012, "三司二十四案", "134",
                 "咸平四年（1001），并夏税案、秋税案为户税案",
                 "原文明载户税案由户部原领夏税案、秋税案合并而成；大中祥符七年以后仍属户部五案。"),
    RelationSpec("中书门下", "都检正厅", 159, 3980, "都检正厅", "191",
                 "官衙名。设于都堂内。为中书检正五房公事治所。",
                 "原文明载都检正厅为北宋前期中书检正五房公事治所；中书即中书门下。"),
    RelationSpec("中书门下", "检正厅", 159, 3981, "检正厅", "191",
                 "中书检正逐房（吏、户、礼、刑、孔目房）公事厅，为各房检正公事之治所。",
                 "原文明载检正厅为北宋前期中书逐房检正公事治所；中书即中书门下。"),
    RelationSpec("宗正寺", "陵台令司", 4812, 4880, "陵台令司", "317",
                 "陵台令 职事官名。隶宗正寺。",
                 "原文明载陵台令隶宗正寺；以景德年间双方时间点表达1080年前已生效的关系。"),
    RelationSpec("鸿胪寺", "左街僧录司", 4002, 6008, "左、右街僧录司", "352",
                 "官司名。隶鸿胪寺。",
                 "原文明载左街僧录司为隶鸿胪寺的两街僧录司实例。"),
    RelationSpec("鸿胪寺", "右街僧录司", 4002, 6009, "左、右街僧录司", "352",
                 "官司名。隶鸿胪寺。",
                 "原文明载右街僧录司为隶鸿胪寺的两街僧录司实例。"),
    RelationSpec("都大提点军器库所", "内弓箭南库", 5338, 5300, "都大提点军器库所", "333",
                 "官司名。为都大提点军器官治所。监领军器库逐库事务。位次于都大提举军器库所。",
                 "原文明载都大提点军器库所监领军器库逐库事务；内弓箭南库为当时军器库。"),
    RelationSpec("都大提点军器库所", "内弓箭外库", 5338, 5303, "都大提点军器库所", "333",
                 "官司名。为都大提点军器官治所。监领军器库逐库事务。位次于都大提举军器库所。",
                 "原文明载都大提点军器库所监领军器库逐库事务；内弓箭外库为当时军器库。"),
    RelationSpec("都大提点军器库所", "内弓箭内库", 5338, 5305, "都大提点军器库所", "333",
                 "官司名。为都大提点军器官治所。监领军器库逐库事务。位次于都大提举军器库所。",
                 "原文明载都大提点军器库所监领军器库逐库事务；内弓箭内库为当时军器库。"),
    RelationSpec("都大提点军器库所", "军器弩剑箭库", 5338, 5328, "都大提点军器库所", "333",
                 "官司名。为都大提点军器官治所。监领军器库逐库事务。位次于都大提举军器库所。",
                 "原文明载都大提点军器库所监领军器库逐库事务；军器弩剑箭库为当时军器库。"),
    RelationSpec("都大提点军器库所", "拣选衣甲器械库", 5338, 5330, "都大提点军器库所", "333",
                 "官司名。为都大提点军器官治所。监领军器库逐库事务。位次于都大提举军器库所。",
                 "原文明载都大提点军器库所监领军器库逐库事务；拣选衣甲器械库为当时军器库。"),
    RelationSpec("尚书省", "尚书吏部", 2199, 313, "吏部流内铨", "103",
                 "诏吏部流内选，自今称尚书省吏部。",
                 "原文明载元丰三年吏部流内铨改称尚书省吏部；据全称补建尚书省到尚书吏部的关系。"),
    RelationSpec("提点在京仓草场所", "折博仓", 6224, 6237, "司农寺仓", "361",
                 "宋前期隶提点在京仓场所，元丰改制后隶司农寺。共有二十五仓。诸如船仓、税仓、折中仓、富国仓、万盈仓、广衍仓等等。",
                 "原文明载京师二十五仓宋前期隶提点在京仓场所；折中仓淳化二年改名折博仓，1080年沿用改名后的实体。"),
)


def entity_for_timepoint(connection: sqlite3.Connection, timepoint_id: int) -> tuple[int, str]:
    row = connection.execute(
        "SELECT e.id, e.title FROM Timepoints t JOIN Entities e ON e.id=t.entity_id WHERE t.id=?",
        (timepoint_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"时间点不存在：{timepoint_id}")
    return int(row[0]), str(row[1])


def find_relation(connection: sqlite3.Connection, parent_id: int, child_id: int) -> int | None:
    row = connection.execute(
        """
        SELECT r.id
        FROM Relationships r
        JOIN Timepoints s ON s.id=r.subject_id
        JOIN Timepoints o ON o.id=r.object_id
        WHERE r.relation_type='上下级机构' AND s.entity_id=? AND o.entity_id=?
        ORDER BY r.id DESC LIMIT 1
        """,
        (parent_id, child_id),
    ).fetchone()
    return int(row[0]) if row else None


def validate_quotations(dictionary_path: Path) -> None:
    dictionary = sqlite3.connect(dictionary_path)
    try:
        for spec in SPECS:
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


def apply_repairs(db_path: Path, dictionary_path: Path = DEFAULT_DICTIONARY) -> tuple[int, int]:
    validate_quotations(dictionary_path)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON")
    inserted = 0
    reused = 0
    try:
        connection.execute("BEGIN IMMEDIATE")
        for spec in SPECS:
            parent_id, parent_title = entity_for_timepoint(connection, spec.subject_timepoint_id)
            child_id, child_title = entity_for_timepoint(connection, spec.object_timepoint_id)
            if parent_title != spec.parent or child_title != spec.child:
                raise ValueError(
                    f"时间点实体不符：{spec.subject_timepoint_id}={parent_title}, "
                    f"{spec.object_timepoint_id}={child_title}"
                )
            relation_id = find_relation(connection, parent_id, child_id)
            if relation_id is not None:
                reused += 1
                continue

            cursor = connection.execute(
                """
                INSERT INTO Relationships(subject_id,object_id,relation_type,staff_quota,staff_type,quotation)
                VALUES (?,?,'上下级机构',NULL,NULL,?)
                """,
                (spec.subject_timepoint_id, spec.object_timepoint_id, spec.quotation),
            )
            relation_id = int(cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)
                VALUES ('Relationships',?,?,?,?)
                """,
                (relation_id, spec.source_entry, spec.source_page, spec.decision),
            )
            citation = f"《宋代官制辞典》第{spec.source_page}页“{spec.source_entry}”条"
            citation_cursor = connection.execute(
                """
                INSERT INTO Citations(target_table,target_id,citation,quotation,note,conflict_flag)
                VALUES ('Relationships',?,?,?,?,0)
                """,
                (relation_id, citation, spec.quotation, spec.decision),
            )
            citation_id = int(citation_cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)
                VALUES ('Citations',?,?,?,'为新建上下级机构关系保存同条辞典证据。')
                """,
                (citation_id, spec.source_entry, spec.source_page),
            )
            inserted += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return inserted, reused


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    args = parser.parse_args()
    inserted, reused = apply_repairs(args.db.resolve(), args.dictionary.resolve())
    print(f"inserted={inserted} reused={reused} db={args.db.resolve()}")


if __name__ == "__main__":
    main()
