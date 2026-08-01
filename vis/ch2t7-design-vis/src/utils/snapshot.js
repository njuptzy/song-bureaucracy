const SNAPSHOT_TIME_TYPES = new Set(["exact", "range", "bounded"]);
const ACTIVATION_WORDS = [
  "始置", "初置", "新置", "创置", "设置", "设立", "建立", "成立", "开设", "创设",
  "复置", "复设", "恢复", "复称", "复旧", "再置", "重置", "重新设置",
  "犹存", "仍存", "尚存", "继续存在", "仍置", "仍设",
];
const NON_RESTORATION_WORDS = ["不复置", "不再置", "未复置", "不复设", "未复设"];
const DIRECT_TERMINATION_WORDS = ["解散", "撤销", "裁撤", "废止", "终结", "名止", "消亡"];
const FAILED_ACTIVATION_WORDS = ["未果", "未成", "未行", "未施行", "未实行", "收回诏书", "作罢"];

function effectiveYear(timepoint) {
  if (!SNAPSHOT_TIME_TYPES.has(timepoint?.time_type) || timepoint?.year_start == null) return null;
  // “元祐初/熙宁末”等 bounded 纪年只知道事件落在一个区间内；到上界年后
  // 才能确定事件已经发生，避免把存废变化提前到区间起点。
  if (timepoint.time_type === "bounded") return timepoint.year_end ?? timepoint.year_start;
  return timepoint.year_start;
}

function isDated(timepoint) {
  return effectiveYear(timepoint) != null;
}

function chainDepth(timepoint, byId) {
  let depth = 0;
  let current = timepoint;
  const seen = new Set();
  while (current?.prev_id != null && !seen.has(current.prev_id)) {
    seen.add(current.prev_id);
    const previous = byId.get(current.prev_id);
    if (!previous || previous.entity_id !== timepoint.entity_id) break;
    depth += 1;
    current = previous;
  }
  return depth;
}

function compareTimepoints(a, b, byId) {
  return (effectiveYear(a) - effectiveYear(b))
    || ((a.year_end ?? a.year_start) - (b.year_end ?? b.year_start))
    || (chainDepth(a, byId) - chainDepth(b, byId))
    || (a.id - b.id);
}

function occurrences(text, word, predicate = () => true) {
  const indexes = [];
  let offset = 0;
  while (offset < text.length) {
    const index = text.indexOf(word, offset);
    if (index < 0) break;
    if (predicate(index)) indexes.push(index);
    offset = index + word.length;
  }
  return indexes;
}

function lastTransition(transitions) {
  return transitions.sort((a, b) => a.index - b.index || a.priority - b.priority).at(-1)?.effect || "preserve";
}

/**
 * 判断一条叙事性时间点是否真的改变实体存废状态。
 *
 * 普通记载只保持此前状态；只有明确设置/恢复或罢废/改置事件才改变状态。
 * 同一句中有多次变化时采用最后一次，例如“始置，旋罢”最终为停用，
 * “罢，后复置”最终为启用。
 */
export function classifyExistenceEffect(timepoint, entity = {}) {
  const event = (timepoint?.event || "").replace(/\s+/g, "");
  if (!event) return "preserve";

  const transitions = [];
  const add = (effect, index, priority = 0) => {
    if (index >= 0) transitions.push({ effect, index, priority });
  };

  for (const word of NON_RESTORATION_WORDS) {
    for (const index of occurrences(event, word)) add("deactivate", index, 2);
  }
  const negativeSpans = NON_RESTORATION_WORDS.flatMap((word) => (
    occurrences(event, word).map((index) => [index, index + word.length])
  ));
  for (const word of ACTIVATION_WORDS) {
    for (const index of occurrences(event, word, (position) => {
      if (["不", "未"].includes(event[position - 1])) return false;
      return !negativeSpans.some(([start, end]) => position >= start && position < end);
    })) add("activate", index, 1);
  }

  // “由甲改置/合并而成”描述当前实体的产生，不是当前实体的终结。
  for (const match of event.matchAll(/由[^，；。]*(?:改置|改名|改称|更名|分置|合并)[^，；。]*(?:而成|为)?/g)) {
    add("activate", match.index ?? 0, 1);
  }

  for (const word of DIRECT_TERMINATION_WORDS) {
    for (const index of occurrences(event, word)) add("deactivate", index, 1);
  }
  for (const word of FAILED_ACTIVATION_WORDS) {
    for (const index of occurrences(event, word)) add("ignore", index, 3);
  }

  const title = (entity?.title || "").replace(/\s+/g, "");
  const titleIndex = title ? event.indexOf(title) : -1;
  const entityScoped = (index) => titleIndex >= 0 && titleIndex <= index;

  // “接收并入的某机构”是接收方的普通记载；只有直接并入/并归才终止当前实体。
  for (const word of ["并入", "并归"]) {
    for (const index of occurrences(event, word)) {
      const prefix = event.slice(Math.max(0, index - 2), index);
      if (prefix === "接收" || event.startsWith("由")) continue;
      if (index === 0 || /[，；。]/.test(event[index - 1]) || entityScoped(index)) {
        add("deactivate", index, 1);
      }
    }
  }

  // 裸“罢/废”很容易指向实体内部官职，只接受独立转折或明确点名当前实体的表达。
  for (const match of event.matchAll(/(?:^|[，；。]|又|旋|遂|寻|后|诏|省|一度)(罢|废)/g)) {
    const index = (match.index ?? 0) + match[0].lastIndexOf(match[1]);
    add("deactivate", index, 1);
  }
  for (const word of ["罢", "废"]) {
    for (const index of occurrences(event, word)) {
      if (entityScoped(index)) add("deactivate", index, 1);
    }
  }

  // “改为/改名为/改置为”终止来源实体；“由……改为”已在上面按新实体处理。
  if (!event.startsWith("由")) {
    for (const match of event.matchAll(/(?:^|[，；。])(改为|改名(?:为)?|改称(?:为)?|改置为)/g)) {
      const index = (match.index ?? 0) + match[0].lastIndexOf(match[1]);
      add("deactivate", index, 1);
    }
  }

  return lastTransition(transitions);
}

