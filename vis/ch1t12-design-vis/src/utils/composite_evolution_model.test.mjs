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

test("综合模型保留官职但不把编制关系伪装成机构树父子关系", () => {
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
  assert.equal(model.nodesById.get(3).parentId, null);
  assert.equal(model.nodesById.get(3).nodeKind, "official");
  assert.equal(model.nodesById.get(3).depth, 0);
  assert.deepEqual(model.officialsByInstitution.get(2).map((node) => node.id), [3]);
  assert.deepEqual(visibleCompositeNodes(model, [1, 2]).map((node) => node.id), [1, 2]);
});

test("变化按名称、机构设置、官员设置和职责四类归档", () => {
  assert.equal(classifyCompositeChange({ text: "改称尚书省", entityType: "机构" }), "name");
  assert.equal(classifyCompositeChange({ text: "元丰改置", entityType: "机构" }), "structure");
  assert.equal(classifyCompositeChange({ text: "增置官一员", entityType: "官职" }), "staff");
  assert.equal(classifyCompositeChange({ text: "掌天下财赋", entityType: "机构" }), "duty");
});

test("按入口年份生成机构树，不把不同时期的下属机构合并", () => {
  const modelAt1050 = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "根机构", type: "机构" },
      { id: 2, title: "早期下属", type: "机构" },
      { id: 3, title: "后期下属", type: "机构" },
    ],
    timepoints: {
      1: [point(11, 1, 1000, "沿置", { time_type: "exact" })],
      2: [point(21, 2, 1000, "始置", { time_type: "exact" })],
      3: [point(31, 3, 1100, "始置", { time_type: "exact" })],
    },
    hierarchyEdges: [
      { id: 101, parent: 1, child: 2, states: [{ id: 101, effective_year: 1000, subject_timepoint_id: 11, object_timepoint_id: 21 }] },
      { id: 102, parent: 1, child: 3, states: [{ id: 102, effective_year: 1100, subject_timepoint_id: 11, object_timepoint_id: 31 }] },
    ],
  }, 1, { year: 1050 });
  assert.deepEqual(modelAt1050.treeNodes.map((node) => node.id), [1, 2]);
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
  assert.equal(relation.iconType, "affiliation_change");
});

test("上下级关系变更只在机构信息带生成一条菱形改隶事件", () => {
  const model = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "甲司", type: "机构" },
      { id: 2, title: "乙司", type: "机构" },
      { id: 3, title: "丙署", type: "机构" },
    ],
    timepoints: {
      1: [point(11, 1, 1000, "统属丙署")],
      2: [point(21, 2, 1050, "统属丙署")],
      3: [
        point(31, 3, 1000, "隶甲司"),
        point(32, 3, 1050, "改隶乙司", { event_type: "affiliation_change" }),
      ],
    },
    hierarchyEdges: [
      { id: 101, parent: 1, child: 3, states: [{ id: 101, subject_timepoint_id: 11, object_timepoint_id: 31 }] },
      { id: 102, parent: 2, child: 3, states: [{ id: 102, subject_timepoint_id: 21, object_timepoint_id: 32 }] },
    ],
  }, 3, { year: 1050 });

  const events = model.bands.institution.filter((event) => event.iconType === "affiliation_change");
  assert.equal(events.length, 1);
  assert.equal(events[0].id, "T32");
  assert.equal(events[0].subject.title, "丙署");
  assert.deepEqual(events[0].sourceEndpoints.map((item) => item.title), ["甲司"]);
  assert.deepEqual(events[0].targetEndpoints.map((item) => item.title), ["乙司"]);
  assert.deepEqual(events[0].evidenceKeys, ["T32", "R101", "R102"]);
});

test("没有显式改隶文字时仍从上下级关系派生只读菱形事件", () => {
  const model = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "甲司", type: "机构" },
      { id: 2, title: "乙司", type: "机构" },
      { id: 3, title: "丙署", type: "机构" },
    ],
    timepoints: {
      1: [point(11, 1, 1000, "统属丙署")],
      2: [point(21, 2, 1050, "统属丙署")],
      3: [point(31, 3, 1000, "隶甲司")],
    },
    hierarchyEdges: [
      { id: 101, parent: 1, child: 3, states: [{ id: 101, subject_timepoint_id: 11, object_timepoint_id: 31 }] },
      { id: 102, parent: 2, child: 3, states: [{ id: 102, effective_year: 1050 }] },
    ],
  }, 3, { year: 1050 });

  const event = model.bands.institution.find((item) => item.id.startsWith("H:reparent:"));
  assert.equal(event.iconType, "affiliation_change");
  assert.equal(event.displayTitle, "甲司 → 乙司");
  assert.equal(event.editableTarget, null);
});

