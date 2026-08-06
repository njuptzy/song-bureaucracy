<template>
  <div ref="hostRef" class="design-template" :class="{ loading: loading }">
    <div v-if="error" class="template-message">{{ error }}</div>
    <div v-else-if="loading" class="template-message">载入 SVG 设计画板…</div>
    <div ref="svgMountRef" class="svg-mount"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import * as d3 from "d3";
import {
  buildYearSnapshot,
  hierarchyEdgesWithoutCollectives,
} from "../utils/snapshot";
import {
  buildInstitutionGroupNodes,
  CENTRAL_GROUP_NAMES,
  entityInstitutionGroup,
  institutionGroupId,
} from "../utils/central_groups";
import {
  anchorBranchToGroup,
  fitRangeShift,
  horizontalRangesFit,
  panFromScrollbarOffset,
  panScrollbarGeometry,
  virtualBusRange,
} from "../utils/hierarchy_layout";
import {
  collapseInstitutionGroups,
  expansionAfterLayout,
  expansionAnchorId,
  institutionGroupsAfterLayout,
  mergeExpansionPaths,
  removeExpandedSubtree,
  toggleInstitutionGroupIds,
} from "../utils/hierarchy_expansion";
import {
  resolveHierarchyContext,
  resolveVisibleSelection,
} from "../utils/hierarchy_navigation";
import {
  clampCompositionScroll,
  compositionScrollAfterDrag,
  compositionSliderGeometry,
} from "../utils/composition_scroll";

const props = defineProps({ data: { type: Object, required: true } });

const hostRef = ref(null);
const svgMountRef = ref(null);
const loading = ref(true);
const error = ref("");
const viewMode = ref("hierarchy");
const selectedRange = ref([1080, 1080]);
const timelineSelectionActive = ref(true);
const selectedId = ref(null);
const selectedCategory = ref("中央机构");
const expandedDetailId = ref(null);
const inlineDetailField = ref("duty");
const inlineDetailOfficialId = ref(null);
const spaceAwareExpansion = ref(false);
const svgCache = new Map();
const hierarchyTemplateCache = new WeakMap();
const yearSnapshotCache = new Map();
const detailPanelOffset = { x: 0, y: 0 };
let detailPanelScrollOffset = 0;
let pendingDetailSectionKey = null;
let lastHierarchyClick = null;
const collapsedHierarchyIds = new Set();
let expandedHierarchyPath = [];
let hierarchyPanX = 0;
let hierarchyPanY = 0;
let expandedInstitutionGroupIds = [];
let lastExpandedInstitutionGroupId = null;
let inlineCompositionScrollOffset = 0;
let renderRevision = 0;
let lastExpandedHierarchyId = null;
let timelineRefreshFrame = null;
let timelineRefreshNeedsStatic = false;

const YEAR_MIN = props.data.meta?.yearMin ?? 960;
const YEAR_MAX = props.data.meta?.yearMax ?? 1279;
const TIMELINE_SCALE_END = YEAR_MAX + 1;
const TIMELINE_X_MIN = 221.63;
const TIMELINE_X_MAX = 1546.36;
const yearScale = d3.scaleLinear()
  .domain([YEAR_MIN, TIMELINE_SCALE_END])
  .range([TIMELINE_X_MIN, TIMELINE_X_MAX])
  .clamp(true);
const TIMELINE_YEAR_WIDTH = yearScale(YEAR_MIN + 1) - yearScale(YEAR_MIN);

const DETAIL_PANEL_BOUNDS = {
  x: 81.77,
  y: 497.57,
  width: 393.72,
  height: 380.1,
};

const entityMap = new Map(props.data.entities.map((entity) => [entity.id, entity]));
const collectiveEntityIds = new Set(props.data.collectiveEntityIds || []);
const titleMap = new Map();
for (const entity of props.data.entities) {
  if (!titleMap.has(entity.title)) titleMap.set(entity.title, entity);
}
const institutionGroupNames = props.data.meta?.institutionGroupNames || {
  中央机构: CENTRAL_GROUP_NAMES,
};
lastExpandedInstitutionGroupId = institutionGroupId(
  "中央机构",
  entityInstitutionGroup(titleMap.get("尚书省"), "中央机构")
);
expandedInstitutionGroupIds = [lastExpandedInstitutionGroupId];
function yearSnapshot(year) {
  if (yearSnapshotCache.has(year)) {
    const cached = yearSnapshotCache.get(year);
    yearSnapshotCache.delete(year);
    yearSnapshotCache.set(year, cached);
    return cached;
  }
  const snapshot = buildYearSnapshot(props.data, year);
  yearSnapshotCache.set(year, snapshot);
  if (yearSnapshotCache.size > 16) {
    yearSnapshotCache.delete(yearSnapshotCache.keys().next().value);
  }
  return snapshot;
}

const currentSnapshot = computed(() => (
  timelineSelectionActive.value ? yearSnapshot(selectedRange.value[0]) : null
));

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

function wrapText(element, text, charsPerLine = 28, lineHeight = 24, maxLines = 7) {
  if (!element) return 0;
  const content = (text || "暂无资料").replace(/\s+/g, " ").trim();
  const lines = [];
  const closingPunctuation = /[，。；：！？、〉》）】」』]/;
  let offset = 0;
  while (offset < content.length && lines.length < maxLines) {
    let end = Math.min(content.length, offset + charsPerLine);
    while (end < content.length && closingPunctuation.test(content[end])) end += 1;
    let line = content.slice(offset, end);
    if (end < content.length && lines.length === maxLines - 1) line = `${line.slice(0, -1)}…`;
    lines.push(line);
    offset = end;
  }
  element.replaceChildren();
  for (const [index, line] of lines.entries()) {
    const tspan = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
    tspan.setAttribute("x", "0");
    tspan.setAttribute("y", String(index * lineHeight));
    tspan.textContent = line;
    element.appendChild(tspan);
  }
  return lines.length;
}

function selectLinkedEntity(entityId) {
  const target = entityMap.get(entityId);
  if (!target) return;
  lastHierarchyClick = null;
  detailPanelScrollOffset = 0;
  inlineCompositionScrollOffset = 0;
  expandedDetailId.value = null;
  inlineDetailOfficialId.value = null;
  selectedId.value = target.id;
  if (target.type === "机构") {
    focusHierarchyContext(target, true);
  } else {
    const affiliation = staffEdgesForView().find((edge) => edge.official === target.id);
    const org = affiliation ? entityMap.get(affiliation.org) : null;
    if (org) focusHierarchyContext(org, true);
  }
  refreshTemplate({ rebindControls: true });
}

function renderLinkedTokens(element, tokens, emptyText, charsPerLine = 28, lineHeight = 18) {
  if (!element) return 0;
  const normalized = tokens.length ? tokens : [{ text: emptyText }];
  element.replaceChildren();
  let line = 0;
  let lineLength = 0;
  for (const token of normalized) {
    let remaining = token.text;
    while (remaining) {
      const room = charsPerLine - lineLength;
      if (room <= 0) {
        line += 1;
        lineLength = 0;
        continue;
      }
      const chunk = remaining.slice(0, room);
      remaining = remaining.slice(chunk.length);
      const tspan = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      if (lineLength === 0) {
        tspan.setAttribute("x", "0");
        tspan.setAttribute("y", String(line * lineHeight));
      }
      tspan.textContent = chunk;
      if (token.entityId != null) {
        tspan.dataset.entityId = String(token.entityId);
        tspan.style.cursor = "pointer";
        tspan.style.fill = "#866d6d";
        tspan.style.textDecoration = "underline";
        d3.select(tspan).on("click.detail-entity-link", (event) => {
          event.preventDefault();
          event.stopPropagation();
          selectLinkedEntity(token.entityId);
        });
      }
      element.appendChild(tspan);
      lineLength += chunk.length;
    }
  }
  return line + 1;
}

function wrapVerticalText(element, text, charsPerColumn = 11, maxColumns = 6, columnGap = 9.81) {
  if (!element) return;
  const content = (text || "暂无资料").replace(/\s+/g, " ").trim();
  const columns = [];
  let offset = 0;
  while (offset < content.length && columns.length < maxColumns) {
    const end = Math.min(content.length, offset + charsPerColumn);
    let column = content.slice(offset, end);
    if (end < content.length && columns.length === maxColumns - 1) {
      column = `${column.slice(0, -1)}…`;
    }
    columns.push(column);
    offset = end;
  }
  element.replaceChildren();
  columns.forEach((column, index) => {
    const tspan = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
    tspan.setAttribute("x", String(-index * columnGap));
    tspan.setAttribute("y", "0");
    tspan.textContent = column;
    element.appendChild(tspan);
  });
}

function fitVerticalBarLabel(label, fullTitle, rect) {
  if (!label || !rect) return;
  const x = Number(rect.getAttribute("x"));
  const y = Number(rect.getAttribute("y"));
  const width = Number(rect.getAttribute("width"));
  const height = Number(rect.getAttribute("height"));
  if (![x, y, width, height].every(Number.isFinite)) return;
  const maxGlyphs = 12;
  const displayTitle = fullTitle.length > maxGlyphs
    ? `${fullTitle.slice(0, maxGlyphs - 1)}…`
    : fullTitle;
  label.replaceChildren();
  label.removeAttribute("transform");
  label.removeAttribute("text-anchor");
  label.removeAttribute("dominant-baseline");
  label.style.writingMode = "horizontal-tb";
  label.style.textOrientation = "mixed";
  label.setAttribute("text-anchor", "middle");
  // 长名称在加宽的书脊内按传统顺序分成右、左两列，避免靠增加高度换字号。
  const columns = displayTitle.length > 6
    ? [
        displayTitle.slice(0, Math.ceil(displayTitle.length / 2)),
        displayTitle.slice(Math.ceil(displayTitle.length / 2)),
      ]
    : [displayTitle];
  const longestColumn = Math.max(...columns.map((column) => column.length));
  const bodyHeight = height - 34;
  const fontSize = Math.min(
    INLINE_COMPOSITION.titleFontSize,
    bodyHeight / Math.max(1, longestColumn)
  );
  label.style.fontSize = `${fontSize}px`;
  const centerX = x + width / 2;
  const top = y + 7;
  const columnGap = Math.min(width * 0.34, fontSize * 1.08);
  columns.forEach((column, columnIndex) => {
    const columnX = centerX + ((columns.length - 1) / 2 - columnIndex) * columnGap;
    [...column].forEach((character, index) => {
      const tspan = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      tspan.setAttribute("x", String(columnX));
      tspan.setAttribute("y", String(top + fontSize * (index + 0.82)));
      tspan.textContent = character;
      label.appendChild(tspan);
    });
  });
}

function fitQuotaLabel(quota, person, edge, rect) {
  if (!quota || !rect) return;
  const x = Number(rect.getAttribute("x"));
  const y = Number(rect.getAttribute("y"));
  const width = Number(rect.getAttribute("width"));
  const height = Number(rect.getAttribute("height"));
  if (![x, y, width, height].every(Number.isFinite)) return;
  const text = edge.staff_quota ? `（${edge.staff_quota}）` : "未载";
  setText(quota, text);
  quota.removeAttribute("transform");
  quota.style.writingMode = "horizontal-tb";
  quota.setAttribute("text-anchor", "middle");
  quota.removeAttribute("dominant-baseline");
  quota.style.fontSize = `${Math.min(
    INLINE_COMPOSITION.quotaFontSize,
    24 / Math.max(2, text.length)
  )}px`;
  quota.setAttribute("x", String(x + width / 2));
  quota.setAttribute("y", String(y + height - 7));
  if (person) {
    person.style.display = edge.staff_quota ? "" : "none";
    person.removeAttribute("transform");
    person.style.writingMode = "horizontal-tb";
    person.setAttribute("text-anchor", "middle");
    person.style.fontSize = `${INLINE_COMPOSITION.personFontSize}px`;
    person.setAttribute("x", String(x + width / 2));
    person.setAttribute("y", String(y + height - 2));
  }
}

function constrainTextWidth(element, maxWidth) {
  if (!element) return;
  element.removeAttribute("textLength");
  element.removeAttribute("lengthAdjust");
  if (element.getComputedTextLength() <= maxWidth) return;
  element.setAttribute("textLength", String(maxWidth));
  element.setAttribute("lengthAdjust", "spacingAndGlyphs");
}

function intervalOverlapsRange(start, end) {
  const [rangeStart, rangeEnd] = selectedRange.value;
  return start <= rangeEnd && end >= rangeStart;
}

function timepointActive(timepoint) {
  if (timepoint.year_start == null || timepoint.year_end == null) return true;
  return intervalOverlapsRange(timepoint.year_start, timepoint.year_end);
}

function selectedRangeLabel() {
  const [start, end] = selectedRange.value;
  if (start === YEAR_MIN && end === YEAR_MAX) return `宋代历史全貌（${start}—${end}年）`;
  if (start === end) return `公元${start}年制度截面`;
  return `公元${start}—${end}年制度范围`;
}

function activeTimepoints(entityId) {
  if (currentSnapshot.value) {
    const timepoint = currentSnapshot.value.currentTimepointByEntity.get(entityId);
    return timepoint ? [timepoint] : [];
  }
  return (props.data.timepoints[String(entityId)] || []).filter(timepointActive);
}

function entityActive(entityId) {
  if (currentSnapshot.value) return currentSnapshot.value.entityIds.has(entityId);
  const timepoints = props.data.timepoints[String(entityId)] || [];
  return timepoints.length > 0;
}

