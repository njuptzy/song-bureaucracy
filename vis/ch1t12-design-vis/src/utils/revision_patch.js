function idKey(value) {
  return String(value);
}

function normalizedTime(row = {}) {
  const keys = [
    "raw_time", "year_start", "year_end", "month", "is_leap_month", "day",
    "end_month", "end_is_leap_month", "end_day", "month_text", "day_text",
    "end_month_text", "end_day_text", "sort_order", "time_type", "parse_note",
  ];
  const normalized = Object.fromEntries(keys.map((key) => [key, row[key] ?? null]));
  normalized.raw_time = row.raw_time ?? row.time ?? null;
  return normalized;
}

function timepointIndex(data) {
  const index = new Map();
  for (const bucketName of ["timepoints", "preSongTimepoints"]) {
    for (const [entityId, rows] of Object.entries(data?.[bucketName] || {})) {
      for (const row of rows || []) index.set(idKey(row.id), { row, entityId, bucketName });
    }
  }
  return index;
}

function relationPayload(row, points, revisionStatus = "") {
  const sourceEntry = points.get(idKey(row.subject_id));
  const targetEntry = points.get(idKey(row.object_id));
  const sourcePoint = sourceEntry?.row;
  const targetPoint = targetEntry?.row;
  return {
    ...row,
    source: sourcePoint?.entity_id ?? sourcePoint?.entityId
      ?? (sourceEntry?.entityId != null ? Number(sourceEntry.entityId) : null),
    target: targetPoint?.entity_id ?? targetPoint?.entityId
      ?? (targetEntry?.entityId != null ? Number(targetEntry.entityId) : null),
    source_timepoint_id: row.subject_id,
    target_timepoint_id: row.object_id,
    source_time: normalizedTime(sourcePoint),
    target_time: normalizedTime(targetPoint),
    display_relation_type: row.relation_type === "前后演变"
      ? "前后演变（未分类）"
      : row.relation_subtype || row.relation_type,
    classification_status: row.relation_type === "前后演变" ? "unclassified" : "classified",
    evidence_key: `R${row.id}`,
    _revision_status: revisionStatus || row._revision_status || "",
  };
}

function isEvolutionRelation(row = {}) {
  return row.relation_type === "前后演变" || String(row.relation_type || "").startsWith("演变·");
}

function relationPeriod(row, points) {
  const sourcePoint = points.get(idKey(row.subject_id))?.row;
  const targetPoint = points.get(idKey(row.object_id))?.row;
  const start = sourcePoint?.year_start ?? targetPoint?.year_start ?? null;
  const end = targetPoint?.year_end ?? targetPoint?.year_start
    ?? sourcePoint?.year_end ?? sourcePoint?.year_start ?? null;
  if (start == null || end == null) return [];
  return [{
    start: Math.min(Number(start), Number(end)),
    end: Math.max(Number(start), Number(end)),
    time_type: sourcePoint?.time_type || targetPoint?.time_type || "",
  }];
}

function staffEdge(row, points, revisionStatus = "") {
  const sourceEntry = points.get(idKey(row.subject_id));
  const targetEntry = points.get(idKey(row.object_id));
  const sourcePoint = sourceEntry?.row;
  const targetPoint = targetEntry?.row;
  return {
    id: row.id,
    org: sourcePoint?.entity_id ?? sourcePoint?.entityId
      ?? (sourceEntry?.entityId != null ? Number(sourceEntry.entityId) : null),
    official: targetPoint?.entity_id ?? targetPoint?.entityId
      ?? (targetEntry?.entityId != null ? Number(targetEntry.entityId) : null),
    staff_quota: row.staff_quota ?? "",
    staff_type: row.staff_type ?? "",
    quotation: row.quotation || "",
    periods: relationPeriod(row, points),
    states: [{
      id: row.id,
      subject_timepoint_id: row.subject_id,
      object_timepoint_id: row.object_id,
    }],
    _revision_status: revisionStatus || row._revision_status || "",
    _revision_original_id: row._revision_original_id,
  };
}

