import { groupInstitutionRootIds, institutionGroupId } from "./central_groups.js";

// 时间线树视图的层级模型：与层级视图共享"制度组虚拟层 + 上下级边"的
// 组织语义，但展开状态完全独立——本视图支持多节点同时展开（时间线树的
// 核心交互），不受层级视图单路径展开状态的影响。

export function timetreeGroupKey(category, group) {
  return institutionGroupId(category, group);
}

export function timetreeEntityKey(entityId) {
  return `entity:${entityId}`;
}

function defaultCategory(entity) {
  return entity?.category || "中央机构";
}

/**
 * 为前序节点补充旋转树的纵向坐标。
 *
 * 叶节点按可见顺序依次占据纵向槽位；展开的父节点位于首尾子树中心。
 * 这等价于把原本“深度向下、兄弟横排”的层级树逆时针旋转 90°，而不是
 * 把前序遍历结果画成带缩进的列表。
 */
export function assignTimetreeLayoutIndices(rows = []) {
  const rowByKey = new Map(rows.map((row) => [row.key, row]));
  const childrenByKey = new Map();
  const roots = [];
  for (const row of rows) {
    if (row.parentKey && rowByKey.has(row.parentKey)) {
      if (!childrenByKey.has(row.parentKey)) childrenByKey.set(row.parentKey, []);
      childrenByKey.get(row.parentKey).push(row);
    } else {
      roots.push(row);
    }
  }

  let nextLeafIndex = 0;
  const place = (row) => {
    const children = childrenByKey.get(row.key) || [];
    if (!children.length) {
      row.layoutIndex = nextLeafIndex;
      nextLeafIndex += 1;
      return row.layoutIndex;
    }
    const childIndices = children.map(place);
    row.layoutIndex = (childIndices[0] + childIndices[childIndices.length - 1]) / 2;
    return row.layoutIndex;
  };
  roots.forEach(place);
  return rows;
}

/**
 * 构建时间线树的可见节点（数组顺序仍为前序遍历，几何位置由 layoutIndex 决定）。
 * 每个节点对应左侧层级树的一个节点；非虚拟节点同时在右侧时间线拥有一条车道。
 *
 * 返回节点对象：{ key, entityId, title, depth, rowIndex, layoutIndex, isVirtual, childCount, expanded }
 * - key：展开状态使用的稳定键（制度组用分组 id，实体用 entity:<id>）
 * - rowIndex：稳定的前序顺序；layoutIndex：旋转树实际使用的纵向槽位
 * - childCount：被收起的下级数量（展开时为 0）
 */
