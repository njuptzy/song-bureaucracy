<template>
  <div
    ref="hostRef"
    class="design-template"
    :class="{ loading: loading, 'revision-panel-active': revisionPanelActive }"
  >
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
  buildSubordinateGroupNodes,
  subordinateGroupFor,
  subordinateGroupId,
} from "../utils/subordinate_groups";
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
  compositionDetailButtonVisible,
  compositionViewButtonVisible,
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
import { buildCompositionModel } from "../utils/composition_model";
import {
  fitCompositionBlock,
  layoutComposition,
  COMPOSITION_GEOMETRY,
} from "../utils/composition_layout";
import { buildEvolutionLanes, buildEvolutionModel } from "../utils/evolution_model";
import { layoutEvolutionModel } from "../utils/evolution_layout";
import { windowEvolutionModel } from "../utils/evolution_window";
import { timelineSelectionForEvolutionItem } from "../utils/evolution_selection";
import { dictionaryEntryText } from "../utils/dictionary_entry";
import { renderEvolutionOverlay } from "../renderers/evolution_renderer";
import { renderTimetreeOverlay } from "../renderers/timetree_renderer";
import {
  buildTimetreeRows,
  defaultTimetreeExpandedKeys,
  timetreeEntityKey,
  timetreeLaneEntityIds,
  toggleTimetreeExpansion,
} from "../utils/timetree_model";
import {
  clampTimetreeScroll,
  layoutTimetreeEvents,
  layoutTimetreeRelations,
  layoutTimetreeSegments,
  TIMETREE_GEOMETRY,
  timetreeLayoutSpan,
  timetreeEventsForLane,
  timetreeRelationEndpointIds,
  timetreeRelationsForEntity,
  timetreeYearToX,
} from "../utils/timetree_layout";
import { formatStandardTime } from "../utils/time_format";

const props = defineProps({
  data: { type: Object, required: true },
  initialState: { type: Object, default: null },
  revisionPanelActive: { type: Boolean, default: false },
});
const emit = defineEmits(["state-change", "selection-change"]);
const initialState = props.initialState || {};

const hostRef = ref(null);
const svgMountRef = ref(null);
const loading = ref(true);
const error = ref("");
const viewMode = ref(["hierarchy", "composition", "evolution", "timetree"].includes(initialState.viewMode)
  ? initialState.viewMode
  : "hierarchy");
const evolutionMode = ref(initialState.evolutionMode === "compare" ? "compare" : "single");
const evolutionEntityIds = ref(Array.isArray(initialState.evolutionEntityIds)
  ? initialState.evolutionEntityIds.slice(0, 4)
  : []);
const selectedEvolutionItem = ref(initialState.selectedEvolutionItem
  ? { ...initialState.selectedEvolutionItem, item: null }
  : null);
const evolutionLanePage = ref(Number.isFinite(initialState.evolutionLanePage)
  ? Math.max(1, Math.floor(initialState.evolutionLanePage))
  : 1);
const evolutionSearchOpen = ref(false);
// 时间线树视图状态：展开键 null = 用默认（制度组全展开）；滚动与选中独立于其他视图。
const timetreeExpandedKeys = ref(null);
const timetreeScroll = ref(0);
const timetreeSelectedEventId = ref(null);
const timetreeSelectedRelationId = ref(null);
const selectedRange = ref(Array.isArray(initialState.selectedRange)
  ? initialState.selectedRange.slice(0, 2)
  : [1080, 1080]);
const timelineSelectionActive = ref(initialState.timelineSelectionActive ?? true);
const selectedId = ref(initialState.selectedId ?? null);
const compositionFocusId = ref(initialState.compositionFocusId ?? null);
const selectedCategory = ref(initialState.selectedCategory || "中央机构");
const expandedDetailId = ref(null);
const inlineDetailField = ref("duty");
const inlineDetailOfficialId = ref(null);
const spaceAwareExpansion = ref(initialState.spaceAwareExpansion ?? false);
const svgCache = new Map();
const hierarchyTemplateCache = new WeakMap();
const yearSnapshotCache = new Map();
let detailPanelScrollOffset = 0;
let pendingDetailSectionKey = null;
const collapsedHierarchyIds = new Set();
let expandedHierarchyPath = [];
let hierarchyPanX = 0;
let hierarchyPanY = 0;
let expandedInstitutionGroupIds = [];
let lastExpandedInstitutionGroupId = null;
let expandedSubordinateGroupIds = [];
let lastExpandedSubordinateGroupId = null;
let inlineCompositionScrollOffset = 0;
let renderRevision = 0;
let lastExpandedHierarchyId = null;
let timelineRefreshFrame = null;
let timelineRefreshNeedsStatic = false;
let evolutionModelCacheKey = "";
let evolutionModelCache = null;
let evolutionLayoutCacheKey = "";
let evolutionLayoutCache = null;

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

// 原画板4-02右侧完整制度构成区域。进入具体机构后，该机构按原稿“省级总框”
// 语法使用整块空间，不再把中书/门下示例区当成独立静态内容保留。
const COMPOSITION_CONTENT_BOUNDS = {
  x: 503.48,
  y: 147.58,
  width: 1309.84,
  height: 717.85,
};

let entityMap = new Map();
let collectiveEntityIds = new Set();
let titleMap = new Map();
let timepointRowById = new Map();
let institutionGroupNames = { 中央机构: CENTRAL_GROUP_NAMES };

function rebuildDataIndexes(data) {
  entityMap = new Map((data?.entities || []).map((entity) => [entity.id, entity]));
  collectiveEntityIds = new Set(data?.collectiveEntityIds || []);
  titleMap = new Map();
  for (const entity of data?.entities || []) {
    if (!titleMap.has(entity.title)) titleMap.set(entity.title, entity);
  }
  timepointRowById = new Map();
  for (const rows of Object.values(data?.timepoints || {})) {
    for (const row of rows || []) {
      if (row?.id != null) timepointRowById.set(row.id, row);
    }
  }
  institutionGroupNames = data?.meta?.institutionGroupNames || {
    中央机构: CENTRAL_GROUP_NAMES,
  };
}

rebuildDataIndexes(props.data);
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
const persistedCanvasState = computed(() => ({
  viewMode: viewMode.value,
  evolutionMode: evolutionMode.value,
  evolutionEntityIds: [...evolutionEntityIds.value],
  selectedEvolutionItem: selectedEvolutionItem.value
    ? { kind: selectedEvolutionItem.value.kind, id: selectedEvolutionItem.value.id }
    : null,
  evolutionLanePage: evolutionLanePage.value,
  selectedRange: [...selectedRange.value],
  timelineSelectionActive: timelineSelectionActive.value,
  selectedId: selectedId.value,
  compositionFocusId: compositionFocusId.value,
  selectedCategory: selectedCategory.value,
  spaceAwareExpansion: spaceAwareExpansion.value,
}));

watch(persistedCanvasState, (state) => emit("state-change", state), {
  immediate: true,
  deep: true,
});

watch(() => props.data, (data) => {
  rebuildDataIndexes(data);
  const affectedEntityIds = new Set(data?.revisionPreview?.affectedEntityIds || []);
  const affectedYears = data?.revisionPreview?.affectedYears || [];
  if (!data?.revisionPreview) {
    yearSnapshotCache.clear();
  } else if (affectedYears.length) {
    const earliest = Math.min(...affectedYears);
    for (const year of yearSnapshotCache.keys()) {
      if (year >= earliest) yearSnapshotCache.delete(year);
    }
  }
  const currentEvolutionIds = new Set([
    ...(evolutionModelCache?.visibleEntityIds || []),
    ...evolutionEntityIds.value,
  ]);
  const evolutionAffected = !data?.revisionPreview
    || [...affectedEntityIds].some((id) => currentEvolutionIds.has(id));
  if (evolutionAffected) {
    evolutionModelCacheKey = "";
    evolutionModelCache = null;
    evolutionLayoutCacheKey = "";
    evolutionLayoutCache = null;
  }
  if (svgMountRef.value) refreshTemplate({ rebindStatic: true, rebindControls: true });
}, { flush: "post" });

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
  detailPanelScrollOffset = 0;
  inlineCompositionScrollOffset = 0;
  expandedDetailId.value = null;
  inlineDetailOfficialId.value = null;
  selectedId.value = target.id;
  if (viewMode.value === "evolution") {
    selectedEvolutionItem.value = null;
    evolutionEntityIds.value = evolutionMode.value === "single"
      ? [target.id]
      : [...new Set([...evolutionEntityIds.value, target.id])].slice(0, 4);
    evolutionLanePage.value = 1;
    refreshTemplate();
    return;
  }
  if (viewMode.value !== "composition") {
    if (target.type === "机构") {
      focusHierarchyContext(target, true);
    } else {
      const affiliation = staffEdgesForView().find((edge) => edge.official === target.id);
      const org = affiliation ? entityMap.get(affiliation.org) : null;
      if (org) focusHierarchyContext(org, true);
    }
  }
  refreshTemplate({ rebindControls: viewMode.value !== "composition" });
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
const HIERARCHY_DESIGN_URL = "/api/design/hierarchy.svg";
const DESIGN_URL_BY_MODE = {
  hierarchy: HIERARCHY_DESIGN_URL,
  composition: "/api/design/composition.svg",
  evolution: HIERARCHY_DESIGN_URL,
  timetree: HIERARCHY_DESIGN_URL,
};

