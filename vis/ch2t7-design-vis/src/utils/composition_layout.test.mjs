import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  COMPOSITION_GEOMETRY,
  fitCompositionBlock,
  layoutComposition,
  staffTextCols,
} from "./composition_layout.js";

const leaf = (id, title, depth = 1, parentId = 3) => ({
  id,
  title,
  depth,
  parentId,
  pathKey: `${parentId}/${id}`,
  staff: [],
  staffItems: [],
  staffText: "编制未载",
  children: [],
});

const nested = leaf(5, "礼部贡院", 1, 3);
nested.children = [
  leaf(51, "礼部贡院试院", 2, 5),
  leaf(52, "礼部贡院封弥院", 2, 5),
  leaf(53, "礼部贡院誊录院", 2, 5),
  leaf(54, "礼部贡院编排所", 2, 5),
  leaf(55, "礼部贡院对读所", 2, 5),
  leaf(56, "礼部贡院别试所", 2, 5),
  leaf(57, "礼部贡院过落司", 2, 5),
];

const section = (id, title, columns) => ({
  id,
  title,
  depth: 0,
  parentId: 1,
  pathKey: `1/${id}`,
  staff: [],
  staffItems: [],
  staffText: "编制未载",
  children: columns,
  columns,
});

const groupBy = (items, keyOf) => {
  const groups = new Map();
  for (const item of items) {
    const key = keyOf(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  return groups;
};

const model = {
  focus: { id: 1, title: "尚书省" },
  selfColumn: {
    id: 1,
    title: "尚书省",
    staff: [{}],
    staffItems: [{ text: "主事六人", kind: "clerk", staffType: "吏" }],
    staffText: "主事六人",
  },
  focusDirectLeaves: [leaf(2, "尚书省左司", 0, 1), leaf(9, "尚书省右司", 0, 1)],
  sections: [
    section(10, "尚书省吏部", [1, 2, 3, 4, 5, 6, 7].map((id) => leaf(100 + id, `吏部司${id}`, 1, 10))),
    section(11, "尚书省户部", [leaf(201, "度支司", 1, 11), leaf(202, "金部司", 1, 11), leaf(203, "仓部司", 1, 11)]),
    section(12, "尚书省礼部", [leaf(301, "礼部司", 1, 12), leaf(302, "祠部司", 1, 12), leaf(303, "主客司", 1, 12), leaf(304, "膳部司", 1, 12), { ...nested, parentId: 12 }]),
    section(13, "尚书省工部", [leaf(401, "工部司", 1, 13), leaf(402, "屯田司", 1, 13), leaf(403, "虞部司", 1, 13), leaf(404, "水部司", 1, 13)]),
    section(14, "尚书省兵部", [1, 2, 3, 4, 5].map((id) => leaf(500 + id, `兵部司${id}`, 1, 14))),
    section(15, "尚书省刑部", [1, 2, 3, 4].map((id) => leaf(600 + id, `刑部司${id}`, 1, 15))),
  ],
};

describe("staffTextCols", () => {
  it("按每列字数折算文本列数", () => {
    assert.equal(staffTextCols("郎中一人", COMPOSITION_GEOMETRY, 26), 1);
    assert.equal(staffTextCols("x".repeat(27), COMPOSITION_GEOMETRY, 26), 2);
    assert.equal(staffTextCols(""), 0);
  });
});

describe("fitCompositionBlock", () => {
  it("布局与画板同尺寸时保持稳定字号和线宽", () => {
    const bounds = { x: 503.48, y: 147.58, width: 1309.84, height: 717.85 };
    const fitted = fitCompositionBlock(bounds, bounds);
    assert.equal(fitted.scale, 1);
    assert.equal(fitted.translateX, 0);
    assert.equal(fitted.translateY, 0);
  });
});

describe("layoutComposition", () => {
  const layout = layoutComposition(model);

  it("绘制一个总框，焦点标题位于总框内部左栏", () => {
    assert.deepEqual(layout.parentRect, layout.bounds);
    assert.ok(layout.focusLabel.rect.x >= layout.parentRect.x);
    assert.ok(layout.focusLabel.rect.x + layout.focusLabel.rect.width < layout.blocks[0].rect.x);
    assert.ok(layout.focusLabel.titlePlateRect.x >= layout.parentRect.x);
    assert.ok(layout.focusLabel.titlePlateRect.y >= layout.parentRect.y);
    assert.equal(layout.blocks.some((block) => block.id === 1), false);
  });

  it("六部采用原稿上四下二的顺序，直属叶合为一个附属列带", () => {
    const top = layout.blocks.filter((block) => block.rect.y === layout.blocks[0].rect.y);
    const bottomY = Math.max(...layout.blocks.map((block) => block.rect.y));
    const bottom = layout.blocks.filter((block) => block.rect.y === bottomY);
    assert.deepEqual(top.map((block) => block.id), [10, 11, 12, 13]);
    assert.deepEqual(bottom.map((block) => block.id), [14, 15, "attachments:1"]);
    const attachments = bottom.at(-1);
    assert.deepEqual(attachments.items.map((item) => item.id), [2, 9]);
  });

  it("部门块只包含直属机构，贡院七个下级嵌套在贡院列内", () => {
    const li = layout.blocks.find((block) => block.id === 12);
    assert.deepEqual(li.items.map((item) => item.id), [301, 302, 303, 304, 5]);
    const gongyuan = li.items.find((item) => item.id === 5);
    assert.equal(gongyuan.children.length, 7);
    for (const child of gongyuan.children) {
      assert.ok(child.rect.x >= gongyuan.rect.x);
      assert.ok(child.rect.y >= gongyuan.rect.y);
      assert.ok(child.rect.x + child.rect.width <= gongyuan.rect.x + gongyuan.rect.width + 1e-7);
      assert.ok(child.rect.y + child.rect.height <= gongyuan.rect.y + gongyuan.rect.height + 1e-7);
    }
  });

  it("宏观横带和每个部门内部行都填满右边界", () => {
    const parentRight = layout.parentRect.x + layout.parentRect.width - COMPOSITION_GEOMETRY.outerPadding;
    const byOuterY = groupBy(layout.blocks, (block) => block.rect.y);
    for (const blocks of byOuterY.values()) {
      const right = Math.max(...blocks.map((block) => block.rect.x + block.rect.width));
      assert.ok(Math.abs(right - parentRight) < 1e-6);
    }
    for (const block of layout.blocks.filter((item) => item.kind === "section")) {
      const byY = groupBy(block.items, (item) => item.rect.y);
      for (const items of byY.values()) {
        const right = Math.max(...items.map((item) => item.rect.x + item.rect.width));
        assert.ok(Math.abs(right - (block.rect.x + block.rect.width)) < 1e-6);
      }
    }
  });

  it("单行部门的机构列拉高填满部门，不保留固定211像素空带", () => {
    const hu = layout.blocks.find((block) => block.id === 11);
    for (const item of hu.items) {
      assert.equal(item.rect.y, hu.rect.y);
      assert.equal(item.rect.height, hu.rect.height);
    }
  });

  it("所有同层机构列之间保留原稿细缝", () => {
    const hu = layout.blocks.find((block) => block.id === 11);
    for (let index = 1; index < hu.items.length; index += 1) {
      const previousRight = hu.items[index - 1].rect.x + hu.items[index - 1].rect.width;
      assert.ok(Math.abs(hu.items[index].rect.x - previousRight - COMPOSITION_GEOMETRY.columnGap) < 1e-6);
    }
  });

  it("空模型返回 null", () => {
    assert.equal(layoutComposition(null), null);
  });
});
