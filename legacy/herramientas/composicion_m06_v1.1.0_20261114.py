#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Composición sección→distrito del M06 publicado, ligera y versionada en git (T-67).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-10 · ESTADO: candidato
CAMBIOS 1.1.0 (T-201): `m06_vigentes(registro, eleccion)` elige por (territorio, elección), por defecto 2023-07-23, nunca solo por run_id mayor.
ANTERIOR: legacy/herramientas/composicion_m06_v1.0.0_20261110.py
QUÉ HACE: el M06 publicado (blob de git) solo trae polígonos por distrito; la asignación sección→distrito vive en el CSV
  ``*_m06_composicion_distritos.csv`` del estado M06 del run (artefactos de 14 días). Esta herramienta toma ese CSV
  (de un directorio, ZIP o TAR ya descargado, con ZIP/TAR anidados), lo valida contra el M06 publicado (mismos distritos,
  nº de secciones = section_count y población = district_pop por distrito) y escribe datos/composicion/<territorio>.csv
  (seccion, distrito, poblacion) más datos/composicion/MANIFEST.json con el sha256 de cada CSV y del M06 de origen.
  Si el CSV no valida contra el M06 del territorio, no escribe nada y lo cuenta como no recuperado.
Uso (en Actions, tras descargar el estado M06 a un directorio por run): python herramientas/composicion_m06.py
  --origen DIR [--territorios t1,t2|todos] [--m06-dir DIR] [--salida DIR] [--registro JSON]
  Con --origen DIR, cada subdirectorio es un run descargado; se prueba contra los territorios pendientes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resultados_ligeros as rl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REGISTRO_VISOR = ROOT / "orchestracion/publicaciones_visor.json"
SALIDA = ROOT / "datos/composicion"
REPO = "jfmurciego/DiputadodeDistrito"
CABECERA = ["seccion", "distrito", "poblacion"]
PATRON = re.compile(r"composicion_distritos\.csv$")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def clave_seccion(valor) -> str:
    """CUSEC_KEY normalizado a 10 dígitos (provincia 2, municipio 3, distrito 2, sección 3)."""
    d = re.sub(r"\D", "", str(valor))
    if not d or len(d) > 10:
        raise ValueError(f"clave de sección no válida: {valor!r}")
    return d.zfill(10)


def _buscar(nombre: str, datos: bytes, prof: int = 0):
    """Genera los bytes de cada composicion_distritos.csv dentro de un ZIP/TAR (anidados) o del propio fichero."""
    if PATRON.search(nombre):
        yield datos
        return
    if prof > 3:
        return
    bio = io.BytesIO(datos)
    if zipfile.is_zipfile(bio):
        z = zipfile.ZipFile(bio)
        for i in z.infolist():
            if not i.is_dir():
                yield from _buscar(i.filename, z.read(i), prof + 1)
    else:
        bio.seek(0)
        try:
            with tarfile.open(fileobj=bio) as t:
                for m in t.getmembers():
                    if m.isfile():
                        yield from _buscar(m.name, t.extractfile(m).read(), prof + 1)
        except tarfile.TarError:
            return


def composiciones(origen: Path):
    """Cada composición hallada bajo ``origen`` (fichero o directorio)."""
    ficheros = [origen] if origen.is_file() else sorted(p for p in origen.rglob("*") if p.is_file())
    for f in ficheros:
        yield from _buscar(f.name, f.read_bytes())


def distritos_m06(m06: bytes) -> dict[int, tuple[int, int]]:
    """district_id → (section_count, district_pop) del M06 publicado (ZIP con un geojson)."""
    z = zipfile.ZipFile(io.BytesIO(m06))
    gj = json.loads(z.read(next(n for n in sorted(z.namelist()) if n.endswith(".geojson"))))
    return {int(f["properties"]["district_id"]): (int(f["properties"]["section_count"]), int(f["properties"]["district_pop"]))
            for f in gj["features"]}


