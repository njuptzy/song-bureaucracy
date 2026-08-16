#!/usr/bin/env python3
"""校对 ch1t12 第一批高置信 event_type / lifecycle_effect 异常。

本脚本只更新显式列出的 Timepoints，并为实际修改追加 BuildRecords。
每条规则同时核验实体名、时间、事件、原字段和引文片段；可重复执行。
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data/database/song_bureaucracy_entries_ch1t12.db"


@dataclass(frozen=True)
class Repair:
    timepoint_id: int
    title: str
    time: str
    event_fragment: str
    quotation_fragment: str
    old_event_type: str
    old_lifecycle_effect: str
    new_event_type: str
    new_lifecycle_effect: str
    source_entry: str
    source_page: str
    decision: str


REPAIRS = (
    Repair(18, "同中书门下平章事", "北宋元丰五年", "宰相之任终结", "宋初至元丰五年",
           "abolish", "preserve", "abolish", "deactivate", "同中书门下平章事", "85",
           "原文把该宰相名的适用期限定至元丰五年，且事件明确记其宰相之任终结；存废影响校正为停用。"),
    Repair(29, "同中书门下平章事、集贤殿大学士", "北宋元丰三年", "罢集贤殿大学士", "元丰三年罢集贤殿大学士",
           "abolish", "preserve", "abolish", "deactivate", "同中书门下平章事、集贤殿大学士", "86",
           "原文明载罢集贤殿大学士，复合宰相官名据此终止；存废影响校正为停用。"),
    Repair(35, "同中书门下平章事、昭文馆大学士", "北宋熙宁九年", "罢昭文馆大学士", "熙宁九年罢昭文馆大学士",
           "abolish", "preserve", "abolish", "deactivate", "同中书门下平章事、昭文馆大学士", "85",
           "原文明载罢昭文馆大学士，复合宰相官名据此终止；存废影响校正为停用。"),
    Repair(50, "尚书左仆射、同中书门下平章事", "南宋乾道八年二月六日", "改为左丞相", "改为左丞相",
           "record", "deactivate", "rename", "deactivate", "尚书左仆射、同中书门下平章事", "88",
           "原文明载该宰相名改为左丞相，属于更名并停用旧名；事件类型校正为更名。"),
    Repair(51, "尚书右仆射、同中书门下平章事", "南宋乾道八年", "宰相名止", "建炎三年至乾道八年宰相名",
           "abolish", "preserve", "abolish", "deactivate", "尚书右仆射、同中书门下平章事", "88",
           "原文限定该宰相名仅行于建炎三年至乾道八年，事件亦记名止；存废影响校正为停用。"),
    Repair(71, "中书侍郎", "南宋建炎三年四月十三日", "复改为参知政事", "中书侍郎复改为参知政事",
           "record", "deactivate", "rename", "deactivate", "中书侍郎", "187",
           "原文明载中书侍郎复改为参知政事，旧职名在该节点停用；事件类型校正为更名。"),
    Repair(77, "中书侍郎", "唐武德三年", "改为中书省侍郎", "唐武德三年改为中书省侍郎",
           "record", "deactivate", "rename", "deactivate", "中书侍郎", "187",
           "原文明载唐武德三年改为中书省侍郎，属于明确更名；事件类型校正为更名。"),
    Repair(87, "尚书省左丞", "南宋建炎三年四月", "罢尚书左、右丞", "罢尚书左、右丞",
           "abolish", "preserve", "abolish", "deactivate", "尚书省左丞", "197",
           "原文明载建炎三年罢尚书左、右丞；尚书省左丞在该节点停用。"),
    Repair(91, "尚书省右丞", "南宋建炎三年四月", "罢尚书左、右丞", "详参“尚书省左丞”条",
           "abolish", "preserve", "abolish", "deactivate", "尚书省右丞", "198",
           "本条明言沿革与尚书省左丞相同并参见左丞条；左丞条明确建炎三年罢左右丞，故右丞亦在该节点停用。"),
    Repair(112, "太师", "北宋政和二年", "改为三公官", "政和二年（1112）改为三公官",
           "record", "deactivate", "reorganize", "preserve", "太师", "91",
           "原文是太师由三师性质改为三公官，名称并未被罢或改名；校正为制度改组且保持存续。"),
    Repair(126, "太保", "北宋政和二年", "改为三公官", "政和二年(1112)改为三公官",
           "record", "deactivate", "reorganize", "preserve", "太保", "91",
           "原文是太保由三师性质改为三公官，名称并未被罢或改名；校正为制度改组且保持存续。"),
    Repair(142, "司徒", "北宋政和二年九月", "罢太尉、司徒、司空", "罢太尉、司徒、司空三公官之名",
           "abolish", "preserve", "abolish", "deactivate", "司徒", "92",
           "原文明载罢太尉、司徒、司空三公官之名；司徒在该节点停用。"),
    Repair(147, "司空", "北宋政和二年九月", "其后不置司空官名", "其后不置司空官名",
           "abolish", "preserve", "abolish", "deactivate", "司空", "93",
           "原文明载罢司空且其后不置该官名；存废影响校正为停用。"),
    Repair(201, "中书五房习学公事", "北宋元丰官制施行时", "检正、习学之名悉罢", "检正、习学之名，悉已罢去",
           "abolish", "preserve", "abolish", "deactivate", "中书五房习学公事", "98",
           "原文明载元丰官制施行后习学之名悉罢；该官职在此节点停用。"),
    Repair(257, "吏部西铨", "宋立国之初", "仅存官印而事废", "仅存官印而事废",
           "abolish", "preserve", "abolish", "deactivate", "吏部三铨", "100",
           "原文明载西铨仅存官印而事废，已不再作为实际办事机构运行；存废影响校正为停用。"),
    Repair(259, "吏部东铨", "宋立国之初", "仅存官印而事废", "仅存官印而事废",
           "abolish", "preserve", "abolish", "deactivate", "吏部三铨", "100",
           "原文明载东铨仅存官印而事废，已不再作为实际办事机构运行；存废影响校正为停用。"),
    Repair(274, "审官院", "北宋熙宁三年五月二十八日", "改为审官东院", "改审官院为审官东院",
           "record", "deactivate", "rename", "deactivate", "审官院", "101",
           "原文明载审官院改为审官东院，属于更名并停用旧名；事件类型校正为更名。"),
    Repair(300, "审官东院", "北宋元丰五年五月", "改为吏部尚书左选", "改审官东院为吏部尚书左选",
           "record", "deactivate", "rename", "deactivate", "审官东院", "103",
           "原文明载审官东院改为吏部尚书左选，属于更名并停用旧名；事件类型校正为更名。"),
    Repair(304, "审官西院", "北宋元丰五年五月", "改为吏部尚书右选", "改为尚书省吏部尚书右选",
           "record", "deactivate", "rename", "deactivate", "审官西院", "103",
           "原文明载审官西院改为尚书省吏部尚书右选，属于更名并停用旧名；事件类型校正为更名。"),
    Repair(345, "详定仪注所", "北宋大中祥符六年八月十一日", "改为礼仪院", "改为礼仪院",
           "record", "deactivate", "rename", "deactivate", "礼仪院", "105",
           "原文明载详定仪注所改为礼仪院，属于更名并停用旧名；事件类型校正为更名。"),
)


def load_timepoint(connection: sqlite3.Connection, repair: Repair) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT t.id, e.title, t.time, t.event, t.event_type, t.lifecycle_effect
        FROM Timepoints t JOIN Entities e ON e.id=t.entity_id
        WHERE t.id=?
        """,
        (repair.timepoint_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"时间点不存在：{repair.timepoint_id}")
    return row


