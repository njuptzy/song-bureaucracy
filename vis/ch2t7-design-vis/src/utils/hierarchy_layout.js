export function anchorBranchToGroup(groupCenterX, groupTreeX, focusTreeX) {
  return groupCenterX - (focusTreeX - groupTreeX);
}

export function virtualBusRange(sourceX, targetXs) {
  const xs = [sourceX, ...targetXs];
  return [Math.min(...xs), Math.max(...xs)];
}
