#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Votos por partido y distrito en git (T-67).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: por cada territorio con composición sección→distrito acreditada (datos/composicion, T-67) y M08 vigente
  (datos/resultados), agrega los votos por partido del ZIP nacional por mesa de Infoelectoral (release
  fuente-infoelectoral-02202307; huella y totales comprobados con herramientas/fuente_infoelectoral_mesas.convert)
  sobre los distritos y escribe datos/resultados/<territorio>_partidos.csv:
  distrito, partido, votos, porcentaje (sobre votos a candidaturas del distrito), blancos, nulos, censo.
  Falla (sin escribir el territorio) si: hay secciones del ZIP sin distrito o distritos con secciones ausentes del ZIP;
  la suma por partido de los distritos no es el total provincial del ZIP; o el ganador de algún distrito no es el del M08
  publicado. Añade la clave ``partidos`` a datos/resultados/MANIFEST.json (sha256 del CSV, de la composición y del ZIP).
  Salida determinista; un CSV que no cambia no se reescribe.
Uso: python herramientas/resultados_partidos.py [--zip ZIP] [--salida DIR] [--composicion DIR] [--registro JSON]
  [--territorios t1,t2|todos]   (sin --zip lo baja del release con gh y comprueba su sha256)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import fuente_infoelectoral_mesas as fim  # noqa: E402
import resultados_ligeros as rl  # noqa: E402

SALIDA = ROOT / "datos/resultados"
COMPOSICION = ROOT / "datos/composicion"
CONTRATOS = ROOT / "configuracion/contratos_infoelectoral.yaml"
FECHA = "2023-07-23"
CABECERA = ["distrito", "partido", "votos", "porcentaje", "blancos", "nulos", "censo"]


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def contratos(ruta: Path = CONTRATOS) -> dict[str, dict]:
    """territorio → contrato Infoelectoral de la elección FECHA."""
    raw = yaml.safe_load(ruta.read_text(encoding="utf-8"))["contracts"]
    return {r["territory_id"]: {"election_id": k, **r} for k, r in raw.items() if str(r.get("election_date")) == FECHA}


def bajar_zip(contrato: dict, destino: Path) -> Path:
    m = contrato["mirror"]
    asset = subprocess.run(["gh", "api", f"repos/{rl.REPO}/releases/tags/{m['release_tag']}", "--jq",
                            f".assets[]|select(.name==\"{m['asset']}\")|.id"], capture_output=True, text=True, check=True).stdout.strip()
    r = subprocess.run(["gh", "api", f"repos/{rl.REPO}/releases/assets/{asset}", "-H", "Accept: application/octet-stream"],
                       capture_output=True, check=True)
    destino.write_bytes(r.stdout)
    return destino


def leer_composicion(ruta: Path) -> dict[str, int]:
    return {r["seccion"]: int(r["distrito"]) for r in csv.DictReader(io.StringIO(ruta.read_text(encoding="utf-8")))}


def mesas_09(zip_path: Path, contrato: dict) -> dict[str, dict[str, int]]:
    """sección (10 dígitos) → censo, blancos y nulos de las mesas de la provincia (sin CERA)."""
    import zipfile
    prefijo, prov = str(contrato["election_prefix"]), str(contrato["province"]).zfill(2)
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"censo": 0, "blancos": 0, "nulos": 0})
    with zipfile.ZipFile(zip_path) as z:
        for line in fim._records(z, contrato["files"]["mesas"]):
            if not line.startswith(prefijo) or line[11:13] != prov or line[13:16] == fim.CERA_MUNICIPALITY:
                continue
            s = out[line[11:13] + line[13:16] + line[16:18] + f"{int(line[18:22].strip()):03d}"]
            s["censo"] += fim._int(line, 24, 30)
            s["blancos"] += fim._int(line, 66, 72)
            s["nulos"] += fim._int(line, 73, 79)
    return dict(out)


