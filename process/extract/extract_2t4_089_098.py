#!/usr/bin/env python3
"""提取 chapter2t4 第 89–98 条：吏部附属机构与审官东院系统。"""
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


FULL = {i: load(i) for i in range(89, 99)}


def q(eid, text):
    assert text in FULL[eid][2], f"#{eid} 不含：{text}"
    return text


def writer(eid):
    return EntryWriter(ENTRY_DB, FULL[eid][0], FULL[eid][1])


def cite(eid):
    return f"《宋代官制辞典》第{FULL[eid][1]}页“{FULL[eid][0]}”条"


def citation(w, table, rid, eid, quote, decision, **kw):
    return w.citation(table, rid, cite(eid), quote, decision, **kw)


def entity(w, title, typ, eid, quote, decision):
    return w.entity(title, typ, decision, quotation=quote)


def timepoint(w, ent, time, event, eid, quote, category, decision, **kw):
    rid = w.timepoint(ent, time, event, decision, quote, attr_category=category, **kw)
    citation(w, "Timepoints", rid, eid, quote, decision)
    return rid


def relationship(w, subject, obj, kind, eid, quote, decision, **kw):
    rid = w.relationship(subject, obj, kind, decision, quote, **kw)
    citation(w, "Relationships", rid, eid, quote, decision)
    return rid


def node(w, title, time, typ=None):
    ent = w.find_entity(title, typ)
    assert ent, f"缺实体：{title}"
    tp = w.find_timepoint(ent, time)
    assert tp, f"{title} 缺 time={time}"
    return ent, tp


def refine_time(w, ent, old_time, new_time, event, quote, decision):
    """同一制度变化后来获得更精确纪年时，细化原节点而不制造同义节点。"""
    exact = w.find_timepoint(ent, new_time)
    if exact:
        return exact
    tp = w.find_timepoint(ent, old_time)
    assert tp, f"实体 {ent} 缺待细化节点 time={old_time}"
    w.conn.execute(
        "UPDATE Timepoints SET time=?,event=?,quotation=? WHERE id=?",
        (new_time, event, quote, tp),
    )
    w._br("Timepoints", tp, f"时间细化 {old_time} -> {new_time}：{decision}")
    return tp


def entry89():
    eid=89; qe=q(eid,"官司名。"); qt=q(eid,"南曹之名始自唐"); qs=q(eid,"北宋沿置"); qend=q(eid,"神宗熙宁五年七月，并入流内钰"); qd=q(eid,"掌选人履历验审，将按吏部格式可以叙资迁调的选人材料（如历任功过）送往流内钰，经流内钰注拟迁资的选人，再由南曹发给历子。这是流内钰的一个辅助性机构"); qstaff=q(eid,"由判吏部流内铨事兼领曹事。令史九人或六人、驱使官一至三人")
    w=writer(eid); en=entity(w,"吏部南曹","机构",eid,qe,"辞典明载为官司。")
    timepoint(w,en,"唐朝","已有南曹之名",eid,qt,"官司名","建唐代职源节点。")
    song=timepoint(w,en,"北宋","沿置，掌选人履历验审，为流内铨辅助机构",eid,qs,"官司名","建北宋沿置节点。")
    citation(w,"Timepoints",song,eid,qd,"补充职掌与机构性质。",note="职掌")
    citation(w,"Timepoints",song,eid,qstaff,"补充兼领方式及吏额。",note="编制；员额存在九/六、一至三的并列记载，不硬填单一 quota")
    end=timepoint(w,en,"北宋熙宁五年七月","并入流内铨",eid,qend,"官司名","建并入节点。")
    oe=w.find_entity("吏部流内铨","机构") or entity(w,"吏部流内铨","机构",eid,qend,"本条明确后继机构；采用正式全称。")
    ot=timepoint(w,oe,"北宋熙宁五年七月","接收并入的吏部南曹",eid,qend,"官司名","建承接节点。")
    relationship(w,end,ot,"前后演变",eid,qend,"吏部南曹并入流内铨。")
    w.commit()


