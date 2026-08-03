import { buildYearSnapshot } from "/ch2t7-design-vis/src/utils/snapshot.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const STATUS_LABELS = {
  matched: "两边都有",
  "excel-only": "仅 Excel",
  "db-only": "仅数据库",
};

const els = {
  sourceStatus: document.querySelector("#sourceStatus"),
  yearInput: document.querySelector("#yearInput"),
  yearRange: document.querySelector("#yearRange"),
  yearLabel: document.querySelector("#yearLabel"),
  showInstitutions: document.querySelector("#showInstitutions"),
  showOffices: document.querySelector("#showOffices"),
  showMatched: document.querySelector("#showMatched"),
  showExcelOnly: document.querySelector("#showExcelOnly"),
  showDbOnly: document.querySelector("#showDbOnly"),
  searchInput: document.querySelector("#searchInput"),
  resetView: document.querySelector("#resetView"),
  kpiGrid: document.querySelector("#kpiGrid"),
  graphSummary: document.querySelector("#graphSummary"),
  viewport: document.querySelector("#graphViewport"),
  svg: document.querySelector("#comparisonGraph"),
  zoomLayer: document.querySelector("#zoomLayer"),
  zoomLabel: document.querySelector("#zoomLabel"),
  emptyState: document.querySelector("#emptyState"),
  detailTitle: document.querySelector("#detailTitle"),
  detailBody: document.querySelector("#detailBody"),
  differenceRows: document.querySelector("#differenceRows"),
};

const state = {
  excel: null,
  current: null,
  comparison: null,
  year: 1080,
  search: "",
  selected: null,
  collapsed: new Set(),
  zoom: { x: 24, y: 24, k: 1 },
  contentSize: { width: 1000, height: 600 },
};

function cleanName(value) {
  return String(value ?? "").replaceAll(/\s+/g, " ").trim();
}

