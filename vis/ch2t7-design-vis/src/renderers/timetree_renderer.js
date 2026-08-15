import { relationPath } from "./evolution_renderer.js";
import {
  TIMETREE_GEOMETRY,
  timetreeNodeX,
  timetreeRowY,
} from "../utils/timetree_layout.js";

const SVG_NS = "http://www.w3.org/2000/svg";

// 视觉常量与 evolution_renderer.js 保持一致（调色时需两处同步）。
const COLORS = {
  ink: "#351704",
  line: "#563905",
  olive: "#918069",
  selected: "#866d6d",
  paper: "#f5f3ec",
  abolish: "#a0432e",
};

// 与演变视图统一：所有关系线同一粗细同一透明度，只有选中才加粗实色。
const RELATION_STROKE = {
  width: 1.1,
  opacity: 0.35,
  selectedWidth: 1.7,
  selectedOpacity: 1,
};

function svgElement(tag, attrs = {}) {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attrs)) {
    if (value != null) element.setAttribute(name, String(value));
  }
  return element;
}

function appendText(parent, text, attrs = {}) {
  const element = svgElement("text", attrs);
  element.textContent = text;
  parent.appendChild(element);
  return element;
}

function addTitle(element, text) {
  const title = svgElement("title");
  title.textContent = text;
  element.appendChild(title);
}

function makeInteractive(element, label, activate) {
  element.setAttribute("role", "button");
  element.setAttribute("tabindex", "0");
  element.setAttribute("aria-label", label);
  element.style.pointerEvents = "all";
  element.style.cursor = "pointer";
  element.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    activate(event);
  });
  element.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    event.stopPropagation();
    activate(event);
  });
}

function eventDescription(event) {
  return [event.rawTime || event.time || "时间未明", event.event || event.quotation || "未载事件"]
    .filter(Boolean)
    .join("：");
}

function ensureTimetreeDefs(svg, geometry) {
  svg.querySelectorAll("[data-timetree-def]").forEach((element) => element.remove());
  let defs = svg.querySelector("defs");
  if (!defs) {
    defs = svgElement("defs");
    svg.insertBefore(defs, svg.firstChild);
  }

  const clip = svgElement("clipPath", {
    id: "timetree-rows-clip",
    clipPathUnits: "userSpaceOnUse",
    "data-timetree-def": "clip",
  });
  clip.appendChild(svgElement("rect", {
    x: 498,
    y: geometry.rowsTop - 16,
    width: 1336,
    height: geometry.rowsBottom - geometry.rowsTop + 32,
  }));

  const arrow = svgElement("marker", {
    id: "timetree-relation-arrow",
    markerWidth: 6,
    markerHeight: 6,
    refX: 5.5,
    refY: 3,
    orient: "auto",
    markerUnits: "userSpaceOnUse",
    "data-timetree-def": "marker",
  });
  arrow.appendChild(svgElement("path", {
    d: "M0.5 0.5L5.5 3L0.5 5.5",
    fill: "none",
    stroke: COLORS.line,
    "stroke-width": 1,
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  }));
  defs.append(clip, arrow);
}

function renderAxis(parent, geometry, yearMin, yearMax) {
  const { plot, axisY, rowsTop, rowsBottom } = geometry;
  parent.appendChild(svgElement("line", {
    x1: plot.x0, y1: axisY, x2: plot.x1, y2: axisY,
    stroke: COLORS.olive, "stroke-width": 0.7,
  }));
  const ticks = [yearMin, ...[1000, 1050, 1100, 1150, 1200, 1250].filter(
    (year) => year > yearMin && year < yearMax,
  ), yearMax];
  const scale = (year) => plot.x0
    + (year - yearMin) / Math.max(1, yearMax - yearMin) * (plot.x1 - plot.x0);
  for (const year of ticks) {
    const x = scale(year);
    parent.appendChild(svgElement("line", {
      x1: x, y1: rowsTop - 8, x2: x, y2: rowsBottom,
      stroke: COLORS.line, "stroke-width": 0.5, "stroke-opacity": 0.07,
      "pointer-events": "none",
    }));
    parent.appendChild(svgElement("line", {
      x1: x, y1: axisY - 6, x2: x, y2: axisY + 6,
      stroke: COLORS.line, "stroke-width": 0.65,
    }));
    appendText(parent, String(year), {
      x, y: axisY - 11, class: "timetree-axis-label", "text-anchor": "middle",
    });
  }
}

