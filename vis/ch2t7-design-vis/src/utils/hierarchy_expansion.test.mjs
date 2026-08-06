import assert from "node:assert/strict";
import test from "node:test";

import {
  collapseInstitutionGroups,
  expansionAfterLayout,
  expansionAnchorId,
  institutionGroupsAfterLayout,
  isRepeatedHierarchyPointer,
  mergeExpansionPaths,
  removeExpandedSubtree,
  toggleInstitutionGroupIds,
} from "./hierarchy_expansion.js";

test("同一机构的第二次按下可跨节点重绘识别为双击", () => {
  const previous = { id: 12, timeStamp: 1000 };
  assert.equal(isRepeatedHierarchyPointer(previous, 12, 1500), true);
  assert.equal(isRepeatedHierarchyPointer(previous, 13, 1500), false);
  assert.equal(isRepeatedHierarchyPointer(previous, 12, 1700), false);
  assert.equal(isRepeatedHierarchyPointer(previous, 12, 900), false);
});

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

test("空间展开按全部分支整体居中，不再锚定第一个节点", () => {
  assert.equal(expansionAnchorId([1, 2], false), 1);
  assert.equal(expansionAnchorId([1, 2], true), null);
});

test("旧模式的顶部虚拟分类仍然只展开新点击项", () => {
  assert.deepEqual(toggleInstitutionGroupIds(["left"], "right", false), ["right"]);
});

test("空间模式允许同时展开左右两个虚拟分类", () => {
  assert.deepEqual(toggleInstitutionGroupIds(["left"], "right", true), ["left", "right"]);
});

test("多个虚拟分类放不下时回退到新点击分类", () => {
  assert.deepEqual(institutionGroupsAfterLayout({
    candidateIds: ["left", "right"],
    clickedId: "right",
    spaceAware: true,
    layoutFits: false,
  }), ["right"]);
  assert.deepEqual(institutionGroupsAfterLayout({
    candidateIds: ["right"],
    clickedId: "right",
    spaceAware: true,
    layoutFits: false,
  }), ["right"]);
});

test("关闭空间模式后只保留最近展开的虚拟分类", () => {
  assert.deepEqual(collapseInstitutionGroups(["left", "right"], "right"), ["right"]);
});
