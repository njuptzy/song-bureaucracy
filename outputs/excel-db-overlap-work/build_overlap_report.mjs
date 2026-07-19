import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const sourcePath = "/Users/zhanyi/Desktop/work/song-bureaucracy/vis/resources/reference/尚书省下机构官职表总表.xlsx";
const dbPath = "/Users/zhanyi/Desktop/work/song-bureaucracy/vis/data/song_bureaucracy_best.db";
const dataPath = "/Users/zhanyi/Desktop/work/song-bureaucracy/vis/song-bureaucracy-visualization-v2/public/data/song-bureaucracy.json";
const outputDir = "/Users/zhanyi/Desktop/work/song-bureaucracy/outputs/excel-db-overlap";
const outputPath = `${outputDir}/尚书省Excel与数据库重叠核查.xlsx`;

const input = await FileBlob.load(sourcePath);
const sourceWb = await SpreadsheetFile.importXlsx(input);
const dataset = JSON.parse(await fs.readFile(dataPath, "utf8"));

const sheets = new Map(sourceWb.worksheets.items.map((sheet) => [sheet.name, sheet]));
const sheetValues = new Map();
function valuesOf(sheetName) {
  if (!sheetValues.has(sheetName)) {
    const sheet = sheets.get(sheetName);
    if (!sheet) throw new Error(`缺少工作表：${sheetName}`);
    sheetValues.set(sheetName, sheet.getUsedRange(true)?.values ?? []);
  }
  return sheetValues.get(sheetName);
}

function rowsOf(sheetName) {
  const values = valuesOf(sheetName);
  const headers = (values[0] ?? []).map((value) => String(value ?? "").trim());
  return values.slice(1).map((valuesRow, index) => {
    const row = {};
    headers.forEach((header, column) => {
      if (header && !(header in row)) row[header] = valuesRow[column];
    });
    return { sheet: sheetName, row: index + 2, rowData: row };
  });
}

function text(value) {
  return String(value ?? "").replace(/\u00a0/g, " ").trim();
}

function norm(value) {
  return text(value)
    .normalize("NFKC")
    .replace(/[\s　]+/g, "")
    .replace(/[·•]/g, "·")
    .replace(/[“”‘’《》〈〉「」『』]/g, "");
}

function shorten(value, max = 240) {
  const s = text(value).replace(/\s+/g, " ");
  return s.length <= max ? s : `${s.slice(0, max - 1)}…`;
}

function splitNames(value) {
  const s = text(value);
  if (!s) return [];
  return [...new Set(
    s.split(/[，、；;\n]+/)
      .map((item) => item.trim().replace(/^[①②③④⑤⑥⑦⑧⑨⑩\d.、）)]+/, "").replace(/[。；;]+$/, ""))
      .filter((item) => item && item.length <= 40 && !/[：:。！？!?]/.test(item))
  )];
}

function aliasCandidates(value) {
  const firstClause = text(value).split(/[。\n]/, 1)[0].replace(/^[①②③④⑤⑥⑦⑧⑨⑩]/, "");
  return splitNames(firstClause)
    .map((item) => item.replace(/^(又称|亦称|简称|别称|或称|即|一称)/, "").trim())
    .filter((item) => item.length >= 2 && item.length <= 12);
}

function levenshtein(a, b) {
  const prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i += 1) {
    let diagonal = prev[0];
    prev[0] = i;
    for (let j = 1; j <= b.length; j += 1) {
      const saved = prev[j];
      prev[j] = Math.min(prev[j] + 1, prev[j - 1] + 1, diagonal + (a[i - 1] === b[j - 1] ? 0 : 1));
      diagonal = saved;
    }
  }
  return prev[b.length];
}

const dbEntities = dataset.entities;
const dbById = new Map(dbEntities.map((entity) => [entity.id, entity]));
const dbByTitle = new Map(dbEntities.map((entity) => [text(entity.title), entity]));
const dbByNorm = new Map();
for (const entity of dbEntities) {
  const key = norm(entity.title);
  if (!dbByNorm.has(key)) dbByNorm.set(key, []);
  dbByNorm.get(key).push(entity);
}

