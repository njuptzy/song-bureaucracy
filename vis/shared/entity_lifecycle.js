const CLAUSE_SEPARATOR = /[，；。！？]/g;

const ACTIVATION_VERBS = [
  "重新设置", "继续存在", "始置", "初置", "新置", "创置", "设置", "设立", "建立", "成立",
  "开设", "创设", "复置", "复设", "恢复", "复称", "复旧", "再置", "重置", "仍置", "仍设",
  "犹存", "仍存", "尚存",
];
const NEGATED_ACTIVATION_VERBS = ["不复置", "不再置", "未复置", "不复设", "未复设"];
const TERMINATION_VERBS = ["解散", "撤销", "裁撤", "废止", "终结", "名止", "消亡", "罢", "废"];
const FAILED_CHANGE_WORDS = ["未果", "未成", "未行", "未施行", "未实行", "收回诏书", "作罢"];
const IMPLICIT_SOURCE_VERBS = ["并入", "并归", "改为", "改名为", "改名", "改称为", "改称", "改置为"];

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
  const leads = ["与此同时", "其后", "此后", "一度", "后来", "旋即", "旋", "遂", "寻", "又", "后", "但", "而", "诏"];
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

function verbTargetsEntity(clause, index, verb, title, { activation = false } = {}) {
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
    if (title && (clause.endsWith(`为${title}`) || clause.endsWith(`成${title}`))) {
      const index = Math.max(clause.lastIndexOf(`为${title}`), clause.lastIndexOf(`成${title}`));
      if (/(?:由|改置|改名|改称|更名|合并|合置|重合)/.test(clause.slice(0, index))) {
        addTransition(transitions, "activate", start + index, "当前实体是改制或合并结果", 2);
      }
    }

    for (const verb of TERMINATION_VERBS) {
      for (const index of occurrences(clause, verb)) {
        if (verbTargetsEntity(clause, index, verb, title)) {
          addTransition(transitions, "deactivate", start + index, `当前实体终止：${verb}`, 2);
        }
      }
    }

    // 这些动词的宾语是去向而不是被处置对象；仅在分句以动词起首、明确省略当前实体
    // 这个主语时，才把当前实体判为终止。“某下属改为……”不会命中。
    for (const verb of IMPLICIT_SOURCE_VERBS) {
      if (clause.startsWith(verb)) {
        addTransition(transitions, "deactivate", start, `当前实体${verb}其他实体`, 2);
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
