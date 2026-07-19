<template>
  <div class="app-shell backgrounded">
    <header class="site-header">
      <svg class="lab-logo" viewBox="0 0 44 44" aria-hidden="true">
        <rect x="3" y="3" width="38" height="38" rx="6" fill="#724a2b" />
        <rect x="6.5" y="6.5" width="31" height="31" rx="4" fill="none" stroke="#f4f1ea" stroke-width="1.2" opacity="0.65" />
        <text x="22" y="30.5" text-anchor="middle" font-size="23" fill="#f4f1ea" font-family="FZQINGKBYSJF, serif">宋</text>
      </svg>
      <h1>宋代官制可视化</h1>

      <div class="search-wrap">
        <label for="entity-search">查找机构或官职</label>
        <div class="search-box">
          <img src="./assets/magnifier.svg" alt="" />
          <input
            id="entity-search"
            v-model.trim="query"
            type="search"
            placeholder="如：都督府、经略安抚使司"
            autocomplete="off"
          />
        </div>
        <div v-if="query && searchResults.length" class="search-results">
          <button
            v-for="item in searchResults"
            :key="`${item.entityId}-${item.yearStart ?? 'entity'}`"
            type="button"
            @click="locateSearchResult(item)"
          >
            <span>{{ item.title }}</span>
            <small>{{ item.entityType }} · {{ item.rawTime }}</small>
          </button>
        </div>
      </div>
    </header>

    <main class="main-stage" v-if="dataset">
      <section class="stage-heading">
        <div class="period-heading">
          <span class="section-kicker">当前历史区间</span>
          <div class="period-line">
            <button type="button" class="year-step" @click="shiftRange(-1)" aria-label="上一年">‹</button>
            <h2>{{ rangeTitle }}</h2>
            <button type="button" class="year-step" @click="shiftRange(1)" aria-label="下一年">›</button>
          </div>
          <p :title="reignTitle">{{ reignTitle }}</p>
        </div>

        <div class="stage-summary">
          <span v-for="item in summaryItems" :key="item.label">
            <strong>{{ item.value }}</strong> {{ item.label }}
          </span>
        </div>

        <div class="filters" aria-label="视图与筛选">
          <button
            type="button"
            :class="{ active: viewMode === 'events' }"
            @click="viewMode = 'events'"
          >
            时序事件
          </button>
          <button
            type="button"
            :class="{ active: viewMode === 'hierarchy' }"
            @click="viewMode = 'hierarchy'"
          >
            层级结构
          </button>
          <button
            type="button"
            :class="{ active: viewMode === 'timeline' }"
            @click="viewMode = 'timeline'"
          >
            年表
          </button>
          <template v-if="viewMode === 'events'">
            <span class="filter-divider"></span>
            <button
              v-for="item in entityFilters"
              :key="item.value"
              type="button"
              :class="{ active: entityFilter === item.value }"
              @click="entityFilter = item.value"
            >
              {{ item.label }}
            </button>
            <span class="filter-divider"></span>
            <select v-model="eventFilter" aria-label="事件类型">
              <option value="all">全部事件</option>
              <option v-for="(label, key) in eventTypeLabels" :key="key" :value="key">
                {{ label }}
              </option>
            </select>
          </template>
        </div>
      </section>

      <section
        class="exploration-area"
        :class="{
          'events-layout': viewMode === 'events',
          'with-detail': viewMode === 'events' && centeredEvent && detailOpen,
        }"
      >
        <template v-if="viewMode === 'events'">
          <div class="entry-rail">
            <div class="rail-caption" aria-hidden="true">
              <span>词条记录</span>
              <span>按时间匹配排序</span>
            </div>

            <div v-if="rankedEvents.length" ref="railStreamRef" class="rail-stream">
              <button
                v-for="item in rankedEvents"
                :key="item.event.id"
                :data-event-id="item.event.id"
                type="button"
                class="entry-card"
                :class="[
                  `event-${item.event.eventType}`,
                  { 'in-range': item.inRange, selected: centeredEvent?.id === item.event.id },
                ]"
                @click="handleEntryClick(item.event, $event)"
              >
                <span class="entry-date">
                  {{ item.event.rawTime }}
                  <small v-if="!item.inRange" class="entry-gap">{{ item.gapText }}</small>
                </span>
                <span class="entry-title-line">
                  <strong :title="item.event.title">{{ item.event.title }}</strong>
                  <em>{{ item.event.entityType }}</em>
                </span>
                <span class="entry-snippet">{{ item.event.event }}</span>
              </button>
            </div>

            <div v-else class="empty-state">
              <span class="empty-seal">无</span>
              <p>没有符合当前筛选条件的精确纪年记录。</p>
            </div>

            <div class="rail-legend" aria-hidden="true">
              <span><i class="legend-marker mk-established"></i>设置/恢复</span>
              <span><i class="legend-marker mk-abolished"></i>罢废</span>
              <span><i class="legend-marker mk-renamed"></i>改称/合并</span>
              <span><i class="legend-marker mk-recorded"></i>记载</span>
            </div>
          </div>

          <div class="center-stage">
            <article
              v-if="centeredEvent"
              ref="centerCardRef"
              :class="['center-card', `event-${centeredEvent.eventType}`]"
              @click="openDetail"
            >
              <div class="center-card-head">
                <span>{{ centeredEvent.entityType }} · {{ centeredEvent.category || "未分类" }}</span>
                <button type="button" aria-label="收起词条" @click.stop="closeCentered">×</button>
              </div>

              <h3>{{ centeredEvent.title }}</h3>
              <p class="center-time">{{ centeredEvent.rawTime }} · 公元{{ centeredEvent.yearStart }}年</p>
              <p class="center-event-text">{{ centeredEvent.event }}</p>

              <dl v-if="centeredEvent.officerType || centeredEvent.grade" class="attributes">
                <template v-if="centeredEvent.officerType">
                  <dt>官职性质</dt><dd>{{ centeredEvent.officerType }}</dd>
                </template>
                <template v-if="centeredEvent.grade">
                  <dt>品级</dt><dd>{{ centeredEvent.grade }}</dd>
                </template>
              </dl>

              <span class="center-foot">
                {{ eventTypeLabels[centeredEvent.eventType] }}
                <template v-if="centeredEvent.relationCount"> · {{ centeredEvent.relationCount }} 条关系</template>
                · {{ centeredEvent.citations.length }} 条引文
              </span>
              <span v-if="!detailOpen" class="center-hint">再次点击卡片查看详情</span>
            </article>

            <div v-else class="stage-placeholder">
              <span class="empty-seal">选</span>
              <p>点击左侧词条，移至此处展开阅读，再次点击查看详情。</p>
            </div>
          </div>

          <EventDetailPanel
            v-if="centeredEvent && detailOpen"
            :event="centeredEvent"
            :relations="selectedRelations"
            @close="detailOpen = false"
            @follow-relation="followRelation"
          />
        </template>

        <template v-else-if="viewMode === 'timeline'">
          <EntityTimeline
            :dataset="dataset"
            :entity-id="timelineEntityId"
            :selected-event="timelineEvent"
            :range="selectedRange"
            @select-entity="onTimelineEntity"
            @select-event="onTimelineEvent"
          />

          <EventDetailPanel
            v-if="timelineEvent"
            :event="timelineEvent"
            :relations="timelineRelations"
            @close="timelineEvent = null"
            @follow-relation="followRelation"
          />
        </template>

        <template v-else>
          <HierarchyView
            :dataset="dataset"
            :selected-entity-id="selectedEntityId"
            :hovered-entity-id="hoveredHierarchyEntityId"
            :active-entities="activeEntities"
            :range="selectedRange"
            @select-entity="(id) => (selectedEntityId = id)"
          />

          <aside v-if="selectedEntity" class="detail-panel">
            <div class="detail-head">
              <span>{{ selectedEntity.type }} · {{ entityAttrs.category || "未分类" }}</span>
              <button type="button" @click="selectedEntityId = null" aria-label="关闭详情">×</button>
            </div>

            <nav v-if="entityBreadcrumb.length" class="breadcrumb" aria-label="上级路径">
              <button
                v-for="node in entityBreadcrumb"
                :key="node.id"
                type="button"
                @click="selectedEntityId = node.id"
              >
                {{ node.title }}
              </button>
            </nav>

            <h3>{{ selectedEntity.title }}</h3>
            <p class="detail-time">
              <template v-if="selectedEntity.yearMin != null">
                公元{{ selectedEntity.yearMin }}—{{ selectedEntity.yearMax }}年 ·
              </template>
              {{ selectedEntity.eventCount }} 条记录
            </p>

            <dl v-if="entityAttrs.officerType || entityAttrs.grade" class="attributes">
              <template v-if="entityAttrs.officerType">
                <dt>官职性质</dt><dd>{{ entityAttrs.officerType }}</dd>
              </template>
              <template v-if="entityAttrs.grade">
                <dt>品级</dt><dd>{{ entityAttrs.grade }}</dd>
              </template>
            </dl>

            <section class="detail-section">
              <div class="section-title">
                <h4>层级关系</h4>
                <span>{{ entityRelations.length }}</span>
              </div>
              <template v-if="entityRelations.length">
                <div v-for="group in groupedEntityRelations" :key="group.type" class="relation-group">
                  <div class="relation-group-title">
                    <span>{{ group.type }}</span>
                    <span>{{ group.items.length }}</span>
                  </div>
                  <div class="relation-list">
                    <button
                      v-for="relation in group.items"
                      :key="relation.id"
                      type="button"
                      @mouseenter="hoveredHierarchyEntityId = relation.otherEntityId"
                      @mouseleave="hoveredHierarchyEntityId = null"
                      @click="followRelation(relation)"
                    >
                      <span class="relation-path">
                        <em class="dir-tag" :class="`via-${relationViaClass(relation.type)}`">
                          {{ relationDirectionLabel(relation) }}
                        </em>
                        {{ relation.otherTitle }}
                      </span>
                      <small v-if="relation.staffQuota">
                        {{ relation.staffQuota }}{{ relation.staffType || "员" }}
                      </small>
                    </button>
                  </div>
                </div>
              </template>
              <p v-else class="quiet-text">这个实体没有关联关系。</p>
            </section>

            <section class="detail-section evidence-section">
              <div class="section-title">
                <h4>纪事与证据</h4>
                <span>{{ entityEvents.length }}</span>
              </div>
              <article v-for="event in entityEvents" :key="event.id">
                <cite>{{ event.rawTime }}</cite>
                <blockquote>{{ event.event }}</blockquote>
                <p v-for="(citation, index) in event.citations" :key="index" class="event-citation">
                  {{ citation.citation }}
                </p>
              </article>
            </section>
          </aside>
        </template>
      </section>
    </main>

    <div v-else class="loading-state">正在展开宋代官制时间……</div>

    <SongTimeline
      v-if="dataset"
      class="song-timeline"
      :years="dataset.years"
      :range="selectedRange"
      @change-range="setRange"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import EntityTimeline from "./components/EntityTimeline.vue";
