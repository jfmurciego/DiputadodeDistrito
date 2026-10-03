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
from herramientas.compatibilidad_poblacion_seccionado import validate_compatibility_package

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

def _source_by_role(source_inputs: list[dict[str, Any]], role: str) -> dict[str, Any]:
    matches = [row for row in source_inputs if str(row.get("role") or "") == role]
    if len(matches) != 1:
        raise ValueError(f"Contrato de fuentes requiere exactamente un role={role}: {len(matches)}")
    return matches[0]


def _prepared_source_bytes(package: Path, source: dict[str, Any]) -> bytes:
    path = str(source.get("path") or "").strip()
    if not path:
        raise ValueError("Fuente preparada sin path")
    direct = [p for p in package.rglob(Path(path).name) if p.is_file()]
    exact = [p for p in direct if p.as_posix().endswith(path)]
    if len(exact) == 1:
        return exact[0].read_bytes()
    bundle = package / "prepared_sources.zip"
    if not bundle.is_file():
        raise FileNotFoundError(f"No se localiza {path!r} ni prepared_sources.zip en {package}")
    with zipfile.ZipFile(bundle) as archive:
        preferred = f"materialized/{path}"
        if preferred in archive.namelist():
            return archive.read(preferred)
        candidates = [
            name for name in archive.namelist()
            if name == path or name.endswith("/" + path)
        ]
        if len(candidates) != 1:
            raise ValueError(f"Paquete territorial ambiguo para {path!r}: {candidates}")
        return archive.read(candidates[0])


def _legacy_open_population_zip(package: Path) -> zipfile.ZipFile:
    """Puente explícito para paquetes previos al contrato físico resuelto."""
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


def _legacy_section_populations(package: Path, edition: str, province_codes: list[str]) -> dict[str, int]:
    wanted = {str(x).zfill(2) for x in province_codes}
    result: dict[str, int] = {}
    with _legacy_open_population_zip(package) as z:
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
                raw_total = str(row.get("Total") or "").strip()
                if raw_total == "":
                    raise ValueError(f"Población ausente para sección {sec}")
                if sec in result:
                    raise ValueError(f"Clave poblacional duplicada antes de sobrescribir: {sec}")
                result[sec] = int(raw_total.replace(".", "").replace(",", ""))
    if not result:
        raise ValueError("La fuente de población preparada no contiene secciones para el territorio")
    return result


def section_populations(
    package: Path,
    source_inputs: list[dict[str, Any]],
    population_year: str,
    province_codes: list[str],
) -> dict[str, int]:
    population_source = _source_by_role(source_inputs, "population")
    contract = population_source.get("consumer_contract")
    if not isinstance(contract, dict):
        return _legacy_section_populations(package, population_year, province_codes)

    if contract.get("schema") != "ddd.resolved-source-binding/1.0":
        raise ValueError("Contrato físico de población con schema no soportado")
    if str(contract.get("materialized_format") or "") != "csv":
        raise ValueError(
            "Formato poblacional aún no soportado por el adaptador: "
            + str(contract.get("materialized_format") or contract.get("source_format") or "")
        )
    fields = contract.get("fields") or {}
    filters = contract.get("filters") or {}
    section_col = str(fields.get("section_id") or "")
    population_col = str(fields.get("population") or "")
    year_col = str(fields.get("year") or "")
    sex_col = str(fields.get("sex") or "")
    age_col = str(fields.get("age") or "")
    if not section_col or not population_col:
        raise ValueError("Contrato físico de población sin section_id/population")

    payload = _prepared_source_bytes(package, population_source)
    if str(contract.get("container") or "") == "zip":
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            member = str(contract.get("archive_member") or "")
            if member and member in archive.namelist():
                raw_payload = archive.read(member)
            else:
                candidates = [
                    name for name in archive.namelist()
                    if not name.endswith("/") and name.lower().endswith((".csv", ".tsv", ".txt"))
                ]
                if len(candidates) != 1:
                    raise ValueError(f"Contrato poblacional ambiguo: archive_member={member!r}, candidatos={candidates}")
                raw_payload = archive.read(candidates[0])
    else:
        raw_payload = payload

    encoding = str(contract.get("encoding") or "utf-8-sig")
    text = raw_payload.decode(encoding)
    delimiter = str(contract.get("delimiter") or "auto")
    if delimiter == "auto":
        first = text.splitlines()[0] if text.splitlines() else ""
        delimiter = max(("\t", ";", ","), key=first.count)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("Fuente poblacional sin cabecera")
    required = {section_col, population_col}
    required.update(x for x in (year_col, sex_col, age_col) if x)
    missing = sorted(required - set(reader.fieldnames))
    if missing:
        raise ValueError(f"Contrato poblacional refiere columnas ausentes: {missing}")

    wanted = {str(x).zfill(2) for x in province_codes}
    result: dict[str, int] = {}
    for row in reader:
        if year_col and str(row.get(year_col) or "").strip() != str(filters.get("year_value", population_year)):
            continue
        if sex_col and str(row.get(sex_col) or "").strip() not in {
            str(x) for x in (filters.get("sex_total_values") or [])
        }:
            continue
        if age_col and str(row.get(age_col) or "").strip() not in {
            str(x) for x in (filters.get("age_total_values") or [])
        }:
            continue
        sec = str(row.get(section_col) or "").split(" ", 1)[0].strip()
        if len(sec) != 10 or sec[:2] not in wanted:
            continue
        raw_total = str(row.get(population_col) or "").strip()
        if raw_total == "":
            raise ValueError(f"Población ausente para sección {sec}")
        if sec in result:
            raise ValueError(f"Clave poblacional duplicada antes de sobrescribir: {sec}")
        result[sec] = int(raw_total.replace(".", "").replace(",", ""))
    if not result:
        raise ValueError("La fuente de población preparada no contiene secciones para el territorio")
    return result


