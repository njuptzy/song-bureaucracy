function normalizeInlineText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function compactText(value) {
  return normalizeInlineText(value).replace(/[\s，,；;。！？!?：:、（）()《》“”‘’]/g, "");
}

function longestSharedSlice(firstValue, secondValue) {
  const first = compactText(firstValue);
  const second = compactText(secondValue);
  if (!first || !second) return "";
  const previous = Array.from({ length: second.length + 1 }, () => 0);
  let longest = "";
  for (let firstIndex = 1; firstIndex <= first.length; firstIndex += 1) {
    const current = Array.from({ length: second.length + 1 }, () => 0);
    for (let secondIndex = 1; secondIndex <= second.length; secondIndex += 1) {
      if (first[firstIndex - 1] !== second[secondIndex - 1]) continue;
      current[secondIndex] = previous[secondIndex - 1] + 1;
      if (current[secondIndex] > longest.length) {
        longest = first.slice(firstIndex - current[secondIndex], firstIndex);
      }
    }
    previous.splice(0, previous.length, ...current);
  }
  return longest;
}

function bestClauseSharedSlice(reference, quotation) {
  let bestShared = "";
  for (const clause of String(quotation || "").split(/[，,；;。！？!?：:\n]+/)) {
    const shared = longestSharedSlice(reference, clause);
    if (shared.length > bestShared.length) bestShared = shared;
  }
  return bestShared;
}

/**
 * 从较长的辞典字段引文中找出与当前时间点真正对应的最小片段。
 * 纪年采用原文中的精确子串；事件采用事件描述与原文分句的最长连续重合，
 * 避免把包含多个年代、多个事件的整段 quotation 全部高亮。
 */
export function preciseTimepointEvidenceTerms({
  quotations = [],
  eventText = "",
  rawTime = "",
  entityTitle = "",
} = {}) {
  const terms = [];
  const normalizedEvent = compactText(eventText);
  const normalizedTime = compactText(rawTime);
  const normalizedTitle = compactText(entityTitle);
  const minimumSharedLength = Math.max(2, Math.min(4, Math.ceil(normalizedEvent.length * 0.35)));
  const minimumTimeLength = Math.max(2, Math.ceil(normalizedTime.length * 0.6));

  for (const quotationValue of quotations || []) {
    const quotation = normalizeInlineText(quotationValue);
    if (!quotation) continue;

    if (normalizedTime && quotation.includes(normalizedTime)) {
      terms.push(normalizedTime);
    } else if (normalizedTime) {
      const sharedTime = bestClauseSharedSlice(normalizedTime, quotation);
      if (sharedTime.length >= minimumTimeLength) terms.push(sharedTime);
    }

    if (!normalizedEvent) continue;
    if (quotation.includes(normalizedEvent)) {
      terms.push(normalizedEvent);
      continue;
    }

    const bestShared = bestClauseSharedSlice(normalizedEvent, quotation);
    const titleOnly = normalizedTitle
      && (bestShared === normalizedTitle || normalizedTitle.includes(bestShared));
    if (bestShared.length >= minimumSharedLength && !titleOnly) terms.push(bestShared);
  }

  return evidenceHighlightTerms(terms);
}

export function evidenceHighlightTerms(values = []) {
  const seen = new Set();
  return (values || [])
    .map(normalizeInlineText)
    .filter((value) => {
      if (!value || seen.has(value)) return false;
      seen.add(value);
      return true;
    })
    .sort((first, second) => second.length - first.length);
}

export function evidenceHighlightMask(text, terms = []) {
  const content = String(text || "");
  const mask = Array.from({ length: content.length }, () => false);
  for (const term of evidenceHighlightTerms(terms)) {
    let offset = 0;
    while (offset < content.length) {
      const index = content.indexOf(term, offset);
      if (index < 0) break;
      for (let cursor = index; cursor < index + term.length; cursor += 1) mask[cursor] = true;
      offset = index + Math.max(1, term.length);
    }
  }
  return mask;
}

export function evidenceLineSegments(text, terms = []) {
  const content = String(text || "");
  const mask = evidenceHighlightMask(content, terms);
  const segments = [];
  for (let index = 0; index < content.length; index += 1) {
    const highlighted = mask[index];
    const previous = segments.at(-1);
    if (previous?.highlighted === highlighted) previous.text += content[index];
    else segments.push({ text: content[index], highlighted });
  }
  return segments;
}
