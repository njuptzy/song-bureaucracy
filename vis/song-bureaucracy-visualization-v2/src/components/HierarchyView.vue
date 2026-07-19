<template>
  <div ref="rootRef" class="hierarchy-view">
    <div class="hierarchy-toolbar">
      <div class="toolbar-copy">
        <strong>{{ focusTitle || "官制层级结构" }}</strong>
        <span>
          {{ listedEntities.length }} 个{{ structureScope === "current" ? "所选时段" : "历时" }}有层级实体
          · {{ isolatedEntities.length }} 个无层级实体
        </span>
      </div>

      <nav v-if="ancestorTrail.length" class="ancestor-bar" aria-label="上级链">
        <template v-for="(ancestor, index) in ancestorTrail" :key="ancestor.id">
          <span v-if="index" class="ancestor-sep">›</span>
          <button type="button" :title="ancestor.title" @click="focusEntity(ancestor.id)">
            {{ ancestor.title }}
          </button>
        </template>
        <span class="ancestor-sep">›</span>
        <span class="ancestor-current">{{ focusTitle }}</span>
      </nav>

      <span class="toolbar-legend" aria-label="层级图图例">
        <span class="legend-item"><i class="node-sample org"></i>机构</span>
        <span class="legend-item"><i class="node-sample office"></i>官职</span>
        <span class="legend-item via-sup">
          <i class="edge-mark-sample"><svg viewBox="0 0 16 16"><path :d="VIA_ICONS.sup" /></svg></i>上下级
        </span>
        <span class="legend-item via-staff">
          <i class="edge-mark-sample"><svg viewBox="0 0 16 16"><path :d="VIA_ICONS.staff" /></svg></i>隶属
        </span>
        <span class="legend-item via-alias">
          <i class="edge-mark-sample"><svg viewBox="0 0 16 16"><path :d="VIA_ICONS.alias" /></svg></i>统称
        </span>
        <span class="legend-item"><i class="line-sample secondary"></i>其他上级</span>
      </span>

      <div class="scope-switch" aria-label="层级结构时间范围">
        <button
          type="button"
          :class="{ active: structureScope === 'current' }"
          @click="structureScope = 'current'"
        >
          所选时段
        </button>
        <button
          type="button"
          :class="{ active: structureScope === 'history' }"
          @click="structureScope = 'history'"
        >
          历时全貌
        </button>
      </div>
    </div>

    <div class="canvas-shell">
      <div ref="stageRef" class="canvas-stage">
      <button
        type="button"
        class="entity-browser-trigger"
        :class="{ active: browserOpen }"
        :title="browserOpen ? '关闭实体目录' : '打开实体目录'"
        @click="browserOpen = !browserOpen"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 4v4M5 20v-5h14v5M5 15v-4h14v4M12 8H5v3M12 8h7v3" />
          <rect x="9" y="2" width="6" height="4" rx="1" />
          <rect x="2" y="18" width="6" height="4" rx="1" />
          <rect x="9" y="18" width="6" height="4" rx="1" />
          <rect x="16" y="18" width="6" height="4" rx="1" />
        </svg>
        <span>实体目录</span>
      </button>

      <aside v-if="browserOpen" class="entity-browser">
        <div class="browser-head">
          <span>机构与官职</span>
          <button type="button" aria-label="关闭" @click="browserOpen = false">×</button>
        </div>
        <div class="browser-scroll">
          <button
            v-for="item in listedEntities"
            :key="item.id"
            type="button"
            class="entity-item"
            :class="{
              focused: item.id === focusId,
              office: item.type === '官职',
              'linked-hover': item.id === hoveredEntityId,
            }"
            @click="onItemClick(item)"
          >
            <i aria-hidden="true"></i>
            <span>{{ item.title }}</span>
            <small v-if="activeEntities.has(item.id)" title="所选时段有记录">●</small>
          </button>
          <div v-if="isolatedEntities.length" class="list-divider">
            {{ structureScope === "current" ? "所选时段无层级关系" : "历时无层级关系" }}
          </div>
          <button
            v-for="item in isolatedEntities"
            :key="item.id"
            type="button"
            class="entity-item quiet"
            :class="{ focused: item.id === focusId, office: item.type === '官职' }"
            @click="onItemClick(item)"
          >
            <i aria-hidden="true"></i>
            <span>{{ item.title }}</span>
            <small v-if="activeEntities.has(item.id)" title="所选时段有记录">●</small>
          </button>
        </div>
      </aside>

      <div v-if="focusId == null" class="stage-hint">
        <span class="empty-seal">选</span>
        <p>从上方搜索或打开实体目录，选择机构或官职。</p>
      </div>

      <svg
        v-else
        ref="svgRef"
        class="hierarchy-canvas"
        :viewBox="`0 0 ${viewW} ${viewH}`"
        role="img"
        :aria-label="`${focusTitle}层级结构图`"
        @wheel.prevent="onWheel"
        @pointermove="onPointerMove"
        @pointerup="endPan"
        @pointercancel="endPan"
        @pointerleave="endPan"
      >
        <defs>
          <marker id="hierarchy-arrow" viewBox="0 0 8 8" refX="6.5" refY="4" markerWidth="5" markerHeight="5" orient="auto">
            <path d="M0 0L8 4L0 8Z" />
          </marker>
          <filter id="node-shadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#5a3a20" flood-opacity="0.16" />
          </filter>
        </defs>

        <rect
          class="canvas-hit-area"
          x="0"
          y="0"
          :width="viewW"
          :height="viewH"
          @pointerdown="beginPan"
        />

        <g :transform="worldTransform">
          <g class="secondary-edges" aria-hidden="true">
            <path
              v-for="edge in visibleSecondaryEdges"
              :key="edge.key"
              :d="secondaryEdgePath(edge)"
              :class="['canvas-edge', 'secondary', `via-${viaClass(edge)}`]"
            />
          </g>

          <g class="primary-buses" aria-hidden="true">
            <path
              v-for="bus in canvasLayout.buses"
              :key="bus.key"
              :d="busPath(bus)"
              class="bus-line"
            />
          </g>

          <g class="primary-edges">
            <g
              v-for="edge in canvasLayout.edges"
              :key="edge.key"
              :class="['edge-group', `via-${viaClass(edge)}`]"
              @click.stop="toggleEdgeEvidence(edge)"
            >
              <path :d="stemPath(edge)" class="canvas-edge" />
              <path :d="stemPath(edge)" class="edge-hit" />
              <g
                v-if="edge.data"
                class="edge-mark"
                :transform="`translate(${edge.target.x} ${edge.busY})`"
              >
                <circle r="7.5" />
                <svg x="-5" y="-5" width="10" height="10" viewBox="0 0 16 16" aria-hidden="true">
                  <path :d="VIA_ICONS[viaClass(edge)]" />
                </svg>
              </g>
              <title>{{ edgeTooltip(edge) }}</title>
            </g>
          </g>

          <g class="canvas-nodes">
            <g
              v-for="node in canvasLayout.nodes"
              :key="node.key"
              :transform="`translate(${node.x} ${node.y})`"
              :class="[
                'canvas-node',
                node.data.entType === '官职' ? 'office' : 'org',
                {
                  focus: node.data.id === focusId,
                  selected: node.data.id === selectedEntityId,
                  'linked-hover': node.data.id === hoveredEntityId,
                  overflow: node.data.overflow,
                },
              ]"
              :data-entity-id="typeof node.data.id === 'number' ? node.data.id : null"
              tabindex="0"
              role="button"
              @click.stop="onNodeClick(node.data)"
              @keydown.enter.prevent="onNodeClick(node.data)"
            >
              <rect
                :x="-nodeWidth(node.data) / 2"
                :y="-nodeHeight(node.data) / 2"
                :width="nodeWidth(node.data)"
                :height="nodeHeight(node.data)"
                rx="5"
              />
              <circle
                v-if="isActiveId(node.data.id)"
                class="active-dot"
                :cx="nodeWidth(node.data) / 2 - 4"
                :cy="-nodeHeight(node.data) / 2 + 5"
                r="3.5"
              />
              <g
                v-if="!node.data.overflow && node.data.id !== focusId"
                class="focus-control"
                :transform="`translate(${-nodeWidth(node.data) / 2 - 10} ${-nodeHeight(node.data) / 2 + 10})`"
                @click.stop="focusEntity(node.data.id)"
              >
                <circle class="focus-target-outer" r="7" />
                <circle class="focus-target-inner" r="3" />
                <path d="M-7 0H-4M4 0H7M0-7V-4M0 4V7" />
                <title>以此为中心</title>
              </g>
              <text class="node-title" text-anchor="middle">
                <tspan
                  v-for="(char, index) in node.data.displayChars"
                  :key="index"
                  x="0"
                  :dy="index === 0 ? titleStart(node.data) : 15"
                >{{ char }}</tspan>
              </text>
              <g
                v-if="node.data.hasChildren && !node.data.overflow && !node.data.depthLimited"
                class="expand-control"
                :transform="`translate(0 ${nodeHeight(node.data) / 2 + 9})`"
                @click.stop="toggle(node.data.id)"
              >
                <circle r="6" />
                <path d="M-3 0H3" />
                <path v-if="!expanded.has(node.data.id)" d="M0-3V3" />
                <title>{{ expanded.has(node.data.id) ? "收起下级" : "展开下级" }}</title>
              </g>
              <text
                v-if="node.data.badge"
                class="node-badge"
                text-anchor="start"
                x="10"
                :y="nodeHeight(node.data) / 2 + 27"
              >{{ node.data.badge }}</text>
              <title>{{ nodeTooltip(node.data) }}</title>
            </g>
          </g>
        </g>
      </svg>

      <div v-if="focusId != null" class="canvas-caption">
        <strong>{{ canvasLayout.realNodeCount }}</strong> 个可见实体
        <span v-if="canvasLayout.hiddenCount">· 尚有 {{ canvasLayout.hiddenCount }} 个下级待展开</span>
        <span>· 点击节点看详情，点击靶标设为中心</span>
      </div>

      <div class="canvas-controls">
        <div class="layout-switch" aria-label="层级画布模式">
          <button type="button" :class="{ active: layoutMode === 'overview' }" @click="setLayoutMode('overview')">
            全貌
          </button>
          <button type="button" :class="{ active: layoutMode === 'focus' }" @click="setLayoutMode('focus')">
            聚焦
          </button>
        </div>
        <div class="zoom-controls">
          <button type="button" aria-label="缩小" @click="changeZoom(-0.15)">−</button>
          <button type="button" aria-label="适应画布" @click="resetViewport">适</button>
          <button type="button" aria-label="放大" @click="changeZoom(0.15)">＋</button>
        </div>
      </div>

      </div>

      <aside v-if="evidenceCard" class="evidence-panel">
        <div class="evidence-head">
          <span>{{ evidenceCard.relations[0].type }} · {{ evidencePeriodLabel(evidenceCard.relations) }}</span>
          <button type="button" aria-label="关闭" @click="evidenceCard = null">×</button>
        </div>
        <p class="evidence-pair">
          {{ evidenceCard.relations[0].subjectTitle }} → {{ evidenceCard.relations[0].objectTitle }}
        </p>
        <div v-for="relation in evidenceCard.relations" :key="relation.id" class="evidence-record">
          <p v-if="evidenceCard.relations.length > 1" class="evidence-period">
            {{ relationPeriodLabel(relation) }}
          </p>
          <article v-for="(citation, index) in relation.citations" :key="index">
            <cite>{{ citation.citation }}</cite>
            <blockquote>{{ citation.quotation }}</blockquote>
            <p v-if="citation.note">{{ citation.note }}</p>
          </article>
          <p v-if="!relation.citations.length" class="quiet-text">该期关系暂无引文记录。</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
