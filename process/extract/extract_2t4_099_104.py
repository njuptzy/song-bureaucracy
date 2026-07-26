#!/usr/bin/env python3
"""提取 chapter2t4 第 99–104 条：审官西院、吏部流内铨、三班院。"""
import json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db")


def load(eid):
    with sqlite3.connect(DICT_DB) as c:
        row=c.execute("SELECT title,page,text,fields FROM chapter2t4 WHERE id=?",(eid,)).fetchone()
    full=(row[2] or "")+"\n"+"\n".join(str(v) for k,v in json.loads(row[3] or "{}").items() if not k.startswith("_"))
    return row[0],row[1],full


FULL={i:load(i) for i in range(99,105)}


def q(eid,text):
    assert text in FULL[eid][2],f"#{eid} 不含：{text}"
    return text


def writer(eid): return EntryWriter(ENTRY_DB,FULL[eid][0],FULL[eid][1])
def cite(eid): return f"《宋代官制辞典》第{FULL[eid][1]}页“{FULL[eid][0]}”条"


def ac(w,table,rid,eid,quote,decision,**kw):
    return w.citation(table,rid,cite(eid),quote,decision,**kw)


def ent(w,title,typ,eid,quote,decision):
    return w.entity(title,typ,decision,quotation=quote)


def tp(w,entity,time,event,eid,quote,category,decision,**kw):
    rid=w.timepoint(entity,time,event,decision,quote,attr_category=category,**kw)
    ac(w,"Timepoints",rid,eid,quote,decision)
    return rid


def rel(w,s,o,kind,eid,quote,decision,**kw):
    rid=w.relationship(s,o,kind,decision,quote,**kw)
    ac(w,"Relationships",rid,eid,quote,decision)
    return rid


def node(w,title,time,typ=None):
    entity=w.find_entity(title,typ); assert entity,f"缺实体 {title}"
    rid=w.find_timepoint(entity,time); assert rid,f"{title} 缺 time={time}"
    return entity,rid


def refine(w,entity,old_time,new_time,event,quote,decision):
    exact=w.find_timepoint(entity,new_time)
    if exact: return exact
    rid=w.find_timepoint(entity,old_time); assert rid,f"实体 {entity} 缺 {old_time}"
    w.conn.execute("UPDATE Timepoints SET time=?,event=?,quotation=? WHERE id=?",(new_time,event,quote,rid))
    w._br("Timepoints",rid,f"时间细化 {old_time}->{new_time}：{decision}")
    return rid


def rechain(w,entity,ids,decision):
    for i,rid in enumerate(ids):
        w.relink(rid,decision,prev_id=ids[i-1] if i else None,succ_id=ids[i+1] if i+1<len(ids) else None)


def canonical_entity(w,short,full,eid,quote):
    target=w.find_entity(full,"机构")
    source=w.find_entity(short,"机构")
    if target:
        assert not source or source==target,f"{short}/{full} 同时存在"
        return target
    assert source,f"缺待规范实体 {short}"
    w.conn.execute("UPDATE Entities SET title=?,quotation=? WHERE id=?",(full,quote,source))
    w._br("Entities",source,f"遇正式词条后将简称实体“{short}”规范为“{full}”，不另建别称实体")
    return source


def remove_direct_relation(w,subject_title,object_title,target_tp,eid,decision):
    rows=w.conn.execute("""SELECT r.id FROM Relationships r
      JOIN Timepoints st ON st.id=r.subject_id JOIN Entities se ON se.id=st.entity_id
      JOIN Timepoints ot ON ot.id=r.object_id JOIN Entities oe ON oe.id=ot.entity_id
      WHERE se.title=? AND oe.title=? AND r.relation_type='前后演变'""",(subject_title,object_title)).fetchall()
    for (rid,) in rows:
        citations=w.conn.execute("SELECT id,citation,quotation FROM Citations WHERE target_table='Relationships' AND target_id=?",(rid,)).fetchall()
        for cid,citation,quotation in citations:
            duplicate=w.conn.execute("SELECT id FROM Citations WHERE target_table='Timepoints' AND target_id=? AND citation=? AND quotation=?",(target_tp,citation,quotation)).fetchone()
            if duplicate:
                w.conn.execute("DELETE FROM BuildRecords WHERE target_table='Citations' AND target_id=?",(cid,))
                w.conn.execute("DELETE FROM Citations WHERE id=?",(cid,))
            else:
                w.conn.execute("UPDATE Citations SET target_table='Timepoints',target_id=? WHERE id=?",(target_tp,cid))
                w._br("Citations",cid,decision)
        w.conn.execute("DELETE FROM BuildRecords WHERE target_table='Relationships' AND target_id=?",(rid,))
        w.conn.execute("DELETE FROM Relationships WHERE id=?",(rid,))


