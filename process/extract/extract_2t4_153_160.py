#!/usr/bin/env python3
"""提取 chapter2t4 第153–160条。"""
import json,os,sqlite3,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from ew import EntryWriter
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));D=os.path.join(R,"data/database/song_bureaucracy_dictionary_ch2t4.db");ENTRY_DB=os.path.join(R,"data/database/song_bureaucracy_entries_ch2t4.db")
def ld(i):
 with sqlite3.connect(D) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
 return r[0],r[1],(r[2] or "")+"\n"+"\n".join(str(v) for k,v in json.loads(r[3] or "{}").items() if not k.startswith("_"))
F={i:ld(i) for i in range(153,161)}
def q(i,s):assert s in F[i][2],s;return s
def W(i):return EntryWriter(ENTRY_DB,F[i][0],F[i][1])
def C(i):return f"《宋代官制辞典》第{F[i][1]}页“{F[i][0]}”条"
def ac(w,t,r,i,z,d,**k):return w.citation(t,r,C(i),z,d,**k)
def en(w,n,y,i,z,d):return w.entity(n,y,d,quotation=z)
def tp(w,e,t,v,i,z,c,d,**k):r=w.timepoint(e,t,v,d,z,attr_category=c,**k);ac(w,"Timepoints",r,i,z,d);return r
def rl(w,s,o,k,i,z,d,**kw):r=w.relationship(s,o,k,d,z,**kw);ac(w,"Relationships",r,i,z,d);return r
def nd(w,n,t,y=None):e=w.find_entity(n,y);assert e;r=w.find_timepoint(e,t);assert r;return e,r
def ch(w,a,d):
 for j,r in enumerate(a):w.relink(r,d,prev_id=a[j-1] if j else None,succ_id=a[j+1] if j+1<len(a) else None)
def e153():
 i=153;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,"待漏院","机构",i,z,"辞典明载为官廨。");a=tp(w,e,"唐朝","已置待漏院",i,z,"官廨名","建唐代源流节点。");b=tp(w,e,"宋初","沿置于宫城左掖门南，供百官候朝",i,z,"官廨名","建宋初沿置节点。");c=tp(w,e,"北宋大中祥符初","真宗辰漏上朝，知班官、驱使官登记迟到官员",i,z,"官廨名","建大中祥符朝仪节点。");ch(w,[a,b,c],"按唐、宋初、大中祥符排序");w.commit()
def e154():
 i=154;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,"朝集院","机构",i,z,"辞典明载为馆舍。");a=tp(w,e,"西汉武帝时","置朝邸，为朝集院制度源流",i,z,"馆舍","建源流节点。");b=tp(w,e,"北宋咸平四年四月","始置于京师朱雀门外，房舍百余区，旋罢",i,z,"馆舍","建首次置罢节点。");c=tp(w,e,"北宋景祐二年十月","复置朝集院，馆地方升朝官待铨注",i,z,"馆舍","建复置节点。");pts=[a,b,c]
 for t in ("北宋熙宁四年","北宋熙宁六年","北宋熙宁七年","北宋熙宁九年"):
  pts.append(tp(w,e,t,"朝集院房舍陆续拨归太学、律学、医学",i,z,"馆舍","建房舍划拨节点。"))
 pts.append(tp(w,e,"北宋熙宁末","朝集院消亡",i,z,"馆舍","建消亡节点。"));pts.append(tp(w,e,"南宋绍兴五年二月","诏拟于临安复置，因台官谏阻未果",i,z,"馆舍","建未果复置节点。"));ch(w,pts,"按历次置罢排序");w.commit()
