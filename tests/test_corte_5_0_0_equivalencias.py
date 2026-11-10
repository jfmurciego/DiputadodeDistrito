# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.1.0
# CAMBIOS 1.1.0: T-215 (paso 4 del corte), nombres v5: la 05 es «P50 Publicación» y la 06 «P30 Distritos — P33 Alternativas»
#   (siguen exigiendo `produccion`); el forense conserva el nombre viejo hasta el parche aparte de D-61 (única excepción).
# FECHA: 2026-11-10
# ANTERIOR: legacy/tests/test_corte_5_0_0_equivalencias_v1.0.0_20261110.py
"""T-198: guardas previas al corte 5.0.0 (D-61): referencias entre flujos y entornos de producción."""
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import generar_equivalencias_5_0_0 as gen  # noqa: E402

WF = ROOT / ".github" / "workflows"
NOMBRE_05 = "P50 Publicación"
NOMBRE_06 = "P30 Distritos — P33 Alternativas"
# D-61/DECISIÓN 3: el cambio de una línea de forense-00.yml («P00 Campaña») va en un parche aparte que exige la
# autorización expresa del propietario. Hasta entonces es la ÚNICA referencia a un flujo que ya no existe.
FORENSE_PENDIENTE = ("forense-00.yml", "00 Ejecución Completa del Proyecto")
FORENSE_PARCHEADO = ("forense-00.yml", "P00 Campaña")


def _nombres():
    out = {}
    for f in sorted(WF.glob("*.yml")):
        m = re.search(r"^name:\s*(.+?)\s*$", f.read_text(encoding="utf-8"), re.M)
        out[f.name] = m.group(1).strip("'\"") if m else None
    return out


class ReferenciasPorNombre(unittest.TestCase):
    def test_workflow_run_y_github_workflow_nombran_flujos_existentes(self):
        existentes = set(_nombres().values())
        encontradas = []
        for f in sorted(WF.glob("*.yml")):
            txt = "\n".join(l for l in f.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#"))
            refs = re.findall(r"""github\.workflow\s*==\s*(?:'([^']+)'|"([^"]+)")""", txt)
            refs = [a or b for a, b in refs]
            for lista in re.findall(r"^\s*workflows:\s*\[(.*?)\]", txt, re.M | re.S):
                refs += [a or b for a, b in re.findall(r"'([^']+)'|\"([^\"]+)\"", lista)]
            for r in refs:
                encontradas.append((f.name, r))
                if (f.name, r) != FORENSE_PENDIENTE:
                    self.assertIn(r, existentes, f"{f.name} nombra un flujo inexistente: {r!r}")
        forense = FORENSE_PARCHEADO if FORENSE_PARCHEADO in encontradas else FORENSE_PENDIENTE
        esperadas = sorted([
            ("auto-merge.yml", "Pruebas de la Plataforma"),
            ("desplegar-visor-publico.yml", NOMBRE_05),
            forense,
            ("generar-alternativas-territoriales.yml", NOMBRE_06),
            ("generar-alternativas-territoriales.yml", NOMBRE_06),
        ])
        self.assertEqual(sorted(encontradas), esperadas, "referencia por nombre nueva o perdida: revisa y actualiza la lista")

    def test_05_y_06_siguen_exigiendo_produccion(self):
        casos = {
            "desplegar-visor-publico.yml": (NOMBRE_05, 1),
            "generar-alternativas-territoriales.yml": (NOMBRE_06, 2),
        }
        for fich, (nombre, n) in casos.items():
            txt = (WF / fich).read_text(encoding="utf-8")
            self.assertEqual(_nombres()[fich], nombre)
            lineas = [l for l in txt.splitlines() if re.match(r"\s*environment:", l) and "produccion" in l]
            self.assertEqual(len(lineas), n, fich)
            for l in lineas:
                self.assertIn(f"github.workflow == '{nombre}'", l, fich)
                self.assertIn("workflow_dispatch", l)


class Equivalencias(unittest.TestCase):
    def test_documento_generado_al_dia(self):
        doc = ROOT / "docs" / "ARQUITECTURA" / "EQUIVALENCIAS_5_0_0.md"
        self.assertEqual(doc.read_text(encoding="utf-8"), gen.generar(), "ejecuta tests/generar_equivalencias_5_0_0.py")

    def test_recuentos_y_sufijo_350(self):
        self.assertEqual(len(gen.territorios()), 71)
        v = gen.variantes_350()
        self.assertEqual(len(v), 49)
        for viejo, padre, nuevo in v:
            self.assertTrue(viejo.startswith("congreso350_"))
            self.assertEqual(nuevo, padre.lower() + "-350")

    def test_flujos_de_la_tabla_existen_en_disco(self):
        nombres = _nombres()
        for fich, _, _, nombre_v5 in gen.FLUJOS:
            self.assertEqual(nombres.get(fich), nombre_v5, fich)

    def test_nombres_visibles_unicos_y_con_codigo_v5(self):
        """Lista de Actions: cada flujo del corte con código de fase o ARC/Interno, sin nombres repetidos."""
        nombres = _nombres()
        self.assertEqual(len(set(nombres.values())), len(nombres), "dos flujos con el mismo nombre visible")
        for fich, _, flujo, nombre_v5 in gen.FLUJOS:
            self.assertTrue(nombre_v5.startswith(flujo.split(" ")[0]), fich)
        self.assertEqual(nombres["mantenimiento-programado.yml"], "Automático — Mantenimiento")  # §b del corte
        internos = [n for f, n in nombres.items() if f.startswith("_reutilizable-")]
        self.assertTrue(internos and all(re.match(r"^Interno · P\d0 ", n) for n in internos), internos)


if __name__ == "__main__":
    unittest.main()
