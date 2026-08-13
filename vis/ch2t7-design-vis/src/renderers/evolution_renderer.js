import { compactRelationLabel } from "../utils/evolution_layout.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const XHTML_NS = "http://www.w3.org/1999/xhtml";

const COLORS = {
  ink: "#351704",
  line: "#563905",
  olive: "#918069",
  oliveFill: "#a5a68d",
  selected: "#866d6d",
  paper: "#f5f3ec",
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

function appendVerticalText(parent, text, attrs = {}, options = {}) {
  const { maxChars = 8, pitch = 11 } = options;
  const x = Number(attrs.x || 0);
  const startY = Number(attrs.y || 0);
  const element = svgElement("text", attrs);
  Array.from(shortened(text, maxChars)).forEach((character, index) => {
    const tspan = svgElement("tspan", {
      x,
      y: startY + index * pitch,
      "text-anchor": "middle",
    });
    tspan.textContent = character;
    element.appendChild(tspan);
  });
  parent.appendChild(element);
  return element;
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

function addTitle(element, text) {
  const title = svgElement("title");
  title.textContent = text;
  element.appendChild(title);
}

function shortened(text, limit = 8) {
  const value = String(text || "").replace(/\s+/g, "").trim();
  if (value.length <= limit) return value || "未载事件";
  return `${value.slice(0, Math.max(1, limit - 1))}…`;
}

function eventDescription(event) {
  return [event.rawTime || event.time || "时间未明", event.event || event.quotation || "未载事件"]
    .filter(Boolean)
    .join("：");
}

function selectedKey(item) {
  if (!item) return "";
  return `${item.kind}:${item.id}`;
}

function ensureDefs(svg) {
  svg.querySelectorAll("[data-evolution-def]").forEach((element) => element.remove());
  let defs = svg.querySelector("defs");
  if (!defs) {
    defs = svgElement("defs");
    svg.insertBefore(defs, svg.firstChild);
  }

  const clip = svgElement("clipPath", {
    id: "evolution-content-clip",
    clipPathUnits: "userSpaceOnUse",
    "data-evolution-def": "clip",
  });
  clip.appendChild(svgElement("rect", { x: 503, y: 128, width: 1311, height: 738 }));

  const arrow = svgElement("marker", {
    id: "evolution-relation-arrow",
    markerWidth: 8,
    markerHeight: 8,
    refX: 7,
    refY: 4,
    orient: "auto",
    markerUnits: "strokeWidth",
    "data-evolution-def": "marker",
  });
  arrow.appendChild(svgElement("path", {
    d: "M0 0L8 4L0 8",
    fill: "none",
    stroke: COLORS.line,
    "stroke-width": 1.15,
  }));
  defs.append(clip, arrow);
}

function renderModeChoice(parent, { x, label, active, onActivate }) {
  const group = svgElement("g", { class: `evolution-mode-choice${active ? " is-active" : ""}` });
  group.appendChild(svgElement("rect", {
    x, y: 338, width: 11, height: 11,
    fill: active ? COLORS.line : "none",
    stroke: COLORS.line,
    "stroke-width": 0.8,
  }));
  appendText(group, label, { x: x + 20, y: 348.5, class: "evolution-selector-copy" });
  makeInteractive(group, `切换到${label}演变模式`, onActivate);
  parent.appendChild(group);
}

function selectorNode(parent, entity, index, selected, removable, handlers) {
  const x = 83 + index * 62;
  const y = 367;
  const width = 46;
  const height = 92;
  const group = svgElement("g", {
    class: `evolution-selector-node${selected ? " is-selected" : ""}`,
    transform: `translate(${x} ${y})`,
    "data-entity-id": entity.id,
  });
  group.appendChild(svgElement("path", {
    d: `M0 7H5V0H${width - 5}V7H${width}V${height}H0Z`,
    fill: selected ? COLORS.ink : "none",
    "fill-opacity": selected ? 0.12 : 0,
    stroke: COLORS.line,
    "stroke-width": selected ? 1.35 : 0.85,
  }));
  appendVerticalText(group, entity.title, {
    x: width / 2,
    y: 14,
    class: "evolution-selector-node-label",
    "text-anchor": "middle",
  }, {
    maxChars: 6,
    pitch: 12.5,
  });
  addTitle(group, `${entity.title}（${entity.type}）`);
  makeInteractive(group, `选择${entity.title}`, () => handlers.onSelectEntity?.(entity.id));

  if (removable) {
    const remove = svgElement("g", {
      class: "evolution-selector-remove",
      transform: `translate(${width - 7} 7)`,
    });
    remove.appendChild(svgElement("circle", {
      cx: 0, cy: 0, r: 7, fill: COLORS.paper, stroke: COLORS.line, "stroke-width": 0.7,
    }));
    remove.appendChild(svgElement("path", {
      d: "M-2.5-2.5L2.5 2.5M2.5-2.5L-2.5 2.5",
      fill: "none", stroke: COLORS.line, "stroke-width": 0.9,
    }));
    makeInteractive(remove, `移除${entity.title}`, () => handlers.onRemoveEntity?.(entity.id));
    group.appendChild(remove);
  }
  parent.appendChild(group);
}

function renderAddNode(parent, index, onActivate) {
  const x = 83 + index * 62;
  const group = svgElement("g", {
    class: "evolution-selector-add",
    transform: `translate(${x} 367)`,
  });
  group.appendChild(svgElement("path", {
    d: "M0 7H5V0H41V7H46V92H0Z",
    fill: "none",
    stroke: COLORS.olive,
    "stroke-width": 0.85,
    "stroke-dasharray": "3 3",
  }));
  group.appendChild(svgElement("path", {
    d: "M17 38H29M23 32V44",
    fill: "none",
    stroke: COLORS.line,
    "stroke-width": 1.2,
    "stroke-linecap": "round",
  }));
  appendText(group, "添加", {
    x: 23, y: 61, class: "evolution-selector-count", "text-anchor": "middle",
  });
  makeInteractive(group, "添加演变对比对象", onActivate);
  parent.appendChild(group);
}

function searchMatches(entities, query, selectedIds) {
  const normalized = String(query || "").trim().toLocaleLowerCase("zh-CN");
  return [...entities]
    .filter((entity) => !selectedIds.includes(entity.id))
    .filter((entity) => !normalized || entity.title.toLocaleLowerCase("zh-CN").includes(normalized))
    .sort((a, b) => {
      const aStarts = normalized && a.title.toLocaleLowerCase("zh-CN").startsWith(normalized) ? 0 : 1;
      const bStarts = normalized && b.title.toLocaleLowerCase("zh-CN").startsWith(normalized) ? 0 : 1;
      return aStarts - bStarts || a.title.localeCompare(b.title, "zh");
    })
    .slice(0, 7);
}

function renderSearchPanel(parent, entities, selectedIds, handlers) {
  const foreignObject = svgElement("foreignObject", {
    class: "evolution-search-panel",
    x: 78,
    y: 322,
    width: 391,
    height: 151,
  });
  foreignObject.style.pointerEvents = "all";
  const panel = document.createElementNS(XHTML_NS, "div");
  panel.className = "evolution-search-surface";
  const row = document.createElementNS(XHTML_NS, "div");
  row.className = "evolution-search-row";
  const input = document.createElementNS(XHTML_NS, "input");
  input.className = "evolution-search-input";
  input.type = "search";
  input.placeholder = "搜索机构或官职";
  input.setAttribute("aria-label", "搜索机构或官职");
  const close = document.createElementNS(XHTML_NS, "button");
  close.className = "evolution-search-close";
  close.type = "button";
  close.setAttribute("aria-label", "关闭搜索");
  close.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13"/></svg>';
  close.addEventListener("click", () => handlers.onSearchOpenChange?.(false));
  row.append(input, close);
  const results = document.createElementNS(XHTML_NS, "div");
  results.className = "evolution-search-results";
  panel.append(row, results);
  foreignObject.appendChild(panel);
  parent.appendChild(foreignObject);

  const drawResults = () => {
    results.replaceChildren();
    const matches = searchMatches(entities, input.value, selectedIds);
    if (!matches.length) {
      const empty = document.createElementNS(XHTML_NS, "p");
      empty.className = "evolution-search-empty";
      empty.textContent = "没有匹配的机构或官职";
      results.appendChild(empty);
      return;
    }
    for (const entity of matches) {
      const button = document.createElementNS(XHTML_NS, "button");
      button.type = "button";
      button.className = "evolution-search-result";
      const title = document.createElementNS(XHTML_NS, "span");
      title.textContent = entity.title;
      const type = document.createElementNS(XHTML_NS, "small");
      type.textContent = entity.type;
      button.append(title, type);
      button.addEventListener("click", () => handlers.onAddEntity?.(entity.id));
      results.appendChild(button);
    }
  };
  input.addEventListener("input", drawResults);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") handlers.onSearchOpenChange?.(false);
  });
  drawResults();
  queueMicrotask(() => input.focus());
}

