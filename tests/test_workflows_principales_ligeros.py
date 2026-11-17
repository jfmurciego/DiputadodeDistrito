from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows"

def load(name):
    return yaml.safe_load((WF/name).read_text(encoding="utf-8")) or {}

class LightweightBusinessWorkflows(unittest.TestCase):
    def test_visible_business_names_are_numbered(self):
        expected={
            "ejecucion-completa-proyecto.yml":"P00 Campaña",
            "p10-fuentes.yml":"P10 Fuentes",
            "p20-distritos.yml":"P20 Distritos",
            "p30-resultados-electorales.yml":"P30 Resultados electorales",
            "p40-publicacion.yml":"P40 Publicación",
        }
        for name,label in expected.items():
            self.assertEqual(load(name)["name"],label)

    def test_electoral_incorporation_does_not_embed_territorial_generation(self):
        ui=load("p30-resultados-electorales.yml")
        self.assertEqual(list(ui["jobs"]),["resolver","incorporar"])
        self.assertNotIn("uses",ui["jobs"]["incorporar"])
        text=(WF/"p30-resultados-electorales.yml").read_text(encoding="utf-8")
        for forbidden in (
            "Base territorial y población","Adyacencias territoriales","Grafo territorial",
            "Formación inicial de distritos","Optimización de distritos",
            "auditar_componentes_geometricos","p40-publicacion.yml",
        ):
            self.assertNotIn(forbidden,text)
        self.assertIn("Verificar producto territorial certificado",text)
        self.assertIn("Verificar resultados electorales preparados",text)
        self.assertIn("Agregar resultados electorales a los distritos",text)
        self.assertIn("Generar producto electoral territorial",text)
        self.assertIn("Registrar disponibilidad del producto electoral",text)

    def test_generation_and_electoral_incorporation_do_not_publish_pages(self):
        generation=(WF/"p20-distritos.yml").read_text(encoding="utf-8")
        electoral=(WF/"p30-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertNotIn("publish_result:",generation)
        self.assertNotIn("pages: write",generation)
        self.assertNotIn("id-token: write",generation)
        territorial=(WF/"p20-distritos.yml").read_text(encoding="utf-8")
        for forbidden in ("M07","M08","p40-publicacion.yml","pages: write","id-token: write","instalar_fuente_electoral_oficial.py"):
            self.assertNotIn(forbidden,territorial)
        self.assertNotIn("publish_result:",electoral)
        self.assertNotIn("pages: write",electoral)
        self.assertNotIn("id-token: write",electoral)

    def test_concurrency_domains_are_explicit(self):
        territorial_prep=(WF/"../../tests/fixtures/p10_vistas/_p11-territoriales.yml").read_text(encoding="utf-8")
        generation=(WF/"p20-distritos.yml").read_text(encoding="utf-8")
        electoral_prep=(WF/"../../tests/fixtures/p10_vistas/_p12-electorales.yml").read_text(encoding="utf-8")
        electoral=(WF/"p30-resultados-electorales.yml").read_text(encoding="utf-8")
        publisher=(WF/"p40-publicacion.yml").read_text(encoding="utf-8")
        # T-375: la concurrencia REAL de P10 es la del workflow (no un comentario de cabecera).
        p10=load("p10-fuentes.yml")
        grupo=p10["concurrency"]["group"]
        self.assertIn("ddd-electoral-prod-",grupo)
        self.assertIn("ddd-territorial-prod-",grupo)
        self.assertEqual(p10["concurrency"]["cancel-in-progress"],False)
        self.assertEqual(p10["concurrency"]["queue"],"max")
        self.assertIn("ddd-territorial-prod-",generation)
        self.assertIn("ddd-territorial-prod-",generation)
        self.assertIn("ddd-territorial-prod-",generation)
        self.assertIn("ddd-electoral-prod-",electoral_prep)
        self.assertIn("ddd-electoral-prod-",electoral)
        self.assertIn("group: ddd-catalog-promotion",territorial_prep)
        self.assertIn("group: ddd-catalog-promotion",electoral_prep)
        # T-360: las cadenas registran sin grupo único (registro re-derivado con reintento).
        self.assertNotIn("group: ddd-catalog-promotion",(WF/"p20-distritos.yml").read_text(encoding="utf-8"))
        self.assertNotIn("group: ddd-catalog-promotion", (WF/"p30-resultados-electorales.yml").read_text(encoding="utf-8"))
        self.assertIn("group: ddd-pages-prod",publisher)
        self.assertIn("cancel-in-progress: false",publisher)

    def test_territorial_registration_runs_after_resumed_skipped_stages(self):
        reusable=load("p20-distritos.yml")
        register=reusable["jobs"]["registrar"]
        self.assertIn("always()",register["if"])
        self.assertIn("needs.auditoria.result == 'success'",register["if"])

    def test_electoral_product_remains_publishable_after_decoupling(self):
        reusable=(WF/"p30-resultados-electorales.yml").read_text(encoding="utf-8")
        publisher=(WF/"p40-publicacion.yml").read_text(encoding="utf-8")
        self.assertIn("Conservar certificación consumible por publicación",reusable)
        self.assertIn("name: ddd-audit-electoral-${{ github.run_id }}",reusable)
        self.assertIn('payload["workflow_run_id"]=int(run_id)',reusable)
        self.assertIn('payload["source_territorial_run_id"]',reusable)
        # T-125: la 05 promueve solo un run explícito; sin él es «solo sitio» y no resuelve latest_validated
        self.assertIn("PRODUCTION_RUN_ID_OVERRIDE",publisher)
        self.assertNotIn("latest_validated.run_id",publisher)


if __name__=="__main__":
    unittest.main()
