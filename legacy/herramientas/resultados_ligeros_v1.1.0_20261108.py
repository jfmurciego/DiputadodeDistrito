#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resultados electorales ligeros por territorio, versionados en git (T-53).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-07 · ESTADO: candidato
CAMBIOS: 1.1.0: conserva la clave «partidos» del MANIFEST y no borra <territorio>_partidos.csv (T-67).
MOTIVO: los votos por partido los escribe herramientas/resultados_partidos.py en el mismo directorio.
ANTERIOR: legacy/herramientas/resultados_ligeros_v1.0.0_20261107.py
QUÉ HACE: por cada territorio con canonical_m08 vigente (el run más reciente) en orchestracion/publicaciones_visor.json,
  lee el M08 (blob inmutable de git, verificado con su sha256) y escribe datos/resultados/<territorio>.csv con una fila por
  distrito: distrito, poblacion, votos_totales, ganador, votos_ganador, porcentaje_ganador (el M08 solo trae el ganador, no
  los votos de cada partido). Escribe también datos/resultados/MANIFEST.json (run, blob_sha y sha256 de origen, sha256 de
  cada CSV). Salida determinista: dos ejecuciones dan los mismos bytes; un CSV que no cambia no se reescribe.
Uso: python herramientas/resultados_ligeros.py [--salida DIR] [--cache DIR] [--m08-dir DIR] [--registro JSON]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRO_VISOR = ROOT / "orchestracion/publicaciones_visor.json"
SALIDA = ROOT / "datos/resultados"
REPO = "jfmurciego/DiputadodeDistrito"
CABECERA = ["distrito", "poblacion", "votos_totales", "ganador", "votos_ganador", "porcentaje_ganador"]


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def vigentes(registro: Path = REGISTRO_VISOR) -> dict[str, dict]:
    """territorio → producto canonical_m08 del run más reciente."""
    prods: dict[str, dict] = {}
    for p in json.loads(registro.read_text(encoding="utf-8"))["products"]:
        if p.get("kind") == "canonical_m08":
            t = p["territory_id"]
            if t not in prods or int(p["run_id"]) > int(prods[t]["run_id"]):
                prods[t] = p
    return dict(sorted(prods.items()))


def filas_m08(datos: bytes) -> list[list]:
    z = zipfile.ZipFile(io.BytesIO(datos))
    gj = json.loads(z.read(next(n for n in sorted(z.namelist()) if n.endswith(".geojson"))))
    filas = []
    for f in sorted(gj["features"], key=lambda f: int(f["properties"]["district_id"])):
        p = f["properties"]
        pct = p.get("winner_share")
        filas.append([int(p["district_id"]), p.get("district_pop", ""), p.get("total_votes", ""),
                      p.get("winner_party") or "", p.get("winner_votes", ""),
                      "" if pct is None else f"{pct * 100:.4f}"])
    return filas


def csv_bytes(filas: list[list]) -> bytes:
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(CABECERA)
    w.writerows(filas)
    return s.getvalue().encode("utf-8")


def bajar_blob(p: dict) -> bytes:
    r = subprocess.run(["gh", "api", f"repos/{REPO}/git/blobs/{p['blob_sha']}", "-H", "Accept: application/vnd.github.raw"],
                       capture_output=True)
    if r.returncode:
        raise RuntimeError(f"blob {p['blob_sha']}: {r.stderr.decode(errors='replace')[:200]}")
    return r.stdout


def generar(salida: Path = SALIDA, registro: Path = REGISTRO_VISOR, cache: Path | None = None,
            m08_dir: Path | None = None) -> dict:
    salida.mkdir(parents=True, exist_ok=True)
    previo = {}
    if (salida / "MANIFEST.json").exists():
        previo = json.loads((salida / "MANIFEST.json").read_text(encoding="utf-8")).get("territorios", {})
    partidos = {}
    if (salida / "MANIFEST.json").exists():
        partidos = json.loads((salida / "MANIFEST.json").read_text(encoding="utf-8")).get("partidos", {})
    terr = {}
    for t, p in vigentes(registro).items():
        ant = previo.get(t)
        csv_ruta = salida / f"{t}.csv"
        if ant and ant["blob_sha"] == p["blob_sha"] and csv_ruta.exists() and sha256(csv_ruta.read_bytes()) == ant["sha256_csv"]:
            terr[t] = ant  # sin cambio: no se baja el blob
            continue
        f = (m08_dir or cache or Path("/nonexistent")) / f"{t}_{p['run_id']}.zip"
        datos = f.read_bytes() if f.exists() else (None if m08_dir else bajar_blob(p))
        if datos is None:
            continue
        if sha256(datos) != p["sha256"]:
            raise ValueError(f"SHA-256 del M08 de {t} no coincide con el registro")
        cuerpo = csv_bytes(filas_m08(datos))
        if not csv_ruta.exists() or csv_ruta.read_bytes() != cuerpo:
            csv_ruta.write_bytes(cuerpo)
        terr[t] = {"run_id": p["run_id"], "blob_sha": p["blob_sha"], "sha256_origen": p["sha256"],
                   "distritos": cuerpo.count(b"\n") - 1, "sha256_csv": sha256(cuerpo)}
    man = {"schema": "ddd.resultados-ligeros/1.0", "origen": "orchestracion/publicaciones_visor.json (canonical_m08)",
           "territorios": dict(sorted(terr.items()))}
    if partidos:
        man["partidos"] = partidos
    texto = json.dumps(man, ensure_ascii=False, indent=1) + "\n"
    ruta = salida / "MANIFEST.json"
    if not ruta.exists() or ruta.read_text(encoding="utf-8") != texto:
        ruta.write_text(texto, encoding="utf-8")
    for viejo in salida.glob("*.csv"):  # territorios que ya no están vigentes
        if viejo.stem not in terr and not viejo.stem.endswith("_partidos"):
            viejo.unlink()
    return man


def ganadores(salida: Path, territorio: str, producto: dict) -> list[str] | None:
    """Ganadores por distrito desde el CSV, si el manifiesto acredita el blob vigente y el sha256 del CSV; si no, None."""
    try:
        m = json.loads((salida / "MANIFEST.json").read_text(encoding="utf-8"))["territorios"][territorio]
        datos = (salida / f"{territorio}.csv").read_bytes()
    except (OSError, KeyError, ValueError):
        return None
    if m["blob_sha"] != producto["blob_sha"] or sha256(datos) != m["sha256_csv"]:
        return None
    return [r["ganador"] for r in csv.DictReader(io.StringIO(datos.decode("utf-8")))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--registro", type=Path, default=REGISTRO_VISOR)
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--m08-dir", type=Path, help="ZIP <territorio>_<run>.zip ya descargados (sin red)")
    a = ap.parse_args(argv)
    man = generar(a.salida, a.registro, a.cache, a.m08_dir)
    print(f"{len(man['territorios'])} territorios en {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