function renderSelector(layer, options) {
  const group = svgElement("g", { class: "evolution-selector-layer" });
  appendText(group, "演变对象", { x: 82, y: 307, class: "evolution-section-heading" });
  group.appendChild(svgElement("line", {
    x1: 82, y1: 319, x2: 475, y2: 319, stroke: COLORS.line, "stroke-width": 0.82,
  }));
  renderModeChoice(group, {
    x: 83,
    label: "单体",
    active: options.mode === "single",
    onActivate: () => options.handlers.onModeChange?.("single"),
  });
  renderModeChoice(group, {
    x: 176,
    label: "对比",
    active: options.mode === "compare",
    onActivate: () => options.handlers.onModeChange?.("compare"),
  });
  appendText(group, `${options.focusEntities.length} / 4`, {
    x: 475, y: 348.5, class: "evolution-selector-count", "text-anchor": "end",
  });
  options.focusEntities.forEach((entity, index) => selectorNode(
    group,
    entity,
    index,
    entity.id === options.activeEntityId,
    options.mode === "compare" && options.focusEntities.length > 1,
    options.handlers,
  ));
  if (options.focusEntities.length < 4) {
    renderAddNode(group, options.focusEntities.length, () => options.handlers.onSearchOpenChange?.(true));
  }
  if (options.searchOpen) {
    renderSearchPanel(group, options.entities, options.focusEntities.map((entity) => entity.id), options.handlers);
  }
  layer.appendChild(group);
}

