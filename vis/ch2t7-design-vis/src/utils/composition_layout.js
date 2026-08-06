// 编制视图布局：把 composition_model.js 的模型映射成画板 4-02 的坐标。
// 几何常量取自原设计稿（SVG viewBox 1920×1080）：
//   列高 211.61，行距 2.29；列框 y 比大框顶部低 2.12；
//   列宽 = 内边距 8.3 + 标题宽 + 编制文本列数 × 列距（7px 竖排小字）。
// 输出全部是数据坐标，渲染层只负责盖章和整体缩放适配。

export const COMPOSITION_GEOMETRY = {
  columnHeight: 211.61,
  rowGap: 2.29,
  blockPaddingX: 2.12,
  blockPaddingY: 2.12,
  blockLabelWidth: 40, // cls-28（32px 竖排大标题）占位
  blockLabelFontSize: 32,
  columnPaddingX: 8.3,
  columnTitleWidth: 16, // cls-50（16px 竖排机构名）
  sectionTitleWidth: 24, // cls-38（24px 竖排分节名）
  sectionGap: 10, // 分节之间的额外间距
  staffFontSize: 7, // cls-31
  staffColPitch: 11,
  staffTextPad: 6,
  staffCharsPerCol: 28,
  titleXOffset: 5.4, // 标题文字相对列框左边的偏移
  titleYOffset: 5.0, // 标题文字相对列框顶部的偏移
};

export function staffTextCols(staffText, geometry = COMPOSITION_GEOMETRY) {
  if (!staffText || staffText === "编制未载") return staffText ? 1 : 0;
  return Math.max(1, Math.ceil(staffText.length / geometry.staffCharsPerCol));
}

function columnWidth(staffText, titleWidth, geometry) {
  const cols = staffTextCols(staffText, geometry);
  return geometry.columnPaddingX
    + titleWidth
    + (cols > 0 ? cols * geometry.staffColPitch + geometry.staffTextPad : 0);
}

function stripWidth(titleWidth, geometry) {
  return geometry.columnPaddingX + titleWidth;
}

// 把 selfColumn / looseColumns / sections 展平成带宽度的排版项序列
function layoutItems(model, geometry) {
  const items = [];
  if (model.selfColumn) {
    items.push({
      kind: "column",
      ...model.selfColumn,
      titleWidth: geometry.columnTitleWidth,
      width: columnWidth(model.selfColumn.staffText, geometry.columnTitleWidth, geometry),
    });
  }
  for (const column of model.looseColumns) {
    items.push({
      kind: "column",
      ...column,
      titleWidth: geometry.columnTitleWidth,
      width: columnWidth(column.staffText, geometry.columnTitleWidth, geometry),
    });
  }
  for (const section of model.sections) {
    items.push({
      kind: "section",
      id: section.id,
      title: section.title,
      staff: section.staff,
      staffText: section.staffText,
      titleWidth: geometry.sectionTitleWidth,
      width: columnWidth(section.staffText, geometry.sectionTitleWidth, geometry),
    });
    for (const column of section.columns) {
      items.push({
        kind: "column",
        ...column,
        titleWidth: geometry.columnTitleWidth,
        width: columnWidth(column.staffText, geometry.columnTitleWidth, geometry),
      });
    }
    items.push({ kind: "sectionEnd", id: `section-end:${section.id}`, width: geometry.sectionGap });
  }
  return items;
}

// 单块排版：块标签在左，内容项从左到右流式排列，超出 maxWidth 换行。
// 返回的 x/y 均为画板坐标；内容超高超宽由渲染层整体缩放处理。
export function layoutComposition(model, {
  origin = { x: 558.34, y: 150.94 },
  maxWidth = 980,
  geometry = COMPOSITION_GEOMETRY,
} = {}) {
  if (!model) return null;
  const items = layoutItems(model, geometry);
  const contentX0 = origin.x + geometry.blockPaddingX + geometry.blockLabelWidth;
  const rowY0 = origin.y + geometry.blockPaddingY;
  const limitX = origin.x + maxWidth - geometry.blockPaddingX;

  const placed = [];
  let cursorX = contentX0;
  let cursorY = rowY0;
  let rowRight = contentX0;
  const breakRow = () => {
    cursorY += geometry.columnHeight + geometry.rowGap;
    cursorX = contentX0;
  };

  for (const item of items) {
    const isBoundary = item.kind === "sectionEnd";
    if (!isBoundary && cursorX > contentX0 && cursorX + item.width > limitX) breakRow();
    if (isBoundary && cursorX === contentX0) continue; // 行首不留分节间距
    const rect = {
      x: cursorX,
      y: cursorY,
      width: item.width,
      height: isBoundary ? 0 : geometry.columnHeight,
    };
    placed.push({ ...item, rect });
    cursorX += item.width;
    if (!isBoundary) rowRight = Math.max(rowRight, cursorX);
  }

  const rowCount = placed.length
    ? Math.round((cursorY - rowY0) / (geometry.columnHeight + geometry.rowGap)) + 1
    : 0;
  const contentBottom = rowCount
    ? cursorY + geometry.columnHeight
    : rowY0 + geometry.columnHeight;

  return {
    origin,
    geometry,
    label: {
      x: origin.x + geometry.blockPaddingX + geometry.blockLabelWidth / 2,
      y: rowY0 + geometry.titleYOffset,
      title: model.focus.title,
    },
    items: placed.filter((item) => item.kind !== "sectionEnd"),
    block: {
      x: origin.x,
      y: origin.y,
      width: Math.max(rowRight, contentX0 + 60) - origin.x + geometry.blockPaddingX,
      height: contentBottom - origin.y + geometry.blockPaddingY,
    },
    rowCount,
  };
}
