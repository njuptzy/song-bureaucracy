import assert from "node:assert/strict";
import test from "node:test";

import {
  nodeChangeIndicatorAriaLabel,
  nodeChangeIndicatorItems,
  nodeChangeIndicatorLayout,
} from "./node_change_indicator.js";

test("节点变化标记只保留过去和未来，不显示同年数量", () => {
  const summary = {
    past: { year: 1070, distance: 10 },
    current: { year: 1080, count: 3 },
    future: { year: 1095, distance: 15 },
  };
  assert.deepEqual(nodeChangeIndicatorItems(summary).map(({ kind, label }) => ({ kind, label })), [
    { kind: "past", label: "前10" },
    { kind: "future", label: "后15" },
  ]);
  assert.equal(nodeChangeIndicatorItems({ current: summary.current }).length, 0);
  assert.equal(
    nodeChangeIndicatorAriaLabel("三司", summary),
    "三司前后结构变化：最近过去变化在1070年，相距10年；最近未来变化在1095年，相距15年",
  );
});

test("左右标记使用可读文字块并保持固定间距", () => {
  const layout = nodeChangeIndicatorLayout([
    { kind: "past", label: "前2" },
    { kind: "future", label: "后120" },
  ]);
  assert.equal(layout.height, 14);
  assert.ok(layout.items[0].width >= 24);
  assert.ok(layout.items[1].width > layout.items[0].width);
  assert.equal(layout.items[1].x, layout.items[0].width + 3);
  assert.equal(layout.width, layout.items[1].x + layout.items[1].width);
});
