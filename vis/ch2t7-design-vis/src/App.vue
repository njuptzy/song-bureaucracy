<template>
  <main class="application-shell">
    <DesignTemplateCanvas
      v-if="data"
      :data="data"
      :initial-state="canvasState"
      @state-change="handleCanvasStateChange"
      @selection-change="handleSelectionChange"
    />
    <div v-else class="loading">{{ loadError || "正在读取职官数据…" }}</div>
    <RevisionWorkspace
      v-if="baseData"
      :edit-mode="editMode"
      :drawer="revisionDrawer"
      :state="revisionState"
      :commits="commits"
      :selection="selectedFact"
      :data="data"
      :busy="revisionBusy"
      :error="revisionError"
      :connection-mode="connectionMode"
      :connect-source="connectSource"
      :connect-target="connectTarget"
      @toggle-edit="toggleEditMode"
      @toggle-drawer="toggleDrawer"
      @clear-selection="selectedFact = null"
      @add-operation="addOperation"
      @workspace-action="workspaceAction"
      @remove-group="removeGroup"
      @commit="commitDraft"
      @restore="restoreVersion"
      @toggle-connect="toggleConnectionMode"
      @cancel-connect="cancelConnection"
      @add-connection="addConnection"
    />
  </main>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import DesignTemplateCanvas from "./components/DesignTemplateCanvas.vue";
import RevisionWorkspace from "./components/RevisionWorkspace.vue";
import { readCanvasState, writeCanvasState } from "./utils/canvas_state";
import { filterSongData } from "./utils/song_scope";
import { applyRevisionPreview } from "./utils/revision_patch";
import { revisionDelete, revisionPost, revisionRequest } from "./utils/revision_api";

const baseData = ref(null);
const data = ref(null);
const dataVersion = ref("");
const loadError = ref("");
const canvasState = ref(readCanvasState());
const revisionState = ref(null);
const revisionPreview = ref(null);
const revisionDrawer = ref("");
const revisionError = ref("");
const revisionBusy = ref(false);
const editMode = ref(false);
const selectedFact = ref(null);
const commits = ref([]);
const connectionMode = ref(false);
const connectSource = ref(null);
const connectTarget = ref(null);
let versionTimer = null;

function handleCanvasStateChange(state) {
  canvasState.value = state;
  writeCanvasState(state);
}

function handleSelectionChange(selection) {
  selectedFact.value = selection;
  if (!editMode.value || !connectionMode.value || selection?.kind !== "timepoint") return;
  if (!connectSource.value) {
    connectSource.value = selection;
    connectTarget.value = null;
    return;
  }
  if (String(connectSource.value.id) === String(selection.id)) return;
  connectTarget.value = selection;
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      if (body?.error) detail = `：${body.error}`;
    } catch { /* non-JSON body */ }
    throw new Error(`HTTP ${response.status}${detail}`);
  }
  return response.json();
}

function applyPreview(preview = revisionPreview.value) {
  if (!baseData.value) return;
  data.value = preview?.state?.draft?.group_count
    ? applyRevisionPreview(baseData.value, preview)
    : baseData.value;
}

async function refreshRevision() {
  revisionState.value = await revisionRequest("/api/revisions/state");
  revisionPreview.value = await revisionRequest("/api/revisions/draft/preview");
  revisionState.value = revisionPreview.value.state || revisionState.value;
  applyPreview();
}

async function refreshData(force = false) {
  try {
    const { version } = await fetchJson("/api/version");
    if (!force && version === dataVersion.value) return;
    if (!force && revisionState.value?.draft?.group_count) {
      await refreshRevision();
      return;
    }
    baseData.value = filterSongData(await fetchJson("/api/data"));
    dataVersion.value = version;
    loadError.value = "";
    if (revisionState.value?.draft?.group_count) applyPreview();
    else data.value = baseData.value;
  } catch (reason) {
    loadError.value = `数据加载失败：${reason.message}`;
  }
}

async function loadCommits() {
  const payload = await revisionRequest("/api/revisions/commits");
  commits.value = payload.commits || [];
}

function toggleEditMode() {
  if (revisionState.value?.edit_locked) return;
  editMode.value = !editMode.value;
  revisionError.value = "";
  if (!editMode.value) cancelConnection();
}

async function toggleDrawer(name) {
  revisionDrawer.value = revisionDrawer.value === name ? "" : name;
  revisionError.value = "";
  if (revisionDrawer.value === "history") {
    try { await loadCommits(); } catch (reason) { revisionError.value = reason.message; }
  }
}

async function runRevisionAction(callback) {
  revisionBusy.value = true;
  revisionError.value = "";
  try {
    return await callback();
  } catch (reason) {
    revisionError.value = reason.message;
    throw reason;
  } finally {
    revisionBusy.value = false;
  }
}

async function addOperation(payload) {
  try {
    const result = await runRevisionAction(() => revisionPost("/api/revisions/draft/operations", payload));
    revisionPreview.value = result.preview;
    revisionState.value = result.preview.state;
    applyPreview(result.preview);
    revisionDrawer.value = "workspace";
  } catch { /* error is displayed by runRevisionAction */ }
}

async function workspaceAction(action) {
  if (action === "discard" && !window.confirm("放弃当前工作区的全部修改？")) return;
  try {
    await runRevisionAction(() => revisionPost(`/api/revisions/draft/${action}`));
    await refreshRevision();
  } catch { /* displayed */ }
}

async function removeGroup(groupId) {
  try {
    await runRevisionAction(() => revisionDelete(`/api/revisions/draft/operations/${groupId}`));
    await refreshRevision();
  } catch { /* displayed */ }
}

async function commitDraft(summary) {
  try {
    await runRevisionAction(() => revisionPost("/api/revisions/commit", { summary }));
    revisionPreview.value = null;
    await refreshData(true);
    await Promise.all([refreshRevision(), loadCommits()]);
    revisionDrawer.value = "history";
    editMode.value = false;
    selectedFact.value = null;
    cancelConnection();
  } catch { /* displayed */ }
}

async function restoreVersion(targetHash) {
  if (!window.confirm("恢复会创建一条新的反向提交，已有历史不会删除。继续？")) return;
  try {
    const preview = await runRevisionAction(() => revisionPost("/api/revisions/restore-preview", { target_hash: targetHash }));
    if (!window.confirm(`将生成 ${preview.operation_count} 项反向操作。确认恢复？`)) return;
    await runRevisionAction(() => revisionPost("/api/revisions/restore", { target_hash: targetHash }));
    await refreshData(true);
    await Promise.all([refreshRevision(), loadCommits()]);
  } catch { /* displayed */ }
}

function toggleConnectionMode() {
  connectionMode.value = !connectionMode.value;
  connectSource.value = null;
  connectTarget.value = null;
  selectedFact.value = null;
}

function cancelConnection() {
  connectionMode.value = false;
  connectSource.value = null;
  connectTarget.value = null;
}

async function addConnection(payload) {
  await addOperation(payload);
  if (!revisionError.value) cancelConnection();
}

onMounted(async () => {
  await refreshData(true);
  try {
    await Promise.all([refreshRevision(), loadCommits()]);
  } catch (reason) {
    revisionError.value = `版本工作区加载失败：${reason.message}`;
  }
  versionTimer = window.setInterval(refreshData, 5000);
});

onBeforeUnmount(() => {
  if (versionTimer != null) window.clearInterval(versionTimer);
});
</script>

<style scoped>
.application-shell { position: relative; width: 100%; height: 100%; overflow: hidden; }
.loading { width: 100%; height: 100%; display: grid; place-items: center; color: var(--ink-2); letter-spacing: 4px; }
</style>