function splitNames(value) {
  return String(value ?? "")
    .split(/[，、,；;\n]/)
    .map(cleanName)
    .filter(Boolean);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function nonEmpty(value) {
  return value !== null && value !== undefined && String(value).trim() !== "";
}

function mergeRecord(base, row, name, kind) {
  const next = { ...(base || {}), name, kind, change: row, row: row.__row };
  for (const [key, value] of Object.entries(row)) {
    if (nonEmpty(value)) next[key] = value;
  }
  return next;
}

function reduceExcelChanges(changes, year, kind) {
  const active = new Map();
  const originalField = kind === "institution" ? "原机构" : "原官职";
  const currentField = kind === "institution" ? "现机构" : "现官职";
  const ordered = changes
    .filter((row) => Number(row["开始-公元年份"]) <= year)
    .sort((a, b) => Number(a["开始-公元年份"]) - Number(b["开始-公元年份"]) || a.__row - b.__row);

  for (const row of ordered) {
    const type = cleanName(row["变更类型"]);
    const originals = splitNames(row[originalField]);
    const current = cleanName(row[currentField]);
    if (type === "取消") {
      originals.forEach((name) => active.delete(name));
      continue;
    }

    let inherited = null;
    for (const original of originals) {
      inherited ||= active.get(original) || null;
    }

    if (["移置", "并入", "合并", "打散"].includes(type)) {
      originals.filter((name) => name !== current).forEach((name) => active.delete(name));
    }

    if (!current) continue;
    const prior = active.get(current) || inherited;
    active.set(current, mergeRecord(prior, row, current, kind));
  }
  return active;
}

function makeEdge(parent, child, type, source, evidence = null) {
  return { parent, child, type, source, evidence };
}

function buildExcelSnapshot(excel, year) {
  const institutions = reduceExcelChanges(excel.institutionChanges, year, "institution");
  const offices = reduceExcelChanges(excel.officeChanges, year, "office");
  const staticOffices = new Map(excel.offices.map((row) => [cleanName(row["官职名"]), row]));
  const nodes = new Map();
  const edges = [];

  for (const [name, item] of institutions) nodes.set(name, { ...item, static: null });
  for (const [name, item] of offices) nodes.set(name, { ...item, static: staticOffices.get(name) || null });

  for (const [name, item] of institutions) {
    for (const parent of splitNames(item["新上级机构"])) {
      if (institutions.has(parent)) edges.push(makeEdge(parent, name, "hierarchy", "excel", item));
    }
    for (const child of splitNames(item["新下级机构"])) {
      if (institutions.has(child)) edges.push(makeEdge(name, child, "hierarchy", "excel", item));
    }
  }

  for (const [name, item] of offices) {
    const staticRow = staticOffices.get(name);
    for (const parent of splitNames(staticRow?.["隶属机构"])) {
      if (institutions.has(parent)) edges.push(makeEdge(parent, name, "staff", "excel", item));
    }
  }

  return { nodes, edges: dedupeEdges(edges) };
}

function dedupeEdges(edges) {
  const result = new Map();
  for (const edge of edges) {
    const key = `${edge.type}|${edge.parent}|${edge.child}`;
    if (!result.has(key)) result.set(key, edge);
  }
  return [...result.values()];
}

function buildCurrentSnapshot(raw, excel, year) {
  const snapshot = buildYearSnapshot(raw, year);
  const entityById = new Map(raw.entities.map((entity) => [entity.id, entity]));
  const activeIds = snapshot.entityIds;
  const excelNames = new Set([
    ...excel.institutions.map((row) => cleanName(row["机构名"])),
    ...excel.offices.map((row) => cleanName(row["官职名"])),
    "皇帝",
  ]);
  const rootIds = raw.entities.filter((entity) => entity.title === "尚书省" && activeIds.has(entity.id)).map((entity) => entity.id);
  const hierarchyChildren = new Map();
  for (const edge of snapshot.hierarchyEdges) {
    if (!hierarchyChildren.has(edge.parent)) hierarchyChildren.set(edge.parent, []);
    hierarchyChildren.get(edge.parent).push(edge.child);
  }

  const scopeIds = new Set(rootIds);
  const queue = [...rootIds];
  while (queue.length) {
    const id = queue.shift();
    for (const child of hierarchyChildren.get(id) || []) {
      if (!scopeIds.has(child)) {
        scopeIds.add(child);
        queue.push(child);
      }
    }
  }
  for (const entity of raw.entities) {
    if (activeIds.has(entity.id) && excelNames.has(cleanName(entity.title))) scopeIds.add(entity.id);
  }
  for (const edge of snapshot.staffEdges) {
    if (scopeIds.has(edge.org)) scopeIds.add(edge.official);
  }

  const nodes = new Map();
  for (const id of scopeIds) {
    const entity = entityById.get(id);
    if (!entity || !activeIds.has(id)) continue;
    const name = cleanName(entity.title);
    const current = snapshot.currentTimepointByEntity.get(id) || null;
    if (!nodes.has(name)) nodes.set(name, { name, kind: entity.type === "机构" ? "institution" : "office", ids: [], current: [] });
    nodes.get(name).ids.push(id);
    if (current) nodes.get(name).current.push(current);
  }

  const edges = [];
  for (const edge of snapshot.hierarchyEdges) {
    const parent = cleanName(entityById.get(edge.parent)?.title);
    const child = cleanName(entityById.get(edge.child)?.title);
    if (nodes.has(parent) && nodes.has(child)) edges.push(makeEdge(parent, child, "hierarchy", "database", edge));
  }
  for (const edge of snapshot.staffEdges) {
    const parent = cleanName(entityById.get(edge.org)?.title);
    const child = cleanName(entityById.get(edge.official)?.title);
    if (nodes.has(parent) && nodes.has(child)) edges.push(makeEdge(parent, child, "staff", "database", edge));
  }
  return { nodes, edges: dedupeEdges(edges), snapshot };
}

function compareSnapshots(excelSnapshot, dbSnapshot) {
  const names = new Set([...excelSnapshot.nodes.keys(), ...dbSnapshot.nodes.keys()]);
  const nodes = new Map();
  for (const name of names) {
    const excel = excelSnapshot.nodes.get(name) || null;
    const database = dbSnapshot.nodes.get(name) || null;
    nodes.set(name, {
      name,
      kind: excel?.kind || database?.kind || "institution",
      status: excel && database ? "matched" : excel ? "excel-only" : "db-only",
      excel,
      database,
    });
  }

  const edgeMap = new Map();
  const addEdges = (edges, source) => {
    for (const edge of edges) {
      const key = `${edge.type}|${edge.parent}|${edge.child}`;
      if (!edgeMap.has(key)) edgeMap.set(key, { ...edge, excel: null, database: null });
      edgeMap.get(key)[source] = edge;
    }
  };
  addEdges(excelSnapshot.edges, "excel");
  addEdges(dbSnapshot.edges, "database");
  const edges = [...edgeMap.values()].map((edge) => ({
    ...edge,
    status: edge.excel && edge.database ? "matched" : edge.excel ? "excel-only" : "db-only",
  }));
  return { nodes, edges, excelSnapshot, dbSnapshot };
}

function visibleStatus(status) {
  return status === "matched" ? els.showMatched.checked : status === "excel-only" ? els.showExcelOnly.checked : els.showDbOnly.checked;
}

function visibleNode(node) {
  return visibleStatus(node.status) && (node.kind === "institution" ? els.showInstitutions.checked : els.showOffices.checked);
}

function parentMap(edges) {
  const result = new Map();
  for (const edge of edges) {
    if (!result.has(edge.child)) result.set(edge.child, []);
    result.get(edge.child).push(edge.parent);
  }
  return result;
}

function renderKpis(comparison) {
  const all = [...comparison.nodes.values()];
  const edgeStatuses = comparison.edges.reduce((acc, edge) => {
    acc[edge.status] = (acc[edge.status] || 0) + 1;
    return acc;
  }, {});
  const cards = [
    ["Excel 当年节点", all.filter((node) => node.excel).length, ""],
    ["数据库当年节点", all.filter((node) => node.database).length, ""],
    ["正式名称一致", all.filter((node) => node.status === "matched").length, "matched"],
    ["仅 Excel", all.filter((node) => node.status === "excel-only").length, "excel-only"],
    ["仅数据库", all.filter((node) => node.status === "db-only").length, "db-only"],
    ["关系不一致", (edgeStatuses["excel-only"] || 0) + (edgeStatuses["db-only"] || 0), ""],
  ];
  els.kpiGrid.innerHTML = cards.map(([label, value, klass]) => `
    <article class="kpi-card ${klass}"><span class="kpi-label">${label}</span><strong class="kpi-value">${value}</strong></article>
  `).join("");
}

function choosePrimaryEdges(nodes, edges) {
  const incoming = new Map();
  for (const edge of edges) {
    if (!nodes.has(edge.parent) || !nodes.has(edge.child) || edge.parent === edge.child) continue;
    if (!incoming.has(edge.child)) incoming.set(edge.child, []);
    incoming.get(edge.child).push(edge);
  }
  const rank = (edge) => (edge.status === "matched" ? 0 : 10) + (edge.type === "hierarchy" ? 0 : 3) + (edge.parent === "皇帝" ? -2 : 0);
  const chosen = [];
  for (const candidates of incoming.values()) chosen.push(candidates.sort((a, b) => rank(a) - rank(b) || a.parent.localeCompare(b.parent, "zh-CN"))[0]);
  return chosen;
}

function layoutGraph(nodes, edges) {
  const primary = choosePrimaryEdges(nodes, edges);
  const parentOf = new Map(primary.map((edge) => [edge.child, edge.parent]));
  const children = new Map();
  for (const edge of primary) {
    if (!children.has(edge.parent)) children.set(edge.parent, []);
    children.get(edge.parent).push(edge.child);
  }
  for (const values of children.values()) values.sort((a, b) => a.localeCompare(b, "zh-CN"));

  const roots = [...nodes.keys()].filter((name) => !parentOf.has(name));
  roots.sort((a, b) => (a === "皇帝" ? -1 : b === "皇帝" ? 1 : a === "尚书省" ? -1 : b === "尚书省" ? 1 : a.localeCompare(b, "zh-CN")));
  const positions = new Map();
  const shownNames = new Set();
  let cursorY = 42;
  let maxDepth = 0;

  const place = (name, depth, ancestry = new Set()) => {
    if (shownNames.has(name) || ancestry.has(name)) return positions.get(name)?.y ?? cursorY;
    shownNames.add(name);
    maxDepth = Math.max(maxDepth, depth);
    const nextAncestry = new Set(ancestry).add(name);
    const visibleChildren = state.collapsed.has(name) ? [] : (children.get(name) || []).filter((child) => nodes.has(child));
    let y;
    if (!visibleChildren.length) {
      y = cursorY;
      cursorY += 54;
    } else {
      const ys = visibleChildren.map((child) => place(child, depth + 1, nextAncestry));
      y = (Math.min(...ys) + Math.max(...ys)) / 2;
    }
    positions.set(name, { x: 58 + depth * 250, y, depth, hasChildren: (children.get(name) || []).length > 0 });
    return y;
  };

  for (const root of roots) {
    place(root, 0);
    cursorY += 28;
  }
  for (const name of nodes.keys()) if (!shownNames.has(name)) place(name, 0);

  const shownEdges = primary.filter((edge) => positions.has(edge.parent) && positions.has(edge.child));
  return {
    positions,
    primaryEdges: shownEdges,
    width: Math.max(760, 58 + (maxDepth + 1) * 250),
    height: Math.max(560, cursorY + 30),
  };
}

function svgElement(tag, attrs = {}) {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, value);
  return element;
}

