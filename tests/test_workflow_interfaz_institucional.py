"""
PROYECTO: Diputado de Distrito
PRUEBA: interfaz institucional de GitHub Actions
VERSIÓN: 1.0.0
FECHA: 2026-09-15
OBJETIVO: exigir una única interfaz territorial general, ruta institucional,
etiquetas públicas españolas y compatibilidad con los IDs técnicos vigentes.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
INTERFACE = WORKFLOWS / "operacion-territorial.yml"

VISIBLE_TERRITORIES = [
    "Andalucía",
    "Aragón",
    "Principado de Asturias",
    "Islas Baleares",
    "Canarias",
    "Cantabria",
    "Castilla-La Mancha",
    "Castilla y León",
    "Cataluña",
    "Comunidad Valenciana",
    "Extremadura",
    "Galicia",
    "Comunidad de Madrid",
    "Región de Murcia",
    "Comunidad Foral de Navarra",
    "País Vasco",
    "La Rioja",
    "Ceuta",
    "Melilla",
]

TECHNICAL_IDS = {
    "Andalucía": "andalucia",
    "Aragón": "aragon",
    "Principado de Asturias": "principado_de_asturias",
    "Islas Baleares": "illes_balears",
    "Canarias": "canarias",
    "Cantabria": "cantabria",
    "Castilla-La Mancha": "castilla_la_mancha",
    "Castilla y León": "castilla_y_leon",
    "Cataluña": "cataluna",
    "Comunidad Valenciana": "comunidad_valenciana",
    "Extremadura": "extremadura",
    "Galicia": "galicia",
    "Comunidad de Madrid": "madrid",
    "Región de Murcia": "region_de_murcia",
    "Comunidad Foral de Navarra": "comunidad_foral_de_navarra",
    "País Vasco": "pais_vasco",
    "La Rioja": "la_rioja",
    "Ceuta": "ceuta",
    "Melilla": "melilla",
}

VISIBLE_OPERATIONS = [
    "Admitir contrato",
    "Verificar contrato",
    "Preparar base M01–M03",
    "Diagnosticar topología",
    "Certificar territorio M01–M06",
    "Producir resultado M01–M08",
    "Generar alternativas GerryChain",
]

VISIBLE_ENSEMBLE_STAGES = [
    "Prueba sintética",
    "Piloto Aragón — 10 alternativas",
    "Lote Aragón — 50 alternativas",
]


def _data():
    return yaml.safe_load(INTERFACE.read_text(encoding="utf-8")) or {}


def _dispatch_inputs():
    data = _data()
    triggers = data.get(True, data.get("on", {})) or {}
    return triggers["workflow_dispatch"]["inputs"]


def test_unica_interfaz_territorial_general_y_sin_picadora_activa():
    assert INTERFACE.is_file()
    assert not (WORKFLOWS / "picadora-territorial.yml").exists()
    assert all("picadora" not in path.name.lower() for path in WORKFLOWS.glob("*.yml"))

    production = (WORKFLOWS / "producir-territorio-por-contrato.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_call" in production
    assert "workflow_dispatch" not in production


def test_nombres_visibles_territoriales_son_espanoles_y_canónicos():
    inputs = _dispatch_inputs()
    assert inputs["territory_id"]["options"] == VISIBLE_TERRITORIES
    assert inputs["territory_id"]["default"] == "La Rioja"
    assert "Islas Baleares" in inputs["territory_id"]["options"]
    assert "illes_balears" not in inputs["territory_id"]["options"]


def test_operaciones_y_fases_no_exponen_ids_tecnicos_en_el_formulario():
    inputs = _dispatch_inputs()
    assert inputs["operation"]["options"] == VISIBLE_OPERATIONS
    assert inputs["operation"]["default"] == "Admitir contrato"
    assert inputs["ensemble_stage"]["options"] == VISIBLE_ENSEMBLE_STAGES
    assert inputs["ensemble_stage"]["default"] == "Prueba sintética"


def test_resolvedor_preserva_ids_tecnicos_territoriales():
    text = INTERFACE.read_text(encoding="utf-8")
    for label, technical_id in TECHNICAL_IDS.items():
        expected = f'"{label}"|{technical_id}) territory_id={technical_id} ;;'
        assert expected in text

    assert "territorios/${{ needs.resolver_interfaz.outputs.territory_id }}/config/" in text
    assert "territory_id: ${{ needs.resolver_interfaz.outputs.territory_id }}" in text


def test_resolvedor_preserva_ids_tecnicos_de_operacion_y_ensemble():
    text = INTERFACE.read_text(encoding="utf-8")
    for technical_operation in (
        "admitir_contrato",
        "verificar_contrato",
        "preparar_base_m01_m03",
        "diagnosticar_topologia",
        "certificar_territorio_m01_m06",
        "producir_resultado_m01_m08",
        "generar_alternativas_gerrychain",
    ):
        assert f"|{technical_operation}) operation={technical_operation} ;;" in text

    for technical_stage in ("synthetic", "aragon_10", "aragon_50"):
        assert f"|{technical_stage}) ensemble_stage={technical_stage} ;;" in text
