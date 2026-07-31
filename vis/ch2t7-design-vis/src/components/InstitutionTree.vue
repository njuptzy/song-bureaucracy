<template>
  <svg ref="svgRef" class="tree-svg">
    <g :transform="transform.toString()">
      <!-- 皇帝装饰总根与各根的连线 -->
      <template v-if="emperor">
        <path
          v-for="l in emperorLinks"
          :key="'el' + l.target.data.id"
          class="link"
          :d="linkPath(l)"
        />
        <g :transform="`translate(${emperor.x}, ${emperor.y})`" class="emperor-node">
          <rect x="-30.5" y="-14" width="61" height="28" />
          <text y="5.5">皇帝</text>
        </g>
      </template>

      <!-- 机构之间的连接线（直角折线） -->
      <path v-for="l in links" :key="'l' + l.target.data.id" class="link" :d="linkPath(l)" />

      <!-- 机构节点：竖排书脊（白底细描边 + 顶部灰绿签 + 竖排题名） -->
      <g
        v-for="n in nodes"
        :key="n.data.id"
        :transform="`translate(${n.x}, ${n.y})`"
        class="spine"
        :class="{ selected: n.data.id === selectedId }"
        @click="onNodeClick(n)"
        @mouseenter="onNodeHover(n, $event)"
        @mousemove="onNodeHover(n, $event)"
        @mouseleave="emit('hover', null)"
      >
        <!-- 顶部签 -->
        <rect
          class="tab"
          :x="-TAB / 2"
          :y="-nodeH(n) / 2 - TAB + 1"
          :width="TAB"
          :height="TAB"
        />
        <!-- 书脊 -->
        <rect
          class="body"
          :x="-nodeW(n) / 2"
          :y="-nodeH(n) / 2"
          :width="nodeW(n)"
          :height="nodeH(n)"
        />
        <!-- 竖排题名 -->
        <text
          class="spine-title"
          :y="-nodeH(n) / 2 + TAB + 6 + titleFont(n)"
          :font-size="titleFont(n)"
        >
          {{ shortTitle(n.data.title) }}
        </text>
        <!-- 展开/收起控制 -->
        <g
          v-if="n.childCount > 0"
          class="toggle"
          :transform="`translate(0, ${nodeH(n) / 2 + 11})`"
          @click.stop="onToggleOnly(n)"
        >
          <circle r="4.5" />
          <text y="2.8">{{ isExpanded(n.data.id) ? "−" : "+" }}</text>
        </g>

        <!-- 官职（编制隶属）浮动面板：不影响树布局；全局开关或选中本节点时展出 -->
        <OfficialHats
          v-if="showOfficials || n.data.id === selectedId"
          :edges="staffByOrg.get(n.data.id) || []"
          :official-info="officialInfo"
          :node-w="nodeW(n)"
          :node-h="nodeH(n)"
          @select-official="(id) => emit('select', id)"
        />
      </g>
    </g>
  </svg>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import * as d3 from "d3";
import OfficialHats from "./OfficialHats.vue";

const props = defineProps({
  data: { type: Object, required: true },
  showOfficials: Boolean,
  expandCommand: Object,
  locateTarget: Object,
  selectedId: Number,
  staffByOrg: { type: Map, required: true },
});
const emit = defineEmits(["select", "hover"]);

const TAB = 7;
const DX = 72;
const DY = 240;

// 书脊宽度/字号按层级递减（设计稿图例：省 / 部 / 司 / 案及以下）
const LEVEL_W = [26, 21, 18, 16, 14];
const LEVEL_FONT = [16, 14, 13, 12, 11];

const svgRef = ref(null);
const transform = ref(d3.zoomIdentity);
const expanded = ref(new Set());
let zoomBehavior = null;

// ---- 图结构 ----
const childrenMap = computed(() => {
  const m = new Map();
  const claimed = new Set();
  for (const e of props.data.hierarchyEdges) {
    if (claimed.has(e.child)) continue; // 多个上级时取第一个，保证是树
    claimed.add(e.child);
    if (!m.has(e.parent)) m.set(e.parent, []);
    m.get(e.parent).push(e.child);
  }
  return m;
});

const parentMap = computed(() => {
  const m = new Map();
  for (const [p, kids] of childrenMap.value) for (const k of kids) m.set(k, p);
  return m;
});

const childSet = computed(() => new Set(parentMap.value.keys()));

const participants = computed(() => {
  const s = new Set(childrenMap.value.keys());
  for (const k of childSet.value) s.add(k);
  return s;
});

