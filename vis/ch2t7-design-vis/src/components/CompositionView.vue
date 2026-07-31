<template>
  <div ref="wrapRef" class="composition-wrap">
    <svg ref="svgRef" class="composition-svg">
      <g :transform="transform.toString()">
        <g
          v-for="n in cells"
          :key="n.data.id"
          class="unit"
          :class="[`depth-${Math.min(n.depth, 4)}`, { selected: n.data.id === selectedId }]"
          @click.stop="emit('select', n.data.id)"
          @mouseenter="emitHover(n, $event)"
          @mousemove="emitHover(n, $event)"
          @mouseleave="emit('hover', null)"
        >
          <rect
            class="unit-body"
            :x="n.x0 + inset(n)"
            :y="n.y0 + inset(n)"
            :width="Math.max(1, n.x1 - n.x0 - inset(n) * 2)"
            :height="Math.max(1, n.y1 - n.y0 - inset(n) * 2)"
          />
          <rect
            v-if="n.depth <= 2"
            class="unit-head"
            :x="n.x0 + inset(n)"
            :y="n.y0 + inset(n)"
            :width="Math.min(headerWidth(n), Math.max(1, n.x1 - n.x0 - inset(n) * 2))"
            :height="Math.max(1, n.y1 - n.y0 - inset(n) * 2)"
          />
          <text
            class="unit-title"
            :class="{ major: n.depth <= 1 }"
            :x="n.x0 + inset(n) + Math.min(headerWidth(n), (n.x1 - n.x0) / 2) / 2"
            :y="n.y0 + inset(n) + 10"
          >{{ shortTitle(n.data.title, n) }}</text>
          <text
            v-if="staffSummary(n)"
            class="staff-summary"
            :x="n.x0 + inset(n) + headerWidth(n) + 7"
            :y="n.y0 + inset(n) + 8"
          >{{ staffSummary(n) }}</text>
          <title>{{ tooltip(n) }}</title>
        </g>
      </g>
    </svg>
    <div v-if="focusTitle" class="focus-caption">
      <b>{{ focusTitle }}</b>
      <span>编制构成 · 双击画布复位</span>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as d3 from "d3";

const props = defineProps({
  data: { type: Object, required: true },
  selectedId: Number,
});
const emit = defineEmits(["select", "hover"]);

const wrapRef = ref(null);
const svgRef = ref(null);
const size = ref({ width: 1200, height: 680 });
const transform = ref(d3.zoomIdentity);
let resizeObserver;
let zoomBehavior;

const entityMap = computed(() => new Map(props.data.entities.map((e) => [e.id, e])));
const childrenMap = computed(() => {
  const map = new Map();
  const claimed = new Set();
  for (const edge of props.data.hierarchyEdges) {
    if (claimed.has(edge.child)) continue;
    claimed.add(edge.child);
    if (!map.has(edge.parent)) map.set(edge.parent, []);
    map.get(edge.parent).push(edge.child);
  }
  return map;
});
const parentMap = computed(() => {
  const map = new Map();
  for (const [parent, children] of childrenMap.value) {
    for (const child of children) map.set(child, parent);
  }
  return map;
});
const roots = computed(() => {
  const participants = new Set(childrenMap.value.keys());
  for (const children of childrenMap.value.values()) for (const child of children) participants.add(child);
  return [...participants].filter((id) => !parentMap.value.has(id));
});

function descendants(id, visiting = new Set()) {
  if (visiting.has(id)) return 0;
  visiting.add(id);
  let count = 0;
  for (const child of childrenMap.value.get(id) || []) count += 1 + descendants(child, visiting);
  return count;
}

const focusId = computed(() => {
  if (props.selectedId != null && entityMap.value.has(props.selectedId)) {
    let id = props.selectedId;
    while (parentMap.value.has(id)) id = parentMap.value.get(id);
    if (roots.value.includes(id)) return id;
  }
  return [...roots.value].sort((a, b) => descendants(b) - descendants(a))[0] ?? null;
});
const focusTitle = computed(() => entityMap.value.get(focusId.value)?.title || "");

const staffByOrg = computed(() => {
  const map = new Map();
  for (const edge of props.data.staffEdges) {
    if (!map.has(edge.org)) map.set(edge.org, []);
    map.get(edge.org).push(edge);
  }
  return map;
});

function buildNode(id, depth = 0, seen = new Set()) {
  const entity = entityMap.value.get(id);
  const node = { id, title: entity?.title || `#${id}`, staff: staffByOrg.value.get(id) || [] };
  if (depth >= 3 || seen.has(id)) return node;
  const nextSeen = new Set(seen).add(id);
  const children = (childrenMap.value.get(id) || []).map((child) => buildNode(child, depth + 1, nextSeen));
  if (children.length) node.children = children;
  return node;
}

