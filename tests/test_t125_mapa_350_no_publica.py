# -*- coding: utf-8 -*-
"""T-125: el mapa 350 (congreso350_*) nunca entra en latest_validated ni en el registro de publicaciones.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.1 · FECHA: 2026-11-12 · ESTADO: candidato · ANTERIOR: legacy/tests/test_t125_mapa_350_no_publica_v1.0.0_20261112.py
CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
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
        completo = [fila("nac01", 100), fila("congreso350_valladolid", 999)]
        self.assertEqual(geo.elegir_latest(completo, completo)["territory_id"], "nac01")

    def test_si_complete_solo_tiene_350_cae_a_territorial_publicable(self):
        r = geo.elegir_latest([fila("congreso350_soria", 900)], [fila("congreso350_soria", 900), fila("aut02", 50)])
        self.assertEqual(r["territory_id"], "aut02")

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
        rpv.rechazar_mapa_350("nac47")
        rpv.rechazar_mapa_350("aut13")

    def test_las_entradas_350_ya_registradas_siguen_validando(self):
        # independiente del registro vivo (T-126 retira las dos de Valladolid): se inyecta una entrada 350 sintética
        import copy
        base = next(e for e in self.registro["products"] if e["kind"] == "canonical_m06")
        ya = copy.deepcopy(base)
        ya.update(id="m06-congreso350_x-1", territory_id="congreso350_x", run_id="1", blob_sha="e" * 40, sha256="f" * 64)
        for k, v in list(ya.items()):  # la ubicación inmutable se deriva del blob_sha
            if isinstance(v, str) and base["blob_sha"] in v:
                ya[k] = v.replace(base["blob_sha"], "e" * 40)
        reg = copy.deepcopy(self.registro)
        reg["products"].append(ya)
        rpv.validate_registry(reg)  # una entrada 350 ya presente sigue validando (grandfather)
        # lo que sí se exige: añadir otra 350 se rechaza aunque ya haya una, y no se toca la existente
        with self.assertRaisesRegex(ValueError, "mapa 350"):
            rpv.make_candidate(reg, [{"territory_id": "congreso350_y", "kind": "canonical_m06"}])
        self.assertEqual(len(rpv.make_candidate(reg, [])["products"]), len(reg["products"]))

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
