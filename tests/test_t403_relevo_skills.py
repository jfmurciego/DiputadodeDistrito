"""T-403 (D-160): cada skill de rol documenta el relevo de chats y CLAUDE.md respeta su tope de líneas."""
from __future__ import annotations

import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ROLES = ("planificador", "coordinador", "operador", "implementador", "ingeniero-motor")
CREAN = ("planificador", "coordinador", "operador")
NO_CREAN = ("implementador", "ingeniero-motor")


def relevo(rol: str) -> str:
    texto = (RAIZ / ".claude" / "skills" / rol / "SKILL.md").read_text(encoding="utf-8")
    assert "\n## Relevo\n" in texto, f"{rol}: falta «## Relevo»"
    return texto.split("\n## Relevo\n", 1)[1]


class RelevoSkills(unittest.TestCase):
    def test_todos_tienen_seccion_umbral_y_get_session(self):
        for rol in ROLES:
            sec = relevo(rol)
            for clave in ("70 %", "get_session", "autocompact_state.threshold"):
                self.assertIn(clave, sec, f"{rol}: {clave}")

    def test_los_tres_roles_crean_sucesora_con_limite_de_linaje(self):
        for rol in CREAN:
            sec = relevo(rol)
            for clave in ("create_session", "lineage.depth", "profundidad 7", "NO crees sucesora",
                          "D-122", "/cierre-sesion", "TRASPASO_"):
                self.assertIn(clave, sec, f"{rol}: {clave}")
            self.assertIn("a los otros dos roles", sec, rol)

    def test_implementador_e_ingeniero_no_crean_sucesora(self):
        for rol in NO_CREAN:
            sec = relevo(rol)
            self.assertIn("No crees sucesora", sec, rol)
            self.assertIn("Coordinador te releva", sec, rol)
            self.assertNotIn("create_session", sec, rol)  # control negativo

    def test_operador_regla_completa(self):
        sec = relevo("operador")
        for clave in ("UNA VEZ", "sucesor inmediato", "caducidad de la ficha",
                      "NUNCA hereda una autorización", "no lanzas, no fusionas ni publicas", "docs/autorizaciones/"):
            self.assertIn(clave, sec, clave)

    def test_control_negativo_otros_roles_sin_regla_d52_de_operador(self):
        for rol in ("planificador", "coordinador"):
            self.assertNotIn("UNA VEZ", relevo(rol), rol)

    def test_claude_md_bajo_100_lineas(self):
        n = len((RAIZ / "CLAUDE.md").read_text(encoding="utf-8").splitlines())
        self.assertLess(n, 100, n)


if __name__ == "__main__":
    unittest.main()
