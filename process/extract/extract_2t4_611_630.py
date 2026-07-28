#!/usr/bin/env python3
"""提取 chapter2t4 第611–630条：馆阁读书、贴职体系与诸直阁贴职。"""
import json,os,sqlite3,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.environ.get("SONG_ENTRY_DB",os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db"))
def load(i):
    with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return {"title":r[0],"page":r[1],"text":r[2] or "","fields":json.loads(r[3] or "{}")}
F={i:load(i) for i in range(611,631)}
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
def fe(w,title,typ="官职"):
    e=w.find_entity(title,typ);assert e,(title,typ);return e
def ft(w,e,time):
    t=w.find_timepoint(e,time);assert t,(e,time);return t
def ensure_node(w,title,time,i,q,event="列为贴职",cat="贴职",grade=None):
    e=w.find_entity(title,"官职") or en(w,title,"官职",i,q,f"原文贴职编制明列{title}。")
    t=w.find_timepoint(e,time) or tp(w,e,time,event,i,q,cat,f"建{title}{time}制度节点。",attr_grade=grade,chain="none")
    return e,t
def mark(w,t,i,q,d,grade=None,k=None):
    row=w.conn.execute("select attr_category,attr_grade from Timepoints where id=?",(t,)).fetchone();assert row
    cat=row[0] or ""
    newcat=cat if "贴职" in cat else (cat+"、贴职" if cat else "贴职")
    newgrade=row[1] or grade
    if (newcat,newgrade)!=row:
        w.conn.execute("update Timepoints set attr_category=?,attr_grade=? where id=?",(newcat,newgrade,t));w._br("Timepoints",t,f"本条明确列为贴职并补品位：category {row[0]}->{newcat}, grade {row[1]}->{newgrade}。")
    ac(w,"Timepoints",t,i,q,d,k)

def entry611():
    i=611;z=Q(i);w=W(i);e=en(w,"馆阁读书","官职",i,z,"原文明载为馆阁学生的优异安置，虽非正式官名，仍属制度化馆阁身份。")
    a=tp(w,e,"北宋咸平二年六月","始许十二岁神童入秘阁读书",i,z,"馆阁学生安置","建馆阁读书始见节点。",chain="none")
    b=tp(w,e,"北宋景德初","命十四岁神童入秘阁读书",i,z,"馆阁学生安置","建景德初沿用节点。",chain="none")
    c=tp(w,e,"北宋大中祥符间","又以神童听于秘阁读书；读书三年后可召试授馆职",i,z,"馆阁学生安置","建大中祥符恩例节点。",chain="none")
    chain(w,[a,b,c],"连接馆阁读书咸平始见、景德及大中祥符沿用节点。")
    office=fe(w,"秘阁","机构");rel(w,ft(w,office,"北宋端拱元年五月五日"),a,"编制隶属",i,z,"馆阁读书安置于秘阁。",staff_type="学生")
    w.commit()

def member(w,g,title,target_time,i,q,d,k=None,citation_kw=None):
    e=fe(w,title);t=ft(w,e,target_time);return rel(w,g,t,"统称与实例",i,q,d,k,citation_kw=citation_kw)

def entry612():
    i=612;main=Q(i);h=Q(i,"职源与沿革");duty=Q(i,"职能");grade=Q(i,"品位");comp=Q(i,"编制");w=W(i)
    e=en(w,"贴职","官职",i,main,"原文明载元丰前后两类带职名泛称贴职。")
    tang=tp(w,e,"唐德宗贞元间","三文馆兼职已有帖职之称",i,h,"带职统称","建唐代职源节点。","职源与沿革",chain="none")
    early=tp(w,e,"北宋元丰改制前","馆职、殿学士及阁职等带职泛称贴职",i,main,"带职统称","建元丰前贴职总称节点。",chain="none")
    jingde=tp(w,e,"北宋景德元年六月","已见多人帖三馆职",i,h,"带职统称","建景德元年实见节点。","职源与沿革",chain="none")
    jingyou=tp(w,e,"北宋景祐四年十二月","科举出身资格限制导致拟带集贤院学士未成",i,h,"带职统称","建景祐带职资格制度节点。","职源与沿革",chain="none")
    reform=tp(w,e,"北宋元丰五年四月二十三日","罢馆职，引发带职制度变革",i,h,"带职统称","建元丰改制节点。","职源与沿革",chain="none")
    yuanyou1=tp(w,e,"北宋元祐元年二月","复置六等贴职",i,comp,"贴职统称","建元祐六等节点。","编制",chain="none")
    yuanyou4=tp(w,e,"北宋元祐四年七月","增馆阁校勘为贴职",i,h,"贴职统称","建元祐四年增等节点。","职源与沿革",chain="none")
    yuanyou5=tp(w,e,"北宋元祐五年九月十六日","增集贤院学士为贴职",i,h,"贴职统称","建元祐五年增等节点。","职源与沿革",chain="none")
    shaosheng=tp(w,e,"北宋绍圣二年四月","改贴职名并罢职事官带职，保留五等",i,h,"贴职统称","建绍圣调整节点。","职源与沿革",chain="none")
    yuanfu=tp(w,e,"北宋元符二年十一月","减为三等贴职",i,h,"贴职统称","建元符三等节点。","职源与沿革",chain="none")
    zhenghe3=tp(w,e,"北宋政和三年十二月","正式确定庶官所带五等职名为贴职",i,h,"贴职统称","建政和三年定称节点。","职源与沿革",chain="none")
    zhenghe6=tp(w,e,"北宋政和六年九月十七日","定九等贴职",i,h,"贴职统称","建政和六年九等节点。","职源与沿革",chain="none")
    south=tp(w,e,"南宋","自直秘阁至集英殿修撰为贴职，并随新阁增直阁贴职",i,main,"贴职统称","建南宋贴职体系节点。",chain="none")
    chain(w,[tang,early,jingde,jingyou,reform,yuanyou1,yuanyou4,yuanyou5,shaosheng,yuanfu,zhenghe3,zhenghe6,south],"连接贴职唐代职源、元丰前实见、元祐至政和定制及南宋扩展。")
    ac(w,"Timepoints",south,i,duty,"补证贴职作为文学高选、补外带职及通向侍从官的功能。","职能",note="职能")
    ac(w,"Timepoints",zhenghe6,i,grade,"补证政和六年各等品位。","品位",note="品位")
    ac(w,"Timepoints",yuanyou1,i,comp,"补证元祐以后历次编制变化及无定员。","编制",note="编制")
    office_group=fe(w,"馆职");rel(w,early,ft(w,office_group,"北宋元丰改制前"),"统称与实例",i,main,"元丰改制前馆职属于泛称贴职所涵盖的带职。")
    # 总条直接明载的新增贴职实体。
    ensure_node(w,"集英殿修撰","北宋政和六年九月十七日",i,comp,grade="正六品")
    ensure_node(w,"秘阁修撰","北宋政和六年九月十七日",i,comp,grade="从六品")
    ensure_node(w,"直睿思殿","北宋政和三年十二月",i,comp)
    ensure_node(w,"睿思殿供奉官","北宋政和三年十二月",i,comp)
    six=(("集贤殿修撰","北宋元祐元年三月二十八日"),("直龙图阁","北宋大中祥符九年十月二十一日"),("直集贤院","北宋元祐元年三月二十八日"),("直秘阁","北宋元祐元年三月"),("集贤校理","北宋元祐元年"),("秘阁校理","北宋元祐元年三月二十八日"))
    for title,time in six:
        conflict={"conflict_flag":1,"note":"第619条另记直龙图阁于元祐六年复列贴职。"} if title=="直龙图阁" else None
        member(w,yuanyou1,title,time,i,comp,f"{title}为元祐六等贴职之一。","编制",conflict)
    member(w,yuanyou4,"馆阁校勘","北宋元祐四年七月四日",i,h,"元祐四年增馆阁校勘为贴职。","职源与沿革")
    member(w,yuanyou5,"集贤院学士","北宋元祐五年九月十六日",i,h,"元祐五年增集贤院学士为贴职。","职源与沿革")
    five=(("集贤殿修撰","北宋绍圣二年四月三日"),("直龙图阁","北宋大中祥符九年十月二十一日"),("直秘阁","北宋绍圣二年四月三日"),("秘阁校理","北宋绍圣二年四月"),("馆阁校勘","北宋元祐四年七月四日"))
    for title,time in five:member(w,shaosheng,title,time,i,comp,f"{title}为绍圣二年保留的五等贴职之一。","编制")
    for title,time in (("集贤殿修撰","北宋元符二年十一月三日"),("直龙图阁","北宋大中祥符九年十月二十一日"),("直秘阁","北宋元符二年十一月")):member(w,yuanfu,title,time,i,comp,f"{title}为元符三等贴职之一。","编制")
    for title,time in (("集贤殿修撰","北宋元符二年十一月三日"),("直龙图阁","北宋大中祥符九年十月二十一日"),("直秘阁","北宋元符二年十一月"),("直睿思殿","北宋政和三年十二月"),("睿思殿供奉官","北宋政和三年十二月")):member(w,zhenghe3,title,time,i,comp,f"{title}为政和三年五等贴职之一。","编制")
    nine=(("集英殿修撰","北宋政和六年九月十七日"),("右文殿修撰","北宋政和五年四月十日"),("秘阁修撰","北宋政和六年九月十七日"),("直龙图阁","北宋大中祥符九年十月二十一日"),("直徽猷阁","北宋政和六年九月十七日"),("直显谟阁","北宋政和六年九月十七日"),("直宝文阁","北宋政和六年九月十七日"),("直天章阁","北宋政和六年九月十七日"),("直秘阁","北宋政和六年九月"))
    for title,time in nine:member(w,zhenghe6,title,time,i,comp,f"{title}为政和六年九等贴职之一。","编制")
    south_members=(("集英殿修撰","北宋政和六年九月十七日"),("右文殿修撰","北宋政和五年四月十日"),("秘阁修撰","北宋政和六年九月十七日"),("直龙图阁","北宋大中祥符九年十月二十一日"),("直天章阁","北宋政和六年九月十七日"),("直宝文阁","北宋政和六年九月十七日"),("直显谟阁","北宋政和六年九月十七日"),("直徽猷阁","北宋政和六年九月十七日"),("直敷文阁","南宋绍兴十年五月十一日"),("直焕章阁","南宋淳熙十五年十一月九日"),("直华文阁","南宋庆元二年五月十五日"),("直宝谟阁","南宋嘉泰二年八月十二日"),("直宝章阁","南宋宝庆二年十月二日"),("直显文阁","南宋咸淳元年六月十八日"),("直秘阁","南宋嘉定十五年"))
    for title,time in south_members:member(w,south,title,time,i,comp,f"{title}属于南宋贴职体系。","编制")
    w.commit()

def entry613_618():
    i=613;z=Q(i);w=W(i);e=fe(w,"集贤殿修撰")
    for time in ("北宋元祐元年三月二十八日","北宋元符二年十一月三日","北宋政和五年四月十日"):
        t=ft(w,e,time);mark(w,t,i,z,"专条补证集贤殿修撰作为贴职的置、等、改。",grade="正六品")
    w.commit()
    i=614;h=Q(i,"职源");duty=Q(i,"职能");grade=Q(i,"品位");w=W(i);e=fe(w,"集英殿修撰");t=ft(w,e,"北宋政和六年九月十七日");mark(w,t,i,h,"专条补证始置。",grade="正六品",k="职源");ac(w,"Timepoints",t,i,duty,"补证南宋外补地方官用途。","职能",note="职能");ac(w,"Timepoints",t,i,grade,"补证贴职最高等、正六品。","品位",note="品位");w.commit()
    i=615;h=Q(i,"职源");duty=Q(i,"职能");grade=Q(i,"品位");w=W(i);e=fe(w,"右文殿修撰");t=ft(w,e,"北宋政和五年四月十日");mark(w,t,i,h,"专条补证由集贤殿修撰改名。",grade="从六品",k="职源");ac(w,"Timepoints",t,i,duty,"补证文臣庶官外任带职。","职能",note="职能");ac(w,"Timepoints",t,i,grade,"补证从六品及高等贴职序位。","品位",note="品位");w.commit()
    i=616;z=Q(i);w=W(i);e=en(w,"殿撰","官职",i,z,"原文明载为三个不同修撰贴职的共同省称。");g=tp(w,e,"宋代（未载具体年月）","集贤殿、集英殿、右文殿三修撰共同省称",i,z,"贴职修撰统称","建殿撰共同省称节点。")
    for title,time in (("集贤殿修撰","北宋元祐元年三月二十八日"),("集英殿修撰","北宋政和六年九月十七日"),("右文殿修撰","北宋政和五年四月十日")):member(w,g,title,time,i,z,f"{title}可共同省称殿撰。")
    w.commit()
    i=617;h=Q(i,"职源");duty=Q(i,"职能");grade=Q(i,"品位");w=W(i);e=fe(w,"秘阁修撰");t=ft(w,e,"北宋政和六年九月十七日");mark(w,t,i,h,"专条补证创置。",grade="从六品",k="职源");ac(w,"Timepoints",t,i,duty,"补证用于秘书省官资深者。","职能",note="职能");ac(w,"Timepoints",t,i,grade,"补证从六品及高等贴职序位。","品位",note="品位");w.commit()
    i=618;z=Q(i);w=W(i);e=en(w,"贴职修撰","官职",i,z,"原文明载为三种修撰贴职总名。");g=tp(w,e,"北宋政和六年九月十七日以后","秘阁、右文殿、集英殿修撰总名",i,z,"贴职修撰统称","建贴职修撰总称节点。")
    for title,time in (("秘阁修撰","北宋政和六年九月十七日"),("右文殿修撰","北宋政和五年四月十日"),("集英殿修撰","北宋政和六年九月十七日")):member(w,g,title,time,i,z,f"{title}为贴职修撰实例。")
    w.commit()

def simple_direct(i,title,time,grade):
    z=Q(i);w=W(i);e=fe(w,title);t=ft(w,e,time);mark(w,t,i,z,"专条补证该直阁列为贴职、品位、序次及外任用途。",grade=grade);w.commit()

def entry619_630():
    i=619;h=Q(i,"沿革");duty=Q(i,"职能");grade=Q(i,"品位");w=W(i);e=fe(w,"直龙图阁");start=ft(w,e,"北宋大中祥符九年十月二十一日");t=tp(w,e,"北宋元祐六年","本条记复六等馆职后列为贴职",i,h,"贴职","建元祐六年复列贴职节点。","沿革",attr_grade="正七品",chain="none");generic=ft(w,e,"宋代（未载具体年月）");chain(w,[start,t,generic],"将直龙图阁元祐复列贴职节点插入始置与总述节点之间。");ac(w,"Timepoints",t,i,duty,"补证文臣庶官外任贴职与升待制台基。","职能",note="职能");ac(w,"Timepoints",t,i,grade,"补证正七品、诸直阁贴职之首。","品位",note="品位",conflict_flag=1);group=fe(w,"贴职");rel(w,ft(w,group,"北宋元祐元年二月"),start,"统称与实例",i,h,"本条另记元祐六年复列贴职。","沿革",citation_kw={"conflict_flag":1,"note":"第612条据元祐元年六等编制已列直龙图阁；本条作元祐六年。"});w.commit()
    simple_direct(620,"直天章阁","北宋政和六年九月十七日","正七品")
    simple_direct(621,"直宝文阁","北宋政和六年九月十七日","正七品")
    simple_direct(622,"直显谟阁","北宋政和六年九月十七日","从七品")
    simple_direct(623,"直徽猷阁","北宋政和六年九月十七日","从七品")
    simple_direct(624,"直敷文阁","南宋绍兴十年五月十一日","从七品")
    simple_direct(625,"直焕章阁","南宋淳熙十五年十一月九日","从七品")
    simple_direct(626,"直华文阁","南宋庆元二年五月十五日","从七品")
    simple_direct(627,"直宝谟阁","南宋嘉泰二年八月十二日",None)
    simple_direct(628,"直宝章阁","南宋宝庆二年十月二日",None)
    simple_direct(629,"直显文阁","南宋咸淳元年六月十八日",None)
    i=630;z=Q(i);w=W(i);e=fe(w,"直秘阁");t=ft(w,e,"南宋嘉定十五年");mark(w,t,i,z,"专条补证南宋直秘阁为贴职末等、正八品及外任用途。",grade="正八品");w.commit()

def main():entry611();entry612();entry613_618();entry619_630()
if __name__=="__main__":main()
