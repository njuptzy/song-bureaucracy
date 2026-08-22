function normalizeInlineText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
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
