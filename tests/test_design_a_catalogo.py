from pathlib import Path
import unittest,yaml
from herramientas.catalogo_preparacion import load_catalog,rows_for,validate_repository

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows"
CAT=ROOT/"configuracion/catalogo_preparacion.yaml"

def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
def triggers(path):
    d=load(path); return d.get("on") or d.get(True) or {}

class DesignA(unittest.TestCase):
    def test_three_business_interfaces_are_named(self):
        self.assertEqual(load(WF/"preparacion-fuentes.yml")["name"],"Preparación de fuentes oficiales")
        self.assertEqual(load(WF/"produccion-distritos.yml")["name"],"Producción de distritos")
        self.assertEqual(load(WF/"pruebas-plataforma.yml")["name"],"Pruebas de la plataforma")

    def test_only_preparation_and_production_have_manual_territorial_button(self):
        manual=[]
        for path in WF.glob("*.yml"):
            t=triggers(path)
            if "workflow_dispatch" in t:
                inputs=(t["workflow_dispatch"] or {}).get("inputs",{}) or {}
                if "territory_id" in inputs: manual.append(path.name)
        self.assertEqual(sorted(manual),["preparacion-fuentes.yml","produccion-distritos.yml"])

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

    def test_production_is_thin_router_interface(self):
        d=load(WF/"produccion-distritos.yml")
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
                        p=ROOT/evidence[key]
                        self.assertTrue(p.is_file() and p.stat().st_size>0,(row["territory_id"],key))

    def test_catalog_validator_rejects_missing_claim_evidence(self):
        import copy,tempfile
        data=copy.deepcopy(load_catalog(CAT))
        aragon=next(r for r in data["territories"] if r["territory_id"]=="aragon")
        aragon["editions"]["2025"]["evidence"]["territorial_product"]="missing/evidence.json"
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"catalog.yaml"
            p.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"evidencia inexistente"):
                validate_repository(p,ROOT)

    def test_forms_match_single_catalog(self):
        prep=(triggers(WF/"preparacion-fuentes.yml")["workflow_dispatch"]["inputs"]["territory_id"]["options"])
        prod=(triggers(WF/"produccion-distritos.yml")["workflow_dispatch"]["inputs"]["territory_id"]["options"])
        self.assertEqual(prep,[r["name"] for r in rows_for("preparation",CAT)])
        self.assertEqual(prod,[r["name"] for r in rows_for("production",CAT)])
        pending=[r for r in load_catalog(CAT)["territories"] if next(iter(r["editions"].values()))["preparation_status"]=="PENDING_INCORPORATION"]
        self.assertTrue(pending)
        self.assertTrue(all(next(iter(r["editions"].values()))["territorial_source_declaration"] is None for r in pending))

if __name__=="__main__": unittest.main()
