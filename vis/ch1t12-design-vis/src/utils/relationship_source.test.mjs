import assert from "node:assert/strict";
import test from "node:test";
import { relationshipSourceOriginal } from "./relationship_source.js";

test("关系来源显示 BuildRecords 匹配到的完整词条原文", () => {
  const result = relationshipSourceOriginal({
    relationshipSources: {
      11: [{
        sourceEntry: "同中书门下平章事",
        sourcePage: "85",
        entries: [{
          id: 7,
          title: "同中书门下平章事",
          page: 85,
          text: "宋前期宰相名。",
          originalText: "宋前期宰相名。\n职源与沿革：这是未截断的完整词条原文。",
        }],
      }],
    },
  }, ["R11", "T9"]);
  assert.equal(result.status, "matched");
  assert.match(result.text, /同中书门下平章事/);
  assert.match(result.text, /这是未截断的完整词条原文/);
});

test("关系来源未加载时不用 quotation 冒充", () => {
  const result = relationshipSourceOriginal({}, ["R11"]);
  assert.equal(result.status, "loading");
  assert.match(result.text, /正在读取/);
});

test("汇总来源无法匹配词条时明确说明", () => {
  const result = relationshipSourceOriginal({
    relationshipSources: {
      12: [{ sourceEntry: "第二编关系汇总", sourcePage: "88-92", entries: [] }],
    },
  }, ["R12"]);
  assert.equal(result.status, "unmatched");
  assert.match(result.text, /第二编关系汇总/);
  assert.match(result.text, /未匹配/);
});
