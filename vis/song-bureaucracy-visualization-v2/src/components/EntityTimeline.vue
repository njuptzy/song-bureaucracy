<template>
  <div class="timeline-view" :class="{ 'comparison-mode': timelineMode === 'comparison' }">
    <aside class="entity-rail">
      <div class="rail-caption" aria-hidden="true">
        <span>机构 / 官职</span>
        <span>{{ entityList.length }}</span>
      </div>
      <div ref="entityListRef" class="rail-list">
        <button
          v-for="item in entityList"
          :key="item.id"
          type="button"
          class="entity-item"
          :data-entity-id="item.id"
          :class="{
            active: item.id === entityId,
            office: item.type === '官职',
            'in-range': item.rangeEventCount > 0,
          }"
          @click="emit('select-entity', item.id)"
        >
          <span class="item-shape" aria-hidden="true"></span>
          <span class="item-title" :title="item.title">{{ item.title }}</span>
          <small :title="`当前时段 ${item.rangeEventCount} 条，共 ${item.eventCount} 条`">
            <template v-if="item.rangeEventCount">{{ item.rangeEventCount }}/</template>{{ item.eventCount }}
          </small>
        </button>
      </div>
      <div class="rail-legend" aria-hidden="true">
        <span><i class="item-shape"></i>机构</span>
        <span><i class="item-shape office"></i>官职</span>
      </div>
    </aside>

    <div v-if="entity" class="timeline-stage">
      <div class="timeline-head">
        <div class="head-title">
          <strong :title="entity.title">{{ entity.title }}</strong>
          <em>{{ entity.type }}</em>
          <small v-if="entity.yearMin != null">公元{{ entity.yearMin }}—{{ entity.yearMax }}年</small>
          <small>
            <template v-if="timelineMode === 'comparison'">
              {{ comparisonRows.length }} 个比较对象 · {{ comparisonEventCount }} 条带纪年记录
            </template>
            <template v-else>
              {{ exactEvents.length }} 条纪年
              <template v-if="undatedEvents.length"> · {{ undatedEvents.length }} 条无精确纪年</template>
            </template>
          </small>
          <small class="range-summary">
            {{ rangeLabel }} ·
            {{ timelineMode === "comparison" ? comparisonRangeEventCount : rangeMatchedEvents.length }} 条命中
          </small>
        </div>
        <div class="timeline-mode-switch" aria-label="年表显示模式">
          <button
            type="button"
            :class="{ active: timelineMode === 'comparison' }"
            :disabled="!comparisonAvailable"
            :title="comparisonAvailable ? '比较所属机构及其编制官职' : '当前对象没有可用于比较的编制隶属关系'"
            @click="timelineMode = 'comparison'"
          >
            相关官职对比
          </button>
          <button
            type="button"
            :class="{ active: timelineMode === 'single' }"
            @click="timelineMode = 'single'"
          >
            当前对象详情
          </button>
        </div>
        <span
          class="head-legend"
          title="事件类型目前根据事件文字中的关键词自动归类，仅用于辅助阅读，点击标记可查看原句核验。"
        >
          <strong>事件标记<em>自动归类</em></strong>
          <span><i class="legend-marker mk-established"></i>设置或恢复</span>
          <span><i class="legend-marker mk-abolished"></i>罢废</span>
          <span><i class="legend-marker mk-renamed"></i>改名或合并</span>
          <span><i class="legend-marker mk-recorded"></i>一般记载</span>
        </span>
        <button
          v-if="timelineMode === 'single'"
          type="button"
          class="play-btn"
          :disabled="!exactEvents.length"
          @click="togglePlay"
        >
          {{ playing ? "暂停" : "播放" }}
        </button>
      </div>

      <div ref="scrollRef" class="timeline-scroll">
        <div v-if="timelineMode === 'comparison'" class="comparison-chart">
          <div class="comparison-note">
            <span>{{ comparisonContextTitle }}</span>
            <small>横线表示有纪年记录的跨度，不等同于完整任职期</small>
          </div>
          <div class="comparison-axis">
            <span class="comparison-label-head">机构 / 官职</span>
            <div class="comparison-track axis-track">
              <i
                v-for="tick in comparisonTicks"
                :key="tick"
                :style="{ left: yearPercent(tick) }"
              >
                {{ tick }}
              </i>
            </div>
          </div>
          <div
            v-for="row in comparisonRows"
            :key="row.entity.id"
            class="comparison-row"
            :class="{
              institution: row.entity.type === '机构',
              current: row.entity.id === entityId,
            }"
          >
            <button
              type="button"
              class="comparison-label"
              :title="row.entity.title"
              @click="emit('select-entity', row.entity.id)"
            >
              <i :class="{ office: row.entity.type === '官职' }"></i>
              <span>{{ row.entity.title }}</span>
              <small v-if="row.quota != null">{{ row.quota }}{{ row.staffType || "员" }}</small>
            </button>
            <div class="comparison-track">
              <span
                v-if="rangeBandStyle"
                class="comparison-selected-range"
                :style="rangeBandStyle"
              ></span>
              <i
                v-for="tick in comparisonTicks"
                :key="tick"
                class="comparison-gridline"
                :style="{ left: yearPercent(tick) }"
              ></i>
              <span
                v-if="row.spanStyle"
                class="comparison-known-span"
                :style="row.spanStyle"
              ></span>
              <button
                v-for="event in row.datedEvents"
                :key="event.id"
                type="button"
                class="comparison-event"
                :class="[
                  `event-${event.eventType}`,
                  {
                    selected: selectedEvent?.id === event.id,
                    'in-range': eventOverlapsRange(event),
                  },
                ]"
                :style="{ left: yearPercent(event.yearStart) }"
                :data-event-id="event.id"
                :title="`${event.rawTime} · ${event.event}`"
                @click="onCardClick(event)"
              ></button>
              <span v-if="!row.datedEvents.length" class="comparison-undated-only">
                仅有时间未明或仅知范围记录
              </span>
            </div>
          </div>
        </div>

        <template v-else>
        <div :key="entityId" class="timeline-rows">
          <template v-for="(row, index) in rows" :key="row.key">
            <div
              v-if="row.kind === 'gap'"
              class="tl-row gap-row"
              :class="{ first: index === 0, last: index === rows.length - 1 }"
            >
              <div class="spine-track"></div>
              <div class="gap-label">隔 {{ row.years }} 年</div>
            </div>

            <div
              v-else-if="row.kind === 'divider'"
              class="tl-row divider-row"
              :class="{ first: index === 0, last: index === rows.length - 1 }"
            >
              <div class="spine-track"></div>
              <div class="divider-label"><span>1127 · 北宋 / 南宋</span></div>
            </div>

            <div
              v-else
              class="tl-row event-row"
              :class="{
                first: index === 0,
                last: index === rows.length - 1,
                'in-range': eventOverlapsRange(row.event),
              }"
              :data-event-id="row.event.id"
            >
              <div class="spine-track">
                <span v-if="row.showYear" class="spine-year">{{ row.event.yearStart }}</span>
                <i class="spine-dot" :class="`event-${row.event.eventType}`"></i>
              </div>
              <button
                type="button"
                class="event-card"
                :class="[{ selected: selectedEvent?.id === row.event.id }, `event-${row.event.eventType}`]"
                :style="{ animationDelay: `${Math.min(index, 12) * 45}ms` }"
                @click="onCardClick(row.event)"
              >
                <span class="card-top">
                  <strong>{{ row.event.rawTime }}</strong>
                  <em class="type-chip" :class="`event-${row.event.eventType}`">
                    {{ typeLabels[row.event.eventType] }}
                  </em>
                  <small v-if="row.event.category">{{ row.event.category }}</small>
                </span>
                <span class="card-text">{{ row.event.event }}</span>
                <span class="card-foot">
                  <template v-if="row.event.relationCount">{{ row.event.relationCount }} 条关系 · </template>
                  {{ row.event.citations.length }} 条引文
                </span>
              </button>
            </div>
          </template>

          <div v-if="!exactEvents.length" class="no-exact">该实体暂无精确纪年记录。</div>
        </div>

        <div v-if="undatedEvents.length" class="undated-block">
          <div class="undated-title">时间未明 / 仅知范围 · {{ undatedEvents.length }}</div>
          <button
            v-for="event in undatedEvents"
            :key="event.id"
            type="button"
            class="undated-row"
            :class="{
              selected: selectedEvent?.id === event.id,
              'in-range': eventOverlapsRange(event),
            }"
            :data-event-id="event.id"
            @click="onCardClick(event)"
          >
            <span class="u-time">
              {{ event.rawTime }}
              <em v-if="event.timeType === 'bounded'">仅知范围，不表示持续</em>
            </span>
            <span class="u-event">{{ event.event }}</span>
          </button>
        </div>
        </template>
      </div>
    </div>

    <div v-else class="timeline-stage">
      <div class="stage-placeholder">
        <span class="empty-seal">表</span>
        <p>从左侧选择一个机构或官职，查看它的完整时间线变化；<br />「播放」可逐年推进自动演示。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// 机构 / 官职时间分析：关联实体对齐比较 + 单体纵向纪事：