import EventDetailPanel from "./components/EventDetailPanel.vue";
import HierarchyView from "./components/HierarchyView.vue";
import SongTimeline from "./components/SongTimeline.vue";
import { buildEntityGraph, groupRelationsByType, relationDirectionLabel, relationViaClass } from "./utils/hierarchy";

const dataset = ref(null);
const query = ref("");
const selectedRange = ref([1132, 1132]);
const centeredEvent = ref(null);
const detailOpen = ref(false);
const centerCardRef = ref(null);
const railStreamRef = ref(null);
const selectedEntityId = ref(null);
const hoveredHierarchyEntityId = ref(null);
const timelineEntityId = ref(null);
const timelineEvent = ref(null);
const viewMode = ref("events");
const entityFilter = ref("all");
const eventFilter = ref("all");

const entityFilters = [
  { value: "all", label: "全部" },
  { value: "机构", label: "机构" },
  { value: "官职", label: "官职" },
];

const eventTypeLabels = {
  established: "设置",
  abolished: "罢废",
  restored: "恢复",
  renamed: "改称",
  merged: "合并",
  recorded: "记载",
};

onMounted(async () => {
  const response = await fetch("./data/song-bureaucracy.json");
  dataset.value = await response.json();
  // 支持深链：?view=hierarchy|timeline&entity=实体ID
  const params = new URLSearchParams(window.location.search);
  const view = params.get("view");
  if (view === "hierarchy" || view === "timeline") viewMode.value = view;
  const entityId = Number(params.get("entity"));
  if (entityId) {
    if (view === "timeline") timelineEntityId.value = entityId;
    else selectedEntityId.value = entityId;
  }
  scrollRailToRange();
});