const eventsByEntity = new Map();
for (const event of dataset.events) {
  if (!eventsByEntity.has(event.entityId)) eventsByEntity.set(event.entityId, []);
  eventsByEntity.get(event.entityId).push(event);
}

const relsByEntity = new Map();
const relsByPair = new Map();
for (const rel of dataset.relations) {
  for (const id of [rel.subjectEntityId, rel.objectEntityId]) {
    if (!relsByEntity.has(id)) relsByEntity.set(id, []);
    relsByEntity.get(id).push(rel);
  }
  const key = `${norm(rel.subjectTitle)}|${norm(rel.objectTitle)}`;
  if (!relsByPair.has(key)) relsByPair.set(key, []);
  relsByPair.get(key).push(rel);
}

function fuzzyCandidate(name, expectedType) {
  const n = norm(name);
  if (!n) return null;
  let best = null;
  for (const entity of dbEntities) {
    if (expectedType && entity.type !== expectedType) continue;
    const candidate = norm(entity.title);
    const distance = levenshtein(n, candidate);
    let score = 1 - distance / Math.max(n.length, candidate.length, 1);
    if ((n.includes(candidate) || candidate.includes(n)) && Math.min(n.length, candidate.length) >= 2) {
      score = Math.max(score, Math.min(n.length, candidate.length) / Math.max(n.length, candidate.length));
    }
    if (!best || score > best.score) best = { entity, score };
  }
  return best && best.score >= 0.55 ? best : null;
}

function matchEntity(record) {
  const exact = dbByTitle.get(record.name);
  if (exact) return { entity: exact, level: "名称完全相同", matchedBy: record.name };
  const normalized = dbByNorm.get(norm(record.name)) ?? [];
  if (normalized.length === 1) return { entity: normalized[0], level: "规范化后相同", matchedBy: record.name };
  return null;
}

function entityMetrics(entity) {
  const events = eventsByEntity.get(entity.id) ?? [];
  const years = events.flatMap((event) => [event.yearStart, event.yearEnd]).filter((year) => Number.isFinite(year));
  return {
    eventCount: events.length,
    relationCount: (relsByEntity.get(entity.id) ?? []).length,
    yearMin: years.length ? Math.min(...years) : null,
    yearMax: years.length ? Math.max(...years) : null,
    timeExamples: events.slice(0, 3).map((event) => event.rawTime).filter(Boolean).join("；"),
  };
}

const staticSpecs = [
  { sheet: "机构静态表", title: "机构名", alias: "简称与别名", expectedType: "机构" },
  { sheet: "官职静态表", title: "官职名", alias: "简称与别名", expectedType: "官职" },
];
const staticRecords = [];
for (const spec of staticSpecs) {
  for (const source of rowsOf(spec.sheet)) {
    const name = text(source.rowData[spec.title]);
    if (!name) continue;
    staticRecords.push({
      sourceSheet: spec.sheet,
      sourceRow: source.row,
      name,
      expectedType: spec.expectedType,
      excelCategory: text(source.rowData.类别) || spec.expectedType,
      aliasText: text(source.rowData[spec.alias]),
      aliases: aliasCandidates(source.rowData[spec.alias]),
      sourcePage: text(source.rowData.参考文档页数),
      sourceCitation: shorten(source.rowData.出处, 160),
    });
  }
}

const uniqueStatic = new Map();
for (const record of staticRecords) {
  const key = `${record.expectedType}|${norm(record.name)}`;
  if (!uniqueStatic.has(key)) uniqueStatic.set(key, record);
}

const entityOverlap = [];
const entityUnmatched = [];
for (const record of uniqueStatic.values()) {
  const match = matchEntity(record);
  if (match) {
    const metrics = entityMetrics(match.entity);
    entityOverlap.push({ ...record, ...match, ...metrics });
  } else {
    entityUnmatched.push({ ...record, fuzzy: fuzzyCandidate(record.name, record.expectedType) });
  }
}
entityOverlap.sort((a, b) => a.expectedType.localeCompare(b.expectedType, "zh") || a.name.localeCompare(b.name, "zh"));
entityUnmatched.sort((a, b) =>
  (b.fuzzy?.score ?? -1) - (a.fuzzy?.score ?? -1) ||
  a.expectedType.localeCompare(b.expectedType, "zh") ||
  a.name.localeCompare(b.name, "zh")
);

