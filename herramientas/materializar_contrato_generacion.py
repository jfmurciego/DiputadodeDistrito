#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Materializa un contrato de generación M01-M06 a partir de fuentes ya preparadas.

La puerta contractual se conserva como validación estructural, pero deja de exigir
industrialización manual territorio a territorio. 01 prepara fuentes y este
materializador completa automáticamente el contrato que 02 necesita.
"""
from __future__ import annotations

import argparse
import copy
import csv
import io
import json
import math
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import yaml

from ddd_core.territory_contract import validate_production_contract

POLICY = Path("configuracion/politica_generacion_territorial_2025.yaml")
MASTER = Path("configuracion/catalogo_territorios_espana_2025.yaml")
PARTITIONS = Path("configuracion/particiones_insulares_2025.json")


def yload(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def ywrite(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")



def update_master_entry(path: Path, territory_id: str, *, status: str, authorization: str, k: int, k_source: str, k_rationale: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = next((i for i, line in enumerate(lines) if f"territory_id: {territory_id}," in line), None)
    if idx is None:
        raise ValueError(f"{territory_id}: ausente del catálogo territorial maestro")
    line = lines[idx]
    values = {
        "status": status,
        "contract_level": "production_m01_m06",
        "production_authorization": authorization,
        "k_districts": str(int(k)),
        "k_source": k_source,
        "k_rationale": json.dumps(str(k_rationale), ensure_ascii=False),
    }
    for key, value in values.items():
        pattern = re.compile(rf"{re.escape(key)}:\s*(?:\"[^\"]*\"|'[^']*'|[^,}}]+)")
        replacement = f"{key}: {value}"
        if pattern.search(line):
            line = pattern.sub(replacement, line)
        else:
            line = line[:-1] + f", {replacement}" + "}"
    lines[idx] = line
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def _open_population_zip(package: Path) -> zipfile.ZipFile:
    direct = list(package.rglob("65034.csv.zip")) if package.exists() else []
    if direct:
        return zipfile.ZipFile(direct[0])
    bundles = list(package.rglob("prepared_sources.zip")) if package.exists() else []
    if not bundles:
        raise FileNotFoundError(f"No se localiza 65034.csv.zip ni prepared_sources.zip en {package}")
    with zipfile.ZipFile(bundles[0]) as outer:
        candidates = [n for n in outer.namelist() if n.endswith("/65034.csv.zip") or n == "65034.csv.zip"]
        if len(candidates) != 1:
            raise ValueError(f"Paquete territorial ambiguo: 65034.csv.zip={candidates}")
        payload = outer.read(candidates[0])
    return zipfile.ZipFile(io.BytesIO(payload))


def section_populations(package: Path, edition: str, province_codes: list[str]) -> dict[str, int]:
    wanted = {str(x).zfill(2) for x in province_codes}
    result: dict[str, int] = {}
    with _open_population_zip(package) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv") and "__MACOSX" not in n]
        if not names:
            raise ValueError("65034.csv.zip no contiene CSV")
        with z.open(names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            header = text.readline()
            if not header:
                raise ValueError("65034.csv está vacío")
            delimiter = ";" if header.count(";") > header.count("\t") else "\t"
            fieldnames = next(csv.reader([header], delimiter=delimiter))
            required = {"Periodo", "Sexo", "Edad", "Secciones", "Total"}
            if not required.issubset(set(fieldnames)):
                raise ValueError(
                    "65034.csv no contiene las columnas esperadas; "
                    f"delimitador={delimiter!r}; columnas={fieldnames}"
                )
            reader = csv.DictReader(text, fieldnames=fieldnames, delimiter=delimiter)
            for row in reader:
                if str(row.get("Periodo") or "") != str(edition):
                    continue
                if str(row.get("Sexo") or "") != "Total" or str(row.get("Edad") or "") != "Todas las edades":
                    continue
                sec = str(row.get("Secciones") or "").split(" ", 1)[0].strip()
                if len(sec) != 10 or sec[:2] not in wanted:
                    continue
                raw_total = str(row.get("Total") or "0").strip().replace(".", "").replace(",", "")
                result[sec] = int(raw_total or "0")
    if not result:
        raise ValueError("La fuente de población preparada no contiene secciones para el territorio")
    return result


def hamilton(populations: dict[str, int], k: int) -> dict[str, int]:
    total = sum(populations.values())
    if total <= 0 or k <= 0:
        raise ValueError("Población/K inválidos para Hamilton")
    exact = {key: k * value / total for key, value in populations.items()}
    out = {key: math.floor(value) for key, value in exact.items()}
    remaining = k - sum(out.values())
    order = sorted(exact, key=lambda key: (exact[key] - math.floor(exact[key]), populations[key], key), reverse=True)
    for key in order[:remaining]:
        out[key] += 1
    if sum(out.values()) != k:
        raise AssertionError("Hamilton no conserva K")
    return out


def component_hamilton(populations: dict[str, int], k: int, floor_ratio: float) -> tuple[dict[str, int], list[str]]:
    """Hamilton con al menos un distrito por componente y suelo factible.

    Si una componente completa no alcanza el suelo global, recibe exactamente un
    distrito y queda declarada como excepción. No se crean conexiones marítimas.
    """
    if k < len(populations):
        raise ValueError(f"K={k} menor que componentes físicas={len(populations)}")
    keys = sorted(populations)
    total = sum(populations.values())
    target = total / k
    floor = target * floor_ratio

    # Un asiento base por componente; Hamilton reparte el resto.
    q = {key: 1 for key in keys}
    rest = k - len(keys)
    exact_rest = {key: rest * populations[key] / total for key in keys}
    for key in keys:
        q[key] += math.floor(exact_rest[key])
    remaining = k - sum(q.values())
    order = sorted(keys, key=lambda key: (exact_rest[key] - math.floor(exact_rest[key]), populations[key], key), reverse=True)
    for key in order[:remaining]:
        q[key] += 1

    # Ninguna componente con más de un distrito puede forzar medias bajo el suelo.
    freed = 0
    for key in keys:
        maximum = max(1, int(math.floor(populations[key] / floor + 1e-12)))
        if q[key] > maximum:
            freed += q[key] - maximum
            q[key] = maximum

    # Redistribuir sólo donde el nuevo promedio sigue sobre el suelo.
    while freed:
        candidates = [
            key for key in keys
            if populations[key] / (q[key] + 1) >= floor - 1e-9
        ]
        if not candidates:
            raise ValueError("No existe reparto de K compatible con componentes y suelo poblacional")
        ideal = {key: k * populations[key] / total for key in keys}
        chosen = max(candidates, key=lambda key: (ideal[key] - q[key], populations[key] / (q[key] + 1), key))
        q[chosen] += 1
        freed -= 1

    exempt = sorted(key for key in keys if q[key] == 1 and populations[key] < floor - 1e-9)
    if sum(q.values()) != k:
        raise AssertionError("Reparto por componentes no conserva K")
    return q, exempt

def component_apportionment_audit(
    populations: dict[str, int],
    quota: dict[str, int],
    k: int,
    floor_ratio: float,
    floor_exempt: list[str],
    *,
    exception_policy: str | None,
) -> dict[str, dict[str, Any]]:
    """Explica el reparto DDD por componente sin atribuirlo a la norma electoral."""
    total = sum(populations.values())
    if total <= 0 or k <= 0:
        raise ValueError("Población/K inválidos para auditar reparto por componentes")
    target = total / k
    floor = target * floor_ratio
    exempt = set(floor_exempt)
    out: dict[str, dict[str, Any]] = {}
    for key in sorted(populations):
        districts = int(quota[key])
        population = int(populations[key])
        average = population / districts
        required = districts == 1 and population < floor - 1e-9
        governed = (not required) or (
            key in exempt and exception_policy == "one_contiguous_district_floor_exception"
        )
        if required and not governed:
            raise ValueError(
                f"{key}: excepción de suelo necesaria pero no gobernada por la política insular"
            )
        out[key] = {
            "population": population,
            "districts": districts,
            "target_population": round(target, 6),
            "average_population_per_district": round(average, 6),
            "relative_deviation_from_target": round((average - target) / target, 9),
            "population_floor": round(floor, 6),
            "floor_exception_required": required,
            "floor_exception_governed": governed,
        }
    return out



def existing_or_bootstrap(root: Path, territory_id: str, territory_name: str, province_codes: list[str], edition: str) -> tuple[dict[str, Any], Path]:
    path = root / "territorios" / territory_id / "config" / f"{territory_id}_{edition}.yaml"
    if path.is_file():
        return yload(path), path
    run_name = f"{territory_id}_{edition}"
    base = f"territorios/{territory_id}/.cache/ddd/preparacion/{{run_name}}"
    cfg = {
        "meta": {
            "procedure_name": "Diputado de Distrito", "territory_id": territory_id,
            "territory": territory_name, "run_name": run_name, "year": int(edition),
            "scope": "provincial", "schema_version": "1.0.0", "status": "generated_bootstrap",
        },
        "io": {
            "project_root": {"path": "../../.."},
            "input": {
                "seccionado": {"path": "inputs/seccionado_2025.zip", "layer": "", "section_key_col": "CUSEC"},
                "population_cip": {
                    "paths": ["inputs/65034.csv.zip"], "sep": "auto", "section_key_col": "Secciones",
                    "pop_col": "Total",
                    "filters": {"year_col": "Periodo", "sexo_col": "Sexo", "edad_col": "Edad",
                                "sexo_total_values": ["Total"], "edad_total_values": ["Todas las edades"]},
                },
            },
            "cache": {"dir": base},
        },
        "territory_contract": {
            "unit_id_role": "census_section", "admin_level_1_role": "province",
            "admin_level_2_role": "municipality", "province_codes": province_codes,
        },
        "modulos": {
            "modulo_01_preparar_base_territorial": {
                "province_codes": province_codes, "drop_missing_population": False,
                "out_geojson": base + f"/{run_name}_m01_secciones_poblacion.geojson.zip",
                "out_report": base + f"/{run_name}_m01_informe.json",
            },
            "modulo_02_construir_adyacencias": {
                "in_geojson": base + f"/{run_name}_m01_secciones_poblacion.geojson.zip",
                "id_field": "CUSEC_KEY", "out_edges_jsonl": base + f"/{run_name}_m02_adyacencias.jsonl",
                "predicate": "contact", "working_crs": "EPSG:3035", "min_shared_border_m": 1.0,
                "max_precision_overlap_area_m2": 1.0, "buffer_m": 0.0, "simplify_m": 0.0,
                "max_candidates": 0, "log_every": 10000, "topology_bridges": [],
            },
            "modulo_03_construir_grafo": {
                "in_geojson": base + f"/{run_name}_m01_secciones_poblacion.geojson.zip",
                "in_edges_jsonl": base + f"/{run_name}_m02_adyacencias.jsonl",
                "id_field": "CUSEC_KEY", "pop_field": "POP_{year}",
                "out_graph_json": base + f"/{run_name}_m03_grafo.json",
                "out_report": base + f"/{run_name}_m03_informe.json",
            },
        },
        "validation": {
            "expected_province_codes": province_codes, "require_unique_section_id": True,
            "require_non_null_population": True, "province_field": "CPRO",
            "municipality_field": "CUMUN", "municipality_name_field": "NMUN",
            "audit_graph_components": True, "audit_admin_level_1_components": True,
            "audit_admin_level_2_components": True, "require_one_graph_component_per_province": False,
            "require_connected_municipalities": False,
        },
    }
    return cfg, path


def materialize(root: Path, territory_id: str, edition: str, package: Path) -> dict[str, Any]:
    policy = yload(root / POLICY)
    master_path = root / MASTER
    master = yload(master_path)
    rows = [x for x in master.get("territories", []) if x.get("territory_id") == territory_id]
    if len(rows) != 1:
        raise ValueError(f"Territorio no único en catálogo maestro: {territory_id}")
    row = rows[0]
    pentry = (policy.get("territories") or {}).get(territory_id)
    if not pentry:
        raise ValueError(f"Sin política nacional de generación: {territory_id}")

    name = str(row["name"])
    provinces = [str(x).zfill(2) for x in row["province_codes"]]
    k = int(pentry["k"])
    defaults = policy["defaults"]
    section_pop = section_populations(package, edition, provinces)
    province_pop = {code: sum(v for sec, v in section_pop.items() if sec[:2] == code) for code in provinces}

    cfg, contract_path = existing_or_bootstrap(root, territory_id, name, provinces, edition)
    modules = cfg.setdefault("modulos", {})

    # Los contratos ya industrializados no se regeneran: se conservan sus
    # parámetros territoriales específicos y sólo se normaliza la autorización.
    already_complete = all(
        isinstance(modules.get(key), dict)
        for key in (
            "modulo_01_preparar_base_territorial", "modulo_02_construir_adyacencias",
            "modulo_03_construir_grafo", "modulo_04_generar_semillas",
            "modulo_05_optimizar_distritos", "modulo_06_consolidar_distritos",
        )
    ) and bool((cfg.get("territory_contract") or {}).get("k_districts"))
    if already_complete:
        current_k = int((cfg.get("territory_contract") or {})["k_districts"])
        if current_k != k:
            raise ValueError(f"K vigente {current_k} no coincide con política nacional {k}")
        cfg.setdefault("meta", {}).update({
            "schema_family": "ddd-territory", "contract_level": "production_m01_m06",
            "contract_schema_version": "1.0.0", "production_authorization": "AUTHORIZED",
        })
        row.update({
            "contract_level": "production_m01_m06", "production_authorization": "AUTHORIZED",
            "k_districts": current_k,
            "k_source": (cfg.get("territory_contract") or {}).get("k_source", pentry["k_source"]),
            "k_rationale": (cfg.get("territory_contract") or {}).get("k_rationale", pentry["rationale"]),
            "status": "generation_ready",
        })
        update_master_entry(
            master_path, territory_id, status="generation_ready", authorization="AUTHORIZED",
            k=current_k,
            k_source=(cfg.get("territory_contract") or {}).get("k_source", pentry["k_source"]),
            k_rationale=(cfg.get("territory_contract") or {}).get("k_rationale", pentry["rationale"]),
        )
        ywrite(contract_path, cfg)
        admitted = validate_production_contract(contract_path, expected_territory=territory_id)
        if admitted["status"] != "ADMITTED" or not admitted.get("production_authorized"):
            raise ValueError("Contrato existente no admitido: " + "; ".join(admitted.get("errors") or []))
        return {
            "schema": "ddd-generation-contract-materialization/1.0",
            "territory_id": territory_id, "edition": edition,
            "contract_path": str(contract_path.relative_to(root)),
            "k": current_k, "partition_mode": "existing_contract",
            "partition_districts": (cfg.get("validation") or {}).get("province_districts") or {},
            "population_floor_exempt_partitions": (cfg.get("validation") or {}).get("population_floor_exempt_partitions") or [],
            "contract_sha256": admitted["contract_sha256"], "status": "READY",
            "preserved_existing_contract": True,
        }
    val = cfg.setdefault("validation", {})
    meta = cfg.setdefault("meta", {})
    contract = cfg.setdefault("territory_contract", {})
    io_cfg = cfg.setdefault("io", {})
    io_cfg.setdefault("runs", {"dir": f"territorios/{territory_id}/resultados/ejecuciones/{{run_id}}"})

    meta.update({
        "procedure_name": "Diputado de Distrito", "territory_id": territory_id, "territory": name,
        "run_name": f"{territory_id}_{edition}", "year": int(edition), "schema_family": "ddd-territory",
        "contract_level": "production_m01_m06", "contract_schema_version": "1.0.0",
        "production_authorization": "AUTHORIZED", "status": "production_ready_auto_materialized",
    })
    meta.setdefault("schema_version", "1.0.0")
    meta.setdefault("scope", "provincial")

    partition_mode = str(pentry.get("partition_mode") or "province_hamilton")
    partition_field = "CPRO"
    municipality_field = "CUMUN"
    partition_lookup = None
    source_geo = modules["modulo_01_preparar_base_territorial"]["out_geojson"]
    quota: dict[str, int]
    floor_exempt: list[str] = []
    partition_audit: dict[str, dict[str, Any]] = {}

    if partition_mode == "physical_components_hamilton":
        pdata = json.loads((root / PARTITIONS).read_text(encoding="utf-8"))
        territory_partitions = (pdata.get("territories") or {}).get(territory_id)
        if not territory_partitions:
            raise ValueError(f"Sin particiones físicas declaradas: {territory_id}")
        mun_map = territory_partitions.get("municipality_to_partition") or {}
        sec_overrides = territory_partitions.get("section_overrides") or {}
        component_pop: dict[str, int] = {key: 0 for key in (territory_partitions.get("components") or {})}
        missing = []
        for sec, pop in section_pop.items():
            partition = sec_overrides.get(sec) or mun_map.get(sec[:5])
            if not partition:
                missing.append(sec)
            else:
                component_pop.setdefault(partition, 0)
                component_pop[partition] += pop
        if missing:
            raise ValueError(f"Partición insular incompleta: {len(missing)} secciones; ejemplo={missing[:5]}")
        quota, floor_exempt = component_hamilton(component_pop, k, float(defaults["population_floor_ratio"]))
        partition_audit = component_apportionment_audit(
            component_pop,
            quota,
            k,
            float(defaults["population_floor_ratio"]),
            floor_exempt,
            exception_policy=(policy.get("archipelago") or {}).get("small_component_policy"),
        )
        partition_field = "DDD_PARTITION"
        municipality_field = "DDD_MUNICIPALITY_PARTITION"
        partition_lookup = str(PARTITIONS)
        val["partition_populations"] = component_pop
    else:
        quota = hamilton(province_pop, k)

    contract.update({
        "unit_id_role": "census_section", "admin_level_1_role": "province",
        "admin_level_2_role": "municipality", "province_codes": provinces,
        "k_districts": k, "k_source": pentry["k_source"], "k_rationale": pentry["rationale"],
        "k_reference_scope": pentry.get("k_reference_scope", "institutional_or_contractual_reference"),
        "k_reference_source": pentry.get("k_reference_source"),
        "apportionment_source": pentry.get("apportionment_source", "ddd_design_policy"),
        "legal_apportionment_reused": bool(pentry.get("legal_apportionment_reused", False)),
        "legal_apportionment_context": pentry.get("legal_context"),
        "district_apportionment": "hamilton_components" if partition_mode == "physical_components_hamilton" else "hamilton",
        "population_floor_ratio": float(defaults["population_floor_ratio"]),
        "population_cap_ratio": float(defaults["population_cap_ratio"]),
        "target_tolerance_ratio": float(defaults["target_tolerance_ratio"]),
        "limits_profile": "standard-1.0.0",
        "require_graph_contiguity": True, "require_single_admin_level_1_per_district": True,
        "require_municipality_discipline": True,
        "oversized_municipality_rule": defaults["oversized_municipality_rule"],
        "municipality_atomicity_limit_ratio": float(defaults["municipality_atomicity_limit_ratio"]),
        "require_auditable_district_catalogue": True,
    })
    if floor_exempt:
        contract["population_floor_exempt_partitions"] = floor_exempt
        contract["small_component_exception_policy"] = policy["archipelago"]["small_component_policy"]

    base = f"territorios/{territory_id}/.cache/ddd/preparacion/{{run_name}}"
    run_name = f"{territory_id}_{edition}"
    m04_in = source_geo
    if partition_lookup:
        m04_in = base + f"/{run_name}_m03_particiones.geojson.zip"

    modules["modulo_04_generar_semillas"] = {
        "in_graph_json": modules["modulo_03_construir_grafo"]["out_graph_json"],
        "in_geojson": m04_in,
        "id_field": "CUSEC_KEY", "pop_field": "POP_{year}",
        "province_field": partition_field, "municipality_field": municipality_field,
        "municipality_name_field": "NMUN",
        "district_apportionment": contract["district_apportionment"], "k_districts": k,
        "municipality_atomicity_limit_ratio": float(defaults["municipality_atomicity_limit_ratio"]),
        "preserve_province_residual_feasibility": True, "seed": 12345,
        "out_geojson": base + f"/{run_name}_m04_semillas.geojson.zip",
        "out_report": base + f"/{run_name}_m04_informe.json",
    }
    if partition_lookup:
        modules["modulo_04_generar_semillas"].update({
            "source_geojson": source_geo,
            "hard_partition_lookup": partition_lookup,
            "hard_partition_territory_id": territory_id,
        })

    modules["modulo_05_optimizar_distritos"] = {
        "in_graph_json": modules["modulo_03_construir_grafo"]["out_graph_json"],
        "in_geojson": modules["modulo_04_generar_semillas"]["out_geojson"],
        "id_field": "CUSEC_KEY", "pop_field": "POP_{year}", "district_field": "district_id",
        "province_field": partition_field, "municipality_field": municipality_field,
        "greedy_moves_limit": 1000, "anneal_iters": 20000, "seed": 12345,
        "anneal_seed_offset": 0, "anneal_outside_penalty": 0.01,
        "anneal_maxdev_weight": 0.05, "anneal_churn_weight": 0.0016,
        "anneal_temp_start": 0.02, "anneal_temp_end": 0.0005,
        "swap_polish_max": 0,
        "out_geojson": base + f"/{run_name}_m05_distritos_optimizados.geojson.zip",
        "out_report": base + f"/{run_name}_m05_informe.json",
    }
    modules["modulo_06_consolidar_distritos"] = {
        "in_geojson": modules["modulo_05_optimizar_distritos"]["out_geojson"],
        "id_field": "CUSEC_KEY", "district_field": "district_id", "pop_field": "POP_{year}",
        "province_field": partition_field, "province_name_field": "NPRO",
        "municipality_field": municipality_field, "municipality_name_field": "NMUN",
        "cudis_field": "CUDIS", "metric_crs": "EPSG:3035", "expected_districts": k,
        "strict_expected_k": True,
        "out_summary_csv": base + f"/{run_name}_m06_resumen_distritos.csv",
        "out_catalog_csv": base + f"/{run_name}_m06_catalogo_distritos.csv",
        "out_composition_csv": base + f"/{run_name}_m06_composicion_distritos.csv",
        "out_geojson": base + f"/{run_name}_m06_secciones.geojson.zip",
        "out_district_geojson": base + f"/{run_name}_m06_distritos.geojson.zip",
    }

    val.update({
        "expected_province_codes": provinces, "expected_districts": k,
        "population_floor_ratio": float(defaults["population_floor_ratio"]),
        "population_cap_ratio": float(defaults["population_cap_ratio"]),
        "target_tolerance_ratio": float(defaults["target_tolerance_ratio"]),
        "province_apportionment": contract["district_apportionment"],
        "province_districts": quota,
        "require_unique_section_id": True, "require_non_null_population": True,
        "require_graph_contiguity": True,
        "require_single_province_per_district": True,
        "require_municipality_discipline": True,
        "province_field": partition_field, "municipality_field": municipality_field,
        "municipality_name_field": "NMUN",
        "municipality_atomicity_limit_ratio": float(defaults["municipality_atomicity_limit_ratio"]),
        "max_mixed_districts_per_split_municipality": 1,
        "require_m06_population_conservation": True,
        "require_m06_assignment_identity_with_m05": True,
        "population_floor_exempt_partitions": floor_exempt,
        "partition_apportionment_audit": partition_audit,
    })
    if partition_mode == "physical_components_hamilton":
        val.update({
            "require_one_graph_component_per_province": False,
            "require_connected_municipalities": False,
            "hard_partition_mode": "physical_components",
            "hard_partition_lookup": str(PARTITIONS),
        })

    # El maestro y el contrato deben coincidir antes de atravesar la puerta R036.
    row.update({
        "contract_level": "production_m01_m06", "production_authorization": "AUTHORIZED",
        "k_districts": k, "k_source": pentry["k_source"], "k_rationale": pentry["rationale"],
        "status": "production_ready_auto_materialized",
    })
    update_master_entry(
        master_path, territory_id, status="generation_ready", authorization="AUTHORIZED",
        k=k, k_source=pentry["k_source"], k_rationale=pentry["rationale"],
    )
    ywrite(contract_path, cfg)

    report = validate_production_contract(contract_path, expected_territory=territory_id)
    if report["status"] != "ADMITTED" or not report.get("production_authorized"):
        raise ValueError("Contrato auto-materializado rechazado: " + "; ".join(report.get("errors") or []))
    return {
        "schema": "ddd-generation-contract-materialization/1.0",
        "territory_id": territory_id, "edition": edition,
        "contract_path": str(contract_path.relative_to(root)),
        "k": k, "partition_mode": partition_mode,
        "k_reference_scope": pentry.get("k_reference_scope", "institutional_or_contractual_reference"),
        "apportionment_source": pentry.get("apportionment_source", "ddd_design_policy"),
        "legal_apportionment_reused": bool(pentry.get("legal_apportionment_reused", False)),
        "legal_apportionment_context": pentry.get("legal_context"),
        "partition_districts": quota,
        "partition_apportionment_audit": partition_audit,
        "population_floor_exempt_partitions": floor_exempt,
        "contract_sha256": report["contract_sha256"], "status": "READY",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", default=".")
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    root = Path(args.root_dir).resolve()
    result = materialize(root, args.territory_id, str(args.edition), Path(args.package).resolve())
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
