#!/usr/bin/env python3
"""提取重建后 chapter2t4 第511–530条（跳过四个无正文占位）：直阁及龙图、天章、宝文阁职。"""
import json,os,sqlite3,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.environ.get("SONG_ENTRY_DB",os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db"))
def load(i):
    with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return {"title":r[0],"page":r[1],"text":r[2] or "","fields":json.loads(r[3] or "{}")}
F={i:load(i) for i in range(511,531)}
def W(i):return EntryWriter(ENTRY_DB,F[i]["title"],F[i]["page"])
def C(i):return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
def entity(w,title,typ,q,d):return w.entity(title,typ,d,quotation=q)
def cite(w,table,rid,i,q,d,**kw):return w.citation(table,rid,C(i),q,d,**kw)
def tp(w,e,time,event,i,q,cat,d,**kw):
    t=w.timepoint(e,time,event,d,q,attr_category=cat,**kw);cite(w,"Timepoints",t,i,q,d);return t
def rel(w,a,b,k,i,q,d,**kw):
    r=w.relationship(a,b,k,d,q,**kw);cite(w,"Relationships",r,i,q,d);return r
def chain(w,ts,d):
    assert len(ts)==len(set(ts))
    for n,t in enumerate(ts):w.relink(t,d,prev_id=ts[n-1] if n else None,succ_id=ts[n+1] if n+1<len(ts) else None)
def reuse(w,title):
    e=w.find_entity(title,"官职");assert e,title;return e
def generic(w,e):
    t=w.find_timepoint(e,"宋代（未载具体年月）");assert t,e;return t

def entry511():
    i=511;z=F[i]["text"];source=F[i]["fields"]["职源"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i)
    e=entity(w,"直阁","官职",z,"本条明载直阁为诸直阁职名总称。")
    first=tp(w,e,"北宋端拱元年五月","直秘阁始置，为诸直阁最早者",i,source,"阁职统称","建直阁最早设置节点。",chain="none")
    g=tp(w,e,"宋代（未载具体年月）","诸直阁职名总称",i,z,"阁职统称","建直阁统称节点。",chain="none")
    last=tp(w,e,"南宋咸淳元年六月","直显文阁始置，为诸直阁最晚者",i,source,"阁职统称","建直阁最晚设置节点。",chain="none")
    chain(w,[first,g,last],"连接直阁设置范围与统称节点。")
    cite(w,"Timepoints",g,i,duty,"补证直阁贴职功能。",note="职能");cite(w,"Timepoints",g,i,rank,"补证直阁分等品位。",note="品位")
    for title in ("直龙图阁","直天章阁","直宝文阁","直显谟阁","直徽猷阁","直敷文阁","直焕章阁","直华文阁","直宝谟阁","直宝章阁","直显文阁","直秘阁"):
        ie=w.find_entity(title,"官职") or entity(w,title,"官职",z,f"本条将{title}列为直阁实例。")
        it=w.find_timepoint(ie,"宋代（未载具体年月）") or tp(w,ie,"宋代（未载具体年月）","直阁职名",i,z,"阁职名",f"建{title}实例节点。")
        rel(w,g,it,"统称与实例",i,z,f"{title}为直阁实例。")
    w.commit()

def specific(i,title,start_time,grade,end_time=None,end_event=None,source_key="职源",category="阁职名"):
    z=F[i]["text"];source=F[i]["fields"][source_key];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=reuse(w,title)
    start=tp(w,e,start_time,"始置",i,source,category,f"建{title}始置节点。",chain="none",attr_grade=grade)
    g=generic(w,e)
    nodes=[start,g]
    if end_time:
        end=tp(w,e,end_time,end_event,i,source,category,f"建{title}{end_event}节点。",chain="none",attr_grade=grade);nodes.append(end)
    chain(w,nodes,f"将分类节点纳入{title}沿革时间链。")
    cite(w,"Timepoints",start,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",start,i,rank,"补证品位。",note="品位")
    w.commit()

def entry512_515():
    specific(512,"龙图阁学士","北宋大中祥符三年七月十九日","正三品")
    specific(513,"龙图阁直学士","北宋景德四年八月二十四日","从三品")
    specific(514,"龙图阁待制","北宋景德元年十月二十九日","从四品")
    specific(515,"直龙图阁","北宋大中祥符九年十月二十一日","正七品")

def entry519_524():
    specific(519,"天章阁学士","北宋庆历七年八月十六日","正三品","南宋绍兴二十一年三月十九日以后","不复作为带职","职源与沿革")
    specific(520,"天章阁直学士","北宋庆历七年八月十六日","从三品","南宋绍兴二十一年三月十九日以后","不复作为带职","职源与沿革")
    specific(522,"天章阁待制","北宋天圣八年十月二十二日","从四品","南宋绍兴二十一年三月十九日以后","不复作为带职","职源与沿革")
    specific(523,"直天章阁","北宋政和六年九月十七日","正七品")
    i=524;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职掌"];rank=F[i]["fields"]["官品"];comp=F[i]["fields"]["编制"];w=W(i)
    e=entity(w,F[i]["title"],"官职",z,"本条明载天章阁侍讲为经筵官。")
    a=tp(w,e,"北宋景祐四年三月一日","始置，为皇帝进讲经术",i,h,"经筵官","建天章阁侍讲始置节点。",chain="none")
    b=tp(w,e,"北宋仁宗朝以后","不复置",i,h,"经筵官","建天章阁侍讲停置节点。",chain="none")
    chain(w,[a,b],"连接天章阁侍讲置罢节点。")
    cite(w,"Timepoints",a,i,duty,"补证进讲职掌。",note="职掌");cite(w,"Timepoints",a,i,rank,"补证官品班位。",note="官品")
    cite(w,"Timepoints",a,i,comp,"补证初置三人。",note="编制")
    w.commit()

def entry525_530():
    specific(525,"宝文阁学士","北宋治平四年五月二十八日","正三品")
    specific(526,"宝文阁直学士","北宋治平四年五月二十八日","从三品")
    specific(527,"宝文阁待制","北宋治平四年五月二十八日","从四品")
    specific(528,"直宝文阁","北宋政和六年九月十七日","正七品")
    i=529;z=F[i]["text"];w=W(i);e=entity(w,"宝文","官职",z,"本条明载宝文为四种宝文阁职名共同省称。")
    g=tp(w,e,"宋代（未载具体年月）","宝文阁学士、直学士、待制、直阁共同省称",i,z,"阁职共同省称","建宝文共同省称节点。")
    for title in ("宝文阁学士","宝文阁直学士","宝文阁待制","直宝文阁"):
        ie=reuse(w,title);it=generic(w,ie)
        rel(w,g,it,"统称与实例",i,z,f"{title}可省称宝文。")
    w.commit()
    i=530;z=F[i]["text"];source=F[i]["fields"]["职源"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i)
    pred=entity(w,"熙明阁学士","官职",source,"原文明载显谟阁学士初名熙明阁学士。")
    p0=tp(w,pred,"北宋建中靖国元年二月九日","始置",i,source,"阁职名","建熙明阁学士始置节点。",chain="none",attr_grade="正三品")
    p1=tp(w,pred,"北宋崇宁元年十一月十七日以前","阁名复改显谟阁，职名随改",i,source,"阁职名","建熙明阁学士改名节点。",chain="none",attr_grade="正三品")
    chain(w,[p0,p1],"连接熙明阁学士始置与改名节点。")
    e=reuse(w,"显谟阁学士")
    start=tp(w,e,"北宋崇宁元年十一月十七日以前","由熙明阁学士改称",i,source,"阁职名","建显谟阁学士改称节点。",chain="none",attr_grade="正三品")
    g=generic(w,e);chain(w,[start,g],"将分类节点纳入显谟阁学士沿革时间链。")
    cite(w,"Timepoints",start,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",start,i,rank,"补证品位。",note="品位")
    rel(w,p1,start,"前后演变",i,source,"熙明阁学士改称显谟阁学士。")
    w.commit()

def main():entry511();entry512_515();entry519_524();entry525_530()
if __name__=="__main__":main()