function relationEffectiveYear(state, timepointById) {
  if (state.effective_year != null) return state.effective_year;
  const endpointYears = [state.subject_timepoint_id, state.object_timepoint_id]
    .map((id) => timepointById.get(id))
    .filter(isDated)
    .map(effectiveYear);
  return endpointYears.length ? Math.max(...endpointYears) : null;
}

function selectRelationStates(edges, year, entityIds, timepointById, keyForEdge) {
  const candidatesByKey = new Map();
  for (const edge of edges) {
    const endpointsPresent = edge.parent != null
      ? entityIds.has(edge.parent) && entityIds.has(edge.child)
      : entityIds.has(edge.org) && entityIds.has(edge.official);
    if (!endpointsPresent) continue;
    const fallbackYears = (edge.periods || []).map((period) => period.start).filter(Number.isFinite);
    const states = edge.states?.length
      ? edge.states
      : fallbackYears.map((effectiveYear) => ({ id: edge.id, effective_year: effectiveYear }));
    for (const state of states) {
      const effectiveYear = relationEffectiveYear(state, timepointById);
      if (effectiveYear == null || effectiveYear > year) continue;
      const key = keyForEdge(edge);
      const current = candidatesByKey.get(key);
      if (!current || effectiveYear > current.effectiveYear) {
        candidatesByKey.set(key, { effectiveYear, items: [{ edge, state }] });
      } else if (effectiveYear === current.effectiveYear) {
        current.items.push({ edge, state });
      }
    }
  }
  const selected = [...candidatesByKey.values()].flatMap(({ effectiveYear, items }) => items.map(({ edge, state }) => ({
    ...edge,
    id: state.id,
    effective_year: effectiveYear,
  })));
  const deduped = new Map();
  for (const edge of selected) {
    const key = edge.parent != null
      ? `${edge.parent}:${edge.child}`
      : `${edge.org}:${edge.official}:${edge.staff_quota || ""}:${edge.staff_type || ""}`;
    if (!deduped.has(key) || edge.id > deduped.get(key).id) deduped.set(key, edge);
  }
  return [...deduped.values()];
}

export function buildYearSnapshot(data, year) {
  const entityById = new Map((data.entities || []).map((entity) => [entity.id, entity]));
  const timepointById = new Map();
  const timepointsByEntity = new Map();
  const currentTimepointByEntity = new Map();
  for (const [entityIdText, timepoints] of Object.entries(data.timepoints || {})) {
    const entityId = Number(entityIdText);
    const normalized = timepoints.map((timepoint) => ({ ...timepoint, entity_id: entityId }));
    timepointsByEntity.set(entityId, normalized);
    normalized.forEach((timepoint) => timepointById.set(timepoint.id, timepoint));
  }
  for (const [entityId, timepoints] of timepointsByEntity) {
    const eligible = timepoints
      .filter((timepoint) => isDated(timepoint) && effectiveYear(timepoint) <= year)
      .sort((a, b) => compareTimepoints(a, b, timepointById));
    let exists = null;
    let currentState = null;
    for (const timepoint of eligible) {
      const effect = classifyExistenceEffect(timepoint, entityById.get(entityId));
      if (effect === "activate") exists = true;
      else if (effect === "deactivate") exists = false;
      else if (effect === "ignore") {
        currentState = timepoint;
        continue;
      }
      // bounded 普通记载只能说明“事件发生在某段内”，不足以单独确定某一年的存在；
      // 但其中明确的设置/罢废转换仍会在区间上界年生效。
      else if (exists == null && timepoint.time_type !== "bounded") exists = true;
      currentState = timepoint;
    }
    if (exists && currentState) currentTimepointByEntity.set(entityId, currentState);
  }
  const entityIds = new Set(currentTimepointByEntity.keys());
  const hierarchyEdges = selectRelationStates(
    data.hierarchyEdges || [],
    year,
    entityIds,
    timepointById,
    (edge) => `hierarchy:${edge.child}`
  );
  const staffEdges = selectRelationStates(
    data.staffEdges || [],
    year,
    entityIds,
    timepointById,
    (edge) => `staff:${edge.official}`
  );
  return { year, currentTimepointByEntity, entityIds, hierarchyEdges, staffEdges };
}
