#!/usr/bin/env python3
"""辞典正文 OCR 切分为条目表（一次性可重复执行脚本）。

用法: python3 split_chapters_2t4.py [编组]
  编组: 2t4（第二至四编，默认）/ 5t7（第五至七编）/ 11t12（第十一至十二编）
  各编组的章节、OCR 文件、目录边界、输出文件名见下方 PROFILES。

方法照 8-10 编（ocr2json.ipynb + json2table.ipynb），并针对 2-4 编 OCR
与目录的实际情况做了以下有日志的增强：

  1. 页码校验：从 MinerU discarded_blocks 的 page_number 块自动推断
     page_idx -> 书页码 的偏移（众数），打印校验失败页。
  2. title 块参与切分：2-4 编大量条目头被 MinerU 标成 title（8-10 编几乎
     都是 text），因此 title 与 text 块同样做前缀匹配；整块等于目录
     h1/h2/h3 标题的跳过。
  3. 匹配归一化：仅用于匹配（不改输出文本）——全角括号（）转半角，
     条目名匹配允许跨过空格/全角空格（OCR 常在条目头插空格，如
     "吏部尚书左选 甲库案"），跨空格的匹配会打印日志。
  4. 标点闸门：名字/属性匹配后余文以 "。，、：；）》" 等开头的是行内提及
     （如 "检匣。太宗雍熙元年..."），不是条目头，按普通正文处理。
  5. 截断标题头补全：title 块是某目录主条目的唯一更长前缀时（如
     "同中书门下平章事、集贤殿大学"），补全为完整条目名，并从下一块开头
     剥掉剩余字符；剥离失败则放弃补全并记日志。
  6. surname（别称）处理：与 8-10 编一致，别称默认不进条目 Trie（并入主
     条目正文）；若别称（长度>=2）在正文独立成段且有实质内容——title 块
     整块/开头为别称，或 text 块以 "别称 xx名。" 定义式开头——拆为独立条
     目标 "_from_surname": true（即 8-10 编 DB 对"小长"条的人工做法；
     2-4 编目录 table1/table2 把枢密院诸房、三馆秘阁等真实条目全标成了
     surname，必须靠此机制找回）。
  7. 交叉验证：切分序列与目录主条目序列 difflib 对齐；对不齐的缺口内做
     模糊配对（等长且仅差 1 字，或相似度>=0.6，且页码差<=3），配上的记
     "fuzzy"（保留正文名字，meta 记录目录名）；目录有而实在配不上的补占
     位（text 为空 + "_placeholder": true）。
  8. 属性名归一化表 attribute_dict 从 json2table.ipynb 原样复用；输出条目
     保留原始属性键（与 第八至十编-表格化结果.json 一致），未覆盖的属性
     名在报告中列出。

输出（文件名随编组变化）：
  data/ocr-results/<编组名>-表格化结果.json       （条目表，格式同 8-10 编）
  data/ocr-results/<编组名>-表格化结果.meta.json  （逐条元数据：页码/编目/状态）
"""

import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OCR_DIR = ROOT / "data" / "ocr-results"
CATALOG_FILE = OCR_DIR / "职官条目分类目录-catalog-refined.json"

