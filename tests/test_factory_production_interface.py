#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, unittest
from pathlib import Path
import yaml
from herramientas.catalogo_preparacion import rows_for

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("resolver",ROOT/"herramientas"/"resolver_ejecucion_territorial.py")
RESOLVER=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(RESOLVER)
WORKFLOW=ROOT/".github/workflows/produccion-distritos.yml"
CATALOG=ROOT/"configuracion/catalogo_preparacion.yaml"

class FactoryProductionInterface(unittest.TestCase):
    def test_dos_contratos_resuelven_la_misma_interfaz(self):
        for territory in ("aragon","castilla_y_leon"):
            d=RESOLVER.resolve(str(ROOT/"territorios"/territory/"config"/f"{territory}_2025.yaml"))
            self.assertEqual(d["decision"],"ADMITTED",d["contract"]["errors"])
            self.assertEqual(d["territory_id"],territory)

    def test_interfaz_manual_se_deriva_del_catalogo(self):
        doc=yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        triggers=doc.get("on") or doc.get(True)
        options=triggers["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        self.assertEqual(options,[r["name"] for r in rows_for("production",CATALOG)])

    def test_linea_comun_m01_m08_y_execute_protegido(self):
        text=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch",text)
        self.assertNotIn("workflow_call",text)
        self.assertIn("EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION",text)
        self.assertIn("resolver_ejecucion_territorial.py",text)
        for stage in range(1,9): self.assertIn(f"M{stage:02d}",text)
        self.assertIn("ddd-state-",text)

if __name__=="__main__": unittest.main()
