#!/usr/bin/env python3
"""Merge the current ch1t7 and best ch8t10 dictionary/result databases.

The two source databases are opened read-only. Outputs are assembled in
temporary files, validated, and only then atomically moved into place.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vis.backend.normalize_times import normalize_time, write_normalized_times


DEFAULT_DICTIONARY_1T7 = ROOT / "data/database/song_bureaucracy_dictionary_ch1t7.db"
DEFAULT_DICTIONARY_8T10 = ROOT / "data/database/song_bureaucracy_dictionary.db"
DEFAULT_RESULT_1T7 = ROOT / "data/database/song_bureaucracy_entries_ch1t7.db"
DEFAULT_RESULT_8T10 = (
    ROOT
    / "agent-v0612/records/v0620-regen-test/"
    / "song_bureaucracy_entries_v0620-regen-test.db"
)
DEFAULT_DICTIONARY_OUTPUT = ROOT / "data/database/song_bureaucracy_dictionary_ch1t10.db"
DEFAULT_RESULT_OUTPUT = ROOT / "data/database/song_bureaucracy_entries_ch1t10.db"

CORE_TABLES = ("Entities", "Timepoints", "Relationships", "Citations")


def ro_connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def backup_database(source: Path, output: Path) -> None:
    source_conn = ro_connect(source)
    output_conn = sqlite3.connect(output)
    try:
        source_conn.backup(output_conn)
    finally:
        output_conn.close()
        source_conn.close()


def create_dictionary(source_1t7: Path, source_8t10: Path, output: Path) -> dict[str, int]:
    conn = sqlite3.connect(output)
    one = ro_connect(source_1t7)
    eight = ro_connect(source_8t10)
    try:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE chapter1t10 (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                catalog TEXT NOT NULL,
                page TEXT NOT NULL,
                text TEXT NOT NULL,
                fields TEXT
            );
            CREATE TABLE DictionarySources (
                combined_id INTEGER PRIMARY KEY,
                source_group TEXT NOT NULL,
                source_id INTEGER NOT NULL,
                UNIQUE(source_group, source_id),
                FOREIGN KEY(combined_id) REFERENCES chapter1t10(id)
            );
            CREATE INDEX idx_chapter1t10_title_page ON chapter1t10(title, page);
            CREATE INDEX idx_dictionary_sources_group_id
                ON DictionarySources(source_group, source_id);
            """
        )
        rows_1t7 = one.execute(
            "SELECT id,title,catalog,page,text,fields FROM chapter1t7 ORDER BY id"
        ).fetchall()
        conn.executemany(
            "INSERT INTO chapter1t10 VALUES (?,?,?,?,?,?)",
            [tuple(row) for row in rows_1t7],
        )
        source_rows = one.execute(
            """
            SELECT ds.combined_id,ds.source_group,ds.source_id
            FROM DictionarySources ds
            JOIN chapter1t7 d ON d.id=ds.combined_id
            ORDER BY ds.combined_id
            """
        ).fetchall()
        source_mapping_total = one.execute(
            "SELECT COUNT(*) FROM DictionarySources"
        ).fetchone()[0]
        conn.executemany(
            "INSERT INTO DictionarySources VALUES (?,?,?)",
            [tuple(row) for row in source_rows],
        )

        offset = one.execute("SELECT MAX(id) FROM chapter1t7").fetchone()[0]
        rows_8t10 = eight.execute(
            "SELECT id,title,catalog,page,text,fields FROM chapter8t10 ORDER BY id"
        ).fetchall()
        conn.executemany(
            "INSERT INTO chapter1t10 VALUES (?,?,?,?,?,?)",
            [(offset + row["id"], *tuple(row)[1:]) for row in rows_8t10],
        )
        conn.executemany(
            "INSERT INTO DictionarySources VALUES (?,?,?)",
            [(offset + row["id"], "8t10", row["id"]) for row in rows_8t10],
        )
        conn.commit()
        return {
            "ch1t7_rows": len(rows_1t7),
            "ch8t10_rows": len(rows_8t10),
            "output_rows": len(rows_1t7) + len(rows_8t10),
            "ch8t10_offset": offset,
            "dropped_orphan_source_mappings_ch1t7": source_mapping_total - len(source_rows),
        }
    finally:
        conn.close()
        one.close()
        eight.close()


