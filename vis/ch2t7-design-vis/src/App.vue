<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <span class="brand-mark">WS</span>
        <h1>中国古代职官体系导览 <small>- 宋朝 · 二至七编</small></h1>
      </div>
      <div class="controls" v-if="data">
        <div class="view-switch" role="tablist" aria-label="视图切换">
          <button :class="{ active: viewMode === 'hierarchy' }" @click="viewMode = 'hierarchy'">层级视图</button>
          <button :class="{ active: viewMode === 'composition' }" @click="viewMode = 'composition'">编制视图</button>
        </div>
        <label v-if="viewMode === 'hierarchy'" class="check">
          <input type="checkbox" v-model="showOfficials" />
          显示官职
        </label>
        <span v-if="viewMode === 'hierarchy'" class="sep"></span>
        <button v-if="viewMode === 'hierarchy'" @click="sendExpand('all')">展开全部</button>
        <button v-if="viewMode === 'hierarchy'" @click="sendExpand('collapse')">全部收起</button>
        <label v-if="viewMode === 'hierarchy'" class="level-label">
          展开到第
          <select v-model.number="expandLevel" @change="sendExpand('level')">
            <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
          </select>
          层
        </label>
      </div>
    </header>

    <div class="body-row" v-if="data">
      <NavPanel
        class="nav"
        :roots="rootList"
        :selected-id="selectedId"
        :selected-summary="selectedSummary"
        @locate="locate"
      />
      <main class="canvas-wrap">
        <InstitutionTree
          v-if="viewMode === 'hierarchy'"
          :data="visibleData"
          :show-officials="showOfficials"
          :expand-command="expandCommand"
          :locate-target="locateTarget"
          :selected-id="selectedId"
          :staff-by-org="staffByOrg"
          @select="onSelect"
          @hover="onHover"
        />
        <CompositionView
          v-else
          :data="visibleData"
          :selected-id="selectedId"
          @select="onSelect"
          @hover="onHover"
        />
        <div v-if="hoverInfo" class="hover-card" :style="hoverStyle">
          <div class="hover-title">{{ hoverInfo.entity.title }}</div>
          <div class="hover-type">{{ hoverInfo.entity.type }}</div>
          <div v-if="hoverInfo.dict" class="hover-text">
            <p v-if="hoverInfo.dict.origin"><b>职源与沿革</b>：{{ hoverInfo.dict.origin }}</p>
            <p v-if="hoverInfo.dict.duty"><b>职掌</b>：{{ hoverInfo.dict.duty }}</p>
            <p v-if="!hoverInfo.dict.origin && !hoverInfo.dict.duty">{{ hoverInfo.dict.summary }}</p>
          </div>
          <div v-else class="hover-text dim">无匹配辞典词条</div>
        </div>
      </main>
      <DetailPanel
        v-if="selectedId"
        class="detail"
        :entity-id="selectedId"
        :data="data"
        :selected-year="selectedYear"
        :staff-by-org="staffByOrg"
        :staff-by-official="staffByOfficial"
        @select="onSelect"
        @close="selectedId = null"
      />
    </div>
    <div v-else class="loading">{{ loadError || '数据加载中…' }}</div>

    <SongTimelineBar v-if="data" v-model="selectedYear" class="timeline" />
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import NavPanel from "./components/NavPanel.vue";
import InstitutionTree from "./components/InstitutionTree.vue";
import DetailPanel from "./components/DetailPanel.vue";
import SongTimelineBar from "./components/SongTimelineBar.vue";
import CompositionView from "./components/CompositionView.vue";

const data = ref(null);
const loadError = ref("");
const showOfficials = ref(false);
const viewMode = ref("hierarchy");
const selectedYear = ref(1080);
const selectedId = ref(null);
const hoverInfo = ref(null);
const expandLevel = ref(2);
const expandCommand = ref({ type: "level", level: 2, seq: 0 });
const locateTarget = ref({ id: null, seq: 0 });

