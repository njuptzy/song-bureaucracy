import assert from "node:assert/strict";
import test from "node:test";

import { relationPath } from "./evolution_renderer.js";

function endpoint(x, y, iconType = "record") {
  return { x, y, timepointId: `${x}:${y}`, iconType };
}

test("关系箭头停在时间点图形外缘而不是中心", () => {
  const path = relationPath(endpoint(100, 100), endpoint(200, 100, "abolish"));
  const numbers = path.match(/-?\d+(?:\.\d+)?/g).map(Number);

  assert.equal(numbers[0], 104);
  assert.equal(numbers.at(-2), 192.5);
  assert.equal(numbers.at(-1), 100);
});

test("跨轨关系同样为罢废三角预留箭头间隔", () => {
  const path = relationPath(endpoint(100, 160), endpoint(100, 80, "abolish"));
  const numbers = path.match(/-?\d+(?:\.\d+)?/g).map(Number);

  assert.equal(numbers[1], 156);
  assert.equal(numbers.at(-2), 100);
  assert.equal(numbers.at(-1), 87.5);
});
