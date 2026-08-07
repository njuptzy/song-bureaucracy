import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { layoutEvolutionModel } from "./evolution_layout.js";
import { buildEvolutionModel } from "./evolution_model.js";

const entity = (id, title = `实体${id}`) => ({ id, title, type: "机构" });
const timepoint = (id, year, event = "普通记载", overrides = {}) => ({
  id,
  time: year == null ? "未知" : String(year),
  event,
  prev_id: null,
  succ_id: null,
  time_type: year == null ? "undated" : "exact",
  year_start: year,
  year_end: year,
  ...overrides,
});

describe("layoutEvolutionModel", () => {
  it("所有轨道、标签、事件和存续段都留在给定边界内", () => {
    const model = buildEvolutionModel({
      entities: [entity(1), entity(2), entity(3)],
      timepoints: {
        1: [timepoint(11, 960, "始置"), timepoint(12, 1279)],
        2: [timepoint(21, 1000, "始置"), timepoint(22, 1100)],
        3: [timepoint(31, 1050, "始置"), timepoint(32, 1200)],
      },
      changeRelations: [
        { id: 1, relation_type: "前后演变", source: 1, target: 2, source_timepoint_id: 12, target_timepoint_id: 21 },
        { id: 2, relation_type: "前后演变", source: 1, target: 3, source_timepoint_id: 12, target_timepoint_id: 31 },
      ],
    }, [1]);
    const bounds = { x: 560, y: 190, width: 1228, height: 630 };
    const layout = layoutEvolutionModel(model, bounds);

    assert.deepEqual(layout.yearScale.domain, [960, 1279]);
    for (const lane of layout.lanes) {
      assert.ok(lane.y >= bounds.y && lane.y <= bounds.y + bounds.height);
      assert.ok(lane.labelX >= bounds.x);
      assert.ok(lane.labelX + lane.labelMaxWidth <= layout.plotBounds.x);
      assert.ok(lane.trackStartX >= bounds.x);
      assert.ok(lane.trackEndX <= bounds.x + bounds.width);
      for (const event of lane.events) {
        assert.ok(event.baseX >= layout.plotBounds.x && event.baseX <= layout.plotBounds.right);
        assert.ok(event.displayX >= layout.plotBounds.x && event.displayX <= layout.plotBounds.right);
      }
      for (const segment of lane.segments) {
        assert.ok(segment.startX >= layout.plotBounds.x);
        assert.ok(segment.endX <= layout.plotBounds.right);
      }
    }
  });

  it("同年事件共享 baseX，只用 displayX/offsetX 避让", () => {
    const model = buildEvolutionModel({
      entities: [entity(1)],
      timepoints: {
        1: [
          timepoint(11, 1000, "始置", { succ_id: 12 }),
          timepoint(12, 1000, "普通记载", { prev_id: 11, succ_id: 13 }),
          timepoint(13, 1000, "又一记载", { prev_id: 12 }),
        ],
      },
      changeRelations: [],
    }, [1]);
    const layout = layoutEvolutionModel(model);
    const events = layout.lanes[0].events;

    assert.equal(new Set(events.map((item) => item.baseX)).size, 1);
    assert.equal(new Set(events.map((item) => item.displayX)).size, 3);
    assert.ok(events.some((item) => item.offsetX !== 0));
    const displayXs = events.map((item) => item.displayX).sort((a, b) => a - b);
    assert.ok(displayXs.every((x, index) => index === 0 || x - displayXs[index - 1] >= 20));
    for (const event of events) {
      assert.equal(event.displayX, event.baseX + event.offsetX);
    }
  });

  it("关系端点按各自年份落位，异年显式关系组没有伪造共同时间", () => {
    const model = buildEvolutionModel({
      entities: [entity(1), entity(2)],
      timepoints: {
        1: [timepoint(11, 980, "始置")],
        2: [timepoint(21, 1000, "始置")],
      },
      changeRelations: [{
        id: 7,
        relation_type: "演变·改置",
        relation_group_id: "g7",
        source: 1,
        target: 2,
        source_timepoint_id: 11,
        target_timepoint_id: 21,
      }],
    }, [1]);
    const layout = layoutEvolutionModel(model);
    const relation = layout.relations[0];
    const group = layout.relationGroups[0];

    assert.notEqual(relation.sourcePoints[0].baseX, relation.targetPoints[0].baseX);
    assert.equal(group.junctionX, null);
    assert.equal(group.divergentEndpointYears, true);
    assert.equal(group.renderMode, "individual");
    assert.ok(Number.isFinite(relation.labelX));
    assert.ok(relation.leader);
    assert.equal(relation.labelVisible, true);
    assert.equal(relation.labelOverflow, false);
    assert.equal(group.labelVisible, false);
  });

  it("同年显式组标签与普通关系标签共同占位", () => {
    const model = buildEvolutionModel({
      entities: [entity(1), entity(2)],
      timepoints: {
        1: [timepoint(11, 1000, "始置")],
        2: [timepoint(21, 1000, "始置")],
      },
      changeRelations: [
        {
          id: 40,
          relation_type: "演变·分拆",
          relation_group_id: "g40",
          source: 1,
          target: 2,
          source_timepoint_id: 11,
          target_timepoint_id: 21,
        },
        {
          id: 41,
          relation_type: "演变·改称",
          source: 1,
          target: 2,
          source_timepoint_id: 11,
          target_timepoint_id: 21,
        },
      ],
    }, [1]);
    const layout = layoutEvolutionModel(model, { x: 10, y: 20, width: 320, height: 140 });
    const group = layout.relationGroups[0];
    const groupedRelation = layout.relations.find((relation) => relation.id === 40);
    const ordinaryRelation = layout.relations.find((relation) => relation.id === 41);

    assert.equal(group.renderMode, "group");
    assert.equal(group.labelVisible, true);
    assert.equal(groupedRelation.labelVisible, false);
    assert.equal(ordinaryRelation.labelVisible, true);
    const overlaps = group.labelBounds.x < ordinaryRelation.labelBounds.right
      && group.labelBounds.right > ordinaryRelation.labelBounds.x
      && group.labelBounds.y < ordinaryRelation.labelBounds.bottom
      && group.labelBounds.bottom > ordinaryRelation.labelBounds.y;
    assert.equal(overlaps, false);
  });

  it("同年及邻近普通关系标签稳定分层并留在画布内", () => {
    const relations = [
      { id: 20, relation_type: "前后演变", source: 1, target: 2, source_timepoint_id: 11, target_timepoint_id: 21 },
      { id: 21, relation_type: "前后演变", source: 1, target: 2, source_timepoint_id: 11, target_timepoint_id: 21 },
      { id: 22, relation_type: "前后演变", source: 1, target: 2, source_timepoint_id: 12, target_timepoint_id: 22 },
    ];
    const input = (changeRelations) => ({
      entities: [entity(1), entity(2)],
      timepoints: {
        1: [
          timepoint(11, 1000, "始置", { succ_id: 12 }),
          timepoint(12, 1001, "普通记载", { prev_id: 11 }),
        ],
        2: [
          timepoint(21, 1000, "始置", { succ_id: 22 }),
          timepoint(22, 1001, "普通记载", { prev_id: 21 }),
        ],
      },
      changeRelations,
    });
    const bounds = { x: 10, y: 20, width: 320, height: 140 };
    const first = layoutEvolutionModel(buildEvolutionModel(input(relations), [1]), bounds);
    const second = layoutEvolutionModel(buildEvolutionModel(input([...relations].reverse()), [1]), bounds);
    const ordinary = first.relations;

    assert.equal(ordinary.length, 3);
    assert.ok(new Set(ordinary.map((relation) => relation.labelY)).size > 1);
    for (const relation of ordinary) {
      assert.equal(relation.labelVisible, true);
      assert.equal(relation.labelOverflow, false);
      assert.ok(Number.isFinite(relation.labelX));
      assert.ok(Number.isFinite(relation.labelY));
      assert.ok(Number.isFinite(relation.leader.x1));
      assert.ok(Number.isFinite(relation.leader.y1));
      assert.ok(Number.isFinite(relation.leader.x2));
      assert.ok(Number.isFinite(relation.leader.y2));
      assert.equal(relation.leader.x1, relation.labelAnchorX);
      assert.equal(relation.leader.y1, relation.labelAnchorY);
      assert.ok(relation.labelBounds.x >= bounds.x);
      assert.ok(relation.labelBounds.right <= bounds.x + bounds.width);
      assert.ok(relation.labelBounds.y >= bounds.y);
      assert.ok(relation.labelBounds.bottom <= bounds.y + bounds.height);
    }
    for (let index = 0; index < ordinary.length; index += 1) {
      for (let otherIndex = index + 1; otherIndex < ordinary.length; otherIndex += 1) {
        const firstBox = ordinary[index].labelBounds;
        const secondBox = ordinary[otherIndex].labelBounds;
        const overlaps = firstBox.x < secondBox.right
          && firstBox.right > secondBox.x
          && firstBox.y < secondBox.bottom
          && firstBox.bottom > secondBox.y;
        assert.equal(overlaps, false);
      }
    }

    const placementsById = (layout) => Object.fromEntries(layout.relations.map((relation) => [
      relation.id,
      [relation.labelX, relation.labelY, relation.leader],
    ]));
    assert.deepEqual(placementsById(first), placementsById(second));

    const duplicateIds = [
      { ...relations[0], id: 30, evidence_key: "R30-A", display_relation_type: "甲" },
      { ...relations[0], id: 30, evidence_key: "R30-B", display_relation_type: "乙" },
    ];
    const duplicateFirst = layoutEvolutionModel(
      buildEvolutionModel(input(duplicateIds), [1]),
      bounds,
    );
    const duplicateSecond = layoutEvolutionModel(
      buildEvolutionModel(input([...duplicateIds].reverse()), [1]),
      bounds,
    );
    const placementsByEvidence = (layout) => Object.fromEntries(layout.relations.map((relation) => [
      relation.evidenceKey,
      [relation.labelX, relation.labelY, relation.leader],
    ]));
    assert.deepEqual(placementsByEvidence(duplicateFirst), placementsByEvidence(duplicateSecond));
  });

  it("空间不足时隐藏溢出关系标签，不再强制叠放", () => {
    const changeRelations = Array.from({ length: 12 }, (_, index) => ({
      id: 100 + index,
      relation_type: "演变·改称",
      display_relation_type: "改称",
      source: 1,
      target: 2,
      source_timepoint_id: 11,
      target_timepoint_id: 21,
    }));
    const model = buildEvolutionModel({
      entities: [entity(1), entity(2)],
      timepoints: {
        1: [timepoint(11, 1000, "始置")],
        2: [timepoint(21, 1000, "始置")],
      },
      changeRelations,
    }, [1]);
    const layout = layoutEvolutionModel(model, { x: 0, y: 0, width: 100, height: 40 });
    const visible = layout.relations.filter((relation) => relation.labelVisible);
    const hidden = layout.relations.filter((relation) => !relation.labelVisible);

    assert.ok(visible.length > 0);
    assert.ok(hidden.length > 0);
    for (const relation of hidden) {
      assert.equal(relation.labelOverflow, true);
      assert.equal(relation.labelX, null);
      assert.equal(relation.labelY, null);
      assert.equal(relation.labelBounds, null);
      assert.equal(relation.leader, null);
    }
    for (let index = 0; index < visible.length; index += 1) {
      for (let otherIndex = index + 1; otherIndex < visible.length; otherIndex += 1) {
        const firstBox = visible[index].labelBounds;
        const secondBox = visible[otherIndex].labelBounds;
        const overlaps = firstBox.x < secondBox.right
          && firstBox.right > secondBox.x
          && firstBox.y < secondBox.bottom
          && firstBox.bottom > secondBox.y;
        assert.equal(overlaps, false);
      }
    }
  });

  it("无年端进入轴外栏，仍可与有年端绘制关系", () => {
    const model = buildEvolutionModel({
      entities: [entity(1), entity(2)],
      timepoints: {
        1: [timepoint(11, 980, "始置")],
        2: [timepoint(21, null, "年代未明")],
      },
      changeRelations: [{
        id: 8,
        relation_type: "职掌·移交",
        source: 1,
        target: 2,
        source_timepoint_id: 11,
        target_timepoint_id: 21,
      }],
    }, [1]);
    const layout = layoutEvolutionModel(model, { x: 10, y: 20, width: 300, height: 180 });
    const target = layout.relations[0].targetPoints[0];

    assert.ok(layout.offAxisBounds);
    assert.equal(target.offAxis, true);
    assert.equal(target.detailOnly, false);
    assert.ok(target.x >= layout.offAxisBounds.x && target.x <= layout.offAxisBounds.right);
    assert.ok(target.y >= layout.bounds.y && target.y <= layout.bounds.bottom);
    assert.equal(layout.relations[0].drawable, true);
    assert.equal(layout.offAxis.relationEndpoints[0].x, target.x);
  });

  it("关系组含无年端时不伪造共同时间", () => {
    const model = buildEvolutionModel({
      entities: [entity(1), entity(2)],
      timepoints: {
        1: [timepoint(11, 980, "始置")],
        2: [timepoint(21, null, "年代未明")],
      },
      changeRelations: [{
        id: 51,
        relation_type: "演变·分拆",
        relation_group_id: "partial-time",
        source: 1,
        target: 2,
        source_timepoint_id: 11,
        target_timepoint_id: 21,
      }],
    }, [1]);

    const group = layoutEvolutionModel(model).relationGroups[0];
    assert.equal(group.junctionX, null);
    assert.equal(group.divergentEndpointYears, false);
    assert.equal(group.renderMode, "individual");
    assert.equal(group.relations[0].labelVisible, true);
  });

  it("极窄边界仍不让标签、轨道和轴外栏越界", () => {
    const model = buildEvolutionModel({
      entities: [entity(1), entity(2)],
      timepoints: {
        1: [timepoint(11, 1000, "始置"), timepoint(12, null)],
        2: [timepoint(21, null, "年代未明")],
      },
      changeRelations: [{
        id: 61,
        relation_type: "职掌·移交",
        source: 1,
        target: 2,
        source_timepoint_id: 11,
        target_timepoint_id: 21,
      }],
    }, [1]);
    const layout = layoutEvolutionModel(model, { x: 4, y: 6, width: 100, height: 40 });

    assert.ok(layout.labelBounds.x >= layout.bounds.x);
    assert.ok(layout.labelBounds.x + layout.labelBounds.width <= layout.bounds.right);
    assert.ok(layout.plotBounds.x >= layout.bounds.x);
    assert.ok(layout.plotBounds.right <= layout.bounds.right);
    assert.ok(layout.offAxisBounds.x >= layout.bounds.x);
    assert.ok(layout.offAxisBounds.right <= layout.bounds.right);
    assert.ok(layout.lanes[0].events[0].displayX <= layout.bounds.right);
    const relation = layout.relations[0];
    if (relation.labelVisible) {
      assert.equal(relation.labelOverflow, false);
      assert.ok(relation.labelBounds.x >= layout.bounds.x);
      assert.ok(relation.labelBounds.right <= layout.bounds.right);
      assert.ok(relation.labelBounds.y >= layout.bounds.y);
      assert.ok(relation.labelBounds.bottom <= layout.bounds.bottom);
    } else {
      assert.equal(relation.labelOverflow, true);
      assert.equal(relation.labelBounds, null);
    }

    const tiny = layoutEvolutionModel(model, { x: 2, y: 3, width: 30, height: 10 });
    assert.ok(tiny.plotBounds.x >= tiny.bounds.x);
    assert.ok(tiny.plotBounds.right <= tiny.bounds.right);
    assert.equal(tiny.relations[0].labelVisible, false);
    assert.equal(tiny.relations[0].labelOverflow, true);
    assert.equal(tiny.relations[0].labelBounds, null);
  });
});
