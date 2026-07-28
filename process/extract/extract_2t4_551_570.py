#!/usr/bin/env python3
"""提取 chapter2t4 第551–570条：后期阁职、三馆秘阁与馆职。"""
import json,os,sqlite3,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.environ.get("SONG_ENTRY_DB",os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db"))
def load(i):
    with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return {"title":r[0],"page":r[1],"text":r[2] or "","fields":json.loads(r[3] or "{}")}
F={i:load(i) for i in range(551,571)}
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
def reuse(w,title,typ="官职"):
    e=w.find_entity(title,typ);assert e,title;return e
def generic(w,e):
    t=w.find_timepoint(e,"宋代（未载具体年月）");assert t,e;return t

def specific(i,title,time,grade=None):
    source=F[i]["fields"]["职源"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=reuse(w,title)
    start=tp(w,e,time,"始置",i,source,"阁职名",f"建{title}始置节点。",chain="none",attr_grade=grade)
    g=generic(w,e);chain(w,[start,g],f"将分类节点纳入{title}沿革时间链。")
    cite(w,"Timepoints",start,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",start,i,rank,"补证品位。",note="品位")
    w.commit()

def entry551_564():
    specific(551,"直华文阁","南宋庆元二年五月十五日","从七品")
    for i,title in ((552,"宝谟阁学士"),(553,"宝谟阁直学士"),(554,"宝谟阁待制"),(555,"直宝谟阁")):
        specific(i,title,"南宋嘉泰二年八月十二日")
    for i,title in ((556,"宝章阁学士"),(557,"宝章阁直学士"),(558,"宝章阁待制"),(559,"直宝章阁")):
        specific(i,title,"南宋宝庆二年十月二日")
    i=560;z=F[i]["text"];w=W(i);e=entity(w,"宝章阁","官职",z,"本条明载宝章、宝章阁为四种宝章阁职名共同省称。")
    g=tp(w,e,"南宋","宝章阁学士、直学士、待制、直阁共同省称",i,z,"阁职共同省称","建宝章阁共同省称节点。")
    for title in ("宝章阁学士","宝章阁直学士","宝章阁待制","直宝章阁"):
        ie=reuse(w,title);rel(w,g,generic(w,ie),"统称与实例",i,z,f"{title}可省称宝章或宝章阁。")
    w.commit()
    for i,title in ((561,"显文阁学士"),(562,"显文阁直学士"),(563,"显文阁待制"),(564,"直显文阁")):
        specific(i,title,"南宋咸淳元年六月十八日")

def member(w,i,parent,title,time,q):
    e=w.find_entity(title,"机构") or entity(w,title,"机构",q,f"第{i}条将{title}列为馆阁机构实例。")
    t=w.find_timepoint(e,time) or tp(w,e,time,"三馆秘阁成员机构",i,q,"文馆机构",f"建{title}成员节点。")
    rel(w,parent,t,"统称与实例",i,q,f"{title}为三馆秘阁成员实例。")
    return e,t

def entry565():
    i=565;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];comp=F[i]["fields"]["编制"];w=W(i)
    e=entity(w,"三馆秘阁","机构",z,"本条明载三馆秘阁为昭文馆、史馆、集贤院、秘阁总名。")
    song=tp(w,e,"宋初","沿唐五代制置昭文馆、史馆、集贤院三馆",i,h,"文馆机构统称","建宋初三馆节点。",chain="none")
    rebuild=tp(w,e,"北宋太平兴国三年","新建三馆，通称崇文院",i,h,"文馆机构统称","建新建三馆节点。",chain="none")
    four=tp(w,e,"北宋端拱元年五月","秘阁建于崇文院内，三馆秘阁并列",i,h,"文馆机构统称","建三馆秘阁并列节点。",chain="none")
    split=tp(w,e,"北宋大中祥符八年至天圣九年十一月","三馆徙崇文外院，与秘阁分居，后复合一",i,h,"文馆机构统称","建三馆秘阁分合节点。",chain="none")
    reform=tp(w,e,"北宋元丰五年四月","以崇文院为秘书省",i,h,"文馆机构统称","建元丰改制节点。",chain="none")
    chain(w,[song,rebuild,four,split,reform],"连接三馆秘阁沿革时间链。")
    cite(w,"Timepoints",four,i,duty,"补证典书育才职能。",note="职能");cite(w,"Timepoints",four,i,comp,"补证四局馆职编制。",note="编制")
    for title in ("昭文馆","史馆","集贤院","秘阁"):member(w,i,four,title,"北宋端拱元年五月",z)
    w.commit()

def office_instance(w,i,parent,title,time,q,category="馆职"):
    e=w.find_entity(title,"官职") or entity(w,title,"官职",q,f"第{i}条将{title}列为馆职实例。")
    t=w.find_timepoint(e,time) or tp(w,e,time,"馆职实例",i,q,category,f"建{title}馆职实例节点。")
    rel(w,parent,t,"统称与实例",i,q,f"{title}为馆职实例。")
    return e,t

def entry566():
    i=566;z=F[i]["text"];w=W(i);e=entity(w,"馆职","官职",z,"本条明载馆职为三馆秘阁官通称及后世秘书省部分职事官称谓。")
    early=tp(w,e,"北宋元丰改制前","三馆秘阁各类文学高选官员通称馆职",i,z,"馆职统称","建元丰前馆职统称节点。",chain="none")
    abolish=tp(w,e,"北宋元丰五年","崇文院罢，旧馆职不复除人",i,z,"馆职统称","建旧馆职停除节点。",chain="none")
    restore=tp(w,e,"北宋元祐元年三月","复部分馆阁职名，但已与馆职职事分离",i,z,"馆职统称","建元祐复名节点。",chain="none")
    formal=tp(w,e,"北宋政和六年九月","带职馆职与殿阁职名正式定名为贴职",i,z,"馆职统称","建贴职定名节点。",chain="none")
    south=tp(w,e,"北宋元祐以后至南宋","秘书省著作郎等职事官被视为馆职",i,z,"馆职统称","建新制馆职节点。",chain="none")
    chain(w,[early,abolish,restore,formal,south],"连接馆职制度演变时间链。")
    early_titles=("昭文馆大学士","监修国史","集贤殿大学士","集贤院学士","集贤院直学士","史馆修撰","集贤修撰","判昭文馆事","直秘阁","集贤校理","秘阁校理","史馆编修","史馆检讨","崇文院检讨","馆阁校勘","秘阁校勘")
    for title in early_titles:office_instance(w,i,early,title,"北宋元丰改制前",z)
    for title in ("著作郎","著作佐郎","秘书郎","校书郎","正字"):office_instance(w,i,south,title,"北宋元祐以后至南宋",z,"秘书省馆职")
    w.commit()

def entry567_568():
    i=567;z=F[i]["text"];w=W(i);e=entity(w,"正馆职","官职",z,"本条明载校理以上三馆秘阁官总称正馆职。")
    g=tp(w,e,"北宋元丰改制前","校理以上三馆秘阁官总称",i,z,"馆职等级统称","建正馆职统称节点。")
    for title in ("集贤校理","秘阁校理"):
        ie=reuse(w,title);it=w.find_timepoint(ie,"北宋元丰改制前");assert it;rel(w,g,it,"统称与实例",i,z,f"{title}为正馆职实例。")
    w.commit()
    i=568;z=F[i]["text"];w=W(i);e=entity(w,"准馆职","官职",z,"本条明载校勘属于准馆职。")
    g=tp(w,e,"北宋元丰改制前","校勘属准馆职，低于校理",i,z,"馆职等级统称","建准馆职统称节点。")
    for title in ("馆阁校勘","秘阁校勘"):
        ie=reuse(w,title);it=w.find_timepoint(ie,"北宋元丰改制前");assert it;rel(w,g,it,"统称与实例",i,z,f"{title}为准馆职实例。")
    w.commit()

def entry569_570():
    i=569;z=F[i]["text"];w=W(i);e=entity(w,"三馆","机构",z,"本条明载三馆为昭文馆、集贤院、史馆总称。")
    early=tp(w,e,"宋前期","昭文馆、集贤院、史馆总称",i,z,"文馆机构统称","建宋前期三馆节点。",chain="none")
    outer=tp(w,e,"北宋天禧元年八月","崇文外院以三馆为号",i,z,"文馆机构统称","建崇文外院三馆馆额节点。",chain="none")
    end=tp(w,e,"北宋元丰五年","三馆罢，职事归秘书省",i,z,"文馆机构统称","建三馆改制节点。",chain="none")
    later=tp(w,e,"北宋元丰五年以后","秘书省俗称三馆",i,z,"文馆机构俗称","建改制后俗称节点。",chain="none")
    chain(w,[early,outer,end,later],"连接三馆总称、馆额、改制与后世俗称节点。")
    for title in ("昭文馆","集贤院","史馆"):
        ie=w.find_entity(title,"机构") or entity(w,title,"机构",z,f"本条将{title}列为三馆实例。")
        it=w.find_timepoint(ie,"宋前期") or tp(w,ie,"宋前期","三馆成员机构",i,z,"文馆机构",f"建{title}三馆成员节点。")
        rel(w,early,it,"统称与实例",i,z,f"{title}为三馆实例。")
    w.commit()
    i=570;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载监三馆书籍秘阁图书为差遣。")
    t=tp(w,e,"北宋咸平元年十一月","始置，以内侍官充，掌书库钥匙",i,z,"馆阁差遣","建监三馆书籍秘阁图书始置节点。",attr_officer_type="内侍官")
    office=w.find_entity("三馆秘阁","机构");ot=w.find_timepoint(office,"北宋端拱元年五月");assert ot
    rel(w,ot,t,"编制隶属",i,z,"该差遣监掌三馆秘阁书籍图书。",staff_type="官")
    w.commit()

def main():entry551_564();entry565();entry566();entry567_568();entry569_570()
if __name__=="__main__":main()
