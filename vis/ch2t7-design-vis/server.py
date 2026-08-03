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
import threading
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


def _institution_category(attr_categories: list[str], source_catalogs: list[str]) -> tuple[str, str]:
    """按结构化类别和辞典目录给机构归入设计稿的五类，不使用实体名称猜测。"""
    attrs = " ".join(attr_categories)
    if any(marker in attrs for marker in ("州府", "州县", "县级")):
        return "州县机构", "时间点类别"
    if "路级" in attrs:
        return "路级机构", "时间点类别"
    if any(marker in attrs for marker in ("军事", "军队", "禁军", "军号", "统兵")):
        return "军队机构", "时间点类别"
    if any(marker in attrs for marker in ("内廷", "宫廷", "宫中", "御前", "内侍", "内诸司")):
        return "内廷机构", "时间点类别"

    catalogs = " ".join(source_catalogs)
    if "第七编 皇宫京城禁卫侍奉机构类" in catalogs:
        military_sections = ("禁军三衙门", "三卫官与六统军门", "环卫官门")
        if any(section in catalogs for section in military_sections):
            return "军队机构", "辞典目录"
        return "内廷机构", "辞典目录"
    # 二至六编均属于宰执、中枢、寺监或司法监察体系，归入中央机构。
    return "中央机构", "辞典编目范围"


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

    # 辞典匹配：按 title 精确匹配 chapter2t7，抽取摘要与 fields 中的职源/职掌
    dict_rows = {}
    catalogs_by_title = {}
    for r in dictionary.execute("SELECT title, catalog, page, text, fields FROM chapter2t7"):
        title = r["title"]
        full_catalog = r["catalog"] or ""
        catalogs_by_title.setdefault(title, set()).add(full_catalog)
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
            "duty": _dict_section(fields, ("职掌", "职责", "职掌与编制")),
        }

    sources_by_entity = {}
    for r in entries.execute(
        "SELECT target_id, source_entry FROM BuildRecords WHERE target_table = 'Entities'"
    ):
        sources_by_entity.setdefault(r["target_id"], set()).add(r["source_entry"])

    category_counts = {}
    for entity in entities:
        if entity["type"] != "机构":
            continue
        source_catalogs = sorted({
            catalog
            for source_entry in sources_by_entity.get(entity["id"], ())
            for catalog in catalogs_by_title.get(source_entry, ())
            if catalog
        })
        attr_categories = sorted({
            item["attr_category"]
            for item in timepoints.get(entity["id"], ())
            if item["attr_category"]
        })
        category, category_basis = _institution_category(attr_categories, source_catalogs)
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
