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

export function horizontalRangesFit(ranges, viewportLeft, viewportRight, gap = 18) {
  const ordered = [...ranges].sort((a, b) => a.left - b.left);
  if (ordered.some((range) => range.left < viewportLeft || range.right > viewportRight)) {
    return false;
  }
  return ordered.every((range, index) => (
    index === 0 || range.left - ordered[index - 1].right >= gap
  ));
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

function matrixAttributes(matrix) {
  return {
    a: matrix.a,
    b: matrix.b,
    c: matrix.c,
    d: matrix.d,
    e: matrix.e,
    f: matrix.f,
  };
}

export function relativeAffineMatrix(rootMatrix, elementMatrix) {
  if (!elementMatrix) return null;
  if (!rootMatrix) return matrixAttributes(elementMatrix);
  const determinant = rootMatrix.a * rootMatrix.d - rootMatrix.b * rootMatrix.c;
  if (!Number.isFinite(determinant) || Math.abs(determinant) < 1e-12) {
    return matrixAttributes(elementMatrix);
  }
  const inverse = {
    a: rootMatrix.d / determinant,
    b: -rootMatrix.b / determinant,
    c: -rootMatrix.c / determinant,
    d: rootMatrix.a / determinant,
    e: (rootMatrix.c * rootMatrix.f - rootMatrix.d * rootMatrix.e) / determinant,
    f: (rootMatrix.b * rootMatrix.e - rootMatrix.a * rootMatrix.f) / determinant,
  };
  return {
    a: inverse.a * elementMatrix.a + inverse.c * elementMatrix.b,
    b: inverse.b * elementMatrix.a + inverse.d * elementMatrix.b,
    c: inverse.a * elementMatrix.c + inverse.c * elementMatrix.d,
    d: inverse.b * elementMatrix.c + inverse.d * elementMatrix.d,
    e: inverse.a * elementMatrix.e + inverse.c * elementMatrix.f + inverse.e,
    f: inverse.b * elementMatrix.e + inverse.d * elementMatrix.f + inverse.f,
  };
}
