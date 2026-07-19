import fs from "node:fs/promises";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const repoRoot = "/Users/zhanyi/Desktop/work/song-bureaucracy";
const dbPath = path.join(repoRoot, "vis/data/song_bureaucracy_visualization.db");
const outputDir = path.join(repoRoot, "outputs/019f7828-9431-7303-a263-365f1cc9a3a3");
const outputPath = path.join(outputDir, "宋代官制时间处理结果_2026-07-19.xlsx");
const previewDir = path.join(outputDir, "spreadsheet-work/previews-v2");

function query(sql) {
  const text = execFileSync("/usr/bin/sqlite3", ["-json", dbPath, sql], {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  }).trim();
  return text ? JSON.parse(text) : [];
}

const rows = query(`
  SELECT
    t.id AS timepoint_id, t.entity_id, e.title AS entity_title, e.type AS entity_type,
    COALESCE(t.time, '') AS raw_time, COALESCE(t.event, '') AS event,
    n.year_start, n.year_end, n.month, n.is_leap_month, n.day,
    n.end_month, n.end_is_leap_month, n.end_day,
    COALESCE(n.month_text, '') AS month_text,
    COALESCE(n.day_text, '') AS day_text,
    COALESCE(n.end_month_text, '') AS end_month_text,
    COALESCE(n.end_day_text, '') AS end_day_text,
    n.sort_order, COALESCE(n.time_type, 'missing') AS time_type,
    COALESCE(n.parse_note, '') AS parse_note,
    CASE
      WHEN n.timepoint_id IS NULL THEN '缺少标准化记录'
      WHEN n.raw_time <> COALESCE(t.time, '') THEN '标准化记录已过期'
      ELSE '已同步'
    END AS sync_status
  FROM Timepoints t
  JOIN Entities e ON e.id = t.entity_id
  LEFT JOIN NormalizedTimes n ON n.timepoint_id = t.id
  ORDER BY t.id
`);

const metadata = query("SELECT key, value FROM TimeNormalizationMetadata ORDER BY key");
const metadataMap = new Map(metadata.map((item) => [item.key, item.value]));

const typeLabels = {
  exact: "精确时间",
  range: "时间范围",
  undated: "无明确纪年",
  pre_song: "宋前时间",
  unresolved: "无法解析",
  missing: "缺少记录",
};

function conversionText(item) {
  if (item.time_type === "exact" && item.year_start != null) {
    let value = `公元${item.year_start}年`;
    if (item.month != null) value += `农历${item.is_leap_month ? "闰" : ""}${item.month}月`;
    if (item.day != null) value += `${item.day}日`;
    return value;
  }
  if (item.time_type === "range" && item.year_start != null) {
    return item.year_end != null && item.year_end !== item.year_start
      ? `公元${item.year_start}—${item.year_end}年`
      : `公元${item.year_start}年（范围记载）`;
  }
  if (item.time_type === "undated") return "无明确公元纪年，保留原文";
  if (item.time_type === "pre_song") return "宋前时间，保留原文";
  if (item.time_type === "unresolved") return "无法可靠换算，需人工核查";
  return "缺少标准化结果";
}

const groups = new Map();
for (const row of rows) {
  let group = groups.get(row.raw_time);
  if (!group) {
    group = {
      rawTime: row.raw_time,
      rows: [],
      entityIds: new Set(),
      entityTitles: new Set(),
      signatures: new Set(),
    };
    groups.set(row.raw_time, group);
  }
  group.rows.push(row);
  group.entityIds.add(row.entity_id);
  group.entityTitles.add(row.entity_title);
  group.signatures.add(JSON.stringify([
    row.year_start, row.year_end, row.month, row.is_leap_month, row.day,
    row.end_month, row.end_is_leap_month, row.end_day, row.sort_order,
    row.time_type, row.parse_note,
  ]));
}

