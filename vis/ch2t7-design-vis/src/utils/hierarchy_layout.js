export function anchorBranchToGroup(groupCenterX, groupTreeX, focusTreeX) {
  return groupCenterX - (focusTreeX - groupTreeX);
}

export function virtualBusRange(sourceX, targetXs) {
  const xs = [sourceX, ...targetXs];
  return [Math.min(...xs), Math.max(...xs)];
}

export function fitRangeShift(contentLeft, contentRight, viewportLeft, viewportRight) {
  const contentWidth = contentRight - contentLeft;
  const viewportWidth = viewportRight - viewportLeft;
  if (contentWidth > viewportWidth) {
    return (viewportLeft + viewportRight - contentLeft - contentRight) / 2;
  }
  if (contentLeft < viewportLeft) return viewportLeft - contentLeft;
  if (contentRight > viewportRight) return viewportRight - contentRight;
  return 0;
}
