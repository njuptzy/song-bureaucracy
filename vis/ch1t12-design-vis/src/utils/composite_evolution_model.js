const CHANGE_CATEGORIES = Object.freeze({
  name: "名称变化",
  structure: "机构设置变化",
  staff: "官员设置及职级变化",
  duty: "职责变化",
});

const NAME_PATTERN = /改称|改名|更名|称为|号曰|旧称|别名|简称/;
const DUTY_PATTERN = /职掌|掌管|掌其|掌[^\s，。；、]{1,8}|移交|归.*掌|分掌|兼领|专掌/;
const STRUCTURE_PATTERN = /改隶|改置|始置|初置|复置|罢置|罢废|废置|并入|分置|增置|裁撤|省并/;

function normalizeId(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : value;
}

function finiteYear(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? Math.round(numeric) : null;
}

function firstDefined(source, keys) {
  for (const key of keys) {
    if (source?.[key] !== undefined && source[key] !== null && source[key] !== "") {
      return source[key];
    }
  }
  return null;
}

function eventYear(item) {
  return finiteYear(firstDefined(item, [
    "effectiveYear", "effective_year", "year_start", "yearStart", "year",
  ]));
}

function eventText(item) {
  return String(firstDefined(item, ["event", "text", "summary", "label"]) || "").trim();
}

function eventType(item) {
  return String(firstDefined(item, ["event_type", "eventType", "type"]) || "");
}

function citationKeys(targetTable, targetId) {
  const prefix = targetTable === "Relationships" ? "R" : "T";
  return targetId == null ? [] : [`${prefix}${targetId}`];
}

function citationsFor(data, keys) {
  return [...new Set(keys || [])].flatMap((key) => (
    Array.isArray(data?.citations?.[key]) ? data.citations[key] : []
  ));
}

function relationEndpoint(member, fallback = {}) {
  const source = member || fallback;
  return {
    entityId: normalizeId(firstDefined(source, ["entityId", "entity_id", "entity", "id"])),
    timepointId: normalizeId(firstDefined(source, [
      "timepointId", "timepoint_id", "object_timepoint_id", "subject_timepoint_id",
    ])),
    year: eventYear(source),
    title: String(firstDefined(source, ["title", "entityTitle"]) || ""),
  };
}

function relationMembers(relation, role) {
  const explicit = role === "source"
    ? firstDefined(relation, ["sourceMembers", "source_members"])
    : firstDefined(relation, ["targetMembers", "target_members"]);
  if (Array.isArray(explicit)) return explicit.map((member) => relationEndpoint(member));
  const fallback = role === "source"
    ? {
      entityId: firstDefined(relation, ["source", "sourceEntityId", "source_entity_id"]),
      timepointId: firstDefined(relation, ["sourceTimepointId", "source_timepoint_id"]),
      year: firstDefined(relation, ["sourceYear", "source_year"]),
    }
    : {
      entityId: firstDefined(relation, ["target", "targetEntityId", "target_entity_id"]),
      timepointId: firstDefined(relation, ["targetTimepointId", "target_timepoint_id"]),
      year: firstDefined(relation, ["targetYear", "target_year"]),
    };
  const endpoint = relationEndpoint(fallback);
  return endpoint.entityId == null && endpoint.timepointId == null ? [] : [endpoint];
}

function relationType(relation) {
  return String(firstDefined(relation, [
    "displayRelationType", "display_relation_type", "relationSubtype", "relation_subtype",
    "relationType", "relation_type", "type",
  ]) || "前后演变");
}

function classifyCompositeChange({ text = "", relationType: type = "", entityType = "机构", eventType: kind = "" }) {
  const combined = `${type} ${text}`;
  if (NAME_PATTERN.test(combined)) return "name";
  if (DUTY_PATTERN.test(combined) || /duty|responsib/i.test(type)) return "duty";
  if (entityType === "官职" || /编制|官员|职级|staff|rank/i.test(type)) return "staff";
  if (
    /affiliation|structure|hierarchy|改隶|改置|设置|机构|前后演变/i.test(type)
    || STRUCTURE_PATTERN.test(text)
    || ["establish", "restore", "abolish", "affiliation_change"].includes(kind)
  ) return "structure";
  return entityType === "官职" ? "staff" : "structure";
}

