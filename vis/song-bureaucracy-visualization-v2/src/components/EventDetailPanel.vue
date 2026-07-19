<template>
  <aside class="detail-panel">
    <div class="detail-head">
      <span>{{ event.entityType }} · {{ event.category || "未分类" }}</span>
      <button type="button" @click="$emit('close')" aria-label="关闭详情">×</button>
    </div>

    <h3>{{ event.title }}</h3>
    <p class="detail-time">
      {{ event.rawTime }}<template v-if="event.yearStart != null"> · 公元{{ event.yearStart }}年</template>
    </p>
    <p class="detail-event">{{ event.event }}</p>

    <dl v-if="event.officerType || event.grade" class="attributes">
      <template v-if="event.officerType">
        <dt>官职性质</dt><dd>{{ event.officerType }}</dd>
      </template>
      <template v-if="event.grade">
        <dt>品级</dt><dd>{{ event.grade }}</dd>
      </template>
    </dl>

    <section class="detail-section">
      <div class="section-title">
        <h4>关联结构</h4>
        <span>{{ relations.length }}</span>
      </div>
      <template v-if="relations.length">
        <div v-for="group in groupedRelations" :key="group.type" class="relation-group">
          <div class="relation-group-title">
            <span>{{ group.type }}</span>
            <span>{{ group.items.length }}</span>
          </div>
          <div class="relation-list">
            <div v-for="relation in group.items" :key="relation.id" class="relation-item">
              <div class="relation-line">
                <button
                  type="button"
                  class="relation-main"
                  :class="{ open: expandedId === relation.id }"
                  :title="expandedId === relation.id ? '收起关系证据' : '展开关系证据'"
                  @click="toggleEvidence(relation.id)"
                >
                  <span class="relation-path">
                    <em class="dir-tag" :class="`via-${viaClassOf(relation.type)}`">
                      {{ directionLabel(relation) }}
                    </em>
                    {{ relation.otherTitle }}
                  </span>
                  <small v-if="relation.staffQuota">
                    {{ relation.staffQuota }}{{ relation.staffType || "员" }}
                  </small>
                  <i class="evidence-chip" :class="{ open: expandedId === relation.id }">证</i>
                </button>
                <button
                  type="button"
                  class="relation-follow"
                  title="跳转到该记录"
                  @click="$emit('follow-relation', relation)"
                >
                  ›
                </button>
              </div>

              <div v-if="expandedId === relation.id" class="relation-evidence">
                <p class="relation-meta">
                  {{ relation.type }} ·
                  <template v-if="relation.periods?.length">{{ relationPeriodsLabel(relation) }}有记录</template>
                  <template v-else>时间未明</template>
                </p>
                <article v-for="(citation, index) in relation.citations" :key="index">
                  <cite>{{ citation.citation }}</cite>
                  <blockquote>{{ citation.quotation }}</blockquote>
                  <p v-if="citation.note">{{ citation.note }}</p>
                </article>
                <p v-if="!relation.citations.length" class="quiet-text">该关系暂无引文记录。</p>
              </div>
            </div>
          </div>
        </div>
      </template>
      <p v-else class="quiet-text">这个时间节点没有关联关系。</p>
    </section>

    <section class="detail-section evidence-section">
      <div class="section-title">
        <h4>辞典证据</h4>
        <span>{{ event.citations.length }}</span>
      </div>
      <article v-for="(citation, index) in event.citations" :key="index">
        <cite>{{ citation.citation }}</cite>
        <blockquote>{{ citation.quotation }}</blockquote>
        <p v-if="citation.note">{{ citation.note }}</p>
      </article>
    </section>
  </aside>
</template>

<script setup>
// 单一时间节点（事件）的详情面板：属性、关联结构、辞典证据。
// 关联结构中的每条关系可就地展开，查看证明该关系的引文
// （关系类型、有记录年份、出处与原文），› 按钮跳转到对端记录。
// 时序事件视图与年表视图共用。
import { computed, ref, watch } from "vue";
import {
  groupRelationsByType,
  relationDirectionLabel as directionLabel,
  relationPeriodsLabel,
  relationViaClass as viaClassOf,
} from "@/utils/hierarchy";

const props = defineProps({
  event: { type: Object, required: true },
  relations: { type: Array, default: () => [] },
});
defineEmits(["close", "follow-relation"]);

const groupedRelations = computed(() => groupRelationsByType(props.relations));

// 展开中的关系证据（一次只展开一条，切换事件时收起）
const expandedId = ref(null);

function toggleEvidence(id) {
  expandedId.value = expandedId.value === id ? null : id;
}

watch(
  () => props.event,
  () => {
    expandedId.value = null;
  }
);
</script>

<style scoped lang="scss">
.relation-item {
  border-bottom: 1px solid var(--line-light);
}

.relation-line {
  display: flex;
  align-items: stretch;

  .relation-main {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 8px;
    min-width: 0;
    border: 0;
    padding: 8px 0;
    color: var(--ink);
    background: transparent;
    font-family: "FZQINGKBYSJF", serif;
    font-size: 13px;
    text-align: left;
    cursor: pointer;

    &:hover {
      background: var(--wash);
    }

    .relation-path {
      display: inline-flex;
      flex: 1;
      align-items: baseline;
      gap: 6px;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    small {
      flex: 0 0 auto;
      color: rgba(90, 58, 32, 0.6);
      font-size: 11px;
    }

    .evidence-chip {
      display: inline-grid;
      flex: 0 0 auto;
      place-items: center;
      width: 16px;
      height: 16px;
      border: 1px solid var(--line);
      border-radius: 50%;
      color: rgba(90, 58, 32, 0.55);
      font-size: 9px;
      font-style: normal;

      &.open {
        border-color: var(--ink-soft);
        color: var(--paper);
        background: var(--ink-soft);
      }
    }
  }

  .relation-follow {
    flex: 0 0 auto;
    width: 26px;
    border: 0;
    border-left: 1px solid var(--line-light);
    color: rgba(90, 58, 32, 0.55);
    background: transparent;
    font-size: 16px;
    cursor: pointer;

    &:hover {
      color: var(--ink);
      background: var(--wash);
    }
  }
}

.relation-evidence {
  margin: 0 0 8px 8px;
  border-left: 2px solid var(--line);
  padding: 4px 0 4px 10px;

  .relation-meta {
    margin: 2px 0 6px;
    color: rgba(90, 58, 32, 0.62);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
    letter-spacing: 0.06em;
  }

  article {
    padding: 6px 0;
  }

  cite {
    display: block;
    color: var(--ink-soft);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
    font-style: normal;
  }

  blockquote {
    margin: 5px 0 0;
    border-left: 2px solid var(--line-light);
    padding-left: 8px;
    color: rgba(90, 58, 32, 0.88);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 12px;
    line-height: 1.65;
  }

  article p,
  .quiet-text {
    margin: 5px 0 0;
    color: rgba(90, 58, 32, 0.65);
    font-family: "FZQINGKBYSJF", serif;
    font-size: 11px;
  }
}
</style>
