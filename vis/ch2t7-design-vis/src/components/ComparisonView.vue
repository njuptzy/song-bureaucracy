<template>
  <section class="comparison-view" aria-label="层级与演变对照视图">
    <button class="comparison-exit" type="button" @click="$emit('exit-comparison')">
      返回单视图
    </button>
    <div class="comparison-pane hierarchy-pane">
      <div class="pane-heading">层级结构</div>
      <DesignTemplateCanvas
        :data="data"
        :initial-state="hierarchyState"
        fixed-view-mode="hierarchy"
        :revision-panel-active="false"
        @state-change="handleHierarchyStateChange"
      />
    </div>
    <div class="comparison-divider" aria-hidden="true"></div>
    <div class="comparison-pane evolution-pane">
      <div class="pane-heading">时间沿革</div>
      <DesignTemplateCanvas
        :data="data"
        :initial-state="evolutionState"
        fixed-view-mode="evolution"
        :revision-panel-active="revisionPanelActive"
        @state-change="handleEvolutionStateChange"
        @selection-change="$emit('selection-change', $event)"
      />
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import DesignTemplateCanvas from "./DesignTemplateCanvas.vue";

const props = defineProps({
  data: { type: Object, required: true },
  initialState: { type: Object, default: null },
  revisionPanelActive: { type: Boolean, default: false },
});
const emit = defineEmits(["state-change", "selection-change", "exit-comparison"]);

function stateFor(mode, nestedKey) {
  const source = props.initialState?.[nestedKey] || props.initialState || {};
  return {
    ...source,
    viewMode: mode,
  };
}

const hierarchyState = computed(() => stateFor("hierarchy", "comparisonHierarchyState"));
const evolutionState = computed(() => stateFor("evolution", "comparisonEvolutionState"));

function handleHierarchyStateChange(state) {
  emit("state-change", {
    ...props.initialState,
    viewMode: "comparison",
    comparisonHierarchyState: { ...state, viewMode: "hierarchy" },
    comparisonEvolutionState: evolutionState.value,
  });
}

function handleEvolutionStateChange(state) {
  emit("state-change", {
    ...props.initialState,
    viewMode: "comparison",
    comparisonHierarchyState: hierarchyState.value,
    comparisonEvolutionState: { ...state, viewMode: "evolution" },
  });
}
</script>

<style scoped>
.comparison-view {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 1px minmax(0, 1fr);
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #f5f3ec;
}

.comparison-pane {
  position: relative;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.comparison-pane :deep(.design-template) {
  width: 100%;
  height: 100%;
}

.pane-heading {
  position: absolute;
  z-index: 3;
  top: 10px;
  left: 16px;
  padding: 3px 8px;
  border: 1px solid rgba(86, 57, 5, 0.32);
  background: rgba(245, 243, 236, 0.86);
  color: #563905;
  font-size: 12px;
  letter-spacing: 2px;
  pointer-events: none;
}

.comparison-divider {
  z-index: 4;
  width: 1px;
  height: 100%;
  background: rgba(86, 57, 5, 0.38);
  pointer-events: none;
}

.comparison-exit {
  position: absolute;
  z-index: 8;
  top: 10px;
  left: 50%;
  padding: 4px 10px;
  transform: translateX(-50%);
  border: 1px solid rgba(86, 57, 5, 0.42);
  background: rgba(245, 243, 236, 0.9);
  color: #563905;
  font: inherit;
  font-size: 11px;
  letter-spacing: 1px;
  cursor: pointer;
}

.comparison-exit:hover,
.comparison-exit:focus-visible {
  background: rgba(145, 128, 105, 0.14);
  outline: none;
}

</style>
