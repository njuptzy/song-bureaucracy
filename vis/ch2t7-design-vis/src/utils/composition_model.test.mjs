import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  buildCompositionModel,
  dedupeStaffEdges,
  quotaLabel,
  staffTextOf,
} from "./composition_model.js";

const entities = [
  { id: 1, title: "尚书省", type: "机构" },
  { id: 2, title: "尚书都省", type: "机构" },
  { id: 3, title: "尚书省吏部", type: "机构" },
  { id: 4, title: "尚书省户部", type: "机构" },
  { id: 5, title: "吏部尚书左选", type: "机构" },
  { id: 6, title: "司封司", type: "机构" },
  { id: 7, title: "户部左曹", type: "机构" },
  { id: 10, title: "郎中", type: "官职" },
  { id: 11, title: "令史", type: "官职" },
  { id: 12, title: "书令史", type: "官职" },
  { id: 13, title: "主事", type: "官职" },
];
const entityMap = new Map(entities.map((e) => [e.id, e]));
const titleOf = (id) => entityMap.get(id)?.title ?? "";

const hierarchy = {
  1: [{ child: 2 }, { child: 4 }, { child: 3 }],
  3: [{ child: 5 }, { child: 6 }],
  4: [{ child: 7 }],
};
const childrenFor = (id) => hierarchy[id] || [];

const staff = {
  1: [{ official: 13, staff_quota: 6, staff_type: "官" }],
  3: [
    { official: 10, staff_quota: 1, staff_type: "官" },
    { official: 11, staff_quota: 14, staff_type: "吏" },
    { official: 12, staff_quota: 35, staff_type: "吏" },
  ],
  5: [{ official: 10, staff_quota: 1, staff_type: "官" }],
  6: [],
};
const staffFor = (id) => staff[id] || [];

describe("quotaLabel", () => {
  it("小整数转中文数字", () => {
    assert.equal(quotaLabel(1), "一人");
    assert.equal(quotaLabel(10), "十人");
  });
  it("大整数保持阿拉伯数字", () => {
    assert.equal(quotaLabel(35), "35人");
  });
  it("字符串员额原样保留并补单位", () => {
    assert.equal(quotaLabel("二员"), "二员");
    assert.equal(quotaLabel("若干"), "若干人");
  });
  it("空值返回空串", () => {
    assert.equal(quotaLabel(null), "");
    assert.equal(quotaLabel(""), "");
  });
});

describe("staffTextOf", () => {
  it("官序列在前、吏序列在后，员额从大到小", () => {
    const { text } = staffTextOf(staff[3], entityMap, titleOf);
    assert.equal(text, "郎中一人，书令史35人，令史14人");
  });
  it("无编制时返回占位文本", () => {
    const { text, staff: s } = staffTextOf([], entityMap, titleOf);
    assert.equal(text, "编制未载");
    assert.equal(s.length, 0);
  });
});

describe("dedupeStaffEdges", () => {
  it("同一官职多条边时优先带员额的", () => {
    const edges = [
      { official: 10, staff_quota: null, staff_type: "官" },
      { official: 10, staff_quota: 1, staff_type: "官" },
    ];
    assert.equal(dedupeStaffEdges(edges, entityMap).length, 1);
    assert.equal(dedupeStaffEdges(edges, entityMap)[0].staff_quota, 1);
  });
  it("非官职端点不占槽", () => {
    const edges = [{ official: 2, staff_quota: 1, staff_type: "官" }];
    assert.equal(dedupeStaffEdges(edges, entityMap).length, 0);
  });
});

describe("buildCompositionModel", () => {
  const model = buildCompositionModel({
    focusId: 1, entityMap, childrenFor, staffFor, titleOf,
  });

  it("focus 自身有编制时生成 selfColumn", () => {
    assert.equal(model.selfColumn.id, 1);
    assert.equal(model.selfColumn.staffText, "主事六人");
  });

  it("无后代的直接下级进入 looseColumns", () => {
    assert.deepEqual(model.looseColumns.map((c) => c.id), [2]);
    assert.equal(model.looseColumns[0].staffText, "编制未载");
  });

  it("有下级的直接下级成为分节，按吏户礼兵刑工排序", () => {
    assert.deepEqual(model.sections.map((s) => s.id), [3, 4]);
    assert.deepEqual(model.sections[0].columns.map((c) => c.id), [5, 6]);
    assert.deepEqual(model.sections[1].columns.map((c) => c.id), [7]);
  });

  it("分节标题自带编制文本", () => {
    assert.equal(model.sections[0].staffText, "郎中一人，书令史35人，令史14人");
  });

  it("focus 不存在时返回 null", () => {
    assert.equal(buildCompositionModel({
      focusId: 99, entityMap, childrenFor, staffFor, titleOf,
    }), null);
  });
});
