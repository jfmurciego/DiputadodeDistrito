from pathlib import Path
import unittest,yaml
from herramientas.catalogo_territorios import format_territory_label, load_master, selector_labels
from herramientas.catalogo_preparacion import load_catalog,rows_for,validate_repository
from herramientas.resolver_fuentes_territorio import territories

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows"
CAT=ROOT/"configuracion/catalogo_preparacion.yaml"

def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
def triggers(path):
    d=load(path); return d.get("on") or d.get(True) or {}

class DesignA(unittest.TestCase):
    def test_business_interfaces_are_named(self):
        self.assertEqual(load(WF/"ejecucion-completa-proyecto.yml")["name"],"P00 Campaña")
        self.assertEqual(load(WF/"preparacion-fuentes.yml")["name"],"P10 Fuentes — P11 Territoriales")
        self.assertEqual(load(WF/"preparacion-resultados-electorales.yml")["name"],"P10 Fuentes — P12 Electorales")
        self.assertEqual(load(WF/"p20-distritos.yml")["name"],"P20 Distritos")  # T-377 (D-139)
        self.assertEqual(load(WF/"incorporacion-resultados-electorales.yml")["name"],"P40 Resultados electorales")
        self.assertEqual(load(WF/"p90-automatico.yml")["name"],"P90 Automático")

    def test_business_workflows_with_territory_selector_are_explicit(self):
        manual=[]
        for path in WF.glob("*.yml"):
            t=triggers(path)
            if "workflow_dispatch" in t:
                inputs=(t["workflow_dispatch"] or {}).get("inputs",{}) or {}
                if "territory_id" in inputs: manual.append(path.name)
        self.assertEqual(sorted(manual),[
            "ejecucion-completa-proyecto.yml",
            "incorporacion-resultados-electorales.yml",
            "preparacion-fuentes.yml",
            "preparacion-resultados-electorales.yml",
        ])  # T-377: P20 usa códigos (`territorios`); P28 retirada

    def test_internal_capabilities_remain(self):
        expected={
          "p40-publicacion.yml",
          "_reutilizable-incorporacion-electoral.yml","p20-distritos.yml",
        }
        self.assertTrue(expected.issubset({p.name for p in WF.glob("*.yml")}))

    def test_generation_and_electoral_incorporation_use_separate_reusables(self):
        generation=load(WF/"p20-distritos.yml")
        # T-377 (D-139): el motor va dentro de P20; la matriz del botón llama al propio fichero.
        self.assertEqual(list(generation["jobs"])[:4],["interfaz","resolver_interfaz","entrada","resolve"])
        self.assertFalse(any("uses" in j for j in generation["jobs"].values()))  # D-148: sin autollamada
        self.assertNotIn("_reutilizable-generacion-territorial.yml",{p.name for p in WF.glob("*.yml")})
        electoral=load(WF/"incorporacion-resultados-electorales.yml")
        self.assertEqual(list(electoral["jobs"]),["preparar","incorporar"])
        self.assertEqual(electoral["jobs"]["incorporar"]["uses"],"./.github/workflows/_reutilizable-incorporacion-electoral.yml")
        reusable=(WF/"_reutilizable-incorporacion-electoral.yml").read_text(encoding="utf-8")
        for forbidden in ("m01:","m02:","m03:","m04:","m05:","m06:","auditar_componentes_geometricos","p40-publicacion.yml"):
            self.assertNotIn(forbidden,reusable)

    def test_catalog_is_real_and_authorization_required(self):
        data=load_catalog(CAT); validate_repository(CAT,ROOT)
        for row in data["territories"]:
            for state in row["editions"].values():
                self.assertIn("production_authorization",state)

    def test_true_availability_claims_have_real_evidence(self):
        data=load_catalog(CAT)
        for row in data["territories"]:
            for state in row["editions"].values():
                evidence=state.get("evidence") or {}
                checks=(("territorial_product_available","territorial_product"),("electoral_source_prepared","electoral_source"),("electoral_product_available","electoral_product"))
                for flag,key in checks:
                    if state.get(flag):
                        self.assertIn(key,evidence,(row["territory_id"],flag))
                        q=ROOT/evidence[key]
                        self.assertTrue(q.is_file() and q.stat().st_size>0,(row["territory_id"],key))

    def test_preparation_uses_common_registry_and_generation_keeps_readiness_gate(self):
        prep=triggers(WF/"preparacion-fuentes.yml")["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        electoral=triggers(WF/"incorporacion-resultados-electorales.yml")["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        expected=selector_labels(ROOT/"configuracion/catalogo_territorios_espana_2025.yaml")
        generable=[r["name"] for r in rows_for("generation",CAT)]
        electoral_ready=[r["name"] for r in rows_for("electoral_application",CAT)]
        self.assertEqual(prep,expected)
        self.assertEqual(electoral,expected)
        self.assertIn("Galicia",generable)
        self.assertIn("Galicia",electoral_ready)

if __name__=="__main__": unittest.main()
