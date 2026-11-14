"""T-307: el motor es estricto con los ids (sin alias legacy en la puerta) y el registro de la preparación escribe
siempre el id canónico (aut02), nunca el legacy del paquete P10."""
import json
import tempfile
import unittest
from pathlib import Path

from ddd_core.territorio_ids import id_legacy
from herramientas.adquirir_fuentes_oficiales import _territory
from herramientas.validar_puerta_ejecucion import validate_gate

NUEVO = "aut01"
LEGACY = id_legacy(NUEVO)


def _razones_puerta(certificado):
    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        for sub in ("cache", "run", "sources"):
            (raiz / sub).mkdir()
        (raiz / "production_status.json").write_text(json.dumps({"territory_id": certificado, "decision": "PASS"}))
        params = raiz / "p.yaml"
        params.write_text("meta:\n  year: 2025\n")
        return validate_gate(phase="territorial_product", artifact_root=raiz, territory_id=NUEVO, edition="2025",
                             run_id="10", artifact_name="ddd-state-10-M06", artifact_digest="a" * 64,
                             params=params)["reasons"]


class PuertaEstrictaTests(unittest.TestCase):
    def test_id_nuevo_pasa(self):
        self.assertNotIn("TERRITORIO_CERTIFICADO_NO_COINCIDE", _razones_puerta(NUEVO))

    def test_id_legacy_se_rechaza(self):
        self.assertIn("TERRITORIO_CERTIFICADO_NO_COINCIDE", _razones_puerta(LEGACY))


class RegistroIdCanonicoTests(unittest.TestCase):
    """El registro de la preparación escribe el id canónico, nunca el legacy del paquete P10."""

    def _decl(self, tid):
        return {"territory": {"id": tid, "business_name": "T", "edition": 2025,
                              "territorial_codes": [{"code": "01", "business_name": "P"}]}}

    def test_declaracion_legacy_escribe_canonico(self):
        self.assertEqual(_territory(self._decl(LEGACY))[0], NUEVO)
        self.assertEqual(_territory(self._decl(NUEVO))[0], NUEVO)

    def test_id_fuera_de_tabla_se_conserva(self):
        self.assertEqual(_territory(self._decl("sintetico_x"))[0], "sintetico_x")


if __name__ == "__main__":
    unittest.main()
