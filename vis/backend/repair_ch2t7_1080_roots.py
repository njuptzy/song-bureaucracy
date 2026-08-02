#!/usr/bin/env python3
"""修复 ch2t7 的1080年伪根节点：存废语义、缺失终点与层级分类。

本脚本只写入原文明载的结构化解释，并为每次更新补齐 Citations 与
BuildRecords。所有操作均幂等；正式库执行前应先制作文件级备份。
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data/database/song_bureaucracy_entries_ch2t7.db"
DEFAULT_DICTIONARY = REPO_ROOT / "data/database/song_bureaucracy_dictionary_ch2t7.db"


@dataclass(frozen=True)
class EventUpdate:
    timepoint_id: int
    entity: str
    old_event: str
    new_event: str
    source_entry: str
    source_page: str
    quotation: str
    decision: str


@dataclass(frozen=True)
class TerminalSpec:
    entity: str
    previous_timepoint_id: int
    time: str
    event: str
    source_entry: str
    source_page: str
    quotation: str
    decision: str


@dataclass(frozen=True)
class CategorySpec:
    timepoint_id: int
    entity: str
    category: str
    source_entry: str
    source_page: str
    quotation: str
    decision: str


@dataclass(frozen=True)
class EvolutionSpec:
    source_timepoint_id: int
    target_timepoint_id: int
    source_entry: str
    source_page: str
    quotation: str
    decision: str


EVENT_UPDATES = (
    EventUpdate(792, "三司", "三部重合为一司", "三部重合为三司",
                "三司", "125", "至咸平六年重合为一司",
                "原文在三司条中明确咸平六年重新合为三司；补明结果实体，避免旧关系无法替代实体自身的复置证据。"),
    EventUpdate(4406, "详定大乐所", "置；讨论、修订大乐制度", "始置；讨论、修订大乐制度",
                "详定大乐所", "303", "临时机构名。仁宗皇祐二年置。",
                "原文明确此临时机构于皇祐二年置；补明激活语义，使临时机构按本次活动证据形成有限时间窗。"),
    EventUpdate(5244, "牛羊司", "重新并入宰杀务", "接收重新并入的宰杀务",
                "牛羊司", "330", "至嘉祐五年（1060）并入",
                "原文的被并入者是宰杀务，不是牛羊司；修正主客体，避免误判牛羊司终止。"),
    EventUpdate(6979, "国子监", "由国子学复改称", "由国子学复改称国子监",
                "国子监", "380", "淳化五年三月二十四日复改称国子监",
                "原文明确国子学复改为国子监；补足结果实体名，使国子监正确重新激活。"),
    EventUpdate(6700, "都大店宅务兼修造司", "修造司改隶八作司",
                "废罢；修造司析出并隶八作司，复为都大店宅务",
                "左右厢店宅务", "372", "大中祥符元年修造司隶八作司",
                "原文明载大中祥符元年修造司析出改隶八作司；都大店宅务兼修造司这一复合机构随之终止。"),
    EventUpdate(250, "吏部尚书铨", "为差遣院所代", "废罢，为差遣院所代",
                "吏部尚书铨", "100", "为差遣院所代",
                "原文明确吏部尚书铨被差遣院取代；将终止语义规范为废罢。"),
    EventUpdate(390, "编修诸司敕式所(令式所)", "并入详定一司敕令所", "废罢，并入详定一司敕令所",
                "详定一司敕令所", "106", "并入“详定一司敕令所”",
                "原文明确各司编敕机构并入详定一司敕令所；规范终止语义。"),
    EventUpdate(436, "看详编修中书门下条例所", "编修中书条例司罢", "废罢，编修中书条例司罢",
                "看详编修中书门下条例所", "109", "编修中书条例司、修司农寺条例司皆罢",
                "原文明确编修中书条例司罢；规范当前实体终止语义。"),
    EventUpdate(463, "都大提举在京诸司库务司", "罢都大提举司", "废罢，都大提举司罢",
                "都大提举在京诸司库务司", "110", "元年（1078）十二月十九日罢",
                "原文明确都大提举司于元丰元年罢；规范当前实体终止语义。"),
    EventUpdate(685, "剥马务", "内、外务合为皮剥所", "废罢，内、外剥马务合为皮剥所",
                "剥马务", "121", "合内、外剥马务为一局",
                "原文明确内外剥马务合并并改称皮剥所；规范旧实体终止语义。"),
    EventUpdate(1216, "马步军粮料院", "复分为马军、步军粮料院", "废罢，复分为马军、步军粮料院",
                "粮料院", "139", "马、步粮料院复分为二院",
                "原文明确马步军粮料院复分为马军、步军粮料院；规范合设实体终止语义。"),
    EventUpdate(1239, "马军专勾司", "两专勾司合并", "废罢，马军、步军两专勾司合并为马步军专勾司",
                "马步军专勾司", "140", "两专勾司合二为一",
                "原文明确马军专勾司参与合并；规范旧实体终止语义。"),
    EventUpdate(1241, "步军专勾司", "两专勾司合并", "废罢，马军、步军两专勾司合并为马步军专勾司",
                "马步军专勾司", "140", "两专勾司合二为一",
                "原文明确步军专勾司参与合并；规范旧实体终止语义。"),
    EventUpdate(3772, "殿中省", "名存实废，仅办理大礼仪仗法物", "实体官署实废；名存实废，仅办理大礼仪仗法物",
                "殿中省", "287", "北宋前期名存实废",
                "原文明确北宋前期殿中省名存实废；标记实体官署当时不作为运行机构存在。"),
    EventUpdate(5688, "左、右骐骥、六坊监", "左、右骐骥两院、天驷四监、左、右天厩二坊合称",
                "废罢；天驷四监合并后，六坊监改称四坊监",
                "左、右骐骥、六坊监", "343", "“六坊监”得改称“四坊、监”",
                "原文明确熙宁三年后六坊监称谓退出并改称四坊监。"),
    EventUpdate(6800, "香药库", "别置内香药库后，香药库有内、外之分",
                "废罢；原单一香药库分为内香药库、外香药库",
                "香药库", "374", "天禧五年六月十七日，东华门外别置内香药库，香药库遂有内、外之分",
                "原文明载天禧五年香药库分为内、外两库；原单一香药库不应在分设后继续作为第三座具体库显示。"),
    EventUpdate(7110, "御书院", "临时设置善书祇应一人",
                "见有御书院，善书祗应人一人供职",
                "国子书博士", "383", "非品官，临时设置，以授御书院善书祗应人",
                "原文中的临时设置对象是国子书博士官，不是御书院；修正事件主语，避免把官职的临时性误记成机构存废。"),
    EventUpdate(6722, "安乐坊", "赐名安济坊", "废罢；赐名安济坊",
                "病坊", "373", "崇宁三年又赐名安济坊",
                "原文明载安乐坊于崇宁三年赐名安济坊；规范旧名称终止语义。"),
    EventUpdate(4302, "太医局", "改隶太常寺、礼部",
                "提举太医局所罢，复称太医局；改隶太常寺、礼部",
                "提举太医局所", "311", "元丰五年新制罢",
                "原文明载提举太医局所于元丰五年罢，而太医局条同时记载元丰新制后的隶属；补明恢复太医局名称的激活语义。"),
    EventUpdate(1037, "度支", "度支诸案定为八案", "仍置度支，为三司内部办事部；诸案定为八案",
                "三司度支诸案", "134", "大中祥符七年后定为八案",
                "原文明载大中祥符七年后仍有三司度支诸案；补明度支作为三司内部办事部继续存在。"),
)


TERMINALS = (
    TerminalSpec("详定编敕所", 375, "北宋熙宁八年九月", "废罢，并入详定一司敕令所",
                 "详定一司敕令所", "106", "熙宁八年九月，所有各司编敕机构并入“详定一司敕令所”",
                 "原文明载熙宁八年九月所有编敕机构并入详定一司敕令所；补建详定编敕所终点。"),
    TerminalSpec("印司", 1255, "北宋元丰三年", "废罢，随提举三司帐司、勾院磨勘司罢置",
                 "提举三司帐司、勾院磨勘司", "140", "元丰三年罢",
                 "印司是该临时提举司的附属机构；原文明载上级于元丰三年罢，补建其随上级终止节点。"),
    TerminalSpec("知杂司", 1256, "北宋元丰三年", "废罢，随提举三司帐司、勾院磨勘司罢置",
                 "提举三司帐司、勾院磨勘司", "140", "元丰三年罢",
                 "此知杂司时间点是该临时提举司的附属机构；原文明载上级于元丰三年罢，补建其随上级终止节点。"),
    TerminalSpec("司天台", 3466, "北宋端拱元年九月", "废罢，改称司天监",
                 "司天监", "268", "宋初沿唐制，称司天台。太宗端拱元年九月，始见有司天监之称",
                 "原文将宋初司天台与端拱元年始见的司天监连续叙述；补建司天台终点。"),
    TerminalSpec("提举在京诸司库务司", 5794, "北宋元丰元年十二月十九日",
                 "废罢，随都大提举在京诸司库务司罢置",
                 "都大提举在京诸司库务司", "110", "神宗元丰元年（1078）十二月十九日罢",
                 "该实体是都大提举在京诸司库务司的省称异名；原文明载本司元丰元年罢，补建终点。"),
    TerminalSpec("都大提举在京诸司库务所", 5916, "北宋元丰元年十二月十九日",
                 "废罢，随都大提举在京诸司库务司罢置",
                 "都大提举在京诸司库务司", "110", "神宗元丰元年（1078）十二月十九日罢",
                 "该实体是都大提举在京诸司库务司的治所异称；原文明载本司元丰元年罢，补建终点。"),
    TerminalSpec("茶库", 6558, "北宋咸平六年", "废罢，二库合并为都茶库",
                 "都茶库", "369", "初分二库，咸平六年合为一库加“都”字",
                 "原文明载原来的两茶库于咸平六年合为都茶库；补建茶库终点。"),
    TerminalSpec("左计司", 826, "北宋淳化五年十二月二十四日", "废罢，与总计司同时废止",
                 "左计司", "126", "置废时间与“总 计司”同。",
                 "左计司原文明确置废时间与总计司相同；补建淳化五年废止终点。"),
    TerminalSpec("右计司", 827, "北宋淳化五年十二月二十四日", "废罢，与总计司同时废止",
                 "左计司", "126", "置废时间与“总 计司”同。",
                 "右计司条详参左计；左计原文明确左右计司置废时间均与总计司相同。"),
    TerminalSpec("马步军粮料院", 1216, "北宋熙宁六年正月五日", "至迟已废罢，复分为马军、步军粮料院",
                 "都大提举在京诸司库务司", "110", "三粮料院等分别由三司、都大提举市易司、开封府归隶本司",
                 "原文明载熙宁六年已存在三粮料院，证明此前马步军粮料院已复分；补建可用于1080截面的最迟终点。"),
    TerminalSpec("天驷左第一监", 5674, "北宋熙宁三年三月六日", "废罢，并为左、右天驷二监",
                 "左、右天驷监", "342", "熙宁三年三月六日并为两监",
                 "原文明确天驷四监于熙宁三年合并为两监；补建旧实例终点。"),
    TerminalSpec("天驷左第二监", 5675, "北宋熙宁三年三月六日", "废罢，并为左、右天驷二监",
                 "左、右天驷监", "342", "熙宁三年三月六日并为两监",
                 "原文明确天驷四监于熙宁三年合并为两监；补建旧实例终点。"),
    TerminalSpec("天驷右第一监", 5676, "北宋熙宁三年三月六日", "废罢，并为左、右天驷二监",
                 "左、右天驷监", "342", "熙宁三年三月六日并为两监",
                 "原文明确天驷四监于熙宁三年合并为两监；补建旧实例终点。"),
    TerminalSpec("天驷右第二监", 5677, "北宋熙宁三年三月六日", "废罢，并为左、右天驷二监",
                 "左、右天驷监", "342", "熙宁三年三月六日并为两监",
                 "原文明确天驷四监于熙宁三年合并为两监；补建旧实例终点。"),
    TerminalSpec("架阁御鞍库房", 5741, "北宋天禧三年四月", "废罢，改称鞍辔库",
                 "鞍辔库", "344", "已见正称“鞍辔库”局名",
                 "原文明确架阁御鞍库房为鞍辔库设置之始，天禧三年已用鞍辔库正称；补建旧称终点。"),
    TerminalSpec("译经院", 5955, "北宋太平兴国八年", "废罢，赐额传法后改称传法院",
                 "传法院", "350", "八年，赐院额名“传法”",
                 "原文明确译经院次年赐额传法并改称传法院；补建旧称终点。"),
    TerminalSpec("折中仓", 6236, "北宋淳化二年", "废罢，改名折博仓",
                 "折中仓", "361", "淳化二年改名折博仓。",
                 "原文明确折中仓于淳化二年改名折博仓；补建旧称终点。"),
    TerminalSpec("都大提举内军器库所", 5339, "北宋元丰五年",
                 "废罢；旧独立监管体制终止，所监军器库改隶卫尉寺",
                 "军器库", "333", "元丰新制隶卫尉寺",
                 "原文明载元丰新制后军器库改隶卫尉寺；都大提举所的唯一职能是总监诸军器库，不能在所监诸库改隶后继续作为独立中央根节点。"),
    TerminalSpec("都大提点军器库所", 5338, "北宋元丰五年",
                 "废罢；旧独立监管体制终止，所监军器库改隶卫尉寺",
                 "军器库", "333", "元丰新制隶卫尉寺",
                 "原文明载元丰新制后军器库改隶卫尉寺；都大提点所的唯一职能是监领军器库逐库事务，不能在所监诸库改隶后继续保留旧监管层。"),
    TerminalSpec("度支", 1037, "北宋元丰五年", "废罢；元丰改制，三司度支诸案统罢",
                 "三司度支诸案", "134", "元丰改制则统罢",
                 "原文明载三司度支诸案在元丰改制时统罢；补建度支作为三司内部办事部的终点。"),
    TerminalSpec("百官案", 999, "北宋元丰五年", "废罢；元丰改制，随三司度支诸案统罢",
                 "三司度支诸案", "134", "元丰改制则统罢",
                 "百官案是三司度支诸案之一；原文明载诸案于元丰改制时统罢，补建百官案终点。"),
)


CATEGORIES = (
    CategorySpec(3694, "实录院", "临时修实录机构", "实录院", "282",
                 "元丰改制前，实录院于崇文院内临时设局",
                 "原文明载元丰改制前实录院为遇事临时设局；按临时机构的离散证据期参与年度截面。"),
    CategorySpec(6576, "诸路", "路级机构", "斗秤务", "369",
                 "诏于诸路转运司治所所在州各置斗秤务",
                 "原文明载该节点表示诸路转运司治所范围，不属于中央机构；归为路级。"),
    CategorySpec(6591, "秦凤路市易司", "路级机构", "在京市易务", "370",
                 "在秦凤路置市易司",
                 "原文明载该市易司设置于秦凤路；归为路级机构。"),
    CategorySpec(6617, "益州交子务", "路级机构", "益州交子务", "371",
                 "成立官营交子务于成都，即益州交子务，又称四川交子务",
                 "原文明载该务设于成都并服务四川；归为路级机构。"),
    CategorySpec(6668, "开封府", "州府机构", "抵当所", "372",
                 "先后隶开封府、都提举市易司、太府寺",
                 "开封府是府级地方行政机构，不属于中央机构；归为州府机构。"),
    CategorySpec(1320, "提举买马监牧司", "路级机构", "群牧行司", "145",
                 "在秦州、凤翔府等地往来应接督办买马公事",
                 "原文明载该司在秦州、凤翔府等地办理买马，归为路级机构。"),
    CategorySpec(1336, "提举陕西等路买马监牧司", "路级机构", "提举陕西等路买马监牧司", "148",
                 "专领本路监牧及买马公事",
                 "原文明载该司专领陕西本路监牧买马，归为路级机构。"),
    CategorySpec(1380, "提举秦凤等路买马监牧司", "路级机构", "提举秦凤等路买马监牧司", "148",
                 "专领秦凤等路分买马、养马、起发马纲等公事",
                 "原文明载该司专领秦凤等路买马养马，归为路级机构。"),
    CategorySpec(2419, "茶场司", "路级机构", "茶场司", "207",
                 "于成都府路诸州创置茶场司",
                 "原文明载茶场司设置于成都府路诸州，归为路级机构。"),
    CategorySpec(7185, "西京国子监", "州府机构", "三京国子监", "385",
                 "北宋西京河南府、南京应天府、北京大名府，于真宗、仁宗朝后，分别置国子监以代府学",
                 "原文明载西京国子监设于河南府并取代府学，不是东京中央国子监；归为州府机构。"),
    CategorySpec(7186, "南京国子监", "州府机构", "三京国子监", "385",
                 "北宋西京河南府、南京应天府、北京大名府，于真宗、仁宗朝后，分别置国子监以代府学",
                 "原文明载南京国子监设于应天府并取代府学，不是东京中央国子监；归为州府机构。"),
    CategorySpec(7187, "北京国子监", "州府机构", "三京国子监", "385",
                 "北宋西京河南府、南京应天府、北京大名府，于真宗、仁宗朝后，分别置国子监以代府学",
                 "原文明载北京国子监设于大名府并取代府学，不是东京中央国子监；归为州府机构。"),
    CategorySpec(7291, "太学馆", "临时科举试机构", "太学生", "388",
                 "国子监临时开太学馆",
                 "原文明载太学馆仅在礼部科举试期间临时开设，省试后即解散；按临时机构的离散证据期参与年度截面。"),
    CategorySpec(6719, "病坊", "州府医疗救济机构", "病坊", "373",
                 "杭州知州苏轼，集公款二千贯，捐家私黄金五十两，在杭创办病坊",
                 "原文明载病坊由杭州知州在杭州创办，归为州府地方机构，不按太府寺目录归入中央。"),
    CategorySpec(6720, "病坊", "州府医疗救济机构", "病坊", "373",
                 "杭州知州苏轼，集公款二千贯，捐家私黄金五十两，在杭创办病坊",
                 "病坊改名节点沿用杭州州府医疗救济机构分类。"),
    CategorySpec(6721, "安乐坊", "州府医疗救济机构", "病坊", "373",
                 "杭州知州苏轼，集公款二千贯，捐家私黄金五十两，在杭创办病坊",
                 "安乐坊是杭州病坊的后继名称，归为州府医疗救济机构。"),
    CategorySpec(6722, "安乐坊", "州府医疗救济机构", "病坊", "373",
                 "崇宁三年又赐名安济坊",
                 "安乐坊赐名终点沿用杭州州府医疗救济机构分类。"),
    CategorySpec(6723, "安济坊", "州府医疗救济机构", "病坊", "373",
                 "崇宁三年又赐名安济坊",
                 "安济坊由杭州安乐坊赐名而来，归为州府医疗救济机构。"),
    CategorySpec(6725, "安济坊", "州府医疗救济机构", "病坊", "373",
                 "杭州知州苏轼，集公款二千贯，捐家私黄金五十两，在杭创办病坊",
                 "安济坊后续演变节点沿用杭州州府医疗救济机构分类。"),
    CategorySpec(6724, "居养院", "州府医疗救济机构", "病坊", "373",
                 "崇宁三年又赐名安济坊，并置居养院",
                 "居养院与杭州安济坊同条同时设置，归为州府医疗救济机构。"),
    CategorySpec(6726, "养济院", "州府医疗救济机构", "养济院", "373",
                 "南宋绍兴十三年，于京师临安府置养济院",
                 "原文明载养济院置于临安府，归为州府医疗救济机构。"),
)


EVOLUTIONS = (
    EvolutionSpec(375, 386, "详定一司敕令所", "106",
                  "熙宁八年九月，所有各司编敕机构并入“详定一司敕令所”",
                  "原文明载详定编敕所并入详定一司敕令所；补建前后演变关系。"),
    EvolutionSpec(3466, 3472, "司天监", "268",
                  "宋初沿唐制，称司天台。太宗端拱元年九月，始见有司天监之称",
                  "原文连续叙述宋初司天台到司天监的称谓演变；补建前后演变关系。"),
)


BAZUO_QUOTES = (
    ("东、西八作司", "408", "官司名。先后隶三司、提举在京诸司库务司、将作监。"),
    ("东、西八作司", "408", "宋初称八作司，置东八作使、西八作使。太平兴国二年分东、西八作司，景德四年六月并为东西八作司（含街道司）。天圣元年五月十六日复分为东八作司、西八作司"),
    ("东、西八作司", "408", "南宋称八作司"),
    ("将作监", "405", "神宗熙宁四年十一月一日，将作监始正名，始专领在京修造事"),
)


TONGWENGUAN_QUOTES = (
    ("同文馆", "352", "馆驿名。隶鸿胪寺。"),
    ("同文馆", "352", "北宋熙宁中创置"),
)


WESTERN_POSTHOUSE_QUOTES = (
    ("都亭西驿", "350", "馆驿。先后隶鸿胪寺、礼部。"),
    ("都亭西驿", "350", "北宋大中祥符间置"),
)


DUTING_POSTHOUSE_QUOTES = (
    ("都亭驿", "349", "馆驿名。先后隶鸿胪寺、都大提举在京诸司库务所、礼部。"),
    ("都亭驿", "349", "北宋太平兴国二年八月，改东京怀信驿（后周世宗置）为都亭驿"),
    ("都大提举在京诸司库务司", "110",
     "熙宁六年正月五日，又增市易务上下界、商税院、翰林图画院、杂买务杂卖场、诸宫观真仪法从库、南郊太庙家事库、开封府司检校库、都亭驿、怀远驿、三粮料院等分别由三司、都大提举市易司、开封府归隶本司"),
)


TRANSLATION_COURT_QUOTES = (
    ("传法院", "350", "官司名。隶鸿胪寺。"),
    ("传法院", "350", "北宋太平兴国七年六月于太平兴国寺建译经院。八年，赐院额名“传法”"),
)


JIANLONG_OFFICE_QUOTES = (
    ("提点建隆观所", "357", "官司名。隶鸿胪寺。"),
    ("鸿胪寺", "348", "资圣院及建隆观提点所，在京寺务司及提点所"),
)


MONK_REGISTRY_QUOTES = (
    ("左、右街僧录司", "352", "官司名。隶鸿胪寺。"),
    ("左、右街僧录司", "352", "通管勾释教(佛教)教门公事"),
    ("僧正司", "353", "设僧正，下辖系帐僧尼。归僧录院管。"),
)


OFFICIALS_DESK_QUOTES = (
    ("百官案", "135", "隶三司度支部。掌京朝官、幕职官俸钱及衣赐，祠祭所用礼物，及诸州驿站所需供给。"),
    ("三司度支诸案", "134", "大中祥符七年后定为八案"),
    ("三司度支诸案", "134", "元丰改制则统罢"),
    ("药蜜库", "369", "监当局名。隶三司百官案"),
)


MEDICAL_NINE_QUOTES = (
    ("提举太医局所", "311", "即太医局设提举官领太医局后，改以“提举太医局所”为名"),
    ("提举太医局所", "311", "元丰五年新制罢"),
    ("太医局", "310", "元丰新制改隶太常寺、礼部"),
    ("太医局", "310", "医学生分九科：大方脉、风科、小方脉、眼科、疮肿兼伤折科、产科、口齿兼咽喉科、针灸科、金镞兼书禁科"),
)


MEDICAL_NINE_RELATIONS = (
    (3943, 4706, "大方脉科"),
    (3946, 4708, "风科"),
    (3949, 4710, "小方脉科"),
    (3952, 4712, "产科"),
    (3955, 4714, "口齿兼咽喉科"),
    (3958, 4716, "疮肿兼伤折科"),
    (3961, 4718, "眼科"),
    (3964, 4720, "针灸科"),
    (3967, 4722, "金镞兼书禁科"),
)


def validate_quotations(dictionary_path: Path) -> None:
    dictionary = sqlite3.connect(dictionary_path)
    try:
        specs = (*EVENT_UPDATES, *TERMINALS, *CATEGORIES, *EVOLUTIONS)
        for spec in specs:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (spec.source_entry, spec.source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{spec.source_entry} 第{spec.source_page}页")
            if not any(spec.quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{spec.source_entry} / {spec.quotation}")
        for source_entry, source_page, quotation in BAZUO_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
        for source_entry, source_page, quotation in TONGWENGUAN_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
        for source_entry, source_page, quotation in WESTERN_POSTHOUSE_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
        for source_entry, source_page, quotation in DUTING_POSTHOUSE_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
        for source_entry, source_page, quotation in TRANSLATION_COURT_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
        for source_entry, source_page, quotation in JIANLONG_OFFICE_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
        for source_entry, source_page, quotation in MONK_REGISTRY_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
        for source_entry, source_page, quotation in OFFICIALS_DESK_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
        for source_entry, source_page, quotation in MEDICAL_NINE_QUOTES:
            rows = dictionary.execute(
                "SELECT text, fields FROM chapter2t7 WHERE title=? AND page=?",
                (source_entry, source_page),
            ).fetchall()
            if not rows:
                raise ValueError(f"辞典词条不存在：{source_entry} 第{source_page}页")
            if not any(quotation in f"{text or ''} {fields or ''}" for text, fields in rows):
                raise ValueError(f"引文不是辞典原文子串：{source_entry} / {quotation}")
    finally:
        dictionary.close()


def timepoint_entity(connection: sqlite3.Connection, timepoint_id: int) -> tuple[int, str]:
    row = connection.execute(
        "SELECT e.id,e.title FROM Timepoints t JOIN Entities e ON e.id=t.entity_id WHERE t.id=?",
        (timepoint_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"时间点不存在：{timepoint_id}")
    return int(row[0]), str(row[1])


def append_audit(
    connection: sqlite3.Connection,
    target_table: str,
    target_id: int,
    source_entry: str,
    source_page: str,
    quotation: str,
    decision: str,
) -> None:
    exists = connection.execute(
        """
        SELECT 1 FROM BuildRecords
        WHERE target_table=? AND target_id=? AND source_entry=? AND decision=?
        """,
        (target_table, target_id, source_entry, decision),
    ).fetchone()
    if exists is None:
        connection.execute(
            """
            INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)
            VALUES (?,?,?,?,?)
            """,
            (target_table, target_id, source_entry, source_page, decision),
        )
    citation = f"《宋代官制辞典》第{source_page}页“{source_entry}”条"
    row = connection.execute(
        """
        SELECT id FROM Citations
        WHERE target_table=? AND target_id=? AND citation=? AND quotation=?
        ORDER BY id LIMIT 1
        """,
        (target_table, target_id, citation, quotation),
    ).fetchone()
    if row is None:
        cursor = connection.execute(
            """
            INSERT INTO Citations(target_table,target_id,citation,quotation,note,conflict_flag)
            VALUES (?,?,?,?,?,0)
            """,
            (target_table, target_id, citation, quotation, decision),
        )
        citation_id = int(cursor.lastrowid)
        connection.execute(
            """
            INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)
            VALUES ('Citations',?,?,?,'为1080年伪根节点修复保存同条辞典证据。')
            """,
            (citation_id, source_entry, source_page),
        )


def delete_target_audit(
    connection: sqlite3.Connection, target_table: str, target_id: int
) -> None:
    citation_ids = [
        int(row[0]) for row in connection.execute(
            "SELECT id FROM Citations WHERE target_table=? AND target_id=?",
            (target_table, target_id),
        )
    ]
    for citation_id in citation_ids:
        connection.execute(
            "DELETE FROM BuildRecords WHERE target_table='Citations' AND target_id=?",
            (citation_id,),
        )
    connection.execute(
        "DELETE FROM Citations WHERE target_table=? AND target_id=?",
        (target_table, target_id),
    )
    connection.execute(
        "DELETE FROM BuildRecords WHERE target_table=? AND target_id=?",
        (target_table, target_id),
    )


def repair_east_west_bazuo(connection: sqlite3.Connection, counts: dict[str, int]) -> None:
    formal_quote = BAZUO_QUOTES[0][2]
    evolution_quote = BAZUO_QUOTES[1][2]
    southern_quote = BAZUO_QUOTES[2][2]
    jiangzuo_quote = BAZUO_QUOTES[3][2]

    row = connection.execute("SELECT title,type FROM Entities WHERE id=3334").fetchone()
    if row is None or row[1] != "机构" or row[0] not in {"八作司", "东、西八作司"}:
        raise ValueError(f"八作司派生实体已漂移：{row}")
    if row[0] == "八作司":
        connection.execute("UPDATE Entities SET title='东、西八作司' WHERE id=3334")
        counts["bazuo_entities_updated"] += 1
    else:
        counts["reused"] += 1
    append_audit(
        connection, "Entities", 3334, "东、西八作司", "408", formal_quote,
        "以第408页正式词头校正第372页关系句临时派生的八作司实体；八作司保留为宋初及南宋阶段名称。",
    )

    def ensure_entity(title: str, decision: str) -> int:
        existing = connection.execute(
            "SELECT id FROM Entities WHERE title=? AND type='机构' ORDER BY id LIMIT 1", (title,)
        ).fetchone()
        if existing is None:
            cursor = connection.execute("INSERT INTO Entities(title,type) VALUES (?,'机构')", (title,))
            entity_id = int(cursor.lastrowid)
            counts["bazuo_entities_inserted"] += 1
        else:
            entity_id = int(existing[0])
            counts["reused"] += 1
        append_audit(connection, "Entities", entity_id, "东、西八作司", "408",
                     evolution_quote, decision)
        return entity_id

    def ensure_timepoint(
        entity_id: int,
        time: str,
        event: str,
        source_entry: str,
        source_page: str,
        quotation: str,
        decision: str,
        category: str = "京城营造机构",
    ) -> int:
        existing = connection.execute(
            "SELECT id FROM Timepoints WHERE entity_id=? AND time=? AND event=? ORDER BY id LIMIT 1",
            (entity_id, time, event),
        ).fetchone()
        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO Timepoints(
                    entity_id,time,event,prev_id,succ_id,attr_category,
                    attr_officer_type,attr_grade,quotation
                ) VALUES (?,?,?,NULL,NULL,?,'','',?)
                """,
                (entity_id, time, event, category, quotation),
            )
            timepoint_id = int(cursor.lastrowid)
            counts["bazuo_timepoints_inserted"] += 1
        else:
            timepoint_id = int(existing[0])
            counts["reused"] += 1
        append_audit(connection, "Timepoints", timepoint_id, source_entry, source_page,
                     quotation, decision)
        return timepoint_id

    def link_chain(timepoint_ids: list[int]) -> None:
        for index, timepoint_id in enumerate(timepoint_ids):
            previous_id = timepoint_ids[index - 1] if index else None
            successor_id = timepoint_ids[index + 1] if index + 1 < len(timepoint_ids) else None
            connection.execute(
                "UPDATE Timepoints SET prev_id=?,succ_id=? WHERE id=?",
                (previous_id, successor_id, timepoint_id),
            )

    def ensure_relation(
        subject_id: int,
        object_id: int,
        quotation: str,
        source_entry: str,
        source_page: str,
        decision: str,
    ) -> int:
        existing = connection.execute(
            """
            SELECT id FROM Relationships
            WHERE subject_id=? AND object_id=? AND relation_type='上下级机构'
            ORDER BY id LIMIT 1
            """,
            (subject_id, object_id),
        ).fetchone()
        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO Relationships(
                    subject_id,object_id,relation_type,staff_quota,staff_type,quotation
                ) VALUES (?,?,'上下级机构',NULL,NULL,?)
                """,
                (subject_id, object_id, quotation),
            )
            relation_id = int(cursor.lastrowid)
            counts["bazuo_relations_inserted"] += 1
        else:
            relation_id = int(existing[0])
            counts["reused"] += 1
        append_audit(connection, "Relationships", relation_id, source_entry, source_page,
                     quotation, decision)
        return relation_id

    # 将第372页派生的单点纳入第408页正式沿革链。
    existing_6703 = connection.execute(
        "SELECT event,attr_category FROM Timepoints WHERE id=6703 AND entity_id=3334"
    ).fetchone()
    if existing_6703 is None or existing_6703[0] not in {
        "统辖修造司", "大中祥符元年，统辖析出的修造司",
    }:
        raise ValueError(f"八作司派生时间点已漂移：{existing_6703}")
    if existing_6703 != ("大中祥符元年，统辖析出的修造司", "京城营造机构"):
        connection.execute(
            """
            UPDATE Timepoints
            SET event='大中祥符元年，统辖析出的修造司', attr_category='京城营造机构'
            WHERE id=6703
            """
        )
        counts["bazuo_timepoints_updated"] += 1
    else:
        counts["reused"] += 1
    append_audit(
        connection, "Timepoints", 6703, "左右厢店宅务", "372",
        "大中祥符元年修造司隶八作司",
        "保留原关系证据，并将该派生节点并入东、西八作司正式沿革链。",
    )

    collective_points = [
        ensure_timepoint(3334, "宋初", "称八作司，置东八作使、西八作使",
                         "东、西八作司", "408", evolution_quote,
                         "建立正式词条的宋初八作司阶段。"),
        ensure_timepoint(3334, "北宋太平兴国二年", "分为东八作司、西八作司",
                         "东、西八作司", "408", evolution_quote,
                         "原文明载太平兴国二年分东、西二司。"),
        ensure_timepoint(3334, "北宋（隶提举在京诸司库务司，具体年月未载）",
                         "先后改隶提举在京诸司库务司",
                         "东、西八作司", "408", formal_quote,
                         "原文明载先后隶提举在京诸司库务司；具体改隶年月未载，关系以该上级1005年始置节点作为生效证据。"),
        ensure_timepoint(3334, "北宋景德四年六月", "东、西二司合并为东西八作司，并含街道司",
                         "东、西八作司", "408", evolution_quote,
                         "原文明载景德四年六月合并为一司。"),
        6703,
        ensure_timepoint(3334, "北宋天圣元年五月十六日", "东西八作司复分为东八作司、西八作司",
                         "东、西八作司", "408", evolution_quote,
                         "原文明载天圣元年五月十六日复分东、西二司。"),
        ensure_timepoint(3334, "北宋熙宁四年十一月一日",
                         "改隶将作监；将作监始专领在京修造事",
                         "将作监", "405", jiangzuo_quote,
                         "第408页明载八作司先后隶将作监；第405页明确熙宁四年将作监始专领在京修造事，据此建立不晚于该年的改隶节点。"),
        ensure_timepoint(3334, "南宋（未载具体年月）", "南宋称八作司",
                         "东、西八作司", "408", southern_quote,
                         "保留原文明载的南宋名称阶段。"),
    ]
    link_chain(collective_points)

    east_id = ensure_entity("东八作司", "建立第408页明确分置的东司实例。")
    west_id = ensure_entity("西八作司", "建立第408页明确分置的西司实例。")

    child_points: dict[int, list[int]] = {}
    for entity_id, title in ((east_id, "东八作司"), (west_id, "西八作司")):
        child_points[entity_id] = [
            ensure_timepoint(entity_id, "北宋太平兴国二年", f"从八作司分置{title}",
                             "东、西八作司", "408", evolution_quote,
                             f"原文明载太平兴国二年分置{title}。"),
            ensure_timepoint(entity_id, "北宋景德四年六月", "废罢；东、西二司合并为东西八作司",
                             "东、西八作司", "408", evolution_quote,
                             "原文明载景德四年六月东、西二司合并。"),
            ensure_timepoint(entity_id, "北宋天圣元年五月十六日", f"复置；东西八作司复分为{title}",
                             "东、西八作司", "408", evolution_quote,
                             f"原文明载天圣元年五月十六日复分并恢复{title}。"),
        ]
        link_chain(child_points[entity_id])

    jiangzuo_tp = ensure_timepoint(
        1999, "北宋熙宁四年十一月一日", "始正名，专领在京修造事",
        "将作监", "405", jiangzuo_quote,
        "补建将作监熙宁四年开始专领在京修造事的时间点，作为八作司改隶的上级端证据。",
        "中央营造机构",
    )

    ensure_relation(788, collective_points[0], formal_quote, "东、西八作司", "408",
                    "原文明载东、西八作司早期隶三司。")
    ensure_relation(458, collective_points[2], formal_quote, "东、西八作司", "408",
                    "原文明载继而隶提举在京诸司库务司；以上级景德二年始置节点限定关系不早于1005年。")
    jiangzuo_relation = ensure_relation(
        jiangzuo_tp, collective_points[6], formal_quote, "东、西八作司", "408",
        "原文明载后隶将作监；以将作监熙宁四年专领在京修造事作为改隶生效节点。",
    )
    append_audit(
        connection, "Relationships", jiangzuo_relation, "将作监", "405", jiangzuo_quote,
        "将作监自熙宁四年始专领在京修造事，与东、西八作司掌京师缮修及后隶将作监的记载互证。",
    )
    for entity_id in (east_id, west_id):
        ensure_relation(collective_points[1], child_points[entity_id][0], evolution_quote,
                        "东、西八作司", "408", "建立太平兴国二年东、西分司的层级实例关系。")
        ensure_relation(collective_points[5], child_points[entity_id][2], evolution_quote,
                        "东、西八作司", "408", "建立天圣元年复分东、西二司的层级实例关系。")


def repair_charity_evolution_chain(connection: sqlite3.Connection, counts: dict[str, int]) -> None:
    quotation = (
        "北宋元祐四年十二月，杭州知州苏轼，集公款二千贯，捐家私黄金五十两，"
        "在杭创办病坊，以收养无助的得疫病人，后扩大为救济城内外老疾贫乏难以生存者。"
        "初由僧人义务主持。后改名安乐坊。崇宁三年又赐名安济坊，并置居养院"
    )
    rows = connection.execute(
        "SELECT id,entity_id,prev_id,succ_id FROM Timepoints WHERE id IN (6719,6720) ORDER BY id"
    ).fetchall()
    if len(rows) != 2 or [row[1] for row in rows] != [3346, 3346]:
        raise ValueError(f"病坊时间链节点已漂移：{rows}")
    desired = {
        6719: (None, 6720),
        6720: (6719, None),
    }
    for timepoint_id, _, prev_id, succ_id in rows:
        expected_prev, expected_succ = desired[timepoint_id]
        if (prev_id, succ_id) == (expected_prev, expected_succ):
            counts["reused"] += 1
        elif (prev_id, succ_id) in {(6720, None), (None, 6719)}:
            connection.execute(
                "UPDATE Timepoints SET prev_id=?,succ_id=? WHERE id=?",
                (expected_prev, expected_succ, timepoint_id),
            )
            counts["charity_chain_links_updated"] += 1
        else:
            raise ValueError(
                f"病坊时间链指针已漂移：{timepoint_id} prev={prev_id} succ={succ_id}"
            )
        append_audit(
            connection, "Timepoints", timepoint_id, "病坊", "373", quotation,
            "修正病坊创办至改名安乐坊的链向；创办节点在前，改名节点在后。",
        )


def repair_tongwenguan_hierarchy(connection: sqlite3.Connection, counts: dict[str, int]) -> None:
    # 鸿胪寺宋前期节点 → 同文馆熙宁中创置节点。关系的实际生效年由两端
    # 时间共同决定，因此不会把同文馆提前到创置之前。
    subject = timepoint_entity(connection, 4002)
    target = timepoint_entity(connection, 5985)
    if subject[1] != "鸿胪寺" or target[1] != "同文馆":
        raise ValueError(f"同文馆上下级端点已漂移：{subject} -> {target}")
    existing = connection.execute(
        """
        SELECT id FROM Relationships
        WHERE subject_id=4002 AND object_id=5985 AND relation_type='上下级机构'
        ORDER BY id LIMIT 1
        """
    ).fetchone()
    quotation = TONGWENGUAN_QUOTES[0][2]
    if existing is None:
        cursor = connection.execute(
            """
            INSERT INTO Relationships(
                subject_id,object_id,relation_type,staff_quota,staff_type,quotation
            ) VALUES (4002,5985,'上下级机构',NULL,NULL,?)
            """,
            (quotation,),
        )
        relation_id = int(cursor.lastrowid)
        counts["tongwenguan_relations_inserted"] += 1
    else:
        relation_id = int(existing[0])
        counts["reused"] += 1
    append_audit(
        connection, "Relationships", relation_id, "同文馆", "352", quotation,
        "原文直接明载同文馆隶鸿胪寺；以同文馆熙宁中创置节点限定北宋前期关系的开始。",
    )


def repair_western_posthouse_hierarchy(
    connection: sqlite3.Connection, counts: dict[str, int]
) -> None:
    # 都亭西驿条明载先后隶鸿胪寺、礼部，并另载大中祥符间始置。以始置
    # 节点承载第一阶段隶属；元丰新制的既有关系继续作为后续制度状态。
    subject = timepoint_entity(connection, 4002)
    target = timepoint_entity(connection, 5929)
    if subject[1] != "鸿胪寺" or target[1] != "都亭西驿":
        raise ValueError(f"都亭西驿上下级端点已漂移：{subject} -> {target}")
    existing = connection.execute(
        """
        SELECT id FROM Relationships
        WHERE subject_id=4002 AND object_id=5929 AND relation_type='上下级机构'
        ORDER BY id LIMIT 1
        """
    ).fetchone()
    quotation = WESTERN_POSTHOUSE_QUOTES[0][2]
    if existing is None:
        cursor = connection.execute(
            """
            INSERT INTO Relationships(
                subject_id,object_id,relation_type,staff_quota,staff_type,quotation
            ) VALUES (4002,5929,'上下级机构',NULL,NULL,?)
            """,
            (quotation,),
        )
        relation_id = int(cursor.lastrowid)
        counts["western_posthouse_relations_inserted"] += 1
    else:
        relation_id = int(existing[0])
        counts["reused"] += 1
    append_audit(
        connection, "Relationships", relation_id, "都亭西驿", "350", quotation,
        "原文直接明载都亭西驿先隶鸿胪寺、后隶礼部；以大中祥符间始置节点承载第一阶段隶属。",
    )
    append_audit(
        connection, "Relationships", relation_id, "都亭西驿", "350",
        WESTERN_POSTHOUSE_QUOTES[1][2],
        "原文明载都亭西驿大中祥符间始置；据此限定鸿胪寺隶属关系不早于该馆驿的始置阶段。",
    )


def repair_duting_posthouse_hierarchy(
    connection: sqlite3.Connection, counts: dict[str, int]
) -> None:
    # 都亭驿先隶鸿胪寺，熙宁六年明确转隶都大提举在京诸司库务司。
    # 把两段关系放回各自的真实时间，并使用正式词头的库务司实体。
    early = connection.execute(
        "SELECT time,event FROM Timepoints WHERE id=5915"
    ).fetchone()
    early_event = "隶鸿胪寺，接待辽国使者"
    if early == ("北宋元丰新制", early_event):
        connection.execute(
            "UPDATE Timepoints SET time=?,quotation=? WHERE id=5915",
            ("北宋太平兴国二年八月", DUTING_POSTHOUSE_QUOTES[0][2]),
        )
        connection.execute("DELETE FROM NormalizedTimes WHERE timepoint_id=5915")
        counts["duting_posthouse_timepoints_updated"] += 1
    elif early == ("北宋太平兴国二年八月", early_event):
        counts["reused"] += 1
    else:
        raise ValueError(f"都亭驿早期鸿胪寺节点已漂移：{early}")
    append_audit(
        connection, "Timepoints", 5915, "都亭驿", "349",
        DUTING_POSTHOUSE_QUOTES[0][2],
        "原文按先后次序明载都亭驿先隶鸿胪寺；把该关系状态从误置的元丰新制移回北宋始置阶段。",
    )
    append_audit(
        connection, "Timepoints", 5915, "都亭驿", "349",
        DUTING_POSTHOUSE_QUOTES[1][2],
        "原文明载太平兴国二年东京怀信驿改名都亭驿；以此限定鸿胪寺阶段不早于都亭驿名启用。",
    )

    early_relation = connection.execute(
        "SELECT subject_id,object_id,relation_type FROM Relationships WHERE id=5072"
    ).fetchone()
    if early_relation == (3987, 5915, "上下级机构"):
        connection.execute("UPDATE Relationships SET subject_id=4002 WHERE id=5072")
        counts["duting_posthouse_relations_reparented"] += 1
    elif early_relation == (4002, 5915, "上下级机构"):
        counts["reused"] += 1
    else:
        raise ValueError(f"鸿胪寺至都亭驿关系已漂移：{early_relation}")
    append_audit(
        connection, "Relationships", 5072, "都亭驿", "349",
        DUTING_POSTHOUSE_QUOTES[0][2],
        "原文直接明载都亭驿先隶鸿胪寺；父端改用鸿胪寺宋前期节点，不再误挂元丰新制。",
    )
    append_audit(
        connection, "Relationships", 5072, "都亭驿", "349",
        DUTING_POSTHOUSE_QUOTES[1][2],
        "以太平兴国二年都亭驿名启用节点限定第一段隶属关系的开始。",
    )

    transfer_time = "北宋熙宁六年正月五日"
    transfer_event = "改隶都大提举在京诸司库务司"
    transfer = connection.execute(
        "SELECT time,event FROM Timepoints WHERE id=5917"
    ).fetchone()
    if transfer == ("北宋（隶都大提举在京诸司库务所年月未载）", "改隶都大提举在京诸司库务所"):
        connection.execute(
            "UPDATE Timepoints SET time=?,event=?,attr_category=?,quotation=? WHERE id=5917",
            (transfer_time, transfer_event, "都大提举在京诸司库务司属馆驿",
             DUTING_POSTHOUSE_QUOTES[2][2]),
        )
        connection.execute("DELETE FROM NormalizedTimes WHERE timepoint_id=5917")
        counts["duting_posthouse_timepoints_updated"] += 1
    elif transfer == (transfer_time, transfer_event):
        counts["reused"] += 1
    else:
        raise ValueError(f"都亭驿熙宁改隶节点已漂移：{transfer}")
    append_audit(
        connection, "Timepoints", 5917, "都大提举在京诸司库务司", "110",
        DUTING_POSTHOUSE_QUOTES[2][2],
        "原文明载熙宁六年正月五日都亭驿归隶本司；补足原先未载的确切改隶年月，并统一正式机构名。",
    )

    transfer_relation = connection.execute(
        "SELECT subject_id,object_id,relation_type FROM Relationships WHERE id=5073"
    ).fetchone()
    if transfer_relation == (5916, 5917, "上下级机构"):
        connection.execute(
            "UPDATE Relationships SET subject_id=462,quotation=? WHERE id=5073",
            (DUTING_POSTHOUSE_QUOTES[2][2],),
        )
        counts["duting_posthouse_relations_reparented"] += 1
    elif transfer_relation == (462, 5917, "上下级机构"):
        counts["reused"] += 1
    else:
        raise ValueError(f"库务司至都亭驿关系已漂移：{transfer_relation}")
    append_audit(
        connection, "Relationships", 5073, "都大提举在京诸司库务司", "110",
        DUTING_POSTHOUSE_QUOTES[2][2],
        "原文明载熙宁六年都亭驿归隶；父端改用正式词头都大提举在京诸司库务司的同日节点。",
    )


def repair_translation_court_hierarchy(
    connection: sqlite3.Connection, counts: dict[str, int]
) -> None:
    # 传法院条未把隶属限定在元丰新制后；以太平兴国八年改名节点作为
    # 子端，使鸿胪寺隶属从“传法院”这一名称正式启用时生效。
    subject = timepoint_entity(connection, 4002)
    target = timepoint_entity(connection, 5956)
    if subject[1] != "鸿胪寺" or target[1] != "传法院":
        raise ValueError(f"传法院上下级端点已漂移：{subject} -> {target}")
    existing = connection.execute(
        """
        SELECT id FROM Relationships
        WHERE subject_id=4002 AND object_id=5956 AND relation_type='上下级机构'
        ORDER BY id LIMIT 1
        """
    ).fetchone()
    quotation = TRANSLATION_COURT_QUOTES[0][2]
    if existing is None:
        cursor = connection.execute(
            """
            INSERT INTO Relationships(
                subject_id,object_id,relation_type,staff_quota,staff_type,quotation
            ) VALUES (4002,5956,'上下级机构',NULL,NULL,?)
            """,
            (quotation,),
        )
        relation_id = int(cursor.lastrowid)
        counts["translation_court_relations_inserted"] += 1
    else:
        relation_id = int(existing[0])
        counts["reused"] += 1
    append_audit(
        connection, "Relationships", relation_id, "传法院", "350", quotation,
        "原文直接明载传法院隶鸿胪寺；以太平兴国八年赐额改称传法院的节点限定关系开始。",
    )


def repair_jianlong_office_merge(
    connection: sqlite3.Connection, counts: dict[str, int]
) -> None:
    formal = connection.execute(
        "SELECT title,type FROM Entities WHERE id=3076"
    ).fetchone()
    if formal != ("提点建隆观所", "机构"):
        raise ValueError(f"正式提点建隆观所实体已漂移：{formal}")
    _, formal_title = timepoint_entity(connection, 6146)
    if formal_title != "提点建隆观所":
        raise ValueError(f"提点建隆观所正式时间点已漂移：6146={formal_title}")

    # 鸿胪寺条中的“建隆观提点所”是倒装称法；第357页正式词头为
    # “提点建隆观所”。元丰关系必须落到同一个正式实体，不能再造第二所。
    relation = connection.execute(
        "SELECT subject_id,object_id,relation_type FROM Relationships WHERE id=5053"
    ).fetchone()
    if relation is None or int(relation[0]) != 3987 or relation[2] != "上下级机构":
        raise ValueError(f"鸿胪寺至提点建隆观所关系已漂移：{relation}")
    if int(relation[1]) == 5883:
        connection.execute("UPDATE Relationships SET object_id=6146 WHERE id=5053")
        counts["jianlong_relations_reparented"] += 1
    elif int(relation[1]) == 6146:
        counts["reused"] += 1
    else:
        raise ValueError(f"鸿胪寺至提点建隆观所子端已漂移：{relation[1]}")
    append_audit(
        connection, "Relationships", 5053, "提点建隆观所", "357",
        JIANLONG_OFFICE_QUOTES[0][2],
        "以第357页正式词头提点建隆观所承载鸿胪寺条所称建隆观提点所；两者是同一官司。",
    )
    append_audit(
        connection, "Entities", 3076, "提点建隆观所", "357",
        JIANLONG_OFFICE_QUOTES[0][2],
        "保留正式词头提点建隆观所作为唯一实体，不另建倒装称法建隆观提点所。",
    )

    duplicate = connection.execute(
        "SELECT title,type FROM Entities WHERE id=2946"
    ).fetchone()
    if duplicate is not None:
        if duplicate != ("建隆观提点所", "机构"):
            raise ValueError(f"倒装提点所实体已漂移：{duplicate}")
        remaining = connection.execute(
            "SELECT COUNT(*) FROM Relationships WHERE subject_id=5883 OR object_id=5883"
        ).fetchone()[0]
        if remaining:
            raise ValueError(f"建隆观提点所仍有{remaining}条未迁移关系")
        delete_target_audit(connection, "Timepoints", 5883)
        connection.execute("DELETE FROM NormalizedTimes WHERE timepoint_id=5883")
        connection.execute("DELETE FROM Timepoints WHERE id=5883")
        delete_target_audit(connection, "Entities", 2946)
        connection.execute("DELETE FROM Entities WHERE id=2946")
        counts["jianlong_timepoints_deleted"] += 1
        counts["jianlong_entities_deleted"] += 1
    else:
        if connection.execute("SELECT 1 FROM Timepoints WHERE id=5883").fetchone():
            raise ValueError("建隆观提点所实体已删但时间点5883仍存在")
        counts["reused"] += 1


def repair_monk_registry_merge(
    connection: sqlite3.Connection, counts: dict[str, int]
) -> None:
    formal = connection.execute(
        "SELECT title,type FROM Entities WHERE id=2950"
    ).fetchone()
    if formal != ("左、右街僧录司", "机构"):
        raise ValueError(f"正式左、右街僧录司实体已漂移：{formal}")
    _, tang_title = timepoint_entity(connection, 6007)
    _, reform_title = timepoint_entity(connection, 5887)
    if tang_title != "左、右街僧录司" or reform_title != "左、右街僧录司":
        raise ValueError(f"左、右街僧录司时间链已漂移：{tang_title} / {reform_title}")

    early_time = "宋代（左、右街僧录司）"
    early_event = "宋代沿置，分左、右二录司，通管佛教教门公事"
    existing = connection.execute(
        "SELECT id FROM Timepoints WHERE entity_id=2950 AND time=? AND event=? ORDER BY id LIMIT 1",
        (early_time, early_event),
    ).fetchone()
    if existing is None:
        previous = connection.execute(
            "SELECT succ_id FROM Timepoints WHERE id=6007"
        ).fetchone()[0]
        successor = connection.execute(
            "SELECT prev_id FROM Timepoints WHERE id=5887"
        ).fetchone()[0]
        if previous != 5887 or successor != 6007:
            raise ValueError(f"左、右街僧录司插入位置已漂移：6007->{previous}, {successor}->5887")
        cursor = connection.execute(
            """
            INSERT INTO Timepoints(
                entity_id,time,event,prev_id,succ_id,attr_category,
                attr_officer_type,attr_grade,quotation
            ) VALUES (2950,?,?,6007,5887,'鸿胪寺属司合称','','',?)
            """,
            (early_time, early_event, MONK_REGISTRY_QUOTES[0][2]),
        )
        early_id = int(cursor.lastrowid)
        connection.execute("UPDATE Timepoints SET succ_id=? WHERE id=6007", (early_id,))
        connection.execute("UPDATE Timepoints SET prev_id=? WHERE id=5887", (early_id,))
        counts["monk_registry_timepoints_inserted"] += 1
    else:
        early_id = int(existing[0])
        counts["reused"] += 1
        connection.execute(
            "UPDATE Timepoints SET prev_id=6007,succ_id=5887 WHERE id=?", (early_id,)
        )
        connection.execute("UPDATE Timepoints SET succ_id=? WHERE id=6007", (early_id,))
        connection.execute("UPDATE Timepoints SET prev_id=? WHERE id=5887", (early_id,))

    append_audit(
        connection, "Timepoints", early_id, "左、右街僧录司", "352",
        MONK_REGISTRY_QUOTES[0][2],
        "以正式词头建立宋代左、右街僧录司承载节点，不另建僧录院别称实体。",
    )
    append_audit(
        connection, "Timepoints", early_id, "左、右街僧录司", "352",
        MONK_REGISTRY_QUOTES[1][2],
        "补充左、右街僧录司通管佛教教门公事的职掌证据。",
    )
    append_audit(
        connection, "Entities", 2950, "左、右街僧录司", "352",
        MONK_REGISTRY_QUOTES[0][2],
        "保留正式词头左、右街僧录司作为唯一中央僧录机构。",
    )

    early_parent = connection.execute(
        """
        SELECT id FROM Relationships
        WHERE subject_id=4002 AND object_id=? AND relation_type='上下级机构'
        ORDER BY id LIMIT 1
        """,
        (early_id,),
    ).fetchone()
    if early_parent is None:
        cursor = connection.execute(
            """
            INSERT INTO Relationships(
                subject_id,object_id,relation_type,staff_quota,staff_type,quotation
            ) VALUES (4002,?,'上下级机构',NULL,NULL,?)
            """,
            (early_id, MONK_REGISTRY_QUOTES[0][2]),
        )
        early_parent_id = int(cursor.lastrowid)
        counts["monk_registry_relations_inserted"] += 1
    else:
        early_parent_id = int(early_parent[0])
        counts["reused"] += 1
    append_audit(
        connection, "Relationships", early_parent_id, "左、右街僧录司", "352",
        MONK_REGISTRY_QUOTES[0][2],
        "原书直接明载左、右街僧录司隶鸿胪寺；以宋代承载节点补足元丰新制前关系。",
    )

    local_relation = connection.execute(
        "SELECT subject_id,object_id,relation_type FROM Relationships WHERE id=5155"
    ).fetchone()
    if local_relation is None or int(local_relation[1]) != 6031 or local_relation[2] != "上下级机构":
        raise ValueError(f"僧正司归属关系已漂移：{local_relation}")
    if int(local_relation[0]) == 6036:
        connection.execute(
            "UPDATE Relationships SET subject_id=? WHERE id=5155", (early_id,)
        )
        counts["monk_registry_relations_reparented"] += 1
    elif int(local_relation[0]) == early_id:
        counts["reused"] += 1
    else:
        raise ValueError(f"僧正司归属父端已漂移：{local_relation[0]}")
    append_audit(
        connection, "Relationships", 5155, "僧正司", "353",
        MONK_REGISTRY_QUOTES[2][2],
        "僧正司条所称僧录院归并到相邻正式词头左、右街僧录司，不另保留第二个中央僧录机构。",
    )

    duplicate = connection.execute(
        "SELECT title,type FROM Entities WHERE id=3035"
    ).fetchone()
    if duplicate is not None:
        if duplicate != ("僧录院", "机构"):
            raise ValueError(f"派生僧录院实体已漂移：{duplicate}")
        remaining = connection.execute(
            "SELECT COUNT(*) FROM Relationships WHERE subject_id=6036 OR object_id=6036"
        ).fetchone()[0]
        if remaining:
            raise ValueError(f"僧录院仍有{remaining}条未迁移关系")
        delete_target_audit(connection, "Timepoints", 6036)
        connection.execute("DELETE FROM NormalizedTimes WHERE timepoint_id=6036")
        connection.execute("DELETE FROM Timepoints WHERE id=6036")
        delete_target_audit(connection, "Entities", 3035)
        connection.execute("DELETE FROM Entities WHERE id=3035")
        counts["monk_registry_timepoints_deleted"] += 1
        counts["monk_registry_entities_deleted"] += 1
    else:
        if connection.execute("SELECT 1 FROM Timepoints WHERE id=6036").fetchone():
            raise ValueError("僧录院实体已删但时间点6036仍存在")
        counts["reused"] += 1


def repair_officials_desk_merge(
    connection: sqlite3.Connection, counts: dict[str, int]
) -> None:
    formal = connection.execute(
        "SELECT title,type FROM Entities WHERE id=515"
    ).fetchone()
    if formal != ("百官案", "机构"):
        raise ValueError(f"正式百官案实体已漂移：{formal}")
    _, formal_title = timepoint_entity(connection, 999)
    if formal_title != "百官案":
        raise ValueError(f"百官案正式时间点已漂移：999={formal_title}")

    # 药蜜库原文中的“三司百官案”是带上级限定的称法，不是第二个机构。
    # 把唯一有效的下级关系迁到正式词头百官案，保留药蜜库原始引文。
    relation = connection.execute(
        "SELECT subject_id,object_id,relation_type FROM Relationships WHERE id=5587"
    ).fetchone()
    if relation is None or int(relation[1]) != 6556 or relation[2] != "上下级机构":
        raise ValueError(f"百官案到药蜜库关系已漂移：{relation}")
    if int(relation[0]) == 6555:
        connection.execute("UPDATE Relationships SET subject_id=999 WHERE id=5587")
        counts["officials_desk_relations_reparented"] += 1
    elif int(relation[0]) == 999:
        counts["reused"] += 1
    else:
        raise ValueError(f"百官案到药蜜库父端已漂移：{relation[0]}")
    append_audit(
        connection, "Relationships", 5587, "百官案", "135",
        OFFICIALS_DESK_QUOTES[0][2],
        "以正式词头百官案替代药蜜库条临时派生的三司百官案实体；药蜜库原关系迁到唯一百官案。",
    )

    # 直接“三司→三司百官案”是重复实体的补丁关系；正式结构已有
    # “三司→度支→百官案”，因此连同其审计记录一并删除。
    if connection.execute("SELECT 1 FROM Relationships WHERE id=6179").fetchone():
        delete_target_audit(connection, "Relationships", 6179)
        connection.execute("DELETE FROM Relationships WHERE id=6179")
        counts["officials_desk_relations_deleted"] += 1
    else:
        counts["reused"] += 1

    duplicate = connection.execute(
        "SELECT title,type FROM Entities WHERE id=3263"
    ).fetchone()
    if duplicate is not None:
        if duplicate != ("三司百官案", "机构"):
            raise ValueError(f"派生百官案实体已漂移：{duplicate}")
        remaining = connection.execute(
            """
            SELECT COUNT(*) FROM Relationships
            WHERE subject_id=6555 OR object_id=6555
            """
        ).fetchone()[0]
        if remaining:
            raise ValueError(f"三司百官案仍有{remaining}条未迁移关系")
        delete_target_audit(connection, "Timepoints", 6555)
        # NormalizedTimes 是可视化工作表并对 Timepoints 保持外键；删除正式
        # 时间点时同步清除对应派生行，实时服务会按剩余时间点重建标准化数据。
        connection.execute("DELETE FROM NormalizedTimes WHERE timepoint_id=6555")
        connection.execute("DELETE FROM Timepoints WHERE id=6555")
        delete_target_audit(connection, "Entities", 3263)
        connection.execute("DELETE FROM Entities WHERE id=3263")
        counts["officials_desk_timepoints_deleted"] += 1
        counts["officials_desk_entities_deleted"] += 1
    else:
        if connection.execute("SELECT 1 FROM Timepoints WHERE id=6555").fetchone():
            raise ValueError("三司百官案实体已删但时间点6555仍存在")
        counts["reused"] += 1


def repair_medical_nine_hierarchy(connection: sqlite3.Connection, counts: dict[str, int]) -> None:
    renamed_parent = timepoint_entity(connection, 4725)
    restored_parent = timepoint_entity(connection, 4302)
    renamed_terminal = timepoint_entity(connection, 4726)
    if renamed_parent[1] != "提举太医局所" or renamed_terminal[1] != "提举太医局所":
        raise ValueError(f"提举太医局所时间点已漂移：{renamed_parent} / {renamed_terminal}")
    if restored_parent[1] != "太医局":
        raise ValueError(f"太医局元丰节点已漂移：{restored_parent}")

    rename_quote = MEDICAL_NINE_QUOTES[0][2]
    reform_quote = MEDICAL_NINE_QUOTES[2][2]
    nine_quote = MEDICAL_NINE_QUOTES[3][2]

    # 原有九条熙宁九年关系误接到已经退出的旧名“太医局”。关系事实不变，
    # 只把父端换成当时正在使用的正式名称“提举太医局所”。
    for relation_id, child_timepoint_id, child_title in MEDICAL_NINE_RELATIONS:
        child = timepoint_entity(connection, child_timepoint_id)
        if child[1] != child_title:
            raise ValueError(f"太医局医学科端点已漂移：{child_timepoint_id}={child}")
        row = connection.execute(
            "SELECT subject_id,object_id,relation_type FROM Relationships WHERE id=?",
            (relation_id,),
        ).fetchone()
        if row is None or int(row[1]) != child_timepoint_id or row[2] != "上下级机构":
            raise ValueError(f"太医局医学科关系已漂移：{relation_id}={row}")
        if int(row[0]) == 4643:
            connection.execute(
                "UPDATE Relationships SET subject_id=4725 WHERE id=?", (relation_id,)
            )
            counts["medical_nine_relations_reparented"] += 1
        elif int(row[0]) == 4725:
            counts["reused"] += 1
        else:
            raise ValueError(f"太医局医学科父端已漂移：{relation_id} subject={row[0]}")
        append_audit(
            connection, "Relationships", relation_id, "提举太医局所", "311", rename_quote,
            f"熙宁八年至元丰五年太医局改以提举太医局所为名；{child_title}在熙宁九年应隶当时名称，而非已退出的太医局旧名。",
        )

        # 元丰五年提举太医局所罢，太医局复称并改隶；为同一组九科建立
        # 新制度状态，使关系在1082年从现名父端继续，而不是永久停在旧名。
        existing = connection.execute(
            """
            SELECT id FROM Relationships
            WHERE subject_id=4302 AND object_id=? AND relation_type='上下级机构'
            ORDER BY id LIMIT 1
            """,
            (child_timepoint_id,),
        ).fetchone()
        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO Relationships(
                    subject_id,object_id,relation_type,staff_quota,staff_type,quotation
                ) VALUES (4302,?,'上下级机构',NULL,NULL,?)
                """,
                (child_timepoint_id, nine_quote),
            )
            restored_relation_id = int(cursor.lastrowid)
            counts["medical_nine_relations_inserted"] += 1
        else:
            restored_relation_id = int(existing[0])
            counts["reused"] += 1
        append_audit(
            connection, "Relationships", restored_relation_id, "太医局", "310", nine_quote,
            f"太医局条明载医学生九科包含{child_title}；以元丰改制后的太医局节点记录复称后的继续隶属。",
        )
        append_audit(
            connection, "Relationships", restored_relation_id, "太医局", "310", reform_quote,
            "元丰新制后太医局恢复现名并改隶太常寺、礼部；本关系状态从该制度节点生效。",
        )

    # 补齐改名机构的返回边；目标节点事件已明确“复称太医局”，年度截面据此
    # 在元丰五年结束提举太医局所并恢复太医局，保证同年只保留一个现名。
    existing = connection.execute(
        """
        SELECT id FROM Relationships
        WHERE subject_id=4726 AND object_id=4302 AND relation_type='前后演变'
        ORDER BY id LIMIT 1
        """
    ).fetchone()
    if existing is None:
        cursor = connection.execute(
            """
            INSERT INTO Relationships(
                subject_id,object_id,relation_type,staff_quota,staff_type,quotation
            ) VALUES (4726,4302,'前后演变',NULL,NULL,?)
            """,
            (MEDICAL_NINE_QUOTES[1][2],),
        )
        evolution_id = int(cursor.lastrowid)
        counts["medical_nine_evolutions_inserted"] += 1
    else:
        evolution_id = int(existing[0])
        counts["reused"] += 1
    append_audit(
        connection, "Relationships", evolution_id, "提举太医局所", "311",
        MEDICAL_NINE_QUOTES[1][2],
        "提举太医局所元丰五年罢，制度对象恢复使用太医局名；补建改名机构返回太医局的演变边。",
    )
    append_audit(
        connection, "Timepoints", 4302, "太医局", "310", reform_quote,
        "太医局条明载元丰新制后的现名与隶属，支持提举太医局所罢后复称太医局。",
    )


