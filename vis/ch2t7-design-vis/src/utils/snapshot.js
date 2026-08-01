const SNAPSHOT_TIME_TYPES = new Set(["exact", "range"]);
const RESTORED_WORDS = ["复置", "复设", "恢复", "复称", "复旧", "再置", "重置", "重新设置"];
const TERMINATED_WORDS = ["不复置", "不再置", "未复置", "不复设", "未复设", "罢", "废", "解散", "撤销", "并入", "合并", "并归"];

function isDated(timepoint) {
  return SNAPSHOT_TIME_TYPES.has(timepoint?.time_type) && timepoint?.year_start != null;
}

function chainDepth(timepoint, byId) {
  let depth = 0;
  let current = timepoint;
  const seen = new Set();
  while (current?.prev_id != null && !seen.has(current.prev_id)) {
    seen.add(current.prev_id);
    const previous = byId.get(current.prev_id);
    if (!previous || previous.entity_id !== timepoint.entity_id) break;
    depth += 1;
    current = previous;
  }
  return depth;
}

function compareTimepoints(a, b, byId) {
  return (a.year_start - b.year_start)
    || ((a.year_end ?? a.year_start) - (b.year_end ?? b.year_start))
    || (chainDepth(a, byId) - chainDepth(b, byId))
    || (a.id - b.id);
}

function stateTerminated(timepoint) {
  const event = timepoint?.event || "";
  if (RESTORED_WORDS.some((word) => event.includes(word))) return false;
  return TERMINATED_WORDS.some((word) => event.includes(word));
}

function relationEffectiveYear(state, timepointById) {
  if (state.effective_year != null) return state.effective_year;
  const endpointYears = [state.subject_timepoint_id, state.object_timepoint_id]
    .map((id) => timepointById.get(id))
    .filter(isDated)
    .map((timepoint) => timepoint.year_start);
  return endpointYears.length ? Math.max(...endpointYears) : null;
}

function selectRelationStates(edges, year, entityIds, timepointById, keyForEdge) {
  const candidatesByKey = new Map();
  for (const edge of edges) {
    const endpointsPresent = edge.parent != null
      ? entityIds.has(edge.parent) && entityIds.has(edge.child)
      : entityIds.has(edge.org) && entityIds.has(edge.official);
    if (!endpointsPresent) continue;
    const fallbackYears = (edge.periods || []).map((period) => period.start).filter(Number.isFinite);
    const states = edge.states?.length
      ? edge.states
      : fallbackYears.map((effectiveYear) => ({ id: edge.id, effective_year: effectiveYear }));
    for (const state of states) {
      const effectiveYear = relationEffectiveYear(state, timepointById);
      if (effectiveYear == null || effectiveYear > year) continue;
      const key = keyForEdge(edge);
      const current = candidatesByKey.get(key);
      if (!current || effectiveYear > current.effectiveYear) {
        candidatesByKey.set(key, { effectiveYear, items: [{ edge, state }] });
      } else if (effectiveYear === current.effectiveYear) {
        current.items.push({ edge, state });
      }
    }
  }
  const selected = [...candidatesByKey.values()].flatMap(({ effectiveYear, items }) => items.map(({ edge, state }) => ({
    ...edge,
    id: state.id,
    effective_year: effectiveYear,
  })));
  const deduped = new Map();
  for (const edge of selected) {
    const key = edge.parent != null
      ? `${edge.parent}:${edge.child}`
      : `${edge.org}:${edge.official}:${edge.staff_quota || ""}:${edge.staff_type || ""}`;
    if (!deduped.has(key) || edge.id > deduped.get(key).id) deduped.set(key, edge);
  }
  return [...deduped.values()];
}

export function buildYearSnapshot(data, year) {
  const timepointById = new Map();
  const timepointsByEntity = new Map();
  const currentTimepointByEntity = new Map();
  for (const [entityIdText, timepoints] of Object.entries(data.timepoints || {})) {
    const entityId = Number(entityIdText);
    const normalized = timepoints.map((timepoint) => ({ ...timepoint, entity_id: entityId }));
    timepointsByEntity.set(entityId, normalized);
    normalized.forEach((timepoint) => timepointById.set(timepoint.id, timepoint));
  }
  for (const [entityId, timepoints] of timepointsByEntity) {
    const eligible = timepoints
      .filter((timepoint) => isDated(timepoint) && timepoint.year_start <= year)
      .sort((a, b) => compareTimepoints(a, b, timepointById));
    const state = eligible.at(-1);
    if (state && !stateTerminated(state)) currentTimepointByEntity.set(entityId, state);
  }
  const entityIds = new Set(currentTimepointByEntity.keys());
  const hierarchyEdges = selectRelationStates(
    data.hierarchyEdges || [],
    year,
    entityIds,
    timepointById,
    (edge) => `hierarchy:${edge.child}`
  );
  const staffEdges = selectRelationStates(
    data.staffEdges || [],
    year,
    entityIds,
    timepointById,
    (edge) => `staff:${edge.official}`
  );
  return { year, currentTimepointByEntity, entityIds, hierarchyEdges, staffEdges };
}
