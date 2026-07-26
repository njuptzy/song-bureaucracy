#!/usr/bin/env python3
"""提取 chapter2t4 第 74–78 条：舍人院、知制诰、直舍人院、起居院系统。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")
IDS = range(74, 79)


def load_entry(entry_id):
    conn = sqlite3.connect(DICT_DB)
    row = conn.execute(
        "SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (entry_id,)
    ).fetchone()
    conn.close()
    full = (row[2] or "") + "\n" + "\n".join(
        str(v) for k, v in json.loads(row[3] or "{}").items() if not k.startswith("_")
    )
    return row[0], row[1], full


FULL = {i: load_entry(i) for i in IDS}


def q(eid, text):
    assert text in FULL[eid][2], f"#{eid} 不含：{text}"
    return text


def cite(eid):
    title, page, _ = FULL[eid]
    return f"《宋代官制辞典》第{page}页“{title}”条"


def writer(eid):
    title, page, _ = FULL[eid]
    return EntryWriter(ENTRY_DB, title, page)


def node(w, title, time, type_=None):
    entity_id = w.find_entity(title, type_)
    assert entity_id, f"缺实体：{title}"
    tp_id = w.find_timepoint(entity_id, time)
    assert tp_id, f"{title} 缺少 time={time} 节点"
    return entity_id, tp_id


def add_cite(w, table, target_id, eid, quote, decision, **kwargs):
    return w.citation(table, target_id, cite(eid), quote, decision, **kwargs)


def add_relation(
    w, subject_tp, object_tp, rel_type, eid, quote, decision,
    staff_quota=None, staff_type=None,
):
    rel = w.relationship(
        subject_tp, object_tp, rel_type, decision, quote,
        staff_quota=staff_quota, staff_type=staff_type,
    )
    add_cite(w, "Relationships", rel, eid, quote, f"为{rel_type}关系提供证据")
    return rel


def entry74():
    eid = 74
    Q_ENT = q(eid, "官署名，隶中书门下。")
    Q_ORIGIN = q(
        eid, "五代后晋开运中（944—946）已见有舍人院之称（《宋会要·职官》3之13）。",
    )
    Q_SONG = q(eid, "宋前期舍人院在中书制敕院内（《分纪》卷7）。")
    Q_END = q(
        eid, "元丰新官制，废舍人院，改为中书后省（《合璧后集》卷21《中书舍人》）。",
    )
    Q_FUNCTION = q(eid, "为知制造与直舍人院莅行公事之所。")
    Q_STAFF = q(
        eid,
        "院内有中书舍人，如中书舍人阙则以它官知制诰，知制诰常置二员或四员，"
        "资浅者称直舍人院。暂时摄领者称权知制诰。",
    )
    w = writer(eid)
    entity_id = w.entity(
        "舍人院", "机构", "辞典明载为官署并隶中书门下，建机构实体。", quotation=Q_ENT,
    )
    tp_origin = w.timepoint(
        entity_id, "五代后晋开运中", "已见舍人院之称",
        "据职源与沿革建宋前源流节点。", Q_ORIGIN, attr_category="官署名",
    )
    add_cite(w, "Timepoints", tp_origin, eid, Q_ORIGIN, "为五代后晋源流提供证据")
    tp_song = w.timepoint(
        entity_id, "宋前期", "在中书制敕院内，为知制诰与直舍人院莅行公事之所",
        "据沿革与职能建宋前期节点。", Q_SONG, attr_category="官署名",
    )
    add_cite(w, "Timepoints", tp_song, eid, Q_ENT, "为官署性质和隶属提供证据")
    add_cite(w, "Timepoints", tp_song, eid, Q_SONG, "为宋前期所在提供证据")
    add_cite(w, "Timepoints", tp_song, eid, Q_FUNCTION, "为舍人院职能提供证据", note="职能")
    add_cite(w, "Timepoints", tp_song, eid, Q_STAFF, "为舍人院编制提供证据", note="编制")
    tp_end = w.timepoint(
        entity_id, "北宋元丰新官制", "废舍人院，改为中书后省",
        "据职源与沿革建废改节点。", Q_END, attr_category="官署名",
    )
    add_cite(w, "Timepoints", tp_end, eid, Q_END, "为元丰废改提供证据")

    successor_id = w.entity(
        "中书后省", "机构", "本条明确舍人院改为中书后省，建后继机构实体。",
        quotation=Q_END,
    )
    successor_tp = w.timepoint(
        successor_id, "北宋元丰新官制", "由舍人院改置",
        "据本条建立中书后省新置节点。", Q_END, attr_category="官署名",
    )
    add_cite(w, "Timepoints", successor_tp, eid, Q_END, "为中书后省改置提供证据")
    add_relation(w, tp_end, successor_tp, "前后演变", eid, Q_END, "舍人院废改为中书后省。")

    _, central_tp = node(w, "中书门下", "宋前期", "机构")
    _, decree_tp = node(w, "制敕院", "宋前期", "机构")
    add_relation(w, central_tp, tp_song, "上下级机构", eid, Q_ENT, "舍人院隶中书门下。")
    add_relation(w, decree_tp, tp_song, "上下级机构", eid, Q_SONG, "宋前期舍人院在制敕院内。")

    posts = (
        ("中书舍人", None, "官职"),
        ("知制诰", None, "差遣名"),
        ("直舍人院", None, "差遣官名"),
        ("权知制诰", None, "差遣名"),
    )
    for title, quota, category in posts:
        post_id = w.find_entity(title, "官职")
        if not post_id:
            post_id = w.entity(
                title, "官职", f"本条编制直接列出{title}，建官职实体。", quotation=Q_STAFF,
            )
        post_tp = w.find_timepoint(post_id, "宋前期")
        if not post_tp:
            post_tp = w.timepoint(
                post_id, "宋前期", f"在舍人院莅行公事或充任相关制诰职事",
                f"据舍人院职能与编制建{title}宋前期节点。", Q_STAFF,
                attr_category=category,
            )
        add_cite(w, "Timepoints", post_tp, eid, Q_STAFF, f"为{title}在舍人院的配置提供证据")
        add_relation(
            w, tp_song, post_tp, "编制隶属", eid, Q_STAFF,
            f"舍人院配置{title}。知制诰员额原文为二员或四员，故不硬填单一整数。",
            staff_quota=quota, staff_type="官",
        )
    w.commit()


def entry75():
    eid = 75
    Q_ENT = q(eid, "差遣名。")
    Q_ORIGIN = q(
        eid,
        "唐开元初（714或715），以它官代中书舍人掌拟诏敕策命者，称“兼知制诰”"
        "（《新唐书·百官志》2）。",
    )
    Q_DUTY = q(
        eid, "掌草拟诰命，与翰林学士对掌外制、内制（《宋史·职官志》1《中书省》）。",
    )
    w = writer(eid)
    entity_id, tp_song = node(w, "知制诰", "宋前期", "官职")
    tp_origin = w.timepoint(
        entity_id, "唐开元初", "以它官代中书舍人掌拟诏敕策命，称兼知制诰",
        "据职源建唐代源流节点。", Q_ORIGIN, attr_category="差遣名", chain="head",
    )
    add_cite(w, "Timepoints", tp_origin, eid, Q_ORIGIN, "为唐开元初职源提供证据")
    add_cite(w, "Timepoints", tp_song, eid, Q_ENT, "为知制诰差遣性质提供证据")
    add_cite(w, "Timepoints", tp_song, eid, Q_DUTY, "为知制诰职掌提供证据", note="职掌")
    w.commit()


def entry76():
    eid = 76
    Q_ENT = q(eid, "差遣官名。")
    Q_SOURCE = q(
        eid,
        "唐朝以他官兼权，称直某官；宋初始有直舍人院之名"
        "（《梦溪笔谈》卷1《故事》、《分纪》卷7《直舍人院》）。",
    )
    Q_END = q(eid, "元丰改制罢，以权中书舍人代之。")
    Q_RESTORE = q(
        eid, "但南宋嘉泰间偶置之（《朝野杂记》乙集卷13《直舍人院》）。",
    )
    Q_DUTY = q(eid, "与知制诰同，只是资格比知制造低而已。")
    w = writer(eid)
    entity_id, tp_song = node(w, "直舍人院", "宋前期", "官职")
    tp_tang = w.timepoint(
        entity_id, "唐朝", "以他官兼权而称直某官，为直舍人院制度之源",
        "据职源与沿革建唐代源流节点。", Q_SOURCE,
        attr_category="差遣官名", chain="head",
    )
    add_cite(w, "Timepoints", tp_tang, eid, Q_SOURCE, "为唐代源流提供证据")
    tp_early = w.timepoint(
        entity_id, "宋初", "始有直舍人院之名，职掌同知制诰而资格较低",
        "据职源与沿革建宋初节点。", Q_SOURCE, attr_category="差遣官名",
        chain="none",
    )
    w.relink(tp_tang, "宋初节点接在唐代源流之后", succ_id=tp_early)
    w.relink(tp_early, "宋初节点接在既有宋前期节点之前", prev_id=tp_tang, succ_id=tp_song)
    w.relink(tp_song, "宋初节点前插，保持互反", prev_id=tp_early)
    add_cite(w, "Timepoints", tp_early, eid, Q_SOURCE, "为宋初始有直舍人院之名提供证据")
    add_cite(w, "Timepoints", tp_early, eid, Q_DUTY, "为直舍人院职掌和资格提供证据")
    tp_end = w.timepoint(
        entity_id, "北宋元丰改制", "罢直舍人院，以权中书舍人代之",
        "据职源与沿革建元丰终结节点。", Q_END, attr_category="差遣官名",
    )
    add_cite(w, "Timepoints", tp_end, eid, Q_END, "为元丰罢直舍人院提供证据")
    tp_restore = w.timepoint(
        entity_id, "南宋嘉泰间", "偶置直舍人院",
        "据职源与沿革建南宋嘉泰间偶置节点。", Q_RESTORE, attr_category="差遣官名",
    )
    add_cite(w, "Timepoints", tp_restore, eid, Q_RESTORE, "为嘉泰间偶置提供证据")

    successor_id = w.entity(
        "权中书舍人", "官职", "本条明确元丰改制以权中书舍人代直舍人院，建后继官职。",
        quotation=Q_END,
    )
    successor_tp = w.timepoint(
        successor_id, "北宋元丰改制", "代替被罢的直舍人院",
        "据本条建立权中书舍人节点。", Q_END, attr_category="差遣官名",
    )
    add_cite(w, "Timepoints", successor_tp, eid, Q_END, "为权中书舍人代置提供证据")
    add_relation(w, tp_end, successor_tp, "前后演变", eid, Q_END, "直舍人院罢，以权中书舍人代之。")
    w.commit()


def entry77():
    eid = 77
    Q_ENT = q(eid, "官司名。北宋前期隶中书门下。院在皇城外。")
    Q_PRE = q(
        eid,
        "北齐有起居省。唐代起居官分隶门下省、中书省。宋初，门下省起居郎、"
        "中书省起居舍人虽各存其名，但职事不举。",
    )
    Q_START = q(eid, "太宗淳化五年四月五日，始于禁中置起居院。")
    Q_MOVE1 = q(eid, "大中祥符六年八月十一日徙院于三馆内")
    Q_MOVE2 = q(eid, "八年移院于右掖门外之西廊。")
    Q_YF = q(
        eid,
        "元丰五年五月行新官制，门下省起居郎、中书省起居舍人各举其职，"
        "罢起居院同修起居注，然起居院之名犹存",
    )
    Q_YY = q(eid, "元祐三年复徙于右掖门之内")
    Q_DUTY = q(eid, "备修注官之地。")
    Q_STAFF = q(
        eid,
        "设勾当起居院事一人，楷书四人，驱使官一人。同修起居注官二人"
        "（《宋会要·职官》2之10《起居院》、《通考·职官》4《起居》）。",
    )
    w = writer(eid)
    entity_id = w.entity(
        "起居院", "机构", "辞典明载为官司并隶中书门下，建机构实体。", quotation=Q_ENT,
    )
    tp_start = w.timepoint(
        entity_id, "北宋淳化五年四月五日", "始于禁中置起居院，备修注官之地",
        "据职源与沿革建始置节点。", Q_START, attr_category="官司名",
    )
    add_cite(w, "Timepoints", tp_start, eid, Q_ENT, "为官司性质、隶属和位置提供证据")
    add_cite(w, "Timepoints", tp_start, eid, Q_START, "为淳化五年始置提供证据")
    add_cite(w, "Timepoints", tp_start, eid, Q_DUTY, "为起居院职能提供证据", note="职掌")
    add_cite(w, "Timepoints", tp_start, eid, Q_STAFF, "为起居院编制提供证据", note="编制")
    tp_move1 = w.timepoint(
        entity_id, "北宋大中祥符六年八月十一日", "徙院于三馆内",
        "据沿革建迁址节点。", Q_MOVE1, attr_category="官司名",
    )
    add_cite(w, "Timepoints", tp_move1, eid, Q_MOVE1, "为迁至三馆内提供证据")
    tp_move2 = w.timepoint(
        entity_id, "北宋大中祥符八年", "移院于右掖门外西廊",
        "据沿革建迁址节点。", Q_MOVE2, attr_category="官司名",
    )
    add_cite(w, "Timepoints", tp_move2, eid, Q_MOVE2, "为迁至右掖门外西廊提供证据")
    tp_yf = w.timepoint(
        entity_id, "北宋元丰五年五月",
        "新官制下罢起居院同修起居注，但起居院之名犹存",
        "据沿革建元丰新制节点；不把起居院误作整体废除。", Q_YF,
        attr_category="官司名",
    )
    add_cite(w, "Timepoints", tp_yf, eid, Q_YF, "为元丰新制后院名犹存提供证据")
    tp_yy = w.timepoint(
        entity_id, "北宋元祐三年", "复徙于右掖门内",
        "据沿革建元祐三年迁址节点。", Q_YY, attr_category="官司名",
    )
    add_cite(w, "Timepoints", tp_yy, eid, Q_YY, "为元祐三年迁址提供证据")
    _, central_tp = node(w, "中书门下", "宋前期", "机构")
    add_relation(w, central_tp, tp_start, "上下级机构", eid, Q_ENT, "北宋前期起居院隶中书门下。")

    # 宋初名存职事不举，元丰新制各举其职。
    active_posts = (("起居郎", "门下省"), ("起居舍人", "中书省"))
    active_nodes = {}
    for title, office in active_posts:
        post_id = w.entity(
            title, "官职", f"本条直接记载{office}{title}，建官职实体。", quotation=Q_PRE,
        )
        tp_early = w.timepoint(
            post_id, "宋初", f"{office}{title}名存而职事不举",
            "据沿革建宋初名存职事不举节点。", Q_PRE, attr_category="起居官",
        )
        add_cite(w, "Timepoints", tp_early, eid, Q_PRE, f"为宋初{title}状态提供证据")
        tp_active = w.timepoint(
            post_id, "北宋元丰五年五月", f"新官制下{office}{title}举其职",
            "据沿革建元丰新制举职节点。", Q_YF, attr_category="起居官",
        )
        add_cite(w, "Timepoints", tp_active, eid, Q_YF, f"为元丰五年{title}举职提供证据")
        active_nodes[title] = tp_active

    staff_posts = (("勾当起居院事", 1, "官"), ("楷书", 4, "吏"), ("驱使官", 1, "吏"))
    for title, quota, staff_type in staff_posts:
        post_id = w.find_entity(title, "官职")
        if not post_id:
            post_id = w.entity(
                title, "官职", f"起居院编制明列{title}{quota}人，建官职实体。", quotation=Q_STAFF,
            )
        post_tp = w.find_timepoint(post_id, "宋前期")
        if not post_tp:
            post_tp = w.timepoint(
                post_id, "宋前期", f"隶起居院，编制{quota}人",
                f"据起居院编制建{title}节点。", Q_STAFF, attr_category="起居院属员",
            )
        add_cite(w, "Timepoints", post_tp, eid, Q_STAFF, f"为{title}编制提供证据")
        add_relation(
            w, tp_start, post_tp, "编制隶属", eid, Q_STAFF,
            f"起居院设{title}{quota}人。", staff_quota=quota, staff_type=staff_type,
        )

    note_id = w.entity(
        "同修起居注", "官职", "起居院编制明列同修起居注官二人，建官职实体。",
        quotation=Q_STAFF,
    )
    note_tp = w.timepoint(
        note_id, "宋前期", "隶起居院，修起居注，编制二人",
        "据起居院编制建宋前期节点。", Q_STAFF, attr_category="差遣官名",
    )
    add_cite(w, "Timepoints", note_tp, eid, Q_STAFF, "为同修起居注编制提供证据")
    add_relation(
        w, tp_start, note_tp, "编制隶属", eid, Q_STAFF,
        "起居院设同修起居注官二人。", staff_quota=2, staff_type="官",
    )
    note_end = w.timepoint(
        note_id, "北宋元丰五年", "新官制正名，罢同修起居注",
        "本条记元丰五年五月罢；#78 记四月，先以年份建共同节点保存冲突证据。",
        Q_YF, attr_category="差遣官名",
    )
    add_cite(
        w, "Timepoints", note_end, eid, Q_YF,
        "本条记元丰五年五月罢同修起居注",
        note="与“同修起居注”条所记元丰五年四月不一致", conflict_flag=1,
    )
    for title, target_tp in active_nodes.items():
        add_relation(
            w, note_end, target_tp, "前后演变", eid, Q_YF,
            f"元丰新制罢同修起居注，{title}举其职。",
        )
    w.commit()


def entry78():
    eid = 78
    Q_ENT = q(eid, "差遣官名。隶起居院。")
    Q_SOURCE = q(
        eid,
        "北宋太宗淳化五年四月五日，置起居院，设掌起居郎事、掌起居舍人事，"
        "以行门下省起居郎、中书省起居舍人之职事。其后赴起居院修起居注官，"
        "称“同修起居注”，省称修起居注。",
    )
    Q_END = q(eid, "神宗元丰五年四月行新官制正名，罢同修起居注")
    Q_DUTY = q(
        eid,
        "大朝会，左、右各一人对立于香案前，以存左、右史侍立正殿之古制；"
        "皇帝常朝之日，轮流递值于崇政、延和二殿；皇帝出巡，随从出入；"
        "所到之处，皆以记录皇帝言动为职，所书皇帝言论行止等，修成起居注"
        "以送史馆备修实录与正史（《宋会要·职官》2之10）。",
    )
    Q_QUOTA = q(eid, "二人。")
    Q_GRADE = q(
        eid,
        "同修起居注，由三馆秘阁校理以上馆职官及进士高等、制科出身之有才望者充，"
        "其地位之清要几与知制诰同，非一般官吏或凭资格所能得"
        "（《合璧后集》卷19《左、右史门》《宋会要·职官》2之13）。",
    )
    w = writer(eid)
    entity_id, tp_song = node(w, "同修起居注", "宋前期", "官职")
    add_cite(w, "Timepoints", tp_song, eid, Q_ENT, "为差遣性质及隶属提供证据")
    add_cite(w, "Timepoints", tp_song, eid, Q_SOURCE, "为同修起居注职源提供证据")
    add_cite(w, "Timepoints", tp_song, eid, Q_DUTY, "为同修起居注职掌提供证据", note="职掌")
    add_cite(w, "Timepoints", tp_song, eid, Q_QUOTA, "为同修起居注二人编制提供证据", note="编制")
    add_cite(w, "Timepoints", tp_song, eid, Q_GRADE, "为同修起居注任职资格和品位提供证据", note="品位")
    _, tp_end = node(w, "同修起居注", "北宋元丰五年", "官职")
    add_cite(
        w, "Timepoints", tp_end, eid, Q_END,
        "本条记元丰五年四月罢同修起居注",
        note="与“起居院”条所记元丰五年五月不一致", conflict_flag=1,
    )

    initial_nodes = []
    for title, office in (("掌起居郎事", "门下省起居郎"), ("掌起居舍人事", "中书省起居舍人")):
        post_id = w.entity(
            title, "官职", f"本条明确淳化五年置{title}，建官职实体。", quotation=Q_SOURCE,
        )
        post_tp = w.timepoint(
            post_id, "北宋淳化五年四月五日", f"置{title}，行{office}之职事",
            f"据职源建{title}始置节点。", Q_SOURCE, attr_category="差遣官名",
        )
        add_cite(w, "Timepoints", post_tp, eid, Q_SOURCE, f"为{title}始置及职掌提供证据")
        initial_nodes.append((title, post_tp))
    for title, post_tp in initial_nodes:
        add_relation(
            w, post_tp, tp_song, "前后演变", eid, Q_SOURCE,
            f"淳化五年先置{title}；其后赴起居院修注者称同修起居注。",
        )

    # 给 #77 已建的“罢同修→起居郎/起居舍人”关系追加本条四月记载，保留月分冲突。
    for title in ("起居郎", "起居舍人"):
        _, target_tp = node(w, title, "北宋元丰五年五月", "官职")
        row = w.conn.execute(
            "SELECT id FROM Relationships WHERE subject_id=? AND object_id=?"
            " AND relation_type='前后演变'", (tp_end, target_tp)
        ).fetchone()
        assert row
        add_cite(
            w, "Relationships", row[0], eid, Q_END,
            f"本条四月记载补证罢同修起居注后由{title}正名举职",
            note="与“起居院”条所记五月不一致", conflict_flag=1,
        )
    w.commit()


def main():
    entry74()
    entry75()
    entry76()
    entry77()
    entry78()
    print("完成 chapter2t4 #74–#78")


if __name__ == "__main__":
    main()