def entry90():
    eid=90; qe=q(eid,"差遣官名。"); qt=q(eid,"唐开元十二年已有判南曹之名"); qs=q(eid,"北宋沿置。"); qd=q(eid,"主掌选人投下文字的审验，并送流内铨注拟受官之后，发给历子"); qstaff=q(eid,"多由判吏部流内铨事差遣兼，或由判吏部事兼")
    w=writer(eid); en=entity(w,"判吏部南曹事","官职",eid,qe,"辞典明载为差遣官。")
    timepoint(w,en,"唐开元十二年","已有判南曹之名",eid,qt,"差遣官名","建唐代职源节点。")
    song=timepoint(w,en,"北宋","沿置，主掌吏部南曹选人文字审验及历子发给",eid,qs,"差遣官名","建北宋沿置节点。")
    citation(w,"Timepoints",song,eid,qd,"补充职掌。",note="职掌")
    citation(w,"Timepoints",song,eid,qstaff,"补充兼任方式。",note="编制")
    _,office=node(w,"吏部南曹","北宋","机构")
    relationship(w,office,song,"编制隶属",eid,qd,"判吏部南曹事主掌南曹职事。",staff_type="官")
    w.commit()


def entry91():
    eid=91; qe=q(eid,"官司名。"); qt=q(eid,"唐朝已置，掌未入流品之京百司吏人，亦称“小铨”"); qs=q(eid,"北宋沿置，归隶吏部"); qd=q(eid,"掌掌掌在京师百司人吏考试与奏差")
    w=writer(eid); en=entity(w,"流外铨","机构",eid,qe,"切分修复后辞典明载为官司。")
    timepoint(w,en,"唐朝","已置，掌未入流品之京百司吏人",eid,qt,"官司名","建唐代职源节点。")
    song=timepoint(w,en,"北宋","沿置，归隶吏部，掌京师百司人吏考试与奏差",eid,qs,"官司名","建北宋沿置节点。")
    citation(w,"Timepoints",song,eid,qd,"补充职掌；quotation 保留 OCR 原字。",note="职掌；原文 OCR 作‘掌掌掌’")
    oe=w.find_entity("吏部","机构") or entity(w,"吏部","机构",eid,qs,"本条直接记载流外铨归隶吏部。")
    ot=w.find_timepoint(oe,"北宋") or timepoint(w,oe,"北宋","管辖流外铨",eid,qs,"官署名","据隶属事实建承载节点。")
    relationship(w,ot,song,"上下级机构",eid,qs,"北宋流外铨归隶吏部。")
    w.commit()


def entry92():
    eid=92; qe=q(eid,"官司名。"); qt=q(eid,"五代后唐同光二年（924）已见置"); qs=q(eid,"宋沿置。"); qd=q(eid,"依州县升降则例，定幕职州县官俸料钱，即依州、县户口之多少，确定上、下、紧、望之等，然后依等定俸"); qstaff=q(eid,"由判吏部事兼领，人吏若干")
    w=writer(eid); en=entity(w,"吏部格式司","机构",eid,qe,"辞典明载为官司。")
    timepoint(w,en,"五代后唐同光二年","已见设置",eid,qt,"官司名","建五代职源节点。")
    song=timepoint(w,en,"宋代","沿置，依州县升降则例确定幕职州县官俸料",eid,qs,"官司名","建宋代沿置节点。")
    citation(w,"Timepoints",song,eid,qd,"补充职掌。",note="职掌")
    post=entity(w,"判吏部事","官职",eid,qstaff,"本条明确由判吏部事兼领。")
    pt=w.find_timepoint(post,"宋代") or timepoint(w,post,"宋代","兼领吏部格式司",eid,qstaff,"差遣官名","建兼领节点。")
    relationship(w,song,pt,"编制隶属",eid,qstaff,"吏部格式司由判吏部事兼领。",staff_type="官")
    w.commit()


def entry93():
    eid=93; qe=q(eid,"官司名。"); qt=q(eid,"唐太和九年（835）已见置，为收藏奏钞之所"); qs=q(eid,"宋沿置。"); qd=q(eid,"掌收藏、保管官员（包括选人）任命之制、敕及黄甲、拟官奏状，并出给注拟官吏的签符、优牒关送南曹、格式司或官告院，以及选人废置、改名等事"); qstaff=q(eid,"判吏部甲库事一人，吏额有院子等名目")
    w=writer(eid); en=entity(w,"吏部甲库","机构",eid,qe,"辞典明载为官司。")
    timepoint(w,en,"唐太和九年","已见置，为收藏奏钞之所",eid,qt,"官司名","建唐代职源节点。")
    song=timepoint(w,en,"宋代","沿置，收藏官员任命文书并出给签符、优牒",eid,qs,"官司名","建宋代沿置节点。对职掌只概括原文，不另造关系。")
    citation(w,"Timepoints",song,eid,qd,"补充职掌。",note="职掌")
    post=entity(w,"判吏部甲库事","官职",eid,qstaff,"编制明载此官一人。")
    pt=timepoint(w,post,"宋代","掌吏部甲库事，编制一人",eid,qstaff,"差遣官名","建编制节点。")
    relationship(w,song,pt,"编制隶属",eid,qstaff,"吏部甲库设判库事一人。",staff_quota=1,staff_type="官")
    w.commit()


