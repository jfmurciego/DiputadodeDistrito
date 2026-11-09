# -*- coding: utf-8 -*-
"""T-125: el mapa 350 (congreso350_*) nunca entra en latest_validated ni en el registro de publicaciones.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Causa real: la 05 42642161355 registró m06/m08 de congreso350_valladolid (run 42613899978) como canonical.
"""
import json
import sys
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
import generar_estado_operativo as geo  # noqa: E402
from herramientas import registro_publicaciones_visor as rpv  # noqa: E402


def fila(t, run):
    return {"territory_id": t, "run_id": str(run)}


class LatestValidated(unittest.TestCase):
    def test_gemelo_350_con_run_mas_reciente_no_gana(self):
        completo = [fila("congreso_alava", 100), fila("congreso350_valladolid", 999)]
        self.assertEqual(geo.elegir_latest(completo, completo)["territory_id"], "congreso_alava")

    def test_si_complete_solo_tiene_350_cae_a_territorial_publicable(self):
        r = geo.elegir_latest([fila("congreso350_soria", 900)], [fila("congreso350_soria", 900), fila("aragon", 50)])
        self.assertEqual(r["territory_id"], "aragon")

    def test_solo_350_no_hay_latest(self):
        self.assertIsNone(geo.elegir_latest([fila("congreso350_madrid", 5)], [fila("congreso350_madrid", 5)]))

    def test_sin_run_id_se_ignora(self):
        self.assertEqual(geo.elegir_latest([fila("a", ""), fila("b", 3)], [])["territory_id"], "b")


class Registro(unittest.TestCase):
    def setUp(self):
        self.registro = json.loads((ROOT / "orchestracion/publicaciones_visor.json").read_text("utf-8"))

    def test_anadir_territorio_350_se_rechaza(self):
        with self.assertRaisesRegex(ValueError, "mapa 350"):
            rpv.make_candidate(self.registro, [{"territory_id": "congreso350_valladolid", "kind": "canonical_m06"}])
        with self.assertRaisesRegex(ValueError, "mapa 350"):
            rpv.rechazar_mapa_350("congreso350_madrid")

    def test_territorio_normal_no_se_rechaza(self):
        rpv.rechazar_mapa_350("congreso_valladolid")
        rpv.rechazar_mapa_350("madrid")

    def test_las_entradas_350_ya_registradas_siguen_validando(self):
        ya = [e for e in self.registro["products"] if str(e.get("territory_id", "")).startswith("congreso350_")]
        self.assertTrue(ya, "el registro actual conserva las entradas de congreso350_valladolid (decisión del propietario)")
        rpv.validate_registry(self.registro)
        self.assertEqual(len(rpv.make_candidate(self.registro, [])["products"]), len(self.registro["products"]))

    def test_describe_production_rechaza_350(self):
        with unittest.mock.patch.object(rpv, "production_metadata", return_value={"territory_id": "congreso350_soria"}):
            with self.assertRaisesRegex(ValueError, "mapa 350"):
                rpv.production_descriptors(ROOT, "123")


class Workflow05(unittest.TestCase):
    def test_sin_run_explicito_no_resuelve_latest_validated(self):
        t = (ROOT / ".github/workflows/desplegar-visor-publico.yml").read_text("utf-8")
        self.assertNotIn("latest_validated.run_id", t)
        self.assertIn("modo solo sitio", t)


if __name__ == "__main__":
    unittest.main()
