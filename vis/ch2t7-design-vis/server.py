#!/usr/bin/env python3
"""ch2t7 宋代职官设计稿可视化：只读数据服务 + dist 静态托管。

用法:
    python3 server.py [--port 8650]

接口:
    GET /api/data   一次返回前端所需全部 JSON（启动后惰性构建并缓存）
    GET /           dist/index.html（需先 pnpm build）
"""

import argparse
import json
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "vis/backend"))

from normalize_times import normalize_time  # noqa: E402
ENTRIES_DB = REPO_ROOT / "data/database/song_bureaucracy_entries_ch2t7.db"
DICT_DB = REPO_ROOT / "data/database/song_bureaucracy_dictionary_ch2t7.db"
DIST_DIR = HERE / "dist"
DESIGN_TIMELINE_SVG = (
    REPO_ROOT
    / "vis/宋代职官体系可视化打包文件 /svg格式/宋代职官体系可视化界面字体转曲_画板 1 副本 4-01.svg"
)

SUMMARY_LEN = 400
SECTION_LEN = 300

_cache = {}


def _connect(path: Path) -> sqlite3.Connection:
    if not path.exists():
        sys.exit(f"数据库不存在: {path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _dict_section(fields: dict, keys) -> str:
    for k in keys:
        v = fields.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:SECTION_LEN]
    return ""


def build_payload() -> dict:
    entries = _connect(ENTRIES_DB)
    dictionary = _connect(DICT_DB)

    entities = [
        {"id": r["id"], "title": r["title"], "type": r["type"]}
        for r in entries.execute("SELECT id, title, type FROM Entities ORDER BY id")
    ]

    timepoints = {}
    normalized_by_id = {}
    for r in entries.execute(
        "SELECT id, entity_id, time, event, prev_id, succ_id, attr_category,"
        " attr_officer_type, attr_grade, quotation FROM Timepoints ORDER BY entity_id, id"
    ):
        normalized = normalize_time(r["time"] or "")
        normalized_payload = {
            "year_start": normalized.year_start,
            "year_end": normalized.year_end,
            "time_type": normalized.time_type,
            "parse_note": normalized.parse_note or "",
        }
        normalized_by_id[r["id"]] = normalized_payload
        timepoints.setdefault(r["entity_id"], []).append(
            {
                "id": r["id"],
                "time": r["time"] or "",
                "event": r["event"] or "",
                "attr_category": r["attr_category"] or "",
                "attr_officer_type": r["attr_officer_type"] or "",
                "attr_grade": r["attr_grade"] or "",
                "quotation": r["quotation"] or "",
                **normalized_payload,
            }
        )

    def entity_edges(relation_type: str):
        rows = entries.execute(
            """
            SELECT r.id AS rid, r.subject_id, r.object_id,
                   s.entity_id AS subj, o.entity_id AS obj,
                   r.staff_quota, r.staff_type
            FROM Relationships r
            JOIN Timepoints s ON r.subject_id = s.id
            JOIN Timepoints o ON r.object_id = o.id
            WHERE r.relation_type = ? AND s.entity_id != o.entity_id
            """,
            (relation_type,),
        )
        return list(rows)

    def periods_for(row):
        periods = []
        seen_periods = set()
        for timepoint_id in (row["subject_id"], row["object_id"]):
            item = normalized_by_id.get(timepoint_id) or {}
            start = item.get("year_start")
            end = item.get("year_end")
            if start is None or end is None:
                continue
            key = (start, end, item.get("time_type"))
            if key in seen_periods:
                continue
            seen_periods.add(key)
            periods.append(
                {"start": start, "end": end, "time_type": item.get("time_type", "")}
            )
        return periods

    # 上下级机构：映射回实体 id 对并去重（subject=上级 → object=下级）
    hierarchy_by_key = {}
    for r in entity_edges("上下级机构"):
        key = (r["subj"], r["obj"])
        if key not in hierarchy_by_key:
            hierarchy_by_key[key] = {
                "id": r["rid"],
                "parent": r["subj"],
                "child": r["obj"],
                "periods": [],
            }
        existing = hierarchy_by_key[key]["periods"]
        for period in periods_for(r):
            if period not in existing:
                existing.append(period)
    hierarchy_edges = list(hierarchy_by_key.values())

    # 编制隶属：subject=机构时间点 → object=官职时间点；同一实体对可能有多条
    # （不同时间点的员额变化），全部保留，按 (org, official, quota, type) 去重
    staff_by_key = {}
    for r in entity_edges("编制隶属"):
        key = (r["subj"], r["obj"], r["staff_quota"] or "", r["staff_type"] or "")
        if key not in staff_by_key:
            staff_by_key[key] = {
                "id": r["rid"],
                "org": r["subj"],
                "official": r["obj"],
                "staff_quota": r["staff_quota"] or "",
                "staff_type": r["staff_type"] or "",
                "periods": [],
            }
        existing = staff_by_key[key]["periods"]
        for period in periods_for(r):
            if period not in existing:
                existing.append(period)
    staff_edges = list(staff_by_key.values())

    citations = {}
    for r in entries.execute(
        "SELECT target_table, target_id, citation, quotation, note, conflict_flag"
        " FROM Citations ORDER BY target_table, target_id, id"
    ):
        key = ("T" if r["target_table"] == "Timepoints" else "R") + str(r["target_id"])
        citations.setdefault(key, []).append(
            {
                "citation": r["citation"] or "",
                "quotation": r["quotation"] or "",
                "note": r["note"] or "",
                "conflict_flag": r["conflict_flag"] or 0,
            }
        )

    # 辞典匹配：按 title 精确匹配 chapter2t7，抽取摘要与 fields 中的职源/职掌
    dict_rows = {}
    for r in dictionary.execute("SELECT title, catalog, page, text, fields FROM chapter2t7"):
        title = r["title"]
        if title in dict_rows:
            continue
        fields = {}
        raw = r["fields"]
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    fields = parsed
            except (ValueError, TypeError):
                fields = {}
        text = (r["text"] or "").strip()
        dict_rows[title] = {
            "page": r["page"],
            "catalog": (r["catalog"] or "").split("/")[-1],
            "summary": text[:SUMMARY_LEN],
            "text": text,
            "origin": _dict_section(fields, ("职源与沿革", "职源", "沿革")),
            "duty": _dict_section(fields, ("职掌", "职责", "职掌与编制")),
        }

    entries.close()
    dictionary.close()

    entity_titles = {e["title"] for e in entities}
    dictionary_payload = {t: v for t, v in dict_rows.items() if t in entity_titles}

    return {
        "entities": entities,
        "timepoints": timepoints,
        "hierarchyEdges": hierarchy_edges,
        "staffEdges": staff_edges,
        "citations": citations,
        "dictionary": dictionary_payload,
        "meta": {
            "entities": len(entities),
            "hierarchyEdges": len(hierarchy_edges),
            "staffEdges": len(staff_edges),
            "dictionaryMatched": len(dictionary_payload),
            "source": ENTRIES_DB.name,
            "yearMin": 960,
            "yearMax": 1279,
        },
    }


