from pathlib import Path
import unittest,yaml
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
        self.assertEqual(load(WF/"preparacion-fuentes.yml")["name"],"Preparación de Datos Territoriales")
        self.assertEqual(load(WF/"preparacion-resultados-electorales.yml")["name"],"Preparación de Resultados Electorales")
        self.assertEqual(load(WF/"produccion-distritos.yml")["name"],"Generación de Distritos Autonómicos")
        self.assertEqual(load(WF/"incorporacion-resultados-electorales.yml")["name"],"Incorporación de Resultados Electorales")
        self.assertEqual(load(WF/"pruebas-plataforma.yml")["name"],"Pruebas de la Plataforma")

    def test_business_workflows_with_territory_selector_are_explicit(self):
        manual=[]
        for path in WF.glob("*.yml"):
            t=triggers(path)
            if "workflow_dispatch" in t:
                inputs=(t["workflow_dispatch"] or {}).get("inputs",{}) or {}
                if "territory_id" in inputs: manual.append(path.name)
        self.assertEqual(sorted(manual),[
            "incorporacion-resultados-electorales.yml",
            "preparacion-fuentes.yml",
            "preparacion-resultados-electorales.yml",
            "produccion-distritos.yml",
        ])

    def test_internal_capabilities_remain(self):
        expected={
          "_reutilizable-auditoria-topologica.yml","_reutilizable-operacion-territorial.yml",
          "desplegar-visor-publico.yml","generar-alternativas-territoriales.yml",
          "notificar-finalizacion-orquestacion.yml","orquestacion-control.yml",
          "orquestacion-durable.yml","producir-territorio-por-contrato.yml",
          "publicar-checkpoint-cyl-m06.yml","validar-contratos-territoriales.yml",
          "validar-productos-publicos.yml",
        }
        self.assertTrue(expected.issubset({p.name for p in WF.glob("*.yml")}))

    def test_generation_and_electoral_incorporation_are_thin_router_interfaces(self):
        for name in ("produccion-distritos.yml","incorporacion-resultados-electorales.yml"):
            d=load(WF/name)
            self.assertEqual(list(d["jobs"]),["resolver_interfaz","ruta"])
            self.assertEqual(d["jobs"]["ruta"]["uses"],"./.github/workflows/_reutilizable-operacion-territorial.yml")
            self.assertFalse("m01" in d["jobs"])
        engine=load(WF/"producir-territorio-por-contrato.yml")
        t=engine.get("on") or engine.get(True)
        self.assertIn("workflow_call",t)

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
        generation=triggers(WF/"produccion-distritos.yml")["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        electoral=triggers(WF/"incorporacion-resultados-electorales.yml")["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        expected=[r["name"] for r in territories()]
        generable=[r["name"] for r in rows_for("generation",CAT)]\n        electoral_ready=[r["name"] for r in rows_for("electoral_application",CAT)]
        self.assertEqual(prep,expected)
        self.assertEqual(generation,producible)
        self.assertEqual(electoral,producible)

if __name__=="__main__": unittest.main()