def create_audit_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS MergeSources;
        CREATE TABLE MergeSources (
            target_table TEXT NOT NULL,
            source_group TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            merged_id INTEGER,
            action TEXT NOT NULL,
            PRIMARY KEY(target_table, source_group, source_id)
        );
        CREATE INDEX idx_merge_sources_target
            ON MergeSources(target_table, merged_id);
        """
    )


def add_audit(
    conn: sqlite3.Connection,
    table: str,
    group: str,
    source_id: int,
    merged_id: int | None,
    action: str,
) -> None:
    conn.execute(
        "INSERT INTO MergeSources VALUES (?,?,?,?,?)",
        (table, group, source_id, merged_id, action),
    )


def target_exists(conn: sqlite3.Connection, table: str, target_id: int) -> bool:
    if table not in CORE_TABLES:
        return False
    return conn.execute(
        f"SELECT 1 FROM {table} WHERE id=?", (target_id,)
    ).fetchone() is not None


def seed_base_audit_and_drop_orphan_buildrecords(
    conn: sqlite3.Connection,
) -> tuple[dict[str, dict[int, int]], int]:
    for table in CORE_TABLES:
        for (row_id,) in conn.execute(f"SELECT id FROM {table} ORDER BY id"):
            add_audit(conn, table, "ch1t7", row_id, row_id, "base")

    dropped = 0
    for row in conn.execute(
        "SELECT id,target_table,target_id FROM BuildRecords ORDER BY id"
    ).fetchall():
        if target_exists(conn, row["target_table"], row["target_id"]):
            add_audit(conn, "BuildRecords", "ch1t7", row["id"], row["id"], "base")
        else:
            add_audit(
                conn, "BuildRecords", "ch1t7", row["id"], None, "dropped_orphan"
            )
            conn.execute("DELETE FROM BuildRecords WHERE id=?", (row["id"],))
            dropped += 1
    # Source IDs are local to each database.  Never seed the ch8t10 map with
    # ch1t7 IDs: a deleted source target could otherwise attach to an unrelated
    # base row that happens to use the same integer ID.
    maps: dict[str, dict[int, int]] = {table: {} for table in CORE_TABLES}
    return maps, dropped


def fill_missing(
    conn: sqlite3.Connection,
    table: str,
    target_id: int,
    columns: tuple[str, ...],
    source: sqlite3.Row,
) -> None:
    current = conn.execute(
        f"SELECT {','.join(columns)} FROM {table} WHERE id=?", (target_id,)
    ).fetchone()
    updates = {
        column: source[column]
        for column, value in zip(columns, current)
        if value is None and source[column] is not None
    }
    if updates:
        assignments = ",".join(f"{column}=?" for column in updates)
        conn.execute(
            f"UPDATE {table} SET {assignments} WHERE id=?",
            (*updates.values(), target_id),
        )


def merge_entities(
    conn: sqlite3.Connection, source: sqlite3.Connection, maps: dict[str, dict[int, int]]
) -> set[int]:
    overlapping: set[int] = set()
    for row in source.execute("SELECT * FROM Entities ORDER BY id"):
        matches = conn.execute(
            "SELECT id FROM Entities WHERE title=? AND type IS ? ORDER BY id",
            (row["title"], row["type"]),
        ).fetchall()
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous target entity: {row['title']!r} / {row['type']!r}"
            )
        if matches:
            merged_id = matches[0][0]
            action = "reused"
            overlapping.add(merged_id)
        else:
            cursor = conn.execute(
                "INSERT INTO Entities(title,type,quotation) VALUES (?,?,NULL)",
                (row["title"], row["type"]),
            )
            merged_id = cursor.lastrowid
            action = "inserted"
        maps["Entities"][row["id"]] = merged_id
        add_audit(conn, "Entities", "ch8t10", row["id"], merged_id, action)
    return overlapping


def merge_timepoints(
    conn: sqlite3.Connection,
    source: sqlite3.Connection,
    maps: dict[str, dict[int, int]],
    overlapping: set[int],
) -> tuple[dict[int, list[tuple[int, int]]], int]:
    source_edges: dict[int, list[tuple[int, int]]] = defaultdict(list)
    reused = 0
    original_target_ids = {
        row[0] for row in conn.execute("SELECT id FROM Timepoints").fetchall()
    }
    source_rows = source.execute("SELECT * FROM Timepoints ORDER BY id").fetchall()
    for row in source_rows:
        entity_id = maps["Entities"][row["entity_id"]]
        matches = []
        if entity_id in overlapping:
            matches = conn.execute(
                "SELECT id FROM Timepoints WHERE entity_id=? AND time IS ? ORDER BY id",
                (entity_id, row["time"]),
            ).fetchall()
            matches = [item for item in matches if item[0] in original_target_ids]
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous timepoint on entity {entity_id}: {row['time']!r}"
            )
        if matches:
            merged_id = matches[0][0]
            action = "reused"
            reused += 1
            fill_missing(
                conn,
                "Timepoints",
                merged_id,
                ("event", "attr_category", "attr_officer_type", "attr_grade"),
                row,
            )
        else:
            cursor = conn.execute(
                """
                INSERT INTO Timepoints(
                    entity_id,time,event,prev_id,succ_id,
                    attr_category,attr_officer_type,attr_grade,quotation
                ) VALUES (?,?,?,NULL,NULL,?,?,?,NULL)
                """,
                (
                    entity_id,
                    row["time"],
                    row["event"],
                    row["attr_category"],
                    row["attr_officer_type"],
                    row["attr_grade"],
                ),
            )
            merged_id = cursor.lastrowid
            action = "inserted"
        maps["Timepoints"][row["id"]] = merged_id
        add_audit(conn, "Timepoints", "ch8t10", row["id"], merged_id, action)

    for row in source_rows:
        entity_id = maps["Entities"][row["entity_id"]]
        current = maps["Timepoints"][row["id"]]
        if row["succ_id"] is not None:
            successor = maps["Timepoints"][row["succ_id"]]
            if current != successor:
                source_edges[entity_id].append((current, successor))
        if entity_id not in overlapping:
            conn.execute(
                "UPDATE Timepoints SET prev_id=?,succ_id=? WHERE id=?",
                (
                    maps["Timepoints"].get(row["prev_id"]),
                    maps["Timepoints"].get(row["succ_id"]),
                    current,
                ),
            )
    return source_edges, reused


def merge_relationships(
    conn: sqlite3.Connection, source: sqlite3.Connection, maps: dict[str, dict[int, int]]
) -> int:
    reused = 0
    for row in source.execute("SELECT * FROM Relationships ORDER BY id"):
        subject_id = maps["Timepoints"][row["subject_id"]]
        object_id = maps["Timepoints"][row["object_id"]]
        matches = conn.execute(
            """
            SELECT id FROM Relationships
            WHERE subject_id=? AND object_id=? AND relation_type IS ?
            ORDER BY id
            """,
            (subject_id, object_id, row["relation_type"]),
        ).fetchall()
        if matches:
            merged_id = matches[0][0]
            action = "reused"
            reused += 1
            fill_missing(
                conn,
                "Relationships",
                merged_id,
                ("staff_quota", "staff_type"),
                row,
            )
        else:
            cursor = conn.execute(
                """
                INSERT INTO Relationships(
                    subject_id,object_id,relation_type,staff_quota,staff_type,quotation
                ) VALUES (?,?,?,?,?,NULL)
                """,
                (
                    subject_id,
                    object_id,
                    row["relation_type"],
                    row["staff_quota"],
                    row["staff_type"],
                ),
            )
            merged_id = cursor.lastrowid
            action = "inserted"
        maps["Relationships"][row["id"]] = merged_id
        add_audit(conn, "Relationships", "ch8t10", row["id"], merged_id, action)
    return reused


def merge_citations(
    conn: sqlite3.Connection, source: sqlite3.Connection, maps: dict[str, dict[int, int]]
) -> int:
    reused = 0
    for row in source.execute("SELECT * FROM Citations ORDER BY id"):
        table = row["target_table"]
        if table not in maps or row["target_id"] not in maps[table]:
            raise ValueError(
                f"Citation {row['id']} has unmappable target {table}:{row['target_id']}"
            )
        target_id = maps[table][row["target_id"]]
        matches = conn.execute(
            """
            SELECT id FROM Citations
            WHERE target_table=? AND target_id=?
              AND citation IS ? AND quotation IS ?
            ORDER BY id
            """,
            (table, target_id, row["citation"], row["quotation"]),
        ).fetchall()
        if matches:
            merged_id = matches[0][0]
            action = "reused"
            reused += 1
        else:
            cursor = conn.execute(
                """
                INSERT INTO Citations(
                    target_table,target_id,citation,quotation,note,conflict_flag
                ) VALUES (?,?,?,?,?,?)
                """,
                (
                    table,
                    target_id,
                    row["citation"],
                    row["quotation"],
                    row["note"],
                    row["conflict_flag"],
                ),
            )
            merged_id = cursor.lastrowid
            action = "inserted"
        maps["Citations"][row["id"]] = merged_id
        add_audit(conn, "Citations", "ch8t10", row["id"], merged_id, action)
    return reused


def merge_buildrecords(
    conn: sqlite3.Connection, source: sqlite3.Connection, maps: dict[str, dict[int, int]]
) -> tuple[int, int]:
    inserted = 0
    dropped = 0
    for row in source.execute("SELECT * FROM BuildRecords ORDER BY id"):
        table = row["target_table"]
        if table not in maps or row["target_id"] not in maps[table]:
            add_audit(
                conn, "BuildRecords", "ch8t10", row["id"], None, "dropped_orphan"
            )
            dropped += 1
            continue
        cursor = conn.execute(
            """
            INSERT INTO BuildRecords(
                target_table,target_id,source_entry,source_page,decision,created_at
            ) VALUES (?,?,?,?,?,?)
            """,
            (
                table,
                maps[table][row["target_id"]],
                row["source_entry"],
                row["source_page"],
                row["decision"],
                row["created_at"],
            ),
        )
        add_audit(
            conn, "BuildRecords", "ch8t10", row["id"], cursor.lastrowid, "inserted"
        )
        inserted += 1
    return inserted, dropped


def chronological_key(conn: sqlite3.Connection, timepoint_id: int) -> tuple[Any, ...]:
    row = conn.execute(
        "SELECT time FROM Timepoints WHERE id=?", (timepoint_id,)
    ).fetchone()
    normalized = normalize_time(row[0] or "")
    missing = normalized.sort_order is None
    return (missing, normalized.sort_order or 0, timepoint_id)


def rebuild_overlap_chains(
    conn: sqlite3.Connection,
    overlapping: set[int],
    source_edges: dict[int, list[tuple[int, int]]],
) -> None:
    for entity_id in sorted(overlapping):
        nodes = [
            row[0]
            for row in conn.execute(
                "SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id", (entity_id,)
            )
        ]
        node_set = set(nodes)
        edges: set[tuple[int, int]] = set(source_edges.get(entity_id, []))
        for row in conn.execute(
            "SELECT id,succ_id FROM Timepoints WHERE entity_id=?", (entity_id,)
        ):
            if row[1] is not None and row[1] in node_set and row[0] != row[1]:
                edges.add((row[0], row[1]))

        outgoing: dict[int, set[int]] = {node: set() for node in nodes}
        indegree = {node: 0 for node in nodes}
        for left, right in edges:
            if left not in node_set or right not in node_set:
                raise ValueError(f"Cross-entity chain constraint on entity {entity_id}")
            if right not in outgoing[left]:
                outgoing[left].add(right)
                indegree[right] += 1

        ready = sorted(
            (node for node in nodes if indegree[node] == 0),
            key=lambda node: chronological_key(conn, node),
        )
        ordered: list[int] = []
        while ready:
            node = ready.pop(0)
            ordered.append(node)
            for successor in sorted(outgoing[node]):
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    ready.append(successor)
                    ready.sort(key=lambda item: chronological_key(conn, item))
        if len(ordered) != len(nodes):
            raise ValueError(f"Conflicting timepoint chains on entity {entity_id}")

        for index, node in enumerate(ordered):
            conn.execute(
                "UPDATE Timepoints SET prev_id=?,succ_id=? WHERE id=?",
                (
                    ordered[index - 1] if index else None,
                    ordered[index + 1] if index + 1 < len(ordered) else None,
                    node,
                ),
            )


def merge_results(source_1t7: Path, source_8t10: Path, output: Path) -> dict[str, Any]:
    backup_database(source_1t7, output)
    conn = sqlite3.connect(output)
    conn.row_factory = sqlite3.Row
    source = ro_connect(source_8t10)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE")
        create_audit_table(conn)
        maps, dropped_base = seed_base_audit_and_drop_orphan_buildrecords(conn)
        overlapping = merge_entities(conn, source, maps)
        source_edges, reused_timepoints = merge_timepoints(
            conn, source, maps, overlapping
        )
        reused_relationships = merge_relationships(conn, source, maps)
        reused_citations = merge_citations(conn, source, maps)
        inserted_buildrecords, dropped_source = merge_buildrecords(conn, source, maps)
        rebuild_overlap_chains(conn, overlapping, source_edges)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        source.close()

    normalization_counts = write_normalized_times(output, output)
    return {
        "overlapping_entities": len(overlapping),
        "reused_timepoints": reused_timepoints,
        "reused_relationships": reused_relationships,
        "reused_citations": reused_citations,
        "inserted_ch8t10_buildrecords": inserted_buildrecords,
        "dropped_orphan_buildrecords_ch1t7": dropped_base,
        "dropped_orphan_buildrecords_ch8t10": dropped_source,
        "normalization": normalization_counts,
    }


def validate_dictionary(path: Path) -> dict[str, int]:
    conn = sqlite3.connect(path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"Dictionary integrity check failed: {integrity}")
        count = conn.execute("SELECT COUNT(*) FROM chapter1t10").fetchone()[0]
        mappings = conn.execute("SELECT COUNT(*) FROM DictionarySources").fetchone()[0]
        if count != 4647 or mappings != count:
            raise ValueError(f"Unexpected dictionary counts: rows={count}, mappings={mappings}")
        return {"rows": count, "source_mappings": mappings}
    finally:
        conn.close()


def disconnected_chain_entities(conn: sqlite3.Connection) -> list[int]:
    entity_rows: dict[int, list[tuple[int, int | None, int | None]]] = defaultdict(list)
    for row in conn.execute(
        "SELECT entity_id,id,prev_id,succ_id FROM Timepoints ORDER BY entity_id,id"
    ):
        entity_rows[row[0]].append((row[1], row[2], row[3]))
    bad: list[int] = []
    for entity_id, rows in entity_rows.items():
        heads = [row_id for row_id, prev_id, _ in rows if prev_id is None]
        if len(heads) != 1:
            bad.append(entity_id)
            continue
        successors = {row_id: succ_id for row_id, _, succ_id in rows}
        visited: set[int] = set()
        current: int | None = heads[0]
        while current is not None and current not in visited:
            visited.add(current)
            current = successors.get(current)
        if len(visited) != len(rows) or current is not None:
            bad.append(entity_id)
    return bad


def source_disconnected_count(path: Path) -> int:
    conn = ro_connect(path)
    try:
        return len(disconnected_chain_entities(conn))
    finally:
        conn.close()


def validate_results(path: Path, inherited_disconnected: int) -> dict[str, Any]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or foreign_keys:
            raise ValueError(
                f"Result DB structural check failed: integrity={integrity}, fk={len(foreign_keys)}"
            )

        orphan_timepoints = conn.execute(
            """SELECT COUNT(*) FROM Timepoints t
               WHERE NOT EXISTS(SELECT 1 FROM Entities e WHERE e.id=t.entity_id)"""
        ).fetchone()[0]
        orphan_relationships = conn.execute(
            """SELECT COUNT(*) FROM Relationships r
               WHERE NOT EXISTS(SELECT 1 FROM Timepoints t WHERE t.id=r.subject_id)
                  OR NOT EXISTS(SELECT 1 FROM Timepoints t WHERE t.id=r.object_id)"""
        ).fetchone()[0]
        orphan_citations = conn.execute(
            """
            SELECT COUNT(*) FROM Citations c WHERE
              (target_table='Entities' AND NOT EXISTS(SELECT 1 FROM Entities x WHERE x.id=c.target_id)) OR
              (target_table='Timepoints' AND NOT EXISTS(SELECT 1 FROM Timepoints x WHERE x.id=c.target_id)) OR
              (target_table='Relationships' AND NOT EXISTS(SELECT 1 FROM Relationships x WHERE x.id=c.target_id)) OR
              target_table NOT IN ('Entities','Timepoints','Relationships')
            """
        ).fetchone()[0]
        orphan_buildrecords = conn.execute(
            """
            SELECT COUNT(*) FROM BuildRecords b WHERE
              (target_table='Entities' AND NOT EXISTS(SELECT 1 FROM Entities x WHERE x.id=b.target_id)) OR
              (target_table='Timepoints' AND NOT EXISTS(SELECT 1 FROM Timepoints x WHERE x.id=b.target_id)) OR
              (target_table='Relationships' AND NOT EXISTS(SELECT 1 FROM Relationships x WHERE x.id=b.target_id)) OR
              (target_table='Citations' AND NOT EXISTS(SELECT 1 FROM Citations x WHERE x.id=b.target_id))
            """
        ).fetchone()[0]
        normalization_missing = conn.execute(
            """SELECT COUNT(*) FROM Timepoints t
               WHERE NOT EXISTS(SELECT 1 FROM NormalizedTimes n WHERE n.timepoint_id=t.id)"""
        ).fetchone()[0]
        bad_chains = conn.execute(
            """
            SELECT COUNT(*) FROM Timepoints t WHERE
              (t.prev_id IS NOT NULL AND NOT EXISTS(
                SELECT 1 FROM Timepoints p
                WHERE p.id=t.prev_id AND p.entity_id=t.entity_id AND p.succ_id=t.id
              )) OR
              (t.succ_id IS NOT NULL AND NOT EXISTS(
                SELECT 1 FROM Timepoints s
                WHERE s.id=t.succ_id AND s.entity_id=t.entity_id AND s.prev_id=t.id
              ))
            """
        ).fetchone()[0]
        disconnected = disconnected_chain_entities(conn)
        issues = {
            "orphan_timepoints": orphan_timepoints,
            "orphan_relationships": orphan_relationships,
            "orphan_citations": orphan_citations,
            "orphan_buildrecords": orphan_buildrecords,
            "normalization_missing": normalization_missing,
            "nonreciprocal_or_cross_entity_chains": bad_chains,
        }
        if any(issues.values()):
            raise ValueError(f"Result DB semantic check failed: {issues}")
        if len(disconnected) > inherited_disconnected:
            raise ValueError(
                "Merge introduced disconnected timepoint chains: "
                f"source={inherited_disconnected}, output={len(disconnected)}, "
                f"entities={disconnected[:20]}"
            )

        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (*CORE_TABLES, "BuildRecords", "NormalizedTimes", "MergeSources")
        }
        actions = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT action,COUNT(*) FROM MergeSources GROUP BY action ORDER BY action"
            )
        }
        return {
            "counts": counts,
            "issues": issues,
            "merge_actions": actions,
            "inherited_disconnected_chain_entities": disconnected,
        }
    finally:
        conn.close()


def replace_atomically(temp: Path, target: Path, overwrite: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Output already exists; pass --overwrite: {target}")
    os.replace(temp, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dictionary-1t7", type=Path, default=DEFAULT_DICTIONARY_1T7)
    parser.add_argument("--dictionary-8t10", type=Path, default=DEFAULT_DICTIONARY_8T10)
    parser.add_argument("--result-1t7", type=Path, default=DEFAULT_RESULT_1T7)
    parser.add_argument("--result-8t10", type=Path, default=DEFAULT_RESULT_8T10)
    parser.add_argument("--dictionary-output", type=Path, default=DEFAULT_DICTIONARY_OUTPUT)
    parser.add_argument("--result-output", type=Path, default=DEFAULT_RESULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path in (
        args.dictionary_1t7,
        args.dictionary_8t10,
        args.result_1t7,
        args.result_8t10,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    temp_dir = Path(tempfile.mkdtemp(prefix="song-bureaucracy-merge-"))
    temp_dictionary = temp_dir / args.dictionary_output.name
    temp_result = temp_dir / args.result_output.name
    try:
        inherited_disconnected = source_disconnected_count(args.result_1t7)
        dictionary_report = create_dictionary(
            args.dictionary_1t7, args.dictionary_8t10, temp_dictionary
        )
        result_report = merge_results(args.result_1t7, args.result_8t10, temp_result)
        validation = {
            "dictionary": validate_dictionary(temp_dictionary),
            "result": validate_results(temp_result, inherited_disconnected),
        }
        replace_atomically(temp_dictionary, args.dictionary_output, args.overwrite)
        replace_atomically(temp_result, args.result_output, args.overwrite)
        print(
            json.dumps(
                {
                    "dictionary_merge": dictionary_report,
                    "result_merge": result_report,
                    "validation": validation,
                    "outputs": {
                        "dictionary": str(args.dictionary_output),
                        "result": str(args.result_output),
                    },
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        for path in temp_dir.glob("*"):
            path.unlink(missing_ok=True)
        temp_dir.rmdir()


if __name__ == "__main__":
    main()
