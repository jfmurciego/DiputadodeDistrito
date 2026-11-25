"""T-499 · maqueta de diseño de la V5 (no es código de producto).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-25 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: T-499, diseño al detalle de la V5.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: Genera la maqueta estática (SVG en HTML) de la V5 con visor/v2/datos/provincias.json y datos_v5_2023.json. Uso: python -I generar_maqueta_v5.py <provincias.json> <datos_v5_2023.json> <salida.html>
"""
import json,math,sys,html
g=json.load(open(sys.argv[1]));d=json.load(open(sys.argv[2]));out=sys.argv[3]
K=72;SP=11;R=4.1;CO=math.cos(math.radians(40))
PAL={"PP":"#1d6fb8","PSOE":"#d32b2b","VOX":"#5fa335","SUMAR":"#cf2a7b","ERC":"#f0ac00","JUNTS":"#18a99b",
 "EH Bildu":"#0f7a52","EAJ-PNV":"#2c5e36","BNG":"#7cb2d8","CCa":"#e8c400","UPN":"#3a55a2"}
NOM={"PP":"PP","PSOE":"PSOE (con PSC)","VOX":"Vox","SUMAR":"Sumar","ERC":"ERC","JUNTS":"Junts","EH Bildu":"EH Bildu",
 "EAJ-PNV":"PNV","BNG":"BNG","CCa":"CC","UPN":"UPN"}
CLASES=[(45,0.0,"≥ 45 %"),(35,0.2,"35–45 %"),(30,0.4,"30–35 %"),(0,0.55,"< 30 %")]
def mix(h,t):
  r,g_,b=(int(h[i:i+2],16) for i in (1,3,5));return "#%02x%02x%02x"%tuple(round(v+(255-v)*t) for v in (r,g_,b))
P=lambda lo,la:((lo+12.75)*CO*K+10,(43.95-la)*K+10)
def polys(f):
  c=f['geometry']['coordinates'];return c if f['geometry']['type']=='MultiPolygon' else [c]
def inside(x,y,poly):
  r=False
  for ring in poly:
    for i in range(len(ring)):
      (x1,y1),(x2,y2)=ring[i],ring[i-1]
      if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1: r=not r
  return r
def dseg(px,py,a,b):
  (x1,y1),(x2,y2)=a,b;dx,dy=x2-x1,y2-y1;L=dx*dx+dy*dy or 1e-9
  t=max(0,min(1,((px-x1)*dx+(py-y1)*dy)/L));return math.hypot(px-x1-t*dx,py-y1-t*dy)
def dedge(x,y,pp):return min(dseg(x,y,r[i],r[i-1]) for poly in pp for r in poly for i in range(len(r)))
def lattice(x0,x1,y0,y1,cx,cy):
  pts=[];row=0;y=cy-math.ceil((cy-y0)/(SP*.866))*SP*.866
  while y<=y1:
    k=round((y-cy)/(SP*.866));off=SP/2 if k%2 else 0
    x=cx+off-math.ceil((cx+off-x0)/SP)*SP
    while x<=x1: pts.append((x,y));x+=SP
    y+=SP*.866
  return pts