const dynamicSpecs = [
  { sheet: "机构动态表2", expectedType: "机构", current: "现机构", original: "原机构", year: "开始-公元年份", rawTime: "开始-时间" },
  { sheet: "官职动态表2", expectedType: "官职", current: "现官职", original: "原官职", year: "开始-公元年份", rawTime: "开始-时间" },
];
const timeChecks = [];
for (const spec of dynamicSpecs) {
  for (const source of rowsOf(spec.sheet)) {
    const name = text(source.rowData[spec.current]) || text(source.rowData[spec.original]);
    if (!name) continue;
    const match = matchEntity({ name, aliases: [] });
    if (!match) continue;
    const parsedYear = Number.parseInt(text(source.rowData[spec.year]).match(/\d{3,4}/)?.[0] ?? "", 10);
    const year = Number.isFinite(parsedYear) ? parsedYear : null;
    const events = eventsByEntity.get(match.entity.id) ?? [];
    const sameYear = year == null ? [] : events.filter((event) => event.yearStart != null && event.yearStart <= year && (event.yearEnd ?? event.yearStart) >= year);
    const nearest = sameYear.length ? sameYear : events
      .filter((event) => event.yearStart != null && year != null)
      .sort((a, b) => Math.abs(a.yearStart - year) - Math.abs(b.yearStart - year))
      .slice(0, 1);
    const evidence = nearest.slice(0, 3);
    timeChecks.push({
      sourceSheet: spec.sheet,
      sourceRow: source.row,
      expectedType: spec.expectedType,
      name,
      changeType: text(source.rowData.变更类型),
      excelYear: year,
      excelTime: text(source.rowData[spec.rawTime]),
      entity: match.entity,
      matchLevel: match.level,
      status: year == null ? "Excel无公元年" : sameYear.length ? "同年命中" : "实体命中、年份未命中",
      dbYears: evidence.map((event) => event.yearStart == null ? "未定年" : `${event.yearStart}${event.yearEnd && event.yearEnd !== event.yearStart ? `—${event.yearEnd}` : ""}`).join("；"),
      dbRawTime: evidence.map((event) => event.rawTime).filter(Boolean).join("；"),
      dbEvent: evidence.map((event) => shorten(event.event, 180)).filter(Boolean).join("；"),
      dbEventIds: evidence.map((event) => event.id).join("、"),
      dbCitation: evidence.flatMap((event) => event.citations ?? []).slice(0, 2).map((citation) => shorten(`${citation.citation || ""} ${citation.quotation || ""}`, 180)).join("；"),
    });
  }
}
timeChecks.sort((a, b) => (a.excelYear ?? 9999) - (b.excelYear ?? 9999) || a.name.localeCompare(b.name, "zh"));

const totalSheets = ["尚书省", "吏部", "户部", "礼部", "兵部", "刑部", "工部"];
const relationshipRules = [
  { field: "下级机构", direction: "down", expected: "上下级机构" },
  { field: "上级机构", direction: "up", expected: "上下级机构" },
  { field: "隶属机构", direction: "up", expected: "编制隶属" },
  { field: "下级官员", direction: "down", expected: "编制隶属" },
  { field: "前身", direction: "up", expected: "前后演变" },
];
const excelRelationMap = new Map();
for (const sheetName of totalSheets) {
  for (const source of rowsOf(sheetName)) {
    const current = text(source.rowData.条目名);
    if (!current) continue;
    for (const rule of relationshipRules) {
      for (const other of splitNames(source.rowData[rule.field])) {
        const subject = rule.direction === "down" ? current : other;
        const object = rule.direction === "down" ? other : current;
        const key = `${norm(subject)}|${norm(object)}|${rule.expected}`;
        if (!excelRelationMap.has(key)) {
          excelRelationMap.set(key, { subject, object, expected: rule.expected, sources: [] });
        }
        excelRelationMap.get(key).sources.push(`${sheetName}!${source.row}（${rule.field}）`);
      }
    }
  }
}