def validar(comp: bytes, m06: bytes) -> list[list]:
    """Filas (seccion, distrito, poblacion) ordenadas; ValueError si no cuadra con el M06 publicado."""
    filas, vistas = [], set()
    for r in csv.DictReader(io.StringIO(comp.decode("utf-8-sig"))):
        idc = next((c for c in ("CUSEC_KEY", "CUSEC", "section_id") if c in r), None)
        if idc is None or "district_id" not in r or "section_pop" not in r:
            raise ValueError("composición sin CUSEC_KEY/district_id/section_pop")
        s = clave_seccion(r[idc])
        if s in vistas:
            raise ValueError(f"sección repetida: {s}")
        vistas.add(s)
        filas.append([s, int(r["district_id"]), int(round(float(r["section_pop"])))])
    esperado = distritos_m06(m06)
    real: dict[int, list[int]] = {}
    for _, d, p in filas:
        c = real.setdefault(d, [0, 0])
        c[0] += 1
        c[1] += p
    if set(real) != set(esperado):
        raise ValueError(f"distritos {sorted(real)} != M06 {sorted(esperado)}")
    for d, (n, pop) in esperado.items():
        if real[d] != [n, pop]:
            raise ValueError(f"distrito {d}: {real[d]} (secciones, población) != M06 {[n, pop]}")
    return sorted(filas)


def csv_bytes(filas) -> bytes:
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


def m06_vigentes(registro: Path = REGISTRO_VISOR, eleccion: str = rl.ELECCION_POR_DEFECTO) -> dict[str, dict]:
    prods = rl.vigente_por_eleccion(json.loads(registro.read_text(encoding="utf-8"))["products"], "canonical_m06", eleccion)
    return dict(sorted(prods.items()))


def extraer(origen: Path, territorios: list[str] | None = None, salida: Path = SALIDA,
            registro: Path = REGISTRO_VISOR, m06_dir: Path | None = None) -> dict:
    """Prueba cada composición de ``origen`` contra los territorios pendientes; escribe las que validan."""
    salida.mkdir(parents=True, exist_ok=True)
    ruta_man = salida / "MANIFEST.json"
    man = json.loads(ruta_man.read_text(encoding="utf-8")) if ruta_man.exists() else {"schema": "ddd.composicion-m06/1.0", "territorios": {}}
    vig = m06_vigentes(registro)
    objetivo = [t for t in vig if territorios is None or t in territorios]
    blobs: dict[str, bytes] = {}

    def m06_de(t: str) -> bytes:
        if t not in blobs:
            p = vig[t]
            f = (m06_dir / f"{t}_{p['run_id']}.zip") if m06_dir else None
            blobs[t] = f.read_bytes() if f and f.exists() else bajar_blob(p)
            if sha256(blobs[t]) != p["sha256"]:
                raise ValueError(f"SHA-256 del M06 de {t} no coincide con el registro")
        return blobs[t]

    hechos = {t for t, m in man["territorios"].items() if m.get("blob_sha") == vig.get(t, {}).get("blob_sha")
              and (salida / f"{t}.csv").exists()}
    pendientes = [t for t in objetivo if t not in hechos]
    for comp in composiciones(origen):
        for t in list(pendientes):
            m06 = m06_de(t)  # un sha256 que no cuadra es un error, no «no recuperado»
            try:
                filas = validar(comp, m06)
            except (ValueError, KeyError):
                continue
            cuerpo = csv_bytes(filas)
            ruta = salida / f"{t}.csv"
            if not ruta.exists() or ruta.read_bytes() != cuerpo:
                ruta.write_bytes(cuerpo)
            p = vig[t]
            man["territorios"][t] = {"run_id": p["run_id"], "blob_sha": p["blob_sha"], "sha256_m06": p["sha256"],
                                     "secciones": len(filas), "sha256_csv": sha256(cuerpo)}
            pendientes.remove(t)
            break
    man["territorios"] = dict(sorted(man["territorios"].items()))
    texto = json.dumps(man, ensure_ascii=False, indent=1) + "\n"
    if not ruta_man.exists() or ruta_man.read_text(encoding="utf-8") != texto:
        ruta_man.write_text(texto, encoding="utf-8")
    return {"hechos": sorted(set(objetivo) - set(pendientes)), "no_recuperados": sorted(pendientes)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--origen", type=Path, required=True)
    ap.add_argument("--territorios", default="todos")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--registro", type=Path, default=REGISTRO_VISOR)
    ap.add_argument("--m06-dir", type=Path, help="ZIP <territorio>_<run>.zip del M06 ya descargados (sin red)")
    a = ap.parse_args(argv)
    ts = None if a.territorios.strip() in ("", "todos") else [t.strip() for t in a.territorios.split(",")]
    r = extraer(a.origen, ts, a.salida, a.registro, a.m06_dir)
    print(f"composición: {len(r['hechos'])} territorios; no recuperados: {', '.join(r['no_recuperados']) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
