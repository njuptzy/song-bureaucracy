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
 * 年号的起止竖线和时间段始终保留；文字是否显示只由持续年数决定，
 * 不因年号字数改变阈值。达到阈值但文字过长时，在自己的时间格内截成省略号，
 * 这样短年号不会被硬挤到邻近年号上方。
 */
export function layoutTimelineEraLabels(eras, xOf, options = {}) {
  const minYears = Number(options.minYears) > 0 ? Number(options.minYears) : 5;
  const fontSize = Number(options.fontSize) > 0 ? Number(options.fontSize) : 10;
  const padding = Number.isFinite(Number(options.padding))
    ? Math.max(0, Number(options.padding))
    : 0;
  const records = normalizeTimelineEras(eras);
  const laidOut = records.map((era) => {
    const startX = Number(xOf(era.start));
    const endX = Number(xOf(era.end + 1));
    const validGeometry = Number.isFinite(startX) && Number.isFinite(endX);
    const safeStartX = validGeometry ? startX : 0;
    const safeEndX = validGeometry ? Math.max(startX, endX) : 0;
    const slotWidth = Math.max(0, safeEndX - safeStartX);
    const durationYears = Math.max(0, era.end - era.start + 1);
    return {
      ...era,
      startX: safeStartX,
      endX: safeEndX,
      slotWidth,
      durationYears,
      labelVisible: validGeometry && durationYears >= minYears,
      labelHiddenReason: validGeometry && durationYears >= minYears ? null : "short-range",
    };
  });

  for (let index = 0; index < laidOut.length; index += 1) {
    const item = laidOut[index];
    const nextStartX = laidOut[index + 1]?.startX ?? item.endX;
    const labelEndX = Math.min(item.endX, nextStartX);
    const labelSlotWidth = Math.max(0, labelEndX - item.startX - padding * 2);
    const maxCharacters = Math.floor(labelSlotWidth / fontSize);
    const codePoints = Array.from(item.name);
    let labelText = item.name;
    if (maxCharacters <= 0) {
      labelText = "";
    } else if (codePoints.length > maxCharacters) {
      labelText = maxCharacters === 1
        ? "…"
        : `${codePoints.slice(0, maxCharacters - 1).join("")}…`;
    }
    item.labelSlotStartX = item.startX + padding;
    item.labelSlotEndX = Math.max(item.labelSlotStartX, labelEndX - padding);
    item.labelSlotWidth = labelSlotWidth;
    item.labelX = item.startX + Math.max(0, labelEndX - item.startX) / 2;
    item.labelText = labelText;
    item.labelWidth = labelText.length * fontSize;
    if (item.labelVisible && !labelText) {
      item.labelVisible = false;
      item.labelHiddenReason = "no-room";
    }
  }
  return laidOut;
}
