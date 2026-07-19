<template>
  <div ref="rootRef" class="hierarchy-view">
    <div class="hierarchy-toolbar">
      <span class="toolbar-stats">
        {{ listedEntities.length }} 个{{ structureScope === "current" ? "所选时段" : "历时" }}有层级实体
        · {{ isolatedEntities.length }} 个无层级实体
      </span>
      <span class="scope-switch" aria-label="层级结构时间范围">
        <button
          type="button"
          :class="{ active: structureScope === 'current' }"
          @click="structureScope = 'current'"
        >
          所选时段结构
        </button>
        <button
          type="button"
          :class="{ active: structureScope === 'history' }"
          @click="structureScope = 'history'"
        >
          历时全貌
        </button>
      </span>
      <span class="toolbar-legend" aria-hidden="true">
        <span class="legend-node org">机构</span>
        <span class="legend-node office">官职</span>
        <span class="legend-edge via-sup">
          <i class="edge-line"></i>
          <svg viewBox="0 0 16 16"><path :d="VIA_ICONS.sup" /></svg>上下级机构
        </span>
        <span class="legend-edge via-staff">
          <i class="edge-line"></i>
          <svg viewBox="0 0 16 16"><path :d="VIA_ICONS.staff" /></svg>编制隶属
        </span>
        <span class="legend-edge via-alias">
          <i class="edge-line"></i>
          <svg viewBox="0 0 16 16"><path :d="VIA_ICONS.alias" /></svg>统称与实例
        </span>
        <span class="active-legend">● 所选时段有记录</span>
      </span>
    </div>
    <div class="hierarchy-body">
      <aside class="entity-list" :class="{ collapsed: listCollapsed }">
        <button
          type="button"
          class="list-toggle"
          :title="listCollapsed ? '展开词条栏' : '收起词条栏'"
          @click="listCollapsed = !listCollapsed"
        >
          {{ listCollapsed ? "›" : "‹" }}
        </button>
        <div class="list-scroll">
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
            :data-entity-id="item.id"
            @click="onItemClick(item)"
          >
            <span class="item-shape" aria-hidden="true"></span>
            <span class="item-title">{{ item.title }}</span>
            <span v-if="activeEntities.has(item.id)" class="item-dot" title="所选时段有记录">●</span>
          </button>
          <div v-if="isolatedEntities.length" class="list-divider">
            {{ structureScope === "current" ? "所选时段无层级关系" : "历时无层级关系" }}
          </div>
          <button
            v-for="item in isolatedEntities"
            :key="item.id"
            type="button"
            class="entity-item quiet"
            :class="{
              focused: item.id === focusId,
              office: item.type === '官职',
              'linked-hover': item.id === hoveredEntityId,
            }"
            :data-entity-id="item.id"
            @click="onItemClick(item)"
          >
            <span class="item-shape" aria-hidden="true"></span>
            <span class="item-title">{{ item.title }}</span>
            <span v-if="activeEntities.has(item.id)" class="item-dot" title="所选时段有记录">●</span>
          </button>
        </div>
        <div class="rail-legend" aria-hidden="true">
          <span><i class="item-shape"></i>机构</span>
          <span><i class="item-shape office"></i>官职</span>
          <span><i class="item-dot">●</i>所选时段有记录</span>
        </div>
      </aside>

      <div class="hierarchy-stage">
        <div v-if="focusId == null" class="stage-hint">
          点击左侧词条，移至中央展开其层级结构；<br />再点击中央词条查看详情。
        </div>
        <template v-else>
          <div class="stage-main">
            <nav v-if="ancestorTrail.length" class="ancestor-bar" aria-label="上级链">
              <template v-for="(ancestor, index) in ancestorTrail" :key="ancestor.id">
                <span v-if="index" class="ancestor-sep">›</span>
                <button
                  type="button"
                  class="ancestor-pill"
                  :class="{ office: ancestor.entType === '官职' }"
                  :title="ancestor.title"
                  @click="focusEntity(ancestor.id)"
                >
                  {{ ancestor.title }}
                </button>
              </template>
              <span class="ancestor-sep">›</span>
              <span class="ancestor-current">{{ focusTitle }}</span>
            </nav>

            <Transition name="tree-fade" mode="out-in">
              <div :key="`${focusId}|${listCollapsed}`" class="tree-scroll">
                <div
                  v-for="(row, index) in treeRows"
                  :key="index"
                  class="tree-row"
                  :data-entity-id="typeof row.id === 'number' ? row.id : null"
                  :class="{
                    focus: row.id === focusId,
                    selected: row.id === selectedEntityId,
                    'linked-hover': row.id === hoveredEntityId,
                    overflow: row.overflow,
                  }"
                >
                  <span v-if="row.depth" class="row-guides" aria-hidden="true">
                    <i v-for="(cont, guideIndex) in row.guides" :key="guideIndex" :class="{ cont }"></i>
                    <i class="stub" :class="{ last: row.isLast }"></i>
                  </span>
                  <button
                    v-if="row.hasChildren"
                    type="button"
                    class="row-caret"
                    :class="{ open: expanded.has(row.id) }"
                    :aria-label="expanded.has(row.id) ? '收起' : '展开'"
                    @click.stop="toggle(row.id)"
                  ></button>
                  <span v-else class="row-caret none"></span>
                  <button
                    type="button"
                    class="row-node"
                    :class="[row.entType === '官职' ? 'office' : 'org', `via-${viaClass(row)}`]"
                    :disabled="row.overflow"
                    :title="rowTooltip(row)"
                    @click="onRowClick(row)"
                  >
                    <span
                      v-if="viaClass(row) !== 'none'"
                      class="via-icon"
                      :class="`via-${viaClass(row)}`"
                      aria-hidden="true"
                    >
                      <svg viewBox="0 0 16 16"><path :d="VIA_ICONS[viaClass(row)]" /></svg>
                    </span>
                    <span v-if="isActiveId(row.id)" class="node-dot" title="所选时段有记录">●</span>
                    <span class="node-title">{{ row.title }}</span>
                    <small v-if="rowBadge(row)" class="node-badge">{{ rowBadge(row) }}</small>
                  </button>
                  <button
                    v-if="row.hasChildren && row.id !== focusId"
                    type="button"
                    class="row-focus"
                    title="将该节点设为层级树中心"
                    @click.stop="focusEntity(row.id)"
                  >
                    以此为中心
                  </button>
                  <button
                    v-if="row.edge"
                    type="button"
                    class="evidence-btn"
                    :class="{ open: evidenceCard?.key === relationKey(row.edge) }"
                    title="查看关系证据"
                    @click.stop="toggleRowEvidence(row)"
                  >
                    证
                  </button>
                </div>
              </div>
            </Transition>
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
              <article v-for="(citation, i) in relation.citations" :key="i">
                <cite>{{ citation.citation }}</cite>
                <blockquote>{{ citation.quotation }}</blockquote>
                <p v-if="citation.note">{{ citation.note }}</p>
              </article>
              <p v-if="!relation.citations.length" class="quiet-text">该期关系暂无引文记录。</p>
            </div>
          </aside>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