// - 有编制关系时默认把机构及其官职逐行放到同一条 960—1279 横轴上；
//   横线仅表达数据库中有纪年记录的跨度，事件标记可打开右侧证据；
// - 时间自上而下流动，左侧脊线串联，公元年份直接标在脊线上；
// - 每条记录一张信息卡：原始纪年、事件类型徽章、全文、关系/引文数，
//   点击卡片在右侧打开详情；
// - 相邻记录相隔 3 年以上插入「隔 N 年」压缩行表现时间流逝；
//   跨越 1127 年插入北宋 / 南宋分隔行；
// - 切换实体时卡片逐张滑入（stagger）；「播放」逐年推进，
//   自动滚动到对应卡片并联动右侧详情，点击任意卡片即停；
// - 无精确纪年的记录列在底部，同样可选中查看详情。
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";

const props = defineProps({
  dataset: { type: Object, required: true },
  entityId: { type: Number, default: null },
  selectedEvent: { type: Object, default: null },
  range: { type: Array, default: null },
  selectionActive: { type: Boolean, default: true },
});
const emit = defineEmits(["select-entity", "select-event"]);

const GAP_YEARS = 4; // 相邻纪年相差达到该年数即插入「隔 N 年」行
const DIVIDER_YEAR = 1127;

const typeLabels = {
  established: "设置",
  abolished: "罢废",
  restored: "恢复",
  renamed: "改称",
  merged: "合并",
  recorded: "记载",
};

