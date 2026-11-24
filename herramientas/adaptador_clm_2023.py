#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adaptador de las autonómicas de Castilla-La Mancha (28-05-2023) a votos por municipio y partido (T-449).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-24 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: D-183 (aut08 por municipio) y decisión del propietario (24-11): la fuente es la copia archivada en la Wayback del xlsx oficial
  de la Junta (Resultados_CLM_2023.xlsx, captura 20261023040608, sha256 7591997d…, medida en el run 45283716584), declarada fuente NO
  oficial porque el portal de la Junta ya no la sirve. Se versiona su hoja «Municipios_Resultados» volcada a CSV por el espejo (sha256 del
  volcado en el manifiesto de ese run). No hay totales oficiales en fichero (el PDF de la Junta no está ni en origen ni en la Wayback):
  el cuadre es contra el Observatorio Electoral de las Naciones (hauteskundea/08-202305.json, «provisional», fuente NO oficial, la misma
  que usa el calendario), y debe ser EXACTO o falla.
QUÉ HACE: verifica el sha256 del volcado y del fichero del Observatorio; escribe `municipios.csv` (municipio INE de 5 cifras, partido =
  sigla de la fuente, votos) y `MANIFEST.json`. «Residentes ausentes-<provincia>» (voto CERA) no se reparte: va en
  `votos_ausentes_no_repartidos`. Cuadre: (1) votos por candidatura y provincia sin CERA = `probintzia` del Observatorio; (2) CERA por
  candidatura y provincia = `cera`; (3) D'Hondt con barrera del 3 % de los votos a candidaturas de la provincia (CERA incluido) = escaños
  por provincia del Observatorio (`barrutiak`), 33 en total.
NO HACE: descargar, repartir a sección (lo hace doble_vuelta_votos_aut.py), lanzar ni publicar.
Uso: python herramientas/adaptador_clm_2023.py --salida DIR
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOLCADO = "fuentes/castilla_la_mancha_autonomicas_2023/municipios_resultados.csv"
VOLCADO_SHA256 = "6d44efc55d936c02e2d95379ce54516a3a844e28cf45c837ba149daebaa11967"  # hoja-1.csv del run 45283716584
XLSX = {"url": "https://web.archive.org/web/20261023040608id_/https://datosabiertos.castillalamancha.es/sites/"
               "datosabiertos.castillalamancha.es/files/Resultados_CLM_2023.xlsx",
        "sha256": "7591997d17c65586bd5d8ac68776e9946e233997f86cbe1c22e08018c16347ca", "bytes": 322602,
        "tipo": "copia_archivada", "oficial": False, "captura": "20261023040608", "run_medida": "45283716584"}
OBSERVATORIO = "fuentes/observatorio_autonomicas/hauteskundea_08-202305.json"
OBSERVATORIO_SHA256 = "0443c79e983f2f8cacd0d992899ff47ecfad0a7317503fc94efe85bb10a63e95"
OBSERVATORIO_URL = "https://nazioenbehatokia.eus/data/autonomikoak/hauteskundea/08-202305.json"
PROVINCIAS = ("02", "13", "16", "19", "45")  # Albacete, Ciudad Real, Cuenca, Guadalajara, Toledo
# siglas del Observatorio → siglas de la fuente (las demás coinciden)
SIGLAS_OBSERVATORIO = {"UNIDAS PODEMOS": "UNIDAS PODEMOS CLM", "Cs": "CS"}
BARRERA = 0.03


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dhondt(votos: dict[str, int], escanos: int, barrera: float = BARRERA) -> dict[str, int]:
    umbral = barrera * sum(votos.values())
    cocientes = sorted(((v / d, v, s) for s, v in votos.items() if v >= umbral for d in range(1, escanos + 1)), reverse=True)
    return dict(Counter(s for _, _, s in cocientes[:escanos]))


def leer_volcado(ruta: Path) -> list[tuple[str, str, str, str, int]]:
    filas = list(csv.reader(ruta.read_text(encoding="utf-8").splitlines()))
    cab = next(i for i, r in enumerate(filas) if r[:7] == ["Provincia", "Municipio", "Nombre", "Candidatura", "Siglas", "Denominación", "Votos"])
    out = []
    for r in filas[cab + 1:]:
        if len(r) >= 7 and r[6].strip():
            out.append((r[0].strip(), r[1].strip(), r[2].strip(), r[4].strip(), int(r[6])))
    if len(out) < 8000:
        raise ValueError(f"volcado incompleto: {len(out)} filas")
    return out


