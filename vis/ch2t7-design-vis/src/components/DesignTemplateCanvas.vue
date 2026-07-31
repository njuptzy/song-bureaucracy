<template>
  <div ref="hostRef" class="design-template" :class="{ loading: loading }">
    <div v-if="error" class="template-message">{{ error }}</div>
    <div v-else-if="loading" class="template-message">载入 SVG 设计画板…</div>
    <div ref="svgMountRef" class="svg-mount"></div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from "vue";
import * as d3 from "d3";

const props = defineProps({ data: { type: Object, required: true } });

const hostRef = ref(null);
const svgMountRef = ref(null);
const loading = ref(true);
const error = ref("");
const viewMode = ref("hierarchy");
const selectedYear = ref(1080);
const selectedId = ref(null);
const selectedCategory = ref("中央机构");
const svgCache = new Map();
const detailPanelOffset = { x: 0, y: 0 };

const DETAIL_PANEL_BOUNDS = {
  x: 81.77,
  y: 497.57,
  width: 393.72,
  height: 380.1,
};

const entityMap = new Map(props.data.entities.map((entity) => [entity.id, entity]));
const titleMap = new Map();
for (const entity of props.data.entities) {
  if (!titleMap.has(entity.title)) titleMap.set(entity.title, entity);
}

function normalizeText(element) {
  return (element.textContent || "").replace(/\s+/g, "").trim();
}

