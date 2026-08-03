const CLAUSE_SEPARATOR = /[，；。！？]/g;

const ACTIVATION_VERBS = [
  "正式建置", "正式举职", "重新设置", "继续存在", "始置", "初置", "新置", "创置", "设置", "设立", "建立", "成立",
  "开设", "创设", "复置", "复设", "恢复", "复称", "复旧", "再置", "重置", "仍置", "仍设",
  "犹存", "仍存", "尚存",
];
const NEGATED_ACTIVATION_VERBS = ["不复置", "不再置", "未复置", "不复设", "未复设"];
const TERMINATION_VERBS = ["废罢", "罢废", "解散", "撤销", "裁撤", "废止", "终结", "名止", "消亡", "罢", "废"];
const FAILED_CHANGE_WORDS = ["未果", "未成", "未行", "未施行", "未实行", "收回诏书", "作罢"];
const IMPLICIT_SOURCE_VERBS = [
  "复分为", "分为", "并入", "并归", "复改为", "复改名为", "复改名", "复改称为", "复改称",
  "改为", "改名为", "改名", "改称为", "改称", "改置为",
];

function splitClauses(text) {
  const clauses = [];
  let start = 0;
  for (const match of text.matchAll(CLAUSE_SEPARATOR)) {
    if (match.index > start) clauses.push({ text: text.slice(start, match.index), start });
    start = match.index + match[0].length;
  }
  if (start < text.length) clauses.push({ text: text.slice(start), start });
  return clauses;
}

function occurrences(text, word) {
  const indexes = [];
  let offset = 0;
  while (offset < text.length) {
    const index = text.indexOf(word, offset);
    if (index < 0) break;
    indexes.push(index);
    offset = index + word.length;
  }
  return indexes;
}

function exactEntityPhrase(text, title) {
  if (!title) return false;
  return text === title || text === `${title}之名` || text === `${title}名`;
}

function stripDiscourseLead(text) {
  let result = text;
  const leads = [
    "与此同时", "其后", "此后", "一度", "后来", "旋即", "统一", "避讳", "旋", "遂", "寻", "又", "后", "但", "而", "诏",
  ];
  let changed = true;
  while (changed) {
    changed = false;
    for (const lead of leads) {
      if (result.startsWith(lead)) {
        result = result.slice(lead.length);
        changed = true;
        break;
      }
    }
  }
  return result;
}

function implicitTerminationTargetsCurrent(before, after) {
  // 时间点本身已经限定了叙述对象，以下词组只是终止动作的语气或制度背景，
  // 不是另一个被罢对象。例如“元丰改制后罢置”“新官制下罢置”。
  if (after && after !== "置") return false;
  if (["正式", "明令", "实际", "再次", "至迟已"].includes(before)) return true;
  if (!after && /后又$/.test(before)) return true;
  if (/^(?:元丰)?改制(?:正名)?后$/.test(before)) return true;
  if (/^(?:行)?新官制(?:下|后)$/.test(before)) return true;
  // “随司天监罢置”表示当前官职或机构随其所属机构一并终止。
  if (/^随.+$/.test(before)) return true;
  return false;
}

function verbTargetsEntity(clause, index, verb, title, { activation = false, termination = false } = {}) {
  const before = stripDiscourseLead(clause.slice(0, index));
  const after = clause.slice(index + verb.length);

  // 明示主语：“三司罢”“太常寺之名废止”。不能只做 title 子串匹配，
  // 否则“太常寺主簿罢置”会把太常寺本身误判为被罢。
  if (exactEntityPhrase(before, title)) return true;

  // 明示宾语：“罢三司”。同样要求完整实体名，不能把“罢三司某案”算作三司被罢。
  if (exactEntityPhrase(after, title)) return true;

  // 只有没有其他名词宾语的独立陈述，才允许按时间点所属实体补出省略的主语。
  if (!before && !after) return true;
  if (!before && /^(?:置|去|归|并归|并入|改|易|后|而)/.test(after)) return true;
  if (activation && !before && /^(?:于|在)/.test(after)) return true;
  // “复置行在同文馆”等写法中，“行在”是地点限定，后面的完整实体名
  // 仍是复置对象；不能因地点前缀而漏掉恢复语义。
  if (activation && title && after === `行在${title}`) return true;
  if (termination && implicitTerminationTargetsCurrent(before, after)) return true;
  return false;
}

function addTransition(transitions, effect, index, reason, priority = 0) {
  transitions.push({ effect, index, reason, priority });
}