function hierarchyEdgesForView() {
  return hierarchyEdgesWithoutCollectives(
    currentSnapshot.value?.hierarchyEdges || props.data.hierarchyEdges,
    collectiveEntityIds,
  );
}

function staffEdgesForView() {
  return currentSnapshot.value?.staffEdges || props.data.staffEdges;
}

function staffFor(entityId) {
  return staffEdgesForView().filter((edge) => edge.org === entityId);
}

function childrenFor(entityId) {
  return hierarchyEdgesForView().filter((edge) => edge.parent === entityId);
}

function titleOf(entityId) {
  return entityMap.get(entityId)?.title || `#${entityId}`;
}

const CATEGORY_NAMES = ["内廷机构", "中央机构", "路级机构", "州县机构", "军队机构"];

function entityCategory(entity) {
  return entity.category || "中央机构";
}

function focusHierarchyContext(entity, revealPath = false) {
  const context = resolveHierarchyContext(entity.id, hierarchyEdgesForView(), entityMap);
  const root = context.root || entity;
  const category = entityCategory(root);
  selectedCategory.value = category;
  lastExpandedInstitutionGroupId = institutionGroupId(
    category,
    entityInstitutionGroup(root, category)
  );
  expandedInstitutionGroupIds = [lastExpandedInstitutionGroupId];
  if (revealPath) {
    expandedHierarchyPath = context.path.slice(0, -1);
    lastExpandedHierarchyId = expandedHierarchyPath.at(-1) ?? null;
  }
  return context;
}

function hierarchyRootEntities(category) {
  const hierarchyEdges = hierarchyEdgesForView();
  const childIds = new Set(hierarchyEdges.map((edge) => edge.child));
  return props.data.entities.filter(
    (entity) => entity.type === "机构"
      && !collectiveEntityIds.has(entity.id)
      && entityCategory(entity) === category
      && entityActive(entity.id)
      && !childIds.has(entity.id)
  );
}

function categoryFocus(category) {
  const roots = hierarchyRootEntities(category);
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
  return [...roots].sort(
    (a, b) => score(b.id) - score(a.id) || a.title.localeCompare(b.title, "zh")
  )[0] || null;
}

function quotaText(edge) {
  const quota = edge.staff_quota ? `${edge.staff_quota}人` : "员额未载";
  return `${titleOf(edge.official)}（${quota}${edge.staff_type ? `，${edge.staff_type}` : ""}）`;
}

const INLINE_DETAIL_FIELDS = [
  { key: "source", label: "出处：" },
  { key: "origin", label: "职源与沿革文本：" },
  { key: "aliases", label: "简称与别名：" },
  { key: "duty", label: "执掌：" },
  { key: "children", label: "下级机构：" },
  { key: "office", label: "衙署：" },
  { key: "composition", label: "编制文本：" },
];

function inlineDetailValues(entity) {
  const dictionary = props.data.dictionary[entity.title] || {};
  const timepoints = activeTimepoints(entity.id);
  const detailTimepoints = (props.data.timepoints[String(entity.id)] || [])
    .filter((timepoint) => Object.keys(timepoint).some((key) => key.startsWith("detail_")))
    .filter((timepoint) => (
      currentSnapshot.value
        ? timepoint.year_start <= selectedRange.value[0]
        : timepointActive(timepoint)
    ))
    .sort((a, b) => a.year_start - b.year_start || a.id - b.id);
  const currentTimepoint = detailTimepoints.at(-1) || timepoints.at(-1) || {};
  const staff = staffFor(entity.id);
  const children = childrenFor(entity.id);
  const events = timepoints
    .map((item) => `${item.time || "时间未明"}：${item.event || item.quotation || "未载事件"}`)
    .join("；");
  const page = dictionary.page || "";
  const source = [
    page ? (page.startsWith("《") ? page : `《宋代官制辞典》第${page}页`) : "",
    dictionary.catalog || "",
    currentTimepoint.detail_source || dictionary.source || "",
  ].filter(Boolean).join("；");
  return {
    source: source || "当前实体未匹配到独立辞典词条。",
    origin: currentTimepoint.detail_origin || dictionary.origin || events || "原文未单列职源与沿革。",
    aliases: dictionary.aliases || "原文未单列简称与别名。",
    duty: currentTimepoint.detail_duty || dictionary.duty || events || dictionary.text || "当前年份未载明确职掌。",
    children: children.length
      ? children.map((edge) => titleOf(edge.child)).join("、")
      : dictionary.children || "当前年份未载明确下级机构。",
    office: currentTimepoint.detail_office || dictionary.office || "原文未单列衙署。",
    composition: currentTimepoint.detail_composition || dictionary.composition
      || (staff.length ? staff.map(quotaText).join("；") : "当前年份未载明确编制。"),
  };
}

function selectedEntity() {
  const selected = entityMap.get(selectedId.value);
  const activeEntityIds = currentSnapshot.value?.entityIds || null;
  const fallback = selected && (!activeEntityIds || activeEntityIds.has(selected.id))
    ? null
    : categoryFocus(selectedCategory.value);
  const resolved = resolveVisibleSelection(selected, activeEntityIds, fallback);
  if (resolved?.id !== selectedId.value) selectedId.value = resolved?.id ?? null;
  return resolved;
}

