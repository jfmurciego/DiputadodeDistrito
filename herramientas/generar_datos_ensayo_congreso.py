#!/usr/bin/env python3
# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# FECHA: 2026-11-14
# CAMBIOS 1.0.0 (T-333): genera los datos de ENSAYO por mesa de las generales 2026-11-29 (nac22 Huesca, nac42 Soria, nac52 Melilla)
#   a partir del ZIP oficial Infoelectoral 2023 por mesa (sha256 fijado en contratos_infoelectoral.yaml). Son datos de 2023
#   REETIQUETADOS como ENSAYO (columna `ensayo` en cada fila y nombre `ensayo_…`): NO son resultados de 2026 ni datos oficiales.
#   Formato = el del adaptador minsait_csv (+ la columna `ensayo`). Escribe un MANIFEST con sha256. No sube nada: lo hace el Operador.
# Claves de sección (decisión del Planificador, opción A): los CSV llevan CLAVES DE SECCIÓN 2026. Cada fila de 2023 (sección T, mesa,
#   partido) se reparte entre las secciones 2026 S que la tabla configuracion/equivalencia_seccionado_ine_2026_a_2023.csv (sha256 fijado)
#   declara como sus compuestas con T, en proporción a peso_poblacion; reparto SOLO para construir el fixture. Entero y determinista:
#   cociente exacto por sección, resto al mayor peso (empate: clave menor); filas con la misma (S, mesa, partido) se suman; orden fijo.
#   Se conserva el total provincial de votos. Las secciones sin fila en la tabla conservan su clave. El id del ensayo se deriva del de 2023.
# ANTERIOR: ninguna (fichero nuevo)
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import yaml

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herramientas import fuente_infoelectoral_mesas as fim  # noqa: E402

ENSAYO_DATE = "2026-11-29"
MARCA = "ENSAYO_2026-11-29_NO_OFICIAL"
RELEASE_TAG = "fuente-ensayo-congreso-2026-11-29"
MANIFEST = Path("configuracion/ensayo_congreso_2026-11-29_MANIFEST.json")
# territorio de ensayo → id de la elección 2023 del contrato Infoelectoral (el id del ensayo se deriva de él)
TERRITORIOS = {
    "nac22": "congreso_huesca_2023-07-23",
    "nac42": "congreso_soria_2023-07-23",
    "nac52": "congreso_melilla_2023-07-23",
}
FIELDS = fim.OUTPUT_FIELDS + ("ensayo",)
EQUIVALENCIA = Path("configuracion/equivalencia_seccionado_ine_2026_a_2023.csv")
EQUIVALENCIA_SHA256 = "d57d5fcfd80372b4842edc914bd43f89a655c91f996d4bd8bbceb5fd6fbfb35e"


def id_ensayo(election_2023: str) -> str:
    return election_2023.replace("2023-07-23", ENSAYO_DATE)