def entry94():
    eid=94; qe=q(eid,"官司名。"); qt=q(eid,"唐始置，五代沿设"); qs=q(eid,"北宋承唐五代之制。"); qd=q(eid,"专管有关选人犯公、私罪，须毁抹其官告文字，即于内批出毁抹期限，牒送刑部毁抹")
    w=writer(eid); en=entity(w,"废置司","机构",eid,qe,"辞典明载为官司。")
    timepoint(w,en,"唐朝","始置",eid,qt,"官司名","建唐代职源节点。")
    timepoint(w,en,"五代","沿设",eid,qt,"官司名","建五代沿革节点。")
    song=timepoint(w,en,"北宋","承唐五代之制，掌选人犯罪后官告文字毁抹",eid,qs,"官司名","建北宋沿置节点。")
    citation(w,"Timepoints",song,eid,qd,"补充职掌。",note="职掌")
    w.commit()


def entry95():
    eid=95; full=FULL[eid][2].split("\n",1)[0]
    qearly=q(eid,"①北宋前期，审官东院、审官西院、流内铨、三班院之总名。"); qnew=q(eid,"②元丰新制，铨注之法，悉归吏部。于是吏部有四选之法：以审官东院为尚书左选，流内铨为侍郎左选，审官西院为尚书右选，三班院为侍郎右选")
    w=writer(eid); group=entity(w,"铨曹四选","机构",eid,full,"原文明载为四选机构的总名。")
    early=timepoint(w,group,"北宋前期","审官东院、审官西院、流内铨、三班院之总名",eid,qearly,"机构合称","建北宋前期合称节点。")
    new=timepoint(w,group,"北宋元丰新制","铨注悉归吏部，形成尚书、侍郎左、右四选",eid,qnew,"机构合称","建元丰新制节点。")
    west=w.find_entity("审官西院","机构")
    west_time="北宋熙宁三年五月" if west and w.find_timepoint(west,"北宋熙宁三年五月") else "北宋前期"
    three=w.find_entity("三班院","机构")
    three_time="北宋雍熙四年七月" if three and w.find_timepoint(three,"北宋雍熙四年七月") else "北宋前期"
    old_specs=(("审官东院","北宋熙宁三年五月二十八日"),("吏部流内铨","北宋淳化四年五月二十日"),("审官西院",west_time),("三班院",three_time))
    old_nodes={}
    for title,time in old_specs:
        en=w.find_entity(title,"机构") or entity(w,title,"机构",eid,qearly,f"原文列为铨曹四选实例：{title}。")
        tp=w.find_timepoint(en,time) or timepoint(w,en,time,"为铨曹四选之一",eid,qearly,"官司名",f"建{title}实例节点。")
        citation(w,"Timepoints",tp,eid,qearly,f"补充{title}属于四选的证据。")
        relationship(w,early,tp,"统称与实例",eid,qearly,f"铨曹四选包括{title}。")
        old_nodes[title]=tp
    pairs=(("审官东院","吏部尚书左选"),("吏部流内铨","吏部侍郎左选"),("审官西院","吏部尚书右选"),("三班院","吏部侍郎右选"))
    for old,title in pairs:
        en=entity(w,title,"机构",eid,qnew,f"元丰四选明列{title}。")
        # 审官东院一路在第96条会由“元丰新制”细化为“元丰五年五月”；
        # 重跑时优先复用已细化节点，避免重新制造泛化节点。
        target_refined = "北宋元丰五年五月" if old in ("审官东院","吏部流内铨","审官西院","三班院") else None
        old_refined = {
            "审官东院":"北宋元丰五年五月",
            "吏部流内铨":"北宋元丰三年八月十四日",
            "审官西院":"北宋元丰五年五月",
            "三班院":"北宋元丰五年五月",
        }.get(old)
        tp=(w.find_timepoint(en,target_refined) if target_refined else None) or w.find_timepoint(en,"北宋元丰新制")
        tp=tp or timepoint(w,en,"北宋元丰新制",f"由{old}改置",eid,qnew,"官司名",f"建{title}新制节点。")
        citation(w,"Timepoints",tp,eid,qnew,f"{title}属于元丰吏部四选。")
        relationship(w,new,tp,"统称与实例",eid,qnew,f"元丰吏部四选包括{title}。")
        old_en=w.find_entity(old,"机构"); assert old_en
        terminal=(w.find_timepoint(old_en,old_refined) if old_refined else None) or w.find_timepoint(old_en,"北宋元丰新制")
        terminal=terminal or timepoint(w,old_en,"北宋元丰新制",f"改为{title}",eid,qnew,"官司名",f"建{old}终结改制节点。")
        citation(w,"Timepoints",terminal,eid,qnew,f"{old}在元丰新制中改为{title}。")
        # “吏部流内铨”条另有元丰三年先改“尚书吏部”、五年再改
        # “吏部侍郎左选”的精确两段沿革；细化后不重建概括性直连边。
        if not (old == "吏部流内铨" and w.find_entity("尚书吏部","机构")):
            relationship(w,terminal,tp,"前后演变",eid,qnew,f"元丰新制以{old}为{title}。")
    w.commit()