function edgePath(source, target) {
  const sx = source.x + 178;
  const sy = source.y;
  const tx = target.x;
  const ty = target.y;
  const bend = Math.max(42, (tx - sx) * 0.48);
  return `M${sx},${sy} C${sx + bend},${sy} ${tx - bend},${ty} ${tx},${ty}`;
}

function applyZoom() {
  const { x, y, k } = state.zoom;
  els.zoomLayer.setAttribute("transform", `translate(${x} ${y}) scale(${k})`);
  els.zoomLabel.textContent = `${Math.round(k * 100)}%`;
}

function resetZoom() {
  const rect = els.viewport.getBoundingClientRect();
  const k = Math.min(1, Math.max(0.26, Math.min((rect.width - 44) / state.contentSize.width, (rect.height - 44) / state.contentSize.height)));
  state.zoom = { x: 24, y: 24, k };
  applyZoom();
}

function renderGraph(comparison, { reset = false } = {}) {
  const nodes = new Map([...comparison.nodes].filter(([, node]) => visibleNode(node)));
  const edges = comparison.edges.filter((edge) => visibleStatus(edge.status) && nodes.has(edge.parent) && nodes.has(edge.child));
  const layout = layoutGraph(nodes, edges);
  state.contentSize = { width: layout.width, height: layout.height };
  els.zoomLayer.replaceChildren();
  els.emptyState.hidden = nodes.size > 0;
  els.graphSummary.textContent = `${nodes.size} 个节点，${layout.primaryEdges.length} 条主层级边；双击可折叠下级。`;

  for (const edge of layout.primaryEdges) {
    const source = layout.positions.get(edge.parent);
    const target = layout.positions.get(edge.child);
    els.zoomLayer.append(svgElement("path", { d: edgePath(source, target), class: `graph-edge ${edge.status}` }));
  }

  const query = cleanName(state.search).toLowerCase();
  for (const [name, node] of nodes) {
    const position = layout.positions.get(name);
    if (!position) continue;
    const width = 178;
    const height = node.kind === "institution" ? 38 : 32;
    const group = svgElement("g", {
      class: `graph-node ${node.kind} ${node.status}${query && name.toLowerCase().includes(query) ? " search-match" : ""}${state.selected === name ? " selected" : ""}`,
      transform: `translate(${position.x} ${position.y - height / 2})`,
      tabindex: "0",
      role: "button",
      "aria-label": `${name}，${STATUS_LABELS[node.status]}`,
    });
    group.append(svgElement("rect", { width, height }));
    const label = svgElement("text", { x: 12, y: height / 2 + 4 });
    label.textContent = name.length > 15 ? `${name.slice(0, 14)}…` : name;
    group.append(label);
    const meta = svgElement("text", { class: "node-meta", x: width - 10, y: height - 7, "text-anchor": "end" });
    meta.textContent = node.kind === "institution" ? "机构" : "官职";
    group.append(meta);
    if (position.hasChildren) {
      const mark = svgElement("circle", { class: "collapse-mark", cx: width, cy: height / 2, r: 8 });
      const symbol = svgElement("text", { class: "collapse-symbol", x: width, y: height / 2 + 0.5 });
      symbol.textContent = state.collapsed.has(name) ? "+" : "−";
      group.append(mark, symbol);
    }
    group.addEventListener("click", (event) => {
      event.stopPropagation();
      state.selected = name;
      renderDetails(node, comparison);
      renderGraph(comparison);
    });
    group.addEventListener("dblclick", (event) => {
      event.preventDefault();
      event.stopPropagation();
      state.collapsed.has(name) ? state.collapsed.delete(name) : state.collapsed.add(name);
      renderGraph(comparison, { reset: true });
    });
    els.zoomLayer.append(group);
  }
  applyZoom();
  if (reset) requestAnimationFrame(resetZoom);
}

