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

test("已有数值年的宋前时间仍不进入宋代截面", () => {
  const entity = { id: 1, title: "唐代机构", type: "机构" };
  const preSong = {
    ...timepoint(10, 618, "唐初设置"),
    time_type: "pre_song",
  };
  assert.equal(buildYearSnapshot(dataFor(entity, [preSong]), 1080).entityIds.has(1), false);
});

test("关系另一端有宋代年份时也不展示宋前端点", () => {
  const entity = { id: 1, title: "沿革机构", type: "机构" };
  const preSong = {
    ...timepoint(10, 618, "唐初设置"),
    time_type: "pre_song",
  };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 10, object_timepoint_id: 20 }],
  }];
  const snapshot = buildYearSnapshot(dataFor(entity, [preSong], hierarchyEdges), 1080);
  assert.equal(snapshot.entityIds.has(1), true);
  assert.equal(snapshot.currentTimepointByEntity.get(1), null);
});

test("前序模糊时间点上的关系证据不能越过后继废罢事件复活实体", () => {
  const entity = { id: 1, title: "编修所", type: "机构" };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 10, object_timepoint_id: 20 }],
  }];
  const data = dataFor(entity, [
    {
      ...timepoint(10, 1069, "编修法令"),
      year_end: 1077,
      time_type: "bounded",
      succ_id: 11,
    },
    timepoint(11, 1075, "废罢", { prev_id: 10 }),
  ], hierarchyEdges);
  assert.equal(buildYearSnapshot(data, 1074).entityIds.has(1), false);
  assert.equal(buildYearSnapshot(data, 1080).entityIds.has(1), false);
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

test("由旧名复改称为当前实体会重新激活", () => {
  const entity = { id: 1, title: "国子监", type: "机构" };
  const snapshot = buildYearSnapshot(dataFor(entity, [
    timepoint(10, 989, "改称国子学"),
    timepoint(11, 994, "由国子学复改称国子监", { prev_id: 10 }),
  ]), 1080);
  assert.equal(snapshot.entityIds.has(1), true);
});

test("新实体名称只含旧实体后缀时不能把旧实体激活", () => {
  const entity = { id: 1, title: "茶库", type: "机构" };
  assert.equal(
    classifyExistenceEffect(timepoint(10, 1003, "废罢，二库合并为都茶库"), entity),
    "deactivate",
  );
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

test("罢下属机构不能终止上级机构", () => {
  const entity = { id: 1, title: "三司", type: "机构" };
  assert.equal(
    classifyExistenceEffect(timepoint(10, 1080, "罢帐司勾院磨勘提举司"), entity),
    "preserve",
  );
  assert.equal(
    classifyExistenceEffect(timepoint(11, 1082, "罢三司，职事归户部"), entity),
    "deactivate",
  );
});

test("不复置内部官职不能终止所属机构", () => {
  const entity = { id: 1, title: "太常寺", type: "机构" };
  assert.equal(
    classifyExistenceEffect(timepoint(10, 1052, "不复置职事主簿"), entity),
    "preserve",
  );
  assert.equal(
    classifyExistenceEffect(timepoint(11, 1052, "此后不复置"), entity),
    "deactivate",
  );
});

test("实体名只是内部官职前缀时不能视为实体自身被罢", () => {
  const entity = { id: 1, title: "太仆寺", type: "机构" };
  assert.equal(
    classifyExistenceEffect(timepoint(10, 1120, "罢太仆寺主簿一员，复为一员"), entity),
    "preserve",
  );
  assert.equal(
    classifyExistenceEffect(timepoint(11, 1121, "罢太仆寺，职事并归兵部驾部"), entity),
    "deactivate",
  );
});

test("下属机构改名不终止上级，省略主语的自身改制才终止", () => {
  const entity = { id: 1, title: "三司", type: "机构" };
  assert.equal(
    classifyExistenceEffect(timepoint(10, 1022, "征欠司改为蠲纳司"), entity),
    "preserve",
  );
  assert.equal(
    classifyExistenceEffect(timepoint(11, 993, "改为总计司"), entity),
    "deactivate",
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

test("有纪年的关系状态可证明无纪年上级在当年存在", () => {
  const parent = { id: 1, title: "上级机构", type: "机构" };
  const undatedParent = {
    id: 10,
    year_start: null,
    year_end: null,
    time_type: "undated",
    event: "下级机构的上级",
    prev_id: null,
  };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 10, object_timepoint_id: 20 }],
  }];
  const snapshot = buildYearSnapshot(dataFor(parent, [undatedParent], hierarchyEdges), 1000);
  assert.equal(snapshot.entityIds.has(1), true);
  assert.equal(snapshot.hierarchyEdges.length, 1);
});

test("关系存在证据不能越过同年或更晚的明确罢废", () => {
  const parent = { id: 1, title: "上级机构", type: "机构" };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 10, object_timepoint_id: 20 }],
  }];
  const data = dataFor(parent, [
    timepoint(10, 1000, "罢"),
  ], hierarchyEdges);
  assert.equal(buildYearSnapshot(data, 1000).entityIds.has(1), false);
});

test("明确罢废后更晚的旧关系证据也不能复活实体", () => {
  const parent = { id: 1, title: "名存实废机构", type: "机构" };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 12, object_timepoint_id: 20 }],
  }];
  const data = dataFor(parent, [
    timepoint(10, 960, "实体官署实废"),
    timepoint(12, 1009, "旧名义隶属记载", { prev_id: 10 }),
  ], hierarchyEdges);
  assert.equal(buildYearSnapshot(data, 1080).entityIds.has(1), false);
});

