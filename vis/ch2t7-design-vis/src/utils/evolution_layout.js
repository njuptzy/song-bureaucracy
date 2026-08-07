const DEFAULT_BOUNDS = { x: 560, y: 190, width: 1228, height: 630 };
const RELATION_LABEL_HEIGHT = 18;
const RELATION_LABEL_ASCENT = 14;
const RELATION_LABEL_LAYER_GAP = 22;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function finite(value, fallback) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function normalizeBounds(bounds = {}) {
  const x = finite(bounds.x ?? bounds.left, DEFAULT_BOUNDS.x);
  const y = finite(bounds.y ?? bounds.top, DEFAULT_BOUNDS.y);
  const width = Math.max(1, finite(
    bounds.width,
    bounds.right != null ? finite(bounds.right, x + DEFAULT_BOUNDS.width) - x : DEFAULT_BOUNDS.width,
  ));
  const height = Math.max(1, finite(
    bounds.height,
    bounds.bottom != null ? finite(bounds.bottom, y + DEFAULT_BOUNDS.height) - y : DEFAULT_BOUNDS.height,
  ));
  return { x, y, width, height, right: x + width, bottom: y + height };
}

function displayableOffAxis(model) {
  const offAxis = model?.offAxis || {};
  return (offAxis.undated?.length || 0)
    + (offAxis.unresolved?.length || 0)
    + (offAxis.relationEndpoints || []).filter((member) => (
      !["pre_song"].includes(member.timeType)
    )).length;
}

function uniqueBy(items, keyOf) {
  return [...new Map((items || []).map((item) => [keyOf(item), item])).values()];
}

function pointKey(member) {
  return [
    member.role,
    member.entityId,
    member.timepointId ?? "",
    member.timeType ?? "",
    member.yearStart ?? "",
    member.yearEnd ?? "",
  ].join(":");
}

function relationLabelWidth(label) {
  const units = [...String(label || "")].reduce((total, character) => (
    total + (/^[\x00-\xff]$/.test(character) ? 0.58 : 1)
  ), 0);
  return Math.max(42, units * 12 + 10);
}

function relationAnchor(relation) {
  const sources = relation.sourcePoints.filter((point) => point.x != null);
  const targets = relation.targetPoints.filter((point) => point.x != null);
  if (!sources.length || !targets.length) return null;
  const center = (points, field) => (
    points.reduce((total, point) => total + point[field], 0) / points.length
  );
  return {
    x: (center(sources, "x") + center(targets, "x")) / 2,
    y: (center(sources, "y") + center(targets, "y")) / 2,
  };
}

function relationGroupAnchor(group) {
  const points = [...group.sourcePoints, ...group.targetPoints]
    .filter((point) => point.x != null);
  if (!points.length) return null;
  return {
    x: Number.isFinite(group.junctionX)
      ? group.junctionX
      : points.reduce((total, point) => total + point.x, 0) / points.length,
    y: points.reduce((total, point) => total + point.y, 0) / points.length,
  };
}

function relationStableKey(relation) {
  const memberKey = (members) => members.map((member) => [
    member.role,
    member.entityId,
    member.timepointId ?? "",
    member.timeType ?? "",
    member.effectiveYear ?? "",
    member.rawTime ?? "",
  ].join(":")).sort().join(",");
  return [
    relation.evidenceKey ?? "",
    relation.relationType ?? "",
    relation.label ?? "",
    relation.quotation ?? "",
    memberKey(relation.sourcePoints),
    memberKey(relation.targetPoints),
  ].join("|");
}

function relationGroupStableKey(group) {
  return [
    group.groupId ?? "",
    group.relationType ?? "",
    group.label ?? "",
    ...group.relations.map(relationStableKey).sort(),
  ].join("|");
}

function labelBox(labelX, labelY, width) {
  const x = labelX - width / 2;
  const y = labelY - RELATION_LABEL_ASCENT;
  return {
    x,
    y,
    width,
    height: RELATION_LABEL_HEIGHT,
    right: x + width,
    bottom: y + RELATION_LABEL_HEIGHT,
  };
}

