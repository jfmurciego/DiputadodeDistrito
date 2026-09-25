from __future__ import annotations

from herramientas import _resolver_ejecucion_completa_core as _core
from herramientas._resolver_ejecucion_completa_core import *  # noqa: F401,F403

# Compatibilidad de API interna usada por la regresión del planificador.
_run_from_artifact = _core._run_from_artifact


def _generation_capabilities(contract: dict) -> dict:
    meta = contract.get("meta") or {}
    territorial = contract.get("territory_contract") or {}
    modules = contract.get("modulos") or {}
    validation = contract.get("validation") or {}
    partitioning = contract.get("partitioning") or {}
    m01 = modules.get("modulo_01_preparar_base_territorial") or {}
    m02 = modules.get("modulo_02_construir_adyacencias") or {}
    m03 = modules.get("modulo_03_construir_grafo") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    m05 = modules.get("modulo_05_optimizar_distritos") or {}
    m06 = modules.get("modulo_06_consolidar_distritos") or {}

    if meta.get("contract_level") != "production_m01_m06" or not all((m01, m02, m03, m04, m05, m06)):
        return _core._blocked("CAP_CONTRACT", "contrato M01-M06 ausente o incompleto")
    if meta.get("production_authorization") != "AUTHORIZED":
        return _core._blocked("CAP_CONTRACT", "producción no autorizada por el contrato efectivo")
    k = territorial.get("k_districts")
    if (not isinstance(k, int) or isinstance(k, bool) or k <= 0
            or m04.get("k_districts") != k or m06.get("expected_districts") != k):
        return _core._blocked("CAP_K", "K ausente o incoherente entre contrato, Formación inicial y Consolidación")
    limits = (
        territorial.get("population_floor_ratio"),
        territorial.get("population_cap_ratio"),
        territorial.get("target_tolerance_ratio"),
    )
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0 for v in limits):
        return _core._blocked("CAP_POPULATION_LIMITS", "suelo, techo o tolerancia poblacional ausentes o inválidos")

    municipality_field = validation.get("municipality_field")
    admin_policy_ok = validation.get("require_municipality_discipline") is True and bool(municipality_field)
    if partitioning.get("enabled") is True:
        partition_field = partitioning.get("partition_unit_field")
        downstream_field = m05.get("municipality_field")
        admin_policy_ok = (
            admin_policy_ok
            and partitioning.get("municipality_field") == municipality_field
            and bool(partition_field)
            and m04.get("municipality_field") == partition_field
            and downstream_field in {municipality_field, partition_field}
            and m06.get("municipality_field") == downstream_field
        )
    else:
        admin_policy_ok = (
            admin_policy_ok
            and m04.get("municipality_field") == municipality_field
            and m05.get("municipality_field") == municipality_field
            and m06.get("municipality_field") == municipality_field
        )
    if not admin_policy_ok:
        return _core._blocked("CAP_ADMIN_POLICY", "disciplina o campo administrativo de trabajo incompletos o incoherentes")

    graph = m03.get("out_graph_json")
    if (not graph or graph != m04.get("in_graph_json") or graph != m05.get("in_graph_json")
            or validation.get("require_graph_contiguity") is not True):
        return _core._blocked("CAP_GRAPH", "grafo contractual o control de contigüidad incompletos")
    if partitioning.get("enabled") is True:
        if (partitioning.get("strategy") != "connected_internal_units"
                or not partitioning.get("output_geojson")
                or partitioning.get("output_geojson") != m04.get("in_geojson")
                or partitioning.get("partition_unit_field") != m04.get("municipality_field")):
            return _core._blocked("CAP_M04_INPUT", "particionado interno no enlaza con Formación inicial")
    elif not m01.get("out_geojson") or m01.get("out_geojson") != m04.get("in_geojson"):
        return _core._blocked("CAP_M04_INPUT", "entrada de Formación inicial no es resoluble desde la base territorial")
    if (not m04.get("out_geojson") or m04.get("out_geojson") != m05.get("in_geojson")
            or not m05.get("out_geojson") or m05.get("out_geojson") != m06.get("in_geojson")):
        return _core._blocked("CAP_GENERATION_CHAIN", "Formación inicial, Optimización y Consolidación no están enlazadas")
    return {"allowed": True}


_core._generation_capabilities = _generation_capabilities


if __name__ == "__main__":
    _core.main()