# 编组配置：章节与 OCR 文件、目录切片右边界（不含；None=切到目录末尾）、
# 输出文件名前缀、目录修正开关
PROFILES = {
    "2t4": {
        "chapters": [
            {"h1": "第二编 宰执官类",
             "file": "MinerU_02-宋代官制辞典-第二编__20260409092437.json"},
            {"h1": "第三编 北宋前期中枢机构类",
             "file": "MinerU_03-宋代官制辞典-第三编__20260409093138.json"},
            {"h1": "第四编 元丰正名后中枢机构类之一",
             "file": "MinerU_04-宋代官制辞典-第四编__20260409103523.json"},
        ],
        "next_h1": "第五编 元丰正名后中枢机构类之二",
        "out": "第二至四编",
        # "一、宰相门宰相"：目录 OCR 把 h2 "一、宰相门" 与首个主条目 "宰相"
        # 粘连，导致主条目被错切成 name="宰" + surname="相"。修正为
        # h2="一、宰相门" + name="宰相"，并删掉随之多出的 surname "相"(p83)。
        "fix_xiangmen": True,
        "drop_surnames": {
            ("第二编 宰执官类", "相", "83"),
            ("第二编 宰执官类", "昭文馆大学士", "85"),
        },
        # 正文粘连修补：把误切出的伪条目并回真正的条目（并保留伪条目名本身，
        # 它是被拆走的正文文字）。每项: bogus 名+页码 -> into 条目名。
        "joins": [
            {"bogus": "宰相", "page": "88", "into": "少宰兼中书侍郎",
             "reason": "少宰兼中书侍郎的正文换行处被拆：'宰相'被误切为独立条目，"
                       "其 text（'名。政和二年九月改尚书右仆射为少宰……'）与"
                       "简称与别名（少宰、亚鼎司）实属少宰兼中书侍郎"},
            {"bogus": "堂后官", "page": "96", "into": "制敕院孔目房",
             "status": "from_surname",
             "reason": "孔目房编制段在块边界被拆：'堂后官一人总其事。下设主事、录事、"
                       "守当官等吏职……'是制敕院孔目房的编制内容（对照吏房/户房各房"
                       "均如此），别称匹配误拆为独立条目"},
            {"bogus": "同知院", "page": "106", "into": "同知太常礼院",
             "status": "from_surname",
             "reason": "同知太常礼院简称引文跨块断开：'国朝同知院四员……'的后半句"
                       "被别称匹配误拆为独立条目，实属同知太常礼院的简称字段"},
            {"bogus": "判官", "page": "133", "into": "权三司度支判官",
             "status": "from_surname",
             "reason": "权三司度支判官标题在‘判官’二字处被别称匹配误拆；"
                       "‘缺，暂代者带权字’及权度支判官简称均属本条"},
            {"bogus": "判官", "page": "133", "into": "权三司户部判官",
             "status": "from_surname",
             "reason": "权三司户部判官标题在‘判官’二字处被别称匹配误拆；"
                       "‘缺，暂代任者带权字’及其简称均属本条"},
        ],
        "embedded_splits": [
            {"source": "都大提举在京诸司库务司", "target": "都大提举在京诸司库务",
             "page": "111", "field": "简称", "marker": "都大提举在京诸司库务 差遣名。",
             "reason": "主管官标题仅比机构名少末字‘司’，被前条简称字段前缀匹配吞入；按正文独立标题拆回"},
            {"source": "枢密院承旨司", "target": "枢密院承旨",
             "page": "116", "field": "简称", "marker": "枢密院承旨 差遣名。",
             "reason": "承旨条标题被承旨司前条的简称字段吞入；按正文独立标题拆回"},
            {"source": "大程官营", "target": "大程官",
             "page": "123", "field": "text", "marker": "大程官 给使名。",
             "move_fields": ["职源"],
             "reason": "大程官标题及其职源、职掌被并入前条大程官营；原始 OCR 与目录均显示为两个独立条目"},
            {"source": "权三司使公事", "target": "权三司使",
             "page": "128", "field": "简称", "marker": "权三司使 差遣官名。",
             "reason": "权三司使标题及正文被前条权三司使公事的简称字段吞入；目录另列本条，正文也有独立定义与庆历三年始置事实"},
        ],
        # 目录本身的 OCR 错字。只改用于条目识别的标题，不改正文引文。
        "catalog_renames": [
            {"from": "吏部尚书钰", "to": "吏部尚书铨", "page": "100",
             "reason": "目录把官署名末字‘铨’误识为‘钰’；正文条目头与下条合称均作‘吏部尚书铨’"},
            {"from": "流外锥", "to": "流外钰", "canonical": "流外铨", "page": "102",
             "reason": "目录误作‘流外锥’，正文条目头误作‘流外钰’；先按正文 OCR 匹配，"
                       "输出标题据官名与正文‘小铨’说明统一为‘流外铨’"},
            {"from": "钰曹四选", "to": "铨曹四选", "page": "102",
             "reason": "目录把‘铨曹四选’误识为‘钰曹四选’，正文条目头作‘铨曹四选’"},
            {"from": "兵部、吏部、司封、司勋宣告院", "to": "兵部、吏部、司封、司勋官告院", "page": "104",
             "reason": "目录把‘官告院’误识为‘宣告院’，正文条目头作‘官告院’"},
            {"from": "判兵部、吏部、司封、司勋官告院事", "to": "判兵部、吏部、司封、司勋宣告院事",
             "canonical": "判兵部、吏部、司封、司勋官告院事", "page": "105",
             "reason": "正文条目头把‘官告院’误识为‘宣告院’；按 OCR 形态切分后恢复规范官名"},
            {"from": "评定编敕所", "to": "详定编敕所", "page": "106",
             "reason": "目录把正文官署名‘详定编敕所’误识为‘评定编敕所’"},
            {"from": "评定一司敕令所", "to": "详定一司敕令所", "page": "106",
             "reason": "目录把正文官署名‘详定一司敕令所’误识为‘评定一司敕令所’"},
            {"from": "评定重修敕令所", "to": "详定重修敕令所", "page": "107",
             "reason": "目录把正文官署名‘详定重修敕令所’误识为‘评定重修敕令所’"},
            {"from": "评定敕令局", "to": "详定敕令局", "page": "107",
             "reason": "目录把正文官署名‘详定敕令局’误识为‘评定敕令局’"},
            {"from": "同提举评定一司敕令", "to": "同提举详定一司敕令", "page": "107",
             "reason": "目录把正文差遣名中的‘详定’误识为‘评定’"},
            {"from": "评定一司敕令", "to": "详定一司敕令", "page": "107",
             "reason": "目录把正文差遣名‘详定一司敕令’误识为‘评定一司敕令’"},
            {"from": "同评定一司敕令", "to": "同详定一司敕令", "page": "107",
             "reason": "目录把正文差遣名‘同详定一司敕令’误识为‘同评定一司敕令’"},
            {"from": "评定一司敕令所删定官", "to": "详定一司敕令所删定官", "page": "107",
             "reason": "目录把正文差遣名中的‘详定’误识为‘评定’"},
            {"from": "评定一司敕令所承受", "to": "详定一司敕令所承受", "page": "107",
             "reason": "目录把正文差遣名中的‘详定’误识为‘评定’"},
            {"from": "评定一司敕令所都大提举诸司", "to": "评定一司敕令所都大提举诸司",
             "canonical": "详定一司敕令所都大提举诸司", "page": "108",
             "reason": "正文与目录均把官署名首字‘详’误识为‘评’，按同段‘详定一司敕令所’恢复规范名"},
            {"from": "评定一司敕令所都大提举诸司官", "to": "评定一司敕令所都大提举诸司官",
             "canonical": "详定一司敕令所都大提举诸司官", "page": "108",
             "reason": "正文与目录均把差遣名首字‘详’误识为‘评’，按同段‘详定一司敕令所’恢复规范名"},
            {"from": "同看详编修中书条例", "to": "同着详编修中书条例",
             "canonical": "同看详编修中书条例", "page": "109",
             "reason": "正文条目头把‘看详’误识为‘着详’；按目录规范名恢复"},
            {"from": "评定官制所", "to": "详定官制所", "page": "109",
             "reason": "目录把正文官署名‘详定官制所’误识为‘评定官制所’"},
        ],
    },
    "5t7": {
        "chapters": [
            {"h1": "第五编 元丰正名后中枢机构类之二",
             "file": "MinerU_05-宋代官制辞典-第五编__20260725190000.json"},
            {"h1": "第六编 司法、监察机构类",
             "file": "MinerU_06-宋代官制辞典-第六编__20260725190000.json"},
            {"h1": "第七编 皇宫京城禁卫侍奉机构类",
             "file": "MinerU_07-宋代官制辞典-第七编__20260725190000.json"},
        ],
        "next_h1": "第八编 军事统率机构与地方治安机构类",
        "out": "第五至七编",
        "fix_xiangmen": False,
        "drop_surnames": set(),
    },
    "11t12": {
        "chapters": [
            {"h1": "第十一编 阶官类",
             "file": "MinerU_11-宋代官制辞典-第十一编__20260725190000.json"},
            {"h1": "第十二编 爵、勋、功臣、检校、宪衔、祠禄官类",
             "file": "MinerU_12-宋代官制辞典-第十二编__20260725190000.json"},
        ],
        "next_h1": None,
        "out": "第十一至十二编",
        "fix_xiangmen": False,
        "drop_surnames": set(),
    },
}