function graphFocusEntity() {
  const selected = selectedEntity();
  if (selected?.type === "机构") return selected;
  const affiliation = staffEdgesForView().find((edge) => edge.official === selected?.id);
  return affiliation
    ? entityMap.get(affiliation.org)
    : selected || categoryFocus(selectedCategory.value);
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

function hierarchyTreeData(rootId, depth = 0, visiting = new Set()) {
  const entity = entityMap.get(rootId);
  if (!entity || visiting.has(rootId)) return null;
  const nextVisiting = new Set(visiting).add(rootId);
  const allChildren = childrenFor(rootId)
    .map((edge) => edge.child)
    .filter((id) => !nextVisiting.has(id))
    .sort((a, b) => titleOf(a).localeCompare(titleOf(b), "zh"));
  const shouldExpand = expandedHierarchyPath.includes(rootId);
  const shownChildren = shouldExpand ? allChildren : [];
  return {
    id: rootId,
    title: entity.title,
    childCount: allChildren.length,
    hiddenCount: allChildren.length - shownChildren.length,
    children: shownChildren
      .map((id) => hierarchyTreeData(id, depth + 1, nextVisiting))
      .filter(Boolean),
  };
}

function hierarchyExpansionPath(node) {
  return node.ancestors()
    .reverse()
    .filter((ancestor) => !ancestor.data.isVirtual)
    .map((ancestor) => ancestor.data.id);
}

function hierarchySubtreeIds(rootId) {
  const result = [];
  const queue = [rootId];
  const visited = new Set();
  while (queue.length) {
    const entityId = queue.shift();
    if (visited.has(entityId)) continue;
    visited.add(entityId);
    result.push(entityId);
    childrenFor(entityId).forEach((edge) => queue.push(edge.child));
  }
  return result;
}

function renderExpansionCandidate(fallbackPath) {
  const candidateIds = [...expandedHierarchyPath];
  refreshTemplate();
  const svg = svgMountRef.value?.querySelector("svg.live-design-svg");
  const resolvedIds = expansionAfterLayout({
    candidateIds,
    fallbackPath,
    spaceAware: spaceAwareExpansion.value,
    layoutFits: svg?.__dynamicHierarchyFitsViewport !== false,
  });
  if (
    resolvedIds.length === candidateIds.length
    && resolvedIds.every((id, index) => id === candidateIds[index])
  ) return;
  expandedHierarchyPath = resolvedIds;
  refreshTemplate();
}

function renderInstitutionGroupCandidate(clickedId) {
  const candidateIds = [...expandedInstitutionGroupIds];
  refreshTemplate();
  const svg = svgMountRef.value?.querySelector("svg.live-design-svg");
  const resolvedIds = institutionGroupsAfterLayout({
    candidateIds,
    clickedId,
    spaceAware: spaceAwareExpansion.value,
    layoutFits: svg?.__dynamicHierarchyFitsViewport !== false,
  });
  if (
    resolvedIds.length === candidateIds.length
    && resolvedIds.every((id, index) => id === candidateIds[index])
  ) return;
  expandedInstitutionGroupIds = resolvedIds;
  refreshTemplate();
}

function categoryForestData(category) {
  const roots = hierarchyRootEntities(category).map((entity) => entity.id);
  const scoreCache = new Map();
  const descendantScore = (entityId, visiting = new Set()) => {
    if (scoreCache.has(entityId)) return scoreCache.get(entityId);
    if (visiting.has(entityId)) return 0;
    const nextVisiting = new Set(visiting).add(entityId);
    const children = childrenFor(entityId).map((edge) => edge.child);
    const score = children.length
      + children.reduce((sum, childId) => sum + descendantScore(childId, nextVisiting), 0);
    scoreCache.set(entityId, score);
    return score;
  };
  const orderedRoots = roots.sort(
    (a, b) => descendantScore(b) - descendantScore(a)
      || titleOf(a).localeCompare(titleOf(b), "zh")
  );
  const availableGroupIds = new Set(orderedRoots.map((entityId) => {
    const entity = entityMap.get(entityId);
    return institutionGroupId(category, entityInstitutionGroup(entity, category));
  }));
  const previousExpandedGroupIds = expandedInstitutionGroupIds;
  expandedInstitutionGroupIds = expandedInstitutionGroupIds.filter((id) => availableGroupIds.has(id));
  if (previousExpandedGroupIds.length && !expandedInstitutionGroupIds.length && orderedRoots.length) {
    const fallback = entityMap.get(orderedRoots[0]);
    lastExpandedInstitutionGroupId = institutionGroupId(
      category,
      entityInstitutionGroup(fallback, category)
    );
    expandedInstitutionGroupIds = [lastExpandedInstitutionGroupId];
  }
  const virtualId = `category:${category}`;
  const showRoots = !collapsedHierarchyIds.has(virtualId);
  const visibleRoots = showRoots
    ? buildInstitutionGroupNodes({
        rootIds: orderedRoots,
        entityMap,
        category,
        groupNames: institutionGroupNames[category] || [],
        expandedGroupIds: expandedInstitutionGroupIds,
        treeForRoot: (id) => hierarchyTreeData(id, 2),
      })
    : [];
  return {
    id: virtualId,
    title: category,
    childCount: orderedRoots.length,
    hiddenCount: orderedRoots.length - visibleRoots.length,
    isVirtual: true,
    children: visibleRoots,
  };
}

function elementBounds(element) {
  try {
    return element.getBBox();
  } catch {
    return null;
  }
}

function fitDynamicNodeLabel(label, fullTitle, polygonBounds) {
  if (!label || !polygonBounds) return;
  const availableLength = polygonBounds.height - 4;
  const maxGlyphs = Math.max(1, Math.floor(availableLength / 17.14));
  const displayTitle = fullTitle.length > maxGlyphs
    ? `${fullTitle.slice(0, maxGlyphs - 1)}…`
    : fullTitle;
  setText(label, displayTitle);
  label.setAttribute("text-anchor", "middle");
  label.setAttribute("dominant-baseline", "central");
  label.setAttribute(
    "transform",
    `translate(${polygonBounds.x + polygonBounds.width / 2} ${polygonBounds.y + polygonBounds.height / 2})`
  );
}

const INLINE_DETAIL_BOUNDS = {
  left: 747.3 - 763.56,
  top: 160.96 - 196.11,
  bottom: 287.81 - 196.11,
};
const INLINE_COMPOSITION = {
  spineX: 763.56,
  panelX: 786.04,
  barX: 794.72,
  panelY: 160.96,
  panelHeight: 126.85,
  barY: 169.5,
  barHeight: 110,
  barWidth: 32,
  barPitch: 40,
  titleFontSize: 13.2,
  quotaFontSize: 7.5,
  personFontSize: 8,
  pageXOffset: 37,
  pageWidth: 126,
  pageShift: 134,
  panelRightPadding: 12,
  maxPanelWidth: 330,
  trackY: 284.6,
};
const INLINE_TITLE_POLYGON_BOUNDS = {
  x: 747.3,
  y: 160.96,
  width: 33.22,
  height: 126.85,
};
function displayStaffFor(entityId) {
  const byOfficial = new Map();
  for (const edge of staffFor(entityId)) {
    const official = entityMap.get(edge.official);
    if (!official?.title?.trim() || official.type !== "官职") continue;
    const current = byOfficial.get(edge.official);
    if (!current || (!current.staff_quota && edge.staff_quota)) {
      byOfficial.set(edge.official, edge);
    }
  }
  return [...byOfficial.values()];
}

function inlineCompositionGeometry(entityId) {
  // 一个有效官职实体只生成一根书脊；重复关系和无标题端点不占空槽。
  const staff = displayStaffFor(entityId);
  const selectedIndex = staff.findIndex(
    (edge) => edge.official === inlineDetailOfficialId.value
  );
  const barX = (index) => (
    INLINE_COMPOSITION.barX
    + index * INLINE_COMPOSITION.barPitch
    + (selectedIndex >= 0 && index > selectedIndex ? INLINE_COMPOSITION.pageShift : 0)
  );
  let contentRight = staff.length
    ? barX(staff.length - 1) + INLINE_COMPOSITION.barWidth
    : INLINE_COMPOSITION.panelX + 4;
  if (selectedIndex >= 0) {
    contentRight = Math.max(
      contentRight,
      barX(selectedIndex) + INLINE_COMPOSITION.pageXOffset + INLINE_COMPOSITION.pageWidth
    );
  }
  const totalContentWidth = contentRight + INLINE_COMPOSITION.panelRightPadding
    - INLINE_COMPOSITION.panelX;
  const panelWidth = Math.min(totalContentWidth, INLINE_COMPOSITION.maxPanelWidth);
  const panelRight = INLINE_COMPOSITION.panelX + panelWidth;
  const maxScroll = Math.max(0, totalContentWidth - panelWidth);
  inlineCompositionScrollOffset = clampCompositionScroll(
    inlineCompositionScrollOffset,
    maxScroll
  );
  if (selectedIndex >= 0 && maxScroll > 0) {
    const selectedLeft = barX(selectedIndex) - INLINE_COMPOSITION.panelX;
    const selectedRight = barX(selectedIndex)
      + INLINE_COMPOSITION.pageXOffset
      + INLINE_COMPOSITION.pageWidth
      - INLINE_COMPOSITION.panelX;
    if (selectedLeft < inlineCompositionScrollOffset) {
      inlineCompositionScrollOffset = selectedLeft;
    } else if (selectedRight > inlineCompositionScrollOffset + panelWidth) {
      inlineCompositionScrollOffset = selectedRight - panelWidth;
    }
    inlineCompositionScrollOffset = clampCompositionScroll(
      inlineCompositionScrollOffset,
      maxScroll
    );
  }
  return {
    staff,
    selectedIndex,
    barX,
    panelRight,
    panelWidth,
    totalContentWidth,
    maxScroll,
    scrollOffset: inlineCompositionScrollOffset,
    left: INLINE_DETAIL_BOUNDS.left,
    right: panelRight - INLINE_COMPOSITION.spineX,
  };
}

function renderInlineDetailCard(svg, layer, templateGroup, layout, entity) {
  if (!templateGroup || !layout || !entity) return;
  const card = templateGroup.cloneNode(true);
  card.classList.add("inline-design-detail", "dynamic-tree-node");
  card.dataset.entityId = String(entity.id);
  card.setAttribute("transform", `translate(${layout.x - 763.56} ${layout.y - 196.11})`);

  const titleLabel = findTextAt(card, 763.56, 196.11, 2);
  fitDynamicNodeLabel(titleLabel, entity.title, INLINE_TITLE_POLYGON_BOUNDS);

  const geometry = inlineCompositionGeometry(entity.id);
  const officialGroups = [...card.children].filter(
    (element) => element.tagName.toLowerCase() === "g" && element.querySelector("text.cls-64")
  );
  const officialTemplate = officialGroups.find((group) => (
    Math.abs(Number(group.querySelector("rect.cls-15")?.getAttribute("x")) - INLINE_COMPOSITION.barX) < 0.1
  )) || officialGroups[0];
  const pageGroup = [...card.children].find(
    (element) => element.tagName.toLowerCase() === "g" && element.querySelector("text.cls-66")
  );
  const pageTemplate = pageGroup?.cloneNode(true);
  officialGroups.forEach((group) => group.remove());
  pageGroup?.remove();

  // 设计稿中的七栏摘要在机构详情页重复信息且挤压核心编制视图，整体移除。
  const directoryLabel = [...card.querySelectorAll("text.cls-67")][0];
  directoryLabel?.parentElement?.remove();

  const panelRect = [...card.children].find((element) => (
    element.tagName.toLowerCase() === "rect"
      && Math.abs(Number(element.getAttribute("x")) - INLINE_COMPOSITION.panelX) < 0.1
  ));
  if (panelRect) {
    panelRect.setAttribute("y", String(INLINE_COMPOSITION.panelY));
    panelRect.setAttribute("height", String(INLINE_COMPOSITION.panelHeight));
    panelRect.setAttribute("width", String(geometry.panelRight - INLINE_COMPOSITION.panelX));
  }
  const panelBorder = [...card.children].find((element) => (
    element.tagName.toLowerCase() === "line"
      && Math.abs(Number(element.getAttribute("x1")) - 1075.8) < 0.1
  ));
  if (panelBorder) {
    panelBorder.setAttribute("x1", String(geometry.panelRight + 2.42));
    panelBorder.setAttribute("x2", String(geometry.panelRight + 2.42));
    panelBorder.setAttribute("y1", String(INLINE_COMPOSITION.panelY));
    panelBorder.setAttribute("y2", String(INLINE_COMPOSITION.panelY + INLINE_COMPOSITION.panelHeight));
  }
  const panelTrack = [...card.children].find((element) => (
    element.tagName.toLowerCase() === "rect" && element.classList.contains("cls-79")
  ));
  const panelProgress = [...card.children].find((element) => (
    element.tagName.toLowerCase() === "rect" && element.classList.contains("cls-37")
  ));
  const panelWidth = geometry.panelWidth;

  const clipId = `inline-composition-clip-${entity.id}`;
  const clipPath = document.createElementNS("http://www.w3.org/2000/svg", "clipPath");
  clipPath.id = clipId;
  clipPath.setAttribute("clipPathUnits", "userSpaceOnUse");
  const clipRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  clipRect.setAttribute("x", String(INLINE_COMPOSITION.panelX));
  clipRect.setAttribute("y", String(INLINE_COMPOSITION.panelY));
  clipRect.setAttribute("width", String(panelWidth));
  clipRect.setAttribute("height", String(INLINE_COMPOSITION.panelHeight));
  clipPath.appendChild(clipRect);
  svg.querySelector("defs")?.appendChild(clipPath);
  const compositionViewport = document.createElementNS("http://www.w3.org/2000/svg", "g");
  compositionViewport.classList.add("inline-composition-scroll-viewport");
  compositionViewport.setAttribute("clip-path", `url(#${clipId})`);
  const compositionContent = document.createElementNS("http://www.w3.org/2000/svg", "g");
  compositionContent.classList.add("inline-composition-scroll-content");
  compositionViewport.appendChild(compositionContent);

  const slider = compositionSliderGeometry({
    panelWidth,
    totalContentWidth: geometry.totalContentWidth,
    scrollOffset: geometry.scrollOffset,
    maxScroll: geometry.maxScroll,
  });
  const sliderEnabled = slider.enabled;
  const { thumbWidth, thumbTravel } = slider;
  const updateCompositionScroll = (nextOffset) => {
    inlineCompositionScrollOffset = clampCompositionScroll(nextOffset, geometry.maxScroll);
    compositionContent.setAttribute(
      "transform",
      `translate(${-inlineCompositionScrollOffset} 0)`
    );
    if (panelProgress && sliderEnabled) {
      const thumbX = INLINE_COMPOSITION.panelX
        + compositionSliderGeometry({
          panelWidth,
          totalContentWidth: geometry.totalContentWidth,
          scrollOffset: inlineCompositionScrollOffset,
          maxScroll: geometry.maxScroll,
        }).thumbOffset;
      panelProgress.setAttribute("x", String(thumbX));
    }
  };

  if (panelTrack) {
    panelTrack.removeAttribute("transform");
    panelTrack.setAttribute("x", String(INLINE_COMPOSITION.panelX));
    panelTrack.setAttribute("y", String(INLINE_COMPOSITION.trackY));
    panelTrack.setAttribute("width", String(panelWidth));
    panelTrack.setAttribute("height", "2.77");
    panelTrack.style.display = sliderEnabled ? "" : "none";
  }
  if (panelProgress) {
    panelProgress.removeAttribute("transform");
    panelProgress.setAttribute("y", String(INLINE_COMPOSITION.trackY - 0.7));
    panelProgress.setAttribute("width", String(thumbWidth));
    panelProgress.setAttribute("height", "4.2");
    panelProgress.setAttribute("rx", "2.1");
    panelProgress.style.display = sliderEnabled ? "" : "none";
    panelProgress.style.cursor = sliderEnabled ? "grab" : "default";
  }
  if (sliderEnabled && panelProgress) {
    const sliderHitArea = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    sliderHitArea.classList.add("inline-composition-slider-hit-area");
    sliderHitArea.setAttribute("x", String(INLINE_COMPOSITION.panelX));
    sliderHitArea.setAttribute("y", String(INLINE_COMPOSITION.trackY - 5));
    sliderHitArea.setAttribute("width", String(panelWidth));
    sliderHitArea.setAttribute("height", "12");
    sliderHitArea.setAttribute("fill", "transparent");
    sliderHitArea.style.cursor = "ew-resize";
    card.insertBefore(sliderHitArea, panelProgress);
    d3.select(sliderHitArea).on("click.inline-composition-slider", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const [pointerX] = d3.pointer(event, card);
      const desiredThumbOffset = Math.max(
        0,
        Math.min(thumbTravel, pointerX - INLINE_COMPOSITION.panelX - thumbWidth / 2)
      );
      updateCompositionScroll(desiredThumbOffset / Math.max(1, thumbTravel) * geometry.maxScroll);
    });
  }
  updateCompositionScroll(geometry.scrollOffset);

  const selectedOfficial = geometry.selectedIndex >= 0
    ? entityMap.get(geometry.staff[geometry.selectedIndex].official)
    : null;
  const values = selectedOfficial ? inlineDetailValues(selectedOfficial) : null;
  geometry.staff.forEach((edge, index) => {
    if (!officialTemplate) return;
    const group = officialTemplate.cloneNode(true);
    const label = group.querySelector("text.cls-64");
    const offsetX = geometry.barX(index) - INLINE_COMPOSITION.barX;
    group.setAttribute("transform", `translate(${offsetX} 0)`);
    for (const bar of group.querySelectorAll("rect")) {
      bar.setAttribute("y", String(INLINE_COMPOSITION.barY));
      bar.setAttribute("width", String(INLINE_COMPOSITION.barWidth));
      bar.setAttribute("height", String(INLINE_COMPOSITION.barHeight));
    }
    const officialTitleText = titleOf(edge.official);
    fitVerticalBarLabel(label, officialTitleText, group.querySelector("rect.cls-15"));
    const quota = group.querySelector("text.cls-72");
    const person = group.querySelector("text.cls-74");
    fitQuotaLabel(quota, person, edge, group.querySelector("rect.cls-15"));
    const isSelected = edge.official === inlineDetailOfficialId.value;
    label.style.fill = isSelected ? "#866d6d" : "#351704";
    group.style.cursor = "pointer";
    d3.select(group).on("click.inline-official", (event) => {
      event.preventDefault();
      event.stopPropagation();
      inlineDetailOfficialId.value = isSelected ? null : edge.official;
      inlineDetailField.value = "duty";
      refreshTemplate();
    });
    compositionContent.appendChild(group);
  });

  if (selectedOfficial && pageTemplate && values) {
    const pageX = geometry.barX(geometry.selectedIndex) + INLINE_COMPOSITION.pageXOffset;
    pageTemplate.setAttribute("transform", `translate(${pageX - 812.52} 0)`);
    for (const [index, pageRect] of [...pageTemplate.querySelectorAll("rect")].entries()) {
      pageRect.setAttribute("y", String(INLINE_COMPOSITION.barY + (index ? 4 : 0)));
      pageRect.setAttribute("width", String(INLINE_COMPOSITION.pageWidth));
      pageRect.setAttribute("height", String(INLINE_COMPOSITION.barHeight - (index ? 8 : 0)));
    }
    const description = pageTemplate.querySelector("text.cls-66");
    description.setAttribute(
      "transform",
      `translate(${812.52 + INLINE_COMPOSITION.pageWidth - 12} ${INLINE_COMPOSITION.barY + 10})`
    );
    description.style.fontSize = "9px";
    wrapVerticalText(description, values[inlineDetailField.value], 11, 12, 10.2);
    const descriptionTitle = document.createElementNS("http://www.w3.org/2000/svg", "title");
    descriptionTitle.textContent = `${selectedOfficial.title}：${values[inlineDetailField.value]}`;
    pageTemplate.appendChild(descriptionTitle);
    compositionContent.appendChild(pageTemplate);
  }

  const scrollComposition = (event) => {
    if (!sliderEnabled) return;
    event.preventDefault();
    event.stopPropagation();
    const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY)
      ? event.deltaX
      : event.deltaY;
    updateCompositionScroll(inlineCompositionScrollOffset + delta);
  };
  compositionViewport.addEventListener("wheel", scrollComposition, { passive: false });
  panelRect?.addEventListener("wheel", scrollComposition, { passive: false });
  if (panelProgress && sliderEnabled) {
    d3.select(panelProgress).call(
      d3.drag()
        .on("start", (event) => {
          event.sourceEvent?.stopPropagation();
          panelProgress.style.cursor = "grabbing";
        })
        .on("drag", (event) => {
          updateCompositionScroll(compositionScrollAfterDrag({
            currentOffset: inlineCompositionScrollOffset,
            deltaX: event.dx,
            maxScroll: geometry.maxScroll,
            thumbTravel,
          }));
        })
        .on("end", () => {
          panelProgress.style.cursor = "grab";
        })
    );
  }
  card.appendChild(compositionViewport);

  const cardTitle = document.createElementNS("http://www.w3.org/2000/svg", "title");
  cardTitle.textContent = `${entity.title}：点击官职翻开详情书页，双击机构书脊收起`;
  card.appendChild(cardTitle);
  d3.select(card)
    .on("click.inline-detail", (event) => event.stopPropagation())
    .on("dblclick.inline-detail", (event) => event.stopPropagation());
  if (titleLabel?.parentElement) {
    titleLabel.parentElement.style.cursor = "zoom-out";
    d3.select(titleLabel.parentElement).on("dblclick.inline-detail-close", (event) => {
      event.preventDefault();
      event.stopPropagation();
      expandedDetailId.value = null;
      inlineDetailOfficialId.value = null;
      refreshTemplate();
    });
  }
  layer.appendChild(card);
}

