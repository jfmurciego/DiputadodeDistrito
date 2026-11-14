"""T-298: la batería toma las fuentes nacionales del espejo (sha256 verificado) y nunca de ine.es; la entrada mínima en R2
se indexa por la identidad del contrato, no por el id del territorio."""
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import json

from herramientas import bateria_motor as b
from herramientas import podar_r2

ROOT = Path(__file__).resolve().parents[1]
# Valores independientes: medidos sobre la descarga real del INE (2026-11-14) y de inputs/partes/reconstruir_fuentes.sh.
SHA = {
    "seccionado_2023.zip": "7a15e700a4592d793230441cfcb4b72e40979998aef019ca644389271886bf1f",
    "seccionado_2024.zip": "df931fa0d372808eb81abb2f2645ed5ecccbd6ed397b85db656980748ddd6bf7",
    "seccionado_2025.zip": "55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4",
    "65034.csv.zip": "91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3",
}


class EspejoIne(unittest.TestCase):
    def test_ficha_de_las_cuatro_fuentes(self):
        f = json.loads((ROOT / "orchestracion/fuentes_r2.json").read_text(encoding="utf-8"))["fuentes"]
        self.assertEqual({k: v["sha256"] for k, v in f.items()}, SHA)
        for k, v in f.items():
            self.assertEqual(v["clave"], f"arc-e/fuentes/ine/{k.rsplit('.zip', 1)[0]}_{SHA[k][:12]}.zip")
            self.assertTrue(v["origen_url"].startswith("https://www.ine.es/") and v["descargado_en"] and v["bytes"])
        self.assertEqual(f["seccionado_2023.zip"]["bytes"], 64929708)

    def test_la_poda_no_puede_borrar_arc_e(self):
        for k in ("arc-e/fuentes/ine/seccionado_2023_7a15e700a459.zip", "arc-e/entradas-minimas/0123456789abcdef.zip"):
            self.assertIsNone(podar_r2._ESTADO.match(k))

    def _con_ficha(self, td: Path, contenido: bytes):
        import hashlib
        ficha = {"x.zip": {"clave": "arc-e/fuentes/ine/x.zip", "sha256": hashlib.sha256(contenido).hexdigest()}}
        return mock.patch.object(b, "_espejo", lambda: ficha)

    def test_toma_del_espejo_sin_red_y_sin_ine(self):
        def sin_red(*a, **k):
            raise AssertionError("acceso a red")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "espejo").mkdir()
            (td / "espejo/x.zip").write_bytes(b"datos")
            with self._con_ficha(td, b"datos"), mock.patch.dict("os.environ", {"DDD_ESPEJO_DIR": str(td / "espejo")}), \
                    mock.patch.object(socket, "socket", sin_red), mock.patch.object(b.urllib.request, "urlopen", sin_red), \
                    mock.patch.object(b.urllib.request, "urlretrieve", sin_red):
                p = b.obtener_fuente_nacional("x.zip", td / "nac")
                self.assertEqual(p.read_bytes(), b"datos")
                # segunda vez: ya está con su sha256, tampoco toca red
                self.assertEqual(b.obtener_fuente_nacional("x.zip", td / "nac"), p)

    def test_sha256_distinto_falla_y_no_deja_fichero(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "espejo").mkdir()
            (td / "espejo/x.zip").write_bytes(b"otra cosa")
            with self._con_ficha(td, b"datos"), mock.patch.dict("os.environ", {"DDD_ESPEJO_DIR": str(td / "espejo")}):
                with self.assertRaises(b.FuenteNacionalError):
                    b.obtener_fuente_nacional("x.zip", td / "nac")
            self.assertFalse((td / "nac/x.zip").exists())

    def test_sin_copia_ni_r2_falla_sin_ir_al_ine(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            vistas = []

            def r2_caido(clave, dest):
                vistas.append(clave)
                raise OSError("sin R2")
            with self._con_ficha(td, b"datos"), mock.patch.dict("os.environ", {}, clear=False), \
                    mock.patch.object(b, "_bajar_r2", r2_caido):
                with self.assertRaises(b.FuenteNacionalError):
                    b.obtener_fuente_nacional("x.zip", td / "nac")
            self.assertEqual(vistas, ["arc-e/fuentes/ine/x.zip"])

    def test_solo_subir_fuentes_toca_el_ine(self):
        import inspect
        for f in (b.nacionales, b.obtener_fuente_nacional, b.entradas):
            self.assertNotIn("urlretrieve", inspect.getsource(f))
            self.assertNotIn("urlopen", inspect.getsource(f))

    def test_clave_r2_por_identidad_no_por_territorio(self):
        a = {"contrato": "territorios/aut01/config/aut01_2025.yaml", "contrato_sha256": "1", "package_sha256": "p", "compatibility_identity_sha256": "c"}
        o = {**a, "contrato": "territorios/otro/config/otro_2025.yaml", "contrato_sha256": "2"}
        self.assertEqual(b.clave_identidad(a), b.clave_identidad(o))
        self.assertNotEqual(b.clave_identidad(a), b.clave_identidad({**a, "package_sha256": "q"}))
        self.assertRegex(b.clave_identidad(a), r"^arc-e/entradas-minimas/[0-9a-f]{16}\.zip$")


if __name__ == "__main__":
    unittest.main()
