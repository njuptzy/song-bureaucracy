#!/usr/bin/env python3
"""提取 chapter2t4 第221–240条：银台司吏职、皮剥所及枢密院杂局。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get("SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db"))


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute("SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (i,)).fetchone()
    fields = json.loads(row[3] or "{}")
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "all": "\n".join([row[2] or ""] + [str(v) for k, v in fields.items() if not k.startswith("_")]),
    }


F = {i: load(i) for i in range(221, 241)}


def q(i, text):
    assert text in F[i]["all"], f"#{i} 不含：{text}"
    return text


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def C(i):
    return f"《宋代官制辞典》第{F[i]['page']}页“{F[i]['title']}”条"


def cite(w, table, rid, i, quotation, decision, **kwargs):
    return w.citation(table, rid, C(i), quotation, decision, **kwargs)


def entity(w, title, type_, i, quotation, decision):
    return w.entity(title, type_, decision, quotation=quotation)


def tp(w, eid, time, event, i, quotation, category, decision, **kwargs):
    tid = w.timepoint(eid, time, event, decision, quotation, attr_category=category, **kwargs)
    cite(w, "Timepoints", tid, i, quotation, decision)
    return tid


def rel(w, source, target, kind, i, quotation, decision, **kwargs):
    rid = w.relationship(source, target, kind, decision, quotation, **kwargs)
    cite(w, "Relationships", rid, i, quotation, decision)
    return rid


def node(w, title, time, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, f"缺实体：{title}"
    tid = w.find_timepoint(eid, time)
    assert tid, f"{title} 缺时间点：{time}"
    return eid, tid


def first_node(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, f"缺实体：{title}"
    row = w.conn.execute("SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (eid,)).fetchone()
    assert row, f"{title} 无时间点"
    return eid, row[0]


def chain(w, ids, decision):
    assert all(ids)
    for pos, tid in enumerate(ids):
        w.relink(tid, decision, prev_id=ids[pos - 1] if pos else None, succ_id=ids[pos + 1] if pos + 1 < len(ids) else None)


def parent(w, period):
    return node(w, "枢密院", period, "机构")[1]


def entry221():
    i = 221; z = F[i]["text"]; w = W(i)
    eid = entity(w, "银台司主事", "官职", i, z, "辞典明载为银台司公吏名。")
    before = tp(w, eid, "北宋康定元年十二月前", "由枢密院主事差充二人，掌本司发放文字", i, z, "公吏", "建改制前银台司主事节点。", chain="none")
    end = tp(w, eid, "北宋康定元年十二月", "罢，改用令史", i, z, "公吏", "建康定罢置节点。", chain="none")
    chain(w, [before, end], "按康定改制前与罢置排序。")
    silver = node(w, "银台司", "北宋淳化四年八月十八日", "机构")[1]
    rel(w, silver, before, "编制隶属", i, z, "银台司差主事二人掌发放文字。", staff_quota=2, staff_type="吏")
    w.commit()


def entry222():
    i = 222; z = F[i]["text"]; w = W(i)
    eid = entity(w, "银台司令史", "官职", i, z, "辞典明载为银台司公吏名。")
    start = tp(w, eid, "北宋康定元年十二月", "取代主事，由枢密院书令史兼任", i, z, "公吏", "建康定改制始置节点。")
    source = node(w, "银台司主事", "北宋康定元年十二月", "官职")[1]
    rel(w, source, start, "前后演变", i, z, "银台司罢主事改用令史。")
    silver = node(w, "银台司", "北宋淳化四年八月十八日", "机构")[1]
    rel(w, silver, start, "编制隶属", i, z, "银台司令史由枢密院书令史兼任。", staff_type="吏")
    w.commit()


def entry223():
    i = 223; z = F[i]["text"]; w = W(i)
    eid = entity(w, "银台司书令史", "官职", i, z, "辞典明载为银台司书吏。")
    start = tp(w, eid, "北宋康定元年十二月后", "由枢密院贴房差充，承行发放、抄写文字", i, z, "公吏", "建康定后银台司书令史节点。")
    silver = node(w, "银台司", "北宋淳化四年八月十八日", "机构")[1]
    rel(w, silver, start, "编制隶属", i, z, "银台司书令史由枢密院贴房差充。", staff_type="吏")
    w.commit()


def entry224():
    i = 224; z = F[i]["all"]; q_move = q(i, "初隶中书，淳化四年八月归隶银台司"); q_staff = q(i, "发敕官三人，吏人充"); w = W(i)
    office = entity(w, "发敕司", "机构", i, F[i]["text"], "辞典明载为京局。")
    initial = tp(w, office, "宋初", "初隶中书，掌受宣敕登记颁下", i, q_move, "京局名", "建初隶中书节点。", chain="none")
    moved = tp(w, office, "北宋淳化四年八月", "归隶银台司", i, q_move, "京局名", "建淳化移隶节点。", chain="none")
    chain(w, [initial, moved], "按初隶中书与淳化归银台排序。")
    middle = entity(w, "中书", "机构", i, q_move, "原文明载发敕司初隶中书。")
    middle_tp = tp(w, middle, "宋初", "发敕司初隶于此", i, q_move, "官署名", "建中书承载节点。")
    silver = node(w, "银台司", "北宋淳化四年八月十八日", "机构")[1]
    rel(w, middle_tp, initial, "上下级机构", i, q_move, "发敕司初隶中书。")
    rel(w, silver, moved, "上下级机构", i, q_move, "淳化四年发敕司归隶银台司。")
    post_e = entity(w, "发敕官", "官职", i, q_staff, "编制明确列发敕官。")
    post = tp(w, post_e, "未知", "吏人充任，三人", i, q_staff, "公吏", "原文无设置时间，建真实无年节点。")
    rel(w, moved, post, "编制隶属", i, q_staff, "发敕司置发敕官三人。", staff_quota=3, staff_type="吏")
    w.commit()


def entry225():
    i = 225; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("枢密院印司", "机构"); assert eid
    stage = w.find_timepoint(eid, "北宋末、南宋初"); assert stage
    cite(w, "Timepoints", stage, i, z, "专条补证印司为二十五房之一并掌诸房用印。")
    end = tp(w, eid, "南宋乾道六年二月", "并入工房", i, z, "办事机构", "建乾道并入工房节点。", chain="none")
    chain(w, [stage, end], "按二十五房时期与乾道并房排序。")
    target = node(w, "枢密院工房", "南宋乾道六年二月", "机构")[1]
    rel(w, end, target, "前后演变", i, z, "印司于乾道六年并入工房。")
    rel(w, parent(w, "南宋绍兴七年"), stage, "上下级机构", i, z, "印司隶枢密院。")
    w.commit()


def entry226():
    i = 226; z = F[i]["text"]; w = W(i)
    office = entity(w, "宣旨院", "机构", i, z, "正文首字疑 OCR 为‘衡署名’，其后明确隶枢密院并具官署职掌，按官署建模。")
    office_tp = tp(w, office, "未知", "枢密院诸房吏人集中办事厅，防止泄密", i, z, "官署名", "原文无始置时间，建真实无年节点。")
    rel(w, parent(w, "南宋绍兴七年"), office_tp, "上下级机构", i, z, "宣旨院隶枢密院。")
    for title, quota in (("法司", 3), ("贴司", 2), ("贴房", 26)):
        post_e = entity(w, title, "官职", i, z, f"宣旨院吏额明确列{title}。")
        row = w.conn.execute("SELECT id FROM Timepoints WHERE entity_id=? ORDER BY id LIMIT 1", (post_e,)).fetchone()
        post = row[0] if row else tp(w, post_e, "未知", f"宣旨院吏职{title}", i, z, "公吏", "原文无时间，建吏职节点。")
        if row: cite(w, "Timepoints", post, i, z, f"补充宣旨院{title}编制。", note="编制")
        rel(w, office_tp, post, "编制隶属", i, z, f"宣旨院置{title}{quota}人。", staff_quota=quota, staff_type="吏")
    guard_e = entity(w, "守阙贴房", "官职", i, z, "宣旨院吏额明确列守阙贴房。")
    guard_before = tp(w, guard_e, "南宋绍兴二十六年前", "二百四十人", i, z, "公吏", "建减额前节点。", chain="none")
    guard_after = tp(w, guard_e, "南宋绍兴二十六年", "减为二百人", i, z, "公吏", "建绍兴减额节点。", chain="none")
    chain(w, [guard_before, guard_after], "按绍兴二十六年前后员额排序。")
    rel(w, office_tp, guard_before, "编制隶属", i, z, "宣旨院原置守阙贴房二百四十人。", staff_quota=240, staff_type="吏")
    rel(w, office_tp, guard_after, "编制隶属", i, z, "绍兴二十六年减守阙贴房为二百人。", staff_quota=200, staff_type="吏")
    w.commit()


def entry227():
    i = 227
    q_head = q(i, "监当局名。先后隶太仆寺、驾部、枢密院。")
    q_969 = q(i, "北宋开宝二年(969)始置，初分内、外剥马务")
    q_1072 = q(i, "熙宁五年四月两务合为一局，以“皮剥所”为名")
    q_south = q(i, "南宋初省罢")
    q_1138 = q(i, "绍兴八年九月三十日复置，以“行在皮剥所”为名")
    q_1169 = q(i, "乾道五年七月二十八日，以“枢密院皮剥所”为名")
    q_staff = q(i, "先后设监官、提举官。人吏有：剥手十五人，专知官一人，手分一人，军典一人，库子二人，节级二人，巡防兵士十六人")
    w = W(i)
    inner = entity(w, "内剥马务", "机构", i, q_969, "原文明载开宝二年内剥马务。")
    outer = entity(w, "外剥马务", "机构", i, q_969, "原文明载开宝二年外剥马务。")
    inner_start = tp(w, inner, "北宋开宝二年", "始置", i, q_969, "监当局", "建内剥马务始置节点。", chain="none")
    outer_start = tp(w, outer, "北宋开宝二年", "始置", i, q_969, "监当局", "建外剥马务始置节点。", chain="none")
    inner_end = tp(w, inner, "北宋熙宁五年四月", "与外剥马务合为皮剥所", i, q_1072, "监当局", "建合并终结节点。", chain="none")
    outer_end = tp(w, outer, "北宋熙宁五年四月", "与内剥马务合为皮剥所", i, q_1072, "监当局", "建合并终结节点。", chain="none")
    chain(w, [inner_start, inner_end], "按开宝始置与熙宁合并排序。")
    chain(w, [outer_start, outer_end], "按开宝始置与熙宁合并排序。")
    peel = entity(w, "皮剥所", "机构", i, q_head, "辞典明载为监当局。")
    peel_start = tp(w, peel, "北宋熙宁五年四月", "由内、外剥马务合并设置", i, q_1072, "监当局", "建皮剥所始置节点。", chain="none")
    peel_end = tp(w, peel, "南宋初", "省罢", i, q_south, "监当局", "建南宋初省罢节点。", chain="none")
    chain(w, [peel_start, peel_end], "按熙宁合并与南宋初省罢排序。")
    mobile = entity(w, "行在皮剥所", "机构", i, q_1138, "辞典明载复置时冠行在名。")
    mobile_start = tp(w, mobile, "南宋绍兴八年九月三十日", "复置", i, q_1138, "监当局", "建行在皮剥所复置节点。", chain="none")
    mobile_end = tp(w, mobile, "南宋乾道五年七月二十八日", "改为枢密院皮剥所", i, q_1169, "监当局", "建改名终结节点。", chain="none")
    chain(w, [mobile_start, mobile_end], "按绍兴复置与乾道改名排序。")
    bureau = entity(w, "枢密院皮剥所", "机构", i, q_1169, "辞典明载乾道五年所定机构名。")
    bureau_start = tp(w, bureau, "南宋乾道五年七月二十八日", "由行在皮剥所改名", i, q_1169, "监当局", "建枢密院皮剥所始置节点。")
    rel(w, inner_end, peel_start, "前后演变", i, q_1072, "内剥马务合入皮剥所。")
    rel(w, outer_end, peel_start, "前后演变", i, q_1072, "外剥马务合入皮剥所。")
    rel(w, peel_end, mobile_start, "前后演变", i, q_1138, "皮剥所省罢后于绍兴复置为行在皮剥所。")
    rel(w, mobile_end, bureau_start, "前后演变", i, q_1169, "行在皮剥所改为枢密院皮剥所。")
    for parent_title in ("太仆寺", "驾部"):
        parent_e = entity(w, parent_title, "机构", i, q_head, f"原文明载皮剥所先后隶{parent_title}。")
        parent_tp = tp(w, parent_e, "未知", f"皮剥所曾隶{parent_title}", i, q_head, "官署名", "原文无具体移隶时间，建承载节点。")
        rel(w, parent_tp, peel_start, "上下级机构", i, q_head, f"皮剥所曾隶{parent_title}。")
    rel(w, parent(w, "南宋绍兴七年"), bureau_start, "上下级机构", i, q_head, "后期皮剥所隶枢密院。")
    staff = (("皮剥所监官", None, "官"), ("皮剥所提举官", None, "官"), ("剥手", 15, "匠"), ("专知官", 1, "吏"), ("手分", 1, "吏"), ("军典", 1, "吏"), ("库子", 2, "吏"), ("节级", 2, "吏"), ("巡防兵士", 16, "兵"))
    for title, quota, staff_type in staff:
        post_e = entity(w, title, "官职", i, q_staff, f"皮剥所编制明确列{title}。")
        post = tp(w, post_e, "宋代", f"皮剥所职役{title}", i, q_staff, "职役", "原文未给单独设置时间，建宋代承载节点。")
        rel(w, peel_start, post, "编制隶属", i, q_staff, f"皮剥所编制包括{title}。", staff_quota=quota, staff_type=staff_type)
    w.commit()


def entry228():
    i = 228; z = F[i]["text"]; w = W(i)
    group_e = entity(w, "剥马务", "机构", i, F[i]["text"], "辞典明载为有内外之分的监当局总名。")
    start = tp(w, group_e, "北宋开宝二年", "始置，分内、外剥马务", i, F[i]["text"], "监当局总名", "建剥马务始置节点。", chain="none")
    end = tp(w, group_e, "北宋熙宁五年四月", "内、外务合为皮剥所", i, F[i]["text"], "监当局总名", "建合并终结节点。", chain="none")
    chain(w, [start, end], "按开宝始置与熙宁合并排序。")
    for title in ("内剥马务", "外剥马务"):
        member = node(w, title, "北宋开宝二年", "机构")[1]
        rel(w, start, member, "统称与实例", i, z, f"剥马务总名分为{title}。")
    target = node(w, "皮剥所", "北宋熙宁五年四月", "机构")[1]
    rel(w, end, target, "前后演变", i, z, "内外剥马务于熙宁五年合为皮剥所。")
    w.commit()


def entry229():
    i = 229; z = F[i]["text"]; w = W(i)
    start = node(w, "行在皮剥所", "南宋绍兴八年九月三十日", "机构")[1]
    cite(w, "Timepoints", start, i, z, "专条补证绍兴复置时冠行在名。")
    source = node(w, "皮剥所", "南宋初", "机构")[1]
    rel(w, source, start, "前后演变", i, z, "皮剥所复置时冠行在二字。")
    w.commit()


def entry230():
    i = 230; z = F[i]["text"]; w = W(i)
    source = node(w, "行在皮剥所", "南宋乾道五年七月二十八日", "机构")[1]
    target = node(w, "枢密院皮剥所", "南宋乾道五年七月二十八日", "机构")[1]
    cite(w, "Timepoints", target, i, z, "专条补证乾道五年改名。")
    rel(w, source, target, "前后演变", i, z, "行在皮剥所改为枢密院皮剥所。")
    w.commit()


def entry231():
    i = 231; z = F[i]["text"]; w = W(i)
    eid = entity(w, "监专公人", "官职", i, z, "辞典明确界定为皮剥所监官、专知官及公人的合称。")
    group = tp(w, eid, "南宋", "皮剥所监官、专知官及手分等公人的合称", i, z, "职役总称", "建南宋合称节点。")
    for title in ("皮剥所监官", "专知官", "手分", "库子", "军典", "节级"):
        member = first_node(w, title, "官职")[1]
        rel(w, group, member, "统称与实例", i, z, f"监专公人合称包括{title}。")
    w.commit()


def entry232():
    i = 232; z = F[i]["text"]; w = W(i)
    post = first_node(w, "剥手", "官职")[1]
    cite(w, "Timepoints", post, i, z, "专条补证剥手为皮剥所匠人及十五人编制。")
    office = node(w, "皮剥所", "北宋熙宁五年四月", "机构")[1]
    rel(w, office, post, "编制隶属", i, z, "皮剥所置剥手十五人。", staff_quota=15, staff_type="匠")
    w.commit()


def entry233():
    i = 233; z = F[i]["text"]; w = W(i)
    eid = w.find_entity("专知官", "官职"); assert eid
    south = tp(w, eid, "南宋", "由副尉差充，主管皮剥所官物等给使", i, F[i]["text"], "公吏", "建南宋专知官职掌节点。", chain="none")
    song = w.find_timepoint(eid, "宋代"); assert song
    chain(w, [song, south], "按宋代通制与南宋专条状态排序。")
    office = node(w, "枢密院皮剥所", "南宋乾道五年七月二十八日", "机构")[1]
    rel(w, office, south, "编制隶属", i, z, "南宋皮剥所专知官由副尉差充。", staff_quota=1, staff_type="吏")
    w.commit()


def entry234():
    i = 234; z = F[i]["text"]; w = W(i)
    post = first_node(w, "军典", "官职")[1]
    cite(w, "Timepoints", post, i, z, "专条补充军典抄转书写簿历的职掌。", note="职掌")
    office = node(w, "皮剥所", "北宋熙宁五年四月", "机构")[1]
    rel(w, office, post, "编制隶属", i, z, "军典隶皮剥所。", staff_type="吏")
    w.commit()


def entry235():
    i = 235; z = F[i]["text"]; w = W(i)
    post = first_node(w, "节级", "官职")[1]
    cite(w, "Timepoints", post, i, z, "专条补充节级来源、员额规则与巡守职掌。", note="编制随巡防兵士人数变化")
    office = node(w, "皮剥所", "北宋熙宁五年四月", "机构")[1]
    rel(w, office, post, "编制隶属", i, z, "节级隶皮剥所并部辖巡防兵士。", staff_type="吏")
    w.commit()


def entry236():
    i = 236
    q_head = q(i, "京局名。隶枢密院。")
    q_start = q(i, "北宋徽宗朝已见置")
    q_duty = q(i, "招收年龄在三十岁以下")
    q_staff = q(i, "提举官一员，干办官兼押教二员，措教官五员、弓马教头五员")
    w = W(i)
    office = entity(w, "御前弓马子弟所", "机构", i, q_head, "辞典明载为隶枢密院京局。")
    office_tp = tp(w, office, "北宋徽宗朝", "已见设置，招收官员与良家子弟教阅武艺", i, q_start, "京局名", "建徽宗朝状态节点。")
    cite(w, "Timepoints", office_tp, i, q_duty, "补充职掌。", note="职掌")
    rel(w, parent(w, "北宋元丰四年"), office_tp, "上下级机构", i, q_head, "御前弓马子弟所隶枢密院。")
    for title, quota in (("御前弓马子弟所提举官", 1), ("御前弓马子弟所干办官兼押教", 2), ("御前弓马子弟所措教官", 5), ("弓马教头", 5)):
        post_e = entity(w, title, "官职", i, q_staff, f"编制明确列{title}。")
        post = tp(w, post_e, "北宋徽宗朝", "随御前弓马子弟所设置", i, q_staff, "职事官", "建徽宗朝编制节点。")
        rel(w, office_tp, post, "编制隶属", i, q_staff, f"御前弓马子弟所置{title}{quota}员。", staff_quota=quota, staff_type="官")
    w.commit()


def entry237():
    i = 237; z = F[i]["text"]; w = W(i)
    post = node(w, "弓马教头", "北宋徽宗朝", "官职")[1]
    cite(w, "Timepoints", post, i, z, "专条补证弓马教头职掌及每百人一员。")
    office = node(w, "御前弓马子弟所", "北宋徽宗朝", "机构")[1]
    rel(w, office, post, "编制隶属", i, z, "弓马教头为弓马子弟所教官，每百人一员。", staff_type="官")
    w.commit()


def entry238():
    i = 238; z = F[i]["all"]; q_head = q(i, "京局名，隶枢密院"); q_start = q(i, "宋朝始置"); w = W(i)
    eid = entity(w, "省马院", "机构", i, q_head, "辞典明载为隶枢密院京局。")
    tid = tp(w, eid, "宋代", "始置，管理喂养及支借京师官马", i, q_start, "京局名", "建宋代始置节点。")
    cite(w, "Timepoints", tid, i, z, "补充省马院职掌与全称。", note="职掌")
    rel(w, parent(w, "宋初"), tid, "上下级机构", i, q_head, "省马院隶枢密院。")
    w.commit()


def entry239():
    i = 239; z = F[i]["text"]; w = W(i)
    group_e = entity(w, "枢密院东厨、西厨", "机构", i, z, "辞典以东厨、西厨合条记载枢密院食堂。")
    group = tp(w, group_e, "未知", "枢密院东厨、西厨总称，免费供给官吏伙食", i, z, "京局总名", "原文无时间，建总称节点。")
    for title in ("枢密院东厨", "枢密院西厨"):
        member_e = entity(w, title, "机构", i, z, f"合条明确列{title}。")
        member = tp(w, member_e, "未知", "枢密院食堂", i, z, "京局名", "原文无时间，建食堂节点。")
        rel(w, group, member, "统称与实例", i, z, f"东厨、西厨总名包括{title}。")
        rel(w, parent(w, "南宋绍兴七年"), member, "上下级机构", i, z, f"{title}为枢密院食堂。")
    w.commit()


def entry240():
    i = 240; z = F[i]["text"]; w = W(i)
    eid = entity(w, "食手", "官职", i, z, "辞典明载为东、西厨公人名。")
    tid = tp(w, eid, "未知", "供东、西厨造膳，共二十八人", i, z, "公人", "原文无时间，建真实无年节点。")
    kitchens = node(w, "枢密院东厨、西厨", "未知", "机构")[1]
    rel(w, kitchens, tid, "编制隶属", i, z, "东、西厨共有食手二十八人。", staff_quota=28, staff_type="公人")
    w.commit()


def main():
    entry221(); entry222(); entry223(); entry224(); entry225()
    entry226(); entry227(); entry228(); entry229(); entry230()
    entry231(); entry232(); entry233(); entry234(); entry235()
    entry236(); entry237(); entry238(); entry239(); entry240()


if __name__ == "__main__":
    main()
