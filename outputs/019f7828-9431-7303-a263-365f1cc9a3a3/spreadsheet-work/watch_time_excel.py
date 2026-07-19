#!/usr/bin/env python3
"""Watch the visualization DB and atomically refresh the generated Excel snapshot."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import time
import zipfile


REPO = Path("/Users/zhanyi/Desktop/work/song-bureaucracy")
DB = REPO / "vis/data/song_bureaucracy_visualization.db"
BUILDER_DIR = REPO / "outputs/019f7828-9431-7303-a263-365f1cc9a3a3/spreadsheet-work"
BUILDER = BUILDER_DIR / "build_time_results.mjs"
GENERATED = REPO / "outputs/019f7828-9431-7303-a263-365f1cc9a3a3/宋代官制时间处理结果_2026-07-19.xlsx"
DEFAULT_TARGET = REPO / "vis/song-bureaucracy-visualization-v2/resources/reports/宋代官制时间处理结果.xlsx"
NODE = Path("/Users/zhanyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")


def database_stamp() -> tuple[tuple[str, int, int], ...]:
    result = []
    for path in (DB, Path(f"{DB}-wal")):
        if path.exists():
            stat = path.stat()
            result.append((path.name, stat.st_mtime_ns, stat.st_size))
    return tuple(result)


def lock_path(target: Path) -> Path:
    return target.with_name(f".~{target.name}")


def build() -> None:
    subprocess.run([str(NODE), str(BUILDER)], cwd=BUILDER_DIR, check=True)
    with zipfile.ZipFile(GENERATED) as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise RuntimeError(f"生成的 Excel 损坏: {bad_file}")


def publish(target: Path) -> bool:
    if lock_path(target).exists():
        print(f"同步版正在打开，等待关闭: {target}", flush=True)
        return False
    temporary = target.with_name(f".{target.name}.new")
    temporary.write_bytes(GENERATED.read_bytes())
    os.replace(temporary, target)
    GENERATED.unlink(missing_ok=True)
    print(f"Excel 已同步: {target}", flush=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    target = args.target.resolve()

    build()
    if args.once:
        if not publish(target):
            raise SystemExit("目标文件正在打开，未覆盖")
        return

    last_stamp = database_stamp()
    pending = not publish(target)
    print(f"监听数据库: {DB}", flush=True)
    print(f"同步文件: {target}", flush=True)
    try:
        while True:
            time.sleep(1.5)
            current_stamp = database_stamp()
            if current_stamp != last_stamp:
                # 等待普通事务或 WAL 写入稳定后再读取。
                time.sleep(1.0)
                stable_stamp = database_stamp()
                if stable_stamp != current_stamp:
                    continue
                print("检测到数据库变化，重新导出 Excel…", flush=True)
                build()
                pending = True
                last_stamp = stable_stamp
            if pending and publish(target):
                pending = False
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
