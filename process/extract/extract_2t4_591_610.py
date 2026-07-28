#!/usr/bin/env python3
"""提取 chapter2t4 第591–610条：史馆末职、集贤院与秘阁。"""
import json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.environ.get("SONG_ENTRY_DB",os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db"))
def load(i):
    with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return {"title":r[0],"page":r[1],"text":r[2] or "","fields":json.loads(r[3] or "{}")}
F={i:load(i) for i in range(591,611)}
def W(i):return EntryWriter(ENTRY_DB,F[i]["title"],F[i]["page"])
def Q(i,k=None):return F[i]["fields"][k] if k else F[i]["text"]
def C(i,k=None):return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'+(f"（{k}字段）" if k else "")
def en(w,title,typ,i,q,d):return w.entity(title,typ,d,quotation=q)
def ac(w,table,rid,i,q,d,k=None,**kw):return w.citation(table,rid,C(i,k),q,d,**kw)
def tp(w,e,time,event,i,q,cat,d,k=None,**kw):
    t=w.timepoint(e,time,event,d,q,attr_category=cat,**kw);ac(w,"Timepoints",t,i,q,d,k);return t
def rel(w,a,b,kind,i,q,d,k=None,citation_kw=None,**kw):
    r=w.relationship(a,b,kind,d,q,**kw);ac(w,"Relationships",r,i,q,d,k,**(citation_kw or {}));return r
def chain(w,ts,d):
    assert ts and len(ts)==len(set(ts)),ts
    for n,t in enumerate(ts):w.relink(t,d,prev_id=ts[n-1] if n else None,succ_id=ts[n+1] if n+1<len(ts) else None)
def fe(w,title,typ):
    e=w.find_entity(title,typ);assert e,(title,typ);return e
def ft(w,e,time):
    t=w.find_timepoint(e,time);assert t,(e,time);return t
def rewrite(w,t,time,event,i,q,cat,d,k=None,officer=None,grade=None):
    row=w.conn.execute("select entity_id,time,event,attr_category,attr_officer_type,attr_grade from Timepoints where id=?",(t,)).fetchone();assert row
    assert not w.conn.execute("select 1 from Timepoints where entity_id=? and time=? and id<>?",(row[0],time,t)).fetchone()
    w.conn.execute("update Timepoints set time=?,event=?,quotation=?,attr_category=?,attr_officer_type=?,attr_grade=? where id=?",(time,event,q,cat or row[3],officer or row[4],grade or row[5],t))
    w._br("Timepoints",t,f"据专条细化 time={row[1]}、event={row[2]} 为 time={time}、event={event}：{d}");ac(w,"Timepoints",t,i,q,d,k);return t
def rename(w,e,new,i,q,d):
    old=w.conn.execute("select title from Entities where id=?",(e,)).fetchone()[0]
    if old!=new:
        assert not w.conn.execute("select 1 from Entities where title=? and type='官职' and id<>?",(new,e)).fetchone()
        w.conn.execute("update Entities set title=?,quotation=? where id=?",(new,q,e));w._br("Entities",e,f"据正式专条将{old}规范为{new}：{d}")
    return e
def post(w,title,time,i,q,cat="馆职",k=None):
    e=en(w,title,"官职",i,q,f"原文编制或专条明载{title}。")
    t=tp(w,e,time,"设置或在编",i,q,cat,f"建{title}编制节点。",k,chain="none")
    return e,t
def update_rel(w,r,quota=None,staff_type=None,d="补充编制属性"):
    old=w.conn.execute("select staff_quota,staff_type from Relationships where id=?",(r,)).fetchone();assert old
    nq=old[0] if quota is None else quota;nt=old[1] if staff_type is None else staff_type
    if (nq,nt)!=old:
        w.conn.execute("update Relationships set staff_quota=?,staff_type=? where id=?",(nq,nt,r));w._br("Relationships",r,f"{d}：quota {old[0]}->{nq}, staff_type {old[1]}->{nt}")
def refine_rel_subject(w,obj,new_subject,d):
    row=w.conn.execute("select id,subject_id from Relationships where object_id=? and relation_type='编制隶属' order by id limit 1",(obj,)).fetchone();assert row,obj
    if row[1]!=new_subject:
        assert not w.conn.execute("select 1 from Relationships where subject_id=? and object_id=? and relation_type='编制隶属'",(new_subject,obj)).fetchone()
        w.conn.execute("update Relationships set subject_id=? where id=?",(new_subject,row[0]));w._br("Relationships",row[0],f"据专条把编制关系机构端点 {row[1]}->{new_subject}：{d}")
    return row[0]

def entry591_592():
    i=591;z=Q(i);w=W(i);e=fe(w,"史馆祗候","官职");old=ft(w,e,"北宋元丰改制前")
    t=rewrite(w,old,"北宋太平兴国三年","始置，后不复除人",i,z,"馆职","据专条细化史馆编制节点。",officer="京官")
    history=fe(w,"史馆","机构");parent=ft(w,history,"北宋太平兴国三年二月一日");refine_rel_subject(w,t,parent,"史馆祗候专条给出太平兴国三年始置时间。");rel(w,parent,t,"编制隶属",i,z,"史馆置史馆祗候，以京官充。",staff_type="官");w.commit()

    i=592;z=Q(i);w=W(i);e=fe(w,"史馆编校书籍","官职");rename(w,e,"编校史馆书籍",i,z,"专条标题为正式词序。")
    old=ft(w,e,"北宋元丰改制前");t=rewrite(w,old,"北宋嘉祐四年六月","始置，整理校对本馆图籍；供职二年可补馆职",i,z,"馆阁实事官","据专条细化史馆编制节点。")
    short=Q(i,"简称");ac(w,"Timepoints",t,i,short,"补读简称字段中的二年补校勘制度事实。","简称",note="简称段制度事实")
    history=fe(w,"史馆","机构");ht=tp(w,history,"北宋嘉祐四年六月","置编校史馆书籍",i,z,"文馆机构","建史馆嘉祐增置实事官节点。",chain="none")
    chain(w,[ft(w,history,"北齐"),ft(w,history,"唐贞观三年十二月"),ft(w,history,"宋初"),ft(w,history,"宋前期"),ft(w,history,"北宋太平兴国三年二月一日"),ft(w,history,"北宋端拱元年五月"),ft(w,history,"北宋大中祥符八年"),ht,ft(w,history,"北宋元丰五年"),ft(w,history,"南宋建炎元年五月"),ft(w,history,"南宋绍兴十年二月二十九日"),ft(w,history,"南宋嘉定六年六月十八日")],"插入史馆嘉祐编校官节点。")
    refine_rel_subject(w,t,ht,"编校史馆书籍专条给出嘉祐四年六月始置时间。");rel(w,ht,t,"编制隶属",i,z,"史馆置编校史馆书籍。",staff_type="官");w.commit()

def entry593():
    i=593;main=Q(i);h=Q(i,"职源与沿革");duty=Q(i,"职能");order=Q(i,"序位");comp=Q(i,"编制");w=W(i);e=fe(w,"集贤院","机构")
    tang=tp(w,e,"唐开元十三年","始有集贤殿书院之名，为宋集贤院所本",i,h,"文馆机构","建唐代职源节点。","职源与沿革",chain="none")
    song=ft(w,e,"宋前期");ac(w,"Timepoints",song,i,h,"补证宋沿唐制置集贤院。","职源与沿革")
    end=ft(w,e,"北宋元丰五年");ac(w,"Timepoints",end,i,h,"补证元丰官制不置集贤院。","职源与沿革")
    chain(w,[tang,song,ft(w,e,"北宋太平兴国三年二月一日"),ft(w,e,"北宋端拱元年五月"),ft(w,e,"北宋大中祥符八年"),end],"补入集贤院唐代职源并重排宋代沿革。")
    ac(w,"Timepoints",song,i,duty,"补证藏书、馆职与储才职能。","职能",note="职能");ac(w,"Timepoints",song,i,order,"补证在史馆之下、秘阁之上。","序位",note="序位");ac(w,"Timepoints",song,i,comp,"补证官额与吏额。","编制",note="编制")
    parent=fe(w,"崇文院","机构");rel(w,ft(w,parent,"北宋太平兴国三年二月一日"),ft(w,e,"北宋太平兴国三年二月一日"),"上下级机构",i,main,"集贤院隶崇文院。")
    specs=(("集贤殿大学士",1),("集贤院学士",None),("集贤殿直学士",None),("集贤修撰",None),("直集贤院",None),("集贤校理",None),("编校集贤院书籍",None))
    for title,quota in specs:
        pe,pt=post(w,title,"北宋元丰改制前",i,comp,k="编制");rel(w,song,pt,"编制隶属",i,comp,f"集贤院馆职额列{title}。","编制",staff_quota=quota,staff_type="官")
    for title,quota in (("孔目官",1),("表奏官",1),("掌舍",1)):
        ce=en(w,title,"官职",i,comp,f"集贤院吏额明列{title}。");ct=w.find_timepoint(ce,"宋前期") or tp(w,ce,"宋前期","集贤院吏额",i,comp,"吏职",f"建{title}集贤院吏额节点。","编制",chain="none")
        if title=="掌舍":chain(w,[ct,ft(w,ce,"北宋淳化四年二月")],"把掌舍宋前期馆阁吏额节点接到淳化四年审官院编制节点之前。")
        rel(w,song,ct,"编制隶属",i,comp,f"集贤院吏额列{title}{quota}人。","编制",staff_quota=quota,staff_type="吏")
    w.commit()

def entry594_595():
    i=594;h=Q(i,"职源");comp=Q(i,"编制、职能");grade=Q(i,"品位");short=Q(i,"简称与别名");w=W(i);e=fe(w,"集贤殿大学士","官职");old=ft(w,e,"北宋元丰改制前")
    song=rewrite(w,old,"宋初","沿置，为宰相带职",i,h,"馆职","据专条细化宽泛馆职节点。","职源")
    tang=tp(w,e,"唐肃宗至德二载","始置",i,h,"馆职","建唐代始置节点。","职源",chain="none");end=tp(w,e,"北宋元丰三年九月二十七日","罢置",i,h,"馆职","建元丰三年罢置节点。","职源",chain="none");chain(w,[tang,song,end],"连接集贤殿大学士唐置、宋沿与罢置。")
    ac(w,"Timepoints",song,i,comp,"补证一人、以宰相充。","编制、职能",note="编制职能");ac(w,"Timepoints",song,i,grade,"补证三相时末相带职与迁转次序。","品位",note="品位");ac(w,"Timepoints",song,i,short,"补证集贤院大学士与集贤殿大学士为同一职及三馆分领。","简称与别名",note="同名归并，不建别称实体")
    office=fe(w,"集贤院","机构");r=rel(w,ft(w,office,"宋前期"),song,"编制隶属",i,comp,"集贤院大学士一人，以宰相充。","编制、职能",staff_quota=1,staff_type="官");update_rel(w,r,1,"官","专条补一人员额");w.commit()

    i=595;z=Q(i);w=W(i);e=fe(w,"集贤殿直学士","官职");old=ft(w,e,"北宋元丰改制前")
    song=rewrite(w,old,"宋初","沿设但罕置，或以此判集贤院事",i,z,"馆职","据专条细化集贤院编制节点。")
    tang=tp(w,e,"唐开元十三年","六品以下入集贤殿书院者称直学士，为设官之始",i,z,"馆职","建唐代始置节点。",chain="none");chain(w,[tang,song],"连接集贤殿直学士唐置与宋沿。")
    office=fe(w,"集贤院","机构");rel(w,ft(w,office,"宋前期"),song,"编制隶属",i,z,"宋初集贤院沿设直学士。",staff_type="官");w.commit()

def entry596():
    i=596;h=Q(i,"职源与沿革");duty=Q(i,"职能");grade=Q(i,"品位");comp=Q(i,"编制");w=W(i);e=fe(w,"集贤院学士","官职");old=ft(w,e,"北宋元丰改制前")
    song=rewrite(w,old,"宋初","沿置集贤院学士",i,h,"馆职","据专条细化宽泛馆职节点。","职源与沿革")
    tang=tp(w,e,"唐开元十三年四月","始有集贤书院学士之称",i,h,"馆职","建唐代始置节点。","职源与沿革",chain="none");end=tp(w,e,"北宋元丰五年","改制罢",i,h,"馆职","建元丰罢置节点。","职源与沿革",chain="none");restore=tp(w,e,"北宋元祐五年九月十六日","复置为贴职",i,h,"贴职","建元祐复置节点。","职源与沿革",chain="none");rank=tp(w,e,"北宋绍圣元年","仪制、恩数依中散大夫",i,grade,"贴职","建绍圣元年班品节点。","品位",attr_grade="从五品",chain="none");change=tp(w,e,"北宋绍圣二年四月三日","改为集贤殿修撰",i,h,"贴职","建改名节点。","职源与沿革",chain="none")
    chain(w,[tang,song,end,restore,rank,change],"连接集贤院学士唐置、宋置罢、复置及改名。")
    ac(w,"Timepoints",song,i,duty,"补证馆职与贴职职能。","职能",note="职能");ac(w,"Timepoints",song,i,grade,"补证任官资格与序位。","品位",note="品位");ac(w,"Timepoints",song,i,comp,"补证无定员。","编制",note="编制")
    target=fe(w,"集贤修撰","官职");tt=tp(w,target,"北宋绍圣二年四月三日","由集贤院学士改称",i,h,"贴职","建改名后继节点。","职源与沿革",chain="none");rel(w,change,tt,"前后演变",i,h,"集贤院学士于绍圣二年改为集贤殿修撰。","职源与沿革")
    office=fe(w,"集贤院","机构");rel(w,ft(w,office,"宋前期"),song,"编制隶属",i,h,"宋沿置集贤院学士。","职源与沿革",staff_type="官");w.commit()

def entry597():
    i=597;h=Q(i,"职源与沿革");duty=Q(i,"职能");grade=Q(i,"品位");comp=Q(i,"编制");w=W(i);e=fe(w,"集贤修撰","官职");rename(w,e,"集贤殿修撰",i,Q(i),"专条采用正式全称。")
    old=ft(w,e,"北宋元丰改制前");song=rewrite(w,old,"宋初","从唐制沿置集贤殿修撰",i,h,"馆职","据专条细化宽泛馆职节点。","职源与沿革")
    a=tp(w,e,"唐开元八年","集贤殿置修撰",i,h,"馆职","建唐开元八年一般修撰节点。","职源与沿革",chain="none");b=tp(w,e,"唐开元十三年","集贤殿书院始置修撰",i,h,"馆职","建唐开元十三年书院修撰节点。","职源与沿革",chain="none");end=tp(w,e,"北宋元丰五年","集贤院改制罢",i,h,"馆职","建元丰罢置节点。","职源与沿革",chain="none");restore=tp(w,e,"北宋元祐元年三月二十八日","复为贴职",i,h,"贴职","建元祐复置节点。","职源与沿革",attr_grade="正六品",chain="none");level=tp(w,e,"北宋元符二年十一月三日","定为三等贴职之一",i,duty,"贴职","建元符贴职等级节点。","职能",attr_grade="正六品",chain="none");change=tp(w,e,"北宋政和五年四月十日","改为右文殿修撰",i,h,"贴职","建政和改名节点。","职源与沿革",chain="none");shaosheng=ft(w,e,"北宋绍圣二年四月三日")
    chain(w,[a,b,song,end,restore,shaosheng,level,change],"连接集贤殿修撰唐代两层职源、宋置罢、复置与改名。")
    ac(w,"Timepoints",song,i,duty,"补证馆阁官储才及带职性质。","职能",note="职能");ac(w,"Timepoints",restore,i,grade,"补证元祐官品正六品。","品位",note="品位");ac(w,"Timepoints",song,i,comp,"补证无定员。","编制",note="编制")
    right=en(w,"右文殿修撰","官职",i,h,"原文明载集贤殿修撰改为右文殿修撰。");rt=tp(w,right,"北宋政和五年四月十日","由集贤殿修撰改称",i,h,"贴职","建右文殿修撰改名节点。","职源与沿革",chain="none");rel(w,change,rt,"前后演变",i,h,"集贤殿修撰改为右文殿修撰。","职源与沿革")
    office=fe(w,"集贤院","机构");rel(w,ft(w,office,"宋前期"),song,"编制隶属",i,h,"宋从唐制置集贤殿修撰。","职源与沿革",staff_type="官");w.commit()

def entry598_601():
    i=598;h=Q(i,"职源与沿革");duty=Q(i,"职掌");grade=Q(i,"品位");w=W(i);e=en(w,"判集贤院事","官职",i,Q(i),"原文明载为馆职名。");song=tp(w,e,"宋初","沿置判集贤院事",i,h,"馆职","建宋初沿置节点。","职源与沿革",chain="none");tang=tp(w,e,"唐开元间","始置",i,h,"馆职","建唐代始置节点。","职源与沿革",chain="none");end=tp(w,e,"北宋元丰五年","改制罢",i,h,"馆职","建元丰罢置节点。","职源与沿革",chain="none");chain(w,[tang,song,end],"连接判集贤院事唐置、宋沿与罢置。");ac(w,"Timepoints",song,i,duty,"补证馆内供职及带职。","职掌",note="职掌");ac(w,"Timepoints",song,i,grade,"补证任官资格与序位。","品位",note="品位");office=fe(w,"集贤院","机构");rel(w,ft(w,office,"宋前期"),song,"编制隶属",i,h,"宋沿置判集贤院事。","职源与沿革",staff_type="官");w.commit()

    i=599;h=Q(i,"职源与沿革");duty=Q(i,"职能");grade=Q(i,"品位");comp=Q(i,"编制");w=W(i);e=fe(w,"直集贤院","官职");old=ft(w,e,"北宋元丰改制前");start=rewrite(w,old,"北宋淳化元年八月二十六日","始置直集贤院",i,h,"馆职","据专条细化集贤院编制节点。","职源与沿革");tang=tp(w,e,"唐开元十九年","始置",i,h,"馆职","建唐代始置节点。","职源与沿革",chain="none");end=tp(w,e,"北宋元丰五年","罢置",i,h,"馆职","建元丰罢置节点。","职源与沿革",chain="none");restore=tp(w,e,"北宋元祐元年三月二十八日","复置为六等贴职之一",i,h,"贴职","建元祐复置节点。","职源与沿革",chain="none");change=tp(w,e,"北宋绍圣二年四月三日","改为直秘阁",i,h,"贴职","建绍圣改名节点。","职源与沿革",chain="none");chain(w,[tang,start,end,restore,change],"连接直集贤院唐置、宋置罢、复置与改名。");ac(w,"Timepoints",start,i,duty,"补证馆职及贴职职能。","职能",note="职能");ac(w,"Timepoints",start,i,grade,"补证任官资格与序位。","品位",note="品位");ac(w,"Timepoints",start,i,comp,"补证无定员。","编制",note="编制")
    target=fe(w,"直秘阁","官职");tt=tp(w,target,"北宋绍圣二年四月三日","承接直集贤院贴职名",i,h,"贴职","建直秘阁承接改名节点。","职源与沿革",chain="none");rel(w,change,tt,"前后演变",i,h,"直集贤院改为直秘阁。","职源与沿革");office=fe(w,"集贤院","机构");rel(w,ft(w,office,"宋前期"),start,"编制隶属",i,h,"北宋始置直集贤院。","职源与沿革",staff_type="官");w.commit()

    i=600;h=Q(i,"职源与沿革");duty=Q(i,"职能");grade=Q(i,"品位");comp=Q(i,"编制");short=Q(i,"简称");w=W(i);e=fe(w,"集贤校理","官职");old=ft(w,e,"北宋元丰改制前");start=rewrite(w,old,"北宋端拱初年","宋始置集贤校理",i,h,"馆职","据专条细化宽泛馆职节点。","职源与沿革");tang=tp(w,e,"唐开元十三年四月","始置",i,h,"馆职","建唐代始置节点。","职源与沿革",chain="none");end=tp(w,e,"北宋元丰五年","改制罢",i,h,"馆职","建元丰罢置节点。","职源与沿革",chain="none");restore=tp(w,e,"北宋元祐元年","列为六等贴职之一",i,h,"贴职","建元祐复置节点。","职源与沿革",chain="none");witness=tp(w,e,"北宋皇祐三年十月","已见集贤校理通称集校",i,short,"馆职","建皇祐实见节点。","简称",chain="none");change=tp(w,e,"北宋绍圣二年四月","改为秘阁校理",i,h,"贴职","建绍圣改名节点。","职源与沿革",chain="none");chain(w,[tang,start,witness,end,restore,change],"连接集贤校理唐置、宋置罢、皇祐实见、复置与改名。");ac(w,"Timepoints",start,i,duty,"补证馆职与外任贴职。","职能",note="职能");ac(w,"Timepoints",start,i,grade,"补证馆职等级。","品位",note="品位");ac(w,"Timepoints",start,i,comp,"补证不定员。","编制",note="编制")
    target=fe(w,"秘阁校理","官职");tt=tp(w,target,"北宋绍圣二年四月","由集贤校理改称",i,h,"贴职","建秘阁校理承接改名节点。","职源与沿革",chain="none");rel(w,change,tt,"前后演变",i,h,"集贤校理改为秘阁校理。","职源与沿革");office=fe(w,"集贤院","机构");rel(w,ft(w,office,"宋前期"),start,"编制隶属",i,h,"宋始置集贤校理。","职源与沿革",staff_type="官");w.commit()

    i=601;z=Q(i);w=W(i);e=fe(w,"编校集贤院书籍","官职");old=ft(w,e,"北宋元丰改制前");start=rewrite(w,old,"北宋嘉祐四年六月","始置，整理校对本院图籍；供职二年可迁馆职",i,z,"馆阁实事官","据专条细化集贤院编制节点。");end=tp(w,e,"北宋元丰五年","改制罢",i,z,"馆阁实事官","建元丰罢置节点。",chain="none");chain(w,[start,end],"连接编校集贤院书籍始置与罢置。");short=Q(i,"简称");ac(w,"Timepoints",start,i,short,"补读简称字段中的编校实例，不建别称实体。","简称",note="简称段制度例证")
    office=fe(w,"集贤院","机构");ot=tp(w,office,"北宋嘉祐四年六月","置编校集贤院书籍",i,z,"文馆机构","建集贤院嘉祐增置实事官节点。",chain="none");chain(w,[ft(w,office,"唐开元十三年"),ft(w,office,"宋前期"),ft(w,office,"北宋太平兴国三年二月一日"),ft(w,office,"北宋端拱元年五月"),ft(w,office,"北宋大中祥符八年"),ot,ft(w,office,"北宋元丰五年")],"插入集贤院嘉祐编校官节点。");refine_rel_subject(w,start,ot,"编校集贤院书籍专条给出嘉祐四年六月始置时间。");rel(w,ot,start,"编制隶属",i,z,"集贤院置编校集贤院书籍。",staff_type="官");w.commit()

def entry602():
    i=602;h=Q(i,"职源与沿革");duty=Q(i,"职能");comp=Q(i,"编制");order=Q(i,"序位");w=W(i);e=fe(w,"秘阁","机构");old=ft(w,e,"北宋端拱元年五月");start=rewrite(w,old,"北宋端拱元年五月五日","始置秘阁",i,h,"文馆机构","据专条补确日。","职源与沿革")
    jin=tp(w,e,"西晋武帝时","已置秘书阁，省称秘阁",i,h,"文馆机构","建西晋职源节点。","职源与沿革",chain="none");rank=tp(w,e,"北宋淳化元年八月","定秘阁次三馆",i,order,"文馆机构","建淳化序位节点。","序位",chain="none");reform=tp(w,e,"北宋元丰五年","归秘书省",i,h,"文馆机构","建元丰归属节点。","职源与沿革",chain="none");hui=tp(w,e,"北宋徽宗即位","重修秘阁",i,h,"文馆机构","建徽宗重修节点。","职源与沿革",chain="none");chain(w,[jin,start,rank,reform,hui],"连接秘阁西晋职源、宋置、序位、元丰归省与徽宗重修。");ac(w,"Timepoints",start,i,duty,"补证藏真本书画、召试储才职能。","职能",note="职能");ac(w,"Timepoints",start,i,comp,"补证官额与吏额。","编制",note="编制")
    secretary=fe(w,"秘书省","机构");rel(w,ft(w,secretary,"北宋元丰五年"),reform,"上下级机构",i,h,"元丰改制后秘阁归秘书省。","职源与沿革")
    specs=(("判秘阁事",1),("直秘阁",None),("秘阁校理",None),("编校秘阁书籍",None))
    for title,quota in specs:
        pe,pt=post(w,title,"北宋元丰改制前",i,comp,k="编制");rel(w,start,pt,"编制隶属",i,comp,f"秘阁馆职额列{title}。","编制",staff_quota=quota,staff_type="官")
    for title,quota in (("典书",3),("楷书",7),("写御书",10),("装裁匠",12)):
        ce=en(w,title,"官职",i,comp,f"秘阁吏额明列{title}。");ct=w.find_timepoint(ce,"宋前期") or tp(w,ce,"宋前期","秘阁吏额",i,comp,"吏职",f"建{title}秘阁吏额节点。","编制",chain="none");rel(w,start,ct,"编制隶属",i,comp,f"秘阁吏额列{title}{quota}人。","编制",staff_quota=quota,staff_type="吏")
    w.commit()

def entry603_606():
    i=603;h=Q(i,"职源与沿革");duty=Q(i,"职能");grade=Q(i,"品位");w=W(i);e=fe(w,"直秘阁","官职");old=ft(w,e,"北宋元丰改制前");start=rewrite(w,old,"北宋端拱元年五月五日","始置直秘阁",i,h,"馆职","据专条细化宽泛馆职节点。","职源与沿革")
    early=tp(w,e,"北宋咸平以前","与秘阁校理、监秘阁图书共掌阁务",i,duty,"馆职","建咸平前职事节点。","职能",chain="none");end=tp(w,e,"北宋元丰五年","不复置；已带者依旧，除职事官后罢带",i,h,"馆职","建元丰停置节点。","职源与沿革",chain="none");restore=tp(w,e,"北宋元祐元年三月","复置为六等贴职之一",i,h,"贴职","建元祐复置节点。","职源与沿革",chain="none");convert=ft(w,e,"北宋绍圣二年四月三日");yuanfu=tp(w,e,"北宋元符二年十一月","定为三等贴职初阶",i,h,"贴职","建元符等级节点。","职源与沿革",chain="none");zhenghe=tp(w,e,"北宋政和六年九月","定为九等贴职初阶",i,h,"贴职","建政和等级节点。","职源与沿革",chain="none");j15=tp(w,e,"南宋嘉定十五年","已见直秘阁为地方官带职",i,duty,"贴职","建嘉定十五年实见节点。","职能",chain="none");j16=tp(w,e,"南宋嘉定十六年","已见直秘阁为地方官带职",i,duty,"贴职","建嘉定十六年实见节点。","职能",chain="none");late=tp(w,e,"南宋后期","京官得直秘阁，位望渐降",i,grade,"贴职","建南宋后期任官与位望节点。","品位",attr_officer_type="京官",attr_grade="正八品",chain="none");generic=ft(w,e,"宋代（未载具体年月）");chain(w,[start,early,end,restore,convert,yuanfu,zhenghe,j15,j16,late,generic],"连接直秘阁始置、职事、元丰停置、复置、等级与南宋变化。");ac(w,"Timepoints",start,i,grade,"补证正八品及宋前期朝官充。","品位",note="品位");office=fe(w,"秘阁","机构");rel(w,ft(w,office,"北宋端拱元年五月五日"),start,"编制隶属",i,h,"秘阁始置直秘阁。","职源与沿革",staff_type="官");w.commit()

    i=604;h=Q(i,"职源与沿革");duty=Q(i,"职掌");grade=Q(i,"品位");comp=Q(i,"编制");w=W(i);e=en(w,"提辖秘阁供御图书","官职",i,Q(i),"原文明载为馆职名。");start=tp(w,e,"北宋端拱元年五月五日","始置，专决秘阁事务",i,h,"馆职","建始置节点。","职源与沿革",attr_officer_type="丞郎、学士",chain="none");change=tp(w,e,"北宋大中祥符九年九月","改称判阁事",i,h,"馆职","建改名节点。","职源与沿革",chain="none");chain(w,[start,change],"连接提辖秘阁供御图书置、改节点。");ac(w,"Timepoints",start,i,duty,"补证专决阁务。","职掌",note="职掌");ac(w,"Timepoints",start,i,grade,"补证任官与序位。","品位",note="品位");ac(w,"Timepoints",start,i,comp,"补证一人。","编制",note="编制");target=fe(w,"判秘阁事","官职");old=ft(w,target,"北宋元丰改制前");tt=rewrite(w,old,"北宋大中祥符九年九月","由提辖秘阁供御图书改称",i,h,"馆职","据改名专条细化秘阁编制节点。","职源与沿革");rel(w,change,tt,"前后演变",i,h,"提辖秘阁供御图书改称判阁事。","职源与沿革");office=fe(w,"秘阁","机构");rel(w,ft(w,office,"北宋端拱元年五月五日"),start,"编制隶属",i,comp,"秘阁置提辖秘阁供御图书一人。","编制",staff_quota=1,staff_type="官");w.commit()

    i=605;h=Q(i,"职源与沿革");duty=Q(i,"职掌");grade=Q(i,"品位");comp=Q(i,"编制");w=W(i);e=fe(w,"判秘阁事","官职");start=ft(w,e,"北宋大中祥符九年九月");ac(w,"Timepoints",start,i,h,"专条补证始置时间。","职源与沿革");end=tp(w,e,"北宋元丰五年","改制罢",i,h,"馆职","建元丰罢置节点。","职源与沿革",chain="none");chain(w,[start,end],"连接判秘阁事始置与罢置。");ac(w,"Timepoints",start,i,duty,"补证领秘阁兼判秘书省。","职掌",note="职掌");ac(w,"Timepoints",start,i,grade,"补证任官与序位。","品位",note="品位");ac(w,"Timepoints",start,i,comp,"补证一人。","编制",note="编制");office=fe(w,"秘阁","机构");r=rel(w,ft(w,office,"北宋端拱元年五月五日"),start,"编制隶属",i,comp,"秘阁置判秘阁事一人。","编制",staff_quota=1,staff_type="官");update_rel(w,r,1,"官","专条补一人员额");w.commit()

    i=606;main=Q(i);h=Q(i,"职源与沿革");duty=Q(i,"职掌");grade=Q(i,"品位");comp=Q(i,"编制");w=W(i);e=fe(w,"秘阁校理","官职");old=ft(w,e,"北宋元丰改制前");start=rewrite(w,old,"北宋端拱元年五月五日","始置秘阁校理",i,h,"馆职","据专条细化宽泛馆职节点。","职源与沿革");early=tp(w,e,"北宋咸平以前","与直秘阁、监秘阁图书共同管理阁务",i,duty,"馆职","建咸平前职事节点。","职掌",chain="none");after=tp(w,e,"北宋咸平以后","不再参与阁务",i,duty,"馆职","建咸平后职事变化节点。","职掌",chain="none");end=tp(w,e,"北宋元丰五年","改制罢",i,h,"馆职","建元丰罢置节点。","职源与沿革",chain="none");restore=tp(w,e,"北宋元祐元年三月二十八日","复为六等贴职之一",i,h,"贴职","建元祐复置节点。","职源与沿革",chain="none");change=ft(w,e,"北宋绍圣二年四月");abolish=tp(w,e,"北宋元符二年十一月十三日","罢带职",i,h,"贴职","建元符罢带节点。","职源与沿革",chain="none");chain(w,[start,early,after,end,restore,change,abolish],"连接秘阁校理始置、职事变化、罢复、改名承接与罢带。");ac(w,"Timepoints",change,i,main,"补证集贤校理于绍圣二年改为秘阁校理。",note="改名总述");ac(w,"Timepoints",start,i,grade,"补证馆职等级及任官。","品位",note="品位");ac(w,"Timepoints",start,i,comp,"补证无定员。","编制",note="编制");office=fe(w,"秘阁","机构");rel(w,ft(w,office,"北宋端拱元年五月五日"),start,"编制隶属",i,h,"秘阁始置秘阁校理。","职源与沿革",staff_type="官");w.commit()

def entry607_610():
    i=607;z=Q(i);w=W(i);e=en(w,"监秘阁图书","官职",i,z,"原文明载为差遣名。");t=tp(w,e,"北宋端拱元年八月","始置，与直秘阁、秘阁校理共掌御书供进及阁务",i,z,"馆阁差遣","建始置节点。",attr_officer_type="内侍官");office=fe(w,"秘阁","机构");rel(w,ft(w,office,"北宋端拱元年五月五日"),t,"编制隶属",i,z,"监秘阁图书为秘阁差遣。",staff_type="官");w.commit()

    i=608;z=Q(i);w=W(i);e=fe(w,"编校秘阁书籍","官职");old=ft(w,e,"北宋元丰改制前");start=rewrite(w,old,"北宋嘉祐四年六月","始置，非馆职；整理校对本阁图书，供职二年可补馆阁校勘",i,z,"馆阁实事官","据专条细化秘阁编制节点。");end=tp(w,e,"北宋元丰五年","改制罢",i,z,"馆阁实事官","建元丰罢置节点。",chain="none");chain(w,[start,end],"连接编校秘阁书籍始置与罢置。");short=Q(i,"简称");ac(w,"Timepoints",start,i,short,"补读简称字段中的二年补校勘制度事实。","简称",note="简称段制度事实");office=fe(w,"秘阁","机构");ot=tp(w,office,"北宋嘉祐四年六月","置编校秘阁书籍",i,z,"文馆机构","建秘阁嘉祐增置实事官节点。",chain="none");chain(w,[ft(w,office,"西晋武帝时"),ft(w,office,"北宋端拱元年五月五日"),ft(w,office,"北宋淳化元年八月"),ot,ft(w,office,"北宋元丰五年"),ft(w,office,"北宋徽宗即位")],"插入秘阁嘉祐编校官节点。");refine_rel_subject(w,start,ot,"编校秘阁书籍专条给出嘉祐四年六月始置时间。");rel(w,ot,start,"编制隶属",i,z,"秘阁置编校秘阁书籍。",staff_type="官");w.commit()

    i=609;z=Q(i);w=W(i);e=en(w,"馆阁编校书籍","官职",i,z,"原文明载为三馆秘阁编校书籍官总名。");group=tp(w,e,"北宋嘉祐四年六月七日","始置四馆编校书籍官，各二员，共八员",i,z,"馆阁实事官统称","建馆阁编校书籍始置节点。",chain="none")
    instances=(("昭文馆","编校昭文馆书籍"),("史馆","编校史馆书籍"),("集贤院","编校集贤院书籍"),("秘阁","编校秘阁书籍"))
    for office_title,post_title in instances:
        pe=fe(w,post_title,"官职");pt=ft(w,pe,"北宋嘉祐四年六月");rel(w,group,pt,"统称与实例",i,z,f"馆阁编校书籍包括{post_title}。");oe=fe(w,office_title,"机构");ot=w.find_timepoint(oe,"北宋嘉祐四年六月") or tp(w,oe,"北宋嘉祐四年六月",f"置{post_title}二员",i,z,"文馆机构",f"建{office_title}嘉祐编校官节点。",chain="none");r=rel(w,ot,pt,"编制隶属",i,z,f"{office_title}置{post_title}二员。",staff_quota=2,staff_type="官");update_rel(w,r,2,"官","总条明载各二员")
    w.commit()

    i=610;h=Q(i,"职源与沿革");duty=Q(i,"职掌");grade=Q(i,"品位");comp=Q(i,"编制");short=Q(i,"简称");w=W(i);e=fe(w,"馆阁校勘","官职");old=ft(w,e,"北宋元丰改制前");start=rewrite(w,old,"北宋天圣四年五月","始见馆阁校勘之名",i,h,"馆职","据专条细化宽泛馆职节点。","职源与沿革",officer="京官");outside=tp(w,e,"北宋天圣五年二月","特许带出外任",i,duty,"馆职","建天圣五年带外特例节点。","职掌",chain="none");end=tp(w,e,"北宋元丰五年","改制罢",i,h,"馆职","建元丰罢置节点。","职源与沿革",chain="none");restore=tp(w,e,"北宋元祐四年七月四日","复置",i,h,"馆职","建元祐复置节点。","职源与沿革",chain="none");end2=tp(w,e,"北宋元符二年十一月十三日","复罢",i,h,"馆职","建元符罢置节点。","职源与沿革",chain="none");chain(w,[start,outside,end,restore,end2],"连接馆阁校勘始见、带外特例、罢复再罢。");ac(w,"Timepoints",start,i,grade,"补证最低等馆职、京官充及低于校理。","品位",note="品位");ac(w,"Timepoints",start,i,comp,"补证无定员。","编制",note="编制");ac(w,"Timepoints",outside,i,short,"补证天圣五年二月特许带外。","简称",note="简称段制度事实");parent=fe(w,"三馆秘阁","机构");rel(w,ft(w,parent,"北宋大中祥符八年至天圣九年十一月"),start,"编制隶属",i,duty,"馆阁校勘在馆供职，校对书籍。","职掌",staff_type="官");w.commit()

def main():
    entry591_592();entry593();entry594_595();entry596();entry597();entry598_601();entry602();entry603_606();entry607_610()
if __name__=="__main__":main()
