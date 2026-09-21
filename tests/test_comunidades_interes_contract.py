import json
import unittest
from pathlib import Path

import yaml

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

    def test_rutas_comarcales_se_declaran_en_yaml_territorial_vigente(self):
        for relative in (
            "territorios/aragon/config/aragon_2025.yaml",
            "territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml",
        ):
            cfg=yaml.safe_load((ROOT/relative).read_text(encoding="utf-8")) or {}
            comarcas=(((cfg.get("io") or {}).get("input") or {}).get("comarcas") or {})
            self.assertIn("enabled",comarcas)
            self.assertIsInstance(comarcas["enabled"],bool)
            self.assertTrue(str(comarcas.get("path") or "").strip())
            self.assertIs(comarcas.get("require_full_coverage"),True)

    def test_source_enabled_coincide_con_yaml_territorial(self):
        contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
        for territory_id, territory in contract["territories"].items():
            cfg=yaml.safe_load((ROOT/territory["configuration"]).read_text(encoding="utf-8")) or {}
            comarcas=(((cfg.get("io") or {}).get("input") or {}).get("comarcas") or {})
            expected=bool(comarcas.get("enabled",False))
            self.assertIs(
                territory["source_enabled"],
                expected,
                f"{territory_id}: source_enabled debe reflejar io.input.comarcas.enabled",
            )

    def test_p07_no_se_presenta_como_superado_en_evidencia_historica(self):
        evidence=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["communities_of_interest"]["criterion"],"P07")
        for record in evidence["territories"].values():
            self.assertEqual(record["communities_of_interest_gate"],"NOT_EVALUABLE")
            self.assertEqual(record["publication_status"],"BLOCKED")

if __name__=="__main__":
    unittest.main()
