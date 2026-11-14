#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-305: la P50 restaura el estado M08/M06 desde R2 si Actions ya no lo tiene (R2 simulado)."""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import restaurar_estado_r2 as r2  # noqa: E402

RUN = "43204696160"
ENV = {"R2_BUCKET": "cubo", "R2_ACCOUNT_ID": "cta"}


def _paquete() -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("estado/aut01_m08_distritos_resultados.geojson.zip", b"geo")
        z.writestr("estado/production_status.json", "{}")
        z.writestr("estado/../../escapa.txt", "x")
        z.writestr("MANIFEST_MINIMO.json", "{}")
    return b.getvalue()


class RestaurarR2(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.datos = _paquete()
        self.man = self.tmp / "archivo_r2.json"
        self._man(hashlib.sha256(self.datos).hexdigest())

    def _man(self, sha, estado="M08"):
        clave = f"aut01/{RUN}/ddd-minimo-{RUN}-{estado}.zip"
        self.man.write_text(json.dumps({"artefactos": {clave: {
            "run_id": RUN, "artefacto": f"ddd-minimo-{RUN}-{estado}", "sha256": sha}}}), encoding="utf-8")
        self.clave = clave

    def _cp(self, origen, destino, extra=None):
        assert origen == f"s3://cubo/{self.clave}"
        Path(destino).write_bytes(self.datos)

    def _run(self, **kw):
        with mock.patch.dict("os.environ", ENV):
            return r2.restaurar(RUN, self.tmp / "root", manifiesto=self.man, cp=self._cp, **kw)

    def test_solo_en_r2_se_restaura(self):
        self.assertEqual(self._run(), 0)
        base = self.tmp / "root" / f"ddd-state-{RUN}-M08"
        self.assertEqual((base / "aut01_m08_distritos_resultados.geojson.zip").read_bytes(), b"geo")
        self.assertTrue((base / "production_status.json").is_file())
        self.assertFalse((self.tmp / "escapa.txt").exists())

    def test_sha256_alterado_se_rechaza(self):
        self.datos = self.datos + b"x"
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            rc = self._run()
        self.assertEqual(rc, 53)
        self.assertIn("RESTAURAR_R2_SHA256", err.getvalue())
        self.assertFalse((self.tmp / "root" / f"ddd-state-{RUN}-M08").exists())

    def test_sin_el_en_ninguno_falla_con_mensaje(self):
        self.man.write_text(json.dumps({"artefactos": {}}), encoding="utf-8")
        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            rc = self._run()
        self.assertEqual(rc, 3)
        for t in ("RESTAURAR_R2_AUSENTE", RUN, f"ddd-minimo-{RUN}-M08", f"ddd-minimo-{RUN}-M06"):
            self.assertIn(t, err.getvalue())

    def test_cae_al_m06_si_no_hay_m08(self):
        self._man(hashlib.sha256(self.datos).hexdigest(), "M06")
        self.assertEqual(self._run(), 0)
        self.assertTrue((self.tmp / "root" / f"ddd-state-{RUN}-M06").is_dir())

    def test_sin_credenciales_error_claro(self):
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            rc = r2.restaurar(RUN, self.tmp / "root", manifiesto=self.man, cp=self._cp)
        self.assertEqual(rc, 3)
        self.assertIn("RESTAURAR_R2_SIN_CREDENCIALES", err.getvalue())

    def test_workflow_orden_y_secretos_solo_en_el_paso(self):
        wf = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        self.assertLess(wf.index("gh run download \"$run\" \"${pats[@]}\""), wf.index("--pattern 'ddd-*'"))
        self.assertLess(wf.index("--pattern 'ddd-*'"), wf.index("python herramientas/restaurar_estado_r2.py"))
        job_env = wf.split("\n    env:\n", 1)[1].split("\n    steps:", 1)[0]
        self.assertNotIn("R2_", job_env)
        self.assertIn("secrets.R2_ACCESS_KEY_ID", wf)


if __name__ == "__main__":
    unittest.main()