const scrollRef = ref(null);
const entityListRef = ref(null);
const playing = ref(false);
const timelineMode = ref("single");
let playTimer = null;
let playIndex = -1;

const rangeLabel = computed(() => {
  if (!props.selectionActive || !props.range) return "未选择时段";
  const [start, end] = props.range;
  return start === end ? `${start}年` : `${start}—${end}年`;
});

function eventOverlapsRange(event) {
  if (
    !props.selectionActive ||
    !props.range ||
    event.timeType === "bounded" ||
    event.yearStart == null
  ) {
    return false;
  }
  const [start, end] = props.range;
  return event.yearStart <= end && (event.yearEnd ?? event.yearStart) >= start;
}

const rangeCountByEntity = computed(() => {
  const counts = new Map();
  for (const event of props.dataset.events) {
    if (!eventOverlapsRange(event)) continue;
    counts.set(event.entityId, (counts.get(event.entityId) || 0) + 1);
  }
  return counts;
});

const entityList = computed(() =>
  [...props.dataset.entities]
    .filter((entity) => entity.eventCount > 0)
    .map((entity) => ({
      ...entity,
      rangeEventCount: rangeCountByEntity.value.get(entity.id) || 0,
    }))
    .sort(
      (a, b) =>
        Number(b.id === props.entityId) - Number(a.id === props.entityId) ||
        b.rangeEventCount - a.rangeEventCount ||
        b.eventCount - a.eventCount ||
        a.title.localeCompare(b.title, "zh")
    )
);

const entity = computed(() =>
  props.dataset.entities.find((item) => item.id === props.entityId) ?? null
);

const entityEvents = computed(() => {
  if (props.entityId == null) return [];
  return props.dataset.events
    .filter((event) => event.entityId === props.entityId)
    .sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0) || a.id - b.id);
});

const exactEvents = computed(() =>
  entityEvents.value.filter((event) => event.timeType === "exact" && event.yearStart != null)
);

const undatedEvents = computed(() =>
  entityEvents.value.filter((event) => event.timeType !== "exact" || event.yearStart == null)
);

