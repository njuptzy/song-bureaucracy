#!/usr/bin/env python3
"""Serve visualization v2 and expose a live, read-only SQLite API."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

try:
    from .export_visualization_data import build_payload
except ImportError:  # 直接执行 python3 vis/backend/serve_visualization_v2.py
    from export_visualization_data import build_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "vis/data/song_bureaucracy_visualization.db"
DEFAULT_DIST = REPO_ROOT / "vis/song-bureaucracy-visualization-v2/dist"


class LivePayloadCache:
    """按 SQLite 主文件和 WAL 的状态缓存序列化结果。

    min_stable_seconds：检测到库文件变化后，等指纹稳定这么久才重建缓存。
    批量写库期间前端会继续拿到旧版本，避免每 1.5 秒一次全量刷新；传 0 表示立即重建。
    """

    def __init__(self, db_path: Path, min_stable_seconds: float = 2.0):
        self.db_path = db_path.resolve()
        self.min_stable_seconds = min_stable_seconds
        self._lock = threading.Lock()
        self._stamp: tuple[tuple[str, int, int], ...] | None = None
        self._version: str | None = None
        self._payload: dict[str, Any] | None = None
        self._body: bytes | None = None
        self._pending_stamp: tuple[tuple[str, int, int], ...] | None = None
        self._pending_since = 0.0

    def _database_stamp(self) -> tuple[tuple[str, int, int], ...]:
        parts = []
        for path in (self.db_path, Path(f"{self.db_path}-wal")):
            if path.exists():
                stat = path.stat()
                parts.append((path.name, stat.st_mtime_ns, stat.st_size))
        if not parts:
            raise FileNotFoundError(self.db_path)
        return tuple(parts)

    @staticmethod
    def _stamp_version(stamp: tuple[tuple[str, int, int], ...]) -> str:
        return hashlib.sha256(repr(stamp).encode("utf-8")).hexdigest()[:16]

    def get(self) -> tuple[str, dict[str, Any], bytes]:
        stamp = self._database_stamp()
        now = time.monotonic()
        with self._lock:
            if self._stamp == stamp and self._payload is not None and self._body is not None:
                self._pending_stamp = None
                return self._version or "", self._payload, self._body

            if self._payload is not None:
                # 已有缓存：新指纹需持续稳定 min_stable_seconds 才重建，期间仍发旧版本
                if self._pending_stamp != stamp:
                    self._pending_stamp = stamp
                    self._pending_since = now
                if now - self._pending_since < self.min_stable_seconds:
                    return self._version or "", self._payload, self._body

            # 在同一个 SQLite 只读快照中装配数据；若写入恰好发生在装配期间，
            # 下一次轮询会根据新 stamp 再刷新，不向数据库写入任何内容。
            payload = build_payload(self.db_path)
            final_stamp = self._database_stamp()
            version = self._stamp_version(final_stamp)
            payload["meta"] = {**payload["meta"], "databaseVersion": version}
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

            self._stamp = final_stamp
            self._version = version
            self._payload = payload
            self._body = body
            self._pending_stamp = None
            return version, payload, body


class Handler(BaseHTTPRequestHandler):
    cache: LivePayloadCache
    static_dir: Path

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _send_bytes(
        self,
        body: bytes,
        content_type: str,
        *,
        status: int = 200,
        version: str | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if version:
            self.send_header("X-Database-Version", version)
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: Any, *, status: int = 200, version: str | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status=status, version=version)

    def _send_static(self, request_path: str) -> None:
        relative = "index.html" if request_path == "/" else request_path.lstrip("/")
        path = (self.static_dir / relative).resolve()
        if not path.is_relative_to(self.static_dir) or not path.is_file():
            self._send_json({"error": "not found"}, status=404)
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"
        self._send_bytes(path.read_bytes(), content_type)

    def do_GET(self) -> None:  # noqa: N802
        path = unquote(urlparse(self.path).path)
        try:
            if path == "/api/data":
                version, _, body = self.cache.get()
                self._send_bytes(body, "application/json; charset=utf-8", version=version)
            elif path == "/api/version":
                version, payload, _ = self.cache.get()
                self._send_json(
                    {"version": version, "meta": payload["meta"]},
                    version=version,
                )
            elif path.startswith("/api/"):
                self._send_json({"error": "unknown api"}, status=404)
            else:
                self._send_static(path)
        except BrokenPipeError:
            pass
        except Exception as exc:
            self._send_json({"error": f"{type(exc).__name__}: {exc}"}, status=500)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8643)
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=2.0,
        help="库文件变化后等待写入稳定的秒数，期间继续发旧版本；0 表示立即刷新（默认 2.0）",
    )
    args = parser.parse_args()

    db_path = args.db.resolve()
    static_dir = args.dist.resolve()
    if not db_path.is_file():
        raise SystemExit(f"数据库不存在: {db_path}")
    if not static_dir.is_dir():
        raise SystemExit(f"前端构建目录不存在: {static_dir}\n请先运行 pnpm build")

    Handler.cache = LivePayloadCache(db_path, min_stable_seconds=args.settle_seconds)
    Handler.static_dir = static_dir
    version, payload, _ = Handler.cache.get()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"实时数据库（只读）: {db_path}")
    print(f"数据库版本: {version}")
    print(
        "数据量: "
        f"{payload['meta']['entityCount']} 实体 / "
        f"{payload['meta']['eventCount']} 时间点 / "
        f"{payload['meta']['relationCount']} 关系"
    )
    print(f"可视化: http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
