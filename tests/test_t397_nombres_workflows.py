"""T-397 (D-155): nombres visibles de los workflows vivos (lista de Actions sin basura).

Literales de la decisión, no recalculados del código. Excepción temporal: las `_reutilizable-*` (workflow_call, «Interno · P<n>0 …»,
fijadas por test_corte_5_0_0_equivalencias); se renombrarán aparte.
"""
import re
import unittest
from pathlib import Path

WF = Path(__file__).resolve().parents[1] / ".github" / "workflows"
NOMBRE = re.compile(r"^name:\s*(.+?)\s*$", re.M)


def nombre(f: Path) -> str:
    return NOMBRE.search(f.read_text(encoding="utf-8")).group(1).strip("'\"")


class NombresWorkflows(unittest.TestCase):
    def vivos(self):
        return [f for f in sorted(WF.glob("*.yml")) if not f.name.startswith("_reutilizable-")]

    def test_prefijo_p_y_sin_interno(self):
        for f in self.vivos():
            n = nombre(f)
            self.assertRegex(n, r"^P\d0 ", f"{f.name}: {n!r} sin prefijo P<n>0")
            self.assertNotIn("Interno", n, f.name)

    def test_nombres_fijados(self):
        self.assertEqual(nombre(WF / "auto-merge.yml"), "P90 Automático — Fusión automática")
        self.assertEqual(nombre(WF / "revisor-pr.yml"), "P90 Automático — Revisor de PR")

    def test_nombres_unicos(self):
        ns = [nombre(f) for f in WF.glob("*.yml")]
        self.assertEqual(len(ns), len(set(ns)), ns)

    def test_nadie_busca_los_nombres_viejos(self):
        for f in WF.glob("*.yml"):
            t = f.read_text(encoding="utf-8")
            for lista in re.findall(r"^\s*workflows:\s*\[(.*?)\]", t, re.M | re.S):
                self.assertNotIn("Fusión automática", lista, f.name)
                self.assertNotIn("Revisor de PR", lista, f.name)


if __name__ == "__main__":
    unittest.main()