function renderHeaderControls(parent, geometry, handlers) {
  const y = geometry.axisY - 6;
  const collapse = appendText(parent, "全部收起", {
    x: geometry.dividerX - 12,
    y,
    class: "timetree-header-control",
    "text-anchor": "end",
  });
  makeInteractive(collapse, "收起全部层级节点", () => handlers.onCollapseAll?.());
  const expand = appendText(parent, "全部展开", {
    x: geometry.dividerX - 72,
    y,
    class: "timetree-header-control",
    "text-anchor": "end",
  });
  makeInteractive(expand, "展开全部层级节点", () => handlers.onExpandAll?.());
}

function renderRowBand(parent, row, y, geometry, selected) {
  const band = svgElement("rect", {
    class: `timetree-row-band${row.rowIndex % 2 ? " is-odd" : ""}${selected ? " is-selected" : ""}`,
    x: 500,
    y: y - geometry.rowPitch / 2,
    width: 1334,
    height: geometry.rowPitch,
    fill: selected ? COLORS.selected : COLORS.line,
    "fill-opacity": 0.028,
  });
  if (row.entityId != null) band.style.cursor = "pointer";
  parent.appendChild(band);
  return band;
}

function renderTreeLink(parent, row, y, parentY, geometry) {
  if (parentY == null) return;
  const nodeX = timetreeNodeX(row.depth, geometry);
  const linkX = nodeX - 22;
  parent.appendChild(svgElement("path", {
    class: "timetree-tree-link",
    d: `M${linkX} ${parentY}V${y}H${nodeX - 15}`,
    fill: "none",
    stroke: COLORS.olive,
    "stroke-width": 0.7,
    "stroke-opacity": 0.6,
    "pointer-events": "none",
  }));
}

function renderTreeNode(parent, row, y, geometry, selected, handlers) {
  const nodeX = timetreeNodeX(row.depth, geometry);
  const group = svgElement("g", {
    class: `timetree-tree-node${row.isVirtual ? " is-virtual" : ""}${selected ? " is-selected" : ""}`,
  });
  if (row.totalChildren > 0) {
    // 展开/收起三角：收起朝右、展开朝下，与层级视图的折叠语义一致。
    const size = 4.2;
    const cx = nodeX - 11;
    const d = row.expanded
      ? `M${cx - size} ${y - size * 0.6}L${cx + size} ${y - size * 0.6}L${cx} ${y + size * 0.8}Z`
      : `M${cx - size * 0.6} ${y - size}L${cx - size * 0.6} ${y + size}L${cx + size * 0.8} ${y}Z`;
    const toggle = svgElement("path", {
      class: "timetree-tree-toggle",
      d,
      fill: row.expanded ? COLORS.line : COLORS.paper,
      stroke: COLORS.line,
      "stroke-width": 0.9,
      "stroke-linejoin": "round",
    });
    makeInteractive(toggle, row.expanded ? `收起${row.title}` : `展开${row.title}`, () => {
      handlers.onToggleNode?.(row.key);
    });
    addTitle(toggle, row.expanded ? "收起下级" : `展开 ${row.totalChildren} 个下级`);
    group.appendChild(toggle);
  }
  const label = appendText(group, row.title, {
    x: nodeX,
    y: y + 4.5,
    class: "timetree-tree-label",
  });
  if (row.entityId != null) {
    makeInteractive(label, `查看${row.title}`, () => handlers.onSelectEntity?.(row.entityId));
    label.addEventListener("dblclick", (event) => {
      event.preventDefault();
      event.stopPropagation();
      handlers.onOpenEvolution?.(row.entityId);
    });
    addTitle(label, `${row.title}（双击进入演变视图）`);
  } else {
    label.style.cursor = "pointer";
    makeInteractive(label, row.expanded ? `收起${row.title}` : `展开${row.title}`, () => {
      handlers.onToggleNode?.(row.key);
    });
  }
  if (row.childCount > 0) {
    appendText(group, `（${row.childCount}）`, {
      x: nodeX + row.title.length * 13.5 + 6,
      y: y + 4.5,
      class: "timetree-tree-count",
    });
  }
  parent.appendChild(group);
}

