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

/**
 * 为年号文字分配各自的真实时间段。
 *
 * 年号的起止竖线和时间段始终保留；只有当文字在自己的时间段内放不下，
 * 或会与前一个可见标签相撞时，才隐藏文字。这样短年号不会被硬挤到邻近
 * 年号上方，但用户仍能通过竖线和时间段知道该年号占据了哪一段时间。
 */
export function layoutTimelineEraLabels(eras, xOf, options = {}) {
  const fontSize = Number(options.fontSize) > 0 ? Number(options.fontSize) : 10;
  const padding = Number.isFinite(Number(options.padding))
    ? Math.max(0, Number(options.padding))
    : 2;
  const gap = Number.isFinite(Number(options.gap))
    ? Math.max(0, Number(options.gap))
    : 1.2;
  const records = normalizeTimelineEras(eras);
  const laidOut = records.map((era) => {
    const startX = Number(xOf(era.start));
    const endX = Number(xOf(era.end + 1));
    const validGeometry = Number.isFinite(startX) && Number.isFinite(endX);
    const safeStartX = validGeometry ? startX : 0;
    const safeEndX = validGeometry ? Math.max(startX, endX) : 0;
    const slotWidth = Math.max(0, safeEndX - safeStartX);
    const labelWidth = Math.max(fontSize, era.name.length * fontSize);
    const labelX = safeStartX + slotWidth / 2;
    const fitsSlot = validGeometry && slotWidth >= labelWidth + padding * 2;
    return {
      ...era,
      startX: safeStartX,
      endX: safeEndX,
      slotWidth,
      labelWidth,
      labelX,
      labelVisible: fitsSlot,
      labelHiddenReason: fitsSlot ? null : "short-range",
    };
  });

  let previousRight = Number.NEGATIVE_INFINITY;
  for (const item of laidOut) {
    if (!item.labelVisible) continue;
    const left = item.labelX - item.labelWidth / 2;
    const right = item.labelX + item.labelWidth / 2;
    if (left < previousRight + gap) {
      item.labelVisible = false;
      item.labelHiddenReason = "collision";
      continue;
    }
    previousRight = right;
  }
  return laidOut;
}