test("明确复置后关系证据可继续证明实体存在", () => {
  const parent = { id: 1, title: "重建机构", type: "机构" };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 12, object_timepoint_id: 20 }],
  }];
  const data = dataFor(parent, [
    timepoint(10, 960, "实体官署实废"),
    timepoint(11, 1070, "复置", { prev_id: 10 }),
    timepoint(12, 1071, "统领下属", { prev_id: 11 }),
  ], hierarchyEdges);
  assert.equal(buildYearSnapshot(data, 1080).entityIds.has(1), true);
  assert.equal(buildYearSnapshot(data, 1080).hierarchyEdges.length, 1);
});

test("临时机构只在原文明载的活动时间窗内显示", () => {
  const entity = { id: 1, title: "临时编修所", type: "机构" };
  const data = dataFor(entity, [
    timepoint(10, 1050, "始置", { attr_category: "临时机构" }),
    timepoint(11, 1053, "继续参定", { prev_id: 10, attr_category: "临时机构" }),
  ]);
  assert.equal(buildYearSnapshot(data, 1052).entityIds.has(1), true);
  assert.equal(buildYearSnapshot(data, 1080).entityIds.has(1), false);
});

test("临时机构多次开设之间的空档不被连成连续存在期", () => {
  const entity = { id: 1, title: "临时实录院", type: "机构" };
  const data = dataFor(entity, [
    timepoint(10, 998, "临时开设", { attr_category: "临时机构" }),
    timepoint(11, 1082, "遇修实录临时开设", { prev_id: 10, attr_category: "临时机构" }),
  ]);
  assert.equal(buildYearSnapshot(data, 998).entityIds.has(1), true);
  assert.equal(buildYearSnapshot(data, 1080).entityIds.has(1), false);
  assert.equal(buildYearSnapshot(data, 1082).entityIds.has(1), true);
});

test("罢废和废罢复合词明确终止当前实体", () => {
  const entity = { id: 1, title: "某司", type: "机构" };
  assert.equal(classifyExistenceEffect(timepoint(10, 1058, "废罢，归其他机构兼领"), entity), "deactivate");
  assert.equal(classifyExistenceEffect(timepoint(11, 1071, "罢废，职事归某寺"), entity), "deactivate");
});

test("省略当前主语的合并和复分会终止来源实体", () => {
  const entity = { id: 1, title: "内剥马务", type: "机构" };
  assert.equal(
    classifyExistenceEffect(timepoint(10, 1072, "与外剥马务合为皮剥所"), entity),
    "deactivate",
  );
  assert.equal(
    classifyExistenceEffect(timepoint(11, 988, "复分为马军、步军粮料院"), entity),
    "deactivate",
  );
});

test("逗号后与其他子库合并沿用前句主语而不终止上级", () => {
  const entity = { id: 1, title: "左藏库", type: "机构" };
  assert.equal(
    classifyExistenceEffect(
      timepoint(10, 1009, "钱库、金银库、丝绵库合并，与生色匹库、杂色匹库合为三库"),
      entity,
    ),
    "preserve",
  );
});

test("分设下级时同一父端关系证明上级继续存在", () => {
  const entity = { id: 1, title: "内藏库", type: "机构" };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 10, object_timepoint_id: 20 }],
  }];
  const snapshot = buildYearSnapshot(dataFor(entity, [
    timepoint(10, 1015, "分为金银、珠玉香药、锦帛、钱四库"),
  ], hierarchyEdges), 1080);
  assert.equal(snapshot.entityIds.has(1), true);
  assert.equal(snapshot.entityIds.has(2), true);
  assert.equal(snapshot.hierarchyEdges.length, 1);
});

test("分设关系补在同一链后继节点时上级仍继续存在", () => {
  const entity = { id: 1, title: "左藏库", type: "机构" };
  const hierarchyEdges = [{
    id: 30,
    parent: 1,
    child: 2,
    periods: [],
    states: [{ id: 30, subject_timepoint_id: 11, object_timepoint_id: 20 }],
  }];
  const snapshot = buildYearSnapshot(dataFor(entity, [
    timepoint(10, 977, "分为三库", { succ_id: 11 }),
    timepoint(11, 993, "下分四类库藏", { prev_id: 10 }),
  ], hierarchyEdges), 1080);
  assert.equal(snapshot.entityIds.has(1), true);
  assert.equal(snapshot.hierarchyEdges.length, 1);
});

test("统一改称和避讳改为会终止旧实体", () => {
  const entity = { id: 1, title: "旧机构", type: "机构" };
  assert.equal(classifyExistenceEffect(timepoint(10, 1005, "统一改称监"), entity), "deactivate");
  assert.equal(classifyExistenceEffect(timepoint(11, 960, "避讳改为昭文馆"), entity), "deactivate");
  assert.equal(classifyExistenceEffect(timepoint(12, 994, "复改称国子监"), entity), "deactivate");
});

test("明确写实体官署实废时不被后续名号记载保留", () => {
  const entity = { id: 1, title: "进奏院", type: "机构" };
  assert.equal(
    classifyExistenceEffect(timepoint(10, 982, "诸州进奏院归并都进奏院，实体官署实废但各州朱记名仍存"), entity),
    "deactivate",
  );
});

test("空存其名的机构不显示，正式建置后恢复", () => {
  const entity = { id: 1, title: "尚食局", type: "机构" };
  assert.equal(classifyExistenceEffect(timepoint(10, 960, "空存其名，职事归御厨"), entity), "deactivate");
  assert.equal(classifyExistenceEffect(timepoint(11, 1103, "正式建置，供御膳羞"), entity), "activate");
});
