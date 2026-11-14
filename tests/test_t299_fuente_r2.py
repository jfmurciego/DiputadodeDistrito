"""T-299: ZIP por mesa de Infoelectoral en R2 (ARC-E) con sha256 del índice; la 03 lo lee de R2 y conserva el release como respaldo."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from herramientas import fuente_r2 as f

ROOT = Path(__file__).resolve().parents[1]
SHA_MESA = "e78fc231326a03cf67bbec87b7100ea0c8c46859daa1b2a631c06daaaf1717f8"  # contrato Infoelectoral (huella del ZIP oficial)


class FuenteR2(unittest.TestCase):
    def test_indice_y_contrato_coinciden(self):
        ficha = f.ficha("02202307_MESA.zip")
        self.assertEqual(ficha["sha256"], SHA_MESA)
        self.assertEqual(ficha["clave"], f"arc-e/fuentes/interior/02202307_MESA_{SHA_MESA[:12]}.zip")
        self.assertEqual(ficha["bytes"], 4578794)
        c = yaml.safe_load((ROOT / "configuracion/contratos_infoelectoral.yaml").read_text(encoding="utf-8"))["contracts"]
        self.assertTrue(any(x.get("source_sha256") == SHA_MESA and x["mirror"]["asset"] == "02202307_MESA.zip" for x in c.values()))

    def _env(self):
        return mock.patch.dict("os.environ", {"R2_BUCKET": "bk", "R2_ACCOUNT_ID": "acc"})

    def test_baja_de_r2_y_verifica(self):
        datos = b"zip de prueba"
        with tempfile.TemporaryDirectory() as td, self._env():
            idx = Path(td) / "i.json"
            idx.write_text('{"fuentes":{"x.zip":{"clave":"arc-e/fuentes/interior/x_1.zip","sha256":"%s"}}}' % hashlib.sha256(datos).hexdigest())
            vistas = []

            def cp(o, d, extra=None):
                vistas.append(o)
                Path(d).write_bytes(datos)
            self.assertEqual(f.bajar("x.zip", Path(td) / "o.zip", cp, idx), 0)
            self.assertEqual(vistas, ["s3://bk/arc-e/fuentes/interior/x_1.zip"])

    def test_sha_distinto_53_y_sin_fichero(self):
        with tempfile.TemporaryDirectory() as td, self._env():
            idx = Path(td) / "i.json"
            idx.write_text('{"fuentes":{"x.zip":{"clave":"k","sha256":"%s"}}}' % ("0" * 64))
            cp = lambda o, d, extra=None: Path(d).write_bytes(b"otra cosa")  # noqa: E731
            self.assertEqual(f.bajar("x.zip", Path(td) / "o.zip", cp, idx), 53)
            self.assertFalse((Path(td) / "o.zip").exists())

    def test_sin_objeto_credenciales_o_indice_devuelve_3(self):
        with tempfile.TemporaryDirectory() as td:
            idx = Path(td) / "i.json"
            idx.write_text('{"fuentes":{"x.zip":{"clave":"k","sha256":"%s"}}}' % ("0" * 64))

            def sin_objeto(o, d, extra=None):
                raise OSError("NoSuchKey")
            with self._env():
                self.assertEqual(f.bajar("x.zip", Path(td) / "o.zip", sin_objeto, idx), 3)
                self.assertEqual(f.bajar("otro.zip", Path(td) / "o.zip", sin_objeto, idx), 3)
            with mock.patch.dict("os.environ", {}, clear=True):
                self.assertEqual(f.bajar("x.zip", Path(td) / "o.zip", sin_objeto, idx), 3)

    def test_subir_exige_el_sha_del_indice(self):
        with tempfile.TemporaryDirectory() as td, self._env():
            idx = Path(td) / "i.json"
            idx.write_text('{"fuentes":{"x.zip":{"clave":"k","sha256":"%s"}}}' % hashlib.sha256(b"ok").hexdigest())
            z = Path(td) / "z"
            z.write_bytes(b"mal")
            llamadas = []
            self.assertEqual(f.subir("x.zip", z, lambda *a, **k: llamadas.append(a), idx), 53)
            z.write_bytes(b"ok")
            self.assertEqual(f.subir("x.zip", z, lambda *a, **k: llamadas.append(a), idx), 0)
            self.assertEqual(len(llamadas), 1)

    def test_la_03_lee_r2_primero_y_conserva_el_release(self):
        txt = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        i = txt.index("fuente_r2.py bajar")
        self.assertGreater(txt.index("curl --fail --location", i), i)
        self.assertGreater(txt.index("gh release download", i), i)
        self.assertIn("fuente_r2.py subir", txt)


if __name__ == "__main__":
    unittest.main()