const exactEvents = computed(() => {
  if (!dataset.value) return [];
  const [start, end] = selectedRange.value;
  return dataset.value.events.filter((event) => {
    if (event.timeType !== "exact" || event.yearStart == null) return false;
    return event.yearStart >= start && event.yearStart <= end;
  });
});

const visibleEvents = computed(() => {
  return exactEvents.value
    .filter((event) => entityFilter.value === "all" || event.entityType === entityFilter.value)
    .filter((event) => eventFilter.value === "all" || event.eventType === eventFilter.value)
    .sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0) || a.id - b.id);
});

// 左栏词条：所有精确纪年事件按与当前区间的时间距离排序，区间内的排在最前
const filteredExactEvents = computed(() => {
  if (!dataset.value) return [];
  return dataset.value.events
    .filter((event) => event.timeType === "exact" && event.yearStart != null)
    .filter((event) => entityFilter.value === "all" || event.entityType === entityFilter.value)
    .filter((event) => eventFilter.value === "all" || event.eventType === eventFilter.value);
});

const rankedEvents = computed(() => {
  const [start, end] = selectedRange.value;
  return filteredExactEvents.value
    .map((event) => {
      const inRange = event.yearStart >= start && event.yearStart <= end;
      const distance = inRange
        ? 0
        : Math.min(Math.abs(event.yearStart - start), Math.abs(event.yearStart - end));
      return {
        event,
        inRange,
        distance,
        gapText: inRange ? "" : event.yearStart < start ? `早 ${distance} 年` : `晚 ${distance} 年`,
      };
    })
    .sort(
      (a, b) =>
        a.distance - b.distance ||
        (a.event.sortOrder || 0) - (b.event.sortOrder || 0) ||
        a.event.id - b.event.id
    );
});

const institutionCount = computed(() => visibleEvents.value.filter((item) => item.entityType === "机构").length);
const officeCount = computed(() => visibleEvents.value.filter((item) => item.entityType === "官职").length);

const entityGraph = computed(() => (dataset.value ? buildEntityGraph(dataset.value) : null));