// 官制层级结构浏览（左列表 + 缩进树）：
// - “所选时段结构”按底部时间范围过滤关系，“历时全貌”展示全部时期关系；
// - 左侧词条列表按与当前时间区间的匹配程度从上到下排列（可收起）：
//   所选时段有记录（青绿圆点）优先，其余有层级关系的实体按记录数随后，
//   无层级关系的实体列在最末分隔线之下；
// - 点击左侧词条或通过搜索定位：该词条成为焦点，下级树以缩进树整棵展开
//   （默认全展开，点 ▸/▾ 收起/展开单层）；子节点按关系类型归组排序
//   （上下级机构 → 编制隶属 → 统称与实例），父子之间用直角肘线连接，不存在交叉线；
// - 主父链以顶部面包屑条展示，点击可回到任一上级；
// - 点击任意树节点只打开/关闭右侧详情；有下级的节点另设“以此为中心”按钮，
//   避免同一种节点点击因是否有下级而产生两种不同结果；
// - 节点形状区分类型（机构方角、官职圆角）；关系类型用「颜色 + 线型 + 图标」
//   三通道区分（上下级机构=深褐实线+建筑、编制隶属=橙色虚线+人形、
//   统称与实例=灰褐点线+交叠方框），图例见顶部工具栏；
// - 行内「证」按钮在右侧栏显示证明该关系的引文；
// - 所选时段模式只保留区间内有记录依据的层级边；历时模式保留全部边并标注纪年。
import { computed, nextTick, reactive, ref, watch } from "vue";
import { buildEntityGraph } from "@/utils/hierarchy";