function normalizeTimepoints(data) {
  const byEntity = new Map();
  const groups = [data?.timepoints || {}, data?.preSongTimepoints || {}];
  for (const group of groups) {
    for (const [entityIdText, values] of Object.entries(group)) {
      const entityId = normalizeId(entityIdText);
      for (const source of values || []) {
        const item = {
          ...source,
          id: normalizeId(source.id),
          entityId: normalizeId(source.entity_id ?? source.entityId ?? entityId),
          year: eventYear(source),
          event: eventText(source),
          eventType: eventType(source),
          citationKeys: citationKeys("Timepoints", source.id),
        };
        if (!byEntity.has(item.entityId)) byEntity.set(item.entityId, []);
        byEntity.get(item.entityId).push(item);
      }
    }
  }
  for (const values of byEntity.values()) {
    values.sort((a, b) => (a.year ?? Number.POSITIVE_INFINITY) - (b.year ?? Number.POSITIVE_INFINITY)
      || String(a.id).localeCompare(String(b.id), "zh", { numeric: true }));
  }
  return byEntity;
}

function normalizeHierarchyEdges(data) {
  return (data?.hierarchyEdges || []).map((edge) => ({
    ...edge,
    id: normalizeId(edge.id),
    parent: normalizeId(edge.parent ?? edge.subject),
    child: normalizeId(edge.child ?? edge.object),
  })).filter((edge) => edge.parent != null && edge.child != null);
}

function normalizeStaffEdges(data) {
  return (data?.staffEdges || []).map((edge) => ({
    ...edge,
    id: normalizeId(edge.id),
    org: normalizeId(edge.org ?? edge.institution ?? edge.parent),
    official: normalizeId(edge.official ?? edge.official_id ?? edge.child),
  })).filter((edge) => edge.org != null && edge.official != null);
}

function normalizeChangeRelations(data) {
  return (data?.changeRelations || data?.evolutionEdges || []).map((relation, index) => ({
    ...relation,
    id: normalizeId(relation.id ?? relation.relationId ?? `relation:${index}`),
    type: relationType(relation),
    sourceMembers: relationMembers(relation, "source"),
    targetMembers: relationMembers(relation, "target"),
    text: String(firstDefined(relation, ["eventText", "event_text", "event", "summary", "quotation"]) || "").trim(),
  }));
}

function addChange(changes, nodesById, change) {
  changes.push(change);
  const endpointIds = new Set([
    change.entityId,
    ...(change.sourceIds || []),
    ...(change.targetIds || []),
  ].filter((id) => id != null));
  for (const id of endpointIds) nodesById.get(id)?.changeIds.push(change.id);
}

function sortChanges(changes) {
  return changes.sort((a, b) => (a.year ?? Number.POSITIVE_INFINITY) - (b.year ?? Number.POSITIVE_INFINITY)
    || String(a.id).localeCompare(String(b.id), "zh", { numeric: true }));
}

/**
 * Build a rendering-neutral composite evolution tree around one institution.
 * The model deliberately keeps all relation endpoints and evidence instead of
 * choosing one target for split/merge/uncertain changes.
 */
