import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCentralGroupNodes,
  centralGroupId,
  groupCentralRootIds,
  OTHER_CENTRAL_GROUP,
} from "./central_groups.js";

const entityMap = new Map([
  [1, { id: 1, title: "中书门下", central_group: "宰辅与决策中枢" }],
  [2, { id: 2, title: "尚书省", central_group: "三省六部与馆阁" }],
  [3, { id: 3, title: "未判机构", central_group: "" }],
]);

test("中央根节点按稳定制度组排序，未判项明确进入其他组", () => {
  assert.deepEqual(groupCentralRootIds([2, 3, 1], entityMap), [
    { group: "宰辅与决策中枢", rootIds: [1] },
    { group: "三省六部与馆阁", rootIds: [2] },
    { group: OTHER_CENTRAL_GROUP, rootIds: [3] },
  ]);
});

test("中央制度组默认收起且一次只展开指定组", () => {
  const nodes = buildCentralGroupNodes({
    rootIds: [1, 2],
    entityMap,
    expandedGroupId: centralGroupId("三省六部与馆阁"),
    treeForRoot: (id) => ({ id, title: entityMap.get(id).title }),
  });
  assert.equal(nodes[0].children.length, 0);
  assert.equal(nodes[0].hiddenCount, 1);
  assert.deepEqual(nodes[1].children, [{ id: 2, title: "尚书省" }]);
  assert.equal(nodes[1].hiddenCount, 0);
});
