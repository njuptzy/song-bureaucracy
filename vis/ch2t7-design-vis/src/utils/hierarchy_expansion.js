export function mergeExpansionPaths(currentIds, nextPath, spaceAware) {
  if (!spaceAware) return [...nextPath];
  return [...new Set([...currentIds, ...nextPath])];
}

export function removeExpandedSubtree(currentIds, subtreeIds) {
  const removed = new Set(subtreeIds);
  return currentIds.filter((id) => !removed.has(id));
}

export function expansionAfterLayout({
  candidateIds,
  fallbackPath,
  spaceAware,
  layoutFits,
}) {
  if (!spaceAware || layoutFits) return [...candidateIds];
  const fallback = new Set(fallbackPath);
  const combinesIndependentBranch = candidateIds.some((id) => !fallback.has(id));
  return combinesIndependentBranch ? [...fallbackPath] : [...candidateIds];
}

export function expansionAnchorId(expandedIds, spaceAware) {
  return spaceAware ? null : expandedIds[0] ?? null;
}
