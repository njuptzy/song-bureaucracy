#!/usr/bin/env python3
"""提取 chapter5t7 第941-960条：将作监、修内司及东、西八作司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_921_940 as previous


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


F = {i: load(i) for i in range(941, 961)}
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


TIME_HINTS = {
    "秦汉": -200,
    "西汉景帝中六年": -144,
    "西晋": 280,
    "隋开皇二十年": 600,
    "隋大业三年": 607,
    "隋大业五年": 609,
    "唐开元十五年": 727,
    "宋初": 960,
    "北宋初": 960.1,
    "北宋前期": 1000,
    "北宋大中祥符五年七月": 1012.54,
    "北宋前期（东、西广备指挥先后隶属，具体年月未载）": 1050,
    "北宋（原供役广备攻城作，具体年月未载）": 1060,
    "北宋熙宁四年十月": 1071.75,
    "北宋熙宁四年十一月一日": 1071.83,
    "北宋熙宁四年十一月二日": 1071.831,
    "北宋熙宁六年八月": 1073.62,
    "北宋熙宁以后（具体年月未载）": 1074,
    "北宋（后入东、西八作司，具体年月未载）": 1075,
    "北宋元丰寄禄格": 1080,
    "北宋元丰新制": 1080.1,
    "北宋元丰五年": 1082,
    "宋代（广备攻城作，具体年月未载）": 1060.1,
    "宋代（广备攻城作二十一作，具体年月未载）": 1060.2,
    "宋代（弓弩院，具体年月未载）": 1100,
    "宋代（将作监官属，具体年月未载）": 1100.1,
    "北宋（提举内中修造，具体年月未载）": 1100.2,
    "北宋（提举在内修造，具体年月未载）": 1100.3,
    "北宋真宗朝（具体年月未载）": 1020,
    "北宋熙宁间（具体年月未载）": 1070,
    "南宋建炎三年四月十三日": 1129.29,
    "南宋绍兴三年十月八日": 1133.78,
    "南宋绍兴三年十月二十九日": 1133.83,
    "南宋绍兴十年": 1140,
    "南宋绍兴十一年四月二十二日": 1141.30,
    "南宋（修内司，具体年月未载）": 1150,
    "南宋（提举修内司，具体年月未载）": 1150.1,
    "南宋（提辖修内司，具体年月未载）": 1150.2,
    "南宋（干办修内司公事，具体年月未载）": 1150.3,
    "南宋淳熙间": 1180,
    "南宋中后期（具体年月未载）": 1200,
    "宋代（东、西八作司八作，具体年月未载）": 1100.4,
    "宋代（东、西八作司勾当官，具体年月未载）": 1100.5,
    "南宋（东、西八作司，具体年月未载）": 1150.4,
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


def set_event(w, tid, event, decision):
    old = w.conn.execute("select event from Timepoints where id=?", (tid,)).fetchone()[0]
    if old == event:
        return
    w.conn.execute("update Timepoints set event=? where id=?", (event, tid))
    w._br("Timepoints", tid, f"事件说明由‘{old}’规范为‘{event}’：{decision}")


def node(w, touched, i, title, type_, time, event, quotation, category,
         decision, field_name=None, *, officer=None, grade=None,
         update_event=False):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )
    if update_event:
        set_event(w, tid, event, decision)
    touched.add(eid)
    return tid


def office_staff(w, touched, i, office, post, time, quotation, decision,
                 field_name=None, *, quota=None, staff_type="官",
                 office_event=None, post_event=None, officer=None, grade=None):
    office_tid = node(
        w, touched, i, office, "机构", time,
        office_event or f"设置{post}", quotation, "办事机构",
        f"建立或复用{office}{time}编制节点。", field_name,
    )
    post_tid = node(
        w, touched, i, post, "官职", time,
        post_event or f"领{office}事", quotation, "职事或差遣官",
        f"建立或复用{post}{time}节点。", field_name,
        officer=officer, grade=grade,
    )
    rid = staff(
        w, i, office_tid, post_tid, quotation, decision, field_name,
        quota=quota, staff_type=staff_type,
    )
    return office_tid, post_tid, rid


def parent_child(w, touched, i, parent, child, time, quotation, decision,
                 field_name=None, *, parent_event=None, child_event=None):
    parent_tid = node(
        w, touched, i, parent, "机构", time,
        parent_event or f"统辖{child}", quotation, "上级机构",
        f"建立或复用{parent}{time}节点。", field_name,
    )
    child_tid = node(
        w, touched, i, child, "机构", time,
        child_event or f"隶属{parent}", quotation, "所属机构",
        f"建立或复用{child}{time}节点。", field_name,
    )
    relation(
        w, i, parent_tid, child_tid, "上下级机构", quotation,
        decision, field_name,
    )
    return parent_tid, child_tid


def evolution(w, touched, i, source_title, target_title, time, quotation,
              decision, field_name=None, *, source_type="机构",
              target_type="机构", source_event=None, target_event=None):
    source_tid = node(
        w, touched, i, source_title, source_type, time,
        source_event or f"转为{target_title}", quotation, "演变前",
        f"建立或复用{source_title}{time}演变节点。", field_name,
    )
    target_tid = node(
        w, touched, i, target_title, target_type, time,
        target_event or f"由{source_title}转入", quotation, "演变后",
        f"建立或复用{target_title}{time}演变节点。", field_name,
    )
    relation(
        w, i, source_tid, target_tid, "前后演变", quotation,
        decision, field_name,
    )
    return source_tid, target_tid


def group_instances(w, touched, i, group_title, type_, time, event, members,
                    quotation, decision, field_name=None):
    group_tid = node(
        w, touched, i, group_title, type_, time, event, quotation,
        f"{type_}统称", f"建立或复用{group_title}{time}统称节点。", field_name,
        update_event=True,
    )
    for member_title in members:
        member_tid = node(
            w, touched, i, member_title, type_, time,
            f"{group_title}所指实例", quotation, f"{group_title}实例",
            f"建立或复用{member_title}{time}实例节点。", field_name,
        )
        relation(
            w, i, group_tid, member_tid, "统称与实例", quotation,
            f"{member_title}是{group_title}的实例。{decision}", field_name,
        )
    return group_tid


def dual_office_post(w, touched, i, title, time, quotation, decision):
    office_tid = node(
        w, touched, i, title, "机构", time, decision, quotation,
        "修内司修造监领机构", f"建立{title}官司机构节点。", update_event=True,
    )
    post_tid = node(
        w, touched, i, title, "官职", time, decision, quotation,
        "修造差遣", f"建立{title}同名差遣节点。", officer="差遣官",
        update_event=True,
    )
    staff(
        w, i, office_tid, post_tid, quotation,
        f"原文兼称官司名、差遣名，以同名不同类型实体分别保存；{decision}",
        staff_type="监领官",
    )
    return office_tid, post_tid


def canonicalize_works_director(w, quotation):
    short = w.find_entity("将作监", "官职")
    formal = w.find_entity("将作监监", "官职")
    if short is not None:
        assert formal is None or formal == short, (short, formal)
        w.conn.execute(
            "update Entities set title='将作监监',quotation=? where id=?",
            (quotation, short),
        )
        w._br(
            "Entities", short,
            "第947条正式词头为将作监监；将既有官职实体将作监规范为正式词头，"
            "与同名机构将作监继续按类型区分。",
        )
        formal = short
    assert formal is not None
    return formal


ATTACK_WORKS = (
    "大木作", "锯匠作", "小木作", "皮作", "大炉作", "小炉作", "麻作",
    "石作", "砖作", "泥作", "井作", "赤白作", "桶作", "瓦作", "竹作",
    "猛火油作", "钉铰作", "火药作", "金火作", "青窑作", "窟子作",
)

EIGHT_WORKS = (
    "泥作", "赤白作", "桐油作", "石作", "瓦作", "竹作", "砖作", "井作",
)


def entry941():
    i, main = 941, F[941]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    first = node(
        w, touched, i, "东、西广备指挥", "机构",
        "北宋前期（东、西广备指挥先后隶属，具体年月未载）",
        "杂役厢军四指挥，先后隶提举在京诸司库务司、将作监",
        main, "杂役厢军指挥统称", "建立正式词头及其早期隶属状态。",
        update_event=True,
    )
    for parent in ("提举在京诸司库务司", "将作监"):
        parent_child(
            w, touched, i, parent, "东、西广备指挥",
            "北宋前期（东、西广备指挥先后隶属，具体年月未载）",
            main, f"原文称东、西广备指挥先后隶于{parent}；不虚构改隶年月。",
            parent_event="先后统辖东、西广备指挥",
            child_event="先后隶提举在京诸司库务司、将作监",
        )
    parent_child(
        w, touched, i, "军器监", "东、西广备指挥", "北宋熙宁六年八月",
        main, "熙宁六年八月东、西广备指挥专隶军器监。",
        parent_event="专辖东、西广备指挥",
        child_event="专隶军器监，四指挥制造攻城武器",
    )
    parent_child(
        w, touched, i, "广备攻城作", "东、西广备指挥",
        "北宋（原供役广备攻城作，具体年月未载）", main,
        "东、西广备四指挥原供役于广备攻城作。",
        parent_event="由东、西广备四指挥供役",
        child_event="原供役广备攻城作",
    )
    parent_child(
        w, touched, i, "东、西八作司", "东、西广备指挥",
        "北宋（后入东、西八作司，具体年月未载）", main,
        "东、西广备四指挥后入东、西八作司供役。",
        parent_event="接收东、西广备四指挥供役",
        child_event="后入东、西八作司，专事攻城武器二十一作制造",
    )
    alias_note(w, i, first, aliases, "简称")
    finish(w, touched, "整理东、西广备指挥正式词头、四指挥性质、三阶段隶属及供役演变。")


def entry942():
    i, quote = 942, F[942]["text"]
    assert len(ATTACK_WORKS) == 21
    w, touched = W(i), set()
    main = node(
        w, touched, i, "广备攻城作", "机构",
        "宋代（广备攻城作，具体年月未载）",
        "八作司之外的攻城武器制造职局，分二十一作",
        quote, "攻城武器制造机构", "建立广备攻城作及其职掌节点。",
        update_event=True,
    )
    group = group_instances(
        w, touched, i, "广备攻城作二十一作", "机构",
        "宋代（广备攻城作二十一作，具体年月未载）",
        "广备攻城作所属二十一作统称", ATTACK_WORKS, quote,
        "原文逐一列明二十一个作的正式名称。",
    )
    relation(
        w, i, main, group, "上下级机构", quote,
        "广备攻城作下分二十一作。",
    )
    parent_child(
        w, touched, i, "广备攻城作", "东、西广备指挥",
        "北宋（原供役广备攻城作，具体年月未载）", quote,
        "东、西广备四指挥承担广备攻城作制造。",
        parent_event="由东、西广备四指挥承担制造",
        child_event="承担广备攻城作制造",
    )
    evolution(
        w, touched, i, "广备攻城作", "东、西八作司",
        "北宋（后入东、西八作司，具体年月未载）", quote,
        "广备攻城作后并入东、西八作司；原文未载具体年月。",
        source_event="后并入东、西八作司",
        target_event="接收广备攻城作",
    )
    finish(w, touched, "整理广备攻城作、二十一作实例、广备指挥承担制造及后并八作司。")


def entry943():
    i, quote = 943, F[943]["text"]
    w, touched = W(i), set()
    start = node(
        w, touched, i, "弓弩院", "机构", "北宋开宝九年",
        "始置，隶三司，制造弩、弓、箭等兵器",
        quote, "兵器制造工署", "记录弓弩院开宝九年始置。", update_event=True,
    )
    parent_child(
        w, touched, i, "三司", "弓弩院", "北宋开宝九年", quote,
        "弓弩院始置时隶三司。", parent_event="统辖弓弩院",
        child_event="始置并隶三司",
    )
    parent_child(
        w, touched, i, "军器监", "弓弩院",
        "北宋熙宁以后（具体年月未载）", quote,
        "熙宁以后弓弩院改隶军器监；原文未给出具体年月。",
        parent_event="熙宁以后统辖弓弩院",
        child_event="熙宁以后改隶军器监",
    )
    later = node(
        w, touched, i, "弓弩院", "机构", "南宋（未载具体年月）",
        "沿置，制造弩弓箭，旬课储入内弓箭库等兵器库",
        quote, "兵器制造工署", "记录南宋沿置及旬课制度。", update_event=True,
    )
    cite(w, "Timepoints", start, i, quote, "补证北宋制造年额与旬课制度。")
    cite(w, "Timepoints", later, i, quote, "补证南宋沿置。")
    finish(w, touched, "整理弓弩院开宝始置、三司至军器监改隶、制造旬课及南宋沿置。")


def entry944():
    i, main = 944, F[944]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "将作监", "机构", "秦汉", "前身称将作少府",
         origin, "前代营造机构源流", "记录秦汉将作少府源流。", "职源与沿革",
         update_event=True)
    node(w, touched, i, "将作监", "机构", "西汉景帝中六年",
         "将作少府改名将作大匠", origin, "前代营造机构源流",
         "记录汉景帝改名。", "职源与沿革", update_event=True)
    node(w, touched, i, "将作监", "机构", "隋开皇二十年",
         "始称将作监", origin, "前代营造机构源流",
         "记录将作监正式名称始于隋。", "职源与沿革", update_event=True)
    node(w, touched, i, "将作监", "机构", "北宋初",
         "沿置但实不举职，工匠之政归三司修造案",
         origin, "具名而不举职机构", "记录北宋初不举职。", "职源与沿革",
         update_event=True)
    node(
        w, touched, i, "三司修造案", "机构", "北宋初",
        "掌工匠修造之政；同期将作监仅掌祭祀杂事",
        duty, "三司修造职能机构",
        "分别保存宋前期修造职能归三司修造案的事实，不据此虚构其与将作监的上下级关系。",
        "职掌", update_event=True,
    )
    node(w, touched, i, "将作监", "机构", "北宋熙宁四年十一月一日",
         "始正名，专领在京修造事", duty, "中央营造机构",
         "记录熙宁四年十一月一日始正名。", "职掌", update_event=True)
    evolution(
        w, touched, i, "嘉庆院", "将作监", "北宋熙宁四年十一月二日",
        origin, "熙宁四年十一月二日以嘉庆院为将作监。", "职源与沿革",
        source_event="改置为将作监", target_event="以嘉庆院改置，始振职",
    )
    reform = node(
        w, touched, i, "将作监", "机构", "北宋元丰新制",
        "元丰新制罢三司，统掌土木工匠及营造政令",
        duty, "中央营造机构", "整理元丰新制职掌。", "职掌", update_event=True,
    )
    for post, quota, kind in (
        ("将作监监", 1, "长官"), ("将作监少监", 1, "贰官"),
        ("将作监丞", 2, "属官"), ("将作监主簿", 2, "属官"),
    ):
        office_staff(
            w, touched, i, "将作监", post, "北宋元丰新制", roster,
            f"元丰新制将作监置{post}{quota}人。", "编制",
            quota=quota, staff_type=kind,
            office_event="元丰新制置监、少监、丞、主簿",
            post_event=f"将作监{kind}，编制{quota}人",
        )
    subordinates = (
        "修内司", "东、西八作司", "竹木务", "事材场", "麦娟场", "窑务",
        "丹粉所", "作坊物料库第三界", "退材场", "帘箔场",
    )
    assert len(subordinates) == 10
    for child in subordinates:
        parent_child(
            w, touched, i, "将作监", child, "北宋元丰新制", roster,
            f"元丰新制将作监所隶官属包括{child}。", "编制",
            parent_event="元丰新制统辖十个官属",
            child_event="列为将作监所隶官属",
        )
    node(w, touched, i, "将作监", "机构", "南宋建炎三年四月十三日",
         "罢置", origin, "废罢机构", "记录建炎三年罢置。", "职源与沿革",
         update_event=True)
    restore = node(
        w, touched, i, "将作监", "机构", "南宋绍兴三年十月二十九日",
        "复置", origin, "复置机构", "记录绍兴三年十月复置。", "职源与沿革",
        update_event=True,
    )
    late = node(
        w, touched, i, "将作监", "机构", "南宋中后期（具体年月未载）",
        "营造事由临安府与京畿转运司分管，本监职事较少并储备人才",
        duty, "中央营造机构", "记录南宋中后期职掌收缩，不据此虚构上下级关系。",
        "职掌", update_event=True,
    )
    cite(w, "Timepoints", reform, i, roster, "补证元丰官属、分案及吏额。", "编制")
    cite(w, "Timepoints", restore, i, roster, "补证绍兴复置后的分次恢复官属。", "编制")
    cite(w, "Timepoints", late, i, duty, "南宋中后期营造分归临安府、京畿转运司。", "职掌")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "补全将作监秦汉隋源流、北宋不举职至熙宁元丰、建炎罢绍兴复及官属链。")


def entry945():
    i, quote = 945, F[945]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "将作监", "判将作监事", "北宋前期", quote,
        "宋前期置判将作监事一人领寺事。", quota=1, staff_type="判监官",
        office_event="不举职时置判监事一人",
        post_event="以朝官以上充，领将作监少量职事", officer="朝官以上充",
    )
    office_staff(
        w, touched, i, "将作监", "判将作监事",
        "北宋熙宁四年十一月一日", quote,
        "熙宁四年设判监二人，其中资浅者带同字；本正式词头保存主判一员。",
        quota=1, staff_type="主判官", office_event="始振职，设判监与同判监",
        post_event="主判在京修造事", officer="朝官以上充",
    )
    finish(w, touched, "整理判将作监事宋前期一员及熙宁振职后主判编制。")


def entry946():
    i, main = 946, F[946]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "将作监", "同判将作监事",
        "北宋熙宁四年十一月一日", main,
        "熙宁四年置同判将作监事一员。", quota=1,
        staff_type="同判官", office_event="始振职，设判监与同判监",
        post_event="资浅者带同字，佐主判领在京修造事",
    )
    evolution(
        w, touched, i, "同判将作监事", "将作监少监", "北宋元丰五年",
        main, "元丰五年同判将作监事改为将作监少监。",
        source_type="官职", target_type="官职",
        source_event="改为将作监少监",
        target_event="由同判将作监事正名",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理同判将作监事熙宁始置、佐领职掌及元丰改少监。")


def entry947():
    i, main = 947, F[947]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    eid = canonicalize_works_director(w, main)
    touched.add(eid)
    node(w, touched, i, "将作监监", "官职", "隋大业五年",
         "将作监大匠改为大监", origin, "前代官制源流",
         "记录隋代大监源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "将作监监", "官职", "唐开元十五年",
         "始称将作监监", origin, "前代官制源流",
         "记录唐代正式官名。", "职源与沿革", update_event=True)
    early = node(
        w, touched, i, "将作监监", "官职", "北宋初",
        "无职事，为文臣迁转阶官", duty, "寄禄阶官",
        "记录宋前期阶官性质。", "职掌", officer="文臣迁转官阶",
        grade="从三品", update_event=True,
    )
    _, reform, _ = office_staff(
        w, touched, i, "将作监", "将作监监", "北宋元丰新制", duty,
        "元丰新制将作监监正名为本监长官，一人。", "职掌", quota=1,
        staff_type="长官", office_event="元丰新制设置长贰",
        post_event="正名为本监长官，总领监事", grade="从四品",
    )
    node(w, touched, i, "将作监监", "官职", "南宋建炎三年四月十三日",
         "随将作监罢置", origin, "废罢官职", "记录建炎罢置。", "职源与沿革",
         update_event=True)
    office_staff(
        w, touched, i, "将作监", "将作监监",
        "南宋绍兴十一年四月二十二日", origin,
        "绍兴十一年复置将作监监一人。", "职源与沿革", quota=1,
        staff_type="长官", office_event="复置长贰",
        post_event="复置为将作监长官，编制一人",
    )
    cite(w, "Timepoints", early, i, rank, "补证宋初沿唐从三品。", "品位")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从四品及班位。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补证元丰一人及南宋屡阙。", "编制")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "规范将作监监正式词头并整理前代源流、阶官至职事官、品位和南宋罢复。")


def entry948():
    i, main = 948, F[948]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "将作监少监", "官职", "隋大业五年", "始置少监",
         origin, "前代官制源流", "记录隋代始置。", "职源与沿革", update_event=True)
    early = node(
        w, touched, i, "将作监少监", "官职", "北宋初",
        "无职事，为文臣迁转阶官", duty, "寄禄阶官",
        "记录宋前期阶官性质。", "职掌", officer="文臣迁转官阶",
        grade="从四品下", update_event=True,
    )
    _, reform, _ = office_staff(
        w, touched, i, "将作监", "将作监少监", "北宋元丰新制", duty,
        "元丰新制将作监少监正名为副贰，一人。", "职掌", quota=1,
        staff_type="贰官", office_event="元丰新制设置长贰",
        post_event="正名为本监副贰，佐监领事", grade="从六品",
    )
    node(w, touched, i, "将作监少监", "官职", "南宋建炎三年四月十三日",
         "随将作监罢置", origin, "废罢官职", "记录建炎罢置。", "职源与沿革",
         update_event=True)
    office_staff(
        w, touched, i, "将作监", "将作监少监",
        "南宋绍兴十一年四月二十二日", roster,
        "绍兴十一年复置将作监少监一人。", "编制", quota=1,
        staff_type="贰官", office_event="复置长贰",
        post_event="复置为副贰，编制一人",
    )
    cite(w, "Timepoints", early, i, rank, "补证宋初从四品下。", "品位")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从六品及班位。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补证元丰一人及南宋屡阙。", "编制")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理将作监少监前代源流、阶官至职事官、品位编制与南宋罢复。")


def entry949():
    i, main = 949, F[949]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    node(w, touched, i, "将作监丞", "官职", "西汉", "将作少府已有丞",
         origin, "前代官制源流", "记录西汉源流。", "职源与沿革", update_event=True)
    node(w, touched, i, "将作监丞", "官职", "隋大业三年", "始置将作监丞",
         origin, "前代官制源流", "记录隋代始置。", "职源与沿革", update_event=True)
    early = node(
        w, touched, i, "将作监丞", "官职", "北宋初",
        "文臣寄禄阶官，状元初授此阶", duty, "寄禄阶官",
        "记录宋前期寄禄阶性质。", "职掌", grade="从六品下",
        update_event=True,
    )
    office_staff(
        w, touched, i, "将作监", "知将作监丞事", "北宋熙宁四年十一月一日",
        duty, "熙宁四年设知将作监丞事参领在京修造。", "职掌",
        quota=2, staff_type="知丞事", office_event="始专领在京修造事",
        post_event="参领在京修造事，编制两员",
    )
    evolution(
        w, touched, i, "将作监丞", "宣义郎", "北宋元丰寄禄格", duty,
        "元丰寄禄格将原寄禄阶将作监丞易为宣义郎。", "职掌",
        source_type="官职", target_type="官职",
        source_event="寄禄阶名易为宣义郎；本词头另正名为职事官",
        target_event="承接将作监丞原寄禄阶",
    )
    _, reform, _ = office_staff(
        w, touched, i, "将作监", "将作监丞", "北宋元丰五年", duty,
        "元丰五年将作监丞止为职事官，参领监事。", "职掌",
        quota=1, staff_type="属官", office_event="元丰新制设置丞",
        post_event="正名为职事官，参领监事", grade="从八品",
    )
    node(w, touched, i, "将作监丞", "官职", "南宋建炎三年四月十三日",
         "随将作监罢置", origin, "废罢官职", "记录建炎罢置。", "职源与沿革",
         update_event=True)
    office_staff(
        w, touched, i, "将作监", "将作监丞", "南宋绍兴三年十月八日",
        origin, "绍兴三年十月复置将作监丞一员。", "职源与沿革",
        quota=1, staff_type="属官", office_event="复置丞",
        post_event="复置，编制一员",
    )
    cite(w, "Timepoints", early, i, rank, "补证宋初品位。", "品位")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从八品及班位。", "品位")
    cite(w, "Timepoints", reform, i, roster, "补证元丰一人、绍兴复置一员。", "编制")
    alias_note(w, i, reform, aliases, "简称")
    finish(w, touched, "整理将作监丞源流、寄禄阶易宣义郎、熙宁知丞事、元丰职事官及南宋罢复。")


def entry950():
    i, main = 950, F[950]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    rank = field(i, "品位")
    aliases = field(i, "简称与别名")
    w, touched = W(i), set()
    node(w, touched, i, "将作监主簿", "官职", "西晋",
         "将作大匠下置主簿", origin, "前代官制源流",
         "记录西晋源流及《晋书》引文标点修复。", "职源与沿革", update_event=True)
    node(w, touched, i, "将作监主簿", "官职", "隋大业三年",
         "始置将作监主簿", origin, "前代官制源流",
         "记录隋代始置。", "职源与沿革", update_event=True)
    early = node(
        w, touched, i, "将作监主簿", "官职", "北宋初",
        "无职事，为文臣寄禄阶官", duty, "寄禄阶官",
        "记录宋初寄禄阶性质。", "职掌", grade="从七品下",
        update_event=True,
    )
    office_staff(
        w, touched, i, "将作监", "知将作监主簿公事", "北宋熙宁四年十月",
        duty, "熙宁四年十月设知将作监主簿公事，掌簿书。", "职掌",
        staff_type="知主簿事", office_event="复将作监职事",
        post_event="掌本监簿书",
    )
    evolution(
        w, touched, i, "将作监主簿", "承务郎", "北宋元丰寄禄格", duty,
        "元丰寄禄格将原寄禄阶将作监主簿易为承务郎。", "职掌",
        source_type="官职", target_type="官职",
        source_event="寄禄阶名易为承务郎；本词头另正名为职事官",
        target_event="承接将作监主簿原寄禄阶",
    )
    _, reform, _ = office_staff(
        w, touched, i, "将作监", "将作监主簿", "北宋元丰五年", duty,
        "元丰五年将作监主簿正名为职事官，罢寄禄职能。", "职掌",
        staff_type="属官", office_event="元丰新制设置主簿",
        post_event="正名为职事官，掌簿书", grade="从八品",
    )
    node(w, touched, i, "将作监主簿", "官职", "南宋建炎三年四月十三日",
         "随将作监罢置", origin, "废罢官职", "记录建炎罢置。", "职源与沿革",
         update_event=True)
    office_staff(
        w, touched, i, "将作监", "将作监主簿", "南宋绍兴十年", origin,
        "绍兴十年复置将作监主簿。", "职源与沿革", quota=1,
        staff_type="属官", office_event="复置主簿", post_event="复置",
    )
    cite(w, "Timepoints", early, i, rank, "补证宋初从七品下。", "品位")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从八品。", "品位")
    alias_note(w, i, reform, aliases, "简称与别名")
    finish(w, touched, "整理将作监主簿源流、寄禄阶易承务郎、熙宁知簿事、元丰职事官及南宋罢复。")


def entry951():
    i, main = 951, F[951]["text"]
    origin = field(i, "职源")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    start = node(
        w, touched, i, "修内司", "机构", "北宋大中祥符五年七月",
        "始见修内司之名，掌皇城宫殿垣宇及太庙修缮",
        origin, "宫城修缮机构", "记录修内司始见时间。", "职源",
        update_event=True,
    )
    parent_child(
        w, touched, i, "提举在京诸司库务司", "修内司", "北宋前期", main,
        "北宋前期修内司隶提举在京诸司库务司。",
        parent_event="统辖修内司", child_event="隶提举在京诸司库务司",
    )
    parent_child(
        w, touched, i, "将作监", "修内司", "北宋元丰新制", main,
        "元丰以后修内司隶将作监。", parent_event="元丰新制统辖修内司",
        child_event="元丰以后隶将作监",
    )
    south = node(
        w, touched, i, "修内司", "机构", "南宋（修内司，具体年月未载）",
        "沿置，兼制造御前军器", duty, "宫城修缮与军器制造机构",
        "记录南宋沿置及职掌扩展。", "职掌", update_event=True,
    )
    for time, post, quota, kind, officer in (
        ("北宋真宗朝（具体年月未载）", "勾当修内司公事", 3, "勾当官", "内侍差充，后或三班使臣充"),
        ("北宋真宗朝（具体年月未载）", "修内司雄武兵级", 1000, "军匠", "雄武兵级"),
        ("南宋（修内司，具体年月未载）", "干办修内司公事", 2, "干办官", None),
    ):
        office_staff(
            w, touched, i, "修内司", post, time, roster,
            f"修内司置{post}{quota}人。", "编制", quota=quota,
            staff_type=kind, office_event="设置修内司属员",
            post_event=f"修内司{kind}，编制{quota}人", officer=officer,
        )
    cite(w, "Timepoints", start, i, duty, "补证修内司宫殿、太庙修缮职掌。", "职掌")
    cite(w, "Timepoints", south, i, roster, "补证南宋干办官编制。", "编制")
    alias_note(w, i, start, aliases, "简称")
    finish(w, touched, "整理修内司始见、前期至元丰改隶、南宋沿置职掌及北南宋编制。")


def entry952():
    i, quote = 952, F[952]["text"]
    w, touched = W(i), set()
    office, _ = dual_office_post(
        w, touched, i, "提举内中修造所", "北宋（提举内中修造，具体年月未载）",
        quote, "作为提举内中修造差遣治所，监领修内司修造宫殿门户",
    )
    repair = node(
        w, touched, i, "修内司", "机构", "北宋（提举内中修造，具体年月未载）",
        "由提举内中修造所监领宫殿门户修造", quote, "被监领机构",
        "建立修内司在本条所述监领关系中的节点。",
    )
    relation(w, i, office, repair, "上下级机构", quote,
             "提举内中修造所监领修内司修造宫殿门户事。")
    finish(w, touched, "区分提举内中修造所的同名官司与差遣，并保存其监领修内司关系。")


def entry953():
    i, quote = 953, F[953]["text"]
    w, touched = W(i), set()
    office = node(
        w, touched, i, "提举在内修造所", "机构",
        "北宋（提举在内修造，具体年月未载）",
        "提举在内中修造差遣治所，监领修内司修造宫殿门户",
        quote, "修内司修造监领机构", "原文仅称官司名，建立机构实体。",
        update_event=True,
    )
    repair = node(
        w, touched, i, "修内司", "机构",
        "北宋（提举在内修造，具体年月未载）",
        "由提举在内修造所监领宫殿门户修造", quote, "被监领机构",
        "建立修内司在本条所述监领关系中的节点。",
    )
    relation(w, i, office, repair, "上下级机构", quote,
             "提举在内修造所监领修内司修造宫殿门户事。")
    finish(w, touched, "整理提举在内修造所官司性质及监领修内司关系。")


def entry954():
    i, quote = 954, F[954]["text"]
    w, touched = W(i), set()
    office, _ = dual_office_post(
        w, touched, i, "提举在内修造所公事",
        "北宋（提举在内修造，具体年月未载）", quote,
        "监领修内司修造宫殿门外、皇城司内建筑物",
    )
    repair = node(
        w, touched, i, "修内司", "机构",
        "北宋（提举在内修造，具体年月未载）",
        "受提举在内修造所公事监领有关修造", quote, "被监领机构",
        "复用修内司本期节点。",
    )
    relation(w, i, office, repair, "上下级机构", quote,
             "提举在内修造所公事监领修内司有关修造事。")
    finish(w, touched, "区分提举在内修造所公事的同名官司与差遣，并保存监领范围。")


def entry955():
    i, quote = 955, F[955]["text"]
    w, touched = W(i), set()
    office, post = dual_office_post(
        w, touched, i, "提举修内司", "南宋（提举修内司，具体年月未载）",
        quote, "在临安孝仁坊内青平山口，提举官监领修内司公事",
    )
    repair = node(
        w, touched, i, "修内司", "机构", "南宋（提举修内司，具体年月未载）",
        "由提举修内司监领", quote, "被监领机构", "建立南宋监领节点。",
    )
    relation(w, i, office, repair, "上下级机构", quote,
             "提举修内司官司监领修内司公事。")
    cite(w, "Timepoints", post, i, quote, "提举修内司差遣由内侍充。")
    finish(w, touched, "区分提举修内司官司与差遣，并整理南宋地点、差充和监领关系。")


def entry956():
    i, main = 956, F[956]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "修内司", "提辖修内司",
        "南宋（提辖修内司，具体年月未载）", main,
        "南宋修内司在干办官之上设提辖官，位次提举官之下。",
        quota=None, staff_type="监临官", office_event="增置提辖监临官",
        post_event="位次提举官之下、干办官之上，由内侍充", officer="内侍充",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理提辖修内司南宋增置原因、位次、内侍差充与简称。")


def entry957():
    i, main = 957, F[957]["text"]
    aliases = field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "修内司", "勾当修内司公事",
        "北宋真宗朝（具体年月未载）", main,
        "真宗朝勾当修内司公事三人，由两内侍省内侍充。",
        quota=3, staff_type="勾当官", office_event="设置勾当官三人",
        post_event="管领修内司公事，位次提举、提辖官之下",
        officer="内侍省、入内内侍省内侍充",
    )
    node(
        w, touched, i, "勾当修内司公事", "官职",
        "北宋熙宁间（具体年月未载）", "或差三班使臣充",
        main, "修内司勾当差遣", "记录熙宁间差充范围变化。",
        officer="三班使臣（武臣）或内侍充", update_event=True,
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理勾当修内司公事真宗朝三人编制、差充、职掌位次及熙宁变化。")


def entry958():
    i, quote = 958, F[958]["text"]
    w, touched = W(i), set()
    evolution(
        w, touched, i, "勾当修内司公事", "干办修内司公事",
        "南宋（干办修内司公事，具体年月未载）", quote,
        "南宋改勾当为干办，干办修内司公事即原勾当修内司公事。",
        source_type="官职", target_type="官职",
        source_event="南宋改称干办修内司公事",
        target_event="由勾当修内司公事改称",
    )
    office_staff(
        w, touched, i, "修内司", "干办修内司公事",
        "南宋（干办修内司公事，具体年月未载）", quote,
        "南宋修内司以干办官管领公事。", staff_type="干办官",
        office_event="勾当官改称干办官",
        post_event="由勾当修内司公事改称",
    )
    finish(w, touched, "整理南宋勾当改干办的明确前后演变及修内司编制隶属。")


def entry959():
    i, quote = 959, F[959]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "皇城司", "识字黄院子",
        "宋代（原属皇城司，具体年月未载）", quote,
        "识字黄院子原属皇城司。", staff_type="公吏",
        office_event="设识字黄院子", post_event="原属皇城司", officer="公吏",
    )
    office_staff(
        w, touched, i, "修内司", "识字黄院子", "南宋淳熙间", quote,
        "淳熙间拨识字黄院子八人入修内司。", quota=8, staff_type="公吏",
        office_event="接收识字黄院子八人",
        post_event="拨入修内司八人，巡视修葺并防工匠作过", officer="公吏",
    )
    finish(w, touched, "整理识字黄院子由皇城司拨入修内司的两期编制隶属、八人员额与职掌。")


def entry960():
    i, main = 960, F[960]["text"]
    origin = field(i, "职源与沿革")
    duty = field(i, "职掌")
    roster = field(i, "编制")
    aliases = field(i, "简称")
    w, touched = W(i), set()
    known_times = (
        ("宋初", "称八作司，置东八作使、西八作使"),
        ("北宋太平兴国二年", "分东、西八作司"),
        ("北宋景德四年六月", "并为东西八作司，含街道司"),
        ("北宋天圣元年五月十六日", "复分东八作司、西八作司"),
        ("南宋（东、西八作司，具体年月未载）", "南宋称八作司，在临安内辖司东库内"),
    )
    nodes = []
    for time, event in known_times:
        nodes.append(node(
            w, touched, i, "东、西八作司", "机构", time, event,
            origin if time != "南宋（东、西八作司，具体年月未载）" else main,
            "京师缮修机构", "复用或补充东、西八作司既有沿革节点。",
            "职源与沿革" if time != "南宋（东、西八作司，具体年月未载）" else None,
            update_event=True,
        ))
    for parent, time in (
        ("三司", "宋初"),
        ("提举在京诸司库务司", "北宋（隶提举在京诸司库务司，具体年月未载）"),
        ("将作监", "北宋熙宁四年十一月一日"),
    ):
        parent_child(
            w, touched, i, parent, "东、西八作司", time, main,
            f"东、西八作司先后隶{parent}；沿用已有证据限定节点。",
            parent_event=f"统辖东、西八作司",
            child_event=f"隶{parent}",
        )
    duty_tp = node(
        w, touched, i, "东、西八作司", "机构",
        "宋代（东、西八作司八作，具体年月未载）",
        "掌京师内外缮修，各司分八作", duty, "京师缮修机构",
        "整理东、西八作司职掌及八作编制。", "职掌", update_event=True,
    )
    group = group_instances(
        w, touched, i, "东、西八作司八作", "机构",
        "宋代（东、西八作司八作，具体年月未载）",
        "东、西八作司各司所分八作统称", EIGHT_WORKS, roster,
        "原文逐一列明每司八作的正式名称。", "编制",
    )
    relation(w, i, duty_tp, group, "上下级机构", roster,
             "东、西八作司各司分八作。", "编制")
    for office in ("东八作司", "西八作司"):
        office_staff(
            w, touched, i, office, "东、西八作司勾当官",
            "宋代（东、西八作司勾当官，具体年月未载）", roster,
            f"{office}置勾当官三人。", "编制", quota=3,
            staff_type="勾当官", office_event="置勾当官三人",
            post_event="东、西二司勾当官，各司三人",
            officer="诸司使副及内侍充",
        )
    parent_child(
        w, touched, i, "东、西八作司", "东、西广备指挥",
        "北宋（后入东、西八作司，具体年月未载）", roster,
        "东、西八作司所属包括杂役、工匠广备指挥。", "编制",
        parent_event="下有广备指挥供役",
        child_event="入东、西八作司供役",
    )
    for tid in nodes:
        cite(w, "Timepoints", tid, i, main, "补证东、西八作司地点及先后隶属。")
    cite(w, "Timepoints", duty_tp, i, roster, "补证勾当官与广备指挥编制。", "编制")
    alias_note(w, i, duty_tp, aliases, "简称")
    finish(w, touched, "复核东、西八作司既有分合链并补职掌、八作实例、勾当官和广备指挥编制。")


def main():
    order = [947, 944, 941, 942, 943, 945, 946, *range(948, 961)]
    for i in order:
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
