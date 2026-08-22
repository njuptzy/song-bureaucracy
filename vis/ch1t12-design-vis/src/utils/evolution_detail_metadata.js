export function timepointContextSections({
  timeType = "",
  timeTypeLabel = "",
  parseNote = "",
  entryComparisonText = "",
  relatedRelationshipLabels = [],
} = {}) {
  const sections = [];
  if (timeType && timeType !== "exact") {
    sections.push({
      label: "时间精度：",
      value: `${timeTypeLabel || timeType}${parseNote ? `；${parseNote}` : ""}`,
    });
  }
  if (entryComparisonText) {
    sections.push({ label: "距入口年份：", value: entryComparisonText });
  }
  const related = [...new Set(relatedRelationshipLabels.filter(Boolean))];
  if (related.length) {
    sections.push({ label: "相关关系：", value: related.join("；") });
  }
  return sections;
}