const props = defineProps({
  dataset: { type: Object, required: true },
  selectedEntityId: { type: Number, default: null },
  hoveredEntityId: { type: Number, default: null },
  activeEntities: { type: Set, default: () => new Set() },
  range: { type: Array, default: null },
});
const emit = defineEmits(["select-entity"]);

const PRIMARY_VIA = { 上下级机构: 0, 编制隶属: 1, 统称与实例: 2 };
const MAX_CHILDREN = 50; // 单节点最多同时展开的下级数（当前数据最多 37，超出才显示“另有 N 个下级”）

// 关系类型图标（16×16 简笔，stroke=currentColor）：建筑=上下级机构、人形=编制隶属、交叠方框=统称与实例、箭头=前后演变
const VIA_ICONS = {
  sup: "M2 13h12M3.5 13V5.5L8 2l4.5 3.5V13M6 13V8.5h1.6V13M8.4 13V8.5H10V13",
  staff: "M8 7.2a2.6 2.6 0 1 0 0-5.2 2.6 2.6 0 0 0 0 5.2zM3 13.5c.6-3 2.6-4.3 5-4.3s4.4 1.3 5 4.3",
  alias: "M2.5 2.5h7v7h-7zM6.5 6.5h7v7h-7z",
  evolve: "M2 8h9.5M8.5 4.5L12.5 8l-4 3.5",
};

const structureScope = ref("current");

// 所选时段模式按底部时间范围过滤；历时模式取消关系时间过滤。
const graph = computed(() =>
  buildEntityGraph(props.dataset, structureScope.value === "current" ? props.range : null)
);

// —— 左侧列表：按与当前区间的匹配程度排序 ——
const linkedIds = computed(
  () => new Set([...graph.value.childrenOf.keys(), ...graph.value.parentRelsOf.keys()])
);

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

// 每个实体的额外上级名称（主父以外），以节点内小字提示
const extraParents = computed(() => {
  const map = new Map();
  for (const [childId, list] of graph.value.parentRelsOf) {
    if (list.length > 1) {
      map.set(
        childId,
        list.slice(1).map((r) => graph.value.entityById.get(r.entityId)?.title ?? `#${r.entityId}`)
      );
    }
  }
  return map;
});

// —— 焦点与展开状态 ——
const focusId = ref(null);
const expanded = reactive(new Set()); // 已展开的下级节点（实体 id）
const listCollapsed = ref(false); // 左侧词条栏收起状态
const rootRef = ref(null);

// —— 关系证据栏：点击行内「证」按钮，在舞台右侧固定栏显示证明该关系的引文 ——
const evidenceCard = ref(null); // { key, relations }
const relationById = computed(() => new Map(props.dataset.relations.map((r) => [r.id, r])));

function relationKey(edge) {
  return (edge.relationIds || [edge.relationId]).join(",");
}

function toggleRowEvidence(row) {
  const key = relationKey(row.edge);
  if (evidenceCard.value?.key === key) {
    evidenceCard.value = null;
    return;
  }
  const relations = (row.edge.relationIds || [row.edge.relationId])
    .map((id) => relationById.value.get(id))
    .filter(Boolean)
    .sort((a, b) => (a.yearStart ?? Infinity) - (b.yearStart ?? Infinity) || a.id - b.id);
  if (!relations.length) return;
  evidenceCard.value = { key, relations };
}

function onItemClick(item) {
  if (item.id === focusId.value) toggleSelect(item.id);
  else focusEntity(item.id);
}