def source_baseline(
    package: Path,
    *,
    territory_id: str,
    edition: str,
    population_year: int,
    section_year: int,
) -> dict[str, Any]:
    report, report_sha256, reasons = validate_compatibility_package(
        package,
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
        require_ready=True,
    )
    if reasons:
        raise ValueError("Paquete sin compatibilidad acreditada: " + "; ".join(reasons))
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    baseline = report.get("baseline") or {}
    population_total = baseline.get("population_total")
    section_count = baseline.get("target_section_count")
    identity = str(report.get("compatibility_identity_sha256") or "")
    package_sha256 = str(manifest.get("sha256") or "")
    if (
        not isinstance(population_total, int)
        or isinstance(population_total, bool)
        or population_total < 0
        or not isinstance(section_count, int)
        or isinstance(section_count, bool)
        or section_count <= 0
        or len(identity) != 64
        or len(package_sha256) != 64
    ):
        raise ValueError("Baseline de fuente incompleto o inválido")
    return {
        "schema": "ddd.source-baseline/1.0",
        "edition": str(edition),
        "population_year": int(population_year),
        "section_year": int(section_year),
        "population_total": int(population_total),
        "target_section_count": int(section_count),
        "package_sha256": package_sha256,
        "compatibility_report_sha256": report_sha256,
        "compatibility_identity_sha256": identity,
    }


def source_input_manifest(package: Path) -> list[dict[str, Any]]:
    bundle = package / "prepared_sources.zip"
    if not bundle.is_file():
        raise ValueError("Paquete territorial sin prepared_sources.zip")
    try:
        with zipfile.ZipFile(bundle) as archive:
            inventory = json.loads(archive.read("inventario_fuentes.json"))
    except (KeyError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise ValueError("Paquete territorial sin inventario de fuentes válido") from exc

    sources = inventory.get("sources") or []
    if not isinstance(sources, list) or not sources:
        raise ValueError("Inventario territorial sin fuentes")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Entrada de inventario territorial inválida")
        path = str(source.get("path") or "").strip()
        digest = str(source.get("sha256") or "").strip().lower()
        role = str(source.get("role") or "").strip()
        source_id = str(source.get("source_id") or "").strip()
        if not path.startswith("inputs/"):
            raise ValueError(f"Ruta de fuente territorial no contractual: {path!r}")
        if path in seen:
            raise ValueError(f"Ruta de fuente territorial duplicada: {path}")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"SHA-256 territorial inválido para {path}")
        seen.add(path)
        consumer_contract = source.get("consumer_contract")
        if consumer_contract is not None:
            if not isinstance(consumer_contract, dict):
                raise ValueError(f"consumer_contract inválido para {source_id or path}")
            if consumer_contract.get("schema") != "ddd.resolved-source-binding/1.0":
                raise ValueError(f"consumer_contract con schema no soportado para {source_id or path}")
            for key, expected in (
                ("path", path),
                ("role", role),
                ("source_id", source_id),
            ):
                observed = str(consumer_contract.get(key) or "")
                if observed != expected:
                    raise ValueError(
                        f"consumer_contract inconsistente {key}: {observed!r} != {expected!r}"
                    )
        out.append({
            "path": path,
            "sha256": digest,
            "role": role,
            "source_id": source_id,
            "consumer_contract": copy.deepcopy(consumer_contract) if consumer_contract is not None else None,
        })
    return out


