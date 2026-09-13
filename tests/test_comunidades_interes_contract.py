import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configuracion/comunidades_interes.json"
EVIDENCE = ROOT / "resultados/fase1/EVIDENCIA_PUBLICABILIDAD.json"


def test_c13_declara_metrica_y_bloqueo_sin_fuente():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["criterion"] == "P07_communities_of_interest"
    assert contract["scope"]["municipality_alone_is_insufficient"] is True
    assert contract["scope"]["partisan_or_election_data_forbidden"] is True
    assert set(contract["metrics"]) == {
        "split_communities",
        "communities_per_district",
        "dominant_population_share",
        "population_retention",
    }
    assert contract["evaluation_rule"]["precommitment_required"] is True
    assert contract["evaluation_rule"]["not_evaluable_blocks_publication"] is True
    assert all(
        item["status"] == "NOT_EVALUABLE" and item["source_enabled"] is False
        for item in contract["territories"].values()
    )


def test_rutas_comarcales_existentes_siguen_inertes():
    for relative in (
        "territorios/aragon/config/aragon_2025.yaml",
        "territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        start = text.index("    comarcas:")
        block = text[start:start + 220]
        assert "enabled: false" in block


def test_p07_no_se_presenta_como_superado():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["communities_of_interest"]["criterion"] == "P07"
    for record in evidence["territories"].values():
        assert record["communities_of_interest_gate"] == "NOT_EVALUABLE"
        assert record["publication_status"] == "BLOCKED"
