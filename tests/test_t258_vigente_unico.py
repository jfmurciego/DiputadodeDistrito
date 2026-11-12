#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-258: un único vigente, el publicado en el visor, para la competición (generadores.Vigente, --reanudar, P30) y la
aceptación (bateria_motor.composicion_publicada / indicadores). Fixtures deterministas, sin red ni motor."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from ddd_motor2 import produccion as p30  # noqa: E402
from ddd_motor2.competir import _mismo_vigente  # noqa: E402
from ddd_motor2.generadores import Vigente  # noqa: E402
from ddd_motor2.vigente import vigente_publicado  # noqa: E402
from herramientas import bateria_motor as bm  # noqa: E402


def repo(root: Path, runs: dict, ficheros: dict, manifest: dict | None = None) -> Path:
    """runs = {territorio: [(run, fecha)]}; ficheros = {ruta relativa: texto}."""
    (root / "orchestracion").mkdir(parents=True, exist_ok=True)
    prods = [{"kind": "canonical_m06", "territory_id": t, "run_id": str(r), **({"election_date": f} if f else {})}
             for t, lista in runs.items() for r, f in lista]
    prods.append({"kind": "canonical_m08", "territory_id": "t", "run_id": "999"})
    (root / "orchestracion" / "publicaciones_visor.json").write_text(json.dumps({"products": prods}), encoding="utf-8")
    for rel, txt in ficheros.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(txt, encoding="utf-8")
    if manifest is not None:
        (root / "datos" / "composicion").mkdir(parents=True, exist_ok=True)
        (root / "datos" / "composicion" / "MANIFEST.json").write_text(json.dumps({"territorios": manifest}))
    return root


VIEJO, NUEVO = "seccion,distrito,poblacion\n1,1,1\n", "seccion,distrito,poblacion\n1,2,1\n"


class VigenteUnico(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())

    def resolver(self, t: str):
        """El vigente de la competición y el de la aceptación, que deben ser el mismo fichero."""
        with mock.patch.object(bm, "ROOT", self.d):
            acept = bm.composicion_publicada(t)
        comp = Vigente(root=self.d).ruta(t)
        self.assertEqual((acept[0], acept[1]), (comp[0], comp[1]), t)
        return vigente_publicado(t, self.d)

    def test_el_del_visor_y_no_el_csv_de_otro_run(self):
        repo(self.d, {"t": [(10, None), (20, "2023-07-23"), (900, "2026-05-31")]},
             {"datos/composicion/t.csv": VIEJO, "datos/composicion/runs/t_20.csv": NUEVO,
              "datos/composicion/runs/t_900.csv": VIEJO}, {"t": {"run_id": "10"}})
        v = self.resolver("t")
        self.assertEqual((v.ruta, v.run, v.motivo), (self.d / "datos/composicion/runs/t_20.csv", "20", ""))

    def test_csv_canonico_solo_si_es_del_run_publicado(self):
        repo(self.d, {"a": [(20, None)], "b": [(20, None)]},
             {"datos/composicion/a.csv": VIEJO, "datos/composicion/b.csv": VIEJO},
             {"a": {"run_id": "20"}, "b": {"run_id": "10"}})
        self.assertEqual(self.resolver("a").ruta, self.d / "datos/composicion/a.csv")
        b = self.resolver("b")  # el publicado (20) no está versionado: sin vigente comparable, nunca el del run 10
        self.assertEqual((b.ruta, b.run), (None, "20"))
        self.assertIn("no tiene composición versionada", b.motivo)
        with mock.patch.object(bm, "ROOT", self.d):
            self.assertEqual(bm.composicion_publicada("b"), (None, "20"))

    def test_sin_registro_en_el_visor_no_hay_vigente(self):
        repo(self.d, {}, {"datos/composicion/c.csv": VIEJO}, {"c": {"run_id": "5"}})
        c = self.resolver("c")
        self.assertEqual((c.ruta, c.run), (None, None))
        self.assertIn("sin mapa publicado en el visor", c.motivo)

    def test_el_generador_vigente_sin_publicado_no_compite_y_dice_por_que(self):
        repo(self.d, {"b": [(20, None)]}, {"datos/composicion/b.csv": VIEJO}, {"b": {"run_id": "10"}})
        from ddd_motor2.competicion import EntradaTerritorio
        s = Vigente(root=self.d).generar(EntradaTerritorio("b", {}, self.d / "g.json"), None, self.d / "out")
        self.assertEqual(s.estado, "SIN_VIGENTE")
        self.assertIn("run 20", s.detalle)

    def test_reanudar_compara_con_el_publicado(self):
        repo(self.d, {"t": [(20, None)]}, {"datos/composicion/t.csv": VIEJO, "datos/composicion/runs/t_20.csv": NUEVO})
        h_pub = hashlib.sha256(NUEVO.encode()).hexdigest()
        h_viejo = hashlib.sha256(VIEJO.encode()).hexdigest()
        with mock.patch("ddd_motor2.generadores.ROOT", self.d):
            self.assertTrue(_mismo_vigente("t", {"vigente": {"sha256_origen": h_pub}}, "D8"))
            self.assertFalse(_mismo_vigente("t", {"vigente": {"sha256_origen": h_viejo}}, "D8"))

    def test_lo_que_elige_el_vigente_entra_en_la_huella_motor2(self):
        files = p30.huella_motor()["engine_files"]
        self.assertIn("orchestracion/publicaciones_visor.json", files)
        self.assertIn("datos/composicion/MANIFEST.json", files)
        self.assertTrue(any(f.startswith("datos/composicion/runs/") for f in files))
        self.assertIn("ddd_motor2/vigente.py", files)


if __name__ == "__main__":
    unittest.main()