// 当前时间区间内有精确纪年记录的实体，用于层级树的活跃高亮
const activeEntities = computed(() => {
  const active = new Set();
  for (const event of exactEvents.value) {
    active.add(event.entityId);
  }
  return active;
});

const summaryItems = computed(() => {
  if (!dataset.value) return [];
  if (viewMode.value === "hierarchy") {
    return [
      { value: dataset.value.entities.filter((item) => item.type === "机构").length, label: "机构" },
      { value: dataset.value.entities.filter((item) => item.type === "官职").length, label: "官职" },
      { value: activeEntities.value.size, label: "当前区间活跃" },
    ];
  }
  if (viewMode.value === "timeline") {
    return [
      { value: dataset.value.entities.filter((item) => item.type === "机构").length, label: "机构" },
      { value: dataset.value.entities.filter((item) => item.type === "官职").length, label: "官职" },
      { value: dataset.value.events.length, label: "条官制记录" },
    ];
  }
  return [
    { value: visibleEvents.value.length, label: "条官制记录" },
    { value: institutionCount.value, label: "机构" },
    { value: officeCount.value, label: "官职" },
  ];
});

const rangeTitle = computed(() => {
  const [start, end] = selectedRange.value;
  return start === end ? `公元 ${start} 年` : `公元 ${start}—${end} 年`;
});

const reignTitle = computed(() => {
  if (!dataset.value) return "";
  const [start, end] = selectedRange.value;
  const phases = [];
  if (start <= 1127) phases.push("北宋");
  if (end >= 1127) phases.push("南宋");
  const eras = dataset.value.eras
    .filter((era) => era.end >= start && era.start <= end)
    .map((era) => era.name);
  return `${[...new Set(phases)].join(" / ")} · ${eras.join("、") || "未定年号"}`;
});

const searchResults = computed(() => {
  if (!dataset.value || !query.value) return [];
  const keyword = query.value.toLowerCase();
  if (viewMode.value === "hierarchy" || viewMode.value === "timeline") {
    const matches = [];
    for (const entity of dataset.value.entities) {
      if (!entity.title.toLowerCase().includes(keyword)) continue;
      matches.push({
        entityId: entity.id,
        title: entity.title,
        entityType: entity.type,
        rawTime:
          entity.yearMin != null
            ? `公元${entity.yearMin}—${entity.yearMax}年`
            : "无精确纪年",
      });
      if (matches.length === 8) break;
    }
    return matches;
  }
  const seen = new Set();
  const matches = [];
  for (const event of dataset.value.events) {
    if (!event.title.toLowerCase().includes(keyword)) continue;
    if (seen.has(event.entityId)) continue;
    seen.add(event.entityId);
    matches.push(event);
    if (matches.length === 8) break;
  }
  return matches;
});

const relationIndex = computed(() => {
  const index = new Map();
  if (!dataset.value) return index;
  for (const relation of dataset.value.relations) {
    if (!index.has(relation.subjectId)) index.set(relation.subjectId, []);
    if (!index.has(relation.objectId)) index.set(relation.objectId, []);
    index.get(relation.subjectId).push({
      ...relation,
      direction: "out",
      otherId: relation.objectId,
      otherTitle: relation.objectTitle,
    });
    index.get(relation.objectId).push({
      ...relation,
      direction: "in",
      otherId: relation.subjectId,
      otherTitle: relation.subjectTitle,
    });
  }
  return index;
});

const eventIndex = computed(() => {
  const index = new Map();
  if (dataset.value) dataset.value.events.forEach((event) => index.set(event.id, event));
  return index;
});

const selectedRelations = computed(() => {
  if (!centeredEvent.value) return [];
  return relationIndex.value.get(centeredEvent.value.id) || [];
});

const timelineRelations = computed(() => {
  if (!timelineEvent.value) return [];
  return relationIndex.value.get(timelineEvent.value.id) || [];
});

// —— 层级模式下的实体卡片 ——

const selectedEntity = computed(() => {
  if (selectedEntityId.value == null || !entityGraph.value) return null;
  return entityGraph.value.entityById.get(selectedEntityId.value) || null;
});

const entityBreadcrumb = computed(() => {
  if (!selectedEntity.value || !entityGraph.value) return [];
  return entityGraph.value
    .ancestorChain(selectedEntity.value.id)
    .map((id) => entityGraph.value.entityById.get(id))
    .filter(Boolean);
});

const entityRelations = computed(() => {
  if (!selectedEntity.value || !dataset.value) return [];
  const id = selectedEntity.value.id;
  const list = [];
  for (const relation of dataset.value.relations) {
    if (relation.subjectEntityId === id) {
      list.push({
        ...relation,
        direction: "out",
        otherEntityId: relation.objectEntityId,
        otherTitle: relation.objectTitle,
      });
    } else if (relation.objectEntityId === id) {
      list.push({
        ...relation,
        direction: "in",
        otherEntityId: relation.subjectEntityId,
        otherTitle: relation.subjectTitle,
      });
    }
  }
  return list;
});

