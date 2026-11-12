#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cuadre del histórico reagregado de España (T-110) con Infoelectoral y con el espejo del Observatorio.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: T-110 (orden del propietario): cuadrar la salida de `reagregacion_historico.py --lote` en las 52 provincias.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: fuera de línea. Por provincia (52) y elección: (1) total de candidaturas del espejo T-89 (Observatorio)
  frente al de Infoelectoral (2023-07, ZIP nacional por mesa, ficheros 08 por provincia y 10 por mesa sin CERA) y frente
  a los CSV oficiales versionados (BOE, 2019-11 y 2023); (2) lo reagregado a distritos (MANIFEST.json) frente al espejo;
  (3) el ganador de 2023 por distrito frente al M08 versionado en `datos/resultados/<circunscripción NAC>.csv`.
  El espejo suma secciones y no incluye el voto CERA: nunca debe superar a la oficial. Escribe un JSON con el cuadre y
  la lista de lo que no cuadra con su motivo.
Uso: python herramientas/cuadre_historico_espana.py --espejo DIR --mesas ZIP --salida JSON
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
import equivalencia_seccionados as eqs  # noqa: E402
import fuente_nazioenbehatokia as fnb  # noqa: E402

TOLERANCIA = 0.10  # defecto máximo admitido del espejo frente a la oficial (CERA + redondeos)


def leer_infoelectoral(zpath: Path, sufijo: str = "022307") -> dict:
    """{provincia: {"total_cand": int, "cera": int, "mesas_sin_cera": int, "partidos": {sigla: votos}}}.
    Fichero 08: votos por candidatura y provincia (columna 20-27); 10: por mesa (municipio 999 = CERA)."""
    z = zipfile.ZipFile(zpath)
    sig = {}
    for ln in z.read(f"03{sufijo}.DAT").decode("latin-1").splitlines():
        sig[ln[8:14]] = ln[14:64].strip()
    out: dict = {}
    for ln in z.read(f"08{sufijo}.DAT").decode("latin-1").splitlines():
        if len(ln) < 28 or ln[13] != "9" and False:
            continue
        p = ln[11:13]
        r = out.setdefault(p, {"total_cand": 0, "cera": 0, "mesas_sin_cera": 0, "partidos": Counter()})
        v = int(ln[20:28])
        r["total_cand"] += v
        r["partidos"][sig.get(ln[14:20], ln[14:20])] += v
    for ln in z.read(f"10{sufijo}.DAT").decode("latin-1").splitlines():
        if len(ln) < 36:
            continue
        r = out.setdefault(ln[11:13], {"total_cand": 0, "cera": 0, "mesas_sin_cera": 0, "partidos": Counter()})
        v = int(ln[29:36])
        if ln[13:16] == "999":
            r["cera"] += v
        else:
            r["mesas_sin_cera"] += v
    return out


def leer_oficial_csv(ruta: Path) -> dict:
    out: dict = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["codigo"], {})[r["partido"]] = int(r["votos"])
    return out


def ganadores_m08(t: str) -> dict:
    p = ROOT / f"datos/resultados/{t}.csv"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8", newline="") as f:
        return {r["distrito"]: r["ganador"] for r in csv.DictReader(f)}