fetch("/api/data")
  .then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then((d) => {
    data.value = d;
  })
  .catch((e) => {
    loadError.value = `数据加载失败：${e.message}`;
  });

const entityMap = computed(() => {
  const m = new Map();
  if (data.value) for (const e of data.value.entities) m.set(e.id, e);
  return m;
});

function periodActive(periods) {
  if (!periods || periods.length === 0) return true;
  return periods.some((p) => selectedYear.value >= p.start && selectedYear.value <= p.end);
}

function timepointActive(tp) {
  if (tp.year_start == null || tp.year_end == null) return true;
  return selectedYear.value >= tp.year_start && selectedYear.value <= tp.year_end;
}

// 两张设计画板共享同一时间截面。年代未明的数据保留，明确不属于当前年的数据隐藏。
const visibleData = computed(() => {
  if (!data.value) return null;
  const timepoints = {};
  for (const [entityId, items] of Object.entries(data.value.timepoints)) {
    const visible = items.filter(timepointActive);
    if (visible.length) timepoints[entityId] = visible;
  }
  return {
    ...data.value,
    timepoints,
    hierarchyEdges: data.value.hierarchyEdges.filter((e) => periodActive(e.periods)),
    staffEdges: data.value.staffEdges.filter((e) => periodActive(e.periods)),
  };
});

// 编制隶属：机构 id -> [边]，官职 id -> [边]
const staffByOrg = computed(() => {
  const m = new Map();
  if (!visibleData.value) return m;
  for (const e of visibleData.value.staffEdges) {
    if (!m.has(e.org)) m.set(e.org, []);
    m.get(e.org).push(e);
  }
  return m;
});
const staffByOfficial = computed(() => {
  const m = new Map();
  if (!visibleData.value) return m;
  for (const e of visibleData.value.staffEdges) {
    if (!m.has(e.official)) m.set(e.official, []);
    m.get(e.official).push(e);
  }
  return m;
});

// 根机构分类：按设计稿左栏五类（内廷/中央/路级/州县/军队），依据时间点 attr_category 与题名归类
function classify(title, cats) {
  const s = `${title} ${cats}`;
  if (/内廷|宫廷|宫闱|禁中|内侍|御前|供御|内衣物|殿中省|尚[食药衣舍辇酝]/.test(s)) return "内廷机构";
  if (/军|禁军|统兵|马政|钤辖|殿前司|侍卫/.test(s)) return "军队机构";
  if (/路级|转运|提刑|提举常平|安抚|发运|总领|漕/.test(s)) return "路级机构";
  if (/州县|州府|县|监当|税务|地方|驻外|驻京/.test(s)) return "州县机构";
  return "中央机构";
}

const rootList = computed(() => {
  if (!visibleData.value) return [];
  const childSet = new Set(visibleData.value.hierarchyEdges.map((e) => e.child));
  const participant = new Set();
  for (const e of visibleData.value.hierarchyEdges) {
    participant.add(e.parent);
    participant.add(e.child);
  }
  const roots = [...participant].filter((id) => !childSet.has(id));
  const sizeCache = new Map();
  const descendantCount = (id) => {
    if (sizeCache.has(id)) return sizeCache.get(id);
    sizeCache.set(id, 0); // 防环
    const kids = visibleData.value.hierarchyEdges.filter((e) => e.parent === id).map((e) => e.child);
    let n = kids.length;
    for (const k of kids) n += descendantCount(k);
    sizeCache.set(id, n);
    return n;
  };
  return roots
    .map((id) => {
      const title = entityMap.value.get(id)?.title || `#${id}`;
      const tps = visibleData.value.timepoints[String(id)] || [];
      const cats = tps.map((t) => t.attr_category).join(" ");
      return {
        id,
        title,
        cat: classify(title, cats),
        size: descendantCount(id),
      };
    })
    .sort((a, b) => b.size - a.size || a.title.localeCompare(b.title, "zh"));
});