def _apply_source_contract(
    cfg: dict[str, Any],
    *,
    population_year: int,
    section_year: int,
    baseline: dict[str, Any],
    source_inputs: list[dict[str, Any]],
) -> None:
    meta = cfg.setdefault("meta", {})
    meta["source_population_year"] = int(population_year)
    meta["source_section_year"] = int(section_year)
    meta["status"] = "source_prepared_pending_pre_m04"

    io_cfg = cfg.setdefault("io", {}).setdefault("input", {})
    population_source = _source_by_role(source_inputs, "population")
    section_source = _source_by_role(source_inputs, "target_sectioning")
    population_contract = population_source.get("consumer_contract")
    section_contract = section_source.get("consumer_contract")

    if isinstance(section_contract, dict):
        section_fields = section_contract.get("fields") or {}
        seccionado_cfg = io_cfg.setdefault("seccionado", {})
        seccionado_cfg["path"] = str(section_contract["path"])
        seccionado_cfg["layer"] = str(section_contract.get("layer") or "")
        if section_fields.get("section_id"):
            seccionado_cfg["section_key_col"] = str(section_fields["section_id"])
    else:
        # Compatibilidad sólo para paquetes durables creados antes de este contrato.
        io_cfg.setdefault("seccionado", {})["path"] = f"inputs/seccionado_{section_year}.zip"

    population_cfg = io_cfg.setdefault("population_cip", {})
    if isinstance(population_contract, dict):
        population_fields = population_contract.get("fields") or {}
        population_filters = population_contract.get("filters") or {}
        population_cfg["paths"] = [str(population_contract["path"])]
        population_cfg["sep"] = str(population_contract.get("delimiter") or "auto")
        population_cfg["section_key_col"] = str(population_fields.get("section_id") or "")
        population_cfg["pop_col"] = str(population_fields.get("population") or "")
        filters_cfg = population_cfg.setdefault("filters", {})
        mapping = {
            "year_col": "year",
            "sexo_col": "sex",
            "edad_col": "age",
        }
        for target, semantic in mapping.items():
            value = str(population_fields.get(semantic) or "")
            if value:
                filters_cfg[target] = value
        filters_cfg["year_value"] = population_filters.get("year_value", int(population_year))
        if "sex_total_values" in population_filters:
            filters_cfg["sexo_total_values"] = list(population_filters["sex_total_values"])
        if "age_total_values" in population_filters:
            filters_cfg["edad_total_values"] = list(population_filters["age_total_values"])
    else:
        population_cfg.setdefault("filters", {})["year_value"] = int(population_year)

    runtime_bindings = {
        "section_id_field": "CUSEC_KEY",
        "population_field": f"POP_{int(population_year)}",
    }
    cfg["resolved_source_contract"] = {
        "schema": "ddd.resolved-source-contract/1.0",
        "population_year": int(population_year),
        "section_year": int(section_year),
        "inputs": {
            "population": copy.deepcopy(population_contract),
            "target_sectioning": copy.deepcopy(section_contract),
        },
        "runtime": runtime_bindings,
    }

    modules = cfg.setdefault("modulos", {})
    for name in (
        "modulo_03_construir_grafo",
        "modulo_04_generar_semillas",
        "modulo_05_optimizar_distritos",
        "modulo_06_consolidar_distritos",
    ):
        module = modules.get(name)
        if isinstance(module, dict):
            module["pop_field"] = "POP_{population_year}"
    electoral = modules.get("modulo_07_agregar_resultados_electorales")
    if isinstance(electoral, dict) and electoral.get("population_field"):
        electoral["population_field"] = "POP_{population_year}"
    partitioning = cfg.get("partitioning")
    if isinstance(partitioning, dict) and partitioning.get("population_field"):
        partitioning["population_field"] = "POP_{population_year}"

    validation = cfg.setdefault("validation", {})
    validation["source_baseline"] = copy.deepcopy(baseline)
    state = cfg.setdefault("generation_state", {})
    state.update({
        "source_prepared": True,
        "generation_enabled": False,
        "package_sha256": baseline["package_sha256"],
        "compatibility_identity_sha256": baseline["compatibility_identity_sha256"],
        "source_inputs": copy.deepcopy(source_inputs),
    })
    territory_contract = cfg.setdefault("territory_contract", {})
    territory_contract["status"] = "source_prepared_pending_pre_m04"


