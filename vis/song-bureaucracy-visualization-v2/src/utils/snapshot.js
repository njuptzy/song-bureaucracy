const SNAPSHOT_TIME_TYPES = new Set(["exact", "range", "bounded"]);
const ACTIVATION_WORDS = [
  "始置", "初置", "新置", "创置", "设置", "设立", "建立", "成立", "开设", "创设",
  "复置", "复设", "恢复", "复称", "复旧", "再置", "重置", "重新设置",
  "犹存", "仍存", "尚存", "继续存在", "仍置", "仍设",
];
const NON_RESTORATION_WORDS = ["不复置", "不再置", "未复置", "不复设", "未复设"];
const DIRECT_TERMINATION_WORDS = ["解散", "撤销", "裁撤", "废止", "终结", "名止", "消亡"];
const FAILED_ACTIVATION_WORDS = ["未果", "未成", "未行", "未施行", "未实行", "收回诏书", "作罢"];

function effectiveYear(event) {
  if (!SNAPSHOT_TIME_TYPES.has(event?.timeType) || event?.yearStart == null) return null;
  if (event.timeType === "bounded") return event.yearEnd ?? event.yearStart;
  return event.yearStart;
}

function isDated(event) {
  return effectiveYear(event) != null;
}

function chainDepth(event, eventById) {
  let depth = 0;
  let current = event;
  const seen = new Set();
  while (current?.prevId != null && !seen.has(current.prevId)) {
    seen.add(current.prevId);
    const previous = eventById.get(current.prevId);
    if (!previous || previous.entityId !== event.entityId) break;
    depth += 1;
    current = previous;
  }
  return depth;
}

function compareEvents(a, b, eventById) {
  return (effectiveYear(a) - effectiveYear(b))
    || ((a.yearEnd ?? a.yearStart) - (b.yearEnd ?? b.yearStart))
    || (chainDepth(a, eventById) - chainDepth(b, eventById))
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

function classifyExistenceEffect(event, entity = {}) {
  const text = (event?.event || "").replace(/\s+/g, "");
  if (!text) return "preserve";
  const transitions = [];
  const add = (effect, index, priority = 0) => {
    if (index >= 0) transitions.push({ effect, index, priority });
  };

  for (const word of NON_RESTORATION_WORDS) {
    for (const index of occurrences(text, word)) add("deactivate", index, 2);
  }
  const negativeSpans = NON_RESTORATION_WORDS.flatMap((word) => (
    occurrences(text, word).map((index) => [index, index + word.length])
  ));
  for (const word of ACTIVATION_WORDS) {
    for (const index of occurrences(text, word, (position) => {
      if (["不", "未"].includes(text[position - 1])) return false;
      return !negativeSpans.some(([start, end]) => position >= start && position < end);
    })) add("activate", index, 1);
  }
  for (const match of text.matchAll(/由[^，；。]*(?:改置|改名|改称|更名|分置|合并)[^，；。]*(?:而成|为)?/g)) {
    add("activate", match.index ?? 0, 1);
  }
  for (const word of DIRECT_TERMINATION_WORDS) {
    for (const index of occurrences(text, word)) add("deactivate", index, 1);
  }
  for (const word of FAILED_ACTIVATION_WORDS) {
    for (const index of occurrences(text, word)) add("ignore", index, 3);
  }

  const title = (entity?.title || "").replace(/\s+/g, "");
  const titleIndex = title ? text.indexOf(title) : -1;
  const entityScoped = (index) => titleIndex >= 0 && titleIndex <= index;
  for (const word of ["并入", "并归"]) {
    for (const index of occurrences(text, word)) {
      const prefix = text.slice(Math.max(0, index - 2), index);
      if (prefix === "接收" || text.startsWith("由")) continue;
      if (index === 0 || /[，；。]/.test(text[index - 1]) || entityScoped(index)) {
        add("deactivate", index, 1);
      }
    }
  }
  for (const match of text.matchAll(/(?:^|[，；。]|又|旋|遂|寻|后|诏|省|一度)(罢|废)/g)) {
    const index = (match.index ?? 0) + match[0].lastIndexOf(match[1]);
    add("deactivate", index, 1);
  }
  for (const word of ["罢", "废"]) {
    for (const index of occurrences(text, word)) {
      if (entityScoped(index)) add("deactivate", index, 1);
    }
  }
  if (!text.startsWith("由")) {
    for (const match of text.matchAll(/(?:^|[，；。])(改为|改名(?:为)?|改称(?:为)?|改置为)/g)) {
      const index = (match.index ?? 0) + match[0].lastIndexOf(match[1]);
      add("deactivate", index, 1);
    }
  }
  return transitions.sort((a, b) => a.index - b.index || a.priority - b.priority).at(-1)?.effect || "preserve";
}

function relationEffectiveYear(relation, eventById) {
  const endpointYears = [relation.subjectId, relation.objectId]
    .map((id) => eventById.get(id))
    .filter(isDated)
    .map(effectiveYear);
  return endpointYears.length ? Math.max(...endpointYears) : null;
}

function relationStateKey(relation) {
  if (relation.type === "上下级机构") return `hierarchy:${relation.objectEntityId}`;
  if (relation.type === "编制隶属") return `staff:${relation.objectEntityId}`;
  return `${relation.type}:${relation.subjectEntityId}:${relation.objectEntityId}`;
}

export function buildYearSnapshot(dataset, year) {
  const entityById = new Map(dataset.entities.map((entity) => [entity.id, entity]));
  const eventById = new Map(dataset.events.map((event) => [event.id, event]));
  const eventsByEntity = new Map();
  for (const event of dataset.events) {
    if (!eventsByEntity.has(event.entityId)) eventsByEntity.set(event.entityId, []);
    eventsByEntity.get(event.entityId).push(event);
  }

  const currentEventByEntity = new Map();
  for (const [entityId, events] of eventsByEntity) {
    const eligible = events
      .filter((event) => isDated(event) && effectiveYear(event) <= year)
      .sort((a, b) => compareEvents(a, b, eventById));
    let exists = null;
    let currentEvent = null;
    for (const event of eligible) {
      const effect = classifyExistenceEffect(event, entityById.get(entityId));
      if (effect === "activate") exists = true;
      else if (effect === "deactivate") exists = false;
      else if (effect === "ignore") {
        currentEvent = event;
        continue;
      } else if (exists == null && event.timeType !== "bounded") exists = true;
      currentEvent = event;
    }
    if (exists && currentEvent) {
      currentEventByEntity.set(entityId, currentEvent);
    }
  }

  const entityIds = new Set(currentEventByEntity.keys());
  const relationStates = new Map();
  for (const relation of dataset.relations) {
    if (!entityIds.has(relation.subjectEntityId) || !entityIds.has(relation.objectEntityId)) continue;
    const effectiveYear = relationEffectiveYear(relation, eventById);
    if (effectiveYear == null || effectiveYear > year) continue;
    const key = relationStateKey(relation);
    const current = relationStates.get(key);
    if (!current || effectiveYear > current.effectiveYear) {
      relationStates.set(key, { effectiveYear, relations: [relation] });
    } else if (effectiveYear === current.effectiveYear) {
      current.relations.push(relation);
    }
  }
  const relations = [...relationStates.values()].flatMap(({ effectiveYear, relations: items }) => (
    items.map((relation) => ({ ...relation, effectiveYear }))
  ));

  return {
    year,
    currentEventByEntity,
    entityIds,
    entities: dataset.entities.filter((entity) => entityIds.has(entity.id)),
    relations,
  };
}
