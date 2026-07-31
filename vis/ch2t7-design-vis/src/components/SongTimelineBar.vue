<template>
  <div ref="wrapRef" class="timeline-bar">
    <!-- 直接使用设计师的字体转曲 SVG，仅裁出底部时间线与编码信息区域。 -->
    <svg class="design-crop" viewBox="0 870 1920 210" preserveAspectRatio="none" aria-label="宋代时间线">
      <image :href="timelineUrl" x="0" y="0" width="1920" height="1080" />
    </svg>

    <!-- 交互层不重绘视觉，只把指针位置换算成 960—1279 年。 -->
    <input
      class="year-hit-area"
      type="range"
      min="960"
      max="1279"
      step="1"
      :value="modelValue"
      aria-label="选择当前年份"
      @input="emit('update:modelValue', Number($event.target.value))"
    />
    <div class="current-year" :style="markerStyle">
      <span>{{ modelValue }}年</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import * as d3 from "d3";

const props = defineProps({ modelValue: { type: Number, default: 1080 } });
const emit = defineEmits(["update:modelValue"]);
const timelineUrl = "/api/design/timeline.svg";

// 与原 SVG 年份轴的实际横坐标一致：960 年约 x=210，1279 年约 x=1559。
const x = d3.scaleLinear().domain([960, 1279]).range([10.94, 81.2]);
const markerStyle = computed(() => ({ left: `${x(props.modelValue)}%` }));
</script>

<style scoped>
.timeline-bar {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #f5f3ec;
}

.design-crop {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
}

.year-hit-area {
  position: absolute;
  left: 10.94%;
  right: 18.8%;
  bottom: 3%;
  width: 70.26%;
  height: 26%;
  margin: 0;
  opacity: 0.001;
  cursor: ew-resize;
}

.current-year {
  position: absolute;
  top: 6%;
  bottom: 3%;
  width: 1px;
  background: rgba(53, 23, 4, 0.72);
  pointer-events: none;
}

.current-year span {
  position: absolute;
  left: 50%;
  top: 0;
  transform: translate(-50%, -2px);
  padding: 1px 5px;
  border: 1px solid #563905;
  background: rgba(254, 254, 254, 0.92);
  color: #351704;
  font-size: 10px;
  white-space: nowrap;
}
</style>