const groupedEntityRelations = computed(() => groupRelationsByType(entityRelations.value));

const entityEvents = computed(() => {
  if (!selectedEntity.value || !dataset.value) return [];
  return dataset.value.events
    .filter((event) => event.entityId === selectedEntity.value.id)
    .sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0) || a.id - b.id);
});

const entityAttrs = computed(() => {
  const attrs = { category: null, officerType: null, grade: null };
  for (const event of entityEvents.value) {
    attrs.category = attrs.category ?? event.category;
    attrs.officerType = attrs.officerType ?? event.officerType;
    attrs.grade = attrs.grade ?? event.grade;
  }
  return attrs;
});

watch(rankedEvents, (items) => {
  if (centeredEvent.value && !items.some((item) => item.event.id === centeredEvent.value.id)) {
    closeCentered();
  }
});

watch(viewMode, (mode) => {
  query.value = "";
  hoveredHierarchyEntityId.value = null;
  if (mode !== "events") closeCentered();
  if (mode !== "hierarchy") selectedEntityId.value = null;
  if (mode !== "timeline") timelineEvent.value = null;
});

function onTimelineEntity(id) {
  timelineEntityId.value = id;
  timelineEvent.value = null;
}

function onTimelineEvent(event) {
  const eventRange = rangeForEvent(event);
  if (eventRange) setRange(eventRange);
  timelineEvent.value = timelineEvent.value?.id === event.id ? null : event;
}

function rangeForEvent(event) {
  if (event?.yearStart == null) return null;
  const rawEnd = event.yearEnd ?? event.yearStart;
  if (rawEnd < 960 || event.yearStart > 1279) return null;
  const start = Math.max(960, Math.min(1279, event.yearStart));
  const end = Math.max(start, Math.min(1279, rawEnd));
  return [start, end];
}

function setRange(range) {
  selectedRange.value = range;
  scrollRailToRange();
}

function shiftRange(offset) {
  const width = selectedRange.value[1] - selectedRange.value[0];
  let start = Math.max(960, Math.min(1279 - width, selectedRange.value[0] + offset));
  setRange([start, start + width]);
}

// 第一次点击：词条卡片从左侧渐进移动到中央展开；再次点击：打开详情
async function handleEntryClick(event, mouseEvent) {
  if (centeredEvent.value?.id === event.id) {
    detailOpen.value = true;
    return;
  }
  const sourceRect = mouseEvent.currentTarget?.getBoundingClientRect();
  centeredEvent.value = event;
  await nextTick();
  flyCardFrom(sourceRect);
}

function flyCardFrom(sourceRect) {
  const card = centerCardRef.value;
  if (!card || !sourceRect) return;
  const target = card.getBoundingClientRect();
  const dx = sourceRect.left + sourceRect.width / 2 - (target.left + target.width / 2);
  const dy = sourceRect.top + sourceRect.height / 2 - (target.top + target.height / 2);
  const sx = sourceRect.width / target.width;
  const sy = sourceRect.height / target.height;
  card.animate(
    [
      { transform: `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`, opacity: 0.3 },
      { transform: "translate(0px, 0px) scale(1, 1)", opacity: 1 },
    ],
    { duration: 460, easing: "cubic-bezier(0.22, 0.9, 0.26, 1)" }
  );
}

function openDetail() {
  detailOpen.value = true;
}

function closeCentered() {
  centeredEvent.value = null;
  detailOpen.value = false;
}

function scrollRailToRange() {
  nextTick(() => {
    const first = railStreamRef.value?.querySelector(".entry-card.in-range");
    first?.scrollIntoView({ block: "center", behavior: "smooth" });
  });
}

function scrollRailToEvent(id) {
  nextTick(() => {
    const element = railStreamRef.value?.querySelector(`[data-event-id="${id}"]`);
    element?.scrollIntoView({ block: "center", behavior: "smooth" });
  });
}

function locateSearchResult(item) {
  query.value = "";
  if (viewMode.value === "hierarchy") {
    selectedEntityId.value = item.entityId;
    return;
  }
  if (viewMode.value === "timeline") {
    onTimelineEntity(item.entityId);
    return;
  }
  if (item.yearStart != null) selectedRange.value = [item.yearStart, item.yearStart];
  centeredEvent.value = item;
  detailOpen.value = true;
  scrollRailToEvent(item.id);
}

function followRelation(relation) {
  hoveredHierarchyEntityId.value = null;
  if (viewMode.value === "hierarchy") {
    selectedEntityId.value = relation.otherEntityId;
    return;
  }
  if (viewMode.value === "timeline") {
    // 沿关系跳到另一实体的时间节点（前后演变可顺藤摸瓜）
    const target = eventIndex.value.get(relation.otherId);
    if (!target) return;
    if (target.entityId !== timelineEntityId.value) onTimelineEntity(target.entityId);
    const targetRange = rangeForEvent(target);
    if (targetRange) setRange(targetRange);
    timelineEvent.value = target;
    return;
  }
  const event = eventIndex.value.get(relation.otherId);
  if (!event) return;
  if (event.yearStart != null) selectedRange.value = [event.yearStart, event.yearStart];
  centeredEvent.value = event;
  detailOpen.value = true;
  scrollRailToEvent(event.id);
}
</script>

