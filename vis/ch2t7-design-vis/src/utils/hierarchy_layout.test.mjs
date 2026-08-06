import assert from "node:assert/strict";
import test from "node:test";

import {
  anchorBranchToGroup,
  fitRangeShift,
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