// 再点击焦点词条：打开详情；已打开则关闭
function toggleSelect(id) {
  emit("select-entity", props.selectedEntityId === id ? null : id);
}

function focusEntity(id) {
  if (id == null) return;
  focusId.value = id;
  evidenceCard.value = null;
  expandFocusedTree();
  // 树重新聚焦时，详情同步到新中心，避免中央结构和右侧内容指向不同实体。
  if (props.selectedEntityId !== id) emit("select-entity", id);
}

function expandFocusedTree() {
  expanded.clear();
  // 整棵下级树全展开（沿 childrenOf 遍历，带环保护）
  const stack = [focusId.value];
  while (stack.length) {
    const current = stack.pop();
    if (expanded.has(current)) continue;
    expanded.add(current);
    for (const child of graph.value.childrenOf.get(current) || []) {
      stack.push(child.entityId);
    }
  }
}

// 树节点点击只选中看详情，不触发 selectedEntityId 的外部定位逻辑。
let suppressNextFocus = false;

function onRowClick(row) {
  if (row.overflow) return;
  suppressNextFocus = true;
  toggleSelect(row.id);
}

function toggle(id) {
  evidenceCard.value = null; // 展开/收起后结构变化，关闭证据栏
  if (expanded.has(id)) expanded.delete(id);
  else expanded.add(id);
}

// —— 主父链面包屑 ——
const ancestorTrail = computed(() => {
  if (focusId.value == null) return [];
  return graph.value.ancestorChain(focusId.value).map((aid) => {
    const ent = graph.value.entityById.get(aid);
    return { id: aid, title: ent?.title ?? `#${aid}`, entType: ent?.type ?? "" };
  });
});

const focusTitle = computed(
  () => graph.value.entityById.get(focusId.value)?.title ?? ""
);

// —— 缩进树行：焦点 + 下级树（默认全展开）先建数据树，再深度优先拍平成行 ——
const treeRows = computed(() => {
  if (focusId.value == null) return [];
  const g = graph.value;

  function buildDown(nodeId, path) {
    const ent = g.entityById.get(nodeId);
    const kids = [...(g.childrenOf.get(nodeId) || [])]
      .filter((k) => !path.has(k.entityId))
      .sort(
        (a, b) =>
          PRIMARY_VIA[a.via] - PRIMARY_VIA[b.via] ||
          (g.entityById.get(b.entityId)?.eventCount ?? 0) -
            (g.entityById.get(a.entityId)?.eventCount ?? 0)
      );
    const node = {
      id: nodeId,
      title: ent?.title ?? `#${nodeId}`,
      entType: ent?.type ?? "",
      extra: extraParents.value.get(nodeId) || null,
      hasChildren: kids.length > 0,
      children: [],
    };
    if (kids.length && expanded.has(nodeId)) {
      const nextPath = new Set(path).add(nodeId);
      node.children = kids
        .slice(0, MAX_CHILDREN)
        .map((k) => ({ ...buildDown(k.entityId, nextPath), edge: k }));
      if (kids.length > MAX_CHILDREN) {
        node.children.push({
          id: `more-${nodeId}`,
          title: `…另有 ${kids.length - MAX_CHILDREN} 个下级`,
          overflow: true,
        });
      }
    }
    return node;
  }

  const rows = [];

  // guides[d] = 第 d 层祖先在该行之后还有后继兄弟（画竖向延续线）
  function flatten(node, depth, guides, isLast) {
    rows.push({ ...node, depth, guides, isLast });
    if (node.children?.length) {
      const kids = node.children;
      kids.forEach((child, index) =>
        flatten(child, depth + 1, [...guides, index < kids.length - 1], index === kids.length - 1)
      );
    }
  }
  flatten(buildDown(focusId.value, new Set()), 0, [], true);
  return rows;
});

// —— 行展示辅助 ——
function isActiveId(id) {
  return typeof id === "number" && props.activeEntities.has(id);
}

function viaClass(row) {
  const via = row.edge?.via;
  if (via === "上下级机构") return "sup";
  if (via === "编制隶属") return "staff";
  if (via === "统称与实例") return "alias";
  return "none";
}

