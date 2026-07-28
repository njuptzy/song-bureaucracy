#!/usr/bin/env python3
"""提取重建后 chapter2t4 第471–490条：坊监、监牧使司与殿学士前段。"""
import json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.environ.get("SONG_ENTRY_DB",os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db"))
def load(i):
    with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return {"title":r[0],"page":r[1],"text":r[2] or "","fields":json.loads(r[3] or "{}")}
F={i:load(i) for i in range(471,491)}
def W(i):return EntryWriter(ENTRY_DB,F[i]["title"],F[i]["page"])
def C(i):return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
def entity(w,title,typ,q,d):return w.entity(title,typ,d,quotation=q)
def cite(w,table,rid,i,q,d,**kw):return w.citation(table,rid,C(i),q,d,**kw)
def tp(w,e,time,event,i,q,cat,d,citation_kw=None,**kw):
    t=w.timepoint(e,time,event,d,q,attr_category=cat,**kw);cite(w,"Timepoints",t,i,q,d,**(citation_kw or {}));return t
def rel(w,a,b,k,i,q,d,**kw):
    r=w.relationship(a,b,k,d,q,**kw);cite(w,"Relationships",r,i,q,d);return r
def node(w,title,time,typ=None):
    e=w.find_entity(title,typ);assert e,title
    t=w.find_timepoint(e,time);assert t,(title,time)
    return e,t
def chain(w,ts,d):
    assert len(ts)==len(set(ts))
    for n,t in enumerate(ts):w.relink(t,d,prev_id=ts[n-1] if n else None,succ_id=ts[n+1] if n+1<len(ts) else None)

def entry471_473():
    i=471;z=F[i]["text"];w=W(i);e=entity(w,"在外坊监","机构",z,"本条总述京师外各类牧马机构。")
    general=tp(w,e,"北宋初","京师外畜马处名称不一",i,z,"马政机构统称","建在外坊监总述节点。")
    for title in ("养马务","马务","马坊","牧马监","监","龙马监","飞龙院"):
        ie=w.find_entity(title,"机构") or entity(w,title,"机构",z,f"本条明列{title}为北宋初在外畜马机构实例。")
        it=w.find_timepoint(ie,"北宋初") or tp(w,ie,"北宋初","京师外畜马机构名目",i,z,"马政机构",f"建{title}实例节点。")
        rel(w,general,it,"统称与实例",i,z,f"{title}为在外坊监实例名目。")
    w.commit()

    i=472;z=F[i]["text"];w=W(i);e=w.find_entity("牧龙坊","机构") or entity(w,"牧龙坊","机构",z,"本条明载牧龙坊为监当局。")
    a=tp(w,e,"北宋太平兴国五年","统一诸州军牧马坊、务、监、院等名目为牧龙坊",i,z,"马政监当机构","建牧龙坊统一改名节点。",chain="none")
    b=tp(w,e,"北宋景德二年七月四日","统一改称监",i,z,"马政监当机构","建牧龙坊改监节点。",chain="none")
    chain(w,[a,b],"连接牧龙坊统一命名与改监节点。")
    w.commit()

    i=473;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职掌"];w=W(i);e=w.find_entity("监","机构") or entity(w,"监","机构",z,"本条明载监为监当局。")
    tang=tp(w,e,"唐代","太仆寺下设牧监，并有沙苑监等径称监者",i,h,"马政监当机构","建监的唐代源流节点。",chain="none")
    song=tp(w,e,"北宋初","牧马处已有沿称监者",i,h,"马政监当机构","建北宋初沿称监节点。",chain="none")
    standard=tp(w,e,"北宋景德二年七月四日","诸州军牧龙坊一律改称监并冠所在地名",i,h,"马政监当机构","建监统一命名节点。",chain="none")
    reform=tp(w,e,"北宋元丰改制后","由隶群牧司改隶太仆寺",i,z,"马政监当机构","建监改隶太仆寺节点。",chain="none")
    chain(w,[tang,song,standard,reform],"连接监的唐宋源流、统一命名与改隶节点。")
    cite(w,"Timepoints",standard,i,duty,"补证监为蓄养放牧国马之所。",note="职掌")
    old=node(w,"牧龙坊","北宋景德二年七月四日","机构")[1];rel(w,old,standard,"前后演变",i,h,"诸州牧龙坊统一改称监。")
    group=node(w,"群牧司","北宋咸平三年九月十六日","机构")[1];rel(w,group,standard,"上下级机构",i,z,"北宋监明载隶群牧司。")
    taipusi=node(w,"太仆寺","北宋元丰五年五月一日","机构")[1];rel(w,taipusi,reform,"上下级机构",i,z,"元丰后监改隶太仆寺。")
    w.commit()

def entry474_477():
    i=474;z=F[i]["text"];w=W(i);office=node(w,"监","北宋景德二年七月四日","机构")[1]
    for title in ("监牧指挥使","监牧副指挥使"):
        e=entity(w,title,"官职",z,f"本条明载{title}为监牧指挥长官。")
        t=tp(w,e,"北宋（未载具体年月）","统领诸州马监照管养马厢兵",i,z,"马政武官",f"建{title}无确年节点。")
        rel(w,office,t,"编制隶属",i,z,f"诸州马监设{title}。",staff_quota=1,staff_type="武官")
    w.commit()
    i=475;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载勾当监公事为监管牧监的差遣。")
    a=tp(w,e,"北宋（未载具体年月）","监管本监牧马公事，三年一任",i,z,"马政差遣","建勾当监公事北宋节点。",chain="none",attr_officer_type="武臣小使臣")
    b=tp(w,e,"南宋","改称主管",i,z,"马政差遣","建南宋改称主管节点。",chain="none")
    chain(w,[a,b],"连接勾当监公事北宋制度与南宋改称节点。")
    rel(w,office,a,"编制隶属",i,z,"诸监各置勾当监公事二员。",staff_quota=2,staff_type="官")
    w.commit()
    i=476;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载监主簿为诸州马监差遣。")
    t=tp(w,e,"北宋熙宁元年八月五日","令马监所在县令、县主簿同管勾监帐册及官物",i,z,"马政吏职","建监主簿同管勾制度节点。",attr_officer_type="县令、县主簿")
    rel(w,office,t,"编制隶属",i,z,"诸州马监均置监主簿。",staff_quota=1,staff_type="官")
    w.commit()
    i=477;z=F[i]["text"];w=W(i);e=entity(w,"群","机构",z,"本条明载群为牧监下的编制单位。")
    t=tp(w,e,"南宋","每监分四群，每群牝马一百、牡马二十三匹并配军兵兽医七十人",i,z,"马政编制单位","建群的南宋编制节点。")
    rel(w,office,t,"上下级机构",i,z,"群明载为牧监下编制。")
    w.commit()

def entry478_480():
    i=478;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];w=W(i);e=entity(w,F[i]["title"],"机构",z,"本条明载孳生监为隶枢密院的监当局。")
    a=tp(w,e,"北宋大中祥符二年","以同州沙苑监为孳生监，是为之始",i,h,"马政监当机构","建孳生监始置节点。",chain="none")
    b=tp(w,e,"北宋熙宁元年九月","以河南诸监为孳生监",i,h,"马政监当机构","建孳生监扩展节点。",chain="none")
    c=tp(w,e,"南宋","沿置",i,h,"马政监当机构","建孳生监南宋沿置节点。",chain="none")
    chain(w,[a,b,c],"连接孳生监始置、扩展及南宋沿置节点。")
    mi=node(w,"枢密院","宋初","机构")[1];rel(w,mi,a,"上下级机构",i,z,"孳生监明载隶枢密院。")
    w.commit()
    i=479;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"机构",z,"本条明载京畿孳生马监为监当局。")
    a=tp(w,e,"北宋元丰六年六月","始置",i,z,"马政监当机构","建京畿孳生马监始置节点。",chain="none")
    b=tp(w,e,"北宋元丰六年八月八日","废罢",i,z,"马政监当机构","按本条正文的连续纪年建元丰六年八月八日废罢节点。",chain="none",citation_kw={"conflict_flag":1,"note":"第480条另记元丰八年八月二十六日罢。"})
    c=tp(w,e,"北宋绍圣元年七月","复置畿内孳生十监",i,z,"马政监当机构","建绍圣复置节点。",chain="none")
    chain(w,[a,b,c],"连接京畿孳生马监始置、废罢与复置节点。")
    w.commit()
    i=480;z=F[i]["text"];w=W(i);e=w.find_entity("京畿孳生马监","机构");assert e
    start=tp(w,e,"北宋元丰六年六月一日","诏置十监，总称畿内牧马监",i,z,"马政监当机构","补建元丰六年六月一日确切始置节点。",chain="none")
    end=tp(w,e,"北宋元丰八年八月二十六日","废罢",i,z,"马政监当机构","按本条建八月二十六日废罢节点。",chain="none",citation_kw={"conflict_flag":1,"note":"第479条正文按连续纪年另记元丰六年八月八日罢。"})
    month=w.find_timepoint(e,"北宋元丰六年六月");day8=w.find_timepoint(e,"北宋元丰六年八月八日");restore=w.find_timepoint(e,"北宋绍圣元年七月")
    chain(w,[month,start,day8,end,restore],"并列保留两条相冲突的废罢日期并连接时间链。")
    w._br("Entities",e,"本条明言畿内牧马监即京畿孳生马监，复用实体而不建立别名实体。")
    w.commit()