const relationOverlap = [];
const relationUnmatched = [];
for (const candidate of excelRelationMap.values()) {
  const subjectEntity = dbByNorm.get(norm(candidate.subject))?.[0] ?? null;
  const objectEntity = dbByNorm.get(norm(candidate.object))?.[0] ?? null;
  if (!subjectEntity || !objectEntity) continue;
  const dbRels = relsByPair.get(`${norm(subjectEntity.title)}|${norm(objectEntity.title)}`) ?? [];
  if (dbRels.length) {
    for (const rel of dbRels) {
      relationOverlap.push({ candidate, subjectEntity, objectEntity, rel, typeMatches: rel.type === candidate.expected });
    }
  } else {
    relationUnmatched.push({ candidate, subjectEntity, objectEntity });
  }
}
relationOverlap.sort((a, b) => a.candidate.subject.localeCompare(b.candidate.subject, "zh") || a.candidate.object.localeCompare(b.candidate.object, "zh"));
relationUnmatched.sort((a, b) => a.candidate.subject.localeCompare(b.candidate.subject, "zh") || a.candidate.object.localeCompare(b.candidate.object, "zh"));
console.log("STAGE analysis", JSON.stringify({ entityOverlap: entityOverlap.length, entityUnmatched: entityUnmatched.length, timeChecks: timeChecks.length, relationOverlap: relationOverlap.length, relationUnmatched: relationUnmatched.length }));

const wb = Workbook.create();

function writeSheet(name, headers, rows, tableName, widths, wrapColumns = []) {
  const sheet = wb.worksheets.add(name);
  sheet.showGridLines = false;
  const matrix = [headers, ...rows];
  sheet.getRangeByIndexes(0, 0, matrix.length, headers.length).values = matrix;
  const table = sheet.tables.add(`A1:${columnName(headers.length)}${matrix.length}`, true, tableName);
  table.style = "TableStyleMedium2";
  table.showBandedRows = true;
  sheet.freezePanes.freezeRows(1);
  sheet.getRange(`A1:${columnName(headers.length)}1`).format = {
    fill: "#6F3F2A",
    font: { bold: true, color: "#FFFFFF" },
    rowHeight: 28,
    verticalAlignment: "center",
  };
  headers.forEach((_, index) => {
    const column = columnName(index + 1);
    sheet.getRange(`${column}:${column}`).format.columnWidth = widths[index] ?? 14;
    if (wrapColumns.includes(index)) sheet.getRange(`${column}2:${column}${matrix.length}`).format.wrapText = true;
  });
  if (rows.length) sheet.getRange(`A2:${columnName(headers.length)}${matrix.length}`).format.verticalAlignment = "top";
  if (rows.length) sheet.getRange(`A2:${columnName(headers.length)}${matrix.length}`).format.rowHeight = 72;
  return sheet;
}

function columnName(index) {
  let value = index;
  let out = "";
  while (value > 0) {
    value -= 1;
    out = String.fromCharCode(65 + (value % 26)) + out;
    value = Math.floor(value / 26);
  }
  return out;
}

const overlapHeaders = ["Excel类型", "Excel名称", "Excel工作表", "Excel行号", "Excel别名", "匹配级别", "命中用名", "DB实体ID", "DB名称", "DB类型", "类型一致", "DB时间点数", "DB关系数", "最早年", "最晚年", "DB时间举例", "Excel参考页", "Excel出处", "核查结论", "核查备注"];
const overlapRows = entityOverlap.map((item) => [
  item.expectedType, item.name, item.sourceSheet, item.sourceRow, shorten(item.aliasText, 180), item.level, item.matchedBy,
  item.entity.id, item.entity.title, item.entity.type, item.expectedType === item.entity.type ? "是" : "否",
  item.eventCount, item.relationCount, item.yearMin, item.yearMax, item.timeExamples, item.sourcePage, item.sourceCitation, "待核查", "",
]);
const overlapSheet = writeSheet("实体重叠", overlapHeaders, overlapRows, "EntityOverlapTable", [10, 22, 14, 9, 28, 15, 20, 10, 22, 10, 10, 11, 10, 9, 9, 32, 12, 36, 12, 30], [4, 15, 17, 19]);
console.log("STAGE entity overlap sheet");
overlapSheet.getRange(`S2:S${overlapRows.length + 1}`).dataValidation = { rule: { type: "list", values: ["待核查", "确认一致", "存在问题"] } };
overlapSheet.getRange(`S2:S${overlapRows.length + 1}`).conditionalFormats.add("containsText", { text: "确认一致", format: { fill: "#DDEFE3", font: { color: "#2E6B45" } } });
overlapSheet.getRange(`S2:S${overlapRows.length + 1}`).conditionalFormats.add("containsText", { text: "存在问题", format: { fill: "#F6D9D5", font: { color: "#9A352D" } } });

