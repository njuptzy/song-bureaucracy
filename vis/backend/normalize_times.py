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


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "vis/data/song_bureaucracy_best.db"
DEFAULT_OUTPUT = ROOT / "vis/data/song_bureaucracy_visualization.db"
DEFAULT_REPORT = ROOT / "vis/reports/time-normalization-report.md"

NORMALIZATION_VERSION = "1.2.0"
REFERENCE_SOURCES = {
    "year_era_table": (
        "教育部《重编国语辞典修订本》附录：中国历代年号表（宋，960—1279）",
        "https://dict.revised.moe.edu.tw/appendix.jsp?ID=3&page=4&la=0&powerMode=0&SN=%E5%AE%8B%20(%E8%A5%BF%E5%85%83960%EF%BD%9E1279)",
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

# 可审计的宽时间表达。这里的 range 表示“史料只把事件约束在该区间内”，
# 不是断言事件或制度在整个区间持续存在。帝王在位期按公元年粒度记录，
# 即位/退位发生的边界年允许相邻区间重叠，避免伪造月日精度。
NAMED_TIME_RANGES: dict[str, tuple[int, int, str]] = {
    # 朝代范围
    "两宋": (960, 1279, "两宋朝代范围"),
    "北宋": (960, 1127, "北宋朝代范围"),
    "北宋时期": (960, 1127, "北宋朝代范围"),
    "北宋（未载具体年月）": (960, 1127, "未载具体年月，仅能约束在北宋"),
    "南宋": (1127, 1279, "南宋朝代范围"),
    "南宋时": (1127, 1279, "南宋朝代范围"),
    "南宋时期": (1127, 1279, "南宋朝代范围"),
    "南宋（未载具体年月）": (1127, 1279, "未载具体年月，仅能约束在南宋"),
    "南宋临安府（未载具体年月）": (1127, 1279, "未载具体年月，仅能约束在南宋"),
    "宋代": (960, 1279, "宋代朝代范围"),
    "宋代千户以上县": (960, 1279, "时间字段含宋代制度描述，仅能约束在宋代"),
    "宋代逐县置一员": (960, 1279, "时间字段含宋代制度描述，仅能约束在宋代"),
    "宋代（县分十等）": (960, 1279, "时间字段含宋代制度描述，仅能约束在宋代"),
    "宋代（未载具体年月）": (960, 1279, "未载具体年月，仅能约束在宋代"),

    # 帝王在位期与复合年号期
    "北宋仁宗朝": (1022, 1063, "仁宗在位期，按公元年粒度"),
    "北宋哲宗朝": (1085, 1100, "哲宗在位期，按公元年粒度"),
    "北宋太宗、真宗亲王时期": (976, 1022, "太宗至真宗在位期，按公元年粒度"),
    "北宋太祖、太宗朝": (960, 997, "太祖至太宗在位期，按公元年粒度"),
    "北宋太祖太宗朝": (960, 997, "太祖至太宗在位期，按公元年粒度"),
    "北宋徽宗朝": (1100, 1125, "徽宗在位期，按公元年粒度"),
    "徽宗朝": (1100, 1125, "徽宗在位期，按公元年粒度"),
    "北宋真宗朝": (997, 1022, "真宗在位期，按公元年粒度"),
    "真宗朝": (997, 1022, "真宗在位期，按公元年粒度"),
    "北宋神宗朝": (1067, 1085, "神宗在位期，按公元年粒度"),
    "北宋熙丰间": (1068, 1085, "熙宁、元丰复合时期"),
    "北宋熙丰时期": (1068, 1085, "熙宁、元丰复合时期"),

    # 有明确朝代上下文的相对时间。边界年保留重叠以反映年粒度。
    "元祐后": (1094, 1127, "元祐以后，约束在北宋"),
    "元祐后（约北宋哲宗元祐年间及以后）": (1094, 1127, "元祐以后，约束在北宋"),
    "北宋元丰后": (1085, 1127, "元丰以后，约束在北宋"),
    "北宋太宗朝后": (997, 1127, "太宗朝以后，约束在北宋"),
    "北宋徽宗朝后": (1125, 1127, "徽宗朝以后，约束在北宋"),
    "北宋景德后": (1007, 1127, "景德以后，约束在北宋"),
    "北宋熙宁后": (1077, 1127, "熙宁以后，约束在北宋"),
    "北宋真宗朝后": (1022, 1127, "真宗朝以后，约束在北宋"),
    "北宋神宗朝起": (1067, 1127, "自神宗朝起，约束在北宋"),
    "北宋英宗即位前": (960, 1063, "英宗即位以前，约束在北宋"),
    "北宋英宗即位后": (1063, 1127, "英宗即位以后，约束在北宋"),
    "北宋英宗治平后": (1067, 1127, "治平以后，约束在北宋"),
    "南宋乾道以后": (1173, 1279, "乾道以后，约束在南宋"),
    "南宋孝宗朝以后": (1189, 1279, "孝宗朝以后，约束在南宋"),
    "南宋开禧后": (1207, 1279, "开禧以后，约束在南宋"),
    "南宋绍兴后": (1162, 1279, "绍兴以后，约束在南宋"),
    "南宋绍熙后": (1194, 1279, "绍熙以后，约束在南宋"),
    "南宋隆兴后": (1164, 1279, "隆兴以后，约束在南宋"),
    "隆兴以后": (1164, 1279, "隆兴以后，约束在南宋"),
    "天圣前": (960, 1023, "天圣以前，约束在北宋"),
    "政和前": (960, 1111, "政和以前，约束在北宋"),
}

NAMED_EXACT_YEARS: dict[str, tuple[int, str]] = {
    "北宋英宗即位": (1063, "英宗即位年，当前仅精确到公元年"),
}


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


def make_year_range(
    start: int,
    end: int,
    note: str | None = None,
    *,
    time_type: str = "range",
) -> Normalized:
    return Normalized(
        start, end, None, 0, None, None, 0, None,
        None, None, None, None,
        make_sort_order(start, None, 0, None), time_type, note,
    )


def invalid_era_year(raw: str) -> tuple[str, int] | None:
    """Return an explicitly written reign year when it exceeds that era."""
    for era_match in ERA_PATTERN.finditer(raw):
        year_match = YEAR_PATTERN.search(raw, era_match.end())
        if not year_match:
            continue
        # Do not attach a year that belongs to a later era in the same string.
        next_era = ERA_PATTERN.search(raw, era_match.end())
        if next_era and next_era.start() < year_match.start():
            continue
        era_year = chinese_number(year_match.group(1))
        if era_year is None:
            continue
        start, end = ERA_YEARS[era_match.group(0)]
        if not start <= start + era_year - 1 <= end:
            return era_match.group(0), era_year
    return None


def normalize_time(raw: str) -> Normalized:
    raw = raw.strip()
    if raw in KNOWN_INVALID_TIMES:
        return Normalized(None, None, None, 0, None, None, 0, None,
                          None, None, None, None, None, "unresolved",
                          "字段内容不是可直接使用的宋代纪年")

    named_exact = NAMED_EXACT_YEARS.get(raw)
    if named_exact:
        year, note = named_exact
        return Normalized(
            year, year, None, 0, None, None, 0, None,
            None, None, None, None,
            make_sort_order(year, None, 0, None), "exact", note,
        )

    named_range = NAMED_TIME_RANGES.get(raw)
    if named_range:
        return make_year_range(*named_range, time_type="bounded")

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

    invalid = invalid_era_year(raw)
    if invalid:
        era, era_year = invalid
        return Normalized(
            None, None, None, 0, None, None, 0, None,
            None, None, None, None, None, "unresolved",
            f"年号年次超出有效范围：{era}{era_year}年",
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
                          make_sort_order(start, None, 0, None), "bounded",
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


def normalized_values(timepoint_id: int, raw_time: str, item: Normalized) -> tuple:
    return (
        timepoint_id, raw_time, item.year_start, item.year_end,
        item.month, item.is_leap_month, item.day,
        item.end_month, item.end_is_leap_month, item.end_day,
        item.month_text, item.day_text,
        item.end_month_text, item.end_day_text,
        item.sort_order, item.time_type, item.parse_note,
    )


def create_normalized_times_table(conn: sqlite3.Connection) -> None:
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
                time_type IN (
                    'exact', 'range', 'bounded', 'undated', 'pre_song', 'unresolved'
                )
            ),
            parse_note TEXT,
            FOREIGN KEY (timepoint_id) REFERENCES Timepoints(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX idx_normalized_times_year ON NormalizedTimes(year_start, sort_order)"
    )
    conn.execute(
        "CREATE INDEX idx_normalized_times_type ON NormalizedTimes(time_type)"
    )


def ensure_bounded_schema(conn: sqlite3.Connection) -> None:
    """Upgrade the derived table when an older CHECK rejects ``bounded``."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'NormalizedTimes'"
    ).fetchone()
    if row and "bounded" in (row[0] or ""):
        return
    conn.execute("DROP TABLE IF EXISTS NormalizedTimes")
    create_normalized_times_table(conn)


def write_normalized_times(output: Path, source: Path) -> dict[str, int]:
    conn = sqlite3.connect(output)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DROP TABLE IF EXISTS NormalizedTimes")
        conn.execute("DROP TABLE IF EXISTS TimeNormalizationMetadata")
        create_normalized_times_table(conn)
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
                normalized_values(timepoint_id, raw_time, item),
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
                "年号换算公元年；原文明示起止的时间为range；朝代、帝王在位期、"
                "复合年号期及有明确上下文的相对时间为bounded，仅表示时间边界，"
                "不表示全程持续；非法年号年次不退化为年号范围；"
                "农历月、闰月、日仅用于同年排序；原始 Timepoints.time 保持不变"
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


def refresh_normalized_times(output: Path) -> tuple[dict[str, int], dict[tuple[str, str], int], int]:
    """在现有工作库内原子刷新 NormalizedTimes，不复制或重建其他业务表。"""
    conn = sqlite3.connect(output)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("BEGIN IMMEDIATE")
        ensure_bounded_schema(conn)
        rows = conn.execute(
            """
            SELECT
                t.id, COALESCE(t.time, ''), COALESCE(n.time_type, 'missing'),
                n.raw_time, n.year_start, n.year_end,
                n.month, n.is_leap_month, n.day,
                n.end_month, n.end_is_leap_month, n.end_day,
                n.month_text, n.day_text, n.end_month_text, n.end_day_text,
                n.sort_order, n.time_type, n.parse_note
            FROM Timepoints t
            LEFT JOIN NormalizedTimes n ON n.timepoint_id = t.id
            ORDER BY t.id
            """
        ).fetchall()
        counts: dict[str, int] = {}
        transitions: dict[tuple[str, str], int] = {}
        changed = 0
        for row in rows:
            timepoint_id, raw_time, old_type = row[:3]
            item = normalize_time(raw_time)
            counts[item.time_type] = counts.get(item.time_type, 0) + 1
            transition = (old_type, item.time_type)
            transitions[transition] = transitions.get(transition, 0) + 1
            new_values = normalized_values(timepoint_id, raw_time, item)
            old_values = (timepoint_id, *row[3:])
            if old_values != new_values:
                changed += 1
            conn.execute(
                """
                INSERT INTO NormalizedTimes (
                    timepoint_id, raw_time, year_start, year_end,
                    month, is_leap_month, day,
                    end_month, end_is_leap_month, end_day,
                    month_text, day_text, end_month_text, end_day_text,
                    sort_order, time_type, parse_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(timepoint_id) DO UPDATE SET
                    raw_time=excluded.raw_time,
                    year_start=excluded.year_start,
                    year_end=excluded.year_end,
                    month=excluded.month,
                    is_leap_month=excluded.is_leap_month,
                    day=excluded.day,
                    end_month=excluded.end_month,
                    end_is_leap_month=excluded.end_is_leap_month,
                    end_day=excluded.end_day,
                    month_text=excluded.month_text,
                    day_text=excluded.day_text,
                    end_month_text=excluded.end_month_text,
                    end_day_text=excluded.end_day_text,
                    sort_order=excluded.sort_order,
                    time_type=excluded.time_type,
                    parse_note=excluded.parse_note
                """,
                new_values,
            )
        metadata_updates = {
            "normalization_version": NORMALIZATION_VERSION,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rule_summary": (
                "年号换算公元年；原文明示起止的时间为range；朝代、帝王在位期、"
                "复合年号期及有明确上下文的相对时间为bounded，仅表示时间边界，"
                "不表示全程持续；非法年号年次不退化为年号范围；"
                "农历月、闰月、日仅用于同年排序；原始 Timepoints.time 保持不变"
            ),
            "reference_year_era_table": " | ".join(REFERENCE_SOURCES["year_era_table"]),
        }
        conn.executemany(
            """
            INSERT INTO TimeNormalizationMetadata(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            metadata_updates.items(),
        )
        conn.commit()
        return counts, transitions, changed
    except Exception:
        conn.rollback()
        raise
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
    for key in ("exact", "range", "bounded", "undated", "pre_song", "unresolved"):
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
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="仅原子刷新现有工作库的 NormalizedTimes，不复制源库或重建业务表",
    )
    args = parser.parse_args()

    output = args.output.resolve()
    if args.in_place:
        if not output.exists():
            raise FileNotFoundError(output)
        counts, transitions, changed = refresh_normalized_times(output)
        validate(output)
        write_report(output, args.report.resolve(), counts)
        print(f"已原子刷新可视化工作库: {output}")
        print(f"实际变化的标准化记录: {changed}")
        print("类型迁移:")
        for (old_type, new_type), count in sorted(transitions.items()):
            print(f"  {old_type} -> {new_type}: {count}")
        print("转换结果:")
        for key in ("exact", "range", "bounded", "undated", "pre_song", "unresolved"):
            print(f"  {key}: {counts.get(key, 0)}")
        return

    source = args.source.resolve()
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
    for key in ("exact", "range", "bounded", "undated", "pre_song", "unresolved"):
        print(f"  {key}: {counts.get(key, 0)}")


if __name__ == "__main__":
    main()
