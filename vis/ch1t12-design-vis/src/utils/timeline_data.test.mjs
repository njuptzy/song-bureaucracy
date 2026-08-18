import assert from "node:assert/strict";
import test from "node:test";
import {
  buildTimelineYearTicks,
  layoutTimelineEraLabels,
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

test("过短年号隐藏文字但保留真实时间段", () => {
  const eras = [
    { name: "建隆", start: 960, end: 963 },
    { name: "开宝", start: 968, end: 976 },
  ];
  const layout = layoutTimelineEraLabels(eras, (year) => year * 4, {
    fontSize: 10,
    padding: 2,
  });
  assert.equal(layout[0].labelVisible, false);
  assert.equal(layout[0].labelHiddenReason, "short-range");
  assert.equal(layout[0].durationYears, 4);
  assert.equal(layout[0].startX, 3840);
  assert.equal(layout[0].endX, 3856);
  assert.equal(layout[1].labelVisible, true);
  assert.equal(layout[1].labelX, (3872 + 3908) / 2);
  assert.equal(layout[1].labelText, "开宝");
});

test("达到固定年限后不因年号字数隐藏，过长文字只截成省略号", () => {
  const layout = layoutTimelineEraLabels([
    { name: "甲乙丙丁", start: 1, end: 5 },
  ], (year) => year * 4, {
    minYears: 5,
    fontSize: 10,
    padding: 2,
  });
  assert.equal(layout[0].durationYears, 5);
  assert.equal(layout[0].labelVisible, true);
  assert.equal(layout[0].labelText, "…");
});

test("可见年号在自己的时间格内，不与相邻文字相撞", () => {
  const eras = [
    { name: "甲", start: 1, end: 10 },
    { name: "乙", start: 11, end: 20 },
  ];
  const layout = layoutTimelineEraLabels(eras, (year) => year * 10, {
    fontSize: 10,
    padding: 2,
  });
  for (const item of layout) {
    assert.equal(item.labelVisible, true);
    assert.ok(item.labelX - item.labelWidth / 2 >= item.labelSlotStartX);
    assert.ok(item.labelX + item.labelWidth / 2 <= item.labelSlotEndX);
  }
  assert.ok(
    layout[1].labelX - layout[1].labelWidth / 2
      > layout[0].labelX + layout[0].labelWidth / 2,
  );
});
