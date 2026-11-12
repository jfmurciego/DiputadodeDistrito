# VERSIÓN: 1.0.0
# FECHA: 2026-11-08
# CAMBIOS: T-87, fichero nuevo.
# MOTIVO: la cadena de publicación resuelve el run origen desde el registro durable de la 00.
# ANTERIOR: ninguna (fichero nuevo)
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.resolver_cadena_publicacion import main, resolver

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows"


class ResolverCadenaPublicacionTests(unittest.TestCase):
    def test_reutilizar_publica_el_run_origen_del_m08(self):
        # Registro durable versionado: 00 «Reutilizar» 42421655965 de Huesca (M08 de 41194447427).
        r = resolver(ROOT, "42421655965")
        self.assertEqual(r["status"], "READY")
        self.assertEqual(r["territory_id"], "congreso_huesca")
        self.assertEqual(r["publish_run_id"], "41194447427")
        self.assertEqual(r["m06_run_id"], "41057319037")
        self.assertEqual(r["m06_artifact"], "ddd-state-41057319037-M06")
        self.assertIn("EJECUCION_REUTILIZADA_PUBLICAR_CON_PRODUCTION_RUN_ID=41194447427", r["notes"])

    def test_00_ejecutada_publica_su_propio_run(self):
        r = resolver(ROOT, "41346917857")
        self.assertEqual((r["status"], r["publish_run_id"], r["reused"]), ("READY", "41346917857", False))
        self.assertEqual(r["m06_artifact"], "ddd-state-41346917857-M06")

    def test_bloquea_sin_registro_o_con_puerta_04_no_validada(self):
        self.assertEqual(resolver(ROOT, "1")["reasons"], ["REGISTRO_00_AUSENTE"])
        self.assertEqual(resolver(ROOT, "abc")["reasons"], ["PRODUCTION_RUN_ID_NO_NUMERICO"])
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "territorios/x/evidencia/ejecuciones_completas"
            d.mkdir(parents=True)
            (d / "7.json").write_text(json.dumps({"territory_id": "x", "status": "SUCCESS", "phases": [
                {"name": "02 · G", "validation_decision": "VALIDADO", "phase_decision": "PASS", "run_id": 7, "artifact": "a"},
                {"name": "04 · I", "validation_decision": "BLOQUEADO", "phase_decision": None, "run_id": 7, "artifact": None},
            ]}), encoding="utf-8")
            r = resolver(Path(tmp), "7")
            self.assertEqual((r["status"], r["reasons"]), ("BLOCK", ["PUERTA_04_NO_VALIDADA"]))
            self.assertEqual(main(["--root", tmp, "--run-id", "7"]), 2)


class CadenaPublicacionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.wf = yaml.safe_load((WF / "cadena-publicacion.yml").read_text(encoding="utf-8"))

    def test_simulacion_por_defecto_y_publicar_solo_con_modo_explicito(self):
        inputs = self.wf[True]["workflow_dispatch"]["inputs"]
        self.assertEqual(inputs["modo"]["default"], "simulacion")
        for job in ("visor", "version_mapa"):
            self.assertIn("needs.resolver.outputs.publicar == 'true'", self.wf["jobs"][job]["if"])

    def test_visor_y_mapa_reciben_el_mismo_run_y_el_mismo_sha(self):
        visor = self.wf["jobs"]["visor"]
        mapa = self.wf["jobs"]["version_mapa"]
        self.assertEqual(visor["uses"], "./.github/workflows/desplegar-visor-publico.yml")
        self.assertEqual(mapa["uses"], "./.github/workflows/publicar-version-mapa.yml")
        self.assertEqual(visor["with"]["production_run_id"], "${{ needs.resolver.outputs.publish_run_id }}")
        self.assertEqual(mapa["with"]["production_run_id"], "${{ needs.resolver.outputs.publish_run_id }}")
        self.assertEqual(visor["with"]["source_sha"], mapa["with"]["source_sha"])
        self.assertEqual(visor["with"]["source_sha"], "${{ needs.resolver.outputs.source_sha }}")


if __name__ == "__main__":
    unittest.main()
