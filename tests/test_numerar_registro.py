"""Registro por fragmentos (T-46): numeración automática y comprobaciones del guardián. Sin red."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))

import comprobar_guardian_main as g  # noqa: E402
import numerar_registro as nr  # noqa: E402

CABECERA = """<!--
Nombre: Registro de cambios DDD
Versión: 1.0.105
Fecha: 2026-11-07
Alcance: T-46 — registro sin conflictos
Estado: candidato
Cambios/motivo: última entrada con número manual
Anterior: legacy/docs/REGISTRO_DE_CAMBIOS_v1.0.104_t44_20261107.md
-->

## 2026-11-07 — T-46 — Registro sin conflictos

Texto histórico.
"""
PREVIA = "<!--\nNombre: Registro de cambios DDD\nVersión: 1.0.104\n-->\n"


def entrada(fecha, tarea, titulo, cuerpo="Causa, cambio y pruebas. PR #999."):
    return f"## {fecha} — {tarea} — {titulo}\n\n{cuerpo}\n"


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)
        (self.raiz / "docs/registro").mkdir(parents=True)
        (self.raiz / "legacy/docs").mkdir(parents=True)
        (self.raiz / nr.REGISTRO).write_text(CABECERA, encoding="utf-8")
        (self.raiz / "legacy/docs/REGISTRO_DE_CAMBIOS_v1.0.104_t44_20261107.md").write_text(PREVIA, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def frag(self, nombre, texto):
        (self.raiz / "docs/registro" / nombre).write_text(texto, encoding="utf-8")


class Numeracion(Base):
    def test_numera_en_orden_con_copia_legacy_y_es_idempotente(self):
        self.frag("2026-11-08_claude-t48-ci.md", entrada("2026-11-08", "T-48", "Revisor en CI"))
        self.frag("2026-11-07_claude-t47-b.md", entrada("2026-11-07", "T-47", "Otra"))
        self.frag("README.md", "# Cómo escribir una entrada\n")
        hechos = nr.numerar(self.raiz, "2026-11-09")
        self.assertEqual(hechos, [("1.0.106", "docs/registro/2026-11-07_claude-t47-b.md"),
                                  ("1.0.107", "docs/registro/2026-11-08_claude-t48-ci.md")])
        texto = (self.raiz / nr.REGISTRO).read_text(encoding="utf-8")
        self.assertIn("Versión: 1.0.107", texto)
        self.assertIn("Alcance: T-48 — Revisor en CI", texto)
        self.assertIn("Texto histórico.", texto)
        self.assertEqual([v for v, _ in nr.indice(texto)], ["1.0.107", "1.0.106"])
        for v in ("1.0.105", "1.0.106"):
            self.assertTrue((self.raiz / f"legacy/docs/REGISTRO_DE_CAMBIOS_v{v}_registro_20261109.md").is_file())
        self.assertEqual(g.comprobar_registro(self.raiz), [])
        self.assertEqual(g.comprobar_fragmentos(self.raiz), [])
        self.assertEqual(nr.numerar(self.raiz, "2026-11-09"), [])
        self.assertEqual((self.raiz / nr.REGISTRO).read_text(encoding="utf-8"), texto)

    def test_comprobar_no_escribe(self):
        self.frag("2026-11-08_x.md", entrada("2026-11-08", "T-48", "X"))
        self.assertEqual(len(nr.numerar(self.raiz, "2026-11-09", escribir=False)), 1)
        self.assertEqual((self.raiz / nr.REGISTRO).read_text(encoding="utf-8"), CABECERA)

    def test_fragmento_mal_formado_no_se_numera(self):
        self.frag("2026-11-08_x.md", "Versión: 1.0.106\n" + entrada("2026-11-08", "T-48", "X"))
        with self.assertRaises(nr.FormatoError):
            nr.numerar(self.raiz, "2026-11-09")
        self.assertEqual((self.raiz / nr.REGISTRO).read_text(encoding="utf-8"), CABECERA)


class Guardian(Base):
    def casos_malos(self):
        return {
            "2026-11-08_Rama-Con-Mayus.md": entrada("2026-11-08", "T-1", "a"),
            "2026-11-08_fecha.md": entrada("2026-11-09", "T-1", "fecha distinta"),
            "2026-11-08_sin-cuerpo.md": "## 2026-11-08 — T-1 — sin cuerpo\n",
            "2026-11-08_titulo.md": "# Título suelto\n\ncuerpo\n",
            "2026-11-08_numero.md": entrada("2026-11-08", "T-1", "a", "<!-- Versión: 1.0.106 -->"),
        }

    def test_formato_de_fragmentos(self):
        for nombre, texto in self.casos_malos().items():
            self.frag(nombre, texto)
        errores = g.comprobar_fragmentos(self.raiz)
        for nombre in self.casos_malos():
            with self.subTest(nombre=nombre):
                self.assertTrue(any(nombre in e for e in errores), errores)

    def test_indice_a_fichero_inexistente_o_numero_mayor(self):
        texto = CABECERA.replace("-->\n", f"-->\n\n{nr.INICIO}\n- 1.0.200 · [x](registro/2026-11-01_falta.md)\n{nr.FIN}\n", 1)
        (self.raiz / nr.REGISTRO).write_text(texto, encoding="utf-8")
        errores = g.comprobar_fragmentos(self.raiz)
        self.assertTrue(any("no existe" in e for e in errores))
        self.assertTrue(any("mayor que la Versión" in e for e in errores))

    def test_repositorio_real_pasa(self):
        self.assertEqual(g.comprobar_fragmentos(ROOT), [])


if __name__ == "__main__":
    unittest.main()