test("机构存废事件只留在主线，不重复进入机构结构信息带", () => {
  const model = buildCompositeEvolutionModel({
    entities: [{ id: 1, title: "甲司", type: "机构" }],
    timepoints: {
      1: [
        point(11, 1, 1000, "始置", { event_type: "establish" }),
        point(12, 1, 1050, "罢置", { event_type: "abolish" }),
        point(13, 1, 1060, "复置", { event_type: "restore" }),
        point(14, 1, 1070, "改置为甲司", { event_type: "record" }),
      ],
    },
  }, 1);

  assert.equal(model.bands.institution.some((event) => ["T11", "T12", "T13"].includes(event.id)), false);
  assert.ok(model.bands.institution.some((event) => event.id === "T14"));
});

test("普通机构记载不冒充结构演变事件", () => {
  const model = buildCompositeEvolutionModel({
    entities: [{ id: 1, title: "秘书省", type: "机构" }],
    timepoints: {
      1: [
        point(11, 1, 1135, "仿唐十八学士制扩馆职，总计二十一人"),
        point(12, 1, 1136, "改置秘书省"),
      ],
    },
  }, 1);

  assert.equal(model.bands.institution.some((event) => event.id === "T11"), false);
  assert.equal(model.bands.institution.some((event) => event.id === "T12"), true);
});

test("前后演变点使用目标端点生效时间并排除纯宋前关系", () => {
  const model = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "旧机构", type: "机构" },
      { id: 2, title: "新机构", type: "机构" },
    ],
    timepoints: {},
    changeRelations: [
      {
        id: 501,
        relation_type: "前后演变",
        source: 1,
        target: 2,
        source_timepoint_id: 11,
        target_timepoint_id: 21,
        source_time: { year_start: 1126, raw_time: "北宋靖康元年", time_type: "exact" },
        target_time: { year_start: 1129, raw_time: "南宋建炎三年", time_type: "exact" },
      },
      {
        id: 502,
        relation_type: "前后演变",
        source: 1,
        target: 2,
        source_time: { year_start: 607, raw_time: "隋大业三年", time_type: "pre_song" },
        target_time: { year_start: 607, raw_time: "隋大业三年", time_type: "pre_song" },
      },
    ],
  }, 1);

  const event = model.bands.institution.find((item) => item.id === "R501");
  assert.equal(event.yearStart, 1129);
  assert.equal(event.eventTime, "南宋建炎三年");
  assert.equal(model.bands.institution.some((item) => item.id === "R502"), false);
});

test("明确前后演变关系优先于同源端点时间点，机构带不重复生成两个点", () => {
  const model = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "国子监", type: "机构" },
      { id: 2, title: "国子学", type: "机构" },
    ],
    timepoints: {
      1: [point(11, 1, 989, "沿置")],
      2: [point(21, 2, 989, "改称国子学")],
    },
    changeRelations: [{
      id: 501,
      relation_type: "前后演变",
      source: 1,
      target: 2,
      source_timepoint_id: 11,
      target_timepoint_id: 21,
      source_time: { year_start: 989, raw_time: "北宋端拱二年", time_type: "exact" },
      target_time: { year_start: 989, raw_time: "北宋端拱二年", time_type: "exact" },
    }],
  }, 1);

  assert.deepEqual(model.bands.institution.map((event) => event.id), ["R501"]);
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

test("综合模型输出三条信息带并保留编制端点", () => {
  const model = buildCompositeEvolutionModel({
    entities: [
      { id: 1, title: "尚书省", type: "机构" },
      { id: 2, title: "吏部", type: "机构" },
      { id: 3, title: "尚书左丞", type: "官职" },
    ],
    timepoints: {
      1: [point(11, 1, 1080, "改置尚书省")],
      2: [point(21, 2, 1080, "掌选事")],
      3: [point(31, 3, 1080, "增置尚书左丞")],
    },
    hierarchyEdges: [{ id: 101, parent: 1, child: 2, periods: [{ start: 1000, end: 1200 }] }],
    staffEdges: [{ id: 201, org: 2, official: 3, periods: [{ start: 1000, end: 1200 }], staff_quota: "二员", staff_type: "官" }],
  }, 1, { year: 1080 });

  assert.ok(model.bands.institution.some((event) => event.band === "institution"));
  assert.ok(model.bands.duty.some((event) => event.band === "duty"));
  const staff = model.bands.staff.find((event) => event.id.startsWith("S201"));
  assert.equal(staff.subject.title, "尚书左丞");
  assert.equal(staff.displaySummary, "二员，官");
  assert.equal(staff.sourceEndpoints[0].title, "吏部");
  const rankChange = model.bands.staff.find((event) => event.id === "T31");
  assert.equal(rankChange.sourceEndpoints[0].title, "吏部");
  assert.equal(rankChange.targetEndpoints[0].title, "尚书左丞");
  assert.equal(rankChange.editableTarget.editorType, "staff_timepoint");
});
