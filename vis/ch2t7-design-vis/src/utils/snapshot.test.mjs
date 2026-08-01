import assert from "node:assert/strict";
import test from "node:test";

import { buildYearSnapshot, classifyExistenceEffect } from "./snapshot.js";

function timepoint(id, year, event, extra = {}) {
  return {
    id,
    year_start: year,
    year_end: year,
    time_type: "exact",
    event,
    prev_id: null,
    ...extra,
  };
}

function dataFor(entity, timepoints, hierarchyEdges = []) {
  return {
    entities: [entity, { id: 2, title: "下级机构", type: "机构" }],
    timepoints: {
      [entity.id]: timepoints,
      2: [timepoint(20, 1000, "始置")],
    },
    hierarchyEdges,
    staffEdges: [],
  };
}

test("罢废后的普通记载不会自动复活实体", () => {
  const entity = { id: 1, title: "朝集院", type: "机构" };
  const snapshot = buildYearSnapshot(dataFor(entity, [
    timepoint(10, 1001, "始置于京师朱雀门外，房舍百余区，旋罢"),
    timepoint(11, 1071, "朝集院房舍陆续拨归太学、律学、医学"),
  ]), 1071);
  assert.equal(snapshot.entityIds.has(1), false);
});

test("明确复置会重新激活此前罢废的实体", () => {
  const entity = { id: 1, title: "某院", type: "机构" };
  const snapshot = buildYearSnapshot(dataFor(entity, [
    timepoint(10, 1000, "始置"),
    timepoint(11, 1010, "罢"),
    timepoint(12, 1020, "复置"),
  ]), 1020);
  assert.equal(snapshot.entityIds.has(1), true);
});

test("拟复置未果不会重新激活实体", () => {
  const entity = { id: 1, title: "某院", type: "机构" };
  const snapshot = buildYearSnapshot(dataFor(entity, [
    timepoint(10, 1000, "始置"),
    timepoint(11, 1010, "罢"),
    timepoint(12, 1020, "诏拟复置，因台官谏阻未果"),
  ]), 1020);
  assert.equal(snapshot.entityIds.has(1), false);
});

test("不复置等否定表达不能被内部的复置字样误判为恢复", () => {
  const entity = { id: 1, title: "某院", type: "机构" };
  assert.equal(classifyExistenceEffect(timepoint(10, 1020, "此后不复置"), entity), "deactivate");
  assert.notEqual(classifyExistenceEffect(timepoint(11, 1020, "未设置专门机构"), entity), "activate");
});

test("模糊时段的存废变化到区间上界才保守生效", () => {
  const entity = { id: 1, title: "某院", type: "机构" };
  const data = dataFor(entity, [
    timepoint(10, 1000, "始置"),
    {
      ...timepoint(11, 1010, "消亡"),
      year_end: 1015,
      time_type: "bounded",
    },
  ]);
  assert.equal(buildYearSnapshot(data, 1014).entityIds.has(1), true);
  assert.equal(buildYearSnapshot(data, 1015).entityIds.has(1), false);
});

test("单独一条模糊时段普通记载不足以断言实体存在", () => {
  const entity = { id: 1, title: "某院", type: "机构" };
  const data = dataFor(entity, [{
    ...timepoint(10, 1010, "掌管文书收发"),
    year_end: 1015,
    time_type: "bounded",
  }]);
  assert.equal(buildYearSnapshot(data, 1015).entityIds.has(1), false);
});

test("首次普通的同时代记载仍可作为存在证据", () => {
  const entity = { id: 1, title: "某院", type: "机构" };
  const snapshot = buildYearSnapshot(dataFor(entity, [
    timepoint(10, 1000, "掌管文书收发"),
  ]), 1000);
  assert.equal(snapshot.entityIds.has(1), true);
});

test("罢内部官职但机构之名犹存时不误杀机构", () => {
  const entity = { id: 1, title: "起居院", type: "机构" };
  assert.equal(
    classifyExistenceEffect(
      timepoint(10, 1082, "新官制下罢起居院同修起居注，但起居院之名犹存"),
      entity,
    ),
    "activate",
  );
});

test("接收并入对象不会被当成接收方自身终止", () => {
  const entity = { id: 1, title: "审官院", type: "机构" };
  assert.equal(
    classifyExistenceEffect(timepoint(10, 993, "接收并入的差遣院"), entity),
    "preserve",
  );
});

test("端点实体罢废后对应关系也退出快照", () => {
  const entity = { id: 1, title: "上级机构", type: "机构" };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 10, object_timepoint_id: 20 }],
  }];
  const data = dataFor(entity, [
    timepoint(10, 1000, "始置"),
    timepoint(11, 1010, "罢", { prev_id: 10 }),
    timepoint(12, 1020, "旧址改作仓库", { prev_id: 11 }),
  ], hierarchyEdges);
  assert.equal(buildYearSnapshot(data, 1005).hierarchyEdges.length, 1);
  assert.equal(buildYearSnapshot(data, 1020).hierarchyEdges.length, 0);
});
