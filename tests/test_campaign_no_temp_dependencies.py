from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_CONGRESS_CONSUMERS = (
    "ddd_core/congreso_contract.py",
    "ddd_core/congreso_preflight_adapter.py",
    "herramientas/preflight_caceres_n08.py",
    "herramientas/preflight_topologico_nacional.py",
    "herramientas/verificar_topologia_nacional.py",
    "herramientas/verificar_evidencia_n08_readonly.py",
    "herramientas/registrar_anomalias_n08.py",
)


def test_active_congress_entrypoints_do_not_read_from_machine_local_temp_paths():
    forbidden = ("/private/tmp/", "/var/folders/", "DDD-n08-expediente")
    for rel in ACTIVE_CONGRESS_CONSUMERS:
        source = (ROOT / rel).read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in source, f"{rel} embeds local temp dependency {marker}"
