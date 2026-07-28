#!/usr/bin/env python3
"""提取 chapter2t4 第451–470条：群牧司属官、行司、提点司与估马司。"""
import json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get("SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db"))

def load(i):
    with sqlite3.connect(DICT_DB) as c:
        r = c.execute("select title,page,text,fields from chapter2t4 where id=?", (i,)).fetchone()
    return {"title": r[0], "page": r[1], "text": r[2] or "", "fields": json.loads(r[3] or "{}")}

F = {i: load(i) for i in range(451, 471)}
def W(i): return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])
def C(i): return f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
def entity(w, title, typ, q, d): return w.entity(title, typ, d, quotation=q)
def cite(w, table, rid, i, q, d, **kw): return w.citation(table, rid, C(i), q, d, **kw)
def tp(w, eid, time, event, i, q, cat, d, citation_kw=None, **kw):
    tid = w.timepoint(eid, time, event, d, q, attr_category=cat, **kw)
    cite(w, "Timepoints", tid, i, q, d, **(citation_kw or {})); return tid
def rel(w, a, b, kind, i, q, d, **kw):
    rid = w.relationship(a, b, kind, d, q, **kw); cite(w, "Relationships", rid, i, q, d); return rid
def node(w, title, time, typ=None):
    e = w.find_entity(title, typ); assert e, title
    t = w.find_timepoint(e, time); assert t, (title, time)
    return e, t
def chain(w, tids, d):
    assert len(tids) == len(set(tids))
    for n, tid in enumerate(tids):
        w.relink(tid, d, prev_id=tids[n-1] if n else None, succ_id=tids[n+1] if n+1 < len(tids) else None)

def group_node(w, time="北宋咸平三年九月十六日"):
    return node(w, "群牧司", time, "机构")[1]

