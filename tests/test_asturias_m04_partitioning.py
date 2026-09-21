from pathlib import Path

import yaml

from herramientas.preparar_unidades_internas import build_command

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "territorios/principado_de_asturias/config/principado_de_asturias_2025.yaml"


def test_asturias_declares_internal_units_before_m04():
    cfg = yaml.safe_load(PARAMS.read_text(encoding="utf-8")) or {}
    policy = cfg.get("partitioning") or {}
    m04 = ((cfg.get("modulos") or {}).get("modulo_04_generar_semillas") or {})

    assert policy["enabled"] is True
    assert policy["strategy"] == "connected_internal_units"
    assert policy["partition_unit_field"] == "M04_PARTITION_UNIT"
    assert float(policy["atomicity_ratio"]) == 1.5
    assert float(policy["chunk_ratio"]) == 0.5
    assert m04["municipality_field"] == "M04_PARTITION_UNIT"
    assert policy["output_geojson"] == m04["in_geojson"]


def test_asturias_internal_units_command_is_resolvable():
    command = build_command(PARAMS, "test-asturias")
    assert command is not None
    joined = " ".join(command)
    assert "construir_unidades_internas_m04.py" in joined
    assert "--partition-unit-field M04_PARTITION_UNIT" in joined
    assert "--atomicity-ratio 1.5" in joined
    assert "--chunk-ratio 0.5" in joined
