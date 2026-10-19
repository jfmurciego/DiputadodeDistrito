"""Versión 1.0.0; 2026-10-13; no mutación en reproducción de evidencias N08.

Nombre: pruebas del verificador aislado N08.
Alcance: expediente nacional 74/74, Cáceres 26/26 y salidas byte-idénticas.
Estado: candidato diagnóstico.
Cambios/motivo: prueba de integración read-only con las evidencias versionadas.
Origen: nuevo; no sustituye pruebas históricas.
Anterior: no aplicable; prueba nueva.
"""
from pathlib import Path

from herramientas.verificar_evidencia_n08_readonly import verify


ROOT = Path(__file__).resolve().parents[1]


def test_reproduces_n08_evidence_without_mutating_versioned_outputs():
    paths = (
        ROOT / "docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013/MATRIZ_FACTIBILIDAD_52.csv",
        ROOT / "docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013/VERIFICACION.json",
        ROOT / "docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013/MANIFEST.json",
        ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/MANIFEST_ENTREGA.json",
        ROOT / "docs/ESTUDIOS/N08_CACERES_20261012/MANIFEST.json",
    )
    before = {path: path.read_bytes() for path in paths}

    result = verify(ROOT)

    assert result["status"] == "PASS"
    assert result["read_only"] is True
    assert result["national_entries_verified"] == 74
    assert result["caceres_entries_verified"] == 26
    assert result["coverage"] == {
        "origin_units": 52,
        "sections": 36554,
        "population_2025": 49128297,
        "K": 407,
        "physical_edges": 99597,
    }
    assert result["generation_authorized"] is False
    assert all(item["byte_identical"] for item in result["outputs"].values())
    assert result["source_manifests_unchanged"] is True
    assert result["versioned_outputs_unchanged"] is True
    assert {path: path.read_bytes() for path in paths} == before


# Bridge function-style regressions into the repository's unittest CI.
def load_tests(loader, tests, pattern):
    import unittest

    suite = unittest.TestSuite()
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            suite.addTest(unittest.FunctionTestCase(fn, description=name))
    return suite