function renderSegments(parent, segments, y) {
  for (const segment of segments || []) {
    if (segment.x1 - segment.x0 < 1.5) continue;
    parent.appendChild(svgElement("line", {
      class: "timetree-lifespan",
      x1: segment.x0, y1: y, x2: segment.x1, y2: y,
      stroke: COLORS.olive,
      "stroke-width": 2,
      "stroke-opacity": 0.5,
      "stroke-linecap": "round",
      "pointer-events": "none",
    }));
  }
}

function renderEvent(parent, event, y, selected, handlers) {
  const iconType = event.iconType || "record";
  const eventY = y + (event.dy || 0);
  const group = svgElement("g", {
    class: `timetree-event timetree-event-${iconType}${selected ? " is-selected" : ""}`,
  });
  const x = event.baseX;

  if (event.timeType === "bounded" && event.rangeStartX != null && event.rangeEndX != null) {
    let startX = Math.min(event.rangeStartX, event.rangeEndX);
    let endX = Math.max(event.rangeStartX, event.rangeEndX);
    const degenerate = Math.abs(endX - startX) < 1;
    if (!degenerate && endX - startX < 8) {
      startX = x - 4;
      endX = x + 4;
    }
    // 起止同年（"宋初"类锚定单年）不画塌陷装饰，与演变视图保持一致。
    if (!degenerate) {
      group.appendChild(svgElement("line", {
        x1: startX, y1: eventY + 8.5, x2: endX, y2: eventY + 8.5,
        stroke: COLORS.olive, "stroke-width": 1.1, "stroke-dasharray": "3 2",
      }));
      group.appendChild(svgElement("path", {
        d: `M${startX} ${eventY + 5}V${eventY + 8.5}M${endX} ${eventY + 5}V${eventY + 8.5}`,
        fill: "none", stroke: COLORS.olive, "stroke-width": 1.1,
      }));
    }
  }
  if (event.timeType === "range" && event.rangeStartX != null && event.rangeEndX != null) {
    const startX = event.rangeStartX;
    const endX = event.rangeEndX;
    group.appendChild(svgElement("path", {
      d: `M${startX} ${eventY - 13}V${eventY - 20}H${endX}V${eventY - 13}`,
      fill: "none", stroke: COLORS.olive, "stroke-width": 0.8,
    }));
    const stemTopX = Math.max(Math.min(startX, endX), Math.min(Math.max(startX, endX), x));
    group.appendChild(svgElement("line", {
      x1: x, y1: eventY - 4.2, x2: stemTopX, y2: eventY - 13,
      stroke: COLORS.olive, "stroke-width": 0.65, "stroke-opacity": 0.85,
      "pointer-events": "none",
    }));
  }

  // 错层回指：竖直茎 + 车道上的定位点，与演变视图"密集点错层"同语法。
  if (event.displaced) {
    group.appendChild(svgElement("line", {
      x1: x, y1: y, x2: x, y2: eventY,
      stroke: COLORS.olive, "stroke-width": 0.65, "stroke-opacity": 0.74,
      "pointer-events": "none",
    }));
    group.appendChild(svgElement("circle", {
      cx: x, cy: y, r: 1.65, fill: COLORS.line, "pointer-events": "none",
    }));
  }

  if (iconType === "establish" || iconType === "abolish") {
    const up = iconType === "establish";
    const size = selected ? 5.6 : 4.8;
    const apexY = up ? eventY - size : eventY + size;
    const baseY = up ? eventY + size * 0.79 : eventY - size * 0.79;
    const color = selected ? COLORS.selected : (up ? COLORS.line : COLORS.abolish);
    group.appendChild(svgElement("path", {
      d: `M${x} ${apexY}L${x + size} ${baseY}H${x - size}Z`,
      fill: color,
      stroke: color,
      "stroke-width": selected ? 1.25 : 1,
      "stroke-linejoin": "round",
    }));
  } else {
    group.appendChild(svgElement("circle", {
      cx: x, cy: eventY, r: selected ? 4.2 : 2.6,
      fill: selected ? COLORS.selected : COLORS.paper,
      stroke: selected ? COLORS.selected : COLORS.line,
      "stroke-width": selected ? 1.2 : 1,
    }));
  }

  group.appendChild(svgElement("circle", {
    cx: x, cy: eventY, r: event.displaced ? 5.5 : 10,
    fill: "transparent", "pointer-events": "all",
  }));
  addTitle(group, eventDescription(event));
  makeInteractive(group, `查看${eventDescription(event)}`, () => handlers.onSelectEvent?.(event));
  parent.appendChild(group);
}

