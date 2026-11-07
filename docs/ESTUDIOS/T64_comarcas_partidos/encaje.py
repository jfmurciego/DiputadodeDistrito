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
    a,n=ari_nmi(g.id_partido,g[c])
    # municipios del partido que caen en la comarca mayoritaria
    pur=ct.max(axis=1).sum()/ct.values.sum()
    return dict(n=len(g),partidos=ct.shape[0],comarcas=ct.shape[1],ARI=round(a,3),NMI=round(n,3),
      pct_mun_en_partido_con_mayoria_unica=round(100*g.id_partido.map(maj>0.5).mean(),1),
      pct_mun_en_comarca_mayoritaria_de_su_partido=round(100*pur,1))
if __name__=="__main__":
    f,k,c=sys.argv[1:4]; pv=sys.argv[4] if len(sys.argv)>4 else None
    pj=pd.read_csv('configuracion/partidos_judiciales.csv',comment='#',dtype=str)
    cm=pd.read_csv(f,dtype=str,encoding='utf-8-sig'); cm[k]=cm[k].str.zfill(5)
    d=pj.merge(cm,left_on='codigo_ine',right_on=k)
    print('TOTAL',metricas(d,c))
    if pv:
        for p,g in d.groupby(pv): print(p,metricas(g,c))