PROFILE_NAME = sys.argv[1] if len(sys.argv) > 1 else "2t4"
if PROFILE_NAME not in PROFILES:
    raise SystemExit(f"未知编组 {PROFILE_NAME!r}，可选: {sorted(PROFILES)}")
PROFILE = PROFILES[PROFILE_NAME]
CHAPTERS = PROFILE["chapters"]
NEXT_H1 = PROFILE["next_h1"]
OUT_JSON = OCR_DIR / f"{PROFILE['out']}-表格化结果.json"
OUT_META = OCR_DIR / f"{PROFILE['out']}-表格化结果.meta.json"

# 属性名归一化表：从 json2table.ipynb 原样复用（8-10 编版本，41 个键）
ATTRIBUTE_DICT = {
    "简称与别名": ["简称"],
    "简称与别称": ["简称"],
    "职源、沿革、职掌、品位": ["职源", "职掌", "官品"],
    "职源与沿革、职掌、官品": ["职源", "职掌", "官品"],
    "职源与沿革、职掌": ["职源", "职掌"],
    "官品、编制、简称与别名": ["官品", "编制", "简称"],
    "职源、沿革、编制": ["职源", "编制"],
    "职掌与沿革": ["职掌", "职源"],
    "职源、职掌、编制": ["职源", "职掌", "编制"],
    "职掌、官品、编制": ["职掌", "官品", "编制"],
    "职源、职掌": ["职源", "职掌"],
    "职掌、品位": ["职掌", "官品"],
    "编制、职能": ["职掌", "编制"],
    "编制与品位": ["编制", "官品"],
    "沿革与职掌": ["职源", "职掌"],
    "省称与别名": ["简称"],
    "简称与追改": ["简称"],
    "简称与旧称": ["简称"],
    "职源与沿革": ["职源"],
    "职源与改革": ["职源"],
    "追称": ["简称"],
    "职掌": ["职掌"],
    "职能": ["职掌"],
    "位遇": ["官品"],
    "序位": ["官品"],
    "地位": ["官品"],
    "品秩": ["官品"],
    "编制": ["编制"],
    "职源": ["职源"],
    "简称": ["简称"],
    "通称": ["简称"],
    "省称": ["简称"],
    "别名": ["简称"],
    "别称": ["简称"],
    "合称": ["简称"],
    "品阶": ["官品"],
    "官品": ["官品"],
    "品位": ["官品"],
    "班位": ["官品"],
    "沿革": ["职源"],
    "泛称": ["简称"],
}

# 匹配后余文以这些字符开头 => 行内提及，不是条目头/属性头
NOT_HEAD_CHARS = "。，、：；）》」』”’!！?？ "
# surname 独立成段的实质内容门槛：余文 "。" 出现在此长度内
SURNAME_DEF_WINDOW = 30

# 目录 OCR 缺陷修正集合来自 PROFILE["drop_surnames"]（逐编组配置，运行时打印日志）
CATALOG_FIX_DROP_SURNAMES = PROFILE["drop_surnames"]


def norm_heading(text):
    """标题归一化：去空白，用于标题块与目录标题的比对。"""
    return re.sub(r"[\s　]+", "", text)


def norm_match(text):
    """匹配用归一化（1:1 字符替换，不改变长度与偏移）：全角括号转半角；
    𬮤->阁：目录 OCR 把"阁"识别为生僻字"𬮤"（第七编阁门系列，正文 OCR 为"阁"）。"""
    return text.replace("（", "(").replace("）", ")").replace("𬮤", "阁")


def get_block_text(block):
    return "".join(
        span["content"] for line in block["lines"] for span in line["spans"]
    )


# ---------------------------------------------------------------- Trie ----
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.keyword = None


class TrieTree:
    """最长前缀匹配 Trie（同 json2table.ipynb），支持跨空格匹配。"""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, keyword):
        node = self.root
        for char in keyword:
            node = node.children.setdefault(char, TrieNode())
        node.is_end = True
        node.keyword = keyword

    def start_with(self, text, skip_spaces=False):
        """返回 (keyword, consumed_len)；无匹配返回 (None, 0)。

        skip_spaces=True 时匹配路径上跳过 text 中的空格/全角空格
        （OCR 条目头内插空格的情形），consumed_len 含被跳过的空格。
        """
        if not text:
            return None, 0
        node = self.root
        matched = None
        matched_len = 0
        i = 0
        while i < len(text):
            char = text[i]
            if skip_spaces and char in " 　" and node is not self.root:
                i += 1
                continue
            if char not in node.children:
                break
            node = node.children[char]
            i += 1
            if node.is_end:
                matched = node.keyword
                matched_len = i
        return matched, matched_len

    def build_from_set(self, keyword_set):
        for keyword in sorted(keyword_set, key=len, reverse=True):
            self.insert(keyword)


