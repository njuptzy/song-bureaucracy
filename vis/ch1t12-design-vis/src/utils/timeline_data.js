function finiteNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

/**
 * 只接受服务端提供的年号记录，不从 SVG 文字或时间点原文猜测年号。
 * 服务端数据来自 vis/backend/normalize_times.py 的 ERA_YEARS。
 */
export function normalizeTimelineEras(eras) {
  if (!Array.isArray(eras)) return [];
  return eras
    .map((era) => ({
      name: String(era?.name ?? "").trim(),
      start: finiteNumber(era?.start),
      end: finiteNumber(era?.end),
      phase: String(era?.phase ?? "").trim(),
    }))
    .filter((era) => era.name && era.start != null && era.end != null && era.start <= era.end)
    .sort((left, right) => left.start - right.start || left.end - right.end || left.name.localeCompare(right.name, "zh-CN"));
}

export function timelineEraForYear(year, eras) {
  const numericYear = finiteNumber(year);
  if (numericYear == null) return null;
  const matches = normalizeTimelineEras(eras)
    .filter((era) => numericYear >= era.start && numericYear <= era.end);
  return matches.at(-1) || null;
}

export function buildTimelineYearTicks(yearMin, yearMax, step = 10) {
  const min = Math.ceil(Number(yearMin));
  const max = Math.floor(Number(yearMax));
  const interval = Math.max(1, Math.floor(Number(step) || 10));
  if (!Number.isFinite(min) || !Number.isFinite(max) || min > max) return [];
  const ticks = new Set([min, max]);
  for (let year = Math.ceil(min / interval) * interval; year <= max; year += interval) {
    ticks.add(year);
  }
  return [...ticks].sort((left, right) => left - right);
}

