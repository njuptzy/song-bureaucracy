import { resolveHierarchyContext } from "./hierarchy_navigation.js";

function finiteYear(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.round(numeric) : null;
}

function normalizeId(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : value ?? null;
}

function eventYear(event) {
  return finiteYear(
    event?.effectiveYear
      ?? event?.effective_year
      ?? event?.eventYear
      ?? event?.year,
  );
}

export function formatYearOffset(entryYear, eventYearValue) {
  const entry = finiteYear(entryYear);
  const event = finiteYear(eventYearValue);
  if (entry == null || event == null) return "距入口年份未定";
  const offset = event - entry;
  if (offset === 0) return "同年";
  return `${offset > 0 ? "+" : ""}${offset}年`;
}

export function yearOffset(entryYear, eventYearValue) {
  const entry = finiteYear(entryYear);
  const event = finiteYear(eventYearValue);
  return entry == null || event == null ? null : event - entry;
}

export function evolutionSelectionComparison(selectedItem, entryYear) {
  if (!selectedItem?.item) return null;
  if (selectedItem.kind === "timepoint") {
    const year = eventYear(selectedItem.item);
    return {
      kind: "timepoint",
      year,
      offset: yearOffset(entryYear, year),
      label: formatYearOffset(entryYear, year),
    };
  }
  if (selectedItem.kind !== "relation") return null;
  const endpoints = [
    ...(selectedItem.item.sourcePoints || []).map((point) => ({ ...point, role: "source" })),
    ...(selectedItem.item.targetPoints || []).map((point) => ({ ...point, role: "target" })),
  ].map((point) => {
    const year = eventYear(point);
    return {
      role: point.role,
      entityId: normalizeId(point.entityId),
      timepointId: normalizeId(point.timepointId),
      year,
      offset: yearOffset(entryYear, year),
      label: formatYearOffset(entryYear, year),
    };
  });
  return { kind: "relation", endpoints };
}

export function resolveHierarchyReturnContext({
  entityId,
  entities = [],
  hierarchyEdges = [],
  staffEdges = [],
  activeEntityIds = null,
}) {
  const entityMap = entities instanceof Map
    ? entities
    : new Map(entities.map((entity) => [normalizeId(entity.id), entity]));
  const requestedId = normalizeId(entityId);
  const requested = entityMap.get(requestedId) || null;
  if (!requested) return null;

  let institution = requested;
  if (requested.type !== "机构") {
    const affiliation = staffEdges.find((edge) => (
      normalizeId(edge.official) === requestedId
      || normalizeId(edge.official_id) === requestedId
    ));
    institution = entityMap.get(normalizeId(affiliation?.org ?? affiliation?.institution)) || null;
  }
  if (!institution) return null;

  const context = resolveHierarchyContext(institution.id, hierarchyEdges, entityMap);
  const active = activeEntityIds == null
    ? true
    : activeEntityIds instanceof Set
      ? activeEntityIds.has(institution.id)
      : activeEntityIds.includes(institution.id);
  return {
    requestedEntityId: requested.id,
    institutionId: institution.id,
    rootId: context.root?.id ?? institution.id,
    path: context.path,
    active,
  };
}
