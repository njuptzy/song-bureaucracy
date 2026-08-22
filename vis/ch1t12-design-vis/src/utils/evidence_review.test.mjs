import test from "node:test";
import assert from "node:assert/strict";

import {
  evidenceReviewKey,
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
    "核验结论：", "精简原文：", "精简原文：", "判断理由：",
  ]);
  assert.equal(sections[0].reviewTone, "green");
});

test("runtime error is neutral rather than red evidence verdict", () => {
  const sections = evidenceReviewSections({ status: "error" });
  assert.equal(sections[0].reviewTone, "neutral");
  assert.match(sections[1].value, /重试/);
});
