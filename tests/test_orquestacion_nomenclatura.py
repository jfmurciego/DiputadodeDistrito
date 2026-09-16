"""Contrato de nomenclatura y compatibilidad de la capa de orquestación."""
from pathlib import Path
import unittest

from herramientas import informe_orquestacion
from herramientas import g10_informe_operativo
from herramientas import materializar_checkpoints
from herramientas import g10_materializar_checkpoints

ROOT=Path(__file__).resolve().parents[1]

class OrquestacionNomenclatura(unittest.TestCase):
    def test_herramientas_canonicas_y_wrappers_compatibles(self):
        self.assertTrue((ROOT/"herramientas/orquestar_ejecucion.py").is_file())
        self.assertTrue((ROOT/"herramientas/informe_orquestacion.py").is_file())
        self.assertTrue((ROOT/"herramientas/materializar_checkpoints.py").is_file())
        self.assertIs(g10_informe_operativo.build,informe_orquestacion.build)
        self.assertIs(g10_materializar_checkpoints.plan,materializar_checkpoints.plan)

    def test_informe_publica_nombre_funcional_y_alias_de_esquema(self):
        state={"schema_version":"1.0","stage_catalog_version":"1","records":[]}
        factual={"phase":"F1","status":"PASS","territories":{}}
        report=informe_orquestacion.build(state,factual)
        self.assertIn("orquestacion",report)
        self.assertIn("g10",report)
        self.assertEqual(report["orquestacion"],report["g10"])
        self.assertTrue(informe_orquestacion.markdown(report).startswith("# Estado operativo de orquestación"))

    def test_workflows_activos_usan_nomenclatura_funcional(self):
        control=(ROOT/".github/workflows/orquestacion-control.yml").read_text(encoding="utf-8")
        durable=(ROOT/".github/workflows/orquestacion-durable.yml").read_text(encoding="utf-8")
        for text in (control,durable):
            self.assertIn("herramientas/orquestar_ejecucion.py",text)
            self.assertNotIn("name: G10",text)
        self.assertIn("herramientas/informe_orquestacion.py",durable)
        self.assertIn("ESTADO_OPERATIVO_ORQUESTACION.json",durable)
        self.assertIn("orquestacion-lote-",durable)

if __name__=="__main__":unittest.main()