function renderAxis(parent, layout, selectedRange, selectionActive) {
  const { plotBounds, yearScale } = layout;
  const axisY = plotBounds.y - 25;
  parent.appendChild(svgElement("line", {
    x1: plotBounds.x, y1: axisY, x2: plotBounds.right, y2: axisY,
    stroke: COLORS.olive, "stroke-width": 0.7,
  }));
  const [yearMin, yearMax] = yearScale.domain;
  const ticks = [yearMin, ...[1000, 1050, 1100, 1150, 1200, 1250].filter(
    (year) => year > yearMin && year < yearMax
  ), yearMax];
  const scale = (year) => yearScale.range[0]
    + (year - yearMin) / Math.max(1, yearMax - yearMin)
      * (yearScale.range[1] - yearScale.range[0]);
  for (const year of ticks) {
    const x = scale(year);
    parent.appendChild(svgElement("line", {
      x1: x, y1: axisY - 6, x2: x, y2: axisY + 6,
      stroke: COLORS.line, "stroke-width": 0.65,
    }));
    appendText(parent, String(year), {
      x, y: axisY - 11, class: "evolution-axis-label", "text-anchor": "middle",
    });
  }
  if (!selectionActive || !selectedRange?.length) return;
  const start = scale(selectedRange[0]);
  const end = scale(selectedRange[1] ?? selectedRange[0]);
  if (Math.abs(end - start) > 1) {
    parent.appendChild(svgElement("rect", {
      class: "evolution-current-range",
      x: Math.min(start, end),
      y: plotBounds.y - 10,
      width: Math.max(1, Math.abs(end - start)),
      height: plotBounds.height + 20,
      fill: COLORS.selected,
      "fill-opacity": 0.055,
      "pointer-events": "none",
    }));
  }
  for (const x of new Set([start, end])) {
    parent.appendChild(svgElement("line", {
      class: "evolution-current-year",
      x1: x, y1: plotBounds.y - 11, x2: x, y2: plotBounds.bottom + 11,
      stroke: COLORS.selected, "stroke-width": 0.9, "stroke-dasharray": "3 3",
      "pointer-events": "none",
    }));
  }
}

function renderEvolutionLegend(parent, layout) {
  const plot = layout?.plotBounds;
  if (!plot || plot.width < 260) return;
  const group = svgElement("g", { class: "evolution-legend" });
  // The legend shares the title band with the view heading; the year axis
  // immediately above keeps the top edge busy, so the legend must sit below it
  // and left of the lane pager to avoid colliding with either.
  const x = Math.max(plot.x + 260, plot.right - 990);
  const rowY = 185;
  appendText(group, "图例", {
    x,
    y: rowY + 3,
    class: "evolution-legend-title",
  });

  const item = (itemX, label, draw) => {
    const sample = svgElement("g", { class: "evolution-legend-item" });
    draw(sample, itemX);
    appendText(sample, label, {
      x: itemX + 13,
      y: rowY + 3,
      class: "evolution-legend-label",
    });
    group.appendChild(sample);
  };
  item(x + 34, "普通记载", (sample, itemX) => {
    sample.appendChild(svgElement("circle", {
      cx: itemX,
      cy: rowY,
      r: 3.2,
      fill: COLORS.paper,
      stroke: COLORS.line,
      "stroke-width": 0.9,
    }));
  });
  item(x + 99, "建置/罢置", (sample, itemX) => {
    sample.appendChild(svgElement("line", {
      x1: itemX,
      y1: rowY - 6,
      x2: itemX,
      y2: rowY + 6,
      stroke: COLORS.line,
      "stroke-width": 1,
    }));
    sample.appendChild(svgElement("rect", {
      x: itemX - 3.5,
      y: rowY - 3.5,
      width: 7,
      height: 7,
      fill: COLORS.paper,
      stroke: COLORS.line,
      "stroke-width": 0.9,
    }));
  });
  item(x + 167, "时间范围", (sample, itemX) => {
    sample.appendChild(svgElement("path", {
      d: `M${itemX - 6} ${rowY + 3}V${rowY - 4}H${itemX + 6}V${rowY + 3}`,
      fill: "none",
      stroke: COLORS.olive,
      "stroke-width": 0.9,
    }));
  });
  item(x + 232, "模糊纪年区间", (sample, itemX) => {
    sample.appendChild(svgElement("line", {
      x1: itemX - 7, y1: rowY + 2, x2: itemX + 7, y2: rowY + 2,
      stroke: COLORS.olive,
      "stroke-width": 1.1,
      "stroke-dasharray": "3 2",
    }));
    sample.appendChild(svgElement("path", {
      d: `M${itemX - 7} ${rowY - 1.5}V${rowY + 2}M${itemX + 7} ${rowY - 1.5}V${rowY + 2}`,
      fill: "none",
      stroke: COLORS.olive,
      "stroke-width": 1.1,
    }));
  });
  item(x + 316, "演变关系", (sample, itemX) => {
    sample.appendChild(svgElement("line", {
      x1: itemX - 7,
      y1: rowY,
      x2: itemX + 6,
      y2: rowY,
      stroke: COLORS.line,
      "stroke-width": 0.95,
      "marker-end": "url(#evolution-relation-arrow)",
    }));
  });
  item(x + 379, "存续段", (sample, itemX) => {
    sample.appendChild(svgElement("line", {
      x1: itemX - 7,
      y1: rowY,
      x2: itemX + 7,
      y2: rowY,
      stroke: COLORS.line,
      "stroke-width": 2,
    }));
  });
  item(x + 437, "密集点错层回指年份", (sample, itemX) => {
    sample.appendChild(svgElement("line", {
      x1: itemX - 7,
      y1: rowY + 3,
      x2: itemX + 5,
      y2: rowY - 3,
      stroke: COLORS.olive,
      "stroke-width": 0.7,
    }));
    sample.appendChild(svgElement("circle", {
      cx: itemX - 7,
      cy: rowY + 3,
      r: 1.4,
      fill: COLORS.line,
    }));
  });
  addTitle(group, "时间轴符号说明");
  parent.appendChild(group);
}

