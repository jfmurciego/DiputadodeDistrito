#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calendario de elecciones autonómicas por comunidad (T-121, paso 1).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: orden del propietario (09-11): histórico autonómico desde 2011; cada comunidad tiene legislaturas de duración propia.
CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/calendario_autonomicas_v1.0.0_20261112.py
QUÉ HACE: lee dos instantáneas con sha256 del Observatorio Electoral de las Naciones (fuentes/observatorio_autonomicas/):
  index.json (calendario por comunidad, código INE 01-17, mes AAAAMM) e iturriak.html (proveedor, URL, granularidad,
  completitud y verificación oficial de cada elección). Escribe configuracion/calendario_autonomicas.csv.
  El día exacto NO sale de memoria: solo se rellena con configuracion/legislatura_vigente.yaml (elección vigente, con su
  fuente) y debe coincidir con el mes del Observatorio; el resto queda con precision=mes hasta contrastarlo con el BOE/boletín.
  Duración = meses hasta la siguiente convocatoria de la misma comunidad (la vigente, fin abierto). La disolución
  anticipada se DERIVA (adelanto = 48 - duración; >=2 meses → «si», 1 → «revisar»): no es dato de boletín.
  Ceuta y Melilla no tienen elecciones autonómicas (asambleas locales, elegidas con las municipales): no figuran en la fuente.
