import assert from "node:assert/strict";
import test from "node:test";
import { relationOriginalSections } from "./relation_detail_sections.js";

test("关系详情始终先显示关系来源词条，再显示端点词条和原文引文", () => {
  const sections = relationOriginalSections({
    relationshipLabel: "关系来源词条原文（2条）：",
    relationshipText: "关系来源",
    dictionaryText: "实体词条",
    quotation: "逐字引文",
    highlightTerms: ["关系证据"],
  });
  assert.deepEqual(sections.map((section) => section.label), [
    "关系来源词条原文（2条）：",
    "词条原文：",
    "原文引文：",
  ]);
  assert.deepEqual(sections[0].highlightTerms, ["关系证据"]);
});