/**
 * 对实体时间点中的叙事文本作保守的生命周期判定。
 *
 * 核心约束：存废词必须以“当前实体”为动作对象；仅仅提到罢废、设置了下属机构或
 * 官职，不改变当前实体状态。无法确认动作对象时返回 preserve，并由普通同时代记载
 * 继续证明该实体在当年存在。
 */
export function classifyEntityLifecycle(eventText, entity = {}) {
  const text = String(eventText || "").replace(/\s+/g, "");
  const title = String(entity?.title || "").replace(/\s+/g, "");
  if (!text) return { effect: "preserve", transitions: [] };

  const transitions = [];
  for (const { text: clause, start } of splitClauses(text)) {
    for (const word of FAILED_CHANGE_WORDS) {
      for (const index of occurrences(clause, word)) {
        addTransition(transitions, "ignore", start + index, `变化未实施：${word}`, 4);
      }
    }

    for (const verb of NEGATED_ACTIVATION_VERBS) {
      for (const index of occurrences(clause, verb)) {
        if (verbTargetsEntity(clause, index, verb, title)) {
          addTransition(transitions, "deactivate", start + index, `当前实体未再设置：${verb}`, 3);
        }
      }
    }

    for (const verb of ACTIVATION_VERBS) {
      for (const index of occurrences(clause, verb)) {
        const precededByNegation = ["不", "未"].includes(clause[index - 1]);
        if (!precededByNegation && verbTargetsEntity(clause, index, verb, title, { activation: true })) {
          addTransition(transitions, "activate", start + index, `当前实体设置或恢复：${verb}`, 2);
        }
      }
    }

    // “由甲改置为乙”“甲合并为乙”只有在结果明确是当前实体时，才证明当前实体产生。
    const resultMatch = clause.match(
      /(?:复改称为|复改称|复改名为|复改名|改置为|改名为|改名|改称为|改称|更名为|更名|合并为|合置为|重合为|仍为|依旧为)([^为]+)$/,
    );
    if (title && resultMatch?.[1] === title) {
      const index = clause.length - title.length;
      addTransition(transitions, "activate", start + index, "当前实体是改制或合并结果", 2);
    }

    for (const verb of TERMINATION_VERBS) {
      for (const index of occurrences(clause, verb)) {
        if (verbTargetsEntity(clause, index, verb, title, { termination: true })) {
          addTransition(transitions, "deactivate", start + index, `当前实体终止：${verb}`, 2);
        }
      }
    }

    // 当前实体作为省略的并列主语：“与外剥马务合为皮剥所”；或前半句先叙述
    // 当前实体的位置变化，后半句“并与……合并”。这种结构的被合并者就是当前实体。
    if ((start === 0 && clause.startsWith("与") && /(?:合并|合为)/.test(clause))
      || /并与[^，；。]*(?:合并|合为)/.test(clause)) {
      const index = Math.max(clause.lastIndexOf("合并"), clause.lastIndexOf("合为"));
      addTransition(transitions, "deactivate", start + index, "当前实体与其他实体合并", 2);
    }

    for (const phrase of ["实体官署实废", "空存其名", "名存实废", "名具实废"]) {
      if (clause.includes(phrase)) {
        addTransition(transitions, "deactivate", start + clause.indexOf(phrase), `原文明确机构仅存空名：${phrase}`, 2);
      }
    }

    // 这些动词的宾语是去向而不是被处置对象；仅在分句以动词起首、明确省略当前实体
    // 这个主语时，才把当前实体判为终止。“某下属改为……”不会命中。
    const actionClause = stripDiscourseLead(clause);
    const actionStart = clause.length - actionClause.length;
    for (const verb of IMPLICIT_SOURCE_VERBS) {
      if (actionClause.startsWith(verb)) {
        addTransition(transitions, "deactivate", start + actionStart, `当前实体${verb}其他实体`, 2);
      }
    }
  }

  const last = transitions
    .sort((a, b) => a.index - b.index || a.priority - b.priority)
    .at(-1);
  return { effect: last?.effect || "preserve", transitions };
}

export function classifyExistenceEffect(timepoint, entity = {}) {
  return classifyEntityLifecycle(timepoint?.event, entity).effect;
}

/**
 * 数据库中曾有上级记录的机构，在所选年份没有可见上级时处于层级断档，
 * 不能因此被提升为虚拟中央根节点。递归处理可避免其下级继续冒充根节点。
 * assignments 必须已经按年份筛成各下级的最新关系状态；historicalChildIds
 * 则包含数据库全部历史上下级关系中的下级实体。
 */
