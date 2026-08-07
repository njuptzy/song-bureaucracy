// 编制视图布局：把 composition_model.js 的数据映射回原画板 4-02 的语义。
//
// 视觉层次不是“所有机构一律生成卡片”：
//   1. 焦点机构是整组内容的自由竖排标题，不带外框；
//   2. 焦点的直属下级各自成为机构块；
//   3. 机构块内部的后代成为所属机构列，边线随深度递减；
//   4. 官职类型用原稿图例的窄帽标记，员额仍由文字表达。
//
// 布局会在多个候选行宽中选择最接近画板宽高比的语义拼版，避免固定 shelf
// 把所有块挤在上方，也避免用统一高度制造大片空白。

export const COMPOSITION_GEOMETRY = {
  columnHeight: 211.61,
  rowGap: 2.29,
  blockPaddingX: 2.12,
  blockPaddingY: 2.12,
  focusTitleWidth: 44,
  focusTitleFontSize: 32,
  focusGapX: 8,
  sectionLabelWidth: 40,
  sectionTitleFontSize: 24,
  columnPaddingX: 7,
  columnTitleFontSize: 16,
  titleXOffset: 5.4,
  titleYOffset: 5,
  titleColGap: 1,
  staffFontSize: 7,
  staffColPitch: 11,
  staffTextPad: 5,
  staffMarkerHeight: 5,
  staffMarkerGap: 3,
  staffCharsPerCol: 26,
  blockGapX: 5,
  blockGapY: 10,
  maxBlockWidth: 500,
  minContentWidth: 56,
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

function titleMetrics(title, fontSize, geometry) {
  const capacity = Math.max(4, Math.floor(
    (geometry.columnHeight - geometry.titleYOffset * 2) / fontSize
  ));
  const cols = Math.max(1, Math.ceil(String(title).length / capacity));
  return {
    capacity,
    cols,
    width: cols * fontSize + (cols - 1) * geometry.titleColGap,
    lines: Math.min(String(title).length, capacity),
  };
}

export function staffTextCols(staffText, geometry = COMPOSITION_GEOMETRY, charsPerCol = null) {
  if (!staffText) return 0;
  const perCol = charsPerCol ?? geometry.staffCharsPerCol;
  return Math.max(1, Math.ceil(staffText.length / perCol));
}

function staffTracks(staffItems, fallbackText, charsPerCol) {
  const source = [];
  if (staffItems?.length) {
    const groups = new Map();
    for (const item of staffItems) {
      const kind = item.kind || "neutral";
      if (!groups.has(kind)) groups.set(kind, []);
      groups.get(kind).push(item.text);
    }
    for (const [kind, pieces] of groups) {
      source.push({ text: pieces.join("，"), kind, staffType: kind });
    }
  } else if (fallbackText) {
    source.push({ text: fallbackText, kind: "empty", staffType: "" });
  }
  const tracks = [];
  for (const item of source) {
    const text = String(item.text || "").trim();
    if (!text) continue;
    for (let offset = 0; offset < text.length; offset += charsPerCol) {
      tracks.push({
        text: text.slice(offset, offset + charsPerCol),
        kind: item.kind || "neutral",
        staffType: item.staffType || "",
        continuation: offset > 0,
      });
    }
  }
  return tracks;
}

function columnItem(column, geometry) {
  const title = titleMetrics(column.title, geometry.columnTitleFontSize, geometry);
  const tracks = staffTracks(
    column.staffItems,
    column.staffText,
    geometry.staffCharsPerCol
  );
  return {
    kind: "column",
    ...column,
    titleCols: title.cols,
    titleCapacity: title.capacity,
    titleWidth: title.width,
    staffTracks: tracks,
    staffMode: "side",
    width: geometry.columnPaddingX
      + title.width
      + (tracks.length ? geometry.staffTextPad + tracks.length * geometry.staffColPitch : 0),
  };
}

function institutionLabelItem(institution, geometry, {
  kind = "section",
  fontSize = geometry.sectionTitleFontSize,
  minWidth = geometry.sectionLabelWidth,
} = {}) {
  const title = titleMetrics(institution.title, fontSize, geometry);
  const usedByTitle = title.lines * fontSize + geometry.staffTextPad;
  const trackY = geometry.titleYOffset + usedByTitle;
  const available = geometry.columnHeight
    - trackY
    - geometry.staffMarkerHeight
    - geometry.staffMarkerGap
    - geometry.titleYOffset;
  const charsPerCol = Math.max(5, Math.floor(available / geometry.staffFontSize));
  const tracks = staffTracks(institution.staffItems, institution.staffText, charsPerCol);
  const tracksWidth = tracks.length * geometry.staffColPitch;
  return {
    kind,
    ...institution,
    titleCols: title.cols,
    titleCapacity: title.capacity,
    titleWidth: title.width,
    fontSize,
    staffTracks: tracks,
    staffMode: "below",
    staffYOffset: trackY,
    width: Math.max(
      minWidth,
      geometry.columnPaddingX + title.width,
      geometry.columnPaddingX + tracksWidth
    ),
  };
}

function layoutBlock(block, geometry) {
  const label = institutionLabelItem(block, geometry);
  const columns = (block.columns || []).map((column) => columnItem(column, geometry));
  const labelWidth = label.width;
  const contentLimit = Math.max(
    geometry.minContentWidth,
    geometry.maxBlockWidth - labelWidth - geometry.blockPaddingX * 2
  );
  const rows = [];
  let row = [];
  let rowWidth = 0;
  for (const item of columns) {
    if (row.length && rowWidth + item.width > contentLimit) {
      rows.push({ items: row, width: rowWidth });
      row = [];
      rowWidth = 0;
    }
    row.push(item);
    rowWidth += item.width;
  }
  if (row.length) rows.push({ items: row, width: rowWidth });

  // 无下级的直属机构仍是完整的机构块，但只显示自身名称与直属编制。
  const contentWidth = rows.length
    ? Math.max(...rows.map((item) => item.width))
    : 0;
  const rowCount = Math.max(1, rows.length);
  const width = geometry.blockPaddingX * 2
    + labelWidth
    + Math.max(columns.length ? geometry.minContentWidth : 0, contentWidth);
  const height = geometry.blockPaddingY * 2
    + rowCount * geometry.columnHeight
    + Math.max(0, rowCount - 1) * geometry.rowGap;
  const placedItems = [];
  rows.forEach((rowItem, rowIndex) => {
    let x = geometry.blockPaddingX + labelWidth;
    const y = geometry.blockPaddingY
      + rowIndex * (geometry.columnHeight + geometry.rowGap);
    rowItem.items.forEach((item) => {
      placedItems.push({
        ...item,
        rect: { x, y, width: item.width, height: geometry.columnHeight },
      });
      x += item.width;
    });
  });
  return {
    id: block.id,
    title: block.title,
    width,
    height,
    label: {
      ...label,
      rect: {
        x: geometry.blockPaddingX,
        y: geometry.blockPaddingY,
        width: labelWidth,
        height: height - geometry.blockPaddingY * 2,
      },
    },
    items: placedItems,
    rowCount,
  };
}

function compositionBlocks(model) {
  return [
    ...model.sections,
    ...model.looseColumns.map((column) => ({
      ...column,
      columns: [],
      solo: true,
    })),
  ];
}

function partitionRows(blocks, maxRowWidth, geometry) {
  const count = blocks.length;
  if (!count) return [];
  const best = Array(count + 1).fill(null);
  best[count] = { cost: 0, rows: [] };
  for (let start = count - 1; start >= 0; start -= 1) {
    let width = 0;
    let height = 0;
    for (let end = start; end < count; end += 1) {
      const block = blocks[end];
      width += (end === start ? 0 : geometry.blockGapX) + block.width;
      height = Math.max(height, block.height);
      if (width > maxRowWidth && end > start) break;
      const fill = Math.min(1, width / maxRowWidth);
      const isLast = end === count - 1;
      const raggedness = (1 - fill) ** 2 * (isLast ? 0.35 : 1);
      const next = best[end + 1];
      if (!next) continue;
      const candidate = {
        cost: raggedness + next.cost,
        rows: [{ blocks: blocks.slice(start, end + 1), width, height }, ...next.rows],
      };
      if (!best[start] || candidate.cost < best[start].cost) best[start] = candidate;
    }
  }
  return best[0]?.rows || [];
}

function placeRows(rows, origin, geometry) {
  const placedBlocks = [];
  let y = origin.y;
  let right = origin.x;
  for (const row of rows) {
    let x = origin.x;
    for (const block of row.blocks) {
      placedBlocks.push({
        ...block,
        rect: { x, y, width: block.width, height: block.height },
        label: {
          ...block.label,
          rect: {
            ...block.label.rect,
            x: block.label.rect.x + x,
            y: block.label.rect.y + y,
          },
        },
        items: block.items.map((item) => ({
          ...item,
          rect: {
            ...item.rect,
            x: item.rect.x + x,
            y: item.rect.y + y,
          },
        })),
      });
      x += block.width + geometry.blockGapX;
      right = Math.max(right, x - geometry.blockGapX);
    }
    y += row.height + geometry.blockGapY;
  }
  return {
    blocks: placedBlocks,
    width: Math.max(0, right - origin.x),
    height: Math.max(0, y - origin.y - geometry.blockGapY),
  };
}

function bestPackedRows(blocks, availableWidth, availableHeight, geometry) {
  if (!blocks.length) return { blocks: [], width: 0, height: geometry.columnHeight };
  const widest = Math.max(...blocks.map((block) => block.width));
  const total = blocks.reduce((sum, block) => sum + block.width, 0)
    + geometry.blockGapX * Math.max(0, blocks.length - 1);
  const targetAspect = availableWidth / Math.max(1, availableHeight);
  let winner = null;
  const steps = 18;
  for (let index = 0; index <= steps; index += 1) {
    const candidateWidth = widest + (Math.max(widest, total) - widest) * (index / steps);
    const rows = partitionRows(blocks, candidateWidth, geometry);
    const placed = placeRows(rows, { x: 0, y: 0 }, geometry);
    if (!placed.width || !placed.height) continue;
    const aspect = placed.width / placed.height;
    const usedArea = blocks.reduce((sum, block) => sum + block.width * block.height, 0);
    const waste = 1 - Math.min(1, usedArea / (placed.width * placed.height));
    const score = Math.abs(Math.log(aspect / targetAspect)) + waste * 0.12;
    if (!winner || score < winner.score) winner = { ...placed, rows, score };
  }
  return winner || placeRows(partitionRows(blocks, availableWidth, geometry), { x: 0, y: 0 }, geometry);
}

export function layoutComposition(model, {
  origin = { x: 558.34, y: 150.94 },
  maxWidth = 1251.77,
  maxHeight = 711.8,
  geometry = COMPOSITION_GEOMETRY,
} = {}) {
  if (!model) return null;

  const focusSource = model.selfColumn || {
    id: model.focus.id,
    title: model.focus.title,
    staff: [],
    staffItems: [],
    staffText: "",
  };
  const focusLabel = institutionLabelItem(focusSource, geometry, {
    kind: "focus",
    fontSize: geometry.focusTitleFontSize,
    minWidth: geometry.focusTitleWidth,
  });
  focusLabel.rect = {
    x: origin.x,
    y: origin.y,
    width: focusLabel.width,
    height: geometry.columnHeight,
  };

  const intrinsicBlocks = compositionBlocks(model).map((block) => layoutBlock(block, geometry));
  const blockOriginX = origin.x + focusLabel.width + geometry.focusGapX;
  const blockAvailableWidth = Math.max(geometry.minContentWidth, maxWidth - focusLabel.width - geometry.focusGapX);
  const packed = bestPackedRows(
    intrinsicBlocks,
    blockAvailableWidth,
    maxHeight,
    geometry
  );
  const placed = placeRows(packed.rows || [], { x: blockOriginX, y: origin.y }, geometry);
  const width = focusLabel.width + geometry.focusGapX + placed.width;
  const height = Math.max(geometry.columnHeight, placed.height);

  return {
    origin,
    geometry,
    focus: model.focus,
    focusLabel,
    blocks: placed.blocks,
    items: placed.blocks.flatMap((block) => block.items),
    bounds: { x: origin.x, y: origin.y, width, height },
    rowCount: packed.rows?.length || 0,
  };
}