def remove_partial_duty_transfer_evolution(
    connection: sqlite3.Connection, counts: dict[str, int]
) -> None:
    """删除把部分职事移交误抽成机构演变的关系。

    元丰五年司农寺只是把此前兼领的京外新法职事交给户部右曹，随后仍以
    司农寺之名掌仓场、园苑、酒曲等事务。二者不是前后相代的同一机构。
    """
    relation_id = 5233
    row = connection.execute(
        """
        SELECT se.title, st.event, te.title, ot.event, r.relation_type
        FROM Relationships r
        JOIN Timepoints st ON st.id=r.subject_id
        JOIN Entities se ON se.id=st.entity_id
        JOIN Timepoints ot ON ot.id=r.object_id
        JOIN Entities te ON te.id=ot.entity_id
        WHERE r.id=?
        """,
        (relation_id,),
    ).fetchone()
    if row is None:
        counts["reused"] += 1
        return
    expected = (
        "司农寺",
        "事权大增，兼为财务和新法政务机构，督领各路提举常平司及官属",
        "户部右曹",
        "接收司农寺旧有京外新法职事",
        "前后演变",
    )
    if tuple(row) != expected:
        raise ValueError(f"关系{relation_id}内容已漂移：{tuple(row)!r}")

    connection.execute(
        "DELETE FROM Citations WHERE target_table='Relationships' AND target_id=?",
        (relation_id,),
    )
    connection.execute(
        "DELETE FROM BuildRecords WHERE target_table='Relationships' AND target_id=?",
        (relation_id,),
    )
    connection.execute("DELETE FROM Relationships WHERE id=?", (relation_id,))
    counts["partial_duty_transfer_evolutions_deleted"] += 1