function renderLaneLabel(parent, lane, selected, onSelectEntity, lanePitch) {
  const height = Math.max(42, Math.min(102, lanePitch ? lanePitch - 12 : 102));
  const width = 34;
  const x = lane.labelX + Math.max(0, lane.labelMaxWidth - width - 8);
  const y = lane.y - height / 2;
  const group = svgElement("g", {
    class: `evolution-lane-label${selected ? " is-selected" : ""}`,
    "data-entity-id": lane.entityId,
  });
  group.appendChild(svgElement("path", {
    d: `M${x} ${y + 5}H${x + 4}V${y}H${x + width - 4}V${y + 5}H${x + width}V${y + height}H${x}Z`,
    fill: selected ? COLORS.ink : COLORS.paper,
    "fill-opacity": selected ? 0.12 : 0.76,
    stroke: COLORS.line,
    "stroke-width": selected ? 1.35 : 0.9,
  }));
  const maxChars = Math.max(2, Math.floor((height - 15) / 10.5) + 1);
  appendVerticalText(group, lane.title, {
    x: x + width / 2,
    y: y + 10,
    class: "evolution-lane-title",
    "text-anchor": "middle",
  }, {
    maxChars,
    pitch: 10.5,
  });
  if (lane.anomalies?.length) {
    const alert = svgElement("g", { class: "evolution-lane-anomaly" });
    alert.appendChild(svgElement("path", {
      d: `M${x + width - 7} ${y - 3}L${x + width + 1} ${y + 11}H${x + width - 15}Z`,
      fill: COLORS.paper, stroke: COLORS.selected, "stroke-width": 0.8,
    }));
    alert.appendChild(svgElement("path", {
      d: `M${x + width - 7} ${y + 1}V${y + 6}M${x + width - 7} ${y + 8.5}V${y + 9}`,
      stroke: COLORS.selected, "stroke-width": 1,
    }));
    addTitle(alert, `${lane.anomalies.length} 项时间链异常`);
    group.appendChild(alert);
  }
  addTitle(group, `${lane.title}（${lane.type}）`);
  makeInteractive(group, `选择${lane.title}`, () => onSelectEntity?.(lane.entityId));
  parent.appendChild(group);
}

function renderEventMark(parent, event, selected, handlers) {
  const group = svgElement("g", {
    class: `evolution-event evolution-event-${event.effect}${selected ? " is-selected" : ""}`,
    "data-timepoint-id": event.id,
  });
  const x = event.displayX;
  const y = event.y;
  const baseY = event.baseY ?? y;
  if (event.displaced) {
    group.appendChild(svgElement("line", {
      class: "evolution-event-stem",
      x1: event.baseX, y1: baseY, x2: x, y2: y,
      stroke: COLORS.olive, "stroke-width": 0.65, "stroke-opacity": 0.74,
    }));
    group.appendChild(svgElement("circle", {
      class: "evolution-event-anchor",
      cx: event.baseX, cy: baseY, r: 1.65,
      fill: COLORS.line,
    }));
  }
  if (event.timeType === "bounded" && event.yearStart != null && event.yearEnd != null) {
    const startX = Math.min(event.rangeStartX ?? event.baseX, event.rangeEndX ?? event.baseX);
    const endX = Math.max(event.rangeStartX ?? event.baseX, event.rangeEndX ?? event.baseX);
    // Fuzzy intervals hang below the lane as a dashed span with solid end
    // ticks — the mirror of the solid "range" bracket above it. The lane
    // itself stays clear, so marks on it remain visible and clickable.
    group.appendChild(svgElement("line", {
      class: "evolution-event-bounded-span",
      x1: startX, y1: y + 8.5, x2: endX, y2: y + 8.5,
      stroke: COLORS.olive,
      "stroke-width": 1.1,
      "stroke-dasharray": "3 2",
    }));
    group.appendChild(svgElement("path", {
      class: "evolution-event-bounded-span",
      d: `M${startX} ${y + 5}V${y + 8.5}M${endX} ${y + 5}V${y + 8.5}`,
      fill: "none",
      stroke: COLORS.olive,
      "stroke-width": 1.1,
    }));
    group.appendChild(svgElement("rect", {
      x: Math.min(startX, endX), y: y + 4, width: Math.max(3, Math.abs(endX - startX)), height: 5.5,
      fill: "transparent", "pointer-events": "all",
    }));
  }
  if (event.timeType === "range" && event.yearStart != null && event.yearEnd != null) {
    const startX = event.rangeStartX ?? event.baseX;
    const endX = event.rangeEndX ?? event.baseX;
    group.appendChild(svgElement("path", {
      d: `M${startX} ${y - 13}V${y - 20}H${endX}V${y - 13}`,
      fill: "none", stroke: COLORS.olive, "stroke-width": 0.8,
    }));
  }
  // For fuzzy (bounded) events the anchor dot only positions the record on the
  // axis — filling it on selection would falsely assert a definite year, so
  // selection highlights the dashed span below the lane instead.
  const markSelected = selected && event.timeType !== "bounded";
  if (event.effect === "ignore") {
    group.appendChild(svgElement("path", {
      d: `M${x - 4} ${y - 4}L${x + 4} ${y + 4}M${x + 4} ${y - 4}L${x - 4} ${y + 4}`,
      stroke: markSelected ? COLORS.selected : COLORS.line,
      "stroke-width": 1,
    }));
  } else if (event.effect === "activate" || event.effect === "deactivate") {
    const tickHalfHeight = event.displaced ? 6.5 : 9;
    group.appendChild(svgElement("line", {
      x1: x, y1: y - tickHalfHeight, x2: x, y2: y + tickHalfHeight,
      stroke: markSelected ? COLORS.selected : COLORS.line,
      "stroke-width": 1.2,
    }));
    group.appendChild(svgElement("rect", {
      x: x - 4, y: y - 4, width: 8, height: 8,
      fill: markSelected ? COLORS.selected : COLORS.paper,
      stroke: markSelected ? COLORS.selected : COLORS.line,
      "stroke-width": 1,
    }));
  } else {
    group.appendChild(svgElement("circle", {
      cx: x, cy: y, r: markSelected ? 4.6 : 3.3,
      fill: markSelected ? COLORS.selected : COLORS.paper,
      stroke: markSelected ? COLORS.selected : COLORS.line,
      "stroke-width": 1,
    }));
  }

  // Selection feedback stays on the mark itself (or, for bounded events, on
  // the dashed span); details live in the left panel, no on-canvas callout.
  group.appendChild(svgElement("circle", {
    cx: x, cy: y, r: event.displaced ? 5.5 : 10,
    fill: "transparent", "pointer-events": "all",
  }));
  addTitle(group, eventDescription(event));
  makeInteractive(group, `查看${eventDescription(event)}`, () => handlers.onSelectEvent?.(event));
  parent.appendChild(group);
}

