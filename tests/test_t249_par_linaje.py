#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del par M06/M08 por linaje (T-249)
VERSIÓN: 1.0.0 · FECHA: 2026-11-11 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: linaje por mismo run o por manifiesto del run del M08 (02 = run del M06, 04 = propio run en success); la P50
  (`candidate`) rechaza un M06 sin su M08 o con un M08 de otro linaje; datos abiertos empareja por linaje.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
import generar_datos_abiertos as da  # noqa: E402
import linaje_m06_m08 as L  # noqa: E402

T = "nac22"  # T-220: el generador filtra por el ámbito NAC del resolutor (un id fuera de la tabla no es nacional)


def prod(kind, run, n):
    return {"kind": kind, "territory_id": T, "territory_label": "Congreso Soria", "run_id": run, "blob_sha": n * 40,
            "sha256": n * 64}


class Linaje(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.root = Path(self._d.name)

    def tearDown(self):
        self._d.cleanup()

    def manifiesto(self, run, r02, r04, res="success"):
        d = self.root / "territorios" / T / "evidencia" / "ejecuciones_completas"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{run}.json").write_text(json.dumps({"phases": [
            {"name": "02 · Generación", "run_id": int(r02), "result": "skipped"},
            {"name": "04 · Incorporación", "run_id": int(r04), "result": res}]}))

    def check(self, base, entries):
        from herramientas.registro_publicaciones_visor import check_pairs
        check_pairs({"products": base + entries}, entries, self.root)

    def test_acreditado_por_manifiesto(self):
        self.manifiesto("7", "5", "7")
        self.assertEqual(L.m06_run_acreditado("7", T, self.root), "5")
        self.manifiesto("8", "5", "8", "failure")
        self.assertIsNone(L.m06_run_acreditado("8", T, self.root))
        self.assertIsNone(L.m06_run_acreditado("9", T, self.root))

    def test_m06_solo_se_rechaza(self):
        viejo = [prod("canonical_m06", "3", "a"), prod("canonical_m08", "3", "b")]
        with self.assertRaisesRegex(ValueError, "PAR_INCOMPLETO.*M08 3 no es del linaje del M06 5"):
            self.check(viejo, [prod("canonical_m06", "5", "c")])
        with self.assertRaisesRegex(ValueError, "PAR_INCOMPLETO.*sin M08"):
            self.check([], [prod("canonical_m06", "5", "c")])

    def test_par_mismo_run_o_cadena(self):
        self.check([], [prod("canonical_m06", "5", "c"), prod("canonical_m08", "5", "d")])
        self.manifiesto("7", "5", "7")
        self.check([prod("canonical_m06", "5", "c")], [prod("canonical_m08", "7", "d")])

    def test_m08_de_otro_linaje_se_rechaza(self):
        self.manifiesto("7", "4", "7")
        with self.assertRaisesRegex(ValueError, "PAR_INCOMPLETO"):
            self.check([prod("canonical_m06", "5", "c")], [prod("canonical_m08", "7", "d")])

    def test_sin_entradas_canonicas_no_comprueba(self):
        self.check([prod("canonical_m06", "5", "c")], [])

    def test_datos_abiertos_empareja_por_linaje(self):
        self.manifiesto("7", "5", "7")
        reg = self.root / "reg.json"
        reg.write_text(json.dumps({"products": [prod("canonical_m06", "5", "c"), prod("canonical_m06", "9", "e"),
                                                prod("canonical_m08", "7", "d")]}))
        p6, p8 = da.pares_vigentes(reg, root=self.root)[T]
        self.assertEqual((p6["run_id"], p8["run_id"]), ("5", "7"))


if __name__ == "__main__":
    unittest.main()
