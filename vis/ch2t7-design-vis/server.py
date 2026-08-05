#!/usr/bin/env python3
"""宋代职官设计稿可视化：只读数据服务 + dist 静态托管。

用法:
    python3 server.py [--port 8650] [--entries-db PATH] [--dict-db PATH]

接口:
    GET /api/data   一次返回前端所需全部 JSON（启动后惰性构建并缓存）
    GET /           dist/index.html（需先 pnpm build）
"""

import argparse
import json
import re
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "vis/backend"))

from normalize_times import normalize_time  # noqa: E402
from institution_categories import classify_institution  # noqa: E402
ENTRIES_DB = REPO_ROOT / "data/database/song_bureaucracy_entries_ch2t7.db"
DICT_DB = REPO_ROOT / "data/database/song_bureaucracy_dictionary_ch2t7.db"
DICT_TABLE = "chapter2t7"
DIST_DIR = HERE / "dist"
DESIGN_DIR = REPO_ROOT / "vis/宋代职官体系可视化打包文件 /svg格式"
DESIGN_HIERARCHY_SVG = DESIGN_DIR / "宋代职官体系可视化界面_画板 1 副本 4-01.svg"
DESIGN_COMPOSITION_SVG = DESIGN_DIR / "宋代职官体系可视化界面_画板 1 副本 4-02.svg"
DESIGN_TIMELINE_SVG = (
    REPO_ROOT
    / "vis/宋代职官体系可视化打包文件 /svg格式/宋代职官体系可视化界面字体转曲_画板 1 副本 4-01.svg"
)
DESIGN_FZQING_FONT = REPO_ROOT / "vis/宋代职官体系可视化打包文件 /字体/FZQingKBYSJW-M.TTF"
DESIGN_ADOBE_SONG_FONT = REPO_ROOT / "vis/宋代职官体系可视化打包文件 /字体/AdobeSongStd-Light.otf"

SUMMARY_LEN = 400
SECTION_LEN = 300

_cache = {}
_cache_lock = threading.Lock()


