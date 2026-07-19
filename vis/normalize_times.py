#!/usr/bin/env python3
"""Create a visualization DB with a minimal normalized time table.

The source database is never modified.  The main timeline only needs a
Gregorian year; lunar month/day values are retained for ordering events within
the same year, while the original Chinese date remains in Timepoints.time.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "vis/data/song_bureaucracy_best.db"
DEFAULT_OUTPUT = ROOT / "vis/data/song_bureaucracy_visualization.db"
DEFAULT_REPORT = ROOT / "vis/time-normalization-report.md"

NORMALIZATION_VERSION = "1.0.0"
REFERENCE_SOURCES = {
    "year_era_table": (
        "教育部《重编国语辞典修订本》附录：中国历代年号表（宋，960—1279）",
        "https://dict.revised.moe.edu.tw/appendix.jsp?ID=3&page=5&ver=5",
    ),
    "calendar_reference": (
        "中央研究院数位文化中心：两千年中西历转换",
        "https://sinocal.sinica.edu.tw/",
    ),
}


# Only the first and last Gregorian years are needed.  Month/day conversion to
# the Gregorian calendar is intentionally out of scope.
ERA_YEARS: dict[str, tuple[int, int]] = {
    "建隆": (960, 963),
    "乾德": (963, 968),
    "开宝": (968, 976),
    "太平兴国": (976, 984),
    "雍熙": (984, 987),
    "端拱": (988, 989),
    "淳化": (990, 994),
    "至道": (995, 997),
    "咸平": (998, 1003),
    "景德": (1004, 1007),
    "大中祥符": (1008, 1016),
    "天禧": (1017, 1021),
    "乾兴": (1022, 1022),
    "天圣": (1023, 1032),
    "明道": (1032, 1033),
    "景祐": (1034, 1038),
    "宝元": (1038, 1040),
    "康定": (1040, 1041),
    "庆历": (1041, 1048),
    "皇祐": (1049, 1054),
    "至和": (1054, 1056),
    "嘉祐": (1056, 1063),
    "治平": (1064, 1067),
    "熙宁": (1068, 1077),
    "元丰": (1078, 1085),
    "元祐": (1086, 1094),
    "绍圣": (1094, 1098),
    "元符": (1098, 1100),
    "建中靖国": (1101, 1101),
    "崇宁": (1102, 1106),
    "大观": (1107, 1110),
    "政和": (1111, 1118),
    "重和": (1118, 1118),
    "宣和": (1119, 1125),
    "靖康": (1126, 1127),
    "建炎": (1127, 1130),
    "绍兴": (1131, 1162),
    "隆兴": (1163, 1164),
    "乾道": (1165, 1173),
    "淳熙": (1174, 1189),
    "绍熙": (1190, 1194),
    "庆元": (1195, 1200),
    "嘉泰": (1201, 1204),
    "开禧": (1205, 1207),
    "嘉定": (1208, 1224),
    "宝庆": (1225, 1227),
    "绍定": (1228, 1233),
    "端平": (1234, 1236),
    "嘉熙": (1237, 1240),
    "淳祐": (1241, 1252),
    "宝祐": (1253, 1258),
    "开庆": (1259, 1259),
    "景定": (1260, 1264),
    "咸淳": (1265, 1274),
    "德祐": (1275, 1276),
    "景炎": (1276, 1278),
    "祥兴": (1278, 1279),
}

ERA_PATTERN = re.compile(
    "|".join(re.escape(name) for name in sorted(ERA_YEARS, key=len, reverse=True))
)
NUMBER_CHARS = "元〇零一二三四五六七八九十廿卅两"
YEAR_PATTERN = re.compile(rf"([{NUMBER_CHARS}]+)年")
MONTH_PATTERN = re.compile(
    rf"(?P<leap>闰)?(?P<month>正|冬|腊|[{NUMBER_CHARS}]+)月"
)
DAY_PATTERN = re.compile(rf"(?P<day>[初{NUMBER_CHARS}]+)日")
GANZHI_PATTERN = re.compile(r"([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])")

SONG_MARKERS = (
    "宋代",
    "北宋",
    "南宋",
    "两宋",
    "宋初",
    "宋前期",
    "宋末",
    "太宗朝",
    "真宗朝",
    "仁宗朝",
    "英宗",
    "神宗朝",
    "哲宗朝",
    "徽宗朝",
    "孝宗朝",
    "宁宗",
)
PRE_SONG_MARKERS = (
    "西汉",
    "秦",
    "魏",
    "晋",
    "北周",
    "隋",
    "唐",
    "五代",
    "后唐",
    "后晋",
    "后汉",
    "南唐",
    "黄初",
    "开元",
    "大历",
    "贞元",
    "长安",
)
KNOWN_INVALID_TIMES = {"北宋东京", "南宋官品", "南宋宣庆二年"}


@dataclass(frozen=True)
class Endpoint:
    era: str
    era_year: int
    year: int
    month: int | None
    is_leap_month: int
    day: int | None
    month_text: str | None
    day_text: str | None


@dataclass(frozen=True)
class Normalized:
    year_start: int | None
    year_end: int | None
    month: int | None
    is_leap_month: int
    day: int | None
    end_month: int | None
    end_is_leap_month: int
    end_day: int | None
    month_text: str | None
    day_text: str | None
    end_month_text: str | None
    end_day_text: str | None
    sort_order: int | None
    time_type: str
    parse_note: str | None = None


def chinese_number(text: str) -> int | None:
    """Convert the small Chinese numbers used in reign years and dates."""
    text = text.strip().replace("初", "").replace("两", "二")
    if not text:
        return None
    if text in {"元", "正"}:
        return 1
    text = text.replace("〇", "零")
    digits = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9}
    if text.startswith("卅"):
        return 30 + (chinese_number(text[1:]) or 0)
    if text.startswith("廿"):
        return 20 + (chinese_number(text[1:]) or 0)
    if "十" in text:
        left, right = text.split("十", 1)
        tens = digits.get(left, 1) if left else 1
        ones = digits.get(right, 0) if right else 0
        return tens * 10 + ones
    if all(ch in digits for ch in text):
        value = 0
        for ch in text:
            value = value * 10 + digits[ch]
        return value
    return None


def parse_month_day(text: str) -> tuple[int | None, int, int | None, str | None, str | None]:
    month_match = MONTH_PATTERN.search(text)
    if not month_match:
        # A few source dates name an intercalary month without saying which
        # month (for example “闰月丁卯”).  Preserve the information but do not
        # invent a numeric month for sorting.
        if "闰月" in text:
            ganzhi_match = GANZHI_PATTERN.search(text.split("闰月", 1)[1])
            return None, 1, None, "闰月", ganzhi_match.group(1) if ganzhi_match else None
        return None, 0, None, None, None

    raw_month = month_match.group("month")
    if raw_month == "正":
        month = 1
    elif raw_month == "冬":
        month = 11
    elif raw_month == "腊":
        month = 12
    else:
        month = chinese_number(raw_month)

    suffix = text[month_match.end():]
    day_match = DAY_PATTERN.search(suffix)
    if day_match:
        raw_day = day_match.group("day")
        day = chinese_number(raw_day)
        day_text = raw_day + "日"
    else:
        ganzhi_match = GANZHI_PATTERN.search(suffix)
        day = None
        day_text = ganzhi_match.group(1) if ganzhi_match else None

    return (
        month,
        1 if month_match.group("leap") else 0,
        day,
        ("闰" if month_match.group("leap") else "") + raw_month + "月",
        day_text,
    )


def parse_endpoint(text: str, default_era: str | None = None) -> Endpoint | None:
    era_matches = list(ERA_PATTERN.finditer(text))
    era = era_matches[-1].group(0) if era_matches else default_era
    if era is None:
        return None

    search_start = era_matches[-1].end() if era_matches else 0
    year_match = YEAR_PATTERN.search(text, search_start)
    if not year_match:
        return None
    era_year = chinese_number(year_match.group(1))
    if era_year is None:
        return None

    start, end = ERA_YEARS[era]
    year = start + era_year - 1
    if not start <= year <= end:
        return None

    month, leap, day, month_text, day_text = parse_month_day(text[year_match.end():])
    return Endpoint(era, era_year, year, month, leap, day, month_text, day_text)


def range_split(raw: str) -> tuple[str, str] | None:
    """Find a range delimiter without confusing it with era names like 至和."""
    for index, char in enumerate(raw):
        if char != "至":
            continue
        if "年" in raw[:index] and "年" in raw[index + 1:]:
            return raw[:index], raw[index + 1:]
    return None


def make_sort_order(year: int, month: int | None, leap: int, day: int | None) -> int:
    # month*2 + leap keeps regular fourth month < leap fourth month < fifth month.
    month_order = (month or 0) * 2 + (leap if month else 0)
    return year * 100_000 + month_order * 100 + (day or 0)


def normalize_time(raw: str) -> Normalized:
    raw = raw.strip()
    if raw in KNOWN_INVALID_TIMES:
        return Normalized(None, None, None, 0, None, None, 0, None,
                          None, None, None, None, None, "unresolved",
                          "字段内容不是可直接使用的宋代纪年")

    split = range_split(raw)
    if split:
        left_text, right_text = split
        left = parse_endpoint(left_text)
        right = parse_endpoint(right_text, left.era if left else None)
        if left and right and left.year <= right.year:
            return Normalized(
                left.year, right.year,
                left.month, left.is_leap_month, left.day,
                right.month, right.is_leap_month, right.day,
                left.month_text, left.day_text, right.month_text, right.day_text,
                make_sort_order(left.year, left.month, left.is_leap_month, left.day),
                "range",
            )

    endpoint = parse_endpoint(raw)
    if endpoint:
        return Normalized(
            endpoint.year, endpoint.year,
            endpoint.month, endpoint.is_leap_month, endpoint.day,
            endpoint.month, endpoint.is_leap_month, endpoint.day,
            endpoint.month_text, endpoint.day_text,
            endpoint.month_text, endpoint.day_text,
            make_sort_order(endpoint.year, endpoint.month, endpoint.is_leap_month, endpoint.day),
            "exact",
        )

    era_match = ERA_PATTERN.search(raw)
    if era_match:
        era = era_match.group(0)
        if any(word in raw for word in ("后", "前", "以后", "以前")):
            return Normalized(None, None, None, 0, None, None, 0, None,
                              None, None, None, None, None, "undated",
                              f"包含相对时间词，保留原文：{era}")
        start, end = ERA_YEARS[era]
        return Normalized(start, end, None, 0, None, None, 0, None,
                          None, None, None, None,
                          make_sort_order(start, None, 0, None), "range",
                          f"仅识别到年号范围：{era}")

    if any(marker in raw for marker in SONG_MARKERS):
        return Normalized(None, None, None, 0, None, None, 0, None,
                          None, None, None, None, None, "undated")
    if any(marker in raw for marker in PRE_SONG_MARKERS):
        return Normalized(None, None, None, 0, None, None, 0, None,
                          None, None, None, None, None, "pre_song")
    return Normalized(None, None, None, 0, None, None, 0, None,
                      None, None, None, None, None, "unresolved")


def create_working_copy(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.chmod(0o644)
        output.unlink()
    source_conn = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    output_conn = sqlite3.connect(output)
    try:
        source_conn.backup(output_conn)
    finally:
        output_conn.close()
        source_conn.close()


def write_normalized_times(output: Path, source: Path) -> dict[str, int]:
    conn = sqlite3.connect(output)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DROP TABLE IF EXISTS NormalizedTimes")
        conn.execute("DROP TABLE IF EXISTS TimeNormalizationMetadata")
        conn.execute(
            """
            CREATE TABLE NormalizedTimes (
                timepoint_id INTEGER PRIMARY KEY,
                raw_time TEXT NOT NULL,
                year_start INTEGER,
                year_end INTEGER,
                month INTEGER,
                is_leap_month INTEGER NOT NULL DEFAULT 0,
                day INTEGER,
                end_month INTEGER,
                end_is_leap_month INTEGER NOT NULL DEFAULT 0,
                end_day INTEGER,
                month_text TEXT,
                day_text TEXT,
                end_month_text TEXT,
                end_day_text TEXT,
                sort_order INTEGER,
                time_type TEXT NOT NULL CHECK (
                    time_type IN ('exact', 'range', 'undated', 'pre_song', 'unresolved')
                ),
                parse_note TEXT,
                FOREIGN KEY (timepoint_id) REFERENCES Timepoints(id)
            )
            """
        )
        rows = conn.execute("SELECT id, time FROM Timepoints ORDER BY id").fetchall()
        counts: dict[str, int] = {}
        for timepoint_id, raw_time in rows:
            item = normalize_time(raw_time)
            counts[item.time_type] = counts.get(item.time_type, 0) + 1
            conn.execute(
                """
                INSERT INTO NormalizedTimes (
                    timepoint_id, raw_time, year_start, year_end,
                    month, is_leap_month, day,
                    end_month, end_is_leap_month, end_day,
                    month_text, day_text, end_month_text, end_day_text,
                    sort_order, time_type, parse_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timepoint_id, raw_time, item.year_start, item.year_end,
                    item.month, item.is_leap_month, item.day,
                    item.end_month, item.end_is_leap_month, item.end_day,
                    item.month_text, item.day_text,
                    item.end_month_text, item.end_day_text,
                    item.sort_order, item.time_type, item.parse_note,
                ),
            )
        conn.execute(
            "CREATE INDEX idx_normalized_times_year ON NormalizedTimes(year_start, sort_order)"
        )
        conn.execute(
            "CREATE INDEX idx_normalized_times_type ON NormalizedTimes(time_type)"
        )
        conn.execute(
            """
            CREATE TABLE TimeNormalizationMetadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        metadata = {
            "normalization_version": NORMALIZATION_VERSION,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_database": str(source),
            "rule_summary": (
                "年号换算公元年；农历月、闰月、日仅用于同年排序；"
                "不进行农历到公历月日转换；原始 Timepoints.time 保持不变"
            ),
            "reference_year_era_table": " | ".join(REFERENCE_SOURCES["year_era_table"]),
            "reference_calendar": " | ".join(REFERENCE_SOURCES["calendar_reference"]),
            "calendar_reference_usage": (
                "仅作为历法转换边界参考；当前版本未进行农历月日到公历日期转换"
            ),
        }
        conn.executemany(
            "INSERT INTO TimeNormalizationMetadata(key, value) VALUES (?, ?)",
            metadata.items(),
        )
        conn.commit()
        return counts
    finally:
        conn.close()


def write_report(output: Path, report: Path, counts: dict[str, int]) -> None:
    conn = sqlite3.connect(output)
    try:
        total = conn.execute("SELECT COUNT(*) FROM NormalizedTimes").fetchone()[0]
        unresolved = conn.execute(
            """
            SELECT timepoint_id, raw_time, COALESCE(parse_note, '')
            FROM NormalizedTimes
            WHERE time_type = 'unresolved'
            ORDER BY timepoint_id
            """
        ).fetchall()
    finally:
        conn.close()

    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 时间标准化运行报告",
        "",
        f"- 版本：`{NORMALIZATION_VERSION}`",
        f"- 生成时间（UTC）：`{datetime.now(timezone.utc).isoformat(timespec='seconds')}`",
        f"- 工作数据库：`{output}`",
        f"- 时间节点总数：{total}",
        "",
        "## 转换结果",
        "",
        "| 类型 | 数量 |",
        "| --- | ---: |",
    ]
    for key in ("exact", "range", "undated", "pre_song", "unresolved"):
        lines.append(f"| `{key}` | {counts.get(key, 0)} |")
    lines.extend([
        "",
        "## 待复核项",
        "",
        "| Timepoint ID | 原始时间 | 说明 |",
        "| ---: | --- | --- |",
    ])
    for timepoint_id, raw_time, note in unresolved:
        lines.append(f"| {timepoint_id} | {raw_time} | {note} |")
    lines.extend([
        "",
        "## 使用资料",
        "",
        f"- [{REFERENCE_SOURCES['year_era_table'][0]}]({REFERENCE_SOURCES['year_era_table'][1]})",
        f"- [{REFERENCE_SOURCES['calendar_reference'][0]}]({REFERENCE_SOURCES['calendar_reference'][1]})",
        "",
        "当前版本未进行农历月日到公历月日转换。",
        "",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")


def validate(output: Path) -> None:
    conn = sqlite3.connect(output)
    try:
        timepoints = conn.execute("SELECT COUNT(*) FROM Timepoints").fetchone()[0]
        normalized = conn.execute("SELECT COUNT(*) FROM NormalizedTimes").fetchone()[0]
        if timepoints != normalized:
            raise RuntimeError(f"时间点数量不一致: Timepoints={timepoints}, NormalizedTimes={normalized}")
        bad_ranges = conn.execute(
            "SELECT COUNT(*) FROM NormalizedTimes WHERE year_start > year_end"
        ).fetchone()[0]
        if bad_ranges:
            raise RuntimeError(f"发现 {bad_ranges} 条开始年晚于结束年的记录")
        bad_months = conn.execute(
            "SELECT COUNT(*) FROM NormalizedTimes WHERE month NOT BETWEEN 1 AND 12"
        ).fetchone()[0]
        bad_days = conn.execute(
            "SELECT COUNT(*) FROM NormalizedTimes WHERE day NOT BETWEEN 1 AND 30"
        ).fetchone()[0]
        if bad_months or bad_days:
            raise RuntimeError(f"非法月日: months={bad_months}, days={bad_days}")
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"数据库完整性检查失败: {integrity}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    if source == output:
        raise ValueError("输出数据库不能覆盖源数据库")

    create_working_copy(source, output)
    counts = write_normalized_times(output, source)
    validate(output)
    write_report(output, args.report.resolve(), counts)

    print(f"源数据库: {source}")
    print(f"可视化工作库: {output}")
    print(f"运行报告: {args.report.resolve()}")
    print("转换结果:")
    for key in ("exact", "range", "undated", "pre_song", "unresolved"):
        print(f"  {key}: {counts.get(key, 0)}")


if __name__ == "__main__":
    main()
