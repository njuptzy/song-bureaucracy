#!/usr/bin/env python3
"""提取 chapter2t4 第 79–88 条：起居官、三铨与审官院系统。"""
import json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")


def load(eid):
    with sqlite3.connect(DICT_DB) as c:
        row = c.execute("SELECT title,page,text,fields FROM chapter2t4 WHERE id=?", (eid,)).fetchone()
    full = (row[2] or "") + "\n" + "\n".join(
        str(v) for k, v in json.loads(row[3] or "{}").items() if not k.startswith("_")
    )
    return row[0], row[1], full


FULL = {i: load(i) for i in range(79, 89)}


def q(eid, text):
    assert text in FULL[eid][2], f"#{eid} 不含：{text}"
    return text


def w(eid):
    return EntryWriter(ENTRY_DB, FULL[eid][0], FULL[eid][1])


def cite(eid):
    return f"《宋代官制辞典》第{FULL[eid][1]}页“{FULL[eid][0]}”条"


def ac(x, table, rid, eid, quote, decision, **kw):
    return x.citation(table, rid, cite(eid), quote, decision, **kw)


def entity(x, title, typ, quote, decision):
    return x.entity(title, typ, decision, quotation=quote)


def tp(x, ent, time, event, eid, quote, category, decision, **kw):
    rid = x.timepoint(ent, time, event, decision, quote, attr_category=category, **kw)
    ac(x, "Timepoints", rid, eid, quote, decision)
    return rid


def rel(x, s, o, kind, eid, quote, decision, **kw):
    rid = x.relationship(s, o, kind, decision, quote, **kw)
    ac(x, "Relationships", rid, eid, quote, decision)
    return rid


def existing(x, title, time, typ=None):
    eid = x.find_entity(title, typ)
    assert eid, f"缺实体 {title}"
    tid = x.find_timepoint(eid, time)
    assert tid, f"{title} 缺 time={time}"
    return eid, tid


def rechain(x, entity_id, ordered_ids, decision):
    """按已核定历史顺序重建单实体 prev/succ 互反链。"""
    for i, tid in enumerate(ordered_ids):
        x.relink(
            tid,
            decision=decision,
            prev_id=ordered_ids[i - 1] if i else None,
            succ_id=ordered_ids[i + 1] if i + 1 < len(ordered_ids) else None,
        )


def entry79_80(eid, title, rel_id):
    text = FULL[eid][2].split("\n", 1)[0]
    x = w(eid)
    ent, tid = existing(x, title, "北宋淳化五年四月五日", "官职")
    ac(x, "Timepoints", tid, eid, text, "本条直接证明该差遣与起居院同时始置及其改称。")
    relation = x.conn.execute("SELECT id FROM Relationships WHERE id=?", (rel_id,)).fetchone()
    assert relation
    ac(x, "Relationships", rel_id, eid, text, "本条直接证明该差遣未几改称同修起居注。")
    _, office_tp = existing(x, "起居院", "北宋淳化五年四月五日", "机构")
    rel(x, office_tp, tid, "编制隶属", eid, text, f"{title}与置起居院同时设置。", staff_type="官")
    x.commit()


def entry81():
    eid = 81
    qe = q(eid, "官司名。宋初吏部铨选机构")
    qsrc = q(eid, "隋朝已置，掌选六品、七品官。")
    qtang = q(eid, "唐为吏部三铨之一。")
    qsong = q(eid, "北宋初沿置。")
    qend = q(eid, "太平兴国六年九月十二日，为差遣院所代")
    qduty = q(eid, "掌七品以下文臣选授")
    x = w(eid)
    ent = entity(x, "吏部尚书铨", "机构", qe, "辞典明载为宋初吏部铨选机构。")
    tp(x, ent, "隋朝", "已置，掌选六品、七品官", eid, qsrc, "官司名", "建隋代职源节点。")
    tp(x, ent, "唐朝", "为吏部三铨之一", eid, qtang, "官司名", "建唐代沿革节点。")
    song = tp(x, ent, "北宋初", "沿置，掌七品以下文臣选授", eid, qsong, "官司名", "建北宋初沿置节点。")
    ac(x, "Timepoints", song, eid, qduty, "补充北宋初职掌证据。", note="职掌")
    end = tp(x, ent, "北宋太平兴国六年九月十二日", "为差遣院所代", eid, qend, "官司名", "建终结节点。")
    de = entity(x, "差遣院", "机构", qend, "本条明确后继为差遣院。")
    dt = tp(x, de, "北宋太平兴国六年九月十二日", "取代吏部尚书铨", eid, qend, "官司名", "建后继机构节点。")
    rel(x, end, dt, "前后演变", eid, qend, "吏部尚书铨为差遣院所代。")
    x.commit()


