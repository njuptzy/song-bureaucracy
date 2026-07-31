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
const svgCache = new Map();

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

function quotaText(edge) {
  const quota = edge.staff_quota ? `${edge.staff_quota}人` : "员额未载";
  return `${titleOf(edge.official)}（${quota}${edge.staff_type ? `，${edge.staff_type}` : ""}）`;
}

function selectedEntity() {
  return entityMap.get(selectedId.value) || titleMap.get("尚书省") || props.data.entities[0];
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
      const entity = titleMap.get(normalizeText(this));
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
          updateDetails(svg);
        });
    });
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

  setText(findTextAt(svg, 99.85, 505.87), entity.title);
  setText(findTextAt(svg, 189.74, 502.91), `公元${selectedYear.value}年制度截面`);
  wrapText(findTextAt(svg, 101.29, 570.06), mainText, 31, 24, 7);
  setText(findTextAt(svg, 100.33, 536.92), "编制与沿革");
  wrapText(findTextAt(svg, 101.29, 783.54), staffText, 31, 22, 2);
  setText(findTextAt(svg, 100.33, 750.4), "编制");
  setText(findTextAt(svg, 100.33, 846.08), `下级机构：${childText}`);

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
        updateDetails(svg);
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
    const entity = titleMap.get(normalizeText(element));
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
    const entity = titleMap.get(normalizeText(nearest.slot));
    const staff = staffFor(entity.id);
    setText(candidate, staff.length ? staff.slice(0, 10).map(quotaText).join("；") : "当前年份未载明确编制");
  }
}

function bindTemplateControls(svg) {
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
    bindEntityTexts(svg);
    replaceCompositionDescriptions(svg);
    bindTemplateControls(svg);
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