const rangeMatchedEvents = computed(() => entityEvents.value.filter(eventOverlapsRange));

const comparisonContext = computed(() => {
  if (!entity.value) return { institution: null, staffRelations: [] };
  const staffRelations = props.dataset.relations.filter(
    (relation) => relation.type === "编制隶属"
  );
  let institutionId = null;
  if (
    entity.value.type === "机构" &&
    staffRelations.some((relation) => relation.subjectEntityId === entity.value.id)
  ) {
    institutionId = entity.value.id;
  } else {
    institutionId =
      staffRelations.find((relation) => relation.objectEntityId === entity.value.id)
        ?.subjectEntityId ?? null;
  }
  if (institutionId == null) return { institution: null, staffRelations: [] };
  const institution =
    props.dataset.entities.find((item) => item.id === institutionId) ?? null;
  return {
    institution,
    staffRelations: staffRelations.filter(
      (relation) => relation.subjectEntityId === institutionId
    ),
  };
});

function yearPercent(year) {
  const clamped = Math.max(960, Math.min(1280, year));
  return `${((clamped - 960) / (1280 - 960)) * 100}%`;
}

const comparisonRows = computed(() => {
  const institution = comparisonContext.value.institution;
  if (!institution) return [];
  const relationByOffice = new Map();
  for (const relation of comparisonContext.value.staffRelations) {
    const existing = relationByOffice.get(relation.objectEntityId);
    if (!existing || (existing.staffQuota == null && relation.staffQuota != null)) {
      relationByOffice.set(relation.objectEntityId, relation);
    }
  }
  const items = [
    { entity: institution, quota: null, staffType: null },
    ...[...relationByOffice.entries()]
      .map(([officeId, relation]) => {
        const office = props.dataset.entities.find((item) => item.id === officeId);
        return office
          ? {
              entity: office,
              quota: relation.staffQuota,
              staffType: relation.staffType,
            }
          : null;
      })
      .filter(Boolean)
      .sort((a, b) => a.entity.title.localeCompare(b.entity.title, "zh")),
  ].sort(
    (a, b) =>
      Number(b.entity.id === props.entityId) - Number(a.entity.id === props.entityId) ||
      Number(b.entity.type === "机构") - Number(a.entity.type === "机构") ||
      a.entity.title.localeCompare(b.entity.title, "zh")
  );

  return items.map((item) => {
    const datedEvents = props.dataset.events
      .filter(
        (event) =>
          event.entityId === item.entity.id &&
          event.timeType !== "bounded" &&
          event.yearStart != null &&
          event.yearStart <= 1279 &&
          (event.yearEnd ?? event.yearStart) >= 960
      )
      .sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0) || a.id - b.id);
    const spanStart = datedEvents.length
      ? Math.min(...datedEvents.map((event) => Math.max(960, event.yearStart)))
      : null;
    const spanEnd = datedEvents.length
      ? Math.max(
          ...datedEvents.map((event) =>
            Math.min(1279, event.yearEnd ?? event.yearStart)
          )
        )
      : null;
    const left = spanStart == null ? null : Number.parseFloat(yearPercent(spanStart));
    const right = spanEnd == null ? null : Number.parseFloat(yearPercent(spanEnd));
    return {
      ...item,
      datedEvents,
      spanStyle:
        left == null || right == null
          ? null
          : {
              left: `${left}%`,
              width: `${Math.max(0.45, right - left)}%`,
            },
    };
  });
});

const comparisonAvailable = computed(() => comparisonRows.value.length > 1);
const comparisonContextTitle = computed(() =>
  comparisonContext.value.institution
    ? `${comparisonContext.value.institution.title}及其编制官职`
    : "当前对象没有可比较的编制官职"
);
const comparisonEventCount = computed(() =>
  comparisonRows.value.reduce((sum, row) => sum + row.datedEvents.length, 0)
);
const comparisonRangeEventCount = computed(() =>
  comparisonRows.value.reduce(
    (sum, row) => sum + row.datedEvents.filter(eventOverlapsRange).length,
    0
  )
);
const comparisonTicks = computed(() =>
  [960, 1000, 1040, 1080, 1120, 1127, 1160, 1200, 1240, 1279]
);
const rangeBandStyle = computed(() => {
  if (!props.selectionActive || !props.range) return null;
  const left = Number.parseFloat(yearPercent(props.range[0]));
  const right = Number.parseFloat(yearPercent(Math.min(props.range[1] + 1, 1280)));
  return {
    left: `${left}%`,
    width: `${Math.max(0.35, right - left)}%`,
  };
});

