// 由导出 JSON 构建实体级层级图。
// 三种层级边：上下级机构（subject=上级 -> object=下级）、
// 编制隶属（subject=机构 -> object=属官，可带员额）、统称与实例（subject=统称 -> object=实例）。
// 前后演变不属于层级结构，不在此构建。
// 传入 range = [起, 止] 时按时间过滤层级边：
// - 关系自带纪年跨度（yearStart/yearEnd）时，要求与区间相交；
// - 关系两端时间点都无纪年时，仅当两端实体在该区间均有纪年活动才认为成立；
//   完全没有时间依据的边在任何区间都不显示（实体仍可从有纪年的边挂出）。

export const HIERARCHY_TYPES = ["上下级机构", "编制隶属", "统称与实例"];

export const RELATION_TYPE_ORDER = ["上下级机构", "编制隶属", "前后演变", "统称与实例"];

// 关系按类型分组，按 RELATION_TYPE_ORDER 排序，供详情面板展示
export function groupRelationsByType(relations) {
  const byType = new Map();
  for (const relation of relations) {
    if (!byType.has(relation.type)) byType.set(relation.type, []);
    byType.get(relation.type).push(relation);
  }
  const groups = [];
  for (const type of RELATION_TYPE_ORDER) {
    if (byType.has(type)) {
      groups.push({ type, items: byType.get(type) });
      byType.delete(type);
    }
  }
  for (const [type, items] of byType) {
    groups.push({ type, items });
  }
  return groups;
}

// 关系方向的中文标注：以当前实体为视角（out=本实体为主体，in=为客体）
const DIRECTION_LABELS = {
  上下级机构: { out: "下级", in: "上级" },
  编制隶属: { out: "属官", in: "隶属于" },
  前后演变: { out: "后继为", in: "前身为" },
  统称与实例: { out: "实例", in: "统称" },
};

export function relationDirectionLabel(relation) {
  return (
    DIRECTION_LABELS[relation.type]?.[relation.direction] ??
    (relation.direction === "out" ? "→" : "←")
  );
}

// 关系类型对应的着色类名（与层级树色条一致）
export function relationViaClass(type) {
  if (type === "上下级机构") return "sup";
  if (type === "编制隶属") return "staff";
  if (type === "统称与实例") return "alias";
  return "evolve";
}

function compareEntities(entityById) {
  return (a, b) => {
    const ea = entityById.get(a);
    const eb = entityById.get(b);
    if (!ea || !eb) return a - b;
    return (eb.eventCount - ea.eventCount) || ea.title.localeCompare(eb.title, "zh");
  };
}

function entityActiveInRange(entity, range) {
  if (!entity || entity.yearMin == null) return false;
  return entity.yearMin <= range[1] && (entity.yearMax ?? entity.yearMin) >= range[0];
}

function relationInRange(rel, entityById, range) {
  if (rel.yearStart != null) {
    return rel.yearStart <= range[1] && (rel.yearEnd ?? rel.yearStart) >= range[0];
  }
  // 关系两端时间点都无纪年：仅当两端实体在该区间均有纪年活动时才成立
  return (
    entityActiveInRange(entityById.get(rel.subjectEntityId), range) &&
    entityActiveInRange(entityById.get(rel.objectEntityId), range)
  );
}

export function buildEntityGraph(dataset, range = null) {
  const entityById = new Map();
  for (const entity of dataset.entities) {
    entityById.set(entity.id, entity);
  }

  const childrenOf = new Map(); // parentId -> [{entityId, via, quota, staffType, relationId}]
  const parentRelsOf = new Map(); // childId -> [{entityId, via, relationId}]
  const hierarchyTypeSet = new Set(HIERARCHY_TYPES);

  for (const rel of dataset.relations) {
    if (!hierarchyTypeSet.has(rel.type)) continue;
    if (range && !relationInRange(rel, entityById, range)) continue;
    const parent = rel.subjectEntityId;
    const child = rel.objectEntityId;
    if (parent === child || !entityById.has(parent) || !entityById.has(child)) continue;
    if (!childrenOf.has(parent)) childrenOf.set(parent, []);
    childrenOf.get(parent).push({
      entityId: child,
      via: rel.type,
      quota: rel.staffQuota,
      staffType: rel.staffType,
      relationId: rel.id,
    });
    if (!parentRelsOf.has(child)) parentRelsOf.set(child, []);
    parentRelsOf.get(child).push({ entityId: parent, via: rel.type, relationId: rel.id });
  }

  // 同一 (父, 子, 类型) 可能因多个时间点出现多条关系，去重并优先保留带员额的记录
  for (const list of childrenOf.values()) {
    const deduped = new Map();
    for (const item of list) {
      const key = `${item.entityId}|${item.via}`;
      const existing = deduped.get(key);
      if (!existing || (existing.quota == null && item.quota != null)) {
        deduped.set(key, item);
      }
    }
    list.length = 0;
    list.push(...deduped.values());
    list.sort((a, b) => compareEntities(entityById)(a.entityId, b.entityId));
  }

  // 主父 = relation id 最小的上级，用于面包屑与“其余上级”提示
  const primaryParent = new Map();
  for (const [child, list] of parentRelsOf) {
    list.sort((a, b) => a.relationId - b.relationId);
    primaryParent.set(child, list[0].entityId);
  }

  const byActivity = compareEntities(entityById);
  const roots = [...childrenOf.keys()].filter((id) => !parentRelsOf.has(id)).sort(byActivity);
  const isolated = dataset.entities
    .map((entity) => entity.id)
    .filter((id) => !parentRelsOf.has(id) && !childrenOf.has(id))
    .sort(byActivity);

  // 从根到指定实体的主父链（不含自身），带环保护
  function ancestorChain(id) {
    const chain = [];
    const seen = new Set([id]);
    let current = primaryParent.get(id);
    while (current != null && !seen.has(current)) {
      chain.unshift(current);
      seen.add(current);
      current = primaryParent.get(current);
    }
    return chain;
  }

  return { entityById, childrenOf, parentRelsOf, primaryParent, roots, isolated, ancestorChain };
}
