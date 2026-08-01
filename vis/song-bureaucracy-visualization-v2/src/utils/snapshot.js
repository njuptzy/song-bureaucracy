const SNAPSHOT_TIME_TYPES = new Set(["exact", "range", "bounded"]);
import { classifyExistenceEffect } from "../../../shared/entity_lifecycle.js";

function effectiveYear(event) {
  if (!SNAPSHOT_TIME_TYPES.has(event?.timeType) || event?.yearStart == null) return null;
  if (event.timeType === "bounded") return event.yearEnd ?? event.yearStart;
  return event.yearStart;
}

function isDated(event) {
  return effectiveYear(event) != null;
}

function chainDepth(event, eventById) {
  let depth = 0;
  let current = event;
  const seen = new Set();
  while (current?.prevId != null && !seen.has(current.prevId)) {
    seen.add(current.prevId);
    const previous = eventById.get(current.prevId);
    if (!previous || previous.entityId !== event.entityId) break;
    depth += 1;
    current = previous;
  }
  return depth;
}

function compareEvents(a, b, eventById) {
  return (effectiveYear(a) - effectiveYear(b))
    || ((a.yearEnd ?? a.yearStart) - (b.yearEnd ?? b.yearStart))
    || (chainDepth(a, eventById) - chainDepth(b, eventById))
    || (a.id - b.id);
}

function compareKnownChainOrder(a, b, eventById) {
  if (!a || !b || a.id === b.id || a.entityId !== b.entityId) return 0;
  let current = b;
  const seen = new Set();
  while (current?.prevId != null && !seen.has(current.prevId)) {
    seen.add(current.prevId);
    current = eventById.get(current.prevId);
    if (!current || current.entityId !== b.entityId) break;
    if (current.id === a.id) return -1;
  }
  current = a;
  seen.clear();
  while (current?.prevId != null && !seen.has(current.prevId)) {
    seen.add(current.prevId);
    current = eventById.get(current.prevId);
    if (!current || current.entityId !== a.entityId) break;
    if (current.id === b.id) return 1;
  }
  return 0;
}

function relationEffectiveYear(relation, eventById) {
  const endpointYears = [relation.subjectId, relation.objectId]
    .map((id) => eventById.get(id))
    .filter(isDated)
    .map(effectiveYear);
  return endpointYears.length ? Math.max(...endpointYears) : null;
}

function relationStateKey(relation) {
  if (relation.type === "上下级机构") return `hierarchy:${relation.objectEntityId}`;
  if (relation.type === "编制隶属") return `staff:${relation.objectEntityId}`;
  return `${relation.type}:${relation.subjectEntityId}:${relation.objectEntityId}`;
}

function relationPresenceEvidence(dataset, year, eventById) {
  const byEntity = new Map();
  const add = (entityId, evidenceYear, eventId) => {
    if (entityId == null || evidenceYear == null || evidenceYear > year) return;
    if (!byEntity.has(entityId)) byEntity.set(entityId, []);
    byEntity.get(entityId).push({
      effectiveYear: evidenceYear,
      event: eventById.get(eventId) || null,
    });
  };
  for (const relation of dataset.relations) {
    if (!["上下级机构", "编制隶属"].includes(relation.type)) continue;
    const evidenceYear = relationEffectiveYear(relation, eventById);
    add(relation.subjectEntityId, evidenceYear, relation.subjectId);
    add(relation.objectEntityId, evidenceYear, relation.objectId);
  }
  return byEntity;
}

export function buildYearSnapshot(dataset, year) {
  const entityById = new Map(dataset.entities.map((entity) => [entity.id, entity]));
  const eventById = new Map(dataset.events.map((event) => [event.id, event]));
  const eventsByEntity = new Map();
  for (const event of dataset.events) {
    if (!eventsByEntity.has(event.entityId)) eventsByEntity.set(event.entityId, []);
    eventsByEntity.get(event.entityId).push(event);
  }

  const presenceEvidenceByEntity = relationPresenceEvidence(dataset, year, eventById);
  const currentEventByEntity = new Map();
  for (const [entityId, entity] of entityById) {
    const eligible = (eventsByEntity.get(entityId) || [])
      .filter((event) => isDated(event) && effectiveYear(event) <= year)
      .map((event) => ({ kind: "event", effectiveYear: effectiveYear(event), event }));
    const relationEvidence = (presenceEvidenceByEntity.get(entityId) || [])
      .map((evidence) => ({ kind: "relation", ...evidence }));
    const evidenceTimeline = [...eligible, ...relationEvidence].sort((a, b) => (
      // 与8050保持同一规则：实体链已明确先后的关系证据，不能因模糊纪年
      // 取区间上界而越过后继废罢事件，错误复活旧机构。
      compareKnownChainOrder(a.event, b.event, eventById)
      || a.effectiveYear - b.effectiveYear
      || (a.kind === b.kind ? 0 : a.kind === "relation" ? -1 : 1)
      || (a.kind === "event" && b.kind === "event" ? compareEvents(a.event, b.event, eventById) : 0)
    ));
    let exists = null;
    let currentEvent = null;
    for (const evidence of evidenceTimeline) {
      if (evidence.kind === "relation") {
        exists = true;
        if (!currentEvent && evidence.event) currentEvent = evidence.event;
        continue;
      }
      const { event } = evidence;
      const effect = classifyExistenceEffect(event, entity);
      if (effect === "activate") exists = true;
      else if (effect === "deactivate") exists = false;
      else if (effect === "ignore") {
        currentEvent = event;
        continue;
      } else if (exists == null && event.timeType !== "bounded") exists = true;
      currentEvent = event;
    }
    if (exists) currentEventByEntity.set(entityId, currentEvent);
  }

  const entityIds = new Set(currentEventByEntity.keys());
  const relationStates = new Map();
  for (const relation of dataset.relations) {
    if (!entityIds.has(relation.subjectEntityId) || !entityIds.has(relation.objectEntityId)) continue;
    const effectiveYear = relationEffectiveYear(relation, eventById);
    if (effectiveYear == null || effectiveYear > year) continue;
    const key = relationStateKey(relation);
    const current = relationStates.get(key);
    if (!current || effectiveYear > current.effectiveYear) {
      relationStates.set(key, { effectiveYear, relations: [relation] });
    } else if (effectiveYear === current.effectiveYear) {
      current.relations.push(relation);
    }
  }
  const relations = [...relationStates.values()].flatMap(({ effectiveYear, relations: items }) => (
    items.map((relation) => ({ ...relation, effectiveYear }))
  ));
  const dedupedRelations = new Map();
  for (const relation of relations) {
    const key = relation.type === "上下级机构"
      ? `${relation.type}:${relation.subjectEntityId}:${relation.objectEntityId}`
      : relation.type === "编制隶属"
        ? `${relation.type}:${relation.subjectEntityId}:${relation.objectEntityId}:${relation.staffQuota || ""}:${relation.staffType || ""}`
        : `${relation.type}:${relation.id}`;
    const current = dedupedRelations.get(key);
    if (!current || relation.id > current.id) dedupedRelations.set(key, relation);
  }

  return {
    year,
    currentEventByEntity,
    entityIds,
    entities: dataset.entities.filter((entity) => entityIds.has(entity.id)),
    relations: [...dedupedRelations.values()],
  };
}