function hierarchyTemplates(svg) {
  if (hierarchyTemplateCache.has(svg)) return hierarchyTemplateCache.get(svg);
  const templateText = findTextAt(svg, 763.56, 196.11, 2);
  const templateGroup = templateText?.parentElement?.cloneNode(true);
  const inlineDetailTemplate = templateText?.parentElement?.parentElement?.cloneNode(true);
  const templatePolygonBounds = elementBounds(templateText?.parentElement?.querySelector("polygon"));
  const emperorText = findTextAt(svg, 1141.69, 153.09, 2);
  const emperorRect = [...svg.querySelectorAll("rect")].find(
    (element) => Math.abs(Number(element.getAttribute("x")) - 1128.61) <= 0.1
      && Math.abs(Number(element.getAttribute("y")) - 133.04) <= 0.1
      && Math.abs(Number(element.getAttribute("width")) - 60.84) <= 0.1
      && Math.abs(Number(element.getAttribute("height")) - 28.23) <= 0.1
  );
  if (!templateGroup || !emperorText || !emperorRect || !templatePolygonBounds) return null;

  // 缓存必须保存脱离画板的不可变模板。原节点随后会被状态绑定调整透明度，
  // 若直接缓存引用，下一次局部重绘会把变淡后的样式复制到虚拟分类标题。
  const emperorTextTemplate = emperorText.cloneNode(true);
  const emperorRectTemplate = emperorRect.cloneNode(true);

  // 原稿的“皇帝”只作为横排分类根的样式模板，不在动态机构树中重复显示。
  emperorText.style.display = "none";
  emperorRect.style.display = "none";

  const centerNodes = [...svg.children].filter((element) => {
    if (["defs", "style", "image"].includes(element.tagName.toLowerCase())) return false;
    const bounds = elementBounds(element);
    return bounds
      && bounds.x >= 480
      && bounds.y >= 130
      && bounds.x + bounds.width <= 1835
      && bounds.y + bounds.height <= 885;
  });
  centerNodes.forEach((element) => {
    element.style.display = "none";
  });

  const templates = {
    templateGroup,
    inlineDetailTemplate,
    templatePolygonBounds,
    emperorText: emperorTextTemplate,
    emperorRect: emperorRectTemplate,
  };
  hierarchyTemplateCache.set(svg, templates);
  return templates;
}

