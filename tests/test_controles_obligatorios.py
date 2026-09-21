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
        funcion = next(
            (n for n in ast.walk(self.arbol) if isinstance(n, ast.FunctionDef) and n.name == "candidate_rank"),
            None,
        )
        self.assertIsNotNone(funcion, "No se encuentra candidate_rank")
        retorno = next(
            (n for n in ast.walk(funcion) if isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple)),
            None,
        )
        self.assertIsNotNone(retorno, "candidate_rank no devuelve una tupla explícita")
        elementos = [ast.unparse(e) for e in retorno.value.elts]
        self.assertGreaterEqual(len(elementos), 8, "candidate_rank perdió dimensiones del objetivo")
        self.assertIn("math.ceil", elementos[1])
        self.assertIn("population_band", elementos[1])
        self.assertEqual(
            float(self.reg["objetivo"]["population_band"]),
            0.005,
            "La banda poblacional registrada debe ser 0.005.",
        )
        forma = next((i for i, e in enumerate(elementos) if "shape" in e and "penalty" in e), None)
        self.assertIsNotNone(forma, "candidate_rank no contiene penalización de forma")
        continuas = [
            i for i, e in enumerate(elementos)
            if e in {"max_rel_dev", "rms"}
            or "max_relative_deviation" in e
            or "rms_relative_deviation" in e
        ]
        self.assertTrue(continuas, "No se localizaron métricas continuas de población")
        self.assertLess(
            forma,
            min(continuas),
            "La forma debe decidir antes que max_rel_dev/rms dentro de la banda poblacional.",
        )

    def test_reproducibilidad(self) -> None:
        if self.reg["reproducibilidad"]["require_pythonhashseed_zero"]:
            self.assertRegex(self.fuente, r"require_pythonhashseed_zero\s*:\s*bool\s*=\s*True")
        if self.reg["reproducibilidad"]["garantia_monotonia"]:
            self.assertRegex(self.fuente, r"selected_rank\s*>\s*initial_rank")


if __name__ == "__main__":
    unittest.main()
