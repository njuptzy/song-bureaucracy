import assert from "node:assert/strict";
import test from "node:test";
import {
  buildCompositeEvolutionModel,
  classifyCompositeChange,
  visibleCompositeNodes,
} from "./composite_evolution_model.js";

function point(id, entityId, year, event, extra = {}) {
  return {
    id,
    entity_id: entityId,
    year_start: year,
    year_end: year,
    time: String(year),
    event,
    lifecycle_effect: "preserve",
    ...extra,
  };
}

test("综合模型包含焦点机构、下属机构和官职", () => {
  const model = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "尚书省", type: "机构" },
      { id: 2, title: "吏部", type: "机构" },
      { id: 3, title: "尚书左仆射", type: "官职" },
      { id: 4, title: "无关机构", type: "机构" },
    ],
    timepoints: {
      1: [point(11, 1, 1069, "沿置")],
      2: [point(21, 2, 1078, "改置吏部")],
      3: [point(31, 3, 1078, "增置尚书左仆射")],
      4: [point(41, 4, 1078, "沿置")],
    },
    hierarchyEdges: [{ id: 101, parent: 1, child: 2 }],
    staffEdges: [{ id: 201, org: 2, official: 3, staff_quota: "一员" }],
  }, 1);

  assert.deepEqual(model.nodes.map((node) => node.id), [1, 2, 3]);
  assert.equal(model.nodesById.get(2).parentId, 1);
  assert.equal(model.nodesById.get(3).parentId, 2);
  assert.equal(model.nodesById.get(3).nodeKind, "official");
  assert.equal(model.nodesById.get(3).depth, 2);
});

test("变化按名称、机构设置、官员设置和职责四类归档", () => {
  assert.equal(classifyCompositeChange({ text: "改称尚书省", entityType: "机构" }), "name");
  assert.equal(classifyCompositeChange({ text: "元丰改置", entityType: "机构" }), "structure");
  assert.equal(classifyCompositeChange({ text: "增置官一员", entityType: "官职" }), "staff");
  assert.equal(classifyCompositeChange({ text: "掌天下财赋", entityType: "机构" }), "duty");
});

test("综合模型保留多端点关系和关系级证据", () => {
  const model = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "甲司", type: "机构" },
      { id: 2, title: "乙司", type: "机构" },
      { id: 3, title: "丙署", type: "机构" },
    ],
    timepoints: {
      1: [point(11, 1, 1000, "沿置")],
      2: [point(21, 2, 1050, "沿置")],
      3: [point(31, 3, 1050, "改隶")],
    },
    hierarchyEdges: [{ id: 101, parent: 1, child: 3 }],
    changeRelations: [{
      id: 501,
      relation_subtype: "改隶事件",
      sourceMembers: [{ entityId: 1, timepointId: 11, effectiveYear: 1000 }],
      targetMembers: [
        { entityId: 2, timepointId: 21, effectiveYear: 1050 },
        { entityId: 3, timepointId: 31, effectiveYear: 1050 },
      ],
    }],
    citations: {
      R501: [{ citation: "《宋会要·职官》", quotation: "甲司改隶乙司、丙署" }],
    },
  }, 1);

  const relation = model.changes.find((change) => change.id === "R501");
  assert.deepEqual(relation.sourceIds, [1]);
  assert.deepEqual(relation.targetIds, [2, 3]);
  assert.equal(relation.uncertain, true);
  assert.deepEqual(relation.citationKeys, ["R501"]);
  assert.equal(relation.citations[0].quotation, "甲司改隶乙司、丙署");
});

test("展开状态只影响可见节点，不改变节点相对父子关系", () => {
  const model = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "根", type: "机构" },
      { id: 2, title: "子", type: "机构" },
      { id: 3, title: "孙", type: "机构" },
    ],
    timepoints: {},
    hierarchyEdges: [
      { id: 1, parent: 1, child: 2 },
      { id: 2, parent: 2, child: 3 },
    ],
  }, 1);
  assert.deepEqual(visibleCompositeNodes(model, [1]).map((node) => node.id), [1, 2]);
  assert.deepEqual(visibleCompositeNodes(model, [1, 2]).map((node) => node.id), [1, 2, 3]);
  assert.equal(model.nodesById.get(3).parentId, 2);
});
