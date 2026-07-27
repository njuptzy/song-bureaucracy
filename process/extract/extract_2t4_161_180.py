#!/usr/bin/env python3
"""提取 chapter2t4 第161–180条：枢密院、长贰与承旨司系统。"""
import json,os,sqlite3,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db")
def load(i):
    with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
    return r[0],r[1],(r[2] or "")+"\n"+"\n".join(str(v) for k,v in json.loads(r[3] or "{}").items() if not k.startswith("_"))
F={i:load(i) for i in range(161,181)}
def q(i,s):assert s in F[i][2],f"#{i} 不含：{s}";return s
def W(i):return EntryWriter(ENTRY_DB,F[i][0],F[i][1])
def C(i):return f"《宋代官制辞典》第{F[i][1]}页“{F[i][0]}”条"
def ac(w,t,r,i,z,d,**kw):return w.citation(t,r,C(i),z,d,**kw)
def en(w,n,y,i,z,d):return w.entity(n,y,d,quotation=z)
def tp(w,e,t,v,i,z,c,d,**kw):r=w.timepoint(e,t,v,d,z,attr_category=c,**kw);ac(w,"Timepoints",r,i,z,d);return r
def rel(w,s,o,k,i,z,d,**kw):r=w.relationship(s,o,k,d,z,**kw);ac(w,"Relationships",r,i,z,d);return r
def node(w,n,t,y=None):e=w.find_entity(n,y);assert e,f"缺实体 {n}";r=w.find_timepoint(e,t);assert r,f"{n}缺{t}";return e,r
def chain(w,ids,d):
    assert all(ids)
    for j,r in enumerate(ids):w.relink(r,d,prev_id=ids[j-1] if j else None,succ_id=ids[j+1] if j+1<len(ids) else None)

def entry161():
    i=161;qn=q(i,"官署名");qt=q(i,"唐末始有枢密院之称");ql=q(i,"后梁开平元年（907）五月，改枢密院为崇政院");qh=q(i,"后唐同光元年（923）十月，依旧称枢密院");qs=q(i,"宋朝沿置");qd=q(i,"宋朝枢密院与中书号称二府，掌兵符、武官选拔除授、兵防边备及军师屯戍之政令");qstaff=q(i,"枢密院长贰有枢密使则置枢密副使，有知院则置同知院，资浅则称签书（署）枢密院事");qxi=q(i,"熙宁元年始并置");qyuan=q(i,"元丰官制罢枢密使、副，至绍兴七年又复置");qsub=q(i,"下设枢密院承旨司");w=W(i)
    office=en(w,"枢密院","机构",i,qn,"辞典明载为官署。");tang=tp(w,office,"唐末","始有枢密院之称",i,qt,"官署名","建唐末机构节点。");liang=tp(w,office,"后梁开平元年五月","改为崇政院",i,ql,"官署名","建后梁改名终结节点。")
    chong=en(w,"崇政院","机构",i,ql,"本条明确枢密院后梁改名机构。");chong_start=tp(w,chong,"后梁开平元年五月","由枢密院改置",i,ql,"官署名","建后梁改置节点。");chong_end=tp(w,chong,"后唐同光元年十月","复称枢密院",i,qh,"官署名","建后唐终结节点。");houtang=tp(w,office,"后唐同光元年十月","由崇政院复称枢密院",i,qh,"官署名","建后唐复名节点。");song=tp(w,office,"宋初","沿置，掌兵符、武官选授及兵防军政",i,qs,"官署名","建宋初沿置节点。");ac(w,"Timepoints",song,i,qd,"补充宋代职掌。",note="职掌")
    xining=tp(w,office,"北宋熙宁元年","枢密使与知院事始并置",i,qxi,"官署名","建长官并置节点。");yuan=tp(w,office,"北宋元丰四年","新官制罢枢密使、副使",i,qyuan,"官署名","建元丰改制节点。");shao=tp(w,office,"南宋绍兴七年","复置枢密使、副使",i,qyuan,"官署名","建绍兴复置节点。")
    rel(w,liang,chong_start,"前后演变",i,ql,"枢密院改为崇政院。");rel(w,chong_end,houtang,"前后演变",i,qh,"崇政院复称枢密院。")
    for n in ("枢密使","枢密副使","知枢密院事","同知枢密院事","签署枢密院事"):
        p=en(w,n,"官职",i,qstaff,f"枢密院长贰编制明确列{n}。");ph=w.ensure_placeholder(p,"总条无统一设置时间，待专条复用。");ac(w,"Timepoints",ph,i,qstaff,"总条补充长贰配置。",note="长贰通制");rel(w,song,ph,"编制隶属",i,qstaff,f"枢密院长贰包括{n}。",staff_type="官")
    sub=en(w,"枢密院承旨司","机构",i,qsub,"总条明确下设承旨司。");subph=w.ensure_placeholder(sub,"总条无始置时间，待专条复用。");ac(w,"Timepoints",subph,i,qsub,"总条补充下设承旨司。");rel(w,song,subph,"上下级机构",i,qsub,"枢密院下设承旨司。")
    chain(w,[tang,liang,houtang,song,xining,yuan,shao],"按唐末、五代、宋初及宋代改制排序");chain(w,[chong_start,chong_end],"按后梁改置、后唐复名排序");w.commit()