const summaries = [...groups.values()].map((group) => {
  const first = group.rows[0];
  const titles = [...group.entityTitles];
  return {
    ...first,
    rawTime: group.rawTime,
    occurrences: group.rows.length,
    entityCount: group.entityIds.size,
    conversion: group.signatures.size === 1 ? conversionText(first) : "存在多种转换结果，需核查",
    entityExamples: titles.slice(0, 8).join("、") + (titles.length > 8 ? `等${titles.length}个实体` : ""),
    timepointIds: group.rows.map((item) => item.timepoint_id).join("、"),
    consistency: group.signatures.size === 1 ? "一致" : `不一致（${group.signatures.size}种）`,
  };
}).sort((a, b) => {
  const aSort = a.sort_order == null ? Number.MAX_SAFE_INTEGER : a.sort_order;
  const bSort = b.sort_order == null ? Number.MAX_SAFE_INTEGER : b.sort_order;
  return aSort - bSort || a.time_type.localeCompare(b.time_type) || a.rawTime.localeCompare(b.rawTime, "zh-CN");
});

const reviewRows = rows.filter((item) =>
  item.time_type === "unresolved" || item.sync_status !== "已同步"
);

const workbook = Workbook.create();
const summary = workbook.worksheets.add("全部时间汇总");
const detail = workbook.worksheets.add("全部时间点明细");
const review = workbook.worksheets.add("无法解析");
const rules = workbook.worksheets.add("处理规则");

const colors = {
  brown: "#6E472B", brownDark: "#4E311F", parchment: "#F4EFE5",
  teal: "#6F9690", tealLight: "#DDEAE7", rust: "#B56F46",
  rustLight: "#F4E3D7", line: "#D8C9B5", white: "#FFFFFF",
};
for (const sheet of [summary, detail, review, rules]) sheet.showGridLines = false;

function styleTableSheet(sheet, headerRange, dataRange) {
  sheet.getRange(headerRange).format = {
    fill: colors.brown,
    font: { bold: true, color: colors.white, name: "Microsoft YaHei" },
    wrapText: true,
    verticalAlignment: "center",
    rowHeight: 34,
  };
  sheet.getRange(dataRange).format.font.name = "Microsoft YaHei";
  sheet.getRange(dataRange).format.verticalAlignment = "center";
  sheet.freezePanes.freezeRows(1);
}

// 第一张表：731 种原始时间文本的全部转换汇总。
const summaryHeaders = [
  "原始时间", "出现次数", "涉及实体数", "时间类型", "转换结果",
  "起始年", "结束年", "起始月", "起始闰月", "起始日",
  "结束月", "结束闰月", "结束日", "排序值", "解析备注",
  "实体示例", "对应时间点ID", "结果一致性",
];
const summaryValues = summaries.map((item) => [
  item.rawTime, item.occurrences, item.entityCount, typeLabels[item.time_type] || item.time_type,
  item.conversion, item.year_start ?? null, item.year_end ?? null, item.month ?? null,
  item.is_leap_month ? "是" : "否", item.day ?? null, item.end_month ?? null,
  item.end_is_leap_month ? "是" : "否", item.end_day ?? null, item.sort_order ?? null,
  item.parse_note, item.entityExamples, item.timepointIds, item.consistency,
]);
summary.getRangeByIndexes(0, 0, 1, summaryHeaders.length).values = [summaryHeaders];
summary.getRangeByIndexes(1, 0, summaryValues.length, summaryHeaders.length).values = summaryValues;
const summaryTable = summary.tables.add(
  summary.getRangeByIndexes(0, 0, summaryValues.length + 1, summaryHeaders.length),
  true,
  "AllTimeSummaryTable",
);
summaryTable.style = "TableStyleMedium2";
summaryTable.showBandedRows = true;
styleTableSheet(summary, "A1:R1", `A2:R${summaryValues.length + 1}`);
summary.freezePanes.freezeColumns(1);
summary.getRange(`B2:C${summaryValues.length + 1}`).format.numberFormat = "#,##0";
summary.getRange(`F2:N${summaryValues.length + 1}`).format.numberFormat = "0";
summary.getRange(`A2:A${summaryValues.length + 1}`).format.wrapText = true;
summary.getRange(`E2:E${summaryValues.length + 1}`).format.wrapText = true;
summary.getRange(`O2:R${summaryValues.length + 1}`).format.wrapText = true;
summary.getRange(`D2:D${summaryValues.length + 1}`).conditionalFormats.add("containsText", {
  text: "无法解析", format: { fill: colors.rustLight, font: { color: colors.rust, bold: true } },
});
summary.getRange("A:A").format.columnWidth = 30;
summary.getRange("B:C").format.columnWidth = 12;
summary.getRange("D:D").format.columnWidth = 16;
summary.getRange("E:E").format.columnWidth = 30;
summary.getRange("F:N").format.columnWidth = 11;
summary.getRange("O:O").format.columnWidth = 36;
summary.getRange("P:P").format.columnWidth = 48;
summary.getRange("Q:Q").format.columnWidth = 44;
summary.getRange("R:R").format.columnWidth = 16;

