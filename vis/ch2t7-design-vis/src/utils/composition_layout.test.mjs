import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  COMPOSITION_GEOMETRY,
  fitCompositionBlock,
  layoutComposition,
  staffTextCols,
} from "./composition_layout.js";

const model = {
  focus: { id: 1, title: "尚书省" },
  selfColumn: {
    id: 1,
    title: "尚书省",
    staff: [{}],
    staffItems: [{ text: "主事六人", kind: "clerk", staffType: "吏" }],
    staffText: "主事六人",
  },
  looseColumns: [{ id: 2, title: "尚书都省", staff: [], staffText: "编制未载" }],
  sections: [
    {
      id: 3,
      title: "尚书省吏部",
      staff: [{}, {}],
      staffText: "郎中一人，书令史35人，令史14人",
      staffItems: [
        { text: "郎中一人", kind: "duty", staffType: "职事官" },
        { text: "书令史35人", kind: "clerk", staffType: "吏" },
        { text: "令史14人", kind: "clerk", staffType: "吏" },
      ],
      columns: [
        {
          id: 5,
          title: "吏部尚书左选",
          depth: 1,
          staff: [{}],
          staffItems: [{ text: "郎中一人", kind: "duty", staffType: "职事官" }],
          staffText: "郎中一人，令史十四人，书令史三十五人，守当官六人，守阙守当官一百五十人",
        },
        { id: 6, title: "司封司", depth: 2, staff: [], staffText: "编制未载" },
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

describe("fitCompositionBlock", () => {
  const bounds = { x: 558.34, y: 150.84, width: 1251.77, height: 711.8 };

  it("小数据块按原设计区域等比放大并居中", () => {
    const fitted = fitCompositionBlock(
      { x: 505, y: 138, width: 544.94, height: 215.85 },
      bounds
    );
    assert.ok(fitted.scale > 2.2 && fitted.scale < 2.4);
    assert.ok(Math.abs(fitted.width - bounds.width) < 1e-6);
    assert.ok(fitted.height < bounds.height);
    assert.ok(Math.abs(fitted.x - bounds.x) < 1e-6);
    assert.ok(fitted.y > bounds.y);
  });

  it("内容过高时按高度缩小且不越出设计区域", () => {
    const fitted = fitCompositionBlock(
      { x: 558.34, y: 150.84, width: 900, height: 1200 },
      bounds
    );
    assert.ok(fitted.scale < 1);
    assert.ok(Math.abs(fitted.height - bounds.height) < 1e-6);
    assert.ok(fitted.width <= bounds.width);
    assert.ok(fitted.x >= bounds.x && fitted.y >= bounds.y);
  });

  it("极少内容限制最大放大倍数，避免单列异常巨大", () => {
    const fitted = fitCompositionBlock(
      { x: 0, y: 0, width: 80, height: 210 },
      bounds
    );
    assert.equal(fitted.scale, 2.4);
  });
});

describe("layoutComposition", () => {
  const layout = layoutComposition(model, {
    origin: { x: 558.34, y: 150.94 },
    maxWidth: 980,
  });

  it("焦点机构是自由标题，直属机构才生成独立外框", () => {
    assert.equal(layout.focusLabel.id, 1);
    assert.equal(layout.focusLabel.kind, "focus");
    assert.deepEqual(layout.blocks.map((block) => block.id), [3, 2]);
    assert.equal(layout.blocks[0].label.title, "尚书省吏部");
    assert.equal(layout.blocks[1].label.title, "尚书都省");
  });

  it("分节标题不再混入共享列，分节内只包含所属机构", () => {
    assert.deepEqual(layout.items.map((item) => item.id), [5, 6]);
    assert.deepEqual(layout.blocks[0].items.map((item) => item.id), [5, 6]);
  });

  it("所属机构保留相对深度供边线粗细编码", () => {
    assert.deepEqual(layout.blocks[0].items.map((item) => item.depth), [1, 2]);
  });

  it("官职类型按图例分轨，同类官职合并以控制信息密度", () => {
    assert.deepEqual(
      layout.blocks[0].label.staffTracks.map((track) => track.kind),
      ["duty", "clerk", "clerk"]
    );
    assert.equal(layout.blocks[0].label.staffTracks[2].continuation, true);
    assert.equal(layout.focusLabel.staffTracks[0].kind, "clerk");
  });

  it("每个分块内部的机构列横向紧邻排列", () => {
    for (const block of layout.blocks) {
      const firstRow = block.items.filter(
        (item) => item.rect.y === block.items[0]?.rect.y
      );
      for (let i = 1; i < firstRow.length; i += 1) {
        const prevRight = firstRow[i - 1].rect.x + firstRow[i - 1].rect.width;
        assert.ok(Math.abs(firstRow[i].rect.x - prevRight) < 1e-9);
      }
    }
  });

  it("无编制机构只生成一个未载轨道，不制造空官职槽", () => {
    const empty = layout.items.find((item) => item.id === 6);
    assert.equal(empty.staffTracks.length, 1);
    assert.equal(empty.staffTracks[0].kind, "empty");
    assert.equal(empty.rect.height, COMPOSITION_GEOMETRY.columnHeight);
  });

  it("每个独立外框包住自己的标签与全部机构列", () => {
    for (const block of layout.blocks) {
      for (const item of [block.label, ...block.items]) {
        assert.ok(item.rect.x >= block.rect.x);
        assert.ok(item.rect.x + item.rect.width <= block.rect.x + block.rect.width + 1e-9);
        assert.ok(item.rect.y >= block.rect.y);
        assert.ok(item.rect.y + item.rect.height <= block.rect.y + block.rect.height + 1e-9);
      }
    }
  });

  it("画板行宽不足时将完整机构分块换到下一排", () => {
    const narrowLayout = layoutComposition(model, {
      origin: { x: 0, y: 0 },
      maxWidth: 200,
    });
    assert.equal(narrowLayout.rowCount, 2);
    assert.ok(narrowLayout.blocks[1].rect.y > narrowLayout.blocks[0].rect.y);
  });

  it("空模型返回 null", () => {
    assert.equal(layoutComposition(null), null);
  });
});