function relationPath(source, target) {
  const deltaY = target.y - source.y;
  if (Math.abs(deltaY) < 1) {
    const lift = source.y > 470 ? -28 : 28;
    const mid = (source.x + target.x) / 2;
    return `M${source.x} ${source.y}C${mid} ${source.y + lift} ${mid} ${target.y + lift} ${target.x} ${target.y}`;
  }
  // Keep cross-lane jumps tight: a wide bend sweeps across empty canvas and
  // reads as a stray arc when the jump spans several lanes.
  const bend = Math.max(18, Math.min(56, Math.abs(deltaY) * 0.26));
  const sourceControlX = source.x + Math.sign(target.x - source.x || 1) * bend;
  const targetControlX = target.x - Math.sign(target.x - source.x || 1) * bend;
  return `M${source.x} ${source.y}C${sourceControlX} ${source.y} ${targetControlX} ${target.y} ${target.x} ${target.y}`;
}

function renderRelation(parent, relation, selected, handlers, suppressLabel = false) {
  if (!relation.drawable) return;
  const sources = relation.sourcePoints.filter((point) => point.x != null);
  const targets = relation.targetPoints.filter((point) => point.x != null);
  if (!sources.length || !targets.length) return;
  const group = svgElement("g", {
    class: `evolution-relation${selected ? " is-selected" : ""}`,
    "data-relation-id": relation.id,
  });
  for (const source of sources) {
    for (const target of targets) {
      // Long vertical jumps cross several lanes; render them quieter so the
      // existence segments and event marks stay dominant.
      const longJump = Math.abs(target.y - source.y) > 200;
      group.appendChild(svgElement("path", {
        d: relationPath(source, target),
        fill: "none",
        stroke: selected ? COLORS.selected : COLORS.line,
        "stroke-width": selected ? 1.7 : (longJump ? 0.9 : 1.05),
        "stroke-opacity": selected ? 1 : (longJump ? 0.4 : 0.68),
        "marker-end": "url(#evolution-relation-arrow)",
      }));
    }
  }
  if (!suppressLabel && relation.labelVisible !== false) {
    const source = sources[0];
    const target = targets[0];
    const labelX = relation.labelX ?? (source.x + target.x) / 2;
    const labelY = relation.labelY ?? (source.y + target.y) / 2 - 7;
    const leader = relation.leader;
    if (leader && Math.hypot(leader.x2 - leader.x1, leader.y2 - leader.y1) > 4) {
      group.appendChild(svgElement("line", {
        x1: leader.x1,
        y1: leader.y1,
        x2: leader.x2,
        y2: leader.y2,
        class: "evolution-relation-label-leader",
        stroke: COLORS.olive,
        "stroke-width": 0.7,
        "stroke-dasharray": "2 2",
        "pointer-events": "none",
      }));
    }
    appendText(group, compactRelationLabel(relation.label), {
      x: labelX,
      y: labelY,
      class: "evolution-relation-label",
      "text-anchor": "middle",
    });
  } else if (!suppressLabel && relation.labelOverflow) {
    const source = sources[0];
    const target = targets[0];
    const x = relation.labelAnchorX ?? (source.x + target.x) / 2;
    const y = relation.labelAnchorY ?? (source.y + target.y) / 2;
    group.appendChild(svgElement("circle", {
      class: "evolution-relation-overflow-marker",
      cx: x,
      cy: y,
      r: 3.2,
      fill: COLORS.paper,
      stroke: COLORS.olive,
      "stroke-width": 0.8,
    }));
    appendText(group, "…", {
      x,
      y: y + 3.2,
      class: "evolution-relation-overflow-glyph",
      "text-anchor": "middle",
    });
  }
  const all = [...sources, ...targets];
  const hit = svgElement("path", {
    d: relationPath(sources[0], targets[0]),
    fill: "none",
    stroke: "transparent",
    "stroke-width": 14,
    "pointer-events": "stroke",
  });
  group.appendChild(hit);
  addTitle(group, `${relation.label}：${all.map((point) => point.rawTime || point.effectiveYear || "年代未明").join(" → ")}`);
  makeInteractive(group, `查看关系${relation.label}`, () => handlers.onSelectRelation?.(relation));
  parent.appendChild(group);
}

