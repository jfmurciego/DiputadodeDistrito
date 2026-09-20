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
            "preparacion-fuentes.yml":"01 · Preparación de Datos Territoriales",
            "produccion-distritos.yml":"02 · Generación de Distritos Autonómicos",
            "preparacion-resultados-electorales.yml":"03 · Preparación de Resultados Electorales",
            "incorporacion-resultados-electorales.yml":"04 · Incorporación de Resultados Electorales",
            "desplegar-visor-publico.yml":"05 · Publicación del Visor",
        }
        for name,label in expected.items():
            self.assertEqual(load(name)["name"],label)

    def test_electoral_incorporation_does_not_embed_territorial_generation(self):
        ui=load("incorporacion-resultados-electorales.yml")
        self.assertEqual(list(ui["jobs"]),["preparar","incorporar"])
        self.assertEqual(ui["jobs"]["incorporar"]["uses"],"./.github/workflows/_reutilizable-incorporacion-electoral.yml")
        text=(WF/"_reutilizable-incorporacion-electoral.yml").read_text(encoding="utf-8")
        for forbidden in (
            "Base territorial y población","Adyacencias territoriales","Grafo territorial",
            "Formación inicial de distritos","Optimización de distritos",
            "auditar_componentes_geometricos","_reutilizable-publicar-sitio.yml",
        ):
            self.assertNotIn(forbidden,text)
        self.assertIn("Verificar producto territorial certificado",text)
        self.assertIn("Verificar resultados electorales preparados",text)
        self.assertIn("Agregar resultados electorales a los distritos",text)
        self.assertIn("Generar producto electoral territorial",text)
        self.assertIn("Registrar producto electoral",text)

    def test_generation_and_electoral_incorporation_do_not_publish_pages(self):
        generation=(WF/"produccion-distritos.yml").read_text(encoding="utf-8")
        electoral=(WF/"incorporacion-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertNotIn("publish_result:",generation)
        self.assertNotIn("pages: write",generation)
        self.assertNotIn("id-token: write",generation)
        territorial=(WF/"_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        for forbidden in ("M07","M08","_reutilizable-publicar-sitio.yml","pages: write","id-token: write","instalar_fuente_electoral_oficial.py"):
            self.assertNotIn(forbidden,territorial)
        self.assertNotIn("publish_result:",electoral)
        self.assertNotIn("pages: write",electoral)
        self.assertNotIn("id-token: write",electoral)

    def test_concurrency_domains_are_explicit(self):
        territorial_prep=(WF/"preparacion-fuentes.yml").read_text(encoding="utf-8")
        generation=(WF/"produccion-distritos.yml").read_text(encoding="utf-8")
        electoral_prep=(WF/"preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        electoral=(WF/"incorporacion-resultados-electorales.yml").read_text(encoding="utf-8")
        publisher=(WF/"_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        self.assertIn("ddd-territorial-prod-",territorial_prep)
        self.assertIn("ddd-territorial-prod-",generation)
        self.assertIn("ddd-electoral-prod-",electoral_prep)
        self.assertIn("ddd-electoral-prod-",electoral)
        self.assertIn("group: ddd-catalog-promotion",territorial_prep)
        self.assertIn("group: ddd-catalog-promotion",electoral_prep)
        self.assertIn("group: ddd-catalog-promotion",(WF/"_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8"))
        self.assertIn("group: ddd-catalog-promotion", (WF/"_reutilizable-incorporacion-electoral.yml").read_text(encoding="utf-8"))
        self.assertIn("group: ddd-pages-prod",publisher)
        self.assertIn("cancel-in-progress: false",publisher)

    def test_electoral_product_remains_publishable_after_decoupling(self):
        reusable=(WF/"_reutilizable-incorporacion-electoral.yml").read_text(encoding="utf-8")
        publisher=(WF/"desplegar-visor-publico.yml").read_text(encoding="utf-8")
        self.assertIn("Conservar certificación consumible por publicación",reusable)
        self.assertIn("name: ddd-audit-${{ github.run_id }}",reusable)
        self.assertIn('payload["workflow_run_id"]=int(run_id)',reusable)
        self.assertIn('payload["source_territorial_run_id"]',reusable)
        self.assertIn("latest_validated.run_id",publisher)

    def test_internal_pipeline_uses_functional_visible_names(self):
        engine=(WF/"producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        for forbidden in (
            "name: M01 ·","name: M02 ·","name: M03 ·","name: M04 ·",
            "name: M05 ·","name: M06 ·","name: M07 ·","name: M08 ·",
            "name: Auditoría geométrica M06",
        ):
            self.assertNotIn(forbidden,engine)
        self.assertIn("name: Consolidación territorial",engine)
        self.assertIn("name: Auditoría geométrica de la consolidación territorial",engine)

if __name__=="__main__":
    unittest.main()
