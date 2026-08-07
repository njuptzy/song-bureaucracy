// 编制画板 4-02 的递归语义布局。
//
// 原稿不是卡片流，而是一个连续填满的机构总框：左侧为焦点机构标题与直属
// 编制，右侧每一块只表示焦点的直接下级；块内只排列该机构的直接孩子，
// 更深节点嵌套在自己的父列内部。每一行都重新分配列宽并填满可用区域，
// 因而不会出现“末行只有两列、右侧仍保留整块空白”的错误。

export const COMPOSITION_GEOMETRY = {
  outerPadding: 3,
  focusLaneMin: 58,
  focusLaneMax: 108,
  focusTitleFontSize: 32,
  focusTitleMinFontSize: 24,
  sectionTitleFontSize: 24,
  sectionTitleMinFontSize: 18,
  columnTitleFontSize: 16,
  columnTitleMinFontSize: 13,
  nestedTitleFontSize: 14,
  nestedTitleMinFontSize: 11,
  // 原稿中的 x 是竖排文字基线，不是字形左边缘。焦点基线相对当前
  // inner rect 为 17.62px；部门和子机构分别约为 15.52px、11.8px。
  focusTitleXOffset: 17.62,
  sectionTitleXOffset: 15.52,
  columnTitleXOffset: 11.8,
  nestedTitleXOffset: 9.5,
  focusTitleYOffset: 7.1,
  sectionTitleYOffset: 7.2,
  columnTitleYOffset: 5,
  nestedTitleYOffset: 5,
  titleColGap: 1,
  staffFontSize: 7,
  summaryStaffFontSize: 8,
  staffColPitch: 8.4,
  summaryStaffColPitch: 9.6,
  focusStaffGap: 7,
  sectionStaffGap: 6,
  columnStaffGap: 8,
  staffBottomPadding: 5,
  textSidePadding: 3,
  sectionGapX: 3,
  sectionGapY: 3,
  columnGap: 2.2,
  nestedGap: 2,
  sectionLabelMin: 40,
  sectionLabelMax: 72,
  branchLabelMin: 25,
};

export function fitCompositionBlock(block, bounds, { maxScale = 2.4 } = {}) {
  if (!block || !bounds || block.width <= 0 || block.height <= 0) return null;
  const scale = Math.min(
    maxScale,
    bounds.width / block.width,
    bounds.height / block.height
  );
  const renderedWidth = block.width * scale;
  const renderedHeight = block.height * scale;
  return {
    scale,
    x: bounds.x + (bounds.width - renderedWidth) / 2,
    y: bounds.y + (bounds.height - renderedHeight) / 2,
    translateX: bounds.x + (bounds.width - renderedWidth) / 2 - block.x * scale,
    translateY: bounds.y + (bounds.height - renderedHeight) / 2 - block.y * scale,
    width: renderedWidth,
    height: renderedHeight,
  };
}

