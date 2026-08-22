import assert from "node:assert/strict";
import test from "node:test";

import {
  evidenceHighlightTerms,
  evidenceLineSegments,
  preciseTimepointEvidenceTerms,
} from "./evidence_highlight.js";

test("关系逐字引文去重并优先匹配较长证据", () => {
  assert.deepEqual(evidenceHighlightTerms(["改隶太府寺", "改隶", "改隶太府寺"]), [
    "改隶太府寺",
    "改隶",
  ]);
});

test("原文只高亮关系证据片段且保留前后文本", () => {
  assert.deepEqual(
    evidenceLineSegments("先隶提举司，后改隶太府寺。", ["改隶太府寺"]),
    [
      { text: "先隶提举司，后", highlighted: false },
      { text: "改隶太府寺", highlighted: true },
      { text: "。", highlighted: false },
    ],
  );
});

test("时间点长引文只提取纪年和事件的最小重合片段", () => {
  assert.deepEqual(
    preciseTimepointEvidenceTerms({
      quotations: [
        "前代已有旧制。至南宋建炎元年五月，于秘书省复建史馆，绍兴十年又罢。",
        "宋沿置，元丰五年始振其职，建炎三年罢。",
      ],
      eventText: "于省内复建史馆",
      rawTime: "南宋建炎元年五月",
      entityTitle: "秘书省",
    }),
    ["南宋建炎元年五月", "复建史馆"],
  );
});

test("纪年前缀不一致时仍匹配原文中的实际纪年写法", () => {
  assert.deepEqual(
    preciseTimepointEvidenceTerms({
      quotations: ["元丰五年五月行新官制，尚书省始振其职。"],
      eventText: "行新官制",
      rawTime: "北宋元丰五年五月",
      entityTitle: "尚书省",
    }),
    ["元丰五年五月", "行新官制"],
  );
});

test("只有实体名相同而事件不相符时不作宽泛高亮", () => {
  assert.deepEqual(
    preciseTimepointEvidenceTerms({
      quotations: ["秘书省掌图籍之事。"],
      eventText: "秘书省另置属官",
      rawTime: "绍兴元年",
      entityTitle: "秘书省",
    }),
    [],
  );
});

test("同一朝代年号但年份不同不能误作纪年证据", () => {
  assert.deepEqual(
    preciseTimepointEvidenceTerms({
      quotations: ["南宋建炎三年四月罢秘书省。"],
      eventText: "复建史馆",
      rawTime: "南宋建炎元年五月",
      entityTitle: "秘书省",
    }),
    [],
  );
});