# ------------------------------------------------------------- 目录处理 ----
def load_catalog():
    """切出 2-4 编目录记录，应用缺陷修正，返回 {h1: {...}} 与修正日志。"""
    with open(CATALOG_FILE, encoding="utf-8") as f:
        records = json.load(f)

    h1_texts = [c["h1"] for c in CHAPTERS]
    start = next(i for i, r in enumerate(records) if r["text"] == h1_texts[0])
    # 右边界：NEXT_H1 所在位置；NEXT_H1 为 None 时切到目录末尾。
    # 两种情况下都在遇到下一个 catalog 级记录（如 "Ⅱ.职官术语与典故目录"）
    # 时截断——那是另一份目录，不属于本编组。
    end = len(records)
    for i in range(start + 1, len(records)):
        r = records[i]
        if r["type"] == "catalog" or (NEXT_H1 and r["text"] == NEXT_H1):
            end = i
            break
    records = records[start:end]

    fix_log = []
    fixed = []
    cur_h1 = None
    seen_tpm = 0  # 第二编中 name='同中书门下平章事' 的出现次数
    for r in records:
        r = dict(r)
        if r["type"] == "h1":
            cur_h1 = r["text"]
        rename = next(
            (item for item in PROFILE.get("catalog_renames", [])
             if r["type"] == "name" and r["text"] == item["from"]
             and str(r.get("page")) == item["page"]),
            None,
        )
        if rename:
            old = r["text"]
            r["text"] = rename["to"]
            fix_log.append(
                f"name '{old}'(p{r.get('page')}) -> '{r['text']}'（{rename['reason']}）"
            )
        if (
            PROFILE.get("fix_xiangmen")
            and r["type"] == "h2"
            and r["text"] == "一、宰相门宰相"
        ):
            r["text"] = "一、宰相门"
            fix_log.append("h2 '一、宰相门宰相' -> '一、宰相门'（目录 OCR 粘连首条目名）")
        elif (
            PROFILE.get("fix_xiangmen")
            and r["type"] == "name"
            and r["text"] == "宰"
            and r.get("page") == "83"
        ):
            r["text"] = "宰相"
            fix_log.append("name '宰'(p83) -> '宰相'（同上，粘连拆回）")
        elif (
            PROFILE.get("fix_xiangmen")
            and cur_h1 == "第二编 宰执官类"
            and r["type"] == "name"
            and r["text"] == "同中书门下平章事"
            and str(r.get("page")) == "85"
        ):
            seen_tpm += 1
            if seen_tpm == 2:
                # 目录 OCR 把长条目名 "同中书门下平章事、昭文馆大学士" 折行拆断：
                # 第一行成了伪主条目（同名重复），第二行 "昭文馆大学士" 成了它的
                # 伪别称（下方 drop_surnames 删除）。正文 p85 确有此独立条目。
                r["text"] = "同中书门下平章事、昭文馆大学士"
                fix_log.append(
                    "name '同中书门下平章事'(p85, 第2次) -> '同中书门下平章事、昭文馆大学士'"
                    "（目录 OCR 折行拆断长条目名）"
                )
        elif (
            r["type"] == "surname"
            and (cur_h1, r["text"], str(r.get("page"))) in CATALOG_FIX_DROP_SURNAMES
        ):
            fix_log.append(
                f"删除 surname '{r['text']}'(p{r.get('page')})（'宰相' 粘连产生的伪别称）"
            )
            continue
        fixed.append(r)
    records = fixed

    chapters = {}
    cur = None
    for r in records:
        if r["type"] == "h1":
            cur = {
                "h1": r["text"],
                "names": [],       # [{text,page,h2,h3}] 主条目（有序）
                "surnames": [],    # [{text,page,h2,h3}] 别称
                "headings": set(),  # 归一化后的 h1/h2/h3 标题
            }
            chapters[r["text"]] = cur
            cur["headings"].add(norm_heading(r["text"]))
            h2 = h3 = None
        elif cur is None:
            continue
        elif r["type"] == "h2":
            h2, h3 = r["text"], None
            cur["headings"].add(norm_heading(r["text"]))
        elif r["type"] == "h3":
            h3 = r["text"]
            cur["headings"].add(norm_heading(r["text"]))
        elif r["type"] == "name":
            cur["names"].append(
                {"text": r["text"], "page": str(r.get("page", "")),
                 "h2": h2, "h3": h3}
            )
        elif r["type"] == "surname":
            cur["surnames"].append(
                {"text": r["text"], "page": str(r.get("page", "")),
                 "h2": h2, "h3": h3}
            )
    return chapters, fix_log


