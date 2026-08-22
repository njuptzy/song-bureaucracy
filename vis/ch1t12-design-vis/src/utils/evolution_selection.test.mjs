import assert from "node:assert/strict";
import test from "node:test";

import {
  compositeEvolutionSelectionFocus,
  compositeEventDetailHeader,
  compositeEventSelection,
  evolutionDetailSelection,
  evolutionComparisonAfterAdd,
  evolutionSelectionAnchors,
  evolutionSelectionFocus,
  timelineSelectionForEvolutionItem,
} from "./evolution_selection.js";

test("综合演变主线和信息带选择都建立互斥聚焦", () => {
  assert.deepEqual(
    compositeEvolutionSelectionFocus({ kind: "timepoint", id: 12 }, null),
    { active: true, mainTimepointId: 12, bandEventId: null },
  );
  assert.deepEqual(
    compositeEvolutionSelectionFocus(null, { id: "staff:8" }),
    { active: true, mainTimepointId: null, bandEventId: "staff:8" },
  );
  assert.deepEqual(
    compositeEvolutionSelectionFocus(null, null),
    { active: false, mainTimepointId: null, bandEventId: null },
  );
});

test("结构演变详情以关系为标题并显示标准化精确纪年", () => {
  assert.deepEqual(compositeEventDetailHeader({
    band: "institution",
    displayTitle: "国子监 → 国子学",
    subject: { title: "国子监" },
    yearStart: 989,
    yearEnd: 989,
    month: 2,
    eventTime: "北宋端拱二年二月",
  }), {
    title: "国子监 → 国子学",
    year: "公元989年2月（北宋端拱二年二月）",
  });
});

test("机构主线选择优先于残留的信息带选择", () => {
  const main = { kind: "timepoint", id: 11, item: { id: 11 } };
  const composite = { id: "R5919" };
  assert.deepEqual(evolutionDetailSelection(main, composite), {
    selectedEvolutionItem: main,
    compositeSelectedEvent: null,
  });
  assert.deepEqual(evolutionDetailSelection(null, composite), {
    selectedEvolutionItem: null,
    compositeSelectedEvent: composite,
  });
});

test("综合演变事件选择向外传递关系证据键和主体", () => {
  const event = {
    id: "R5919",
    subject: { entityId: 2001, title: "秘书监" },
    evidenceKeys: ["R5919"],
  };
  assert.deepEqual(compositeEventSelection(event), {
    kind: "composite-event",
    id: "R5919",
    entityId: 2001,
    item: event,
  });
  assert.equal(compositeEventSelection(null), null);
});

test("添加对象会保留当前实体并直接进入对比模式", () => {
  assert.deepEqual(evolutionComparisonAfterAdd([174], 201), {
    mode: "compare",
    entityIds: [174, 201],
    activeEntityId: 201,
  });
});

test("对比对象去重并始终限制为四个", () => {
  assert.deepEqual(evolutionComparisonAfterAdd([1, 2, 2, 3, 4], 5), {
    mode: "compare",
    entityIds: [1, 2, 3, 5],
    activeEntityId: 5,
  });
});

test("时间点选择联动到单年快照", () => {
  assert.deepEqual(
    timelineSelectionForEvolutionItem("timepoint", 1080, [960, 1279]),
    { active: true, range: [1080, 1080] },
  );
});

test("前后演变关系不把两个端点误作连续时间范围", () => {
  assert.deepEqual(
    timelineSelectionForEvolutionItem("relation", 1115, [960, 1279]),
    { active: false, range: [960, 1279] },
  );
});

test("关系端点分别连接真实年份，同年端点只保留一条定位线", () => {
  assert.deepEqual(evolutionSelectionAnchors({
    kind: "relation",
    item: {
      sourcePoints: [
        { effectiveYear: 1115, baseX: 300, y: 420 },
        { effectiveYear: 1115, baseX: 300, y: 510 },
      ],
      targetPoints: [{ effectiveYear: 1121, baseX: 340, y: 620 }],
    },
  }), [
    { year: 1115, x: 300, y: 510 },
    { year: 1121, x: 340, y: 620 },
  ]);
});

test("时间点使用真实年份锚点而不是避让后的显示位置", () => {
  assert.deepEqual(evolutionSelectionAnchors({
    kind: "timepoint",
    item: {
      effectiveYear: 1080,
      baseX: 260,
      baseY: 400,
      displayX: 272,
      y: 412,
    },
  }), [{ year: 1080, x: 260, y: 400 }]);
});

test("点击关系时只保留该关系的真实端点作为聚焦上下文", () => {
  assert.deepEqual(evolutionSelectionFocus({
    kind: "relation",
    id: 7,
    item: {
      sourcePoints: [{ timepointId: 11 }, { timepointId: 11 }],
      targetPoints: [{ timepointId: 21 }],
    },
  }), {
    active: true,
    relationId: 7,
    timepointIds: [11, 21],
  });
});

test("点击时间点时聚焦范围只包含该点", () => {
  assert.deepEqual(evolutionSelectionFocus({
    kind: "timepoint",
    id: 31,
    item: { id: 31 },
  }), {
    active: true,
    relationId: null,
    timepointIds: [31],
  });
});

test("派生的层级变化事件使用字符串 ID 时仍保持自身高亮", () => {
  assert.deepEqual(evolutionSelectionFocus({
    kind: "timepoint",
    id: "hierarchy:reparent:3:1050:1:2:subject",
    item: { id: "hierarchy:reparent:3:1050:1:2:subject" },
  }), {
    active: true,
    relationId: null,
    timepointIds: ["hierarchy:reparent:3:1050:1:2:subject"],
  });
});
