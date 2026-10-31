"""Versión 1.1.0 — Regresión de guard de Pages y trazabilidad del visor.
Fecha: 2026-10-27. Alcance: vistas analíticas Congreso y empaquetado.
Estado: prueba. Anterior: legacy/n08_pilot_pages_gate_20261027/current/tests/test_congreso_visor.py.
"""
from pathlib import Path
import unittest

from herramientas.preparar_visor_congreso_leon import artifact_provenance

ROOT = Path(__file__).resolve().parents[1]


class CongressViewerContractTests(unittest.TestCase):
    def test_both_provinces_auto_load_with_explicit_scope(self):
        html = (ROOT / "visor/congreso/index.html").read_text(encoding="utf-8")
        script = (ROOT / "visor/congreso/congreso.js").read_text(encoding="utf-8")
        for expected in ("value=\"24\"", "value=\"10\"", "PILOTO ANALÍTICO", "NO CERTIFICADO"):
            self.assertIn(expected, html)
        for expected in ('"24":{name:"León"', '"10":{name:"Cáceres"',
                         'fetch("data/"+cpro', 'municipios-divididos.geojson',
                         'NOT_CERTIFIED', "sourceDetails.textContent",
                         "candidate_file_sha256", "execution_id",
                         "detail.textContent"):
            self.assertIn(expected, script)
        self.assertNotIn('innerHTML=', script)

    def test_pages_excludes_congress_route_by_default_and_requires_opt_in(self):
        workflow = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        home = (ROOT / "visor/index.html").read_text(encoding="utf-8")
        self.assertNotIn('href="congreso/"', home)
        self.assertIn("include_congreso_analytical_preview", workflow)
        self.assertIn("default: false", workflow)
        core_start = workflow.index("- name: Construir sitio candidato completo")
        pilot_start = workflow.index("- name: Preparar visor analítico Congreso opt-in")
        validate_start = workflow.index("- name: Validar sitio candidato completo")
        self.assertNotIn("/congreso/", workflow[core_start:pilot_start])
        optional_step = workflow[pilot_start:validate_start]
        self.assertIn("if: ${{ inputs.include_congreso_analytical_preview }}", optional_step)
        self.assertIn("mkdir -p /tmp/site-candidate/congreso/data", optional_step)
        self.assertNotIn("congreso/data", (ROOT / "orchestracion/publicaciones_visor.json").read_text(encoding="utf-8"))

    def test_geojson_provenance_is_exact_and_rejects_invalid_identity(self):
        digest = "a" * 64
        self.assertEqual(artifact_provenance("40414472380", digest), {
            "execution_id": "40414472380",
            "candidate_file_sha256": digest,
        })
        for run_id, candidate_sha in (("", digest), ("run-1", digest), ("123", "bad")):
            with self.subTest(run_id=run_id, candidate_sha=candidate_sha):
                with self.assertRaises(ValueError):
                    artifact_provenance(run_id, candidate_sha)

    def test_pilot_preflight_packs_standalone_viewer_without_public_deploy(self):
        workflow = (ROOT / "legacy/workflows/retirados_20261031/congreso-piloto-leon.yml").read_text(encoding="utf-8")
        self.assertIn("N08_STANDALONE_VIEWER_READY", workflow)
        self.assertIn("piloto-autonomo.html", workflow)
        self.assertIn("10-split", workflow)
        self.assertEqual(workflow.count('--execution-id "$GITHUB_RUN_ID"'), 3)
        self.assertNotIn("actions/deploy-pages", workflow)


if __name__ == "__main__":
    unittest.main()
