#!/usr/bin/env python3
"""提取 chapter2t4 第147–152条：编修条例司与详定官制所。"""
import json,os,sqlite3,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db"); ENTRY_DB=os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db")
def load(i):
 with sqlite3.connect(DICT_DB) as c:r=c.execute("select title,page,text,fields from chapter2t4 where id=?",(i,)).fetchone()
 return r[0],r[1],(r[2] or "")+"\n"+"\n".join(str(v) for k,v in json.loads(r[3] or "{}").items() if not k.startswith("_"))
F={i:load(i) for i in range(147,153)}
def q(i,s):assert s in F[i][2],f"#{i} 不含{s}";return s
def w(i):return EntryWriter(ENTRY_DB,F[i][0],F[i][1])
def ci(i):return f"《宋代官制辞典》第{F[i][1]}页“{F[i][0]}”条"
def ac(x,t,r,i,z,d,**kw):return x.citation(t,r,ci(i),z,d,**kw)
def en(x,n,y,i,z,d):return x.entity(n,y,d,quotation=z)
def tp(x,e,t,v,i,z,c,d,**kw):r=x.timepoint(e,t,v,d,z,attr_category=c,**kw);ac(x,"Timepoints",r,i,z,d);return r
def rel(x,s,o,k,i,z,d,**kw):r=x.relationship(s,o,k,d,z,**kw);ac(x,"Relationships",r,i,z,d);return r
def node(x,n,t,y=None):e=x.find_entity(n,y);assert e;r=x.find_timepoint(e,t);assert r;return e,r
def chain(x,a,d):
 for j,r in enumerate(a):x.relink(r,d,prev_id=a[j-1] if j else None,succ_id=a[j+1] if j+1<len(a) else None)

def e147():
 i=147;z=F[i][2].split("\n",1)[0];x=w(i);g=en(x,"编修条例司","机构",i,z,"辞典明确为两条例司总名。") ;gt=tp(x,g,"北宋熙宁间","编修中书条例司、编修司农寺条例司总名",i,z,"官署总名","建总名节点。")
 for n in ("编修中书条例司","编修司农寺条例司"):
  e=en(x,n,"机构",i,z,f"总名条明确列实例{n}。");p=tp(x,e,"北宋熙宁间","编修条例司实例",i,z,"官署名","建实例节点。");rel(x,gt,p,"统称与实例",i,z,f"编修条例司是{n}等机构的总名。")
 x.commit()
def e148():
 i=148;qn=q(i,"立法机构名");qs=q(i,"熙宁二年九月十六日，在神宗倡议下置着详编修中书条例官");qo=q(i,"十月张官设吏，增置编修官七人");qe=q(i,"熙宁八年）编修中书条例司、修司农寺条例司皆罢");qst=q(i,"看详编修中书条例官二人，同看详编修中书条例，或置一人，编修中书条例官七人");x=w(i)
 e=en(x,F[i][0],"机构",i,qn,"辞典明载为立法机构。");a=tp(x,e,"北宋熙宁二年九月十六日","始置看详编修中书条例官，清理修订中书五房条例",i,qs,"立法机构名","建始置节点。");b=tp(x,e,"北宋熙宁二年十月","张官设吏，增置编修官七人",i,qo,"立法机构名","建扩充节点。");c=tp(x,e,"北宋熙宁八年","编修中书条例司罢",i,qe,"立法机构名","建罢废节点。")
 for n,num in (("看详编修中书条例",2),("同看详编修中书条例",1),("编修中书条例",7)):
  p=en(x,n,"官职",i,qst,f"编制明确列{n}。");pt=tp(x,p,"北宋熙宁二年九月十六日","条例所属官",i,qst,"差遣官","建编制节点。");rel(x,a,pt,"编制隶属",i,qst,f"条例所设{n}。",staff_quota=num,staff_type="官")
 chain(x,[a,b,c],"按始置、扩充、罢废排序");x.commit()
def e149():
 i=149;z=F[i][2].split("\n",1)[0];x=w(i);e=x.find_entity(F[i][0],"官职");_,p=node(x,F[i][0],"北宋熙宁二年九月十六日","官职");ac(x,"Timepoints",p,i,z,"补充充任资格与编排、修订中书条例职掌。",note="职掌");x.commit()
def e150():
 i=150;z=F[i][2].split("\n",1)[0];x=w(i);e=x.find_entity(F[i][0],"官职");_,old=node(x,F[i][0],"北宋熙宁二年九月十六日","官职");p=tp(x,e,"北宋熙宁七年三月","看详官两员以上，资浅者带同字",i,z,"差遣官","建熙宁七年制度节点。");chain(x,[old,p],"按始设、熙宁七年排序");x.commit()
def e151():
 i=151;z=F[i][2].split("\n",1)[0];x=w(i);_,p=node(x,F[i][0],"北宋熙宁二年九月十六日","官职");ac(x,"Timepoints",p,i,z,"补充次第编排、删定取舍及京官兼充。",note="职掌与充任");x.commit()
def e152():
 i=152;qn=q(i,"官署名");qs=q(i,"北宋神宗元丰三年六月十五日始置");qe=q(i,"元丰五年九月二十三日罢局");qd=q(i,"神宗元丰间改革官名制度的起草方案机构");qst=q(i,"设详定官制官二人、同详定官制官一人，属官有检讨文字");x=w(i);e=en(x,"详定官制所","机构",i,qn,"辞典明载为官署。");a=tp(x,e,"北宋元丰三年六月十五日","始置，起草改革官名制度方案",i,qs,"官署名","建始置节点。");ac(x,"Timepoints",a,i,qd,"补充职能。",note="职能");b=tp(x,e,"北宋元丰五年九月二十三日","罢局",i,qe,"官署名","建罢废节点。")
 for n,num in (("详定官制官",2),("同详定官制官",1),("详定官制所检讨文字",None)):
  p=en(x,n,"官职",i,qst,f"官制所编制明确列{n}。");pt=tp(x,p,"北宋元丰三年六月十五日","详定官制所属官",i,qst,"差遣官","建编制节点。");rel(x,a,pt,"编制隶属",i,qst,f"详定官制所设{n}。",staff_quota=num,staff_type="官")
 chain(x,[a,b],"按始置、罢局排序");x.commit()
def main():e147();e148();e149();e150();e151();e152()
if __name__=="__main__":main()
