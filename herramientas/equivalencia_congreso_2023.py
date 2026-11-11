#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Equivalencia de las secciones del ZIP por mesa del Congreso 2023 ausentes del seccionado del M06 (T-101, D-17).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-10 · ESTADO: candidato
CAMBIOS: 1.1.0 (T-225, D-65): --salida (otra pareja CSV/JSON, p. ej. el M06 sobre el seccionado INE 2025),
  --prefijo (solo los contratos cuyo territorio empieza así; congreso_ deja fuera los gemelos congreso350_) y, por
  provincia, sha256_secciones_m06 (sha256 de los CUSEC del seccionado M06, ordenados y unidos por «\n») para que el
  archivista elija la tabla cuyo seccionado coincide con la composición. Sin argumentos nuevos, igual que 1.0.0.
  1.0.0: fichero nuevo.
MOTIVO: D-17 del propietario: el archivista (herramientas/archivo_origen.py partidos) tolera desajustes pequeños de
  código de sección entre el ZIP de Interior (secciones del censo electoral de julio de 2023) y el M06 de Congreso
  (seccionado INE 2023, Secciones_2023), repartiendo sus votos con la intersección de T-85 (peso = población de la
  sección del M06, D-13). El runner no tiene las geometrías, así que la tabla
  de las secciones desajustadas se versiona aquí con sus fuentes y sha256.
ANTERIOR: legacy/herramientas/equivalencia_congreso_2023_v1.0.0_20261110.py
QUÉ HACE: para cada contrato Infoelectoral 2023 (configuracion/contratos_infoelectoral.yaml) toma las secciones del ZIP
  nacional por mesa (release fuente-infoelectoral-02202307, sha256 del contrato) que no existen en el seccionado INE
  2023 del M06 y las cruza con herramientas/equivalencia_seccionados.equivalencia, con su geometría tomada del
  seccionado INE posterior más cercano que la tenga (2024; 2025 de reserva). Escribe:
    configuracion/equivalencia_secciones_congreso_2023.csv  seccion_zip, seccion_m06, tipo, peso_area, frac_m06
                                                            (frac_m06 = a(zip∩m06)/a(m06); el archivista calcula el
                                                            peso de población con la población de la composición)
    configuracion/equivalencia_secciones_congreso_2023.json fuentes con sha256, sha256 del CSV y, por provincia, las
                                                            secciones desajustadas y su % de votos a candidaturas.
Uso: python herramientas/equivalencia_congreso_2023.py --zip MESA.zip --seccionado-m06 SECC2023.zip
       --geometria SECC2024.zip [SECC2025.zip ...]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import equivalencia_seccionados as es  # noqa: E402
import resultados_partidos as rp  # noqa: E402

CSV_SALIDA = ROOT / "configuracion/equivalencia_secciones_congreso_2023.csv"
JSON_SALIDA = ROOT / "configuracion/equivalencia_secciones_congreso_2023.json"
SCHEMA = "ddd.equivalencia-congreso-2023/1.0"


def votos_por_seccion(zip_path: Path, contrato: dict) -> dict[str, int]:
    with tempfile.TemporaryDirectory() as tmp:
        rp.fim.convert(zip_path, contrato, Path(tmp) / "m.csv")
        out: dict[str, int] = defaultdict(int)
        for r in csv.DictReader(open(Path(tmp) / "m.csv", encoding="utf-8")):
            out[r["codigo_provincia"] + r["codigo_municipio"] + r["codigo_distrito"] + r["codigo_seccion"]] += int(r["votos"])
    return dict(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--seccionado-m06", type=Path, required=True, help="seccionado INE 2023 (el de la composición M06)")
    ap.add_argument("--geometria", type=Path, nargs="+", required=True, help="seccionados INE posteriores, por orden")
    ap.add_argument("--salida", type=Path, default=CSV_SALIDA, help="CSV de salida (el JSON va al lado, .json)")
    ap.add_argument("--prefijo", default="", help="solo territorios con este prefijo (p. ej. congreso_)")
    a = ap.parse_args(argv)
    csv_salida, json_salida = a.salida.resolve(), a.salida.resolve().with_suffix(".json")
    ctrs = {t: c for t, c in rp.contratos().items() if str(t).startswith(a.prefijo)}
    sha_zip = es.sha256(a.zip)
    if any(c["source_sha256"] != sha_zip for c in ctrs.values()):
        raise SystemExit("HUELLA_ZIP_DISTINTA")
    m06 = es.leer_seccionado(a.seccionado_m06)
    geos = [es.leer_seccionado(g) for g in a.geometria]
    filas, provincias = [], {}
    for terr, ctr in sorted(ctrs.items()):
        cpro = str(ctr["province"]).zfill(2)
        votos = votos_por_seccion(a.zip, ctr)
        zsec = set(rp.mesas_09(a.zip, ctr))
        sobran = sorted(zsec - set(m06.get(cpro, {})))
        faltan = sorted(set(m06.get(cpro, {})) - zsec)
        total = sum(votos.values())
        hist = {}
        for s in sobran:
            g = next((t[cpro][s] for t in geos if s in t.get(cpro, {})), None)
            if g is not None:
                hist[s] = g
        eq = es.equivalencia(hist, m06[cpro], {}) if hist else {}
        detalle = []
        for s in sobran:
            e = eq.get(s, {"tipo": "sin_geometria", "area": {}})
            for v in sorted(e["area"]):
                frac = hist[s].intersection(m06[cpro][v]).area / m06[cpro][v].area if e["tipo"] != "1:1" else 1.0
                filas.append([s, v, e["tipo"], f"{e['area'][v]:.6f}", f"{frac:.6f}"])
            detalle.append({"seccion": s, "votos": votos.get(s, 0), "tipo": e["tipo"], "secciones_m06": sorted(e["area"])})
        v_des = sum(votos.get(s, 0) for s in sobran)
        provincias[terr] = {"provincia": cpro, "votos_candidaturas": total, "votos_desajustados": v_des,
                            "pct_desajuste": round(100 * v_des / total, 4) if total else 0.0,
                            "secciones_zip_sin_m06": detalle, "secciones_m06_sin_zip": faltan,
                            "sha256_secciones_m06": hashlib.sha256("\n".join(sorted(m06.get(cpro, {}))).encode()).hexdigest()}
        print(terr, len(sobran), len(faltan), provincias[terr]["pct_desajuste"], flush=True)
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["seccion_zip", "seccion_m06", "tipo", "peso_area", "frac_m06"])
    w.writerows(sorted(filas))
    cuerpo = s.getvalue().encode("utf-8")
    csv_salida.write_bytes(cuerpo)
    meta = {"schema": SCHEMA, "decision": "D-17 (tope 0,5 % de los votos de la provincia); peso D-13",
            "csv": {"ruta": csv_salida.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(cuerpo).hexdigest()},
            "fuentes": {"zip_mesa_2023": {"release": "fuente-infoelectoral-02202307", "sha256": sha_zip},
                        "seccionado_m06": {"url": f"{es.URL_INE}{a.seccionado_m06.name}", "sha256": es.sha256(a.seccionado_m06)},
                        "geometria": [{"url": f"{es.URL_INE}{g.name}", "sha256": es.sha256(g)} for g in a.geometria]},
            "umbral_1a1": es.UMBRAL, "astilla": es.ASTILLA, "provincias": provincias}
    json_salida.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
