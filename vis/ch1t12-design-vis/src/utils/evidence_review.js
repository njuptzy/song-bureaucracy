export const EVIDENCE_VERDICT_META = {
  supported: { marker: "green", symbol: "✓", label: "本条引文支持该事件" },
  not_supported: { marker: "red", symbol: "×", label: "本条引文未能支持该事件" },
  contradicted: { marker: "red", symbol: "×", label: "本条引文与该事件冲突" },
};

export function evidenceReviewKey(timepointId, citationRowId, evidenceText = "") {
  let hash = 2166136261;
  for (const character of String(evidenceText)) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return `${Number(timepointId)}:${Number(citationRowId)}:${(hash >>> 0).toString(16)}`;
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
  if (result.verdict === "supported") {
    for (const quotation of result.concise_quotations || []) {
      sections.push({ label: "精简原文：", value: quotation });
    }
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