function rowBadge(row) {
  const bits = [];
  if (structureScope.value === "history" && row.edge) {
    bits.push(edgePeriodLabel(row.edge));
  }
  if (row.edge?.via === "编制隶属" && row.edge?.quota != null) {
    bits.push(`${row.edge.quota}${row.edge.staffType || "员"}`);
  }
  if (row.extra?.length) bits.push(`另有${row.extra.length}个上级`);
  return bits.join(" · ");
}

function periodText(start, end) {
  return start === end ? `${start}年` : `${start}—${end}年`;
}

function edgePeriodLabel(edge) {
  const periods = edge.periods || [];
  if (!periods.length) return "时间未明";
  const suffix = edge.hasUndated ? "、另有时间未明记录" : "";
  if (periods.length <= 2) {
    return `${periods.map((p) => periodText(p.start, p.end)).join("、")}${suffix}`;
  }
  return `${periodText(periods[0].start, periods[0].end)}等${periods.length}期${suffix}`;
}

function relationPeriodLabel(relation) {
  if (relation.yearStart == null) return "时间未明";
  return periodText(relation.yearStart, relation.yearEnd ?? relation.yearStart);
}

function evidencePeriodLabel(relations) {
  const labels = [...new Set(relations.map(relationPeriodLabel))];
  if (labels.length <= 2) return labels.join("、");
  return `${labels[0]}等${labels.length}期记录`;
}

function rowTooltip(row) {
  if (row.overflow) return "下级过多，未全部展开";
  const ent = graph.value.entityById.get(row.id);
  if (!ent) return row.title;
  const bits = [`${ent.title}（${ent.type}）`, `共${ent.eventCount}条记录`];
  if (ent.yearMin != null) bits.push(`${ent.yearMin}—${ent.yearMax}年有记录`);
  if (row.edge) bits.push(`关系：${row.edge.via}`);
  if (row.extra?.length) bits.push(`其他上级：${row.extra.join("、")}`);
  if (row.id === focusId.value) bits.push("点击查看详情");
  return bits.join(" · ");
}

watch(
  () => props.selectedEntityId,
  (id) => {
    if (suppressNextFocus) {
      suppressNextFocus = false;
      return;
    }
    if (id != null && id !== focusId.value) focusEntity(id);
  }
);

watch(structureScope, () => {
  evidenceCard.value = null;
  if (focusId.value != null) expandFocusedTree();
});

watch(
  () => props.hoveredEntityId,
  async (id) => {
    if (id == null) return;
    await nextTick();
    const selector = `[data-entity-id="${id}"]`;
    rootRef.value?.querySelector(`.tree-row${selector}`)?.scrollIntoView({
      behavior: "smooth",
      block: "center",
      inline: "nearest",
    });
    rootRef.value?.querySelector(`.entity-item${selector}`)?.scrollIntoView({
      behavior: "smooth",
      block: "center",
      inline: "nearest",
    });
  }
);

// 深链：?view=hierarchy&entity=实体ID
if (props.selectedEntityId != null) focusEntity(props.selectedEntityId);
</script>

<style scoped lang="scss">
.hierarchy-view {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  padding-right: 10px;
}