function renderRelationGroup(parent, relationGroup, selectedRelationKey, handlers) {
  if (!relationGroup.drawable) return;
  if (relationGroup.renderMode === "individual" || relationGroup.junctionX == null) {
    relationGroup.relations.forEach((relation) => renderRelation(
      parent,
      relation,
      `relation:${relation.id}` === selectedRelationKey,
      handlers,
    ));
    return;
  }
  const group = svgElement("g", {
    class: "evolution-relation-group",
    "data-relation-group-id": relationGroup.groupId,
  });
  const points = [...relationGroup.sourcePoints, ...relationGroup.targetPoints]
    .filter((point) => point.x != null);
  const centerY = points.length
    ? points.reduce((sum, point) => sum + point.y, 0) / points.length
    : 0;
  const junctionX = relationGroup.junctionX;
  const junction = { x: junctionX, y: centerY };
  for (const source of relationGroup.sourcePoints.filter((point) => point.x != null)) {
    group.appendChild(svgElement("path", {
      d: relationPath(source, junction), fill: "none", stroke: COLORS.line, "stroke-width": 1.05,
    }));
  }
  for (const target of relationGroup.targetPoints.filter((point) => point.x != null)) {
    group.appendChild(svgElement("path", {
      d: relationPath(junction, target), fill: "none", stroke: COLORS.line,
      "stroke-width": 1.05, "marker-end": "url(#evolution-relation-arrow)",
    }));
  }
  group.appendChild(svgElement("rect", {
    x: junctionX - 5, y: centerY - 5, width: 10, height: 10,
    fill: COLORS.paper, stroke: COLORS.line, "stroke-width": 1,
  }));
  if (relationGroup.labelVisible !== false) {
    const leader = relationGroup.leader;
    if (leader && Math.hypot(leader.x2 - leader.x1, leader.y2 - leader.y1) > 4) {
      group.appendChild(svgElement("line", {
        x1: leader.x1,
        y1: leader.y1,
        x2: leader.x2,
        y2: leader.y2,
        class: "evolution-relation-label-leader",
        stroke: COLORS.olive,
        "stroke-width": 0.7,
        "stroke-dasharray": "2 2",
        "pointer-events": "none",
      }));
    }
    const hasLayout = Number.isFinite(relationGroup.labelX)
      && Number.isFinite(relationGroup.labelY);
    appendText(group, compactRelationLabel(relationGroup.label), {
      x: hasLayout ? relationGroup.labelX : junctionX + 11,
      y: hasLayout ? relationGroup.labelY : centerY - 8,
      class: "evolution-relation-label",
      "text-anchor": hasLayout ? "middle" : "start",
    });
  } else if (relationGroup.labelOverflow) {
    group.appendChild(svgElement("circle", {
      class: "evolution-relation-overflow-marker",
      cx: junctionX,
      cy: centerY,
      r: 3.2,
      fill: COLORS.paper,
      stroke: COLORS.olive,
      "stroke-width": 0.8,
    }));
    appendText(group, "…", {
      x: junctionX,
      y: centerY + 3.2,
      class: "evolution-relation-overflow-glyph",
      "text-anchor": "middle",
    });
  }
  relationGroup.relations.forEach((relation) => {
    if (`relation:${relation.id}` === selectedRelationKey) {
      group.classList.add("is-selected");
    }
  });
  makeInteractive(group, `查看事件组${relationGroup.label}`, () => {
    const relation = relationGroup.relations[0];
    if (relation) handlers.onSelectRelation?.(relation);
  });
  parent.appendChild(group);
}

function renderOffAxis(parent, layout, selectedItem, handlers) {
  const bounds = layout.offAxisBounds;
  if (!bounds) return;
  // A faint wash ties the floating undated/unresolved marks into a visible zone.
  parent.appendChild(svgElement("rect", {
    x: bounds.x + 6,
    y: bounds.y - 16,
    width: bounds.width - 12,
    height: bounds.height + 24,
    rx: 5,
    fill: COLORS.olive,
    "fill-opacity": 0.055,
    stroke: COLORS.olive,
    "stroke-width": 0.55,
    "stroke-opacity": 0.32,
    "stroke-dasharray": "2 4",
    "pointer-events": "none",
  }));
  parent.appendChild(svgElement("line", {
    x1: bounds.x, y1: bounds.y - 4, x2: bounds.x, y2: bounds.bottom + 4,
    stroke: COLORS.olive, "stroke-width": 0.65, "stroke-dasharray": "3 3",
  }));
  for (const bucket of ["undated", "unresolved"]) {
    const column = layout.offAxis.columns?.[bucket];
    if (!column) continue;
    appendText(parent, column.label, {
      x: column.x, y: bounds.y - 10, class: "evolution-offaxis-heading", "text-anchor": "middle",
    });
    for (const event of layout.offAxis[bucket] || []) {
      const group = svgElement("g", {
        class: `evolution-offaxis-event${selectedKey(selectedItem) === `timepoint:${event.id}` ? " is-selected" : ""}`,
      });
      group.appendChild(svgElement("circle", {
        cx: event.x, cy: event.y, r: 4.5,
        fill: selectedKey(selectedItem) === `timepoint:${event.id}` ? COLORS.selected : COLORS.paper,
        stroke: bucket === "unresolved" ? COLORS.selected : COLORS.line,
        "stroke-width": 1,
      }));
      group.appendChild(svgElement("circle", {
        cx: event.x, cy: event.y, r: 10, fill: "transparent", "pointer-events": "all",
      }));
      addTitle(group, eventDescription(event));
      makeInteractive(group, `查看${column.label}事件`, () => handlers.onSelectEvent?.(event));
      parent.appendChild(group);
    }
  }
}

/**
 * StoryFlow-style braid prototype: cross-lane relations whose endpoints sit in
 * the same year cluster share one vertical trunk instead of each sweeping its
 * own S-curve across the canvas. Singles keep the classic path.
 */