function evolutionEdge(row, points, revisionStatus = "") {
  const sourceEntry = points.get(idKey(row.subject_id));
  const targetEntry = points.get(idKey(row.object_id));
  const sourcePoint = sourceEntry?.row;
  const targetPoint = targetEntry?.row;
  return {
    id: row.id,
    source: sourcePoint?.entity_id ?? sourcePoint?.entityId
      ?? (sourceEntry?.entityId != null ? Number(sourceEntry.entityId) : row.source ?? null),
    target: targetPoint?.entity_id ?? targetPoint?.entityId
      ?? (targetEntry?.entityId != null ? Number(targetEntry.entityId) : row.target ?? null),
    periods: relationPeriod(row, points).length ? relationPeriod(row, points) : row.periods || [],
    states: [{
      id: row.id,
      subject_timepoint_id: row.subject_id,
      object_timepoint_id: row.object_id,
    }],
    _revision_status: revisionStatus || row._revision_status || "",
  };
}

function manualDifferenceMap(differences, table) {
  return new Map(
    (differences || [])
      .filter((item) => item.target_table === table && !item.automatic)
      .map((item) => [idKey(item.target_id), item]),
  );
}

function removeRowFromBuckets(buckets, rowId) {
  const key = idKey(rowId);
  for (const bucketName of ["timepoints", "preSongTimepoints"]) {
    for (const [entityId, rows] of Object.entries(buckets[bucketName])) {
      if (!(rows || []).some((row) => idKey(row.id) === key)) continue;
      buckets[bucketName][entityId] = rows.filter((row) => idKey(row.id) !== key);
    }
  }
}

function putTimepoint(buckets, row) {
  const entityId = idKey(row.entity_id ?? row.entityId);
  const bucketName = row.time_type === "pre_song" ? "preSongTimepoints" : "timepoints";
  const current = buckets[bucketName][entityId] || [];
  buckets[bucketName][entityId] = [...current, row];
}

function applyTimepointPatch(data, preview) {
  const patch = preview?.patch?.timepoints || { upsert: [], delete: [] };
  const buckets = {
    timepoints: { ...(data.timepoints || {}) },
    preSongTimepoints: { ...(data.preSongTimepoints || {}) },
  };
  const original = timepointIndex(data);
  const manual = manualDifferenceMap(preview?.differences, "Timepoints");

  for (const rowId of patch.delete || []) removeRowFromBuckets(buckets, rowId);
  for (const row of patch.upsert || []) {
    removeRowFromBuckets(buckets, row.id);
    const difference = manual.get(idKey(row.id));
    const status = difference?.action === "insert" ? "added"
      : difference?.action === "update" ? "modified" : "";
    putTimepoint(buckets, { ...row, _revision_status: status });
  }

  for (const difference of preview?.differences || []) {
    if (difference.target_table !== "Timepoints" || !difference.before) continue;
    if (difference.action === "delete") {
      putTimepoint(buckets, {
        ...difference.before,
        id: `deleted:${difference.target_id}`,
        _revision_original_id: difference.target_id,
        _revision_status: "deleted",
      });
    } else if (difference.action === "update" && !difference.automatic) {
      const before = difference.before;
      const after = difference.after || {};
      if (before.time !== after.time) {
        putTimepoint(buckets, {
          ...before,
          ...(original.get(idKey(difference.target_id))?.row || {}),
          id: `before:${difference.target_id}`,
          prev_id: null,
          succ_id: null,
          _revision_original_id: difference.target_id,
          _revision_status: "before",
        });
      }
    }
  }
  return buckets;
}