function renderDetails(node, comparison) {
  els.detailTitle.textContent = node.name;
  const excelParents = parentMap(comparison.excelSnapshot.edges).get(node.name) || [];
  const dbParents = parentMap(comparison.dbSnapshot.edges).get(node.name) || [];
  const excel = node.excel;
  const database = node.database;
  const excelEvidence = excel?.["新职能"] || excel?.["职掌"] || excel?.static?.["职源与沿革文本"] || "";
  const dbCurrent = database?.current?.[0] || null;
  els.detailBody.innerHTML = `
    <p><span class="status-chip ${node.status}">${STATUS_LABELS[node.status]}</span><span class="status-chip">${node.kind === "institution" ? "机构" : "官职"}</span></p>
    <div class="detail-section">
      <h3>Excel</h3>
      ${excel ? `
        <p>动态表第 ${escapeHtml(excel.row)} 行 · ${escapeHtml(excel["开始-时间"] || excel["开始-公元年份"])} · ${escapeHtml(excel["变更类型"])}</p>
        <p><strong>上级：</strong>${escapeHtml(excelParents.join("、") || "未记录")}</p>
        ${excelEvidence ? `<p class="detail-quote">${escapeHtml(excelEvidence)}</p>` : ""}
      ` : "<p>这一年 Excel 中没有该节点。</p>"}
    </div>
    <div class="detail-section">
      <h3>当前 ch2t7 数据库</h3>
      ${database ? `
        <p><strong>实体 ID：</strong>${escapeHtml(database.ids.join("、"))}</p>
        <p><strong>上级：</strong>${escapeHtml(dbParents.join("、") || "未记录")}</p>
        ${dbCurrent ? `<p><strong>${escapeHtml(dbCurrent.time)}</strong><br>${escapeHtml(dbCurrent.event)}</p>${dbCurrent.quotation ? `<p class="detail-quote">${escapeHtml(dbCurrent.quotation)}</p>` : ""}` : "<p>该截面没有可显示的当前时间点。</p>"}
      ` : "<p>这一年当前数据库中没有该节点。</p>"}
    </div>
  `;
}

