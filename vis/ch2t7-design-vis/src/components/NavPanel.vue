<template>
  <nav class="nav-panel">
    <div class="cat-title">机构分类</div>
    <div class="cat-row">
      <button
        v-for="c in CATS"
        :key="c"
        class="cat-btn"
        :class="{ active: c === cat }"
        @click="cat = c"
      >
        {{ c }}
      </button>
    </div>

    <ul class="root-list">
      <li
        v-for="r in items"
        :key="r.id"
        :class="{ active: r.id === selectedId }"
        @click="emit('locate', r.id)"
      >
        {{ r.title }}
        <span class="size">{{ r.size }}</span>
      </li>
      <li v-if="!items.length" class="empty">此类暂无机构</li>
    </ul>

    <div class="selected-box">
      <div class="selected-title">当前选择机构说明</div>
      <div class="selected-text">{{ selectedSummary || "点击机构分类中的机构或画布节点查看。" }}</div>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  roots: { type: Array, required: true }, // [{id, title, cat, size}]
  selectedId: Number,
  selectedSummary: String,
});
const emit = defineEmits(["locate"]);

// 设计稿左栏五类
const CATS = ["内廷机构", "中央机构", "路级机构", "州县机构", "军队机构"];
const cat = ref("中央机构");

const items = computed(() => props.roots.filter((r) => r.cat === cat.value));
</script>

<style scoped>
.nav-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 0;
  font-size: 13px;
  color: var(--ink);
}

.cat-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 4px;
  padding: 12px 14px 10px;
  color: var(--ink);
}

.cat-row {
  display: flex;
  gap: 6px;
  padding: 0 12px 10px;
  border-bottom: 1px solid var(--line);
}

.cat-btn {
  flex: 1;
  writing-mode: vertical-rl;
  letter-spacing: 3px;
  height: 96px;
  background: rgba(254, 254, 254, 0.55);
  border: 1px solid var(--olive);
  color: var(--ink);
  font-size: 13px;
  cursor: pointer;
  padding: 6px 0;
}

.cat-btn:hover {
  border-color: var(--ink-2);
}

.cat-btn.active {
  background: var(--olive-fill);
  border-color: var(--ink-2);
  font-weight: 700;
}

.root-list {
  list-style: none;
  margin: 0;
  padding: 4px 0;
  overflow-y: auto;
  flex: 1;
  min-height: 60px;
}

.root-list li {
  cursor: pointer;
  padding: 3px 14px;
  border-bottom: 1px dotted var(--line);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  justify-content: space-between;
}

.root-list li:hover {
  background: rgba(165, 166, 141, 0.2);
}

.root-list li.active {
  background: rgba(165, 166, 141, 0.4);
  font-weight: 700;
}

.root-list .size {
  color: var(--ink-2);
  font-size: 11px;
  opacity: 0.7;
}

.root-list .empty {
  color: var(--ink-2);
  opacity: 0.6;
  cursor: default;
  justify-content: center;
}

.selected-box {
  margin: 8px 10px 10px;
  border: 1px solid var(--ink-2);
  background: rgba(254, 254, 254, 0.7);
  padding: 10px;
  flex: none;
}

.selected-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: 2px;
  margin-bottom: 6px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 4px;
}

.selected-text {
  font-size: 12px;
  line-height: 1.8;
  color: var(--ink-2);
  max-height: 180px;
  overflow-y: auto;
}
</style>