function renderRelation(parent, relation, selected, handlers) {
  if (!relation.drawable) return;
  const group = svgElement("g", {
    class: `timetree-relation${selected ? " is-selected" : ""}`,
    "data-relation-id": relation.id,
  });
  const stroke = selected ? COLORS.selected : COLORS.line;
  for (const source of relation.sourcePoints) {
    for (const target of relation.targetPoints) {
      group.appendChild(svgElement("path", {
        d: relationPath(source, target),
        fill: "none",
        stroke,
        "stroke-width": selected ? RELATION_STROKE.selectedWidth : RELATION_STROKE.width,
        "stroke-opacity": selected
          ? RELATION_STROKE.selectedOpacity
          : RELATION_STROKE.opacity,
        "marker-end": "url(#timetree-relation-arrow)",
      }));
    }
  }
  const source = relation.sourcePoints[0];
  const target = relation.targetPoints[0];
  const hit = svgElement("path", {
    d: relationPath(source, target),
    fill: "none",
    stroke: "transparent",
    "stroke-width": 14,
    "pointer-events": "stroke",
  });
  group.appendChild(hit);
  const endpoints = [...relation.sourcePoints, ...relation.targetPoints];
  addTitle(group, `${relation.label}：${endpoints
    .map((point) => point.rawTime || point.effectiveYear || "年代未明")
    .join(" → ")}`);
  makeInteractive(group, `查看关系${relation.label}`, () => handlers.onSelectRelation?.(relation));
  parent.appendChild(group);
}

function renderOffAxisBadge(parent, lane, y, geometry) {
  const count = lane.offAxisEvents?.length || 0;
  if (!count) return;
  const badge = appendText(parent, `轴外·${count}`, {
    x: geometry.plot.x1 - 2,
    y: y + 3,
    class: "timetree-offaxis-badge",
    "text-anchor": "end",
  });
  addTitle(badge, lane.offAxisEvents
    .map((event) => eventDescription(event))
    .join("\n"));
}

function renderScrollbar(parent, scroll, geometry, handlers) {
  if (!scroll || scroll.maxOffset <= 0) return;
  const trackX = 1840;
  const trackY = geometry.rowsTop;
  const trackHeight = geometry.rowsBottom - geometry.rowsTop;
  const thumbHeight = Math.max(
    28,
    trackHeight * scroll.viewportHeight / scroll.contentHeight,
  );
  const travel = trackHeight - thumbHeight;
  const thumbY = trackY + (scroll.offset / scroll.maxOffset) * travel;
  parent.appendChild(svgElement("rect", {
    class: "timetree-scrollbar-track",
    x: trackX, y: trackY, width: 4, height: trackHeight,
    fill: COLORS.line, "fill-opacity": 0.06, rx: 2,
  }));
  const thumb = svgElement("rect", {
    class: "timetree-scrollbar-thumb",
    x: trackX, y: thumbY, width: 4, height: thumbHeight,
    fill: COLORS.line, "fill-opacity": 0.3, rx: 2,
  });
  thumb.style.cursor = "grab";
  parent.appendChild(thumb);
  const fractionFromEvent = (event) => {
    // SVG 以 xMidYMid meet 等比缩放：反算 viewBox 坐标需统一缩放率加 letterbox 偏移。
    const svgEl = parent.ownerSVGElement;
    const rect = svgEl?.getBoundingClientRect();
    if (!rect || !rect.width || !rect.height) return null;
    const scale = Math.min(rect.width / 1920, rect.height / 1080);
    const offsetY = (rect.height - 1080 * scale) / 2;
    const svgY = (event.clientY - rect.top - offsetY) / scale;
    return (svgY - trackY - thumbHeight / 2) / Math.max(1, travel);
  };
  const onDrag = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const fraction = fractionFromEvent(event);
    if (fraction != null) handlers.onScrollToFraction?.(Math.max(0, Math.min(1, fraction)));
  };
  thumb.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    thumb.setPointerCapture(event.pointerId);
    const move = (moveEvent) => onDrag(moveEvent);
    const up = () => {
      thumb.removeEventListener("pointermove", move);
      thumb.removeEventListener("pointerup", up);
      thumb.removeEventListener("pointercancel", up);
    };
    thumb.addEventListener("pointermove", move);
    thumb.addEventListener("pointerup", up);
    thumb.addEventListener("pointercancel", up);
  });
}

