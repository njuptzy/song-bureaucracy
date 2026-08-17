export const HIERARCHY_HEADER_LAYOUT = Object.freeze({
  settingsY: 31,
  settingsHeight: 36,
  controlWidth: 126,
  controlGap: 12,
  spaceControlX: 1470,
  animationControlX: 1608,
  viewRowY: 80,
  evolutionViewX: 1398.5,
  evolutionViewLabelX: 1461.4,
});

export function hierarchyAnimationShouldRun({
  enabled,
  viewMode,
  hasSvg,
  reduceMotion = false,
} = {}) {
  return Boolean(enabled && viewMode === "hierarchy" && hasSvg && !reduceMotion);
}
