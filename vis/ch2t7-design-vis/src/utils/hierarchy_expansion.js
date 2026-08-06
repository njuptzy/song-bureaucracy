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

export function toggleInstitutionGroupIds(currentIds, clickedId, spaceAware) {
  if (currentIds.includes(clickedId)) {
    return currentIds.filter((id) => id !== clickedId);
  }
  return spaceAware ? [...currentIds, clickedId] : [clickedId];
}

export function institutionGroupsAfterLayout({
  candidateIds,
  clickedId,
  spaceAware,
  layoutFits,
}) {
  if (!spaceAware || layoutFits || candidateIds.length <= 1) return [...candidateIds];
  return [clickedId];
}

export function collapseInstitutionGroups(expandedIds, lastExpandedId) {
  const focusId = expandedIds.includes(lastExpandedId)
    ? lastExpandedId
    : expandedIds.at(-1);
  return focusId ? [focusId] : [];
}

export function isRepeatedHierarchyPointer(previous, entityId, timeStamp, maxDelay = 650) {
  return previous?.id === entityId
    && timeStamp >= previous.timeStamp
    && timeStamp - previous.timeStamp <= maxDelay;
}
