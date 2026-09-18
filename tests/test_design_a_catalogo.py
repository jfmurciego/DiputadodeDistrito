from pathlib import Path
import unittest
import yaml
from herramientas.catalogo_preparacion import load_catalog, rows_for

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github"/"workflows"

class DesignA(unittest.TestCase):
    def test_exactly_three_workflows(self):
        self.assertEqual(sorted(p.name for p in WF.glob("*.yml")),["preparacion-fuentes.yml","produccion-distritos.yml","pruebas-plataforma.yml"])

    def test_visible_names(self):
        expected={"preparacion-fuentes.yml":"Preparación de fuentes oficiales","produccion-distritos.yml":"Producción de distritos","pruebas-plataforma.yml":"Pruebas de la plataforma"}
        for filename,name in expected.items():
            self.assertEqual(yaml.safe_load((WF/filename).read_text(encoding="utf-8"))["name"],name)

    def _options(self, filename):
        doc=yaml.safe_load((WF/filename).read_text(encoding="utf-8"))
        trigger=doc.get("on") or doc.get(True)
        return trigger["workflow_dispatch"]["inputs"]["territory_id"]["options"]

    def test_preparation_options_come_from_catalog(self):
        self.assertEqual(self._options("preparacion-fuentes.yml"),[r["name"] for r in rows_for("preparation",ROOT/"configuracion"/"catalogo_preparacion.yaml")])

    def test_production_options_come_from_catalog(self):
        self.assertEqual(self._options("produccion-distritos.yml"),[r["name"] for r in rows_for("production",ROOT/"configuracion"/"catalogo_preparacion.yaml")])

    def test_catalog_has_required_states(self):
        self.assertEqual(len(load_catalog(ROOT/"configuracion"/"catalogo_preparacion.yaml")["territories"]),19)

    def test_chain_and_checkpoints_remain_common(self):
        text=(WF/"produccion-distritos.yml").read_text(encoding="utf-8")
        for stage in range(1,9): self.assertIn(f"M{stage:02d}",text)
        self.assertIn("ddd-state-",text)
        self.assertNotIn("uses: ./.github/workflows/",text)

if __name__=="__main__":
    unittest.main()
