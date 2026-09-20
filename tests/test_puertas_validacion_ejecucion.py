from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows"
GATE = WF / "_reutilizable-puerta-validacion.yml"
ORCH = WF / "ejecucion-completa-proyecto.yml"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_puerta_reutilizable_tiene_contrato_uniforme():
    data = load(GATE)
    triggers = data.get("on") or data.get(True)
    call = triggers["workflow_call"]
    assert set(call["outputs"]) == {
        "decision",
        "run_id",
        "artifact_name",
        "artifact_digest",
        "evidence_artifact",
    }
    text = GATE.read_text(encoding="utf-8")
    assert "VALIDADO" in text
    assert "BLOQUEADO" in text
    assert "ddd.validation-gate/1.0" in text
    assert "artifact_digest" in text
    assert "expected_digest" in text


def test_puerta_valida_semantica_de_los_cuatro_productos():
    text = GATE.read_text(encoding="utf-8")
    assert "seleccionar_paquete_fuentes" in text
    assert "seleccionar_checkpoint_productivo" in text
    assert "production_status.json" in text
    assert "validar_paquete_electoral.py" in text
    assert "ddd-electoral-application-report-" in text
    assert "electoral_application" in text


def test_orquestador_no_consumira_una_fase_sin_puerta_verde():
    data = load(ORCH)
    jobs = data["jobs"]
    assert "validar_territorial" in jobs["generar"]["needs"]
    assert "validar_generacion" in jobs["preparar_electoral"]["needs"]
    assert "validar_electoral" in jobs["incorporar"]["needs"]
    assert "validar_producto" in jobs["actualizar_estado"]["needs"]
    assert "validar_producto" in jobs["publicar"]["needs"]


def test_evidencia_de_puerta_se_conserva_90_dias():
    text = GATE.read_text(encoding="utf-8")
    assert "ddd-validation-gate-" in text
    assert "retention-days: 90" in text
