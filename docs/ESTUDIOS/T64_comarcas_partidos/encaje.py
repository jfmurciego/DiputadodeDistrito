#!/usr/bin/env python3
"""Encaje partidos judiciales (configuracion/partidos_judiciales.csv) vs una relación municipio→comarca.
Uso: encaje.py <csv_comarcas> <col_municipio> <col_comarca> [col_provincia]"""
import sys, pandas as pd, numpy as np
from math import log
def comb2(x): return x*(x-1)/2
def ari_nmi(a,b):
    ct=pd.crosstab(a,b).values.astype(float); n=ct.sum()
    s=comb2(ct).sum(); sa=comb2(ct.sum(1)).sum(); sb=comb2(ct.sum(0)).sum(); e=sa*sb/comb2(n); mx=(sa+sb)/2
    ari=1.0 if mx==e else (s-e)/(mx-e)
    pa=ct.sum(1)/n; pb=ct.sum(0)/n; p=ct/n
    ha=-(pa*np.log(pa)).sum(); hb=-(pb*np.log(pb)).sum()
    nz=p>0; mi=(p[nz]*np.log(p[nz]/np.outer(pa,pb)[nz])).sum()
    nmi=1.0 if ha+hb==0 else 2*mi/(ha+hb)
    return ari,nmi
def metricas(g,c):
    ct=pd.crosstab(g.id_partido,g[c])
    maj=ct.max(axis=1)/ct.sum(axis=1)
    a,n=ari_nmi(g.id_partido,g[c]) if ct.shape[0]>1 and ct.shape[1]>1 else (float('nan'),float('nan'))
    # municipios del partido que caen en la comarca mayoritaria
    pur=ct.max(axis=1).sum()/ct.values.sum()
    return dict(n=len(g),partidos=ct.shape[0],comarcas=ct.shape[1],ARI=None if a!=a else round(a,3),NMI=None if n!=n else round(n,3),
      pct_mun_en_partido_con_mayoria_unica=round(100*g.id_partido.map(maj>0.5).mean(),1),
      pct_mun_en_comarca_mayoritaria_de_su_partido=round(100*pur,1))
if __name__=="__main__":
    import json
    f,k,c=sys.argv[1:4]
    pj=pd.read_csv('configuracion/partidos_judiciales.csv',comment='#',dtype=str)
    cm=pd.read_csv(f,dtype=str,encoding='utf-8-sig',comment='#'); cm[k]=cm[k].str.zfill(5)
    d=pj.merge(cm,left_on='codigo_ine',right_on=k)
    res={'cobertura_municipios_con_partido_y_comarca':len(d),'TOTAL':metricas(d,c),'provincias':{}}
    for p,g in d.groupby(d.codigo_ine.str[:2]): res['provincias'][p]=metricas(g,c)
    # desencajes: partidos repartidos con segunda comarca >=25% o comarcas repartidas entre partidos
    ct=pd.crosstab(d.id_partido,d[c]); ex=[]
    for pid,r in ct.iterrows():
        t=r.sum(); top=r.sort_values(ascending=False)
        if t>=8 and top.iloc[1]/t>=0.25: ex.append((pid,int(t),[(a,int(b)) for a,b in top.head(3).items() if b>0]))
    ex.sort(key=lambda x:-x[1]); res['partidos_partidos_por_comarcas']=ex[:12]
    ctc=ct.T; ex2=[]
    for cid,r in ctc.iterrows():
        t=r.sum(); top=r.sort_values(ascending=False)
        if t>=8 and top.iloc[1]/t>=0.25: ex2.append((cid,int(t),[(a,int(b)) for a,b in top.head(3).items() if b>0]))
    ex2.sort(key=lambda x:-x[1]); res['comarcas_partidas_por_partidos']=ex2[:12]
    print(json.dumps(res,ensure_ascii=False,indent=1,default=float))
