const DATA_FILES = {
  summary: "data/summary.json",
  entities: "data/entities.json",
  timepoints: "data/timepoints.json",
  relationships: "data/relationships.json",
  citations: "data/citations.json",
  dictionary: "data/dictionary.json",
};

const COLORS = {
  机构: "#0f766e",
  官职: "#4f46e5",
  unknown: "#b7791f",
  evidence: "#5b7f62",
  relation: "#50606b",
};

const RELATION_COLORS = {
  上下级机构: "#0f766e",
  编制隶属: "#4f46e5",
  前后演变: "#b7791f",
  统称与实例: "#8b5cf6",
};

const state = {
  data: null,
  activeView: "overview",
  selectedEntityId: null,
  selectedRelationshipId: null,
  filters: {
    search: "",
    type: "all",
    relation: "all",
  },
};

const els = {
  sourceLine: document.querySelector("#sourceLine"),
  globalSearch: document.querySelector("#globalSearch"),
  typeFilter: document.querySelector("#typeFilter"),
  relationFilter: document.querySelector("#relationFilter"),
  metricCards: document.querySelector("#metricCards"),
  entityList: document.querySelector("#entityList"),
  entityCountLabel: document.querySelector("#entityCountLabel"),
  entityDetail: document.querySelector("#entityDetail"),
  dictionaryDetail: document.querySelector("#dictionaryDetail"),
  networkStatus: document.querySelector("#networkStatus"),
  networkDetail: document.querySelector("#networkDetail"),
  timelineDetail: document.querySelector("#timelineDetail"),
  toast: document.querySelector("#toast"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function short(value, length = 120) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > length ? `${text.slice(0, length)}...` : text;
}

function badge(label, kind = "") {
  return `<span class="badge ${kind}">${escapeHtml(label)}</span>`;
}

function typeBadge(type) {
  return badge(type, type === "机构" ? "org" : "office");
}

async function loadData() {
  const entries = await Promise.all(
    Object.entries(DATA_FILES).map(async ([key, path]) => [key, await d3.json(path)])
  );
  const data = Object.fromEntries(entries);
  indexData(data);
  state.data = data;
  state.selectedEntityId = data.entities[0]?.id ?? null;
}

function indexData(data) {
  data.entityById = new Map(data.entities.map((entity) => [entity.id, entity]));
  data.timepointsByEntity = d3.group(data.timepoints, (timepoint) => timepoint.entity_id);
  data.relationshipById = new Map(data.relationships.map((relationship) => [relationship.id, relationship]));
  data.relationshipsByEntity = new Map();
  for (const relationship of data.relationships) {
    for (const id of [relationship.subject_entity_id, relationship.object_entity_id]) {
      if (!data.relationshipsByEntity.has(id)) data.relationshipsByEntity.set(id, []);
      data.relationshipsByEntity.get(id).push(relationship);
    }
  }
  data.citationsByTimepoint = d3.group(
    data.citations.filter((citation) => citation.target_table === "Timepoints"),
    (citation) => citation.target_id
  );
  data.citationsByRelationship = d3.group(
    data.citations.filter((citation) => citation.target_table === "Relationships"),
    (citation) => citation.target_id
  );
  data.dictionaryByTitle = d3.group(data.dictionary, (entry) => entry.title);
}

function setupControls() {
  for (const type of Object.keys(state.data.summary.relationship_type_counts).sort()) {
    els.relationFilter.insertAdjacentHTML("beforeend", `<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`);
  }
  els.globalSearch.addEventListener("input", () => {
    state.filters.search = els.globalSearch.value;
    renderCurrentView();
  });
  els.typeFilter.addEventListener("change", () => {
    state.filters.type = els.typeFilter.value;
    renderCurrentView();
  });
  els.relationFilter.addEventListener("change", () => {
    state.filters.relation = els.relationFilter.value;
    renderCurrentView();
  });

  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = button.dataset.view;
      document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab === button));
      document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === state.activeView));
      renderCurrentView();
    });
  });
}