export function staffTextCols(staffText, _geometry = COMPOSITION_GEOMETRY, charsPerCol = 26) {
  if (!staffText) return 0;
  return Math.max(1, Math.ceil(String(staffText).length / charsPerCol));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function characters(value) {
  return Array.from(String(value || ""));
}

function isMissingStaffText(value) {
  return /^(?:编制|员额)?未载[。.]?$/.test(String(value || "").trim());
}

// 原稿没有“编制未载”占位，也不按官/吏类型拆成左右并列轨道。模型已经把
// 官职排成阅读顺序，这里保持该顺序合为一段，随后只按可用高度切列。
function continuousStaffText(source) {
  const pieces = (source.staffItems || [])
    .map((item) => String(item.text || "").trim())
    .filter(Boolean);
  if (pieces.length) return pieces.join("，");
  const fallback = String(source.staffText || "").trim();
  return source.staff?.length && fallback && !isMissingStaffText(fallback) ? fallback : "";
}

function textRole(kind, depth, geometry) {
  if (kind === "focus") {
    return {
      titleXOffset: geometry.focusTitleXOffset,
      titleYOffset: geometry.focusTitleYOffset,
      titleMinFontSize: geometry.focusTitleMinFontSize,
      staffFontSize: geometry.summaryStaffFontSize,
      staffTrackPitch: geometry.summaryStaffColPitch,
      staffGap: geometry.focusStaffGap,
      staffClass: "cls-30",
    };
  }
  if (kind === "section") {
    return {
      titleXOffset: geometry.sectionTitleXOffset,
      titleYOffset: geometry.sectionTitleYOffset,
      titleMinFontSize: geometry.sectionTitleMinFontSize,
      staffFontSize: geometry.summaryStaffFontSize,
      staffTrackPitch: geometry.summaryStaffColPitch,
      staffGap: geometry.sectionStaffGap,
      staffClass: "cls-30",
    };
  }
  const nested = depth > 1;
  return {
    titleXOffset: nested ? geometry.nestedTitleXOffset : geometry.columnTitleXOffset,
    titleYOffset: nested ? geometry.nestedTitleYOffset : geometry.columnTitleYOffset,
    titleMinFontSize: nested
      ? geometry.nestedTitleMinFontSize
      : geometry.columnTitleMinFontSize,
    staffFontSize: geometry.staffFontSize,
    staffTrackPitch: geometry.staffColPitch,
    staffGap: geometry.columnStaffGap,
    staffClass: "cls-31",
  };
}

function fittedTitleFontSize(title, rect, baseFontSize, role) {
  const length = Math.max(1, characters(title).length);
  const availableHeight = Math.max(1, rect.height - role.titleYOffset * 2);
  const singleColumnFit = Math.floor((availableHeight / length) * 2) / 2;
  return clamp(
    Math.min(baseFontSize, singleColumnFit),
    role.titleMinFontSize,
    baseFontSize,
  );
}

function horizontalTextMetrics({
  role,
  fontSize,
  titleCols,
  titlePitch,
  staffTrackCount,
  geometry,
}) {
  const staffHalfSpan = staffTrackCount
    ? (staffTrackCount - 1) * role.staffTrackPitch / 2 + role.staffFontSize / 2
    : 0;
  // 多列编制围绕标题基线居中，列数较多时只把整组向右平移到安全边距内。
  const titleXOffset = Math.max(
    role.titleXOffset,
    staffTrackCount ? geometry.textSidePadding + staffHalfSpan : role.titleXOffset,
  );
  const titleRight = titleXOffset
    + Math.max(0, titleCols - 1) * titlePitch
    + fontSize / 2;
  const staffRight = staffTrackCount ? titleXOffset + staffHalfSpan : 0;
  return {
    titleXOffset,
    staffRightmostXOffset: titleXOffset
      + Math.max(0, staffTrackCount - 1) * role.staffTrackPitch / 2,
    requiredWidth: Math.max(titleRight, staffRight) + geometry.textSidePadding,
  };
}

function labelMetrics(source, {
  kind,
  rect,
  fontSize,
  geometry,
  depth,
}) {
  const role = textRole(kind, depth, geometry);
  const resolvedFontSize = fittedTitleFontSize(source.title, rect, fontSize, role);
  const titleChars = characters(source.title);
  const titleCapacity = Math.max(1, Math.floor(
    (rect.height - role.titleYOffset * 2) / resolvedFontSize
  ));
  const titleCols = Math.max(1, Math.ceil(titleChars.length / titleCapacity));
  const titlePitch = resolvedFontSize + geometry.titleColGap;
  const titleWidth = titleCols * resolvedFontSize
    + Math.max(0, titleCols - 1) * geometry.titleColGap;
  const titleLines = Math.min(titleChars.length, titleCapacity);
  const staffYOffset = role.titleYOffset
    + titleLines * resolvedFontSize
    + role.staffGap;
  const availableStaffHeight = Math.max(
    0,
    rect.height - staffYOffset - geometry.staffBottomPadding,
  );
  const charsPerCol = Math.floor(availableStaffHeight / role.staffFontSize);
  const staffChars = characters(continuousStaffText(source));
  const allTracks = [];
  if (charsPerCol > 0) {
    for (let offset = 0; offset < staffChars.length; offset += charsPerCol) {
      allTracks.push({
        text: staffChars.slice(offset, offset + charsPerCol).join(""),
        kind: "neutral",
        staffType: "",
        continuation: offset > 0,
      });
    }
  }

  const fullHorizontal = horizontalTextMetrics({
    role,
    fontSize: resolvedFontSize,
    titleCols,
    titlePitch,
    staffTrackCount: allTracks.length,
    geometry,
  });
  let visibleTrackCount = allTracks.length;
  let horizontal = fullHorizontal;
  while (visibleTrackCount > 0 && horizontal.requiredWidth > rect.width) {
    visibleTrackCount -= 1;
    horizontal = horizontalTextMetrics({
      role,
      fontSize: resolvedFontSize,
      titleCols,
      titlePitch,
      staffTrackCount: visibleTrackCount,
      geometry,
    });
  }
  const staffTracks = allTracks.slice(0, visibleTrackCount).map((track) => ({ ...track }));
  if (visibleTrackCount < allTracks.length && staffTracks.length) {
    const last = staffTracks.at(-1);
    const lastChars = characters(last.text);
    last.text = `${lastChars.slice(0, Math.max(1, charsPerCol - 1)).join("")}…`;
  }
  return {
    fontSize: resolvedFontSize,
    titleCapacity,
    titleCols,
    titleLines,
    titlePitch,
    titleWidth,
    titleXOffset: horizontal.titleXOffset,
    titleYOffset: role.titleYOffset,
    staffYOffset,
    staffTracks,
    staffTrackCount: allTracks.length,
    staffRightmostXOffset: horizontal.staffRightmostXOffset,
    staffTrackPitch: role.staffTrackPitch,
    staffFontSize: role.staffFontSize,
    staffGap: role.staffGap,
    staffMode: "below",
    staffClass: role.staffClass,
    fullRequiredWidth: fullHorizontal.requiredWidth,
    requiredWidth: horizontal.requiredWidth,
    charsPerStaffCol: charsPerCol,
  };
}

function placedLabel(source, {
  kind,
  rect,
  labelRect = rect,
  fontSize,
  geometry,
  depth = source.depth ?? 0,
  children = [],
}) {
  const metrics = labelMetrics(source, {
    kind,
    rect: labelRect,
    fontSize,
    geometry,
    depth,
  });
  const placed = {
    kind,
    ...source,
    depth,
    rect,
    labelRect,
    children,
    ...metrics,
  };
  if (kind === "focus") {
    placed.titlePlateRect = {
      x: rect.x - geometry.outerPadding + 0.24,
      y: rect.y - geometry.outerPadding + 1.32,
      width: Math.min(40.67, Math.max(0, rect.width + geometry.outerPadding - 1)),
      height: Math.min(
        rect.height + geometry.outerPadding - 2,
        characters(source.title).length * metrics.fontSize + 14.81
      ),
    };
  }
  return placed;
}

function nodeWeight(node) {
  const own = 1
    + Math.min(1.2, String(node.title || "").length * 0.09)
    + Math.min(1.4, String(node.staffText || "").length * 0.012);
  if (!node.children?.length) return own;
  return own + node.children.reduce((sum, child) => sum + nodeWeight(child) * 0.28, 0);
}

function sectionWeight(section) {
  return 1.4 + (section.columns || []).reduce((sum, child) => sum + Math.sqrt(nodeWeight(child)), 0);
}

function preferredInternalRows(section) {
  const columns = section.columns || [];
  const demand = columns.reduce((sum, child) => sum + nodeWeight(child), 0);
  return columns.length >= 6 || demand >= 11 ? 2 : 1;
}

function allocateWidths(items, totalWidth, gap, weightOf) {
  if (!items.length) return [];
  const available = Math.max(0, totalWidth - gap * Math.max(0, items.length - 1));
  const weights = items.map((item) => Math.max(0.35, Math.sqrt(weightOf(item))));
  const totalWeight = weights.reduce((sum, value) => sum + value, 0);
  let used = 0;
  return items.map((item, index) => {
    const width = index === items.length - 1
      ? Math.max(0, available - used)
      : available * (weights[index] / totalWeight);
    used += width;
    return width;
  });
}

function balancedGroups(items, rowCount, weightOf) {
  if (!items.length) return [];
  const rows = Math.max(1, Math.min(rowCount, items.length));
  const total = items.reduce((sum, item) => sum + weightOf(item), 0);
  const target = total / rows;
  const result = [];
  let start = 0;
  let remainingRows = rows;
  while (remainingRows > 0) {
    if (remainingRows === 1) {
      result.push(items.slice(start));
      break;
    }
    const maxEnd = items.length - (remainingRows - 1);
    let bestEnd = start + 1;
    let weight = 0;
    let bestDistance = Infinity;
    for (let end = start + 1; end <= maxEnd; end += 1) {
      weight += weightOf(items[end - 1]);
      const distance = Math.abs(weight - target);
      if (distance <= bestDistance) {
        bestDistance = distance;
        bestEnd = end;
      } else if (weight > target) {
        break;
      }
    }
    result.push(items.slice(start, bestEnd));
    start = bestEnd;
    remainingRows -= 1;
  }
  return result;
}

function layoutBranch(node, rect, geometry) {
  const depth = node.depth ?? 1;
  if (!node.children?.length) {
    return placedLabel(node, {
      kind: "column",
      rect,
      fontSize: depth > 1 ? geometry.nestedTitleFontSize : geometry.columnTitleFontSize,
      geometry,
      depth,
    });
  }

  const baseFontSize = depth > 1
    ? geometry.nestedTitleFontSize
    : geometry.columnTitleFontSize;
  const probe = labelMetrics(node, {
    kind: "column",
    rect,
    fontSize: baseFontSize,
    geometry,
    depth,
  });
  // 分支标题栏必须按真实文字轨数留宽；只按 staff_type 组数估宽会让贡院
  // 等长编制穿过父栏，压到右侧嵌套机构标题上。
  const desiredLane = Math.max(geometry.branchLabelMin, probe.fullRequiredWidth);
  const labelWidth = clamp(
    desiredLane,
    geometry.branchLabelMin,
    Math.max(geometry.branchLabelMin, rect.width * 0.42)
  );
  const labelRect = {
    x: rect.x,
    y: rect.y,
    width: Math.min(labelWidth, rect.width),
    height: rect.height,
  };
  const childArea = {
    x: labelRect.x + labelRect.width + geometry.nestedGap,
    y: rect.y,
    width: Math.max(0, rect.width - labelRect.width - geometry.nestedGap),
    height: rect.height,
  };
  const nestedRowCount = node.children.length >= 6 && childArea.height >= 130 ? 2 : 1;
  const groups = balancedGroups(node.children, nestedRowCount, nodeWeight);
  const rowHeight = groups.length
    ? (childArea.height - geometry.nestedGap * (groups.length - 1)) / groups.length
    : childArea.height;
  const children = [];
  groups.forEach((group, rowIndex) => {
    const widths = allocateWidths(group, childArea.width, geometry.nestedGap, nodeWeight);
    let x = childArea.x;
    group.forEach((child, index) => {
      const childRect = {
        x,
        y: childArea.y + rowIndex * (rowHeight + geometry.nestedGap),
        width: widths[index],
        height: rowHeight,
      };
      children.push(layoutBranch(child, childRect, geometry));
      x += widths[index] + geometry.nestedGap;
    });
  });
  return placedLabel(node, {
    kind: "column",
    rect,
    labelRect,
    fontSize: baseFontSize,
    geometry,
    depth,
    children,
  });
}

function layoutSection(block, rect, geometry) {
  if (block.kind === "attachments") {
    const widths = allocateWidths(block.columns, rect.width, geometry.columnGap, nodeWeight);
    let x = rect.x;
    const items = block.columns.map((node, index) => {
      const item = layoutBranch({ ...node, depth: 1 }, {
        x,
        y: rect.y,
        width: widths[index],
        height: rect.height,
      }, geometry);
      x += widths[index] + geometry.columnGap;
      return item;
    });
    return { ...block, rect, label: null, items };
  }

  const sectionProbe = labelMetrics(block.section, {
    kind: "section",
    rect,
    fontSize: geometry.sectionTitleFontSize,
    geometry,
    depth: 0,
  });
  const labelWidth = clamp(
    Math.max(rect.width * 0.15, sectionProbe.fullRequiredWidth),
    geometry.sectionLabelMin,
    Math.min(geometry.sectionLabelMax, rect.width * 0.28)
  );
  const labelRect = { x: rect.x, y: rect.y, width: labelWidth, height: rect.height };
  const label = placedLabel(block.section, {
    kind: "section",
    rect: labelRect,
    fontSize: geometry.sectionTitleFontSize,
    geometry,
    depth: 0,
  });
  const content = {
    x: labelRect.x + labelRect.width + geometry.columnGap,
    y: rect.y,
    width: Math.max(0, rect.width - labelRect.width - geometry.columnGap),
    height: rect.height,
  };
  const groups = balancedGroups(block.columns, block.internalRows, nodeWeight);
  const rowHeight = groups.length
    ? (content.height - geometry.columnGap * (groups.length - 1)) / groups.length
    : content.height;
  const items = [];
  groups.forEach((group, rowIndex) => {
    const widths = allocateWidths(group, content.width, geometry.columnGap, nodeWeight);
    let x = content.x;
    group.forEach((node, index) => {
      const nodeRect = {
        x,
        y: content.y + rowIndex * (rowHeight + geometry.columnGap),
        width: widths[index],
        height: rowHeight,
      };
      items.push(layoutBranch(node, nodeRect, geometry));
      x += widths[index] + geometry.columnGap;
    });
  });
  return { ...block, rect, label, items };
}

function departmentRank(title) {
  const hints = ["吏部", "户部", "礼部", "工部", "兵部", "刑部"];
  const index = hints.findIndex((hint) => String(title).includes(hint));
  return index < 0 ? hints.length : index;
}

function genericOuterRows(blocks) {
  if (blocks.length <= 4) return [blocks];
  const rowCount = blocks.length <= 8 ? 2 : 3;
  return balancedGroups(blocks, rowCount, (block) => block.weight);
}

function outerRows(blocks) {
  const sectionBlocks = blocks.filter((block) => block.kind === "section");
  const attachment = blocks.find((block) => block.kind === "attachments");
  const six = ["吏部", "户部", "礼部", "工部", "兵部", "刑部"].map((hint) => (
    sectionBlocks.find((block) => String(block.section.title).includes(hint))
  ));
  if (six.every(Boolean)) {
    const used = new Set(six);
    const extra = sectionBlocks.filter((block) => !used.has(block));
    const rows = [six.slice(0, 4), [...six.slice(4), ...(attachment ? [attachment] : [])]];
    if (extra.length) rows.push(...genericOuterRows(extra));
    return rows.filter((row) => row.length);
  }
  return genericOuterRows(blocks);
}

function flattenItems(items) {
  const result = [];
  const visit = (item) => {
    result.push(item);
    for (const child of item.children || []) visit(child);
  };
  for (const item of items) visit(item);
  return result;
}

export function layoutComposition(model, {
  origin = { x: 503.48, y: 147.58 },
  maxWidth = 1309.84,
  maxHeight = 717.85,
  geometry = COMPOSITION_GEOMETRY,
} = {}) {
  if (!model) return null;
  const parentRect = { x: origin.x, y: origin.y, width: maxWidth, height: maxHeight };
  const inner = {
    x: parentRect.x + geometry.outerPadding,
    y: parentRect.y + geometry.outerPadding,
    width: parentRect.width - geometry.outerPadding * 2,
    height: parentRect.height - geometry.outerPadding * 2,
  };
  const focusSource = model.selfColumn || {
    id: model.focus.id,
    title: model.focus.title,
    staff: [],
    staffItems: [],
    staffText: "",
  };
  const focusProbe = labelMetrics(focusSource, {
    kind: "focus",
    rect: inner,
    fontSize: geometry.focusTitleFontSize,
    geometry,
    depth: -1,
  });
  const focusLaneWidth = clamp(
    Math.max(geometry.focusLaneMin, focusProbe.fullRequiredWidth),
    geometry.focusLaneMin,
    geometry.focusLaneMax
  );
  const focusRect = { x: inner.x, y: inner.y, width: focusLaneWidth, height: inner.height };
  const focusLabel = placedLabel(focusSource, {
    kind: "focus",
    rect: focusRect,
    fontSize: geometry.focusTitleFontSize,
    geometry,
    depth: -1,
  });

  const blocks = [...model.sections]
    .sort((a, b) => departmentRank(a.title) - departmentRank(b.title)
      || a.title.localeCompare(b.title, "zh"))
    .map((section) => ({
      kind: "section",
      id: section.id,
      section,
      columns: section.columns || section.children || [],
      internalRows: preferredInternalRows(section),
      weight: sectionWeight(section),
    }));
  if (model.focusDirectLeaves?.length) {
    blocks.push({
      kind: "attachments",
      id: `attachments:${model.focus.id}`,
      columns: model.focusDirectLeaves,
      internalRows: 1,
      weight: Math.max(1.2, model.focusDirectLeaves.reduce((sum, node) => sum + nodeWeight(node), 0) * 0.65),
    });
  }

  const grid = {
    x: focusRect.x + focusRect.width + geometry.sectionGapX,
    y: inner.y,
    width: Math.max(0, inner.width - focusRect.width - geometry.sectionGapX),
    height: inner.height,
  };
  const rows = outerRows(blocks);
  const rowUnits = rows.map((row) => (
    1 + Math.max(0, ...row.map((block) => block.internalRows - 1)) * 0.55
  ));
  const totalUnits = rowUnits.reduce((sum, unit) => sum + unit, 0) || 1;
  const availableHeight = grid.height - geometry.sectionGapY * Math.max(0, rows.length - 1);
  const placedBlocks = [];
  let y = grid.y;
  rows.forEach((row, rowIndex) => {
    const height = availableHeight * (rowUnits[rowIndex] / totalUnits);
    const widths = allocateWidths(row, grid.width, geometry.sectionGapX, (block) => block.weight);
    let x = grid.x;
    row.forEach((block, index) => {
      const rect = { x, y, width: widths[index], height };
      placedBlocks.push(layoutSection(block, rect, geometry));
      x += widths[index] + geometry.sectionGapX;
    });
    y += height + geometry.sectionGapY;
  });

  const allItems = [focusLabel];
  for (const block of placedBlocks) {
    if (block.label) allItems.push(block.label);
    allItems.push(...flattenItems(block.items));
  }
  return {
    origin,
    geometry,
    focus: model.focus,
    parentRect,
    focusLabel,
    blocks: placedBlocks,
    items: allItems,
    bounds: parentRect,
    rowCount: rows.length,
  };
}
