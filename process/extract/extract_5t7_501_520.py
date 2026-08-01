#!/usr/bin/env python3
"""提取 chapter5t7 第501-520条：译经属官、寺务司与僧录僧正系统。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_481_500 as previous


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch5t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter5t7 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(501, 521)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
state = base.state
relation = base.relation
staff = base.staff
tp = base.tp
alias_note = base.alias_note


TIME_HINTS = {
    "南朝宋": 420, "五代后梁末帝时": 915,
    "唐代": 618, "唐宣宗朝": 850,
    "唐天宝二载": 743, "唐贞元四年（原文括注758）": 788,
    "五代后晋": 936, "五代十国": 907,
    "宋初": 960.1, "北宋": 960.2,
    "北宋太平兴国中": 980,
    "北宋太平兴国八年": 983,
    "北宋淳化四年": 993,
    "北宋大中祥符六年九月": 1013.70,
    "北宋天禧五年": 1021,
    "北宋天圣八年五月": 1030.38,
    "北宋熙宁中": 1070,
    "北宋熙宁元年十二月": 1068.96,
    "北宋熙宁四年三月": 1071.21,
    "北宋熙宁八年七月二日": 1075.51,
    "北宋熙宁八年七月二十三日": 1075.57,
    "北宋元丰新制": 1080.9,
    "北宋元丰改制后": 1082.4,
    "北宋宣和元年": 1119, "北宋宣和五年": 1123,
    "南宋建炎三年四月十三日": 1129.28,
    "南宋绍兴三年二月四日": 1133.10,
    "南宋绍兴五年正月十五日": 1135.04,
    "南宋隆兴二年": 1164,
    "宋代（传法院译官）": 1050.1,
    "宋代（在京寺务司）": 1050.2,
    "宋代（左、右街僧录司）": 1050.3,
    "宋代（地方僧正司）": 1050.4,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    m = re.search(r"(-?\d{3,4})", time or "")
    if m:
        return (int(m.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [r[0] for r in sorted(rows, key=lambda r: time_key(r[1], r[0]))]
    for n, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[n - 1] if n else None,
            succ_id=ordered[n + 1] if n + 1 < len(ordered) else None,
        )


def set_event(w, tid, event, decision):
    old = w.conn.execute("select event from Timepoints where id=?", (tid,)).fetchone()[0]
    if old != event:
        w.conn.execute("update Timepoints set event=? where id=?", (event, tid))
        w._br("Timepoints", tid, f"事件说明由‘{old}’规范为‘{event}’：{decision}")


def exact_state(w, i, title, type_, time, event, quotation, category, decision,
                field_name=None, *, officer=None, grade=None, note=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade, note=note,
    )
    set_event(w, tid, event, decision)
    return eid, tid


def normalize_zhengyi(w):
    old = w.find_entity("译经证义", "官职")
    new = w.find_entity("证义", "官职")
    if old and not new:
        w.conn.execute("update Entities set title='证义' where id=?", (old,))
        w._br("Entities", old, "按第502条独立词头，将上一批推定名‘译经证义’规范为‘证义’。")
        return old
    assert not old and new, (old, new)
    return new


def entry501():
    i, main = 501, F[501]["text"]
    w = W(i)
    eid, post = exact_state(
        w, i, "译经缀文", "官职", "宋代（传法院译官）",
        "隶译经院，在笔受初译基础上贯通润色佛经，编制二人",
        main, "传法院译经僧官", "补足译经缀文隶属、职掌与定额。", officer="译经僧官",
    )
    staff(w, i, tp(w, "传法院", "机构", "北宋太平兴国八年"), post,
          main, "传法院置译经缀文二人。", quota=2, staff_type="译经僧官")
    rechain(w, eid, "整理译经缀文时间链。")
    w.commit()


def entry502():
    i, main = 502, F[502]["text"]
    w = W(i)
    eid = normalize_zhengyi(w)
    post = w.find_timepoint(eid, "宋代（传法院译官）")
    assert post is not None
    set_event(w, post, "由义学僧充，校定梵学笔受、译经缀文所译佛经经义，编制八人",
              "补足证义职掌、任用与定额。")
    cite(w, "Timepoints", post, i, main, "补足证义职掌、任用与定额。")
    staff(w, i, tp(w, "传法院", "机构", "北宋太平兴国八年"), post,
          main, "传法院置证义八人。", quota=8, staff_type="义学僧官")
    rechain(w, eid, "整理证义时间链。")
    w.commit()


def entry503():
    i, main = 503, F[503]["text"]
    history, duty = field(i, "职源与沿革"), field(i, "职能")
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "印经院", "机构", "北宋太平兴国八年",
        "始置，制板印刷汉译佛经并颁行、出售各地",
        history, "佛经印行机构", "建立印经院始置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充印经院职能。", "职能")
    _, abolished = exact_state(
        w, i, "印经院", "机构", "北宋熙宁四年三月",
        "罢废，职事归京师显圣寺管", history,
        "佛经印行机构", "建立熙宁四年罢废节点。", "职源与沿革",
    )
    temple_eid, temple = exact_state(
        w, i, "显圣寺", "机构", "北宋熙宁四年三月",
        "接收印经院佛经印行职事", history,
        "佛寺", "建立显圣寺承接印经院职事节点。", "职源与沿革",
    )
    relation(w, i, abolished, temple, "前后演变", history,
             "熙宁四年罢印经院，职事归显圣寺。", "职源与沿革")
    touched.update((eid, temple_eid))
    for x in touched:
        rechain(w, x, "整理印经院罢废及显圣寺承接时间链。")
    w.commit()


def entry504():
    i, main = 504, F[504]["text"]
    history, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "同文馆", "机构", "北宋熙宁中",
        "创置，名称取自唐同文寺，接待高丽进奉使人",
        history, "鸿胪寺属馆驿", "建立同文馆创置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "补充接待高丽使人职掌。", "职掌")
    _, reform = exact_state(
        w, i, "同文馆", "机构", "北宋元丰新制",
        "隶鸿胪寺，接待高丽进奉使人", main,
        "鸿胪寺属馆驿", "补足元丰鸿胪寺所隶节点。",
    )
    relation(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), reform,
             "上下级机构", main, "同文馆隶鸿胪寺。")
    _, abolished = exact_state(
        w, i, "同文馆", "机构", "南宋建炎三年四月十三日",
        "罢废", history, "馆驿", "建立建炎三年罢废节点。", "职源与沿革",
    )
    _, restored = exact_state(
        w, i, "同文馆", "机构", "南宋绍兴三年二月四日",
        "复置行在同文馆", history, "馆驿",
        "建立绍兴三年复置节点。", "职源与沿革",
    )
    touched.add(eid)
    for title, officer, quota, time, event in (
        ("勾当同文馆", "勾当官", 1, "北宋熙宁中", "以内侍充，掌同文馆事"),
        ("主管同文馆", "主管官", 1, "南宋绍兴三年二月四日", "南宋改勾当官为主管官"),
        ("同文馆后行", "后行", 1, "宋代（鸿胪寺馆驿编制）", "同文馆吏额"),
        ("同文馆执役", "执役", 22, "宋代（鸿胪寺馆驿编制）", "看守本馆执役"),
    ):
        seid, post = exact_state(
            w, i, title, "官职", time, f"{event}，编制{quota}人", roster,
            "同文馆属员", f"建立{title}编制。", "编制", officer=officer,
        )
        parent = restored if time.startswith("南宋") else reform
        staff(w, i, parent, post, roster, f"同文馆置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    for x in touched:
        rechain(w, x, "整理同文馆存废及属员完整时间链。")
    w.commit()


def entry505():
    i, main, aliases = 505, F[505]["text"], field(505, "简称")
    w = W(i)
    eid, office = exact_state(
        w, i, "管勾同文馆所", "机构", "北宋熙宁中",
        "同文馆管勾官办事机构，掌高丽使节入境后的接迎、管押仪制、供需与赐物排办",
        main, "同文馆属所", "建立管勾同文馆所职掌。",
    )
    relation(w, i, tp(w, "同文馆", "机构", "北宋熙宁中"), office,
             "上下级机构", main, "管勾同文馆所为同文馆办事机构。")
    alias_note(w, i, office, aliases, "简称")
    rechain(w, eid, "整理管勾同文馆所时间链。")
    w.commit()


def entry506():
    i, main = 506, F[506]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "在京寺务司", "机构", "北宋淳化四年",
        "创置，掌京城大寺殿宇、廊舍修葺，初隶开封府使院判官",
        origin, "寺观修缮机构", "建立在京寺务司创置节点。", "职源",
    )
    cite(w, "Timepoints", start, i, duty, "补充寺观修缮职掌。", "职掌")
    parent_eid, parent = exact_state(
        w, i, "开封府使院判官", "官职", "北宋熙宁元年十二月",
        "专管勾使院公事，并管辖在京寺务司", aliases,
        "开封府属官", "建立开封府使院判官管辖寺务司节点。", "简称", officer="判官",
    )
    _, under = exact_state(
        w, i, "在京寺务司", "机构", "北宋熙宁元年十二月",
        "隶开封府判官专管勾使院公事", aliases,
        "开封府属司", "建立熙宁元年明确隶属节点。", "简称",
    )
    staff(w, i, under, parent, aliases,
          "开封府使院判官管辖在京寺务司。", "简称", staff_type="管辖判官")
    _, changed = exact_state(
        w, i, "在京寺务司", "机构", "北宋熙宁八年七月二日",
        "不再隶开封府使院判官，改隶鸿胪寺", aliases,
        "鸿胪寺属司", "建立熙宁八年改隶节点。", "简称",
    )
    relation(w, i, tp(w, "鸿胪寺", "机构", "宋前期"), changed,
             "上下级机构", main, "在京寺务司后改隶鸿胪寺。")
    touched.update((eid, parent_eid))
    for title, officer, quota in (
        ("提点在京寺务司", "提点官", 1), ("监在京寺务司", "监官", 1),
    ):
        seid, post = exact_state(
            w, i, title, "官职", "宋代（在京寺务司）",
            f"在京寺务司所置{officer}，编制{quota}人", roster,
            "在京寺务司属官", f"建立{title}定额。", "编制", officer=officer,
        )
        staff(w, i, changed, post, roster, f"在京寺务司置{officer}{quota}人。", "编制",
              quota=quota, staff_type=officer)
        touched.add(seid)
    alias_note(w, i, changed, aliases, "简称")
    for x in touched:
        rechain(w, x, "整理在京寺务司隶属及属官完整时间链。")
    w.commit()


def entry507():
    i, main, aliases = 507, F[507]["text"], field(507, "简称")
    w = W(i)
    eid, post = exact_state(
        w, i, "提点在京寺务司", "官职", "北宋熙宁八年七月二日",
        "以内侍官充，掌管辖寺务司事；寺务司不再隶开封府使院判官",
        main, "在京寺务司提点官", "建立熙宁八年提点官任用与职掌。", officer="内侍差遣",
    )
    staff(w, i, tp(w, "在京寺务司", "机构", "北宋熙宁八年七月二日"), post,
          main, "在京寺务司由内侍提点。", staff_type="提点官")
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理提点在京寺务司时间链。")
    w.commit()


def entry508():
    i, main, aliases = 508, F[508]["text"], field(508, "简称")
    w = W(i)
    eid, office = exact_state(
        w, i, "提点在京寺务所", "机构", "宋代（在京寺务司）",
        "提点在京寺务司官的办事机构", main,
        "在京寺务司属所", "建立提点在京寺务所。",
    )
    relation(w, i, tp(w, "在京寺务司", "机构", "北宋熙宁八年七月二日"), office,
             "上下级机构", main, "提点在京寺务所为寺务司提点官办事机构。")
    alias_note(w, i, office, aliases, "简称")
    rechain(w, eid, "整理提点在京寺务所时间链。")
    w.commit()


def entry509():
    i, main = 509, F[509]["text"]
    origin, duty = field(i, "职源"), field(i, "职掌")
    w = W(i)
    touched = set()
    eid, start = exact_state(
        w, i, "课利司", "机构", "北宋雍熙四年",
        "始置，隶三司，掌京师寺观、邸店、庄园应纳衣钵钱物、房钱与课额",
        origin, "三司属司", "建立课利司始置节点。", "职源",
    )
    cite(w, "Timepoints", start, i, main, "补充课利司隶属。")
    cite(w, "Timepoints", start, i, duty, "补充课利司职掌。", "职掌")
    relation(w, i, tp(w, "三司", "机构", "宋初"), start,
             "上下级机构", main, "课利司隶三司。")
    officer_eid, officer = exact_state(
        w, i, "寺务司官", "官职", "宋代（在京寺务司）",
        "兼领课利司", main, "寺务司属官合称",
        "建立兼领课利司的寺务司官。", officer="兼领官",
    )
    staff(w, i, start, officer, main, "课利司由寺务司官兼领。", staff_type="兼领官")
    touched.update((eid, officer_eid))
    for x in touched:
        rechain(w, x, "整理课利司及兼领寺务司官时间链。")
    w.commit()


def entry510():
    i, main = 510, F[510]["text"]
    history, duty, grade = field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位")
    w = W(i)
    eid, tang = exact_state(
        w, i, "功德使", "官职", "唐贞元四年（原文括注758）",
        "始置左、右街功德使，总道士、女冠之籍；原文括注公元758，与贞元四年不合，照录纪年并注明",
        history, "宗教事务兼官", "建立唐代功德使始置节点。", "职源与沿革", officer="功德使",
        note="原文‘德宗贞元四年（758）’年号与公元括注不合；保留原文并以贞元四年排序。",
    )
    cite(w, "Timepoints", tang, i, duty, "补充僧道选补与考试职掌。", "职掌")
    _, jin = exact_state(
        w, i, "功德使", "官职", "五代后晋",
        "始由开封尹兼任", history, "宗教事务兼官",
        "建立后晋任用节点。", "职源与沿革", officer="开封尹兼官",
    )
    _, song = exact_state(
        w, i, "功德使", "官职", "北宋",
        "沿五代之制，由开封府尹兼任，掌僧尼、道冠选补与学业考试",
        history, "宗教事务兼官", "建立北宋沿置节点。", "职源与沿革", officer="开封府尹兼官",
    )
    cite(w, "Timepoints", song, i, grade, "补充开封府尹兼任及权位。", "品位")
    _, ended = exact_state(
        w, i, "功德使", "官职", "北宋元丰改制后",
        "不再设置", history, "宗教事务兼官",
        "建立元丰改制后停设节点。", "职源与沿革", officer="功德使",
    )
    rechain(w, eid, "整理功德使完整时间链。")
    w.commit()


def entry511():
    i, main = 511, F[511]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    eid, tang = exact_state(
        w, i, "左、右街僧录司", "机构", "唐代",
        "已设左、右街僧录司，分左、右二司", origin,
        "佛教事务机构合称", "建立唐代左、右街僧录司节点。", "职源",
    )
    _, song = exact_state(
        w, i, "左、右街僧录司", "机构", "北宋元丰新制",
        "隶鸿胪寺，通管佛教教门公事，掌僧尼帐籍及僧官补授",
        main, "鸿胪寺属司合称", "补足宋代隶属与职掌节点。",
    )
    cite(w, "Timepoints", song, i, duty, "补充佛教教门职掌。", "职掌")
    relation(w, i, tp(w, "鸿胪寺", "机构", "北宋元丰新制"), song,
             "上下级机构", main, "左、右街僧录司隶鸿胪寺。")
    touched.add(eid)
    for title in ("左街僧录司", "右街僧录司"):
        seid, member = exact_state(
            w, i, title, "机构", "宋代（左、右街僧录司）",
            "左、右街僧录司之一", main,
            "佛教事务机构", f"建立{title}实例。",
        )
        relation(w, i, song, member, "统称与实例", main,
                 f"{title}为左、右街僧录司实例。")
        touched.add(seid)
    alias_note(w, i, song, aliases, "简称")
    for x in touched:
        rechain(w, x, "整理左、右街僧录司及左右实例时间链。")
    w.commit()


def paired_monk_post(i, collective, time, event, category, quotation,
                     field_name=None, aliases=None, instance_quotation=None):
    w = W(i)
    touched = set()
    eid, group = exact_state(
        w, i, collective, "官职", time, event, quotation,
        category + "合称", f"建立{collective}节点。", field_name, officer="僧官合称",
    )
    touched.add(eid)
    stem = collective.removeprefix("左、右街")
    for side in ("左街", "右街"):
        title = side + stem
        member_quote = instance_quotation or quotation
        seid, post = exact_state(
            w, i, title, "官职", time, f"{collective}所含{title}", member_quote,
            category, f"建立{title}实例。", field_name, officer="僧官",
        )
        relation(w, i, group, post, "统称与实例", member_quote,
                 f"{title}为{collective}实例。", field_name)
        staff(w, i, tp(w, side + "僧录司", "机构", "宋代（左、右街僧录司）"), post,
              member_quote, f"{side}僧录司设置{title}。", field_name, staff_type="僧官")
        touched.add(seid)
    if aliases:
        alias_note(w, i, group, aliases, "简称")
    for x in touched:
        rechain(w, x, f"整理{collective}及左右实例时间链。")
    w.commit()


def entry512():
    i = 512
    main = F[i]["text"]
    origin, duty, aliases = field(i, "职源"), field(i, "职掌"), field(i, "简称")
    w = W(i)
    eid, tang = exact_state(
        w, i, "左、右街正僧录", "官职", "唐代",
        "唐置左右街僧录官，尚无正、副之分", origin,
        "僧录合称", "建立唐代僧录源流节点。", "职源", officer="僧录",
    )
    rechain(w, eid, "整理左、右街正僧录唐代源流时间链。")
    w.commit()
    paired_monk_post(i, "左、右街正僧录", "北宋",
                     "北宋始设正僧录", "正僧录", origin, "职源", aliases, main)
    w = W(i)
    group = tp(w, "左、右街正僧录", "官职", "北宋")
    cite(w, "Timepoints", group, i, duty, "补充管干佛教教门公事职掌。", "职掌")
    set_event(w, group, "北宋始设正僧录，管干佛教教门公事", "合并职源与职掌说明。")
    w.commit()


def entry513():
    i = 513
    main = F[i]["text"]
    origin, duty = field(i, "职源"), field(i, "职掌")
    paired_monk_post(i, "左、右街副僧录", "北宋太平兴国中",
                     "始置", "副僧录", origin, "职源", instance_quotation=main)
    w = W(i)
    first = tp(w, "左、右街副僧录", "官职", "北宋太平兴国中")
    cite(w, "Timepoints", first, i, duty, "补充宋初演讲经论职掌。", "职掌")
    set_event(w, first, "始置，宋初演讲经论", "合并职源与职掌说明。")
    eid, later = exact_state(
        w, i, "左、右街副僧录", "官职", "北宋天圣八年五月",
        "与正僧录同管勾佛教教门公事", duty,
        "副僧录合称", "建立天圣八年职掌变化节点。", "职掌", officer="僧官合称",
    )
    rechain(w, eid, "整理左、右街副僧录完整时间链。")
    w.commit()


def entry514():
    i, main = 514, F[514]["text"]
    paired_monk_post(i, "左、右街都监", "北宋太平兴国中",
                     "始置，位在首座之上", "僧录司都监", main)


def entry515():
    i = 515
    main = F[i]["text"]
    origin, duty, aliases = field(i, "职源"), field(i, "职掌"), field(i, "简称")
    w = W(i)
    eid, tang = exact_state(
        w, i, "左、右街首座", "官职", "唐宣宗朝",
        "首座之名始见", origin, "僧录司首座合称",
        "建立首座唐代源流节点。", "职源", officer="僧官合称",
    )
    rechain(w, eid, "整理左、右街首座唐代源流时间链。")
    w.commit()
    paired_monk_post(i, "左、右街首座", "北宋太平兴国中",
                     "始置", "僧录司首座", origin, "职源", aliases, main)
    w = W(i)
    group = tp(w, "左、右街首座", "官职", "北宋太平兴国中")
    cite(w, "Timepoints", group, i, duty, "补充演讲经论职掌。", "职掌")
    set_event(w, group, "始置，演讲经论", "合并职源与职掌说明。")
    w.commit()


def entry516():
    i = 516
    main = F[i]["text"]
    origin, duty, aliases = field(i, "职源"), field(i, "职掌"), field(i, "简称")
    paired_monk_post(i, "左、右街鉴义", "北宋天禧五年",
                     "始置", "僧录司鉴义", origin, "职源", aliases, main)
    w = W(i)
    group = tp(w, "左、右街鉴义", "官职", "北宋天禧五年")
    cite(w, "Timepoints", group, i, duty, "补充鉴义职掌。", "职掌")
    set_event(w, group, "始置，演讲经论并删定译经院所译佛经", "合并职源与职掌说明。")
    w.commit()


def entry517():
    i, main = 517, F[517]["text"]
    paired_monk_post(i, "左、右街守阙鉴义", "宋代（左、右街僧录司）",
                     "非正官鉴义，为候阙待补的额外编制",
                     "僧录司守阙鉴义", main)


def entry518():
    i, main = 518, F[518]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    touched = set()
    eid, song = exact_state(
        w, i, "僧正司", "机构", "宋初",
        "始见置，为地方州军僧官机构，掌本州府军僧尼帐籍及寺庙事务",
        history, "地方佛教事务机构", "建立僧正司宋初节点。", "职源与沿革",
    )
    cite(w, "Timepoints", song, i, duty, "补充僧正司职掌。", "职掌")
    _, renamed = exact_state(
        w, i, "僧正司", "机构", "北宋宣和元年",
        "改名德士司", history, "地方佛教事务机构",
        "建立宣和元年改名节点。", "职源与沿革",
    )
    successor_eid, successor = exact_state(
        w, i, "德士司", "机构", "北宋宣和元年",
        "由天下州府僧正司改名", history, "地方佛教事务机构",
        "建立德士司承接节点。", "职源与沿革",
    )
    relation(w, i, renamed, successor, "前后演变", history,
             "宣和元年僧正司改名德士司。", "职源与沿革")
    _, restored = exact_state(
        w, i, "僧正司", "机构", "北宋宣和五年",
        "已恢复旧名", history, "地方佛教事务机构",
        "建立宣和五年复名节点。", "职源与沿革",
    )
    _, south = exact_state(
        w, i, "僧正司", "机构", "南宋隆兴二年",
        "南宋地方仍见设置", history, "地方佛教事务机构",
        "建立南宋沿置节点。", "职源与沿革",
    )
    bureau_eid, bureau = exact_state(
        w, i, "僧录院", "机构", "宋代（地方僧正司）",
        "管辖地方僧正司", roster, "佛教事务机构",
        "据僧正司归属建立僧录院节点。", "编制",
    )
    relation(w, i, bureau, song, "上下级机构", roster,
             "僧正司归僧录院管。", "编制")
    alias_note(w, i, song, aliases, "简称")
    touched.update((eid, successor_eid, bureau_eid))
    for x in touched:
        rechain(w, x, "整理僧正司、德士司及僧录院管辖时间链。")
    w.commit()


def entry519():
    i, main = 519, F[519]["text"]
    origin, duty = field(i, "职源"), field(i, "职掌")
    w = W(i)
    eid, ancient = exact_state(
        w, i, "僧正", "官职", "南朝宋",
        "已有僧正之名", origin, "地方僧官",
        "建立僧正南朝源流节点。", "职源", officer="僧官",
    )
    _, abolished = exact_state(
        w, i, "僧正", "官职", "五代后梁末帝时",
        "废罢", origin, "地方僧官",
        "建立后梁废罢节点。", "职源", officer="僧官",
    )
    _, song = exact_state(
        w, i, "僧正", "官职", "北宋大中祥符六年九月",
        "诸州军设置，为僧正司主管官，掌本州军僧尼名籍与寺院事务",
        duty, "地方僧官", "建立宋代僧正职掌节点。", "职掌", officer="僧正",
    )
    staff(w, i, tp(w, "僧正司", "机构", "宋初"), song,
          duty, "僧正司设置僧正主管本州军佛教事务。", "职掌", staff_type="僧正")
    rechain(w, eid, "整理僧正完整时间链。")
    w.commit()


def entry520():
    i, main = 520, F[520]["text"]
    w = W(i)
    eid, start = exact_state(
        w, i, "德士司", "机构", "北宋宣和元年",
        "由天下州府僧正司改名", main,
        "地方佛教事务机构", "补足德士司改名节点。",
    )
    relation(w, i, tp(w, "僧正司", "机构", "北宋宣和元年"), start,
             "前后演变", main, "宣和元年僧正司改名德士司。")
    _, restored = exact_state(
        w, i, "德士司", "机构", "北宋宣和五年",
        "复旧名僧正司", main,
        "地方佛教事务机构", "建立宣和五年复旧名节点。",
    )
    relation(w, i, restored, tp(w, "僧正司", "机构", "北宋宣和五年"),
             "前后演变", main, "宣和五年德士司复名僧正司。")
    rechain(w, eid, "整理德士司改名及复名时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(501, 521)] == [
        "译经缀文", "证义", "印经院", "同文馆", "管勾同文馆所",
        "在京寺务司", "提点在京寺务司", "提点在京寺务所", "课利司",
        "功德使", "左、右街僧录司", "左、右街正僧录", "左、右街副僧录",
        "左、右街都监", "左、右街首座", "左、右街鉴义",
        "左、右街守阙鉴义", "僧正司", "僧正", "德士司",
    ]
    for i in range(501, 521):
        globals()[f"entry{i}"]()


if __name__ == "__main__":
    main()