function templateCategoryItems(svg) {
  const sharedItems = [...svg.querySelectorAll(
    ".shared-category-navigation > .shared-category-item"
  )].map((group) => ({
    category: group.dataset.category || "",
    textElement: [...group.children].find(
      (child) => child.tagName.toLowerCase() === "text"
    ),
    group,
  })).filter(({ category, textElement }) => (
    CATEGORY_NAMES.includes(category) && textElement
  ));
  if (sharedItems.length) return sharedItems;

  return [...svg.children]
    .filter((group) => group.tagName.toLowerCase() === "g")
    .map((group) => {
      const textElement = [...group.children].find((child) => (
        child.tagName.toLowerCase() === "text"
          && CATEGORY_NAMES.includes(normalizeText(child))
      ));
      return textElement
        ? { category: normalizeText(textElement), textElement, group }
        : null;
    })
    .filter(Boolean);
}

function prepareSharedCategoryGroup(group, category) {
  [group, ...group.querySelectorAll("[class]")].forEach((element) => {
    element.removeAttribute("class");
  });
  group.classList.add("shared-category-item");
  group.dataset.category = category;

  const label = [...group.children].find(
    (child) => child.tagName.toLowerCase() === "text"
  );
  label?.classList.add("shared-category-label");

  const outline = [...group.children].find(
    (child) => child.tagName.toLowerCase() === "polygon"
  );
  outline?.classList.add("shared-category-outline");

  const selection = [...group.children].find((child) => (
    child.tagName.toLowerCase() === "g" && child.querySelector("polygon")
  ));
  if (selection) {
    selection.classList.add("shared-category-selection");
    selection.querySelector("polygon")?.classList.add("shared-category-selection-shape");
  }
  return group;
}

// 4-02 原稿把路级四司嵌进分类栏；完整编制画板只需沿用层级画板的
// 五大类导航。直接克隆 4-01 的五个原始 group，避免维护第二套坐标。
function alignCompositionCategoryNavigation(svg) {
  const hierarchyTemplate = svgCache.get(HIERARCHY_DESIGN_URL);
  if (!hierarchyTemplate) throw new Error("层级视图分类栏模板未加载");
  const sourceItems = templateCategoryItems(hierarchyTemplate);
  const targetItems = templateCategoryItems(svg);
  if (sourceItems.length !== CATEGORY_NAMES.length || targetItems.length !== CATEGORY_NAMES.length) {
    throw new Error("机构分类栏槽位不完整");
  }

  const sourceByCategory = new Map(sourceItems.map((item) => [item.category, item]));
  const targetGroups = [...new Set(targetItems.map((item) => item.group))];
  const insertionPoint = targetGroups[0];
  const parent = insertionPoint?.parentNode;
  if (!parent) throw new Error("机构分类栏挂载点缺失");

  const navigation = svgElement("g", { class: "shared-category-navigation" });
  for (const category of CATEGORY_NAMES) {
    const source = sourceByCategory.get(category);
    if (!source) throw new Error(`层级视图缺少${category}槽位`);
    navigation.appendChild(
      prepareSharedCategoryGroup(source.group.cloneNode(true), category)
    );
  }
  parent.insertBefore(navigation, insertionPoint);
  targetGroups.forEach((group) => group.remove());
}

function entityCategory(entity) {
  return entity.category || "中央机构";
}