# ------------------------------------------------------------- 页码校验 ----
def extract_pages(chapter):
    """提取一章的逐页块流，自动推断页码偏移并校验。返回 (blocks, report)。"""
    with open(OCR_DIR / chapter["file"], encoding="utf-8") as f:
        ocr = json.load(f)
    pdf_info = ocr["pdf_info"]

    page_numbers = []
    for page in pdf_info:
        pn = None
        for db in page.get("discarded_blocks", []):
            if db["type"] == "page_number":
                pn = get_block_text(db).strip()
        page_numbers.append((page["page_idx"], pn))

    diffs = Counter()
    for page_idx, pn in page_numbers:
        if pn and pn.isdigit():
            diffs[int(pn) - page_idx] += 1
    if not diffs:
        raise RuntimeError(f"{chapter['h1']}: 无法从 page_number 块推断页码偏移")
    offset, _ = diffs.most_common(1)[0]

    failures = []
    for page_idx, pn in page_numbers:
        expect = str(page_idx + offset)
        if pn != expect:
            failures.append((page_idx, pn, expect))

    blocks = []
    unexpected_types = Counter()
    for page in pdf_info:
        page_no = str(page["page_idx"] + offset)
        for pb in page["para_blocks"]:
            if pb["type"] not in ("text", "title"):
                unexpected_types[pb["type"]] += 1
                continue
            text = get_block_text(pb)
            if text.strip():
                blocks.append({"page": page_no, "type": pb["type"], "text": text})
    report = {
        "pages": len(pdf_info),
        "offset": offset,
        "offset_votes": dict(diffs),
        "failures": failures,
        "unexpected_block_types": dict(unexpected_types),
        "n_blocks": len(blocks),
    }
    return blocks, report


# ------------------------------------------------------------- 正文切分 ----
DEFINITION_RE = re.compile(r"^[^。]{0,12}名[。，,]")  # "xx名。"/"xx名，" 定义式开头


def looks_like_surname_entry(rest):
    """surname 后余文是否像实质条目内容（定义式开头或短句即句号）。"""
    rest = rest.lstrip()
    if not rest or rest[0] in NOT_HEAD_CHARS:
        return False
    if DEFINITION_RE.match(rest):
        return True
    end = rest.find("。")
    return 0 < end <= SURNAME_DEF_WINDOW


def split_chapter(chapter_meta, blocks):
    """把一章的块流切成条目。返回 (entries, split_report)。"""
    names = chapter_meta["names"]
    name_set = {n["text"] for n in names}
    surname_set = {s["text"] for s in chapter_meta["surnames"]}
    headings = chapter_meta["headings"]

    trie_name = TrieTree()
    trie_name.build_from_set({norm_match(n) for n in name_set})
    trie_attr = TrieTree()
    trie_attr.build_from_set({norm_match(a) for a in ATTRIBUTE_DICT})
    trie_surname = TrieTree()
    # 与主条目同名的别称、1 字别称不做独立成段判断
    trie_surname.build_from_set(
        {norm_match(s) for s in surname_set - name_set if len(s) >= 2}
    )

    report = {
        "space_skip_matches": [],
        "truncated_heads": [],
        "strip_failures": [],
        "surname_entries": [],
        "punct_gate_rejects": [],
        "prefix_body_rejects": [],
        "body_absorbed_heads": [],
        "suspicious_title_blocks": [],
        "leading_orphan_texts": [],
    }

    stream = []
    pending_strip = None  # 截断标题头需从下一块开头剥掉的字符
    pending_body = False  # 上一条目头独占一块、尚无内容
    last_name = None  # 最近切出的条目名，用于识别"正文以父名开头"的误切

    def emit_name(name, consumed, page, from_surname=False):
        nonlocal last_name, pending_body
        last_name = name
        rest = text[consumed:]
        # 条目头独占一块（无正文）时，下一块优先视为其正文
        pending_body = not rest.strip()
        stream.append(
            {"type": "bureaucracy_name", "text": name, "page": page,
             "from_surname": from_surname}
        )
        if rest.strip():
            stream.append({"type": "text", "text": rest, "page": page})

    for idx, blk in enumerate(blocks):
        text = blk["text"]
        mtext = norm_match(text)
        # 1) 标题块（h1/h2/h3），整块精确匹配才跳过
        if norm_heading(text) in headings:
            continue
        # 2) 截断标题头的续块：剥掉名字剩余字符
        if pending_strip:
            if mtext.startswith(pending_strip):
                text = text[len(pending_strip):].lstrip()
                mtext = norm_match(text)
                pending_strip = None
                if not text:
                    continue
            else:
                report["strip_failures"].append((blk["page"], text[:60]))
                pending_strip = None

        # 上一条目头独占一块且还没有内容：本 text 块是其正文的开头，
        # 即使它以其他条目名/别称开头（如 "门下省左司谏、……通称。"）
        # 也不新开条目。title 块与属性行不受影响，仍走正常匹配。
        absorb_as_body = pending_body and blk["type"] == "text"
        pending_body = False

        b, blen = trie_name.start_with(mtext, skip_spaces=True)
        s, slen = trie_surname.start_with(mtext)
        a, alen = trie_attr.start_with(mtext)
        if absorb_as_body and (b or s):
            # 属性行（如 "职源 ……"）仍可正常识别；否则抑制名字匹配，
            # 让本块落入正文
            name_like = b if (b and (not s or len(b) >= len(s))) else s
            if not a or len(name_like) > len(a):
                report["body_absorbed_heads"].append(
                    (blk["page"], name_like, text[:40])
                )
                b = s = None

        # 3) 截断标题头补全：title 块是某主条目的唯一更长前缀
        #    （补全必须长于普通前缀匹配，且下一块能以剩余字符开头）
        if blk["type"] == "title":
            cands = [n for n in name_set
                     if norm_match(n).startswith(mtext) and len(n) > len(mtext)]
            longer = [n for n in cands if b is None or len(n) > len(b)]
            if len(longer) == 1:
                full = longer[0]
                rest_chars = norm_match(full)[len(mtext):]
                nxt = blocks[idx + 1]["text"] if idx + 1 < len(blocks) else ""
                if norm_match(nxt).startswith(rest_chars):
                    report["truncated_heads"].append((text, full, blk["page"]))
                    stream.append({"type": "bureaucracy_name", "text": full,
                                   "page": blk["page"], "from_surname": False})
                    pending_strip = rest_chars
                    # 补全的头同样独占一块、尚无内容：下一块（剥掉剩余字符后）
                    # 是其正文，即使以其他条目名开头也不新开条目
                    last_name = full
                    pending_body = True
                    continue

        # 4) 名字/别称匹配：取更长者；等长优先主条目
        use = None
        if b and (not s or len(b) >= len(s)):
            use = ("name", b, blen)
        elif s:
            use = ("surname", s, slen)
        if use and use[0] == "name":
            kind, kw, consumed = use
            if " " in text[:consumed] or "　" in text[:consumed]:
                report["space_skip_matches"].append((blk["page"], kw, text[:50]))
            rest = text[consumed:]
            if rest[:1] and rest[0] in NOT_HEAD_CHARS and rest[0] not in " 　":
                # 行内提及（如 "检匣。太宗..."），不是条目头
                report["punct_gate_rejects"].append((blk["page"], kw, text[:40]))
            elif (
                last_name
                and len(kw) < len(last_name)
                and last_name.startswith(kw)
            ):
                # 正文以当前条目名的前缀开头（如条目"枢密院户房"的正文
                # 以"枢密院办事机构之一……"开头），是父名提及，不是新条目头
                report["prefix_body_rejects"].append(
                    (blk["page"], kw, last_name, text[:40])
                )
            else:
                emit_name(kw, consumed, blk["page"])
                continue
        elif use and use[0] == "surname":
            kind, kw, consumed = use
            rest = text[consumed:]
            # 别称独立成段：title 块，或 text 块余文像实质定义
            if blk["type"] == "title" or looks_like_surname_entry(rest):
                report["surname_entries"].append((kw, blk["page"], text[:50]))
                emit_name(kw, consumed, blk["page"], from_surname=True)
                continue
            # 否则按普通正文落入前一条目

        # 5) 属性前缀匹配
        if a:
            rest = text[alen:]
            if rest[:1] and rest[0] in NOT_HEAD_CHARS and rest[0] not in " 　":
                pass  # 如 "品位。" 之类行内提及，按正文处理
            else:
                stream.append({"type": "attribute", "text": a, "page": blk["page"]})
                if rest.strip():
                    stream.append({"type": "text", "text": rest, "page": blk["page"]})
                continue

        # 6) 疑似标题但不在目录标题集合（OCR 噪声的 门 标题等），记日志
        if blk["type"] == "title" and re.match(
            r"^(第.{1,3}编|[一二三四五六七八九十]+、|[\[（]?附)", text.strip()
        ):
            report["suspicious_title_blocks"].append((blk["page"], text[:60]))
        stream.append({"type": "text", "text": text, "page": blk["page"]})

    # 第二遍：合并成条目（同 json2table.ipynb）
    entries = []
    item = None
    current_attribute = None
    for rec in stream:
        if rec["type"] == "bureaucracy_name":
            item = {
                "name": rec["text"],
                "_page": rec["page"],
                "_from_surname": rec.get("from_surname", False),
                "texts": [],
            }
            entries.append(item)
            current_attribute = "texts"
        elif rec["type"] == "attribute":
            if item is None:
                report["leading_orphan_texts"].append("[attribute] " + rec["text"])
                continue
            current_attribute = rec["text"]
            item.setdefault(current_attribute, "")
        else:
            if item is None:
                report["leading_orphan_texts"].append(rec["text"][:60])
                continue
            if current_attribute == "texts":
                item["texts"].append(rec["text"].strip())
            else:
                item[current_attribute] += rec["text"].strip()

    for item in entries:
        item["text"] = "".join(item["texts"])
        del item["texts"]
    return entries, report


