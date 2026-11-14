#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-301: la P50 versiona la composición sección→distrito de cada M06 canónico que publica."""
from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import composicion_m06 as cm  # noqa: E402

WORKFLOW = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")


def _m06(distritos: dict[int, tuple[int, int]]) -> bytes:
    gj = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"district_id": d, "section_count": n, "district_pop": p}, "geometry": None}
        for d, (n, p) in distritos.items()]}
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x_m06_distritos.geojson", json.dumps(gj))
    return b.getvalue()


CSV = "CUSEC_KEY,district_id,section_pop\n0400100001,0,100\n0400100002,0,50\n0400100003,1,70\n"


class PublicarComposicion(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.run = self.tmp / "production" / "555"
        self.run.mkdir(parents=True)
        (self.run / "x_m06_composicion_distritos.csv").write_text(CSV, encoding="utf-8")
        self.salida = self.tmp / "composicion"

    def _desc(self, nombre: str, territorio: str, m06: bytes) -> dict:
        f = self.tmp / nombre
        f.write_bytes(m06)
        return {"kind": "canonical_m06", "territory_id": territorio, "run_id": "555", "local_source": str(f)}

    def _escribir(self, descs) -> Path:
        p = self.tmp / "desc.json"
        p.write_text(json.dumps(descs), encoding="utf-8")
        return p

    def test_escribe_composicion_y_manifiesto(self):
        m06 = _m06({0: (2, 150), 1: (1, 70)})
        r = cm.publicar(self._escribir([self._desc("a.zip", "aut01", m06)]), self.run, self.salida)
        self.assertEqual(r, {"hechos": ["aut01"], "no_recuperados": {}})
        cuerpo = (self.salida / "runs" / "aut01_555.csv").read_bytes()
        self.assertEqual(cuerpo.decode(), "seccion,distrito,poblacion\n0400100001,0,100\n0400100002,0,50\n0400100003,1,70\n")
        man = json.loads((self.salida / "MANIFEST_RUNS.json").read_text(encoding="utf-8"))["ficheros"]["runs/aut01_555.csv"]
        self.assertEqual(man["sha256_csv"], hashlib.sha256(cuerpo).hexdigest())
        self.assertEqual(man["sha256_m06"], hashlib.sha256(m06).hexdigest())
        self.assertEqual(man["secciones"], 3)

    def test_territorio_que_no_cuadra_se_declara_y_no_se_pierde_otro(self):
        bueno = self._desc("a.zip", "aut01", _m06({0: (2, 150), 1: (1, 70)}))
        malo = self._desc("b.zip", "aut02", _m06({0: (9, 999)}))
        p = self._escribir([bueno, malo])
        r = cm.publicar(p, self.run, self.salida)
        self.assertEqual(r["hechos"], ["aut01"])
        self.assertEqual(list(r["no_recuperados"]), ["aut02"])
        self.assertTrue((self.salida / "runs" / "aut01_555.csv").is_file())
        self.assertFalse((self.salida / "runs" / "aut02_555.csv").exists())
        self.assertEqual(cm.main(["--descriptores", str(p), "--origen", str(self.run), "--salida", str(self.tmp / "s2")]), 44)

    def test_ignora_escenarios_y_m08(self):
        d = self._desc("a.zip", "aut01", _m06({0: (2, 150), 1: (1, 70)}))
        d["kind"] = "scenario_m06"
        self.assertEqual(cm.publicar(self._escribir([d]), self.run, self.salida), {"hechos": [], "no_recuperados": {}})

    def test_reutiliza_el_fichero_con_id_viejo_si_existe(self):
        (self.salida / "runs").mkdir(parents=True)
        viejo = self.salida / "runs" / "andalucia_555.csv"
        viejo.write_text("x", encoding="utf-8")
        cm.publicar(self._escribir([self._desc("a.zip", "aut01", _m06({0: (2, 150), 1: (1, 70)}))]), self.run, self.salida)
        self.assertTrue(viejo.read_text().startswith("seccion,"))
        self.assertFalse((self.salida / "runs" / "aut01_555.csv").exists())


class FlujoP50(unittest.TestCase):
    def test_workflow_extrae_antes_de_crear_blobs_y_persiste(self):
        self.assertIn("herramientas/composicion_m06.py --descriptores", WORKFLOW)
        self.assertLess(WORKFLOW.index("composicion_m06.py --descriptores"), WORKFLOW.index("Promover productos a blob persistente"))
        self.assertIn('datos_abiertos datos/composicion)', WORKFLOW)
        self.assertIn('git add -A -- "$PUBLICATION_REGISTRY" datos/resultados datos_abiertos datos/composicion', WORKFLOW)
        self.assertNotIn("set +e", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