def apply_repairs(db_path: Path, dictionary_path: Path = DEFAULT_DICTIONARY) -> dict[str, int]:
    validate_quotations(dictionary_path)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON")
    counts = {
        "events_updated": 0,
        "terminals_inserted": 0,
        "categories_updated": 0,
        "evolutions_inserted": 0,
        "bazuo_entities_updated": 0,
        "bazuo_entities_inserted": 0,
        "bazuo_timepoints_updated": 0,
        "bazuo_timepoints_inserted": 0,
        "bazuo_relations_inserted": 0,
        "charity_chain_links_updated": 0,
        "tongwenguan_relations_inserted": 0,
        "western_posthouse_relations_inserted": 0,
        "duting_posthouse_timepoints_updated": 0,
        "duting_posthouse_relations_reparented": 0,
        "translation_court_relations_inserted": 0,
        "jianlong_relations_reparented": 0,
        "jianlong_timepoints_deleted": 0,
        "jianlong_entities_deleted": 0,
        "monk_registry_timepoints_inserted": 0,
        "monk_registry_relations_inserted": 0,
        "monk_registry_relations_reparented": 0,
        "monk_registry_timepoints_deleted": 0,
        "monk_registry_entities_deleted": 0,
        "officials_desk_relations_reparented": 0,
        "officials_desk_relations_deleted": 0,
        "officials_desk_timepoints_deleted": 0,
        "officials_desk_entities_deleted": 0,
        "medical_nine_relations_reparented": 0,
        "medical_nine_relations_inserted": 0,
        "medical_nine_evolutions_inserted": 0,
        "partial_duty_transfer_evolutions_deleted": 0,
        "reused": 0,
    }
    try:
        connection.execute("BEGIN IMMEDIATE")
        for spec in EVENT_UPDATES:
            _, title = timepoint_entity(connection, spec.timepoint_id)
            if title != spec.entity:
                raise ValueError(f"时间点实体不符：{spec.timepoint_id}={title}，预期{spec.entity}")
            current = connection.execute(
                "SELECT event FROM Timepoints WHERE id=?", (spec.timepoint_id,)
            ).fetchone()[0]
            if current == spec.new_event:
                counts["reused"] += 1
            elif current == spec.old_event:
                connection.execute(
                    "UPDATE Timepoints SET event=? WHERE id=?", (spec.new_event, spec.timepoint_id)
                )
                counts["events_updated"] += 1
            else:
                raise ValueError(f"时间点{spec.timepoint_id}事件已漂移：{current}")
            append_audit(connection, "Timepoints", spec.timepoint_id, spec.source_entry,
                         spec.source_page, spec.quotation, spec.decision)

        for spec in TERMINALS:
            entity_id, title = timepoint_entity(connection, spec.previous_timepoint_id)
            if title != spec.entity:
                raise ValueError(f"前序时间点实体不符：{spec.previous_timepoint_id}={title}，预期{spec.entity}")
            existing = connection.execute(
                "SELECT id FROM Timepoints WHERE entity_id=? AND time=? AND event=? ORDER BY id LIMIT 1",
                (entity_id, spec.time, spec.event),
            ).fetchone()
            if existing is None:
                previous = connection.execute(
                    "SELECT succ_id,attr_category,attr_officer_type,attr_grade FROM Timepoints WHERE id=?",
                    (spec.previous_timepoint_id,),
                ).fetchone()
                if previous[0] is not None:
                    raise ValueError(f"前序时间点{spec.previous_timepoint_id}已有后继{previous[0]}")
                cursor = connection.execute(
                    """
                    INSERT INTO Timepoints(
                        entity_id,time,event,prev_id,succ_id,
                        attr_category,attr_officer_type,attr_grade,quotation
                    ) VALUES (?,?,?,?,NULL,?,?,?,?)
                    """,
                    (entity_id, spec.time, spec.event, spec.previous_timepoint_id,
                     previous[1], previous[2], previous[3], spec.quotation),
                )
                terminal_id = int(cursor.lastrowid)
                connection.execute(
                    "UPDATE Timepoints SET succ_id=? WHERE id=?",
                    (terminal_id, spec.previous_timepoint_id),
                )
                counts["terminals_inserted"] += 1
            else:
                terminal_id = int(existing[0])
                counts["reused"] += 1
                connection.execute(
                    "UPDATE Timepoints SET succ_id=? WHERE id=? AND succ_id IS NULL",
                    (terminal_id, spec.previous_timepoint_id),
                )
            append_audit(connection, "Timepoints", terminal_id, spec.source_entry,
                         spec.source_page, spec.quotation, spec.decision)

        for spec in CATEGORIES:
            _, title = timepoint_entity(connection, spec.timepoint_id)
            if title != spec.entity:
                raise ValueError(f"分类时间点实体不符：{spec.timepoint_id}={title}，预期{spec.entity}")
            current = connection.execute(
                "SELECT attr_category FROM Timepoints WHERE id=?", (spec.timepoint_id,)
            ).fetchone()[0]
            if current == spec.category:
                counts["reused"] += 1
            else:
                connection.execute(
                    "UPDATE Timepoints SET attr_category=? WHERE id=?",
                    (spec.category, spec.timepoint_id),
                )
                counts["categories_updated"] += 1
            append_audit(connection, "Timepoints", spec.timepoint_id, spec.source_entry,
                         spec.source_page, spec.quotation, spec.decision)

        for spec in EVOLUTIONS:
            source_entity_id, _ = timepoint_entity(connection, spec.source_timepoint_id)
            target_entity_id, _ = timepoint_entity(connection, spec.target_timepoint_id)
            existing = connection.execute(
                """
                SELECT r.id FROM Relationships r
                JOIN Timepoints s ON s.id=r.subject_id
                JOIN Timepoints o ON o.id=r.object_id
                WHERE r.relation_type='前后演变' AND s.entity_id=? AND o.entity_id=?
                ORDER BY r.id LIMIT 1
                """,
                (source_entity_id, target_entity_id),
            ).fetchone()
            if existing is None:
                cursor = connection.execute(
                    """
                    INSERT INTO Relationships(subject_id,object_id,relation_type,staff_quota,staff_type,quotation)
                    VALUES (?,?,'前后演变',NULL,NULL,?)
                    """,
                    (spec.source_timepoint_id, spec.target_timepoint_id, spec.quotation),
                )
                relation_id = int(cursor.lastrowid)
                counts["evolutions_inserted"] += 1
            else:
                relation_id = int(existing[0])
                counts["reused"] += 1
            append_audit(connection, "Relationships", relation_id, spec.source_entry,
                         spec.source_page, spec.quotation, spec.decision)
        repair_east_west_bazuo(connection, counts)
        repair_charity_evolution_chain(connection, counts)
        repair_tongwenguan_hierarchy(connection, counts)
        repair_western_posthouse_hierarchy(connection, counts)
        repair_duting_posthouse_hierarchy(connection, counts)
        repair_translation_court_hierarchy(connection, counts)
        repair_jianlong_office_merge(connection, counts)
        repair_monk_registry_merge(connection, counts)
        repair_officials_desk_merge(connection, counts)
        repair_medical_nine_hierarchy(connection, counts)
        remove_partial_duty_transfer_evolution(connection, counts)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    args = parser.parse_args()
    counts = apply_repairs(args.db.resolve(), args.dictionary.resolve())
    print(" ".join(f"{key}={value}" for key, value in counts.items()))
    print(f"db={args.db.resolve()}")


if __name__ == "__main__":
    main()