function templateSelectionCategory() {
  if (viewMode.value !== "composition" || compositionFocusId.value == null) {
    return selectedCategory.value;
  }
  const focus = entityMap.get(compositionFocusId.value);
  if (!focus) return selectedCategory.value;
  const context = resolveHierarchyContext(focus.id, hierarchyEdgesForView(), entityMap);
  return entityCategory(context.root || focus);
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
    if (!spaceAwareExpansion.value) expandedSubordinateGroupIds = [];
    for (let index = 0; index < context.path.length - 1; index += 1) {
      const parent = entityMap.get(context.path[index]);
      const child = entityMap.get(context.path[index + 1]);
      const group = subordinateGroupFor(parent?.title, child?.title);
      if (!group) continue;
      const groupId = subordinateGroupId(parent.id, group);
      expandedSubordinateGroupIds = spaceAwareExpansion.value
        ? [...new Set([...expandedSubordinateGroupIds, groupId])]
        : [groupId];
      lastExpandedSubordinateGroupId = groupId;
    }
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
const DETAIL_PANEL_EXTRA_KEYS = ["extra-1", "extra-2"];
const DETAIL_PANEL_SECTION_KEYS = [
  ...INLINE_DETAIL_FIELDS.map((field) => field.key),
  ...DETAIL_PANEL_EXTRA_KEYS,
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
  if (viewMode.value === "evolution") {
    const evolutionSelection = entityMap.get(selectedId.value)
      || entityMap.get(evolutionEntityIds.value[0]);
    if (evolutionSelection?.id !== selectedId.value) {
      selectedId.value = evolutionSelection?.id ?? null;
    }
    return evolutionSelection || null;
  }
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
  if (viewMode.value === "composition" && compositionFocusId.value != null) {
    const compositionFocus = entityMap.get(compositionFocusId.value);
    if (compositionFocus?.type === "机构") return compositionFocus;
  }
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
  const groupedChildren = shouldExpand
    ? buildSubordinateGroupNodes({
        parent: entity,
        childIds: allChildren,
        entityMap,
        expandedGroupIds: expandedSubordinateGroupIds,
        treeForChild: (id) => hierarchyTreeData(id, depth + 2, nextVisiting),
      })
    : null;
  const shownChildren = shouldExpand ? allChildren : [];
  return {
    id: rootId,
    title: entity.title,
    childCount: allChildren.length,
    hiddenCount: allChildren.length - shownChildren.length,
    children: groupedChildren || shownChildren
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

function renderSubordinateGroupCandidate(clickedId) {
  const candidateIds = [...expandedSubordinateGroupIds];
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
  expandedSubordinateGroupIds = resolvedIds;
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

function appendCompositionNodeButton(nodeGroup, {
  className,
  x,
  y,
  ariaLabel,
  titleText,
  onActivate,
}) {
  const buttonSize = 11;
  const button = document.createElementNS(SVG_NS, "g");
  button.classList.add("composition-detail-button", className);
  button.setAttribute("transform", `translate(${x} ${y})`);
  button.setAttribute("role", "button");
  button.setAttribute("tabindex", "0");
  button.setAttribute("aria-label", ariaLabel);
  button.style.cursor = "pointer";

  const hitArea = document.createElementNS(SVG_NS, "rect");
  hitArea.setAttribute("x", "-4");
  hitArea.setAttribute("y", "-4");
  hitArea.setAttribute("width", "19");
  hitArea.setAttribute("height", "19");
  hitArea.setAttribute("fill", "transparent");
  hitArea.setAttribute("pointer-events", "all");

  const surface = document.createElementNS(SVG_NS, "rect");
  surface.classList.add("composition-detail-button-surface");
  surface.setAttribute("width", String(buttonSize));
  surface.setAttribute("height", String(buttonSize));
  surface.setAttribute("rx", "1.5");
  surface.setAttribute("fill", "#563905");
  surface.setAttribute("fill-opacity", "0");
  surface.setAttribute("stroke", "none");

  const bookIcon = document.createElementNS(SVG_NS, "path");
  bookIcon.setAttribute(
    "d",
    "M4 5.5c2.15-.7 4.02-.28 5.5 1.05v8.05C8 13.32 6.15 12.9 4 13.55V5.5Zm11 0c-2.15-.7-4.02-.28-5.5 1.05v8.05c1.5-1.28 3.35-1.7 5.5-1.05V5.5Z"
  );
  bookIcon.setAttribute("fill", "none");
  bookIcon.setAttribute("stroke", "#563905");
  bookIcon.setAttribute("stroke-width", "1.15");
  bookIcon.setAttribute("stroke-linecap", "round");
  bookIcon.setAttribute("stroke-linejoin", "round");
  bookIcon.setAttribute("transform", "scale(0.62)");
  bookIcon.setAttribute("opacity", "0.9");

  const title = document.createElementNS(SVG_NS, "title");
  title.textContent = titleText;
  button.append(hitArea, surface, bookIcon, title);
  d3.select(button)
    .on("pointerdown.composition-action", (event) => event.stopPropagation())
    .on("click.composition-action", onActivate)
    .on("keydown.composition-action", (event) => {
      if (event.key === "Enter" || event.key === " ") onActivate(event);
    })
    .on("mouseenter.composition-action", () => {
      surface.setAttribute("fill-opacity", "0.12");
    })
    .on("mouseleave.composition-action", () => {
      surface.setAttribute("fill-opacity", "0");
    });
  nodeGroup.appendChild(button);
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
  cardTitle.textContent = `${entity.title}：点击官职翻开详情书页，点击机构书脊收起`;
  card.appendChild(cardTitle);
  d3.select(card)
    .on("click.inline-detail", (event) => event.stopPropagation())
    .on("dblclick.inline-detail", (event) => event.stopPropagation());
  if (titleLabel?.parentElement) {
    titleLabel.parentElement.style.cursor = "zoom-out";
    d3.select(titleLabel.parentElement).on("click.inline-detail-close", (event) => {
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
      nodeGroup.dataset.virtualRole = node.data.isInstitutionGroup
        ? "institution-group"
        : node.data.isSubordinateGroup
          ? "subordinate-group"
          : "category-root";
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
      : node.data.isSubordinateGroup
        ? expandedSubordinateGroupIds.includes(node.data.id)
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
      const entryReserve = node.data.id === selectedId.value ? 14 : 0;
      const barCount = Math.min(5, Math.max(1, Math.ceil(Math.log2(hiddenCount + 1))));
      for (let index = 0; index < barCount; index += 1) {
        const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        bar.setAttribute("x", String(bounds.x + 1));
        bar.setAttribute("y", String(bounds.y + bounds.height - 4 - index * 3));
        bar.setAttribute("width", String(bounds.width - 2 - entryReserve));
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
    const detailHint = node.data.isVirtual
      ? ""
      : "；右上角开书按钮就地展开编制关系，选中后点击右下角按钮进入编制视图";
    title.textContent = hiddenCount
      ? `${node.data.title}；尚有 ${hiddenCount} 个下级机构未展开${interactionHint}${detailHint}`
      : `${node.data.title}${interactionHint}${detailHint}`;
    nodeGroup.appendChild(title);
    if (!node.data.isVirtual) nodeGroup.setAttribute("aria-label", title.textContent);

    nodeGroup.style.cursor = "pointer";
    if (!node.data.isVirtual && expandedDetailId.value === node.data.id) expandedDetailNode = node;

    if (compositionDetailButtonVisible({
      isVirtual: node.data.isVirtual,
      isExpanded,
      isSelected: node.data.id === selectedId.value,
      isDetailOpen: expandedDetailId.value === node.data.id,
    }) && polygonBounds) {
      const buttonSize = 11;
      const buttonX = polygonBounds.x + polygonBounds.width - buttonSize - 3;
      appendCompositionNodeButton(nodeGroup, {
        className: "inline-composition-button",
        x: buttonX,
        y: polygonBounds.y + 3,
        ariaLabel: `展开${node.data.title}的编制关系`,
        titleText: "就地展开编制关系",
        onActivate: (event) => {
          event.preventDefault();
          event.stopPropagation();
          detailPanelScrollOffset = 0;
          inlineDetailField.value = "duty";
          inlineCompositionScrollOffset = 0;
          expandedDetailId.value = node.data.id;
          inlineDetailOfficialId.value = null;
          refreshTemplate();
        },
      });
    }

    if (compositionViewButtonVisible({
      isVirtual: node.data.isVirtual,
      isSelected: node.data.id === selectedId.value,
    }) && polygonBounds) {
      const buttonSize = 11;
      appendCompositionNodeButton(nodeGroup, {
        className: "composition-view-button",
        x: polygonBounds.x + polygonBounds.width - buttonSize - 3,
        y: polygonBounds.y + polygonBounds.height - buttonSize - 3,
        ariaLabel: `进入${node.data.title}的编制视图`,
        titleText: "进入编制视图",
        onActivate: (event) => {
          event.preventDefault();
          event.stopPropagation();
          detailPanelScrollOffset = 0;
          inlineDetailField.value = "duty";
          inlineCompositionScrollOffset = 0;
          expandedDetailId.value = null;
          inlineDetailOfficialId.value = null;
          selectedId.value = node.data.id;
          compositionFocusId.value = node.data.id;
          viewMode.value = "composition";
        },
      });
    }

    const toggleVirtualNode = (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (node.data.isSubordinateGroup) {
        const wasExpanded = expandedSubordinateGroupIds.includes(node.data.id);
        expandedSubordinateGroupIds = toggleInstitutionGroupIds(
          expandedSubordinateGroupIds,
          node.data.id,
          spaceAwareExpansion.value
        );
        if (!wasExpanded) lastExpandedSubordinateGroupId = node.data.id;
        hierarchyPanX = 0;
        hierarchyPanY = 0;
        if (!wasExpanded) {
          renderSubordinateGroupCandidate(node.data.id);
          return;
        }
      } else if (node.data.isInstitutionGroup) {
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

// —— 编制视图（画板 4-02）：数据 join + 模板盖章 ——
// 设计稿中的示例机构列只作为样式来源（cls-17/18 边框、cls-28/38/50/31 文字类），
// 首次进入编制视图时整批隐藏；实际内容由 composition_model（数据 join）
// 和 composition_layout（坐标排版）两个纯函数生成，不再复用示例槽位。
const compositionExampleCache = new WeakMap();

function hideCompositionExamples(svg) {
  if (compositionExampleCache.has(svg)) return;
  [...svg.children].forEach((element) => {
    if (["defs", "style", "image"].includes(element.tagName.toLowerCase())) return;
    // getBBox 不含元素自身的 translate，文本类元素必须用 transform 里的参考点判断位置。
    const point = position(element);
    const rawX = element.getAttribute("x");
    const rawY = element.getAttribute("y");
    const attrX = rawX == null ? null : Number(rawX);
    const attrY = rawY == null ? null : Number(rawY);
    const bbox = elementBounds(element);
    const x = point?.x ?? attrX ?? bbox?.x;
    const y = point?.y ?? attrY ?? bbox?.y;
    if (x == null || y == null) return;
    if (x >= 480 && y >= 130 && x <= 1835 && y <= 885) {
      element.style.display = "none";
    }
  });
  compositionExampleCache.set(svg, true);
}

const SVG_NS = "http://www.w3.org/2000/svg";

function svgElement(tag, attrs = {}) {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attrs)) element.setAttribute(name, String(value));
  return element;
}

// 竖排文字：首列落在 (x, y)，后续列向右 +pitch（CSS writing-mode: tb 负责竖排）。
function stampVerticalText(parent, {
  x, y, text, cls, charsPerCol, pitch, maxCols = 4, entityId = null,
  fontSize = null,
}) {
  const element = svgElement("text", { class: cls, transform: `translate(${x} ${y})` });
  // 原 SVG 的 class 自带固定字号；动态嵌套标题必须用布局计算后的字号覆盖它，
  // 否则 14/13.5px 的几何仍会以 16px 绘制并发生列间碰撞。
  if (Number.isFinite(fontSize)) element.style.fontSize = `${fontSize}px`;
  const content = Array.from(String(text || ""));
  const cols = [];
  for (let offset = 0; offset < content.length && cols.length < maxCols; offset += charsPerCol) {
    let column = content.slice(offset, offset + charsPerCol);
    if (offset + charsPerCol < content.length && cols.length === maxCols - 1) {
      column = [...column.slice(0, -1), "…"];
    }
    cols.push(column.join(""));
  }
  cols.forEach((column, index) => {
    const tspan = svgElement("tspan", { x: String(index * pitch), y: "0" });
    tspan.textContent = column;
    element.appendChild(tspan);
  });
  if (entityId != null) element.dataset.entityId = String(entityId);
  parent.appendChild(element);
  return element;
}

function stampStaffTracks(group, item) {
  const tracks = item.staffTracks || [];
  const labelRect = item.labelRect || item.rect;
  tracks.forEach((track, index) => {
    // 原稿的编制始终接在机构名下方，多列以标题基线为中心向左展开。
    const x = labelRect.x
      + item.staffRightmostXOffset
      - index * item.staffTrackPitch;
    stampVerticalText(group, {
      x,
      y: labelRect.y + item.staffYOffset,
      text: track.text,
      cls: `${item.staffClass || "cls-31"} composition-staff-text`,
      charsPerCol: Math.max(1, Array.from(track.text).length),
      pitch: item.staffTrackPitch,
      maxCols: 1,
      fontSize: item.staffFontSize,
    });
  });
}

function stampCompositionItem(layer, item, geometry) {
  const { rect } = item;
  const labelRect = item.labelRect || rect;
  const group = svgElement("g", { class: `composition-item composition-${item.kind}` });
  group.style.cursor = "pointer";
  if (item.titlePlateRect) {
    group.appendChild(svgElement("rect", {
      class: "cls-8 composition-focus-title-plate",
      x: item.titlePlateRect.x,
      y: item.titlePlateRect.y,
      width: item.titlePlateRect.width,
      height: item.titlePlateRect.height,
    }));
  }
  if (item.kind === "column") {
    const level = Math.min(4, Math.max(3, Number(item.depth || 1) + 2));
    group.appendChild(svgElement("rect", {
      class: `cls-18 composition-institution-border composition-level-${level}`,
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height,
    }));
  } else {
    group.appendChild(svgElement("rect", {
      class: "composition-item-hit-area",
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height,
    }));
  }
  d3.select(group).on("click", (event) => {
    event.stopPropagation();
    selectLinkedEntity(item.id);
  });
  const titleClass = item.kind === "focus"
    ? "cls-28"
    : item.kind === "section"
      ? "cls-38"
      : "cls-50";
  const titleFontSize = item.fontSize || (item.kind === "focus"
    ? geometry.focusTitleFontSize
    : item.kind === "section"
      ? geometry.sectionTitleFontSize
      : geometry.columnTitleFontSize);
  stampVerticalText(group, {
    x: labelRect.x + item.titleXOffset,
    y: labelRect.y + item.titleYOffset,
    text: item.title,
    cls: titleClass,
    charsPerCol: item.titleCapacity,
    pitch: item.titlePitch || titleFontSize + geometry.titleColGap,
    maxCols: item.titleCols || 1,
    entityId: item.id,
    fontSize: titleFontSize,
  });
  stampStaffTracks(group, item);
  layer.appendChild(group);
  for (const child of item.children || []) stampCompositionItem(layer, child, geometry);
}

function renderDynamicComposition(svg) {
  svg.querySelector(".dynamic-composition-layer")?.remove();
  hideCompositionExamples(svg);
  const layer = svgElement("g", { class: "dynamic-composition-layer" });
  svg.appendChild(layer);
  const focus = graphFocusEntity();
  const model = focus && buildCompositionModel({
    focusId: focus.id,
    entityMap,
    childrenFor,
    staffFor,
    titleOf,
  });
  const layout = model && layoutComposition(model, {
    origin: {
      x: COMPOSITION_CONTENT_BOUNDS.x,
      y: COMPOSITION_CONTENT_BOUNDS.y,
    },
    maxWidth: COMPOSITION_CONTENT_BOUNDS.width,
    maxHeight: COMPOSITION_CONTENT_BOUNDS.height,
  });
  if (!layout) return;
  const { geometry } = layout;
  const fitted = fitCompositionBlock(layout.bounds, COMPOSITION_CONTENT_BOUNDS);
  if (!fitted) return;
  const content = svgElement("g", {
    class: "dynamic-composition-fitted-content",
    transform: `translate(${fitted.translateX} ${fitted.translateY}) scale(${fitted.scale})`,
  });
  layer.appendChild(content);

  content.appendChild(svgElement("rect", {
    class: "cls-3 composition-institution-border composition-level-1",
    x: layout.parentRect.x,
    y: layout.parentRect.y,
    width: layout.parentRect.width,
    height: layout.parentRect.height,
  }));
  stampCompositionItem(content, layout.focusLabel, geometry);
  for (const block of layout.blocks) {
    content.appendChild(svgElement("rect", {
      class: `cls-17 composition-institution-border composition-level-2${block.kind === "attachments" ? " composition-attachments-frame" : ""}`,
      x: block.rect.x,
      y: block.rect.y,
      width: block.rect.width,
      height: block.rect.height,
    }));
    if (block.label) stampCompositionItem(content, block.label, geometry);
    for (const item of block.items) stampCompositionItem(content, item, geometry);
  }
}

const evolutionTemplateCache = new WeakMap();

function hideEvolutionExamples(svg) {
  hierarchyTemplates(svg);
  if (evolutionTemplateCache.has(svg)) return;
  [...svg.children].forEach((element) => {
    if (["defs", "style", "image"].includes(element.tagName.toLowerCase())) return;
    if (normalizeText(element).startsWith("宋朝的职官体系是自秦朝以来")) {
      element.classList.add("evolution-intro-copy");
    }
    const point = position(element);
    const bounds = elementBounds(element);
    const x = point?.x ?? bounds?.x;
    const y = point?.y ?? bounds?.y;
    if (x == null || y == null) return;
    if (x >= 58 && x <= 480 && y >= 270 && y <= 478) {
      element.style.display = "none";
    }
  });
  evolutionTemplateCache.set(svg, true);
}

function evolutionFocusEntities() {
  return evolutionEntityIds.value
    .map((entityId) => entityMap.get(entityId))
    .filter(Boolean)
    .slice(0, 4);
}

function ensureEvolutionFocus() {
  let focusEntities = evolutionFocusEntities();
  if (!focusEntities.length) {
    const fallback = entityMap.get(selectedId.value) || categoryFocus(selectedCategory.value);
    if (fallback) {
      evolutionEntityIds.value = [fallback.id];
      selectedId.value = fallback.id;
      focusEntities = [fallback];
    }
  }
  if (evolutionMode.value === "single" && focusEntities.length > 1) {
    const activeId = focusEntities.some((entity) => entity.id === selectedId.value)
      ? selectedId.value
      : focusEntities[0].id;
    evolutionEntityIds.value = [activeId];
    focusEntities = [entityMap.get(activeId)].filter(Boolean);
  }
  return focusEntities;
}

function applyEvolutionTimelineSelection(kind, effectiveYear = null) {
  const next = timelineSelectionForEvolutionItem(
    kind,
    effectiveYear,
    [YEAR_MIN, YEAR_MAX],
  );
  timelineSelectionActive.value = next.active;
  selectedRange.value = next.range;
}

function renderDynamicEvolution(svg) {
  hideEvolutionExamples(svg);
  const focusEntities = ensureEvolutionFocus();
  const focusIds = focusEntities.map((entity) => entity.id);
  const modelKey = focusIds.join(":");
  if (!evolutionModelCache || evolutionModelCacheKey !== modelKey) {
    evolutionModelCache = buildEvolutionModel(
      props.data,
      focusIds,
      { yearMin: YEAR_MIN, yearMax: YEAR_MAX },
    );
    evolutionModelCacheKey = modelKey;
    evolutionLayoutCacheKey = "";
    evolutionLayoutCache = null;
  }
  const windowedModel = windowEvolutionModel(evolutionModelCache, evolutionLanePage.value, 8);
  if (windowedModel.laneWindow.page !== evolutionLanePage.value) {
    evolutionLanePage.value = windowedModel.laneWindow.page;
  }
  const layoutKey = `${modelKey}:${windowedModel.laneWindow.page}`;
  if (!evolutionLayoutCache || evolutionLayoutCacheKey !== layoutKey) {
    evolutionLayoutCache = layoutEvolutionModel(windowedModel, {
      x: 520,
      y: 258,
      width: 1278,
      height: 568,
    });
    evolutionLayoutCacheKey = layoutKey;
  }
  const model = windowedModel;
  const layout = evolutionLayoutCache;
  if (selectedEvolutionItem.value) {
    const { kind, id } = selectedEvolutionItem.value;
    const item = kind === "relation"
      ? layout.relations.find((relation) => relation.id === id)
      : layout.lanes
        .flatMap((lane) => [...(lane.events || []), ...(lane.offAxisEvents || [])])
        .find((event) => event.id === id);
    selectedEvolutionItem.value = item ? { kind, id, item } : null;
  }
  svg.__evolutionModel = model;
  svg.__evolutionLayout = layout;

  const handlers = {
    onSelectEntity(entityId) {
      selectedId.value = entityId;
      selectedEvolutionItem.value = null;
      emit("selection-change", null);
      detailPanelScrollOffset = 0;
      refreshTemplate();
    },
    onRemoveEntity(entityId) {
      const remaining = evolutionEntityIds.value.filter((id) => id !== entityId);
      if (!remaining.length) return;
      evolutionEntityIds.value = remaining;
      if (selectedId.value === entityId) selectedId.value = remaining[0];
      selectedEvolutionItem.value = null;
      evolutionLanePage.value = 1;
      detailPanelScrollOffset = 0;
      refreshTemplate();
    },
    onAddEntity(entityId) {
      evolutionEntityIds.value = evolutionMode.value === "single"
        ? [entityId]
        : [...new Set([...evolutionEntityIds.value, entityId])].slice(0, 4);
      selectedId.value = entityId;
      selectedEvolutionItem.value = null;
      evolutionLanePage.value = 1;
      evolutionSearchOpen.value = false;
      detailPanelScrollOffset = 0;
      refreshTemplate();
    },
    onModeChange(mode) {
      if (mode === evolutionMode.value) return;
      evolutionMode.value = mode;
      evolutionSearchOpen.value = false;
      selectedEvolutionItem.value = null;
      evolutionLanePage.value = 1;
      if (mode === "single") {
        const activeId = evolutionEntityIds.value.includes(selectedId.value)
          ? selectedId.value
          : evolutionEntityIds.value[0];
        evolutionEntityIds.value = activeId == null ? [] : [activeId];
      }
      refreshTemplate();
    },
    onSearchOpenChange(open) {
      evolutionSearchOpen.value = Boolean(open);
      refreshTemplate();
    },
    onLanePageChange(page) {
      const nextPage = Math.max(1, Math.min(model.laneWindow.pageCount, Math.floor(page)));
      if (nextPage === evolutionLanePage.value) return;
      evolutionLanePage.value = nextPage;
      selectedEvolutionItem.value = null;
      if (!focusIds.includes(selectedId.value)) selectedId.value = focusIds[0] ?? null;
      detailPanelScrollOffset = 0;
      refreshTemplate();
    },
    onSelectEvent(event) {
      const current = selectedEvolutionItem.value;
      if (current?.kind === "timepoint" && current.id === event.id) {
        // 再次点击已选中的事件 = 取消选择，并复位联动的时间线框选。
        selectedEvolutionItem.value = null;
        emit("selection-change", null);
        applyEvolutionTimelineSelection(null);
        svg.__moveTimelineSelection?.();
        svg.__syncTimelineSelectionStyle?.();
        refreshTemplate();
        return;
      }
      selectedId.value = event.entityId;
      selectedEvolutionItem.value = { kind: "timepoint", id: event.id, item: event };
      emit("selection-change", {
        kind: "timepoint",
        id: event.id,
        entityId: event.entityId,
        item: { ...event },
      });
      detailPanelScrollOffset = 0;
      applyEvolutionTimelineSelection("timepoint", event.effectiveYear);
      refreshTemplate();
    },
    onSelectRelation(relation) {
      const current = selectedEvolutionItem.value;
      if (current?.kind === "relation" && current.id === relation.id) {
        // 再次点击已选中的关系 = 取消选择，并复位联动的时间线框选。
        selectedEvolutionItem.value = null;
        emit("selection-change", null);
        applyEvolutionTimelineSelection(null);
        svg.__moveTimelineSelection?.();
        svg.__syncTimelineSelectionStyle?.();
        refreshTemplate();
        return;
      }
      selectedEvolutionItem.value = { kind: "relation", id: relation.id, item: relation };
      emit("selection-change", {
        kind: "relation",
        id: relation.id,
        item: { ...relation },
      });
      detailPanelScrollOffset = 0;
      applyEvolutionTimelineSelection("relation");
      refreshTemplate();
    },
  };

  renderEvolutionOverlay(svg, {
    layout,
    entities: props.data.entities,
    focusEntities,
    activeEntityId: selectedId.value,
    selectedItem: selectedEvolutionItem.value,
    selectedRange: selectedRange.value,
    selectionActive: timelineSelectionActive.value,
    mode: evolutionMode.value,
    searchOpen: evolutionSearchOpen.value,
    handlers,
  });
}

// —— 时间线树视图：左侧层级树（原层级逆时针旋转 90°）+ 右侧逐行对齐的时间线 ——

function timetreeActiveExpandedKeys(category) {
  if (timetreeExpandedKeys.value !== null) return timetreeExpandedKeys.value;
  const inherited = [
    ...expandedInstitutionGroupIds,
    ...expandedHierarchyPath.map((entityId) => timetreeEntityKey(entityId)),
  ];
  if (inherited.length) return inherited;
  return defaultTimetreeExpandedKeys({
    entities: props.data.entities,
    category,
    groupNames: institutionGroupNames[category] || [],
  });
}

function renderDynamicTimetree(svg) {
  hideEvolutionExamples(svg);
  // hideEvolutionExamples 的隐藏区（x58–480/y270–478）覆盖了左侧分类导航，
  // 时间线树视图仍需要它切换分类，恢复显示。
  for (const element of svg.children) {
    if (element.style?.display !== "none") continue;
    const text = normalizeText(element);
    if (CATEGORY_NAMES.some((name) => text.includes(name))) {
      element.style.removeProperty("display");
    }
  }
  const treeTemplates = hierarchyTemplates(svg);
  const category = selectedCategory.value;
  const rows = buildTimetreeRows({
    entities: props.data.entities,
    hierarchyEdges: hierarchyEdgesWithoutCollectives(props.data.hierarchyEdges || []),
    category,
    collectiveIds: [...collectiveEntityIds],
    groupNames: institutionGroupNames[category] || [],
    expandedIds: new Set(timetreeActiveExpandedKeys(category)),
  });
  const laneModel = buildEvolutionLanes(
    props.data,
    timetreeLaneEntityIds(rows),
    { yearMin: YEAR_MIN, yearMax: YEAR_MAX },
  );

  const geometry = TIMETREE_GEOMETRY;
  const layoutSpan = timetreeLayoutSpan(rows);
  const scrollOffset = clampTimetreeScroll(timetreeScroll.value, layoutSpan, geometry);
  if (scrollOffset !== timetreeScroll.value) timetreeScroll.value = scrollOffset;
  const xOf = (year) => timetreeYearToX(year, YEAR_MIN, YEAR_MAX, geometry.plot);
  const yByEntityId = new Map(rows
    .filter((row) => row.entityId != null)
    .map((row) => [row.entityId, geometry.rowsTop
      + (row.layoutIndex ?? row.rowIndex) * geometry.rowPitch
      + geometry.rowPitch / 2 - scrollOffset]));

  const lanesByEntityId = new Map(laneModel.lanes.map((lane) => [lane.entityId, lane]));
  const visibleLaneIds = new Set(laneModel.lanes.map((lane) => lane.entityId));
  const activeLaneId = visibleLaneIds.has(selectedId.value) ? selectedId.value : null;
  const focusedLaneRelations = timetreeRelationsForEntity(laneModel.relations, activeLaneId);
  const linkedEndpointIds = activeLaneId == null
    ? null
    : timetreeRelationEndpointIds(focusedLaneRelations);
  const eventsByLane = new Map();
  const segmentsByLane = new Map();
  const eventPositionById = new Map();
  for (const lane of laneModel.lanes) {
    const y = yByEntityId.get(lane.entityId);
    const events = layoutTimetreeEvents(
      timetreeEventsForLane(lane.events, {
        active: lane.entityId === activeLaneId,
        linkedEndpointIds,
      }),
      xOf,
    );
    eventsByLane.set(lane.entityId, events);
    segmentsByLane.set(lane.entityId, layoutTimetreeSegments(lane.segments, xOf));
    for (const event of events) {
      eventPositionById.set(event.id, {
        x: event.baseX,
        y: y + (event.dy || 0),
        iconType: event.iconType,
        rawTime: event.rawTime,
        effectiveYear: event.effectiveYear,
      });
    }
  }
  const relations = layoutTimetreeRelations(focusedLaneRelations, eventPositionById)
    .filter((relation) => relation.drawable);

  const handlers = {
    onSelectEntity(entityId) {
      selectedId.value = entityId;
      timetreeSelectedEventId.value = null;
      timetreeSelectedRelationId.value = null;
      emit("selection-change", null);
      detailPanelScrollOffset = 0;
      refreshTemplate();
    },
    onToggleNode(key) {
      timetreeExpandedKeys.value = toggleTimetreeExpansion(
        rows,
        timetreeActiveExpandedKeys(category),
        key,
      );
      refreshTemplate();
    },
    onExpandAll() {
      const next = new Set(timetreeActiveExpandedKeys(category));
      for (const row of buildTimetreeRows({
        entities: props.data.entities,
        hierarchyEdges: hierarchyEdgesWithoutCollectives(props.data.hierarchyEdges || []),
        category,
        collectiveIds: [...collectiveEntityIds],
        groupNames: institutionGroupNames[category] || [],
        expandedIds: new Set(["__none__"]),
      })) {
        if (row.totalChildren > 0) next.add(row.key);
      }
      // 全部展开需要递归收集： collapsed 节点的下级键也要在集合里。
      let grew = true;
      while (grew) {
        grew = false;
        for (const row of buildTimetreeRows({
          entities: props.data.entities,
          hierarchyEdges: hierarchyEdgesWithoutCollectives(props.data.hierarchyEdges || []),
          category,
          collectiveIds: [...collectiveEntityIds],
          groupNames: institutionGroupNames[category] || [],
          expandedIds: next,
        })) {
          if (row.totalChildren > 0 && !next.has(row.key)) {
            next.add(row.key);
            grew = true;
          }
        }
      }
      timetreeExpandedKeys.value = [...next];
      refreshTemplate();
    },
    onCollapseAll() {
      timetreeExpandedKeys.value = [];
      refreshTemplate();
    },
    onSelectEvent(event) {
      if (timetreeSelectedEventId.value === event.id) {
        // 再次点击已选中的事件 = 取消选择（与演变视图一致）。
        timetreeSelectedEventId.value = null;
        refreshTemplate();
        return;
      }
      selectedId.value = event.entityId;
      timetreeSelectedEventId.value = event.id;
      timetreeSelectedRelationId.value = null;
      detailPanelScrollOffset = 0;
      refreshTemplate();
    },
    onSelectRelation(relation) {
      timetreeSelectedRelationId.value = timetreeSelectedRelationId.value === relation.id
        ? null
        : relation.id;
      refreshTemplate();
    },
    onScroll(deltaY) {
      const next = clampTimetreeScroll(
        timetreeScroll.value + deltaY * 0.6,
        layoutSpan,
        geometry,
      );
      if (next === timetreeScroll.value) return;
      timetreeScroll.value = next;
      scheduleTimelineRefresh();
    },
    onScrollToFraction(fraction) {
      const maxOffset = clampTimetreeScroll(Number.POSITIVE_INFINITY, layoutSpan, geometry);
      timetreeScroll.value = clampTimetreeScroll(maxOffset * fraction, layoutSpan, geometry);
      scheduleTimelineRefresh();
    },
    onOpenEvolution(entityId) {
      selectedId.value = entityId;
      evolutionEntityIds.value = [entityId];
      evolutionMode.value = "single";
      selectedEvolutionItem.value = null;
      evolutionLanePage.value = 1;
      viewMode.value = "evolution";
    },
  };

  renderTimetreeOverlay(svg, {
    rows,
    lanesByEntityId,
    eventsByLane,
    segmentsByLane,
    relations,
    yearMin: YEAR_MIN,
    yearMax: YEAR_MAX,
    scroll: {
      offset: scrollOffset,
      maxOffset: clampTimetreeScroll(Number.POSITIVE_INFINITY, layoutSpan, geometry),
      viewportHeight: geometry.rowsBottom - geometry.rowsTop,
      contentHeight: layoutSpan * geometry.rowPitch,
    },
    selectedEntityId: selectedId.value,
    selectedEventId: timetreeSelectedEventId.value,
    selectedRelationId: timetreeSelectedRelationId.value,
    treeTemplates,
    handlers,
  });
}

function populateCenter(svg) {
  if (viewMode.value === "hierarchy") renderDynamicHierarchy(svg);
  else if (viewMode.value === "composition") renderDynamicComposition(svg);
  else if (viewMode.value === "timetree") renderDynamicTimetree(svg);
  else renderDynamicEvolution(svg);
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
      if (this.closest(".dynamic-tree-layer, .dynamic-evolution-layer")) return;
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
    for (const key of DETAIL_PANEL_SECTION_KEYS) {
      const label = labelTemplate.cloneNode(false);
      label.dataset.detailSectionLabel = key;
      const content = contentTemplate.cloneNode(false);
      content.dataset.detailSectionContent = key;
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

}

const EVOLUTION_EFFECT_LABELS = {
  activate: "启用",
  preserve: "普通记载",
  deactivate: "罢废",
  ignore: "拟议未行",
};

const EVOLUTION_EVENT_TYPE_LABELS = {
  establish: "建置",
  restore: "复置",
  abolish: "罢废",
  rename: "改称",
  reorganize: "改置",
  merge: "合并",
  split: "分拆",
  incorporate: "并入",
  duty_transfer: "职掌移交",
  affiliation_change: "隶属变化",
  staffing_change: "编制变化",
  record: "一般记载",
};

const EVOLUTION_TIME_TYPE_LABELS = {
  exact: "明确时间点",
  range: "明确连续区间",
  bounded: "模糊时间边界",
  undated: "年代未明",
  unresolved: "时间待核查",
  pre_song: "宋前资料",
};

function evidenceLines(key, fallbackQuotation = "") {
  const citations = props.data.citations?.[key] || [];
  const quotation = fallbackQuotation
    || citations.map((item) => item.quotation).filter(Boolean).join("；");
  const source = citations.map((item) => item.citation).filter(Boolean).join("；");
  const note = citations.map((item) => item.note).filter(Boolean).join("；");
  return {
    quotation: quotation || "当前记录没有可展示的逐字引文。",
    source: source || "当前记录没有单列出处。",
    note: note || "无补充校勘说明。",
  };
}

function memberTimeLabel(member) {
  const row = timepointRowById.get(member?.timepointId) || {};
  return formatStandardTime({
    yearStart: member?.yearStart ?? row.year_start,
    yearEnd: member?.yearEnd ?? row.year_end,
    month: row.month,
    day: row.day,
    isLeapMonth: row.is_leap_month,
    rawTime: member?.rawTime || row.raw_time,
  });
}

function eventTimeLabel(event) {
  const row = timepointRowById.get(event?.id) || {};
  return formatStandardTime({
    yearStart: event?.yearStart ?? row.year_start,
    yearEnd: event?.yearEnd ?? row.year_end,
    month: row.month,
    day: row.day,
    isLeapMonth: row.is_leap_month,
    rawTime: event?.rawTime || row.raw_time,
  });
}

function relationEndpointLabel(member) {
  const entity = entityMap.get(member?.entityId);
  return `${entity?.title || `#${member?.entityId}`}（${memberTimeLabel(member)}）`;
}

function evolutionDetailPayload(svg) {
  const model = svg.__evolutionModel;
  const selected = selectedEvolutionItem.value;
  if (selected?.kind === "timepoint") {
    const event = selected.item;
    const entity = entityMap.get(event.entityId) || selectedEntity();
    const dictionaryOriginal = dictionaryEntryText(props.data.dictionary?.[entity?.title] || {});
    const evidence = evidenceLines(`T${event.id}`, event.quotation);
    const related = (model?.relations || []).filter((relation) => (
      relation.sourceTimepointId === event.id || relation.targetTimepointId === event.id
    ));
    return {
      title: entity?.title || "时间节点",
      year: eventTimeLabel(event),
      sections: [
        { label: "事件：", value: event.event || "原文未单列事件名。" },
        {
          label: "事件类型：",
          value: EVOLUTION_EVENT_TYPE_LABELS[event.eventType] || event.eventType || "一般记载",
        },
        {
          label: "词条原文：",
          value: dictionaryOriginal || "当前实体未匹配到辞典原文词条。",
        },
        {
          label: "存废判定：",
          value: `${EVOLUTION_EFFECT_LABELS[event.effect] || event.effect || "普通记载"}。关系箭头不参与这一判定。`,
        },
        {
          label: "时间精度：",
          value: `${EVOLUTION_TIME_TYPE_LABELS[event.timeType] || event.timeType || "未标注"}${event.parse_note ? `；${event.parse_note}` : ""}`,
        },
        {
          label: "相关关系：",
          value: related.length
            ? related.map((relation) => relation.label).join("；")
            : "当前时间点没有结构化演变关系。",
        },
        { label: "原文引文：", value: evidence.quotation },
        { label: "出处：", value: evidence.source },
        { label: "校勘说明：", value: evidence.note },
      ],
    };
  }

  if (selected?.kind === "relation") {
    const relation = selected.item;
    const evidence = evidenceLines(relation.evidenceKey || `R${relation.id}`, relation.quotation);
    const sources = (relation.sourceMembers || []).map(relationEndpointLabel).join("、");
    const targets = (relation.targetMembers || []).map(relationEndpointLabel).join("、");
    const endpointYears = [...new Set(
      [...(relation.sourceMembers || []), ...(relation.targetMembers || [])]
        .map((member) => memberTimeLabel(member)),
    )];
    return {
      title: relation.label,
      year: endpointYears.length ? endpointYears.join(" → ") : "年代未明",
      sections: [
        { label: "关系：", value: relation.label },
        { label: "来源：", value: sources || "来源端点未完整记录。" },
        { label: "目标：", value: targets || "目标端点未完整记录。" },
        {
          label: "编码状态：",
          value: relation.implementationStatus === "unclassified"
            ? "旧前后演变关系，尚未结构化细分；界面不依据自由文本猜测。"
            : `结构化关系${relation.groupId ? `；事件组 ${relation.groupId}` : "；未设置事件组"}。`,
        },
        { label: "原文引文：", value: evidence.quotation },
        { label: "出处：", value: evidence.source },
        { label: "校勘说明：", value: evidence.note },
      ],
    };
  }

  const entity = selectedEntity();
  if (!entity) return null;
  const lane = model?.lanes?.find((item) => item.entityId === entity.id);
  const relations = (model?.relations || []).filter((relation) => (
    relation.sourceEntityId === entity.id || relation.targetEntityId === entity.id
  ));
  const timepoints = props.data.timepoints[String(entity.id)] || [];
  const dictionary = props.data.dictionary?.[entity.title] || {};
  const dictionaryOriginal = dictionaryEntryText(dictionary);
  const segmentLabel = lane?.segments?.length
    ? lane.segments.map((segment) => `${segment.startYear}—${segment.endYear}`).join("；")
    : "当前算法未确认宋代存续段。";
  return {
    title: entity.title,
    year: `${timepoints.length} 个时间点`,
    sections: [
      { label: "实体类型：", value: entity.type },
      {
        label: "词条原文：",
        value: dictionaryOriginal || "当前实体未匹配到辞典原文词条。",
      },
      { label: "确认存续段：", value: segmentLabel },
      {
        label: "时间节点：",
        value: timepoints.length
          ? timepoints.map((item) => `${formatStandardTime(item)}：${item.event || item.quotation || "未载事件"}`).join("；")
          : "没有时间节点。",
      },
      {
        label: "结构化关系：",
        value: relations.length
          ? relations.map((relation) => relation.label).join("；")
          : "没有直接演变关系。",
      },
      {
        label: "数据异常：",
        value: lane?.anomalies?.length
          ? `${lane.anomalies.length} 项时间链异常；各链按断开的轨道展示，不自动补线。`
          : "未发现多链头、悬空链接或环。",
      },
      { label: "职源与沿革：", value: dictionary.origin || dictionary.text || "原文未单列职源与沿革。" },
      { label: "出处：", value: dictionary.source || dictionary.catalog || dictionary.page || "当前实体未匹配到独立出处。" },
    ],
  };
}

function updateEvolutionDetails(svg) {
  const payload = evolutionDetailPayload(svg);
  if (!payload) return;
  const title = findTextAt(svg, 99.85, 505.87);
  const year = findTextAt(svg, 189.74, 502.91);
  setText(title, payload.title);
  setText(year, payload.year);
  constrainTextWidth(title, 78);
  constrainTextWidth(year, 270);

  const panelGroup = svg.querySelector(".detail-panel-group");
  const topRightBorder = panelGroup?.__topRightBorder;
  if (topRightBorder && year) {
    const yearX = position(year)?.x ?? 189.74;
    const lineStart = Math.max(308.55, Math.min(468, yearX + year.getComputedTextLength() + 8));
    topRightBorder.setAttribute(
      "points",
      `229.27 877.67 475.49 877.67 475.49 497.57 ${lineStart} 497.57`,
    );
  }

  let cursorY = 536.92;
  DETAIL_PANEL_SECTION_KEYS.forEach((key, index) => {
    const label = svg.querySelector(`[data-detail-section-label='${key}']`);
    const content = svg.querySelector(`[data-detail-section-content='${key}']`);
    const section = payload.sections[index];
    if (!label || !content) return;
    if (!section) {
      label.style.display = "none";
      content.style.display = "none";
      return;
    }
    label.style.display = "";
    content.style.display = "";
    label.setAttribute("transform", `translate(100.33 ${cursorY})`);
    label.style.fill = "#351704";
    label.style.cursor = "default";
    d3.select(label).on("click.detail-field-link", null);
    setText(label, section.label);
    cursorY += 25;
    content.setAttribute("transform", `translate(101.29 ${cursorY})`);
    const lines = wrapText(content, section.value, 28, 18, Infinity);
    cursorY += Math.max(1, lines) * 18 + 13;
  });
  const scrollContent = svg.querySelector(".detail-panel-scroll-content");
  if (scrollContent) scrollContent.dataset.contentBottom = String(cursorY + 2);
  panelGroup?.__updateDetailScroll?.();
}

function updateDetails(svg) {
  if (viewMode.value === "evolution") {
    updateEvolutionDetails(svg);
    return;
  }
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
    DETAIL_PANEL_EXTRA_KEYS.forEach((key) => {
      const extraLabel = svg.querySelector(`[data-detail-section-label='${key}']`);
      const extraContent = svg.querySelector(`[data-detail-section-content='${key}']`);
      if (extraLabel) extraLabel.style.display = "none";
      if (extraContent) extraContent.style.display = "none";
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
  DETAIL_PANEL_EXTRA_KEYS.forEach((key) => {
    const extraLabel = svg.querySelector(`[data-detail-section-label='${key}']`);
    const extraContent = svg.querySelector(`[data-detail-section-content='${key}']`);
    if (extraLabel) extraLabel.style.display = "none";
    if (extraContent) extraContent.style.display = "none";
  });

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
    spaceAwareExpansion.value = !spaceAwareExpansion.value;
    if (!spaceAwareExpansion.value) {
      expandedInstitutionGroupIds = collapseInstitutionGroups(
        expandedInstitutionGroupIds,
        lastExpandedInstitutionGroupId
      );
      expandedSubordinateGroupIds = collapseInstitutionGroups(
        expandedSubordinateGroupIds,
        lastExpandedSubordinateGroupId
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

function enterEvolutionView() {
  const compositionFocus = entityMap.get(compositionFocusId.value);
  const focus = compositionFocus || entityMap.get(selectedId.value) || graphFocusEntity();
  if (focus) {
    selectedId.value = focus.id;
    evolutionEntityIds.value = [focus.id];
  }
  evolutionMode.value = "single";
  selectedEvolutionItem.value = null;
  evolutionLanePage.value = 1;
  evolutionSearchOpen.value = false;
  detailPanelScrollOffset = 0;
  viewMode.value = "evolution";
}

function restoreHierarchyFocus() {
  const selected = entityMap.get(selectedId.value) || entityMap.get(evolutionEntityIds.value[0]);
  if (!selected) return;
  selectedId.value = selected.id;
  if (selected.type === "机构") {
    focusHierarchyContext(selected, true);
    return;
  }
  const affiliation = props.data.staffEdges?.find((edge) => edge.official === selected.id);
  const institution = affiliation ? entityMap.get(affiliation.org) : null;
  if (institution) focusHierarchyContext(institution, true);
}

function ensureTimetreeViewControl(svg) {
  let control = svg.querySelector(".timetree-view-control");
  if (!control) {
    control = svgElement("g", { class: "timetree-view-control" });
    // 演变视图按钮在 1248.5，空间展开控件在 1392（层级视图内显示）；
    // 时间线树放在演变视图左侧，避开两者。
    const surface = svgElement("rect", {
      x: 1110.5,
      y: 80,
      width: 125.8,
      height: 26,
      rx: 2.7,
      fill: "#a5a68d",
      "fill-opacity": 0,
      stroke: "#563905",
      "stroke-width": 0.78,
      "stroke-opacity": 0.42,
    });
    const template = findTextAt(svg, 1570.42, 98.84, 2);
    const label = template?.cloneNode(true) || svgElement("text", { class: "cls-49" });
    label.setAttribute("transform", "translate(1173.4 98.84)");
    label.setAttribute("text-anchor", "middle");
    setText(label, "时间线树");
    control.append(surface, label);
    svg.appendChild(control);
  }
  const active = viewMode.value === "timetree";
  const surface = control.querySelector("rect");
  const label = control.querySelector("text");
  surface?.setAttribute("fill-opacity", active ? "0.55" : "0");
  surface?.setAttribute("stroke-opacity", active ? "0.8" : "0.42");
  if (label) label.style.fontWeight = active ? "700" : "400";
  const activate = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (active) return;
    selectedEvolutionItem.value = null;
    viewMode.value = "timetree";
  };
  control.setAttribute("role", "button");
  control.setAttribute("tabindex", active ? "-1" : "0");
  control.setAttribute("aria-label", active ? "当前为时间线树视图" : "打开时间线树视图");
  control.style.cursor = active ? "default" : "pointer";
  d3.select(control)
    .on("click.timetree-view", active ? null : activate)
    .on("keydown.timetree-view", active ? null : (event) => {
      if (event.key === "Enter" || event.key === " ") activate(event);
    });
}

function ensureEvolutionViewControl(svg) {
  let control = svg.querySelector(".evolution-view-control");
  if (!control) {
    control = svgElement("g", { class: "evolution-view-control" });
    const surface = svgElement("rect", {
      x: 1248.5,
      y: 80,
      width: 125.8,
      height: 26,
      rx: 2.7,
      fill: "#a5a68d",
      "fill-opacity": 0,
      stroke: "#563905",
      "stroke-width": 0.78,
      "stroke-opacity": 0.42,
    });
    const template = findTextAt(svg, 1570.42, 98.84, 2);
    const label = template?.cloneNode(true) || svgElement("text", { class: "cls-49" });
    label.setAttribute("transform", "translate(1311.4 98.84)");
    label.setAttribute("text-anchor", "middle");
    setText(label, "演变视图");
    control.append(surface, label);
    svg.appendChild(control);
  }
  const active = viewMode.value === "evolution";
  const surface = control.querySelector("rect");
  const label = control.querySelector("text");
  surface?.setAttribute("fill-opacity", active ? "0.55" : "0");
  surface?.setAttribute("stroke-opacity", active ? "0.8" : "0.42");
  if (label) label.style.fontWeight = active ? "700" : "400";
  makeEvolutionControlInteractive(control, active);
}

function makeEvolutionControlInteractive(control, active) {
  const activate = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (!active) enterEvolutionView();
  };
  control.setAttribute("role", "button");
  control.setAttribute("tabindex", active ? "-1" : "0");
  control.setAttribute("aria-label", active ? "当前为演变视图" : "打开演变视图");
  control.style.cursor = active ? "default" : "pointer";
  d3.select(control)
    .on("click.evolution-view", active ? null : activate)
    .on("keydown.evolution-view", active ? null : (event) => {
      if (event.key === "Enter" || event.key === " ") activate(event);
    });
}

function bindTemplateControls(svg) {
  svg.querySelectorAll(".view-mode-hit-area").forEach((element) => element.remove());
  ensureEvolutionViewControl(svg);
  ensureTimetreeViewControl(svg);
  const categoryItems = templateCategoryItems(svg);
  const selectionTemplate = categoryItems
    .map(({ group }) => [...group.children].find(
      (child) => child.tagName.toLowerCase() === "g"
        && (
          child.classList.contains("cls-81")
          || child.classList.contains("cls-59")
          || child.classList.contains("shared-category-selection")
        )
    ))
    .find(Boolean)?.cloneNode(true);

  for (const { group } of categoryItems) {
    [...group.children]
      .filter((child) => child.tagName.toLowerCase() === "g"
        && (
          child.classList.contains("cls-81")
          || child.classList.contains("cls-59")
          || child.classList.contains("shared-category-selection")
        ))
      .forEach((child) => child.remove());
  }

  const selectedItem = categoryItems.find(
    ({ category }) => category === templateSelectionCategory()
  );
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
      if (this.closest(".dynamic-tree-layer, .dynamic-evolution-layer, .evolution-view-control, .dynamic-timetree-layer, .timetree-view-control")) return;
      const text = normalizeText(this);
      if (text === "层级视图" || text === "编制视图") {
        const targetMode = text === "层级视图" ? "hierarchy" : "composition";
        // 编制视图只能从层级机构词条的右下角入口进入；顶栏只承担返回层级。
        const canActivate = targetMode === "hierarchy"
          && (viewMode.value === "composition"
            || viewMode.value === "evolution"
            || viewMode.value === "timetree");
        const activateView = (event) => {
          event.stopPropagation();
          if (!canActivate) return;
          if (compositionFocusId.value != null) {
            const focus = entityMap.get(compositionFocusId.value);
            if (focus) {
              selectedId.value = focus.id;
              focusHierarchyContext(focus, true);
            }
          }
          if (viewMode.value === "evolution" || viewMode.value === "timetree") {
            restoreHierarchyFocus();
          }
          viewMode.value = "hierarchy";
        };
        this.style.cursor = canActivate ? "pointer" : "default";
        this.style.fontWeight = targetMode === viewMode.value ? "700" : "400";
        d3.select(this).on("click.view-mode", canActivate ? activateView : null);
        const bounds = elementBounds(this);
        if (canActivate && bounds && this.parentNode) {
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
        const categoryInteractive = viewMode.value === "hierarchy" || viewMode.value === "timetree";
        if (!categoryInteractive) {
          this.style.cursor = "default";
          d3.select(this).on("click.category", null);
          if (group?.tagName.toLowerCase() === "g") {
            group.style.cursor = "default";
            group.style.pointerEvents = "none";
            d3.select(group).on("click.category", null);
          }
          return;
        }
        const activate = (event) => {
          event.stopPropagation();
          detailPanelScrollOffset = 0;
          collapsedHierarchyIds.clear();
          expandedHierarchyPath = [];
          lastExpandedHierarchyId = null;
          hierarchyPanX = 0;
          hierarchyPanY = 0;
          timetreeExpandedKeys.value = null;
          timetreeScroll.value = 0;
          timetreeSelectedEventId.value = null;
          timetreeSelectedRelationId.value = null;
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
    if (viewMode.value === "evolution") selectedEvolutionItem.value = null;
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
  svg.__moveTimelineSelection = () => {
    if (timelineSelectionActive.value) moveBrush(selectedRange.value);
    else brushLayer.call(brush.move, null);
  };
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

async function loadSvgTemplate(url) {
  if (svgCache.has(url)) return;
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

async function renderTemplate() {
  const requestedMode = viewMode.value;
  const revision = ++renderRevision;
  const url = DESIGN_URL_BY_MODE[requestedMode] || HIERARCHY_DESIGN_URL;
  const requiredUrls = requestedMode === "composition"
    ? [url, HIERARCHY_DESIGN_URL]
    : [url];
  const needsLoad = requiredUrls.some((requiredUrl) => !svgCache.has(requiredUrl));
  if (needsLoad) loading.value = true;
  error.value = "";
  try {
    await Promise.all(requiredUrls.map(loadSvgTemplate));
    if (revision !== renderRevision || requestedMode !== viewMode.value) return;
    const svg = svgCache.get(url).cloneNode(true);
    if (requestedMode === "composition") alignCompositionCategoryNavigation(svg);
    svgMountRef.value.replaceChildren(svg);
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.classList.add("live-design-svg");
    selectedEntity();
    populateCenter(svg);
    bindEntityTexts(svg);
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
  if (viewMode.value === "evolution") {
    svg.querySelector(".dynamic-evolution-layer")?.remove();
    svg.querySelectorAll("[data-evolution-def]").forEach((element) => element.remove());
  }
  if (viewMode.value === "timetree") {
    svg.querySelector(".dynamic-timetree-layer")?.remove();
    svg.querySelectorAll("[data-timetree-def]").forEach((element) => element.remove());
  }

  selectedEntity();
  populateCenter(svg);
  // 编制画板的动态机构列由 renderDynamicComposition 生成并自带 data-entity-id，
  // 需要整图扫描绑定悬停与点击；层级画板的动态节点在 populateCenter 内自行绑定。
  if (rebindStatic || viewMode.value === "composition") {
    bindEntityTexts(svg);
  }
  if (rebindControls) bindTemplateControls(svg);
  updateDetails(svg);
  svg.__syncTimelineSelectionStyle?.();
  svg.__moveTimelineSelection?.();
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
.design-template.revision-panel-active .svg-mount :deep(.evolution-selector-layer) {
  visibility: hidden;
  pointer-events: none;
}
.design-template.revision-panel-active .svg-mount :deep(.evolution-intro-copy) {
  display: none;
}
.svg-mount :deep(.shared-category-label) {
  fill: #351704;
  font-family: FZQINGKBYSS-M--GB1-0, FZQingKeBenYueSongS;
  font-size: 19.34px;
  glyph-orientation-vertical: 0deg;
  text-orientation: upright;
  writing-mode: tb;
}
.svg-mount :deep(.shared-category-outline) {
  fill: none;
  stroke: #563905;
  stroke-miterlimit: 10;
}
.svg-mount :deep(.shared-category-selection) { opacity: 0.4; }
.svg-mount :deep(.shared-category-selection-shape) {
  fill: #351704;
  stroke: #563905;
  stroke-miterlimit: 10;
  stroke-width: 0.75px;
}
.svg-mount :deep(.dynamic-tree-node:focus) { outline: none; }
.svg-mount :deep(.dynamic-tree-node:focus-visible .dynamic-tree-node-hit-area) { stroke: #563905; stroke-width: 1.2; stroke-dasharray: 3 2; }
.svg-mount :deep(.composition-detail-button:focus) { outline: none; }
.svg-mount :deep(.composition-detail-button:focus-visible .composition-detail-button-surface) { fill-opacity: 0.08; stroke: #563905; stroke-width: 0.8; stroke-dasharray: 1.5 1; }
.svg-mount :deep(.composition-item-hit-area) { fill: transparent; stroke: none; pointer-events: all; }
.svg-mount :deep(.composition-institution-border) { fill: none; stroke: #563905; }
.svg-mount :deep(.composition-level-1) { stroke-width: 3px; }
.svg-mount :deep(.composition-level-2) { stroke-width: 2px; }
.svg-mount :deep(.composition-level-3) { stroke-width: 1.15px; }
.svg-mount :deep(.composition-level-4) { stroke-width: 0.51px; }
.svg-mount :deep(.space-aware-expansion-control:focus) { outline: none; }
.svg-mount :deep(.space-aware-expansion-control:focus-visible [data-control-part="outline"]) { stroke-width: 1.35; stroke-dasharray: 3 2; }
.svg-mount :deep(.svg-entity-hover) { filter: drop-shadow(0 0 2px rgba(53, 23, 4, 0.75)); text-decoration: underline; }
/* —— 时间线树视图 —— */
.svg-mount :deep(.timetree-axis-label) { fill: #918069; font-size: 11px; letter-spacing: 1px; }
.svg-mount :deep(.timetree-header-control) { fill: #563905; font-size: 11px; letter-spacing: 1px; }
.svg-mount :deep(.timetree-header-control:hover) { text-decoration: underline; }
.svg-mount :deep(.timetree-row-band.is-odd) { fill-opacity: 0.05; }
.svg-mount :deep(.timetree-row-band:hover) { fill-opacity: 0.09; }
.svg-mount :deep(.timetree-row-band.is-selected) { fill-opacity: 0.12; }
.svg-mount :deep(.timetree-tree-node) { cursor: pointer; }
.svg-mount :deep(.timetree-tree-node:focus) { outline: none; }
.svg-mount :deep(.timetree-offaxis-badge) { fill: #918069; font-size: 9px; letter-spacing: 0.5px; }
.svg-mount :deep(.timetree-empty-hint) { fill: #918069; font-size: 14px; letter-spacing: 3px; }
.svg-mount :deep(.timetree-scrollbar-thumb:hover) { fill-opacity: 0.5; }
.template-message { position: absolute; inset: 0; display: grid; place-items: center; z-index: 5; color: #563905; background: #f5f3ec; letter-spacing: 3px; }
</style>