function renderDynamicHierarchy(svg) {
  svg.__dynamicHierarchyFitsViewport = true;
  const templates = hierarchyTemplates(svg);
  if (!templates) return;
  const {
    templateGroup,
    inlineDetailTemplate,
    templatePolygonBounds,
    emperorText,
    emperorRect,
  } = templates;

  const data = categoryForestData(selectedCategory.value);
  if (!data) return;
  const root = d3.hierarchy(data);
  const area = { left: 500, right: 1830, top: 130, bottom: 850 };
  const depthGap = 145;
  const expandedComposition = expandedDetailId.value != null
    ? inlineCompositionGeometry(expandedDetailId.value)
    : null;
  const virtualNodeWidth = (node) => Math.max(
    Number(emperorRect.getAttribute("width")),
    node.data.title.length * 17.14 + 24
  );
  const nodeLeftExtent = (node) => {
    if (node.data.isVirtual) return virtualNodeWidth(node) / 2;
    return expandedDetailId.value === node.data.id
      ? Math.abs(expandedComposition?.left ?? INLINE_DETAIL_BOUNDS.left)
      : 17;
  };
  const nodeRightExtent = (node) => {
    if (node.data.isVirtual) return virtualNodeWidth(node) / 2;
    return expandedDetailId.value === node.data.id
      ? Math.max(17, expandedComposition?.right ?? 17)
      : 17;
  };
  d3.tree()
    .nodeSize([52, depthGap])
    .separation((a, b) => {
      // D3 在同层按“右节点 a、左节点 b”询问间距；详情只向右展开，
      // 因此只把 b 的右宽度和 a 的左宽度计入，不能在左侧镜像留白。
      const requiredDistance = nodeRightExtent(b)
        + nodeLeftExtent(a)
        + (a.parent === b.parent ? 18 : 30);
      return Math.max(a.parent === b.parent ? 1 : 1.25, requiredDistance / 52);
    })(root);

  // 制度组是稳定导航层，必须完整铺在中央区域；下方机构树单独按当前组定位。
  // 不能直接用整棵不对称树的坐标，否则展开某组时会把其他制度组推出画布。
  const areaCenterX = (area.left + area.right) / 2;
  const institutionGroupNodes = (root.children || []).filter(
    (node) => node.data.isInstitutionGroup
  );
  const expandedInstitutionGroupIdSet = new Set(expandedInstitutionGroupIds);
  const expandedInstitutionGroupNodes = institutionGroupNodes.filter(
    (node) => expandedInstitutionGroupIdSet.has(node.data.id)
  );
  const institutionGroupRowX = new Map();
  if (institutionGroupNodes.length) {
    const nodeWidths = institutionGroupNodes.map(virtualNodeWidth);
    const availableGap = institutionGroupNodes.length > 1
      ? ((area.right - area.left) - d3.sum(nodeWidths)) / (institutionGroupNodes.length - 1)
      : 22;
    const groupGap = Math.max(12, Math.min(22, availableGap));
    const rowWidth = d3.sum(nodeWidths) + groupGap * (institutionGroupNodes.length - 1);
    let cursorX = areaCenterX - rowWidth / 2;
    for (const [index, node] of institutionGroupNodes.entries()) {
      const width = nodeWidths[index];
      institutionGroupRowX.set(node.data.id, cursorX + width / 2);
      cursorX += width + groupGap;
    }
  }

  const expandedBranchCenterX = new Map();
  const expandedBranchRanges = [];
  let focusedBranchNode = null;
  for (const expandedInstitutionGroupNode of expandedInstitutionGroupNodes) {
    let branchCenterX = institutionGroupRowX.get(expandedInstitutionGroupNode.data.id)
      ?? areaCenterX;
    if (expandedInstitutionGroupNode.descendants().length <= 1) {
      expandedBranchCenterX.set(expandedInstitutionGroupNode.data.id, branchCenterX);
      continue;
    }
    const branchNodes = expandedInstitutionGroupNode.descendants().slice(1);
    const anchorId = expansionAnchorId(
      expandedHierarchyPath,
      spaceAwareExpansion.value || expandedInstitutionGroupNodes.length > 1
    );
    const branchFocus = branchNodes.find((node) => node.data.id === anchorId);
    if (branchFocus) focusedBranchNode = branchFocus;
    const minOffset = d3.min(
      branchNodes,
      (node) => node.x - expandedInstitutionGroupNode.x - nodeLeftExtent(node)
    );
    const maxOffset = d3.max(
      branchNodes,
      (node) => node.x - expandedInstitutionGroupNode.x + nodeRightExtent(node)
    );
    const branchWidth = maxOffset - minOffset;
    const viewportWidth = area.right - area.left;
    if (branchFocus) {
      // 展开大机构时让它仍位于所属制度组正下方；超宽的下级树交给视口拖动，
      // 不能为了塞满画布把父节点漂到相邻制度组下面。
      branchCenterX = anchorBranchToGroup(
        branchCenterX,
        expandedInstitutionGroupNode.x,
        branchFocus.x
      );
    } else if (expandedInstitutionGroupNodes.length === 1) {
      branchCenterX = branchWidth <= viewportWidth
        ? Math.max(
            area.left - minOffset,
            Math.min(area.right - maxOffset, branchCenterX)
          )
        : areaCenterX - (minOffset + maxOffset) / 2;
    }
    expandedBranchCenterX.set(expandedInstitutionGroupNode.data.id, branchCenterX);
    expandedBranchRanges.push({
      id: expandedInstitutionGroupNode.data.id,
      left: branchCenterX + minOffset,
      right: branchCenterX + maxOffset,
    });
  }
  const expandedGroupBranchesFit = expandedInstitutionGroupNodes.length <= 1
    || horizontalRangesFit(expandedBranchRanges, area.left, area.right, 24);

  const clipId = "dynamic-tree-viewport-clip";
  const clipPath = document.createElementNS("http://www.w3.org/2000/svg", "clipPath");
  clipPath.id = clipId;
  const clipRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  clipRect.setAttribute("x", String(area.left));
  clipRect.setAttribute("y", String(area.top));
  clipRect.setAttribute("width", String(area.right - area.left));
  clipRect.setAttribute("height", String(area.bottom - area.top));
  clipPath.appendChild(clipRect);
  svg.querySelector("defs")?.appendChild(clipPath);

  const viewport = document.createElementNS("http://www.w3.org/2000/svg", "g");
  viewport.classList.add("dynamic-tree-viewport");
  viewport.setAttribute("clip-path", `url(#${clipId})`);
  const dragSurface = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  dragSurface.setAttribute("x", String(area.left));
  dragSurface.setAttribute("y", String(area.top));
  dragSurface.setAttribute("width", String(area.right - area.left));
  dragSurface.setAttribute("height", String(area.bottom - area.top));
  dragSurface.setAttribute("fill", "transparent");
  dragSurface.style.cursor = "grab";
  viewport.appendChild(dragSurface);

  const layer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  layer.classList.add("dynamic-tree-layer");
  viewport.appendChild(layer);
  svg.appendChild(viewport);

  const nodeLayout = new Map(root.descendants().map((node) => {
    let x;
    if (node.depth === 0) {
      x = areaCenterX;
    } else if (node.data.isInstitutionGroup) {
      x = institutionGroupRowX.get(node.data.id) ?? areaCenterX;
    } else {
      const institutionGroupAncestor = node.ancestors().find(
        (ancestor) => expandedInstitutionGroupIdSet.has(ancestor.data.id)
      );
      x = institutionGroupAncestor
        ? (expandedBranchCenterX.get(institutionGroupAncestor.data.id) ?? areaCenterX)
          + node.x - institutionGroupAncestor.x
        : areaCenterX + node.x - root.x;
    }
    // 制度组是新增的一层导航，不能再完整占用旧树的一层高度。
    // 一级机构贴近制度组，后续真实上下级仍沿用设计稿的层间距。
    const y = node.depth === 0
      ? 147.15
      : node.depth >= 2
        ? 305 + (node.depth - 2) * depthGap
        : 221.11 + (node.depth - 1) * depthGap;
    if (node.data.isVirtual) {
      const width = virtualNodeWidth(node);
      const height = Number(emperorRect.getAttribute("height"));
      return [node, { x, y, top: y - height / 2, bottom: y + height / 2, width, height }];
    }
    return [node, {
      x,
      y,
      left: x + (
        expandedDetailId.value === node.data.id
          ? expandedComposition?.left ?? INLINE_DETAIL_BOUNDS.left
          : -17
      ),
      right: x + (
        expandedDetailId.value === node.data.id ? expandedComposition?.right ?? 17 : 17
      ),
      top: y + (
        expandedDetailId.value === node.data.id
          ? INLINE_DETAIL_BOUNDS.top
          : templatePolygonBounds.y - 196.11
      ),
      bottom: y + (
        expandedDetailId.value === node.data.id
          ? INLINE_DETAIL_BOUNDS.bottom
          : templatePolygonBounds.y + templatePolygonBounds.height - 196.11
      ),
    }];
  }));

  if (!spaceAwareExpansion.value && focusedBranchNode?.children?.length) {
    const descendantLayouts = focusedBranchNode.descendants()
      .slice(1)
      .map((node) => nodeLayout.get(node));
    const descendantLeft = d3.min(
      descendantLayouts,
      (layout) => layout.left ?? layout.x - (layout.width || 34) / 2
    );
    const descendantRight = d3.max(
      descendantLayouts,
      (layout) => layout.right ?? layout.x + (layout.width || 34) / 2
    );
    const descendantShift = fitRangeShift(
      descendantLeft,
      descendantRight,
      area.left + 18,
      area.right - 18
    );
    if (descendantShift) {
      descendantLayouts.forEach((layout) => {
        layout.x += descendantShift;
        if (layout.left != null) layout.left += descendantShift;
        if (layout.right != null) layout.right += descendantShift;
      });
    }
  }

  const horizontalBounds = [...nodeLayout.values()].map((layout) => ({
    left: layout.left ?? layout.x - (layout.width || 34) / 2,
    right: layout.right ?? layout.x + (layout.width || 34) / 2,
  }));
  const contentLeft = d3.min(horizontalBounds, (bounds) => bounds.left) ?? area.left;
  const contentRight = d3.max(horizontalBounds, (bounds) => bounds.right) ?? area.right;
  const contentWidth = contentRight - contentLeft;
  const viewportWidth = area.right - area.left;
  const minPan = contentWidth <= viewportWidth ? 0 : area.right - contentRight;
  const maxPan = contentWidth <= viewportWidth ? 0 : area.left - contentLeft;
  const contentTop = d3.min([...nodeLayout.values()], (layout) => layout.top) ?? area.top;
  const contentBottom = d3.max([...nodeLayout.values()], (layout) => layout.bottom) ?? area.bottom;
  const contentHeight = contentBottom - contentTop;
  const viewportHeight = area.bottom - area.top;
  svg.__dynamicHierarchyFitsViewport = (
    contentWidth <= viewportWidth
    && contentHeight <= viewportHeight
    && expandedGroupBranchesFit
  );
  const minPanY = contentHeight <= viewportHeight ? 0 : area.bottom - contentBottom;
  const maxPanY = contentHeight <= viewportHeight ? 0 : area.top - contentTop;
  const panControls = document.createElementNS("http://www.w3.org/2000/svg", "g");
  panControls.classList.add("dynamic-tree-pan-controls");
  viewport.appendChild(panControls);
  const makePanRect = (className, attributes) => {
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.classList.add(className, "dynamic-tree-scroll-control");
    Object.entries(attributes).forEach(([name, value]) => rect.setAttribute(name, String(value)));
    panControls.appendChild(rect);
    return rect;
  };
  let horizontalTrack = null;
  let horizontalThumb = null;
  let horizontalHitArea = null;
  if (contentWidth > viewportWidth) {
    horizontalHitArea = makePanRect("dynamic-tree-scroll-hit-horizontal", {
      x: area.left,
      y: area.bottom - 13,
      width: viewportWidth,
      height: 13,
      fill: "transparent",
    });
    horizontalTrack = makePanRect("dynamic-tree-scroll-track-horizontal", {
      x: area.left,
      y: area.bottom - 6,
      width: viewportWidth,
      height: 1.5,
      rx: 0.75,
      fill: "#563905",
      opacity: 0.2,
    });
    horizontalTrack.style.pointerEvents = "none";
    horizontalThumb = makePanRect("dynamic-tree-scroll-thumb-horizontal", {
      x: area.left,
      y: area.bottom - 7.4,
      width: 42,
      height: 4.2,
      rx: 2.1,
      fill: "#563905",
      opacity: 0.7,
    });
    horizontalHitArea.style.cursor = "ew-resize";
    horizontalThumb.style.cursor = "grab";
  }
  let verticalTrack = null;
  let verticalThumb = null;
  let verticalHitArea = null;
  if (contentHeight > viewportHeight) {
    verticalHitArea = makePanRect("dynamic-tree-scroll-hit-vertical", {
      x: area.right - 13,
      y: area.top,
      width: 13,
      height: viewportHeight,
      fill: "transparent",
    });
    verticalTrack = makePanRect("dynamic-tree-scroll-track-vertical", {
      x: area.right - 6,
      y: area.top,
      width: 1.5,
      height: viewportHeight,
      rx: 0.75,
      fill: "#563905",
      opacity: 0.2,
    });
    verticalTrack.style.pointerEvents = "none";
    verticalThumb = makePanRect("dynamic-tree-scroll-thumb-vertical", {
      x: area.right - 7.4,
      y: area.top,
      width: 4.2,
      height: 42,
      rx: 2.1,
      fill: "#563905",
      opacity: 0.7,
    });
    verticalHitArea.style.cursor = "ns-resize";
    verticalThumb.style.cursor = "grab";
  }
  const updatePanControls = () => {
    if (horizontalThumb) {
      const geometry = panScrollbarGeometry({
        viewportSize: viewportWidth,
        contentSize: contentWidth,
        minPan,
        maxPan,
        currentPan: hierarchyPanX,
      });
      horizontalThumb.setAttribute("x", String(area.left + geometry.thumbOffset));
      horizontalThumb.setAttribute("width", String(geometry.thumbSize));
    }
    if (verticalThumb) {
      const geometry = panScrollbarGeometry({
        viewportSize: viewportHeight,
        contentSize: contentHeight,
        minPan: minPanY,
        maxPan: maxPanY,
        currentPan: hierarchyPanY,
      });
      verticalThumb.setAttribute("y", String(area.top + geometry.thumbOffset));
      verticalThumb.setAttribute("height", String(geometry.thumbSize));
    }
  };
  const applyHierarchyPan = (nextPanX, nextPanY = hierarchyPanY) => {
    hierarchyPanX = Math.max(minPan, Math.min(maxPan, nextPanX));
    hierarchyPanY = Math.max(minPanY, Math.min(maxPanY, nextPanY));
    layer.setAttribute("transform", `translate(${hierarchyPanX} ${hierarchyPanY})`);
    updatePanControls();
  };
  if (horizontalHitArea && horizontalThumb) {
    d3.select(horizontalHitArea).on("click.tree-scroll", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const geometry = panScrollbarGeometry({
        viewportSize: viewportWidth,
        contentSize: contentWidth,
        minPan,
        maxPan,
        currentPan: hierarchyPanX,
      });
      const [pointerX] = d3.pointer(event, viewport);
      const offset = pointerX - area.left - geometry.thumbSize / 2;
      applyHierarchyPan(
        panFromScrollbarOffset(offset, geometry.thumbTravel, minPan, maxPan),
        hierarchyPanY
      );
    });
    d3.select(horizontalThumb).call(
      d3.drag()
        .on("start", (event) => {
          event.sourceEvent?.stopPropagation();
          horizontalThumb.style.cursor = "grabbing";
        })
        .on("drag", (event) => {
          const geometry = panScrollbarGeometry({
            viewportSize: viewportWidth,
            contentSize: contentWidth,
            minPan,
            maxPan,
            currentPan: hierarchyPanX,
          });
          applyHierarchyPan(
            panFromScrollbarOffset(
              geometry.thumbOffset + event.dx,
              geometry.thumbTravel,
              minPan,
              maxPan
            ),
            hierarchyPanY
          );
        })
        .on("end", () => {
          horizontalThumb.style.cursor = "grab";
        })
    );
  }
  if (verticalHitArea && verticalThumb) {
    d3.select(verticalHitArea).on("click.tree-scroll", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const geometry = panScrollbarGeometry({
        viewportSize: viewportHeight,
        contentSize: contentHeight,
        minPan: minPanY,
        maxPan: maxPanY,
        currentPan: hierarchyPanY,
      });
      const [, pointerY] = d3.pointer(event, viewport);
      const offset = pointerY - area.top - geometry.thumbSize / 2;
      applyHierarchyPan(
        hierarchyPanX,
        panFromScrollbarOffset(offset, geometry.thumbTravel, minPanY, maxPanY)
      );
    });
    d3.select(verticalThumb).call(
      d3.drag()
        .on("start", (event) => {
          event.sourceEvent?.stopPropagation();
          verticalThumb.style.cursor = "grabbing";
        })
        .on("drag", (event) => {
          const geometry = panScrollbarGeometry({
            viewportSize: viewportHeight,
            contentSize: contentHeight,
            minPan: minPanY,
            maxPan: maxPanY,
            currentPan: hierarchyPanY,
          });
          applyHierarchyPan(
            hierarchyPanX,
            panFromScrollbarOffset(
              geometry.thumbOffset + event.dy,
              geometry.thumbTravel,
              minPanY,
              maxPanY
            )
          );
        })
        .on("end", () => {
          verticalThumb.style.cursor = "grab";
        })
    );
  }
  let nextPanX = hierarchyPanX;
  let nextPanY = hierarchyPanY;
  const expandedLayout = nodeLayout.get(
    root.descendants().find((node) => (
      !node.data.isVirtual && node.data.id === expandedDetailId.value
    ))
  );
  if (expandedLayout) {
    const detailLeft = expandedLayout.left + nextPanX;
    const detailRight = expandedLayout.right + nextPanX;
    const detailTop = expandedLayout.top + nextPanY;
    const detailBottom = expandedLayout.bottom + nextPanY;
    if (detailLeft < area.left) nextPanX += area.left - detailLeft;
    if (detailRight > area.right) nextPanX -= detailRight - area.right;
    if (detailTop < area.top) nextPanY += area.top - detailTop;
    if (detailBottom > area.bottom) nextPanY -= detailBottom - area.bottom;
  }
  applyHierarchyPan(nextPanX, nextPanY);

  d3.select(viewport)
    .call(d3.drag()
      .filter((event) => (
        !event.target.closest?.(".dynamic-tree-node")
        && !event.target.closest?.(".dynamic-tree-scroll-control")
      ))
      .on("start", () => {
        dragSurface.style.cursor = "grabbing";
      })
      .on("drag", (event) => {
        applyHierarchyPan(hierarchyPanX + event.dx, hierarchyPanY + event.dy);
      })
      .on("end", () => {
        dragSurface.style.cursor = "grab";
      }))
    .on("wheel.tree-pan", (event) => {
      if (contentWidth <= viewportWidth && contentHeight <= viewportHeight) return;
      event.preventDefault();
      if (contentHeight > viewportHeight && !event.shiftKey && Math.abs(event.deltaY) >= Math.abs(event.deltaX)) {
        applyHierarchyPan(hierarchyPanX, hierarchyPanY - event.deltaY);
      } else {
        const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
        applyHierarchyPan(hierarchyPanX - delta, hierarchyPanY);
      }
    }, { passive: false });

  const appendLink = (points) => {
    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    polyline.setAttribute("class", "cls-26 dynamic-tree-link");
    polyline.setAttribute("points", points);
    polyline.style.pointerEvents = "none";
    layer.appendChild(polyline);
  };

  // 每个虚拟节点使用独立横向总线，虚拟分组不冒充数据库中的历史层级边。
  const virtualParents = root.descendants().filter((node) => (
    node.data.isVirtual && node.children?.length
  ));
  for (const virtualParent of virtualParents) {
    const source = nodeLayout.get(virtualParent);
    const targets = virtualParent.children.map((child) => nodeLayout.get(child));
    const busY = (source.bottom + Math.min(...targets.map((target) => target.top))) / 2;
    const [busLeft, busRight] = virtualBusRange(
      source.x,
      targets.map((target) => target.x)
    );
    appendLink(`${source.x},${source.bottom} ${source.x},${busY}`);
    appendLink(`${busLeft},${busY} ${busRight},${busY}`);
    targets.forEach((target) => {
      appendLink(`${target.x},${busY} ${target.x},${target.top}`);
    });
  }

  // 更深层级严格从父节点外框底边连到子节点外框顶边。
  for (const link of root.links().filter((item) => !item.source.data.isVirtual)) {
    const source = nodeLayout.get(link.source);
    const target = nodeLayout.get(link.target);
    const middleY = (source.bottom + target.top) / 2;
    appendLink(
      `${source.x},${source.bottom} ${source.x},${middleY} ${target.x},${middleY} ${target.x},${target.top}`
    );
  }

  let nodeIndex = 0;
  let expandedDetailNode = null;
  for (const node of root.descendants()) {
    const layout = nodeLayout.get(node);
    const nodeGroup = node.data.isVirtual
      ? document.createElementNS("http://www.w3.org/2000/svg", "g")
      : templateGroup.cloneNode(true);
    nodeGroup.classList.add("dynamic-tree-node");
    nodeGroup.setAttribute("role", "button");
    nodeGroup.setAttribute("tabindex", "0");
    if (!node.data.isVirtual) nodeGroup.dataset.entityId = String(node.data.id);
    if (node.data.isVirtual) {
      nodeGroup.dataset.virtualRole = node.data.isInstitutionGroup ? "institution-group" : "category-root";
      nodeGroup.setAttribute("aria-label", `${node.data.title}，${node.data.childCount}项`);
      const rootRect = emperorRect.cloneNode(true);
      rootRect.style.removeProperty("display");
      rootRect.setAttribute("x", String(-layout.width / 2));
      rootRect.setAttribute("y", String(-layout.height / 2));
      rootRect.setAttribute("width", String(layout.width));
      rootRect.setAttribute("height", String(layout.height));
      rootRect.removeAttribute("opacity");
      rootRect.style.removeProperty("opacity");
      const rootLabel = emperorText.cloneNode(true);
      rootLabel.style.removeProperty("display");
      rootLabel.removeAttribute("opacity");
      rootLabel.style.removeProperty("opacity");
      rootLabel.removeAttribute("transform");
      rootLabel.setAttribute("x", "0");
      rootLabel.setAttribute("y", "0");
      rootLabel.setAttribute("text-anchor", "middle");
      rootLabel.setAttribute("dominant-baseline", "central");
      setText(rootLabel, node.data.title);
      if (node.data.isInstitutionGroup) rootRect.setAttribute("opacity", "0.82");
      nodeGroup.append(rootRect, rootLabel);
      nodeGroup.setAttribute("transform", `translate(${layout.x} ${layout.y})`);
    } else {
      nodeGroup.setAttribute("transform", `translate(${layout.x - 763.56} ${layout.y - 196.11})`);
    }
    const label = nodeGroup.querySelector("text");
    const hiddenCount = node.data.hiddenCount || 0;
    if (!node.data.isVirtual) setText(label, node.data.title);
    if (label && !node.data.isVirtual) label.dataset.entityId = String(node.data.id);
    const isExpanded = node.data.isInstitutionGroup
      ? expandedInstitutionGroupIds.includes(node.data.id)
      : node.data.isVirtual
        ? !collapsedHierarchyIds.has(node.data.id)
      : expandedHierarchyPath.includes(node.data.id);
    if (!node.data.isVirtual && node.data.id !== selectedId.value && !isExpanded) {
      nodeGroup.querySelector("g.cls-81")?.remove();
    }
    layer.appendChild(nodeGroup);

    const templatePolygon = node.data.isVirtual ? null : nodeGroup.querySelector("polygon");
    const polygonBounds = templatePolygon ? elementBounds(templatePolygon) : null;
    const hitBounds = node.data.isVirtual
      ? { x: -layout.width / 2, y: -layout.height / 2, width: layout.width, height: layout.height }
      : polygonBounds;
    if (hitBounds) {
      const hitArea = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      hitArea.classList.add("dynamic-tree-node-hit-area");
      hitArea.setAttribute("x", String(hitBounds.x));
      hitArea.setAttribute("y", String(hitBounds.y));
      hitArea.setAttribute("width", String(hitBounds.width));
      hitArea.setAttribute("height", String(hitBounds.height));
      hitArea.setAttribute("fill", "transparent");
      hitArea.setAttribute("pointer-events", "all");
      hitArea.setAttribute("aria-hidden", "true");
      nodeGroup.insertBefore(hitArea, nodeGroup.firstChild);
    }
    if (!node.data.isVirtual) fitDynamicNodeLabel(label, node.data.title, polygonBounds);
    if (!node.data.isVirtual && expandedDetailId.value === node.data.id) {
      // 详情 SVG 自带同一根书脊，隐藏基础节点以免两层描边和文字叠在一起。
      nodeGroup.style.visibility = "hidden";
    }
    if (label && polygonBounds) {
      const clipId = `dynamic-tree-node-clip-${nodeIndex}`;
      nodeIndex += 1;
      const clipPath = document.createElementNS("http://www.w3.org/2000/svg", "clipPath");
      clipPath.id = clipId;
      clipPath.setAttribute("clipPathUnits", "userSpaceOnUse");
      const clipRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      clipRect.setAttribute("x", String(polygonBounds.x + 3));
      clipRect.setAttribute("y", String(polygonBounds.y + 2));
      clipRect.setAttribute("width", String(polygonBounds.width - 6));
      clipRect.setAttribute("height", String(polygonBounds.height - 4));
      clipPath.appendChild(clipRect);
      svg.querySelector("defs")?.appendChild(clipPath);
      const labelClipGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      labelClipGroup.setAttribute("clip-path", `url(#${clipId})`);
      label.parentNode.insertBefore(labelClipGroup, label);
      labelClipGroup.appendChild(label);
    }
    if (!node.data.isVirtual && polygonBounds && hiddenCount > 0) {
      const bounds = polygonBounds;
      const barCount = Math.min(5, Math.max(1, Math.ceil(Math.log2(hiddenCount + 1))));
      for (let index = 0; index < barCount; index += 1) {
        const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        bar.setAttribute("x", String(bounds.x + 1));
        bar.setAttribute("y", String(bounds.y + bounds.height - 4 - index * 3));
        bar.setAttribute("width", String(bounds.width - 2));
        bar.setAttribute("height", "1.8");
        bar.setAttribute("fill", "#563905");
        bar.setAttribute("opacity", ".55");
        nodeGroup.appendChild(bar);
      }
    }

    const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
    const interactionHint = node.data.childCount
      ? (isExpanded ? "；再次点击收起下级机构" : "；点击展开下级机构")
      : "";
    const detailHint = node.data.isVirtual ? "" : "；双击展开机构详情";
    title.textContent = hiddenCount
      ? `${node.data.title}；尚有 ${hiddenCount} 个下级机构未展开${interactionHint}${detailHint}`
      : `${node.data.title}${interactionHint}${detailHint}`;
    nodeGroup.appendChild(title);
    if (!node.data.isVirtual) nodeGroup.setAttribute("aria-label", title.textContent);

    nodeGroup.style.cursor = "pointer";
    if (!node.data.isVirtual && expandedDetailId.value === node.data.id) expandedDetailNode = node;
    const toggleVirtualNode = (event) => {
      event.preventDefault();
      event.stopPropagation();
      lastHierarchyClick = null;
      if (node.data.isInstitutionGroup) {
        const wasExpanded = expandedInstitutionGroupIds.includes(node.data.id);
        expandedInstitutionGroupIds = toggleInstitutionGroupIds(
          expandedInstitutionGroupIds,
          node.data.id,
          spaceAwareExpansion.value
        );
        if (!wasExpanded) lastExpandedInstitutionGroupId = node.data.id;
        expandedHierarchyPath = [];
        lastExpandedHierarchyId = null;
        hierarchyPanX = 0;
        hierarchyPanY = 0;
        if (!wasExpanded) {
          renderInstitutionGroupCandidate(node.data.id);
          return;
        }
      } else if (collapsedHierarchyIds.has(node.data.id)) {
        collapsedHierarchyIds.delete(node.data.id);
      } else {
        collapsedHierarchyIds.add(node.data.id);
        expandedHierarchyPath = [];
        lastExpandedHierarchyId = null;
      }
      hierarchyPanX = 0;
      hierarchyPanY = 0;
      refreshTemplate();
    };
    const nodeSelection = d3.select(nodeGroup)
      .on("click.dynamic-tree", (event) => {
        if (node.data.isVirtual) {
          toggleVirtualNode(event);
          return;
        }
        event.preventDefault();
        event.stopPropagation();
        const repeatedClick = lastHierarchyClick?.id === node.data.id
          && event.timeStamp - lastHierarchyClick.timeStamp <= 360;
        if (repeatedClick) {
          expandedHierarchyPath = lastHierarchyClick.expandedHierarchyPath;
          lastExpandedHierarchyId = lastHierarchyClick.lastExpandedHierarchyId;
          hierarchyPanX = lastHierarchyClick.panX;
          hierarchyPanY = lastHierarchyClick.panY;
          lastHierarchyClick = null;
          detailPanelScrollOffset = 0;
          selectedId.value = node.data.id;
          inlineDetailField.value = "duty";
          inlineCompositionScrollOffset = 0;
          expandedDetailId.value = node.data.id;
          inlineDetailOfficialId.value = null;
          refreshTemplate();
          return;
        }
        lastHierarchyClick = {
          id: node.data.id,
          timeStamp: event.timeStamp,
          expandedHierarchyPath: [...expandedHierarchyPath],
          lastExpandedHierarchyId,
          panX: hierarchyPanX,
          panY: hierarchyPanY,
        };
        detailPanelScrollOffset = 0;
        inlineCompositionScrollOffset = 0;
        expandedDetailId.value = null;
        inlineDetailOfficialId.value = null;
        selectedId.value = node.data.id;
        if (node.data.childCount) {
          const expandedIndex = expandedHierarchyPath.indexOf(node.data.id);
          if (expandedIndex >= 0) {
            expandedHierarchyPath = removeExpandedSubtree(
              expandedHierarchyPath,
              hierarchySubtreeIds(node.data.id)
            );
            lastExpandedHierarchyId = expandedHierarchyPath.at(-1) ?? null;
          } else {
            const fallbackPath = hierarchyExpansionPath(node);
            expandedHierarchyPath = mergeExpansionPaths(
              expandedHierarchyPath,
              fallbackPath,
              spaceAwareExpansion.value
            );
            lastExpandedHierarchyId = node.data.id;
            renderExpansionCandidate(fallbackPath);
            return;
          }
        }
        refreshTemplate();
      })
      .on("dblclick.dynamic-tree-detail", (event) => {
        // 双击已由连续两次 click 跨 SVG 重绘识别；这里只阻止浏览器默认行为。
        event.preventDefault();
        event.stopPropagation();
      });
    nodeSelection.on("keydown.dynamic-tree", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      if (node.data.isVirtual) {
        toggleVirtualNode(event);
      } else {
        event.preventDefault();
        event.stopPropagation();
        nodeGroup.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      }
    });
  }

  if (expandedDetailNode) {
    renderInlineDetailCard(
      svg,
      layer,
      inlineDetailTemplate,
      nodeLayout.get(expandedDetailNode),
      entityMap.get(expandedDetailNode.data.id)
    );
  }
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
  const parentEdge = hierarchyEdgesForView().find((edge) => edge.child === focus.id);
  const siblings = parentEdge
    ? childrenFor(parentEdge.parent).map((edge) => edge.child).filter((id) => id !== focus.id)
    : [];
  assignSlots(siblingSlots, siblings);
  const contextSlot = findTextAt(svg, 1446.2, 183, 2);
  if (contextSlot) assignSlots([contextSlot], parentEdge ? [parentEdge.parent] : []);
}