def entry82():
    eid = 82
    qdef = q(eid, "吏部尚书铨、吏部西铨、吏部东铨合称。")
    qtang = q(eid, "唐、五代有吏部三铨")
    qsong = q(eid, "宋立国之初，三铨之名仍旧，而侍郎所主东、西铨，仅存官印而事废；唯吏部尚书铨举职事。")
    x = w(eid)
    group = entity(x, "吏部三铨", "机构", qdef, "原文明载三机构合称，建统称机构。")
    gt = tp(x, group, "唐、五代", "吏部尚书铨、吏部西铨、吏部东铨合称吏部三铨", eid, qtang, "机构合称", "建唐五代合称节点。")
    gs = tp(x, group, "宋立国之初", "三铨之名仍旧，东、西铨事废，唯尚书铨举职事", eid, qsong, "机构合称", "建宋初制度状态节点。")
    for title in ("吏部尚书铨", "吏部西铨", "吏部东铨"):
        en = x.find_entity(title, "机构") or entity(x, title, "机构", qdef, f"原文列为吏部三铨实例：{title}。")
        tt = x.find_timepoint(en, "唐、五代") or tp(x, en, "唐、五代", "为吏部三铨之一", eid, qdef, "官司名", f"建{title}唐五代节点。")
        ss_event = "举职事" if title == "吏部尚书铨" else "仅存官印而事废"
        ss = x.find_timepoint(en, "宋立国之初") or tp(x, en, "宋立国之初", ss_event, eid, qsong, "官司名", f"建{title}宋初节点。")
        relation = rel(x, gt, tt, "统称与实例", eid, qdef, f"吏部三铨包括{title}；统称关系只建一次。")
        ac(x, "Relationships", relation, eid, qsong, f"补充宋初{title}仍属三铨的证据。")
        if title == "吏部尚书铨":
            _, sui = existing(x, title, "隋朝", "机构")
            _, tang = existing(x, title, "唐朝", "机构")
            _, song_early = existing(x, title, "北宋初", "机构")
            _, end = existing(x, title, "北宋太平兴国六年九月十二日", "机构")
            rechain(
                x, en, [sui, tang, tt, ss, song_early, end],
                "按隋→唐/五代→宋立国之初→北宋初→太平兴国六年重排",
            )
    x.commit()


def entry83():
    eid = 83
    qe = q(eid, "官司名。")
    qs = q(eid, "始置于北宋太平兴国六年九月十二日")
    qend = q(eid, "淳化四年五月二十日并入审官院")
    qd = q(eid, "考核、比较少卿监以下京朝官任满归朝待命者，据中书所下员阙，量材录用，授以新官")
    x = w(eid)
    ent = x.find_entity("差遣院", "机构") or entity(x, "差遣院", "机构", qe, "辞典明载为官司。")
    start = x.find_timepoint(ent, "北宋太平兴国六年九月十二日")
    assert start
    ac(x, "Timepoints", start, eid, qs, "本条补充差遣院始置的直接证据。")
    ac(x, "Timepoints", start, eid, qd, "补充差遣院职掌。", note="职掌")
    end = tp(x, ent, "北宋淳化四年五月二十日", "并入审官院", eid, qend, "官司名", "建并入节点。")
    se = entity(x, "审官院", "机构", qend, "本条明确差遣院并入审官院。")
    st = tp(x, se, "北宋淳化四年五月二十日", "接收并入的差遣院", eid, qend, "官司名", "建审官院承接节点。")
    rel(x, end, st, "前后演变", eid, qend, "差遣院并入审官院。")
    x.commit()