export function buildCompositeEvolutionModel(data, focusEntityId, options = {}) {
  const entities = (data?.entities || []).map((entity) => ({
    ...entity,
    id: normalizeId(entity.id),
  }));
  const entityMap = new Map(entities.map((entity) => [entity.id, entity]));
  const focusId = normalizeId(focusEntityId);
  const focus = entityMap.get(focusId);
  if (!focus) return null;

  const hierarchyEdges = normalizeHierarchyEdges(data);
  const staffEdges = normalizeStaffEdges(data);
  const timepoints = normalizeTimepoints(data);
  const childrenByParent = new Map();
  for (const edge of hierarchyEdges) {
    if (!childrenByParent.has(edge.parent)) childrenByParent.set(edge.parent, []);
    if (!childrenByParent.get(edge.parent).some((id) => id === edge.child)) {
      childrenByParent.get(edge.parent).push(edge.child);
    }
  }

  const visibleIds = new Set([focusId]);
  const parentByChild = new Map();
  const queue = [focusId];
  while (queue.length) {
    const parentId = queue.shift();
    for (const childId of childrenByParent.get(parentId) || []) {
      if (visibleIds.has(childId)) continue;
      visibleIds.add(childId);
      parentByChild.set(childId, parentId);
      queue.push(childId);
    }
  }

  const officialByInstitution = new Map();
  for (const edge of staffEdges) {
    if (!visibleIds.has(edge.org)) continue;
    if (!officialByInstitution.has(edge.org)) officialByInstitution.set(edge.org, []);
    if (!officialByInstitution.get(edge.org).includes(edge.official)) {
      officialByInstitution.get(edge.org).push(edge.official);
    }
  }
  for (const ids of officialByInstitution.values()) {
    for (const id of ids) visibleIds.add(id);
  }

  const nodesById = new Map();
  for (const id of visibleIds) {
    const entity = entityMap.get(id);
    if (!entity) continue;
    const isOfficial = entity.type === "官职";
    const parentId = isOfficial
      ? staffEdges.find((edge) => edge.official === id && visibleIds.has(edge.org))?.org ?? null
      : (id === focusId ? null : parentByChild.get(id) ?? null);
    nodesById.set(id, {
      id,
      title: entity.title || "",
      type: entity.type || "机构",
      nodeKind: isOfficial ? "official" : "institution",
      parentId,
      depth: 0,
      childIds: [],
      changeIds: [],
      expanded: id === focusId,
    });
  }
  for (const node of nodesById.values()) {
    if (node.parentId != null && nodesById.has(node.parentId)) {
      nodesById.get(node.parentId).childIds.push(node.id);
      node.depth = nodesById.get(node.parentId).depth + 1;
    }
  }

  const changes = [];
  for (const node of nodesById.values()) {
    for (const point of timepoints.get(node.id) || []) {
      const category = classifyCompositeChange({
        text: point.event,
        entityType: node.type,
        eventType: point.eventType,
      });
      const id = `T${point.id}`;
      addChange(changes, nodesById, {
        id,
        kind: "timepoint",
        category,
        categoryLabel: CHANGE_CATEGORIES[category],
        entityId: node.id,
        sourceIds: [node.id],
        targetIds: [],
        year: point.year,
        eventTime: point.raw_time ?? point.time ?? "",
        eventText: point.event,
        eventType: point.eventType,
        citationKeys: point.citationKeys,
        citations: citationsFor(data, point.citationKeys),
        quotation: point.quotation || "",
      });
    }
  }

  const relationEntries = normalizeChangeRelations(data);
  for (const relation of relationEntries) {
    // 关系端点不能因为不在当前树的展开范围内而被裁掉；渲染层可以
    // 将外部端点作为关系上下文显示，但不得替关系擅自选择一个去向。
    const sourceIds = relation.sourceMembers.map((member) => member.entityId).filter((id) => id != null);
    const targetIds = relation.targetMembers.map((member) => member.entityId).filter((id) => id != null);
    if (!sourceIds.length && !targetIds.length) continue;
    const endpointYears = [...relation.sourceMembers, ...relation.targetMembers]
      .map((member) => member.year)
      .filter((year) => year != null);
    const category = classifyCompositeChange({
      text: relation.text,
      relationType: relation.type,
      entityType: sourceIds.some((id) => entityMap.get(id)?.type === "官职") ? "官职" : "机构",
    });
    const relationCitationKeys = citationKeys("Relationships", relation.id);
    addChange(changes, nodesById, {
      id: `R${relation.id}`,
      kind: "relation",
      category,
      categoryLabel: CHANGE_CATEGORIES[category],
      entityId: sourceIds.length === 1 && targetIds.length === 1 ? sourceIds[0] : null,
      sourceIds,
      targetIds,
      sourcePoints: relation.sourceMembers,
      targetPoints: relation.targetMembers,
      year: endpointYears.length ? Math.min(...endpointYears) : null,
      eventTime: relation.eventTime || "",
      eventText: relation.text || relation.type,
      relationType: relation.type,
      citationKeys: relationCitationKeys,
      citations: citationsFor(data, relationCitationKeys),
      quotation: relation.quotation || "",
      uncertain: sourceIds.length !== 1 || targetIds.length !== 1,
    });
  }

  sortChanges(changes);
  const root = nodesById.get(focusId);
  const categories = Object.entries(CHANGE_CATEGORIES).map(([key, label]) => ({
    key,
    label,
    count: changes.filter((change) => change.category === key).length,
  }));
  return {
    focusEntityId: focusId,
    focusTitle: focus.title || "",
    nodes: [...nodesById.values()],
    nodesById,
    root,
    changes,
    categories,
    hierarchyEdges,
    staffEdges,
    yearMin: finiteYear(options.yearMin),
    yearMax: finiteYear(options.yearMax),
  };
}

export function visibleCompositeNodes(model, expandedIds = []) {
  if (!model?.nodes) return [];
  const expanded = new Set(expandedIds);
  const visible = [];
  const visit = (node, ancestorVisible = true) => {
    if (!node || !ancestorVisible) return;
    visible.push(node);
    if (!expanded.has(node.id)) return;
    for (const childId of node.childIds || []) visit(model.nodesById?.get(childId), true);
  };
  visit(model.root, true);
  return visible;
}

export { CHANGE_CATEGORIES, classifyCompositeChange };
