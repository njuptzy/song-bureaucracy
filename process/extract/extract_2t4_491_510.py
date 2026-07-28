#!/usr/bin/env python3
"""提取重建后 chapter2t4 第491–510条（495为无正文占位）：殿阁学士。"""
import json, os, sqlite3, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.environ.get("SONG_ENTRY_DB",os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db"))
def load(i):
    with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return {"title":r[0],"page":r[1],"text":r[2] or "","fields":json.loads(r[3] or "{}")}
F={i:load(i) for i in range(491,511)}
def W(i):return EntryWriter(ENTRY_DB,F[i]["title"],F[i]["page"])
def C(i):return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
def entity(w,title,typ,q,d):return w.entity(title,typ,d,quotation=q)
def cite(w,table,rid,i,q,d,**kw):return w.citation(table,rid,C(i),q,d,**kw)
def tp(w,e,time,event,i,q,cat,d,**kw):
    t=w.timepoint(e,time,event,d,q,attr_category=cat,**kw);cite(w,"Timepoints",t,i,q,d);return t
def rel(w,a,b,k,i,q,d,**kw):
    r=w.relationship(a,b,k,d,q,**kw);cite(w,"Relationships",r,i,q,d);return r
def node(w,title,time,typ=None):
    e=w.find_entity(title,typ);assert e,title
    t=w.find_timepoint(e,time);assert t,(title,time)
    return e,t
def chain(w,ts,d):
    assert len(ts)==len(set(ts))
    for n,t in enumerate(ts):w.relink(t,d,prev_id=ts[n-1] if n else None,succ_id=ts[n+1] if n+1<len(ts) else None)
def reuse(w,title):
    e=w.find_entity(title,"官职");assert e,title;return e

def entry491_494():
    i=491;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=reuse(w,F[i]["title"])
    a=tp(w,e,"北宋太平兴国五年正月十五日","始置，为优宠老臣之清职",i,h,"殿阁职名","建文明殿学士始置节点。",chain="none")
    b=tp(w,e,"北宋庆历七年八月十六日","改名为紫宸殿学士",i,h,"殿阁职名","建文明殿学士改名节点。",chain="none")
    generic=w.find_timepoint(e,"宋代（未载具体年月）");assert generic
    chain(w,[a,generic,b],"将殿学士实例分类节点纳入文明殿学士置改时间链。")
    cite(w,"Timepoints",a,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",a,i,rank,"补证班位。",note="品位")
    w.commit()

    i=492;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];w=W(i);e=reuse(w,F[i]["title"])
    a=tp(w,e,"北宋庆历七年八月十六日","由文明殿学士改名始置",i,h,"殿阁职名","建紫宸殿学士始置节点。",chain="none")
    b=w.find_timepoint(e,"北宋庆历八年五月八日");assert b
    generic=w.find_timepoint(e,"宋代（未载具体年月）");assert generic
    cite(w,"Timepoints",b,i,h,"补证紫宸殿学士改为观文殿学士。",note="职源与沿革")
    chain(w,[a,generic,b],"将殿学士实例分类节点纳入紫宸殿学士置改时间链。")
    cite(w,"Timepoints",a,i,duty,"补证执政罢任带职职能。",note="职能")
    old=node(w,"文明殿学士","北宋庆历七年八月十六日","官职")[1]
    rel(w,old,a,"前后演变",i,h,"文明殿学士改名为紫宸殿学士。")
    w.commit()

    for i,title,start_time in ((493,"资政殿大学士","北宋景德二年十二月七日"),(494,"资政殿学士","北宋景德二年四月二十六日")):
        z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=reuse(w,title)
        a=tp(w,e,start_time,"始置，用以优宠执政离任者并备顾问",i,h,"殿阁职名",f"建{title}始置节点。",chain="none",attr_grade="正三品")
        b=tp(w,e,"南宋","沿置",i,h,"殿阁职名",f"建{title}南宋沿置节点。",chain="none",attr_grade="正三品")
        generic=w.find_timepoint(e,"宋代（未载具体年月）");assert generic
        chain(w,[a,generic,b],f"将殿学士实例分类节点纳入{title}始置至南宋时间链。")
        cite(w,"Timepoints",a,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",a,i,rank,"补证品位。",note="品位")
        w.commit()

def entry496_501():
    i=496;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=reuse(w,F[i]["title"])
    t0=tp(w,e,"后唐天成元年五月二十日","始置",i,h,"殿阁职名","建端明殿学士后唐始置节点。",chain="none")
    t1=tp(w,e,"北宋太平兴国五年正月十五日","改为文明殿学士",i,h,"殿阁职名","建端明殿学士首次改名节点。",chain="none")
    t2=tp(w,e,"北宋明道二年","复置，始除人",i,h,"殿阁职名","建端明殿学士复置节点。",chain="none",attr_grade="正三品")
    t3=tp(w,e,"北宋政和四年八月三日","改为延康殿学士",i,h,"殿阁职名","建端明殿学士改延康节点。",chain="none",attr_grade="正三品")
    t4=tp(w,e,"南宋建炎二年二月十三日","由延康殿学士复改旧名",i,h,"殿阁职名","建南宋复名端明殿学士节点。",chain="none",attr_grade="正三品")
    generic=w.find_timepoint(e,"宋代（未载具体年月）");assert generic
    chain(w,[t0,t1,t2,generic,t3,t4],"将分类节点纳入端明殿学士置、改、复置及复名时间链。")
    cite(w,"Timepoints",t2,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",t2,i,rank,"补证品位。",note="品位")
    civilized=node(w,"文明殿学士","北宋太平兴国五年正月十五日","官职")[1];rel(w,t1,civilized,"前后演变",i,h,"端明殿学士改为文明殿学士。")
    w.commit()

    i=497;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];w=W(i);e=reuse(w,F[i]["title"])
    a=tp(w,e,"北宋政和四年八月三日","由端明殿学士改名始置",i,h,"殿阁职名","建延康殿学士始置节点。",chain="none",attr_grade="正三品")
    b=tp(w,e,"南宋建炎二年二月十三日","复端明殿学士旧名",i,h,"殿阁职名","建延康殿学士复旧名节点。",chain="none",attr_grade="正三品")
    generic=w.find_timepoint(e,"宋代（未载具体年月）");assert generic
    chain(w,[a,generic,b],"将分类节点纳入延康殿学士置改时间链。")
    cite(w,"Timepoints",a,i,duty,"补证职能。",note="职能")
    old=node(w,"端明殿学士","北宋政和四年八月三日","官职")[1];new=node(w,"端明殿学士","南宋建炎二年二月十三日","官职")[1]
    rel(w,old,a,"前后演变",i,h,"端明殿学士改为延康殿学士。")
    rel(w,b,new,"前后演变",i,h,"延康殿学士复端明殿学士旧名。")
    w.commit()

    pairs=((498,"宣和殿大学士",500,"保和殿大学士","北宋政和七年六月二日"),(499,"宣和殿学士",501,"保和殿学士","北宋政和五年四月二十四日"))
    for i,old_title,j,new_title,start_time in pairs:
        z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];w=W(i);e=reuse(w,old_title)
        a=tp(w,e,start_time,"始置，优宠近臣",i,h,"殿阁职名",f"建{old_title}始置节点。",chain="none",attr_grade="正三品")
        b=tp(w,e,"北宋宣和元年二月一日",f"改名为{new_title}",i,h,"殿阁职名",f"建{old_title}改名节点。",chain="none",attr_grade="正三品")
        generic=w.find_timepoint(e,"宋代（未载具体年月）");assert generic
        chain(w,[a,generic,b],f"将分类节点纳入{old_title}始置与改名时间链。")
        cite(w,"Timepoints",a,i,duty,"补证职能。",note="职能")
        w.commit()
        z2=F[j]["text"];h2=F[j]["fields"]["职源与沿革"];duty2=F[j]["fields"]["职能"];rank2=F[j]["fields"]["品位"];w=W(j);ne=reuse(w,new_title)
        c=tp(w,ne,"北宋宣和元年二月一日",f"由{old_title}改名始置",j,h2,"殿阁职名",f"建{new_title}始置节点。",chain="none",attr_grade="正三品")
        d=tp(w,ne,"南宋","沿置",j,h2,"殿阁职名",f"建{new_title}南宋沿置节点。",chain="none",attr_grade="正三品")
        generic=w.find_timepoint(ne,"宋代（未载具体年月）");assert generic
        chain(w,[c,generic,d],f"将分类节点纳入{new_title}始置与南宋沿置时间链。")
        cite(w,"Timepoints",c,j,duty2,"补证职能。",note="职能");cite(w,"Timepoints",c,j,rank2,"补证品位。",note="品位")
        old_end=node(w,old_title,"北宋宣和元年二月一日","官职")[1];rel(w,old_end,c,"前后演变",j,h2,f"{old_title}改名为{new_title}。")
        w.commit()

def entry502_507():
    i=502;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载保和殿直学士为职名。")
    a=tp(w,e,"北宋宣和六年四月十七日","始置，为保和殿待制序进职名",i,z,"殿阁职名","建保和殿直学士始置节点。",chain="none")
    b=tp(w,e,"南宋","废罢",i,z,"殿阁职名","建保和殿直学士南宋废罢节点。",chain="none")
    chain(w,[a,b],"连接保和殿直学士置罢节点。")
    w.commit()
    i=503;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载宣和殿待制为职名。")
    a=tp(w,e,"北宋政和八年三月十六日","始置，初以优宠驸马都尉",i,h,"殿阁职名","建宣和殿待制始置节点。",chain="none")
    b=tp(w,e,"北宋宣和元年二月一日","改为保和殿待制",i,h,"殿阁职名","建宣和殿待制改名节点。",chain="none")
    chain(w,[a,b],"连接宣和殿待制始置与改名节点。")
    cite(w,"Timepoints",a,i,duty,"补证职能。",note="职能")
    w.commit()
    i=504;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载保和殿待制即宣和殿待制改名。")
    t=tp(w,e,"北宋宣和元年二月一日","由宣和殿待制改名",i,z,"殿阁职名","建保和殿待制改名承接节点。",attr_grade="从四品")
    old=node(w,"宣和殿待制","北宋宣和元年二月一日","官职")[1];rel(w,old,t,"前后演变",i,z,"宣和殿待制改名保和殿待制。")
    w.commit()

    i=505;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i)
    pred=entity(w,"崇政院直学士","官职",h,"原文明载后梁崇政院始置直学士。")
    p0=tp(w,pred,"后梁开平二年","枢密院改崇政院，始置直学士",i,h,"枢密职名","建崇政院直学士始置节点。",chain="none")
    p1=tp(w,pred,"后唐同光年间","改为枢密直学士",i,h,"枢密职名","建崇政院直学士改名节点。",chain="none")
    chain(w,[p0,p1],"连接崇政院直学士置改节点。")
    e=entity(w,F[i]["title"],"官职",z,"本条明载枢密直学士为职事官名、职名。")
    a=tp(w,e,"后唐同光年间","由崇政院直学士改名",i,h,"枢密职名","建枢密直学士始置节点。",chain="none")
    song=tp(w,e,"北宋初","沿置，签署枢密院事并备顾问",i,h,"枢密职名","建北宋沿置节点。",chain="none",attr_grade="正三品")
    change=tp(w,e,"北宋政和四年八月三日","改称述古殿直学士",i,h,"枢密职名","建政和改称节点。",chain="none",attr_grade="正三品")
    restore=tp(w,e,"北宋政和四年十月二十四日","改回枢密直学士旧名",i,h,"枢密职名","建政和复名节点。",chain="none",attr_grade="正三品")
    south=tp(w,e,"南宋","存其名",i,h,"枢密职名","建南宋存名节点。",chain="none",attr_grade="正三品")
    chain(w,[a,song,change,restore,south],"连接枢密直学士源流、改称、复名与南宋节点。")
    cite(w,"Timepoints",song,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",song,i,rank,"补证品位。",note="品位")
    rel(w,p1,a,"前后演变",i,h,"崇政院直学士改为枢密直学士。")
    w.commit()
    i=506;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载述古殿学士为枢密直学士短期改名。")
    a=tp(w,e,"北宋政和四年八月三日","由枢密直学士改名",i,z,"殿阁职名","建述古殿学士始置节点。",chain="none",attr_grade="正三品")
    b=tp(w,e,"北宋政和四年十月二十四日","改回枢密直学士",i,z,"殿阁职名","建述古殿学士复名节点。",chain="none",attr_grade="正三品")
    chain(w,[a,b],"连接述古殿学士置改节点。")
    old=node(w,"枢密直学士","北宋政和四年八月三日","官职")[1];new=node(w,"枢密直学士","北宋政和四年十月二十四日","官职")[1]
    rel(w,old,a,"前后演变",i,z,"枢密直学士改名述古殿学士。")
    rel(w,b,new,"前后演变",i,z,"述古殿学士改回枢密直学士。")
    w.commit()
    i=507;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载密谏为枢密直学士与谏议大夫的连称。")
    tp(w,e,"宋代（未载具体年月）","枢密直学士与谏议大夫连称",i,z,"官衔连称","建密谏连称节点；连称组成不误建为统称与实例关系。")
    w.commit()

def collective(i,title,instance_suffixes,first_time,last_time,grade):
    z=F[i]["text"];source=F[i]["fields"]["职源"];duty=F[i]["fields"]["职能"];rank=F[i]["fields"]["品位"];w=W(i);e=entity(w,title,"官职",z,f"本条明载{title}为诸阁同类职名总称。")
    first=tp(w,e,first_time,"最早同类职名始置",i,source,"阁职统称",f"建{title}最早设置节点。",chain="none",attr_grade=grade)
    generic=tp(w,e,"宋代（未载具体年月）","诸阁同类职名总称",i,z,"阁职统称",f"建{title}统称节点。",chain="none",attr_grade=grade)
    last=tp(w,e,last_time,"最晚同类职名始置",i,source,"阁职统称",f"建{title}最晚设置节点。",chain="none",attr_grade=grade)
    chain(w,[first,generic,last],f"连接{title}设置范围节点。")
    cite(w,"Timepoints",generic,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",generic,i,rank,"补证品位。",note="品位")
    for prefix in ("龙图","天章","宝文","显谟","徽猷","敷文","焕章","华文","宝谟","宝章","显文"):
        ititle=prefix+instance_suffixes
        ie=w.find_entity(ititle,"官职") or entity(w,ititle,"官职",z,f"本条将{ititle}列为{title}实例。")
        it=w.find_timepoint(ie,"宋代（未载具体年月）") or tp(w,ie,"宋代（未载具体年月）",f"{title}实例",i,z,"阁职名",f"建{ititle}实例节点。")
        rel(w,generic,it,"统称与实例",i,z,f"{ititle}为{title}实例。")
    w.commit()

def entry508_510():
    collective(508,"阁学士","阁学士","北宋大中祥符三年","南宋咸淳元年","正三品")
    collective(509,"阁直学士","阁直学士","北宋景德四年八月","南宋咸淳元年六月","从三品")
    collective(510,"阁待制","阁待制","北宋景德元年十月","南宋咸淳元年六月","从四品")

def main():entry491_494();entry496_501();entry502_507();entry508_510()
if __name__=="__main__":main()
