<template>
  <div ref="wrapRef" class="timeline-bar">
    <svg ref="svgRef"></svg>
    <input
      class="year-slider"
      type="range"
      min="960"
      max="1279"
      step="1"
      :value="modelValue"
      aria-label="当前公元年份"
      @input="emit('update:modelValue', Number($event.target.value))"
    />
    <div class="year-readout" :style="readoutStyle">{{ modelValue }}年</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import * as d3 from "d3";

const props = defineProps({ modelValue: { type: Number, default: 1080 } });
const emit = defineEmits(["update:modelValue"]);

// 与 vis/song-bureaucracy-visualization-v2/src/components/SongTimeline.vue 一致
const EMPERORS = [
  { name: "太祖", start: 960, end: 976 },
  { name: "太宗", start: 976, end: 997 },
  { name: "真宗", start: 997, end: 1022 },
  { name: "仁宗", start: 1022, end: 1063 },
  { name: "英宗", start: 1063, end: 1067 },
  { name: "神宗", start: 1067, end: 1085 },
  { name: "哲宗", start: 1085, end: 1100 },
  { name: "徽宗", start: 1100, end: 1126 },
  { name: "钦宗", start: 1126, end: 1127 },
  { name: "高宗", start: 1127, end: 1162 },
  { name: "孝宗", start: 1162, end: 1189 },
  { name: "光宗", start: 1189, end: 1194 },
  { name: "宁宗", start: 1194, end: 1224 },
  { name: "理宗", start: 1224, end: 1264 },
  { name: "度宗", start: 1264, end: 1274 },
  { name: "恭帝", start: 1274, end: 1276 },
  { name: "端宗", start: 1276, end: 1278 },
  { name: "少帝", start: 1278, end: 1280 },
];

// 设计稿图例「官职类分类」四色
const OFFICIAL_KINDS = [
  { kind: "差遣官", color: "#a5a68d" },
  { kind: "职事官", color: "#918069" },
  { kind: "阶官", color: "#866d6d" },
  { kind: "吏", color: "#c3c3c3" },
];
// 设计稿图例「机构」按名称级别：省 / 部 / 司 / 案及以下
const ORG_LEVELS = ["省", "部", "司", "案及以下"];

const INK = "#351704";
const INK2 = "#563905";
const OLIVE = "#918069";

const wrapRef = ref(null);
const svgRef = ref(null);
const readoutStyle = computed(() => ({
  left: `calc(56px + (100% - 372px) * ${(props.modelValue - 960) / 319})`,
}));

