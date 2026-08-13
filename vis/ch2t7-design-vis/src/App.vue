<template>
  <DesignTemplateCanvas
    v-if="data"
    :data="data"
    :initial-state="canvasState"
    @state-change="handleCanvasStateChange"
  />
  <div v-else class="loading">{{ loadError || "正在读取 ch2t7 数据…" }}</div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import DesignTemplateCanvas from "./components/DesignTemplateCanvas.vue";
import { readCanvasState, writeCanvasState } from "./utils/canvas_state";
import { filterSongData } from "./utils/song_scope";

const data = ref(null);
const dataVersion = ref("");
const loadError = ref("");
const canvasState = ref(readCanvasState());
let versionTimer = null;

function handleCanvasStateChange(state) {
  canvasState.value = state;
  writeCanvasState(state);
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    // 服务端 500 会带 JSON 错误说明（如缺少分类证据的机构 ID），一并显示便于定位。
    let detail = "";
    try {
      const body = await response.json();
      if (body?.error) detail = `：${body.error}`;
    } catch { /* 非 JSON 错误体 */ }
    throw new Error(`HTTP ${response.status}${detail}`);
  }
  return response.json();
}

async function refreshData(force = false) {
  try {
    const { version } = await fetchJson("/api/version");
    if (!force && version === dataVersion.value) return;
    data.value = filterSongData(await fetchJson("/api/data"));
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
