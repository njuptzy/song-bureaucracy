#!/usr/bin/env python3
"""用现有 8050 前端独立展示尚书省 Excel 数据。"""

import argparse
import hashlib
import json
import re
import sys
import threading
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
VIS_ROOT = HERE.parent
EXCEL_JSON = HERE / "excel_data.json"
ORIGINAL_VIS = VIS_ROOT / "ch2t7-design-vis"
DIST_DIR = ORIGINAL_VIS / "dist"
DESIGN_DIR = VIS_ROOT / "宋代职官体系可视化打包文件 /svg格式"
DESIGN_FILES = {
    "/api/design/hierarchy.svg": DESIGN_DIR / "宋代职官体系可视化界面_画板 1 副本 4-01.svg",
    "/api/design/composition.svg": DESIGN_DIR / "宋代职官体系可视化界面_画板 1 副本 4-02.svg",
    "/api/design/timeline.svg": DESIGN_DIR / "宋代职官体系可视化界面字体转曲_画板 1 副本 4-01.svg",
    "/api/design/fzqing.ttf": VIS_ROOT / "宋代职官体系可视化打包文件 /字体/FZQingKBYSJW-M.TTF",
    "/api/design/adobe-song.otf": VIS_ROOT / "宋代职官体系可视化打包文件 /字体/AdobeSongStd-Light.otf",
}

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
}

_cache = {}
_cache_lock = threading.Lock()


def clean(value) -> str:
    return str(value or "").strip()


def names(value) -> list[str]:
    """拆分 Excel 中明确的顿号式列表；顿号保留为正式名称的一部分。"""
    return [item.strip() for item in re.split(r"[，；;\n]+", clean(value)) if item.strip()]


def year_of(row):
    value = row.get("开始-公元年份")
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"(?:9\d{2}|1[012]\d{2})", clean(value))
    return int(match.group()) if match else None


def source_label(table: str, row: dict) -> str:
    return f'Excel“{table}”第{row.get("__row", "?")}行'


def detail_text(row: dict, fields: tuple[str, ...]) -> str:
    return "\n".join(clean(row.get(field)) for field in fields if clean(row.get(field)))


def _fingerprint() -> str:
    digest = hashlib.sha256()
    for path in (EXCEL_JSON, DIST_DIR / "index.html"):
        stat = path.stat()
        digest.update(f"{path}:{stat.st_mtime_ns}:{stat.st_size}".encode())
    return digest.hexdigest()[:20]


