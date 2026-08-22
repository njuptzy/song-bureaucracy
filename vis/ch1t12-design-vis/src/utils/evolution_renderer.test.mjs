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
  compositeBandItemVisibility,
  compositeBandLabelWidth,
  compositeEventGuidePoints,
  layoutCompositeBandEventRows,
  layoutCompositeBandLabels,
  layoutCompositeMainLaneEvents,
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

it("可见圆点不相交时优先共用轴线，点击热区和标签不挤占点位", () => {
  const events = [
    { id: "a", displayTitle: "嘉庆院 → 将作监", displaySummary: "前后演变", x: 180 },
    { id: "b", displayTitle: "少府监 → 将作监", displaySummary: "前后演变", x: 650 },
    { id: "c", displayTitle: "近邻机构 → 将作监", displaySummary: "前后演变", x: 658 },
    { id: "d", displayTitle: "同点机构 → 将作监", displaySummary: "前后演变", x: 658 },
  ];
  const placements = layoutCompositeBandEventRows(events, 900, (event) => event.x);
  assert.equal(placements[0].rowIndex, 0);
  assert.equal(placements[1].rowIndex, 0);
  assert.equal(placements[2].rowIndex, 0);
  assert.equal(placements[3].rowIndex, 1);
  assert.equal(placements[0].x, placements[0].anchorX);
  assert.equal(placements[3].x, placements[3].anchorX);
});

it("信息带标签即使位于圆点旁也明确画线连接", () => {
  const placements = [
    { event: { displayTitle: "增置官职" }, x: 80, anchorX: 80, rowIndex: 0 },
    { event: { displayTitle: "员额变化" }, x: 260, anchorX: 260, rowIndex: 0 },
  ];
  const labels = layoutCompositeBandLabels(placements, 420, 18, 72);

  assert.ok(labels.every((placement) => placement.label));
  assert.ok(labels.every((placement) => placement.label.leader));
  assert.ok(labels.every((placement) => placement.label.leader.x1 === placement.x));
  assert.ok(labels.every((placement) => placement.label.box.x > placement.x));
  assert.ok(labels.every((placement) => placement.label.box.y >= 14));
  assert.ok(labels[0].label.box.right < labels[1].label.box.x);
});

it("下沉事件使用垂直虚线回指并在圆点前留出间隙", () => {
  const points = compositeEventGuidePoints({
    anchorX: 80,
    markerY: 58,
  });

  assert.deepEqual(points, [
    [80, 0],
    [80, 52.5],
  ]);
});

it("圆点右侧原位可用时优先水平直连，不上下挪动", () => {
  const [placement] = layoutCompositeBandLabels([{
    event: { displayTitle: "国子监丞编制" },
    x: 80,
    anchorX: 80,
    rowIndex: 2,
  }], 320, 18, 100);

  assert.ok(placement.label);
  assert.equal(placement.label.leader.y2, placement.label.leader.y1);
  assert.equal(placement.label.box.x, placement.x + 15);
});

it("轴线上相邻事件可使用安全的第一排和第二近邻排标签", () => {
  const placements = [80, 160, 240].map((x, index) => ({
    event: { displayTitle: `国子监事件${index + 1}` },
    x,
    anchorX: x,
    rowIndex: 0,
  }));
  const labels = layoutCompositeBandLabels(placements, 400, 18, 100)
    .map((placement) => placement.label)
    .filter(Boolean);

  assert.ok(labels.length >= 2);
  assert.ok(labels.every((label) => label.box.y >= 14));
  assert.ok(labels.every((label) => label.leader.y2 - label.leader.y1 <= 40));
});

it("同一年纵向相邻圆点可按18像素行距连续接标签", () => {
  const placements = Array.from({ length: 6 }, (_, rowIndex) => ({
    event: { displayTitle: `编制${rowIndex + 1}` },
    x: 60,
    anchorX: 60,
    rowIndex,
  }));
  const labels = layoutCompositeBandLabels(placements, 260, 18, 130)
    .map((placement) => placement.label)
    .filter(Boolean);

  assert.equal(labels.length, placements.length);
  assert.ok(labels.every((label) => label.leader.y2 === label.box.y + 7));
});

it("信息带按汉字实际宽度和描边余量计算标签碰撞框", () => {
  assert.equal(compositeBandLabelWidth("国子监录编制"), 78);
  assert.equal(compositeBandLabelWidth("A1编制"), 42);
});

it("标签会避开其他事件图标的扩大禁入区", () => {
  const placements = [
    { event: { displayTitle: "国子监祭酒编制" }, x: 40, anchorX: 40, rowIndex: 1 },
    { event: { displayTitle: "博士编制" }, x: 130, anchorX: 130, rowIndex: 1 },
  ];
  const laidOut = layoutCompositeBandLabels(placements, 280, 18, 100);
  const markerBoxes = placements.map((placement) => ({
    x: placement.x - 10,
    y: placement.rowIndex * 18 - 10,
    right: placement.x + 10,
    bottom: placement.rowIndex * 18 + 10,
  }));

  for (const placement of laidOut) {
    if (!placement.label) continue;
    for (const marker of markerBoxes) {
      const box = placement.label.box;
      const overlaps = box.x < marker.right + 3
        && box.right + 3 > marker.x
        && box.y < marker.bottom + 3
        && box.bottom + 3 > marker.y;
      assert.equal(overlaps, false);
    }
  }
});