.hierarchy-toolbar {
  display: flex;
  align-items: center;
  height: 34px;
  border-bottom: 1px solid var(--line-light);
  padding: 0 14px 7px;
  color: rgba(90, 58, 32, 0.56);
  font-size: 11px;
  letter-spacing: 0.14em;

  .scope-switch {
    display: inline-flex;
    flex: 0 0 auto;
    margin-left: 14px;
    border: 1px solid var(--line);
    border-radius: 3px;
    overflow: hidden;
    letter-spacing: 0;

    button {
      border: 0;
      border-right: 1px solid var(--line-light);
      padding: 2px 7px;
      color: rgba(90, 58, 32, 0.58);
      background: transparent;
      font-family: "FZQINGKBYSJF", serif;
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

  .toolbar-legend {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-left: 18px;
    letter-spacing: 0;
  }

  .legend-node {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border: 1px solid var(--ink-soft);
    padding: 0 5px;

    svg {
      width: 11px;
      height: 11px;
      fill: none;
      stroke: currentColor;
      stroke-linecap: round;
      stroke-linejoin: round;
      stroke-width: 1.5;
    }

    &.org {
      background: rgba(106, 74, 42, 0.14);
      border-radius: 3px;
    }

    &.office {
      border-color: var(--line);
      background: rgba(106, 74, 42, 0.03);
      border-radius: 999px;
    }
  }

  // 关系类型图例：线型样本 + 图标（不用节点外框，避免与实体形状混淆）
  .legend-edge {
    display: inline-flex;
    align-items: center;
    gap: 4px;

    svg {
      width: 11px;
      height: 11px;
      fill: none;
      stroke: currentColor;
      stroke-linecap: round;
      stroke-linejoin: round;
      stroke-width: 1.5;
    }

    .edge-line {
      width: 16px;
      border-top: 2px solid currentColor;
    }

    &.via-sup {
      color: var(--ink-soft);
    }

    &.via-staff {
      color: #cf8a52;

      .edge-line {
        border-top-style: dashed;
      }
    }

    &.via-alias {
      color: var(--line);

      .edge-line {
        border-top-style: dotted;
      }
    }
  }

  .active-legend {
    color: var(--teal);
  }
}

.hierarchy-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.entity-list {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 210px;
  flex-shrink: 0;
  min-height: 0;
  border-right: 1px solid var(--line-light);
  transition: width 160ms ease;

  &.collapsed {
    width: 15px;

    .list-scroll,
    .rail-legend {
      display: none;
    }
  }

  // 分界线上的收起手柄：平时半透明，悬停才显现
  .list-toggle {
    position: absolute;
    z-index: 3;
    top: 50%;
    right: 0;
    width: 15px;
    height: 44px;
    transform: translateY(-50%);
    border: 1px solid var(--line-light);
    border-right: 0;
    border-radius: 4px 0 0 4px;
    padding: 0;
    color: rgba(90, 58, 32, 0.5);
    background: var(--paper);
    font-size: 10px;
    line-height: 1;
    cursor: pointer;
    opacity: 0.45;

    &:hover {
      color: var(--ink);
      opacity: 1;
    }
  }

  .list-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 6px 8px 24px;
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
    padding: 3px 6px;
    margin-bottom: 1px;
    color: var(--ink-soft);
    background: transparent;
    font-family: "FZQINGKBYSJF", serif;
    font-size: 12px;
    text-align: left;
    cursor: pointer;

    &:hover {
      border-color: var(--line);
      background: var(--wash);
    }

    &.focused {
      border-color: var(--ink-soft);
      background: rgba(106, 74, 42, 0.1);
    }

    &.linked-hover {
      border-color: var(--rust);
      background: rgba(180, 112, 71, 0.18);
      box-shadow: inset 3px 0 0 var(--rust);
      color: var(--ink);
    }

    &.quiet:not(.linked-hover) {
      color: rgba(90, 58, 32, 0.45);
    }

    .item-shape {
      width: 9px;
      height: 9px;
      flex-shrink: 0;
      border: 1px solid var(--ink-soft);
      border-radius: 1px;
      background: rgba(106, 74, 42, 0.14);
    }

    &.office .item-shape {
      border-color: var(--line);
      border-radius: 50%;
      background: rgba(106, 74, 42, 0.03);
    }

    .item-title {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .item-dot {
      color: var(--teal);
      font-size: 9px;
    }
  }

  .list-divider {
    margin: 10px 4px 6px;
    border-top: 1px solid var(--line-light);
    padding-top: 8px;
    color: rgba(90, 58, 32, 0.45);
    font-size: 10px;
    letter-spacing: 0.2em;
  }

  .rail-legend {
    display: flex;
    flex: 0 0 auto;
    gap: 12px;
    border-top: 1px solid var(--line-light);
    padding: 7px 8px;
    color: rgba(90, 58, 32, 0.6);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 10px;

    span {
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }

    .item-shape {
      width: 9px;
      height: 9px;
      border: 1px solid var(--ink-soft);
      border-radius: 1px;
      background: rgba(106, 74, 42, 0.14);

      &.office {
        border-color: var(--line);
        border-radius: 50%;
        background: rgba(106, 74, 42, 0.03);
      }
    }

    .item-dot {
      color: var(--teal);
      font-size: 9px;
    }
  }
}

.hierarchy-stage {
  position: relative;
  display: flex;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  user-select: none;
}

.stage-main {
  position: relative;
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.stage-hint {
  position: absolute;
  top: 38%;
  right: 0;
  left: 0;
  color: rgba(90, 58, 32, 0.5);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 13px;
  line-height: 2;
  text-align: center;
  pointer-events: none;
}

// —— 主父链面包屑 ——
.ancestor-bar {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 5px;
  overflow-x: auto;
  border-bottom: 1px solid var(--line-light);
  padding: 7px 10px;
  scrollbar-width: none;

  .ancestor-sep {
    flex: 0 0 auto;
    color: var(--line);
    font-size: 11px;
  }

  .ancestor-pill {
    flex: 0 0 auto;
    border: 1px solid var(--ink-soft);
    border-radius: 3px;
    padding: 2px 8px;
    color: var(--ink-soft);
    background: rgba(106, 74, 42, 0.14);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
    cursor: pointer;

    &.office {
      border-color: var(--line);
      border-radius: 999px;
      background: rgba(106, 74, 42, 0.03);
    }

    &:hover {
      background: var(--wash);
    }
  }

  .ancestor-current {
    flex: 0 0 auto;
    padding: 2px 4px;
    color: var(--ink);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 12px;
  }
}

// —— 缩进树 ——
.tree-scroll {
  flex: 1;
  overflow: auto;
  padding: 8px 18px 40px 6px;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.tree-row {
  display: flex;
  align-items: center;
  height: 34px;
  white-space: nowrap;
}

.tree-fade-enter-active,
.tree-fade-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}

.tree-fade-enter-from {
  opacity: 0;
  transform: translateX(-14px);
}

.tree-fade-leave-to {
  opacity: 0;
}

// 直角肘线：每个深度层级一格，祖先有后继兄弟则画竖向延续线
.row-guides {
  display: flex;
  flex: 0 0 auto;
  align-self: stretch;

  i {
    position: relative;
    width: 64px;
  }

  i.cont::before {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 31px;
    border-left: 1px solid var(--line-light);
    content: "";
  }

  i.stub::before {
    position: absolute;
    top: 0;
    left: 31px;
    height: 50%;
    border-left: 1px solid var(--line);
    content: "";
  }

  i.stub::after {
    position: absolute;
    top: 50%;
    left: 31px;
    width: 27px;
    border-top: 1px solid var(--line);
    content: "";
  }

  // 非末位兄弟：竖线贯通整行
  i.stub:not(.last)::before {
    height: 100%;
  }
}

.row-caret {
  position: relative;
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  border: 0;
  padding: 0;
  color: var(--ink-soft);
  background: transparent;
  cursor: pointer;

  &::before {
    position: absolute;
    inset: 0;
    font-size: 11px;
    line-height: 18px;
    text-align: center;
    content: "▸";
  }

  &.open::before {
    content: "▾";
  }

  &.none {
    cursor: default;
  }
}

// 节点内关系类型图标（与图例同款）
.via-icon {
  display: inline-flex;
  flex: 0 0 auto;
  align-self: center;

  svg {
    width: 12px;
    height: 12px;
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 1.5;
  }

  &.via-sup {
    color: var(--ink-soft);
  }

  &.via-staff {
    color: #cf8a52;
  }

  &.via-alias {
    color: var(--line);
  }
}

.row-node {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: baseline;
  gap: 7px;
  border: 1px solid var(--ink-soft);
  border-left-width: 3px;
  border-radius: 3px;
  padding: 2px 9px;
  color: var(--ink-soft);
  background: rgba(106, 74, 42, 0.14);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 13px;
  cursor: pointer;

  &.office {
    border-color: var(--line);
    border-radius: 999px;
    background: rgba(106, 74, 42, 0.03);
  }

  // 关系类型左边条：实线深褐=上下级机构、虚线橙=编制隶属、点线灰褐=统称与实例
  &.via-sup {
    border-left-color: var(--ink-soft);
  }

  &.via-staff {
    border-left-color: #cf8a52;
    border-left-style: dashed;
  }

  &.via-alias {
    border-left-color: var(--line);
    border-left-style: dotted;
  }

  &:hover:not(:disabled) {
    background: var(--wash);
  }

  &:disabled {
    border-style: dashed;
    color: rgba(90, 58, 32, 0.55);
    background: transparent;
    cursor: default;
    font-style: italic;
  }

  .node-dot {
    align-self: center;
    color: var(--teal);
    font-size: 9px;
  }

  .node-badge {
    color: rgba(90, 58, 32, 0.6);
    font-size: 10px;
  }
}

// 焦点行与详情选中行
.tree-row.focus .row-node {
  border-color: var(--ink-soft);
  color: var(--paper);
  background: var(--ink-soft);

  .node-badge,
  .node-dot,
  .via-icon {
    color: rgba(244, 241, 234, 0.8);
  }

  .via-icon svg {
    stroke: rgba(244, 241, 234, 0.85);
  }
}

.tree-row.selected:not(.focus) .row-node {
  box-shadow: inset 0 0 0 1px var(--ink-soft);
}

.tree-row.linked-hover .row-node {
  outline: 2px solid var(--rust);
  outline-offset: 2px;
  background: rgba(180, 112, 71, 0.2);
  box-shadow: 0 0 12px rgba(180, 112, 71, 0.32);
}

.tree-row.focus.linked-hover .row-node {
  background: var(--ink-soft);
}

.row-focus {
  flex: 0 0 auto;
  margin-left: 5px;
  border: 0;
  border-bottom: 1px solid transparent;
  padding: 1px 2px;
  color: rgba(90, 58, 32, 0.48);
  background: transparent;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
  cursor: pointer;

  &:hover {
    border-bottom-color: var(--ink-soft);
    color: var(--ink);
  }
}

// 行内独立「证」按钮（节点右侧，查看关系证据，与跳转热区分开）
.evidence-btn {
  display: inline-grid;
  flex: 0 0 auto;
  place-items: center;
  align-self: center;
  width: 18px;
  height: 18px;
  margin-left: 4px;
  border: 1px solid var(--line);
  border-radius: 50%;
  padding: 0;
  color: rgba(90, 58, 32, 0.6);
  background: var(--paper);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
  cursor: pointer;

  &:hover {
    border-color: var(--ink-soft);
    color: var(--ink);
  }

  &.open {
    border-color: var(--ink-soft);
    color: var(--paper);
    background: var(--ink-soft);
  }
}

// 右侧关系证据栏（固定栏，不遮挡树行）
.evidence-panel {
  width: min(340px, 36%);
  flex: 0 0 auto;
  overflow-y: auto;
  border-left: 1px solid var(--ink-soft);
  padding: 12px 16px 24px;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;

  .evidence-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    color: rgba(90, 58, 32, 0.65);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
    letter-spacing: 0.06em;

    button {
      border: 0;
      padding: 0 3px;
      color: inherit;
      background: transparent;
      cursor: pointer;
      font-size: 18px;
      line-height: 1;
    }
  }

  .evidence-pair {
    margin: 8px 0 4px;
    color: var(--ink);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 14px;
    line-height: 1.5;
  }

  .evidence-record + .evidence-record {
    margin-top: 8px;
    border-top: 1px dashed var(--line);
    padding-top: 5px;
  }

  .evidence-period {
    margin: 0;
    color: var(--rust);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
  }

  article {
    border-top: 1px solid var(--line-light);
    padding: 8px 0 6px;
  }

  cite {
    display: block;
    color: var(--ink-soft);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
    font-style: normal;
  }

  blockquote {
    margin: 6px 0 0;
    border-left: 2px solid var(--line-light);
    padding-left: 8px;
    color: rgba(90, 58, 32, 0.88);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 12px;
    line-height: 1.7;
  }

  article p {
    margin: 5px 0 0;
    color: rgba(90, 58, 32, 0.65);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
  }
}
</style>