// 第二张表：数据库全部 1813 个时间点，一条不省略。
const detailHeaders = [
  "时间点ID", "实体ID", "实体名称", "实体类型", "原始时间", "时间类型", "转换结果",
  "起始年", "结束年", "起始月", "起始闰月", "起始日", "结束月", "结束闰月", "结束日",
  "起始月原文", "起始日原文", "结束月原文", "结束日原文", "排序值",
  "同步状态", "解析备注", "事件描述",
];
const detailValues = rows.map((item) => [
  item.timepoint_id, item.entity_id, item.entity_title, item.entity_type, item.raw_time,
  typeLabels[item.time_type] || item.time_type, conversionText(item),
  item.year_start ?? null, item.year_end ?? null, item.month ?? null,
  item.is_leap_month ? "是" : "否", item.day ?? null, item.end_month ?? null,
  item.end_is_leap_month ? "是" : "否", item.end_day ?? null,
  item.month_text, item.day_text, item.end_month_text, item.end_day_text,
  item.sort_order ?? null, item.sync_status, item.parse_note, item.event,
]);
detail.getRangeByIndexes(0, 0, 1, detailHeaders.length).values = [detailHeaders];
detail.getRangeByIndexes(1, 0, detailValues.length, detailHeaders.length).values = detailValues;
const detailTable = detail.tables.add(
  detail.getRangeByIndexes(0, 0, detailValues.length + 1, detailHeaders.length),
  true,
  "AllTimepointDetailsTable",
);
detailTable.style = "TableStyleMedium2";
detailTable.showBandedRows = true;
styleTableSheet(detail, "A1:W1", `A2:W${detailValues.length + 1}`);
detail.freezePanes.freezeColumns(2);
detail.getRange(`A2:B${detailValues.length + 1}`).format.numberFormat = "0";
detail.getRange(`H2:T${detailValues.length + 1}`).format.numberFormat = "0";
detail.getRange(`C2:G${detailValues.length + 1}`).format.wrapText = true;
detail.getRange(`V2:W${detailValues.length + 1}`).format.wrapText = true;
detail.getRange(`U2:U${detailValues.length + 1}`).conditionalFormats.add("notContainsText", {
  text: "已同步", format: { fill: colors.rustLight, font: { color: colors.rust, bold: true } },
});
detail.getRange("A:B").format.columnWidth = 11;
detail.getRange("C:C").format.columnWidth = 24;
detail.getRange("D:D").format.columnWidth = 10;
detail.getRange("E:E").format.columnWidth = 30;
detail.getRange("F:F").format.columnWidth = 16;
detail.getRange("G:G").format.columnWidth = 30;
detail.getRange("H:T").format.columnWidth = 11;
detail.getRange("U:U").format.columnWidth = 16;
detail.getRange("V:V").format.columnWidth = 36;
detail.getRange("W:W").format.columnWidth = 52;

// 第三张表：真正需要人工判断的记录。
const reviewHeaders = ["时间点ID", "实体ID", "实体名称", "实体类型", "原始时间", "当前处理结果", "解析备注", "事件描述"];
const reviewValues = reviewRows.map((item) => [
  item.timepoint_id, item.entity_id, item.entity_title, item.entity_type,
  item.raw_time, conversionText(item), item.parse_note, item.event,
]);
review.getRangeByIndexes(0, 0, 1, reviewHeaders.length).values = [reviewHeaders];
review.getRangeByIndexes(1, 0, reviewValues.length, reviewHeaders.length).values = reviewValues;
const reviewTable = review.tables.add(
  review.getRangeByIndexes(0, 0, reviewValues.length + 1, reviewHeaders.length),
  true,
  "UnresolvedTimesTable",
);
reviewTable.style = "TableStyleMedium3";
styleTableSheet(review, "A1:H1", `A2:H${reviewValues.length + 1}`);
review.getRange(`A2:H${reviewValues.length + 1}`).format.wrapText = true;
review.getRange("A:B").format.columnWidth = 11;
review.getRange("C:C").format.columnWidth = 24;
review.getRange("D:D").format.columnWidth = 10;
review.getRange("E:F").format.columnWidth = 32;
review.getRange("G:G").format.columnWidth = 40;
review.getRange("H:H").format.columnWidth = 52;