def entry481_487():
    i=481;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];w=W(i);e=entity(w,F[i]["title"],"机构",z,"本条明载河南、北监牧使司为官署。")
    a=tp(w,e,"北宋熙宁元年九月十六日","河南、河北各置监牧使司，统领外州诸牧监",i,h,"马政机构","建河南北监牧使司始置节点。",chain="none")
    b=tp(w,e,"北宋熙宁八年四月二十九日","废罢",i,h,"马政机构","建河南北监牧使司废罢节点。",chain="none")
    chain(w,[a,b],"连接河南北监牧使司置罢节点。")
    cite(w,"Timepoints",a,i,duty,"补证两司统领外州牧监且外监不隶群牧司。",note="职能")
    w.commit()
    i=482;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职掌"];rank=F[i]["fields"]["品位"];comp=F[i]["fields"]["编制"];w=W(i);e=entity(w,F[i]["title"],"官职",z,"本条明载河南、北监牧使为差遣。")
    tang=tp(w,e,"唐仪凤三年","始置检校陇右诸牧监使，后又有楼烦监牧使",i,h,"马政差遣","建监牧使唐代源流节点。",chain="none")
    a=tp(w,e,"北宋熙宁元年九月十六日","始置河南监牧使、河北监牧使，分领外州马监",i,h,"马政差遣","建河南北监牧使始置节点。",chain="none",attr_officer_type="朝官")
    b=tp(w,e,"北宋熙宁八年四月二十九日","废罢",i,h,"马政差遣","建河南北监牧使废罢节点。",chain="none")
    chain(w,[tang,a,b],"连接监牧使唐代源流与北宋置罢节点。")
    cite(w,"Timepoints",a,i,duty,"补证监牧使分领外州马政职掌。",note="职掌")
    office=node(w,"河南、北监牧使司","北宋熙宁元年九月十六日","机构")[1];rel(w,office,a,"编制隶属",i,comp,"河南、河北两司各置监牧使一员。",staff_quota=2,staff_type="官")
    mi=node(w,"枢密院","北宋熙宁元年","机构")[1];rel(w,mi,a,"编制隶属",i,rank,"河南、北监牧使不隶群牧司而隶枢密院。",staff_quota=2,staff_type="官")
    w.commit()
    i=483;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职掌"];w=W(i)
    e=w.find_entity("提举陕西买马监牧司","机构");assert e
    w.conn.execute("update Entities set title=? where id=?",(F[i]["title"],e));w._br("Entities",e,"据本条正称将前条简称实体统一为提举陕西等路买马监牧司。")
    old=w.find_timepoint(e,"北宋嘉祐五年八月二十八日");assert old
    w.conn.execute("update Timepoints set event=?,quotation=? where id=?",("始以权陕西转运副使专领本路监牧及买马公事，设局置官",h,old));w._br("Timepoints",old,"据本条补全提举司始置事实。")
    cite(w,"Timepoints",old,i,h,"补证提举陕西等路买马监牧司始置。",note="职源与沿革")
    end=tp(w,e,"北宋元祐元年七月二十九日","去监牧二字，改称提举陕西等路买马司",i,h,"马政机构","建提举司改名节点。",chain="none")
    chain(w,[old,end],"连接提举陕西等路买马监牧司始置与改名节点。")
    se=entity(w,"提举陕西等路买马司","机构",h,"原文明载元祐元年后去监牧二字为正称。")
    st=tp(w,se,"北宋元祐元年七月二十九日","由提举陕西等路买马监牧司改称",i,h,"马政机构","建改称承接节点。")
    rel(w,end,st,"前后演变",i,h,"元祐元年去监牧二字改为提举陕西等路买马司。")
    cite(w,"Timepoints",old,i,duty,"补证提举司买马监牧职掌。",note="职掌")
    w.commit()
    for i,title in ((484,"提举陕西等路监牧及买马公事"),(485,"提举陕西等路买马监牧司勾当公事")):
        z=F[i]["text"];w=W(i);e=entity(w,title,"官职",z,f"本条明载{title}为差遣。")
        t=tp(w,e,"北宋嘉祐五年以后（未载具体年月）",z.split("。")[1] if "。" in z else z,i,z,"马政差遣",f"建{title}无确年节点。",attr_officer_type="京官" if i==485 else None)
        office=node(w,"提举陕西等路买马监牧司","北宋嘉祐五年八月二十八日","机构")[1]
        rel(w,office,t,"编制隶属",i,z,f"{title}为提举司属官。",staff_quota=1,staff_type="官")
        w.commit()
    i=486;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"机构",z,"本条明载提举秦凤等路买马监牧司为官司。")
    tp(w,e,"北宋熙宁年间","设置，专领秦凤等路买马、养马、起发马纲",i,z,"马政机构","建秦凤买马监牧司节点。")
    w.commit()
    i=487;z=F[i]["text"];w=W(i);e=entity(w,F[i]["title"],"机构",z,"本条明载监牧指挥为牧马军。")
    t=tp(w,e,"北宋（未载具体年月）","牧马军",i,z,"马政军队","建监牧指挥无确年节点。")
    pe=entity(w,"熙河路牧养十监","机构",z,"原文明载监牧指挥隶熙河路牧养十监。")
    pt=tp(w,pe,"北宋（未载具体年月）","统辖监牧指挥",i,z,"马政机构","建熙河路牧养十监节点。")
    rel(w,pt,t,"上下级机构",i,z,"监牧指挥明载隶熙河路牧养十监。")
    w.commit()

