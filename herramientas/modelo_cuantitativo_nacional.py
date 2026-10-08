#!/usr/bin/env python3
"""Modelo cuantitativo nacional, independiente de la generación territorial.

VERSIÓN: 1.0.0
NOMBRE: Repartos exploratorios por población y comparación por unidades comunes
FECHA: 2026-10-08
ALCANCE: análisis local nacional; no genera mapas ni contratos productivos.
ESTADO: candidato; decisiones institucionales pendientes.
CAMBIOS: cálculo exacto de cuotas y K derivado, extracción INE y correspondencias.
MOTIVO: estudiar el perfil solicitado sin fijar K ni modificar el motor autonómico.
ORIGEN: nuevo componente; sin predecesor.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import zipfile
from collections import Counter
from fractions import Fraction
from pathlib import Path

VERSION = "1.0.0"
SOURCE_URL = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv"


def metadata():
    return {"version": VERSION, "name": "Modelo cuantitativo nacional exploratorio",
            "date": "2026-10-08", "scope": "análisis local; sin generación territorial",
            "status": "CANDIDATE_NOT_INSTITUTIONALLY_APPROVED",
            "changes": "cuotas exactas y K calculado a partir de población",
            "reason": "perfil de cálculo del Director de 120000 habitantes; no contrato electoral",
            "origin": "artefacto nuevo, sin predecesor"}


def positive_integer(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name}: entero positivo requerido")


def populations_checked(populations):
    if not populations:
        raise ValueError("universo provincial vacío")
    for code, population in populations.items():
        if not isinstance(code, str) or not re.fullmatch(r"\d{2}", code):
            raise ValueError("código provincial debe ser cadena de dos dígitos")
        if type(population) is not int or population < 0:
            raise ValueError(f"población inválida: {code}")
    return dict(sorted(populations.items()))


def half_up(numerator, denominator):
    """Enteros no negativos: empate exacto hacia arriba, sin float ni bankers rounding."""
    return (2 * numerator + denominator) // (2 * denominator)


def largest_remainder(populations, seats):
    """Hamilton puro; desempate por código INE ascendente, no por orden de entrada."""
    populations = populations_checked(populations)
    if type(seats) is not int or seats < 0:
        raise ValueError("escaños deben ser entero no negativo")
    total = sum(populations.values())
    if total == 0:
        if seats:
            raise ValueError("reparto positivo sin población")
        return {code: 0 for code in populations}
    quotas = {code: Fraction(pop * seats, total) for code, pop in populations.items()}
    allocation = {code: quota.numerator // quota.denominator for code, quota in quotas.items()}
    ranking = sorted(quotas, key=lambda code: (-(quotas[code] - allocation[code]), code))
    for code in ranking[:seats - sum(allocation.values())]:
        allocation[code] += 1
    assert sum(allocation.values()) == seats
    return allocation


def calculate(populations, target=120000):
    positive_integer(target, "target")
    populations = populations_checked(populations)
    total = sum(populations.values())
    derived_k = half_up(total, target)
    allocations = {
        "floor_independiente": {c: p // target for c, p in populations.items()},
        "nearest_half_up_independiente": {c: half_up(p, target) for c, p in populations.items()},
        "ceil_independiente": {c: (p + target - 1) // target for c, p in populations.items()},
        "hamilton_k_derivado": largest_remainder(populations, derived_k),
    }
    # Contrafactual: mantiene mínimos de referencia, pero NO el tamaño legal del Congreso.
    # Ceuta y Melilla quedan fijas en 1 y excluidas del reparto residual provincial.
    minimum_model = None
    if set(populations) == {f"{i:02d}" for i in range(1, 53)}:
        base = {c: 1 if c in {"51", "52"} else 2 for c in populations}
        remaining = derived_k - sum(base.values())
        provincial_populations = {c: p for c, p in populations.items() if c not in {"51", "52"}}
        if remaining >= 0 and (sum(provincial_populations.values()) > 0 or remaining == 0):
            residual = largest_remainder(provincial_populations, remaining)
            minimum_model = {c: base[c] + residual.get(c, 0) for c in populations}
            allocations["minimos_referencia_k_derivado"] = minimum_model
    results = []
    for rule, allocation in allocations.items():
        k = sum(allocation.values())
        rows = []
        for code, population in populations.items():
            assigned = allocation[code]
            row = {
                "province_code": code, "population": population,
                "target_quota": str(Fraction(population, target)),
                "k_assigned": assigned,
                "mean_population": str(Fraction(population, assigned)) if assigned else None,
            }
            if rule == "hamilton_k_derivado":
                row["allocation_quota"] = str(Fraction(population * derived_k, total)) if total else "0"
            elif rule == "minimos_referencia_k_derivado":
                provincial_total = sum(p for c, p in populations.items() if c not in {"51", "52"})
                row["allocation_quota"] = "1" if code in {"51", "52"} else str(2 + (Fraction(population * remaining, provincial_total) if provincial_total else 0))
            else:
                row["allocation_quota"] = row["target_quota"]
            rows.append(row)
        results.append({
            "rule": rule, "k_total": k, "population_total": total,
            "within_constitutional_size_reference": 300 <= k <= 400,
            "equals_congress_size_reference": k == 350,
            "minimum_reference_violations": [c for c, n in allocation.items() if n < (1 if c in {"51", "52"} else 2)],
            "city_fixed_one_reference_violations": [c for c in ("51", "52") if c in allocation and allocation[c] != 1],
            "zero_district_populated_provinces": [c for c, n in allocation.items() if n == 0 and populations[c] > 0],
            "rows": rows,
        })
    return {
        "schema": "ddd.national-quantitative-model/1.0", "version": VERSION,
        "metadata": metadata(),
        "status": "EXPLORATORY_NOT_INSTITUTIONALLY_APPROVED",
        "target_population_hypothesis": target, "population_total": total,
        "global_derived_k": derived_k,
        "minimum_reference_model_status": "CALCULATED" if minimum_model is not None else "NOT_APPLICABLE_OR_INFEASIBLE",
        "alternatives": results,
    }


def extract_ine(zip_path, expected_sha256, year):
    """Lee sólo agregados provinciales Total/Todas las edades; no suma secciones."""
    positive_integer(year, "year")
    path = Path(zip_path)
    with path.open("rb") as raw_source:
        digest = hashlib.file_digest(raw_source, "sha256").hexdigest()
    if digest != expected_sha256:
        raise ValueError("SHA del ZIP distinto del manifiesto")
    rows = {}; national = None
    with zipfile.ZipFile(path) as archive:
        with io.TextIOWrapper(archive.open("65034.csv"), encoding="utf-8-sig") as source:
            for row in csv.DictReader(source, delimiter="\t"):
                if row["Periodo"] != str(year) or row["Sexo"] != "Total" or row["Edad"] != "Todas las edades" or row["Municipios"] or row["Secciones"]:
                    continue
                raw = row["Total"]
                if not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+)", raw):
                    raise ValueError("población INE no entera")
                population = int(raw.replace(".", ""))
                province = row["Provincias"]
                if province:
                    code, name = province.split(" ", 1)
                    if code in rows:
                        raise ValueError(f"agregado provincial duplicado: {code}")
                    rows[code] = {"province_code": code, "name": name, "population": population}
                else:
                    if national is not None:
                        raise ValueError("total nacional duplicado")
                    national = population
    if set(rows) != {f"{i:02d}" for i in range(1, 53)}:
        raise ValueError("cobertura incompleta: se requieren 50 provincias y dos ciudades autónomas")
    if national != sum(r["population"] for r in rows.values()):
        raise ValueError("suma provincial distinta del total nacional INE")
    return {
        "metadata": metadata(),
        "provider": "Instituto Nacional de Estadística", "source_url": SOURCE_URL,
        "table": "65034", "source_zip_sha256": digest,
        "population_year": year, "reference_date": f"{year}-01-01",
        "filter": "Sexo=Total; Edad=Todas las edades; Municipios y Secciones vacíos",
        "national_population": national, "rows": [rows[c] for c in sorted(rows)],
    }


def compare_assignments(old, new, *, same_unit_universe_accredited=False):
    """Compara membresía, nunca igualdad del número de distrito o del código entre años.

    El caller debe acreditar equivalencia temporal de las unidades (o crosswalk común).
    Sin ella no se calculan métricas que puedan aparentar comparabilidad.
    """
    if same_unit_universe_accredited is not True:
        return {"status": "NOT_COMPARABLE", "reason": "unidad temporal común no acreditada", "pairs": None}
    for assignments in (old, new):
        if not assignments or any(not isinstance(u, str) or not u.strip() or not isinstance(d, str) or not d.strip() for u, d in assignments.items()):
            raise ValueError("asignaciones vacías o identidades inválidas")
    if set(old) != set(new):
        return {"status": "NOT_COMPARABLE", "reason": "cobertura de unidades diferente", "only_old": sorted(set(old) - set(new)), "only_new": sorted(set(new) - set(old)), "pairs": None}
    old_sizes = Counter(old.values()); new_sizes = Counter(new.values())
    intersections = Counter((old[u], new[u]) for u in old)
    pairs = []
    for (left, right), intersection in sorted(intersections.items()):
        pairs.append({"old_district": left, "new_district": right, "shared_units": intersection,
                      "old_units": old_sizes[left], "new_units": new_sizes[right],
                      "jaccard": str(Fraction(intersection, old_sizes[left] + new_sizes[right] - intersection)),
                      "exact_membership": intersection == old_sizes[left] == new_sizes[right]})
    return {"status": "COMPARABLE_MEMBERSHIP_ONLY", "unit_count": len(old),
            "old_district_count": len(old_sizes), "new_district_count": len(new_sizes),
            "exact_membership_pairs": sum(p["exact_membership"] for p in pairs), "pairs": pairs}


def inventory_maps(root):
    """Inventario de composiciones conservadas; no inventa mapas de años ausentes."""
    root = Path(root)
    paths = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
    records = []
    for raw in paths:
        if not raw.endswith("/M06/composicion_distritos.csv"):
            continue
        path = root / raw
        with path.open(encoding="utf-8") as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames or []
            rows = list(reader)
        records.append({"path": raw, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "territorial_scope": "autonómico",
                        "explicit_population_year": 2025 if "POP_2025" in columns else None,
                        "unit_count": len(rows), "district_count": len({r["district_id"] for r in rows}),
                        "columns": columns})
    return {"metadata": metadata(), "schema": "ddd.map-comparison-inventory/1.0",
            "status": "NOT_COMPARABLE", "reason": "No se ha identificado un par de mapas distritales 2022/2025 ni un universo temporal común acreditado; pendientes rutas del Director.",
            "search_scope": "composiciones M06 conservadas en Git; no búsqueda exhaustiva en disco personal ni consulta remota",
            "available_compositions": records,
            "paths_containing_2022": [p for p in paths if "2022" in p],
            "common_unit_universe_accredited": False,
            "exact_matches": None, "differences": None, "pairs": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--target", type=int, default=120000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inventory-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    # Calcula y valida todo antes de crear salida; exige destino nuevo para conservar runs.
    source = extract_ine(args.zip, args.expected_sha256, args.year)
    result = calculate({r["province_code"]: r["population"] for r in source["rows"]}, args.target)
    inventory = inventory_maps(args.inventory_root)
    args.output.mkdir(parents=True, exist_ok=False)
    for filename, payload in (("fuente_poblacion.json", source), ("modelo.json", result), ("comparacion_mapas.json", inventory)):
        (args.output / filename).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    names = {r["province_code"]: r["name"] for r in source["rows"]}
    with (args.output / "reparto_provincial.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["rule", "province_code", "name", "population", "target_quota", "allocation_quota", "k_assigned", "mean_population"], lineterminator="\n")
        writer.writeheader()
        for alternative in result["alternatives"]:
            for row in alternative["rows"]:
                writer.writerow({"rule": alternative["rule"], "name": names[row["province_code"]], **row})
    manifest = {"metadata": metadata(), "schema": "ddd.national-analysis-manifest/1.0",
                "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "source_zip_sha256": source["source_zip_sha256"],
                "files": {name: hashlib.sha256((args.output / name).read_bytes()).hexdigest() for name in
                          ("fuente_poblacion.json", "modelo.json", "comparacion_mapas.json", "reparto_provincial.csv")}}
    (args.output / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"population": result["population_total"], "global_derived_k": result["global_derived_k"], "alternatives": {r["rule"]: r["k_total"] for r in result["alternatives"]}}, sort_keys=True))


if __name__ == "__main__":
    main()