function filteredEntities() {
  const search = state.filters.search.trim().toLowerCase();
  return state.data.entities.filter((entity) => {
    if (state.filters.type !== "all" && entity.type !== state.filters.type) return false;
    if (!search) return true;
    const dictionaryText = (state.data.dictionaryByTitle.get(entity.title) || [])
      .map((entry) => `${entry.title} ${entry.text_summary}`)
      .join(" ");
    const relationText = (state.data.relationshipsByEntity.get(entity.id) || [])
      .map((relationship) => `${relationship.relation_type} ${relationship.subject_entity_title} ${relationship.object_entity_title}`)
      .join(" ");
    return `${entity.id} ${entity.title} ${entity.type} ${dictionaryText} ${relationText}`.toLowerCase().includes(search);
  });
}

function renderCurrentView() {
  if (state.activeView === "overview") renderOverview();
  if (state.activeView === "entities") renderEntities();
  if (state.activeView === "network") renderNetwork();
  if (state.activeView === "timeline") renderTimeline();
}

function renderAll() {
  const { summary } = state.data;
  els.sourceLine.textContent = `输出库：${summary.source.entry_db}；辞典库：${summary.source.dictionary_db}`;
  renderOverview();
  renderEntities();
  renderNetwork();
  renderTimeline();
}

function renderOverview() {
  const { summary } = state.data;
  const cards = [
    ["实体", summary.counts.Entities],
    ["时间点", summary.counts.Timepoints],
    ["关系", summary.counts.Relationships],
    ["引用", summary.counts.Citations],
    ["辞典条目", summary.counts.DictionaryEntries],
    ["辞典唯一标题", summary.counts.DictionaryUniqueTitles],
    ["占位时间点", summary.placeholder_timepoints],
  ];
  els.metricCards.innerHTML = cards.map(([label, value]) => `
    <article class="metric-card">
      <div class="label">${escapeHtml(label)}</div>
      <div class="value">${Number(value).toLocaleString("zh-CN")}</div>
    </article>
  `).join("");
  drawBarChart("#entityTypeChart", summary.entity_type_counts, (key) => COLORS[key] || COLORS.relation);
  drawBarChart("#relationTypeChart", summary.relationship_type_counts, (key) => RELATION_COLORS[key] || COLORS.relation);
  drawBarChart("#structureChart", {
    实体: summary.counts.Entities,
    时间点: summary.counts.Timepoints,
    关系: summary.counts.Relationships,
    引用: summary.counts.Citations,
    辞典条目: summary.counts.DictionaryEntries,
    占位时间点: summary.placeholder_timepoints,
  }, () => COLORS.evidence, { horizontal: true });
}