function populateCompositionCenter(svg) {
  const focus = graphFocusEntity();
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
  if (!focus) {
    assignSlots(slots, []);
    return;
  }
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
  if (viewMode.value === "hierarchy") renderDynamicHierarchy(svg);
  else populateCompositionCenter(svg);
}

function bindEntityTexts(svg) {
  const activeIds = new Set();
  for (const edge of hierarchyEdgesForView()) {
    activeIds.add(edge.parent);
    activeIds.add(edge.child);
  }
  for (const edge of staffEdgesForView()) {
    activeIds.add(edge.org);
    activeIds.add(edge.official);
  }

  d3.select(svg)
    .selectAll("text")
    .each(function () {
      if (this.closest(".dynamic-tree-layer")) return;
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
          selectLinkedEntity(entity.id);
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
  panelGroup.__topRightBorder = [...panelGroup.querySelectorAll("polyline")].find((polyline) => (
    (polyline.getAttribute("points") || "").includes("475.49 497.57 308.55 497.57")
  ));

  const defs = svg.querySelector("defs") || svg.insertBefore(
    document.createElementNS("http://www.w3.org/2000/svg", "defs"),
    svg.firstChild
  );
  const clipPath = document.createElementNS("http://www.w3.org/2000/svg", "clipPath");
  clipPath.id = "detail-panel-content-clip";
  clipPath.setAttribute("clipPathUnits", "userSpaceOnUse");
  const clipRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  clipRect.setAttribute("x", "88");
  clipRect.setAttribute("y", "524.81");
  clipRect.setAttribute("width", "371");
  clipRect.setAttribute("height", "352.41");
  clipPath.appendChild(clipRect);
  defs.appendChild(clipPath);

  const scrollViewport = document.createElementNS("http://www.w3.org/2000/svg", "g");
  scrollViewport.classList.add("detail-panel-scroll-viewport");
  scrollViewport.setAttribute("clip-path", "url(#detail-panel-content-clip)");
  const scrollContent = document.createElementNS("http://www.w3.org/2000/svg", "g");
  scrollContent.classList.add("detail-panel-scroll-content");
  scrollViewport.appendChild(scrollContent);
  panelGroup.appendChild(scrollViewport);

  const bodyPositions = [
    [101.29, 570.06],
    [100.33, 536.92],
    [101.29, 783.54],
    [100.33, 750.4],
    [100.33, 846.08],
  ];
  const contentNodes = bodyPositions
    .map(([x, y]) => findTextAt(svg, x, y))
    .filter(Boolean);
  const labelTemplate = findTextAt(svg, 100.33, 536.92)?.cloneNode(false);
  const contentTemplate = findTextAt(svg, 101.29, 570.06)?.cloneNode(false);
  contentNodes.forEach((node) => node.remove());
  if (labelTemplate && contentTemplate) {
    const sectionLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    sectionLayer.classList.add("detail-panel-sections");
    for (const field of INLINE_DETAIL_FIELDS) {
      const label = labelTemplate.cloneNode(false);
      label.dataset.detailSectionLabel = field.key;
      const content = contentTemplate.cloneNode(false);
      content.dataset.detailSectionContent = field.key;
      sectionLayer.append(label, content);
    }
    scrollContent.appendChild(sectionLayer);
  }

  const scrollTrack = [...panelGroup.querySelectorAll("rect")].find((rect) => (
    Math.abs(Number(rect.getAttribute("x")) - 471.34) < 1
      && Math.abs(Number(rect.getAttribute("y")) - 524.81) < 1
      && Number(rect.getAttribute("height")) > 300
  ));
  const scrollThumb = [...panelGroup.querySelectorAll("rect")].find((rect) => (
    Math.abs(Number(rect.getAttribute("x")) - 471.34) < 1
      && Math.abs(Number(rect.getAttribute("y")) - 524.81) < 1
      && Number(rect.getAttribute("height")) > 20
      && Number(rect.getAttribute("height")) < 200
  ));
  if (scrollTrack) {
    scrollTrack.removeAttribute("class");
    scrollTrack.classList.add("detail-panel-scroll-track");
    scrollTrack.setAttribute("x", "465.25");
    scrollTrack.setAttribute("width", "1.5");
    scrollTrack.setAttribute("rx", "0.75");
    scrollTrack.setAttribute("fill", "#563905");
    scrollTrack.setAttribute("opacity", "0.2");
  }
  if (scrollThumb) {
    scrollThumb.removeAttribute("class");
    scrollThumb.classList.add("detail-panel-scroll-thumb");
    scrollThumb.setAttribute("x", "464.25");
    scrollThumb.setAttribute("width", "3.5");
    scrollThumb.setAttribute("rx", "1.75");
    scrollThumb.setAttribute("fill", "#563905");
    scrollThumb.setAttribute("opacity", "0.62");
  }

  const scrollHitArea = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  scrollHitArea.classList.add("detail-panel-scroll-hit-area");
  scrollHitArea.setAttribute("x", String(DETAIL_PANEL_BOUNDS.x));
  scrollHitArea.setAttribute("y", "524.81");
  scrollHitArea.setAttribute("width", String(DETAIL_PANEL_BOUNDS.width));
  scrollHitArea.setAttribute("height", "352.41");
  scrollHitArea.setAttribute("fill", "transparent");
  scrollHitArea.setAttribute("pointer-events", "all");
  scrollHitArea.style.cursor = "default";
  panelGroup.insertBefore(scrollHitArea, scrollViewport);
  if (scrollThumb) panelGroup.appendChild(scrollThumb);

  const updateScroll = () => {
    const contentBottom = Number(scrollContent.dataset.contentBottom || 536.92);
    const viewportBottom = 872;
    const maxScroll = Math.max(0, contentBottom - viewportBottom);
    detailPanelScrollOffset = Math.max(0, Math.min(maxScroll, detailPanelScrollOffset));
    scrollContent.setAttribute("transform", `translate(0 ${-detailPanelScrollOffset})`);
    if (!scrollTrack || !scrollThumb) return;
    const trackY = Number(scrollTrack.getAttribute("y"));
    const trackHeight = Number(scrollTrack.getAttribute("height"));
    const contentHeight = Math.max(1, contentBottom - 536.92);
    const viewportHeight = viewportBottom - 536.92;
    const proportionalThumbHeight = trackHeight * viewportHeight / contentHeight;
    const thumbHeight = Math.max(30, Math.min(96, trackHeight, proportionalThumbHeight));
    const thumbTravel = trackHeight - thumbHeight;
    const thumbY = trackY + (maxScroll ? detailPanelScrollOffset / maxScroll * thumbTravel : 0);
    scrollThumb.setAttribute("y", String(thumbY));
    scrollThumb.setAttribute("height", String(thumbHeight));
    scrollTrack.style.display = maxScroll ? "" : "none";
    scrollThumb.style.display = maxScroll ? "" : "none";
    scrollThumb.style.cursor = maxScroll ? "grab" : "default";
  };
  panelGroup.__updateDetailScroll = updateScroll;

  const scrollDetailPanel = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const renderedHeight = svg.getBoundingClientRect().height || svg.viewBox.baseVal.height;
    detailPanelScrollOffset += event.deltaY * svg.viewBox.baseVal.height / renderedHeight;
    updateScroll();
  };
  // 正文链接位于 scrollViewport，空白区域由底层 hit area 承接；
  // 两层都监听滚轮，保持整个详情框可滚动。
  scrollViewport.addEventListener("wheel", scrollDetailPanel, { passive: false });
  scrollHitArea.addEventListener("wheel", scrollDetailPanel, { passive: false });

  if (scrollThumb) {
    d3.select(scrollThumb).call(
      d3.drag()
        .on("start", (event) => {
          event.sourceEvent?.stopPropagation();
          scrollThumb.style.cursor = "grabbing";
        })
        .on("drag", (event) => {
          const contentBottom = Number(scrollContent.dataset.contentBottom || 536.92);
          const maxScroll = Math.max(0, contentBottom - 872);
          const trackHeight = Number(scrollTrack?.getAttribute("height") || 352.41);
          const thumbHeight = Number(scrollThumb.getAttribute("height"));
          const thumbTravel = Math.max(1, trackHeight - thumbHeight);
          detailPanelScrollOffset += event.dy * maxScroll / thumbTravel;
          updateScroll();
        })
        .on("end", updateScroll)
    );
  }

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
  if (!entity) {
    const title = findTextAt(svg, 99.85, 505.87);
    const year = findTextAt(svg, 189.74, 502.91);
    setText(title, selectedCategory.value);
    setText(year, selectedRangeLabel());
    constrainTextWidth(title, 78);
    constrainTextWidth(year, 270);
    const [firstField, ...hiddenFields] = INLINE_DETAIL_FIELDS;
    const label = svg.querySelector(`[data-detail-section-label='${firstField.key}']`);
    const content = svg.querySelector(`[data-detail-section-content='${firstField.key}']`);
    if (label && content) {
      label.style.display = "";
      content.style.display = "";
      label.setAttribute("transform", "translate(100.33 536.92)");
      content.setAttribute("transform", "translate(101.29 561.92)");
      setText(label, "当前截面：");
      wrapText(
        content,
        "所选年份没有可展示的非统称根机构。统称实体仍按规则排除；可切换年份或取消时间选择查看。",
        28,
        18,
        Infinity
      );
    }
    hiddenFields.forEach((field) => {
      const hiddenLabel = svg.querySelector(`[data-detail-section-label='${field.key}']`);
      const hiddenContent = svg.querySelector(`[data-detail-section-content='${field.key}']`);
      if (hiddenLabel) hiddenLabel.style.display = "none";
      if (hiddenContent) hiddenContent.style.display = "none";
    });
    const scrollContent = svg.querySelector(".detail-panel-scroll-content");
    if (scrollContent) scrollContent.dataset.contentBottom = "650";
    detailPanelScrollOffset = 0;
    svg.querySelector(".detail-panel-group")?.__updateDetailScroll?.();
    return;
  }
  const values = inlineDetailValues(entity);
  const staff = displayStaffFor(entity.id);
  const children = childrenFor(entity.id);

  const detailSlots = {
    title: findTextAt(svg, 99.85, 505.87),
    year: findTextAt(svg, 189.74, 502.91),
  };
  setText(detailSlots.title, entity.title);
  setText(detailSlots.year, selectedRangeLabel());
  constrainTextWidth(detailSlots.title, 78);
  constrainTextWidth(detailSlots.year, 270);
  const panelGroup = svg.querySelector(".detail-panel-group");
  const topRightBorder = panelGroup?.__topRightBorder;
  if (topRightBorder && detailSlots.year) {
    const yearX = position(detailSlots.year)?.x ?? 189.74;
    const lineStart = Math.max(
      308.55,
      Math.min(468, yearX + detailSlots.year.getComputedTextLength() + 8)
    );
    topRightBorder.setAttribute(
      "points",
      `229.27 877.67 475.49 877.67 475.49 497.57 ${lineStart} 497.57`
    );
  }
  let cursorY = 536.92;
  for (const field of INLINE_DETAIL_FIELDS) {
    const label = svg.querySelector(`[data-detail-section-label='${field.key}']`);
    const content = svg.querySelector(`[data-detail-section-content='${field.key}']`);
    if (!label || !content) continue;
    label.style.display = "";
    content.style.display = "";
    label.setAttribute("transform", `translate(100.33 ${cursorY})`);
    setText(label, field.label);
    label.style.cursor = "default";
    label.style.fill = inlineDetailField.value === field.key ? "#866d6d" : "#351704";
    d3.select(label).on("click.detail-field-link", null);
    cursorY += 25;
    content.setAttribute("transform", `translate(101.29 ${cursorY})`);
    let lines;
    if (field.key === "children" && children.length) {
      const tokens = children.flatMap((edge, index) => [
        { text: titleOf(edge.child), entityId: edge.child },
        ...(index < children.length - 1 ? [{ text: "、" }] : []),
      ]);
      lines = renderLinkedTokens(content, tokens, values.children);
    } else if (field.key === "composition" && staff.length) {
      const tokens = staff.flatMap((edge, index) => [
        { text: titleOf(edge.official), entityId: edge.official },
        { text: `（${edge.staff_quota ? `${edge.staff_quota}人` : "员额未载"}${edge.staff_type ? `，${edge.staff_type}` : ""}）` },
        ...(index < staff.length - 1 ? [{ text: "；" }] : []),
      ]);
      lines = renderLinkedTokens(content, tokens, values.composition);
    } else {
      lines = wrapText(content, values[field.key], 28, 18, Infinity);
    }
    cursorY += Math.max(1, lines) * 18 + 13;
  }
  cursorY += 2;
  const scrollContent = svg.querySelector(".detail-panel-scroll-content");
  if (scrollContent) scrollContent.dataset.contentBottom = String(cursorY);
  const updateScroll = svg.querySelector(".detail-panel-group")?.__updateDetailScroll;
  if (pendingDetailSectionKey) {
    const target = svg.querySelector(
      `[data-detail-section-label='${pendingDetailSectionKey}']`
    );
    const targetY = position(target)?.y;
    if (Number.isFinite(targetY)) {
      detailPanelScrollOffset = Math.max(0, targetY - 536.92);
    }
    pendingDetailSectionKey = null;
  }
  updateScroll?.();

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
        detailPanelScrollOffset = 0;
        selectedId.value = edge.official;
        refreshTemplate();
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
  if (!graphFocusEntity()) {
    candidates.forEach((candidate) => {
      candidate.style.opacity = "0";
    });
    return;
  }
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

function bindSpaceAwareExpansionControl(svg) {
  let control = svg.querySelector(".space-aware-expansion-control");
  if (!control) {
    const ns = "http://www.w3.org/2000/svg";
    control = document.createElementNS(ns, "g");
    control.classList.add("space-aware-expansion-control");
    control.setAttribute("transform", "translate(1392 73)");
    control.setAttribute("role", "switch");
    control.setAttribute("tabindex", "0");
    control.style.cursor = "pointer";

    const outline = document.createElementNS(ns, "rect");
    outline.dataset.controlPart = "outline";
    outline.setAttribute("x", "0");
    outline.setAttribute("y", "0");
    outline.setAttribute("width", "126");
    outline.setAttribute("height", "36");
    outline.setAttribute("fill", "#563905");
    outline.setAttribute("stroke", "#563905");

    const backPage = document.createElementNS(ns, "rect");
    backPage.dataset.controlPart = "back-page";
    backPage.setAttribute("x", "12");
    backPage.setAttribute("y", "9");
    backPage.setAttribute("width", "11");
    backPage.setAttribute("height", "16");
    backPage.setAttribute("fill", "none");
    backPage.setAttribute("stroke", "#563905");
    backPage.setAttribute("stroke-width", "0.9");

    const frontPage = backPage.cloneNode(false);
    frontPage.dataset.controlPart = "front-page";
    frontPage.setAttribute("x", "18");
    frontPage.setAttribute("y", "12");

    const label = document.createElementNS(ns, "text");
    label.setAttribute("class", "cls-49");
    label.setAttribute("x", "38");
    label.setAttribute("y", "18");
    label.setAttribute("dominant-baseline", "central");
    label.textContent = "空间展开";

    const title = document.createElementNS(ns, "title");
    control.append(outline, backPage, frontPage, label, title);
    svg.appendChild(control);
  }

  const sync = () => {
    const enabled = spaceAwareExpansion.value;
    const outline = control.querySelector("[data-control-part='outline']");
    const frontPage = control.querySelector("[data-control-part='front-page']");
    control.style.display = viewMode.value === "hierarchy" ? "" : "none";
    control.setAttribute("aria-checked", String(enabled));
    control.setAttribute(
      "aria-label",
      enabled ? "关闭空间展开，恢复单节点展开" : "开启空间展开，空间足够时保留多个节点"
    );
    outline.setAttribute("fill-opacity", enabled ? "0.12" : "0");
    outline.setAttribute("stroke-width", enabled ? "1.35" : "0.8");
    frontPage.setAttribute("fill", enabled ? "#563905" : "none");
    frontPage.setAttribute("fill-opacity", enabled ? "0.16" : "0");
    control.querySelector("title").textContent = enabled
      ? "空间展开已开启：空间足够时保留多个机构分支"
      : "空间展开已关闭：点击新节点时收起旧分支";
  };

  const toggle = (event) => {
    event.preventDefault();
    event.stopPropagation();
    lastHierarchyClick = null;
    spaceAwareExpansion.value = !spaceAwareExpansion.value;
    if (!spaceAwareExpansion.value) {
      expandedInstitutionGroupIds = collapseInstitutionGroups(
        expandedInstitutionGroupIds,
        lastExpandedInstitutionGroupId
      );
    }
    if (!spaceAwareExpansion.value && expandedHierarchyPath.length > 1) {
      const focusId = lastExpandedHierarchyId ?? expandedHierarchyPath.at(-1);
      expandedHierarchyPath = focusId == null
        ? []
        : resolveHierarchyContext(focusId, hierarchyEdgesForView(), entityMap).path;
    }
    hierarchyPanX = 0;
    hierarchyPanY = 0;
    sync();
    refreshTemplate();
  };
  d3.select(control)
    .on("click.space-aware-expansion", toggle)
    .on("keydown.space-aware-expansion", (event) => {
      if (event.key === "Enter" || event.key === " ") toggle(event);
    })
    .on("mouseenter.space-aware-expansion", () => {
      control.querySelector("[data-control-part='outline']")?.setAttribute("stroke-width", "1.35");
    })
    .on("mouseleave.space-aware-expansion", sync);
  svg.__syncSpaceAwareExpansionControl = sync;
  sync();
}

function bindTemplateControls(svg) {
  svg.querySelectorAll(".view-mode-hit-area").forEach((element) => element.remove());
  const categoryItems = [...svg.querySelectorAll("text")]
    .filter((textElement) => !textElement.closest(".dynamic-tree-layer"))
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
      if (this.closest(".dynamic-tree-layer")) return;
      const text = normalizeText(this);
      if (text === "层级视图" || text === "编制视图") {
        const activateView = (event) => {
          event.stopPropagation();
          viewMode.value = text === "层级视图" ? "hierarchy" : "composition";
        };
        this.style.cursor = "pointer";
        this.style.fontWeight = (text === "层级视图") === (viewMode.value === "hierarchy") ? "700" : "400";
        d3.select(this).on("click.view-mode", activateView);
        const bounds = elementBounds(this);
        if (bounds && this.parentNode) {
          const hitArea = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          hitArea.classList.add("view-mode-hit-area");
          hitArea.setAttribute("x", String(bounds.x - 12));
          hitArea.setAttribute("y", String(bounds.y - 8));
          hitArea.setAttribute("width", String(bounds.width + 24));
          hitArea.setAttribute("height", String(bounds.height + 16));
          hitArea.setAttribute("fill", "transparent");
          hitArea.setAttribute("pointer-events", "all");
          hitArea.style.cursor = "pointer";
          const transform = this.getAttribute("transform");
          if (transform) hitArea.setAttribute("transform", transform);
          this.parentNode.insertBefore(hitArea, this);
          d3.select(hitArea).on("click.view-mode", activateView);
        }
      }

      if (CATEGORY_NAMES.includes(text)) {
        const category = text;
        const group = this.parentElement;
        const activate = (event) => {
          event.stopPropagation();
          lastHierarchyClick = null;
          detailPanelScrollOffset = 0;
          collapsedHierarchyIds.clear();
          expandedHierarchyPath = [];
          lastExpandedHierarchyId = null;
          hierarchyPanX = 0;
          hierarchyPanY = 0;
          selectedCategory.value = category;
          selectedId.value = null;
          expandedDetailId.value = null;
          inlineDetailOfficialId.value = null;
          const focus = categoryFocus(category);
          lastExpandedInstitutionGroupId = focus
            ? institutionGroupId(category, entityInstitutionGroup(focus, category))
            : null;
          expandedInstitutionGroupIds = lastExpandedInstitutionGroupId
            ? [lastExpandedInstitutionGroupId]
            : [];
          refreshTemplate({ rebindControls: true });
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

  bindSpaceAwareExpansionControl(svg);

}

function bindTimelineRange(svg) {
  const originalTriangle = [...svg.querySelectorAll("path")].find(
    (path) => (path.getAttribute("d") || "").startsWith("M837.34,1027.81")
  );
  const originalYear = [...svg.querySelectorAll("text")].find(
    (text) => normalizeText(text) === "1109年" && Math.abs((position(text)?.y ?? 0) - 1035.22) < 1
  );
  const originalGuideLine = [...svg.querySelectorAll("line")].find(
    (line) => Math.abs(Number(line.getAttribute("x1")) - 838.19) < 0.1
      && Math.abs(Number(line.getAttribute("y1")) - 913.08) < 0.1
      && Math.abs(Number(line.getAttribute("y2")) - 1021.73) < 0.1
  );
  if (!originalTriangle || !originalYear) return;
  originalTriangle.style.display = "none";
  originalYear.style.display = "none";
  // 设计稿的 1109 年标记由三段竖线和上下端帽组成，需与静态三角一起隐藏。
  originalGuideLine?.parentElement?.parentElement?.style.setProperty("display", "none");

  const timelineLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  timelineLayer.classList.add("timeline-range-control");
  svg.appendChild(timelineLayer);

  const brush = d3.brushX()
    .extent([[TIMELINE_X_MIN, 909.73], [TIMELINE_X_MAX, 1042]])
    .handleSize(18);
  const brushLayer = d3.select(timelineLayer)
    .append("g")
    .attr("class", "timeline-range-brush")
    .call(brush);
  brushLayer.select(".overlay")
    .attr("fill", "transparent")
    .attr("cursor", "crosshair");
  brushLayer.select(".selection")
    .attr("fill", "transparent")
    .attr("stroke", "none")
    .attr("cursor", "grab");
  brushLayer.selectAll(".handle")
    .attr("fill", "transparent")
    .attr("stroke", "none")
    .attr("cursor", "ew-resize");

  const rangeLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
  rangeLine.classList.add("timeline-selected-range");
  rangeLine.setAttribute("y1", "1024");
  rangeLine.setAttribute("y2", "1024");
  rangeLine.setAttribute("stroke", "#563905");
  rangeLine.setAttribute("stroke-width", "3");
  rangeLine.setAttribute("pointer-events", "none");
  timelineLayer.appendChild(rangeLine);

  const handleGroups = [0, 1].map((index) => {
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.classList.add("timeline-range-handle");
    group.setAttribute("pointer-events", "none");

    const guide = document.createElementNS("http://www.w3.org/2000/svg", "line");
    guide.setAttribute("y1", "909.73");
    guide.setAttribute("y2", "1024");
    guide.setAttribute("stroke", "#351704");
    guide.setAttribute("stroke-width", "0.81");
    guide.setAttribute("stroke-dasharray", "2.1 2.1");
    guide.setAttribute("pointer-events", "none");

    const triangle = originalTriangle.cloneNode(true);
    triangle.style.removeProperty("display");
    triangle.setAttribute("pointer-events", "none");

    const label = originalYear.cloneNode(true);
    label.style.removeProperty("display");
    label.setAttribute("pointer-events", "none");

    const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
    title.textContent = index === 0 ? "所选时段起始年份" : "所选时段结束年份";

    group.append(guide, triangle, label, title);
    timelineLayer.appendChild(group);
    return { group, guide, triangle, label, index };
  });

  const cancelControl = document.createElementNS("http://www.w3.org/2000/svg", "g");
  cancelControl.classList.add("timeline-cancel-selection");
  cancelControl.style.cursor = "pointer";
  cancelControl.setAttribute("role", "button");
  cancelControl.setAttribute("aria-label", "取消当前时间选择，恢复显示全宋");
  cancelControl.setAttribute("tabindex", "0");
  const cancelHitArea = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  cancelHitArea.setAttribute("x", "94");
  cancelHitArea.setAttribute("y", "1027");
  cancelHitArea.setAttribute("width", "82");
  cancelHitArea.setAttribute("height", "23");
  cancelHitArea.setAttribute("fill", "none");
  cancelHitArea.setAttribute("pointer-events", "all");
  cancelHitArea.setAttribute("stroke", "#563905");
  cancelHitArea.setAttribute("stroke-width", "0.8");
  cancelHitArea.setAttribute("stroke-opacity", "0.72");
  const cancelLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
  cancelLabel.setAttribute("class", "cls-39");
  cancelLabel.setAttribute("x", "135");
  cancelLabel.setAttribute("y", "1039");
  cancelLabel.setAttribute("text-anchor", "middle");
  cancelLabel.setAttribute("dominant-baseline", "central");
  cancelLabel.textContent = "× 取消选择";
  const cancelTitle = document.createElementNS("http://www.w3.org/2000/svg", "title");
  cancelTitle.textContent = "取消当前时间选择，恢复显示全宋";
  cancelControl.append(cancelHitArea, cancelLabel, cancelTitle);
  timelineLayer.appendChild(cancelControl);

  const renderRange = (range) => {
    const selectionVisible = timelineSelectionActive.value;
    cancelControl.style.display = selectionVisible ? "" : "none";
    rangeLine.style.display = selectionVisible ? "" : "none";
    handleGroups.forEach((handle) => {
      handle.group.style.display = selectionVisible ? "" : "none";
    });
    if (!selectionVisible) return;
    const [start, end] = range;
    const years = [start, end];
    rangeLine.setAttribute("x1", String(yearScale(start)));
    rangeLine.setAttribute("x2", String(yearScale(end)));
    rangeLine.style.display = start === end ? "none" : "";
    for (const handle of handleGroups) {
      const year = years[handle.index];
      const x = yearScale(year);
      const isDuplicate = handle.index === 1 && start === end;
      handle.group.style.display = isDuplicate ? "none" : "";
      handle.guide.setAttribute("x1", String(x));
      handle.guide.setAttribute("x2", String(x));
      handle.triangle.setAttribute("transform", `translate(${x - 837.69} 0)`);
      handle.label.setAttribute("transform", `translate(${x + 7} 1035.22)`);
      handle.label.replaceChildren(document.createTextNode(`${year}年`));
    }
  };

  const rangeFromPointer = (event) => {
    const x = d3.pointer(event.sourceEvent, timelineLayer)[0];
    const year = Math.max(YEAR_MIN, Math.min(YEAR_MAX, Math.round(yearScale.invert(x))));
    return [year, year];
  };

  const moveBrush = (range) => {
    if (range[0] === range[1]) {
      const center = yearScale(range[0]);
      brushLayer.call(brush.move, [
        Math.max(TIMELINE_X_MIN, center - TIMELINE_YEAR_WIDTH / 2),
        Math.min(TIMELINE_X_MAX, center + TIMELINE_YEAR_WIDTH / 2),
      ]);
      return;
    }
    brushLayer.call(brush.move, [yearScale(range[0]), yearScale(range[1])]);
  };

  brush.on("brush", (event) => {
    if (!event.sourceEvent || !event.selection) return;
    const nextRange = rangeFromPointer(event);
    timelineSelectionActive.value = true;
    renderRange(nextRange);
    if (
      selectedRange.value[0] !== nextRange[0]
      || selectedRange.value[1] !== nextRange[1]
    ) {
      selectedRange.value = nextRange;
      scheduleTimelineRefresh();
    }
  });
  brush.on("end", (event) => {
    if (!event.sourceEvent) return;
    const nextRange = rangeFromPointer(event);
    timelineSelectionActive.value = true;
    selectedRange.value = nextRange;
    moveBrush(nextRange);
    flushTimelineRefresh();
  });

  const cancelSelection = (event) => {
    event.preventDefault();
    event.stopPropagation();
    timelineSelectionActive.value = false;
    selectedRange.value = [YEAR_MIN, YEAR_MAX];
    brushLayer.call(brush.move, null);
    renderRange(selectedRange.value);
    flushTimelineRefresh();
  };
  d3.select(cancelControl)
    .on("click.cancel-selection", cancelSelection)
    .on("keydown.cancel-selection", (event) => {
      if (event.key === "Enter" || event.key === " ") cancelSelection(event);
    });

  svg.__syncTimelineSelectionStyle = () => renderRange(selectedRange.value);
  renderRange(selectedRange.value);
  if (timelineSelectionActive.value) moveBrush(selectedRange.value);
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
  const requestedMode = viewMode.value;
  const revision = ++renderRevision;
  const url = `/api/design/${requestedMode}.svg`;
  const needsLoad = !svgCache.has(url);
  if (needsLoad) loading.value = true;
  error.value = "";
  try {
    if (needsLoad) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();
      const parsed = new DOMParser().parseFromString(source, "image/svg+xml");
      const parsedSvg = parsed.documentElement;
      if (parsedSvg.localName !== "svg" || parsed.querySelector("parsererror")) {
        throw new Error("原 SVG 无法解析");
      }
      svgCache.set(url, document.importNode(parsedSvg, true));
    }
    if (revision !== renderRevision || requestedMode !== viewMode.value) return;
    const svg = svgCache.get(url).cloneNode(true);
    svgMountRef.value.replaceChildren(svg);
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.classList.add("live-design-svg");
    selectedEntity();
    populateCenter(svg);
    bindEntityTexts(svg);
    replaceCompositionDescriptions(svg);
    bindTemplateControls(svg);
    bindTimelineRange(svg);
    setupDetailPanel(svg);
    updateDetails(svg);
  } catch (reason) {
    if (revision !== renderRevision) return;
    error.value = `SVG 设计稿加载失败：${reason.message}`;
  } finally {
    if (revision === renderRevision) loading.value = false;
  }
}

function refreshTemplate({ rebindStatic = false, rebindControls = false } = {}) {
  const svg = svgMountRef.value?.querySelector("svg.live-design-svg");
  if (!svg) {
    renderTemplate();
    return;
  }

  if (viewMode.value === "hierarchy") {
    svg.querySelector(".dynamic-tree-viewport")?.remove();
    svg.querySelectorAll(
      "clipPath[id^='dynamic-tree-'], clipPath[id^='inline-composition-']"
    ).forEach((clipPath) => clipPath.remove());
  }

  selectedEntity();
  populateCenter(svg);
  // 编制画板会复用并改写原 SVG 槽位，槽位对应实体变化后必须同步重绑；
  // 层级画板的动态节点则在 populateCenter 内自行绑定，可跳过整图扫描。
  if (rebindStatic || viewMode.value === "composition") {
    bindEntityTexts(svg);
    replaceCompositionDescriptions(svg);
  }
  if (rebindControls) bindTemplateControls(svg);
  updateDetails(svg);
  svg.__syncTimelineSelectionStyle?.();
  svg.__syncSpaceAwareExpansionControl?.();
}

function scheduleTimelineRefresh({ rebindStatic = false } = {}) {
  timelineRefreshNeedsStatic ||= rebindStatic;
  if (timelineRefreshFrame != null) return;
  timelineRefreshFrame = window.requestAnimationFrame(() => {
    const needsStatic = timelineRefreshNeedsStatic;
    timelineRefreshFrame = null;
    timelineRefreshNeedsStatic = false;
    refreshTemplate({ rebindStatic: needsStatic });
  });
}

function flushTimelineRefresh(rebindStatic = false) {
  if (timelineRefreshFrame != null) {
    window.cancelAnimationFrame(timelineRefreshFrame);
    timelineRefreshFrame = null;
  }
  timelineRefreshNeedsStatic = false;
  refreshTemplate({ rebindStatic });
}

watch(viewMode, renderTemplate);
onMounted(async () => {
  installDesignFonts();
  try {
    await document.fonts?.load('17.14px "FZQINGKBYSS-M--GB1-0"');
  } catch {
    // 字体加载失败时仍保留 SVG 自带的回退字体。
  }
  renderTemplate();
});
onUnmounted(() => {
  if (timelineRefreshFrame != null) window.cancelAnimationFrame(timelineRefreshFrame);
});
</script>

<style scoped>
.design-template { width: 100%; height: 100%; position: relative; overflow: hidden; background: #f5f3ec; }
.svg-mount { width: 100%; height: 100%; }
.svg-mount :deep(.live-design-svg) { display: block; width: 100%; height: 100%; }
.svg-mount :deep(.dynamic-tree-node:focus) { outline: none; }
.svg-mount :deep(.dynamic-tree-node:focus-visible .dynamic-tree-node-hit-area) { stroke: #563905; stroke-width: 1.2; stroke-dasharray: 3 2; }
.svg-mount :deep(.space-aware-expansion-control:focus) { outline: none; }
.svg-mount :deep(.space-aware-expansion-control:focus-visible [data-control-part="outline"]) { stroke-width: 1.35; stroke-dasharray: 3 2; }
.svg-mount :deep(.svg-entity-hover) { filter: drop-shadow(0 0 2px rgba(53, 23, 4, 0.75)); text-decoration: underline; }
.template-message { position: absolute; inset: 0; display: grid; place-items: center; z-index: 5; color: #563905; background: #f5f3ec; letter-spacing: 3px; }
</style>
