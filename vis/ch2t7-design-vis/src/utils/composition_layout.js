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
  sectionTitleFontSize: 24,
  columnTitleFontSize: 16,
  nestedTitleFontSize: 14,
  titleXOffset: 5.4,
  titleYOffset: 5,
  titleColGap: 1,
  staffFontSize: 7,
  summaryStaffFontSize: 8,
  staffColPitch: 11,
  staffTextPad: 5,
  staffMarkerHeight: 5,
  staffMarkerGap: 3,
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

function groupedStaffSources(staffItems, fallbackText) {
  if (!staffItems?.length) {
    return fallbackText ? [{ text: fallbackText, kind: "empty", staffType: "" }] : [];
  }
  const groups = new Map();
  for (const item of staffItems) {
    const kind = item.kind || "neutral";
    if (!groups.has(kind)) groups.set(kind, []);
    groups.get(kind).push(item.text);
  }
  return [...groups].map(([kind, pieces]) => ({
    text: pieces.join("，"),
    kind,
    staffType: kind,
  }));
}

function staffTracksFor(source, rect, title, fontSize, staffMode, geometry) {
  const titleCapacity = Math.max(1, Math.floor(
    (rect.height - geometry.titleYOffset * 2) / fontSize
  ));
  const titleCols = Math.max(1, Math.ceil(String(title || "").length / titleCapacity));
  const titleWidth = titleCols * fontSize + Math.max(0, titleCols - 1) * geometry.titleColGap;
  const titleLines = Math.min(String(title || "").length, titleCapacity);
  const staffYOffset = staffMode === "below"
    ? geometry.titleYOffset + titleLines * fontSize + geometry.staffTextPad
    : geometry.titleYOffset;
  const staffFontSize = staffMode === "below"
    ? geometry.summaryStaffFontSize
    : geometry.staffFontSize;
  const availableHeight = Math.max(
    staffFontSize * 4,
    rect.height
      - staffYOffset
      - geometry.titleYOffset
  );
  const charsPerCol = Math.max(4, Math.floor(availableHeight / staffFontSize));
  const horizontalStart = staffMode === "below"
    ? geometry.titleXOffset
    : geometry.titleXOffset + titleWidth + geometry.staffTextPad;
  const maxTracks = Math.max(1, Math.floor(
    (rect.width - horizontalStart) / geometry.staffColPitch
  ));
  const tracks = [];
  for (const item of groupedStaffSources(source.staffItems, source.staffText)) {
    const text = String(item.text || "").trim();
    for (let offset = 0; offset < text.length; offset += charsPerCol) {
      tracks.push({
        text: text.slice(offset, offset + charsPerCol),
        kind: item.kind,
        staffType: item.staffType,
        continuation: offset > 0,
      });
    }
  }
  const result = tracks.length > maxTracks ? tracks.slice(0, maxTracks) : tracks;
  if (tracks.length > maxTracks) {
    const last = result[result.length - 1];
    last.text = `${last.text.slice(0, Math.max(1, charsPerCol - 1))}…`;
  }
  return {
    titleCapacity,
    titleWidth,
    staffYOffset,
    staffTracks: result,
    staffMode,
    staffClass: staffMode === "below" ? "cls-30" : "cls-31",
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
  const staffMode = kind === "column" ? "side" : "below";
  const placed = {
    kind,
    ...source,
    depth,
    rect,
    labelRect,
    fontSize,
    children,
    ...staffTracksFor(source, labelRect, source.title, fontSize, staffMode, geometry),
  };
  if (kind === "focus") {
    placed.titlePlateRect = {
      x: rect.x + 0.24,
      y: rect.y + 1.32,
      width: Math.min(40.67, Math.max(0, rect.width - 1)),
      height: Math.min(
        rect.height - 2,
        String(source.title || "").length * fontSize + 14.81
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

  const desiredLane = geometry.branchLabelMin
    + Math.min(18, groupedStaffSources(node.staffItems, node.staffText).length * 5);
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
    fontSize: depth > 1 ? geometry.nestedTitleFontSize : geometry.columnTitleFontSize,
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

  const labelWidth = clamp(
    rect.width * 0.15,
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
  const focusStaffGroups = groupedStaffSources(focusSource.staffItems, focusSource.staffText).length;
  const focusLaneWidth = clamp(
    geometry.focusLaneMin + Math.max(0, focusStaffGroups - 1) * geometry.staffColPitch,
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