function bundleRelations(relations) {
  const items = [];
  const singles = [];
  for (const relation of relations) {
    const source = relation.sourcePoints.find((point) => point.x != null);
    const target = relation.targetPoints.find((point) => point.x != null);
    if (!source || !target || relation.hasOffAxisEndpoint || Math.abs(target.y - source.y) < 1) {
      singles.push(relation);
      continue;
    }
    items.push({ relation, source, target, cx: (source.x + target.x) / 2 });
  }
  items.sort((first, second) => first.cx - second.cx);
  const bundles = [];
  const claimed = new Set();
  for (const item of items) {
    if (claimed.has(item)) continue;
    const cluster = [item];
    claimed.add(item);
    for (const other of items) {
      if (claimed.has(other)) continue;
      if (Math.abs(other.cx - item.cx) <= 70) {
        cluster.push(other);
        claimed.add(other);
      }
    }
    if (cluster.length > 1) bundles.push(cluster);
    else singles.push(item.relation);
  }
  return { bundles, singles };
}

function renderRelationBundle(parent, bundle, selectedKey, handlers) {
  const group = svgElement("g", { class: "evolution-relation-bundle" });
  const trunkX = bundle.reduce((sum, item) => sum + item.cx, 0) / bundle.length;
  const ys = bundle.flatMap((item) => [item.source.y, item.target.y]);
  const trunkTop = Math.min(...ys);
  const trunkBottom = Math.max(...ys);
  group.appendChild(svgElement("line", {
    class: "evolution-relation-trunk",
    x1: trunkX, y1: trunkTop, x2: trunkX, y2: trunkBottom,
    stroke: COLORS.line, "stroke-width": 1.9, "stroke-opacity": 0.5,
    "stroke-linecap": "round", "pointer-events": "none",
  }));
  for (const item of bundle) {
    const { relation, source, target } = item;
    const isSelected = selectedKey === `relation:${relation.id}`;
    const color = isSelected ? COLORS.selected : COLORS.line;
    const width = isSelected ? 1.7 : 1.05;
    const opacity = isSelected ? 1 : 0.68;
    const sub = svgElement("g", {
      class: `evolution-relation${isSelected ? " is-selected" : ""}`,
      "data-relation-id": relation.id,
    });
    const entry = Math.max(-9, Math.min(9, (target.y - source.y) * 0.06));
    const into = `M${source.x} ${source.y}Q${trunkX} ${source.y} ${trunkX} ${source.y + entry}`;
    const outFromY = target.y - entry;
    const out = `M${trunkX} ${outFromY}Q${trunkX} ${target.y} ${target.x} ${target.y}`;
    sub.appendChild(svgElement("path", {
      d: into, fill: "none", stroke: color, "stroke-width": width, "stroke-opacity": opacity,
    }));
    sub.appendChild(svgElement("path", {
      d: out, fill: "none", stroke: color, "stroke-width": width, "stroke-opacity": opacity,
      "marker-end": "url(#evolution-relation-arrow)",
    }));
    if (relation.labelVisible !== false) {
      appendText(sub, compactRelationLabel(relation.label), {
        x: relation.labelX ?? trunkX,
        y: relation.labelY ?? (source.y + target.y) / 2 - 7,
        class: "evolution-relation-label",
        "text-anchor": "middle",
      });
    }
    sub.appendChild(svgElement("path", {
      d: `${into}L${trunkX} ${outFromY}${out.slice(1)}`,
      fill: "none", stroke: "transparent", "stroke-width": 12, "pointer-events": "stroke",
    }));
    addTitle(sub, `${relation.label}：${[source, target].map((point) => point.rawTime || point.effectiveYear || "年代未明").join(" → ")}`);
    makeInteractive(sub, `查看关系${relation.label}`, () => handlers.onSelectRelation?.(relation));
    group.appendChild(sub);
  }
  parent.appendChild(group);
}

function renderLanePagerButton(parent, { x, direction, disabled, onActivate }) {
  const label = direction < 0 ? "上一组关联轨道" : "下一组关联轨道";
  const group = svgElement("g", {
    class: `evolution-lane-pager-button${disabled ? " is-disabled" : ""}`,
    transform: `translate(${x} 169)`,
    "aria-disabled": String(disabled),
  });
  group.appendChild(svgElement("rect", {
    x: 0,
    y: 0,
    width: 22,
    height: 22,
    rx: 2,
    fill: "none",
    stroke: COLORS.line,
    "stroke-width": 0.75,
    "stroke-opacity": disabled ? 0.28 : 0.68,
  }));
  group.appendChild(svgElement("path", {
    d: direction < 0 ? "M13.5 6.5L9 11L13.5 15.5" : "M8.5 6.5L13 11L8.5 15.5",
    fill: "none",
    stroke: COLORS.line,
    "stroke-width": 1.1,
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    opacity: disabled ? 0.28 : 1,
  }));
  addTitle(group, label);
  if (!disabled) makeInteractive(group, label, onActivate);
  parent.appendChild(group);
}

function renderLanePager(parent, laneWindow, handlers) {
  if (!laneWindow || laneWindow.pageCount <= 1) return;
  const group = svgElement("g", { class: "evolution-lane-pager" });
  renderLanePagerButton(group, {
    x: 1492,
    direction: -1,
    disabled: laneWindow.page <= 1,
    onActivate: () => handlers.onLanePageChange?.(laneWindow.page - 1),
  });
  appendText(group, `关联 ${laneWindow.page}/${laneWindow.pageCount}`, {
    x: 1550,
    y: 184,
    class: "evolution-lane-pager-label",
    "text-anchor": "middle",
  });
  renderLanePagerButton(group, {
    x: 1586,
    direction: 1,
    disabled: laneWindow.page >= laneWindow.pageCount,
    onActivate: () => handlers.onLanePageChange?.(laneWindow.page + 1),
  });
  addTitle(
    group,
    `当前显示 ${laneWindow.visibleLanes} 条，共 ${laneWindow.totalLanes} 条轨道`,
  );
  parent.appendChild(group);
}

