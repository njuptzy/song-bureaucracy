export const NODE_CHANGE_INDICATOR_GEOMETRY = Object.freeze({
  gap: 4,
  minimumRadius: 7.5,
  maximumRadius: 11.5,
  estimatedGlyphWidth: 4.6,
  horizontalPadding: 5,
});

export function nodeChangeIndicatorItems(summary) {
  return [
    summary?.past ? {
      kind: "past",
      label: `-${summary.past.distance}`,
      title: `最近过去变化：${summary.past.year}年（距今${summary.past.distance}年）`,
    } : null,
    summary?.future ? {
      kind: "future",
      label: `+${summary.future.distance}`,
      title: `最近未来变化：${summary.future.year}年（${summary.future.distance}年后）`,
    } : null,
  ].filter(Boolean);
}

export function nodeChangeIndicatorLayout(items) {
  let cursorX = 0;
  let maximumRadius = 0;
  const positionedItems = (items || []).map((item) => {
    const estimatedDiameter = item.label.length * NODE_CHANGE_INDICATOR_GEOMETRY.estimatedGlyphWidth
      + NODE_CHANGE_INDICATOR_GEOMETRY.horizontalPadding;
    const radius = Math.max(
      NODE_CHANGE_INDICATOR_GEOMETRY.minimumRadius,
      Math.min(NODE_CHANGE_INDICATOR_GEOMETRY.maximumRadius, estimatedDiameter / 2),
    );
    const positioned = { ...item, centerX: cursorX + radius, radius };
    cursorX += radius * 2 + NODE_CHANGE_INDICATOR_GEOMETRY.gap;
    maximumRadius = Math.max(maximumRadius, radius);
    return positioned;
  });
  return {
    width: Math.max(0, cursorX - (positionedItems.length ? NODE_CHANGE_INDICATOR_GEOMETRY.gap : 0)),
    height: maximumRadius * 2,
    centerY: maximumRadius,
    items: positionedItems.map((item) => ({ ...item, centerY: maximumRadius })),
  };
}

export function nodeChangeIndicatorAriaLabel(title, summary, isVirtual = false) {
  const parts = [];
  if (summary?.past) {
    parts.push(`最近过去变化在${summary.past.year}年，相距${summary.past.distance}年`);
  }
  if (summary?.future) {
    parts.push(`最近未来变化在${summary.future.year}年，相距${summary.future.distance}年`);
  }
  return `${title}${isVirtual ? "组内" : ""}前后结构变化：${parts.join("；")}`;
}
