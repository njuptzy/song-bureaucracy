#!/usr/bin/env python3
"""Initialize combined ch1t12 dictionary/result DBs without modifying inputs."""

from __future__ import annotations

import argparse
import os
import sqlite3
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY_BASE = ROOT / "data/database/song_bureaucracy_dictionary_ch1t10.db"
DEFAULT_DICTIONARY_11T12 = ROOT / "data/database/song_bureaucracy_dictionary_ch11t12.db"
DEFAULT_RESULT_BASE = ROOT / "data/database/song_bureaucracy_entries_ch1t10.db"
DEFAULT_DICTIONARY_OUTPUT = ROOT / "data/database/song_bureaucracy_dictionary_ch1t12.db"
DEFAULT_RESULT_OUTPUT = ROOT / "data/database/song_bureaucracy_entries_ch1t12.db"


def ro_connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def copy_database(source: Path, output: Path) -> None:
    source_connection = ro_connect(source)
    output_connection = sqlite3.connect(output)
    try:
        source_connection.backup(output_connection)
    finally:
        output_connection.close()
        source_connection.close()


def build_dictionary(base: Path, source_11t12: Path, output: Path) -> None:
    copy_database(base, output)
    connection = sqlite3.connect(output)
    source = ro_connect(source_11t12)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("ALTER TABLE chapter1t10 RENAME TO chapter1t12")
        offset = connection.execute("SELECT MAX(id) FROM chapter1t12").fetchone()[0]
        rows = source.execute(
            "SELECT id,title,catalog,page,text,fields FROM chapter11t12 ORDER BY id"
        ).fetchall()
        connection.executemany(
            "INSERT INTO chapter1t12(id,title,catalog,page,text,fields) VALUES (?,?,?,?,?,?)",
            [(offset + row["id"], *tuple(row)[1:]) for row in rows],
        )
        connection.executemany(
            "INSERT INTO DictionarySources(combined_id,source_group,source_id) VALUES (?,?,?)",
            [(offset + row["id"], "11t12", row["id"]) for row in rows],
        )
        connection.commit()
    finally:
        connection.close()
        source.close()


def validate_dictionary(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()
        count = connection.execute("SELECT COUNT(*) FROM chapter1t12").fetchone()[0]
        mappings = connection.execute("SELECT COUNT(*) FROM DictionarySources").fetchone()[0]
        source_11t12 = connection.execute(
            "SELECT COUNT(*) FROM DictionarySources WHERE source_group='11t12'"
        ).fetchone()[0]
        assert (count, mappings, source_11t12) == (5252, 5252, 605), (
            count,
            mappings,
            source_11t12,
        )
    finally:
        connection.close()


def validate_result(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        connection.close()


def replace(temp: Path, target: Path, overwrite: bool) -> None:
    if target.exists() and not overwrite:
        raise FileExistsError(f"目标已存在，请显式传入 --overwrite：{target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temp, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dictionary-base", type=Path, default=DEFAULT_DICTIONARY_BASE)
    parser.add_argument("--dictionary-11t12", type=Path, default=DEFAULT_DICTIONARY_11T12)
    parser.add_argument("--result-base", type=Path, default=DEFAULT_RESULT_BASE)
    parser.add_argument("--dictionary-output", type=Path, default=DEFAULT_DICTIONARY_OUTPUT)
    parser.add_argument("--result-output", type=Path, default=DEFAULT_RESULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for source_file in (args.dictionary_base, args.dictionary_11t12, args.result_base):
        if not source_file.is_file():
            raise FileNotFoundError(source_file)
    temp_dir = Path(tempfile.mkdtemp(prefix="song-bureaucracy-ch1t12-"))
    temp_dictionary = temp_dir / "dictionary.db"
    temp_result = temp_dir / "result.db"
    try:
        build_dictionary(args.dictionary_base, args.dictionary_11t12, temp_dictionary)
        copy_database(args.result_base, temp_result)
        validate_dictionary(temp_dictionary)
        validate_result(temp_result)
        replace(temp_dictionary, args.dictionary_output, args.overwrite)
        replace(temp_result, args.result_output, args.overwrite)
        print(f"dictionary={args.dictionary_output}")
        print(f"result={args.result_output}")
        print("dictionary_rows=5252 source_11t12=605")
    finally:
        temp_dictionary.unlink(missing_ok=True)
        temp_result.unlink(missing_ok=True)
        temp_dir.rmdir()


if __name__ == "__main__":
    main()
