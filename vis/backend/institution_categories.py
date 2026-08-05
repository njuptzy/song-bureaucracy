"""Classify institutions into the five categories used by the design visualization."""

from collections.abc import Iterable


CATEGORY_NAMES = (
    "内廷机构",
    "中央机构",
    "路级机构",
    "州县机构",
    "军队机构",
)

_ATTRIBUTE_MARKERS = {
    "州县机构": ("州府", "州县", "县级", "地方行政单位"),
    # “路”只按明确的行政层级措辞识别，避免把“京师道路机构”误判为路级。
    "路级机构": ("路级",),
    "军队机构": ("军事", "军队", "禁军", "军号", "统兵", "军实例", "军编制"),
    "内廷机构": (
        "内廷",
        "内庭",
        "宫廷",
        "宫中",
        "宫内",
        "宫禁",
        "内侍",
        "东宫",
        "后宫",
        "御前",
        "尚书内省",
    ),
    "中央机构": ("中央", "中枢"),
}

_CHAPTER_CATEGORIES = {
    "第一编": "内廷机构",
    "第二编": "中央机构",
    "第三编": "中央机构",
    "第四编": "中央机构",
    "第五编": "中央机构",
    "第六编": "中央机构",
    "第八编": "军队机构",
    "第九编": "路级机构",
    "第十编": "州县机构",
}

_CHAPTER_SEVEN_MILITARY_SECTIONS = (
    "禁军三衙门",
    "三卫官与六统军门",
    "环卫官门",
)

_NON_CENTRAL_PRIORITY = ("州县机构", "路级机构", "军队机构", "内廷机构")


def _attribute_candidates(attr_categories: Iterable[str]) -> set[str]:
    attrs = " ".join(item for item in attr_categories if item)
    return {
        category
        for category, markers in _ATTRIBUTE_MARKERS.items()
        if any(marker in attrs for marker in markers)
    }


def _catalog_category(catalog: str) -> str | None:
    if "第七编 皇宫京城禁卫侍奉机构类" in catalog:
        if any(section in catalog for section in _CHAPTER_SEVEN_MILITARY_SECTIONS):
            return "军队机构"
        return "内廷机构"
    for chapter, category in _CHAPTER_CATEGORIES.items():
        if chapter in catalog:
            return category
    return None


def catalog_categories(source_catalogs: Iterable[str]) -> set[str]:
    return {
        category
        for catalog in source_catalogs
        if catalog and (category := _catalog_category(catalog))
    }


def resolve_source_catalogs(
    entity_title: str,
    source_refs: Iterable[tuple[str, str]],
    catalogs_by_reference,
    catalogs_by_page,
    catalogs_by_title,
) -> set[str]:
    """Resolve catalogs without letting ambiguous title fallback pollute precise evidence."""
    headword_catalogs = set()
    precise_catalogs = set()
    fallback_catalogs = set()

    for source_entry, source_page in source_refs:
        exact = catalogs_by_reference.get((source_entry, source_page), set())
        catalogs = exact
        if not catalogs and source_page:
            catalogs = catalogs_by_page.get(source_page, set())
        if catalogs:
            precise_catalogs.update(catalogs)
            if exact and source_entry == entity_title:
                headword_catalogs.update(catalogs)
        elif source_entry:
            fallback_catalogs.update(catalogs_by_title.get(source_entry, set()))

    # The entity's own formal dictionary headword is stronger than incidental
    # mentions in other entries. If no own headword exists, page evidence is
    # still stronger than a page-less same-title fallback.
    return headword_catalogs or precise_catalogs or fallback_catalogs


def classify_institution(
    attr_categories: Iterable[str], source_catalogs: Iterable[str]
) -> tuple[str | None, str]:
    """Return a design category and an auditable classification basis."""
    attr_candidates = _attribute_candidates(attr_categories)
    catalog_candidates = catalog_categories(source_catalogs)

    agreement = attr_candidates & catalog_candidates
    if len(agreement) == 1:
        return agreement.pop(), "时间点类别与辞典目录一致"
    if len(attr_candidates) == 1:
        return attr_candidates.pop(), "时间点类别"
    if len(catalog_candidates) == 1:
        return catalog_candidates.pop(), "辞典目录"

    # Cross-chapter entities often combine a central predecessor or supervisor
    # with one more specific institutional setting. Do not let the broad
    # central bucket absorb that explicit non-central evidence.
    non_central = catalog_candidates - {"中央机构"}
    if len(non_central) == 1:
        return non_central.pop(), "跨编辞典目录（采用具体非中央类别）"

    candidates = agreement or attr_candidates or catalog_candidates
    for category in _NON_CENTRAL_PRIORITY:
        if category in candidates:
            return category, "多重分类证据（按具体类别优先级）"
    if "中央机构" in candidates:
        return "中央机构", "中央机构明确证据"
    return None, "缺少可判定的分类证据"
