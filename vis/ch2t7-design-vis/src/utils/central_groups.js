export const CENTRAL_GROUP_NAMES = [
  "宰辅与决策中枢",
  "三省六部与馆阁",
  "礼仪宗室与宫廷事务",
  "财赋农政与马政",
  "五监与工程教育",
  "司法监察",
  "寺监制度统称",
];

export const OTHER_CENTRAL_GROUP = "其他中央机构";

export function centralGroupId(group) {
  return `central-group:${group}`;
}

export function groupCentralRootIds(rootIds, entityMap) {
  const grouped = new Map();
  for (const entityId of rootIds) {
    const group = entityMap.get(entityId)?.central_group || OTHER_CENTRAL_GROUP;
    if (!grouped.has(group)) grouped.set(group, []);
    grouped.get(group).push(entityId);
  }
  const known = CENTRAL_GROUP_NAMES.filter((group) => grouped.has(group));
  const extra = [...grouped.keys()]
    .filter((group) => !CENTRAL_GROUP_NAMES.includes(group))
    .sort((a, b) => a.localeCompare(b, "zh"));
  return [...known, ...extra].map((group) => ({ group, rootIds: grouped.get(group) }));
}

export function buildCentralGroupNodes({ rootIds, entityMap, expandedGroupId, treeForRoot }) {
  return groupCentralRootIds(rootIds, entityMap).map(({ group, rootIds: groupedRootIds }) => {
    const id = centralGroupId(group);
    const expanded = id === expandedGroupId;
    return {
      id,
      title: group,
      childCount: groupedRootIds.length,
      hiddenCount: expanded ? 0 : groupedRootIds.length,
      isVirtual: true,
      isCentralGroup: true,
      children: expanded ? groupedRootIds.map(treeForRoot).filter(Boolean) : [],
    };
  });
}
