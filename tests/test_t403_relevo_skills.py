"""T-403 (D-160): cada skill de rol documenta el relevo de chats y CLAUDE.md respeta su tope de líneas."""
from __future__ import annotations

import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ROLES = ("planificador", "coordinador", "operador", "implementador", "ingeniero-motor")


class RelevoSkills(unittest.TestCase):
    def test_cada_skill_de_rol_tiene_seccion_relevo(self):
        for rol in ROLES:
            texto = (RAIZ / ".claude" / "skills" / rol / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("\n## Relevo\n", texto, rol)
            self.assertIn("70 %", texto, rol)

    def test_operador_no_hereda_autorizaciones(self):
        texto = (RAIZ / ".claude" / "skills" / "operador" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("NUNCA hereda una autorización", texto)

    def test_claude_md_bajo_100_lineas(self):
        n = len((RAIZ / "CLAUDE.md").read_text(encoding="utf-8").splitlines())
        self.assertLess(n, 100, n)


if __name__ == "__main__":
    unittest.main()
