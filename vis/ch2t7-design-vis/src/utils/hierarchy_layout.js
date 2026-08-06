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

export function panScrollbarGeometry({
  viewportSize,
  contentSize,
  minPan,
  maxPan,
  currentPan,
  minThumbSize = 42,
}) {
  const panRange = Math.max(0, maxPan - minPan);
  const enabled = contentSize > viewportSize && panRange > 0;
  if (!enabled) {
    return { enabled: false, thumbSize: viewportSize, thumbTravel: 0, thumbOffset: 0 };
  }
  const thumbSize = Math.max(
    minThumbSize,
    Math.min(viewportSize, viewportSize * viewportSize / contentSize)
  );
  const thumbTravel = viewportSize - thumbSize;
  const clampedPan = Math.max(minPan, Math.min(maxPan, currentPan));
  const thumbOffset = (maxPan - clampedPan) / panRange * thumbTravel;
  return { enabled, thumbSize, thumbTravel, thumbOffset };
}

export function panFromScrollbarOffset(offset, thumbTravel, minPan, maxPan) {
  if (thumbTravel <= 0) return maxPan;
  const clampedOffset = Math.max(0, Math.min(thumbTravel, offset));
  return maxPan - clampedOffset / thumbTravel * (maxPan - minPan);
}
