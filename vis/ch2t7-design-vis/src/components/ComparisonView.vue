<template>
  <section class="comparison-view" aria-label="层级与演变对照视图">
    <DesignTemplateCanvas
      :data="data"
      :initial-state="initialState"
      fixed-view-mode="comparison"
      :revision-panel-active="revisionPanelActive"
      @state-change="$emit('state-change', $event)"
      @selection-change="$emit('selection-change', $event)"
    />
    <button class="comparison-exit" type="button" @click="$emit('exit-comparison')">
      返回单视图
    </button>
  </section>
</template>

<script setup>
import DesignTemplateCanvas from "./DesignTemplateCanvas.vue";

defineProps({
  data: { type: Object, required: true },
  initialState: { type: Object, default: null },
  revisionPanelActive: { type: Boolean, default: false },
});
defineEmits(["state-change", "selection-change", "exit-comparison"]);
</script>

<style scoped>
.comparison-view {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #f5f3ec;
}

.comparison-view :deep(.design-template) {
  width: 100%;
  height: 100%;
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