function overlapArea(first, second, gapX = 8, gapY = 4) {
  const overlapWidth = Math.min(first.right + gapX, second.right)
    - Math.max(first.x - gapX, second.x);
  const overlapHeight = Math.min(first.bottom + gapY, second.bottom)
    - Math.max(first.y - gapY, second.y);
  return Math.max(0, overlapWidth) * Math.max(0, overlapHeight);
}

function steppedCandidates(preferred, minimum, maximum, step, count) {
  const result = [];
  const seen = new Set();
  const add = (value) => {
    const candidate = clamp(value, minimum, maximum);
    const key = candidate.toFixed(6);
    if (seen.has(key)) return;
    seen.add(key);
    result.push(candidate);
  };
  add(preferred);
  for (let level = 1; level <= count; level += 1) {
    add(preferred - level * step);
    add(preferred + level * step);
  }
  add(minimum);
  add(maximum);
  return result;
}

function leaderToBox(anchor, box) {
  let x2 = clamp(anchor.x, box.x, box.right);
  let y2 = clamp(anchor.y, box.y, box.bottom);
  if (x2 === anchor.x && y2 === anchor.y) {
    const distances = [
      { distance: Math.abs(anchor.y - box.y), x: anchor.x, y: box.y },
      { distance: Math.abs(anchor.y - box.bottom), x: anchor.x, y: box.bottom },
      { distance: Math.abs(anchor.x - box.x), x: box.x, y: anchor.y },
      { distance: Math.abs(anchor.x - box.right), x: box.right, y: anchor.y },
    ].sort((first, second) => first.distance - second.distance);
    x2 = distances[0].x;
    y2 = distances[0].y;
  }
  return { x1: anchor.x, y1: anchor.y, x2, y2 };
}

function layoutEvolutionLabels(labelItems, bounds, plotBounds) {
  const placementRight = bounds.right;
  const preferredLeft = clamp(plotBounds.x, bounds.x, placementRight);
  const placementLeft = placementRight - preferredLeft >= 1 ? preferredLeft : bounds.x;
  const placementWidth = Math.max(1, placementRight - placementLeft);
  const minimumY = bounds.y + RELATION_LABEL_ASCENT;
  const maximumY = Math.max(minimumY, bounds.bottom - (
    RELATION_LABEL_HEIGHT - RELATION_LABEL_ASCENT
  ));
  const prepared = labelItems
    .filter((item) => item.anchor)
    .sort((first, second) => first.priority - second.priority
      || first.anchor.x - second.anchor.x
      || first.anchor.y - second.anchor.y
      || String(first.id).localeCompare(String(second.id), "zh", { numeric: true })
      || first.stableKey.localeCompare(
        second.stableKey,
        "zh",
        { numeric: true },
      )
      || first.key.localeCompare(second.key, "zh", { numeric: true }));
  const placements = new Map();
  const occupied = [];

  for (const item of prepared) {
    const { anchor } = item;
    const width = relationLabelWidth(item.label);
    if (bounds.height < RELATION_LABEL_HEIGHT || width > placementWidth) {
      placements.set(item.key, {
        labelX: null,
        labelY: null,
        labelBounds: null,
        labelAnchorX: anchor.x,
        labelAnchorY: anchor.y,
        leader: null,
        labelVisible: false,
        labelOverflow: true,
      });
      continue;
    }
    const halfWidth = width / 2;
    const minimumX = placementLeft + halfWidth;
    const maximumX = Math.max(minimumX, placementRight - halfWidth);
    const preferredX = clamp(anchor.x, minimumX, maximumX);
    const preferredY = clamp(anchor.y - 10, minimumY, maximumY);
    const verticalCount = Math.max(2, Math.ceil(bounds.height / RELATION_LABEL_LAYER_GAP));
    const yCandidates = steppedCandidates(
      preferredY,
      minimumY,
      maximumY,
      RELATION_LABEL_LAYER_GAP,
      verticalCount,
    );
    const horizontalStep = Math.max(28, width * 0.7);
    const horizontalCount = Math.max(1, Math.ceil(placementWidth / horizontalStep));
    const xCandidates = steppedCandidates(
      preferredX,
      minimumX,
      maximumX,
      horizontalStep,
      horizontalCount,
    );
    const candidates = [];
    for (const labelY of yCandidates) {
      candidates.push({ labelX: preferredX, labelY });
    }
    for (const labelX of xCandidates.slice(1)) {
      for (const labelY of yCandidates) candidates.push({ labelX, labelY });
    }

    let best = null;
    for (const candidate of candidates) {
      const box = labelBox(candidate.labelX, candidate.labelY, width);
      const overlap = occupied.reduce((total, item) => total + overlapArea(box, item), 0);
      const distance = Math.abs(candidate.labelY - preferredY)
        + Math.abs(candidate.labelX - preferredX) * 0.35;
      const score = overlap * 1000 + distance;
      if (!best || score < best.score) best = { ...candidate, box, score, overlap };
      if (overlap === 0) break;
    }
    const visible = best.overlap === 0;
    const placement = {
      labelX: visible ? best.labelX : null,
      labelY: visible ? best.labelY : null,
      labelBounds: visible ? best.box : null,
      labelAnchorX: anchor.x,
      labelAnchorY: anchor.y,
      leader: visible ? leaderToBox(anchor, best.box) : null,
      labelVisible: visible,
      labelOverflow: !visible,
    };
    placements.set(item.key, placement);
    if (visible) occupied.push(best.box);
  }
  return placements;
}