def _database_fingerprint() -> str:
    parts = []
    for path in (ENTRIES_DB, DICT_DB):
        for candidate in (path, Path(f"{path}-wal")):
            try:
                stat = candidate.stat()
                # mtime 和文件大小可能在同尺寸数据库替换、原位更新后保持不变；
                # ctime 与 inode 一并进入指纹，避免实时服务继续发送旧 payload。
                parts.append(
                    f"{candidate.name}:{stat.st_ino}:{stat.st_mtime_ns}:"
                    f"{stat.st_ctime_ns}:{stat.st_size}"
                )
            except FileNotFoundError:
                parts.append(f"{candidate.name}:missing")
    return "|".join(parts)


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
                "prev_id": r["prev_id"],
                "succ_id": r["succ_id"],
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

    # 统称主体仍保留在数据中供检索和详情使用；前端仅在它没有明确
    # 上下级机构边时，避免把它作为独立机构挂到虚拟分类根下。
    collective_rows = entity_edges("统称与实例")
    collective_entity_ids = {row["subj"] for row in collective_rows}
    collective_instance_edges = [
        {
            "id": row["rid"],
            "collective": row["subj"],
            "instance": row["obj"],
            "periods": periods_for(row),
            "states": [
                {
                    "id": row["rid"],
                    "subject_timepoint_id": row["subject_id"],
                    "object_timepoint_id": row["object_id"],
                }
            ],
        }
        for row in collective_rows
    ]

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
                "states": [],
            }
        hierarchy_by_key[key]["states"].append(
            {
                "id": r["rid"],
                "subject_timepoint_id": r["subject_id"],
                "object_timepoint_id": r["object_id"],
            }
        )
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
                "states": [],
            }
        staff_by_key[key]["states"].append(
            {
                "id": r["rid"],
                "subject_timepoint_id": r["subject_id"],
                "object_timepoint_id": r["object_id"],
            }
        )
        existing = staff_by_key[key]["periods"]
        for period in periods_for(r):
            if period not in existing:
                existing.append(period)
    staff_edges = list(staff_by_key.values())

    # 前后演变：供年度截面执行同一机构不同名称的互斥切换。
    # 与上下级边不同，这些边不参与层级树，只携带端点时间证据。
    evolution_edges = []
    for r in entity_edges("前后演变"):
        evolution_edges.append(
            {
                "id": r["rid"],
                "source": r["subj"],
                "target": r["obj"],
                "periods": periods_for(r),
                "states": [
                    {
                        "id": r["rid"],
                        "subject_timepoint_id": r["subject_id"],
                        "object_timepoint_id": r["object_id"],
                    }
                ],
            }
        )

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

    # 辞典匹配：按 title 精确匹配当前辞典表，抽取摘要与 fields 中的职源/职掌
    dict_rows = {}
    catalogs_by_title = {}
    catalogs_by_page = {}
    catalogs_by_reference = {}
    query = f'SELECT title, catalog, page, text, fields FROM "{DICT_TABLE}"'
    for r in dictionary.execute(query):
        title = r["title"]
        page = str(r["page"] or "").strip()
        full_catalog = r["catalog"] or ""
        catalogs_by_title.setdefault(title, set()).add(full_catalog)
        if page:
            catalogs_by_page.setdefault(page, set()).add(full_catalog)
            catalogs_by_reference.setdefault((title, page), set()).add(full_catalog)
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
            "catalog": full_catalog.split("/")[-1],
            "summary": text[:SUMMARY_LEN],
            "text": text,
            "origin": _dict_section(fields, ("职源与沿革", "职源", "沿革")),
            "aliases": _dict_section(fields, ("简称与别名", "简称", "别称")),
            "duty": _dict_section(fields, ("职掌", "职责", "职掌与编制")),
            "children": _dict_section(fields, ("下级机构", "所辖机构", "所属机构")),
            "office": _dict_section(fields, ("衙署", "办公地点")),
            "composition": _dict_section(fields, ("编制", "官额", "吏额")),
        }

    sources_by_entity = {}
    for r in entries.execute(
        "SELECT target_id, source_entry, source_page"
        " FROM BuildRecords WHERE target_table = 'Entities'"
    ):
        source = (r["source_entry"] or "").strip()
        page = str(r["source_page"] or "").strip()
        sources_by_entity.setdefault(r["target_id"], set()).add((source, page))

    category_by_entity = {}
    for entity in entities:
        if entity["type"] != "机构":
            continue
        source_catalogs = set()
        for source_entry, source_page in sources_by_entity.get(entity["id"], ()):
            catalogs = catalogs_by_reference.get((source_entry, source_page), set())
            if not catalogs and source_page:
                catalogs = catalogs_by_page.get(source_page, set())
            if not catalogs and source_entry:
                catalogs = catalogs_by_title.get(source_entry, set())
            source_catalogs.update(catalogs)
        attr_categories = sorted({
            item["attr_category"]
            for item in timepoints.get(entity["id"], ())
            if item["attr_category"]
        })
        category_by_entity[entity["id"]] = classify_institution(
            attr_categories, sorted(source_catalogs)
        )

    # Derived instances and renamed successors may have no direct BuildRecord.
    # They inherit only across semantic identity edges, never from hierarchy.
    identity_edges = [
        (edge["collective"], edge["instance"], "统称与实例")
        for edge in collective_instance_edges
    ] + [
        (edge["source"], edge["target"], "前后演变")
        for edge in evolution_edges
    ]
    changed = True
    while changed:
        changed = False
        for source_id, target_id, relation_type in identity_edges:
            source_category = category_by_entity.get(source_id, (None, ""))[0]
            target_category = category_by_entity.get(target_id, (None, ""))[0]
            if source_category and target_id in category_by_entity and not target_category:
                category_by_entity[target_id] = (
                    source_category,
                    f"沿{relation_type}继承自实体 #{source_id}",
                )
                changed = True
            elif target_category and source_id in category_by_entity and not source_category:
                category_by_entity[source_id] = (
                    target_category,
                    f"沿{relation_type}继承自实体 #{target_id}",
                )
                changed = True

    unresolved_category_ids = [
        entity_id
        for entity_id, (category, _) in category_by_entity.items()
        if category is None
    ]
    if unresolved_category_ids:
        sample = ", ".join(str(entity_id) for entity_id in unresolved_category_ids[:20])
        raise ValueError(
            f"有 {len(unresolved_category_ids)} 个机构缺少分类证据，示例实体 ID: {sample}"
        )

    category_counts = {}
    for entity in entities:
        if entity["type"] != "机构":
            continue
        category, category_basis = category_by_entity[entity["id"]]
        entity["category"] = category
        entity["category_basis"] = category_basis
        category_counts[category] = category_counts.get(category, 0) + 1

    entries.close()
    dictionary.close()

    entity_titles = {e["title"] for e in entities}
    dictionary_payload = {t: v for t, v in dict_rows.items() if t in entity_titles}

    return {
        "entities": entities,
        "timepoints": timepoints,
        "hierarchyEdges": hierarchy_edges,
        "staffEdges": staff_edges,
        "evolutionEdges": evolution_edges,
        "collectiveEntityIds": sorted(collective_entity_ids),
        "collectiveInstanceEdges": collective_instance_edges,
        "citations": citations,
        "dictionary": dictionary_payload,
        "meta": {
            "entities": len(entities),
            "hierarchyEdges": len(hierarchy_edges),
            "staffEdges": len(staff_edges),
            "evolutionEdges": len(evolution_edges),
            "collectiveEntities": len(collective_entity_ids),
            "collectiveInstanceEdges": len(collective_instance_edges),
            "dictionaryMatched": len(dictionary_payload),
            "categoryCounts": category_counts,
            "categoryUnresolved": len(unresolved_category_ids),
            "categoryUnresolvedIds": unresolved_category_ids,
            "source": ENTRIES_DB.name,
            "yearMin": 960,
            "yearMax": 1279,
        },
    }


