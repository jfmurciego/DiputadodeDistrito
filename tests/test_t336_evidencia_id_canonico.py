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
WORKFLOW = ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml"


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
    def test_chown_antes_del_cp_y_cp_no_silencioso(self):
        txt = WORKFLOW.read_text(encoding="utf-8")
        i = txt.index("name: Resolver y materializar fuentes declaradas")
        paso = txt[i:txt.index("- id: evaluate", i)]
        self.assertLess(paso.index('sudo chown -R "$(id -u):$(id -g)" "$EVIDENCE_DIR"'), paso.index("cp .ddd-source-checkpoint"))
        self.assertIn("|| {", paso[paso.index("cp .ddd-source-checkpoint"):])


if __name__ == "__main__":
    unittest.main()
