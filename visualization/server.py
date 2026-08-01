#!/usr/bin/env python3
"""职官演变审查可视化 —— 本地只读 Web 服务。

将结构化结果数据库（Entities/Timepoints/Relationships/Citations）与
《宋代官制辞典》原文并排展示，按辞典条目逐条审查，自动标出可疑数据。

启动：
  python3 visualization/server.py [--entry-db PATH] [--dict-db PATH] [--port 8642]

数据库以只读模式打开（uri mode=ro），本服务绝不写库。
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import threading
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent
DEFAULT_ENTRY_DB = ROOT / "agent-v0612/records/v0614-v4-flash/song_bureaucracy_entries_v0614-v4-flash.db"
DEFAULT_DICT_DB = ROOT / "data/database/song_bureaucracy_dictionary.db"
DICT_TABLE = "chapter8t10"

PLACEHOLDER_TIME = "未知"
PLACEHOLDER_EVENT = "占位"

ISSUE_LABELS = {
  "quotation_not_found": "引用原文匹配失败",
  "citation_unparsed": "引用出处无法解析",
  "citation_entry_missing": "引用指向的辞典条目不存在",
  "chain_broken": "时间点链异常",
  "placeholder_left": "残留占位时间点",
  "no_citation": "缺少引用",
  "conflict_flagged": "标记为冲突的引用",
  "dangling": "悬空引用/关系",
}


# ---------------------------------------------------------------------------
# citation 出处解析：从引文出处文本中解析（页码, 词条名）
# ---------------------------------------------------------------------------

CITATION_PATTERNS = [
  # 《宋代官制辞典》第529页“发运使司”条
  re.compile(
    r"《(?:宋代官制)?辞典》\s*第\s*(\d+)\s*页\s*[“”\"‘’']\s*([^“”\"‘’']+?)\s*[“”\"‘’']\s*(?:词条|条目|条)"
  ),
  # 《辞典》482页 “河北兵马大元帅” 词条 “基本介绍” 标签
  re.compile(
    r"《(?:宋代官制)?辞典》\s*(\d+)\s*页\s*[“”\"‘’']\s*([^“”\"‘’']+?)\s*[“”\"‘’']\s*(?:词条|条目)"
  ),
  # 《宋代官制辞典》111页，枢密院条目，执掌字段 / 枢密院词条
  re.compile(
    r"《(?:宋代官制)?辞典》\s*(\d+)\s*页[，,、\s]*[“”\"‘’']?([^，,、“”\"‘’'\s]+?)[“”\"‘’']?\s*(?:词条|条目)"
  ),
  # 《辞典》482页 “河北兵马大元帅” 基本介绍
  re.compile(
    r"《(?:宋代官制)?辞典》\s*(\d+)\s*页\s*[“”\"‘’']\s*([^“”\"‘’']+?)\s*[“”\"‘’']"
  ),
  # 仅有页码：《辞典》482页 ……（词条名缺失，靠 quotation 在该页条目中消歧）
  re.compile(r"《(?:宋代官制)?辞典》\s*(\d+)\s*页"),
  # 旧/模型变体格式：把词条名直接写在书名号里，如
  # 《河北兵马大元帅府》482页 基本介绍
  # 注意排除《辞典》/《宋代官制辞典》，这些由上面的专门格式处理。
  re.compile(r"《([^》]+?)》\s*(\d+)\s*页"),
]


def parse_citation(text: Optional[str]) -> Optional[tuple[str, Optional[str]]]:
  """返回 (page, title)；title 可能为 None（只解析出页码）；完全失败返回 None。"""
  if not text:
    return None
  for pattern in CITATION_PATTERNS[:4]:
    m = pattern.search(text)
    if m:
      return m.group(1), m.group(2).strip()
  m = CITATION_PATTERNS[4].search(text)
  if m:
    return m.group(1), None
  m = CITATION_PATTERNS[5].search(text)
  if m:
    title = m.group(1).strip()
    if title not in {"辞典", "宋代官制辞典"}:
      return m.group(2), title
  return None


# ---------------------------------------------------------------------------
# quotation 高亮匹配：规范化后子串查找，并映射回原文下标区间
# ---------------------------------------------------------------------------

_IGNORED_CHARS = set(
  "，。、；：？！·…—‐-－_*~～,.;:?!\"'“”‘’()（）[]【】《》〈〉<>"
  "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
)


def normalize_with_map(text: str) -> tuple[str, list[int]]:
  """去掉空白和标点；返回规范化串和「规范化下标 -> 原文下标」映射。"""
  chars: list[str] = []
  index_map: list[int] = []
  for i, ch in enumerate(text):
    if ch.isspace() or ch in _IGNORED_CHARS:
      continue
    chars.append(ch)
    index_map.append(i)
  return "".join(chars), index_map


def match_quotation(
  norm_text: str, index_map: list[int], raw_len: int, quotation: str
) -> Optional[dict[str, Any]]:
  """在条目原文中定位 quotation。

  返回 {"status": "exact"|"partial", "start": int, "end": int}（原文下标区间），
  找不到返回 None。
  """
  norm_q, _ = normalize_with_map(quotation)
  if not norm_q:
    return None

  def locate(fragment: str, status: str) -> Optional[dict[str, Any]]:
    pos = norm_text.find(fragment)
    if pos < 0:
      return None
    start = index_map[pos]
    last = pos + len(fragment) - 1
    end = index_map[last] + 1 if last < len(index_map) else raw_len
    return {"status": status, "start": start, "end": end}

  hit = locate(norm_q, "exact")
  if hit:
    return hit
  # 退化匹配：取规范化后的前缀/后缀片段（OCR 局部差异时仍可定位大致位置）
  for length in (20, 12):
    if len(norm_q) <= length:
      continue
    hit = locate(norm_q[:length], "partial") or locate(norm_q[-length:], "partial")
    if hit:
      return hit
  return None


# ---------------------------------------------------------------------------
# 数据模型：全量加载两个数据库，建立关联与一致性检查结果
# ---------------------------------------------------------------------------

class Model:
  def __init__(self, entry_db: Path, dict_db: Path, dict_table: str = DICT_TABLE):
    self.entry_db = entry_db
    self.dict_db = dict_db
    self.dict_table = dict_table
    self._load_tables()
    self._index_dictionary()
    self._link_citations()
    self._check_consistency()
    self._map_entities_to_entries()

  # ---- 加载 ----

  @staticmethod
  def _read_rows(db_path: Path, sql: str) -> list[dict[str, Any]]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
      return [dict(row) for row in conn.execute(sql)]
    finally:
      conn.close()

  def _load_tables(self) -> None:
    self.entities = self._read_rows(self.entry_db, "SELECT * FROM Entities ORDER BY id")
    self.timepoints = self._read_rows(self.entry_db, "SELECT * FROM Timepoints ORDER BY id")
    self.relationships = self._read_rows(
      self.entry_db, "SELECT * FROM Relationships ORDER BY id"
    )
    self.citations = self._read_rows(self.entry_db, "SELECT * FROM Citations ORDER BY id")
    try:
      self.build_records = self._read_rows(self.entry_db, "SELECT * FROM BuildRecords ORDER BY id")
    except sqlite3.OperationalError:
      self.build_records = []
    self.dict_entries = self._read_rows(
      self.dict_db,
      f"SELECT id, title, catalog, page, text, fields FROM {self.dict_table} ORDER BY id",
    )

    self.entity_by_id = {row["id"]: row for row in self.entities}
    self.tp_by_id = {row["id"]: row for row in self.timepoints}
    self.rel_by_id = {row["id"]: row for row in self.relationships}
    self.tps_by_entity: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for tp in self.timepoints:
      self.tps_by_entity[tp["entity_id"]].append(tp)
    self.rels_by_tp: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for rel in self.relationships:
      self.rels_by_tp[rel["subject_id"]].append(rel)
      if rel["object_id"] != rel["subject_id"]:
        self.rels_by_tp[rel["object_id"]].append(rel)
    self.cites_by_target: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for cite in self.citations:
      self.cites_by_target[(cite["target_table"], cite["target_id"])].append(cite)
    self.build_records_by_target: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for br in self.build_records:
      self.build_records_by_target[(br["target_table"], br["target_id"])].append(br)

  def _index_dictionary(self) -> None:
    self.entry_by_id = {row["id"]: row for row in self.dict_entries}
    self.entry_by_title_page: dict[tuple[str, str], dict[str, Any]] = {}
    self.entries_by_title: dict[str, list[dict[str, Any]]] = defaultdict(list)
    self.entries_by_page: dict[str, list[dict[str, Any]]] = defaultdict(list)
    self.entry_norm_text: dict[int, tuple[str, list[int]]] = {}
    for row in self.dict_entries:
      # Agent 看到的词条全文 = text（基本介绍）+ fields 各标签内容，
      # 引文常出自标签段（职源与沿革、简称等），匹配和展示都必须用拼接后的全文
      parts = [f"【基本介绍】{row['text'] or ''}"]
      try:
        fields = json.loads(row["fields"]) if row["fields"] else {}
      except (json.JSONDecodeError, TypeError):
        fields = {}
      for key, value in fields.items():
        parts.append(f"【{key}】{value}")
      row["text"] = "\n\n".join(parts)
      row.pop("fields", None)

      title = (row["title"] or "").strip()
      page = str(row["page"]).strip()
      self.entry_by_title_page.setdefault((title, page), row)
      self.entries_by_title[title].append(row)
      self.entries_by_page[page].append(row)
      self.entry_norm_text[row["id"]] = normalize_with_map(row["text"] or "")

  # ---- citation 关联与原文匹配 ----

  def _match_in_entry(self, entry_id: int, quotation: Optional[str]) -> Optional[dict[str, Any]]:
    if not quotation:
      return None
    norm_text, index_map = self.entry_norm_text[entry_id]
    raw_len = len(self.entry_by_id[entry_id]["text"] or "")
    return match_quotation(norm_text, index_map, raw_len, quotation)

  def _link_citations(self) -> None:
    """为每条 citation 计算：parsed（出处解析）、entry_id（关联条目）、match（原文区间）。"""
    self.cite_link: dict[int, dict[str, Any]] = {}
    for cite in self.citations:
      info: dict[str, Any] = {"parsed": None, "entry_id": None, "match": None}
      parsed = parse_citation(cite["citation"])
      if parsed:
        page, title = parsed
        info["parsed"] = {"page": page, "title": title}
        entry = None
        if title:
          entry = self.entry_by_title_page.get((title, page))
          if entry is None:
            candidates = self.entries_by_title.get(title, [])
            entry = candidates[0] if len(candidates) == 1 else None
        if entry is None:
          # 仅有页码（或词条名对不上）：在该页的条目中用 quotation 消歧
          hits = []
          for cand in self.entries_by_page.get(page, []):
            if title and (cand["title"] or "").strip() != title:
              continue
            m = self._match_in_entry(cand["id"], cite["quotation"])
            if m:
              hits.append((cand, m))
          if len(hits) == 1:
            entry, info["match"] = hits[0][0], hits[0][1]
        if entry is not None:
          info["entry_id"] = entry["id"]
          if info["match"] is None:
            info["match"] = self._match_in_entry(entry["id"], cite["quotation"])
      self.cite_link[cite["id"]] = info

  # ---- 实体时间线（prev/succ 链）排序与检查 ----

  def _order_timepoints(self, entity_id: int) -> tuple[list[dict[str, Any]], list[str]]:
    """按链遍历排序时间点；返回 (有序列表, 链异常描述列表)。未入链的节点附加在尾部。"""
    tps = self.tps_by_entity.get(entity_id, [])
    problems: list[str] = []
    if not tps:
      return [], problems
    by_id = {tp["id"]: tp for tp in tps}

    for tp in tps:
      for key, back in (("succ_id", "prev_id"), ("prev_id", "succ_id")):
        ref = tp[key]
        if ref is None:
          continue
        target = by_id.get(ref)
        if target is None:
          owner = self.tp_by_id.get(ref)
          where = f"属于实体 {owner['entity_id']}" if owner else "不存在"
          problems.append(f"时间点 {tp['id']} 的 {key}={ref} {where}")
        elif target[back] != tp["id"]:
          problems.append(
            f"时间点 {tp['id']} 与 {ref} 的 prev/succ 指针不互逆"
          )

    heads = [tp for tp in tps if tp["prev_id"] is None]
    if not heads:
      problems.append("没有链头（prev_id 全部非空，可能成环）")
    elif len(heads) > 1:
      problems.append(f"存在 {len(heads)} 个链头，时间线断裂为多段")

    ordered: list[dict[str, Any]] = []
    visited: set[int] = set()
    for head in heads:
      current: Optional[dict[str, Any]] = head
      while current and current["id"] not in visited:
        ordered.append(current)
        visited.add(current["id"])
        current = by_id.get(current["succ_id"]) if current["succ_id"] is not None else None
    leftovers = [tp for tp in tps if tp["id"] not in visited]
    if leftovers and heads:
      problems.append(
        "存在未接入链的时间点: " + ", ".join(str(tp["id"]) for tp in leftovers)
      )
    ordered.extend(sorted(leftovers, key=lambda tp: tp["id"]))
    return ordered, sorted(set(problems))

  # ---- 一致性检查 ----

  def _add_issue(
    self,
    issue_type: str,
    message: str,
    *,
    entity_id: Optional[int] = None,
    target_table: Optional[str] = None,
    target_id: Optional[int] = None,
    entry_ids: Optional[list[int]] = None,
  ) -> None:
    entity = self.entity_by_id.get(entity_id) if entity_id is not None else None
    self.issues.append(
      {
        "id": len(self.issues) + 1,
        "type": issue_type,
        "label": ISSUE_LABELS[issue_type],
        "message": message,
        "entity_id": entity_id,
        "entity_title": entity["title"] if entity else None,
        "target_table": target_table,
        "target_id": target_id,
        "entry_ids": entry_ids or [],
      }
    )

  def _entity_of_target(self, target_table: str, target_id: int) -> Optional[int]:
    if target_table == "Timepoints":
      tp = self.tp_by_id.get(target_id)
      return tp["entity_id"] if tp else None
    if target_table == "Relationships":
      rel = self.rel_by_id.get(target_id)
      if rel:
        tp = self.tp_by_id.get(rel["subject_id"])
        return tp["entity_id"] if tp else None
    return None

  def _check_consistency(self) -> None:
    self.issues: list[dict[str, Any]] = []

    # 引用：解析 / 条目存在性 / 原文匹配 / 冲突标记 / 悬空
    for cite in self.citations:
      target = (cite["target_table"], cite["target_id"])
      entity_id = self._entity_of_target(*target)
      link = self.cite_link[cite["id"]]
      entry_ids = [link["entry_id"]] if link["entry_id"] is not None else []
      common = {
        "entity_id": entity_id,
        "target_table": "Citations",
        "target_id": cite["id"],
        "entry_ids": entry_ids,
      }

      exists = (
        cite["target_id"] in self.tp_by_id
        if cite["target_table"] == "Timepoints"
        else cite["target_id"] in self.rel_by_id
      )
      if not exists:
        self._add_issue(
          "dangling",
          f"引用 {cite['id']} 指向不存在的 {cite['target_table']} #{cite['target_id']}",
          **common,
        )

      if link["parsed"] is None:
        self._add_issue(
          "citation_unparsed",
          f"引用 {cite['id']} 出处无法解析: {cite['citation'] or '(空)'}",
          **common,
        )
      elif link["entry_id"] is None:
        parsed = link["parsed"]
        self._add_issue(
          "citation_entry_missing",
          f"引用 {cite['id']} 指向辞典 {parsed['page']}页"
          f"“{parsed['title'] or '?'}”，但辞典库中找不到对应条目",
          **common,
        )
      elif cite["quotation"] and link["match"] is None:
        self._add_issue(
          "quotation_not_found",
          f"引用 {cite['id']} 的原文片段在辞典条目中匹配不到（疑似幻觉或 OCR 差异）",
          **common,
        )

      if cite["conflict_flag"]:
        self._add_issue(
          "conflict_flagged",
          f"引用 {cite['id']} 被标记为史料冲突" + (f"；备注：{cite['note']}" if cite["note"] else ""),
          **common,
        )

    # 关系：悬空、缺引用
    for rel in self.relationships:
      missing = [
        f"{side}={rel[side]}"
        for side in ("subject_id", "object_id")
        if rel[side] not in self.tp_by_id
      ]
      entity_id = self._entity_of_target("Relationships", rel["id"])
      if missing:
        self._add_issue(
          "dangling",
          f"关系 {rel['id']}（{rel['relation_type']}）指向不存在的时间点: " + ", ".join(missing),
          entity_id=entity_id,
          target_table="Relationships",
          target_id=rel["id"],
        )
      if not self.cites_by_target.get(("Relationships", rel["id"])):
        self._add_issue(
          "no_citation",
          f"关系 {rel['id']}（{rel['relation_type']}）没有任何引用支撑",
          entity_id=entity_id,
          target_table="Relationships",
          target_id=rel["id"],
        )

    # 时间点：占位残留、缺引用；实体：链异常
    for entity in self.entities:
      ordered, problems = self._order_timepoints(entity["id"])
      if problems:
        self._add_issue(
          "chain_broken",
          f"实体“{entity['title']}”时间线异常：" + "；".join(problems),
          entity_id=entity["id"],
          target_table="Entities",
          target_id=entity["id"],
        )
      for tp in ordered:
        # 占位残留只看 event 是否带“占位”前缀，与 time 无关
        # （time=未知 很多时候是辞典本就没给时间的合理标注，不算问题）。
        event = tp["event"] or ""
        if event == PLACEHOLDER_EVENT:
          self._add_issue(
            "placeholder_left",
            f"实体“{entity['title']}”残留占位时间点 {tp['id']}（空壳，未被真实事件填充）",
            entity_id=entity["id"],
            target_table="Timepoints",
            target_id=tp["id"],
          )
        elif event.startswith(PLACEHOLDER_EVENT):
          self._add_issue(
            "placeholder_left",
            f"实体“{entity['title']}”时间点 {tp['id']} 残留“占位”脏前缀"
            f"（真实事件已写入但未清理前缀：{event[:24]}…）",
            entity_id=entity["id"],
            target_table="Timepoints",
            target_id=tp["id"],
          )
        elif not self.cites_by_target.get(("Timepoints", tp["id"])):
          self._add_issue(
            "no_citation",
            f"实体“{entity['title']}”的时间点 {tp['id']}（{tp['time']} {tp['event']}）没有任何引用",
            entity_id=entity["id"],
            target_table="Timepoints",
            target_id=tp["id"],
          )

  # ---- 实体 <-> 辞典条目 映射；问题归属条目 ----

  def _entity_citation_ids(self, entity_id: int) -> list[int]:
    """实体名下（时间点 + 所涉关系）的全部 citation id。"""
    cite_ids: list[int] = []
    seen_rels: set[int] = set()
    for tp in self.tps_by_entity.get(entity_id, []):
      for cite in self.cites_by_target.get(("Timepoints", tp["id"]), []):
        cite_ids.append(cite["id"])
      for rel in self.rels_by_tp.get(tp["id"], []):
        if rel["id"] in seen_rels:
          continue
        seen_rels.add(rel["id"])
        for cite in self.cites_by_target.get(("Relationships", rel["id"]), []):
          cite_ids.append(cite["id"])
    return cite_ids

  def _map_entities_to_entries(self) -> None:
    # entries_of_entity: 实体名下引用涉及的全部条目（按首次出现顺序）
    # primary_entry_of_entity: 实体的「主属条目」——贡献引用最多的那个条目
    #   （平票取最早出现）。其余条目只是「借引用」关系。
    self.entries_of_entity: dict[int, list[int]] = {}
    self.primary_entry_of_entity: dict[int, Optional[int]] = {}
    self.entities_of_entry: dict[int, set[int]] = defaultdict(set)
    self.primary_entities_of_entry: dict[int, set[int]] = defaultdict(set)
    self.referenced_entities_of_entry: dict[int, set[int]] = defaultdict(set)
    for entity in self.entities:
      counts: dict[int, int] = {}
      order: list[int] = []
      for cid in self._entity_citation_ids(entity["id"]):
        eid = self.cite_link[cid]["entry_id"]
        if eid is None:
          continue
        if eid not in counts:
          counts[eid] = 0
          order.append(eid)
        counts[eid] += 1
      # 有些批跑把 citation 写成了原始史书出处（如《要录》卷85壬寅），
      # 没有《辞典》页码/词条名，导致引用无法反向归属到辞典条目。
      # 对可视化来说，实体标题与辞典词条标题完全一致时，仍应挂回同名词条；
      # 这只是展示归属兜底，不修改数据库，也不把简称/模糊匹配算作同一条。
      if not order:
        same_title_entries = self.entries_by_title.get(entity["title"], [])
        if same_title_entries:
          for entry in same_title_entries:
            order.append(entry["id"])
            counts[entry["id"]] = 0
      self.entries_of_entity[entity["id"]] = order
      for eid in order:
        self.entities_of_entry[eid].add(entity["id"])
      # 主属判定：
      #   1) 优先同名词条——若实体引用涉及的条目里有标题与实体完全同名者，
      #      它就是这个实体的「家」（即便引用大多借自别的词条）。
      #      典型：「河北兵马大元帅府」实体借用了「河北兵马元帅」词条的大量引用，
      #      但它有专属同名词条，应主属同名词条，而非借引用最多的那个。
      #   2) 否则取引用数最多的条目；平票取最早出现（order 下标越小越优先）。
      primary: Optional[int] = None
      if order:
        same_title = [
          eid for eid in order if self.entry_by_id[eid]["title"] == entity["title"]
        ]
        pool = same_title or order
        primary = max(pool, key=lambda e: (counts[e], -order.index(e)))
      self.primary_entry_of_entity[entity["id"]] = primary
      for eid in order:
        if eid == primary:
          self.primary_entities_of_entry[eid].add(entity["id"])
        else:
          self.referenced_entities_of_entry[eid].add(entity["id"])
    self.unlinked_entities = [
      e["id"] for e in self.entities if not self.entries_of_entity[e["id"]]
    ]

    # 实体级问题补挂到其关联的所有条目，便于条目徽标统计
    self.issues_of_entry: dict[int, list[dict[str, Any]]] = defaultdict(list)
    self.unlinked_issues: list[dict[str, Any]] = []
    for issue in self.issues:
      entry_ids = list(issue["entry_ids"])
      if not entry_ids and issue["entity_id"] is not None:
        entry_ids = self.entries_of_entity.get(issue["entity_id"], [])
        issue["entry_ids"] = entry_ids
      if entry_ids:
        for eid in entry_ids:
          self.issues_of_entry[eid].append(issue)
      else:
        self.unlinked_issues.append(issue)

  # ---- API 数据组装 ----

  def _serialize_build_records(self, target_table: str, target_id: int) -> list[dict[str, Any]]:
    return [
      {
        "id": br["id"],
        "source_entry": br["source_entry"],
        "source_page": br["source_page"],
        "decision": br["decision"],
        "created_at": br["created_at"],
      }
      for br in self.build_records_by_target.get((target_table, target_id), [])
    ]

  def _serialize_citation(self, cite: dict[str, Any]) -> dict[str, Any]:
    link = self.cite_link[cite["id"]]
    entry = self.entry_by_id.get(link["entry_id"]) if link["entry_id"] is not None else None
    return {
      **cite,
      "conflict_flag": bool(cite["conflict_flag"]),
      "entry_id": link["entry_id"],
      "entry_title": entry["title"] if entry else None,
      "entry_page": entry["page"] if entry else None,
      "match": link["match"],
      "parsed": link["parsed"],
      "build_records": self._serialize_build_records("Citations", cite["id"]),
    }

  def _serialize_entity(self, entity_id: int) -> dict[str, Any]:
    entity = self.entity_by_id[entity_id]
    ordered, chain_problems = self._order_timepoints(entity_id)
    tps = []
    for tp in ordered:
      rels = []
      for rel in self.rels_by_tp.get(tp["id"], []):
        role = "subject" if rel["subject_id"] == tp["id"] else "object"
        other_id = rel["object_id"] if role == "subject" else rel["subject_id"]
        other_tp = self.tp_by_id.get(other_id)
        other_entity = self.entity_by_id.get(other_tp["entity_id"]) if other_tp else None
        rels.append(
          {
            **rel,
            "role": role,
            "other_timepoint_id": other_id,
            "other_time": other_tp["time"] if other_tp else None,
            "other_entity_id": other_entity["id"] if other_entity else None,
            "other_entity_title": other_entity["title"] if other_entity else None,
            "other_entity_type": other_entity["type"] if other_entity else None,
            "citations": [
              self._serialize_citation(c)
              for c in self.cites_by_target.get(("Relationships", rel["id"]), [])
            ],
            "build_records": self._serialize_build_records("Relationships", rel["id"]),
          }
        )
      tps.append(
        {
          **tp,
          "is_placeholder": (tp["event"] or "").startswith(PLACEHOLDER_EVENT),
          "citations": [
            self._serialize_citation(c)
            for c in self.cites_by_target.get(("Timepoints", tp["id"]), [])
          ],
          "relationships": rels,
          "build_records": self._serialize_build_records("Timepoints", tp["id"]),
        }
      )
    return {
      **entity,
      "entry_ids": self.entries_of_entity.get(entity_id, []),
      "chain_problems": chain_problems,
      "timepoints": tps,
      "build_records": self._serialize_build_records("Entities", entity_id),
    }

  def _entry_highlights(self, entry_id: int) -> list[dict[str, Any]]:
    highlights = []
    for cite in self.citations:
      link = self.cite_link[cite["id"]]
      if link["entry_id"] == entry_id and link["match"]:
        highlights.append({"citation_id": cite["id"], **link["match"]})
    return highlights

  def api_meta(self) -> dict[str, Any]:
    issue_counts: dict[str, int] = defaultdict(int)
    for issue in self.issues:
      issue_counts[issue["type"]] += 1
    return {
      "entry_db": str(self.entry_db),
      "dict_db": str(self.dict_db),
      "counts": {
        "Entities": len(self.entities),
        "Timepoints": len(self.timepoints),
        "Relationships": len(self.relationships),
        "Citations": len(self.citations),
        "DictionaryEntries": len(self.dict_entries),
      },
      "issue_counts": dict(issue_counts),
      "issue_labels": ISSUE_LABELS,
      "issue_total": len(self.issues),
      "unlinked_entities": [
        {"id": eid, "title": self.entity_by_id[eid]["title"]} for eid in self.unlinked_entities
      ],
      "unlinked_issue_count": len(self.unlinked_issues),
    }

  def api_entries(self) -> list[dict[str, Any]]:
    rows = []
    for idx, entry in enumerate(self.dict_entries):
      primary_ids = self.primary_entities_of_entry.get(entry["id"], set())
      referenced_ids = self.referenced_entities_of_entry.get(entry["id"], set())
      issues = self.issues_of_entry.get(entry["id"], [])
      rows.append(
        {
          "id": entry["id"],
          # 与 agent.py 跑批时的 records_<N>_xxx.json 文件名编号一致（dict_index_list 的 1-based 顺序）
          "record_no": idx + 1,
          "title": entry["title"],
          "page": entry["page"],
          "catalog": entry["catalog"],
          # 结构库实体可能采用规范化简称，而辞典保留完整机构名，例如：
          # 实体“礼部”对应辞典词条“尚书省礼部”。前端把这些主属实体名
          # 作为检索别名，使用户可以用图谱中看到的名称直接找到原词条。
          "search_aliases": sorted(
            {
              self.entity_by_id[entity_id]["title"]
              for entity_id in primary_ids
              if self.entity_by_id[entity_id]["title"] != entry["title"]
            }
          ),
          # 徽标只数主属实体，借引用实体不计入
          "entity_count": len(primary_ids),
          "referenced_count": len(referenced_ids),
          "issue_count": len(issues),
          "issue_types": sorted({i["type"] for i in issues}),
        }
      )
    return rows

  def api_entry(self, entry_id: int) -> Optional[dict[str, Any]]:
    entry = self.entry_by_id.get(entry_id)
    if entry is None:
      return None
    primary_ids = sorted(self.primary_entities_of_entry.get(entry_id, set()))
    referenced_ids = sorted(self.referenced_entities_of_entry.get(entry_id, set()))
    return {
      "entry": entry,
      # entities = 主属本词条的实体；referenced_entities = 仅在本词条留有引用、
      # 但主属其他词条的实体（借引用），前端折叠到次要区显示
      "entities": [self._serialize_entity(eid) for eid in primary_ids],
      "referenced_entities": [self._serialize_entity(eid) for eid in referenced_ids],
      "highlights": self._entry_highlights(entry_id),
      "issues": self.issues_of_entry.get(entry_id, []),
    }

  def api_unlinked(self) -> dict[str, Any]:
    """伪条目：所有未能关联到任何辞典条目的实体与问题。"""
    return {
      "entry": None,
      "entities": [self._serialize_entity(eid) for eid in self.unlinked_entities],
      "referenced_entities": [],
      "highlights": [],
      "issues": self.unlinked_issues,
    }

  def api_entity(self, entity_id: int) -> Optional[dict[str, Any]]:
    if entity_id not in self.entity_by_id:
      return None
    detail = self._serialize_entity(entity_id)
    entries = []
    for eid in detail["entry_ids"]:
      entry = self.entry_by_id[eid]
      entries.append({**entry, "highlights": self._entry_highlights(eid)})
    return {"entity": detail, "entries": entries}

  def api_issues(self) -> list[dict[str, Any]]:
    return self.issues


# ---------------------------------------------------------------------------
# 模型缓存：按两个数据库文件的 mtime 自动失效，刷新页面即见最新数据
# ---------------------------------------------------------------------------

class ModelCache:
  def __init__(self, entry_db: Path, dict_db: Path, dict_table: str = DICT_TABLE):
    self.entry_db = entry_db
    self.dict_db = dict_db
    self.dict_table = dict_table
    self._lock = threading.Lock()
    self._model: Optional[Model] = None
    self._stamp: Optional[tuple[float, float]] = None

  def get(self) -> Model:
    stamp = (self.entry_db.stat().st_mtime, self.dict_db.stat().st_mtime)
    with self._lock:
      if self._model is None or self._stamp != stamp:
        self._model = Model(self.entry_db, self.dict_db, self.dict_table)
        self._stamp = stamp
      return self._model


# ---------------------------------------------------------------------------
# HTTP 服务
# ---------------------------------------------------------------------------

STATIC_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
}


class Handler(BaseHTTPRequestHandler):
  cache: ModelCache  # 由 main() 注入

  def log_message(self, format: str, *args: Any) -> None:
    pass  # 安静模式

  def _send_json(self, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json; charset=utf-8")
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    self.end_headers()
    self.wfile.write(body)

  def _send_static(self, name: str) -> None:
    path = (STATIC_DIR / name).resolve()
    if not str(path).startswith(str(STATIC_DIR)) or not path.is_file():
      self._send_json({"error": "not found"}, 404)
      return
    body = path.read_bytes()
    self.send_response(200)
    self.send_header("Content-Type", STATIC_TYPES.get(path.suffix, "application/octet-stream"))
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    self.end_headers()
    self.wfile.write(body)

  def do_GET(self) -> None:  # noqa: N802 (http.server 接口命名)
    path = unquote(urlparse(self.path).path)
    try:
      if path.startswith("/api/"):
        self._handle_api(path)
      elif path == "/":
        self._send_static("index.html")
      else:
        self._send_static(path.lstrip("/"))
    except BrokenPipeError:
      pass
    except Exception as exc:  # 把后端异常暴露给页面，方便排查
      self._send_json({"error": f"{type(exc).__name__}: {exc}"}, 500)

  def _handle_api(self, path: str) -> None:
    model = self.cache.get()
    if path == "/api/meta":
      self._send_json(model.api_meta())
    elif path == "/api/entries":
      self._send_json(model.api_entries())
    elif path == "/api/entry/unlinked":
      self._send_json(model.api_unlinked())
    elif (m := re.fullmatch(r"/api/entry/(\d+)", path)):
      data = model.api_entry(int(m.group(1)))
      self._send_json(data if data else {"error": "entry not found"}, 200 if data else 404)
    elif (m := re.fullmatch(r"/api/entity/(\d+)", path)):
      data = model.api_entity(int(m.group(1)))
      self._send_json(data if data else {"error": "entity not found"}, 200 if data else 404)
    elif path == "/api/issues":
      self._send_json(model.api_issues())
    else:
      self._send_json({"error": "unknown api"}, 404)


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--entry-db", type=Path, default=DEFAULT_ENTRY_DB)
  parser.add_argument("--dict-db", type=Path, default=DEFAULT_DICT_DB)
  parser.add_argument("--dict-table", default=DICT_TABLE,
                      help=f"辞典库中的条目表名（默认 {DICT_TABLE}）")
  parser.add_argument("--port", type=int, default=8642)
  args = parser.parse_args()

  if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.dict_table):
    raise SystemExit(f"非法表名: {args.dict_table}")

  for label, path in (("结果数据库", args.entry_db), ("辞典数据库", args.dict_db)):
    if not path.exists():
      raise SystemExit(f"{label}不存在: {path}")

  Handler.cache = ModelCache(
    args.entry_db.resolve(), args.dict_db.resolve(), args.dict_table
  )
  Handler.cache.get()  # 启动时预热并提前暴露数据问题

  server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
  print(f"结果数据库: {args.entry_db}")
  print(f"辞典数据库: {args.dict_db} (表 {args.dict_table})")
  print(f"审查界面: http://127.0.0.1:{args.port}/")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass


if __name__ == "__main__":
  main()
