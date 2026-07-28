#!/usr/bin/env python3
"""Export the visualization working database to a compact browser JSON file."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

try:
    from .normalize_times import ERA_YEARS, NORMALIZATION_VERSION, normalize_time
except ImportError:  # 直接执行 python3 vis/backend/export_visualization_data.py
    from normalize_times import ERA_YEARS, NORMALIZATION_VERSION, normalize_time


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "vis/data/song_bureaucracy_visualization.db"
DEFAULT_OUTPUT = ROOT / "vis/song-bureaucracy-visualization-v2/public/data/song-bureaucracy.json"


def classify_event(event: str) -> str:
    if any(word in event for word in ("复置", "恢复", "复称", "复旧")):
        return "restored"
    if any(word in event for word in ("罢", "废", "解散", "撤销")):
        return "abolished"
    if any(word in event for word in ("改名", "改称", "易名", "更名")):
        return "renamed"
    if any(word in event for word in ("并入", "合并", "并归")):
        return "merged"
    if any(word in event for word in ("始置", "设置", "设立", "初置", "置司", "创置")):
        return "established"
    return "recorded"


def phase_for_era(start: int) -> str:
    return "北宋" if start < 1127 else "南宋"


def endpoint_period(event: dict | None) -> dict | None:
    """单个时间点自身的纪年段，作为关系的一条离散依据。无纪年时返回 None。"""
    if (
        not event
        or event["timeType"] not in {"exact", "range"}
        or event["yearStart"] is None
    ):
        return None
    return {
        "start": event["yearStart"],
        "end": event["yearEnd"] if event["yearEnd"] is not None else event["yearStart"],
    }


def _has_table(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def build_payload(db_path: Path) -> dict:
    """从 SQLite 构建前端数据；数据库全程只读。

    NormalizedTimes 缺失，或其 raw_time 与最新 Timepoints.time 不一致时，
    直接用最新中文时间重新标准化。这样修改、增加时间点后无需先重建工作库。
    """
    conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        citation_map: dict[tuple[str, int], list[dict]] = defaultdict(list)
        for row in conn.execute(
            "SELECT target_table, target_id, citation, quotation, note, conflict_flag FROM Citations ORDER BY id"
        ):
            citation_map[(row["target_table"], row["target_id"])].append({
                "citation": row["citation"],
                "quotation": row["quotation"],
                "note": row["note"],
                "conflict": bool(row["conflict_flag"]),
            })

        has_normalized_times = _has_table(conn, "NormalizedTimes")
        normalization_is_current = False
        if has_normalized_times and _has_table(conn, "TimeNormalizationMetadata"):
            row = conn.execute(
                "SELECT value FROM TimeNormalizationMetadata WHERE key = 'normalization_version'"
            ).fetchone()
            normalization_is_current = bool(row and row[0] == NORMALIZATION_VERSION)
        if has_normalized_times:
            normalized_columns = """
                n.timepoint_id AS normalized_timepoint_id,
                n.raw_time AS normalized_raw_time,
                n.year_start, n.year_end, n.month, n.is_leap_month, n.day,
                n.month_text, n.day_text, n.sort_order, n.time_type
            """
            normalized_join = "LEFT JOIN NormalizedTimes n ON n.timepoint_id = t.id"
        else:
            normalized_columns = """
                NULL AS normalized_timepoint_id, NULL AS normalized_raw_time,
                NULL AS year_start, NULL AS year_end, NULL AS month,
                NULL AS is_leap_month, NULL AS day, NULL AS month_text,
                NULL AS day_text, NULL AS sort_order, NULL AS time_type
            """
            normalized_join = ""

        events: list[dict] = []
        event_by_id: dict[int, dict] = {}
        for row in conn.execute(
            f"""
            SELECT
                t.id, t.entity_id, e.title, e.type AS entity_type,
                t.time, t.event, t.attr_category, t.attr_officer_type, t.attr_grade,
                {normalized_columns}
            FROM Timepoints t
            JOIN Entities e ON e.id = t.entity_id
            {normalized_join}
            ORDER BY t.id
            """
        ):
            raw_time = row["time"] or ""
            normalized_is_current = (
                normalization_is_current
                and
                row["normalized_timepoint_id"] is not None
                and row["normalized_raw_time"] == raw_time
            )
            if normalized_is_current:
                normalized = {
                    "year_start": row["year_start"],
                    "year_end": row["year_end"],
                    "month": row["month"],
                    "is_leap_month": row["is_leap_month"],
                    "day": row["day"],
                    "month_text": row["month_text"],
                    "day_text": row["day_text"],
                    "sort_order": row["sort_order"],
                    "time_type": row["time_type"],
                }
            else:
                parsed = normalize_time(raw_time)
                normalized = {
                    "year_start": parsed.year_start,
                    "year_end": parsed.year_end,
                    "month": parsed.month,
                    "is_leap_month": parsed.is_leap_month,
                    "day": parsed.day,
                    "month_text": parsed.month_text,
                    "day_text": parsed.day_text,
                    "sort_order": parsed.sort_order,
                    "time_type": parsed.time_type,
                }
            item = {
                "id": row["id"],
                "entityId": row["entity_id"],
                "title": row["title"],
                "entityType": row["entity_type"],
                "rawTime": raw_time,
                "event": row["event"],
                "eventType": classify_event(row["event"] or ""),
                "category": row["attr_category"],
                "officerType": row["attr_officer_type"],
                "grade": row["attr_grade"],
                "yearStart": normalized["year_start"],
                "yearEnd": normalized["year_end"],
                "month": normalized["month"],
                "isLeapMonth": bool(normalized["is_leap_month"]),
                "day": normalized["day"],
                "monthText": normalized["month_text"],
                "dayText": normalized["day_text"],
                "sortOrder": normalized["sort_order"],
                "timeType": normalized["time_type"],
                "citations": citation_map.get(("Timepoints", row["id"]), []),
            }
            events.append(item)
            event_by_id[row["id"]] = item

        events.sort(key=lambda item: (item["sortOrder"] is None, item["sortOrder"] or 0, item["id"]))

        relations: list[dict] = []
        relation_counts: Counter[int] = Counter()
        for row in conn.execute(
            """
            SELECT
                r.id, r.subject_id, r.object_id, r.relation_type,
                r.staff_quota, r.staff_type,
                st.entity_id AS subject_entity_id, ot.entity_id AS object_entity_id,
                se.title AS subject_title, se.type AS subject_type,
                oe.title AS object_title, oe.type AS object_type
            FROM Relationships r
            JOIN Timepoints st ON st.id = r.subject_id
            JOIN Entities se ON se.id = st.entity_id
            JOIN Timepoints ot ON ot.id = r.object_id
            JOIN Entities oe ON oe.id = ot.entity_id
            ORDER BY r.id
            """
        ):
            relation_counts[row["subject_id"]] += 1
            relation_counts[row["object_id"]] += 1
            # 离散依据模型：保留两端时间点各自的纪年段，不做 min/max 合并。
            # 两端相隔很远时合并跨度会编造出没有史料依据的连续期。
            periods = []
            for period in (
                endpoint_period(event_by_id.get(row["subject_id"])),
                endpoint_period(event_by_id.get(row["object_id"])),
            ):
                if period and period not in periods:
                    periods.append(period)
            periods.sort(key=lambda p: (p["start"], p["end"]))
            relations.append({
                "id": row["id"],
                "subjectId": row["subject_id"],
                "objectId": row["object_id"],
                "subjectEntityId": row["subject_entity_id"],
                "objectEntityId": row["object_entity_id"],
                "type": row["relation_type"],
                "staffQuota": row["staff_quota"],
                "staffType": row["staff_type"],
                "subjectTitle": row["subject_title"],
                "subjectType": row["subject_type"],
                "objectTitle": row["object_title"],
                "objectType": row["object_type"],
                "periods": periods,
                "citations": citation_map.get(("Relationships", row["id"]), []),
            })

        for event_id, item in event_by_id.items():
            item["relationCount"] = relation_counts[event_id]

        activity: dict[int, dict] = defaultdict(
            lambda: {"eventCount": 0, "yearMin": None, "yearMax": None}
        )
        for event in events:
            stat = activity[event["entityId"]]
            stat["eventCount"] += 1
            if event["timeType"] == "exact" and event["yearStart"] is not None:
                stat["yearMin"] = event["yearStart"] if stat["yearMin"] is None else min(stat["yearMin"], event["yearStart"])
                stat["yearMax"] = event["yearStart"] if stat["yearMax"] is None else max(stat["yearMax"], event["yearStart"])

        entities: list[dict] = []
        for row in conn.execute("SELECT id, title, type FROM Entities ORDER BY id"):
            entities.append({
                "id": row["id"],
                "title": row["title"],
                "type": row["type"],
                **activity[row["id"]],
            })

        exact_year_counts = Counter(
            event["yearStart"] for event in events
            if event["timeType"] == "exact" and event["yearStart"] is not None
        )
        years = [
            {"year": year, "count": exact_year_counts.get(year, 0)}
            for year in range(960, 1280)
        ]
        eras = [
            {"name": name, "start": bounds[0], "end": bounds[1], "phase": phase_for_era(bounds[0])}
            for name, bounds in ERA_YEARS.items()
        ]

        return {
            "meta": {
                "title": "宋代官制时序图谱",
                "yearStart": 960,
                "yearEnd": 1279,
                "eventCount": len(events),
                "relationCount": len(relations),
                "entityCount": len(entities),
                "boundedCount": sum(event["timeType"] == "bounded" for event in events),
                "undatedCount": sum(event["timeType"] == "undated" for event in events),
                "timeUncertainCount": sum(
                    event["timeType"] in {"bounded", "undated"} for event in events
                ),
            },
            "years": years,
            "eras": eras,
            "entities": entities,
            "events": events,
            "relations": relations,
        }
    finally:
        conn.close()


def export(db_path: Path, output_path: Path) -> None:
    payload = build_payload(db_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"已导出: {output_path}")
    print(
        f"实体: {len(payload['entities'])}, "
        f"事件: {len(payload['events'])}, "
        f"关系: {len(payload['relations'])}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    export(args.db, args.output)


if __name__ == "__main__":
    main()