def nombre_fichero(election_2023: str) -> str:
    return f"ensayo_{id_ensayo(election_2023)}.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def cargar_tabla(path: Path) -> dict[str, list[tuple[str, int, str]]]:
    """{sección 2023: [(sección 2026, peso_poblacion en millonésimas, tipo)]}, ordenado por (-peso, sección 2026)."""
    if sha256(path) != EQUIVALENCIA_SHA256:
        raise ValueError("SHA-256 de la tabla de equivalencia 2026→2023 no coincide con el fijado")
    por_2023: dict[str, list[tuple[str, int, str]]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            peso = int(round(float(row["peso_poblacion"]) * 1_000_000))
            por_2023.setdefault(row["seccion_2023"], []).append((row["seccion_2026"], peso, row["tipo"]))
    for lista in por_2023.values():
        lista.sort(key=lambda t: (-t[1], t[0]))
    return por_2023


def _repartir(votos: int, candidatos: list[tuple[str, int, str]]) -> list[tuple[str, int]]:
    total = sum(p for _s, p, _t in candidatos)
    pesos = [p for _s, p, _t in candidatos] if total > 0 else [1] * len(candidatos)
    total = sum(pesos)
    partes = [votos * p // total for p in pesos]
    partes[0] += votos - sum(partes)  # resto al mayor peso (la lista viene ordenada por -peso, clave)
    return [(c[0], v) for c, v in zip(candidatos, partes)]


def repartir_claves_2026(csv_in: Path, csv_out: Path, tabla: dict[str, list[tuple[str, int, str]]]) -> dict:
    """CSV largo por mesa de 2023 → CSV con claves de sección 2026 y la marca ENSAYO en cada fila (LF, orden fijo)."""
    acumulado: dict[tuple, int] = {}
    with csv_in.open(encoding="utf-8", newline="") as src:
        reader = csv.DictReader(src)
        if tuple(reader.fieldnames or ()) != fim.OUTPUT_FIELDS:
            raise ValueError(f"Cabecera inesperada en el CSV de origen: {reader.fieldnames}")
        for row in reader:
            cusec = row["codigo_provincia"] + row["codigo_municipio"] + row["codigo_distrito"] + row["codigo_seccion"]
            candidatos = tabla.get(cusec) or [(cusec, 1, "identidad")]
            for destino, votos in _repartir(int(row["votos"]), candidatos):
                key = (destino, row["codigo_mesa"], row["partido"], row["codigo_ccaa"])
                acumulado[key] = acumulado.get(key, 0) + votos
    tipos: dict[str, set] = {}
    for lista in tabla.values():
        for s26, _p, tipo in lista:
            tipos.setdefault(s26, set()).add(tipo)
    secciones, mesas, total = set(), set(), 0
    with csv_out.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for (s26, mesa, partido, ccaa), votos in sorted(acumulado.items()):
            writer.writerow({"codigo_ccaa": ccaa, "codigo_provincia": s26[:2], "codigo_municipio": s26[2:5],
                             "codigo_distrito": s26[5:7], "codigo_seccion": s26[7:10], "codigo_mesa": mesa,
                             "partido": partido, "votos": votos, "ensayo": MARCA})
            secciones.add(s26)
            mesas.add((s26, mesa))
            total += votos
    por_tipo = {t: sorted(s for s in secciones if t in tipos.get(s, ())) for t in ("1:1", "contenida", "partida")}
    return {"rows": len(acumulado), "sections": len(secciones), "polling_stations": len(mesas), "candidate_votes": total,
            "sections_by_type": {t: len(v) for t, v in por_tipo.items()}, "partida_sections": por_tipo["partida"]}


def generar(zip_path: Path, out_dir: Path, root_dir: Path = Path(".")) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    infoelectoral = yaml.safe_load((root_dir / fim.DEFAULT_PATH).read_text(encoding="utf-8"))["contracts"]
    tabla = cargar_tabla(root_dir / EQUIVALENCIA)
    files = {}
    zip_sha = None
    for tid, election_2023 in TERRITORIOS.items():
        contract = fim.resolve(election_id=election_2023, territory_id=tid, election_date="2023-07-23", root_dir=root_dir)
        with tempfile.TemporaryDirectory() as tmp:
            conv = fim.convert(zip_path, contract, Path(tmp) / "mesas.csv")  # verifica el sha256 del ZIP y los totales
            target = out_dir / nombre_fichero(election_2023)
            res = repartir_claves_2026(Path(tmp) / "mesas.csv", target, tabla)
        if res["candidate_votes"] != conv["candidate_votes"]:
            raise ValueError(f"El reparto no conserva el total provincial de {tid}")
        zip_sha = conv["source_sha256"]
        exp = infoelectoral[election_2023]["expected"]
        files[tid] = {
            "file": target.name, "sha256": sha256(target), "bytes": target.stat().st_size, "rows": res["rows"],
            "election_id_ensayo": id_ensayo(election_2023), "derived_from_election_id": election_2023,
            "province": str(contract["province"]), "ccaa": str(exp["ccaa"]),
            "sections": res["sections"], "polling_stations": res["polling_stations"], "candidate_votes": res["candidate_votes"],
            "sections_2023": conv["sections"], "polling_stations_2023": conv["polling_stations"],
            "sections_by_type": res["sections_by_type"], "partida_sections": res["partida_sections"],
        }
    return {
        "schema": "ddd-ensayo-datos-manifest/1.1",
        "rehearsal": True,
        "official": False,
        "status": "PROVISIONAL",
        "mark": MARCA,
        "warning": "Datos de ENSAYO derivados del ZIP Infoelectoral 2023 por mesa; no son resultados de 2026 ni datos oficiales.",
        "election_date_label": ENSAYO_DATE,
        "release_tag": RELEASE_TAG,
        "derived_from": {"source": "Ministerio del Interior — Infoelectoral 02202307_MESA.zip", "sha256": zip_sha},
        "section_keys": "claves de sección 2026: cada fila 2023 se reparte entre las secciones 2026 de la tabla por peso_poblacion (cociente exacto, resto al mayor peso, empate por clave); solo para construir el fixture; total provincial conservado",
        "equivalence_table": {"path": EQUIVALENCIA.as_posix(), "sha256": EQUIVALENCIA_SHA256},
        "feed_format": "sin documento: formato minsait_provisional supuesto (el que acepta adaptador_minsait_csv, más la columna ensayo)",
        "operator_check": "los sha256 de este MANIFEST solo se confrontan al regenerar: el Operador ejecuta el generador con el ZIP oficial y compara antes de subir los CSV (tests.test_datos_ensayo_congreso_t333 con DDD_ZIP_INFOELECTORAL_2023)",
        "files": files,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--manifest", type=Path, help="Dónde escribir el MANIFEST (por defecto, el del repo)")
    ns = ap.parse_args()
    manifest = generar(ns.zip, ns.out_dir, ns.root_dir)
    target = ns.manifest or (ns.root_dir / MANIFEST)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({t: {"file": f["file"], "sha256": f["sha256"]} for t, f in manifest["files"].items()}, indent=2))


if __name__ == "__main__":
    main()
