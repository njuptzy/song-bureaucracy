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
        # 目录 OCR 把正文“简称与别名”中的别称误标成了独立主条目。
        # 每项按编、名称、页码精确匹配，只修正目录类型，不改正文内容。
        "catalog_retypes": [
            {"h1": "第四编 元丰正名后中枢机构类之一",
             "text": "大两省", "page": "176", "to": "surname",
             "reason": "该项是给事中条“简称与别名”的第⑫项，原始正文连续作"
                       "“⑫大两省。官称……”，并无第二个独立词条头"},
        ],
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
            {"bogus": "勾院", "page": "136", "into": "判三司盐铁勾院公事",
             "reason": "判三司盐铁勾院公事的正文在‘盐铁/勾院’换行处被误拆；"
                       "‘勾院主判官，掌本部帐籍考校、勾销事’及简称均属本条"},
            {"bogus": "勾院", "page": "136", "into": "判三司度支勾院公事",
             "reason": "判三司度支勾院公事的正文在‘度支/勾院’换行处被误拆；"
                       "‘勾院主判官，掌本部帐籍考校、勾销事’及简称均属本条"},
            {"bogus": "判官", "page": "136", "into": "三司户部勾院",
             "status": "from_surname", "target_field": "编制",
             "reason": "三司户部勾院编制字段在‘主/判官’换行处被别称匹配误拆；"
                       "‘判官一人’及后续吏额、简称均属本条"},
            {"bogus": "勾院", "page": "136", "into": "判三司户部勾院公事",
             "reason": "判三司户部勾院公事的正文在‘户部/勾院’换行处被误拆；"
                       "‘勾院主判官，掌本部帐籍考校、勾销事’及简称均属本条"},
            {"bogus": "勾院", "page": "141", "into": "提举三司帐勾磨勘司",
             "reason": "提举三司帐勾磨勘司的正文在‘帐司/勾院磨勘司’换行处被误拆；"
                       "‘勾院磨勘司的衔名’是本条定义的后半句"},
            {"bogus": "同提举", "page": "141", "into": "同提举三司帐司、勾院磨勘司",
             "status": "from_surname", "promote_target": True,
             "reason": "目录完整标题在正文被拆成‘同提举/三司帐司勾院磨勘司’两段；"
                       "应将误作别称条的正文并回目录占位并恢复为真实条目"},
            {"bogus": "监牧使", "page": "148", "into": "河南、北监牧使司",
             "status": "from_surname", "target_field": "简称",
             "reason": "河南、北监牧使司的简称引文跨页断成‘并送/监牧使司。’；"
                       "‘监牧使’不是独立词条，应连同‘司。’并回上一条简称字段"},
            {"bogus": "直天章阁", "page": "155", "into": "直宝文阁",
             "target_field": "品位",
             "reason": "直宝文阁品位句跨页断成‘序位在/直天章阁下、直显谟阁上’；"
                       "页首‘直天章阁’是被误切的句中成分，并非重复词条"},
            {"bogus": "尚书省", "page": "171", "into": "内两省",
             "reason": "内两省条所引《石林燕语》跨页断为‘尚书省/及六曹皆书《周官》……’；"
                       "页首‘尚书省’是续句组成部分，并非独立目录条目"},
            {"bogus": "进奏院", "page": "181", "into": "守阙副知",
             "reason": "守阙副知正文跨页断成‘为都/进奏院进奏官候补人……’；"
                       "续页首‘进奏院’是句中成分，被主条目同名前缀误切为伪条目"},
            {"bogus": "都进奏院", "page": "182", "into": "邸吏",
             "promote_target": True,
             "reason": "邸吏标题在原书 p182 独立排印，但 OCR 漏掉标题；"
                       "正文以‘都进奏院吏人别称’开头，被同名机构前缀误切为伪条目"},
            {"bogus": "鼓", "page": "185", "into": "监鼓",
             "reason": "监鼓正文跨页断成‘掌监守登门/鼓（《宋会要》……）’；"
                       "页首‘鼓’是被拆走的句尾，不是独立词条"},
            {"bogus": "杂役", "page": "185", "into": "看鼓",
             "promote_target": True,
             "reason": "目录有‘看鼓’而 OCR 漏掉标题，正文‘杂役名。隶登闻鼓院……’"
                       "被误切为不在目录的‘杂役’条；应并回看鼓并恢复真实条目"},
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
            {"source": "都进奏院", "target": "钤辖诸道进奏院",
             "page": "181", "field": "简称与别名",
             "marker": "铃辖诸道进奏院差遣官名",
             "move_fields": ["简称"],
             "reason": "钤辖诸道进奏院标题及正文被前条都进奏院的别名字段吞入；"
                       "原始 OCR p181 有独立标题与定义，后续简称字段也属于本条"},
            {"source": "御营使司", "target": "御营使",
             "page": "202", "field": "简称",
             "marker": "御营使 兼官名。",
             "move_fields": ["职源与沿革", "职掌", "品位"],
             "reason": "御营使标题及定义被前条御营使司的简称字段吞入，"
                       "其后职源、职掌、品位字段也均描述御营使官职"},
            {"source": "御营使司都统制司", "target": "御营使司都统制",
             "page": "202", "field": "简称",
             "marker": "御营使司都统制 武官名。",
             "reason": "御营使司都统制标题及定义被前条都统制司机构的简称字段吞入；"
                       "目录另列该武官，正文也从“武官名”开始独立定义"},
            {"source": "御营宿卫使司", "target": "御营宿卫使",
             "page": "203", "field": "编制",
             "marker": "御营宿卫使 武官名。",
             "reason": "御营宿卫使标题、始置年月与职掌被前条使司的编制字段吞入；"
                       "目录另列该武官，正文从“武官名”起独立定义"},
            {"source": "左藏封桩库库子", "target": "尚书省",
             "page": "208", "field": "text",
             "marker": "尚书省讲议司 临时官署名。",
             "target_text": "临时官署名。",
             "move_fields": ["职源", "职掌", "编制", "简称"],
             "target_tail_field": "简称",
             "target_tail_with_name": True,
             "reason": "左藏封桩库库子与尚书省讲议司标题被OCR并在同一文本块；"
                       "讲议司全部字段误挂前条，下一页‘尚书省讲义武备房……’又是简称引文续句"},
            {"source": "吏部尚书左选催驱案", "target": "吏部尚书左选甲库案",
             "page": "215", "field": "text",
             "marker": "吏部尚书左选用库案 ",
             "target_after_marker": True,
             "reason": "原书p215在催驱案后另起‘吏部尚书左选甲库案’，"
                       "OCR把‘甲’误识为‘用’并将整条正文吞入催驱案；"
                       "按原书标题拆回目录占位，正文原样取标记后的内容"},
            {"source": "吏部尚书右选名籍案", "target": "吏部尚书右选甲库案",
             "page": "216", "field": "text",
             "marker": "吏部尚书右选用库案 ",
             "target_after_marker": True,
             "reason": "原书p216在名籍案后另起‘吏部尚书右选甲库案’，"
                       "OCR把‘甲’误识为‘用’并将整条正文吞入名籍案；"
                       "按原书标题拆回目录占位，正文原样取标记后的内容"},
            {"source": "吏部侍郎左选名籍案", "target": "吏部侍郎左选甲库案",
             "page": "218", "field": "text",
             "marker": "吏部侍郎左选用库案 ",
             "target_after_marker": True,
             "reason": "原书p218在名籍案后另起‘吏部侍郎左选甲库案’，"
                       "OCR把‘甲’误识为‘用’并将整条正文吞入名籍案；"
                       "按原书标题拆回目录占位，正文原样取标记后的内容"},
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
            {"from": "提领三椎货务都茶场所", "to": "提领三榷货务都茶场所", "page": "205",
             "reason": "目录把官署名中的‘榷’误识为‘椎’，正文独立标题作‘提领三榷货务都茶场所’"},
            {"from": "主管尚书省制造宣告局", "to": "主管尚书省制造官告局", "page": "224",
             "reason": "核对原书p224，目录把‘官告局’误识为‘宣告局’"},
            {"from": "宣告院", "to": "官告院", "page": "224",
             "reason": "核对原书p224，目录把独立词条‘官告院’误识为‘宣告院’"},
            {"from": "宣告院绫纸库", "to": "官告院绫纸库", "page": "224",
             "reason": "核对原书p224，目录把‘官告院绫纸库’误识为‘宣告院绫纸库’"},
            {"from": "主管宣告院", "to": "主管官告院", "page": "224",
             "reason": "核对原书p224，目录把‘主管官告院’误识为‘主管宣告院’"},
            {"from": "户部左曹课利窦", "to": "户部左曹课利窠", "page": "228",
             "reason": "核对原书p228，目录把独立词条‘户部左曹课利窠’末字误识为‘窦’"},
            {"from": "仓部司棠柒案", "to": "仓部司棠余案", "canonical": "仓部司柴采案",
             "page": "232",
             "reason": "核对原书p232，目录与正文分别误识为‘棠柒案’和‘棠余案’，"
                       "原书独立词头及正文均明确作‘仓部司柴采案’"},
            {"from": "度牌库", "to": "度牒库", "page": "238",
             "reason": "目录把正文独立机构名‘度牒库’中的‘牒’误识为‘牌’"},
            {"from": "监度牌库", "to": "监度牒库", "page": "238",
             "reason": "目录把正文独立监当官名‘监度牒库’中的‘牒’误识为‘牌’"},
            {"from": "提领度牌所", "to": "提领度牒所", "page": "238",
             "reason": "目录把正文独立官司名‘提领度牒所’中的‘牒’误识为‘牌’"},
            {"from": "尚书省讲议司", "to": "尚书省", "canonical": "尚书省讲议司", "page": "208",
             "reason": "正文标题被前条库子吞入，仅余简称引文续句以‘尚书省’开头；"
                       "先按被误切形态匹配，拆回正文后恢复目录正式名"},
            {"from": "讲议司评定官", "to": "讲议司", "canonical": "讲议司详定官", "page": "208",
             "strip_text_prefix": "详定官 ",
             "reason": "目录把‘详定官’误识为‘评定官’，正文标题‘讲议司详定官’"
                       "又只按较短前缀‘讲议司’切开；恢复正式官名并移除正文中的标题尾"},
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
            {"from": "胃案", "to": "胄案", "page": "134",
             "reason": "目录把盐铁部军器事务机构‘胄案’误识为‘胃案’，正文独立标题明确作‘胄案’"},
            {"from": "点检三馆秘图书籍", "to": "点检三馆秘阁书籍", "page": "159",
             "reason": "目录把‘秘阁’误识为‘秘图’；正文嵌入标题明确作‘点检三馆秘阁书籍’"},
            {"from": "耦头", "to": "蠍头", "canonical": "螭头", "page": "171",
             "reason": "目录把‘螭头’误识为‘耦头’，正文嵌入标题误识为‘蠍头’；"
                       "按正文所引‘螭首’及通行史官典故恢复规范名"},
            {"from": "瓯院", "to": "瓯院", "canonical": "匦院", "page": "183",
             "reason": "目录与 OCR 均误识为‘瓯院’；核对原书第四编 PDF p183，"
                       "独立标题明确作‘匦院’"},
            {"from": "瓯", "to": "軋", "canonical": "匦", "page": "183",
             "reason": "目录误识为‘瓯’，正文标题 OCR 误识为‘軋’；"
                       "核对原书第四编 PDF p183，独立标题明确作‘匦’"},
            {"from": "迦纳司", "to": "蠲纳司", "page": "138",
             "reason": "目录把‘蠲’误识为‘迦’；正文独立标题明确作‘蠲纳司’，且征欠司沿革载乾兴元年改名"},
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
        "catalog_renames": [
            {"from": "三巫", "to": "三丞", "page": "297",
             "reason": "核对第五编 PDF p297，目录把独立词条‘三丞’误识为‘三巫’；"
                       "正文明确为宗正寺丞、太常寺丞、秘书省丞的合称"},
            {"from": "教宗院", "to": "敦宗院", "page": "323",
             "reason": "核对第五编 PDF p323，目录把官司名‘敦宗院’误识为‘教宗院’；"
                       "正文标题及全条内容均明确作‘敦宗院’"},
            {"from": "保州教宗院", "to": "保州敦宗院", "page": "323",
             "reason": "核对第五编 PDF p323-324，目录把‘保州敦宗院’误识为"
                       "‘保州教宗院’，正文标题及续页正文均明确作‘敦’"},
            {"from": "于办玉牒所玉牒殿", "to": "干办玉牒所玉牒殿", "page": "325",
             "reason": "核对第五编 PDF p325，目录漏识条目首字‘干’，正文独立标题"
                       "明确作‘干办玉牒所玉牒殿’"},
            {"from": "廖牺案", "to": "廪牺案", "page": "301",
             "reason": "核对第五编 PDF p301，目录把太常寺办事机构‘廪牺案’"
                       "误识为‘廖牺案’，正文独立标题明确作‘廪牺案’"},
            {"from": "评定大乐所", "to": "详定大乐所", "page": "303",
             "reason": "核对第五编 PDF p303，目录把临时机构‘详定大乐所’"
                       "误识为‘评定大乐所’，正文独立标题明确作‘详定大乐所’"},
            {"from": "衡前乐", "to": "衙前乐", "page": "307",
             "reason": "核对第五编 PDF p307，目录把州府乐部‘衙前乐’"
                       "误识为‘衡前乐’，正文独立标题明确作‘衙前乐’"},
            {"from": "议案", "to": "仪案", "page": "320",
             "reason": "核对第五编 PDF p320，目录把大宗正司六案之一‘仪案’"
                       "误识为‘议案’，正文独立标题明确作‘仪案’"},
            {"from": "刑事", "to": "刑案", "page": "320",
             "reason": "核对第五编 PDF p320，目录把大宗正司六案之一‘刑案’"
                       "误识为‘刑事’，正文独立标题明确作‘刑案’"},
            {"from": "肾佐", "to": "胥佐", "page": "327",
             "reason": "第五编 p327 正文独立标题及释文均明确作‘胥佐’，目录误识为‘肾佐’"},
            {"from": "左、右天厥院", "to": "左、右天厩院", "page": "341",
             "reason": "第五编 p341 目录把马政机构名‘左、右天厩院’的‘厩’"
                       "误识为‘厥’，正文独立标题明确作‘天厩院’"},
            {"from": "孽官", "to": "孽官", "canonical": "辇官", "page": "347",
             "reason": "核对第五编 PDF p347，目录把御辇院三类辇官通称‘辇官’"
                       "误识为‘孽官’，正文独立标题明确作‘辇官’"},
            {"from": "左、右天厥使", "to": "左、右天厩使", "page": "342",
             "reason": "第五编 p342 目录把差遣名‘左、右天厩使’的‘厩’"
                       "误识为‘厥’，正文独立标题及简称均明确作‘天厩使’"},
        ],
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
        retype = next(
            (item for item in PROFILE.get("catalog_retypes", [])
             if cur_h1 == item["h1"] and r["type"] == "name"
             and r["text"] == item["text"]
             and str(r.get("page")) == item["page"]),
            None,
        )
        if retype:
            old_type = r["type"]
            r["type"] = retype["to"]
            fix_log.append(
                f"{old_type} '{r['text']}'(p{r.get('page')}) -> {r['type']}"
                f"（{retype['reason']}）"
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
        target_i = ti if ti < bi else ti - 1
        target = all_entries[target_i]
        # 伪条目名本身是被拆走的正文文字，一并接回。通常接回正文；若断点
        # 位于属性字段中（如“主/判官一人”），则由 target_field 指定归位字段。
        target_field = join.get("target_field", "text")
        target[target_field] = (
            target.get(target_field, "") + bogus["name"] + bogus.get("text", "")
        )
        for k, v in bogus.items():
            if k in ("name", "text") or k.startswith("_"):
                continue
            if k in target:
                target[k] += v
            else:
                target[k] = v
        if join.get("promote_target"):
            target.pop("_placeholder", None)
            all_meta[target_i]["status"] = "ok"
        print(f"  [粘连修补] '{join['bogus']}'(p{join['page']}) 并回 '{join['into']}'："
              f"{join['reason']}")

    for item in PROFILE.get("embedded_splits", []):
        source_i = next(i for i,e in enumerate(all_entries) if e["name"] == item["source"])
        target_i = next(
            i
            for i, e in enumerate(all_entries)
            if e["name"] == item["target"]
            and (
                not item.get("page")
                or str(all_meta[i].get("page")) == str(item["page"])
            )
        )
        value = all_entries[source_i].get(item["field"], "")
        assert item["marker"] in value, f"嵌入拆分标记不存在：{item['marker']}"
        before, marker, after = value.partition(item["marker"])
        all_entries[source_i][item["field"]] = before.rstrip()
        target_tail = all_entries[target_i].get("text", "")
        if item.get("target_tail_with_name"):
            target_tail = all_entries[target_i]["name"] + target_tail
        if item.get("target_after_marker"):
            all_entries[target_i]["text"] = after
        else:
            all_entries[target_i]["text"] = item.get("target_text", marker + after)
        for key in item.get("move_fields", []):
            if key in all_entries[source_i]:
                all_entries[target_i][key] = all_entries[source_i].pop(key)
        if item.get("target_tail_field") and target_tail:
            key = item["target_tail_field"]
            all_entries[target_i][key] = all_entries[target_i].get(key, "") + target_tail
        all_entries[target_i].pop("_placeholder", None)
        all_meta[target_i]["status"] = "ok"
        print(f"  [嵌入拆分] '{item['target']}'(p{item['page']}) 从 '{item['source']}' 的"
              f" {item['field']} 字段拆出：{item['reason']}")

    if PROFILE_NAME == "2t4":
        by_name = {e["name"]: (e, m) for e, m in zip(all_entries, all_meta)}

        manufacturing_manager, manufacturing_manager_meta = by_name[
            "主管尚书省制造官告局"
        ]
        bogus_notice_alias, bogus_notice_alias_meta = by_name["宣告局"]
        assert manufacturing_manager["text"] == "差遣官名。"
        assert bogus_notice_alias.get("_from_surname") is True
        assert bogus_notice_alias["text"].startswith("主管官，由")
        manufacturing_manager["text"] += "官告局" + bogus_notice_alias["text"]
        for key, value in list(bogus_notice_alias.items()):
            if key in ("name", "text", "_from_surname"):
                continue
            manufacturing_manager[key] = value
        bogus_notice_alias.clear()
        bogus_notice_alias.update({"name": "官告局", "text": "", "_placeholder": True})
        bogus_notice_alias_meta["name"] = "官告局"
        bogus_notice_alias_meta["status"] = "placeholder"
        for key in ("h1", "h2", "h3"):
            bogus_notice_alias_meta[key] = manufacturing_manager_meta.get(key)
        print("  [跨栏归位] '主管尚书省制造官告局'(p224)：主管官正文从误切别称条"
              "‘宣告局’接回，并将纯别称恢复为‘官告局’空占位")

        notice_office, notice_office_meta = by_name["官告院"]
        paper_store, paper_store_meta = by_name["官告院绫纸库"]
        notice_manager, _ = by_name["主管官告院"]
        assert notice_office["text"].startswith("官署名。")
        assert notice_manager["text"].startswith("差遣官员。")

        store_title = "告院绫纸库 官告院附属机构名。"
        assert store_title in notice_office["别名"]
        office_aliases, _ = notice_office["别名"].split(store_title, 1)
        notice_office["别名"] = office_aliases.rstrip()
        paper_store["text"] = "官告院附属机构名。"
        paper_store["职能"] = notice_office.pop("职能")

        store_staff_marker = "隶属机构：官告院绫纸库。"
        assert store_staff_marker in notice_office["编制"]
        office_staff, subordinate_staff = notice_office["编制"].split(
            store_staff_marker, 1
        )
        notice_office["编制"] = office_staff.rstrip() + store_staff_marker
        paper_store["编制"] = subordinate_staff.rstrip()
        paper_store.pop("_placeholder", None)
        paper_store_meta["status"] = "ok"
        print("  [跨栏归位] '官告院绫纸库'(p224)：标题OCR漏首字‘官’，"
              "从‘官告院’别名及编制字段拆回独立附属机构，保持词条ID")

        warehouse, _ = by_name["仓部司"]
        wrong_cases = "分案六，即仓场、上供、巢籴、给纳、知杂、开拆。"
        assert wrong_cases in warehouse["编制"]
        warehouse["编制"] = warehouse["编制"].replace(
            wrong_cases,
            "分案六，即仓场、上供、柴采、给纳、知杂、开拆。",
        )
        forage_case, _ = by_name["仓部司棠余案"]
        wrong_duty = "掌粮草巢籴、坐仓折纳"
        assert wrong_duty in forage_case["text"]
        forage_case["text"] = forage_case["text"].replace(
            wrong_duty,
            "掌粮草柴采、坐仓折纳",
        )
        print("  [OCR字误] '仓部司柴采案'(p232)：核原书恢复独立词头、正文‘柴采’"
              "及仓部司六案编制中的‘柴采’，保持词条ID")

        guest_post, _ = by_name["主客司员外郎"]
        bogus_yuanlang, bogus_yuanlang_meta = by_name["员郎"]
        assert guest_post["编制"].endswith("只置一")
        assert bogus_yuanlang.get("_from_surname") is True
        assert bogus_yuanlang["text"] == "官（《宋会要·职官》13之7）。"
        assert "简称" in bogus_yuanlang
        guest_post["编制"] += bogus_yuanlang["name"] + bogus_yuanlang["text"]
        guest_post["简称"] = bogus_yuanlang["简称"]
        guest_post["职源"] = guest_post["职源"].replace(
            "开皇六年《隋书", "开皇六年（《隋书",
        )
        bogus_yuanlang.clear()
        bogus_yuanlang.update({"name": "员郎", "text": "", "_placeholder": True})
        bogus_yuanlang_meta["status"] = "placeholder"
        print("  [跨页归位] '主客司员外郎'(p238-239)：将‘员郎官’续文及简称字段"
              "并回本条，伪条目‘员郎’改为空占位以稳定后续词条ID")

        capital_judge_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "都官司郎中" and str(meta.get("page")) == "250"
        ]
        bogus_shangshu_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "尚书" and str(meta.get("page")) == "251"
            and meta.get("status") == "from_surname"
        ]
        capital_outside_placeholder_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "都官员外郎" and str(meta.get("page")) == "251"
            and entry.get("_placeholder") is True
        ]
        bogus_capital_office_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "都官司" and str(meta.get("page")) == "251"
            and meta.get("status") == "not_in_catalog"
        ]
        assert len(capital_judge_matches) == 1
        assert len(bogus_shangshu_matches) == 1
        assert len(capital_outside_placeholder_matches) == 1
        assert len(bogus_capital_office_matches) == 1
        capital_judge, _ = capital_judge_matches[0]
        bogus_shangshu, bogus_shangshu_meta = bogus_shangshu_matches[0]
        capital_outside, capital_outside_meta = capital_outside_placeholder_matches[0]
        bogus_capital_office, bogus_capital_office_meta = bogus_capital_office_matches[0]

        assert capital_judge["职源"].endswith("（《六典》卷6《刑部")
        assert bogus_shangshu["text"] == "·都官郎中》）。"
        capital_judge["职源"] += bogus_shangshu["name"] + bogus_shangshu["text"]
        for key in ("职掌", "官品", "简称"):
            capital_judge[key] = bogus_shangshu[key]
        bogus_shangshu.clear()
        bogus_shangshu.update({"name": "尚书", "text": "", "_placeholder": True})
        bogus_shangshu_meta["status"] = "placeholder"

        assert bogus_capital_office["text"] == "员外郎阶官名、职事官名。"
        capital_outside.clear()
        capital_outside.update({
            "name": "都官司员外郎",
            "text": "阶官名、职事官名。",
        })
        for key in ("职源", "职掌", "官品", "简称与别名"):
            capital_outside[key] = bogus_capital_office[key]
        capital_outside_meta["name"] = "都官司员外郎"
        capital_outside_meta["status"] = "ok"
        bogus_capital_office.clear()
        bogus_capital_office.update({"name": "都官司", "text": "", "_placeholder": True})
        bogus_capital_office_meta["status"] = "placeholder"
        print("  [跨页归位] '都官司郎中、员外郎'(p250-251)：将页首‘尚书’续文及"
              "职掌、官品、简称接回郎中条，将误切‘都官司+员外郎’恢复到目录占位；"
              "两个伪条目改为空占位以稳定后续词条ID")

        work_case_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "工部工作案" and str(meta.get("page")) == "254"
            and entry.get("_placeholder") is True
        ]
        bogus_work_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "工部" and str(meta.get("page")) == "254"
            and meta.get("status") == "from_surname"
        ]
        assert len(work_case_matches) == 1
        assert len(bogus_work_matches) == 1
        work_case, work_case_meta = work_case_matches[0]
        bogus_work, bogus_work_meta = bogus_work_matches[0]
        assert bogus_work["text"].startswith("工作方案 元丰新制")
        work_case["text"] = (
            "元丰新制尚书省工部六案之一，为本部常设办事部门。"
            "掌舟、车、器械、钱货等百工制作"
            "（《宋史·职官志》3《工部尚书》及《分纪》卷11《工部尚书》）。"
        )
        work_case.pop("_placeholder", None)
        work_case_meta["status"] = "ok"
        bogus_work.clear()
        bogus_work.update({"name": "工部", "text": "", "_placeholder": True})
        bogus_work_meta["status"] = "placeholder"
        print("  [跨栏归位] '工部工作案'(p254)：原书独立标题与正文被别称‘工部’"
              "误切并多识一‘方’字；正文移回目录占位，伪条目改为空占位")

        audit_office, _ = by_name["比部司"]
        broken_audit_quote = "“勾覆、理欠、凭由案及印发钞引事归比部（《宋史"
        assert broken_audit_quote in audit_office["职掌"]
        audit_office["职掌"] = audit_office["职掌"].replace(
            broken_audit_quote,
            "“勾覆、理欠、凭由案及印发钞引事归比部”（《宋史",
        )
        audit_clerk, _ = by_name["比部司郎中"]
        alias_marker = "简称与别名 ①"
        assert alias_marker in audit_clerk["官品"]
        audit_grade, audit_aliases = audit_clerk["官品"].split(alias_marker, 1)
        audit_clerk["官品"] = audit_grade.rstrip()
        audit_clerk["简称与别名"] = "①" + audit_aliases
        print("  [字段归位] '比部司、比部司郎中'(p251-252)：补元祐三年引文闭引号，"
              "并将误粘入官品的简称与别名拆回独立字段")

        yu_office_clerk_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "虞部司郎中" and str(meta.get("page")) == "257"
        ]
        bogus_registry_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "主簿" and str(meta.get("page")) == "258"
            and meta.get("status") == "from_surname"
        ]
        assert len(yu_office_clerk_matches) == 1
        assert len(bogus_registry_matches) == 1
        yu_office_clerk, _ = yu_office_clerk_matches[0]
        bogus_registry, bogus_registry_meta = bogus_registry_matches[0]
        assert yu_office_clerk["简称"].endswith("“自")
        assert bogus_registry["text"] == "凡十一迁，其官至尚书虞部郎中。”"
        yu_office_clerk["简称"] += bogus_registry["name"] + bogus_registry["text"]
        bogus_registry.clear()
        bogus_registry.update({"name": "主簿", "text": "", "_placeholder": True})
        bogus_registry_meta["status"] = "placeholder"
        print("  [跨页归位] '虞部司郎中'(p257-258)：页首‘主簿凡十一迁’为简称"
              "引文续文，接回本条；伪条目‘主簿’改为空占位以稳定后续词条ID")

        library_director_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "秘书省监" and str(meta.get("page")) == "261"
        ]
        bogus_book_office_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "书省" and str(meta.get("page")) == "262"
            and meta.get("status") == "from_surname"
        ]
        assert len(library_director_matches) == 1
        assert len(bogus_book_office_matches) == 1
        library_director, _ = library_director_matches[0]
        bogus_book_office, bogus_book_office_meta = bogus_book_office_matches[0]
        assert library_director["简称与别名"].endswith("：“（秘")
        assert bogus_book_office["text"].startswith(")监淳熙以后三人")
        library_director["简称与别名"] += (
            bogus_book_office["name"] + bogus_book_office["text"]
        )
        library_director["简称与别名"] = library_director["简称与别名"].replace(
            "（秘书省)监淳熙", "（秘书省）监淳熙",
        )
        bogus_book_office.clear()
        bogus_book_office.update({"name": "书省", "text": "", "_placeholder": True})
        bogus_book_office_meta["status"] = "placeholder"
        print("  [跨页归位] '秘书省监'(p261-262)：页首‘书省）监淳熙以后’为"
              "简称引文续文，接回本条；伪条目‘书省’改为空占位")

        history_overseer_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "提纲史事" and str(meta.get("page")) == "262"
        ]
        bogus_secretariat_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "秘书省" and str(meta.get("page")) == "262"
            and meta.get("status") == "not_in_catalog"
        ]
        assert len(history_overseer_matches) == 1
        assert len(bogus_secretariat_matches) == 1
        history_overseer, _ = history_overseer_matches[0]
        bogus_secretariat, bogus_secretariat_meta = bogus_secretariat_matches[0]
        assert history_overseer["text"].endswith("的提举")
        assert bogus_secretariat["text"] == "官兼，提领本朝修史事（《馆阁续录》卷7）。"
        history_overseer["text"] += (
            bogus_secretariat["name"] + bogus_secretariat["text"]
        )
        bogus_secretariat.clear()
        bogus_secretariat.update({"name": "秘书省", "text": "", "_placeholder": True})
        bogus_secretariat_meta["status"] = "placeholder"
        print("  [跨栏归位] '提纲史事'(p262)：将误切成伪条目‘秘书省’的标题尾"
              "与正文接回本条，伪条目改为空占位以稳定后续词条ID")

        secretary_assistant_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "秘书" and str(meta.get("page")) == "262"
            and meta.get("status") == "fuzzy"
        ]
        assert len(secretary_assistant_matches) == 1
        secretary_assistant, secretary_assistant_meta = secretary_assistant_matches[0]
        assert secretary_assistant["text"] == "丞宋前期阶官名，元丰改制后职事"
        assert secretary_assistant.get("_catalog_name") == "秘书承"
        secretary_assistant["name"] = "秘书丞"
        secretary_assistant["text"] = "宋前期阶官名，元丰改制后职事官名。"
        secretary_assistant.pop("_catalog_name", None)
        secretary_assistant_meta["name"] = "秘书丞"
        secretary_assistant_meta["status"] = "ok"
        secretary_assistant_meta.pop("catalog_name", None)
        print("  [标题归位] '秘书丞'(p262)：标题末字‘丞’被吞入正文，目录又误作"
              "‘秘书承’；据原书恢复标题及定义句末‘官名。’")

        secretariat_supervisor_office, _ = by_name["秘书省都监司"]
        secretariat_supervisor, secretariat_supervisor_meta = by_name["秘书省都监"]
        assert secretariat_supervisor.get("_placeholder") is True
        embedded_title = "秘书省都监 差遣名。"
        embedded_alias = "都监。《宋会要·职官》18之11《秘书省》"
        source_aliases = secretariat_supervisor_office["简称"]
        assert embedded_title in source_aliases
        office_alias, supervisor_tail = source_aliases.split(embedded_title, 1)
        assert embedded_alias in supervisor_tail
        supervisor_body, supervisor_alias_tail = supervisor_tail.split(
            embedded_alias, 1
        )
        secretariat_supervisor_office["简称"] = office_alias.rstrip()
        secretariat_supervisor.clear()
        secretariat_supervisor.update({
            "name": "秘书省都监",
            "text": "差遣名。" + supervisor_body.rstrip(),
            "简称": embedded_alias + supervisor_alias_tail,
        })
        secretariat_supervisor_meta["status"] = "ok"
        print("  [字段归位] '秘书省都监'(p265)：独立标题、正文及简称被前条"
              "‘秘书省都监司’的简称字段吞入；据原书拆回目录占位并保持ID")

        fire_room, _ = by_name["潜火司"]
        fire_soldier_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "潜火" and entry.get("_placeholder") is True
            and str(meta.get("page")) == "军兵"
        ]
        assert len(fire_soldier_matches) == 1
        fire_soldier, fire_soldier_meta = fire_soldier_matches[0]
        embedded_fire_title = "潜火军兵 救火士兵，"
        assert embedded_fire_title in fire_room["text"]
        room_text, soldier_tail = fire_room["text"].split(
            embedded_fire_title, 1
        )
        fire_room["text"] = room_text.rstrip()
        fire_soldier.clear()
        fire_soldier.update({
            "name": "潜火军兵",
            "text": "救火士兵，" + soldier_tail,
        })
        fire_soldier_meta["name"] = "潜火军兵"
        fire_soldier_meta["page"] = "267"
        fire_soldier_meta["body_page"] = "267"
        fire_soldier_meta["status"] = "ok"
        print("  [标题归位] '潜火军兵'(p267)：目录把标题两字误作词名、后两字"
              "误作页码，正文又被‘潜火司’前缀吞入；据原书拆回并保持ID")

        astronomy_office_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "司天监官" and str(meta.get("page")) == "268"
            and meta.get("status") == "fuzzy"
        ]
        assert len(astronomy_office_matches) == 1
        astronomy_office, astronomy_office_meta = astronomy_office_matches[0]
        assert astronomy_office["text"] == "司名。隶京百司、提举所"
        assert astronomy_office.get("_catalog_name") == "司天监"
        astronomy_office["name"] = "司天监"
        astronomy_office["text"] = "官司名。隶京百司、提举所。"
        astronomy_office.pop("_catalog_name", None)
        astronomy_office_meta["name"] = "司天监"
        astronomy_office_meta["status"] = "ok"
        astronomy_office_meta.pop("catalog_name", None)
        print("  [标题归位] '司天监'(p268)：正文标题尾‘官’被吞入定义首字，"
              "恢复原书标题及‘官司名’完整定义")

        monitor_student, _ = by_name["司天监监生"]
        bogus_calendar_study_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "历算" and str(meta.get("page")) == "272"
            and meta.get("status") == "from_surname"
        ]
        assert len(bogus_calendar_study_matches) == 1
        bogus_calendar_study, bogus_calendar_study_meta = (
            bogus_calendar_study_matches[0]
        )
        assert monitor_student["text"].endswith("监生须精熟")
        assert bogus_calendar_study["text"].startswith("学，月终有俸钱")
        monitor_student["text"] += (
            bogus_calendar_study["name"] + bogus_calendar_study["text"]
        )
        monitor_student["简称"] = bogus_calendar_study["简称"]
        bogus_calendar_study.clear()
        bogus_calendar_study.update({
            "name": "历算", "text": "", "_placeholder": True,
        })
        bogus_calendar_study_meta["status"] = "placeholder"
        print("  [跨页归位] '司天监监生'(p271-272)：页首‘历算学’为上页"
              "‘监生须精熟’续文，并连同简称接回；伪条目‘历算’改为空占位")

        calendar_clerk, _ = by_name["司天监历算科主簿"]
        calendar_official, calendar_official_meta = by_name["司天监历算"]
        assert calendar_official.get("_placeholder") is True
        embedded_calendar_title = "司天监历算 技术官。"
        assert embedded_calendar_title in calendar_clerk["text"]
        clerk_text, official_text = calendar_clerk["text"].split(
            embedded_calendar_title, 1
        )
        calendar_clerk["text"] = clerk_text.rstrip().replace(
            "隶司天监司天监官充。", "隶司天监。司天监官充。",
        )
        calendar_assistant, _ = by_name["司天监历算科丞"]
        assert "隶司天监司天监官充。" in calendar_assistant["text"]
        calendar_assistant["text"] = calendar_assistant["text"].replace(
            "隶司天监司天监官充。", "隶司天监。司天监官充。",
        )
        calendar_official.clear()
        calendar_official.update({
            "name": "司天监历算",
            "text": "技术官。" + official_text,
            "简称": calendar_clerk.pop("简称"),
        })
        calendar_official_meta["status"] = "ok"
        print("  [嵌入拆分] '司天监历算'(p272)：独立标题、正文和简称被"
              "‘司天监历算科主簿’吞入，拆回目录占位并补历算科丞、主簿"
              "正文句号")

        for science_title in (
            "司天监历算科", "司天监天文科", "司天监三式科",
        ):
            science_entry, _ = by_name[science_title]
            assert science_entry["text"].startswith("窟名。")
            science_entry["text"] = "窠名。" + science_entry["text"][3:]
        print("  [OCR字误] p272：核原书将历算科、天文科、三式科定义首词"
              "‘窟名’恢复为‘窠名’")

        taiyi, _ = by_name["司天监三式科太乙"]
        dunjia_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "司天监三式科通甲"
            and str(meta.get("page")) == "273"
            and meta.get("status") == "placeholder"
        ]
        assert len(dunjia_matches) == 1
        dunjia, dunjia_meta = dunjia_matches[0]
        embedded_dunjia_title = "司天监三式科循甲 技术官。"
        assert embedded_dunjia_title in taiyi["text"]
        taiyi_text, dunjia_text = taiyi["text"].split(
            embedded_dunjia_title, 1
        )
        taiyi["text"] = taiyi_text.rstrip()
        dunjia.clear()
        dunjia.update({
            "name": "司天监三式科遁甲",
            "text": "技术官。" + dunjia_text,
        })
        dunjia_meta["name"] = "司天监三式科遁甲"
        dunjia_meta["status"] = "ok"
        print("  [嵌入拆分] p273：核原书将误识并吞入太乙条的"
              "‘司天监三式科遁甲’拆回目录占位，恢复独立词条")

        astronomy_proposal_office, _ = by_name["提举太史局所"]
        astronomy_proposal, astronomy_proposal_meta = by_name["提举太史局"]
        assert astronomy_proposal.get("_placeholder") is True
        embedded_proposal_title = "提举太史局 差遣名。"
        assert embedded_proposal_title in astronomy_proposal_office["text"]
        office_text, proposal_text = astronomy_proposal_office["text"].split(
            embedded_proposal_title, 1
        )
        astronomy_proposal_office["text"] = office_text.rstrip()
        astronomy_proposal.clear()
        astronomy_proposal.update({
            "name": "提举太史局",
            "text": "差遣名。" + proposal_text,
            "简称": astronomy_proposal_office.pop("简称"),
        })
        astronomy_proposal_meta["status"] = "ok"
        print("  [嵌入拆分] p274：将被‘提举太史局所’吞入的"
              "‘提举太史局’正文与简称拆回独立目录条目")

        taishi_cheng, _ = by_name["太史局丞"]
        assert "《职源摄要》" in taishi_cheng["品位"]
        taishi_cheng["品位"] = taishi_cheng["品位"].replace(
            "《职源摄要》", "《职源撮要》",
        )
        qiehu, _ = by_name["太史局挈壶正"]
        broken_qiehu_history = qiehu["职源与沿革"]
        duty_marker = "掌 掌知漏刻"
        assert duty_marker in broken_qiehu_history
        qiehu_history, qiehu_duty = broken_qiehu_history.split(
            duty_marker, 1
        )
        qiehu["职源与沿革"] = qiehu_history.rstrip()
        qiehu["职掌"] = "掌知漏刻" + qiehu_duty
        print("  [字段修复] p275-276：核原书恢复太史局丞出处"
              "‘职源撮要’，并将太史局挈壶正‘掌知漏刻’从沿革拆回职掌")

        calendar_branch, _ = by_name["太史局历算科"]
        calendar_dispatch, calendar_dispatch_meta = by_name["太史局历算"]
        assert calendar_dispatch.get("_placeholder") is True
        calendar_dispatch_marker = "太史局历算 差遣名。"
        assert calendar_dispatch_marker in calendar_branch["text"]
        branch_text, dispatch_text = calendar_branch["text"].split(
            calendar_dispatch_marker, 1
        )
        calendar_branch["text"] = branch_text.rstrip()
        calendar_dispatch.clear()
        calendar_dispatch.update({
            "name": "太史局历算",
            "text": "差遣名。" + dispatch_text,
            "简称": calendar_branch.pop("简称"),
        })
        calendar_dispatch_meta["status"] = "ok"
        print("  [嵌入拆分] p277：将被‘太史局历算科’吞入的"
              "‘太史局历算’正文与简称拆回独立目录条目")

        astronomy_court, _ = by_name["太史局天文院"]
        evening_report, evening_report_meta = by_name["酉点天文日状官"]
        assert evening_report.get("_placeholder") is True
        evening_report_marker = "西点天文日状官 差遣名。"
        assert evening_report_marker in astronomy_court["简称"]
        court_alias, evening_report_text = astronomy_court["简称"].split(
            evening_report_marker, 1
        )
        astronomy_court["简称"] = court_alias.rstrip()
        evening_report.clear()
        evening_report.update({
            "name": "酉点天文日状官",
            "text": "差遣名。" + evening_report_text,
        })
        evening_report_meta["status"] = "ok"
        print("  [嵌入拆分] p277：核原书将误识为‘西点’且吞入天文院"
              "简称字段的‘酉点天文日状官’恢复为独立词条")

        taishi_student, _ = by_name["学生"]
        assert str(_["page"]) == "278"
        assert taishi_student["text"].startswith("更名。")
        taishi_student["text"] = "吏名。" + taishi_student["text"][3:]

        bureau_people, _ = by_name["太史局官生学生"]
        embedded_alias = " 简称太史官生。"
        assert embedded_alias in bureau_people["text"]
        people_text, people_alias = bureau_people["text"].split(
            embedded_alias, 1
        )
        bureau_people["text"] = people_text.replace(
            "礼生、 历生", "礼生、历生",
        ).rstrip()
        bureau_people["简称"] = (
            "太史官生。" + people_alias
        ).replace("浑仪 之法", "浑仪之法")

        observatory_students, _ = by_name["天文院司辰额内瞻望局学生"]
        assert observatory_students["text"].startswith("文院所属")
        observatory_students["text"] = (
            "天" + observatory_students["text"]
        )

        commoner_calendarist, _ = by_name["草泽应聘造历人"]
        assert commoner_calendarist["text"].endswith(
            "（《宋会要·运历》1之13)。"
        )
        commoner_calendarist["text"] = commoner_calendarist["text"][:-2] + "）。"
        print("  [OCR与字段修复] p278-279：恢复太史局学生‘吏名’、"
              "太史官生简称字段、天文院首字及草泽造历条跨栏中文括号")

        calendar_copyist_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "楷书" and str(meta.get("page")) == "279"
        ]
        assert len(calendar_copyist_matches) == 1
        calendar_copyist, _ = calendar_copyist_matches[0]
        assert "誉抄历书" in calendar_copyist["text"]
        calendar_copyist["text"] = calendar_copyist["text"].replace(
            "誉抄历书", "誊抄历书",
        )
        history_institute_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "国史院" and str(meta.get("page")) == "280"
        ]
        assert len(history_institute_matches) == 1
        history_institute, _ = history_institute_matches[0]
        assert "《挥塵后录》" in history_institute["职掌"]
        history_institute["职掌"] = history_institute["职掌"].replace(
            "《挥塵后录》", "《挥麈后录》",
        )

        co_compiler, _ = by_name["实录院同修撰"]
        broken_co_compiler_citation = (
            "（《宋史·宋绶传》、《玉海》卷48《乾兴真宗实录》，"
            "但未冠以“实录院”之名。"
        )
        assert broken_co_compiler_citation in co_compiler["text"]
        co_compiler["text"] = co_compiler["text"].replace(
            broken_co_compiler_citation,
            "（《宋史·宋绶传》、《玉海》卷48《乾兴真宗实录》），"
            "但未冠以“实录院”之名。",
        )
        combined_compiler, _ = by_name["国史实录院编修检讨官"]
        assert "（屋）寻迁著作郎" in combined_compiler["text"]
        combined_compiler["text"] = combined_compiler["text"].replace(
            "（屋）寻迁著作郎", "（焘）寻迁著作郎",
        )
        calendar_office, _ = by_name["日历所"]
        assert "钰次成一朝编年" in calendar_office["职掌"]
        assert "日历比实录更为详瞻" in calendar_office["职掌"]
        calendar_office["职掌"] = calendar_office["职掌"].replace(
            "钰次成一朝编年", "铨次成一朝编年",
        ).replace("日历比实录更为详瞻", "日历比实录更为详赡")
        print("  [OCR与标点修复] p283-284：核原书补实录院同修撰出处"
              "右括号，恢复李焘名及日历所‘铨次’‘详赡’")

        meeting_minutes_reader, _ = by_name["编修会要所检阅文字"]
        assert "则下笔官" in meeting_minutes_reader["text"]
        meeting_minutes_reader["text"] = meeting_minutes_reader["text"].replace(
            "则下笔官", "即下笔官",
        )
        general_supervisor, _ = by_name["都大提举诸司官"]
        assert "（乾道四年)" in general_supervisor["text"]
        assert general_supervisor["text"].endswith("18之32)")
        general_supervisor["text"] = general_supervisor["text"].replace(
            "（乾道四年)", "（乾道四年）",
        )[:-1] + "）"

        receiver, _ = by_name["承受官"]
        false_supervisor_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "提举诸司" and str(meta.get("page")) == "286"
            and meta.get("status") == "from_surname"
        ]
        assert len(false_supervisor_matches) == 1
        false_supervisor, false_supervisor_meta = false_supervisor_matches[0]
        assert receiver["text"].endswith("位次于都大")
        assert false_supervisor["text"] == "官、高于主管诸司官。"
        receiver["text"] += false_supervisor["name"] + false_supervisor["text"]
        receiver["简称"] = false_supervisor["简称"]
        false_supervisor.clear()
        false_supervisor.update({
            "name": "提举诸司", "text": "", "_placeholder": True,
        })
        false_supervisor_meta["status"] = "placeholder"
        false_supervisor_meta.pop("from_surname", None)

        long_distance_courier, _ = by_name["投送文字大程官"]
        assert long_distance_courier["text"].startswith("更名。")
        long_distance_courier["text"] = (
            "吏名。" + long_distance_courier["text"][3:]
        )
        print("  [跨页与OCR修复] p285-286：恢复会要所检阅文字‘即下笔官’、"
              "都大提举诸司引文括号，将伪条目‘提举诸司’续文和简称归回"
              "承受官，并恢复投送文字大程官‘吏名’")

        historian, _ = by_name["史官"]
        assert "《攻瑰集》" in historian["text"]
        assert historian["别称"].startswith("耳笔。")
        historian["text"] = historian["text"].replace(
            "《攻瑰集》", "《攻媿集》",
        )
        historian["别称"] = "珥笔。" + historian["别称"][3:]

        palace_service, _ = by_name["殿中省"]
        palace_history = palace_service["职源与沿革"]
        assert "是为之始《隋书" in palace_history
        assert "正月四日罢《十朝纲要》" in palace_history
        palace_service["职源与沿革"] = palace_history.replace(
            "是为之始《隋书", "是为之始（《隋书",
        ).replace("正月四日罢《十朝纲要》", "正月四日罢（《十朝纲要》")
        assert "祫祫" in palace_service["职掌"]
        palace_service["职掌"] = palace_service["职掌"].replace(
            "祫祫", "禘祫",
        )
        judge_palace, _ = by_name["判殿中省事"]
        assert "祫洽" in judge_palace["text"]
        judge_palace["text"] = judge_palace["text"].replace(
            "祫洽", "禘祫",
        )

        palace_vice_director, _ = by_name["殿中省少监"]
        assert "《虞史》" in palace_vice_director["职源与沿革"]
        assert "《鏖史》" in palace_vice_director["简称"]
        palace_vice_director["职源与沿革"] = palace_vice_director[
            "职源与沿革"
        ].replace("《虞史》", "《麈史》")
        palace_vice_director["简称"] = palace_vice_director["简称"].replace(
            "《鏖史》", "《麈史》",
        )
        palace_assistant, _ = by_name["殿中省丞"]
        assert "《塵史》" in palace_assistant["职掌"]
        palace_assistant["职掌"] = palace_assistant["职掌"].replace(
            "《塵史》", "《麈史》",
        )

        palace_clerk, _ = by_name["令史"]
        assert "谱练" in palace_clerk["text"]
        palace_clerk["text"] = palace_clerk["text"].replace(
            "谱练", "谙练",
        )
        copy_clerk, _ = by_name["贴司"]
        assert "谱练行遣" in copy_clerk["text"]
        copy_clerk["text"] = copy_clerk["text"].replace(
            "谱练行遣", "谙练行遣",
        )
        imperial_food, _ = by_name["尚食局"]
        assert "膳餳" in imperial_food["职掌"]
        imperial_food["职掌"] = imperial_food["职掌"].replace(
            "膳餳", "膳羞",
        )
        imperial_kitchen, _ = by_name["太官局"]
        assert imperial_kitchen["text"] == "官司名。隶殿中省尚食局"
        assert "膳徒三十（" in imperial_kitchen["编制"]
        imperial_kitchen["text"] += "。"
        imperial_kitchen["编制"] = imperial_kitchen["编制"].replace(
            "膳徒三十（", "膳徒三十人（",
        )
        print("  [OCR字误] p286-289：核原书恢复史官‘珥笔’与《攻媿集》、"
              "殿中省‘禘祫’及出处括号、《麈史》、‘谙练’、尚食局‘膳羞’，"
              "并补太官局句号与‘膳徒三十人’")

        imperial_carriage, _ = by_name["尚辇局"]
        assert "……日尚辇" in imperial_carriage["简称"]
        imperial_carriage["简称"] = imperial_carriage["简称"].replace(
            "……日尚辇", "……曰尚辇",
        )
        imperial_stable, _ = by_name["尚乘局"]
        broken_stable_history = (
            "《建隆以后合班之制》、《元丰以后合班之制》，"
            "而另新增尚酝局（《分纪》卷24）。"
        )
        assert broken_stable_history in imperial_stable["职源与沿革"]
        imperial_stable["职源与沿革"] = imperial_stable[
            "职源与沿革"
        ].replace(
            broken_stable_history,
            "《建隆以后合班之制》、《元丰以后合班之制》），"
            "而另新增尚酝局（《分纪》卷24）。",
        )

        bureau_manager, _ = by_name["管勾殿中省某局"]
        controller_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "典范" and str(meta.get("page")) == "291"
            and meta.get("status") == "placeholder"
        ]
        assert len(controller_matches) == 1
        controller, controller_meta = controller_matches[0]
        embedded_controller_marker = "典御 职事官名。"
        assert embedded_controller_marker in bureau_manager["简称与别名"]
        manager_alias, controller_text = bureau_manager["简称与别名"].split(
            embedded_controller_marker, 1,
        )
        bureau_manager["简称与别名"] = manager_alias.rstrip()
        controller.clear()
        controller.update({
            "name": "典御",
            "text": "职事官名。" + controller_text,
        })
        for key in ("职源与沿革", "职掌", "编制", "品位", "合称"):
            assert key in bureau_manager
            controller[key] = bureau_manager.pop(key)
        controller_meta["name"] = "典御"
        controller_meta["status"] = "ok"

        gate_guard, _ = by_name["监门"]
        assert gate_guard["text"].endswith("同前书19之10）。")
        assert "19之4、5、6)" in gate_guard["text"]
        gate_guard["text"] = gate_guard["text"].replace(
            "19之4、5、6)", "19之4、5、6）",
        )
        physician, _ = by_name["医师"]
        assert "名医充政和二年" in physician["品位"]
        physician["品位"] = physician["品位"].replace(
            "名医充政和二年", "名医充。政和二年",
        )
        print("  [嵌入拆分与OCR修复] p290-292：将被管勾殿中省某局别名字段"
              "吞入的‘典御’拆回独立条目，恢复尚辇局‘曰尚辇’、尚乘局括号、"
              "监门引文右括号及医师品位句号")

        garment_craftsman, _ = by_name["典功"]
        assert "輞头、衣帽" in garment_craftsman["text"]
        garment_craftsman["text"] = garment_craftsman["text"].replace(
            "輞头、衣帽", "幞头、衣帽",
        )

        garment_attendant, _ = by_name["衣徒"]
        curtain_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "幂士" and str(meta.get("page")) == "293"
            and meta.get("status") == "placeholder"
        ]
        assert len(curtain_matches) == 1
        curtain_attendant, curtain_meta = curtain_matches[0]
        embedded_curtain_marker = "幕士 公吏名。"
        assert embedded_curtain_marker in garment_attendant["text"]
        garment_text, curtain_text = garment_attendant["text"].split(
            embedded_curtain_marker, 1,
        )
        garment_attendant["text"] = garment_text.rstrip()
        curtain_attendant.clear()
        curtain_attendant.update({
            "name": "幕士",
            "text": "公吏名。" + curtain_text,
        })
        curtain_meta["name"] = "幕士"
        curtain_meta["status"] = "ok"

        clothing_store_supervisor, _ = by_name["监尚衣库"]
        broken_clothing_store_citation = (
            "（《宋会要·职官》19之2《宋会要·食货》52之25《尚衣库》）。"
        )
        assert broken_clothing_store_citation in clothing_store_supervisor["text"]
        clothing_store_supervisor["text"] = clothing_store_supervisor["text"].replace(
            broken_clothing_store_citation,
            "（《宋会要·职官》19之2、《宋会要·食货》52之25《尚衣库》）。",
        )
        print("  [嵌入拆分与OCR修复] p292-293：恢复典功‘幞头’，将被衣徒"
              "吞入的‘幕士’拆回独立条目，并补监尚衣库两处出处间顿隔")

        new_clothing_store, _ = by_name["监新衣库"]
        tailoring_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "栽造院" and str(meta.get("page")) == "294"
            and meta.get("status") == "placeholder"
        ]
        assert len(tailoring_matches) == 1
        tailoring_office, tailoring_meta = tailoring_matches[0]
        embedded_tailoring_marker = "裁造院 官司名。"
        assert embedded_tailoring_marker in new_clothing_store["简称"]
        store_alias, tailoring_text = new_clothing_store["简称"].split(
            embedded_tailoring_marker, 1,
        )
        new_clothing_store["简称"] = store_alias.rstrip()
        tailoring_office.clear()
        tailoring_office.update({
            "name": "裁造院",
            "text": "官司名。" + tailoring_text,
        })
        tailoring_meta["name"] = "裁造院"
        tailoring_meta["status"] = "ok"
        print("  [嵌入拆分] p294：将被监新衣库简称字段吞入的‘裁造院’"
              "拆回独立条目，并恢复误识标题‘栽造院’")

        acting_history, _ = by_name["权提举国史院"]
        continuation_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "国史院" and str(meta.get("page")) == "281"
            and meta.get("status") == "not_in_catalog"
        ]
        assert len(continuation_matches) == 1
        continuation, continuation_meta = continuation_matches[0]
        assert acting_history["text"].endswith("由参知政事兼领")
        assert continuation["text"].startswith("者，带“权”字。")
        acting_history["text"] += continuation["text"]
        acting_history["简称"] = continuation["简称"]
        continuation.clear()
        continuation.update({
            "name": "国史院", "text": "", "_placeholder": True,
        })
        continuation_meta["status"] = "placeholder"
        continuation_meta.pop("not_in_catalog", None)
        print("  [跨栏与OCR修复] p279-281：恢复楷书‘誊抄’、"
              "《挥麈后录》，并将国史院伪条目续文并回权提举国史院")

        meal_case, _ = by_name["祠祭生料知杂案"]
        assert "膿部司" in meal_case["text"] and "飪饥" in meal_case["text"]
        meal_case["text"] = meal_case["text"].replace(
            "膿部司", "膳部司",
        ).replace("飪饥", "饔饩")
        banquet_case, _ = by_name["宴设馆客供进给赐案"]
        wrong_banquet_citation = "（《宋会要·职官》）13之43）。"
        assert wrong_banquet_citation in banquet_case["text"]
        banquet_case["text"] = banquet_case["text"].replace(
            wrong_banquet_citation, "（《宋会要·职官》13之43）。",
        )
        tribute_office, _ = by_name["礼部贡院"]
        assert tribute_office["text"] == "官司名。隶尚书省礼部"
        tribute_office["text"] += "。"
        print("  [OCR字误] p239：核原书恢复‘膳部司’‘祠祭饔饩’，修正宴设案"
              "出处括号并补礼部贡院正文句号")

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

        back_office, _ = by_name["中书后省"]
        wrong_case = "设案四：上案、下案、制造、记注案。"
        assert wrong_case in back_office["编制"]
        back_office["编制"] = back_office["编制"].replace(
            wrong_case,
            "设案四：上案、下案、制诰、记注案。",
        )
        print("  [OCR字误] '中书后省'(p187)：核原书将南宋四案中的‘制造’恢复为‘制诰’")

        room_post, room_meta = by_name["中书检正逐房（吏、户、礼刑、孔目房)公事"]
        bogus_zhongshu, bogus_meta = by_name["中书"]
        assert room_post.get("_placeholder") is True
        assert bogus_zhongshu.get("_from_surname") is True
        assert bogus_zhongshu.get("text") == "检正逐房（吏、户、礼、刑、孔目房）公事 宰属官名。"
        for key, value in list(bogus_zhongshu.items()):
            if key in ("name", "_from_surname"):
                continue
            room_post[key] = value
        room_post["name"] = "中书检正逐房（吏、户、礼、刑、孔目房）公事"
        room_post.pop("_placeholder", None)
        room_meta["name"] = room_post["name"]
        room_meta["status"] = "ok"
        bogus_zhongshu.clear()
        bogus_zhongshu.update({"name": "中书", "text": "", "_placeholder": True})
        bogus_meta["status"] = "placeholder"
        print("  [跨栏归位] '中书检正逐房公事'(p191)：正文从误切伪条目‘中书’移回，"
              "并保留空占位以稳定后续词条ID")

        right_remonstrance, _ = by_name["右谏议大夫"]
        wrong_origin = "谭议大夫始置于后汉"
        assert wrong_origin in right_remonstrance["职源"]
        right_remonstrance["职源"] = right_remonstrance["职源"].replace(
            wrong_origin,
            "谏议大夫始置于后汉",
        )
        print("  [OCR字误] '右谏议大夫'(p189)：核原书将‘谭议大夫’恢复为‘谏议大夫’")

        book_clerk_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "书令吏" and str(meta.get("page")) == "192"
        ]
        assert len(book_clerk_matches) == 1
        book_clerk, book_clerk_meta = book_clerk_matches[0]
        book_clerk["name"] = "书令史"
        book_clerk_meta["name"] = "书令史"
        print("  [OCR字误] '书令史'(p192)：核原书将误识标题‘书令吏’恢复为‘书令史’")

        two_assistants_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "二丞" and str(meta.get("page")) == "贰丞"
        ]
        assert len(two_assistants_matches) == 1
        _, two_assistants_meta = two_assistants_matches[0]
        two_assistants_meta["page"] = "198"
        print("  [页码归位] '二丞'(p198)：标题同行异写‘贰丞’误作页码，恢复原书页码198")

    if PROFILE_NAME == "5t7":
        temple_deputies = next(e for e in all_entries if e["name"] == "寺监副贰")
        wrong_deputy = "元丰五年新制，九寺副贰，仍为九寺少监"
        assert wrong_deputy in temple_deputies["text"]
        temple_deputies["text"] = temple_deputies["text"].replace(
            wrong_deputy, "元丰五年新制，九寺副贰，仍为九寺少卿"
        )
        print("  [OCR字误] '寺监副贰'(p295)：核第五编原页恢复‘九寺少卿’")

        seven_temple_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "七寺"
            and str(meta.get("page")) == "297"
            and entry.get("text", "").startswith("宋代九寺")
        ]
        assert len(seven_temple_matches) == 1
        seven_temple, seven_temple_meta = seven_temple_matches[0]
        seven_temple.pop("_not_in_catalog", None)
        seven_temple_meta["status"] = "ok"
        seven_temple_meta.pop("not_in_catalog", None)

        seven_minister_matches = [
            (entry, meta)
            for entry, meta in zip(all_entries, all_meta)
            if entry["name"] == "七寺"
            and str(meta.get("page")) == "297"
            and re.match(r"^\s*卿\s+", entry.get("text", ""))
        ]
        assert len(seven_minister_matches) == 1
        seven_minister, seven_minister_meta = seven_minister_matches[0]
        assert re.match(r"^\s*卿\s+", seven_minister["text"]), repr(
            seven_minister["text"][:40]
        )
        seven_minister["name"] = "七寺卿"
        seven_minister["text"] = re.sub(
            r"^\s*卿\s+", "", seven_minister["text"], count=1
        )
        seven_minister.pop("_not_in_catalog", None)
        seven_minister_meta["name"] = "七寺卿"
        seven_minister_meta["status"] = "ok"
        print("  [标题归位] '七寺卿'(p297)：正文标题被较短目录词头‘七寺’截断，"
              "恢复独立词条并移除正文首字‘卿’")

        judge_taichang = next(e for e in all_entries if e["name"] == "判太常寺")
        combined_history = judge_taichang["职源与沿革"]
        duty_marker = "\n职掌 "
        assert duty_marker in combined_history
        history, duty = combined_history.split(duty_marker, 1)
        judge_taichang["职源与沿革"] = history
        judge_taichang["职掌"] = duty
        print("  [字段归位] '判太常寺'(p298)：将粘在职源与沿革末尾的职掌段拆回"
              "独立‘职掌’字段")

        taichang = next(e for e in all_entries if e["name"] == "太常寺")
        assert "奉礼部" in taichang["编制"]
        taichang["编制"] = taichang["编制"].replace("奉礼部", "奉礼郎")
        taichang_minister = next(e for e in all_entries if e["name"] == "太常寺卿")
        assert "坛壻" in taichang_minister["职掌"]
        taichang_minister["职掌"] = taichang_minister["职掌"].replace(
            "坛壻", "坛壝"
        )
        print("  [OCR字误] '太常寺/太常寺卿'(p297-298)：核原书恢复‘奉礼郎’与"
              "‘坛壝’")

        ritual_officer = next(e for e in all_entries if e["name"] == "太常寺奉礼郎")
        rank_and_staff = ritual_officer["品位"]
        staff_marker = "编制 元丰新制一人"
        assert staff_marker in rank_and_staff
        rank, staff = rank_and_staff.split("编制 ", 1)
        ritual_officer["品位"] = rank.rstrip()
        ritual_officer["编制"] = staff
        print("  [字段归位] '太常寺奉礼郎'(p300)：将粘在品位末尾的编制段拆回"
              "独立‘编制’字段")

        suburban_officer = next(e for e in all_entries if e["name"] == "郊社局令")
        assert "四郊坛壇" in suburban_officer["职掌"]
        suburban_officer["职掌"] = suburban_officer["职掌"].replace(
            "四郊坛壇", "四郊坛壝"
        )
        print("  [OCR字误] '郊社局令'(p301)：核原书恢复‘四郊坛壝’")

        funeral_assistant = next(e for e in all_entries if e["name"] == "挽郎")
        assert "葫补官名" in funeral_assistant["text"]
        funeral_assistant["text"] = funeral_assistant["text"].replace(
            "葫补官名", "荫补官名"
        )
        print("  [OCR字误] '挽郎'(p304)：核第五编原页恢复‘荫补官名’")

        teaching_control = next(e for e in all_entries if e["name"] == "钤辖教坊所")
        control_post = next(e for e in all_entries if e["name"] == "钤辖教坊")
        assert control_post.get("_placeholder") is True
        combined = teaching_control["品位"]
        rank_marker = "\n编制 "
        post_marker = "钤辖教坊 差遣官。"
        assert rank_marker in combined and post_marker in combined
        rank, tail = combined.split(rank_marker, 1)
        roster, post_text = tail.split(post_marker, 1)
        teaching_control["品位"] = rank
        teaching_control["编制"] = roster.replace("铃辖官", "钤辖官")
        control_post["text"] = "差遣官。" + post_text
        control_post["简称"] = teaching_control.pop("简称").replace("铃辖", "钤辖")
        control_post.pop("_placeholder", None)
        control_post_meta = all_meta[all_entries.index(control_post)]
        control_post_meta["status"] = "ok"
        print("  [字段归位] '钤辖教坊所/钤辖教坊'(p307)：拆回所的编制字段及"
              "独立差遣官正文、简称，并核原书恢复‘钤辖’字形")

        yamen_music_i = next(
            i for i, e in enumerate(all_entries) if e["name"] == "衙前乐"
        )
        yamen_music_meta = all_meta[yamen_music_i]
        all_entries.insert(
            yamen_music_i + 1,
            {"name": "衙前", "text": "", "_placeholder": True},
        )
        all_meta.insert(
            yamen_music_i + 1,
            {
                "name": "衙前", "page": "307",
                "h1": yamen_music_meta["h1"], "h2": yamen_music_meta["h2"],
                "h3": yamen_music_meta["h3"], "status": "placeholder",
            },
        )
        print("  [ID占位] '衙前'(p307)：真实正文已归回‘衙前乐’，原多出条目位"
              "保留为空占位，避免第93条以后既有辞典ID整体前移")

        medical_office = next(e for e in all_entries if e["name"] == "提举太医局所")
        medical_supervisor = next(e for e in all_entries if e["name"] == "提举太医局")
        assert medical_supervisor.get("_placeholder") is True
        post_marker = "提举太医局 差遣名。"
        assert post_marker in medical_office["text"]
        office_text, post_text = medical_office["text"].split(post_marker, 1)
        medical_office["text"] = office_text.rstrip()
        medical_supervisor["text"] = "差遣名。" + post_text
        medical_supervisor["简称"] = medical_office.pop("简称")
        medical_supervisor.pop("_placeholder", None)
        medical_supervisor_meta = all_meta[all_entries.index(medical_supervisor)]
        medical_supervisor_meta["status"] = "ok"
        print("  [条目拆分] '提举太医局所/提举太医局'(p311)：按原书独立标题"
              "拆回官司与差遣官正文，简称归入差遣官条")

        registry = next(e for e in all_entries if e["name"] == "宗正寺主簿")
        continuation_matches = [
            (e, m) for e, m in zip(all_entries, all_meta)
            if e["name"] == "主簿" and e.get("text") == "一员。”"
            and str(m.get("page")) == "316" and m.get("status") == "not_in_catalog"
        ]
        assert len(continuation_matches) == 1
        continuation, continuation_meta = continuation_matches[0]
        assert registry["简称"].endswith("宗正并省")
        registry["简称"] += continuation["text"]
        continuation.clear()
        continuation.update({"name": "主簿", "text": "", "_placeholder": True})
        continuation_meta["status"] = "placeholder"
        print("  [跨页续文] '宗正寺主簿/主簿'(p315-316)：将简称引文末句"
              "‘宗正并省一员’并回第166条，第167条保留为空占位")

        kuaiji = next(
            e for e in all_entries if e["name"] == "知会稽县事兼主管攒宫事务"
        )
        assert kuaiji["text"].startswith("兴二十九年九月十日置")
        kuaiji["text"] = "绍" + kuaiji["text"]
        print("  [OCR漏字] '知会稽县事兼主管攒宫事务'(p317)：核原书补回"
              "句首‘绍’，恢复‘绍兴二十九年九月十日置’")

        palace_supervisor = next(e for e in all_entries if e["name"] == "攒宫都监")
        palace_inspection = next(e for e in all_entries if e["name"] == "检察宫陵所")
        assert palace_inspection.get("_placeholder") is True
        inspection_marker = "检察官陵所 官司名。隶宗正司。"
        assert inspection_marker in palace_supervisor["text"]
        supervisor_text, _ = palace_supervisor["text"].split(inspection_marker, 1)
        palace_supervisor["text"] = supervisor_text.rstrip()
        palace_inspection["text"] = "官司名。隶宗正司。"
        palace_inspection["职源"] = palace_supervisor.pop("职源")
        palace_inspection["职掌"] = palace_supervisor.pop("职掌").replace(
            "诸攒官司", "诸攒宫司"
        )
        palace_inspection.pop("_placeholder", None)
        inspection_meta = all_meta[all_entries.index(palace_inspection)]
        inspection_meta["status"] = "ok"
        print("  [条目拆分] '攒宫都监/检察宫陵所'(p317-318)：按原书独立标题"
              "拆回检察宫陵所正文、职源与职掌，并恢复‘宫’字")

        household_case = next(e for e in all_entries if e["name"] == "户案")
        ritual_case = next(e for e in all_entries if e["name"] == "仪案")
        ritual_marker = "仪案 大宗正司办事机构之一。"
        if ritual_case.get("_placeholder") is True:
            assert ritual_marker in household_case["text"]
            household_text, ritual_text = household_case["text"].split(
                ritual_marker, 1
            )
            household_case["text"] = household_text.rstrip()
            ritual_case["text"] = "大宗正司办事机构之一。" + ritual_text
            ritual_case.pop("_placeholder", None)
            ritual_meta = all_meta[all_entries.index(ritual_case)]
            ritual_meta["status"] = "ok"
        else:
            assert ritual_marker not in household_case["text"]
            assert ritual_case["text"].startswith("大宗正司办事机构之一。")

        military_case = next(e for e in all_entries if e["name"] == "兵案")
        criminal_case = next(e for e in all_entries if e["name"] == "刑案")
        criminal_marker = "刑案 大宗正司办事机构之一。"
        if criminal_case.get("_placeholder") is True:
            assert criminal_marker in military_case["text"]
            military_text, criminal_text = military_case["text"].split(
                criminal_marker, 1
            )
            military_case["text"] = military_text.rstrip()
            criminal_case["text"] = "大宗正司办事机构之一。" + criminal_text
            criminal_case.pop("_placeholder", None)
            criminal_meta = all_meta[all_entries.index(criminal_case)]
            criminal_meta["status"] = "ok"
        else:
            assert criminal_marker not in military_case["text"]
            assert criminal_case["text"].startswith("大宗正司办事机构之一。")
        print("  [条目拆分] '户案/仪案、兵案/刑案'(p320)：按原书独立标题"
              "拆回大宗正司仪案与刑案正文，并恢复目录误识字形")

        for page_title in ("绍兴府大宗正行司", "主管宗室财用", "教授"):
            page_matches = [
                m for e, m in zip(all_entries, all_meta)
                if e["name"] == page_title and str(m.get("page")) == "32"
            ]
            assert len(page_matches) == 1, (page_title, page_matches)
            page_meta = page_matches[0]
            page_meta["page"] = "321"
        print("  [页码归位] '绍兴府大宗正行司/主管宗室财用/教授'(p321)："
              "核原书补回目录 OCR 漏失的末位页码‘1’")

        front_clerk = next(e for e in all_entries if e["name"] == "前行")
        assert "(《(宋会要·职官》20之20)" in front_clerk["text"]
        front_clerk["text"] = front_clerk["text"].replace(
            "(《(宋会要·职官》20之20)", "(《宋会要·职官》20之20)", 1
        )
        print("  [OCR符号] '前行'(p320)：核原书恢复引书括号次序")

        guanglu_registry = next(e for e in all_entries if e["name"] == "光禄寺主簿")
        combined_staff = guanglu_registry["编制"]
        alias_marker = "\n简称 "
        assert alias_marker in combined_staff
        staff, aliases = combined_staff.split(alias_marker, 1)
        guanglu_registry["编制"] = staff.rstrip()
        guanglu_registry["简称"] = aliases
        print("  [字段归位] '光禄寺主簿'(p326)：将粘在编制末尾的简称段拆回"
              "独立‘简称’字段")

        inner_material_store = next(e for e in all_entries if e["name"] == "内物料库")
        combined_text = inner_material_store["text"]
        history_marker = "\n职源与沿革 "
        assert history_marker in combined_text
        summary, history = combined_text.split(history_marker, 1)
        inner_material_store["text"] = summary.rstrip()
        inner_material_store["职源与沿革"] = history
        print("  [字段归位] '内物料库'(p329)：将粘在正文末尾的职源与沿革段拆回"
              "独立‘职源与沿革’字段")

        weiyu_deputy = next(e for e in all_entries if e["name"] == "卫尉寺少卿")
        combined_staff = weiyu_deputy["编制"]
        alias_marker = "\n简称 "
        assert alias_marker in combined_staff
        staff_text, aliases = combined_staff.split(alias_marker, 1)
        weiyu_deputy["编制"] = staff_text.rstrip()
        weiyu_deputy["简称"] = aliases
        print("  [字段归位] '卫尉寺少卿'(p332)：将粘在编制末尾的简称段拆回"
              "独立‘简称’字段")

        right_street = next(e for e in all_entries if e["name"] == "知右街司事")
        street_continuations = [
            (e, m) for e, m in zip(all_entries, all_meta)
            if e["name"] == "街司" and str(m.get("page")) == "337"
            and m.get("status") == "from_surname"
        ]
        assert len(street_continuations) == 1
        street_tail, street_tail_meta = street_continuations[0]
        assert right_street["text"] == "差遣名。以诸司使充。领右"
        assert street_tail["text"] == "事(《宋会要·职官》22之13)。"
        right_street["text"] += street_tail["name"] + street_tail["text"]
        street_tail.clear()
        street_tail.update({"name": "街司", "text": "", "_placeholder": True})
        street_tail_meta["status"] = "placeholder"
        print("  [跨页续文] '知右街司事/街司'(p336-337)：将页首续文"
              "‘街司事’并回第373条，第374条保留为空占位")

        golden_guard = next(
            e for e in all_entries if e["name"] == "左、右金吾引驾仗司"
        )
        combined_duty = golden_guard["职掌"]
        roster_marker = "编制 "
        assert roster_marker in combined_duty
        duty_text, roster_text = combined_duty.split(roster_marker, 1)
        golden_guard["职掌"] = duty_text.rstrip()
        golden_guard["编制"] = roster_text
        print("  [字段归位] '左、右金吾引驾仗司'(p337)：将粘在职掌末尾的"
              "编制段拆回独立‘编制’字段")

        judge_guard = next(
            e for e in all_entries if e["name"] == "判左、右金吾引驾仗司事"
        )
        combined_text = judge_guard["text"]
        alias_marker = "\n简称 "
        assert alias_marker in combined_text
        body_text, aliases = combined_text.split(alias_marker, 1)
        judge_guard["text"] = body_text.rstrip()
        judge_guard["简称"] = aliases
        print("  [字段归位] '判左、右金吾引驾仗司事'(p337)：将粘在正文末尾的"
              "简称段拆回独立‘简称’字段")

        street_guard_manager = next(
            e for e in all_entries
            if e["name"] == "勾当左右金吾街仗、六军仪仗司事"
        )
        street_guard_executor = next(
            e for e in all_entries if e["name"] == "干办左、右金吾街仗司事"
        )
        assert street_guard_executor.get("_placeholder") is True
        executor_marker = "南宋改勾当官为干办官。"
        assert executor_marker in street_guard_manager["text"]
        manager_text, executor_text = street_guard_manager["text"].split(
            executor_marker, 1
        )
        street_guard_manager["text"] = manager_text.rstrip()
        street_guard_executor["text"] = executor_marker + executor_text
        street_guard_executor.pop("_placeholder", None)
        executor_meta = all_meta[all_entries.index(street_guard_executor)]
        executor_meta["status"] = "ok"
        print("  [条目拆分] '勾当左右金吾街仗、六军仪仗司事/"
              "干办左、右金吾街仗司事'(p338)：按目录独立词头拆回南宋干办官正文")

        color_official = next(e for e in all_entries if e["name"] == "四色官")
        sacrificial_spear = next(e for e in all_entries if e["name"] == "穰稍官")
        assert sacrificial_spear.get("_placeholder") is True
        spear_marker = "穣稍官 "
        assert spear_marker in color_official["text"]
        color_text, spear_text = color_official["text"].split(spear_marker, 1)
        color_official["text"] = color_text.rstrip()
        sacrificial_spear["text"] = spear_text
        sacrificial_spear.pop("_placeholder", None)
        spear_meta = all_meta[all_entries.index(sacrificial_spear)]
        spear_meta["status"] = "ok"
        print("  [条目拆分] '四色官/穰稍官'(p338)：将 OCR 连写的穣稍官正文"
              "拆回目录占位，条目名按目录规范字形‘穰’保留")

        escort_grade = next(e for e in all_entries if e["name"] == "管押节级")
        service_grade = next(e for e in all_entries if e["name"] == "祇应节级")
        assert service_grade.get("_placeholder") is True
        service_marker = "祗应节级 武职名。"
        assert service_marker in escort_grade["text"]
        escort_text, service_text = escort_grade["text"].split(service_marker, 1)
        escort_grade["text"] = escort_text.rstrip()
        service_grade["text"] = "武职名。" + service_text
        service_grade.pop("_placeholder", None)
        service_meta = all_meta[all_entries.index(service_grade)]
        service_meta["status"] = "ok"
        print("  [条目拆分] '管押节级/祇应节级'(p346)：将 OCR 连写的"
              "祗应节级正文拆回目录占位，条目名按目录规范字形‘祇’保留")

        long_grade = next(e for e in all_entries if e["name"] == "下都辇官长行")
        down_official = next(e for e in all_entries if e["name"] == "下都辇官")
        generic_official = next(e for e in all_entries if e["name"] == "孽官")
        assert down_official.get("_placeholder") is True
        assert generic_official.get("_placeholder") is True
        down_marker = "下都辇官 应奉人。"
        assert down_marker in long_grade["text"]
        long_text, down_text = long_grade["text"].split(down_marker, 1)
        long_grade["text"] = long_text.rstrip()
        down_official["text"] = "应奉人。" + down_text
        down_official.pop("_placeholder", None)
        combined_aliases = long_grade.pop("简称")
        generic_marker = "辇官 挚官院所属"
        assert generic_marker in combined_aliases
        down_aliases, generic_text = combined_aliases.split(generic_marker, 1)
        down_official["简称"] = down_aliases.rstrip()
        generic_official["text"] = "御辇院所属" + generic_text
        generic_official.pop("_placeholder", None)
        for restored in (down_official, generic_official):
            restored_meta = all_meta[all_entries.index(restored)]
            restored_meta["status"] = "ok"
        print("  [条目拆分] '下都辇官长行/下都辇官/辇官'(p347)："
              "核原书拆回三个独立词条，并恢复‘御辇院’OCR误字")

        royal_stable = next(e for e in all_entries if e["name"] == "御前马院")
        riding_staff = next(e for e in all_entries if e["name"] == "御前马院习马使效")
        assert riding_staff.get("_placeholder") is True
        riding_marker = "前马院供职骑习御马祗应者"
        aliases = royal_stable["简称"]
        assert riding_marker in aliases
        stable_aliases, riding_tail = aliases.split(riding_marker, 1)
        royal_stable["简称"] = stable_aliases.rstrip()
        riding_staff["text"] = "诸军将校差在御前马院供职骑习御马祗应者" + riding_tail
        riding_staff.pop("_placeholder", None)
        riding_meta = all_meta[all_entries.index(riding_staff)]
        riding_meta["status"] = "ok"
        print("  [条目拆分] '御前马院/御前马院习马使效'(p347-348)："
              "核原书将跨页正文从御前马院简称字段拆回独立词条")

        temple_manager = next(e for e in all_entries if e["name"] == "提点在京寺务司")
        manager_office = next(e for e in all_entries if e["name"] == "提点在京寺务所")
        assert manager_office.get("_placeholder") is True
        combined_aliases = temple_manager["简称"]
        office_marker = "务司官办事机构"
        assert office_marker in combined_aliases
        manager_aliases, office_tail = combined_aliases.split(office_marker, 1)
        temple_manager["简称"] = manager_aliases.rstrip()
        office_body = "提点在京寺务司官办事机构" + office_tail
        alias_marker = "提点所。"
        assert alias_marker in office_body
        body_text, office_aliases = office_body.split(alias_marker, 1)
        manager_office["text"] = "官司名。" + body_text.rstrip()
        manager_office["简称"] = alias_marker + office_aliases
        manager_office.pop("_placeholder", None)
        manager_office_meta = all_meta[all_entries.index(manager_office)]
        manager_office_meta["status"] = "ok"
        print("  [条目拆分] '提点在京寺务司/提点在京寺务所'(p352)："
              "核原书将提点官办事机构及简称拆回独立词条")

        monk_office = next(e for e in all_entries if e["name"] == "僧正司")
        monk_post = next(e for e in all_entries if e["name"] == "僧正")
        assert monk_post.get("_placeholder") is True
        post_marker = "僧正 僧官名。"
        assert post_marker in monk_office["简称"]
        office_aliases, post_tail = monk_office["简称"].split(post_marker, 1)
        assert not post_tail.strip()
        monk_office["简称"] = office_aliases.rstrip()
        duty_marker = "僧正司主管官。"
        assert duty_marker in monk_office["职掌"]
        office_duty, post_duty = monk_office["职掌"].split(duty_marker, 1)
        monk_office["职掌"] = office_duty.rstrip()
        monk_post["text"] = "僧官名。"
        monk_post["职源"] = monk_office.pop("职源")
        monk_post["职掌"] = duty_marker + post_duty
        monk_post.pop("_placeholder", None)
        monk_post_meta = all_meta[all_entries.index(monk_post)]
        monk_post_meta["status"] = "ok"
        print("  [条目拆分] '僧正司/僧正'(p353)：核原书将僧官词条的"
              "释义、职源与职掌从僧正司字段拆回目录占位")

        virtue_office = next(e for e in all_entries if e["name"] == "道德院")
        wrong_subject = "北宋徽宗宣和元年改名德士司"
        assert wrong_subject in virtue_office["text"]
        virtue_office["text"] = virtue_office["text"].replace(
            wrong_subject, "北宋徽宗宣和元年由左、右街道录院改名", 1
        )
        print("  [OCR串条] '道德院'(p354)：据本条引文将误串的佛教机构"
              "‘德士司’恢复为改名前身‘左、右街道录院’")

        taoist_office = next(e for e in all_entries if e["name"] == "道正司")
        taoist_post = next(e for e in all_entries if e["name"] == "道正")
        assert taoist_post.get("_placeholder") is True
        taoist_post_marker = "道正 道官名。"
        assert taoist_post_marker in taoist_office["职掌"]
        office_duty, post_duty = taoist_office["职掌"].split(
            taoist_post_marker, 1
        )
        taoist_office["职掌"] = office_duty.rstrip()
        taoist_post["text"] = "道官名。"
        taoist_post["职掌"] = post_duty
        taoist_post.pop("_placeholder", None)
        taoist_post_meta = all_meta[all_entries.index(taoist_post)]
        taoist_post_meta["status"] = "ok"
        print("  [条目拆分] '道正司/道正'(p354)：按原书独立标题将道正官名、"
              "职掌及置额从道正司职掌字段拆回目录占位")

        chief_taoist = next(e for e in all_entries if e["name"] == "左、右街")
        chief_taoist_meta = all_meta[all_entries.index(chief_taoist)]
        assert chief_taoist.get("_catalog_name") == "左右街都道录"
        assert chief_taoist_meta.get("status") == "fuzzy"
        chief_taoist["name"] = "左右街都道录"
        chief_taoist.pop("_catalog_name", None)
        chief_taoist_meta["name"] = "左右街都道录"
        chief_taoist_meta["status"] = "ok"
        chief_taoist_meta.pop("catalog_name", None)
        print("  [标题归位] '左右街都道录'(p355)：正文标题被短目录前缀"
              "‘左、右街’截断，恢复完整正式词头")

        joint_knowledge = next(
            e for e in all_entries if e["name"] == "同知左右街道录院事"
        )
        bogus_joint = next(
            e for e in all_entries
            if e["name"] == "同知" and e.get("_from_surname") is True
        )
        assert joint_knowledge.get("_placeholder") is True
        joint_prefix = "左、右街道录院事 "
        assert bogus_joint["text"].startswith(joint_prefix)
        joint_knowledge["text"] = bogus_joint["text"][len(joint_prefix):]
        joint_knowledge.pop("_placeholder", None)
        joint_meta = all_meta[all_entries.index(joint_knowledge)]
        joint_meta["status"] = "ok"
        bogus_joint.clear()
        bogus_joint.update({"name": "同知", "text": "", "_placeholder": True})
        bogus_joint_meta = all_meta[all_entries.index(bogus_joint)]
        bogus_joint_meta["status"] = "placeholder"
        bogus_joint_meta.pop("from_surname", None)
        print("  [条目归位] '同知左右街道录院事/同知'(p355)：将被简称匹配"
              "拆出的正文并回完整目录词头，原伪条位保留为空占位")

        left_knowledge = next(e for e in all_entries if e["name"] == "知左街道录院事")
        bogus_dudao = next(
            e for e in all_entries
            if e["name"] == "都道" and e.get("_from_surname") is True
        )
        assert left_knowledge["text"].rstrip().endswith("职事官。"), repr(
            left_knowledge["text"][-100:]
        )
        assert bogus_dudao["text"].startswith("旧名：左街道录")
        left_knowledge["text"] = (
            left_knowledge["text"].rstrip() + "都道" + bogus_dudao["text"]
        )
        bogus_dudao.clear()
        bogus_dudao.update({"name": "都道", "text": "", "_placeholder": True})
        bogus_dudao_meta = all_meta[all_entries.index(bogus_dudao)]
        bogus_dudao_meta["status"] = "placeholder"
        bogus_dudao_meta.pop("from_surname", None)
        print("  [跨页续文] '知左街道录院事/都道'(p355)：恢复引文连续句"
              "‘都道旧名：左街道录’，原误拆伪条位保留为空占位")

        for title in ("左街副道录", "右街副道录"):
            post = next(e for e in all_entries if e["name"] == title)
            missing_book_mark = "。宋大诏令集》卷224"
            assert missing_book_mark in post["text"]
            post["text"] = post["text"].replace(
                missing_book_mark, "。《宋大诏令集》卷224", 1
            )
        print("  [OCR符号] '左街副道录/右街副道录'(p356)：核原书补回"
              "《宋大诏令集》的左书名号")

        joint_left_signer = next(
            e for e in all_entries if e["name"] == "同签书左街道录院事"
        )
        assert joint_left_signer["text"].startswith("八年由左街副都监改名")
        joint_left_signer["text"] = "道官名。政和" + joint_left_signer["text"]
        print("  [OCR漏文] '同签书左街道录院事'(p357)：核原书补回句首"
              "‘道官名。政和’")

        zen_office = next(
            e for e in all_entries if e["name"] == "提点崇真圣禅院所"
        )
        bogus_supervisor = next(
            e for e in all_entries
            if e["name"] == "提点" and e.get("_from_surname") is True
        )
        assert zen_office.get("_placeholder") is True
        zen_prefix = "崇真资圣禅院所 "
        assert bogus_supervisor["text"].startswith(zen_prefix)
        zen_office["name"] = "提点崇真资圣禅院所"
        zen_office["text"] = bogus_supervisor["text"][len(zen_prefix):]
        for key, value in bogus_supervisor.items():
            if key not in ("name", "text", "_from_surname", "__status__"):
                zen_office[key] = value
        zen_office.pop("_placeholder", None)
        zen_meta = all_meta[all_entries.index(zen_office)]
        zen_meta["name"] = "提点崇真资圣禅院所"
        zen_meta["status"] = "ok"
        bogus_supervisor.clear()
        bogus_supervisor.update(
            {"name": "提点", "text": "", "_placeholder": True}
        )
        bogus_supervisor_meta = all_meta[all_entries.index(bogus_supervisor)]
        bogus_supervisor_meta["status"] = "placeholder"
        bogus_supervisor_meta.pop("from_surname", None)
        print("  [条目归位] '提点崇真资圣禅院所/提点'(p357)：按原书"
              "恢复完整词头，将误拆正文和字段并回目录位，伪条位保留为空占位")

        agriculture = next(e for e in all_entries if e["name"] == "司农寺")
        missing_parenthesis = "等事《宋会要·职官》26之1、2）"
        assert missing_parenthesis in agriculture["职掌"]
        agriculture["职掌"] = agriculture["职掌"].replace(
            missing_parenthesis, "等事（《宋会要·职官》26之1、2）", 1
        )
        print("  [OCR符号] '司农寺'(p358)：核原书补回宋前期职掌引文前"
              "的左括号")

        agriculture_minister = next(e for e in all_entries if e["name"] == "司农寺卿")
        assert "元丰新制一人《宋会要·职官》26之2）" in agriculture_minister["编制"]
        agriculture_minister["编制"] = agriculture_minister["编制"].replace(
            "元丰新制一人《宋会要·职官》26之2）",
            "元丰新制一人（《宋会要·职官》26之2）",
            1,
        )
        agriculture_deputy = next(
            e for e in all_entries if e["name"] == "司农寺少卿"
        )
        assert "(《宋史·职官志》)9)" in agriculture_deputy["职掌"]
        agriculture_deputy["职掌"] = agriculture_deputy["职掌"].replace(
            "(《宋史·职官志》)9)", "（《宋史·职官志》9）", 1
        )
        agriculture_assistant = next(
            e for e in all_entries if e["name"] == "司农寺丞"
        )
        bad_rank_citation = "(《宋史·职官志》9《元丰以后合班之制》。"
        assert bad_rank_citation in agriculture_assistant["品位"]
        agriculture_assistant["品位"] = agriculture_assistant["品位"].replace(
            bad_rank_citation, "（《宋史·职官志》9《元丰以后合班之制》）。", 1
        )
        print("  [OCR符号] '司农寺卿/少卿/丞'(p359)：核原书恢复编制、"
              "职掌与品位三处引文括号")

        chief_assistant = next(e for e in all_entries if e["name"] == "司农寺都丞")
        combined_rank = chief_assistant["品位"]
        staff_marker = "编制 一员"
        assert staff_marker in combined_rank
        rank, staff_text = combined_rank.split("编制 ", 1)
        chief_assistant["品位"] = rank.rstrip()
        chief_assistant["编制"] = staff_text
        print("  [字段归位] '司农寺都丞'(p360)：将粘在品位末尾的编制一员"
              "拆回独立编制字段")

        water_mill = next(e for e in all_entries if e["name"] == "水辗磨务")
        water_mill_meta = all_meta[all_entries.index(water_mill)]
        history_marker = "\n职源与沿革 "
        assert history_marker in water_mill["text"]
        summary, history_text = water_mill["text"].split(history_marker, 1)
        water_mill["name"] = "水碾磨务"
        water_mill["text"] = summary
        water_mill["职源与沿革"] = history_text.replace("水辗磨务", "水碾磨务")
        combined_duty = water_mill["职掌"]
        roster_marker = "编制 "
        assert roster_marker in combined_duty
        duty_text, roster_text = combined_duty.split(roster_marker, 1)
        water_mill["职掌"] = duty_text.rstrip().replace("水砓辗磨", "水硙碾磨")
        water_mill["编制"] = roster_text.replace("水辗磨务", "水碾磨务")
        water_mill_meta["name"] = "水碾磨务"
        print("  [标题字段归位] '水碾磨务'(p361)：核原书恢复‘碾’字，"
              "并将正文中的职源与沿革及职掌末尾的编制拆回独立字段")

        fodder_yard = next(e for e in all_entries if e["name"] == "司农寺草料场")
        assert fodder_yard["简称"].startswith("栫司。")
        fodder_yard["简称"] = "秣司。" + fodder_yard["简称"][3:]
        print("  [OCR字误] '司农寺草料场'(p361)：核原书将别称‘栫司’"
              "恢复为‘秣司’")

        warehouse_yard_office = next(
            e for e in all_entries if e["name"] == "提点在京仓草场所"
        )
        warehouse_yard_post = next(
            e for e in all_entries if e["name"] == "提点在京仓草场"
        )
        assert warehouse_yard_post.get("_placeholder") is True
        post_marker = "提点在京仓草场 差遣名。"
        combined_aliases = warehouse_yard_office["简称"]
        assert post_marker in combined_aliases
        office_aliases, post_tail = combined_aliases.split(post_marker, 1)
        post_alias_marker = "①提点官。"
        assert post_alias_marker in post_tail
        post_text, post_aliases = post_tail.split(post_alias_marker, 1)
        warehouse_yard_office["简称"] = office_aliases.rstrip()
        warehouse_yard_post["text"] = "差遣名。" + post_text.rstrip()
        warehouse_yard_post["简称"] = post_alias_marker + post_aliases
        warehouse_yard_post.pop("_placeholder", None)
        warehouse_yard_post_meta = all_meta[all_entries.index(warehouse_yard_post)]
        warehouse_yard_post_meta["status"] = "ok"
        print("  [条目拆分] '提点在京仓草场所/提点在京仓草场'(p361)："
              "将差遣官正文及简称从前条简称字段拆回目录占位")

        chief_warehouse_yard = next(
            e for e in all_entries if e["name"] == "都大提点在京仓草场"
        )
        chief_warehouse_yard_meta = all_meta[all_entries.index(chief_warehouse_yard)]
        assert chief_warehouse_yard.get("_catalog_name") == "都大提点在京仓草场司"
        assert chief_warehouse_yard["text"].startswith("官之治所。")
        chief_warehouse_yard["name"] = "都大提点在京仓草场司"
        chief_warehouse_yard["text"] = (
            "官司名。都大提点在京仓草场" + chief_warehouse_yard["text"]
        )
        chief_warehouse_yard.pop("_catalog_name", None)
        chief_warehouse_yard_meta["name"] = "都大提点在京仓草场司"
        chief_warehouse_yard_meta["status"] = "ok"
        chief_warehouse_yard_meta.pop("catalog_name", None)
        print("  [标题归位] '都大提点在京仓草场司'(p362)：恢复被短前缀"
              "截断的完整官司词头及正文定义")

        north_bank_office = next(
            e for e in all_entries if e["name"] == "京北排岸司"
        )
        combined_origin = north_bank_office["职源"]
        duty_marker = "\n职掌 "
        assert duty_marker in combined_origin
        origin_text, duty_text = combined_origin.split(duty_marker, 1)
        north_bank_office["职源"] = origin_text.rstrip()
        north_bank_office["职掌"] = duty_text
        print("  [字段归位] '京北排岸司'(p363)：核原书将粘在职源末尾的"
              "职掌拆回独立字段")

        yeast_office = next(
            e for e in all_entries
            if e["name"] == "都曲院" and e.get("text", "").startswith("监当局名。")
        )
        alias_marker = "\n简称 "
        assert alias_marker in yeast_office["text"]
        yeast_text, yeast_alias = yeast_office["text"].split(alias_marker, 1)
        yeast_office["text"] = yeast_text.rstrip()
        yeast_office["简称"] = yeast_alias

        wine_retailer = next(e for e in all_entries if e["name"] == "小博士")
        yeast_continuation = next(
            e for e in all_entries
            if e["name"] == "都曲院" and e.get("_not_in_catalog") is True
        )
        assert wine_retailer["text"].endswith("许")
        assert yeast_continuation["text"].startswith("催理")
        wine_retailer["text"] += "都曲院" + yeast_continuation["text"]
        continuation_meta = all_meta[all_entries.index(yeast_continuation)]
        yeast_continuation.clear()
        yeast_continuation.update(
            {"name": "都曲院", "text": "", "_placeholder": True}
        )
        continuation_meta["status"] = "placeholder"
        continuation_meta.pop("not_in_catalog", None)
        print("  [跨页续文] '都曲院/小博士'(p363-364)：拆回都曲院简称字段，"
              "并将页首‘都曲院催理’并回小博士条，原伪条位保留为空占位")

        treasury = next(e for e in all_entries if e["name"] == "太府寺")
        missing_roster_parenthesis = "书状司一人《宋会要·职官》27之1、31）"
        assert missing_roster_parenthesis in treasury["编制"]
        treasury["编制"] = treasury["编制"].replace(
            missing_roster_parenthesis,
            "书状司一人（《宋会要·职官》27之1、31）",
            1,
        )

        treasury_assistant = next(
            e for e in all_entries if e["name"] == "太府寺丞"
        )
        assert "南宋建炎二年四月十三日罢" in treasury_assistant["职源与沿革"]
        treasury_assistant["职源与沿革"] = treasury_assistant["职源与沿革"].replace(
            "南宋建炎二年四月十三日罢",
            "南宋建炎三年四月十三日罢",
            1,
        )
        print("  [OCR符号字误] '太府寺/太府寺丞'(p364-365)：核原书补回"
              "编制引文左括号，并将建炎罢置年由二年恢复为三年")

        left_treasury = next(e for e in all_entries if e["name"] == "左藏库")
        wrong_transfer_date = "淳熙十年八月二十八日拨隶户部"
        assert wrong_transfer_date in left_treasury["职源与沿革"]
        left_treasury["职源与沿革"] = left_treasury["职源与沿革"].replace(
            wrong_transfer_date,
            "淳熙十年六月二十八日拨隶户部",
            1,
        )
        print("  [OCR字误] '左藏库'(p366)：核原书将左藏南库拨隶户部日期"
              "由淳熙十年八月二十八日恢复为六月二十八日")

        imperial_treasure = next(e for e in all_entries if e["name"] == "奉宸库")
        imperial_treasure_meta = all_meta[all_entries.index(imperial_treasure)]
        assert imperial_treasure_meta["page"] == "36"
        assert imperial_treasure_meta.get("body_page") == "368"
        imperial_treasure_meta["page"] = "368"
        print("  [目录页码] '奉宸库'：核原书将目录漏识的 p36 "
              "恢复为正文页 p368")

        joint_supervisor = next(
            e for e in all_entries if e["name"] == "监行在太平惠民和剂局"
        )
        prepared_medicine = next(
            e for e in all_entries if e["name"] == "太医局熟药所"
        )
        assert prepared_medicine.get("_placeholder") is True
        medicine_marker = "\n太医局熟药所 监当局名。"
        assert joint_supervisor["text"].endswith(medicine_marker)
        joint_supervisor["text"] = joint_supervisor["text"][:-len(medicine_marker)]
        for key in ("职源与沿革", "职掌", "编制", "简称与别名"):
            assert key in joint_supervisor
            prepared_medicine[key] = joint_supervisor.pop(key)
        prepared_medicine["text"] = "监当局名。"
        prepared_medicine.pop("_placeholder", None)
        prepared_medicine_meta = all_meta[all_entries.index(prepared_medicine)]
        prepared_medicine_meta["status"] = "ok"
        print("  [跨页断条] '监行在太平惠民和剂局/太医局熟药所'(p373-374)："
              "核原书将页末新词头及四组字段移回太医局熟药所，并取消空占位")

        military_grain_manager = next(
            e for e in all_entries
            if e["name"] == "诸军粮料院"
            and e.get("_catalog_name") == "干办行在诸军粮料院"
        )
        military_grain_manager_meta = all_meta[
            all_entries.index(military_grain_manager)
        ]
        jiankang_grain_office = next(
            e for e in all_entries if e["name"] == "分差建康府诸军粮料院"
        )
        assert jiankang_grain_office.get("_placeholder") is True
        jiankang_marker = "设于建康府。"
        assert jiankang_marker in military_grain_manager["text"]
        manager_text, jiankang_text = military_grain_manager["text"].split(
            jiankang_marker, 1
        )
        military_grain_manager["name"] = "干办行在诸军粮料院"
        military_grain_manager["text"] = (
            "差遣名。北宋诸军粮料院" + manager_text.rstrip()
        )
        military_grain_manager.pop("_catalog_name", None)
        military_grain_manager_meta["name"] = "干办行在诸军粮料院"
        military_grain_manager_meta["status"] = "ok"
        military_grain_manager_meta.pop("catalog_name", None)
        jiankang_grain_office["text"] = (
            "监当局名。" + jiankang_marker + jiankang_text
        )
        jiankang_grain_office.pop("_placeholder", None)
        jiankang_meta = all_meta[all_entries.index(jiankang_grain_office)]
        jiankang_meta["status"] = "ok"
        print("  [条目拆分] '干办行在诸军粮料院/分差建康府诸军粮料院'"
              "(p375-376)：按原书独立词头拆回差遣官与建康监当局正文")

        military_grain_office = next(
            e for e in all_entries
            if e["name"] == "诸军粮料院" and "职源与沿革" in e
        )
        combined_history = military_grain_office["职源与沿革"]
        military_duty_marker = "职掌 "
        assert military_duty_marker in combined_history
        military_history, military_duty = combined_history.split(
            military_duty_marker, 1
        )
        military_grain_office["职源与沿革"] = military_history.rstrip()
        military_grain_office["职掌"] = military_duty
        print("  [字段归位] '诸军粮料院'(p375)：将粘在职源与沿革末尾的"
              "职掌拆回独立字段")

        lizhou_grain_office = next(
            e for e in all_entries
            if e["name"] == "总领四川财赋军马钱粮所干办行在分差户部利州粮料院"
        )
        fish_pass_marker = "总领四川财赋军马钱粮所干办行名。"
        assert fish_pass_marker in lizhou_grain_office["text"]
        lizhou_text, fish_pass_text = lizhou_grain_office["text"].split(
            fish_pass_marker, 1
        )
        fish_pass_title = (
            "总领四川财赋军马钱粮所干办行在分差户部鱼关粮料院"
        )
        fish_pass_entry = {
            "name": fish_pass_title,
            "text": "监当局名。" + fish_pass_text,
            "简称": lizhou_grain_office.pop("简称"),
        }
        lizhou_grain_office["text"] = lizhou_text.rstrip()
        lizhou_i = all_entries.index(lizhou_grain_office)
        lizhou_meta = all_meta[lizhou_i]
        all_entries.insert(lizhou_i + 1, fish_pass_entry)
        all_meta.insert(
            lizhou_i + 1,
            {
                "name": fish_pass_title,
                "page": "376",
                "body_page": "376",
                "h1": lizhou_meta["h1"],
                "h2": lizhou_meta["h2"],
                "h3": lizhou_meta["h3"],
                "status": "ok",
            },
        )

        bogus_military_alias_matches = [
            (e, m) for e, m in zip(all_entries, all_meta)
            if e["name"] == "诸军专司"
            and e.get("_placeholder") is True
            and str(m.get("page")) == "376"
        ]
        assert len(bogus_military_alias_matches) == 1
        bogus_military_alias, bogus_military_alias_meta = (
            bogus_military_alias_matches[0]
        )
        bogus_i = all_entries.index(bogus_military_alias)
        assert all_meta[bogus_i] is bogus_military_alias_meta
        del all_entries[bogus_i]
        del all_meta[bogus_i]
        print("  [条目拆分] '利州粮料院/鱼关粮料院'(p376)：按原书两个"
              "独立词头拆开正文及简称；删除同页误列为主条的简称‘诸军专司’，"
              "保持后续辞典ID稳定")

        civilian_audit = next(e for e in all_entries if e["name"] == "诸司专勾司")
        assert "提举诸司库\n务司" in civilian_audit["text"]
        civilian_audit["text"] = civilian_audit["text"].replace(
            "提举诸司库\n务司", "提举诸司库务司", 1
        )

        regional_grain_audit = next(
            e for e in all_entries if e["name"] == "鄂州、建康、镇江分差粮审院"
        )
        assert regional_grain_audit["text"].startswith("分\n差鄂州")
        regional_grain_audit["text"] = regional_grain_audit["text"].replace(
            "分\n差鄂州", "分差鄂州", 1
        )
        print("  [版面换行] '诸司专勾司/鄂州、建康、镇江分差粮审院'"
              "(p376-378)：核原书合并栏宽造成的词中换行‘库务司’与‘分差’")

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
        prefix = rename.get("strip_text_prefix")
        if prefix:
            text = all_entries[i].get("text", "")
            assert text.startswith(prefix), (
                f"规范条目名 {canonical} 预期正文前缀不存在：{prefix!r}"
            )
            all_entries[i]["text"] = text[len(prefix):]
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
