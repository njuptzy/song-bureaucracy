#!/usr/bin/env python3
"""从表格化结果建辞典库（按编组）。

用法: python3 build_dictionary_db_2t4.py [1|2t4|5t7|11t12]   (默认 2t4)

输入:
  data/ocr-results/<编组名>-表格化结果.json   (条目内容: name/text/各属性)
  data/ocr-results/<编组名>-表格化结果.meta.json (逐条元数据: page/h1/h2/h3/status, 与结果位置对齐)
输出:
  data/database/song_bureaucracy_dictionary_ch<编组>.db, 表 chapter<编组>
  schema 与 song_bureaucracy_dictionary.db 的 chapter8t10 完全一致。

meta 中 status 说明: ok=正文目录匹配; placeholder=目录有正文未匹配(text 为空);
not_in_catalog=正文有目录未收; from_surname/fuzzy=别称或模糊匹配。全部入库,
status 记入 fields.__status__ 供下游参考。
"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROFILES = {
    "1": {"out": "第一编"},
    "2t4": {"out": "第二至四编"},
    "5t7": {"out": "第五至七编"},
    "11t12": {"out": "第十一至十二编"},
}

SCHEMA = """
CREATE TABLE {table} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    catalog TEXT NOT NULL,
    page TEXT NOT NULL,
    text TEXT NOT NULL,
    fields TEXT
);
"""

CATALOG_PREFIX = "宋代官制辞典/I.职官条目分类目录"


def fix_ch1_chenfei(entries, meta):
    """修复第一编 p14 的嵌入切分错误。

    目录 OCR 把“宸妃”误识为“寝妃”；正文 OCR 中宸妃的定义和
    “职源与沿革”又被粘到上一条“贵人”。原始页块明确依次为：
    贵人品阶 -> 宸妃定义 -> 宸妃职源与沿革 -> 宝林。
    """
    noble = entries[92]
    chenfei = entries[93]
    chenfei_meta = meta[93]
    assert noble == {
        "name": "贵人",
        "职源": "东汉光武帝建武元年(25)始置（见《后汉书·光烈阴皇后纪》）。宋真宗大中祥符二年(1009)特置贵人。",
        "品阶": "属内命妇末阶，无视品。宸妃 内命妇，特置封号。仁宗用以追赠生母、真宗顺容李氏而设。",
        "职源与沿革": "唐高宗时已有此名号（《唐会要》卷3《内职杂录》）。宋仁宗明道元年（1032）二月特置（见《长编》卷111）。",
        "text": "皇帝妾之位号。",
    }
    assert chenfei == {"name": "寝妃", "text": "", "_placeholder": True}
    assert chenfei_meta["name"] == "寝妃" and chenfei_meta["status"] == "placeholder"

    noble["品阶"] = "属内命妇末阶，无视品。"
    history = noble.pop("职源与沿革")
    chenfei.clear()
    chenfei.update({
        "name": "宸妃",
        "职源与沿革": history,
        "text": "内命妇，特置封号。仁宗用以追赠生母、真宗顺容李氏而设。",
    })
    chenfei_meta.update({
        "name": "宸妃",
        "body_page": "14",
        "status": "ok",
    })


def main() -> int:
    profile_name = sys.argv[1] if len(sys.argv) > 1 else "2t4"
    if profile_name not in PROFILES:
        raise SystemExit(f"未知编组 {profile_name!r}，可选: {sorted(PROFILES)}")
    out = PROFILES[profile_name]["out"]
    table = f"chapter{profile_name}"
    result_json = os.path.join(ROOT, f"data/ocr-results/{out}-表格化结果.json")
    meta_json = os.path.join(ROOT, f"data/ocr-results/{out}-表格化结果.meta.json")
    db_path = os.path.join(ROOT, f"data/database/song_bureaucracy_dictionary_ch{profile_name}.db")

    with open(result_json, encoding="utf-8") as f:
        entries = json.load(f)
    with open(meta_json, encoding="utf-8") as f:
        meta = json.load(f)
    if profile_name == "1":
        fix_ch1_chenfei(entries, meta)
    assert len(entries) == len(meta), "结果与 meta 条数不一致"
    for i, (e, m) in enumerate(zip(entries, meta)):
        assert e["name"] == m["name"], f"第 {i} 条 name 不对齐: {e['name']} vs {m['name']}"

    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA.format(table=table))

    rows = []
    for e, m in zip(entries, meta):
        parts = [CATALOG_PREFIX, m["h1"]]
        if m.get("h2"):
            parts.append(m["h2"])
        if m.get("h3"):
            parts.append(m["h3"])
        catalog = "/".join(parts)

        fields = {k: v for k, v in e.items() if k not in ("name", "text") and v}
        if m["status"] != "ok":
            fields["__status__"] = m["status"]

        rows.append((
            e["name"],
            catalog,
            str(m["page"]),
            e.get("text", ""),
            json.dumps(fields, ensure_ascii=False) if fields else None,
        ))

    conn.executemany(
        f"INSERT INTO {table} (title, catalog, page, text, fields) VALUES (?,?,?,?,?)",
        rows,
    )
    conn.commit()

    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    empty = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE text=''").fetchone()[0]
    print(f"写入 {db_path}: {n} 条 (其中空 text {empty} 条)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