def entry488_490():
    i=488;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];w=W(i);e=entity(w,"殿学士","官职",z,"本条明载殿学士为诸殿大学士、学士总名。")
    t1=tp(w,e,"南朝陈","始有德教殿学士之名",i,h,"殿阁职名统称","建殿学士名源节点。",chain="none")
    t2=tp(w,e,"唐景龙二年","始置集贤殿大学士",i,h,"殿阁职名统称","建殿大学士名源节点。",chain="none")
    t3=tp(w,e,"后唐天成元年","始置端明殿学士",i,h,"殿阁职名统称","建后唐殿学士节点。",chain="none")
    song=tp(w,e,"宋代（未载具体年月）","诸殿大学士、学士的总名",i,z,"殿阁职名统称","建宋代殿学士统称节点。",chain="none")
    chain(w,[t1,t2,t3,song],"连接殿学士名源与宋代统称节点。")
    titles=("观文殿大学士","观文殿学士","资政殿大学士","资政殿学士","端明殿学士","保和殿大学士","保和殿学士","文明殿大学士","文明殿学士","紫宸殿学士","延康殿学士","宣和殿大学士","宣和殿学士")
    for title in titles:
        ie=w.find_entity(title,"官职") or entity(w,title,"官职",z,f"本条将{title}列为殿学士实例。")
        it=w.find_timepoint(ie,"宋代（未载具体年月）") or tp(w,ie,"宋代（未载具体年月）","殿学士职名",i,z,"殿阁职名",f"建{title}统称实例节点。")
        rel(w,song,it,"统称与实例",i,z,f"{title}为殿学士实例。")
    w.commit()
    i=489;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];grade=F[i]["fields"]["品位"];w=W(i);e=w.find_entity(F[i]["title"],"官职");assert e
    generic=w.find_timepoint(e,"宋代（未载具体年月）");assert generic
    start=tp(w,e,"北宋皇祐元年六月十三日","始置，供宰相离任外调带职并备顾问",i,h,"殿阁职名","建观文殿大学士始置节点。",chain="none",attr_grade="从二品")
    south=tp(w,e,"南宋","沿置",i,h,"殿阁职名","建南宋沿置节点。",chain="none",attr_grade="从二品")
    chain(w,[start,generic,south],"连接观文殿大学士始置、通期与南宋节点。")
    cite(w,"Timepoints",start,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",start,i,grade,"补证品位。",note="品位")
    w.commit()
    i=490;z=F[i]["text"];h=F[i]["fields"]["职源与沿革"];duty=F[i]["fields"]["职能"];grade=F[i]["fields"]["品位"];w=W(i);e=w.find_entity(F[i]["title"],"官职");assert e
    generic=w.find_timepoint(e,"宋代（未载具体年月）");assert generic
    start=tp(w,e,"北宋庆历八年五月八日","由紫宸殿学士改名为观文殿学士",i,h,"殿阁职名","建观文殿学士始置改名节点。",chain="none",attr_grade="正三品")
    south=tp(w,e,"南宋","沿置",i,h,"殿阁职名","建观文殿学士南宋沿置节点。",chain="none",attr_grade="正三品")
    chain(w,[start,generic,south],"连接观文殿学士始置与南宋沿置节点。")
    olde=w.find_entity("紫宸殿学士","官职");assert olde
    oldt=tp(w,olde,"北宋庆历八年五月八日","改名为观文殿学士",i,h,"殿阁职名","建紫宸殿学士改名节点。")
    rel(w,oldt,start,"前后演变",i,h,"紫宸殿学士于庆历八年改名观文殿学士。")
    cite(w,"Timepoints",start,i,duty,"补证职能。",note="职能");cite(w,"Timepoints",start,i,grade,"补证品位。",note="品位")
    w.commit()

def main():entry471_473();entry474_477();entry478_480();entry481_487();entry488_490()
if __name__=="__main__":main()