def entry99():
    eid=99; qe=q(eid,"官司名。"); qs=q(eid,"北宋神宗熙宁三年五月始置"); qend=q(eid,"元丰五年五月行新官制，改为尚书省吏部尚书右选"); qd=q(eid,"掌阁门祗候、大使臣以上武官磨勘、差遣"); qstaff=q(eid,"知院官二人，主簿二人")
    w=writer(eid); office=w.find_entity("审官西院","机构") or ent(w,"审官西院","机构",eid,qe,"辞典明载为官司。")
    start=refine(w,office,"北宋前期","北宋熙宁三年五月","始置，掌武官磨勘、差遣",qs,"第99条给出始置月份")
    ac(w,"Timepoints",start,eid,qs,"为审官西院始置提供证据"); ac(w,"Timepoints",start,eid,qd,"补充职掌",note="职掌"); ac(w,"Timepoints",start,eid,qstaff,"补充编制",note="知院官、主簿各二人")
    end=refine(w,office,"北宋元丰新制","北宋元丰五年五月","改为吏部尚书右选",qend,"第99条给出终结月份")
    ac(w,"Timepoints",end,eid,qend,"为审官西院改制提供证据")
    target=w.find_entity("吏部尚书右选","机构") or ent(w,"吏部尚书右选","机构",eid,qend,"本条明确后继机构。")
    target_tp=refine(w,target,"北宋元丰新制","北宋元丰五年五月","由审官西院改置",qend,"第99条给出改置月份")
    ac(w,"Timepoints",target_tp,eid,qend,"为吏部尚书右选改置提供证据")
    rel(w,end,target_tp,"前后演变",eid,qend,"审官西院改为吏部尚书右选。")
    rechain(w,office,[start,end],"按熙宁始置、元丰终结排序")
    w.commit()


def add_staff_evidence(relation,quote,decision):
    w=writer(99); ac(w,"Relationships",relation,99,quote,decision); w.commit()


def entry100():
    eid=100; text=FULL[eid][2].split("\n",1)[0]; w=writer(eid)
    official=w.find_entity("知审官西院事","官职") or ent(w,"知审官西院事","官职",eid,text,"辞典明载为差遣官。")
    point=tp(w,official,"北宋熙宁三年五月十八日","始置，掌武官磨勘与常程差遣，编制二人",eid,text,"差遣官名","建始置、职掌及编制节点。")
    _,office=node(w,"审官西院","北宋熙宁三年五月","机构")
    relation=rel(w,office,point,"编制隶属",eid,text,"审官西院设知院事二人。",staff_quota=2,staff_type="官")
    w.commit(); add_staff_evidence(relation,q(99,"知院官二人，主簿二人"),"补充审官西院编制证据")


def entry101():
    eid=101; text=FULL[eid][2].split("\n",1)[0]; w=writer(eid)
    official=w.find_entity("审官西院主簿","官职") or ent(w,"审官西院主簿","官职",eid,text,"辞典明载为差遣官。")
    start=tp(w,official,"北宋熙宁三年六月","始置，掌本院簿书勾稽事，编制二员",eid,text,"差遣官名","建始置、职掌及编制节点。")
    later=tp(w,official,"北宋熙宁四年十一月","减为一员",eid,text,"差遣官名","建员额变化节点。")
    _,office=node(w,"审官西院","北宋熙宁三年五月","机构")
    relation=rel(w,office,start,"编制隶属",eid,text,"审官西院初设主簿二员。",staff_quota=2,staff_type="官")
    rel(w,office,later,"编制隶属",eid,text,"熙宁四年后审官西院主簿一员。",staff_quota=1,staff_type="官")
    w.commit(); add_staff_evidence(relation,q(99,"知院官二人，主簿二人"),"补充审官西院初设主簿二人的证据")