def _component_populations(root: Path, territory_id: str, section_pop: dict[str, int]) -> dict[str, int]:
    pdata = json.loads((root / PARTITIONS).read_text(encoding="utf-8"))
    territory = (pdata.get("territories") or {}).get(territory_id)
    if not territory:
        raise ValueError(f"Sin particiones físicas declaradas: {territory_id}")
    mun_map = territory.get("municipality_to_partition") or {}
    overrides = territory.get("section_overrides") or {}
    populations = {str(key): 0 for key in (territory.get("components") or {})}
    missing: list[str] = []
    for section, population in section_pop.items():
        component = overrides.get(section) or mun_map.get(section[:5])
        if not component:
            missing.append(section)
            continue
        populations.setdefault(str(component), 0)
        populations[str(component)] += int(population)
    if missing:
        raise ValueError(
            f"Partición insular incompleta para la fuente acreditada: {len(missing)} secciones; ejemplo={missing[:5]}"
        )
    return populations


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



def existing_or_bootstrap(
    root: Path,
    territory_id: str,
    territory_name: str,
    province_codes: list[str],
    edition: str,
    section_year: str | None = None,
) -> tuple[dict[str, Any], Path]:
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
                "seccionado": {"path": f"inputs/seccionado_{section_year or edition}.zip", "layer": "", "section_key_col": "CUSEC"},
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
                "id_field": "CUSEC_KEY", "pop_field": "POP_{population_year}",
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


