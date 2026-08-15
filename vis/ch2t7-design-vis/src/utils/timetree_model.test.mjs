import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  buildTimetreeRows,
  defaultTimetreeExpandedKeys,
  timetreeEntityKey,
  timetreeGroupKey,
  timetreeLaneEntityIds,
  toggleTimetreeExpansion,
} from "./timetree_model.js";

const CENTRAL_GROUPS = ["决策中枢", "行政执行"];

function entity(id, title, overrides = {}) {
  return { id, title, type: "机构", category: "中央机构", ...overrides };
}

describe("buildTimetreeRows", () => {
  it("无制度组配置时根节点直接位于第 0 层", () => {
    const rows = buildTimetreeRows({
      entities: [entity(1, "甲司"), entity(2, "乙司")],
      hierarchyEdges: [],
      category: "中央机构",
      groupNames: [],
      expandedIds: new Set(),
    });
    assert.deepEqual(rows.map((row) => [row.entityId, row.depth]), [[1, 0], [2, 0]]);
  });

  it("制度组作为虚拟行参与排序，收起时带下级计数", () => {
    const rows = buildTimetreeRows({
      entities: [
        entity(1, "甲司", { central_group: "决策中枢" }),
        entity(2, "乙司", { central_group: "行政执行" }),
        entity(3, "丙司", { central_group: "行政执行" }),
      ],
      hierarchyEdges: [],
      category: "中央机构",
      groupNames: CENTRAL_GROUPS,
      expandedIds: new Set(),
    });
    assert.deepEqual(rows.map((row) => row.title), ["决策中枢", "行政执行"]);
    assert.ok(rows.every((row) => row.isVirtual));
    assert.deepEqual(rows.map((row) => row.childCount), [1, 2]);
  });

  it("展开制度组后按前序输出机构行，展开机构显示下级", () => {
    const rows = buildTimetreeRows({
      entities: [
        entity(1, "甲司", { central_group: "决策中枢" }),
        entity(2, "乙司", { central_group: "行政执行" }),
        entity(3, "丙司"),
      ],
      hierarchyEdges: [{ parent: 2, child: 3 }],
      category: "中央机构",
      groupNames: CENTRAL_GROUPS,
      expandedIds: new Set([
        timetreeGroupKey("中央机构", "行政执行"),
        timetreeEntityKey(2),
      ]),
    });
    assert.deepEqual(
      rows.map((row) => [row.title, row.depth, row.isVirtual]),
      [
        ["决策中枢", 0, true],
        ["行政执行", 0, true],
        ["乙司", 1, false],
        ["丙司", 2, false],
      ],
    );
  });

  it("旋转后父节点位于多个子节点的纵向中心", () => {
    const rows = buildTimetreeRows({
      entities: [entity(1, "中枢"), entity(2, "甲司"), entity(3, "乙司"), entity(4, "丙司")],
      hierarchyEdges: [
        { parent: 1, child: 2 },
        { parent: 1, child: 3 },
        { parent: 1, child: 4 },
      ],
      category: "中央机构",
      groupNames: [],
      expandedIds: new Set([timetreeEntityKey(1)]),
    });
    const byTitle = new Map(rows.map((row) => [row.title, row]));
    assert.equal(byTitle.get("中枢").layoutIndex, 1);
    assert.deepEqual(
      ["甲司", "乙司", "丙司"]
        .map((title) => byTitle.get(title).layoutIndex)
        .sort((a, b) => a - b),
      [0, 1, 2],
    );
  });

  it("多层旋转树保持各级父节点对子树居中", () => {
    const rows = buildTimetreeRows({
      entities: [
        entity(1, "根"), entity(2, "左支"), entity(3, "右支"),
        entity(4, "左一"), entity(5, "左二"), entity(6, "右一"),
      ],
      hierarchyEdges: [
        { parent: 1, child: 2 }, { parent: 1, child: 3 },
        { parent: 2, child: 4 }, { parent: 2, child: 5 },
        { parent: 3, child: 6 },
      ],
      category: "中央机构",
      groupNames: [],
      expandedIds: new Set([
        timetreeEntityKey(1), timetreeEntityKey(2), timetreeEntityKey(3),
      ]),
    });
    const byTitle = new Map(rows.map((row) => [row.title, row]));
    assert.equal(
      byTitle.get("左支").layoutIndex,
      (byTitle.get("左一").layoutIndex + byTitle.get("左二").layoutIndex) / 2,
    );
    assert.equal(byTitle.get("右支").layoutIndex, byTitle.get("右一").layoutIndex);
    assert.equal(
      byTitle.get("根").layoutIndex,
      (byTitle.get("左支").layoutIndex + byTitle.get("右支").layoutIndex) / 2,
    );
    assert.notEqual(byTitle.get("左一").layoutIndex, byTitle.get("左二").layoutIndex);
  });

  it("层级边成环时不死循环", () => {
    const rows = buildTimetreeRows({
      entities: [entity(1, "甲司"), entity(2, "乙司")],
      hierarchyEdges: [
        { parent: 1, child: 2 },
        { parent: 2, child: 1 },
      ],
      category: "中央机构",
      groupNames: [],
      expandedIds: new Set([timetreeEntityKey(1), timetreeEntityKey(2)]),
    });
    assert.ok(rows.length <= 2);
  });

  it("统称实体与其他分类不进入行", () => {
    const rows = buildTimetreeRows({
      entities: [
        entity(1, "甲司"),
        entity(2, "统称甲"),
        entity(3, "州县甲", { category: "州县机构" }),
        entity(4, "某官", { type: "官职" }),
      ],
      hierarchyEdges: [],
      category: "中央机构",
      collectiveIds: [2],
      groupNames: [],
      expandedIds: new Set(),
    });
    assert.deepEqual(rows.map((row) => row.entityId), [1]);
  });

  it("车道实体列表只含非虚拟行且保持行序", () => {
    const rows = buildTimetreeRows({
      entities: [
        entity(1, "甲司", { central_group: "决策中枢" }),
        entity(2, "乙司", { central_group: "行政执行" }),
      ],
      hierarchyEdges: [],
      category: "中央机构",
      groupNames: CENTRAL_GROUPS,
      expandedIds: new Set(CENTRAL_GROUPS.map((group) => timetreeGroupKey("中央机构", group))),
    });
    assert.deepEqual(timetreeLaneEntityIds(rows), [1, 2]);
  });

  it("制度组展开与层次结构一样互斥", () => {
    const rows = [
      { key: "group:a", isVirtual: true, parentKey: null },
      { key: "group:b", isVirtual: true, parentKey: null },
    ];
    assert.deepEqual(toggleTimetreeExpansion(rows, ["group:a"], "group:b"), ["group:b"]);
    assert.deepEqual(toggleTimetreeExpansion(rows, ["group:a"], "group:a"), []);
  });

  it("机构展开只保留当前祖先路径，收起时移除后代", () => {
    const rows = [
      { key: "group:a", isVirtual: true, parentKey: null },
      { key: "entity:1", isVirtual: false, parentKey: "group:a" },
      { key: "entity:2", isVirtual: false, parentKey: "entity:1" },
      { key: "entity:3", isVirtual: false, parentKey: "group:a" },
    ];
    assert.deepEqual(
      toggleTimetreeExpansion(rows, ["group:a", "entity:3"], "entity:2"),
      ["group:a", "entity:1", "entity:2"],
    );
    assert.deepEqual(
      toggleTimetreeExpansion(
        rows,
        ["group:a", "entity:1", "entity:2"],
        "entity:1",
      ),
      ["group:a"],
    );
  });
});

describe("defaultTimetreeExpandedKeys", () => {
  it("默认只展开首个有数据的制度组、机构保持收起", () => {
    const keys = defaultTimetreeExpandedKeys({
      entities: [
        entity(1, "甲司", { central_group: "决策中枢" }),
        entity(2, "乙司", { central_group: "行政执行" }),
      ],
      category: "中央机构",
      groupNames: CENTRAL_GROUPS,
    });
    assert.deepEqual(keys, [timetreeGroupKey("中央机构", "决策中枢")]);
  });

  it("无制度组配置时默认全部收起", () => {
    assert.deepEqual(defaultTimetreeExpandedKeys({
      entities: [entity(1, "甲司")],
      category: "路级机构",
      groupNames: [],
    }), []);
  });
});