function renderDifferenceTable(comparison) {
  const query = cleanName(state.search).toLowerCase();
  const excelParents = parentMap(comparison.excelSnapshot.edges);
  const dbParents = parentMap(comparison.dbSnapshot.edges);
  const rows = [...comparison.nodes.values()]
    .filter(visibleNode)
    .filter((node) => !query || node.name.toLowerCase().includes(query))
    .sort((a, b) => ({ "excel-only": 0, "db-only": 1, matched: 2 }[a.status] - ({ "excel-only": 0, "db-only": 1, matched: 2 }[b.status]) || a.name.localeCompare(b.name, "zh-CN"));
  els.differenceRows.innerHTML = rows.slice(0, 500).map((node) => {
    const current = node.database?.current?.[0];
    return `<tr data-name="${escapeHtml(node.name)}">
      <td class="table-status ${node.status}">${STATUS_LABELS[node.status]}</td>
      <td>${node.kind === "institution" ? "机构" : "官职"}</td>
      <td>${escapeHtml(node.name)}</td>
      <td>${escapeHtml((excelParents.get(node.name) || []).join("、") || "—")}</td>
      <td>${escapeHtml((dbParents.get(node.name) || []).join("、") || "—")}</td>
      <td>${escapeHtml(current ? `${current.time}：${current.event}` : "—")}</td>
    </tr>`;
  }).join("");
  els.differenceRows.querySelectorAll("tr").forEach((row) => row.addEventListener("click", () => {
    const node = comparison.nodes.get(row.dataset.name);
    if (!node) return;
    state.selected = node.name;
    renderDetails(node, comparison);
    renderGraph(comparison);
  }));
}

function rebuildComparison({ reset = true } = {}) {
  if (!state.excel || !state.current) return;
  const excelSnapshot = buildExcelSnapshot(state.excel, state.year);
  const dbSnapshot = buildCurrentSnapshot(state.current, state.excel, state.year);
  state.comparison = compareSnapshots(excelSnapshot, dbSnapshot);
  renderKpis(state.comparison);
  renderGraph(state.comparison, { reset });
  renderDifferenceTable(state.comparison);
  if (state.selected && state.comparison.nodes.has(state.selected)) renderDetails(state.comparison.nodes.get(state.selected), state.comparison);
}

function bindControls() {
  const setYear = (value) => {
    state.year = Math.max(960, Math.min(1279, Number(value) || 1080));
    els.yearInput.value = state.year;
    els.yearRange.value = state.year;
    els.yearLabel.textContent = state.year;
    state.collapsed.clear();
    rebuildComparison({ reset: true });
  };
  els.yearInput.addEventListener("change", (event) => setYear(event.target.value));
  els.yearRange.addEventListener("input", (event) => setYear(event.target.value));
  for (const checkbox of [els.showInstitutions, els.showOffices, els.showMatched, els.showExcelOnly, els.showDbOnly]) checkbox.addEventListener("change", () => rebuildComparison({ reset: true }));
  els.searchInput.addEventListener("input", (event) => {
    state.search = event.target.value;
    if (state.comparison) {
      renderGraph(state.comparison);
      renderDifferenceTable(state.comparison);
    }
  });
  els.resetView.addEventListener("click", resetZoom);
}

function bindPanZoom() {
  let drag = null;
  els.viewport.addEventListener("wheel", (event) => {
    event.preventDefault();
    const rect = els.viewport.getBoundingClientRect();
    const px = event.clientX - rect.left;
    const py = event.clientY - rect.top;
    const nextK = Math.max(0.18, Math.min(2.6, state.zoom.k * Math.exp(-event.deltaY * 0.0012)));
    const ratio = nextK / state.zoom.k;
    state.zoom.x = px - (px - state.zoom.x) * ratio;
    state.zoom.y = py - (py - state.zoom.y) * ratio;
    state.zoom.k = nextK;
    applyZoom();
  }, { passive: false });
  els.viewport.addEventListener("pointerdown", (event) => {
    if (event.target.closest?.(".graph-node")) return;
    drag = { x: event.clientX, y: event.clientY, startX: state.zoom.x, startY: state.zoom.y };
    els.viewport.classList.add("dragging");
    els.viewport.setPointerCapture(event.pointerId);
  });
  els.viewport.addEventListener("pointermove", (event) => {
    if (!drag) return;
    state.zoom.x = drag.startX + event.clientX - drag.x;
    state.zoom.y = drag.startY + event.clientY - drag.y;
    applyZoom();
  });
  const finishDrag = () => { drag = null; els.viewport.classList.remove("dragging"); };
  els.viewport.addEventListener("pointerup", finishDrag);
  els.viewport.addEventListener("pointercancel", finishDrag);
}

async function load() {
  bindControls();
  bindPanZoom();
  try {
    const [excelResponse, currentResponse, metaResponse] = await Promise.all([
      fetch("./excel_data.json", { cache: "no-store" }),
      fetch("/api/current-data", { cache: "no-store" }),
      fetch("/api/meta", { cache: "no-store" }),
    ]);
    if (!excelResponse.ok || !currentResponse.ok) throw new Error("数据接口返回失败");
    [state.excel, state.current] = await Promise.all([excelResponse.json(), currentResponse.json()]);
    const meta = metaResponse.ok ? await metaResponse.json() : null;
    els.sourceStatus.textContent = meta ? `Excel：${state.excel.institutions.length}机构 / ${state.excel.offices.length}官职 · 数据库实时读取` : "两套数据已载入";
    rebuildComparison({ reset: true });
  } catch (error) {
    console.error(error);
    els.sourceStatus.textContent = `载入失败：${error.message}`;
    els.emptyState.hidden = false;
    els.emptyState.textContent = "无法载入数据，请确认通过本目录 server.py 启动。";
  }
}

load();
