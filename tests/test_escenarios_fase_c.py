"""Versión 1.0.0; 2026-11-02; candidato. T-27 fase (c): una campaña de otro algoritmo es un escenario que no registra y se describe como scenario_*."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from herramientas import registro_publicaciones_visor as reg
from herramientas.gestor_campana_nacional import persist_state_for

CERTIFIED = {"decision": "PASS_WITH_EXCEPTIONS"}


def row(**plan):
    base = {"pre_m04_accreditation_planned": False, "run_prepare_electoral": False, "run_incorporate": True}
    base.update(plan)
    return {"execution_plan": base, "territorial_product": CERTIFIED}


class PersistenciaDeEscenariosTests(unittest.TestCase):
    def test_canonico_conserva_su_formula(self):
        self.assertTrue(persist_state_for(row(), "Canónico"))
        self.assertFalse(persist_state_for(row(run_incorporate=False), "Canónico"))

    def test_otro_algoritmo_sobre_territorio_certificado_no_registra(self):
        for strategy in ("GerryChain", "GerryChain 25", "GerryChain 50"):
            self.assertFalse(persist_state_for(row(), strategy), strategy)

    def test_primera_generacion_o_sin_producto_certificado_sigue_registrando(self):
        self.assertTrue(persist_state_for(row(pre_m04_accreditation_planned=True), "GerryChain 50"))
        sin_producto = {"execution_plan": row()["execution_plan"], "territorial_product": {}}
        self.assertTrue(persist_state_for(sin_producto, "GerryChain 50"))
        bloqueado = {"execution_plan": row()["execution_plan"], "territorial_product": {"decision": "BLOCK"}}
        self.assertTrue(persist_state_for(bloqueado, "GerryChain 50"))


class DescriptoresDeEscenarioTests(unittest.TestCase):
    def describe(self, **kwargs):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(reg, "production_metadata", return_value={
                 "territory_id": "nac37", "territory_label": "Nacional Salamanca", "expected_districts": 3,
                 "production_status": {"territorial_certification_status": "PASS"}}), \
             mock.patch.object(reg, "read_json", return_value={"decision": "PASS", "gate_statement": "ok"}), \
             mock.patch.object(reg, "certification_status", return_value="CERTIFIED"), \
             mock.patch.object(reg, "first", side_effect=lambda root, pattern: Path(td) / pattern.replace("*", "x")):
            return reg.production_descriptors(Path(td), "555", **kwargs)

    def test_canonico_no_cambia(self):
        d = self.describe()
        self.assertEqual([x["kind"] for x in d], ["canonical_m06", "canonical_m08"])
        self.assertNotIn("scenario_id", d[0])
        self.assertEqual(d[0]["id"], "m06-congreso_salamanca-555")

    def test_escenario_se_describe_como_scenario_m06_m08(self):
        d = self.describe(scenario_id="gerrychain-50-555", strategy="GerryChain 50")
        self.assertEqual([x["kind"] for x in d], ["scenario_m06", "scenario_m08"])
        for x in d:
            self.assertEqual((x["scenario_id"], x["strategy"], x["scenario_kind"], x["canonical"]),
                             ("gerrychain-50-555", "GerryChain 50", "alternative", False))
            self.assertIn("gerrychain-50-555", x["id"])
        # Los descriptores pasan la validación del registro una vez resueltos sus activos inmutables.
        entries = []
        for x in d:
            blob = ("a" if x["stage"] == "M06" else "b") * 40
            entries.append({**x, "source_type": "repository_blob", "repository": "o/r", "blob_sha": blob,
                            "immutable_location": f"github-git-blob://o/r/{blob}", "sha256": blob + blob[:24]})
        reg.validate_registry({"schema": reg.SCHEMA, "products": entries, "ensembles": []})


class CableadoDePublicacionTests(unittest.TestCase):
    def test_los_dos_workflows_aceptan_escenario_y_lo_pasan_al_describir(self):
        root = Path(__file__).resolve().parents[1] / ".github/workflows"
        interfaz = (root / "desplegar-visor-publico.yml").read_text(encoding="utf-8")
        publicador = (root / "_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        for text in (interfaz, publicador):
            self.assertIn("scenario_id", text)
        self.assertIn("scenario_strategy", interfaz)
        self.assertIn('${SCENARIO_ID:+--scenario-id "$SCENARIO_ID" --strategy "$SCENARIO_STRATEGY"}', publicador)
        self.assertIn("scenario_id: ${{ inputs.scenario_id }}", interfaz)


if __name__ == "__main__":
    unittest.main()