def entry84():
    eid = 84
    qe=q(eid,"官司名。"); qs=q(eid,"北宋淳化三年十月二十二日始置"); qend=q(eid,"四年二月二十八日改名审官院"); qd=q(eid,"掌考核京朝官，所谓甄别“中外官吏清浊”，以定黜陟")
    x=w(eid); en=entity(x,"磨勘京朝官院","机构",qe,"辞典明载为官司。")
    s=tp(x,en,"北宋淳化三年十月二十二日","始置，考核京朝官以定黜陟",eid,qs,"官司名","建始置节点。"); ac(x,"Timepoints",s,eid,qd,"补充职掌。",note="职掌")
    e=tp(x,en,"北宋淳化四年二月二十八日","改名审官院",eid,qend,"官司名","建改名节点。")
    oe=x.find_entity("审官院","机构") or entity(x,"审官院","机构",qend,"本条明确后继机构。")
    ot=tp(x,oe,"北宋淳化四年二月二十八日","由磨勘京朝官院改名",eid,qend,"官司名","建后继节点。")
    rel(x,e,ot,"前后演变",eid,qend,"磨勘京朝官院改名审官院。")
    may=x.find_timepoint(oe,"北宋淳化四年五月二十日")
    if may:
        ordered=[ot,may]
        later=x.find_timepoint(oe,"北宋熙宁三年五月二十八日")
        if later:
            ordered.append(later)
        rechain(x,oe,ordered,"审官院二月改名始置在前，五月接收差遣院在后，熙宁改名终结")
    x.commit()


def entry85():
    eid=85; qe=q(eid,"官司名。"); qs=q(eid,"北宋太宗淳化三年十月二十二日始置"); qend=q(eid,"淳化四年二月二十八日改名考课院"); qd=q(eid,"考核幕职州县官（选人）资历与功过，以定黜陟"); qstaff=q(eid,"设同知磨勘幕职州县官院事三人")
    x=w(eid); en=entity(x,"磨勘幕职州县官院","机构",qe,"辞典明载为官司。")
    s=tp(x,en,"北宋淳化三年十月二十二日","始置，考核幕职州县官资历与功过",eid,qs,"官司名","建始置节点。"); ac(x,"Timepoints",s,eid,qd,"补充职掌。",note="职掌")
    post=entity(x,"同知磨勘幕职州县官院事","官职",qstaff,"编制明载此官。")
    pt=tp(x,post,"北宋淳化三年十月二十二日","设三人，由朝官以上文臣差充",eid,qstaff,"差遣官名","建编制节点。")
    rel(x,s,pt,"编制隶属",eid,qstaff,"该院设同知院事三人。",staff_quota=3,staff_type="官")
    e=tp(x,en,"北宋淳化四年二月二十八日","改名考课院",eid,qend,"官司名","建改名节点。")
    oe=entity(x,"考课院","机构",qend,"本条明确后继机构。")
    ot=tp(x,oe,"北宋淳化四年二月二十八日","由磨勘幕职州县官院改名",eid,qend,"官司名","建后继节点。")
    rel(x,e,ot,"前后演变",eid,qend,"磨勘幕职州县官院改名考课院。")
    x.commit()


def entry86():
    eid=86; text=FULL[eid][2].split("\n",1)[0]; x=w(eid)
    en,st=existing(x,"考课院","北宋淳化四年二月二十八日","机构")
    ac(x,"Timepoints",st,eid,text,"本条直接证明考课院改名设立及职掌。")
    end=tp(x,en,"北宋淳化四年五月二十日","并入流内铨",eid,text,"官司名","建并入节点。")
    oe=entity(x,"吏部流内铨","机构",text,"本条明确考课院并入流内铨；采用正式全称。")
    ot=tp(x,oe,"北宋淳化四年五月二十日","接收并入的考课院",eid,text,"官司名","建承接节点。")
    rel(x,end,ot,"前后演变",eid,text,"考课院并入流内铨。")
    x.commit()