DESPL={"08":(52,22)}   # Barcelona: racimo al mar con línea guía
shapes=[];dots=[];lines=[];lab=[];fitinfo={}
tot={}
for f in g['features']:
  c=f['properties']['cod'];pr=d['provincias'][c];n=pr['escanos']
  for x in pr['partidos']: tot.setdefault(x['p'],[0,0]);tot[x['p']][0]+=x['votos'];tot[x['p']][1]+=x['escanos']
  pp=[[[P(*p) for p in r] for r in poly] for poly in polys(f)]
  win=max(pr['partidos'],key=lambda x:x['votos']);pct=100*win['votos']/pr['votos_candidaturas']
  t=next(tt for lim,tt,_ in CLASES if pct>=lim);fill=mix(PAL[win['p']],t)
  dpath=" ".join("M"+" L".join("%.1f,%.1f"%p for p in r)+"Z" for poly in pp for r in poly)
  shapes.append(f'<path d="{dpath}" fill="{fill}" fill-opacity="0.88" stroke="#fff" stroke-width="0.9"><title>{html.escape(pr["nombre"])}: {NOM[win["p"]]} {pct:.1f} %</title></path>'.replace(".", ".").replace("%.","%.") )
  if c in ("51","52"): continue
  big=max(pp,key=lambda poly:len(poly[0]))
  xs=[p[0] for p in big[0]];ys=[p[1] for p in big[0]]
  cand=[p for p in lattice(min(xs),max(xs),min(ys),max(ys),sum(xs)/len(xs),sum(ys)/len(ys)) if inside(*p,big)]
  cx,cy=max(cand,key=lambda p:dedge(*p,[big])) if cand else (sum(xs)/len(xs),sum(ys)/len(ys))
  allp=[(x,y) for poly in pp for p_ in [poly] for (x,y) in []]
  if c in DESPL:
    ax,ay=cx+DESPL[c][0],cy+DESPL[c][1]
    pts=sorted(lattice(ax-80,ax+80,ay-80,ay+80,ax,ay),key=lambda p:math.hypot(p[0]-ax,p[1]-ay))[:n]
    lines.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ax:.1f}" y2="{ay:.1f}" stroke="#3a4652" stroke-width="1"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" fill="#3a4652"/>')
    halo=True;modo="desplazado"
  else:
    lat=lattice(cx-120,cx+120,cy-120,cy+120,cx,cy)
    ins=[p for p in lat if any(inside(*p,poly) for poly in pp) and dedge(*p,pp)>=R*0.55]
    ins.sort(key=lambda p:math.hypot(p[0]-cx,p[1]-cy))
    if len(ins)>=n: pts=ins[:n];halo=False;modo="dentro"
    else:
      pts=sorted(lat,key=lambda p:math.hypot(p[0]-cx,p[1]-cy))[:n];halo=True;modo="desborda"
  fitinfo[pr['nombre']]=modo
  pts.sort(key=lambda p:(round(p[1],1),p[0]))
  seq=[x['p'] for x in pr['partidos'] for _ in range(x['escanos'])]
  if halo:
    hx=[p[0] for p in pts];hy=[p[1] for p in pts]
    dots.append(f'<rect x="{min(hx)-R-3:.1f}" y="{min(hy)-R-3:.1f}" width="{max(hx)-min(hx)+2*R+6:.1f}" height="{max(hy)-min(hy)+2*R+6:.1f}" rx="7" fill="#fff" fill-opacity="0.85" stroke="#3a4652" stroke-width="0.8"/>')
  for (x,y),p in zip(pts,seq):
    dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{R}" fill="{PAL[p]}" stroke="#fff" stroke-width="1.1"><title>{html.escape(pr["nombre"])} · {NOM[p]}</title></circle>')
  if n>=12 or c in DESPL: lab.append((cx,cy,pr['nombre'],n,c))
# recuadro Canarias (la geometría del visor ya la trae desplazada)
cbx=[P(-12.75,36.25),P(-7.55,34.05)]
frames=[f'<rect x="{cbx[0][0]:.1f}" y="{cbx[0][1]:.1f}" width="{cbx[1][0]-cbx[0][0]:.1f}" height="{cbx[1][1]-cbx[0][1]:.1f}" fill="none" stroke="#5b6470" stroke-width="1" stroke-dasharray="4 3"/><text x="{cbx[0][0]+6:.1f}" y="{cbx[0][1]+14:.1f}" class="rot">Canarias</text>']
# recuadros Ceuta y Melilla, ampliados ×8
def recuadro(c,x0,y0):
  f=next(f for f in g['features'] if f['properties']['cod']==c);pr=d['provincias'][c]
  win=max(pr['partidos'],key=lambda x:x['votos']);pct=100*win['votos']/pr['votos_candidaturas']
  t=next(tt for lim,tt,_ in CLASES if pct>=lim);ring=polys(f)[0][0]
  xs=[P(*p)[0] for p in ring];ys=[P(*p)[1] for p in ring];mx,my=sum(xs)/len(xs),sum(ys)/len(ys);s=8
  pth="M"+" L".join("%.1f,%.1f"%(x0+46+(x-mx)*s,y0+40+(y-my)*s) for x,y in zip(xs,ys))+"Z"
  o=f'<rect x="{x0}" y="{y0}" width="92" height="74" fill="#fff" fill-opacity=".6" stroke="#5b6470" stroke-width="1" stroke-dasharray="4 3"/><path d="{pth}" fill="{mix(PAL[win["p"]],t)}" fill-opacity=".88" stroke="#fff"/>'
  o+=f'<circle cx="{x0+46}" cy="{y0+40}" r="{R}" fill="{PAL[win["p"]]}" stroke="#fff" stroke-width="1.1"/><text x="{x0+6}" y="{y0+13}" class="rot">{pr["nombre"]} · {pct:.0f} %</text>'
  return o