const subtreeSize = computed(() => {
  const cache = new Map();
  const walk = (id) => {
    if (cache.has(id)) return cache.get(id);
    cache.set(id, 0); // 防环
    let n = 0;
    for (const k of childrenMap.value.get(id) || []) n += 1 + walk(k);
    cache.set(id, n);
    return n;
  };
  for (const id of participants.value) walk(id);
  return cache;
});

const roots = computed(() =>
  [...participants.value]
    .filter((id) => !childSet.value.has(id))
    .sort((a, b) => (subtreeSize.value.get(b) || 0) - (subtreeSize.value.get(a) || 0))
);

const depthMap = computed(() => {
  const m = new Map();
  const queue = roots.value.map((id) => [id, 1]);
  while (queue.length) {
    const [id, d] = queue.shift();
    if (m.has(id)) continue;
    m.set(id, d);
    for (const k of childrenMap.value.get(id) || []) queue.push([k, d + 1]);
  }
  return m;
});

const entityTitles = computed(() => {
  const m = new Map();
  for (const e of props.data.entities) m.set(e.id, e.title);
  return m;
});

// 官职图标所需的信息：品阶档位 + 官职类分类（差遣官/职事官/阶官/吏，设计稿图例）
const officialInfo = computed(() => {
  const m = new Map();
  for (const e of props.data.entities) {
    if (e.type !== "官职") continue;
    const tps = props.data.timepoints[String(e.id)] || [];
    const grade = (tps.find((t) => t.attr_grade) || {}).attr_grade || "";
    const category = tps.map((t) => t.attr_category).join(" ");
    m.set(e.id, {
      title: e.title,
      tier: gradeTier(grade),
      kind: officialKind(category),
    });
  }
  return m;
});

const GRADE_NUM = { 一: 1, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9 };
function gradeTier(grade) {
  const mm = /[正从]?([一二三四五六七八九])品/.exec(grade || "");
  if (!mm) return 5;
  return Math.min(5, Math.ceil(GRADE_NUM[mm[1]] / 2));
}
function officialKind(category) {
  if (/吏|公人|杂役|乐工/.test(category)) return "吏";
  if (/差遣|差使|权摄|判.+事/.test(category)) return "差遣官";
  if (/阶官|寄禄|武阶/.test(category)) return "阶官";
  return "职事官";
}

// ---- 展开状态 ----
function isExpanded(id) {
  return expanded.value.has(id);
}

function applyCommand(cmd) {
  if (!cmd) return;
  if (cmd.type === "all") {
    expanded.value = new Set([...childrenMap.value.keys()]);
  } else if (cmd.type === "collapse") {
    expanded.value = new Set();
  } else if (cmd.type === "level") {
    const s = new Set();
    for (const [id, d] of depthMap.value) {
      if (d < cmd.level && childrenMap.value.has(id)) s.add(id);
    }
    expanded.value = s;
  }
}

watch(
  () => props.expandCommand,
  (cmd) => applyCommand(cmd),
  { immediate: true, deep: true }
);

// ---- 布局 ----
const layout = computed(() => {
  const build = (id, depth) => {
    const node = { id, depth, title: entityTitles.value.get(id) || `#${id}` };
    node.childCount = (childrenMap.value.get(id) || []).length;
    if (expanded.value.has(id)) {
      const kids = (childrenMap.value.get(id) || []).map((k) => build(k, depth + 1));
      if (kids.length) node.children = kids;
    }
    return node;
  };
  const rootData = { id: "__emperor__", children: roots.value.map((r) => build(r, 1)) };
  const hier = d3.hierarchy(rootData);
  d3.tree().nodeSize([DX, DY])(hier);
  return hier;
});

const emperor = computed(() => {
  const l = layout.value;
  return l.children && l.children.length ? { x: l.x, y: l.y } : null;
});

const emperorLinks = computed(() => layout.value.links().filter((l) => l.source.depth === 0));
const links = computed(() => layout.value.links().filter((l) => l.source.depth > 0));
const nodes = computed(() => layout.value.descendants().filter((n) => n.depth > 0));

// 直角折线：父节点底边 -> 竖直 -> 水平 -> 竖直 -> 子节点顶边
function linkPath(l) {
  const y1 = l.source.y + (l.source.depth === 0 ? 14 : nodeH(l.source) / 2);
  const y2 = l.target.y - nodeH(l.target) / 2 - (l.target.data.childCount ? 0 : 0);
  const ym = (y1 + y2) / 2;
  return `M ${l.source.x} ${y1} V ${ym} H ${l.target.x} V ${y2}`;
}