// 官制层级结构二维画布（2026-07 重写视口层）：
// - 布局在“世界坐标”中计算（d3Tree），SVG viewBox 固定为容器像素尺寸，
//   视口状态 {zoom, panX, panY} 显式管理，不再有隐式 meet 缩放叠加：
//   「适」= 按内容 bbox 计算 fit；滚轮以鼠标为锚缩放；拖动按屏幕像素平移。
// - 展开模型：每个父节点独立分页（余N项点击翻页），删除全局节点预算；
//   因多上级去重而未显示的实体不计入“余N项”，以辅助虚线表达。
// - 展开/收起/翻页不触发全画布重新居中：被操作的节点锚定在原地，子树就地显隐；
//   只有重设中心、切换时间范围/所选时段/历时/布局模式时才重新 fit。
//   单纯打开或关闭详情不改变中心，也不扰动画布视口。
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { hierarchy as d3Hierarchy, tree as d3Tree } from "d3";
import { buildEntityGraph, relationPeriodsLabel } from "@/utils/hierarchy";

const props = defineProps({
  dataset: { type: Object, required: true },
  selectedEntityId: { type: Number, default: null },
  hoveredEntityId: { type: Number, default: null },
  activeEntities: { type: Set, default: () => new Set() },
  range: { type: Array, default: null },
});
const emit = defineEmits(["select-entity"]);

