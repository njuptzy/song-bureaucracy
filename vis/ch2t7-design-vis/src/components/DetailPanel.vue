<template>
  <aside class="detail-panel" v-if="entity">
    <div class="head">
      <div>
        <h2>{{ entity.title }}</h2>
        <span class="badge">{{ entity.type }}</span>
        <span class="badge year">{{ selectedYear }}年截面</span>
        <span v-if="dict" class="badge page">辞典页 {{ dict.page }}</span>
      </div>
      <button class="close" @click="emit('close')">×</button>
    </div>

    <section v-if="dict">
      <h3>辞典词条</h3>
      <div class="catalog">{{ dict.catalog }}</div>
      <p v-if="dict.origin"><b>职源与沿革</b>：{{ dict.origin }}</p>
      <p v-if="dict.duty"><b>职掌</b>：{{ dict.duty }}</p>
      <details>
        <summary>查看词条原文</summary>
        <p class="source-text">{{ dict.text || dict.summary }}</p>
      </details>
    </section>

    <section v-if="childList.length">
      <h3>下级机构（{{ childList.length }}）</h3>
      <ul class="staff">
        <li v-for="s in childList" :key="s.id" @click="emit('select', s.id)">
          <span class="name">{{ s.title }}</span>
        </li>
      </ul>
    </section>

    <section v-if="staffList.length">
      <h3>编制隶属官职（{{ staffList.length }}）</h3>
      <ul class="staff">
        <li v-for="s in staffList" :key="s.edgeId" @click="emit('select', s.id)">
          <span class="name">{{ s.title }}</span>
          <span v-if="s.quota" class="quota">员 {{ s.quota }}</span>
          <span v-if="s.staffType" class="quota">{{ s.staffType }}</span>
          <span v-if="relationCitation(s.edgeId)" class="evidence-dot" title="此关系有原文证据">据</span>
        </li>
      </ul>
    </section>

    <section v-if="orgList.length">
      <h3>所属机构（{{ orgList.length }}）</h3>
      <ul class="staff">
        <li v-for="s in orgList" :key="s.edgeId" @click="emit('select', s.id)">
          <span class="name">{{ s.title }}</span>
          <span v-if="s.quota" class="quota">员 {{ s.quota }}</span>
        </li>
      </ul>
    </section>

    <section v-if="relationEvidence.length">
      <h3>当前关系原文（{{ relationEvidence.length }}）</h3>
      <details v-for="item in relationEvidence" :key="item.key" class="relation-proof">
        <summary>{{ item.label }}</summary>
        <div v-for="(citation, index) in item.citations" :key="index" class="citation">
          <b>{{ citation.citation || "出处未标" }}</b>
          <p v-if="citation.quotation">「{{ citation.quotation }}」</p>
          <p v-if="citation.note">{{ citation.note }}</p>
        </div>
      </details>
    </section>

    <section v-if="timepoints.length">
      <h3>时间点（{{ timepoints.length }}）</h3>
      <ul class="tps">
        <li v-for="tp in timepoints" :key="tp.id">
          <div class="tp-time">{{ tp.time || "时间未明" }}</div>
          <div class="tp-event">
            {{ tp.event }}
            <span v-if="tp.attr_grade" class="grade">{{ tp.attr_grade }}</span>
            <span v-if="tp.attr_category" class="cat">{{ tp.attr_category }}</span>
          </div>
          <div v-if="tp.quotation" class="quote">「{{ tp.quotation }}」</div>
          <div v-for="(c, i) in citationsOf(tp.id)" :key="i" class="citation">
            <b>{{ c.citation }}</b>
            <span v-if="c.quotation">：{{ c.quotation }}</span>
            <span v-if="c.conflict_flag" class="conflict">（有冲突）</span>
          </div>
        </li>
      </ul>
    </section>
  </aside>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  entityId: { type: Number, required: true },
  data: { type: Object, required: true },
  staffByOrg: { type: Map, required: true },
  staffByOfficial: { type: Map, required: true },
  selectedYear: { type: Number, required: true },
});
const emit = defineEmits(["select", "close"]);

const entity = computed(
  () => props.data.entities.find((e) => e.id === props.entityId) || null
);

const dict = computed(() =>
  entity.value ? props.data.dictionary[entity.value.title] || null : null
);

function periodActive(periods) {
  if (!periods || periods.length === 0) return true;
  return periods.some((p) => props.selectedYear >= p.start && props.selectedYear <= p.end);
}

const timepoints = computed(() =>
  (props.data.timepoints[String(props.entityId)] || []).filter((tp) => {
    if (tp.year_start == null || tp.year_end == null) return true;
    return props.selectedYear >= tp.year_start && props.selectedYear <= tp.year_end;
  })
);

const titleOf = computed(() => {
  const m = new Map();
  for (const e of props.data.entities) m.set(e.id, e.title);
  return (id) => m.get(id) || `#${id}`;
});