const hierarchy = computed(() => {
  if (focusId.value == null) return null;
  const root = d3.hierarchy(buildNode(focusId.value));
  root.sum((d) => Math.max(1, d.staff.length * 1.6 + (d.title?.length || 1) / 4));
  root.sort((a, b) => b.value - a.value);
  d3
    .treemap()
    .size([Math.max(640, size.value.width - 32), Math.max(420, size.value.height - 32)])
    .paddingOuter(4)
    .paddingTop((n) => (n.depth <= 1 ? 5 : 2))
    .paddingInner(2)
    .tile(d3.treemapSquarify.ratio(1.25))(root);
  return root;
});
const cells = computed(() => hierarchy.value?.descendants().filter((n) => n.depth > 0) || []);

function inset(n) {
  return n.depth === 1 ? 1.5 : 0.5;
}
function headerWidth(n) {
  return n.depth <= 1 ? 38 : 24;
}
function shortTitle(title, n) {
  const max = Math.max(2, Math.floor((n.y1 - n.y0 - 16) / (n.depth <= 1 ? 22 : 15)));
  return title.length > max ? title.slice(0, max) : title;
}
function officialTitle(id) {
  return entityMap.value.get(id)?.title || `#${id}`;
}
function staffSummary(n) {
  if (n.depth > 2 || n.x1 - n.x0 < 58) return "";
  const parts = n.data.staff.slice(0, 4).map((edge) => {
    const quota = edge.staff_quota ? `${edge.staff_quota}人` : "";
    return `${officialTitle(edge.official)}${quota}`;
  });
  return parts.join(" · ");
}
function tooltip(n) {
  const lines = [n.data.title];
  if (n.data.staff.length) {
    lines.push(...n.data.staff.slice(0, 12).map((edge) => `${officialTitle(edge.official)}${edge.staff_quota ? `：${edge.staff_quota}人` : ""}`));
  } else {
    lines.push("未载明确编制关系");
  }
  return lines.join("\n");
}
function emitHover(n, event) {
  emit("hover", { id: n.data.id, x: event.clientX, y: event.clientY });
}

function resetView() {
  if (!svgRef.value || !zoomBehavior) return;
  const k = 0.96;
  const t = d3.zoomIdentity.translate(16, 16).scale(k);
  d3.select(svgRef.value).transition().duration(300).call(zoomBehavior.transform, t);
}

onMounted(() => {
  resizeObserver = new ResizeObserver(([entry]) => {
    size.value = { width: entry.contentRect.width, height: entry.contentRect.height };
  });
  resizeObserver.observe(wrapRef.value);
  zoomBehavior = d3.zoom().scaleExtent([0.45, 4]).on("zoom", (event) => (transform.value = event.transform));
  const svg = d3.select(svgRef.value).call(zoomBehavior);
  svg.on("dblclick.zoom", null).on("dblclick", resetView);
  nextTick(resetView);
});
onBeforeUnmount(() => resizeObserver?.disconnect());
watch(focusId, () => nextTick(resetView));
</script>

<style scoped>
.composition-wrap { position: relative; width: 100%; height: 100%; overflow: hidden; }
.composition-svg { width: 100%; height: 100%; display: block; cursor: grab; }
.composition-svg:active { cursor: grabbing; }
.unit { cursor: pointer; }
.unit-body { fill: rgba(254, 254, 254, 0.48); stroke: var(--ink-2); stroke-width: 1px; vector-effect: non-scaling-stroke; }
.unit-head { fill: rgba(165, 166, 141, 0.2); stroke: var(--ink-2); stroke-width: 0.65px; vector-effect: non-scaling-stroke; }
.unit:hover .unit-body { fill: rgba(254, 254, 254, 0.88); stroke-width: 1.6px; }
.unit.selected .unit-body { fill: rgba(165, 166, 141, 0.42); stroke-width: 2px; }
.unit-title { writing-mode: vertical-rl; fill: var(--ink); font-size: 13px; letter-spacing: 1.5px; dominant-baseline: hanging; pointer-events: none; }
.unit-title.major { font-size: 20px; font-weight: 700; letter-spacing: 3px; }
.staff-summary { writing-mode: vertical-rl; fill: var(--ink-2); font-size: 9px; letter-spacing: 0.5px; opacity: 0.88; pointer-events: none; }
.focus-caption { position: absolute; left: 18px; top: 14px; display: flex; gap: 12px; align-items: baseline; padding: 5px 10px; color: var(--ink); background: rgba(254,254,254,.82); border: 1px solid var(--line); pointer-events: none; }
.focus-caption b { font-size: 18px; letter-spacing: 3px; }
.focus-caption span { font-size: 11px; color: var(--ink-2); }
</style>