export function buildTimetreeRows({
  entities = [],
  hierarchyEdges = [],
  category = "中央机构",
  collectiveIds = [],
  groupNames = [],
  expandedIds = new Set(),
} = {}) {
  const entityMap = new Map(entities.map((entity) => [entity.id, entity]));
  const collectiveSet = new Set(collectiveIds);
  const eligible = (entity) => entity
    && entity.type === "机构"
    && defaultCategory(entity) === category
    && !collectiveSet.has(entity.id);

  const childrenByParent = new Map();
  const childIds = new Set();
  for (const edge of hierarchyEdges || []) {
    const child = entityMap.get(edge.child);
    if (!entityMap.has(edge.parent) || !child || collectiveSet.has(edge.child)) continue;
    if (!childrenByParent.has(edge.parent)) childrenByParent.set(edge.parent, []);
    childrenByParent.get(edge.parent).push(edge.child);
    childIds.add(edge.child);
  }
  for (const ids of childrenByParent.values()) {
    ids.sort((a, b) => (entityMap.get(a)?.title || "").localeCompare(
      entityMap.get(b)?.title || "",
      "zh",
    ));
  }

  // 根节点排序沿用层级视图：下级越多越靠前，同名按中文标题。
  const scoreCache = new Map();
  const descendantScore = (entityId, visiting = new Set()) => {
    if (scoreCache.has(entityId)) return scoreCache.get(entityId);
    if (visiting.has(entityId)) return 0;
    const nextVisiting = new Set(visiting).add(entityId);
    const children = childrenByParent.get(entityId) || [];
    const score = children.length + children.reduce(
      (sum, childId) => sum + descendantScore(childId, nextVisiting),
      0,
    );
    scoreCache.set(entityId, score);
    return score;
  };

  const rootIds = entities
    .filter((entity) => eligible(entity) && !childIds.has(entity.id))
    .map((entity) => entity.id)
    .sort((a, b) => descendantScore(b) - descendantScore(a)
      || (entityMap.get(a)?.title || "").localeCompare(entityMap.get(b)?.title || "", "zh"));

  const rows = [];
  const visitEntity = (entityId, depth, visiting, parentKey = null) => {
    const entity = entityMap.get(entityId);
    if (!entity || visiting.has(entityId)) return;
    const nextVisiting = new Set(visiting).add(entityId);
    const children = (childrenByParent.get(entityId) || [])
      .filter((childId) => !nextVisiting.has(childId));
    const key = timetreeEntityKey(entityId);
    const expanded = expandedIds.has(key);
    rows.push({
      key,
      entityId,
      parentKey,
      rowIndex: rows.length,
      title: entity.title || `#${entityId}`,
      depth,
      isVirtual: false,
      childCount: expanded ? 0 : children.length,
      totalChildren: children.length,
      expanded,
    });
    if (expanded) {
      for (const childId of children) visitEntity(childId, depth + 1, nextVisiting, key);
    }
  };

  const groups = groupNames.length
    ? groupInstitutionRootIds(rootIds, entityMap, category, groupNames)
    : [{ group: "", rootIds }];

  for (const { group, rootIds: groupedRootIds } of groups) {
    if (!group) {
      for (const rootId of groupedRootIds) visitEntity(rootId, 0, new Set());
      continue;
    }
    const key = timetreeGroupKey(category, group);
    const expanded = expandedIds.has(key);
    rows.push({
      key,
      entityId: null,
      parentKey: null,
      rowIndex: rows.length,
      title: group,
      depth: 0,
      isVirtual: true,
      childCount: expanded ? 0 : groupedRootIds.length,
      totalChildren: groupedRootIds.length,
      expanded,
    });
    if (expanded) {
      for (const rootId of groupedRootIds) visitEntity(rootId, 1, new Set(), key);
    }
  }
  return assignTimetreeLayoutIndices(rows);
}

/** 非虚拟行的实体 id，按行顺序——右侧时间线车道的构建顺序。 */
export function timetreeLaneEntityIds(rows) {
  return rows.filter((row) => !row.isVirtual && row.entityId != null)
    .map((row) => row.entityId);
}

/**
 * 与层次结构视图一致的单路径展开：制度组互斥，机构只保留当前祖先路径；
 * 收起节点时移除它及所有已展开后代。
 */
export function toggleTimetreeExpansion(rows = [], currentKeys = [], clickedKey) {
  const rowByKey = new Map(rows.map((row) => [row.key, row]));
  const clicked = rowByKey.get(clickedKey);
  if (!clicked) return [...currentKeys];
  const current = new Set(currentKeys);

  if (clicked.isVirtual) {
    return current.has(clickedKey) ? [] : [clickedKey];
  }

  if (!current.has(clickedKey)) {
    const path = [];
    let cursor = clicked;
    while (cursor) {
      path.push(cursor.key);
      cursor = cursor.parentKey ? rowByKey.get(cursor.parentKey) : null;
    }
    return path.reverse();
  }

  const removed = new Set([clickedKey]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const row of rows) {
      if (!removed.has(row.key) && row.parentKey && removed.has(row.parentKey)) {
        removed.add(row.key);
        changed = true;
      }
    }
  }
  return currentKeys.filter((key) => !removed.has(key));
}

/** 默认展开：只打开首个有数据的制度组，机构保持收起。 */
export function defaultTimetreeExpandedKeys({
  entities = [],
  category = "中央机构",
  groupNames = [],
} = {}) {
  if (!groupNames.length) return [];
  const entityMap = new Map(entities.map((entity) => [entity.id, entity]));
  const rootIds = entities
    .filter((entity) => entity?.type === "机构" && defaultCategory(entity) === category)
    .map((entity) => entity.id);
  const [first] = groupInstitutionRootIds(rootIds, entityMap, category, groupNames);
  return first?.group ? [timetreeGroupKey(category, first.group)] : [];
}