<style>
:root {
  --ink: #5a3a20;
  --ink-soft: #724a2b;
  --line: #ad9278;
  --line-light: rgba(114, 74, 43, 0.24);
  --paper: #f4f1ea;
  --wash: rgba(174, 142, 113, 0.15);
  --teal: #6f9690;
  --rust: #b47047;
}

/* 事件类型图例标记（全局共享：时序事件视图、年表视图） */
.legend-marker {
  display: inline-block;
  width: 9px;
  height: 9px;
  border: 1.5px solid var(--ink-soft);
  border-radius: 50%;
  background: var(--paper);
}

.legend-marker.mk-established,
.legend-marker.mk-restored {
  background: var(--teal);
}

.legend-marker.mk-abolished {
  border-radius: 0;
  background: var(--rust);
  transform: rotate(45deg) scale(0.75);
}

.legend-marker.mk-renamed,
.legend-marker.mk-merged {
  border-radius: 0;
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  height: 100%;
  margin: 0;
}

body {
  overflow: hidden;
  color: var(--ink);
  background: #f4f3ef;
  font-family: "FZQINGKBYSJF", serif;
}

button,
input,
select {
  font: inherit;
}

button {
  color: inherit;
}

.backgrounded {
  background-image: url("./assets/background.png");
  background-attachment: fixed;
}

.app-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: 8.3vh 75.7vh 16vh;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.site-header {
  position: relative;
  display: flex;
  align-items: center;
  color: var(--ink-soft);
}

.site-header::after {
  position: absolute;
  right: 1.8vw;
  bottom: 0;
  left: 1.8vw;
  border-bottom: 0.3vh solid var(--ink-soft);
  content: "";
}

.lab-logo {
  display: inline-block;
  width: 34px;
  height: 34px;
  margin-left: 2vw;
}

.site-header h1 {
  margin: 0;
  margin-left: 1vh;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 4vh;
  font-weight: 400;
}

.search-wrap {
  position: relative;
  width: min(360px, 28vw);
  margin-right: 4vh;
  margin-left: auto;
  font-family: "FZQINGKBYSJF", serif;
}

.search-wrap label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 0.1vh solid var(--ink-soft);
  padding: 8px 4px;
}

.search-box img {
  width: 17px;
  opacity: 0.72;
}

.search-box input {
  width: 100%;
  border: 0;
  outline: 0;
  color: var(--ink);
  background: transparent;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 2vh;
}

.search-results {
  position: absolute;
  z-index: 20;
  top: 44px;
  right: 0;
  width: 100%;
  border: 1px solid var(--line);
  background-image: url("./assets/background.png");
}

.search-results button {
  display: flex;
  flex-direction: column;
  width: 100%;
  border: 0;
  border-bottom: 1px solid var(--line-light);
  padding: 9px 12px;
  text-align: left;
  background: transparent;
  cursor: pointer;
}

.search-results button:hover {
  background: var(--wash);
}

.search-results small {
  margin-top: 3px;
  color: rgba(90, 58, 32, 0.65);
}

.main-stage {
  display: grid;
  grid-template-rows: 5.6vh minmax(0, 1fr);
  min-width: 0;
  min-height: 0;
  padding: 0 1.8vw;
}

.stage-heading {
  display: grid;
  grid-template-columns: minmax(280px, 360px) max-content minmax(0, 1fr);
  align-items: center;
  gap: 18px;
  border-bottom: 0.1vh solid var(--line);
}

.section-kicker {
  display: none;
}

.period-line {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 5px;
}

.period-line h2 {
  min-width: 166px;
  margin: 0;
  font-size: 19px;
  font-weight: 400;
  letter-spacing: 0.04em;
  text-align: center;
}

.period-heading {
  display: flex;
  align-items: center;
  min-width: 0;
}