// ---- 节点几何 ----
function nodeW(n) {
  return LEVEL_W[Math.min(n.data.depth, 5) - 1];
}
function titleFont(n) {
  return LEVEL_FONT[Math.min(n.data.depth, 5) - 1];
}
function shortTitle(title) {
  return title.length > 11 ? title.slice(0, 11) : title;
}
function nodeH(n) {
  const len = Math.min(n.data.title.length, 11);
  return Math.min(190, Math.max(88, TAB + 14 + len * (titleFont(n) + 2.5) + 16));
}

// ---- 交互 ----
function onNodeClick(n) {
  const id = n.data.id;
  if (n.data.childCount > 0) toggleExpand(id);
  emit("select", id);
}
function onToggleOnly(n) {
  toggleExpand(n.data.id);
}
function toggleExpand(id) {
  const s = new Set(expanded.value);
  if (s.has(id)) s.delete(id);
  else s.add(id);
  expanded.value = s;
}

function onNodeHover(n, ev) {
  emit("hover", { id: n.data.id, x: ev.clientX, y: ev.clientY });
}

// ---- 缩放与定位 ----
onMounted(() => {
  const svg = d3.select(svgRef.value);
  zoomBehavior = d3
    .zoom()
    .scaleExtent([0.15, 3])
    .on("zoom", (e) => {
      transform.value = e.transform;
    });
  svg.call(zoomBehavior);
  svg.on("dblclick.zoom", null); // 禁用默认双击放大
  svg.on("dblclick", homeView);
  homeView();
});

// 初始视图：原大比例，对准最大的一级机构（树极宽，整体缩放会把书脊缩没）
function homeView() {
  const ns = nodes.value;
  if (!ns.length || !svgRef.value) return;
  const rect = svgRef.value.getBoundingClientRect();
  const firstRootId = roots.value[0];
  const anchor = ns.find((n) => n.data.id === firstRootId) || ns[0];
  const k = 1;
  const t = d3.zoomIdentity.translate(rect.width * 0.3 - anchor.x * k, 70).scale(k);
  d3.select(svgRef.value).call(zoomBehavior.transform, t);
}

watch(
  () => props.locateTarget,
  async (t) => {
    if (!t || t.id == null) return;
    // 展开全部祖先
    const s = new Set(expanded.value);
    let p = parentMap.value.get(t.id);
    while (p != null) {
      s.add(p);
      p = parentMap.value.get(p);
    }
    expanded.value = s;
    await nextTick();
    centerOn(t.id, true);
  },
  { deep: true }
);

function centerOn(id, animate) {
  if (id == null || !svgRef.value) return;
  const node = nodes.value.find((n) => n.data.id === id);
  if (!node) return;
  const rect = svgRef.value.getBoundingClientRect();
  const k = transform.value.k || 1;
  const t = d3.zoomIdentity
    .translate(rect.width / 2 - node.x * k, rect.height / 2 - node.y * k)
    .scale(k);
  const svg = d3.select(svgRef.value);
  if (animate) svg.transition().duration(500).call(zoomBehavior.transform, t);
  else svg.call(zoomBehavior.transform, t);
}
</script>

<style scoped>
.tree-svg {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}

.tree-svg:active {
  cursor: grabbing;
}

.link {
  fill: none;
  stroke: var(--ink-2);
  stroke-opacity: 0.5;
  stroke-width: 1px;
}

.emperor-node rect {
  fill: rgba(254, 254, 254, 0.65);
  stroke: var(--ink-2);
  stroke-width: 2px;
}

.emperor-node text {
  font-size: 16px;
  fill: var(--ink);
  text-anchor: middle;
  letter-spacing: 4px;
}

.spine {
  cursor: pointer;
}

.spine .tab {
  fill: var(--olive-fill);
  fill-opacity: 0.6;
  stroke: var(--ink-2);
  stroke-width: 0.84px;
}

.spine .body {
  fill: rgba(254, 254, 254, 0.55);
  stroke: var(--olive);
  stroke-width: 0.75px;
}

.spine:hover .body {
  fill: rgba(254, 254, 254, 0.9);
  stroke: var(--ink-2);
}

.spine.selected .body {
  fill: rgba(165, 166, 141, 0.35);
  stroke: var(--ink-2);
  stroke-width: 1.5px;
}

.spine-title {
  writing-mode: vertical-rl;
  letter-spacing: 2.5px;
  fill: var(--ink);
  text-anchor: middle;
  pointer-events: none;
}

.toggle {
  cursor: pointer;
}

.toggle circle {
  fill: var(--panel);
  stroke: var(--ink-2);
  stroke-width: 0.75px;
}

.toggle text {
  font-size: 8px;
  fill: var(--ink-2);
  text-anchor: middle;
  pointer-events: none;
}
</style>