def entry162():
    i=162;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,"枢密行府","机构",i,z,"辞典明载为枢密院驻外机构。");ranges=(("南宋绍兴四年十一月","南宋绍兴五年二月"),("南宋绍兴九年四月","南宋绍兴九年九月"),("南宋绍兴十一年五月","南宋绍兴十二年正月"),("南宋绍兴三十一年十月","南宋绍兴三十二年五月"),("南宋乾道三年六月","南宋乾道四年三月"));ids=[]
    for a,b in ranges:
        s=tp(w,e,a,"开枢密行府",i,z,"驻外机构名","建行府开设节点。",chain="none");t=tp(w,e,b,"本次枢密行府结束",i,z,"驻外机构名","建行府结束节点。",chain="none");ids.extend((s,t))
    _,parent=node(w,"枢密院","南宋绍兴七年","机构")
    for s,_ in zip(ids[::2],ids[1::2]):rel(w,parent,s,"上下级机构",i,z,"枢密行府为枢密院临时驻外机构。")
    chain(w,ids,"按五次行府起止排序");w.commit()

def entry163():
    i=163;qn=q(i,"职事官名");qt=q(i,"唐宪宗元和中（806—820）始置枢密使");qs=q(i,"北宋初沿置枢密使");qy=q(i,"神宗元丰四年（1081）正月罢置");qr=q(i,"南宋高宗绍兴七年（1137）正月复置枢密使");qd=q(i,"为枢密院长官，佐皇帝，执兵政");w=W(i);e=w.find_entity("枢密使","官职");a=tp(w,e,"唐宪宗元和中","始置枢密使",i,qt,"职事官名","建唐代职源节点。");b=tp(w,e,"北宋初","沿置，为枢密院长官，佐皇帝执兵政",i,qs,"职事官名","建北宋沿置节点。");ac(w,"Timepoints",b,i,qd,"补充职掌。",note="职掌");c=tp(w,e,"北宋元丰四年正月","罢枢密使",i,qy,"职事官名","建罢置节点。");d=tp(w,e,"南宋绍兴七年正月","复置，官品从一品",i,qr,"职事官名","建复置节点。",attr_grade="从一品");_,o=node(w,"枢密院","宋初","机构");rel(w,o,b,"编制隶属",i,qd,"枢密使为枢密院长官。",staff_type="官");broad=w.find_timepoint(e,"宋代");chain(w,[a,b,c,d,broad],"按专条时间排序并保留宋代总述节点");w.commit()
def entry164():
    i=164;z=F[i][2].split("\n",1)[0];w=W(i);_,p=node(w,"枢密使","北宋初","官职");ac(w,"Timepoints",p,i,z,"补充北宋前期文臣任枢密使多加检校太尉的制度事实。",note="任职形态；枢密太尉仅为称谓，不另建实体");w.commit()
def entry165():
    # 纯粹说明“枢使”为枢密使寄理称，四表不存别称关系。
    return