// 第四张表：说明汇总依据和字段边界。
rules.mergeCells("A1:D2");
rules.getRange("A1").values = [["当前时间处理规则与来源"]];
rules.getRange("A1:D2").format = {
  fill: colors.brownDark,
  font: { bold: true, color: colors.white, size: 18, name: "Microsoft YaHei" },
  verticalAlignment: "center",
};
rules.getRange("A4:B4").values = [["项目", "当前内容"]];
const generatedAt = `UTC ${String(metadataMap.get("generated_at_utc") || "").replace("T", " ").replace("+00:00", "")}`.trim();
const ruleValues = [
  ["汇总覆盖", `${summaries.length} 种原始时间文本；${rows.length} 个数据库时间点`],
  ["同步状态", `${rows.filter((item) => item.sync_status === "已同步").length} / ${rows.length} 已同步`],
  ["处理规则", metadataMap.get("rule_summary") || ""],
  ["标准化版本", metadataMap.get("normalization_version") || ""],
  ["生成时间", generatedAt],
  ["源数据库", metadataMap.get("source_database") || ""],
  ["年号表参考", metadataMap.get("reference_year_era_table") || ""],
  ["历法参考", metadataMap.get("reference_calendar") || ""],
  ["历法使用边界", metadataMap.get("calendar_reference_usage") || ""],
];
rules.getRangeByIndexes(4, 0, ruleValues.length, 2).values = ruleValues;
rules.getRange("A4:B4").format = { fill: colors.teal, font: { bold: true, color: colors.white, name: "Microsoft YaHei" } };
rules.getRange(`A5:B${ruleValues.length + 4}`).format = {
  font: { name: "Microsoft YaHei" }, wrapText: true, verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: colors.line },
};
rules.getRange(`A5:A${ruleValues.length + 4}`).format = {
  fill: colors.parchment, font: { bold: true, color: colors.brown, name: "Microsoft YaHei" },
};
rules.getRange("A:A").format.columnWidth = 22;
rules.getRange("B:B").format.columnWidth = 92;
rules.getRange(`5:${ruleValues.length + 4}`).format.rowHeight = 42;
rules.freezePanes.freezeRows(2);

await fs.mkdir(previewDir, { recursive: true });
const renderSpecs = [
  ["全部时间汇总", "A1:R18", "all-summary.png", 0.78],
  ["全部时间点明细", "A1:W15", "all-details.png", 0.72],
  ["无法解析", `A1:H${reviewValues.length + 1}`, "unresolved.png", 1.1],
  ["处理规则", `A1:D${ruleValues.length + 4}`, "rules.png", 1.05],
];
for (const [sheetName, range, fileName, scale] of renderSpecs) {
  const image = await workbook.render({ sheetName, range, scale, format: "png" });
  await fs.writeFile(path.join(previewDir, fileName), new Uint8Array(await image.arrayBuffer()));
}

const inspectSummary = await workbook.inspect({
  kind: "table", range: "全部时间汇总!A1:R10", include: "values,formulas",
  tableMaxRows: 10, tableMaxCols: 18,
});
console.log("SUMMARY_CHECK");
console.log(inspectSummary.ndjson);
const errorCheck = await workbook.inspect({
  kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan",
});
console.log("ERROR_CHECK");
console.log(errorCheck.ndjson);

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`OUTPUT=${outputPath}`);
console.log(`SUMMARY_ROWS=${summaries.length};DETAIL_ROWS=${rows.length};REVIEW_ROWS=${reviewRows.length}`);
