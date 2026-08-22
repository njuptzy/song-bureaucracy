import assert from "node:assert/strict";
import test from "node:test";

import { timepointContextSections } from "./evolution_detail_metadata.js";

test("明确时间点和空关系不重复占用详情空间", () => {
  assert.deepEqual(timepointContextSections({
    timeType: "exact",
    timeTypeLabel: "明确时间点",
    entryComparisonText: "-47年",
    relatedRelationshipLabels: [],
  }), [
    { label: "距入口年份：", value: "-47年" },
  ]);
});

test("模糊时间和真实相关关系仍保留", () => {
  assert.deepEqual(timepointContextSections({
    timeType: "range",
    timeTypeLabel: "时间范围",
    parseNote: "止年未定",
    entryComparisonText: "+6年",
    relatedRelationshipLabels: ["秘书省 → 史馆", "秘书省 → 史馆"],
  }), [
    { label: "时间精度：", value: "时间范围；止年未定" },
    { label: "距入口年份：", value: "+6年" },
    { label: "相关关系：", value: "秘书省 → 史馆" },
  ]);
});
