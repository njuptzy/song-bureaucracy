#!/usr/bin/env python3
"""提取 chapter2t4 第 105–112 条：官告院与礼仪院系统。"""
import json,os,sqlite3,sys

sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB=os.path.join(ROOT,"data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB=os.path.join(ROOT,"data/database/song_bureaucracy_entries_ch2t4.db")


def load(i):
    with sqlite3.connect(DICT_DB) as c: r=c.execute("SELECT title,page,text,fields FROM chapter2t4 WHERE id=?",(i,)).fetchone()
    return r[0],r[1],(r[2] or "")+"\n"+"\n".join(str(v) for k,v in json.loads(r[3] or "{}").items() if not k.startswith("_"))


FULL={i:load(i) for i in range(105,113)}
def q(i,s): assert s in FULL[i][2],f"#{i} 不含：{s}"; return s
def writer(i): return EntryWriter(ENTRY_DB,FULL[i][0],FULL[i][1])
def cite(i): return f"《宋代官制辞典》第{FULL[i][1]}页“{FULL[i][0]}”条"
def ac(w,t,r,i,quote,d,**kw): return w.citation(t,r,cite(i),quote,d,**kw)
def entity(w,title,typ,i,quote,d): return w.entity(title,typ,d,quotation=quote)


def tp(w,en,time,event,i,quote,cat,d,**kw):
    r=w.timepoint(en,time,event,d,quote,attr_category=cat,**kw); ac(w,"Timepoints",r,i,quote,d); return r


def rel(w,s,o,kind,i,quote,d,**kw):
    r=w.relationship(s,o,kind,d,quote,**kw); ac(w,"Relationships",r,i,quote,d); return r


def node(w,title,time,typ=None):
    en=w.find_entity(title,typ); assert en,f"缺实体 {title}"
    r=w.find_timepoint(en,time); assert r,f"{title} 缺 {time}"; return en,r


def rechain(w,en,ids,d):
    for n,r in enumerate(ids): w.relink(r,d,prev_id=ids[n-1] if n else None,succ_id=ids[n+1] if n+1<len(ids) else None)


def entry105():
    i=105; text=FULL[i][2].split("\n",1)[0]; w=writer(i)
    en,r=node(w,"勾当三班院公事","北宋雍熙四年七月","官职")
    ac(w,"Timepoints",r,i,text,"本条补充勾当三班院公事的职掌、充任资格及无定员性质",note="职掌与编制")
    _,office=node(w,"三班院","北宋雍熙四年七月","机构")
    relation=rel(w,office,r,"编制隶属",i,text,"勾当三班院公事掌三班院职事，不定员。",staff_type="官")
    w.commit()


def entry106():
    i=106; qe=q(i,"宋前期官署名。"); qorigin=q(i,"五代后唐同光二年(924)已有“吏部官告院”"); qd=q(i,"掌文臣、武官、将校告身（任命书）按级别制造，包括命妇及封、赠官告按格式精制"); qstaff=q(i,"提举兵、吏、司封、司勋官告院一人。判兵、吏、司封、司勋官告院事一人。主封爵、宗室、皇帝内外命妇告身的司封郎中一人。吏额：太宗朝时书写官告令史十人。绫纸库专知官一人。仁宗朝，正名十五人，守阙私名十五人")
    w=writer(i); title="兵部、吏部、司封、司勋官告院"; en=entity(w,title,"机构",i,qe,"辞典明载为宋前期官署。")
    origin=tp(w,en,"五代后唐同光二年","已有吏部官告院",i,qorigin,"官署名","建五代职源节点。")
    song=tp(w,en,"宋前期","掌各级文武官、将校及封赠官告制造",i,qe,"官署名","建宋前期制度节点。")
    ac(w,"Timepoints",song,i,qd,"补充职掌",note="职掌")
    tai=tp(w,en,"北宋太宗朝","书写官告令史十人，设绫纸库专知官一人",i,qstaff,"官署名","建太宗朝吏额节点。")
    ren=tp(w,en,"北宋仁宗朝","正名十五人、守阙私名十五人",i,qstaff,"官署名","建仁宗朝吏额节点。")
    posts=(("提举兵部、吏部、司封、司勋官告院事",1,"官"),("判兵部、吏部、司封、司勋官告院事",1,"官"),("司封郎中",1,"官"),("书写官告令史",10,"吏"),("绫纸库专知官",1,"吏"))
    for title,quota,kind in posts:
        pe=w.find_entity(title,"官职") or entity(w,title,"官职",i,qstaff,f"官告院编制明列{title}。")
        time="北宋太宗朝" if title in ("书写官告令史","绫纸库专知官") else "宋前期"
        ptp=w.find_timepoint(pe,time) or tp(w,pe,time,f"官告院设{quota}人",i,qstaff,"官职名","建官告院编制节点。")
        subject=tai if time=="北宋太宗朝" else song
        rel(w,subject,ptp,"编制隶属",i,qstaff,f"官告院设{title}{quota}人。",staff_quota=quota,staff_type=kind)
    rechain(w,en,[origin,song,tai,ren],"按五代源流、宋前期、太宗、仁宗排序")
    w.commit()


def entry107():
    i=107; text=FULL[i][2].split("\n",1)[0]; w=writer(i); title="提举兵部、吏部、司封、司勋官告院事"
    en,r=node(w,title,"宋前期","官职"); ac(w,"Timepoints",r,i,text,"补充提举官告院由知制诰充、为长官的证据",note="职掌与充任资格")
    _,office=node(w,"兵部、吏部、司封、司勋官告院","宋前期","机构")
    rel(w,office,r,"编制隶属",i,text,"提举官告院为长官，编制一人。",staff_quota=1,staff_type="官"); w.commit()


def entry108():
    i=108; text=FULL[i][2].split("\n",1)[0]; w=writer(i); title="判兵部、吏部、司封、司勋官告院事"
    en,r=node(w,title,"宋前期","官职"); ac(w,"Timepoints",r,i,text,"补充判官告院由带职京朝官充、位次于提举官的证据",note="职掌与充任资格")
    _,office=node(w,"兵部、吏部、司封、司勋官告院","宋前期","机构")
    rel(w,office,r,"编制隶属",i,text,"判官告院为主管官之一，编制一人。",staff_quota=1,staff_type="官"); w.commit()


def entry109():
    i=109; qe=q(i,"官司名。"); qpre=q(i,"北宋大中祥符元年四月五日，于起居院置详定仪注所"); qchange=q(i,"大中祥符六年(1013)八月十一日改为礼仪院"); qend=q(i,"天圣元年（1023）四月八日罢"); qd=q(i,"裁定举行典礼所用仪仗、法物等各项制度，统掌有关送中书礼房的各种内外书奏文字"); qstaff=q(i,"官额有判礼仪院、知礼仪院；吏额二十二人")
    w=writer(i); pre=entity(w,"详定仪注所","机构",i,qpre,"本条明确礼仪院前身。")
    pre_start=tp(w,pre,"北宋大中祥符元年四月五日","于起居院置详定仪注所",i,qpre,"官司名","建前身始置节点。")
    pre_end=tp(w,pre,"北宋大中祥符六年八月十一日","改为礼仪院",i,qchange,"官司名","建前身终结节点。")
    office=entity(w,"礼仪院","机构",i,qe,"辞典明载为官司。")
    start=tp(w,office,"北宋大中祥符六年八月十一日","由详定仪注所改置，掌典礼制度与内外书奏",i,qchange,"官司名","建礼仪院始置节点。")
    ac(w,"Timepoints",start,i,qd,"补充职掌",note="职掌"); ac(w,"Timepoints",start,i,qstaff,"补充官额与吏额",note="编制")
    end=tp(w,office,"北宋天圣元年四月八日","罢礼仪院",i,qend,"官司名","建终结节点。")
    rel(w,pre_end,start,"前后演变",i,qchange,"详定仪注所改为礼仪院。")
    qiju_en=w.find_entity("起居院","机构"); assert qiju_en
    qiju=w.find_timepoint(qiju_en,"北宋大中祥符元年四月五日") or tp(w,qiju_en,"北宋大中祥符元年四月五日","院内置详定仪注所",i,qpre,"官司名","建与详定仪注所同刻的隶属端点。",chain="none")
    qiju_order=[w.find_timepoint(qiju_en,t) for t in ("北宋淳化五年四月五日","北宋大中祥符元年四月五日","北宋大中祥符六年八月十一日","北宋大中祥符八年","北宋元丰五年五月","北宋元祐三年")]
    rechain(w,qiju_en,qiju_order,"插入大中祥符元年置详定仪注所节点并按历史顺序重排")
    rel(w,qiju,pre_start,"上下级机构",i,qpre,"详定仪注所置于起居院。")
    w.commit()


def entry110():
    i=110; text=FULL[i][2].split("\n",1)[0]; w=writer(i)
    en=w.find_entity("判礼仪院","官职") or entity(w,"判礼仪院","官职",i,text,"辞典明载为差遣。")
    point=tp(w,en,"北宋大中祥符六年八月十一日","参知政事统领礼仪院，编制一员",i,text,"差遣名","建礼仪院存续期编制节点。")
    _,office=node(w,"礼仪院","北宋大中祥符六年八月十一日","机构")
    rel(w,office,point,"编制隶属",i,text,"礼仪院设判院一员。",staff_quota=1,staff_type="官"); w.commit()


def entry111():
    i=111; qe=q(i,"差遣名。"); qt1=q(i,"唐朝德宗建中之前，有知礼仪院"); qt2=q(i,"开元元年正月有知太常寺礼仪事"); qs=q(i,"北宋大中祥符七年二月始置"); qend=q(i,"天圣元年四月八日，改为判太常礼院"); qd=q(i,"凡制度文物，及祠祭所用有不符合典礼者，知院都得主持裁定"); qg=q(i,"三品以上充"); qstaff=q(i,"一员或二员")
    w=writer(i); en=entity(w,"知礼仪院事","官职",i,qe,"辞典明载为差遣。")
    tang1=tp(w,en,"唐开元元年正月","有知太常寺礼仪事",i,qt2,"差遣名","建唐代源流节点。")
    tang2=tp(w,en,"唐德宗建中之前","有知礼仪院",i,qt1,"差遣名","建唐代沿革节点。")
    start=tp(w,en,"北宋大中祥符七年二月","始置，以两制以上朝官充，主持典礼裁定",i,qs,"差遣名","建北宋始置节点。",attr_grade="三品以上充")
    ac(w,"Timepoints",start,i,qd,"补充职掌",note="职掌"); ac(w,"Timepoints",start,i,qg,"补充品位",note="三品以上充"); ac(w,"Timepoints",start,i,qstaff,"补充员额",note="一员或二员，不硬填单一 quota")
    end=tp(w,en,"北宋天圣元年四月八日","改为判太常礼院",i,qend,"差遣名","建终结改名节点。")
    successor=entity(w,"判太常礼院","官职",i,qend,"本条明确后继差遣。")
    successor_tp=tp(w,successor,"北宋天圣元年四月八日","由知礼仪院事改置",i,qend,"差遣名","建后继节点。")
    rel(w,end,successor_tp,"前后演变",i,qend,"知礼仪院事改为判太常礼院。")
    _,office=node(w,"礼仪院","北宋大中祥符六年八月十一日","机构")
    rel(w,office,start,"编制隶属",i,qs,"礼仪院设置知院事一至二员。",staff_type="官")
    rechain(w,en,[tang1,tang2,start,end],"按唐开元、建中前、北宋始置、天圣改名排序")
    w.commit()


def entry112():
    i=112; text=FULL[i][2].split("\n",1)[0]; w=writer(i)
    en=w.find_entity("同知礼仪院事","官职") or entity(w,"同知礼仪院事","官职",i,text,"辞典明载为差遣。")
    start=tp(w,en,"北宋大中祥符六年八月十一日","始置；二员以上知院事带同字，位次于判院",i,text,"差遣名","建始置、职掌与位次节点。")
    _,office=node(w,"礼仪院","北宋大中祥符六年八月十一日","机构")
    rel(w,office,start,"编制隶属",i,text,"礼仪院同时置二员以上知院事时称同知礼仪院事。",staff_type="官"); w.commit()


def main():
    entry105(); entry106(); entry107(); entry108(); entry109(); entry110(); entry111(); entry112()


if __name__=="__main__": main()
