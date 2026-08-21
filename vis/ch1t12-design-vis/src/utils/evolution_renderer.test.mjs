import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  EVOLUTION_SELECTOR_SLOT_STEP,
  evolutionEventIconSize,
  evolutionEndpointClearance,
  evolutionIdentityGlyphMetrics,
  evolutionLaneIdentityLayout,
  relationPath,
  evolutionLaneTitleMetrics,
  compositeTreeScrollMetrics,
  compositeBandTrackBounds,
  layoutCompositeBandEventRows,
  compositeSectionLayout,
} from "../renderers/evolution_renderer.js";

it("三信息带与机构主线共用完全相同的年份横轴", () => {
  const layout = {
    bounds: { x: 520 },
    plotBounds: { x: 650, right: 1798 },
    yearScale: { range: [650, 1798] },
  };
  assert.deepEqual(compositeBandTrackBounds(layout), {
    labelX: 520,
    trackX: 650,
    trackRight: 1798,
  });
});

it("圆点不相交的演变事件共用轴线，只有相撞时才下沉回指", () => {
  const events = [
    { id: "a", displayTitle: "嘉庆院 → 将作监", displaySummary: "前后演变", x: 180 },
    { id: "b", displayTitle: "少府监 → 将作监", displaySummary: "前后演变", x: 650 },
    { id: "c", displayTitle: "近邻机构 → 将作监", displaySummary: "前后演变", x: 658 },
  ];
  const placements = layoutCompositeBandEventRows(events, 900, (event) => event.x);
  assert.equal(placements[0].rowIndex, 0);
  assert.equal(placements[1].rowIndex, 0);
  assert.equal(placements[2].rowIndex, 1);
  assert.equal(placements[0].x, placements[0].anchorX);
  assert.notEqual(placements[2].x, placements[2].anchorX);
});

it("机构主线、机构结构和编制区域严格等高", () => {
  const sections = compositeSectionLayout({ y: 258, height: 568 });
  assert.equal(sections.bandsTop - sections.mainTop, sections.sectionHeight);
  assert.equal(sections.mainTop + sections.sectionHeight * 3, 822);
});

function point(iconType, x, y) {
  return { iconType, timepointId: `${iconType}-${x}-${y}`, x, y };
}

describe("evolutionEventIconSize", () => {
  it("主图未选中事件与图例使用同一尺寸", () => {
    assert.equal(evolutionEventIconSize("record"), 4.2);
    assert.equal(evolutionEventIconSize("establish"), 7.2);
    assert.equal(evolutionEventIconSize("abolish"), 7.2);
    assert.equal(evolutionEventIconSize("affiliation_change"), 7);
  });

  it("选中态只在图例基准上增加一级强调", () => {
    assert.equal(evolutionEventIconSize("record", true), 5.2);
    assert.equal(evolutionEventIconSize("establish", true), 8.2);
    assert.equal(evolutionEventIconSize("affiliation_change", true), 8);
  });
});

describe("evolutionLaneTitleMetrics", () => {
  it("14px 竖排实体名逐字分开且仍限制在签条高度内", () => {
    const metrics = evolutionLaneTitleMetrics(100, 198);

    assert.equal(metrics.pitch, 16);
    assert.equal(metrics.maxChars, 6);
    assert.ok(metrics.pitch > 14);
    assert.ok((5 - 1) * metrics.pitch < 98);
  });

  it("短签条减少可见字数而不压缩字距", () => {
    assert.deepEqual(evolutionLaneTitleMetrics(100, 140), { pitch: 16, maxChars: 3 });
  });
});

