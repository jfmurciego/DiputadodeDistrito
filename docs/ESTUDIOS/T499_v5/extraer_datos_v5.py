"""T-499 · maqueta de diseño de la V5 (no es código de producto).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-25 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: T-499, diseño al detalle de la V5.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: Extrae de BOE-A-2023-18907 (XML con sha256 comprobado a mano) los votos a candidaturas por provincia (cuadros II y III) y los junta con configuracion/resultados_oficiales_congreso_2023.csv. Uso: python -I extraer_datos_v5.py <BOE.xml> <csv> > datos_v5_2023.json
"""
import re,html,json,csv,hashlib,sys
xmlp,csvp=sys.argv[1],sys.argv[2]
raw=open(xmlp,'rb').read(); t=raw.decode('utf-8')
tabs=re.findall(r'<table.*?</table>',t,re.S)
num=lambda s:int(re.sub(r'[^0-9]','',s) or 0)
tot={}; est=0
for tb in tabs:
  rows=[[html.unescape(re.sub('<[^>]+>','',c)).strip() for c in re.findall(r'<t[dh].*?</t[dh]>',r,re.S)] for r in re.findall(r'<tr.*?</tr>',tb,re.S)]
  con_esc=rows[1][1]=='Escaños'
  for r in rows[2:]:
    vals=r[2::2] if con_esc else r[1:]
    s=sum(num(v) for v in vals)
    if r[0].startswith('Total estatal'): est+=s
    else: tot[r[0]]=tot.get(r[0],0)+s
print('provincias',len(tot),'suma',sum(tot.values()),'total estatal',est,file=sys.stderr)
assert sum(tot.values())==est and len(tot)==52
filas=list(csv.DictReader(open(csvp,encoding='utf-8')))
orden=[]; [orden.append((f['codigo'],f['provincia'],int(f['escanos_circunscripcion']))) for f in filas if (f['codigo'],f['provincia'],int(f['escanos_circunscripcion'])) not in orden]
claves=list(tot)  # mismo orden del BOE; emparejar por orden
ORDEN=['02','03','04','01','33','05','06','07','08','48','09','10','11','39','12','13','14','15','16','20','17','18','19','21','22','23','24','25','27','28','29','30','31','32','34','35','36','26','37','38','40','41','42','43','44','45','46','47','49','50','51','52']
cand=dict(zip(ORDEN,[tot[k] for k in claves]))
prov={}
for c,n,e in orden:
  ps=[f for f in filas if f['codigo']==c]
  prov[c]={'nombre':n,'escanos':e,'votos_candidaturas':cand[c],
    'partidos':sorted([{'p':f['partido'],'votos':int(f['votos']),'escanos':int(f['escanos'])} for f in ps],key=lambda x:(-x['escanos'],-x['votos']))}
  assert sum(x['escanos'] for x in ps for x in [ {'escanos':int(x['escanos'])}])==e
print(json.dumps({'fuente':'BOE-A-2023-18907 (cuadros II y III)','sha256_xml':hashlib.sha256(raw).hexdigest(),
 'csv':'configuracion/resultados_oficiales_congreso_2023.csv','sha256_csv':hashlib.sha256(open(csvp,'rb').read()).hexdigest(),
 'votos_candidaturas_estatal':est,'denominador':'votos a candidaturas (suma de los cuadros II y III por circunscripción; sin votos en blanco)',
 'provincias':prov},ensure_ascii=False,indent=1))
