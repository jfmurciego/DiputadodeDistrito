"""Versión 1.0.0; 2026-11-03; candidato. T-35: el publicador único recibe el sha256 del zip del ensemble."""
from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = yaml.safe_load((ROOT / ".github/workflows/generar-alternativas-territoriales.yml").read_text(encoding="utf-8"))
PUBLISHER = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
JOBS = WF["jobs"]


class PublicacionDeEnsemblesTests(unittest.TestCase):
    def test_publish_y_republish_exponen_el_sha256_del_zip(self):
        for name in ("publish", "republish"):
            with self.subTest(name):
                self.assertEqual(JOBS[name]["outputs"]["ensemble_sha256"], "${{ steps.release.outputs.ensemble_sha256 }}")
                step = next(s for s in JOBS[name]["steps"] if s.get("id") == "release")
                self.assertIn('echo "ensemble_sha256=$(sha256sum "$asset" | cut -d\' \' -f1)" >> "$GITHUB_OUTPUT"', step["run"])
                # El hash se calcula sobre el mismo fichero que se sube al release.
                self.assertLess(step["run"].index('gh release'), step["run"].index("sha256sum"))

    def test_los_despliegues_pasan_el_hash_al_publicador(self):
        self.assertEqual(JOBS["desplegar_publish"]["with"]["ensemble_sha256"], "${{ needs.publish.outputs.ensemble_sha256 }}")
        self.assertEqual(JOBS["desplegar_republish"]["with"]["ensemble_sha256"], "${{ needs.republish.outputs.ensemble_sha256 }}")
        for name in ("desplegar_publish", "desplegar_republish"):
            self.assertEqual(JOBS[name]["with"]["target_page"], "Visor territorial")
            self.assertEqual(JOBS[name]["uses"], "./.github/workflows/_reutilizable-publicar-sitio.yml")

    def test_el_publicador_exige_exactamente_ese_formato(self):
        self.assertIn("ensemble_sha256:", PUBLISHER)
        self.assertIn("^[0-9a-f]{64}$", PUBLISHER)
        with tempfile.TemporaryDirectory() as td:
            asset = Path(td) / "ensemble-x.zip"
            asset.write_bytes(b"contenido")
            out = subprocess.run(["bash", "-c", 'cd "$1" && asset=ensemble-x.zip && sha256sum "$asset" | cut -d\' \' -f1', "_", td],
                                 capture_output=True, text=True, check=True).stdout.strip()
        self.assertRegex(out, r"^[0-9a-f]{64}$")

    def test_la_publicacion_sigue_siendo_solo_adicion_de_ensembles(self):
        text = (ROOT / ".github/workflows/generar-alternativas-territoriales.yml").read_text(encoding="utf-8")
        for forbidden in ("promover_catalogo", "catalogo_preparacion.yaml", "estado_operativo", "territorial_product", "canonical_m06"):
            self.assertNotIn(forbidden, text, forbidden)

    def test_republicacion_para_cualquier_territorio_con_config_y_50_bloqueado(self):
        step = next(s for s in JOBS["republish"]["steps"] if s.get("id") == "source")["run"]
        self.assertIn('configuracion/ensemble/${{ inputs.territory_id }}.json', step)
        self.assertIn("*:ensemble_10) ;;", step)
        self.assertIn("aragon:aragon_10) ;;", step)
        self.assertNotIn("*:ensemble_50", step)
        self.assertNotIn("aragon:aragon_50) ;;", step)
        assemble = next(s for s in JOBS["republish"]["steps"] if s.get("name") == "Reensamblar galería con el código actual")["run"]
        self.assertIn("configuracion/ensemble/${{ inputs.territory_id }}.json", assemble)


if __name__ == "__main__":
    unittest.main()
