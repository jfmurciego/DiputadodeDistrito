import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"configuracion/comunidades_interes.json"
EVIDENCE=ROOT/"resultados/fase1/EVIDENCIA_PUBLICABILIDAD.json"

class ComunidadesInteresContract(unittest.TestCase):
    def test_c13_declara_metrica_y_bloqueo_sin_fuente(self):
        contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["criterion"],"P07_communities_of_interest")
        self.assertIs(contract["scope"]["municipality_alone_is_insufficient"],True)
        self.assertIs(contract["scope"]["partisan_or_election_data_forbidden"],True)
        self.assertEqual(set(contract["metrics"]),{"split_communities","communities_per_district","dominant_population_share","population_retention"})
        self.assertIs(contract["evaluation_rule"]["precommitment_required"],True)
        self.assertIs(contract["evaluation_rule"]["not_evaluable_blocks_publication"],True)
        self.assertTrue(all(item["status"]=="NOT_EVALUABLE" and item["source_enabled"] is False for item in contract["territories"].values()))

    def test_rutas_comarcales_existentes_siguen_inertes(self):
        for relative in ("territorios/aragon/config/aragon_2025.yaml","territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml"):
            text=(ROOT/relative).read_text(encoding="utf-8")
            start=text.index("    comarcas:")
            block=text[start:start+220]
            self.assertIn("enabled: false",block)

    def test_p07_no_se_presenta_como_superado(self):
        evidence=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["communities_of_interest"]["criterion"],"P07")
        for record in evidence["territories"].values():
            self.assertEqual(record["communities_of_interest_gate"],"NOT_EVALUABLE")
            self.assertEqual(record["publication_status"],"BLOCKED")

if __name__=="__main__":
    unittest.main()