def ganadores_b(t: str, clave: str) -> dict:
    p = ROOT / f"datos/resultados/historico/{clave}/{t}.csv"
    with open(p, encoding="utf-8", newline="") as f:
        return {r["distrito"]: r["ganador"] for r in csv.DictReader(f)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--espejo", type=Path, required=True)
    ap.add_argument("--mesas", type=Path, required=True, help="02202307_MESA.zip (release fuente-infoelectoral-02202307)")
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--tolerancia", type=float, default=TOLERANCIA)
    a = ap.parse_args(argv)
    esp = json.loads((ROOT / eqs.MANIFIESTO_ESPEJO).read_text(encoding="utf-8"))
    man = json.loads((ROOT / "datos/resultados/historico/MANIFEST.json").read_text(encoding="utf-8"))["territorios"]
    por_prov = {v["provincia"]: t for t, v in man.items()}
    interior = leer_infoelectoral(a.mesas)
    oficial = {"202307": leer_oficial_csv(ROOT / fnb.OFICIALES["202307"]),
               "201911": leer_oficial_csv(ROOT / fnb.OFICIALES["201911"])}
    provs = sorted({r.split("/")[-1][:-5] for r in esp["ficheros"] if "/sekzioa/" in r})
    filas, nocuadra = [], []
    for c in provs:
        t = por_prov.get(c)
        for e in esp["elecciones"]:
            k = e["clave"]
            ruta = f"data/{k}/sekzioa/{c}.json"
            if eqs.sha256(a.espejo / ruta) != esp["ficheros"][ruta]["sha256"]:
                raise SystemExit(f"HUELLA_ESPEJO_DISTINTA {ruta}")
            doc = json.loads((a.espejo / ruta).read_text(encoding="utf-8"))
            tot = fnb.totales_provincia(doc)
            f = {"provincia": c, "territorio": t, "eleccion": k, "votos_espejo": sum(tot.values())}
            if k == "202307" and c in interior:
                i = interior[c]
                f["infoelectoral"] = {"candidaturas_provincia": i["total_cand"], "mesas_sin_cera": i["mesas_sin_cera"],
                                      "cera": i["cera"], "mesas_total": i["mesas_sin_cera"] + i["cera"]}
                f["defecto_vs_provincia"] = round(1 - f["votos_espejo"] / i["total_cand"], 5)
                f["defecto_vs_mesas_sin_cera"] = round(1 - f["votos_espejo"] / i["mesas_sin_cera"], 5) \
                    if i["mesas_sin_cera"] else None
                if f["votos_espejo"] > i["total_cand"]:
                    nocuadra.append({**{x: f[x] for x in ("provincia", "territorio", "eleccion")},
                                     "motivo": "ESPEJO_SUPERA_INFOELECTORAL",
                                     "detalle": f"{f['votos_espejo']} > {i['total_cand']}"})
                elif f["defecto_vs_provincia"] > a.tolerancia:
                    nocuadra.append({**{x: f[x] for x in ("provincia", "territorio", "eleccion")},
                                     "motivo": "DEFECTO_SOBRE_TOLERANCIA", "detalle": f"{f['defecto_vs_provincia']:.2%}"})
                elif f["defecto_vs_mesas_sin_cera"] is not None and abs(f["defecto_vs_mesas_sin_cera"]) > 0.005:
                    nocuadra.append({**{x: f[x] for x in ("provincia", "territorio", "eleccion")},
                                     "motivo": "ESPEJO_DISTINTO_DE_MESAS_SIN_CERA",
                                     "detalle": f"{f['defecto_vs_mesas_sin_cera']:.2%} (Infoelectoral mesas sin CERA "
                                                f"{i['mesas_sin_cera']})"})
            if k in oficial and c in oficial[k]:
                cmp_ = fnb.contrastar_provincia(tot, oficial[k][c], a.tolerancia)
                f["boe"] = {"comparados": len(cmp_["comparaciones"]), "errores": cmp_["errores"],
                            "sin_homologar": cmp_["sin_homologar"], "avisos": cmp_["avisos"]}
                for x in cmp_["errores"]:
                    nocuadra.append({"provincia": c, "territorio": t, "eleccion": k, "motivo": "ESPEJO_SUPERA_BOE",
                                     "detalle": x})
                for x in cmp_["avisos"]:
                    nocuadra.append({"provincia": c, "territorio": t, "eleccion": k, "motivo": "DEFECTO_BOE_SOBRE_TOLERANCIA",
                                     "detalle": x})
            if t is None:
                f["reagregado"] = "SIN_M06"
            else:
                cu = man[t]["cuadre"][k]
                f["reagregado"] = {"votos_distritos": cu["votos_distritos"], "votos_perdidos": cu["votos_perdidos"],
                                   "dif_max_partido": cu["dif_max_partido"], "ok": cu["ok"]}
                if not cu["ok"] or cu["votos_perdidos"] or cu["dif_max_partido"]:
                    nocuadra.append({"provincia": c, "territorio": t, "eleccion": k, "motivo": "REAGREGADO_NO_CUADRA",
                                     "detalle": f"perdidos {cu['votos_perdidos']}, dif {cu['dif_max_partido']}"})
            filas.append(f)
    # ganador 2023: B frente al M08 versionado
    dist23 = {}
    for t in sorted(man):
        m08 = ganadores_m08(t)
        if not m08:
            continue
        b = ganadores_b(t, "202307")
        dif = sorted(d for d in b if d in m08 and b[d] != m08[d])
        dist23[t] = {"distritos": len(b), "ganador_distinto": dif}
        for d in dif:
            nocuadra.append({"provincia": man[t]["provincia"], "territorio": t, "eleccion": "202307",
                             "motivo": "GANADOR_2023_DISTINTO_DE_M08",
                             "detalle": f"distrito {d}: B {b[d]} / M08 {m08[d]} (siglas tal cual; puede ser solo "
                                        f"nombre distinto de la misma lista)"})
    for c in provs:
        if c not in por_prov:
            nocuadra.append({"provincia": c, "territorio": None, "eleccion": "todas", "motivo": "SIN_M06_VIGENTE",
                             "detalle": "no hay producto territorial M06 publicado: sin distritos que reagregar "
                                        "(el espejo sí se contrastó)"})
    out = {"schema": "ddd.cuadre-historico-espana/1.0", "tolerancia": a.tolerancia,
           "fuentes": {"mesas_infoelectoral": eqs.sha256(a.mesas), "espejo": esp["ficheros"]["index.json"]["sha256"]
                       if "index.json" in esp["ficheros"] else eqs.MANIFIESTO_ESPEJO,
                       "boe": {k: fnb.OFICIALES[k] for k in oficial}},
           "provincias": filas, "ganador_2023_vs_m08": dist23,
           "no_cuadra": sorted(nocuadra, key=lambda x: (x["motivo"], x["provincia"], x["eleccion"]))}
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(len(filas), "provincia×elección;", len(nocuadra), "incidencias",
          dict(Counter(x["motivo"] for x in nocuadra)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
