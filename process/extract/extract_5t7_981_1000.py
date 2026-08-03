#!/usr/bin/env python3
"""提取 chapter5t7 第981-1000条：都水监丞、主簿与南北外丞司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_961_980 as previous


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


F = {i: load(i) for i in range(981, 1001)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
state = base.state
relation = base.relation
staff = base.staff
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
parent_child = previous.parent_child
evolution = previous.evolution
group_instances = previous.group_instances


TIME_HINTS = {
    "秦汉": -200,
    "西晋": 280,
    "隋大业三年": 607,
    "宋初": 960,
    "北宋嘉祐三年十一月二十二日": 1058.89,
    "北宋元丰三年八月二十二日前": 1080.63,
    "北宋元丰三年八月二十二日": 1080.64,
    "北宋元丰三年九月二十八日": 1080.74,
    "北宋元丰正名（具体年月未载）": 1081,
    "北宋元丰五年前": 1081.9,
    "北宋元丰五年": 1082,
    "北宋元丰、元祐间（具体年月未载）": 1084,
    "北宋元祐元年四月四日": 1086.27,
    "北宋（外都水监丞司分南北前，具体年月未载）": 1070,
    "北宋元丰六年七月六日": 1083.52,
    "南宋绍兴九年": 1139,
    "南宋绍兴十年": 1140,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    match = re.search(r"(-?\d{3,4})", time or "")
    if match:
        return (int(match.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def canonicalize_outside_envoy(w, quotation):
    old = w.find_entity("外都水使者", "官职")
    formal = w.find_entity("外都水监使者", "官职")
    if old is not None:
        assert formal is None or formal == old, (old, formal)
        w.conn.execute(
            "update Entities set title='外都水监使者',quotation=? where id=?",
            (quotation, old),
        )
        w._br(
            "Entities", old,
            "第987条正式词头为外都水监使者；将前批据编制段建立的简称外都水使者规范为正式名。",
        )
        formal = old
    return formal


def entry981():
    i, main = 981, F[981]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    post = node(
        w, touched, i, "管勾都水监丞公事", "官职", "北宋元丰五年前",
        "以他官兼充的都水监丞差遣，或称知、管勾",
        main, "差遣官", "记录元丰五年前管勾都水监丞公事的差遣性质。",
        update_event=True,
    )
    evolution(
        w, touched, i, "管勾都水监丞公事", "都水监丞", "北宋元丰五年",
        main, "元丰五年后都水监丞始正式除人，管勾差遣转为职事官。",
        source_type="官职", target_type="官职",
        source_event="新官制后不再作为兼充差遣",
        target_event="元丰五年后始正式除人",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理管勾都水监丞公事在元丰改制前的差遣性质及元丰五年正名。")


def entry982():
    i = 982
    main = F[i]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "都水监丞", "官职", "秦汉",
         "已有都水丞官", origin, "前代水官源流",
         "记录秦汉都水丞源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "都水监丞", "官职", "隋大业三年",
         "始置都水监丞", origin, "前代水官源流",
         "记录隋大业三年始置都水监丞。", "职源与沿革", update_event=True)
    _, post, _ = office_staff(
        w, touched, i, "都水监", "都水监丞", "北宋元丰五年",
        roster, "都水监丞编制二人，另有外监丞一至二人。", "编制",
        quota=2, staff_type="丞", office_event="元丰新制设置都水监丞",
        post_event="参领本监公事，编制二人", grade="从八品",
    )
    cite(w, "Timepoints", post, i, main, "确认都水监丞为职事官。")
    cite(w, "Timepoints", post, i, duty, "补证内丞参领本监、外丞出外治河职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证从八品及班序。", "品位")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "补全都水监丞秦汉隋源流、元丰职事官品位、职掌、编制与简称。")


def entry983():
    i, main = 983, F[983]["text"]
    w, touched = W(i), set()
    for time, event in (
        ("北宋元丰三年八月二十二日前",
         "三员配置：一员在外治理河埽、二员在京都水监"),
        ("北宋元丰三年八月二十二日",
         "三员配置改为二员在外分管南北司、一员留在本监"),
    ):
        group_instances(
            w, touched, i, "都水监内外监丞", "官职", time, event,
            ("都水监丞", "外都水监丞"), main,
            "原文以都水监内外监丞统称本监与外治河的三名监丞。",
        )
    finish(w, touched, "整理都水监内外监丞三员统称及元丰三年内外员额转换。")


def entry984():
    i, main = 984, F[984]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "都水监", "知都水监主簿公事",
        "北宋嘉祐三年十一月二十二日", origin,
        "嘉祐三年始置知都水监主簿公事一人。", "职源与沿革",
        quota=1, staff_type="知主簿事", office_event="初置并设知主簿事",
        post_event="掌领簿书并可干办修河公事", officer="京朝官充",
    )
    cite(w, "Timepoints", post, i, main, "确认知都水监主簿公事为差遣。")
    cite(w, "Timepoints", post, i, duty, "补证簿书及修河职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "补证以京朝官充。", "品位")
    cite(w, "Timepoints", post, i, roster, "补证编制一人。", "编制")
    evolution(
        w, touched, i, "知都水监主簿公事", "都水监主簿",
        "北宋元丰正名（具体年月未载）", origin,
        "元丰正名罢知主簿差遣，改称都水监主簿。", "职源与沿革",
        source_type="官职", target_type="官职",
        source_event="元丰正名罢差遣", target_event="元丰正名为职事官",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理知都水监主簿公事嘉祐始置、职掌编制及元丰正名。")


def entry985():
    i, main = 985, F[985]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    for time, event in (
        ("西晋", "水衡都尉下设主簿"),
        ("隋大业三年", "置都水监主簿"),
        ("宋初", "沿唐制为文臣迁转阶官，后不复设"),
    ):
        node(w, touched, i, "都水监主簿", "官职", time, event,
             origin, "主簿源流或阶官", f"记录都水监主簿{time}沿革。",
             "职源与沿革", update_event=True)
    reform = node(
        w, touched, i, "都水监主簿", "官职",
        "北宋元丰正名（具体年月未载）",
        "始正式除人，掌本监簿书，不许签书公事",
        origin, "职事官", "记录元丰正名后都水监主簿始除人。",
        "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", reform, i, main, "确认兼具阶官与职事官性质。")
    cite(w, "Timepoints", reform, i, duty, "补证元丰后的簿书职掌与签书限制。", "职掌")
    node(w, touched, i, "都水监主簿", "官职", "南宋绍兴十年",
         "罢置", origin, "废罢官职", "记录绍兴十年罢都水监主簿。",
         "职源与沿革", update_event=True)
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "整理都水监主簿西晋隋源流、宋初阶官、元丰职事与绍兴罢置。")


def entry986():
    i, main = 986, F[986]["text"]
    aliases = field(i, "别称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "都水监", "勾当都水监公事",
        "北宋元丰、元祐间（具体年月未载）", main,
        "元丰、元祐间临时添置勾当都水监公事，非常员。",
        staff_type="临时勾当官", office_event="临时添置勾当官外出治河",
        post_event="临时外出干办修治黄河，非常员",
    )
    alias_note(w, i, post, aliases, "别称")
    finish(w, touched, "整理勾当都水监公事元丰元祐临时设置、外出治河与别称。")


def entry987():
    i, main = 987, F[987]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    eid = canonicalize_outside_envoy(w, main)
    if eid is not None:
        touched.add(eid)
    _, post, _ = office_staff(
        w, touched, i, "都水监", "外都水监使者",
        "北宋元祐元年四月四日", aliases,
        "元祐元年添置外都水监使者一员。", "简称",
        quota=1, staff_type="外使者", office_event="添置外都水监使者",
        post_event="掌黄河决口改道，可由河北路转运水使兼任",
        officer="或由河北路转运水使兼",
    )
    cite(w, "Timepoints", post, i, main,
         "补证外都水监使者始置、治河职掌及北外监丞领属。")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "恢复外都水监使者正式词头，整理元祐始置、员额、治河职掌与简称。")


def entry988():
    i, main = 988, F[988]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    office = node(
        w, touched, i, "外都水监丞司", "机构",
        "北宋嘉祐三年十一月二十二日",
        "置司澶州，由监丞一员领黄河决口改道后修治公事",
        main, "外治河机构", "补全外都水监丞司始置、治所与职掌。",
        update_event=True,
    )
    parent_child(
        w, touched, i, "都水监", "外都水监丞司",
        "北宋嘉祐三年十一月二十二日", main,
        "都水监置外都水监丞司于澶州。",
        parent_event="设置外都水监丞司",
        child_event="置司澶州，领黄河决口改道后修治公事",
    )
    for target in ("外都水监丞南司", "外都水监丞北司"):
        evolution(
            w, touched, i, "外都水监丞司", target,
            "北宋元丰三年八月二十二日", main,
            f"元丰三年八月二十二日外都水监丞司一分为南北二司，{target}为其一。",
            source_event="一分为外都水监丞南司、北司",
            target_event="由外都水监丞司分置",
        )
    alias_note(w, i, office, aliases, "简称")
    finish(w, touched, "整理外都水监丞司嘉祐置司、都水监隶属、职掌及元丰分南北司。")


def entry989():
    i, main = 989, F[989]["text"]
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    post = node(
        w, touched, i, "外都水监丞", "官职", "北宋元丰三年八月二十二日前",
        "都水监丞轮差在外治河的便称，正式称知都水监丞公事",
        main, "外治河监丞便称", "按正式词头建立外都水监丞官职节点。",
        update_event=True,
    )
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理外都水监丞正式词头、便称性质、对应正称与别名。")


def entry990():
    i, main = 990, F[990]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "外都水监丞司", "管勾外都水监丞司公事",
        "北宋（外都水监丞司分南北前，具体年月未载）", main,
        "外都水监丞司置管勾官一至二员，资浅者带同字。",
        staff_type="管勾属官（一至二员）",
        office_event="设置管勾属官一至二员",
        post_event="干办所管地分治河公事，位在外监丞之下",
    )
    finish(w, touched, "整理管勾外都水监丞司公事的属官性质、员额、位次与治河职掌。")


def entry991():
    assert F[991]["text"] == ""
    assert F[991]["fields"].get("_placeholder") is True


def entry992():
    i, main = 992, F[992]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "外都水监丞司", "勾当外都水监丞司公事",
        "北宋（外都水监丞司分南北前，具体年月未载）", main,
        "勾当外都水监丞司公事为本司属员，职掌同管勾官而资序稍次。",
        staff_type="勾当属员", office_event="设置勾当属员",
        post_event="职掌同管勾官，资序稍次",
    )
    finish(w, touched, "整理勾当外都水监丞司公事的属员性质、职掌与资序。")


def entry993():
    assert F[993]["text"] == ""
    assert F[993]["fields"].get("_placeholder") is True


def entry994():
    i, main = 994, F[994]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    _, south = evolution(
        w, touched, i, "外都水监丞司", "外都水监丞南司",
        "北宋元丰三年八月二十二日", origin,
        "元丰三年八月分外都水监丞司为南北二司。", "职源与沿革",
        source_event="一分为外都水监丞南司、北司",
        target_event="分置，治所在河阴县，管南岸等三十六埽",
    )
    cite(w, "Timepoints", south, i, main, "补证南司官司性质及河阴县治所。")
    cite(w, "Timepoints", south, i, duty, "补证南司三十六埽治河范围。", "职掌")
    office_staff(
        w, touched, i, "外都水监丞南司", "知外都水监丞南司公事",
        "北宋元丰三年八月二十二日", roster,
        "外都水监丞南司由一员外都水监丞分管。", "编制",
        quota=1, staff_type="外监丞", office_event="由一员外监丞分管",
        post_event="分管南司，辖四都大提举司",
    )
    evolution(
        w, touched, i, "外都水监丞南司", "南外都水监丞司",
        "北宋元丰三年九月二十八日", origin,
        "元丰三年九月二十八日南司改名南外都水监丞司。", "职源与沿革",
        source_event="改名南外都水监丞司", target_event="由外都水监丞南司改名",
    )
    finish(w, touched, "整理外都水监丞南司分置、治所职掌、外丞编制及九月改名。")


def entry995():
    i, main = 995, F[995]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "外都水监丞南司", "知外都水监丞南司公事",
        "北宋元丰三年八月二十二日", main,
        "元丰三年八月始置知外都水监丞南司公事。",
        quota=1, staff_type="知南司公事",
        office_event="设置知司公事", post_event="领外都水监丞南司公事",
    )
    evolution(
        w, touched, i, "知外都水监丞南司公事", "知南外都水监丞司公事",
        "北宋元丰三年九月二十八日", main,
        "随南司改名，知南司公事改称知南外都水监丞司公事。",
        source_type="官职", target_type="官职",
        source_event="改称知南外都水监丞司公事",
        target_event="由知外都水监丞南司公事改名",
    )
    finish(w, touched, "整理知外都水监丞南司公事始置、领司与九月改名。")


def entry996():
    i, main = 996, F[996]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "南外都水监丞司", "机构",
        "北宋元丰三年九月二十八日",
        "由外都水监丞南司改名，置司澶州",
        main, "外治河机构", "记录南外都水监丞司改名与治所。",
        update_event=True,
    )
    node(w, touched, i, "南外都水监丞司", "机构", "南宋绍兴九年",
         "复置，治所在南京应天府", main, "复置外治河机构",
         "记录绍兴九年复置与治所。", update_event=True)
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理南外都水监丞司元丰改名、澶州治所、绍兴复置与简称。")


def entry997():
    i, main = 997, F[997]["text"]
    w, touched = W(i), set()
    evolution(
        w, touched, i, "知外都水监丞南司公事", "知南外都水监丞司公事",
        "北宋元丰三年九月二十八日", main,
        "元丰三年九月二十八日随司名改称。",
        source_type="官职", target_type="官职",
        source_event="改称知南外都水监丞司公事",
        target_event="由知外都水监丞南司公事改名，掌领南外司",
    )
    _, post, _ = office_staff(
        w, touched, i, "南外都水监丞司", "知南外都水监丞司公事",
        "北宋元丰三年九月二十八日", main,
        "知南外都水监丞司公事隶都水监并掌领南外司。",
        quota=1, staff_type="南外监丞", office_event="设置知司公事一人",
        post_event="掌领南外司，位次北外监丞、都水监丞",
    )
    cite(w, "Timepoints", post, i, main,
         "简称段只作知南外都水丞等名称证据，不另建别名实体。",
         note="简称不另建实体")
    finish(w, touched, "整理知南外都水监丞司公事元丰改名、编制隶属、职掌位次与简称。")


def entry998():
    i, main = 998, F[998]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    w, touched = W(i), set()
    _, north = evolution(
        w, touched, i, "外都水监丞司", "外都水监丞北司",
        "北宋元丰三年八月二十二日", origin,
        "元丰三年八月分外都水监丞司为南北二司。", "职源与沿革",
        source_event="一分为外都水监丞南司、北司",
        target_event="分置，治所在北京金堤，管黄河及御河等河防",
    )
    cite(w, "Timepoints", north, i, main, "补证北司官司性质及北京金堤治所。")
    cite(w, "Timepoints", north, i, duty, "补证北司三十三埽及三河河防范围。", "职掌")
    office_staff(
        w, touched, i, "外都水监丞北司", "知外都水监丞北司公事",
        "北宋元丰三年八月二十二日", roster,
        "外都水监丞北司由一员外都水监丞分管。", "编制",
        quota=1, staff_type="外监丞", office_event="由一员外监丞分管",
        post_event="分管北司，辖四都大提举司",
    )
    evolution(
        w, touched, i, "外都水监丞北司", "北外都水监丞司",
        "北宋元丰三年九月二十八日", origin,
        "元丰三年九月二十八日北司改名北外都水监丞司。", "职源与沿革",
        source_event="改名北外都水监丞司", target_event="由外都水监丞北司改名",
    )
    finish(w, touched, "整理外都水监丞北司分置、治所职掌、外丞编制及九月改名。")


def entry999():
    i, main = 999, F[999]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "外都水监丞北司", "知外都水监丞北司公事",
        "北宋元丰三年八月二十二日", main,
        "元丰三年八月始置知外都水监丞北司公事。",
        quota=1, staff_type="知北司公事",
        office_event="设置知司公事", post_event="领外都水监丞北司公事",
    )
    evolution(
        w, touched, i, "知外都水监丞北司公事", "知北外都水监丞司公事",
        "北宋元丰三年九月二十八日", main,
        "随北司改名，知北司公事改称知北外都水监丞司公事。",
        source_type="官职", target_type="官职",
        source_event="改称知北外都水监丞司公事",
        target_event="由知外都水监丞北司公事改名",
    )
    finish(w, touched, "整理知外都水监丞北司公事始置、领司与九月改名。")


def entry1000():
    i, main = 1000, F[1000]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "北外都水监丞司", "机构",
        "北宋元丰三年九月二十八日",
        "由外都水监丞北司改名，治所在澶州",
        main, "外治河机构", "记录北外都水监丞司改名与治所。",
        update_event=True,
    )
    node(w, touched, i, "北外都水监丞司", "机构",
         "北宋元丰六年七月六日", "治所移恩州",
         main, "外治河机构", "记录元丰六年移治恩州。", update_event=True)
    node(w, touched, i, "北外都水监丞司", "机构", "南宋绍兴九年",
         "复置，治所在东京开封", main, "复置外治河机构",
         "记录绍兴九年复置与治所。", update_event=True)
    node(w, touched, i, "北外都水监丞司", "机构", "南宋绍兴十年",
         "罢置", main, "废罢机构", "记录绍兴十年罢北外司。",
         update_event=True)
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理北外都水监丞司元丰改名移治、绍兴复置罢置与简称。")


def main():
    for i in range(981, 1001):
        globals()[f"entry{i}"]()
        suffix = " placeholder skipped" if i in (991, 993) else " done"
        print(f"#{i} {F[i]['title']}{suffix}")


if __name__ == "__main__":
    main()