const unmatchedHeaders = ["Excel类型", "Excel名称", "Excel工作表", "Excel行号", "Excel别名", "Excel参考页", "最相近DB名称", "候选DB ID", "候选DB类型", "相似度", "说明", "核查结论", "核查备注"];
const unmatchedRows = entityUnmatched.map((item) => [
  item.expectedType, item.name, item.sourceSheet, item.sourceRow, shorten(item.aliasText, 180), item.sourcePage,
  item.fuzzy?.entity.title ?? "", item.fuzzy?.entity.id ?? null, item.fuzzy?.entity.type ?? "", item.fuzzy ? Number(item.fuzzy.score.toFixed(3)) : null,
  item.fuzzy ? "仅为字符串近似候选，不计入重叠" : "未找到可靠候选", "待核查", "",
]);
const unmatchedSheet = writeSheet("实体待核查", unmatchedHeaders, unmatchedRows, "EntityReviewTable", [10, 22, 14, 9, 28, 12, 22, 10, 10, 10, 28, 12, 30], [4, 10, 12]);
console.log("STAGE entity review sheet");
unmatchedSheet.getRange(`J2:J${unmatchedRows.length + 1}`).format.numberFormat = "0.0%";
unmatchedSheet.getRange(`L2:L${unmatchedRows.length + 1}`).dataValidation = { rule: { type: "list", values: ["待核查", "确认未收录", "候选相同", "其他"] } };

const timeHeaders = ["Excel类型", "Excel名称", "Excel工作表", "Excel行号", "变更类型", "Excel公元年", "Excel时间原文", "DB实体ID", "DB名称", "实体匹配", "时间核查结果", "DB对应/最近年份", "DB时间原文", "DB事件ID", "DB事件", "DB引用证据", "核查结论", "核查备注"];
const timeRows = timeChecks.map((item) => [
  item.expectedType, item.name, item.sourceSheet, item.sourceRow, item.changeType, item.excelYear, item.excelTime,
  item.entity.id, item.entity.title, item.matchLevel, item.status, item.dbYears, item.dbRawTime, item.dbEventIds,
  item.dbEvent, item.dbCitation, "待核查", "",
]);
const timeSheet = writeSheet("时间核查", timeHeaders, timeRows, "TimeCheckTable", [10, 22, 14, 9, 14, 11, 26, 10, 22, 15, 22, 18, 28, 12, 38, 42, 12, 30], [6, 12, 14, 15, 17]);
console.log("STAGE time sheet");
timeSheet.getRange(`Q2:Q${timeRows.length + 1}`).dataValidation = { rule: { type: "list", values: ["待核查", "确认一致", "时间有差异", "其他"] } };
timeSheet.getRange(`K2:K${timeRows.length + 1}`).conditionalFormats.add("containsText", { text: "同年命中", format: { fill: "#DDEFE3", font: { color: "#2E6B45" } } });
timeSheet.getRange(`K2:K${timeRows.length + 1}`).conditionalFormats.add("containsText", { text: "年份未命中", format: { fill: "#F9E7C9", font: { color: "#8A5A12" } } });

