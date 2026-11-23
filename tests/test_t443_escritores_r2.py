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
            k, km = "fuentes/por-territorio/nacionales/soria/2025/paquete.zip", "fuentes/por-territorio/nacionales/soria/2025/manifiesto.json"
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


class EdicionInmutable(unittest.TestCase):
    def test_otro_paquete_en_la_misma_edicion_falla_y_no_pisa(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            carpeta = td / "pkg"
            carpeta.mkdir()
            (carpeta / "bundle.zip").write_bytes(b"bundle")
            h = hashlib.sha256(b"bundle").hexdigest()
            (carpeta / "manifest.json").write_text(json.dumps({"path": "bundle.zip", "sha256": h}), encoding="utf-8")
            k = "fuentes/por-territorio/nacionales/soria/2025/paquete.zip"
            subidas = []
            args = argparse.Namespace(territorio="nac42", paquete=str(carpeta), run="1", out=str(td / "out"))
            with mock.patch.dict("os.environ", {"R2_BUCKET": "bk", "R2_ACCOUNT_ID": "a"}), \
                    mock.patch.object(b, "validar_paquete_p10", lambda t, c: None), \
                    mock.patch.object(b, "_identidad_contrato", lambda t: {"package_sha256": h}), \
                    mock.patch.object(b, "_anios_fuentes", lambda t: ("2025", "2023", "2023")), \
                    mock.patch("herramientas.archivar_artefactos_r2.r2_cliente",
                               lambda bk, c: (lambda x: "0" * 64 if x == k else None, lambda *a: subidas.append(a))):
                self.assertEqual(b.archivar_p10(args), 1)
            self.assertEqual(subidas, [])


class LecturaP10(unittest.TestCase):
    def _zip(self, td: Path, nombre: str, contenido: bytes) -> tuple[Path, str]:
        import zipfile
        z = td / nombre
        h = hashlib.sha256(contenido).hexdigest()
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("bundle.zip", contenido)
            zf.writestr("manifest.json", json.dumps({"path": "bundle.zip", "sha256": h}))
        return z, h

    def test_ruta_nueva_con_otro_contrato_cae_a_la_clave_por_package_sha256(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            otro, _ = self._zip(td, "otro.zip", b"contrato anterior")
            bueno, h = self._zip(td, "bueno.zip", b"contrato vigente")
            objetos = {"fuentes/por-territorio/nacionales/soria/2025/paquete.zip": otro, f"arc-e/paquetes-p10/{h}.zip": bueno}
            vistas = []

            def cp(origen, destino):
                k = origen.split("/", 3)[3]
                vistas.append(k)
                Path(destino).write_bytes(objetos[k].read_bytes())
            with mock.patch.dict("os.environ", {"R2_BUCKET": "bk"}), mock.patch.object(b, "_identidad_contrato", lambda t: {"package_sha256": h}), \
                    mock.patch.object(b, "_anios_fuentes", lambda t: ("2025", "2023", "2023")), mock.patch.object(b, "_r2_cp", cp), \
                    mock.patch("herramientas.seleccionar_paquete_fuentes.validate_prepared_package", lambda *a, **k: (True, [])):
                pkg = b.paquete_p10_desde_r2("nac42", td / "out")
                self.assertEqual(vistas, list(objetos))
                self.assertEqual((pkg / "bundle.zip").read_bytes(), b"contrato vigente")
                objetos.pop(f"arc-e/paquetes-p10/{h}.zip")  # sin respaldo: el paquete de otro contrato sigue siendo un fallo cerrado
                with self.assertRaises(b.PaqueteP10Corrupto):
                    b.paquete_p10_desde_r2("nac42", td / "out2")


class ArchivoOrigen(unittest.TestCase):
    def test_superado_falla_en_vez_de_devolver_otro_run(self):
        from herramientas import archivo_origen as ao
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "orchestracion").mkdir()
            from herramientas import rutas_r2
            k = rutas_r2.ruta_estado("aut06", "ddd-audit-1")
            r2 = {k: {"sha256": "f" * 64, "run": "41037133399", "bytes": 1}}
            art = {"id": 5, "name": "ddd-audit-41037133327", "expired": False, "expires_at": "2026-12-01T00:00:00Z",
                   "workflow_run": {"id": 41037133327}}
            with self.assertRaisesRegex(ValueError, "ARCHIVO_R2_SUPERADO"):
                ao.archivar_uno(art, ao.ar.rutas_r2.ti.id_legacy("aut06"), root, lambda a, p: p.write_bytes(b"x"), lambda k: None,
                                lambda *a: self.fail("no debe subir"), "bk", r2_cab=r2.get)


class Espejos(unittest.TestCase):
    def test_fuentes_inmutables(self):
        self.assertIn("ya existe en R2 con otro sha256 (fuentes inmutables): no se sube", PS1_GALICIA)
        self.assertIn("$mclave = 'fuentes/xunta/2024/manifiesto.json'", PS1_GALICIA)
        self.assertIn("elseif ($e1 -eq 'distinto' -and $clave.StartsWith('fuentes/')) { throw", PS1_INE)

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
