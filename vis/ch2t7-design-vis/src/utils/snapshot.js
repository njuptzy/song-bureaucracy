const SNAPSHOT_TIME_TYPES = new Set(["exact", "range", "bounded"]);
import { classifyExistenceEffect } from "../../../shared/entity_lifecycle.js";

export { classifyExistenceEffect } from "../../../shared/entity_lifecycle.js";

function effectiveYear(timepoint) {
  if (!SNAPSHOT_TIME_TYPES.has(timepoint?.time_type) || timepoint?.year_start == null) return null;
  // “元祐初/熙宁末”等 bounded 纪年只知道事件落在一个区间内；到上界年后
  // 才能确定事件已经发生，避免把存废变化提前到区间起点。
  if (timepoint.time_type === "bounded") return timepoint.year_end ?? timepoint.year_start;
  return timepoint.year_start;
}

function isDated(timepoint) {
  return effectiveYear(timepoint) != null;
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
  return (effectiveYear(a) - effectiveYear(b))
    || ((a.year_end ?? a.year_start) - (b.year_end ?? b.year_start))
    || (chainDepth(a, byId) - chainDepth(b, byId))
    || (a.id - b.id);
}

function compareKnownChainOrder(a, b, byId) {
  if (!a || !b || a.id === b.id || a.entity_id !== b.entity_id) return 0;
  let current = b;
  const seen = new Set();
  while (current?.prev_id != null && !seen.has(current.prev_id)) {
    seen.add(current.prev_id);
    current = byId.get(current.prev_id);
    if (!current || current.entity_id !== b.entity_id) break;
    if (current.id === a.id) return -1;
  }
  current = a;
  seen.clear();
  while (current?.prev_id != null && !seen.has(current.prev_id)) {
    seen.add(current.prev_id);
    current = byId.get(current.prev_id);
    if (!current || current.entity_id !== a.entity_id) break;
    if (current.id === b.id) return 1;
  }
  return 0;
}

function relationEffectiveYear(state, timepointById) {
  if (state.effective_year != null) return state.effective_year;
  const endpointYears = [state.subject_timepoint_id, state.object_timepoint_id]
    .map((id) => timepointById.get(id))
    .filter(isDated)
    .map(effectiveYear);
  return endpointYears.length ? Math.max(...endpointYears) : null;
}

function relationPresenceEvidence(data, year, timepointById) {
  const byEntity = new Map();
  const add = (entityId, evidenceYear, timepointId) => {
    if (entityId == null || evidenceYear == null || evidenceYear > year) return;
    if (!byEntity.has(entityId)) byEntity.set(entityId, []);
    byEntity.get(entityId).push({
      effectiveYear: evidenceYear,
      timepoint: timepointById.get(timepointId) || null,
    });
  };
  for (const edge of [...(data.hierarchyEdges || []), ...(data.staffEdges || [])]) {
    const subjectEntityId = edge.parent ?? edge.org;
    const objectEntityId = edge.child ?? edge.official;
    if (edge.states?.length) {
      for (const state of edge.states) {
        const evidenceYear = relationEffectiveYear(state, timepointById);
        add(subjectEntityId, evidenceYear, state.subject_timepoint_id);
        add(objectEntityId, evidenceYear, state.object_timepoint_id);
      }
    } else {
      for (const period of edge.periods || []) {
        add(subjectEntityId, period.start, null);
        add(objectEntityId, period.start, null);
      }
    }
  }
  return byEntity;
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
  const entityById = new Map((data.entities || []).map((entity) => [entity.id, entity]));
  const timepointById = new Map();
  const timepointsByEntity = new Map();
  const currentTimepointByEntity = new Map();
  for (const [entityIdText, timepoints] of Object.entries(data.timepoints || {})) {
    const entityId = Number(entityIdText);
    const normalized = timepoints.map((timepoint) => ({ ...timepoint, entity_id: entityId }));
    timepointsByEntity.set(entityId, normalized);
    normalized.forEach((timepoint) => timepointById.set(timepoint.id, timepoint));
  }
  const presenceEvidenceByEntity = relationPresenceEvidence(data, year, timepointById);
  for (const [entityId, entity] of entityById) {
    const eligible = (timepointsByEntity.get(entityId) || [])
      .filter((timepoint) => isDated(timepoint) && effectiveYear(timepoint) <= year)
      .map((timepoint) => ({ kind: "timepoint", effectiveYear: effectiveYear(timepoint), timepoint }));
    const relationEvidence = (presenceEvidenceByEntity.get(entityId) || [])
      .map((evidence) => ({ kind: "relation", ...evidence }));
    const evidenceTimeline = [...eligible, ...relationEvidence].sort((a, b) => (
      // 关系证据挂在实体自身的时间点上；若链已明确先后，就不能让一个宽泛
      // “熙宁间”关系按区间上界排到其后继的明确废罢事件之后，造成旧机构复活。
      compareKnownChainOrder(a.timepoint, b.timepoint, timepointById)
      || a.effectiveYear - b.effectiveYear
      // 同年关系先证明“这一年存在”，自身的明确罢废事件随后覆盖它。
      || (a.kind === b.kind ? 0 : a.kind === "relation" ? -1 : 1)
      || (a.kind === "timepoint" && b.kind === "timepoint"
        ? compareTimepoints(a.timepoint, b.timepoint, timepointById)
        : 0)
    ));
    let exists = null;
    let currentState = null;
    for (const evidence of evidenceTimeline) {
      if (evidence.kind === "relation") {
        exists = true;
        if (!currentState && evidence.timepoint) currentState = evidence.timepoint;
        continue;
      }
      const { timepoint } = evidence;
      const effect = classifyExistenceEffect(timepoint, entity);
      if (effect === "activate") exists = true;
      else if (effect === "deactivate") exists = false;
      else if (effect === "ignore") {
        currentState = timepoint;
        continue;
      }
      // bounded 普通记载只能说明“事件发生在某段内”，不足以单独确定某一年的存在；
      // 但其中明确的设置/罢废转换仍会在区间上界年生效。
      else if (exists == null && timepoint.time_type !== "bounded") exists = true;
      currentState = timepoint;
    }
    if (exists) currentTimepointByEntity.set(entityId, currentState);
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
