# -*- coding: utf-8 -*-
"""T-443 (3/5): `bateria_motor archivar-p10` escribe en el árbol nuevo de R2 (D-188/D-190) con el manifiesto de la carpeta.

Archivista y P75: tests/test_archivar_artefactos_r2.py y tests/test_t418_p75.py. Espejos PowerShell: tests/test_t354_espejo_galicia.py y
tests/test_t356_espejo_ine_observatorio.py (sin pwsh en CI: se comprueba el texto).
"""
import argparse
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herramientas import bateria_motor as b  # noqa: E402

PS1_GALICIA = (ROOT / "herramientas/espejo_galicia_r2.ps1").read_text(encoding="utf-8")
PS1_INE = (ROOT / "herramientas/espejo_ine_observatorio_r2.ps1").read_text(encoding="ascii")


class ArchivarP10(unittest.TestCase):
    def test_paquete_y_manifiesto_en_fuentes_por_territorio(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            carpeta = td / "pkg"
            carpeta.mkdir()
            (carpeta / "bundle.zip").write_bytes(b"bundle")
            h = hashlib.sha256(b"bundle").hexdigest()
            (carpeta / "manifest.json").write_text(json.dumps({"path": "bundle.zip", "sha256": h}), encoding="utf-8")
            r2 = {}

            def sha(k):
                return r2.get(k, (None,))[0]

            def subir(k, ruta, hh):
                r2[k] = (hh, Path(ruta).read_bytes())
            args = argparse.Namespace(territorio="nac42", paquete=str(carpeta), run="44000000001", out=str(td / "out"))
            with mock.patch.dict("os.environ", {"R2_BUCKET": "bk", "R2_ACCOUNT_ID": "a"}), \
                    mock.patch.object(b, "validar_paquete_p10", lambda t, c: None), \
                    mock.patch.object(b, "_identidad_contrato", lambda t: {"package_sha256": h}), \
                    mock.patch("herramientas.archivar_artefactos_r2.r2_cliente", lambda bk, c: (sha, subir)):
                self.assertEqual(b.archivar_p10(args), 0)
            k, km = "fuentes/por-territorio/nacionales/soria/paquete.zip", "fuentes/por-territorio/nacionales/soria/manifiesto.json"
            self.assertEqual(sorted(r2), [km, k])
            man = json.loads(r2[km][1])
            self.assertEqual((man["run"], man["huella"]), ("44000000001", h))  # huella = package_sha256 del contrato
            self.assertEqual(man["ficheros"]["paquete.zip"]["sha256"], r2[k][0])
            reg = json.loads((td / "out" / "ARCHIVO_PAQUETES_P10.json").read_text(encoding="utf-8"))["nac42"]
            self.assertEqual((reg["clave"], reg["clave_anterior"]), (k, f"arc-e/paquetes-p10/{h}.zip"))
            # idempotente: misma huella → no resube
            n = dict(r2)
            with mock.patch.dict("os.environ", {"R2_BUCKET": "bk", "R2_ACCOUNT_ID": "a"}), \
                    mock.patch.object(b, "validar_paquete_p10", lambda t, c: None), \
                    mock.patch.object(b, "_identidad_contrato", lambda t: {"package_sha256": h}), \
                    mock.patch("herramientas.archivar_artefactos_r2.r2_cliente",
                               lambda bk, c: (sha, lambda *a: self.fail("resube sin cambios"))):
                self.assertEqual(b.archivar_p10(args), 0)
            self.assertEqual(r2, n)


class Espejos(unittest.TestCase):
    def test_galicia_al_arbol_nuevo_con_clave_anterior(self):
        self.assertIn('$clave = "fuentes/xunta/2024/galicia_parlamento_2024_$($f.id).csv"', PS1_GALICIA)
        self.assertIn('clave_anterior = $claveAnterior', PS1_GALICIA)
        self.assertIn("VERSIÓN 1.1.0", PS1_GALICIA.splitlines()[1])

    def test_ine_sin_clave_en_el_indice_va_al_arbol_nuevo(self):
        self.assertIn('$clave = "fuentes/ine/$anio/$($p.nombre)"', PS1_INE)
        self.assertIn('$clave = "fuentes/gobierno-vasco/$r0"', PS1_INE)
        self.assertNotIn("Substring(0, 12)).zip", PS1_INE)  # ya no se compone la clave vieja con sha12


if __name__ == "__main__":
    unittest.main()
