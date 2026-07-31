<template>
  <DesignTemplateCanvas v-if="data" :key="dataVersion" :data="data" />
  <div v-else class="loading">{{ loadError || "正在读取 ch2t7 数据…" }}</div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import DesignTemplateCanvas from "./components/DesignTemplateCanvas.vue";

const data = ref(null);
const dataVersion = ref("");
const loadError = ref("");
let versionTimer = null;

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function refreshData(force = false) {
  try {
    const { version } = await fetchJson("/api/version");
    if (!force && version === dataVersion.value) return;
    data.value = await fetchJson("/api/data");
    dataVersion.value = version;
    loadError.value = "";
  } catch (reason) {
    loadError.value = `数据加载失败：${reason.message}`;
  }
}

onMounted(async () => {
  await refreshData(true);
  versionTimer = window.setInterval(refreshData, 5000);
});

onBeforeUnmount(() => {
  if (versionTimer != null) window.clearInterval(versionTimer);
});
</script>

<style scoped>
.loading { width: 100%; height: 100%; display: grid; place-items: center; color: var(--ink-2); letter-spacing: 4px; }
</style>