# ------------------------------------------------------------- 交叉验证 ----
def fuzzy_score(cat_name, split_name):
    """目录名与切出名的模糊相似度：等长仅差 1 字给 0.9，否则用 ratio。"""
    a, b = norm_match(cat_name), norm_match(split_name)
    if a == b:
        return 1.0
    if len(a) == len(b):
        diff = sum(1 for x, y in zip(a, b) if x != y)
        if diff == 1:
            return 0.9
    return SequenceMatcher(None, a, b).ratio()


def page_int(p):
    return int(p) if p and p.isdigit() else None


def align_and_validate(chapter_meta, entries):
    """目录主条目序列 vs 切分条目序列对齐 + 缺口模糊配对。

    返回 (final, report)；final 元素为 (entry|None, catalog_record|None, status)。
    """
    catalog = chapter_meta["names"]
    catalog_names = [n["text"] for n in catalog]
    split_names = [e["name"] for e in entries]

    sm = SequenceMatcher(a=catalog_names, b=split_names, autojunk=False)

    final = []
    report = {"missing": [], "extra": [], "fuzzy": [], "page_mismatch": []}

    def emit_entry(ent, cat, status):
        final.append((ent, cat, status))
        if cat is not None:
            cp, bp = page_int(cat["page"]), page_int(ent["_page"])
            if cp is not None and bp is not None and cp != bp:
                report["page_mismatch"].append((ent["name"], cat["page"], ent["_page"]))

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                ent, cat = entries[j1 + k], catalog[i1 + k]
                emit_entry(ent, cat, "from_surname" if ent["_from_surname"] else "ok")
            continue

        # 缺口：先做模糊配对（目录 OCR 噪声 vs 正文 OCR 噪声）
        cats = list(range(i1, i2))
        splits = list(range(j1, j2))
        pairs = []
        for ci in cats:
            cp = page_int(catalog[ci]["page"])
            for si in splits:
                ent = entries[si]
                bp = page_int(ent["_page"])
                if cp is not None and bp is not None and abs(cp - bp) > 3:
                    continue
                score = fuzzy_score(catalog[ci]["text"], ent["name"])
                if score >= 0.6:
                    pairs.append((score, ci, si))
        pairs.sort(reverse=True)
        used_c, used_s = set(), set()
        for score, ci, si in pairs:
            if ci in used_c or si in used_s:
                continue
            used_c.add(ci)
            used_s.add(si)
            ent, cat = entries[si], catalog[ci]
            report["fuzzy"].append((cat["text"], ent["name"], cat["page"], round(score, 2)))
            emit_entry(ent, cat, "fuzzy")

        # 剩余：目录侧补占位，正文侧保留为多出条目
        for ci in cats:
            if ci in used_c:
                continue
            cat = catalog[ci]
            report["missing"].append((cat["text"], cat["page"], cat["h2"]))
            final.append((None, cat, "placeholder"))
        for si in splits:
            if si in used_s:
                continue
            ent = entries[si]
            status = "from_surname" if ent["_from_surname"] else "not_in_catalog"
            report["extra"].append((ent["name"], ent["_page"], status))
            final.append((ent, None, status))

    return final, report


