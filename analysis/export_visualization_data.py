#!/usr/bin/env python3
"""Export Song Bureaucracy SQLite data for the static D3 dashboard.

The export is intentionally visualization-only. It reads SQLite databases and
materializes raw table records plus lightweight join fields for frontend views.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENTRY_DB = ROOT / "data/database/song_bureaucracy_entries_v0304.db"
DEFAULT_DICT_DB = ROOT / "data/database/song_bureaucracy_dictionary.db"
DEFAULT_OUTPUT_DIR = ROOT / "visualization/data"


def connect(path: Path) -> sqlite3.Connection:
  conn = sqlite3.connect(path)
  conn.row_factory = sqlite3.Row
  return conn


def rows(conn: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
  return [dict(row) for row in conn.execute(sql)]


def short_text(text: str | None, limit: int = 240) -> str:
  text = " ".join((text or "").split())
  return text if len(text) <= limit else f"{text[:limit]}..."


def export(entry_db: Path, dict_db: Path, output_dir: Path) -> None:
  output_dir.mkdir(parents=True, exist_ok=True)

  with connect(entry_db) as entry_conn, connect(dict_db) as dict_conn:
    entities = rows(entry_conn, "SELECT id, title, type FROM Entities ORDER BY id")
    timepoints = rows(entry_conn, "SELECT * FROM Timepoints ORDER BY id")
    relationships = rows(entry_conn, "SELECT * FROM Relationships ORDER BY id")
    citations = rows(entry_conn, "SELECT * FROM Citations ORDER BY id")
    dictionary = rows(
      dict_conn,
      "SELECT id, title, catalog, page, text, fields FROM chapter8t10 ORDER BY id",
    )

  entity_by_id = {entity["id"]: entity for entity in entities}
  timepoint_by_id = {timepoint["id"]: timepoint for timepoint in timepoints}
  timepoints_by_entity: dict[int, list[dict[str, Any]]] = defaultdict(list)
  for timepoint in timepoints:
    timepoints_by_entity[timepoint["entity_id"]].append(timepoint)

  citations_by_timepoint: dict[int, list[dict[str, Any]]] = defaultdict(list)
  citations_by_relationship: dict[int, list[dict[str, Any]]] = defaultdict(list)
  for citation in citations:
    if citation["target_table"] == "Timepoints":
      citations_by_timepoint[citation["target_id"]].append(citation)
    elif citation["target_table"] == "Relationships":
      citations_by_relationship[citation["target_id"]].append(citation)

  relationship_records: list[dict[str, Any]] = []
  dangling_relationships: list[int] = []
  for relationship in relationships:
    subject_tp = timepoint_by_id.get(relationship["subject_id"])
    object_tp = timepoint_by_id.get(relationship["object_id"])
    if subject_tp is None or object_tp is None:
      dangling_relationships.append(relationship["id"])
      continue

    subject_entity = entity_by_id[subject_tp["entity_id"]]
    object_entity = entity_by_id[object_tp["entity_id"]]
    relationship_records.append(
      {
        **relationship,
        "subject_entity_id": subject_entity["id"],
        "subject_entity_title": subject_entity["title"],
        "subject_entity_type": subject_entity["type"],
        "subject_time": subject_tp["time"],
        "subject_event": subject_tp["event"],
        "object_entity_id": object_entity["id"],
        "object_entity_title": object_entity["title"],
        "object_entity_type": object_entity["type"],
        "object_time": object_tp["time"],
        "object_event": object_tp["event"],
        "citation_count": len(citations_by_relationship.get(relationship["id"], [])),
      }
    )

  citation_target_ids = {
    "Timepoints": set(timepoint_by_id),
    "Relationships": {relationship["id"] for relationship in relationships},
  }
  orphan_citations = [
    citation["id"]
    for citation in citations
    if citation["target_id"] not in citation_target_ids.get(citation["target_table"], set())
  ]

  if dangling_relationships:
    raise RuntimeError(f"Dangling relationship ids: {dangling_relationships[:10]}")
  if orphan_citations:
    raise RuntimeError(f"Orphan citation ids: {orphan_citations[:10]}")

  entity_records = [
    {
      **entity,
      "timepoint_count": len(timepoints_by_entity.get(entity["id"], [])),
      "relationship_count": sum(
        1
        for relationship in relationship_records
        if relationship["subject_entity_id"] == entity["id"]
        or relationship["object_entity_id"] == entity["id"]
      ),
      "citation_count": sum(
        len(citations_by_timepoint.get(timepoint["id"], []))
        for timepoint in timepoints_by_entity.get(entity["id"], [])
      ),
    }
    for entity in entities
  ]

  timepoint_records = [
    {
      **timepoint,
      "entity_title": entity_by_id[timepoint["entity_id"]]["title"],
      "entity_type": entity_by_id[timepoint["entity_id"]]["type"],
      "citation_count": len(citations_by_timepoint.get(timepoint["id"], [])),
      "is_placeholder": timepoint["time"] == "未知" or timepoint["event"] == "占位",
    }
    for timepoint in timepoints
  ]

  dictionary_records = [
    {
      "id": item["id"],
      "title": item["title"],
      "catalog": item["catalog"],
      "page": item["page"],
      "text": item["text"],
      "text_summary": short_text(item["text"]),
    }
    for item in dictionary
  ]

  summary = {
    "source": {
      "entry_db": str(entry_db.relative_to(ROOT)),
      "dictionary_db": str(dict_db.relative_to(ROOT)),
    },
    "counts": {
      "Entities": len(entities),
      "Timepoints": len(timepoints),
      "Relationships": len(relationships),
      "Citations": len(citations),
      "DictionaryEntries": len(dictionary),
      "DictionaryUniqueTitles": len({item["title"] for item in dictionary}),
    },
    "entity_type_counts": dict(Counter(entity["type"] for entity in entities)),
    "relationship_type_counts": dict(Counter(rel["relation_type"] for rel in relationships)),
    "placeholder_timepoints": sum(1 for item in timepoint_records if item["is_placeholder"]),
  }

  payloads = {
    "summary.json": summary,
    "entities.json": entity_records,
    "timepoints.json": timepoint_records,
    "relationships.json": relationship_records,
    "citations.json": citations,
    "dictionary.json": dictionary_records,
  }

  for filename, payload in payloads.items():
    (output_dir / filename).write_text(
      json.dumps(payload, ensure_ascii=False, indent=2),
      encoding="utf-8",
    )

  print(f"Exported visualization data to {output_dir}")
  print(json.dumps(summary["counts"], ensure_ascii=False))


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--entry-db", type=Path, default=DEFAULT_ENTRY_DB)
  parser.add_argument("--dict-db", type=Path, default=DEFAULT_DICT_DB)
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  args = parser.parse_args()
  export(args.entry_db.resolve(), args.dict_db.resolve(), args.output_dir.resolve())


if __name__ == "__main__":
  main()