def build_payload() -> dict:
    raw = json.loads(EXCEL_JSON.read_text(encoding="utf-8"))
    entities = []
    entity_by_key = {}
    dictionary = {}
    timepoint_drafts = defaultdict(list)
    hierarchy_drafts = []
    staff_drafts = []
    evolution_drafts = []
    citations = defaultdict(list)
    sequence = 0

    def ensure_entity(title: str, entity_type: str):
        title = clean(title)
        if not title:
            return None
        key = (entity_type, title)
        if key not in entity_by_key:
            entity = {
                "id": len(entities) + 1,
                "title": title,
                "type": entity_type,
            }
            if entity_type == "机构":
                entity.update({"category": "中央机构", "category_basis": "Excel机构表"})
            entity_by_key[key] = entity
            entities.append(entity)
        return entity_by_key[key]

    for row in raw.get("institutions", []):
        entity = ensure_entity(row.get("机构名"), "机构")
        if not entity:
            continue
        origin = clean(row.get("职源与沿革文本"))
        aliases = clean(row.get("简称与别名"))
        source = clean(row.get("出处"))
        dictionary[entity["title"]] = {
            "page": clean(row.get("参考文档页数")),
            "catalog": "尚书省机构表",
            "summary": aliases[:400],
            "text": "\n".join(part for part in (aliases, origin, source) if part),
            "origin": origin[:300],
            "duty": "",
        }

    for row in raw.get("offices", []):
        entity = ensure_entity(row.get("官职名"), "官职")
        if not entity:
            continue
        origin = clean(row.get("职源与沿革文本"))
        aliases = clean(row.get("简称与别名"))
        source = clean(row.get("出处"))
        dictionary[entity["title"]] = {
            "page": clean(row.get("参考文档页数")),
            "catalog": "尚书省官职表",
            "summary": aliases[:400],
            "text": "\n".join(part for part in (aliases, origin, source) if part),
            "origin": origin[:300],
            "duty": "",
        }

    def add_timepoint(
        entity, year, raw_time, event, quotation, source, row_order,
        *, category="", officer_type="", grade="",
    ):
        nonlocal sequence
        if not entity or year is None:
            return None
        sequence += 1
        draft = {
            "_sequence": sequence,
            "_row_order": row_order,
            "entity_id": entity["id"],
            "time": clean(raw_time) or str(year),
            "event": clean(event),
            "attr_category": clean(category),
            "attr_officer_type": clean(officer_type),
            "attr_grade": clean(grade),
            "quotation": clean(quotation),
            "year_start": year,
            "year_end": year,
            "time_type": "exact",
            "parse_note": "Excel已提供公元年份",
            "_citation": source,
        }
        timepoint_drafts[entity["id"]].append(draft)
        return draft

    def event_text(title, action, details=""):
        return "；".join(part for part in (f"{title}{action}", details) if part)

    org_rows = raw.get("institutionChanges", [])
    for row in org_rows:
        year = year_of(row)
        if year is None:
            continue
        change = clean(row.get("变更类型"))
        old_names = names(row.get("原机构"))
        new_names = names(row.get("现机构"))
        # 合并类的“原机构”是明确列表；其他单元格中的顿号属于正式名称。
        source = source_label("机构动态表2", row)
        details = detail_text(row, ("新职能", "编制文本", "衙署"))
        quotation = details or source
        row_order = int(row.get("__row") or 0)
        old_entities = [ensure_entity(name, "机构") for name in old_names]
        new_entities = [ensure_entity(name, "机构") for name in new_names]

        old_points = []
        new_points = []
        rename_like = change in {"移置", "并入", "合并", "打散"} or (
            change == "变更" and old_names != new_names
        )
        if change == "取消":
            for entity in old_entities:
                old_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], "罢置", details), quotation, source, row_order,
                    category="中央机构",
                ))
        elif rename_like:
            target_text = "、".join(new_names)
            for entity in old_entities:
                old_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], f"改置为{target_text}", details),
                    quotation, source, row_order, category="中央机构",
                ))
            for entity in new_entities:
                new_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], "设置", details), quotation, source, row_order,
                    category="中央机构",
                ))
        elif change == "拆分":
            for entity in old_entities:
                old_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], "下设新机构", details), quotation, source, row_order,
                    category="中央机构",
                ))
            for entity in new_entities:
                new_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], "设置", details), quotation, source, row_order,
                    category="中央机构",
                ))
        elif change in {"新增", "重启"}:
            for entity in new_entities:
                new_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], "设置", details), quotation, source, row_order,
                    category="中央机构",
                ))
        else:
            for entity in new_entities or old_entities:
                action = "设置并调整" if change == "变更" else "调整"
                new_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], action, details), quotation, source, row_order,
                    category="中央机构",
                ))

        anchor_points = new_points or old_points
        for point in new_points:
            entity_title = entities[point["entity_id"] - 1]["title"]
            entry = dictionary.get(entity_title)
            if entry and clean(row.get("新职能")):
                entry["duty"] = clean(row.get("新职能"))[:300]

        # 新上级机构 → 当前机构（或取消前的原机构）
        child_entities = new_entities or old_entities
        child_points = new_points or old_points
        for parent_name in names(row.get("新上级机构")):
            parent = ensure_entity(parent_name, "机构")
            parent_point = add_timepoint(
                parent, year, row.get("开始-时间"),
                event_text(parent["title"], "有下级机构记载"), source, source, row_order,
                category="中央机构",
            )
            for child, child_point in zip(child_entities, child_points):
                if parent["id"] != child["id"] and child_point:
                    hierarchy_drafts.append((parent, child, parent_point, child_point, source))

        # 当前机构 → 新下级机构
        for parent, parent_point in zip(child_entities, child_points):
            for child_name in names(row.get("新下级机构")):
                child = ensure_entity(child_name, "机构")
                if child["id"] == parent["id"]:
                    continue
                child_point = add_timepoint(
                    child, year, row.get("开始-时间"),
                    event_text(child["title"], "作为下级机构记载"), source, source, row_order,
                    category="中央机构",
                )
                hierarchy_drafts.append((parent, child, parent_point, child_point, source))

        if rename_like:
            for old_entity, old_point in zip(old_entities, old_points):
                for new_entity, new_point in zip(new_entities, new_points):
                    if old_entity["id"] != new_entity["id"]:
                        evolution_drafts.append((old_entity, new_entity, old_point, new_point, source))

    office_rows = raw.get("officeChanges", [])
    for row in office_rows:
        year = year_of(row)
        if year is None:
            continue
        change = clean(row.get("变更类型"))
        old_names = names(row.get("原官职"))
        new_names = names(row.get("现官职"))
        source = source_label("官职动态表2", row)
        details = detail_text(row, ("职掌", "官品文本", "编制文本"))
        quotation = details or source
        row_order = int(row.get("__row") or 0)
        old_entities = [ensure_entity(name, "官职") for name in old_names]
        new_entities = [ensure_entity(name, "官职") for name in new_names]
        old_points = []
        new_points = []
        rename_like = change in {"打散", "合并"} or (
            change == "变更" and old_names != new_names
        )
        attrs = {
            "officer_type": row.get("类别"),
            "grade": row.get("官品"),
        }
        if change == "取消":
            for entity in old_entities:
                old_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], "罢置", details), quotation, source, row_order,
                    **attrs,
                ))
        elif rename_like:
            target_text = "、".join(new_names)
            for entity in old_entities:
                old_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], f"改置为{target_text}", details),
                    quotation, source, row_order, **attrs,
                ))
            for entity in new_entities:
                new_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], "设置", details), quotation, source, row_order,
                    **attrs,
                ))
        elif change in {"新增", "重启"}:
            for entity in new_entities:
                new_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], "设置", details), quotation, source, row_order,
                    **attrs,
                ))
        else:
            for entity in new_entities or old_entities:
                action = "设置并调整" if change == "变更" else "调整"
                new_points.append(add_timepoint(
                    entity, year, row.get("开始-时间"),
                    event_text(entity["title"], action, details), quotation, source, row_order,
                    **attrs,
                ))

        for point in new_points:
            entity_title = entities[point["entity_id"] - 1]["title"]
            entry = dictionary.get(entity_title)
            if entry and clean(row.get("职掌")):
                entry["duty"] = clean(row.get("职掌"))[:300]
        if rename_like:
            for old_entity, old_point in zip(old_entities, old_points):
                for new_entity, new_point in zip(new_entities, new_points):
                    if old_entity["id"] != new_entity["id"]:
                        evolution_drafts.append((old_entity, new_entity, old_point, new_point, source))

    # 按实体、年份、Excel 行号串起互为 reciprocal 的时间链。
    next_timepoint_id = 1
    for entity in entities:
        drafts = timepoint_drafts.get(entity["id"], [])
        drafts.sort(key=lambda item: (item["year_start"], item["_row_order"], item["_sequence"]))
        for draft in drafts:
            draft["id"] = next_timepoint_id
            next_timepoint_id += 1
        for index, draft in enumerate(drafts):
            draft["prev_id"] = drafts[index - 1]["id"] if index else None
            draft["succ_id"] = drafts[index + 1]["id"] if index + 1 < len(drafts) else None
            citations[f'T{draft["id"]}'].append({
                "citation": draft["_citation"],
                "quotation": draft["quotation"],
                "note": "由Excel动态表转换",
                "conflict_flag": 0,
            })

    timepoints = {}
    for entity_id, drafts in timepoint_drafts.items():
        timepoints[str(entity_id)] = [
            {key: value for key, value in draft.items() if not key.startswith("_") and key != "entity_id"}
            for draft in drafts
        ]

    relation_id = 1

    def relation_state(subject_point, object_point):
        return {
            "id": None,
            "subject_timepoint_id": subject_point["id"],
            "object_timepoint_id": object_point["id"],
        }

    def relation_period(subject_point, object_point):
        year = max(subject_point["year_start"], object_point["year_start"])
        return [{"start": year, "end": year, "time_type": "exact"}]

    hierarchy_edges = []
    for parent, child, parent_point, child_point, source in hierarchy_drafts:
        if not parent_point or not child_point:
            continue
        state = relation_state(parent_point, child_point)
        state["id"] = relation_id
        hierarchy_edges.append({
            "id": relation_id,
            "parent": parent["id"],
            "child": child["id"],
            "periods": relation_period(parent_point, child_point),
            "states": [state],
        })
        citations[f"R{relation_id}"].append({
            "citation": source, "quotation": source,
            "note": "Excel记载的上下级机构关系", "conflict_flag": 0,
        })
        relation_id += 1

    # 官职静态表直接提供隶属机构；关系从官职第一次有年份证据时生效。
    for row in raw.get("offices", []):
        official = ensure_entity(row.get("官职名"), "官职")
        if not official:
            continue
        official_points = timepoint_drafts.get(official["id"], [])
        if not official_points:
            continue
        official_point = official_points[0]
        year = official_point["year_start"]
        for org_name in names(row.get("隶属机构")):
            org = ensure_entity(org_name, "机构")
            org_points = timepoint_drafts.get(org["id"], [])
            eligible = [point for point in org_points if point["year_start"] <= year]
            # 动态表没有给这个机构提供同期年份证据时，不猜测关系的生效年份。
            if not eligible:
                continue
            org_point = eligible[-1]
            state = relation_state(org_point, official_point)
            state["id"] = relation_id
            source = source_label("官职静态表", row)
            staff_drafts.append({
                "id": relation_id,
                "org": org["id"],
                "official": official["id"],
                "staff_quota": "",
                "staff_type": clean(row.get("类别")),
                "periods": relation_period(org_point, official_point),
                "states": [state],
            })
            citations[f"R{relation_id}"].append({
                "citation": source, "quotation": clean(row.get("隶属机构")),
                "note": "Excel官职静态表记载的隶属机构", "conflict_flag": 0,
            })
            relation_id += 1

    evolution_edges = []
    for old_entity, new_entity, old_point, new_point, source in evolution_drafts:
        if not old_point or not new_point:
            continue
        state = relation_state(old_point, new_point)
        state["id"] = relation_id
        evolution_edges.append({
            "id": relation_id,
            "source": old_entity["id"],
            "target": new_entity["id"],
            "periods": relation_period(old_point, new_point),
            "states": [state],
        })
        citations[f"R{relation_id}"].append({
            "citation": source, "quotation": source,
            "note": "Excel变更类型转换的前后演变关系", "conflict_flag": 0,
        })
        relation_id += 1

    category_counts = defaultdict(int)
    for entity in entities:
        if entity["type"] == "机构":
            category_counts[entity["category"]] += 1

    return {
        "entities": entities,
        "timepoints": timepoints,
        "hierarchyEdges": hierarchy_edges,
        "staffEdges": staff_drafts,
        "evolutionEdges": evolution_edges,
        "collectiveEntityIds": [],
        "collectiveInstanceEdges": [],
        "citations": dict(citations),
        "dictionary": dictionary,
        "meta": {
            "entities": len(entities),
            "hierarchyEdges": len(hierarchy_edges),
            "staffEdges": len(staff_drafts),
            "evolutionEdges": len(evolution_edges),
            "collectiveEntities": 0,
            "collectiveInstanceEdges": 0,
            "dictionaryMatched": len(dictionary),
            "categoryCounts": dict(category_counts),
            "source": raw.get("source", {}).get("file", EXCEL_JSON.name),
            "yearMin": 960,
            "yearMax": 1279,
        },
    }