# ---------------------------------------------------------------- 主流程 ----
def main():
    chapters_meta, fix_log = load_catalog()
    print("== 目录修正 ==")
    for line in fix_log:
        print("  " + line)

    all_entries = []
    all_meta = []
    uncovered_attrs = set()
    total_summary = []

    for ch in CHAPTERS:
        h1 = ch["h1"]
        meta = chapters_meta[h1]
        blocks, page_report = extract_pages(ch)
        print(f"\n== {h1} ==")
        print(f"  页数 {page_report['pages']}，推断页码偏移 +{page_report['offset']}"
              f"（投票 {page_report['offset_votes']}）")
        if page_report["failures"]:
            print(f"  页码校验失败 {len(page_report['failures'])} 页："
                  f"{page_report['failures'][:20]}")
        else:
            print("  页码校验全部通过")
        if page_report["unexpected_block_types"]:
            print(f"  非 text/title 块（已跳过）：{page_report['unexpected_block_types']}")

        entries, split_report = split_chapter(meta, blocks)
        n_sur = sum(1 for e in entries if e["_from_surname"])
        print(f"  正文块 {page_report['n_blocks']}，切出条目 {len(entries)}"
              f"（含别称独立成段 {n_sur}；目录主条目 {len(meta['names'])}，"
              f"别称 {len(meta['surnames'])}）")
        if split_report["space_skip_matches"]:
            print(f"  跨空格匹配 {len(split_report['space_skip_matches'])} 处：")
            for pg, kw, ctx in split_report["space_skip_matches"]:
                print(f"    p{pg}: {kw}  <- {ctx}")
        if split_report["truncated_heads"]:
            print(f"  截断标题头补全 {len(split_report['truncated_heads'])} 处：")
            for t, full, pg in split_report["truncated_heads"]:
                print(f"    p{pg}: '{t}' -> '{full}'")
        if split_report["strip_failures"]:
            print(f"  截断续块剥离失败 {len(split_report['strip_failures'])} 处："
                  f"{split_report['strip_failures'][:10]}")
        if split_report["punct_gate_rejects"]:
            print(f"  标点闸门拦截行内提及 {len(split_report['punct_gate_rejects'])} 处")
        if split_report["suspicious_title_blocks"]:
            print(f"  疑似标题块（未匹配目录标题，按正文处理）"
                  f"{len(split_report['suspicious_title_blocks'])} 处：")
            for pg, t in split_report["suspicious_title_blocks"]:
                print(f"    p{pg}: {t}")
        if split_report["leading_orphan_texts"]:
            print(f"  首个条目前的孤儿文本 {len(split_report['leading_orphan_texts'])} 块："
                  f"{split_report['leading_orphan_texts'][:5]}")

        final, val_report = align_and_validate(meta, entries)
        n_ph = sum(1 for _, _, s in final if s == "placeholder")
        print(f"  对齐结果：模糊配对 {len(val_report['fuzzy'])}，"
              f"目录缺失补占位 {n_ph}，多出条目 {len(val_report['extra'])}，"
              f"页码不一致 {len(val_report['page_mismatch'])}")
        for cname, bname, pg, score in val_report["fuzzy"]:
            print(f"    [模糊配对] 目录 '{cname}'(p{pg}) <-> 正文 '{bname}' ({score})")
        for name, pg, h2 in val_report["missing"]:
            print(f"    [缺失->占位] {name}（目录 p{pg}，{h2}）")
        for name, pg, status in val_report["extra"]:
            print(f"    [多出:{status}] {name}（正文 p{pg}）")
        for name, cp, bp in val_report["page_mismatch"]:
            print(f"    [页码不一致] {name}：目录 p{cp} vs 正文 p{bp}")

        for ent, cat, status in final:
            if status == "placeholder":
                out = {"name": cat["text"], "text": "", "_placeholder": True}
                m = {
                    "name": cat["text"],
                    "page": cat["page"],
                    "h1": h1, "h2": cat["h2"], "h3": cat["h3"],
                    "status": "placeholder",
                }
            else:
                out = {"name": ent["name"]}
                attrs = {k: v for k, v in ent.items()
                         if k not in ("name", "text", "_page", "_from_surname")}
                for k in attrs:
                    if k not in ATTRIBUTE_DICT:
                        uncovered_attrs.add(k)
                out.update(attrs)
                out["text"] = ent["text"]
                if status == "from_surname":
                    out["_from_surname"] = True
                elif status == "not_in_catalog":
                    out["_not_in_catalog"] = True
                m = {
                    "name": ent["name"],
                    "page": cat["page"] if cat is not None else ent["_page"],
                    "body_page": ent["_page"],
                    "h1": h1,
                    "h2": cat["h2"] if cat is not None else None,
                    "h3": cat["h3"] if cat is not None else None,
                    "status": status,
                }
                if status == "fuzzy":
                    m["catalog_name"] = cat["text"]
                    out["_catalog_name"] = cat["text"]
            all_entries.append(out)
            all_meta.append(m)
        total_summary.append((h1, len(meta["names"]), len(entries), len(final)))

    print("\n== 汇总 ==")
    for h1, n_cat, n_split, n_final in total_summary:
        print(f"  {h1}：目录 {n_cat}，切出 {n_split}，最终 {n_final}")
    print(f"  总计最终条目 {len(all_entries)}（目录主条目合计 "
          f"{sum(s[1] for s in total_summary)}）")

    # 正文粘连修补：伪条目并回真正条目（见 PROFILE["joins"]）
    for join in PROFILE.get("joins", []):
        want_status = join.get("status", "not_in_catalog")
        bi = next(
            (i for i, (e, m) in enumerate(zip(all_entries, all_meta))
             if e["name"] == join["bogus"] and m.get("body_page", m["page"]) == join["page"]
             and m["status"] == want_status),
            None,
        )
        ti = next(
            (i for i, e in enumerate(all_entries) if e["name"] == join["into"]),
            None,
        )
        if bi is None or ti is None:
            print(f"  [修补失败] {join['bogus']}(p{join['page']}) -> {join['into']}："
                  f"bogus={bi} into={ti}")
            continue
        bogus = all_entries.pop(bi)
        all_meta.pop(bi)
        target = all_entries[ti if ti < bi else ti - 1]
        # 伪条目名本身是被拆走的正文文字，一并接回
        target["text"] = (target.get("text", "") + bogus["name"] + bogus.get("text", ""))
        for k, v in bogus.items():
            if k in ("name", "text") or k.startswith("_"):
                continue
            if k in target:
                target[k] += v
            else:
                target[k] = v
        print(f"  [粘连修补] '{join['bogus']}'(p{join['page']}) 并回 '{join['into']}'："
              f"{join['reason']}")

    for item in PROFILE.get("embedded_splits", []):
        source_i = next(i for i,e in enumerate(all_entries) if e["name"] == item["source"])
        target_i = next(i for i,e in enumerate(all_entries) if e["name"] == item["target"])
        value = all_entries[source_i].get(item["field"], "")
        assert item["marker"] in value, f"嵌入拆分标记不存在：{item['marker']}"
        before, marker, after = value.partition(item["marker"])
        all_entries[source_i][item["field"]] = before.rstrip()
        all_entries[target_i]["text"] = marker + after
        for key in item.get("move_fields", []):
            if key in all_entries[source_i]:
                all_entries[target_i][key] = all_entries[source_i].pop(key)
        all_entries[target_i].pop("_placeholder", None)
        all_meta[target_i]["status"] = "ok"
        print(f"  [嵌入拆分] '{item['target']}'(p{item['page']}) 从 '{item['source']}' 的"
              f" {item['field']} 字段拆出：{item['reason']}")

    if PROFILE_NAME == "2t4":
        by_name = {e["name"]: (e, m) for e, m in zip(all_entries, all_meta)}
        power, _ = by_name["权领枢密院事"]
        broken = power["text"]
        marker = "源与沿革"
        assert broken.startswith("之制。职事官名，徽宗朝临时") and marker in broken
        _, history = broken.split(marker, 1)
        power["text"] = "职事官名，徽宗朝临时之制。"
        power["职源与沿革"] = history
        print("  [字段归位] '权领枢密院事'(p115)：跨块的标题尾与职源字段恢复到对应位置")

        office, _ = by_name["枢密院承旨司"]
        post, _ = by_name["枢密院承旨"]
        duty_marker = "为承旨司（院）长官"
        assert duty_marker in office["职掌"]
        office_duty, post_duty = office["职掌"].split(duty_marker, 1)
        office["职掌"] = office_duty.rstrip()
        post["职掌"] = duty_marker + post_duty
        for key in ("职源与沿革", "品位"):
            post[key] = office.pop(key)
        print("  [字段归位] '枢密院承旨'(p116)：职源、职掌、品位从承旨司条移回本条")

        editor, _ = by_name["枢密院编修"]
        assert editor["text"] == "事官。元祐前为差遣，其后为职"
        editor["text"] = "元祐前为差遣，其后为职事官。"
        print("  [跨栏归位] '枢密院编修'(p119)：页末跨行的‘事官。’移回‘其后为职’之后")

    # 个别目录与正文 OCR 错字不同：用正文 OCR 形态完成切分后，再恢复规范条目名。
    for rename in PROFILE.get("catalog_renames", []):
        canonical = rename.get("canonical")
        if not canonical:
            continue
        matches = [
            i for i, (e, m) in enumerate(zip(all_entries, all_meta))
            if e["name"] == rename["to"] and str(m.get("page")) == rename["page"]
        ]
        if len(matches) != 1:
            print(
                f"  [规范名失败] '{rename['to']}' -> '{canonical}'(p{rename['page']})："
                f"匹配数={len(matches)}"
            )
            continue
        i = matches[0]
        all_entries[i]["name"] = canonical
        all_meta[i]["name"] = canonical
        print(
            f"  [规范条目名] '{rename['to']}' -> '{canonical}'(p{rename['page']})："
            f"{rename['reason']}"
        )

    print(f"  修补后最终条目 {len(all_entries)}")
    if uncovered_attrs:
        print(f"  attribute_dict 未覆盖的属性名（原样保留，需人工增补归一化表）："
              f"{sorted(uncovered_attrs)}")
    else:
        print("  所有属性名均被 attribute_dict 覆盖")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)
    print(f"\n已写出 {OUT_JSON}")
    print(f"已写出 {OUT_META}")


if __name__ == "__main__":
    sys.exit(main())
