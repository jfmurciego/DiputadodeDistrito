#!/usr/bin/env python3
"""Municipio→comarca agraria desde el Anexo I del RD 1076/2014 (BOE-A-2014-13257), conciliado con el INE 2025.
Uso: generar_comarcas_agrarias.py <rd1076.xml> <salida.csv> [sin_conciliar.csv]   (ejecutar desde la raíz del repo)"""
import csv, hashlib, re, sys, html, unicodedata
from collections import defaultdict
ART={"el","la","los","las","l","les","lo","a","o","as","os","sa","ses","es","els","s","na"}
def plegar(x):
    x=unicodedata.normalize("NFD",x.lower()); x="".join(c for c in x if not unicodedata.combining(c))
    return "".join(t for t in re.findall(r"[a-z0-9]+",x) if t not in ART)
def leer(xml):
    a=xml.index('<p class="anexo_num">ANEXO I<'); s=xml[a:xml.index('<p class="anexo_num">ANEXO II<',a)]
    prov=None; filas=[]
    for t in re.findall(r'<p class="([^"]*)">(.*?)</p>',s,re.S):
        c,tx=t; tx=html.unescape(re.sub(r"<[^>]+>","",tx)).strip()
        if c=="centro_cursiva" or c.startswith("anexo") or not tx: continue
        if tx.endswith(":") and ":" not in tx[:-1]: prov=tx[:-1].strip(); continue
        if ":" in tx and prov:
            com,ms=tx.split(":",1)
            if com.upper()!=com: continue
            for m in re.split(r",\s*(?![^()]*\))",ms.strip().rstrip(".")):
                if m.strip(): filas.append((prov,com.strip(),m.strip()))
    return filas
def main(xmlp,out,out2=None):
    xml=open(xmlp,encoding="utf-8").read(); filas=leer(xml)
    ine={r["codigo_ine"]:r["nombre_ine"] for r in csv.DictReader(open("datos/distritos/municipios_ine_2025.csv",encoding="utf-8"))}
    idx=defaultdict(list)
    for k,n in ine.items():
        for v in re.split(r"\s*/\s*",n): idx[plegar(v)].append(k)
    # provincia por voto de coincidencias únicas
    voto=defaultdict(lambda:defaultdict(int))
    for p,c,m in filas:
        for v in re.split(r"\s*/\s*",m):
            ks=idx.get(plegar(v),[])
            if len(ks)==1: voto[p][ks[0][:2]]+=1
    cp={p:max(v,key=v.get) for p,v in voto.items()}
    asig={}; no=[]
    for p,c,m in filas:
        pr=cp.get(p); ks=set()
        for v in re.split(r"\s*/\s*",m): ks|={k for k in idx.get(plegar(v),[]) if k[:2]==pr}
        ks={k for k in ks if k not in asig}
        if len(ks)==1: asig[ks.pop()]=(p,c,m)
        else: no.append((p,c,m,len(ks)))
    sin=sorted(set(ine)-set(asig))
    h=hashlib.sha256(xml.encode()).hexdigest()
    with open(out,"w",encoding="utf-8",newline="") as f:
        f.write(f"# fuente: Real Decreto 1076/2014 Anexo I (comarcas agrarias, municipios del Catastro de rústica 2013); BOE-A-2014-13257; https://www.boe.es/diario_boe/xml.php?id=BOE-A-2014-13257; sha256 del XML {h}\n")
        w=csv.writer(f,lineterminator="\n"); w.writerow(["codigo_ine","provincia","comarca_agraria","id_comarca","nombre_ine","nombre_anexo"])
        for k in sorted(asig):
            p,c,m=asig[k]; w.writerow([k,k[:2],c,f"{k[:2]}-{c}",ine[k],m])
    if out2:
        with open(out2,"w",encoding="utf-8",newline="") as f:
            w=csv.writer(f,lineterminator="\n"); w.writerow(["origen","provincia","comarca","nombre","candidatos"])
            for p,c,m,n in no: w.writerow(["anexo",p,c,m,n])
            for k in sin: w.writerow(["ine_2025",k[:2],"",ine[k]+f" ({k})",""])
    print(f"filas={len(filas)} asignados={len(asig)}/{len(ine)} ({len(asig)/len(ine):.2%}) anexo_sin_casar={len(no)} ine_sin_comarca={len(sin)} comarcas={len({v[1]+v[0] for v in asig.values()})} sha256={h}")
if __name__=="__main__": main(*sys.argv[1:])
