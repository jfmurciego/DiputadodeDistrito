"""Nombre: regresiones contra el predecesor F10. Versión: 1.0.0.
Fecha: 2026-10-12. Alcance: pruebas locales controladas. Estado: candidato.
Cambios/motivo: reproducir los fallos causales previos a la corrección.
Origen: predecesores conservados en legacy/herramientas para este incremento.
"""
from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import tests.test_f10_interannual_correspondence as regressions
import herramientas.adquirir_fuentes_oficiales as acquisition


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compatibility = load("compatibility_predecessor", "legacy/herramientas/compatibilidad_poblacion_seccionado_pre_F10_interanual_20261012.py")
regressions.reconcile_population_sectioning = compatibility.reconcile_population_sectioning
regressions._intersects = compatibility._intersects
acquisition.acquire = load("acquisition_predecessor", "legacy/herramientas/adquirir_fuentes_oficiales_pre_F10_raw_population_20261012.py").acquire
suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromTestCase(regressions.InterannualCorrespondenceTests),
    regressions.PopulationInputPreservationTests("test_acquisition_keeps_original_bytes_when_valencia_coverage_blocks"),
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
print("Baseline regressions:", result.testsRun, "failures", len(result.failures), "errors", len(result.errors))
assert result.testsRun == 5 and len(result.failures) == 3 and len(result.errors) == 2
