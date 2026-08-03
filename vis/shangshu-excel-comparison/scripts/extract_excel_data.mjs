import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const repoRoot = new URL("../../../", import.meta.url);
const sourcePath = new URL("../../副本尚书省下机构官职表总表.xlsx", import.meta.url);
const outputPath = new URL("../excel_data.json", import.meta.url);

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(fileURLToPath(sourcePath)));

function rowsFromSheet(name) {
  const sheet = workbook.worksheets.getItem(name);
  const values = sheet.getUsedRange(true).values;
  const headers = values[0].map((value) => String(value ?? "").trim());
  return values.slice(1).filter((row) => row.some((value) => value !== null && value !== "")).map((row, index) => {
    const item = { __row: index + 2 };
    headers.forEach((header, column) => {
      item[header] = row[column] ?? null;
    });
    return item;
  });
}

const payload = {
  source: {
    file: "副本尚书省下机构官职表总表.xlsx",
    generatedAt: new Date().toISOString(),
    note: "由工作簿标准化静态表与动态表提取；原工作簿未被修改。",
  },
  institutions: rowsFromSheet("机构静态表"),
  offices: rowsFromSheet("官职静态表"),
  institutionChanges: rowsFromSheet("机构动态表2"),
  officeChanges: rowsFromSheet("官职动态表2"),
  changeTypes: rowsFromSheet("变更类型"),
};

await fs.writeFile(fileURLToPath(outputPath), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
console.log(JSON.stringify({
  repoRoot: fileURLToPath(repoRoot),
  output: fileURLToPath(outputPath),
  institutions: payload.institutions.length,
  offices: payload.offices.length,
  institutionChanges: payload.institutionChanges.length,
  officeChanges: payload.officeChanges.length,
}));