function position(element) {
  const match = /translate\(([-.\d]+)[ ,]([-.\d]+)/.exec(element.getAttribute("transform") || "");
  return match ? { x: Number(match[1]), y: Number(match[2]) } : null;
}

function findTextAt(svg, x, y, tolerance = 1) {
  return [...svg.querySelectorAll("text")].find((element) => {
    const point = position(element);
    return point && Math.abs(point.x - x) <= tolerance && Math.abs(point.y - y) <= tolerance;
  });
}

function setText(element, text) {
  if (!element) return;
  element.replaceChildren(document.createTextNode(text || "暂无资料"));
}

function wrapText(element, text, charsPerLine = 31, lineHeight = 24, maxLines = 7) {
  if (!element) return;
  const content = (text || "暂无资料").replace(/\s+/g, " ").trim();
  const lines = [];
  for (let i = 0; i < content.length && lines.length < maxLines; i += charsPerLine) {
    let line = content.slice(i, i + charsPerLine);
    if (i + charsPerLine < content.length && lines.length === maxLines - 1) line = `${line.slice(0, -1)}…`;
    lines.push(line);
  }
  element.replaceChildren();
  for (const [index, line] of lines.entries()) {
    const tspan = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
    tspan.setAttribute("x", "0");
    tspan.setAttribute("y", String(index * lineHeight));
    tspan.textContent = line;
    element.appendChild(tspan);
  }
}

function periodActive(periods) {
  if (!periods || periods.length === 0) return true;
  return periods.some((period) => selectedYear.value >= period.start && selectedYear.value <= period.end);
}

function timepointActive(timepoint) {
  if (timepoint.year_start == null || timepoint.year_end == null) return true;
  return selectedYear.value >= timepoint.year_start && selectedYear.value <= timepoint.year_end;
}

function activeTimepoints(entityId) {
  return (props.data.timepoints[String(entityId)] || []).filter(timepointActive);
}

function staffFor(entityId) {
  return props.data.staffEdges.filter((edge) => edge.org === entityId && periodActive(edge.periods));
}

function childrenFor(entityId) {
  return props.data.hierarchyEdges.filter((edge) => edge.parent === entityId && periodActive(edge.periods));
}

function titleOf(entityId) {
  return entityMap.get(entityId)?.title || `#${entityId}`;
}

const CATEGORY_NAMES = ["内廷机构", "中央机构", "路级机构", "州县机构", "军队机构"];

function entityCategory(entity) {
  const categories = (props.data.timepoints[String(entity.id)] || [])
    .map((timepoint) => timepoint.attr_category || "")
    .join(" ");
  const text = `${entity.title} ${categories}`;
  if (/内廷|宫廷|宫闱|禁中|内侍|御前|供御|殿中省|尚[食药衣舍辇酝]/.test(text)) return "内廷机构";
  if (/军队|军事|禁军|统兵|马军|步军|殿前司|侍卫|枢密|钤辖|都统制/.test(text)) return "军队机构";
  if (/路级|转运|提刑|提举常平|安抚|发运|总领|经略|漕司/.test(text)) return "路级机构";
  if (/州县|州府|府县|县衙|监当|税务|地方行政|知州|知县/.test(text)) return "州县机构";
  return "中央机构";
}

function categoryFocus(category) {
  const candidates = props.data.entities.filter(
    (entity) => entity.type === "机构" && entityCategory(entity) === category
  );
  const candidateIds = new Set(candidates.map((entity) => entity.id));
  const hasCategoryParent = new Set();
  for (const edge of props.data.hierarchyEdges) {
    if (!periodActive(edge.periods)) continue;
    if (candidateIds.has(edge.parent) && candidateIds.has(edge.child)) hasCategoryParent.add(edge.child);
  }
  const roots = candidates.filter((entity) => !hasCategoryParent.has(entity.id));
  const pool = roots.length ? roots : candidates;
  const scoreCache = new Map();
  const score = (entityId, visiting = new Set()) => {
    if (scoreCache.has(entityId)) return scoreCache.get(entityId);
    if (visiting.has(entityId)) return 0;
    const nextVisiting = new Set(visiting).add(entityId);
    const children = childrenFor(entityId).map((edge) => edge.child);
    const value = children.length + children.reduce((sum, childId) => sum + score(childId, nextVisiting), 0);
    scoreCache.set(entityId, value);
    return value;
  };
  return [...pool].sort(
    (a, b) => score(b.id) - score(a.id) || a.title.localeCompare(b.title, "zh")
  )[0] || null;
}

function quotaText(edge) {
  const quota = edge.staff_quota ? `${edge.staff_quota}人` : "员额未载";
  return `${titleOf(edge.official)}（${quota}${edge.staff_type ? `，${edge.staff_type}` : ""}）`;
}

function selectedEntity() {
  return entityMap.get(selectedId.value) || titleMap.get("尚书省") || props.data.entities[0];
}

function graphFocusEntity() {
  const selected = selectedEntity();
  if (selected?.type === "机构") return selected;
  const affiliation = props.data.staffEdges.find(
    (edge) => edge.official === selected?.id && periodActive(edge.periods)
  );
  return affiliation ? entityMap.get(affiliation.org) : titleMap.get("尚书省") || selected;
}

function hierarchyLevels(rootId, maxDepth) {
  const levels = [[rootId]];
  const visited = new Set([rootId]);
  for (let depth = 1; depth <= maxDepth; depth += 1) {
    const next = [];
    for (const parentId of levels[depth - 1]) {
      const children = childrenFor(parentId)
        .map((edge) => edge.child)
        .filter((id) => !visited.has(id))
        .sort((a, b) => titleOf(a).localeCompare(titleOf(b), "zh"));
      for (const childId of children) {
        visited.add(childId);
        next.push(childId);
      }
    }
    levels.push(next);
  }
  return levels;
}

function assignSlots(slots, entityIds) {
  const ordered = [...slots].sort((a, b) => {
    const pa = position(a);
    const pb = position(b);
    return pa.x - pb.x || pa.y - pb.y;
  });
  ordered.forEach((slot, index) => {
    const entityId = entityIds[index];
    if (entityId == null) {
      slot.style.opacity = "0";
      slot.removeAttribute("data-entity-id");
      return;
    }
    const title = titleOf(entityId);
    slot.style.opacity = "1";
    slot.dataset.entityId = String(entityId);
    setText(slot, title.length > 13 ? `${title.slice(0, 12)}…` : title);
  });
}

function populateHierarchyCenter(svg) {
  const focus = graphFocusEntity();
  if (!focus) return;
  const texts = [...svg.querySelectorAll("text")];
  const rootSlot = findTextAt(svg, 763.56, 196.11, 2);
  const buckets = [
    rootSlot ? [rootSlot] : [],
    texts.filter((element) => {
      const point = position(element);
      return point && point.x > 480 && point.y >= 300 && point.y < 400 && element.getAttribute("class") === "cls-56";
    }),
    texts.filter((element) => {
      const point = position(element);
      return point && point.x > 480 && point.y >= 430 && point.y < 550 && ["cls-48", "cls-56"].includes(element.getAttribute("class"));
    }),
    texts.filter((element) => {
      const point = position(element);
      return point && point.x > 480 && point.y >= 570 && point.y < 700 && ["cls-38", "cls-59"].includes(element.getAttribute("class"));
    }),
    texts.filter((element) => {
      const point = position(element);
      return point && point.x > 480 && point.y >= 700 && point.y < 850 && element.getAttribute("class") === "cls-59";
    }),
  ];
  const levels = hierarchyLevels(focus.id, buckets.length - 1);
  buckets.forEach((slots, depth) => assignSlots(slots, levels[depth] || []));

  // 原画板还预留了两个皇帝直属机构槽；填入焦点机构的同级机构，而非保留示例名称。
  const siblingSlots = [findTextAt(svg, 1735.2, 196.3, 2), findTextAt(svg, 1780.8, 196.3, 2)].filter(Boolean);
  const parentEdge = props.data.hierarchyEdges.find(
    (edge) => edge.child === focus.id && periodActive(edge.periods)
  );
  const siblings = parentEdge
    ? childrenFor(parentEdge.parent).map((edge) => edge.child).filter((id) => id !== focus.id)
    : [];
  assignSlots(siblingSlots, siblings);
  const contextSlot = findTextAt(svg, 1446.2, 183, 2);
  if (contextSlot) assignSlots([contextSlot], parentEdge ? [parentEdge.parent] : []);
}

function populateCompositionCenter(svg) {
  const focus = graphFocusEntity();
  if (!focus) return;
  const slots = [...svg.querySelectorAll("text")].filter((element) => {
    const point = position(element);
    const className = element.getAttribute("class");
    return (
      point &&
      point.x > 500 &&
      point.y > 140 &&
      point.y < 850 &&
      ["cls-28", "cls-38", "cls-50"].includes(className) &&
      normalizeText(element).length <= 16
    );
  });
  const levels = hierarchyLevels(focus.id, 5);
  const flattened = levels.flat();
  const seen = new Set();
  const unique = flattened.filter((id) => !seen.has(id) && seen.add(id));
  const orderedSlots = [...slots].sort((a, b) => {
    const pa = position(a);
    const pb = position(b);
    return pa.y - pb.y || pa.x - pb.x;
  });
  assignSlots(orderedSlots, unique);
}

function populateCenter(svg) {
  if (viewMode.value === "hierarchy") populateHierarchyCenter(svg);
  else populateCompositionCenter(svg);
}

function bindEntityTexts(svg) {
  const activeIds = new Set();
  for (const edge of props.data.hierarchyEdges) {
    if (periodActive(edge.periods)) {
      activeIds.add(edge.parent);
      activeIds.add(edge.child);
    }
  }
  for (const edge of props.data.staffEdges) {
    if (periodActive(edge.periods)) {
      activeIds.add(edge.org);
      activeIds.add(edge.official);
    }
  }

  d3.select(svg)
    .selectAll("text")
    .each(function () {
      const entity = this.dataset.entityId
        ? entityMap.get(Number(this.dataset.entityId))
        : titleMap.get(normalizeText(this));
      if (!entity) return;
      const point = position(this);
      // 左侧详情标题和顶部信息卡由 updateDetails 单独处理。
      if (point && point.x < 500) return;
      this.dataset.entityId = String(entity.id);
      this.style.cursor = "pointer";
      this.style.transition = "opacity .18s ease";
      this.style.opacity = activeIds.has(entity.id) || activeTimepoints(entity.id).length ? "1" : "0.2";
      d3.select(this)
        .on("mouseenter", () => this.classList.add("svg-entity-hover"))
        .on("mouseleave", () => this.classList.remove("svg-entity-hover"))
        .on("click", (event) => {
          event.stopPropagation();
          selectedId.value = entity.id;
          selectedCategory.value = entityCategory(entity);
          renderTemplate();
        });
    });
}

function setupDetailPanel(svg) {
  const panelNodes = [...svg.children].filter((element) => {
    if (["defs", "style", "image"].includes(element.tagName.toLowerCase())) return false;
    let bounds;
    try {
      bounds = element.getBBox();
    } catch {
      return false;
    }
    return bounds.x >= 70
      && bounds.y >= 480
      && bounds.x + bounds.width <= 482
      && bounds.y + bounds.height <= 885;
  });
  if (!panelNodes.length) return;

  const panelGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  panelGroup.classList.add("detail-panel-group");
  panelGroup.setAttribute("transform", `translate(${detailPanelOffset.x} ${detailPanelOffset.y})`);
  svg.insertBefore(panelGroup, panelNodes[0]);
  panelNodes.forEach((node) => panelGroup.appendChild(node));

  const defs = svg.querySelector("defs") || svg.insertBefore(
    document.createElementNS("http://www.w3.org/2000/svg", "defs"),
    svg.firstChild
  );
  const clipPath = document.createElementNS("http://www.w3.org/2000/svg", "clipPath");
  clipPath.id = "detail-panel-content-clip";
  clipPath.setAttribute("clipPathUnits", "userSpaceOnUse");
  const clipRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  clipRect.setAttribute("x", String(DETAIL_PANEL_BOUNDS.x + 7));
  clipRect.setAttribute("y", String(DETAIL_PANEL_BOUNDS.y + 2));
  clipRect.setAttribute("width", String(DETAIL_PANEL_BOUNDS.width - 17));
  clipRect.setAttribute("height", String(DETAIL_PANEL_BOUNDS.height - 7));
  clipPath.appendChild(clipRect);
  defs.appendChild(clipPath);

  const dragHandle = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  dragHandle.classList.add("detail-panel-drag-handle");
  dragHandle.setAttribute("x", String(DETAIL_PANEL_BOUNDS.x));
  dragHandle.setAttribute("y", String(DETAIL_PANEL_BOUNDS.y));
  dragHandle.setAttribute("width", String(DETAIL_PANEL_BOUNDS.width));
  dragHandle.setAttribute("height", "52");
  dragHandle.setAttribute("fill", "transparent");
  dragHandle.setAttribute("pointer-events", "all");
  dragHandle.style.cursor = "grab";
  panelGroup.appendChild(dragHandle);

  const viewBox = svg.viewBox.baseVal;
  const minX = viewBox.x - DETAIL_PANEL_BOUNDS.x;
  const maxX = viewBox.x + viewBox.width - DETAIL_PANEL_BOUNDS.x - DETAIL_PANEL_BOUNDS.width;
  const minY = viewBox.y - DETAIL_PANEL_BOUNDS.y;
  const maxY = viewBox.y + viewBox.height - DETAIL_PANEL_BOUNDS.y - DETAIL_PANEL_BOUNDS.height;
  const movePanel = () => {
    panelGroup.setAttribute("transform", `translate(${detailPanelOffset.x} ${detailPanelOffset.y})`);
  };
  d3.select(dragHandle)
    .on("click", (event) => event.stopPropagation())
    .call(
      d3.drag()
        .on("start", (event) => {
          event.sourceEvent?.stopPropagation();
          dragHandle.style.cursor = "grabbing";
        })
        .on("drag", (event) => {
          detailPanelOffset.x = Math.max(minX, Math.min(maxX, detailPanelOffset.x + event.dx));
          detailPanelOffset.y = Math.max(minY, Math.min(maxY, detailPanelOffset.y + event.dy));
          movePanel();
        })
        .on("end", () => {
          dragHandle.style.cursor = "grab";
        })
    );
}

function updateDetails(svg) {
  const entity = selectedEntity();
  if (!entity) return;
  const dictionary = props.data.dictionary[entity.title] || {};
  const timepoints = activeTimepoints(entity.id);
  const staff = staffFor(entity.id);
  const children = childrenFor(entity.id);
  const eventText = timepoints.map((item) => `${item.time || "时间未明"}：${item.event}`).join("；");
  const mainText = eventText || dictionary.text || "当前年份未载明确事件。";
  const staffText = staff.length ? staff.map(quotaText).join("；") : "当前年份未载明确编制。";
  const childText = children.length ? children.map((edge) => titleOf(edge.child)).join("、") : "当前年份未载明确下级机构。";

  const detailSlots = {
    title: findTextAt(svg, 99.85, 505.87),
    year: findTextAt(svg, 189.74, 502.91),
    main: findTextAt(svg, 101.29, 570.06),
    mainLabel: findTextAt(svg, 100.33, 536.92),
    staff: findTextAt(svg, 101.29, 783.54),
    staffLabel: findTextAt(svg, 100.33, 750.4),
    children: findTextAt(svg, 100.33, 846.08),
  };
  Object.values(detailSlots).forEach((slot) => {
    slot?.setAttribute("clip-path", "url(#detail-panel-content-clip)");
  });
  setText(detailSlots.title, entity.title);
  setText(detailSlots.year, `公元${selectedYear.value}年制度截面`);
  wrapText(detailSlots.main, mainText, 31, 24, 7);
  setText(detailSlots.mainLabel, "编制与沿革");
  wrapText(detailSlots.staff, staffText, 31, 22, 2);
  setText(detailSlots.staffLabel, "编制");
  wrapText(detailSlots.children, `下级机构：${childText}`, 31, 18, 2);

  // 第一画板顶部浮动卡：仍使用原有框、竖排槽位和官职条，只替换内容。
  if (viewMode.value === "hierarchy") {
    setText(findTextAt(svg, 763.56, 196.11), entity.title);
    const officialSlots = [...svg.querySelectorAll("text")]
      .filter((element) => {
        const point = position(element);
        return point && point.x >= 790 && point.x <= 1080 && point.y >= 180 && point.y <= 240 && titleMap.has(normalizeText(element));
      })
      .sort((a, b) => position(a).x - position(b).x);
    officialSlots.forEach((slot, index) => {
      const edge = staff[index];
      slot.style.display = edge ? "" : "none";
      if (!edge) return;
      setText(slot, titleOf(edge.official));
      slot.dataset.entityId = String(edge.official);
      d3.select(slot).on("click", (event) => {
        event.stopPropagation();
        selectedId.value = edge.official;
        renderTemplate();
      });
      const slotPoint = position(slot);
      const quotaSlot = [...svg.querySelectorAll("text")].find((candidate) => {
        const point = position(candidate);
        return point && Math.abs(point.x - (slotPoint.x - 7.5)) < 4 && Math.abs(point.y - 269.7) < 2;
      });
      if (quotaSlot) setText(quotaSlot, edge.staff_quota ? `（${edge.staff_quota}）` : "（未载）");
    });
  }
}

function replaceCompositionDescriptions(svg) {
  if (viewMode.value !== "composition") return;
  const candidates = [...svg.querySelectorAll("text")].filter((element) => {
    const point = position(element);
    const text = normalizeText(element);
    return point && point.x > 500 && point.y > 130 && point.y < 870 && text.length > 14 && /人|官额|吏额|郎中|侍郎/.test(text) && !titleMap.has(text);
  });
  const institutionSlots = [...svg.querySelectorAll("text")].filter((element) => {
    const point = position(element);
    const entity = element.dataset.entityId
      ? entityMap.get(Number(element.dataset.entityId))
      : titleMap.get(normalizeText(element));
    return point && point.x > 500 && point.y > 130 && point.y < 870 && entity?.type === "机构";
  });
  const used = new Set();
  for (const candidate of candidates) {
    const point = position(candidate);
    const nearest = institutionSlots
      .filter((slot) => !used.has(slot))
      .map((slot) => {
        const p = position(slot);
        return { slot, distance: Math.abs(p.x - point.x) + Math.abs(p.y - point.y) * 0.35 };
      })
      .sort((a, b) => a.distance - b.distance)[0];
    if (!nearest) continue;
    used.add(nearest.slot);
    const entity = nearest.slot.dataset.entityId
      ? entityMap.get(Number(nearest.slot.dataset.entityId))
      : titleMap.get(normalizeText(nearest.slot));
    const staff = staffFor(entity.id);
    setText(candidate, staff.length ? staff.slice(0, 10).map(quotaText).join("；") : "当前年份未载明确编制");
  }
}

function bindTemplateControls(svg) {
  const categoryItems = [...svg.querySelectorAll("text")]
    .map((textElement) => ({
      category: normalizeText(textElement),
      textElement,
      group: textElement.parentElement,
    }))
    .filter(({ category, group }) => CATEGORY_NAMES.includes(category) && group?.tagName.toLowerCase() === "g");
  const selectionTemplate = categoryItems
    .map(({ group }) => [...group.children].find(
      (child) => child.tagName.toLowerCase() === "g"
        && (child.classList.contains("cls-81") || child.classList.contains("cls-59"))
    ))
    .find(Boolean)?.cloneNode(true);

  for (const { group } of categoryItems) {
    [...group.children]
      .filter((child) => child.tagName.toLowerCase() === "g"
        && (child.classList.contains("cls-81") || child.classList.contains("cls-59")))
      .forEach((child) => child.remove());
  }

  const selectedItem = categoryItems.find(({ category }) => category === selectedCategory.value);
  const selectedOutline = selectedItem
    ? [...selectedItem.group.children].find((child) => child.tagName.toLowerCase() === "polygon")
    : null;
  if (selectionTemplate && selectedItem && selectedOutline) {
    const selectionPolygon = selectionTemplate.querySelector("polygon");
    selectionPolygon?.setAttribute("points", selectedOutline.getAttribute("points") || "");
    selectedItem.group.insertBefore(selectionTemplate, selectedItem.group.firstChild);
  }

  d3.select(svg)
    .selectAll("text")
    .each(function () {
      const text = normalizeText(this);
      if (text === "层级视图" || text === "编制视图") {
        this.style.cursor = "pointer";
        this.style.fontWeight = (text === "层级视图") === (viewMode.value === "hierarchy") ? "700" : "400";
        d3.select(this).on("click", (event) => {
          event.stopPropagation();
          viewMode.value = text === "层级视图" ? "hierarchy" : "composition";
        });
      }

      if (CATEGORY_NAMES.includes(text)) {
        const category = text;
        const group = this.parentElement;
        const activate = (event) => {
          event.stopPropagation();
          selectedCategory.value = category;
          const focus = categoryFocus(category);
          selectedId.value = focus?.id ?? null;
          renderTemplate();
        };
        this.style.cursor = "pointer";
        d3.select(this).on("click.category", activate);
        if (group?.tagName.toLowerCase() === "g") {
          group.style.cursor = "pointer";
          group.style.pointerEvents = "bounding-box";
          d3.select(group).on("click.category", activate);
        }
      }
    });

  d3.select(svg).on("click.timeline", (event) => {
    const [x, y] = d3.pointer(event, svg);
    if (y < 890 || x < 200 || x > 1570) return;
    selectedYear.value = Math.round(d3.scaleLinear().domain([210, 1559]).range([960, 1279]).clamp(true)(x));
  });
}

function installDesignFonts() {
  if (document.getElementById("ch2t7-design-fonts")) return;
  const style = document.createElement("style");
  style.id = "ch2t7-design-fonts";
  style.textContent = `
    @font-face { font-family: FZQINGKBYSS-M--GB1-0; src: url('/api/design/fzqing.ttf') format('truetype'); }
    @font-face { font-family: FZQINGKBYSS-R--GB1-0; src: url('/api/design/fzqing.ttf') format('truetype'); }
    @font-face { font-family: FZQingKeBenYueSongS; src: url('/api/design/fzqing.ttf') format('truetype'); }
    @font-face { font-family: AdobeSongStd-Light-GBpc-EUC-H; src: url('/api/design/adobe-song.otf') format('opentype'); }
  `;
  document.head.appendChild(style);
}

async function renderTemplate() {
  loading.value = true;
  error.value = "";
  const url = `/api/design/${viewMode.value}.svg`;
  try {
    if (!svgCache.has(url)) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      svgCache.set(url, await response.text());
    }
    svgMountRef.value.innerHTML = svgCache.get(url);
    await nextTick();
    const svg = svgMountRef.value.querySelector("svg");
    if (!svg) throw new Error("原 SVG 中未找到画板");
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.classList.add("live-design-svg");
    populateCenter(svg);
    bindEntityTexts(svg);
    replaceCompositionDescriptions(svg);
    bindTemplateControls(svg);
    setupDetailPanel(svg);
    updateDetails(svg);
  } catch (reason) {
    error.value = `SVG 设计稿加载失败：${reason.message}`;
  } finally {
    loading.value = false;
  }
}

watch(viewMode, renderTemplate);
watch(selectedYear, () => renderTemplate());
onMounted(() => {
  installDesignFonts();
  renderTemplate();
});
</script>

<style scoped>
.design-template { width: 100%; height: 100%; position: relative; overflow: hidden; background: #f5f3ec; }
.svg-mount { width: 100%; height: 100%; }
.svg-mount :deep(.live-design-svg) { display: block; width: 100%; height: 100%; }
.svg-mount :deep(.svg-entity-hover) { filter: drop-shadow(0 0 2px rgba(53, 23, 4, 0.75)); text-decoration: underline; }
.template-message { position: absolute; inset: 0; display: grid; place-items: center; z-index: 5; color: #563905; background: #f5f3ec; letter-spacing: 3px; }
</style>