export function detachedHierarchyEntityIds(assignments, activeEntityIds, historicalChildIds = null) {
  const visible = new Set(activeEntityIds || []);
  const parentsByChild = new Map();
  for (const assignment of assignments || []) {
    const parentId = assignment?.parentId;
    const childId = assignment?.childId;
    if (parentId == null || childId == null || parentId === childId) continue;
    if (!parentsByChild.has(childId)) parentsByChild.set(childId, new Set());
    parentsByChild.get(childId).add(parentId);
  }
  for (const childId of historicalChildIds || []) {
    if (childId != null && !parentsByChild.has(childId)) parentsByChild.set(childId, new Set());
  }

  const hidden = new Set();
  let changed = true;
  while (changed) {
    changed = false;
    for (const [childId, parentIds] of parentsByChild) {
      if (!visible.has(childId)) continue;
      if ([...parentIds].some((parentId) => visible.has(parentId))) continue;
      visible.delete(childId);
      hidden.add(childId);
      changed = true;
    }
  }
  return hidden;
}

/**
 * 统称本身若有历史上级，它的实例也不能绕过该关系成为虚拟中央根节点。
 * 递归展开可覆盖“统称的实例仍是另一个统称”的嵌套结构。
 */
export function expandHistoricalHierarchyChildIds(directChildIds, memberships) {
  const result = new Set(directChildIds || []);
  let changed = true;
  while (changed) {
    changed = false;
    for (const membership of memberships || []) {
      if (!result.has(membership?.collectiveEntityId)
        || result.has(membership?.instanceEntityId)) continue;
      result.add(membership.instanceEntityId);
      changed = true;
    }
  }
  return result;
}

/**
 * 统称发生明确的前后演变时，旧统称下已生效的实例名称也同步退出。
 * 新实例是否进入截面仍由新实例自己的时间点决定，不在这里猜测一一对应关系。
 */
export function expandCollectiveInstanceTransitions(transitions, memberships) {
  const expanded = [...(transitions || [])];
  for (const transition of transitions || []) {
    if (transition?.effectiveYear == null) continue;
    for (const membership of memberships || []) {
      if (membership?.collectiveEntityId !== transition.sourceEntityId) continue;
      if (membership.effectiveYear != null
        && membership.effectiveYear > transition.effectiveYear) continue;
      expanded.push({
        sourceEntityId: membership.instanceEntityId,
        targetEntityId: transition.targetEntityId,
        effectiveYear: transition.effectiveYear,
      });
    }
  }
  return expanded;
}

/**
 * “前后演变”表示同一制度对象的版本切换。只要某个有纪年的后继已经生效，
 * 它的来源实体以及沿无纪年演变边可追溯到的更早名称都必须退出年度截面。
 *
 * transitions: [{ sourceEntityId, targetEntityId, effectiveYear }]
 * effectiveYear 为 null 的边本身不猜测切换年份，但可在下游有确定年份时
 * 作为谱系连接使用。例如“病坊（年月未载）→安乐坊→1104安济坊”。
 */
export function evolutionDeactivationYears(transitions, year) {
  const incomingByTarget = new Map();
  for (const transition of transitions || []) {
    if (transition?.sourceEntityId == null || transition?.targetEntityId == null) continue;
    if (!incomingByTarget.has(transition.targetEntityId)) {
      incomingByTarget.set(transition.targetEntityId, []);
    }
    incomingByTarget.get(transition.targetEntityId).push(transition);
  }

  const deactivated = new Map();
  const markDeactivated = (entityId, anchorYear) => {
    const previous = deactivated.get(entityId);
    if (previous == null || anchorYear > previous) deactivated.set(entityId, anchorYear);
  };
  const visitAncestors = (entityId, anchorYear, seen) => {
    if (seen.has(entityId)) return;
    seen.add(entityId);
    for (const transition of incomingByTarget.get(entityId) || []) {
      // 只沿无纪年边回溯：它们本身无法决定旧名何时退出，需要借下游
      // 有纪年的切换点补足。已有纪年的旧边已经在自己的年份直接生效，
      // 若继续按当前 anchorYear 递归传播，会把 A→B→A 这类复归循环中的 A
      // 在恢复当年再次误删（如三司分部后又重合为三司）。
      if (transition.effectiveYear != null) continue;
      markDeactivated(transition.sourceEntityId, anchorYear);
      visitAncestors(transition.sourceEntityId, anchorYear, seen);
    }
  };

  for (const transition of transitions || []) {
    if (transition.effectiveYear == null || transition.effectiveYear > year) continue;
    markDeactivated(transition.sourceEntityId, transition.effectiveYear);
    visitAncestors(transition.sourceEntityId, transition.effectiveYear, new Set());
  }
  return deactivated;
}
