// 编制视图布局：把 composition_model.js 的模型映射成画板 4-02 的多机构分块。
// 几何常量取自原设计稿（SVG viewBox 1920×1080）：
//   列高 211.61，行距 2.29；列框 y 比大框顶部低 2.12；
//   列内左侧竖排机构名（cls-50 16px），右侧小号竖排编制文本（cls-31 7px）；
//   每个直属机构分节各有独立 cls-17 外框，竖排分节名（cls-38 24px）
//   位于框内左端，所属机构列在框内换行。
// 输出全部是数据坐标，渲染层只负责盖章和整体缩放适配。

export const COMPOSITION_GEOMETRY = {
  columnHeight: 211.61,
  rowGap: 2.29,
  blockPaddingX: 2.12,
  blockPaddingY: 2.12,
  blockLabelWidth: 40, // cls-28（32px 竖排大标题）占位
  blockLabelFontSize: 32,
  blockLabelCharsPerCol: 12,
  columnPaddingX: 8.3,
  columnTitleFontSize: 16, // cls-50 竖排机构名
  sectionTitleFontSize: 24, // cls-38 竖排分节名
  sectionGap: 10, // 分节之间的额外间距
  blockGapX: 4,
  blockGapY: 4,
  // 原稿单块最宽约432，动态文本较长时放宽到500，优先保持同机构列在一排。
  maxBlockWidth: 500,
  staffFontSize: 7, // cls-31
  staffColPitch: 11,
  staffTextPad: 6,
  staffCharsPerCol: 28,
  titleXOffset: 5.4, // 标题文字相对列框左边的偏移
  titleYOffset: 5.0, // 标题文字相对列框顶部的偏移
  titleColGap: 1, // 多列标题之间的额外间隙
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

function columnItem(column, geometry, fontSize) {
  const title = titleMetrics(column.title, fontSize, geometry);
  const staffCols = staffTextCols(column.staffText, geometry);
  return {
    ...column,
    titleCols: title.cols,
    titleCapacity: title.capacity,
    titleWidth: title.width,
    staffCols,
    staffCharsPerCol: geometry.staffCharsPerCol,
    staffMode: "side", // 编制文本排在标题右侧
    width: geometry.columnPaddingX
      + title.width
      + (staffCols > 0 ? staffCols * geometry.staffColPitch + geometry.staffTextPad : 0),
  };
}

function sectionItem(section, geometry) {
  const title = titleMetrics(section.title, geometry.sectionTitleFontSize, geometry);
  // 分节编制文本接在标题下方：标题占去的竖向空间先扣除。
  const usedByTitle = title.lines * geometry.sectionTitleFontSize + geometry.staffTextPad;
  const underChars = Math.max(6, Math.floor(
    (geometry.columnHeight - geometry.titleYOffset * 2 - usedByTitle) / geometry.staffFontSize
  ));
  const staffCols = staffTextCols(section.staffText, geometry, underChars);
  return {
    kind: "section",
    id: section.id,
    title: section.title,
    staff: section.staff,
    staffText: section.staffText,
    titleCols: title.cols,
    titleCapacity: title.capacity,
    titleWidth: title.width,
    staffCols,
    staffCharsPerCol: underChars,
    staffMode: "below", // 编制文本接在标题正下方，溢出列向右排
    staffYOffset: geometry.titleYOffset + usedByTitle,
    width: geometry.columnPaddingX
      + title.width
      + (staffCols > 1 ? (staffCols - 1) * geometry.staffColPitch + geometry.staffTextPad : 0),
  };
}

function compositionBlocks(model) {
  const blocks = [];
  if (model.selfColumn || model.looseColumns.length || !model.sections.length) {
    blocks.push({
      id: model.focus.id,
      title: model.focus.title,
      staff: model.selfColumn?.staff || [],
      staffText: model.selfColumn?.staffText || "",
      columns: model.looseColumns,
    });
  }
  blocks.push(...model.sections);
  return blocks;
}

function layoutBlock(block, geometry) {
  const label = sectionItem(block, geometry);
  const columns = block.columns.map((column) => ({
    kind: "column",
    ...columnItem(column, geometry, geometry.columnTitleFontSize),
  }));
  const labelWidth = Math.max(geometry.blockLabelWidth, label.width);
  const contentLimit = Math.max(
    geometry.columnPaddingX + geometry.columnTitleFontSize,
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
  if (row.length || !rows.length) rows.push({ items: row, width: rowWidth });

  const contentWidth = Math.max(60, ...rows.map((item) => item.width));
  const width = geometry.blockPaddingX * 2 + labelWidth + contentWidth;
  const height = geometry.blockPaddingY * 2
    + rows.length * geometry.columnHeight
    + Math.max(0, rows.length - 1) * geometry.rowGap;
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
    rowCount: rows.length,
  };
}

// 每个直属机构独立成框，再按原画板区域从左到右、从上到下拼排。
export function layoutComposition(model, {
  origin = { x: 558.34, y: 150.94 },
  maxWidth = 980,
  geometry = COMPOSITION_GEOMETRY,
} = {}) {
  if (!model) return null;
  const intrinsicBlocks = compositionBlocks(model).map((block) => layoutBlock(block, geometry));
  const placedBlocks = [];
  let cursorX = origin.x;
  let cursorY = origin.y;
  let shelfHeight = 0;
  let right = origin.x;
  let shelfCount = 1;

  for (const block of intrinsicBlocks) {
    if (cursorX > origin.x && cursorX + block.width > origin.x + maxWidth) {
      cursorX = origin.x;
      cursorY += shelfHeight + geometry.blockGapY;
      shelfHeight = 0;
      shelfCount += 1;
    }
    const dx = cursorX;
    const dy = cursorY;
    placedBlocks.push({
      ...block,
      rect: { x: dx, y: dy, width: block.width, height: block.height },
      label: {
        ...block.label,
        rect: {
          ...block.label.rect,
          x: block.label.rect.x + dx,
          y: block.label.rect.y + dy,
        },
      },
      items: block.items.map((item) => ({
        ...item,
        rect: {
          ...item.rect,
          x: item.rect.x + dx,
          y: item.rect.y + dy,
        },
      })),
    });
    cursorX += block.width + geometry.blockGapX;
    shelfHeight = Math.max(shelfHeight, block.height);
    right = Math.max(right, cursorX - geometry.blockGapX);
  }
  const bottom = cursorY + shelfHeight;

  return {
    origin,
    geometry,
    focus: model.focus,
    blocks: placedBlocks,
    items: placedBlocks.flatMap((block) => block.items),
    bounds: {
      x: origin.x,
      y: origin.y,
      width: Math.max(60, right - origin.x),
      height: Math.max(geometry.columnHeight, bottom - origin.y),
    },
    shelfCount,
  };
}
