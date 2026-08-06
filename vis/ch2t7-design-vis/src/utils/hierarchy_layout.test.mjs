import assert from "node:assert/strict";
import test from "node:test";

import { anchorBranchToGroup, virtualBusRange } from "./hierarchy_layout.js";

test("展开的大机构锚定在所属制度组正下方", () => {
  const branchCenter = anchorBranchToGroup(620, 300, 650);
  assert.equal(branchCenter + 650 - 300, 620);
});

test("虚拟分组总线同时覆盖来源节点和全部目标节点", () => {
  assert.deepEqual(virtualBusRange(620, [970]), [620, 970]);
  assert.deepEqual(virtualBusRange(970, [620, 760]), [620, 970]);
});
