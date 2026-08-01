<template>
  <div class="timeline-shell">
    <div ref="root" class="timeline-root" aria-label="公元960年至1279年宋代官制时间线"></div>
    <button
      v-if="selectionActive"
      type="button"
      class="clear-selection"
      title="取消当前时间段选择，恢复显示全宋"
      @click="emit('cancel-selection')"
    >
      × 取消选择
    </button>
  </div>
</template>

<script setup>
// 时间轴复刻 CBDB-Migration-Map src/components/TimeLine.vue 的样式：
// 固定 2560 内部画幅 + viewBox 缩放；左侧控制栏（年 / 朝代 / 官制事件三行标签）、
// 顶部年刻度轴、朝代分隔带、事件刻度行、底部粗拖动轴 + 实心刷选框。
// 对外接口：props.years / props.range / props.selectionActive，
// emit("change-range", [start, end]) 或 emit("cancel-selection")。
import * as d3 from "d3";
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  years: { type: Array, required: true },
  range: { type: Array, required: true },
  selectionActive: { type: Boolean, default: true },
});
const emit = defineEmits(["change-range", "cancel-selection"]);

const root = ref(null);
let resizeObserver;
let brushGroup;
let brush;
let yearScale;

// —— 与 CBDB TimeLine 一致的画幅与布局参数 ——
const WIDTH = 2560;
// 保持时间线有效高度不变，将原先底部多余的留白移到顶部，让整组内容下移。
const MARGIN = { top: 0.2, left: 0.02, right: 0.02, bottom: 0.13 };
const YEAR_START = 960;
const YEAR_END = 1280; // 比例尺右端 = 最后一年 1279 + 1
const YEAR_STEP = 10;
const RW = 10; // 拖动轴刷选条半高

// —— CBDB 调色板 ——
const INK = "#6a4c2a"; // 主墨色：轴线、标签方块、拖动轴
const INK_TEXT = "#5a3a20"; // 年刻度文字
const INK_ALT = "#6e4d2b"; // 朝代 / 事件文字
const LINE = "#ad9278"; // 分隔线、刻度线
const EVENT_TICK = "#ac9176"; // 事件刻度
const BRUSH_FILL = "#a78d73"; // 刷选框填充
const FONT = "FZQINGKBYSJF";

const FIRST_YEAR = 960;
const LAST_YEAR = 1279;