const relHeaders = ["Excel上级/主体", "Excel下级/客体", "Excel预期关系", "Excel来源位置", "DB关系ID", "DB主体ID", "DB主体名称", "DB客体ID", "DB客体名称", "DB关系类型", "关系类型一致", "DB起年", "DB止年", "员额", "员额类型", "DB引用证据", "核查结论", "核查备注"];
const relRows = relationOverlap.map((item) => [
  item.candidate.subject, item.candidate.object, item.candidate.expected, item.candidate.sources.slice(0, 8).join("；"),
  item.rel.id, item.subjectEntity.id, item.subjectEntity.title, item.objectEntity.id, item.objectEntity.title,
  item.rel.type, item.typeMatches ? "是" : "否", item.rel.yearStart, item.rel.yearEnd, item.rel.staffQuota, item.rel.staffType,
  (item.rel.citations ?? []).slice(0, 2).map((citation) => shorten(`${citation.citation || ""} ${citation.quotation || ""}`, 200)).join("；"),
  "待核查", "",
]);
const relSheet = writeSheet("关系重叠", relHeaders, relRows, "RelationOverlapTable", [24, 24, 14, 34, 10, 10, 22, 10, 22, 14, 12, 9, 9, 9, 11, 44, 12, 30], [3, 15, 17]);
console.log("STAGE relation overlap sheet");
relSheet.getRange(`Q2:Q${relRows.length + 1}`).dataValidation = { rule: { type: "list", values: ["待核查", "确认一致", "关系有差异", "其他"] } };
relSheet.getRange(`K2:K${relRows.length + 1}`).conditionalFormats.add("containsText", { text: "否", format: { fill: "#F6D9D5", font: { color: "#9A352D" } } });

const relReviewHeaders = ["Excel上级/主体", "Excel下级/客体", "Excel预期关系", "Excel来源位置", "DB主体ID", "DB主体名称", "DB客体ID", "DB客体名称", "说明", "核查结论", "核查备注"];
const relReviewRows = relationUnmatched.map((item) => [
  item.candidate.subject, item.candidate.object, item.candidate.expected, item.candidate.sources.slice(0, 8).join("；"),
  item.subjectEntity.id, item.subjectEntity.title, item.objectEntity.id, item.objectEntity.title,
  "两端实体均在数据库中，但未找到同方向关系", "待核查", "",
]);
const relReviewSheet = writeSheet("关系待核查", relReviewHeaders, relReviewRows, "RelationReviewTable", [24, 24, 14, 34, 10, 22, 10, 22, 34, 12, 30], [3, 8, 10]);
console.log("STAGE relation review sheet");
relReviewSheet.getRange(`J2:J${relReviewRows.length + 1}`).dataValidation = { rule: { type: "list", values: ["待核查", "应补入数据库", "Excel关系不成立", "其他"] } };

const summary = wb.worksheets.add("核查说明");
summary.showGridLines = false;
summary.getRange("A1:J1").merge();
summary.getRange("A1").values = [["尚书省 Excel 与最优数据库重叠核查"]];
summary.getRange("A1:J1").format = { fill: "#5F3828", font: { bold: true, color: "#FFFFFF", size: 18 }, rowHeight: 36, horizontalAlignment: "center", verticalAlignment: "center" };
summary.getRange("A3:J3").values = [["实体重叠", null, "实体待核查", null, "时间同年命中", null, "关系重叠", null, "关系待核查", null]];
summary.getRange("A4").formulas = [["=COUNTA('实体重叠'!$A$2:$A$1000)"]];
summary.getRange("C4").formulas = [["=COUNTA('实体待核查'!$A$2:$A$1000)"]];
summary.getRange("E4").formulas = [["=COUNTIF('时间核查'!$K$2:$K$2000,\"同年命中\")"]];
summary.getRange("G4").formulas = [["=COUNTA('关系重叠'!$A$2:$A$3000)"]];
summary.getRange("I4").formulas = [["=COUNTA('关系待核查'!$A$2:$A$3000)"]];
for (const cell of ["A3:B4", "C3:D4", "E3:F4", "G3:H4", "I3:J4"]) {
  summary.getRange(cell).format = { fill: "#F1E7DD", borders: { preset: "outside", style: "thin", color: "#C8AE9C" } };
}
for (const cell of ["A4", "C4", "E4", "G4", "I4"]) summary.getRange(cell).format = { font: { bold: true, color: "#5F3828", size: 16 }, horizontalAlignment: "center" };
summary.getRange("A6:J6").merge();
summary.getRange("A6").values = [["核查口径"]];
summary.getRange("A6:J6").format = { fill: "#B97951", font: { bold: true, color: "#FFFFFF" }, rowHeight: 25 };
summary.getRange("A7:J14").values = [
  ["1", "实体范围", "以“机构静态表”和“官职静态表”为准，避免 30 张工作表中的拆分版、汇总版重复计数。", null, null, null, null, null, null, null],
  ["2", "实体重叠", "只有主名称完全相同，或仅空白/Unicode 规范化后相同，才计入重叠。", null, null, null, null, null, null, null],
  ["3", "别名与近似候选", "Excel 别名和字符串相似只列入“实体待核查”，不计入重叠，必须人工确认。", null, null, null, null, null, null, null],
  ["4", "时间核查", "以两张“动态表2”的开始公元年，与当前数据库导出的标准化年份比较；同年命中不代表事件语义完全一致。", null, null, null, null, null, null, null],
  ["5", "关系核查", "从尚书省及六部总表的下级机构、上级机构、隶属机构、下级官员、前身字段提取；两端名称必须都命中数据库。", null, null, null, null, null, null, null],
  ["6", "关系重叠", "数据库存在同方向主体—客体关系即列入；“关系类型一致”另列，防止方向相同但类型不同被误判为完全一致。", null, null, null, null, null, null, null],
  ["7", "源文件", sourcePath, null, null, null, null, null, null, null],
  ["8", "数据库", `${dbPath}（981 实体、1813 时间点、1177 关系、3126 引用）`, null, null, null, null, null, null, null],
];
summary.getRange("A7:A14").format = { horizontalAlignment: "center", font: { bold: true, color: "#8B573B" } };
summary.getRange("B7:B14").format = { font: { bold: true } };
summary.getRange("C7:J14").merge(true);
summary.getRange("C7:J14").format = { wrapText: true, verticalAlignment: "top" };
summary.getRange("A7:J14").format.borders = { preset: "inside", style: "thin", color: "#E2D4CA" };
summary.getRange("A16:J16").merge();
summary.getRange("A16").values = [["使用方法：先在“实体重叠”确认名称与类型，再看“时间核查”和“关系重叠”；黄色/红色提示项优先核查。核查结论列已设置下拉选项。"]];
summary.getRange("A16:J16").format = { fill: "#FFF3D6", font: { color: "#76521B" }, wrapText: true, rowHeight: 32 };
summary.getRange("A:J").format.columnWidth = 13;
summary.getRange("B:B").format.columnWidth = 16;
summary.getRange("C:J").format.columnWidth = 15;
summary.freezePanes.freezeRows(1);
console.log("STAGE summary sheet");