const PRIMARY_VIA = { 上下级机构: 0, 编制隶属: 1, 统称与实例: 2 };
// 关系类型图标（16×16 简笔，stroke=currentColor）：建筑=上下级机构、人形=编制隶属、交叠方框=统称与实例
const VIA_ICONS = {
  sup: "M2 13h12M3.5 13V5.5L8 2l4.5 3.5V13M6 13V8.5h1.6V13M8.4 13V8.5H10V13",
  staff: "M8 7.2a2.6 2.6 0 1 0 0-5.2 2.6 2.6 0 0 0 0 5.2zM3 13.5c.6-3 2.6-4.3 5-4.3s4.4 1.3 5 4.3",
  alias: "M2.5 2.5h7v7h-7zM6.5 6.5h7v7h-7z",
};
const NODE_WIDTH = 42;
const NODE_HEIGHT_MAX = 124;
const OVERVIEW_CHILD_LIMIT = 24;
const FOCUS_CHILD_LIMIT = 14;
const OVERVIEW_MAX_DEPTH = 7;
const FOCUS_MAX_DEPTH = 2;
const X_SEP = 84;
const Y_SEP = 190;
const ZOOM_MIN = 0.12;
const ZOOM_MAX = 3;

const structureScope = ref("current");
const layoutMode = ref("overview");
const browserOpen = ref(false);
const focusId = ref(null);
const expanded = reactive(new Set());
const childLimits = reactive(new Map());
const evidenceCard = ref(null);
const rootRef = ref(null);
const stageRef = ref(null);
const svgRef = ref(null);

// —— 视口状态（世界坐标 → 屏幕坐标：translate(pan) scale(zoom)）——
const zoom = ref(1);
const panX = ref(0);
const panY = ref(0);
const viewW = ref(1120);
const viewH = ref(560);
const drag = reactive({ active: false, pointerId: null, x: 0, y: 0 });
let resizeObserver;

const graph = computed(() =>
  buildEntityGraph(props.dataset, structureScope.value === "current" ? props.range : null)
);
const relationById = computed(() => new Map(props.dataset.relations.map((relation) => [relation.id, relation])));
const linkedIds = computed(() => new Set([...graph.value.childrenOf.keys(), ...graph.value.parentRelsOf.keys()]));

function byTimeMatch(a, b) {
  const tier = (props.activeEntities.has(b.id) ? 1 : 0) - (props.activeEntities.has(a.id) ? 1 : 0);
  return tier || b.eventCount - a.eventCount || a.title.localeCompare(b.title, "zh");
}

const listedEntities = computed(() =>
  [...linkedIds.value]
    .map((id) => graph.value.entityById.get(id))
    .filter(Boolean)
    .sort(byTimeMatch)
);

const isolatedEntities = computed(() =>
  graph.value.isolated
    .map((id) => graph.value.entityById.get(id))
    .filter(Boolean)
    .sort(byTimeMatch)
);

const ancestorTrail = computed(() => {
  if (focusId.value == null) return [];
  return graph.value.ancestorChain(focusId.value).map((id) => {
    const entity = graph.value.entityById.get(id);
    return { id, title: entity?.title ?? `#${id}`, entType: entity?.type ?? "" };
  });
});

const focusTitle = computed(() => graph.value.entityById.get(focusId.value)?.title ?? "");

function sortedChildren(id) {
  return [...(graph.value.childrenOf.get(id) || [])].sort(
    (a, b) =>
      (PRIMARY_VIA[a.via] ?? 9) - (PRIMARY_VIA[b.via] ?? 9) ||
      (graph.value.entityById.get(b.entityId)?.eventCount ?? 0) -
        (graph.value.entityById.get(a.entityId)?.eventCount ?? 0) ||
      (graph.value.entityById.get(a.entityId)?.title ?? "").localeCompare(
        graph.value.entityById.get(b.entityId)?.title ?? "",
        "zh"
      )
  );
}

function displayChars(title) {
  const chars = [...String(title || "")];
  return chars.length > 7 ? [...chars.slice(0, 6), "…"] : chars;
}

function makeBadge(edge, extraParentCount = 0) {
  const bits = [];
  if (edge?.via === "编制隶属" && edge.quota != null) bits.push(`${edge.quota}${edge.staffType || "员"}`);
  if (structureScope.value === "history" && edge?.periods?.length) {
    const first = edge.periods[0];
    bits.push(first.start === first.end ? `${first.start}` : `${first.start}—${first.end}`);
  }
  if (extraParentCount) bits.push(`另${extraParentCount}上级`);
  return bits.join("·");
}

