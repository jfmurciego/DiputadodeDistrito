"""T-336: un paquete/evidencia de fuentes con territory_id distinto del canónico se rechaza o se re-adquiere.

Sin alias ni reescritura: el id viejo (p. ej. el de Extremadura antes del renombrado T-220) no se restaura.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ddd_core import territorio_ids
from herramientas.ejecutar_fuentes_workflow import checkpoint_territory_mismatch
from herramientas.gestionar_fuentes_checkpoint import execute_source_policy
from herramientas.seleccionar_paquete_fuentes import select_first_valid, validate_prepared_package
from tests.test_preparacion_fuentes_reutilizacion import build_package, rewrite_bundle

CANON = "aut11"
VIEJO = territorio_ids.tabla()[CANON].id_legacy
ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/p20-distritos.yml"


def _checkpoint(base: Path, territory: str) -> Path:
    ck = base / "ck"
    build_package(ck / "sources", territory=territory)
    return ck


class SelectorExacto(unittest.TestCase):
    def test_id_canonico_se_reutiliza(self):
        with tempfile.TemporaryDirectory() as td:
            pkg = build_package(Path(td) / "p", territory=CANON)
            self.assertEqual(validate_prepared_package(pkg, territory_id=CANON, edition=2025), (True, []))

    def test_id_legacy_en_todo_el_paquete_se_rechaza(self):
        with tempfile.TemporaryDirectory() as td:
            pkg = build_package(Path(td) / "p", territory=VIEJO)
            ok, reasons = validate_prepared_package(pkg, territory_id=CANON, edition=2025)
            self.assertFalse(ok)
            self.assertTrue(any("distinto" in r for r in reasons), reasons)
            sel, _ = select_first_valid([pkg], territory_id=CANON, edition=2025, reuse_enabled=True)
            self.assertIsNone(sel)

    def test_id_legacy_solo_en_un_documento_se_rechaza(self):
        for doc in ("inventario_fuentes.json", "manifiesto_procedencia.json", "decision_adquisicion.json"):
            with self.subTest(doc=doc), tempfile.TemporaryDirectory() as td:
                pkg = build_package(Path(td) / "p", territory=CANON)

                def mut(members, doc=doc):
                    d = json.loads(members[doc])
                    d["territory_id"] = VIEJO
                    members[doc] = json.dumps(d).encode()

                rewrite_bundle(pkg, mut)
                ok, reasons = validate_prepared_package(pkg, territory_id=CANON, edition=2025)
                self.assertFalse(ok, reasons)


class CheckpointReanudacion(unittest.TestCase):
    def _cadena(self, territory: str):
        """Simula la cadena de preparación de aut11: checkpoint restaurado → política → ¿REUSE o ACQUIRE?"""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            ck = _checkpoint(base, territory)
            llamadas = []

            def downloader(working: Path) -> dict:
                llamadas.append(1)
                raise RuntimeError("ACQUIRE_SIMULADO")

            motivos = checkpoint_territory_mismatch(ck, CANON)
            ck_in = None if motivos else ck
            try:
                ev = execute_source_policy(
                    requested_edition=2025, working=base / "w", checkpoint_in=ck_in,
                    checkpoint_out=base / "out", official_available=True,
                    downloader=downloader, expected_records=None,
                )
                decision = ev["decision"]
            except RuntimeError as exc:
                decision = str(exc)
            return motivos, decision, len(llamadas)

    def test_checkpoint_con_id_viejo_fuerza_acquire(self):
        motivos, decision, llamadas = self._cadena(VIEJO)
        self.assertTrue(motivos)
        self.assertEqual((decision, llamadas), ("ACQUIRE_SIMULADO", 1))

    def test_checkpoint_con_id_canonico_es_reuse(self):
        motivos, decision, llamadas = self._cadena(CANON)
        self.assertEqual(motivos, [])
        self.assertEqual((decision, llamadas), ("REUSE", 0))

    def test_sin_checkpoint_no_hay_motivos(self):
        self.assertEqual(checkpoint_territory_mismatch(None, CANON), [])


class WorkflowPermisos(unittest.TestCase):
    def test_puerta_falla_si_la_adquisicion_fallo(self):
        txt = WORKFLOW.read_text(encoding="utf-8")
        i = txt.index("name: Aplicar puerta de preparación")
        paso = txt[i:txt.index("  m01:", i)]
        self.assertIn("ACQUIRE_OUTCOME: ${{ steps.acquire.outcome }}", paso)
        self.assertIn('[[ "$ACQUIRE_OUTCOME" != failure ]]', paso)

    def test_chown_antes_del_cp_y_cp_no_silencioso(self):
        txt = WORKFLOW.read_text(encoding="utf-8")
        i = txt.index("name: Resolver y materializar fuentes declaradas")
        paso = txt[i:txt.index("- id: evaluate", i)]
        self.assertLess(paso.index('sudo chown -R "$(id -u):$(id -g)" "$EVIDENCE_DIR"'), paso.index("cp .ddd-source-checkpoint"))
        self.assertIn("|| {", paso[paso.index("cp .ddd-source-checkpoint"):])


class SelectorCLIyP10(unittest.TestCase):
    """El paso del P10 («Recuperar fuente territorial registrada») ejecutado de verdad bajo `bash -eo pipefail`."""

    PREP = ROOT / ".github/workflows/preparacion-fuentes.yml"

    def _cola_del_paso(self) -> str:
        import yaml
        d = yaml.safe_load(self.PREP.read_text(encoding="utf-8"))
        for job in d["jobs"].values():
            for st in job.get("steps", []):
                if st.get("name") == "Recuperar fuente territorial registrada":
                    run = st["run"]
                    return run[run.index("rc=0\n"):]
        raise AssertionError("paso no encontrado")

    def _ejecutar(self, territory: str, **kw):
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            build_package(cwd / ".ddd-source-package", territory=territory, **kw)
            out, summ = cwd / "out.txt", cwd / "summary.md"
            out.touch(); summ.touch()
            env = dict(os.environ, PYTHONPATH=str(ROOT), TERRITORY_ID=CANON, EDITION="2025", POPULATION_YEAR="2025",
                       SECTION_YEAR="2025", REGISTERED_RUN_ID="42720735134",
                       REGISTERED_ARTIFACT_NAME=f"ddd-source-package-{VIEJO}-2025-42720735134",
                       GITHUB_OUTPUT=str(out), GITHUB_STEP_SUMMARY=str(summ))
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", self._cola_del_paso()], cwd=cwd, env=env,
                               capture_output=True, text=True)
            return r.returncode, out.read_text(), summ.read_text(), r.stdout + r.stderr

    def test_paquete_id_viejo_adquiere_de_verdad(self):
        rc, out, summ, _ = self._ejecutar(VIEJO)
        self.assertEqual(rc, 0)
        self.assertIn("reused_candidate=false", out)
        self.assertIn("ADQUIRIRÁ", summ)

    def test_cadena_completa_id_viejo_rc3_y_adquisicion_real(self):
        """rc 3 → el directorio de trabajo queda limpio → execute_source_policy adquiere (no lee el paquete viejo)."""
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            build_package(cwd / ".ddd-source-package", territory=VIEJO)
            out, summ = cwd / "out.txt", cwd / "summary.md"
            out.touch(); summ.touch()
            env = dict(os.environ, PYTHONPATH=str(ROOT), TERRITORY_ID=CANON, EDITION="2025", POPULATION_YEAR="2025",
                       SECTION_YEAR="2025", REGISTERED_RUN_ID="1", REGISTERED_ARTIFACT_NAME="x",
                       GITHUB_OUTPUT=str(out), GITHUB_STEP_SUMMARY=str(summ))
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", self._cola_del_paso()], cwd=cwd, env=env,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("reused_candidate=false", out.read_text())
            self.assertFalse((cwd / ".ddd-source-package").exists())
            llamadas = []

            def downloader(working: Path) -> dict:
                llamadas.append(1)
                raise RuntimeError("ACQUIRE_REAL")

            with self.assertRaisesRegex(RuntimeError, "ACQUIRE_REAL"):
                execute_source_policy(requested_edition=2025, working=cwd / ".ddd-source-package",
                                      checkpoint_in=None, checkpoint_out=cwd / "ck", official_available=True,
                                      downloader=downloader, expected_records=None)
            self.assertEqual(len(llamadas), 1)

    def test_paquete_canonico_se_reutiliza_y_lo_dice(self):
        rc, out, summ, _ = self._ejecutar(CANON)
        self.assertEqual(rc, 0)
        self.assertIn("reused_candidate=true", out)
        self.assertIn("REUTILIZÓ", summ)

    def test_otro_rechazo_sigue_fallando(self):
        rc, out, _, _ = self._ejecutar(CANON, edition=2024)
        self.assertNotEqual(rc, 0)
        self.assertNotIn("reused_candidate=false", out)

    def test_nac_con_paquete_viejo_adquiere(self):
        nac = next(t for t in territorio_ids.tabla() if t.startswith("nac"))
        viejo = territorio_ids.tabla()[nac].id_legacy
        with tempfile.TemporaryDirectory() as td:
            pkg = build_package(Path(td) / "p", territory=viejo)
            self.assertFalse(validate_prepared_package(pkg, territory_id=nac, edition=2025)[0])
            pkg2 = build_package(Path(td) / "q", territory=nac)
            self.assertTrue(validate_prepared_package(pkg2, territory_id=nac, edition=2025)[0])


class ReanudacionBloquea(unittest.TestCase):
    def test_checkpoint_de_reanudacion_con_id_viejo_se_bloquea(self):
        from herramientas.validar_fuentes_reanudacion import validate_resume_sources
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "territorios" / CANON / "config"
            cfg.mkdir(parents=True)
            (cfg / "fuentes_oficiales.yaml").write_text("territory:\n  edition: 2025\n", encoding="utf-8")
            (root / "params.yaml").write_text(f"meta:\n  territory_id: {CANON}\n", encoding="utf-8")
            build_package(root / "viejo", territory=VIEJO)
            with self.assertRaisesRegex(RuntimeError, "no canónico"):
                validate_resume_sources(params=root / "params.yaml", package=root / "viejo", root_dir=root)


if __name__ == "__main__":
    unittest.main()
