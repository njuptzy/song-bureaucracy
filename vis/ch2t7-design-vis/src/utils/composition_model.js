// 编制视图（画板 4-02）的数据 join 模型。
// 设计稿语义：焦点机构只作为全图大号标题，不生成重复外框；它的直属机构
// （如尚书省吏部）各自成框，每列描边框 = 一个更下级机构，列内是竖排
// 机构名与按官职类型分轨的编制文本（如“郎中一人，书令史三十五人”）。
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

// 原设计稿右下角只定义了四种官职视觉编码。数据库里大量 staff_type 仅写作
// “官”或直接写具体差遣名称，不能擅自把它们归为职事官；无法从原值确认时
// 使用 neutral，仍显示原始文字，但不冒充四类中的任何一类。
export function officialKindOf(staffType) {
  const value = String(staffType || "").trim();
  if (!value) return "neutral";
  if (/胥|吏/.test(value)) return "clerk";
  if (/差遣/.test(value)) return "dispatch";
  if (/阶官|散官|寄禄/.test(value)) return "rank";
  if (/职事官/.test(value)) return "duty";
  return "neutral";
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
  const items = staff.map((edge) => {
    const quota = quotaLabel(edge.staff_quota);
    return {
      officialId: edge.official,
      title: titleOf(edge.official),
      quota,
      text: `${titleOf(edge.official)}${quota}`,
      kind: officialKindOf(edge.staff_type),
      staffType: edge.staff_type || "",
    };
  });
  return {
    staff,
    items,
    text: items.length ? items.map((item) => item.text).join("，") : emptyText,
  };
}

// focus 机构的编制视图模型：
// - selfColumn：focus 自身的直属编制（有编制才出现，设计稿里紧随大号标题）；
// - looseColumns：没有下级的直接下级机构，各自成为最小完整机构块；
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
    const { staff, items, text } = staffTextOf(
      staffFor(id), entityMap, titleOf, emptyStaffText
    );
    return { id, title: titleOf(id), staff, staffItems: items, staffText: text };
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
    const stack = [...grandChildren].reverse().map((id) => ({
      id,
      depth: 1,
      parentId: childId,
    }));
    while (stack.length) {
      const { id, depth, parentId } = stack.pop();
      if (visited.has(id)) continue;
      visited.add(id);
      columns.push({ ...columnOf(id), depth, parentId });
      const next = childIdsOf(id);
      for (let i = next.length - 1; i >= 0; i -= 1) {
        stack.push({ id: next[i], depth: depth + 1, parentId: id });
      }
    }
    const { staff, items, text } = staffTextOf(
      staffFor(childId), entityMap, titleOf, emptyStaffText
    );
    sections.push({
      id: childId,
      title: titleOf(childId),
      staff,
      staffItems: items,
      staffText: text,
      columns,
    });
  }

  sections.sort((a, b) => (
    sectionOrderKey(a.title) - sectionOrderKey(b.title)
    || a.title.localeCompare(b.title, "zh")
  ));

  const selfStaff = staffTextOf(staffFor(focusId), entityMap, titleOf, emptyStaffText);
  const selfColumn = selfStaff.staff.length
    ? {
      id: focusId,
      title: focus.title,
      staff: selfStaff.staff,
      staffItems: selfStaff.items,
      staffText: selfStaff.text,
    }
    : null;

  return {
    focus: { id: focusId, title: focus.title },
    selfColumn,
    looseColumns,
    sections,
  };
}