xm,ym=P(-7.3,36.25)
frames.append(recuadro("51",xm,ym));frames.append(recuadro("52",xm+100,ym))
W,H=P(4.5,34.0)
labels="".join(f'<text x="{x:.1f}" y="{y-(SP*3.2 if c!="08" else -SP*4.2):.1f}" class="lbl" text-anchor="middle">{html.escape(nm)} {n}</text>' for x,y,nm,n,c in lab if c not in ("08",))
bx,by=next((x,y) for x,y,nm,n,c in lab if c=="08");labels+=f'<text x="{bx+DESPL["08"][0]:.1f}" y="{by+DESPL["08"][1]-SP*3.4:.1f}" class="lbl" text-anchor="middle">Barcelona 32</text>'
svg=f'<svg viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#eef3f7"/>{"".join(shapes)}{"".join(frames)}{"".join(lines)}{"".join(dots)}{labels}</svg>'
E=d['votos_candidaturas_estatal'];orden=sorted(tot,key=lambda p:(-tot[p][1],-tot[p][0]))
otros=E-sum(v[0] for v in tot.values())
rows="".join(f'<tr><td><i style="background:{PAL[p]}"></i>{NOM[p]}</td><td>{100*tot[p][0]/E:.1f} %</td><td>{tot[p][1]}</td></tr>' for p in orden)
rows+=f'<tr class="ot"><td><i style="background:#9aa3ad"></i>Resto (sin escaño)</td><td>{100*otros/E:.1f} %</td><td>0</td></tr><tr class="tt"><td>Total</td><td>100 %</td><td>{sum(v[1] for v in tot.values())}</td></tr>'
esc="".join(f'<li><span style="background:{mix("#1d6fb8",t)}"></span>{txt}</li>' for _,t,txt in CLASES)
page=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Maqueta V5</title><style>
body{{margin:0;font:13px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif;color:#1c2630;background:#fff}}
.wrap{{display:flex;gap:18px;padding:16px;align-items:flex-start}} h1{{font-size:17px;margin:0 0 2px}} .sub{{color:#5b6470;margin:0 0 10px}}
.lbl{{font:600 11px system-ui,sans-serif;fill:#1c2630;paint-order:stroke;stroke:#fff;stroke-width:3px}} .rot{{font:600 10px system-ui,sans-serif;fill:#3a4652}}
aside{{width:290px;flex:none}} table{{border-collapse:collapse;width:100%}} td{{padding:4px 6px;border-bottom:1px solid #e3e8ed}} td:nth-child(n+2){{text-align:right;font-variant-numeric:tabular-nums}}
th{{text-align:left;font-size:11px;color:#5b6470;padding:4px 6px}} th:nth-child(n+2){{text-align:right}}
td i{{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:7px;vertical-align:-1px;border:1px solid #fff;box-shadow:0 0 0 1px #c9d1d8}}
.ot td{{color:#5b6470}} .tt td{{font-weight:700;border-bottom:0}} h3{{font-size:13px;margin:14px 0 6px}}
ul{{list-style:none;padding:0;margin:0;display:flex;gap:4px}} li{{flex:1;font-size:11px;text-align:center}} li span{{display:block;height:14px;border-radius:3px;margin-bottom:3px}}
small{{color:#5b6470;display:block;margin-top:10px}}</style></head><body><div class="wrap"><div>
<h1>Congreso 2023 · situación actual</h1><p class="sub">Un punto por diputado (350), escaños oficiales. Provincia coloreada por el partido más votado; intensidad según su % de voto.</p>{svg}</div>
<aside><h3>Partidos con escaño</h3><table><tr><th>Partido</th><th>% voto</th><th>Escaños</th></tr>{rows}</table>
<h3>Intensidad: % del más votado</h3><ul>{esc}</ul>
<small>Fuente: BOE-A-2023-18907 (Junta Electoral Central), cuadros II y III. % sobre votos a candidaturas. Sin estimaciones ni encuestas. Maqueta de diseño (T-499), no es el visor.</small></aside></div></body></html>'''
open(out,'w').write(page)
print(json.dumps({k:v for k,v in fitinfo.items() if v!='dentro'},ensure_ascii=False),file=sys.stderr)
