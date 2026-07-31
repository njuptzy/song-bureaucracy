<template>
  <DesignTemplateCanvas v-if="data" :data="data" />
  <div v-else class="loading">{{ loadError || "正在读取 ch2t7 数据…" }}</div>
</template>

<script setup>
import { ref } from "vue";
import DesignTemplateCanvas from "./components/DesignTemplateCanvas.vue";

const data = ref(null);
const loadError = ref("");

fetch("/api/data")
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((payload) => {
    data.value = payload;
  })
  .catch((reason) => {
    loadError.value = `数据加载失败：${reason.message}`;
  });
</script>

<style scoped>
.loading { width: 100%; height: 100%; display: grid; place-items: center; color: var(--ink-2); letter-spacing: 4px; }
</style>
