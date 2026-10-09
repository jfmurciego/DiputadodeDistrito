import ast
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"configuracion/m04_engine.json"
PUBLIC_ENTRYPOINTS=(ROOT/"modulos/04_generar_semillas.py",ROOT/"herramientas/construir_unidades_internas_m04.py")
CANONICAL_FACADE=ROOT/"ddd_core/m04_seed_engine.py"

class M04EngineContract(unittest.TestCase):
    def test_unico_motor_m04_declarado_y_existente(self):
        contract=json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(contract["status"],"ACTIVE")
        self.assertEqual(contract["engine_id"],"ddd_core.m04_seed_engine")
        self.assertIs(contract["dynamic_loading_allowed"],False)
        self.assertTrue((ROOT/contract["active_entrypoint"]).is_file())
        self.assertTrue((ROOT/contract["cli_entrypoint"]).is_file())

    def test_entrypoints_publicos_no_seleccionan_version_ni_cargan_dinamicamente(self):
        for path in PUBLIC_ENTRYPOINTS:
            source=path.read_text(encoding="utf-8")
            self.assertNotIn("spec_from_file_location",source)
            self.assertNotIn("importlib",source)
            self.assertNotIn("m04_seed_engine_v",source)
            self.assertIn("from ddd_core import m04_seed_engine",source)

    def test_fachada_canonica_compone_estaticamente_sin_carga_dinamica(self):
        source=CANONICAL_FACADE.read_text(encoding="utf-8")
        tree=ast.parse(source)
        self.assertNotIn("spec_from_file_location",source)
        self.assertNotIn("importlib",source)
        imports=[
            node for node in ast.walk(tree)
            if isinstance(node,(ast.Import,ast.ImportFrom))
        ]
        self.assertTrue(imports)
        self.assertIn("from ddd_core import m04_seed_engine_v7412 as core",source)
        self.assertIn("from ddd_core import m04_seed_engine_v7411 as postprocess_engine",source)

if __name__=="__main__":
    unittest.main()
