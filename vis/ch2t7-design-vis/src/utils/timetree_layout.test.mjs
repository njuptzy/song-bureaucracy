import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  clampTimetreeScroll,
  layoutTimetreeEvents,
  layoutTimetreeRelations,
  layoutTimetreeSegments,
  TIMETREE_GEOMETRY,
  timetreeNodeX,
  timetreeRowY,
  timetreeYearToX,
} from "./timetree_layout.js";

describe("timetreeYearToX", () => {
  it("起止年映射到时间区两端", () => {
    assert.equal(timetreeYearToX(960, 960, 1279), TIMETREE_GEOMETRY.plot.x0);
    assert.equal(timetreeYearToX(1279, 960, 1279), TIMETREE_GEOMETRY.plot.x1);
  });
});

describe("clampTimetreeScroll", () => {
  it("行数不足一屏时锁死在 0", () => {
    assert.equal(clampTimetreeScroll(50, 3), 0);
  });

  it("超长内容钳制在最大偏移内", () => {
    const maxOffset = 100 * TIMETREE_GEOMETRY.rowPitch
      - (TIMETREE_GEOMETRY.rowsBottom - TIMETREE_GEOMETRY.rowsTop);
    assert.equal(clampTimetreeScroll(99999, 100), maxOffset);
    assert.equal(clampTimetreeScroll(-5, 100), 0);
  });
});

describe("timetreeRowY / timetreeNodeX", () => {
  it("行 y 随滚动偏移线性移动", () => {
    const base = timetreeRowY(0, 0);
    assert.equal(base, TIMETREE_GEOMETRY.rowsTop + TIMETREE_GEOMETRY.rowPitch / 2);
    assert.equal(timetreeRowY(0, 20), base - 20);
    assert.equal(timetreeRowY(3, 0), base + 3 * TIMETREE_GEOMETRY.rowPitch);
  });

  it("树节点 x 随深度右移且不超过树区右界", () => {
    assert.equal(timetreeNodeX(0), TIMETREE_GEOMETRY.tree.x0);
    assert.ok(timetreeNodeX(99) <= TIMETREE_GEOMETRY.tree.maxX);
  });
});

describe("layoutTimetreeEvents", () => {
  const xOf = (year) => timetreeYearToX(year, 960, 1279);

  it("事件 displayX 锚在真实年份上，密集点错层", () => {
    const events = layoutTimetreeEvents([
      { id: 1, effectiveYear: 1000, yearStart: 1000, yearEnd: 1000, timeType: "exact" },
      { id: 2, effectiveYear: 1000.5, yearStart: 1000, yearEnd: 1001, timeType: "bounded" },
      { id: 3, effectiveYear: 1100, yearStart: 1100, yearEnd: 1100, timeType: "exact" },
    ], xOf);
    assert.equal(events[0].baseX, xOf(1000));
    assert.equal(events[0].dy, 0);
    assert.notEqual(events[1].dy, 0);
    assert.ok(events[1].displaced);
    assert.equal(events[2].dy, 0);
  });

  it("离轴事件（无有效年份）不参与布局", () => {
    const events = layoutTimetreeEvents([
      { id: 1, effectiveYear: null, timeType: "undated" },
    ], xOf);
    assert.equal(events.length, 0);
  });
});

describe("layoutTimetreeSegments / layoutTimetreeRelations", () => {
  const xOf = (year) => timetreeYearToX(year, 960, 1279);

  it("存续段映射为 x 区间", () => {
    const [segment] = layoutTimetreeSegments([
      { id: "s1", startYear: 1000, endYear: 1100, openStart: false, openEnd: true },
    ], xOf);
    assert.equal(segment.x0, xOf(1000));
    assert.equal(segment.x1, xOf(1100));
  });

  it("关系端点定位到已布局事件；缺端点的关系不可画", () => {
    const positions = new Map([
      [11, { x: 100, y: 200, iconType: "record" }],
      [12, { x: 300, y: 300, iconType: "establish" }],
    ]);
    const [ok, missing] = layoutTimetreeRelations([
      {
        id: 1,
        sourceMembers: [{ timepointId: 11, entityId: 1 }],
        targetMembers: [{ timepointId: 12, entityId: 2 }],
      },
      {
        id: 2,
        sourceMembers: [{ timepointId: 99, entityId: 3 }],
        targetMembers: [{ timepointId: 12, entityId: 2 }],
      },
    ], positions);
    assert.ok(ok.drawable);
    assert.equal(ok.sourcePoints[0].x, 100);
    assert.equal(ok.targetPoints[0].y, 300);
    assert.ok(!missing.drawable);
  });
});
