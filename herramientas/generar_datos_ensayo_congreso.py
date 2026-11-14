#!/usr/bin/env python3
# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# FECHA: 2026-11-14
# CAMBIOS 1.0.0 (T-333): genera los datos de ENSAYO por mesa de las generales 2026-11-29 (nac22 Huesca, nac42 Soria, nac52 Melilla)
#   a partir del ZIP oficial Infoelectoral 2023 por mesa (sha256 fijado en contratos_infoelectoral.yaml). Son datos de 2023
#   REETIQUETADOS como ENSAYO (columna `ensayo` en cada fila y nombre `ensayo_…`): NO son resultados de 2026 ni datos oficiales.
#   Formato = el del adaptador minsait_csv (+ la columna `ensayo`). Escribe un MANIFEST con sha256. No sube nada: lo hace el Operador.
# ANTERIOR: (fichero nuevo)
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
# territorio de ensayo → (id de la elección 2023 del contrato Infoelectoral, eslug del fichero)
TERRITORIOS = {
    "nac22": ("congreso_huesca_2023-07-23", "huesca"),
    "nac42": ("congreso_soria_2023-07-23", "soria"),
    "nac52": ("congreso_melilla_2023-07-23", "melilla"),
}
FIELDS = fim.OUTPUT_FIELDS + ("ensayo",)


def nombre_fichero(slug: str) -> str:
    return f"ensayo_congreso_{slug}_{ENSAYO_DATE}.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def reetiquetar(csv_in: Path, csv_out: Path) -> dict:
    """Copia el CSV largo por mesa añadiendo la marca ENSAYO en cada fila; salida determinista (LF, orden del origen)."""
    rows = 0
    with csv_in.open(encoding="utf-8", newline="") as src, csv_out.open("w", encoding="utf-8", newline="") as dst:
        reader = csv.DictReader(src)
        if tuple(reader.fieldnames or ()) != fim.OUTPUT_FIELDS:
            raise ValueError(f"Cabecera inesperada en el CSV de origen: {reader.fieldnames}")
        writer = csv.DictWriter(dst, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in reader:
            writer.writerow({**row, "ensayo": MARCA})
            rows += 1
    return {"rows": rows}


def generar(zip_path: Path, out_dir: Path, root_dir: Path = Path(".")) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    infoelectoral = yaml.safe_load((root_dir / fim.DEFAULT_PATH).read_text(encoding="utf-8"))["contracts"]
    files = {}
    zip_sha = None
    for tid, (election_2023, slug) in TERRITORIOS.items():
        contract = fim.resolve(election_id=election_2023, territory_id=tid, election_date="2023-07-23", root_dir=root_dir)
        with tempfile.TemporaryDirectory() as tmp:
            conv = fim.convert(zip_path, contract, Path(tmp) / "mesas.csv")  # verifica el sha256 del ZIP y los totales
            target = out_dir / nombre_fichero(slug)
            rows = reetiquetar(Path(tmp) / "mesas.csv", target)["rows"]
        zip_sha = conv["source_sha256"]
        exp = infoelectoral[election_2023]["expected"]
        files[tid] = {
            "file": target.name, "sha256": sha256(target), "bytes": target.stat().st_size, "rows": rows,
            "election_id_ensayo": f"congreso_{slug}_{ENSAYO_DATE}", "derived_from_election_id": election_2023,
            "province": str(contract["province"]), "ccaa": str(exp["ccaa"]),
            "sections": conv["sections"], "polling_stations": conv["polling_stations"], "candidate_votes": conv["candidate_votes"],
        }
    return {
        "schema": "ddd-ensayo-datos-manifest/1.0",
        "rehearsal": True,
        "official": False,
        "status": "PROVISIONAL",
        "mark": MARCA,
        "warning": "Datos de ENSAYO derivados del ZIP Infoelectoral 2023 por mesa; no son resultados de 2026 ni datos oficiales.",
        "election_date_label": ENSAYO_DATE,
        "release_tag": RELEASE_TAG,
        "derived_from": {"source": "Ministerio del Interior — Infoelectoral 02202307_MESA.zip", "sha256": zip_sha},
        "section_keys": "seccionado 2023 (sin rekey a 2026): la tabla de equivalencia 2026→2023 deja sin cambio las secciones que no figuran en ella",
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