def materialize(
    root: Path,
    territory_id: str,
    edition: str,
    package: Path,
    source_year: str | None = None,
    population_year: str | None = None,
    section_year: str | None = None,
) -> dict[str, Any]:
    legacy_year = str(source_year) if source_year not in (None, "") else None
    if population_year in (None, ""):
        population_year = legacy_year
    if section_year in (None, ""):
        section_year = legacy_year
    if population_year in (None, "") or section_year in (None, ""):
        raise ValueError("population_year y section_year son obligatorios; la edición no es un fallback temporal")
    population_year = str(population_year)
    section_year = str(section_year)
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
    source_inputs = source_input_manifest(package)
    section_pop = section_populations(package, source_inputs, population_year, provinces)
    baseline = source_baseline(
        package,
        territory_id=territory_id,
        edition=str(edition),
        population_year=int(population_year),
        section_year=int(section_year),
    )
    required_roles = {"population", "target_sectioning"}
    declared_roles = {str(item.get("role") or "") for item in source_inputs}
    if not required_roles.issubset(declared_roles):
        missing = sorted(required_roles - declared_roles)
        raise ValueError("Inventario territorial no cubre roles contractuales: " + ", ".join(missing))
    province_pop = {code: sum(v for sec, v in section_pop.items() if sec[:2] == code) for code in provinces}
    if sum(section_pop.values()) != baseline["population_total"]:
        raise ValueError("La suma poblacional usada por el contrato contradice el baseline acreditado")

    cfg, contract_path = existing_or_bootstrap(root, territory_id, name, provinces, edition, section_year)
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
        cfg.setdefault("meta", {})["year"] = int(edition)
        _apply_source_contract(
            cfg,
            population_year=int(population_year),
            section_year=int(section_year),
            baseline=baseline,
            source_inputs=source_inputs,
        )
        current_k = int((cfg.get("territory_contract") or {})["k_districts"])
        if current_k != k:
            raise ValueError(f"K vigente {current_k} no coincide con política nacional {k}")
        cfg.setdefault("meta", {}).update({
            "schema_family": "ddd-territory", "contract_level": "production_m01_m06",
            "contract_schema_version": "1.0.0", "production_authorization": "AUTHORIZED",
            "status": "source_prepared_pending_pre_m04",
        })
        if str(pentry.get("partition_mode") or "") == "physical_components_hamilton":
            component_pop = _component_populations(root, territory_id, section_pop)
            floor_ratio = float(defaults["population_floor_ratio"])
            quota, floor_exempt = component_hamilton(component_pop, current_k, floor_ratio)
            cfg.setdefault("validation", {})["partition_populations"] = component_pop
            cfg["validation"]["province_districts"] = quota
            cfg["validation"]["population_floor_exempt_partitions"] = floor_exempt
            cfg["validation"]["partition_apportionment_audit"] = component_apportionment_audit(
                component_pop,
                quota,
                current_k,
                floor_ratio,
                floor_exempt,
                exception_policy=(policy.get("archipelago") or {}).get("small_component_policy"),
            )
        row.update({
            "contract_level": "production_m01_m06", "production_authorization": "AUTHORIZED",
            "k_districts": current_k,
            "k_source": (cfg.get("territory_contract") or {}).get("k_source", pentry["k_source"]),
            "k_rationale": (cfg.get("territory_contract") or {}).get("k_rationale", pentry["rationale"]),
            "status": "source_prepared_pending_pre_m04",
        })
        update_master_entry(
            master_path, territory_id, status="source_prepared_pending_pre_m04", authorization="AUTHORIZED",
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
            "territory_id": territory_id,
            "edition": edition,
            "population_year": population_year,
            "section_year": section_year,
            "contract_path": str(contract_path.relative_to(root)),
            "k": current_k, "partition_mode": "existing_contract",
            "partition_districts": (cfg.get("validation") or {}).get("province_districts") or {},
            "population_floor_exempt_partitions": (cfg.get("validation") or {}).get("population_floor_exempt_partitions") or [],
            "contract_sha256": admitted["contract_sha256"],
            "source_baseline": baseline,
            "generation_enabled": False,
            "status": "SOURCE_PREPARED_PENDING_PRE_M04",
            "preserved_existing_contract": True,
        }
    val = cfg.setdefault("validation", {})
    meta = cfg.setdefault("meta", {})
    contract = cfg.setdefault("territory_contract", {})
    io_cfg = cfg.setdefault("io", {})
    io_cfg.setdefault("runs", {"dir": f"territorios/{territory_id}/resultados/ejecuciones/{{run_id}}"})

    meta.update({
        "procedure_name": "Diputado de Distrito", "territory_id": territory_id, "territory": name,
        "run_name": f"{territory_id}_{edition}",
        "year": int(edition),
        "source_population_year": int(population_year),
        "source_section_year": int(section_year),
        "schema_family": "ddd-territory",
        "contract_level": "production_m01_m06", "contract_schema_version": "1.0.0",
        "production_authorization": "AUTHORIZED", "status": "source_prepared_pending_pre_m04",
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
        component_pop = _component_populations(root, territory_id, section_pop)
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

    if partition_mode == "physical_components_hamilton":
        modules["modulo_02_construir_adyacencias"].update({
            "bridge_admin_level_1_field": "CPRO",
            "bridge_admin_level_2_field": "CUMUN",
        })

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
        "id_field": "CUSEC_KEY", "pop_field": "POP_{population_year}",
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
        "id_field": "CUSEC_KEY", "pop_field": "POP_{population_year}", "district_field": "district_id",
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
        "id_field": "CUSEC_KEY", "district_field": "district_id", "pop_field": "POP_{population_year}",
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

    _apply_source_contract(
        cfg,
        population_year=int(population_year),
        section_year=int(section_year),
        baseline=baseline,
        source_inputs=source_inputs,
    )

    # La fuente preparada no habilita generación: la puerta pre-M04 lo hará después.
    row.update({
        "contract_level": "production_m01_m06", "production_authorization": "AUTHORIZED",
        "k_districts": k, "k_source": pentry["k_source"], "k_rationale": pentry["rationale"],
        "status": "source_prepared_pending_pre_m04",
    })
    update_master_entry(
        master_path, territory_id, status="source_prepared_pending_pre_m04", authorization="AUTHORIZED",
        k=k, k_source=pentry["k_source"], k_rationale=pentry["rationale"],
    )
    ywrite(contract_path, cfg)

    report = validate_production_contract(contract_path, expected_territory=territory_id)
    if report["status"] != "ADMITTED" or not report.get("production_authorized"):
        raise ValueError("Contrato auto-materializado rechazado: " + "; ".join(report.get("errors") or []))
    return {
        "schema": "ddd-generation-contract-materialization/1.0",
        "territory_id": territory_id,
        "edition": edition,
        "population_year": population_year,
        "section_year": section_year,
        "contract_path": str(contract_path.relative_to(root)),
        "k": k, "partition_mode": partition_mode,
        "k_reference_scope": pentry.get("k_reference_scope", "institutional_or_contractual_reference"),
        "apportionment_source": pentry.get("apportionment_source", "ddd_design_policy"),
        "legal_apportionment_reused": bool(pentry.get("legal_apportionment_reused", False)),
        "legal_apportionment_context": pentry.get("legal_context"),
        "partition_districts": quota,
        "partition_apportionment_audit": partition_audit,
        "population_floor_exempt_partitions": floor_exempt,
        "source_baseline": baseline,
        "contract_sha256": report["contract_sha256"],
        "generation_enabled": False,
        "status": "SOURCE_PREPARED_PENDING_PRE_M04",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", default=".")
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--source-year")
    ap.add_argument("--population-year")
    ap.add_argument("--section-year")
    ap.add_argument("--output")
    args = ap.parse_args()
    root = Path(args.root_dir).resolve()
    result = materialize(
        root,
        args.territory_id,
        str(args.edition),
        Path(args.package).resolve(),
        args.source_year,
        args.population_year,
        args.section_year,
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