function renderMain(layer, layout, options) {
  const group = svgElement("g", {
    class: "evolution-main-layer",
    "clip-path": "url(#evolution-content-clip)",
  });
  const primaryFocus = options.focusEntities[0];
  const title = options.mode === "compare"
    ? "机构与官职演变对比"
    : `${shortened(primaryFocus?.title || "实体", 18)}演变`;
  appendText(group, title, { x: 535, y: 188, class: "evolution-view-heading" });
  appendText(group, options.mode === "compare"
    ? "共同时间尺度"
    : `${primaryFocus?.type || "实体"} · 单体及直接关联`, {
    x: 1770,
    y: 188,
    class: "evolution-view-subheading",
    "text-anchor": "end",
  });
  renderLanePager(group, layout.laneWindow, options.handlers);
  group.appendChild(svgElement("line", {
    x1: 535, y1: 202, x2: 1770, y2: 202, stroke: COLORS.line, "stroke-width": 0.72,
  }));
  if (!layout.lanes.length) {
    appendText(group, "当前对象没有可展示的宋代时间节点", {
      x: 1150, y: 500, class: "evolution-empty", "text-anchor": "middle",
    });
    layer.appendChild(group);
    return;
  }
  renderAxis(group, layout, options.selectedRange, options.selectionActive);
  renderEvolutionLegend(group, layout);
  const hasDrawableRelations = (layout.relations || []).some((relation) => relation.drawable)
    || (layout.relationGroups || []).some((relationGroup) => relationGroup.drawable);
  if (!hasDrawableRelations) {
    appendText(group, "当前对象暂无可定位的前后演变关系", {
      x: (layout.plotBounds.x + layout.plotBounds.right) / 2,
      y: layout.plotBounds.y + 76,
      class: "evolution-empty",
      "text-anchor": "middle",
    });
  }
  const selected = selectedKey(options.selectedItem);
  const eventsToRender = [];
  for (const lane of layout.lanes) {
    group.appendChild(svgElement("line", {
      x1: lane.trackStartX, y1: lane.y, x2: lane.trackEndX, y2: lane.y,
      stroke: COLORS.olive, "stroke-width": 0.65, "stroke-dasharray": "3 4", opacity: 0.45,
    }));
    for (const segment of lane.segments || []) {
      group.appendChild(svgElement("line", {
        x1: segment.startX, y1: segment.y, x2: segment.endX, y2: segment.y,
        stroke: COLORS.line, "stroke-width": 2.1,
        "stroke-dasharray": segment.inferredStart ? "5 3" : null,
        opacity: segment.inferredStart ? 0.68 : 1,
      }));
      if (!segment.openStart) {
        group.appendChild(svgElement("line", {
          x1: segment.startX, y1: segment.y - 7, x2: segment.startX, y2: segment.y + 7,
          stroke: COLORS.line, "stroke-width": 1,
        }));
      }
      if (!segment.openEnd) {
        group.appendChild(svgElement("line", {
          x1: segment.endX, y1: segment.y - 7, x2: segment.endX, y2: segment.y + 7,
          stroke: COLORS.line, "stroke-width": 1,
        }));
      }
    }
    renderLaneLabel(
      group,
      lane,
      lane.entityId === options.activeEntityId,
      options.handlers.onSelectEntity,
      layout.lanePitch,
    );
    for (const event of lane.events || []) {
      event.rangeStartX = event.yearStart == null ? event.baseX : (
        layout.yearScale.range[0]
          + (event.yearStart - layout.yearScale.domain[0])
            / Math.max(1, layout.yearScale.domain[1] - layout.yearScale.domain[0])
            * (layout.yearScale.range[1] - layout.yearScale.range[0])
      );
      event.rangeEndX = event.yearEnd == null ? event.baseX : (
        layout.yearScale.range[0]
          + (event.yearEnd - layout.yearScale.domain[0])
            / Math.max(1, layout.yearScale.domain[1] - layout.yearScale.domain[0])
            * (layout.yearScale.range[1] - layout.yearScale.range[0])
      );
      eventsToRender.push(event);
    }
  }

  const groupedRelationIds = new Set(layout.relationGroups.flatMap((item) => item.relationIds || []));
  const ungrouped = layout.relations.filter((relation) => !groupedRelationIds.has(relation.id));
  const { bundles, singles } = bundleRelations(ungrouped);
  for (const bundle of bundles) {
    renderRelationBundle(group, bundle, selected, options.handlers);
  }
  for (const relation of singles) {
    renderRelation(
      group,
      relation,
      selected === `relation:${relation.id}`,
      options.handlers,
    );
  }
  for (const relationGroup of layout.relationGroups) {
    renderRelationGroup(group, relationGroup, selected, options.handlers);
  }
  // Render the selected event last so its emphasis stays on top of
  // neighbouring marks instead of being painted over by them.
  const orderedEvents = [
    ...eventsToRender.filter((event) => selected !== `timepoint:${event.id}`),
    ...eventsToRender.filter((event) => selected === `timepoint:${event.id}`),
  ];
  for (const event of orderedEvents) {
    renderEventMark(
      group,
      event,
      selected === `timepoint:${event.id}`,
      options.handlers,
    );
  }
  renderOffAxis(group, layout, options.selectedItem, options.handlers);
  layer.appendChild(group);
}

/** Render the data-driven evolution layer into the unchanged 4-01 design SVG. */
export function renderEvolutionOverlay(svg, options) {
  svg.querySelector(".dynamic-evolution-layer")?.remove();
  ensureDefs(svg);
  const layer = svgElement("g", { class: "dynamic-evolution-layer" });
  layer.style.pointerEvents = "none";
  renderSelector(layer, options);
  renderMain(layer, options.layout, options);
  svg.appendChild(layer);
  return layer;
}
