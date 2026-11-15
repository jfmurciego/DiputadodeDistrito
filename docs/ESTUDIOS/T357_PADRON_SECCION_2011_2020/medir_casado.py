"""T-357: mide el casado de secciones (INE población, seccionado INE, votos del Observatorio).
Uso: python -I medir_casado.py <dir_trabajo> ; espera en <dir>: t30832.csv, x<año>/*.dbf (seccionados),
obs/data/<elec>/sekzioa/*.json, obs/geo/sekzioak/<año>/*.json, c11/i/C2011_ccaa*_Indicadores.csv, c11/c/*.dbf"""
import json,struct,glob,sys,collections
W=sys.argv[1]
def dbf(p):
    b=open(p,'rb').read();n,hl,rl=struct.unpack('<IHH',b[4:12]);f=[];o=32
    while b[o]!=13: f.append((b[o:o+11].split(b'\0')[0].decode(),b[o+16]));o+=32
    for i in range(n):
        r=b[hl+i*rl:hl+(i+1)*rl];c=1;d={}
        for nm,l in f: d[nm]=r[c:c+l].decode('latin1').strip();c+=l
        yield d
def num(s):
    s=s.replace('.','')
    return int(s) if s.isdigit() else None
atlas=collections.defaultdict(dict);raw=collections.defaultdict(collections.Counter);punto=collections.defaultdict(collections.Counter)
for l in open(W+'/t30832.csv',encoding='utf-8-sig'):
    p=l.rstrip('\n').split(';')
    if len(p)==6 and p[3]=='Población' and p[2]:
        atlas[p[4]][p[2][:10]]=num(p[5]); raw[p[4]][p[5] if not p[5].replace('.','').isdigit() else 'valor']+=1
        if p[5]=='.': punto[p[4]][p[2][:2]]+=1
c11={}
for f in glob.glob(W+'/c11/i/C2011_ccaa*_Indicadores.csv'):
    h=None
    for l in open(f,encoding='utf-8-sig'):
        p=l.rstrip('\n').split(',')
        if h is None: h=p;continue
        d=dict(zip(h,p));c11[d['cpro'].zfill(2)+d['cmun'].zfill(3)+d['dist'].zfill(2)+d['secc'].zfill(3)]=num(d['t1_1'])
els={'201111':(2012,'2012'),'201512':(2015,'2015'),'201606':(2016,'2016'),'201904':(2019,'2019'),'201911':(2020,'2020')}
out={'atlas_30832_secciones_por_periodo':{k:{'filas':len(v),'con_valor':sum(x is not None for x in v.values()),'suma_poblacion':sum(x or 0 for x in v.values())} for k,v in sorted(atlas.items())},
     'censo2011_indicadores':{'secciones':len(c11),'con_valor':sum(x is not None for x in c11.values()),'suma_t1_1':sum(x or 0 for x in c11.values())}}
def cmp(a,b): return {'n':len(a),'casan':len(a&b),'faltan_en_otro':len(a-b),'faltan_aqui':len(b-a)}
cen=set(c11);res={}
for e,(y,gy) in els.items():
    ine={r['CUSEC'] for r in dbf(glob.glob(f'{W}/x{y}/*.dbf')[0]) if r['CUSEC']}
    vot=set()
    for f in glob.glob(f'{W}/obs/data/{e}/sekzioa/*.json'): vot|=set(json.load(open(f))['r'])
    geo=set()
    for f in glob.glob(f'{W}/obs/geo/sekzioak/{gy}/*.json'): geo|={x['id'] for x in json.load(open(f))['features']}
    r={'seccionado_ine':len(ine),'votos_observatorio':len(vot),'geo_observatorio':len(geo),
       'ine_vs_votos':cmp(ine,vot),'ine_vs_geo':cmp(ine,geo),
       'solo_votos_muestra':sorted(vot-ine)[:5],'solo_ine_muestra':sorted(ine-vot)[:5]}
    for per in sorted(atlas):
        A={k for k,v in atlas[per].items() if v is not None}
        if per in {str(y-1),str(y),str(y+1)} and int(per)>=2015:
            r['atlas_'+per]={'con_valor':len(A),'vs_seccionado_ine':cmp(ine,A),'vs_votos':cmp(vot,A)}
    if e=='201111': r['censo2011_vs_seccionado_2012']=cmp(ine,{k for k,v in c11.items() if v is not None}); r['censo2011_vs_votos']=cmp(vot,{k for k,v in c11.items() if v is not None})
    res[e]=r
out['elecciones']=res
out['atlas_30832_clasificacion_filas']={k:dict(v) for k,v in sorted(raw.items())}  # 'valor' / '.' (no publicado) / '""' (vacío)
out['atlas_30832_provincias_con_punto_top8']={k:v.most_common(8) for k,v in sorted(punto.items())}
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