const staffList = computed(() =>
  (props.staffByOrg.get(props.entityId) || []).map((e) => ({
    edgeId: e.id,
    id: e.official,
    title: titleOf.value(e.official),
    quota: e.staff_quota,
    staffType: e.staff_type,
  }))
);

const orgList = computed(() =>
  (props.staffByOfficial.get(props.entityId) || []).map((e) => ({
    edgeId: e.id,
    id: e.org,
    title: titleOf.value(e.org),
    quota: e.staff_quota,
  }))
);

const childList = computed(() => {
  const seen = new Set();
  const out = [];
  for (const e of props.data.hierarchyEdges) {
    if (e.parent !== props.entityId || seen.has(e.child) || !periodActive(e.periods)) continue;
    seen.add(e.child);
    out.push({ edgeId: e.id, id: e.child, title: titleOf.value(e.child) });
  }
  return out;
});

function citationsOf(tpId) {
  return props.data.citations["T" + tpId] || [];
}

function relationCitation(edgeId) {
  return (props.data.citations["R" + edgeId] || [])[0] || null;
}

const relationEvidence = computed(() => {
  const candidates = [
    ...childList.value.map((item) => ({ edgeId: item.edgeId, label: `下级机构：${item.title}` })),
    ...staffList.value.map((item) => ({ edgeId: item.edgeId, label: `编制官职：${item.title}` })),
    ...orgList.value.map((item) => ({ edgeId: item.edgeId, label: `所属机构：${item.title}` })),
  ];
  const seen = new Set();
  return candidates.flatMap((item) => {
    if (seen.has(item.edgeId)) return [];
    seen.add(item.edgeId);
    const citations = props.data.citations["R" + item.edgeId] || [];
    return citations.length ? [{ ...item, key: `R${item.edgeId}`, citations }] : [];
  });
});
</script>

<style scoped>
.detail-panel {
  background: rgba(254, 254, 254, 0.72);
  color: var(--ink);
  padding: 14px 16px 30px;
  font-size: 13px;
  line-height: 1.8;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 2px solid var(--ink-2);
  padding-bottom: 8px;
}

.head h2 {
  margin: 0 0 4px;
  font-size: 20px;
  letter-spacing: 2px;
}

.badge {
  display: inline-block;
  border: 1px solid var(--olive);
  padding: 0 6px;
  font-size: 11px;
  color: var(--ink-2);
  margin-right: 6px;
}

.badge.page {
  color: var(--ink);
  border-color: var(--ink-2);
}

.badge.year { background: rgba(165, 166, 141, 0.25); }

.evidence-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 15px;
  height: 15px;
  margin-left: 4px;
  border: 1px solid var(--ink-2);
  border-radius: 50%;
  color: var(--ink-2);
  font-size: 9px;
}

.close {
  border: none;
  background: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--ink-2);
}

section {
  margin-top: 14px;
}

h3 {
  font-size: 14px;
  margin: 0 0 6px;
  color: var(--ink);
  letter-spacing: 2px;
  border-left: 6px solid var(--olive-fill);
  padding-left: 6px;
}

.catalog {
  font-size: 11px;
  color: var(--ink-2);
  margin-bottom: 6px;
}

p {
  margin: 4px 0;
}

details summary {
  cursor: pointer;
  color: var(--ink-2);
  font-size: 12px;
}

.staff {
  list-style: none;
  margin: 0;
  padding: 0;
  columns: 2;
}

.staff li {
  cursor: pointer;
  padding: 2px 0;
  break-inside: avoid;
}

.staff li:hover .name {
  color: var(--ink);
  text-decoration: underline;
}

.quota {
  font-size: 11px;
  color: var(--ink-2);
  margin-left: 4px;
}

.tps {
  list-style: none;
  margin: 0;
  padding: 0;
}

.tps li {
  border-left: 2px solid var(--olive);
  padding: 4px 0 8px 10px;
  margin-bottom: 8px;
}

.tp-time {
  font-weight: 700;
  color: var(--ink);
}

.grade,
.cat {
  display: inline-block;
  font-size: 11px;
  border: 1px solid var(--olive);
  padding: 0 4px;
  margin-left: 4px;
  color: var(--ink-2);
}

.quote {
  font-size: 12px;
  color: var(--ink-2);
  margin-top: 2px;
}

.citation {
  font-size: 11px;
  color: var(--ink-2);
  margin-top: 3px;
  padding-left: 8px;
  border-left: 1px dotted var(--line);
}

.source-text { white-space: pre-wrap; }

.relation-proof { margin: 5px 0; }

.relation-proof summary { cursor: pointer; color: var(--ink-2); }

.relation-proof p { margin: 3px 0; }

.conflict {
  color: #a03c28;
}
</style>
