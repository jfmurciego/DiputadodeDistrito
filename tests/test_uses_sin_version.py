"""Control del normalizador de equivalencia (`tests/_uses_sin_version.py`): ignora la versión, no la acción ni el resto del paso."""
import copy
import unittest

from tests._uses_sin_version import sin_version

PASO = {"name": "x", "uses": "owner/repo@" + "a" * 40, "with": {"k": "v"}}


def wf(paso):
    return {"jobs": {"j": {"steps": [paso, {"uses": "./.github/actions/local"}], "uses": "./.github/workflows/r.yml"}}}


class Normalizador(unittest.TestCase):
    def test_bump_de_version_es_equivalente(self):
        n = copy.deepcopy(PASO)
        n["uses"] = "owner/repo@" + "b" * 40
        self.assertEqual(sin_version(wf(PASO)), sin_version(wf(n)))

    def test_locales_y_reutilizables_intactos(self):
        r = sin_version(wf(PASO))["jobs"]["j"]
        self.assertEqual(r["uses"], "./.github/workflows/r.yml")
        self.assertEqual(r["steps"][1]["uses"], "./.github/actions/local")

    def test_controles_negativos(self):
        for cambio in (lambda p: p.update(uses="otro/repo@" + "a" * 40), lambda p: p["with"].update(k="w"),
                       lambda p: p.update(run="echo"), lambda p: p.pop("with")):
            n = copy.deepcopy(PASO)
            cambio(n)
            self.assertNotEqual(sin_version(wf(PASO)), sin_version(wf(n)))
        w = wf(PASO)
        w["jobs"]["j"]["steps"].pop(0)
        self.assertNotEqual(sin_version(wf(PASO)), sin_version(w))
