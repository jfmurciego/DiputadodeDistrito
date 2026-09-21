import unittest
from pathlib import Path
import yaml
from herramientas.preparar_unidades_internas import build_command

ROOT=Path(__file__).resolve().parents[1]
PARAMS=ROOT/"territorios/principado_de_asturias/config/principado_de_asturias_2025.yaml"

class AsturiasM04Partitioning(unittest.TestCase):
    def test_asturias_declares_internal_units_before_m04(self):
        cfg=yaml.safe_load(PARAMS.read_text(encoding="utf-8")) or {}
        policy=cfg.get("partitioning") or {}
        m04=((cfg.get("modulos") or {}).get("modulo_04_generar_semillas") or {})
        self.assertIs(policy["enabled"],True)
        self.assertEqual(policy["strategy"],"connected_internal_units")
        self.assertEqual(policy["partition_unit_field"],"M04_PARTITION_UNIT")
        self.assertEqual(float(policy["atomicity_ratio"]),1.5)
        self.assertEqual(float(policy["chunk_ratio"]),0.5)
        self.assertEqual(m04["municipality_field"],"M04_PARTITION_UNIT")
        self.assertEqual(policy["output_geojson"],m04["in_geojson"])

    def test_asturias_internal_units_command_is_resolvable(self):
        command=build_command(PARAMS,"test-asturias")
        self.assertIsNotNone(command)
        joined=" ".join(command)
        self.assertIn("construir_unidades_internas_m04.py",joined)
        self.assertIn("--partition-unit-field M04_PARTITION_UNIT",joined)
        self.assertIn("--atomicity-ratio 1.5",joined)
        self.assertIn("--chunk-ratio 0.5",joined)

if __name__=="__main__":
    unittest.main()