const defaultChildLimit = () =>
  layoutMode.value === "focus" ? FOCUS_CHILD_LIMIT : OVERVIEW_CHILD_LIMIT;

const visualTree = computed(() => {
  if (focusId.value == null || !graph.value.entityById.has(focusId.value)) return null;
  const seen = new Set();
  const maxDepth = layoutMode.value === "focus" ? FOCUS_MAX_DEPTH : OVERVIEW_MAX_DEPTH;
  let hiddenCount = 0;

  function build(id, edge = null, depth = 0, path = new Set()) {
    const entity = graph.value.entityById.get(id);
    if (!entity || path.has(id) || seen.has(id)) return null;
    seen.add(id);

    const allChildren = sortedChildren(id).filter((child) => !path.has(child.entityId));
    const data = {
      id,
      title: entity.title,
      displayChars: displayChars(entity.title),
      entType: entity.type,
      eventCount: entity.eventCount,
      yearMin: entity.yearMin,
      yearMax: entity.yearMax,
      edge,
      hasChildren: allChildren.length > 0,
      depthLimited: allChildren.length > 0 && depth >= maxDepth,
      badge: makeBadge(edge, Math.max(0, (graph.value.parentRelsOf.get(id)?.length || 1) - 1)),
      children: [],
    };

    if (!allChildren.length) return data;
    if (depth >= maxDepth) {
      hiddenCount += allChildren.length;
      data.badge = [data.badge, `下级${allChildren.length}`].filter(Boolean).join(" · ");
      return data;
    }
    if (!expanded.has(id)) return data;

    const limit = childLimits.get(id) ?? defaultChildLimit();
    const nextPath = new Set(path).add(id);
    let shown = 0;
    let omitted = 0;
    for (const child of allChildren) {
      if (seen.has(child.entityId)) continue; // 多上级去重：不计入“余N项”
      if (shown >= limit) {
        omitted += 1;
        continue;
      }
      const childNode = build(child.entityId, child, depth + 1, nextPath);
      if (childNode) {
        data.children.push(childNode);
        shown += 1;
      }
    }
    if (omitted > 0) {
      hiddenCount += omitted;
      data.children.push({
        id: `more-${id}`,
        key: `more-${id}`,
        title: `余${omitted}项`,
        displayChars: displayChars(`余${omitted}项`),
        entType: "overflow",
        overflow: true,
        parentId: id,
        omitted,
        children: [],
      });
    }
    return data;
  }

  const root = build(focusId.value);
  return root ? { root, hiddenCount } : null;
});

const canvasLayout = computed(() => {
  const empty = { nodes: [], edges: [], buses: [], secondaryEdges: [], hiddenCount: 0, realNodeCount: 0, bbox: null };
  if (!visualTree.value) return empty;

  const root = d3Hierarchy(visualTree.value.root, (data) => data.children);
  d3Tree().nodeSize([X_SEP, Y_SEP])(root);
  const nodes = root.descendants().map((node) =>
    Object.assign(node, { key: node.data.key || String(node.data.id) })
  );

  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const node of nodes) {
    const w = nodeWidth(node.data);
    const h = nodeHeight(node.data);
    // 徽标文字从卡片右侧 x=10 起排，按每字约 8px 估算宽度，避免 bbox 裁掉徽标
    const badgeExtent = node.data.badge ? 10 + node.data.badge.length * 8 : 0;
    minX = Math.min(minX, node.x - w / 2);
    maxX = Math.max(maxX, node.x + Math.max(w / 2, badgeExtent));
    minY = Math.min(minY, node.y - h / 2);
    maxY = Math.max(maxY, node.y + h / 2 + 40); // 展开按钮 + 徽标 + 下行连线起点空间
  }
  const bbox = {
    w: maxX - minX + 80,
    h: maxY - minY + 76,
    cx: (minX + maxX) / 2,
    cy: (minY + maxY) / 2 + 10,
  };

  const positionedById = new Map(
    nodes.filter((node) => typeof node.data.id === "number").map((node) => [node.data.id, node])
  );
  const edges = root.links().map((link, index) => ({
    key: `primary-${link.target.data.id}-${index}`,
    source: link.source,
    target: link.target,
    data: link.target.data.edge || null,
  }));

  // 同一父节点的所有子节点只共用一条横向总线：
  // 父节点竖线 → 一条横线 → 每个子节点各自向下的箭头。
  // 关系类型在总线分叉点用「颜色 + 类型图标」圆标区分，连线本身全为实线。
  const edgesBySource = new Map();
  for (const edge of edges) {
    const sourceKey = edge.source.data.id;
    if (!edgesBySource.has(sourceKey)) edgesBySource.set(sourceKey, []);
    edgesBySource.get(sourceKey).push(edge);
  }

  const buses = [];
  for (const [sourceId, members] of edgesBySource) {
    const source = members[0].source;
    // 下行连线从卡片下缘出发，穿过展开按钮（纸色圆底遮住线头），直达总线
    const sourceY = source.y + nodeHeight(source.data) / 2;
    const targetY = Math.min(
      ...members.map((edge) => edge.target.y - nodeHeight(edge.target.data) / 2 - 8)
    );
    const busY = sourceY + (targetY - sourceY) * 0.48;
    for (const edge of members) edge.busY = busY;
    buses.push({
      key: `bus-${sourceId}`,
      source,
      members,
      busY,
      minX: Math.min(source.x, ...members.map((edge) => edge.target.x)),
      maxX: Math.max(source.x, ...members.map((edge) => edge.target.x)),
    });
  }

  const secondaryEdges = [];
  for (const target of nodes) {
    if (typeof target.data.id !== "number") continue;
    const primaryParentId = target.parent?.data.id;
    for (const parentRel of graph.value.parentRelsOf.get(target.data.id) || []) {
      if (parentRel.entityId === primaryParentId) continue;
      const source = positionedById.get(parentRel.entityId);
      if (!source) continue;
      const fullEdge = (graph.value.childrenOf.get(parentRel.entityId) || []).find(
        (edge) => edge.entityId === target.data.id && edge.via === parentRel.via
      );
      secondaryEdges.push({
        key: `secondary-${parentRel.entityId}-${target.data.id}-${parentRel.relationId}`,
        source,
        target,
        data: fullEdge || parentRel,
      });
    }
  }

  return {
    nodes,
    edges,
    buses,
    secondaryEdges,
    hiddenCount: visualTree.value.hiddenCount,
    realNodeCount: nodes.filter((node) => typeof node.data.id === "number").length,
    bbox,
  };
});

