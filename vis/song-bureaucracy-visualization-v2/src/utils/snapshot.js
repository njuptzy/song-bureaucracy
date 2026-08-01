const SNAPSHOT_TIME_TYPES = new Set(["exact", "range"]);
const TERMINAL_EVENT_TYPES = new Set(["abolished", "merged"]);

function isDated(event) {
  return SNAPSHOT_TIME_TYPES.has(event?.timeType) && event?.yearStart != null;
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
  return (a.yearStart - b.yearStart)
    || ((a.sortOrder ?? 0) - (b.sortOrder ?? 0))
    || (chainDepth(a, eventById) - chainDepth(b, eventById))
    || (a.id - b.id);
}

function relationEffectiveYear(relation, eventById) {
  const endpointYears = [relation.subjectId, relation.objectId]
    .map((id) => eventById.get(id))
    .filter(isDated)
    .map((event) => event.yearStart);
  return endpointYears.length ? Math.max(...endpointYears) : null;
}

function relationStateKey(relation) {
  if (relation.type === "上下级机构") return `hierarchy:${relation.objectEntityId}`;
  if (relation.type === "编制隶属") return `staff:${relation.objectEntityId}`;
  return `${relation.type}:${relation.subjectEntityId}:${relation.objectEntityId}`;
}

export function buildYearSnapshot(dataset, year) {
  const eventById = new Map(dataset.events.map((event) => [event.id, event]));
  const eventsByEntity = new Map();
  for (const event of dataset.events) {
    if (!eventsByEntity.has(event.entityId)) eventsByEntity.set(event.entityId, []);
    eventsByEntity.get(event.entityId).push(event);
  }

  const currentEventByEntity = new Map();
  for (const [entityId, events] of eventsByEntity) {
    const state = events
      .filter((event) => isDated(event) && event.yearStart <= year)
      .sort((a, b) => compareEvents(a, b, eventById))
      .at(-1);
    if (state && !TERMINAL_EVENT_TYPES.has(state.eventType)) {
      currentEventByEntity.set(entityId, state);
    }
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

  return {
    year,
    currentEventByEntity,
    entityIds,
    entities: dataset.entities.filter((entity) => entityIds.has(entity.id)),
    relations,
  };
}