def entry96():
    eid=96; text=FULL[eid][2].split("\n",1)[0]; qstart=q(eid,"北宋神宗熙宁三年五月二十八日，改审官院为审官东院。"); qend=q(eid,"元丰五年五月改审官东院为吏部尚书左选"); qstaff=q(eid,"审官东院设知院事官二人、主簿二员")
    w=writer(eid); en,st=node(w,"审官东院","北宋熙宁三年五月二十八日","机构")
    citation(w,"Timepoints",st,eid,qstart,"本条直接证明审官东院改置时间。")
    citation(w,"Timepoints",st,eid,text,"补充职掌沿用审官院及编制。",note="职掌与编制")
    for title,quota,time in (("知审官东院事",2,"北宋熙宁三年五月二十八日"),("审官东院主簿",2,"北宋熙宁三年五月")):
        pe=w.find_entity(title,"官职") or entity(w,title,"官职",eid,qstaff,f"编制明列{title}。")
        pt=w.find_timepoint(pe,time) or timepoint(w,pe,time,f"审官东院设{quota}员",eid,qstaff,"差遣官名","建编制节点。")
        relationship(w,st,pt,"编制隶属",eid,qstaff,f"审官东院设{title}{quota}员。",staff_quota=quota,staff_type="官")
    end=refine_time(w,en,"北宋元丰新制","北宋元丰五年五月","改为吏部尚书左选",qend,"第96条给出精确月份。")
    citation(w,"Timepoints",end,eid,qend,"为审官东院终结改制提供精确月份。")
    oe=w.find_entity("吏部尚书左选","机构") or entity(w,"吏部尚书左选","机构",eid,qend,"本条明确后继机构。")
    ot=refine_time(w,oe,"北宋元丰新制","北宋元丰五年五月","由审官东院改置",qend,"第96条给出精确月份。")
    citation(w,"Timepoints",ot,eid,qend,"为吏部尚书左选改置提供精确月份。")
    relationship(w,end,ot,"前后演变",eid,qend,"审官东院改为吏部尚书左选。")
    w.commit()


def entry97():
    eid=97; text=FULL[eid][2].split("\n",1)[0]; w=writer(eid)
    en=w.find_entity("知审官东院事","官职") or entity(w,"知审官东院事","官职",eid,text,"辞典明载为差遣官。")
    tp=timepoint(w,en,"北宋熙宁三年五月二十八日","始置，掌文臣京朝官磨勘、差遣事，编制二员",eid,text,"差遣官名","建始置、职掌及编制节点。")
    _,office=node(w,"审官东院","北宋熙宁三年五月二十八日","机构")
    relationship(w,office,tp,"编制隶属",eid,text,"审官东院设知院事二员。",staff_quota=2,staff_type="官")
    w.commit()


def entry98():
    eid=98; text=FULL[eid][2].split("\n",1)[0]; w=writer(eid)
    en=w.find_entity("审官东院主簿","官职") or entity(w,"审官东院主簿","官职",eid,text,"辞典明载为差遣官。")
    tp=w.find_timepoint(en,"北宋熙宁三年五月") or timepoint(w,en,"北宋熙宁三年五月","始置，掌本院文书勾稽事，编制二员",eid,text,"差遣官名","建始置、职掌及编制节点。")
    citation(w,"Timepoints",tp,eid,text,"本条直接证明主簿始置、职掌和员额。")
    _,office=node(w,"审官东院","北宋熙宁三年五月二十八日","机构")
    relationship(w,office,tp,"编制隶属",eid,text,"审官东院设主簿二员。",staff_quota=2,staff_type="官")
    w.commit()


def main():
    entry89(); entry90(); entry91(); entry92(); entry93()
    entry94(); entry95(); entry96(); entry97(); entry98()


if __name__ == "__main__":
    main()