function drawBarChart(selector, obj, colorFn, options = {}) {
  const svg = d3.select(selector);
  const node = svg.node();
  const width = node.clientWidth || 600;
  const height = node.clientHeight || 280;
  svg.selectAll("*").remove();
  const data = Object.entries(obj).map(([key, value]) => ({ key, value: Number(value) }));
  const margin = { top: 18, right: 24, bottom: options.horizontal ? 28 : 74, left: options.horizontal ? 120 : 48 };

  if (options.horizontal) {
    const x = d3.scaleLinear().domain([0, d3.max(data, (d) => d.value) || 1]).nice().range([margin.left, width - margin.right]);
    const y = d3.scaleBand().domain(data.map((d) => d.key)).range([margin.top, height - margin.bottom]).padding(0.22);
    svg.append("g").attr("transform", `translate(0,${height - margin.bottom})`).call(d3.axisBottom(x).ticks(5));
    svg.append("g").attr("transform", `translate(${margin.left},0)`).call(d3.axisLeft(y).tickSize(0));
    svg.selectAll("rect").data(data).join("rect")
      .attr("x", margin.left)
      .attr("y", (d) => y(d.key))
      .attr("width", (d) => Math.max(1, x(d.value) - margin.left))
      .attr("height", y.bandwidth())
      .attr("rx", 4)
      .attr("fill", (d) => colorFn(d.key));
    svg.selectAll(".value-label").data(data).join("text")
      .attr("x", (d) => x(d.value) + 6)
      .attr("y", (d) => y(d.key) + y.bandwidth() / 2 + 4)
      .text((d) => d.value);
    return;
  }

  const x = d3.scaleBand().domain(data.map((d) => d.key)).range([margin.left, width - margin.right]).padding(0.24);
  const y = d3.scaleLinear().domain([0, d3.max(data, (d) => d.value) || 1]).nice().range([height - margin.bottom, margin.top]);
  svg.append("g").attr("transform", `translate(0,${height - margin.bottom})`).call(d3.axisBottom(x)).selectAll("text")
    .attr("transform", "rotate(-32)")
    .attr("text-anchor", "end");
  svg.append("g").attr("transform", `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(5));
  svg.selectAll("rect").data(data).join("rect")
    .attr("x", (d) => x(d.key))
    .attr("y", (d) => y(d.value))
    .attr("width", x.bandwidth())
    .attr("height", (d) => height - margin.bottom - y(d.value))
    .attr("rx", 4)
    .attr("fill", (d) => colorFn(d.key));
}

function renderEntities() {
  const entities = filteredEntities();
  if (!entities.some((entity) => entity.id === state.selectedEntityId)) {
    state.selectedEntityId = entities[0]?.id ?? state.selectedEntityId;
  }
  els.entityCountLabel.textContent = `${entities.length} 个`;
  els.entityList.innerHTML = entities.slice(0, 700).map((entity) => `
    <div class="entity-row ${entity.id === state.selectedEntityId ? "active" : ""}" data-id="${entity.id}">
      <div class="entity-id">#${entity.id}</div>
      <div>
        <div class="entity-title">${escapeHtml(entity.title)}</div>
        <div class="badges">${typeBadge(entity.type)}${badge(`时间点 ${entity.timepoint_count}`)}${badge(`关系 ${entity.relationship_count}`)}</div>
      </div>
    </div>
  `).join("");
  els.entityList.querySelectorAll(".entity-row").forEach((row) => {
    row.addEventListener("click", () => selectEntity(Number(row.dataset.id)));
  });
  renderEntityDetail();
}

function selectEntity(id) {
  state.selectedEntityId = id;
  renderEntities();
  if (state.activeView === "network") renderNetwork();
  if (state.activeView === "timeline") renderTimeline();
}

function renderEntityDetail() {
  const entity = state.data.entityById.get(state.selectedEntityId);
  if (!entity) {
    els.entityDetail.innerHTML = `<p class="small-muted">没有匹配实体。</p>`;
    els.dictionaryDetail.innerHTML = "";
    return;
  }
  const timepoints = state.data.timepointsByEntity.get(entity.id) || [];
  const relationships = state.data.relationshipsByEntity.get(entity.id) || [];
  els.entityDetail.innerHTML = `
    <div class="entity-heading">
      <div>
        <h3>#${entity.id} ${escapeHtml(entity.title)}</h3>
        <div class="badges">${typeBadge(entity.type)}${badge(`时间点 ${timepoints.length}`)}${badge(`关系 ${relationships.length}`)}${badge(`引用 ${entity.citation_count}`)}</div>
      </div>
    </div>
    <h3>时间点</h3>
    ${timepoints.map(renderTimepointCard).join("") || `<p class="small-muted">无时间点。</p>`}
    <h3>相关关系</h3>
    ${relationships.slice(0, 80).map(renderRelationCard).join("") || `<p class="small-muted">无关系。</p>`}
  `;
  renderDictionaryDetail(entity);
}

function renderTimepointCard(timepoint) {
  return `
    <article class="timepoint-card ${timepoint.is_placeholder ? "placeholder" : ""}">
      <strong>#${timepoint.id} ${escapeHtml(timepoint.time || "无时间")}</strong>
      <div class="small-muted">事件：${escapeHtml(timepoint.event || "")}；prev=${timepoint.prev_id ?? "NULL"}；succ=${timepoint.succ_id ?? "NULL"}</div>
      <div class="small-muted">属性：${escapeHtml([timepoint.attr_category, timepoint.attr_officer_type, timepoint.attr_grade].filter(Boolean).join(" / ") || "无")}</div>
      <div class="badges">${badge(`引用 ${timepoint.citation_count}`)}${timepoint.is_placeholder ? badge("占位/未知", "unknown") : ""}</div>
    </article>
  `;
}

function renderRelationCard(relationship) {
  return `
    <article class="relation-card" data-relation-id="${relationship.id}">
      <strong>#${relationship.id} ${escapeHtml(relationship.relation_type)}</strong>
      <div class="small-muted">${escapeHtml(relationship.subject_entity_title)} → ${escapeHtml(relationship.object_entity_title)}</div>
      <div class="small-muted">引用 ${relationship.citation_count}</div>
    </article>
  `;
}

function renderDictionaryDetail(entity) {
  const entries = state.data.dictionaryByTitle.get(entity.title) || [];
  els.dictionaryDetail.innerHTML = `
    <h3>同名辞典条目</h3>
    ${entries.map((entry) => `
      <article class="dict-card">
        <strong>#${entry.id} ${escapeHtml(entry.title)} · p${escapeHtml(entry.page)}</strong>
        <div class="small-muted">${escapeHtml(entry.catalog)}</div>
        <p>${escapeHtml(entry.text_summary)}</p>
      </article>
    `).join("") || `<p class="small-muted">没有同名辞典条目。</p>`}
  `;
}

function relationPassesFilter(relationship) {
  if (state.filters.relation !== "all" && relationship.relation_type !== state.filters.relation) return false;
  if (state.filters.type !== "all" && relationship.subject_entity_type !== state.filters.type && relationship.object_entity_type !== state.filters.type) return false;
  return true;
}

function buildNetworkSubset() {
  const filteredIds = new Set(filteredEntities().map((entity) => entity.id));
  const hasFocusedFilter = state.filters.search.trim() || state.filters.type !== "all";
  let links = state.data.relationships.filter(relationPassesFilter);

  if (state.selectedEntityId && !hasFocusedFilter) {
    links = links.filter((relationship) => relationship.subject_entity_id === state.selectedEntityId || relationship.object_entity_id === state.selectedEntityId);
  }
  if (hasFocusedFilter) {
    links = links.filter((relationship) => filteredIds.has(relationship.subject_entity_id) || filteredIds.has(relationship.object_entity_id));
  }
  if (!links.length) links = state.data.relationships.filter(relationPassesFilter).slice(0, 160);
  links = links.slice(0, 420);

  const nodeIds = new Set();
  links.forEach((relationship) => {
    nodeIds.add(relationship.subject_entity_id);
    nodeIds.add(relationship.object_entity_id);
  });
  if (state.selectedEntityId) nodeIds.add(state.selectedEntityId);
  const nodes = Array.from(nodeIds)
    .map((id) => state.data.entityById.get(id))
    .filter(Boolean)
    .slice(0, 240)
    .map((entity) => ({ id: entity.id, title: entity.title, type: entity.type }));
  const allowedIds = new Set(nodes.map((node) => node.id));
  return {
    nodes,
    links: links.filter((relationship) => allowedIds.has(relationship.subject_entity_id) && allowedIds.has(relationship.object_entity_id)),
  };
}

function renderNetwork() {
  const subset = buildNetworkSubset();
  els.networkStatus.textContent = `${subset.nodes.length} 节点 / ${subset.links.length} 边`;
  drawNetwork(subset);
  renderNetworkDetail();
}

function drawNetwork({ nodes, links }) {
  const svg = d3.select("#networkGraph");
  const node = svg.node();
  const width = node.clientWidth || 800;
  const height = node.clientHeight || 650;
  svg.selectAll("*").remove();
  const g = svg.append("g");
  svg.call(d3.zoom().scaleExtent([0.35, 4]).on("zoom", (event) => g.attr("transform", event.transform)));

  const simLinks = links.map((relationship) => ({
    ...relationship,
    source: relationship.subject_entity_id,
    target: relationship.object_entity_id,
  }));
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(simLinks).id((d) => d.id).distance(90).strength(0.38))
    .force("charge", d3.forceManyBody().strength(-230))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius((d) => 13 + Math.min(8, d.title.length / 4)));

  const link = g.append("g").selectAll("line").data(simLinks).join("line")
    .attr("class", (d) => `link ${d.id === state.selectedRelationshipId ? "active" : ""}`)
    .attr("stroke", (d) => RELATION_COLORS[d.relation_type] || COLORS.relation)
    .attr("stroke-width", 1.5)
    .on("click", (event, d) => {
      event.stopPropagation();
      state.selectedRelationshipId = d.id;
      state.selectedEntityId = d.subject_entity_id;
      renderNetwork();
    });

  const nodeSelection = g.append("g").selectAll("circle").data(nodes).join("circle")
    .attr("class", (d) => `node ${d.id === state.selectedEntityId ? "active" : ""}`)
    .attr("r", (d) => 6 + Math.min(6, Math.sqrt((state.data.relationshipsByEntity.get(d.id) || []).length)))
    .attr("fill", (d) => COLORS[d.type] || COLORS.relation)
    .on("click", (event, d) => {
      event.stopPropagation();
      state.selectedEntityId = d.id;
      state.selectedRelationshipId = null;
      renderNetwork();
      renderEntityDetail();
      renderTimeline();
    })
    .call(d3.drag()
      .on("start", (event) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on("drag", (event) => {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      })
      .on("end", (event) => {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }));

  const labels = g.append("g").selectAll("text").data(nodes).join("text")
    .attr("class", "graph-label")
    .text((d) => short(d.title, 12));

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);
    nodeSelection.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
    labels.attr("x", (d) => d.x + 10).attr("y", (d) => d.y + 4);
  });
}

function renderNetworkDetail() {
  const relationship = state.data.relationshipById.get(state.selectedRelationshipId);
  if (relationship) {
    const citations = state.data.citationsByRelationship.get(relationship.id) || [];
    els.networkDetail.innerHTML = `
      <h3>#${relationship.id} ${escapeHtml(relationship.relation_type)}</h3>
      ${renderRelationEndpoint("主体", relationship.subject_entity_title, relationship.subject_time, relationship.subject_event, relationship.subject_id)}
      ${renderRelationEndpoint("客体", relationship.object_entity_title, relationship.object_time, relationship.object_event, relationship.object_id)}
      <h3>引用</h3>
      ${citations.map((citation) => `
        <article class="dict-card">
          <strong>${escapeHtml(citation.citation || "无出处")}</strong>
          <p>${escapeHtml(citation.quotation || "")}</p>
        </article>
      `).join("") || `<p class="small-muted">该关系没有引用。</p>`}
    `;
    return;
  }
  const entity = state.data.entityById.get(state.selectedEntityId);
  els.networkDetail.innerHTML = entity ? `
    <h3>#${entity.id} ${escapeHtml(entity.title)}</h3>
    <div class="badges">${typeBadge(entity.type)}</div>
    <p class="small-muted">点击网络中的边可以查看关系方向、时间点与引用。</p>
  ` : `<p class="small-muted">未选中节点或关系。</p>`;
}

function renderRelationEndpoint(label, title, time, event, timepointId) {
  return `
    <article class="relation-card">
      <strong>${label}</strong>
      <div>${escapeHtml(title)} · 时间点 #${timepointId}</div>
      <div class="small-muted">${escapeHtml(time)} / ${escapeHtml(event)}</div>
    </article>
  `;
}

function renderTimeline() {
  const entity = state.data.entityById.get(state.selectedEntityId);
  const timepoints = entity ? state.data.timepointsByEntity.get(entity.id) || [] : [];
  els.timelineDetail.innerHTML = entity ? `
    <h3>#${entity.id} ${escapeHtml(entity.title)}</h3>
    <div class="badges">${typeBadge(entity.type)}</div>
    <div class="timeline-track">
      ${timepoints.map((timepoint) => `
        <article class="timeline-item ${timepoint.is_placeholder ? "placeholder" : ""}">
          <strong>#${timepoint.id} ${escapeHtml(timepoint.time || "无时间")}</strong>
          <div>${escapeHtml(timepoint.event || "")}</div>
          <div class="small-muted">prev=${timepoint.prev_id ?? "NULL"} / succ=${timepoint.succ_id ?? "NULL"} / 引用 ${timepoint.citation_count}</div>
        </article>
      `).join("")}
    </div>
  ` : `<p class="small-muted">未选中实体。</p>`;
  drawEvolutionGraph();
}

function drawEvolutionGraph() {
  const svg = d3.select("#evolutionGraph");
  const node = svg.node();
  const width = node.clientWidth || 700;
  const height = node.clientHeight || 620;
  svg.selectAll("*").remove();

  let links = state.data.relationships.filter((relationship) => relationship.relation_type === "前后演变");
  if (state.selectedEntityId) {
    const selectedLinks = links.filter((relationship) => relationship.subject_entity_id === state.selectedEntityId || relationship.object_entity_id === state.selectedEntityId);
    if (selectedLinks.length) links = selectedLinks;
  }
  links = links.slice(0, 120);
  const nodeMap = new Map();
  for (const relationship of links) {
    nodeMap.set(relationship.subject_entity_id, { id: relationship.subject_entity_id, title: relationship.subject_entity_title, type: relationship.subject_entity_type });
    nodeMap.set(relationship.object_entity_id, { id: relationship.object_entity_id, title: relationship.object_entity_title, type: relationship.object_entity_type });
  }
  const nodes = Array.from(nodeMap.values());
  if (!links.length) {
    svg.append("text").attr("x", 20).attr("y", 32).text("当前实体没有前后演变关系。").attr("fill", "#68747d");
    return;
  }

  const simLinks = links.map((relationship) => ({ ...relationship, source: relationship.subject_entity_id, target: relationship.object_entity_id }));
  svg.append("defs").append("marker")
    .attr("id", "arrow").attr("viewBox", "0 -5 10 10").attr("refX", 17).attr("refY", 0)
    .attr("markerWidth", 6).attr("markerHeight", 6).attr("orient", "auto")
    .append("path").attr("d", "M0,-5L10,0L0,5").attr("fill", COLORS.unknown);
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(simLinks).id((d) => d.id).distance(120))
    .force("charge", d3.forceManyBody().strength(-260))
    .force("center", d3.forceCenter(width / 2, height / 2));
  const link = svg.append("g").selectAll("line").data(simLinks).join("line")
    .attr("stroke", COLORS.unknown)
    .attr("stroke-width", 1.8)
    .attr("marker-end", "url(#arrow)");
  const circle = svg.append("g").selectAll("circle").data(nodes).join("circle")
    .attr("r", 8)
    .attr("fill", (d) => COLORS[d.type] || COLORS.relation)
    .on("click", (_, d) => {
      state.selectedEntityId = d.id;
      renderTimeline();
    });
  const label = svg.append("g").selectAll("text").data(nodes).join("text")
    .attr("class", "graph-label")
    .text((d) => short(d.title, 14));
  simulation.on("tick", () => {
    link.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y).attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
    circle.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
    label.attr("x", (d) => d.x + 11).attr("y", (d) => d.y + 4);
  });
}

async function init() {
  try {
    await loadData();
    setupControls();
    renderAll();
  } catch (error) {
    console.error(error);
    document.body.innerHTML = `<main><section class="panel" style="padding:18px;"><h1>加载失败</h1><p>${escapeHtml(error.message)}</p></section></main>`;
  }
}

init();
