#!/usr/bin/env python3
"""Alta del producto paralelo «Congreso 350»: un territorio por provincia con K = escaños reales de 2023.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: T-102 (decisión D-19 del propietario). Para cada provincia del Congreso ya dada de alta
  (`congreso_<prov>`, K de N06, 407 distritos) crea su gemelo `congreso350_<prov>` con
  K = escaños de la circunscripción en las generales del 23-07-2023, leídos del CSV oficial
  `configuracion/resultados_oficiales_congreso_2023.csv` (BOE-A-2023-18907; su sha256 queda en el contrato).
  Copia del gemelo 407 todo lo demás (fuentes, CRS, puentes, límites de población, exenciones, contrato
  Infoelectoral) y cambia solo identidad, rutas y K. Añade filas nuevas al catálogo maestro, la política,
  la matriz de legislatura, el registro electoral, las fuentes territoriales, el catálogo de preparación,
  los contratos Infoelectoral y los selectores de los workflows. Idempotente: lo ya dado de alta no se toca.
NO HACE: tocar los 407 (contratos, K, M08, publicaciones); provincias insulares (Baleares, Las Palmas,
  Santa Cruz de Tenerife: su reparto por islas espera decisión del propietario); lanzar ni publicar.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SEATS = Path("configuracion/resultados_oficiales_congreso_2023.csv")
BOE = "BOE-A-2023-18907"
TOTAL_SEATS = 350
INSULAR = {"07", "35", "38"}
PREFIX = "congreso350_"
LABEL_PREFIX = "Congreso 350 "
VARIANT = "congreso_350"
WORKFLOWS = (
    "ejecucion-completa-proyecto.yml", "incorporacion-resultados-electorales.yml", "preparacion-fuentes.yml",
    "preparacion-legislatura-vigente.yml", "preparacion-resultados-electorales.yml", "produccion-distritos.yml",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seats_2023(root: Path = ROOT) -> dict[str, int]:
    """Escaños por circunscripción (CPRO → K) del CSV oficial; exige 52 provincias y 350 escaños."""
    seats: dict[str, int] = {}
    with (root / SEATS).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            code, k = row["codigo"].zfill(2), int(row["escanos_circunscripcion"])
            if seats.setdefault(code, k) != k:
                raise ValueError(f"Escaños distintos en filas de la provincia {code}")
    if len(seats) != 52 or sum(seats.values()) != TOTAL_SEATS:
        raise ValueError(f"El CSV oficial debe dar 52 provincias y {TOTAL_SEATS} escaños")
    return seats


def twin_id(tid: str) -> str:
    return PREFIX + tid.removeprefix("congreso_")


def twin_label(label: str) -> str:
    return LABEL_PREFIX + label.removeprefix("Congreso ")


def provinces(root: Path = ROOT) -> list[dict]:
    """Gemelos 350 de las provincias peninsulares, Ceuta y Melilla (49), en orden INE."""
    master = yaml.safe_load((root / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8"))
    seats = seats_2023(root)
    rows = []
    for row in master.get("pilot_territories") or []:
        if row.get("batch") not in ("congreso_provincias", "piloto_congreso"):
            continue
        code = row["province_codes"][0]
        if code in INSULAR:
            continue
        rows.append({"code": code, "source_id": row["territory_id"], "source_label": row["name"],
                     "territory_id": twin_id(row["territory_id"]), "label": twin_label(row["name"]),
                     "pilot_code": f"R{code}", "k": seats[code], "k_407": int(row["k_districts"])})
    return sorted(rows, key=lambda r: r["code"])


def rationale(p: dict, csv_sha: str) -> str:
    # Sin «/»: el validador del contrato resuelve como ruta los textos que la llevan.
    return (f"Congreso 350 (D-19): K={p['k']} son los escaños de {p['label'].removeprefix(LABEL_PREFIX)} "
            f"(CPRO {p['code']}) en las generales del 23-07-2023, {BOE}; CSV oficial de escaños con sha256 {csv_sha}.")


def k_reference(csv_sha: str) -> str:
    return f"{BOE}; {SEATS} sha256={csv_sha}"


LEGAL_CONTEXT = "Escaños por circunscripción de las generales del 23-07-2023 (D-19)."


def _rename(text: str, p: dict) -> str:
    text = re.sub(rf"\b{re.escape(p['source_id'])}(?![a-z])", p["territory_id"], text)
    return text.replace(p["source_label"], p["label"])


def twin_contract(root: Path, p: dict, csv_sha: str) -> dict:
    """Contrato M01–M06 del gemelo: el del 407 con identidad, rutas y K cambiados."""
    src = root / f"territorios/{p['source_id']}/config/{p['source_id']}_2025.yaml"
    contract = yaml.safe_load(_rename(src.read_text(encoding="utf-8"), p))
    k, code = p["k"], p["code"]
    tc = contract["territory_contract"]
    tc.update({"k_districts": k, "k_source": "norma", "k_rationale": rationale(p, csv_sha),
               "k_reference_scope": "legal_apportionment_2023", "k_reference_source": k_reference(csv_sha),
               "apportionment_source": "boe_congreso_2023", "legal_apportionment_reused": True,
               "legal_apportionment_context": LEGAL_CONTEXT})
    mods = contract["modulos"]
    mods["modulo_04_generar_semillas"]["k_districts"] = k
    mods["modulo_06_consolidar_distritos"]["expected_districts"] = k
    contract["validation"]["expected_districts"] = k
    contract["validation"]["province_districts"] = {code: k}
    contract["meta"]["product_variant"] = VARIANT
    contract["meta"]["parent_territory_id"] = p["source_id"]
    return contract


def _append(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    path.write_text(content.rstrip("\n") + "\n" + text.rstrip("\n") + "\n", encoding="utf-8")


def _line_of(path: Path, needle: str) -> str:
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if needle in l]
    if len(lines) != 1:
        raise ValueError(f"{path}: se esperaba una línea con {needle!r} y hay {len(lines)}")
    return lines[0]


def _block_of(path: Path, start: str) -> str:
    """Bloque YAML que empieza en la línea `start` y acaba antes de la siguiente con la misma sangría o menos."""
    lines = path.read_text(encoding="utf-8").splitlines()
    i = lines.index(start)
    lead = len(start) - len(start.lstrip(" "))
    j = i + 1
    while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip(" ")) > lead):
        j += 1
    while j > i + 1 and not lines[j - 1].strip():
        j -= 1
    return "\n".join(lines[i:j])


def _policy_block(root: Path, p: dict, csv_sha: str) -> str:
    path = root / "configuracion/politica_generacion_territorial_2025.yaml"
    block = _rename(_block_of(path, f"  {p['source_id']}:"), p)
    block = re.sub(r"(?m)^    k: \d+$", f"    k: {p['k']}", block)
    # El materializador (01) reconstruye estos campos del contrato desde la política.
    extra = (f"    k_source: norma\n    k_reference_scope: legal_apportionment_2023\n"
             f"    k_reference_source: \"{k_reference(csv_sha)}\"\n    apportionment_source: boe_congreso_2023\n"
             f"    legal_apportionment_reused: true\n    legal_context: \"{LEGAL_CONTEXT}\"")
    block = block.replace("    k_source: formula", extra)
    return re.sub(r'(?m)^    rationale: ".*"$', f'    rationale: "{rationale(p, csv_sha)}"', block, count=1)


def _master_line(root: Path, p: dict, csv_sha: str) -> str:
    line = _line_of(root / "configuracion/catalogo_territorios_espana_2025.yaml", f"territory_id: {p['source_id']},")
    line = _rename(line, p)
    line = re.sub(r"pilot_code: '\w+'", f"pilot_code: '{p['pilot_code']}'", line)
    line = re.sub(r" plate_code: '\w+',", "", line)
    line = re.sub(r"scope: \w+,", f"scope: {VARIANT},", line)
    line = re.sub(r"batch: \w+,", f"batch: {VARIANT},", line)
    line = re.sub(r"k_districts: \d+", f"k_districts: {p['k']}", line).replace("k_source: formula", "k_source: norma")
    return re.sub(r'k_rationale: ".*"\}$', f'k_rationale: "{rationale(p, csv_sha)}", parent_territory_id: {p["source_id"]}}}', line)


def declared(root: Path) -> set[str]:
    master = yaml.safe_load((root / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8"))
    return {str(r["territory_id"]) for r in master.get("pilot_territories") or []}


def generate(root: Path = ROOT, only: list[str] | None = None) -> list[str]:
    csv_sha = _sha(root / SEATS)
    existing = declared(root)
    todo = [p for p in provinces(root) if p["territory_id"] not in existing
            and (not only or p["territory_id"] in only or p["code"] in only)]
    for p in todo:
        tid = p["territory_id"]
        _append(root / "configuracion/catalogo_territorios_espana_2025.yaml", _master_line(root, p, csv_sha))
        policy = root / "configuracion/politica_generacion_territorial_2025.yaml"
        text = policy.read_text(encoding="utf-8")
        cut = text.index("\narchipelago:")
        policy.write_text(text[:cut].rstrip("\n") + "\n\n" + _policy_block(root, p, csv_sha) + "\n" + text[cut:], encoding="utf-8")
        prep = root / "configuracion/preparacion_legislatura_vigente.yaml"
        block = _rename(_block_of(prep, f"  - territory_id: {p['source_id']}"), p)
        _append(prep, re.sub(r"(?m)^    pilot_code: \w+$", f"    pilot_code: {p['pilot_code']}", block))
        reg = root / "configuracion/registro_electoral.yaml"
        line = _rename(_line_of(reg, f"  {p['source_id']}: {{"), p)
        _append(reg, re.sub(r"pilot_code: \w+", f"pilot_code: {p['pilot_code']}", line))
        _append(root / "fuentes/territorios_espana.yaml", _rename(_line_of(root / "fuentes/territorios_espana.yaml",
                                                                             f"{{id: {p['source_id']},"), p))
        infoe = root / "configuracion/contratos_infoelectoral.yaml"
        _append(infoe, _rename(_block_of(infoe, f"  {p['source_id']}_2023-07-23:"), p))
        _append(root / "configuracion/catalogo_preparacion.yaml", f"""- territory_id: {tid}
  name: {p['label']}
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
        cfg = root / f"territorios/{tid}/config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "fuentes_oficiales.yaml").write_text(
            _rename((root / f"territorios/{p['source_id']}/config/fuentes_oficiales.yaml").read_text(encoding="utf-8"), p),
            encoding="utf-8")
        (cfg / f"{tid}_2025.yaml").write_text(
            yaml.safe_dump(twin_contract(root, p, csv_sha), allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8")
        for workflow in WORKFLOWS:
            _add_option(root / ".github/workflows" / workflow, p["label"])
    return [p["territory_id"] for p in todo]


def _add_option(path: Path, label: str) -> None:
    """Añade la etiqueta tras la última opción de territorio (lista en bloque o en línea)."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    listed = [i for i, l in enumerate(lines) if l.startswith("          - Congreso ")]
    inline = [i for i, l in enumerate(lines) if "options:" in l and "'Congreso " in l]
    if listed:
        lines.insert(listed[-1] + 1, f"          - {label}\n")
    elif inline:
        i = inline[0]
        lines[i] = lines[i].rstrip("\n").rstrip("]") + f", '{label}']\n"
    else:
        raise ValueError(f"{path}: no encuentro el selector de provincias")
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--root-dir", type=Path, default=ROOT)
    parser.add_argument("--solo", nargs="*", default=None, help="territory_id o CPRO (por defecto, las 49)")
    args = parser.parse_args()
    added = generate(args.root_dir, args.solo)
    print(f"{len(added)} provincias Congreso 350 dadas de alta: {', '.join(added)}")


if __name__ == "__main__":
    main()