def entry451_457():
    i=451; z=F[i]["text"]; h=F[i]["fields"]["职源与沿革"]; duty=F[i]["fields"]["职掌"]; rank=F[i]["fields"]["品位"]; w=W(i)
    e=entity(w,F[i]["title"],"官职",z,"本条明载同群牧制置使为差遣。")
    a=tp(w,e,"北宋皇祐元年九月二十一日","见置，为群牧制置使之副贰兼职",i,h,"马政差遣","建同群牧制置使见置节点。",chain="none",attr_officer_type="宣徽使、节度使")
    b=tp(w,e,"北宋熙宁元年以后","不置",i,h,"马政差遣","建同群牧制置使停置节点。",chain="none")
    chain(w,[a,b],"连接同群牧制置使见置与停置节点。")
    cite(w,"Timepoints",a,i,duty,"补证同群牧制置使与正使同职掌但属兼职。",note="职掌")
    cite(w,"Timepoints",a,i,rank,"补证任官资格及位次。",note="品位")
    rel(w,group_node(w),a,"编制隶属",i,F[i]["fields"]["编制"],"同群牧制置使为群牧司不常置的副贰长官。",staff_type="官")
    w.commit()

    i=452; z=F[i]["text"]; h=F[i]["fields"]["职源与沿革"]; duty=F[i]["fields"]["职掌"]; rank=F[i]["fields"]["品位"]; w=W(i)
    e=w.find_entity("群牧使","官职") or entity(w,"群牧使","官职",z,"本条明载群牧使为差遣。")
    renamed=w.find_timepoint(e,"北宋景德二年七月三日"); assert renamed
    start=tp(w,e,"北宋景德二年七月四日","始置，为群牧司长官，专领本司公事",i,h,"马政差遣","建群牧使正式始置节点。",chain="none")
    change=tp(w,e,"北宋熙宁九年九月十六日","定以枢密都承旨兼群牧使",i,rank,"马政差遣","建群牧使任官制度变更节点。",chain="none",attr_officer_type="枢密都承旨")
    end=tp(w,e,"北宋元丰五年五月一日","随群牧司废罢",i,h,"马政差遣","建群牧使废罢节点。",chain="none")
    chain(w,[renamed,start,change,end],"连接群牧使改称、始置、任官制度变化和废罢节点。")
    cite(w,"Timepoints",start,i,duty,"补证群牧使为群牧司长官并专决事务。",note="职掌")
    rel(w,group_node(w),start,"编制隶属",i,duty,"群牧使为群牧司长官。",staff_quota=1,staff_type="官")
    w.commit()

    i=453; z=F[i]["text"]; w=W(i); e=entity(w,F[i]["title"],"官职",z,"本条明载同群牧使为编制外差遣。")
    a=tp(w,e,"北宋皇祐元年六月二十八日","始置，为群牧使编制外差遣",i,z,"马政差遣","建同群牧使始置节点。",chain="none",attr_officer_type="翰林学士")
    b=tp(w,e,"北宋至和元年七月八日","权增一员，后不为例",i,z,"马政差遣","建同群牧使权增一员节点。",chain="none",attr_officer_type="龙图阁直学士")
    chain(w,[a,b],"连接同群牧使始置与权增节点。")
    rel(w,group_node(w),a,"编制隶属",i,z,"同群牧使为群牧使编制外差遣。",staff_type="官")
    w.commit()

    i=454; z=F[i]["text"]; h=F[i]["fields"]["职源与沿革"]; duty=F[i]["fields"]["职掌"]; w=W(i)
    e=entity(w,F[i]["title"],"官职",z,"本条明载勾当制置群牧司事为差遣。")
    a=tp(w,e,"北宋咸平三年九月","与制置群牧使同时置，按察本司公事",i,h,"马政差遣","建勾当制置群牧司事始置节点。",chain="none",attr_officer_type="内侍班院左班副都知")
    b=tp(w,e,"北宋景德二年七月三日","去制置之号，改为群牧副使",i,h,"马政差遣","建勾当制置群牧司事改称节点。",chain="none")
    chain(w,[a,b],"连接勾当制置群牧司事置改节点。")
    cite(w,"Timepoints",a,i,duty,"补证按察本司公事的职掌。",note="职掌")
    rel(w,group_node(w),a,"编制隶属",i,F[i]["fields"]["品位"],"勾当制置群牧司事为位次于制置使的群牧司属官。",staff_type="官")
    w.commit()

    i=455; z=F[i]["text"]; h=F[i]["fields"]["职源与沿革"]; duty=F[i]["fields"]["职掌"]; rank=F[i]["fields"]["品位"]; comp=F[i]["fields"]["编制"]; w=W(i)
    e=entity(w,F[i]["title"],"官职",z,"本条明载群牧副使为差遣。")
    start=tp(w,e,"北宋景德二年七月三日","始置，为群牧司副长官，专决本司小事",i,h,"马政差遣","建群牧副使始置节点。",chain="none")
    change=tp(w,e,"北宋熙宁九年七月十六日","定以枢密副都承旨兼群牧副使",i,rank,"马政差遣","建群牧副使任官制度变更节点。",chain="none",attr_officer_type="枢密副都承旨")
    end=tp(w,e,"北宋元丰五年五月一日","随群牧司废罢",i,h,"马政差遣","建群牧副使废罢节点。",chain="none")
    chain(w,[start,change,end],"连接群牧副使置罢与任官变化节点。")
    cite(w,"Timepoints",start,i,duty,"补证群牧副使职掌。",note="职掌")
    rel(w,group_node(w),start,"编制隶属",i,comp,"群牧司立定副使一员为额。",staff_quota=1,staff_type="官")
    old=node(w,"勾当制置群牧司事","北宋景德二年七月三日","官职")[1]
    rel(w,old,start,"前后演变",i,h,"群牧副使由勾当制置群牧司事改称。")
    w.commit()

    for i,title,start_time,end_time,officer,quota in [
        (456,"群牧都监","北宋景德四年八月十二日","北宋元丰五年五月一日","诸司使以上",None),
        (457,"群牧判官","北宋景德二年七月以前","北宋元丰五年五月一日","京官或朝官",None)]:
        z=F[i]["text"]; h=F[i]["fields"]["职源与沿革"]; duty=F[i]["fields"]["职掌"]; comp=F[i]["fields"]["编制"]; w=W(i)
        e=entity(w,title,"官职",z,f"本条明载{title}为差遣。")
        a=tp(w,e,start_time,"见置，巡按诸州马坊监并点检监察国马",i,h,"马政差遣",f"建{title}见置节点。",chain="none",attr_officer_type=officer)
        b=tp(w,e,end_time,"随群牧司废罢",i,h,"马政差遣",f"建{title}废罢节点。",chain="none")
        chain(w,[a,b],f"连接{title}置罢节点。")
        cite(w,"Timepoints",a,i,duty,f"补证{title}巡按点检职掌。",note="职掌")
        rel(w,group_node(w),a,"编制隶属",i,comp,f"{title}为群牧司属官。",staff_quota=quota,staff_type="官")
        w.commit()

