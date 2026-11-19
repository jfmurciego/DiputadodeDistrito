"""T-397 (D-155): nombres visibles de los workflows vivos (lista de Actions sin basura).

T-397b (D-159): con botón (workflow_dispatch en la UI) → «P…» sin «_»; sin botón → «_P…» (al final de la lista).
Literales de la decisión, no recalculados del código. Las `_reutilizable-*` (workflow_call, «Interno · P<n>0 …») quedan fuera:
las fija test_corte_5_0_0_equivalencias y no tienen botón ni se buscan; renombrarlas exigiría tocar 3 ficheros compartidos y sus fixtures.
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

    CON_BOTON = {
        "gestor-campanas.yml": "P00 Campaña — Gestor", "ejecucion-completa-proyecto.yml": "P00 Campaña",
        "p10-fuentes.yml": "P10 Fuentes", "p20-distritos.yml": "P20 Distritos",
        "p30-resultados-electorales.yml": "P30 Resultados electorales", "p40-publicacion.yml": "P40 Publicación",
        "p50-publicacion-academica.yml": "P50 Publicación académica", "p70-archivo.yml": "P70 Archivo",
        "p80-verificacion-motor.yml": "P80 Verificación del motor",
        "p00-campana.yml": "P00 Campaña",  # T-379 PR 3 (diseño T-378 §9: mismo nombre que la 00 mientras convivan)
    }
    SIN_BOTON = {
        "activacion-por-eleccion.yml": "_P00 Campaña — Elección",
        "revisor-pr.yml": "_P90 Automático — Revisor de PR",
        "auto-merge.yml": "_P90 Automático — Fusión automática",
        "p00-cadena.yml": "_P00 Campaña — cadena de un territorio",  # T-379 PR 3: solo workflow_call
    }
    # Pendientes de T-379 2a (#888, turno exclusivo): se pasan a SIN_BOTON después de fusionarla.
    PENDIENTES_2A = {
        "preparacion-legislatura-vigente.yml": "P00 Campaña — Legislatura",
    }

    def test_con_boton_sin_guion_bajo(self):
        for f, esperado in self.CON_BOTON.items():
            self.assertEqual(nombre(WF / f), esperado, f)
            self.assertRegex(esperado, r"^P\d0 ")

    def test_sin_boton_con_guion_bajo(self):
        for f, esperado in self.SIN_BOTON.items():
            self.assertEqual(nombre(WF / f), esperado, f)
            self.assertRegex(esperado, r"^_P\d0 ")

    def test_pendientes_2a_sin_cambiar(self):
        for f, esperado in self.PENDIENTES_2A.items():
            self.assertEqual(nombre(WF / f), esperado, f)

    def test_p90_automatico_conserva_su_nombre(self):
        """Es el objetivo de los `workflow_run` de auto-merge: renombrarlo rompe la fusión."""
        self.assertEqual(nombre(WF / "p90-automatico.yml"), "P90 Automático")

    def test_todos_cubiertos_y_sin_interno(self):
        conocidos = set(self.CON_BOTON) | set(self.SIN_BOTON) | set(self.PENDIENTES_2A) | {"p90-automatico.yml"}
        self.assertEqual({f.name for f in self.vivos()}, conocidos)
        for f in self.vivos():
            self.assertNotIn("Interno", nombre(f), f.name)

    def test_control_negativo(self):
        """El patrón rechaza un nombre sin botón sin «_» y uno con botón con «_»."""
        self.assertIsNone(re.match(r"^_P\d0 ", "P90 Automático — Revisor de PR"))
        self.assertIsNone(re.match(r"^P\d0 ", "_P00 Campaña — Elección"))

    def test_nombres_unicos(self):
        # Única excepción: P00 nueva repite «P00 Campaña» de la 00 mientras convivan (T-379 PR 3, diseño T-378 §9).
        self.assertEqual(nombre(WF / "p00-campana.yml"), nombre(WF / "ejecucion-completa-proyecto.yml"))
        ns = [nombre(f) for f in WF.glob("*.yml") if f.name != "p00-campana.yml"]
        self.assertEqual(len(ns), len(set(ns)), ns)

    def test_nadie_busca_los_nombres_viejos(self):
        for f in WF.glob("*.yml"):
            t = f.read_text(encoding="utf-8")
            for lista in re.findall(r"^\s*workflows:\s*\[(.*?)\]", t, re.M | re.S):
                self.assertNotIn("Fusión automática", lista, f.name)
                self.assertNotIn("Revisor de PR", lista, f.name)
                self.assertNotIn("Elección", lista, f.name)
                self.assertNotIn("Legislatura", lista, f.name)


if __name__ == "__main__":
    unittest.main()
