#!/usr/bin/env python3
"""提取 chapter2t4 第 21–30 条（含"详参"跳转补读的 #703 门下侍郎、#802 中书侍郎）。

按现行 prompt：称谓别称不落库；"见/详参"跳转条目补读并提取，引用归实际出处；
同一 time 节点复用；无时间事实（职掌/品位/编制）挂对应节点作引用。
"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")

IDS = [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 703, 802]


def load_entry(entry_id):
    conn = sqlite3.connect(DICT_DB)
    row = conn.execute(
        "SELECT title, page, text, fields FROM chapter2t4 WHERE id=?", (entry_id,)
    ).fetchone()
    conn.close()
    full = (row[2] or "") + "\n" + "\n".join(
        str(v) for v in json.loads(row[3] or "{}").values()
    )
    return row[0], row[1], full


FULL = {i: load_entry(i) for i in IDS}


def q(eid, s):
    assert s in FULL[eid][2], f"#{eid} 不含: {s[:50]}…"
    return s


def cite(eid):
    t, p, _ = FULL[eid]
    return f"《宋代官制辞典》第{p}页“{t}”条"


def writer(eid):
    t, p, _ = FULL[eid]
    return EntryWriter(ENTRY_DB, t, p)


# --------------------------------------------------------------- #21 ----
def entry21():
    C = cite(21)
    Q_A = q(21, "（战国）秦武王二年（前309）始置左、右丞相（《史记·秦本纪》）。")
    Q_B = q(21, "南宋孝宗乾道八年二月六日，改尚书左仆射、同中书门下平章事为左丞相，"
                "尚书右仆射、同中书门下平章事为右丞相（《玉堂杂记》中）。")
    Q_C = q(21, "品位、职掌 详参“宰相”条。")
    w = writer(21)
    e = w.find_entity("左、右丞相", "官职")
    assert e
    tp = w.timepoint(
        e, "战国秦武王二年", "始置左、右丞相（秦）",
        "据职源与沿革“（战国）秦武王二年（前309）始置左、右丞相”建秦制源流节点，接链首。",
        Q_A, attr_category="宰相名", chain="head",
    )
    w.citation("Timepoints", tp, C, Q_A, "为秦制源流节点提供沿革证据")
    tp_qd = w.find_timepoint(e, "南宋乾道八年")
    assert tp_qd
    w.citation("Timepoints", tp_qd, C, Q_B, "本条目佐证乾道八年二月六日改置左、右丞相")
    w.citation("Timepoints", tp_qd, C, Q_C,
               "品位、职掌转引“宰相”条，此处登记转引关系", note="品位职掌详参“宰相”条")
    w.commit()


# --------------------------------------------------------------- #22 ----
def entry22():
    C = cite(22)
    Q_A = q(22, "唐中宗神龙元年（705）六月十五日，始置平章军国重事"
                "（《旧唐书·中宗纪》、《物原》6《官原》）。")
    Q_B = q(22, "北宋元祐元年始入衔（《宋诏令》卷57《守太师致仕文彦博拜太师、平章军国重事制》）。")
    Q_ZZ = q(22, "六日一朝，过问大典礼、大刑政及进退侍从官、三京尹、三路安抚使以上高级臣僚"
                 "（《朝野杂记》乙集卷13《平章军国重事》）。")
    Q_PW = q(22, "待元老重臣，位在宰相上。")
    w = writer(22)
    e = w.entity("平章军国重事", "官职",
                 "《辞典》88页独立成条，“贵官名”，建官职实体。",
                 quotation=q(22, "贵官名。"))
    tp1 = w.timepoint(
        e, "唐神龙元年六月十五日", "始置平章军国重事",
        "据职源与沿革“唐中宗神龙元年（705）六月十五日，始置平章军国重事”建始置节点。",
        Q_A, attr_category="贵官名",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为唐始置节点提供沿革证据")
    tp2 = w.timepoint(
        e, "北宋元祐元年", "始入衔（文彦博拜太师、平章军国重事）",
        "据职源与沿革“北宋元祐元年始入衔”建节点。",
        Q_B, attr_category="贵官名",
    )
    w.citation("Timepoints", tp2, C, Q_B, "为元祐入衔节点提供沿革证据")
    w.citation("Timepoints", tp2, C, Q_ZZ, "职掌证据：六日一朝，过问大典礼、大刑政等", note="职掌")
    w.citation("Timepoints", tp2, C, Q_PW, "品位证据：待元老重臣，位在宰相上", note="品位")
    w.commit()


# --------------------------------------------------------------- #23 ----
def entry23():
    C = cite(23)
    Q_A = q(23, "元祐三年（1088）四月五日始置（《长编》卷409，元祐三年四月辛巳）。")
    Q_ZZ = q(23, "三日或五日一赴都堂，过问军国大事，名义上低于平章军国重事一等，除去“重”字，"
                 "实际上事无轻重、无不过问，实兼三省大权（《宋会要·职官》1之42、43）。")
    Q_PW = q(23, "待元老重臣，位在宰相之上。")
    w = writer(23)
    e = w.entity("同平章军国事", "官职",
                 "《辞典》88页独立成条，“贵官名”，建官职实体。",
                 quotation=q(23, "贵官名。"))
    tp1 = w.timepoint(
        e, "北宋元祐三年四月五日", "始置同平章军国事",
        "据职源“元祐三年（1088）四月五日始置”建始置节点。",
        Q_A, attr_category="贵官名",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为始置节点提供职源证据")
    w.citation("Timepoints", tp1, C, Q_ZZ, "职掌证据：赴都堂过问军国大事，实兼三省大权", note="职掌")
    w.citation("Timepoints", tp1, C, Q_PW, "品位证据：待元老重臣，位在宰相之上", note="品位")
    w.commit()


# --------------------------------------------------------------- #24 ----
def entry24():
    C = cite(24)
    Q_A = q(24, "南宋宁宗开禧元年（1205）七月六日，以韩侂胄为平章军国事"
                "（《宋宰辅编年录校补》卷20）。")
    Q_ZZ = q(24, "三日一朝。战事起，一日一朝，垄断朝政，侵夺宰相之权"
                 "（《朝野杂记》乙集卷13《平章军国事》）。")
    Q_PW = q(24, "位在宰相上，省“重”字，所过问事广；省“同”字，所任则专，"
                 "实际上比“平章军国重事”、“同平章军国事”地位高"
                 "（《宋史·职官志》1《平章军国重事》）。")
    w = writer(24)
    e = w.entity("平章军国事", "官职",
                 "《辞典》89页独立成条，“贵官名”，建官职实体。",
                 quotation=q(24, "贵官名。"))
    tp1 = w.timepoint(
        e, "南宋开禧元年七月六日", "以韩侂胄为平章军国事（始）",
        "据职源“南宋宁宗开禧元年（1205）七月六日，以韩侂胄为平章军国事”建节点。",
        Q_A, attr_category="贵官名",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为开禧置节点提供职源证据")
    w.citation("Timepoints", tp1, C, Q_ZZ, "职掌证据：三日一朝，垄断朝政", note="职掌")
    w.citation("Timepoints", tp1, C, Q_PW, "品位证据：位在宰相上，所任则专", note="品位")
    w.commit()


# --------------------------------------------------------------- #25 ----
def entry25():
    C = cite(25)
    Q_A = q(25, "出使在外而带丞相之名，始于西汉初樊哙、尹恢，此为唐五代使相的起源"
                "（《玉海》卷120《汉丞相》、《历代职官表》卷2《内阁》之《历代建置》）。")
    Q_B = q(25, "使相之名，从唐玄宗朝起，始与宰相分列。凡带三省长官"
                "（尚书令、中书令、纳言或侍中）及同中书门下平章事或同中书门下三品，"
                "在外任节度使或他官者，都列为使相（《唐会要》卷1）。")
    Q_C = q(25, "宋初，凡节度使、枢密使、亲王、留守、检校官兼中书令、侍中、"
                "同中书门下平章事，为使相（《长编》卷17，开宝九年二月庚戌）。")
    Q_D = q(25, "元丰改制，易为开府仪同三司带节度使为使相"
                "（《通考·职官》18《开府仪同三司》）。")
    Q_PW = q(25, "官品依本官。设使相，主要用于优待勋贤故老及宰相罢任者。")
    Q_ZZ = q(25, "使相不参预政事，凡除授将、相等制敕，在敕尾不署名，注一“使”字"
                 "（《宋会要·职官》1之16）。")
    w = writer(25)
    e = w.entity("使相", "官职",
                 "《辞典》89页独立成条，“加官名”，建官职实体。",
                 quotation=q(25, "加官名。"))
    tp1 = w.timepoint(
        e, "西汉初", "出使在外而带丞相之名（使相起源）",
        "据职源与沿革①建起源节点。", Q_A, attr_category="加官名",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为使相起源节点提供沿革证据")
    tp2 = w.timepoint(
        e, "唐玄宗朝",
        "使相之名始与宰相分列：凡带三省长官及同中书门下平章事或同中书门下三品，"
        "在外任节度使或他官者，都列为使相",
        "据职源与沿革②建节点。", Q_B, attr_category="加官名",
    )
    w.citation("Timepoints", tp2, C, Q_B, "为唐使相分列节点提供沿革证据")
    tp3 = w.timepoint(
        e, "宋初",
        "凡节度使、枢密使、亲王、留守、检校官兼中书令、侍中、同中书门下平章事，为使相",
        "据职源与沿革③建节点。", Q_C, attr_category="加官名",
    )
    w.citation("Timepoints", tp3, C, Q_C, "为宋初使相节点提供沿革证据")
    w.citation("Timepoints", tp3, C, Q_PW, "品位证据：官品依本官，优待勋贤故老", note="品位")
    w.citation("Timepoints", tp3, C, Q_ZZ, "职掌证据：不参预政事，敕尾注“使”字", note="职掌")
    tp4 = w.timepoint(
        e, "北宋元丰改制", "易为开府仪同三司带节度使为使相",
        "据职源与沿革④建节点。", Q_D, attr_category="加官名",
    )
    w.citation("Timepoints", tp4, C, Q_D, "为元丰改制节点提供沿革证据")
    w.commit()


# --------------------------------------------------------------- #26 ----
def entry26():
    C = cite(26)
    Q_DEF = q(26, "官名。凡节度使带同中书门下平章事者，非真宰相，为使相。其制源于唐。")
    Q_B = q(26, "北宋元丰改官制，同中书门下平章事易以开府仪同三司，亦带节度使，称使相"
                "（《石林燕语》卷4）。")
    w = writer(26)
    e = w.entity("节度使、同中书门下平章事", "官职",
                 "《辞典》89页独立成条，为节度使带同中书门下平章事之使相形态，建官职实体。",
                 quotation=Q_DEF)
    tp1 = w.timepoint(
        e, "唐", "其制源于唐（节度使带同中书门下平章事，非真宰相，为使相）",
        "据本条“其制源于唐”建源流节点。", Q_DEF, attr_category="官名",
    )
    w.citation("Timepoints", tp1, C, Q_DEF, "为唐源流节点提供原文证据")
    tp2 = w.timepoint(
        e, "北宋元丰改制", "同中书门下平章事易以开府仪同三司，亦带节度使，称使相",
        "据本条“北宋元丰改官制，同中书门下平章事易以开府仪同三司”建变革节点。",
        Q_B, attr_category="官名",
    )
    w.citation("Timepoints", tp2, C, Q_B, "为元丰变革节点提供原文证据")
    w.commit()


# --------------------------------------------------------------- #27 ----
def entry27():
    C = cite(27)
    Q_A = q(27, "正式作为宰相官名，始于唐太宗贞观十三年(639)十一月三十日，"
                "刘洎以黄门侍郎、参知政事（《玉海》卷120《唐宰相》）。")
    Q_B = q(27, "北宋乾德二年(964)四月十九日，设参知政事（《长编》卷5）。")
    Q_C = q(27, "元丰官制，罢参知政事（《宋史·职官志》1《参知政事》）。")
    Q_D = q(27, "南宋建炎三年(1129)后，仍以参知政事为副相（同上书）。")
    Q_PW = q(27, "下宰相一等，为副相之职。官品须视本官阶。")
    Q_PW2 = q(27, "南宋建炎三年后为正二品（《宋史·职官志》8《官品》）。")
    Q_BZ = q(27, "宰相与参知政事多不过五员，两相则三参，三相则两参。")
    Q_ZZ = q(27, "为副宰相之职，与宰相同升都堂议政事，如宰相阙，则轮日执宰相笔，"
                 "行相事（《长编》卷37，至道元年四月戊子，《宋史·职官志》1《参知政事》）。")
    w = writer(27)
    e = w.entity("参知政事", "官职",
                 "《辞典》89页独立成条，“职事官名”，宋副相，建官职实体。",
                 quotation=q(27, "职事官名。"))
    tp1 = w.timepoint(
        e, "唐贞观十三年十一月三十日", "始以参知政事为宰相官名（刘洎以黄门侍郎、参知政事）",
        "据职源与沿革②建唐制源流节点。", Q_A, attr_category="职事官名",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为唐制源流节点提供沿革证据")
    tp2 = w.timepoint(
        e, "北宋乾德二年四月十九日", "设参知政事",
        "据职源与沿革③建宋始设节点。", Q_B, attr_category="职事官名",
        attr_grade="视本官阶",
    )
    w.citation("Timepoints", tp2, C, Q_B, "为宋始设节点提供沿革证据")
    w.citation("Timepoints", tp2, C, Q_PW, "品位证据：下宰相一等，官品视本官阶", note="品位")
    w.citation("Timepoints", tp2, C, Q_BZ, "编制证据：多不过五员", note="编制")
    w.citation("Timepoints", tp2, C, Q_ZZ, "职掌证据：副宰相之职，轮日执宰相笔", note="职掌")
    tp3 = w.timepoint(
        e, "北宋元丰官制", "罢参知政事",
        "据职源与沿革④建罢节点。", Q_C, attr_category="职事官名",
    )
    w.citation("Timepoints", tp3, C, Q_C, "为元丰罢节点提供沿革证据")
    tp4 = w.timepoint(
        e, "南宋建炎三年", "仍以参知政事为副相",
        "据职源与沿革⑤建复置节点。", Q_D, attr_category="职事官名",
        attr_grade="正二品",
    )
    w.citation("Timepoints", tp4, C, Q_D, "为建炎复置节点提供沿革证据")
    w.citation("Timepoints", tp4, C, Q_PW2, "官品证据：建炎三年后正二品", note="官品")
    w.commit()
    return tp3, tp4


# --------------------------------------------------------------- #28 ----
def entry28():
    C = cite(28)
    Q = q(28, "南宋绍兴三十二年七月九日，参知政事汪澈受命为湖北京西路督视军马，"
              "以“参知政事行府”为名（《宋会要·职官》39之12）。")
    w = writer(28)
    e = w.entity("参知政事行府", "机构",
                 "《辞典》90页独立成条，“临时机构名”，建机构实体。",
                 quotation=q(28, "临时机构名。"))
    tp1 = w.timepoint(
        e, "南宋绍兴三十二年七月九日",
        "参知政事汪澈受命为湖北京西路督视军马，以“参知政事行府”为名",
        "据本条建始置节点。", Q, attr_category="临时机构名",
    )
    w.citation("Timepoints", tp1, C, Q, "为始置节点提供原文证据")
    w.commit()


# --------------------------------------------------------------- #29 ----
def entry29():
    C = cite(29)
    Q_A = q(29, "元丰新官制，罢参知政事，以门下侍郎为副相之职。")
    Q_B = q(29, "至南宋建炎三年四月，仍复参知政事，而不以门下侍郎为副相之职"
                "（《朝野杂记》甲集卷10《参知政事》）")
    Q_REF = q(29, "详参“门下省·门下侍郎”条。")
    w = writer(29)
    e = w.entity("门下侍郎", "官职",
                 "《辞典》90页独立成条，“职事官名”，建官职实体。",
                 quotation=q(29, "职事官名。"))
    tp1 = w.timepoint(
        e, "北宋元丰新制", "罢参知政事，以门下侍郎为副相之职",
        "据本条“元丰新官制，罢参知政事，以门下侍郎为副相之职”建节点。",
        Q_A, attr_category="职事官名",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为元丰副相节点提供原文证据")
    w.citation("Timepoints", tp1, C, Q_REF,
               "跳转指引：已补读“门下省·门下侍郎”条（p175）并提取其事实",
               note="详参“门下省·门下侍郎”条")
    tp2 = w.timepoint(
        e, "南宋建炎三年四月十三日", "复参知政事，门下侍郎不再为副相之职",
        "据本条“至南宋建炎三年四月，仍复参知政事，而不以门下侍郎为副相之职”建节点"
        "（日期据“门下省·门下侍郎”条四月十三日）。",
        Q_B, attr_category="职事官名",
    )
    w.citation("Timepoints", tp2, C, Q_B, "为建炎复参节点提供原文证据")
    w.commit()


# --------------------------------------------------------------- #30 ----
def entry30():
    C = cite(30)
    Q_A = q(30, "元丰改制之后，至南宋建炎三年，为副相之职"
                "（《朝野杂记》甲集卷10《参知政事》）。")
    Q_B = q(30, "建炎三年四月十三日，“门下、中书侍郎复为参知政事”（《宋史·宰辅表》四）。")
    Q_REF = q(30, "详参“中书省·中书侍郎”条。")
    w = writer(30)
    e = w.entity("中书侍郎", "官职",
                 "《辞典》90页独立成条，“职事官名”，建官职实体。",
                 quotation=q(30, "职事官名。"))
    tp1 = w.timepoint(
        e, "北宋元丰新制", "元丰改制之后为副相之职",
        "据本条“元丰改制之后，至南宋建炎三年，为副相之职”建节点。",
        Q_A, attr_category="职事官名",
    )
    w.citation("Timepoints", tp1, C, Q_A, "为元丰副相节点提供原文证据")
    w.citation("Timepoints", tp1, C, Q_REF,
               "跳转指引：已补读“中书省·中书侍郎”条（p187）并提取其事实",
               note="详参“中书省·中书侍郎”条")
    tp2 = w.timepoint(
        e, "南宋建炎三年四月十三日", "门下、中书侍郎复为参知政事",
        "据本条“建炎三年四月十三日，‘门下、中书侍郎复为参知政事’”建节点。",
        Q_B, attr_category="职事官名",
    )
    w.citation("Timepoints", tp2, C, Q_B, "为复参节点提供原文证据")
    w.commit()


# ------------------------------------------- 补读 #703 门下侍郎（门下省）----
def annex703():
    C = cite(703)
    Q_HAN = q(703, "门下侍郎之名可追溯至汉代给事黄门侍郎，位次侍中，"
                   "但为皇帝左右侍从官（《分纪》卷9所引《汉官仪》）。")
    Q_WJ = q(703, "魏晋以来给事黄门侍郎属侍卫官（《南齐书·百官志》）。")
    Q_SUI = q(703, "隋炀帝及唐前期称门下省黄门侍郎（《六典》卷8）。")
    Q_TB = q(703, "唐天宝二年(743)改称门下省侍郎，为宋代所沿用（《旧唐书·职官志》2）。")
    Q_SQ = q(703, "宋前期不与政事，但为宰相所带阶官。")
    Q_GP1 = q(703, "宋前期依唐制为正三品（《宋史·职官志》8,页3996）。")
    Q_YF = q(703, "元丰新制有两种职能，一为尚书左仆射兼官，以充侍中之职，任左相；"
                  "一为取代宋前期参知政事，任副相，掌审阅中书拟命与百司、诸路上奏的重要文书，"
                  "如有不当，须执奏；同意，即交给事中读。此外，大祠祭导舆辂、诏进止"
                  "（《通考·职官》4《门下省·侍郎》）。")
    Q_GP2 = q(703, "元丰新制定为正二品（《宋会要·职官》2之3）。")
    Q_END = q(703, "南宋建炎三年四月十三日，门下、中书侍郎并为参知政事所代，"
                   "此后门下侍郎不置（《要录》卷22庚申）。")
    w = writer(703)
    e = w.find_entity("门下侍郎", "官职")
    assert e, "#29 应已建"
    # 链首前依次插入（新->旧）：唐天宝二年 -> 隋唐前期 -> 魏晋 -> 汉
    for time, event, quote in (
        ("唐天宝二年", "改称门下省侍郎，为宋代所沿用", Q_TB),
        ("隋炀帝及唐前期", "称门下省黄门侍郎", Q_SUI),
        ("魏晋以来", "给事黄门侍郎属侍卫官", Q_WJ),
        ("汉代", "给事黄门侍郎，位次侍中，为皇帝左右侍从官（门下侍郎之名可追溯）", Q_HAN),
    ):
        tp = w.timepoint(
            e, time, event,
            f"据“门下省·门下侍郎”条职源与沿革建{time}节点（详参跳转补读），接链首。",
            quote, attr_category="阶官名", chain="head",
        )
        w.citation("Timepoints", tp, C, quote, f"为{time}节点提供沿革证据（门下省·门下侍郎条）")
    # 宋前期：插在天宝二年与元丰新制之间
    tp_tb = w.find_timepoint(e, "唐天宝二年")
    tp_yf = w.find_timepoint(e, "北宋元丰新制")
    tp_sq = w.timepoint(
        e, "宋前期", "不与政事，为宰相所带阶官",
        "据“门下省·门下侍郎”条职掌①建宋前期节点（详参跳转补读），链中插入。",
        Q_SQ, attr_category="阶官名", attr_grade="正三品", chain="none",
    )
    w.relink(tp_sq, prev_id=tp_tb, succ_id=tp_yf, decision="宋前期节点插入天宝二年与元丰新制之间")
    w.relink(tp_tb, succ_id=tp_sq, decision="宋前期节点插入其后")
    w.relink(tp_yf, prev_id=tp_sq, decision="宋前期节点插入其前")
    w.citation("Timepoints", tp_sq, C, Q_SQ, "为宋前期阶官节点提供职掌证据（门下省·门下侍郎条）")
    w.citation("Timepoints", tp_sq, C, Q_GP1, "官品证据：宋前期正三品", note="官品")
    # 元丰新制节点：复用（补官品属性），追加本条证据
    tp_yf2 = w.timepoint(
        e, "北宋元丰新制", "（复用）", "复用元丰新制节点，补正二品属性。",
        Q_YF, attr_grade="正二品", chain="none",
    )
    assert tp_yf2 == tp_yf
    w.citation("Timepoints", tp_yf, C, Q_YF, "为元丰职能（仆射兼官/任副相）提供职掌证据（门下省·门下侍郎条）")
    w.citation("Timepoints", tp_yf, C, Q_GP2, "官品证据：元丰新制正二品", note="官品")
    # 终结节点复用 #29 的建炎三年四月十三日，追加本条证据
    tp_end = w.find_timepoint(e, "南宋建炎三年四月十三日")
    assert tp_end
    w.citation("Timepoints", tp_end, C, Q_END, "为门下侍郎不置节点提供沿革证据（门下省·门下侍郎条）")
    w.commit()


# ------------------------------------------- 补读 #802 中书侍郎（中书省）----
def annex802():
    C = cite(802)
    Q_JIN = q(802, "中书侍郎之名始于晋，“及晋，（通事郎）改曰中书侍郎”（《晋书·职官志》）。")
    Q_SUI = q(802, "隋称内史省侍郎、内书省侍郎。")
    Q_WD = q(802, "唐武德三年改为中书省侍郎（《大唐六典》卷9《中书省》、《隋书·百官表》下）。")
    Q_SQ = q(802, "宋前期为同中书门下平章事（宰相）所带阶官，实无职事。")
    Q_GP1 = q(802, "宋前期沿唐制为正三品。")
    Q_BW = q(802, "宋建隆三年定班位，中书侍郎在六部尚书、右散骑之下，"
                  "大中祥符元年八月，升于散骑之上、次于六部尚书（《宋会要·职官》2之1）。")
    Q_YF = q(802, "元丰新制，中书侍郎有两种职能，一为尚书右仆射兼官，充宰相之职；"
                  "一为单除，代参知政事行副宰相之职（《通考·职官》5《中书省·侍郎》）。")
    Q_GP2 = q(802, "元丰新制后为正二品（《宋会要·职官》3之6）。")
    Q_END = q(802, "建炎三年四月，中书侍郎复改为参知政事，右仆射亦不兼中书侍郎（《要录》卷22）。")
    w = writer(802)
    e = w.find_entity("中书侍郎", "官职")
    assert e, "#30 应已建"
    for time, event, quote in (
        ("唐武德三年", "改为中书省侍郎", Q_WD),
        ("隋", "称内史省侍郎、内书省侍郎", Q_SUI),
        ("晋", "始置中书侍郎（通事郎改）", Q_JIN),
    ):
        tp = w.timepoint(
            e, time, event,
            f"据“中书省·中书侍郎”条职源建{time}节点（详参跳转补读），接链首。",
            quote, attr_category="阶官名", chain="head",
        )
        w.citation("Timepoints", tp, C, quote, f"为{time}节点提供职源证据（中书省·中书侍郎条）")
    tp_wd = w.find_timepoint(e, "唐武德三年")
    tp_yf = w.find_timepoint(e, "北宋元丰新制")
    tp_sq = w.timepoint(
        e, "宋前期", "为同中书门下平章事（宰相）所带阶官，实无职事",
        "据“中书省·中书侍郎”条职掌①建宋前期节点（详参跳转补读），链中插入。",
        Q_SQ, attr_category="阶官名", attr_grade="正三品", chain="none",
    )
    w.relink(tp_sq, prev_id=tp_wd, succ_id=tp_yf, decision="宋前期节点插入武德三年与元丰新制之间")
    w.relink(tp_wd, succ_id=tp_sq, decision="宋前期节点插入其后")
    w.relink(tp_yf, prev_id=tp_sq, decision="宋前期节点插入其前")
    w.citation("Timepoints", tp_sq, C, Q_SQ, "为宋前期阶官节点提供职掌证据（中书省·中书侍郎条）")
    w.citation("Timepoints", tp_sq, C, Q_GP1, "官品证据：宋前期正三品", note="官品")
    w.citation("Timepoints", tp_sq, C, Q_BW, "班位证据：建隆三年定班位、大中祥符元年升班", note="品位")
    tp_yf2 = w.timepoint(
        e, "北宋元丰新制", "（复用）", "复用元丰新制节点，补正二品属性。",
        Q_YF, attr_grade="正二品", chain="none",
    )
    assert tp_yf2 == tp_yf
    w.citation("Timepoints", tp_yf, C, Q_YF, "为元丰职能（仆射兼官/代参知行副相）提供职掌证据（中书省·中书侍郎条）")
    w.citation("Timepoints", tp_yf, C, Q_GP2, "官品证据：元丰新制后正二品", note="官品")
    tp_end = w.find_timepoint(e, "南宋建炎三年四月十三日")
    assert tp_end
    w.citation("Timepoints", tp_end, C, Q_END, "为中书侍郎复改参知政事节点提供职掌证据（中书省·中书侍郎条）")
    w.commit()


# ------------------------------------------- 关系：参知政事 <-> 侍郎 ----
def relations(tp27_ba, tp27_fu):
    w = EntryWriter(ENTRY_DB, "参知政事/门下侍郎/中书侍郎", "89-90")
    C29, C30 = cite(29), cite(30)
    Q29A = q(29, "元丰新官制，罢参知政事，以门下侍郎为副相之职。")
    Q30A = q(30, "元丰改制之后，至南宋建炎三年，为副相之职"
                 "（《朝野杂记》甲集卷10《参知政事》）。")
    Q30B = q(30, "建炎三年四月十三日，“门下、中书侍郎复为参知政事”（《宋史·宰辅表》四）。")
    e_mx = w.find_entity("门下侍郎", "官职")
    e_zs = w.find_entity("中书侍郎", "官职")
    tp_mx_yf = w.find_timepoint(e_mx, "北宋元丰新制")
    tp_zs_yf = w.find_timepoint(e_zs, "北宋元丰新制")
    tp_mx_jy = w.find_timepoint(e_mx, "南宋建炎三年四月十三日")
    tp_zs_jy = w.find_timepoint(e_zs, "南宋建炎三年四月十三日")

    rel = w.relationship(
        tp27_ba, tp_mx_yf, "前后演变",
        "据“门下侍郎”条（p90），元丰新官制罢参知政事，以门下侍郎为副相之职，"
        "建前后演变（来源→后继）。", Q29A,
    )
    w.citation("Relationships", rel, C29, Q29A, "为罢参改侍郎演变关系提供原文证据")
    rel = w.relationship(
        tp27_ba, tp_zs_yf, "前后演变",
        "据“中书侍郎”条（p90），元丰改制之后中书侍郎为副相之职（代参知政事），"
        "建前后演变（来源→后继）。", Q30A,
    )
    w.citation("Relationships", rel, C30, Q30A, "为罢参改侍郎演变关系提供原文证据")
    rel = w.relationship(
        tp_mx_jy, tp27_fu, "前后演变",
        "据“中书侍郎”条（p90），建炎三年四月十三日门下、中书侍郎复为参知政事，"
        "建前后演变（来源→后继）。", Q30B,
    )
    w.citation("Relationships", rel, C30, Q30B, "为复参演变关系提供原文证据")
    rel = w.relationship(
        tp_zs_jy, tp27_fu, "前后演变",
        "据“中书侍郎”条（p90），建炎三年四月十三日门下、中书侍郎复为参知政事，"
        "建前后演变（来源→后继）。", Q30B,
    )
    w.citation("Relationships", rel, C30, Q30B, "为复参演变关系提供原文证据")
    w.commit()


if __name__ == "__main__":
    entry21(); print("21 OK")
    entry22(); print("22 OK")
    entry23(); print("23 OK")
    entry24(); print("24 OK")
    entry25(); print("25 OK")
    entry26(); print("26 OK")
    tp27_ba, tp27_fu = entry27(); print("27 OK")
    entry28(); print("28 OK")
    entry29(); print("29 OK")
    entry30(); print("30 OK")
    annex703(); print("703(补读) OK")
    annex802(); print("802(补读) OK")
    relations(tp27_ba, tp27_fu); print("relations OK")
    conn = sqlite3.connect(ENTRY_DB)
    for t in ("Entities", "Timepoints", "Relationships", "Citations", "BuildRecords"):
        print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    conn.close()
