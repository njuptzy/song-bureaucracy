export function relationOriginalSections({
  relationshipLabel = "关系来源词条原文：",
  relationshipText = "",
  dictionaryText = "",
  quotation = "",
} = {}) {
  return [
    { label: relationshipLabel, value: relationshipText },
    { label: "词条原文：", value: dictionaryText },
    { label: "原文引文：", value: quotation },
  ];
}