const visibleSecondaryEdges = computed(() => {
  const highlighted = new Set(
    [props.selectedEntityId, props.hoveredEntityId].filter((id) => typeof id === "number")
  );
  if (!highlighted.size) return [];
  return canvasLayout.value.secondaryEdges.filter(
    (edge) => highlighted.has(edge.source.data.id) || highlighted.has(edge.target.data.id)
  );
});

const worldTransform = computed(
  () => `translate(${panX.value} ${panY.value}) scale(${zoom.value})`
);

function nodeWidth(data) {
  return data.overflow ? 48 : NODE_WIDTH;
}

function nodeHeight(data) {
  if (data.overflow) return 70;
  // 高度按竖排字数给足，标题不溢出卡片
  return Math.max(68, Math.min(NODE_HEIGHT_MAX, data.displayChars.length * 15 + 26));
}

function titleStart(data) {
  return -((data.displayChars.length - 1) * 15) / 2 + 4;
}

function busPath(bus) {
  if (!bus.source) return "";
  const sourceY = bus.source.y + nodeHeight(bus.source.data) / 2;
  return `M${bus.source.x},${sourceY}V${bus.busY}M${bus.minX},${bus.busY}H${bus.maxX}`;
}

function stemPath(edge) {
  if (!edge.target || edge.busY == null) return "";
  const targetY = edge.target.y - nodeHeight(edge.target.data) / 2 - 8;
  return `M${edge.target.x},${edge.busY}V${targetY}`;
}

function secondaryEdgePath(edge) {
  if (!edge.source || !edge.target) return "";
  const sourceY = edge.source.y + nodeHeight(edge.source.data) / 2 + 8;
  const targetY = edge.target.y - nodeHeight(edge.target.data) / 2 - 8;
  const middleY = sourceY + (targetY - sourceY) * 0.48;
  return `M${edge.source.x},${sourceY}V${middleY}H${edge.target.x}V${targetY}`;
}

function viaClass(edge) {
  const via = edge?.data?.via;
  if (via === "上下级机构") return "sup";
  if (via === "编制隶属") return "staff";
  if (via === "统称与实例") return "alias";
  return "sup";
}

function isActiveId(id) {
  return typeof id === "number" && props.activeEntities.has(id);
}

function nodeTooltip(data) {
  if (data.overflow) return `点击展开下一页（还有 ${data.omitted} 个下级）`;
  const bits = [`${data.title}（${data.entType}）`, `共${data.eventCount}条记录`];
  if (data.yearMin != null) bits.push(`${data.yearMin}—${data.yearMax}年有记录`);
  if (data.edge) bits.push(`关系：${data.edge.via}`);
  bits.push("点击看详情，点击左上靶标设为中心");
  return bits.join(" · ");
}

function edgeTooltip(edge) {
  if (!edge.data) return "层级关系";
  const bits = [edge.data.via || "层级关系"];
  if (edge.data.periods?.length) bits.push(edgePeriodLabel(edge.data));
  if (edge.data.quota != null) bits.push(`${edge.data.quota}${edge.data.staffType || "员"}`);
  bits.push("点击查看关系证据");
  return bits.join(" · ");
}

function periodText(start, end) {
  return start === end ? `${start}年` : `${start}—${end}年`;
}

function edgePeriodLabel(edge) {
  const periods = edge.periods || [];
  if (!periods.length) return "时间未明";
  const suffix = edge.hasUndated ? "、另有时间未明记录" : "";
  if (periods.length <= 2) return `${periods.map((period) => periodText(period.start, period.end)).join("、")}${suffix}`;
  return `${periodText(periods[0].start, periods[0].end)}等${periods.length}期${suffix}`;
}

function relationKey(edge) {
  return (edge?.relationIds || [edge?.relationId]).filter(Boolean).join(",");
}

function toggleEdgeEvidence(edge) {
  if (!edge.data) return;
  const key = relationKey(edge.data);
  if (!key) return;
  if (evidenceCard.value?.key === key) {
    evidenceCard.value = null;
    return;
  }
  const relations = (edge.data.relationIds || [edge.data.relationId])
    .map((id) => relationById.value.get(id))
    .filter(Boolean)
    .sort((a, b) => (a.periods?.[0]?.start ?? Infinity) - (b.periods?.[0]?.start ?? Infinity) || a.id - b.id);
  if (relations.length) evidenceCard.value = { key, relations };
}

function relationPeriodLabel(relation) {
  return relationPeriodsLabel(relation);
}

function evidencePeriodLabel(relations) {
  const labels = [...new Set(relations.map(relationPeriodLabel))];
  return labels.length <= 2 ? labels.join("、") : `${labels[0]}等${labels.length}期记录`;
}

function onItemClick(item) {
  if (item.id === focusId.value) toggleSelection(item.id);
  else focusEntity(item.id);
  browserOpen.value = false;
}

let suppressNextFocus = false;

function toggleSelection(id) {
  suppressNextFocus = true;
  emit("select-entity", props.selectedEntityId === id ? null : id);
}