def entry87():
    eid=87; qe=q(eid,"官司名。"); qstart=q(eid,"北宋淳化四年二月，改磨勘京朝官院为审官院，又将差遣院并入。"); qend=q(eid,"熙宁三年五月二十八日，改审官院为审官东院"); qd=q(eid,"考核六品以下京朝官殿最，排列其爵名、秩位，在此基础上提出相应的内、外职务任命方案，上报以待批"); qstaff=q(eid,"审官院隶中书门下。知院官二人，书令史七人，掌舍二人")
    x=w(eid); en=x.find_entity("审官院","机构") or entity(x,"审官院","机构",qe,"辞典明载为官司。")
    st=x.find_timepoint(en,"北宋淳化四年二月二十八日") or tp(x,en,"北宋淳化四年二月二十八日","由磨勘京朝官院改名",eid,qstart,"官司名","建始置节点。")
    ac(x,"Timepoints",st,eid,qstart,"补充审官院来源与差遣院并入证据。"); ac(x,"Timepoints",st,eid,qd,"补充职掌。",note="职掌"); ac(x,"Timepoints",st,eid,qstaff,"补充隶属与编制。",note="编制")
    central,ct=existing(x,"中书门下","宋前期","机构"); rel(x,ct,st,"上下级机构",eid,qstaff,"审官院隶中书门下。")
    for title,quota,kind in (("书令史",7,"吏"),("掌舍",2,"吏")):
        pe=x.find_entity(title,"官职") or entity(x,title,"官职",qstaff,f"审官院编制明列{title}。")
        pt=x.find_timepoint(pe,"北宋淳化四年二月") or tp(x,pe,"北宋淳化四年二月",f"审官院设{quota}人",eid,qstaff,"官职名","建编制节点。")
        rel(x,st,pt,"编制隶属",eid,qstaff,f"审官院设{title}{quota}人。",staff_quota=quota,staff_type=kind)
    end=tp(x,en,"北宋熙宁三年五月二十八日","改为审官东院",eid,qend,"官司名","建改名节点。")
    oe=entity(x,"审官东院","机构",qend,"本条明确后继机构。")
    ot=tp(x,oe,"北宋熙宁三年五月二十八日","由审官院改名",eid,qend,"官司名","建后继节点。")
    rel(x,end,ot,"前后演变",eid,qend,"审官院改为审官东院。")
    x.commit()


def entry88():
    eid=88; text=FULL[eid][2].split("\n",1)[0]; x=w(eid)
    en=x.find_entity("知审官院事","官职") or entity(x,"知审官院事","官职",text,"辞典明载为北宋差遣官。")
    tid=tp(x,en,"北宋淳化四年五月二十日","始置，掌审官院京朝官磨勘、差遣职事",eid,text,"差遣官名","建始置及职掌节点。",attr_grade="知杂侍御史（从六品）以上朝官或翰林学士（正三品）充")
    office,ot=existing(x,"审官院","北宋淳化四年二月二十八日","机构")
    relation=rel(x,ot,tid,"编制隶属",eid,text,"知审官院事掌审官院职事；编制关系只建一次。",staff_type="官")
    x.commit()
    # “审官院”条的“知院官二人”是同一编制事实，作为第二条证据挂到精确关系上。
    qstaff=q(87,"审官院隶中书门下。知院官二人，书令史七人，掌舍二人")
    x87=w(87)
    ac(x87,"Relationships",relation,87,qstaff,"补充审官院设知院官二人的证据。")
    x87.commit()


def main():
    entry79_80(79,"掌起居郎事",157)
    entry79_80(80,"掌起居舍人事",158)
    entry81(); entry82(); entry83(); entry84(); entry85(); entry86(); entry87(); entry88()


if __name__ == "__main__":
    main()
