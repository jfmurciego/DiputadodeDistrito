# -*- coding: utf-8 -*-
"""T-368: resolutores de P70 Archivo (`herramientas/p70_resolver.py`) y listado de R2 (`herramientas/listar_r2.py`).

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Los valores esperados son literales; los datos de entrada son sintéticos (sin estado vivo del repositorio salvo la lista de poda aprobada).
"""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))
import listar_r2 as lr  # noqa: E402
import p70_resolver as pr  # noqa: E402


class Resolutores(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        (self.d / "orchestracion").mkdir()
        (self.d / "configuracion").mkdir()

    def catalogo(self, filas):
        (self.d / pr.CATALOGO).write_text(json.dumps({"territorios": filas}), encoding="utf-8")

    def test_run_p10_del_catalogo(self):
        self.catalogo({"aut01": {"fuente_territorial": {"run_id": "111"}}, "aut02": {"fuente_territorial": {}}})
        self.assertEqual(pr.run_p10(self.d, "aut01"), "111")
        with self.assertRaisesRegex(ValueError, "P70_SIN_PAQUETE_P10"):
            pr.run_p10(self.d, "aut02")

    def test_territorio_invalido_se_rechaza(self):
        self.catalogo({})
        for malo in ("", "aut01 aut02", "../x", "AUT01;ls"):
            with self.assertRaisesRegex(ValueError, "P70_TERRITORIO_INVALIDO"):
                pr.run_p10(self.d, malo)

    def test_fecha_de_eleccion(self):
        (self.d / pr.VISOR).write_text(json.dumps({"products": [{"election_date": "2026-05-17"}, {"election_date": "2026-05-17"}, {"election_date": "2026-02-08"}]}), encoding="utf-8")
        self.assertEqual(pr.fecha_eleccion(self.d, "2023-07"), "2023-07-23")
        self.assertEqual(pr.fecha_eleccion(self.d, "2026-05"), "2026-05-17")
        for malo in ("2026-13", "2026-5", "20260517", "2025-01"):
            with self.assertRaises(ValueError):
                pr.fecha_eleccion(self.d, malo)

    def test_edicion_exige_la_eleccion_registrada(self):
        (self.d / pr.REGISTRO).write_text("territories:\n  aut01: {election_date: '2026-05-17'}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "P70_ELECCION_NO_VIGENTE"):
            pr.edicion(self.d, "aut01", "2023-07")
        with self.assertRaisesRegex(ValueError, "P70_ELECCION_INVALIDA"):
            pr.edicion(self.d, "aut01", "2026")

    def test_sha_de_poda_aprobado_y_control_negativo(self):
        self.assertEqual(pr.sha_poda(ROOT), "40eef3b56c28625a1cb4a0eeef157f85de657fcebac744cc1e6a329858f0a98e")  # literal fijado por el propietario (T-145)
        for rel in (pr.LISTA_PODA, pr.SHA_PODA):
            (self.d / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.d / pr.LISTA_PODA).write_bytes(b"clave\nx\n")
        (self.d / pr.SHA_PODA).write_text(hashlib.sha256(b"otra lista").hexdigest() + "\n")
        with self.assertRaisesRegex(ValueError, "P70_LISTA_NO_APROBADA"):  # lista cambiada sin cambiar el sha aprobado
            pr.sha_poda(self.d)
        (self.d / pr.SHA_PODA).write_text("no-es-un-sha\n")
        with self.assertRaises(ValueError):
            pr.sha_poda(self.d)


class Listado(unittest.TestCase):
    def test_resumen_por_carpeta_y_total(self):
        objs = [{"Key": "a/1.zip", "Size": 6 * 10**9}, {"Key": "a/2.zip", "Size": 10**9}, {"Key": "b/x", "Size": 10**9}, {"Key": "suelto.json", "Size": 5}]
        r = lr.resumir(objs)
        self.assertEqual(list(r["carpetas"]), ["a", "b", "(raíz)"])  # por tamaño descendente
        self.assertEqual(r["carpetas"]["a"], {"bytes": 7 * 10**9, "objetos": 2})
        self.assertEqual(r["total_bytes"], 8 * 10**9 + 5)
        self.assertEqual(r["porcentaje"], 80.0)
        self.assertIn("80.0 % de 10 GB", lr.tabla(r))

    def test_vacio(self):
        self.assertEqual(lr.resumir([])["total_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
