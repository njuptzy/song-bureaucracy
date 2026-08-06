"""Classify institutions into the five categories used by the design visualization."""

from collections.abc import Iterable


CATEGORY_NAMES = (
    "内廷机构",
    "中央机构",
    "路级机构",
    "州县机构",
    "军队机构",
)

CENTRAL_GROUP_NAMES = (
    "宰辅与决策中枢",
    "三省六部与馆阁",
    "礼仪宗室与宫廷事务",
    "财赋农政与马政",
    "五监与工程教育",
    "司法监察",
    "寺监制度统称",
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


def classify_central_group(
    title: str, attr_categories: Iterable[str], source_catalogs: Iterable[str]
) -> tuple[str | None, str]:
    """Classify a central institution by the dictionary's institutional system."""
    catalogs = " ".join(item for item in source_catalogs if item)
    attrs = " ".join(item for item in attr_categories if item)

    formal_systems = {
        "礼仪宗室与宫廷事务": {"太常寺", "宗正寺", "光禄寺", "卫尉寺", "鸿胪寺"},
        "财赋农政与马政": {"太仆寺", "司农寺", "太府寺"},
        "五监与工程教育": {"秘书监", "国子监", "少府监", "军器监", "将作监", "都水监"},
        "司法监察": {"大理寺"},
        "寺监制度统称": {"九寺五监", "九寺三监", "七寺"},
    }
    for group, titles in formal_systems.items():
        if title in titles:
            basis = "寺监制度统称" if group == "寺监制度统称" else "正式寺监制度归属"
            return group, basis

    if "第六编 司法、监察机构类" in catalogs or any(
        marker in attrs for marker in ("司法机构", "监察机构", "谏官机构")
    ):
        return "司法监察", "辞典司法监察编目或明确类别"

    if (
        "第四编 元丰正名后中枢机构类之一" in catalogs
        or "殿阁学士与三馆秘阁门" in catalogs
    ):
        return "三省六部与馆阁", "辞典三省六部或馆阁编目"

    if "第五编" in catalogs:
        section_groups = {
            "礼仪宗室与宫廷事务": (
                "二、太常寺门",
                "三、宗正寺大宗正司门",
                "四、光禄寺门",
                "五、卫尉寺门",
                "七、鸿胪寺门",
            ),
            "财赋农政与马政": ("六、太仆寺门", "八、司农寺门", "九、太府寺门"),
            "五监与工程教育": (
                "十、五监、国子监门",
                "十一、少府监门",
                "十二、军器监门",
                "十三、将作监门",
                "十四、都水监门",
            ),
        }
        for group, sections in section_groups.items():
            if any(section in catalogs for section in sections):
                return group, "辞典寺监分门编目"

        if "一、总九寺五监门" in catalogs:
            if "机构统称" in attrs:
                return "寺监制度统称", "辞典寺监总类与统称类别"
            if any(marker in attrs for marker in ("司法", "大理寺")):
                return "司法监察", "寺监总类中的司法职能"
            if any(marker in attrs for marker in ("财政", "财赋", "农政", "马政")):
                return "财赋农政与马政", "寺监总类中的财赋农马职能"
            if any(marker in attrs for marker in ("教育", "营造", "军器", "水利", "河渠")):
                return "五监与工程教育", "寺监总类中的教育工程职能"
            if any(
                marker in attrs
                for marker in ("礼制", "礼乐", "宗室", "宾客礼仪", "宫廷", "寺监机构")
            ):
                return "礼仪宗室与宫廷事务", "寺监总类中的礼仪宫廷职能"

    if "第二编" in catalogs or "第三编" in catalogs:
        return "宰辅与决策中枢", "辞典宰执或北宋前期中枢编目"
    return None, "缺少中央制度分组证据"
