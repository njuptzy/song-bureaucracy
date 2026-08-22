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

test("all related verdicts highlight only exact excerpts inside the original quotation", () => {
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
    ["甲司改隶乙司"],
  );
  assert.deepEqual(
    evidenceReviewQuotationHighlights({ ...result, verdict: "contradicted" }, "某年，甲司改隶乙司。"),
    ["甲司改隶乙司"],
  );
  assert.deepEqual(
    evidenceReviewQuotationHighlights({ ...result, verdict: "irrelevant" }, "某年，甲司改隶乙司。"),
    [],
  );
});

test("evidence verdicts expose distinct severity and excerpt labels", () => {
  const insufficient = evidenceReviewSections({
    verdict: "not_supported", concise_quotations: ["只记甲司"], reason: "缺少改隶对象。",
  });
  assert.equal(insufficient[0].reviewTone, "amber");
  assert.equal(insufficient[1].label, "相关片段：");

  const contradicted = evidenceReviewSections({
    verdict: "contradicted", concise_quotations: ["仍隶甲司"], reason: "与改隶乙司冲突。",
  });
  assert.equal(contradicted[0].reviewTone, "red");
  assert.equal(contradicted[1].label, "冲突片段：");

  const irrelevant = evidenceReviewSections({
    verdict: "irrelevant", concise_quotations: [], reason: "没有相关内容。",
  });
  assert.equal(irrelevant[0].reviewTone, "critical");
  assert.equal(irrelevant.length, 2);
});

test("runtime error is neutral rather than red evidence verdict", () => {
  const sections = evidenceReviewSections({ status: "error" });
  assert.equal(sections[0].reviewTone, "neutral");
  assert.match(sections[1].value, /重试/);
});
