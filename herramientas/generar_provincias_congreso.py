#!/usr/bin/env python3
"""Alta de las provincias del Congreso como territorios del flujo 00, con Huesca como plantilla.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-10-31 · ESTADO: candidato
QUÉ HACE: para cada provincia del reparto N06 (K aprobado, 407 escaños) que aún no exista, añade la
  entrada en el catálogo maestro (pilot_territories, con número INE y letras de matrícula), la política,
  la matriz de legislatura, el registro electoral, las fuentes territoriales, el catálogo de preparación,
  el contrato Infoelectoral (totales calculados del ZIP oficial nacional) y el contrato bootstrap M01–M06.
  Es idempotente: una provincia ya dada de alta no se toca.
NO HACE: provincias insulares (Baleares, Las Palmas, Santa Cruz de Tenerife), que necesitan la partición
  por islas; ni lanzar ejecuciones.
ANTERIOR: ninguno (herramienta nueva).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPARTO = Path("docs/ESTUDIOS/N06_DECISION_K_20261012/resultados/reparto_ddd_52.csv")
ELECTION_DATE = "2023-07-23"
ELECTION_PREFIX = "02202307"
INSULAR = {"07", "35", "38"}
TEMPLATE = "congreso_huesca"

# Nombre en español y letras de la matrícula provincial (último sistema provincial).
PROVINCES = {
    "01": ("Álava", "VI"), "02": ("Albacete", "AB"), "03": ("Alicante", "A"), "04": ("Almería", "AL"),
    "05": ("Ávila", "AV"), "06": ("Badajoz", "BA"), "07": ("Baleares", "IB"), "08": ("Barcelona", "B"),
    "09": ("Burgos", "BU"), "10": ("Cáceres", "CC"), "11": ("Cádiz", "CA"), "12": ("Castellón", "CS"),
    "13": ("Ciudad Real", "CR"), "14": ("Córdoba", "CO"), "15": ("La Coruña", "C"), "16": ("Cuenca", "CU"),
    "17": ("Gerona", "GI"), "18": ("Granada", "GR"), "19": ("Guadalajara", "GU"), "20": ("Guipúzcoa", "SS"),
    "21": ("Huelva", "H"), "22": ("Huesca", "HU"), "23": ("Jaén", "J"), "24": ("León", "LE"),
    "25": ("Lérida", "L"), "26": ("La Rioja", "LO"), "27": ("Lugo", "LU"), "28": ("Madrid", "M"),
    "29": ("Málaga", "MA"), "30": ("Murcia", "MU"), "31": ("Navarra", "NA"), "32": ("Orense", "OU"),
    "33": ("Asturias", "O"), "34": ("Palencia", "P"), "35": ("Las Palmas", "GC"), "36": ("Pontevedra", "PO"),
    "37": ("Salamanca", "SA"), "38": ("Santa Cruz de Tenerife", "TF"), "39": ("Cantabria", "S"),
    "40": ("Segovia", "SG"), "41": ("Sevilla", "SE"), "42": ("Soria", "SO"), "43": ("Tarragona", "T"),
    "44": ("Teruel", "TE"), "45": ("Toledo", "TO"), "46": ("Valencia", "V"), "47": ("Valladolid", "VA"),
    "48": ("Vizcaya", "BI"), "49": ("Zamora", "ZA"), "50": ("Zaragoza", "Z"), "51": ("Ceuta", "CE"),
    "52": ("Melilla", "ML"),
}
WORKFLOWS = (
    "ejecucion-completa-proyecto.yml", "incorporacion-resultados-electorales.yml", "preparacion-fuentes.yml",
    "preparacion-legislatura-vigente.yml", "preparacion-resultados-electorales.yml", "produccion-distritos.yml",
)


def slug(name: str) -> str:
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", plain).strip("_")


def provinces(root: Path) -> list[dict]:
    rows = []
    with (root / REPARTO).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            code = row["province_code"].zfill(2)
            name, plate = PROVINCES[code]
            rows.append({"code": code, "name": name, "plate": plate, "k": int(row["k_province"]),
                         "population_2025": int(row["population_2025"]),
                         "territory_id": f"congreso_{slug(name)}", "label": f"Congreso {name}",
                         "pilot_code": f"C{code}"})
    if len(rows) != 52 or sum(r["k"] for r in rows) != 407:
        raise ValueError("El reparto N06 debe tener 52 provincias y 407 escaños")
    return rows


def _rationale(p: dict) -> str:
    return (f"Congreso: K={p['k']} es la cuota de {p['name']} (CPRO {p['code']}) en N06-OWNER-20261012-K, con K_i "
            "igual al mayor entre 1 y la parte entera de (P_i + 60.000) entre 120.000, y K2025 = 407.")


def electoral_stats(zip_path: Path) -> dict[str, dict]:
    """Totales por provincia del ZIP oficial por mesa, sin CERA (municipio 999)."""
    stats: dict[str, dict] = defaultdict(lambda: {"sections": set(), "polling_stations": 0, "candidate_votes": 0,
                                                  "blank_votes": 0, "null_votes": 0, "parties": set(),
                                                  "cera_records": 0, "ccaa": set()})
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open("09022307.DAT") as fh:
            for raw in fh:
                line = raw.decode("iso-8859-1").rstrip("\r\n")
                if not line.startswith(ELECTION_PREFIX):
                    continue
                s = stats[line[11:13]]
                if line[13:16] == "999":
                    s["cera_records"] += 1
                    continue
                s["polling_stations"] += 1
                s["sections"].add((line[13:16], line[16:18], line[18:22].strip()))
                s["ccaa"].add(line[9:11])
                s["blank_votes"] += int(line[65:72]); s["null_votes"] += int(line[72:79])
                s["candidate_votes"] += int(line[79:86])
        with archive.open("10022307.DAT") as fh:
            for raw in fh:
                line = raw.decode("iso-8859-1").rstrip("\r\n")
                if line.startswith(ELECTION_PREFIX) and line[13:16] != "999":
                    stats[line[11:13]]["parties"].add(line[23:29])
    result = {}
    for code, s in stats.items():
        if len(s["ccaa"]) != 1:
            continue
        result[code] = {"ccaa": s["ccaa"].pop(), "sections": len(s["sections"]),
                        "polling_stations": s["polling_stations"], "parties": len(s["parties"]),
                        "candidate_votes": s["candidate_votes"], "blank_votes": s["blank_votes"],
                        "null_votes": s["null_votes"],
                        "voters": s["candidate_votes"] + s["blank_votes"] + s["null_votes"],
                        "cera_records": s["cera_records"]}
    return result


def _append(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    path.write_text(content.rstrip("\n") + "\n" + text.rstrip("\n") + "\n", encoding="utf-8")


def _insert_before(path: Path, marker: str, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    index = content.index(marker)
    path.write_text(content[:index] + text.rstrip("\n") + "\n" + content[index:], encoding="utf-8")


def _bootstrap_contract(root: Path, p: dict) -> None:
    """Contrato M01–M06 inicial con un paquete sintético, como el de Huesca; la 01 lo rematerializa."""
    sys.path.insert(0, str(root))
    from herramientas.materializar_contrato_generacion import materialize
    from tests.test_materializacion_contratos_nacionales import population_package
    work = Path(tempfile.mkdtemp())
    try:
        (work / "configuracion").mkdir(parents=True)
        (work / "inputs").mkdir()
        shutil.copy2(root / "configuracion/politica_generacion_territorial_2025.yaml", work / "configuracion")
        shutil.copy2(root / "configuracion/particiones_insulares_2025.json", work / "configuracion")
        (work / "configuracion/catalogo_territorios_espana_2025.yaml").write_text(
            f"territories:\n  - {{territory_id: {p['territory_id']}, name: {p['label']}, province_codes: ['{p['code']}'], "
            "batch: piloto_congreso, status: bootstrap, contract_level: bootstrap_m01_m03}\n", encoding="utf-8")
        (work / "inputs/MANIFEST.sha256").write_text(
            "0" * 64 + "  inputs/seccionado_2023.zip\n" + "1" * 64 + "  inputs/65034.csv.zip\n", encoding="utf-8")
        package = population_package(work, [(f"{p['code']}12501001", p["population_2025"])],
                                     population_year=2023, section_year=2023)
        result = materialize(work, p["territory_id"], "2025", package, population_year="2023", section_year="2023")
        target = root / result["contract_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work / result["contract_path"], target)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def generate(root: Path, zip_path: Path) -> list[str]:
    master_path = root / "configuracion/catalogo_territorios_espana_2025.yaml"
    existing = {row["territory_id"] for row in yaml.safe_load(master_path.read_text(encoding="utf-8")).get("pilot_territories") or []}
    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    template = (yaml.safe_load((root / "configuracion/contratos_infoelectoral.yaml").read_text(encoding="utf-8"))
                ["contracts"][f"{TEMPLATE}_{ELECTION_DATE}"])
    if zip_sha != template["source_sha256"]:
        raise ValueError("El ZIP no es el oficial declarado en el contrato de Huesca")
    stats = electoral_stats(zip_path)
    sources_template = (root / f"territorios/{TEMPLATE}/config/fuentes_oficiales.yaml").read_text(encoding="utf-8")
    added: list[str] = []
    for p in provinces(root):
        if p["territory_id"] in existing or p["code"] in INSULAR:
            continue
        tid, label, code, k = p["territory_id"], p["label"], p["code"], p["k"]
        election_id = f"{tid}_{ELECTION_DATE}"
        e = stats[code]
        _append(master_path,
                f"  - {{territory_id: {tid}, pilot_code: '{p['pilot_code']}', plate_code: '{p['plate']}', scope: congreso, "
                f"name: {label}, province_codes: ['{code}'], batch: congreso_provincias, status: generation_ready, "
                f"contract_level: production_m01_m06, production_authorization: AUTHORIZED, k_districts: {k}, "
                f"k_source: formula, k_rationale: \"{_rationale(p)}\"}}")
        _insert_before(root / "configuracion/politica_generacion_territorial_2025.yaml", "\narchipelago:", f"""
  {tid}:
    k: {k}
    k_source: formula
    partition_mode: province_hamilton
    rationale: "{_rationale(p)}"
    population_limits:
      population_floor_ratio: 0.85
      population_cap_ratio: 1.15
      target_tolerance_ratio: 0.15
      municipality_atomicity_limit_ratio: 1.15
      decided_at: "2026-10-31"
      evidence: "configuracion/politica_generacion_territorial_2025.yaml#territories.{TEMPLATE}.population_limits"
      rationale: "Reglas del Congreso del propietario, iguales que el piloto Huesca: suelo 85 %, techo 115 % y un municipio que cabe bajo el techo no se divide."
