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
        self.assertEqual(payload["schema"],"ddd-estado-operativo/2.2")
        galicia=next(r for r in payload["territories"] if r["territory_id"]=="aut12")

        catalog=yaml.safe_load((ROOT/"configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
        row=next(r for r in catalog["territories"] if r["territory_id"]=="aut12")
        state=row["editions"]["2025"]

        def receipt(kind):
            rel=(state.get("evidence") or {}).get(kind)
            self.assertTrue(rel)
            data=json.loads((ROOT/rel).read_text(encoding="utf-8"))
            self.assertEqual(data["territory_id"],"aut12")
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
        # T-247b: regla de linaje (#354). El M08 cuenta solo si es del run del M06 vigente o si el manifiesto de SU run
        # acredita la 02 con ese M06 y la 04 en success; si no (p. ej. M06 nuevo con la 04 de la cadena aún pendiente),
        # el dashboard debe dar «yellow». Antes bastaba con electoral_product_available, y la campaña lo rompía.
        def m08_del_m06_vigente():
            if str(electoral["run_id"])==str(territorial["run_id"]):
                return True
            path=ROOT/f"territorios/aut12/evidencia/ejecuciones_completas/{electoral['run_id']}.json"
            if not path.is_file():
                return False
            fases={str(p.get("name",""))[:2]:p for p in json.loads(path.read_text(encoding="utf-8")).get("phases") or []}
            f02,f04=fases.get("02") or {},fases.get("04") or {}
            return (str(f02.get("run_id"))==str(territorial["run_id"]) and str(f04.get("run_id"))==str(electoral["run_id"])
                    and f04.get("result")=="success")
        expected_re="green" if state.get("electoral_product_available") and m08_del_m06_vigente() else "yellow"

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

    def test_dashboard_conserva_estado_operativo_y_anade_activacion_completa(self):
        html=(ROOT/"dashboard/index.html").read_text(encoding="utf-8")
        self.assertIn('data-view="operational"',html)
        self.assertIn('data-view="activation"',html)
        self.assertIn('id="view-operational"',html)
        self.assertIn('id="view-activation"',html)
        self.assertIn("Mapa de Activación",html)
        self.assertIn("Cadena de Activación",html)
        self.assertIn("Cuadro maestro de Activación",html)

    def test_activacion_presenta_solo_su_fase(self):
        html=(ROOT/"dashboard/index.html").read_text(encoding="utf-8")
        activation=html.split('id="view-activation"',1)[1]
        for forbidden in ("M04","M06","Generación territorial","Publicación opcional"):
            self.assertNotIn(forbidden,activation)
        for expected in (
            "Población",
            "Secciones / geometría",
            "Resultados electorales",
            "Desfase temporal relevante",
            "Estado de Activación",
            "Qué falta para activarlo",
        ):
            self.assertIn(expected,activation)

    def test_activacion_tiene_seis_tarjetas_mapa_ficha_y_embudo(self):
        js=(ROOT/"dashboard/app.js").read_text(encoding="utf-8")
        for label in (
            "Activadas",
            "Activables ahora",
            "Pendientes de fuente territorial",
            "Pendientes de fuente electoral",
            "Bloqueadas",
            "Sustitución temporal acreditada",
        ):
            self.assertIn(label,js)
        self.assertIn("MAP_POINTS",js)
        for territory_id in (
            "aut01","aut02","aut03","aut04","aut05",
            "aut06","aut07","aut08","aut09",
            "aut10","aut11","aut12","aut13","aut14",
            "aut15","aut16","aut17","aut18","aut19",
        ):
            self.assertIn(territory_id,js)
        for step in (
            "Legislatura resuelta",
            "Años resueltos",
            "Fuente territorial",
            "Fuente electoral",
            "Par durable",
        ):
            self.assertIn(step,js)

    def test_dashboard_activacion_solo_presenta_dictamen_y_par_durable(self):
        js=(ROOT/"dashboard/app.js").read_text(encoding="utf-8")
        self.assertIn("data.source_readiness",js)
        self.assertIn("row.activation",js)
        self.assertIn("row.territorial",js)
        self.assertIn("row.electoral",js)
        self.assertIn("row.next_steps",js)
        self.assertNotIn("resolver_preparacion_legislatura",js)
        self.assertNotIn("population_year_required ===",js)
        self.assertNotIn("section_year_required ===",js)

    def test_assets_fuente_y_publicados_del_dashboard_estan_sincronizados(self):
        for name in ("index.html","app.js","styles.css"):
            self.assertEqual(
                (ROOT/"dashboard"/name).read_text(encoding="utf-8"),
                (ROOT/"publicado/dashboard"/name).read_text(encoding="utf-8"),
                name,
            )

    def test_dashboard_no_expone_preflight(self):
        html=(ROOT/"dashboard/index.html").read_text(encoding="utf-8").lower()
        js=(ROOT/"dashboard/app.js").read_text(encoding="utf-8").lower()
        self.assertNotIn("preflight",html); self.assertNotIn("preflight",js); self.assertIn("validación",js)

if __name__=="__main__":
    unittest.main()