def get_payload() -> bytes:
    if "data" not in _cache:
        print("[server] 构建 /api/data payload ...", flush=True)
        _cache["data"] = json.dumps(build_payload(), ensure_ascii=False).encode("utf-8")
        print(f"[server] payload 大小 {len(_cache['data']) / 1024 / 1024:.1f} MB", flush=True)
    return _cache["data"]


CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "Ch2t7DesignVis/0.1"

    def log_message(self, fmt, *args):  # 安静一点
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/design/timeline.svg":
            self._send(200, DESIGN_TIMELINE_SVG.read_bytes(), "image/svg+xml")
            return
        if path == "/api/data":
            try:
                self._send(200, get_payload(), "application/json; charset=utf-8")
            except Exception as exc:  # noqa: BLE001
                self._send(500, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        if path == "/api/health":
            self._send(200, b'{"ok":true}', "application/json")
            return

        # 静态文件：dist/
        if path in ("", "/"):
            path = "/index.html"
        safe = Path(*[p for p in path.split("/") if p not in ("", "..")])
        target = (DIST_DIR / safe).resolve()
        if not str(target).startswith(str(DIST_DIR.resolve())) or not target.is_file():
            # SPA 回退
            target = DIST_DIR / "index.html"
            if not target.is_file():
                self._send(503, "dist/ 不存在，请先运行 pnpm build".encode(), "text/plain; charset=utf-8")
                return
        ctype = CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self._send(200, target.read_bytes(), ctype)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8650)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[server] 数据源: {ENTRIES_DB}")
    print(f"[server] 服务地址: http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
