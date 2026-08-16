import assert from "node:assert/strict";
import test from "node:test";

import {
  anchorBranchToGroup,
  fitRangeShift,
  horizontalRangesFit,
  panFromScrollbarOffset,
  panScrollbarGeometry,
  virtualBusRange,
} from "./hierarchy_layout.js";

test("展开的大机构锚定在所属制度组正下方", () => {
  const branchCenter = anchorBranchToGroup(620, 300, 650);
  assert.equal(branchCenter + 650 - 300, 620);
});

test("虚拟分组总线同时覆盖来源节点和全部目标节点", () => {
  assert.deepEqual(virtualBusRange(620, [970]), [620, 970]);
  assert.deepEqual(virtualBusRange(970, [620, 760]), [620, 970]);
});

test("下级子树利用可用宽度，不在左侧裁断后留下右侧空白", () => {
  assert.equal(fitRangeShift(380, 1280, 500, 1810), 120);
  assert.equal(fitRangeShift(620, 1920, 500, 1810), -110);
  assert.equal(fitRangeShift(620, 1280, 500, 1810), 0);
});

test("左右分类分支互不重叠且位于视口内时可同时展示", () => {
  assert.equal(horizontalRangesFit([
    { left: 520, right: 760 },
    { left: 1460, right: 1780 },
  ], 500, 1830), true);
  assert.equal(horizontalRangesFit([
    { left: 520, right: 960 },
    { left: 940, right: 1320 },
  ], 500, 1830), false);
  assert.equal(horizontalRangesFit([
    { left: 420, right: 760 },
  ], 500, 1830), false);
});

test("机构树溢出时滚动条覆盖完整平移范围", () => {
  const left = panScrollbarGeometry({
    viewportSize: 1000,
    contentSize: 2000,
    minPan: -1000,
    maxPan: 0,
    currentPan: 0,
  });
  const right = panScrollbarGeometry({
    viewportSize: 1000,
    contentSize: 2000,
    minPan: -1000,
    maxPan: 0,
    currentPan: -1000,
  });
  assert.equal(left.enabled, true);
  assert.equal(left.thumbSize, 500);
  assert.equal(left.thumbOffset, 0);
  assert.equal(right.thumbOffset, right.thumbTravel);
  assert.equal(panFromScrollbarOffset(right.thumbTravel, right.thumbTravel, -1000, 0), -1000);
});