def entry102():
    eid=102; qe=q(eid,"官司名。"); qstart=q(eid,"其时在建隆三年。"); qname=q(eid,"元丰三年八月十四日，改名为尚书吏部"); qend=q(eid,"五年五月，元丰新制改为吏部侍郎左选"); qd=q(eid,"初，主管选人常调；淳化四年五月考课院并入后，并掌选人奏举与考核"); qstaff=q(eid,"判流内铨事二人，令史十一人")
    w=writer(eid); office=canonical_entity(w,"流内铨","吏部流内铨",eid,qe)
    start=w.find_timepoint(office,"北宋建隆三年") or tp(w,office,"北宋建隆三年","代吏部尚书铨掌选人常调事",eid,qstart,"官司名","建流内铨始置节点。",chain="head")
    ac(w,"Timepoints",start,eid,qd,"补充初掌选人常调",note="职掌")
    _,kaoke=node(w,"吏部流内铨","北宋淳化四年五月二十日","机构"); ac(w,"Timepoints",kaoke,eid,qd,"补充考课院并入后兼掌奏举与考核",note="职掌变化")
    terminal=refine(w,office,"北宋元丰新制","北宋元丰三年八月十四日","改名尚书吏部",qname,"细化首次改名时间")
    ac(w,"Timepoints",terminal,eid,qname,"为改名尚书吏部提供证据")
    shang=ent(w,"尚书吏部","机构",eid,qname,"本条明确元丰三年后继机构。")
    shang_start=tp(w,shang,"北宋元丰三年八月十四日","由吏部流内铨改名",eid,qname,"官司名","建尚书吏部始置节点。")
    shang_end=tp(w,shang,"北宋元丰五年五月","改为吏部侍郎左选",eid,qend,"官司名","建尚书吏部终结节点。")
    left=w.find_entity("吏部侍郎左选","机构") or ent(w,"吏部侍郎左选","机构",eid,qend,"本条明确后继机构。")
    left_tp=refine(w,left,"北宋元丰新制","北宋元丰五年五月","由尚书吏部改置",qend,"细化新制月份")
    ac(w,"Timepoints",left_tp,eid,qend,"为吏部侍郎左选改置提供证据")
    remove_direct_relation(w,"吏部流内铨","吏部侍郎左选",left_tp,eid,"删除概括性直连边，改由尚书吏部承接两段沿革")
    rel(w,terminal,shang_start,"前后演变",eid,qname,"吏部流内铨改名尚书吏部。")
    rel(w,shang_end,left_tp,"前后演变",eid,qend,"尚书吏部改为吏部侍郎左选。")
    times=("北宋建隆三年","北宋淳化四年五月二十日","北宋熙宁五年七月","北宋元丰三年八月十四日")
    rechain(w,office,[w.find_timepoint(office,t) for t in times],"按建隆始置至元丰三年改名排序")
    ac(w,"Timepoints",start,eid,qstaff,"补充机构编制",note="判流内铨事二人，令史十一人")
    w.commit()


def entry103():
    eid=103; qe=q(eid,"差遣官名。"); qs=q(eid,"北宋太祖乾德元年始置"); qd=q(eid,"主管流内铨，即掌幕职州县官的功过磨勘与差遣注授"); qg=q(eid,"差知杂侍御史以上朝官充"); qstaff=q(eid,"二人")
    w=writer(eid); official=w.find_entity("判吏部流内铨事","官职") or ent(w,"判吏部流内铨事","官职",eid,qe,"辞典明载为差遣官。")
    point=tp(w,official,"北宋乾德元年","始置，主管流内铨，编制二人",eid,qs,"差遣官名","建始置节点。",attr_grade="知杂侍御史以上朝官充")
    ac(w,"Timepoints",point,eid,qd,"补充职掌",note="职掌"); ac(w,"Timepoints",point,eid,qg,"补充充任资格",note="品位"); ac(w,"Timepoints",point,eid,qstaff,"补充员额",note="编制二人")
    _,office=node(w,"吏部流内铨","北宋建隆三年","机构")
    rel(w,office,point,"编制隶属",eid,qs,"吏部流内铨设判铨事二人。",staff_quota=2,staff_type="官")
    w.commit()


