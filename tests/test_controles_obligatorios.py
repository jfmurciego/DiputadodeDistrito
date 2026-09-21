"""Verifica que el motor de producción M05 conserva todos los controles
declarados en configuracion/controles_obligatorios.yaml.

Es un análisis estático: no importa gerrychain ni ejecuta el motor, así que
corre en la CI general sin el entorno aislado de GerryChain.

Si este test falla, NO se relaja: o se restaura el control en el motor, o se
retira del registro con un commit propio justificado en el registro de cambios.
"""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "configuracion" / "controles_obligatorios.yaml"


def _cargar() -> tuple[dict, str, ast.Module]:
    reg = yaml.safe_load(REGISTRO.read_text(encoding="utf-8"))
    fuente = (RAIZ / reg["motor"]).read_text(encoding="utf-8")
    return reg, fuente, ast.parse(fuente)


def _restricciones_emitidas(fuente: str) -> set[str]:
    # violations.append(f"nombre:...") / violations.append("nombre")
    emitidas = set(re.findall(r'violations\.append\(\s*f?"([a-z_]+)', fuente))
    # return ["nombre"] (salida temprana)
    emitidas |= set(re.findall(r'return\s*\[\s*"([a-z_]+)"\s*\]', fuente))
    return emitidas


def _identificadores(arbol: ast.Module, nombre: str) -> set[str] | None:
    """Nombres, atributos y claves de subíndice usados en el CÓDIGO de la
    función. Ignora comentarios y docstrings: la primera versión de este test
    daba falso positivo porque un comentario decía «forma determinista»."""
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            ids: set[str] = set()
            for n in ast.walk(nodo):
                if isinstance(n, ast.Name):
                    ids.add(n.id)
                elif isinstance(n, ast.Attribute):
                    ids.add(n.attr)
                elif isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
                        and isinstance(n.slice.value, str):
                    ids.add(n.slice.value)
                elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                    ids.add(n.func.id)
            return ids
    return None


class ControlesObligatorios(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reg, cls.fuente, cls.arbol = _cargar()

    def test_restricciones_duras_presentes(self) -> None:
        emitidas = _restricciones_emitidas(self.fuente)
        faltan = sorted(set(self.reg["restricciones_duras"]) - emitidas)
        self.assertEqual(
            faltan, [],
            f"El motor {self.reg['motor']} ya no emite: {faltan}. "
            "Restaura el control o retíralo del registro con justificación.",
        )

    def test_comarca_activa_en_propuesta(self) -> None:
        if not self.reg["objetivo"]["comarca_surcharge_activo"]:
            self.skipTest("comarca desactivada explícitamente en el registro")
        self.assertIn("region_surcharge", self.fuente)
        if re.search(r"region_surcharge\s*=\s*None", self.fuente):
            self.fail("region_surcharge=None desactiva la comarca en la propuesta ReCom.")

    def test_forma_en_objetivo(self) -> None:
        if not self.reg["objetivo"]["forma_en_objetivo"]:
            self.skipTest("forma desactivada explícitamente en el registro")
        ids = _identificadores(self.arbol, "candidate_rank")
        self.assertIsNotNone(ids, "No se encuentra candidate_rank")
        termino_forma = any(re.search(r"polsby|compact|shape", i, re.I) for i in ids)
        cota_dura = "UpperBound" in self.fuente
        self.assertTrue(
            termino_forma or cota_dura,
            "candidate_rank no contiene término de forma y no hay cota dura "
            "sobre aristas de corte. cut_edges detrás de dos flotantes de "
            "población en una tupla lexicográfica no decide nunca.",
        )

    def test_reproducibilidad(self) -> None:
        if self.reg["reproducibilidad"]["require_pythonhashseed_zero"]:
            self.assertRegex(self.fuente, r"require_pythonhashseed_zero\s*:\s*bool\s*=\s*True")
        if self.reg["reproducibilidad"]["garantia_monotonia"]:
            self.assertRegex(self.fuente, r"selected_rank\s*>\s*initial_rank")


if __name__ == "__main__":
    unittest.main()