def get_payload() -> bytes:
    fingerprint = _fingerprint()
    with _cache_lock:
        if _cache.get("fingerprint") != fingerprint:
            print("[excel-vis] Excel数据已更新，重建 /api/data ...", flush=True)
            _cache["payload"] = json.dumps(build_payload(), ensure_ascii=False).encode("utf-8")
            _cache["fingerprint"] = fingerprint
        return _cache["payload"]


def static_body(target: Path) -> bytes:
    body = target.read_bytes()
    if target.suffix == ".html":
        body = body.replace(
            "宋代职官体系导览 · 二至七编".encode(),
            "尚书省机构官职体系 · Excel".encode(),
        )
    elif target.suffix == ".js":
        body = body.replace("正在读取 ch2t7 数据…".encode(), "正在读取 Excel 数据…".encode())
    return body


class Handler(BaseHTTPRequestHandler):
    server_version = "ShangshuExcelVis/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_body(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/data":
            try:
                self.send_body(200, get_payload(), CONTENT_TYPES[".json"])
            except Exception as exc:  # noqa: BLE001
                self.send_body(500, json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), CONTENT_TYPES[".json"])
            return
        if path == "/api/version":
            self.send_body(200, json.dumps({"version": _fingerprint()}).encode(), CONTENT_TYPES[".json"])
            return
        if path == "/api/health":
            self.send_body(200, b'{"ok":true,"source":"excel"}', CONTENT_TYPES[".json"])
            return
        if path in DESIGN_FILES:
            target = DESIGN_FILES[path]
            self.send_body(200, target.read_bytes(), CONTENT_TYPES.get(target.suffix, "application/octet-stream"))
            return

        if path in ("", "/"):
            path = "/index.html"
        safe = Path(*[part for part in path.split("/") if part not in ("", "..")])
        target = (DIST_DIR / safe).resolve()
        if not str(target).startswith(str(DIST_DIR.resolve())) or not target.is_file():
            target = DIST_DIR / "index.html"
        if not target.is_file():
            self.send_body(503, "原8050构建文件不存在".encode(), "text/plain; charset=utf-8")
            return
        self.send_body(200, static_body(target), CONTENT_TYPES.get(target.suffix, "application/octet-stream"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8060)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[excel-vis] 数据源: {EXCEL_JSON}")
    print(f"[excel-vis] 服务地址: http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
