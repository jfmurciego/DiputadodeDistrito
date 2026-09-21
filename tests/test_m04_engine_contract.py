import ast
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"configuracion/m04_engine.json"
OPERATIONAL=(ROOT/"modulos/04_generar_semillas.py",ROOT/"ddd_core/m04_seed_engine.py",ROOT/"herramientas/construir_unidades_internas_m04.py")

class M04EngineContract(unittest.TestCase):
    def test_unico_motor_m04_declarado_y_existente(self):
        contract=json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(contract["status"],"ACTIVE")
        self.assertEqual(contract["engine_id"],"ddd_core.m04_seed_engine")
        self.assertIs(contract["dynamic_loading_allowed"],False)
        self.assertTrue((ROOT/contract["active_entrypoint"]).is_file())
        self.assertTrue((ROOT/contract["cli_entrypoint"]).is_file())

    def test_ruta_operativa_no_tiene_carga_dinamica_ni_version_seleccionable(self):
        for path in OPERATIONAL:
            source=path.read_text(encoding="utf-8"); tree=ast.parse(source)
            self.assertNotIn("spec_from_file_location",source); self.assertNotIn("importlib",source)
            self.assertFalse(any(isinstance(node,ast.Constant) and isinstance(node.value,str) and "m04_seed_engine_v" in node.value for node in ast.walk(tree)))

    def test_cli_y_herramienta_importan_el_motor_canonico(self):
        for relative in ("modulos/04_generar_semillas.py","herramientas/construir_unidades_internas_m04.py"):
            source=(ROOT/relative).read_text(encoding="utf-8")
            self.assertIn("from ddd_core import m04_seed_engine",source)

if __name__=="__main__":
    unittest.main()