async function onNodeClick(data) {
  if (data.overflow) {
    const before = canvasNodePos(data.parentId);
    childLimits.set(data.parentId, (childLimits.get(data.parentId) ?? defaultChildLimit()) + defaultChildLimit());
    await nextTick();
    anchorViewport(before, data.parentId);
    return;
  }
  browserOpen.value = false;
  toggleSelection(data.id);
}

async function focusEntity(id, emitSelection = true) {
  if (id == null || !graph.value.entityById.has(id)) return;
  focusId.value = id;
  evidenceCard.value = null;
  childLimits.clear();
  expandFocusedTree();
  await nextTick();
  resetViewport();
  if (emitSelection && props.selectedEntityId !== id) emit("select-entity", id);
}

function expandFocusedTree() {
  expanded.clear();
  const stack = [focusId.value];
  const seen = new Set();
  while (stack.length) {
    const current = stack.pop();
    if (current == null || seen.has(current)) continue;
    seen.add(current);
    expanded.add(current);
    for (const child of graph.value.childrenOf.get(current) || []) stack.push(child.entityId);
  }
}

// 展开/收起不再触发全画布重新居中：记录被点节点的位置，
// 重新布局后平移视口把它锚回原地，子树就地出现或消失。
async function toggle(id) {
  evidenceCard.value = null;
  const before = canvasNodePos(id);
  if (expanded.has(id)) expanded.delete(id);
  else expanded.add(id);
  await nextTick();
  anchorViewport(before, id);
}

function canvasNodePos(id) {
  const node = canvasLayout.value.nodes.find((item) => item.data.id === id);
  return node ? { x: node.x, y: node.y } : null;
}

function anchorViewport(before, id) {
  if (!before) return;
  const after = canvasNodePos(id);
  if (!after) return;
  panX.value += (before.x - after.x) * zoom.value;
  panY.value += (before.y - after.y) * zoom.value;
}

async function setLayoutMode(mode) {
  layoutMode.value = mode;
  childLimits.clear();
  await nextTick();
  resetViewport();
}

// —— 视口操作 ——

function clampZoom(value) {
  return Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, value));
}

// 按内容 bbox 计算缩放与居中，「适」按钮与重设中心时调用
function fitViewport() {
  const bbox = canvasLayout.value.bbox;
  if (!bbox || !viewW.value || !viewH.value) return;
  const next = clampZoom(Math.min(viewW.value / bbox.w, viewH.value / bbox.h) * 0.94);
  zoom.value = Math.min(next, 1.2);
  panX.value = viewW.value / 2 - bbox.cx * zoom.value;
  panY.value = viewH.value / 2 - bbox.cy * zoom.value;
}

function resetViewport() {
  fitViewport();
}

function zoomAt(factor, cx, cy) {
  const next = clampZoom(zoom.value * factor);
  if (next === zoom.value) return;
  panX.value = cx - ((cx - panX.value) * next) / zoom.value;
  panY.value = cy - ((cy - panY.value) * next) / zoom.value;
  zoom.value = next;
}

function changeZoom(delta) {
  zoomAt(1 + delta, viewW.value / 2, viewH.value / 2);
}

function onWheel(event) {
  const rect = svgRef.value?.getBoundingClientRect();
  if (!rect) return;
  // 指数步进：触控板连续小滚动平滑，鼠标滚轮一格约 ±15%，避免大幅跳变
  const unit = event.deltaMode === 1 ? 16 : 1;
  const factor = Math.exp((-event.deltaY * unit * 0.0016));
  zoomAt(factor, event.clientX - rect.left, event.clientY - rect.top);
}

function beginPan(event) {
  drag.active = true;
  drag.pointerId = event.pointerId;
  drag.x = event.clientX;
  drag.y = event.clientY;
  svgRef.value?.setPointerCapture?.(event.pointerId);
}

function onPointerMove(event) {
  if (!drag.active || drag.pointerId !== event.pointerId) return;
  panX.value += event.clientX - drag.x;
  panY.value += event.clientY - drag.y;
  drag.x = event.clientX;
  drag.y = event.clientY;
}

function endPan(event) {
  if (!drag.active) return;
  if (event?.pointerId != null && drag.pointerId !== event.pointerId) return;
  drag.active = false;
  if (drag.pointerId != null) svgRef.value?.releasePointerCapture?.(drag.pointerId);
  drag.pointerId = null;
}

onMounted(() => {
  resizeObserver = new ResizeObserver((entries) => {
    const rect = entries[0]?.contentRect;
    if (!rect?.width || !rect?.height) return;
    viewW.value = Math.round(rect.width);
    viewH.value = Math.round(rect.height);
    // 画布可用区域变化后重新计算最佳位置，避免窗口或面板变化造成偏移。
    resetViewport();
  });
  if (stageRef.value) resizeObserver.observe(stageRef.value);
});

onBeforeUnmount(() => resizeObserver?.disconnect());

watch(
  () => props.selectedEntityId,
  (id) => {
    if (suppressNextFocus) {
      suppressNextFocus = false;
      return;
    }
    if (id != null && id !== focusId.value) focusEntity(id, false);
  }
);

// 自动重新居中的触发点：切换时间范围、所选时段/历时。
// 重设中心与切换布局模式在各自函数内显式 fit；展开/收起/翻页走节点锚定，视口不动。
watch(structureScope, async () => {
  evidenceCard.value = null;
  childLimits.clear();
  await nextTick();
  resetViewport();
});

watch(
  () => props.range,
  async () => {
    await nextTick();
    resetViewport();
  },
  { deep: true }
);

// 深链：?view=hierarchy&entity=实体ID
if (props.selectedEntityId != null) focusEntity(props.selectedEntityId, false);
</script>

