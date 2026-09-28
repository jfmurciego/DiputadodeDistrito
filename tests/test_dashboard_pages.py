import json
import re
import unittest

import yaml
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

        catalog=yaml.safe_load((ROOT/"configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
        row=next(r for r in catalog["territories"] if r["territory_id"]=="galicia")
        state=row["editions"]["2025"]

        def receipt(kind):
            rel=(state.get("evidence") or {}).get(kind)
            self.assertTrue(rel)
            data=json.loads((ROOT/rel).read_text(encoding="utf-8"))
            self.assertEqual(data["territory_id"],"galicia")
            self.assertEqual(str(data["edition"]),"2025")
            self.assertRegex(str(data["artifact_sha256"]).removeprefix("sha256:"),r"^[0-9a-f]{64}$")
            self.assertTrue(data["run_id"])
            return data

        territorial=receipt("territorial_product")
        electoral=receipt("electoral_product")
        pass_cert={"PASS","PASS_WITH_EXCEPTIONS","PASS_WITH_GOVERNED_EXCEPTIONS"}
        expected_g="green" if (
            state.get("territorial_product_available")
            and state.get("territorial_certification") in pass_cert
            and territorial.get("decision") in pass_cert
        ) else "yellow" if (
            state.get("territorial_product_available")
            or state.get("production_authorization") in {"AUTHORIZED","PREFLIGHT"}
        ) else "gray"
        expected_re="green" if state.get("electoral_product_available") and electoral else "yellow"

        self.assertEqual(galicia["g"],expected_g)
        self.assertEqual(galicia["re"],expected_re)
        expected_run=electoral["run_id"] if expected_re=="green" else territorial["run_id"]
        self.assertEqual(galicia["run_id"],expected_run)
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

    def test_promocion_dashboard_serializa_solo_la_escritura_compartida(self):
        manual=MANUAL.read_text(encoding="utf-8")
        self.assertIn("ddd-shared-operational-state",manual)
        self.assertIn("python -m herramientas.persistir_estado_operativo_compartido",manual)
        self.assertIn("--sync-dashboard-assets",manual)
        self.assertNotIn("git pull --rebase origin main",manual)

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