/**
 * 时间线树视图：左侧层级树（原层级结构逆时针旋转 90°：根在左、深度向右、
 * 兄弟纵排）与右侧时间线逐行对齐；每一非虚拟行就是一条机构车道。
 */
export function renderTimetreeOverlay(svg, options) {
  const {
    rows = [],
    lanesByEntityId = new Map(),
    eventsByLane = new Map(),
    segmentsByLane = new Map(),
    relations = [],
    yearMin,
    yearMax,
    scroll = null,
    selectedEntityId = null,
    selectedEventId = null,
    selectedRelationId = null,
    handlers = {},
  } = options;
  const geometry = TIMETREE_GEOMETRY;

  ensureTimetreeDefs(svg, geometry);
  svg.querySelector(".dynamic-timetree-layer")?.remove();

  const layer = svgElement("g", { class: "dynamic-timetree-layer" });
  svg.appendChild(layer);

  renderAxis(layer, geometry, yearMin, yearMax);
  renderHeaderControls(layer, geometry, handlers);

  if (!rows.length) {
    appendText(layer, "当前分类暂无机构数据", {
      x: (geometry.tree.x0 + geometry.plot.x1) / 2,
      y: (geometry.rowsTop + geometry.rowsBottom) / 2,
      class: "timetree-empty-hint",
      "text-anchor": "middle",
    });
    return;
  }

  const content = svgElement("g", { "clip-path": "url(#timetree-rows-clip)" });
  layer.appendChild(content);

  const yByKey = new Map(rows.map((row) => [
    row.key,
    timetreeRowY(row.rowIndex, scroll?.offset || 0, geometry),
  ]));

  // 第一遍：行带、树连线、存续段（底层）。
  const underlay = svgElement("g", { class: "timetree-underlay" });
  content.appendChild(underlay);
  for (const row of rows) {
    const y = yByKey.get(row.key);
    const selected = row.entityId != null && row.entityId === selectedEntityId;
    const band = renderRowBand(underlay, row, y, geometry, selected);
    if (row.entityId != null) {
      makeInteractive(band, `查看${row.title}`, () => handlers.onSelectEntity?.(row.entityId));
    }
    renderTreeLink(underlay, row, y, row.parentKey ? yByKey.get(row.parentKey) : null, geometry);
    if (row.entityId != null) {
      renderSegments(underlay, segmentsByLane.get(row.entityId), y);
    }
  }

  // 关系线压在事件点之下。
  const relationLayer = svgElement("g", { class: "timetree-relations" });
  content.appendChild(relationLayer);
  for (const relation of relations) {
    renderRelation(relationLayer, relation, relation.id === selectedRelationId, handlers);
  }

  // 第二遍：事件点与树节点（顶层，保证可点）。
  const overlay = svgElement("g", { class: "timetree-overlay" });
  content.appendChild(overlay);
  for (const row of rows) {
    const y = yByKey.get(row.key);
    if (row.entityId != null) {
      for (const event of eventsByLane.get(row.entityId) || []) {
        renderEvent(overlay, event, y, event.id === selectedEventId, handlers);
      }
      const lane = lanesByEntityId.get(row.entityId);
      if (lane) renderOffAxisBadge(overlay, lane, y, geometry);
    }
    renderTreeNode(overlay, row, y, geometry, row.entityId === selectedEntityId, handlers);
  }

  // 滚轮滚动：挂在整层上，事件从行带/事件点冒泡上来，不挡任何点击。
  layer.addEventListener("wheel", (event) => {
    event.preventDefault();
    handlers.onScroll?.(event.deltaY);
  }, { passive: false });

  renderScrollbar(layer, scroll, geometry, handlers);
}