def assert_evidence(connection: sqlite3.Connection, repair: Repair) -> None:
    found = connection.execute(
        """
        SELECT 1 FROM Citations
        WHERE target_table='Timepoints' AND target_id=? AND quotation LIKE ?
        LIMIT 1
        """,
        (repair.timepoint_id, f"%{repair.quotation_fragment}%"),
    ).fetchone()
    if found is None:
        raise ValueError(
            f"时间点 {repair.timepoint_id} 未找到预期引文片段：{repair.quotation_fragment}"
        )


def apply_repairs(db_path: Path) -> tuple[int, int]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    changed = 0
    reused = 0
    try:
        connection.execute("BEGIN IMMEDIATE")
        for repair in REPAIRS:
            row = load_timepoint(connection, repair)
            actual_identity = (row["title"], row["time"])
            expected_identity = (repair.title, repair.time)
            if actual_identity != expected_identity or repair.event_fragment not in row["event"]:
                raise ValueError(
                    f"时间点 {repair.timepoint_id} 身份漂移："
                    f"{actual_identity!r}, event={row['event']!r}"
                )
            assert_evidence(connection, repair)

            current = (row["event_type"], row["lifecycle_effect"])
            old = (repair.old_event_type, repair.old_lifecycle_effect)
            new = (repair.new_event_type, repair.new_lifecycle_effect)
            if current == new:
                reused += 1
                continue
            if current != old:
                raise ValueError(
                    f"时间点 {repair.timepoint_id} 字段漂移：current={current}, "
                    f"expected_old={old}, expected_new={new}"
                )

            connection.execute(
                "UPDATE Timepoints SET event_type=?, lifecycle_effect=? WHERE id=?",
                (*new, repair.timepoint_id),
            )
            connection.execute(
                """
                INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)
                VALUES ('Timepoints',?,?,?,?)
                """,
                (repair.timepoint_id, repair.source_entry, repair.source_page, repair.decision),
            )
            changed += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return changed, reused


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    changed, reused = apply_repairs(args.db.resolve())
    print(f"changed={changed} reused={reused} db={args.db.resolve()}")


if __name__ == "__main__":
    main()