def e155():
 i=155;qn=q(i,"司名");qs=q(i,"景德二年（1005）十月十五日始置");qe=q(i,"元丰元年（1078）十二月十九日罢");qst=q(i,"都大提举官二员（天圣后或置五员），勾当公事官二员");w=W(i);e=en(w,F[i][0],"机构",i,qn,"辞典明载为司。");a=tp(w,e,"北宋景德二年十月十五日","始置，统筹在京诸司库务场院坊作七十四所",i,qs,"司名","建始置节点。");ac(w,"Timepoints",a,i,F[i][2].split("\n",1)[0],"补充职能。",note="职能");b=tp(w,e,"北宋天圣后","都大提举官或置五员",i,qst,"司名","建编制变化节点。");c=tp(w,e,"北宋熙宁二年十一月","所辖库务场院七十三处",i,q(i,"熙宁二年十一月为七十三处"),"司名","建辖区数量节点。");d=tp(w,e,"北宋熙宁三年六月","所辖库务场院七十二处",i,q(i,"三年六月为七十二处"),"司名","建辖区数量节点。");f=tp(w,e,"北宋熙宁六年正月五日","增隶市易务、商税院等机构",i,q(i,"熙宁六年正月五日，又增"),"司名","建增隶节点。");g=tp(w,e,"北宋元丰元年十二月十九日","罢都大提举司",i,qe,"司名","建罢废节点。")
 for n,num in (("都大提举在京诸司库务",2),("都大提举在京诸司库务司勾当公事",2)):
  p=en(w,n,"官职",i,qst,f"编制明确列{n}。");pt=tp(w,p,"北宋景德二年十月十五日","本司属官",i,qst,"差遣名","建编制节点。");rl(w,a,pt,"编制隶属",i,qst,f"本司设{n}。",staff_quota=num,staff_type="官")
 ch(w,[a,b,c,d,f,g],"按始置、编制变化、罢废排序");w.commit()
def e156():
 i=156;z=F[i][2].rstrip();w=W(i);_,p=nd(w,F[i][0],"北宋景德二年十月十五日","官职");ac(w,"Timepoints",p,i,z,"补充文臣、内侍充任及总辖本司公事。",note="职掌与充任");_,o=nd(w,"都大提举在京诸司库务司","北宋景德二年十月十五日","机构");rl(w,o,p,"编制隶属",i,z,"主管官掌总辖本司公事。",staff_quota=2,staff_type="官");w.commit()
def e157():
 i=157;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,F[i][0],"官职",i,z,"辞典明载为差遣。");p=tp(w,e,"北宋天圣后","提举官二员时资浅者带同字，同领本司公事",i,z,"差遣名","依总条天圣后编制语境建节点。");_,o=nd(w,"都大提举在京诸司库务司","北宋天圣后","机构");rl(w,o,p,"编制隶属",i,z,"同都大提举与都大官同领本司公事。",staff_type="官");w.commit()
def e158():
 i=158;z=F[i][2];w=W(i);e=w.find_entity(F[i][0],"官职");_,p=nd(w,F[i][0],"北宋景德二年十月十五日","官职");ac(w,"Timepoints",p,i,z,"补充朝官充任、二人编制及点检职掌。",note="职掌与编制");w.commit()
def e159():
 i=159;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,"库经","官职",i,z,"辞典明载为公人。");p=tp(w,e,"未知","每库眼设置，掌官物收支文历",i,z,"公人名","原文无时间，建制度节点。");_,o=nd(w,"都大提举在京诸司库务司","北宋景德二年十月十五日","机构");rl(w,o,p,"编制隶属",i,z,"在京诸司库务各库眼置库经。",staff_type="吏");w.commit()
def e160():
 i=160;z=F[i][2].split("\n",1)[0];w=W(i);e=en(w,"都库经","官职",i,z,"辞典明载为公人。");p=tp(w,e,"未知","掌数库官物收贮的库经，带都字",i,z,"公人名","原文无时间，建制度节点。");_,o=nd(w,"都大提举在京诸司库务司","北宋景德二年十月十五日","机构");rl(w,o,p,"编制隶属",i,z,"都库经属在京诸司库务系统。",staff_type="吏");w.commit()
def main():e153();e154();e155();e156();e157();e158();e159();e160()
if __name__=="__main__":main()