def agregar(zip_path: Path, contrato: dict, comp: dict[str, int], m08_ganadores: list[str]) -> bytes:
    """CSV de votos por partido y distrito; ValueError si algo no cuadra (ver módulo)."""
    with tempfile.TemporaryDirectory() as tmp:
        resumen = fim.convert(zip_path, contrato, Path(tmp) / "mesas.csv")  # huella y totales del contrato
        filas = list(csv.DictReader(open(Path(tmp) / "mesas.csv", encoding="utf-8")))
    por_seccion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in filas:
        sec = r["codigo_provincia"] + r["codigo_municipio"] + r["codigo_distrito"] + r["codigo_seccion"]
        por_seccion[sec][r["partido"]] += int(r["votos"])
    extra09 = mesas_09(zip_path, contrato)
    zsec = set(extra09)
    if zsec != set(comp):
        falta, sobra = sorted(zsec - set(comp)), sorted(set(comp) - zsec)
        raise ValueError(f"secciones del ZIP sin distrito {len(falta)} (p. ej. {falta[:3]}); "
                         f"secciones de la composición ausentes del ZIP {len(sobra)} (p. ej. {sobra[:3]})")
    votos: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    meta: dict[int, dict[str, int]] = defaultdict(lambda: {"censo": 0, "blancos": 0, "nulos": 0})
    for sec, d in comp.items():
        for p, v in por_seccion.get(sec, {}).items():
            votos[d][p] += v
        for k, v in extra09[sec].items():
            meta[d][k] += v
    total_zip: dict[str, int] = defaultdict(int)
    for s in por_seccion.values():
        for p, v in s.items():
            total_zip[p] += v
    total_dist: dict[str, int] = defaultdict(int)
    for d in votos.values():
        for p, v in d.items():
            total_dist[p] += v
    if dict(total_dist) != dict(total_zip) or sum(total_dist.values()) != resumen["candidate_votes"]:
        raise ValueError("la suma por partido de los distritos no coincide con el total provincial del ZIP")
    distritos = sorted(set(comp.values()))
    if len(distritos) != len(m08_ganadores):
        raise ValueError(f"distritos {len(distritos)} != distritos del M08 {len(m08_ganadores)}")
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(CABECERA)
    for d, g_m08 in zip(distritos, m08_ganadores):
        orden = sorted(votos[d].items(), key=lambda kv: (-kv[1], kv[0]))
        if not orden or orden[0][0] != g_m08:
            raise ValueError(f"distrito {d}: ganador {orden[0][0] if orden else None} != M08 {g_m08}")
        tot = sum(v for _, v in orden)
        for p, v in orden:
            w.writerow([d, p, v, f"{v * 100 / tot:.4f}" if tot else "", meta[d]["blancos"], meta[d]["nulos"], meta[d]["censo"]])
    return s.getvalue().encode("utf-8")


def generar(salida: Path = SALIDA, registro: Path = rl.REGISTRO_VISOR, composicion: Path = COMPOSICION,
            zip_path: Path | None = None, territorios: list[str] | None = None, contratos_yaml: Path = CONTRATOS) -> dict:
    ctr = contratos(contratos_yaml)
    m08 = rl.vigentes(registro)
    ruta_man = composicion / "MANIFEST.json"
    comps = json.loads(ruta_man.read_text(encoding="utf-8"))["territorios"] if ruta_man.exists() else {}
    ruta_sal = salida / "MANIFEST.json"
    man = json.loads(ruta_sal.read_text(encoding="utf-8")) if ruta_sal.exists() else {"schema": "ddd.resultados-ligeros/1.0", "territorios": {}}
    previo = man.get("partidos", {})
    nuevo: dict[str, dict] = {}
    omitidos: list[str] = []
    tmp = tempfile.TemporaryDirectory()
    try:
        for t in sorted(m08):
            if territorios is not None and t not in territorios:
                if t in previo:
                    nuevo[t] = previo[t]
                continue
            cm, rutac = comps.get(t), composicion / f"{t}.csv"
            if t not in ctr or not cm or not rutac.exists() or sha256(rutac.read_bytes()) != cm["sha256_csv"]:
                omitidos.append(t)
                continue
            gan = rl.ganadores(salida, t, m08[t])
            if gan is None:
                omitidos.append(t)
                continue
            ant, rutap = previo.get(t), salida / f"{t}_partidos.csv"
            if (ant and ant["blob_sha_m08"] == m08[t]["blob_sha"] and ant["sha256_composicion"] == cm["sha256_csv"]
                    and rutap.exists() and sha256(rutap.read_bytes()) == ant["sha256_csv"]):
                nuevo[t] = ant
                continue
            if zip_path is None:
                zip_path = bajar_zip(ctr[t], Path(tmp.name) / "mesa.zip")
            cuerpo = agregar(zip_path, ctr[t], leer_composicion(rutac), gan)
            if not rutap.exists() or rutap.read_bytes() != cuerpo:
                rutap.write_bytes(cuerpo)
            nuevo[t] = {"blob_sha_m08": m08[t]["blob_sha"], "sha256_composicion": cm["sha256_csv"],
                        "sha256_zip": ctr[t]["source_sha256"], "sha256_csv": sha256(cuerpo)}
    finally:
        tmp.cleanup()
    man["partidos"] = dict(sorted(nuevo.items()))
    texto = json.dumps(man, ensure_ascii=False, indent=1) + "\n"
    if not ruta_sal.exists() or ruta_sal.read_text(encoding="utf-8") != texto:
        ruta_sal.write_text(texto, encoding="utf-8")
    for viejo in salida.glob("*_partidos.csv"):
        if viejo.name[:-len("_partidos.csv")] not in nuevo:
            viejo.unlink()
    return {"hechos": sorted(nuevo), "omitidos": omitidos}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--composicion", type=Path, default=COMPOSICION)
    ap.add_argument("--registro", type=Path, default=rl.REGISTRO_VISOR)
    ap.add_argument("--territorios", default="todos")
    a = ap.parse_args(argv)
    ts = None if a.territorios.strip() in ("", "todos") else [t.strip() for t in a.territorios.split(",")]
    r = generar(a.salida, a.registro, a.composicion, a.zip, ts)
    print(f"partidos: {len(r['hechos'])} territorios; sin composición/M08: {len(r['omitidos'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