<style scoped lang="scss">
.hierarchy-view {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.hierarchy-toolbar {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  min-height: 38px;
  gap: 16px;
  border-bottom: 1px solid var(--line-light);
  padding: 3px 12px 5px;
  color: rgba(90, 58, 32, 0.62);
}

.toolbar-copy {
  display: flex;
  align-items: baseline;
  min-width: 0;
  gap: 9px;

  strong {
    overflow: hidden;
    max-width: 220px;
    color: var(--ink);
    font-size: 15px;
    font-weight: 400;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  span {
    font-size: 10px;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }
}

.ancestor-bar {
  display: flex;
  flex: 1;
  align-items: center;
  min-width: 0;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;

  button {
    flex: 0 0 auto;
    border: 0;
    border-bottom: 1px solid var(--line);
    padding: 1px 2px;
    color: var(--ink-soft);
    background: transparent;
    font-size: 10px;
    cursor: pointer;
  }

  .ancestor-sep {
    color: var(--line);
    font-size: 10px;
  }

  .ancestor-current {
    overflow: hidden;
    color: var(--ink);
    font-size: 11px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.scope-switch,
.layout-switch,
.zoom-controls {
  display: inline-flex;
  flex: 0 0 auto;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 4px;

  button {
    border: 0;
    border-right: 1px solid var(--line-light);
    padding: 3px 8px;
    color: rgba(90, 58, 32, 0.66);
    background: rgba(244, 241, 234, 0.72);
    font-size: 10px;
    cursor: pointer;

    &:last-child {
      border-right: 0;
    }

    &.active {
      color: var(--paper);
      background: var(--ink-soft);
    }
  }
}

.canvas-shell {
  display: flex;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.canvas-stage {
  position: relative;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.hierarchy-canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: grab;
  touch-action: none;

  &:active {
    cursor: grabbing;
  }
}

.canvas-hit-area {
  fill: transparent;
}

.canvas-edge {
  fill: none;
  stroke: var(--ink-soft);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.15;
  marker-end: url(#hierarchy-arrow);
  pointer-events: none;
}

.bus-line {
  fill: none;
  stroke: var(--ink-soft);
  stroke-linecap: square;
  stroke-linejoin: miter;
  stroke-width: 1.15;
}

.edge-group {
  color: var(--ink-soft);
  cursor: pointer;

  &.via-staff .canvas-edge {
    stroke: #b96f42;
  }

  &.via-alias .canvas-edge {
    stroke: #8e8175;
  }

  &:hover .canvas-edge {
    stroke-width: 2.4;
  }
}

// 总线分叉点的类型图标标记：纸色圆底 + 类型色描边与图标
.edge-mark {
  pointer-events: none;

  circle {
    fill: var(--paper);
    stroke: var(--ink-soft);
    stroke-width: 1.2;
  }

  path {
    fill: none;
    stroke: var(--ink-soft);
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 1.5;
  }
}

.edge-group.via-staff .edge-mark circle,
.edge-group.via-staff .edge-mark path {
  stroke: #b96f42;
}

.edge-group.via-alias .edge-mark circle,
.edge-group.via-alias .edge-mark path {
  stroke: #8e8175;
}

.edge-hit {
  fill: none;
  stroke: transparent;
  stroke-width: 12;
}

.secondary-edges .canvas-edge {
  stroke: var(--rust);
  stroke-dasharray: 5 5;
  stroke-width: 1;
  opacity: 0.62;
}

#hierarchy-arrow path {
  fill: var(--ink-soft);
}

.canvas-node {
  color: var(--paper);
  cursor: pointer;
  outline: none;

  rect {
    fill: #6d4a2e;
    stroke: rgba(90, 58, 32, 0.82);
    stroke-width: 1;
    filter: url(#node-shadow);
  }

  &.office rect {
    fill: #55756c;
    stroke: #45635b;
  }

  &.focus rect {
    fill: #263a4a;
    stroke: #172b3d;
    stroke-width: 2;
  }

  &.selected:not(.focus) rect {
    stroke: var(--rust);
    stroke-width: 3;
  }

  &.linked-hover rect {
    stroke: var(--rust);
    stroke-width: 4;
  }

  &.overflow rect {
    fill: rgba(244, 241, 234, 0.92);
    stroke: var(--line);
    stroke-dasharray: 4 3;
    filter: none;
  }

  &.overflow .node-title {
    fill: var(--ink-soft);
  }
}

.node-title {
  fill: currentColor;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 13px;
  pointer-events: none;
}

.node-badge {
  fill: rgba(90, 58, 32, 0.66);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 8px;
  pointer-events: none;
}

.active-dot {
  fill: #83b0a9;
  stroke: var(--paper);
  stroke-width: 1;
}

.expand-control {
  cursor: pointer;

  circle {
    fill: var(--paper);
    stroke: var(--ink-soft);
    stroke-width: 1;
  }

  path {
    fill: none;
    stroke: var(--ink-soft);
    stroke-linecap: round;
    stroke-width: 1.2;
  }
}

.focus-control {
  cursor: pointer;

  circle,
  path {
    fill: var(--paper);
    stroke: var(--ink-soft);
    stroke-linecap: round;
    stroke-width: 1;
  }

  .focus-target-inner {
    fill: none;
  }

  path {
    fill: none;
  }

  &:hover .focus-target-outer {
    fill: var(--ink-soft);
  }

  &:hover .focus-target-inner,
  &:hover path {
    stroke: var(--paper);
  }
}

.entity-browser-trigger {
  position: absolute;
  z-index: 12;
  bottom: 17px;
  left: 17px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--ink-soft);
  border-radius: 5px;
  padding: 6px 8px;
  color: var(--paper);
  background: var(--rust);
  box-shadow: 0 4px 14px rgba(90, 58, 32, 0.18);
  cursor: pointer;

  svg {
    width: 20px;
    height: 20px;
    fill: none;
    stroke: currentColor;
    stroke-linejoin: round;
    stroke-width: 1.5;
  }

  span {
    font-size: 10px;
  }

  &.active {
    background: var(--ink-soft);
  }
}

.entity-browser {
  position: absolute;
  z-index: 11;
  top: 14px;
  bottom: 56px;
  left: 14px;
  display: flex;
  width: min(260px, 27vw);
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--ink-soft);
  border-radius: 7px;
  background: rgba(244, 241, 234, 0.96);
  box-shadow: 0 8px 26px rgba(90, 58, 32, 0.2);
  backdrop-filter: blur(4px);
}

.browser-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--line);
  padding: 8px 10px;
  color: var(--ink);
  font-size: 12px;

  button {
    border: 0;
    padding: 0 3px;
    background: transparent;
    font-size: 20px;
    cursor: pointer;
  }
}

.browser-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.entity-item {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 7px;
  border: 1px solid transparent;
  border-radius: 3px;
  padding: 4px 6px;
  color: var(--ink-soft);
  background: transparent;
  font-size: 11px;
  text-align: left;
  cursor: pointer;

  i {
    width: 9px;
    height: 9px;
    flex: 0 0 auto;
    border: 1px solid var(--ink-soft);
    border-radius: 1px;
    background: rgba(106, 74, 42, 0.16);
  }

  &.office i {
    border-color: #55756c;
    border-radius: 50%;
    background: rgba(85, 117, 108, 0.14);
  }

  span {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  small {
    color: var(--teal);
  }

  &:hover,
  &.focused {
    border-color: var(--line);
    background: var(--wash);
  }

  &.focused {
    box-shadow: inset 3px 0 0 var(--ink-soft);
  }

  &.quiet {
    color: rgba(90, 58, 32, 0.46);
  }
}

.list-divider {
  margin: 10px 4px 5px;
  border-top: 1px solid var(--line-light);
  padding-top: 7px;
  color: rgba(90, 58, 32, 0.46);
  font-size: 9px;
  letter-spacing: 0.14em;
}

.canvas-caption {
  position: absolute;
  bottom: 16px;
  left: 108px;
  color: rgba(90, 58, 32, 0.56);
  font-size: 9px;
  letter-spacing: 0.05em;
  pointer-events: none;

  strong {
    color: var(--ink-soft);
    font-size: 11px;
  }
}

.toolbar-legend {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 10px;
  color: rgba(90, 58, 32, 0.62);
  font-size: 9px;
  white-space: nowrap;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.node-sample {
  width: 9px;
  height: 11px;
  border-radius: 2px;
  background: #6d4a2e;

  &.office {
    border-radius: 5px;
    background: #55756c;
  }
}

// 与画布中总线分叉点一致的类型图标样式
.edge-mark-sample {
  display: inline-grid;
  place-items: center;
  width: 14px;
  height: 14px;
  border: 1px solid var(--ink-soft);
  border-radius: 50%;
  color: var(--ink-soft);

  svg {
    width: 9px;
    height: 9px;
  }

  path {
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 1.5;
  }
}

.legend-item.via-staff .edge-mark-sample {
  border-color: #b96f42;
  color: #b96f42;
}

.legend-item.via-alias .edge-mark-sample {
  border-color: #8e8175;
  color: #8e8175;
}

.line-sample {
  width: 22px;
  border-top: 1px solid var(--ink-soft);
}

.line-sample.secondary {
  border-top-color: var(--rust);
  border-top-style: dashed;
}

.canvas-controls {
  position: absolute;
  z-index: 6;
  right: 15px;
  bottom: 15px;
  display: flex;
  flex-direction: column;
  align-items: end;
  gap: 5px;
}

.layout-switch,
.zoom-controls {
  background: rgba(244, 241, 234, 0.9);
  box-shadow: 0 3px 12px rgba(90, 58, 32, 0.12);
}

.zoom-controls button {
  min-width: 28px;
  font-size: 12px;
}

// 证据页停靠在画布右侧，作为侧栏挤压画布而不是覆盖
.evidence-panel {
  flex: 0 0 auto;
  width: min(320px, 31vw);
  overflow-y: auto;
  border-left: 1px solid var(--ink-soft);
  padding: 12px 15px 20px;
  background: rgba(244, 241, 234, 0.97);
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.evidence-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  color: rgba(90, 58, 32, 0.66);
  font-size: 10px;

  button {
    border: 0;
    padding: 0 3px;
    background: transparent;
    font-size: 19px;
    cursor: pointer;
  }
}

.evidence-pair {
  margin: 8px 0 5px;
  color: var(--ink);
  font-size: 14px;
}

.evidence-record + .evidence-record {
  margin-top: 8px;
  border-top: 1px dashed var(--line);
  padding-top: 7px;
}

.evidence-period,
.quiet-text {
  margin: 4px 0;
  color: var(--rust);
  font-size: 10px;
}

.evidence-panel article {
  border-top: 1px solid var(--line-light);
  padding: 8px 0 5px;

  cite {
    display: block;
    color: var(--ink-soft);
    font-size: 10px;
    font-style: normal;
  }

  blockquote {
    margin: 6px 0 0;
    border-left: 2px solid var(--line-light);
    padding-left: 8px;
    font-size: 11px;
    line-height: 1.65;
  }

  p {
    color: rgba(90, 58, 32, 0.65);
    font-size: 10px;
  }
}

.stage-hint {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
  color: rgba(90, 58, 32, 0.54);

  .empty-seal {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    margin: 0 auto;
    border: 1px solid var(--line);
    font-size: 22px;
  }

  p {
    font-size: 12px;
  }
}

@media (max-width: 960px) {
  .toolbar-copy span,
  .ancestor-bar,
  .toolbar-legend {
    display: none;
  }

  .hierarchy-toolbar {
    justify-content: space-between;
  }

  .entity-browser {
    width: min(280px, 58vw);
  }

  .evidence-panel {
    width: min(330px, 62vw);
  }
}
</style>
