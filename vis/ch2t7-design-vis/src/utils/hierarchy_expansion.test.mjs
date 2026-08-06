import assert from "node:assert/strict";
import test from "node:test";

import {
  expansionAfterLayout,
  mergeExpansionPaths,
  removeExpandedSubtree,
} from "./hierarchy_expansion.js";

test("旧模式始终只保留刚点击节点的展开路径", () => {
  assert.deepEqual(mergeExpansionPaths([1, 2], [1, 3], false), [1, 3]);
});

test("空间展开模式合并两条分支且不重复共同祖先", () => {
  assert.deepEqual(mergeExpansionPaths([1, 2], [1, 3], true), [1, 2, 3]);
});

test("收起节点时只移除该节点及其已展开后代", () => {
  assert.deepEqual(removeExpandedSubtree([1, 2, 4, 3], [2, 4]), [1, 3]);
});

test("组合布局超出画布时回退到新分支，单支自身溢出仍保留", () => {
  assert.deepEqual(expansionAfterLayout({
    candidateIds: [1, 2, 3],
    fallbackPath: [1, 3],
    spaceAware: true,
    layoutFits: false,
  }), [1, 3]);
  assert.deepEqual(expansionAfterLayout({
    candidateIds: [1, 3],
    fallbackPath: [1, 3],
    spaceAware: true,
    layoutFits: false,
  }), [1, 3]);
});

test("组合布局在画布内时同时保留两个分支", () => {
  assert.deepEqual(expansionAfterLayout({
    candidateIds: [1, 2, 3],
    fallbackPath: [1, 3],
    spaceAware: true,
    layoutFits: true,
  }), [1, 2, 3]);
});