def entry458_461():
    i=458; z=F[i]["text"]; w=W(i); e=entity(w,F[i]["title"],"官职",z,"本条明载权群牧判官为资序未足正判官者所带差遣。")
    t=tp(w,e,"北宋皇祐三年八月","定资序未足者带‘权’字",i,z,"马政差遣","建权群牧判官资序制度节点。",attr_officer_type="未足正群牧判官资序者")
    rel(w,group_node(w),t,"编制隶属",i,z,"权群牧判官为群牧司判官的权职层级。",staff_type="官")
    w.commit()

    i=459; z=F[i]["text"]; w=W(i); e=entity(w,F[i]["title"],"官职",z,"本条明载权发遣群牧判官公事为差遣。")
    t=tp(w,e,"北宋熙宁十年七月三日","见置，资序更浅者带权发遣，并主管群牧行司",i,z,"马政差遣","建权发遣群牧判官公事见置节点。",attr_officer_type="资序未及权群牧判官者")
    w.commit()

    i=460; z=F[i]["text"]; w=W(i); e=entity(w,F[i]["title"],"官职",z,"本条将兼管内群牧事的知州、知军定义为通称差遣。")
    t=tp(w,e,"北宋咸平三年十月","令有监牧处知州、知军、通判兼管内群牧事",i,z,"地方马政兼差","建同群牧事知州、军制度节点。",attr_officer_type="知州、知军、通判")
    w.commit()

    i=461; z=F[i]["text"]; h=F[i]["fields"]["职源与沿革"]; duty=F[i]["fields"]["职掌"]; comp=F[i]["fields"]["编制"]; w=W(i)
    e=entity(w,F[i]["title"],"机构",z,"本条明载群牧行司为隶群牧司的官署。")
    a=tp(w,e,"北宋熙宁十年七月三日","始置，往来秦州、凤翔府督办买马并兼领同州沙苑监",i,h,"马政行司机构","建群牧行司始置节点。",chain="none")
    b=tp(w,e,"北宋元丰三年四月二十一日","废罢，改为提举买马监牧司",i,h,"马政行司机构","建群牧行司改罢节点。",chain="none")
    chain(w,[a,b],"连接群牧行司置改节点。")
    cite(w,"Timepoints",a,i,duty,"补证群牧行司督办买马职掌。",note="职掌")
    rel(w,group_node(w),a,"上下级机构",i,z,"群牧行司明载隶群牧司。")
    officer=node(w,"权发遣群牧判官公事","北宋熙宁十年七月三日","官职")[1]
    rel(w,a,officer,"编制隶属",i,comp,"群牧行司由权发遣群牧判官公事总领。",staff_quota=1,staff_type="官")
    se=entity(w,"提举买马监牧司","机构",h,"原文明载群牧行司改为提举买马监牧司。")
    st=tp(w,se,"北宋元丰三年四月二十一日","由群牧行司改置",i,h,"马政机构","建提举买马监牧司承接节点。")
    rel(w,b,st,"前后演变",i,h,"群牧行司罢后改为提举买马监牧司。")
    w.commit()

def inspection_office(i,title,side,transition_time):
    z=F[i]["text"]; w=W(i); e=entity(w,title,"机构",z,f"本条明载{title}为官署。")
    first=tp(w,e,"北宋前期（未载具体年月）",f"隶群牧司，纠按{side}诸牧马坊监事",i,z,"马政巡察机构",f"建{title}隶群牧司节点。",chain="none")
    second=tp(w,e,transition_time,f"改隶兵部驾部，继续纠按{side}诸牧监",i,z,"马政巡察机构",f"建{title}改隶驾部节点。",chain="none")
    end=tp(w,e,"北宋绍圣四年","废罢",i,z,"马政巡察机构",f"建{title}废罢节点。",chain="none")
    chain(w,[first,second,end],f"连接{title}隶属变化与废罢节点。")
    rel(w,group_node(w),first,"上下级机构",i,z,f"{title}在元丰改制前隶群牧司。")
    drive=w.find_entity("驾部","机构"); assert drive
    dt=tp(w,drive,transition_time,f"接管{title}",i,z,"兵部属司",f"建驾部接管{title}节点。")
    rel(w,dt,second,"上下级机构",i,z,f"{title}元丰改制后隶兵部驾部。")
    w.commit()

def entry462_465():
    inspection_office(462,"提点左厢诸监司","河北","北宋（未载改隶具体年月）")
    i=463; z=F[i]["text"]; alias=F[i]["fields"]["简称"]; w=W(i); e=entity(w,F[i]["title"],"官职",z,"本条明载提点左厢诸监公事为差遣。")
    t=tp(w,e,"北宋明道元年（见任）","纠察左厢河北诸坊监牧事",i,alias,"马政差遣","据简称引文中的明道元年见任信息建节点。",attr_officer_type="诸司使")
    office=node(w,"提点左厢诸监司","北宋前期（未载具体年月）","机构")[1]
    rel(w,office,t,"编制隶属",i,z,"提点左厢诸监公事为左厢提点司主管差遣。",staff_quota=1,staff_type="官")
    w.commit()
    inspection_office(464,"提点右厢诸监司","河南","北宋元丰五年改制后")
    i=465; z=F[i]["text"]; w=W(i); e=entity(w,F[i]["title"],"官职",z,"本条明载提点右厢诸监公事为差遣。")
    t=tp(w,e,"北宋前期（未载具体年月）","纠察河南诸牧马监公事",i,z,"马政差遣","建提点右厢诸监公事无确年节点。")
    office=node(w,"提点右厢诸监司","北宋前期（未载具体年月）","机构")[1]
    rel(w,office,t,"编制隶属",i,z,"提点右厢诸监公事为右厢提点司主管差遣。",staff_quota=1,staff_type="官")
    w.commit()

