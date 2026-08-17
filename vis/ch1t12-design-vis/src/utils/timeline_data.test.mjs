import assert from "node:assert/strict";
import test from "node:test";
import {
  buildTimelineYearTicks,
  normalizeTimelineEras,
  timelineEraForYear,
} from "./timeline_data.js";

test("时间轴直接使用服务端年号范围，不从文字猜测", () => {
  const eras = normalizeTimelineEras([
    { name: "元丰", start: 1078, end: 1085 },
    { name: "建隆", start: 960, end: 963 },
  ]);
  assert.deepEqual(eras.map(({ name, start, end }) => ({ name, start, end })), [
    { name: "建隆", start: 960, end: 963 },
    { name: "元丰", start: 1078, end: 1085 },
  ]);
  assert.equal(timelineEraForYear(1080, eras)?.name, "元丰");
});

test("交界年沿用服务端表的年末截面顺序", () => {
  const eras = [
    { name: "政和", start: 1111, end: 1118 },
    { name: "重和", start: 1118, end: 1118 },
  ];
  assert.equal(timelineEraForYear(1118, eras)?.name, "重和");
});

test("年份刻度以服务端实际范围为边界", () => {
  assert.deepEqual(buildTimelineYearTicks(960, 1279, 10).slice(-3), [1260, 1270, 1279]);
});

