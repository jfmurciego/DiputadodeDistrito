# -*- coding: utf-8 -*-
"""T-199: dimensión de elección en el registro del visor (compatible hacia atrás) y FECHA parametrizada.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.1 · FECHA: 2026-11-12 · ESTADO: candidato · CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.1 · FECHA: 2026-11-12 · ESTADO: candidato · ANTERIOR: legacy/tests/test_t199_eleccion_registro_fecha_v1.0.0_20261112.py
"""
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
from herramientas import registro_publicaciones_visor as rpv  # noqa: E402
import resultados_partidos as rp  # noqa: E402


def entrada(run, **extra):
    sha = "%064x" % int(run)
    e = {"id": f"m08-congreso_huesca-{run}", "asset_type": "electoral_product", "source_type": "repository_blob",
         "repository": "o/r", "blob_sha": sha[-40:], "immutable_location": f"github-git-blob://o/r/{sha[-40:]}",
         "territory_id": "nac22", "sha256": sha, "kind": "canonical_m08", "run_id": str(run), "canonical": True}
    e.update(extra)
    return e


def registro(*entradas):
    return {"schema": rpv.SCHEMA, "products": list(entradas), "ensembles": []}


class Registro(unittest.TestCase):
    def test_entrada_antigua_se_lee_igual_y_es_de_2023(self):
        e = entrada(1)
        rpv.validate_registry(registro(e))
        self.assertEqual(rpv.eleccion_de(e), "2023-07-23")

    def test_registro_real_valida_y_sin_dimension(self):
        reg = json.loads((ROOT / "orchestracion/publicaciones_visor.json").read_text("utf-8"))
        rpv.validate_registry(reg)
        self.assertTrue(all(rpv.eleccion_de(e) == "2023-07-23" for e in reg["products"] if "election_date" not in e))

    def test_dos_canonicos_misma_familia_conviven_si_difiere_la_eleccion(self):
        nueva = entrada(9, election_date="2026-11-29", election_id="congreso_huesca_2026-11-29")
        rpv.validate_registry(registro(entrada(1), nueva))
        with self.assertRaises(ValueError):
            rpv.validate_registry(registro(entrada(1), entrada(2)))  # mismo caso sin dimensión: sigue rechazado
        with self.assertRaises(ValueError):
            rpv.validate_registry(registro(nueva, entrada(10, election_date="2026-11-29")))

    def test_dimension_invalida(self):
        for extra in ({"election_date": "29-11-2026"}, {"election_date": "2026-13-45"},
                      {"election_id": "congreso_huesca_2026-11-29"},
                      {"election_date": "2026-11-29", "election_id": "congreso_huesca_2023-07-23"}):
            with self.assertRaises(ValueError, msg=str(extra)):
                rpv.validate_registry(registro(entrada(1, **extra)))

    def test_guardar_y_cargar_conserva_la_dimension(self):
        t = Path(tempfile.mkdtemp()) / "r.json"
        rpv.save_registry(t, registro(entrada(9, election_date="2026-11-29")))
        self.assertEqual(rpv.eleccion_de(rpv.load_registry(t)["products"][0]), "2026-11-29")


class Descriptores(unittest.TestCase):
    def _descriptores(self, **kw):
        meta = {"territory_id": "nac22", "territory_label": "Huesca", "expected_districts": 2,
                "production_status": {"decision": "PASS"}}
        with mock.patch.object(rpv, "production_metadata", return_value=meta), \
                mock.patch.object(rpv, "read_json", return_value={"decision": "PASS"}), \
                mock.patch.object(rpv, "certification_status", return_value="CERTIFIED"), \
                mock.patch.object(rpv, "first", side_effect=lambda root, pat: Path("x.zip") if "m08" in pat else None):
            return rpv.production_descriptors(Path("."), "7", **kw)

    def test_propaga_la_eleccion(self):
        d = self._descriptores(election_date="2026-11-29", election_id="congreso_huesca_2026-11-29")
        self.assertEqual((d[0]["election_date"], d[0]["election_id"]), ("2026-11-29", "congreso_huesca_2026-11-29"))

    def test_sin_eleccion_no_añade_campos(self):
        self.assertNotIn("election_date", self._descriptores()[0])

    def test_eleccion_imposible_falla(self):
        with self.assertRaises(ValueError):
            self._descriptores(election_date="2026-99-99")


class Fecha(unittest.TestCase):
    def test_fecha_2026_sale_del_yaml(self):
        self.assertEqual(rp.fecha_generales_2026(), "2026-11-29")
        self.assertEqual(rp.resolver_fecha("2026"), "2026-11-29")
        self.assertEqual(rp.resolver_fecha(None), "2023-07-23")
        self.assertEqual(rp.resolver_fecha("2019-11-10"), "2019-11-10")
        with self.assertRaises(ValueError):
            rp.resolver_fecha("ayer")

    def test_yaml_sin_fecha_o_con_fecha_imposible(self):
        d = Path(tempfile.mkdtemp())
        sin, mala, ausente = d / "sin.yaml", d / "mala.yaml", d / "no_existe.yaml"
        sin.write_text("schema: x\n", encoding="utf-8")
        mala.write_text("election_date: '2026-99-99'\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "election_date"):
            rp.fecha_generales_2026(sin)
        with self.assertRaisesRegex(ValueError, "2026-99-99"):
            rp.fecha_generales_2026(mala)
        with self.assertRaisesRegex(ValueError, "no_existe.yaml"):
            rp.fecha_generales_2026(ausente)
        for malo in ("2026-99-99", "2026-02-30", "2026/11/29"):
            with self.assertRaises(ValueError, msg=malo):
                rp.resolver_fecha(malo)

    def test_contratos_por_fecha(self):
        d = Path(tempfile.mkdtemp()) / "c.yaml"
        d.write_text("contracts:\n  a_2023:\n    territory_id: t1\n    election_date: '2023-07-23'\n"
                     "  a_2026:\n    territory_id: t1\n    election_date: '2026-11-29'\n", encoding="utf-8")
        self.assertEqual(rp.contratos(d)["t1"]["election_id"], "a_2023")
        self.assertEqual(rp.contratos(d, "2026-11-29")["t1"]["election_id"], "a_2026")

    def test_vigentes_por_eleccion_no_se_pisan(self):
        t = Path(tempfile.mkdtemp()) / "r.json"
        t.write_text(json.dumps(registro(entrada(1), entrada(9, election_date="2026-11-29"))), encoding="utf-8")
        self.assertEqual(rp.vigentes_eleccion(t)["nac22"]["run_id"], "1")
        self.assertEqual(rp.vigentes_eleccion(t, "2026-11-29")["nac22"]["run_id"], "9")


if __name__ == "__main__":
    unittest.main()
