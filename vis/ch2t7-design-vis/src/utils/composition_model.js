// 编制视图（画板 4-02）的数据 join 模型。
// 设计稿语义：一个 cls-17 大框 = 焦点机构；框内左端 cls-38 竖排条 = 有下级的
// 下级机构分节（如尚书省吏部）；每列 cls-18 描边框 = 一个机构，列内
// cls-50 竖排机构名 + cls-31 小号竖排编制文本（如"郎中一人，分案十二，吏人五十六"）。
// 本模块只做纯数据组装，不碰 DOM、不算坐标（坐标见 composition_layout.js）。

// 分节的制度次序：吏户礼兵刑工优先，其余按中文标题排序。
const SECTION_ORDER_HINTS = ["吏部", "户部", "礼部", "兵部", "刑部", "工部"];

// staff_type 中属于"吏"序列的值，排序时排在官序列之后（设计稿先官额后吏额）。
const CLERK_TYPES = new Set(["吏", "公吏"]);

const CN_DIGITS = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"];

export function quotaLabel(quota) {
  if (quota == null || quota === "") return "";
  const num = Number(quota);
  if (Number.isInteger(num) && num >= 1 && num <= 10) return `${CN_DIGITS[num]}人`;
  if (Number.isInteger(num) && num > 10) return `${num}人`;
  const text = String(quota).trim();
  if (!text) return "";
  return /员|人$/.test(text) ? text : `${text}人`;
}

function sectionOrderKey(title) {
  const index = SECTION_ORDER_HINTS.findIndex((hint) => String(title).includes(hint));
  return index < 0 ? SECTION_ORDER_HINTS.length : index;
}

// 同一官职可能因多个时间点出现多条编制隶属边：一个官职只占一个槽，
// 优先保留带员额的边（与 DesignTemplateCanvas.displayStaffFor 同规则）。
export function dedupeStaffEdges(edges, entityMap) {
  const byOfficial = new Map();
  for (const edge of edges || []) {
    const official = entityMap.get(edge.official);
    if (!official?.title?.trim() || official.type !== "官职") continue;
    const current = byOfficial.get(edge.official);
    if (!current || (!current.staff_quota && edge.staff_quota)) {
      byOfficial.set(edge.official, edge);
    }
  }
  return [...byOfficial.values()];
}

function compareStaffEdges(entityMap, titleOf) {
  return (a, b) => {
    const clerkA = CLERK_TYPES.has(a.staff_type) ? 1 : 0;
    const clerkB = CLERK_TYPES.has(b.staff_type) ? 1 : 0;
    if (clerkA !== clerkB) return clerkA - clerkB;
    const quotaA = Number(a.staff_quota);
    const quotaB = Number(b.staff_quota);
    const numA = Number.isFinite(quotaA) ? quotaA : -1;
    const numB = Number.isFinite(quotaB) ? quotaB : -1;
    if (numA !== numB) return numB - numA;
    return titleOf(a.official).localeCompare(titleOf(b.official), "zh");
  };
}

export function staffTextOf(edges, entityMap, titleOf, emptyText = "编制未载") {
  const staff = dedupeStaffEdges(edges, entityMap).sort(compareStaffEdges(entityMap, titleOf));
  const pieces = staff.map((edge) => {
    const quota = quotaLabel(edge.staff_quota);
    return `${titleOf(edge.official)}${quota}`;
  });
  return { staff, text: pieces.length ? pieces.join("，") : emptyText };
}

// focus 机构的编制视图模型：
// - selfColumn：focus 自身的编制列（有编制才出现，设计稿里紧随大框标题）；
// - looseColumns：没有下级的直接下级机构，紧随 selfColumn 之后（如尚书都省）；
// - sections：有下级的直接下级机构，每个分节内含其全部后代（先根 DFS 展平）。
// 同一实体只进入第一个命中的列（与 hierarchyLevels 的去重规则一致）。
export function buildCompositionModel({
  focusId,
  entityMap,
  childrenFor,
  staffFor,
  titleOf,
  emptyStaffText = "编制未载",
}) {
  const focus = entityMap.get(focusId);
  if (!focus) return null;

  const columnOf = (id) => {
    const { staff, text } = staffTextOf(staffFor(id), entityMap, titleOf, emptyStaffText);
    return { id, title: titleOf(id), staff, staffText: text };
  };

  const childIdsOf = (id) => (childrenFor(id) || []).map((edge) => edge.child);

  const visited = new Set([focusId]);
  const sections = [];
  const looseColumns = [];

  const directChildren = childIdsOf(focusId)
    .filter((id) => !visited.has(id) && visited.add(id))
    .sort((a, b) => titleOf(a).localeCompare(titleOf(b), "zh"));

  for (const childId of directChildren) {
    const grandChildren = childIdsOf(childId);
    if (!grandChildren.length) {
      looseColumns.push(columnOf(childId));
      continue;
    }
    // 分节：先根 DFS 展平全部后代为列。
    const columns = [];
    const stack = [...grandChildren].reverse();
    while (stack.length) {
      const id = stack.pop();
      if (visited.has(id)) continue;
      visited.add(id);
      columns.push(columnOf(id));
      const next = childIdsOf(id);
      for (let i = next.length - 1; i >= 0; i -= 1) stack.push(next[i]);
    }
    const { staff, text } = staffTextOf(staffFor(childId), entityMap, titleOf, emptyStaffText);
    sections.push({ id: childId, title: titleOf(childId), staff, staffText: text, columns });
  }

  sections.sort((a, b) => (
    sectionOrderKey(a.title) - sectionOrderKey(b.title)
    || a.title.localeCompare(b.title, "zh")
  ));

  const selfStaff = staffTextOf(staffFor(focusId), entityMap, titleOf, emptyStaffText);
  const selfColumn = selfStaff.staff.length
    ? { id: focusId, title: focus.title, staff: selfStaff.staff, staffText: selfStaff.text }
    : null;

  return {
    focus: { id: focusId, title: focus.title },
    selfColumn,
    looseColumns,
    sections,
  };
}
