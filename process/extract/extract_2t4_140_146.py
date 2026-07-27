#!/usr/bin/env python3
"""提取 chapter2t4 第 140–146 条：编类圣政所与制置三司条例司。"""
import json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db")

def load(i):
    with sqlite3.connect(DICT_DB) as c: r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return r[0],r[1],(r[2] or "")+"\n"+"\n".join(str(v) for k,v in json.loads(r[3] or "{}").items() if not k.startswith("_"))
FULL={i:load(i) for i in range(140,147)}
def q(i,s): assert s in FULL[i][2],f"#{i} 不含：{s}"; return s
def writer(i): return EntryWriter(ENTRY_DB,FULL[i][0],FULL[i][1])
def cite(i): return f"《宋代官制辞典》第{FULL[i][1]}页“{FULL[i][0]}”条"
def ac(w,t,r,i,quote,d,**kw): return w.citation(t,r,cite(i),quote,d,**kw)
def entity(w,title,typ,i,quote,d): return w.entity(title,typ,d,quotation=quote)
def tp(w,en,time,event,i,quote,cat,d,**kw):
    r=w.timepoint(en,time,event,d,quote,attr_category=cat,**kw); ac(w,"Timepoints",r,i,quote,d); return r
def rel(w,s,o,kind,i,quote,d,**kw):
    r=w.relationship(s,o,kind,d,quote,**kw); ac(w,"Relationships",r,i,quote,d); return r
def node(w,title,time,typ=None):
    en=w.find_entity(title,typ); assert en,f"缺实体 {title}"; r=w.find_timepoint(en,time); assert r,f"{title} 缺 {time}"; return en,r
def rechain(w,ids,d):
    assert all(ids)
    for n,r in enumerate(ids): w.relink(r,d,prev_id=ids[n-1] if n else None,succ_id=ids[n+1] if n+1<len(ids) else None)

def entry140():
    i=140; text=FULL[i][2].split("\n",1)[0]; qstart=q(i,"绍兴三十二年九月十一日，由敕令所改名"); qend=q(i,"隆兴元年五月十九日，并入国史日历所")
    w=writer(i); office=entity(w,"编类圣政所","机构",i,text,"辞典明载为编敕机构。")
    start=tp(w,office,"南宋绍兴三十二年九月十一日","由敕令所改名，编纂大号令、大政事及忠臣义士传记",i,qstart,"编敕机构名","建改名始置节点。")
    ac(w,"Timepoints",start,i,text,"补充完整职掌。",note="职掌")
    end=tp(w,office,"南宋隆兴元年五月十九日","并入国史日历所",i,qend,"编敕机构名","建并入终结节点。")
    source_en=w.find_entity("详定一司敕令所","机构"); source=tp(w,source_en,"南宋绍兴三十二年九月十一日","改为编类圣政所",i,qstart,"编修法令机构名","建同刻演变来源节点。",chain="none")
    successor=entity(w,"国史日历所","机构",i,qend,"本条明确编类圣政所并入的后继机构。")
    successor_tp=tp(w,successor,"南宋隆兴元年五月十九日","编类圣政所并入",i,qend,"官署名","建同刻演变后继节点。")
    rel(w,source,start,"前后演变",i,qstart,"敕令所改名为编类圣政所。")
    rel(w,end,successor_tp,"前后演变",i,qend,"编类圣政所并入国史日历所。")
    order=[w.find_timepoint(source_en,t) for t in ("北宋熙宁间","北宋熙宁三年","北宋熙宁八年九月","北宋徽宗大观时","南宋绍兴五年","南宋绍兴三十二年九月十一日","南宋绍兴末","南宋乾道四年","南宋乾道六年","南宋淳熙十五年")]
    rechain(w,order,"插入绍兴三十二年改名节点并按历史顺序重排"); rechain(w,[start,end],"按始置、并入排序"); w.commit()

def entry141():
    i=141; text=FULL[i][2].split("\n",1)[0]; w=writer(i)
    post=entity(w,"提举编类圣政","官职",i,text,"辞典明载为兼官。")
    point=tp(w,post,"南宋绍兴三十二年九月","始设，由宰相、知枢密院事兼，参知政事兼权",i,text,"兼官名","建始设、充任与职掌节点。")
    _,office=node(w,"编类圣政所","南宋绍兴三十二年九月十一日","机构")
    rel(w,office,point,"编制隶属",i,text,"编类圣政所设提举兼官。",staff_type="官"); w.commit()

