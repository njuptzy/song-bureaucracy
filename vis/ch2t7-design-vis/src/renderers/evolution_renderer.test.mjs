import assert from "node:assert/strict";
import test from "node:test";

import { eventStemGeometry, relationPath } from "./evolution_renderer.js";

function endpoint(x, y, iconType = "record") {
  return { x, y, timepointId: `${x}:${y}`, iconType };
}

test("关系箭头停在时间点图形外缘而不是中心", () => {
  const path = relationPath(endpoint(100, 100), endpoint(200, 100, "abolish"));
  const numbers = path.match(/-?\d+(?:\.\d+)?/g).map(Number);

  assert.equal(numbers[0], 103.1);
  assert.equal(numbers.at(-2), 194.2);
  assert.equal(numbers.at(-1), 100);
  assert.equal(numbers.at(-3), 100);
});

test("跨轨关系箭头沿目标图标中心线进入而不是指向轨道线", () => {
  const path = relationPath(endpoint(100, 160), endpoint(100, 80, "abolish"));
  const numbers = path.match(/-?\d+(?:\.\d+)?/g).map(Number);

  assert.equal(numbers[1], 156.9);
  assert.equal(numbers.at(-2), 100);
  assert.equal(numbers.at(-1), 85.8);
  assert.equal(numbers.at(-3), 103.4);
  assert.equal(numbers.at(-4), 100);
});

test("普通圆点端精确接到空心圆外沿，不重叠也不留断口", () => {
  const path = relationPath(endpoint(100, 100), endpoint(160, 150));
  const numbers = path.match(/-?\d+(?:\.\d+)?/g).map(Number);

  assert.ok(Math.abs(Math.hypot(numbers[0] - 100, numbers[1] - 100) - 3.1) < 1e-9);
  assert.ok(Math.abs(Math.hypot(numbers.at(-2) - 160, numbers.at(-1) - 150) - 3.1) < 1e-9);
});

test("同年错层事件的回指线独立于事件图标计算，供底层先行绘制", () => {
  assert.deepEqual(eventStemGeometry({
    id: 11,
    displaced: true,
    baseX: 200,
    baseY: 140,
    displayX: 200,
    y: 102,
  }), {
    x1: 200,
    y1: 140,
    x2: 200,
    y2: 102,
    anchorX: 200,
    anchorY: 140,
  });
  assert.equal(eventStemGeometry({
    displaced: false,
    baseX: 200,
    baseY: 140,
    displayX: 200,
    y: 140,
  }), null);
});