def construir(salida: Path, raiz: Path = ROOT) -> dict:
    vol, obs_p = raiz / VOLCADO, raiz / OBSERVATORIO
    if sha256(vol) != VOLCADO_SHA256:
        raise ValueError(f"sha256 del volcado no coincide: {sha256(vol)}")
    if sha256(obs_p) != OBSERVATORIO_SHA256:
        raise ValueError(f"sha256 del Observatorio no coincide: {sha256(obs_p)}")
    obs = json.loads(obs_p.read_text(encoding="utf-8"))
    sig = [SIGLAS_OBSERVATORIO.get(s, s) for s in obs["s"]]
    votos: dict[str, Counter] = defaultdict(Counter)
    prov: dict[str, Counter] = defaultdict(Counter)
    cera: dict[str, Counter] = defaultdict(Counter)
    for p, m, nombre, sigla, v in leer_volcado(vol):
        if p not in PROVINCIAS:
            raise ValueError(f"provincia fuera de Castilla-La Mancha: {p}")
        if nombre.startswith("Residentes ausentes"):
            cera[p][sigla] += v
        else:
            votos[f"{p}{m.zfill(3)}"][sigla] += v
            prov[p][sigla] += v
    fallos = []
    for p in PROVINCIAS:
        esperado = {sig[i]: v for i, v in obs["probintzia"][p][3]}
        if {s: v for s, v in prov[p].items() if v} != {s: v for s, v in esperado.items() if v}:
            fallos.append(f"votos {p}: {dict(prov[p])} ≠ {esperado}")
        esperado_cera = {sig[i]: v for i, v in obs["cera"][p][5]}
        if {s: v for s, v in cera[p].items() if v} != {s: v for s, v in esperado_cera.items() if v}:
            fallos.append(f"CERA {p}: {dict(cera[p])} ≠ {esperado_cera}")
    escanos_obs = {b[1]: {sig[i]: k for i, k in b[2]} for b in obs["barrutiak"]}
    escanos = {}
    for p in PROVINCIAS:
        k = sum(escanos_obs[p].values())
        escanos[p] = dhondt(dict(prov[p] + cera[p]), k)
        if escanos[p] != escanos_obs[p]:
            fallos.append(f"escaños {p}: {escanos[p]} ≠ {escanos_obs[p]}")
    total_escanos = sum(sum(e.values()) for e in escanos.values())
    if total_escanos != sum(k for _, k in obs["eserlekuak"]):
        fallos.append(f"escaños totales {total_escanos}")
    salida.mkdir(parents=True, exist_ok=True)
    with (salida / "municipios.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["municipio", "partido", "votos"])
        for m in sorted(votos):
            for s, v in sorted(votos[m].items()):
                if v:
                    w.writerow([m, s, v])
    ausentes = Counter()
    for c in cera.values():
        ausentes.update(c)
    man = {"schema": "ddd-clm-2023/1.0", "territorio": "aut08", "eleccion": "202305", "nivel": "municipio", "aproximado_en_distrito": True,
           "fuente": {**XLSX, "volcado": VOLCADO, "volcado_sha256": VOLCADO_SHA256,
                      "nota": "copia archivada del fichero oficial de la Junta; fuente NO oficial (decisión del propietario, 24-11)"},
           "cuadre_contra": {"url": OBSERVATORIO_URL, "fichero": OBSERVATORIO, "sha256": OBSERVATORIO_SHA256,
                             "nota": "Observatorio Electoral de las Naciones, marcado «provisional»; fuente NO oficial (no hay totales oficiales en fichero)"},
           "municipios": len(votos), "votos_por_provincia": {p: sum(prov[p].values()) for p in PROVINCIAS},
           "cera_por_provincia": {p: sum(cera[p].values()) for p in PROVINCIAS}, "votos_ausentes_no_repartidos": {s: v for s, v in sorted(ausentes.items()) if v},
           "escanos_dhondt": {p: dict(sorted(e.items())) for p, e in escanos.items()}, "escanos_total": total_escanos,
           "cuadra": not fallos, "fallos": fallos}
    man["fuentes"] = {"fuente": man["fuente"], "cuadre_observatorio": {**man["cuadre_contra"], "cuadra": not fallos,
                                                                      "escanos_dhondt": man["escanos_dhondt"]}}  # lo lee doble_vuelta_votos_aut
    (salida / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if fallos:
        raise ValueError("no cuadra con el Observatorio: " + "; ".join(fallos))
    return man


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args(argv)
    m = construir(a.salida)
    print(json.dumps({k: m[k] for k in ("municipios", "cuadra", "escanos_total")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
