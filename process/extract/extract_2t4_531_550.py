#!/usr/bin/env python3
"""提取 chapter2t4 第531–550条：显谟、徽猷、敷文、焕章、华文阁职。"""
import json,os,sqlite3,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.environ.get("SONG_ENTRY_DB",os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db"))
def load(i):
    with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return {"title":r[0],"page":r[1],"text":r[2] or "","fields":json.loads(r[3] or "{}")}
F={i:load(i) for i in range(531,551)}
def W(i):return EntryWriter(ENTRY_DB,F[i]["title"],F[i]["page"])
def C(i):return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
def entity(w,title,q,d):return w.entity(title,"官职",d,quotation=q)
def cite(w,table,rid,i,q,d,**kw):return w.citation(table,rid,C(i),q,d,**kw)
def tp(w,e,time,event,i,q,d,grade=None,citation_kw=None,**kw):
    t=w.timepoint(e,time,event,d,q,attr_category="阁职名",attr_grade=grade,**kw);cite(w,"Timepoints",t,i,q,d,**(citation_kw or {}));return t
def rel(w,a,b,k,i,q,d):
    r=w.relationship(a,b,k,d,q);cite(w,"Relationships",r,i,q,d);return r
def chain(w,ts,d):
    assert len(ts)==len(set(ts))
    for n,t in enumerate(ts):w.relink(t,d,prev_id=ts[n-1] if n else None,succ_id=ts[n+1] if n+1<len(ts) else None)
def reuse(w,title):
    e=w.find_entity(title,"官职");assert e,title;return e
def generic(w,e):
    t=w.find_timepoint(e,"宋代（未载具体年月）");assert t,e;return t

def specific(i,title,time,grade,event="始置"):
    source=F[i]["fields"]["职源"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=reuse(w,title)
    start=tp(w,e,time,event,i,source,f"建{title}始置节点。",grade,chain="none")
    g=generic(w,e);chain(w,[start,g],f"将分类节点纳入{title}沿革时间链。")
    cite(w,"Timepoints",start,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",start,i,rank,"补证品位。",note="品位")
    w.commit()

def entry531_533():
    i=531;source=F[i]["fields"]["职源"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=reuse(w,F[i]["title"])
    first=tp(w,e,"北宋建中靖国元年二月九日","始置，原文称初以熙明阁学士为名",i,source,"建显谟阁直学士初置节点；不据省漏字另造前身实体。","从三品",chain="none")
    named=tp(w,e,"北宋崇宁元年十一月十七日以前","已称显谟阁直学士",i,source,"建显谟阁直学士定名节点。","从三品",chain="none")
    g=generic(w,e);chain(w,[first,named,g],"连接显谟阁直学士初置、定名与分类节点。")
    cite(w,"Timepoints",named,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",named,i,rank,"补证品位。",note="品位")
    w.commit()
    i=532;source=F[i]["fields"]["职源"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i)
    pe=entity(w,"熙明阁待制",source,"原文明载显谟阁待制初名熙明阁待制。")
    p0=tp(w,pe,"北宋建中靖国元年二月九日","始置",i,source,"建熙明阁待制始置节点。","从四品",chain="none")
    p1=tp(w,pe,"北宋崇宁元年十一月十七日以前","改称显谟阁待制",i,source,"建熙明阁待制改名节点。","从四品",chain="none")
    chain(w,[p0,p1],"连接熙明阁待制置改节点。")
    e=reuse(w,F[i]["title"]);start=tp(w,e,"北宋崇宁元年十一月十七日以前","由熙明阁待制改称",i,source,"建显谟阁待制定名节点。","从四品",chain="none")
    g=generic(w,e);chain(w,[start,g],"将分类节点纳入显谟阁待制沿革时间链。")
    cite(w,"Timepoints",start,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",start,i,rank,"补证品位。",note="品位")
    rel(w,p1,start,"前后演变",i,source,"熙明阁待制改称显谟阁待制。")
    w.commit()
    specific(533,"直显谟阁","北宋政和六年九月十七日","从七品")

def common_name(i,name,titles):
    z=F[i]["text"];w=W(i);e=entity(w,name,z,f"本条明载{name}为同阁四种职名共同省称。")
    g=tp(w,e,"宋代（未载具体年月）",f"{name}阁学士、直学士、待制、直阁共同省称",i,z,f"建{name}共同省称节点。")
    for title in titles:
        ie=reuse(w,title);it=generic(w,ie);rel(w,g,it,"统称与实例",i,z,f"{title}可省称{name}。")
    w.commit()

def entry534_543():
    specific(534,"徽猷阁学士","北宋大观二年二月十三日","正三品")
    specific(535,"徽猷阁直学士","北宋大观二年二月十三日","从三品")
    specific(536,"徽猷阁待制","北宋大观二年二月十三日","从四品")
    i=537;source=F[i]["fields"]["职源"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=reuse(w,"直徽猷阁")
    start=tp(w,e,"北宋政和元年九月十七日","始置",i,source,"建直徽猷阁始置节点。","从七品",citation_kw={"conflict_flag":1,"note":"第538条另记政和六年增置直阁。"},chain="none")
    g=generic(w,e);chain(w,[start,g],"将分类节点纳入直徽猷阁沿革时间链。")
    cite(w,"Timepoints",start,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",start,i,rank,"补证品位。",note="品位")
    w.commit()
    i=538;z=F[i]["text"];w=W(i);e=reuse(w,"直徽猷阁")
    later=tp(w,e,"北宋政和六年九月十七日","本条另记增置直阁",i,z,"保留徽猷阁直阁始置异说。","从七品",citation_kw={"conflict_flag":1,"note":"第537条另记政和元年九月十七日始置。"},chain="none")
    start=w.find_timepoint(e,"北宋政和元年九月十七日");g=generic(w,e);chain(w,[start,g,later],"并列保留直徽猷阁两种始置时间。")
    w.commit()
    common_name(538,"徽猷",("徽猷阁学士","徽猷阁直学士","徽猷阁待制","直徽猷阁"))
    specific(539,"敷文阁学士","南宋绍兴十年五月十一日","正三品")
    specific(540,"敷文阁直学士","南宋绍兴十年五月十一日","从三品")
    specific(541,"敷文阁待制","南宋绍兴十年五月十一日","从四品")
    specific(542,"直敷文阁","南宋绍兴十年五月十一日","从七品")
    common_name(543,"敷文",("敷文阁学士","敷文阁直学士","敷文阁待制","直敷文阁"))

def entry544_550():
    for i,title,grade in ((544,"焕章阁学士","正三品"),(545,"焕章阁直学士","从三品"),(546,"焕章阁待制","从四品"),(547,"直焕章阁","从七品")):
        specific(i,title,"南宋淳熙十五年十一月九日",grade)
    for i,title,grade in ((548,"华文阁学士","正三品"),(549,"华文阁直学士","从三品"),(550,"华文阁待制","从四品")):
        specific(i,title,"南宋庆元二年五月十五日",grade)

def main():entry531_533();entry534_543();entry544_550()
if __name__=="__main__":main()