function applyRelationPatch(data, preview, points) {
  const patch = preview?.patch?.relationships || { upsert: [], delete: [] };
  const deleted = new Set((patch.delete || []).map(idKey));
  const upserts = new Map((patch.upsert || []).map((row) => [idKey(row.id), row]));
  const manual = manualDifferenceMap(preview?.differences, "Relationships");
  const changeRelations = (data.changeRelations || [])
    .filter((row) => !deleted.has(idKey(row.id)) && !upserts.has(idKey(row.id)))
    .map((row) => relationPayload({
      ...row,
      subject_id: row.subject_id ?? row.source_timepoint_id,
      object_id: row.object_id ?? row.target_timepoint_id,
    }, points, row._revision_status || ""));
  const evolutionEdges = (data.evolutionEdges || [])
    .filter((row) => !deleted.has(idKey(row.id)) && !upserts.has(idKey(row.id)))
    .map((row) => {
      const state = row.states?.[0] || {};
      return evolutionEdge({
        ...row,
        subject_id: state.subject_timepoint_id ?? row.subject_id,
        object_id: state.object_timepoint_id ?? row.object_id,
      }, points, row._revision_status || "");
    });
  const staffEdges = (data.staffEdges || [])
    .filter((row) => {
      const relationIds = new Set([
        row.id,
        ...(row.states || []).map((state) => state.id),
      ].map(idKey));
      return ![...relationIds].some((id) => deleted.has(id) || upserts.has(id));
    })
    .map((row) => {
      const periods = (row.states || []).flatMap((state) => relationPeriod({
        subject_id: state.subject_timepoint_id,
        object_id: state.object_timepoint_id,
      }, points));
      return {
        ...row,
        periods: periods.filter((period, index) => periods.findIndex((candidate) => (
          candidate.start === period.start && candidate.end === period.end
          && candidate.time_type === period.time_type
        )) === index),
      };
    });

  for (const row of upserts.values()) {
    const difference = manual.get(idKey(row.id));
    const status = difference?.action === "insert" ? "added"
      : difference?.action === "update" ? "modified" : "";
    if (isEvolutionRelation(row)) {
      changeRelations.push(relationPayload(row, points, status));
      evolutionEdges.push(evolutionEdge(row, points, status));
    } else if (row.relation_type === "编制隶属") {
      staffEdges.push(staffEdge(row, points, status));
    }
  }
  for (const difference of preview?.differences || []) {
    if (difference.target_table !== "Relationships" || !difference.before) continue;
    if (!difference.automatic && difference.action === "update") {
      const before = {
        ...difference.before,
        id: `before:${difference.target_id}`,
        _revision_original_id: difference.target_id,
      };
      if (isEvolutionRelation(before)) {
        changeRelations.push(relationPayload(before, points, "before"));
        evolutionEdges.push(evolutionEdge(before, points, "before"));
      } else if (before.relation_type === "编制隶属") {
        staffEdges.push(staffEdge(before, points, "before"));
      }
    } else if (difference.action === "delete") {
      const before = {
        ...difference.before,
        id: `deleted:${difference.target_id}`,
        _revision_original_id: difference.target_id,
      };
      if (isEvolutionRelation(before)) {
        changeRelations.push(relationPayload(before, points, "deleted"));
        evolutionEdges.push(evolutionEdge(before, points, "deleted"));
      } else if (before.relation_type === "编制隶属") {
        staffEdges.push(staffEdge(before, points, "deleted"));
      }
    }
  }
  return { changeRelations, evolutionEdges, staffEdges };
}

function citationKey(row) {
  return `${row.target_table === "Timepoints" ? "T" : "R"}${row.target_id}`;
}

function applyCitationPatch(data, preview) {
  const patch = preview?.patch?.citations || { upsert: [], delete: [] };
  const result = { ...(data.citations || {}) };
  const deleted = new Set((patch.delete || []).map(idKey));
  for (const [key, rows] of Object.entries(result)) {
    if ((rows || []).some((row) => deleted.has(idKey(row.id)))) {
      result[key] = rows.filter((row) => !deleted.has(idKey(row.id)));
    }
  }
  for (const row of patch.upsert || []) {
    for (const [key, rows] of Object.entries(result)) {
      if ((rows || []).some((item) => idKey(item.id) === idKey(row.id))) {
        result[key] = rows.filter((item) => idKey(item.id) !== idKey(row.id));
      }
    }
    const key = citationKey(row);
    result[key] = [...(result[key] || []), { ...row }];
  }
  return result;
}

/** Apply only the server-provided revision delta; untouched data keeps identity. */
export function applyRevisionPreview(data, preview) {
  if (!data || !preview?.patch) return data;
  const buckets = applyTimepointPatch(data, preview);
  const withTimepoints = { ...data, ...buckets };
  const points = timepointIndex(withTimepoints);
  return {
    ...withTimepoints,
    ...applyRelationPatch(data, preview, points),
    citations: applyCitationPatch(data, preview),
    revisionPreview: {
      differences: preview.differences || [],
      affectedEntityIds: preview.affected_entity_ids || [],
      affectedYears: preview.affected_years || [],
    },
  };
}