/**
 * Lay out the rendering-neutral evolution model in SVG user-space coordinates.
 * `baseX` is always the exact time coordinate; `displayX` only adds collision
 * avoidance and therefore must never be read back as a historical date.
 */
export function layoutEvolutionModel(model, requestedBounds = DEFAULT_BOUNDS) {
  const bounds = normalizeBounds(requestedBounds);
  const lanesSource = model?.lanes || [];
  const laneCount = lanesSource.length;
  const hasOffAxis = displayableOffAxis(model) > 0;
  const outerGap = Math.min(clamp(bounds.width * 0.012, 4, 16), bounds.width * 0.06);
  const labelWidth = Math.min(
    clamp(bounds.width * 0.095, 56, 126),
    bounds.width * 0.28,
  );
  const offAxisWidth = hasOffAxis
    ? Math.min(clamp(bounds.width * 0.135, 80, 166), bounds.width * 0.24)
    : 0;
  const labelBounds = {
    x: bounds.x,
    y: bounds.y,
    width: labelWidth,
    height: bounds.height,
  };
  const offAxisBounds = hasOffAxis ? {
    x: bounds.right - offAxisWidth,
    y: bounds.y,
    width: offAxisWidth,
    height: bounds.height,
    right: bounds.right,
    bottom: bounds.bottom,
  } : null;
  const plotLeft = clamp(bounds.x + labelWidth + outerGap, bounds.x, bounds.right);
  const desiredPlotRight = bounds.right - (hasOffAxis ? offAxisWidth + outerGap : outerGap);
  const plotRight = clamp(Math.max(plotLeft, desiredPlotRight), plotLeft, bounds.right);
  const plotBounds = {
    x: plotLeft,
    y: bounds.y,
    width: plotRight - plotLeft,
    height: bounds.height,
    right: plotRight,
    bottom: bounds.bottom,
  };
  const yearMin = finite(model?.yearMin, 960);
  const yearMax = Math.max(yearMin, finite(model?.yearMax, 1279));
  const yearSpan = Math.max(1, yearMax - yearMin);
  const yearToX = (year) => plotLeft
    + (clamp(finite(year, yearMin), yearMin, yearMax) - yearMin) / yearSpan
      * (plotRight - plotLeft);

  const verticalPadding = Math.min(34, bounds.height * 0.075);
  const laneTop = bounds.y + verticalPadding;
  const laneBottom = bounds.bottom - verticalPadding;
  const lanePitch = laneCount > 1 ? (laneBottom - laneTop) / (laneCount - 1) : 0;
  const laneY = (index) => laneCount === 1
    ? bounds.y + bounds.height / 2
    : laneTop + index * lanePitch;
  const laneByEntity = new Map();
  const eventByTimepoint = new Map();

  const lanes = lanesSource.map((lane, index) => {
    const y = clamp(laneY(index), bounds.y, bounds.bottom);
    const sameYear = new Map();
    for (const event of lane.events || []) {
      const key = event.effectiveYear;
      if (!sameYear.has(key)) sameYear.set(key, []);
      sameYear.get(key).push(event);
    }
    const laidOutEvents = [];
    for (const [year, events] of sameYear) {
      const ordered = [...events].sort((a, b) => (
        (a.chainIndex ?? 0) - (b.chainIndex ?? 0)
        || (a.eventIndex ?? 0) - (b.eventIndex ?? 0)
        || String(a.id).localeCompare(String(b.id), "zh", { numeric: true })
      ));
      const baseX = yearToX(year);
      const availableSpacing = ordered.length > 1
        ? (plotRight - plotLeft) / Math.max(ordered.length + 1, 2)
        : 0;
      const spacing = Math.min(
        ordered.some((event) => event.expanded) ? 24 : 10,
        availableSpacing,
      );
      let offsets = ordered.map((_, itemIndex) => (
        (itemIndex - (ordered.length - 1) / 2) * spacing
      ));
      const minimumX = baseX + Math.min(...offsets, 0);
      const maximumX = baseX + Math.max(...offsets, 0);
      const shift = minimumX < plotLeft
        ? plotLeft - minimumX
        : maximumX > plotRight
          ? plotRight - maximumX
          : 0;
      offsets = offsets.map((offset) => offset + shift);
      ordered.forEach((event, itemIndex) => {
        const offsetX = offsets[itemIndex];
        const laidOut = {
          ...event,
          baseX,
          displayX: clamp(baseX + offsetX, plotLeft, plotRight),
          offsetX,
          y,
        };
        laidOutEvents.push(laidOut);
        eventByTimepoint.set(event.id, laidOut);
      });
    }
    laidOutEvents.sort((a, b) => a.baseX - b.baseX
      || a.displayX - b.displayX
      || (a.chainIndex ?? 0) - (b.chainIndex ?? 0));
    const laidOut = {
      ...lane,
      index,
      y,
      labelX: bounds.x,
      labelY: y,
      labelMaxWidth: Math.max(1, labelWidth - outerGap),
      trackStartX: plotLeft,
      trackEndX: plotRight,
      segments: (lane.segments || []).map((segment) => ({
        ...segment,
        startX: yearToX(segment.startYear),
        endX: yearToX(segment.endYear),
        y,
      })),
      events: laidOutEvents,
    };
    laneByEntity.set(lane.entityId, laidOut);
    return laidOut;
  });

  const offAxisColumnX = (bucket) => {
    if (!offAxisBounds) return null;
    if (bucket === "unresolved") return offAxisBounds.x + offAxisBounds.width * 0.73;
    return offAxisBounds.x + offAxisBounds.width * 0.27;
  };
  const offAxisEventMap = new Map();
  const layoutOffAxisEvents = (items, bucket) => {
    const groupedByEntity = new Map();
    for (const item of items || []) {
      if (!groupedByEntity.has(item.entityId)) groupedByEntity.set(item.entityId, []);
      groupedByEntity.get(item.entityId).push(item);
    }
    const result = [];
    for (const [entityId, entityItems] of groupedByEntity) {
      const baseY = laneByEntity.get(entityId)?.y ?? bounds.y + bounds.height / 2;
      const maxSpread = laneCount > 1 ? Math.max(0, lanePitch * 0.7) : bounds.height * 0.35;
      const spacing = entityItems.length > 1
        ? Math.min(10, maxSpread / (entityItems.length - 1 || 1))
        : 0;
      entityItems.forEach((item, index) => {
        const offsetY = (index - (entityItems.length - 1) / 2) * spacing;
        const laidOut = {
          ...item,
          bucket,
          x: offAxisColumnX(bucket),
          y: clamp(baseY + offsetY, bounds.y, bounds.bottom),
          offsetY,
          offAxis: true,
          detailOnly: false,
        };
        result.push(laidOut);
        offAxisEventMap.set(item.id, laidOut);
      });
    }
    return result;
  };

  const offAxis = {
    ...(model?.offAxis || {}),
    bounds: offAxisBounds,
    columns: offAxisBounds ? {
      undated: { x: offAxisColumnX("undated"), label: "年代未明" },
      unresolved: { x: offAxisColumnX("unresolved"), label: "时间待核查" },
    } : null,
    undated: layoutOffAxisEvents(model?.offAxis?.undated, "undated"),
    unresolved: layoutOffAxisEvents(model?.offAxis?.unresolved, "unresolved"),
    preSong: (model?.offAxis?.preSong || []).map((item) => ({
      ...item,
      x: null,
      y: laneByEntity.get(item.entityId)?.y ?? null,
      offAxis: true,
      detailOnly: true,
    })),
    outsideRange: (model?.offAxis?.outsideRange || []).map((item) => ({
      ...item,
      x: null,
      y: laneByEntity.get(item.entityId)?.y ?? null,
      offAxis: true,
      detailOnly: true,
    })),
    relationEndpoints: [],
  };

  const layoutMember = (member) => {
    const event = member.timepointId != null ? eventByTimepoint.get(member.timepointId) : null;
    if (event) {
      return {
        ...member,
        baseX: event.baseX,
        x: event.displayX,
        y: event.y,
        offsetX: event.offsetX,
        offAxis: false,
        detailOnly: false,
      };
    }
    const offAxisEvent = member.timepointId != null
      ? offAxisEventMap.get(member.timepointId)
      : null;
    if (offAxisEvent) {
      return {
        ...member,
        baseX: null,
        x: offAxisEvent.x,
        y: offAxisEvent.y,
        offAxis: true,
        detailOnly: false,
      };
    }
    const lane = laneByEntity.get(member.entityId);
    if (member.effectiveYear != null
      && member.effectiveYear >= yearMin
      && member.effectiveYear <= yearMax
      && member.timeType !== "pre_song") {
      const baseX = yearToX(member.effectiveYear);
      return {
        ...member,
        baseX,
        x: baseX,
        y: lane?.y ?? bounds.y + bounds.height / 2,
        offsetX: 0,
        offAxis: false,
        detailOnly: false,
      };
    }
    const detailOnly = member.timeType === "pre_song"
      || (member.effectiveYear != null
        && (member.effectiveYear < yearMin || member.effectiveYear > yearMax));
    const bucket = member.timeType === "unresolved" ? "unresolved" : "undated";
    return {
      ...member,
      baseX: null,
      x: detailOnly ? null : offAxisColumnX(bucket),
      y: lane?.y ?? bounds.y + bounds.height / 2,
      offAxis: true,
      detailOnly,
    };
  };

  const relationsWithoutLabels = (model?.relations || []).map((relation) => {
    const sourcePoints = relation.sourceMembers.map(layoutMember);
    const targetPoints = relation.targetMembers.map(layoutMember);
    return {
      ...relation,
      sourcePoints,
      targetPoints,
      hasOffAxisEndpoint: [...sourcePoints, ...targetPoints].some((point) => point.offAxis),
      drawable: sourcePoints.some((point) => point.x != null)
        && targetPoints.some((point) => point.x != null),
    };
  });
  const relationById = new Map();
  for (const relation of relationsWithoutLabels) {
    if (!relationById.has(relation.id)) relationById.set(relation.id, []);
    relationById.get(relation.id).push(relation);
  }
  const relationGroupsWithoutLabels = (model?.relationGroups || []).map((group) => {
    const groupedRelations = uniqueBy(
      group.relationIds.flatMap((id) => relationById.get(id) || []),
      (relation) => relation.key,
    );
    const sourcePoints = uniqueBy(
      groupedRelations.flatMap((relation) => relation.sourcePoints),
      pointKey,
    );
    const targetPoints = uniqueBy(
      groupedRelations.flatMap((relation) => relation.targetPoints),
      pointKey,
    );
    const allPoints = [...sourcePoints, ...targetPoints];
    const baseXs = allPoints.map((point) => point.baseX);
    const allEndpointsDated = baseXs.length > 0 && baseXs.every(Number.isFinite);
    const commonBaseX = allEndpointsDated
      && baseXs.every((x) => Math.abs(x - baseXs[0]) < 1e-7)
      ? baseXs[0]
      : null;
    return {
      ...group,
      relations: groupedRelations,
      sourcePoints,
      targetPoints,
      junctionX: commonBaseX,
      divergentEndpointYears: commonBaseX == null && baseXs.filter(Number.isFinite).length > 1,
      renderMode: commonBaseX == null ? "individual" : "group",
      drawable: sourcePoints.some((point) => point.x != null)
        && targetPoints.some((point) => point.x != null),
    };
  });
  const aggregatedGroupIds = new Set(
    relationGroupsWithoutLabels
      .filter((group) => group.renderMode === "group")
      .map((group) => group.groupId),
  );
  const groupLabelKey = (group) => `group:${typeof group.groupId}:${String(group.groupId)}`;
  const relationLabelKey = (relation) => `relation:${relation.key}`;
  const labelItems = [
    ...relationGroupsWithoutLabels
      .filter((group) => group.drawable && group.renderMode === "group")
      .map((group) => ({
        key: groupLabelKey(group),
        id: group.groupId,
        priority: 0,
        label: group.label,
        anchor: relationGroupAnchor(group),
        stableKey: relationGroupStableKey(group),
      })),
    ...relationsWithoutLabels
      .filter((relation) => relation.drawable && (
        relation.groupId == null || !aggregatedGroupIds.has(relation.groupId)
      ))
      .map((relation) => ({
        key: relationLabelKey(relation),
        id: relation.id,
        priority: 1,
        label: relation.label,
        anchor: relationAnchor(relation),
        stableKey: relationStableKey(relation),
      })),
  ];
  const labelPlacements = layoutEvolutionLabels(labelItems, bounds, plotBounds);
  const relations = relationsWithoutLabels.map((relation) => ({
    ...relation,
    labelX: null,
    labelY: null,
    labelBounds: null,
    labelAnchorX: null,
    labelAnchorY: null,
    leader: null,
    labelVisible: false,
    labelOverflow: false,
    ...(labelPlacements.get(relationLabelKey(relation)) || {}),
  }));
  const relationByKey = new Map(relations.map((relation) => [relation.key, relation]));
  const relationGroups = relationGroupsWithoutLabels.map((group) => ({
    ...group,
    relations: group.relations.map((relation) => relationByKey.get(relation.key) || relation),
    labelX: null,
    labelY: null,
    labelBounds: null,
    labelAnchorX: null,
    labelAnchorY: null,
    leader: null,
    labelVisible: false,
    labelOverflow: false,
    ...(labelPlacements.get(groupLabelKey(group)) || {}),
  }));

  offAxis.relationEndpoints = (model?.offAxis?.relationEndpoints || []).map((endpoint) => {
    const point = layoutMember(endpoint);
    return { ...endpoint, ...point };
  });

  return {
    ...model,
    bounds,
    labelBounds,
    plotBounds,
    offAxisBounds,
    yearScale: {
      domain: [yearMin, yearMax],
      range: [plotLeft, plotRight],
    },
    lanePitch,
    lanes,
    relations,
    relationGroups,
    offAxis,
  };
}
