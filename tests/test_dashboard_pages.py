import unittest
from pathlib import Path
from herramientas.generar_estado_dashboard import build

ROOT=Path(__file__).resolve().parents[1]
MANUAL=ROOT/".github/workflows/desplegar-visor-publico.yml"
REUSABLE=ROOT/".github/workflows/_reutilizable-publicar-sitio.yml"

class DashboardPages(unittest.TestCase):
    def test_dashboard_fuente_y_snapshot_publicado_existen(self):
        for base in (ROOT/"dashboard",ROOT/"publicado/dashboard"):
            for name in ("index.html","app.js","styles.css"):
                self.assertTrue((base/name).is_file())
        self.assertTrue((ROOT/"publicado/dashboard/status.json").is_file())

    def test_dashboard_se_genera_desde_catalogo(self):
        payload=build(ROOT,"2025")
        self.assertEqual(payload["schema"],"ddd-estado-operativo/2.1")
        galicia=next(r for r in payload["territories"] if r["territory_id"]=="galicia")
        self.assertEqual(galicia["g"],"green")
        self.assertEqual(galicia["re"],"green")
        self.assertTrue(galicia["run_id"])
        self.assertGreaterEqual(payload["kpis"]["complete"],1)
        self.assertTrue(payload["latest_validated"]["run_id"])

    def test_publicador_manual_y_reutilizable_estan_separados(self):
        manual=MANUAL.read_text(encoding="utf-8"); reusable=REUSABLE.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",manual); self.assertIn("workflow_call:",manual)
        self.assertIn("workflow_call:",reusable); self.assertNotIn("workflow_dispatch:",reusable)
        self.assertIn("pagina_publicar:",manual); self.assertIn("- Dashboard operativo",manual)
        self.assertIn("- Visor territorial",manual); self.assertIn("- Sitio completo",manual)

    def test_produccion_automatica_preserva_dashboard_promovido(self):
        reusable=REUSABLE.read_text(encoding="utf-8")
        self.assertIn("cp -R publicado/dashboard/. /tmp/site-candidate/dashboard/",reusable)
        self.assertIn("with: {path: /tmp/site-candidate}",reusable)
        self.assertNotIn("cp dashboard/index.html",reusable)

    def test_promocion_dashboard_es_explicita_y_trazable(self):
        manual=MANUAL.read_text(encoding="utf-8")
        for token in ("generar_estado_operativo","orchestracion/estado_operativo.json","README.md","cp dashboard/index.html dashboard/app.js dashboard/styles.css publicado/dashboard/"):
            self.assertIn(token,manual)
        self.assertIn('git commit -m "chore: sincronizar estado operativo antes de publicar"',manual)
        self.assertIn("for attempt in 1 2 3",manual)
        self.assertIn("git pull --rebase origin main && git push origin HEAD:main",manual)
        self.assertIn("No se pudo sincronizar el estado operativo antes de publicar.",manual)

    def test_visor_enlaza_dashboard(self):
        html=(ROOT/"visor/index.html").read_text(encoding="utf-8")
        self.assertIn('href="dashboard/"',html)

    def test_evidencia_oculta_de_publicacion_se_sube(self):
        reusable=REUSABLE.read_text(encoding="utf-8")
        self.assertIn("path: .ddd-publication",reusable)
        self.assertIn("include-hidden-files: true",reusable)

    def test_dashboard_no_expone_preflight(self):
        html=(ROOT/"dashboard/index.html").read_text(encoding="utf-8").lower()
        js=(ROOT/"dashboard/app.js").read_text(encoding="utf-8").lower()
        self.assertNotIn("preflight",html); self.assertNotIn("preflight",js); self.assertIn("validación",js)

if __name__=="__main__":
    unittest.main()