describe("evolution identity glyphs", () => {
  it("选择器槽位只保留删除按钮所需的最小安全间距", () => {
    assert.equal(EVOLUTION_SELECTOR_SLOT_STEP, 52);
    assert.equal(EVOLUTION_SELECTOR_SLOT_STEP - 46, 6);
  });

  it("左侧选择器中的机构和官职图标使用同一中心与同一高度", () => {
    const institution = evolutionIdentityGlyphMetrics("机构", 92, 23, 0);
    const official = evolutionIdentityGlyphMetrics("官职", 92, 23, 0);

    assert.equal(institution.x + institution.width / 2, 23);
    assert.equal(official.x + official.width / 2, 23);
    assert.ok(Math.abs(institution.bodyBottom - 92) < 1e-9);
    assert.ok(Math.abs(official.bodyBottom - 92) < 1e-9);
    assert.ok(official.bodyTop > institution.bodyTop);
  });

  it("左侧选择器与右侧轨道共享完全相同的 SVG 尺寸计算", () => {
    for (const entityType of ["机构", "官职"]) {
      const lane = evolutionLaneIdentityLayout(entityType, 92, 0, 54);
      const glyph = evolutionIdentityGlyphMetrics(entityType, 92, lane.centerX, 0);
      assert.equal(glyph.scale, lane.scale);
      assert.equal(glyph.width, lane.width);
      assert.equal(glyph.x, lane.x);
    }
  });
});

describe("compositeTreeScrollMetrics", () => {
  it("内容未溢出时锁定在顶部并占满滚动轨道", () => {
    assert.deepEqual(compositeTreeScrollMetrics(4, 23, 105, 80), {
      contentHeight: 92,
      maxScroll: 0,
      offset: 0,
      trackHeight: 105,
      thumbHeight: 105,
      thumbTravel: 0,
      thumbOffset: 0,
    });
  });

  it("完整保留所有树行并钳制滚动位置", () => {
    const metrics = compositeTreeScrollMetrics(36, 23, 105, 9999);
    assert.equal(metrics.contentHeight, 828);
    assert.equal(metrics.maxScroll, 723);
    assert.equal(metrics.offset, 723);
    assert.equal(metrics.thumbHeight, 20);
    assert.equal(metrics.thumbOffset, metrics.thumbTravel);
  });

  it("编制列表可从首项滚动到第23项", () => {
    const metrics = compositeTreeScrollMetrics(23, 23, 84, Number.POSITIVE_INFINITY);
    assert.equal(metrics.contentHeight, 529);
    assert.equal(metrics.maxScroll, 445);
    assert.equal(metrics.offset, 445);
    assert.equal(metrics.thumbHeight, 20);
    assert.equal(metrics.thumbOffset, metrics.thumbTravel);
  });
});

describe("evolution relation endpoints", () => {
  it("圆点按实际半径停止，方向变化不改变圆形边界", () => {
    const source = point("record", 100, 100);
    assert.equal(evolutionEndpointClearance(source, { x: 200, y: 100 }), 4.7);
    assert.equal(evolutionEndpointClearance(source, { x: 200, y: 200 }), 4.7);
  });

  it("菱形和三角形按连接方向求轮廓交点", () => {
    const diamond = point("affiliation_change", 100, 100);
    const triangle = point("establish", 100, 100);
    const horizontalDiamond = evolutionEndpointClearance(diamond, { x: 200, y: 100 });
    const diagonalDiamond = evolutionEndpointClearance(diamond, { x: 200, y: 200 });
    const verticalTriangle = evolutionEndpointClearance(triangle, { x: 100, y: 0 });
    const downwardTriangle = evolutionEndpointClearance(triangle, { x: 100, y: 200 });
    assert.equal(horizontalDiamond, 7.55);
    assert.ok(diagonalDiamond < horizontalDiamond);
    assert.equal(verticalTriangle, 7.7);
    assert.ok(downwardTriangle < verticalTriangle);
  });

  it("关系路径的起止端点使用 display 坐标而不是历史锚点", () => {
    const source = { ...point("record", 100, 100), baseX: 40, baseY: 40 };
    const target = { ...point("affiliation_change", 300, 240), baseX: 80, baseY: 80 };
    const path = relationPath(source, target);
    const values = path.match(/-?\d+(?:\.\d+)?/g).map(Number);
    const endX = values.at(-2);
    const endY = values.at(-1);
    assert.notEqual(endX, target.baseX);
    assert.notEqual(endY, target.baseY);
    assert.ok(endX < target.x);
    assert.ok(endY < target.y);
  });
});
