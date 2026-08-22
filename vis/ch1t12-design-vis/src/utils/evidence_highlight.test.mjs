import assert from "node:assert/strict";
import test from "node:test";

import {
  evidenceHighlightTerms,
  evidenceLineSegments,
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