function draw() {
  if (!root.value) return;
  const sWidth = root.value.clientWidth;
  const sHeight = root.value.clientHeight || 172;
  if (!sWidth) return;

  const width = WIDTH;
  const height = (sHeight / sWidth) * width;
  const ih = height * (1 - MARGIN.top - MARGIN.bottom);
  const iw = width * (1 - MARGIN.left - MARGIN.right);
  const cw = iw / 10; // 控制栏总宽度
  const gap = ih / 15; // 分割线与文字分隔竖线之间的距离
  const divloc = ih / 3; // 分割线起始位置
  const th = (ih * 3) / 15; // 文字分割线高度

  d3.select(root.value).selectAll("*").remove();
  const svg = d3
    .select(root.value)
    .append("svg")
    .attr("width", sWidth)
    .attr("height", sHeight)
    .attr("viewBox", `0 0 ${width} ${height}`);
  const container = svg
    .append("g")
    .attr("transform", `translate(${width * MARGIN.left}, ${height * MARGIN.top})`);

  yearScale = d3.scaleLinear().domain([YEAR_START, YEAR_END]).range([cw, iw]);
  const yearWidth = yearScale(YEAR_START + 1) - yearScale(YEAR_START);

  // ------------------------------------------------------------------
  // 控制栏：上下分隔线（仅控制栏宽度）
  // ------------------------------------------------------------------
  container.append("line")
    .attr("transform", "translate(0, 1.5)")
    .attr("stroke", INK)
    .attr("stroke-width", 1.5)
    .attr("x1", 0)
    .attr("x2", cw - 2 * gap);
  container.append("line")
    .attr("transform", `translate(0, ${ih})`)
    .attr("stroke", INK)
    .attr("stroke-width", 1.5)
    .attr("x1", 0)
    .attr("x2", cw - 2 * gap);

  // 控制栏：三个行标签（实心方块 + 文字）
  const rowLabels = [
    { text: "年", y: 0, fill: INK },
    { text: "朝代·帝系", y: divloc, fill: INK },
    { text: "官制事件", y: 2 * divloc, fill: INK_ALT },
  ];
  const labelG = container
    .selectAll("g.row-label")
    .data(rowLabels)
    .join("g")
    .attr("class", "row-label");
  labelG
    .append("rect")
    .attr("x", 0)
    .attr("y", (d) => divloc / 4 + d.y)
    .attr("width", divloc / 4)
    .attr("height", divloc / 4)
    .attr("stroke", (d) => d.fill)
    .attr("fill", (d) => d.fill);
  labelG
    .append("text")
    .attr("x", divloc / 2)
    .attr("y", (d) => d.y + divloc / 2)
    .style("fill", (d) => d.fill)
    .attr("font-size", 18)
    .attr("font-family", FONT)
    .text((d) => d.text);

  // ------------------------------------------------------------------
  // 年刻度轴：axisBottom 置于顶部，刻度向下
  // ------------------------------------------------------------------
  const tickValues = d3.range(YEAR_START, YEAR_END + YEAR_STEP, YEAR_STEP);
  const isMajor = (d) => d % 100 === 0 || d === YEAR_START || d === YEAR_END;
  container
    .append("g")
    .call(d3.axisBottom(yearScale).tickValues(tickValues).tickFormat((d) => d))
    .call((g) => {
      g.select(".domain")
        .attr("stroke", INK)
        .attr("stroke-width", 2)
        .attr("transform", "translate(0, 1.5)");
      g.selectAll(".tick line").remove();
      g.selectAll(".tick")
        .append("line")
        .attr("stroke", LINE)
        .attr("y2", (d) => (isMajor(d) ? 18 : 8))
        .attr("stroke-width", 1);
      g.selectAll(".tick text")
        .attr("font-size", (d) => (isMajor(d) ? 15 : 12))
        .attr("dy", (d) => (isMajor(d) ? 13 : 5))
        .attr("fill", INK_TEXT)
        .attr("font-family", FONT)
        .attr("alignment-baseline", "hanging");
    });

  // ------------------------------------------------------------------
  // 朝代行：分割线 + 各朝代起点竖线 + 居中朝代名
  // ------------------------------------------------------------------
  container
    .append("g")
    .attr("transform", `translate(0, ${divloc})`)
    .call((g) => {
      g.append("line")
        .attr("stroke", LINE)
        .attr("x1", cw)
        .attr("x2", iw)
        .attr("stroke-width", 0.8);
    });

  const dynasties = [
    { name: "北宋", start: 960, end: 1127 },
    { name: "南宋", start: 1127, end: 1280 },
  ];
  container
    .append("g")
    .selectAll("g")
    .data(dynasties)
    .join("g")
    .attr("transform", (d) => `translate(${yearScale(d.start)}, 0)`)
    .call((g) => {
      g.append("line")
        .attr("transform", `translate(0, ${divloc + gap})`)
        .attr("stroke", LINE)
        .attr("y2", th)
        .attr("stroke-width", 0.8);
      g.append("text")
        .attr("transform", `translate(3, ${divloc + gap + 1})`)
        .text((d) => d.name)
        .attr("x", (d) => 0.5 * (yearScale(d.end) - yearScale(d.start)) - 3)
        .attr("y", 0)
        .attr("font-family", FONT)
        .attr("font-size", 13)
        .attr("fill", INK_ALT)
        .attr("alignment-baseline", "hanging")
        .attr("text-anchor", "middle");
    });

  // 帝系：朝代行下半部分按皇帝执政分段，窄段省略名字（悬停可见）
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
  const empTop = divloc + gap + th * 0.42;
  const empBottom = divloc + gap + th;
  const emperorG = container
    .append("g")
    .selectAll("g")
    .data(EMPERORS)
    .join("g")
    .attr("transform", (d) => `translate(${yearScale(d.start)}, 0)`);
  emperorG
    .append("rect")
    .attr("y", empTop)
    .attr("width", (d) => yearScale(d.end) - yearScale(d.start))
    .attr("height", empBottom - empTop)
    .attr("fill", (_, i) => (i % 2 ? "rgba(106, 74, 42, 0.045)" : "rgba(106, 74, 42, 0.1)"));
  emperorG
    .append("line")
    .attr("transform", `translate(0, ${empTop})`)
    .attr("stroke", LINE)
    .attr("y2", empBottom - empTop)
    .attr("stroke-width", 0.8);
  emperorG
    .filter((d) => yearScale(d.end) - yearScale(d.start) >= 26)
    .append("text")
    .attr("x", (d) => 0.5 * (yearScale(d.end) - yearScale(d.start)))
    .attr("y", empTop + 2.5)
    .attr("font-family", FONT)
    .attr("font-size", 11.5)
    .attr("fill", INK_ALT)
    .attr("alignment-baseline", "hanging")
    .attr("text-anchor", "middle")
    .text((d) => d.name);
  emperorG
    .append("title")
    .text((d) => `${d.name} ${d.start}—${Math.min(d.end - 1, 1279)}年在位`);

  // 朝代行与事件行之间的分割线
  const eventRowY = divloc + gap * 2 + th;
  container
    .append("g")
    .attr("transform", `translate(0, ${eventRowY})`)
    .call((g) => {
      g.append("line")
        .attr("stroke", LINE)
        .attr("x1", cw)
        .attr("x2", iw)
        .attr("stroke-width", 0.8);
    });

  // ------------------------------------------------------------------
  // 官制事件行：每年一根刻度，长度随当年记录数变化；点击刻度定位到该年
  // ------------------------------------------------------------------
  const maxCount = d3.max(props.years, (d) => d.count) || 1;
  const tickLength = (count) =>
    count > 0 ? th / 12 + (th / 2 - th / 12) * Math.sqrt(count / maxCount) : 0;

  const yearTick = container
    .append("g")
    .attr("class", "event-ticks")
    .selectAll("g")
    .data(props.years)
    .join("g")
    .attr("transform", (d) => `translate(${yearScale(d.year)}, 0)`)
    .style("cursor", (d) => (d.count ? "pointer" : "default"))
    .on("click", (_, d) => {
      if (d.count) emit("change-range", [d.year, d.year]);
    });
  yearTick
    .append("line")
    .attr("transform", `translate(0, ${eventRowY})`)
    .attr("stroke", EVENT_TICK)
    .attr("y2", (d) => tickLength(d.count))
    .attr("stroke-width", 1.5);
  yearTick
    .append("rect")
    .attr("x", -yearWidth / 2)
    .attr("y", eventRowY)
    .attr("width", yearWidth)
    .attr("height", Math.max(th / 2, ih - eventRowY - RW))
    .attr("fill", "transparent");
  yearTick
    .append("title")
    .text((d) => `${d.year}年：${d.count}条精确纪年记录`);

  // 标志性事件（朝代行与事件行之下、拖动轴之上的文字标注）
  const landmarks = [
    { year: 960, label: "北宋建立", anchor: "start", dx: 3 },
    { year: 1127, label: "宋室南渡", anchor: "middle", dx: 0 },
    { year: 1279, label: "宋亡", anchor: "end", dx: -3 },
  ];
  container
    .append("g")
    .selectAll("g")
    .data(landmarks)
    .join("g")
    .attr("transform", (d) => `translate(${yearScale(d.year)}, 0)`)
    .call((g) => {
      g.append("text")
        .attr("transform", `translate(0, ${divloc + gap * 4 + th + th / 4})`)
        .text((d) => d.label)
        .attr("x", (d) => d.dx)
        .attr("y", -10)
        .attr("font-size", 18)
        .attr("fill", INK_ALT)
        .attr("alignment-baseline", "hanging")
        .attr("font-family", FONT)
        .attr("text-anchor", (d) => d.anchor);
    });

  // ------------------------------------------------------------------
  // 拖动轴 + 刷选
  // ------------------------------------------------------------------
  container
    .append("line")
    .attr("transform", `translate(0, ${ih})`)
    .attr("x1", cw)
    .attr("x2", iw)
    .attr("stroke", INK)
    .attr("stroke-width", 2);

  brush = d3.brushX().extent([
    [cw, ih - RW / 2],
    [iw, ih + RW / 2],
  ]);
  brushGroup = container.append("g").call(brush);

  // 加大 overlay 高度，方便点击与触摸
  brushGroup
    .select(".overlay")
    .attr("y", brushGroup.select(".overlay").attr("y") - 50)
    .attr("height", 100);

  brushGroup
    .select(".selection")
    .attr("fill", BRUSH_FILL)
    .attr("fill-opacity", 1)
    .attr("stroke", INK)
    .attr("stroke-width", 1);

  brush.on("end", (event) => {
    if (!event.sourceEvent) return; // 程序性移动不处理
    const x = d3.pointer(event.sourceEvent, container.node())[0];
    const year = Math.max(FIRST_YEAR, Math.min(LAST_YEAR, Math.round(yearScale.invert(x))));
    moveBrush([year, year]);
    emit("change-range", [year, year]);
  });

  moveBrush(props.selectionActive ? props.range : null);
}

