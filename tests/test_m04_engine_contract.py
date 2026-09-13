import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configuracion/m04_engine.json"
OPERATIONAL = (
    ROOT / "modulos/04_generar_semillas.py",
    ROOT / "ddd_core/m04_seed_engine.py",
    ROOT / "herramientas/construir_unidades_internas_m04.py",
)


def test_unico_motor_m04_declarado_y_existente():
    contract = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert contract["status"] == "ACTIVE"
    assert contract["engine_id"] == "ddd_core.m04_seed_engine"
    assert contract["dynamic_loading_allowed"] is False
    assert (ROOT / contract["active_entrypoint"]).is_file()
    assert (ROOT / contract["cli_entrypoint"]).is_file()


def test_ruta_operativa_no_tiene_carga_dinamica_ni_version_seleccionable():
    for path in OPERATIONAL:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert "spec_from_file_location" not in source
        assert "importlib" not in source
        assert not any(
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "m04_seed_engine_v" in node.value
            for node in ast.walk(tree)
        )


def test_cli_y_herramienta_importan_el_motor_canonico():
    for relative in (
        "modulos/04_generar_semillas.py",
        "herramientas/construir_unidades_internas_m04.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "from ddd_core import m04_seed_engine" in source
