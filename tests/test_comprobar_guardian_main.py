"""Pruebas del guardián de main (marcas de conflicto y numeración del registro)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from herramientas.comprobar_guardian_main import (
    comprobar_marcas,
    comprobar_registro,
    marcas_en_texto,
    siguiente,
)

# Las marcas se construyen en tiempo de ejecución para que este fichero no las contenga.
OPEN, SEP, CLOSE = "<" * 7, "=" * 7, ">" * 7


def _cabecera(version: str, anterior: str) -> str:
    return f"<!--\nNombre: Registro de cambios DDD\nVersión: {version}\nFecha: 2026-11-07\nAnterior: {anterior}\n-->\n\n## entrada\n"


class Marcas(unittest.TestCase):
    def test_bloque_completo_detectado(self):
        texto = f"a\n{OPEN} HEAD\nb\n{SEP}\nc\n{CLOSE} rama\nd\n"
        self.assertEqual(marcas_en_texto(texto), [2, 4, 6])

    def test_separador_suelto_no_es_marca(self):
        self.assertEqual(marcas_en_texto(f"Título\n{SEP}\ntexto\n"), [])

    def test_marca_de_cierre_suelta_detectada(self):
        self.assertEqual(marcas_en_texto(f"x\n{CLOSE} main\n"), [2])

    def test_comprobar_marcas_sobre_ficheros(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "limpio.md").write_text("ok\n", encoding="utf-8")
            (raiz / "roto.md").write_text(f"{OPEN} HEAD\n{SEP}\n{CLOSE} x\n", encoding="utf-8")
            (raiz / "binario.bin").write_bytes(b"\0" + OPEN.encode())
            errores = comprobar_marcas(sorted(raiz.iterdir()), raiz)
        self.assertEqual(len(errores), 3)
        self.assertTrue(all("roto.md" in e for e in errores))


class Registro(unittest.TestCase):
    def _repo(self, actual: str, previa: str, nombre_previa: str | None = None) -> Path:
        raiz = Path(tempfile.mkdtemp())
        nombre = nombre_previa or previa
        rel = f"legacy/docs/REGISTRO_DE_CAMBIOS_v{nombre}_t00_20261107.md"
        (raiz / "legacy/docs").mkdir(parents=True)
        (raiz / "docs").mkdir()
        (raiz / rel).write_text(_cabecera(previa, "legacy/docs/otro.md"), encoding="utf-8")
        (raiz / "docs/REGISTRO_DE_CAMBIOS.md").write_text(_cabecera(actual, rel), encoding="utf-8")
        return raiz

    def test_siguiente(self):
        self.assertEqual(siguiente("1.0.94"), "1.0.95")
        self.assertEqual(siguiente("1.0.9"), "1.0.10")

    def test_consecutivo_pasa(self):
        self.assertEqual(comprobar_registro(self._repo("1.0.95", "1.0.94")), [])

    def test_salto_falla(self):
        errores = comprobar_registro(self._repo("1.0.96", "1.0.94"))
        self.assertEqual(len(errores), 1)
        self.assertIn("no consecutiva", errores[0])

    def test_repetido_falla(self):
        self.assertTrue(comprobar_registro(self._repo("1.0.94", "1.0.94")))

    def test_nombre_y_cabecera_del_predecesor_discrepan(self):
        errores = comprobar_registro(self._repo("1.0.95", "1.0.94", nombre_previa="1.0.93"))
        self.assertTrue(any("el nombre dice" in e for e in errores))

    def test_predecesor_inexistente_falla(self):
        raiz = self._repo("1.0.95", "1.0.94")
        for f in (raiz / "legacy/docs").iterdir():
            f.unlink()
        self.assertIn("falta la copia legacy", comprobar_registro(raiz)[0])


if __name__ == "__main__":
    unittest.main()