const selectedSummary = computed(() => {
  if (!selectedId.value || !data.value) return "";
  const ent = entityMap.value.get(selectedId.value);
  if (!ent) return "";
  const dict = data.value.dictionary[ent.title];
  if (dict) return dict.summary;
  const tps = data.value.timepoints[String(ent.id)] || [];
  return tps.length ? `${tps[0].time}：${tps[0].event}` : "";
});

const hoverStyle = computed(() => {
  if (!hoverInfo.value) return {};
  const x = Math.min(hoverInfo.value.x + 16, window.innerWidth - 340);
  const y = Math.min(hoverInfo.value.y + 12, window.innerHeight - 260);
  return { left: `${x}px`, top: `${y}px` };
});

function sendExpand(type) {
  expandCommand.value = { type, level: expandLevel.value, seq: expandCommand.value.seq + 1 };
}

function locate(id) {
  locateTarget.value = { id, seq: locateTarget.value.seq + 1 };
  selectedId.value = id;
}

function onSelect(id) {
  selectedId.value = id;
}

function onHover(info) {
  if (!info) {
    hoverInfo.value = null;
    return;
  }
  const ent = entityMap.value.get(info.id);
  if (!ent) return;
  hoverInfo.value = {
    entity: ent,
    dict: data.value.dictionary[ent.title] || null,
    x: info.x,
    y: info.y,
  };
}
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid var(--line);
  background: rgba(254, 254, 254, 0.5);
  flex: none;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  font-style: italic;
  color: var(--ink);
  letter-spacing: -2px;
}

.brand h1 {
  font-size: 20px;
  margin: 0;
  letter-spacing: 3px;
  color: var(--ink);
}

.brand small {
  font-size: 13px;
  color: var(--ink-2);
  letter-spacing: 1px;
}

.controls {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--ink-2);
}

.controls button {
  background: rgba(254, 254, 254, 0.6);
  border: 1px solid var(--olive);
  color: var(--ink-2);
  padding: 4px 10px;
  cursor: pointer;
  font-size: 13px;
}

.controls button:hover {
  border-color: var(--ink-2);
  color: var(--ink);
}

.view-switch {
  display: flex;
  gap: 4px;
  margin-right: 6px;
}

.view-switch button {
  min-width: 82px;
  border-color: var(--line);
  background: rgba(254, 254, 254, 0.45);
}

.view-switch button.active {
  color: var(--ink);
  border-color: var(--ink-2);
  background: rgba(165, 166, 141, 0.32);
  font-weight: 700;
}

.sep {
  width: 1px;
  height: 18px;
  background: var(--line);
}

.body-row {
  display: flex;
  flex: 1;
  min-height: 0;
}

.nav {
  flex: none;
  width: 250px;
  border-right: 1px solid var(--line);
  background: rgba(254, 254, 254, 0.45);
  overflow: hidden;
  display: flex;
}

.canvas-wrap {
  position: relative;
  flex: 1;
  min-width: 0;
}

.detail {
  flex: none;
  width: 330px;
  border-left: 1px solid var(--line);
  overflow-y: auto;
}

.timeline {
  flex: none;
  height: clamp(160px, 20vh, 220px);
  border-top: 1px solid var(--line);
}

.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-2);
  letter-spacing: 4px;
}

.hover-card {
  position: fixed;
  z-index: 50;
  width: 330px;
  background: rgba(254, 254, 254, 0.94);
  border: 1px solid var(--ink-2);
  box-shadow: 3px 3px 10px rgba(53, 23, 4, 0.25);
  padding: 10px 12px;
  pointer-events: none;
  color: var(--ink);
}

.hover-title {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 2px;
}

.hover-type {
  font-size: 11px;
  color: var(--ink-2);
  margin-bottom: 6px;
  border-bottom: 1px dotted var(--line);
  padding-bottom: 4px;
}

.hover-text {
  font-size: 12px;
  line-height: 1.7;
  max-height: 180px;
  overflow: hidden;
  color: var(--ink-2);
}

.hover-text p {
  margin: 4px 0;
}

.dim {
  color: var(--ink-2);
  opacity: 0.6;
}
</style>
