<template>
  <g v-if="cols.length" class="officials" :transform="`translate(${nodeW / 2 + 12}, ${-nodeH / 2})`">
    <!-- 虚线容器（对应设计稿官职展开面板） -->
    <rect
      class="panel"
      x="0"
      y="0"
      :width="panelW"
      :height="PANEL_H"
      rx="1"
      @click.stop
      @mouseenter.stop
    />
    <g
      v-for="(c, i) in cols"
      :key="c.edgeId"
      class="official"
      :transform="`translate(${PAD + i * PITCH}, ${PAD})`"
      @click.stop="emit('select-official', c.official)"
      @mouseenter.stop
    >
      <!-- 顶签：官职类分类四色 -->
      <rect class="otab" :x="-OTAB / 2" :y="-OTAB + 1" :width="OTAB" :height="OTAB" :fill="kindColor(c.kind)" />
      <!-- 官职条 -->
      <rect class="obody" :x="-COL_W / 2" y="0" :width="COL_W" :height="COL_H" />
      <!-- 竖排官名 -->
      <text class="oname" :y="OTAB + 10">{{ short(c.title) }}</text>
      <!-- 员额 -->
      <text v-if="c.quota" class="oquota" :y="COL_H - 4">{{ c.quota }}人</text>
      <title>{{ c.title }}{{ c.quota ? `（员额 ${c.quota}）` : "" }}</title>
    </g>
    <text v-if="overflow > 0" class="omore" :x="panelW - PAD" :y="PANEL_H - 6">+{{ overflow }}</text>
  </g>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  edges: { type: Array, required: true }, // 该机构的编制隶属边
  officialInfo: { type: Map, required: true }, // officialId -> {title, tier, kind}
  nodeW: { type: Number, required: true },
  nodeH: { type: Number, required: true },
});
const emit = defineEmits(["select-official"]);

const COL_W = 15.4;
const COL_H = 101.6;
const PITCH = 21.1;
const PAD = 8;
const OTAB = 6;
const MAX_SHOW = 8;

// 设计稿图例「官职类分类」四色
const KIND_COLORS = {
  差遣官: "#a5a68d",
  职事官: "#918069",
  阶官: "#866d6d",
  吏: "#c3c3c3",
};
function kindColor(kind) {
  return KIND_COLORS[kind] || KIND_COLORS["职事官"];
}

const cols = computed(() => {
  const items = [];
  for (const e of props.edges) {
    const info = props.officialInfo.get(e.official);
    if (!info) continue;
    items.push({
      edgeId: e.id,
      official: e.official,
      title: info.title,
      tier: info.tier,
      kind: info.kind,
      quota: e.staff_quota,
    });
  }
  // 按品阶档位自左而右（一品在左）
  items.sort((a, b) => a.tier - b.tier || a.title.localeCompare(b.title, "zh"));
  return items.slice(0, MAX_SHOW);
});

const overflow = computed(() => Math.max(0, props.edges.length - MAX_SHOW));
const panelW = computed(() => cols.value.length * PITCH + PAD * 2 - (PITCH - COL_W));
const PANEL_H = COL_H + PAD * 2;

function short(t) {
  return t.length > 7 ? t.slice(0, 7) : t;
}
</script>

<style scoped>
.panel {
  fill: rgba(254, 254, 254, 0.78);
  stroke: var(--ink-2);
  stroke-width: 0.75px;
  stroke-opacity: 0.6;
  stroke-dasharray: 3 2;
}

.official {
  cursor: pointer;
}

.otab {
  fill-opacity: 0.85;
  stroke: var(--ink-2);
  stroke-width: 0.6px;
}

.obody {
  fill: rgba(254, 254, 254, 0.6);
  stroke: var(--olive);
  stroke-width: 0.75px;
}

.official:hover .obody {
  fill: rgba(254, 254, 254, 0.95);
  stroke: var(--ink-2);
}

.oname {
  writing-mode: vertical-rl;
  letter-spacing: 1px;
  font-size: 11px;
  fill: var(--ink);
  text-anchor: middle;
  pointer-events: none;
}

.oquota {
  font-size: 8.5px;
  fill: var(--ink-2);
  text-anchor: middle;
  pointer-events: none;
}

.omore {
  font-size: 9px;
  fill: var(--ink-2);
  text-anchor: end;
}
</style>
