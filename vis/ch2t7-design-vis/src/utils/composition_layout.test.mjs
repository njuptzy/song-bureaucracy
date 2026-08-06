import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  COMPOSITION_GEOMETRY,
  layoutComposition,
  staffTextCols,
} from "./composition_layout.js";

const model = {
  focus: { id: 1, title: "尚书省" },
  selfColumn: { id: 1, title: "尚书省", staff: [{}], staffText: "主事六人" },
  looseColumns: [{ id: 2, title: "尚书都省", staff: [], staffText: "编制未载" }],
  sections: [
    {
      id: 3,
      title: "尚书省吏部",
      staff: [{}, {}],
      staffText: "郎中一人，书令史35人，令史14人",
      columns: [
        { id: 5, title: "吏部尚书左选", staff: [{}], staffText: "郎中一人，令史十四人，书令史三十五人，守当官六人，守阙守当官一百五十人" },
        { id: 6, title: "司封司", staff: [], staffText: "编制未载" },
      ],
    },
  ],
};

describe("staffTextCols", () => {
  it("按每列字数折算文本列数", () => {
    assert.equal(staffTextCols("郎中一人"), 1);
    assert.equal(staffTextCols("x".repeat(29)), 2);
    assert.equal(staffTextCols(""), 0);
  });
});

describe("layoutComposition", () => {
  const layout = layoutComposition(model, {
    origin: { x: 558.34, y: 150.94 },
    maxWidth: 980,
  });

  it("块标签位于块内左端", () => {
    assert.equal(layout.label.title, "尚书省");
    assert.ok(layout.label.x > 558.34 && layout.label.x < 610);
    assert.ok(layout.label.y > 150.94);
  });

  it("排版项顺序：自身列 → 松散列 → 分节 → 分节列", () => {
    assert.deepEqual(layout.items.map((item) => item.id), [1, 2, 3, 5, 6]);
    assert.equal(layout.items[2].kind, "section");
  });

  it("列横向依次排开且不超过行宽上限", () => {
    const row1 = layout.items.filter((item) => item.rect.y === layout.items[0].rect.y);
    for (let i = 1; i < row1.length; i += 1) {
      const prevRight = row1[i - 1].rect.x + row1[i - 1].rect.width;
      assert.ok(Math.abs(row1[i].rect.x - prevRight) < 1e-9);
    }
    for (const item of row1) {
      assert.ok(item.rect.x + item.rect.width <= 558.34 + 980);
    }
  });

  it("无编制列比带编制列窄", () => {
    const narrow = layout.items.find((item) => item.id === 6);
    const wide = layout.items.find((item) => item.id === 5);
    assert.ok(narrow.rect.width < wide.rect.width);
    assert.equal(narrow.rect.height, COMPOSITION_GEOMETRY.columnHeight);
  });

  it("块矩形包住全部内容", () => {
    for (const item of layout.items) {
      assert.ok(item.rect.x >= layout.block.x);
      assert.ok(item.rect.x + item.rect.width <= layout.block.x + layout.block.width + 1e-9);
      assert.ok(item.rect.y + item.rect.height <= layout.block.y + layout.block.height + 1e-9);
    }
  });

  it("行宽不足时换行", () => {
    const narrowLayout = layoutComposition(model, {
      origin: { x: 0, y: 0 },
      maxWidth: 200,
    });
    const rows = new Set(narrowLayout.items.map((item) => item.rect.y));
    assert.ok(rows.size > 1);
    assert.ok(narrowLayout.rowCount === rows.size);
  });

  it("空模型返回 null", () => {
    assert.equal(layoutComposition(null), null);
  });
});