Uso: python herramientas/calendario_autonomicas.py generar | comprobar
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FUENTE_DIR = "fuentes/observatorio_autonomicas"
SALIDA = "configuracion/calendario_autonomicas.csv"
URL_INDEX = "https://nazioenbehatokia.eus/data/autonomikoak/index.json"
URL_ITURRIAK = "https://nazioenbehatokia.eus/iturriak.html"
INICIO = "201101"
LEGISLATURA_MESES = 48
# código INE de comunidad -> (territory_id del catálogo, etiqueta de la tabla «iturriak» del Observatorio)
COMUNIDADES = {
    "01": ("aut01", "Andalucía"), "02": ("aut02", "Aragón"), "03": ("aut03", "Asturies"),
    "04": ("aut04", "Illes Balears"), "05": ("aut05", "Canarias"), "06": ("aut06", "Cantabria"),
    "07": ("aut07", "Castilla y León"), "08": ("aut08", "Castilla-La Mancha"),
    "09": ("aut09", "Catalunya"), "10": ("aut10", "País Valencià"), "11": ("aut11", "Extremadura"),
    "12": ("aut12", "Galiza"), "13": ("aut13", "Madrid"), "14": ("aut14", "Murcia"),
    "15": ("aut15", "Nafarroa Garaia"), "16": ("aut16", "EAE"), "17": ("aut17", "La Rioja"),
}
SIN_PARLAMENTO = ("aut18", "aut19")
MESES = {m: i + 1 for i, m in enumerate("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split())}
CAMPOS = ["comunidad", "cod_ine", "mes", "fecha", "precision", "en_alcance", "vigente", "fin_legislatura_mes",
          "duracion_meses", "adelanto_meses", "disolucion_anticipada", "proveedor_resultados", "url_resultados",
          "granularidad", "completitud", "url_verificacion", "fuente_calendario", "fuente_url", "fuente_sha256"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parsear_iturriak(texto: str) -> list[dict]:
    """Filas de la tabla «Elecciones autonómicas · fuente de cada elección» → dicts."""
    filas = []
    for tr in re.findall(r"<tr>(.*?)</tr>", texto, re.S):
        th = re.search(r"<th>(.*?)</th>", tr, re.S)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if not th or len(tds) != 5:
            continue
        m = re.fullmatch(r"(\w+) de (\d{4})", html.unescape(re.sub(r"<[^>]*>", "", tds[0])).strip())
        if not m or m.group(1) not in MESES:
            continue

        def txt(x): return html.unescape(re.sub(r"<[^>]*>", "", x)).strip()

        def url(x):
            u = re.search(r'href="([^"]+)"', x)
            return html.unescape(u.group(1)) if u else ""
        filas.append({"etiqueta": html.unescape(th.group(1)).strip(), "mes": f"{m.group(2)}{MESES[m.group(1)]:02d}",
                      "proveedor": txt(tds[1]), "url": url(tds[1]), "granularidad": txt(tds[2]),
                      "completitud": txt(tds[3]), "verificacion": url(tds[4])})
    return filas


def dif_meses(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[4:]) - int(a[4:])


def construir(raiz: Path = ROOT) -> list[dict]:
    idx_p, it_p = raiz / FUENTE_DIR / "index.json", raiz / FUENTE_DIR / "iturriak.html"
    idx = json.loads(idx_p.read_text(encoding="utf-8"))
    it = parsear_iturriak(it_p.read_text(encoding="utf-8"))
    por_clave = {}
    for f in it:
        por_clave.setdefault((f["etiqueta"], f["mes"]), []).append(f)
    vig = yaml.safe_load((raiz / "configuracion/legislatura_vigente.yaml").read_text(encoding="utf-8"))
    dias = {t["territory_id"]: str(t["fecha"]) for t in vig["territorios"] if t.get("ambito") != "nacional"}
    meses: dict[str, list[str]] = {}
    for dia in idx["egunak"]:
        for cca, aaaamm in dia["osagaiak"].items():
            meses.setdefault(cca, []).append(aaaamm)
    # la tabla de fuentes también lista las elecciones «sin datos» (Cantabria 2011), que el índice marca como hutsik
    etiq = {e: c for c, (_, e) in COMUNIDADES.items()}
    de_tabla = {(etiq[f["etiqueta"]], f["mes"]) for f in it}
    de_indice = {(c, m) for c, ms in meses.items() for m in ms}
    huecos = {(c, dia["k"][1:]) for dia in idx["egunak"] for c in dia.get("hutsik", [])}
    if de_indice - de_tabla or de_tabla - de_indice != huecos:
        raise SystemExit(f"índice y tabla de fuentes discrepan: {sorted(de_indice - de_tabla)} / {sorted(de_tabla - de_indice - huecos)}")
    for c, m in huecos:
        meses.setdefault(c, []).append(m)
    desconocidas = sorted(set(meses) - set(COMUNIDADES))
    if desconocidas:
        raise SystemExit(f"códigos de comunidad sin mapear: {desconocidas}")
    filas = []
    for cca, (tid, etiqueta) in COMUNIDADES.items():
        lista = sorted(meses.get(cca, []))
        for i, aaaamm in enumerate(lista):
            src = por_clave.get((etiqueta, aaaamm))
            if not src or len(src) != 1:
                raise SystemExit(f"{tid} {aaaamm}: la tabla de fuentes del Observatorio tiene {len(src or [])} filas (esperada 1)")
            f = src[0]
            sig = lista[i + 1] if i + 1 < len(lista) else ""
            dur = dif_meses(aaaamm, sig) if sig else ""
            adel = max(0, LEGISLATURA_MESES - dur) if sig else ""
            fecha = ""
            if not sig and tid in dias:
                if dias[tid][:7].replace("-", "") != aaaamm:
                    raise SystemExit(f"{tid}: legislatura_vigente.yaml ({dias[tid]}) no coincide con el Observatorio ({aaaamm})")
                fecha = dias[tid]
            filas.append({
                "comunidad": tid, "cod_ine": cca, "mes": f"{aaaamm[:4]}-{aaaamm[4:]}", "fecha": fecha,
                "precision": "dia" if fecha else "mes", "en_alcance": "si" if aaaamm >= INICIO else "no (previa)",
                "vigente": "si" if not sig else "no", "fin_legislatura_mes": f"{sig[:4]}-{sig[4:]}" if sig else "",
                "duracion_meses": dur, "adelanto_meses": adel,
                "disolucion_anticipada": "" if not sig else ("si" if adel >= 2 else "revisar" if adel == 1 else "no"),
                "proveedor_resultados": f["proveedor"], "url_resultados": f["url"], "granularidad": f["granularidad"],
                "completitud": f["completitud"], "url_verificacion": f["verificacion"],
                "fuente_calendario": "Observatorio Electoral de las Naciones (data/autonomikoak/index.json + iturriak.html)",
                "fuente_url": f"{URL_INDEX} ; {URL_ITURRIAK}", "fuente_sha256": f"{sha(idx_p)} ; {sha(it_p)}"})
    filas.sort(key=lambda r: (r["comunidad"], r["mes"]))
    return filas


def escribir(filas: list[dict], destino: Path) -> None:
    with destino.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, CAMPOS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def main(argv: list[str]) -> int:
    modo = argv[0] if argv else "comprobar"
    filas = construir()
    if modo == "generar":
        escribir(filas, ROOT / SALIDA)
        print(f"{len(filas)} filas → {SALIDA}")
        return 0
    esperado = ROOT / SALIDA
    tmp = esperado.with_suffix(".tmp")
    escribir(filas, tmp)
    ok = tmp.read_bytes() == esperado.read_bytes()
    tmp.unlink()
    print("OK" if ok else f"{SALIDA} desactualizado: ejecuta generar")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
