import test from "node:test";
import assert from "node:assert/strict";

import {
  evidenceReviewKey,
  evidenceReviewQuotationHighlights,
  evidenceReviewSections,
} from "./evidence_review.js";

test("review key separates citation rows on one timepoint", () => {
  assert.notEqual(evidenceReviewKey(2, 3), evidenceReviewKey(2, 4));
});

test("supported result keeps each verbatim excerpt separate", () => {
  const sections = evidenceReviewSections({
    verdict: "supported",
    concise_quotations: ["甲", "乙"],
    reason: "两段共同支持。",
  });
  assert.deepEqual(sections.map((item) => item.label), [
    "核验结论：", "支持片段：", "支持片段：", "判断理由：",
  ]);
  assert.equal(sections[0].reviewTone, "green");
  assert.equal(sections[1].reviewTone, "green");
});

test("supported result highlights only exact excerpts inside the original quotation", () => {
  const result = {
    verdict: "supported",
    concise_quotations: ["甲司改隶乙司", "不在原文", "甲司改隶乙司"],
  };
  assert.deepEqual(
    evidenceReviewQuotationHighlights(result, "某年，甲司改隶乙司。"),
    ["甲司改隶乙司"],
  );
  assert.deepEqual(
    evidenceReviewQuotationHighlights({ ...result, verdict: "not_supported" }, "某年，甲司改隶乙司。"),
    [],
  );
});

test("runtime error is neutral rather than red evidence verdict", () => {
  const sections = evidenceReviewSections({ status: "error" });
  assert.equal(sections[0].reviewTone, "neutral");
  assert.match(sections[1].value, /重试/);
});