await fs.mkdir(outputDir, { recursive: true });
const previewDir = `${outputDir}/previews`;
await fs.mkdir(previewDir, { recursive: true });
const previewSpecs = [
  ["核查说明", "A1:J16"],
  ["实体重叠", "A1:T16"],
  ["实体待核查", "A1:M16"],
  ["时间核查", "A1:R14"],
  ["关系重叠", "A1:R14"],
  ["关系待核查", "A1:K14"],
];
for (const [sheetName, range] of previewSpecs) {
  console.log(`STAGE render ${sheetName}`);
  const preview = await wb.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(`${previewDir}/${sheetName}.png`, new Uint8Array(await preview.arrayBuffer()));
}

const keyInspect = await wb.inspect({
  kind: "table",
  sheetId: "实体重叠",
  range: "A1:T8",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 20,
  maxChars: 12000,
});
console.log("STAGE key inspect");
console.log(keyInspect.ndjson);
const candidateInspect = await wb.inspect({
  kind: "table",
  sheetId: "实体待核查",
  range: "A1:M16",
  include: "values,formulas",
  tableMaxRows: 16,
  tableMaxCols: 13,
  maxChars: 12000,
});
console.log("STAGE candidate inspect");
console.log(candidateInspect.ndjson);

const errorScan = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
console.log("STAGE error scan");
const output = await SpreadsheetFile.exportXlsx(wb);
console.log("STAGE export");
await output.save(outputPath);

console.log(JSON.stringify({
  outputPath,
  sourceSheets: sourceWb.worksheets.items.length,
  staticUnique: uniqueStatic.size,
  entityOverlap: entityOverlap.length,
  entityUnmatched: entityUnmatched.length,
  timeChecks: timeChecks.length,
  timeSameYear: timeChecks.filter((item) => item.status === "同年命中").length,
  relationOverlap: relationOverlap.length,
  relationTypeMatches: relationOverlap.filter((item) => item.typeMatches).length,
  relationUnmatched: relationUnmatched.length,
  errorScan: errorScan.ndjson,
}, null, 2));