def entry466_469():
    i=466; z=F[i]["text"]; h=F[i]["fields"]["职源与沿革"]; duty=F[i]["fields"]["职掌"]; w=W(i)
    e=entity(w,F[i]["title"],"机构",z,"本条明载在京估马司为监当局。")
    a=tp(w,e,"北宋咸平元年十一月三日","始置于开封建隆坊，掌验收定价进京纲马",i,h,"马政监当机构","建在京估马司始置节点。",chain="none")
    b=tp(w,e,"北宋嘉祐三年闰十二月二十五日","废罢，归群牧司兼领",i,h,"马政监当机构","建在京估马司废罢节点。",chain="none")
    chain(w,[a,b],"连接在京估马司置罢节点。")
    cite(w,"Timepoints",a,i,duty,"补证估马司验马定价职掌。",note="职掌")
    ge=node(w,"群牧司","北宋咸平三年九月十六日","机构")[0]
    gt=tp(w,ge,"北宋嘉祐三年闰十二月二十五日","兼领原在京估马司职事",i,h,"马政机构","建群牧司兼领估马事务节点。",chain="none")
    gstart=group_node(w); gend=node(w,"群牧司","北宋元丰五年五月一日","机构")[1]
    chain(w,[gstart,gt,gend],"将兼领估马司节点插入群牧司时间链。")
    rel(w,b,gt,"前后演变",i,h,"在京估马司罢后由群牧司兼领。")
    w.commit()

    i=467; z=F[i]["text"]; w=W(i); e=entity(w,F[i]["title"],"官职",z,"本条明载勾当估马司公事为差遣。")
    t=tp(w,e,"北宋前期（未载具体年月）","掌估马司公事",i,z,"马政差遣","建勾当估马司公事无确年节点。",attr_officer_type="诸司使")
    office=node(w,"在京估马司","北宋咸平元年十一月三日","机构")[1]
    rel(w,office,t,"编制隶属",i,z,"估马司设勾当官一人。",staff_quota=1,staff_type="官")
    w.commit()

    i=468; z=F[i]["text"]; w=W(i); e=entity(w,F[i]["title"],"机构",z,"本条明载陕西估马司为监当局。")
    t=tp(w,e,"北宋嘉祐五年八月二十八日","奉诏设置",i,z,"马政监当机构","建陕西估马司始置节点。")
    pe=entity(w,"提举陕西买马监牧司","机构",z,"原文明载陕西估马司隶提举陕西买马监牧司。")
    pt=tp(w,pe,"北宋嘉祐五年八月二十八日","统辖陕西估马司",i,z,"马政机构","建提举陕西买马监牧司统辖节点。")
    rel(w,pt,t,"上下级机构",i,z,"陕西估马司明载隶提举陕西买马监牧司。")
    w.commit()

    i=469; z=F[i]["text"]; w=W(i); e=entity(w,F[i]["title"],"官职",z,"本条明载典吏为估马司公吏。")
    t=tp(w,e,"北宋前期（未载具体年月）","承办估马司事务",i,z,"马政吏职","建估马司典吏无确年节点。")
    office=node(w,"在京估马司","北宋咸平元年十一月三日","机构")[1]
    rel(w,office,t,"编制隶属",i,z,"典吏明载隶估马司。",staff_type="吏")
    w.commit()

def entry470():
    i=470; z=F[i]["text"]; w=W(i); e=entity(w,"马官","官职",z,"本条将各类牧马官员明确界定为马官通称。")
    general=tp(w,e,"宋代（未载具体年月）","左右骐骥院及内外诸坊、务、监牧马官员的通称",i,z,"马政官员统称","建马官统称节点。")
    for title in ("监官","提举官","勾当官","监牧使","提点官"):
        ie=w.find_entity(title,"官职") or entity(w,title,"官职",z,f"本条将{title}列为马官实例。")
        it=w.find_timepoint(ie,"宋代（未载具体年月）") or tp(w,ie,"宋代（未载具体年月）","牧养国马机构官员",i,z,"马政差遣",f"建{title}作为马官实例的节点。")
        rel(w,general,it,"统称与实例",i,z,f"原文明列{title}等通称马官。")
    w.commit()

def main():
    entry451_457(); entry458_461(); entry462_465(); entry466_469(); entry470()

if __name__ == "__main__": main()
