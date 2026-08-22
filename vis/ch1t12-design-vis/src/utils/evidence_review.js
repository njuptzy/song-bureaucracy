export const EVIDENCE_VERDICT_META = {
  supported: { marker: "green", symbol: "✓", label: "本条引文支持该事件", excerptLabel: "支持片段：" },
  not_supported: { marker: "amber", symbol: "!", label: "本条引文相关，但证据不足", excerptLabel: "相关片段：" },
  contradicted: { marker: "red", symbol: "×", label: "本条引文与该事件冲突", excerptLabel: "冲突片段：" },
  irrelevant: { marker: "critical", symbol: "×", label: "本条引文与该事件完全无关（高风险）", excerptLabel: "" },
};

export function evidenceReviewKey(timepointId, citationRowId, evidenceText = "") {
  let hash = 2166136261;
  for (const character of String(evidenceText)) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return `${Number(timepointId)}:${Number(citationRowId)}:${(hash >>> 0).toString(16)}`;
}

export function evidenceReviewQuotationHighlights(result, quotation = "") {
  if (!EVIDENCE_VERDICT_META[result?.verdict] || result.verdict === "irrelevant") return [];
  const source = String(quotation || "");
  return [...new Set(result.concise_quotations || [])]
    .map((span) => String(span || "").trim())
    .filter((span) => span && source.includes(span));
}

export function evidenceReviewSections(result) {
  if (!result) return [];
  if (result.status === "loading") {
    return [{ label: "核验状态：", value: "正在核验本条引文…", reviewTone: "neutral" }];
  }
  if (result.status === "error") {
    return [
      { label: "核验状态：", value: "核验未完成", reviewTone: "neutral" },
      { label: "提示：", value: "当前无法取得有效核验结果，请重试。" },
    ];
  }
  const meta = EVIDENCE_VERDICT_META[result.verdict];
  if (!meta) return [];
  const sections = [{
    label: "核验结论：",
    value: `${meta.symbol} ${meta.label}`,
    reviewTone: meta.marker,
  }];
  for (const quotation of result.concise_quotations || []) {
    sections.push({ label: meta.excerptLabel, value: quotation, reviewTone: meta.marker });
  }
  sections.push({ label: "判断理由：", value: result.reason });
  return sections;
}

export async function requestEvidenceReview(timepointId, citationRowId, signal) {
  const response = await fetch("/api/evidence-review", {
    method: "POST",
    cache: "no-store",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      timepoint_id: Number(timepointId),
      citation_row_id: Number(citationRowId),
    }),
  });
  let payload = {};
  try {
    payload = await response.json();
  } catch {
    // 统一为用户可重试的中性错误，不泄露上游响应。
  }
  if (!response.ok) {
    const error = new Error(payload.error || "引文核验暂时无法完成");
    error.code = payload.code || "service_unavailable";
    error.retryable = payload.retryable !== false;
    throw error;
  }
  return payload;
}

export async function requestCachedEvidenceReview(timepointId, citationRowId, signal) {
  const query = new URLSearchParams({
    timepoint_id: String(Number(timepointId)),
    citation_row_id: String(Number(citationRowId)),
  });
  const response = await fetch(`/api/evidence-review?${query}`, {
    method: "GET",
    cache: "no-store",
    signal,
  });
  if (response.status === 404) return null;
  let payload = {};
  try {
    payload = await response.json();
  } catch {
    // 读取失败不触发模型，也不覆盖当前界面。
  }
  if (!response.ok) return null;
  return payload;
}
