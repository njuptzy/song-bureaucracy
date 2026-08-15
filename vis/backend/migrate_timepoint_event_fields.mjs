#!/usr/bin/env node

import { DatabaseSync } from "node:sqlite";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

import {
  classifyEntityLifecycle,
  classifyEventType,
} from "../shared/entity_lifecycle.js";

const EVENT_TYPES = [
  "establish", "restore", "abolish", "rename", "reorganize", "merge", "split",
  "incorporate", "duty_transfer", "affiliation_change", "staffing_change",
  "record",
];
const LIFECYCLE_EFFECTS = ["activate", "preserve", "deactivate", "ignore"];

function option(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : "";
}

function requiredPath(name) {
  const value = option(name);
  if (!value) throw new Error(`缺少 ${name}`);
  const path = resolve(value);
  if (!existsSync(path)) throw new Error(`${name} 不存在：${path}`);
  return path;
}

function quoteIdentifier(value) {
  if (!/^[A-Za-z0-9_]+$/.test(value)) throw new Error(`非法表名：${value}`);
  return `"${value}"`;
}

function aliasCandidates(value) {
  const text = String(value || "").trim();
  if (!text) return [];
  const lead = text.split(/[。《（(]/, 1)[0];
  return lead
    .replace(/^(?:简称|又称|亦称|别称)[：:]?/, "")
    .split(/[、，,；;或]/)
    .map((item) => item.trim())
    .filter((item) => item && item.length <= 12 && !/[“”"：:]/.test(item));
}

function dictionaryAliases(databasePath, table) {
  if (!databasePath || !existsSync(databasePath)) return new Map();
  const dictionary = new DatabaseSync(databasePath, { readOnly: true });
  const aliases = new Map();
  try {
    const rows = dictionary.prepare(`SELECT title, fields FROM ${quoteIdentifier(table)}`).all();
    for (const row of rows) {
      let fields = {};
      try {
        fields = JSON.parse(row.fields || "{}");
      } catch {
        fields = {};
      }
      const values = [fields["简称与别名"], fields["简称"], fields["别称"]]
        .flatMap(aliasCandidates);
      aliases.set(row.title, [...new Set(values)]);
    }
  } finally {
    dictionary.close();
  }
  return aliases;
}

const entriesPath = requiredPath("--entries-db");
const dictionaryPath = option("--dict-db") ? requiredPath("--dict-db") : "";
const dictionaryTable = option("--dict-table") || "chapter1t12";
const aliasesByTitle = dictionaryAliases(dictionaryPath, dictionaryTable);
const entries = new DatabaseSync(entriesPath);

try {
  entries.exec("PRAGMA foreign_keys = ON");
  const columns = new Set(entries.prepare("PRAGMA table_info(Timepoints)").all().map((row) => row.name));
  entries.exec("BEGIN IMMEDIATE");
  if (!columns.has("event_type")) {
    entries.exec(`ALTER TABLE Timepoints ADD COLUMN event_type TEXT NOT NULL DEFAULT 'record' CHECK(event_type IN (${EVENT_TYPES.map((value) => `'${value}'`).join(",")}))`);
  }
  if (!columns.has("lifecycle_effect")) {
    entries.exec(`ALTER TABLE Timepoints ADD COLUMN lifecycle_effect TEXT NOT NULL DEFAULT 'preserve' CHECK(lifecycle_effect IN (${LIFECYCLE_EFFECTS.map((value) => `'${value}'`).join(",")}))`);
  }

  const update = entries.prepare(
    "UPDATE Timepoints SET event_type=?, lifecycle_effect=? WHERE id=?",
  );
  const counts = { eventType: {}, lifecycleEffect: {} };
  const rows = entries.prepare(`
    SELECT t.id, t.event, e.title
    FROM Timepoints t JOIN Entities e ON e.id=t.entity_id
    ORDER BY t.id
  `).all();
  for (const row of rows) {
    const entity = { title: row.title, aliases: aliasesByTitle.get(row.title) || [] };
    const eventType = classifyEventType(row.event);
    const lifecycleEffect = classifyEntityLifecycle(row.event, entity).effect;
    update.run(eventType, lifecycleEffect, row.id);
    counts.eventType[eventType] = (counts.eventType[eventType] || 0) + 1;
    counts.lifecycleEffect[lifecycleEffect] = (counts.lifecycleEffect[lifecycleEffect] || 0) + 1;
  }
  entries.exec("COMMIT");
  console.log(JSON.stringify({ rows: rows.length, ...counts }, null, 2));
} catch (error) {
  try {
    entries.exec("ROLLBACK");
  } catch {
    // The transaction may not have started.
  }
  throw error;
} finally {
  entries.close();
}