def get_payload() -> bytes:
    fingerprint = _database_fingerprint()
    with _cache_lock:
        if _cache.get("fingerprint") != fingerprint:
            print("[server] 数据库已更新，重建 /api/data payload ...", flush=True)
            _cache["data"] = json.dumps(build_payload(), ensure_ascii=False).encode("utf-8")
            _cache["fingerprint"] = fingerprint
            print(f"[server] payload 大小 {len(_cache['data']) / 1024 / 1024:.1f} MB", flush=True)
        return _cache["data"]


def get_version() -> bytes:
    return json.dumps({"version": _database_fingerprint()}, ensure_ascii=False).encode("utf-8")


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
        design_files = {
            "/api/design/hierarchy.svg": DESIGN_HIERARCHY_SVG,
            "/api/design/composition.svg": DESIGN_COMPOSITION_SVG,
            "/api/design/timeline.svg": DESIGN_TIMELINE_SVG,
            "/api/design/fzqing.ttf": DESIGN_FZQING_FONT,
            "/api/design/adobe-song.otf": DESIGN_ADOBE_SONG_FONT,
        }
        if path in design_files:
            content_type = {
                ".svg": "image/svg+xml",
                ".ttf": "font/ttf",
                ".otf": "font/otf",
            }.get(design_files[path].suffix.lower(), "application/octet-stream")
            self._send(200, design_files[path].read_bytes(), content_type)
            return
        if path == "/api/data":
            try:
                self._send(200, get_payload(), "application/json; charset=utf-8")
            except Exception as exc:  # noqa: BLE001
                self._send(500, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        if path == "/api/version":
            self._send(200, get_version(), "application/json; charset=utf-8")
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
    global ENTRIES_DB, DICT_DB, DICT_TABLE

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8650)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--entries-db", type=Path, default=ENTRIES_DB)
    parser.add_argument("--dict-db", type=Path, default=DICT_DB)
    parser.add_argument("--dict-table", default=DICT_TABLE)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.dict_table):
        parser.error("--dict-table 必须是合法的 SQLite 表名")
    ENTRIES_DB = args.entries_db.expanduser().resolve()
    DICT_DB = args.dict_db.expanduser().resolve()
    DICT_TABLE = args.dict_table
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[server] 结构化数据源: {ENTRIES_DB}")
    print(f"[server] 辞典数据源: {DICT_DB}（表 {DICT_TABLE}）")
    print(f"[server] 服务地址: http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