def entry166():
    i=166;z=F[i][2];w=W(i);e=w.find_entity("枢密副使","官职");a=tp(w,e,"后晋天福间","始见枢密副使",i,q(i,"至后晋天福间始见有枢密副使之设"),"职事官名","建五代职源节点。");b=tp(w,e,"北宋建隆元年","置枢密副使，副佐枢密使协理院事",i,q(i,"北宋建隆元年(960)即置枢密副使"),"职事官名","建北宋始置节点。");c=tp(w,e,"北宋元丰四年正月","罢枢密副使",i,q(i,"元丰四年正月罢枢密副使"),"职事官名","建罢置节点。");d=tp(w,e,"南宋绍兴七年","复置枢密副使",i,q(i,"南宋绍兴七年复置"),"职事官名","建复置节点。",attr_grade="正二品");ac(w,"Timepoints",b,i,q(i,"枢密使副佐，协理枢密院事"),"补充职掌。",note="职掌");_,o=node(w,"枢密院","宋初","机构");rel(w,o,b,"编制隶属",i,z,"枢密副使为枢密院副贰。",staff_type="官");broad=w.find_timepoint(e,"宋代");chain(w,[a,b,c,d,broad],"按专条时间排序并保留宋代总述节点");w.commit()
def entry167():
    i=167;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,"判枢密院事","官职",i,z,"辞典明载为职事官。");a=tp(w,e,"北宋庆历二年七月十七日","特置，处理西北边事",i,z,"职事官名","建特置节点。");b=tp(w,e,"北宋庆历二年九月五日","因判名太重而罢",i,z,"职事官名","建罢废节点。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,a,"编制隶属",i,z,"判枢密院事处理本院边事。",staff_type="官");chain(w,[a,b],"按特置、罢废排序");w.commit()
def entry168():
    i=168;w=W(i);e=w.find_entity("知枢密院事","官职");a=tp(w,e,"后晋天福元年","始置知枢密院事",i,q(i,"后晋天福元年（936），始置知枢密院事"),"职事官名","建五代职源节点。");b=tp(w,e,"北宋淳化二年九月","初设，为枢密院长官",i,q(i,"北宋淳化二年（991）九月初设"),"职事官名","建北宋始置节点。");c=tp(w,e,"北宋元丰四年十一月","独以知院事为长官，编制一员",i,q(i,"元丰四年十一月，罢枢密使，即独以知院事为长官"),"职事官名","建元丰改制节点。",attr_grade="正二品");d=tp(w,e,"南宋绍兴七年后","与枢密使交错或并置",i,q(i,"南宋绍兴七年后，又与枢密使交错或并置"),"职事官名","建南宋节点。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,b,"编制隶属",i,q(i,"为枢密院长官，佐皇帝掌兵政"),"知院事为枢密院长官。",staff_type="官");broad=w.find_timepoint(e,"宋代");chain(w,[a,b,c,d,broad],"按专条时间排序并保留宋代总述节点");w.commit()
def entry169():
    i=169;w=W(i);e=w.find_entity("同知枢密院事","官职");a=tp(w,e,"北宋淳化二年九月八日","始置，为枢密院副长官",i,q(i,"淳化二年(991)九月八日始置"),"职事官名","建始置节点。",attr_grade="正二品");b=tp(w,e,"北宋元丰四年十一月","专以同知枢密院事为副贰",i,q(i,"元丰四年十一月专以同知枢密院事为副贰"),"职事官名","建元丰改制节点。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,a,"编制隶属",i,q(i,"佐枢长协理枢密院事"),"同知院事为枢密院副贰。",staff_type="官");broad=w.find_timepoint(e,"宋代");chain(w,[a,b,broad],"按专条时间排序并保留宋代总述节点");w.commit()
def entry170():
    i=170;w=W(i);e=w.find_entity("签署枢密院事","官职");a=tp(w,e,"北宋太平兴国四年正月十三日","始置，为枢密院副贰",i,q(i,"太平兴国四年(979)正月十三日始置"),"职事官名","建始置节点。");b=tp(w,e,"北宋治平元年","改为签书枢密院事",i,q(i,"英宗赵曙于1064年即位后，签署枢密院事改为签书枢密院事"),"职事官名","建改名节点。");c=tp(w,e,"北宋元丰新制","罢签署枢密院事",i,q(i,"元丰新制罢"),"职事官名","建罢置节点。");d=tp(w,e,"北宋元祐三年","复置",i,q(i,"元祐三年复置"),"职事官名","建复置节点。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,a,"编制隶属",i,q(i,"枢密院副贰，协理枢密院事"),"签署院事为枢密院副贰。",staff_type="官");chain(w,[a,b,c,d],"按始置、改名、罢复排序");w.commit()
def entry171():
    i=171;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,"同签署枢密院事","官职",i,z,"辞典明载为职事官。");p=tp(w,e,"北宋太平兴国八年十一月二十一日","始置；二员并置时带同字",i,z,"职事官名","建始置节点。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,p,"编制隶属",i,z,"同签署枢密院事为本院副贰。",staff_type="官");w.commit()
def entry172():
    i=172;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,"签书枢密院事","官职",i,z,"辞典明载为签署院事改名。");p=tp(w,e,"北宋治平元年","由签署枢密院事改置",i,z,"职事官名","建改名后继节点。");_,src=node(w,"签署枢密院事","北宋治平元年","官职");rel(w,src,p,"前后演变",i,z,"签署枢密院事改为签书枢密院事。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,p,"编制隶属",i,z,"签书枢密院事为枢密院副贰。",staff_type="官");w.commit()
def entry173():
    i=173;w=W(i);e=en(w,"同签书枢密院事","官职",i,q(i,"职事官名"),"辞典明载为职事官。");a=tp(w,e,"北宋治平三年四月一日","始置，为枢密院副贰",i,q(i,"宋治平三年（1066）四月一日始置"),"职事官名","建始置节点。");b=tp(w,e,"北宋治平四年九月","罢",i,q(i,"次年九月即罢"),"职事官名","建罢置节点。");c=tp(w,e,"北宋政和七年二月","复置",i,q(i,"政和七年二月童贯曾除"),"职事官名","建政和复置节点。");d=tp(w,e,"北宋政和七年三月","罢同签书",i,q(i,"三月便罢"),"职事官名","建政和罢置节点。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,a,"编制隶属",i,q(i,"为枢密院副贰，佐枢长治本院事"),"同签书为枢密院副贰。",staff_type="官");broad=w.find_timepoint(e,"宋代");chain(w,[a,b,c,d,broad],"按专条时间排序并保留宋代总述节点");w.commit()
def entry174():
    i=174;w=W(i);e=en(w,"领枢密院事","官职",i,q(i,"职事官名，徽宗朝临时之制"),"辞典明载为临时职事官。");a=tp(w,e,"北宋政和七年十二月十七日","始置，任枢密院长官、握发兵权",i,q(i,"政和七年十二月十七日始置"),"职事官名","建始置节点。");b=tp(w,e,"北宋靖康元年二月","罢",i,q(i,"靖康元年二月罢"),"职事官名","建罢置节点。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,a,"编制隶属",i,q(i,"枢密院长官之任，握发兵之权"),"领枢密院事任本院长官。",staff_type="官");chain(w,[a,b],"按始置、罢废排序");w.commit()
def entry175():
    i=175;w=W(i);e=en(w,"权领枢密院事","官职",i,q(i,"职事官名，徽宗朝临时之制"),"辞典明载为临时职事官。");a=tp(w,e,"北宋政和七年三月七日","由同签书枢密院事改名，为枢密院副贰",i,q(i,"政和七年三月七日始有此称，由同签书枢密院事改名"),"职事官名","建改名始置节点。");b=tp(w,e,"北宋宣和三年五月后","不复置",i,q(i,"宣和三年五月后不复置"),"职事官名","建终结节点。");_,src=node(w,"同签书枢密院事","北宋政和七年三月","官职");rel(w,src,a,"前后演变",i,q(i,"由同签书枢密院事改名"),"同签书枢密院事改为权领枢密院事。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,a,"编制隶属",i,q(i,"为枢密院副贰，有参领兵权之职"),"权领枢密院事为本院副贰。",staff_type="官");chain(w,[a,b],"按始置、停置排序");w.commit()
def entry176():
    i=176;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,F[i][0],"官职",i,z,"辞典明载为代理差遣。");p=tp(w,e,"北宋咸平三年正月","长贰正员全缺时暂置代理院事",i,z,"差遣官","建代理节点。");_,o=node(w,"枢密院","宋初","机构");rel(w,o,p,"编制隶属",i,z,"权同发遣枢密院事代理本院职事。",staff_type="官");w.commit()
def entry177():
    i=177;qn=q(i,"官司名。枢密院办事机构");qs=q(i,"熙宁二年八月十二日始见铸“枢密承旨司记”");qstaff=q(i,"承旨司官额，有枢密都承旨、副都承旨、枢密院承旨、枢密院副承旨，常置一、二员，不备置");w=W(i);e=w.find_entity("枢密院承旨司","机构");p=tp(w,e,"北宋熙宁二年八月十二日","始见承旨司记，掌理枢密院诸房公事",i,qs,"官司名","复用总条占位写入始见节点。");ac(w,"Timepoints",p,i,qn,"补充办事机构性质。")
    _,parent=node(w,"枢密院","北宋熙宁元年","机构");rel(w,parent,p,"上下级机构",i,qn,"承旨司为枢密院办事机构。")
    for n in ("枢密院都承旨","枢密院副都承旨","枢密院承旨","枢密院副承旨"):
        post=en(w,n,"官职",i,qstaff,f"承旨司官额明确列{n}。")
        ph=w.ensure_placeholder(post,"总条无统一始置时间，待专条复用。") if n in ("枢密院都承旨","枢密院承旨") else tp(w,post,"未知","承旨司官额，常置一、二员而不备置",i,qstaff,"差遣名","原文无统一始置时间，建官额节点。")
        ac(w,"Timepoints",ph,i,qstaff,"总条补充承旨司官额。",note="常置一二员，不备置");rel(w,p,ph,"编制隶属",i,qstaff,f"承旨司官额包括{n}。",staff_type="官")
    w.commit()
def entry178():
    i=178;w=W(i);e=w.find_entity("枢密院承旨","官职");a=tp(w,e,"五代","已有枢密院承旨",i,q(i,"五代已有"),"差遣名","复用占位建五代职源节点。");b=tp(w,e,"宋初","沿置，为承旨司长官，通署诸房公事",i,q(i,"宋初沿置"),"差遣名","建宋初沿置节点。");ac(w,"Timepoints",b,i,q(i,"为承旨司（院）长官，通署本院诸房公事"),"补充职掌。",note="职掌");c=tp(w,e,"北宋太平兴国七年四月","加都字，改为枢密院都承旨",i,q(i,"至太平兴国七年四月，枢密院承旨加“都”字"),"差遣名","建改名节点。");_,office=node(w,"枢密院承旨司","北宋熙宁二年八月十二日","机构");rel(w,office,b,"编制隶属",i,q(i,"为承旨司（院）长官"),"枢密院承旨为承旨司长官。",staff_type="官");chain(w,[a,b,c],"按五代、宋初、太平兴国改名排序");w.commit()
def entry179():
    i=179;w=W(i);e=w.find_entity("枢密院都承旨","官职");p=tp(w,e,"北宋太平兴国七年四月三日","由枢密院承旨加都字，任属官之首，编制一员",i,q(i,"太平兴国七年(982)四月三日始以枢密承旨加“都”字"),"职事官","复用占位建始置节点。",attr_grade="从五品");_,src=node(w,"枢密院承旨","北宋太平兴国七年四月","官职");rel(w,src,p,"前后演变",i,q(i,"始以枢密承旨加“都”字"),"枢密院承旨加都字为都承旨。");_,office=node(w,"枢密院承旨司","北宋熙宁二年八月十二日","机构");rel(w,office,p,"编制隶属",i,q(i,"枢密院属官之首"),"都承旨为承旨司属官之首。",staff_quota=1,staff_type="官");w.commit()
def entry180():
    i=180;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,F[i][0],"官职",i,z,"辞典明载为临时差遣。");p=tp(w,e,"未知","正员缺时暂行代理都承旨事",i,z,"临时差遣","原文无时间，建代理制度节点。");_,office=node(w,"枢密院承旨司","北宋熙宁二年八月十二日","机构");rel(w,office,p,"编制隶属",i,z,"权都承旨代理承旨司都承旨事。",staff_type="官");w.commit()
def main():
    entry161();entry162();entry163();entry164();entry165();entry166();entry167();entry168();entry169();entry170();entry171();entry172();entry173();entry174();entry175();entry176();entry177();entry178();entry179();entry180()
if __name__=="__main__":main()
