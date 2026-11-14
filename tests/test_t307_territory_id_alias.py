"""T-307: la cadena P00 acepta el id legacy del paquete P10 frente al id nuevo del run (D-61); un id ajeno bloquea."""
import unittest

from ddd_core.territorio_ids import id_legacy
from herramientas.evaluar_preparacion_territorial import evaluate
from herramientas.validar_puerta_ejecucion import _campaign_namespace_is_consistent

NUEVO = "aut01"
LEGACY = id_legacy(NUEVO)
AJENO = "aut02"


def _cabecera(tid):
    return {"territory_id": tid, "territory": "T", "edition": 2025, "population_year": 2025,
            "section_year": 2025, "environment": "test", "acquisition_mode": "simulated"}


def _headers_ok(doc_id):
    decl = {"territory": {"id": NUEVO, "business_name": "T", "edition": 2025, "source_year": 2025}, "required_sources": []}
    docs = [_cabecera(doc_id) for _ in range(3)]
    res = evaluate(catalog={"sources": {}}, declaration=decl, resolved_declaration=docs[0], inventory=docs[1],
                   provenance=docs[2], environment="test")
    return res["checks"]["headers_equal"], res


class AliasTerritoryIdTests(unittest.TestCase):
    def test_legacy_en_paquete_se_acepta(self):
        ok, res = _headers_ok(LEGACY)
        self.assertTrue(ok, res.get("reasons"))

    def test_mismo_id_se_acepta(self):
        self.assertTrue(_headers_ok(NUEVO)[0])

    def test_id_ajeno_bloquea(self):
        ok, res = _headers_ok(id_legacy(AJENO))
        self.assertFalse(ok)
        ok, _ = _headers_ok(AJENO)
        self.assertFalse(ok)

    def test_namespace_campana_con_alias(self):
        ns = f"campaign-10-1--01--{LEGACY}"
        self.assertTrue(_campaign_namespace_is_consistent(ns, territory_id=NUEVO, run_id="10"))
        self.assertFalse(_campaign_namespace_is_consistent(
            f"campaign-10-1--01--{id_legacy(AJENO)}", territory_id=NUEVO, run_id="10"))


if __name__ == "__main__":
    unittest.main()