def entry104():
    eid=104; text=FULL[eid][2].split("\n",1)[0]; qstart=q(eid,"太宗雍熙四年七月，始于内客省使厅事设三班院机构"); qexpand=q(eid,"淳化二年正月十四日，增左、右侍禁与三班奉职（由殿前承旨改）、三班借职（由借职承旨改）为三班院使臣"); qend=q(eid,"神宗元丰五年行新官制，三班院罢归尚书省吏部，改称吏部侍郎右选"); qtot=q(eid,"宋初，仅三百人，真宗天禧间四千二百余人，英宗治平三年增至八千八百余人，神宗元丰三年总数达一万一千六百九十人"); qstaff=q(eid,"设勾当三班院公事，不定员；熙宁三年七月设主簿二人"); qclerks=q(eid,"有勾押官一人，押司官一人，前行三人，后行十一人"); qcats=q(eid,"三班使臣包括东、西头供奉官，左、右侍禁，左、右班殿直，三班奉职，三班借职")
    w=writer(eid); office=w.find_entity("三班院","机构") or ent(w,"三班院","机构",eid,text,"辞典明载为官司。")
    start=refine(w,office,"北宋前期","北宋雍熙四年七月","始设三班院机构，独立后归隶中书",qstart,"细化始置年月")
    ac(w,"Timepoints",start,eid,text,"补充三班院隶属沿革")
    expand=tp(w,office,"北宋淳化二年正月十四日","扩充三班院使臣类别",eid,qexpand,"官司名","建编制类别变化节点。")
    for title in ("东头供奉官","西头供奉官","左侍禁","右侍禁","左班殿直","右班殿直","三班奉职","三班借职"):
        pe=w.find_entity(title,"官职") or ent(w,title,"官职",eid,qcats,f"三班使臣类别明列{title}。")
        ptp=w.find_timepoint(pe,"北宋淳化二年正月十四日") or tp(w,pe,"北宋淳化二年正月十四日","列为三班院使臣类别",eid,qcats,"武官名","建三班使臣类别节点。")
        rel(w,expand,ptp,"编制隶属",eid,qcats,f"三班院使臣包括{title}。",staff_type="官")
    totals=(("宋初","三班使臣约三百人"),("北宋天禧间","三班使臣四千二百余人"),("北宋治平三年","三班使臣八千八百余人"),("北宋元丰三年","三班使臣一万一千六百九十人"))
    total_nodes=[]
    for time,event in totals:
        if time=="宋初":
            ac(w,"Timepoints",start,eid,qtot,"补充宋初使臣总数",note="编制总数约三百人"); continue
        total_nodes.append(tp(w,office,time,event,eid,qtot,"官司名","建使臣总数变化节点。"))
    mainpost=ent(w,"勾当三班院公事","官职",eid,qstaff,"本条编制明列此差遣。")
    main_tp=tp(w,mainpost,"北宋雍熙四年七月","掌三班院公事，不定员",eid,qstaff,"差遣官名","建无定员编制节点。")
    rel(w,start,main_tp,"编制隶属",eid,qstaff,"三班院设勾当公事，不定员。",staff_type="官")
    staff_change=tp(w,office,"北宋熙宁三年七月","始设主簿二人",eid,qstaff,"官司名","建编制变化节点。")
    clerk=ent(w,"三班院主簿","官职",eid,qstaff,"本条明载熙宁三年设主簿。")
    clerk_tp=tp(w,clerk,"北宋熙宁三年七月","始置，编制二人",eid,qstaff,"差遣官名","建主簿编制节点。")
    rel(w,staff_change,clerk_tp,"编制隶属",eid,qstaff,"三班院设主簿二人。",staff_quota=2,staff_type="官")
    for title,quota in (("勾押官",1),("押司官",1),("前行",3),("后行",11)):
        pe=w.find_entity(title,"官职") or ent(w,title,"官职",eid,qclerks,f"吏额明列{title}。")
        ptp=w.find_timepoint(pe,"北宋雍熙四年七月") or tp(w,pe,"北宋雍熙四年七月",f"三班院吏额{quota}人",eid,qclerks,"吏职名","建吏额节点。")
        rel(w,start,ptp,"编制隶属",eid,qclerks,f"三班院设{title}{quota}人。",staff_quota=quota,staff_type="吏")
    end=refine(w,office,"北宋元丰新制","北宋元丰五年五月","罢归尚书省吏部，改称吏部侍郎右选",qend,"细化终结月份")
    right=w.find_entity("吏部侍郎右选","机构") or ent(w,"吏部侍郎右选","机构",eid,qend,"本条明确后继机构。")
    right_tp=refine(w,right,"北宋元丰新制","北宋元丰五年五月","由三班院改置",qend,"细化改置月份")
    ac(w,"Timepoints",end,eid,qend,"为三班院终结提供证据"); ac(w,"Timepoints",right_tp,eid,qend,"为侍郎右选改置提供证据")
    rel(w,end,right_tp,"前后演变",eid,qend,"三班院改为吏部侍郎右选。")
    _,central=node(w,"中书门下","宋前期","机构"); rel(w,central,start,"上下级机构",eid,text,"三班院独立置院后归隶中书。")
    ordered=[start,expand,w.find_timepoint(office,"北宋天禧间"),w.find_timepoint(office,"北宋治平三年"),staff_change,w.find_timepoint(office,"北宋元丰三年"),end]
    rechain(w,office,ordered,"按雍熙始置、淳化扩编、历次总数、元丰终结排序")
    w.commit()


def main():
    entry99(); entry100(); entry101(); entry102(); entry103(); entry104()


if __name__=="__main__": main()