.period-heading p {
  overflow: hidden;
  min-width: 0;
  margin: 0 0 0 10px;
  border-left: 1px solid var(--line-light);
  padding-left: 10px;
  color: rgba(90, 58, 32, 0.7);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.year-step {
  width: 22px;
  height: 22px;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  font-size: 19px;
  line-height: 17px;
}

.year-step:hover {
  background: var(--wash);
}

.stage-summary {
  display: flex;
  align-items: center;
  color: rgba(90, 58, 32, 0.72);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
  white-space: nowrap;
}

.stage-summary span {
  display: flex;
  align-items: baseline;
  gap: 4px;
  border-left: 1px solid var(--line-light);
  padding: 0 11px;
}

.stage-summary span:first-child {
  border-left: 0;
  padding-left: 0;
}

.stage-summary strong {
  color: var(--ink);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 17px;
  font-weight: 400;
}

.filters {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  font-family: "FZQINGKBYSJF", serif;
}

.filters button,
.filters select {
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 4px 11px;
  color: var(--ink-soft);
  background: transparent;
  cursor: pointer;
}

.filters button:hover,
.filters select:hover {
  background: var(--wash);
}

.filters button.active {
  color: var(--paper);
  background: var(--ink-soft);
}

.filters select {
  border-color: var(--line-light);
  outline: none;
}

.filter-divider {
  width: 1px;
  height: 20px;
  margin: 0 6px;
  background: var(--line);
}

.exploration-area {
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.exploration-area.events-layout {
  display: grid;
  grid-template-columns: 310px minmax(0, 1fr);
}

.exploration-area.events-layout.with-detail {
  grid-template-columns: 310px minmax(0, 1fr) auto;
}

.entry-rail {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  border-right: 1px solid var(--line-light);
}

.rail-caption {
  display: flex;
  flex: 0 0 auto;
  justify-content: space-between;
  align-items: end;
  height: 34px;
  padding: 0 8px 7px 4px;
  border-bottom: 1px solid var(--line-light);
  color: rgba(90, 58, 32, 0.56);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
  letter-spacing: 0.14em;
}

.rail-stream {
  flex: 1;
  overflow-y: auto;
  padding: 4px 6px 34px 0;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.entry-card {
  position: relative;
  display: block;
  width: 100%;
  border: 0;
  border-bottom: 1px solid var(--line-light);
  padding: 8px 4px 8px 18px;
  text-align: left;
  background: transparent;
  cursor: pointer;
}

.entry-card::before {
  position: absolute;
  top: 14px;
  left: 3px;
  width: 9px;
  height: 9px;
  border: 1.5px solid var(--ink-soft);
  border-radius: 50%;
  background: var(--paper);
  content: "";
}

.entry-card.event-established::before,
.entry-card.event-restored::before {
  background: var(--teal);
}

.entry-card.event-abolished::before {
  border-radius: 0;
  transform: rotate(45deg) scale(0.75);
  background: var(--rust);
}

.entry-card.event-renamed::before,
.entry-card.event-merged::before {
  border-radius: 0;
}

.entry-card:not(.in-range) {
  opacity: 0.42;
}

.entry-card:hover,
.entry-card.selected {
  background: linear-gradient(90deg, rgba(174, 142, 113, 0.18), transparent);
  opacity: 1;
}

.entry-date {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  color: var(--ink-soft);
  font-size: 11px;
}

.entry-gap {
  flex: 0 0 auto;
  color: rgba(90, 58, 32, 0.5);
  font-size: 10px;
}

.entry-title-line {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 2px;
}

.entry-title-line strong {
  flex: 0 1 auto;
  min-width: 0;
  overflow: hidden;
  font-size: 15px;
  font-weight: 400;
  letter-spacing: 0.04em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.entry-title-line em {
  flex: 0 0 auto;
  border: 1px solid var(--line);
  padding: 0 3px;
  color: rgba(90, 58, 32, 0.62);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
  font-style: normal;
}

.entry-snippet {
  display: block;
  overflow: hidden;
  margin-top: 2px;
  color: rgba(90, 58, 32, 0.72);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.entry-rail .empty-state {
  flex: 1;
  height: auto;
}

.center-stage {
  display: grid;
  place-items: center;
  place-items: safe center;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.center-card {
  width: min(560px, 94%);
  max-height: 100%;
  overflow-y: auto;
  border: 1px solid var(--line);
  border-top: 3px solid var(--ink-soft);
  padding: 18px 26px 16px;
  background: var(--paper);
  box-shadow: 0 12px 36px rgba(90, 58, 32, 0.18);
  cursor: pointer;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.center-card.event-established,
.center-card.event-restored {
  border-top-color: var(--teal);
}

.center-card.event-abolished {
  border-top-color: var(--rust);
}

.center-card.event-renamed,
.center-card.event-merged {
  border-top-color: var(--line);
}

.rail-legend {
  display: flex;
  flex: 0 0 auto;
  flex-wrap: wrap;
  gap: 4px 12px;
  border-top: 1px solid var(--line-light);
  padding: 7px 8px 7px 4px;
  color: rgba(90, 58, 32, 0.6);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
}

.rail-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.center-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: rgba(90, 58, 32, 0.65);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.center-card-head button {
  border: 0;
  padding: 0 4px;
  color: inherit;
  background: transparent;
  cursor: pointer;
  font-size: 24px;
}

.center-card h3 {
  margin: 10px 0 4px;
  font-size: 30px;
  font-weight: 400;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.center-time {
  margin: 0;
  color: var(--ink-soft);
  font-size: 13px;
}

.center-event-text {
  margin: 15px 0;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 15px;
  line-height: 1.8;
}

.center-card .attributes {
  margin-bottom: 6px;
}

.center-foot {
  display: block;
  margin-top: 10px;
  border-top: 1px solid var(--line-light);
  padding-top: 9px;
  color: rgba(90, 58, 32, 0.6);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 12px;
}

.center-hint {
  display: block;
  margin-top: 7px;
  color: rgba(90, 58, 32, 0.45);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
  letter-spacing: 0.12em;
}

.stage-placeholder {
  text-align: center;
  color: rgba(90, 58, 32, 0.55);
}

.stage-placeholder .empty-seal {
  margin: 0 auto;
}

.stage-placeholder p {
  font-family: "FZQINGKBYSJF", serif;
  font-size: 13px;
  line-height: 1.6;
}

.detail-panel {
  width: min(390px, 32vw);
  overflow-y: auto;
  border-left: 1px solid var(--ink-soft);
  padding: 18px 22px 32px;
  background: transparent;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.detail-head,
.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: rgba(90, 58, 32, 0.65);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.detail-head button {
  border: 0;
  padding: 0 4px;
  background: transparent;
  cursor: pointer;
  font-size: 24px;
}

.detail-panel h3 {
  margin: 12px 0 4px;
  font-size: 25px;
  font-weight: 400;
  line-height: 1.25;
}

.detail-time {
  margin: 0;
  color: var(--ink-soft);
  font-size: 13px;
}

.detail-event {
  margin: 17px 0;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 14px;
  line-height: 1.75;
}

.attributes {
  display: grid;
  grid-template-columns: 66px 1fr;
  gap: 6px 10px;
  border-top: 1px solid var(--line-light);
  border-bottom: 1px solid var(--line-light);
  padding: 10px 0;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 12px;
}

.attributes dt {
  color: rgba(90, 58, 32, 0.6);
}

.attributes dd {
  margin: 0;
}

.detail-section {
  margin-top: 22px;
}

.section-title {
  border-bottom: 1px solid var(--line);
  padding-bottom: 6px;
}

.section-title h4 {
  margin: 0;
  color: var(--ink);
  font-size: 14px;
  font-weight: 400;
}

.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
}

.breadcrumb button {
  border: 0;
  border-bottom: 1px solid var(--line);
  padding: 1px 2px;
  color: var(--ink-soft);
  background: transparent;
  cursor: pointer;
  font-size: 11px;
}

.breadcrumb button:hover {
  background: var(--wash);
}

.breadcrumb button::after {
  margin-left: 4px;
  color: var(--line);
  content: "›";
}

.relation-group-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 4px 0 2px;
  color: rgba(90, 58, 32, 0.65);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.relation-list button {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  width: 100%;
  border: 0;
  border-bottom: 1px solid var(--line-light);
  padding: 8px 0;
  text-align: left;
  background: transparent;
  cursor: pointer;
}

.relation-list button:hover {
  background: var(--wash);
}

.relation-list small {
  color: rgba(90, 58, 32, 0.6);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
}

.relation-path {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
  font-size: 13px;
}

.dir-tag {
  flex: 0 0 auto;
  border: 1px solid currentColor;
  border-radius: 2px;
  padding: 0 3px;
  font-size: 10px;
  font-style: normal;
}

.dir-tag.via-sup {
  color: var(--ink-soft);
}

.dir-tag.via-staff {
  color: #cf8a52;
}

.dir-tag.via-alias {
  color: var(--line);
}

.dir-tag.via-evolve {
  color: rgba(90, 58, 32, 0.55);
}

.evidence-section article {
  border-bottom: 1px solid var(--line-light);
  padding: 12px 0;
  font-family: "FZQINGKBYSJF", serif;
}

.evidence-section cite {
  display: block;
  color: var(--ink-soft);
  font-size: 11px;
  font-style: normal;
}

.evidence-section blockquote {
  margin: 8px 0 0;
  padding-left: 10px;
  border-left: 2px solid var(--line);
  font-size: 13px;
  line-height: 1.65;
}

.evidence-section article p,
.quiet-text {
  color: rgba(90, 58, 32, 0.65);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
  line-height: 1.5;
}

.evidence-section .event-citation {
  margin: 6px 0 0;
  padding-left: 10px;
}

.empty-state,
.loading-state {
  display: grid;
  place-content: center;
  height: 100%;
  text-align: center;
  color: rgba(90, 58, 32, 0.62);
}

.empty-seal {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  margin: 0 auto;
  border: 1px solid var(--line);
  font-size: 22px;
}

.loading-state {
  grid-row: 2;
}

.song-timeline {
  width: 100%;
  min-width: 0;
  min-height: 0;
  background: transparent;
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-rows: 78px minmax(0, 1fr) 160px;
  }

  .brand-copy p,
  .stage-summary {
    display: none;
  }

  .stage-heading {
    grid-template-columns: 1fr auto;
  }

  .filters {
    grid-column: 2;
  }

  .exploration-area.events-layout {
    grid-template-columns: 230px minmax(0, 1fr);
  }

  .exploration-area.events-layout.with-detail {
    grid-template-columns: 230px minmax(0, 1fr) auto;
  }

  .detail-panel {
    width: 42vw;
  }
}
</style>
