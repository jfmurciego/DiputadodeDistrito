"""T-357: contrasta ficheros del Observatorio bajados con orchestracion/fuente_nazioenbehatokia.json.
Uso: python -I contrastar_observatorio.py <manifiesto.json> <dir_obs> ; imprime n y discrepancias."""
import json,hashlib,sys,os
man=json.load(open(sys.argv[1]))['ficheros'];n=0;bad=[];falta=[]
for k,v in man.items():
    if not k.startswith(('data/2011','data/2015','data/2016','data/2019','geo/sekzioak/2012/','geo/sekzioak/2015/','geo/sekzioak/2016/','geo/sekzioak/2019/','geo/sekzioak/2020/')): continue
    p=os.path.join(sys.argv[2],k)
    if not os.path.exists(p): falta.append(k);continue
    b=open(p,'rb').read();n+=1
    if len(b)!=v['bytes'] or hashlib.sha256(b).hexdigest()!=v['sha256']: bad.append(k)
print('ficheros contrastados',n,'discrepancias',len(bad),'no encontrados',len(falta),bad[:5],falta[:5])