onMounted(() => {
  const wrap = wrapRef.value;
  const W = wrap.clientWidth;
  const H = wrap.clientHeight;
  const legendW = 300;
  const margin = { left: 56, right: legendW + 16 };
  const iw = W - margin.left - margin.right;

  const svg = d3.select(svgRef.value).attr("width", W).attr("height", H);
  const g = svg.append("g").attr("transform", `translate(${margin.left}, 0)`);

  const x = d3.scaleLinear().domain([960, 1279]).range([0, iw]);

  const bandTop = 12;
  const bandH = 26;
  const axisY = H - 34;

  // 行标签（朝代 / 年份）
  const labels = svg.append("g");
  labels
    .append("text")
    .attr("x", margin.left - 10)
    .attr("y", bandTop + bandH / 2 + 4)
    .attr("text-anchor", "end")
    .attr("font-size", 12)
    .attr("fill", INK)
    .text("朝代");
  labels
    .append("text")
    .attr("x", margin.left - 10)
    .attr("y", axisY + 22)
    .attr("text-anchor", "end")
    .attr("font-size", 12)
    .attr("fill", INK)
    .text("年份");

  // 帝系分段
  const emp = g.append("g").selectAll("g").data(EMPERORS).join("g");
  emp
    .append("rect")
    .attr("x", (d) => x(d.start))
    .attr("y", bandTop)
    .attr("width", (d) => x(d.end) - x(d.start))
    .attr("height", bandH)
    .attr("fill", (_, i) => (i % 2 ? "rgba(86, 57, 5, 0.05)" : "rgba(86, 57, 5, 0.12)"))
    .attr("stroke", "rgba(86, 57, 5, 0.3)")
    .attr("stroke-width", 0.5);
  emp
    .filter((d) => x(d.end) - x(d.start) >= 24)
    .append("text")
    .attr("x", (d) => (x(d.start) + x(d.end)) / 2)
    .attr("y", bandTop + bandH / 2 + 4)
    .attr("text-anchor", "middle")
    .attr("font-size", 11.5)
    .attr("fill", INK)
    .text((d) => d.name);
  emp
    .append("title")
    .text((d) => `${d.name} ${d.start}—${Math.min(d.end - 1, 1279)}年在位`);

  // 1127 南北宋分界
  g.append("line")
    .attr("x1", x(1127))
    .attr("x2", x(1127))
    .attr("y1", 4)
    .attr("y2", axisY)
    .attr("stroke", "#a03c28")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "4 3");
  g.append("text")
    .attr("x", x(1127) + 4)
    .attr("y", 12)
    .attr("font-size", 10)
    .attr("fill", "#a03c28")
    .text("1127 南渡");

  // 年份刻度尺（每 10 年刻度，20 年标字）
  g.append("line")
    .attr("x1", 0)
    .attr("x2", iw)
    .attr("y1", axisY)
    .attr("y2", axisY)
    .attr("stroke", INK2)
    .attr("stroke-opacity", 0.6)
    .attr("stroke-width", 0.8);
  for (let yr = 960; yr <= 1280; yr += 10) {
    const major = yr % 20 === 0;
    g.append("line")
      .attr("x1", x(yr))
      .attr("x2", x(yr))
      .attr("y1", axisY)
      .attr("y2", axisY + (major ? 6 : 3))
      .attr("stroke", INK2)
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 0.8);
    if (major) {
      g.append("text")
        .attr("x", x(yr))
        .attr("y", axisY + 17)
        .attr("text-anchor", "middle")
        .attr("font-size", 9.5)
        .attr("fill", INK2)
        .text(yr + "年");
    }
  }

  // ---- 编码信息（设计稿右下角图例） ----
  const lg = svg.append("g").attr("transform", `translate(${W - legendW}, 6)`);
  lg.append("text").attr("font-size", 13).attr("font-weight", 700).attr("fill", INK).text("编码信息");
  lg
    .append("line")
    .attr("x1", 0)
    .attr("x2", legendW - 12)
    .attr("y1", 6)
    .attr("y2", 6)
    .attr("stroke", INK2)
    .attr("stroke-opacity", 0.5);

  // 机构级别（书脊宽度递减）
  ORG_LEVELS.forEach((t, i) => {
    const gg = lg.append("g").attr("transform", `translate(${10 + i * 34}, 16)`);
    gg
      .append("rect")
      .attr("x", -7)
      .attr("y", 0)
      .attr("width", 14)
      .attr("height", 44 - i * 4)
      .attr("fill", "rgba(254,254,254,0.55)")
      .attr("stroke", OLIVE)
      .attr("stroke-width", 0.75);
    gg
      .append("rect")
      .attr("x", -3)
      .attr("y", -5)
      .attr("width", 6)
      .attr("height", 6)
      .attr("fill", "#a5a68d")
      .attr("fill-opacity", 0.6)
      .attr("stroke", INK2)
      .attr("stroke-width", 0.6);
    gg
      .append("text")
      .attr("y", 58)
      .attr("text-anchor", "middle")
      .attr("font-size", 9.5)
      .attr("fill", INK2)
      .text(t);
  });

  // 官职类分类
  OFFICIAL_KINDS.forEach((k, i) => {
    const gg = lg.append("g").attr("transform", `translate(${170 + (i % 2) * 62}, ${22 + Math.floor(i / 2) * 26})`);
    gg
      .append("rect")
      .attr("x", 0)
      .attr("y", -7)
      .attr("width", 9)
      .attr("height", 9)
      .attr("fill", k.color)
      .attr("fill-opacity", 0.85)
      .attr("stroke", INK2)
      .attr("stroke-width", 0.6);
    gg.append("text").attr("x", 14).attr("y", 1).attr("font-size", 10).attr("fill", INK2).text(k.kind);
  });

  lg
    .append("text")
    .attr("y", 92)
    .attr("font-size", 9.5)
    .attr("fill", INK2)
    .attr("opacity", 0.85)
    .text("数据来源：《宋代官制辞典》二至七编结构化库（ch2t7）");
});
</script>

<style scoped>
.timeline-bar {
  position: relative;
  width: 100%;
  height: 100%;
  background: rgba(254, 254, 254, 0.45);
}

.year-slider {
  position: absolute;
  left: 56px;
  right: 316px;
  bottom: 19px;
  width: calc(100% - 372px);
  height: 24px;
  margin: 0;
  opacity: 0.01;
  cursor: ew-resize;
}

.year-readout {
  position: absolute;
  top: 45px;
  transform: translateX(-50%);
  padding: 1px 5px;
  border: 1px solid var(--ink-2);
  background: rgba(254, 254, 254, 0.9);
  color: var(--ink);
  font-size: 11px;
  pointer-events: none;
  white-space: nowrap;
}

.year-readout::after {
  content: "";
  position: absolute;
  left: 50%;
  top: 100%;
  width: 1px;
  height: 27px;
  background: var(--ink-2);
  opacity: 0.75;
}

svg {
  display: block;
}
</style>