it("圆点右侧放不下标签时直接隐藏", () => {
  const placements = [
    { event: { displayTitle: "一个很长的编制变化标签" }, x: 45, anchorX: 45, rowIndex: 0 },
  ];
  const [placement] = layoutCompositeBandLabels(placements, 90, 18, 44);

  assert.equal(placement.label, null);
});

it("密集信息带贪心保留清晰标签并隐藏其余冲突项", () => {
  const placements = Array.from({ length: 8 }, (_, index) => ({
    event: { displayTitle: `编制事件${index + 1}` },
    x: 40 + index * 17,
    anchorX: 40 + index * 17,
    rowIndex: index % 3,
  }));
  const labels = layoutCompositeBandLabels(placements, 240, 18, 72)
    .map((placement) => placement.label)
    .filter(Boolean);

  assert.ok(labels.length > 0);
  assert.ok(labels.length < placements.length);
  assert.ok(labels.every((label) => label.leader));
  for (const label of labels) {
    assert.ok(label.box.x >= 0);
    assert.ok(label.box.right <= 240);
    assert.ok(label.box.y >= 14);
    assert.equal(label.textAnchor, "start");
    for (let index = 1; index < label.leader.points.length; index += 1) {
      const previous = label.leader.points[index - 1];
      const current = label.leader.points[index];
      assert.ok(previous[0] === current[0] || previous[1] === current[1]);
    }
    assert.ok(label.leader.x2 >= label.leader.x1);
    assert.ok(label.leader.y2 >= label.leader.y1);
    assert.ok(label.leader.y2 - label.leader.y1 <= 40);
  }
  for (let index = 0; index < labels.length; index += 1) {
    for (let compared = index + 1; compared < labels.length; compared += 1) {
      const first = labels[index].box;
      const second = labels[compared].box;
      const overlaps = first.x < second.right + 4
        && first.right + 4 > second.x
        && first.y < second.bottom + 4
        && first.bottom + 4 > second.y;
      assert.equal(overlaps, false);
    }
  }
});

it("编制标签只使用事件点附近的下方空位", () => {
  const placements = Array.from({ length: 5 }, (_, index) => ({
    event: { displayTitle: `密集编制变化${index + 1}` },
    x: 100 + index * 4,
    anchorX: 100 + index * 4,
    rowIndex: 0,
  }));
  const labels = layoutCompositeBandLabels(placements, 260, 18, 120)
    .map((placement) => placement.label)
    .filter(Boolean);

  assert.ok(labels.length > 0);
  assert.ok(labels.length < placements.length);
  assert.ok(labels.every((label) => label.leader.y2 - label.leader.y1 <= 40));
});

it("标签仍在视口时不会随圆点提前隐藏", () => {
  assert.deepEqual(compositeBandItemVisibility({
    markerY: 10,
    labelBox: { y: 70, bottom: 84 },
  }, 30, 60), {
    markerVisible: false,
    labelVisible: true,
    leaderVisible: true,
  });
});

it("机构主线、机构结构和编制区域严格等高", () => {
  const sections = compositeSectionLayout({ y: 258, height: 568 });
  assert.equal(sections.bandsTop - sections.mainTop, sections.sectionHeight);
  assert.equal(sections.mainTop + sections.sectionHeight * 3, 822);
});

it("机构主线在轴线上下分层并保持足够行距", () => {
  const events = [
    { id: "axis", baseX: 100, displayX: 100, y: 200 },
    { id: "upper", baseX: 100, displayX: 82, y: 182 },
    { id: "lower", baseX: 100, displayX: 118, y: 218 },
    { id: "far", baseX: 100, displayX: 64, y: 164 },
  ];
  const result = layoutCompositeMainLaneEvents(events, 200, 80, 220, 40);

  assert.equal(result[0].y, 80);
  assert.ok(result[1].y < 80);
  assert.ok(result.slice(2).every((event) => event.y > 80));
  assert.equal(new Set(result.map((event) => event.y)).size, 4);
  assert.ok(result.every((event) => event.y <= 196));
  assert.ok(result.every((event) => event.displayX === 100));
  assert.ok(result.every((event) => event.displayX === event.baseX));
  const orderedYs = result.map((event) => event.y).sort((first, second) => first - second);
  const gaps = orderedYs.slice(1).map((y, index) => y - orderedYs[index]);
  assert.ok(gaps.every((gap) => gap >= 28));
  assert.ok(gaps.every((gap) => gap <= 36));
});

it("机构主线只在真实年份相近时换到下一行且回指保持竖直", () => {
  const events = [
    { id: "a", baseX: 100, displayX: 82 },
    { id: "b", baseX: 112, displayX: 130 },
    { id: "c", baseX: 160, displayX: 142 },
  ];
  const result = layoutCompositeMainLaneEvents(events, 200, 80, 220, 40);

  assert.equal(result[0].y, 80);
  assert.ok(result[1].y < 80);
  assert.equal(result[2].y, 80);
  assert.deepEqual(result.map((event) => event.displayX), [100, 112, 160]);
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