""")
        _append(root / "configuracion/preparacion_legislatura_vigente.yaml", f"""  - territory_id: {tid}
    pilot_code: {p['pilot_code']}
    name: {label}
    election_id: {election_id}
    election_date: '{ELECTION_DATE}'
    territorial: {{population_required_year: 2023, population_current_year: 2025, population_selected_year: 2023, population_lag_years: 0, population_reference_date: '2023-01-01', section_required_year: 2023, section_current_year: 2025, section_selected_year: 2023, section_lag_years: 0, section_reference_label: 'Secciones_2023', temporal_evidence: configuracion/evidencia_disponibilidad_fuentes_territoriales_2026-09-30.json, action: ACQUIRE_WRONG_YEAR, reason: 'Congreso: elección general del 23-07-2023; población por sección y seccionado oficial 2023, contemporáneos de la elección.'}}
    electoral: {{source: 'Ministerio del Interior — Infoelectoral, resultados por mesa, Congreso 23-07-2023', granularity: section_party, action: ACQUIRE, definitive_gap_status: NOT_EVALUATED}}""")
        _append(root / "configuracion/registro_electoral.yaml",
                f"  {tid}: {{pilot_code: {p['pilot_code']}, name: {label}, election_id: {election_id}, "
                f"election_date: '{ELECTION_DATE}', title: Congreso de los Diputados 2023 — {p['name']}}}")
        _append(root / "fuentes/territorios_espana.yaml", f"  - {{id: {tid}, name: {label}, province_codes: ['{code}']}}")
        _append(root / "configuracion/catalogo_preparacion.yaml", f"""- territory_id: {tid}
  name: {label}
  editions:
    '2025':
      territory_declared: true
      preparation_status: READY_INITIAL
      contract_path: territorios/{tid}/config/{tid}_2025.yaml
      territorial_source_declaration: territorios/{tid}/config/fuentes_oficiales.yaml
      electoral_source_declaration: null
      territorial_sources_prepared: false
      territorial_contract_complete: false
      territorial_product_available: false
      electoral_source_prepared: false
      electoral_product_available: false
      territorial_certification: NOT_CERTIFIED
      production_authorization: AUTHORIZED
      last_valid_checkpoint: null""")
        expected = "\n".join(f"      {key}: {repr(value) if key == 'ccaa' else value}" for key, value in e.items())
        _append(root / "configuracion/contratos_infoelectoral.yaml", f"""  {election_id}:
    territory_id: {tid}
    election_date: '{ELECTION_DATE}'
    publisher: {template['publisher']}
    license: '{template['license']}'
    source_url: {template['source_url']}
    source_sha256: {zip_sha}
    source_bytes: {template['source_bytes']}
    mirror: {{release_tag: {template['mirror']['release_tag']}, asset: {template['mirror']['asset']}}}
    election_prefix: '{ELECTION_PREFIX}'
    files:
      mesas: {template['files']['mesas']}
      candidaturas_mesa: {template['files']['candidaturas_mesa']}
      candidaturas: {template['files']['candidaturas']}
    province: '{code}'
    expected:
{expected}""")
        sources = sources_template.replace(TEMPLATE, tid).replace("Congreso Huesca", label).replace("'22'", f"'{code}'")
        target = root / f"territorios/{tid}/config/fuentes_oficiales.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(sources, encoding="utf-8")
        for workflow in WORKFLOWS:
            path = root / ".github/workflows" / workflow
            text = path.read_text(encoding="utf-8")
            previous = added[-1] if added else "Congreso Huesca"
            previous_label = previous if previous == "Congreso Huesca" else next(
                q["label"] for q in provinces(root) if q["territory_id"] == previous)
            if f"          - {previous_label}\n" in text:
                text = text.replace(f"          - {previous_label}\n", f"          - {previous_label}\n          - {label}\n", 1)
            elif f"'{previous_label}']" in text:
                text = text.replace(f"'{previous_label}']", f"'{previous_label}', '{label}']", 1)
            else:
                raise ValueError(f"{workflow}: no encuentro la opción {previous_label}")
            path.write_text(text, encoding="utf-8")
        added.append(tid)
    for tid in added:
        _bootstrap_contract(root, next(p for p in provinces(root) if p["territory_id"] == tid))
    return added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, required=True, help="02202307_MESA.zip oficial (release espejo)")
    parser.add_argument("--root-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    added = generate(args.root_dir, args.zip)
    print(f"{len(added)} provincias dadas de alta: {', '.join(added)}")


if __name__ == "__main__":
    main()