// 把刷选框移动到指定年份区间（[start, end] 为闭区间）
function moveBrush(range) {
  if (!brushGroup || !yearScale || !brush) return;
  if (!range) {
    brushGroup.call(brush.move, null);
    return;
  }
  const [start, end] = range;
  brushGroup.call(brush.move, [
    yearScale(start),
    yearScale(Math.min(end + 1, YEAR_END)),
  ]);
}

watch(
  () => [props.range, props.selectionActive],
  ([range, selectionActive]) => nextTick(() => moveBrush(selectionActive ? range : null)),
  { deep: true }
);
watch(
  () => props.years,
  () => nextTick(draw),
  { deep: true }
);

onMounted(() => {
  draw();
  resizeObserver = new ResizeObserver(draw);
  resizeObserver.observe(root.value);
});

onBeforeUnmount(() => resizeObserver?.disconnect());
</script>

<style scoped>
.timeline-shell {
  position: relative;
  width: 100%;
  height: 100%;
}

.timeline-root {
  width: 100%;
  height: 100%;
  overflow: hidden;
  user-select: none;
}

.clear-selection {
  position: absolute;
  z-index: 3;
  top: 5px;
  right: 2vw;
  height: 23px;
  border: 1px solid rgba(114, 74, 43, 0.46);
  border-radius: 3px;
  padding: 0 8px;
  color: rgba(90, 58, 32, 0.72);
  background: rgba(244, 241, 234, 0.9);
  font-family: "FZQINGKBYSJF", serif;
  font-size: 10px;
  cursor: pointer;
}

.clear-selection:hover {
  border-color: var(--ink-soft);
  color: var(--ink-soft);
  background: var(--paper);
}

:deep(.timeline-root .overlay) {
  cursor: crosshair;
}
</style>
