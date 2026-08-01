// 由导出 JSON 构建实体级层级图。
// 只有上下级机构（subject=上级 -> object=下级）构成行政层级树。
// 编制隶属（subject=机构 -> object=属官）和统称与实例
// （subject=统称 -> object=实例）分别进入独立关系索引，不再冒充父子层级。
// 前后演变属于时间结构，不在此构建。
// 关系的纪年依据是离散的：periods 里每段来自关系某一端时间点自身的纪年，
// 不做两端合并（两端相隔很远时，合并跨度会编造出没有依据的连续期）。
// 传入年份时构建“年末快照”：每个实体取该年以前最后一个有明确纪年的时间点，
// 状态延续到下一时间点；罢废/合并后不显示，复置后重新显示。关系同样取截至该年最近一次归属。

import { buildYearSnapshot } from "./snapshot";

export const HIERARCHY_TYPES = ["上下级机构"];

export const RELATION_TYPE_ORDER = ["上下级机构", "编制隶属", "前后演变", "统称与实例"];

// 单条关系的依据时段文本（"1126年、1126—1127年"；无纪年时返回"时间未明"）
export function relationPeriodsLabel(relation) {
  const periods = relation?.periods || [];
  if (!periods.length) return "时间未明";
  return periods
    .map((p) => (p.start === p.end ? `${p.start}年` : `${p.start}—${p.end}年`))
    .join("、");
}

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

export function buildEntityGraph(dataset, yearOrRange = null) {
  const snapshotYear = Array.isArray(yearOrRange) ? yearOrRange[0] : yearOrRange;
  const snapshot = snapshotYear == null ? null : buildYearSnapshot(dataset, snapshotYear);
  const sourceEntities = snapshot?.entities || dataset.entities;
  const sourceRelations = snapshot?.relations || dataset.relations;
  const entityById = new Map();
  for (const entity of sourceEntities) {
    entityById.set(entity.id, entity);
  }

  const childrenOf = new Map(); // parentId -> [{entityId, via, quota, staffType, relationId}]
  const parentRelsOf = new Map(); // childId -> [{entityId, via, relationId}]
  const staffChildrenOf = new Map(); // institutionId -> [office relation item]
  const staffParentsOf = new Map(); // officeId -> [institution relation item]
  const instancesOf = new Map(); // collectiveId -> [instance relation item]
  const collectivesOf = new Map(); // instanceId -> [collective relation item]
  const hierarchyTypeSet = new Set(HIERARCHY_TYPES);

  for (const rel of sourceRelations) {
    const parent = rel.subjectEntityId;
    const child = rel.objectEntityId;
    if (parent === child || !entityById.has(parent) || !entityById.has(child)) continue;
    const item = {
      entityId: child,
      via: rel.type,
      quota: rel.staffQuota,
      staffType: rel.staffType,
      relationId: rel.id,
      relationIds: [rel.id],
      hasUndated: !rel.periods?.length,
      periods: (rel.periods || []).map((p) => ({ start: p.start, end: p.end })),
    };

    if (rel.type === "编制隶属") {
      if (!staffChildrenOf.has(parent)) staffChildrenOf.set(parent, []);
      staffChildrenOf.get(parent).push(item);
      if (!staffParentsOf.has(child)) staffParentsOf.set(child, []);
      staffParentsOf.get(child).push({ ...item, entityId: parent });
      continue;
    }
    if (rel.type === "统称与实例") {
      if (!instancesOf.has(parent)) instancesOf.set(parent, []);
      instancesOf.get(parent).push(item);
      if (!collectivesOf.has(child)) collectivesOf.set(child, []);
      collectivesOf.get(child).push({ ...item, entityId: parent });
      continue;
    }
    if (!hierarchyTypeSet.has(rel.type)) continue;
    if (!childrenOf.has(parent)) childrenOf.set(parent, []);
    childrenOf.get(parent).push(item);
    if (!parentRelsOf.has(child)) parentRelsOf.set(child, []);
    parentRelsOf.get(child).push({ entityId: parent, via: rel.type, relationId: rel.id });
  }

  // 同一对实体可能因多个时间点出现多条关系，合并关系、纪年与员额。
  function dedupeRelationMaps(...maps) {
    for (const map of maps) {
      for (const list of map.values()) {
        const deduped = new Map();
        for (const item of list) {
          const key = `${item.entityId}|${item.via}`;
          const existing = deduped.get(key);
          if (!existing) {
            deduped.set(key, item);
            continue;
          }
          for (const relationId of item.relationIds) {
            if (!existing.relationIds.includes(relationId)) existing.relationIds.push(relationId);
          }
          for (const period of item.periods) {
            if (!existing.periods.some((p) => p.start === period.start && p.end === period.end)) {
              existing.periods.push(period);
            }
          }
          existing.hasUndated ||= item.hasUndated;
          if (existing.quota == null && item.quota != null) {
            existing.quota = item.quota;
            existing.staffType = item.staffType;
          }
        }
        list.length = 0;
        for (const item of deduped.values()) {
          item.periods.sort((a, b) => a.start - b.start || a.end - b.end);
          list.push(item);
        }
        list.sort((a, b) => compareEntities(entityById)(a.entityId, b.entityId));
      }
    }
  }
  dedupeRelationMaps(childrenOf, staffChildrenOf, staffParentsOf, instancesOf, collectivesOf);

  // 主父 = relation id 最小的上级，用于面包屑与“其余上级”提示
  const primaryParent = new Map();
  for (const [child, list] of parentRelsOf) {
    list.sort((a, b) => a.relationId - b.relationId);
    primaryParent.set(child, list[0].entityId);
  }

  const byActivity = compareEntities(entityById);
  const roots = [...childrenOf.keys()].filter((id) => !parentRelsOf.has(id)).sort(byActivity);
  const isolated = sourceEntities
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

  return {
    entityById,
    childrenOf,
    parentRelsOf,
    staffChildrenOf,
    staffParentsOf,
    instancesOf,
    collectivesOf,
    primaryParent,
    roots,
    isolated,
    ancestorChain,
  };
}