def entry142():
    i=142; text=FULL[i][2].split("\n",1)[0]; w=writer(i)
    post=entity(w,"编类圣政检讨官","官职",i,text,"辞典明载为差遣。")
    point=tp(w,post,"南宋绍兴三十二年九月十一日","由秘书省官兼充，掌撰编敕令，编制二员",i,text,"差遣名","依所属机构始置时间建编制节点。")
    _,office=node(w,"编类圣政所","南宋绍兴三十二年九月十一日","机构")
    rel(w,office,point,"编制隶属",i,text,"编类圣政所设检讨官二员。",staff_quota=2,staff_type="官"); w.commit()

def entry143():
    i=143; qname=q(i,"主持变法的临时官署名"); qstart=q(i,"熙宁二年二月二十七日始置"); qend=q(i,"三年五月十五日诏罢，结局在六月以后"); qstaff=q(i,"同制置三司条例司，二员；制置三司条例司检详文字二员或三员；制置三司条例司相度利害官若干")
    w=writer(i); office=entity(w,"制置三司条例司","机构",i,qname,"辞典明载为主持变法的临时官署。")
    start=w.timepoint(office,"北宋熙宁二年二月二十七日","始置，领导财政改革、议行变法","建始置节点。",qstart,attr_category="临时官署名")
    ac(w,"Timepoints",start,i,qname,"补充机构性质。"); ac(w,"Timepoints",start,i,qstaff,"补充属官编制。",note="检详文字二或三员，相度利害官若干")
    ac(w,"Timepoints",start,i,qstart,"总条与主管官条始置日相差十日。",conflict_flag=1,note="本条作二月二十七日；同制置三司条例条作二月十七日")
    end=tp(w,office,"北宋熙宁三年五月十五日","诏罢，结局在六月以后",i,qend,"临时官署名","建罢废节点。")
    for title,quota in (("同制置三司条例",2),("制置三司条例司检详文字",None),("制置三司条例司相度利害官",None)):
        post=entity(w,title,"官职",i,qstaff,f"条例司编制明确列{title}。")
        p=tp(w,post,"北宋熙宁二年二月二十七日","制置三司条例司属官",i,qstaff,"差遣官",f"建{title}编制承载节点。")
        rel(w,start,p,"编制隶属",i,qstaff,f"制置三司条例司设{title}。",staff_quota=quota,staff_type="官")
    rechain(w,[start,end],"按始置、罢废排序"); w.commit()

def entry144():
    i=144; text=FULL[i][2].split("\n",1)[0]; qdate=q(i,"熙宁二年二月十七日始置")
    w=writer(i); en=w.find_entity("同制置三司条例","官职"); old=w.find_timepoint(en,"北宋熙宁二年二月二十七日")
    exact=tp(w,en,"北宋熙宁二年二月十七日","始置，掌领条例司、制订新法、签书公事",i,text,"差遣官","按本专条建立始置节点。",chain="none")
    ac(w,"Timepoints",exact,i,qdate,"与条例司总条日期冲突。",conflict_flag=1,note="本条作二月十七日；条例司总条作二月二十七日")
    office_en,office=node(w,"制置三司条例司","北宋熙宁二年二月二十七日","机构")
    ac(w,"Timepoints",office,i,qdate,"补充主管官条所载异文。",conflict_flag=1,note="主管官条作二月十七日；机构总条作二月二十七日")
    rel(w,office,exact,"编制隶属",i,text,"同制置三司条例掌领本司，初置二员。",staff_quota=2,staff_type="官")
    rechain(w,[exact,old],"保留冲突日期，按十七日、二十七日排序"); w.commit()

def entry145():
    i=145; text=FULL[i][2].split("\n",1)[0]; w=writer(i); en=w.find_entity(FULL[i][0],"官职"); _,point=node(w,FULL[i][0],"北宋熙宁二年二月二十七日","官职")
    ac(w,"Timepoints",point,i,text,"补充参与商议理财、拟订新法的职掌。",note="职掌")
    _,office=node(w,"制置三司条例司","北宋熙宁二年二月二十七日","机构"); rel(w,office,point,"编制隶属",i,text,"检详文字为条例司属官。",staff_type="官"); w.commit()

def entry146():
    i=146; text=FULL[i][2].split("\n",1)[0]; w=writer(i); en=w.find_entity(FULL[i][0],"官职"); _,point=node(w,FULL[i][0],"北宋熙宁二年二月二十七日","官职")
    ac(w,"Timepoints",point,i,text,"补充出使诸路考察新法施行的职掌。",note="职掌")
    _,office=node(w,"制置三司条例司","北宋熙宁二年二月二十七日","机构"); rel(w,office,point,"编制隶属",i,text,"相度利害官为条例司属官。",staff_type="官"); w.commit()

def main():
    entry140(); entry141(); entry142(); entry143(); entry144(); entry145(); entry146()
if __name__=="__main__": main()