// 行序列：事件行 + 「隔 N 年」压缩行 + 1127 分隔行
const rows = computed(() => {
  const list = [];
  const events = exactEvents.value;
  events.forEach((event, index) => {
    const prev = events[index - 1];
    if (prev && event.yearStart - prev.yearStart >= GAP_YEARS) {
      list.push({ kind: "gap", key: `gap-${index}`, years: event.yearStart - prev.yearStart });
    }
    if (prev && prev.yearStart < DIVIDER_YEAR && event.yearStart >= DIVIDER_YEAR) {
      list.push({ kind: "divider", key: `divider-${index}` });
    }
    list.push({
      kind: "event",
      key: `event-${event.id}`,
      event,
      showYear: !prev || prev.yearStart !== event.yearStart,
    });
  });
  return list;
});

function scrollToEvent(id) {
  nextTick(() => {
    scrollRef.value
      ?.querySelector(`[data-event-id="${id}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
}

function onCardClick(event) {
  stopPlay();
  emit("select-event", event);
}

function stopPlay() {
  playing.value = false;
  if (playTimer) clearInterval(playTimer);
  playTimer = null;
  playIndex = -1;
}

function togglePlay() {
  if (playing.value) {
    stopPlay();
    return;
  }
  if (!exactEvents.value.length) return;
  playing.value = true;
  playIndex = exactEvents.value.findIndex((event) => event.id === props.selectedEvent?.id);
  stepPlay();
  playTimer = setInterval(stepPlay, 1200);
}

function stepPlay() {
  const events = exactEvents.value;
  playIndex += 1;
  if (playIndex >= events.length) {
    stopPlay();
    return;
  }
  const event = events[playIndex];
  emit("select-event", event);
  scrollToEvent(event.id);
}

watch(
  () => props.entityId,
  () => {
    stopPlay();
    timelineMode.value = comparisonAvailable.value ? "comparison" : "single";
  },
  { immediate: true }
);

// 选中原本未命中的实体后，它会随新时间段提升到列表首位，并让列表回到该实体位置。
watch(
  () => [props.entityId, props.range?.[0], props.range?.[1]],
  async () => {
    if (props.entityId == null) return;
    await nextTick();
    const container = entityListRef.value;
    const item = container?.querySelector(`[data-entity-id="${props.entityId}"]`);
    if (!container || !item) return;
    const containerRect = container.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();
    const top = container.scrollTop + itemRect.top - containerRect.top;
    container.scrollTo({ top: Math.max(0, top - 6), behavior: "smooth" });
  },
  { flush: "post" }
);

// 搜索、关系跳转等外部选中时滚动到对应卡片
watch(
  () => props.selectedEvent,
  (event) => {
    if (event && !playing.value) scrollToEvent(event.id);
  }
);

onBeforeUnmount(() => {
  if (playTimer) clearInterval(playTimer);
});
</script>

<style scoped lang="scss">
.timeline-view {
  display: flex;
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding-right: 10px;
}

.timeline-view.comparison-mode {
  padding-right: 0;

  .entity-rail {
    display: none;
  }

  .comparison-chart {
    padding-right: 0.2vw;
  }

  .comparison-axis,
  .comparison-row {
    // 下方总时间线的年份轴起点为 2vw 外边距 + 9.6vw 控制栏 = 11.6vw。
    // 主内容左边界为 1.8vw，扣除 comparison-chart 的 4px 左内边距后，
    // 上方标签栏使用剩余的 9.8vw - 4px，年份轴即可在同一位置起步。
    grid-template-columns: calc(9.8vw - 4px) minmax(480px, 1fr);
  }
}

.entity-rail {
  display: flex;
  flex-direction: column;
  width: 210px;
  flex-shrink: 0;
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

.rail-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 8px 24px;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

.rail-legend {
  display: flex;
  flex: 0 0 auto;
  gap: 14px;
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

  &.active {
    border-color: var(--ink-soft);
    background: rgba(106, 74, 42, 0.1);
  }

  &.in-range small {
    color: var(--teal);
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

  &.in-range .item-shape {
    border-color: var(--teal);
    background: var(--teal);
  }

  .item-title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  small {
    color: rgba(90, 58, 32, 0.5);
    font-size: 10px;
  }
}

.timeline-stage {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.timeline-head {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 14px;
  height: 40px;
  border-bottom: 1px solid var(--line-light);
  padding: 0 10px 6px 4px;

  .head-title {
    display: flex;
    flex: 1;
    align-items: baseline;
    gap: 8px;
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;

    strong {
      flex: 0 1 auto;
      min-width: 0;
      max-width: min(440px, 32vw);
      overflow: hidden;
      font-size: 18px;
      font-weight: 400;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    em {
      flex: 0 0 auto;
      border: 1px solid var(--line);
      padding: 0 4px;
      color: rgba(90, 58, 32, 0.62);
      font-size: 11px;
      font-style: normal;
    }

    small {
      flex: 0 0 auto;
      color: rgba(90, 58, 32, 0.6);
      font-family: "FZQINGKBYSJF", serif;
      font-size: 11px;
      white-space: nowrap;
    }

    .range-summary {
      border-left: 1px solid var(--line-light);
      padding-left: 8px;
      color: var(--teal);
    }
  }

  .head-legend {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-left: auto;
    color: rgba(90, 58, 32, 0.6);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 10px;
    white-space: nowrap;

    > strong {
      display: inline-flex;
      flex-direction: column;
      color: var(--ink-soft);
      font-size: 9px;
      font-weight: 400;
      line-height: 1.05;

      em {
        color: var(--rust);
        font-size: 7px;
        font-style: normal;
        letter-spacing: 0.04em;
      }
    }

    span {
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
  }

  .play-btn {
    border: 1px solid var(--ink-soft);
    border-radius: 999px;
    padding: 3px 16px;
    color: var(--ink-soft);
    background: transparent;
    font-family: "FZQINGKBYSJF", serif;
    font-size: 12px;
    cursor: pointer;

    &:hover:not(:disabled) {
      background: var(--wash);
    }

    &:disabled {
      border-color: var(--line-light);
      color: rgba(90, 58, 32, 0.4);
      cursor: default;
    }
  }
}

.timeline-mode-switch {
  display: inline-flex;
  flex: 0 0 auto;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 4px;

  button {
    border: 0;
    border-right: 1px solid var(--line-light);
    padding: 3px 7px;
    color: rgba(90, 58, 32, 0.62);
    background: transparent;
    font-family: "FZQINGKBYSJF", serif;
    font-size: 9px;
    cursor: pointer;

    &:last-child {
      border-right: 0;
    }

    &.active {
      color: var(--paper);
      background: var(--ink-soft);
    }

    &:disabled {
      color: rgba(90, 58, 32, 0.3);
      background: rgba(114, 74, 43, 0.04);
      cursor: not-allowed;
    }
  }
}

.timeline-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-anchor: none;
  padding: 4px 0 60px;
  scrollbar-color: var(--line) transparent;
  scrollbar-width: thin;
}

// —— 关联实体对齐比较 ——
.comparison-chart {
  min-width: 680px;
  padding: 4px 12px 50px 4px;
}

.comparison-note {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  border-bottom: 1px solid var(--line-light);
  padding: 5px 4px 7px;
  color: var(--ink);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;

  small {
    color: rgba(90, 58, 32, 0.52);
    font-size: 8px;
  }
}

.comparison-axis,
.comparison-row {
  display: grid;
  grid-template-columns: 165px minmax(480px, 1fr);
  align-items: stretch;
}

.comparison-axis {
  position: sticky;
  z-index: 4;
  top: -4px;
  height: 36px;
  border-bottom: 1px solid var(--line);
  background: rgba(244, 241, 234, 0.97);
}

.comparison-label-head {
  display: flex;
  align-items: end;
  padding: 0 8px 6px;
  color: rgba(90, 58, 32, 0.56);
  font-size: 9px;
  letter-spacing: 0.08em;
}

.comparison-track {
  position: relative;
  min-width: 0;
  border-left: 1px solid var(--line-light);
}

.axis-track i {
  position: absolute;
  bottom: 5px;
  transform: translateX(-50%);
  color: rgba(90, 58, 32, 0.58);
  font-size: 8px;
  font-style: normal;
}

.comparison-row {
  min-height: 35px;
  border-bottom: 1px solid rgba(114, 74, 43, 0.12);

  &.institution {
    background: rgba(106, 74, 42, 0.06);
  }

  &.current {
    box-shadow: inset 3px 0 0 var(--rust);
  }
}

.comparison-label {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 6px;
  overflow: hidden;
  border: 0;
  padding: 5px 8px;
  color: var(--ink);
  background: transparent;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
  text-align: left;
  cursor: pointer;

  &:hover {
    background: var(--wash);
  }

  i {
    width: 8px;
    height: 8px;
    flex: 0 0 auto;
    border: 1px solid var(--ink-soft);
    border-radius: 1px;
    background: rgba(106, 74, 42, 0.14);

    &.office {
      border-radius: 50%;
      background: var(--paper);
    }
  }

  span {
    overflow: hidden;
    flex: 1;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  small {
    flex: 0 0 auto;
    color: rgba(90, 58, 32, 0.55);
    font-size: 8px;
  }
}

.comparison-gridline {
  position: absolute;
  top: 0;
  bottom: 0;
  border-left: 1px solid rgba(114, 74, 43, 0.1);
}

.comparison-selected-range {
  position: absolute;
  z-index: 0;
  top: 0;
  bottom: 0;
  min-width: 2px;
  background: rgba(157, 83, 52, 0.08);
}

.comparison-known-span {
  position: absolute;
  z-index: 1;
  top: 50%;
  height: 3px;
  min-width: 3px;
  transform: translateY(-50%);
  border-radius: 2px;
  background: rgba(90, 58, 32, 0.38);
}

.comparison-event {
  position: absolute;
  z-index: 2;
  top: 50%;
  width: 9px;
  height: 9px;
  transform: translate(-50%, -50%);
  border: 1.5px solid var(--ink-soft);
  border-radius: 50%;
  padding: 0;
  background: var(--paper);
  cursor: pointer;

  &:hover,
  &.selected {
    z-index: 3;
    box-shadow: 0 0 0 4px rgba(157, 83, 52, 0.2);
  }

  &.in-range {
    border-color: var(--rust);
  }

  &.event-established,
  &.event-restored {
    background: var(--teal);
  }

  &.event-abolished {
    border-radius: 0;
    background: var(--rust);
    transform: translate(-50%, -50%) rotate(45deg) scale(0.76);
  }

  &.event-renamed,
  &.event-merged {
    border-radius: 1px;
  }

  &.event-recorded {
    border-color: rgba(90, 58, 32, 0.58);
  }
}

.comparison-undated-only {
  position: absolute;
  top: 50%;
  left: 8px;
  transform: translateY(-50%);
  color: rgba(90, 58, 32, 0.42);
  font-size: 8px;
}

// —— 纵向年表 ——
.tl-row {
  display: flex;
  align-items: stretch;
}

.spine-track {
  position: relative;
  flex: 0 0 auto;
  width: 96px;

  &::before {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 60px;
    border-left: 1px solid var(--line);
    content: "";
  }
}

// 首行脊线从圆点起、末行到圆点止
.tl-row.first > .spine-track::before {
  top: 50%;
}

.tl-row.last > .spine-track::before {
  bottom: 50%;
}

.spine-year {
  position: absolute;
  top: 50%;
  right: 68px;
  transform: translateY(-50%);
  color: var(--ink-soft);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 12px;
  letter-spacing: 0.04em;
}

.spine-dot {
  position: absolute;
  top: 50%;
  left: 60px;
  width: 9px;
  height: 9px;
  border: 1.5px solid var(--ink-soft);
  border-radius: 50%;
  background: var(--paper);
  transform: translate(-50%, -50%);

  &.event-established,
  &.event-restored {
    background: var(--teal);
  }

  &.event-abolished {
    border-radius: 0;
    background: var(--rust);
    transform: translate(-50%, -50%) rotate(45deg) scale(0.75);
  }

  &.event-renamed,
  &.event-merged {
    border-radius: 0;
  }
}

.event-row.in-range {
  .spine-dot {
    box-shadow: 0 0 0 4px rgba(111, 150, 144, 0.18);
  }

  .event-card {
    border-color: rgba(111, 150, 144, 0.75);
    background: rgba(111, 150, 144, 0.1);
  }
}

// 事件信息卡
.event-card {
  display: block;
  flex: 1;
  min-width: 0;
  margin: 7px 26px 7px 14px;
  border: 1px solid var(--line-light);
  border-left: 3px solid var(--ink-soft);
  border-radius: 4px;
  padding: 9px 16px 8px;
  text-align: left;
  color: var(--ink);
  background: rgba(244, 241, 234, 0.72);
  cursor: pointer;
  animation: card-in 360ms ease both;

  &:hover {
    border-color: var(--ink-soft);
  }

  &.selected {
    border-color: var(--ink-soft);
    box-shadow: 0 4px 18px rgba(90, 58, 32, 0.16);
  }
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }

  to {
    opacity: 1;
    transform: none;
  }
}

.card-top {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;

  strong {
    font-size: 15px;
    font-weight: 400;
    letter-spacing: 0.03em;
  }

  small {
    color: rgba(90, 58, 32, 0.6);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
  }
}

.type-chip {
  border-radius: 999px;
  padding: 0 8px;
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
  font-style: normal;
  line-height: 1.7;

  &.event-established,
  &.event-restored {
    color: #fff;
    background: var(--teal);
  }

  &.event-abolished {
    color: #fff;
    background: var(--rust);
  }

  &.event-renamed,
  &.event-merged {
    border: 1px solid var(--line);
    color: var(--ink-soft);
  }

  &.event-recorded {
    border: 1px solid var(--line-light);
    color: rgba(90, 58, 32, 0.66);
  }
}

.card-text {
  display: block;
  margin-top: 5px;
  color: rgba(90, 58, 32, 0.88);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 13px;
  line-height: 1.75;
}

.card-foot {
  display: block;
  margin-top: 5px;
  color: rgba(90, 58, 32, 0.5);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
}

// 「隔 N 年」压缩行
.gap-row {
  align-items: center;
  height: 26px;

  .spine-track::before {
    border-left-style: dashed;
  }
}

.gap-label {
  margin-left: 14px;
  color: rgba(90, 58, 32, 0.45);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
  letter-spacing: 0.2em;
}

// 1127 分隔行
.divider-row {
  align-items: center;
  height: 34px;
}

.divider-label {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 10px;
  margin: 0 26px 0 14px;
  color: rgba(90, 58, 32, 0.6);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 11px;
  letter-spacing: 0.18em;

  &::before,
  &::after {
    flex: 1;
    border-top: 1px solid var(--line);
    content: "";
  }
}

.no-exact {
  padding: 40px 0;
  text-align: center;
  color: rgba(90, 58, 32, 0.55);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 13px;
}

// 无精确纪年记录
.undated-block {
  border-top: 1px solid var(--line-light);
  margin: 18px 26px 0 110px;
  padding-top: 8px;

  .undated-title {
    padding: 4px 0;
    color: rgba(90, 58, 32, 0.56);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
    letter-spacing: 0.14em;
  }

  .undated-row {
    display: block;
    width: 100%;
    border: 0;
    border-bottom: 1px solid var(--line-light);
    padding: 6px 4px;
    text-align: left;
    color: var(--ink-soft);
    background: transparent;
    font-family: "FZQINGKBYSJF", serif;
    font-size: 12px;
    cursor: pointer;

    &:hover,
    &.selected {
      background: var(--wash);
    }

    &.in-range {
      border-bottom-color: rgba(111, 150, 144, 0.75);
      background: rgba(111, 150, 144, 0.1);
      box-shadow: inset 3px 0 0 var(--teal);
    }

    .u-time {
      display: block;
      color: rgba(90, 58, 32, 0.6);
      font-size: 11px;

      em {
        margin-left: 6px;
        color: rgba(142, 83, 43, 0.78);
        font-style: normal;
      }
    }

    .u-event {
      display: block;
      margin-top: 2px;
      line-height: 1.6;
    }
  }
}

.stage-placeholder {
  display: grid;
  flex: 1;
  place-content: center;
  text-align: center;
  color: rgba(90, 58, 32, 0.55);

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
    font-family: "FZQINGKBYSJF", serif;
    font-size: 13px;
    line-height: 1.8;
  }
}
</style>
