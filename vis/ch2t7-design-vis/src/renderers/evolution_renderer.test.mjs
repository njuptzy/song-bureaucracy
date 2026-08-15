import assert from "node:assert/strict";
import test from "node:test";

import { relationPath } from "./evolution_renderer.js";

function endpoint(x, y, iconType = "record") {
  return { x, y, timepointId: `${x}:${y}`, iconType };
}

function cubicFromPath(path) {
  const values = path.match(/-?\d+(?:\.\d+)?/g).map(Number);
  return {
    start: { x: values[0], y: values[1] },
    control1: { x: values[2], y: values[3] },
    control2: { x: values[4], y: values[5] },
    end: { x: values[6], y: values[7] },
  };
}

function cubicPoint(curve, t) {
  const inverse = 1 - t;
  return {
    x: inverse ** 3 * curve.start.x
      + 3 * inverse ** 2 * t * curve.control1.x
      + 3 * inverse * t ** 2 * curve.control2.x
      + t ** 3 * curve.end.x,
    y: inverse ** 3 * curve.start.y
      + 3 * inverse ** 2 * t * curve.control1.y
      + 3 * inverse * t ** 2 * curve.control2.y
      + t ** 3 * curve.end.y,
  };
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

test("关系曲线检测第三方事件点并选择不穿点的候选路径", () => {
  const source = endpoint(100, 180);
  const target = endpoint(100, 80, "abolish");
  const baseline = relationPath(source, target);
  const obstaclePoint = cubicPoint(cubicFromPath(baseline), 0.48);
  const obstacle = {
    ...obstaclePoint,
    timepointId: "unrelated-event",
    iconType: "record",
  };
  const routed = relationPath(source, target, [obstacle]);
  const routedCurve = cubicFromPath(routed);
  const minimumDistance = Math.min(...Array.from({ length: 81 }, (_, index) => {
    const point = cubicPoint(routedCurve, index / 80);
    return Math.hypot(point.x - obstacle.x, point.y - obstacle.y);
  }));

  assert.notEqual(routed, baseline);
  assert.ok(minimumDistance >= 5.8);
});
