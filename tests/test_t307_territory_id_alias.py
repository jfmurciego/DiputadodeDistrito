"""T-307: la cadena P00 acepta el id legacy del paquete P10 frente al id nuevo del run (D-61); un id ajeno bloquea."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from ddd_core.territorio_ids import id_legacy
from herramientas.evaluar_preparacion_territorial import evaluate
from ddd_ensemble.prepared_bundle import BundleValidationError, validate_prepared_bundle
from herramientas import fuente_infoelectoral_mesas as fim
from herramientas.validar_paquete_electoral import validate_package
from herramientas.validar_puerta_ejecucion import _campaign_namespace_is_consistent, validate_gate

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


class AliasOtrasPuertasTests(unittest.TestCase):
    def test_puerta_territorio_certificado(self):
        def razones(certificado):
            with tempfile.TemporaryDirectory() as d:
                raiz = Path(d)
                for sub in ("cache", "run", "sources"):
                    (raiz / sub).mkdir()
                (raiz / "production_status.json").write_text(json.dumps({"territory_id": certificado, "decision": "PASS"}))
                params = raiz / "p.yaml"
                params.write_text("meta:\n  year: 2025\n")
                r = validate_gate(phase="territorial_product", artifact_root=raiz, territory_id=NUEVO, edition="2025",
                                  run_id="10", artifact_name="ddd-state-10-M06", artifact_digest="a" * 64, params=params)
            return r["reasons"]
        self.assertNotIn("TERRITORIO_CERTIFICADO_NO_COINCIDE", razones(LEGACY))
        self.assertIn("TERRITORIO_CERTIFICADO_NO_COINCIDE", razones(id_legacy(AJENO)))

    def test_bundle_preparado(self):
        from ddd_ensemble import prepared_bundle as pb

        def error_real(tid):
            with tempfile.TemporaryDirectory() as d:
                z = Path(d) / "b.zip"
                with zipfile.ZipFile(z, "w") as zf:
                    zf.writestr("manifest.json", json.dumps({"schema": pb.SCHEMA, "territory_id": tid}))
                try:
                    validate_prepared_bundle(str(z), NUEVO)
                except BundleValidationError as exc:
                    return str(exc)
            return ""
        self.assertNotIn("territorio", error_real(LEGACY))
        self.assertIn("territorio no coincide", error_real(id_legacy(AJENO)).lower())

    def test_paquete_electoral(self):
        def error(tid):
            with tempfile.TemporaryDirectory() as d:
                pkg = Path(d)
                (pkg / "manifest.json").write_text(json.dumps(
                    {"schema": "ddd-electoral-package/1.0", "decision": "REUSE", "territory_id": tid, "edition": "2025"}))
                try:
                    validate_package(package=pkg, params=pkg / "p.yaml", territory_id=NUEVO, edition="2025", root=pkg)
                except Exception as exc:  # noqa: BLE001
                    return str(exc)
            return ""
        self.assertNotIn("territorio o edición", error(LEGACY))
        self.assertIn("territorio o edición", error(id_legacy(AJENO)))

    def test_infoelectoral_resolve(self):
        raiz = Path(__file__).resolve().parents[1]
        base = dict(election_id="congreso_huesca_2023-07-23", election_date="2023-07-23", root_dir=raiz)
        try:
            fim.resolve(territory_id=id_legacy("nac22"), **base)
        except ValueError as exc:
            self.assertNotIn("otra identidad", str(exc))
        with self.assertRaisesRegex(ValueError, "otra identidad"):
            fim.resolve(territory_id=id_legacy(AJENO), **base)


class RegistroIdCanonicoTests(unittest.TestCase):
    """El registro de la preparación escribe el id canónico, nunca el legacy del paquete P10."""

    def _decl(self, tid):
        return {"territory": {"id": tid, "business_name": "T", "edition": 2025,
                              "territorial_codes": [{"code": "01", "business_name": "P"}]}}

    def test_declaracion_legacy_escribe_canonico(self):
        from herramientas.adquirir_fuentes_oficiales import _territory
        self.assertEqual(_territory(self._decl(LEGACY))[0], NUEVO)
        self.assertEqual(_territory(self._decl(NUEVO))[0], NUEVO)

    def test_id_fuera_de_tabla_se_conserva(self):
        from herramientas.adquirir_fuentes_oficiales import _territory
        self.assertEqual(_territory(self._decl("sintetico_x"))[0], "sintetico_x")


if __name__ == "__main__":
    unittest.main()
